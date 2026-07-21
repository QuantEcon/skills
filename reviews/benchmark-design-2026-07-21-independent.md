# First-principles design review — `benchmark/` lecture-evaluation system

**Date:** 2026-07-21
**Branch reviewed:** `docs-skills-usage`
**Scope:** the full evaluation system in `benchmark/` — rubric dimensions and weights, metrics, aggregation and verdict method, thresholds and calibration, measurement architecture. Everything treated as open to revision; the goal is the best possible evaluation system for QuantEcon, where lectures are teaching materials first.
**Method:** read every design document ([README.md](benchmark/README.md), [EVALUATION_FRAMEWORK.md](benchmark/references/EVALUATION_FRAMEWORK.md), [scripts/README.md](benchmark/scripts/README.md), [SKILL.md](benchmark/skills/review-acceleration/SKILL.md), [examples README](benchmark/references/examples/README.md)), the scoring engine ([rubric.py](benchmark/scripts/scoring/rubric.py), [score.py](benchmark/scripts/scoring/score.py)), both worked evaluations (evidence, results, reports), and the measurement scripts; then ran the rubric against synthetic edge cases to test the aggregation empirically. The numbered edge-case results below (A–D) were produced by executing `rubric.score_all` directly on constructed evidence.

## Bottom line

The system's core measurement doctrine — **as-used, fresh-process, compile-time-counted** — is genuinely right and well-executed, but the scoring layer on top of it has structural flaws that can produce wrong verdicts. Three were confirmed empirically:

