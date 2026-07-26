# The report bundle

Every audit in this plugin delivers the same four-document bundle. A shared shape means a reader who has read one audit can read any of them, and a later audit can diff against an earlier one mechanically (doctrine rule 7).

## Where it goes

**Never into `QuantEcon/skills`.** This repo holds the procedure; the findings belong with the thing audited. In order of preference:

1. The audited repo's own notes system — `.dev/audits/<date>-<subject>/` or equivalent.
2. The paired `project-*` repo, when the audit serves a program rather than a repo (`project-translation/reports/` for a translation audit).
3. A dedicated `audit-*` repo, per [QEP-3](https://github.com/QuantEcon/qeps/pull/7), once an audit is recurring and its findings are worth publishing.

Confirm the destination before phase 4 and name it in the report. Private inputs stay in private destinations: a `project-*` repo's contents must not be summarised into a public one.

## The four documents

**`01-<subject>-report.md`** — the argument. Method and evidence base; the snapshot timestamp; portfolio statistics; the findings that change a status, each with its evidence tag; the tiering, tied to the repo's existing plan; policy alignment; and a time-boxed execution order for whoever acts on it.

**`02-<subject>-catalog.md`** — the enumeration. A legend, then a full summary table (item · tier · action · type · priority), then one entry per open item:

> **Bold header line** — the item and its one-line characterisation
> *Status:* what is actually true, with evidence and its tag
> *Recommend:* the proposed action, and what it depends on
> *Links:* related items, in and out of this repo

Close with the verification of the closed set (explicitly thread-complete), and write up anything agreed-but-never-filed as a proposed new item, in a form that could be filed as-is.

**`03-<subject>-links.md`** — the graph. Clusters and their anchor items; a concrete table of missing links worth adding; true orphans and over-dense hubs; and the external cross-link registry (sibling repos, program and meta issues, evidence PRs).

**`README.md`** — the index. Headline numbers, what each document is for, and **the coverage statement**: exactly what was and was not inspected, per [doctrine §5](doctrine.md#5-coverage-self-audit). This is the first thing a reader should be able to check and the last thing the audit should write.

## Rules that apply to all four

- **Tag every claim** with its evidence class ([doctrine §2](doctrine.md#2-evidence-classes)). An untagged status claim is a defect.
- **Recommendations are proposals.** Write them in the imperative for whoever executes ("close, citing PR #204"), but the audit does not execute them.
- **Suggested comment text is a draft, in a fenced block, clearly marked as unsent** — and subject to the closing-keyword hazard in [quantecon-context.md](quantecon-context.md#the-cross-repo-graph-is-the-point).
- **Date the bundle and name the snapshot.** Two audits of the same repo must be distinguishable at a glance, and every number in a bundle refers to one point in time.
