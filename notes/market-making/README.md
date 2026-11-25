# Trading and Market Making

How markets work at the level of orders, how market makers earn and lose money, how they set quotes
and manage inventory, and how large orders are executed. Each term is explained the first time it
appears; a glossary is at the end. Formulas come first, then numbers.

Every code block runs on its own (`uv run python file.py`); the comments show its output. Related
pages: trading costs in [finance](../finance/README.md#8-trading-costs), swaps market structure in
[interest rates](../rates/README.md#9-electronic-swaps-market-structure), and a full market-making
system in [system design](../system-design/README.md). A tested limit order book is in
[`src/quantprep/systems/order_book.py`](../../src/quantprep/systems/order_book.py).

Contents:

1. [The order book](#1-the-order-book)
2. [How a market maker makes and loses money](#2-how-a-market-maker-makes-and-loses-money)
3. [Adverse selection](#3-adverse-selection)
4. [Inventory: the Avellaneda-Stoikov model](#4-inventory-the-avellaneda-stoikov-model)
5. [Fair value and short-term signals](#5-fair-value-and-short-term-signals)
6. [Quoting requests for quote (RFQs)](#6-quoting-requests-for-quote-rfqs)
7. [Hedging and risk controls](#7-hedging-and-risk-controls)
8. [Executing large orders](#8-executing-large-orders)
9. [Trading strategies in brief](#9-trading-strategies-in-brief)
10. [Measuring a market-making business](#10-measuring-a-market-making-business)
11. [Interview questions](#11-interview-questions)
12. [Glossary](#12-glossary)

---

## 1. The order book

An **order book** lists all resting buy orders (**bids**) and sell orders (**asks** or offers) at each
price. Orders at the same price are filled in arrival order: **price-time priority**.

| Term | Meaning |
|---|---|
| **Best bid / best ask** | Highest price someone will buy at / lowest price someone will sell at. Together: the **top of book** or **touch**. |
| **Spread** | `ask - bid`. **Mid** = `(bid + ask) / 2`. |
| **Depth** | Quantity available at each price level. |
| **Tick size** | Smallest allowed price step. When the spread is one tick most of the time, the asset is **tick-constrained** and queue position matters a lot. |
| **Limit order** | Buy or sell at a given price or better. Rests in the book if not filled: it **provides liquidity** (the **maker**). |
| **Market order** | Trade now at the best available prices. It **takes liquidity** (the **taker**) and pays the spread. |
| **IOC / FOK** | Immediate-or-cancel: fill what you can now, cancel the rest. Fill-or-kill: all now or nothing. |
| **Post-only** | A limit order that is cancelled instead of trading immediately, so it is always a maker. |
| **Iceberg** | An order that shows only part of its size; the rest refills as the shown part trades. |
| **Maker-taker fees** | Many exchanges pay makers a **rebate** and charge takers a fee. |
| **Queue position** | How much quantity is ahead of your order at its price. Your order fills only after all of it trades or cancels. |

**Expected time to fill** a resting order: `time ≈ quantity ahead / (rate it trades + rate it cancels)`.

---

## 2. How a market maker makes and loses money

A **market maker** quotes both a bid and an ask and earns the spread when both sides trade. Three
things decide whether this works:

`P&L = spread capture  +  inventory P&L  +  rebates - fees`

| Part | Formula | Meaning |
|---|---|---|
| **Spread capture** (edge) | `Σ side × (mid at fill - fill price) × size` | What you earn versus mid at the moment of each fill. `side` = +1 for a buy, -1 for a sell. Positive by construction for a maker. |
| **Inventory P&L** | `Σ position × Δmid` | Gain or loss on the position you hold while waiting for the other side. |
| **Adverse selection** | shows up inside inventory P&L | The mid tends to move against you right after you trade with someone better informed. |

**The core tension:** a tighter spread wins more trades but earns less on each one and attracts more
informed traders. A wider spread is safer but trades less. Holding inventory earns nothing and adds
risk, so a market maker wants to turn it over quickly.

---

## 3. Adverse selection

**Adverse selection:** the people most eager to trade with you are often those who know the price is
about to move. A market maker must charge enough on uninformed flow to pay for losses on informed
flow.

**Glosten-Milgrom model.** The true value is `V_H` or `V_L` with equal chance. A fraction `μ` of
traders know it; the rest buy or sell at random. The ask is set so the market maker breaks even on a
buy: `ask = E[V | a buy arrives]`.

- Formula: `spread = μ × (V_H - V_L)`.
- Example: 20% informed, values 1 apart: `spread = 0.2 × 1 = 0.2`.
- Meaning: the spread exists even with zero costs, purely to pay for informed trading.

**Kyle model.** One informed trader hides among random **noise traders**. The price moves in
proportion to net order flow:

- Formula: `Δprice = λ × order flow`, with `λ = σ_V / (2 σ_U)`. `σ_V` = uncertainty about the true
  value, `σ_U` = size of noise trading.
- Example: `σ_V = 2`, `σ_U = 1,000` shares: `λ = 0.001`, so a net 500-share buy moves the price 0.5.
- Meaning: **Kyle's lambda** measures how illiquid a market is. More noise trading means deeper markets.

**Measuring it in practice: markouts.**
`markout(h) = side × (mid at time t + h - fill price)`, from the market maker's side, for horizons
`h` such as 1 second, 10 seconds, 1 minute.
- Positive and stable: you capture spread and keep it.
- Starts positive then decays below zero: you are being picked off. Widen, skew or stop quoting that
  client or venue.

---

## 4. Inventory: the Avellaneda-Stoikov model

The standard model for how a market maker should quote around its inventory.

**Set-up:** mid price `s` moves randomly with volatility `σ`. Your quotes at distance `δ` from mid
get hit at rate `A e^{-kδ}` (further away, fewer fills). You hold inventory `q`, have risk aversion
`γ`, and stop at time `T`.

- **Reservation price** (your own fair value given the inventory you hold):
  `r = s - q γ σ² (T - t)`
- **Optimal total spread** around it:
  `δ_bid + δ_ask = γ σ² (T - t) + (2/γ) ln(1 + γ/k)`

**Meaning:**
- Long inventory (`q > 0`) pushes both quotes down: you sell more readily and buy less readily.
  This is called **skewing**.
- More volatility, more risk aversion or more time left: bigger skew and wider spread.
- `(2/γ) ln(1 + γ/k)` is the spread from competition for fills alone; `k` is how fast fill
  probability falls as you quote further away.

```python
import numpy as np

# Avellaneda-Stoikov (2008) set-up: mid follows Brownian motion, fills arrive at rate A*exp(-k*distance)
s0, T, sigma, dt = 100.0, 1.0, 2.0, 0.005
gamma, k, A = 0.1, 1.5, 140.0
n_paths, n_steps = 1_000, int(T / dt)
half_spread = 0.5 * (gamma * sigma**2 * T + (2 / gamma) * np.log(1 + gamma / k))  # used by both


def simulate(skew_inventory: bool, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    s = np.full(n_paths, s0)
    q = np.zeros(n_paths)                 # inventory
    cash = np.zeros(n_paths)
    for i in range(n_steps):
        tau = T - i * dt                  # time left
        if skew_inventory:
            reservation = s - q * gamma * sigma**2 * tau
            spread = gamma * sigma**2 * tau + (2 / gamma) * np.log(1 + gamma / k)
            bid, ask = reservation - spread / 2, reservation + spread / 2
        else:
            bid, ask = s - half_spread, s + half_spread
        hit_bid = rng.random(n_paths) < A * np.exp(-k * (s - bid)) * dt
        hit_ask = rng.random(n_paths) < A * np.exp(-k * (ask - s)) * dt
        q += hit_bid.astype(float) - hit_ask
        cash += np.where(hit_ask, ask, 0.0) - np.where(hit_bid, bid, 0.0)
        s = s + sigma * np.sqrt(dt) * rng.choice([-1.0, 1.0], n_paths)
    return cash + q * s, q                # final P&L marked at mid, final inventory


for name, skew in [("inventory-skewed", True), ("symmetric", False)]:
    pnl, q = simulate(skew)
    print(f"{name:17s} P&L mean {pnl.mean():6.2f}  std {pnl.std():5.2f}  "
          f"final inventory std {q.std():5.2f}")
# inventory-skewed  P&L mean  65.05  std  6.49  final inventory std  2.85
# symmetric         P&L mean  66.87  std 12.92  final inventory std  7.83
```

**Reading the output.** Skewing gives up a little average P&L but halves its standard deviation and
keeps inventory much smaller. That is the trade every market maker makes.

**Extensions asked about:** inventory limits (Guéant-Lehalle-Fernandez-Tapia gives closed-form quotes
with a hard cap), adding a short-term price signal (shift the reservation price by the predicted
move), and hedging inventory in a correlated instrument instead of only skewing.

---

## 5. Fair value and short-term signals

The mid is not always the best estimate of value. Common improvements:

| Signal | Formula | Idea |
|---|---|---|
| **Order book imbalance** | `I = Q_bid / (Q_bid + Q_ask)` | More size on the bid than the ask suggests the next move is up. |
| **Weighted mid** (microprice) | `micro = I × ask + (1 - I) × bid` | Fair value leans towards the side with *less* size, which is more likely to be cleared. |
| **Trade flow** | sum of signed trade sizes over a recent window | Persistent buying predicts further short-term rises. |
| **Lead-lag** | price of a related, faster instrument | Futures often move before the cash product; a liquid swap tenor before an illiquid one. |
| **Cross-asset** | moves in correlated markets | e.g. Treasury futures for swaps, index futures for single stocks. |

**Example:** bid 99.98 with 900 lots, ask 100.00 with 100 lots. `I = 900 / 1000 = 0.9`, so
`micro = 0.9 × 100.00 + 0.1 × 99.98 = 99.998`, well above the mid of 99.99.

**Signal half-life:** short-term signals decay within seconds to minutes, so latency matters. A
signal is useful only if its predicted move is larger than the cost of acting on it (spread plus
fees).

---

## 6. Quoting requests for quote (RFQs)

In dealer markets (bonds, swaps, foreign exchange) clients send a **request for quote** to several
dealers and trade with the best price. The dealer chooses how far from mid to quote.

- Formula: `E[profit] = P(win | quote s) × (s - expected adverse move)`
- `P(win | s)` falls as `s` widens; estimate it from your history of won and lost RFQs.
- `expected adverse move` comes from the markouts of past trades with that client.

```python
import numpy as np

# Quote an RFQ at mid + s (in basis points). The client compares several dealers.
s0, width = 0.5, 0.2           # win probability is 50% at 0.5 bp; falls off over ~0.2 bp
adverse = 0.2                  # expected move against us after winning, bp (from markouts)


def win_prob(s: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp((s - s0) / width))


s = np.linspace(0, 2, 2001)
expected = win_prob(s) * (s - adverse)                 # E[profit] = P(win) x (edge - adverse cost)
best = s[expected.argmax()]
print(f"best quote {best:.3f} bp, win rate {win_prob(best):.0%}, "
      f"expected profit {expected.max():.3f} bp per RFQ")
# best quote 0.553 bp, win rate 43%, expected profit 0.153 bp per RFQ
for a in [0.0, 0.4]:
    e = win_prob(s) * (s - a)
    print(f"adverse cost {a} bp -> best quote {s[e.argmax()]:.3f} bp, "
          f"win rate {win_prob(s[e.argmax()]):.0%}")
# adverse cost 0.0 bp -> best quote 0.453 bp, win rate 56%
# adverse cost 0.4 bp -> best quote 0.681 bp, win rate 29%
```

**Meaning:** quote wider for clients whose trades move the market afterwards; quote tighter for
clients whose flow is uninformed. **Winner's curse:** when you win, you were the cheapest dealer,
so on average your price was more wrong than the others'. **Information leakage:** a large client
asking many dealers reveals its intention, and the losing dealers may trade ahead.

Other inputs to the quote: size (bigger means more impact to hedge), current inventory (a quote that
reduces your risk can be tighter, the same skew idea as section 4), and the client relationship.

---

## 7. Hedging and risk controls

**Skew or hedge?** After a fill you can wait for an offsetting client trade (skew quotes and earn the
spread) or hedge now in a liquid market (pay its spread, remove the risk).
Rule: hedge when `expected cost of waiting = ½ γ × variance while waiting` is greater than the cost of
hedging now. Large or risky positions are hedged quickly; small ones are kept and skewed.

**Hedge ratio:** `hedge size = risk of position / risk per unit of hedge`. For swaps, hedge DV01 with
Treasury futures; the remaining risk is **basis risk** (the hedge does not move exactly like the
position).

**Risk controls every automated trading system has:**
- **Position and risk limits** per instrument, per desk, and in total.
- **Price checks:** reject a quote too far from a reference price ("fat-finger" protection).
- **Stale data check:** pull quotes if market data stops updating.
- **Order rate limits** and **maximum order size**.
- **Loss limits:** stop trading after a daily loss threshold.
- **Kill switch:** one action cancels every order and stops the strategy.

---

## 8. Executing large orders

A large order cannot trade all at once without moving the price, but trading slowly leaves it exposed
to price moves. Execution algorithms balance the two.

| Algorithm | What it does |
|---|---|
| **TWAP** | Time-weighted: equal amounts in equal time slices. |
| **VWAP** | Volume-weighted: trade in proportion to the usual volume curve over the day (more at open and close). |
| **POV** | Percentage of volume: always be a fixed share (e.g. 10%) of market volume. |
| **Implementation shortfall** | Minimise total cost versus the price when the decision was made; trades faster early. |

**Almgren-Chriss model.** Sell `X` shares over time `T`. Trading faster costs more temporary impact
(`η` per unit of trading speed); trading slower leaves more price risk (`σ`). With risk aversion `λ`:

- Formula: holdings `x(t) = X sinh(κ (T - t)) / sinh(κ T)`, with `κ = √(λ σ² / η)`.
- Meaning: small `λ` gives a straight line (TWAP). Large `λ` sells most of the order early.

```python
import numpy as np

# Almgren-Chriss: sell X shares over T days, trading off impact cost against price risk
X, T, n = 1_000_000, 5.0, 5                 # shares, days, trading intervals
sigma = 0.95                                # price volatility, $ per share per sqrt(day)
eta = 2.5e-6                                # temporary impact: $ per share per (share/day)
t = np.linspace(0, T, n + 1)

for risk_aversion in [1e-8, 1e-6, 1e-5]:
    kappa = np.sqrt(risk_aversion * sigma**2 / eta)
    holdings = X * np.sinh(kappa * (T - t)) / np.sinh(kappa * T)
    trades = -np.diff(holdings)
    print(f"risk aversion {risk_aversion:.0e}: thousand shares sold per day",
          np.round(trades / 1e3).astype(int))
# 1e-08: [204 201 199 198 197]   almost even, like TWAP
# 1e-06: [455 252 143  87  63]
# 1e-05: [850 127  19   3   0]   sell fast to cut risk
```

Impact itself follows the **square-root law** (cost ≈ `σ × √(size / daily volume)`); see the
[finance page](../finance/README.md#8-trading-costs).

---

## 9. Trading strategies in brief

| Strategy | Idea | Key risk |
|---|---|---|
| **Market making** | Earn the spread; stay flat | Adverse selection, inventory |
| **Statistical arbitrage** | Many small, diversified bets on predicted short-term moves | Crowding, costs, regime change |
| **Pairs trading** | Two related assets; buy the cheap one and sell the rich one when their spread is unusually wide | The relationship breaks |
| **Momentum / trend** | Assets that rose keep rising over weeks to months | Sharp reversals |
| **Mean reversion** | Short-term moves partly reverse | Trends that keep going |
| **Carry** | Hold what pays more (higher yield, roll-down) | Sudden unwinds |
| **Relative value** (rates) | Rich/cheap points on the curve, swap spreads, futures basis | Leverage, funding |

**Pairs trading in formulas:**
- Spread: `x_t = log P_A - β log P_B`, with `β` from a regression. Test that the spread is stationary
  (does not drift away) with a **cointegration** test (Engle-Granger).
- Signal: `z = (x_t - mean) / std`. Enter at `|z| > 2`, exit near 0.
- Speed: fit `x_t = φ x_{t-1} + ε`. **Half-life** of a deviation = `-ln 2 / ln φ`.
  `φ = 0.95` gives about 13.5 days.

---

## 10. Measuring a market-making business

| Metric | Formula / meaning |
|---|---|
| **Markouts** | Average `side × (mid later - fill price)` at several horizons, split by client, venue and size. |
| **Hit ratio / win rate** | RFQs won / RFQs quoted. Too high: too cheap. Too low: not competitive. |
| **Fill rate** | Resting quote volume that actually traded. |
| **Spread capture** | Realised edge per unit traded. |
| **Inventory turnover / holding time** | How quickly positions are offset. |
| **P&L per unit of risk** | Daily P&L divided by average DV01 or position size. |
| **Sharpe ratio of daily P&L** | Good market-making businesses often have very high values (above 3) because they earn small amounts very often. |
| **Latency** | Time from market data to order sent (tick-to-trade), measured in microseconds. |

**Backtesting market making is hard.** A simulator must model queue position (your order fills
only after the queue ahead), latency, the fact that your own orders change what others do, and
adverse selection on your fills. Assuming "filled whenever the price touches my quote" makes almost
any strategy look profitable.

---

## 11. Interview questions

Each answer gives the formula first, then the numbers, then why.

**Q1. 20% of traders are informed and the asset is worth either 99 or 101. What spread do you quote?**
- Formula: `spread = μ × (V_H - V_L)` (Glosten-Milgrom).
- Numbers: `0.2 × (101 - 99) = 0.4`, so quote 99.80 / 100.20.
- Why: the gain from uninformed traders must pay for losses to informed ones.

**Q2. You are long 10 units. Mid 100, σ = 2, γ = 0.1, half the session left (T - t = 0.5). Where
is your reservation price?**
- Formula: `r = s - q γ σ² (T - t)`.
- Numbers: `100 - 10 × 0.1 × 4 × 0.5 = 98`.
- Why: you value the asset below mid because you hold too much of it, so both quotes move down.

**Q3. Bid 99.98 × 900, ask 100.00 × 100. Where is fair value?**
- Formula: `micro = I × ask + (1 - I) × bid`, `I = Q_bid / (Q_bid + Q_ask)`.
- Numbers: `I = 0.9`, `micro = 99.998`.
- Why: the thin ask is likely to be cleared, so the next mid is more likely up.

**Q4. You bought at 100.00 and one minute later the mid is 99.97. Across thousands of trades with
one client this is typical. What do you do?**
- Formula: `markout = side × (mid later - fill price) = +1 × (99.97 - 100.00) = -0.03`.
- Why: consistent negative markouts mean the client is informed. Widen or skew their quotes, quote
  smaller, or hedge faster.

**Q5. Your order is 500 lots behind at the bid; 50 lots trade there per second and nothing cancels.
When do you expect to fill?**
- Formula: `time ≈ quantity ahead / trade rate`.
- Numbers: `500 / 50 = 10` seconds.
- Why: price-time priority; cancellations ahead of you would make it sooner.

**Q6. Kyle model: σ_V = 2, noise trading σ_U = 1,000 shares. How much does a net buy of 500 move
the price?**
- Formula: `Δp = λ × flow`, `λ = σ_V / (2 σ_U)`.
- Numbers: `λ = 0.001`, `Δp = 0.5`.

**Q7. A strategy wins 40% of the time. Winners average 3, losers 1.5. Is it profitable? What hit
rate breaks even?**
- Formula: `E = p W - (1 - p) L`; breakeven `p* = L / (W + L)`.
- Numbers: `0.4 × 3 - 0.6 × 1.5 = 0.3 > 0`; `p* = 1.5 / 4.5 = 33%`.

**Q8. A pairs spread follows `x_t = 0.95 x_{t-1} + ε`. How long does a deviation take to halve?**
- Formula: `half-life = -ln 2 / ln φ`.
- Numbers: `-0.693 / ln 0.95 = -0.693 / -0.0513 ≈ 13.5` days.

**Q9. Why does an Almgren-Chriss trader with higher risk aversion sell faster?**
- Formula: `κ = √(λ σ² / η)`; holdings fall like `sinh(κ (T - t))`.
- Why: larger `λ` raises `κ`, putting more weight on cutting exposure to price moves than on
  saving impact cost.

**Q10. Your market-making backtest shows a Sharpe ratio of 8. What do you check?**
- Fill assumptions (queue position, partial fills), latency, adverse selection on fills, fees and
  rebates, whether quotes would have changed the market, and look-ahead in the signals. Most
  unrealistic backtests fill orders that would never have filled.

---

## 12. Glossary

| Term | Plain meaning |
|---|---|
| Adverse selection | Trading with someone who knows more, so the price moves against you afterwards |
| Ask / offer | Price at which someone will sell |
| Basis risk | Risk that the hedge does not move exactly like the position |
| Bid | Price at which someone will buy |
| Cointegration | Two series that wander but whose difference stays stationary |
| Depth | Quantity available at each price |
| FOK / IOC | Fill-or-kill / immediate-or-cancel orders |
| Half-life | Time for a deviation to shrink by half |
| Iceberg | Order that shows only part of its size |
| Implementation shortfall | Cost of execution versus the decision price |
| Inventory | Position a market maker holds between trades |
| Kill switch | Control that cancels all orders and stops trading |
| Kyle's lambda | Price impact per unit of net order flow |
| Latency | Delay between an event and your reaction |
| Maker / taker | Provides liquidity with a resting order / removes it by trading immediately |
| Markout | Trade P&L measured a fixed time after the trade |
| Microprice | Mid weighted by book imbalance |
| Noise trader | Trader without information who trades for other reasons |
| Order book | List of resting bids and asks |
| POV | Percentage-of-volume execution |
| Price-time priority | Best price first, then earliest order |
| Queue position | Quantity ahead of your order at its price |
| Rebate | Payment to the maker for providing liquidity |
| Reservation price | Your own fair value after adjusting for inventory |
| RFQ | Request for quote |
| Skew | Shift both quotes to encourage trades that reduce inventory |
| Spread | Ask minus bid |
| Tick size | Smallest price step |
| TWAP / VWAP | Time- / volume-weighted average price |
| Winner's curse | Winning a competitive quote means you were probably the most wrong |
