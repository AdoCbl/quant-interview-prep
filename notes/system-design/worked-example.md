# System Design, Step by Step: A Real-Time Risk and P&L Service

One system design question worked from start to finish, slowly, with every idea explained when it
first appears. If you can explain this one design well, you can adapt it to most questions a
trading firm asks. The [main system design page](README.md) has the general framework, latency
numbers and six shorter designs; a glossary is at the end of this page.

**The question:** *"Design a system that gives traders and risk managers live risk (sensitivities
such as delta, vega and DV01) and P&L for all the firm's positions, plus what-if scenarios and an
end-of-day run."*

Contents:

1. [What a system design interview is testing](#1-what-a-system-design-interview-is-testing)
2. [Step 1: Clarify requirements](#2-step-1-clarify-requirements)
3. [Step 2: Estimate the scale](#3-step-2-estimate-the-scale)
4. [Step 3: Start with the simplest design that works](#4-step-3-start-with-the-simplest-design-that-works)
5. [Step 4: The full design](#5-step-4-the-full-design)
6. [Step 5: Follow four requests through the system](#6-step-5-follow-four-requests-through-the-system)
7. [Step 6: Deep dives](#7-step-6-deep-dives)
8. [Step 7: What breaks, and what happens then](#8-step-7-what-breaks-and-what-happens-then)
9. [Step 8: Monitoring and service targets](#9-step-8-monitoring-and-service-targets)
10. [Step 9: Trade-offs to say out loud](#10-step-9-trade-offs-to-say-out-loud)
11. [A tiny runnable prototype](#11-a-tiny-runnable-prototype)
12. [How to deliver it in 45 minutes](#12-how-to-deliver-it-in-45-minutes)
13. [Follow-up questions](#13-follow-up-questions)
14. [Glossary](#14-glossary)

---

## 1. What a system design interview is testing

There is no single right answer. The interviewer watches *how you get to* an answer:

- Do you find out what is actually needed before drawing boxes?
- Do you put rough numbers on the problem, and let them drive choices?
- Do you start simple and add complexity only for a reason you can name?
- Do you know what each component costs you (the trade-off)?
- Do you think about failures, correctness and the people who use it?

For a trading firm, add: **numbers must be correct, reproducible and explainable**. A fast risk
number that is wrong is worse than a slow one that is right.

---

## 2. Step 1: Clarify requirements

Spend about five minutes asking questions and writing the answers down. Split them into two kinds.

**Functional requirements** (what it does):

| Requirement | Detail you agree with the interviewer |
|---|---|
| Positions | Built from every trade, across all desks and books |
| Live risk | PV (present value), delta, gamma, vega, DV01 and bucketed DV01 per position, refreshed as markets move |
| Live P&L | Today's P&L per position, split into "from new trades" and "from market moves" |
| Aggregation | Totals up a hierarchy: position → book → desk → firm, and by other tags (underlying, currency, tenor) |
| What-if | "What if rates rise 25 bp and vol rises 2 points?" on any slice of the portfolio, answered in seconds |
| End of day (EOD) | Official risk, P&L and VaR (value at risk) at closing prices, finished before the next morning |
| History | Any past day's numbers, exactly as reported, available on request |

**Non-functional requirements** (how well it does it):

| Quality | Target to propose |
|---|---|
| Freshness | Vanilla products within 2 seconds of a price move; complex products within 1 minute |
| What-if latency | Under 5 seconds for a desk-sized portfolio |
| EOD | Done within a 2-hour window |
| Correctness | Reproducible: the same inputs always give the same numbers, and every number can be traced to its inputs |
| Availability | During trading hours, live risk must keep working when a machine fails |
| Audit | Every result records which trades, market data and code version produced it |

**Questions worth asking**: How many positions? Which products: mostly vanillas (closed-form
prices) or also exotics (Monte Carlo)? Who are the users, and how many? Is this replacing an
existing system?

---

## 3. Step 2: Estimate the scale

Rough numbers decide the design, so do the arithmetic out loud. Say each assumption.

| Quantity | Assumption | Result |
|---|---|---|
| Positions | 190,000 vanilla + 10,000 complex | 200,000 |
| Trades per day | 500,000, bursting to 2,000 a second | about 20 a second on average |
| Underlyings and curves | 5,000 | |
| Market data after merging updates | each underlying updates at most 10 times a second | at most 50,000 updates a second |
| Vanilla price time | 20 µs (microseconds) | `190,000 × 20 µs = 3.8 CPU-seconds` per full reprice |
| Complex price time | 50 ms (Monte Carlo) | `10,000 × 50 ms = 500 CPU-seconds` per full reprice |
| Greeks by bumping | about 20 bumped prices per position | vanilla `3.8 × 20 = 76` CPU-s; complex `500 × 20 = 10,000` CPU-s |
| EOD VaR | 250 historical scenarios, full revaluation for vanillas | `190,000 × 250 × 20 µs = 950` CPU-s |
| Result size per snapshot | 200,000 positions × 30 measures × 8 bytes | about 48 MB |
| Scenario P&L stored per day | 200,000 × 250 × 8 bytes | about 400 MB a day, about 100 GB a year |

What the numbers tell us:
1. **Vanillas are cheap; complex products dominate the cost** (10,000 of 10,076 CPU-seconds for Greeks). So treat them differently: their own worker pool, slower refresh, and faster methods (algorithmic differentiation, Greeks-based approximations).
2. **A full vanilla refresh in 2 seconds** needs `76 CPU-s / 2 s ≈ 40 cores`. Recomputing only what changed (section 7.2) cuts this a lot.
3. **Storage is small** by modern standards: one well-chosen database can hold years of results.
4. **Trades are slow compared with market data**, so position keeping is easy; market data volume is the thing to control.

---

## 4. Step 3: Start with the simplest design that works

Always describe the simplest version first; it shows you would not over-build.

```
 trades ─┐
         ├──► one program: positions + latest prices ──► price everything ──► print totals
 prices ─┘
```

One process holds all positions and the latest prices in memory and reprices everything in a
loop. That is perfectly fine for one desk with a few thousand vanilla positions. It breaks as we scale:

| Problem with the simple version | What we add, and why |
|---|---|
| One machine cannot reprice 200,000 positions fast enough | **Many stateless pricing workers** sharing the work |
| If the program crashes, the positions in memory are lost | A durable, ordered **trade log** that positions can be rebuilt from |
| Prices change while a run is in progress, so totals mix old and new prices | **Versioned market data snapshots** |
| Every tick triggers a full reprice | A **dependency index** to reprice only affected positions |
| Users ask for history and different groupings | A **results store** and a **query service** |
| A slow end-of-day run blocks interactive what-ifs | **Separate pools** with priorities |

Each row is a reason. Say the reason before you add the box.

---

## 5. Step 4: The full design

```
  Trading systems                     Exchanges / data vendors
        │ trades                             │ ticks
        ▼                                    ▼
  ┌──────────────┐                   ┌──────────────────┐
  │  Trade log   │ ordered, durable, │ Market data feed │ merges bursts: keep the
  │ (sequenced)  │ replayable        │  + conflation    │ latest price per instrument
  └──────┬───────┘                   └────────┬─────────┘
         ▼                                    ▼
  ┌──────────────┐                   ┌──────────────────┐
  │   Position   │                   │ Snapshot service │ freezes a consistent set of
  │   service    │                   │  (versioned)     │ prices, curves, vols: id = v123
  └──────┬───────┘                   └────────┬─────────┘
         │ positions + versions               │ snapshot ids
         └───────────────┬────────────────────┘
                         ▼
               ┌────────────────────┐    reference data (contracts,
               │  Risk scheduler    │◄── calendars, hierarchy)
               │ (dependency index, │
               │  splits into tasks)│
               └─────────┬──────────┘
            ┌────────────┼─────────────┐
            ▼            ▼             ▼
      ┌──────────┐ ┌──────────┐ ┌──────────────┐
      │ Live pool│ │What-if   │ │ Batch / EOD  │  stateless pricing workers,
      │ vanillas │ │pool      │ │ + complex    │  same pricing library,
      └────┬─────┘ └────┬─────┘ └──────┬───────┘  scaled on a cluster
           └────────────┼──────────────┘
                        ▼
               ┌────────────────────┐
               │   Results store    │  column store, keyed by
               │ (+ scenario P&L)   │  (snapshot, position, measure)
               └─────────┬──────────┘
                         ▼
               ┌────────────────────┐
               │ Aggregation + API  │──► dashboards (live push), what-if requests,
               └────────────────────┘    reports, other systems
```

What each box does, in one or two sentences:

| Component | Job | Key design choice |
|---|---|---|
| **Trade log** | Stores every trade event in order, durably, and lets anyone replay it from any point | Every event has a unique trade ID and a sequence number |
| **Position service** | Turns the trade stream into current positions per book | Idempotent: seeing the same trade twice changes nothing |
| **Market data feed + conflation** | Receives ticks and keeps only the latest per instrument when updates arrive faster than we can use them | Prevents a burst from creating a growing backlog |
| **Snapshot service** | Takes the current prices, curves and vol surfaces and freezes them under a version ID | Snapshots are never edited; a correction makes a new version |
| **Risk scheduler** | Decides *what* to compute: which positions, which snapshot, which measures, and splits that into tasks | Holds the dependency index: underlying → positions |
| **Pricing workers** | Price a batch of positions against a snapshot and return measures | **Stateless**: any worker can do any task; easy to add, remove or restart |
| **Results store** | Keeps every result with its inputs' versions | Columnar, partitioned by date; append-only |
| **Aggregation + API** | Sums measures up the hierarchy, serves queries and what-ifs, pushes live updates | Knows which measures can be summed (section 7.3) |
| **Reference data** | Contract details, holiday calendars, the book/desk hierarchy | Versioned too: a calendar fix must not silently change history |

---

## 6. Step 5: Follow four requests through the system

Walking one request through the boxes is the clearest way to show the design works.

**A. A new trade arrives (buy 100 ZN futures in the rates book).**
1. The trading system publishes the trade to the trade log with ID `T812` and sequence number 40,117.
2. The position service reads it, checks that it hasn't seen `T812` before and that 40,117 follows 40,116 (no gap), and updates the position `rates / ZN` by +100.
3. It tells the scheduler: "position `rates / ZN` changed".
4. The scheduler sends one small task: price that position against the latest snapshot.
5. A live-pool worker prices it and writes the result; the aggregator adjusts the rates book total by the difference; dashboards get the update within about a second.

**B. A price ticks (ES futures move).**
1. Ticks arrive at hundreds per second; conflation keeps the latest ES price.
2. Every 200 ms the snapshot service publishes a new version, say v8,431, containing the ES change.
3. The scheduler asks the dependency index "which positions depend on ES?" and gets, say, 1,200 positions out of 200,000.
4. Only those 1,200 are repriced; everyone else's results are reused from v8,430.
5. Totals are recomputed as old total − old values + new values.

**C. A risk manager runs a what-if ("rates +25 bp, vol +2 points, rates desk").**
1. The API receives `{portfolio: "desk=rates", base_snapshot: v8,431, shocks: [...], measures: [pv, dv01]}`.
2. The scheduler builds a shocked snapshot (a new version derived from v8,431) and splits the desk's 30,000 positions into batches of 500.
3. Tasks go to the **what-if pool**, which is reserved so an EOD run can't slow it down.
4. Results come back, are aggregated, and are returned with the snapshot and code versions used. The same request later returns the cached answer.

**D. The end-of-day run.**
1. At the close, the snapshot service takes the official closing prices as snapshot `EOD-2026-11-27`.
2. Positions are frozen as of the cut-off sequence number.
3. The batch pool prices every position under the EOD snapshot and 250 historical scenarios.
4. Results and scenario P&L vectors are written to the results store; VaR is computed from the vectors; reports are produced.
5. Every number records: the snapshot ID, the trade sequence cut-off, the pricing library version.

---

## 7. Step 6: Deep dives

Interviewers usually pick one or two of these. Choose the one you know best if they let you.

### 7.1 Consistent snapshots and reproducibility

- **Problem:** if each worker reads "the latest price" whenever it starts, a run mixes prices from different moments, and nobody can reproduce it.
- **Solution:** every computation names a snapshot version. Workers load that exact version (and cache it locally, since snapshots never change). The results store keys every result by snapshot version, trade sequence number and code version.
- **Why it matters:** a trader asking "why did my DV01 change?" can compare two runs input by input. Regulators and auditors can rerun any past day.
- **Corrections:** a wrong price is fixed by a *new* snapshot version, never by editing an old one. Reports can show "as reported then" and "as corrected now".

### 7.2 Recompute only what changed

- **Dependency index:** a map from each market input (an underlying, a curve, a vol surface) to the positions that use it. It is built when positions change.
- When a snapshot changes a few inputs, reprice only the dependent positions. In the prototype below, an ES tick reprices 1 of 3 positions.
- **Totals update by difference:** `new total = old total − old value + new value`, so aggregation is O(changed positions), not O(all positions).
- Curves are shared by thousands of positions, so a curve change still triggers a big reprice; that is when **Greeks-based estimates** help: `ΔPV ≈ delta·ΔS + ½·gamma·ΔS²` immediately, followed by full repricing a moment later.

### 7.3 Aggregation: what can be added and what can't

- **Additive measures** (PV, P&L, delta, vega, DV01) can be summed up the hierarchy: the desk total is the sum of its books.
- **VaR and Expected Shortfall are not additive**: they are a quantile (or tail average) of a P&L distribution, and positions partly cancel each other. The firm's VaR is usually *less* than the sum of desks' VaRs (diversification).
- **So store the scenario P&L vector** for each position (one number per scenario). To get the VaR of any grouping, add the vectors, then take the quantile. In the prototype: rates VaR 1,022 + equity VaR 2,751 = 3,773, but the combined VaR is 2,411.
- Storage cost: 250 numbers per position per day (about 400 MB a day here), which is affordable.

### 7.4 Scaling the computation

- **Unit of work:** a task = (a batch of positions, one snapshot, a list of measures). Batches of a few hundred positions make each task about 10–100 ms: big enough to keep overhead small, small enough to spread evenly.
- **Stateless workers** pull tasks from a queue. Add workers when the queue grows (autoscaling on a cluster such as Kubernetes); remove them when it shrinks.
- **Separate pools** for live risk, what-ifs and batch, with priorities, so an urgent request never waits behind the EOD run.
- **Stragglers** (one slow task delays the whole run): split large tasks, set timeouts, and re-send late tasks to another worker. This is safe because tasks are idempotent (writing the same result twice is harmless).
- **Data locality:** each worker caches the snapshots it has loaded; send a worker more tasks on the snapshot it already has.

### 7.5 Caching

- Cache key = `(instrument terms, snapshot version, scenario, measure, code version)`. Because snapshots never change, a cached result is never stale; a new snapshot simply means a new key. No invalidation logic is needed, which is the main benefit of versioning.
- Evict old snapshots' results from memory after a while; they remain in the results store.

### 7.6 Exactly-once effects from at-least-once delivery

- Networks and retries mean a message can arrive twice (at-least-once delivery). True exactly-once delivery is very hard.
- So make processing **idempotent**: every trade has a unique ID, and the position service ignores IDs it has seen. Every result write is keyed, so rewriting it is harmless.
- **Sequence numbers** detect gaps: if trade 40,118 arrives after 40,116, ask the log to replay from 40,117 before trusting the position.

### 7.7 Back-pressure and conflation

- If ticks arrive faster than we can reprice, a queue would grow without limit, and risk would fall further and further behind.
- **Conflation**: keep only the latest price per instrument, and take snapshots on a timer (e.g. every 200 ms). Risk stays at most one interval behind, whatever the tick rate.
- **Back-pressure**: when the live queue is too long, the scheduler skips intermediate snapshots and jumps to the newest.

### 7.8 Storage

- **Hot**: the latest results in memory in the aggregation service, for dashboards.
- **Warm**: a column store (kdb+, ClickHouse) partitioned by date, for "show me vega by desk for last month".
- **Cold**: older days in Parquet files on object storage.
- Store results **bitemporally**: the business date the number is for, and when it was computed. That supports both "as reported" and "as corrected".

---

## 8. Step 7: What breaks, and what happens then

| Failure | Effect | Response |
|---|---|---|
| A pricing worker crashes | Its tasks never finish | Task times out and is retried on another worker; idempotent writes make it safe |
| The position service crashes | No new trades applied | Restart and replay the trade log from the last checkpointed sequence number |
| Market data feed stops | Risk silently goes stale | Detect: "no update for X seconds" alert; mark results **stale** on dashboards; never present old numbers as live |
| A bad price (e.g. 10× too high) | Wild risk and P&L | Sanity checks before snapshotting (moves beyond limits, crossed markets); hold the instrument at the last good price with a visible flag |
| A trade is missing | Wrong positions | Gap detection on sequence numbers; daily reconciliation against the clearing broker |
| EOD run is late | Morning reports missing | Monitor progress against the deadline; restart failed parts only; keep spare capacity |
| A new pricing library release changes numbers | Unexplained P&L | Run both versions side by side on the same snapshot before release ("golden-number" tests) |
| The results store is down | No history, no queries | Live risk keeps running from memory; writes are buffered in the log and replayed |

---

## 9. Step 8: Monitoring and service targets

- **Service level objectives (SLOs)**, targets you promise users: "99% of vanilla risk updates within 2 s of a tick", "EOD finished by 02:00 on 99.5% of days", "what-ifs under 5 s for 95% of requests".
- **Metrics** to graph and alert on: queue depth per pool, task latency percentiles (p50, p99), snapshot age, trade sequence lag, failed tasks per product, stale-instrument count.
- **Logs and traces** carry the snapshot ID and request ID, so one bad number can be followed through every service.
- **Business checks**: P&L explain unexplained above a limit, risk jumps beyond X% day on day, positions not reconciled.

---

## 10. Step 9: Trade-offs to say out loud

| Choice | What you gain | What you give up |
|---|---|---|
| Versioned, immutable snapshots | Reproducibility, simple caching, safe parallelism | Storage, and a small delay (one snapshot interval) |
| Conflation | Bounded lag under bursts | Some intermediate prices are never priced |
| Stateless workers | Easy scaling and recovery | Each worker must load snapshots; needs a cache |
| Incremental recompute | Much less compute | More complex bookkeeping (dependency index) |
| Storing scenario P&L vectors | VaR for any grouping | More storage (~100 GB a year here) |
| Greeks-based estimates for complex products | Instant approximate risk | Inaccurate for big moves; must be followed by full repricing |
| Separate worker pools | Predictable latency for urgent requests | Some idle capacity |

---

## 11. A tiny runnable prototype

All the core ideas fit in one small program: idempotent trades with gap detection, versioned
snapshots, a dependency index for incremental repricing, a cache keyed by snapshot version, and
VaR from summed scenario vectors. Real systems split these pieces across services; the logic is the same.

```python
"""A tiny, single-process version of the risk service's core ideas.

Real systems split these classes across services and machines; the logic stays the same:
- events carry sequence numbers and IDs, so duplicates and gaps are detected (idempotency);
- market data is frozen into versioned snapshots, so results are reproducible;
- a dependency index means a price tick reprices only the positions that depend on it;
- additive risk (PV, delta) is summed up the hierarchy; VaR is NOT, so we keep P&L vectors.
"""

from collections import defaultdict
from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class Trade:
    trade_id: str
    seq: int                # position in the trade stream
    book: str
    underlying: str
    qty: float              # linear instrument: value = qty * price


@dataclass(frozen=True)
class Snapshot:
    version: int
    prices: dict[str, float]


@dataclass
class RiskService:
    positions: dict[tuple[str, str], float] = field(default_factory=lambda: defaultdict(float))
    seen_trades: set[str] = field(default_factory=set)
    last_seq: int = 0
    by_underlying: dict[str, set[tuple[str, str]]] = field(default_factory=lambda: defaultdict(set))
    snapshots: list[Snapshot] = field(default_factory=list)
    cache: dict[tuple[int, str, str], float] = field(default_factory=dict)
    reprices: int = 0

    # ---- ingestion ---------------------------------------------------------------
    def on_trade(self, t: Trade) -> str:
        if t.trade_id in self.seen_trades:
            return f"dup {t.trade_id} ignored"          # at-least-once delivery + idempotency
        gap = t.seq != self.last_seq + 1
        self.seen_trades.add(t.trade_id)
        self.last_seq = max(self.last_seq, t.seq)
        key = (t.book, t.underlying)
        self.positions[key] += t.qty
        self.by_underlying[t.underlying].add(key)
        return f"booked {t.trade_id}" + (" (GAP: request replay)" if gap else "")

    def on_market_data(self, prices: dict[str, float]) -> Snapshot:
        base = self.snapshots[-1].prices if self.snapshots else {}
        snap = Snapshot(len(self.snapshots) + 1, {**base, **prices})   # new version, never edited
        self.snapshots.append(snap)
        return snap

    # ---- pricing -----------------------------------------------------------------
    def pv(self, snap: Snapshot, key: tuple[str, str]) -> float:
        ck = (snap.version, *key)
        if ck not in self.cache:                       # cache keyed by snapshot version
            self.reprices += 1
            self.cache[ck] = self.positions[key] * snap.prices[key[1]]
        return self.cache[ck]

    def book_pv(self, snap: Snapshot) -> dict[str, float]:
        out: dict[str, float] = defaultdict(float)
        for key in self.positions:
            out[key[0]] += self.pv(snap, key)          # additive: just sum
        return dict(out)

    def incremental(self, old: Snapshot, new: Snapshot) -> dict[str, float]:
        """Reprice only positions whose underlying changed; reuse cached values for the rest."""
        changed = {u for u, p in new.prices.items() if old.prices.get(u) != p}
        affected = set().union(*(self.by_underlying[u] for u in changed)) if changed else set()
        for key in self.positions:
            if key not in affected:                    # unchanged inputs -> reuse old value
                self.cache[(new.version, *key)] = self.pv(old, key)
        return self.book_pv(new)

    # ---- non-additive risk -------------------------------------------------------
    def var_99(self, snap: Snapshot, shocks: np.ndarray, books: set[str]) -> float:
        """Historical-style VaR: P&L per scenario, summed across books, then the 1% quantile."""
        names = sorted(snap.prices)
        pnl = np.zeros(len(shocks))
        for (book, und), qty in self.positions.items():
            if book in books:
                pnl += qty * snap.prices[und] * shocks[:, names.index(und)]
        return -np.quantile(pnl, 0.01)


svc = RiskService()
for t in [Trade("T1", 1, "rates", "ZN", 1000), Trade("T2", 2, "rates", "SR3", -400),
          Trade("T2", 2, "rates", "SR3", -400),                     # duplicate delivery
          Trade("T4", 4, "equity", "ES", 20)]:                      # seq 3 missing
    print(svc.on_trade(t))

s1 = svc.on_market_data({"ZN": 110.5, "SR3": 96.2, "ES": 5000.0})
print("v1 book PV:", {k: round(v) for k, v in svc.book_pv(s1).items()}, " reprices:", svc.reprices)

s2 = svc.on_market_data({"ES": 5010.0})                             # only ES ticks
before = svc.reprices
print("v2 book PV:", {k: round(v) for k, v in svc.incremental(s1, s2).items()},
      " new reprices:", svc.reprices - before)
print("v1 still reproducible:", {k: round(v) for k, v in svc.book_pv(s1).items()})

# 1,000 daily return scenarios for (ES, SR3, ZN), sorted by name. Stocks and bonds are
# negatively correlated here, so the two books partly offset each other.
vol = np.array([0.012, 0.0005, 0.004])
corr = np.array([[1.0, -0.2, -0.4],
                 [-0.2, 1.0, 0.6],
                 [-0.4, 0.6, 1.0]])
rng = np.random.default_rng(0)
shocks = rng.multivariate_normal(np.zeros(3), corr * np.outer(vol, vol), size=1000)
v_r, v_e = svc.var_99(s2, shocks, {"rates"}), svc.var_99(s2, shocks, {"equity"})
v_all = svc.var_99(s2, shocks, {"rates", "equity"})
print(f"VaR rates {v_r:,.0f} + equity {v_e:,.0f} = {v_r + v_e:,.0f}, but firm VaR = {v_all:,.0f}")
```

Output:

```text
booked T1
booked T2
dup T2 ignored
booked T4 (GAP: request replay)
v1 book PV: {'rates': 72020, 'equity': 100000}  reprices: 3
v2 book PV: {'rates': 72020, 'equity': 100200}  new reprices: 1
v1 still reproducible: {'rates': 72020, 'equity': 100000}
VaR rates 1,022 + equity 2,751 = 3,773, but firm VaR = 2,411
```

What the output shows, line by line:
1. The duplicate `T2` is ignored, and the missing sequence number 3 is noticed.
2. Snapshot v1 needs 3 prices (one per position).
3. Snapshot v2 only changed ES, so only **1** position is repriced; the other results are reused.
4. Snapshot v1 is still exactly reproducible after v2 exists.
5. VaR does not add up: 1,022 + 2,751 = 3,773 for the two books separately, but 2,411 together.

---

## 12. How to deliver it in 45 minutes

| Minutes | Say and draw |
|---|---|
| 0–5 | Requirements: functional list, then the numbers (freshness, what-if latency, EOD window, reproducibility) |
| 5–9 | Estimates: positions, price times, CPU-seconds, storage. Point out that complex products dominate |
| 9–12 | The single-process version, and the list of reasons it breaks |
| 12–22 | The full diagram, box by box, with one sentence each |
| 22–27 | Walk a trade and a price tick through it |
| 27–40 | Deep dive: snapshots and reproducibility, or incremental recompute, or VaR aggregation |
| 40–45 | Failures, monitoring, trade-offs, and what you would build first |

**What to build first** (a good closing answer): trade log + position service + snapshot service
+ a single pricing pool + results store, for vanillas only. Then add incremental repricing, the
what-if pool, complex products and VaR in that order, because each step is useful on its own.

---

## 13. Follow-up questions

1. **How would you handle 10× more positions?** Mostly more workers; the scheduler and aggregator are partitioned by desk; batch sizes stay the same. The dependency index and results store partition by desk or underlying.
2. **How do you make sure the EOD numbers match what traders saw at the close?** Both use the same pricing library version and the same official closing snapshot; the live system can switch to the EOD snapshot at the cut-off.
3. **What if two users run the same what-if?** The request key (portfolio selector, base snapshot, shocks, measures, code version) hits the cache.
4. **How do you add a new product type?** Add a pricer to the shared library with tests (known identities and golden numbers); the scheduler and workers need no change because they only call `price(position, snapshot)`.
5. **How would you explain a P&L number to a trader?** P&L explain: split today's P&L into new trades, delta × move, ½ gamma × move², vega × vol change, theta, and an unexplained remainder, using the stored Greeks and both snapshots.
6. **Push or pull for dashboards?** Push changed totals over a streaming connection (e.g. WebSocket) at most a few times a second; pull for history and drill-down queries.
7. **Why not just use a big database and SQL for everything?** Pricing is computation, not querying; it needs parallel workers and in-memory market data. The database is for results and history.

---

## 14. Glossary

| Term | Meaning |
|---|---|
| Aggregation | Combining position-level numbers into totals for a book, desk or firm |
| At-least-once delivery | A message is guaranteed to arrive, but may arrive more than once |
| Autoscaling | Adding or removing workers automatically as the workload changes |
| Back-pressure | Slowing down or skipping input when the system can't keep up |
| Bitemporal | Storing both the date a value is for and when it was recorded |
| Column store | A database that stores each column together; fast for sums over many rows |
| Conflation | Keeping only the latest update per item when updates arrive faster than they can be used |
| Dependency index | A map from each market input to the positions that depend on it |
| DV01 | Change in value for a one-basis-point (0.01%) move in rates |
| End of day (EOD) | The official daily run at closing prices |
| Idempotent | Doing an operation twice has the same effect as doing it once |
| Partitioning | Splitting data or work across machines by a key (desk, underlying) |
| Present value (PV) | Today's value of a position |
| Reproducible | The same inputs always give the same outputs, so results can be rechecked |
| Sequence number | A counter on each message, used to detect gaps and order events |
| Service level objective (SLO) | A measurable target, e.g. "99% of updates within 2 seconds" |
| Snapshot | A frozen, versioned set of market data used for a calculation |
| Stateless worker | A worker that keeps nothing between tasks, so any worker can do any task |
| Straggler | A slow task that holds up a whole run |
| Value at risk (VaR) | A loss level exceeded only with a small probability, e.g. 1% of days |
| What-if | A calculation under user-chosen market shocks |
