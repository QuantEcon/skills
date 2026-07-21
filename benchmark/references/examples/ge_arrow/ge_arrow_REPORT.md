# Evaluation Report — `ge_arrow.md`: NumPy (`main`) → JAX (`update_ge_arrow`)

Applies the system in [`../../EVALUATION_FRAMEWORK.md`](../../EVALUATION_FRAMEWORK.md) to the only code change on branch `update_ge_arrow`. All numbers below are reproduced by `scripts/run_all.py` (CPU, jax 0.4.35, numpy 2.1.3) into `results/`. Every dimension score is **computed from [`evidence.json`](evidence.json) by the shared rubric** (`../../../scripts/scoring/rubric.py`) — see `results/scorecard.json` for the derivation.

## TL;DR — weighted score **2.85 / 5** → *net mixed, slightly negative for this lecture*

The rewrite is **better software** (one-call pure API, real bug fixes) but a **worse lecture** on the two axes that matter most here: it is harder to read and — contrary to the stated motivation — **slower in every regime this lecture actually runs**, while silently dropping numerical precision.

| Dimension | Wt | Score | Weighted | how the score arises |
|---|:--:|:--:|:--:|---|
| Correctness & numerical fidelity | 0.20 | 3 | 0.60 | ships float32 → drift 1.7e-4 ∈ (1e-8,1e-3] |
| Readability & pedagogical clarity | 0.25 | 2 | 0.50 | Δprereq +6→2, docstrings 0.55→2 (worse-of-two) |
| Computational efficiency (as used) | 0.15 | 2 | 0.30 | as-used speedup 0.022× < 0.8 |
| Logic & design | 0.15 | 4 | 0.60 | 3/4 criteria met |
| Coding style & idiom | 0.10 | 2 | 0.20 | 1/4 criteria met (only clean call sites) |
| API ergonomics & reusability | 0.10 | 5 | 0.50 | 1 statement per result |
| Maintainability & robustness | 0.05 | 3 | 0.15 | 2/4 criteria met |
| **Total** | **1.00** | | **2.85** | |

---

## What changed

| | Original (`main`) | Rewrite (`update_ge_arrow`) |
|---|---|---|
| Library | NumPy | JAX (`jnp`, `lax`, `jit`) |
| Container | mutable `class` with methods | immutable `NamedTuple` of results |
| Entry point | build object + 3 ordered method calls | one `@jit` function `compute_rc_model` |
| Loops | Python `for` (×6) | `jax.lax.fori_loop` / `lax.cond` (0 Python loops) |
| Infinite-horizon flag | `T=None` | `T=0` |
| Notable | typo `value_functionss`; uses global `P,n,K` | fixes both |

---

## Evidence by dimension

### 1 · Correctness & numerical fidelity → **3/5**
`check_equivalence.py` over all 11 example/initial-state combinations:

- **Under float64:** every object matches, `max|Δ| = 1.4e-14` → the rewrite's *logic is identical*. ✅
- **As the lecture actually runs (float32 default, no `jax_enable_x64`):** `ex2` deviates by `1.7e-4`; several others ~`1e-4`. The published tables move in the 4th–5th significant figure. ❌ unflagged precision loss.

→ Correct economics, silently reduced precision. Score capped at 3.

### 2 · Readability & pedagogical clarity → **2/5**
`static_metrics.py`:

| metric | old | new |
|---|--:|--:|
| prerequisite concepts | **7** | **13** |
| docstring coverage | **0.90** | **0.55** |
| code lines (model def) | 119 | 161 |
| sub-definitions | 10 | 22 |
| Python loops a reader parses | 6 | 0 (replaced by `fori_loop` closures) |

The pricing kernel — mathematically just $Q_{ij}=\beta(y_j/y_i)^{-\gamma}P_{ij}$ — becomes two nested `fori_loop`s with `.at[j].set(...)` carries. For a lecture whose economies are 2×2, this is pure cognitive overhead. **Biggest single driver of the negative verdict** (and the heaviest-weighted dimension).

