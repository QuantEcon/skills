# Audit doctrine

The method every skill in this plugin follows. Skills own their subject matter — what to verify, how to tier, what the link graph means — and inherit everything here. Authored once; a skill that needs a rule cites this file rather than restating it.

## 1. What makes a bulk audit trustworthy

1. **Never trust an artifact's claim about its own state.** Every "fixed in X", "scheduled into Y", "superseded by Z" is a hypothesis until checked against the current default branch, `CHANGELOG.md`, and merged PRs. Cite `file:line`, a PR, or a tag for each verified claim.
2. **Check both directions.** Open items that are actually resolved, *and* closed items whose fix never really landed. An audit that only prunes is half an audit.
3. **Read every thread, closed ones included.** Closed threads carry decisions, deferred remainders, and agreed-but-never-filed work. Skipping the closed side was the one gap in this runbook's first execution, and it is the default failure mode — the snapshot captures closed threads precisely so there is no cost excuse.
4. **Distinguish guarded from fixed.** "Now fails loudly" is not "root cause resolved". Record which kind of remainder each item carries.
5. **Respect explicit maintainer intent.** A "keeping this open because…" comment beats tidiness. Note it and move on; never recommend against a stated decision without new evidence.
6. **Draft policies are conditional.** Where the governing policy is itself a draft or an open PR, recommend only what is already canonical, mark the rest *post-acceptance*, and never pre-empt the policy's own tooling.
7. **Diff against prior audits.** If an earlier audit exists, reconcile with it: convergence is corroboration, divergence needs an explanation.
8. **Match confidence to inspection.** Every claim's evidence class must be recoverable from the writeup.

## 2. Evidence classes

Findings are tagged so a reader can tell what was actually inspected. This is the machine-checkable form of rule 8, and it is what lets a reviewer trust a long report without re-running it.

| Tag | Means | Minimum citation |
|---|---|---|
| `[verified]` | Checked against code, a diff, or a build artifact | `file:line`, a merged PR, or a tag |
| `[stated]` | Asserted by a human in a thread or a notes file | Comment URL or `file:line` |
| `[inferred]` | The audit's own reasoning across sources | The sources it reasons from |

An unqualified claim is a defect. `[inferred]` is legitimate and often the most valuable class — but it must never be dressed as `[verified]`, and a status change recommended on `[inferred]` alone should say so in the recommendation itself.

## 3. Read-only boundary

**These skills observe and report. They never mutate the tracker** — no closing, labelling, milestoning, commenting, or editing, and no branch or file changes in the audited repo.

That boundary is what makes the family safe to run headlessly and safe to point at any repo in the org. Every action an audit recommends lands as a proposal in the report, executed later by a human or by a separate, deliberately-invoked step. An audit that half-applied its own findings would also be an audit whose report no longer describes the repo it was run against.

Corollary: an audit never writes into the plugin directory, and its outputs never live in `QuantEcon/skills`. See [deliverables.md](deliverables.md) for where they go.

## 4. Phases, and surviving a long run

Bulk audits outlive sessions. Context runs out, rate limits bite, machines sleep. Each skill runs the same five phases, and **each phase writes its output to the working directory before the next begins**, so a lost session resumes at the last completed phase instead of restarting.

| Phase | Produces | Resumable from |
|---|---|---|
| 1. Snapshot | `meta.json`, `issues.json`, `prs.json`, `coverage.json` | — |
| 2. Verify | per-item findings with evidence tags | the snapshot |
| 3. Relate | the cross-link / parity graph | phase 2 |
| 4. Write | the report bundle | phases 2–3 |
| 5. Self-audit | the coverage statement, folded back in | all of the above |

Phase 1 is deterministic and belongs in [`../scripts/`](../scripts/), not in model judgement. Fetching once also **freezes the audit's point in time**: every later claim refers to the snapshot, and "events after the snapshot" becomes a stated property of the report rather than an unnoticed gap. Record the snapshot timestamp in the report; never silently mix fresh API reads into a later phase.

## 5. Coverage self-audit

Before delivering, reconcile — and **close any gap found rather than merely disclosing it**. `coverage.json` from phase 1 does the mechanical half: items captured against the number sequence `1..max`, threads captured against items with comments, and a truncation flag when a stream returns exactly at the fetch limit.

The judgement half is the skill's:

- Explain every unaccounted number. Gaps are usually deleted or transferred items, or numbers burned by branches that never opened a PR — but an unexplained gap looks identical to a silent truncation.
- State the residue explicitly: what was *not* inspected. PR review threads? Native sub-issue and Projects membership, both invisible to REST? Anything after the snapshot time?
- If the self-audit changes a finding, fold the change back into the documents. Never append a correction section — a report whose conclusions and body disagree is worse than one that is simply late.

**No silent caps.** If the audit bounded its own coverage anywhere — sampled, capped at top-N, skipped a class of item — say so in the coverage statement. Silent truncation reads as complete coverage, which is the one failure an auditor cannot recover from.
