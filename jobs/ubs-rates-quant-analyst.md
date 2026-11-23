# UBS — Quantitative Analyst, Rates (Rates Quantitative Analytics)

- **Link:** https://www.linkedin.com/jobs/view/quantitative-analyst-rates-at-ubs-4486065788/ (ref 344368BR)
- **Location:** New York (page header also says Charlotte, NC; confirm)
- **Comp:** $225k–$242.5k base + discretionary variable
- **Team:** Front-office QA — models for valuation and risk of IR, credit and hybrid derivatives;
  analytics library development; cross-asset risk and P&L reporting.

## Requirements (from JD)
- Masters/PhD in a quantitative field
- C++ or Python
- Quant finance, derivative pricing and/or ML
- **Hands-on IR options, lightly structured and exotic rates products and their modelling**
- **Calibration and risk-based P&L analysis of IR option & term-structure models**
- Clear communication of complex ideas; curiosity about AI-assisted workflows

## What they will likely test
| Area | Expect | Prep in repo |
|---|---|---|
| Stochastic calculus | Itô, Girsanov, change of numeraire (T-forward, annuity measure), martingale pricing | `notes/stochastic-calculus` |
| IR options | Caps/floors (Black & Bachelier/normal), swaptions under annuity measure, put-call parity for swaptions, vol cube, **SABR** (Hagan formula, β, smile dynamics, negative rates / shifted SABR) | `notes/rates` |
| Term-structure models | **Hull–White 1F** (analytic ZCB, calibration to coterminal swaptions, trinomial tree / PDE), G2++, **LMM**, Cheyette / local-vol; mean reversion's effect on Bermudans | `notes/rates` |
| Exotics | Bermudan swaptions (LSMC / PDE), CMS & convexity adjustment, callable range accruals, spread options, snowballs | `notes/rates` |
| Risk & P&L | Bump vs AAD Greeks, vega by bucket, **P&L explain** (theta, delta, gamma, vega, cross terms, unexplained), calibration stability → noisy Greeks | `notes/rates` |
| Numerics | MC (variance reduction, QMC, pathwise/LR Greeks), PDE (Crank–Nicolson, boundary conditions), calibration optimisers (Levenberg–Marquardt) | `notes/linear-algebra` |
| C++ | OO design of a pricing library (instrument / model / pricer separation), smart pointers, templates, performance | `cpp/` |

## Projects to build for this role
- [ ] Black & Bachelier cap/swaption pricers + implied vol inversion
- [ ] SABR: Hagan implied vol, calibrate (α, ρ, ν) to a smile; show β/ρ degeneracy
- [ ] Hull–White 1F: analytic ZCB/ZCB options, Jamshidian swaption, calibrate σ to coterminal swaptions
- [ ] Bermudan swaption via HW trinomial tree or LSMC; compare to European bound
- [ ] P&L explain on a swaption book over a simulated day move
