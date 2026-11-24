# Root Finding & Optimisation: Bisection, Newton, Gradient Descent

Two closely related problems that come up constantly in quant work:
- **Root finding**: find x where f(x) = 0. Examples: implied volatility, bond yield, each step of building a yield curve.
- **Optimisation**: find x where f(x) is smallest. Examples: model calibration, portfolio construction, fitting machine learning models.

**The link between them**: at a minimum the slope is zero, so *minimising f is root finding on its gradient* ∇f(x) = 0. (The gradient ∇f is the vector of slopes in each direction.) Newton's method for minimisation is literally Newton's root-finding method applied to the gradient.

Code with tests: [`src/quantprep/numerics/root_finding.py`](../../src/quantprep/numerics/root_finding.py), [`src/quantprep/numerics/optimization.py`](../../src/quantprep/numerics/optimization.py), [`tests/test_numerics.py`](../../tests/test_numerics.py). The numbers quoted below come from running that code.

---

## Part 1 — Root finding (solve f(x) = 0)

### Bisection
- **Setup**: you need a *bracket* [lo, hi] with f(lo) and f(hi) of opposite signs. If f is continuous, a root lies between them.
- **Step**: evaluate the midpoint, and keep whichever half still has a sign change.
- **Speed**: the bracket halves every step, so the error after n steps is at most (hi − lo) / 2ⁿ. That is about one binary digit per step, or ~3.3 steps per decimal digit. Getting 12 digits takes ~40 steps.
- **Strength**: it *cannot fail* if the bracket is valid. It needs no derivative.
- **Weakness**: slow. It also needs a bracket, and can't find a root where the function touches zero without crossing (e.g. x² at 0).

### Newton's method (also called Newton–Raphson)
- **Idea**: replace the curve by its tangent line at the current point, and jump to where the tangent crosses zero:

  **x_new = x − f(x) / f′(x)**

- **Speed**: near a root, the error is roughly *squared* each step ("quadratic convergence"), so the number of correct digits roughly doubles each step. From the test run on f(x) = x³ − 2x − 5, starting at 3:

  | Step | Error |
  |---|---|
  | 1 | 0.27 |
  | 2 | 0.033 |
  | 3 | 0.00058 |
  | 4 | 0.00000019 |
  | 5 | 0.00000000000002 |

  That's 6 steps to machine precision, against 40 for bisection.
- **Failure modes** (asked in interviews):
  1. **Flat spot**: f′(x) ≈ 0 makes the step huge, or undefined.
  2. **Overshooting and divergence**: for f(x) = arctan(x) started at x = 2, Newton jumps further away each step, reaching 8.6 × 10²⁰ after 6 steps.
  3. **Cycling**: some functions make Newton bounce between two points forever.
  4. **Bad start**: it only converges reliably when started *close enough* to the root.
  5. **Repeated roots** (where the curve touches zero, e.g. (x − 1)²): convergence drops to linear (slow).
- **Cost**: one f evaluation plus one f′ evaluation per step.

### Secant method
- Newton's method with f′ replaced by the slope through the last two points: no derivative needed.
- **Speed**: in between. The error exponent is about 1.618 (the golden ratio): "superlinear". It took 7 steps in the test.
- Use it when the derivative is unavailable or expensive. It can fail in the same ways as Newton.

### Safeguarded Newton (what production code uses)
- Keep a bracket *and* try Newton steps. If the Newton step lands outside the bracket, or the derivative is zero, take a bisection step instead. Shrink the bracket after every evaluation.
- You get Newton's speed near the root and bisection's guarantee everywhere.
- **Brent's method** (`scipy.optimize.brentq`) does the same without derivatives. It mixes bisection, the secant method and a curve fit through three points. **It's the default choice for one-dimensional root finding.**

### Summary table
| Method | Needs | Speed near the root | Guaranteed? | Steps for 12 digits (test) |
|---|---|---|---|---|
| Bisection | a bracket | linear: 1 binary digit / step | yes | 40 |
| Newton | f′ and a good start | quadratic: digits double | no | 6 |
| Secant | two starting points | superlinear (order ~1.618) | no | 7 |
| Safeguarded Newton / Brent | a bracket (+ f′ for Newton) | fast | yes | 7 |

