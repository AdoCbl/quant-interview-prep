# Morgan Stanley — FID, Associate/VP, US Interest Rate Swaps Algo Trading Strategist

- **Link:** https://morganstanley.eightfold.ai/careers/job/549799568955 (JR042143)
- **Location:** New York · Strats, US E-Swaps team · posted 2026-08-10
- **Comp:** Associate $150k–$200k; VP $225k–$250k base + incentive
- **Role:** Algorithmic market making in USD IRS — research, modelling, back-testing, deployment, live
  monitoring of automated quoting/hedging strategies. Front office, close to traders and sales.

## Requirements (from JD)
- 4+ yrs quant role (ideally e-trading / market making / front office)
- Degree in CS / Eng / Maths / Physics / FE
- **Strong Python**; SDLC and system design
- **KDB/q** with large / high-frequency market & trading data
- Preferred: Java/OO; automated market-making (pricing, hedging, execution, risk); rates products
  (swaps, UST, bond/rate futures), pricing and risk

## What they will likely test
| Area | Expect | Prep in repo |
|---|---|---|
| Rates products | Swap mechanics (SOFR OIS, fixed vs float legs, day counts), par rate, DV01, swap spreads, futures vs swaps, invoice spreads, curve building (bootstrapping) | `notes/rates` |
| Market making | Inventory risk, skewing quotes, Avellaneda–Stoikov, adverse selection, fill-probability modelling, hedging residual risk with futures/UST, RFQ vs CLOB (D2C vs D2D/SEF) | `notes/market-making` |
| Stats / ML | Regression on flow data, signal evaluation (IC, decay, t-stats), overfitting in backtests, time-series CV, markouts | `notes/statistics`, `notes/machine-learning` |
| KDB/q | Tables, `select … by`, `aj` (as-of join) for trades vs quotes, `wj`, `xbar` bucketing, partitioned DBs | `notes/kdb-q` |
| Python | pandas/numpy fluency, live coding a backtest or markout analysis | `src/quantprep` |
| Probability | Brainteasers, market-making games ("make me a market on…") | `notes/probability`, `notes/brainteasers` |
| Behavioural | Ownership of live strategies, incident handling, working with traders | `notes/behavioral` |

## Projects to build for this role
- [ ] USD SOFR curve bootstrapper (deposits/futures/swaps) → par rates, DV01, key-rate risk
- [ ] Avellaneda–Stoikov market-making simulator with inventory penalty; plot PnL vs. risk aversion
- [ ] Markout analysis: simulated RFQ fills, compute markouts at 1s/10s/60s by client tier
- [ ] q exercises: install free kdb+ (personal edition), do `aj`/`wj` trade-quote joins on synthetic ticks
