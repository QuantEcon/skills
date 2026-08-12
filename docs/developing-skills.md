# Developing skills

For contributors adding or modifying plugins in this repo. (Using them: [using-skills.md](using-skills.md).)

## Repo layout

```
.claude-plugin/marketplace.json   # the catalogue — every plugin registers here
scripts/                          # manifest + frontmatter validation, version-bump guard (CI runs these)
docs/                             # these guides
<plugin>/                         # one directory per plugin
  .claude-plugin/plugin.json      # name, description, version
  CHANGELOG.md                    # required: one entry per released version
  README.md                       # the plugin's user guide
  skills/<skill-name>/SKILL.md    # one directory per skill
  scripts/                        # deterministic scripts the skills drive
  references/                     # rule/rubric content the skills read
```

**A plugin needs its manifest and its changelog; a skill needs only `SKILL.md`.** A skill that is purely a procedure — nothing deterministic to run, no long reference material to point at — is one file in one directory, and should stay that way. `scripts/` appears when there is something mechanical worth doing in code; `references/` when the skill needs more context than belongs in its body. Adding either before you need it just makes the skill harder to read.

The three live plugins show some of the range: `qe` (an umbrella skill plus thin per-category sub-skills sharing plugin-level rules and scripts, alongside an unrelated standalone procedure with one script of its own), `benchmark` (one skill driving a deterministic engine, with worked examples as its regression baseline), and `audit` (sibling procedures sharing a method document). None of these is the house style — they are what three problems happened to need.

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
- **Self-contained plugins** (load-bearing — this one is a hard constraint of how plugins install, not a preference): an installed plugin ships only its own directory. No relative links or paths that escape the plugin root; use absolute GitHub URLs for repo-level files, and anchor runtime paths for the installed context with `${CLAUDE_PLUGIN_ROOT}` — `benchmark/skills/review-acceleration/SKILL.md` is the worked example.

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

The plugin is the released artifact and its version string is how a release is delivered, so a bump is a shipping decision rather than bookkeeping. Bump it in **both** `<plugin>/.claude-plugin/plugin.json` and the plugin's `marketplace.json` entry — `validate.py` enforces that the two agree, and `plugin.json` is the one that wins at install time.

