# A Quantitative Evaluation System for JAX Rewrites of QuantEcon Lectures

This document defines a **reusable, quantitative system** for deciding whether rewriting a QuantEcon lecture's code (e.g. converting NumPy → JAX) actually *improves the lecture*. It was designed against the first such change, `lectures/ge_arrow.md` (branch `update_ge_arrow` vs `main`), and is applied to it in [`ge_arrow_REPORT.md`](examples/ge_arrow/ge_arrow_REPORT.md).

The guiding principle: **these are teaching lectures first and programs second.** A rewrite that makes the code faster or more "modern" but harder for a learner to read, or that silently changes the numbers, is not automatically an improvement. The system therefore weights pedagogy heavily and never treats "uses JAX" as a goal in itself — JAX must *earn* its place on each lecture.

---

## 1. The seven dimensions

| # | Dimension | Weight | What it answers |
|---|-----------|:---:|---|
| 1 | Correctness & numerical fidelity | 0.20 | Does the new code compute the *same economics*, at the *same precision*? |
| 2 | Readability & pedagogical clarity | 0.25 | Can a learner follow it? Does the code mirror the math? |
| 3 | Computational efficiency (as used) | 0.15 | Is it faster *in the regime the lecture actually runs*? |
| 4 | Logic & design | 0.15 | Are functions natural, pure, non-repetitive, bug-free? |
| 5 | Coding style & idiom | 0.10 | Idiomatic Python/JAX and consistent with house style? |
| 6 | API ergonomics & reusability | 0.10 | How easy is the object to call, compose, and reuse? |
| 7 | Maintainability & robustness | 0.05 | How easy to test, debug, and safely extend later? |

Weights sum to 1.0. **Readability (0.25) outranks efficiency (0.15)** on purpose: the audience is learners, and most lecture models are tiny. Adjust the weights per lecture family if needed (e.g. a "performance" lecture could raise dimension 3), but record any change.

Each dimension is scored **1–5** against the anchors below, then combined:

```
weighted_total = Σ  weight_d × score_d        (range 1–5)
```

### Interpreting the total

| Total | Meaning |
|---|---|
| **≥ 4.0** | Clear improvement — merge. |
| **3.0 – 3.9** | Net positive but with fixable regressions — merge after addressing them. |
| **2.5 – 2.9** | Mixed / wash — improvements offset by real regressions; revisit before merging. |
| **< 2.5** | Net regression — do not merge as-is. |

