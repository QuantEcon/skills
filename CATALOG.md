# Skill catalog

What this marketplace installs today, filtered to what is **operational**: a skill appears here once it is merged *and* runs to its stated purpose, not merely once its files are on `main`. Listing is not a claim about how far a skill has been validated — the State column answers that for each one, and says so plainly when the answer is "not much". Anything not listed does not exist yet as a usable skill, however firmly it has been discussed. Work in flight lives in the tracking issue for its plugin; ideas nobody has committed to live in [FUTURE-IDEAS.md](FUTURE-IDEAS.md).

Merged-but-not-yet-working scaffolding is deliberately absent. It registers in the slash menu once its plugin is installed, so [docs/using-skills.md](docs/using-skills.md) lists it and says it reports "not yet operational" — but a catalog that advertises skills which do nothing is worth less than one that stays true.

| Plugin | Skills | State | Tracking |
|---|---|---|---|
| **`qe`** — author-facing skills, from drafting a lecture to merging its PR | `/qe:copilot-review` | Operational, and validated from an installed plugin on 2026-08-03: plugin-root path resolution, cross-repo mode, and running from outside a working tree. The style skills (`check-style` and six per-category siblings) are merged as scaffolding and report that they are not yet operational, so they are not listed here until the rule snapshot and deterministic preflight land. | [#3](https://github.com/QuantEcon/skills/issues/3) |
| **`benchmark`** — evaluating accelerated lecture implementations | `/benchmark:review-acceleration` | Operational for workspace runs: rubric v2, a deterministic scoring engine, and two complete worked evaluations as regression baselines. | [#4](https://github.com/QuantEcon/skills/issues/4) |
| **`audit`** — bulk, read-only repository audits | `/audit:issues` | Run once **as a skill** — a 230-item tracker on 2026-07-28, 22 minutes, seven plugin defects found and recorded ([record](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-action-translation-2026-07-28.md)). That validates the method as far as one run goes and no further: its central claim, resumability, is still untested, because the run was never interrupted. Further runs: [#16](https://github.com/QuantEcon/skills/issues/16). | [#12](https://github.com/QuantEcon/skills/issues/12), [#16](https://github.com/QuantEcon/skills/issues/16) |

Installation and setup are in [README.md](README.md); what it is like to run one is in [docs/using-skills.md](docs/using-skills.md).

## Principles

The point of the marketplace is to **share institutional knowledge** — the checks, rubrics and procedures that experienced maintainers already apply by hand — so the same work produces more consistent results wherever it is run, across roughly 245 non-archived repos. Everything below serves that.

- **Few, high-frequency skills** over many niche ones, each validated against actual PR history. The 2026-07-21 analysis of ~630 merged PRs across the four main lecture repos is the evidence base: style was the largest recurring theme by a wide margin, which is why it is the flagship. A skill justified by breadth rather than frequency, as the audit family is, should say so.
- **Report first, fix on request.** Skills produce a structured report and offer fixes; they never silently edit. Safe to run in CI, and authors stay in control.
- **Cited claims; computed scores.** Every finding carries a citation — a rule ID plus `file:line`, or a number plus its source. Skills whose output is a findings list need nothing more. Skills that aggregate judgements into a scored verdict use the evidence-file pattern from the benchmark plugin: judgement recorded as cited answers, every score computed by a deterministic engine, never typed by hand (see [docs/developing-skills.md](docs/developing-skills.md)).
- **Scaffolding is advice, not instruction.** Report shapes, phase divisions, naming forms and directory conventions are described as what an existing skill does, not as contracts a new one has to satisfy. Three plugins is not enough to know which of them generalise, and a rule invented from one worked example mostly succeeds at forcing the next skill into the first one's shape. A skill can be a single `SKILL.md`. Where something genuinely must hold — read-only boundaries, cited claims, a stated coverage of what was and was not checked — say so plainly and give the reason; everything else can converge later, once there is something to generalise from.

Note what the last two have in common: the rules stated firmly are the ones that keep output *checkable by someone who will not re-run it*. That is the test worth applying before writing any new rule down.
