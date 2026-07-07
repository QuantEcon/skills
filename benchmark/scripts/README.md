# benchmark plugin — scripts

Supporting scripts for `/benchmark:eval-py-acceleration`.

**Pending:** these are being collected from the evaluation work on [QuantEcon/lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717), where they were developed and validated against `ge_arrow.md` (and the `aiyagari.md` Bellman pattern as the HIGH calibration case):

- `check_equivalence.py` — diff all published objects between implementations, under default dtype and `jax_enable_x64`
- `static_metrics.py` — prerequisite-concept count, docstring coverage, code size metrics
- `benchmark.py` — scaling curves and crossover-n between implementations
- `cold_start.py` — cold-start / compile-time measurement
- `sweep_bench.py` — parameter-sweep timing (cold and warm)
- `as_used_total.py` — the headline metric: full lecture solver sequence replayed in a fresh process
- `bellman_bench.py` — the aiyagari-pattern calibration benchmark
- `run_all.py` — orchestrator

As they land they will be generalised from `ge_arrow`-specific code to take a lecture/implementation pair as input.
