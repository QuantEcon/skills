# AGENTS.md

Guidance for AI coding agents and human contributors working in `QuantEcon/skills`. This is the canonical instructions file; tool-specific files point here — Claude Code reads [CLAUDE.md](CLAUDE.md), which imports it.

## What this repository is

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) holding QuantEcon's shared agent skills and the deterministic scripts they drive. The goal is to share institutional knowledge — the checks, rubrics and procedures experienced maintainers already apply by hand — so the same work produces consistent results wherever it runs. Orientation is in [README.md](README.md); what has actually shipped is in [CATALOG.md](CATALOG.md); work in flight is in the per-plugin tracking issues.

**The repo is early, and its conventions are deliberately loose.** Where a doc describes a report shape, a phase division, a naming form or a directory layout, read it as what an existing skill does rather than as a contract a new one must satisfy — see [CATALOG.md § Principles](CATALOG.md#principles). The few things that genuinely must hold are stated plainly, with their reasons, and they are all about keeping a skill's output checkable by someone who will not re-run it.

## Single source of truth

The governing principle for everything here — [@jstac](https://github.com/jstac), by email, July 2026:

> For example, skills point to existing documentation in the manual wherever possible, instead of repeating what the manual says.

Content lives in exactly one place; everywhere else links to it. Restated copies drift, and a drifted copy is worse than no copy — a reader who finds two versions cannot tell which is current, and neither can an agent.

What this means in practice:

- **Skills point outward.** When a skill needs a rule, a convention, or a procedure that already exists in the [QuantEcon manual](https://manual.quantecon.org) or in `QuantEcon/style-guide`, it cites and links to it. A `SKILL.md` carries only what the skill itself adds: the procedure it runs, the judgement it applies, the output it produces.
- **Rule text is authored upstream only.** `qe/references/rules/` is a *rendered consumer* of `QuantEcon/style-guide`, kept aligned by a render target and a CI drift check — never hand-edited here. See [qe/references/rules/README.md](qe/references/rules/README.md).
- **Numbers drift fastest** — weights, thresholds, verdict bands, versions. The rubric's weights are stated in [`benchmark/references/EVALUATION_FRAMEWORK.md`](benchmark/references/EVALUATION_FRAMEWORK.md) and implemented once in `benchmark/scripts/scoring/rubric.py`; anywhere else they come up, quote with a pointer rather than re-tabulating.
- **Every topic has an owning doc** (see the map below). Before adding a section, work out which file owns the topic, put it there, and link from wherever else it comes up.
- **Across boundaries, link — don't copy.** An installed plugin ships only its own directory, so a reference to a repo-level file or another plugin is an absolute GitHub URL, never a duplicated paragraph ([developing-skills § Conventions](docs/developing-skills.md#conventions)).
- **The one deliberate exception**: a `SKILL.md` frontmatter `description` must stand alone, because it is what natural-language invocation matches against. Restate what the skill does in that one sentence; the details stay behind the link.

Before adding a paragraph, check whether it already exists. If it does, link to it. If it already exists twice, collapsing the two into one plus a pointer is a fix, not scope creep.

## Where things are documented

| Topic | Canonical location |
|---|---|
| What the marketplace is, installation (local, lecture repos, CI) | [README.md](README.md) |
| Using the skills: setup, invocation, what to expect | [docs/using-skills.md](docs/using-skills.md) |
| Contributing: layout, conventions, dev loop, local testing, versioning, PR flow | [docs/developing-skills.md](docs/developing-skills.md) |
| Running an evaluation by hand, end to end | [docs/tutorial-run-an-evaluation.md](docs/tutorial-run-an-evaluation.md) |
| The benchmark skill: modes, report format, manual pipeline | [benchmark/README.md](benchmark/README.md) |
| Rubric: dimensions, weights, anchors, verdict bands | [benchmark/references/EVALUATION_FRAMEWORK.md](benchmark/references/EVALUATION_FRAMEWORK.md) |
| Style rule text and schema | `QuantEcon/style-guide` (upstream — never authored in this repo) |
| What has shipped, and the principles behind it | [CATALOG.md](CATALOG.md) |
| Parked ideas, not committed to | [FUTURE-IDEAS.md](FUTURE-IDEAS.md) |
| Work in flight, per plugin | issues [#3](https://github.com/QuantEcon/skills/issues/3) (`qe`), [#4](https://github.com/QuantEcon/skills/issues/4) (`benchmark`), [#12](https://github.com/QuantEcon/skills/issues/12) (`audit`) |

## Working in this repo

- **Validate before committing**: `python scripts/validate.py`. A malformed manifest breaks installation silently in every consuming repo, so CI runs the same check.
- **Test from a real consuming project**, not from inside this repo — path-resolution bugs only surface when a plugin runs from an install location. Both tiers are in [developing-skills § Testing locally](docs/developing-skills.md#testing-locally).
- **The product principles** — report first, fix on request; deterministic before LLM; cited claims and computed scores; scaffolding as advice rather than instruction — are stated once in [CATALOG.md § Principles](CATALOG.md#principles) and elaborated in [developing-skills § Conventions](docs/developing-skills.md#conventions). Follow them; don't restate them in new files.
- **A new skill starts as an issue, not a doc entry.** CATALOG.md lists what has merged, so it stays true; the plan for something unbuilt belongs in its plugin's tracking issue, where it can change without anyone mistaking it for a description of the repo.
- **Commit subjects** name the area, then the change: `Docs: hands-on evaluation tutorial…`, `Rubric v2: enforced couplings…`. The repo squash-merges, so stacked branches need `git rebase --onto origin/main <old-base>` once the base PR lands.
- **`NEXT-SESSION.md` is scratch**: deliberately uncommitted working notes. Don't commit it and don't cite it as documentation.

## Writing to GitHub

Issue bodies, PR descriptions, and comments render differently from committed Markdown — write for the renderer:

- **Don't hard-wrap paragraphs.** GitHub turns a single newline into a line break, so source wrapped at 80 characters renders as ragged mid-sentence breaks. One unbroken line per paragraph, blank line between paragraphs. (Committed `.md` files are the opposite case, where wrapping is fine.)
- **Don't put prose in fenced code blocks.** A fence renders as a fixed-width scrolling box that crops the readable width. Use tables and lists for explanation; reserve fences for code and commands meant to be copied.
- **Don't precede a cross-repo reference with a closing keyword.** `Fixes QuantEcon/style-guide#6` auto-closes that upstream issue when the commit lands on `main`. Write `See …`, `Mirrors the change in …`, or `Ports the fix from …` instead.
