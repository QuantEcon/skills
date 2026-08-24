---
name: workplan
description: Create, read, resume, update, or close the work-plan tracking issue — the single GitHub issue that carries state between agent sessions. One skill for the artifact's whole lifecycle - create a plan (from a backlog triage, the current session, or a closing plan's carry-forward register), read one and validate it against live state with recommended next steps (read-only), resume at session start (re-verify premises and revise the body before working), update at session end (revision-log comment and resume pointer), or close a completed plan with a ledger and a successor. Use when asked to create a work plan, show or check the plan, see what's on it or what's next, resume from a plan, record session state, or close out and hand over to the next session. All writes are drafted and gated on approval; reading writes nothing. Takes a verb and optionally the plan issue's number or URL, or discovers the repo's single open work-plan issue.
---

# workplan

One skill for the whole lifecycle of the **work-plan issue** — the org's cross-session state carrier: the single GitHub issue a session resumes from, works through, and hands over to the next session. A session is one agent context window; when it ends, the context is gone, so one acceptance test governs everything this skill writes:

> **A fresh agent, given only the issue, can resume the work without the old conversation.**

The `workplan-*` family is two skills: this one carries the plan through `create` → `read` → `resume` → `update` → `close`-and-succeed; [`workplan-project`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-project/SKILL.md) builds a **project** (tracker + sub-issues, the phased-package shape) from an audit or review report.

