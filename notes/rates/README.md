# Interest Rates

Interest rate products, curves, risk and models, for quant researcher and quant developer
interviews on rates desks. Each term is explained the first time it appears; a glossary is at the
end. Formulas come first, then numbers.

Every code block runs on its own (`uv run python file.py`). The numbers in the comments come from
running it. Basics such as duration and convexity of a single bond are in the
[finance page](../finance/README.md#7-bonds-and-interest-rates-basics).

Contents:

1. [Building blocks](#1-building-blocks)
2. [Instruments](#2-instruments)
3. [Building a curve](#3-building-a-curve)
4. [Risk: DV01 and bucketed deltas](#4-risk-dv01-and-bucketed-deltas)
5. [P&L explain, carry and roll-down](#5-pl-explain-carry-and-roll-down)
6. [Curve trades and PCA](#6-curve-trades-and-pca)
7. [Options: swaptions, caps and SABR](#7-options-swaptions-caps-and-sabr)
8. [Term structure models](#8-term-structure-models)
9. [Electronic swaps market structure](#9-electronic-swaps-market-structure)
10. [Interview questions](#10-interview-questions)
11. [Glossary](#11-glossary)

---

## 1. Building blocks

| Term | Formula | Meaning |
|---|---|---|
| **Discount factor** `P(t)` | `P(t) = e^{-z(t) t}` | Today's value of $1 paid at time `t`. Everything else is built from it. |
| **Zero rate** `z(t)` | `z(t) = -ln P(t) / t` | The single rate that discounts a payment at `t`. |
| **Forward rate** `F(t₁, t₂)` | `F = (P(t₁) / P(t₂) - 1) / τ` | The rate for borrowing from `t₁` to `t₂`, locked in today. `τ = t₂ - t₁` as a year fraction. |
| **Instantaneous forward** `f(t)` | `f(t) = -∂ ln P(t) / ∂t` | The forward rate over a tiny period at `t`. Zero rate = average of forwards: `z(t) = (1/t) ∫₀ᵗ f(u) du`. |
| **Annuity** (PV01) | `A = Σ τᵢ P(tᵢ)` | Value of receiving 1 per year on a schedule of dates. Converts a rate difference into money. |
| **Par swap rate** | `S = (P(t₀) - P(tₙ)) / A` | The fixed rate that makes a swap worth zero today. |

**Compounding.** The same discount factor can be written with different conventions:
simple `1 / (1 + rτ)`, annual `(1 + r)^{-t}`, continuous `e^{-rt}`. Always say which one you use.

**Day count conventions** turn dates into the year fraction `τ`:

| Convention | Rule | Used for |
|---|---|---|
| ACT/360 | actual days / 360 | SOFR, USD money markets, USD swap legs |
| ACT/365F | actual days / 365 | GBP (SONIA) |
| 30/360 | every month counts as 30 days | USD corporate bonds, older USD swap fixed legs |
| ACT/ACT | actual days / actual days in the period | US Treasuries |

**Business day convention.** If a payment date falls on a holiday, **modified following** moves it to
the next business day, unless that crosses into the next month, in which case it moves back.
**Spot lag:** USD swaps start two business days after the trade date (T+2).

---

## 2. Instruments

| Instrument | What it is | Price or rate |
|---|---|---|
| **SOFR** | Secured Overnight Financing Rate: the USD overnight rate for loans backed by Treasuries. It replaced USD LIBOR in 2023. | Published daily by the New York Fed. |
| **Compounded SOFR** | How a floating period's rate is set: compound each day's SOFR over the period, known only at the end ("in arrears"). | `(Π (1 + rᵢ dᵢ / 360) - 1) × 360 / D`, `dᵢ` = days rate `rᵢ` applies, `D` = days in the period. |
| **SOFR future** | Exchange-traded contract on compounded SOFR over a 1- or 3-month period. | Price = `100 - rate`. |
| **FRA** | Forward rate agreement: fixes the rate on one future period. | Fair rate = the forward rate `F(t₁, t₂)`. |
| **Interest rate swap** | Exchange fixed payments for floating payments on a **notional** (the amount interest is calculated on; it is never exchanged). **Payer** = pay fixed, gains when rates rise. **Receiver** = receive fixed, gains when rates fall. | `PV_receiver = N × (K - S) × A`, `K` = fixed rate. |
| **OIS** | Overnight index swap: floating leg pays a compounded overnight rate (SOFR). In USD, all standard swaps are now SOFR OIS: annual fixed vs annual floating, both ACT/360. | Par swap rate `S`. |
| **Basis swap** | Floating vs floating (e.g. SOFR vs Fed Funds). | Quoted as a spread on one leg. |
| **Treasury note / bond** | Government bond, semi-annual coupons. | Price or yield. |
| **Treasury future** | Exchange-traded future on a basket of Treasuries; the seller delivers the **cheapest-to-deliver** bond. The main hedge on many swap desks. | Price; risk via the cheapest-to-deliver bond. |
| **Swap spread** | Swap rate minus Treasury yield of the same maturity. Now often negative at long maturities, because dealers' balance sheet costs make holding Treasuries expensive. | In basis points. |
| **Swaption** | Option to enter a swap at a fixed strike. "1y × 5y" = expires in 1 year into a 5-year swap. | Usually quoted in normal volatility. |
| **Cap / floor** | A series of options (caplets) on each floating fixing. Pays when the rate is above (cap) or below (floor) the strike. | Sum of caplet prices. |

**Why a floating leg is easy to value.** A floating leg that pays the forward rate on each period,
plus notional at the end, is worth exactly par today. So without the notional:
`PV_floating = P(t₀) - P(tₙ)`. This is why the par swap rate formula above has no forecasts in it.

---

## 3. Building a curve

**Goal:** find discount factors `P(t)` so that every quoted market instrument reprices exactly.

**Bootstrapping:** solve for one discount factor at a time, from shortest to longest maturity, each
using the ones already found. For annual swaps with par rate `Sₙ`:

`Sₙ × Σᵢ₌₁ⁿ P(i) = 1 - P(n)`  ⟹  `P(n) = (1 - Sₙ × Σᵢ₌₁ⁿ⁻¹ P(i)) / (1 + Sₙ)`

```python
import numpy as np

# Annual par swap rates (decimal) quoted at these tenors, in years
tenors = np.array([1, 2, 3, 5, 7, 10])
quotes = np.array([0.0430, 0.0405, 0.0390, 0.0380, 0.0382, 0.0390])


def bootstrap(quotes: np.ndarray) -> np.ndarray:
    """Discount factors for years 1..10 from annual-pay par swap rates."""
    years = np.arange(1, 11)
    par = np.interp(years, tenors, quotes)        # fill missing tenors (simple choice)
    df = np.empty(len(years))
    for n in range(len(years)):
        annuity_so_far = df[:n].sum()             # year fractions are all 1 here
        df[n] = (1 - par[n] * annuity_so_far) / (1 + par[n])
    return df


df = bootstrap(quotes)
years = np.arange(1, 11)
zero = -np.log(df) / years                        # continuously compounded zero rates
fwd = df[:-1] / df[1:] - 1                        # 1-year forward rates, annual compounding
print("discount factors", df.round(5))      # 0.95877 0.92376 0.8918 ... 0.68157
print("zero rates %    ", (100 * zero).round(3))  # 4.21 3.965 3.817 3.768 ... 3.834
print("1y forwards %   ", (100 * np.r_[1 / df[0] - 1, fwd]).round(3))
# 4.3 3.791 3.583 3.689 3.581 3.866 3.888 4.064 4.128 4.193  (zig-zag: see below)

# Check: each quoted swap reprices to par, i.e. S_n * sum(DF_1..n) = 1 - DF_n
for t, s in zip(tenors, quotes, strict=True):
    assert abs(s * df[:t].sum() - (1 - df[t - 1])) < 1e-12
print("all quoted swaps reprice exactly")
```

**What real curve building adds:**
- **Instruments by maturity:** overnight SOFR and SOFR futures for the first 1–2 years (adjusted for
  convexity, see Q6), then SOFR swaps out to 50 years.
- **Interpolation** between known points. Common choices: linear in log discount factor (gives flat
  forwards between points), or monotone convex (smooth, positive forwards). The example above
  interpolates par rates linearly, which is why its forward rates zig-zag: interpolation choice
  drives forward rates and hedges.
- **Fed meeting dates:** the overnight rate only moves at central bank meetings, so the front of the
  curve is built as steps between meeting dates.
- **Turn of year:** rates jump over the year-end because banks shrink balance sheets; add a spike.
- **Multi-curve:** one curve to discount (the collateral rate, SOFR for USD cleared swaps) and
  separate curves to project other floating rates. Before 2008 one curve did both.
- **Global solver:** with non-local interpolation, fit all instruments together with Newton's method
  (see [numerical methods](../numerical-methods/README.md)) instead of one at a time.

---

## 4. Risk: DV01 and bucketed deltas

| Term | Formula | Meaning |
|---|---|---|
| **DV01** | `DV01 = -∂PV / ∂r × 0.0001` | Change in value for a 1 basis point (0.01%) move in rates. Sign conventions vary; say yours. |
| **DV01 of a swap** | `DV01 ≈ N × A × 0.0001` | A $100m 10-year swap with annuity 8.2 has DV01 ≈ $82,000. |
| **Bucketed delta** (key-rate risk) | bump one input quote by 1 bp, rebuild the curve, reprice | Shows *where* on the curve the risk sits. The buckets add up to the parallel DV01. |
| **Par vs zero risk** | | **Par risk** = sensitivity to the quoted instruments (what traders can hedge with). **Zero risk** = sensitivity to zero rates. Converted with the Jacobian. |
| **Jacobian** | `J = ∂(zero rates) / ∂(quotes)` | Matrix linking the two risk views: `par risk = Jᵀ × zero risk`. |
| **Gamma** (convexity) | `∂² PV / ∂r²` | How DV01 itself changes as rates move. |

```python
import numpy as np

tenors = np.array([1, 2, 3, 5, 7, 10])
quotes = np.array([0.0430, 0.0405, 0.0390, 0.0380, 0.0382, 0.0390])


def bootstrap(quotes: np.ndarray) -> np.ndarray:
    years = np.arange(1, 11)
    par = np.interp(years, tenors, quotes)
    df = np.empty(len(years))
    for n in range(len(years)):
        df[n] = (1 - par[n] * df[:n].sum()) / (1 + par[n])
    return df


def receiver_pv(df: np.ndarray, fixed: float, years: int, notional: float) -> float:
    """Receive fixed, pay floating. Floating leg of a par swap is worth 1 - DF_n."""
    annuity = df[:years].sum()
    return notional * (fixed * annuity - (1 - df[years - 1]))


notional, fixed, n = 100e6, 0.0400, 7             # receive 4.00% on $100m for 7 years
df = bootstrap(quotes)
pv = receiver_pv(df, fixed, n, notional)
par_rate = (1 - df[n - 1]) / df[:n].sum()
annuity = df[:n].sum()
print(f"7y par rate {par_rate:.4%}, PV ${pv:,.0f}")    # 3.8200%, $1,086,065
print(f"PV check: (fixed - par) x annuity x notional = ${(fixed - par_rate) * annuity * notional:,.0f}")  # $1,086,065

bp = 1e-4
buckets = []
for i in range(len(quotes)):                       # bump one quote at a time, rebuild, reprice
    bumped = quotes.copy()
    bumped[i] += bp
    buckets.append(receiver_pv(bootstrap(bumped), fixed, n, notional) - pv)
parallel = receiver_pv(bootstrap(quotes + bp), fixed, n, notional) - pv
print("bucket deltas $ per bp:", dict(zip(tenors.tolist(), np.round(buckets).tolist(), strict=True)))
# {1: -13.0, 2: -27.0, 3: -70.0, 5: -144.0, 7: -60477.0, 10: 0.0}
print(f"sum of buckets {sum(buckets):,.0f}, parallel bump {parallel:,.0f}, "
      f"annuity x notional x 1bp {annuity * notional * bp:,.0f}")
# sum of buckets -60,731, parallel bump -60,717, annuity x notional x 1bp 60,337
```

**Reading the output.** Almost all the risk sits in the 7-year bucket because the swap matches a quoted
instrument exactly. A swap whose maturity falls between quotes (for example 6 years) spreads its
risk over the neighbouring buckets, as decided by the interpolation. The DV01 is about annuity ×
notional × 1 bp, plus a small correction because the swap is not at par.

**Hedging:** a desk hedges the bucketed deltas with the most liquid instruments (2, 5, 10, 30-year
swaps or Treasury futures). Hedge ratio = `DV01_position / DV01_hedge`. Whatever is left over is
**curve risk** between the hedge points.

---

## 5. P&L explain, carry and roll-down

**P&L explain** (P&L attribution) splits the day's profit into causes. A large unexplained part means
a model or data problem.

`P&L ≈ Σₖ Δₖ × Δrₖ  +  ½ Σₖ Γₖ × Δrₖ²  +  Θ × Δt  +  new trades  +  unexplained`

- `Δₖ` = bucketed delta for bucket `k`, `Δrₖ` = change in that quote in basis points.
- `Γₖ` = gamma; `Θ` = theta, the change from time passing with an unchanged curve.
- **Theta** splits into **carry** and **roll-down**.

| Term | Formula | Meaning |
|---|---|---|
| **Carry** | `(fixed rate - floating rate) × N × time` | Income from holding the position if nothing moves. A 7-year receiver at 3.82% funded at a 4.30% floating rate carries `-48 bp` a year. |
| **Roll-down** | `(S_n - S_{n-Δt}) × DV01` | Gain as the swap ages and is valued at a shorter, different rate. With `S₇ = 3.82%` and `S₆ = 3.81%`, the receiver gains about 1 bp × DV01 over the year. |
| **Breakeven** | `carry + roll-down` in basis points | How far rates can move against you before the position loses money. |

**Why it matters:** with an inverted front end (short rates above long rates), receivers have
negative carry. Interviewers expect you to compute carry and roll-down before calling a trade
attractive.

---

## 6. Curve trades and PCA

| Trade | Construction | Bet |
|---|---|---|
| **Outright** | receive (or pay) one maturity | rates fall (or rise) |
| **Steepener** | receive short maturity, pay long maturity, **DV01-neutral** | long rates rise relative to short ones |
| **Flattener** | the reverse | the curve flattens |
| **Butterfly** | receive the middle, pay both wings (e.g. 2s5s10s) | the middle is cheap relative to the wings |
| **Swap spread** | swap vs Treasury of the same maturity | swap spread widens or narrows |
| **Invoice spread** | Treasury future vs a matching swap | the same, using futures |

**DV01-neutral sizing.** `N_short = N_long × DV01_long / DV01_short` (DV01 per unit notional).
Example: 2s10s steepener with $100m of 10-year (annuity 8.16) needs
`100m × 8.16 / 1.88 ≈ $434m` of 2-year (annuity 1.88).

**Principal component analysis (PCA)** of daily curve changes finds the main ways the curve moves:
1. **Level** (all rates up or down together): about 80–90% of the variance.
2. **Slope** (short and long move apart): about 5–15%.
3. **Curvature** (middle vs ends): a few percent.

Weighting a butterfly by PCA so it has zero exposure to level and slope leaves a pure bet on
curvature. Hedging only level and slope leaves the trade exposed to the rest.

---

## 7. Options: swaptions, caps and SABR

**Normal (Bachelier) model.** Rates can be near zero or negative, so rates options are quoted in
**normal volatility**: the standard deviation of the rate change in basis points per year.

Payer swaption, forward swap rate `F`, strike `K`, expiry `T`, annuity `A`:
`Payer = A × [(F - K) N(d) + σ_N √T N'(d)]`, `d = (F - K) / (σ_N √T)`.
At the money: `Payer = Receiver ≈ A × σ_N × √(T / 2π) ≈ 0.4 × A × σ_N × √T`.

```python
import numpy as np
from scipy.stats import norm

# Discount factors for years 1..10 (from the bootstrap above)
df = np.array([0.95877, 0.92376, 0.89180, 0.86008, 0.83034,
               0.79943, 0.76951, 0.73946, 0.71015, 0.68157])

# 1y x 5y payer swaption: right to pay fixed on a 5-year swap starting in 1 year
expiry, length = 1, 5
annuity = df[expiry:expiry + length].sum()                    # DF_2 + ... + DF_6
forward = (df[expiry - 1] - df[expiry + length - 1]) / annuity
strike, normal_vol, notional = forward, 0.0100, 100e6         # at the money, 100 bp a year


def bachelier_payer(F: float, K: float, sigma: float, T: float, A: float) -> float:
    d = (F - K) / (sigma * np.sqrt(T))
    return A * ((F - K) * norm.cdf(d) + sigma * np.sqrt(T) * norm.pdf(d))


price = notional * bachelier_payer(forward, strike, normal_vol, expiry, annuity)
rule = notional * annuity * normal_vol * np.sqrt(expiry / (2 * np.pi))
print(f"forward swap rate {forward:.4%}, annuity {annuity:.4f}")   # 3.7009%, 4.3054
print(f"swaption price ${price:,.0f}; ATM rule A*sigma*sqrt(T/2pi) ${rule:,.0f}")  # both $1,717,610

rng = np.random.default_rng(0)                                # Monte Carlo check
F_T = forward + normal_vol * np.sqrt(expiry) * rng.standard_normal(1_000_000)
mc = notional * annuity * np.maximum(F_T - strike, 0).mean()
print(f"Monte Carlo ${mc:,.0f}")                                # $1,720,908
```

**Why the annuity appears.** Price the swaption with the annuity as the unit of account (the
**annuity measure**). The forward swap rate then has no drift, so the payoff is a simple call on a
normally distributed `F`, scaled by `A`. Caplets use the same idea with a single discount factor
(the **T-forward measure**).

**Converting volatilities:** normal vol ≈ lognormal (Black) vol × `F`. For example 25% Black vol at
`F = 4%` ≈ 100 bp normal vol. Per day: `σ_daily ≈ σ_annual / √252`, so 100 bp a year ≈ 6.3 bp a day.

**SABR** (stochastic alpha, beta, rho) models the **volatility smile** of each expiry:

`dF = α F^β dW`, `dα = ν α dZ`, `corr(dW, dZ) = ρ`.

| Parameter | Controls |
|---|---|
| `α` | the level of volatility (at the money vol ≈ `α / F^{1-β}`) |
| `β` | the "backbone": how the at-the-money vol moves when `F` moves. Often fixed (0 for normal, 0.5, or 1). |
| `ρ` | skew: correlation between rate and volatility |
| `ν` | vol of vol: curvature of the smile (how expensive far strikes are) |

Hagan's formula gives an implied volatility for each strike in closed form. Weaknesses: it can give
negative probability densities at low strikes. Fixes: shifted SABR (add a shift so `F + shift > 0`)
or arbitrage-free versions.

---

## 8. Term structure models

Used to price products whose value depends on the path of rates (Bermudan swaptions, callable
bonds) and to simulate future exposure.

| Model | Dynamics | Pros and cons |
|---|---|---|
| **Vasicek** | `dr = a (b - r) dt + σ dW` | Short rate `r` pulled towards `b` at speed `a`. Closed-form bond prices. Cannot match today's curve. |
| **Hull-White** (one factor) | `dr = (θ(t) - a r) dt + σ dW` | Vasicek with a time-varying target `θ(t)` chosen to fit today's curve exactly. Closed-form bonds and European swaptions; fast trees and PDE (partial differential equation) solvers for Bermudans. One factor means all rates move together: no decorrelation between maturities. |
| **HJM** | `df(t,T) = μ dt + σ(t,T) dW` | Heath-Jarrow-Morton: models the whole forward curve. No-arbitrage fixes the drift from the volatility: `μ = σ(t,T) ∫ₜᵀ σ(t,u) du`. A framework, not one model. |
| **LMM** (LIBOR market model, now forward market model) | each period's forward rate follows its own process, lognormal or SABR-like | Matches caps and swaptions directly; many factors give realistic decorrelation. Slow: needs Monte Carlo. |

**Mean reversion `a` in Hull-White** controls how much later forward rates move relative to early
ones. Higher `a` means less correlation between expiry dates, which makes Bermudan swaptions more
valuable. It is the key calibration choice for Bermudans.

**Calibration:** pick parameters so the model reprices liquid instruments, usually the swaptions
whose expiries and underlying swaps match the exotic trade. Use Levenberg–Marquardt
([numerical methods](../numerical-methods/README.md)).

```python
import numpy as np

# Vasicek: dr = a (b - r) dt + sigma dW   (Hull-White = same, with b(t) fitted to today's curve)
a, b, sigma, r0, T = 0.10, 0.04, 0.01, 0.043, 5.0

B = (1 - np.exp(-a * T)) / a
lnA = (B - T) * (a**2 * b - sigma**2 / 2) / a**2 - sigma**2 * B**2 / (4 * a)
closed_form = np.exp(lnA - B * r0)

rng = np.random.default_rng(0)
n_paths, n_steps = 200_000, 500
dt = T / n_steps
r = np.full(n_paths, r0)
integral = np.zeros(n_paths)
for _ in range(n_steps):
    r_next = r + a * (b - r) * dt + sigma * np.sqrt(dt) * rng.standard_normal(n_paths)
    integral += 0.5 * (r + r_next) * dt                      # trapezoid rule for the integral of r
    r = r_next
mc = np.exp(-integral).mean()
print(f"5y zero-coupon bond: closed form {closed_form:.5f}, Monte Carlo {mc:.5f}")  # 0.81030, 0.81023
print(f"5y zero rate {-np.log(closed_form) / T:.4%}")                       # 4.2070%
```

---

## 9. Electronic swaps market structure

| Term | Meaning |
|---|---|
| **Clearing** | A central counterparty (LCH, CME) stands between both sides, so neither carries the other's default risk. Standard USD swaps must be cleared. |
| **SEF** | Swap execution facility: a regulated electronic venue (Tradeweb, Bloomberg) where standard swaps must trade. |
| **D2C / D2D** | Dealer-to-client (clients ask dealers for prices) and dealer-to-dealer (dealers trade with each other, often on order books). |
| **RFQ** | Request for quote: a client asks several dealers (at least two or three on a SEF) for a price and trades on the best one. |
| **CLOB** | Central limit order book: anonymous continuous trading, like a stock exchange. |
| **Package** | Several legs traded as one, e.g. a spread or butterfly quoted as one number. |
| **Win rate / hit ratio** | Share of RFQs a dealer wins. Too high means the dealer is pricing too cheaply. |
| **Markout** | P&L of a trade measured a fixed time later (1 s, 1 min, 1 hour) against the mid. Persistent negative markouts mean the counterparty is better informed. |

**What an algorithmic swaps desk builds:** a real-time curve from futures and the latest trades, a
price for each RFQ (mid + spread for size, risk and client), automatic hedging with Treasury
futures, inventory limits, and post-trade analysis of markouts and win rates. The
[system design page](../system-design/README.md) has a worked design, and the
[market-making notes](../market-making/README.md) cover the quoting models.

---

## 10. Interview questions

Each answer gives the formula first, then the numbers, then why.

**Q1. What is the DV01 of a $100m 10-year at-the-money swap?**
- Formula: `DV01 ≈ N × A × 0.0001`, with `A = Σ P(tᵢ)` for annual payments.
- Numbers: annuity 8.16 from the curve above: `100m × 8.16 × 0.0001 ≈ $82,000` per bp.
- Why: a 1 bp change in the fixed rate changes every annual payment by `N × 0.0001`, and the
  annuity values that stream. Rule of thumb: DV01 per $1m ≈ maturity × $80–100 at 4% rates.

**Q2. Why is the floating leg of a swap worth par minus the final discount factor?**
- Formula: each period pays the forward rate: `τ F × P(tᵢ) = P(tᵢ₋₁) - P(tᵢ)`.
- Numbers: summing over all periods telescopes to `P(t₀) - P(tₙ)`.
- Why: you can replicate each floating payment by borrowing and lending at today's discount
  factors, so no rate forecasts are needed.

**Q3. You receive fixed on a 7-year swap at 3.82%; the floating rate is 4.30% and the 6-year rate
is 3.81%. Expected P&L over a year if the curve doesn't move?**
- Formula: `carry + roll-down = (K - floating) + (S₇ - S₆)` in basis points, then × DV01 for money.
- Numbers: `(3.82 - 4.30) + (3.82 - 3.81) = -48 + 1 = -47 bp` a year.
- Why: with an inverted front end, receiving fixed costs money while you wait.

**Q4. Size a DV01-neutral 2s10s steepener on $100m of 10-year.**
- Formula: `N₂ = N₁₀ × A₁₀ / A₂`.
- Numbers: `100m × 8.16 / 1.88 ≈ $434m` of 2-year.
- Why: equal DV01 means a parallel move makes nothing; only the slope matters.

**Q5. Price an at-the-money 1y × 5y payer swaption: annuity 4.3, normal vol 100 bp, $100m.**
- Formula: `≈ 0.4 × N × A × σ_N × √T`.
- Numbers: `0.4 × 100m × 4.3 × 0.01 × 1 ≈ $1.72m` (exact: $1,717,610).
- Why: at the money, the Bachelier price is `A σ √T / √(2π)`, and `1/√(2π) ≈ 0.4`.

**Q6. Why do SOFR futures rates sit above FRA rates for the same period?**
- Formula: `FRA rate ≈ futures rate - ½ σ² T₁ T₂` (Hull-White approximation; `T₁`, `T₂` = start
  and end of the period).
- Numbers: `σ = 1%`, `T₁ = 2`, `T₂ = 2.25`: `½ × 0.0001 × 2 × 2.25 = 2.25 bp`.
- Why: futures settle daily. When rates rise you receive margin and reinvest it at higher rates;
  when they fall you pay margin and fund it cheaply. That advantage is paid for with a higher rate.

**Q7. Is a receiver swap long or short convexity?**
- Formula: `PV_receiver = N (K - S) A(r)`, and `A` falls as rates rise.
- Why: when rates fall the annuity rises, so each basis point is worth more: gains grow faster than
  losses. The receiver is long convexity (small for swaps, large for long-dated bonds). A payer is
  short convexity.

**Q8. Convert 25% Black volatility to normal volatility at a 4% forward.**
- Formula: `σ_N ≈ σ_B × F`.
- Numbers: `0.25 × 4% = 1% = 100 bp` a year, ≈ `100 / √252 ≈ 6.3 bp` a day.
- Why: lognormal vol is a percentage of the rate; normal vol is in rate units.

**Q9. Why does Hull-White mean reversion matter for a Bermudan swaption?**
- Formula: in Hull-White the volatility of the rate at time `t` decays as `e^{-a(T - t)}`.
- Why: higher `a` lowers the correlation between rates at different exercise dates, which raises
  the value of being able to choose when to exercise. Two models calibrated to the same European
  swaptions but with different `a` give different Bermudan prices.

**Q10. Your P&L explain shows a large unexplained amount. Where do you look?**
- Formula: `unexplained = actual P&L - (Δ × Δr + ½ Γ Δr² + Θ Δt + new trades)`.
- Check, in order: missed or late-booked trades; stale or wrong market data (a bad quote); a curve
  that failed to build or changed interpolation; fixings and cash flows on the day; big moves where
  second-order terms are not enough; model or calibration changes.

---

## 11. Glossary

| Term | Plain meaning |
|---|---|
| Annuity (PV01) | Value of 1 paid per year over the swap's dates |
| Basis point (bp) | 0.01% |
| Bermudan swaption | A swaption that can be exercised on several dates |
| Bootstrapping | Building a curve one maturity at a time from market quotes |
| Bucketed delta | Sensitivity to one curve input at a time |
| Carry | Income from holding a position if nothing moves |
| Cheapest to deliver | The bond a futures seller will choose to deliver |
| Clearing | A central counterparty sits between buyer and seller |
| CLOB | Central limit order book |
| Convexity adjustment | Correction between futures and forward rates due to daily margining |
| Day count | Rule for turning dates into a year fraction |
| Discount factor | Today's value of $1 paid in the future |
| DV01 | Value change for a 1 bp rate move |
| FRA | Forward rate agreement |
| Forward rate | Rate for a future period, locked in today |
| HJM | Heath-Jarrow-Morton framework for modelling the whole forward curve |
| Hull-White | Short-rate model with mean reversion, fitted to today's curve |
| Jacobian | Matrix of how zero rates change with each quoted instrument |
| LMM | Market model of forward rates for each period |
| Markout | Trade P&L measured a fixed time after the trade |
| Mean reversion | Tendency of rates to be pulled back towards a level |
| Normal volatility | Standard deviation of rate changes in basis points |
| Notional | Amount interest is calculated on; not exchanged in a swap |
| OIS | Overnight index swap |
| Par swap rate | Fixed rate that makes a swap worth zero |
| Payer / receiver | Pays / receives the fixed rate |
| PCA | Principal component analysis: the main independent ways the curve moves |
| RFQ | Request for quote |
| Roll-down | Gain from a position ageing along an unchanged curve |
| SABR | Volatility smile model with parameters α, β, ρ, ν |
| SEF | Swap execution facility |
| SOFR | Secured Overnight Financing Rate, the USD benchmark |
| Spot lag | Days between trade date and start date |
| Swap spread | Swap rate minus Treasury yield |
| Swaption | Option to enter a swap |
| Theta | Value change from time passing |
| Zero rate | Single rate discounting one payment |
