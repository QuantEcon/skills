#!/usr/bin/env python3
"""Fail a pull request that changes a plugin's shipped files without bumping
that plugin's version.

Run from anywhere; paths are resolved from this file's location:

    python scripts/check-version-bump.py [--base origin/main]

It reads committed history only. Uncommitted work in the tree is not part of
the check — the script says so when it sees any.

Why this exists
---------------
The plugin install cache is keyed by *version string* —
`~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` — and
`claude plugin update` compares version strings only. Change a SKILL.md
without changing the version and the update reports "already at the latest
version" and refreshes nothing: the edit is merged, published, and invisible
to every consuming repository. **The version bump is the delivery mechanism,
not bookkeeping**, which is why an unbumped change is a CI failure rather than
a review nit. It has happened here already — PR #27 edited a shipped SKILL.md
under `qe/` with `qe` left at 0.2.0.

What counts as a change
-----------------------
Every tracked file under a plugin's directory, with no exemptions —
`SKILL.md`, `scripts/`, `references/`, the plugin's `README.md`, and its
`CHANGELOG.md`. The plugin directory *is* the shipped artefact; if a file is
inside it, a user gets it from the cache, and the only way to give them the new
copy is a new version. A file *leaving* a plugin directory counts too, which is
why rename detection is switched off below: what a plugin ships changed either
way.

What this does not check
------------------------
That `plugin.json` and the `marketplace.json` entry carry the same version —
`scripts/validate.py` enforces that, and duplicating it here would mean two
places to fix when the rule changes. This guard reads `plugin.json` as the
authority (it is what wins at install time) and, if the two disagree, prints a
pointer to the validator rather than raising its own error.

It does *not* delegate the question of whether a version exists at all.
`validate.py` only compares the two manifests to each other, so a missing
`version` key in both, or an unquoted `"version": 0.2`, passes there — and
would read here as "some other value" if it were trusted. A version that is
not a non-empty string is not a usable cache-key path segment, so this guard
treats it as a failure in its own right.

And the release note
--------------------
A plugin that legitimately bumps must also carry a heading for the new version
in `<plugin>/CHANGELOG.md`, in the same diff. That is not tidiness: the
changelog is the only record of what changed that reaches someone whose copy is
an extracted install cache with no `.git` and no way to reach one. The check is
deliberately loose — any Markdown heading containing the version as a whole
token satisfies it — so the file's format is not a CI contract.

Exit codes
----------
0  every touched plugin was bumped (or needed no bump)
1  at least one plugin changed without a usable bump — the version did not
   move, it moved backwards, it landed on a version string already published
   on the base branch, there is no usable version string at all, or the new
   version has no changelog entry
2  the check could not be performed (usually a shallow clone — see below);
   deliberately *not* 0, because a guard that silently passes when it cannot
   see the base is worse than no guard

CHANGELOG.md: why a bump is required for changelog-only edits
-------------------------------------------------------------
Against requiring one: a changelog is documentation, not behaviour; no skill
reads it; a typo fix would mint a release with no substance in it.

For requiring one (what this script does): the changelog ships *inside* the
plugin directory, so it is copied into the install cache like everything else.
If it can be edited without a bump, the changelog a user reads at
`.../cache/quantecon/qe/0.2.0/CHANGELOG.md` is permanently a different document
from the one on `main` — a drifted copy that nobody can tell is stale, which is
the exact failure the repo's single-source-of-truth principle exists to
prevent. An exemption also has to define "only", so a mixed PR would need
per-file bookkeeping and its own tests. And in the intended workflow the rule
costs nothing: a changelog entry is written *in* the release commit that bumps
the version, so the requirement only bites the retroactive edit — the one case
where what a user reads really is changing, and where a patch bump is the
honest description of what happened.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE_PATH = ".claude-plugin/marketplace.json"

EXIT_OK = 0
EXIT_UNBUMPED = 1
EXIT_CANNOT_CHECK = 2

# How many changed files to list per plugin before truncating the report.
MAX_LISTED = 8

# Sentinels for the two ways a version can be unreadable. Neither is a string,
# so neither can ever compare equal to a real version and be mistaken for one.
NO_MANIFEST = object()      # no plugin.json at that revision
NOT_A_VERSION = object()    # plugin.json exists, "version" is missing or not a string


# --------------------------------------------------------------------------
# git plumbing
# --------------------------------------------------------------------------

def git(*args):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True
    )


def git_out(*args):
    """Stdout of a git command, or None if it failed."""
    proc = git(*args)
    return None if proc.returncode != 0 else proc.stdout


def cannot_check(headline, *lines):
    # Flush stdout first: CI merges the two streams, and a report that arrives
    # out of order reads as though the guard passed and then complained.
    sys.stdout.flush()
    print(f"version-bump guard: CANNOT CHECK — {headline}", file=sys.stderr)
    for line in lines:
        print(f"  {line}" if line else "", file=sys.stderr)
    sys.stderr.flush()
    sys.exit(EXIT_CANNOT_CHECK)


CHECKOUT_FIX = (
    "    - uses: actions/checkout@v4",
    "      with:",
    "        fetch-depth: 0   # the guard needs the base branch and the merge base",
)


def resolve_merge_base(base_ref, head_ref):
    """Merge base of base_ref and head_ref, or a loud exit explaining the fix.

    Every failure here is a *setup* failure, and setup failures exit 2 rather
    than 0. actions/checkout defaults to a single ref at depth 1, which leaves
    no base branch and no shared history — under that default this guard can
    see nothing, and a green tick would be a lie.
    """
    if git_out("rev-parse", "--verify", "--quiet", f"{base_ref}^{{commit}}") is None:
        cannot_check(
            f"`{base_ref}` does not exist in this clone, so there is no base to diff against.",
            "actions/checkout@v4 fetches one ref at depth 1 by default, which does not",
            "create remote-tracking refs for other branches. Fix the workflow:",
            "",
            *CHECKOUT_FIX,
            "",
            "Refusing to report success on a check that never ran.",
        )

    if (git_out("rev-parse", "--is-shallow-repository") or "").strip() == "true":
        cannot_check(
            "this is a shallow clone, so the merge base cannot be trusted.",
            f"`{base_ref}` resolves, but grafted history makes `git merge-base` either fail",
            "or answer from a truncated graph — a wrong base silently changes which files",
            "the guard thinks the PR touched. Fix the workflow:",
            "",
            *CHECKOUT_FIX,
            "",
            "Or, if the checkout must stay shallow, deepen it before this step:",
            "",
            "    git fetch --unshallow origin",
            f"    git fetch origin {base_ref.split('/')[-1]}:refs/remotes/{base_ref}",
        )

    merge_base = git_out("merge-base", base_ref, head_ref)
    if merge_base is None or not merge_base.strip():
        cannot_check(
            f"`{base_ref}` and `{head_ref}` share no common ancestor.",
            "The clone is missing history, or the branch was force-pushed onto an",
            "unrelated root. Fix the workflow:",
            "",
            *CHECKOUT_FIX,
        )
    return merge_base.strip()


def changed_files(base_ref, head_ref):
    """Paths the PR touched: the three-dot diff, i.e. base..merge-base..head.

    Three dots, not two: a two-dot diff against a moving `origin/main` reports
    every file that main changed since the branch point as though the PR had
    changed it.

    `--no-renames`, because a rename is otherwise reported as its destination
    only, which hides the deletion side. Moving a file *out* of a plugin
    changes what that plugin ships exactly as much as editing it does, and this
    repo moves content out of plugins routinely — the single-source-of-truth
    principle is what makes that a normal PR rather than an exotic one.
    """
    proc = git("diff", "--name-only", "--no-renames", "-z", f"{base_ref}...{head_ref}")
    if proc.returncode != 0:
        cannot_check(
            f"`git diff {base_ref}...{head_ref}` failed.",
            proc.stderr.strip() or "(no stderr)",
        )
    return [p for p in proc.stdout.split("\0") if p]


def load_json_at(rev, path):
    """Parse a JSON file as of `rev`; None if it does not exist there."""
    out = git_out("show", f"{rev}:{path}")
    if out is None:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        cannot_check(f"{path} at {rev[:12]} is not valid JSON — {exc}")


# --------------------------------------------------------------------------
# plugin discovery
# --------------------------------------------------------------------------

def plugin_index(marketplace):
    """Map plugin directory prefix -> {name, entry_version}, from the catalogue.

    The set of plugins is whatever `marketplace.json` says it is at that
    revision — never a hardcoded list, so adding or renaming a plugin needs no
    change here. `source` is normally the relative string form (`"./qe"`); the
    object form is accepted for completeness, taking `path` and falling back to
    the plugin name.
    """
    index = {}
    if not isinstance(marketplace, dict):
        return index
    for entry in marketplace.get("plugins") or []:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        source = entry.get("source")
        if isinstance(source, str):
            prefix = source
        elif isinstance(source, dict):
            prefix = source.get("path") or name
        else:
            prefix = None
        if not name or not prefix:
            continue
        if prefix.startswith("./"):
            prefix = prefix[2:]
        prefix = prefix.strip("/")
        # A non-local source ships from somewhere else; nothing in this repo's
        # diff can be part of it, and `..`/absolute paths are not ours to police.
        if not prefix or prefix.startswith("/") or ".." in Path(prefix).parts:
            continue
        index[prefix] = {"name": name, "entry_version": entry.get("version")}
    return index


def manifest_version(rev, prefix):
    """The plugin's version at `rev`, or a sentinel saying why there isn't one.

    The version IS the cache-key path segment, so it must be a non-empty
    string. A missing key, a null, or an unquoted number (`"version": 0.2`) is
    not one. `validate.py` does not catch those — it only compares the two
    manifests to each other, and `None == None` and `0.2 == 0.2` both pass —
    so they are caught here instead of being trusted as "some other version".
    """
    if not prefix:
        return NO_MANIFEST
    manifest = load_json_at(rev, f"{prefix}/.claude-plugin/plugin.json")
    if not isinstance(manifest, dict):
        return NO_MANIFEST
    version = manifest.get("version")
    if not isinstance(version, str) or not version.strip():
        return NOT_A_VERSION
    return version


def changelog_mentions(rev, prefix, version):
    """Does `<prefix>/CHANGELOG.md` at `rev` carry a heading for `version`?

    Deliberately loose: any Markdown heading line containing the version as a
    whole token counts, so the file's exact heading style is not a CI contract.
    The check exists so that the release note lands in the same diff as the
    bump a reviewer is looking at, not to police formatting.

    Returns True, False, or None when there is no CHANGELOG.md at all.
    """
    text = git_out("show", f"{rev}:{prefix}/CHANGELOG.md")
    if text is None:
        return None
    pattern = re.compile(r"(?<![\w.-])" + re.escape(version) + r"(?![\w.-])")
    return any(line.lstrip().startswith("#") and pattern.search(line)
               for line in text.splitlines())


def version_key(version):
    """Leading numeric components of a version, or None if it is not numeric.

    Only used to catch a *downgrade*; anything with a pre-release suffix or a
    non-numeric shape returns None and the ordering check is skipped rather
    than guessed at. The equality checks do not depend on this.
    """
    if not isinstance(version, str):
        return None
    parts = version.split(".")
    if not parts or not all(p.isdigit() for p in parts):
        return None
    return tuple(int(p) for p in parts)


def group_by_plugin(files, prefixes):
    """Bucket changed files under the longest plugin prefix that contains them."""
    ordered = sorted(prefixes, key=len, reverse=True)
    touched = {}
    for path in files:
        for prefix in ordered:
            if path == prefix or path.startswith(prefix + "/"):
                touched.setdefault(prefix, []).append(path)
                break
    return touched


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def files_phrase(paths):
    return f"{len(paths)} file{'' if len(paths) == 1 else 's'}"


def describe(paths):
    shown = paths[:MAX_LISTED]
    lines = [f"      {p}" for p in shown]
    if len(paths) > len(shown):
        lines.append(f"      … and {len(paths) - len(shown)} more")
    return lines


CACHE_NOTE = (
    "      This is delivery, not bookkeeping. The install cache is keyed by the",
    "      version string — ~/.claude/plugins/cache/<marketplace>/{name}/<version>/",
    "      — and `claude plugin update` compares version strings only. Without a new",
    "      one, every consuming repo is told \"already at the latest version\" and",
    "      goes on running the old files.",
)


def failure_report(failure):
    name, prefix, paths = failure["name"], failure["prefix"], failure["paths"]
    kind = failure["kind"]
    manifest = f"{prefix}/.claude-plugin/plugin.json" if prefix else "the plugin manifest"

    if kind == "downgrade":
        headline = (f"  {name} — {files_phrase(paths)} changed and the version went "
                    f"BACKWARDS, {failure['base']!r} → {failure['head']!r}")
        remedy = [
            f"      Fix: choose a version above {failure['base']!r}. A version string is a",
            "      cache key, so reusing an old one leaves anybody who installed that",
            "      version with their stale copy and no way to be told about it.",
        ]
    elif kind == "reused":
        headline = (f"  {name} — {files_phrase(paths)} changed and {failure['head']!r} is "
                    f"already published on the base branch")
        remedy = [
            f"      Fix: choose a version above {failure['base']!r} — the branch is behind",
            "      the base and is reusing a version string that is already serving as a",
            "      cache key, so the new content would never reach anyone who has it.",
            "      Rebase onto the base branch first, then pick the next version.",
        ]
    elif kind == "no_version":
        headline = (f"  {name} — {files_phrase(paths)} changed and there is no usable "
                    f"version string in {manifest}")
        remedy = [
            "      Fix: set \"version\" to a quoted semver string, e.g. \"0.2.1\". An unquoted",
            "      number (0.2), a null, or a missing key is not a cache-key path segment.",
            "      scripts/validate.py does not catch this: it only compares plugin.json to",
            "      the marketplace entry, and two identical non-strings compare equal.",
        ]
    elif kind in ("no_changelog", "no_entry"):
        missing = ("CHANGELOG.md does not exist" if kind == "no_changelog"
                   else f"CHANGELOG.md has no heading for {failure['head']!r}")
        headline = (f"  {name} — bumped to {failure['head']!r} but "
                    f"{prefix}/{missing}")
        remedy = [
            f"      Fix: add a heading for {failure['head']!r} at the top of",
            f"      {prefix}/CHANGELOG.md, above the previous version, saying what a user",
            "      of this plugin can now do or what behaves differently. One line is the",
            "      right length for a small change.",
            "",
            "      The entry belongs in this diff because the changelog ships inside the",
            "      plugin directory: it is the only record of what changed that reaches",
            "      someone whose copy is an extracted install cache with no git history.",
            "      Any Markdown heading containing the version satisfies this check — the",
            "      format is not a CI contract.",
        ]
        return [headline, "", *remedy]
    else:  # "unbumped"
        headline = (f"  {name} — {files_phrase(paths)} of shipped content changed, "
                    f"version still {failure['head']!r}")
        remedy = [
            f"      Fix: raise \"version\" in {manifest} and in",
            f"      the `{name}` entry of {MARKETPLACE_PATH} (scripts/validate.py",
            "      enforces that the two agree), and add the matching entry to",
            f"      {prefix}/CHANGELOG.md. Semver as this repo already uses it:",
            "      patch for a fix, minor for new or reworked capability.",
        ]

    return [
        headline,
        *describe(paths),
        "",
        *remedy,
        "",
        *(line.format(name=name) for line in CACHE_NOTE),
    ]


# --------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Fail a PR that changes plugin files without bumping the plugin version."
    )
    parser.add_argument(
        "--base", default="origin/main",
        help="base ref the PR targets (default: origin/main)",
    )
    parser.add_argument(
        "--head", default="HEAD",
        help="head ref under test (default: HEAD)",
    )
    args = parser.parse_args(argv)

    merge_base = resolve_merge_base(args.base, args.head)
    files = changed_files(args.base, args.head)

    # Three views of the catalogue. The merge base is where the branch forked;
    # the base *tip* is what is published right now (a branch that is behind can
    # otherwise land a version already in use as a cache key); HEAD is what the
    # PR proposes.
    base_index = plugin_index(load_json_at(merge_base, MARKETPLACE_PATH) or {})
    tip_index = plugin_index(load_json_at(args.base, MARKETPLACE_PATH) or {})
    head_market = load_json_at(args.head, MARKETPLACE_PATH)
    if head_market is None:
        cannot_check(
            f"{MARKETPLACE_PATH} does not exist at {args.head}.",
            "Without the catalogue there is no way to discover which directories are plugins.",
        )
    head_index = plugin_index(head_market)

    touched = group_by_plugin(files, set(base_index) | set(tip_index) | set(head_index))

    # Everything below is keyed by plugin NAME, not by directory prefix. `source`
    # is only where a plugin happens to live in one revision: keying on the
    # prefix makes relocating a plugin look like a delete plus a brand-new
    # plugin, and both halves of that pair are exempt from a bump.
    prefixes_of = {}
    for index, rev_key in ((base_index, "base"), (tip_index, "tip"), (head_index, "head")):
        for prefix, meta in index.items():
            prefixes_of.setdefault(meta["name"], {})[rev_key] = prefix

    print(f"version-bump guard: base {args.base} (merge base {merge_base[:12]}), "
          f"{len(files)} file(s) changed")

    if args.head == "HEAD":
        dirty = [ln for ln in (git_out("status", "--porcelain") or "").splitlines() if ln]
        if dirty:
            print(f"  note {len(dirty)} uncommitted change(s) in the working tree are NOT "
                  f"part of this check — it reads committed history only.")

    failures = []
    reported = False

    for name in sorted(prefixes_of):
        slots = prefixes_of[name]
        paths = sorted({p for slot in slots.values() for p in touched.get(slot, [])})
        if not paths:
            continue
        reported = True

        head_prefix = slots.get("head")
        if head_prefix is None:
            print(f"  ok  {name} — removed from {MARKETPLACE_PATH} at {args.head}; "
                  f"no bump required ({files_phrase(paths)})")
            continue

        # Every version this plugin is already published under, on either the
        # fork point or the current base tip.
        published = {v for v in (manifest_version(merge_base, slots.get("base")),
                                 manifest_version(args.base, slots.get("tip")))
                     if isinstance(v, str)}

        head_version = manifest_version(args.head, head_prefix)
        if not isinstance(head_version, str):
            why = ("no plugin.json" if head_version is NO_MANIFEST
                   else "\"version\" is missing or not a string")
            failures.append({"name": name, "prefix": head_prefix, "paths": paths,
                             "base": None, "head": None, "kind": "no_version"})
            print(f"  !!  {name} — {files_phrase(paths)} changed and "
                  f"{head_prefix}/.claude-plugin/plugin.json has no usable version "
                  f"({why})")
            continue

        entry_version = head_index[head_prefix].get("entry_version")
        if entry_version not in (None, head_version):
            print(f"  note {name} — {MARKETPLACE_PATH} says {entry_version!r}, "
                  f"plugin.json says {head_version!r}; using plugin.json "
                  f"(scripts/validate.py reports the mismatch)")

        # `published` is a set, and every unorderable version shares the key ().
        # max() over tied keys returns whichever element iteration reached first,
        # and set order for strings varies with hash randomisation — so two
        # pre-release versions would make `highest` differ between runs. Sorting
        # first makes the tie-break the version string itself: still arbitrary,
        # but the same arbitrary answer every time. A guard that reports
        # different things on different runs cannot be trusted with either.
        highest = (max(sorted(published), key=lambda v: version_key(v) or ())
                   if published else None)
        unorderable = sorted(v for v in published if version_key(v) is None)
        if unorderable:
            print(f"  note {name} — {', '.join(repr(v) for v in unorderable)} "
                  f"{'is' if len(unorderable) == 1 else 'are'} not X.Y.Z, so the "
                  f"downgrade check is skipped for this plugin; the version must "
                  f"still differ from every published one")
        record = {"name": name, "prefix": head_prefix, "paths": paths,
                  "base": highest, "head": head_version}

        if published:
            if head_version in published:
                record["kind"] = "unbumped" if head_version == highest else "reused"
                failures.append(record)
                if record["kind"] == "unbumped":
                    print(f"  !!  {name} — {files_phrase(paths)} changed, version still "
                          f"{head_version!r}")
                else:
                    print(f"  !!  {name} — {files_phrase(paths)} changed and "
                          f"{head_version!r} is already published (base tip is at "
                          f"{highest!r})")
                continue

            base_key, head_key = version_key(highest), version_key(head_version)
            if base_key and head_key and head_key < base_key:
                record["kind"] = "downgrade"
                failures.append(record)
                print(f"  !!  {name} — version went backwards, {highest} → {head_version}")
                continue

        # The version is usable. The release it names still owes an entry, in
        # this diff, where the reviewer looking at the content change can see it.
        entry = changelog_mentions(args.head, head_prefix, head_version)
        if entry is not True:
            record["kind"] = "no_changelog" if entry is None else "no_entry"
            failures.append(record)
            print(f"  !!  {name} — {highest or 'new'} → {head_version}, but "
                  f"{head_prefix}/CHANGELOG.md "
                  f"{'does not exist' if entry is None else 'has no entry for it'}")
            continue

        if highest is None:
            print(f"  ok  {name} — new plugin at {head_version!r} "
                  f"({files_phrase(paths)}); no published version to bump from")
        else:
            print(f"  ok  {name} — {highest} → {head_version} ({files_phrase(paths)})")

    if not reported:
        print("  ok  no plugin directory touched — nothing to bump")
        return EXIT_OK

    if failures:
        plural = "" if len(failures) == 1 else "s"
        sys.stdout.flush()
        print(f"\nversion-bump guard: {len(failures)} plugin{plural} cannot ship as "
              f"proposed.\n", file=sys.stderr)
        for failure in failures:
            for line in failure_report(failure):
                print(line, file=sys.stderr)
            print("", file=sys.stderr)
        sys.stderr.flush()
        return EXIT_UNBUMPED

    print("\nversion-bump guard: every touched plugin carries a new version.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
