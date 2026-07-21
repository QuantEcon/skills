---
name: check-style
description: Check a QuantEcon lecture against the QuantEcon style guide and report violations by rule ID, with an offer to fix. Covers all categories (writing, math, code, figures, jax, refs) or a requested subset. Use when reviewing a lecture PR for style compliance or preparing a lecture for a PR. Never edits without confirmation.
---

# check-style

> **Status: scaffolding.** The rule content (`references/rules/`) and deterministic preflight scripts (`scripts/`) land in follow-up PRs, tracked in [CATALOG.md](../../../CATALOG.md) and the work plan in `QuantEcon/project-style-guide`. Until they land this skill reports that it is not yet operational.

Umbrella style check for one lecture. Runs every category, or only the categories named in the arguments.

## Invocation

```
/qe:check-style <lecture> [categories...]
```

- `<lecture>` — a lecture source file (e.g. `lectures/aiyagari.md`) or, on a PR branch, omitted to mean "the lectures changed on this branch".
- `[categories...]` — optional subset from: `writing`, `math`, `code`, `figures`, `jax`, `refs`. Default: all.

Per-category entry points also exist as sub-skills (`/qe:check-writing`, `/qe:check-math`, `/qe:check-code`, `/qe:check-figures`, `/qe:check-jax`, `/qe:check-refs`) — they run the same rules from the same shared references.

## Procedure (once rules land)

1. **Preflight** — run the deterministic checkers in `scripts/` over the lecture. These cover the `build_risk` rules first (they break HTML/PDF builds) and the mechanical rules. Zero false positives is the bar; the checkers are MyST-context-aware (narrative vs math environment vs code cell vs directive).
2. **Category passes** — for each requested category, evaluate the hybrid/judgement rules in `references/rules/<category>.md` against the lecture.
3. **Report** — one table per category: rule ID, severity, location (`file:line`), finding, proposed fix. Summarize counts by severity.
4. **Fix on request only** — after the report, offer to apply fixes. Never auto-apply rules marked `auto_fix: false` or `build_risk: true` (e.g. RNG-stream changes alter published figures) — for those, present the fix and let the author apply it.

## Rule source

Rules live in `references/rules/*.md`, one file per category, in the `QuantEcon/style-guide` schema (frontmatter: `id`, `mode`, `severity`, `build_risk`, `auto_fix`, `detection`, `exclusions`). Rule text is authored only in `QuantEcon/style-guide`; this directory is a rendered, drift-checked snapshot of it (see `references/rules/README.md` and [project-style-guide#6](https://github.com/QuantEcon/project-style-guide/issues/6)).
