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
import pathlib
import subprocess  # noqa: F401  (used for per-file diffs)
import sys

ROOT = "workspace/roundtable/"

# Most specific pattern wins, so order matters: the first match is the owner.
# The programme-wide register. The manager ALLOCATES every D<n>; the parent WRITES the
# entries. That split is deliberate and is the only place in this tree where allocation
# and authorship differ - see OWNERSHIP.md.
PROGRAMME_FILES = (
    ("workspace/studies/DEFECTS.md", "parent"),
    ("workspace/studies/*.md", "parent"),
    ("workspace/studies/out/*", "parent"),
    ("workspace/chrono/*", "parent"),
)

SHARED_ROLE_DIRS = (
    "workspace/developer/*",
    "workspace/manager/*",
    "workspace/strategy_research/*",
)

RULES: list[tuple[str, str]] = [
    ("tests/test_bt1_*.py", "BT1"),
    ("tests/test_bt2_*.py", "BT2"),
    ("tests/test_bt3_*.py", "BT3"),
    ("tests/test_ef1_*.py", "EF1"),
    ("tests/test_ef2_*.py", "EF2"),
    ("tests/test_ef3_*.py", "EF3"),
    ("tests/test_ef4_*.py", "EF4"),
    ("tests/test_ef5_*.py", "EF5"),
    ("tests/test_ef6_*.py", "EF6"),
    ("tests/test_ef7_*.py", "EF7"),
    ("tests/test_bt4_*.py", "BT4"),
    ("tests/test_bt5_*.py", "BT5"),
    ("tests/test_bt6_*.py", "BT6"),
    (ROOT + "discovery/AVENUES.md", "discovery"),
    (ROOT + "discovery/MAIN_TASKS.md", "discovery"),
    (ROOT + "discovery/bursts/*", "discovery"),
    (ROOT + "discovery2/*", "DISC2"),
    (ROOT + "manager/*", "manager"),
    (ROOT + "DIVISION.md", "manager"),
    (ROOT + "OPEN_QUESTIONS.md", "manager"),
    (ROOT + "research/R1*", "R1"),
    (ROOT + "research/R2*", "R2"),
    (ROOT + "research/R3*", "R3"),
    (ROOT + "research/R4*", "R4"),
    (ROOT + "research/R5*", "R5"),
    (ROOT + "research/R6*", "R6"),
    (ROOT + "backtest/BT1/*", "BT1"),
    (ROOT + "backtest/BT2/*", "BT2"),
    (ROOT + "backtest/BT3/*", "BT3"),
    (ROOT + "edge/EF1/*", "EF1"),
    (ROOT + "edge/EF2/*", "EF2"),
    (ROOT + "edge/EF3/*", "EF3"),
    (ROOT + "edge/EF4/*", "EF4"),
    (ROOT + "edge/EF5/*", "EF5"),
    (ROOT + "edge/EF6/*", "EF6"),
    (ROOT + "edge/EF7/*", "EF7"),
    (ROOT + "edge/EDGE_BRIEF.md", "parent"),
    (ROOT + "edge/RESULTS.md", "parent"),
    (ROOT + "backtest/BT4/*", "BT4"),
    (ROOT + "backtest/BT5/*", "BT5"),
    (ROOT + "backtest/BT6/*", "BT6"),
    (ROOT + "BRIEF.md", "parent"),
    (ROOT + "THROTTLE.md", "parent"),
    (ROOT + "LEDGER.md", "parent"),
    (ROOT + "OWNERSHIP.md", "parent"),
    (ROOT + "PIPELINE.md", "parent"),
    (ROOT + "PARKED.md", "parent"),
    (ROOT + "check_ownership.py", "parent"),
    (ROOT + "check_refs.py", "parent"),
    (ROOT + "REGISTRY.md", "parent"),
    (ROOT + "lib/*", "parent"),
    # The two paper-trading sessions. Each owns its own journal tree and nothing
    # else writes there - the same one-writer-per-file rule as every other lane.
    ("workspace/paper/CALL/*", "CALL"),
    ("workspace/paper/REPLAY/*", "REPLAY"),
    # The anchored-structures study (ANCH1): pre-registration, shared harness, per-symbol runs.
    ("workspace/anchors/*", "ANCH"),
]


