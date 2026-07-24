# benchmark plugin

Evaluation tooling for QuantEcon lecture code rewrites — the question it answers is never "is JAX faster?" but **"does this implementation earn its place in this lecture?"** Lectures are teaching materials first and programs second; the plugin's rubric weights readability (0.25) above efficiency (0.15) on purpose.

One skill, two modes:

| Mode | Question | Needs | Produces |
|---|---|---|---|
| **Review** | Did this conversion PR improve the lecture? | baseline + candidate implementations | A scored report with a merge recommendation |
| **Triage** | Is this lecture worth converting at all? | the existing lecture only | A predicted verdict band with the binding constraint named |

Status: evaluation system landed (v0.2.0); skill wiring tracked in [skills#4](https://github.com/QuantEcon/skills/issues/4). The system was developed and validated by [@xuanguang-li](https://github.com/xuanguang-li) on [lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717) and [#654](https://github.com/QuantEcon/lecture-python.myst/pull/654).

## Using the skill

```
/benchmark:review-acceleration <PR number or baseline..candidate refs>   # review mode
/benchmark:review-acceleration should we convert <lecture>?              # triage mode
```

### Review mode — what you get

The skill follows the measure → record-evidence → score contract ([scripts/README.md](scripts/README.md)): it extracts both implementations verbatim from the lecture's code cells, adapts the measurement templates, runs them, fills `evidence.json` with cited answers, and lets the engine compute the verdict — **no score is ever typed by hand**. The session shows the engine's derivation table (every score with the measured number and threshold band that produced it), and the final report follows the worked examples' format:

1. **TL;DR** — weighted score, verdict band, the decisive facts in one paragraph
2. **Dimension table** — weight / score / weighted contribution / one-line driver each
3. **What changed** — before/after implementation shape
4. **Evidence by dimension** — `max|Δ|` in both dtype regimes, prerequisite-concept and docstring deltas, the as-used vs warm timing table, crossover-n, recompile audit
5. **Recommendation** — a must-fix list where each item is tagged with the dimension it lifts, plus where the score lands after fixes

See [references/examples/ge_arrow/ge_arrow_REPORT.md](references/examples/ge_arrow/ge_arrow_REPORT.md) (2.85/5, no-conversion; candidate band mixed/wash) and [references/examples/markov_asset/markov_asset_REPORT.md](references/examples/markov_asset/markov_asset_REPORT.md) (2.25/5, no-conversion + gated net regression) for complete real reports. Verdict bands, the v2 verdict gates / no-conversion rule / sensitivity stamp, weights, and scoring anchors: [references/EVALUATION_FRAMEWORK.md](references/EVALUATION_FRAMEWORK.md) §1–2.

**The one rule to remember:** warm-only speedups are never the headline. The ge_arrow case measured 1.4–4.8× faster warm and **45× slower as-used** — the as-used number (fresh process, actual problem sizes, compile time included) decides the efficiency score.

### Triage mode — before any code is written

Four checks, using only the existing lecture:

1. **Baseline as-used total** — replay the lecture's real call sequence (the NumPy half of an `as_used_total.py` template). This bounds the entire possible win: a lecture whose compute totals 30ms has nothing to give.
2. **Workload-pattern match** — against the two calibrated poles: **aiyagari-shaped** (large fixed-shape arrays, many re-solves, stable static args → measured ~24× as-used win) vs **ge_arrow-shaped** (tiny models, fresh static args per call → measured ~45× as-used loss).
3. **Crossover comparison** — the lecture's problem sizes vs the warm crossover-n from the scaling data.
4. **Readability-cost forecast** — which concepts the conversion would force on readers (static args, `lax` carries, checkify, the float32/x64 distinction), against the prerequisite-concept bands.

Then the decision rule that falls out of the rubric weights: efficiency (0.15) can gain at most +0.30 weighted (band 3→5), while readability (0.25) losing two bands costs −0.50 — **a conversion that costs meaningful readability cannot break even on speed alone**; it must also win on logic & design and ergonomics, and those structural wins are usually achievable in plain NumPy.

**Validation (2026-07-21):** triage applied blind (baseline-side data only) to the three known cases reproduces every known verdict:

| Case | Baseline total | Pattern | Triage says | Full evaluation said |
|---|---|---|---|---|
| ge_arrow | 0.028 s | n=2/3, fresh static args | don't convert | 2.85 wash; 45× slower as-used |
| markov_asset | 0.087 s | n=5/25, LAPACK-bound | don't convert | 2.25 net regression |
| aiyagari pattern | 54.3 s | 200×7 fixed, 20 re-solves | convert | 23.8× as-used win |

Scope limit, confirmed by the same test: triage predicts whether the prize is worth pursuing — it cannot predict conversion-quality outcomes (markov_asset's masked `err.throw()` defect was a property of the PR, invisible to triage). Note also that this validation is **in-sample** — the three cases are the ones the thresholds were calibrated on; out-of-sample validation accumulates as fresh lectures are triaged.

## Manual usage (no skill)

The full recipe is in [scripts/README.md](scripts/README.md) ("Evaluating a new lecture"); quickstart from this directory:

```bash
conda activate quantecon
python references/examples/<lecture>/scripts/run_all.py      # measure + provenance stamp
# fill references/examples/<lecture>/evidence.json (numbers + cited yes/no answers)
python scripts/scoring/score.py references/examples/<lecture>
```

Sanity anchors: re-running either worked example must reproduce **2.85** / **2.25** (both now carrying the v2 **no-conversion** verdict; ge_arrow stamps *fragile*, markov_asset *robust*). A step-by-step walkthrough of the whole procedure — with the ge_arrow reproduction as a checkable example — is [docs/tutorial-run-an-evaluation.md](https://github.com/QuantEcon/skills/blob/main/docs/tutorial-run-an-evaluation.md).

## Map

| Path | What |
|---|---|
| [skills/review-acceleration/](skills/review-acceleration/SKILL.md) | The skill (procedure, both modes) |
| [scripts/README.md](scripts/README.md) | Deterministic engine (`scripts/scoring/`): rubric, scorer, evidence template, provenance stamp |
| [scripts/calibration/](scripts/calibration/bellman_bench.py) | The shared HIGH-efficiency anchor (~24× ⇒ score 5) |
| [references/EVALUATION_FRAMEWORK.md](references/EVALUATION_FRAMEWORK.md) | The standard in prose — weights, anchors, checklists, verdict bands |
| [references/examples/](references/examples/README.md) | Two complete worked evaluations + the logic-check/provenance audit; the regression baseline |
