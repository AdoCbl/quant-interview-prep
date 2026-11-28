# System Design for Quant Developer Interviews

System design rounds are open-ended: "Design a risk service", "Design a market data system", "Design a matching engine". There's no single right answer. Interviewers watch *how you think*:
- Do you ask about requirements?
- Do you estimate the scale?
- Do you pick sensible parts?
- Do you know the trade-offs?
- Do you plan for failure?

This page has four parts:
- **Part 1:** a framework you can use for any question.
- **Part 2:** the building blocks and the numbers to know.
- **Part 3:** six worked designs for trading firms (risk and analytics platforms, electronic swaps trading, market data, matching, backtesting).
- **Part 4:** common follow-up questions.

New to system design? Start with the slower, fully worked [step-by-step example](worked-example.md) (a real-time risk and P&L service, with a runnable prototype).

Abbreviations are spelled out on first use, and a glossary is at the end. A tested order book is in [`src/quantprep/systems/order_book.py`](../../src/quantprep/systems/order_book.py).

---

## Part 1 — A framework for any question (about 45 minutes)

| Step | Time | What to do | Example phrases |
|---|---|---|---|
| 1. Clarify requirements | 5 min | **What** it must do (features) and **how well** (speed, volume, correctness, uptime). Ask who the users are. | "Is this for live trading or end-of-day reporting?" "What latency is acceptable?" |
| 2. Estimate scale | 3 min | Rough numbers: events per second, data size per day, number of users, result sizes | "50,000 positions × 200 scenarios = 10 million prices per run" |
| 3. Define the interface and data | 5 min | The main requests and responses; the main records and their keys | `run_scenarios(portfolio_id, scenario_set, market_data_version)` |
| 4. Draw the high-level design | 10 min | Boxes and arrows from input to output; say what each box does | "Feed handler → normaliser → in-memory cache → pricer → publisher" |
| 5. Go deep on the hard part | 15 min | Usually where the volume, latency or correctness risk is. Pick it yourself, or follow the interviewer | "The hard part is consistent market data across 10,000 workers…" |
| 6. Failures and bottlenecks | 5 min | What breaks first as volume grows? What if a machine, network or data source dies? | "If the price feed goes stale, we pull our quotes automatically" |
| 7. Trade-offs and next steps | 2 min | What you chose, what you gave up, and how it would evolve | "I chose simplicity over the last millisecond; we can add X later" |

**Habits that score well**
- **Say your assumptions out loud** and write the key numbers down.
- **Start simple**, then improve: "A single process would work up to X; beyond that we split by Y."
- **Name the trade-off** whenever you choose something, e.g. "Caching makes reads fast, but results can be stale. We tag each result with its data version."
- **Use finance language correctly**: positions, trades, books, desks, P&L (profit and loss), risk sensitivities, market data snapshots, end of day.
- **Correctness beats speed** for risk and money. Say how you keep results reproducible and auditable.

---

## Part 2 — Building blocks and numbers

### Latency numbers to know (approximate, order of magnitude)
| Operation | Time |
|---|---|
| CPU cache read (closest level) | ~1 nanosecond (ns) |
| Main memory (RAM) read | ~100 ns |
| Pass a message between threads through shared memory | ~100 ns – 1 microsecond (µs) |
| Solid-state disk random read | ~20–100 µs |
| Network round trip inside one data centre | ~100–500 µs |
| Chicago ↔ New York one way (microwave links / fibre) | ~4 ms / ~7 ms |
| New York ↔ London round trip | ~70 ms |
| Typical web service request | 10–100 milliseconds (ms) |

