# Quant Interview Prep

Preparation for **Quant Researcher (QR)** and **Quant Developer (QD)** interviews.

## Layout

| Path | Purpose |
|---|---|
| `jobs/` | Target job descriptions + per-role prep maps (start at `jobs/README.md`) |
| `notes/<topic>/README.md` | Theory notes + solved problems per topic |
| `src/quantprep/` | Python implementations (pricing, Monte Carlo, stats, ML) |
| `tests/` | pytest tests for `src/quantprep` |
| `cpp/src`, `cpp/tests` | C++ implementations for QD (data structures, low-latency, order book) |
| `notebooks/` | Exploratory Jupyter notebooks |
| `mock-interviews/` | Logs of mock interviews: questions asked, mistakes, follow-ups |

## Topics

**Both tracks**
- Probability — expectation, conditioning, Markov chains, combinatorics
- Brainteasers / mental math
- Statistics — estimation, hypothesis testing, regression

**Quant Research**
- Stochastic calculus — Brownian motion, Itô, Girsanov
- Finance — options pricing, Greeks, portfolio theory, factor models
- Linear algebra — eigen-decomposition, PCA, covariance estimation
- Numerical methods — root finding (bisection, Newton, Brent), gradient descent vs Newton, calibration (Levenberg–Marquardt) — see `notes/numerical-methods`
- Machine learning — bias/variance, regularisation, time-series CV, overfitting in backtests
- LLMs, agents, RAG, MCP — transformer basics, retrieval pipelines, agent patterns, finance pitfalls

**Quant Developer**
- C++ — memory model, move semantics, templates, cache-friendly design, lock-free structures
- Python (mid/senior) — data model, internals, concurrency, performance, NumPy/pandas depth — see `notes/python`
- Data structures & algorithms (LeetCode-style)
- System design — market data feed handler, order book, matching engine, backtester

## Commands

```bash
uv sync                 # install Python deps
uv run pytest           # run Python tests
make -C cpp test        # build and run C++ tests
uv run jupyter lab      # notebooks
```
