# Reference examples — logic check and provenance

The two evaluations in this directory are the **canonical reference cases** for `/benchmark:review-acceleration`: they calibrate the rubric's thresholds, serve as the worked demonstrations of the method, and act as the **regression baseline** — any change to the scoring engine or the measurement templates must reproduce their scorecards. This document explains each example in detail and records the line-by-line logic review performed on 2026-07-21 (all scripts, all data files), so their accuracy is auditable rather than asserted.

**Review verdict: logic sound, methodology fair, every traceable number consistent with its source.** Known caveats are listed at the end — none changes either verdict.

---

## How an evaluation fits together

Each example directory is one self-contained evaluation of a lecture rewrite (NumPy `main` → JAX PR branch):

| Piece | Role |
|---|---|
| `scripts/model_old.py`, `model_new.py` | Faithful extractions of the two implementations. Any deviation from the lecture source is disclosed in the module docstring and is itself an evaluation finding |
| `scripts/*` (measurement) | Produce objective numbers into `results/*.json` |
| `evidence.json` | The **only place judgement is recorded**: measured numbers copied into quantitative slots (with source), structural checklist items answered true/false with citations to the diff |
| `results/scorecard.json` | Computed by `../../scripts/scoring/score.py` from the evidence — **no score is ever typed by hand** |
| `<lecture>_REPORT.md` | The human-readable verdict, written from scorecard + evidence |

The measurement standard throughout: **as-used, fresh-process** — replay the lecture's actual call sequence at its actual problem sizes in a new interpreter, so JAX trace/compile time counts; warm numbers are reported alongside, never alone.

---

## Example 1 — `ge_arrow` (lecture-python.myst#717) → **2.85/5, mixed/wash**

### The economics

The lecture solves a recursive competitive equilibrium with one-period Arrow securities. For each example economy `(s, P, ys)` it computes: the pricing kernel `Q` (β × marginal-utility ratio × transition probability), the resolvent `V = (I−Q)⁻¹` (or partial sums for finite `T`), wealth-distribution shares `α` from the initial-state row of `V`, continuation wealths `ψ`, bond price `PRF`, risk-free rate `R`, and value functions `J`. All economies are tiny: 2×2 or 3×3.

### The two implementations