**Ways to look at the table**:
- Memory is about 100× slower than the CPU cache. Keeping data compact and in order (arrays, not pointer-heavy structures) is the biggest single-machine speed lever.
- Network hops dominate everything else, so fast trading systems put the computers next to the exchange ("co-location").
- **The speed tier sets the design**:
  - *Ultra-low latency* (nanoseconds to microseconds): exchange market making in futures and equities. Specialised C++, special network cards, sometimes FPGAs (programmable chips).
  - *Low latency* (sub-millisecond to milliseconds): electronic rates and credit trading, request-for-quote responses.
  - *Interactive* (100 ms to seconds): risk dashboards, what-if tools.
  - *Batch* (minutes to hours): end-of-day risk, regulatory reports, research backtests.

### Common building blocks
| Block | What it does | Examples | Trade-off to mention |
|---|---|---|---|
| **Message queue / log** | Producers append events; consumers read at their own pace; events can be replayed | Kafka, Solace, Aeron, kdb+ tickerplant | Slightly more latency, in return for decoupling, buffering and replay |
| **Cache** | Keeps recent results in memory | Redis, an in-process dictionary | Fast, but can be stale. Decide how entries expire or are invalidated |
| **Relational database** | Tables with transactions; strong consistency | PostgreSQL, Oracle, SQL Server | Correct and familiar; harder to scale writes |
| **Time-series / column store** | Fast scans and aggregations over many rows of few columns | kdb+, ClickHouse, Parquet files | Superb for tick data and analytics; weaker for single-row updates |
| **Object storage** | Cheap storage for huge files | S3, files on a network drive | Cheap and durable; slower access |
| **Compute grid / cluster** | Many workers process independent tasks | Kubernetes, an in-house grid, Ray, Spark | Scales out; the costs are coordination, data movement and stragglers |
| **Load balancer / gateway** | Spreads requests and routes queries to the right service | NGINX, a kdb+ gateway | Single entry point; must not become a bottleneck |

### Key concepts
- **Scaling up vs scaling out**: a bigger machine is simple but has a limit. More machines have no hard limit but need data split across them ("partitioning" or "sharding"), for example by desk, instrument or portfolio.
- **Stateless vs stateful services**:
  - Stateless workers (no memory between requests) are easy to add, remove and restart.
  - Keep state in a database, a log, or a few carefully replicated services.
- **Replication and failover**: keep copies of state on several machines. If the main copy (the "primary") fails, a standby takes over. Ask "who decides that the primary is dead?", to avoid two primaries at once ("split brain").
- **Delivery guarantees for messages**:
  - *At most once*: may lose messages.
  - *At least once*: may duplicate messages.
  - *Exactly once*: hard to achieve. Usually you get it with at-least-once delivery plus **idempotent** handling, where processing a message twice has the same effect as once. Example: every trade carries a unique ID, and duplicates are ignored.
- **Sequence numbers**: number every message. A receiver can then detect gaps (lost messages), reorder, and recover by replaying from the last number it saw.
- **Event sourcing**: store the list of events (orders, trades, market data), not just the current state. State can then be rebuilt, audited and replayed. This is very common in trading, and helps reproduce bugs and answer regulators.
- **Consistency vs availability**: when the network splits, a system must choose to stop accepting updates (stay consistent) or keep going with possibly conflicting data (stay available). Money and positions usually choose consistency.
- **Back-pressure**: when consumers are slower than producers, slow the producers down or drop or merge updates. For market data, keep only the latest price per instrument ("conflation") rather than queueing every tick.
- **Observability**:
  - **Metrics** (rates, latency percentiles such as p99, the time 99% of requests beat).
  - **Logs**.
  - **Traces** (one request followed across services).
  - **Alerts** tied to targets: "99.9% of risk runs finish within 5 minutes".
  - Many quant developer roles include on-call support, so talk about this.

---

## Part 3 — Worked designs

### Design A: Risk and scenario analytics service (analytics / middle office)
**Prompt**: "Traders and risk managers need option and rate sensitivities for all positions, plus what-if scenarios such as 'rates up 50 basis points, volatility up 2 points', for any time horizon."

