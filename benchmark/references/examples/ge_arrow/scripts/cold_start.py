"""
Measure GENUINE cold-start latency in a fresh interpreter.

Run as a one-shot process: import time is excluded, but the first
trace+compile of `compute_rc_model` for the n=2 lecture economy is included.
This is what a reader waits for the first time a JAX cell executes, and again
each time a new `s0_idx` / `T` / shape is requested (static args -> recompile).

Prints a single JSON line consumed by run_all.py.
"""
import json
import sys
import time

mode = sys.argv[1] if len(sys.argv) > 1 else "jax_first"

import numpy as np

if mode == "numpy":
    import model_old as old
    s = np.array([0, 1]); P = np.array([[.5, .5], [.5, .5]])
    ys = np.empty((2, 2)); ys[:, 0] = 1 - s; ys[:, 1] = s
    t0 = time.perf_counter()
    m = old.RecurCompetitive(s, P, ys)
    m.wealth_distribution(0); m.continuation_wealths(); m.value_functionss()
    t1 = time.perf_counter()
    print(json.dumps({"mode": mode, "first_call_s": t1 - t0}))

else:
    import jax
    import jax.numpy as jnp
    import model_new as new
    s = jnp.array([0., 1.]); P = jnp.array([[.5, .5], [.5, .5]])
    ys = jnp.array([[1., 0.], [0., 1.]])
    t0 = time.perf_counter()
    m = new.compute_rc_model(s, P, ys, s0_idx=0, T=0)
    jax.block_until_ready(m.J)
    t1 = time.perf_counter()
    # second call at a NEW static arg (s0_idx=1) -> recompiles
    t2 = time.perf_counter()
    m2 = new.compute_rc_model(s, P, ys, s0_idx=1, T=0)
    jax.block_until_ready(m2.J)
    t3 = time.perf_counter()
    print(json.dumps({"mode": mode,
                      "first_call_s": t1 - t0,
                      "recompile_new_s0idx_s": t3 - t2}))
