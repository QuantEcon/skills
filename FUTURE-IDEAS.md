# Future skill ideas

Documented so they aren't lost; deliberately **not** in the active plan. Current focus: the style skill family (see [CATALOG.md](CATALOG.md)). Each idea below is evidence-backed by the 2026-07 PR-history analysis (~630 merged PRs across lecture-python.myst, lecture-python-intro, lecture-python-advanced.myst, lecture-dp).

## Parked candidates

### mirror-lecture (cross-repo SYNC)

Mirror an upstream lecture change into a downstream repo. 13 of lecture-dp's 28 lifetime PRs are `SYNC:` PRs; the same infra fix (Pages deploy migration, linkcheck fix, fetch-depth) has landed 2–4× across repos by hand. The playbook is stable and documented in existing PR bodies: pin upstream commit hash, localize `{doc}` cross-references, defer TOC wiring, neutral commit-reference wording (no closing keywords before `owner/repo#N`).

### triage-build (environment-upgrade breakage)

Classify a failed lecture build against known failure patterns (deprecation sweeps, pandas 3.0 read-only arrays, unpinned-package breakage à la `prettytable`, SymPy overflow) and propose the known fix. Recurs ~15×/year across repos. Overlaps meta#304's `jupyter-book-fixer` idea.

### migrate-rng (np.random → Generator campaign)

meta#299: ~13 identical PRs so far, many lectures remaining. Mechanical with a defined judgement checkpoint (figure changes from RNG-stream changes). Time-limited — only worth a skill if the campaign runs long. The unsettled convention (`rng` explicit arg vs `rng=None` fallback — lp #874 vs intro #741) should be settled in the manual regardless.

### intake-lecture (LaTeX → MyST intake)

"Tom's lectures" intake formatting: ~20 PRs in lp + adv converting delivered material to house MyST style. Maps to meta#304's `latex-to-myst`. Real but bursty.

### migrate-data (data-lectures repointing)

meta#338 / data-lectures#15 playbook: data PR first, byte-compare sha256 gate, repoint URLs, delete local copies (lp #973, intro #792). Pure skill material, low current volume.

### Editorial-round implementation

Parse a review issue's checklist into a diff against one lecture — lecture-python-intro's dominant RA workflow (~30 PRs). Largely absorbed by the style skill's fix mode; revisit only if a gap remains after it ships.

## How skills could serve the benchmarking programme (note for meta#335)

Benchmark *data capture* stays in the programme repos (`QuantEcon/benchmarks` — workstream A; `QuantEcon/tool-lecture-benchmark` — workstream C). Skills are natural *consumers and interfaces* of that data:

1. **`.jupyter_cache` telemetry reader** — nbclient already records per-cell timings in every CI build; nothing surfaces them. A skill + ~50-line script reading `_build/.jupyter_cache` (or a CI artifact) and diffing a PR preview against main ("cell `solve-ex4` went 8 ms → 950 ms") is the cheapest high-value entry point and seeds workstream C. It would have flagged the lecture-python.myst#717 regression the day the PR opened.
2. **Crossover advisory** — once workstream A produces crossover curves, a skill answering "this lecture solves n=2 economies 100 times — which backend?" from measured data rather than rules of thumb, during authoring or review.
3. **Provenance/schema guardian** — generate and validate the shared result + environment-descriptor stamp (meta#335's first blocking deliverable) across all three workstreams' outputs.
4. **`/benchmark:review-acceleration`** is workstream B's deliverable and already lives here.

## Rejected

- Per-measurement skills (`cold-start`, `sweep-bench`, `scaling-curve`) — measurements, not workflows; they are scripts inside the benchmark plugin.
- Typo/grammar skills — trivial, no skill needed.
- `track-runtime` as a skill — workstream C's job; see the telemetry note above.
