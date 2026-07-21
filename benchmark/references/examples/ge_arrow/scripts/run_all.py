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
    # see scripts/calibration/bellman_bench.py
]

for title, cmd in STEPS:
    print("\n" + "=" * 70)
    print("==", title)
    print("=" * 70)
    parts = cmd.split()
    subprocess.run([PY, os.path.join(HERE, parts[0])] + parts[1:],
                   cwd=HERE, check=False)

# Provenance stamp for this measurement run (seed of the QuantEcon/meta#335
# shared result + environment-descriptor schema).
def write_env():
    import json
    import platform
    from importlib import metadata
    info = {"python": sys.version.split()[0],
            "platform": platform.platform(), "machine": platform.machine()}
    for pkg in ("numpy", "jax", "jaxlib", "quantecon"):
        try:
            info[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            pass
    res = os.path.join(os.path.dirname(HERE), "results")
    os.makedirs(res, exist_ok=True)
    with open(os.path.join(res, "env.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)


write_env()

# Scoring is shared across lectures: fill ../evidence.json from the results
# above, then apply the common rubric (scripts/scoring/rubric.py) via the engine.
print("\n" + "=" * 70 + "\n== Scorecard (shared rubric)\n" + "=" * 70)
LEC_DIR = os.path.dirname(HERE)                       # this example's folder
PLUGIN = os.path.dirname(os.path.dirname(os.path.dirname(LEC_DIR)))
subprocess.run([PY, os.path.join(PLUGIN, "scripts", "scoring", "score.py"),
                LEC_DIR], check=False)