**1. Requirements**
- **Functional**:
  - Compute present value and sensitivities (delta, gamma, vega, DV01, the value change for a one-basis-point rate move) per position.
  - Aggregate up the hierarchy (trade → book → desk → firm).
  - Run user-defined scenario grids.
  - Serve live updates intraday and a full run at end of day.
- **Non-functional**:
  - Interactive what-ifs within seconds.
  - The end-of-day run finishes within its time window.
  - Results are **reproducible**: the same inputs give the same numbers.
  - Results are auditable.
- **Questions to ask**: how many positions and instruments? How complex are the products (closed-form options vs Monte Carlo exotics)? How fresh must live risk be (seconds or minutes)?

**2. Estimate**
- Say 100,000 positions, 20 risk measures, and a scenario grid of 10 rate shifts × 10 volatility shifts = 100 scenarios. That's 10 million revaluations per full grid.
- At ~50 µs per vanilla price, that is 500 CPU-seconds: about 5 seconds on 100 cores.
- Exotics priced by Monte Carlo can be 1,000× slower and dominate, so they need special treatment (see the deep dive).

**3. High-level design**
```
 Trades / positions ──► Position service ──┐
                                           ├──► Job planner ──► Task queue ──► Pricing workers (scalable, stateless)
 Market data ──► Snapshot service ─────────┘                                         │
 (curves, vol surfaces, prices;                                                       ▼
  each snapshot has a version ID)                                      Results store (column store)
                                                                                      │
 Users / dashboards ◄── Query and aggregation API ◄──────────────────────────────────┘
```
- **Snapshot service**: freezes a consistent set of market data (all curves and volatility surfaces as of one moment) and gives it an ID.
  - Every result records the snapshot ID, the position version and the pricing library version → reproducible and auditable.
- **Job planner**: turns a request (portfolio × scenarios × measures) into independent tasks, e.g. one task per (batch of instruments, scenario).
  - Pricing is "embarrassingly parallel": tasks don't depend on each other.
- **Pricing workers**: stateless and running the shared pricing library. They scale out on Kubernetes (a system that runs and scales containerised services), adding workers when the queue grows.
  - Each worker caches the market data snapshots it has loaded.
- **Results store**: a column store keyed by (snapshot, scenario, position, measure). It is fast for "sum vega by desk across scenarios".

**4. Deep dives the interviewer may pick**
- **Aggregation**: present value, delta and DV01 are **additive** and can be summed up the hierarchy. Value-at-risk (VaR, a loss level exceeded only with small probability) and expected shortfall are **not additive**: you must keep the per-scenario profit and loss vectors and aggregate *those*, then take the quantile.
- **Incremental updates**: when one trade arrives intraday, reprice only that position and adjust the totals. Don't recompute the whole book. When market data ticks, reprice only positions that depend on the changed curve, using a dependency map from curve to instruments.
- **Caching**: key results by (instrument, snapshot ID, scenario, library version). Identical requests are then free, and invalidation is automatic: a new snapshot means a new key.
- **Expensive products**: run Monte Carlo exotics on their own pool, reuse random numbers across scenarios (lower noise in differences), and use adjoint algorithmic differentiation (AAD) to get all sensitivities for about the cost of a few prices. Alternatively, approximate scenarios with a Taylor expansion, ΔV ≈ delta·Δx + ½·gamma·Δx², and only fully reprice large shocks.
- **Stragglers**: one slow task delays the whole job. Split big tasks, set timeouts, and retry on another worker. Tasks must be idempotent, so a retry can't double-count.
- **What-if vs batch**: interactive what-ifs go to a reserved, high-priority worker pool, so a big end-of-day job can't starve them.

**5. Failures**
- A worker dies: its task times out and is retried.
- Market data is missing: refuse to run, or use the last good snapshot *with a visible flag*. Never silently mix.
- A bad price: sanity checks such as an option price outside its arbitrage bounds, or sensitivity changes over X% since yesterday, raise alerts.
- **Observability**: job duration, queue depth, error rate per product, and freshness of the live risk.

