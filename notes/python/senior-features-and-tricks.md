# Python: Features and Tricks That Make Code Look Senior

Companion to the [Python page](README.md). Interviewers judge three things: is it correct, is it clear, and do you know the standard library.
The right built-in tool beats a clever one-liner. Each block below runs on its own (3.12+).

## Model the problem with types, not loose strings and tuples
```python
from dataclasses import dataclass, replace
from enum import StrEnum


class Side(StrEnum):
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True, slots=True, kw_only=True)
class Order:
    symbol: str
    side: Side
    qty: int
    price: float

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise ValueError(f"qty must be positive, got {self.qty}")


order = Order(symbol="ZN", side=Side.BUY, qty=10, price=110.5)
bigger = replace(order, qty=20)            # frozen, so make a changed copy
print(bigger)       # Order(symbol='ZN', side=<Side.BUY: 'buy'>, qty=20, price=110.5)
print(bigger.side == "buy")                # True: a StrEnum compares equal to its string
try:
    Order(symbol="ZN", side=Side.SELL, qty=0, price=110.5)
except ValueError as err:
    print(err)                             # qty must be positive, got 0
```
- **`StrEnum`**: a typo like `"biy"` fails at once instead of silently matching nothing.
- **`kw_only=True`**: callers must write `qty=` and `price=`, so two numbers can never be swapped.
- **`__post_init__`**: check inputs once, where the object is created, then trust it everywhere.
- **`replace`**: change a copy of a frozen object (`copy.replace` does the same for any object, 3.13+).

## Small built-ins that replace hand-written loops
```python
import bisect
import heapq
import io
from collections import Counter
from itertools import accumulate, batched, pairwise

prices = [100.0, 101.0, 99.5, 102.0]
returns = [b / a - 1 for a, b in pairwise(prices)]          # consecutive pairs
wealth = list(accumulate(returns, lambda w, r: w * (1 + r), initial=1.0))
print([f"{r:+.2%}" for r in returns])      # ['+1.00%', '-1.49%', '+2.51%']
print(f"{wealth[-1]=:.4f}")                # wealth[-1]=1.0200  (the = prints the expression)
print(f"{1234567.891:,.2f}")               # 1,234,567.89

print(list(batched(range(7), 3)))          # [(0, 1, 2), (3, 4, 5), (6,)]

weights = [0.5, 0.3, 0.2]
tickers = ["AAPL", "MSFT", "NVDA"]
print(dict(zip(tickers, weights, strict=True)))  # strict=True raises if the lengths differ

feed_a = [(1, "A"), (4, "A")]              # (timestamp, source), each already sorted
feed_b = [(2, "B"), (3, "B")]
print(list(heapq.merge(feed_a, feed_b)))   # [(1, 'A'), (2, 'B'), (3, 'B'), (4, 'A')]

ticks = [(9.0, 100.1), (9.5, 100.3), (10.0, 100.2)]          # (time, price), sorted by time
i = bisect.bisect_right(ticks, 9.7, key=lambda t: t[0]) - 1  # key= since 3.10
print(ticks[i])                            # (9.5, 100.3): last tick at or before 9.7

defaults = {"tenor": "10Y", "notional": 1e6}
print(defaults | {"notional": 5e6})        # {'tenor': '10Y', 'notional': 5000000.0}
print(Counter(["buy", "sell", "buy", "buy"]).most_common(1))    # [('buy', 3)]

f = io.StringIO("AAPL,190.1\nMSFT,410.2\n")
while line := f.readline():                # := assigns and tests in one step
    print(line.strip().split(","))         # ['AAPL', '190.1'] then ['MSFT', '410.2']
```
| Tool | Replaces |
|---|---|
| `pairwise` | `for i in range(1, len(x))` with `x[i-1]`, `x[i]` |
| `accumulate(..., initial=)` | a running total or running product loop |
| `batched` (3.12+) | slicing a list into chunks by hand |
| `zip(strict=True)` | silent truncation when two lists have different lengths |
| `f"{x=}"`, `:,.2f`, `:+.2%` | `print("x", x)` and manual number formatting |
| `heapq.merge` | merging sorted feeds into one list and re-sorting |
| `bisect(..., key=)` | a linear scan for "last value at or before time t" |
| `a \| b` on dicts | `c = a.copy(); c.update(b)` |
| `:=` (walrus) | reading a value before the loop and again at the end of it |

