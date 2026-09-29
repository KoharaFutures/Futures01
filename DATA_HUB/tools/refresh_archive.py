#!/usr/bin/env python3
"""Keep ``data/archive/`` complete: fold in stray fetch fragments, then pull fresh bars.

Two jobs, both append-only through :class:`futures_agents.data.archive.BarArchive`
(which never deletes a bar it already holds):

1. ``--merge-fragments DIR`` folds every ``{SYM}_{MIN}m_fetched_*.jsonl`` file in DIR
   (the CALL desk wrote ~2,900 of these) into the archive. Vendor stubs
   (``volume == 0 and high == low``) are rejected - the CALL desk measured one of
   these 12.20 points wrong on MGC (N5a).
2. ``--fetch`` pulls the newest bars from Yahoo for each symbol/frame and reconciles
   them. Needs ``pip install yfinance``. The newest bar is dropped while forming.

    python3 DATA_HUB/tools/refresh_archive.py --fetch
    python3 DATA_HUB/tools/refresh_archive.py --merge-fragments Archived_Do_Not_Refference/workspace/paper/CALL/data
    python3 DATA_HUB/tools/refresh_archive.py --fetch --symbols MNQ MGC --frames 5 60

Prints one line per series: bars before -> after, added, conflicts, newest bar.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from futures_agents.data.archive import BarArchive  # noqa: E402
from futures_agents.data.bars import Bar, BarSeries  # noqa: E402
from futures_agents.timeutil import to_et  # noqa: E402
from datetime import datetime  # noqa: E402

SYMBOLS = ("MNQ", "MES", "MGC", "MCL")
# (minutes, days of lookback) - inside Yahoo's per-interval caps.
FRAMES = ((1, 7.0), (5, 55.0), (15, 55.0), (30, 55.0), (60, 700.0), (240, 700.0), (1440, 3650.0))
FRAG = re.compile(r"^(?P<sym>[A-Z0-9]+)_(?P<min>\d+)m_fetched_.*\.jsonl$")


def is_stub(d: dict) -> bool:
    return float(d.get("v", 0) or 0) == 0 and float(d["h"]) == float(d["l"])


def merge_fragments(archive: BarArchive, folder: pathlib.Path) -> None:
    groups: dict[tuple[str, int], dict[str, dict]] = defaultdict(dict)
    for p in sorted(folder.glob("*_fetched_*.jsonl")):
        m = FRAG.match(p.name)
        if not m:
            continue
        key = (m["sym"], int(m["min"]))
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            if is_stub(d):
                continue
            prev = groups[key].get(d["ts"])
            # later files win unless they would replace a real-volume bar with a zero-volume one
            if prev is None or float(d.get("v", 0) or 0) > 0 or float(prev.get("v", 0) or 0) == 0:
                groups[key][d["ts"]] = d
    for (sym, mins), rows in sorted(groups.items()):
        bars = [Bar(ts=to_et(datetime.fromisoformat(r["ts"])), open=float(r["o"]), high=float(r["h"]),
                    low=float(r["l"]), close=float(r["c"]), volume=float(r.get("v", 0) or 0),
                    minutes=mins, complete=True) for r in rows.values()]
        bars.sort(key=lambda b: b.ts)
        rep = archive.reconcile(BarSeries(sym, mins, bars), symbol=sym, minutes=mins)
        _report("merge", sym, mins, rep, archive)


def fetch(archive: BarArchive, symbols, frames) -> None:
    from futures_agents.data.yahoo import YahooFeed, YahooError
    feed = YahooFeed()
    for sym in symbols:
        for mins, days in FRAMES:
            if frames and mins not in frames:
                continue
            try:
                res = feed.fetch(sym, minutes=mins, days=days)
            except YahooError as exc:
                print(f"fetch {sym:4s} {mins:>5}m FAILED: {str(exc).splitlines()[0]}")
                continue
            if res.is_empty:
                print(f"fetch {sym:4s} {mins:>5}m EMPTY ({'; '.join(res.warnings)[:120]})")
                continue
            _report("fetch", sym, mins, archive.reconcile_result(res), archive)


def _report(kind, sym, mins, rep, archive) -> None:
    series = archive.load(sym, mins)
    newest = series[-1].ts.isoformat() if len(series) else "-"
    print(f"{kind} {sym:4s} {mins:>5}m had {rep.had:>6} +{rep.added:<5} conflicts {len(rep.conflicts):<4}"
          f" -> {len(series):>6} bars, newest {newest}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--merge-fragments", type=pathlib.Path)
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--symbols", nargs="+", default=list(SYMBOLS))
    ap.add_argument("--frames", nargs="+", type=int, default=[])
    ap.add_argument("--archive", default=str(ROOT / "data" / "archive"))
    a = ap.parse_args()
    archive = BarArchive(a.archive)
    if a.merge_fragments:
        merge_fragments(archive, a.merge_fragments)
    if a.fetch:
        fetch(archive, [s.upper() for s in a.symbols], set(a.frames))
    if not (a.merge_fragments or a.fetch):
        ap.print_help()


if __name__ == "__main__":
    main()
