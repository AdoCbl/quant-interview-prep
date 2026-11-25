"""Small lognormal LIBOR/forward market model (LMM) toolkit for the LMM page and its figures."""

import numpy as np
from scipy.stats import norm

TAU = 1.0                                   # annual periods
N = 10                                      # forwards F_1..F_10 cover [1, 11] years
T = np.arange(0, N + 2, dtype=float)        # tenor dates T_0..T_11
F0 = np.full(N + 1, 0.035)                  # F_i spans [T_i, T_i+1]; F_0 has already fixed


def abcd_vol(time_to_expiry, a=-0.02, b=0.30, c=1.0, d=0.15):
    """Rebonato's abcd shape: vol of a forward as a function of its time to expiry."""
    tau = np.maximum(time_to_expiry, 0.0)
    return (a + b * tau) * np.exp(-c * tau) + d


def correlation(beta):
    """rho_ij = exp(-beta |T_i - T_j|) for forwards 1..N (index 0 unused)."""
    return np.exp(-beta * np.abs(T[:, None] - T[None, :]))[: N + 1, : N + 1]


def discount_factors(F):
    """P(0, T_k) for k = 0..N+1 from the forwards."""
    return np.r_[1.0, np.cumprod(1 / (1 + TAU * F))]           # F[0] spans [T_0, T_1], already fixed


def black(F, K, var):
    sd = np.sqrt(var)
    d1 = (np.log(F / K) + 0.5 * var) / sd
    return F * norm.cdf(d1) - K * norm.cdf(d1 - sd)


def integrated_cov(i, j, t_end, beta, n=400):
    """rho_ij * integral_0^t_end sigma_i(t) sigma_j(t) dt."""
    t = np.linspace(0, t_end, n)
    integrand = abcd_vol(T[i] - t) * abcd_vol(T[j] - t)
    return correlation(beta)[i, j] * np.trapezoid(integrand, t)


def caplet_black(k, K):
    P = discount_factors(F0)
    return P[k + 1] * TAU * black(F0[k], K, integrated_cov(k, k, T[k], 0.0))


def swap_terms(start, end):
    """Forward indices, annuity and forward swap rate for a swap from T_start to T_end."""
    P = discount_factors(F0)
    idx = np.arange(start, end)
    annuity = TAU * P[idx + 1].sum()
    weights = TAU * P[idx + 1] / annuity
    return idx, annuity, float(weights @ F0[idx]), weights


def rebonato_swaption_vol(start, end, beta):
    """Rebonato's approximation of the Black vol of the forward swap rate."""
    idx, _, S, w = swap_terms(start, end)
    var = sum(w[a] * w[b] * F0[i] * F0[j] * integrated_cov(i, j, T[start], beta)
              for a, i in enumerate(idx) for b, j in enumerate(idx))
    return np.sqrt(var / T[start]) / S


def simulate_to(t_end, beta, n_paths=100_000, dt=0.05, seed=0):
    """Forwards at t_end under the terminal measure (numeraire P(t, T_N+1)), log-Euler steps."""
    rng = np.random.default_rng(seed)
    chol = np.linalg.cholesky(correlation(beta)[1:, 1:])
    logF = np.tile(np.log(F0[1:]), (n_paths, 1))
    rho = correlation(beta)[1:, 1:]
    for step in range(round(t_end / dt)):
        t = step * dt
        alive = T[1 : N + 1] > t + 1e-12                         # a forward stops after it fixes
        vol = abcd_vol(T[1 : N + 1] - t) * alive
        Fx = np.exp(logF)
        g = TAU * vol * Fx / (1 + TAU * Fx)                      # shape (paths, N)
        # drift_i = -vol_i * sum_{j > i} rho_ij g_j  (terminal measure)
        later = (rho * np.triu(np.ones((N, N)), 1)) @ g.T        # (N, paths)
        drift = -vol * later.T - 0.5 * vol**2
        z = rng.standard_normal((n_paths, N)) @ chol.T
        logF += drift * dt + vol * np.sqrt(dt) * z
    out = np.empty((n_paths, N + 1))
    out[:, 0] = np.nan
    out[:, 1:] = np.exp(logF)
    return out


def mc_swaption(start, end, K, beta, **kw):
    """Payer swaption price by Monte Carlo, expiring at T_start."""
    F = simulate_to(T[start], beta, **kw)
    # P(T_start, T_k) for k > start, then rebase to the terminal bond P(T_start, T_N+1)
    growth = np.cumprod(1 / (1 + TAU * F[:, start:]), axis=1)    # P(T_start, T_start+1 ..)
    annuity = TAU * growth[:, : end - start].sum(axis=1)
    swap = (1 - growth[:, end - start - 1]) / annuity
    payoff = annuity * np.maximum(swap - K, 0)
    terminal = growth[:, -1]                                     # P(T_start, T_N+1)
    P = discount_factors(F0)
    return P[-1] * np.mean(payoff / terminal)


def mc_caplet(k, K, beta=0.1, **kw):
    F = simulate_to(T[k], beta, **kw)
    growth = np.cumprod(1 / (1 + TAU * F[:, k:]), axis=1)
    payoff_at_pay = TAU * np.maximum(F[:, k] - K, 0)
    value_at_fix = payoff_at_pay * growth[:, 0]                  # discount T_k+1 -> T_k
    P = discount_factors(F0)
    return P[-1] * np.mean(value_at_fix / growth[:, -1])
