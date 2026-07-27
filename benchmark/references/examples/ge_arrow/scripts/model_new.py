"""
Verbatim extraction of the NEW (branch `update_ge_arrow`) JAX implementation
of the Arrow-securities competitive-equilibrium model from
`lectures/ge_arrow.md`.

Copied as-is from the lecture so that benchmarks and equivalence checks run the
exact code under evaluation.
"""

import jax
import jax.numpy as jnp
import numpy as np
from typing import NamedTuple
from functools import partial


class RecurCompetitive(NamedTuple):
    """
    A class that represents a recursive competitive economy
    with one-period Arrow securities.
    """
    s: jax.Array    # state vector
    P: jax.Array    # transition matrix
    ys: jax.Array   # endowments ys = [y1, y2, .., yT]
    y: jax.Array    # total endowment under each state
    n: int          # number of states
    K: int          # number of agents
    γ: float        # risk aversion
    β: float        # discount rate
    T: float        # time horizon, 0 if infinite
    Q: jax.Array    # pricing kernel
    V: jax.Array    # resolvent / partial-sum matrices
    PRF: jax.Array  # price of risk-free bond
    R: jax.Array    # risk-free rate
    A: jax.Array    # natural debt limit
    α: jax.Array    # wealth distribution
    ψ: jax.Array    # continuation value
    J: jax.Array    # optimal value


@partial(jax.jit, static_argnames=("T", "s0_idx"))
def compute_rc_model(s, P, ys, s0_idx=0, γ=0.5, β=0.98, T=0):
    """Complete equilibrium objects under the endogenous pricing kernel.

    Args
    ----
    s : array-like
        Markov states.
    P : array-like
        Transition matrix.
    ys : array-like
        Endowment matrix; rows index states, columns index agents.
    s0_idx : int, optional
        Index of the initial zero-asset-holding state.
    γ : float, optional
        Risk aversion parameter.
    β : float, optional
        Discount factor.
    T : int, optional
        Number of periods; 0 means an infinite-horizon economy.

    Returns
    -------
    RecurCompetitive
        Instance containing all parameters and computed equilibrium results.
    """
    n, K = ys.shape
    y = jnp.sum(ys, axis=1)

    def u(c):
        "CRRA utility evaluated elementwise."
        return c ** (1 - γ) / (1 - γ)

    def u_prime(c):
        "Marginal utility for the CRRA specification."
        return c ** (-γ)

    def pricing_kernel(c):
        "Build the Arrow-security pricing kernel matrix."

        Q = jnp.empty((n, n))
        # fori_loop iterates over each state i while carrying the partially
        # filled matrix Q as the loop carry.
        def body_fun_i(i, Q):
            # fills row i entry-by-entry.
            def body_fun_j(j, q):
                ratio = u_prime(c[j]) / u_prime(c[i])
                # Return a (n,) array
                return q.at[j].set(β * ratio * P[i, j])

            q = jax.lax.fori_loop(
                0, n, body_fun_j, jnp.zeros((n,))
                )
            return Q.at[i, :].set(q)

        Q = jax.lax.fori_loop(
            0, n, body_fun_i, jnp.zeros((n, n))
            )
        return Q

    def resolvent_operator(Q):
        "Compute the resolvent or finite partial sums of Q depending on T."

        def infinite_period():
            # If T=0, V.shape = (1, n, n)
            V = jnp.zeros((T+1, n, n))
            V = V.at[0].set(jnp.linalg.inv(jnp.eye(n) - Q))
            return V

        # V = [I + Q + Q^2 + ... + Q^T] (finite case)
        def finite_period():
            V = jnp.zeros((T+1, n, n))
            V = V.at[0].set(jnp.eye(n))

            Qt = jnp.eye(n)

            # Loop body_fun advances the Q power and accumulates the geometric sum.
            def body_fun(t, carry):
                Qt, V = carry
                Qt = Qt @ Q
                V = V.at[t].set(V[t-1] + Qt)
                return Qt, V

            _, V = jax.lax.fori_loop(1, T+1, body_fun, (Qt, V))
            return V

        V = jax.lax.cond(T==0, infinite_period, finite_period)

        return V

    def natural_debt_limit(ys, V):
        "Compute natural debt limits from the terminal resolvent block."
        return V[-1] @ ys

    def wealth_distribution(V, ys, y, s0_idx):
        "Recover equilibrium wealth shares α from the initial state row."

        # row of V corresponding to s0
        Vs0 = V[-1, s0_idx, :]
        α = Vs0 @ ys / (Vs0 @ y)

        return α

    def continuation_wealths(V, α):
        "Back out continuation wealths for each agent."
        diff = jnp.empty((n, K))

        # Loop scatters each agent's state-dependent surplus into the column k.
        def body_fun(k, diff):
            return diff.at[:, k].set(α[k] * y - ys[:, k])

        # Applies body_fun sequentially while threading diff.
        diff = jax.lax.fori_loop(0, K, body_fun, diff)

        ψ = V @ diff

        return ψ

    def price_risk_free_bond(Q):
        "Given Q, compute price of one-period risk-free bond"
        return jnp.sum(Q, axis=1)

    def risk_free_rate(Q):
        "Given Q, compute one-period gross risk-free interest rate R"
        return jnp.reciprocal(price_risk_free_bond(Q))

    def value_functions(α, y):
        "Assemble lifetime value functions for each agent."

        # compute (I - βP)^(-1) in infinite case
        def infinite_period():
            # If T=0, V.shape = (1, n, n)
            P_seq = jnp.empty((T+1, n, n))
            P_seq = P_seq.at[0].set(
                jnp.linalg.inv(jnp.eye(n) - β * P)
                )
            return P_seq
        # and (I + βP + ... + β^T P^T) in finite case

        def finite_period():
            P_seq = jnp.empty((T+1, n, n))
            P_seq = P_seq.at[0].set(jnp.eye(n))

            Pt = jnp.eye(n)

            def body_fun(t, carry):
                Pt, P_seq = carry
                Pt = Pt @ P
                P_seq = P_seq.at[t].set(P_seq[t-1] + Pt * β ** t)
                return Pt, P_seq

            _, P_seq = jax.lax.fori_loop(
                1, T+1, body_fun, (Pt, P_seq)
                )
            return P_seq

        P_seq = jax.lax.cond(T==0, infinite_period, finite_period)

        # compute the matrix [u(α_1 y), ..., u(α_K, y)]
        def body_fun(k, flow):
            return flow.at[:, k].set(u(α[k] * y))

        flow = jax.lax.fori_loop(0, K, body_fun, jnp.empty((n, K)))

        J = P_seq @ flow

        return J

    Q = pricing_kernel(y)
    V = resolvent_operator(Q)
    A = natural_debt_limit(ys, V)
    α = wealth_distribution(V, ys, y, s0_idx)
    ψ = continuation_wealths(V, α)
    PRF = price_risk_free_bond(Q)
    R = risk_free_rate(Q)
    J = value_functions(α, y)

    return RecurCompetitive(
        s=s, P=P, ys=ys, y=y, n=n, K=K, γ=γ, β=β, T=T,
        Q=Q, V=V, A=A, α=α, ψ=ψ, PRF=PRF, R=R, J=J
        )
