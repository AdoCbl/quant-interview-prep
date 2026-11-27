# Quant Developer, Analytics and Middle Office: Targeted Prep

A focused plan for a quant developer role on an analytics platform. The team builds services that
compute sensitivities (option Greeks and rate risk) across asset classes, runs what-if scenarios,
serves analytics over any time horizon, and works directly with risk managers and trading desks,
including an on-call rotation. Each term is explained the first time it appears; a glossary is at the end.

Python code blocks run on their own (`uv run python file.py`) and the block after each shows its
output. The tested engine used below is
[`src/quantprep/analytics/risk_engine.py`](../../src/quantprep/analytics/risk_engine.py), with tests in
[`tests/test_risk_engine.py`](../../tests/test_risk_engine.py).

Contents:

1. [What the job is, and what gets tested](#1-what-the-job-is-and-what-gets-tested)
2. [A 10-day plan](#2-a-10-day-plan)
3. [Sensitivities: analytic vs bump-and-revalue](#3-sensitivities-analytic-vs-bump-and-revalue)
4. [A risk and scenario engine you can talk through](#4-a-risk-and-scenario-engine-you-can-talk-through)
5. [Analytics over any time horizon](#5-analytics-over-any-time-horizon)
6. [Engineering: Git, CI/CD, Docker, Kubernetes](#6-engineering-git-cicd-docker-kubernetes)
7. [Elixir and the BEAM in one page](#7-elixir-and-the-beam-in-one-page)
8. [On-call and production incidents](#8-on-call-and-production-incidents)
9. [Mock interview: 15 questions with answers](#9-mock-interview-15-questions-with-answers)
10. [Behavioural round](#10-behavioural-round)
11. [Questions to ask them](#11-questions-to-ask-them)
12. [Glossary](#12-glossary)

---

## 1. What the job is, and what gets tested

**The job in one sentence:** build and run reliable, fast, reproducible services that turn positions
and market data into the numbers risk managers and traders act on: PV (present value), Greeks,
DV01, scenario P&L and history.

| Round | What they probe | Prepare from |
|---|---|---|
| Coding (1–2 rounds) | Medium algorithm problems; clean, tested, readable code in Python or C++ | [DSA](../dsa/README.md), [Python](../python/README.md), [features and tricks](../python/senior-features-and-tricks.md) |
| Derivatives and rates | Black-Scholes, Greeks, put-call parity, bump vs analytic Greeks, DV01, curve building, swap PV | Section 3 below, [finance](../finance/README.md), [rates](../rates/README.md), [domain](../domain/README.md) |
| Maths | Linear algebra, optimisation, numerical methods, probability, statistics | [linear algebra](../linear-algebra/README.md), [numerical methods](../numerical-methods/README.md), [probability](../probability/README.md), [statistics](../statistics/README.md) |
| System design | A risk / scenario analytics service | [System design, Design A](../system-design/README.md#design-a-risk-and-scenario-analytics-service-analytics--middle-office), sections 4–6 below |
| Behavioural | Working with traders and risk, ownership, on-call under pressure, humility | Section 10 below |

**What separates a strong candidate** for this kind of team:
1. You explain a number end to end: which trade, which market data snapshot, which model, which bump.
2. You think about correctness first (tests against known identities, reproducibility), then speed.
3. You know the finance well enough to spot a wrong number: a put with positive delta, a receiver swap with positive DV01, P&L explain with a large unexplained residual.
4. You have run production systems and talk calmly about incidents.

---

## 2. A 10-day plan

| Day | Focus | Done when you can... |
|---|---|---|
| 1 | Black-Scholes, Greeks, parity ([finance §6](../finance/README.md#6-options)) | derive delta and vega, and state put-call parity and what breaks it |
| 2 | Sections 3–4 here; read the risk engine and its tests | explain bump size, central differences and the error trade-off |
| 3 | Rates: curves, DV01, bucketed risk ([rates §1–5](../rates/README.md)) | compute a swap's PV and DV01 by hand |
| 4 | Domain: futures, P&L, Treasury and SOFR futures ([domain](../domain/README.md)) | explain variation margin, FIFO P&L, CTD and the convexity adjustment |
| 5 | Linear algebra and numerical methods | explain Cholesky, PCA, conditioning, Newton vs Brent, least squares |
| 6 | Probability and statistics | solve 10 classic problems aloud in under 5 minutes each |
| 7 | DSA: 8 problems from [DSA](../dsa/README.md), timed at 25 minutes | solve and test each without hints |
| 8 | System design: Design A plus sections 5–6 here, timed at 45 minutes | draw it, size it, and handle the follow-up questions |
| 9 | Behavioural: write 6 stories (section 10) and say them out loud | tell each story in 2 minutes |
| 10 | Full mock: section 9, then the weakest area again | — |

---

## 3. Sensitivities: analytic vs bump-and-revalue

**Bump-and-revalue** (also called finite differences): reprice with an input moved slightly, and divide the price change by the move.

- Forward difference: `Δ ≈ (V(S+h) − V(S)) / h`. Error is proportional to `h`.
- Central difference: `Δ ≈ (V(S+h) − V(S−h)) / 2h`. Error is proportional to `h²`, at the cost of one extra price.
- Second derivative: `Γ ≈ (V(S+h) − 2V(S) + V(S−h)) / h²`.
- **Step size trade-off**: total error ≈ `c·h² + ε·V / h`, where `ε ≈ 10⁻¹⁶` is double-precision rounding. A small `h` cuts the truncation error (from the formula being an approximation) but magnifies rounding error. Best central-difference `h` ≈ `ε^(1/3)` × scale, about 10⁻⁵ relative. For gamma it is `ε^(1/4)`, so gamma needs larger bumps.

```python
import math

from scipy.stats import norm


def call(s: float, k: float = 100, t: float = 1.0, r: float = 0.03, v: float = 0.2) -> float:
    d1 = (math.log(s / k) + (r + 0.5 * v * v) * t) / (v * math.sqrt(t))
    return s * norm.cdf(d1) - k * math.exp(-r * t) * norm.cdf(d1 - v * math.sqrt(t))


s0 = 100.0
d1 = (math.log(s0 / 100) + (0.03 + 0.02) * 1.0) / 0.2
exact_delta, exact_gamma = norm.cdf(d1), norm.pdf(d1) / (s0 * 0.2)

print(" step h    forward err   central err   gamma err")
for h in (1e0, 1e-2, 1e-4, 1e-6, 1e-8):
    fwd = (call(s0 + h) - call(s0)) / h
    ctr = (call(s0 + h) - call(s0 - h)) / (2 * h)
    gam = (call(s0 + h) - 2 * call(s0) + call(s0 - h)) / (h * h)
    print(f"{h:7.0e}   {abs(fwd - exact_delta):11.1e}   {abs(ctr - exact_delta):11.1e}"
          f"   {abs(gam - exact_gamma):9.1e}")
```

Output:

```text
 step h    forward err   central err   gamma err
  1e+00       9.6e-03       7.2e-05     2.8e-06
  1e-02       9.7e-05       7.2e-09     3.5e-10
  1e-04       9.7e-07       6.7e-12     4.6e-07
  1e-06       1.0e-08       7.4e-09     1.6e-02
  1e-08       8.8e-07       8.8e-07     1.9e-02
```

The best central step is around 10⁻⁴ here, and gamma blows up below 10⁻⁶. That is why desks use fixed, sensible bumps (1% of spot, 1 vol point, 1 basis point) and report Greeks *in those units*.

| | Analytic Greeks | Bump-and-revalue |
|---|---|---|
| Speed | One evaluation | 2 prices per first-order Greek (central difference); n inputs need 2n prices |
| Accuracy | Exact for the model | Depends on the bump; noisy with Monte Carlo unless the same random numbers are reused |
| Coverage | Needs a formula per product | Works for any pricer, which is why platforms use it as the default |
| Matches P&L? | Infinitesimal | A 1 bp bump is what traders see; for big moves, scenarios are better |

Points interviewers like:
- **Bucketed (key-rate) DV01**: bump each curve input separately and *rebuild* the curve; the bucket DV01s should add up to roughly the parallel DV01.
- **Cross gamma** (e.g. vanna, `∂²V/∂S∂σ`): bump two inputs at once; needed when scenarios move spot and vol together.
- **Sticky strike vs sticky delta**: when spot moves, does the vol for a given strike stay fixed, or does the whole smile move with spot? The choice changes delta, so say which one you use.
- **Algorithmic differentiation** (AAD, adjoint algorithmic differentiation): the computer applies the chain rule backwards through the pricing code and gets *all* sensitivities for about 3–5× the cost of one price. It is standard for large Monte Carlo books.
- **Consistency checks**: analytic and bumped Greeks should agree within tolerance. Greeks should be continuous from one day to the next. Signs should be sensible.

---

## 4. A risk and scenario engine you can talk through

The engine in `src/quantprep/analytics/risk_engine.py` is about 150 lines and makes the design choices interviewers ask about:

- **Immutable market snapshot** (`Market`, a frozen dataclass whose dictionaries are read-only): a bump returns a *new* snapshot, so a scenario can never leak into the base case. A snapshot ID makes results reproducible.
- **One interface** (`pv(market)`): every instrument gets every bumped Greek for free; options also have analytic Greeks, and a test checks the two agree.
- **Positions tagged by book** so that additive measures (PV, delta, vega, DV01) are summed up the hierarchy. VaR (value at risk) is *not* additive: keep scenario P&L vectors and aggregate those.
- **Full-revaluation scenario grid** plus a **Taylor estimate** (`delta·dS + ½ gamma·dS² + vega·dσ + rho·dr`). A test checks they agree for small shocks; for large shocks only full revaluation is trustworthy.
- **Tests check identities**, not just that the code runs: put-call parity, a par swap has PV 0, the DV01 formula, a future's delta equals `e^(rT)` × multiplier, additivity, and a zero shock giving zero P&L.

```python
from quantprep.analytics import (
    EuropeanOption,
    Future,
    Market,
    Position,
    Swap,
    book_risk,
    scenario_grid,
)

m = Market(spots={"SPX": 5000.0}, vols={"SPX": 0.18}, rate=0.04)
book = [
    Position(EuropeanOption("SPX", 5000, 0.5), 200, book="index-vol"),
    Position(EuropeanOption("SPX", 4500, 0.5, call=False), -300, book="index-vol"),
    Position(Future("SPX", 0.25, trade_price=5050.0, multiplier=50), -2, book="index-vol"),
    Position(Swap(0.04, 10, notional=50e6), 1, book="rates"),
]

for name, r in book_risk(book, m).items():
    print(f"{name:9s} PV {r['pv']:>11,.0f}  delta {r.get('delta', 0):6.1f}"
          f"  gamma {r.get('gamma', 0):7.4f}  vega/pt {r.get('vega', 0) * 0.01:8,.0f}"
          f"  DV01 {r['dv01']:8,.0f}")

grid = scenario_grid(book, m, spot_moves=[-0.10, -0.05, 0.0, 0.05, 0.10],
                     vol_moves=[-0.05, 0.0, 0.05], rate_moves=[0.0, 0.005])
print("worst scenario:", min(grid, key=grid.get), f"{min(grid.values()):,.0f}")
print("spot +10%, vol -5pt, rates flat:", f"{grid[0.10, -0.05, 0.0]:,.0f}")
```

Output:

```text
index-vol PV      45,380  delta   60.7  gamma  0.0137  vega/pt      313  DV01       26
rates     PV    -327,482  delta    0.0  gamma  0.0000  vega/pt        0  DV01  -41,870
worst scenario: (-0.1, 0.05, 0.005) -2,083,466
spot +10%, vol -5pt, rates flat: 28,306
```

How to read it: the worst corner combines all three shocks. The rates book dominates it (DV01 −41,870 × 50 bp ≈ −2.09 million); the option book adds a small loss because its short 4500 puts gain vega as spot falls toward them.

**How it scales** (the system design follow-up): split work by (batch of positions × scenario), run it on stateless workers, cache by (instrument, snapshot ID, scenario, library version), and reprice incrementally when one trade or one curve changes. See [Design A](../system-design/README.md#design-a-risk-and-scenario-analytics-service-analytics--middle-office).

---

## 5. Analytics over any time horizon

"Any time horizon" means: show me risk or P&L for today, month to date, or any past date, *exactly as it was*, and also as corrected since then.

- **Bitemporal data**: store two times for every record: **valid time** (the business date the number is for) and **knowledge time** (when the system learned it). Corrections are appended, never overwritten.
  - "What did we report on 3 January?" = filter on knowledge time ≤ 3 January.
  - "What is the true history?" = latest knowledge for each valid date.
- **Additive over time**: P&L and cash flows can be summed over days. Risk (delta, DV01) is a *level* at a point in time: report an end-of-period value or an average, never a sum.
- **As-of joins**: attach to each trade the latest quote at or before its time. This is the basic tick-analytics operation (`pd.merge_asof`, `aj` in kdb+/q).
- **Storage**: a columnar time-series store partitioned by date, with snapshots of market data and positions, so any day can be recomputed with the code version used at the time.

```python
import pandas as pd

# Bitemporal marks: `valid` = the day the mark is for, `known` = when we learned it.
# The 2nd-Jan mark was corrected on the 4th.
marks = pd.DataFrame({
    "valid": pd.to_datetime(["2027-01-01", "2027-01-02", "2027-01-03", "2027-01-02"]),
    "known": pd.to_datetime(["2027-01-01 18:00", "2027-01-02 18:00", "2027-01-03 18:00",
                             "2027-01-04 09:00"]),
    "price": [100.0, 101.0, 99.5, 101.6],
})


def as_of(knowledge_time: str) -> pd.Series:
    """Marks as we believed them at `knowledge_time`: latest version per valid day."""
    seen = marks[marks["known"] <= pd.Timestamp(knowledge_time)]
    return seen.sort_values("known").groupby("valid")["price"].last()


print("as reported on 3 Jan:", as_of("2027-01-03 23:00").tolist())   # what traders saw
print("as known today      :", as_of("2027-01-05").tolist())          # after the correction

# P&L over any horizon from daily P&L: sum the days (P&L is additive in time)
pos = 1_000
daily = (as_of("2027-01-05").diff().dropna() * pos).round(2)
print("daily:", daily.tolist(), " 2-day:", round(daily.sum(), 2))

# Latest price at or before each trade time (as-of join, the core of tick analytics)
trades = pd.DataFrame({"t": pd.to_datetime(["2027-01-02 12:00", "2027-01-03 20:00"]), "qty": [5, -3]})
quotes = pd.DataFrame({"t": pd.to_datetime(["2027-01-02 09:00", "2027-01-02 15:00",
                                            "2027-01-03 18:00"]), "mid": [100.8, 101.1, 99.4]})
print(pd.merge_asof(trades, quotes, on="t").to_string(index=False))
```

Output:

```text
as reported on 3 Jan: [100.0, 101.0, 99.5]
as known today      : [100.0, 101.6, 99.5]
daily: [1600.0, -2100.0]  2-day: -500.0
                  t  qty   mid
2027-01-02 12:00:00    5 100.8
2027-01-03 20:00:00   -3  99.4
```

---

## 6. Engineering: Git, CI/CD, Docker, Kubernetes

| Topic | What to be able to say |
|---|---|
| **Git** | Short-lived branches and small pull requests; rebase vs merge (rebase rewrites your own branch to sit on top of main; merge keeps both histories); `git bisect` finds the commit that broke a number; never rewrite shared history. |
| **CI/CD** (continuous integration / delivery) | Every push runs lint, type checks and tests, including **golden-number tests**: price a fixed book against a stored snapshot and fail if PV or Greeks move beyond tolerance. Deploy automatically to staging, then production behind a flag or a canary. |
| **Docker** | A container image bundles the code and its exact dependencies, so a pricing library runs the same on a laptop, in CI and in production. Pin versions, use small base images, run as a non-root user. |
| **Kubernetes** (K8s) | Runs containers across many machines. *Pod*: one or more containers scheduled together. *Deployment*: keeps N copies running and rolls out new versions. *Service*: a stable network name in front of pods. *Horizontal Pod Autoscaler*: adds pods when CPU or queue depth rises. *Liveness/readiness probes*: restart dead pods; send traffic only to ready ones. *ConfigMap/Secret*: configuration and credentials. |
| **Observability** | Metrics (latency, queue depth, error rate per product), structured logs with a request or snapshot ID, traces across services, and alerts on symptoms that users would notice. |

A minimal container sketch for a Python pricing worker (`quantprep.worker` is a placeholder module):

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
COPY src ./src
USER 1000
CMD ["uv", "run", "python", "-m", "quantprep.worker"]
```

---

## 7. Elixir and the BEAM in one page

Some analytics platforms run their service layer on **Elixir**, a functional language on the
**BEAM** (the Erlang virtual machine, built for telephone switches that must never go down).

| Idea | Meaning | Why a risk platform cares |
|---|---|---|
| **Processes** | Very lightweight (about 2 KB each); millions per machine; each has its own memory | One process per user subscription, per book or per market-data feed |
| **Message passing** | Processes share nothing; they send each other immutable messages | No locks and no data races |
| **Supervisors** | A process that restarts its children when they crash, following a set strategy | "Let it crash": a bad message kills one process, not the service |
| **OTP** | The standard library of patterns: `GenServer` (a stateful server process), `Supervisor`, `Application` | Uniform structure across services |
| **Preemptive scheduler** | The BEAM interrupts long-running processes so none can starve the others | Low, predictable latency for live risk while heavy jobs run |
| **Weakness** | Slow at number crunching | Heavy maths goes to native code (Rust via Rustler, C/C++ via NIFs, native implemented functions) or to separate Python/C++ pricing services |

What a small stateful server looks like (Elixir is not installed here, so this is not run):

```elixir
defmodule BookRisk do
  use GenServer
  # Client API
  def start_link(book), do: GenServer.start_link(__MODULE__, %{book: book, dv01: 0.0}, name: via(book))
  def add_trade(book, dv01), do: GenServer.cast(via(book), {:trade, dv01})
  def dv01(book), do: GenServer.call(via(book), :dv01)
  # Server callbacks: state is only touched here, one message at a time
  def init(state), do: {:ok, state}
  def handle_cast({:trade, d}, s), do: {:noreply, %{s | dv01: s.dv01 + d}}
  def handle_call(:dv01, _from, s), do: {:reply, s.dv01, s}
  defp via(book), do: {:via, Registry, {BookRegistry, book}}
end
```

Talking point: "Python is great for research and pricing; the BEAM is great for many concurrent,
long-lived, fault-tolerant services; C++ or Rust for the hot loops. I'd draw the boundaries along those lines."

---

## 8. On-call and production incidents

A playbook to describe, step by step:

1. **Acknowledge and assess**: who is affected (a desk, risk, the end-of-day run), how badly, and since when. Say so in the incident channel early.
2. **Mitigate before you diagnose**: roll back the last deploy, fail over, or serve the last good snapshot *with a visible stale flag*. Never serve wrong numbers silently.
3. **Diagnose**: what changed? Deploys, market data, reference data, positions, load. Compare against yesterday's golden numbers. Use `git bisect` or replay the job against a fixed snapshot.
4. **Fix and verify** with the user who reported it ("your DV01 is back, please check the 10-year bucket").
5. **Blameless post-mortem**: timeline, root cause, why tests and alerts missed it, and actions (a new test, a new alert, a runbook entry).

Typical analytics incidents: a missing or stale curve, a holiday calendar error, a bad vol point creating a huge vega, a duplicated trade, a slow task holding up the end-of-day run, or a library upgrade that moved numbers by a small amount.

---

## 9. Mock interview: 15 questions with answers

**Q1. Delta of an at-the-money call, and why is it not 0.5?**
`Δ = N(d₁)`, `d₁ = (ln(S/K) + (r + ½σ²)T) / (σ√T)`. At the money (`S = K`), `d₁ = (r + ½σ²)√T / σ > 0`, so `Δ > 0.5`. With `r = 3%`, `σ = 20%`, `T = 1`: `d₁ = 0.25`, `Δ = 0.599`.

**Q2. Put-call parity, and a use for it in a risk system.**
`C − P = S − K·e^(−rT)` (no dividends). Use: a test, a check on market data (it detects bad quotes), and a way to get a put's Greeks from a call's: `Δ_put = Δ_call − 1`, same gamma and vega.

**Q3. Your bumped gamma is noisy. Why, and what do you do?**
Second differences divide by `h²`, so rounding (and Monte Carlo noise) is amplified. Use a larger relative bump (about 1%), the same random numbers for up and down, analytic or AAD gamma, or a smoothed payoff near the strike.

**Q4. How do you compute bucketed DV01?**
Bump one curve input (e.g. the 5-year swap quote) by 1 bp, *rebuild* the curve, reprice, repeat for each input. Check the sum against a parallel bump. Cost: one curve build and a full reprice per bucket, so cache per bucket and reprice only the trades that depend on that curve.

**Q5. Why is VaR not additive, and how do you aggregate it?**
VaR is a quantile, and the quantile of a sum is not the sum of quantiles (diversification). Store each book's P&L vector over the same scenarios, add the vectors, then take the quantile.

**Q6. Two runs of the end-of-day job give different numbers. Where do you look?**
Inputs first: snapshot IDs, position versions, reference data, library versions. Then non-determinism: unseeded random numbers, parallel floating-point sums in different orders (addition is not associative in floating point), dictionary/set ordering, time-dependent code ("today" read from the clock instead of the run date).

**Q7. Design an API for what-if scenarios.**
Request: `{portfolio selector, base snapshot ID, list of shocks (curve bp by tenor, vol points by surface, spot % by name), measures}`. Response: results keyed by scenario and aggregation level, plus the snapshot, position version and library version. Make requests idempotent and cacheable; run interactive requests on a reserved pool.

**Q8. How would you make a 2-hour end-of-day run take 20 minutes?**
Profile first. Then: parallelise by position batch, cache curve builds and vol surfaces per snapshot, vectorise vanilla pricing (NumPy), skip unchanged trades (incremental), move Monte Carlo exotics to their own pool, use AAD instead of many bumps, and fix stragglers by splitting big tasks.

**Q9. Solve `f(σ) = BS(σ) − price = 0` for implied volatility robustly.**
Newton (`σ ← σ − f/vega`) converges fast but fails when vega is tiny (deep in or out of the money). Use safeguarded Newton: keep a bracket `[lo, hi]` and fall back to bisection when a Newton step leaves it. Check the arbitrage bounds of the price first. See [numerical methods](../numerical-methods/README.md).

**Q10. Why use Cholesky to simulate correlated moves, and what if it fails?**
If `Σ = L·Lᵀ` and `z` is independent normals, `L·z` has covariance `Σ`. Cholesky fails if `Σ` is not positive definite, which is common with estimated or stitched matrices. Fix: clip negative eigenvalues and rescale to a unit diagonal (nearest correlation matrix). See [linear algebra](../linear-algebra/README.md).

**Q11. Expected number of coin tosses to see two heads in a row?**
`E = 6`. With states "no head yet" (`E₀`) and "one head" (`E₁`): `E₀ = 1 + ½E₁ + ½E₀`, `E₁ = 1 + ½·0 + ½E₀`, giving `E₀ = 6`.

**Q12. A trader says "my DV01 jumped overnight but I didn't trade". Possible causes?**
Curve or market data change (a new curve definition, a bad quote), a CTD switch on a futures hedge, trades rolling into a new bucket as time passes, an expiry or a fixing, reference data changes, a library release, or a booking amendment. Compare the inputs to yesterday's one by one.

**Q13. What does a receiver swap's DV01 sign tell you, and the formula?**
Receive fixed: PV = `N·(K·A − (1 − DF_n))`, where `A = Σ τᵢ·DFᵢ` is the annuity. Rates up, PV down, so DV01 < 0 under the convention "PV change for +1 bp". Numbers in the engine's test.

**Q14. Stream: maintain a book's total delta as trades and price updates arrive, at scale.**
Hold per-position Greeks in memory (a hash map by position ID). On a trade, add its contribution; on a price tick, reprice only positions on that underlying (a map from underlying to positions) and update the total by the difference. O(affected positions) per event, not O(book).

**Q15. How do you test a pricing library?**
Known identities (put-call parity, a par swap with PV 0, zero-vol limit equal to intrinsic value), limits (T → 0, σ → ∞), Monte Carlo vs closed form within a confidence interval, analytic vs bumped Greeks, golden-number regression tests on a fixed snapshot, and property-based tests (a call price rises with spot and falls with strike).

---

## 10. Behavioural round

Use **STAR**: Situation (one sentence), Task (your responsibility), Action (what *you* did, in detail; most of the time goes here), Result (a number if possible, plus what you learned). Two minutes per story.

Prepare six stories; most questions map onto one of them:

| Story | Likely questions |
|---|---|
| A production incident you handled | "Tell me about a time something broke", "working under pressure", on-call |
| Working with a demanding user (trader, risk manager) | "Difficult stakeholder", "explaining technical ideas to non-technical people" |
| A number that looked wrong and you traced it | "Attention to detail", "debugging", "ownership" |
| A performance or reliability improvement | "Biggest technical achievement", "impact" |
| A disagreement about design | "Conflict", "changing your mind" |
| A mistake you made | "Failure", "what would you do differently" (show humility and the fix) |

What trading-firm teams look for: ownership ("I followed it to the root cause"), humility and curiosity, collaborating closely with users, speed *with* correctness, and comfort being on call.

**"Why this role?"** Connect three things: you like being close to the business (traders and risk use your numbers every day), the mix of maths and engineering (pricing, sensitivities, distributed systems), and owning services in production.

---

## 11. Questions to ask them

- Which asset classes and products does the platform cover today, and which are next?
- How are Greeks produced: analytic, bumped, AAD? Who owns the pricing models: quants, or this team?
- How do you guarantee reproducibility of past numbers (snapshots, bitemporal storage)?
- What is the split between the service layer and the numerical code, and in which languages?
- What does an on-call week look like, and what was the last significant incident?
- How do risk managers and desks request new analytics, and how fast do they ship?
- What would make someone very successful in their first six months here?

---

## 12. Glossary

| Term | Meaning |
|---|---|
| AAD | Adjoint algorithmic differentiation: all sensitivities for a few times the cost of one price |
| As-of join | Attach to each record the latest record from another table at or before its time |
| BEAM | The Erlang virtual machine that Elixir runs on |
| Bitemporal | Storing both the business date of a value and when it became known |
| Bucketed DV01 | DV01 split by curve input (key rate), found by bumping each input separately |
| Bump-and-revalue | Computing a sensitivity by repricing with a slightly moved input |
| Canary | Releasing a new version to a small share of traffic first |
| Central difference | `(V(x+h) − V(x−h)) / 2h`; error proportional to h² |
| CI/CD | Continuous integration / delivery: automatic tests and deployments on every change |
| Container | A packaged program with its exact dependencies (Docker) |
| Cross gamma | Second derivative with respect to two different inputs, e.g. vanna (spot and vol) |
| Golden-number test | Regression test that compares outputs on a fixed input against stored values |
| GenServer | An Elixir/Erlang server process that holds state and handles messages one at a time |
| Kubernetes | System that runs and scales containers across many machines |
| Middle office | Team that owns official positions, P&L and P&L explain |
| Pod | The smallest unit Kubernetes runs: one or more containers |
| Post-mortem | Written review after an incident: timeline, root cause, actions |
| Snapshot | Frozen, versioned set of market data used for a calculation |
| STAR | Situation, Task, Action, Result: a structure for behavioural answers |
| Sticky strike / sticky delta | Whether implied vol follows the strike or moves with spot when spot moves |
| Supervisor | Elixir/Erlang process that restarts crashed child processes |
| Taylor estimate | Approximating P&L from Greeks instead of repricing |
| VaR | Value at risk: a loss level exceeded only with a small probability |
