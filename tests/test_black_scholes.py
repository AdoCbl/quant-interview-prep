from math import exp

from quantprep.black_scholes import bs_price


def test_put_call_parity():
    S, K, T, r, sigma = 100.0, 95.0, 0.5, 0.03, 0.2
    c = bs_price(S, K, T, r, sigma, call=True)
    p = bs_price(S, K, T, r, sigma, call=False)
    assert abs((c - p) - (S - K * exp(-r * T))) < 1e-10
