# Finance

Core finance concepts that come up in quant researcher and quant developer interviews. Each term is
explained once, in plain words, the first time it appears. A glossary at the end lists them all.

Every code block runs on its own: copy it into a file and run `uv run python file.py`. The numbers
in the comments come from running the code.

Contents:

1. [Returns](#1-returns)
2. [Performance metrics: Sharpe ratio and friends](#2-performance-metrics-sharpe-ratio-and-friends)
3. [Why a Sharpe ratio can lie](#3-why-a-sharpe-ratio-can-lie)
4. [Risk measures](#4-risk-measures)
5. [Portfolio theory](#5-portfolio-theory)
6. [Options](#6-options)
7. [Bonds and interest rates basics](#7-bonds-and-interest-rates-basics)
8. [Trading costs](#8-trading-costs)
9. [Interview questions](#9-interview-questions)
10. [Glossary](#10-glossary)

---

## 1. Returns

| Term | Formula | Meaning |
|---|---|---|
| **Simple return** | `R = P_t / P_{t-1} - 1` | Percentage change in price. Adds up **across assets**: portfolio return = Σ weight × asset return. |
| **Log return** | `r = ln(P_t / P_{t-1})` | Adds up **across time**: the 1-year log return is the sum of the daily log returns. `r ≈ R` when returns are small. |
| **Excess return** | `R - r_f` | Return above the **risk-free rate** `r_f` (what you earn on cash or short government bills with no risk). |
| **Annualised return** | `mean daily × 252` | 252 is the usual number of trading days in a year. Use 12 for monthly, 52 for weekly. |
| **Annualised volatility** | `std daily × √252` | **Volatility** = standard deviation of returns. It scales with the square root of time because variances of independent returns add. |
| **CAGR** | `(final / initial)^(1/years) - 1` | Compound annual growth rate: the constant yearly return that turns the starting value into the final value. |

**Volatility drag.** The compound (geometric) growth rate is lower than the average (arithmetic)
return: `g ≈ μ - σ² / 2`. Example: +50% then −50% averages 0% but leaves you with 75% of your money.
Higher volatility means a bigger gap, which is why leverage can make a profitable strategy lose
money over time.

---

## 2. Performance metrics: Sharpe ratio and friends

| Metric | Formula (annualised) | What it tells you |
|---|---|---|
| **Sharpe ratio** | `(mean excess return) / (volatility)` | Return earned per unit of total risk. Roughly: below 0.5 weak, 1 good, above 2 very good (and worth checking for mistakes). |
| **Sortino ratio** | `mean excess return / downside deviation` | Like Sharpe, but only counts the bad days as risk. **Downside deviation** = `√mean(min(r, 0)²)`. |
| **Maximum drawdown** | `min over t of (wealth_t / running peak_t - 1)` | **Drawdown** = how far you are below the previous high. Maximum drawdown is the worst peak-to-trough fall. |
| **Calmar ratio** | `CAGR / |maximum drawdown|` | Growth per unit of worst loss. Popular with managed-futures funds. |
| **Beta (β)** | `cov(strategy, market) / var(market)` | How much the strategy moves when the market moves 1%. |
| **Alpha (α)** | `mean(strategy) - β × mean(market)` | Return **not** explained by market exposure: the part attributed to skill. |
| **Tracking error** | `std(strategy - benchmark)` | How far the strategy strays from its **benchmark** (the index it is measured against). |
| **Information ratio** | `mean(strategy - benchmark) / tracking error` | A Sharpe ratio for the return above the benchmark. |
| **Hit rate** | `fraction of trades or days with profit` | Meaningless alone: a 30% hit rate is fine if winners are much bigger than losers. |
| **Turnover** | `Σ |weight change| per year` | How much of the portfolio is traded. High turnover means high trading costs. |

```python
import numpy as np

rng = np.random.default_rng(0)
r = rng.normal(0.0005, 0.01, 2520)        # 10 years of daily excess returns
mkt = rng.normal(0.0004, 0.012, 2520)     # daily market returns
strat = 0.0001 + 1.2 * mkt + rng.normal(0, 0.008, 2520)

mu, sd = r.mean(), r.std(ddof=1)
sharpe = mu / sd * np.sqrt(252)
downside = np.sqrt(np.mean(np.minimum(r, 0) ** 2))
sortino = mu / downside * np.sqrt(252)

wealth = np.cumprod(1 + r)
drawdown = wealth / np.maximum.accumulate(wealth) - 1
max_dd = drawdown.min()
cagr = wealth[-1] ** (252 / len(r)) - 1
calmar = cagr / -max_dd

beta = np.cov(strat, mkt, ddof=1)[0, 1] / np.var(mkt, ddof=1)
alpha = (strat.mean() - beta * mkt.mean()) * 252
active = strat - mkt
tracking_error = active.std(ddof=1) * np.sqrt(252)
info_ratio = active.mean() * 252 / tracking_error

print(f"Sharpe {sharpe:.2f}, Sortino {sortino:.2f}")          # Sharpe 0.31, Sortino 0.44
print(f"max drawdown {max_dd:.1%}, CAGR {cagr:.1%}, Calmar {calmar:.2f}")  # -31.3%, 3.7%, 0.12
print(f"beta {beta:.2f}, alpha {alpha:.1%}")                  # beta 1.21, alpha 2.0%
print(f"tracking error {tracking_error:.1%}, IR {info_ratio:.2f}")  # 13.4%, 0.42
```

**Notice:** the true Sharpe ratio of `r` is `0.0005 / 0.01 × √252 = 0.79`, but ten years of data
gave 0.31. That is the topic of the next section.

---

## 3. Why a Sharpe ratio can lie

1. **Estimation noise.** The standard error of an annualised Sharpe ratio `SR` measured over `T`
   years is about `√((1 + SR²/2) / T)`. With 10 years and SR ≈ 0.3 that is ±0.32, so the measured
   value is barely distinguishable from zero. Rule of thumb: you need about `(2 / SR)²` years to be
   95% sure a strategy has a positive Sharpe ratio (16 years for SR = 0.5, 4 years for SR = 1).
2. **The √252 rule assumes independent returns.** If daily returns are positively
   **autocorrelated** (today's return predicts tomorrow's in the same direction), as with illiquid
   assets or stale prices, √252 overstates the annual Sharpe ratio. Lo (2002) gives the correction.
3. **Fat tails and short volatility.** Selling options or insurance earns small steady gains and
   rare huge losses. The Sharpe ratio looks great until the crash. Check skewness, kurtosis and
   maximum drawdown alongside it.
4. **Multiple testing.** Try 100 random strategies and the best one will have a high Sharpe ratio
   by luck. The **deflated Sharpe ratio** (Bailey and López de Prado) adjusts for the number of
   strategies tried. Always ask "how many things did you test?"
5. **Look-ahead bias and survivorship bias.** **Look-ahead bias** = using data that was not yet
   available at decision time. **Survivorship bias** = testing only on companies that still exist
   today, which drops the ones that went bankrupt.
6. **Costs ignored.** A high-turnover strategy can have a gross Sharpe of 3 and a net Sharpe below
   zero. See [section 8](#8-trading-costs).

---

## 4. Risk measures

| Term | Meaning |
|---|---|
| **Value at Risk (VaR)** | The loss that is exceeded only with a small probability. "1-day 99% VaR = $1m" means on 99% of days you lose less than $1m. |
| **Expected Shortfall (ES)** | Also called Conditional VaR. The **average** loss on the days worse than VaR. Captures how bad the tail is, not just where it starts. Basel banking rules now use ES at 97.5%. |
| **Historical VaR** | Read VaR straight off the past returns (an empirical quantile). No distribution assumed. |
| **Parametric VaR** | Assume returns are normal: `VaR = z × σ - μ`, with `z = 2.33` at 99%. Underestimates fat tails. |
| **Stress test** | Revalue the portfolio under a specific bad scenario (2008, March 2020, rates +200 basis points). |
| **Correlation** | Moves between −1 and +1. Correlations tend to rise towards 1 in a crisis, exactly when diversification is needed. |

```python
import numpy as np

rng = np.random.default_rng(0)
r = rng.normal(0.0005, 0.01, 2520)

cutoff = np.quantile(r, 0.01)              # the 1% worst daily return
var_99 = -cutoff
es_99 = -r[r <= cutoff].mean()
var_normal = 2.326 * r.std(ddof=1) - r.mean()
print(f"historical VaR {var_99:.2%}, ES {es_99:.2%}, normal VaR {var_normal:.2%}")
# historical VaR 2.30%, ES 2.71%, normal VaR 2.30%  (they agree because the data is normal)
```

**Key properties.** VaR is not **subadditive**: the VaR of two books combined can be larger than the
sum of their VaRs, which punishes diversification. ES is subadditive, which is one reason
regulators moved to it. Neither can be summed across desks; you must recompute on the combined
portfolio.

---

## 5. Portfolio theory

**Portfolio return and risk** with weights `w`, expected returns `μ` and **covariance matrix** `Σ`
(the table of how every pair of assets moves together):

- expected return = `wᵀμ`
- variance = `wᵀΣw`

**Diversification.** `n` assets each with volatility `σ` and pairwise correlation `ρ`, equal weights:
portfolio variance = `σ² (ρ + (1 - ρ) / n)`. As `n` grows it falls to `ρσ²`, not to zero. The
common part cannot be diversified away.

| Term | Meaning |
|---|---|
| **Mean-variance optimisation** | Markowitz (1952): choose weights for the highest expected return at each level of variance. |
| **Efficient frontier** | The curve of those best portfolios. Anything below it is beaten by something on it. |
| **Minimum-variance portfolio** | `w ∝ Σ⁻¹ 1`. The lowest-risk portfolio; needs no return forecasts, which makes it robust. |
| **Tangency portfolio** | `w ∝ Σ⁻¹ (μ - r_f)`. The portfolio with the highest Sharpe ratio. |
| **Capital market line** | Mixing cash with the tangency portfolio. Every investor holds the same risky mix and only changes how much cash. |
| **CAPM** | Capital Asset Pricing Model: `E[R_i] - r_f = β_i (E[R_m] - r_f)`. Only market risk is rewarded; risk you can diversify away earns nothing. |
| **Factor model** | `R_i = α_i + Σ β_ik F_k + ε_i`. Returns are explained by a few common **factors** (market, size, value, momentum, quality). Fama-French is the classic. ε is the asset-specific part. |
| **Risk parity** | Weight assets so each contributes equal risk, instead of equal money. |
| **Kelly criterion** | The bet size that maximises long-run growth: leverage `f* = (μ - r_f) / σ²`. In practice traders use half-Kelly or less, because estimates of μ are noisy and full Kelly has deep drawdowns. |

```python
import numpy as np

mu = np.array([0.06, 0.08, 0.10])          # expected annual returns
vol = np.array([0.10, 0.15, 0.20])
corr = np.array([[1.0, 0.3, 0.2],
                 [0.3, 1.0, 0.5],
                 [0.2, 0.5, 1.0]])
cov = np.outer(vol, vol) * corr
rf = 0.03

w_minvar = np.linalg.solve(cov, np.ones(3))   # solve, don't invert the matrix
w_minvar /= w_minvar.sum()
w_tangency = np.linalg.solve(cov, mu - rf)
w_tangency /= w_tangency.sum()

for name, w in [("min variance", w_minvar), ("tangency", w_tangency)]:
    ret, risk = w @ mu, np.sqrt(w @ cov @ w)
    print(f"{name}: weights {w.round(3)}, return {ret:.2%}, vol {risk:.2%}, "
          f"Sharpe {(ret - rf) / risk:.3f}")
# min variance: weights [0.745 0.185 0.07 ], return 6.65%, vol 9.25%, Sharpe 0.395
# tangency: weights [0.486 0.244 0.27 ], return 7.57%, vol 10.35%, Sharpe 0.441
```

**In practice** the optimiser amplifies errors in `μ`: small changes in forecasts flip weights
wildly. Fixes: **shrinkage** of the covariance matrix (Ledoit-Wolf, pull it towards a simple
target), weight limits, Black-Litterman (blend your views with market-implied returns).

---

## 6. Options

| Term | Meaning |
|---|---|
| **Call / put** | The right, not the obligation, to buy (call) or sell (put) at the **strike** `K` on or before **expiry** `T`. Payoff: call `max(S - K, 0)`, put `max(K - S, 0)`. |
| **European / American** | European options can be exercised only at expiry; American at any time. |
| **In / at / out of the money** | Whether exercising now would pay (in), the strike equals the spot (at), or would not pay (out). |
| **Put-call parity** | `C - P = S - K e^{-rT}` for European options. Holds without any model; violating it is an **arbitrage** (riskless profit). |
| **Black-Scholes** | `C = S N(d1) - K e^{-rT} N(d2)`, with `d1 = [ln(S/K) + (r + σ²/2)T] / (σ√T)` and `d2 = d1 - σ√T`. `N` is the standard normal cumulative distribution. Assumes constant volatility and continuous trading. |
| **Implied volatility** | The σ that makes Black-Scholes match the market price. Markets quote options in implied volatility, not dollars. See [numerical methods](../numerical-methods/README.md) for how to solve for it. |
| **Smile / skew** | Implied volatility differs by strike. Equity puts with low strikes have higher implied volatility (crash fear), so the curve slopes down: the skew. |
| **Risk-neutral pricing** | Price = discounted expected payoff under a probability where every asset grows at `r`. Works because the option can be hedged, so risk preferences drop out. |

**The Greeks** measure how the option price changes:

| Greek | Definition | Call formula | Intuition |
|---|---|---|---|
| **Delta (Δ)** | ∂C/∂S | `N(d1)` | Shares to hold to hedge. About 0.5 at the money. |
| **Gamma (Γ)** | ∂²C/∂S² | `N'(d1) / (S σ √T)` | How fast delta changes. Largest at the money near expiry. |
| **Vega** | ∂C/∂σ | `S N'(d1) √T` | Gain per 1.00 (100 points) rise in volatility. Divide by 100 for per point. |
| **Theta (Θ)** | ∂C/∂t | `-S N'(d1) σ / (2√T) - r K e^{-rT} N(d2)` | Value lost per year as time passes. Usually negative for a long option. |
| **Rho (ρ)** | ∂C/∂r | `K T e^{-rT} N(d2)` | Sensitivity to interest rates. |

**Gamma and theta trade off.** A delta-hedged option's profit per small time step is about
`½ Γ S² (σ_realised² - σ_implied²) dt`. Buying an option is a bet that the market will move more
than implied volatility says; theta is the rent you pay for that bet.

**Quick mental price.** At the money with zero rates: `C ≈ 0.4 × S × σ × √T`. For S = 100, σ = 20%,
T = 1 that gives 8.0.

```python
import numpy as np
from scipy.stats import norm

S, K, T, r, sigma = 100.0, 100.0, 1.0, 0.03, 0.20

d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
d2 = d1 - sigma * np.sqrt(T)
call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
put = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

delta = norm.cdf(d1)
gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
vega = S * norm.pdf(d1) * np.sqrt(T)
theta = -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)

print(f"call {call:.4f}, put {put:.4f}")                         # call 9.4134, put 6.4580
print(f"parity error {call - put - (S - K * np.exp(-r * T)):.1e}")  # 0.0e+00
print(f"delta {delta:.4f}, gamma {gamma:.4f}, vega {vega:.2f}, theta {theta:.2f}")
# delta 0.5987, gamma 0.0193, vega 38.67, theta -5.38
```

The call is 9.41 rather than 8.0 because rates are 3%, which raises the forward price. The average
of call and put (7.94) is close to the zero-rate rule of thumb. The repo's tested version lives in
`src/quantprep/black_scholes.py`.

---

## 7. Bonds and interest rates basics

Full detail for the rates roles is in [notes/rates](../rates/README.md). The essentials:

| Term | Meaning |
|---|---|
| **Discount factor** `D(t)` | Today's value of $1 paid at time `t`. With a continuous rate: `e^{-rt}`. |
| **Yield to maturity** | The single rate that discounts all of a bond's cash flows back to its price. |
| **Basis point (bp)** | 0.01%. Rates moves are quoted in basis points. |
| **Macaulay duration** | Weighted average time of the cash flows, weighted by their present value. |
| **Modified duration** | `Macaulay / (1 + y)`. Percentage price change for a 1.00 change in yield: `ΔP/P ≈ -D_mod Δy`. |
| **DV01** | Dollar value of a basis point: price change when yields fall 1 bp. `DV01 = D_mod × P × 0.0001`. The main risk number on a rates desk. |
| **Convexity** | Curvature of price against yield. Adds `+½ × convexity × P × Δy²`, so long bonds lose less than duration predicts when yields rise and gain more when they fall. |
| **Forward rate** | The rate for borrowing between two future dates that is locked in today, implied by today's curve. |
| **Yield curve** | Yields plotted against maturity. Normally upward sloping; **inverted** when short rates are above long rates. |
| **Swap** | Exchange fixed-rate payments for floating-rate payments (in USD, floating = SOFR, the overnight secured rate). The **par swap rate** is the fixed rate that makes the swap worth zero today. |

```python
import numpy as np

coupon, y, years = 0.04, 0.05, 10            # 4% annual coupon, 5% yield, 10 years
t = np.arange(1, years + 1)
cash_flows = np.full(years, coupon * 100)
cash_flows[-1] += 100                         # principal repaid at the end


def price(yld: float) -> float:
    return float((cash_flows / (1 + yld) ** t).sum())


P = price(y)
macaulay = (t * cash_flows / (1 + y) ** t).sum() / P
modified = macaulay / (1 + y)
dv01 = (price(y - 1e-4) - price(y + 1e-4)) / 2
convexity = (price(y + 1e-4) + price(y - 1e-4) - 2 * P) / (P * 1e-8)

print(f"price {P:.2f}, Macaulay {macaulay:.2f}, modified {modified:.2f}")  # 92.28, 8.36, 7.96
print(f"DV01 {dv01:.4f}, convexity {convexity:.1f}")                       # 0.0735, 78.3

dy = 0.01                                     # yields up 100 bp
print(f"actual {price(y + dy) - P:.3f}")                                   # -6.998
print(f"duration only {-modified * P * dy:.3f}")                           # -7.347
print(f"duration + convexity {-modified * P * dy + 0.5 * convexity * P * dy**2:.3f}")  # -6.986
```

---

## 8. Trading costs

| Term | Meaning |
|---|---|
| **Bid / ask / spread** | Bid = best price someone will buy at; ask = best price someone will sell at. The **spread** is the gap. Crossing it costs half the spread versus the **mid** price. |
| **Slippage** | Difference between the price you expected and the price you got. |
| **Market impact** | Your own trading pushes the price against you. The **square-root law**: impact ≈ `c × σ_daily × √(order size / daily volume)`, with `c` around 1. Doubling size raises cost per share by √2, not 2. |
| **Implementation shortfall** | Total cost versus the price when you decided to trade: spread + impact + delay + missed fills. |
| **VWAP / TWAP** | Volume-weighted / time-weighted average price. Common execution benchmarks and algorithms that slice an order over the day. |
| **Capacity** | How much money a strategy can run before impact eats its edge. |

**Net Sharpe check:** annual cost ≈ turnover × cost per unit traded. A strategy with 20× annual
turnover and 5 bp cost per trade pays 1% a year, which can be most of its return.

---

## 9. Interview questions

**Q1. Daily Sharpe ratio is 0.1. What is the annual Sharpe ratio?**
`0.1 × √252 ≈ 1.59`, assuming daily returns are independent. Mention that autocorrelation breaks
this.

**Q2. A strategy has Sharpe 2 over 1 year. Is it good?**
Standard error is about `√((1 + 2) / 1) ≈ 1.7`, so the true value could easily be near zero. Ask
how many strategies were tried, whether costs are included, and look at drawdowns and skew.

**Q3. Two strategies, each with Sharpe 1, correlation 0. Sharpe of a 50/50 mix?**
Returns add, volatilities add in quadrature: Sharpe = `1 × √2 ≈ 1.41`. With `n` uncorrelated
equal-Sharpe strategies, Sharpe grows like `√n`. This is the reason multi-strategy funds exist.

**Q4. Why can a strategy with positive average return lose money over time?**
Volatility drag: geometric growth ≈ `μ - σ²/2`. With μ = 5% and σ = 40%, growth ≈ −3% a year.

**Q5. Why is Expected Shortfall preferred to VaR?**
It describes how bad the tail is (VaR only says where it starts), and it is subadditive, so it
never penalises diversification.

**Q6. Price an at-the-money 1-year call, S = 100, σ = 25%, zero rates, in your head.**
`0.4 × 100 × 0.25 × 1 = 10`.

**Q7. You are long a delta-hedged option. When do you make money?**
When realised volatility is above the implied volatility you paid. Gamma gains from moves, theta
loses with time.

**Q8. Why does the call price rise with volatility even though volatility is "risk"?**
The payoff is convex: the downside is capped at the premium while the upside is not, so more spread
in outcomes raises the expected payoff.

**Q9. A 10-year bond has modified duration 8 and price 100. Yields rise 25 bp. New price?**
`ΔP ≈ -8 × 100 × 0.0025 = -2`, so about 98, slightly higher once convexity is added.

**Q10. Why is the minimum-variance portfolio often used instead of the tangency portfolio?**
It needs no expected-return forecasts, which are the noisiest input. The tangency portfolio is very
sensitive to errors in them.

---

## 10. Glossary

| Term | Plain meaning |
|---|---|
| Alpha | Return not explained by exposure to the market or other factors |
| Arbitrage | A riskless profit from mispriced assets |
| Basis point (bp) | 0.01% |
| Benchmark | The index a strategy is compared against |
| Beta | Sensitivity of a strategy to the market |
| CAGR | Compound annual growth rate |
| Calmar ratio | CAGR divided by maximum drawdown |
| CAPM | Capital Asset Pricing Model; only market risk earns a reward |
| Convexity | Curvature of bond price against yield |
| Covariance matrix | Table of how each pair of assets moves together |
| Delta, Gamma, Vega, Theta, Rho | Option sensitivities to spot, delta, volatility, time and rates |
| Discount factor | Today's value of $1 paid in the future |
| Drawdown | Fall from the previous peak |
| Duration | Sensitivity of a bond price to its yield; also average time to cash flows |
| DV01 | Price change for a 1 basis point move in yield |
| Efficient frontier | The set of portfolios with the best return for each risk level |
| Expected Shortfall (ES) | Average loss beyond VaR |
| Factor | A common driver of many asset returns (market, size, value, momentum) |
| Implied volatility | Volatility that makes the model price match the market price |
| Information ratio | Excess return over benchmark divided by tracking error |
| Kelly criterion | Bet size that maximises long-run growth |
| Log return | `ln(P_t / P_{t-1})`; adds across time |
| Market impact | Price move caused by your own trade |
| Put-call parity | `C - P = S - K e^{-rT}` |
| Risk-free rate | Return on cash with no risk |
| Risk-neutral pricing | Pricing with expected payoffs where all assets grow at the risk-free rate |
| Sharpe ratio | Excess return divided by volatility |
| Shrinkage | Pulling a noisy estimate towards a simpler target to reduce error |
| Skew / smile | Implied volatility varying with strike |
| Slippage | Expected price minus achieved price |
| Sortino ratio | Excess return divided by downside deviation |
| Spread | Ask price minus bid price |
| Survivorship bias | Testing only on assets that still exist |
| Swap | Exchange of fixed for floating interest payments |
| Tracking error | Volatility of returns relative to the benchmark |
| Turnover | How much of the portfolio is traded per year |
| VaR | Value at Risk: loss exceeded only with small probability |
| Volatility | Standard deviation of returns |
| Volatility drag | Gap between average and compound return, about σ²/2 |
| VWAP / TWAP | Volume- / time-weighted average price |
| Yield curve | Yields plotted against maturity |
| Yield to maturity | Single discount rate matching a bond's price |
