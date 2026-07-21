---
name: review-acceleration
description: Review whether an accelerated implementation (JAX, Numba) of QuantEcon lecture code actually improves the lecture. Measures as-used performance (fresh process, JIT compile time included), numerical fidelity (float32/float64), and readability, then produces a weighted scored report with a merge recommendation. Use when reviewing a NumPy→JAX/Numba conversion PR or deciding whether to convert a lecture.
---

# review-acceleration

> **Status: evaluation system landed; skill wiring in progress.** The system was developed and validated by @xuanguang-li on [QuantEcon/lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717) and [#654](https://github.com/QuantEcon/lecture-python.myst/pull/654) and now lives in this plugin: the rubric in [`references/EVALUATION_FRAMEWORK.md`](../../references/EVALUATION_FRAMEWORK.md), the deterministic scoring engine in `scripts/scoring/`, and two complete worked evaluations in `references/examples/`. Remaining work is this skill's operational procedure: [QuantEcon/skills#4](https://github.com/QuantEcon/skills/issues/4). Tracking: [QuantEcon/meta#335](https://github.com/QuantEcon/meta/issues/335) (workstream B).

## Guiding principle

QuantEcon lectures are teaching materials first and programs second. A rewrite that is faster or more modern but harder for a learner to read, or that silently changes published numbers, is not an improvement. "Uses JAX" is never a goal in itself — the accelerated implementation must earn its place on each lecture.

## Procedure

Given a baseline implementation (usually `main`) and a candidate (usually a PR branch) for one lecture, follow the measure → record-evidence → score contract in [`scripts/README.md`](../../scripts/README.md) — **scores are never typed by hand**:

1. **Scaffold** — create `references/examples/<lecture>/` from an existing example: extract `model_old.py` (baseline) and `model_new.py` (candidate) verbatim from the lecture's code cells, and adapt the measurement templates (`check_equivalence.py`, `static_metrics.py`, `benchmark.py`, `as_used_total.py`, plus lecture-specific ones) to the lecture's actual examples and call sequence. Adapting templates per lecture is this skill's job — there is deliberately no rigid harness.
2. **Measure** — `run_all.py`: equivalence under the default dtype AND `jax_enable_x64` (report `max|Δ|` per regime); static metrics (prerequisite concepts, docstring coverage); the **as-used benchmark** — replay the lecture's *actual* solver call sequence at its *actual* sizes in a fresh interpreter so trace/compile time counts (`as_used_speedup = baseline total / candidate total`), with warm timings alongside (never alone), a crossover-n scaling curve, and a recompile audit. A provenance stamp (`results/env.json`, generated per-run) records the environment and any failed steps.
3. **Record evidence** — fill `evidence.json` from the results: measured numbers into the quantitative slots with sources; each structural checklist item answered true/false **with a citation to the diff**. This file is the only place judgement is recorded.
4. **Score** — `python scripts/scoring/score.py references/examples/<lecture>` computes all seven dimensions and the weighted total deterministically. The weights, threshold anchors, and verdict bands are defined in [`references/EVALUATION_FRAMEWORK.md`](../../references/EVALUATION_FRAMEWORK.md) §1–2 and machine-encoded in `scripts/scoring/rubric.py` — never restate or re-derive them here.
5. **Report** — write `<lecture>_REPORT.md` from the scorecard + evidence, following the worked examples' format: TL;DR with the weighted score and verdict, the dimension table with drivers, evidence per dimension, and a must-fix list mapping each recommendation to the dimension it lifts.

Never present warm-only speedups as the headline — the ge_arrow case measured 1.4–4.8× faster warm and ~45× slower as-used.

## Triage mode (no candidate yet)

When the question is "should this lecture be converted at all," run the prospective subset — only the existing lecture is needed:

1. **Baseline as-used total**: adapt just the baseline half of an `as_used_total.py` template and replay the lecture's real call sequence — this bounds the maximum possible win (a 30 ms lecture has nothing to give).
2. **Pattern-match** against the calibrated poles: aiyagari-shaped (large fixed shapes, many re-solves, stable static args → ~24× win) vs ge_arrow-shaped (tiny models, fresh static args per call → ~45× loss).
3. **Crossover check**: the lecture's problem sizes vs warm crossover-n.
4. **Readability-cost forecast**: which prerequisite concepts the conversion would force.

Decision rule from the weights: efficiency (0.15) gains at most +0.30 weighted; readability (0.25) losing two bands costs −0.50 — a conversion that costs meaningful readability cannot break even on speed alone, and structural wins are usually achievable in the baseline library. Report a predicted verdict band with the binding constraint named, not a scorecard. Validated 2026-07-21: blind triage on ge_arrow (0.028 s → don't convert), markov_asset (0.087 s → don't convert), and the aiyagari pattern (54.3 s → convert) reproduced all three known verdicts; triage cannot predict conversion-quality defects (markov_asset's build bug), and must say so.

## Calibration baseline (regression anchors)

The two worked evaluations in `references/examples/` are the validation baseline — re-running their pipelines must reproduce these verdicts:

- **`ge_arrow`** ([#717](https://github.com/QuantEcon/lecture-python.myst/pull/717)): **2.85/5 — mixed/wash.** Tiny 2×2/3×3 economies, fresh static args per call → ~45× slower as-used despite warm wins.
- **`markov_asset`** ([#654](https://github.com/QuantEcon/lecture-python.myst/pull/654)): **2.25/5 — net regression.** A stray `err.throw()` that crashes in any clean namespace and, in notebook order, silently disables the checkify stability validation (a masked failure — see the REPORT erratum); float32 drift near a critical stability margin.
- **HIGH anchor:** the aiyagari Bellman pattern (`scripts/calibration/bellman_bench.py`) — large fixed-shape arrays, many re-solves; ~25× faster as-used → the "score 5" calibration.

The rubric will also be distilled into the QuantEcon manual as the companion to the JAX style page ([QuantEcon.manual#104](https://github.com/QuantEcon/QuantEcon.manual/issues/104)).
