"""
Run the whole markov_asset evaluation pipeline; regenerate ../results/.
Requires the `quantecon` conda env (jax 0.4.x, numpy 2.x, quantecon).
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STEPS = [
    ("Smoke test (does each version run?)", "smoke_test.py"),
    ("Numerical equivalence (float32, as shipped)", "check_equivalence.py"),
    ("Static metrics", "static_metrics.py"),
    ("Scaling benchmark", "benchmark.py"),
    ("As-used total (numpy)", "as_used_total.py numpy"),
    ("As-used total (jax, bug-patched)", "as_used_total.py jax"),
]

for title, cmd in STEPS:
    print("\n" + "=" * 70 + f"\n== {title}\n" + "=" * 70)
    parts = cmd.split()
    subprocess.run([PY, os.path.join(HERE, parts[0])] + parts[1:],
                   cwd=HERE, check=False)

# Scoring is shared across lectures: fill ../evidence.json from the results
# above, then apply the common rubric (scoring/rubric.py) via the engine.
print("\n" + "=" * 70 + "\n== Scorecard (shared rubric)\n" + "=" * 70)
ROOT = os.path.dirname(os.path.dirname(HERE))
subprocess.run([PY, os.path.join(ROOT, "scoring", "score.py"), "markov_asset"],
               cwd=ROOT, check=False)

print("\nNote: to also get the x64 equivalence numbers, run:")
print("  JAX_ENABLE_X64=1 python check_equivalence.py")
