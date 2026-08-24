---
name: workplan-read
description: Read a work-plan tracking issue without changing it — find the repo's open plan (or take an issue number/URL), report its current state (revision stamp and its age, what leads next, the live-state facts, block status, the latest revision log), and flag how stale the plan is. Strictly read-only, it never edits the issue or posts comments; working the plan starts with workplan-update's resume path instead. Use when asked to show the work plan, see what's on the plan, check the plan's status, find out where things were left off or what's next, or answer questions about a plan without starting or ending a session.
---

# workplan-read

Reads a work-plan issue and reports its state — nothing more. This is the family's front door for questions like "what's on the plan?", "where did we leave off?", "what leads next session?": before this skill existed those requests routed to [`workplan-update`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md), a maintenance skill whose every verb writes; none of its three moments (`resume`/`update`/`close`) is "just look".

The `workplan-*` family: [`workplan-project`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-project/SKILL.md) builds a project (tracker + sub-issues) from a report; [`workplan-issue`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md) creates a work-plan issue and owns the convention that defines its shape; [`workplan-update`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md) maintains one across sessions; this skill reads one.

> **Status: merged, no validated run yet.** Shipped in `qe` 0.5.0, from the friction finding in [#50](https://github.com/QuantEcon/skills/issues/50). First-run validation is tracked in [#3](https://github.com/QuantEcon/skills/issues/3).

Requires `gh`, authenticated — for reading only.

## Invocation

```
/qe:workplan-read [issue# | url]
```

With no argument, discovery works exactly as in [`workplan-update` § Invocation](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md#invocation): one open plan proceeds, several is a finding to surface, zero means there is no plan yet — offer [`workplan-issue`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md).

## What this skill writes

Nothing. No issue edits, no comments, no local drafts to approve — there is no gate because there is nothing to gate. If the conversation turns into maintaining the plan, that is a handoff, not scope creep here (see below).

## The report

Read the body and the comment thread (`gh issue view <n> --comments`), then report — in this order, because it is the order a reader needs:

- **Header**: title, number, open/closed, and the body's own **revision stamp** with its age ("stamped 2026-08-20 18:04 AEST — 5 days ago"). The stamp is the plan's warranty date; lead with it.
- **The front of the plan**: what the body says leads next, and why it leads — the resume pointer is the single most useful line in the artifact.
- **Live-state facts**: the body's live-state table, reported as the plan's claims *as of the stamp*, not as current truth.
- **Blocks and gates**: each work block, its status, and what gates it.
- **Latest revision log**: who/when, what landed, what inverted — the last comment is the previous session's handover note.
- **Explicitly not doing**: relay it when the user's question touches something the plan already deferred — that section exists precisely to stop re-litigation.

Answer the user's actual question from this material; the full dump is for "show me the plan", not for every query.

## The staleness caveat — the one obligation

The convention this family operates ([`workplan-issue` § The convention](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md#the-convention)) is that a plan body is trusted *as of its revision stamp*, and the gap since is unaudited. A read must not blur that line:

- Always report the stamp's age. After a long gap, say plainly that every fact carries that date.
- **Do not re-verify, and do not silently correct.** If you happen to know a body claim is stale (a PR merged since, say), report the body faithfully *and* note the discrepancy as an observation — never present a half-verified hybrid as the plan, because nobody stamped that hybrid. Re-verification that revises the body is [`workplan-update`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md)'s `resume` path, under its gates.
- **End with the handoff when it applies**: if the user is about to work the plan, point at `/qe:workplan-update resume`. Reading is the front door to a session, not a way around the verification discipline.

## Gotchas

- **The plan's link graph spans repos.** Report what the body cites where it cites it; don't chase every linked issue across the estate unless the user's question requires it — this is a read, not a sweep.
- **Comments are revision logs, newest last.** The *latest* comment is the handover; earlier ones are history. Don't summarise the whole thread as if it were current state — the body is the single source of truth, revised in place.
- **A closed plan is still readable.** Its closing ledger and carry-forward register answer "what happened to X?"; if the user wants the live thread, follow the "continuing from #N" chain forward to the open successor and read that.
