# Statistics Cheatsheet

## 1. Distributions to know cold
| Dist | Mean | Var | Notes |
|---|---|---|---|
| Bernoulli(p) | p | p(1−p) | |
| Binomial(n,p) | np | np(1−p) | sum of n Bernoullis |
| Poisson(λ) | λ | λ | sum of Poissons is Poisson |
| Geometric(p) (trials to 1st success) | 1/p | (1−p)/p² | memoryless |
| Uniform(a,b) | (a+b)/2 | (b−a)²/12 | |
| Exponential(λ) | 1/λ | 1/λ² | memoryless; min of exps ~ Exp(Σλᵢ) |
| Normal(μ,σ²) | μ | σ² | 68/95/99.7 at 1/2/3σ; 1.645 / 1.96 / 2.576 |
| Lognormal: e^X, X~N(μ,σ²) | e^{μ+σ²/2} | (e^{σ²}−1)e^{2μ+σ²} | |
| χ²ₖ | k | 2k | sum of k squared std normals |
| tₙ | 0 (n>1) | n/(n−2) | fatter tails than normal → normal as n→∞ |

- Var(aX+bY) = a²Var X + b²Var Y + 2ab Cov(X,Y)
- Law of total expectation: E[X] = E[E[X|Y]]; total variance: Var X = E[Var(X|Y)] + Var(E[X|Y])
- Corr ∈ [−1,1]; zero correlation ⇏ independence (except jointly Gaussian)

## 2. Estimators
- **Bias** = E[θ̂] − θ; **MSE** = Var(θ̂) + Bias²
- **Consistent**: θ̂ →ᵖ θ as n→∞. **Efficient**: lowest variance (Cramér–Rao bound = 1/(n·I(θ)))
- Sample variance: divide by **n−1** for unbiasedness (Bessel); the MLE divides by n (biased, lower MSE)
- Std error of the mean: σ/√n — halving the error needs 4× the data
- **MLE**: maximise log-likelihood; consistent, asymptotically normal, variance → 1/(n·I(θ)); invariant (MLE of g(θ) = g(θ̂))
- **Method of moments**: match sample moments to theoretical ones
- **LLN**: sample mean → μ. **CLT**: √n(X̄ − μ)/σ → N(0,1) (needs finite variance)
- **Delta method**: Var(g(θ̂)) ≈ g′(θ)² Var(θ̂)
- **Bootstrap**: resample with replacement for SE/CI; use a **block bootstrap** for time series

## 3. Hypothesis testing
- **p-value**: P(data at least this extreme | H₀). *Not* P(H₀ true).
- **Type I** (α): reject a true H₀. **Type II** (β): fail to reject a false H₀. **Power** = 1 − β
- Power rises with n, effect size and α, and falls with σ
- **CI**: θ̂ ± z·SE. A 95% CI means 95% of such intervals cover θ (frequentist)
- **Tests**: z (σ known or large n), t (σ unknown), paired t, χ² (variance / goodness of fit / independence), F (variance ratio / joint regression significance), KS (whole distribution)
- **Multiple testing**: with m tests at α, P(≥1 false positive) = 1 − (1−α)^m
  - Bonferroni: α/m (controls FWER, conservative)
  - Benjamini–Hochberg: controls FDR (sort p-values; reject p₍ᵢ₎ ≤ iα/m)
  - Quant context: data-mined backtests → use the deflated Sharpe ratio / a t-stat > 3 hurdle (Harvey–Liu–Zhu)

## 4. Linear regression (OLS)
- Model y = Xβ + ε; **β̂ = (XᵀX)⁻¹Xᵀy**; Var(β̂) = σ²(XᵀX)⁻¹; σ̂² = RSS/(n−p)
- Single regressor: β̂ = Cov(x,y)/Var(x) = ρ·σᵧ/σₓ; **R² = ρ²**
- Regressing y on x vs x on y: β_yx · β_xy = ρ² (the slopes are *not* reciprocals unless |ρ|=1)
- **Gauss–Markov** (linearity, exogeneity E[ε|X]=0, homoskedasticity, no autocorrelation, full rank) ⇒ OLS is BLUE. Add normal errors ⇒ exact t/F tests
- t-stat = β̂ⱼ / SE(β̂ⱼ); F-test for joint restrictions
- R² never falls when you add regressors → use adjusted R², AIC/BIC or out-of-sample R²
- **Geometry**: ŷ = Hy with H = X(XᵀX)⁻¹Xᵀ (a projection); residuals ⟂ columns of X
- **Frisch–Waugh–Lovell**: β̂ⱼ = the coefficient from regressing y on (xⱼ residualised on the other regressors)

| Problem | Effect | Fix |
|---|---|---|
| Omitted variable (correlated with x) | **biased** β̂: bias = β_omit · Cov(x,z)/Var(x) | add control, IV |
| Measurement error in x | attenuation toward 0: β̂ → β·Var(x*)/(Var(x*)+σᵤ²) | IV, errors-in-variables |
| Multicollinearity | unbiased but huge SE, unstable signs | drop/combine, ridge, PCA |
| Heteroskedasticity | β̂ unbiased, SE wrong | White / HC robust SE, WLS |
| Autocorrelated errors | β̂ unbiased, SE too small | Newey–West (HAC) SE, GLS |
| Overlapping returns (e.g. daily obs of 1m returns) | SE badly understated | HAC with lag ≥ overlap, non-overlapping samples |
| Outliers / fat tails | unstable fit | robust regression (Huber), winsorise |

**Duplicate-data trick question:** duplicate every row → β̂ unchanged, SEs shrink by √2, so the t-stats are spuriously inflated.

