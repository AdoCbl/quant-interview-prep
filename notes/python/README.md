# Python for Mid-Level and Senior Interviews

This page assumes you already know the basics: syntax, lists, dicts, classes, loops. It covers what interviewers use to tell mid-level and senior candidates from juniors:
- how Python works underneath,
- the traps,
- performance,
- concurrency,
- NumPy and pandas in depth.

All snippets were checked on Python 3.14, NumPy 2.5 and pandas 3.1. Abbreviations are spelled out the first time they appear, and a glossary is at the end.

---

## 1. Names, objects and mutability

Full walkthrough with diagrams, traps and NumPy/pandas behaviour: [references and copies](references-and-copies.md).

**Core idea**: a variable is a *name tag attached to an object*, not a box that holds a value. Assignment never copies; it just attaches another tag.

```python
a = [1, 2]
b = a          # b is the same list, not a copy
b.append(3)    # a is now [1, 2, 3] too
```

- **Mutable** (can change in place): list, dict, set, most user-defined objects.
- **Immutable**: int, float, str, tuple, frozenset, bytes.
- **Identity vs equality**:
  - `is` checks "the same object".
  - `==` checks "equal value".
  - Always write `x is None`, never `x == None`, because a class can redefine `==`.
- **Small integer cache**: CPython (the standard Python implementation) pre-creates the integers −5 to 256. That's why `a is b` can be True for small numbers and False for large ones. Never rely on `is` for numbers or strings.
- **Copies**:
  - `list(x)`, `x[:]`, `x.copy()` and `copy.copy(x)` are *shallow*: the outer container is new, but the items inside are shared.
  - `copy.deepcopy(x)` copies everything recursively.

### Classic traps (asked constantly)

**1. A mutable default argument is created once, when the function is defined:**
```python
def add(item, bucket=[]):      # same list reused on every call!
    bucket.append(item); return bucket
add(1); add(2)                 # → [1, 2]

def add(item, bucket=None):    # correct
    if bucket is None: bucket = []
    bucket.append(item); return bucket
```

**2. Closures capture the variable, not its value at the time ("late binding"):**
```python
fs = [lambda: i for i in range(3)]
[f() for f in fs]              # → [2, 2, 2], not [0, 1, 2]
fs = [lambda i=i: i for i in range(3)]   # fix: bind the current value as a default
```

**3. `+=` on a list inside a tuple both raises an error *and* modifies the list:**
```python
t = ([1],)
t[0] += [2]    # TypeError: tuples don't support item assignment
t              # → ([1, 2],)  — the list was extended before the assignment failed
```

**4. Building a 2D grid with `*` shares the rows:**
```python
grid = [[0] * 3] * 3; grid[0][0] = 1   # every row changes
grid = [[0] * 3 for _ in range(3)]     # correct
```

**5. Changing a list or dict while looping over it** skips items or raises an error. Loop over a copy, or build a new collection.

---

## 2. Classes and the "data model"

Python calls special methods (named with double underscores, e.g. `__len__`, nicknamed "dunder" methods) to implement built-in behaviour. Knowing which ones exist is a senior-level signal.

| You write | Python calls |
|---|---|
| `repr(x)` / `str(x)` | `__repr__` (for developers, unambiguous) / `__str__` (for display) |
| `x == y`, `x < y` | `__eq__`, `__lt__` (use `functools.total_ordering` to fill in the rest) |
| `hash(x)`, dict keys, set members | `__hash__` |
| `len(x)`, `x[i]`, `for v in x` | `__len__`, `__getitem__`, `__iter__` / `__next__` |
| `with x:` | `__enter__`, `__exit__` |
| `x.attr` when missing | `__getattr__` (only for *missing* attributes); `__getattribute__` runs for *every* lookup |
| `x(…)` | `__call__` |

### Hashing rules
- Objects that are equal **must** have the same hash.
- If you define `__eq__` without `__hash__`, Python sets `__hash__` to `None` and the objects can no longer be dict keys or set members.
- Only make objects hashable if they are effectively immutable. Otherwise a key can "disappear" from a dict after it changes.

