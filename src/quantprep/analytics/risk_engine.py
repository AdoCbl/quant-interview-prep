"""A small multi-asset risk engine: price a book, compute sensitivities, run what-if scenarios.

Design (the same shape as a production analytics service, scaled down):
- ``Market`` is an immutable snapshot (spots, vols, one flat rate). Bumping returns a new snapshot,
  so a scenario can never leak into the base case.
- Every instrument implements ``pv(market)``. Sensitivities come from bump-and-revalue, so any new
  instrument gets every Greek for free; options also have analytic Greeks to check against.
- ``Position`` = instrument x quantity, tagged with a book, so results aggregate up a hierarchy.
"""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from itertools import product
from types import MappingProxyType
from typing import Protocol

from scipy.stats import norm


# ---------------------------------------------------------------- market data
@dataclass(frozen=True, slots=True)
class Market:
    spots: Mapping[str, float]
    vols: Mapping[str, float]
    rate: float                          # flat, continuously compounded
    snapshot_id: str = "base"

    def __post_init__(self) -> None:     # freeze the dicts too
        object.__setattr__(self, "spots", MappingProxyType(dict(self.spots)))
        object.__setattr__(self, "vols", MappingProxyType(dict(self.vols)))

    def bump(self, *, spot: Mapping[str, float] | None = None, spot_rel: float = 0.0,
             vol: float = 0.0, rate: float = 0.0, tag: str = "bumped") -> Market:
        """Absolute spot bumps per name, a relative bump to every spot, absolute vol and rate."""
        spots = {k: (v + (spot or {}).get(k, 0.0)) * (1 + spot_rel) for k, v in self.spots.items()}
        vols = {k: v + vol for k, v in self.vols.items()}
        return replace(self, spots=spots, vols=vols, rate=self.rate + rate, snapshot_id=tag)


# ---------------------------------------------------------------- instruments
class Instrument(Protocol):
    underlying: str

    def pv(self, m: Market) -> float: ...


@dataclass(frozen=True, slots=True)
class EuropeanOption:
    underlying: str
    strike: float
    expiry: float                        # years
    call: bool = True

    def _d1_d2(self, m: Market) -> tuple[float, float, float, float]:
        s, v, t = m.spots[self.underlying], m.vols[self.underlying], self.expiry
        d1 = (math.log(s / self.strike) + (m.rate + 0.5 * v * v) * t) / (v * math.sqrt(t))
        return s, v, d1, d1 - v * math.sqrt(t)

    def pv(self, m: Market) -> float:
        s, _, d1, d2 = self._d1_d2(m)
        df = math.exp(-m.rate * self.expiry)
        if self.call:
            return s * norm.cdf(d1) - self.strike * df * norm.cdf(d2)
        return self.strike * df * norm.cdf(-d2) - s * norm.cdf(-d1)

    def analytic_greeks(self, m: Market) -> dict[str, float]:
        """Delta per 1.00 of spot, gamma per 1.00^2, vega per 1.00 of vol, rho per 1.00 of rate."""
        s, v, d1, d2 = self._d1_d2(m)
        t, df = self.expiry, math.exp(-m.rate * self.expiry)
        sign = 1 if self.call else -1
        return {
            "delta": norm.cdf(d1) if self.call else norm.cdf(d1) - 1,
            "gamma": norm.pdf(d1) / (s * v * math.sqrt(t)),
            "vega": s * norm.pdf(d1) * math.sqrt(t),
            "rho": sign * self.strike * t * df * norm.cdf(sign * d2),
        }


@dataclass(frozen=True, slots=True)
class Future:
    """Value of a futures position entered at ``trade_price`` (no dividends)."""

    underlying: str
    expiry: float
    trade_price: float
    multiplier: float = 1.0

    def pv(self, m: Market) -> float:
        fwd = m.spots[self.underlying] * math.exp(m.rate * self.expiry)
        return (fwd - self.trade_price) * self.multiplier


@dataclass(frozen=True, slots=True)
class Swap:
    """Receive fixed ``fixed_rate`` annually for ``years`` on ``notional``, against floating."""

    fixed_rate: float
    years: int
    notional: float = 1.0
    underlying: str = "USD"

    def pv(self, m: Market) -> float:
        dfs = [math.exp(-m.rate * t) for t in range(1, self.years + 1)]
        return self.notional * (self.fixed_rate * sum(dfs) - (1 - dfs[-1]))


# ---------------------------------------------------------------- positions and risk
@dataclass(frozen=True, slots=True)
class Position:
    instrument: Instrument
    quantity: float
    book: str = "default"
    tags: tuple[str, ...] = field(default=())


# Standard bump sizes: 1% of spot, 1 vol point, 1 basis point
SPOT_REL, VOL_BUMP, RATE_BUMP = 0.01, 0.01, 0.0001


def bump_greeks(inst: Instrument, m: Market) -> dict[str, float]:
    """Central-difference sensitivities, reported in the same units as ``analytic_greeks``.

    dollar_delta / dollar_gamma are per 1% move; dv01 is the PV change for +1 bp in rates.
    """
    name = inst.underlying
    s = m.spots.get(name)
    out: dict[str, float] = {}
    base = inst.pv(m)
    if s is not None:
        h = s * SPOT_REL
        up, dn = inst.pv(m.bump(spot={name: h})), inst.pv(m.bump(spot={name: -h}))
        out["delta"] = (up - dn) / (2 * h)
        out["gamma"] = (up - 2 * base + dn) / (h * h)
    if name in m.vols:
        up, dn = inst.pv(m.bump(vol=VOL_BUMP)), inst.pv(m.bump(vol=-VOL_BUMP))
        out["vega"] = (up - dn) / (2 * VOL_BUMP)
    up, dn = inst.pv(m.bump(rate=RATE_BUMP)), inst.pv(m.bump(rate=-RATE_BUMP))
    out["rho"] = (up - dn) / (2 * RATE_BUMP)
    out["dv01"] = out["rho"] * RATE_BUMP
    return out


def book_risk(positions: list[Position], m: Market) -> dict[str, dict[str, float]]:
    """PV and Greeks summed per book (PV and first-order Greeks are additive)."""
    agg: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for p in positions:
        agg[p.book]["pv"] += p.quantity * p.instrument.pv(m)
        for k, v in bump_greeks(p.instrument, m).items():
            agg[p.book][k] += p.quantity * v
    return {b: dict(v) for b, v in agg.items()}


def scenario_grid(positions: list[Position], m: Market, spot_moves: list[float],
                  vol_moves: list[float], rate_moves: list[float] = (0.0,)
                  ) -> dict[tuple[float, float, float], float]:
    """Full-revaluation P&L for every (relative spot move, vol move, rate move)."""
    base = sum(p.quantity * p.instrument.pv(m) for p in positions)
    out = {}
    for ds, dv, dr in product(spot_moves, vol_moves, rate_moves):
        shocked = m.bump(spot_rel=ds, vol=dv, rate=dr, tag=f"s{ds:+}/v{dv:+}/r{dr:+}")
        out[ds, dv, dr] = sum(p.quantity * p.instrument.pv(shocked) for p in positions) - base
    return out


def taylor_pnl(greeks: Mapping[str, float], spot: float, ds_rel: float, dvol: float,
               drate: float) -> float:
    """Second-order estimate: delta*dS + 1/2 gamma*dS^2 + vega*dvol + rho*drate."""
    ds = spot * ds_rel
    return (greeks.get("delta", 0) * ds + 0.5 * greeks.get("gamma", 0) * ds * ds
            + greeks.get("vega", 0) * dvol + greeks.get("rho", 0) * drate)
