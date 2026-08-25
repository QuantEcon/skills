# qe plugin — scripts

## `fetch-copilot.sh`

Dumps GitHub Copilot's review of a pull request — the overview, then every inline comment with the ID to reply to — for [`/qe:copilot-review`](../skills/copilot-review/SKILL.md). Read-only: it never posts. Requires an authenticated `gh`; run `bash fetch-copilot.sh --help` for the argument forms.

Two details are load-bearing rather than incidental. It **paginates both passes** over `pulls/<PR>/comments`, because `gh` applies `--jq` per page and refuses `--slurp` alongside it — and a reply always sorts after the comment it answers, so a single unpaginated page loses the reply markers and a re-run would double-post. And it **prefixes every line quoted from GitHub with `| `**, so no comment body can forge the `== ID` record header that the reply step keys on.