- A lecture that **does not build** can score 3.9–4.2 → "merge" territory (compensatory aggregation, no gates).
- A **no-op conversion** (candidate byte-identical to baseline) scores 3.40 → "net positive" (the scale's zero is displaced).
- Moving a **single hand-counted concept** flips markov_asset's verdict band (2.25 "net regression" → 2.50 "wash").

The critique is ranked by decision impact; each item carries evidence and a recommended replacement design.

---

## What the system gets right (keep these)

- **The as-used doctrine.** Fresh process, real call sequence, real sizes, compile time counted, warm numbers never the headline. The ge_arrow case (1.4–4.8× faster warm, 45× slower as-used) proves this rule earns its keep. This is the system's central insight and should survive any redesign.
- **Evidence → score determinism.** Scores computed, never typed; every score carries its derivation; scorecards reproduce byte-identically; the 5⁷ brute-force band-edge audit found and fixed real FP bugs. This auditability discipline is rare and valuable.
- **Verbatim extraction with disclosed deviations**, including keeping markov_asset's build-breaking bug in `model_new.py`.
- **The caveat register** (M1/m3/n6 in the examples README) is unusually honest — M1 already anticipates part of finding 4.
- **Triage's bounding logic** — "the baseline as-used total bounds the entire possible win" — is elegant, cheap, and correct.

---

## 1. The verdict is compensatory with no gates — a lecture that doesn't build can be told "merge"

The weighted mean lets any dimension buy off any other. Running the rubric on a candidate with `builds: false` and strong scores elsewhere:

| Synthetic case | Total | Verdict (`rubric.py:75-82`) |
|---|--:|---|
| Does not build, all else max, bug-override set | **3.90** | "net positive with fixable regressions — merge after addressing them" |
| Same, evaluator forgets the override flag | **4.20** | "clear improvement — merge" |
| Every dimension at its "wash" anchor (all 3s) | **3.00** | "net positive with fixable regressions" |

markov_asset landed at 2.25 only because its *other* dimensions were also weak — the rubric has no mechanism guaranteeing that outcome. Note also that the build-breaking bug must be recorded twice (`builds: false` in correctness *and* `introduces_correctness_bug: true` in logic_design) with nothing enforcing consistency; forgetting the duplicate is worth +0.30 and a band.

The all-3s case exposes a band mislabeling: every dimension's 3 is defined as "wash" (efficiency 0.8–1.3× is literally labeled "wash" in the anchors), yet a total of 3.0 maps to "net positive — merge after addressing." The wash band (2.5–2.9) sits *below* the scale's center. The ge_arrow report feels this: it calls 2.85 "net mixed, *slightly negative*" while the band says "mixed/wash."

**Recommended design.** Non-compensatory gates checked *before* any weighted total:

- **G1 — executes end-to-end** on the shipped configuration. Fail → "do not merge," full stop, whatever the total.
- **G2 — published numbers preserved** (within tolerance under the shipped dtype config) *or* the change is explicitly flagged and justified in the PR. Silent changes to printed numbers fail the gate — this is the framework's own stated principle ("silently changes the numbers"), which the current scoring only *discounts* rather than blocks.

Then re-center the bands so 3.0 is a wash, and make band labels *descriptive* ("net improvement" / "wash" / "net regression") rather than imperative ("merge after addressing them" asserts fixability the score cannot know — the must-fix list is where fixability belongs).

## 2. The scale's zero is displaced — a no-op conversion scores 3.40 "net positive"

The verdict claims to answer "did this change improve the lecture?" but roughly 40% of the weight scores the *candidate in absolute terms*: the four structural checklists (0.45 combined weight) ask whether the new code is pure, global-free, idiomatic, testable; the docstring column of readability is `docstring_cov_new`, an absolute; ergonomics counts the candidate's statements.

The identity test — candidate byte-identical to ge_arrow's baseline, evidence filled per the committed conventions — yields **3.40, "net positive with fixable regressions — merge after addressing them"** for a PR that changes nothing.

The converse also holds: converting an already-pristine baseline (lake_model-style) inherits structural 4s–5s from virtues the baseline already had, and `fixes_prior_bugs` means a conversion of a *clean* lecture caps logic at 4 — the candidate is punished for the baseline's quality. The checklists even mix framings internally: `fixes_prior_bugs` is a delta, `pure_no_order_dependence` is an absolute.

**Recommended design.** Score **both implementations on the same absolute anchors** and derive the verdict from the delta profile. The machinery barely changes: `static_metrics.py` already measures both sides; the checklists just get answered twice. Output becomes two absolute scorecards plus a per-dimension delta table; the verdict comes from the weighted delta (identity = 0.0 by construction) with the gates from finding 1. The dual scorecards are independently useful for QuantEcon: "the baseline itself scores 2.4 — the fix is a rewrite, not necessarily a JAX rewrite" is exactly the recommendation the ge_arrow report reached by hand.

## 3. Measurement architecture: the system measures a hand-built reconstruction, not the lecture

Each evaluation hand-adapts `as_used_total.py` to re-enact the lecture's call sequence. This puts the headline metric at the mercy of adaptation choices: the ge_arrow script implements the λ-sweep as a 100-iteration Python loop on the NumPy side and one jitted `fori_loop` on the JAX side (`as_used_total.py:50-54` vs `:89-99`) — defensible (caveat n6 documents it), but it's an evaluator's judgement sitting inside the decisive number, and nothing verifies the reconstruction against the lecture. markov_asset needed a hand-patched copy just to produce a timing. And the whole thing is timed **once** — a single pass per side feeding threshold cliffs at 0.8×/1.3×/3×.

Beyond that: the deliverable is the *lecture* (prose + code + outputs), but only extracted code is evaluated — markov_asset's prose edits went unassessed, and prose is where pedagogy actually lives.

**Recommended design.** Measure the lecture itself. The lectures are executable MyST documents: for each branch, convert with jupytext and execute with nbclient in a fresh kernel, recording **per-cell wall time** (repeat K≥5, take medians). As-used time is then the real reader/CI wait, by definition — no reconstruction, no asymmetry class, no per-lecture timing scripts. Equivalence becomes an **executed-output diff**: compare the printed numbers between branches numerically — which is *directly* "were the published numbers preserved?" (gate G2), and it catches build breaks natively (markov_asset's `NameError` fails execution — no `smoke_test.py` needed). The current micro-benchmarks (crossover-n, recompile audit, cold-start) remain valuable as *diagnosis* feeding the must-fix list, not as verdict inputs. This is also the only architecture that scales across ~200 QuantEcon lectures, and it makes triage nearly free (baseline-side timing = execute the current lecture).

## 4. Readability — the heaviest weight rides on the weakest instrument

`n_prerequisite_concepts` drives the 0.25-weight dimension, and it is a hand-curated list embedded in each lecture's script (`static_metrics.py:41-52`) — caveat M1 admits this. The counting granularity is arbitrary ("jax.jit & tracing" and "static_argnames & recompilation" are two concepts; "NumPy arrays & slicing" is one), and the verdict is exquisitely sensitive to it: **recounting markov_asset's +5 as +4 — one concept — moves the total from 2.25 ("net regression — do not merge") to 2.50 ("mixed/wash")**, verified against the committed evidence.

Further problems: the delta treats concepts as fungible (7 OOP concepts out, 7 JAX concepts in = +0 = band 5, though the audience already knows the former from the series and none of the latter); `docstring_cov_new` is absolute, not a delta, and is a weak proxy for lecture code whose real documentation is the surrounding prose; and the "math-to-code distance" tie-breaker promised in EVALUATION_FRAMEWORK.md §2 never appears in `score_readability` (`rubric.py:104-111`).

**Recommended design.** Curate the concept inventory **once at series level, not per lecture**: a versioned `concepts.yml` mapping detection patterns → canonical concepts → the lecture where the series first teaches each. The existing `CONCEPTS` regex dict shows most JAX concepts have syntactic signatures (`jax.jit`, `static_argnames`, `.at[].set`, `lax.fori_loop`) — the fragile step was per-lecture deduplication into "ideas," which a shared map eliminates. The metric becomes mechanical: concepts used by the candidate that the series has *not taught at or before this lecture*, minus the same for baseline. Pair it with a prose check — for each new concept, does the PR's added prose explain it near first use? (A concept explained in prose is pedagogy; one that appears bare is burden.) Judgement that remains moves into `evidence.json` as cited slots — the M1 fix already proposed on skills PR #5, endorsed and extended here.

## 5. Efficiency: ratio-only scoring with a saturating floor and no materiality test

Three problems in `score_efficiency` (`rubric.py:114-124`):

1. Everything below 0.8× collapses to one band: 0.75× slower and 45× slower both score 2.
2. `correct_or_fixable` is near-vacuous (all code is "fixable"; both committed cases say so), so score 1 is practically unreachable — it's a 4-point scale in disguise.
3. Most important, **the ratio ignores absolute materiality**: ge_arrow's "45× slower" is 0.035 s → 1.56 s — 1.5 wall-clock seconds a reader would never notice. Triage mode already knows this ("a lecture whose compute totals 30 ms has nothing to give") but review mode doesn't: it hands ge_arrow a −2-band penalty for an imperceptible cost, while the actual crimes (readability, precision) are elsewhere. Ratios of tiny denominators are also noise-dominated — a single unrepeated pass deciding a banded score.

**Recommended design.** Two-dimensional scoring: a **materiality zone** first (|Δtotal| below a threshold — say 2 s of reader/CI wait — is automatically a 3/wash, whatever the ratio), then **log-symmetric ratio bands** outside it, so 3× faster and 3× slower are equidistant from wash. Under this, ge_arrow's efficiency is a 3 (correct: the case against it is pedagogy, not seconds), aiyagari's −52 s is a decisive 5, and the headline stops sounding catastrophic ("45×!") for immaterial stakes. Require K fresh-process repeats with the band assignment stable across the spread before it's recorded.

## 6. Calibration is two in-sample points, and triage's validation is circular

The thresholds claim calibration "against two measured end points" — 25× and 0.022×. Two points pin the two extreme bands; every interior boundary (0.8, 1.3, 3× for efficiency; +1–2/+3–4 for concepts; the docstring cuts) has **zero observed cases** — both real evaluations landed in band 2 of readability and band 2 of efficiency.

The triage validation table in the plugin README "reproduces every known verdict" on exactly the three cases the thresholds were built from — in-sample prediction presented as validation.

The HIGH anchor's provenance is inconsistent: EVALUATION_FRAMEWORK.md (§2, dimension 3) cites 1664 ms / 29.3 s while the committed `bellman_bench.json` says 2955 ms / 54.3 s — same ~24× ratio, visibly different run, in a system whose brand is citation fidelity.

**Recommended design.** Label all interior thresholds *provisional* in the framework; pre-register a recalibration protocol (after every N evaluations, re-fit band edges against the accumulated evidence files, version the rubric, re-run the regression anchors); treat the next several real evaluations as out-of-sample tests of triage and report hits/misses. Reconcile the anchor numbers now — either re-run and update the doc, or cite the JSON.

## 7. Cross-dimension double counting quietly rewrites the weights

Single root causes score in multiple dimensions:

- **float32** hits correctness (the entire band-3 rung), maintainability (`dtype_precision_safe`), and readability (the "float32/x64 flag" concept).
- **Purity** appears in logic (`pure_no_order_dependence`), maintainability (`pure_unit_testable`), and ergonomics (`fragile_protocol`).
- **Vectorisation** appears in logic (`good_algorithmic_choices`), style (`vectorised_where_natural` *and* `correct_control_flow_primitive`), efficiency, and readability (the `fori_loop`/carry concepts).

So the effective weight of these facts exceeds any nominal number, and the headline claim "readability (0.25) outranks efficiency (0.15)" isn't reliably true of the system's actual behavior. Seven dimensions also carry overlap costs: maintainability at 0.05 can swing the total by at most 0.20 — ceremony without leverage.

**Recommended design.** Either assign each observable to exactly one home dimension and publish the assignment, or — better — consolidate to four orthogonal dimensions re-derived from the teaching-first principle:

| Dimension | Weight (proposed) | Contents |
|---|:--:|---|
| Fidelity | ~0.25 | gates + precision policy |
| Pedagogy | ~0.40 | concept burden, math-to-code, prose explanation, exercise integrity |
| Cost | ~0.15 | as-used time with materiality, dependency/install burden |
| Code quality | ~0.20 | purity / idiom / API / maintainability merged |

Fewer, cleaner dimensions make the weights mean what they say.

## 8. No reliability engineering around the human/AI judgement slots

The system's motto — "no score is ever typed by hand" — is true but subtly overstated: the *scores* are computed, but the checklist booleans, `fragile_protocol`, `correct_or_fixable`, concept lists, and `statements_for_one_result` are hand-typed judgements that map deterministically to scores. Determinism relocated the subjectivity; it didn't remove it. There is no inter-rater data — no evidence that two independent evaluators (or two AI-skill runs) fill `evidence.json` the same way, on an instrument where finding 4 shows one boolean or one concept can flip a verdict.

**Recommended design.** Since the skill automates the fill, reliability testing is nearly free: run the evidence-fill twice in independent sessions, diff the judgement slots, and surface disagreements for human adjudication rather than silently keeping one. Track agreement rates across evaluations — that number, not the determinism claim, is what makes the structural dimensions trustworthy.

## 9. Smaller defects (fix opportunistically)

- `score_correctness` (`rubric.py:92`): the x64-divergence guard fires only when `d > 1e-8` — divergent logic with small shipped drift slips into bands 4–5. Also the band-3 reason string hardcodes "ships float32" as the explanation regardless of actual cause.
- Correctness thresholds are **absolute** `max|Δ|`; for lectures whose published objects are large-magnitude, 1e-3 absolute may be ~1e-6 relative and still scores 2. Use relative error (or per-object normalization).
- `score_ergonomics` (`rubric.py:129`) gives base 2 for any n≥4, but the prose anchor reserves 2 for "ordered, side-effecting" protocols — code and prose disagree.
- Dependency cost is unmeasured: adding `jax`/`jaxlib` to a lecture is a real installability burden for students (platform wheels, Windows) and belongs in the Cost dimension.
- Hardware policy should be pinned in the framework: "as-used" = the target series' actual build environment (CPU runners for lecture-python.myst, GPU for lecture-jax), recorded by `env_stamp.py`. A conversion verdict is environment-relative and should say so.
- Anchors were measured on jax 0.4.35 (old by now); compile costs and defaults drift across JAX releases. The recalibration trigger lives only in a script docstring — promote it to the framework.

---

## Summary

The measurement doctrine (as-used, fresh-process) and the auditability discipline are the right foundation — keep both. The redesign priorities:

1. **Gates before any weighted total** (builds; published numbers preserved), with re-centered, descriptive bands.
2. **Symmetric dual scoring** so the verdict measures the *change*, with identity = 0.
3. **Execute the actual lecture on both branches** (per-cell timing + output diff) in place of hand-adapted replay scripts — simultaneously fixes gate G2, kills the reconstruction-fidelity risk, and scales to the whole series.
4. **Series-level concept inventory** with mechanical detection in place of per-lecture hand lists.
5. **Materiality zone plus log-symmetric bands** for efficiency.

Items 1, 2, and 5 are pure `rubric.py` changes that could land quickly and be validated against the two committed evidence files; item 3 is the one real piece of new engineering; item 4 is a natural companion to the QuantEcon.manual style-page work already tracked in QuantEcon.manual#104.

---

## Appendix — empirical verification runs

All produced by calling `rubric.score_all` directly (engine at `benchmark/scripts/scoring/rubric.py`, evidence conventions as in the two committed `evidence.json` files):

| Case | Construction | Total | Verdict |
|---|---|--:|---|
| A | No-op conversion: candidate ≡ ge_arrow baseline; quantitative slots take the baseline's own measured values (Δ=0, speedup 1.0×, docstrings 0.90, 4 ordered statements); checklists describe the baseline code (order-dependent methods, module globals, typo) | **3.40** | net positive with fixable regressions — merge after addressing them |
| B | `builds: false`, every other slot maximal, `introduces_correctness_bug: true` (logic capped at 3) | **3.90** | net positive with fixable regressions — merge after addressing them |
| B2 | Same as B but the duplicate override flag left false | **4.20** | clear improvement — merge |
| C | Every dimension at its "wash" anchor (score 3 on all seven) | **3.00** | net positive with fixable regressions — merge after addressing them |
| D | markov_asset committed evidence with `delta_prereq_concepts` 5 → 4 (one fewer hand-counted concept; docstrings 0.75 → band 4, so the concept column pins the readability score) | 2.25 → **2.50** | net regression → mixed / wash |
