---
name: workplan
description: Create, read, resume, update, or close the work-plan tracking issue — the single GitHub issue that carries state between agent sessions — one skill for the artifact's whole lifecycle. Reading validates the plan against live state and recommends next steps, writing nothing; every other verb drafts locally and writes only after approval. Use when asked to create a work plan, show or check the plan, see what's on it or what's next, resume from a plan, record session state, or close out and hand over to the next session. Takes a verb and optionally the plan issue's number or URL, or discovers the repo's single open work-plan issue.
---

# workplan

One skill for the whole lifecycle of the **work-plan issue**: the single GitHub issue a session resumes from, works through, and hands over to the next session. A session is one agent context window; when it ends, the context is gone, so one acceptance test governs everything this skill writes:

> **A fresh agent, given only the issue, can resume the work without the old conversation.**

The `workplan-*` family is two skills: this one carries the plan through `create` → `read` → `resume` → `update` → `close`-and-succeed; [`workplan-project`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-project/SKILL.md) builds a **project** (tracker + sub-issues) from an audit or review report.

> **Status: merged, no validated run yet.** First-run validation is tracked in [#3](https://github.com/QuantEcon/skills/issues/3).

Requires `gh`, authenticated (`read` uses it for reading only).

## The convention

Observed practice across the org's work-plan issues (exemplars: the [project-translation#37](https://github.com/QuantEcon/project-translation/issues/37) session chain, the [workspace-lectures#48](https://github.com/QuantEcon/workspace-lectures/issues/48) weekly series, [skills#25](https://github.com/QuantEcon/skills/issues/25)). Formalising it as a QEP is planned; until that lands, this section records the practice — and once it lands, this section becomes a pointer.

- **The body is the single source of truth for current state, revised in place.** It never accumulates narrative, and it stamps its own revision — with time and timezone, not a bare date, when sessions run close together (see the date-rollover gotcha below).
- **Comments are revision logs**: what changed and why — especially premises that *inverted* rather than merely aged.
- **Claims are verified against live state, never assumed or carried forward.** The artifact's whole value is that a future session can trust it blind; one unverified "fact" poisons that.
- **New defects become their own issues, not plan paragraphs.** A problem a session discovers is filed as a linked issue (the exemplars file them same-day) and the plan cites it; prose-only findings are how things get lost.
- **A plan is not a dumping ground.** Work that is real but not agreed goes to its own labelled issue; the "explicitly not doing" section exists so deferrals are decisions, not omissions.
- **Two genres, one lifecycle each.** A *period plan* (a session's or week's work) closes with a ledger and is succeeded; a *long-lived tracker* (a project-duration state register) is resumed and updated but never session-closed.
- **Succession never copies.** The successor is built from the carry-forward register — unfinished and deferred items plus what the closing session surfaced — and opens "continuing from #N".
- **One open period plan per repo at a time.** This is what makes "resume the session" — and this skill's issue discovery — unambiguous.
- **Plan issues stay untyped** pending the [QEP-2](https://github.com/QuantEcon/qeps/blob/main/qeps/qep-0002-standard-github-labels.md) field report on labelling plan/tracking issues.

## Invocation

```
/qe:workplan [create [owner/repo] | read [--full] | resume [--full] | update | close] [issue# | url]
```

Both arguments are optional. With no issue, discovery looks for the repo's open plan (`gh issue list --state open --search "work plan in:title"`, plus `TRACKING:`/`PLAN:` title prefixes): exactly one hit proceeds; several is a finding to surface; zero means there is no plan yet — that is `create`'s job, offer it. With no verb: a look-shaped request — status, what's next, where things were left — is `read`; anything else, ask which moment this is rather than inferring, because the cost of running `close` when the user meant `update` is a wrongly closed plan.

## What this skill writes

`read` writes nothing. Every other verb drafts locally first, shows the draft (as a diff against the live body where a body is being revised), and writes only after the user approves it.

| Call | Verb | Gate |
|---|---|---|
| `gh issue create` | create; close (the successor) | after the user approves the draft body |
| `gh issue edit` (revise the plan body) | resume, update | after the user approves the body diff |
| `gh issue comment` (revision log / closing ledger) | resume, update, close | same approval |
| `gh issue close` | close | explicit confirmation, separately from the drafts |

**Do not run the mutating verbs headlessly.** A filed issue can be closed but not unfiled, and a closed-and-succeeded plan chain is expensive to untangle; the confirmations are the safety model.

Every body and comment is GitHub-rendered, so the [rules for writing to GitHub](https://github.com/QuantEcon/skills/blob/main/AGENTS.md#writing-to-github) apply — including never putting a closing keyword before an `owner/repo#N` reference, which in a plan citing issues across the estate is the difference between a status note and accidentally closing someone's issue.

## Anchor and sweep

Shared machinery for `read`, `resume`, `update`, and `create`'s session-bootstrap source:

- **Anchor**: the body's own revision stamp — the convention makes the "since when" explicit. Fall back to the issue's last-edit time if the stamp is missing.
- **Sweep**: everything since the anchor, scoped by the plan's own link graph — plans routinely live in one repo while the work spans several. Commits on default branches, PRs opened/merged/closed, issues filed/edited/closed (`gh search issues/prs --updated ">STAMP"`, `git log` where a clone exists).
- **Attribute honestly.** Traces since the anchor include other people's, bots', and parallel sessions' work. An update records what *happened*; it claims as this session's only what this session did.
- **The conversation supplies only what traces cannot**: decisions made, dead ends worth not repeating, things learned, and the resume pointer. Every claim that *can* carry a trace citation (a PR, commit, or issue number) must.

## `read` — look, validate, recommend (writes nothing)

**Read** the body and comment thread (`gh issue view <n> --comments`) and report, in this order: the **revision stamp with its age** first ("stamped 2026-08-20 18:04 AEST — 5 days ago"); the front of the plan (what leads and why); the live-state facts *as of the stamp*; blocks and their gates; the latest revision-log comment — the previous session's handover; and "explicitly not doing" when the user's question touches something the plan already deferred. A closed plan is still readable: its ledger and carry-forward register answer "what happened to X?"; for the live thread, follow the "continuing from #N" chain forward.

**Validate**: the body was true at its stamp; the gap since is unaudited. Sweep it and check the plan's premises — default depth is the front-of-plan items plus anything the sweep contradicts; `--full` checks every claim, worth it after a long gap. Classify each checked claim *holds* (still true), *aged* (true but the numbers moved — give both values), or *inverted* (what the plan believed, what is true, and the trace that shows it). Report body and reality side by side, never blended — a half-verified hybrid presented as "the plan" is worse than either, because nobody stamped it. Validation is not revision: a dead premise goes in the report and the recommendation, and the body changes only through `resume`/`update`, gated — that line is what keeps `read` safe to run casually.

**Recommend**, and stop: what actually leads next; whether the body needs re-stamping first (any inverted premise or material drift → `resume`; everything holds → the plan can be worked as written); or the verb the moment calls for (all items done or carried → `close`; a defect surfaced → file it as its own issue). Name the verb and the reason; running it is the user's move.

## `create` — open a plan

**1. Gather — three sources.** *Backlog triage*: sweep the repo's open issues, PRs and recent activity, and organise the *agreed* work — a planning pass, not an audit (for a whole-tracker review that re-verifies every issue against the code, run [`/qe:audit-issues`](https://github.com/QuantEcon/skills/blob/main/qe/skills/audit-issues/SKILL.md) first and feed its report to `workplan-project`). *Session bootstrap*: the session did work with no plan open — anchor-and-sweep over the session's traces plus the stated goals for next session; the first plan is a handover with no predecessor. *Succession*: the carry-forward register handed over by `close` — the register, never the old body, is the input; add what the closing session surfaced. When the source isn't obvious from how the verb was reached, ask.

**2. Verify the baseline.** Every fact the plan will rest on is measured *now* and stamped: tag positions, coverage counts, open-PR sets, CI state — whatever the work blocks depend on. Each row of the live-state table says what was measured and when, because a future session will trust it without seeing how it was built. What cannot be verified now goes in as an open question, not a fact.

**3. Draft the body** — from the exemplars, a live-state table over dependency-ordered blocks:

- **Title**: match the host repo's existing chain; default `Work plan — <scope>: <what leads>` for a period plan (the QEP will settle one form).
- **Opening line**: where the plan came from — "continuing from #N (closed <date> with its ledger)" for succession, or the triage/session that produced it — plus the convention line: *this body is the single source of truth for the session, revised in place against live state before working it.*
- **Live-state table**: the step-2 baseline, every row stamped.
- **Work blocks, ordered by dependency, not size**, each naming its gate, with the **front of the plan explicit**: what leads next session, and why.
- **Explicitly not doing**: what was considered and deferred, with the reason — the section that stops the next session from re-litigating.
- **No type label** (see the convention).

Present the draft and **wait for approval**.

**4. File it.** Check the one-open-plan invariant first: an existing open period plan is a finding — the right move is usually `update` of that plan, not a second one; create anyway only if the user says the scopes are genuinely disjoint. Then `gh issue create --repo <o>/<r> --title … --body-file …` (no labels). In succession, creation order belongs to `close`.

## `resume` and `update` — the session moments

Same mechanics at opposite ends of the session: sweep since the anchor, revise the body in place, post a revision-log comment — each write gated as tabulated above.

- **`resume` (session start)**: the plan was true when its last session ended; the gap since is unaudited. Run `read`'s validation at working depth, then revise the body — facts re-measured with fresh stamps, the front of the plan re-pointed, dead premises corrected. Comment when something material changed; an inverted premise *always* gets a comment recording what the plan believed, what is true, and how the work changes. Then the session works the plan.
- **`update` (session end, plan continues)**: tick what completed, re-measure the facts the session touched, and set the **resume pointer** — what leads next session, and why. The comment records what landed (with trace citations), what was decided, what inverted, what was deferred and why. Before posting, test the pair against the acceptance test: could a fresh context resume from the issue alone? Anything essential still living only in the conversation isn't written down yet.

`gh issue edit --body` replaces the whole body: fetch the live body immediately before editing and diff against *that*, not what was fetched at session start — another session or a human may have edited in between.

## `close` — plan complete

- Verify every item is done or explicitly carried forward — nothing silently dropped. Items that remain move to the carry-forward register, visibly.
- Draft the **closing ledger** (shipped / decided / carried forward) and the successor, via `create`'s succession source.
- On approval, in this order: create the successor, post the ledger citing it, close the old plan — at every step the open end is findable.
- Only a *period plan* closes. A long-lived tracker gets `read`, `resume` and `update` only; say so rather than offering `close`.

## Gotchas

- **Date rollovers mislead.** The exemplar chain records a "2026-08-19/2026-08-20" revision pair that was actually fourteen hours apart (a Sydney date rolling over) — hence the convention's time-and-timezone stamps.
- **This skill vs [`workplan-project`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-project/SKILL.md)**: phases and sub-issues someone works through over weeks → `workplan-project`; one issue the next session resumes from → `create`. The two compose: a project tracker plus period plans that work through it and reference it (the workspace-lectures pattern: tracker [#14](https://github.com/QuantEcon/workspace-lectures/issues/14), weekly plans alongside).
