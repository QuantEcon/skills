"""
"As-used" total latency for the WHOLE ge_arrow lecture.

We replay the exact sequence of solver calls the lecture's code cells make and
time it end-to-end, once, in a fresh interpreter -- i.e. what a reader actually
waits for. For JAX every distinct (shape, s0_idx, T) triggers its own
trace+compile, so this captures the real compile burden; NumPy just runs.

Run as two separate processes:
    python as_used_total.py numpy
    python as_used_total.py jax
Each prints a JSON line; run_all.py aggregates them into results/as_used.json.
"""
import json
import sys
import time
import numpy as np

mode = sys.argv[1] if len(sys.argv) > 1 else "numpy"


def economies():
    out = {}
    s = np.array([0., 1.]); P = np.array([[.5, .5], [.5, .5]])
    ys = np.empty((2, 2)); ys[:, 0] = 1 - s; ys[:, 1] = s
    out["ex1"] = (s, P, ys.copy())
    s = np.array([1., 2.]); ys = np.empty((2, 2)); ys[:, 0] = 1.5; ys[:, 1] = s
    out["ex2"] = (s, P, ys.copy())
    λ = 0.9; P3 = np.array([[1 - λ, λ], [0., 1.]])
    ys = np.empty((2, 2)); ys[:, 0] = [1, 0]; ys[:, 1] = [0, 1]
    out["ex3"] = (s, P3, ys.copy())
    s4 = np.array([1., 2., 3.]); λ = μ = .9; δ = .05
    P4 = np.array([[1 - λ, λ, 0], [μ/2, μ, μ/2], [(1-δ)/2, (1-δ)/2, δ]])
    ys4 = np.empty((3, 2)); ys4[:, 0] = [.25, .75, .2]; ys4[:, 1] = [1.25, .25, .2]
    out["ex4"] = (s4, P4, ys4.copy())
    return out


if mode == "numpy":
    import model_old as old
    E = economies()
    t0 = time.perf_counter()
    # ex1, ex2, ex3 : two initial states each
    for key in ["ex1", "ex2", "ex3"]:
        s, P, ys = E[key]
        for s0 in (0, 1):
            m = old.RecurCompetitive(s, P, ys)
            m.wealth_distribution(s0); m.continuation_wealths(); m.value_functionss()
    # ex3 lambda sweep (100 points, python loop)
    s, _, ys = E["ex3"]
    for λ in np.linspace(0, 0.99, 100):
        P = np.array([[1 - λ, λ], [0., 1.]])
        m = old.RecurCompetitive(s, P, ys)
        m.wealth_distribution(0); m.wealth_distribution(1)
    # ex4 : three initial states
    s, P, ys = E["ex4"]
    for s0 in (0, 1, 2):
        m = old.RecurCompetitive(s, P, ys)
        m.wealth_distribution(s0); m.continuation_wealths(); m.value_functionss()
    # finite T=10 (ex1) two states, and T=10000 convergence check
    s, P, ys = E["ex1"]
    for s0 in (0, 1):
        m = old.RecurCompetitive(s, P, ys, T=10)
        m.wealth_distribution(s0); m.continuation_wealths(); m.value_functionss()
    m = old.RecurCompetitive(s, P, ys, T=10000)
    m.wealth_distribution(1); m.continuation_wealths(); m.value_functionss()
    print(json.dumps({"mode": "numpy", "total_s": time.perf_counter() - t0}))

else:
    import jax
    import jax.numpy as jnp
    import model_new as new
    E = economies()

    def J(s, P, ys, s0, T=0):
        m = new.compute_rc_model(jnp.asarray(s), jnp.asarray(P),
                                 jnp.asarray(ys), s0_idx=s0, T=T)
        jax.block_until_ready(m.J)

    t0 = time.perf_counter()
    for key in ["ex1", "ex2", "ex3"]:
        s, P, ys = E[key]
        for s0 in (0, 1):
            J(s, P, ys, s0)
    # lambda sweep as the lecture does it: one jitted fori_loop
    s, _, ys = E["ex3"]; sj = jnp.asarray(s); ysj = jnp.asarray(ys)
    λj = jnp.linspace(0, 0.99, 100)

    @jax.jit
    def sweep():
        def body(i, carry):
            a0, a1 = carry
            λ = λj[i]; P = jnp.array([[1 - λ, λ], [0., 1.]])
            m0 = new.compute_rc_model(sj, P, ysj, s0_idx=0)
            m1 = new.compute_rc_model(sj, P, ysj, s0_idx=1)
            return a0.at[i].set(m0.α), a1.at[i].set(m1.α)
        return jax.lax.fori_loop(0, 100, body,
                                 (jnp.empty((100, 2)), jnp.empty((100, 2))))
    jax.block_until_ready(sweep())

    s, P, ys = E["ex4"]
    for s0 in (0, 1, 2):
        J(s, P, ys, s0)
    s, P, ys = E["ex1"]
    for s0 in (0, 1):
        J(s, P, ys, s0, T=10)
    J(s, P, ys, 1, T=10000)
    print(json.dumps({"mode": "jax", "total_s": time.perf_counter() - t0}))
