# Python References and Copies

One mental model that explains every "why did that change?" moment in Python, then the copy
tools, the common traps, and how NumPy and pandas differ. Each term is explained the first time it
appears; a glossary is at the end.

Every code block runs on its own (`uv run python file.py`); the block after it shows its real
output. Related: [Python page](README.md), [Python under the hood](internals.md).

Contents:

1. [The one mental model: names are labels](#1-the-one-mental-model-names-are-labels)
2. [Mutable vs immutable](#2-mutable-vs-immutable)
3. [Function arguments](#3-function-arguments)
4. [The mutable default argument](#4-the-mutable-default-argument)
5. [Shallow copy vs deep copy](#5-shallow-copy-vs-deep-copy)
6. [Which copy does each tool make?](#6-which-copy-does-each-tool-make)
7. [Seven traps](#7-seven-traps)
8. [NumPy views and pandas Copy-on-Write](#8-numpy-views-and-pandas-copy-on-write)
9. [Controlling copies: deepcopy, custom copies, immutability](#9-controlling-copies-deepcopy-custom-copies-immutability)
10. [Decision guide](#10-decision-guide)
11. [Interview questions](#11-interview-questions)
12. [Glossary](#12-glossary)

---

## 1. The one mental model: names are labels

A Python variable is **not a box that holds a value**. It is a **label (a name) attached to an
object**. Objects live separately; names just point at them.

```
a = [1, 2, 3]          a ──►  [1, 2, 3]

b = a                  a ──►  [1, 2, 3]   ◄── b      (one object, two labels)

b.append(4)            a ──►  [1, 2, 3, 4] ◄── b     (the object changed; both labels see it)

b = [9]                a ──►  [1, 2, 3, 4]
                       b ──►  [9]                    (b moved to a new object; a unaffected)
```

Two rules follow, and they explain almost everything:

1. **`=` never copies.** It attaches a name to an object. Copying only happens when you ask for it.
2. There are two different kinds of "change":
   - **Mutating** the object (`append`, `x[0] = ...`, `d["k"] = ...`, `.update`, `+=` on a list): everyone pointing at it sees the change.
   - **Rebinding** the name (`b = something`): only that name moves; other names and the object are untouched.

Tools to check: `a is b` asks "same object?"; `a == b` asks "equal values?"; `id(a)` is the object's identity.

```python
# Assignment never copies: it puts a second label on the SAME object
a = [1, 2, 3]
b = a
b.append(4)
print(a, b, a is b)            # both labels see the change

# Rebinding moves a label to a NEW object; the other label is untouched
b = [9]
print(a, b, a is b)
```

Output:

```text
[1, 2, 3, 4] [1, 2, 3, 4] True
[1, 2, 3, 4] [9] False
```

---

## 2. Mutable vs immutable

- **Immutable** objects can never change after creation: `int`, `float`, `bool`, `str`, `tuple`, `frozenset`, `bytes`, `None`. Any "change" builds a new object and rebinds the name. So sharing them is always safe.
- **Mutable** objects can change in place: `list`, `dict`, `set`, `bytearray`, most class instances, NumPy arrays, DataFrames. Sharing them means sharing changes.
- **`+=` depends on the type**: for a list it means "extend in place" (mutation); for an int or str it means "make a new object" (rebinding). `x = x + y` always builds a new object.

```python
# Immutable objects (int, float, str, tuple) can't change, so "changing" makes a new object
x = 10
y = x
y += 1                          # builds a new int 11 and moves the label y
print(x, y)

s = "abc"
t = s
t += "d"                        # new string
print(s, t)

# Mutable objects (list, dict, set) change in place, so every label sees it
p = [1, 2]
q = p
q += [3]                        # for a list, += is extend: IN PLACE
print(p, q)

q = q + [4]                     # + builds a NEW list, then rebinds q
print(p, q)
```

Output:

```text
10 11
abc abcd
[1, 2, 3] [1, 2, 3]
[1, 2, 3] [1, 2, 3, 4]
```

---

## 3. Function arguments

Python passes **the object itself** to a function, and the parameter becomes a new label on it.
This is called **call by sharing** (or pass-by-object-reference). It is neither "pass by value"
(no copy is made) nor "pass by reference" (the function can't rebind the caller's variable).

- Mutating the argument inside the function → the caller sees it.
- Rebinding the parameter inside the function → the caller does **not** see it.
- Immutable arguments therefore behave as if passed by value.

```python
# Function arguments: the parameter is a new label on the caller's object
# ("call by sharing", also called pass-by-object-reference)

def add_item(lst: list[int]) -> None:
    lst.append(99)              # mutates the caller's list


def replace(lst: list[int]) -> None:
    lst = [0]  # noqa: F841     only moves the LOCAL label; caller unaffected


def bump(n: int) -> None:
    n += 1                      # int is immutable: local label now points to a new int


nums, count = [1, 2], 5
add_item(nums)
replace(nums)
bump(count)
print(nums, count)


# To "return a changed version" without touching the input, copy first
def with_item(lst: list[int]) -> list[int]:
    return [*lst, 99]           # new list


print(with_item([1, 2]))
```

Output:

```text
[1, 2, 99] 5
[1, 2, 99]
```

Good practice: a function should *either* change its input (and return `None`, like `list.sort`)
*or* return a new object and leave the input alone (like `sorted`), and its name should make clear which.

---

## 4. The mutable default argument

Default values are created **once, when the `def` statement runs**, not on each call. A mutable
default is therefore one shared object that keeps every call's changes. Use `None` and create the
object inside.

```python
# The mutable default argument trap: the default is created ONCE, when `def` runs
def log_bad(msg: str, history: list[str] = []) -> list[str]:  # noqa: B006 (shown on purpose)
    history.append(msg)
    return history


print(log_bad("a"), log_bad("b"))          # the same list, shared across calls


def log_good(msg: str, history: list[str] | None = None) -> list[str]:
    history = [] if history is None else history
    history.append(msg)
    return history


print(log_good("a"), log_good("b"))
```

Output:

```text
['a', 'b'] ['a', 'b']
['a'] ['b']
```

---

## 5. Shallow copy vs deep copy

- A **shallow copy** creates a new *outer* container, but fills it with **the same inner objects** (the same references). Changing the outer level of the copy is independent; changing an inner mutable object is shared.
- A **deep copy** (`copy.deepcopy`) copies the whole structure recursively, so nothing mutable is shared.

```
book    ──► { "desk": "rates", "trades": ─┐ }
                                          ├──► [ {id 1, qty 10} ]   ◄── shared by a shallow copy
shallow ──► { "desk": "rates", "trades": ─┘ }

deep    ──► { "desk": "rates", "trades": ───► [ {id 1, qty 10} ] }  (its own list and dicts)
```

```python
import copy

book = {"desk": "rates", "trades": [{"id": 1, "qty": 10}]}

alias = book                     # same object
shallow = copy.copy(book)        # new outer dict, SAME inner list and dicts
deep = copy.deepcopy(book)       # new everything, all the way down

book["desk"] = "credit"          # change the outer level
book["trades"][0]["qty"] = 0     # change an inner object
book["trades"].append({"id": 2, "qty": 5})

print("alias:  ", alias)
print("shallow:", shallow)
print("deep:   ", deep)
print("shallow shares the inner list:", shallow["trades"] is book["trades"])
print("deep shares the inner list:   ", deep["trades"] is book["trades"])
```

Output:

```text
alias:   {'desk': 'credit', 'trades': [{'id': 1, 'qty': 0}, {'id': 2, 'qty': 5}]}
shallow: {'desk': 'rates', 'trades': [{'id': 1, 'qty': 0}, {'id': 2, 'qty': 5}]}
deep:    {'desk': 'rates', 'trades': [{'id': 1, 'qty': 10}]}
shallow shares the inner list: True
deep shares the inner list:    False
```

Read the output row by row: the alias saw everything; the shallow copy kept its own `"desk"` but
shares the trades list (so it saw the new trade and the qty change); the deep copy saw nothing.

---

## 6. Which copy does each tool make?

| Expression | Kind | Note |
|---|---|---|
| `b = a` | **no copy** (alias) | same object |
| `a[:]`, `list(a)`, `a.copy()`, `[*a]`, `copy.copy(a)` | shallow | lists |
| `dict(d)`, `d.copy()`, `{**d}`, `d \| {}` | shallow | dicts |
| `set(s)`, `s.copy()` | shallow | sets |
| `[row.copy() for row in grid]` | one level deeper | often all you need for a list of lists |
| `copy.deepcopy(x)` | deep | slower; handles shared parts and cycles |
| `tuple(t)`, `str(s)` on the same type | **no copy** | immutable, so Python just returns the same object |
| `np_array[1:3]` | **view** (no copy) | see section 8 |
| `np_array.copy()`, `np.array(x)` | copy | |
| `df.copy()` / any derived DataFrame (pandas 3) | behaves as a copy | Copy-on-Write, see section 8 |

```python
import copy

nested = [[1, 2], [3, 4]]

# All of these are SHALLOW: new outer list, same inner lists
for name, c in [("slice", nested[:]), ("list()", list(nested)), (".copy()", nested.copy()),
                ("copy.copy", copy.copy(nested)), ("[*x]", [*nested]),
                ("comprehension", [row for row in nested])]:
    print(f"{name:14s} new outer: {c is not nested}   same inner: {c[0] is nested[0]}")

# A copy one level deeper, often all you need (and faster than deepcopy)
rows = [row.copy() for row in nested]
rows[0][0] = 100
print("row copies:", nested, rows)

# dict(d), d.copy(), {**d}, set(s), s.copy() are shallow too
d = {"k": [1]}
d2 = {**d}
d2["k"].append(2)
print("shallow dict:", d)
```

Output:

```text
slice          new outer: True   same inner: True
list()         new outer: True   same inner: True
.copy()        new outer: True   same inner: True
copy.copy      new outer: True   same inner: True
[*x]           new outer: True   same inner: True
comprehension  new outer: True   same inner: True
row copies: [[1, 2], [3, 4]] [[100, 2], [3, 4]]
shallow dict: {'k': [1, 2]}
```

---

## 7. Seven traps

1. **`[[0] * 3] * 3`** makes three references to *one* row. Use `[[0] * 3 for _ in range(3)]`.
2. **`dict.fromkeys(keys, [])`** gives every key the same list. Use `{k: [] for k in keys}` or `defaultdict(list)`.
3. **A mutable class attribute** (`trades = []` in the class body) is shared by every instance. Create it in `__init__`.
4. **Appending the same object in a loop** (`row = {}` outside the loop) gives a list of identical references. Create the object inside the loop.
5. **Late-binding closures**: `lambda: i` captures the *variable* `i`, read when called, not its value when the lambda was made. Bind it as a default: `lambda i=i: i`.
6. **A tuple holding a list**: the tuple can't be changed, but the list inside can. `t[0] += [3]` mutates the list *and then* raises `TypeError` when it tries to store into the tuple.
7. **Changing a list while looping over it** skips items, because the loop's index keeps moving while items shift. Build a new list (comprehension) or loop over a copy (`for x in xs[:]`).

```python
# Trap 1: * repeats the REFERENCE
grid = [[0] * 3] * 3
grid[0][0] = 1
print("1.", grid)

# Trap 2: dict.fromkeys with a mutable value shares one object between all keys
by_desk = dict.fromkeys(["rates", "fx"], [])  # noqa: RUF024 (shown on purpose)
by_desk["rates"].append("trade-1")
print("2.", by_desk)
print("   fix:", {k: [] for k in ["rates", "fx"]})


# Trap 3: a mutable CLASS attribute is shared by every instance
class Book:
    trades: list[str] = []              # one list on the class  # noqa: RUF012 (shown on purpose)

    def add(self, t: str) -> None:
        self.trades.append(t)           # finds the class list, mutates it


b1, b2 = Book(), Book()
b1.add("x")
print("3.", b2.trades)                  # b2 sees b1's trade

# Trap 4: appending the same dict in a loop
rows, row = [], {}
for i in range(3):
    row["i"] = i                        # same dict every time
    rows.append(row)
print("4.", rows)

# Trap 5: closures capture VARIABLES, not values (late binding)
fs = [lambda: i for i in range(3)]       # noqa: B023 (shown on purpose)
print("5.", [f() for f in fs], " fix:", [f() for f in [lambda i=i: i for i in range(3)]])

# Trap 6: a tuple holding a list. The tuple can't change, but the list inside can
t = ([1], 2)
try:
    t[0] += [3]                         # the list IS extended, then the tuple assignment fails
except TypeError as e:
    print("6.", type(e).__name__, "but t is now", t)

# Trap 7: changing a list while looping over it skips items
xs = [1, 2, 2, 3]
for x in xs:
    if x == 2:
        xs.remove(x)
print("7.", xs, " fix:", [x for x in [1, 2, 2, 3] if x != 2])
```

Output:

```text
1. [[1, 0, 0], [1, 0, 0], [1, 0, 0]]
2. {'rates': ['trade-1'], 'fx': ['trade-1']}
   fix: {'rates': [], 'fx': []}
3. ['x']
4. [{'i': 2}, {'i': 2}, {'i': 2}]
5. [2, 2, 2]  fix: [0, 1, 2]
6. TypeError but t is now ([1, 3], 2)
7. [1, 2, 3]  fix: [1, 3]
```

---

## 8. NumPy views and pandas Copy-on-Write

**NumPy** avoids copying large arrays when it can:
- **Basic slicing** (`a[1:4]`, `a[:, 0]`), `reshape`, `.T` and `.view()` return a **view**: a new array object that points at the *same memory*. Writing to the view writes to the original.
- **Fancy indexing** (a list or array of indices) and **boolean masks** return a **copy**.
- Check with `np.shares_memory(a, b)`, or `b.base is a`. Call `.copy()` when you need independence (e.g. before returning a slice of a big array that you'll keep: a view keeps the whole original array alive).

**pandas 3** uses **Copy-on-Write** (CoW) everywhere:
- Every object derived from another (a column, a filtered frame, a slice) **behaves like an independent copy**; data is only physically copied when one of them is modified, so it stays cheap.
- So `sub = df[mask]; sub["px"] = 0` never changes `df` (no more `SettingWithCopyWarning`), and **chained assignment** like `df["px"][0] = 1` does nothing to `df`.
- To change a DataFrame, index it directly in one step: `df.loc[mask, "px"] = 0`.

```python
import numpy as np
import pandas as pd

# NumPy: basic slicing returns a VIEW (same memory); fancy or boolean indexing returns a COPY
a = np.arange(6)
view = a[1:4]
view[0] = 100
print("slice view changes a:  ", a)

b = np.arange(6)
picked = b[[1, 2, 3]]                     # fancy index -> copy
picked[0] = 100
print("fancy copy leaves b:   ", b)
print("shares memory?", np.shares_memory(a, view), np.shares_memory(b, picked))

base = np.arange(6)
c = base.reshape(2, 3)                    # reshape / transpose are views when possible
print("reshape is a view:", np.shares_memory(base, c))
safe = a[1:4].copy()                      # explicit copy when you need independence
print("explicit copy:", np.shares_memory(a, safe))

# pandas 3: Copy-on-Write. Every derived object BEHAVES like a copy; data is copied lazily
df = pd.DataFrame({"px": [100.0, 101.0, 102.0], "qty": [1, 2, 3]})
sub = df[df["qty"] > 1]
sub.loc[:, "px"] = 0.0                    # changes only sub
print("df unchanged:", df["px"].tolist(), " sub:", sub["px"].tolist())

col = df["px"]
col.iloc[0] = -1.0                        # changes only col, not df
print("df unchanged again:", df["px"].tolist())

df.loc[df["qty"] > 1, "px"] = 0.0         # the one right way to change df: index it directly
print("df after .loc:", df["px"].tolist())
```

Output:

```text
slice view changes a:   [  0 100   2   3   4   5]
fancy copy leaves b:    [0 1 2 3 4 5]
shares memory? True False
reshape is a view: True
explicit copy: False
df unchanged: [100.0, 101.0, 102.0]  sub: [0.0, 0.0]
df unchanged again: [100.0, 101.0, 102.0]
df after .loc: [100.0, 0.0, 0.0]
```

---

## 9. Controlling copies: deepcopy, custom copies, immutability

- `copy.deepcopy` keeps a **memo** (a dict of objects already copied), so shared sub-objects stay shared within the copy, and cycles don't loop forever.
- Define `__copy__` / `__deepcopy__` to control what gets copied, e.g. share a large read-only market data curve but give each copy its own cache.
- Prefer **immutable data** where you can: frozen dataclasses, tuples, `frozenset`. If nothing can change, sharing is always safe and you never need defensive copies. `dataclasses.replace(obj, field=new)` returns a modified copy.

```python
import copy
from dataclasses import dataclass, field, replace

# deepcopy keeps a memo of objects already copied, so shared parts and cycles survive
shared = [1, 2]
pair = [shared, shared]
dup = copy.deepcopy(pair)
print("sharing preserved:", dup[0] is dup[1], " but new:", dup[0] is not shared)

loop: list = []
loop.append(loop)                         # a list that contains itself
print("cycle copied:", copy.deepcopy(loop)[0] is not loop)


# Control copying with __copy__ / __deepcopy__, e.g. share a big read-only curve
class Pricer:
    def __init__(self, curve: list[float]) -> None:
        self.curve = curve                # large, read-only: share it
        self.cache: dict = {}             # per-copy state: don't share it

    def __deepcopy__(self, memo: dict) -> "Pricer":
        new = Pricer(self.curve)          # same curve object
        memo[id(self)] = new
        return new


p = Pricer([0.04] * 1000)
p.cache["x"] = 1
q = copy.deepcopy(p)
print("curve shared:", q.curve is p.curve, " cache fresh:", q.cache)


# Frozen dataclasses: no in-place changes, so sharing is always safe; replace() makes a new one
@dataclass(frozen=True)
class Trade:
    id: int
    qty: int
    tags: tuple[str, ...] = field(default=())   # tuple, not list, to stay truly immutable


t1 = Trade(1, 10)
t2 = replace(t1, qty=20)
print(t1, t2)
```

Output:

```text
sharing preserved: True  but new: True
cycle copied: True
curve shared: True  cache fresh: {}
Trade(id=1, qty=10, tags=()) Trade(id=1, qty=20, tags=())
```

---

## 10. Decision guide

| Situation | Do this |
|---|---|
| Passing data to a function that only reads it | Nothing: no copy needed |
| You will modify something the caller still owns | Copy first (`.copy()`), or return a new object instead |
| A list/dict of immutable items (numbers, strings) | Shallow copy is enough |
| A list of lists / dict of lists that you will modify inside | `[x.copy() for x in ...]` or `copy.deepcopy` |
| Default argument that's a list/dict/set | Default to `None`, create inside |
| Slicing a big NumPy array that you'll keep long-term | `.copy()` so the big array can be freed |
| Changing a pandas DataFrame | `df.loc[rows, cols] = value` in one step |
| Data many parts of a program share | Make it immutable (frozen dataclass, tuple) |

---

## 11. Interview questions

1. **Is Python pass-by-value or pass-by-reference?** Neither: call by sharing. The function receives the same object; mutations are visible to the caller, rebinding is not.
2. **What is the difference between `is` and `==`?** `is` compares identity (same object); `==` compares values (calls `__eq__`). Use `is` only for `None` and other singletons.
3. **Why does `x += [1]` change other names pointing to the list, but `x = x + [1]` doesn't?** List `+=` calls `__iadd__`, which extends in place; `+` builds a new list and rebinds `x`.
4. **When is a shallow copy not enough?** When the container holds mutable objects that you will change; the copy shares them.
5. **Why are mutable default arguments dangerous?** The default is evaluated once at function definition and shared by every call.
6. **Does slicing a list copy it? A NumPy array?** A list slice is a shallow copy. A NumPy basic slice is a view of the same memory.
7. **How does `deepcopy` handle a list that contains itself?** Its memo dict maps `id(original)` to the copy, so the second time it meets the same object it reuses the copy.
8. **Why can a tuple be unhashable?** A tuple is hashable only if everything inside is; `([1], 2)` contains a list, so `hash()` raises `TypeError`.

---

## 12. Glossary

| Term | Meaning |
|---|---|
| Alias | A second name for the same object |
| Call by sharing | Python's argument passing: the parameter is a new name for the caller's object |
| Chained assignment | `df["col"][row] = value`: two indexing steps; does not modify `df` under Copy-on-Write |
| Copy-on-Write (CoW) | Derived objects act as copies, but the data is copied only when one is modified |
| Deep copy | A recursive copy in which no mutable part is shared with the original |
| Identity | Which object a name refers to; compared with `is`, shown by `id()` |
| Immutable | Cannot change after creation (int, str, tuple, frozenset) |
| Late binding | A closure reads a variable's value when it runs, not when it was created |
| Memo (deepcopy) | The dict deepcopy uses to remember objects already copied |
| Mutable | Can change in place (list, dict, set, most objects, arrays) |
| Mutation | Changing an object in place, visible through every name that refers to it |
| Rebinding | Pointing a name at a different object; other names are unaffected |
| Shallow copy | A new outer container holding the same inner objects |
| View (NumPy) | An array object that shares memory with another array |
