---
name: workplan-read
description: Read a work-plan tracking issue, validate it against live state, and recommend next steps — find the repo's open plan (or take an issue number/URL), report its current state, check the plan's premises read-only against what actually happened since its revision stamp (commits, PRs, issues), and finish with a recommendation of what leads next and whether the plan body needs revising first. Strictly read-only: it never edits the issue or posts comments — discrepancies become recommendations, usually to run workplan-update's resume path, never silent corrections. Use when asked to show or check the work plan, see what's on the plan or what's next, find out where things were left off, or get oriented before starting a session.
---

# workplan-read

Reads a work-plan issue, validates it, and recommends next steps — without writing anything. This is the family's front door for "what's on the plan?", "where did we leave off?", "what should I do next?": before this skill existed those requests routed to [`workplan-update`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md), a maintenance skill whose every verb writes; none of its three moments (`resume`/`update`/`close`) is "just look".

The `workplan-*` family: [`workplan-project`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-project/SKILL.md) builds a project (tracker + sub-issues) from a report; [`workplan-issue`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md) creates a work-plan issue and owns the convention that defines its shape; [`workplan-update`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md) maintains one across sessions; this skill reads and validates one, recommending next steps.

> **Status: merged, no validated run yet.** Shipped in `qe` 0.5.0, from the friction finding in [#50](https://github.com/QuantEcon/skills/issues/50). First-run validation is tracked in [#3](https://github.com/QuantEcon/skills/issues/3).

Requires `gh`, authenticated — for reading only.

## Invocation

```
/qe:workplan-read [--full] [issue# | url]
```

With no issue, discovery works exactly as in [`workplan-update` § Invocation](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md#invocation): one open plan proceeds, several is a finding to surface, zero means there is no plan yet — offer [`workplan-issue`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md). `--full` validates every claim in the body rather than the default depth (see step 2).

## What this skill writes

Nothing. No issue edits, no comments, no local drafts to approve — there is no gate because there is nothing to gate. Everything it finds comes out as a report and a recommendation; acting on the recommendation is a handoff to the skill that owns that write, under that skill's gates.

## 1. Read

Read the body and the comment thread (`gh issue view <n> --comments`), and establish:

- **Header**: title, number, open/closed, and the body's own **revision stamp** with its age ("stamped 2026-08-20 18:04 AEST — 5 days ago"). The stamp is the plan's warranty date and the anchor for step 2.
- **The front of the plan**: what the body says leads next, and why it leads.
- **Live-state facts**: the body's live-state table — the plan's claims *as of the stamp*.
- **Blocks and gates**: each work block, its status, and what gates it.
- **Latest revision log**: the last comment is the previous session's handover note — who/when, what landed, what inverted.
- **Explicitly not doing**: what the plan already deferred, so a recommendation doesn't re-litigate a decision the plan records.

## 2. Validate (read-only)

The body was true at its stamp; the gap since is unaudited. Audit it — with reads only:

- **Sweep since the stamp**, scoped by the plan's own link graph, using the same discipline as [`workplan-update` § Anchor and sweep](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md#1-anchor-and-sweep-all-paths-start-here): commits on default branches, PRs opened/merged/closed, issues filed/edited/closed (`gh search issues/prs --updated ">STAMP"`, `git log` where a clone exists). Plans routinely live in one repo while the work spans several.
- **Check the plan's premises against what the sweep found.** Default depth: the front-of-plan items plus anything the sweep contradicts; `--full` checks every claim in the body — worth it after a long gap.
- **Classify each checked claim**: *holds* (still true as stated), *aged* (true but the numbers moved — say both values), or *inverted* (no longer true — say what the plan believed, what is actually true, and the trace that shows it). Every verdict cites its evidence: a commit, PR, or issue number, or a command output.
- **Report body and reality side by side, never blended.** The body still says what it said; your findings are observations about it. A half-verified hybrid presented as "the plan" is worse than either, because nobody stamped it — bringing the body up to date is [`workplan-update`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md)'s job, under its approval gates.

## 3. Recommend

Close with a recommendation the user can act on — advice, not action:

- **What leads next, and why**: the front of the plan if it survived validation, or what validation says actually leads now if it didn't.
- **Whether the body needs revising first.** Any inverted premise, or material drift in the live-state facts, means the plan should be re-stamped before being worked: recommend `/qe:workplan-update resume` (with `--full` after a long gap). If everything holds, say so — the plan can be worked as written.
- **Match the moment.** Findings can also point at the family's other paths: every item done or carried → suggest `close`; no plan found → suggest [`workplan-issue`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md); a new defect surfaced by the sweep → suggest filing it as its own issue (per the convention, defects become issues, not paragraphs).
- **Never run the handoff unasked.** The recommendation names the skill and the reason; invoking it is the user's move.

## Gotchas

- **Validation here is not revision.** Finding a dead premise does not license fixing it — the finding goes in the report and the recommendation, and the body changes only through `workplan-update`, gated. This is the line that keeps a read skill safe to run casually.
- **A read-only sweep is still a sweep of other people's work.** Traces since the stamp include humans', bots', and parallel sessions' activity; report what happened without guessing at attribution.
- **Comments are revision logs, newest last.** The *latest* comment is the handover; earlier ones are history. Don't summarise the whole thread as if it were current state — the body is the single source of truth, revised in place.
- **A closed plan is still readable.** Its closing ledger and carry-forward register answer "what happened to X?"; if the user wants the live thread, follow the "continuing from #N" chain forward to the open successor and read that.
