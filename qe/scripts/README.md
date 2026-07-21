# qe plugin — scripts

**Pending.** Deterministic, MyST-context-aware preflight checkers driven by `/qe:check-style` and the category sub-skills:

- `preflight.py` — run all mechanical rules from `references/rules/` against a lecture; zero-false-positive bar, validated against the `QuantEcon/style-guide` fixtures layout (`tests/fixtures/<rule-id>/{correct,incorrect}/`). Context-splits MyST source (narrative vs math environment vs code cell vs directive) before matching — plain grep over lecture source produces false positives (e.g. `f'(x)` derivatives vs transpose `'`).
- `sync-rules.py` — sync the vendored `references/rules/` snapshot from `QuantEcon/style-guide` once that DB is the leading source; paired with a CI drift check in this repo.

The `build_risk` checks (rules that break HTML/PDF builds) are the first implementation target.
