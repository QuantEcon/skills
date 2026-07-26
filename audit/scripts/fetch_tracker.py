#!/usr/bin/env python3
"""Snapshot a repository's whole issue and PR tracker to disk, then reconcile
what was captured against what should exist.

    python fetch_tracker.py QuantEcon/action-translation --out .audit/action-translation

Why a script instead of letting the skill run `gh` ad hoc: a portfolio audit is
long, and every phase after the first re-reads the same data. Fetching once into
a frozen snapshot makes the run cheap, makes it resumable after a lost session,
and pins every later claim to a single point in time — so "events after scrape
time" is a stated property of the report rather than an unnoticed gap.

Comment threads come down inside the same list call, so the snapshot is
thread-complete for both open *and* closed items in two API round trips.

Writes into `--out`:

    meta.json      repo, snapshot time (UTC), gh version, auth state, counts
    issues.json    every issue, any state, with its full comment thread
    prs.json       every PR, any state, with comments, reviews, and closing refs
    coverage.json  the mechanical half of the coverage self-audit

Stdlib only, so it runs anywhere `gh` does.
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ISSUE_FIELDS = [
    "number", "title", "state", "stateReason", "labels", "milestone",
    "assignees", "author", "body", "comments", "createdAt", "updatedAt",
    "closedAt", "url",
]

PR_FIELDS = [
    "number", "title", "state", "labels", "milestone", "author", "body",
    "comments", "reviews", "createdAt", "updatedAt", "closedAt", "mergedAt",
    "mergeCommit", "headRefName", "baseRefName", "url",
    "closingIssuesReferences",
]


def die(msg):
    print(f"fetch_tracker: {msg}", file=sys.stderr)
    sys.exit(1)


def run_gh(args):
    """Run a gh subcommand, returning parsed JSON."""
    proc = subprocess.run(
        ["gh", *args], capture_output=True, text=True,
    )
    if proc.returncode != 0:
        die(f"`gh {' '.join(args)}` failed:\n{proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        die(f"`gh {' '.join(args)}` returned invalid JSON — {exc}")


def preflight(repo):
    """Fail in the first minute, not the third hour."""
    if shutil.which("gh") is None:
        die("the GitHub CLI (`gh`) is not on PATH — install it, or fall back to "
            "the unauthenticated route documented in the skill")
    auth = subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True,
    )
    if auth.returncode != 0:
        die("`gh auth status` reports no authentication. Private QuantEcon repos "
            "(project-*, style-guide, cli) are unreachable unauthenticated, and "
            "the anonymous API allows only 60 requests/hour. Run `gh auth login`.")
    if repo.count("/") != 1 or not all(repo.split("/")):
        die(f"expected OWNER/REPO, got {repo!r}")
    # Confirms the repo exists and is visible to these credentials.
    run_gh(["repo", "view", repo, "--json", "name"])
    return auth.stdout + auth.stderr


def reconcile(issues, prs, limit):
    """Reconcile captured items against the number sequence they should fill.

    GitHub draws issue and PR numbers from one per-repo sequence, so a complete
    capture accounts for every number from 1 to the highest one seen. Gaps are
    real (deleted or transferred items, and PR numbers burned by never-opened
    branches) but they are exactly what a silent truncation also looks like —
    so they are reported as unaccounted numbers for the audit to explain, never
    swallowed here.
    """
    issue_numbers = {i["number"] for i in issues}
    pr_numbers = {p["number"] for p in prs}
    seen = issue_numbers | pr_numbers
    highest = max(seen) if seen else 0
    unaccounted = [n for n in range(1, highest + 1) if n not in seen]

    def thread_stats(items):
        with_comments = [i for i in items if i.get("comments")]
        return {
            "total": len(items),
            "with_comments": len(with_comments),
            "comments_captured": sum(len(i.get("comments") or []) for i in with_comments),
        }

    open_issues = [i for i in issues if i["state"].upper() == "OPEN"]
    closed_issues = [i for i in issues if i["state"].upper() != "OPEN"]

    return {
        "highest_number": highest,
        "items_captured": len(seen),
        "issues": len(issues),
        "prs": len(prs),
        "unaccounted_numbers": unaccounted,
        "unaccounted_count": len(unaccounted),
        "threads_open_issues": thread_stats(open_issues),
        "threads_closed_issues": thread_stats(closed_issues),
        "threads_prs": thread_stats(prs),
        "truncation_risk": {
            "limit": limit,
            "issues_at_limit": len(issues) >= limit,
            "prs_at_limit": len(prs) >= limit,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Snapshot a repo's full issue/PR tracker for a bulk audit.",
    )
    parser.add_argument("repo", help="OWNER/REPO, e.g. QuantEcon/action-translation")
    parser.add_argument("--out", required=True, help="snapshot directory to write")
    parser.add_argument(
        "--limit", type=int, default=1000,
        help="max items per stream (default 1000); coverage.json flags a stream "
             "that comes back at the limit, because that is indistinguishable "
             "from truncation",
    )
    args = parser.parse_args()

    auth_note = preflight(args.repo)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"fetching issues from {args.repo} …")
    issues = run_gh([
        "issue", "list", "-R", args.repo, "--state", "all",
        "--limit", str(args.limit), "--json", ",".join(ISSUE_FIELDS),
    ])
    print(f"  {len(issues)} issues")

    print(f"fetching pull requests from {args.repo} …")
    prs = run_gh([
        "pr", "list", "-R", args.repo, "--state", "all",
        "--limit", str(args.limit), "--json", ",".join(PR_FIELDS),
    ])
    print(f"  {len(prs)} pull requests")

    gh_version = subprocess.run(
        ["gh", "--version"], capture_output=True, text=True,
    ).stdout.splitlines()[0]

    coverage = reconcile(issues, prs, args.limit)
    meta = {
        "repo": args.repo,
        "snapshot_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "gh_version": gh_version,
        "authenticated": "Logged in" in auth_note,
        "limit": args.limit,
        "issue_fields": ISSUE_FIELDS,
        "pr_fields": PR_FIELDS,
    }

    (out / "issues.json").write_text(json.dumps(issues, indent=2) + "\n")
    (out / "prs.json").write_text(json.dumps(prs, indent=2) + "\n")
    (out / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(f"\nsnapshot written to {out}/  ({meta['snapshot_utc']})")
    print(f"  numbers 1..{coverage['highest_number']}: "
          f"{coverage['items_captured']} accounted, "
          f"{coverage['unaccounted_count']} unaccounted")
    oi = coverage["threads_open_issues"]
    ci = coverage["threads_closed_issues"]
    print(f"  open issues   {oi['total']:>4}  ({oi['with_comments']} with threads, "
          f"{oi['comments_captured']} comments)")
    print(f"  closed issues {ci['total']:>4}  ({ci['with_comments']} with threads, "
          f"{ci['comments_captured']} comments)")
    if coverage["truncation_risk"]["issues_at_limit"] or coverage["truncation_risk"]["prs_at_limit"]:
        print("\n  WARNING: a stream came back exactly at --limit; re-run with a "
              "higher --limit before trusting the counts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
