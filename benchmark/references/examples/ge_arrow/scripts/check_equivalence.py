"""
Numerical-equivalence check between the OLD (NumPy) and NEW (JAX) versions of
the Arrow-securities model.

For every example economy that appears in the lecture we build both models and
compare the equilibrium objects (Q, R, A, V, α, ψ, J). This answers the most
basic evaluation question: *does the rewrite still compute the same economics?*

Output: results/equivalence.json (default dtype) or results/equivalence_x64.json
(when run with JAX_ENABLE_X64=1), plus a human-readable summary on stdout — one
file per precision regime, so the x64 run never clobbers the as-shipped run.
"""

import json
import os
import numpy as np
import jax
import jax.numpy as jnp

import model_old as old
import model_new as new

RESULTS = os.path.join(os.path.dirname(__file__), "..", "results")
os.makedirs(RESULTS, exist_ok=True)

# Objects compared. The OLD API requires calling stateful methods in order, so
# we wrap a helper that reproduces what the lecture does.
ATOL = 1e-6
RTOL = 1e-5


def run_old(s, P, ys, s0_idx=0, T=None):
    m = old.RecurCompetitive(np.asarray(s), np.asarray(P), np.asarray(ys), T=T)
    α = m.wealth_distribution(s0_idx)
    ψ = m.continuation_wealths()
    J = m.value_functionss()
    return {
        "Q": np.asarray(m.Q), "R": np.asarray(m.R), "A": np.asarray(m.A),
        "V": np.asarray(m.V[-1]), "α": np.asarray(α),
        "ψ": np.asarray(ψ if T is None else ψ[-1]),
        "J": np.asarray(J if T is None else J[-1]),
    }


def run_new(s, P, ys, s0_idx=0, T=None):
    Tn = 0 if T is None else T
    m = new.compute_rc_model(jnp.asarray(s, dtype=float),
                             jnp.asarray(P, dtype=float),
                             jnp.asarray(ys, dtype=float),
                             s0_idx=s0_idx, T=Tn)
    return {
        "Q": np.asarray(m.Q), "R": np.asarray(m.R), "A": np.asarray(m.A),
        "V": np.asarray(m.V[-1]), "α": np.asarray(m.α),
        "ψ": np.asarray(m.ψ if T is None else m.ψ[-1]),
        "J": np.asarray(m.J if T is None else m.J[-1]),
    }


def examples():
    # Example 1
    s = [0, 1]; P = [[.5, .5], [.5, .5]]
    ys = np.empty((2, 2)); ys[:, 0] = 1 - np.array(s); ys[:, 1] = s
    yield "ex1_s0", dict(s=s, P=P, ys=ys.copy(), s0_idx=0)
    yield "ex1_s1", dict(s=s, P=P, ys=ys.copy(), s0_idx=1)

    # Example 2
    s = [1, 2]; P = [[.5, .5], [.5, .5]]
    ys = np.empty((2, 2)); ys[:, 0] = 1.5; ys[:, 1] = s
    yield "ex2_s0", dict(s=s, P=P, ys=ys.copy(), s0_idx=0)
    yield "ex2_s1", dict(s=s, P=P, ys=ys.copy(), s0_idx=1)

    # Example 3
    s = [1, 2]; λ = 0.9; P = [[1 - λ, λ], [0, 1]]
    ys = np.empty((2, 2)); ys[:, 0] = [1, 0]; ys[:, 1] = [0, 1]
    yield "ex3_s0", dict(s=s, P=P, ys=ys.copy(), s0_idx=0)
    yield "ex3_s1", dict(s=s, P=P, ys=ys.copy(), s0_idx=1)

    # Example 4
    s = [1, 2, 3]; λ = μ = .9; δ = .05
    P = [[1 - λ, λ, 0], [μ / 2, μ, μ / 2], [(1 - δ) / 2, (1 - δ) / 2, δ]]
    ys = np.empty((3, 2)); ys[:, 0] = [.25, .75, .2]; ys[:, 1] = [1.25, .25, .2]
    for i in range(3):
        yield f"ex4_s{i}", dict(s=s, P=P, ys=ys.copy(), s0_idx=i)

    # Finite horizon (Example 1, T=10)
    s = [0, 1]; P = [[.5, .5], [.5, .5]]
    ys = np.empty((2, 2)); ys[:, 0] = 1 - np.array(s); ys[:, 1] = s
    yield "ex1_finite_T10_s0", dict(s=s, P=P, ys=ys.copy(), s0_idx=0, T=10)
    yield "ex1_finite_T10_s1", dict(s=s, P=P, ys=ys.copy(), s0_idx=1, T=10)


def main():
    report = {}
    all_ok = True
    for name, kw in examples():
        o = run_old(**kw)
        nw = run_new(**kw)
        per_obj = {}
        ok = True
        for key in o:
            a, b = o[key], nw[key]
            try:
                close = bool(np.allclose(a, b, atol=ATOL, rtol=RTOL))
                maxerr = float(np.max(np.abs(a - b)))
            except Exception as e:  # shape mismatch etc.
                close, maxerr = False, float("nan")
            per_obj[key] = {"match": close, "max_abs_err": maxerr}
            ok = ok and close
        report[name] = {"ok": ok, "objects": per_obj}
        all_ok = all_ok and ok
        flag = "OK " if ok else "FAIL"
        worst = max((v["max_abs_err"] for v in per_obj.values()
                     if v["max_abs_err"] == v["max_abs_err"]), default=float("nan"))
        print(f"[{flag}] {name:22s}  max|Δ| = {worst:.2e}")

    x64 = bool(jax.config.jax_enable_x64)
    report["_summary"] = {"all_equivalent": all_ok, "atol": ATOL, "rtol": RTOL,
                          "jax_enable_x64": x64}
    fname = "equivalence_x64.json" if x64 else "equivalence.json"
    with open(os.path.join(RESULTS, fname), "w") as f:
        json.dump(report, f, indent=2)
    print("\nALL EQUIVALENT:", all_ok)


if __name__ == "__main__":
    main()
