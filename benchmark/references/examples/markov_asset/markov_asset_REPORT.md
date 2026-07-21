# Evaluation Report — `markov_asset.md`: NumPy (`main`) → JAX (`update_markov_asset`)

Applies the system in [`../../EVALUATION_FRAMEWORK.md`](../../EVALUATION_FRAMEWORK.md) to the NumPy→JAX conversion of `markov_asset.md`. All numbers are reproduced by `scripts/run_all.py` (CPU, jax 0.4.35, numpy 2.1.3, quantecon) into `results/`. Every dimension score is **computed from [`evidence.json`](evidence.json) by the shared rubric** (`../../../scripts/scoring/rubric.py`) — see `results/scorecard.json` for the derivation.

## TL;DR — weighted score **2.25 / 5** → *net regression as shipped: do not merge until fixed*

The conversion **does not build**: the shipped `call_option` raises `NameError: name 'err' is not defined`, so the call-option and exercise cells crash. That single defect dominates the score. Once the bug is patched, the change is roughly *neutral* — genuinely better structure (immutable `NamedTuple` + factory functions, pure `test_stability`, idiomatic `lax` loops) offset by a readability drop from the `checkify` plumbing, ~6× slower as-used runtime at these tiny state spaces, and float32 precision drift up to `1e-2`.

| Dimension | Wt | Score | Weighted | how the score arises |
|---|:--:|:--:|:--:|---|
| Correctness & numerical fidelity | 0.20 | 1 | 0.20 | does not build (overrides Δ bands) |
| Readability & pedagogical clarity | 0.25 | 2 | 0.50 | Δprereq +5→2, docstrings 0.75→4 (worse-of-two) |
| Computational efficiency (as used) | 0.15 | 2 | 0.30 | as-used speedup 0.17× < 0.8 |
| Logic & design | 0.15 | 3 | 0.45 | 4/4 criteria met, **capped at 3** (introduces a bug) |
| Coding style & idiom | 0.10 | 4 | 0.40 | 3/4 criteria met (idiomatic primitives) |
| API ergonomics & reusability | 0.10 | 3 | 0.30 | 3 statements + fragile protocol |
| Maintainability & robustness | 0.05 | 2 | 0.10 | 1/4 criteria met |
| **Total** | **1.00** | | **2.25** | |

---

## What changed

| | Original (`main`) | Rewrite (`update_markov_asset`) |
|---|---|---|
| Library | NumPy | JAX (`jnp`, `lax`, `jit`, `experimental.checkify`) |
| Model container | mutable `AssetPriceModel` class (`__init__`) | `MarkovChain` + `AssetPriceModel` `NamedTuple`s + `create_*` factories |
| Growth function | stores callable `g`, computes `g(y)` on demand | precomputes and stores vector `G = g(state_values)` |
| Stability check | `self.test_stability` raises `ValueError` | module `test_stability` via `checkify.check` |
| Iterative solvers | Python `while` / `for` loops | `jax.lax.while_loop` / `jax.lax.fori_loop` |
| Call protocol | `v = tree_price(ap)` | `err, v = tree_price_jit(ap); err.throw()` |
| Prose | — | many title-case → sentence-case + link/figure edits (non-code) |

---

## Evidence by dimension

### 1 · Correctness & numerical fidelity → **1/5**
Three findings, from `smoke_test.py` and `check_equivalence.py`:

- **Build-breaking bug (decisive).** The shipped `call_option` contains a stray `err.throw()` referencing a name that is never bound in the function (it calls `p = consol_price(ap, ζ)`, which returns only `p`). `call_option_jit(...)` raises `NameError: name 'err' is not defined`. The lecture cells "consol price and call option value" and Exercise 1 both call it → **the lecture does not build as shipped.**
- **Logic otherwise equivalent.** Under `JAX_ENABLE_X64=1`, every *working* asset (`tree_price`, `consol_price`, `finite_call_option`, and a bug-patched `call_option`) matches NumPy to `max|Δ| ≈ 1e-11` across the default, β=0.9, and exercise models.
- **Silent precision drift.** As shipped (float32, no x64), drift reaches `1.02e-2` on the exercise model — amplified because its spectral radius `1.0618` sits a hair below the stability bound `1/β = 1.0638` (margin `0.002`), so float32 rounding is both inaccurate and close to flipping the stability check.

