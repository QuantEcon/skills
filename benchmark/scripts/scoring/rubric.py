"""
THE SCORING STANDARD  (single source of truth, shared by every lecture).

This module encodes the rubric described in prose in
../../references/EVALUATION_FRAMEWORK.md
so that a score is a *deterministic function of evidence*, never a hand-typed
number. Nothing here is lecture-specific: the same rubric is applied to every
lecture. Only the per-lecture `evidence.json` changes.

Two kinds of dimension:

  * QUANTITATIVE (correctness, readability, efficiency, ergonomics) — the score
    comes from a measured metric via an explicit threshold table.
  * STRUCTURAL (logic&design, style&idiom, maintainability) — the score comes
    from a fixed 4-item yes/no checklist: score = 1 + (#criteria met), with a
    small number of documented override caps. Every checklist answer in
    evidence.json must carry a citation.

Each scorer returns (score:int, reason:str) so the derivation is auditable.

v2 (2026-07, from the three-way design review): the logic&design bug-cap is
derived from the correctness evidence inside `score_all`; correctness 1/2
gates the verdict band; a "no-conversion" verdict fires on the triage
don't-convert profile; the as-used metric accepts a median-of-runs list.
"""

# ---- weights (sum to 1.0); rationale in EVALUATION_FRAMEWORK.md -------------
WEIGHTS = {
    "correctness":    0.20,
    "readability":    0.25,
    "efficiency":     0.15,
    "logic_design":   0.15,
    "style_idiom":    0.10,
    "ergonomics":     0.10,
    "maintainability": 0.05,
}

TITLES = {
    "correctness":    "Correctness & numerical fidelity",
    "readability":    "Readability & pedagogical clarity",
    "efficiency":     "Computational efficiency (as used)",
    "logic_design":   "Logic & design",
    "style_idiom":    "Coding style & idiom",
    "ergonomics":     "API ergonomics & reusability",
    "maintainability": "Maintainability & robustness",
}

KIND = {
    "correctness": "quantitative", "readability": "quantitative",
    "efficiency": "quantitative", "ergonomics": "quantitative",
    "logic_design": "structural", "style_idiom": "structural",
    "maintainability": "structural",
}

# ---- fixed 4-item checklists for the structural dimensions ------------------
# Each key is a criterion phrased so that TRUE = good. Order is the display order.
CHECKLISTS = {
    "logic_design": [
        "pure_no_order_dependence",   # pure functions; no ordered stateful calls
        "no_global_state",            # no reliance on module/global variables
        "good_algorithmic_choices",   # vectorised where natural; no needless recompute
        "fixes_prior_bugs",           # removes a real bug/smell from the original
    ],
    "style_idiom": [
        "vectorised_where_natural",       # broadcast/einsum, not scalar loops
        "correct_control_flow_primitive", # scan/while_loop/fori_loop used aptly
        "no_anti_idiomatic_constructs",   # no cond-on-static, loop-where-vectorise
        "clean_call_sites_and_naming",    # call sites read cleanly; consistent naming
    ],
    "maintainability": [
        "pure_unit_testable",         # easy to unit-test in isolation
        "dtype_precision_safe",       # x64/float64 enabled; no silent dtype trap
        "no_footgun_for_editors",     # call protocol hard to misuse
        "robust_no_brittle_conditions",  # no reliance on near-critical/low-precision edges
    ],
}


# ---- total → verdict bands -------------------------------------------------
# Ordered worst → best; verdict gating compares indices into this list.
BANDS = [
    "net regression — do not merge as-is",
    "mixed / wash — improvements offset by real regressions; revisit before merging",
    "net positive with fixable regressions — merge after addressing them",
    "clear improvement — merge",
]
SHORT_BANDS = ["net regression", "mixed/wash", "net positive", "clear improvement"]


def band_index(total):
    if total >= 4.0:
        return 3
    if total >= 3.0:
        return 2
    if total >= 2.5:
        return 1
    return 0


def verdict(total):
    return BANDS[band_index(total)]


# Policy floor (a policy choice, anchored not derived): a lecture whose whole
# baseline replay finishes in under this many seconds has no as-used time worth
# buying, so a candidate that is *also slower* as-used earns the
# "no-conversion" verdict regardless of its polish. Reconciles review mode
# with triage — both blind-validated don't-convert baselines (ge_arrow
# 0.028 s, markov_asset 0.087 s) sit far below this floor, the convert case
# (aiyagari pattern, 54.3 s) far above it.
NO_CONVERSION_BASELINE_S = 1.0


