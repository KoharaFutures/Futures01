#!/usr/bin/env python3
"""LTA CONCEPT CALLOUTS — fetch fresh bars into this lane's own cache, never into data/archive.

The shared DATA_HUB/tools/refresh_archive.py overwrites committed bars whenever Yahoo re-serves
a timestamp with different values (LVNFIB/archive_guard.py documents 1,321 MGC 60m bars rewritten
in one fetch). This desk therefore leaves data/archive/ alone and keeps fresh bars in
workspace/paper/LTA/live/<SYM>_<TF>m.jsonl (git-ignored). lta_levels.load() reads the archive
and appends only cache bars NEWER than the archive's newest bar.

    python3 workspace/paper/LTA/fetch.py                       # MNQ MES MGC MCL, 5/15/30/60m
    python3 workspace/paper/LTA/fetch.py --symbols MGC --frames 5 60

Prints one line per series with its newest bar. The bar still forming is dropped.
"""
from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
LIVE = HERE / "live"
ET = ZoneInfo("America/New_York")
PERIOD = {5: "5d", 15: "5d", 30: "10d", 60: "1mo"}


def _rows(d, tf, now):
    rows = []
    for ix, r in d.iterrows():
        ts = ix.to_pydatetime().astimezone(ET)
        if ts + timedelta(minutes=tf) > now:          # still forming
            continue
        try:
            v = float(r.get("Volume", 0) or 0)
            o, h, l, c = (float(r[k]) for k in ("Open", "High", "Low", "Close"))
        except (TypeError, ValueError):
            continue
        if c != c or (v == 0 and h == l):             # NaN or vendor stub
            continue
        rows.append({"ts": ts.isoformat(), "o": o, "h": h, "l": l, "c": c, "v": v})
    return rows


def fetch_frame(syms, tf) -> list[str]:
    """One vendor call per timeframe for all symbols (fewer calls = fewer HTTP 429s)."""
    import yfinance as yf
    tick = [f"{s}=F" for s in syms]
    d = yf.download(tick, period=PERIOD[tf], interval=f"{tf}m", progress=False,
                    auto_adjust=False, prepost=True, group_by="ticker", threads=False)
    now = datetime.now(ET)
    LIVE.mkdir(exist_ok=True)
    out = []
    for s, t in zip(syms, tick):
        try:
            sub = d[t] if d is not None and not d.empty else None
        except KeyError:
            sub = None
        rows = _rows(sub.dropna(how="all"), tf, now) if sub is not None else []
        if not rows:
            out.append(f"{s} {tf:>2}m  EMPTY (vendor returned nothing) — cache left as it was")
            continue
        (LIVE / f"{s}_{tf}m.jsonl").write_text("".join(json.dumps(x) + "\n" for x in rows))
        out.append(f"{s} {tf:>2}m  {len(rows):>5} bars, newest {rows[-1]['ts']}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--symbols", nargs="+", default=["MNQ", "MES", "MGC", "MCL"])
    ap.add_argument("--frames", nargs="+", type=int, default=[5, 15, 30, 60])
    a = ap.parse_args()
    ok = True
    for tf in a.frames:
        try:
            for line in fetch_frame(a.symbols, tf):
                ok = ok and "EMPTY" not in line
                print("fetch " + line)
        except Exception as e:
            ok = False
            print(f"fetch {tf}m FAILED: {type(e).__name__}: {e}")
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