## Errors and clean-up done properly
```python
import json
from contextlib import ExitStack, suppress
from pathlib import Path


class ConfigError(Exception):
    pass


def load_config(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError as err:
        e = ConfigError("bad config")
        e.add_note("hint: check for a trailing comma")     # 3.11+: extra context in the traceback
        raise e from err                                    # keeps the original error attached


try:
    load_config('{"tenor": "10Y",}')
except ConfigError as err:
    print(err, "| caused by:", type(err.__cause__).__name__, "|", err.__notes__)
    # bad config | caused by: JSONDecodeError | ['hint: check for a trailing comma']

with suppress(FileNotFoundError):          # clearer than try/except/pass
    Path("no_such_file.tmp").unlink()

paths = [Path(f"part_{i}.tmp") for i in range(3)]
with ExitStack() as stack:                 # open a variable number of files, all closed safely
    files = [stack.enter_context(p.open("w")) for p in paths]
    for i, fh in enumerate(files):
        fh.write(str(i))
for p in paths:
    p.unlink()

for n in [9, 15, 21]:
    if n % 2 == 0:
        print("found even", n)
        break
else:                                       # runs only if the loop did not break
    print("no even number")                 # no even number
```
- **`raise ... from err`** keeps the original cause in the traceback; **`add_note`** adds context.
- Raise a **specific** exception type, never `except:` or `except Exception: pass`.
- **`suppress`** for an error you expect and accept; **`ExitStack`** when the number of resources
  is only known at run time.
- **`for ... else`**: the `else` runs only if the loop finished without `break`. Handy for search.

## Pythonic design patterns
```python
import math
from functools import cached_property, singledispatch
from typing import ClassVar, Protocol, Self


class Pricer(Protocol):                     # any class with this method fits; no inheritance needed
    def price(self, spot: float) -> float: ...


class Model:
    registry: ClassVar[dict[str, type["Model"]]] = {}
    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs):  # runs when a subclass is defined
        super().__init_subclass__(**kwargs)
        Model.registry[cls.name] = cls

    @classmethod
    def create(cls, name: str, **params) -> Self:
        return cls.registry[name](**params)


class Forward(Model):
    name = "forward"

    def __init__(self, strike: float, rate: float, years: float):
        self.strike, self.rate, self.years = strike, rate, years

    @cached_property                        # computed once, on first access
    def discount(self) -> float:
        return math.exp(-self.rate * self.years)

    def price(self, spot: float) -> float:
        return spot - self.strike * self.discount


def value_book(pricers: list[Pricer], spot: float) -> float:
    return sum(p.price(spot) for p in pricers)


fwd = Model.create("forward", strike=100.0, rate=0.03, years=1.0)
print(sorted(Model.registry), f"{value_book([fwd, fwd], 105.0):.4f}")  # ['forward'] 15.9109


@singledispatch
def to_rate(x) -> float:                    # one name, implementation chosen by argument type
    raise TypeError(f"cannot convert {type(x).__name__}")


@to_rate.register
def _(x: float) -> float:
    return x


@to_rate.register
def _(x: str) -> float:                     # "4.25%" -> 0.0425
    return float(x.rstrip("%")) / 100


print(to_rate(0.05), to_rate("4.25%"))      # 0.05 0.0425
```
- **`Protocol`**: an interface checked by shape ("has a `price` method"), so any object fits.
- **`__init_subclass__` registry**: new models register themselves; no central `if/elif` list to edit.
- **`Self`** (3.11+): the return type is "an instance of this class", even for subclasses.
- **`cached_property`**: an expensive value computed once, on first access.
- **`singledispatch`**: one function name, with the implementation chosen by the argument's type.

## Habits that position you as senior in a live coding round
1. **Clarify first**: input size, edge cases (empty, duplicates, ties), units (annual rate? decimal
   or percent?). One minute of questions saves ten of rewriting.
2. **Write the signature before the body**: type hints and a one-line docstring with units, e.g.
   `def dv01(notional: float, rate: float, years: float) -> float:`.
3. **Simple and correct first, then faster**: state the complexity of each version, e.g.
   "sorting is O(n log n); a heap gives O(n log k) for the top k".
4. **Name things by meaning**: `notional`, `fills`, `best_bid`, not `x`, `tmp`, `d2`.
5. **Test out loud**: finish with two or three `assert`s, including an edge case and a known identity
   (e.g. put-call parity).
6. **Mention the trade-offs you skipped**: float vs `Decimal`, list vs `deque`, thread safety,
   what happens at 100 times the data.
7. **Avoid what reads as junior**: mutable default arguments, bare `except`, global state, a class
   where a function would do, and one-liners nobody can read.

---

## Glossary

| Term | Meaning |
|---|---|
| Dataclass | A class whose `__init__`, `__repr__` and `__eq__` are written for you |
| Enum / StrEnum | A fixed set of named values; `StrEnum` members also act as strings |
| Frozen | Immutable: fields cannot be changed after creation |
| Protocol | An interface defined by which methods an object has, not by what it inherits |
| Registry | A dict that maps names to classes, filled in automatically as classes are defined |
| Traceback | The error report listing the chain of calls that led to an exception |
| Walrus operator | `:=`, which assigns a value inside an expression |
