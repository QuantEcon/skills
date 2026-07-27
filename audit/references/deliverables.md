# Reporting

What an audit hands back. The four-document bundle below is what `/audit:issues` produces; it is a worked example, not a contract every skill in this plugin has to satisfy. A skill should produce what its subject actually needs — a debt audit's output is a filing-ready catalog, a parity audit's is a divergence list, and a small audit may reasonably be a single document. Reach for the bundle where it fits, and don't manufacture a section to fill a slot.

What every audit owes its reader is much smaller, and is in the last section.

## Where it goes

**Never into `QuantEcon/skills`.** This repo holds the procedure; the findings belong with the thing audited. In order of preference:

1. The audited repo's own notes system — `.dev/audits/<date>-<subject>/` or equivalent.
2. The paired `project-*` repo, when the audit serves a program rather than a repo (`project-translation/reports/` for a translation audit).
3. A dedicated `audit-*` repo, per [QEP-3](https://github.com/QuantEcon/qeps/pull/7), once an audit is recurring and its findings are worth publishing.

Confirm the destination before writing, and name it in the report. Private inputs stay in private destinations: a `project-*` repo's contents must not be summarised into a public one.

## The `/audit:issues` bundle

Four documents, which suit a whole-tracker review because it has an argument to make, a long enumeration to carry, and a graph worth drawing separately. Another audit may need two of these, or none.

**`01-<subject>-report.md`** — the argument. Method and evidence base; the snapshot timestamp; portfolio statistics; the findings that change a status, each with its evidence tag; the tiering, tied to the repo's existing plan; policy alignment; and a time-boxed execution order for whoever acts on it.

**`02-<subject>-catalog.md`** — the enumeration. A legend, then a full summary table (item · tier · action · type · priority), then one entry per open item:

> **Bold header line** — the item and its one-line characterisation
> *Status:* what is actually true, with evidence and its tag
> *Recommend:* the proposed action, and what it depends on
> *Links:* related items, in and out of this repo

Close with the verification of the closed set (explicitly thread-complete), and write up anything agreed-but-never-filed as a proposed new item, in a form that could be filed as-is.

**`03-<subject>-links.md`** — the graph. Clusters and their anchor items; a concrete table of missing links worth adding; true orphans and over-dense hubs; and the external cross-link registry (sibling repos, program and meta issues, evidence PRs). This one is the most tracker-specific of the four — an audit whose subject has no interesting link structure should simply not produce it.

**`README.md`** — the index. Headline numbers, what each document is for, and the coverage statement.

Where a later audit does reuse this shape, keeping the names and the entry format identical is worth something: a reader who has read one bundle can read the next, and two audits of the same subject diff mechanically ([doctrine rule 7](doctrine.md#1-what-makes-a-bulk-audit-trustworthy)). That is a reason to converge where the shape fits, not a reason to force it.

## What any audit owes its reader

Short list, and this part is not advisory — each item is what keeps a long report checkable by someone who will not re-run it.

- **A coverage statement.** Exactly what was and was not inspected, per [doctrine §5](doctrine.md#5-coverage-self-audit). In a bundle it belongs in the index; in a single document it is a section. It is the first thing a reader should be able to check and the last thing the audit should write.
- **An evidence tag on every claim** ([doctrine §2](doctrine.md#2-evidence-classes)). An untagged status claim is a defect.
- **Recommendations marked as proposals.** Write them in the imperative for whoever executes ("close, citing PR #204"), but the audit does not execute them.
- **Drafted comment text marked as unsent**, in a fenced block — and subject to the closing-keyword hazard in [quantecon-context.md](quantecon-context.md#the-cross-repo-graph-is-the-point).
- **A date and a named snapshot.** Two audits of the same subject must be distinguishable at a glance, and every number in a report refers to one point in time.
