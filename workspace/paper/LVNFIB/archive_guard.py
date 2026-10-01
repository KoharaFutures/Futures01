#!/usr/bin/env python3
"""Hold data/archive/ to the append-only rule in CLAUDE.md §6.

DATA_HUB/tools/refresh_archive.py (shared, not this desk's to edit) overwrites a bar
whenever Yahoo re-serves that timestamp with different values. On 2026-10-01 a single
--fetch rewrote 1321 MGC 60m bars going back to 2024-11, e.g. the 2024-11-06 11:00
close moving 2674.80 -> 2699.00, and 2024-11-04 01:00 open becoming exactly its high.
That is not a late print settling; it is two-year-old history changing under the desk,
and it moved arm A's measured prior from +0.2379R (t +1.027, payoff 1.58) to
+0.1827R (t +0.811, payoff 1.44) with triggers 164 -> 151.

So: every timestamp already committed keeps its committed values, and only genuinely
new timestamps are allowed through. Run after any fetch, before trusting a number.
Exit 0 always; it reports what it refused.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
ARCH = ROOT / "data" / "archive"


def committed(rel: str) -> dict | None:
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    out = {}
    for line in r.stdout.splitlines():
        line = line.strip()
        if line:
            rec = json.loads(line)
            out[rec["ts"]] = rec
    return out


def working(path: pathlib.Path) -> dict:
    out = {}
    for line in path.open():
        line = line.strip()
        if line:
            rec = json.loads(line)
            out[rec["ts"]] = rec
    return out


def main() -> int:
    refused = appended = touched = 0
    for path in sorted(ARCH.glob("*.jsonl")):
        rel = path.relative_to(ROOT).as_posix()
        base = committed(rel)
        if base is None:                       # not yet tracked: nothing to protect
            continue
        live = working(path)
        bad = [ts for ts in live if ts in base and live[ts] != base[ts]]
        new = [ts for ts in live if ts not in base]
        if not bad:
            appended += len(new)
            continue
        merged = dict(base)                    # committed history wins, verbatim
        for ts in new:
            merged[ts] = live[ts]
        with path.open("w") as fh:
            for ts in sorted(merged):
                fh.write(json.dumps(merged[ts]) + "\n")
        refused += len(bad)
        appended += len(new)
        touched += 1
        print(f"  {path.name:20s} refused {len(bad):5d} rewrite(s), kept {len(new)} new bar(s)")
    print(f"archive_guard: {refused} historical rewrite(s) refused across {touched} file(s), "
          f"{appended} new bar(s) kept")
    return 0


if __name__ == "__main__":
    sys.exit(main())
