"""
Run the whole evaluation pipeline and regenerate everything in ../results/.

Usage:
    python run_all.py

Requires the `quantecon` conda env (jax 0.4.x, numpy 2.x). See README.md.
"""
import json
import subprocess
import sys
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
K_AS_USED = 3   # fresh-process repeats per as-used side (v2: median, not a single pass)


def median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0

# (title, command, results-file to aggregate the script's JSON line into or None)
STEPS = [
    ("Numerical equivalence", "check_equivalence.py", None),
    ("Static metrics", "static_metrics.py", None),
    ("Performance benchmark", "benchmark.py", None),
    ("Cold-start (numpy)", "cold_start.py numpy", "cold_start.json"),
    ("Cold-start (jax)", "cold_start.py jax_first", "cold_start.json"),
    ("Lambda-sweep benchmark", "sweep_bench.py", None),
    ("As-used total (numpy)", "as_used_total.py numpy", "as_used.json"),
    ("As-used total (jax)", "as_used_total.py jax", "as_used.json"),
    # HIGH-end efficiency calibration is shared, not lecture-specific:
    # see scripts/calibration/bellman_bench.py
]

collected = {}
failed = []
for title, cmd, agg in STEPS:
    print("\n" + "=" * 70)
    print("==", title)
    print("=" * 70)
    parts = cmd.split()
    argv = [PY, os.path.join(HERE, parts[0])] + parts[1:]
    if agg is None:
        p = subprocess.run(argv, cwd=HERE, check=False)
        if p.returncode:
            failed.append(title)
        continue
    # Persist the script's JSON line (these run as fresh processes and only
    # print their result; the headline as-used metric must not live on the
    # console alone). As-used steps repeat K_AS_USED times so the headline
    # metric is a median of fresh-process runs, never a single pass.
    reps = K_AS_USED if agg == "as_used.json" else 1
    for _ in range(reps):
        p = subprocess.run(argv, cwd=HERE, check=False, capture_output=True,
                           text=True)
        sys.stdout.write(p.stdout)
        if p.stderr:
            sys.stderr.write(p.stderr)
        if p.returncode:
            failed.append(title)
            break
        for line in reversed(p.stdout.strip().splitlines()):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if not isinstance(rec, dict):
                continue  # a stray scalar/list line is not a result record
            bucket = collected.setdefault(agg, {})
            key = rec.get("mode", "?")
            if agg == "as_used.json":
                bucket.setdefault(key, dict(rec, runs=[]))["runs"].append(
                    rec["total_s"])
            else:
                if key in bucket:
                    print(f"WARNING: duplicate mode {key!r} for {agg}",
                          file=sys.stderr)
                bucket[key] = rec
            break

RES = os.path.join(os.path.dirname(HERE), "results")
os.makedirs(RES, exist_ok=True)
for fname, recs in collected.items():
    modes = list(recs)
    if fname == "as_used.json" and "numpy" in recs and len(modes) == 2:
        other = next(m for m in modes if m != "numpy")
        a, b = recs["numpy"], recs[other]
        if a.get("runs") and b.get("runs"):
            a["total_s"] = median(a["runs"])
            b["total_s"] = median(b["runs"])
            recs["as_used_speedup"] = a["total_s"] / b["total_s"]
            recs["as_used_speedup_runs"] = [x / y
                                            for x, y in zip(a["runs"], b["runs"])]
            recs["baseline_as_used_seconds"] = a["total_s"]
    with open(os.path.join(RES, fname), "w", encoding="utf-8") as f:
        json.dump(recs, f, indent=2)
    print(f"wrote results/{fname}")

LEC_DIR = os.path.dirname(HERE)                       # this example's folder
# Shared engine location: the installed plugin root when the skill drives an
# evaluation from a user workspace; falls back to this repo's layout.
PLUGIN = (os.environ.get("CLAUDE_PLUGIN_ROOT")
          or os.path.dirname(os.path.dirname(os.path.dirname(LEC_DIR))))

# Provenance stamp (shared: scripts/scoring/env_stamp.py — the seed of the
# QuantEcon/meta#335 result + environment-descriptor schema). Failed step
# titles are recorded so a partial run cannot claim full provenance.
subprocess.run([PY, os.path.join(PLUGIN, "scripts", "scoring", "env_stamp.py"),
                LEC_DIR] + failed, check=False)

# Scoring is shared across lectures: fill ../evidence.json from the results
# above, then apply the common rubric (scripts/scoring/rubric.py) via the engine.
print("\n" + "=" * 70 + "\n== Scorecard (shared rubric)\n" + "=" * 70)
subprocess.run([PY, os.path.join(PLUGIN, "scripts", "scoring", "score.py"),
                LEC_DIR], check=False)
