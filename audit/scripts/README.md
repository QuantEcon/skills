# Deterministic audit machinery

Phase 1 of every audit is mechanical, so it belongs here rather than in model judgement ([doctrine §4](../references/doctrine.md#4-phases-and-surviving-a-long-run)). Stdlib only, driving `gh`; no install step.

## `fetch_tracker.py`

Snapshots a repository's whole tracker — issues and PRs, any state, with full comment threads — and reconciles the capture against the number sequence it should fill.

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/fetch_tracker.py OWNER/REPO --out <dir>/snapshot
```

| Output | Contents |
|---|---|
| `meta.json` | Repo, snapshot time (UTC), `gh` version, auth state, the fields requested |
| `issues.json` | Every issue, any state, each with its comment thread |
| `prs.json` | Every PR, with comments, reviews, and `closingIssuesReferences` |
| `coverage.json` | Items against `1..max`, thread counts by open/closed, truncation flag |

Three properties the audit depends on:

- **Thread-complete on the closed side.** Comment threads come down inside the list call, so reading closed threads — doctrine rule 3, and the gap the first execution of this runbook found — costs nothing extra.
- **Frozen in time.** Every later phase reads this snapshot, so the report describes one instant and "events after the snapshot" is a stated property rather than a silent gap.
- **Honest about its own limits.** `unaccounted_numbers` lists gaps in the number sequence for the audit to explain, and `truncation_risk` flags a stream that returned exactly at `--limit`, which is indistinguishable from truncation. Neither is swallowed.

Preflight refuses to start without `gh` and authentication, because the anonymous API is 60 requests/hour per IP and returns nothing at all for the org's private repos.

Not captured, because REST does not return them: native sub-issue links and Projects membership. Fetch those with `gh api graphql` when a tracker issue depends on them, and disclose them in the coverage statement regardless.
