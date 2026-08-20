---
name: workplan-issue
description: Create a work-plan tracking issue — triage and organise work into the single GitHub issue that carries state between agent sessions. Takes its work from a backlog triage, from the current session (bootstrapping a first plan from what the session did and intends), or from a closing plan's carry-forward register (opening the successor), organises it into dependency-ordered blocks over a freshly verified live-state baseline, and files the issue only after the user approves the draft. Use when asked to create a work plan, organise work into a plan or tracking issue, set up the next session's plan, or open the successor to a completed plan.
---

# workplan-issue

Creates the artifact the rest of the family revolves around: the **work-plan issue**, the org's cross-session state carrier. Triage and organise work — from a backlog, from the session in progress, or from a closing plan — into one dependency-ordered, live-state-verified issue that a future session can work from without any other context.

The `workplan-*` family: [`workplan-project`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-project/SKILL.md) builds a project (tracker + sub-issues) from a report; this skill creates a single work-plan issue; [`workplan-update`](https://github.com/QuantEcon/skills/blob/main/qe/skills/workplan-update/SKILL.md) maintains one across sessions.

> **Status: merged, no validated run yet.** Shipped in `qe` 0.4.0. First-run validation is tracked in [#3](https://github.com/QuantEcon/skills/issues/3).

Requires `gh`, authenticated.

## The convention

This is observed practice across the org's work-plan issues (exemplars: the [project-translation#37](https://github.com/QuantEcon/project-translation/issues/37) session chain, the [workspace-lectures#48](https://github.com/QuantEcon/workspace-lectures/issues/48) weekly series, [skills#25](https://github.com/QuantEcon/skills/issues/25)). Formalising it as a QEP is planned; until that lands, this section records the practice — and once it lands, this section becomes a pointer. `workplan-update` operates the same convention and links here.

- **The body is the single source of truth for current state, revised in place.** It never accumulates narrative, and it stamps its own revision date ("Revised YYYY-MM-DD").
- **Comments are revision logs**: what changed and why — especially premises that *inverted* rather than merely aged.
- **Claims are verified against live state, never assumed or carried forward.** A plan body silently carrying a dead premise is worse than no plan.
- **Two genres, one lifecycle each.** A *period plan* (a session's or week's work) closes with a ledger and is succeeded; a *long-lived tracker* (a project-duration state register) gets resumed and updated but is never session-closed.
- **Succession never copies.** The successor is built from the carry-forward register — unfinished and deferred items plus what the closing session surfaced — and opens "continuing from #N".
- **One open period plan per repo at a time.** This is what makes "resume the session" — and this family's issue discovery — unambiguous.
- **Plan issues stay untyped** pending the [QEP-2](https://github.com/QuantEcon/qeps/blob/main/qeps/qep-0002-standard-github-labels.md) field report on labelling plan/tracking issues.

## Invocation

```
/qe:workplan-issue [owner/repo]
```

The repo defaults to the one you are standing in. Which of the three sources below applies is usually obvious from how the skill was reached; when it is not, ask.

## What this skill writes

Steps 1–3 are read-only apart from local draft files. The one write:

| Call | Step | Gate |
|---|---|---|
| `gh issue create` | 4 | after the user approves the draft body |

## 1. Gather — three sources of work

- **Backlog triage**: sweep the repo's open issues and PRs and recent activity, and organise the *agreed* work into an ordered plan. This is a planning pass, not an audit — for a whole-tracker review that re-verifies every issue's status against the code, run [`/audit:issues`](https://github.com/QuantEcon/skills/blob/main/audit/skills/issues/SKILL.md) first and feed its report to `workplan-project`; this skill organises work whose validity is already trusted.
- **Session bootstrap**: the session did work with no plan open. Use `workplan-update`'s anchor-and-sweep discipline over the session's traces (commits, PRs, issues touched) plus the stated goals for next session — the first plan is a handover with no predecessor.
- **Succession**: a closing plan's carry-forward register, handed over by `workplan-update`'s close path. The register — not the old body — is the input; add what the closing session surfaced.

## 2. Verify the baseline

Every fact the plan will rest on is measured *now* and stamped (time and timezone, not a bare date): tag positions, coverage counts, open-PR sets, CI state — whatever the work blocks depend on. A future session will trust this table without being able to see how it was built, so each row says what was measured and when. Facts that cannot be verified now go in as open questions, not as facts.

## 3. Draft the body (the shape)

From the exemplars — a live-state table over dependency-ordered blocks:

- **Title**: the org currently has several conventions (`Work plan — <scope>: <what leads>`, `TRACKING: <project>`, week-of datings). Match the host repo's existing chain; default to `Work plan — <scope>: <what leads>` for a period plan. The QEP will settle one form.
- **Opening line**: where this plan came from — "continuing from #N (closed <date> with its ledger)" for succession, or the triage/session that produced it — plus the convention line: *this body is the single source of truth for the session, revised in place against live state before working it.*
- **Live-state table**: the step-2 baseline, `| Fact | Value |`, every row stamped.
- **Work blocks, ordered by dependency, not size** — each block names its gate ("after D1", "blocked on a maintainer decision") and the **front of the plan is explicit**: what leads next session, and why it leads.
- **Explicitly not doing**: what was considered and deferred, with the reason — the section that stops the next session from re-litigating.
- **No type label** (see the convention above).

Every body is GitHub-rendered, so the [rules for writing to GitHub](https://github.com/QuantEcon/skills/blob/main/AGENTS.md#writing-to-github) apply — unbroken paragraphs, no prose in fences, and never a closing keyword before an `owner/repo#N` reference.

Present the draft and **wait for approval**.

## 4. File it (on approval)

- **Check the one-open-plan invariant first**: if the repo already has an open period plan, that is a finding — the right move is usually a `workplan-update` of the existing plan, not a second one. Create anyway only if the user says the scopes are genuinely disjoint.
- `gh issue create --repo <o>/<r> --title … --body-file …` (no labels — see the convention).
- In succession, the creation order belongs to `workplan-update`'s close path: successor first, then the ledger citing it, then the close.

## Gotchas

- **This skill vs `workplan-project`**: needs phases and sub-issues someone will work through over weeks → project. Needs one issue the next session resumes from → this skill. The two compose: a project tracker plus period plans that work through it and reference it (the workspace-lectures pattern: tracker [#14](https://github.com/QuantEcon/workspace-lectures/issues/14), weekly plans alongside).
- **A plan is not a dumping ground.** Work that is real but not agreed goes to its own labelled issue, and the plan links it or leaves it out; the "explicitly not doing" section exists so deferrals are decisions, not omissions.
- **Don't seed the body with unverified claims to save time.** The whole value of the artifact is that a future session can trust it blind; one unverified "fact" poisons that.
