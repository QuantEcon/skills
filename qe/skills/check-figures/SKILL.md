---
name: check-figures
description: Check a QuantEcon lecture's figures against the style guide — mystnb captions (lowercase, short, named for numref), no ax.set_title, lowercase axis labels, lw=2, width, no unjustified figsize, plotly latex link-back. Reports violations by rule ID with an offer to fix.
---

# check-figures

> **Status: scaffolding.** Rule content lands in follow-up PRs; see [CATALOG.md](https://github.com/QuantEcon/skills/blob/main/CATALOG.md). Until then this skill reports that it is not yet operational.

Category entry point for the `figures` rules — figure and plotting conventions.

This is a thin pointer: it runs the same procedure as [/qe:check-style](../check-style/SKILL.md) restricted to the `figures` category, using the shared rules in `references/rules/figures.md` and the shared preflight scripts in `scripts/`. See the umbrella skill for the full procedure (preflight → category pass → report → fix on request).