### Dataclasses
They write `__init__`, `__repr__` and `__eq__` for you:
```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    @property
    def mid(self) -> float: return (self.bid + self.ask) / 2
```
- `frozen=True` makes it immutable and hashable.
- `slots=True` saves memory (see below).
- Never use a mutable default value directly. Write `field(default_factory=list)`.

### `__slots__`
- It declares a fixed list of attributes, so instances have no per-object dictionary.
- This uses much less memory and gives slightly faster attribute access, which matters for millions of small objects (ticks, orders).
- The cost: you can't add new attributes at run time.

### Inheritance order
- With multiple inheritance, Python searches parent classes in the **method resolution order**, computed by an algorithm called C3 linearisation. Inspect it with `Class.__mro__`.
- `super()` means "the next class in that order", not "my parent". That's what makes cooperative multiple inheritance work.

### Descriptors (how `property`, methods and `classmethod` actually work)
- A descriptor is an object on a *class* that defines `__get__` (and optionally `__set__` and `__delete__`). When you access the attribute, Python calls those methods instead of returning the object.
- Plain functions are descriptors, which is how `obj.method` becomes a "bound method" with `self` filled in.
- **Lookup order** for `obj.x`:
  1. a descriptor on the class that defines `__set__` (a "data descriptor", e.g. `property`);
  2. the instance's own attributes;
  3. other class attributes and descriptors (e.g. plain methods).

### Customising class creation
- `__init_subclass__` runs whenever a subclass is defined. It's a simple way to register plugins, such as every pricing model registering itself by name.
- **Metaclasses** (the class of a class) can do the same and more, but are rarely needed now. Say so in an interview: it shows judgment.

### Interfaces
- `abc.ABC` with `@abstractmethod`: subclasses *must* implement the methods, checked at creation time.
- `typing.Protocol`: "structural typing". Any class with the right methods qualifies, without inheriting. It's checked by type checkers, not at run time (unless marked `@runtime_checkable`).

---

## 3. Functions, decorators, generators

**Parameter kinds**:
```python
def f(a, b, /, c, *, d, **kw): ...
```
- `a` and `b` are positional-only.
- `c` can be passed either way.
- `d` is keyword-only.
- `**kw` collects any extra keyword arguments.

**Decorators**: a decorator is a function that takes a function and returns a replacement. Always use `functools.wraps` so the name and docstring survive.

A decorator that takes its own arguments needs three levels of functions:
```python
import functools, time

def retry(times: int):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return fn(*args, **kwargs)
                except ConnectionError:
                    if attempt == times - 1: raise
                    time.sleep(2 ** attempt)
        return wrapper
    return decorator
```

**Generators** produce values lazily, one at a time, using `yield`. They give constant memory for huge streams, such as reading a tick file line by line:
```python
from collections.abc import Iterator
from typing import NamedTuple

class Tick(NamedTuple):
    symbol: str
    price: float
    size: int

def parse(line: str) -> Tick:              # one CSV line: symbol,price,size
    symbol, price, size = line.strip().split(",")
    return Tick(symbol, float(price), int(size))

def read_ticks(path: str) -> Iterator[Tick]:
    with open(path) as f:
        for line in f:
            yield parse(line)

big_trades = (t for t in read_ticks("ticks.csv") if t.size > 1_000_000)  # nothing is read yet
```
- `yield from other_generator` hands over to another generator.
- Generators also accept `.send(value)` and `.close()`. These are the old foundation of coroutines.
- A generator can only be consumed **once**.

**Useful standard-library tools**:
- **`functools`**:
  - `cache` / `lru_cache(maxsize=…)`: remember results; arguments must be hashable.
  - `partial`: pre-fill some arguments.
  - `singledispatch`: choose an implementation based on the first argument's type.
  - `cached_property`: compute an attribute once on first access.
- **`itertools`**: `islice`, `chain`, `groupby` (input must be sorted by the key first!), `accumulate`, `product`, `combinations`, `pairwise`, `batched` (3.12+).
- **`collections`**:
  - `deque`: fast appends and pops at both ends.
  - `defaultdict`, `Counter`.
  - `OrderedDict`: has `move_to_end`, handy for a cache that evicts the least recently used item.
- **`heapq`**: a min-heap on a list (for the top-k items, or merging sorted streams).
- **`bisect`**: binary search in a sorted list.

