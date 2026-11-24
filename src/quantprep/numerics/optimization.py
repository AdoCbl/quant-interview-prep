"""Minimising a function: gradient descent vs Newton's method, and least-squares fitting.

- gradient_descent: step downhill along the negative gradient. Cheap per step, but on a long
  narrow valley (an "ill-conditioned" problem) it zig-zags and needs many steps.
- newton_minimize: jump to the minimum of the local quadratic approximation, using the
  second-derivative matrix (the Hessian). Very few steps near the minimum, but each step
  needs the Hessian and a linear solve (cost grows like n^3 in the number of unknowns n).
- levenberg_marquardt: the standard method for least-squares fitting, i.e. model
  calibration (e.g. fitting SABR or Hull-White parameters to market prices). It blends
  Gauss-Newton (fast) with gradient descent (safe), adjusting the blend each step.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

Vec = np.ndarray


@dataclass
class OptResult:
    x: Vec
    iterations: int
    converged: bool


def gradient_descent(grad: Callable[[Vec], Vec], x0, lr: float, momentum: float = 0.0,
                     tol: float = 1e-8, max_iter: int = 100_000) -> OptResult:
    """x_new = x - lr * gradient. With momentum > 0, each step also keeps a fraction of the
    previous step ("heavy ball"), which speeds up progress along narrow valleys.

    For a quadratic with largest curvature L, the learning rate must be below 2 / L or the
    iterates blow up; lr = 1 / L is the safe textbook choice.
    """
    x = np.asarray(x0, dtype=float).copy()
    velocity = np.zeros_like(x)
    for i in range(1, max_iter + 1):
        g = grad(x)
        if np.linalg.norm(g) < tol:
            return OptResult(x, i, True)
        velocity = momentum * velocity - lr * g
        x = x + velocity
        if not np.all(np.isfinite(x)):
            return OptResult(x, i, False)  # diverged: learning rate too large
    return OptResult(x, max_iter, False)


def newton_minimize(f: Callable[[Vec], float], grad: Callable[[Vec], Vec],
                    hess: Callable[[Vec], np.ndarray], x0, tol: float = 1e-10,
                    max_iter: int = 100) -> OptResult:
    """Solve H p = -g for the step p, then shorten it if needed (a "backtracking line search").

    Safeguards, because pure Newton can go uphill when the Hessian is not positive definite
    (i.e. the function is not bowl-shaped there):
    - if the solve fails or p does not point downhill, use the plain gradient direction -g;
    - halve the step until the function actually decreases enough (the Armijo condition).
    """
    x = np.asarray(x0, dtype=float).copy()
    for i in range(1, max_iter + 1):
        g = grad(x)
        if np.linalg.norm(g) < tol:
            return OptResult(x, i, True)
        try:
            p = np.linalg.solve(hess(x), -g)  # never form the inverse explicitly
        except np.linalg.LinAlgError:
            p = -g
        if g @ p >= 0:                         # not a descent direction
            p = -g
        t, fx = 1.0, f(x)
        while f(x + t * p) > fx + 1e-4 * t * (g @ p) and t > 1e-12:
            t *= 0.5
        x = x + t * p
    return OptResult(x, max_iter, False)


def levenberg_marquardt(residuals: Callable[[Vec], Vec], jacobian: Callable[[Vec], np.ndarray],
                        x0, lam: float = 1e-3, tol: float = 1e-12,
                        max_iter: int = 200) -> OptResult:
    """Minimise the sum of squared residuals r(x) (model minus market, one per instrument).

    Each step solves (J^T J + lam * diag(J^T J)) d = -J^T r, where J is the matrix of
    derivatives of each residual with respect to each parameter.
    - lam small: a Gauss-Newton step (Newton's method with the Hessian approximated by J^T J).
    - lam large: a short gradient-descent step.
    If a step reduces the error, accept it and lower lam (trust the fast model more);
    otherwise reject it and raise lam.
    """
    x = np.asarray(x0, dtype=float).copy()
    r = residuals(x)
    cost = r @ r
    for i in range(1, max_iter + 1):
        J = jacobian(x)
        JtJ, Jtr = J.T @ J, J.T @ r
        if np.linalg.norm(Jtr, np.inf) < tol:
            return OptResult(x, i, True)
        d = np.linalg.solve(JtJ + lam * np.diag(np.diag(JtJ)), -Jtr)
        x_new = x + d
        r_new = residuals(x_new)
        cost_new = r_new @ r_new
        if cost_new < cost:
            x, r = x_new, r_new
            if cost - cost_new < tol * (1 + cost):
                return OptResult(x, i, True)
            cost = cost_new
            lam = max(lam / 10, 1e-12)
        else:
            lam *= 10
    return OptResult(x, max_iter, False)
