"""Small SABR toolkit shared by the SABR page and its figures."""

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm


def sabr_black_vol(F, K, T, alpha, beta, rho, nu):
    """Hagan et al. (2002) lognormal (Black) implied volatility."""
    F, K = np.asarray(F, float), np.asarray(K, float)
    fk = F * K
    log_fk = np.log(F / K)
    one_b = 1 - beta
    denom = fk ** (one_b / 2) * (1 + one_b**2 / 24 * log_fk**2 + one_b**4 / 1920 * log_fk**4)
    z = nu / alpha * fk ** (one_b / 2) * log_fk
    x = np.log((np.sqrt(1 - 2 * rho * z + z**2) + z - rho) / (1 - rho))
    z_over_x = np.where(np.abs(z) < 1e-8, 1.0, z / np.where(np.abs(x) < 1e-12, 1.0, x))
    correction = 1 + (one_b**2 / 24 * alpha**2 / fk**one_b
                      + rho * beta * nu * alpha / (4 * fk ** (one_b / 2))
                      + (2 - 3 * rho**2) / 24 * nu**2) * T
    return alpha / denom * z_over_x * correction


def alpha_for_atm(F, T, atm_vol, beta, rho, nu):
    """Alpha that gives a chosen at-the-money Black vol (keeps the level fixed)."""
    return brentq(lambda a: sabr_black_vol(F, F, T, a, beta, rho, nu) - atm_vol, 1e-6, 5.0)


def black_call(F, K, T, vol):
    d1 = (np.log(F / K) + 0.5 * vol**2 * T) / (vol * np.sqrt(T))
    return F * norm.cdf(d1) - K * norm.cdf(d1 - vol * np.sqrt(T))


def bachelier_call(F, K, T, vol):
    d = (F - K) / (vol * np.sqrt(T))
    return (F - K) * norm.cdf(d) + vol * np.sqrt(T) * norm.pdf(d)


def normal_vol(F, K, T, black_vol):
    """Convert a Black vol to the normal (Bachelier) vol with the same price."""
    price = black_call(F, K, T, black_vol)
    return brentq(lambda v: bachelier_call(F, K, T, v) - price, 1e-6, 0.2)


def normal_vols_bp(F, strikes, T, alpha, beta, rho, nu):
    vols = sabr_black_vol(F, strikes, T, alpha, beta, rho, nu)
    return np.array([normal_vol(F, k, T, v) for k, v in zip(strikes, vols, strict=True)]) * 1e4
