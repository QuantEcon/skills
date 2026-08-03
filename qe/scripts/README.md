# qe plugin — scripts

## `fetch-copilot.sh`

Dumps GitHub Copilot's review of a pull request — the overview, then every inline comment with the ID to reply to — for [`/qe:copilot-review`](../skills/copilot-review/SKILL.md). Read-only: it never posts. Requires an authenticated `gh`; run `bash fetch-copilot.sh --help` for the argument forms.

Two details are load-bearing rather than incidental. It **paginates both passes** over `pulls/<PR>/comments`, because `gh` applies `--jq` per page and refuses `--slurp` alongside it — and a reply always sorts after the comment it answers, so a single unpaginated page loses the reply markers and a re-run would double-post. And it **prefixes every line quoted from GitHub with `| `**, so no comment body can forge the `== ID` record header that the reply step keys on.

## Style preflight

**Pending.** Deterministic, MyST-context-aware preflight checkers driven by `/qe:check-style` and the category sub-skills:

- `preflight.py` — run all mechanical rules from `references/rules/` against a lecture; zero-false-positive bar, validated against the `QuantEcon/style-guide` fixtures layout (`tests/fixtures/<rule-id>/{correct,incorrect}/`). Context-splits MyST source (narrative vs math environment vs code cell vs directive) before matching — plain grep over lecture source produces false positives (e.g. `f'(x)` derivatives vs transpose `'`).
- `sync-rules.py` — sync the vendored `references/rules/` snapshot from `QuantEcon/style-guide` once that DB is the leading source; paired with a CI drift check in this repo.

The `build_risk` checks (rules that break HTML/PDF builds) are the first implementation target.
