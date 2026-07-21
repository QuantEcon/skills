"""
THE SCORING STANDARD  (single source of truth, shared by every lecture).

This module encodes the rubric described in prose in ../EVALUATION_FRAMEWORK.md
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
def verdict(total):
    if total >= 4.0:
        return "clear improvement — merge"
    if total >= 3.0:
        return "net positive with fixable regressions — merge after addressing them"
    if total >= 2.5:
        return "mixed / wash — improvements offset by real regressions; revisit before merging"
    return "net regression — do not merge as-is"


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
        if score > 3:
            note = " (capped at 3: introduces a correctness bug)"
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
        return score_efficiency(ev["as_used_speedup"], ev["correct_or_fixable"])
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

    rows, total = [], 0.0
    for dim in WEIGHTS:
        ev = merged[dim]
        s, reason = score_dimension(dim, ev)
        w = WEIGHTS[dim]
        total += w * s
        rows.append({"dim": dim, "title": TITLES[dim], "kind": KIND[dim],
                     "weight": w, "score": s, "weighted": round(w * s, 3),
                     "reason": reason,
                     "citations": ev.get("citations", ev.get("source"))})
    return {"rows": rows, "total": round(total, 2), "verdict": verdict(total)}