**Convergence order in one line**: if eₙ is the error at step n, then e_{n+1} ≈ C · eₙ^p.
- p = 1 is *linear*: each step multiplies the error by a constant less than 1.
- p = 2 is *quadratic*.

### Quant examples

**Implied volatility.** Solve BS(σ) − market price = 0, where BS is the Black–Scholes price as a function of volatility σ.
- The derivative is **vega** (the sensitivity of price to volatility), so Newton is natural.
- **Starting guess**: σ ≈ √(2π / T) × price / S, an approximation for at-the-money options (Brenner–Subrahmanyam). Here T is the time to expiry and S is the spot price.
- **Problem**: deep in- or out-of-the-money options have *tiny vega*, so plain Newton overshoots. Use the safeguarded version.

  In the tests it took 4 steps at the money (strike 100) and 10–11 steps at strikes 50 and 200.
- **Check the price first**: a call must be worth between max(S − K·e^(−rT), 0) and S, where K is the strike and r the interest rate. Outside that range, no volatility can produce the price ("arbitrage bounds"), so return an error instead of iterating.
- Price is an *increasing* function of volatility, so there is at most one solution.

**Bond yield to maturity.** Solve PV(y) − price = 0, where PV is the present value of the cash flows at yield y.
- The derivative is −price × modified duration. Newton converges in about 4–6 steps, because PV(y) is smooth and gently curved.

**Yield curve bootstrapping.** Instruments are taken in order of maturity. Each one adds one unknown (the next discount factor or zero rate), solved by a one-dimensional root search such as Brent.

**Several equations at once.** Newton generalises:
- Solve J·Δ = −F, then set x_new = x + Δ.
- Here F is the vector of equations, and J is the **Jacobian**: the matrix of derivatives of each equation with respect to each unknown.
- Each step needs a linear solve, roughly n³ work for n unknowns.

---

## Part 2 — Optimisation: gradient descent vs Newton's method

### Gradient descent
- **Idea**: walk downhill. The negative gradient is the direction of steepest descent:

  **x_new = x − η · ∇f(x)**

  where **η** (eta) is the *step size*, called the *learning rate* in machine learning.
- **Choosing η**:
  - Too small: very slow progress.
  - Too large: the iterates oscillate and blow up.
  - For a bowl-shaped quadratic whose steepest curvature is L, you need η < 2/L. The safe choice is η = 1/L. In the tests, η = 2.1/L failed.
- **Speed depends on the shape of the problem**:
  - The **condition number** κ is the steepest curvature divided by the flattest (for a quadratic, the ratio of the largest to the smallest eigenvalue of its matrix).
  - A large κ means a long narrow valley. Gradient descent zig-zags across the valley instead of moving along it.
  - The number of steps grows roughly like κ × log(1/accuracy).
  - In the test (κ = 100), plain gradient descent needed **1,834 steps**.
- **Cost per step**: just one gradient, O(n) memory. It scales to millions of unknowns, which is why machine learning uses it.

### Faster variants of gradient descent
- **Momentum ("heavy ball")**: each step keeps a fraction β (e.g. 0.9) of the previous step, so movement builds up along the valley floor and the zig-zags cancel. In the test: **254 steps** instead of 1,834.
  - The number of steps grows like √κ instead of κ when tuned.
- **Nesterov momentum**: like momentum, but evaluates the gradient at the "look-ahead" point. It is slightly better in theory and in practice.
- **Stochastic gradient descent**: estimate the gradient from a small random batch of data, not all of it. Steps are noisy but very cheap. This is standard for machine learning.
- **Adam**: momentum plus a separate, automatically adjusted step size for each parameter, based on its recent gradient sizes. It's the default for training neural networks.
- **Preconditioning**: rescale the variables so the valley becomes round, which lowers κ. Even just standardising the inputs to similar scales helps a lot.

### Newton's method for minimisation
- **Idea**: approximate f near x by a quadratic (a bowl), using the gradient g and the **Hessian** H (the matrix of second derivatives, i.e. the curvature). Jump straight to that bowl's bottom:

  **Solve H · p = −g, then x_new = x + p**

