# Validation run — ge_arrow re-evaluated from a fresh checkout (2026-07-22)

The dry run required by [skills#8](https://github.com/QuantEcon/skills/issues/8) §3: check out the lecture repo at the state prior to the motivating PR, drive the wired skill procedure end-to-end in a user workspace, and cross-compare against the committed reference evaluation. Target: **ge_arrow / [lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717)** — the PR the system was first developed on, still open, and independent of the #654 acceptance test that issue #8 reserves for the adjudicated run. Nothing was posted to either upstream PR.

## Setup

| | |
|---|---|
| Refs | base `8cfba4c` (merge-base of `update_ge_arrow` with `main` — also #654's merge-base), head `8c2d0d7` (PR head; last pushed 2026-07-09, so identical to the state the reference evaluation measured) |
| Workspace | fresh partial clone; evaluation under `benchmark-eval/ge_arrow/` per the wired SKILL.md; plugin read-only via `CLAUDE_PLUGIN_ROOT` |
| Environment | python 3.13.9, **jax 0.10.1, numpy 2.3.5**, macOS arm64 — deliberately *not* the reference environment (jax 0.4.35, numpy 2.1.3), so this also tests robustness to library drift |

## Cross-comparison

| Quantity | Reference (committed) | Fresh re-run | Band agreement |
|---|---|---|---|
| Candidate extraction | `model_new.py` | byte-identical to lecture cell at head | verbatim confirmed |
| Baseline extraction | `model_old.py` (globals fix disclosed) | matches, two deviation classes (below) | confirmed with findings |
| float32 worst max\|Δ\| | 1.7e-4 (ex2) | 1.01e-4 (ex3_s0/J) | same band → correctness 3 |
| x64 worst max\|Δ\| | 1.4e-14 | 1.42e-13, all match | same conclusion (≪1e-8) |
| as-used speedup | 0.022× (single pass) | 0.0251× (median of 3; spread 0.0227–0.0353× within one band) | same band → efficiency 2 |
| baseline as-used total | 0.035 s | 0.0292 s (median of 3) | both under the 1 s floor |
| Δprereq / docstrings / statements | +6 / 0.90→0.55 / 1 | identical | identical |
| **Weighted total** | **2.85** | **2.85** | exact |
| **Verdict** | no-conversion (candidate band mixed/wash) | no-conversion (candidate band mixed/wash) | exact |
| **Sensitivity** | fragile, 3 deciding flips | fragile, same 3 flips (`builds`, `matches_under_x64`, `good_algorithmic_choices`) | exact |

The v2 additions all exercised on real data: K-repeat medians with per-run speedups, the no-conversion verdict, the sensitivity stamp, `CLAUDE_PLUGIN_ROOT` resolution from a workspace, and the per-run provenance stamp (which recorded the environment difference).

## Findings (the point of a dry run)

1. **ge_arrow's `check_equivalence.py` had no x64 handling** — it always wrote `results/equivalence.json`, so the x64 run clobbered the as-shipped run, and the evidence file's dual-regime citation was not reproducible from `run_all.py` alone (markov_asset's template already wrote per-regime files). **Fixed**: the script now writes `equivalence_x64.json` when `JAX_ENABLE_X64=1` and records the regime in its summary.
2. **Undisclosed cosmetic deviation in the baseline extraction**: `model_old.py` normalises arithmetic spacing (`T+1` → `T + 1`, `t-1` → `t - 1`) beyond its one disclosed deviation class (the globals fix). Semantics identical; now disclosed in the file's fidelity note per the v2 verbatim rule.
3. **Median-of-ratios vs ratio-of-medians**: with `as_used_runs` present the engine scores the median of per-run speedups (0.0251×) rather than the ratio of median totals (0.0244×). Same band here; the evidence template documents `as_used_runs` as per-run speedups, which is the authoritative form.
4. Upstream provenance was recorded by PR number and branch but **not by SHA**; both committed evidence files now carry `source_pr` + base/head SHAs (both PRs share merge-base `8cfba4c`).

## Conclusion

The skill procedure runs end-to-end from a clean checkout in a user workspace and **reproduces the reference evaluation exactly at the level the rubric claims to be reproducible** (bands, total, verdict, sensitivity stamp) across a major JAX version change, with measured quantities moving only within their bands. The #654 acceptance run can proceed on this procedure.
