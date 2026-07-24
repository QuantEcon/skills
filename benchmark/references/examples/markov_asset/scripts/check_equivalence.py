"""
Numerical-equivalence check: OLD (NumPy) vs NEW (JAX) markov_asset code,
using the SAME model/parameter combinations the lecture actually runs:

  * tree_price   -- default model (β=0.96), risk-aversion sweep γ∈{1.2..2.0}
  * consol_price -- β=0.9 model, ζ=1.0
  * call_option  -- β=0.9 model, ζ=1.0, strike=40  (SHIPPED VERSION CRASHES:
                    NameError `err`; we also compare a bug-patched copy)
  * exercise model (n=5 custom chain, β=0.94, γ=2, g=identity):
                    tree_price, consol_price, finite_call_option (k=5,25),
                    call_option (patched)

Run with JAX_ENABLE_X64=1 to separate genuine logic differences from the
float32-vs-float64 gap (the lecture ships float32).

Output: results/equivalence_x64_<bool>.json + stdout.
"""
import json
import os
import numpy as np
import jax
import jax.numpy as jnp
import quantecon as qe

import model_old as old
import model_new as new

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS, exist_ok=True)
ATOL, RTOL = 1e-5, 1e-4


def new_call_option_fixed(ap, ζ, p_s, ϵ=1e-7):
    "NEW call_option with the stray err.throw() removed."
    β, γ, P, G = ap.β, ap.γ, ap.mc.P, ap.G
    M = P * G ** (- γ)
    new.test_stability(M, β)
    p = new.consol_price(ap, ζ)
    n = M.shape[0]
    w = jnp.zeros(n)

    def step(state):
        w, _ = state
        w_new = jnp.maximum(β * M @ w, p - p_s)
        return (w_new, jnp.amax(jnp.abs(w - w_new)))

    def cond(state):
        _, e = state
        return e > ϵ
    final_w, _ = jax.lax.while_loop(cond, step, (w, ϵ + 1))
    return final_w


new_call_fixed_jit = jax.jit(new.checkify.checkify(new_call_option_fixed))


def cmp(a, b):
    a, b = np.asarray(a), np.asarray(b)
    try:
        return {"match": bool(np.allclose(a, b, atol=ATOL, rtol=RTOL)),
                "max_abs_err": float(np.max(np.abs(a - b)))}
    except Exception:
        return {"match": False, "max_abs_err": float("nan")}


def exercise_models():
    n = 5
    P = np.full((n, n), 0.0125)
    P[range(n), range(n)] += 1 - P.sum(1)
    s = np.array([0.95, 0.975, 1.0, 1.025, 1.05])
    ap_o = old.AssetPriceModel(β=0.94, mc=qe.MarkovChain(P, state_values=s),
                               γ=2.0, g=lambda x: x)
    mc_n = new.MarkovChain(P=jnp.array(P), state_values=jnp.array(s))
    ap_n = new.create_customized_ap_model(mc=mc_n, g=lambda x: x, β=0.94, γ=2.0)
    return ap_o, ap_n


def main():
    r = {}

    # A. tree_price, default model, gamma sweep
    tree = {}
    for γ in [1.2, 1.4, 1.6, 1.8, 2.0]:
        v_o = old.tree_price(old.AssetPriceModel(γ=γ))
        ap_n = new.create_customized_ap_model(new.create_ap_model().mc, γ=γ)
        err, v_n = new.tree_price_jit(ap_n); err.throw()
        tree[f"γ={γ}"] = cmp(v_o, v_n)
    r["tree_price_default_sweep"] = tree

    # B. consol_price, β=0.9 model
    ap_o9 = old.AssetPriceModel(β=0.9)
    ap_n9 = new.create_ap_model(β=0.9)
    err, p_n = new.consol_price_jit(ap_n9, 1.0); err.throw()
    r["consol_price_beta0.9"] = cmp(old.consol_price(ap_o9, 1.0), p_n)

    # C. call_option, β=0.9 model  (shipped crashes -> compare patched)
    try:
        new.call_option_jit(ap_n9, 1.0, 40.0)
        shipped = {"runs": True, "error": None}
    except Exception as e:
        shipped = {"runs": False, "error": f"{type(e).__name__}: {e}"}
    err, w_fix = new_call_fixed_jit(ap_n9, 1.0, 40.0); err.throw()
    r["call_option_beta0.9"] = {
        "shipped": shipped,
        "patched_vs_numpy": cmp(old.call_option(ap_o9, 1.0, 40.0), w_fix)}

    # D/E. exercise model (n=5, β=0.94)
    ap_o, ap_n = exercise_models()
    err, v_n = new.tree_price_jit(ap_n); err.throw()
    err, p_n = new.consol_price_jit(ap_n, 1.0); err.throw()
    ex = {"tree_price": cmp(old.tree_price(ap_o), v_n),
          "consol_price": cmp(old.consol_price(ap_o, 1.0), p_n)}
    for k in (5, 25):
        err, w_n = new.finite_call_option_jit(ap_n, 1.0, 150.0, k); err.throw()
        ex[f"finite_call_k{k}"] = cmp(
            old.finite_horizon_call_option(ap_o, 1.0, 150.0, k), w_n)
    err, w_fix = new_call_fixed_jit(ap_n, 1.0, 150.0); err.throw()
    ex["call_option_patched"] = cmp(old.call_option(ap_o, 1.0, 150.0), w_fix)
    r["exercise_model"] = ex

    x64 = jax.config.read("jax_enable_x64")
    r["_meta"] = {"jax_enable_x64": x64, "atol": ATOL, "rtol": RTOL}

    # print
    print(f"jax_enable_x64 = {x64}")
    worst = 0.0
    def show(name, d):
        nonlocal worst
        worst = max(worst, d["max_abs_err"])
        print(f"  {name:34s} match={d['match']!s:5s}  max|Δ|={d['max_abs_err']:.2e}")
    print(" tree_price (default sweep):")
    for k, d in r["tree_price_default_sweep"].items():
        show("   " + k, d)
    show("consol_price (β=0.9)", r["consol_price_beta0.9"])
    print(f"  call_option (β=0.9) SHIPPED runs = {shipped['runs']}"
          + ("" if shipped["runs"] else f"  <-- {shipped['error']}"))
    show("call_option (β=0.9) patched", r["call_option_beta0.9"]["patched_vs_numpy"])
    print(" exercise model (n=5, β=0.94):")
    for k in ("tree_price", "consol_price", "finite_call_k5",
              "finite_call_k25", "call_option_patched"):
        show("   " + k, r["exercise_model"][k])
    print(f"\n worst max|Δ| across working assets = {worst:.2e}")

    with open(os.path.join(RESULTS, f"equivalence_x64_{x64}.json"), "w") as f:
        json.dump(r, f, indent=2)


if __name__ == "__main__":
    main()
