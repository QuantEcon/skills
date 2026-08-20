# QuantEcon Skills

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) housing QuantEcon's shared agent skills and their supporting scripts.

Each plugin bundles one area of work — a skill (the instructions Claude follows) plus the deterministic scripts it drives — so the same versioned toolkit works locally for authors and RAs, and headlessly in CI.

📖 **[quantecon.github.io/skills](https://quantecon.github.io/skills)** — the documentation, rendered and navigable. It is built from the files in this repository, so reading either one gets you the same content.

## Plugins

| Plugin | For | Covers |
|---|---|---|
| `qe` | Authors and RAs writing lectures | Style checks against the QuantEcon style guide (scaffolding today), working through the review feedback on a PR once it is open, and the `workplan-*` family — turning audit reports into tracked work projects and carrying work-plan state between agent sessions |
| `benchmark` | Maintainers reviewing accelerated implementations | Measured, rubric-scored evaluation of a conversion |
| `audit` | Maintainers sweeping a whole repository | Bulk, read-only audits — every issue, every PR, a codebase, a translated series — each producing a written report |

`qe` is the author-facing surface — one memorable prefix for everyday work, spanning a lecture's life from drafting to merge and the work planning around it. `check-style` is the umbrella style check (whole lecture, optional category filter, e.g. `/qe:check-style lectures/aiyagari.md figures math`; merged as scaffolding, not yet operational) and `/qe:copilot-review` picks the lecture up after the PR is open, working through Copilot's review comment by comment. The `workplan-*` family serves the maintainer end: `/qe:workplan-project` turns an audit or review report into a tracking issue with sub-issues, `/qe:workplan-issue` creates the single work-plan issue that carries state between agent sessions, and `/qe:workplan-update` maintains it across sessions (resume, update, or close-and-succeed). `benchmark` and `audit` are specialist toolkits, installed by the maintainers who need them.

**Which skills work right now is in [CATALOG.md](CATALOG.md)** — it lists what has merged *and* is operational, so this page does not repeat it. Skills whose scaffolding has merged but which do not run yet are in [docs/using-skills.md](docs/using-skills.md), because they still appear in the slash menu. Ideas nobody has committed to are tracked as [low-priority enhancement issues](https://github.com/QuantEcon/skills/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement+label%3Alow-priority).

## Documentation

Start with [docs/using-skills.md](docs/using-skills.md) to use the skills, and [docs/developing-skills.md](docs/developing-skills.md) to build or change one. The full map of which file owns which topic is in [AGENTS.md](AGENTS.md) — the canonical instructions for contributors and coding agents — so it is not repeated here.

## Installation

### Automatic (lecture repos)

Lecture repositories opt in by checking the following into their `.claude/settings.json`. Anyone who opens the repo and trusts it gets the marketplace and plugins installed automatically — no commands to run:

```json
{
  "extraKnownMarketplaces": {
    "quantecon": {
      "source": { "source": "github", "repo": "QuantEcon/skills" }
    }
  },
  "enabledPlugins": {
    "qe@quantecon": true,
    "benchmark@quantecon": true
  }
}
```

`audit` is deliberately absent from the lecture-repo block: it is maintainer tooling, and the plugin is the enable unit, so auto-installing it would put org-wide audit skills in every author's command list. Maintainers install it themselves.

### Manual (any project)

```
/plugin marketplace add QuantEcon/skills
/plugin install qe@quantecon
/plugin install benchmark@quantecon
/plugin install audit@quantecon
```

Those are slash commands in a Claude Code session; **restart the session afterwards**, since plugins register at startup. `/plugin` is a terminal-CLI built-in, so in the VS Code extension or the web app use the equivalent `claude plugin …` CLI commands instead — see [using-skills § Setup](docs/using-skills.md#setup).

### CI (GitHub Actions)

The official action accepts the marketplace and plugin directly:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    plugin_marketplaces: "https://github.com/QuantEcon/skills.git"
    plugins: "benchmark@quantecon"
    prompt: "/benchmark:review-acceleration <args>"
```

## Contributing

Open a PR adding or modifying a plugin directory and registering it in `.claude-plugin/marketplace.json`. The whole workflow — repo layout, conventions, local testing, validation (`python scripts/validate.py`), and the version-bump-plus-changelog rule that CI enforces on every plugin change — is in [docs/developing-skills.md](docs/developing-skills.md), and the repo-wide ground rules are in [AGENTS.md](AGENTS.md).

Broader context for this repository: [QuantEcon/meta#304](https://github.com/QuantEcon/meta/issues/304) (toolkit proposal) and [QuantEcon/meta#335](https://github.com/QuantEcon/meta/issues/335) (benchmarking programme).
