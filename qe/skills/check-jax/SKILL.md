---
name: check-jax
description: Check a QuantEcon lecture's JAX usage against the style guide — GPU admonition include, jax.random.key discipline, lax control-flow patterns with bounded while_loop, NamedTuple model structure, anti-patterns like .at[].set() in Python loops. Reports violations by rule ID with an offer to fix.
---

# check-jax

> **Status: scaffolding.** Rule content lands in follow-up PRs; see [CATALOG.md](https://github.com/QuantEcon/skills/blob/main/CATALOG.md). Until then this skill reports that it is not yet operational.

Category entry point for the `jax` rules — JAX conventions and anti-patterns.

This is a thin pointer: it runs the same procedure as [/qe:check-style](../check-style/SKILL.md) restricted to the `jax` category, using the shared rules in `references/rules/jax.md` and the shared preflight scripts in `scripts/`. See the umbrella skill for the full procedure (preflight → category pass → report → fix on request).
