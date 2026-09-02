#!/usr/bin/env bash
#
# tracker-snapshot.sh — dump a project tracker and its direct sub-issues, in order.
#
# Prints the tracker's state, issue type, stamp date and sub-issue counts, then
# the tracker body, then one record per direct sub-issue in tracker order —
# which under QEP-6 is plan order. Grandchildren are not read.
#
# Usage:
#   tracker-snapshot.sh owner/repo#7               # the tracker, as one argument
#   tracker-snapshot.sh owner/repo 7               # the same, as two
#   tracker-snapshot.sh https://github.com/owner/repo/issues/7
#   tracker-snapshot.sh owner/repo#7 --bodies      # also print every sub-issue body
#
# Requires gh (authenticated) and python3. No working tree is needed.
#
# Everything quoted from GitHub is prefixed with "| " so that no body can forge a
# "== #" record header — see SKILL.md, "Reading the snapshot".
set -euo pipefail

if [ -t 2 ]; then _red=$(printf '\033[31m'); _off=$(printf '\033[0m'); else _red=''; _off=''; fi
die() { printf '%serror:%s %s\n' "$_red" "$_off" "$*" >&2; exit 1; }
usage() { sed -n '3,16p' "$0" | sed 's/^#\{1,\} \{0,1\}//'; exit "${1:-0}"; }

command -v gh >/dev/null 2>&1 || die "gh is not installed — see https://cli.github.com"
command -v python3 >/dev/null 2>&1 || die "python3 is not installed"
gh auth status >/dev/null 2>&1 || die "gh is not authenticated — run: gh auth login (or set GH_TOKEN)"

bodies=0; repo=""; num=""
for a in "$@"; do
  case "$a" in
    -h|--help) usage 0 ;;
    --bodies) bodies=1 ;;
    https://github.com/*/*/issues/*)
      rest=${a#https://github.com/}; repo=${rest%%/issues/*}; num=${rest##*/issues/}; num=${num%%[/?#]*} ;;
    */*#*) repo=${a%%#*}; num=${a##*#} ;;
    */*) repo=$a ;;
    *[!0-9]*) die "unexpected argument: $a (want owner/repo#N, owner/repo N, or an issue URL)" ;;
    *) num=$a ;;
  esac
done
[ -n "$repo" ] || die "name the tracker's repository: owner/repo#N"
[ -n "$num" ] || die "name the tracker's issue number: owner/repo#N"
owner=${repo%%/*}; name=${repo##*/}

query='query($owner:String!,$name:String!,$num:Int!){
  repository(owner:$owner,name:$name){
    issue(number:$num){
      title state url body
      issueType{name}
      repository{isPrivate}
      subIssuesSummary{total completed}
      subIssues(first:100){
        totalCount
        nodes{ number title state url body issueType{name} repository{nameWithOwner isPrivate} }
      }
    }
  }
}'

json=$(gh api graphql -F owner="$owner" -F name="$name" -F num="$num" -f query="$query" 2>&1) \
  || { printf 'gh: %s\n' "$json" >&2; die "could not read $repo#$num"; }

tmp=$(mktemp); trap 'rm -f "$tmp"' EXIT; printf '%s' "$json" > "$tmp"
BODIES=$bodies python3 - "$repo" "$num" "$tmp" <<'PY'
import json, os, re, sys
repo, num, path = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as fh:
    data = json.load(fh)
issue = (data.get("data") or {}).get("repository", {}).get("issue")
if issue is None:
    msgs = "; ".join(e.get("message", "?") for e in data.get("errors", [])) or "no such issue"
    sys.exit(f"error: could not read {repo}#{num}: {msgs}")

def quoted(text):
    return "".join(f"| {line}\n" for line in (text or "").splitlines()) or "| (empty)\n"

stamp = re.search(r"^## Where we stand \(verified (\d{4}-\d{2}-\d{2})", issue["body"] or "", re.M)
itype = (issue.get("issueType") or {}).get("name") or "untyped"
summ = issue["subIssuesSummary"]; total = issue["subIssues"]["totalCount"]
priv = "private" if issue["repository"]["isPrivate"] else "public"
print(f"# Tracker snapshot — {repo}#{num}")
print(f"# {issue['state']} · type {itype} · {priv} repository · stamp {stamp.group(1) if stamp else 'NONE'}"
      f" · sub-issues {summ['total']} ({summ['completed']} completed)")
print(f"# {issue['title']}")
print(f"# {issue['url']}")
if total > 100:
    print(f"# WARNING: {total} direct sub-issues; only the first 100 are listed below")
print("\n## Tracker body\n")
print(quoted(issue["body"]), end="")
print("\n## Sub-issues, in tracker order (position is sequence)\n")
for i, n in enumerate(issue["subIssues"]["nodes"], 1):
    t = (n.get("issueType") or {}).get("name") or "untyped"
    # QEP-6's role marker counts only when the body *opens* with it — a later
    # mention is discussion of some other decision, not a role claim.
    opens_with_marker = re.match(r"\s*\*\*Decision point\*\*", n.get("body") or "") is not None
    role = "decision" if t == "Decision" or opens_with_marker else "work"
    print(f"== #{n['number']}  {i:>2}  {n['state']:<6} {t:<9} {role:<8} {n['repository']['nameWithOwner']}  {n['title']}")
    if os.environ.get("BODIES") == "1":
        print(quoted(n.get("body")), end="")
print(f"\n({len(issue['subIssues']['nodes'])} direct sub-issue(s) listed; the tracker reports {summ['total']})")
PY