- **Speed**: near the minimum, the error is squared each step (quadratic convergence). **For an exact quadratic it reaches the minimum in one step**, whatever the condition number. In the test it took 1 step against 1,834 for gradient descent. On the curved Rosenbrock valley test function, it took under 50 steps against tens of thousands for gradient descent.
- **Why it ignores the condition number**: multiplying by H⁻¹ automatically rescales every direction by its curvature. Newton is "perfectly preconditioned" gradient descent.
- **Costs and dangers**:
  1. **Expensive steps**: forming H needs about n² numbers, and solving needs about n³ operations. That's fine for 10–1,000 parameters (calibration) and impossible for 10 million (neural networks).
  2. **Wrong direction**: if H is not positive definite (the surface is not bowl-shaped there, e.g. near a saddle point or a maximum), the Newton step can go *uphill* or towards the saddle. In non-convex problems Newton is *attracted* to saddle points; gradient descent isn't.
  3. **Overshooting far from the minimum**: the quadratic approximation is poor there.
- **Standard safeguards** (all in `newton_minimize`):
  - If the step doesn't point downhill, fall back to −g.
  - **Line search**: halve the step until f decreases enough.
  - Alternatively, a **trust region** limits the step to an area where the quadratic model is believed.
- **Never compute H⁻¹ explicitly.** Solve the linear system with `np.linalg.solve`, or with a Cholesky factorisation when H is positive definite. It's faster and more accurate.

### In between: quasi-Newton methods
- **BFGS** (named after Broyden, Fletcher, Goldfarb and Shanno) builds an *approximation* of the Hessian from how the gradient changes between steps. It needs only gradients, and is much faster than gradient descent ("superlinear").
- **L-BFGS** ("limited-memory BFGS") keeps only the last ~10 steps instead of a full n × n matrix, so it scales to large problems. It's the default in `scipy.optimize.minimize` for smooth problems with many parameters (`method="L-BFGS-B"`, which also handles bounds).

### Least squares: calibration's workhorse
Calibration minimises the squared differences between model and market:

  Σᵢ (model priceᵢ(θ) − market priceᵢ)²

over the model parameters θ (e.g. SABR's α, ρ, ν, or Hull–White's mean reversion and volatility).
- **Gauss–Newton**: approximate the Hessian by JᵀJ, where J holds the derivatives of each pricing error with respect to each parameter. This needs no second derivatives, and is accurate when the fit is good.
- **Levenberg–Marquardt**: solve (JᵀJ + λ·diag(JᵀJ)) · d = −Jᵀr, where r is the vector of pricing errors.
  - Small λ gives a Gauss–Newton step (fast). Large λ gives a short gradient-descent step (safe).
  - After a good step, lower λ; after a bad step, raise it.
  - **It's the standard calibration algorithm.** In `scipy` it's `least_squares(method="lm")`.
  - The test fits a curve y = a·e^(−bt) + c to noisy data and recovers the parameters.
- **Practical calibration tips**:
  - Scale the parameters to similar sizes.
  - Weight the instruments, e.g. by 1/vega to fit in volatility terms rather than price terms.
  - Use sensible bounds (correlation between −1 and 1, volatility above 0).
  - Start from yesterday's parameters: faster, and more stable day to day, which means less noise in hedge ratios and profit-and-loss explanations.

### Gradient descent vs Newton: comparison
| | Gradient descent | Newton |
|---|---|---|
| Uses | slopes (first derivatives) | slopes + curvature (second derivatives) |
| Cost per step | low: one gradient, n numbers | high: Hessian (n² numbers) + solve (~n³) |
| Steps needed | many; grows with the condition number κ (√κ with momentum) | few; quadratic convergence near the minimum, 1 step for a quadratic |
| Sensitive to scaling? | very | no (rescales itself) |
| Needs tuning? | learning rate | little (line search) |
| Non-convex problems | escapes saddle points with noise | can be drawn to saddle points; needs safeguards |
| Typical use | machine learning, huge n, noisy gradients | small or medium n, smooth problems: calibration, maximum-likelihood fits, portfolio optimisation |
| Middle ground | momentum, Adam | BFGS, L-BFGS, Gauss–Newton, Levenberg–Marquardt |

