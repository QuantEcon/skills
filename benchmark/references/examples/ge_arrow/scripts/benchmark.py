"""
Performance benchmark: OLD (NumPy) vs NEW (JAX) Arrow-securities model.

We measure three regimes that matter for a *lecture*:

1. "As-used latency"  -- the time a learner actually waits for one result the
   first time a given (shape, static-arg) combination is requested. For JAX this
   INCLUDES tracing + XLA compilation, because every new `s0_idx`/`T`/shape
   triggers a fresh compile (they are static_argnames / shape-dependent).

2. "Warm / amortized" -- repeated calls once compilation is cached. This is the
   regime JAX is designed to win, relevant only if the function is called many
   times at a fixed shape.

3. "Scaling"          -- how warm runtime grows with the number of Markov states
   n, to show the problem size at which JAX's vectorised/compiled execution
   overtakes NumPy.

Output: results/benchmark.json + stdout table.
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


def make_economy(n, K=2, seed=0):
    rng = np.random.default_rng(seed)
    P = rng.random((n, n)); P /= P.sum(axis=1, keepdims=True)
    ys = rng.random((n, K)) + 0.5
    s = np.arange(n)
    return s, P, ys


def time_it(fn, repeat=7, number=1):
    """Return median seconds per call over `repeat` trials of `number` calls."""
    samples = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        for _ in range(number):
            fn()
        t1 = time.perf_counter()
        samples.append((t1 - t0) / number)
    return statistics.median(samples)


def old_call(s, P, ys, s0_idx=0, T=None):
    m = old.RecurCompetitive(s, P, ys, T=T)
    m.wealth_distribution(s0_idx)
    m.continuation_wealths()
    m.value_functionss()
    return m


def new_call(s, P, ys, s0_idx=0, T=0):
    m = new.compute_rc_model(s, P, ys, s0_idx=s0_idx, T=T)
    # force completion of async dispatch
    jax.block_until_ready(m.J)
    return m


def bench_as_used():
    """Latency of a single fresh result at lecture size n=2 (cold for JAX)."""
    s, P, ys = make_economy(2)
    sj, Pj, ysj = jnp.asarray(s, float), jnp.asarray(P), jnp.asarray(ys)

    # NumPy: just one call
    t_old = time_it(lambda: old_call(s, P, ys), repeat=11)

    # JAX cold: clear cache so compilation is included, fresh each trial
    def jax_cold():
        new.compute_rc_model._clear_cache()
        m = new.compute_rc_model(sj, Pj, ysj, s0_idx=0, T=0)
        jax.block_until_ready(m.J)
    t_new_cold = time_it(jax_cold, repeat=7)

    return {"n": 2, "numpy_s": t_old, "jax_cold_s": t_new_cold,
            "slowdown_cold": t_new_cold / t_old}


def bench_warm(n=2):
    s, P, ys = make_economy(n)
    sj, Pj, ysj = jnp.asarray(s, float), jnp.asarray(P), jnp.asarray(ys)
    # warm up compilation
    new_call(sj, Pj, ysj)
    t_old = time_it(lambda: old_call(s, P, ys), repeat=11, number=5)
    t_new = time_it(lambda: new_call(sj, Pj, ysj), repeat=11, number=5)
    return {"n": n, "numpy_s": t_old, "jax_warm_s": t_new,
            "speedup_warm": t_old / t_new}


def bench_scaling():
    rows = []
    for n in [2, 3, 5, 10, 25, 50, 100, 200, 400]:
        s, P, ys = make_economy(n)
        sj, Pj, ysj = jnp.asarray(s, float), jnp.asarray(P), jnp.asarray(ys)
        new_call(sj, Pj, ysj)  # warm
        rep = 7 if n <= 100 else 5
        t_old = time_it(lambda: old_call(s, P, ys), repeat=rep)
        t_new = time_it(lambda: new_call(sj, Pj, ysj), repeat=rep)
        rows.append({"n": n, "numpy_s": t_old, "jax_warm_s": t_new,
                     "speedup_warm": t_old / t_new})
        print(f"  n={n:4d}  numpy={t_old*1e3:9.3f} ms   "
              f"jax_warm={t_new*1e3:9.3f} ms   speedup={t_old/t_new:6.2f}x")
    return rows


def main():
    print("== As-used latency (n=2, JAX cold incl. compile) ==")
    as_used = bench_as_used()
    print(f"  numpy      = {as_used['numpy_s']*1e3:9.3f} ms")
    print(f"  jax cold   = {as_used['jax_cold_s']*1e3:9.3f} ms"
          f"  ({as_used['slowdown_cold']:.0f}x slower than numpy)")

    print("\n== Warm / amortized (compile cached) ==")
    warm = [bench_warm(2), bench_warm(3)]
    for w in warm:
        print(f"  n={w['n']}: numpy={w['numpy_s']*1e3:.4f} ms  "
              f"jax_warm={w['jax_warm_s']*1e3:.4f} ms  "
              f"speedup={w['speedup_warm']:.2f}x")

    print("\n== Scaling (warm) ==")
    scaling = bench_scaling()

    out = {"as_used_latency": as_used, "warm": warm, "scaling": scaling,
           "jax_x64": jax.config.read("jax_enable_x64"),
           "device": str(jax.devices()[0])}
    with open(os.path.join(RESULTS, "benchmark.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote results/benchmark.json")


if __name__ == "__main__":
    main()
