# qe plugin — rules

**Pending.** One file per category (`writing.md`, `math.md`, `code.md`, `figures.md`, `jax.md`, `refs.md`), each holding that category's rules in the `QuantEcon/style-guide` schema:

```yaml
id: qe-writing-004        # stable rule ID, reported to users
category: writing
mode: mechanical | hybrid | llm
severity: error | warning | style
build_risk: true | false   # breaks HTML/PDF builds
auto_fix: true | false     # false ⇒ present fix, never apply
detection: ...             # regex + context for mechanical/hybrid rules
exclusions: ...            # known carve-outs (e.g. f'(x) derivatives)
```

Seeding plan (see the work plan in `QuantEcon/project-style-guide`): reconcile `action-style-guide`'s 49 rule prompts against the current QuantEcon Manual `manual/styleguide/` pages, author each rule in this schema, and submit each reconciled rule upstream to `QuantEcon/style-guide` for ratification. Once that DB leads, `scripts/sync-rules.py` (pending) plus a CI drift check keep this vendored copy aligned.

The three `build_risk` rules land first: `align` inside `$$` (must be `aligned`), tick-count nesting in admonitions, floats inside exercise/solution/`prf:` directives.
