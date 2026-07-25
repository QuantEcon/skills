"""
Scoring engine / CLI.  Applies the shared rubric (rubric.py) to one lecture's
evidence and writes an auditable scorecard.

Usage:
    python scripts/scoring/score.py <lecture-dir>
    # e.g. python scripts/scoring/score.py references/examples/ge_arrow

It reads   <lecture-dir>/evidence.json  (inputs + citations; filled from results/)
and writes <lecture-dir>/results/scorecard.json  and prints the derivation table.

The score of every dimension is COMPUTED here from the evidence via rubric.py —
no score is ever written by hand. To change a score you change the measured
metric or a checklist answer in evidence.json, or the standard in rubric.py.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rubric  # noqa: E402

# Evidence keys that are provenance/prose, not scored inputs.
_NON_INPUT_KEYS = ("citations", "source", "lecture", "branch")


def _perturbations(evidence):
    """Yield (dotted-path, old, new, mutated-evidence) — one input changed per
    yield: booleans flipped; integer counts ±1; measured floats ±10%."""
    def walk(node, path):
        for k, v in node.items():
            if k.startswith("_") or k in _NON_INPUT_KEYS:
                continue
            p = path + [k]
            if isinstance(v, dict):
                yield from walk(v, p)
            elif isinstance(v, bool):
                yield p, v, [not v]
            elif isinstance(v, int):
                yield p, v, [v - 1, v + 1]
            elif isinstance(v, float):
                yield p, v, [v * 0.9, v * 1.1]

    for path, old, alts in walk(evidence, []):
        for alt in alts:
            mutated = copy.deepcopy(evidence)
            node = mutated
            for k in path[:-1]:
                node = node[k]
            node[path[-1]] = alt
            yield ".".join(path), old, alt, mutated


def sensitivity(evidence, base):
    """One-flip sensitivity stamp: is the *final* verdict (band after gating,
    plus the no-conversion flag) stable under single-input perturbations?"""
    outcome0 = (base["no_conversion"], base["band_verdict"])
    tested, skipped, flips = 0, [], []
    for label, old, new, mutated in _perturbations(evidence):
        try:
            r = rubric.score_all(mutated)
        except Exception as exc:
            # A perturbation that breaks scoring cannot be deciding — but it is
            # also not evidence of stability, so it is reported rather than
            # silently counted in the denominator the stamp is judged on.
            skipped.append({"input": label, "error": f"{type(exc).__name__}: {exc}"})
            continue
        tested += 1
        if (r["no_conversion"], r["band_verdict"]) != outcome0:
            flips.append({
                "input": label, "from": old, "to": new, "total": r["total"],
                "outcome": (("no-conversion; " if r["no_conversion"] else "")
                            + r["band_verdict"]),
            })
    # A verdict already in the bottom band cannot be perturbed downward: no
    # single input can make "net regression" worse. So "no deciding flips"
    # there is partly the band's geometry rather than the evidence's strength —
    # only upward moves were ever available to the search. Reporting that as
    # plain "robust" asserts a support the run did not demonstrate, and
    # SKILL.md carries the stamp verbatim into the report.
    floored = base.get("band_index") == 0
    if flips:
        stamp, note = "fragile", ""
    elif floored:
        stamp = "robust-at-floor"
        note = ("no perturbation changed the outcome, but the verdict is "
                "already in the bottom band, where no single input can make it "
                "worse — only upward moves were available to this search, so "
                "the stability is partly structural, not purely evidential")
    else:
        stamp, note = "robust", ""

    return {"stamp": stamp, "stamp_note": note,
            "perturbations_tested": tested, "deciding_flips": flips,
            "perturbations_skipped": skipped}


def main(lecture_dir):
    lec_dir = os.path.abspath(lecture_dir)
    lecture = os.path.basename(lec_dir)
    ev_path = os.path.join(lec_dir, "evidence.json")
    if not os.path.exists(ev_path):
        sys.exit(f"no evidence file at {ev_path}")
    with open(ev_path, encoding="utf-8") as f:
        evidence = json.load(f)

    # The authoring contracts are enforced, not just documented: every scored
    # input the verdict gates read must be present, and a structural criterion
    # that moves a score up must say what it rests on.
    problems = rubric.validate_evidence(evidence)
    if problems:
        sys.exit(f"evidence.json is not valid ({len(problems)} problem(s)):"
                 "\n  - " + "\n  - ".join(problems))

    result = rubric.score_all(evidence)
    sens = sensitivity(evidence, result)

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
    skipped = sens["perturbations_skipped"]
    print(f"SENSITIVITY: {sens['stamp']} "
          f"({sens['perturbations_tested']} single-input perturbations scored"
          + (f"; {len(skipped)} skipped — see scorecard.json" if skipped else "")
          + ")")
    if sens["stamp_note"]:
        print(f"     └ {sens['stamp_note']}")
    for fl in sens["deciding_flips"]:
        print(f"     └ {fl['input']}: {fl['from']} → {fl['to']} "
              f"⇒ total {fl['total']:.2f}, {fl['outcome']}")

    out = {
        "lecture": lecture,
        "branch": evidence.get("branch"),
        "weighted_total_out_of_5": result["total"],
        "verdict": result["verdict"],
        "band_verdict": result["band_verdict"],
        "verdict_gate": result["verdict_gate"],
        "no_conversion": result["no_conversion"],
        "sensitivity": sens,
        "dimensions": result["rows"],
        "_note": "Scores are computed by scripts/scoring/rubric.py from "
                 f"{lecture}/evidence.json; do not edit by hand.",
    }
    res_dir = os.path.join(lec_dir, "results")
    os.makedirs(res_dir, exist_ok=True)
    dst = os.path.join(res_dir, "scorecard.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nwrote {os.path.relpath(dst)}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/scoring/score.py <lecture-dir>")
    main(sys.argv[1])
