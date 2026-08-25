# QuantEcon Skills

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) housing QuantEcon's shared agent skills and their supporting scripts.

One plugin, `qe`, bundles the skills (the instructions Claude follows) with the deterministic scripts they drive, so the same versioned toolkit works locally for authors and RAs, and headlessly in CI.

📖 **[quantecon.github.io/skills](https://quantecon.github.io/skills)** — the documentation, rendered and navigable. It is built from the files in this repository, so reading either one gets you the same content.

## The `qe` plugin

One plugin, one namespace ([#43](https://github.com/QuantEcon/skills/issues/43)): every skill installs as `/qe:<name>`, so an invocation always reads as a QuantEcon skill.

| Skill | For | Does |
|---|---|---|
| `/qe:copilot-review` | Authors with an open PR | Works through Copilot's review comment by comment: verdict and fix per comment, threaded replies so each resolves from the GitHub UI |
| `/qe:benchmark` | Maintainers weighing acceleration | Advises whether a lecture is worth converting at all (triage), or scores a submitted NumPy→JAX/Numba conversion against the rubric (review) |
| `/qe:audit-issues` | Maintainers sweeping a repository | Whole-tracker audit, read-only: every issue's status verified against the code, tiered into the repo's plan, delivered as a report bundle |
| `/qe:workplan-project` | Maintainers organising work | Turns an audit or review report into a tracking issue with linked sub-issues |
| `/qe:workplan` | Anyone carrying work across sessions | The work-plan issue's whole lifecycle — create, read (validate and recommend, writing nothing), resume, update, close-and-succeed |

Style checks against the QuantEcon style guide (`/qe:check-style`) are planned in [skills#3](https://github.com/QuantEcon/skills/issues/3) and land once their rule snapshot and deterministic preflight exist. Until qe 0.7.0 the benchmark and audit skills were the separate `benchmark` and `audit` plugins — if you installed those, uninstall them (`claude plugin uninstall benchmark@quantecon audit@quantecon`) so the retired names don't linger in your menu.

**How far each skill has been validated is in [CATALOG.md](CATALOG.md)** — it lists what has merged *and* is operational, so this page does not repeat it. Skills not yet built live only as plans in the tracking issues — nothing ships as a non-working menu entry. Ideas nobody has committed to are tracked as [low-priority enhancement issues](https://github.com/QuantEcon/skills/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement+label%3Alow-priority).

## Documentation

Start with [docs/using-skills.md](docs/using-skills.md) to use the skills, and [docs/developing-skills.md](docs/developing-skills.md) to build or change one. The full map of which file owns which topic is in [AGENTS.md](AGENTS.md) — the canonical instructions for contributors and coding agents — so it is not repeated here.

## Installation

### Automatic (lecture repos)

Lecture repositories opt in by checking the following into their `.claude/settings.json`. Anyone who opens the repo and trusts it gets the marketplace and plugin installed automatically — no commands to run:

```json
{
  "extraKnownMarketplaces": {
    "quantecon": {
      "source": { "source": "github", "repo": "QuantEcon/skills" }
    }
  },
  "enabledPlugins": {
    "qe@quantecon": true
  }
}
```

Since the plugin is the enable unit and there is now one plugin, every consumer gets the full skill list — including the read-only maintainer tooling (audits, benchmark). That trade was weighed in [#43](https://github.com/QuantEcon/skills/issues/43): two extra read-only entries in a five-item menu, against a namespace every invocation shares.

### Manual (any project)

```
/plugin marketplace add QuantEcon/skills
/plugin install qe@quantecon
```

Those are slash commands in a Claude Code session; **restart the session afterwards**, since plugins register at startup. `/plugin` is a terminal-CLI built-in, so in the VS Code extension or the web app use the equivalent `claude plugin …` CLI commands instead — see [using-skills § Setup](docs/using-skills.md#setup).

### CI (GitHub Actions)

The official action accepts the marketplace and plugin directly:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    plugin_marketplaces: "https://github.com/QuantEcon/skills.git"
    plugins: "qe@quantecon"
    prompt: "/qe:benchmark <args>"
```

## Contributing

Open a PR modifying the `qe/` plugin directory (its `marketplace.json` entry included when the version moves). The whole workflow — repo layout, conventions, local testing, validation (`python scripts/validate.py`), and the version-bump-plus-changelog rule that CI enforces on every plugin change — is in [docs/developing-skills.md](docs/developing-skills.md), and the repo-wide ground rules are in [AGENTS.md](AGENTS.md).

Broader context for this repository: [QuantEcon/meta#304](https://github.com/QuantEcon/meta/issues/304) (toolkit proposal) and [QuantEcon/meta#335](https://github.com/QuantEcon/meta/issues/335) (benchmarking programme).
