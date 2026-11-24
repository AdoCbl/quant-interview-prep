"""Black-Scholes pricing for European options (seed example)."""

from math import exp, log, sqrt

from scipy.stats import norm


def bs_price(S: float, K: float, T: float, r: float, sigma: float, call: bool = True) -> float:
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)
    if call:
        return S * norm.cdf(d1) - K * exp(-r * T) * norm.cdf(d2)
    return K * exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)


def bs_vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Sensitivity of the option price to volatility (same for calls and puts)."""
    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    return S * norm.pdf(d1) * sqrt(T)
