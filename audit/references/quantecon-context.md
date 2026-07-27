# Auditing a QuantEcon repository

What a generic tracker audit gets wrong about this org, and the conventions every skill in this plugin resolves against. Policies are cited, never restated — several are live drafts, and a copy here would be a copy that drifts.

## Repo type sets the expectations

[QEP-3 (Draft, qeps#7)](https://github.com/QuantEcon/qeps/pull/7) names the repo families. Type is the strongest prior an audit has about what its issues *mean*, and tiering that ignores it will mis-rank almost everything:

| Family | What the tracker mostly holds | Audit consequence |
|---|---|---|
| `lecture-*` | Content corrections, build breakage from environment upgrades, style campaigns | Build-breaking issues are release-gating; content issues rarely are. Many are one instance of a campaign — check siblings before tiering. |
| `action-*`, `workflow-*` | Consumer-visible behaviour, release gates | Anything a downstream repo consumes via `uses:` is higher-stakes than its thread suggests. Verify against the tag, not `main`. |
| `status-*` | Machine-updated reporters | The data is generated; issues are about the collector or the contract. Never recommend edits to generated data. |
| `project-*` | Narrative, decisions, roadmaps (private) | Issues are decision records. "Stale" often means *decided and not written up*, which is a re-homing action, not a close. |
| `QuantEcon/meta` | Org-wide coordination | An issue in a repo that is really org-wide belongs here; an issue here that is really repo-local belongs there. Flag the mismatch, don't move it. |

If the repo's own type is ambiguous, say so once and audit it as the closest family rather than inventing a sixth.

## Labels: recommend, never apply

The standard set is [QEP-2 (Draft, qeps#2)](https://github.com/QuantEcon/qeps/pull/2) — 19 core labels plus 2 lecture-extension labels — re-recording the settled decision in [meta#324](https://github.com/QuantEcon/meta/issues/324). Because QEP-2 is still a draft, doctrine rule 6 applies: recommend only already-canonical labels, mark anything else *post-acceptance*.

Application is owned by the `qe` CLI, not by an audit:

```
qe gh labels check     # read-only drift report, non-zero exit on drift
```

An audit may report label drift and cite that command. It must never hand-apply or hand-prune labels — profiles (`lectures`, `software`) decide which repos carry which subset, and hand-editing desynchronises a repo from its profile in a way the next `sync` will silently revert.

## The cross-repo graph is the point

QuantEcon's lecture repos are near-siblings, and the same fix lands in several of them as `SYNC:` PRs. A single-repo audit that ignores this produces confident, wrong conclusions — most often "this is stale" about an issue whose fix landed in a sibling, or "unique" about the fourth instance of a known campaign.

For every open item, ask: does a sibling repo carry the same issue, and has it been resolved there? Is this one step of a rollout whose other steps are elsewhere? Is there a program or meta issue that owns the whole family? Record these in the report's external cross-link registry, and treat a sibling's merged fix as `[verified]` evidence only after checking that *this* repo's default branch actually contains it — a wave escape is exactly a fix that was claimed for a repo and never landed in it.

**Hazard when writing cross-repo references.** Any suggested comment or issue body the audit drafts must avoid a GitHub closing keyword (`close(s|d)`, `fix(es|ed)`, `resolve(s|d)`) immediately before an `owner/repo#N` reference. GitHub's auto-linker treats that as a closing reference and will close the *referenced* upstream item when the text lands on a default branch. Use neutral wording — "Mirrors the change in `owner/repo#N`", "See `owner/repo#N`", "Ports the fix from `owner/repo#N`". Plain same-repo `#N` links are unaffected.

## Finding the plan to slot into

Doctrine says slot findings into the repo's existing plan, never invent a parallel one. QuantEcon repos keep that plan in one of several places; look in this order and state which one was used:

1. `.dev/` — `STATE.md`, `PLAN.md`, `FUTURE.md`, `decisions/`, `log/`
2. Root-level `PLAN.md`, `ROADMAP.md`, `NEXT-STEPS.md`, `CATALOG.md`
3. `AGENTS.md` / `CLAUDE.md` — often the only durable convention record in a small repo
4. The paired `project-*` repo, for work that belongs to a program rather than a repo
5. A live work-plan or tracking issue in the tracker itself

If none exists, say so and tier against the repo's milestones instead. Proposing a notes system is out of scope — that is a change to the repo, and audits do not change repos.

## Access

Authenticated `gh` is assumed. Several QuantEcon repos are private (`project-*`, `style-guide`, `cli`, `jupyteach`, `atlas.quantecon.org`), so the unauthenticated fallbacks that work for public repos — the anonymous REST endpoint, `codeload` tarballs, `raw.githubusercontent.com`, scraping embedded JSON out of issue HTML — return nothing there. The snapshot script fails on missing auth for exactly this reason. On a public repo without `gh`, the fallbacks are viable but share a 60 requests/hour per-IP budget: fetch metadata first, comment threads second, and expect to lose the tail.

A thread reconstructed that way carries a caveat the `gh` path does not: it can begin mid-conversation, so attribute comments cautiously and treat "the thread says" claims as `[stated]` at best. An audit that took this route must say so in its coverage statement — the snapshot script's guarantees do not apply to it.