A lecture that crashes on build is the worst correctness outcome, hence score 1.

### 2 · Readability & pedagogical clarity → **2/5**
`static_metrics.py`:

| metric | old | new |
|---|--:|--:|
| prerequisite concepts | **8** | **13** (+5) |
| docstring coverage | 0.86 | 0.75 |
| code lines (model+funcs) | 74 | 101 (+36%) |
| statements to price one asset | 2 | 3 |

The five new prerequisites are all `checkify`-related or JAX-structural: `checkify.check`, the `(err, value)` return contract, `err.throw()`, two `NamedTuple`s + two factory functions, and the float32/x64 distinction. Every asset call site now carries boilerplate — `err, v = tree_price_jit(ap); err.throw()` — that has nothing to do with the economics. +5 prerequisites lands in the score-2 band.

### 3 · Computational efficiency (as used) → **2/5**
Replaying the whole lecture's asset-pricing sequence once in a fresh process (`as_used_total.py`, JAX side bug-patched so it can complete):

| NumPy total | JAX total | as-used speedup |
|--:|--:|--:|
| **~0.15–0.18 s** | **~0.7–1.1 s** | **~0.17× (≈5–6× slower)** |

*(Representative single-CPU medians; ±~15% run-to-run.)*

Scaling (`benchmark.py`, warm): the core operations are LAPACK `eigvals` + dense `solve` (`O(n³)`) in both libraries, so JAX has little to exploit on CPU — it is *slower* at the lecture's `n = 5` and `n = 25`, and only edges ahead (1.2–1.4×) at `n ≥ 250`, which this lecture never uses. Stated speed goal not met.

### 4 · Logic & design → **3/5**
Real improvements: the mutable class becomes two immutable `NamedTuple`s built by clear `create_ap_model` / `create_customized_ap_model` factories; `test_stability` is a pure function; the original's reliance on a module-global `n` in `__init__` is gone. Offset by the introduced logic defect (the stray `err.throw()`) and the extra `checkify` indirection.

### 5 · Coding style & idiom → **4/5**
3 of the 4 idiom criteria are met: `M = P * G**(-γ)` is properly vectorised, `jax.lax.while_loop` (infinite-horizon option) and `fori_loop` (finite horizon) are the *correct* primitives for these genuinely iterative solvers (a better use of JAX than `ge_arrow`'s loop-ported pricing kernel), and `checkify` is the idiomatic way to keep a runtime assertion under `jit`. The one failing criterion is clean call sites: every usage carries `(err, val)` unpack + `err.throw()` ceremony.

### 6 · API ergonomics & reusability → **3/5**
Factory functions and immutable models compose well (easily `vmap`-able over γ). But the `checkify` call protocol — unpack `(err, val)` then remember `err.throw()` — is error-prone, and the shipped code itself demonstrates the failure mode. `statements_for_one_result`: 2 → 3.

### 7 · Maintainability & robustness → **2/5**
Purity aids testing, but two silent traps remain for future editors: float32 by default (worsened by the `0.002` stability margin) and the `checkify` return contract that already produced one shipped `NameError`.

---

## Recommendation

**Must-fix before merge (correctness):**
1. Delete the stray `err.throw()` in `call_option` (it belongs only at the *call site* after `call_option_jit`). *(D1)*
2. Add `jax.config.update("jax_enable_x64", True)` — the near-critical spectral radius makes float32 genuinely risky here, not just imprecise. *(D1, D7)*

**Then, to lift the score toward "merge":**
3. Reduce `checkify` boilerplate at call sites (e.g. a small helper that unpacks and throws) to recover readability. *(D2, D6)*
4. Given the `O(n³)` LAPACK-bound workload at `n ≤ 25`, consider whether JAX earns its place in *this* lecture at all, or whether it is better reserved for the large, repeatedly-solved models where it wins (cf. the aiyagari calibration in `EVALUATION_FRAMEWORK.md`). *(D3)*

After fixes 1–2 the correctness score rises from 1 to ~3 and the total clears the 2.5 "wash" line; fixes 3–4 would push it toward the 3.0 "merge after addressing" threshold — the same profile as the `ge_arrow` conversion.
