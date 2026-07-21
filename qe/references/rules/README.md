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

Rule text is authored **only** in `QuantEcon/style-guide` (the programme's Phase 5 exit criterion — no drift). This directory is a **rendered consumer**: a `render-skill` target in `style-guide` (sibling of the planned `render-manual`/`render-action`) renders ratified rules here, and `scripts/sync-rules.py` (pending) plus a CI drift check keep the snapshot aligned. Transcription of the ~55 catalogued rules into `style-guide` is Phase 1 of the programme — proposal and sequencing in [project-style-guide#6](https://github.com/QuantEcon/project-style-guide/issues/6).

The three `build_risk` rules land first: `align` inside `$$` (must be `aligned`), tick-count nesting in admonitions, floats inside exercise/solution/`prf:` directives.
