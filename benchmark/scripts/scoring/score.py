"""
Scoring engine / CLI.  Applies the shared rubric (rubric.py) to one lecture's
evidence and writes an auditable scorecard.

Usage:
    python scoring/score.py <lecture>        # e.g. ge_arrow, markov_asset

It reads   <lecture>/evidence.json      (inputs + citations; filled from results/)
and writes <lecture>/results/scorecard.json  and prints the derivation table.

The score of every dimension is COMPUTED here from the evidence via rubric.py —
no score is ever written by hand. To change a score you change the measured
metric or a checklist answer in evidence.json, or the standard in rubric.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import rubric  # noqa: E402


def main(lecture):
    lec_dir = os.path.join(ROOT, lecture)
    ev_path = os.path.join(lec_dir, "evidence.json")
    if not os.path.exists(ev_path):
        sys.exit(f"no evidence file at {ev_path}")
    with open(ev_path, encoding="utf-8") as f:
        evidence = json.load(f)

    result = rubric.score_all(evidence)

    # ---- print an auditable table ----
    print(f"\nSCORECARD — {lecture}  (branch {evidence.get('branch', '?')})")
    print("=" * 78)
    print(f"{'dimension':34s} {'kind':11s} {'wt':>4s} {'sc':>3s} {'wtd':>5s}")
    print("-" * 78)
    for r in result["rows"]:
        print(f"{r['title']:34s} {r['kind']:11s} {r['weight']:>4.2f} "
              f"{r['score']:>3d} {r['weighted']:>5.2f}")
        print(f"     └ {r['reason']}")
    print("-" * 78)
    print(f"{'WEIGHTED TOTAL':34s} {'':11s} {'':>4s} {'':>3s} {result['total']:>5.2f}")
    print(f"VERDICT: {result['verdict']}")

    out = {
        "lecture": lecture,
        "branch": evidence.get("branch"),
        "weighted_total_out_of_5": result["total"],
        "verdict": result["verdict"],
        "dimensions": result["rows"],
        "_note": "Scores are computed by scoring/rubric.py from "
                 f"{lecture}/evidence.json; do not edit by hand.",
    }
    res_dir = os.path.join(lec_dir, "results")
    os.makedirs(res_dir, exist_ok=True)
    dst = os.path.join(res_dir, "scorecard.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nwrote {os.path.relpath(dst, ROOT)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scoring/score.py <lecture>")
    main(sys.argv[1])
