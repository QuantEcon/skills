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
| `[verified]` | Checked against code, a diff, or a build artifact | `file:line`, a merged PR, a tag, or a commit — each reachable from the baseline ref (below) |
| `[stated]` | Asserted by a human in a thread or a notes file | Comment URL or `file:line` |
| `[inferred]` | The audit's own reasoning across sources | The sources it reasons from |

An unqualified claim is a defect. `[inferred]` is legitimate and often the most valuable class — but it must never be dressed as `[verified]`, and a status change recommended on `[inferred]` alone should say so in the recommendation itself.

**Every `[verified]` citation is relative to one named ref, and must be reachable from it.** An audit states the ref it verified against — the default branch at the snapshot commit — and that ref is what makes its citations checkable. A citation the reader cannot resolve there is not a weaker citation; it is a false one, and worse than an untagged claim, because the tag is what invited the trust.

The failure is easy to miss because it resolves for whoever wrote it. Run 1's headline finding cited a commit that is real, does touch the file, and exists only on an unmerged branch — while the report's own header said "verified against `main` @ `2c3d624`" ([defect 1](https://github.com/QuantEcon/skills/issues/21)). A working tree carrying extra branches, or a `gh` call that searches the whole repository rather than one ref, will both produce citations that a reader checking out the stated ref finds nothing at.

So, before tagging anything `[verified]`:

```bash
git merge-base --is-ancestor <sha> <ref>   # exit 0 = citable; non-zero = not on that ref
```

The same question applies to the other citation forms, mechanically or by eye: a `file:line` must be that file and that line **on the baseline ref**, not in the working tree; a PR must be *merged into* it; a tag must be an ancestor of it. Where a claim genuinely rests on off-ref work — an open PR's branch, a fork — that is legitimate evidence, but it is cited as the open PR it is and tagged `[stated]` or `[inferred]`, never `[verified]`.

## 3. Read-only boundary

**These skills observe and report. They never mutate what they audit** — no closing, labelling, milestoning, commenting or editing on the tracker, and in the audited repo no commits, no pushes, no branches, and no changes to tracked files.

That boundary is what makes the family safe to run headlessly and safe to point at any repo in the org. Every action an audit recommends lands as a proposal in the report, executed later by a human or by a separate, deliberately-invoked step. An audit that half-applied its own findings would also be an audit whose report no longer describes the repo it was run against.

**A run may write its own working directory**, including inside the audited checkout. An audit that produces a report necessarily produces files, and what this boundary protects is the repo's *content and history*, not its untracked filesystem. So: the working directory stays untracked, nothing is added to `.gitignore` — that would itself be an edit to a tracked file — and committing or publishing the bundle is a human step taken after reading it. Prefer a location the repo already ignores where one exists; a skill's own working-directory rule says where. This resolves a contradiction with [deliverables.md](deliverables.md), which delivers the bundle *into* the audited repo's notes system: the rule is about mutation, not about writing.

Corollary: an audit never writes into the plugin directory, and its outputs never live in `QuantEcon/skills`. See [deliverables.md](deliverables.md) for where they go.

## 4. Checkpointing

An audit's intermediate work is worth writing down — but not for the reason this section used to give. It claimed bulk audits outlive sessions: context running out, rate limits biting, machines sleeping. The first measured run refuted all three at once — 230 items in 22 minutes, with none of those mechanisms in play ([run record](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-action-translation-2026-07-28.md)). The rule survived the measurement; its justification did not, and a doctrine that demands evidence for every claim owes one here.

**Write each phase's output to the working directory before starting the next**, for three reasons that hold at any duration:

1. **The checkpoint is evidence, not insurance.** A per-item verification log is what the final enumeration is assembled *from*, and what a reviewer counts against the coverage numbers — run 1's 56-of-56 reconciliation was done against the log, not the report. This is the strongest of the three, and unlike the claim it replaces it can be checked.
2. **Interruption does not care how long the run is.** A cancelled session, a tool error, a rate limit. Twenty-two minutes of item-by-item judgement is still expensive to re-derive.
3. **The cost is asymmetric.** A line per item is nearly free; the phase is not.

How a skill divides itself into phases is its own business — the division below is one that worked, not a template to fill. Note what reason 1 implies, though: a checkpoint written and then superseded minutes later without ever being read earns nothing. Name artifacts where they carry evidence, not at every phase boundary out of symmetry.

Two properties separate a checkpoint from a claim about one, and a skill that promises resumability owes both. The artifact needs a **name the next session can find without guessing** — an unnamed intermediate is only resumable if two sessions independently invent the same file. And a phase that iterates over many items must **append as it works, not write when it finishes**, because the phase long enough to be worth checkpointing is the phase a run dies *inside*. Output that exists only on completion is no checkpoint at all, exactly where one was needed.

Two things are worth doing whatever the division. **Fetch once, and fetch first**, deterministically, in [`../scripts/`](../scripts/) rather than in model judgement. That also **freezes the audit's point in time**: every later claim refers to the snapshot, so "events after the snapshot" becomes a stated property of the report rather than an unnoticed gap. Record the snapshot timestamp; never silently mix fresh API reads into a later phase.

`/audit:issues` uses five phases, which suit an audit that must capture a whole tracker, check it item by item, and then write at length:

| Phase | Produces | Resumable from |
|---|---|---|
| 1. Snapshot | `meta.json`, `issues.json`, `prs.json`, `coverage.json` | — |
| 2. Verify | per-item findings with evidence tags | the snapshot, plus its own partial output |
| 3. Relate | the cross-link / parity graph | phase 2 |
| 4. Write | the report | phases 2–3 |
| 5. Self-audit | the coverage statement, folded back in | all of the above |

A shorter audit may collapse verify and write, and one whose subject has no interesting link structure has no phase 3 at all. What it cannot skip is the last one, for the reason in §5.

## 5. Coverage self-audit

Before delivering, reconcile — and **close any gap found rather than merely disclosing it**. `coverage.json` from phase 1 does the mechanical half: items captured against the number sequence `1..max`, discussion captured per field it can live in — comments for issues, comments *and* reviews for PRs, split open and closed on both sides — and a truncation flag when a stream returns exactly at the fetch limit.

The judgement half is the skill's:

- Explain every unaccounted number. Gaps are usually deleted or transferred items, or numbers burned by branches that never opened a PR — but an unexplained gap looks identical to a silent truncation.
- State the residue explicitly: what was *not* inspected. Inline review comments, which the snapshot's review bodies do not include? Native sub-issue and Projects membership, both invisible to REST? Anything after the snapshot time?
- If the self-audit changes a finding, fold the change back into the documents. Never append a correction section — a report whose conclusions and body disagree is worse than one that is simply late.

**No silent caps.** If the audit bounded its own coverage anywhere — sampled, capped at top-N, skipped a class of item — say so in the coverage statement. Silent truncation reads as complete coverage, which is the one failure an auditor cannot recover from.
