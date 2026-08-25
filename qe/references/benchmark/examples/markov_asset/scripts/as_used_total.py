"""
"As-used" total latency for the WHOLE markov_asset lecture asset-pricing code.

Replays the sequence of solver calls the lecture cells make, once, in a fresh
interpreter (so JAX compiles + checkify overhead count). NOTE: the shipped NEW
`call_option` crashes (NameError `err`); to obtain a runnable end-to-end timing
we substitute a bug-patched call_option for the JAX side, and record that the
*shipped* code would not complete at all.

Run:  python as_used_total.py numpy   |   python as_used_total.py jax
"""
import json
import sys
import time
import numpy as np

mode = sys.argv[1] if len(sys.argv) > 1 else "numpy"


def exercise_arrays():
    n = 5
    P = np.full((n, n), 0.0125)
    P[range(n), range(n)] += 1 - P.sum(1)
    s = np.array([0.95, 0.975, 1.0, 1.025, 1.05])
    return P, s


if mode == "numpy":
    import quantecon as qe
    import model_old as old
    P5, s5 = exercise_arrays()
    t0 = time.perf_counter()
    # tree_price gamma sweep (default model, 5 values)
    for γ in [1.2, 1.4, 1.6, 1.8, 2.0]:
        old.tree_price(old.AssetPriceModel(γ=γ))
    # consol + call, beta=0.9 model
    ap9 = old.AssetPriceModel(β=0.9)
    old.consol_price(ap9, 1.0)
    old.call_option(ap9, 1.0, 40.0)
    # exercise model: tree, consol, call, finite (k=5,25)
    apm = old.AssetPriceModel(β=0.94, mc=qe.MarkovChain(P5, state_values=s5),
                              γ=2.0, g=lambda x: x)
    old.tree_price(apm); old.consol_price(apm, 1.0)
    old.call_option(apm, 1.0, 150.0)
    for k in (5, 25):
        old.finite_horizon_call_option(apm, 1.0, 150.0, k)
    print(json.dumps({"mode": "numpy", "total_s": time.perf_counter() - t0}))

else:
    import jax
    import jax.numpy as jnp
    import model_new as new

    # bug-patched call option so the JAX pipeline can complete end-to-end
    def call_fixed(ap, ζ, p_s, ϵ=1e-7):
        β, γ, P, G = ap.β, ap.γ, ap.mc.P, ap.G
        M = P * G ** (- γ)
        new.test_stability(M, β)
        p = new.consol_price(ap, ζ)
        n = M.shape[0]

        def step(st):
            w, _ = st
            wn = jnp.maximum(β * M @ w, p - p_s)
            return (wn, jnp.amax(jnp.abs(w - wn)))

        def cond(st):
            _, e = st
            return e > ϵ
        fw, _ = jax.lax.while_loop(cond, step, (jnp.zeros(n), ϵ + 1))
        return fw
    call_fixed_jit = jax.jit(new.checkify.checkify(call_fixed))

    P5, s5 = exercise_arrays()
    t0 = time.perf_counter()
    for γ in [1.2, 1.4, 1.6, 1.8, 2.0]:
        ap = new.create_customized_ap_model(new.create_ap_model().mc, γ=γ)
        e, v = new.tree_price_jit(ap); e.throw()
    ap9 = new.create_ap_model(β=0.9)
    e, p = new.consol_price_jit(ap9, 1.0); e.throw()
    e, w = call_fixed_jit(ap9, 1.0, 40.0); e.throw()
    mc_n = new.MarkovChain(P=jnp.array(P5), state_values=jnp.array(s5))
    apm = new.create_customized_ap_model(mc=mc_n, g=lambda x: x, β=0.94, γ=2.0)
    e, v = new.tree_price_jit(apm); e.throw()
    e, p = new.consol_price_jit(apm, 1.0); e.throw()
    e, w = call_fixed_jit(apm, 1.0, 150.0); e.throw()
    for k in (5, 25):
        e, w = new.finite_call_option_jit(apm, 1.0, 150.0, k); e.throw()
    jax.block_until_ready(w)
    print(json.dumps({"mode": "jax_patched", "total_s": time.perf_counter() - t0,
                      "note": "shipped call_option crashes; patched here to time"}))
