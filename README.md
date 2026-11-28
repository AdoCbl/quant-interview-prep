# Quant Interview Prep

Preparation for **Quant Researcher (QR)** and **Quant Developer (QD)** interviews.

## Layout

| Path | Purpose |
|---|---|
| `notes/<topic>/README.md` | Theory notes + solved problems per topic |
| `src/quantprep/` | Python implementations (pricing, Monte Carlo, stats, ML) |
| `tests/` | pytest tests for `src/quantprep` |
| `cpp/src`, `cpp/tests` | C++ implementations for QD (data structures, low-latency, order book) |
| `notebooks/` | Exploratory Jupyter notebooks |
| `mock-interviews/` | Logs of mock interviews: questions asked, mistakes, follow-ups |

## Topics

**Both tracks**
- [Probability](notes/probability/README.md) — toolkit (linearity, indicators, first-step analysis, Bayes, martingales), distributions, 14 classic problems checked by simulation
- Brainteasers / mental math
- [Culture fit and behavioural](notes/behavioral/culture-fit.md) — what trading firms look for, STAR answers, question bank, worked answers, red flags, questions to ask
- Statistics — estimation, hypothesis testing, regression

**Quant Research**
- Stochastic calculus — Brownian motion, Itô, Girsanov
- [Finance](notes/finance/README.md) — returns, Sharpe ratio and its pitfalls, VaR and Expected Shortfall, portfolio theory, options and Greeks, bond duration and DV01, trading costs
- [Interest rates](notes/rates/README.md) — curves and bootstrapping, swaps, DV01 and bucketed risk, carry and roll-down, curve trades, swaptions and SABR, Hull-White and LMM, electronic swaps markets; deep dives on [SABR](notes/rates/sabr.md) and [LMM](notes/rates/lmm.md)
- [Domain knowledge](notes/domain/README.md) — proprietary trading firm and middle office, trade lifecycle and clearing, futures and variation margin, FIFO vs average-cost P&L, reconciliation, Treasury futures (CTD, basis, implied repo), SOFR futures and convexity, options P&L explain and scenario margin, equity/energy/crypto, market calendar
- [Trading and market making](notes/market-making/README.md) — order book, adverse selection (Glosten-Milgrom, Kyle), Avellaneda-Stoikov inventory quoting, microprice, RFQ pricing, hedging and risk controls, Almgren-Chriss execution, pairs trading, markouts
- [Linear algebra](notes/linear-algebra/README.md) — PSD matrices, Cholesky and correlation repair, least squares and conditioning, PCA of curve moves
- Numerical methods — root finding (bisection, Newton, Brent), gradient descent vs Newton, calibration (Levenberg–Marquardt) — see `notes/numerical-methods`
- Machine learning — bias/variance, regularisation, time-series CV, overfitting in backtests
- LLMs, agents, RAG, MCP — transformer basics, retrieval pipelines, agent patterns, finance pitfalls

**Quant Developer**
- [DRW: posted interview questions](notes/drw-interview/README.md) — reported process and 48 reported questions with worked solutions (probability, games, trading, stats, coding, C++/systems), answers checked by code
- [Analytics and middle office: targeted prep](notes/analytics-dev/README.md) — what gets tested, 10-day plan, analytic vs bumped Greeks, a tested risk and scenario engine (`src/quantprep/analytics`), bitemporal / any-horizon analytics, Git/CI/CD/Docker/Kubernetes, Elixir and the BEAM, on-call, 15 mock questions, behavioural stories, questions to ask
- C++ — memory model, move semantics, templates, cache-friendly design, lock-free structures
- [Python (mid/senior)](notes/python/README.md) — data model, internals, concurrency, performance, NumPy/pandas depth; plus [features, tricks and live-coding habits](notes/python/senior-features-and-tricks.md)
- [Data structures and algorithms](notes/dsa/README.md) ([C++ version](notes/dsa/cpp.md)) — complexity, pattern picker, two pointers, sliding window, prefix sums, stacks and heaps, graphs (BFS, DFS, topological sort, Dijkstra, Bellman-Ford arbitrage), intervals, binary search on the answer, DP, backtracking, trading-flavoured problems (rolling VWAP, order book, Fenwick tree)
- System design — framework, latency numbers, risk/scenario service, swap market-making system, feed handler, kdb+ tick, matching engine, backtester — see `notes/system-design`

## Commands

```bash
uv sync                 # install Python deps
uv run pytest           # run Python tests
make -C cpp test        # build and run C++ tests
uv run jupyter lab      # notebooks
```
