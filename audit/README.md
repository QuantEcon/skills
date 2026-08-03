# audit

Bulk audits of a QuantEcon repository. Where `qe` serves an author working on one lecture and `benchmark` evaluates one conversion, these skills sweep a whole portfolio — every issue, every PR, a whole codebase, a whole translated series — and deliver a report.

## Skills

| Skill | Audits | Status |
|---|---|---|
| [`/audit:issues`](skills/issues/SKILL.md) | Every issue, open and closed: status verified against the code, tiered into the repo's plan | runbook landed |
| `/audit:prs` | Every open PR: does it solve a real issue, is it mergeable, what should the review say | candidate |
| `/audit:tech-debt` | A codebase's accumulated debt, with a filing-ready issue catalog | candidate |
| `/audit:translations` | Parity between a source series and a translation (`lecture-python.myst` ↔ `lecture-python.zh-cn`) | candidate |

Only the first is written. The rest are candidates, tracked in [issue #12](https://github.com/QuantEcon/skills/issues/12) — each still needs the evidence a skill here normally carries before anyone writes it. Shipping one first is the point: the shared method gets proven against a real procedure before more are built on top of it.

## What belongs here

Two tests:

1. **Bulk** — it sweeps a portfolio, not an item. Reviewing one PR's technical quality is not an audit; reviewing all of them is.
2. **Read-only** — it observes and reports. No skill here mutates a tracker, a branch, or a file in the audited repo ([doctrine §3](references/doctrine.md#3-read-only-boundary)).

The read/write line is the one that matters, and it is deliberate: it mirrors the org's own automation split, where the family boundary *is* the permission boundary. Anything that acts on findings — filing the catalog as issues, posting the drafted comments, applying labels — is a separate human-invoked step, which is what makes this family safe to point at any repo and safe to run headlessly.

An audit also produces a written report rather than a chat answer, since the point is something a reader can check later. That says nothing about how long it is or how many files it takes — see [deliverables.md](references/deliverables.md), which describes what `/audit:issues` produces without requiring the next skill to match it.

## Shared references

Skills are thin; the method lives once at plugin level.

| Document | Owns |
|---|---|
| [references/doctrine.md](references/doctrine.md) | Trust rules, evidence classes, read-only boundary, checkpointing, coverage self-audit |
| [references/quantecon-context.md](references/quantecon-context.md) | Repo types, label ownership, the cross-repo graph, notes-system discovery, access |
| [references/deliverables.md](references/deliverables.md) | What an audit owes its reader, where reports may land, and the `/audit:issues` bundle as a worked example |
| [scripts/](scripts/) | Deterministic fetch machinery |

## Running one

```
/audit:issues QuantEcon/action-translation
```

Audits work from a frozen snapshot and checkpoint to disk as they go, so an interrupted run resumes rather than restarting — and every number in the report refers to one point in time.

**Budget tens of minutes, not hours.** The first measured run covered a 230-item tracker in **22 minutes** end to end ([record](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-action-translation-2026-07-28.md)). What scales is the **open issue** count, not the item count: phase 2 verifies the open set at about 10 seconds each — 9 of those 22 minutes for 56 issues — while the remaining phases are largely fixed. So a 1000-item repo with a small open set is cheaper than a 300-item repo with a large one. That is one data point; a repo whose issues need deeper code archaeology will run slower per issue.

Headless runs work the same way:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    plugin_marketplaces: "https://github.com/QuantEcon/skills.git"
    plugins: "audit@quantecon"
    prompt: "/audit:issues QuantEcon/action-translation"
```

## A note on naming

Skill names here are objects because the plugin is the verb: `/audit:issues`, `/audit:translations`. Both read as commands, which is the part that matters, and `/audit:audit-issues` would stutter at every invocation.

`audit` was chosen over `review` for the same reason the family excludes single-item work: `review` is already the per-item word here (`/benchmark:review-acceleration`, and PR review generally), so a `/review:prs` that sweeps every open PR would sit one keystroke from reviewing one. `audit` also matches QEP-3's `audit-` repo prefix and already connotes observe-and-report, which is the boundary this plugin enforces.
