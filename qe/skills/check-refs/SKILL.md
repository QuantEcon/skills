---
name: check-refs
description: Check a QuantEcon lecture's citations and cross-document links against the style guide — {cite} vs {cite:t} usage, {doc} links with the standard intersphinx prefixes, auto-title link text, bib entries in _static/quant-econ.bib. Reports violations by rule ID with an offer to fix.
---

# check-refs

> **Status: scaffolding.** Rule content lands in follow-up PRs; see [CATALOG.md](../../../CATALOG.md). Until then this skill reports that it is not yet operational.

Category entry point for the `refs` rules — citations and cross-document links.

This is a thin pointer: it runs the same procedure as [/qe:check-style](../check-style/SKILL.md) restricted to the `refs` category, using the shared rules in `references/rules/refs.md` and the shared preflight scripts in `scripts/`. See the umbrella skill for the full procedure (preflight → category pass → report → fix on request).
