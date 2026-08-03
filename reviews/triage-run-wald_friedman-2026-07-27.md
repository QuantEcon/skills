# Triage run — wald_friedman evaluated with no candidate (2026-07-27)

The first end-to-end exercise of `/benchmark:review-acceleration` in **triage mode** — the prospective, no-candidate path described in [`SKILL.md` § "Triage mode (no candidate yet)"](../benchmark/skills/review-acceleration/SKILL.md) — against a lecture that had never been evaluated. Two purposes: answer the conversion question for a real Table C candidate, and test the path that the two committed worked examples (both review-mode) do not cover. The plugin findings it produced are filed as [skills#14](https://github.com/QuantEcon/skills/issues/14); the lecture defect it tripped over is [lecture-python.myst#1008](https://github.com/QuantEcon/lecture-python.myst/issues/1008). Nothing was posted to any upstream PR.

Target chosen from the July 2026 rng-triage / JAX-candidacy review, whose Table C tags four lectures **Benchmark** — `navy_captain`, `wald_friedman`, `wald_friedman_2`, `likelihood_ratio_process_2` — none of which has a PR open. That absence is what forces triage mode: there is no candidate implementation to measure against.

## Setup

| | |
|---|---|
| Target | `lectures/wald_friedman.md` at blob `75b341e3` — byte-identical in the worktree, at `HEAD`, and in `origin/main`, so a valid `main` baseline |
| Mode | triage (baseline only). No candidate exists; `score.py` is not run, because the rubric scores a *delta* |
| Workspace | `benchmark-eval/wald_friedman/` inside the lecture checkout, plugin read-only via `CLAUDE_PLUGIN_ROOT`, per the wired SKILL.md |
| Environment | Python 3.13.9, numpy 2.3.5, jax 0.10.1, jaxlib 0.10.1, **numba 0.62.1**, quantecon 0.11.2, macOS arm64, 10 cores, CPU-only |

The numba version is recorded here by hand — `env_stamp.py` does not capture it (finding 3).

## Verdict

**No-conversion — do not convert `wald_friedman` to JAX. Binding constraint: only ~4% of the lecture's as-used time is addressable by a `vmap`-style rewrite.**

Baseline as-used total, replaying the lecture's real solver call sequence at its real sizes in a fresh interpreter, 3 repeats, median as headline: **5.586 s** (runs 5.755 / 5.586 / 5.276). That *clears* the rubric's 1 s no-conversion materiality floor by 5.6×. The floor is nonetheless the wrong instrument here — see finding 4.

Decomposed by kind of work:

| Cost | seconds | share | addressable by `vmap`? |
|---|---|---|---|
| `scipy.integrate.quad` inside `js_dist` / `compute_KL` | 2.644 | 47% | No — 1-D quadrature |
| numba compile (3 kernel signatures: 0.760 + 0.425 + ~0.216) | ~1.40 | 25% | No — JAX substitutes its own, typically larger |
| pure-Python driver loops (`run_markov_sprt` 1.122, `run_var_sprt` 0.055) | ~1.18 | 21% | Not by JAX — `for i in range(N)` over N=1,000 calling `@njit` singles; `prange` is the fix |
| **actual `prange` simulation work** | **~0.24** | **~4%** | **Yes** |
| residual / interpreter overhead | ~0.12 | 2% | — |

The lecture has exactly two `prange` kernels — `run_sprt_simulation` (cell @507) and `run_adjusted_thresholds` (cell @905). Together they are ~0.24 s of 5.586 s, so the **Amdahl ceiling on the whole conversion is 1.045×**, before JAX pays back the ~1.4 s of numba compilation it would replace.

The headline "N=20,000 simulation" that makes this lecture look like a candidate runs in **5.0 ms** warm. Its 0.789 s stage is ~0.76 s of numba compilation and ~5 ms of work. A warm-only or whole-cell measurement reads that as 0.8 s of simulation and points the other way — this is the single fact that decides the lecture, and the as-used discipline is what exposed it.

### The `vmap` waste ratio

A conversion replaces `prange` over independent SPRT paths with `vmap` over `lax.while_loop`. A batched `while_loop` steps **every** lane until the **last** lane's condition goes false, so batched cost tracks the maximum stopping time, not the mean:

| Cell | mean stop | max stop | max/mean |
|---|---|---|---|
| headline, cell @507 | 1.59 | 10 | 6.3× |
| `params_1`, cell @695 | 1.08 | 4 | 3.7× |
| `params_2`, cell @695 | 11.07 | 72 | 6.5× |
| `params_3`, cell @695 | 41.83 | 311 | 7.4× |

So the ~0.24 s of addressable work becomes 0.9–1.8 s of lane-steps. The conversion makes the only part it can touch do 3.7–7.4× more work. This is the JAX style guide's sequential case and its own answer applies.

### Readability cost

The kernel a conversion must rewrite *is* the pedagogical content — the sequential stopping rule, in a lecture titled *A Problem that Stumped Milton Friedman (and that Abraham Wald solved by inventing sequential analysis)*. A JAX version forces `jax.random` key splitting, `vmap`, **`lax.while_loop` with split `cond_fun`/`body_fun` and a carry tuple**, `jnp` immutability, and `gammaln` for the beta density (`math.gamma` is not traceable). The third is the expensive one: "draw, update, check, stop", readable top-to-bottom in six lines, becomes a carry threaded through two callbacks, or a fixed-`max_n` scan with masking that no longer *looks* like sequential stopping. Against the weights — efficiency 0.15 can contribute at most +0.30 and here contributes nothing; readability 0.25 losing two bands costs −0.50 — the case cannot break even.

### If the 5.59 s is worth reducing

In measured order, none of it involving JAX: `js_dist`/`compute_KL` at 2.64 s (47%) — 100 combos × 4 `scipy.quad` calls, each rebuilding two numba-jitted densities; closed-form Beta KL via `betaln` removes most of it. Then the pure-Python `run_markov_sprt`/`run_var_sprt` at 1.18 s (21%) — `prange`, consistent with the rest of the lecture. Then numba compile at ~1.4 s (25%), largely irreducible, though `cache=True` helps re-runs. Each is a larger win than the entire conversion's ceiling and none costs the reader a prerequisite concept.

## Corrections to Table C

- The artifact's evidence for tagging this lecture is "simulations up to N=20,000 across three `prange` loops". The lecture has **two** `prange` loops (cells @528 and @906), not three.
- N=20,000 is not a bottleneck: **5.0 ms** warm. The `prange` loops are ~4% of the lecture's time.
- `wald_friedman_2` is tagged "convert together with `wald_friedman`". Since `wald_friedman` is a no-conversion, that coupling should be re-examined rather than inherited. `likelihood_ratio_process_2` shares the beta-density and sequential-stopping idiom, so both the waste ratio and the defect below are worth checking there directly.

## Findings (the point of a triage run)

1. **No timeout on measurement subprocesses.** `run_all.py` calls `subprocess.run(argv, cwd=HERE, check=False)` with no `timeout=`. Lecture code with data-dependent loops can fail to terminate, and when it does the pipeline hangs with no output and no error — indistinguishable from slow progress. This happened twice here, ~10 minutes each, saturating all ten cores. A `timeout=` feeding `steps_failed` converts a hang into recorded provenance, which is what the stamp already exists to do.
2. **Triage mode has no scaffold.** `SKILL.md` documents it, including "adapt just the baseline half of an `as_used_total.py` template", but the plugin ships nothing: `grep -rn triage` over `scripts/` and `references/` matches only three comment lines in `rubric.py`; both worked examples are review-mode; `EVIDENCE_TEMPLATE.json` and `score.py` assume a candidate. This run had to invent a cell extractor, a `build_model_old.py` slicing definition-bearing regions out of the lecture, a verbatim-fidelity gate, and a triage driver — ~250 lines standing between the question and any answer. Table C alone lists eight candidates with no PR against seven open conversion PRs, so triage is the more common entry point and the unsupported one.
3. **`env_stamp.py` does not record numba.** It stamps `numpy`, `jax`, `jaxlib`, `quantecon`. Every baseline in this plugin's remit is NumPy+Numba, and numba's version and threading layer move the measured numbers; a run on a different numba, or a different `NUMBA_NUM_THREADS`, is not comparable and `results/env.json` would not show it. Adding `numba` and `scipy` covers it.
4. **The 1 s materiality floor measures the wrong quantity.** `NO_CONVERSION_BASELINE_S = 1.0` is read against `baseline_as_used_seconds`. This lecture clears it 5.6× while being 96% unreachable by the conversion in question. The floor answers "is there time here?" when the decision needs "is there *addressable* time here?" Both blind-validated don't-convert anchors (ge_arrow 0.035 s, markov_asset 0.18 s) sit two orders of magnitude *below* the floor, so clears-the-floor-but-nothing-to-sell is a shape the calibration has not exercised. `rubric.py`'s comment is candid that the threshold's placement is not load-bearing; this run suggests the *quantity* may be. Open design call on skills#14: key the gate on addressable time (which requires the decomposition to become a measured artifact), or leave the gate — it only fires in review mode, where a candidate exists — and have triage report the addressable fraction as a first-class number.
5. **Subprocess output is captured, not streamed.** `capture_output=True` means a long-running probe emits nothing until it exits; combined with finding 1, a hang looks like slow progress. Tee-ing progress to a file under `results/` is the cheap workaround.

## Defect found in the lecture

`sprt_single_run` (cell @507) is `while True` with no iteration cap, and its increment can go NaN. `p(x,a,b) = r * x**(a-1) * (1-x)**(b-1)` diverges at the endpoints when `a<1` or `b<1`; `np.random.beta(0.5, 0.4)` does return exactly `1.0`, at which point both densities are `inf`, the increment is `log(inf) - log(inf) = nan`, and `log_L` is NaN from then on. Every comparison against NaN is False, so neither stopping branch can ever fire and the call spins forever — no crash, no warning.

Reachable with the lecture's **own** `params_3` = Beta(0.5,0.4) vs Beta(0.4,0.5), measured at **1 non-terminating path per 200,000** (first at seed 12837; NaN first appears at step n=58 with `z = 1.0`). All four shipped cells were replayed at their exact `(seed0, N)` and all four terminate — by luck of their seed ranges, not by construction. The lecture's own sibling kernels already guard (`markov_sprt_single_run` caps at `max_n = 10000`, `var_sprt_single_run` at `max_T = 500`); only the headline SPRT is unbounded. Filed with a verified reproducer as lecture-python.myst#1008.

## What held up

The prescribed procedure did real work. The instruction to **diff the extracted code and the replayed call sequence against the lecture's cells before measuring** caught drift on its first run; making it a hard gate — every code line in the extracted module and every replayed call must appear verbatim in the lecture source, compared right-stripped so the lecture's trailing whitespace does not produce false failures — cost little and is the piece this run would least want to be without. The **as-used over warm** discipline is the whole ballgame on this lecture (5.0 ms behind 760 ms of compilation). The fresh-process K-repeat with a median headline behaved well: 5.755 / 5.586 / 5.276 s, tight enough that no conclusion rests on run-to-run noise.

## Method

Because triage ships no scaffold, the workspace was improvised; it is not committed. The shape, for whoever builds finding 2's bundle:

1. **`extract_cells.py`** — parse the lecture's MyST `{code-cell}` blocks into `cells.txt`, each tagged with its source line, so nothing downstream is retyped.
2. **`build_model_old.py`** — concatenate explicit, auditable line-range slices of the definition-bearing cells into `model_old.py`, leaving the driver statements out (the as-used replay owns those).
3. **`verify_extraction.py`** — the fidelity gate. Every code line in `model_old.py`, and every line inside the `# REPLAY-BEGIN` / `# REPLAY-END` markers of `as_used_total.py`, must appear verbatim in the lecture. Exits non-zero otherwise.
4. **`as_used_total.py`** — replay the lecture's driver sequence, verbatim between markers, with per-stage timers outside them; one JSON line to stdout.
5. **`run_triage.py`** — K fresh-process repeats, median headline, plus the auxiliary probes, then the provenance stamp via `CLAUDE_PLUGIN_ROOT`.

Deviations from the lecture's code, all disclosed: plotting helpers are excluded from the timed sequence (`plot_likelihood_paths`, which does carry real compute, was timed separately at 0.278 s and reported apart); and the pathology scan adds an iteration cap to a *copy* of `sprt_single_run`, the cap being the instrument.

## Conclusion

Triage mode reaches a defensible verdict on a lecture with no candidate, and the verdict is decided by a quantity the current rubric does not measure — the addressable share, not the total. The procedure's measurement discipline held; its scaffolding did not exist. Both are actionable: findings 1, 3 and 5 are small patches, finding 2 is a bundle to build, finding 4 is a design call for the rubric's author.
