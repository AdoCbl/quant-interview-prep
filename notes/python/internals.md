# Python Under the Hood

How CPython (the standard Python implementation) actually stores objects and implements the
standard library's containers: `int`, `list`, `tuple`, `dict`, `set`, `str`, `deque`,
`OrderedDict`, `heapq`, `sorted`, `lru_cache`, plus the interpreter, memory management and
attribute lookup. Senior interviews probe this to see whether you can predict performance and
explain surprising behaviour. Each term is explained the first time it appears; a glossary is at the end.

Every code block runs on its own (`uv run python file.py`); the block after it shows its output
from **CPython 3.14** on 64-bit macOS. Exact byte counts change between versions; the mechanisms
don't. Basics (data model, concurrency, NumPy) are on the [main Python page](README.md); idioms are
in [features and tricks](senior-features-and-tricks.md).

Contents:

1. [Every value is an object](#1-every-value-is-an-object)
2. [list and tuple](#2-list-and-tuple)
3. [dict and set: hash tables](#3-dict-and-set-hash-tables)
4. [str](#4-str)
5. [collections and heapq](#5-collections-and-heapq)
6. [Sorting: Timsort](#6-sorting-timsort)
7. [The interpreter: bytecode and specialisation](#7-the-interpreter-bytecode-and-specialisation)
8. [Memory management](#8-memory-management)
9. [Attribute lookup, descriptors and the MRO](#9-attribute-lookup-descriptors-and-the-mro)
10. [Generators, itertools and lru_cache](#10-generators-itertools-and-lru_cache)
11. [The GIL and free-threaded Python](#11-the-gil-and-free-threaded-python)
12. [Interview questions](#12-interview-questions)
13. [Glossary](#13-glossary)

---

## 1. Every value is an object

- Every value lives on the heap as a C struct that starts with a **header**: a **reference count** (how many references point to it) and a pointer to its **type**. A variable is just a name bound to a pointer.
- So even `1` costs 28 bytes, and a list of numbers is a list of *pointers* to separate number objects (this is why NumPy arrays, which store raw 8-byte values side by side, are 3–4× smaller and much faster).
- **`int`** has arbitrary precision: stored as an array of 30-bit "digits". Arithmetic on big ints is O(digits); multiplication uses Karatsuba above a size threshold.
- **Small-int cache**: −5 to 256 are created once at start-up and shared, so `is` happens to be true for them. Never use `is` to compare numbers or strings; use `==`.
- **Immortal objects** (3.12+): `None`, `True`, `False`, small ints and some strings have a reference count that never changes, which avoids cache-line traffic between threads.

```python
import sys

# Every value is a heap object with a header: reference count + pointer to its type
print("sizes:", {name: sys.getsizeof(v) for name, v in
                 [("int 1", 1), ("int 2**100", 2**100), ("float", 1.0), ("None", None),
                  ("empty tuple", ()), ("empty list", []), ("empty dict", {}), ("empty str", "")]})

# int: arbitrary precision, stored as base-2**30 "digits"
print("int digits:", sys.int_info.bits_per_digit, "bits;",
      "2**100 needs", -(-(2**100).bit_length() // 30), "digits")

# Small ints -5..256 are preallocated singletons
a, b = int("256"), int("256")
c, d = int("257"), int("257")
print("256 is 256:", a is b, " 257 is 257:", c is d)

# Immortal objects (3.12+): None, True, small ints never change refcount
print("refcount of None is huge:", sys.getrefcount(None) > 10**9)
x = []
print("refcount of a fresh list (incl. the call's own reference):", sys.getrefcount(x))
y = x
print("after y = x:", sys.getrefcount(x))
```

Output:

```text
sizes: {'int 1': 28, 'int 2**100': 40, 'float': 24, 'None': 16, 'empty tuple': 48, 'empty list': 56, 'empty dict': 64, 'empty str': 41}
int digits: 30 bits; 2**100 needs 4 digits
256 is 256: True  257 is 257: False
refcount of None is huge: True
refcount of a fresh list (incl. the call's own reference): 2
after y = x: 3
```

---

## 2. list and tuple

- A **list** is a resizable array of pointers: a pointer to the array, its length and its **capacity** (allocated slots).
- `append` writes into a spare slot in O(1). When full, it grows to about `n + n/8 + 6` slots (rounded to a multiple of 4) and copies the pointers. Geometric growth makes `append` **amortised O(1)**; Python's factor (≈1.125) is small, saving memory at the cost of more frequent copies.
- Insert or delete at the front shifts every pointer: O(n). `x in list` compares one by one: O(n).
- A **tuple** is fixed-size, stored in one block with no spare capacity, and small tuples are recycled from free lists: smaller and faster to create than lists. Tuples of hashable items are hashable, so they work as dict keys.

```python
import sys

# list = array of pointers with spare capacity; growth is about 1.125x + a constant
lst, caps = [], []
for _ in range(64):
    lst.append(None)
    cap = (sys.getsizeof(lst) - sys.getsizeof([])) // 8   # 8-byte pointer per slot
    if not caps or cap != caps[-1]:
        caps.append(cap)
print("capacities as you append:", caps)

# A list holds references, not values: * copies the reference
grid = [[0] * 3] * 3
grid[0][0] = 1
print("aliased rows:", grid)
grid = [[0] * 3 for _ in range(3)]
grid[0][0] = 1
print("independent rows:", grid)

# tuple: fixed size, no spare capacity, so smaller; free lists make small tuples cheap
print("list vs tuple of 3:", sys.getsizeof([1, 2, 3]), sys.getsizeof((1, 2, 3)))
```

Output:

```text
capacities as you append: [4, 8, 16, 24, 32, 40, 52, 64]
aliased rows: [[1, 0, 0], [1, 0, 0], [1, 0, 0]]
independent rows: [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
list vs tuple of 3: 88 72
```

---

## 3. dict and set: hash tables

**How a dict lookup works:**
1. Compute `hash(key)` (cached on `str` objects).
2. Use the low bits of the hash to pick a slot in the **index table**.
3. If the slot holds a different key, probe again with **perturbed probing**: `perturb >>= 5`, then `i = (5·i + 1 + perturb) mod size` (`perturb` starts as the full hash). This feeds the high bits of the hash in, so similar hashes spread out.
4. Compare keys by identity first, then by `==`.

**Compact layout (3.6+):** a small sparse **index table** of 1–8 byte integers points into a dense **entries array** of `(hash, key, value)` in insertion order. This uses less memory than one sparse table, makes iteration fast, and is why dicts keep insertion order (guaranteed since 3.7).

- The table is resized when it is 2/3 full, so a few inserts are slow (O(n) copy) but the average is O(1).
- Deleting leaves a **dummy** (tombstone) marker so probe chains stay intact; dummies are cleared on the next resize.
- `hash(-1)` is −2, because −1 signals an error in C. Integer hashes are the value modulo the prime 2⁶¹ − 1. Equal numbers hash equally (`hash(1) == hash(1.0) == hash(True)`), so they are the same key.
- **Hash randomisation**: `str` and `bytes` hashes use a random seed per process (set `PYTHONHASHSEED` to fix it), which blocks collision attacks. Never rely on set iteration order or store `hash()` values across runs.
- If many keys collide, each insert scans the chain, and building the dict becomes O(n²) (below: doubling n quadruples the time).
- **Instance attributes**: since 3.13, ordinary objects store their attributes in an inline array, laid out by a key table shared by every instance of the class. A real `__dict__` is only created if you access it. `__slots__` still uses the least memory and blocks new attributes.
- **set** uses its own table (no entries array, so no ordering), with a short **linear probe** of several neighbouring slots before jumping, which is cache-friendly. Set algebra (`a & b`) loops over the smaller set.

```python
import sys
import time
import tracemalloc

# Hashes: ints hash to themselves (mod 2**61 - 1), except -1 which is reserved for errors
print("hash(42), hash(-1), hash(-2):", hash(42), hash(-1), hash(-2))
print("hash(2**61 - 1):", hash(2**61 - 1), " equal values hash equal:", hash(1) == hash(1.0) == hash(True))

# Compact dict: an index table (sparse) + an entries array (dense, insertion order)
d, sizes = {}, []
for i in range(40):
    d[i] = i
    s = sys.getsizeof(d)
    if not sizes or s != sizes[-1][1]:
        sizes.append((len(d), s))
print("(len, bytes) when the dict resizes:", sizes)


# Collisions: every key with the same hash turns lookups into a linear probe
class Bad:
    __slots__ = ("v",)

    def __init__(self, v: int) -> None:
        self.v = v

    def __hash__(self) -> int:
        return 0                       # every key collides

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Bad) and self.v == other.v


for n in (500, 1000, 2000):
    t = time.perf_counter()
    _ = {Bad(i): i for i in range(n)}
    print(f"n={n}: {time.perf_counter() - t:.3f}s to build (quadratic)")

# Instance attributes: since 3.13 plain objects store attributes inline and only build a
# real dict if you touch __dict__. Measure real allocations, not getsizeof.
class P:
    def __init__(self) -> None:
        self.a, self.b, self.c = 1, 2, 3


class S:
    __slots__ = ("a", "b", "c")

    def __init__(self) -> None:
        self.a, self.b, self.c = 1, 2, 3


def bytes_per_object(cls: type, touch_dict: bool = False, n: int = 10_000) -> float:
    tracemalloc.start()
    objs = [cls() for _ in range(n)]
    if touch_dict:
        for o in objs:
            _ = o.__dict__              # forces a real dict per object
    used = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()
    return (used - sys.getsizeof(objs)) / n


print(f"bytes per object: plain {bytes_per_object(P):.0f}, after touching __dict__ "
      f"{bytes_per_object(P, touch_dict=True):.0f}, __slots__ {bytes_per_object(S):.0f}")
```

Output:

```text
hash(42), hash(-1), hash(-2): 42 -2 -2
hash(2**61 - 1): 0  equal values hash equal: True
(len, bytes) when the dict resizes: [(1, 224), (6, 352), (11, 632), (22, 1168)]
n=500: 0.007s to build (quadratic)
n=1000: 0.028s to build (quadratic)
n=2000: 0.112s to build (quadratic)
bytes per object: plain 96, after touching __dict__ 160, __slots__ 56
```

Times vary by machine; the 4× ratio per doubling is the point.

---

## 4. str

- Strings are immutable sequences of Unicode code points. Under **PEP 393** ("flexible string representation") each string picks 1, 2 or 4 bytes per character, based on its widest character: ASCII and Latin-1 use 1, most other scripts 2, emoji and rare characters 4. One emoji makes the whole string 4× bigger.
- `len(s)` and `s[i]` are O(1), because the width is fixed within each string.
- **Interning**: identifier-like literals in your code and attribute names are stored once and shared, so dict lookups on them compare pointers. Strings built at run time are separate objects; `sys.intern` shares them (useful for millions of repeated symbol names).
- Repeated `s += t` copies the whole string each time: O(n²) in total. CPython can sometimes resize in place when nothing else references the string, but don't rely on it; use `"".join(parts)`.

```python
import sys

# str (PEP 393): each string uses 1, 2 or 4 bytes per character, set by its widest character
for s in ("a" * 100, "é" * 100, "€" * 100, "😀" * 100):
    print(f"{s[0]!r}: {sys.getsizeof(s)} bytes for 100 chars")
print("one emoji makes the whole string 4 bytes per char:", sys.getsizeof("a" * 99 + "😀"))

# Interning: identifier-like literals are shared; runtime strings are not unless interned
prefix = "tick"
a = prefix + "_data"                 # built at runtime
b = prefix + "_data"
print("built at runtime, same object?", a is b, " after sys.intern:", sys.intern(a) is sys.intern(b))

# Strings are immutable; += in a loop may copy. CPython sometimes resizes in place when the
# string has a single reference, but don't rely on it: use "".join(parts).
parts = [str(i) for i in range(5)]
print("".join(parts))
```

Output:

```text
'a': 141 bytes for 100 chars
'é': 157 bytes for 100 chars
'€': 258 bytes for 100 chars
'😀': 460 bytes for 100 chars
one emoji makes the whole string 4 bytes per char: 460
built at runtime, same object? False  after sys.intern: True
01234
```

---

## 5. collections and heapq

| Type | Under the hood | Consequences |
|---|---|---|
| `deque` | Doubly linked list of fixed blocks of 64 pointers | O(1) `append`/`pop` at both ends; O(n) indexing in the middle; `maxlen` makes a ring buffer |
| `OrderedDict` | A dict plus a doubly linked list of its keys | O(1) `move_to_end`, `popitem(last=False)`: the classic LRU cache. About twice the memory of a dict |
| `defaultdict` | A dict subclass whose `__missing__` calls `default_factory` and inserts the result | Reading a missing key *inserts* it: use `in` or `.get` to test |
| `Counter` | A dict subclass of counts | `most_common(k)` uses `heapq.nlargest`: O(n log k) |
| `heapq` | Functions on a plain list kept as a binary min-heap: `h[k] <= h[2k+1]` and `h[2k+2]` | `heapify` O(n); push/pop O(log n); no decrease-key, so use lazy deletion |
| `bisect` | Binary search on a sorted list | Search O(log n), but `insort` is O(n) because the list shifts |
| `queue.Queue` | A deque plus a lock and condition variables | Thread-safe hand-off between threads; slower than a bare deque |

```python
import heapq
import sys
from collections import Counter, OrderedDict, defaultdict, deque

# deque: a doubly linked list of fixed blocks of 64 pointers -> O(1) at both ends,
# but O(n) to index the middle. Memory grows one block at a time.
dq, steps = deque(), []
for i in range(200):
    dq.append(i)
    s = sys.getsizeof(dq)
    if not steps or s != steps[-1][1]:
        steps.append((len(dq), s))
print("deque (len, bytes) at each new block:", steps)

# OrderedDict: a dict plus a doubly linked list of keys -> move_to_end and popitem(last=False)
# are O(1), at roughly twice the memory of a dict
od, d = OrderedDict.fromkeys(range(1000)), dict.fromkeys(range(1000))
print("OrderedDict vs dict bytes:", sys.getsizeof(od), sys.getsizeof(d))
od.move_to_end(0)
print("after move_to_end(0), first key:", next(iter(od)))

# defaultdict calls default_factory inside __missing__; plain dict.get does not insert
dd = defaultdict(list)
dd["x"].append(1)
print("defaultdict:", dict(dd), " reading a missing key inserts it:", dd["y"], "->", sorted(dd))

# Counter is a dict subclass; most_common(k) uses heapq.nlargest: O(n log k)
print(Counter("mississippi").most_common(2))

# heapq: a plain list with heap[k] <= heap[2k+1], heap[2k+2]; the minimum is heap[0]
h = [5, 1, 8, 3, 9, 2]
heapq.heapify(h)                       # O(n), bottom-up
print("heapified:", h, " invariant holds:",
      all(h[k] <= h[c] for k in range(len(h)) for c in (2 * k + 1, 2 * k + 2) if c < len(h)))
```

Output:

```text
deque (len, bytes) at each new block: [(1, 760), (33, 1288), (97, 1816), (161, 2344)]
OrderedDict vs dict bytes: 85400 36952
after move_to_end(0), first key: 1
defaultdict: {'x': [1]}  reading a missing key inserts it: [] -> ['x', 'y']
[('i', 4), ('s', 4)]
heapified: [1, 3, 2, 5, 9, 8]  invariant holds: True
```

The deque starts with one block and grows by one block of 64 slots at a time (the first block is entered in the middle, so it fills after 32).

---

## 6. Sorting: Timsort

`list.sort` and `sorted` use **Timsort**, a merge sort tuned for real data:
1. Scan for **runs**: stretches that are already ascending (or strictly descending, which it reverses).
2. Extend short runs to a minimum length (32–64) with binary insertion sort.
3. Merge runs from a stack, choosing the order by the **powersort** policy (since 3.11), which keeps merges balanced.
4. While merging, if one side keeps winning, switch to **galloping**: exponential search for where the other side's next item goes, skipping long blocks in O(log n) comparisons.

Results: O(n) on sorted or reversed input, O(n log n) worst case, **stable** (equal keys keep their order), and n/2 extra memory at most. It counts only `<` comparisons, so define `__lt__` (or pass `key=`) for custom types.

```python
import random
from functools import total_ordering


@total_ordering
class Counted:
    """Wraps a value and counts comparisons, to see how much work sorting does."""

    count = 0
    __slots__ = ("v",)

    def __init__(self, v: int) -> None:
        self.v = v

    def __lt__(self, other: "Counted") -> bool:
        Counted.count += 1
        return self.v < other.v

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Counted) and self.v == other.v


def comparisons(data: list[int]) -> int:
    Counted.count = 0
    sorted(Counted(x) for x in data)
    return Counted.count


n = 10_000
rng = random.Random(0)
cases = {
    "already sorted": list(range(n)),
    "reversed": list(range(n, 0, -1)),
    "two sorted runs": list(range(0, n, 2)) + list(range(1, n, 2)),
    "sorted + 10 random at end": list(range(n - 10)) + [rng.randrange(n) for _ in range(10)],
    "random": rng.sample(range(n), n),
}
for name, data in cases.items():
    print(f"{name:26s} {comparisons(data):7d} comparisons")
print(f"n log2 n = {n * n.bit_length():,} (roughly)")

# Stability: equal keys keep their input order, so you can sort by several keys in passes
trades = [("MSFT", 3), ("AAPL", 1), ("MSFT", 1), ("AAPL", 2)]
by_qty = sorted(trades, key=lambda t: t[1])
print(sorted(by_qty, key=lambda t: t[0]))       # by symbol, then quantity
```

Output:

```text
already sorted                9999 comparisons
reversed                      9999 comparisons
two sorted runs              19999 comparisons
sorted + 10 random at end    10219 comparisons
random                      120201 comparisons
n log2 n = 140,000 (roughly)
[('AAPL', 1), ('AAPL', 2), ('MSFT', 1), ('MSFT', 3)]
```

`key=` functions are called once per item (decorate-sort-undecorate), so an expensive key is computed n times, not n log n times.

---

## 7. The interpreter: bytecode and specialisation

- Source is compiled to **bytecode** (`.pyc` files in `__pycache__`), run by an evaluation loop in C. `dis.dis(fn)` shows it.
- **Specialising adaptive interpreter** (3.11+): after an instruction has run a few times, it is rewritten in place for the types actually seen, e.g. `BINARY_OP` → `BINARY_OP_ADD_INT`, `LOAD_ATTR` → `LOAD_ATTR_INSTANCE_VALUE`. If the types change, it falls back to the generic version. This is why code with stable types runs faster.
- 3.14 adds "borrowed" loads (`LOAD_FAST_BORROW`) that skip reference-count updates when it is safe.
- **JIT compiler**: an experimental copy-and-patch JIT exists since 3.13 (built with `--enable-experimental-jit`; off by default). It compiles hot traces of specialised instructions to machine code.
- Local variables live in an array in the frame (fast, by index); globals and built-ins are dict lookups, which is why a local alias is faster in a tight loop.

```python
import dis


def total(xs: list[int]) -> int:
    s = 0
    for x in xs:
        s += x
    return s


def ops(fn, adaptive: bool) -> list[str]:
    """Names of the bytecode instructions in the loop body (generic or specialised)."""
    names = [i.opname for i in dis.get_instructions(fn, adaptive=adaptive)]
    return [n for n in names if n.startswith(("BINARY_OP", "FOR_ITER", "LOAD_FAST", "STORE_FAST"))]


print("before running:", ops(total, adaptive=False))
for _ in range(1000):                 # warm up: the interpreter watches the types it sees
    total(list(range(10)))
print("after warm-up: ", ops(total, adaptive=True))
```

Output:

```text
before running: ['STORE_FAST', 'LOAD_FAST_BORROW', 'FOR_ITER', 'STORE_FAST', 'LOAD_FAST_BORROW_LOAD_FAST_BORROW', 'BINARY_OP', 'STORE_FAST', 'LOAD_FAST_BORROW']
after warm-up:  ['STORE_FAST', 'LOAD_FAST_BORROW', 'FOR_ITER_LIST', 'STORE_FAST', 'LOAD_FAST_BORROW_LOAD_FAST_BORROW', 'BINARY_OP_ADD_INT', 'STORE_FAST', 'LOAD_FAST_BORROW']
```

---

## 8. Memory management

1. **Reference counting**: every new reference increments the count, every lost reference decrements it, and the object is freed the moment the count reaches 0 (deterministic, which is why files often close promptly).
2. **Cycle collector** (`gc` module): objects in a reference cycle never reach 0. The collector tracks container objects and periodically finds groups reachable only from each other. It uses generations (new objects are scanned most often), and from 3.14 it is **incremental**: it scans the old generation a piece at a time, cutting long pauses.
3. **`weakref`**: a reference that does not raise the count, for caches and back-pointers (child → parent) without creating cycles.
4. **pymalloc**: small objects (≤ 512 bytes) come from a dedicated allocator that carves large **arenas** into **pools** of same-size blocks. It is fast, but memory freed inside an arena returns to the OS only when the whole arena is empty, so a process's memory use can stay high after you free many objects.
5. **`__del__`** (finalisers) runs when the object is freed; avoid it for important clean-up, and use `with` (context managers) instead.

```python
import gc
import weakref


class Node:
    def __init__(self, name: str) -> None:
        self.name = name
        self.other: Node | None = None


def on_free(name: str):
    return lambda _ref: print(f"  freed {name}")


# 1) Reference counting frees an object the moment its last reference goes
print("refcount:")
a = Node("a")
ref = weakref.ref(a, on_free("a"))       # a weak reference does not keep `a` alive
del a                                    # count hits 0 -> freed immediately
print("  weakref now points to:", ref())

# 2) A cycle keeps both counts above 0, so only the cycle collector can free it
print("cycle:")
gc.disable()
x, y = Node("x"), Node("y")
x.other, y.other = y, x
rx, ry = weakref.ref(x, on_free("x")), weakref.ref(y, on_free("y"))
del x, y
print("  after del, still alive:", rx() is not None and ry() is not None)
print("  gc.collect() found", gc.collect(), "unreachable objects")
gc.enable()

# 3) Break cycles yourself with weakref (e.g. child -> parent links)
print("thresholds (generation 0 triggers):", gc.get_threshold()[0])
```

Output:

```text
refcount:
  freed a
  weakref now points to: None
cycle:
  after del, still alive: True
  freed x
  freed y
  gc.collect() found 14 unreachable objects
thresholds (generation 0 triggers): 2000
```

The collector reports more than two objects because each `Node` also owns attribute storage and the weak-reference callbacks; `gc.collect()` counts every unreachable container it frees.

---

## 9. Attribute lookup, descriptors and the MRO

`obj.attr` follows this order (implemented in `object.__getattribute__`):
1. A **data descriptor** on the class (defines `__set__` or `__delete__`, e.g. `property`): call its `__get__`.
2. The instance's own attributes (`__dict__` or inline values).
3. A **non-data descriptor** (only `__get__`, e.g. a plain function) or other class attribute.
4. If all fail: `__getattr__`, if defined.

- Functions are non-data descriptors: `obj.method` returns a new **bound method** object each time (cheap, but measurable in hot loops, so bind it to a local).
- `property`, `classmethod`, `staticmethod` and `__slots__` are all descriptors.
- **MRO** (method resolution order): for multiple inheritance, Python computes a **C3 linearisation**: a list of classes where each class comes before its parents and the order of bases is kept. `super()` means "the next class in the MRO of the instance", not "my parent", which is what makes cooperative multiple inheritance work.

```python
class Positive:
    """A data descriptor: validates on assignment. Lives on the class, not the instance."""

    def __set_name__(self, owner: type, name: str) -> None:
        self.private = "_" + name

    def __get__(self, obj, objtype=None):
        return self if obj is None else getattr(obj, self.private)

    def __set__(self, obj, value: float) -> None:
        if value <= 0:
            raise ValueError(f"{self.private[1:]} must be > 0, got {value}")
        setattr(obj, self.private, value)


class Option:
    vol = Positive()                         # data descriptor: beats the instance dict
    expiry = Positive()

    def __init__(self, vol: float, expiry: float) -> None:
        self.vol, self.expiry = vol, expiry

    def __getattr__(self, name: str):        # only called when normal lookup FAILS
        return f"<no {name}>"


o = Option(0.2, 1.0)
print(o.vol, o.missing)
try:
    o.vol = -1
except ValueError as e:
    print("ValueError:", e)

# Functions are non-data descriptors: o.method creates a bound method on each access
print("bound method created on each access:", Option.__init__.__get__(o) is not Option.__init__.__get__(o))


# MRO (method resolution order) uses C3 linearisation: children before parents,
# left-to-right order of bases kept, each class once
class Base:
    def name(self) -> str:
        return "Base"


class Rates(Base):
    def name(self) -> str:
        return "Rates>" + super().name()


class Vol(Base):
    def name(self) -> str:
        return "Vol>" + super().name()


class RatesVol(Rates, Vol):
    def name(self) -> str:
        return "RatesVol>" + super().name()


print([c.__name__ for c in RatesVol.__mro__])
print(RatesVol().name())                  # super() follows the MRO, not the parent class
```

Output:

```text
0.2 <no missing>
ValueError: vol must be > 0, got -1
bound method created on each access: True
['RatesVol', 'Rates', 'Vol', 'Base', 'object']
RatesVol>Rates>Vol>Base
```

---

## 10. Generators, itertools and lru_cache

- A **generator** is a function whose frame (local variables and instruction pointer) is kept on the heap between `next` calls, so it uses constant memory for an infinite stream. `yield from` delegates to a sub-generator; `async def` coroutines use the same machinery.
- **itertools** functions are C iterators: lazy, constant memory, fast. `tee` stores the items one copy has consumed and the other has not, so it can use unbounded memory if one copy runs far ahead.
- **`functools.lru_cache`** (C implementation): a dict from an argument key to a node in a circular doubly linked list ordered by use. A hit moves the node to the front; a miss at `maxsize` evicts the back. O(1) both ways. Arguments must be hashable. The cache holds strong references, so caching methods on `self` keeps instances alive.
- `functools.cache` is `lru_cache(maxsize=None)`: no linked list, just a dict, and slightly faster.

```python
import functools
import itertools
import sys

# Generators keep a suspended frame: O(1) memory however long the stream
gen = (x * x for x in range(10**9))
print("generator object bytes:", sys.getsizeof(gen), " first values:", list(itertools.islice(gen, 3)))

# itertools are lazy C iterators; tee buffers what one copy has seen and the other has not
a, b = itertools.tee(range(5))
print("tee:", list(a), list(b))


# lru_cache: a dict from argument key to a node in a circular doubly linked list (C code)
@functools.lru_cache(maxsize=2)
def price(k: int) -> int:
    print(f"  computing {k}")
    return k * 10


for k in (1, 2, 1, 3, 2):               # 3 evicts 2 (least recently used), so 2 is recomputed
    price(k)
print(price.cache_info())

# Gotcha: 1 == 1.0 and hash(1) == hash(1.0), yet they get separate entries. The C key builder uses
# a lone int or str argument as the key itself but wraps other types in a tuple, and 1 != (1.0,).
price.cache_clear()
price(1)
price(1.0)
print("1 and 1.0 share an entry:", price.cache_info().hits == 1)     # False
```

Output:

```text
generator object bytes: 208  first values: [0, 1, 4]
tee: [0, 1, 2, 3, 4] [0, 1, 2, 3, 4]
  computing 1
  computing 2
  computing 3
  computing 2
CacheInfo(hits=1, misses=4, maxsize=2, currsize=2)
  computing 1
  computing 1.0
1 and 1.0 share an entry: False
```

---

## 11. The GIL and free-threaded Python

- The **GIL** (global interpreter lock) lets only one thread run Python bytecode at a time. It makes reference counting and the built-in containers safe without fine-grained locks. A running thread is asked to release it every 5 ms (`sys.getswitchinterval()`), and C code releases it around blocking I/O and long computations (NumPy, hashing, compression).
- **Atomic** under the GIL: single bytecode operations on built-in types, e.g. `list.append`, `dict[k] = v`, `deque.popleft`. **Not atomic**: `x += 1`, `d[k] = d.get(k, 0) + 1`, check-then-act sequences. Use a `Lock`.
- **Free-threaded build** (`python3.14t`, officially supported in 3.14): no GIL. Each object gets a per-thread owner for fast reference counting (**biased reference counting**), containers get per-object locks, and memory is freed only once no thread could still be reading it. Pure-Python code can then use all cores; single-thread code is somewhat slower, and C extensions must declare themselves safe. Check with `sys._is_gil_enabled()`.
- The safest code works the same either way: share data through `queue.Queue` and protect compound updates with locks.

---

## 12. Interview questions

1. **Why is `append` amortised O(1)?** Capacity grows geometrically (about ×1.125 plus a constant), so over n appends the total copying is proportional to n.
2. **Why are dict lookups O(1) on average but O(n) in the worst case?** Hashing picks a slot directly; with many collisions, probing visits many slots. Hash randomisation for strings defends against crafted collisions.
3. **Why do dicts preserve insertion order?** The compact layout stores entries in a dense array in insertion order, with a separate index table for hashing.
4. **What happens if you mutate a key after inserting it?** Its hash changes, so lookups probe the wrong slot and the entry becomes unreachable. That is why mutable built-ins (`list`, `dict`, `set`) are unhashable.
5. **Why can `a is b` be True for 256 and False for 257?** Small ints −5..256 are cached singletons; larger ones are separate objects. Use `==`.
6. **Why is `sorted` fast on nearly sorted data?** Timsort finds existing runs and gallops through long one-sided merges: O(n) for sorted input.
7. **When does memory not go back to the OS after `del`?** pymalloc returns an arena only when all its blocks are free; scattered survivors keep arenas alive. Fixes: process large batches in a subprocess, use NumPy arrays, or reuse objects.
8. **How does `super()` decide which method to call?** It finds the next class after the current one in the instance's MRO (C3 linearisation).
9. **Why are local variables faster than globals?** Locals are read from an array by index; globals need a dict lookup (and built-ins a second one).
10. **Is `x += 1` thread-safe?** No: it is a load, an add and a store, and a thread switch can happen between them, with or without the GIL.
11. **Why might `@lru_cache` on a method cause a memory leak?** The cache keeps `self` alive in its keys. Use a per-instance cache or `functools.cached_property`.
12. **What does `__slots__` save, and what does it cost?** It removes per-instance attribute dictionaries (here 160 → 56 bytes per object once `__dict__` is touched), but instances can't get new attributes, and multiple inheritance with slots needs care.

---

## 13. Glossary

| Term | Meaning |
|---|---|
| Amortised O(1) | Average cost per operation over many operations, despite occasional slow ones |
| Arena / pool | pymalloc's big memory chunks and their same-size-block subdivisions |
| Biased reference counting | Free-threaded scheme: the owning thread updates a count cheaply, others use atomic operations |
| Bound method | A function object paired with the instance it was looked up on |
| Bytecode | Instructions for Python's virtual machine, compiled from source |
| C3 linearisation | The algorithm that orders classes for method lookup in multiple inheritance |
| Compact dict | Dict layout with a sparse index table pointing into a dense, ordered entries array |
| Cycle collector | The part of `gc` that frees groups of objects that only reference each other |
| Descriptor | An object on a class defining `__get__` / `__set__`, which controls attribute access |
| Galloping | Exponential search used by Timsort when one run keeps winning a merge |
| GIL | Global interpreter lock: one thread runs Python bytecode at a time |
| Immortal object | An object whose reference count never changes (3.12+) |
| Interning | Storing one shared copy of equal strings |
| MRO | Method resolution order: the class search order for attribute lookup |
| Perturbed probing | Dict collision strategy that mixes higher hash bits into each probe |
| PEP 393 | Flexible string storage: 1, 2 or 4 bytes per character per string |
| pymalloc | CPython's allocator for objects of 512 bytes or less |
| Reference count | Number of references to an object; it is freed at zero |
| Specialisation | Rewriting a bytecode instruction for the types it actually sees (3.11+) |
| Timsort | Python's adaptive, stable merge sort that exploits existing runs |
| Tombstone (dummy) | Marker left in a hash table slot after a delete, to keep probe chains intact |
| Weak reference | A reference that does not keep its object alive |
