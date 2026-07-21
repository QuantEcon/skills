"""
Static code metrics for the OLD and NEW markov_asset implementations
(same methodology as the ge_arrow evaluation).

Output: results/static_metrics.json + stdout.
"""
import ast
import json
import os
import re

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "..", "results")
os.makedirs(RESULTS, exist_ok=True)

PREREQS = {
    "old": ["Python class / OOP", "__init__ constructor", "instance state (self.)",
            "NumPy arrays", "matrix @ / solve", "np.linalg eigvals/solve",
            "Python while/for loops", "raise/except for errors"],
    "new": ["NamedTuple (2 of them)", "typing annotations", "factory functions",
            "jnp vs np", "jax.jit & tracing", "float32 default / x64 flag",
            "jax.experimental.checkify", "checkify.check contract",
            "checkified call returns (err, val) tuple", "err.throw()",
            "jax.lax.while_loop (cond/body/carry)", "jax.lax.fori_loop",
            "functional array update .at[].set()"],
}


def code_lines(src):
    return sum(1 for ln in src.splitlines()
               if ln.strip() and not ln.strip().startswith("#"))


def max_nesting(tree):
    best = 0
    def walk(node, d):
        nonlocal best
        for c in ast.iter_child_nodes(node):
            if isinstance(c, (ast.FunctionDef, ast.For, ast.While, ast.If, ast.With)):
                best = max(best, d + 1); walk(c, d + 1)
            else:
                walk(c, d)
    for n in tree.body:
        walk(n, 0)
    return best


def defs_docs(tree):
    nd = ndoc = 0
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            nd += 1
            if ast.get_docstring(n):
                ndoc += 1
    return nd, ndoc


def loops(tree):
    return sum(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree))


def analyze(path, key):
    src = open(path, encoding="utf-8").read()
    t = ast.parse(src)
    nd, ndoc = defs_docs(t)
    return {"code_lines": code_lines(src), "n_defs": nd,
            "docstring_coverage": round(ndoc / nd, 2) if nd else 0,
            "max_nesting_depth": max_nesting(t), "explicit_loops": loops(t),
            "n_prerequisite_concepts": len(PREREQS[key]),
            "prerequisite_concepts": PREREQS[key]}


def main():
    old = analyze(os.path.join(HERE, "model_old.py"), "old")
    new = analyze(os.path.join(HERE, "model_new.py"), "new")
    # calls to obtain one priced asset (e.g. call option) + handle result
    # (key name matches EVIDENCE_TEMPLATE.json / the ge_arrow template)
    #   OLD: build model, call function -> 2
    #   NEW: build model, call *_jit -> (err,val), err.throw() -> 3
    old["statements_for_one_result"] = 2
    new["statements_for_one_result"] = 3
    out = {"old": old, "new": new}
    keys = ["code_lines", "n_defs", "docstring_coverage", "max_nesting_depth",
            "explicit_loops", "n_prerequisite_concepts", "statements_for_one_result"]
    print(f"{'metric':30s} {'OLD':>10s} {'NEW':>10s}")
    print("-" * 52)
    for k in keys:
        print(f"{k:30s} {str(old[k]):>10s} {str(new[k]):>10s}")
    with open(os.path.join(RESULTS, "static_metrics.json"), "w") as f:
        json.dump(out, f, indent=2)


if __name__ == "__main__":
    main()
