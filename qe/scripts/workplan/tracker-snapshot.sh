#!/usr/bin/env bash
#
# tracker-snapshot.sh — dump a project tracker and its direct sub-issues, in order.
#
# A shim kept for the invocation lines that name it: the work is done by
# tracker_snapshot.py beside it, which reads through the GitHub REST API only
# (GraphQL is unavailable from Claude Code sessions). Same arguments, same text
# output; --json and --out PATH write the snapshot QEP-7 names.
#
# Usage:
#   tracker-snapshot.sh owner/repo#7               # the tracker, as one argument
#   tracker-snapshot.sh owner/repo 7               # the same, as two
#   tracker-snapshot.sh https://github.com/owner/repo/issues/7
#   tracker-snapshot.sh owner/repo#7 --bodies      # also print every sub-issue body
#   tracker-snapshot.sh owner/repo#7 --json --out .qe/snapshot.json
#
# Requires python3 and a token: GH_TOKEN / GITHUB_TOKEN, or an authenticated gh.
set -euo pipefail
command -v python3 >/dev/null 2>&1 || { echo "error: python3 is not installed" >&2; exit 1; }
exec python3 "$(dirname "$0")/tracker_snapshot.py" "$@"
