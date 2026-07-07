# QuantEcon Skills

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) housing QuantEcon's shared agent skills and their supporting scripts.

Each plugin bundles one area of work — a skill (the instructions Claude follows) plus the deterministic scripts it drives — so the same versioned toolkit works locally for authors and RAs, and headlessly in CI.

## Plugins

| Plugin | Skills | Status | Tracking |
|---|---|---|---|
| `benchmark` | `/benchmark:eval-py-acceleration` | under construction | [meta#335](https://github.com/QuantEcon/meta/issues/335) |

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
    "benchmark@quantecon": true
  }
}
```

### Manual (any project)

```
/plugin marketplace add QuantEcon/skills
/plugin install benchmark@quantecon
```

### CI (GitHub Actions)

The official action accepts the marketplace and plugin directly:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    plugin_marketplaces: "https://github.com/QuantEcon/skills.git"
    plugins: "benchmark@quantecon"
    prompt: "/benchmark:eval-py-acceleration <args>"
```

## Layout

```
.claude-plugin/marketplace.json   # the marketplace catalogue
benchmark/                        # one directory per plugin
  .claude-plugin/plugin.json
  skills/eval-py-acceleration/SKILL.md
  scripts/                        # supporting Python scripts the skill drives
```

## Contributing

Open a PR adding or modifying a plugin directory and registering it in `.claude-plugin/marketplace.json`. Test locally with `claude --plugin-dir ./<plugin>` before submitting. Broader context for this repository: [QuantEcon/meta#304](https://github.com/QuantEcon/meta/issues/304) (toolkit proposal) and [QuantEcon/meta#335](https://github.com/QuantEcon/meta/issues/335) (benchmarking programme).
