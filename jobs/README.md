# Target Roles

| # | Firm | Role | Type | Location | Base |
|---|---|---|---|---|---|
| 1 | DRW | [Quant Dev, Analytics / Middle Office](drw-quant-dev-analytics.md) | QD | Chicago | $150–200k |
| 2 | Morgan Stanley | [USD IRS Algo Trading Strategist](ms-usd-swaps-algo-strat.md) | QR/QD (strat) | NYC | $150–250k |
| 3 | UBS | [Quant Analyst, Rates QA](ubs-rates-quant-analyst.md) | QR (modelling) | NYC | $225–242.5k |

## Common thread: interest rates
All three touch rates. Shared core first, then role-specific depth.

| Topic | DRW | MS | UBS | Priority |
|---|:-:|:-:|:-:|:-:|
| Swaps, curve building, DV01 / key-rate risk | ✓ | ✓✓ | ✓✓ | **1** |
| Option pricing & Greeks (BS, Black, Bachelier) | ✓✓ | ✓ | ✓✓ | **1** |
| Probability / brainteasers | ✓ | ✓✓ | ✓ | **1** |
| Python fluency (numpy/pandas, live coding) | ✓ | ✓✓ | ✓ | **1** |
| Numerical methods (root-finding, MC, PDE, optimisation) | ✓✓ | ✓ | ✓✓ | 2 |
| Statistics / ML / backtesting | ✓ | ✓✓ | ✓ | 2 |
| SABR, Hull–White, LMM, calibration, P&L explain | | | ✓✓ | 2 (UBS) |
| Market making, inventory, adverse selection | | ✓✓ | | 2 (MS) |
| KDB/q | | ✓✓ | | 3 (MS) |
| System design: analytics / risk service, Docker/K8s | ✓✓ | ✓ | | 3 (DRW) |
| C++ / DS&A | ✓ | | ✓ | 3 |

## Suggested order
1. **Rates core** — curve bootstrapper + swap pricer + DV01 (reused by all three)
2. **Options core** — BS/Black/Bachelier, Greeks, implied vol solver
3. Daily: 3–5 probability/brainteaser problems + 1 coding problem
4. Branch per interview schedule: UBS → SABR/HW/exotics · MS → market making + q · DRW → risk engine + system design
