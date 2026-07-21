---
name: check-math
description: Check a QuantEcon lecture's mathematical notation against the style guide — \\top transpose, aligned (never align) inside $$, no \\tag, \\mathbb P/E/V, plain-letter distribution names, sequence and matrix conventions. Reports violations by rule ID with an offer to fix.
---

# check-math

> **Status: scaffolding.** Rule content lands in follow-up PRs; see [CATALOG.md](https://github.com/QuantEcon/skills/blob/main/CATALOG.md). Until then this skill reports that it is not yet operational.

Category entry point for the `math` rules — mathematical notation conventions.

This is a thin pointer: it runs the same procedure as [/qe:check-style](../check-style/SKILL.md) restricted to the `math` category, using the shared rules in `references/rules/math.md` and the shared preflight scripts in `scripts/`. See the umbrella skill for the full procedure (preflight → category pass → report → fix on request).
