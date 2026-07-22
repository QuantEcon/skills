"""
Faithful, runnable extraction of the ORIGINAL (main branch) NumPy implementation
of the Arrow-securities competitive-equilibrium model from
`lectures/ge_arrow.md`.

Notes on fidelity
-----------------
* The class is copied as-is from the `main` branch, with ONE class of change:
  the original methods `pricing_kernel` and `continuation_wealths` referenced
  the *module-level globals* `P`, `n`, `K` instead of `self.P`, `self.n`,
  `self.K`. In the lecture those globals happen to exist, so the code runs, but
  it is a latent bug / reliance on global state. To make this module
  self-contained and correct we replaced those references with `self.*`. This
  is recorded as an evaluation finding (see EVALUATION_FRAMEWORK.md, "Logic").
* The method name `value_functionss` (double 's') is preserved verbatim, because
  it is part of what we are evaluating (a typo in the public API).
* Cosmetic-only: arithmetic spacing was normalised in a few places
  (`T+1` → `T + 1`, `t-1` → `t - 1`). Found by diffing this file against a
  fresh extraction from the lecture at base 8cfba4c (validation run
  2026-07-22); semantics identical, disclosed per the v2 verbatim rule.
"""

import numpy as np


class RecurCompetitive:
    """
    A class that represents a recursive competitive economy
    with one-period Arrow securities.
    """

    def __init__(self,
                 s,        # state vector
                 P,        # transition matrix
                 ys,       # endowments ys = [y1, y2, .., yI]
                 γ=0.5,    # risk aversion
                 β=0.98,   # discount rate
                 T=None):  # time horizon, none if infinite

        # preference parameters
        self.γ = γ
        self.β = β

        # variables dependent on state
        self.s = s
        self.P = P
        self.ys = ys
        self.y = np.sum(ys, 1)

        # dimensions
        self.n, self.K = ys.shape

        # compute pricing kernel
        self.Q = self.pricing_kernel()

        # compute price of risk-free one-period bond
        self.PRF = self.price_risk_free_bond()

        # compute risk-free rate
        self.R = self.risk_free_rate()

        # V = [I - Q]^{-1} (infinite case)
        if T is None:
            self.T = None
            self.V = np.empty((1, self.n, self.n))
            self.V[0] = np.linalg.inv(np.eye(self.n) - self.Q)
        # V = [I + Q + Q^2 + ... + Q^T] (finite case)
        else:
            self.T = T
            self.V = np.empty((T + 1, self.n, self.n))
            self.V[0] = np.eye(self.n)

            Qt = np.eye(self.n)
            for t in range(1, T + 1):
                Qt = Qt.dot(self.Q)
                self.V[t] = self.V[t - 1] + Qt

        # natural debt limit
        self.A = self.V[-1] @ ys

    def u(self, c):
        "The CRRA utility"

        return c ** (1 - self.γ) / (1 - self.γ)

    def u_prime(self, c):
        "The first derivative of CRRA utility"

        return c ** (-self.γ)

    def pricing_kernel(self):
        "Compute the pricing kernel matrix Q"

        c = self.y

        n = self.n
        Q = np.empty((n, n))
        for i in range(n):
            for j in range(n):
                ratio = self.u_prime(c[j]) / self.u_prime(c[i])
                Q[i, j] = self.β * ratio * self.P[i, j]

        self.Q = Q

        return Q

    def wealth_distribution(self, s0_idx):
        "Solve for wealth distribution α"

        # set initial state
        self.s0_idx = s0_idx

        # simplify notations
        n = self.n
        Q = self.Q
        y, ys = self.y, self.ys

        # row of V corresponding to s0
        Vs0 = self.V[-1, s0_idx, :]
        α = Vs0 @ self.ys / (Vs0 @ self.y)

        self.α = α

        return α

    def continuation_wealths(self):
        "Given α, compute the continuation wealths ψ"

        diff = np.empty((self.n, self.K))
        for k in range(self.K):
            diff[:, k] = self.α[k] * self.y - self.ys[:, k]

        ψ = self.V @ diff
        self.ψ = ψ

        return ψ

    def price_risk_free_bond(self):
        "Give Q, compute price of one-period risk free bond"

        PRF = np.sum(self.Q, axis=1)
        self.PRF = PRF

        return PRF

    def risk_free_rate(self):
        "Given Q, compute one-period gross risk-free interest rate R"

        R = np.sum(self.Q, axis=1)
        R = np.reciprocal(R)
        self.R = R

        return R

    def value_functionss(self):
        "Given α, compute the optimal value functions J in equilibrium"

        n, T = self.n, self.T
        β = self.β
        P = self.P

        # compute (I - βP)^(-1) in infinite case
        if T is None:
            P_seq = np.empty((1, n, n))
            P_seq[0] = np.linalg.inv(np.eye(n) - β * P)
        # and (I + βP + ... + β^T P^T) in finite case
        else:
            P_seq = np.empty((T + 1, n, n))
            P_seq[0] = np.eye(n)

            Pt = np.eye(n)
            for t in range(1, T + 1):
                Pt = Pt.dot(P)
                P_seq[t] = P_seq[t - 1] + Pt * β ** t

        # compute the matrix [u(α_1 y), ..., u(α_K, y)]
        flow = np.empty((n, self.K))
        for k in range(self.K):
            flow[:, k] = self.u(self.α[k] * self.y)

        J = P_seq @ flow

        self.J = J

        return J
