# QuantEcon Skills

A [Claude Code plugin marketplace](https://code.claude.com/docs/en/plugin-marketplaces) housing QuantEcon's shared agent skills and their supporting scripts.

Each plugin bundles one area of work — a skill (the instructions Claude follows) plus the deterministic scripts it drives — so the same versioned toolkit works locally for authors and RAs, and headlessly in CI.

## Plugins

| Plugin | Skills | Status | Tracking |
|---|---|---|---|
| `qe` | `/qe:check-style` (+ `check-writing`, `check-math`, `check-code`, `check-figures`, `check-jax`, `check-refs`) | scaffolding | [CATALOG.md](CATALOG.md), work plan in `project-style-guide` |
| `benchmark` | `/benchmark:review-acceleration` | under construction | [meta#335](https://github.com/QuantEcon/meta/issues/335) |
| `audit` | `/audit:issues` (+ planned `prs`, `tech-debt`, `translations`) | first runbook landed | [CATALOG.md](CATALOG.md) §3 |

The `qe` plugin is the author-facing surface: one memorable prefix for the skills authors use while editing lectures and preparing PRs. `check-style` is the umbrella (whole lecture, optional category filter, e.g. `/qe:check-style lectures/aiyagari.md figures math`); the per-category sub-skills run the same shared rules individually. `benchmark` is a specialist family for maintainers evaluating accelerated implementations. `audit` is the maintainer-facing family for bulk, read-only sweeps of a whole repository — every issue, every PR, a whole codebase, a whole translated series — each delivering a report bundle rather than a chat answer. See [CATALOG.md](CATALOG.md) for the plan and [FUTURE-IDEAS.md](FUTURE-IDEAS.md) for parked candidates.

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

### CI (GitHub Actions)

The official action accepts the marketplace and plugin directly:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    plugin_marketplaces: "https://github.com/QuantEcon/skills.git"
    plugins: "benchmark@quantecon"
    prompt: "/benchmark:review-acceleration <args>"
```

## Layout

```
.claude-plugin/marketplace.json   # the marketplace catalogue
scripts/validate.py               # manifest + frontmatter validation (run in CI)
qe/                               # author-facing plugin
  .claude-plugin/plugin.json
  skills/check-style/SKILL.md     # umbrella skill
  skills/check-<category>/        # thin per-category sub-skills
  references/rules/               # shared rule files (style-guide schema)
  scripts/                        # shared deterministic preflight checkers
benchmark/                        # specialist plugin
  .claude-plugin/plugin.json
  skills/review-acceleration/SKILL.md
  scripts/                        # supporting Python scripts the skill drives
audit/                            # maintainer-facing bulk-audit plugin
  .claude-plugin/plugin.json
  skills/issues/SKILL.md          # one skill per audit subject
  references/                     # shared doctrine, org context, bundle contract
  scripts/                        # deterministic snapshot + coverage machinery
```

## Contributing

Open a PR adding or modifying a plugin directory and registering it in `.claude-plugin/marketplace.json`. Test locally with `claude --plugin-dir ./<plugin>` before submitting.

Run `python scripts/validate.py` before pushing — it checks that every plugin resolves, that `plugin.json` agrees with `marketplace.json` on name, version, and description, and that each `SKILL.md` has frontmatter whose `name` matches its directory. CI runs the same script on every PR; a malformed manifest otherwise breaks installation silently in every consuming lecture repository.

Broader context for this repository: [QuantEcon/meta#304](https://github.com/QuantEcon/meta/issues/304) (toolkit proposal) and [QuantEcon/meta#335](https://github.com/QuantEcon/meta/issues/335) (benchmarking programme).
