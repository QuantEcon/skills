"""
Static code metrics for the OLD and NEW implementations.

Computes objective, reproducible numbers used by several rubric dimensions:
  * code size (non-blank, non-comment lines in the model definition)
  * number of def/functions and maximum lexical nesting depth
  * docstring coverage
  * "concept surface" -- count of advanced-API tokens a reader must understand
  * number of explicit loops
  * call-site ergonomics -- how many statements the lecture needs to obtain one
    full set of results (α, ψ, J)

Source of truth = the two extracted modules (model_old.py / model_new.py),
which are verbatim copies of the lecture code (see their headers).

Output: results/static_metrics.json + stdout table.
"""
import ast
import json
import os
import re

HERE = os.path.dirname(__file__)
RESULTS = os.path.join(HERE, "..", "results")
os.makedirs(RESULTS, exist_ok=True)

# Tokens that represent a *concept a reader must already understand* to follow
# the code. NumPy-side and JAX-side, scored symmetrically.
CONCEPTS = {
    "old": [
        r"\bclass\b", r"def __init__", r"self\.", r"@", r"for .+ in ",
        r"np\.linalg\.inv", r"np\.empty", r"\.dot\(", r"@",
    ],
    "new": [
        r"NamedTuple", r"@partial", r"jax\.jit", r"static_argnames",
        r"jax\.lax\.fori_loop", r"jax\.lax\.cond", r"\.at\[", r"\.set\(",
        r"jnp\.", r"def body_fun", r"carry",
    ],
}

# Distinct prerequisite *ideas* (deduplicated, hand-curated from the token hits).
PREREQS = {
    "old": ["Python class / OOP", "__init__ constructor", "instance state (self.)",
            "NumPy arrays & slicing", "matrix @ / .dot", "np.linalg.inv",
            "Python for-loops"],
    "new": ["Python class / OOP (NamedTuple)", "immutable NamedTuple",
            "typing annotations", "functools.partial", "jax.jit & tracing",
            "static_argnames & recompilation", "functional purity (no in-place)",
            "jnp vs np", "jax.lax.fori_loop (carry)", "jax.lax.cond",
            "functional array update .at[].set()", "nested closures as sub-fns",
            "float32 default / x64 flag"],
}


def code_lines(src):
    n = 0
    for line in src.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        n += 1
    return n


def max_nesting(tree):
    """Maximum nesting depth of def/for/if/with within function bodies."""
    best = 0

    def walk(node, depth):
        nonlocal best
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.For, ast.While,
                                  ast.If, ast.With)):
                best = max(best, depth + 1)
                walk(child, depth + 1)
            else:
                walk(child, depth)

    for node in tree.body:
        walk(node, 0)
    return best


def count_defs_and_docs(tree):
    ndef, ndoc = 0, 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            ndef += 1
            if ast.get_docstring(node):
                ndoc += 1
    return ndef, ndoc


def count_loops(tree):
    return sum(isinstance(n, (ast.For, ast.While)) for n in ast.walk(tree))


def concept_hits(src, patterns):
    return sum(len(re.findall(p, src)) for p in patterns)


def analyze(path, key):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    ndef, ndoc = count_defs_and_docs(tree)
    return {
        "code_lines": code_lines(src),
        "n_defs": ndef,
        "docstring_coverage": round(ndoc / ndef, 2) if ndef else 0,
        "max_nesting_depth": max_nesting(tree),
        "explicit_loops": count_loops(tree),
        "concept_token_hits": concept_hits(src, CONCEPTS[key]),
        "n_prerequisite_concepts": len(PREREQS[key]),
        "prerequisite_concepts": PREREQS[key],
    }


def main():
    old = analyze(os.path.join(HERE, "model_old.py"), "old")
    new = analyze(os.path.join(HERE, "model_new.py"), "new")

    # Call-site ergonomics: statements needed to get α, ψ, J for one economy.
    # OLD: construct + 3 stateful method calls in order.   NEW: 1 call.
    old["statements_for_one_result"] = 4
    new["statements_for_one_result"] = 1

    out = {"old": old, "new": new}
    keys = ["code_lines", "n_defs", "docstring_coverage", "max_nesting_depth",
            "explicit_loops", "concept_token_hits", "n_prerequisite_concepts",
            "statements_for_one_result"]
    print(f"{'metric':30s} {'OLD(numpy)':>12s} {'NEW(jax)':>12s}")
    print("-" * 56)
    for k in keys:
        print(f"{k:30s} {str(old[k]):>12s} {str(new[k]):>12s}")

    with open(os.path.join(RESULTS, "static_metrics.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nwrote results/static_metrics.json")


if __name__ == "__main__":
    main()
