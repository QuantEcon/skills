# Skill catalog — active plan

Current focus, validated against ~630 merged PRs across the four main lecture repos (2026-07-21). Parked ideas live in [FUTURE-IDEAS.md](FUTURE-IDEAS.md).

## Principles

- **Few, high-frequency skills** over many niche ones; every skill is validated against actual PR history.
- **Focal point is PR management**: consistent review results, plus the same checks run by authors on a working copy before opening a PR.
- **Report first, fix on request.** Skills produce a structured report and offer fixes; they never silently edit. Safe in CI, authors stay in control.
- **Cited claims; computed scores.** Every finding carries a citation (rule ID + `file:line`, or a number + its source). Skills whose output is a findings list need nothing more. Skills that aggregate judgements into a scored verdict use the evidence-file pattern from the benchmark plugin: judgement recorded as cited answers, every score computed by a deterministic engine, never typed by hand (see [docs/developing-skills.md](docs/developing-skills.md)).

## 1. Style skill family — flagship

Check a lecture (working copy or PR diff) against the QuantEcon style guide; report violations by rule ID; offer fixes.

**Evidence:** the largest recurring PR theme — ~25+ human style PRs across all repos plus the `action-style-guide` campaign in lecture-python-advanced; the ~30 RA "editorial suggestions" PRs in lecture-python-intro overlap almost 1:1 with the rule set, so this skill absorbs that workflow too. Weakest audit categories (Figures 7.4/10 corpus-wide; Math 5.6 in adv) show where it pays first.

**Naming and structure (decided 2026-07-21):** the author-facing surface lives in a **`qe` plugin** — one memorable prefix for the author network — while `benchmark` remains its own specialist plugin. An umbrella **`/qe:check-style`** runs the full check (optional trailing category words, e.g. `/qe:check-style aiyagari figures math`), and **thin per-category sub-skills** (`/qe:check-writing`, `/qe:check-math`, `/qe:check-code`, `/qe:check-figures`, `/qe:check-jax`, `/qe:check-refs`) give autocomplete discoverability and precise natural-language auto-triggering. Sub-skills are ~10-line pointers; all rule content lives once at plugin level (`qe/references/rules/`, `qe/scripts/`), so there is no duplicated rule text to keep in sync. Future author-facing base skills (see [FUTURE-IDEAS.md](FUTURE-IDEAS.md)) join the `qe` plugin.

**Rules architecture (two layers):**

1. **Canonical source:** `QuantEcon/style-guide` — the machine-readable rules DB. Its Phase 0 (schema, `build/validate.py` + CI, fixtures convention, governance) landed 2026-06-11; Phase 1 (transcribing the ~55 catalogued rules) restarts with this skill work supplying the priority order and the labour. Rule text is authored **only** there (the programme's no-drift exit criterion); the manual's `styleguide/` pages and this plugin both become rendered consumers. Proposal: [project-style-guide#6](https://github.com/QuantEcon/project-style-guide/issues/6).
2. **Rendered snapshot (in this plugin):** `qe/references/rules/` holds a rendered, drift-checked copy (`render-skill` target upstream + `scripts/sync-rules.py` + CI check here) in the style-guide schema (`qe-*` IDs, `mode: mechanical|hybrid|llm`, `severity`, `build_risk`, `auto_fix`, `exclusions`). Open decision (issue #6): `style-guide` is private (D8) while this marketplace is public — vendor full rules (revisit D8), fetch at runtime via `gh`, or render summaries only.

**Check machinery (inside the skill, regardless of naming):**

- **Deterministic preflight scripts first** — the three `build_risk` rules (`align` in `$$`, tick-count nesting, floats inside exercise/solution/`prf:`) plus the ~24 mechanical rules (legacy `np.random.*`, `time.time()`, `\mathcal N`, `pip install jax`, `PRNGKey`, transpose notation with derivative carve-outs, …). Must be MyST-context-aware (narrative vs math env vs code cell) — plain grep produces false positives; the style-guide repo's `tests/fixtures/` layout is the ready-made zero-FP test harness.
- **LLM passes per category** for hybrid/judgement rules (heading case with proper-noun allow-list, one-sentence-paragraph splitting, caption quality, JAX anti-patterns, …).
- **Never auto-fix `build_risk`/RNG rules** — changing an RNG stream changes published figures; report + guided fix only.
- The "should this lecture use JAX at all" gate stays thin here — that judgement belongs to `review-acceleration` (the boundary QuantEcon.manual#104 draws).

This delivers the planned `qestyle-linter` + `qestyle` pair as Claude Code skills — consistent with programme decision D2 ("CLI engine, Claude Code as the interface") and the planned split-and-retire of `action-style-guide`.

## 2. `/benchmark:review-acceleration` — finish

Blocked on the eight evaluation scripts (@xuanguang-li agreed 2026-07-07 to package and send). **Unblocked now:** the full rubric (7 weighted dimensions, verdict bands, HIGH/LOW calibration cases) is specified in the lecture-python.myst#717 thread and can move into `references/rubric.md` ahead of the scripts. Validation cases: lecture-python.myst#717 and #654.

## 3. `audit` — the bulk-audit family

Portfolio-wide, read-only sweeps of one repository, each delivering a report bundle. Four skills: **`/audit:issues`** (every issue, open and closed — landed), then **`/audit:prs`** (every open PR: does it solve a real issue, is it mergeable, what should the review say), **`/audit:tech-debt`** (a codebase's debt plus a filing-ready issue catalog), **`/audit:translations`** (parity between a source series and its translation).

**Evidence:** unlike the style family, the case here is not per-repo frequency — a tracker audit is a once-or-twice-a-year event for any one repo. It is *breadth*: the org has ~245 non-archived repos, and three of the four procedures have already been executed by hand — the issue triage this plugin ships, the `quantecon-py` technical-debt report, and the zh-cn translation work. Each hand run cost hours of re-derivation because the method lived in a pasted prompt.

**Structure (proposed 2026-07-26):** four sibling skills, no umbrella — unlike `qe`'s categories, these are distinct procedures over distinct inputs, so the `qe` pattern to reuse is plugin-level sharing, not the umbrella. The method is authored once in `audit/references/` (`doctrine.md`, `quantecon-context.md`, `deliverables.md`) and each `SKILL.md` carries only its own subject matter. Membership test: bulk **and** read-only **and** report-bundle output — which keeps single-item review (`/benchmark:review-acceleration`) outside the family and stops the plugin becoming a general runbook dump.

**Why read-only is structural, not cautious:** the boundary mirrors the org's own automation split, where the family line *is* the permission line. It makes the family safe to point at any repo and safe to run headlessly, and it keeps a report honest — an audit that half-applied its findings would describe a repo that no longer exists. Acting on a bundle (filing the catalog, posting drafted comments, `qe gh labels sync`) is a separate human-invoked step.

**Long-run machinery:** every skill runs the same five phases (snapshot → verify → relate → write → self-audit), each checkpointed to disk so a lost session resumes rather than restarts, and all reading one frozen snapshot so the report describes a single point in time. Phase 1 is deterministic (`audit/scripts/fetch_tracker.py`), which also makes the coverage self-audit mechanical rather than narrated.
