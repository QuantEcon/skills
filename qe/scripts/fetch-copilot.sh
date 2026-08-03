#!/usr/bin/env bash
#
# fetch-copilot.sh — dump GitHub Copilot's review feedback for a pull request.
#
# Prints the review overview, then every inline Copilot comment with the ID you
# reply to. Comments that already have a reply are flagged with who wrote it, so
# a re-run does not double-post.
#
# Usage:
#   fetch-copilot.sh                      # current branch's PR, in the repo you are standing in
#   fetch-copilot.sh 42                   # PR 42 in the repo you are standing in
#   fetch-copilot.sh owner/repo 42        # PR 42 in another repo
#   fetch-copilot.sh owner/repo#42        # same, as one argument
#   fetch-copilot.sh https://github.com/owner/repo/pull/42
#   GH_REPO=owner/repo fetch-copilot.sh 42
#
# Requires gh (authenticated). The working tree is only what an omitted repo or
# PR number is inferred from — give both and it runs from anywhere.
#
# Everything quoted from GitHub is prefixed with "| " so that no comment body can
# forge a "== ID" record header — see SKILL.md, "Reading the output".
set -euo pipefail

if [ -t 2 ]; then _red=$(printf '\033[31m'); _off=$(printf '\033[0m'); else _red=''; _off=''; fi
die() { printf '%serror:%s %s\n' "$_red" "$_off" "$*" >&2; exit 1; }
usage() { sed -n '3,18p' "$0" | sed 's/^#\{1,\} \{0,1\}//'; exit "${1:-0}"; }

command -v gh >/dev/null 2>&1 || die "gh is not installed — see https://cli.github.com"
gh auth status >/dev/null 2>&1 || die "gh is not authenticated — run: gh auth login (or set GH_TOKEN)"

repo=""; pr=""; origin=""

case "${1-}" in -h|--help) usage 0 ;; esac

# Consume arguments explicitly: an unread argument used to be discarded in
# silence, which turned "fetch-copilot.sh 42 owner/repo" into a complete,
# plausible report about a different repository.
case "${1-}" in
  *://*/pull/*)                                        # a pull-request URL
      u="${1%%\?*}"; u="${u%/}"
      pr="${u##*/}"; u="${u%/pull/*}"
      repo="${u#*://}"; repo="${repo#*/}"
      origin="argument"; shift ;;
  */*'#'*) repo="${1%%'#'*}"; pr="${1##*'#'}"; origin="argument"; shift ;;
  */*)     repo="$1"; origin="argument"; shift
           if [ $# -gt 0 ]; then pr="$1"; shift; fi ;;
  '#'*)    pr="${1#'#'}"; shift ;;
  '')      if [ $# -gt 0 ]; then shift; fi ;;
  *)       pr="$1"; shift ;;
esac
[ $# -eq 0 ] || die "unexpected extra argument: $1  (usage: fetch-copilot.sh [owner/repo] [PR])"

# Checked before the repo is resolved, so a mistyped argument names itself rather
# than surfacing as whatever the repo lookup happens to fail on.
if [ -n "$pr" ]; then
  case "$pr" in *[!0-9]*) die "PR must be a number, got: $pr" ;; esac
fi

# gh resolves the repo from the git remote and ignores GH_REPO while inside a
# working tree, so read GH_REPO here rather than relying on gh to honour it.
if [ -z "$repo" ] && [ -n "${GH_REPO-}" ]; then
  repo="$GH_REPO"; origin="GH_REPO"
fi

if [ -z "$repo" ]; then
  repo="$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)" || repo=""
  [ -n "$repo" ] || die "not inside a git repo and no repo given — try: fetch-copilot.sh owner/repo 42"
  origin="working tree"
fi

# $repo is interpolated into a REST path below, where a URL or a stray path
# segment produces a broken copy-paste command under a heading that says to use it.
case "$repo" in
  */*/*|*:*|*' '*|*'?'*) die "repo must be owner/repo, got: $repo" ;;
  */*) : ;;
  *)   die "repo must be owner/repo, got: $repo" ;;
esac

if [ -z "$pr" ]; then
  pr="$(gh pr view --repo "$repo" --json number -q .number 2>/dev/null)" || pr=""
  [ -n "$pr" ] || die "no PR found for the current branch in $repo — pass a number: fetch-copilot.sh $repo 42"
fi

tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT

# Resolve the PR before reporting on it. PR numbers collide across repos, so a
# wrong-repo lookup otherwise yields a plausible "no Copilot review found" for a
# PR nobody asked about — a silent failure this check turns into a loud one.
# gh's own stderr is passed through: every failure here used to be reported as
# "no such PR", including gh being unauthenticated, offline, or rate-limited.
if ! info="$(gh pr view "$pr" --repo "$repo" --json state,title -q '.state + " · " + .title' 2>"$tmp/err")"; then
  sed 's/^/gh: /' "$tmp/err" >&2
  die "could not read $repo#$pr (repo came from: $origin) — for a different repo: fetch-copilot.sh owner/repo $pr"
fi

printf '# Copilot review — %s #%s\n' "$repo" "$pr"
printf '# %s  (repo from: %s)\n' "$info" "$origin"

# Copilot writes its real overview — the change summary and the per-file table —
# only in its FIRST review. Every re-review after a push is a ~120-character
# stub, so taking the last review renders the summary as nothing at all.
printf '\n## Overview\n'
gh pr view "$pr" --repo "$repo" --json reviews --jq '
  [.reviews[]
   | select(.author.login == "copilot-pull-request-reviewer")
   | select((.body // "") != "")] as $c
  | if ($c | length) == 0 then "(no Copilot review found)"
    else (($c | max_by(.body | length) | .body)
          | gsub("\r"; "") | rtrimstr("\n") | split("\n") | map("| " + .) | join("\n"))
         + (if ($c | length) > 1
            then "\n\n(Copilot posted \($c | length) reviews on this PR; the summary above is its most detailed one. The rest are re-review stubs.)"
            else "" end)
    end'

printf '\n## Inline comments\n'
printf 'Reply with: gh api repos/%s/pulls/%s/comments/<ID>/replies -f body="..."\n\n' "$repo" "$pr"

# Two passes, both paginated. gh applies --jq per page and refuses --slurp
# alongside it, so the reply set cannot be built in the same pass that prints the
# comments — and it has to span every page: a reply always sorts after the
# comment it answers, so on a PR past one page the flags would all be missing and
# a re-run would post duplicate replies.
gh api --paginate "repos/$repo/pulls/$pr/comments?per_page=100" \
  --jq '.[] | select(.in_reply_to_id) | "\(.in_reply_to_id)\t\(.user.login)"' \
  | sort -u > "$tmp/replied"

gh api --paginate "repos/$repo/pulls/$pr/comments?per_page=100" --jq '
  .[] | select(.user.login == "Copilot")
  | "== ID \(.id)  \(.path // "?"):\(.line // .original_line // "?")",
    ((.body // "(empty body)") | gsub("\r"; "") | rtrimstr("\n") | split("\n") | map("| " + .)[]),
    ""' > "$tmp/comments"

awk -v repl="$tmp/replied" '
  BEGIN {
    while ((getline line < repl) > 0) {
      split(line, f, "\t")
      who[f[1]] = (f[1] in who) ? who[f[1]] "," f[2] : f[2]
    }
  }
  /^== ID / {
    n++
    if ($3 in who) { printf "%s  [REPLIED by %s]\n", $0, who[$3]; next }
  }
  { print }
  END {
    if (n == 0) print "(no inline Copilot comments)"
    else printf "(%d inline Copilot comment(s))\n", n
  }
' "$tmp/comments"
