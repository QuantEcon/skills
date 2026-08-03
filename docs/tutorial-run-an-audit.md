# Tutorial: run a whole-tracker audit

This walks `/audit:issues` end to end against **[QuantEcon/action-translation](https://github.com/QuantEcon/action-translation)** — 228 items, the repo the runbook was first executed against by hand.

It differs from the [evaluation tutorial](tutorial-run-an-evaluation.md) in one important way. That one reproduces a committed reference, so every number you produce can be checked. Here there is no reference: `/audit:issues` has been run as a skill exactly **once** — run 1, against this same repo on 2026-07-28, which found seven plugin defects and is recorded [here](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-action-translation-2026-07-28.md). A method generalised from one execution is still a hypothesis, so your run is the next data point in the validation program ([skills#16](https://github.com/QuantEcon/skills/issues/16)), and the part no automation can supply is your judgement of the output. Step 6 is therefore not optional garnish — it is the result.

Canonical references (this tutorial points, never restates): the procedure in [SKILL.md](../audit/skills/issues/SKILL.md), the method in [doctrine.md](../audit/references/doctrine.md), the org conventions in [quantecon-context.md](../audit/references/quantecon-context.md), the output contract in [deliverables.md](../audit/references/deliverables.md).

## What you need

- The `audit` plugin installed (Step 0). It is deliberately not in the lecture-repo auto-install block — it is maintainer tooling.
- `gh` authenticated. Preflight refuses to start without it, because the anonymous API returns nothing for the org's private repos and is capped at 60 requests/hour.
- A checkout of the audited repo. Phase 2 verifies claims against its default branch, so a tracker-only run cannot do the job.
- **Tens of minutes**, and a session you can afford to interrupt — interrupting it is one of the tests. Run 1 took 22 minutes end to end for 230 items, of which phase 2 was about 9 — roughly 10 seconds for each of its 56 open issues. Budget the total, and scale it by the *open* count rather than the item count.

## Step 0 — install the plugin

```bash
claude plugin marketplace add QuantEcon/skills
claude plugin install audit@quantecon
```

**Then restart your session** — plugins register at startup, so the skill does not appear until you reopen.

The `/plugin marketplace add …` slash form does the same job, but it is a *terminal-CLI built-in*: the VS Code extension and the web app answer `/plugin isn't available in this environment`, while the `claude plugin` CLI above works from any shell. Confirm with `claude plugin list` — the version it reports should match the `audit` entry in [`marketplace.json`](../.claude-plugin/marketplace.json). (Naming a number here would go stale on the next release; if the two disagree, the install did not pick up the latest — `claude plugin update audit@quantecon`.)

If `/audit:issues` is still unrecognised after restarting, the plugin-prefixed slash form needs Claude Code 2.1.216+; the bare `/issues` works on older builds, and natural-language invocation ("audit every issue in this repo, output to …") works on any version ([using-skills § troubleshooting](using-skills.md#updating-and-troubleshooting)).

## Step 1 — put the working directory where the repo already ignores it

```bash
cd ~/work/quantecon/action-translation
git checkout main && git pull --ff-only   # phase 2 verifies against the DEFAULT branch
git status --short                        # must be empty — the read-only baseline
git check-ignore -v .dev/scratch/x        # → .gitignore:… .dev/scratch/*
```

**Be on the default branch, not merely clean.** Phase 2's core question is whether an issue still reproduces on `main`; run from a feature branch and every answer is measured against your unmerged work instead. A clean tree on the wrong branch passes the `git status` check and silently invalidates the phase the whole run exists to test — so check the branch, not just the status.

`action-translation` has a `.dev/` notes system whose `.dev/scratch/*` is already gitignored, which makes it the first-choice working directory: the run leaves `git status` completely clean, and no `.gitignore` edit is needed — that would itself be a change to a tracked file. Repos without one fall back to an untracked `.audit/` at the root ([SKILL.md § Working directory](../audit/skills/issues/SKILL.md)).

## Step 2 — invoke

```
/audit:issues QuantEcon/action-translation --out .dev/scratch/audit-2026-07-28
```

Before phase 1 the skill *discovers* its inputs rather than asking for them: the notes system (here `.dev/` — `STATE.md`, `PLAN.md`, `FUTURE.md`, `decisions/`), the label policy, the work-plan anchor to tier against, and any prior audits. It should ask you only where discovery is genuinely ambiguous — two plausible plan anchors, say — and never merely because something came up empty. **Every resolved input must appear in the report's method section**; that is the first thing to check in Step 6.

## Step 3 — phase 1, the snapshot (~11 seconds)

Deterministic, and the only phase driven by a script rather than judgement. Measured 2026-07-27:

```
fetching issues from QuantEcon/action-translation …
  116 issues
fetching pull requests from QuantEcon/action-translation …
  112 pull requests

  numbers 1..228: 228 accounted, 0 unaccounted
  open issues     55    49 comments across 30
  closed issues   61    80 comments across 32
  open PRs         2    2 comments across 1, 5 reviews across 2
  closed PRs     110    28 comments across 18, 377 reviews across 105
```

Three things to read off it. **`0 unaccounted`** means every number in `1..228` was captured — a non-zero count is not automatically wrong (deleted or transferred items, PR numbers burned by branches that never opened) but each one now owes an explanation in Step 5. **No truncation warning** — a stream returning exactly at `--limit` is indistinguishable from a truncated one. And **`meta.json`'s `fetched_by` should be you**, since visibility is per-account.

Your counts will differ from the ones above — the tracker moves (#11 measured 111/110 in July). That is expected and is why the report quotes its own snapshot timestamp rather than an earlier count.

## Step 4 — phase 2, verify — and interrupt it

The long phase: 116 items checked against the default branch rather than against what their threads claim. Findings are appended to `findings.md` **one entry per item, as each is verified**.

**This is the test.** Once 20–30 entries exist, interrupt the session — close it, or press Esc twice. Then open a new session in the same directory and re-invoke the same command. What should happen: it reads `findings.md`, resumes at the lowest issue number with no entry, and re-verifies only the last entry (which may have been half-written). What would be a failure: restarting from item 1, skipping the item it died on, or duplicating entries.

Resumability is asserted in three separate files and has never been tested. Until this run, phases 2 and 3 named no artifacts at all, so a resumed session could only work if it happened to invent the same filename — the fix is [#17](https://github.com/QuantEcon/skills/pull/17), and this is what checks it.

While it runs, `tail findings.md` occasionally. Every status claim should carry `[verified]`, `[stated]` or `[inferred]`, and a `[verified]` should cite `file:line`, a merged PR, or a tag — never a comment.

## Step 5 — phases 3 to 5

Phase 3 writes the cross-link graph to `links.md`. Phase 4 tiers into the plan it discovered in Step 2 and writes the bundle. Phase 5 reconciles against `coverage.json` and folds any correction *back into* the documents rather than appending an erratum.

With 55 open issues this run should produce the **full four-document bundle**; a repo under about 30 open issues should instead fold the catalog and links into the report. That threshold is new and untested, so note whether four documents felt right at 55 or merely dutiful. The bundle's destination is `.dev/audits/<date>-issues/` — the audit writes it there, but **committing it is your call, not the run's**.

## Step 6 — review the output

The run cannot check any of this about itself. Ten checks, the last two of which only you can make:

| # | Check | Where to look | What failure looks like |
|---|---|---|---|
| 1 | Method section is complete | report §1 | The plan anchor, label policy and prior-audit search are not all named |
| 2 | Every claim is tagged | catalog entries | An untagged status claim — a defect by the doctrine's own rule |
| 3 | `[verified]` means verified | sample 5 "fixed" calls | Citation is a thread comment rather than code, a merged PR, or a tag |
| 4 | Code beat the thread | sample 5 more | The report repeats "fixed in #204" without saying it checked the branch |
| 5 | The closed side was read | closed-set verification | Closed issues summarised from title and `stateReason` only; no deferred remainders surfaced |
| 6 | Coverage is honest | `README.md` index | Unaccounted numbers waved at collectively; residue (inline review comments, GraphQL-only data) not stated |
| 7 | Siblings were checked | external cross-link registry | No sibling considered, in an org where the same fix lands in several repos as `SYNC:` PRs |
| 8 | Drafted comments are safe | GC tier | A closing keyword immediately before an `owner/repo#N` reference — that closes the *upstream* item when it lands |
| 9 | **Is the tiering right?** | report tiering section | T0 that isn't this week's work, or a tier list not actually tied to `.dev/PLAN.md`. You are the authority; the run is guessing |
| 10 | **Would you act on it?** | the whole bundle | The only check that matters, and the only one no self-audit can make |

Then confirm the boundary held: `git status --short` shows nothing but your ignored working directory, and the tracker is unchanged — no comments, no labels, no closures.

## Step 7 — record the run

Findings belong in this repo; the bundle does not. Write `reviews/audit-run-action-translation-2026-07-28.md`, following the [ge_arrow validation run](../reviews/validation-run-ge_arrow-2026-07-22.md):

- **Setup** — repo, snapshot timestamp, `fetched_by`, item counts, unaccounted numbers, plugin version.
- **Cost** — wall clock and rough token spend per phase. Run 1's figures are in [its record](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-action-translation-2026-07-28.md); a second data point at a different repo type is what turns one measurement into an estimate.
- **The ten checks** from Step 6, each held or broken, with the evidence.
- **Interruption log** — where you killed it, what resuming actually did.
- **What the doctrine did and did not transfer** — the payload. A rule that was cited and load-bearing, a rule that never came up, and a rule the run had to work around are three different verdicts, and only the third is a bug.
- **Your read of the bundle** — checks 9 and 10 in prose.

Post the summary to [skills#16](https://github.com/QuantEcon/skills/issues/16). Anything that broke becomes an issue against the plugin, not a note in the margin.