## 5. Regularisation
- **Ridge** (L2): β̂ = (XᵀX + λI)⁻¹Xᵀy; shrinks coefficients, handles collinearity, never exactly 0; Bayesian view = Gaussian prior
- **Lasso** (L1): sparse solutions / variable selection; Laplace prior; picks one feature from a correlated group arbitrarily
- **Elastic net**: L1 + L2
- Standardise features first; choose λ by (time-series) cross-validation
- Bias–variance: Error = Bias² + Variance + Irreducible noise

## 6. Time series
- **Weak stationarity**: constant mean and variance, autocovariance depends only on the lag
- **AR(1)**: xₜ = φxₜ₋₁ + εₜ, stationary iff |φ|<1; Var = σ²/(1−φ²); ACF = φ^k; half-life = ln 2 / (−ln φ)
- **MA(q)**: ACF cuts off after lag q. **AR(p)**: PACF cuts off after lag p
- **Random walk**: Var grows ∝ t; regressing one random walk on another → **spurious regression** (high R², meaningless)
- **Unit-root tests**: ADF (H₀: unit root), KPSS (H₀: stationary)
- **Cointegration**: xₜ, yₜ are I(1) but yₜ − βxₜ is I(0) → pairs trading / spread. Engle–Granger (OLS then ADF on the residual) or Johansen
- **Ornstein–Uhlenbeck**: dX = θ(μ − X)dt + σdW; the discrete-time version is AR(1) with φ = e^{−θΔt}
- **Volatility**: ARCH/GARCH(1,1): σ²ₜ = ω + αε²ₜ₋₁ + βσ²ₜ₋₁, stationary if α+β<1; EWMA = IGARCH (RiskMetrics λ≈0.94)
- Returns are close to uncorrelated, but |returns| and squared returns are autocorrelated (vol clustering)
- **Look-ahead bias**: never fit with future data; use walk-forward / purged, embargoed CV

## 7. Covariance & PCA
- Sample covariance S = (1/(n−1)) XᶜᵀXᶜ (X centred). It is singular if p ≥ n and noisy if p/n is not small
- **Shrinkage** (Ledoit–Wolf): Σ̂ = δF + (1−δ)S, with F = a structured target (constant correlation, identity, factor model)
- **PCA**: eigendecompose the covariance; PCs are orthogonal and ordered by variance explained
  - Rates curve: PC1 ≈ level (~80–90%), PC2 ≈ slope, PC3 ≈ curvature
- Random-matrix theory: eigenvalues inside the Marchenko–Pastur band are noise
- Valid correlation matrix: symmetric, PSD, ones on the diagonal. If invalid, fix with the nearest-correlation-matrix (Higham) method or by clipping eigenvalues

## 8. Bayesian basics
- Posterior ∝ likelihood × prior
- Conjugates: Beta–Binomial (Beta(a,b) → Beta(a+k, b+n−k)), Normal–Normal, Gamma–Poisson
- Normal–Normal posterior mean = precision-weighted average of the prior mean and the data
- MAP with a Gaussian prior = ridge; with a Laplace prior = lasso

## 9. Quant-specific stats
- **Sharpe ratio**: SR = μ/σ; annualise ×√252 (daily, iid). SE(SR̂) ≈ √((1 + SR²/2)/T) with T in periods
  - t-stat of mean return ≈ SR_annual · √years. SR=1 needs ~4 years for t≈2
- **IC (information coefficient)**: correlation of signal with forward return (use Spearman for robustness)
  - Fundamental law: IR ≈ IC · √breadth
- **Markouts**: average PnL a fixed time after a fill (1s / 10s / 60s), split by client/venue → measures adverse selection
- **Beta**: β = Cov(r, r_m)/Var(r_m); hedge ratio = minimum-variance = ρ·σ_y/σ_x
- **Overfitting**: number of trials matters; out-of-sample decay; deflated SR; avoid tuning on the test set
- **Survivorship and selection bias**: universe as-of date, delisted names
- **VaR / ES**: VaR_α = quantile of the loss; ES = E[loss | loss > VaR]. ES is coherent (subadditive), VaR is not

## 10. Classic interview questions
1. Is the sample variance biased? → With 1/n yes; 1/(n−1) is unbiased; s (the sample std) is still biased.
2. Regress y on x with slope 2 and R²=0.5. What's the slope of x on y? → ρ²/β = 0.5/2 = 0.25 (needs ρ², not 1/β).
3. Corr(X,Y)=ρ₁, Corr(Y,Z)=ρ₂; what range can Corr(X,Z) take? → ρ₁ρ₂ ± √((1−ρ₁²)(1−ρ₂²)) (from PSD).
4. Coin gives 60 heads in 100 tosses — fair? → z = (60−50)/5 = 2, p≈0.046 two-sided.
5. You test 100 strategies and the best has t=2.5 — is it real? → Multiple testing: expect ~1 at p<0.01 by chance; deflate.
6. Why use HAC SEs on overlapping returns? → The overlap induces MA(h−1) autocorrelation, so naive SEs are too small.
7. Add a regressor uncorrelated with y — what happens to R² and the other β's? → R² weakly ↑; the other β's change iff it is correlated with them.
8. Expected max of n iid N(0,1)? → ≈ √(2 ln n). This is why the best backtest out of many looks good.
9. Estimating the correlation of two assets with asynchronous closes → Epps effect / biased down; use lower-frequency or lead-lag (Dimson) adjustments.
10. MLE of the Exp(λ) rate? → λ̂ = 1/x̄ (biased; unbiased version (n−1)/Σx).