- **A version bump is the delivery mechanism** (load-bearing — this is how the install cache works, not a convention we chose). An installed plugin lives at `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, and `claude plugin update` compares version strings only: if the content changed and the version did not, it reports "already at the latest version" and refreshes nothing. Merged content with an unchanged version reaches nobody who has the plugin installed, and nothing warns you. This has already happened here three times — most recently [#27](https://github.com/QuantEcon/skills/pull/27), which edited a shipped `SKILL.md` under `qe/` without bumping `qe`.
- **Therefore any change to any file under `<plugin>/` bumps that plugin's version.** Every file in the directory ships; there is no non-shipping edit inside it, and an exception list is where a rule like this rots. A file *moved out* of a plugin counts too — what it ships changed either way. Repo-level files — `docs/`, `README.md`, `CATALOG.md`, CI, the marketplace manifest — ship to nobody and bump nothing.
- **Choose the number for what a user of the plugin experiences.** A new skill, or a procedure that now does something materially different: minor (benchmark's scaffolding → working evaluation system was 0.1.0 → 0.3.0 — there was never a published 0.2.0). A correction that leaves the procedure as it was: patch. Nothing below 1.0.0 promises stability.
- **The catalogue's own top-level `version` in `marketplace.json`** moves only when a plugin is added or removed. (Past practice is mixed — adding `qe` did not move it, adding `audit` did — so the rule is stated here rather than inferred.) It is not a cache key and delivers nothing, so it gets no changelog entry.

### The changelog

Every plugin keeps its own `<plugin>/CHANGELOG.md`, and the version bump and its entry land in the same PR. [`qe/CHANGELOG.md`](../qe/CHANGELOG.md) is the worked example; the format and its reasons are stated in the file itself.

Why the file exists is worth stating honestly, because inside this repo it adds little: squash-merge already makes `git log --oneline -- qe/` one clean line per PR, and the commit-subject convention already reads as a changelog. It earns its place on two grounds. **The installed user has no git log** — the cache is an extracted directory with no `.git`, no remote to query, and for someone in the VS Code extension no practical path to one — so a file shipped inside the plugin directory is the only way to tell them what changed between the version they have and the one they would get. That is also why it is per-plugin rather than at the repo root: [self-contained plugins](#conventions) means an installed plugin ships only its own directory, so a root changelog is unreachable from the thing it describes, and a plugin's changelog links out with absolute GitHub URLs only. And **the entry is what makes the bump happen**: a reviewer looking at a diff that touches `qe/skills/…` and carries no new version heading can see the omission, which is what #27 walked into.

Keep entries short and user-facing — what someone can now do, or what behaves differently. An entry that only restates the PR title is the right length for a small change; an entry that recapitulates the diff is not useful to anyone. Where the changelog and a PR title are word for word identical, that is fine: a changelog entry is frozen at release, so the two copies cannot drift, and they are aimed at different readers.

There is no `Unreleased` section. It would park the description of a change away from the bump that delivers it, which is the one coupling that has to hold, and squash-merge leaves nothing for it to hold anyway: one PR is one commit, one version, one entry. Dates are the date you open the PR — you cannot know the merge date while writing, and a day's drift does not matter. Two PRs against the same plugin will conflict at the top of the file; **that conflict is the mechanism**, not a cost, since it is what stops both branches claiming the same version. Resolve it the ordinary way: rebase onto `main` and take the next version, in `plugin.json`, the `marketplace.json` entry, and the heading.

### The CI guard

`validate.yml` runs [`scripts/check-version-bump.py`](../scripts/check-version-bump.py) on every pull request into `main`. If any file under `<plugin>/` differs from the merge base, that plugin's `plugin.json` version must differ too — and must not be one already published on `main` — and `<plugin>/CHANGELOG.md` must carry a heading naming it. Any Markdown heading containing the version satisfies the last check; the file's format is not a CI contract.

It compares against the merge base *and* the base tip, so a branch that is behind `main` cannot land a version somebody else already shipped. It reads committed history only, so `python scripts/check-version-bump.py` run locally before you commit will say so rather than pretend to have checked your working tree. It needs full history (`fetch-depth: 0`) and exits **2** rather than 0 when it cannot see the base — a guard that silently passes when it cannot run manufactures confidence.

There is no override label. The escape hatch, on the rare occasion a bump feels disproportionate, is a patch bump: one line in two files, semantically honest, and unlike an exemption it actually delivers the change.

A second job runs `claude plugin validate --strict` against each plugin and the marketplace, using the runtime's own parser. It is separate because it installs an npm toolchain and `validate.py` should stay fast, and it catches what a regex frontmatter reader cannot — real YAML errors, and unknown `plugin.json` keys. The CLI is pinned there deliberately: under `--strict` an upstream warning becomes an error, and an unpinned install would let someone else's release fail an unrelated PR.

### Tags

Each release is tagged `{name}--v{version}`, so three independently-versioned plugins share one tag namespace. Tag from a clean checkout of `main` after the release merges:

```bash
claude plugin tag ./<plugin> --push -m "<plugin> %s"
```

It takes the version from `plugin.json`, refuses unless the marketplace entry agrees, refuses if the plugin fails validation, and refuses on a dirty working tree — so a tag cannot point at a version you did not mean to release. `--dry-run` prints what it would do.

**Nothing installs from a tag.** The marketplace serves `main`, so the merge is still the release and the tag is a bookmark for human archaeology — which is also why only current versions were tagged when the scheme was adopted, rather than backfilling history. Several historical versions could not have been tagged honestly: some name two different published trees, because content shipped twice under one version before the guard existed, and others sit at commits that fail today's validation. Each `CHANGELOG.md` records that ambiguity in prose, with PR numbers, which is more than a tag can carry.

## PR flow

- Branch, PR, CI must be green. This repo **squash-merges** — stacked branches need `git rebase --onto origin/main <old-base>` after the base PR merges (already-upstream commits drop automatically).
- External contributions land with the contributor as git author (`--author`, GitHub noreply address unless they prefer otherwise) and integration fixes as separate commits — see PR #5 for the pattern.
- [CATALOG.md](../CATALOG.md) lists what has merged *and* is operational, and nothing else, so a PR that makes a skill operational updates it while a PR that plans one — or that lands its scaffolding — does not. Scaffolding still belongs in [using-skills.md](using-skills.md), since it registers in the slash menu as soon as its plugin is installed. Work in flight belongs in the plugin's tracking issue ([#3](https://github.com/QuantEcon/skills/issues/3) `qe`, [#4](https://github.com/QuantEcon/skills/issues/4) `benchmark`, [#12](https://github.com/QuantEcon/skills/issues/12) `audit`); ideas nobody has committed to belong in the tracker as [low-priority enhancement issues](https://github.com/QuantEcon/skills/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement+label%3Alow-priority), each carrying its own merit assessment. The style-guide rule content is authored in `QuantEcon/style-guide`, never here — this repo's `qe` plugin consumes a rendered snapshot ([project-style-guide#6](https://github.com/QuantEcon/project-style-guide/issues/6)).
