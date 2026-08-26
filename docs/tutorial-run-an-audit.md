# Tutorial: run a whole-tracker audit

This walks `/qe:audit-issues` end to end against **[QuantEcon/action-translation](https://github.com/QuantEcon/action-translation)** — 228 items, the repo the runbook was first executed against by hand.

It differs from the [evaluation tutorial](tutorial-run-an-evaluation.md) in one important way. That one reproduces a committed reference, so every number you produce can be checked. Here there is no reference. `/qe:audit-issues` has been run as a skill **twice**: run 1 against this same repo on 2026-07-28, which found seven plugin defects ([record](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-action-translation-2026-07-28.md)), and run 2 against `QuantEcon/meta` on 2026-08-25 — 317 items, 138 open — which was deliberately killed mid-run and **resumed correctly**, settling the claim the program exists to check ([record](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-meta-2026-08-25.md)). Two points still make a method a hypothesis, so your run is the next data point in the validation program ([skills#16](https://github.com/QuantEcon/skills/issues/16)), and the part no automation can supply is your judgement of the output. Step 6 is therefore not optional garnish — it is the result.

**What run 3 should target**, since run 2 closed the obvious gaps: interrupt **mid-write** (run 2's kill left a clean entry, so the truncation guard has never fired) and interrupt **inside the closed pass** (run 2's kill landed in the open pass, and the closed pass turns out not to be incrementally checkpointed at all — [#57](https://github.com/QuantEcon/skills/issues/57)).

Canonical references (this tutorial points, never restates): the procedure in [SKILL.md](../qe/skills/audit-issues/SKILL.md), the method in [doctrine.md](../qe/references/audit/doctrine.md), the org conventions in [quantecon-context.md](../qe/references/audit/quantecon-context.md), the output contract in [deliverables.md](../qe/references/audit/deliverables.md).

## What you need

- The `qe` plugin installed (Step 0). Since the [#43](https://github.com/QuantEcon/skills/issues/43) consolidation in qe 0.7.0 there is no separate `audit` plugin: the plugin is the enable unit, so any repo that opts into `qe` gets this maintainer tooling alongside the author-facing skills.
- `gh` authenticated. Preflight refuses to start without it, because the anonymous API returns nothing for the org's private repos and is capped at 60 requests/hour.
- A checkout of the audited repo. Phase 2 verifies claims against its default branch, so a tracker-only run cannot do the job.
- **Tens of minutes**, and a session you can afford to interrupt — interrupting it is still one of the tests. Run 1 took 22 minutes end to end for 230 items, of which phase 2 was about 9 — roughly 10 seconds for each of its 56 open issues. Run 2 took ~53 minutes for 317 items and 138 open, including its interruption gap. Both the open count (2.5×) and the elapsed time (~2.4×) scaled together, so **scale your budget by the *open* count rather than the item count** — now on two points rather than one.

## Step 0 — install the plugin

```bash
claude plugin marketplace add QuantEcon/skills
claude plugin install qe@quantecon
```

**Then restart your session** — plugins register at startup, so the skill does not appear until you reopen.

The `/plugin marketplace add …` slash form does the same job, but it is a *terminal-CLI built-in*: the VS Code extension and the web app answer `/plugin isn't available in this environment`, while the `claude plugin` CLI above works from any shell. Confirm with `claude plugin list` — the version it reports should match the `qe` entry in [`marketplace.json`](../.claude-plugin/marketplace.json). (Naming a number here would go stale on the next release; if the two disagree, the install did not pick up the latest — `claude plugin update qe@quantecon`.)

If `/qe:audit-issues` is still unrecognised after restarting, the plugin-prefixed slash form needs Claude Code 2.1.216+; the bare `/audit-issues` works on older builds, and natural-language invocation ("audit every issue in this repo, output to …") works on any version ([using-skills § troubleshooting](using-skills.md#updating-and-troubleshooting)).

## Step 1 — put the working directory where the repo already ignores it

```bash
cd ~/work/quantecon/action-translation
git checkout main && git pull --ff-only   # phase 2 verifies against the DEFAULT branch
git status --short                        # must be empty — the read-only baseline
git check-ignore -v .dev/scratch/x        # → .gitignore:… .dev/scratch/*
```

**Be on the default branch, not merely clean.** Phase 2's core question is whether an issue still reproduces on `main`; run from a feature branch and every answer is measured against your unmerged work instead. A clean tree on the wrong branch passes the `git status` check and silently invalidates the phase the whole run exists to test — so check the branch, not just the status.

`action-translation` has a `.dev/` notes system whose `.dev/scratch/*` is already gitignored, which makes it the first-choice working directory: the run leaves `git status` completely clean, and no `.gitignore` edit is needed — that would itself be a change to a tracked file. Repos without one fall back to an untracked `.audit/` at the root ([SKILL.md § Working directory](../qe/skills/audit-issues/SKILL.md)).

**Check that fallback before you take it.** Run 2 exposed the gap ([#61](https://github.com/QuantEcon/skills/issues/61)): the rule's stated goal is that a run leaves `git status` clean, but an untracked `.audit/` *does* show in `git status` unless the repo ignores that path — and `meta` has no `.gitignore` at all. The consequence there was 2.4 MB of findings, including AWS and access-token material, sitting untracked in a public checkout until moved by hand. If `git check-ignore .audit/x` comes back empty, put the working directory **outside the checkout** instead — `~/work/quantecon/_audits/<date>-<owner>-<repo>-issues/` is the convention run 2 settled on.

## Step 2 — invoke

```
/qe:audit-issues QuantEcon/action-translation --out .dev/scratch/audit-2026-07-28
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

The long phase: 116 items checked against the default branch rather than against what their threads claim. The guarantee is that findings are appended to `findings.md` **one entry per item, as each is verified** — both passes, the open issues under `## Open` and the closed ones under `## Closed` — so an interrupted run loses one item rather than the phase. Run 2 measured that it holds on the open side and not the closed one; see below.

**This is still the test, and it now has an expected answer.** Once 20–30 entries exist, interrupt the session — close it, or press Esc twice. Then open a new session in the same directory and re-invoke the same command. What should happen: it partitions `issues.json` by state and, for each side independently, resumes at the lowest number with no entry under the matching heading, re-verifying only the last entry in each (which may have been half-written). What would be a failure: restarting from item 1, skipping the item it died on, duplicating entries, or resuming the open set correctly while re-doing the closed set from scratch.

**Write your prediction down before you resume** — the lowest un-entered number on each side, and the file's byte count. Run 2 did exactly this, predicted `#261`, and got it: the pre-kill bytes were byte-identical afterwards, so the resume was a pure append. A prediction recorded after the fact is not evidence.

**Interrupt during the closed pass too, if you get the chance** — that is the half nothing has ever resumed from, and run 2 found out why. It sampled `findings.md` throughout and measured the write pattern: 15+ checkpoint writes across the 138 open items, in batches of 8–9 every 75–120 s, against **exactly one** write for all 179 closed ones — the complete section in a single flush at the end. [#34](https://github.com/QuantEcon/skills/pull/34) fixed the *format* (the `## Closed` heading and the two-partition resume rule) and left the *granularity* untouched, so an interrupt anywhere in the closed survey still loses the phase rather than one item, and the resume rule's address-by-issue-number is not well-defined against `deliverables.md`'s grouped entries anyway. That is [#57](https://github.com/QuantEcon/skills/issues/57), open. Expect the closed pass to restart from scratch until it lands — and if you can, sample `findings.md` while it runs so run 3 measures the pattern rather than inferring it.

While it runs, `tail findings.md` occasionally. Every status claim should carry `[verified]`, `[stated]` or `[inferred]`, and a `[verified]` should cite `file:line`, a merged PR, a tag, or a commit — **and whatever it cites must resolve on the ref the audit named**, never a comment. A citation that only resolves in the author's working tree or on an unmerged branch is the defect [doctrine §2](../qe/references/audit/doctrine.md#2-evidence-classes) now rules out; run 1's headline finding had exactly that shape.

## Step 5 — phases 3 to 5

Phase 3 writes the cross-link graph to `links.md`. Phase 4 tiers into the plan it discovered in Step 2 and writes the bundle. Phase 5 reconciles against `coverage.json` and folds any correction *back into* the documents rather than appending an erratum.

With 55 open issues this run should produce the **full four-document bundle**; a repo under about 30 open issues should instead fold the catalog and links into the report. That threshold is still untested — run 2's 138 open issues did not bind it either — so note whether four documents felt right at 55 or merely dutiful. The bundle's destination is `.dev/audits/<date>-issues/` where a notes system exists; where one does not, keep it wherever Step 1 put the working directory. Either way **committing it is your call, not the run's** — and read it before you decide: run 2's bundle carried AWS and access-token findings that belonged in a different repo than the one audited.

## Step 6 — review the output

The run cannot check any of this about itself. Ten checks, the last two of which only you can make:

| # | Check | Where to look | What failure looks like |
|---|---|---|---|
| 1 | Method section is complete | report §1 | The plan anchor, label policy and prior-audit search are not all named |
| 2 | Every claim is tagged | catalog entries | An untagged status claim — a defect by the doctrine's own rule |
| 3 | `[verified]` means verified | sample 5 "fixed" calls, and **resolve each on the ref named in the header** | Citation is a thread comment rather than code — or a citation of any form that looks right and does not resolve on that ref. `git merge-base --is-ancestor <sha> <ref>` on any commit cited. This is the check run 1 passed and should not have |
| 4 | Code beat the thread | sample 5 more | The report repeats "fixed in #204" without saying it checked the branch |
| 5 | The closed side was read | closed-set verification, **and `findings.md`** | Closed issues summarised from title and `stateReason` only; no deferred remainders surfaced. Also check the checkpoint, not just the output: closed entries reaching the catalog with no matching `## Closed` block is how run 1 passed this check in its report while failing it in its log |
| 6 | Coverage is honest | `README.md` index | Unaccounted numbers waved at collectively; residue (inline review comments, GraphQL-only data) not stated |
| 7 | Siblings were checked | external cross-link registry | No sibling considered, in an org where the same fix lands in several repos as `SYNC:` PRs |
| 8 | Drafted comments are safe | GC tier | A closing keyword immediately before an `owner/repo#N` reference — that closes the *upstream* item when it lands |
| 9 | **Is the tiering right?** | report tiering section | T0 that isn't this week's work, or a tier list not actually tied to `.dev/PLAN.md`. You are the authority; the run is guessing |
| 10 | **Would you act on it?** | the whole bundle | The only check that matters, and the only one no self-audit can make |

Then confirm the boundary held — and **measure it rather than eyeballing it**. `git status --short` should show nothing but your ignored working directory, and `HEAD` should be unmoved. For the tracker, fingerprint it before and after: number, state, `updated_at`, comment count and labels for every issue, hashed. Any close, label or comment moves `updated_at` on the affected issue, so identical hashes turn the doctrine's read-only promise into a measurement for the cost of two `gh` calls. Run 2 did this first and recommends it become a standard step ([#59](https://github.com/QuantEcon/skills/issues/59)); take the baseline *before* invoking, which is the one thing run 2 got slightly wrong.

## Step 7 — record the run

Findings belong in this repo; the bundle does not. Write `reviews/audit-run-<repo>-<date>.md` — run 1's is [audit-run-action-translation-2026-07-28.md](../reviews/audit-run-action-translation-2026-07-28.md) — following the shape of the [ge_arrow validation run](../reviews/validation-run-ge_arrow-2026-07-22.md):

- **Setup** — repo, snapshot timestamp, `fetched_by`, item counts, unaccounted numbers, plugin version.
- **Cost** — wall clock and rough token spend per phase, against [run 1](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-action-translation-2026-07-28.md) and [run 2](https://github.com/QuantEcon/skills/blob/main/reviews/audit-run-meta-2026-08-25.md). Two points support the open-count scaling rule but do not establish a rate, and run 2's total includes an interruption, so it bounds rather than measures.
- **The ten checks** from Step 6, each held or broken, with the evidence.
- **Interruption log** — where you killed it, the prediction you recorded beforehand, and what resuming actually did. Run 2's is the shape to follow: state at kill captured externally, prediction written down, then a table of expectation against result.
- **The read-only fingerprint** — the before and after hashes, per Step 6.
- **What you discarded** — candidate findings you investigated and could not support. A validation report that lists only confirmed findings hides its own false-positive rate; run 2 records two.
- **What the doctrine did and did not transfer** — the payload. A rule that was cited and load-bearing, a rule that never came up, and a rule the run had to work around are three different verdicts, and only the third is a bug.
- **Your read of the bundle** — checks 9 and 10 in prose.

Post the summary to [skills#16](https://github.com/QuantEcon/skills/issues/16). Anything that broke becomes an issue against the plugin, not a note in the margin.