---

### Design B: Electronic market-making system for interest rate swaps
**Prompt**: "Design a system that continuously quotes USD interest rate swaps to clients, responds to requests for quotes, and manages the resulting risk."

**1. Requirements**
- **Functional**:
  - Compute a fair mid-price for each swap from the live yield curve.
  - Stream two-way prices (a bid and an offer) to trading platforms.
  - Answer requests for quote (RFQs, where a client asks a few dealers for a price and picks the best) within the platform's time limit.
  - Adjust prices for inventory and client.
  - Hedge the resulting risk.
  - Enforce risk limits.
- **Non-functional**:
  - Low latency: milliseconds, not nanoseconds; rates e-trading is fast but not exchange high-frequency trading.
  - Must never quote on **stale** or wrong prices.
  - Every decision is logged for later analysis and compliance.

**2. High-level design**
```
 Futures / Treasury / swap market data ──► Feed handlers ──► Curve builder (rebuilds the swap curve on every relevant tick)
                                                                    │ fair mid by tenor
                                                                    ▼
 Position keeper ──(inventory)──► Quote engine: mid + spread (by size, client tier, volatility) + skew (by inventory)
                                                                    │
                                                                    ▼
                                   Pre-trade risk checks (limits, price sanity, kill switch)
                                                                    │
                                     ┌──────────────────────────────┴───────────────┐
                                     ▼                                              ▼
                     Venue gateways (streaming prices, RFQ replies)        Auto-hedger (trades futures/Treasuries
                                     │ fills                                to cut risk past a threshold)
                                     ▼
                     Trade capture ──► Position keeper ──► Risk and P&L, markout analytics (kdb+)
```

**3. Key points to discuss**
- **Curve builder**: fits the curve from the most liquid instruments (futures, Treasuries, benchmark swaps). It must be fast, so rebuild incrementally, or update risk-weighted mids with a sensitivity-based approximation between full rebuilds.
- **Quote engine**:
  - price = mid ± (half-spread) − (skew × inventory).
  - When the desk is long risk, shade both prices to attract sellers less and buyers more.
  - The spread widens with volatility, size and client "toxicity", meaning how often that client's trades are followed by prices moving against us. This is measured by **markouts**: P&L at 1 s, 10 s and 60 s after each trade.
- **Safety first**:
  - Pull all quotes automatically if market data is stale (no update for X ms), if the curve fit fails, or on a manual **kill switch**.
  - Enforce per-client and global limits on size, risk, P&L loss and message rate.
