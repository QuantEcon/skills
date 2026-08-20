---
name: workplan-update
description: Maintain a work-plan tracking issue across agent sessions — at session start, re-verify the plan's premises against live state and revise the body before working; at session end, record what the session did with a revision-log comment and a resume pointer, or, when the plan is complete, close it with a ledger and hand the carry-forward register to a successor. Updates are built from verifiable traces (commits, PRs, issues) so a fresh session can resume from the issue alone. Use when asked to update a work plan, resume from one, close out a session, record session state, or hand over to the next session. Takes the plan issue's URL or number, or discovers the repo's single open work-plan issue.
---

# workplan-update

Maintains the issue that carries **cross-session state**: the work-plan issue a session resumes from, works through, and hands over to the next session. A session is one agent context window; when it ends, the context is gone, so this skill's one acceptance test governs everything it writes:

> **A fresh agent, given only the issue, can resume the work without the old conversation.**

The `workplan-*` family: [`workplan-project`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-project/SKILL.md) builds a project (tracker + sub-issues) from a report; [`workplan-issue`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md) creates a work-plan issue and owns the convention that defines its shape; this skill maintains one across sessions.

> **Status: merged, no validated run yet.** Shipped in `qe` 0.4.0. First-run validation is tracked in [#3](https://github.com/QuantEcon/skills/issues/3).

Requires `gh`, authenticated. The convention this skill operates — body as single source of truth revised in place, comments as revision logs, ledger-then-succeed, the period-plan/tracker genre split — is stated once, in [`workplan-issue` § The convention](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md#the-convention); what follows assumes it.

## Invocation

```
/qe:workplan-update [resume|update|close] [issue#]
```

Both arguments are optional. With no issue, discovery looks for the repo's open plan (`gh issue list --state open --search "work plan in:title"`, plus `TRACKING:`/`PLAN:` title prefixes): exactly one hit proceeds; several is a finding to surface, not a coin flip; zero means there is no plan yet — that is [`workplan-issue`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md)'s job, offer it. With no verb, ask which moment this is rather than inferring — the cost of running `close` when the user meant `update` is a wrongly closed plan.

## What this skill writes

Everything is drafted locally and shown as a diff against the live body first; each write happens only after the user approves that draft. The close path carries the firmest gate.

| Call | Path | Gate |
|---|---|---|
| `gh issue edit` (revise the plan body) | resume, update | after the user approves the body diff |
| `gh issue comment` (revision log / closing ledger) | resume, update, close | same approval |
| `gh issue close` | close | explicit confirmation, separately from the drafts |

The successor a close needs is created by `workplan-issue`, under its own gate.

**Do not run the close path headlessly.** A closed-and-succeeded plan chain is expensive to untangle; the confirmation is the safety model.

## 1. Anchor and sweep (all paths start here)

- **Anchor**: the body's own revision stamp — the convention makes the "since when" explicit. Fall back to the issue's last-edit time if the stamp is missing.
- **Sweep**: everything since the anchor, scoped by the plan's own link graph — plans routinely live in one repo while the work spans several. Commits on default branches, PRs opened/merged/closed, issues filed/edited/closed (`gh search issues/prs --updated ">STAMP"`, `git log` where a clone exists).
- **Attribute honestly.** Traces since the anchor include other people's, bots', and parallel sessions' work. The update records what *happened*; it claims as this session's only what this session did.
- **The conversation supplies only what traces cannot**: decisions made, dead ends worth not repeating, things learned, and the resume pointer. Every claim that *can* carry a trace citation (a PR, commit, or issue number) must.

## 2. `resume` — session start

The plan was true when its last session ended; the gap since then is unaudited. Before working it:

- Re-verify its premises against live state. Default depth: the front-of-plan items plus anything the sweep contradicts. `--full` re-verifies every claim in the body — use it after a long gap or before a close.
- Revise the body in place: facts re-measured with fresh timestamps, the front of the plan re-pointed, dead premises corrected.
- Post a revision-log comment when something material changed; an inverted premise *always* gets one, recording what the plan believed, what is actually true, and how the work changes.

Then the session works the plan; the skill's job at this moment is done.

## 3. `update` — session end, plan continues

- Revise the body: tick what completed, re-measure the facts the session touched, and set the **resume pointer** — what leads next session, and why it leads.
- Post the session's revision-log comment: what landed (with trace citations), what was decided, what inverted, what was deferred and why.
- Before posting, test the pair against the acceptance test: could a fresh context resume from the issue alone? If anything essential lives only in the conversation, it isn't written down yet.

## 4. `close` — plan complete

- Verify every item is done or explicitly carried forward — nothing silently dropped. If items remain and the user still wants to close, they move to the carry-forward register, visibly.
- Draft the **closing ledger** (shipped / decided / carried forward) and hand the register to [`workplan-issue`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-issue/SKILL.md), whose succession mode drafts the successor ("continuing from #N").
- On approval, in this order: `workplan-issue` creates the successor, then post the closing ledger citing it, then close the old plan. The chain never dangles — at every step the open end is findable.
- Only a *period plan* closes. If the issue is a long-lived tracker (a state register with no end-of-period shape), only `resume` and `update` apply; say so rather than offering `close`.

## Gotchas

- **`gh issue edit --body` replaces the whole body.** Fetch the live body immediately before editing and diff against *that*, not against what was fetched at session start — another session or a human may have edited in between.
- **Date rollovers mislead.** The exemplar chain records a "2026-08-19/2026-08-20" revision pair that was actually fourteen hours apart (a Sydney date rolling over). Stamp revisions with times and timezone, not bare dates, when sessions run close together.
- **New defects become issues, not paragraphs.** A problem the session discovers is filed as its own linked issue (the exemplars file them same-day); the plan cites it. Prose-only findings are how things get lost.
- **Every body and comment is GitHub-rendered**, so the [rules for writing to GitHub](https://github.com/QuantEcon/skills/blob/main/AGENTS.md#writing-to-github) apply — including never putting a closing keyword before an `owner/repo#N` reference, which in a plan that cites issues across the estate is the difference between a status note and accidentally closing someone's issue.