- **Old (NumPy):** a mutable class; the lecture calls `wealth_distribution(s0) → continuation_wealths() → value_functionss()` **in that order** (each mutates `self`; the typo'd method name is real). Disclosed extraction deviation: the lecture's `pricing_kernel`/`continuation_wealths` referenced module-level globals `P, n, K`; the extraction uses `self.*` so the module is self-contained — recorded as a logic finding against the original, not silently repaired behaviour.
- **New (JAX):** one `NamedTuple` + a single jitted factory `compute_rc_model(s, P, ys, s0_idx, T)` with `static_argnames=("T", "s0_idx")` — every distinct `(s0_idx, T, shape)` triggers a fresh compile. Kept verbatim, **including** the patterns the evaluation criticizes (nested `fori_loop` scalar-scatter pricing kernel; `lax.cond` on the static `T`).

### The measurements and where each evidence number comes from

| Evidence slot | Value | Source | Logic-check notes |
|---|---|---|---|
| `max_delta_shipped` | 1.7e-4 | `check_equivalence.py` → `results/equivalence.json` | 11 cases: 4 economies × initial states + finite T=10. Compares Q, R, A, V[-1], α, ψ, J. Verified worst-case in the results file: 1.679e-4 (ex2, float32-as-shipped) |
| `matches_under_x64` | true | same script re-run with `JAX_ENABLE_X64=1` | max\|Δ\| ≈ 1.4e-14 under x64 → logic identical, drift is purely float32. *Caveat m3: the x64 run overwrites the same results file; regime not stamped* |
| `delta_prereq_concepts` | +6 (7→13) | `static_metrics.py` → `results/static_metrics.json` | **Hand-curated lists** (see caveat M1), disclosed as such in the script |
| `docstring_cov_new` | 0.55 (from 0.90) | same | AST-measured (objective) |
| `as_used_speedup` | **0.022× (≈45× slower)** | `as_used_total.py` (two fresh processes) → `results/as_used.json` *(generated per-run, not committed — the committed provenance is `evidence.json`)* | The replayed sequence mirrors the lecture exactly: ex1–ex3 × 2 initial states, the λ-sweep (NumPy: 100-iteration Python loop; JAX: one jitted `fori_loop` sweep, *as each lecture version does it*), ex4 × 3 states, finite T=10 × 2, T=10000 × 1. `block_until_ready` on every JAX call |
| `statements_for_one_result` | 1 (from 4) | `static_metrics.py` | Hand-asserted constant (caveat M1); the 4 is the ordered old protocol, the 1 is the single factory call |
| structural checklists | 1–4 criteria each | `evidence.json` citations | e.g. style meets only clean-call-sites → 1+1 = 2 |

Supporting (context, not scored directly): `benchmark.py` (cold ≈ 300 ms incl. compile at n=2; warm crossover at n≈10–25; scaling to n=400), `cold_start.py` (first call + the 133 ms recompile at a new `s0_idx`), `sweep_bench.py` (the JAX-favourable bound: the sweep is the one repeated workload).

### Why 2.85

Weighted: correctness 3 (logic identical under x64 but ships float32 with unflagged 4th–5th-significant-figure drift) + readability 2 (kernel one-liner becomes nested `fori_loop` plumbing) + efficiency 2 (45× slower as-used; warm wins never materialize at n≤3) + logic 4 (fixes the ordered-mutation/global-state/typo defects, minus the unvectorised O(n²) kernel) + style 2 + ergonomics 5 (one immutable call) + maintainability 3. The verdict captures the case's essence: **a structurally better rewrite that is slower and harder to read in the regime the lecture actually runs.**

---

## Example 2 — `markov_asset` (lecture-python.myst#654) → **2.25/5, net regression**

### The economics

Lucas-tree, consol, and call-option pricing over a Markov chain (default: 25-state Tauchen). Core operations are `eigvals` (stability check) and dense `solve` — O(n³) LAPACK work in both libraries, at n = 5 and 25.

### The two implementations

- **Old (NumPy):** mutable `AssetPriceModel` class + four pricing functions. Disclosed extraction deviation: the lecture's `__init__` reads a module-level `n=25`; the extraction defines it at module level too (global reliance recorded as a finding, mirroring ge_arrow).
- **New (JAX):** two `NamedTuple`s + factories; `checkify` for the stability assertion under `jit`; `lax.while_loop`/`fori_loop` solvers. Kept verbatim **including the build-breaking bug**: `call_option` contains a stray `err.throw()` referencing a name never bound in that scope (marked `# <-- VERBATIM from lecture` in `model_new.py`). Whether it runs is part of what is evaluated.

### The bug and the near-critical precision finding

- `smoke_test.py` demonstrates the crash exactly as the lecture calls it: `call_option_jit(...)` → `NameError: name 'err' is not defined`. Two lecture cells (consol/call-option cell, Exercise 1) depend on it → **the lecture does not build as shipped** → correctness 1 by the does-not-build override.
- `check_equivalence.py` additionally compares a **bug-patched copy** (verified line-identical to shipped logic minus the stray `err.throw()`) to establish that the *intended* logic is right: under x64 every asset matches NumPy to ≈1e-11. As shipped (float32) drift reaches **1.02e-2** on the exercise model — and that model's spectral radius (1.0618) sits **0.002 below** the stability bound 1/β = 1.0638, so float32 is not merely imprecise but close to flipping the stability check itself. Regimes are stored separately (`equivalence_x64_{True,False}.json`) with the x64 flag stamped in `_meta` — the pattern ge_arrow's template should adopt (caveat m3).

### The measurements

| Evidence slot | Value | Source | Logic-check notes |
|---|---|---|---|
| `builds` | false | `smoke_test.py`, recorded in `equivalence_x64_False.json` | Decisive: overrides the Δ bands → correctness 1 |
| `max_delta_shipped` | 1.02e-2 | `equivalence_x64_False.json` | Verified in file: 1.016e-2 |
| `matches_under_x64` | true | `equivalence_x64_True.json` | ≈1e-11 on all working assets |
| `delta_prereq_concepts` | +5 (8→13) | `static_metrics.py` | All five additions are checkify/JAX-structural (hand-curated; caveat M1) |
| `docstring_cov_new` | 0.75 (from 0.86) | same | AST-measured |
| `as_used_speedup` | 0.17× (≈6× slower) | `as_used_total.py` → `results/as_used.json` *(generated per-run, not committed)* | JAX side uses the patched `call_option` **so an end-to-end timing exists at all** — disclosed in the docstring and in the output record (`"mode": "jax_patched"`). Sequence mirrors the lecture: γ-sweep ×5, consol+call at β=0.9, exercise model (tree, consol, call, finite k=5,25) |
| `statements_for_one_result` | 3 (from 2) | `static_metrics.py` | The `(err, val)` unpack + `err.throw()` ceremony |
| logic checklist | 4/4 met, **capped at 3** | evidence citations | The cap (introduces a correctness bug) is the rubric's override working as designed |

`benchmark.py` (scaling) provides the context for efficiency: the workload is LAPACK-bound in both libraries, so JAX is slower at n=5 and n=25 and only edges ahead (~1.2–1.4×) at n≥250 — sizes this lecture never uses.

### Why 2.25

correctness 1 (does not build) + readability 2 + efficiency 2 + logic 3 (capped) + style 4 (the `lax` loops are the *correct* primitives here — a better JAX use than ge_arrow's) + ergonomics 3 + maintainability 2. The report's must-fix list is concrete: delete the stray `err.throw()`, enable x64 (genuinely required given the stability margin); those two fixes alone lift the total past the 2.5 line.

---

## The shared HIGH anchor — `../../scripts/calibration/bellman_bench.py`

`aiyagari.md` is JAX on both branches, so the HIGH end of the efficiency scale is calibrated on its *computational pattern*: the vectorised Bellman operator on a 200×7 grid, solved by VFI (~397 iterations), then re-solved 20× as an equilibrium loop would — the regime JAX is built for. Fairness properties verified: x64 enabled; the NumPy baseline uses the same broadcast/vectorised algorithm (not a strawman); implementations agree to ~1e-14; cold timing uses `_clear_cache()`; the equilibrium loop includes exactly one compile. Result: **~25× faster as-used** → pins "≥3× → score 5", with ge_arrow's 0.022× anchoring the LOW end.

---

## Verification performed (2026-07-21)

1. **Line-by-line review** of every script in the package (models, measurements, orchestration, scoring engine, calibration).
2. **Scorecard reproduction:** `score.py` regenerates both committed scorecards **byte-identically** from `evidence.json` alone.
3. **Evidence↔results cross-check (scripted):** every quantitative evidence slot matches its results-file source (Δprereq, docstring coverage, max\|Δ\| shipped, crash record, statements).
4. **Rubric edge audit:** brute force over all 5⁷ score combinations found FP band-edge misclassifications (797 cases), fixed by computing the verdict from the rounded total; neither reference case was affected.
5. **Fairness audit:** `block_until_ready` on every JAX timing; fresh processes for as-used; medians over repeats; identical call sequences per side; disclosed patches only where timing is otherwise impossible.

## Known caveats (recorded, deliberate, or pending upstream)

| ID | Caveat | Status |
|---|---|---|
| **M1** | `n_prerequisite_concepts` (readability driver, weight 0.25) and `statements_for_one_result` (ergonomics) are **hand-curated judgements encoded in the measurement scripts**, disclosed as such — not AST measurements. When the skill adapts templates to a new lecture it authors these lists, so they need the same citation discipline as the structural checklists. Proposed: move them into `evidence.json` as cited judgement slots. | Raised with the system's author (@xuanguang-li) on skills PR #5 |
| m3 | ge_arrow's `equivalence.json` does not stamp the x64 regime and is overwritten between regimes; markov_asset's split-file pattern (`equivalence_x64_{bool}.json` + `_meta`) is the better template | Adopt on next template revision |
| n6 | `sweep_bench` asymmetry: the old sweep computes only α (constructor + `wealth_distribution`), while the new one-call API forcibly computes everything — faithful to each API as used, but part of the measured sweep disadvantage is API-induced | Documented; by design (the API's cost is real) |
| — | markov_asset's as-used timing requires the bug-patched `call_option`; the shipped code cannot complete at all | Disclosed in script, output record, and report |
| — | Benchmarks are CPU-only; timings vary ±~15% run-to-run — the rubric keys on orders of magnitude | Framework limitation note |
