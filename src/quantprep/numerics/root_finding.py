"""Root finding: solve f(x) = 0 for one unknown.

Every function returns a RootResult with the iteration count, so you can compare speeds.

| Method              | Needs                    | Speed near the root          | Can fail?                     |
|---------------------|--------------------------|------------------------------|-------------------------------|
| bisection           | a bracket [lo, hi]       | slow: 1 binary digit / step  | never (if the bracket is valid)|
| newton              | f and its derivative f'  | fast: digits double per step | yes: flat spots, overshooting |
| secant              | two starting points      | fairly fast (order ~1.618)   | yes, like Newton              |
| safeguarded_newton  | bracket + f'             | fast, like Newton            | no: falls back to bisection   |

Quant uses: implied volatility, bond yield to maturity, each step of curve bootstrapping.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass

from quantprep.black_scholes import bs_price, bs_vega

Fn = Callable[[float], float]


@dataclass
class RootResult:
    root: float
    iterations: int
    converged: bool


def bisection(f: Fn, lo: float, hi: float, tol: float = 1e-12, max_iter: int = 200) -> RootResult:
    """Halve a bracket whose ends have opposite signs. Error after n steps <= (hi - lo) / 2^n."""
    f_lo, f_hi = f(lo), f(hi)
    if f_lo == 0:
        return RootResult(lo, 0, True)
    if f_hi == 0:
        return RootResult(hi, 0, True)
    if f_lo * f_hi > 0:
        raise ValueError("f(lo) and f(hi) must have opposite signs")
    for i in range(1, max_iter + 1):
        mid = 0.5 * (lo + hi)
        f_mid = f(mid)
        if f_mid == 0 or 0.5 * (hi - lo) < tol:
            return RootResult(mid, i, True)
        if (f_mid < 0) == (f_lo < 0):
            lo, f_lo = mid, f_mid
        else:
            hi = mid
    return RootResult(0.5 * (lo + hi), max_iter, False)


def newton(f: Fn, df: Fn, x0: float, tol: float = 1e-12, max_iter: int = 50) -> RootResult:
    """Follow the tangent line to where it crosses zero: x_new = x - f(x) / f'(x).

    Near a simple root the number of correct digits roughly doubles each step ("quadratic
    convergence"). Far from the root, or where f' is close to 0, steps can shoot off.
    """
    x = x0
    for i in range(1, max_iter + 1):
        fx, dfx = f(x), df(x)
        if dfx == 0:
            return RootResult(x, i, False)          # flat tangent: no crossing point
        step = fx / dfx
        x -= step
        if abs(step) < tol * (1 + abs(x)):
            return RootResult(x, i, True)
    return RootResult(x, max_iter, False)


def secant(f: Fn, x0: float, x1: float, tol: float = 1e-12, max_iter: int = 100) -> RootResult:
    """Newton's method with the derivative replaced by the slope through the last two points.

    Useful when f' is unavailable or expensive. One new f evaluation per step.
    """
    f0, f1 = f(x0), f(x1)
    for i in range(1, max_iter + 1):
        if f1 == f0:
            return RootResult(x1, i, False)
        x2 = x1 - f1 * (x1 - x0) / (f1 - f0)
        if abs(x2 - x1) < tol * (1 + abs(x2)):
            return RootResult(x2, i, True)
        x0, f0, x1, f1 = x1, f1, x2, f(x2)
    return RootResult(x1, max_iter, False)


def safeguarded_newton(f: Fn, df: Fn, lo: float, hi: float, x0: float | None = None,
                       tol: float = 1e-12, max_iter: int = 100) -> RootResult:
    """Newton's speed with bisection's guarantee: the production choice.

    Keep a bracket [lo, hi] around the root. Take the Newton step if it lands inside the
    bracket; otherwise (or if the derivative is 0) take a bisection step. Shrink the bracket
    using the sign of f at each new point. (Brent's method, scipy.optimize.brentq, uses the
    same idea without needing a derivative.)
    """
    f_lo = f(lo)
    if f_lo * f(hi) > 0:
        raise ValueError("f(lo) and f(hi) must have opposite signs")
    x = 0.5 * (lo + hi) if x0 is None else min(max(x0, lo), hi)
    for i in range(1, max_iter + 1):
        fx = f(x)
        if fx == 0:
            return RootResult(x, i, True)
        if (fx < 0) == (f_lo < 0):                  # shrink the bracket
            lo, f_lo = x, fx
        else:
            hi = x
        dfx = df(x)
        x_new = x - fx / dfx if dfx != 0 else math.nan
        if not (lo < x_new < hi):                   # Newton left the bracket: bisect instead
            x_new = 0.5 * (lo + hi)
        if abs(x_new - x) < tol * (1 + abs(x_new)) or hi - lo < tol:
            return RootResult(x_new, i, True)
        x = x_new
    return RootResult(x, max_iter, False)


def implied_vol(price: float, S: float, K: float, T: float, r: float,
                call: bool = True) -> RootResult:
    """Volatility that makes the Black-Scholes price equal the market price.

    - The derivative of price with respect to volatility is vega, so Newton is natural.
    - Starting guess: sigma ~ sqrt(2*pi/T) * price / S (a formula for at-the-money options,
      from Brenner and Subrahmanyam), kept inside the bracket.
    - Deep in- or out-of-the-money, vega is tiny and plain Newton overshoots badly, which is
      why the safeguarded version is used.
    """
    disc_k = K * math.exp(-r * T)
    lower = max(S - disc_k, 0.0) if call else max(disc_k - S, 0.0)
    upper = S if call else disc_k
    if not (lower < price < upper):
        raise ValueError("price is outside the no-arbitrage bounds; no implied volatility exists")
    guess = math.sqrt(2 * math.pi / T) * price / S
    return safeguarded_newton(
        lambda v: bs_price(S, K, T, r, v, call) - price,
        lambda v: bs_vega(S, K, T, r, v),
        lo=1e-6, hi=10.0, x0=guess,
    )


def bond_yield(price: float, coupon_rate: float, years: int, face: float = 100.0,
               freq: int = 2) -> RootResult:
    """Yield to maturity: the single annual rate (compounded `freq` times a year) that makes
    the discounted cash flows equal the price. The derivative of price with respect to yield
    is minus (price x modified duration), so Newton converges in a handful of steps.
    """
    n = years * freq
    c = face * coupon_rate / freq
    times = range(1, n + 1)

    def pv(y: float) -> float:
        d = 1 + y / freq
        return sum(c / d**k for k in times) + face / d**n - price

    def dpv(y: float) -> float:
        d = 1 + y / freq
        return -sum(k * c / d ** (k + 1) for k in times) / freq - n * face / d ** (n + 1) / freq

    return newton(pv, dpv, x0=coupon_rate if coupon_rate > 0 else 0.05)
