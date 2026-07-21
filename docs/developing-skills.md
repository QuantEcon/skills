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
- **Deterministic before LLM**: put everything mechanical in `scripts/` (checkable, testable, zero-false-positive bar); reserve the skill's judgement for what genuinely needs it, and require citations when it judges.
- **Don't duplicate content across docs** — one canonical location, pointers elsewhere. Rule text, weights, and thresholds especially: restated copies drift.
- **Self-contained plugins**: an installed plugin ships only its own directory. No relative links or paths that escape the plugin root; use absolute GitHub URLs for repo-level files, and anchor runtime paths for the installed context (issue #4 tracks the `${CLAUDE_PLUGIN_ROOT}` pattern).

## Development loop

```bash
# try a plugin against a real project without installing it
claude --plugin-dir ./benchmark

# validate everything the marketplace serves
python scripts/validate.py
```

`validate.py` checks: every catalogue entry resolves to a real directory; `plugin.json` agrees with `marketplace.json` on name/version/description; every SKILL.md has frontmatter whose `name` matches its directory. Negative-test your changes (break something on purpose; the validator must fail loudly) — a malformed manifest breaks installation silently in every consuming repo.

## Versioning and releases

Bump the version in **both** `plugin.json` and the plugin's `marketplace.json` entry — the validator enforces they match. Scaffolding → first usable content is a minor bump (the benchmark plugin's evaluation-system landing was 0.1.0 → 0.2.0).

## PR flow

- Branch, PR, CI must be green. This repo **squash-merges** — stacked branches need `git rebase --onto origin/main <old-base>` after the base PR merges (already-upstream commits drop automatically).
- External contributions land with the contributor as git author (`--author`, GitHub noreply address unless they prefer otherwise) and integration fixes as separate commits — see PR #5 for the pattern.
- Plans live in [CATALOG.md](../CATALOG.md) (active) and [FUTURE-IDEAS.md](../FUTURE-IDEAS.md) (parked); per-plugin work items live in issues ([#3](https://github.com/QuantEcon/skills/issues/3) style, [#4](https://github.com/QuantEcon/skills/issues/4) benchmark). The style-guide rule content is authored in `QuantEcon/style-guide`, never here — this repo's `qe` plugin consumes a rendered snapshot ([project-style-guide#6](https://github.com/QuantEcon/project-style-guide/issues/6)).