- **Hedging**: decide hedge timing and instrument. Hedging immediately is costly; waiting adds risk. Many desks net client flows first, since one client's buy offsets another's sell.
- **Determinism and replay**: record every input event with timestamps. The same event log must reproduce the same quotes, which is essential for debugging and for backtesting quote logic.
- **Data**: ticks, quotes, RFQs and fills go into kdb+ for research: hit rates (the share of RFQs won), markouts, and spread optimisation. Research ideas then become parameters in the live engine (the job's "research → deployment → monitoring" loop).

---

### Design C: Market data feed handler
**Prompt**: "Receive an exchange's market data and deliver a clean order book to internal trading programs."

- **Input**: exchanges usually publish over **UDP multicast** (one sender to many receivers, with no delivery guarantee). They often use two identical feeds, called **A and B lines**, on different networks.
- **Steps**:
  1. **Arbitrate A/B**: take each sequence number from whichever line delivers it first, and drop the duplicate.
  2. **Detect gaps**: a missing sequence number means lost data. Request a retransmission, or rebuild from a **snapshot** feed and replay updates after it. Mark the book "stale" until it's recovered.
  3. **Decode** the exchange's binary format (e.g. SBE or ITCH) into internal events.
  4. **Build the book**: apply add, modify and delete messages to an order book (see Design E).
  5. **Publish** to internal consumers:
     - On the same machine, through **shared memory ring buffers** (a fixed-size circular queue; see [`cpp/src/ring_buffer.hpp`](../../cpp/src/ring_buffer.hpp)).
     - Across machines, through internal multicast or a messaging layer.
- **Latency tricks**:
  - Pin threads to CPU cores.
  - Avoid memory allocation and locks on the hot path.
  - Use **kernel bypass** networking, where the program reads the network card directly without going through the operating system.
  - Pre-allocate everything.
  - Process each message to completion in one thread.
- **Slow consumers**: never let one slow program block the feed. Give each consumer its own buffer, and *conflate* (send only the latest book) if it falls behind.

---

### Design D: Tick data platform (kdb+ "tick" architecture)
Know this one for any role that uses kdb+:
```
 Feed handlers ──► Tickerplant ──► Real-time database (today's data, in memory)
                     │   └──────► Real-time subscribers (e.g. live analytics, VWAP calculators)
                     ▼
                  Log file on disk (replayed after a crash)
                                         │ at end of day: save, then clear memory
                                         ▼
                          Historical database (on disk, split into one folder per date)
 Users ──► Gateway ──► routes each query to the real-time and/or historical database, then merges the results
```
- **Tickerplant**: receives every update, writes it to a log file, and publishes it to subscribers. It doesn't store data itself.
- **Real-time database**: holds today's data in memory for fast queries.
- **Historical database**: past days, partitioned by date and stored by column, so "one column for one day" reads only what is needed.
- **Recovery**: after a crash, the real-time database replays the tickerplant's log.
- **Queries**: as-of joins (`aj`, the latest quote at each trade's time), time buckets (`xbar`), and window joins (`wj`).

---

### Design E: Matching engine (an exchange's core)
**Prompt**: "Design the engine that matches buy and sell orders."

- **Rules**: price-time priority. The best price trades first; at equal prices, the earliest order trades first.
- **Data structures** (implemented and tested in [`order_book.py`](../../src/quantprep/systems/order_book.py)):
  - For each side, the price levels, kept sorted so the best price is found in O(1). Each level holds a queue of orders in arrival order.
  - A map from order ID to order, so cancels are O(1).
  - Prices stored as **integer ticks**, never floating point.
  - In C++, levels are often an array indexed by price tick (prices cluster near the best price), with intrusive linked lists and pre-allocated memory pools.
- **Architecture**:
  - A single-threaded matching loop per instrument (or group of instruments) is the usual choice: deterministic, with no locks.
  - In front of it, a **sequencer** gives every incoming message a global order and a sequence number, and writes it to a replicated log before matching.
  - A hot standby replays the same log and can take over instantly with identical state.
- **Around the core**:
  - Gateways check the session and message format.
  - Pre-trade risk checks enforce credit limits and stop "fat finger" mistakes (absurd sizes or prices).
  - The engine publishes trades and book changes to the market data feed.
- **Extras to mention**: order types (market, limit, immediate-or-cancel, fill-or-kill, iceberg), auctions at the open and close, self-trade prevention, and circuit breakers (trading halts on large moves).

---

### Design F: Backtesting platform
**Prompt**: "Design a system for researchers to test trading strategies on historical data."

- **Data**: **point-in-time** storage. Every record carries the time it became known, not just the time it refers to. Corrections are stored as new versions, not overwrites. The universe of instruments must include ones that later disappeared (avoids **survivorship bias**).
- **Engine types**:
  - **Vectorised** (whole-array calculations in pandas or NumPy): very fast, good for daily signals; easy to introduce look-ahead by mistake.
  - **Event-driven** (replay events in time order through the same strategy code that runs live): slower but realistic. It handles order fills, latency and path-dependence. Best practice is **one strategy code path for both backtest and live trading**.
- **Realism**: model trading costs, the bid–ask spread, market impact, latency, partial fills and queue position (for limit orders), and borrowing and funding costs.
- **Scale**: run many parameter sets in parallel on a cluster, and cache intermediate features.
- **Research hygiene**: record each run's code version, data version and parameters. Separate training and test periods (walk-forward testing). Count how many variants were tried, since trying many inflates the best result.

---

## Part 4 — Common follow-up questions

1. **"Volume grows 10×. What breaks first?"** Find the bottleneck by stage: input rate, compute, storage writes, query load. Then scale that stage: partition by instrument or desk, add workers, add a cache, conflate updates.
2. **"How do you make results reproducible?"** Version everything: market data snapshot IDs, position versions, library and code versions, configuration. Store them with each result. Keep the input event logs so runs can be replayed.
3. **"How do you avoid double-processing a trade?"** Give it a unique ID and make processing idempotent: ignore IDs already seen. Use sequence numbers to detect gaps and duplicates.
4. **"A downstream system is slow. What happens?"** Back-pressure: bounded queues, then shed or merge (conflate) updates. Never let one slow consumer block the critical path.
5. **"How do you deploy changes safely to a live trading system?"** Run tests and replay recorded production traffic. Roll out gradually (one instrument or desk first), keep feature switches and a fast rollback, deploy outside trading hours where possible, and keep the kill switch ready.
6. **"C++ or Python for this part?"** Python (or Java/C#) for orchestration, analytics and research, where development speed matters. C++ or Rust for latency-critical or compute-heavy loops: pricing libraries, feed handlers, matching. Bind them together with pybind11 or similar.
7. **"How would you monitor it?"** Business metrics (risk freshness, quotes live, hit rate, P&L) plus technical metrics (latency percentiles, queue depth, error rates). Alerts must be actionable, with a runbook for the on-call person.
8. **"Where is the single point of failure?"** Walk through each box. Each needs a standby or a restart path, and its state must be recoverable from a log or a replica.

---

## Glossary
| Term | Meaning |
|---|---|
| Latency / throughput | Time per request / requests handled per second |
| p99 latency | The time that 99% of requests finish within |
| ns, µs, ms | Nanosecond (10⁻⁹ s), microsecond (10⁻⁶ s), millisecond (10⁻³ s) |
| P&L | Profit and loss |
| DV01 | Value change for a one-basis-point (0.01%) move in rates |
| VaR | Value at risk: a loss level exceeded only with a small probability (e.g. 1%) |
| RFQ | Request for quote: a client asks dealers for a price on a specific trade |
| Markout | P&L of a trade measured a fixed time after it happened |
| Kill switch | A control that immediately stops all quoting or trading |
| Snapshot | A frozen, consistent copy of all market data at one moment, with an ID |
| Idempotent | Doing it twice has the same effect as doing it once |
| Sequence number | A counter on each message, used to detect gaps and duplicates |
| Event sourcing | Storing every event, so state can be rebuilt and replayed |
| Conflation | Merging queued updates and keeping only the latest |
| Back-pressure | Slowing producers when consumers can't keep up |
| Sharding / partitioning | Splitting data or work across machines by a key |
| Kubernetes | A system that runs, scales and restarts containerised services |
| Column store | A database that stores each column together; fast for analytics |
| kdb+ / q | A column-store time-series database (kdb+) and its query language (q), widely used for tick data |
| Tickerplant | The kdb+ process that logs and publishes every incoming update |
| UDP multicast | Network sending from one sender to many receivers, with no delivery guarantee |
| Kernel bypass | Reading the network card directly, skipping the operating system, for speed |
| Ring buffer | A fixed-size circular queue, often used between threads |
| Price-time priority | Matching rule: best price first, then earliest order |
| Tick (price) | The minimum price increment |
| AAD | Adjoint algorithmic differentiation: computes all sensitivities for about the cost of a few prices |
| Point-in-time data | Data stored with when it became known, so backtests can't see the future |
| Survivorship bias | Testing only on instruments that still exist, which overstates results |
