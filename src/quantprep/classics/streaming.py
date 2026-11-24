"""Streaming statistics that appear in quant interviews.

- RunningMedian: the median of all values seen so far, O(log n) per value, using two heaps:
    `low`  is a max-heap holding the smaller half (stored negated, since heapq is a min-heap)
    `high` is a min-heap holding the larger half
  Keep them balanced (sizes equal, or `low` larger by one); the median is at the top(s).
- sliding_window_max: the maximum of every window of k consecutive values in O(n) total,
  using a "monotonic deque" of indices whose values are decreasing from front to back.
  E.g. rolling high of a price series.
- RunningMeanVar: mean and variance in one pass with Welford's method. This is numerically
  stable, unlike the formula E[x^2] - E[x]^2, which suffers cancellation.
"""

import heapq
import math
from collections import deque
from collections.abc import Sequence


class RunningMedian:
    def __init__(self) -> None:
        self._low: list[float] = []   # max-heap via negation
        self._high: list[float] = []  # min-heap

    def add(self, x: float) -> None:
        if not self._low or x <= -self._low[0]:
            heapq.heappush(self._low, -x)
        else:
            heapq.heappush(self._high, x)
        # rebalance so that len(low) == len(high) or len(low) == len(high) + 1
        if len(self._low) > len(self._high) + 1:
            heapq.heappush(self._high, -heapq.heappop(self._low))
        elif len(self._high) > len(self._low):
            heapq.heappush(self._low, -heapq.heappop(self._high))

    def median(self) -> float:
        if not self._low:
            raise ValueError("no data")
        if len(self._low) > len(self._high):
            return -self._low[0]
        return (-self._low[0] + self._high[0]) / 2


def sliding_window_max(values: Sequence[float], k: int) -> list[float]:
    if k <= 0:
        raise ValueError("k must be positive")
    dq: deque[int] = deque()  # indices; their values are decreasing front to back
    out = []
    for i, v in enumerate(values):
        while dq and values[dq[-1]] <= v:
            dq.pop()             # smaller older values can never be a window maximum again
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()         # front index has left the window
        if i >= k - 1:
            out.append(values[dq[0]])
    return out


class RunningMeanVar:
    def __init__(self) -> None:
        self.n = 0
        self.mean = 0.0
        self._m2 = 0.0  # sum of squared deviations from the current mean

    def add(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        self._m2 += delta * (x - self.mean)

    @property
    def variance(self) -> float:
        """Sample variance (divides by n - 1)."""
        return self._m2 / (self.n - 1) if self.n > 1 else math.nan
