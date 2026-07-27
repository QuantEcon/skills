# Developing skills

For contributors adding or modifying plugins in this repo. (Using them: [using-skills.md](using-skills.md).)

## Repo layout

```
.claude-plugin/marketplace.json   # the catalogue — every plugin registers here
scripts/validate.py               # manifest + frontmatter validation (CI runs this)
docs/                             # these guides
<plugin>/                         # one directory per plugin
  .claude-plugin/plugin.json      # name, description, version
  README.md                       # the plugin's user guide
  skills/<skill-name>/SKILL.md    # one directory per skill
  scripts/                        # deterministic scripts the skills drive
  references/                     # rule/rubric content the skills read
```

**Only `SKILL.md` is required.** A skill that is purely a procedure — nothing deterministic to run, no long reference material to point at — is one file in one directory, and should stay that way. `scripts/` appears when there is something mechanical worth doing in code; `references/` when the skill needs more context than belongs in its body. Adding either before you need it just makes the skill harder to read.

The three live plugins show some of the range: `qe` (umbrella skill plus thin per-category sub-skills, sharing plugin-level rules and scripts), `benchmark` (one skill driving a deterministic engine, with worked examples as its regression baseline), and `audit` (sibling procedures sharing a method document). None of these is the house style — they are what three problems happened to need.

## Conventions

