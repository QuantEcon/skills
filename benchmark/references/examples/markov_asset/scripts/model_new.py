"""
Verbatim extraction of the NEW (branch `update_markov_asset`) JAX implementation
of the Markov asset-pricing code from `lectures/markov_asset.md`.

Copied AS-IS from the lecture so benchmarks and equivalence checks exercise the
exact code under evaluation -- INCLUDING the `err.throw()` line inside
`call_option`, which references a name that is never bound in that scope. We
keep it verbatim because whether it runs is part of what we are evaluating.
"""
import jax
import jax.numpy as jnp
import quantecon as qe
from jax.numpy.linalg import eigvals, solve
from jax.experimental import checkify
from typing import NamedTuple


class MarkovChain(NamedTuple):
    "Stores the primitives of a Markov chain."
    P: jax.Array
    state_values: jax.Array


class AssetPriceModel(NamedTuple):
    "Stores the primitives of the asset pricing model."
    mc: MarkovChain
    G: jax.Array
    β: float
    γ: float


def create_ap_model(g=jnp.exp, β=0.96, γ=2.0):
    "Create an AssetPriceModel class using standard Markov chain."
    n, ρ, σ = 25, 0.9, 0.02
    qe_mc = qe.tauchen(n, ρ, σ)
    P = jnp.array(qe_mc.P)
    state_values = jnp.array(qe_mc.state_values)
    G = g(state_values)
    mc = MarkovChain(P=P, state_values=state_values)
    return AssetPriceModel(mc=mc, G=G, β=β, γ=γ)


def create_customized_ap_model(mc: MarkovChain, g=jnp.exp, β=0.96, γ=2.0):
    "Create an AssetPriceModel class using a customized Markov chain."
    G = g(mc.state_values)
    return AssetPriceModel(mc=mc, G=G, β=β, γ=γ)


def test_stability(Q, β):
    "Stability test for a given matrix Q."
    sr = jnp.max(jnp.abs(eigvals(Q)))
    checkify.check(
        sr < 1 / β,
        "Spectral radius condition failed with radius = {sr}", sr=sr
        )
    return sr


def tree_price(ap):
    "Computes the price-dividend ratio of the Lucas tree."
    β, γ, P, G = ap.β, ap.γ, ap.mc.P, ap.G
    J = P * G ** (1 - γ)
    test_stability(J, β)
    n = J.shape[0]
    I = jnp.identity(n)
    Ones = jnp.ones(n)
    v = solve(I - β * J, β * J @ Ones)
    return v


tree_price_jit = jax.jit(checkify.checkify(tree_price))


def consol_price(ap, ζ):
    "Computes price of a consol bond with payoff ζ."
    β, γ, P, G = ap.β, ap.γ, ap.mc.P, ap.G
    M = P * G ** (- γ)
    test_stability(M, β)
    n = M.shape[0]
    I = jnp.identity(n)
    Ones = jnp.ones(n)
    p = solve(I - β * M, β * ζ * M @ Ones)
    return p


consol_price_jit = jax.jit(checkify.checkify(consol_price))


def call_option(ap, ζ, p_s, ϵ=1e-7):
    "Computes price of a call option on a consol bond."
    β, γ, P, G = ap.β, ap.γ, ap.mc.P, ap.G
    M = P * G ** (- γ)
    test_stability(M, β)
    # Compute option price
    p = consol_price(ap, ζ)
    err.throw()                       # <-- VERBATIM from lecture: `err` undefined
    n = M.shape[0]
    w = jnp.zeros(n)
    error = ϵ + 1

    def step(state):
        w, _ = state
        w_new = jnp.maximum(β * M @ w, p - p_s)
        error_new = jnp.amax(jnp.abs(w - w_new))
        return (w_new, error_new)

    def cond(state):
        _, error = state
        return error > ϵ

    final_w, _ = jax.lax.while_loop(cond, step, (w, error))
    return final_w


call_option_jit = jax.jit(checkify.checkify(call_option))


def finite_call_option(ap, ζ, p_s, k):
    "Computes k period option value."
    β, γ, P, G = ap.β, ap.γ, ap.mc.P, ap.G
    M = P * G ** (- γ)
    test_stability(M, β)
    p = consol_price(ap, ζ)
    n = M.shape[0]

    def step(i, w):
        w = jnp.maximum(β * M @ w, p - p_s)
        return w

    w = jax.lax.fori_loop(0, k, step, jnp.zeros(n))
    return w


finite_call_option_jit = jax.jit(checkify.checkify(finite_call_option))