### 3 · Computational efficiency (as used) → **2/5**
This was the stated motivation, so it matters that it is **not achieved here.**

**Headline metric — replaying the *entire* lecture solver sequence once in a fresh process (`as_used_total.py`):**

| NumPy total | JAX total | **as-used speedup** |
|--:|--:|--:|
| **0.035 s** | **1.56 s** | **0.022× — i.e. ~45× slower** |

Per-regime detail explaining why:

| Regime (n=2 unless noted) | NumPy | JAX | Result |
|---|--:|--:|---|
| First solve (cold, incl. compile) | 6.2 ms | 286 ms | **46× slower** |
| Recompile per new `s0_idx`/`T` | — | 133 ms | each distinct call recompiles |
| Warm repeat | 0.032 ms | 0.022 ms | 1.4× faster *(never used)* |
| λ-sweep (100 pts), as run once | 1.8 ms | 300 ms cold | **170× slower** |
| λ-sweep warm | — | 0.37 ms | 4.8× faster *(never realized)* |

Scaling crossover (`benchmark.py`): NumPy and JAX-warm are even near **n≈10**; JAX wins **2–6×** for `n = 25…200`. **The lecture never exceeds n=3.** For calibration, the same machinery on the large, repeatedly-solved aiyagari pattern (shared `../../../scripts/calibration/bellman_bench.py`) is **25× faster** — a score-5 case. `ge_arrow`'s `0.022×` maps to **score 2** (< 0.8×, but correct and fixable).

### 4 · Logic & design → **4/5**
Genuine improvements, all verified in the diff:
- removes order-dependent stateful methods (old required `wealth_distribution → continuation_wealths → value_functionss`);
- removes reliance on module-level `P, n, K` (a latent bug in the original);
- fixes the `value_functionss` typo;
- de-duplicates (`R` no longer recomputes `sum(Q)`); returns one result object.

Minus one point: the pricing kernel is ported as an `O(n²)` scalar loop instead of a vectorised outer product.

### 5 · Coding style & idiom → **2/5**
Only 1 of the 4 idiom criteria is met (clean call sites / `NamedTuple` naming). The three computational-idiom criteria fail: not vectorised where natural (the nested-`fori_loop` pricing kernel), wrong control-flow primitive (`fori_loop` where broadcasting fits), and an anti-idiomatic `jax.lax.cond(T==0, …)` that **traces both branches** although `T` is already a static argument (a plain `if` would compile only the needed branch).

### 6 · API ergonomics & reusability → **5/5**
`statements_for_one_result`: **4 → 1**. `compute_rc_model(s, P, ys, s0_idx=1, T=10)` returns an immutable bundle; fully `jit`/`vmap`-composable. Clear win.

### 7 · Maintainability & robustness → **3/5**
Purity aids unit testing, but `jit` + `static_argnames` + 3-deep closures hinder step-debugging, and the float32 default is a silent trap for future reuse.

---

## Recommendation

The conversion is **not yet a net improvement for this particular lecture.** Two paths:

**A. Keep NumPy for `ge_arrow`.** The models are 2×2/3×3; NumPy is faster as-used, more readable, and matches the published numbers. Reserve JAX for lectures with large, repeated, fixed-shape computation.

**B. If JAX is kept, fix these before re-scoring** (each maps to a dimension):
1. **Vectorise the pricing kernel** → `Q = β*(y[None,:]/y[:,None])**(-γ)*P` *(D2 readability, D3 efficiency, D5 idiom).*
2. **Enable float64**: `jax.config.update("jax_enable_x64", True)` so published numbers are preserved *(D1, D7).*
3. **Reduce recompiles**: avoid making `s0_idx`/`T` static, or vectorise over `s0_idx`, so the lecture doesn't pay a fresh compile per call *(D3).*
4. **Restore docstrings** on the nested helpers; replace `lax.cond` on a static `T` with a Python `if` *(D2, D5).*

Re-running `run_all.py` after these fixes would likely lift readability to ~3, efficiency to ~3, and the total above the 3.0 "merge after fixes" line.