---

## Part 3 — Interview questions with short answers

1. **Bisection vs Newton: when would you pick bisection?** When robustness matters more than speed: no derivative is available, there's no good starting point, or the function is badly behaved. In practice, combine them (safeguarded Newton or Brent).
2. **Why does Newton converge quadratically?** Expand f around the root r. The tangent-line step removes the first-order error, and what's left is proportional to the square of the previous error: e_{n+1} ≈ (f″(r) / 2f′(r)) · eₙ².
3. **When does Newton fail?** Zero or tiny derivative, a start too far away, cycling, or a repeated root (convergence becomes linear).
4. **Implied volatility for a deep out-of-the-money option: what goes wrong, and how do you fix it?** Vega is tiny, so Newton steps are huge. Use a bracket with a bisection fallback (or Brent), a good starting guess, and check the arbitrage bounds first.
5. **Gradient descent is crawling. What can you do?** Rescale or standardise the variables, add momentum, use a line search, or switch to L-BFGS or Newton if the problem is small.
6. **What is the largest stable learning rate for a quadratic?** η < 2/L, where L is the largest curvature (the largest eigenvalue of the Hessian).
7. **Why isn't Newton used to train neural networks?** The Hessian has n² entries (with n in the millions or billions), solving costs n³, gradients are noisy, and Newton is attracted to saddle points.
8. **How many Newton steps to minimise a quadratic?** One, whatever its condition number.
9. **The Hessian isn't positive definite. What does that mean, and what do you do?** You're not in a bowl: it's a saddle point or a maximum. Fall back to the gradient direction, add a multiple of the identity matrix to H (this is what Levenberg–Marquardt's λ does), or use a trust region.
10. **What is the relation between root finding and optimisation?** Minimising f means solving ∇f = 0. Newton for minimisation is Newton root finding on the gradient, and the Hessian is the Jacobian of the gradient.
11. **Your calibrated parameters jump around from day to day. Why, and what's the fix?** The problem is badly conditioned: different parameter sets fit almost equally well, as with SABR's β and ρ. Fix one parameter, add a penalty for moving away from yesterday's values, start from yesterday's solution, or reduce the number of parameters.
12. **How do you get derivatives if you don't have formulas?** Finite differences, (f(x + h) − f(x − h)) / 2h, with h ≈ 10⁻⁵ to 10⁻⁶ relative to the size of x. Too small an h and rounding error dominates; too large and the approximation is poor. Alternatively, automatic differentiation (exact derivatives computed by the program) — in banks, "adjoint algorithmic differentiation" for risk.

---

## Glossary
| Term | Meaning |
|---|---|
| Root | A value x where f(x) = 0 |
| Bracket | An interval [lo, hi] where f changes sign, so it contains a root |
| Derivative f′(x) | The slope of f at x |
| Gradient ∇f | The vector of slopes of f in each variable's direction |
| Hessian H | The matrix of second derivatives: how the slopes change (curvature) |
| Jacobian J | The matrix of derivatives of several functions with respect to several variables |
| Positive definite | A matrix whose quadratic shape is a bowl (curves up in every direction) |
| Saddle point | A flat point that curves up in some directions and down in others |
| Convex function | One bowl with no other dips, so any local minimum is the global minimum |
| Linear / superlinear / quadratic convergence | The error shrinks by a constant factor per step / faster than that / is squared each step |
| Condition number κ | Steepest curvature ÷ flattest curvature; large means a long narrow valley |
| Learning rate (step size) η | How far gradient descent moves along the negative gradient each step |
| Line search | Shrinking a step until the function decreases enough |
| Trust region | Limiting the step to a zone where the local approximation is believed |
| Vega | Sensitivity of an option price to volatility |
| Modified duration | Percentage price change of a bond per unit change in yield |
| BFGS / L-BFGS | Quasi-Newton methods that approximate the Hessian from gradients; L- means limited memory |
| Levenberg–Marquardt | Least-squares method blending Gauss–Newton and gradient descent |
| Finite difference | Approximating a derivative from function values at nearby points |
