# Benchmark evaluation system — merged design review (2026-07-21)

Synthesis of two independent design critiques of the evaluation system, run deliberately in isolation from each other as a bias control:

- **Review A** ([benchmark-design-2026-07-21-independent.md](benchmark-design-2026-07-21-independent.md)) — a fresh session with an unframed prompt; 9 findings, empirically verified against the engine.
- **Review B** — a 36-agent adversarial workflow: six critics attacking from independent angles, every non-minor critique then passed to a **steelman defender** instructed to save the original design; only critiques surviving the strongest defense are reported. Two critiques survived outright (CRITIQUE_STANDS); most were PARTIALLY_DEFENDED — the residuals below are what remains after the best defense.

Findings present in **both** independent runs are the most robust. All demonstrations referenced here were produced by executing `rubric.py`/the notebooks, not by inspection alone. The scope was the *design*; the system's architecture (evidence → deterministic engine, verbatim extraction, the as-used doctrine) was validated previously and both reviews independently concluded it should survive any redesign.

---

## 1. Corrections of record (already applied)

The review process falsified three claims our own documents made — corrected via erratum and rewording on this branch, and on [lecture-python.myst#654](https://github.com/QuantEcon/lecture-python.myst/pull/654):

1. **"markov_asset's lecture does not build as shipped" — false as worded.** Executing all cells of the PR branch's notebook in order completes cleanly (preview CI passes): earlier cells bind a global `err` that the stray `err.throw()` inside `call_option` silently resolves to. The true finding is *subtler and worse*: the stale-global masking means **the checkify stability validation never actually runs in the shipped lecture**, on the model whose spectral radius sits 0.002 below the stability bound; a reader copying the function into a clean namespace hits the `NameError`. `builds: false` remains a true measurement under the system's declared fresh-process regime; the sentence about the lecture was wrong.
2. **"The replayed sequence mirrors the lecture exactly" — false for both reference cases.** ge_arrow's replay constructs 12 model objects where the lecture constructs 6 and reuses them across initial states; markov_asset's replay builds a fresh model per γ where the lecture mutates one object, and omits two calls. The reconstruction-fidelity risk the review process flagged abstractly had already occurred, undetected.
3. **"Medians over repeats" — false for the headline metric.** The as-used totals are single passes per side; only the warm/scaling benchmarks use medians. The one metric that solely decides a 0.15-weight dimension is the least-replicated measurement in the system.

## 2. Findings that survive the steelman defense

### 2.1 The verdict's safety couplings exist only by convention (both reviews; residual after defense)

The defense established something the critiques missed: **with the documented evidence convention followed** (build failure recorded in both `builds` and the logic-design bug flag), a non-building lecture's ceiling is exactly **3.90 < 4.0** — the two overrides jointly form a designed soft gate on the unconditional-merge band. But that coupling is enforced by reviewer discipline, not code: one forgotten boolean yields **4.20 "clear improvement — merge" for a lecture that crashes** — in a system whose stated contract is that scores are deterministic functions of evidence. Worse, Review B closed the "requires dishonest evidence" escape: `builds: true`, `matches_under_x64: true`, `max|Δ| > 1e-1` (a float32 catastrophe with no logic bug) reaches **4.2 with fully honest evidence**.

### 2.2 The readability instrument inverts its own ground truth (CRITIQUE_STANDS)

`score_readability` = worse-of(Δprereq-concepts, docstring coverage). Executed against the framework's own labeled exemplars: **odu.py — the framework's LOW-readability example — measures 0.86 docstring coverage**, and code written in the flagship aiyagari style (inline shape comments, undocumented closures/NamedTuples) measures ~0.41–0.55 and is **mechanically capped at readability 2** regardless of concept count. The metric anti-correlates with the framework's own judgements at both ends, and the construct the prose says defines the dimension ("math-to-code distance") has no encoding in the scorer at all.

### 2.3 Review mode and triage mode contradict each other (residual after defense)

A fully-polished ge_arrow — every fix from its own report applied, the intrinsic 0.022× as-used unchanged — scores **4.0 "clear improvement — merge"** while the (blind-validated) triage rule says *don't convert* at a 0.028 s baseline. The band vocabulary cannot express "no-conversion" — a verdict the system's own authors needed twice and both times delivered in prose outside the score.

### 2.4 Band labels use delta language an absolute-hybrid total cannot license (both reviews; narrowed by defense)

The defense partly refuted Review A's "3 is neutral" (only efficiency anchors 3 as wash; correctness/readability anchor *no-change at 5*). What survives: ~40% of the weight scores the candidate absolutely, so a no-op rewrite of a ge_arrow-quality baseline scores ~3.35–3.55 — rewrites landing in [3.0, 3.55) are *worse than doing nothing* yet labeled "net positive." The homogeneous-population defense (baselines share a known-bad house style, so absolute criteria are deltas in disguise) is honest but population-bound — a clean-baseline conversion scores 4.30 "clear improvement" for virtues the baseline already had.

### 2.5 Judgement noise exceeds band resolution (both reviews; narrowed by defense)

One hand-counted concept flips markov_asset 2.25→2.50 across a band; one contestable checklist boolean flips ge_arrow 2.85→3.00; ~27% of ordering-preserving weight vectors flip ge_arrow's band. The defense's strongest point: every demonstrated flip crosses a *deliberation* boundary (the operational next step is identical), never the merge/reject gates, which sit ≥0.35 away. What survives: the 2-decimal total communicates precision the instrument lacks; the concept-count grain rule exists only by example; a one-flip sensitivity stamp (~20 lines in score.py) would make fragility visible.

### 2.6 Fact-level fan-out is undocumented (both reviews; substantially defended)

The per-consequence billing defense is strong — a decision harming readers *and* callers *and* editors *should* cost multiply, and most of the demonstrated 1.35-point checkify swing decomposes into legitimately distinct harms. What survives: two near-verbatim duplicate criteria across logic/style (`good_algorithmic_choices` glossed as "vectorised where natural" vs style's `vectorised_where_natural`); and no document states that a root cause's total influence is the sum over its manifestations — the weight table invites misreading.

### 2.7 "Calibrated" overclaims (both reviews)

The two measured anchors pin the efficiency scale's *extremes*; every interior edge (0.8/1.3/3×; the Δ bands; the concept and coverage cuts; the 4.0/3.0/2.5 verdict cutoffs) has zero observed cases and no recorded derivation. The defense showed the wash band is deliberately wider than the noise floor (a real design rationale) — but nothing in the repo records it. Same class: the triage "3/3 validation" is in-sample (now noted in the docs).

## 3. Defended — no change recommended

- **The efficiency ratio-only form** (Review A's materiality critique): the ratio is the right construct for "did the conversion meet its stated goal"; log-rescoring changes no committed verdict; absolute reader-seconds belong in *triage* (where they already are) and in the report prose (where they already are).
- **The weighted total per se**: it provides a real total order for programme-level triage and a distance-to-merge trajectory; the four-gate alternative was shown to be a lossy projection of the rubric fitted on its own calibration set — its "3/3 agreement" validates the rubric, not the gates.
- **min() aggregation in readability** (direction): the gameable input (docstrings) has no upward power under min() — Goodhart-resistant by shape. The problem is the input (2.2), not the aggregation.
- **Per-consequence multi-counting as a principle** (2.6's core).

## 4. Recommended v2 changes

Ordered by (impact ÷ effort); items 1–5 are engine/doc changes validatable against the committed evidence files; item 6 needs @xuanguang-li's design input.

| # | Change | Effort |
|---|---|---|
| 1 | **Enforce the couplings in code**: derive the logic-design cap from `builds`/x64-divergence in `score_all`; gate the verdict — correctness 1 (any cause) caps the verdict at "net regression," correctness 2 caps at "mixed/wash" | ~5 lines |
| 2 | **Add a "no-conversion" verdict**: when the efficiency evidence shows the triage don't-convert profile (immaterial baseline total + slower as-used), the verdict says so instead of scoring the polish | ~10 lines |
| 3 | **Sensitivity stamp**: score.py perturbs each boolean and band-adjacent value, marks the scorecard `robust` or `fragile (deciding flips listed)`; report totals at the precision the instrument supports | ~20 lines |
| 4 | **K-repeat as-used** (median of ≥3 fresh-process runs; contested-band annotation when the spread crosses an edge) | script change |
| 5 | **Documentation honesty pass**: thresholds labeled policy choices with derivation notes; fan-out paragraph; concept-grain rule stated (one item per reader-facing API surface, symmetric old/new); "calibrated" → "anchored" | prose |
| 6 | **Readability instrument v2**: replace docstring coverage with equation-traceability (per numbered equation: can a reviewer cite the single implementing expression? fraction traceable, old vs new — same citation discipline as the checklists); move concept lists into evidence.json as cited slots (extends the M1 proposal) | design + rubric |
| 7 | **Extraction/replay verification**: a mechanical step diffing extracted code against the lecture's cells, and the replay's call sequence against the lecture's — closing the fidelity gap that produced §1.2. Longer-term: evaluate executing the lecture itself at both refs (nbclient per-cell timings; meta#335 telemetry) as the as-used source, with the current scripts as the diagnostic layer | design |

## 5. What both reviews agree must survive

The as-used, fresh-process, compile-counted doctrine; evidence → deterministic scoring with printed derivations; verbatim extraction with disclosed deviations; the calibration-anchor discipline; the caveat register; triage's bounding logic. The redesign is of the scoring superstructure, not the measurement foundation.
