#!/usr/bin/env python3
"""tracker_snapshot.py — read a project tracker and its direct sub-issues, in plan order.

Reads through the GitHub REST API only (GraphQL is unavailable from Claude Code
sessions), so it runs anywhere a token does: `GH_TOKEN` / `GITHUB_TOKEN`, or the
token an authenticated `gh` holds (`gh auth token`).

    tracker_snapshot.py owner/repo#7                  # text: header, tracker body, children in order
    tracker_snapshot.py owner/repo#7 --bodies         # text, plus every child body
    tracker_snapshot.py owner/repo#7 --json           # the snapshot as JSON on stdout
    tracker_snapshot.py owner/repo#7 --json --out .qe/snapshot.json
    tracker_snapshot.py https://github.com/owner/repo/issues/7

Position in the child list is plan order (QEP-6, "Order is positional"); grandchildren
are not read. Every line quoted from GitHub in the text form is prefixed with "| " so
that no body can forge a "== #" record header. Read-only: nothing is written to GitHub.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"

# C2 §3.4 — the stamp grammar, verbatim (status-projects docs/contracts/tracker.md).
STAMP_HEADING = re.compile(
    r"^\#{2,3}[ \t]+Where we stand[ \t]*"
    r"\(verified[ \t]+(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?:[ \t]+(?P<time>\d{2}:\d{2}(?::\d{2})?))?"
    r"(?:[ \t]*(?P<zone>Z|[+-]\d{2}:?\d{2}|[A-Za-z]{2,5}))?"
    r"[ \t]*\)[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)
STAMP_BANNER = re.compile(
    r"^[ \t]{0,3}>[ \t]*\*\*Updated[ \t]+(?P<date>\d{4}-\d{2}-\d{2})"
    r"(?:[ \t]+(?P<time>\d{2}:\d{2}(?::\d{2})?))?"
    r"(?:[ \t]*(?P<zone>Z|[+-]\d{2}:?\d{2}|[A-Za-z]{2,5}))?",
    re.MULTILINE | re.IGNORECASE,
)
HEADING_PRESENT = re.compile(r"^\#{2,3}[ \t]+Where we stand\b", re.MULTILINE | re.IGNORECASE)

# The phase marker a work item's body opens with (workplan-project writes it; QEP-7 names it
# as the cross-repository fallback for phase membership).
PHASE_MARKER = re.compile(
    r"(?:\bPart of (?:[\w.-]+/[\w.-]+)?#\d+ \(Phase (?P<a>\w+)\))|(?:\bPhase (?P<b>\w+) of (?:[\w.-]+/[\w.-]+)?#\d+\b)"
)
DECISION_MARKER = re.compile(r"\s*\*\*Decision point\*\*")
REF = re.compile(r"^(?P<repo>[\w.-]+/[\w.-]+)#(?P<num>\d+)$")
URL = re.compile(r"^https://github\.com/(?P<repo>[\w.-]+/[\w.-]+)/issues/(?P<num>\d+)")


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def token() -> str:
    tok = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if tok:
        return tok
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=20)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    die("no GitHub token: set GH_TOKEN, or authenticate gh (gh auth login)")
    return ""  # unreachable


def get(path: str, tok: str, params: dict | None = None):
    url = API + path + (("?" + urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {tok}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "qe-tracker-snapshot",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r), r.headers
    except urllib.error.HTTPError as e:
        return {"__error__": e.code, "__url__": url}, {}


def parse_target(args: list[str]) -> tuple[str, int]:
    repo, num = None, None
    for a in args:
        m = URL.match(a) or REF.match(a)
        if m:
            repo, num = m.group("repo"), int(m.group("num"))
        elif "/" in a and "#" not in a:
            repo = a
        elif a.isdigit():
            num = int(a)
        else:
            die(f"unexpected argument: {a} (want owner/repo#N, owner/repo N, or an issue URL)")
    if not repo or num is None:
        die("name the tracker: owner/repo#N")
    return repo, num


def read_stamp(body: str, today: dt.date) -> tuple[str, str | None]:
    text = (body or "").replace("\r\n", "\n")
    for form, pat in (("heading", STAMP_HEADING), ("banner", STAMP_BANNER)):
        for m in pat.finditer(text):
            try:
                when = dt.date.fromisoformat(m.group("date"))
            except ValueError:
                continue
            if (when - today).days > 1:
                continue
            return form, m.group("date")
    return "none", None


def phase_of(body: str) -> str | None:
    m = PHASE_MARKER.search(body or "")
    return (m.group("a") or m.group("b")) if m else None


def repo_of(issue: dict) -> str:
    return issue["repository_url"].split("/repos/")[1]


def snapshot(repo: str, num: int, tok: str, want_bodies: bool) -> dict:
    today = dt.datetime.now(dt.timezone.utc).date()
    tracker, _ = get(f"/repos/{repo}/issues/{num}", tok)
    if "__error__" in tracker:
        die(f"could not read {repo}#{num}: HTTP {tracker['__error__']}")
    visibility: dict[str, bool | None] = {}

    def private(r: str) -> bool | None:
        if r not in visibility:
            meta, _ = get(f"/repos/{r}", tok)
            visibility[r] = None if "__error__" in meta else bool(meta.get("private"))
        return visibility[r]

    children_raw: list[dict] = []
    page = 1
    while True:
        chunk, headers = get(f"/repos/{repo}/issues/{num}/sub_issues", tok, {"per_page": 100, "page": page})
        if isinstance(chunk, dict) and "__error__" in chunk:
            die(f"could not read sub-issues of {repo}#{num}: HTTP {chunk['__error__']}")
        children_raw.extend(chunk)
        if len(chunk) < 100 or 'rel="next"' not in (headers.get("Link") or ""):
            break
        page += 1

    def blocked_by(r: str, n: int) -> dict:
        deps, _ = get(f"/repos/{r}/issues/{n}/dependencies/blocked_by", tok, {"per_page": 50})
        if isinstance(deps, dict) and "__error__" in deps:
            return {"total": None, "open": None}
        return {
            "total": len(deps),
            "open": [f"{repo_of(d)}#{d['number']}" for d in deps if d.get("state") == "open"],
        }

    children = []
    for i, c in enumerate(children_raw, 1):
        r = repo_of(c)
        body = c.get("body") or ""
        t = (c.get("type") or {}).get("name")
        role = "decision" if (t == "Decision" or DECISION_MARKER.match(body)) else "work"
        rec = {
            "position": i,
            "ref": f"{r}#{c['number']}",
            "repo": r,
            "number": c["number"],
            "private": private(r),
            "title": c.get("title") or "",
            "state": c.get("state"),
            "state_reason": c.get("state_reason"),
            "type": t,
            "role": role,
            "milestone": (c.get("milestone") or {}).get("title"),
            "phase": phase_of(body),
            "blocked_by": blocked_by(r, c["number"]),
            "url": c.get("html_url"),
        }
        if want_bodies:
            rec["body"] = body
        children.append(rec)

    body = tracker.get("body") or ""
    form, date = read_stamp(body, today)
    summ = tracker.get("sub_issues_summary") or {}
    return {
        "generated_by": "qe/scripts/workplan/tracker_snapshot.py",
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tracker": {
            "ref": f"{repo}#{num}",
            "repo": repo,
            "number": num,
            "url": tracker.get("html_url"),
            "title": tracker.get("title") or "",
            "state": tracker.get("state"),
            "state_reason": tracker.get("state_reason"),
            "type": (tracker.get("type") or {}).get("name"),
            "private": private(repo),
            "stamp": {"form": form, "date": date, "heading_present": bool(HEADING_PRESENT.search(body))},
            "sub_issues_summary": {"total": summ.get("total", len(children)), "completed": summ.get("completed", 0)},
            "blocked_by": blocked_by(repo, num),
            "milestone": (tracker.get("milestone") or {}).get("title"),
            "comments": tracker.get("comments"),
            "created_at": tracker.get("created_at"),
            "updated_at": tracker.get("updated_at"),
            "body": body,
        },
        "children": children,
        "children_truncated": len(children) < summ.get("total", len(children)),
    }


def quoted(text: str) -> str:
    return "".join(f"| {line}\n" for line in (text or "").splitlines()) or "| (empty)\n"


def render_text(snap: dict, want_bodies: bool) -> str:
    t = snap["tracker"]
    out = []
    priv = {True: "private", False: "public", None: "unknown-visibility"}[t["private"]]
    out.append(f"# Tracker snapshot — {t['ref']}")
    out.append(f"# {t['state'].upper()} · type {t['type'] or 'untyped'} · {priv} repository · stamp "
               f"{t['stamp']['date'] or 'NONE'} · sub-issues {t['sub_issues_summary']['total']} "
               f"({t['sub_issues_summary']['completed']} completed)")
    out.append(f"# {t['title']}")
    out.append(f"# {t['url']}")
    if snap["children_truncated"]:
        out.append(f"# WARNING: {t['sub_issues_summary']['total']} direct sub-issues; only {len(snap['children'])} are listed below")
    out.append("\n## Tracker body\n")
    out.append(quoted(t["body"]).rstrip("\n"))
    out.append("\n## Sub-issues, in tracker order (position is sequence)\n")
    for c in snap["children"]:
        bo = c["blocked_by"]["open"]
        edges = "" if bo is None else (f"  blocked-by {len(bo)} open" if bo else "")
        out.append(f"== #{c['number']}  {c['position']:>2}  {c['state'].upper():<6} {c['type'] or 'untyped':<9} "
                   f"{c['role']:<8} {c['repo']}  {c['title']}{edges}")
        if want_bodies and "body" in c:
            out.append(quoted(c["body"]).rstrip("\n"))
    out.append(f"\n({len(snap['children'])} direct sub-issue(s) listed; the tracker reports {t['sub_issues_summary']['total']})")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("target", nargs="+", help="owner/repo#N, owner/repo N, or an issue URL")
    p.add_argument("--bodies", action="store_true", help="include every child body")
    p.add_argument("--json", action="store_true", help="emit the snapshot as JSON")
    p.add_argument("--out", help="write the JSON snapshot to this path (implies --json for the file)")
    a = p.parse_args(argv)
    repo, num = parse_target(a.target)
    snap = snapshot(repo, num, token(), want_bodies=a.bodies or bool(a.out))
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(snap, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {a.out}", file=sys.stderr)
    if a.json:
        json.dump(snap, sys.stdout, indent=1, ensure_ascii=False)
        print()
    elif not a.out:
        sys.stdout.write(render_text(snap, a.bodies))
    return 0


if __name__ == "__main__":
    sys.exit(main())
