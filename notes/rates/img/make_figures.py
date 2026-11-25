"""Regenerate the figures for sabr.md and lmm.md:  uv run python notes/rates/img/make_figures.py"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from lmm_lib import (
    F0,
    T,
    abcd_vol,
    black,
    caplet_black,
    discount_factors,
    mc_swaption,
    rebonato_swaption_vol,
    swap_terms,
)
from sabr_lib import alpha_for_atm, black_call, normal_vols_bp, sabr_black_vol
from scipy.optimize import brentq

OUT = Path(__file__).parent
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]          # categorical slots 1-3, fixed order
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"

mpl.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
    "axes.titlesize": 11, "axes.titleweight": "bold", "axes.labelsize": 9.5,
    "xtick.color": INK_2, "ytick.color": INK_2, "xtick.labelsize": 9, "ytick.labelsize": 9,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
    "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
    "lines.linewidth": 2, "lines.solid_capstyle": "round", "legend.frameon": False,
    "legend.fontsize": 8.5, "legend.labelcolor": INK, "font.size": 9.5,
})

F, EXPIRY = 0.03, 5.0
STRIKES = np.linspace(0.005, 0.07, 120)
BASE = {"beta": 0.5, "rho": -0.3, "nu": 0.4}


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=150)
    plt.close(fig)


def smile(atm_black=0.25, **params):
    p = BASE | params
    a = params.get("alpha") or alpha_for_atm(F, EXPIRY, atm_black, p["beta"], p["rho"], p["nu"])
    return normal_vols_bp(F, STRIKES, EXPIRY, a, p["beta"], p["rho"], p["nu"])


def sabr_params():
    a0 = alpha_for_atm(F, EXPIRY, 0.25, **BASE)
    panels = [
        ("alpha: overall level", [({"alpha": a0 * m}, f"alpha = {a0 * m:.3f}") for m in (0.8, 1.0, 1.2)]),
        ("beta: backbone skew (ATM held fixed)", [({"beta": b}, f"beta = {b}") for b in (0.0, 0.5, 1.0)]),
        ("rho: skew (tilt)", [({"rho": r}, f"rho = {r}") for r in (-0.6, -0.3, 0.3)]),
        ("nu: smile curvature (wings)", [({"nu": n}, f"nu = {n}") for n in (0.2, 0.4, 0.8)]),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(8, 5.6), sharex=True)
    for ax, (title, cases) in zip(axes.flat, panels, strict=True):
        for color, (params, label) in zip(SERIES, cases, strict=True):
            ax.plot(STRIKES * 100, smile(**params), color=color, label=label)
        ax.axvline(F * 100, color=INK_2, linewidth=0.8)
        ax.set_title(title, loc="left")
        ax.legend(loc="upper right")
    for ax in axes[1]:
        ax.set_xlabel("strike (%)   [vertical line = forward 3%]")
    for ax in axes[:, 0]:
        ax.set_ylabel("normal vol (bp / year)")
    save(fig, "sabr_params.png")


def sabr_backbone():
    forwards = np.linspace(0.01, 0.06, 60)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for color, beta in zip(SERIES, (0.0, 0.5, 1.0), strict=True):
        a = alpha_for_atm(F, EXPIRY, 0.25, beta, 0.0, 0.3)       # same ATM vol at F = 3%
        atm = [normal_vols_bp(f, np.array([f]), EXPIRY, a, beta, 0.0, 0.3)[0] for f in forwards]
        ax.plot(forwards * 100, atm, color=color, label=f"beta = {beta}")
    ax.set_title("Backbone: how ATM normal vol moves when the forward moves", loc="left")
    ax.set_xlabel("forward rate (%)")
    ax.set_ylabel("ATM normal vol (bp / year)")
    ax.legend(loc="upper left")
    save(fig, "sabr_backbone.png")


def sabr_density():
    ks = np.linspace(0.0005, 0.08, 800)
    h = 1e-5
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for color, expiry in zip(SERIES, (1.0, 10.0, 30.0), strict=True):
        a = alpha_for_atm(F, expiry, 0.25, 0.5, -0.3, 0.6)

        def call(k, expiry=expiry, a=a):
            return black_call(F, k, expiry, sabr_black_vol(F, k, expiry, a, 0.5, -0.3, 0.6))

        density = (call(ks + h) - 2 * call(ks) + call(ks - h)) / h**2
        ax.plot(ks * 100, density / 100, color=color, label=f"expiry {expiry:.0f}y")
    ax.axhline(0, color=INK_2, linewidth=0.8)
    ax.set_ylim(-0.6, 1.2)
    ax.set_title("Implied density from Hagan's formula (nu = 0.6)", loc="left")
    ax.set_xlabel("rate at expiry (%)")
    ax.set_ylabel("probability per 1% of rate")
    ax.legend(loc="upper right")
    save(fig, "sabr_density.png")


def lmm_abcd():
    tau = np.linspace(0, 10, 200)
    cases = [((-0.02, 0.30, 1.0, 0.15), "humped: a=-0.02, b=0.30, c=1.0, d=0.15"),
             ((0.10, 0.00, 0.5, 0.12), "decaying: a=0.10, b=0, c=0.5, d=0.12"),
             ((0.00, 0.00, 1.0, 0.20), "flat: d=0.20")]
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for color, (p, label) in zip(SERIES, cases, strict=True):
        ax.plot(tau, 100 * abcd_vol(tau, *p), color=color, label=label)
    ax.set_title("abcd volatility: (a + b tau) exp(-c tau) + d", loc="left")
    ax.set_xlabel("time to expiry of the forward, tau (years)")
    ax.set_ylabel("lognormal vol (%)")
    ax.set_ylim(0, 30)
    ax.legend(loc="upper right")
    save(fig, "lmm_abcd.png")


def lmm_correlation():
    gap = np.linspace(0, 10, 200)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for color, beta in zip(SERIES, (0.05, 0.2, 0.5), strict=True):
        ax.plot(gap, np.exp(-beta * gap), color=color, label=f"beta = {beta}")
    ax.set_title("Correlation between two forwards: exp(-beta |Ti - Tj|)", loc="left")
    ax.set_xlabel("distance between the two forwards' dates (years)")
    ax.set_ylabel("correlation")
    ax.set_ylim(0, 1.02)
    ax.legend(loc="upper right")
    save(fig, "lmm_correlation.png")


def lmm_swaption_vs_corr():
    betas = np.array([0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0])
    _, annuity, S, _ = swap_terms(2, 7)
    rebonato = [100 * rebonato_swaption_vol(2, 7, b) for b in betas]
    mc_betas = betas[[0, 2, 4, 6]]
    mc = []
    for b in mc_betas:                                   # back out the Black vol of the MC price
        price = mc_swaption(2, 7, S, b, n_paths=50_000)
        mc.append(100 * brentq(lambda v, p=price: annuity * black(S, S, v**2 * T[2]) - p, 0.01, 1))
    P = discount_factors(F0)
    caplet = caplet_black(2, F0[2])                      # caplet on the first forward, 2y expiry
    caplet_vol = brentq(lambda v: P[3] * black(F0[2], F0[2], v**2 * T[2]) - caplet, 0.01, 1)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(betas, rebonato, color=SERIES[0], label="2y x 5y swaption vol (Rebonato formula)")
    ax.plot(mc_betas, mc, "o", color=SERIES[0], markersize=8, markeredgecolor=SURFACE,
            markeredgewidth=2, label="same, Monte Carlo")
    ax.axhline(100 * caplet_vol, color=SERIES[1],
               label="2y caplet vol on the first forward (does not depend on beta)")
    ax.set_title("Lower correlation lowers swaption vol; caplets are unchanged", loc="left")
    ax.set_xlabel("correlation decay beta")
    ax.set_ylabel("Black vol (%)")
    ax.set_ylim(10, 26)
    ax.legend(loc="lower left")
    save(fig, "lmm_swaption_vs_corr.png")


if __name__ == "__main__":
    for make in (sabr_params, sabr_backbone, sabr_density, lmm_abcd, lmm_correlation,
                 lmm_swaption_vs_corr):
        make()
        print("made", make.__name__)
