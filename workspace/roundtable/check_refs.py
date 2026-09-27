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

    for field in ("RE", "ALSO"):
        raw = fields.get(field, "none")
        if not raw:
            problems.append(f"{path.name}: {field}: is empty (use 'none')")
            continue
        for tok in re.split(r"[,\s]+", raw):
            if tok and not ID.match(tok):
                problems.append(
                    f"{path.name}: {field}: '{tok}' is not a registry id shape "
                    f"(see REGISTRY.md; a bare Q2 is ambiguous)")
    for field in ("FROM", "TO"):
        if field not in fields:
            problems.append(f"{path.name}: no {field}: header")
    return problems


def main() -> int:
    if not MSGS.is_dir():
        print("no msgs/ directory yet - nothing to check")
        return 0
    files = sorted(p for p in MSGS.glob("*.md"))
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
