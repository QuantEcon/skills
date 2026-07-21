"""Write <lecture-dir>/results/env.json — the provenance stamp for a measurement run.

Usage:
    python scripts/scoring/env_stamp.py <lecture-dir> [failed-step-title ...]

Seed of the QuantEcon/meta#335 shared result + environment-descriptor schema:
python/platform plus the versions of the measurement-relevant libraries.
Any extra arguments are recorded as `steps_failed`, so a partial run is
self-describing instead of silently claiming full provenance for results
files an earlier environment produced.

Invoked by each example's run_all.py with the interpreter that ran the
measurements (the stamp must describe the measurement environment).
"""
import json
import os
import platform
import sys
from importlib import metadata


def main(lecture_dir, failed):
    info = {"python": sys.version.split()[0],
            "platform": platform.platform(), "machine": platform.machine()}
    for pkg in ("numpy", "jax", "jaxlib", "quantecon"):
        try:
            info[pkg] = metadata.version(pkg)
        except metadata.PackageNotFoundError:
            pass
    if failed:
        info["steps_failed"] = failed
    res = os.path.join(os.path.abspath(lecture_dir), "results")
    os.makedirs(res, exist_ok=True)
    with open(os.path.join(res, "env.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)
    suffix = f"  (steps_failed: {len(failed)})" if failed else ""
    print(f"wrote {os.path.join(res, 'env.json')}{suffix}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/scoring/env_stamp.py <lecture-dir> [failed-step-title ...]")
    main(sys.argv[1], sys.argv[2:])
