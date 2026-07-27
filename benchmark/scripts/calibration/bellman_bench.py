"""
Measured backing for the HIGH-efficiency anchor (score 5).

`aiyagari.md` is JAX on both branches, so there is no numpy baseline inside the
repo. Instead we re-implement *its computational pattern* -- the vectorised
Bellman operator of `aiyagari.md:288-300` solved by value-function iteration on
an `a_size` x `z_size` grid -- in BOTH NumPy and JAX, and time it the way the
lecture actually uses it:

  * one household solve = VFI to convergence (hundreds of jitted iterations);
  * the equilibrium loop re-solves the household problem many times at a FIXED
    shape (here R=20), so JAX's one-time compile is amortised.

This is the regime where JAX is supposed to win, so the measured speedup here
calibrates what "score 5" means for the shared efficiency threshold in
scoring/rubric.py. It is NOT tied to any single lecture; the low-end
calibration is any tiny-model lecture's own as_used_total.py (e.g. ge_arrow,
~45x slower). Run it once (or when hardware changes) to re-check the anchor.

Output: bellman_bench.json (beside this script) + stdout.
"""
import json
import os
import time
import numpy as np
import jax
import jax.numpy as jnp
from functools import partial

jax.config.update("jax_enable_x64", True)

RESULTS = os.path.dirname(__file__)   # write beside this script

A_SIZE, Z_SIZE = 200, 7
β, γ, r, w = 0.96, 2.0, 0.03, 1.0
TOL = 1e-7

rng = np.random.default_rng(0)
a_grid_np = np.linspace(1e-4, 20.0, A_SIZE)
z_grid_np = np.linspace(0.5, 1.5, Z_SIZE)
Π_np = rng.random((Z_SIZE, Z_SIZE)); Π_np /= Π_np.sum(1, keepdims=True)


# ----------------------------- NumPy -----------------------------
def u_np(c):
    return c ** (1 - γ) / (1 - γ)


def bellman_np(v, a_grid, z_grid, Π):
    a = a_grid.reshape(A_SIZE, 1, 1)
    z = z_grid.reshape(1, Z_SIZE, 1)
    ap = a_grid.reshape(1, 1, A_SIZE)
    c = w * z + (1 + r) * a - ap
    vv = v.reshape(1, 1, A_SIZE, Z_SIZE)
    PP = Π.reshape(1, Z_SIZE, 1, Z_SIZE)
    EV = np.sum(vv * PP, axis=-1)
    B = np.where(c > 0, u_np(c) + β * EV, -np.inf)
    return np.max(B, axis=-1)


def solve_np():
    v = np.zeros((A_SIZE, Z_SIZE))
    err, it = 1.0, 0
    while err > TOL and it < 2000:
        v_new = bellman_np(v, a_grid_np, z_grid_np, Π_np)
        err = np.max(np.abs(v_new - v))
        v = v_new
        it += 1
    return v, it


# ----------------------------- JAX -----------------------------
a_grid_j = jnp.asarray(a_grid_np)
z_grid_j = jnp.asarray(z_grid_np)
Π_j = jnp.asarray(Π_np)


def u_j(c):
    return c ** (1 - γ) / (1 - γ)


@jax.jit
def bellman_j(v):
    a = a_grid_j.reshape(A_SIZE, 1, 1)
    z = z_grid_j.reshape(1, Z_SIZE, 1)
    ap = a_grid_j.reshape(1, 1, A_SIZE)
    c = w * z + (1 + r) * a - ap
    vv = v.reshape(1, 1, A_SIZE, Z_SIZE)
    PP = Π_j.reshape(1, Z_SIZE, 1, Z_SIZE)
    EV = jnp.sum(vv * PP, axis=-1)
    B = jnp.where(c > 0, u_j(c) + β * EV, -jnp.inf)
    return jnp.max(B, axis=-1)


@jax.jit
def solve_j():
    def cond(state):
        v, err, it = state
        return (err > TOL) & (it < 2000)

    def body(state):
        v, err, it = state
        v_new = bellman_j(v)
        return v_new, jnp.max(jnp.abs(v_new - v)), it + 1

    v0 = jnp.zeros((A_SIZE, Z_SIZE))
    v, err, it = jax.lax.while_loop(cond, body, (v0, 1.0, 0))
    return v, it


def med(fn, repeat):
    xs = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        r = fn()
        xs.append(time.perf_counter() - t0)
    xs.sort()
    return xs[len(xs) // 2], r


def main():
    # correctness: numpy and jax agree
    v_np, it_np = solve_np()
    v_j, it_j = solve_j(); jax.block_until_ready(v_j)
    max_diff = float(np.max(np.abs(np.asarray(v_j) - v_np)))

    # single solve, numpy
    t_np, _ = med(solve_np, 5)

    # single solve, jax COLD (fresh compile)
    solve_j._clear_cache(); bellman_j._clear_cache()
    t0 = time.perf_counter()
    r = solve_j(); jax.block_until_ready(r)
    t_j_cold = time.perf_counter() - t0

    # single solve, jax WARM
    def warm():
        r = solve_j(); jax.block_until_ready(r); return r
    t_j_warm, _ = med(warm, 9)

    # equilibrium loop: R=20 re-solves at fixed shape
    R = 20
    t0 = time.perf_counter()
    for _ in range(R):
        solve_np()
    eq_np = time.perf_counter() - t0

    solve_j._clear_cache(); bellman_j._clear_cache()
    t0 = time.perf_counter()
    for _ in range(R):
        r = solve_j(); jax.block_until_ready(r)
    eq_j = time.perf_counter() - t0   # includes 1 compile + 20 warm solves

    out = {
        "grid": [A_SIZE, Z_SIZE], "vfi_iters": int(it_np),
        "agree_max_abs": max_diff,
        "single_numpy_s": t_np,
        "single_jax_cold_s": t_j_cold,
        "single_jax_warm_s": t_j_warm,
        "single_speedup_cold": t_np / t_j_cold,
        "single_speedup_warm": t_np / t_j_warm,
        "eq_loop_R": R,
        "eq_numpy_s": eq_np,
        "eq_jax_total_s": eq_j,
        "eq_as_used_speedup": eq_np / eq_j,
    }
    print(f"grid {A_SIZE}x{Z_SIZE}, VFI {it_np} iters, agree to {max_diff:.1e}")
    print(f"single solve : numpy {t_np*1e3:8.2f} ms | "
          f"jax cold {t_j_cold*1e3:8.2f} ms | jax warm {t_j_warm*1e3:8.2f} ms")
    print(f"             : warm speedup = {out['single_speedup_warm']:.1f}x  "
          f"cold speedup = {out['single_speedup_cold']:.2f}x")
    print(f"equilibrium loop (R={R}, the as-used pattern):")
    print(f"             : numpy {eq_np*1e3:8.1f} ms | jax total {eq_j*1e3:8.1f} ms"
          f"  -> as-used speedup = {out['eq_as_used_speedup']:.1f}x")
    with open(os.path.join(RESULTS, "bellman_bench.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
