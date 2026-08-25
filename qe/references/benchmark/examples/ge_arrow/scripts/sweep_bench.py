"""
Benchmark the one workload in the lecture that repeats the solver many times:
Example 3's sweep over 100 values of the transition probability lambda.

OLD: a Python for-loop building 100 NumPy models.
NEW: a single jitted `fori_loop` (compile once, run 100 iterations).

This is the scenario most favourable to the JAX rewrite, so it bounds the
upside. Prints JSON consumed by run_all.py.
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

s_np = np.array([1, 2])
ys_np = np.empty((2, 2)); ys_np[:, 0] = [1, 0]; ys_np[:, 1] = [0, 1]
λ_seq = np.linspace(0, 0.99, 100)


def old_sweep():
    αs0 = np.empty((100, 2)); αs1 = np.empty((100, 2))
    for i, λ in enumerate(λ_seq):
        P = np.array([[1 - λ, λ], [0, 1]])
        m = old.RecurCompetitive(s_np, P, ys_np)
        αs0[i] = m.wealth_distribution(0)
        αs1[i] = m.wealth_distribution(1)
    return αs0, αs1


s_j = jnp.asarray(s_np, float)
ys_j = jnp.asarray(ys_np)
λ_j = jnp.asarray(λ_seq)


@jax.jit
def new_sweep():
    def body(i, carry):
        a0, a1 = carry
        λ = λ_j[i]
        P = jnp.array([[1 - λ, λ], [0., 1.]])
        m0 = new.compute_rc_model(s_j, P, ys_j, s0_idx=0)
        m1 = new.compute_rc_model(s_j, P, ys_j, s0_idx=1)
        return a0.at[i].set(m0.α), a1.at[i].set(m1.α)
    a0 = jnp.empty((100, 2)); a1 = jnp.empty((100, 2))
    return jax.lax.fori_loop(0, 100, body, (a0, a1))


def med(fn, repeat, number=1):
    xs = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        for _ in range(number):
            r = fn()
        xs.append((time.perf_counter() - t0) / number)
    return statistics.median(xs), r


def main():
    t_old, _ = med(old_sweep, repeat=7)

    # cold (includes compile of the whole sweep)
    new.compute_rc_model._clear_cache()
    t0 = time.perf_counter()
    r = new_sweep(); jax.block_until_ready(r)
    t_new_cold = time.perf_counter() - t0

    # warm
    def warm():
        r = new_sweep(); jax.block_until_ready(r); return r
    t_new_warm, _ = med(warm, repeat=11, number=3)

    out = {
        "old_python_loop_s": t_old,
        "jax_sweep_cold_s": t_new_cold,
        "jax_sweep_warm_s": t_new_warm,
        "speedup_warm": t_old / t_new_warm,
        "speedup_cold": t_old / t_new_cold,
    }
    print(f"  old python loop   = {t_old*1e3:8.3f} ms")
    print(f"  jax sweep (cold)  = {t_new_cold*1e3:8.3f} ms  "
          f"({out['speedup_cold']:.2f}x vs numpy)")
    print(f"  jax sweep (warm)  = {t_new_warm*1e3:8.3f} ms  "
          f"({out['speedup_warm']:.2f}x vs numpy)")
    with open(os.path.join(RESULTS, "sweep.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
