#!/usr/bin/env python3
"""Validate the marketplace catalogue, plugin manifests, and skill frontmatter.

Run from the repository root:

    python scripts/validate.py

Exits non-zero with a list of problems if anything is inconsistent. Catching
these here matters because a malformed manifest breaks plugin installation
silently in every consuming lecture repository.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKETPLACE = ROOT / ".claude-plugin" / "marketplace.json"

errors = []


def error(msg):
    errors.append(msg)


def load_json(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        error(f"{path.relative_to(ROOT)}: missing")
    except json.JSONDecodeError as exc:
        error(f"{path.relative_to(ROOT)}: invalid JSON — {exc}")
    return None


def parse_frontmatter(path):
    """Return the YAML frontmatter of a SKILL.md as a dict of top-level keys.

    Deliberately not a full YAML parse — skill frontmatter is flat `key: value`
    and avoiding a PyYAML dependency keeps this runnable anywhere.
    """
    text = path.read_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        error(f"{path.relative_to(ROOT)}: no YAML frontmatter block")
        return None
    fields = {}
    for line in match.group(1).split("\n"):
        if line.startswith(" ") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def check_skill(skill_dir, plugin_name):
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        error(f"{skill_dir.relative_to(ROOT)}: no SKILL.md")
        return
    fields = parse_frontmatter(skill_md)
    if fields is None:
        return
    errors_before = len(errors)
    rel = skill_md.relative_to(ROOT)
    name = fields.get("name")
    if not name:
        error(f"{rel}: frontmatter missing `name`")
    elif name != skill_dir.name:
        error(f"{rel}: frontmatter name `{name}` != directory `{skill_dir.name}`")
    description = fields.get("description")
    if not description:
        error(f"{rel}: frontmatter missing `description`")
    elif len(description) < 40:
        error(f"{rel}: description too short to trigger reliably ({len(description)} chars)")
    if len(errors) == errors_before:
        print(f"  ok  /{plugin_name}:{skill_dir.name}")
    else:
        print(f"  !!  /{plugin_name}:{skill_dir.name} — see problems below")


def resolve_source(entry, name):
    """Locate a plugin's directory from its `source`, and reject sources that
    would break install.

    A plugin co-located with this marketplace must use a relative-path source
    (`"./qe"`) so install uses the already-present marketplace copy. A remote
    source pointing back at this repo forces an install-time re-clone — the SSH
    failure reported in QuantEcon/skills#10 — so we flag it here rather than let
    it reach users. Returns the resolved directory Path, or None if the source
    is malformed.
    """
    source = entry.get("source")
    if source is None:
        error(f"marketplace.json: plugin `{name}` missing `source`")
        return None
    if isinstance(source, str):
        if not source.startswith("./"):
            error(
                f"marketplace.json: plugin `{name}` source `{source}` must start "
                f"with `./` (a path relative to the marketplace root)"
            )
            return None
        return ROOT / source[2:]
    if isinstance(source, dict):
        target = str(source.get("repo") or source.get("url") or "")
        if "QuantEcon/skills" in target:
            error(
                f"marketplace.json: plugin `{name}` uses a remote source pointing "
                f"back at this repo, which forces an install-time re-clone (SSH "
                f"failure in #10). Use a relative path: \"source\": \"./{name}\"."
            )
        return ROOT / source.get("path", name)
    error(
        f"marketplace.json: plugin `{name}` source must be a relative path string "
        f"or an object, got {type(source).__name__}"
    )
    return None


def check_plugin(entry):
    if not isinstance(entry, dict):
        error(f"marketplace.json: plugin entry must be an object, got {type(entry).__name__}")
        return
    name = entry.get("name")
    if not name:
        error("marketplace.json: plugin entry missing `name`")
        return

    plugin_dir = resolve_source(entry, name)
    if plugin_dir is None:
        return
    if not plugin_dir.is_dir():
        rel = plugin_dir.relative_to(ROOT) if ROOT in plugin_dir.parents else plugin_dir
        error(f"marketplace.json: plugin `{name}` points at missing directory `{rel}`")
        return

    manifest = load_json(plugin_dir / ".claude-plugin" / "plugin.json")
    if manifest is None:
        return
    print(f"plugin: {name}")
    if manifest.get("name") != name:
        error(
            f"{path}/.claude-plugin/plugin.json: name `{manifest.get('name')}` "
            f"!= marketplace entry `{name}`"
        )
    if manifest.get("version") != entry.get("version"):
        error(
            f"plugin `{name}`: version mismatch — plugin.json "
            f"{manifest.get('version')!r} vs marketplace.json {entry.get('version')!r}"
        )
    if manifest.get("description") != entry.get("description"):
        error(f"plugin `{name}`: description differs between plugin.json and marketplace.json")

    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        error(f"{path}: no skills/ directory")
        return
    skill_dirs = sorted(d for d in skills_dir.iterdir() if d.is_dir())
    if not skill_dirs:
        error(f"{path}/skills: contains no skills")
    for skill_dir in skill_dirs:
        check_skill(skill_dir, name)


def main():
    marketplace = load_json(MARKETPLACE)
    if marketplace is None:
        print("\n".join(errors), file=sys.stderr)
        return 1

    # `owner` is a required top-level object in the marketplace schema; a manifest
    # missing it is rejected by `/plugin marketplace add` (QuantEcon/skills#10).
    owner = marketplace.get("owner")
    if not isinstance(owner, dict) or not owner.get("name"):
        error("marketplace.json: missing required `owner` object with a `name` field")

    plugins = marketplace.get("plugins", [])
    if not isinstance(plugins, list):
        error(f"marketplace.json: `plugins` must be a list, got {type(plugins).__name__}")
        plugins = []
    elif not plugins:
        error("marketplace.json: no plugins registered")
    for entry in plugins:
        check_plugin(entry)

    if errors:
        print(f"\n{len(errors)} problem(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"\nAll {len(plugins)} plugin(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
