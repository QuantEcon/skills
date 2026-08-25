"""
Verbatim-faithful extraction of the ORIGINAL (main branch) NumPy implementation
of the Markov asset-pricing code from `lectures/markov_asset.md`.

Copied from `main`. The only adaptation: the original `AssetPriceModel.__init__`
references a *module-level* `n` when building the default Markov chain
(`qe.tauchen(n, ...)`); in the lecture `n=25` is defined in an earlier cell, so
we define it here too. (This global reliance is itself an evaluation finding,
mirroring the ge_arrow case.)
"""
import numpy as np
import quantecon as qe
from numpy.linalg import eigvals, solve

n = 25  # module-level default state-space size (as in the lecture)


class AssetPriceModel:
    """
    A class that stores the primitives of the asset pricing model.
    """
    def __init__(self, β=0.96, mc=None, γ=2.0, g=np.exp):
        self.β, self.γ = β, γ
        self.g = g

        # A default process for the Markov chain
        if mc is None:
            self.ρ = 0.9
            self.σ = 0.02
            self.mc = qe.tauchen(n, self.ρ, self.σ)
        else:
            self.mc = mc

        self.n = self.mc.P.shape[0]

    def test_stability(self, Q):
        "Stability test for a given matrix Q."
        sr = np.max(np.abs(eigvals(Q)))
        if not sr < 1 / self.β:
            msg = f"Spectral radius condition failed with radius = {sr}"
            raise ValueError(msg)


def tree_price(ap):
    "Computes the price-dividend ratio of the Lucas tree."
    β, γ, P, y = ap.β, ap.γ, ap.mc.P, ap.mc.state_values
    J = P * ap.g(y) ** (1 - γ)
    ap.test_stability(J)
    I = np.identity(ap.n)
    Ones = np.ones(ap.n)
    v = solve(I - β * J, β * J @ Ones)
    return v


def consol_price(ap, ζ):
    "Computes price of a consol bond with payoff ζ."
    β, γ, P, y = ap.β, ap.γ, ap.mc.P, ap.mc.state_values
    M = P * ap.g(y) ** (- γ)
    ap.test_stability(M)
    I = np.identity(ap.n)
    Ones = np.ones(ap.n)
    p = solve(I - β * M, β * ζ * M @ Ones)
    return p


def call_option(ap, ζ, p_s, ϵ=1e-7):
    "Computes price of a call option on a consol bond."
    β, γ, P, y = ap.β, ap.γ, ap.mc.P, ap.mc.state_values
    M = P * ap.g(y) ** (- γ)
    ap.test_stability(M)
    p = consol_price(ap, ζ)
    w = np.zeros(ap.n)
    error = ϵ + 1
    while error > ϵ:
        w_new = np.maximum(β * M @ w, p - p_s)
        error = np.amax(np.abs(w - w_new))
        w = w_new
    return w


def finite_horizon_call_option(ap, ζ, p_s, k):
    "Computes k period option value."
    β, γ, P, y = ap.β, ap.γ, ap.mc.P, ap.mc.state_values
    M = P * ap.g(y) ** (- γ)
    ap.test_stability(M)
    p = consol_price(ap, ζ)
    w = np.zeros(ap.n)
    for i in range(k):
        w = np.maximum(β * M @ w, p - p_s)
    return w
