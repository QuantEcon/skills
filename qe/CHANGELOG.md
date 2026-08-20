# Changelog — `qe`

Every released version of this plugin, newest first. A version exists because the content below shipped in it: the plugin cache is keyed by version string, so what you have installed is exactly the entries down to the version `claude plugin list` reports for `qe`.

Versions are [semver](https://semver.org) as a user of this plugin experiences it — a new skill, or a procedure that now does something materially different, is a minor bump; a correction that leaves the procedure as it was is a patch. Nothing below 1.0.0 promises stability.

Repository: [QuantEcon/skills](https://github.com/QuantEcon/skills) ([every commit that touched this plugin](https://github.com/QuantEcon/skills/commits/main/qe)). How a release is made: [developing-skills § Versioning and releases](https://github.com/QuantEcon/skills/blob/main/docs/developing-skills.md#versioning-and-releases).

## 0.3.0 — 2026-08-20

Adds `/qe:workplan`, which closes the loop the `audit` plugin opens: audits produce evidence-cited report bundles, and this skill turns a bundle into tracked, actionable work.

**Added**

- `/qe:workplan <report-or-bundle> [owner/repo]` — turns an audit or review report into a QEP-compliant work package: read the bundle (index first, metadata scraped from the bolded header block — these reports carry no frontmatter), extract the findings that clear a stated three-part bar (actionable, evidenced, material), re-verify each against the target repo's current `main` before it earns a place, draft a tracking issue and sub-issues locally in the shape of the worked exemplar QuantEcon.py#925/#926, and — only after the user approves the drafts — file them with `gh` and link them as native GitHub sub-issues.
- A default mapping from the priority vocabularies the existing report corpus actually uses — triage verdicts (`MERGE`…`CLOSE`), 1–5 star quality, `P0`–`P3`, `GC`/`T0`–`T3` tiers, word priorities, severity glyphs — to an in/out decision, read against the rubric each report states for itself.
- Deduplication and supersession rules: trust the header **Snapshot** date over the directory name, keep the latest snapshot when bundles overlap, warn before building from a `_processed/` bundle, and surface disagreements between reports rather than silently resolving them.
- QEP alignment: exactly one QEP-2 type label per issue, priority labels only for outliers (no `medium-priority` exists), labels checked against the target repo before being proposed; and a QEP-1 check that flags a package which crosses repos or changes team workflow as possibly wanting a QEP instead of a pile of issues.
- The same third-party-write discipline as `/qe:copilot-review`: a "what this skill writes" table, every `gh` mutation gated on draft approval, safe re-runs by searching before creating, and a warning not to run the filing step headlessly.
- A method note in every draft package recording what was extracted *and* what was dropped in re-verification and why, so the filtering itself is checkable by someone who will not re-run it.

**Changed**

- The plugin description widens from "…working through a PR's review feedback" to also cover turning audit and review reports into tracked work packages.

## 0.2.2 — 2026-08-03

**Fixed**

- `/qe:check-math`'s description showed `\\top`, `\\tag` and `\\mathbb` where it meant `\top`, `\tag` and `\mathbb`. YAML plain scalars do no escape processing, so the doubled backslashes were literal — the description is what natural-language invocation matches against, so this was wrong in the one string that most needs to be right. (It stays unquoted deliberately: `\t` and `\m` are not valid double-quoted YAML escapes, so quoting it would break the file outright.)
- `/qe:copilot-review`'s status banner sent readers to [issue #3](https://github.com/QuantEcon/skills/issues/3) for "plan and open questions". That issue tracks the style-check surface and says nothing about this skill. The banner now credits the PR the skill shipped in and scopes #3 to the work it actually covers.

## 0.2.1 — 2026-08-03

**Fixed**

- `/qe:copilot-review`'s status banner said the skill "has never run from an installed plugin", which was false while being read from one. It now reads **operational**, validated on 2026-08-03 from an installed `qe@quantecon`: plugin-root path resolution, cross-repo mode, and running from outside a working tree. The correction was authored in [#27](https://github.com/QuantEcon/skills/pull/27), which did not bump `qe` — so until this release no installed user had received it.
- The same banner no longer writes `${CLAUDE_PLUGIN_ROOT}` in prose. The harness interpolates the variable, so on an installed plugin the sentence rendered with the reader's own cache path spliced into it. It now appears only inside code blocks.

**Added**

- This changelog.

## 0.2.0 — 2026-08-03

Adds `/qe:copilot-review`, the first `qe` skill that does real work end to end.

**Added**

- `/qe:copilot-review [PR] [owner/repo]` — runs the loop fetch → advise → fix → reply over a pull request's Copilot review. Both arguments are optional; with neither it works on the current branch's PR in the repo you are standing in. Five argument forms are accepted: none, `42`, `owner/repo 42`, `owner/repo#42`, and a full PR URL. Naming both repo and PR lets the skill run from anywhere, including outside a git working tree.
- Threaded replies via `pulls/<PR>/comments/<ID>/replies`, which is what makes a comment resolvable from the GitHub UI — a top-level `gh pr comment` does not thread and leaves the conversations open.
- `scripts/fetch-copilot.sh` — a read-only dump of a PR's Copilot review: the resolved repo and where it came from, the PR's state and title, the review overview, then every inline comment as `== ID <n> [REPLIED by <login>] path:line`. Invoked through `bash` so it works whether or not the executable bit survived install; `--help` prints the argument forms.
- Safe re-runs: the `[REPLIED by <login>]` marker names who answered each thread, so a second run replies only to comments still unanswered instead of double-posting.
- An explicit "what this skill writes" table — every mutating call (`/replies` POST, `gh pr comment`, `git commit`/`push`), the step it happens in, and the go-ahead that gates it — plus a warning not to run the skill headlessly, since a posted reply cannot be unposted and CI has nobody to confirm.
- A stop-on-ambiguity rule in the advise step: judgement calls surface the competing interpretations and ask before any code is touched, rather than being silently patched.
- Guidance that Copilot is sometimes wrong — an invalid comment gets a reasoned push-back reply, not a silent skip — and that reply bodies follow the repo's rules for writing to GitHub.

**Changed**

- The plugin description widens from "style checking and lecture editing support" to "style checking, lecture editing support, and working through a PR's review feedback", so `qe` now covers a lecture from drafting through to merging its PR.

**Fixed**

These are defects found while promoting the skill from a personal one, so none of them ever shipped in a `qe` release. They are listed because they describe what the shipped script does and does not do.

- Full pagination of `pulls/<PR>/comments` in both passes, so PRs with more than 30 review comments are reported completely. Previously only the first page was read — on a 104-comment PR it showed 19 and reported none as answered, so a re-run would have posted 19 duplicate replies.
- The overview shows the most detailed Copilot review rather than the newest, and says how many there were. Copilot re-reviews after every push and each re-review is a ~120-character stub, so on a PR with 33 reviews the summary previously rendered as nothing.
- `gh` failures surface `gh`'s own stderr instead of being reported uniformly as "no such PR", so missing `gh`, unauthenticated, offline and rate-limited are distinguishable.
- Transposed arguments are rejected. `fetch-copilot.sh 42 owner/repo` used to discard the second argument and produce a complete, plausible report about a different repository.
- Every line quoted from GitHub is prefixed with `| `, so a comment body cannot forge the `== ID` record header the reply step keys on, and third-party content is visibly marked as data to assess rather than instruction to obey.
- A PR URL no longer half-succeeds into a broken copy-paste command; a null comment body no longer prints the literal `null`; and the ANSI colour in the error path no longer leaks into non-TTY logs.
- Two documented claims corrected: Copilot is one GitHub App under three login strings (`copilot-pull-request-reviewer`, the same with `[bot]`, and `Copilot`), which is why reviews and comments filter on different values; and `line` is null on *outdated* comments, not multi-line ones.
- The working-tree requirement is stated correctly: the tree is what an omitted repo *or* PR number is inferred from, so naming a repo alone is not enough when the PR number is left out.

## 0.1.0 — 2026-07-21

First release. The author-facing style-check surface appears in the slash menu as scaffolding: the skills register and report that they are not yet operational when run.

- `/qe:check-style <lecture> [categories...]` — the umbrella style check for one lecture, with an optional category filter (`/qe:check-style lectures/aiyagari.md figures math`). On a PR branch the lecture argument can be omitted to mean "the lectures changed on this branch".
- Six per-category entry points running the same shared rules restricted to one category: `/qe:check-writing`, `/qe:check-math`, `/qe:check-code`, `/qe:check-figures`, `/qe:check-jax`, `/qe:check-refs`.
- The contract every check will follow: deterministic preflight first (build-breaking rules ahead of mechanical ones), then per-category passes, then one report table per category — rule ID, severity, `file:line`, finding, proposed fix — with counts by severity.
- Report first, fix only on request: nothing is edited without confirmation, and rules marked `auto_fix: false` or `build_risk: true` (RNG-stream changes, for instance, which alter published figures) are presented for the author to apply rather than applied.
- `references/rules/README.md` — the rule schema the vendored snapshot will use (`id`, `category`, `mode`, `severity`, `build_risk`, `auto_fix`, `detection`, `exclusions`), and the statement that rule text is authored only in `QuantEcon/style-guide` and rendered here.
- `scripts/README.md` — the pending MyST-context-aware `preflight.py` and `sync-rules.py` drift check.

---

**Before this file existed**, two changes to `qe/` shipped without a version bump, so two different trees have been distributed under one version string each. Under 0.1.0, [#5](https://github.com/QuantEcon/skills/pull/5) rewrote the status banner in all seven `check-*` skills to point at [issue #3](https://github.com/QuantEcon/skills/issues/3) instead of `CATALOG.md`. Under 0.2.0, [#27](https://github.com/QuantEcon/skills/pull/27) made the correction now released as 0.2.1. If your install predates those dates, `claude plugin update` will not have reconciled it — reinstalling at 0.2.1 gets you the current tree. The [CI guard](https://github.com/QuantEcon/skills/blob/main/scripts/check-version-bump.py) landed alongside this release is what stops it happening again.
