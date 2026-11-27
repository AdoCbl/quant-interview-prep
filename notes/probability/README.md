# Probability

The tools that solve almost every interview probability question, then 14 classic problems. Each
has a statement, a solution, the key insight and common follow-ups. When practising, try each one
for five minutes before reading the solution. Each term is explained the first time it appears; a
glossary is at the end. The code block at the end checks the answers by simulation (Monte Carlo).

Contents:

1. [The toolkit](#1-the-toolkit)
2. [Distributions to know](#2-distributions-to-know)
3. [Classic problems](#3-classic-problems)
4. [Checking answers by simulation](#4-checking-answers-by-simulation)
5. [Glossary](#5-glossary)

---

## 1. The toolkit

| Tool | Formula | Use it when |
|---|---|---|
| **Linearity of expectation** | `E[X + Y] = E[X] + E[Y]`, even if X and Y are dependent | Counting expected numbers of things: write the count as a sum of indicators |
| **Indicator variables** | `1_A` = 1 if A happens, else 0; `E[1_A] = P(A)` | "Expected number of fixed points / pairs / runs" |
| **Conditioning (first-step analysis)** | `E[X] = Σ P(first step = s) · E[X ∣ first step = s]` | Waiting times, games, Markov chains: write one equation per state |
| **Law of total probability** | `P(A) = Σ P(A ∣ Bᵢ) P(Bᵢ)` | Split into cases |
| **Bayes' rule** | `P(A ∣ B) = P(B ∣ A) P(A) / P(B)` | Updating on evidence; test results |
| **Symmetry** | Equally likely outcomes have equal probabilities | "Probability that the first ace comes before the first king" = ½ |
| **Complement** | `P(at least one) = 1 − P(none)` | Birthday-type problems |
| **Tail sum** | For `X ≥ 0` integer: `E[X] = Σₖ₌₁^∞ P(X ≥ k)` | Expected maximum or minimum |
| **Variance of a sum** | `Var(X + Y) = Var X + Var Y + 2 Cov(X, Y)` | Portfolio variance, sums of indicators |
| **Martingale / optional stopping** | A fair game stopped at a bounded time has `E[X_stop] = X_0` | Gambler's ruin and fair-game problems in one line |

---

## 2. Distributions to know

| Distribution | Mean | Variance | Typical story |
|---|---|---|---|
| Bernoulli(p) | p | p(1−p) | One trial |
| Binomial(n, p) | np | np(1−p) | Number of successes in n trials |
| Geometric(p) (trials until first success) | 1/p | (1−p)/p² | Waiting for a success |
| Poisson(λ) | λ | λ | Counts of rare events per interval |
| Uniform(0, 1) | ½ | 1/12 | Random point; the k-th smallest of n has mean k/(n+1) |
| Exponential(λ) | 1/λ | 1/λ² | Waiting time; memoryless; min of independent exponentials is exponential with rate Σλ |
| Normal(μ, σ²) | μ | σ² | Sums of many small effects; 68/95/99.7% within 1/2/3 σ |

---

## 3. Classic problems

**P1. Expected tosses of a fair coin until two heads in a row (HH)? And until HT?**
- Solution (HH): states "start" and "just saw H". `E₀ = 1 + ½E₁ + ½E₀`, `E₁ = 1 + ½·0 + ½E₀`. So `E₀ = 6`.
- HT: once you see H, you only wait for a T (an H keeps you in the same state): `E = 2 + 2 = 4`.
- Insight: HH is slower because a failure (HT) sends you back to the start; for HT, a failure (HH) does not.
- Follow-ups: HHH = 14. In general, for HH...H with n heads: `2^(n+1) − 2`.

**P2. Expected number of rolls of a die until a 6?**
- Geometric with `p = 1/6`: `E = 6`.
- Follow-up: until all six faces have appeared (coupon collector): `6·(1 + ½ + ⅓ + ¼ + ⅕ + ⅙) = 14.7`.

**P3. Expected maximum of two dice.**
- Tail sum or count: `P(max ≤ k) = (k/6)²`, so `P(max = k) = (2k − 1)/36`. `E = Σ k(2k − 1)/36 = 161/36 ≈ 4.47`.

**P4. n people put hats in a pile and each draws one at random. Expected number with their own hat?**
- Indicators: each person has probability 1/n, so `E = n · 1/n = 1`, for every n.
- Insight: linearity works even though the events are dependent.
- Follow-up: the probability that nobody gets their own hat → `1/e ≈ 0.368`.

**P5. Birthday problem: how many people for a better-than-even chance of a shared birthday?**
- `P(all different) = Π (1 − k/365)` for k = 0..n−1; it falls below ½ at `n = 23`.
- Quick estimate: `P(no match) ≈ exp(−n²/(2·365))`; set it to ½: `n ≈ √(2·365·ln 2) ≈ 22.5`.

**P6. Break a stick at two uniformly random points. Probability the three pieces form a triangle?**
- A triangle needs every piece < ½. The bad events "piece i ≥ ½" are disjoint, and each has probability ¼. So `P = 1 − 3·¼ = ¼`.

**P7. Gambler's ruin: start with $3, bet $1 on a fair coin until $0 or $10. Probability of reaching $10?**
- Your wealth is a martingale (a fair game: expected next value = current value). Optional stopping: `3 = 10·p + 0·(1 − p)`, so `p = 0.3`.
- Follow-up: the expected duration is `3 × 7 = 21` bets. With a biased coin (q/p ≠ 1): `p = (1 − (q/p)³) / (1 − (q/p)¹⁰)`.

**P8. A test is 99% sensitive and 95% specific; 1% of people are ill. You test positive. Probability you are ill?**
- Formula: `P(ill ∣ +) = P(+ ∣ ill)·P(ill) / [P(+ ∣ ill)·P(ill) + P(+ ∣ healthy)·P(healthy)]`.
- Numbers: `0.99·0.01 / (0.99·0.01 + 0.05·0.99) = 0.0099 / 0.0594 ≈ 16.7%`.
- Insight: when the condition is rare, most positives are false positives.

**P9. Monty Hall: you pick door 1 of 3; the host, who knows where the car is, opens a door with a goat. Switch?**
- Yes: switching wins with probability ⅔. Your first pick is right with probability ⅓ and the host's action does not change that, so the other closed door has ⅔.

**P10. Two envelopes / a game: you roll a die and may roll again once, keeping the second roll. Strategy and value?**
- On the second roll you expect 3.5. Keep the first roll if it is 4 or more. Value `= (4 + 5 + 6)/6 + (3/6)·3.5 = 2.5 + 1.75 = 4.25`.
- Follow-up: with three rolls, keep the first if ≥ 5; value `= 14/3 ≈ 4.67`.

**P11. Expected minimum of n independent Uniform(0, 1) variables.**
- `P(min > x) = (1 − x)ⁿ`, so `E = ∫₀¹ (1 − x)ⁿ dx = 1/(n + 1)`. The maximum has mean `n/(n + 1)`.

**P12. Random walk: probability a symmetric walk ever returns to 0? Expected time to hit +1?**
- In one dimension it returns with probability 1, but the expected time to hit +1 is infinite. (In three dimensions the probability of return is only about 0.34.)

**P13. X and Y are standard normals with correlation ρ. What is P(X > 0 and Y > 0)?**
- `P = ¼ + arcsin(ρ) / (2π)`. For ρ = 0 it is ¼; for ρ = 1 it is ½.

**P14. Brownian motion `W`: `E[W_t²]`, `E[W_s W_t]`, and the probability it ends above where it started?**
- `E[W_t²] = t`, `E[W_s W_t] = min(s, t)`, `P(W_t > 0) = ½`. The reflection principle gives `P(max over [0, t] ≥ a) = 2·P(W_t ≥ a)`.

---

## 4. Checking answers by simulation

```python
import numpy as np

rng = np.random.default_rng(0)
n = 200_000


def tosses_until(pattern: str, trials: int = 20_000) -> float:
    """Average number of fair coin tosses until `pattern` (e.g. 'HH') first appears."""
    total = 0
    for _ in range(trials):
        seq = ""
        while not seq.endswith(pattern):
            seq += "H" if rng.random() < 0.5 else "T"
        total += len(seq)
    return total / trials


print(f"HH {tosses_until('HH'):.2f} (exact 6), HT {tosses_until('HT'):.2f} (exact 4)")

# Broken stick: break [0, 1] at two uniform points; P(the three pieces form a triangle) = 1/4
u = np.sort(rng.random((n, 2)), axis=1)
pieces = np.column_stack([u[:, 0], u[:, 1] - u[:, 0], 1 - u[:, 1]])
print(f"triangle {np.mean(pieces.max(axis=1) < 0.5):.4f} (exact 0.25)")

# Expected max of two dice = 161/36
d = rng.integers(1, 7, size=(n, 2))
print(f"E[max of 2 dice] {d.max(axis=1).mean():.4f} (exact {161 / 36:.4f})")

# Coupon collector: expected draws to see all 6 faces = 6 * H_6 = 14.7
draws = []
for _ in range(20_000):
    seen, k = set(), 0
    while len(seen) < 6:
        seen.add(int(rng.integers(6)))
        k += 1
    draws.append(k)
print(f"coupon collector {np.mean(draws):.2f} (exact {6 * sum(1 / i for i in range(1, 7)):.2f})")

# Gambler's ruin: start at 3, stop at 0 or 10, fair coin -> P(reach 10) = 3/10
wins = 0
for _ in range(20_000):
    x = 3
    while 0 < x < 10:
        x += 1 if rng.random() < 0.5 else -1
    wins += x == 10
print(f"gambler's ruin {wins / 20_000:.4f} (exact 0.3)")

# Bayes: test 99% sensitive, 95% specific, prevalence 1% -> P(ill | positive) ~ 16.7%
ill = rng.random(n) < 0.01
positive = np.where(ill, rng.random(n) < 0.99, rng.random(n) < 0.05)
print(f"P(ill | +) {ill[positive].mean():.3f} (exact {0.99 * 0.01 / (0.99 * 0.01 + 0.05 * 0.99):.3f})")

# E[min of n uniforms] = 1/(n+1)
print(f"E[min of 4 uniforms] {rng.random((n, 4)).min(axis=1).mean():.4f} (exact 0.2000)")
```

Output:

```text
HH 5.96 (exact 6), HT 3.98 (exact 4)
triangle 0.2489 (exact 0.25)
E[max of 2 dice] 4.4816 (exact 4.4722)
coupon collector 14.66 (exact 14.70)
gambler's ruin 0.2952 (exact 0.3)
P(ill | +) 0.167 (exact 0.167)
E[min of 4 uniforms] 0.2007 (exact 0.2000)
```

Simulation is a good habit in interviews: if you have a laptop, a 10-line check catches algebra
slips. Standard error ≈ `σ/√n`, so 20,000 trials give about 2 decimal places.

---

## 5. Glossary

| Term | Meaning |
|---|---|
| Conditional probability | `P(A ∣ B)`: probability of A given that B happened |
| Coupon collector | Expected draws to see all n types: `n·(1 + ½ + ... + 1/n)` |
| First-step analysis | Writing an equation for each state by conditioning on the first move |
| Indicator variable | A variable equal to 1 if an event happens and 0 otherwise |
| Linearity of expectation | The expectation of a sum is the sum of expectations, always |
| Markov chain | A process whose next state depends only on the current state |
| Martingale | A process whose expected next value, given the past, equals its current value |
| Memoryless | `P(X > s + t ∣ X > s) = P(X > t)`; true for exponential and geometric distributions |
| Monte Carlo | Estimating a quantity by averaging random simulations |
| Optional stopping | For a martingale stopped at a well-behaved time, the expected final value equals the start |
| Reflection principle | For Brownian motion, paths that touch a level can be mirrored, doubling a tail probability |
