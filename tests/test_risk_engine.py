import math

import pytest

from quantprep.analytics import (
    EuropeanOption,
    Future,
    Market,
    Position,
    Swap,
    book_risk,
    bump_greeks,
    scenario_grid,
    taylor_pnl,
)

M = Market(spots={"SPX": 100.0}, vols={"SPX": 0.2}, rate=0.03)


def test_put_call_parity():
    c = EuropeanOption("SPX", 105, 0.5, call=True).pv(M)
    p = EuropeanOption("SPX", 105, 0.5, call=False).pv(M)
    assert c - p == pytest.approx(100 - 105 * math.exp(-0.03 * 0.5), abs=1e-12)


@pytest.mark.parametrize("call", [True, False])
def test_bump_matches_analytic(call):
    opt = EuropeanOption("SPX", 95, 1.0, call=call)
    a, b = opt.analytic_greeks(M), bump_greeks(opt, M)
    assert b["delta"] == pytest.approx(a["delta"], rel=1e-3)
    assert b["gamma"] == pytest.approx(a["gamma"], rel=1e-3)
    assert b["vega"] == pytest.approx(a["vega"], rel=1e-3)
    assert b["rho"] == pytest.approx(a["rho"], rel=1e-6)


def test_future_delta_is_forward_factor_and_no_vega():
    fut = Future("SPX", 0.25, trade_price=100.0, multiplier=50)
    g = bump_greeks(fut, M)
    assert g["delta"] == pytest.approx(50 * math.exp(0.03 * 0.25), rel=1e-12)
    assert g["gamma"] == pytest.approx(0, abs=1e-6)
    assert g["vega"] == pytest.approx(0, abs=1e-12)


def test_par_swap_has_zero_pv_and_negative_dv01():
    dfs = [math.exp(-0.03 * t) for t in range(1, 6)]
    par = (1 - dfs[-1]) / sum(dfs)
    swap = Swap(par, 5, notional=1e6)
    assert swap.pv(M) == pytest.approx(0, abs=1e-6)
    assert bump_greeks(swap, M)["dv01"] < 0      # receiver: loses when rates rise
    annuity = sum(t * d for t, d in zip(range(1, 6), dfs, strict=True))
    assert bump_greeks(swap, M)["dv01"] == pytest.approx(
        -1e6 * 1e-4 * (par * annuity + 5 * dfs[-1]), rel=1e-6)


def test_market_is_immutable_and_bump_does_not_leak():
    bumped = M.bump(spot_rel=0.1, vol=0.05)
    assert M.spots["SPX"] == 100.0 and M.vols["SPX"] == 0.2
    assert bumped.spots["SPX"] == pytest.approx(110.0)
    with pytest.raises(TypeError):
        M.spots["SPX"] = 1.0  # type: ignore[index]


def test_book_risk_is_additive():
    a = Position(EuropeanOption("SPX", 100, 1.0), 10, book="opts")
    b = Position(EuropeanOption("SPX", 110, 0.5, call=False), -5, book="opts")
    c = Position(Future("SPX", 1.0, 100.0), -6, book="hedge")
    risk = book_risk([a, b, c], M)
    expected = 10 * bump_greeks(a.instrument, M)["delta"] - 5 * bump_greeks(b.instrument, M)["delta"]
    assert risk["opts"]["delta"] == pytest.approx(expected)
    assert set(risk) == {"opts", "hedge"}


def test_scenario_grid_zero_shock_and_taylor():
    book = [Position(EuropeanOption("SPX", 100, 1.0), 10)]
    grid = scenario_grid(book, M, [-0.01, 0.0, 0.01], [0.0, 0.01])
    assert grid[0.0, 0.0, 0.0] == pytest.approx(0, abs=1e-12)
    g = {k: 10 * v for k, v in bump_greeks(book[0].instrument, M).items()}
    # small shocks: second-order Taylor within 2% of full revaluation
    assert taylor_pnl(g, 100, 0.01, 0.01, 0) == pytest.approx(grid[0.01, 0.01, 0.0], rel=0.02)
