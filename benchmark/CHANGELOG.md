# Changelog — `benchmark`

Every released version of this plugin, newest first. A version exists because the content below shipped in it: the plugin cache is keyed by version string, so what you have installed is exactly the entries down to the version `claude plugin list` reports for `benchmark`.

Versions are [semver](https://semver.org) as a user of this plugin experiences it — a new skill, or a procedure that now does something materially different, is a minor bump; a correction that leaves the procedure as it was is a patch. Nothing below 1.0.0 promises stability.

Repository: [QuantEcon/skills](https://github.com/QuantEcon/skills) ([every commit that touched this plugin](https://github.com/QuantEcon/skills/commits/main/benchmark)). How a release is made: [developing-skills § Versioning and releases](https://github.com/QuantEcon/skills/blob/main/docs/developing-skills.md#versioning-and-releases).

## 0.4.0 — 2026-08-07

Triage becomes the front door, and every output leads with the decision. The reframing follows the maintainers' direction — the product most wanted is "look at a lecture and advise whether a JAX upgrade is recommended" — and the measured record agrees: in every evaluation to date (ge_arrow, markov_asset, wald_friedman, and the 2026-08-06 ge_arrow re-run on [skills#10](https://github.com/QuantEcon/skills/issues/10)) the recommendation was decided by the triage-layer instruments — the as-used baseline and what a conversion could reach — and never moved by the scorecard on top. Review mode is unchanged and stays: it is the mode that caught markov_asset's masked build defect, and it applies the day a conversion PR exists.

**Changed**

- `SKILL.md` leads with triage — the no-candidate "should this lecture be converted?" question — behind a "Which mode" router, with review as the second mode. The frontmatter description now opens with the advise use case, so natural-language invocation matches the common question. Review-mode content is unchanged.
- The scorer's printed output and the report format lead with the verdict. `score.py` prints `VERDICT:` above the weighted total, labels the total "for the record", and the deciding-flip lines name the verdict they flip to before the recomputed number (previously `⇒ total 2.30, …`, which two careful readers in a row took as the headline — [skills#14, finding 6](https://github.com/QuantEcon/skills/issues/14)). The report's TL;DR opens with the full verdict and carries the score alongside as candidate quality for the record; the dimension table gains a verdict row so it still carries the decision when quoted on its own.
- `README.md` puts triage first throughout — the mode table, the invocation examples, and the mode sections — and states that triage builds no candidate: it measures the lecture as it stands and bounds what a conversion could deliver.

Nothing in the rubric, weights, gates, or scorecard JSON changed: the regression anchors (2.85 / 2.25) and the fixtures reproduce unchanged.

## 0.3.2 — 2026-08-03

**Fixed**

- The plugin README's status line said skill wiring was "tracked in skills#4". The wiring shipped in 0.3.0 — it is in that release's entry below — so the line pointed at an open issue for work that had already landed. 0.3.1 corrected the version number in that same sentence and left the stale clause standing, which is how a half-fixed line survives a review. It now describes the plugin as operational for workspace runs since 0.3.0 and points at this changelog for what shipped when.

## 0.3.1 — 2026-08-03

**Added**

- This changelog.

**Fixed**

- The plugin README's status line named `v0.2.0` — a version that was never released (see the note at the foot of this file). It now names `v0.3.0`, the release in which the evaluation system actually became runnable. That is a historical fact rather than a restatement of the current version, so it will not go stale again on the next bump.

## 0.3.0 — 2026-07-27

The evaluation system became runnable: a deterministic scoring engine, rubric v2 with verdict gates, two complete worked evaluations to copy from, a triage mode, and the install fix that made the plugin installable at all.

**Added**

- A runnable scoring engine: `python scripts/scoring/score.py <lecture-dir>` turns an evidence file into a scorecard. No score is ever typed by hand; the session shows the derivation table — every dimension score with the measured number and threshold band that produced it.
- `references/EVALUATION_FRAMEWORK.md` — the rubric in prose: seven weighted dimensions, numeric scoring anchors, structural checklists, verdict bands, worked HIGH/LOW examples. `SKILL.md` points here instead of restating weights, so recalibration cannot drift the copies.
- `scripts/scoring/EVIDENCE_TEMPLATE.json` — the judgement contract you fill in: measured numbers plus cited yes/no answers.
- Two complete worked evaluations in `references/examples/` (ge_arrow 2.85/5, markov_asset 2.25/5) with measurement scripts, results, evidence and reports — usable as per-lecture templates and as regression anchors, plus a README documenting where every evidence number came from.
- `scripts/calibration/bellman_bench.py` — the shared aiyagari Bellman benchmark that pins the "25x as-used = score 5" efficiency anchor.
- Rubric v2 verdict gates: the logic-and-design bug cap is derived from the correctness evidence (does it build, does it diverge under x64) rather than trusting a hand-set boolean, and the correctness score caps the verdict — a float32 catastrophe with no logic bug can no longer come out as "merge".
- A no-conversion verdict: a lecture whose baseline as-used total is under the 1 s materiality floor, with a slower candidate, now gets "don't convert" instead of a polished score of the rewrite.
- A sensitivity stamp on every scorecard: each scored input is perturbed one at a time (bools flipped, counts ±1, floats ±10%) and the verdict is stamped robust / fragile / robust-at-floor with the deciding flips listed.
- K-repeat as-used measurement: `run_all.py` repeats each side three times in fresh processes, the headline speedup is the median, and per-run spread feeds a contested-band annotation.
- Triage mode — "is this lecture worth converting at all?", answered from the existing lecture alone: baseline as-used total, workload-pattern match against the two calibrated poles, crossover check, readability-cost forecast, and the weight algebra that follows. Validated blind against the three known cases before being documented, including the documented limit that it cannot predict conversion-quality defects.
- `benchmark/README.md` — the plugin's user guide: review vs triage mode, the report format, the manual pipeline quickstart, and the one rule to remember (warm-only speedups are never the headline).
- Skill wiring for installed runs: evaluations are scaffolded under `<workspace>/benchmark-eval/<lecture>/` with the plugin read-only at `${CLAUDE_PLUGIN_ROOT}`, preconditions stated up front, and an extraction/replay diff check so the replay provably matches the lecture.
- A provenance stamp written to `results/env.json` (python/platform/numpy/jax/quantecon versions), including the titles of any failed pipeline step so a partial run cannot claim full provenance.
- `references/fixtures/rubric_v2` — synthetic evidence whose only job is to execute five v2 code paths the worked examples never touch; every source string is prefixed `SYNTHETIC:` so the numbers cannot be cited as evidence about a lecture.

**Changed**

- The skill is now `/benchmark:review-acceleration`, renamed from `/benchmark:eval-py-acceleration`. The rename was authored on 2026-07-21 in [#1](https://github.com/QuantEcon/skills/pull/1) but reached installed users only with this version bump.
- `score.py` takes a lecture directory path and works from any working directory, instead of resolving a lecture name against a package root.
- Correction of record on markov_asset: the lecture does build in notebook order — a stale global `err` masks a stray `err.throw()`, silently disabling the checkify stability validation. Worse than a crash, but not the build failure the original report claimed; erratum prepended to the report and the wording fixed in the examples README, `SKILL.md` and the plugin README.
- Two earlier certifications withdrawn as overstated: the reference replays deviate from the lectures' construction patterns (not "mirrors the lecture exactly"), and the as-used totals were single-pass, not medians over repeats (v2 restores repeats explicitly).
- The plugin README's triage baselines are labelled as triage-time (2026-07-21) measurements, and the framework and `SKILL.md` stop restating them — the gate reads each lecture's own `baseline_as_used_seconds`.
- `SKILL.md` forbids reporting robust-at-floor as plain robust: a verdict already in the bottom band cannot be perturbed downward, so zero deciding flips there is band geometry, not evidence strength.

**Fixed**

- Install was broken for every user. The repo-level `.claude-plugin/marketplace.json` omitted the required top-level `owner`, and every plugin entry — this one included — used a remote source `{"source": "github", "repo": "QuantEcon/skills", "path": "benchmark"}` that forced an install-time SSH re-clone of this repo. All three entries switched to the co-located relative-path form (`"./benchmark"`), so install uses the marketplace copy already on disk: no SSH, no auth prerequisite. Surfaced by [@xuanguang-li](https://github.com/xuanguang-li) testing this plugin, [#10](https://github.com/QuantEcon/skills/issues/10).
- The verdict band is computed from the rounded total, so the band always agrees with the number shown — raw floating-point sums could land at 2.4999999999999996 for combinations that are exactly 2.50 (797 of 78125 score combinations affected).
- `matches_under_x64` now caps correctness on its own. The extra `max_delta_shipped > 1e-8` conjunct made the guard structurally unable to fire in exactly the "wrong economics masked by low precision" case it exists to catch — such a candidate scored correctness 5 / total 3.25; it now scores correctness 1 / total 2.30, gated to net regression.
- `score.py` validates evidence before scoring and refuses evidence that omits a scored input the gates read, or that marks a structural criterion met without a citation. A missing `baseline_as_used_seconds` silently disarmed the no-conversion verdict, and stripping every citation left the score unchanged.
- The headline metrics (as-used total, cold start) are persisted to `results/as_used.json` and `results/cold_start.json` with the derived speedup, instead of existing only on the console while the docstrings claimed aggregation.
- The sensitivity stamp's denominator is honest: perturbations that raise are recorded in `perturbations_skipped` rather than silently counted as tested.
- `run_all.py` hardened — JSON scalar stdout lines no longer abort the pipeline, per-step return codes are tracked, the as-used speedup derivation guards both sides, and duplicate mode keys warn instead of silently overwriting.
- ge_arrow's `check_equivalence.py` writes `equivalence_x64.json` under `JAX_ENABLE_X64` instead of clobbering the as-shipped results.
- ge_arrow static metrics double-counted concept-token hits via a duplicated pattern (informational metric; 110 → 105).
- markov_asset's `statements_for_one_asset` renamed to `statements_for_one_result` to match the evidence-template vocabulary (values unchanged).
- Two files that were CRLF (`references/EVALUATION_FRAMEWORK.md`, the ge_arrow report) are normalized to LF, so a future one-line edit no longer renders as a whole-file diff.

## 0.1.0 — 2026-07-07

First release: the plugin appears in the marketplace with a documented but not yet runnable evaluation procedure — a v0 outline skill, no executable scripts.

- `/benchmark:eval-py-acceleration` — a v0 outline of the acceleration-review procedure: the five steps (equivalence check, static metrics, as-used benchmark, seven-dimension scoring, report), the seven weights (readability 0.25 deliberately above efficiency 0.15), the verdict bands, and the two calibration anchors (aiyagari Bellman ~25x faster as-used = HIGH; ge_arrow ~45x slower as-used = LOW).
- The guiding principle a user is meant to apply: lectures are teaching materials first, so "uses JAX" is never a goal in itself.
- `scripts/README.md` listing the eight measurement scripts still to be collected from [lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717).

---

**There is no 0.2.0.** It existed on a branch inside [#5](https://github.com/QuantEcon/skills/pull/5) and was superseded within the same pull request; because the repo squash-merges, `main` went 0.1.0 → 0.3.0 in one commit and 0.2.0 was never published. Nothing is missing from this file.
