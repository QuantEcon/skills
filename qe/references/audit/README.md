# The audit skills

Bulk audits of a QuantEcon repository. Where `qe`'s author-facing skills serve one lecture and `/qe:benchmark` evaluates one conversion, this family sweeps a whole portfolio — every issue, every PR, a whole codebase, a whole translated series — and delivers a report. Shipped in the `qe` plugin; until qe 0.7.0 this was the separate `audit` plugin.

## Skills

| Skill | Audits | Status |
|---|---|---|
| [`/qe:audit-issues`](../../skills/audit-issues/SKILL.md) | Every issue, open and closed: status verified against the code, tiered into the repo's plan | runbook landed |
| `/qe:audit-prs` | Every open PR: does it solve a real issue, is it mergeable, what should the review say | candidate |
| `/qe:audit-tech-debt` | A codebase's accumulated debt, with a filing-ready issue catalog | candidate |
| `/qe:audit-translations` | Parity between a source series and a translation (`lecture-python.myst` ↔ `lecture-python.zh-cn`) | candidate |

Only the first is written. The rest are candidates, tracked in [issue #12](https://github.com/QuantEcon/skills/issues/12) — each still needs the evidence a skill here normally carries before anyone writes it. Shipping one first is the point: the shared method gets proven against a real procedure before more are built on top of it.

## What belongs here

Two tests:

1. **Bulk** — it sweeps a portfolio, not an item. Reviewing one PR's technical quality is not an audit; reviewing all of them is.
2. **Read-only** — it observes and reports. No skill here mutates a tracker, a branch, or a file in the audited repo ([doctrine §3](doctrine.md#3-read-only-boundary)).

The read/write line is the one that matters, and it is deliberate: it mirrors the org's own automation split, where the family boundary *is* the permission boundary. Anything that acts on findings — filing the catalog as issues, posting the drafted comments, applying labels — is a separate human-invoked step, which is what makes this family safe to point at any repo and safe to run headlessly. (Consolidation into `qe` softened the old plugin-boundary framing — the enable unit is now the whole plugin — but the read-only rule itself is unchanged and doctrine §3 still enforces it per skill.)

An audit also produces a written report rather than a chat answer, since the point is something a reader can check later. That says nothing about how long it is or how many files it takes — see [deliverables.md](deliverables.md), which describes what `/qe:audit-issues` produces without requiring the next skill to match it.

## Shared references

Skills are thin; the method lives once, shared by the family.

| Document | Owns |
|---|---|
| [doctrine.md](doctrine.md) | Trust rules, evidence classes, read-only boundary, checkpointing, coverage self-audit |
| [quantecon-context.md](quantecon-context.md) | Repo types, label ownership, the cross-repo graph, notes-system discovery, access |
| [deliverables.md](deliverables.md) | What an audit owes its reader, where reports may land, and the `/qe:audit-issues` bundle as a worked example |
| [scripts/audit/](../../scripts/audit/) | Deterministic fetch machinery |

## Running one

```
/qe:audit-issues QuantEcon/action-translation
```

Audits work from a frozen snapshot and checkpoint to disk as they go, so an interrupted run resumes rather than restarting — and every number in the report refers to one point in time.

**Budget tens of minutes, not hours.** The first measured run covered a 230-item tracker in **22 minutes** end to end ([record](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-action-translation-2026-07-28.md)). What scales is the **open issue** count, not the item count: phase 2 verifies the open set at about 10 seconds each — 9 of those 22 minutes for 56 issues — while the remaining phases are largely fixed. So a 1000-item repo with a small open set is cheaper than a 300-item repo with a large one. That is one data point; a repo whose issues need deeper code archaeology will run slower per issue.

Headless runs work the same way:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    plugin_marketplaces: "https://github.com/QuantEcon/skills.git"
    plugins: "qe@quantecon"
    prompt: "/qe:audit-issues QuantEcon/action-translation"
```

## A note on naming

Inside the `qe` namespace the family reads as `/qe:audit-<object>` — `/qe:audit-issues`, `/qe:audit-translations`. The `audit-` stem keeps the family greppable in a flat skill list ([#43](https://github.com/QuantEcon/skills/issues/43)), and each name still reads as a command. (Before consolidation the stem was the plugin: `/audit:issues`.)

`audit` was chosen over `review` for the same reason the family excludes single-item work: `review` is already the per-item word here (the benchmark skill's review mode, and PR review generally), so an audit named `review-prs` would sit one keystroke from reviewing one PR. `audit` also matches QEP-3's `audit-` repo prefix and already connotes observe-and-report, which is the boundary this family enforces.