Guidance rather than gates. The repo is early, and most of what follows generalises from one or two worked examples; where something is genuinely load-bearing it says so and gives the reason. Departing from the rest is fine when you have a reason — and worth mentioning in the PR, since a second example is how any of this eventually becomes a real convention ([CATALOG.md § Principles](../CATALOG.md#principles)).

- **Invocations read as commands** — the whole `/plugin:skill` string, not the skill name alone. `/qe:check-style` puts the verb in the skill because `qe` names a domain; `/audit:issues` puts it in the plugin and leaves the skill as the object. Both read as imperatives, which is the only part that matters. There is no rule yet about which to prefer — three plugins is too few to know, so pick what reads best and let a convention emerge from use.
- **Description quality matters**: the SKILL.md frontmatter `description` is what natural-language invocation matches against. State what the skill does, what it measures, and when to use it. `validate.py` rejects descriptions too short to trigger reliably.
- **Report first, fix on request** (load-bearing) — skills never silently edit; anything `build_risk` or output-changing (RNG streams) is presented, never auto-applied.
- **Deterministic before LLM** (load-bearing, and the reason is that a reader has to be able to check a skill's output without re-running it): put what is mechanical in `scripts/` (checkable, testable, zero-false-positive bar); reserve the skill's judgement for what genuinely needs it. The discipline scales with what the skill outputs:
  1. *Every skill*: claims carry citations — rule ID + `file:line`, or a number + its source. A findings list needs nothing more; don't add ceremony to simple skills.
  2. *Skills that judge*: record judgement as discrete answers (true/false per criterion, each cited), not free prose — so it's checkable.
  3. *Skills that score*: when multiple judgements aggregate into a verdict with stakes, use the benchmark plugin's evidence-file pattern — judgement lives only in an evidence file, a deterministic engine computes every score, and no score is ever typed by hand. Aggregation is where hand-waving hides; the engine eliminates it.
- **Don't duplicate content across docs** — one canonical location, pointers elsewhere. Rule text, weights, and thresholds especially: restated copies drift.
- **Self-contained plugins** (load-bearing — this one is a hard constraint of how plugins install, not a preference): an installed plugin ships only its own directory. No relative links or paths that escape the plugin root; use absolute GitHub URLs for repo-level files, and anchor runtime paths for the installed context (issue #4 tracks the `${CLAUDE_PLUGIN_ROOT}` pattern).

## Development loop

```bash
# validate everything the marketplace serves
python scripts/validate.py
```

`validate.py` checks: every catalogue entry resolves to a real directory; `plugin.json` agrees with `marketplace.json` on name/version/description; every SKILL.md has frontmatter whose `name` matches its directory. Negative-test your changes (break something on purpose; the validator must fail loudly) — a malformed manifest breaks installation silently in every consuming repo.

## Testing locally

Two tiers, fastest first. Either way, **test from a real consuming project** (a lecture repo checkout), not from inside this repo — the whole class of path-resolution bugs (`${CLAUDE_PLUGIN_ROOT}`, workspace-vs-plugin working directories) only surfaces when the plugin runs read-only from an install location while the working directory is somewhere else.

**Tier 1 — skill iteration, no install.** Load one plugin directly into a session:

```bash
claude --plugin-dir /path/to/skills/<plugin>    # e.g. .../skills/benchmark
```

Nothing is installed and no marketplace state is touched. Best while editing SKILL.md or scripts; restart the session to pick up changes.

**Tier 2 — full install simulation, before merging to `main`.** Add your checkout as a local-path marketplace so you exercise exactly what users get (marketplace metadata, install, versioning, plugin-root resolution). In a Claude Code session in the consuming project:

```
/plugin marketplace add /path/to/your/skills-checkout
/plugin install benchmark@quantecon
```

Two things to know:

- **The marketplace serves whatever your checkout has checked out.** To test a PR branch, leave the working tree on that branch for the duration of the test.
- **Local and GitHub sources share the marketplace name** (`quantecon`, from `marketplace.json`) and cannot coexist — if the production marketplace is already added, `/plugin marketplace remove quantecon` first.

**Switching back to production** once the PR has merged:

```
/plugin marketplace remove quantecon
/plugin marketplace add QuantEcon/skills
/plugin install benchmark@quantecon
```

Confirm with `/plugin marketplace list` (the source should read `QuantEcon/skills`, not your local path) and `/plugin list` (the version should match the merged `plugin.json`). Routine setup and updating for end users is covered in [using-skills.md](using-skills.md).

## The documentation site

These guides, the plugin guides, and the shared reference material are published to [quantecon.github.io/skills](https://quantecon.github.io/skills) by [`.github/workflows/docs.yml`](../.github/workflows/docs.yml) on every push to `main`. Preview it before you push:

```bash
npm install -g mystmd@1.10.1   # same version CI pins in docs.yml
myst start                     # live-reloading preview
```

Two things follow from how it is wired. **Pages are rendered from the files where they already live** — [`myst.yml`](../myst.yml) points at `benchmark/README.md` and `audit/references/*.md` in place, never a copy — so editing a plugin's docs updates the site, and no plugin loses documentation it needs to ship with it. And **the sources have to stay readable on GitHub**, since the repo view is the other half of the audience: prefer plain Markdown, and keep relative links relative, because CI checks that every one of them resolves.

## Versioning and releases

Bump the version in **both** `plugin.json` and the plugin's `marketplace.json` entry — the validator enforces they match. Scaffolding → first usable content is a minor bump (the benchmark plugin's evaluation-system landing was 0.1.0 → 0.2.0).

## PR flow

- Branch, PR, CI must be green. This repo **squash-merges** — stacked branches need `git rebase --onto origin/main <old-base>` after the base PR merges (already-upstream commits drop automatically).
- External contributions land with the contributor as git author (`--author`, GitHub noreply address unless they prefer otherwise) and integration fixes as separate commits — see PR #5 for the pattern.
- [CATALOG.md](../CATALOG.md) lists what has merged and nothing else, so a PR that adds a skill updates it and a PR that plans one does not. Work in flight belongs in the plugin's tracking issue ([#3](https://github.com/QuantEcon/skills/issues/3) `qe`, [#4](https://github.com/QuantEcon/skills/issues/4) `benchmark`, [#12](https://github.com/QuantEcon/skills/issues/12) `audit`); ideas nobody has committed to belong in [FUTURE-IDEAS.md](../FUTURE-IDEAS.md). The style-guide rule content is authored in `QuantEcon/style-guide`, never here — this repo's `qe` plugin consumes a rendered snapshot ([project-style-guide#6](https://github.com/QuantEcon/project-style-guide/issues/6)).
