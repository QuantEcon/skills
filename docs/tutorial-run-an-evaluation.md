# Tutorial: run a full evaluation by hand

This walks the `/benchmark:review-acceleration` procedure end-to-end **by hand**, using the recorded [ge_arrow validation run](../reviews/validation-run-ge_arrow-2026-07-22.md) as the worked example — so every number you produce can be checked against a committed reference. When you invoke the skill, Claude drives these same steps for you; doing it manually once is the fastest way to understand what the skill measures, what the scorecard means, and how to debug a run that goes wrong.

Canonical references (this tutorial points, never restates): the procedure in [SKILL.md](../benchmark/skills/review-acceleration/SKILL.md), the rubric in [EVALUATION_FRAMEWORK.md](../benchmark/references/EVALUATION_FRAMEWORK.md), the engine contract in [scripts/README.md](../benchmark/scripts/README.md).

## What you need

- The `benchmark` plugin installed (or this repo checked out — its `benchmark/` directory serves as the plugin root).
- A Python environment with `jax`, `numpy`, and the lecture's imports. The reference used jax 0.4.35; the validation run used jax **0.10.1** — the verdict reproduced anyway, which is the point of band-based scoring.
- A checkout of the lecture repo. Evaluations always compare two refs: a **baseline** (the lecture before the conversion) and a **candidate** (the conversion PR's head).

## Step 0 — check out the exact states under evaluation

Every committed evidence file records its provenance: `source_pr` plus base/head SHAs. For ge_arrow ([lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717)):

```bash
git clone --filter=blob:none https://github.com/QuantEcon/lecture-python.myst
cd lecture-python.myst
git fetch origin update_ge_arrow:update_ge_arrow
git merge-base origin/main update_ge_arrow     # → 8cfba4c = the state prior to the PR
```

The merge-base is the "world before the PR" — that's the baseline. The PR branch head (`8c2d0d7`) is the candidate.

## Step 1 — scaffold the workspace

Evaluations live in **your workspace**, never inside the plugin (which is read-only when installed):

```bash
export CLAUDE_PLUGIN_ROOT=/path/to/plugin/benchmark   # or the installed plugin root
mkdir -p benchmark-eval/ge_arrow/scripts
cp $CLAUDE_PLUGIN_ROOT/references/examples/ge_arrow/scripts/*.py benchmark-eval/ge_arrow/scripts/
cp $CLAUDE_PLUGIN_ROOT/scripts/scoring/EVIDENCE_TEMPLATE.json benchmark-eval/ge_arrow/evidence.json
```

Because we are *reproducing* the ge_arrow evaluation, we copy its already-adapted scripts. For a **new** lecture you adapt them — extract `model_old.py` from the lecture at the baseline ref and `model_new.py` at the candidate ref **verbatim** (disclose any deviation), and rewrite the measurement scripts around the lecture's actual examples and call sequence. That adaptation is the skill's real work; there is deliberately no rigid harness. Either way, before measuring, diff your extractions against the lecture's cells — the validation run did exactly this and caught an undisclosed whitespace normalisation in the committed baseline extraction.

## Step 2 — measure

```bash
conda run -n quantecon python benchmark-eval/ge_arrow/scripts/run_all.py
```

`run_all.py` runs every measurement and aggregates results into `benchmark-eval/ge_arrow/results/`. The headline is the **as-used benchmark**: the lecture's real call sequence, at its real sizes, in a fresh interpreter so JIT compile time counts — repeated 3× per side, median taken. From the validation run:

```
== As-used total (numpy) ==
{"mode": "numpy", "total_s": 0.0272}  {"total_s": 0.0440}  {"total_s": 0.0292}
== As-used total (jax) ==
{"mode": "jax",   "total_s": 1.1947}  {"total_s": 1.2470}  {"total_s": 1.1603}
```

→ `results/as_used.json` records both `runs` lists, the medians, per-run speedups, and `baseline_as_used_seconds` (0.0292 s here). A provenance stamp (`results/env.json`) records the environment and any failed steps.

### The two precision regimes

Correctness is measured **twice**, and the two runs answer different questions:

- **As shipped (float32).** JAX computes in float32 by default, NumPy in float64 — so this run measures what a *reader actually experiences*: how far the published numbers drift. It drives the correctness Δ-bands (validation run: worst max|Δ| = 1.01e-4 → correctness 3).
- **Under x64 (`JAX_ENABLE_X64=1`).** This flips JAX to float64, putting both implementations at the *same* precision. Any remaining divergence cannot be rounding — it means the two implementations compute **different economics**, which forces correctness 1 and the logic-design bug cap. Agreement here (validation run: 1.42e-13) proves the drift in the first run is purely precision, not logic.

```bash
cd benchmark-eval/ge_arrow/scripts
JAX_ENABLE_X64=1 python check_equivalence.py    # writes results/equivalence_x64.json
```

The script writes one file **per regime** (`equivalence.json` / `equivalence_x64.json`) so the second run can't clobber the first — a fix that came out of the validation run, which found the x64 rerun silently overwriting the as-shipped results.

## Step 3 — record evidence

Fill `benchmark-eval/ge_arrow/evidence.json` from `results/`: measured numbers into the quantitative slots (each with its source file named), and each structural checklist item answered true/false **with a citation to the diff**. This file is the only place judgement lives — for a reproduction run the structural answers carry over unchanged (same diff), and only the measured quantities update.

## Step 4 — score

```bash
python $CLAUDE_PLUGIN_ROOT/scripts/scoring/score.py benchmark-eval/ge_arrow
```

No score is ever typed by hand — the engine computes all seven dimensions and prints the derivation of each. The validation run's tail:

```
WEIGHTED TOTAL                                           2.85
VERDICT: no-conversion — the baseline as-used total 0.0292 s is under the 1 s
materiality floor and the candidate is slower as-used (0.0251×): this lecture
should not be converted, whatever the candidate's polish. Candidate quality
for the record: 2.85/5, mixed/wash
SENSITIVITY: fragile (29 single-input perturbations)
     └ quantitative.correctness.builds: True → False ⇒ total 2.30, ...
     └ quantitative.correctness.matches_under_x64: True → False ⇒ total 2.30, ...
     └ structural.logic_design.criteria.good_algorithmic_choices: False → True ⇒ total 3.00, ...
```

Three things to read off a v2 scorecard beyond the total: the **verdict gate** (broken correctness caps the band regardless of polish), the **no-conversion** verdict (a lecture with nothing to gain shouldn't be converted, however good the candidate), and the **sensitivity stamp** (would any single contestable input flip the outcome? here: yes, three would — the scorecard says so instead of hiding it).

## Step 5 — cross-compare

Raw numbers are machine- and version-dependent; **bands are the reproducibility contract**. What must match the reference, and what may drift:

| Quantity | Reference | Validation run | Contract |
|---|---|---|---|
| float32 worst max\|Δ\| | 1.7e-4 | 1.01e-4 | same Δ-band (→ correctness 3) |
| as-used speedup | 0.022× | 0.0251× (median of 3) | same efficiency band (→ 2) |
| baseline total | 0.035 s | 0.0292 s | same side of the 1 s floor |
| **Total / verdict / stamp** | 2.85, no-conversion, fragile | 2.85, no-conversion, fragile (same 3 flips) | **exact** |

If your bands move, something real changed — check `results/env.json` first, then the extraction diff from Step 1.

## Step 6 — report

Write `<lecture>_REPORT.md` from the scorecard + evidence following the worked examples' format ([ge_arrow](../benchmark/references/examples/ge_arrow/ge_arrow_REPORT.md), [markov_asset](../benchmark/references/examples/markov_asset/markov_asset_REPORT.md)): TL;DR with the full verdict, dimension table, evidence per dimension, and a must-fix list. For the validation run the "report" is the [cross-comparison record](../reviews/validation-run-ge_arrow-2026-07-22.md) itself.
