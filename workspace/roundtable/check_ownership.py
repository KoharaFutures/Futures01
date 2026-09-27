#!/usr/bin/env python3
"""Audit that no agent wrote a file it does not own.

Mode bits cannot enforce ownership here - every agent runs as root. So ownership is a
convention, and this is the thing that makes a convention real: it runs at the commit
boundary, and the parent session reverts anything it flags.

Usage:
    python3 workspace/roundtable/check_ownership.py <agent> [<agent> ...] [--allow <path>]

Each <agent> is a writer name from OWNERSHIP.md: parent, discovery, manager, or a
researcher id such as R1. Pass the agents that were dispatched in the round being
committed. Exit status is 1 if any changed path has no owner among them.
"""
from __future__ import annotations

import fnmatch
import subprocess
import sys

ROOT = "workspace/roundtable/"

# Most specific pattern wins, so order matters: the first match is the owner.
RULES: list[tuple[str, str]] = [
    ("tests/test_bt1_*.py", "BT1"),
    ("tests/test_bt2_*.py", "BT2"),
    ("tests/test_bt3_*.py", "BT3"),
    (ROOT + "discovery/AVENUES.md", "discovery"),
    (ROOT + "discovery/MAIN_TASKS.md", "discovery"),
    (ROOT + "discovery/bursts/*", "discovery"),
    (ROOT + "manager/*", "manager"),
    (ROOT + "DIVISION.md", "manager"),
    (ROOT + "OPEN_QUESTIONS.md", "manager"),
    (ROOT + "research/R1*", "R1"),
    (ROOT + "research/R2*", "R2"),
    (ROOT + "research/R3*", "R3"),
    (ROOT + "backtest/BT1/*", "BT1"),
    (ROOT + "backtest/BT2/*", "BT2"),
    (ROOT + "backtest/BT3/*", "BT3"),
    (ROOT + "BRIEF.md", "parent"),
    (ROOT + "THROTTLE.md", "parent"),
    (ROOT + "LEDGER.md", "parent"),
    (ROOT + "OWNERSHIP.md", "parent"),
    (ROOT + "PIPELINE.md", "parent"),
    (ROOT + "check_ownership.py", "parent"),
    (ROOT + "check_refs.py", "parent"),
    (ROOT + "REGISTRY.md", "parent"),
]


def owner(path: str) -> str | None:
    """The sole writer of ``path``, or None if the tree does not assign one."""
    for pattern, who in RULES:
        if fnmatch.fnmatch(path, pattern):
            return who
    if fnmatch.fnmatch(path, ROOT + "msgs/*"):
        # Write-once: the creator owns it. A *modified* message is always a violation,
        # whoever did it, because nobody may edit a message after it is posted.
        return "msgs"
    return None


def changed() -> list[tuple[str, str]]:
    out = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", ROOT, "tests"],
        capture_output=True, text=True, check=True,
    ).stdout
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        rows.append((line[:2].strip(), line[3:].strip()))
    return rows


def main(argv: list[str]) -> int:
    args = argv[1:]
    allowed: set[str] = set()
    dispatched: set[str] = set()
    it = iter(args)
    for a in it:
        if a == "--allow":
            allowed.add(next(it, ""))
        else:
            dispatched.add(a)
    if not dispatched:
        print("usage: check_ownership.py <agent> [...] [--allow <path>]", file=sys.stderr)
        return 2

    violations: list[str] = []
    ok = 0
    for status, path in changed():
        if path in allowed:
            # A declared exception. Named on the command line and recorded in the commit
            # message, so it reads as a decision rather than a gap in the map.
            print(f"  allowed     {path}  (explicit exception)")
            ok += 1
            continue
        who = owner(path)
        if who is None:
            violations.append(f"  UNASSIGNED  {path}\n              no owner in OWNERSHIP.md")
        elif who == "msgs":
            if status == "M":
                violations.append(
                    f"  EDITED MSG  {path}\n              messages are write-once; "
                    f"post a new one instead")
            else:
                ok += 1
        elif who not in dispatched and who != "parent":
            violations.append(
                f"  WRONG HAND  {path}\n              owned by {who}, "
                f"not dispatched this round ({', '.join(sorted(dispatched)) or 'none'})")
        else:
            ok += 1

    if violations:
        print(f"OWNERSHIP FAILED - {len(violations)} violation(s), {ok} clean\n")
        print("\n".join(violations))
        print("\nRevert the flagged paths, or correct OWNERSHIP.md if the map is wrong.")
        return 1

    print(f"ownership clean - {ok} changed path(s), all written by their owner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