A score is only as good as its evidence. **Every dimension must cite at least one measured number or a concrete code excerpt** (see §3). The scripts in [each example's `scripts/`](examples/) produce the numbers automatically.

---

## 2. Scoring anchors + worked high/low examples

For each dimension we give (a) the metric(s) that quantify it, (b) the 1–5 anchors, and (c) a **HIGH-scoring** and **LOW-scoring** example so reviewers agree on what "good" looks like.

**Dimensions 1, 2, 3, 6 carry numeric score thresholds** (a measured number maps directly to 1–5); dimensions 4, 5, 7 are structural and scored against criteria + cited evidence. The numeric thresholds were calibrated against two real, *measured* end points: a HIGH case (the aiyagari Bellman pattern, 25× faster as-used) and a LOW case (the full `ge_arrow` lecture, 45× slower as-used).

**Every example below is real code already in `lecture-python.myst`**, cited by `file:line`, not a hypothetical. The HIGH examples are mostly drawn from lectures the QuantEcon team has already converted well to JAX — `aiyagari.md`, `lake_model.md` — and the LOW examples from `ge_arrow.md` and the older class-based `odu.py`. (Line numbers are as of branch `update_ge_arrow` / `main` at the time of writing; search the cited symbol if they drift.)

### How a score is computed (no hand-typed numbers)

The rubric is machine-encoded in [`scoring/rubric.py`](../scripts/scoring/rubric.py) so that **a score is a deterministic function of evidence**, applied identically to every lecture. The workflow — and the contract an AI skill follows — is:

1. **Measure** (per lecture, objective): run `<lecture>/scripts/run_all.py` → `<lecture>/results/*.json`.
2. **Record evidence** (per lecture): fill `<lecture>/evidence.json` (schema: [`scoring/EVIDENCE_TEMPLATE.json`](../scripts/scoring/EVIDENCE_TEMPLATE.json)) — copy the measured numbers into the quantitative slots (noting the source file) and answer each structural checklist item true/false **with a citation to the diff**. This file, plus the measured results, is the *only* per-lecture input.
3. **Score** (shared, mechanical): `python scripts/scoring/score.py references/examples/<lecture>` applies `rubric.py` and writes `<lecture>/results/scorecard.json`, printing the derivation of every score. No score is ever written by hand; to change one you change a measured metric, a checklist answer, or the standard itself.

**Quantitative dimensions (1, 2, 3, 6)** map a measured number to 1–5 via the threshold tables in the sections below (calibrated against two measured end points: the aiyagari Bellman pattern at 25× faster as-used, and the full `ge_arrow` lecture at 45× slower).

**Structural dimensions (4, 5, 7)** each have a fixed **4-item yes/no checklist**; the score is **`1 + (number of criteria met)`**, plus a small number of documented override caps. The checklists are:

| Dim | Criterion 1 | Criterion 2 | Criterion 3 | Criterion 4 | Override |
|---|---|---|---|---|---|
| **4 Logic & design** | pure / no order-dependence | no global state | good algorithmic choices | fixes prior bugs | introduces a correctness bug → **cap 3** |
| **5 Style & idiom** | vectorised where natural | correct control-flow primitive | no anti-idiomatic constructs | clean call sites & naming | — |
| **7 Maintainability** | pure / unit-testable | dtype/precision-safe | no footgun for editors | robust (no brittle conditions) | — |

Worked check (from the two committed `evidence.json` files): `ge_arrow` style meets only *clean call sites* → 1+1 = **2**; `markov_asset` logic meets all four but introduces a build-breaking bug → 1+4 = 5, capped to **3**.

---

### Dimension 1 — Correctness & numerical fidelity · weight 0.20

**Metrics** (from `check_equivalence.py`):
- `all_equivalent` — do all equilibrium objects (Q, R, A, V, α, ψ, J) match the original across every example economy?
- `max_abs_err` — largest absolute deviation from the original numbers.
- default dtype / precision (float32 vs float64).

**Anchors (numeric — keyed to `max|Δ|` vs the original, as the lecture ships)**

| Score | as-shipped `max\|Δ\|` | precision |
|:---:|:---:|---|
| 5 | ≤ 1e-10 | float64 preserved; any diff explained |
| 4 | ≤ 1e-8 | preserved |
| 3 | logic matches under x64 (≤1e-10) **but ships float32** → 1e-5…1e-3 drift, unflagged |
| 2 | 1e-3 … 1e-1 on some object, or instability in edge cases |
| 1 | > 1e-1 / NaN where equality is expected — wrong economics |

> **HIGH (5):** `lectures/aiyagari.md:72` opens the JAX section with
> ```python
> jax.config.update("jax_enable_x64", True)
> ```
> so its linear solves and value iteration run in double precision — published capital/interest numbers match a NumPy reference to machine epsilon. (`lectures/newton_method.md` does the same.)
>
> **LOW (3, the `ge_arrow` case):** `lectures/ge_arrow.md` has **no** such line. Under float64 the rewrite matches the original to `1.4e-14`, proving the logic is identical — but as shipped it runs in float32, so example 2's printed `α`, `ψ`, `J` move by `1.7e-4`. Correct math, quietly degraded precision. *(Reproduce: run `check_equivalence.py` with and without `JAX_ENABLE_X64=1`.)*

---

### Dimension 2 — Readability & pedagogical clarity · weight 0.25

**Metrics** (from `static_metrics.py`) + reviewer reading:
- `n_prerequisite_concepts` — distinct ideas a reader must already know.
- `docstring_coverage` — fraction of defs with a docstring.
- `code_lines`, `n_defs`, closure-nesting depth.
- **Math-to-code distance** (judgement): does a code line look like the equation it implements?

**Anchors (numeric — keyed to Δ prerequisite-concepts vs the original and to docstring coverage; both from `static_metrics.py`)**

| Score | new prerequisite concepts | docstring coverage | & |
|:---:|:---:|:---:|---|
| 5 | +0 | ≥ 0.80 | code lines read like the math |
| 4 | +1–2 | ≥ 0.75 | still transparent |
| 3 | +3–4 | 0.60–0.75 | readable if you know the framework |
| 2 | +5–6 | < 0.60 | core formula obscured by plumbing |
| 1 | +7 or more | — | learner can't map a cell to its economics |

*(Use the worse of the two columns; the "&" column is the tie-breaker.)*

> **HIGH (5):** `lectures/aiyagari.md:288-300` builds the Bellman right-hand side with broadcasting that visibly mirrors the math $r(a,z,a') + \beta\,E\,v$, and a single branchless feasibility test:
> ```python
> a  = jnp.reshape(a_grid, (a_size, 1, 1))     # a[i]   -> a[i, j, ip]
> z  = jnp.reshape(z_grid, (1, z_size, 1))     # z[j]   -> z[i, j, ip]
> ap = jnp.reshape(a_grid, (1, 1, a_size))     # ap[ip] -> ap[i, j, ip]
> c = w * z + (1 + r) * a - ap
> ...
> return jnp.where(c > 0, u(c) + β * EV, -jnp.inf)
> ```
> A reader sees the budget constraint and the Bellman equation directly.
>
> **LOW (2, the `ge_arrow` case):** `lectures/ge_arrow.md:938-959` expands the one-line kernel $Q_{ij}=\beta\,(y_j/y_i)^{-\gamma}P_{ij}$ into two nested `jax.lax.fori_loop`s with `q.at[j].set(...)` carries:
> ```python
> def body_fun_i(i, Q):
>     def body_fun_j(j, q):
>         ratio = u_prime(c[j]) / u_prime(c[i])
>         return q.at[j].set(β * ratio * P[i, j])
>     q = jax.lax.fori_loop(0, n, body_fun_j, jnp.zeros((n,)))
>     return Q.at[i, :].set(q)
> Q = jax.lax.fori_loop(0, n, body_fun_i, jnp.zeros((n, n)))
> ```
> Prerequisite concepts rise **7 → 13**, docstring coverage falls **0.90 → 0.55**, and the simple "ratio of marginal utilities" idea is buried under functional-update plumbing.
>
> **Also LOW (2), pre-JAX style:** the Bellman operator in `lectures/_static/lecture_specific/odu/odu.py:114-123` loops `for i in range(N)` over flattened grid points doing a `fixed_quad` integral per cell — the value-iteration math is hard to see through the Python scaffolding. (This is the kind of code a *good* JAX rewrite should improve; contrast with the aiyagari HIGH example above.)

---

### Dimension 3 — Computational efficiency (as actually used) · weight 0.15

**Crucial rule:** measure efficiency **in the regime the lecture runs**, not a hypothetical large-scale one. For JAX that means *including* trace+compile time whenever the lecture hits a new shape or `static_argnames` value, because each of those triggers a recompile.

**Metrics** (from `benchmark.py`, `cold_start.py`, `sweep_bench.py`):
- as-used latency (cold, lecture problem size);
- warm/amortized latency;
- scaling curve + the crossover `n` where JAX overtakes NumPy;
- recompile cost per distinct static-arg value.

**The metric that decides the score** is the **as-used speedup**

```
as_used_speedup = (total NumPy wall time) / (total JAX wall time)
```

measured over the lecture's *actual* sequence of solver calls, at its *actual* problem sizes, in a fresh interpreter (so JAX's compiles count). `>1` = JAX faster, `<1` = JAX slower.

**Anchors (numeric)**

| Score | as-used speedup | meaning |
|:---:|:---:|---|
| 5 | **≥ 3×** | materially faster as the lecture runs it |
| 4 | **1.3× – 3×** | clearly faster |
| 3 | **0.8× – 1.3×** | wash; JAX only wins warm / at sizes the lecture never reaches |
| 2 | **< 0.8×** | measurably slower as used; stated goal not met, but correct & fixable |
| 1 | < 0.8× **and** worse (wrong/unstable, or no fix path) | slower with no redemption |

> **HIGH (5) — MEASURED.** `aiyagari.md` is JAX on both branches (no NumPy baseline in-repo), so we benchmarked *its computational pattern* — the vectorised Bellman of `aiyagari.md:288-300` solved by value-function iteration on a `200×7` grid, then re-solved 20× as an equilibrium loop would. This is a **shared calibration of the efficiency threshold, not a per-lecture script** (`../scripts/calibration/bellman_bench.py`, results in `../scripts/calibration/bellman_bench.json`):
>
> | | NumPy | JAX | speedup |
> |---|--:|--:|--:|
> | one solve (397 VFI iters), warm | 1664 ms | 69 ms | **24×** |
> | equilibrium loop, R=20 (as-used, incl. compile) | 29.3 s | 1.16 s | **25×** |
>
> Results agree to `1.1e-14`. Large array + many fixed-shape re-solves → the one-time compile is amortised and JAX wins by ~25×. *(Representative single-CPU medians; ±~15% run-to-run — the decisive fact is the order of magnitude.)* **as-used speedup ≈25 ≥ 3 → score 5.**
>
> **LOW (2) — MEASURED.** Replaying the *entire* `ge_arrow` solver sequence (all examples + the λ-sweep + finite/`T=10000`) once in a fresh process (`scripts/as_used_total.py`):
>
> | NumPy total | JAX total | as-used speedup |
> |--:|--:|--:|
> | **0.035 s** | **1.56 s** | **0.022× (≈45× slower)** |
>
> Every economy is 2×2/3×3 and each call uses fresh static args (`s0_idx`, `T`) → a fresh compile each time (first solve 286 ms, recompile 133 ms, λ-sweep 300 ms cold). JAX *would* win warm at `n ≳ 25` (see `benchmark.py` scaling), but the lecture's economics fix the size tiny. **as-used 0.022 < 0.8 → score 2** (correct and fixable, so not a 1).

---

### Dimension 4 — Logic & design · weight 0.15

**Metrics**: `explicit_loops`, repetition/DRY review, statefulness, latent bugs.

**Anchors**

| Score | Criterion |
|:---:|---|
| 5 | Pure, single-responsibility functions; no repetition; no order-dependence; no global reliance; fixes prior bugs. |
| 4 | Mostly clean; minor redundancy. |
| 3 | Works but has some duplication or awkward coupling. |
| 2 | Order-dependent mutation, duplicated computation, or reliance on globals. |
| 1 | Tangled control flow or logic that is hard to reason about / buggy. |

> **HIGH (5):** `lectures/lake_model.md:216-275` declares parameters as a frozen `LakeModel(NamedTuple)` with defaults, then computes everything with *pure* jitted functions that take the model as an argument:
> ```python
> class LakeModel(NamedTuple):
>     λ: float = 0.283; α: float = 0.013; b: float = 0.0124; d: float = 0.00822
>
> @jax.jit
> def compute_matrices(model: LakeModel):
>     λ, α, b, d = model.λ, model.α, model.b, model.d
>     ...
> ```
> No instance is mutated, no call ordering matters, no globals. (The `ge_arrow` rewrite adopts this same pattern — its strongest aspect.)
>
> **LOW (2, the `ge_arrow` *original*):** `wealth_distribution(s0)` → `continuation_wealths()` → `value_functionss()` must be called **in that order** because each mutates `self`; `risk_free_rate` recomputes `sum(Q)` instead of reusing `PRF`; `pricing_kernel` references the **module-level** `P`; and the public method is misspelled `value_functionss`. The rewrite fixing these is exactly why it scores well here.

---

### Dimension 5 — Coding style & idiom · weight 0.10

**Metrics**: PEP 8 / project-style conformance, and — for JAX — whether the code uses *idiomatic* JAX (vectorisation, `vmap`, `where`) rather than mechanically porting Python loops.

**Anchors**

| Score | Criterion |
|:---:|---|
| 5 | Idiomatic in both languages; vectorised where natural; consistent naming. |
| 4 | Idiomatic with minor nits. |
| 3 | Correct but mixes idioms or ports loops literally where vectorisation fits. |
| 2 | Anti-idiomatic constructs that a JAX reviewer would flag. |
| 1 | Fights the framework throughout. |

> **HIGH (5):** `lectures/aiyagari.md:300` uses branchless `jnp.where(c > 0, u(c) + β * EV, -jnp.inf)` to impose feasibility, and `lectures/lake_model.md: 261` iterates a time series with `jax.lax.scan` (the idiomatic carry/collect primitive) instead of hand-rolled index updates.
>
> **LOW (2, the `ge_arrow` case):** nested `fori_loop` scalar scatter for the pricing kernel (vectorisation was a one-liner), and `jax.lax.cond(T==0, …)` that **traces both branches every call** where `T` is already static and a plain Python `if` would do. Only 1 of 4 idiom criteria is met (clean call sites), so the checklist gives 1+1 = 2.

---

### Dimension 6 — API ergonomics & reusability · weight 0.10

**Metrics**: `statements_for_one_result` (calls needed to obtain α, ψ, J); composability (jit/vmap-friendly?); immutability.

**Anchors (numeric — keyed to `statements_for_one_result`, i.e. the calls a user must write to obtain α, ψ, J for one economy)**

| Score | statements | & |
|:---:|:---:|---|
| 5 | 1 | immutable result, trivially `jit`/`vmap`-composable |
| 4 | ≤ 2 | one object + minor setup |
| 3 | 3 | order-independent |
| 2 | ≥ 3 | **ordered, side-effecting** calls (wrong order → silent garbage) |
| 1 | — | fragile protocol, easy to misuse silently |

> **HIGH (5):** `lectures/lake_model.md` — `model = LakeModel()` then `compute_matrices(model)` / `simulate_path(...)`; the model is an immutable argument passed to stateless functions, trivially `vmap`-able over parameters. The `ge_arrow` rewrite matches this: `m = compute_rc_model(s, P, ys, s0_idx=1, T=10)` returns one immutable bundle (`m.Q, m.α, m.ψ, m.J, …`), `statements_for_one_result = 1`.
>
> **LOW (2):** `odu.py`'s `SearchProblem` and the `ge_arrow` *original* both require *build object → call mutating methods in the correct order*. For `ge_arrow` that is `wealth_distribution → continuation_wealths → value_functionss`; `statements_for_one_result = 4`, and calling them out of order silently gives wrong/garbage results.

---

### Dimension 7 — Maintainability & robustness · weight 0.05

**Metrics**: testability (pure vs stateful), debuggability (can you step through it?), and "footguns" left for future editors.

**Anchors**

| Score | Criterion |
|:---:|---|
| 5 | Pure & easily unit-tested; no silent traps; easy to extend. |
| 4 | Testable; small caveats. |
| 3 | Testable but harder to debug, or leaves a minor trap. |
| 2 | Hard to debug or carries a silent correctness trap (e.g. dtype). |
| 1 | Brittle; changes likely to break silently. |

> **HIGH (5):** `lectures/aiyagari.md` pairs pure jitted functions with the explicit `jax.config.update("jax_enable_x64", True)` at `:72`, so a future editor reusing the functions gets full precision by default and can unit-test each `@jax.jit` function in isolation.
>
> **LOW (3, the `ge_arrow` case):** purity *helps* testing, but `jit` + `static_argnames` + 3-deep closures make stepping hard, and the float32 default is a silent trap for the next person who reuses the function.

---

## 3. How to run the system

```bash
conda activate quantecon                      # jax 0.4.x, numpy 2.x, quantecon
python references/examples/<lecture>/scripts/run_all.py   # measure → <lecture>/results/*.json,
                                              # then apply the shared rubric
python scripts/scoring/score.py references/examples/<lecture>   # (re)compute the scorecard alone
```

`run_all.py` runs the measurement scripts (e.g. `check_equivalence.py`, `static_metrics.py`, `benchmark.py`, `as_used_total.py`, and lecture-specific ones) and finishes by invoking `scripts/scoring/score.py`, which reads `<lecture>/evidence.json` and writes `<lecture>/results/scorecard.json`.

**To evaluate a *different* lecture** see the "Evaluate a new lecture" recipe in [`README.md`](../scripts/README.md): scaffold `<lecture>/`, drop in `model_old.py` / `model_new.py`, adapt the measurement scripts, fill `evidence.json`, and run the two commands above. The framework, weights, thresholds, and checklists are lecture-independent; only the inputs change.

## 4. Limitations / honesty notes

- Benchmarks are **CPU-only** (`jax.devices() == [CpuDevice]`). On GPU/TPU the crossover `n` shifts left and JAX's warm advantage grows — but the lecture's models are still tiny, so the as-used verdict is unlikely to change.
- Dimension scores 2/5/6 are partly judgement; the rubric anchors and the cited metrics make them auditable, not arbitrary.
- `concept_token_hits` from `static_metrics.py` is a raw frequency and is *informational only*; `n_prerequisite_concepts` is the readability metric that feeds scoring.
