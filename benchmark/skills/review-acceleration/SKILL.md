---
name: review-acceleration
description: Review whether an accelerated implementation (JAX, Numba) of QuantEcon lecture code actually improves the lecture. Measures as-used performance (fresh process, JIT compile time included), numerical fidelity (float32/float64), and readability, then produces a weighted scored report with a merge recommendation. Use when reviewing a NumPy→JAX/Numba conversion PR or deciding whether to convert a lecture.
---

# review-acceleration

> **Status: under construction.** This skill is being built collaboratively with @xuanguang-li from the evaluation system he published on [QuantEcon/lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717). The supporting scripts referenced below are being collected into this plugin's `scripts/` directory. Tracking: [QuantEcon/meta#335](https://github.com/QuantEcon/meta/issues/335) (workstream B).

## Guiding principle

QuantEcon lectures are teaching materials first and programs second. A rewrite that is faster or more modern but harder for a learner to read, or that silently changes published numbers, is not an improvement. "Uses JAX" is never a goal in itself — the accelerated implementation must earn its place on each lecture.

## Procedure (v0 outline)

Given a baseline implementation (usually `main`) and a candidate (usually a PR branch) for one lecture:

1. **Equivalence check** (`scripts/check_equivalence.py`, pending): run both implementations over every example in the lecture; diff all published objects under the default dtype AND with `jax_enable_x64` enabled; report `max|Δ|` for each regime.
2. **Static metrics** (`scripts/static_metrics.py`, pending): prerequisite-concept count, docstring coverage, code lines, number of definitions, closure-nesting depth — for both implementations.
3. **As-used benchmark** (`scripts/as_used_total.py`, pending): replay the lecture's *actual* solver call sequence, at its *actual* problem sizes, in a fresh interpreter so JIT trace/compile time counts. Compute `as_used_speedup = baseline total wall time / candidate total wall time`. Record warm timings alongside (never alone), a crossover-n scaling curve, and a recompile audit (one recompile per distinct static-argument value or shape).
4. **Score seven dimensions** (1–5 against the rubric anchors) and combine with weights: correctness & numerical fidelity 0.20, readability & pedagogical clarity 0.25, computational efficiency as-used 0.15, logic & design 0.15, coding style & idiom 0.10, API ergonomics 0.10, maintainability 0.05. Readability deliberately outranks efficiency.
5. **Report** with per-dimension evidence and the weighted total: ≥ 4.0 merge; 3.0–3.9 merge after addressing fixable regressions; 2.5–2.9 revisit before merging; < 2.5 do not merge as-is. Include a concrete fix list mapping each recommendation to the dimension it lifts.

The full rubric with numeric scoring anchors and worked HIGH/LOW examples lives in the [#717 thread](https://github.com/QuantEcon/lecture-python.myst/pull/717) and will move into this plugin's `references/` and the QuantEcon manual ([QuantEcon.manual#104](https://github.com/QuantEcon/QuantEcon.manual/issues/104)).

## Calibration cases

- **HIGH:** the `aiyagari.md` Bellman pattern — large fixed-shape arrays, many re-solves; measured ~25× faster as-used under JAX.
- **LOW:** the `ge_arrow.md` conversion (lecture-python.myst#717) — 2×2/3×3 economies, fresh static args per call; measured ~45× slower as-used despite warm speedups.
