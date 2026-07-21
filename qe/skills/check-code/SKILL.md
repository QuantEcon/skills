---
name: check-code
description: Check a QuantEcon lecture's code cells against the style guide — NumPy Generator API (no legacy np.random.*), unicode Greek variable names, package-install cell placement, qe.Timer over time.time, parallel-RNG thread safety. Reports violations by rule ID; RNG-stream fixes are never auto-applied.
---

# check-code

> **Status: scaffolding.** Rule content lands in follow-up PRs; see [CATALOG.md](https://github.com/QuantEcon/skills/blob/main/CATALOG.md). Until then this skill reports that it is not yet operational.

Category entry point for the `code` rules — code style and library idiom.

This is a thin pointer: it runs the same procedure as [/qe:check-style](../check-style/SKILL.md) restricted to the `code` category, using the shared rules in `references/rules/code.md` and the shared preflight scripts in `scripts/`. See the umbrella skill for the full procedure (preflight → category pass → report → fix on request).