def owner(path: str) -> str | None:
    """The sole writer of ``path``, or None if the tree does not assign one."""
    for pattern, who in RULES:
        if fnmatch.fnmatch(path, pattern):
            return who
    for pat, who in PROGRAMME_FILES:
        if fnmatch.fnmatch(path, pat):
            return who
    for pat in SHARED_ROLE_DIRS:
        if fnmatch.fnmatch(path, pat):
            return "shared-role"
    if fnmatch.fnmatch(path, ROOT + "discovery/claims/*"):
        return "msgs"          # write-once, same rule as a message
    if fnmatch.fnmatch(path, ROOT + "lib/*"):
        return "parent"
    if fnmatch.fnmatch(path, ROOT + "msgs/*"):
        # Write-once: the creator owns it. A *modified* message is always a violation,
        # whoever did it, because nobody may edit a message after it is posted.
        return "msgs"
    return None


def changed() -> list[tuple[str, str]]:
    out = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--",
         "workspace", "tests"],
        capture_output=True, text=True, check=True,
    ).stdout
    rows = []
    for line in out.splitlines():
        if not line.strip():
            continue
        rows.append((line[:2].strip(), line[3:].strip()))
    return rows


def duplicate_module_basenames() -> list[str]:
    """Agent code dirs that share a module basename.

    The per-agent `tests/test_<agent>_*.py` rule stops two agents owning one TEST file.
    Nothing stopped two agents owning `code/window.py` - and BT5 hit exactly that: both
    edge-finders insert their own `code/` at sys.path[0], first insertion wins,
    sys.modules caches it, and pytest then aborts the whole collection.

    The loud failure is the lucky one. If two agents each ship `session_window.py`,
    both test files import ONE engine and pass, and the independent-implementation
    argument this whole roundtable rests on is silently void. So this is checked by
    basename across every agent code directory, not by whether the suite happens to run.
    """
    import collections
    seen: dict[str, list[str]] = collections.defaultdict(list)
    for d in pathlib.Path(ROOT).glob("*/*/code/*.py"):
        if "__pycache__" in str(d):
            continue
        seen[d.name].append(str(d))
    out = []
    for name, paths in sorted(seen.items()):
        if len(paths) > 1:
            out.append(f"  SHARED NAME {name}\n              " + "\n              ".join(paths))
    return out


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

    dupes = duplicate_module_basenames()
    if dupes:
        print("MODULE-NAME COLLISIONS - two agents' code/ dirs share a basename.")
        print("An import picks whichever sys.path entry came first, so tests that look")
        print("independent may exercise one module. Rename with an agent prefix.\n")
        print("\n".join(dupes) + "\n")
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
        elif who == "shared-role":
            # A standing role directory. Legal, but it is shared by every agent of
            # that type - six live agents are `developer` right now - so it cannot
            # hold anything two of them would both write. Reported, never failed.
            print(f"  shared-role {path}\n              role dir, not a private lane "
                  f"- move anything durable into your own directory")
            ok += 1
        elif who == "msgs":
            if status == "M":
                # What write-once protects is that two readers never disagree about what
                # a message SAID. A pure append, marked as a later correction, does not
                # break that - a reader sees the original and the correction. A REWRITE
                # does, because the earlier text is gone with no trace. So distinguish
                # them by whether the diff removes anything.
                n = subprocess.run(
                    ["git", "diff", "--numstat", "--", path],
                    capture_output=True, text=True, check=False).stdout.split()
                deletions = int(n[1]) if len(n) >= 2 and n[1].isdigit() else -1
                if deletions == 0:
                    print(f"  appended    {path}\n              append-only correction to a "
                          f"posted message - allowed, but prefer a follow-up message")
                    ok += 1
                    continue
                violations.append(
                    f"  REWRITTEN   {path}\n              a posted message was rewritten "
                    f"({deletions} line(s) removed); post a correction instead")
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
