#!/usr/bin/env python3
"""Agent C: INDEPENDENT sweep for contract-roll merges. Reads ONLY visible.jsonl.

NOT view.py's roll_flags() (which tests envelope constancy + a max-jump). This tests
a different, arithmetic property:

  STRADDLED FORBIDDEN CORRIDOR.  If two contract months at a constant calendar
  spread are interleaved into one bar series, then in a window of W bars there is a
  price band that (a) NO open/high/low/close ever touches, and (b) EVERY bar in the
  window straddles - low below it, high above it.  Both at once is impossible for a
  single instrument: a bar whose low is under a band and whose high is over it must
  have traded through the band, so some quote would land inside it.  A large
  directional move or a weekend gap creates an untouched band too, but it is NOT
  straddled - bars sit wholly above or wholly below it.  Condition (b) is the
  discriminator and it needs no tuned fraction.

Reported: corridor width in points, and as a multiple of the prior 20-bar median
true range.  Every window width 3..25 at every start is swept.
"""
import json, os, statistics as st

D = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(D, os.pardir, "visible.jsonl"))]
N = len(rows)

def base(i, n=20):
    seg = [r["h"] - r["l"] for r in rows[max(0, i-n):i]]
    return max(st.median(seg), 0.25) if seg else 0.25

def straddled_corridor(i, W):
    """Widest price band untouched by any OHLC in rows[i:i+W] AND straddled by
    every bar in the window. Returns (width, lo, hi)."""
    seg = rows[i:i+W]
    lo_edge = max(r["l"] for r in seg)     # corridor must sit above every low
    hi_edge = min(r["h"] for r in seg)     # ... and below every high
    if hi_edge <= lo_edge:
        return 0.0, None, None             # bars do not share a common interior
    vals = sorted(v for r in seg for v in (r["o"], r["h"], r["l"], r["c"])
                  if lo_edge <= v <= hi_edge)
    pts = [lo_edge] + vals + [hi_edge]
    g, a, b = 0.0, None, None
    for x, y in zip(pts, pts[1:]):
        if y - x > g:
            g, a, b = y - x, x, y
    return g, a, b

print("STRADDLED-FORBIDDEN-CORRIDOR SWEEP - widths 3..25, all starts\n")
best_at = {}
hits = []
for W in range(3, 26):
    bw = (0.0,)
    for i in range(20, N - W + 1):
        g, a, b = straddled_corridor(i, W)
        s = g / base(i)
        if g > bw[0]:
            bw = (g, s, i, W, a, b)
        if g >= 20.0 and s >= 2.0:
            hits.append((s, g, i, i+W-1, W, a, b))
    best_at[W] = bw

# maximal regions
hits.sort(reverse=True)
regions = []
for s, g, a0, b0, W, lo, hi in hits:
    for R in regions:
        if not (b0 < R["a"] - 1 or a0 > R["b"] + 1):
            R["a"] = min(R["a"], a0); R["b"] = max(R["b"], b0)
            if s > R["s"]: R.update(s=s, g=g, W=W, lo=lo, hi=hi)
            break
    else:
        regions.append(dict(a=a0, b=b0, s=s, g=g, W=W, lo=lo, hi=hi))
regions.sort(key=lambda R: -R["s"])

print(f"window hits (corridor >=20pt AND >=2.0x prior median range): {len(hits)}")
print(f"distinct regions: {len(regions)}\n")
for R in regions:
    a, b = R["a"], R["b"]; seg = rows[a:b+1]
    mr = sum(x["h"]-x["l"] for x in seg)/len(seg)
    hs = max(x["h"] for x in seg)-min(x["h"] for x in seg)
    ls = max(x["l"] for x in seg)-min(x["l"] for x in seg)
    gaps = [abs(rows[x]["o"]-rows[x-1]["c"]) for x in range(a+1, b+1)]
    zv = sum(1 for x in seg if x["v"] == 0)
    print(f"  ** bars {a}-{b}  {rows[a]['ts'][:16]} -> {rows[b]['ts'][:16]}  n={b-a+1}")
    print(f"     corridor {R['g']:.2f}pt untouched+straddled ({R['lo']}..{R['hi']}), "
          f"{R['s']:.2f}x prior median range, widest at W={R['W']}")
    print(f"     mean range {mr:.2f}  high-band {hs:.2f}  low-band {ls:.2f}  "
          f"max|o[i]-c[i-1]| {max(gaps) if gaps else 0:.2f}  zero-vol {zv}")

print("\nWIDEST STRADDLED CORRIDOR FOUND AT EACH WIDTH (whole tape, incl. above):")
for W in range(3, 26):
    g, s, i, w, a, b = best_at[W] if len(best_at[W]) > 1 else (0,0,0,W,0,0)
    print(f"   W={W:2d}  {g:6.2f}pt ({s:5.2f}x)  bars {i}-{i+W-1}  {rows[i]['ts'][:16]}")

print("\nSAME SWEEP WITH THE KNOWN MERGE EXCISED (bars 1140-1165 removed from starts):")
for W in range(3, 26):
    bw = (0.0, 0.0, 0, W, 0, 0)
    for i in range(20, N - W + 1):
        if not (i+W-1 < 1140 or i > 1165):
            continue
        g, a, b = straddled_corridor(i, W)
        if g > bw[0]:
            bw = (g, g/base(i), i, W, a, b)
    print(f"   W={W:2d}  {bw[0]:6.2f}pt ({bw[1]:5.2f}x)  bars {bw[2]}-{bw[2]+W-1}  "
          f"{rows[bw[2]]['ts'][:16]}")

print("\nCALENDAR COVERAGE, MES quarterly rolls (Mar/Jun/Sep/Dec):")
print(f"   tape spans {rows[0]['ts'][:10]} .. {rows[-1]['ts'][:10]}  ({len(rows)} bars)")
for lab, d in [("Dec-2024 expiry / roll week", "2024-12-20"),
               ("Mar-2025 expiry / roll week", "2025-03-21")]:
    print(f"   {lab} ~{d}: {'INSIDE the tape' if rows[0]['ts'][:10] <= d <= rows[-1]['ts'][:10] else 'OUTSIDE the tape - NOT TESTABLE here'}")