**Context managers**: `with` guarantees clean-up, even when an error occurs. The shortest way to write one:
```python
from contextlib import contextmanager
import time

@contextmanager
def timer(label):
    start = time.perf_counter()
    try:
        yield
    finally:
        print(f"{label}: {time.perf_counter() - start:.3f}s")
```

---

## 4. How CPython runs your code

Deeper dive: [Python under the hood](internals.md) covers how `int`, `list`, `dict`, `set`, `str`, `deque`, `heapq`, `sorted` and `lru_cache` are implemented, plus bytecode specialisation, memory management, descriptors and the GIL.

- **Compilation**: source code is compiled to **bytecode** (instructions for Python's virtual machine), which an interpreter loop executes. Use `dis.dis(fn)` to see it.
- **Recent speed-ups**:
  - 3.11 made the interpreter roughly 25% faster ("specialising" instructions for the types it actually sees).
  - 3.13 added an experimental just-in-time compiler.
- **Memory management**:
  1. **Reference counting**: each object counts how many names point to it, and is freed the moment that count reaches zero. This is why files are usually closed promptly, though you should still use `with`.
  2. **Cycle collector**: objects that refer to each other in a loop never reach zero, so a separate garbage collector (the `gc` module) periodically finds and frees such cycles.
- **The GIL (global interpreter lock)**: in standard CPython, only one thread executes Python bytecode at a time.
  - Threads still help for **waiting** work (network, disk), because the lock is released while waiting.
  - Threads don't speed up **pure-Python computation**.
  - NumPy, pandas and many C libraries **release the lock** during heavy computation, so threads *can* speed those up.
  - **Free-threaded Python**: since 3.13 there is a separate build without the GIL (officially supported from 3.14, installed as `python3.14t`). Some libraries aren't ready for it yet, and single-thread code runs a little slower.
- **Sizes**: `sys.getsizeof` reports only the container itself, not the objects inside it. An empty object is ~50+ bytes and a float is 24 bytes. That's why a NumPy array of a million floats (8 MB) is far smaller than a list of a million Python floats (~32 MB).
- **Dictionaries** keep insertion order (a language guarantee since 3.7). They are hash tables, with average O(1) lookup. (O(1) means constant time, regardless of size.)

### Cost of common operations
| Operation | Cost |
|---|---|
| `list.append`, `list.pop()` | O(1) on average |
| `list.insert(0, x)`, `list.pop(0)`, `x in list` | O(n): use `deque` or a `set` instead |
| `dict` / `set` lookup, insert, delete | O(1) on average |
| `sorted`, `list.sort` | O(n log n); *stable* (equal items keep their order) |
| `heapq.heappush` / `heappop` | O(log n) |
| `bisect.bisect_left` | O(log n) search (inserting into a list is still O(n)) |
| String building in a loop with `+=` | can be O(n²); use `"".join(parts)` |

---

## 5. Concurrency: choosing the right tool

| Work type | Tool | Why |
|---|---|---|
| Many slow network or disk calls (market data APIs, databases) | `asyncio`, or threads | Time is spent waiting; one process can juggle thousands of waits |
| Heavy pure-Python computation | `multiprocessing` / `ProcessPoolExecutor` | Separate processes each have their own interpreter, so the GIL doesn't block them |
| Heavy NumPy / pandas / C-library computation | threads often suffice | These libraries release the GIL |
| A simple parallel map | `concurrent.futures` (`ThreadPoolExecutor` / `ProcessPoolExecutor`) | Same interface for both; easy to switch |

### Processes
- Arguments and results are **pickled** (serialised to bytes) to cross between processes. Sending large arrays is slow, so share memory (`multiprocessing.shared_memory`) or have each worker load its own data.
- **Start method**: on macOS and Windows, new processes are started fresh ("spawn"), so worker code must be importable and protected by `if __name__ == "__main__":`. On Linux, the default changed in 3.14 from copying the parent process ("fork") to "forkserver".

### asyncio essentials
```python
import asyncio

async def fetch(symbol):
    await asyncio.sleep(0.1)          # stands in for a network call
    return symbol, 100.0

async def main():
    async with asyncio.TaskGroup() as tg:        # 3.11+: if one task fails, the others are cancelled
        tasks = [tg.create_task(fetch(s)) for s in ["AAPL", "MSFT"]]
    return [t.result() for t in tasks]

asyncio.run(main())
```
- **Never block the event loop**: a single `time.sleep()` or heavy calculation inside `async` code freezes *every* task. Use `await asyncio.sleep()`, or push blocking work to a thread with `await asyncio.to_thread(fn, ...)`.
- `asyncio.gather` runs awaitables together. `asyncio.wait_for` (or `asyncio.timeout`) adds a time limit.
- Use a bounded `asyncio.Queue` for producer/consumer pipelines, so a fast producer can't use up all the memory ("back-pressure").

### Thread safety
- Even with the GIL, `x += 1` on shared data is **not** atomic: it's several bytecode steps. Use `threading.Lock`, or a `queue.Queue` for handing work between threads.

---

## 6. Performance

1. **Measure first**:
   - `cProfile` / `python -m cProfile -s cumtime script.py`: which functions take time.
   - `line_profiler`: which lines.
   - `py-spy`: samples a running program without changing it.
   - `tracemalloc`: where memory is allocated.
   - `timeit`: small comparisons.
2. **Better algorithm and data structure** usually beat any micro-tuning (see the cost table in section 4).
3. **Vectorise**: move loops into NumPy or pandas, which run in compiled code. A Python loop over a million numbers is typically 50–100× slower than the NumPy equivalent.
4. **Compile the hot loop** when it can't be vectorised (for example, a path-dependent calculation):
   - **Numba**: add `@njit` to a numeric function and it is compiled to machine code. It's great for Monte Carlo inner loops.
   - **Cython** or a C++/Rust extension (for example via `pybind11` or `PyO3`) for the highest performance.
5. **Micro-tricks** (only after profiling):
   - Use built-ins (`sum`, `min`, `sorted`, `any`).
   - Keep frequently used functions in local variables inside tight loops.
   - Avoid creating many small objects.
   - Use `__slots__`.
   - Prefer generators for streaming and lists when you'll iterate several times.

---

## 7. NumPy in depth

### Views vs copies (asked very often)
- **Basic slicing** (`a[1:4]`, `a[:, 0]`) returns a **view**: it shares memory, so writing to it changes the original.
- **Fancy indexing** with a list or array of positions (`a[[1, 2]]`) and **boolean masks** (`a[a > 0]`) return **copies**.

```python
import numpy as np

a = np.arange(6)
b = a[1:4];   b[0] = 99    # a changes:  [0 99 2 3 4 5]
c = a[[1, 2]]; c[0] = -1   # a unchanged: c is a copy
```
- Check with `np.shares_memory(a, b)`. Use `.copy()` when you need independence.

### Memory layout
- An array is a block of memory plus **strides**: how many bytes to jump to reach the next element along each dimension.
- **Row-major vs column-major**:
  - The default is row-major ("C order"): each row is contiguous.
  - Column-major ("Fortran order") stores each column contiguously.
  - Looping along the contiguous direction is much faster, because the CPU cache is used well.
- Transposing (`.T`) and many reshapes just change the strides, without copying anything.

### Broadcasting rules
Shapes are compared from the **last** dimension backwards. Each pair of dimensions must be equal, or one of them must be 1 (which is stretched to match).
```python
import numpy as np

rng = np.random.default_rng(0)
prices = rng.normal(100, 5, size=(252, 50))   # shape (days, assets)
means = prices.mean(axis=0)          # shape (50,)
demeaned = prices - means            # (252, 50) - (50,) works: subtracts each asset's mean
row_means = prices.mean(axis=1, keepdims=True)   # (252, 1), keeps the dimension so it broadcasts
```

### Data type pitfalls
- **Integers silently wrap around** on overflow: `np.array([2**31 - 1], dtype=np.int32) + 1` → `-2147483648`. Python's own integers never overflow.
- `float32` has only ~7 significant digits: `np.float32(16777217.0)` → `16777216.0`. Use `float64` for prices and risk.
- Compare floats with `np.isclose` / `np.allclose`, never `==`.
- `NaN` (not-a-number) is not equal to itself. Use `np.isnan`, or the `np.nan*` functions (`np.nanmean`) to skip missing values.

### Good habits
- Never grow arrays in a loop with `np.append`: every call copies the whole array. Pre-allocate with `np.empty(n)`, or collect results in a list and convert once.
- Use in-place operations to avoid temporary arrays: `a *= 2`, `np.add(a, b, out=a)`.
- `np.einsum` writes tensor operations compactly, e.g. a portfolio variance for many portfolios at once:
  ```python
  import numpy as np

  rng = np.random.default_rng(0)
  X = rng.normal(size=(500, 4))
  Cov = np.cov(X, rowvar=False)                 # 4 x 4 covariance of 4 assets
  W = rng.dirichlet(np.ones(4), size=3)         # 3 portfolios' weights, shape (3, 4)
  variances = np.einsum("pi,ij,pj->p", W, Cov, W)   # one variance per portfolio
  ```
- Random numbers: use `rng = np.random.default_rng(seed)`, a modern independent generator you pass around, rather than the old global `np.random.seed`.
- Linear algebra: use `np.linalg.solve(A, b)` rather than `inv(A) @ b` (faster and more accurate). Use `cholesky` for a covariance matrix you know is positive definite.

---

## 8. pandas in depth

- **Index alignment**: arithmetic between two Series or DataFrames lines them up by index label *first*, then computes. Labels missing from one side give `NaN`. This is powerful, and a common source of silent bugs: check the indexes match.
- **Copy-on-write** (the default from pandas 3.0): every result behaves like a copy. Changing a selection never changes the original DataFrame, and the old `SettingWithCopyWarning` is gone. To change data, use `df.loc[rows, col] = value` on the original.
- **`groupby` choices**:
  - `agg`: one value per group (sum, mean).
  - `transform`: the result has the same length as the input, e.g. demeaning returns within each date:
    ```python
    import pandas as pd

    df = pd.DataFrame({"date": ["d1", "d1", "d2", "d2"], "ret": [0.01, 0.03, -0.02, 0.00]})
    df["ret_demeaned"] = df["ret"] - df.groupby("date")["ret"].transform("mean")
    ```
  - `apply`: anything, but slow. Avoid it when `agg` or `transform` work.
- **Time series**:
  - Store timestamps in a single time zone (UTC, coordinated universal time) and convert only for display.
  - `resample("5min")` buckets by time.
  - `rolling(20)` uses a fixed number of rows; `rolling("20D")` uses a time window.
  - `shift(1)` uses the previous value. Forgetting it is the classic look-ahead bug in backtests.
- **`merge_asof`**: for each row, it finds the latest matching row *at or before* its time. It's the pandas version of kdb+'s `aj` (as-of join), used to attach the prevailing quote to each trade. Both tables must be sorted by time, and use `by="symbol"` to match within each instrument.
  ```python
  import pandas as pd

  quotes = pd.DataFrame({
      "time": pd.to_datetime(["2026-11-24 09:30:00", "2026-11-24 09:30:02", "2026-11-24 09:30:05"]),
      "symbol": ["AAPL", "AAPL", "AAPL"],
      "bid": [189.9, 190.0, 190.1], "ask": [190.0, 190.1, 190.2],
  })
  trades = pd.DataFrame({
      "time": pd.to_datetime(["2026-11-24 09:30:01", "2026-11-24 09:30:04"]),
      "symbol": ["AAPL", "AAPL"], "price": [190.0, 190.1],
  })
  with_quote = pd.merge_asof(trades.sort_values("time"), quotes.sort_values("time"),
                             on="time", by="symbol", direction="backward")
  ```
- **Speed and memory**:
  - Avoid `iterrows` / `itertuples` loops; vectorise instead.
  - Convert repeated strings (symbols, desks) to the `category` type.
  - Downcast `float64` → `float32` only when the precision loss is acceptable.
  - Read only the needed columns. Store data in **Parquet** (a compressed column-based file format), not CSV.
- **Polars**: a newer DataFrame library, written in Rust. It is multi-threaded, with a "lazy" mode that optimises the whole query before running it. It's often several times faster than pandas on large data, and worth mentioning.

---

## 9. Type hints and code quality

- Type hints don't change how code runs. Tools (`mypy`, `pyright`) check them and catch bugs before you run anything.
- **Modern syntax**:
  - `list[int]`, `dict[str, float]`, `int | None` (3.10+).
  - Generics written as `def first[T](xs: list[T]) -> T:` (3.12+).
  - `type Price = float` for type aliases (3.12+).
- **Useful types**:
  - `Literal["call", "put"]`: one of these exact values.
  - `TypedDict`: the shape of a dict.
  - `Protocol`: structural interfaces.
  - `@overload`: different return types for different arguments.
  - `Final`: must not be reassigned.
- 3.14 evaluates annotations lazily, only when someone asks for them. This means fewer problems with classes that refer to each other.
- **Tooling**: `uv` (fast package and environment manager), `ruff` (fast linter and formatter), `pytest`.
  - `pytest` fixtures supply test data and set-up.
  - `@pytest.mark.parametrize` runs one test over many inputs.
  - **Property-based testing** with `hypothesis`: generate random inputs and check that a rule always holds, e.g. "put–call parity holds for any valid inputs".
- **Structural pattern matching** (3.10+): `match`/`case` can unpack nested data, which is good for parsing messages.
  ```python
  def handle_trade(px: float, qty: int) -> None: print("trade", px, qty)
  def handle_quote(bid: float, ask: float) -> None: print("quote", bid, ask)
  def log_unknown(msg: dict) -> None: print("unknown", msg)

  def route(msg: dict) -> None:
      match msg:
          case {"type": "trade", "px": px, "qty": qty}: handle_trade(px, qty)
          case {"type": "quote", "bid": b, "ask": a}:   handle_quote(b, a)
          case _: log_unknown(msg)

  route({"type": "trade", "px": 101.5, "qty": 200})
  ```
- **Exception groups** (3.11+): `except*` handles several errors raised together, for example by a `TaskGroup`.

---

## 10. Numerical gotchas (very relevant for quant roles)

- **Floats are binary approximations**: `0.1 + 0.2 == 0.3` is `False`.
  - Use `math.isclose`.
  - Use `decimal.Decimal` for exact decimal amounts, such as cash balances or fees.
- **Summing many floats loses accuracy**:
  - A plain loop adding `0.1` ten times gives `0.9999999999999999`.
  - `math.fsum` is exact.
  - The built-in `sum()` has used compensated (more accurate) addition for floats since 3.12.
  - NumPy uses pairwise summation, which is accurate enough for most uses.
- **Catastrophic cancellation**: subtracting two nearly equal large numbers destroys precision. Examples are the one-pass variance formula E[x²] − E[x]², and finite-difference Greeks with a tiny bump. Use Welford's online algorithm for the variance, and a sensible bump size.
- **Overflow in exponentials**: compute log(Σ eˣ) as m + log(Σ e^(x−m)) with m = max(x) ("log-sum-exp"). Use `scipy.special.logsumexp`.
- **Rounding**: `round(2.5)` → `2` and `round(3.5)` → `4`. Python rounds halves to the nearest *even* number ("banker's rounding"). Use `Decimal.quantize` with an explicit rounding rule when a convention requires otherwise.
- **Integer division with negatives** rounds *down*: `-7 // 2` → `-4`, and `-7 % 2` → `1`. C++ rounds towards zero instead, a classic source of bugs when porting code.
- **Dates**:
  - Use time-zone-aware `datetime` objects.
  - Business-day and day-count conventions (Actual/360, 30/360) need explicit code or a library; never guess.

---

## 11. Interview questions with short answers

1. **What does the GIL prevent, and how do you get parallel speed anyway?** Two threads can't run Python bytecode at the same time. Use processes for pure-Python computation, threads or `asyncio` for waiting work, and NumPy or compiled code (which release the lock) for numeric work. Or use the free-threaded build.
2. **Why is `def f(x=[])` a bug?** The default list is created once and shared by every call.
3. **List vs tuple?** Tuples are immutable, hashable (if their contents are), slightly smaller and faster, and signal "fixed record". Lists are for collections that change.
4. **How does a dict work, and what can be a key?** A hash table with average constant-time lookup. Keys must be hashable, and equal keys must have equal hashes.
5. **Generator vs list?** A generator computes values on demand, uses constant memory and can be consumed only once. A list stores everything and can be reused.
6. **`__getattr__` vs `__getattribute__`?** The first runs only when normal lookup fails. The second runs on every attribute access, so overriding it is easy to get wrong (infinite recursion).
7. **What does `super()` actually call?** The next class in the method resolution order of the *object's* class, which isn't necessarily the direct parent.
8. **How would you speed up a slow backtest loop?** Profile it; vectorise with NumPy or pandas; if it's path-dependent, compile the loop with Numba; check the data types and avoid copying data inside the loop.
9. **View or copy: `a[a > 0]`?** A copy, because boolean masks and integer-list indexing copy, while slices give views.
10. **Write an LRU cache (one that evicts the least recently used item).** Use `OrderedDict`: on `get`, call `move_to_end(key)`; on `put`, insert and `move_to_end`, and if the cache is over capacity, `popitem(last=False)`. Both operations are O(1). Or just use `functools.lru_cache` for functions.
11. **What happens when you `import` a module twice?** It runs only once. Later imports return the cached module from `sys.modules`.
12. **How do you avoid look-ahead bias in pandas?** Use `shift` for anything that must be known in advance, `merge_asof` with `direction="backward"`, and rolling windows that end at the current row. Assert that every feature's timestamp is earlier than its target's.

---

## 12. Classic implementations (with code)

Full, commented, tested code is in [`src/quantprep/classics/`](../../src/quantprep/classics/). Each structure is checked against Python's built-in equivalent over thousands of random operations ([`tests/test_classics.py`](../../tests/test_classics.py)). Run the tests with `uv run pytest tests/test_classics.py`.

| File | What it is | Running time | Key idea to explain |
|---|---|---|---|
| [`hash_map.py`](../../src/quantprep/classics/hash_map.py) | A dictionary from scratch | get/set/delete O(1) on average | One flat table; step to the next slot on a collision; "tombstones" for deletes; grow at 2/3 full |
| [`binary_search.py`](../../src/quantprep/classics/binary_search.py) | Exact search, lower/upper bound, search on the answer, rotated array, root finding (implied volatility) | O(log n) | One consistent template: half-open range `[lo, hi)`, `while lo < hi` |
| [`lru_cache.py`](../../src/quantprep/classics/lru_cache.py) | LRU cache (with `OrderedDict`, and from scratch), plus a caching decorator | get/put O(1) | Dict for finding a node + doubly linked list for the order |
| [`heap.py`](../../src/quantprep/classics/heap.py) | Min-heap from scratch, top-k of a stream | push/pop O(log n), build O(n) | A tree stored in a list: children at 2i+1 and 2i+2 |
| [`streaming.py`](../../src/quantprep/classics/streaming.py) | Running median, sliding-window max, one-pass mean/variance | O(log n), O(1) on average, O(1) | Two heaps; a deque of decreasing values; Welford's method |
| [`union_find.py`](../../src/quantprep/classics/union_find.py) | Grouping items into connected sets | almost O(1) | Attach the smaller tree under the larger; shorten paths while searching |
| [`trie.py`](../../src/quantprep/classics/trie.py) | Prefix tree for autocomplete | O(word length) | Nested dicts, one level per character |

### Binary search: the one template to memorise
```python
def lower_bound(a, x):            # first index i with a[i] >= x  (= bisect.bisect_left)
    lo, hi = 0, len(a)            # answer is always inside [lo, hi)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1          # mid is too small, so the answer is to its right
        else:
            hi = mid              # mid might be the answer; keep it
    return lo
```
- **Upper bound** (the first index with `a[i] > x`): change `<` to `<=`.
- **Search on the answer**: replace `a[mid] < x` with "is `mid` too small?" for any yes/no test that flips once. Examples: the smallest batch size that fits in memory, or the integer square root.
- In C++, write `lo + (hi - lo) / 2` to avoid integer overflow. Python integers never overflow.

### LRU cache from scratch: the core
```python
class Node:
    __slots__ = ("key", "value", "prev", "next")
    def __init__(self, key=None, value=None):
        self.key, self.value, self.prev, self.next = key, value, None, None

class LRUCache:
    def __init__(self, capacity):
        self.capacity, self.map = capacity, {}               # key -> node
        self.head, self.tail = Node(), Node()                 # dummy ends: no empty-list special cases
        self.head.next, self.tail.prev = self.tail, self.head

    def get(self, key):
        node = self.map.get(key)
        if node is None:
            return None
        self._unlink(node); self._append(node)                # move to "most recent" end
        return node.value

    def put(self, key, value):
        if key in self.map:
            node = self.map[key]; node.value = value
            self._unlink(node); self._append(node)
            return
        if len(self.map) == self.capacity:
            oldest = self.head.next                           # least recent sits at the front
            self._unlink(oldest); del self.map[oldest.key]
        node = Node(key, value); self.map[key] = node; self._append(node)

    def _unlink(self, node):                                  # remove from the list
        node.prev.next, node.next.prev = node.next, node.prev

    def _append(self, node):                                  # insert just before the tail
        last = self.tail.prev
        last.next, node.prev, node.next, self.tail.prev = node, last, self.tail, node
```
- Each node stores its own key, so the evicted key can be removed from the dict.
- Follow-up questions:
  - *Thread safety?* Wrap `get` and `put` in a `threading.Lock`.
  - *Expiry by time?* Store a timestamp per node and treat expired nodes as missing.
  - *Evict the least *frequently* used instead (LFU)?* Keep a dict from usage count to an ordered set of keys, and track the minimum count.

### Dictionary from scratch: the core of the lookup
```python
EMPTY = object()      # marker: slot never used
DELETED = object()    # marker: slot used, then deleted (a "tombstone")

class HashMap:
    def __init__(self, capacity: int = 8):    # capacity must be a power of two
        self.keys = [EMPTY] * capacity
        self.values = [None] * capacity

    def _find_slot(self, key):
        mask = len(self.keys) - 1                  # table size is a power of two
        i = hash(key) & mask                       # low bits of the hash = starting slot
        first_tombstone = None
        while True:
            k = self.keys[i]
            if k is EMPTY:                         # key is not present
                return (first_tombstone if first_tombstone is not None else i), False
            if k is DELETED:
                if first_tombstone is None: first_tombstone = i   # remember a reusable slot
            elif k is key or k == key:
                return i, True
            i = (i + 1) & mask                     # collision: try the next slot
```
- **Why tombstones?** Emptying a deleted slot would break the chain for any key that had stepped past it.
- **Why grow at two-thirds full?** Fuller tables make the chains of slots to check long, and lookups slow down sharply.
- **How the real `dict` differs**: CPython jumps around the table using more bits of the hash (not just the next slot), and keeps a separate list of entries in insertion order. That's why dicts remember insertion order.

---

## 13. Features, tricks and live-coding habits

Moved to its own page: [senior-features-and-tricks.md](senior-features-and-tricks.md). It covers modelling with types, built-ins that replace loops, error handling, Pythonic design patterns, and habits that come across as senior in a live coding round.

---

## Glossary
| Term | Meaning |
|---|---|
| CPython | The standard Python implementation, written in C |
| Bytecode | Low-level instructions that Python's virtual machine executes |
| GIL | Global interpreter lock: lets only one thread run Python bytecode at a time |
| Free-threaded build | A Python build without the GIL (3.13+, officially supported from 3.14) |
| O(1), O(n), O(n log n) | How running time grows with input size n: constant, linear, slightly more than linear |
| Dunder method | A special method with double underscores, like `__init__` |
| Descriptor | A class attribute that controls access through `__get__` / `__set__` |
| MRO | Method resolution order: the order Python searches classes for an attribute |
| Pickle | Python's built-in way to turn objects into bytes and back |
| Event loop | The scheduler inside `asyncio` that switches between waiting tasks |
| Vectorise | Replace a Python loop with one operation on a whole array |
| View | An array that shares memory with another array |
| Strides | Bytes to skip to move one step along each dimension of an array |
| Copy-on-write | Data is shared until someone changes it, then copied, so changes never leak |
| Parquet | A compressed, column-based file format for tables |
| UTC | Coordinated universal time: the standard reference time zone |
| Protocol | An interface defined by which methods an object has, not by what it inherits |
| LRU | Least recently used: a cache policy that evicts the item unused for longest |
