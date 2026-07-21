# Using QuantEcon skills

For lecture authors, reviewers, and maintainers who want to *use* the skills. (Building new ones: [developing-skills.md](developing-skills.md).)

## Setup

**In a lecture repo that has opted in** — nothing to do. Repos that check the marketplace into `.claude/settings.json` (see the [repo README](../README.md)) install everything automatically when you open the repo in Claude Code and trust it.

**Anywhere else** — three commands in a Claude Code session (the marketplace first, then the plugins you want):

```
/plugin marketplace add QuantEcon/skills
/plugin install qe@quantecon           # author-facing base skills
/plugin install benchmark@quantecon    # lecture-evaluation tooling
```

**In CI** — `anthropics/claude-code-action@v1` accepts `plugin_marketplaces` and `plugins` inputs directly; see the repo README for the workflow snippet.

## Invoking a skill

Three ways, all equivalent:

1. **Slash command** — type `/` and pick from the menu, e.g. `/benchmark:review-acceleration 717`. Trailing words are passed to the skill as arguments.
2. **Natural language** — describe what you want ("check this lecture's figures against the style guide"; "is this JAX conversion actually an improvement?") and the matching skill triggers on its description.
3. **Category entry points** — some plugins expose thin sub-skills (`/qe:check-figures`, `/qe:check-math`, …) so a narrow check is one keystroke and shows up in autocomplete.

## What to expect

- **Report first, fix on request.** Skills produce a structured report and *offer* changes; they never silently edit your files. Risky fixes (anything that breaks builds or changes published figures, e.g. RNG-stream changes) are presented but never auto-applied.
- **Evidence, not vibes.** Reports cite rule IDs, `file:line` locations, and measured numbers. The benchmark plugin goes further: its scores are computed by a deterministic engine from recorded evidence — the session shows the full derivation.
- **The same skill works pre-PR and in review.** Run it on your working copy before opening a PR (catch issues early), or point it at an open PR (consistent review).

## The plugins

| Plugin | Skills | What they do | Status |
|---|---|---|---|
| `qe` | `/qe:check-style` + `check-{writing,math,code,figures,jax,refs}` | Style-guide compliance for lecture source, by rule ID | scaffolding — [skills#3](https://github.com/QuantEcon/skills/issues/3) |
| `benchmark` | `/benchmark:review-acceleration` | Score a NumPy→JAX/Numba conversion (review mode) or assess whether a lecture is worth converting (triage mode) | system landed — [guide](../benchmark/README.md), [skills#4](https://github.com/QuantEcon/skills/issues/4) |

## Updating and troubleshooting

- **Update**: `/plugin` → marketplace → update, or reinstall; repos with the settings.json opt-in track the marketplace automatically.
- **Skill not in the menu?** Check the plugin is installed and enabled (`/plugin`), and that you trusted the repo. In settings-managed repos, `enabledPlugins` must list it.
- **A skill reports "not yet operational"** — it's scaffolding; its issue link says what's pending.
- **Version pinning**: plugin versions live in the marketplace catalogue; CI validates that every manifest is consistent, so a broken install is a bug — please open an issue.
