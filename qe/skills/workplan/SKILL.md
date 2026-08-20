---
name: workplan
description: Turn an audit or review report into a QEP-compliant work package — extract the high-value findings, re-verify each one against the target repository's current state, and organise the survivors into a GitHub tracking issue with linked sub-issues, labelled per QEP-2. Everything is drafted locally first; nothing is filed on GitHub until the user approves the drafts. Use when asked to process a report or audit into a work plan, turn review findings into issues, or build a work package from a report bundle. Takes a path to a report file or bundle directory, and optionally the target owner/repo.
---

# workplan

Automates the loop **read a report bundle → extract the high-value findings → re-verify each against the repo as it is today → draft a work package → (on approval) file it as a tracking issue with sub-issues**.

> **Status: merged, no validated run yet.** Shipped in `qe` 0.3.0. First-run validation — a real bundle, from an installed plugin — is tracked in [#3](https://github.com/QuantEcon/skills/issues/3).

Requires `gh`, authenticated: step 3 reads the target repo, step 5 writes to it. The reports themselves are local files — typically bundles under `~/work/quantecon/_audits/` and `~/work/quantecon/_reviews/`, many produced by the [`audit`](https://github.com/QuantEcon/skills/tree/main/audit) plugin, but any evidence-cited report works.

## Invocation

```
/qe:workplan <report-or-bundle> [owner/repo]
```

The first argument is a report file or a bundle directory. The target repo defaults to the repository the report names in its own header block; name it explicitly when the report spans several repos or the header is ambiguous. **Quote the path** — real bundle names contain colons, spaces, and `+`.

## What this skill writes

Steps 1–4 write only local draft files, next to the report. Step 5 acts on a third party, so every mutating call is listed here, and each happens only after the user has approved the drafts:

| Call | Step | What it does |
|---|---|---|
| `gh issue create` | 5 | the tracking issue, then one issue per work item |
| `gh api …/issues/<parent>/sub_issues` (POST) | 5 | links each work item as a native sub-issue |
| `gh issue edit` | 5 | fills the created sub-issue numbers back into the tracking issue's plan table |

A filed issue can be closed but not unfiled, so **do not run step 5 headlessly** — the approval gate after step 4 is the safety model.

## 1. Read the report

Reports vary — issues-only triage, PR-review packs, issues + PRs, technical-debt and test-suite studies, compliance reports — so key on the signals below rather than assuming one skeleton.

- **In a bundle directory, read the index first**: `README.md` or `REPORT.md` names the master document and links the per-item files (`PR-<n>-review.md`, `issue-<nnn>.md`), usually already ordered by recommended attention.
- **Metadata is not frontmatter.** It is a run of bolded `**Key:** value` pairs directly under the H1: repository, **Snapshot** date, baseline `main` SHA, scope, and — critically — **Supersedes**. Scrape that block; it is the most reliable structure in any of these reports.
- **Trust the header date, not the directory name.** Bundles get filed under dates that differ from the snapshot the report was actually taken at. When the same items appear in more than one bundle, deduplicate by (repo, item number) and keep the latest **Snapshot**.
- **A bundle under `_processed/` has already been actioned.** Say so and confirm before building a package from one.
- **Prefer a machine-readable companion where the report advertises one** (e.g. `triage-summary.csv`, one row per PR with quality, triage verdict, priority, and blockers) — it is the report's own structured summary of itself.

## 2. Extract — the high-value bar

A finding enters the candidate set only if all three hold:

- **Actionable** — it names a concrete change someone could start on: a fix, a decision to make, a thing to verify. Landscape narrative, statistics, and "what does not need to change" sections inform the tracking issue's background but produce no work item.
- **Evidenced** — it arrives with its citation: `file:line`, a commit SHA, an issue/PR number, measured output, or a `[verified: …]` tag. Carry the citation forward verbatim into the draft. A claim with no evidence is not promoted to a work item — at most it becomes a "verify whether…" candidate.
- **Material** — it sits at the top of the report's own scale, or it is a correctness/blocker finding at any tier.

Reports use several priority vocabularies, sometimes more than one at once. Read each against the rubric the report itself states nearby (they redefine scales between reports), and as a default mapping:

| Report says | Treat as |
|---|---|
| `P0`, 🔴, `GC`/`T0`, `high-priority`, `GAP-n (High)`, "Blocker" | high value — in |
| `MERGE`, `MERGE AFTER MINOR CHANGES` (PR triage) | in: the work item is landing it |
| `NEEDS MAINTAINER DECISION` | in, as a *decision* item (see step 4) |
| `CLOSE`, `FIXED`, ledger lines under "Resolved:" | out — hygiene the report already dispatched |
| Quality ★★ or below | usually out — the report itself says not to act on it as written; include only if the *underlying problem* independently clears the bar |
| `P2`/`P3`, `low-priority`, `T2`/`T3` | out, unless several cluster into one coherent phase |

Also mine the **repo-level findings ledger** where the report has one ("Resolved: / Still open: / New this pack:") — its *still open* and *new* entries are the densest source of cross-cutting problems not attached to any single item.

## 3. Validate against the present

The report is a snapshot and is stale by construction. For each candidate, check against the target repo's current `main` before it earns a place:

- Does the cited `file:line` still exist, and does the code still do what the finding says? (`git log <snapshot-sha>..HEAD -- <path>` on a clone, or the GitHub UI at head.)
- Is the cited issue/PR still open, and unchanged in the way that matters?
- Has a fix landed since the snapshot SHA?
- A claim the report tagged `[stated]` or `[inferred]` (rather than `[verified]`) is re-verified now, or its work item is reframed as "verify, then fix".

Drop what no longer holds, and record every drop with its reason in the draft's method note — the user should see what was filtered out, not just what survived.

## 4. Draft the work package (local files only)

Write drafts into `<bundle>/workplan/`: `00-tracking.md`, then `NN-<slug>.md` per sub-issue. The shape follows the worked exemplar, [QuantEcon.py#925](https://github.com/QuantEcon/QuantEcon.py/issues/925) with sub-issue [#926](https://github.com/QuantEcon/QuantEcon.py/issues/926):

- **Tracking issue**: Background (why now, with sources) → where we stand → a findings/gaps table with severity → a **work plan table** (`Phase | Issue | Work item`) → a sequencing paragraph (what gates what, what can land immediately) → what does *not* need to change → sources, including the report bundle this package came from and the snapshot SHA. When step 3 left genuine unknowns, phase 0 is the phase that converts them into knowns, and the dependent items say they are gated on it.
- **Sub-issues**: open with `Part of #<tracking> (Phase k).`, then the problem with its evidence as SHA-pinned permalinks, the proposed fix, and an **acceptance criteria** checklist. A finding the report left as a judgement call becomes a *decision* sub-issue — the question, the options, and the report's lean — never a silently chosen fix.
- **Labels per [QEP-2](https://github.com/QuantEcon/qeps/blob/main/qeps/qep-0002-standard-github-labels.md)**: exactly one type label per issue (`bug`/`enhancement`/`infrastructure`/`maintenance`/`discuss`…), priority labels only for the genuine outliers — there is deliberately no `medium-priority`, unlabelled *is* the middle. Check the labels exist in the target repo (`gh label list`); if not, flag that the repo hasn't adopted the QEP-2 set and propose only labels it has.
- **[QEP-1](https://github.com/QuantEcon/qeps/blob/main/qeps/qep-0001-purpose-and-process.md) check**: if the package crosses repositories or changes how the whole team works, it may warrant a QEP rather than (or before) a pile of issues — say so instead of filing.
- Every body will be GitHub-rendered, so the [rules for writing to GitHub](https://github.com/QuantEcon/skills/blob/main/AGENTS.md#writing-to-github) apply: one unbroken line per paragraph, no prose in fenced blocks, and never a closing keyword before an `owner/repo#N` reference.

Present the drafts — including the method note listing what was extracted, what was dropped in step 3 and why — and **wait for approval** before step 5.

## 5. File it (on approval)

Creation order resolves the numbering chicken-and-egg:

1. Create the tracking issue with `—` in the plan table's Issue column.
2. Create each sub-issue (`gh issue create --repo <o>/<r> --title … --body-file … --label …`); each already cites `Part of #<tracking>`.
3. `gh issue edit` the tracking issue to fill the real numbers into the plan table.
4. Link each as a **native sub-issue** — this is what makes GitHub render the progress bar and the sub-issue list:

   ```bash
   id=$(gh api repos/<o>/<r>/issues/<child-number> --jq .id)
   gh api repos/<o>/<r>/issues/<parent-number>/sub_issues -F sub_issue_id="$id"
   ```

5. Read the tracking issue back and confirm every sub-issue is listed.

**Re-runs are safe if you look first**: before each create, `gh issue list --repo <o>/<r> --search "<title> in:title"` — file only what is missing, and edit rather than duplicate.

When everything is filed, offer — don't do unasked — to move the bundle into its tree's `_processed/`, which is the local convention for "actioned".

## Gotchas

- **`sub_issue_id` is the issue's database `id`, not its number.** Posting the issue *number* either fails or links the wrong issue — always resolve via `--jq .id` first.
- **The exemplar's quality bar is the target.** #926 carries benchmarks, a rewritten implementation, and pinned permalinks because the report behind it did; a sub-issue only ever restates *the report's* evidence and your step-3 verification — it does not decorate a thin finding into looking like a thick one.
- **A package that wants more than ~15 sub-issues is a signal**, not an achievement — raise the bar in step 2 or split by phase into separate packages. (GitHub's hard cap is 100 sub-issues per parent, but the readable limit is far lower.)
- **Reports disagree with each other.** When two bundles cover the same item with different verdicts, the later snapshot wins, but say in the draft that an earlier report disagreed — the divergence is itself information.
