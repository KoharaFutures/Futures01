#!/usr/bin/env python3
"""Fail the commit if any message lacks a resolvable RE: header.

Seven agents cross-reference each other constantly, and an ambiguous reference does not
announce itself - it sends the reader to the wrong finding and surfaces later as an
untraceable disagreement. This enforces the one thing that prevents it: every message
states what it is about, in an id whose shape says who issued it.

Usage:
    python3 workspace/roundtable/check_refs.py
"""
from __future__ import annotations

import pathlib
import re
import sys

MSGS = pathlib.Path("workspace/roundtable/msgs")

# Written before REGISTRY.md existed, so they cannot be held to it. Named rather than
# skipped by a number threshold, so the exemption cannot silently widen. Note that
# 02_BT1_R1 is substantively compliant - it carries a bold "**Re:**" line naming
# ALGO-1 - just not in the machine-readable form.
PRE_REGISTRY = frozenset({
    "01_manager_all_division.md",
    "02_BT1_R1_verify-ALGO-1.md",
    # BT2 and BT3 were dispatched before REGISTRY.md existed, so their round-1 fidelity
    # questions cannot be held to it either. Both name their subject in prose.
    "04_BT3_R3_verify-ALGO-1.md",
    "05_BT2_R2_verify-ALGO-1.md",
})

# <ISSUER>-<KIND>-<n> and the kinds that legitimately have no issuer prefix
# (avenues and programme-wide defects are allocated centrally, so they cannot collide).
ID = re.compile(
    r"""^(
        MAIN-\d{2}(/S\d+)?          # MAIN-01, MAIN-01/S2
      | (I|II|III|X)-\d+            # avenue: I-12, X-4
      | DISC-LEAD-\d+
      | D\d+                        # programme-wide defect
      | (R[123]|BT[123]|DISC)-      # issuer-prefixed:
        (Q\d+|REQ-\d+|ALGO-\d+|D\d+[a-z]?|[AB]-\d+)
      | MGR-(T\d+|Q\d+|REQ-\d+)    # manager task / question / request
      | ADJ-\d+                     # manager adjudication
      | R-\d+                       # board rule
      | D-[A-Z]+\d+                 # researcher-local defect note, e.g. D-L1, D-MTF3
      | X-\d+                       # cross-cutting avenue
      | round-1                     # the pre-registry round
      | none
    )$""",
    re.VERBOSE,
)


def check(path: pathlib.Path) -> list[str]:
    head = path.read_text().splitlines()[:12]
    problems: list[str] = []
    fields = {}
    for line in head:
        m = re.match(r"^(RE|ALSO|FROM|TO|TASK):\s*(.*)$", line.strip())
        if m:
            fields[m.group(1)] = m.group(2).strip()

    if "RE" not in fields:
        return [f"{path.name}: no RE: header in the first 12 lines"]

    # RE: is the load-bearing field and is strict - it must resolve to exactly one id,
    # because it is what a reader follows. ALSO: is advisory, so it only has to CONTAIN
    # a recognisable id; prose, filenames and paths alongside are useful, not errors.
    re_raw = fields.get("RE", "")
    re_toks = [t for t in re.split(r"[,\s]+", re_raw) if t]
    re_ids = [t for t in re_toks if ID.match(t)]
    if not re_toks:
        problems.append(f"{path.name}: RE: is empty")
    elif not re_ids:
        problems.append(
            f"{path.name}: RE: '{re_raw}' contains no registry id "
            f"(see REGISTRY.md; a bare Q2 is ambiguous)")
    elif len(re_ids) > 1:
        problems.append(
            f"{path.name}: RE: names {len(re_ids)} ids ({', '.join(re_ids)}); "
            f"RE: takes exactly one - put the rest in ALSO:")

    also_raw = fields.get("ALSO", "none")
    also_toks = [t for t in re.split(r"[,\s]+", also_raw) if t]
    if not also_toks:
        problems.append(f"{path.name}: ALSO: is empty (use 'none')")
    elif not any(ID.match(t) or t.endswith(".md") or "/" in t or t.lower() == "none"
                 for t in also_toks):
        problems.append(
            f"{path.name}: ALSO: '{also_raw}' contains no id, path or 'none'")
    for field in ("FROM", "TO"):
        if field not in fields:
            problems.append(f"{path.name}: no {field}: header")
    return problems


def main() -> int:
    if not MSGS.is_dir():
        print("no msgs/ directory yet - nothing to check")
        return 0
    files = sorted(p for p in MSGS.glob("*.md"))

    # The shared counter collided under parallelism (two 03s, two 04s, three 05s).
    # Report it so a bare "see msgs/04" is never trusted, but do not fail on the
    # legacy files - they are write-once and already cited.
    import collections
    lead = collections.Counter()
    for p in files:
        head = p.name.split("_", 1)[0]
        if head.isdigit():
            lead[head] += 1
    dupes = {k: v for k, v in lead.items() if v > 1}
    if dupes:
        print("NOTE  shared-counter collisions (cite these by full filename, never by number):")
        for k in sorted(dupes):
            names = [p.name for p in files if p.name.startswith(k + "_")]
            print(f"  {k}: {dupes[k]} files -> {', '.join(names)}")
        print()
    allp: list[str] = []
    skipped = 0
    for p in files:
        if p.name in PRE_REGISTRY:
            skipped += 1
            continue
        allp += check(p)
    if allp:
        print(f"REFERENCES FAILED - {len(allp)} problem(s) across {len(files)} message(s)\n")
        print("\n".join("  " + x for x in allp))
        return 1
    print(f"references clean - {len(files) - skipped} checked, "
          f"{skipped} pre-registry, every one resolvable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
