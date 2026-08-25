# Using QuantEcon skills

For lecture authors, reviewers, and maintainers who want to *use* the skills. (Building new ones: [developing-skills.md](developing-skills.md).)

## Setup

**In a lecture repo that has opted in** — nothing to do. Repos that check the marketplace into `.claude/settings.json` (see the [repo README](../README.md)) install everything automatically when you open the repo in Claude Code and trust it.

**Anywhere else** — two commands in a Claude Code session (the marketplace, then the one plugin):

```
/plugin marketplace add QuantEcon/skills
/plugin install qe@quantecon
```

**`/plugin` is a terminal-CLI built-in**, so the VS Code extension and the web app answer `/plugin isn't available in this environment`. The `claude plugin` CLI does the same job from any shell and works everywhere:

```bash
claude plugin marketplace add QuantEcon/skills
claude plugin install qe@quantecon
```

Either route, **restart the session afterwards** — plugins register at startup, so a newly installed skill is absent until you reopen. `claude plugin list` shows what is installed and at which version.

**In CI** — `anthropics/claude-code-action@v1` accepts `plugin_marketplaces` and `plugins` inputs directly; see the repo README for the workflow snippet.

## Invoking a skill

Two ways, equivalent:

1. **Slash command** — type `/` and pick from the menu, e.g. `/qe:benchmark 717`. Trailing words are passed to the skill as arguments.
2. **Natural language** — describe what you want ("work through Copilot's review of this PR"; "is this JAX conversion actually an improvement?") and the matching skill triggers on its description.

## What to expect

- **Report first, fix on request.** Skills produce a structured report and *offer* changes; they never silently edit your files. Risky fixes (anything that breaks builds or changes published figures, e.g. RNG-stream changes) are presented but never auto-applied.
- **Evidence, not vibes.** Reports cite rule IDs, `file:line` locations, and measured numbers. The benchmark skill goes further: its scores are computed by a deterministic engine from recorded evidence — the session shows the full derivation.
- **The same skill works pre-PR and in review.** Run it on your working copy before opening a PR (catch issues early), or point it at an open PR (consistent review).

## The skills

Everything that registers in your slash menu — one plugin, five skills. Since `qe` 0.6.0 every entry is a skill that actually runs — an unbuilt skill lives only as the plan in its family's tracking issue (the style-check family, for example, is [skills#3](https://github.com/QuantEcon/skills/issues/3)). [CATALOG.md](../CATALOG.md) is the stricter list: merged, operational, *and* stating how far each has been validated.

| Skill | What it does | Status |
|---|---|---|
| `/qe:copilot-review` | Work through GitHub Copilot's review of a PR: a verdict and recommended fix per comment, then a threaded reply to each one so they can be resolved from the GitHub UI | operational, validated from an installed plugin 2026-08-03 — [#26](https://github.com/QuantEcon/skills/pull/26) |
| `/qe:workplan-project`, `/qe:workplan` | The work-plan family: `workplan-project` turns an audit/review report into a tracking issue with linked sub-issues; `workplan` carries the single work-plan issue that holds state between agent sessions through its lifecycle — `create`, `read` (validate against live state and recommend next steps; writes nothing), `resume`, `update`, `close`-and-succeed. All GitHub writes are drafted first and gated on your approval | merged as complete procedures, no validated run yet — [skills#3](https://github.com/QuantEcon/skills/issues/3) |
| `/qe:benchmark` | Advise whether a lecture is worth converting at all (triage — the front door), or score a submitted NumPy→JAX/Numba conversion against the rubric (review) | operational for workspace runs — [guide](../qe/references/benchmark/README.md), [skills#4](https://github.com/QuantEcon/skills/issues/4) |
| `/qe:audit-issues` | Sweep a whole tracker: verify each issue's status against the code rather than the thread, tier the open set into the repo's plan, deliver a report bundle. Read-only — it recommends, never applies | run once as a skill, method validated only that far — [tutorial](tutorial-run-an-audit.md), [guide](../qe/references/audit/README.md), [skills#16](https://github.com/QuantEcon/skills/issues/16) |

## Updating and troubleshooting

- **Update**: `claude plugin update qe@quantecon` from any shell, or `/plugin` → marketplace → update; repos with the settings.json opt-in track the marketplace automatically. Like installs, updates apply on the next session restart.
- **Skill not in the menu?** Check the plugin is installed and enabled (`/plugin`), and that you trusted the repo. In settings-managed repos, `enabledPlugins` must list it.
- **`Unknown command: /qe:benchmark`?** The plugin-prefixed slash form needs a recent Claude Code (v2.1.216+; check with `claude --version`). On older versions the skill still registers under the bare `/benchmark`, and **natural-language invocation works on any version** — just describe the task ("is this JAX conversion worth merging?"). If it resolves under none of these, the install didn't complete — re-run `/plugin install qe@quantecon`. And if the *old* names (`/benchmark:review-acceleration`, `/audit:issues`) still appear, the retired plugins are lingering — `claude plugin uninstall benchmark@quantecon audit@quantecon`.
- **Version pinning**: plugin versions live in the marketplace catalogue; CI validates that every manifest is consistent, so a broken install is a bug — please open an issue.
