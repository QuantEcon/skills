# Skill catalog

What this marketplace installs today. A skill appears here once it is merged — anything not listed does not exist yet, however firmly it has been discussed. Work in flight lives in the tracking issue for its plugin; ideas nobody has committed to live in [FUTURE-IDEAS.md](FUTURE-IDEAS.md).

| Plugin | Skills | State | Tracking |
|---|---|---|---|
| **`qe`** — author-facing style checks | `/qe:check-style`, plus six per-category siblings: `check-writing`, `check-math`, `check-code`, `check-figures`, `check-jax`, `check-refs` | Scaffolding. The rendered rule snapshot and the deterministic preflight have not landed, and the skills report that they are not yet operational when run. | [#3](https://github.com/QuantEcon/skills/issues/3) |
| **`benchmark`** — evaluating accelerated lecture implementations | `/benchmark:review-acceleration` | Operational for workspace runs: rubric v2, a deterministic scoring engine, and two complete worked evaluations as regression baselines. | [#4](https://github.com/QuantEcon/skills/issues/4) |
| **`audit`** — bulk, read-only repository audits | `/audit:issues` | Runbook landed, and executed once end to end against a real repo — **by hand, never yet as a skill**. Treat its method as unvalidated until the first run under [#16](https://github.com/QuantEcon/skills/issues/16) reports. | [#12](https://github.com/QuantEcon/skills/issues/12), [#16](https://github.com/QuantEcon/skills/issues/16) |

Installation and setup are in [README.md](README.md); what it is like to run one is in [docs/using-skills.md](docs/using-skills.md).

## Principles

The point of the marketplace is to **share institutional knowledge** — the checks, rubrics and procedures that experienced maintainers already apply by hand — so the same work produces more consistent results wherever it is run, across roughly 245 non-archived repos. Everything below serves that.

- **Few, high-frequency skills** over many niche ones, each validated against actual PR history. The 2026-07-21 analysis of ~630 merged PRs across the four main lecture repos is the evidence base: style was the largest recurring theme by a wide margin, which is why it is the flagship. A skill justified by breadth rather than frequency, as the audit family is, should say so.
- **Report first, fix on request.** Skills produce a structured report and offer fixes; they never silently edit. Safe to run in CI, and authors stay in control.
- **Cited claims; computed scores.** Every finding carries a citation — a rule ID plus `file:line`, or a number plus its source. Skills whose output is a findings list need nothing more. Skills that aggregate judgements into a scored verdict use the evidence-file pattern from the benchmark plugin: judgement recorded as cited answers, every score computed by a deterministic engine, never typed by hand (see [docs/developing-skills.md](docs/developing-skills.md)).
- **Scaffolding is advice, not instruction.** Report shapes, phase divisions, naming forms and directory conventions are described as what an existing skill does, not as contracts a new one has to satisfy. Three plugins is not enough to know which of them generalise, and a rule invented from one worked example mostly succeeds at forcing the next skill into the first one's shape. A skill can be a single `SKILL.md`. Where something genuinely must hold — read-only boundaries, cited claims, a stated coverage of what was and was not checked — say so plainly and give the reason; everything else can converge later, once there is something to generalise from.

Note what the last two have in common: the rules stated firmly are the ones that keep output *checkable by someone who will not re-run it*. That is the test worth applying before writing any new rule down.