def _median(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2.0


# =====================  QUANTITATIVE SCORERS  ===============================
def score_correctness(builds, max_delta_shipped, matches_under_x64):
    """max|Δ| vs the original *as the lecture ships* (float32 unless x64 set)."""
    if not builds:
        return 1, "does not build as shipped → 1 (overrides Δ bands)"
    d = max_delta_shipped
    if not matches_under_x64 and d > 1e-8:
        return 1, f"logic diverges under x64 (max|Δ|={d:.1e}) → wrong economics → 1"
    if d <= 1e-10:
        return 5, f"max|Δ|={d:.1e} ≤ 1e-10 → 5"
    if d <= 1e-8:
        return 4, f"max|Δ|={d:.1e} ≤ 1e-8 → 4"
    if d <= 1e-3:
        return 3, f"logic matches under x64 but ships float32 → drift {d:.1e} (1e-8,1e-3] → 3"
    if d <= 1e-1:
        return 2, f"material drift max|Δ|={d:.1e} (1e-3,1e-1] → 2"
    return 1, f"max|Δ|={d:.1e} > 1e-1 → 1"


def score_readability(delta_prereq_concepts, docstring_cov_new):
    dp = delta_prereq_concepts
    sp = 5 if dp <= 0 else 4 if dp <= 2 else 3 if dp <= 4 else 2 if dp <= 6 else 1
    c = docstring_cov_new
    sd = 5 if c >= 0.80 else 4 if c >= 0.75 else 3 if c >= 0.60 else 2
    s = min(sp, sd)
    return s, (f"Δprereq={dp:+d}→{sp}, docstrings={c:.2f}→{sd}; "
              f"worse-of-two → {s}")


def score_efficiency(as_used_speedup, correct_or_fixable):
    s = as_used_speedup
    if s >= 3:
        return 5, f"as-used speedup {s:.3g}× ≥ 3 → 5"
    if s >= 1.3:
        return 4, f"as-used speedup {s:.3g}× ∈ [1.3,3) → 4"
    if s >= 0.8:
        return 3, f"as-used speedup {s:.3g}× ∈ [0.8,1.3) → 3 (wash)"
    if correct_or_fixable:
        return 2, f"as-used speedup {s:.3g}× < 0.8 (slower) but correct/fixable → 2"
    return 1, f"as-used speedup {s:.3g}× < 0.8 and wrong/unfixable → 1"


def score_ergonomics(statements_for_one_result, fragile_protocol):
    n = statements_for_one_result
    base = 5 if n <= 1 else 4 if n == 2 else 3 if n == 3 else 2
    if fragile_protocol and base > 3:
        return 3, f"{n} statement(s)→{base}, but fragile protocol caps at 3"
    if fragile_protocol:
        return base, f"{n} statement(s) + fragile protocol → {base}"
    return base, f"{n} statement(s) to obtain one result → {base}"


# =====================  STRUCTURAL SCORER  ==================================
def score_structural(dim, criteria, overrides=None):
    """score = 1 + (#criteria met), with documented override caps."""
    overrides = overrides or {}
    keys = CHECKLISTS[dim]
    met = [k for k in keys if criteria.get(k)]
    score = 1 + len(met)
    note = ""
    if dim == "logic_design" and overrides.get("introduces_correctness_bug"):
        derived = overrides.get("_bug_derived_from")
        why = (f"correctness-bug cap derived from correctness evidence: {derived}"
               if derived else "introduces a correctness bug")
        if score > 3:
            note = f" (capped at 3: {why})"
        score = min(score, 3)
    reason = (f"{len(met)}/4 criteria met [{', '.join(met) or 'none'}] "
              f"→ 1+{len(met)}={1+len(met)}{note}")
    return score, reason


# =====================  DRIVER  ============================================
def score_dimension(dim, ev):
    """Dispatch one dimension's evidence dict `ev` to the right scorer."""
    if dim == "correctness":
        return score_correctness(ev["builds"], ev["max_delta_shipped"],
                                 ev["matches_under_x64"])
    if dim == "readability":
        return score_readability(ev["delta_prereq_concepts"],
                                 ev["docstring_cov_new"])
    if dim == "efficiency":
        runs = ev.get("as_used_runs")
        if runs:
            sp = _median(runs)
            s, reason = score_efficiency(sp, ev["correct_or_fixable"])
            per_run = {score_efficiency(r, ev["correct_or_fixable"])[0]
                       for r in runs}
            if len(per_run) > 1:
                reason += (f" [median of {len(runs)} fresh-process runs, spread "
                           f"{min(runs):.3g}–{max(runs):.3g}×; CONTESTED BAND: "
                           f"runs alone would score {sorted(per_run)}]")
            else:
                reason += (f" [median of {len(runs)} fresh-process runs, spread "
                           f"{min(runs):.3g}–{max(runs):.3g}× within one band]")
            return s, reason
        s, reason = score_efficiency(ev["as_used_speedup"],
                                     ev["correct_or_fixable"])
        return s, reason + (" [single-run measurement; the v2 standard is a "
                            "median of ≥3 fresh-process runs — see "
                            "as_used_runs in the evidence template]")
    if dim == "ergonomics":
        return score_ergonomics(ev["statements_for_one_result"],
                                ev["fragile_protocol"])
    # structural
    return score_structural(dim, ev["criteria"],
                            {k: v for k, v in ev.items() if k != "criteria"})


def score_all(evidence):
    """Return the full breakdown for a lecture's `evidence` dict.

    `evidence` has keys "quantitative" and "structural", each mapping a
    dimension id to its evidence dict (see EVIDENCE_TEMPLATE.json).
    """
    merged = {}
    merged.update(evidence.get("quantitative", {}))
    merged.update(evidence.get("structural", {}))

    # ---- derived safety coupling: the logic&design correctness-bug cap
    # follows from the correctness evidence itself, so one forgotten boolean
    # can no longer leave a non-building (or x64-divergent) candidate uncapped.
    corr = merged.get("correctness", {})
    derived = None
    if not corr.get("builds", True):
        derived = "does not build as shipped"
    elif (not corr.get("matches_under_x64", True)
          and corr.get("max_delta_shipped", 0.0) > 1e-8):
        derived = "logic diverges under x64"
    if derived and "logic_design" in merged \
            and not merged["logic_design"].get("introduces_correctness_bug"):
        ld = dict(merged["logic_design"])
        ld["introduces_correctness_bug"] = True
        ld["_bug_derived_from"] = derived
        merged["logic_design"] = ld

    rows, total, scores = [], 0.0, {}
    for dim in WEIGHTS:
        ev = merged[dim]
        s, reason = score_dimension(dim, ev)
        w = WEIGHTS[dim]
        total += w * s
        scores[dim] = s
        rows.append({"dim": dim, "title": TITLES[dim], "kind": KIND[dim],
                     "weight": w, "score": s, "weighted": round(w * s, 3),
                     "reason": reason,
                     "citations": ev.get("citations", ev.get("source"))})
    # Verdict on the rounded total so the band always agrees with the number
    # shown: raw FP sums can land at e.g. 2.4999999999999996 for combinations
    # that are exactly 2.50 in exact arithmetic.
    total = round(total, 2)

    # ---- verdict gates: a candidate whose correctness is broken cannot
    # weighted-average its way into a merge band, whatever its polish.
    base_idx = band_index(total)
    final_idx, gate = base_idx, None
    if scores["correctness"] == 1 and base_idx > 0:
        final_idx = 0
        gate = "correctness 1 caps the verdict at net regression"
    elif scores["correctness"] == 2 and base_idx > 1:
        final_idx = 1
        gate = "correctness 2 caps the verdict at mixed/wash"

    # ---- no-conversion: when the efficiency evidence shows the triage
    # don't-convert profile, the verdict says so instead of scoring the polish.
    eff = merged.get("efficiency", {})
    runs = eff.get("as_used_runs")
    sp = _median(runs) if runs else eff.get("as_used_speedup")
    base_s = eff.get("baseline_as_used_seconds")
    no_conv = bool(base_s is not None and base_s < NO_CONVERSION_BASELINE_S
                   and sp is not None and sp < 1.0)

    v = BANDS[final_idx]
    if gate:
        v += (f" [gated: {gate}; the ungated total {total:.2f} would band as "
              f"{SHORT_BANDS[base_idx]}]")
    if no_conv:
        v = (f"no-conversion — the baseline as-used total {base_s:.3g} s is under "
             f"the {NO_CONVERSION_BASELINE_S:g} s materiality floor and the "
             f"candidate is slower as-used ({sp:.3g}×): this lecture should not "
             f"be converted, whatever the candidate's polish. Candidate quality "
             f"for the record: {total:.2f}/5, {SHORT_BANDS[final_idx]}"
             + (f" [{gate}]" if gate else ""))
    return {"rows": rows, "total": total, "verdict": v,
            "band_verdict": BANDS[final_idx], "verdict_gate": gate,
            "no_conversion": no_conv}
