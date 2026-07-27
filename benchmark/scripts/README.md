# benchmark plugin — scripts

The deterministic core of `/benchmark:review-acceleration`: the shared scoring engine and the efficiency calibration. Developed and validated by [@xuanguang-li](https://github.com/xuanguang-li) on [lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717) and [#654](https://github.com/QuantEcon/lecture-python.myst/pull/654).

## Layout

```
scoring/
  rubric.py               the standard as code: evidence → score, deterministically
  score.py                engine/CLI: <lecture-dir>/evidence.json → results/scorecard.json
  env_stamp.py            provenance stamp: <lecture-dir>/results/env.json (+ failed steps)
  EVIDENCE_TEMPLATE.json  the judgement contract a new evaluation fills in
calibration/
  bellman_bench.py        shared aiyagari Bellman benchmark — pins the "25× as-used
  bellman_bench.json      = score 5" efficiency anchor
```

All commands below run from the plugin root (`benchmark/` in this repo).

The rubric in prose — dimensions, weights, anchors, checklists, verdict bands, worked HIGH/LOW examples — is [`../references/EVALUATION_FRAMEWORK.md`](../references/EVALUATION_FRAMEWORK.md). Two complete worked evaluations (measurement scripts, results, evidence, reports) live in [`../references/examples/`](../references/examples/) and double as the regression baseline the skill must reproduce.

## How scoring works

Scores are **never typed by hand** — each is a deterministic function of evidence:

1. **Measure** — `python references/examples/<lecture>/scripts/run_all.py` runs the per-lecture measurement scripts and writes `results/*.json` plus a provenance stamp (`results/env.json`: Python/platform/library versions and any failed steps — the seed of the QuantEcon/meta#335 shared result schema; generated per-run, not committed). The as-used steps repeat 3× per side in fresh processes; the headline speedup is a **median**, with per-run values kept for the contested-band check.
2. **Record evidence** — fill `<lecture>/evidence.json` (copy `scoring/EVIDENCE_TEMPLATE.json`): measured numbers into the quantitative slots with their source, and each structural checklist item answered true/false **with a citation to the diff**.
3. **Score** — `python scripts/scoring/score.py references/examples/<lecture>` applies `rubric.py` and writes `results/scorecard.json`, printing the derivation of every score, the final verdict (after the v2 correctness gates and the no-conversion rule), and the one-flip **sensitivity stamp** (robust/fragile with deciding flips).

## Evaluating a new lecture

Per-lecture measurement scripts are **adapted templates, not a fixed harness** — copy an existing example and adapt (this is the step the skill automates):

```bash
conda activate quantecon                        # jax 0.4.x, numpy 2.x, quantecon
mkdir -p references/examples/<lecture>/{scripts,results}
cp scripts/scoring/EVIDENCE_TEMPLATE.json references/examples/<lecture>/evidence.json
# drop in model_old.py (from main) and model_new.py (from the PR branch),
# adapt check_equivalence / static_metrics / benchmark / as_used_total from an
# existing example, wire them into run_all.py, then:
python references/examples/<lecture>/scripts/run_all.py
python scripts/scoring/score.py references/examples/<lecture>
# write <lecture>_REPORT.md from the scorecard + evidence
```

Benchmarks are CPU-only; timings vary ±~15% run-to-run, so the rubric keys on orders of magnitude, not exact milliseconds.
