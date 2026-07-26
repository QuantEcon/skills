# audit

Bulk audits of a QuantEcon repository. Where `qe` serves an author working on one lecture and `benchmark` evaluates one conversion, these skills sweep a whole portfolio — every issue, every PR, a whole codebase, a whole translated series — and deliver a report.

## Skills

| Skill | Audits | Status |
|---|---|---|
| [`/audit:issues`](skills/issues/SKILL.md) | Every issue, open and closed: status verified against the code, tiered into the repo's plan | runbook landed |
| `/audit:prs` | Every open PR: does it solve a real issue, is it mergeable, what should the review say | planned |
| `/audit:tech-debt` | A codebase's accumulated debt, with a filing-ready issue catalog | planned |
| `/audit:translations` | Parity between a source series and a translation (`lecture-python.myst` ↔ `lecture-python.zh-cn`) | planned |

Planned skills are tracked in [CATALOG.md](https://github.com/QuantEcon/skills/blob/main/CATALOG.md); this plugin ships with the first one so the shared doctrine is proven against a real procedure before three more are written on top of it.

## What belongs here

Three tests, all of which must pass:

1. **Bulk** — it sweeps a portfolio, not an item. Reviewing one PR's technical quality is not an audit; reviewing all of them is.
2. **Read-only** — it observes and reports. No skill here mutates a tracker, a branch, or a file in the audited repo ([doctrine §3](references/doctrine.md#3-read-only-boundary)).
3. **Report bundle** — the output is the four-document bundle in [deliverables.md](references/deliverables.md), not a chat answer.

The read/write line is deliberate and mirrors the org's own automation split, where the family boundary *is* the permission boundary. Anything that acts on findings — filing the catalog as issues, posting the drafted comments, applying labels — is a separate human-invoked step, which is what makes this family safe to point at any repo and safe to run headlessly.

## Shared references

Skills are thin; the method lives once at plugin level.

| Document | Owns |
|---|---|
| [references/doctrine.md](references/doctrine.md) | Trust rules, evidence classes, read-only boundary, phases, coverage self-audit |
| [references/quantecon-context.md](references/quantecon-context.md) | Repo types, label ownership, the cross-repo graph, notes-system discovery, access |
| [references/deliverables.md](references/deliverables.md) | The report bundle contract and where bundles are allowed to land |
| [scripts/](scripts/) | Deterministic phase-1 machinery |

## Running one

```
/audit:issues QuantEcon/action-translation
```

Audits are long. They work from a frozen snapshot and checkpoint each phase to disk, so a run that loses its session resumes at the last completed phase rather than restarting — and every number in the report refers to one point in time. Expect hours, not minutes, on a repo with a hundred items.

Headless runs work the same way:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    plugin_marketplaces: "https://github.com/QuantEcon/skills.git"
    plugins: "audit@quantecon"
    prompt: "/audit:issues QuantEcon/action-translation"
```

## A note on naming

The repo's convention is verb-first skill names, and these are nouns. The verb is the plugin: `/audit:issues` and `/audit:translations` read as commands at the point of use, which is where the convention's purpose lies, and `audit-issues` inside an `audit` plugin would stutter at every invocation. The subject-noun names also keep the four skills parallel, which matters more here than in `qe` — the family is defined by a shared method applied to different subjects.
