"""
Performance benchmark: OLD (NumPy) vs NEW (JAX) markov_asset.

Two parts:
  1. as-used total -- replay the lecture's asset-pricing calls once in a fresh
     process (run via `as_used_total.py`; this file focuses on scaling).
  2. scaling -- tree_price + consol_price warm runtime as the state space n
     grows, to find where JAX's compiled O(n^3) solve/eigvals overtakes NumPy.

The core ops (eigvals, dense solve) are O(n^3) LAPACK either way; the lecture
uses n=5 and n=25. Uses the bug-patched call_option is not needed here (we time
tree/consol only).

Output: results/scaling.json + stdout.
"""
import json
import os
import time
import statistics
import numpy as np
import jax
import jax.numpy as jnp

import model_old as old
import model_new as new

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS, exist_ok=True)


def make(n, seed=0):
    rng = np.random.default_rng(seed)
    P = rng.random((n, n)); P /= P.sum(1, keepdims=True)
    sv = np.linspace(-0.1, 0.1, n)   # small so spectral radius stays < 1/β
    return P, sv


def med(fn, repeat, number=1):
    xs = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        for _ in range(number):
            r = fn()
        xs.append((time.perf_counter() - t0) / number)
    return statistics.median(xs)


def main():
    rows = []
    for n in [5, 25, 50, 100, 250, 500, 1000]:
        P, sv = make(n)
        # OLD
        import quantecon as qe
        mc = qe.MarkovChain(P, state_values=sv)
        ap_o = old.AssetPriceModel(β=0.96, mc=mc, γ=2.0, g=np.exp)
        # NEW
        mc_n = new.MarkovChain(P=jnp.asarray(P), state_values=jnp.asarray(sv))
        ap_n = new.create_customized_ap_model(mc=mc_n, g=jnp.exp, β=0.96, γ=2.0)

        def old_call():
            old.tree_price(ap_o); old.consol_price(ap_o, 1.0)

        def new_call():
            e, v = new.tree_price_jit(ap_n)
            e2, p = new.consol_price_jit(ap_n, 1.0)
            jax.block_until_ready((v, p))

        new_call()  # warm
        rep = 7 if n <= 250 else 5
        t_o = med(old_call, rep)
        t_n = med(new_call, rep)
        rows.append({"n": n, "numpy_s": t_o, "jax_warm_s": t_n,
                     "speedup_warm": t_o / t_n})
        print(f"  n={n:5d}  numpy={t_o*1e3:9.3f} ms  jax_warm={t_n*1e3:9.3f} ms"
              f"  speedup={t_o/t_n:6.2f}x")

    with open(os.path.join(RESULTS, "scaling.json"), "w") as f:
        json.dump({"scaling": rows, "device": str(jax.devices()[0]),
                   "jax_x64": jax.config.read("jax_enable_x64")}, f, indent=2)


if __name__ == "__main__":
    main()
