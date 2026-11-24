import math

import numpy as np
import pytest
from scipy.optimize import brentq

from quantprep.black_scholes import bs_price
from quantprep.numerics.optimization import gradient_descent, levenberg_marquardt, newton_minimize
from quantprep.numerics.root_finding import (
    bisection,
    bond_yield,
    implied_vol,
    newton,
    safeguarded_newton,
    secant,
)

f = lambda x: x**3 - 2 * x - 5          # classic example; root ≈ 2.0945514815
df = lambda x: 3 * x**2 - 2
ROOT = brentq(f, 2, 3, xtol=1e-15)


def test_all_methods_find_root_and_newton_is_fastest():
    results = {
        "bisection": bisection(f, 2, 3),
        "newton": newton(f, df, 2.5),
        "secant": secant(f, 2, 3),
        "safeguarded": safeguarded_newton(f, df, 2, 3),
    }
    for name, res in results.items():
        assert res.converged, name
        assert res.root == pytest.approx(ROOT, abs=1e-10), name
    assert results["bisection"].iterations >= 35          # ~1 binary digit per step
    assert results["newton"].iterations <= 7              # digits double per step
    assert results["secant"].iterations < results["bisection"].iterations


def test_newton_error_squares_each_step():
    """Quadratic convergence: e_{n+1} ≈ C * e_n^2, with C = f''/(2 f') at the root."""
    x, errors = 3.0, []
    for _ in range(4):
        x -= f(x) / df(x)
        errors.append(abs(x - ROOT))
    C = (6 * ROOT) / (2 * df(ROOT))
    assert errors[3] / errors[2] ** 2 == pytest.approx(C, rel=0.05)


def test_plain_newton_can_fail_but_safeguarded_does_not():
    g = math.atan                       # root at 0; from |x0| > ~1.39 Newton overshoots and diverges
    dg = lambda x: 1 / (1 + x * x)
    assert not newton(g, dg, 2.0).converged
    res = safeguarded_newton(g, dg, -5, 10, x0=2.0)
    assert res.converged and abs(res.root) < 1e-10


@pytest.mark.parametrize("K", [50, 80, 100, 120, 200])
@pytest.mark.parametrize("call", [True, False])
def test_implied_vol_round_trip(K, call):
    S, T, r, vol = 100.0, 0.5, 0.03, 0.35
    price = bs_price(S, K, T, r, vol, call)
    res = implied_vol(price, S, K, T, r, call)
    assert res.converged and res.root == pytest.approx(vol, abs=1e-7)


def test_implied_vol_rejects_arbitrage_price():
    with pytest.raises(ValueError):
        implied_vol(0.0, 100, 100, 1.0, 0.0)  # a call can't be worth 0 here


def test_bond_yield():
    par = bond_yield(100.0, 0.05, 10)          # a bond priced at par yields its coupon
    assert par.converged and par.root == pytest.approx(0.05, abs=1e-10)
    cheap = bond_yield(95.0, 0.05, 10)
    assert cheap.root > 0.05 and cheap.iterations <= 6


# ---------- optimisation ----------
A = np.diag([1.0, 100.0])                # condition number 100: a long narrow valley
quad_grad = lambda x: A @ x
quad_f = lambda x: 0.5 * x @ A @ x
quad_hess = lambda x: A


def test_gd_slow_on_ill_conditioned_quadratic_newton_one_step():
    gd = gradient_descent(quad_grad, [1.0, 1.0], lr=1 / 100)       # lr = 1 / L
    nt = newton_minimize(quad_f, quad_grad, quad_hess, [1.0, 1.0])
    assert gd.converged and nt.converged
    assert gd.iterations > 1000          # ~ condition number × log(1/tolerance)
    assert nt.iterations <= 2            # exact in one step for a quadratic (+1 to confirm)
    assert np.allclose(nt.x, 0)


def test_momentum_helps_and_too_large_lr_diverges():
    plain = gradient_descent(quad_grad, [1.0, 1.0], lr=1 / 100)
    heavy = gradient_descent(quad_grad, [1.0, 1.0], lr=1 / 100, momentum=0.8)
    assert heavy.iterations < plain.iterations / 3
    assert not gradient_descent(quad_grad, [1.0, 1.0], lr=2.1 / 100, max_iter=5000).converged


def rosen(x):
    return (1 - x[0]) ** 2 + 100 * (x[1] - x[0] ** 2) ** 2


def rosen_grad(x):
    return np.array([-2 * (1 - x[0]) - 400 * x[0] * (x[1] - x[0] ** 2), 200 * (x[1] - x[0] ** 2)])


def rosen_hess(x):
    return np.array([[2 - 400 * (x[1] - 3 * x[0] ** 2), -400 * x[0]], [-400 * x[0], 200.0]])


def test_rosenbrock_newton_vs_gd():
    nt = newton_minimize(rosen, rosen_grad, rosen_hess, [-1.2, 1.0])
    gd = gradient_descent(rosen_grad, [-1.2, 1.0], lr=1e-3, tol=1e-6, max_iter=200_000)
    assert nt.converged and np.allclose(nt.x, [1, 1], atol=1e-8)
    assert gd.converged and np.allclose(gd.x, [1, 1], atol=1e-4)
    assert nt.iterations < 50
    assert gd.iterations > 1000


def test_levenberg_marquardt_calibrates_curve():
    """Fit a discount-like curve y = a * exp(-b t) + c to noisy data, like calibrating a model."""
    rng = np.random.default_rng(0)
    t = np.linspace(0.25, 30, 40)
    true = np.array([0.8, 0.15, 0.2])
    y = true[0] * np.exp(-true[1] * t) + true[2] + rng.normal(0, 1e-4, t.size)

    def resid(p):
        return p[0] * np.exp(-p[1] * t) + p[2] - y

    def jac(p):
        e = np.exp(-p[1] * t)
        return np.column_stack([e, -p[0] * t * e, np.ones_like(t)])

    res = levenberg_marquardt(resid, jac, [0.5, 0.5, 0.0])
    assert res.converged and np.allclose(res.x, true, atol=1e-3)
