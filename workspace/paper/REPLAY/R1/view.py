#!/usr/bin/env python3
"""Compact view of R1's visible tape. Reads ONLY visible.jsonl - never the source series.

Exists to cut the context cost of each decision point, which is what limits how many
bars the replay can honestly cover (see NOTES.md, burst 3).
"""
import json, sys, os
from collections import OrderedDict

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visible.jsonl")
rows = [json.loads(l) for l in open(P)]
detail = int(sys.argv[1]) if len(sys.argv) > 1 else 12
sessions = int(sys.argv[2]) if len(sys.argv) > 2 else 8

# ATR(14) true range on the visible tail
def atr(n=14):
    seg = rows[-(n + 1):]
    trs = []
    for prev, cur in zip(seg, seg[1:]):
        trs.append(max(cur["h"] - cur["l"], abs(cur["h"] - prev["c"]), abs(cur["l"] - prev["c"])))
    return sum(trs) / len(trs) if trs else 0.0

# per ET-date OHLC of the visible tape
days = OrderedDict()
for i, r in enumerate(rows):
    k = r["ts"][:10]
    d = days.setdefault(k, {"o": r["o"], "h": r["h"], "l": r["l"], "c": r["c"], "n": 0, "first": i})
    d["h"] = max(d["h"], r["h"]); d["l"] = min(d["l"], r["l"]); d["c"] = r["c"]; d["n"] += 1

print(f"visible {len(rows)} bars  |  {rows[0]['ts']} -> {rows[-1]['ts']}  |  ATR14 {atr():.2f}  (0.5 floor {atr()/2:.2f})")
print(f"\nlast {sessions} ET dates:")
for k, d in list(days.items())[-sessions:]:
    print(f"  {k}  o {d['o']:<9} h {d['h']:<9} l {d['l']:<9} c {d['c']:<9} bars {d['n']}")

lo = min(r["l"] for r in rows[-sessions * 22:])
hi = max(r["h"] for r in rows[-sessions * 22:])
print(f"\nrange over that window: {lo} - {hi}  ({hi - lo:.2f} pts), last close {rows[-1]['c']}")

print(f"\nlast {detail} bars:")
for i, r in enumerate(rows[-detail:], start=len(rows) - detail):
    print(f"  [{i}] {r['ts']}  o {r['o']:<9} h {r['h']:<9} l {r['l']:<9} c {r['c']:<9} v {int(r['v'])}")
