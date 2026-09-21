#!/usr/bin/env python3
"""tracker_lint.py — report-only readability and structure lint for a project tracker.

Reads a snapshot written by tracker_snapshot.py (`--json`) and reports, never fixes:

    tracker_snapshot.py owner/repo#7 --json | tracker_lint.py -
    tracker_lint.py .qe/snapshot.json [--stamp-budget 200] [--next-words 40] [--title-chars 80]

The checks are the mechanical ones QEP-6's Adoption clause names for a lint, plus the
readability budgets the qe skills keep (numbers are the skills', not the QEP's):

  STAMP      one stamp, in the canonical form, with a readable date
  NEXT       at most one `**Next:**` line, in the stamp section, one line long
  BUDGET     the stamp section's length against the budget
  STORY      dated past-event paragraphs under the stamp — history in the state register
  ROSTER     a numbered list of work items outside the sub-issue list
  PHASESTAT  status words or dates written into the phase table
  GATEPROSE  gate prose that restates an edge the platform already holds
  CHECKBOX   checkbox work lists in the body
  SEQTOKEN   sequence tokens in child titles or milestone names
  TITLELEN   child titles over the length budget
  PHASES     phase carrier coverage — milestones or body markers — over the children

Exit status is always 0: the report is the product.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys

DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
BOLD_LEAD = re.compile(r"^\s*\*\*(?P<lead>[^*]{1,160})\*\*")
PAST_WORDS = re.compile(r"\b(built|done|decided|merged|shipped|landed|released|closed|completed|fixed|recorded|filed|applied)\b", re.I)
NEXT_LINE = re.compile(r"^\s*\*\*Next:\*\*", re.M)
ORDERED_ITEM = re.compile(r"^\s*\d+\.\s+(.*)$")
ISSUE_REF = re.compile(r"(?<![\w/])(?:[\w.-]+/[\w.-]+)?#(\d+)\b")
CHECKBOX = re.compile(r"^\s*[-*]\s+\[[ xX]\]", re.M)
SEQ_TOKEN = re.compile(r"^(?:W\d+\b|Phase\s*\d+\s*[:—-]|Stage\s*\d+\s*[:—-]|wp\d+-stage\d+)", re.I)
STATUS_WORDS = re.compile(r"\b(done|closed|complete[d]?|in progress|underway|shipped|merged)\b", re.I)
GATE_WORDS = re.compile(r"\b(wait|waits|waiting|blocked|blocks|gate|gated|after|before|depends|until)\b", re.I)


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def stamp_section(body: str) -> tuple[str, str | None]:
    """The text under the `## Where we stand` heading up to the next `## `, and the heading line."""
    m = re.search(r"^(#{2,3})[ \t]+Where we stand.*$", body, re.M | re.I)
    if not m:
        return "", None
    level = len(m.group(1))
    rest = body[m.end():]
    nxt = re.search(rf"^#{{1,{level}}}[ \t]+\S", rest, re.M)
    return (rest[: nxt.start()] if nxt else rest), m.group(0)


def phase_table(body: str) -> list[list[str]]:
    rows = []
    lines = body.splitlines()
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("|") and re.search(r"\|\s*phase", ln, re.I) and i + 1 < len(lines) and re.match(r"^\s*\|\s*:?-", lines[i + 1]):
            j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[j].strip().strip("|").split("|")])
                j += 1
            break
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("snapshot", help="path to a JSON snapshot, or - for stdin")
    p.add_argument("--stamp-budget", type=int, default=200, help="words allowed under the stamp (default 200)")
    p.add_argument("--next-words", type=int, default=40, help="words allowed on the Next: line (default 40)")
    p.add_argument("--title-chars", type=int, default=80, help="characters allowed in a child title (default 80)")
    p.add_argument("--json", action="store_true", help="emit findings as JSON")
    a = p.parse_args(argv)
    snap = json.load(sys.stdin if a.snapshot == "-" else open(a.snapshot))
    t, kids = snap["tracker"], snap["children"]
    body = (t.get("body") or "").replace("\r\n", "\n")
    findings: list[dict] = []

    def add(code, msg, detail=None):
        findings.append({"code": code, "message": msg, **({"detail": detail} if detail else {})})

    # STAMP
    st = t["stamp"]
    headings = len(re.findall(r"^#{2,3}[ \t]+Where we stand\b", body, re.M | re.I))
    if st["form"] == "heading" and headings == 1:
        pass
    elif st["form"] == "heading":
        add("STAMP", f"{headings} `Where we stand` headings; the contract wants exactly one")
    elif st["heading_present"]:
        add("STAMP", "a `Where we stand` heading is present but its parenthetical is not `(verified YYYY-MM-DD[ HH:MM TZ])` — stamp-unreadable")
    elif st["form"] == "banner":
        add("STAMP", "stamped by the `> **Updated …**` banner only; the canonical form is the heading")
    else:
        add("STAMP", "unstamped: no `## Where we stand (verified YYYY-MM-DD)` heading")
    section, _ = stamp_section(body)
    stamp_date = dt.date.fromisoformat(st["date"]) if st.get("date") else None

    # NEXT
    nexts = NEXT_LINE.findall(body)
    if len(nexts) > 1:
        add("NEXT", f"{len(nexts)} `**Next:**` lines; the body carries one, in the stamp section")
    if nexts and not NEXT_LINE.search(section):
        add("NEXT", "the `**Next:**` line is outside the stamp section")
    for m in NEXT_LINE.finditer(section):
        para = paragraphs(section[m.start():])[0] if paragraphs(section[m.start():]) else ""
        words = len(para.split())
        if words > a.next_words:
            add("NEXT", f"the `Next:` line is {words} words; budget {a.next_words} — one work item and one line of pickup context")

    # BUDGET
    swords = len(section.split())
    if swords > a.stamp_budget:
        add("BUDGET", f"the stamp section is {swords} words; budget {a.stamp_budget}")

    # STORY — dated past-event paragraphs under the stamp
    story = []
    for para in paragraphs(section):
        if NEXT_LINE.match(para):
            continue
        lead = BOLD_LEAD.match(para)
        head = lead.group("lead") if lead else para[:120]
        dates = [d for d in DATE.findall(head)]
        past = PAST_WORDS.search(head) is not None
        older = any(stamp_date and dt.date.fromisoformat(d) < stamp_date for d in dates if _is_date(d))
        if (dates and past) or older:
            story.append(f"[{len(para.split())} words] {head.strip()[:90]}")
    if story:
        add("STORY", f"{len(story)} dated past-event paragraph(s) under the stamp — history in the state register; move them to the revision-log comment", story)

    # ROSTER — numbered lists whose items are mostly work-item references
    items = [m.group(1) for m in ORDERED_ITEM.finditer(body)]
    runs, run = [], []
    for ln in body.splitlines():
        if ORDERED_ITEM.match(ln):
            run.append(ln)
        else:
            if len(run) >= 3:
                runs.append(run)
            run = []
    if len(run) >= 3:
        runs.append(run)
    for r in runs:
        with_ref = sum(1 for ln in r if ISSUE_REF.search(ln))
        if with_ref >= max(3, int(0.6 * len(r))):
            add("ROSTER", f"a numbered list of {len(r)} items, {with_ref} naming work items — a roster restating list order; sequencing rationale explains why, it never enumerates", [ln.strip()[:90] for ln in r[:4]])

    # PHASESTAT — status or dates in the phase table
    rows = phase_table(body)
    flagged = []
    for row in rows:
        for cell in row[1:]:
            if DATE.search(cell) or re.search(r"\*\*[^*]*\b(done|closed)\b", cell, re.I):
                flagged.append(f"{row[0][:30]} → {cell[:70]}")
                break
    if flagged:
        add("PHASESTAT", f"{len(flagged)} phase-table row(s) carry a date or a completion claim — status in the phase table is a mirror; the list (or the milestone) holds it", flagged)

    # GATEPROSE — pairs that are native edges and are also stated in gate-like prose
    edges = []
    for c in kids:
        for b in (c["blocked_by"]["open"] or []):
            edges.append((c, b))
    restated = []
    for c, b in edges:
        cn, bn = str(c["number"]), b.split("#")[1]
        for para in paragraphs(body):
            if GATE_WORDS.search(para) and re.search(rf"#{cn}\b", para) and re.search(rf"#{bn}\b", para):
                restated.append(f"{c['ref']} ← {b}")
                break
    if restated:
        add("GATEPROSE", f"{len(restated)} native blocked-by edge(s) are also spelled out in gate prose — the platform holds the edge; the body keeps only the rationale", sorted(set(restated)))

    # CHECKBOX
    n_cb = len(CHECKBOX.findall(body))
    if n_cb:
        add("CHECKBOX", f"{n_cb} checkbox item(s) in the body — never read as progress; work lists belong in sub-issues")

    # SEQTOKEN / TITLELEN
    seq = [c["ref"] + "  " + c["title"][:60] for c in kids if SEQ_TOKEN.match(c["title"])]
    if seq:
        add("SEQTOKEN", f"{len(seq)} child title(s) carry a sequence token — order lives in list position, never in names", seq)
    ms = sorted({c["milestone"] for c in kids if c.get("milestone")})
    bad_ms = [m for m in ms if m.isdigit() or SEQ_TOKEN.match(m)]
    if bad_ms:
        add("SEQTOKEN", "milestone names carry a sequence token or are purely numeric", bad_ms)
    long_t = [f"{c['ref']}  ({len(c['title'])})  {c['title'][:70]}…" for c in kids if len(c["title"]) > a.title_chars]
    if long_t:
        add("TITLELEN", f"{len(long_t)} child title(s) over {a.title_chars} characters — the sub-issue list is the first digest, and long titles do not scan", long_t)

    # PHASES — carrier coverage
    if kids:
        with_ms = sum(1 for c in kids if c.get("milestone"))
        with_marker = sum(1 for c in kids if c.get("phase"))
        work = [c for c in kids if c["role"] == "work"]
        uncovered = [c for c in work if not c.get("milestone") and not c.get("phase")]
        if rows and uncovered:
            add("PHASES", f"the body has a phase table with {len(rows)} rows, but {len(uncovered)} of {len(work)} work items carry neither a milestone nor a `Part of #N (Phase k)` marker — phase progress cannot be derived for them",
                [f"{c['ref']}  {c['title'][:60]}" for c in uncovered[:8]])
        elif not rows and (with_ms or with_marker):
            add("PHASES", "children carry phase markers or milestones but the body has no phase table (intent and exit criterion)")

    # Report
    words = len(body.split())
    longest = max((len(p.split()) for p in paragraphs(body)), default=0)
    if a.json:
        json.dump({"tracker": t["ref"], "words": words, "stamp_words": swords, "longest_paragraph": longest, "findings": findings}, sys.stdout, indent=1)
        print()
        return 0
    print(f"tracker-lint — {t['ref']} · {t['type'] or 'untyped'} · stamp {st['form']} {st.get('date') or ''} · "
          f"{words} words, {swords} under the stamp, longest paragraph {longest} words · "
          f"{len(kids)} children ({t['sub_issues_summary']['completed']} closed) · comments {t.get('comments')}")
    if not findings:
        print("  ok — nothing to report")
    for f in findings:
        print(f"  {f['code']:<10} {f['message']}")
        for d in f.get("detail") or []:
            print(f"             · {d}")
    return 0


def _is_date(s: str) -> bool:
    try:
        dt.date.fromisoformat(s)
        return True
    except ValueError:
        return False


if __name__ == "__main__":
    sys.exit(main())
