# Changelog — `qe`

Every released version of this plugin, newest first. A version exists because the content below shipped in it: the plugin cache is keyed by version string, so what you have installed is exactly the entries down to the version `claude plugin list` reports for `qe`.

Versions are [semver](https://semver.org) as a user of this plugin experiences it — a new skill, or a procedure that now does something materially different, is a minor bump; a correction that leaves the procedure as it was is a patch. Nothing below 1.0.0 promises stability.

Repository: [QuantEcon/skills](https://github.com/QuantEcon/skills) ([every commit that touched this plugin](https://github.com/QuantEcon/skills/commits/main/qe)). How a release is made: [developing-skills § Versioning and releases](https://github.com/QuantEcon/skills/blob/main/docs/developing-skills.md#versioning-and-releases).

## 0.11.0 — 2026-09-08

Follows the [QEP-6](https://github.com/QuantEcon/qeps/pull/18) §4 amendments ruled on 2026-09-08 ([qeps#18](https://github.com/QuantEcon/qeps/pull/18#issuecomment-5583823922)), and corrects two citations that were wrong rather than merely stale. QEP-6 is still a Draft and this plugin still tracks it by PR, as 0.10.0 did.

**Changed**

- **`workplan-project` writes dependency edges.** Step 6's mutating-call table gains `gh issue edit <item> --add-blocked-by <blocker>`. QEP-6 §4 has required native edges for a real sequencing constraint since it was drafted and **no skill in this family wrote one** — every edge on the org's conformant trackers was made by hand after a review found them missing. The row carries the two platform facts a producer needs: one call per edge, since `gh` takes no list; and for a blocker in another repository `gh` refuses the flag, so the REST `dependencies/blocked_by` endpoint is used instead, whose body takes the blocker's numeric **id** rather than its number.
- **A gate between packages is carried, not just described.** The cross-package guidance previously said a gate is *stated* once in the body of the package that waits. Under the amended §4 the gate is **carried as native edges** and only its rationale is stated — "prose is the one carrier no consumer reads" — with the phase-level form spelled out: the first item of the waiting phase is blocked by every item of the phase it waits on, which is linear in the upstream phase and clears when that *phase* closes rather than when the upstream tracker does. Where a phase's exit criterion is a single `Decision`, each waiting item carries the edge to the `Decision` instead.
- **The sibling back-pointer is no longer an obligation.** §4's requirement that the waited-on project point back was struck: blocked-by and blocking are two ends of one edge, so the reverse direction is read rather than written. A `Related work` entry pointing at the rationale stays available prose.

**Fixed**

- **Two Adoption clause citations were off by one.** QEP-6's Adoption list read `1., 2., 2., 3., 4.` in source, and Markdown renumbers an ordered list on render — so the published document showed 1–5 while every citation after the first pointed one clause short. The read-before-link obligation is **clause 3**, not clause 2; the C2-precedence ruling this skill applies is **clause 4**, not clause 3. (0.10.0's release note below cites clause 3 for the precedence ruling; that is left as written, since it records what shipped.) The source numbering is corrected upstream and is now enforced by a CI check ([qeps#30](https://github.com/QuantEcon/qeps/pull/30)).
- **QEP-2 is Accepted, and the audit context said it was a Draft.** `references/audit/quantecon-context.md` told an agent that doctrine rule 6 applied and to mark anything beyond the already-canonical labels *post-acceptance*. QEP-2 has been Accepted since it merged, so the whole set is canonical. The same passage now names `qep-0002-labels.yml` as the authority and records how the CLI tracks it: the appendix is vendored verbatim with a pin to the `qeps` revision it came from, and a weekly job compares the vendored *blob* against upstream — content rather than commit, so it fires when the schema moves and not when another QEP is edited. Verified on 2026-09-08: vendored, upstream and at-pin blobs are all `161cd746`, so the copy is current. An earlier plugin-era gap, where four labels were omitted from a hand-kept manifest, is what that vendoring closed.

## 0.10.0 — 2026-09-02

`workplan-project` is brought into line with [QEP-6](https://github.com/QuantEcon/qeps/pull/18) (draft), the standard for project-tracker structure and order, following the six findings its field test ([qeps#19](https://github.com/QuantEcon/qeps/issues/19)) filed against the skill — [#69](https://github.com/QuantEcon/skills/issues/69) to [#74](https://github.com/QuantEcon/skills/issues/74), adopted into [#63](https://github.com/QuantEcon/skills/issues/63) as phase 1. The skill has still not run against a real bundle ([#65](https://github.com/QuantEcon/skills/issues/65)); this release changes what that run will produce. Where C2 and QEP-6 disagree the skill now says so and cites QEP-6's Adoption clause 3, which rules QEP-6 authoritative for structure until the contract's handover.

**Changed**

- **The tracker body carries a phase table, not a plan table.** `Phase | Intent | Exit criterion` replaces `Phase | Issue | Work item`: membership, order and state belong to the sub-issue list, and the old table was the body mirror QEP-6 §7 forbids — C2-conformant, since C2 only rules that checkbox progress is never read, and QEP-6-non-conformant. The tracking issue is now written once: no placeholder numbers, no backfill edit, and no second body write to lose the stamp in (#69).
- **Plan order is stated and kept.** Draft file order is plan order; sub-issues are linked with `gh issue edit --add-sub-issue` in that order, the read-back asserts it, and a re-run places a recovered item in its position with the reprioritise API instead of appending it to the bottom of the list. The database-id gotcha moves off the link path to the one call that needs it. Until [status-projects#19](https://github.com/QuantEcon/status-projects/issues/19) ships the dashboard cannot show the difference, so the check is on GitHub (#70).
- **Linking reads the parent first.** Sub-issue membership is single-parent and `gh`'s link verbs replace an existing parent silently, so every pre-existing issue's parent is read before it is linked; an already-parented item is named in the approval draft with the tracker it would leave, and a re-run that finds one stops before linking (#72).
- **A membership gate, new step 4**, sits between validation and drafting: the definition of done is written first, each survivor is tested against QEP-6 §1's criterion, packages split by definition of done rather than by count or phase, and findings that clear the bar but not the gate are filed unparented (#71).
- **The exemplar is cited for content, not shape.** QuantEcon.py#925's stamp now parses, but its plan table still carries an `Issue` and a `Status` column; the shape comes from QEP-6 Appendix A, with #925 cited for body content and #926 for the evidence bar (#73).
- **Split packages get `Related work` and `Gates`**: each package names its siblings (projects, never work items), and a gate between packages is written once, in the body of the package that waits, at phase granularity by default (#74).
- Housekeeping: the status banner points at #65 rather than #3, and the retired `audit` plugin link points at `/qe:audit-issues`.

## 0.9.0 — 2026-09-02

The work-plan family gains a third skill, extracted from a hand run: the roadmap drawn for the Lectures monorepo project from its tracker ([project-monorepo#30](https://github.com/QuantEcon/project-monorepo/pull/30), members-only). Tracked in [#63](https://github.com/QuantEcon/skills/issues/63).

**Added**

- `/qe:workplan-roadmap` — draw or update a project's `ROADMAP.md`: two GitHub-rendered mermaid flowcharts (the route — phases, decision gates, the pathways each gate can choose — and every tracker sub-issue with its dependencies), a table of what each gate can decide, and a node index. It snapshots the tracker with the new `scripts/workplan/tracker-snapshot.sh` (direct sub-issues in plan order, with the `Decision` role read from the native issue type or the QEP-6 body marker), diffs the snapshot against the roadmap's node index, and reports the *structural* changes only — an item merely closing is not one, by the file's own update rule. The file, the commit and the pull request are written after approval; the tracker itself is never edited. The roadmap lives beside the plan in the tracker's repository, never on the projects dashboard, because [C2 §2.2](https://github.com/QuantEcon/status-projects/blob/main/docs/contracts/tracker.md) withholds a private tracker's children from the public site.

**Changed**

- `workplan` and `workplan-project` now describe the family as three skills and link the third.

## 0.8.0 — 2026-08-26

The work-plan skills gain a second reader. Since 2026-08-24 the [projects dashboard](https://quantecon.github.io/status-projects/) parses every registered project tracker nightly and publishes a per-tracker compliance block, so a tracker these skills produce is now read by a machine as well as by the next session. The two ends are pointed at one contract — [`docs/contracts/tracker.md`](https://github.com/QuantEcon/status-projects/blob/main/docs/contracts/tracker.md) (C2), which states the rules once and which the skills link to rather than restate ([#49](https://github.com/QuantEcon/skills/issues/49) item 2).

**Changed**

- **The revision stamp is now a heading in a fixed form** — `## Where we stand (verified YYYY-MM-DD)`, optionally with a time and zone. The skills carry the two example forms and the one authoring rule, not the parser grammar: C2 owns that and stays the authority, and `status-projects` being private is why the example is inline rather than a bare pointer. Both skills stamped before this release; they stamped in prose the collector cannot read, so a plan revised faithfully every session still published as unstamped. `create` writes the heading, `resume` and `update` re-date it, `read` reports its age and says when it is absent or malformed, and anchor-and-sweep reads the date from the stamp alone — a `verified` in a table cell or a checklist is not a stamp, and taking one as the anchor mis-scopes the sweep.
- **Long-lived trackers carry the native `Project` issue type**, applied after creation by `workplan`'s `create` and by `workplan-project`'s filing step. This replaces "plan issues stay untyped pending the QEP-2 field report": the field report is [qeps#11](https://github.com/QuantEcon/qeps/issues/11) and its answer turned out not to be a label at all, so QEP-2's set is untouched and `type:Project` filters org-wide. Period plans stay untyped — a session's working document is not a project.
- **`workplan-project` drafts the work as native sub-issues, explicitly.** It already created them; the reason is now stated, because it is load-bearing rather than cosmetic — a tracker whose work lives in body checkboxes publishes its progress as `null`, not as a percentage.

**Added**

- **Both skills now say that a conformant tracker is still invisible until it is registered**, and offer to draft its `projects.yml` row — slug, programme, stage, owner, one public sentence, and the tracker in `Owner/repo#N` form. Opening the pull request against `QuantEcon/status-projects` stays the user's move; the skills draft and stop. Automating the registration PR end to end is [#49](https://github.com/QuantEcon/skills/issues/49) item 1 and is not in this release.

**Known gaps, tracked rather than fixed here**: the `qe:tracker-conform` skill the contract names as the fix half of its compliance block ([#49](https://github.com/QuantEcon/skills/issues/49) item 3), and the `wp{issue#}-stage{n}` milestone convention ([#55](https://github.com/QuantEcon/skills/issues/55)).

## 0.7.0 — 2026-08-25

One namespace ([#43](https://github.com/QuantEcon/skills/issues/43)): the `benchmark` and `audit` plugins fold into `qe`, so every invocation reads as a QuantEcon skill and the catalog is one flat, small list. Three plugin prefixes encoded an installation distinction users don't care about when typing a command. This release starts strictly above every retiring stream (qe 0.6.0, benchmark 0.4.0, audit 0.2.0), so no version number in this merged changelog ever names two trees; the retired plugins' own entries are preserved below as historical sections.

**Added**

- `/qe:benchmark` — the benchmark plugin's `/benchmark:review-acceleration`, renamed to match how everyone refers to it; triage vs review stays mode selection from the arguments. Procedure unchanged; the scoring engine now lives at `scripts/benchmark/scoring/` and the framework, worked examples and fixtures at `references/benchmark/`, with `${CLAUDE_PLUGIN_ROOT}` paths updated throughout (including the worked examples' `run_all.py` engine lookup and its repo-layout fallback).
- `/qe:audit-issues` — the audit plugin's `/audit:issues`; the `audit-` stem keeps the family greppable if `/qe:audit-prs` or `/qe:audit-translations` ever pass their validation gate. Procedure unchanged; the shared method docs live at `references/audit/` and the snapshot fetcher at `scripts/audit/`.

**Removed**

- The separate `benchmark` and `audit` plugins. **Migration for installed users**: run `claude plugin uninstall benchmark@quantecon audit@quantecon` (or the `/plugin` menu equivalent), or the retired skills linger in the slash menu under their old names; lecture repos drop `benchmark@quantecon` from `enabledPlugins` in `.claude/settings.json`. One consequence is deliberate and worth knowing: the plugin is the enable unit, so every `qe` consumer now gets the audit skills too — two extra read-only entries in a five-item menu, judged an acceptable trade in #43.

**Changed**

- The plugin description now names the whole surface: PR review feedback, acceleration triage/review, bulk audits, report-to-project, and the work-plan lifecycle.
- Old tags (`benchmark--v0.4.0`, `audit--v0.2.0`, …) remain valid archaeology for the retired streams.

## 0.6.0 — 2026-08-25

The style-check scaffolding leaves the shipped plugin. The seven `check-*` skills had reported "not yet operational" since they merged in [#2](https://github.com/QuantEcon/skills/pull/2), because everything that would make them work — the rendered rules snapshot, the deterministic preflight — is still pending upstream (see [issue #3](https://github.com/QuantEcon/skills/issues/3)). Shipping menu entries that do nothing costs more than it signals: they occupy seven slots in every consumer's slash menu and every description competes for natural-language routing against skills that actually run. The plan is unchanged and stays in issue #3, where unbuilt work belongs; the skills return operational, not as scaffolding.

**Removed**

- `/qe:check-style` and the six per-category entry points (`/qe:check-writing`, `/qe:check-math`, `/qe:check-code`, `/qe:check-figures`, `/qe:check-jax`, `/qe:check-refs`) — all scaffolding, none operational. The carefully-authored frontmatter descriptions and the umbrella's procedure sketch are preserved on issue #3 for when the skills re-land.
- `qe/references/rules/` (the documented location for the pending rules snapshot) and the "Style preflight" section of `qe/scripts/README.md` — scaffolding for the same pending work, likewise consolidated into issue #3.

**Changed**

- The plugin description drops "style checking, lecture editing support" — it now names only what ships: PR review feedback, report-to-project, and the work-plan lifecycle.

## 0.5.0 — 2026-08-25

The work-plan lifecycle consolidates into one skill and gains a read verb. Two findings from reviewing the family in real use drove this ([#50](https://github.com/QuantEcon/skills/issues/50)): asking to *read* a plan routed to `workplan-update` — the only skill whose description mentioned an existing plan — whose every verb writes; and the deeper cause was structural: `workplan-issue`, `workplan-update`, and the proposed `workplan-read` were all verbs on the *same artifact* split across separate skills, which is what forced the cross-skill handoffs (close handing succession to `workplan-issue`, discovery and anchor-and-sweep linked between files, four descriptions competing for "work plan" requests). The family is now two skills: `/qe:workplan` (the state-carrier issue's lifecycle) and `/qe:workplan-project` (report → project), unchanged.

**Added**

- `/qe:workplan [create [owner/repo] | read [--full] | resume [--full] | update | close] [issue#]` — the work-plan issue's whole lifecycle in one skill. `create`, `resume`, `update`, and `close` are the procedures shipped in 0.4.0 as `workplan-issue` and `workplan-update`, now sharing one statement of the convention, one issue-discovery rule, and one anchor-and-sweep section; succession is internal to `close` (draft successor via `create`'s succession source → post ledger citing it → close, so the chain never dangles) instead of a documented handshake between two skills. With no verb, a look-shaped request dispatches to `read`; anything else asks which moment it is.
- The new `read` verb — look, validate, recommend, writing nothing. **Read**: the revision stamp and its age first (the plan's warranty date), then the front of the plan, the live-state facts *as of the stamp*, block status, and the latest revision-log comment. **Validate**: a read-only sweep since the stamp checks the plan's premises — default depth is the front-of-plan items plus anything the sweep contradicts, `--full` checks every claim — and classifies each as *holds*, *aged*, or *inverted*, with a trace citation, reporting body and reality side by side rather than blended. **Recommend**: what actually leads next and whether the body needs re-stamping first (via `resume`), or which other verb the moment calls for — named, never run unasked. No approval gates because there is nothing to gate; `resume` now begins as a `read` at working depth.

**Removed**

- `/qe:workplan-issue` and `/qe:workplan-update` as separate skills — their procedures live on unchanged as `workplan`'s verbs. They existed for one release (0.4.0) with no validated run, so consolidating before first use costs nothing.

**Changed**

- The name `/qe:workplan` is reused: it meant the report-to-project skill for one morning in 0.3.0 (renamed `workplan-project` in 0.4.0, before any installed use); from this release it is the lifecycle skill.
- `workplan-project`'s family cross-reference now names the two-skill shape.
- Skill status banners no longer restate release history (which skill shipped when, under what name) — this changelog owns that; a banner now says only the skill's validation status. Applied to `workplan` and `workplan-project`.
- The plugin description widens to "creating, reading and carrying work-plan state across agent sessions".

## 0.4.0 — 2026-08-20

The work-plan surface becomes a three-skill family with one name scheme: `workplan-project` builds a *project* (tracker + sub-issues) from a report, `workplan-issue` creates a single *work-plan issue* (the org's cross-session state carrier), and `workplan-update` maintains one across agent sessions. The family formalises a practice observed across ~45 ad-hoc work-plan issues in 15 org repos; the convention itself is slated for a QEP, and until that lands it is stated once, in `workplan-issue`, with the other skills pointing at it.

**Added**

- `/qe:workplan-issue [owner/repo]` — triage and organise work into a work-plan tracking issue, from any of three sources: a backlog triage (a planning pass over agreed work — a full tracker *audit* stays `/audit:issues`' job), a session bootstrap (the first plan is a handover with no predecessor), or a closing plan's carry-forward register (succession — the register, never a copy of the old body). The body shape comes from the org's exemplars: a live-state table in which every fact is measured now and stamped with time and timezone, dependency-ordered work blocks with their gates named, an explicit front of plan, and an "explicitly not doing" section so deferrals are decisions rather than omissions. Files nothing until the draft is approved, and checks the one-open-plan-per-repo invariant before creating.
- `/qe:workplan-update [resume|update|close] [issue#]` — maintains a work-plan issue across sessions, where a session is one agent context window. Three moments: `resume` (session start — re-verify the plan's premises against live state and revise the body *before* working it; `--full` re-verifies every claim), `update` (session end, plan continues — body revised in place with a resume pointer, plus a revision-log comment built from verifiable traces swept since the body's own revision stamp), and `close` (plan complete — closing ledger, successor created via `workplan-issue`, in an order that never leaves the chain dangling; closing a long-lived tracker is a category error the skill refuses). One acceptance test governs every write: a fresh agent, given only the issue, can resume the work without the old conversation.
- The same third-party-write discipline as the rest of `qe`: every `gh` mutation tabulated and gated on an approved draft (shown as a diff against the *freshly re-fetched* live body, since `gh issue edit --body` replaces wholesale), the close path behind a separate explicit confirmation, and warnings not to run the mutating paths headlessly.

**Changed**

- `/qe:workplan` is renamed `/qe:workplan-project`. It shipped this morning in 0.3.0; the rename lands the same day, before any installed use, so the family shares one prefix while the cost is zero. The procedure is unchanged; its output is now called a work *project* to match the family vocabulary.
- The plugin description widens to cover creating and carrying work-plan state across agent sessions.

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

---

## Historical — the `benchmark` plugin (folded into `qe` at 0.7.0)

Released 2026-07-07 to 2026-08-07 as the separate `benchmark` plugin; its skill lives on as `/qe:benchmark`. These entries are frozen as shipped — version numbers and tags (`benchmark--v0.4.0`) name the retired plugin's own stream, which qe's 0.7.0 starts strictly above so no number ever names two trees.

### benchmark 0.4.0 — 2026-08-07

Triage becomes the front door, and every output leads with the decision. The reframing follows the maintainers' direction — the product most wanted is "look at a lecture and advise whether a JAX upgrade is recommended" — and the measured record agrees: in every evaluation to date (ge_arrow, markov_asset, wald_friedman, and the 2026-08-06 ge_arrow re-run on [skills#10](https://github.com/QuantEcon/skills/issues/10)) the recommendation was decided by the triage-layer instruments — the as-used baseline and what a conversion could reach — and never moved by the scorecard on top. Review mode is unchanged and stays: it is the mode that caught markov_asset's masked build defect, and it applies the day a conversion PR exists.

**Changed**

- `SKILL.md` leads with triage — the no-candidate "should this lecture be converted?" question — behind a "Which mode" router, with review as the second mode. The frontmatter description now opens with the advise use case, so natural-language invocation matches the common question. Review-mode content is unchanged.
- The scorer's printed output and the report format lead with the verdict. `score.py` prints `VERDICT:` above the weighted total, labels the total "for the record", and the deciding-flip lines name the verdict they flip to before the recomputed number (previously `⇒ total 2.30, …`, which two careful readers in a row took as the headline — [skills#14, finding 6](https://github.com/QuantEcon/skills/issues/14)). The report's TL;DR opens with the full verdict and carries the score alongside as candidate quality for the record; the dimension table gains a verdict row so it still carries the decision when quoted on its own.
- `README.md` puts triage first throughout — the mode table, the invocation examples, and the mode sections — and states that triage builds no candidate: it measures the lecture as it stands and bounds what a conversion could deliver.
- Triage now names its canonical decision criteria: the manual's JAX style page ([when to use JAX, when not to](https://manual.quantecon.org/styleguide/jax.html), including *Converting from Numba § Decide first*), cited rather than restated. The skill's four checks are framed as the measurement layer that tests whether those criteria hold for a given lecture — "a real bottleneck" is a claim the as-used baseline and pattern match establish or refute, while the page's "teaching JAX itself" criterion is editorial and stays a maintainer call.
- The triage decision rule no longer re-derives numbers from the rubric weights: it states the conclusion qualitatively and points to `references/EVALUATION_FRAMEWORK.md`, which the skill's own scoring step already said was the only place weights live. Triage's outcome vocabulary is standardized on **convert / don't-convert** in both `SKILL.md` and `README.md`. (Caught by Copilot's review of the 0.4.0 PR.)

Nothing in the rubric, weights, gates, or scorecard JSON changed: the regression anchors (2.85 / 2.25) and the fixtures reproduce unchanged.

### benchmark 0.3.2 — 2026-08-03

**Fixed**

- The plugin README's status line said skill wiring was "tracked in skills#4". The wiring shipped in 0.3.0 — it is in that release's entry below — so the line pointed at an open issue for work that had already landed. 0.3.1 corrected the version number in that same sentence and left the stale clause standing, which is how a half-fixed line survives a review. It now describes the plugin as operational for workspace runs since 0.3.0 and points at this changelog for what shipped when.

### benchmark 0.3.1 — 2026-08-03

**Added**

- This changelog.

**Fixed**

- The plugin README's status line named `v0.2.0` — a version that was never released (see the note at the foot of this file). It now names `v0.3.0`, the release in which the evaluation system actually became runnable. That is a historical fact rather than a restatement of the current version, so it will not go stale again on the next bump.

### benchmark 0.3.0 — 2026-07-27

The evaluation system became runnable: a deterministic scoring engine, rubric v2 with verdict gates, two complete worked evaluations to copy from, a triage mode, and the install fix that made the plugin installable at all.

**Added**

- A runnable scoring engine: `python scripts/scoring/score.py <lecture-dir>` turns an evidence file into a scorecard. No score is ever typed by hand; the session shows the derivation table — every dimension score with the measured number and threshold band that produced it.
- `references/EVALUATION_FRAMEWORK.md` — the rubric in prose: seven weighted dimensions, numeric scoring anchors, structural checklists, verdict bands, worked HIGH/LOW examples. `SKILL.md` points here instead of restating weights, so recalibration cannot drift the copies.
- `scripts/scoring/EVIDENCE_TEMPLATE.json` — the judgement contract you fill in: measured numbers plus cited yes/no answers.
- Two complete worked evaluations in `references/examples/` (ge_arrow 2.85/5, markov_asset 2.25/5) with measurement scripts, results, evidence and reports — usable as per-lecture templates and as regression anchors, plus a README documenting where every evidence number came from.
- `scripts/calibration/bellman_bench.py` — the shared aiyagari Bellman benchmark that pins the "25x as-used = score 5" efficiency anchor.
- Rubric v2 verdict gates: the logic-and-design bug cap is derived from the correctness evidence (does it build, does it diverge under x64) rather than trusting a hand-set boolean, and the correctness score caps the verdict — a float32 catastrophe with no logic bug can no longer come out as "merge".
- A no-conversion verdict: a lecture whose baseline as-used total is under the 1 s materiality floor, with a slower candidate, now gets "don't convert" instead of a polished score of the rewrite.
- A sensitivity stamp on every scorecard: each scored input is perturbed one at a time (bools flipped, counts ±1, floats ±10%) and the verdict is stamped robust / fragile / robust-at-floor with the deciding flips listed.
- K-repeat as-used measurement: `run_all.py` repeats each side three times in fresh processes, the headline speedup is the median, and per-run spread feeds a contested-band annotation.
- Triage mode — "is this lecture worth converting at all?", answered from the existing lecture alone: baseline as-used total, workload-pattern match against the two calibrated poles, crossover check, readability-cost forecast, and the weight algebra that follows. Validated blind against the three known cases before being documented, including the documented limit that it cannot predict conversion-quality defects.
- `benchmark/README.md` — the plugin's user guide: review vs triage mode, the report format, the manual pipeline quickstart, and the one rule to remember (warm-only speedups are never the headline).
- Skill wiring for installed runs: evaluations are scaffolded under `<workspace>/benchmark-eval/<lecture>/` with the plugin read-only at `${CLAUDE_PLUGIN_ROOT}`, preconditions stated up front, and an extraction/replay diff check so the replay provably matches the lecture.
- A provenance stamp written to `results/env.json` (python/platform/numpy/jax/quantecon versions), including the titles of any failed pipeline step so a partial run cannot claim full provenance.
- `references/fixtures/rubric_v2` — synthetic evidence whose only job is to execute five v2 code paths the worked examples never touch; every source string is prefixed `SYNTHETIC:` so the numbers cannot be cited as evidence about a lecture.

**Changed**

- The skill is now `/benchmark:review-acceleration`, renamed from `/benchmark:eval-py-acceleration`. The rename was authored on 2026-07-21 in [#1](https://github.com/QuantEcon/skills/pull/1) but reached installed users only with this version bump.
- `score.py` takes a lecture directory path and works from any working directory, instead of resolving a lecture name against a package root.
- Correction of record on markov_asset: the lecture does build in notebook order — a stale global `err` masks a stray `err.throw()`, silently disabling the checkify stability validation. Worse than a crash, but not the build failure the original report claimed; erratum prepended to the report and the wording fixed in the examples README, `SKILL.md` and the plugin README.
- Two earlier certifications withdrawn as overstated: the reference replays deviate from the lectures' construction patterns (not "mirrors the lecture exactly"), and the as-used totals were single-pass, not medians over repeats (v2 restores repeats explicitly).
- The plugin README's triage baselines are labelled as triage-time (2026-07-21) measurements, and the framework and `SKILL.md` stop restating them — the gate reads each lecture's own `baseline_as_used_seconds`.
- `SKILL.md` forbids reporting robust-at-floor as plain robust: a verdict already in the bottom band cannot be perturbed downward, so zero deciding flips there is band geometry, not evidence strength.

**Fixed**

- Install was broken for every user. The repo-level `.claude-plugin/marketplace.json` omitted the required top-level `owner`, and every plugin entry — this one included — used a remote source `{"source": "github", "repo": "QuantEcon/skills", "path": "benchmark"}` that forced an install-time SSH re-clone of this repo. All three entries switched to the co-located relative-path form (`"./benchmark"`), so install uses the marketplace copy already on disk: no SSH, no auth prerequisite. Surfaced by [@xuanguang-li](https://github.com/xuanguang-li) testing this plugin, [#10](https://github.com/QuantEcon/skills/issues/10).
- The verdict band is computed from the rounded total, so the band always agrees with the number shown — raw floating-point sums could land at 2.4999999999999996 for combinations that are exactly 2.50 (797 of 78125 score combinations affected).
- `matches_under_x64` now caps correctness on its own. The extra `max_delta_shipped > 1e-8` conjunct made the guard structurally unable to fire in exactly the "wrong economics masked by low precision" case it exists to catch — such a candidate scored correctness 5 / total 3.25; it now scores correctness 1 / total 2.30, gated to net regression.
- `score.py` validates evidence before scoring and refuses evidence that omits a scored input the gates read, or that marks a structural criterion met without a citation. A missing `baseline_as_used_seconds` silently disarmed the no-conversion verdict, and stripping every citation left the score unchanged.
- The headline metrics (as-used total, cold start) are persisted to `results/as_used.json` and `results/cold_start.json` with the derived speedup, instead of existing only on the console while the docstrings claimed aggregation.
- The sensitivity stamp's denominator is honest: perturbations that raise are recorded in `perturbations_skipped` rather than silently counted as tested.
- `run_all.py` hardened — JSON scalar stdout lines no longer abort the pipeline, per-step return codes are tracked, the as-used speedup derivation guards both sides, and duplicate mode keys warn instead of silently overwriting.
- ge_arrow's `check_equivalence.py` writes `equivalence_x64.json` under `JAX_ENABLE_X64` instead of clobbering the as-shipped results.
- ge_arrow static metrics double-counted concept-token hits via a duplicated pattern (informational metric; 110 → 105).
- markov_asset's `statements_for_one_asset` renamed to `statements_for_one_result` to match the evidence-template vocabulary (values unchanged).
- Two files that were CRLF (`references/EVALUATION_FRAMEWORK.md`, the ge_arrow report) are normalized to LF, so a future one-line edit no longer renders as a whole-file diff.

### benchmark 0.1.0 — 2026-07-07

First release: the plugin appears in the marketplace with a documented but not yet runnable evaluation procedure — a v0 outline skill, no executable scripts.

- `/benchmark:eval-py-acceleration` — a v0 outline of the acceleration-review procedure: the five steps (equivalence check, static metrics, as-used benchmark, seven-dimension scoring, report), the seven weights (readability 0.25 deliberately above efficiency 0.15), the verdict bands, and the two calibration anchors (aiyagari Bellman ~25x faster as-used = HIGH; ge_arrow ~45x slower as-used = LOW).
- The guiding principle a user is meant to apply: lectures are teaching materials first, so "uses JAX" is never a goal in itself.
- `scripts/README.md` listing the eight measurement scripts still to be collected from [lecture-python.myst#717](https://github.com/QuantEcon/lecture-python.myst/pull/717).

---

**There is no 0.2.0.** It existed on a branch inside [#5](https://github.com/QuantEcon/skills/pull/5) and was superseded within the same pull request; because the repo squash-merges, `main` went 0.1.0 → 0.3.0 in one commit and 0.2.0 was never published. Nothing is missing from this file.

## Historical — the `audit` plugin (folded into `qe` at 0.7.0)

Released 2026-07-27 to 2026-08-07 as the separate `audit` plugin; its skill lives on as `/qe:audit-issues`. Frozen as shipped, same convention as above (tags `audit--v0.2.0` etc.).

### audit 0.2.0 — 2026-08-07

The two severity-1 defects from the first measured run, which are the same defect at different altitudes: an audit's own record claiming more than it can support.

**Changed**

- **`[verified]` now requires evidence reachable from the ref the audit named.** Doctrine §2 is the single statement of it — §1 rule 1 no longer carries its own copy of the accepted-forms list, which is how the two drifted apart in the first place — and it covers every citation form — a commit must be an ancestor of the baseline ref, a `file:line` must be that line *on the ref* rather than in the working tree, a PR must be merged into it — and `/audit:issues` runs `git merge-base --is-ancestor <sha> <ref>` before tagging a commit citation. Run 1's headline finding cited a commit that is real, does touch the file, and exists only on an unmerged branch, while the report's header said it had verified against `main`. A citation that resolves for its author and not for its reader is worse than an untagged claim, because the tag is what invited the trust. Evidence that genuinely lives off-ref stays citable — as the open PR it is, tagged `[stated]` or `[inferred]`.
- **Phase 2 checkpoints both of its passes.** `findings.md` now carries `## Open` and `## Closed` sections, and the resume rule partitions `issues.json` by state and resumes each side independently at the lowest number with no entry. Run 1 wrote only the 56 open issues to the checkpoint and sent the 62 closed ones straight to the catalog, so a run interrupted during the closed pass would have re-verified all 62 from scratch while reporting itself complete — the single-block resume rule shipped in 0.1.2 could not see the difference.

### audit 0.1.4 — 2026-08-03

Doctrine §4's rule survived the first measured run; its justification did not. The section is re-derived from what that run actually produced, and the cost figures the skill quotes are replaced with measured ones.

**Changed**

- Doctrine §4 is renamed from "Surviving a long run" to "Checkpointing", and rests on three reasons that hold at any duration rather than on the claim that audits outlive sessions. The first measured run refuted that claim outright — 230 items in 22 minutes, with no context exhaustion, rate limit or sleeping machine in play. The strongest replacement reason is checkable: the per-item log is what the final enumeration is assembled *from*, and what a reviewer counts the coverage numbers against.
- `/audit:issues` no longer describes itself as "long-running by design — a hundred-issue repo is a multi-hour run". It now quotes the measured cost: roughly **10 seconds per open issue**, with a 230-item tracker carrying 56 open issues taking 22 minutes. Cost tracks open issues needing verification rather than total items, so a large tracker with a small open set is cheaper than a small one with a large set.
- The cost figures are stated so the two measures cannot be confused. Previously a reader met "roughly 10 seconds per open issue" beside "a 230-item tracker with 56 open took 22 minutes" and could not reconcile them — 56 × 10 s is 9 minutes, not 22. The 10-second rate is phase 2 alone; 22 minutes is end to end, and the remaining phases are largely fixed. Both numbers now say which question they answer.
- Checkpoint artifacts are named where they carry evidence rather than at every phase boundary out of symmetry — a checkpoint written and superseded minutes later without ever being read earns nothing.

### audit 0.1.3 — 2026-08-03

**Added**

- This changelog.

**Fixed**

- `/audit:issues`'s frontmatter `description` was an unquoted YAML plain scalar containing `Read-only: it recommends…`. A `: ` inside a plain scalar is a parse error, so a strict loader drops the skill's metadata rather than reading it, and `claude plugin validate` rejects the file outright. The value is now quoted. Nothing about the procedure changed.

### audit 0.1.2 — 2026-07-28

Resolves the contradiction that told an audit to write its bundle into the repo it promised not to touch: the boundary is now mutation, not writing, and the skill says exactly where to put its working directory so a run leaves `git status` clean.

**Added**

- Discovery-ordered working-directory selection, taken from contact with a real repo: prefer a location the repo already ignores (`.dev/scratch/audit-<YYYY-MM-DD>/` in QuantEcon repos, where `.dev/scratch/*` is already gitignored), fall back to an untracked `.audit/<repo>-<YYYY-MM-DD>/` at the checkout root, then to somewhere outside the checkout entirely. Which one was used goes in the report's method section.
- Doctrine §3 now says explicitly that a run may write its own working directory, including inside the audited checkout — provided the directory stays untracked and nothing is added to `.gitignore`, since that would itself be an edit to a tracked file.

**Changed**

- Doctrine §3 narrowed from "no branch or file changes in the audited repo" to what it was always protecting — content and history: no commits, no pushes, no branches, no edits to tracked files. Mutation, not writing, is the boundary.
- `deliverables.md` states the split: writing the bundle is the audit's job, committing or publishing it is a human step taken after reading it.

**Fixed**

- The read-only/working-directory contradiction the plugin carried since 0.1.0 — §3 forbade file changes in the audited repo while `deliverables.md` made that repo's own notes system the bundle's first-choice destination, and 0.1.1's default `--out` wrote there too. A run following the docs literally could not satisfy both.

### audit 0.1.1 — 2026-07-28

An interrupted run can actually be resumed: the intermediate artifacts now have names and locations, phase 2 appends per item instead of writing at the end, and the bundle shrinks to fit a small tracker.

**Added**

- A stated working-directory layout under `--out` (`.audit/<repo>-<YYYY-MM-DD>/` by convention): `snapshot/` from phase 1, `findings.md` from phase 2, `links.md` from phase 3, and the delivered `01-…`/`02-…`/`03-…`/`README.md` bundle from phase 4. Previously phases 2 and 3 produced "per-item findings" and "the cluster map" with no filename and no location, so resuming worked only if two sessions independently invented the same file.
- A stated resume rule: on restart, read `findings.md` and resume at the lowest number in `issues.json` with no entry, re-verifying the last entry rather than trusting a possibly truncated write.
- `meta.json` records `fetched_by`, the account the snapshot was taken as — which matters because visibility on the org's private repos is per-account.

**Changed**

- Phase 2 appends each item's finding to `findings.md` as it is verified, in the catalog entry format, so phase 4 assembles the catalog instead of re-deriving it.
- The bundle scales to the tracker: below roughly 30 open issues, fold the catalog and the link graph into the report, keep the `README.md` index, and say which shape was used in the coverage statement. Four unconditional documents forced three files of padding on a small tracker, and padding makes a report less checkable.
- Doctrine §4 now states the general rule: a checkpoint owes a findable name and incremental writes, or it is a claim about resumability rather than the property itself.

**Fixed**

- `meta["authenticated"]` is removed, not deprecated. It could only ever be `true` (preflight exits on every unauthenticated path), so it was a provenance field carrying no evidence — in the plugin whose doctrine is that every claim carries its evidence class. **Anything reading that field must switch to `fetched_by`.**
- An interrupted phase 2 now loses one item rather than the whole phase — it was the phase specified to write on completion, and the phase a hundred-item run dies inside rather than between.

### audit 0.1.0 — 2026-07-27

First release. `/audit:issues` sweeps an entire GitHub tracker — open and closed — verifies each item against the code rather than the thread, tiers the open set into the repo's existing plan, and delivers an evidence-cited report bundle, without ever touching the tracker.

- `/audit:issues <owner/repo>` — a whole-tracker audit in five phases (snapshot, per-item verification, cross-link graph, tiered report, coverage self-audit). The four runbook fields (plan anchor, tier scheme, repo type, notes system) are optional arguments with documented discovery, so the usual invocation is just the repo.
- A deterministic snapshot step, `scripts/fetch_tracker.py OWNER/REPO --out <dir>`: every issue and PR in any state with full comment threads (and PR reviews, and `closingIssuesReferences`) in two `gh` round trips, written as `meta.json`, `issues.json`, `prs.json`, `coverage.json`. Closed threads cost nothing extra to read, and the snapshot freezes the audit's point in time so "events after the snapshot" is a stated property of the report instead of an unnoticed gap.
- `coverage.json` reconciliation: captured items against the number sequence `1..max`, discussion counts split open/closed, and an explicit truncation flag when a stream returns exactly at `--limit` (default 1000) — a case indistinguishable from truncation, so it is surfaced rather than swallowed. PR review bodies count toward captured discussion, not just comments: on the example repo, closed PRs carried 374 reviews against 28 comments.
- Snapshot files are written in issue/PR number order, so two runs over an unchanged tracker are byte-identical and a re-fetch diffs down to what actually changed.
- Thread payloads are shape-asserted at capture, so a `gh` build returning counts instead of lists fails by name at the point of capture rather than crashing later or silently under-reporting threads while the report still claims thread-completeness.
- Preflight that refuses to start without `gh` and an authenticated account, because the anonymous API is 60 req/h per IP and returns nothing at all for the org's private repos.
- Plugin-level method shared by every future audit skill: `references/doctrine.md` (trust rules, evidence classes `[verified]`/`[stated]`/`[inferred]`, the read-only boundary, checkpointing, the coverage self-audit), `references/quantecon-context.md` (repo types, label ownership, the cross-repo graph, access, and the caveat that an HTML-reconstructed thread may start mid-conversation), and `references/deliverables.md` (what an audit owes its reader, and where a bundle may land).
- QuantEcon-specific triage judgement: tier by repo type (a build break in a lecture repo and a consumer-visible change in an action repo outrank thread activity), check sibling repos before concluding, leave label application to `qe`, and keep GitHub closing keywords out of drafted cross-repo references so drafted text cannot close an upstream item when someone posts it.
- The four-document bundle, the five phases and "produces a bundle" are stated as a worked example rather than a requirement, after a single execution. What an audit owes its reader — coverage statement, evidence tag per claim, recommendations marked as proposals, drafted comments marked unsent, a date and a named snapshot — stays mandatory and presumes no file count.
