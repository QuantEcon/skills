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
    print(f"  ok  /{plugin_name}:{skill_dir.name}")


def check_plugin(entry):
    name = entry.get("name")
    if not name:
        error("marketplace.json: plugin entry missing `name`")
        return
    path = entry.get("source", {}).get("path", name)
    plugin_dir = ROOT / path
    if not plugin_dir.is_dir():
        error(f"marketplace.json: plugin `{name}` points at missing directory `{path}`")
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

    plugins = marketplace.get("plugins", [])
    if not plugins:
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
