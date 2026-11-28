# Domain Knowledge: Proprietary Trading, Futures and the Middle Office

What a proprietary trading firm does, how a trade moves from execution to settlement, and the
products a multi-asset trading firm deals in every day: futures, Treasury and SOFR
futures, options on futures, and a quick tour of equity index, energy and crypto. The angle is
what a quant developer building analytics (positions, P&L, risk, margin) needs to know. Each term
is explained the first time it appears; a glossary is at the end. Formulas come first, then numbers.

Every code block runs on its own (`uv run python file.py`); the block after it shows its output.
Related pages: curves, swaps and DV01 in [interest rates](../rates/README.md), Greeks and duration
in [finance](../finance/README.md), order books and hedging in
[market making](../market-making/README.md), and risk and P&L systems in
[system design](../system-design/README.md).

Contents:

1. [How a proprietary trading firm works](#1-how-a-proprietary-trading-firm-works)
2. [The life of a trade](#2-the-life-of-a-trade)
3. [Futures mechanics](#3-futures-mechanics)
4. [Positions and P&L](#4-positions-and-pl)
5. [Treasury futures and the basis](#5-treasury-futures-and-the-basis)
6. [SOFR futures](#6-sofr-futures)
7. [Options on futures: P&L explain and margin](#7-options-on-futures-pl-explain-and-margin)
8. [Other asset classes in brief](#8-other-asset-classes-in-brief)
9. [The market calendar](#9-the-market-calendar)
10. [What an analytics team builds](#10-what-an-analytics-team-builds)
11. [Interview questions](#11-interview-questions)
12. [Glossary](#12-glossary)

---

## 1. How a proprietary trading firm works

A **proprietary ("prop") trading firm** trades only its own capital. It has no clients and no
client money, so it earns nothing from fees: all revenue is trading P&L (profit and loss).

| Function | What it does |
|---|---|
| **Trading desks** | Grouped by product (rates, energy, equities, crypto, options). Make markets, trade relative value (one instrument against a related one), or take directional views. |
| **Quant research** | Builds signals, pricing models and fair values. |
| **Quant development / engineering** | Builds trading systems, pricing libraries, data pipelines and analytics. |
| **Risk** | Sets and monitors limits (DV01, Greeks, loss limits, concentration); runs stress tests. |
| **Middle office** | Owns the "official" view of positions and P&L: trade capture checks, end-of-day marks, P&L explain, reconciliation with brokers and exchanges. |
| **Operations / back office** | Clearing, margin payments, settlement, fees, accounting. |

Typical styles at such a firm:

- **Market making**: quote both sides on an exchange and earn the bid-ask spread.
- **Relative value**: Treasury cash vs futures (the basis), futures calendar spreads, swap spreads, curve trades.
- **Volatility trading**: options on rates, energy or equity futures, delta-hedged, so the P&L comes from realised vs implied volatility.
- **Longer-horizon** discretionary or systematic positions.

What makes the analytics hard: many products, many venues, very high trade counts, positions that
must be right to the contract before the next open, and P&L that traders, risk and finance must all agree on.

---

## 2. The life of a trade

1. **Order and execution**: a trader or algorithm sends an order to an exchange (e.g. CME, the Chicago Mercantile Exchange, for US rates, equity index and energy futures) and receives fills.
2. **Trade capture**: each fill is booked into the firm's trade store. The exchange and the broker also send a **drop copy**: an independent copy of the fills, used to check that nothing was missed.
3. **Clearing**: the trade is given up to a **clearing broker** (an FCM, futures commission merchant). The **clearing house** (CCP, central counterparty) then becomes the buyer to every seller and the seller to every buyer, so nobody is exposed to the original counterparty.
4. **Margin**: the clearing house requires **initial margin** (a deposit sized to cover a bad day) and pays or collects **variation margin** every day: the change in value of the position at the official **settlement price**.
5. **End of day**: positions are marked at settlement prices, P&L is computed and explained, and internal positions are **reconciled** against the clearing broker's statement. Any mismatch is a **break** and must be fixed before the next session.
6. **Expiry or delivery**: futures are rolled to the next contract, cash-settled, or physically delivered (Treasury futures deliver bonds; crude oil delivers barrels).

---

## 3. Futures mechanics

A **future** is an exchange-traded agreement to buy or sell something at a set price on a later
date. Gains and losses are paid in cash every day, so the contract's value resets to zero each night.

- **Contract multiplier**: dollars per 1.00 move in the quoted price. **Tick**: the smallest allowed price move.
- `tick value = multiplier × tick size`
- `daily variation margin = (settle_today − settle_yesterday) × multiplier × quantity`
- The sum of daily variation margin always equals `(last settle − entry price) × multiplier × quantity`.

Contract codes are a root plus a month letter plus a year: `ZNH7` = 10-year note future, March 2027.
Month letters: F Jan, G Feb, H Mar, J Apr, K May, M Jun, N Jul, Q Aug, U Sep, V Oct, X Nov, Z Dec.
Treasury prices are quoted in 32nds of a point: `110-16+` = 110 + 16.5/32 = 110.515625.

```python
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Future:
    name: str
    multiplier: float       # dollars per 1.00 move in the quoted price
    tick: float             # smallest allowed price move

    @property
    def tick_value(self) -> float:
        return self.multiplier * self.tick


def parse_32nds(quote: str) -> float:
    """Treasury quote '110-16+' = 110 + 16.5/32. A trailing '+' means half a 32nd."""
    whole, frac = quote.split("-")
    half = 0.5 if frac.endswith("+") else 0.0
    return int(whole) + (int(frac.rstrip("+")) + half) / 32


specs = [
    Future("ES  S&P 500 E-mini", 50, 0.25),
    Future("ZN  10y Treasury note", 1000, 1 / 64),     # $100k face; price in % of par
    Future("ZT  2y Treasury note", 2000, 1 / 256),     # $200k face
    Future("SR3 3m SOFR", 2500, 0.005),                # $25 per basis point
    Future("CL  WTI crude oil", 1000, 0.01),           # 1,000 barrels
]
for f in specs:
    print(f"{f.name:24s} tick {f.tick:<11.8g} = ${f.tick_value:g}")

# Daily variation margin on a long 10 ZN position
zn, qty = specs[1], 10
entry = parse_32nds("110-16")
settles = [parse_32nds(q) for q in ("110-13", "110-23", "110-19")]
prev, total = entry, 0.0
for day, s in enumerate(settles, 1):
    vm = (s - prev) * zn.multiplier * qty   # cash paid (-) or received (+) today
    total += vm
    prev = s
    print(f"day {day}: settle {s:.5f}  variation margin {vm:+,.2f}")
print(f"total {total:+,.2f} = (last settle - entry) x 1000 x 10 = {(prev - entry) * 1000 * qty:+,.2f}")
```

Output:

```text
ES  S&P 500 E-mini       tick 0.25        = $12.5
ZN  10y Treasury note    tick 0.015625    = $15.625
ZT  2y Treasury note     tick 0.00390625  = $7.8125
SR3 3m SOFR              tick 0.005       = $12.5
CL  WTI crude oil        tick 0.01        = $10
day 1: settle 110.40625  variation margin -937.50
day 2: settle 110.71875  variation margin +3,125.00
day 3: settle 110.59375  variation margin -1,250.00
total +937.50 = (last settle - entry) x 1000 x 10 = +937.50
```

---

## 4. Positions and P&L

- **Realised P&L**: locked in by closing trades. **Unrealised P&L**: open position × (mark − cost).
- `total P&L = realised + unrealised`, and the total does not depend on the cost method.
- **FIFO** (first in, first out) closes the oldest lots first. **Average cost** keeps one blended entry price. The same fills give the same total, but a different split between realised and unrealised. That split matters for tax, for accounting, and for reports such as "realised P&L today".
- A **position flip** (long 10, sell 25, now short 15) must close the old lots and open a new lot at the fill price.
- **Marks**: futures use the exchange settlement price. Over-the-counter (OTC) products, which do not trade on an exchange, use curve or model marks, checked by **independent price verification (IPV)**.
- **Fees** (exchange, clearing, broker) and **financing** (repo, cash interest) are part of P&L, so book them separately so they can be explained.

```python
from collections import deque


def fifo_pnl(fills: list[tuple[int, float]], mark: float) -> tuple[float, float]:
    """fills = (signed quantity, price). Returns (realised, unrealised) under first-in-first-out."""
    lots: deque[list[float]] = deque()      # open lots [signed qty, price], all the same sign
    realised = 0.0
    for qty, px in fills:
        while qty and lots and (lots[0][0] > 0) != (qty > 0):   # fill closes existing lots
            lot = lots[0]
            close = min(abs(qty), abs(lot[0])) * (1 if lot[0] > 0 else -1)
            realised += close * (px - lot[1])
            lot[0] -= close
            qty += close
            if lot[0] == 0:
                lots.popleft()
        if qty:
            lots.append([qty, px])                               # what is left opens a new lot
    unrealised = sum(q * (mark - p) for q, p in lots)
    return realised, unrealised


def avg_cost_pnl(fills: list[tuple[int, float]], mark: float) -> tuple[float, float]:
    pos, avg, realised = 0, 0.0, 0.0
    for qty, px in fills:
        if pos == 0 or (pos > 0) == (qty > 0):                   # adding: update the average
            avg = (avg * pos + px * qty) / (pos + qty)
            pos += qty
        else:                                                    # reducing (maybe flipping)
            close = -qty if abs(qty) <= abs(pos) else pos
            realised += close * (px - avg)
            pos += qty
            if pos and (pos > 0) == (qty > 0):                   # flipped: rest opens at px
                avg = px
    return realised, pos * (mark - avg)


fills = [(+100, 10.0), (+50, 11.0), (-120, 12.0), (+30, 9.0)]
for name, fn in (("FIFO", fifo_pnl), ("average cost", avg_cost_pnl)):
    r, u = fn(fills, mark=11.5)
    print(f"{name:12s} realised {r:7.2f}  unrealised {u:7.2f}  total {r + u:7.2f}")

print(fifo_pnl([(+10, 100.0), (-25, 103.0)], mark=101.0))       # flip to short 15

# Reconciliation: internal positions vs the clearing broker's statement
internal = {"ZNH7": 120, "SR3M7": -400, "ESH7": 15, "CLG7": 0}
clearing = {"ZNH7": 120, "SR3M7": -350, "ESH7": 15, "ZBH7": 5}
breaks = {k: (internal.get(k, 0), clearing.get(k, 0))
          for k in internal.keys() | clearing.keys()
          if internal.get(k, 0) != clearing.get(k, 0)}
print(dict(sorted(breaks.items())))
```

Output:

```text
FIFO         realised  220.00  unrealised   90.00  total  310.00
average cost realised  200.00  unrealised  110.00  total  310.00
(30.0, 30.0)
{'SR3M7': (-400, -350), 'ZBH7': (0, 5)}
```

Each break in the reconciliation output needs a reason: a missed fill, a late give-up, an
allocation to the wrong account, or an expiry that was not processed.

---

## 5. Treasury futures and the basis

A Treasury future lets the seller deliver **any bond from a basket** (for the 10-year note
future, notes with 6½ to 10 years left). To make bonds comparable, each has a **conversion factor
(CF)**: roughly its price per $1 of face value at a 6% yield.

- **Invoice price** received by the seller: `futures price × CF + accrued interest`.
- **Cheapest to deliver (CTD)**: the bond that maximises the seller's profit at delivery. Ignoring carry, it is the bond with the lowest `price / CF`.
- **Gross basis**: `bond price − futures price × CF`.
- **Carry**: `coupon income − financing cost` = `accrued over the period − price × repo × days / 360`. **Repo** is borrowing cash against the bond as collateral; the repo rate is the financing cost.
- **Net basis**: `gross basis − carry`. It is the value of the seller's **delivery options**: choice of bond (quality option), choice of day in the delivery month (timing option), and late-day delivery after the futures price is fixed (wild card option). The CTD has the smallest net basis.
- **Implied repo rate (IRR)**: the financing rate at which buying the bond and delivering it into the future breaks even: `IRR = (F × CF + AI_delivery − P) / P × 360 / days`. Here `F` is the futures price, `AI` the accrued interest, `P` the bond price paid today (shown with no accrued because today is a coupon date). The CTD has the highest IRR.
- **Futures DV01** ≈ `DV01 of the CTD / CF`. **Hedge ratio** = `DV01 of the position / DV01 of one future`.

Why the CTD switches: at yields above 6%, long-duration bonds fall in price more than their conversion factors assume, so the longest bond becomes cheapest. Below 6%, the shortest bond is cheapest. A CTD switch changes the future's DV01, which is why the basis carries option value.

```python
def bond_price(coupon: float, years: float, y: float) -> float:
    """Clean price per 100 face, on a coupon date, semi-annual coupons, yield y."""
    n, c, r = round(years * 2), coupon / 2 * 100, y / 2
    return c * (1 - (1 + r) ** -n) / r + 100 * (1 + r) ** -n


def conversion_factor(coupon: float, years: float) -> float:
    """Price per 1 face at a 6% yield (exact here because maturities are whole half-years)."""
    return round(bond_price(coupon, years, 0.06) / 100, 4)


# Deliverable basket: (coupon, years to maturity at delivery)
basket = [(0.03875, 6.5), (0.0425, 7.5), (0.0400, 8.5), (0.04625, 9.5)]
cfs = [conversion_factor(c, t) for c, t in basket]
print("conversion factors", cfs)                    # see output below

# 1) Which bond is cheapest to deliver (CTD) depends on the yield level
for y in (0.03, 0.045, 0.06, 0.075):         # at exactly 6% every ratio is 100
    ratios = [bond_price(c, t, y) / cf for (c, t), cf in zip(basket, cfs, strict=True)]
    ctd = min(range(4), key=ratios.__getitem__)
    print(f"yield {y:.1%}: price/CF = {[round(x, 2) for x in ratios]}  CTD = bond {ctd}")

# 2) Fair futures price, basis and implied repo at a 4.5% yield, 90 days to delivery
y, repo, days = 0.045, 0.040, 90
fut = None
rows = []
for (c, t), cf in zip(basket, cfs, strict=True):
    p = bond_price(c, t, y)                         # today on a coupon date: no accrued
    accrued_at_delivery = c / 2 * 100 * days / 182
    forward = p * (1 + repo * days / 360) - accrued_at_delivery
    rows.append((p, cf, accrued_at_delivery, forward / cf))
fut = min(r[3] for r in rows)                       # seller delivers the cheapest bond
print(f"fair futures price {fut:.4f}")
for i, (p, cf, ai, _) in enumerate(rows):
    gross_basis = p - fut * cf
    carry = ai - p * repo * days / 360            # coupon earned minus financing cost
    net_basis = gross_basis - carry
    implied_repo = (fut * cf + ai - p) / p * 360 / days
    print(f"bond {i}: gross basis {gross_basis * 32:6.2f}  net basis {round(net_basis * 32, 2) + 0.0:6.2f} (32nds)"
          f"  implied repo {implied_repo:.3%}")

# 3) Futures DV01 and hedge ratio: DV01_future ~ DV01_CTD / CF
ctd = min(range(4), key=lambda i: rows[i][3])
c, t = basket[ctd]
dv01_ctd = (bond_price(c, t, y - 0.00005) - bond_price(c, t, y + 0.00005)) * 1000  # $ per bp, $100k
dv01_fut = dv01_ctd / cfs[ctd]
print(f"CTD DV01 ${dv01_ctd:.2f}/bp per $100k, future DV01 ${dv01_fut:.2f}/bp")
print(f"hedge a $25,000/bp swap book with {25_000 / dv01_fut:.0f} futures")
```

Output:

```text
conversion factors [0.887, 0.8955, 0.8683, 0.9015]
yield 3.0%: price/CF = [118.53, 120.98, 123.75, 125.73]  CTD = bond 0
yield 4.5%: price/CF = [108.81, 109.91, 111.14, 111.99]  CTD = bond 0
yield 6.0%: price/CF = [100.0, 100.0, 100.0, 100.0]  CTD = bond 0
yield 7.5%: price/CF = [92.01, 91.14, 90.17, 89.53]  CTD = bond 3
fair futures price 108.8144
bond 0: gross basis  -0.22  net basis   0.00 (32nds)  implied repo 4.000%
bond 1: gross basis  31.37  net basis  29.23 (32nds)  implied repo 0.287%
bond 2: gross basis  64.54  net basis  63.78 (32nds)  implied repo -4.261%
bond 3: gross basis  91.57  net basis  87.28 (32nds)  implied repo -6.807%
CTD DV01 $54.68/bp per $100k, future DV01 $61.64/bp
hedge a $25,000/bp swap book with 406 futures
```

The **basis trade** buys the CTD bond with repo financing and sells futures (or the reverse). It
earns the difference between the implied repo rate and the actual repo rate, and is exposed to the
CTD switching and to repo rates changing.

---

## 6. SOFR futures

SOFR (Secured Overnight Financing Rate) is the US overnight repo rate. A **3-month SOFR future**
settles on SOFR compounded over a 3-month period starting on an **IMM date** (the third Wednesday of
March, June, September or December).

- `price = 100 − rate`. A 1 bp rise in rates is a 0.01 fall in price.
- `DV01 per contract = $1,000,000 × 0.25 years × 0.0001 = $25`.
- **Strip**: consecutive contracts. **Packs** are groups of four: white (year 1), red (year 2), green (year 3). **Bundles** are all contracts out to a given year, traded as one.
- **Convexity adjustment**: `forward rate ≈ futures rate − ½ σ² T₁ T₂`, where `σ` is the normal volatility of the short rate and `T₁`, `T₂` are the start and end of the period. Futures settle daily and forwards do not, so futures rates sit above forward rates. The gap grows with the square of maturity.
- From the forwards, discount factors chain as `DF(T₂) = DF(T₁) / (1 + 0.25 × f)`, and the par swap rate is `(1 − DF_n) / Σ 0.25 × DFᵢ`. This is how the front of the swap curve is built from futures (see [rates section 3](../rates/README.md#3-building-a-curve)).

```python
import numpy as np

# Eight quarterly 3m SOFR futures (the first two years of the strip)
prices = np.array([96.10, 96.25, 96.40, 96.50, 96.55, 96.58, 96.60, 96.60])
start = 0.25 * np.arange(1, 9)           # each contract's period starts here (years)
end = start + 0.25

futures_rate = (100 - prices) / 100
sigma = 0.01                             # normal vol of the short rate: 100 bp per year
convexity = 0.5 * sigma**2 * start * end # Hull-White approximation
forward = futures_rate - convexity

print("futures rate %:", np.round(futures_rate * 100, 3))
print("convexity bp  :", np.round(convexity * 1e4, 2))
print(f"white pack (contracts 1-4) {prices[:4].mean():.4f}, red pack (5-8) {prices[4:].mean():.4f}")

# Discount factors and the 2-year quarterly par swap rate from the strip
# (assume the first 3 months are known at 4.00%)
df = np.cumprod(1 / (1 + 0.25 * np.r_[0.04, forward[:7]]))
par = (1 - df[-1]) / (0.25 * df.sum())
print(f"2y par swap rate {par:.4%}")

# Contract P&L: $25 per basis point per contract
qty, move_bp = -200, -3.5                # short 200 contracts, rates fall 3.5 bp (price rises)
pnl = qty * -move_bp * 25                # price change in bp = -rate change
print(f"P&L {pnl:+,.0f} USD")
```

Output:

```text
futures rate %: [3.9  3.75 3.6  3.5  3.45 3.42 3.4  3.4 ]
convexity bp  : [0.06 0.19 0.38 0.62 0.94 1.31 1.75 2.25]
white pack (contracts 1-4) 96.3125, red pack (5-8) 96.5825
2y par swap rate 3.6253%
P&L -17,500 USD
```

---

## 7. Options on futures: P&L explain and margin

Exchange-traded options on SOFR futures, Treasury futures, energy and equity index futures are a
large share of exchange trading. They are priced with Black's model (Black-Scholes applied to a futures price).

**P&L explain** (attribution): split the day's P&L into the risks that caused it, using the Greeks:

`P&L ≈ Δ·dF + ½ Γ·dF² + vega·dσ + θ·dt + unexplained`

- `Δ` (delta) = sensitivity to the futures price, `Γ` (gamma) = change in delta, vega = sensitivity to volatility, `θ` (theta) = time decay.
- **Unexplained** = actual repriced P&L minus the sum. It must be small. A large unexplained number means missing risks (cross terms such as vanna, the change in delta when vol moves), a bad mark, or a booking error. Middle office investigates it every day.

**Scenario margin** (as in SPAN, the exchange's Standard Portfolio Analysis of Risk): revalue the
portfolio over a grid of price moves (fractions of a "scan range") and vol up/down, and charge the
worst loss. Hedges offset, so a delta-hedged book needs far less margin than a naked short option.

```python
import math
from itertools import product

from scipy.stats import norm


def black76(F: float, K: float, vol: float, T: float) -> dict[str, float]:
    """Call on a future (zero rates for simplicity): price and Greeks."""
    d1 = (math.log(F / K) + 0.5 * vol**2 * T) / (vol * math.sqrt(T))
    d2 = d1 - vol * math.sqrt(T)
    return {
        "price": F * norm.cdf(d1) - K * norm.cdf(d2),
        "delta": norm.cdf(d1),
        "gamma": norm.pdf(d1) / (F * vol * math.sqrt(T)),
        "vega": F * norm.pdf(d1) * math.sqrt(T),               # per 1.00 of vol
        "theta": -F * norm.pdf(d1) * vol / (2 * math.sqrt(T)),  # per year
    }


# Book: long 100 calls, delta-hedged with short futures; $1,000 per point per contract
n, mult = 100, 1000
F0, K, vol0, T0, dt = 100.0, 100.0, 0.20, 0.25, 1 / 252
g = black76(F0, K, vol0, T0)
hedge = -round(n * g["delta"])
print(f"short {-hedge} futures against {n} calls (delta {g['delta']:.3f})")

# Next day: future +2, vol +1 point
F1, vol1 = 102.0, 0.21
dF, dvol = F1 - F0, vol1 - vol0
explain = {
    "delta": (n * g["delta"] + hedge) * dF,
    "gamma": n * 0.5 * g["gamma"] * dF**2,
    "vega": n * g["vega"] * dvol,
    "theta": n * g["theta"] * dt,
}
actual = n * (black76(F1, K, vol1, T0 - dt)["price"] - g["price"]) + hedge * dF
for k, v in explain.items():
    print(f"{k:12s} {v * mult:+10,.0f}")
print(f"{'unexplained':12s} {(actual - sum(explain.values())) * mult:+10,.0f}")
print(f"{'actual':12s} {actual * mult:+10,.0f}")


# Scenario ("SPAN-style") margin: worst loss over a grid of price and vol moves
def scenario_margin(calls: int, futures: int, scan: float = 6.0, vol_scan: float = 0.04) -> float:
    base = calls * black76(F0, K, vol0, T0)["price"]
    worst = 0.0
    for frac, dv in product((-1, -2 / 3, -1 / 3, 0, 1 / 3, 2 / 3, 1), (-vol_scan, vol_scan)):
        Fs = F0 + frac * scan
        pnl = calls * black76(Fs, K, vol0 + dv, T0)["price"] - base + futures * (Fs - F0)
        worst = min(worst, pnl)
    return -worst * mult


print(f"margin: short 100 calls {scenario_margin(-100, 0):,.0f}, "
      f"hedged short calls {scenario_margin(-100, -hedge):,.0f}, "
      f"our book {scenario_margin(100, hedge):,.0f}")
```

Output:

```text
short 52 futures against 100 calls (delta 0.520)
delta               -12
gamma            +7,969
vega            +19,922
theta            -3,162
unexplained        -424
actual          +24,293
margin: short 100 calls 450,914, hedged short calls 138,914, our book 79,707
```

Read the output as: the gamma and vega gains outweigh one day of theta; the unexplained
residual is about 2% of the day's P&L, mostly the vanna cross term and higher-order terms.

---

## 8. Other asset classes in brief

| Asset | Key relationship | What to know |
|---|---|---|
| **Equity index futures** | `F = S · e^((r − q)T)`, with `S` spot, `r` financing rate, `q` dividend yield | Rich futures imply a high financing rate. Quarterly roll; index rebalances. |
| **Energy** (crude, natural gas, power) | Curve shape: **contango** (deferred contracts dearer, storage costs) or **backwardation** (front dearer, scarce supply) | Roll yield, physical delivery and storage, crack spreads (crude vs refined products), weather. |
| **Agriculture, metals** | Same carry logic: `F = S · e^((r + storage − convenience yield)T)` | Seasonality, delivery locations and grades. |
| **FX** | Covered interest parity: `F = S · e^((r_domestic − r_foreign)T)` | The cross-currency basis is the deviation from parity. |
| **Crypto** | Dated futures trade at a basis to spot; **perpetual futures** never expire and use a **funding rate** paid between longs and shorts to keep them near spot | Trades all day every day, sits across many venues, and needs separate custody (holding the coins safely), and its funding rate and basis can be large. |

```python
import math

# Equity index future: F = S * exp((r - q) * T)
S, r, q, T = 5000.0, 0.043, 0.014, 0.25
fair = S * math.exp((r - q) * T)
market = 5045.0
implied_r = math.log(market / S) / T + q          # financing rate the market price implies
print(f"fair {fair:.2f}, market {market:.2f}, implied financing {implied_r:.2%}")

# Crypto: dated-future basis and perpetual funding, both as annual rates
spot, fut, days = 60_000.0, 61_500.0, 90
print(f"annualised basis {(fut / spot - 1) * 365 / days:.2%}")
funding_8h = 0.0001                               # 0.01% paid every 8 hours by longs to shorts
print(f"annualised funding {funding_8h * 3 * 365:.2%}")

# Energy: curve shape and the roll yield of holding the front month
curve = [78.00, 77.20, 76.50, 75.90]              # monthly crude futures, $/barrel
shape = "backwardation" if curve[0] > curve[1] else "contango"
roll = (curve[0] - curve[1]) / curve[1] * 12      # earned monthly as the next contract rolls up
print(f"{shape}, roll yield {roll:.2%} a year if the curve stays put")
```

Output:

```text
fair 5036.38, market 5045.00, implied financing 4.98%
annualised basis 10.14%
annualised funding 10.95%
backwardation, roll yield 12.44% a year if the curve stays put
```

---

## 9. The market calendar

| Event | Why it matters |
|---|---|
| **FOMC** (Federal Reserve rate decisions, 8 a year) | Moves the whole SOFR strip; option vols spike before and fall after |
| **CPI** (inflation) and **payrolls** (employment report, first Friday) | The biggest scheduled rates moves |
| **Treasury auctions** and the quarterly refunding | Supply concessions, then a squeeze (a shortage that drives the price up) in the newly issued bond |
| **Quarterly futures roll** (Treasury: late Feb, May, Aug, Nov; SOFR at IMM dates) | Volume moves to the next contract; calendar spreads, CTD and repo matter |
| **Month-end and quarter-end** | Index extension buying, balance-sheet constraints, repo spikes |
| **Holidays** | Different calendars per exchange and currency; wrong calendars give wrong accruals and fixings |

---

## 10. What an analytics team builds

- **Position service**: real-time positions from fills, start-of-day positions from clearing, and per-account and per-strategy views.
- **P&L engine**: realised and unrealised P&L, fees and financing; intraday (at live prices) and end of day (at settlement prices); daily, month-to-date and year-to-date.
- **P&L explain**: Greeks-based and full revaluation; unexplained P&L flagged above a set level.
- **Risk**: DV01 and bucketed DV01, Greeks, scenario and stress tests, margin estimates, limit monitoring with alerts.
- **Reference data**: contract specifications, expiry and roll calendars, conversion factors, holiday calendars, day counts. Small errors here cause large P&L errors.
- **Reconciliation**: trades and positions against drop copies and clearing statements, with breaks routed to owners.
- **Market data**: settlement prices, curves, vol surfaces, all stored with time stamps so any past day can be rerun.

Good analytics give one number per question, can be rebuilt for any past date, and can explain every change from yesterday.

---

## 11. Interview questions

**Q1. What is the tick value of a 10-year note future, and the P&L of 50 contracts moving 8 ticks?**
- Formula: `tick value = multiplier × tick`; `P&L = ticks × tick value × contracts`.
- Numbers: `1000 × 1/64 = $15.625`; `8 × 15.625 × 50 = $6,250`.

**Q2. Why can FIFO and average-cost P&L differ?**
- Formula: `total = realised + unrealised` is the same; only the split moves.
- Numbers: section 4: FIFO 220 + 90, average cost 200 + 110, both 310.
- Why: the methods assign different entry prices to the units still held.

**Q3. Which bond is cheapest to deliver when yields rise well above 6%?**
- Formula: CTD = lowest `price / CF` (ignoring carry).
- Numbers: section 5: at 3% the 6½-year bond is cheapest; at 7.5% the 9½-year bond is.
- Why: conversion factors assume a 6% yield. Above it, long-duration bonds are cheaper than their factor implies.

**Q4. How many 10-year note futures hedge a swap book with $25,000 DV01?**
- Formula: `N = DV01_book / (DV01_CTD / CF)`.
- Numbers: `DV01_CTD = $54.68` per $100k, `CF = 0.887`, so `61.64` per future; `25,000 / 61.64 ≈ 406`.
- Why: the future tracks the CTD, scaled by its conversion factor.

**Q5. What does an implied repo rate above the market repo rate tell you?**
- Formula: `IRR = (F × CF + AI_delivery − P) / P × 360 / days`.
- Why: buying the bond with repo and delivering it earns more than its financing cost, so the future is rich relative to cash. Sell futures, buy bonds (the basis trade).

**Q6. Why is a SOFR future's rate above the forward rate for the same period?**
- Formula: `forward ≈ futures − ½ σ² T₁ T₂`.
- Numbers: `σ = 1%`, `T₁ = 2`, `T₂ = 2.25`: `0.5 × 0.0001 × 4.5 = 2.25 bp`.
- Why: daily margin lets a short futures holder reinvest gains when rates rise and finance losses when rates fall, which is worth something to them; the futures rate rises to compensate.

**Q7. The P&L explain shows a large unexplained number. What do you check?**
- First check the data: missing or late trades, wrong settlement prices or vols, a wrong contract multiplier, an expiry that wasn't processed.
- Then the model: missing cross terms (vanna, the change in delta when volatility moves), large moves where second-order terms aren't enough, and curve or vol surface changes the Greeks don't capture.

**Q8. Internal position says −400 SOFR contracts, the clearing statement says −350. Next step?**
- List the trades on both sides for that contract, compare with the exchange drop copy, and find the 50-lot (a missed fill, a give-up the clearer rejected, a trade booked to the wrong account). Hold the position at the clearer's number until the cause is confirmed.

**Q9. A crypto perpetual pays 0.01% funding every 8 hours. What is that per year, and who pays?**
- Formula: `annual ≈ rate × 3 × 365`.
- Numbers: `0.0001 × 1,095 = 10.95%`. Longs pay shorts when the perpetual trades above spot.

**Q10. Why does a delta-hedged long option book still need margin?**
- Margin is the worst loss over a grid of scenarios. A long option hedged for delta still loses when vol falls and time passes. Section 7: $79,707 for the hedged long book, against $450,914 for 100 naked short calls.

---

## 12. Glossary

| Term | Meaning |
|---|---|
| Accrued interest (AI) | Coupon earned since the last payment, paid by a bond buyer to the seller |
| Backwardation | Futures curve where nearer contracts are dearer than later ones |
| Basis (Treasury) | Bond price minus futures price × conversion factor |
| Basis trade | Buying the cheapest-to-deliver bond with repo and selling futures (or the reverse) |
| Break | A mismatch between two records of the same trade or position |
| Bundle | All quarterly SOFR futures out to a given year, traded as one |
| Carry | Income from holding a position (coupon) minus its financing cost |
| Clearing house (CCP) | Central counterparty that stands between buyer and seller and collects margin |
| Contango | Futures curve where later contracts are dearer than nearer ones |
| Conversion factor (CF) | Scaling that makes bonds in a futures basket comparable; ≈ price at a 6% yield |
| Convexity adjustment | Gap between futures and forward rates caused by daily margining |
| Cheapest to deliver (CTD) | The basket bond the futures seller will choose to deliver |
| Delivery options | The futures seller's choices of bond, delivery day and timing |
| Drop copy | Independent copy of fills sent by the exchange or broker, used for reconciliation |
| FCM | Futures commission merchant: the clearing broker that faces the clearing house for you |
| FIFO | First in, first out: closing the oldest open lots first |
| Funding rate | Periodic payment between longs and shorts in a perpetual future |
| Give-up | Passing a trade from the executing broker to the clearing broker |
| IMM dates | Third Wednesday of March, June, September and December |
| Implied repo rate (IRR) | Financing rate at which buying a bond and delivering it into the future breaks even |
| Initial margin | Deposit required by the clearing house to cover a bad day's loss |
| Independent price verification (IPV) | Checking traders' marks against outside prices |
| Middle office | Team that owns the official positions, P&L and P&L explain |
| Net basis | Gross basis minus carry; the value of the delivery options |
| Pack | Four consecutive quarterly SOFR futures (white = year 1, red = year 2, ...) |
| P&L explain | Splitting P&L into the risks that produced it, plus an unexplained residual |
| Perpetual future | A crypto future with no expiry, kept near spot by a funding rate |
| Proprietary trading | Trading the firm's own capital, with no clients |
| Realised / unrealised P&L | Locked in by closing trades / on positions still open |
| Repo | Borrowing cash against a bond as collateral; the repo rate is the cost |
| Roll | Closing an expiring future and opening the next one |
| Settlement price | Official end-of-day futures price used for margin and P&L |
| SOFR | Secured Overnight Financing Rate: the US overnight repo benchmark |
| SPAN | The exchange's scenario-based method for setting initial margin |
| Tick / tick value | Smallest price move / its value in dollars for one contract |
| Variation margin | Daily cash payment of the change in a futures position's value |
