# DRW — Quant Developer, Unified Platform (Analytics / Middle Office)

- **Link:** https://www.linkedin.com/jobs/view/quant-developer-unified-platform-analytics-middle-office-at-drw-4483137349/
- **Location:** Chicago, IL (page also says Charlotte, NC; confirm) · Mid-Senior · Full-time
- **Comp:** $150k–$200k base + discretionary bonus
- **Team:** UP – Analytics – Middle Office. Services that compute analytic measures across asset
  classes, what-if scenario analysis, analytics over any time horizon; works with risk managers and
  desks on **option and rate sensitivities**.

## Requirements (from JD)
- Applied maths: linear algebra, optimisation, numerical methods
- Statistics and probability
- Quantitative modelling of financial products and derivatives
- Functional / OO / imperative languages; Git, CI/CD, Docker, Kubernetes
- Familiarity: one of Elixir / Python / Java / C#; one of C / C++ / Rust
- Pricing, risk management, portfolio analytics; exchange-traded assets; DS&A
- On-call rotation; close contact with users

## What they will likely test
| Area | Expect | Prep in repo |
|---|---|---|
| Coding | DS&A medium LeetCode in Python/C++; clean, tested code | `src/quantprep`, `cpp/` |
| Derivatives | Black-Scholes & Greeks, bump-and-reval vs analytic Greeks, put-call parity, vol surface basics | `notes/finance` |
| Rates | DV01 / PV01, key-rate durations, curve bumps, swap PV | `notes/rates` |
| Numerical methods | Root finding (implied vol via Newton/Brent), finite differences, MC variance reduction, interpolation, least squares / optimisation | `notes/linear-algebra` |
| System design | **Risk/analytics service**: scenario engine (shocks → reprice → aggregate), caching, batching, horizontal scaling on K8s, consistency of market data snapshots, latency vs. throughput | `notes/system-design` |
| Probability | Standard brainteasers, expectation, conditional probability | `notes/probability` |
| Behavioural | Collaboration, humility, debugging under pressure (on-call), working with traders | `notes/behavioral` |

## Projects to build for this role
- [ ] Portfolio risk engine: price a book of options + swaps, compute Greeks/DV01, run scenario grid (spot × vol × rate shifts)
- [ ] Implied-vol solver (Newton with Brent fallback) + tests
- [ ] Short design doc: "scenario analytics service" (API, compute grid, caching, K8s deployment)
- [ ] Skim Elixir basics (BEAM, actors, supervisors) — DRW is known for using it; good talking point
