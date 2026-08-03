# Changelog — `audit`

Every released version of this plugin, newest first. A version exists because the content below shipped in it: the plugin cache is keyed by version string, so what you have installed is exactly the entries down to the version `claude plugin list` reports for `audit`.

Versions are [semver](https://semver.org) as a user of this plugin experiences it — a new skill, or a procedure that now does something materially different, is a minor bump; a correction that leaves the procedure as it was is a patch. Nothing below 1.0.0 promises stability.

Repository: [QuantEcon/skills](https://github.com/QuantEcon/skills) ([every commit that touched this plugin](https://github.com/QuantEcon/skills/commits/main/audit)). How a release is made: [developing-skills § Versioning and releases](https://github.com/QuantEcon/skills/blob/main/docs/developing-skills.md#versioning-and-releases).

## 0.1.4 — 2026-08-03

Doctrine §4's rule survived the first measured run; its justification did not. The section is re-derived from what that run actually produced, and the cost figures the skill quotes are replaced with measured ones.

**Changed**

- Doctrine §4 is renamed from "Surviving a long run" to "Checkpointing", and rests on three reasons that hold at any duration rather than on the claim that audits outlive sessions. The first measured run refuted that claim outright — 230 items in 22 minutes, with no context exhaustion, rate limit or sleeping machine in play. The strongest replacement reason is checkable: the per-item log is what the final enumeration is assembled *from*, and what a reviewer counts the coverage numbers against.
- `/audit:issues` no longer describes itself as "long-running by design — a hundred-issue repo is a multi-hour run". It now quotes the measured cost: roughly **10 seconds per open issue**, with a 230-item tracker carrying 56 open issues taking 22 minutes. Cost tracks open issues needing verification rather than total items, so a large tracker with a small open set is cheaper than a small one with a large set.
- The cost figures are stated so the two measures cannot be confused. Previously a reader met "roughly 10 seconds per open issue" beside "a 230-item tracker with 56 open took 22 minutes" and could not reconcile them — 56 × 10 s is 9 minutes, not 22. The 10-second rate is phase 2 alone; 22 minutes is end to end, and the remaining phases are largely fixed. Both numbers now say which question they answer.
- Checkpoint artifacts are named where they carry evidence rather than at every phase boundary out of symmetry — a checkpoint written and superseded minutes later without ever being read earns nothing.

## 0.1.3 — 2026-08-03

**Added**

- This changelog.

**Fixed**

- `/audit:issues`'s frontmatter `description` was an unquoted YAML plain scalar containing `Read-only: it recommends…`. A `: ` inside a plain scalar is a parse error, so a strict loader drops the skill's metadata rather than reading it, and `claude plugin validate` rejects the file outright. The value is now quoted. Nothing about the procedure changed.

## 0.1.2 — 2026-07-28

Resolves the contradiction that told an audit to write its bundle into the repo it promised not to touch: the boundary is now mutation, not writing, and the skill says exactly where to put its working directory so a run leaves `git status` clean.

**Added**

- Discovery-ordered working-directory selection, taken from contact with a real repo: prefer a location the repo already ignores (`.dev/scratch/audit-<YYYY-MM-DD>/` in QuantEcon repos, where `.dev/scratch/*` is already gitignored), fall back to an untracked `.audit/<repo>-<YYYY-MM-DD>/` at the checkout root, then to somewhere outside the checkout entirely. Which one was used goes in the report's method section.
- Doctrine §3 now says explicitly that a run may write its own working directory, including inside the audited checkout — provided the directory stays untracked and nothing is added to `.gitignore`, since that would itself be an edit to a tracked file.

**Changed**

- Doctrine §3 narrowed from "no branch or file changes in the audited repo" to what it was always protecting — content and history: no commits, no pushes, no branches, no edits to tracked files. Mutation, not writing, is the boundary.
- `deliverables.md` states the split: writing the bundle is the audit's job, committing or publishing it is a human step taken after reading it.

**Fixed**

- The read-only/working-directory contradiction the plugin carried since 0.1.0 — §3 forbade file changes in the audited repo while `deliverables.md` made that repo's own notes system the bundle's first-choice destination, and 0.1.1's default `--out` wrote there too. A run following the docs literally could not satisfy both.

## 0.1.1 — 2026-07-28

An interrupted run can actually be resumed: the intermediate artifacts now have names and locations, phase 2 appends per item instead of writing at the end, and the bundle shrinks to fit a small tracker.

**Added**

- A stated working-directory layout under `--out` (`.audit/<repo>-<YYYY-MM-DD>/` by convention): `snapshot/` from phase 1, `findings.md` from phase 2, `links.md` from phase 3, and the delivered `01-…`/`02-…`/`03-…`/`README.md` bundle from phase 4. Previously phases 2 and 3 produced "per-item findings" and "the cluster map" with no filename and no location, so resuming worked only if two sessions independently invented the same file.
- A stated resume rule: on restart, read `findings.md` and resume at the lowest number in `issues.json` with no entry, re-verifying the last entry rather than trusting a possibly truncated write.
- `meta.json` records `fetched_by`, the account the snapshot was taken as — which matters because visibility on the org's private repos is per-account.

**Changed**

- Phase 2 appends each item's finding to `findings.md` as it is verified, in the catalog entry format, so phase 4 assembles the catalog instead of re-deriving it.
- The bundle scales to the tracker: below roughly 30 open issues, fold the catalog and the link graph into the report, keep the `README.md` index, and say which shape was used in the coverage statement. Four unconditional documents forced three files of padding on a small tracker, and padding makes a report less checkable.
- Doctrine §4 now states the general rule: a checkpoint owes a findable name and incremental writes, or it is a claim about resumability rather than the property itself.

**Fixed**

- `meta["authenticated"]` is removed, not deprecated. It could only ever be `true` (preflight exits on every unauthenticated path), so it was a provenance field carrying no evidence — in the plugin whose doctrine is that every claim carries its evidence class. **Anything reading that field must switch to `fetched_by`.**
- An interrupted phase 2 now loses one item rather than the whole phase — it was the phase specified to write on completion, and the phase a hundred-item run dies inside rather than between.

## 0.1.0 — 2026-07-27

First release. `/audit:issues` sweeps an entire GitHub tracker — open and closed — verifies each item against the code rather than the thread, tiers the open set into the repo's existing plan, and delivers an evidence-cited report bundle, without ever touching the tracker.

- `/audit:issues <owner/repo>` — a whole-tracker audit in five phases (snapshot, per-item verification, cross-link graph, tiered report, coverage self-audit). The four runbook fields (plan anchor, tier scheme, repo type, notes system) are optional arguments with documented discovery, so the usual invocation is just the repo.
- A deterministic snapshot step, `scripts/fetch_tracker.py OWNER/REPO --out <dir>`: every issue and PR in any state with full comment threads (and PR reviews, and `closingIssuesReferences`) in two `gh` round trips, written as `meta.json`, `issues.json`, `prs.json`, `coverage.json`. Closed threads cost nothing extra to read, and the snapshot freezes the audit's point in time so "events after the snapshot" is a stated property of the report instead of an unnoticed gap.
- `coverage.json` reconciliation: captured items against the number sequence `1..max`, discussion counts split open/closed, and an explicit truncation flag when a stream returns exactly at `--limit` (default 1000) — a case indistinguishable from truncation, so it is surfaced rather than swallowed. PR review bodies count toward captured discussion, not just comments: on the example repo, closed PRs carried 374 reviews against 28 comments.
- Snapshot files are written in issue/PR number order, so two runs over an unchanged tracker are byte-identical and a re-fetch diffs down to what actually changed.
- Thread payloads are shape-asserted at capture, so a `gh` build returning counts instead of lists fails by name at the point of capture rather than crashing later or silently under-reporting threads while the report still claims thread-completeness.
- Preflight that refuses to start without `gh` and an authenticated account, because the anonymous API is 60 req/h per IP and returns nothing at all for the org's private repos.
- Plugin-level method shared by every future audit skill: `references/doctrine.md` (trust rules, evidence classes `[verified]`/`[stated]`/`[inferred]`, the read-only boundary, checkpointing, the coverage self-audit), `references/quantecon-context.md` (repo types, label ownership, the cross-repo graph, access, and the caveat that an HTML-reconstructed thread may start mid-conversation), and `references/deliverables.md` (what an audit owes its reader, and where a bundle may land).
- QuantEcon-specific triage judgement: tier by repo type (a build break in a lecture repo and a consumer-visible change in an action repo outrank thread activity), check sibling repos before concluding, leave label application to `qe`, and keep GitHub closing keywords out of drafted cross-repo references so drafted text cannot close an upstream item when someone posts it.
- The four-document bundle, the five phases and "produces a bundle" are stated as a worked example rather than a requirement, after a single execution. What an audit owes its reader — coverage statement, evidence tag per claim, recommendations marked as proposals, drafted comments marked unsent, a date and a named snapshot — stays mandatory and presumes no file count.
