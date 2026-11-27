# Linear Algebra

The linear algebra that comes up in quant interviews and in risk systems: positive definite
matrices and Cholesky (correlated simulation), eigenvalues and PCA (yield curve factors),
least squares and conditioning (calibration). Each term is explained the first time it appears; a
glossary is at the end. Code blocks run on their own; the block after each shows its output.

Contents:

1. [Core facts](#1-core-facts)
2. [Correlation matrices, Cholesky and repair](#2-correlation-matrices-cholesky-and-repair)
3. [Least squares and conditioning](#3-least-squares-and-conditioning)
4. [PCA of yield curve moves](#4-pca-of-yield-curve-moves)
5. [Interview questions](#5-interview-questions)
6. [Glossary](#6-glossary)

---

## 1. Core facts

| Fact | Formula | Why it matters |
|---|---|---|
| Eigen-decomposition | `A v = λ v`; for symmetric `A`: `A = V Λ Vᵀ`, `V` orthogonal, `λ` real | Covariance matrices are symmetric, so this always works |
| Positive semi-definite (PSD) | `xᵀ A x ≥ 0` for all x ⟺ all eigenvalues ≥ 0 | Every covariance matrix is PSD: `xᵀ Σ x` is the variance of a portfolio x |
| Positive definite (PD) | All eigenvalues > 0 | Needed for Cholesky and for inverting |
| Cholesky | `A = L Lᵀ`, `L` lower triangular, for PD `A`; cost `n³/3` | Simulating correlated variables; solving PD systems fast |
| Trace and determinant | `tr A = Σ λᵢ`, `det A = Π λᵢ` | Total variance = trace of the covariance |
| SVD (singular value decomposition) | `A = U S Vᵀ` for any matrix | Least squares, rank, PCA without forming the covariance |
| Condition number | `κ(A) = σ_max / σ_min` | You lose about `log₁₀ κ` digits of accuracy when solving `A x = b` |
| Inverse of 2×2 | `[[a, b], [c, d]]⁻¹ = [[d, −b], [−c, a]] / (ad − bc)` | Mental maths in interviews |

Portfolio variance: `σ²_p = wᵀ Σ w`. The minimum-variance portfolio: `w ∝ Σ⁻¹ 1` (see [finance](../finance/README.md#5-portfolio-theory)).

---

## 2. Correlation matrices, Cholesky and repair

- If `C = L Lᵀ` and `z` has independent standard normal entries, then `x = L z` has `Cov(x) = L E[z zᵀ] Lᵀ = L Lᵀ = C`.
- A correlation matrix built pair by pair (different data windows, or edited by hand) is often **not** PSD, so Cholesky fails.
- **Repair** (a simple version of the nearest correlation matrix): eigen-decompose, clip negative eigenvalues to a small positive number, rebuild, and rescale to a unit diagonal. Higham's algorithm finds the true nearest one.
- When is a 3×3 correlation matrix valid? `1 − ρ₁₂² − ρ₁₃² − ρ₂₃² + 2ρ₁₂ρ₁₃ρ₂₃ ≥ 0` (the determinant). With ρ₁₂ = 0.9 and ρ₂₃ = 0.3, a ρ₁₃ of −0.6 is impossible: if 1 and 2 move together and 2 and 3 move together, 1 and 3 can't strongly oppose each other.

```python
import numpy as np

rng = np.random.default_rng(0)

# 1) Correlated normals with Cholesky: if C = L L^T and z ~ N(0, I), then L z has covariance C
C = np.array([[1.0, 0.8, 0.5],
              [0.8, 1.0, 0.6],
              [0.5, 0.6, 1.0]])
L = np.linalg.cholesky(C)
x = rng.standard_normal((200_000, 3)) @ L.T
print("sample correlation:\n", np.round(np.corrcoef(x, rowvar=False), 3))

# 2) A stitched-together "correlation" matrix that is not positive semi-definite
bad = np.array([[1.0, 0.9, -0.6],
                [0.9, 1.0, 0.3],
                [-0.6, 0.3, 1.0]])
w, V = np.linalg.eigh(bad)
print("eigenvalues:", np.round(w, 4))                  # one is negative -> Cholesky fails
try:
    np.linalg.cholesky(bad)
except np.linalg.LinAlgError as e:
    print("cholesky:", e)
fixed = V @ np.diag(np.clip(w, 1e-8, None)) @ V.T      # clip negative eigenvalues
d = np.sqrt(np.diag(fixed))
fixed = fixed / np.outer(d, d)                         # rescale to a unit diagonal
print("repaired:\n", np.round(fixed, 3))
print("min eigenvalue after:", f"{np.linalg.eigvalsh(fixed).min():.2e}")

# 3) Least squares: QR/lstsq vs the normal equations on a badly conditioned problem
t = np.linspace(0, 1, 50)
A = np.vander(t, 10, increasing=True)                  # polynomial basis 1, t, ..., t^9
coef_true = np.ones(10)
b = A @ coef_true
print(f"condition number of A: {np.linalg.cond(A):.1e}, of A^T A: {np.linalg.cond(A.T @ A):.1e}")
lstsq = np.linalg.lstsq(A, b, rcond=None)[0]
normal = np.linalg.solve(A.T @ A, A.T @ b)
print(f"max coefficient error: lstsq {np.abs(lstsq - 1).max():.1e}, "
      f"normal equations {np.abs(normal - 1).max():.1e}")
```

Output:

```text
sample correlation:
 [[1.    0.801 0.501]
 [0.801 1.    0.6  ]
 [0.501 0.6   1.   ]]
eigenvalues: [-0.2339  1.2734  1.9606]
cholesky: Matrix is not positive definite
repaired:
 [[ 1.     0.741 -0.491]
 [ 0.741  1.     0.221]
 [-0.491  0.221  1.   ]]
min eigenvalue after: 9.23e-09
condition number of A: 3.6e+06, of A^T A: 1.3e+13
max coefficient error: lstsq 1.5e-10, normal equations 6.1e-04
```

---

## 3. Least squares and conditioning

- Problem: minimise `‖A x − b‖²`. Solution: `x = (AᵀA)⁻¹ Aᵀ b` (the **normal equations**).
- Never compute it that way on real data: `κ(AᵀA) = κ(A)²`, so you lose twice as many digits. Use QR or SVD (`np.linalg.lstsq`), which work with `A` directly. The output above shows the gap: an error of 1.5 × 10⁻¹⁰ with `lstsq` against 6 × 10⁻⁴ with the normal equations.
- **Ridge regression** `x = (AᵀA + λI)⁻¹ Aᵀ b` improves conditioning by adding λ to every eigenvalue.
- Never compute `A⁻¹` explicitly to solve a system: `np.linalg.solve` is faster and more accurate.

---

## 4. PCA of yield curve moves

**PCA** (principal component analysis): the eigenvectors of the covariance matrix of daily curve
changes are the directions in which the curve moves, ordered by how much variance each explains.
For rates, the first three are almost always **level** (all tenors move together), **slope** (short
vs long) and **curvature** (the middle vs the ends), together explaining about 95–99%.

```python
import numpy as np

rng = np.random.default_rng(1)
tenors = np.array([1, 2, 3, 5, 7, 10, 20, 30])

# Simulate daily curve changes (bp) from three known shapes: level, slope, curvature
level = np.ones(8)
slope = (tenors - tenors.mean()) / tenors.std()
curve = (np.log(tenors) - np.log(tenors).mean()) ** 2
curve -= curve.mean()
shapes = np.column_stack([level, slope, curve])
shapes /= np.linalg.norm(shapes, axis=0)
f = rng.standard_normal((1000, 3)) * [6.0, 2.5, 1.0]  # factor sizes in bp
moves = f @ shapes.T + rng.standard_normal((1000, 8)) * 0.3

# PCA = eigen-decomposition of the covariance matrix
cov = np.cov(moves, rowvar=False)
w, V = np.linalg.eigh(cov)
w, V = w[::-1], V[:, ::-1]                             # largest first
print("variance explained:", np.round(w[:4] / w.sum(), 4))
print("PC1 loadings:", np.round(V[:, 0] * np.sign(V[:, 0].sum()), 2))  # roughly flat = level

# Hedge with PCs: a DV01 vector by tenor ($/bp) and its exposure to each factor
dv01 = np.array([0, 2_000, 0, -5_000, 0, 4_000, 0, 0], dtype=float)
exposure = V[:, :3].T @ dv01
print("exposure to PC1..PC3 ($ per unit factor):", np.round(exposure))
```

Output:

```text
variance explained: [0.8277 0.1392 0.0228 0.0023]
PC1 loadings: [0.35 0.35 0.35 0.35 0.35 0.35 0.37 0.37]
exposure to PC1..PC3 ($ per unit factor): [-374.  391.  483.]
```

Uses: hedge only the top 2–3 factors instead of every tenor; build scenarios from factor shocks;
check that a curve trade such as a butterfly is neutral to level and slope. See
[rates section 6](../rates/README.md#6-curve-trades-and-pca).

---

## 5. Interview questions

**Q1. Is `[[1, 0.9, 0.9], [0.9, 1, −0.9], [0.9, −0.9, 1]]` a valid correlation matrix?**
- Determinant: `1 − 3·0.81 + 2·(0.9)(0.9)(−0.9) = 1 − 2.43 − 1.458 < 0`. Not valid.

**Q2. What are the eigenvalues of an n×n matrix with 1 on the diagonal and ρ everywhere else?**
- `1 + (n − 1)ρ` (once, eigenvector all ones) and `1 − ρ` (n − 1 times). Valid (PSD) only if `ρ ≥ −1/(n − 1)`.
- Insight: the "market factor" eigenvalue grows with n, which is why one factor dominates equity correlations.

**Q3. How do you simulate two normals with correlation ρ?**
- `x₁ = z₁`, `x₂ = ρ z₁ + √(1 − ρ²) z₂`. This is the 2×2 Cholesky factor.

**Q4. Why can `A x = b` give garbage even though `A` is invertible?**
- A large condition number: small errors in `b` (or rounding) are magnified by up to `κ(A)`. Rescale columns, regularise, or use SVD and drop tiny singular values.

**Q5. How do you compute the top eigenvector of a huge sparse matrix?**
- Power iteration: `v ← A v / ‖A v‖`. It converges at rate `|λ₂/λ₁|`. Use Lanczos/Arnoldi (`scipy.sparse.linalg.eigsh`) in practice.

**Q6. Matrix multiplication cost, and why is NumPy's so fast?**
- `n³` multiply-adds naively. NumPy calls BLAS (basic linear algebra subprograms), which splits the matrices into cache-sized blocks and uses SIMD instructions (one instruction on several numbers) and threads.

---

## 6. Glossary

| Term | Meaning |
|---|---|
| BLAS | Basic linear algebra subprograms: optimised low-level matrix routines |
| Cholesky decomposition | `A = L Lᵀ` with `L` lower triangular, for positive definite `A` |
| Condition number | Ratio of largest to smallest singular value; how much errors are amplified |
| Eigenvalue / eigenvector | `A v = λ v`: a direction `v` that `A` only stretches, by `λ` |
| Normal equations | `AᵀA x = Aᵀ b`: the least-squares solution, numerically poor |
| Orthogonal matrix | `Vᵀ V = I`: columns are perpendicular unit vectors |
| PCA | Principal component analysis: eigenvectors of a covariance matrix, by variance explained |
| Positive (semi-)definite | All eigenvalues > 0 (≥ 0); every covariance matrix is PSD |
| Power iteration | Repeatedly multiplying by A to find the largest eigenvector |
| QR decomposition | `A = Q R` with Q orthogonal and R upper triangular; stable least squares |
| Ridge regression | Least squares plus a penalty `λ‖x‖²`, which improves conditioning |
| SVD | Singular value decomposition `A = U S Vᵀ`, exists for every matrix |
