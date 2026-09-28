#!/usr/bin/env python3
"""Agent C: bar-shape / volume substrate audit. Reads ONLY visible.jsonl."""
import json, os
from collections import defaultdict, Counter

D = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(D, os.pardir, "visible.jsonl"))]
N = len(rows)
hr = lambda r: int(r["ts"][11:13])

print(f"bars {N}   {rows[0]['ts']} -> {rows[-1]['ts']}")

# ---- ordering / duplicates / monotonicity -------------------------------
ord_bad = [i for i, r in enumerate(rows)
           if not (r["l"] <= r["o"] <= r["h"] and r["l"] <= r["c"] <= r["h"] and r["l"] <= r["h"])]
ts = [r["ts"] for r in rows]
dups = [t for t, n in Counter(ts).items() if n > 1]
nonmono = [i for i in range(1, N) if ts[i] <= ts[i-1]]
neg_v = [i for i, r in enumerate(rows) if r["v"] < 0]
offgrid = [i for i, r in enumerate(rows)
           if any(abs((r[k]*4) - round(r[k]*4)) > 1e-9 for k in "ohlc")]
print(f"OHLC ordering violations {len(ord_bad)}  dup ts {len(dups)}  non-monotonic ts {len(nonmono)}"
      f"  negative volume {len(neg_v)}  off-tick-grid prices {len(offgrid)}")
if ord_bad: print("  ", ord_bad[:20])
if offgrid: print("   offgrid:", offgrid[:20])

# ---- rangeless / zero volume -------------------------------------------
rangeless = [i for i, r in enumerate(rows) if r["h"] == r["l"]]
zerov = [i for i, r in enumerate(rows) if r["v"] == 0]
print(f"\nrangeless (h==l) {len(rangeless)}  ({100*len(rangeless)/N:.2f}%)")
print(f"zero-volume      {len(zerov)}  ({100*len(zerov)/N:.2f}%)")

by_hr = defaultdict(lambda: [0,0,0,0])   # n, rangeless, zerov, sum_v
for i, r in enumerate(rows):
    b = by_hr[hr(r)]
    b[0] += 1
    b[1] += (r["h"] == r["l"])
    b[2] += (r["v"] == 0)
    b[3] += r["v"]
print("\nET hour |  bars | rangeless |  zero-vol  | mean vol   | RTH?")
for h in sorted(by_hr):
    n, rl, zv, sv = by_hr[h]
    print(f"  {h:02d}:00 | {n:5d} | {rl:4d} {100*rl/n:5.1f}% | {zv:4d} {100*zv/n:5.1f}% | {sv/n:10,.0f} | "
          f"{'RTH' if 9 <= h <= 16 else ''}")

RTH = lambda h: 9 <= h <= 16
rth_z = [i for i in zerov if RTH(hr(rows[i]))]
print(f"\n*** zero-volume bars inside RTH 09:00-16:00 ET: {len(rth_z)} ***")
for i in rth_z:
    r = rows[i]
    print(f"   [{i}] {r['ts']}  o {r['o']} h {r['h']} l {r['l']} c {r['c']}  range {r['h']-r['l']:.2f}")
rth_rl = [i for i in rangeless if RTH(hr(rows[i]))]
print(f"rangeless bars inside RTH: {len(rth_rl)}")
for i in rth_rl[:20]:
    r = rows[i]; print(f"   [{i}] {r['ts']} px {r['c']} v {int(r['v'])}")

# zero-volume with nonzero range = quotes moved but no trades: internally odd
zv_moved = [i for i in zerov if rows[i]["h"] != rows[i]["l"]]
print(f"\nzero-volume bars that nonetheless have a non-zero range: {len(zv_moved)} of {len(zerov)}")
# how big are they
if zv_moved:
    rg = sorted(rows[i]["h"]-rows[i]["l"] for i in zv_moved)
    print(f"   their ranges: min {rg[0]:.2f} med {rg[len(rg)//2]:.2f} max {rg[-1]:.2f}")

# per-ET-date count of bars (cycle length sanity)
dates = defaultdict(int)
for r in rows: dates[r["ts"][:10]] += 1
c = Counter(dates.values())
print(f"\nbars per ET date distribution: {dict(sorted(c.items()))}")
print(f"ET dates covered: {len(dates)}  first {min(dates)}  last {max(dates)}")
missing_16 = [d for d in dates if not any(r["ts"][:10]==d and hr(r)==16 for r in rows)]
print(f"ET dates with no 16:00 bar: {len(missing_16)} -> {sorted(missing_16)[:12]}")
