---
name: check-writing
description: Check a QuantEcon lecture's prose against the style guide's writing rules — one-sentence paragraphs, sentence-case headings, bold-for-definitions/italic-for-emphasis, minimal capitalization, uppercase statistical acronyms. Reports violations by rule ID with an offer to fix.
---

# check-writing

> **Status: scaffolding.** Rule content lands in follow-up PRs; see [CATALOG.md](../../../CATALOG.md). Until then this skill reports that it is not yet operational.

Category entry point for the `writing` rules — prose style and structure.

This is a thin pointer: it runs the same procedure as [/qe:check-style](../check-style/SKILL.md) restricted to the `writing` category, using the shared rules in `references/rules/writing.md` and the shared preflight scripts in `scripts/`. See the umbrella skill for the full procedure (preflight → category pass → report → fix on request).
