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

The two live plugins show the two shapes: `qe` (umbrella skill + thin per-category sub-skills sharing plugin-level rules and scripts) and `benchmark` (one skill driving a deterministic engine with worked examples as its regression baseline).

## Conventions

- **Verb-first skill names** (`check-style`, `review-acceleration`) — they read as commands.
- **Description quality matters**: the SKILL.md frontmatter `description` is what natural-language invocation matches against. State what the skill does, what it measures, and when to use it. `validate.py` rejects descriptions too short to trigger reliably.
- **Report first, fix on request** — skills never silently edit; anything `build_risk` or output-changing (RNG streams) is presented, never auto-applied.
- **Deterministic before LLM**: put everything mechanical in `scripts/` (checkable, testable, zero-false-positive bar); reserve the skill's judgement for what genuinely needs it. The discipline scales with what the skill outputs:
  1. *Every skill*: claims carry citations — rule ID + `file:line`, or a number + its source. A findings list needs nothing more; don't add ceremony to simple skills.
  2. *Skills that judge*: record judgement as discrete answers (true/false per criterion, each cited), not free prose — so it's checkable.
  3. *Skills that score*: when multiple judgements aggregate into a verdict with stakes, use the benchmark plugin's evidence-file pattern — judgement lives only in an evidence file, a deterministic engine computes every score, and no score is ever typed by hand. Aggregation is where hand-waving hides; the engine eliminates it.
- **Don't duplicate content across docs** — one canonical location, pointers elsewhere. Rule text, weights, and thresholds especially: restated copies drift.
- **Self-contained plugins**: an installed plugin ships only its own directory. No relative links or paths that escape the plugin root; use absolute GitHub URLs for repo-level files, and anchor runtime paths for the installed context (issue #4 tracks the `${CLAUDE_PLUGIN_ROOT}` pattern).

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

## Versioning and releases

Bump the version in **both** `plugin.json` and the plugin's `marketplace.json` entry — the validator enforces they match. Scaffolding → first usable content is a minor bump (the benchmark plugin's evaluation-system landing was 0.1.0 → 0.2.0).

## PR flow

- Branch, PR, CI must be green. This repo **squash-merges** — stacked branches need `git rebase --onto origin/main <old-base>` after the base PR merges (already-upstream commits drop automatically).
- External contributions land with the contributor as git author (`--author`, GitHub noreply address unless they prefer otherwise) and integration fixes as separate commits — see PR #5 for the pattern.
- Plans live in [CATALOG.md](../CATALOG.md) (active) and [FUTURE-IDEAS.md](../FUTURE-IDEAS.md) (parked); per-plugin work items live in issues ([#3](https://github.com/QuantEcon/skills/issues/3) style, [#4](https://github.com/QuantEcon/skills/issues/4) benchmark). The style-guide rule content is authored in `QuantEcon/style-guide`, never here — this repo's `qe` plugin consumes a rendered snapshot ([project-style-guide#6](https://github.com/QuantEcon/project-style-guide/issues/6)).
