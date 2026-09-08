---
name: workplan-project
description: Turn an audit or review report into a QEP-compliant work project — extract the high-value findings, re-verify each one against the target repository's current state, and organise the survivors into a GitHub tracking issue with linked sub-issues, labelled per QEP-2. Everything is drafted locally first; nothing is filed on GitHub until the user approves the drafts. Use when asked to process a report or audit into a work plan, turn review findings into issues, or build a work package from a report bundle. Takes a path to a report file or bundle directory, and optionally the target owner/repo.
---

# workplan-project

Automates the loop **read a report bundle → extract the high-value findings → re-verify each against the repo as it is today → draft a work project → (on approval) file it as a tracking issue with sub-issues**.

The `workplan-*` family is three skills: this one builds a **project** (tracker + sub-issues, the phased-package shape) from a report; [`workplan`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan/SKILL.md) carries the single **work-plan issue** (the cross-session state carrier) through its whole lifecycle — create, read, resume, update, close-and-succeed; [`workplan-roadmap`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-roadmap/SKILL.md) draws the project this skill files as mermaid flowcharts.

> **Status: merged, no validated run yet.** First-run validation — a real bundle, from an installed plugin — is tracked in [#65](https://github.com/QuantEcon/skills/issues/65).

Requires `gh`, authenticated: step 3 reads the target repo, step 6 writes to it. The reports themselves are local files — typically bundles under `~/work/quantecon/_audits/` and `~/work/quantecon/_reviews/`, many produced by [`/qe:audit-issues`](https://github.com/QuantEcon/skills/blob/main/qe/skills/audit-issues/SKILL.md), but any evidence-cited report works.

## Invocation

```
/qe:workplan-project <report-or-bundle> [owner/repo]
```

The first argument is a report file or a bundle directory. The target repo defaults to the repository the report names in its own header block; name it explicitly when the report spans several repos or the header is ambiguous. **Quote the path** — real bundle names contain colons, spaces, and `+`.

## What this skill writes

Steps 1–5 write only local draft files, next to the report. Step 6 acts on a third party, so every mutating call is listed here, and each happens only after the user has approved the drafts:

| Call | Step | What it does |
|---|---|---|
| `gh issue create` | 6 | the tracking issue, one issue per work item, and any step-4 non-member findings, filed unparented |
| `gh issue edit <parent-number> --add-sub-issue` | 6 | links each work item as a native sub-issue, in plan order |
| `gh api …/issues/<parent-number>/sub_issues/priority` (PATCH) | 6 | re-runs only: moves a recovered item into its plan position |
| `gh issue edit <parent-number> --type Project` | 6 | applies the native issue type to the tracking issue |
| `gh issue edit <item> --add-blocked-by <blocker>` | 6 | records a real sequencing constraint as a native dependency (§4). One call per edge — `gh` takes no list. For a blocker in **another repository** `gh` refuses the flag outright; use `gh api --method POST repos/<o>/<r>/issues/<n>/dependencies/blocked_by`, whose body takes the blocker's numeric **id**, not its number |

A filed issue can be closed but not unfiled, so **do not run step 6 headlessly** — the approval gate after step 5 is the safety model.

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
| `NEEDS MAINTAINER DECISION` | in, as a *decision* item (see step 5) |
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

## 4. Decide membership

Step 2 is a quality bar and step 3 a truth bar; neither asks whether a finding belongs to *this* project. A report bundle covers a repository over a window, which is not a project, so a goal written from whatever survived describes the list instead of constraining it — and a package built that way passes every structural check while being a repository sweep with a goal fitted afterwards, which is exactly what the QEP-6 field test produced ([qeps#19](https://github.com/QuantEcon/qeps/issues/19), amendment 9).

So, before drafting, write the project's **definition of done** in one sentence — what has to be true for the tracker to close — from the report's framing of the problem, not from the survivors. Then test each survivor against it using [QEP-6 §1](https://github.com/QuantEcon/qeps/pull/18)'s membership criterion, which is cited rather than restated here except for its diagnostic, because the diagnostic is the working tool: **if the goal must be widened to justify an item's membership, the item is not a member.**

- **Two definitions of done are two packages**, whatever the count. Fifteen items that all serve one goal are a large project, not a bad one; the ~15 figure in the gotchas is a prompt to re-ask this question, never the criterion, and splitting by phase or by size leaves each half with the same fitted-afterwards goal.
- **Non-members that still clear step 2's bar are filed as ordinary issues and left unparented.** An unparented issue is the normal case (§1), and a skill that has just filtered a report will otherwise parent everything it kept.
- **The method note records each exclusion** as *kept, not a member of this project*, distinct from step 3's *dropped, no longer holds* — the user should be able to see both lists and disagree with either.

## 5. Draft the work package (local files only)

Write drafts into `<bundle>/workplan/`: `00-tracking.md`, then `NN-<slug>.md` per sub-issue. The **shape** is [QEP-6 Appendix A](https://github.com/QuantEcon/qeps/pull/18)'s skeleton. Two worked exemplars cover what a skeleton cannot show, and each is cited for one thing: [QuantEcon.py#925](https://github.com/QuantEcon/QuantEcon.py/issues/925) for the *content* of a tracker body — background with sources, a gaps table with severities, sequencing rationale, what does not change — and its sub-issue [#926](https://github.com/QuantEcon/QuantEcon.py/issues/926) for the *evidence bar*. #925 is not cited for shape: its plan table carries an `Issue` and a `Status` column, which is the mirror QEP-6 §7 forbids, so copy its sections and not its table. A concrete artefact beats an abstract rule for any producer, which is why the exemplar's defect is named here rather than left for the reader to notice.

- **Tracking issue**: Background (why now, with sources) → **`## Where we stand (verified <date>)`** → a findings/gaps table with severity → a **phase table** (`Phase | Intent | Exit criterion`) → **Gates** (which phase waits on what) and a sequencing paragraph (why this order, what can land immediately) → what does *not* need to change → sources, including the report bundle this package came from and the snapshot SHA. That heading is the project tracker contract's status stamp and its form is exact — see **The tracker contract** below. The phase table carries what the sub-issue list cannot — what each phase is for and when it is finished — and **never an `Issue` or `Status` column**: membership, order and state are the sub-issue list's, and a body that repeats them is the mirror [QEP-6 §7](https://github.com/QuantEcon/qeps/pull/18) forbids, one that can visibly disagree with the live list rendered on the same page. When step 3 left genuine unknowns, phase 0 is the phase that converts them into knowns, and the dependent items say they are gated on it.
- **Plan order**: the draft file order *is* the plan order — `NN-<slug>.md` files numbered in the order the work should happen, each phase's items contiguous — because the sub-issue list is the plan under [QEP-6 §3](https://github.com/QuantEcon/qeps/pull/18): position is sequence, and the topmost open item is next. Step 6 files and links in that order and checks the result against it. The `NN-` prefix is a draft filename and nothing else — it never reaches an issue title, since §3 bans sequence tokens in titles and milestone names outright.
- **More than one package**: when step 4 splits the survivors, each package's draft gets a `## Related work` section naming its siblings — one line each on how they relate, **projects only, never work items**, since an entry about a work item is the sub-issue list restated or dependency prose, both of which [QEP-6 §7](https://github.com/QuantEcon/qeps/pull/18) forbids. A gate between packages is **carried as native dependency edges**, with only its *rationale* stated once, in the body of the package that *waits* — prose is the one carrier no consumer reads. An edge is written only where the downstream item cannot start without something the upstream produces — a ruling, a field, a document, a page it draws from; that two items touch the same file, or will be worked in sequence, is plan order, which is position and not an edge, and it goes under the body's sequencing rationale rather than its gates. State it at the granularity that is actually true: usually one phase waiting on one phase, not one project waiting on one project, since a tracker-to-tracker edge asserts that nothing in the downstream may start and parks it wholesale in any consumer deriving parked-ness from open blockers. [§4](https://github.com/QuantEcon/qeps/pull/18) gives the phase-level form — the **first item of the waiting phase is blocked by every item of the phase it waits on**, which is linear in the upstream phase rather than a cross-product and clears when that *phase* closes rather than when the upstream tracker does. Where a phase's exit criterion is a single `Decision` closing, each waiting item carries the edge to that `Decision` instead. The sibling's `Related work` entry *may* point at the rationale but is not obliged to: blocked-by and blocking are two ends of one edge, so the waited-on package needs no back-pointer to stay in step. Both sections are in Appendix A; they are named here because a producer fills the slots that exist and invents none.
- **Sub-issues**: open with `Part of #<tracking> (Phase k).`, then the problem with its evidence as SHA-pinned permalinks, the proposed fix, and an **acceptance criteria** checklist. A finding the report left as a judgement call becomes a *decision* sub-issue — the question, the options, and the report's lean — never a silently chosen fix.
- **A work item that is an existing issue** — landing PR #n, deciding issue #m, a finding the repo had already filed — is linked, not re-created, and linking is claiming: sub-issue membership is single-parent, so adding an issue here removes it from whatever tracker holds it now. Read its parent at draft time, `gh issue view <n> --repo <o>/<r> --json parent --jq '.parent.number // empty'`, and where that is non-empty the method note says so in terms the user can act on: *item #n is currently a work item of #p; adding it here removes it from #p.* The approval that follows then covers the detachment knowingly, or the item stays where it is and the package cites it instead.
- **Labels per [QEP-2](https://github.com/QuantEcon/qeps/blob/main/qeps/qep-0002-standard-github-labels.md)**: exactly one type label per issue (`bug`/`enhancement`/`infrastructure`/`maintenance`/`discuss`…), priority labels only for the genuine outliers — there is deliberately no `medium-priority`, unlabelled *is* the middle. Check the labels exist in the target repo (`gh label list`); if not, flag that the repo hasn't adopted the QEP-2 set and propose only labels it has.
- **The tracker contract**: what this skill produces *is* a project tracker — one issue, its direct sub-issues the work — so it is drafted to conform with [`docs/contracts/tracker.md`](https://github.com/QuantEcon/status-projects/blob/main/docs/contracts/tracker.md) (C2), which states the rules once and is not restated here. Three bear on the draft: the stamp heading above in its exact form; the work in **native sub-issues**, never body checkboxes, since checkbox progress publishes as `null`; and the native `Project` issue type, applied at step 6.
- **The tracker structure**: [QEP-6](https://github.com/QuantEcon/qeps/pull/18) (draft) rules what the tracker body may and may not carry, and this skill follows it wherever it goes further than C2. The two disagree in one place worth knowing: C2 forbids nothing in the body beyond the stamp and never *reads* a plan table, so a roster of work items there is C2-conformant, while QEP-6 §7 forbids it. QEP-6's Adoption clause 4 rules that QEP-6 is authoritative for tracker structure until C2's planned handover to it; this skill applies that ruling rather than choosing between the two, and says so here so that a reader who checks the draft against C2 alone is not surprised.
- **[QEP-1](https://github.com/QuantEcon/qeps/blob/main/qeps/qep-0001-purpose-and-process.md) check**: if the package crosses repositories or changes how the whole team works, it may warrant a QEP rather than (or before) a pile of issues — say so instead of filing.
- Every body will be GitHub-rendered, so the [rules for writing to GitHub](https://github.com/QuantEcon/skills/blob/main/AGENTS.md#writing-to-github) apply: one unbroken line per paragraph, no prose in fenced blocks, and never a closing keyword before an `owner/repo#N` reference.

Present the drafts — including the method note listing what was extracted, what was dropped in step 3 and why, and what was kept but excluded in step 4 — and **wait for approval** before step 6.

## 6. File it (on approval)

The tracking issue is written **once**: its body names no sub-issue numbers, so nothing has to be filled in after the children exist, and there is no second body write to lose the stamp in.

1. Create the tracking issue (`gh issue create --repo <o>/<r> --title … --body-file … --label …`).
2. Create each sub-issue the same way, **in draft order**; each already cites `Part of #<tracking>`.
3. Link each as a **native sub-issue**, in the same order — this is what makes GitHub render the progress bar and the sub-issue list, and linking appends, so linking in draft order produces plan order:

   ```bash
   gh issue edit <parent-number> --repo <o>/<r> --add-sub-issue <child-number>
   ```

   The verb takes plain issue numbers (`gh` ≥ 2.94); no database-id lookup on this path. It also **replaces an existing parent unconditionally** — `--add-sub-issue` and `--parent` both send `replace_parent=true` with no opt-out, so on an already-parented issue the same call succeeds and steals it. Issues created in item 2 above are parentless and safe. For anything else, the parent read in step 5 is the guard, and it has to have happened: never link an issue whose parent this run has not read. (The raw REST `POST …/sub_issues` behaves differently — it omits `replace_parent` and fails on a parented child — which is why the skill uses one method, the verb, with one guard, rather than two methods with two behaviours.)
4. Apply the tracker's native type: `gh issue edit <parent-number> --repo <o>/<r> --type Project`. It is org-level and label-free, so QEP-2's set is untouched; if the type is missing the call fails harmlessly — report it and carry on, since an untyped tracker is a finding rather than a failure.
5. Read back and confirm every sub-issue is listed, **in draft order**, and the stamp heading is intact. `gh api repos/<o>/<r>/issues/<parent-number>/sub_issues --jq '.[].number'` returns the list in position order, which is what the rendered page shows. Check on GitHub, not on the projects dashboard: its collector re-sorts children by issue number until [status-projects#19](https://github.com/QuantEcon/status-projects/issues/19) ships, so a tracker in plan order and one in arbitrary order publish identically there.

**Re-runs are safe if you look first, and place what they file**: before each create, `gh issue list --repo <o>/<r> --search "<title> in:title"` — file only what is missing, and edit rather than duplicate. An issue the search finds is one the drafts did not know about, so its parent has not been read: read it now, and if it is set, **stop before linking** and bring it back to the user with the parent named — the approval covered filing the package, not detaching someone else's work item. A detachment that goes ahead is recorded in the method note and in the tracking issue's sources, so the change is visible to whoever owns the other tracker. A recovered item then has to be **moved into its plan position**, because linking appends it to the bottom whatever phase it belongs to — a phase-2 item recovered on a re-run lands after phase 4, silently, and the tracker no longer states the plan. Reordering is the one sub-issue operation with no `gh` verb; it is the reprioritise API, and it wants database ids, not numbers:

```bash
# database ids of the parent's current children, in list order
gh api repos/<o>/<r>/issues/<parent-number>/sub_issues --jq '.[] | "\(.number) \(.id)"'
# place the recovered item directly after its intended predecessor
gh api --method PATCH repos/<o>/<r>/issues/<parent-number>/sub_issues/priority \
  -F sub_issue_id=<child-id> -F after_id=<predecessor-id>
```

Then run the item-5 read-back again. The reprioritise write is reflected in the list read-back, and REST, GraphQL and the rendered page all return the same order.

When everything is filed, say plainly that the tracker is **not on the projects dashboard until it is registered**: a row in [`projects.yml`](https://github.com/QuantEcon/status-projects/blob/main/projects.yml) carrying its slug, programme, stage, owner, one public sentence and the tracker in `Owner/repo#N` form, landed as a pull request against `QuantEcon/status-projects` and gated by that repo's validator. Offer to draft the row; leave opening the PR to the user. Then offer — don't do unasked — to move the bundle into its tree's `_processed/`, which is the local convention for "actioned".

## Gotchas

- **The reprioritise call mixes two kinds of integer.** The parent in the path is an issue *number*; `sub_issue_id` and `after_id` in the body are database *ids*, ten-digit and unrelated to the numbers. Both are bare integers and the API cannot tell a transposition from a request, so read the ids from the `sub_issues` listing in the same breath as the call. This is the only place the skill needs a database id; linking takes numbers.
- **Linking is claiming, and the theft is silent.** In the QEP-6 field test ([qeps#19](https://github.com/QuantEcon/qeps/issues/19), finding 1) ten items linked into a new tracker were detached from the org's QEP-2 rollout tracker by that act alone, leaving it with one closed child and a published 100%. No error, no warning, in a repository nobody was watching. One `--json parent` read per pre-existing item is the whole cost of not doing that; QEP-6 Adoption clause 3 makes it an obligation on conform tooling, and for the create path this skill is that tooling.
- **The exemplar's quality bar is the target.** #926 carries benchmarks, a rewritten implementation, and pinned permalinks because the report behind it did; a sub-issue only ever restates *the report's* evidence and your step-3 verification — it does not decorate a thin finding into looking like a thick one.
- **A package that wants more than ~15 sub-issues is a signal**, not an achievement — go back to step 4 and ask whether the survivors answer to one definition of done. Usually they answer to two, and the phase boundary turns out to be the membership boundary: an oversized package is most often a membership problem wearing a size costume. Split by definition of done, never by count. (GitHub's hard cap is 100 sub-issues per parent, but the readable limit is far lower.)
- **Reports disagree with each other.** When two bundles cover the same item with different verdicts, the later snapshot wins, but say in the draft that an earlier report disagreed — the divergence is itself information.
