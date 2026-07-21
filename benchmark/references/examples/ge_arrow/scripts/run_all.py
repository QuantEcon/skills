"""
Run the whole evaluation pipeline and regenerate everything in ../results/.

Usage:
    python run_all.py

Requires the `quantecon` conda env (jax 0.4.x, numpy 2.x). See README.md.
"""
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

STEPS = [
    ("Numerical equivalence", "check_equivalence.py"),
    ("Static metrics", "static_metrics.py"),
    ("Performance benchmark", "benchmark.py"),
    ("Cold-start (numpy)", "cold_start.py numpy"),
    ("Cold-start (jax)", "cold_start.py jax_first"),
    ("Lambda-sweep benchmark", "sweep_bench.py"),
    ("As-used total (numpy)", "as_used_total.py numpy"),
    ("As-used total (jax)", "as_used_total.py jax"),
    # HIGH-end efficiency calibration is shared, not lecture-specific:
    # see scoring/calibration/bellman_bench.py
]

for title, cmd in STEPS:
    print("\n" + "=" * 70)
    print("==", title)
    print("=" * 70)
    parts = cmd.split()
    subprocess.run([PY, os.path.join(HERE, parts[0])] + parts[1:],
                   cwd=HERE, check=False)

# Scoring is shared across lectures: fill ../evidence.json from the results
# above, then apply the common rubric (scoring/rubric.py) via the engine.
print("\n" + "=" * 70 + "\n== Scorecard (shared rubric)\n" + "=" * 70)
ROOT = os.path.dirname(os.path.dirname(HERE))
subprocess.run([PY, os.path.join(ROOT, "scoring", "score.py"), "ge_arrow"],
               cwd=ROOT, check=False)
