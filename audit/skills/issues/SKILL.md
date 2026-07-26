---
name: issues
description: Audit every issue in a GitHub repository, open and closed — verify each status against the code rather than the thread, hunt fixed-but-open and never-landed-fix candidates, tier the open set into the repo's existing plan, and deliver a report bundle with a cross-link map. Read-only: it recommends tracker changes but never makes them. Use for a whole-tracker review, not a single issue.
---

# audit:issues

Whole-tracker review of one repository. Long-running by design — a hundred-issue repo is a multi-hour run — so it works from a frozen snapshot and checkpoints every phase to disk.

> **Status: first runbook of the `audit` family.** The procedure below is the QuantEcon-adapted form of a runbook that has been executed once end to end; the gap that execution found (closed threads unread) is now doctrine rule 3 and is closed by the snapshot. Plan and family design: [CATALOG.md §3](https://github.com/QuantEcon/skills/blob/main/CATALOG.md).

## Invocation

```
/audit:issues [OWNER/REPO] [--out DIR]
```

Both arguments are optional. With no repo, audit the current checkout's `origin`. Everything else is discovered:

| Input | Discovery | On failure |
|---|---|---|
| Project-notes system | The search order in [quantecon-context.md](../../references/quantecon-context.md#finding-the-plan-to-slot-into) | Say none was found; tier against milestones |
| Label policy | [QEP-2](https://github.com/QuantEcon/qeps/pull/2), status read at run time | Treat as draft — recommend canonical labels only |
| Work-plan anchor | The live plan or tracking issue in the tracker | Tier against the notes system alone |
| Prior audits | Earlier audit bundles in the notes system; closed "priority order" issues | Note that this is the first audit |

Ask only when discovery is ambiguous — two plausible plan anchors, say — not when it simply comes up empty. Report every resolved input in the report's method section.

## Read this first

- [doctrine.md](../../references/doctrine.md) — trust rules, evidence classes, the read-only boundary, phases, coverage self-audit
- [quantecon-context.md](../../references/quantecon-context.md) — repo types, label ownership, the cross-repo graph, the closing-keyword hazard
- [deliverables.md](../../references/deliverables.md) — the bundle contract

Then, in the audited repo: the notes system, `CHANGELOG.md`, the latest release notes, and `AGENTS.md`/`CLAUDE.md`.

## Phase 1 — snapshot

```bash
python ${CLAUDE_PLUGIN_ROOT}/scripts/fetch_tracker.py OWNER/REPO --out <dir>/snapshot
```

Preflight fails in the first minute on missing `gh`, missing auth, or an invisible repo — read the error rather than working around it. The snapshot captures issues and PRs in any state with full comment threads, so closed threads cost nothing extra to read and there is no excuse for skipping them.

Two things REST does not return, so the snapshot cannot hold them: **native sub-issue links** and **Projects membership**. Fetch those with `gh api graphql` where a parent/tracker issue depends on them, and list them in the coverage statement either way.

Read `coverage.json` before proceeding. A stream at the fetch limit, or unaccounted numbers, is a phase 1 problem — fix it here, not in the writeup.

## Phase 2 — verify

Per [doctrine §1](../../references/doctrine.md#1-what-makes-a-bulk-audit-trustworthy), the thread is a hypothesis and the default branch is the evidence.

**Each open issue.** Does the complaint still reproduce on the default branch — check the named file or function, not the claim about it? Did a merged PR or a campaign claim it, and does the diff actually contain the change (this is where wave escapes hide)? Is it a duplicate of another open issue — same fix, no mutual link? Is it superseded, where a newer issue is the better carrier — then port the lessons across and close the old one as superseded, never silently. Is it blocked on an external decision — annotate the hold and split live from gated scope, so the issue does not read as wholly frozen when part of it is actionable. For parents and trackers: are the children attached natively, and is it still the plan of record?

**Each closed issue.** Is `stateReason` sensible? Does it map to a shipped PR or a recorded decision? Were the thread's remainders re-homed somewhere still open, or did they die with the thread?

**Hunt these categories actively** — they are what the audit exists to find: fixed-but-open · scheduled-but-escaped · unlinked duplicates · delivered-elsewhere (close when the dependency lands) · validated-purpose-served · agreed-but-never-filed, where a thread proposal got a nod and no issue · stale notes-system lines, which are reported as nits rather than tracker actions.

Sibling-repo checks belong here too: for QuantEcon, "resolved in a sibling" and "one step of a rollout" are the two most common wrong conclusions a single-repo audit reaches.

## Phase 3 — relate

Parse every `#N` in all issue **and** PR bodies, both directions. One parsing caveat: a range reference (`#169–#176`) matches its endpoints only, so check milestone membership before declaring the middle numbers orphaned.

Produce the cluster map, the table of missing links worth adding (duplicate pairs, origin↔carrier, complementary checks, family orphans), true orphans and over-dense hubs, and the external cross-link registry.

## Phase 4 — tier and write

Slot into the repo's existing plan; never invent a parallel one. Tier by repo type — a build break in a `lecture-*` repo and a consumer-visible change in an `action-*` repo outrank their thread activity.

| Tier | Contents |
|---|---|
| **GC** | Verified done, superseded, or duplicate. Each gets a one-line closing comment, drafted and unsent. |
| **T0** | This week: live breakage, security exposure, release-gate reds, scheduled plan steps, small verified fixes. |
| **T1** | Aligned with the current phase or milestone of the repo's plan. |
| **T2** | Production quality, grouped by family — issues sharing a fix-shape are one unit of work. |
| **T3** | Decision-gated, external-dependency, deliberately deferred, parking lots. |

Priority labels only for genuine outliers, a handful either way, and only if the policy provides them. Then write the bundle per [deliverables.md](../../references/deliverables.md), as `01-issue-triage-report.md`, `02-issue-catalog.md`, `03-issue-links.md`, `README.md`.

## Phase 5 — self-audit

Run [doctrine §5](../../references/doctrine.md#5-coverage-self-audit) against `coverage.json`: reconcile the counts, explain every unaccounted number, confirm threads were read on both the open and closed sides, and state the residue — PR review threads, GraphQL-only data, anything after the snapshot timestamp. Fold any change back into the documents rather than appending a correction.

## What this skill does not do

It does not close, label, comment, or edit — see [doctrine §3](../../references/doctrine.md#3-read-only-boundary). The tracker pass is a separate, human-driven step working from the bundle, and label application belongs to `qe gh labels`. Judging one PR's technical quality is likewise out of scope; that is a per-item review, not a portfolio audit.
