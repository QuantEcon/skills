# Audit run 2 — `QuantEcon/meta`, 2026-08-25

Second run in the [`/qe:audit-issues` validation program](https://github.com/QuantEcon/skills/issues/16), and the
first run of the skill under its consolidated name (`qe` 0.7.0; run 1 was `audit` 0.1.x). Its headline purpose was
to falsify the one claim the program exists to check and run 1 left untested: **does an interrupted run resume
correctly across a lost session?**

Run 1's record, for comparison throughout, is
[`audit-run-action-translation-2026-07-28.md`](audit-run-action-translation-2026-07-28.md).

**Method note.** The run was executed by the maintainer in a Claude Code session. A second, independent session
observed it from outside — sampling `findings.md` every 15–20 seconds, fingerprinting the tracker before and
after, and recording a prediction of the resume point *before* the resume happened. That external observation is
what produced the findings in §5; none of them is visible in the finished bundle. Recommended for run 3.

**Citations are pinned to `qe--v0.7.0`** — the tag whose tree this run actually executed — so every quoted
guarantee stays checkable against the same artifact even after the skill changes. A run record whose citations
drift is the defect run 1 was faulted for, one level up.

## 1. Snapshot provenance

| Field | Value |
|---|---|
| Repo | `QuantEcon/meta` (public) |
| `snapshot_utc` | `2026-08-25T05:49:04+00:00` |
| `gh_version` | 2.98.0 (2026-08-20) |
| `fetched_by` | mmcky |
| Baseline ref | `origin/main` @ `58d577d` |
| Captured | 317 issues, 23 PRs, 340 items; highest number 368 |
| Open / closed | 138 / 179 |
| Unaccounted numbers | 28, **all 28 explained** (8 transferred to other repos, 20 converted to Discussions) |
| Truncation | none — `issues_at_limit: false`, `prs_at_limit: false` |

The plan's stored figures (161 open / 319 items, measured 2026-08-07) had drifted; 138 / 317 is the measurement at
run time. Worth noting for estimates: a stored open-count ages faster than the total.

## 2. Cost and duration

| Measure | Value |
|---|---|
| Wall clock, snapshot → final bundle file | ~53 minutes |
| — of which | one operator-controlled interruption gap of unmeasured length |
| Resumed session, at the "closed batch D" mark | 19m 0s, 60.5k tokens |
| Open pass, observed rate | 138 items; 85 → 138 in 652s of the sampled window |
| Bundle | `README.md` 7.5K, `01-` 17K, `02-` 155K, `03-` 10K, plus `findings.md` 117K and `snapshot/` |

Against run 1 — 230 items, 56 open, 22 minutes — this run was 317 items and 138 open in roughly 53 minutes.
Both the open count (2.5×) and the elapsed time (~2.4×) scaled together, which is consistent with run 1's
conclusion that *the open-issue count is what scales*, now supported by a second point rather than one. It is
still two points on a line, and this run's total includes an interruption, so it bounds rather than establishes
the rate.

**The "expect hours, not minutes" claim that run 1 corrected stays corrected.** A 317-item tracker with 138 open
issues finished inside an hour including a full restart.

## 3. Claims under test

Each row is [#16's claims table](https://github.com/QuantEcon/skills/issues/16), marked against what this run
actually produced.

| Claim | Verdict | Evidence |
|---|---|---|
| Resumes across a lost session | **HELD** | Resumed at `#261` — the predicted point, recorded before the fact. See §4. |
| Thread-complete on the closed side | **HELD** | All 179 closed threads read; 194 comments on open issues, 416 on closed, 131 comments + 10 review bodies on PRs. Five closed-side defects found that exist *only* in threads (§6). |
| Every claim carries an evidence class | **HELD** | 176 evidence tags across 138 catalogued open issues — 9 `[verified]`, 97 `[verified live]`, 61 `[stated]`, 9 `[inferred]`. No untagged status line found. |
| The self-audit closes gaps rather than disclosing them | **HELD** | 28 unaccounted numbers, each explained individually with its destination named, not waved at collectively. Residue enumerated in four numbered classes. |
| Read-only | **HELD — verified, not asserted** | See §4. |
| Sibling checks catch wave escapes | **HELD** | e.g. `#330` found fully delivered by checking all 17 `g4dn.2xlarge` workflow files across repos while its own table still marked four repos pending; `#261` found superseded by `#282` because seven of its nine "pending" repos no longer have a `gh-pages` branch. |
| Tiering slots into the repo's existing plan | **PENDING** | The run discovered `#344` and `#357` as plan anchors and tiered against them — but whether a maintainer *agrees* with the tiering is the one thing no self-audit can check. Awaiting mmcky's read; this is run 1's check 9/10 in a new instance. |

**A note on `[verified]` in a repo with no code.** This run was chosen because `meta` has no code to verify
against — the sharpest stress on doctrine rule 1 ("the thread is a hypothesis and the default branch is the
evidence"), where `meta`'s default branch is two files. The audit's answer was to lean on
**`[verified live YYYY-MM-DD]`** — 97 of its 176 tags — checking claims against *other* repositories' live state,
published sites, and workflow files rather than against `meta` itself. That is a reasonable adaptation and it is
declared in the catalog's own legend. Whether the doctrine should name that as a first-class evidence class,
rather than leaving it to be improvised per run, is a real question for
[#12](https://github.com/QuantEcon/skills/issues/12) — and it is exactly the question #16 predicted this repo
would raise.

## 4. Interruption log

**State at kill** (captured externally before the resume, so it cannot be reconstructed after the fact):

- Phase 2, **open pass**; no `## Closed` section existed yet
- 68 entries recorded, `#4` → `#260`, ascending, none outside the open partition
- The final write (`#260`) was **complete and clean** — all four fields present, file terminated with a newline
- `findings.md` 42,028 bytes

**Prediction recorded before resuming**: resume at `#261` (the lowest open issue with no entry); do not re-walk
`#4`–`#260`; do not skip `#261`.

**What actually happened**:

| Expectation | Result |
|---|---|
| Resume at `#261` | Yes |
| No re-walking of completed items | Yes — the pre-kill 42,028 bytes were byte-identical afterwards; pure append |
| No skipping the item it died on | Yes |
| No duplicate entries | Yes — none anywhere in the file |
| Announce state correctly | Yes — "68 of the open issues are verified through `#260`; the closed pass hasn't started", matching an independent computation exactly |

**Two things this interrupt did *not* test**, stated so run 3 can target them:

1. **The truncation guard.** [`SKILL.md`](https://github.com/QuantEcon/skills/blob/qe--v0.7.0/qe/skills/audit-issues/SKILL.md) says to "re-verify the last entry in each rather than trusting a possibly
   truncated write". The kill left a clean write, so the guard was never exercised. Whether `#260` was
   re-verified is *indeterminate from the artifacts* — there is no duplicate entry, but re-verifying need not
   mean rewriting. Only the session transcript could settle it. **Run 3 should interrupt mid-write** to produce
   a genuinely partial entry.
2. **Resuming the closed pass.** The kill landed in the open pass. Given §5, resuming *inside* the closed pass is
   now the more interesting test.

**Read-only, verified rather than asserted.** A fingerprint of all 317 issues — number, state, `updated_at`,
comment count, labels — was taken before the run and again after:

```
before: 317 issues, sha256 024ccc8d4cd437e7…
after:  317 issues, sha256 024ccc8d4cd437e7…  (identical)
```

Any close, label, or comment would have moved `updated_at` on the affected issue. **No tracked file changed**
either: `HEAD` still `58d577d` and a clean index with no diff, the only entry in `git status` being the
untracked `?? .audit/` — the run's own output directory, which is where the working-directory rule puts it. Run 1 asserted read-only compliance;
this is the first run to demonstrate it. **Recommend the fingerprint-diff become a standard step** — it costs two
`gh` calls and converts a doctrine promise into a measurement.

*Caveat, stated because it bounds the claim*: the baseline was taken shortly after the run began, not before it,
so a mutation in the first minutes would not have been caught.

## 5. Finding — the closed pass is not incrementally checkpointed

This is the run's principal method finding, and it is invisible in the finished bundle.

Sampling `findings.md` throughout gave the write pattern:

| Phase | Checkpoint writes | Granularity |
|---|---|---|
| Open (138 items) | 15+ | batches of 8–9 entries, every 75–120s |
| Closed (179 items) | **1** | nothing for the entire survey, then the complete 10.8 KB section in a single write |

[`SKILL.md`](https://github.com/QuantEcon/skills/blob/qe--v0.7.0/qe/skills/audit-issues/SKILL.md) phase 2 states the guarantee plainly:

> Write each item's finding to `findings.md` as it is verified — **the closed pass too** … so that an interrupted
> run loses one item rather than the phase.

For the closed side that does not hold. An interrupt anywhere in the closed survey loses **the phase** — all 179
threads re-read from scratch.

**This is run 1's defect 2 in a new form.** Defect 2 was "the closed side is never checkpointed"; `audit` 0.2.0
added the `## Closed` heading and the two-partition resume rule. That fixed the *format* and left the
*granularity* untouched — the closed side is still all-or-nothing, now with a heading to be all-or-nothing under.

There is a second-order consequence worth recording separately, because the two conventions were written
independently and do not compose:

- **[`deliverables.md`](https://github.com/QuantEcon/skills/blob/qe--v0.7.0/qe/references/audit/deliverables.md) permits grouped entries** — "entries are grouped where a whole family shares one answer;
  every closed issue is named exactly once" — and this run used them, giving 9 `**#N` headers covering all 179
  closed issues.
- **The resume rule addresses by issue number** — "resume at the lowest number with no entry under the matching
  heading" — which is not well-defined against grouped prose.

So even if the closed pass *were* checkpointed incrementally, the resume rule as written could not address into
it. Any fix needs to touch both.

**What was not concluded, and why.** Two candidate findings were investigated and discarded rather than reported,
because the evidence did not support them:

- *Out-of-order writes create a silent-skip hazard.* The post-resume block was written `261, 282, 263, 264, …` —
  genuinely out of order. But the documented resume rule is a set difference ("lowest number with no entry"),
  which is order-independent, so ordering is cosmetic. The hazard argument required assuming the run used a
  high-water-mark algorithm, and the only evidence for that was it *describing* its position as "verified through
  `#260`" — an accurate plain-English summary of a correct set-difference result. Inferring an implementation
  from prose is not evidence. **Residue**: [`SKILL.md`](https://github.com/QuantEcon/skills/blob/qe--v0.7.0/qe/skills/audit-issues/SKILL.md)'s guard names two wrong shortcuts ("do not infer progress
  from the file's length or from a single block") but not "the highest recorded number". Adding the third is a
  one-line clarification, not a defect.
- *Batched writes violate append-as-you-go.* They do not. Writing after 9 of 70 items is checkpointing
  mid-phase, which is the doctrine's actual concern. Once measured, the exposure is bounded and modest — ~9 items
  and ~2 minutes. Whether the doctrine should name a target granularity is a design question, not a compliance
  failure.

Both are recorded here because a validation report that only lists confirmed findings hides its own false
positive rate, and because the discipline that killed them — refusing a claim whose citation does not actually
support it — is the same discipline run 1's severity-1 defect failed.

## 6. What the audit found about `meta`

Reported as the audit's own output, not re-verified by this record. The maintainer read (§3, pending) is what
validates it.

- **The tracker systematically understates what is already done** — five independent instances of one cause,
  rollout state tracked in hand-maintained markdown tables that drift: `#330` (fully delivered, table shows four
  repos pending), `#363`/`#364` (both books live, six unticked boxes describing shipped work), `#298` (targets
  theme v0.20.2; theme is at v0.22.0), `#351` (two of three rows done), `#261` (superseded by `#282`).
- **19 of 138 open issues (14%) are verifiably closeable**, each with a drafted, unsent closing comment.
- **The urgent work is unlabelled and unlinked** — three confirmed reader-visible defects: `discourse.quantecon.org`
  has no DNS record while five published pages still link to it; `intro.quantecon.org/inequality.html` contains no
  `Plotly.newPlot` while its prose promises a figure; `dynamics.quantecon.org/black_litterman.html` ships draggable
  sliders with no kernel.
- **Five closed-side defects**, all thread-only — most notably `#85`, closed COMPLETED in 2023 with half its scope
  never done: no lecture repo carries a `LICENSE` file, confirmed by 404 on `GET /repos/{repo}/license` across six
  repos.
- **Nine proposed new issues**, drafted ready to file.

**Doctrine §5 compliance, observed live**: the run initially recommended attaching native sub-issues to `#362` and
`#335`, then a GraphQL check showed `#362` already complete and `#358` carrying eleven. It **folded the correction
into the documents** rather than appending it — which is what §5 requires — and narrowed its recommendation from
"adopt sub-issues" to "stop recording rollout state in issue bodies".

## 7. What the doctrine did and did not transfer

Per #16, three verdicts are distinct: a rule cited and load-bearing, a rule that never came up, and a rule the run
had to work around. Only the third is a bug.

**Load-bearing.** §2's evidence classes (176 tags); §3's read-only boundary (verified clean); §5's
close-the-gap-don't-disclose-it (28/28 explained, and the folded correction above); `quantecon-context.md`'s
sibling-repo checks, which produced the single highest-value finding class.

**Never came up.** The `.dev/` notes-system conventions — `meta` has no notes system, so the working directory
fell through to the documented `.audit/` fallback. The bundle-scale rule also did not bind at 138 open issues.

**Worked around.** Two:

1. **`[verified]` against a repo with no code**, resolved by improvising `[verified live <date>]` (§3). It worked,
   it is declared, and it should probably be promoted into the doctrine rather than reinvented per run.
2. **Plan-anchor discovery with no `PLAN.md`** — `quantecon-context.md`'s search order fell through to *prior
   audit issues* (`#344`, `#357`) as the anchor. That is arguably the intended behaviour, but the search order
   does not name it explicitly, and it is now the second repo where the notes-system-first ordering did not apply.

## 8. Recommended follow-ups

Filed separately, not as paragraphs here, per the plan convention:

1. **Checkpoint the closed pass incrementally**, and reconcile the resume rule with grouped entries (§5). This is
   the one defect of substance.
2. **Promote `[verified live <date>]` into [`doctrine.md`](https://github.com/QuantEcon/skills/blob/qe--v0.7.0/qe/references/audit/doctrine.md) §2** as a named evidence class, or state explicitly that
   ref-relative verification does not apply to trackers without code (§3, §7).
3. **Add "the highest recorded number" to [`SKILL.md`](https://github.com/QuantEcon/skills/blob/qe--v0.7.0/qe/skills/audit-issues/SKILL.md)'s list of wrong ways to infer progress** (§5, residue).
4. **Make the tracker fingerprint-diff a standard run step** (§4).
5. **Run 3 should interrupt mid-write, and inside the closed pass** (§4).
6. **`#23` input**: the closed pass is 179 of 317 items — 56% of the run — for the cheapest checks in the audit.
   It scales badly (on `lecture-python.myst`, 1003 items against 73 open, it would be ~93% of the run) and, unlike
   the bundle, has no scale rule. Whether it earns that share is now answerable with two data points.

## 9. Outstanding — the maintainer's read

The one thing no self-audit can supply, and run 1's checks 9 and 10 in a new instance:

- Does the tiering against `#344`/`#357` match how the repo is actually planned, and would you act on it?
- Are the 19 drafted closing comments ones you would send?
- Where should the bundle live? It contains AWS and access-token findings; the run flagged
  `QuantEcon/infrastructure` as the better home for those portions. `meta` is public and has no notes system, so
  the bundle currently sits untracked in `.audit/`.
