# Validation run — `/audit:issues` on `QuantEcon/action-translation` (2026-07-28)

Run 1 of the validation program in [skills#16](https://github.com/QuantEcon/skills/issues/16): the first execution of `/audit:issues` **as a skill**. Every prior execution was by hand, as a runbook, so the plugin's method was generalised from a single manual pass. This run tests it.

Unlike the [ge_arrow validation run](validation-run-ge_arrow-2026-07-22.md), there is no committed reference to reproduce — the point is not that a number comes back the same, but whether the procedure holds and whether the output is worth acting on.

**Result: the bundle is good and the plugin has seven defects**, one of them in the checkpoint fix shipped the day before ([#17](https://github.com/QuantEcon/skills/pull/17)). The single most important claim — resumability — remains untested, because the run was not interrupted.

## Setup

| | |
|---|---|
| Repo | `QuantEcon/action-translation` — `action-*` family, the `.dev/` convention pilot |
| Plugin | `audit` 0.1.2, installed from the `quantecon` marketplace (user scope) |
| Snapshot | `2026-07-28T06:45:58Z`, `fetched_by: mmcky`, `gh` 2.96.0 |
| Verified against | `main` @ `2c3d624` (v0.24.0 + 17 commits) |
| Working directory | `.dev/scratch/audit-2026-07-28/` — gitignored via `.dev/scratch/*` |
| Invocation | `/audit:issues QuantEcon/action-translation --out .dev/scratch/audit-2026-07-28` |
| Captured | 118 issues + 112 PRs = 230 items, numbers 1–230, **0 unaccounted**, no truncation |

## Cost — the docs are wrong by an order of magnitude

| Phase | Completed | Elapsed |
|---|---|---|
| 1 — snapshot | 16:45:59 | ~11 s |
| 2 — verify (56 open issues) | 16:54:57 | ~9 min |
| 3 — relate | 16:58:24 | ~3 min |
| 4 — write (3 documents + index) | 17:08:05 | ~10 min |
| **Total** | | **~23 min** for 230 items |

[`audit/README.md`](../audit/README.md) says *"Expect hours, not minutes, on a repo with a hundred items"*; [`SKILL.md`](../audit/skills/issues/SKILL.md) says *"a hundred-issue repo is a multi-hour run"*. Both are wrong by roughly an order of magnitude on this repo.

This is uncomfortable rather than merely inaccurate, because it partly undercuts its own machinery. [doctrine §4](../audit/references/doctrine.md) justifies phase checkpointing on the premise that *"bulk audits outlive sessions"*. At 23 minutes they do not. Checkpointing is not thereby worthless — a 1000-item tracker scales up, interruption remains possible, and the incremental log turned out to be independently useful as an audit trail — but the stated *reason* is false and should be corrected rather than quietly retained. See defect 4.

## The claims under test

| # | Claim | Verdict |
|---|---|---|
| 1 | Method section names every discovered input | **Held.** Repo type, notes system, work-plan anchor (#198), label policy, prior audits, working directory — all named with what each resolved to |
| 2 | Every claim carries an evidence class | **Held.** Tags used throughout; `findings.md` restates the doctrine §2 legend in its header |
| 3 | `[verified]` means verified | **BROKEN** — see defect 1 |
| 4 | Code beat the thread | **Held.** Independently confirmed: PR #197 (`bb10ce0`) never touched `docs/user/heading-maps.md`, as the audit claims |
| 5 | The closed side was read | **Held in output, broken in checkpoint** — see defect 2 |
| 6 | Coverage is honest | **Held, exactly.** The index's coverage table matches `coverage.json` on every number. Six-item residue, one flagged as potentially conclusion-changing. *"Bounds this audit placed on itself: none by sampling"* |
| 7 | Read-only boundary | **Held.** `git status --short` empty after writing ~127 KB into the repo. The discovery-ordered working directory from [#19](https://github.com/QuantEcon/skills/pull/19) works as designed |
| 8 | Drafted comments are safe | **Held.** Zero closing keywords before any cross-repo reference; four drafted comments all marked **unsent** |
| 9 | Is the tiering right? | *Maintainer's call — pending* |
| 10 | Would you act on it? | *Maintainer's call — pending* |

## Interruption test — not performed

Tutorial step 4 asks the operator to interrupt phase 2 once 20–30 findings exist and restart. The run went straight through, so **resumability is still unvalidated**. `findings.md` shows a single clean pass with no duplicate or missing entries, which demonstrates that the checkpoint *materialises* — a real gain, since before #17 phases 2 and 3 named no artifacts at all — but not that resuming from it works.

Defect 2 makes this worse than a neutral gap: the resume rule as written would have misbehaved had the run died in the closed-set pass.

## Defects found

1. **A `[verified]` citation that does not verify, on the headline finding.** The #91 wave-escape entry cites `b99b431` as where `docs/user/heading-maps.md`'s history ends. That commit is real and does touch the file — but it is **not on `main`**; it exists only on `origin/fix/heading-map-position-fallback`, unmerged, dated 2026-03-24. The last commit touching that path on `main` is `0ea2539`. The audit's own header says "verified against `main` @ `2c3d624`". The conclusion survives independent checking and is arguably strengthened, but a reviewer who checks the citation finds nothing — worse than no citation. [doctrine §2](../audit/references/doctrine.md) says cite `file:line`, a merged PR, or a tag; it never says *confirm the commit is an ancestor of the ref you named*. One `git merge-base --is-ancestor` closes it.

2. **The closed side was never checkpointed.** `findings.md` contains one section — `## Open issues`, 56 entries. The 62 closed issues were verified and appear in the catalog, but went straight to the deliverable. Half the phase-2 work sat outside the checkpoint, and it breaks the resume rule from #17: *"resume at the lowest number in `issues.json` with no entry"* would have re-verified all 62 closed issues from scratch. A defect in the fix, found by running it.

3. **The bundle landed where it cannot be delivered.** [`deliverables.md`](../audit/references/deliverables.md) names `.dev/audits/<date>-<subject>/` as the destination; the bundle is in `.dev/scratch/`, which is gitignored — so it cannot be committed where it sits. The run correctly followed SKILL.md's working-directory table, which lists the bundle under `--out`. SKILL.md and deliverables.md now contradict each other, introduced by #17. The convention side is now a suggestion at [QuantEcon.manual#140](https://github.com/QuantEcon/QuantEcon.manual/issues/140).

4. **The cost claim is wrong** (see above), and with it doctrine §4's stated justification for checkpointing.

5. **Provenance links point at a machine-local plugin cache.** The bundle cites `../../../.claude/plugins/cache/quantecon/audit/0.1.2/references/doctrine.md` — dead for every other reader, in a document intended to be committed into the audited repo. `deliverables.md` never says how a bundle should cite the plugin; it should be a GitHub URL pinned to the version.

6. **Preflight does not check token scopes.** The one gap that could change conclusions — Projects v2 membership — came from a token lacking `read:project`. The run handled it correctly: stated in the residue, flagged as conclusion-changing rather than additive, with `gh auth refresh -s read:project` named as the fix. But `fetch_tracker.py` could detect it in the first minute instead of surfacing it at the end.

7. **The concluding summary over-claimed one citation.** It reported `selectForwardCandidates` "citing the issue number in its docstring"; the `#106` references are in `src/cli/__tests__/forward-discovery.test.ts`, a test file. The substance holds; the location does not.

## What the doctrine did and did not transfer

Three different verdicts, and only the third is a bug.

**Cited and load-bearing.** Rule 1 (verify against the branch, not the thread) produced the run's most valuable finding. Rule 3 (read closed threads) produced the #117 remainder finding, which is invisible from the open set. Rule 7 (diff against prior audits) worked and correctly reported *convergence* rather than manufacturing novelty — the audit's willingness to say "this corroborates the prior audit rather than adding to it" is a good sign. §2's evidence classes and §5's residue discipline both survived contact. §3's read-only boundary held, and the [#19](https://github.com/QuantEcon/skills/pull/19) working-directory rule delivered exactly what it promised.

**Never came up.** Rule 6 (draft policies are conditional) was applied to QEP-2 but did no work, because the repo's labels already carry QEP-shaped descriptions. Rule 4 (guarded vs fixed) was not visibly exercised. Neither is evidence against the rule — this is one repo of one type.

**Had to be worked around.** §4's phase division assumes phases long enough to be worth checkpointing; at 23 minutes the ceremony exceeded the need, and the checkpoint that was written covered only half the phase (defect 2). The bundle destination could not be honoured at all (defect 3).

## Quality assessment

The four headline findings map onto the categories doctrine says to hunt: a wave escape (#91), two fixed-but-open (#89, #106), and a closed-with-remainders (#117). It surfaced one time-sensitive operational risk — PR #225, open and mergeable, with a measurement in #227 showing it regresses the path it touches from 93.3% to 33.3% structural pass at p = 0.002, a measurement that lives in an issue rather than on the PR a reviewer would act from.

Its framing is the part hardest to specify and easiest to lose: *"this tracker is in unusually good shape … what this audit found is not rot but four places where the record and the code have come apart, which in a tracker this trusted is the more dangerous failure."* An audit that reports a healthy tracker honestly, and then explains why its findings still matter, is doing the job.

## Follow-up

Defects are tracked at [skills#21](https://github.com/QuantEcon/skills/issues/21). The `.dev/audits/` convention question is at [QuantEcon.manual#140](https://github.com/QuantEcon/QuantEcon.manual/issues/140). Run 2 should be interrupted deliberately, since run 1 left the program's headline claim untested.
