"""Binary search and its common variants.

The one idea: keep an interval that is guaranteed to contain the answer, and halve it each step.
That gives O(log n) steps. Most bugs are off-by-one errors, so use ONE template consistently:
a half-open interval [lo, hi) with the loop condition `while lo < hi`.

Variants:
- binary_search:  index of x, or -1
- lower_bound:    first index i with a[i] >= x   (same as bisect.bisect_left)
- upper_bound:    first index i with a[i] >  x   (same as bisect.bisect_right)
- first_true:     smallest integer in [lo, hi) where a yes/no test switches from False to True
                  ("binary search on the answer", e.g. minimum capacity, integer square root)
- search_rotated: find x in a sorted array that was rotated, e.g. [4, 5, 6, 1, 2, 3]
- bisect_root:    root of a continuous function by repeated halving, e.g. implied volatility
"""

from collections.abc import Callable, Sequence


def lower_bound(a: Sequence, x) -> int:
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2  # Python ints don't overflow; in C++ write lo + (hi - lo) / 2
        if a[mid] < x:
            lo = mid + 1      # answer is to the right of mid
        else:
            hi = mid          # mid could be the answer
    return lo


def upper_bound(a: Sequence, x) -> int:
    lo, hi = 0, len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo


def binary_search(a: Sequence, x) -> int:
    i = lower_bound(a, x)
    return i if i < len(a) and a[i] == x else -1


def count_in_range(a: Sequence, low, high) -> int:
    """How many values v satisfy low <= v <= high, in O(log n)."""
    return upper_bound(a, high) - lower_bound(a, low)


def first_true(lo: int, hi: int, test: Callable[[int], bool]) -> int:
    """Smallest n in [lo, hi) with test(n) True, assuming test is False...False True...True.

    Returns hi if test is never True.
    """
    while lo < hi:
        mid = (lo + hi) // 2
        if test(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def isqrt(n: int) -> int:
    """Integer square root via binary search on the answer: largest r with r*r <= n."""
    return first_true(0, n + 2, lambda r: r * r > n) - 1


def search_rotated(a: Sequence, x) -> int:
    """Index of x in a rotated sorted array with distinct values, or -1. O(log n).

    At each step at least one half [lo, mid] or [mid, hi] is in sorted order. Check whether
    x lies inside that sorted half; if so search there, otherwise search the other half.
    """
    lo, hi = 0, len(a) - 1  # closed interval here, because we compare a[lo] and a[hi]
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[lo] <= a[mid]:                # left half is sorted
            if a[lo] <= x < a[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:                              # right half is sorted
            if a[mid] < x <= a[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


def bisect_root(f: Callable[[float], float], lo: float, hi: float,
                tol: float = 1e-10, max_iter: int = 200) -> float:
    """Root of f on [lo, hi], given that f(lo) and f(hi) have opposite signs.

    Slower than Newton's method (about 1 bit of accuracy per step), but it can never diverge.
    Production implied-volatility solvers often use Newton with a bisection fallback.
    """
    f_lo = f(lo)
    if f_lo * f(hi) > 0:
        raise ValueError("f(lo) and f(hi) must have opposite signs")
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        f_mid = f(mid)
        if f_mid == 0 or hi - lo < tol:
            return mid
        if (f_mid < 0) == (f_lo < 0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