> **Status: merged, no validated run yet.** The lifecycle shipped as separate skills (`workplan-issue`, `workplan-update`) in `qe` 0.4.0 and was consolidated here — gaining the `read` verb ([#50](https://github.com/QuantEcon/skills/issues/50)) — in 0.5.0. First-run validation is tracked in [#3](https://github.com/QuantEcon/skills/issues/3).

Requires `gh`, authenticated (`read` uses it for reading only).

## The convention

This is observed practice across the org's work-plan issues (exemplars: the [project-translation#37](https://github.com/QuantEcon/project-translation/issues/37) session chain, the [workspace-lectures#48](https://github.com/QuantEcon/workspace-lectures/issues/48) weekly series, [skills#25](https://github.com/QuantEcon/skills/issues/25)). Formalising it as a QEP is planned; until that lands, this section records the practice — and once it lands, this section becomes a pointer. Every verb below operates it.

- **The body is the single source of truth for current state, revised in place.** It never accumulates narrative, and it stamps its own revision — with time and timezone, not a bare date, when sessions run close together (see the date-rollover gotcha below).
- **Comments are revision logs**: what changed and why — especially premises that *inverted* rather than merely aged.
- **Claims are verified against live state, never assumed or carried forward.** A plan body silently carrying a dead premise is worse than no plan.
- **Two genres, one lifecycle each.** A *period plan* (a session's or week's work) closes with a ledger and is succeeded; a *long-lived tracker* (a project-duration state register) gets resumed and updated but is never session-closed.
- **Succession never copies.** The successor is built from the carry-forward register — unfinished and deferred items plus what the closing session surfaced — and opens "continuing from #N".
- **One open period plan per repo at a time.** This is what makes "resume the session" — and this skill's issue discovery — unambiguous.
- **Plan issues stay untyped** pending the [QEP-2](https://github.com/QuantEcon/qeps/blob/main/qeps/qep-0002-standard-github-labels.md) field report on labelling plan/tracking issues.

## Invocation

```
/qe:workplan [create [owner/repo] | read [--full] | resume [--full] | update | close] [issue#]
```

Both arguments are optional. With no issue, discovery looks for the repo's open plan (`gh issue list --state open --search "work plan in:title"`, plus `TRACKING:`/`PLAN:` title prefixes): exactly one hit proceeds; several is a finding to surface, not a coin flip; zero means there is no plan yet — that is `create`'s job, offer it. With no verb: if the user only wants to *look* at the plan — status, what's next, where things were left — that is `read`; otherwise ask which moment this is rather than inferring — the cost of running `close` when the user meant `update` is a wrongly closed plan.

## What this skill writes

`read` writes nothing — no issue edits, no comments, no drafts to approve. Every other verb drafts locally first, shows the draft (as a diff against the live body where a body is being revised), and writes only after the user approves it. The close path carries the firmest gate.

| Call | Verb | Gate |
|---|---|---|
| — nothing | read | — |
| `gh issue create` | create; close (the successor) | after the user approves the draft body |
| `gh issue edit` (revise the plan body) | resume, update | after the user approves the body diff |
| `gh issue comment` (revision log / closing ledger) | resume, update, close | same approval |
| `gh issue close` | close | explicit confirmation, separately from the drafts |

**Do not run the mutating verbs headlessly.** A filed issue can be closed but not unfiled, and a closed-and-succeeded plan chain is expensive to untangle; the confirmations are the safety model.

## Anchor and sweep

Shared machinery for `read`, `resume`, `update`, and `create`'s session-bootstrap source:

- **Anchor**: the body's own revision stamp — the convention makes the "since when" explicit. Fall back to the issue's last-edit time if the stamp is missing.
- **Sweep**: everything since the anchor, scoped by the plan's own link graph — plans routinely live in one repo while the work spans several. Commits on default branches, PRs opened/merged/closed, issues filed/edited/closed (`gh search issues/prs --updated ">STAMP"`, `git log` where a clone exists).
- **Attribute honestly.** Traces since the anchor include other people's, bots', and parallel sessions' work. An update records what *happened*; it claims as this session's only what this session did.
- **The conversation supplies only what traces cannot**: decisions made, dead ends worth not repeating, things learned, and the resume pointer. Every claim that *can* carry a trace citation (a PR, commit, or issue number) must.

## `read` — look, validate, recommend (writes nothing)

The front door: "what's on the plan?", "where did we leave off?", "what should I do next?". Three steps, all read-only.

**Read** the body and comment thread (`gh issue view <n> --comments`) and report, in this order: the **revision stamp with its age** first ("stamped 2026-08-20 18:04 AEST — 5 days ago" — the plan's warranty date); the front of the plan (what leads and why); the live-state facts *as of the stamp*; blocks and their gates; the latest revision-log comment (the previous session's handover); and the "explicitly not doing" section when the user's question touches something the plan already deferred.

**Validate**: the body was true at its stamp; the gap since is unaudited. Sweep it (see above) and check the plan's premises — default depth is the front-of-plan items plus anything the sweep contradicts; `--full` checks every claim, worth it after a long gap. Classify each checked claim: *holds* (still true), *aged* (true but the numbers moved — say both values), or *inverted* (what the plan believed, what is actually true, and the trace that shows it). Report body and reality **side by side, never blended** — a half-verified hybrid presented as "the plan" is worse than either, because nobody stamped it.

**Recommend**, and stop: what actually leads next; whether the body needs re-stamping first (any inverted premise or material drift → recommend `resume`, with `--full` after a long gap; everything holds → say the plan can be worked as written); or which other verb the moment calls for (all items done or carried → `close`; a defect surfaced by the sweep → file it as its own issue). The recommendation names the verb and the reason; running it is the user's move.

## `create` — open a plan

Steps 1–3 are read-only apart from local draft files; the one write is `gh issue create`, after approval.

**1. Gather — three sources of work.** *Backlog triage*: sweep the repo's open issues and PRs and recent activity, and organise the *agreed* work into an ordered plan — a planning pass, not an audit (for a whole-tracker review that re-verifies every issue's status against the code, run [`/audit:issues`](https://github.com/QuantEcon/skills/blob/main/audit/skills/issues/SKILL.md) first and feed its report to `workplan-project`). *Session bootstrap*: the session did work with no plan open — apply the anchor-and-sweep discipline over the session's traces plus the stated goals for next session; the first plan is a handover with no predecessor. *Succession*: a closing plan's carry-forward register, handed over by the `close` verb — the register, never the old body, is the input; add what the closing session surfaced. Which source applies is usually obvious from how the verb was reached; when it is not, ask.

**2. Verify the baseline.** Every fact the plan will rest on is measured *now* and stamped (time and timezone): tag positions, coverage counts, open-PR sets, CI state — whatever the work blocks depend on. A future session will trust this table without seeing how it was built, so each row says what was measured and when. Facts that cannot be verified now go in as open questions, not as facts.

**3. Draft the body.** From the exemplars — a live-state table over dependency-ordered blocks: a **title** matching the host repo's existing chain (default `Work plan — <scope>: <what leads>` for a period plan; the QEP will settle one form); an **opening line** saying where the plan came from ("continuing from #N (closed <date> with its ledger)" for succession, or the triage/session that produced it) plus the convention line — *this body is the single source of truth for the session, revised in place against live state before working it*; the **live-state table** from step 2, every row stamped; **work blocks ordered by dependency, not size**, each naming its gate, with the **front of the plan explicit** — what leads next session and why; and **"explicitly not doing"** — what was considered and deferred, with the reason, so the next session doesn't re-litigate. No type label (see the convention). Present the draft and **wait for approval**.

**4. File it.** Check the one-open-plan invariant first: if the repo already has an open period plan, that is a finding — the right move is usually `update` of the existing plan, not a second one; create anyway only if the user says the scopes are genuinely disjoint. Then `gh issue create --repo <o>/<r> --title … --body-file …` (no labels). In succession, the creation order belongs to `close` (below).

## `resume` — session start

The plan was true when its last session ended; the gap since then is unaudited. Before working it:

- Run `read`'s validation at working depth: re-verify the plan's premises against live state — the front-of-plan items plus anything the sweep contradicts; `--full` re-verifies every claim in the body, worth it after a long gap or before a close.
- Revise the body in place: facts re-measured with fresh timestamps, the front of the plan re-pointed, dead premises corrected.
- Post a revision-log comment when something material changed; an inverted premise *always* gets one, recording what the plan believed, what is actually true, and how the work changes.

Then the session works the plan; the skill's job at this moment is done.

## `update` — session end, plan continues

- Revise the body: tick what completed, re-measure the facts the session touched, and set the **resume pointer** — what leads next session, and why it leads.
- Post the session's revision-log comment: what landed (with trace citations), what was decided, what inverted, what was deferred and why.
- Before posting, test the pair against the acceptance test: could a fresh context resume from the issue alone? If anything essential lives only in the conversation, it isn't written down yet.

## `close` — plan complete

- Verify every item is done or explicitly carried forward — nothing silently dropped. If items remain and the user still wants to close, they move to the carry-forward register, visibly.
- Draft the **closing ledger** (shipped / decided / carried forward) and draft the successor via `create`'s succession source — built from the register, opening "continuing from #N".
- On approval, in this order: create the successor, then post the closing ledger citing it, then close the old plan. The chain never dangles — at every step the open end is findable.
- Only a *period plan* closes. If the issue is a long-lived tracker (a state register with no end-of-period shape), only `read`, `resume` and `update` apply; say so rather than offering `close`.

## Gotchas

- **`read`'s validation is not revision.** Finding a dead premise does not license fixing it — the finding goes in the report and the recommendation, and the body changes only through `resume`/`update`, gated. This is the line that keeps `read` safe to run casually.
- **`gh issue edit --body` replaces the whole body.** Fetch the live body immediately before editing and diff against *that*, not against what was fetched at session start — another session or a human may have edited in between.
- **Date rollovers mislead.** The exemplar chain records a "2026-08-19/2026-08-20" revision pair that was actually fourteen hours apart (a Sydney date rolling over). Stamp revisions with times and timezone, not bare dates, when sessions run close together.
- **New defects become issues, not paragraphs.** A problem a session discovers is filed as its own linked issue (the exemplars file them same-day); the plan cites it. Prose-only findings are how things get lost.
- **A plan is not a dumping ground.** Work that is real but not agreed goes to its own labelled issue, and the plan links it or leaves it out; the "explicitly not doing" section exists so deferrals are decisions, not omissions.
- **Don't seed the body with unverified claims to save time.** The whole value of the artifact is that a future session can trust it blind; one unverified "fact" poisons that.
- **This skill vs `workplan-project`**: needs phases and sub-issues someone will work through over weeks → [`workplan-project`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-project/SKILL.md). Needs one issue the next session resumes from → `create`. The two compose: a project tracker plus period plans that work through it and reference it (the workspace-lectures pattern: tracker [#14](https://github.com/QuantEcon/workspace-lectures/issues/14), weekly plans alongside).
- **A closed plan is still readable.** Its closing ledger and carry-forward register answer "what happened to X?"; for the live thread, follow the "continuing from #N" chain forward to the open successor.
- **Every body and comment is GitHub-rendered**, so the [rules for writing to GitHub](https://github.com/QuantEcon/skills/blob/main/AGENTS.md#writing-to-github) apply — including never putting a closing keyword before an `owner/repo#N` reference, which in a plan that cites issues across the estate is the difference between a status note and accidentally closing someone's issue.
