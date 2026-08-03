# Deterministic audit machinery

Fetching is mechanical, so it belongs here rather than in model judgement ([doctrine §4](../references/doctrine.md#4-checkpointing)). Stdlib only, driving `gh`; no install step.

## `fetch_tracker.py`

Snapshots a repository's whole tracker — issues and PRs, any state, with full comment threads — and reconciles the capture against the number sequence it should fill.

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/fetch_tracker.py OWNER/REPO --out <dir>/snapshot
```

| Output | Contents |
|---|---|
| `meta.json` | Repo, snapshot time (UTC), `gh` version, the fetching account, the fields requested |
| `issues.json` | Every issue, any state, each with its comment thread |
| `prs.json` | Every PR, with comments, reviews, and `closingIssuesReferences` |
| `coverage.json` | Items against `1..max`, discussion counts by open/closed — comments for issues, comments and reviews for PRs — truncation flag |

Three properties the audit depends on:

- **Thread-complete on the closed side.** Comment threads come down inside the list call, so reading closed threads — doctrine rule 3, and the gap the first execution of this runbook found — costs nothing extra.
- **Frozen in time.** Every later phase reads this snapshot, so the report describes one instant and "events after the snapshot" is a stated property rather than a silent gap. Items are written in number order rather than `gh`'s undocumented default sort, so two snapshots of the same repo differ only where the tracker did.
- **Honest about its own limits.** `unaccounted_numbers` lists gaps in the number sequence for the audit to explain, and `truncation_risk` flags a stream that returned exactly at `--limit`, which is indistinguishable from truncation. Neither is swallowed. The thread fields are shape-asserted at capture, so a `gh` build returning comment *counts* rather than objects fails immediately and by name, instead of crashing three phases later or quietly under-reporting the threads the doctrine claims were read.

Preflight refuses to start without `gh` and authentication, because the anonymous API is 60 requests/hour per IP and returns nothing at all for the org's private repos.

Not captured, because REST does not return them: native sub-issue links and Projects membership. Fetch those with `gh api graphql` when a tracker issue depends on them, and disclose them in the coverage statement regardless.

One more gap worth naming, because it is easy to mistake for coverage: `reviews` holds review bodies and verdicts, not the inline comments left on individual lines. A PR can be counted as reviewed while its line-level discussion goes unread. Fetch those per PR with `gh api repos/OWNER/REPO/pulls/N/comments` where a finding turns on them — and list them as residue when it does not.
