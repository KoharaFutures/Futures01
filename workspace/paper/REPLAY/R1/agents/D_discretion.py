#!/usr/bin/env python3
"""Does the desk's DISCRETION add anything to the naked pattern?

Agent C mechanised thesis 5 and measured 91 tradeable firings at -0.113R, worse
than a -0.020R placebo. But C's mechanisation has no LEVEL-QUALITY, LIQUIDITY or
TREND-DEPTH filter, and those are precisely what the desk's two real trades
required and what it cited when DECLINING a mechanically-firing signal at bar 1502
("price crossed 5845.0 four times in six bars - a chop midpoint, not broken
support"). So C measures the naked pattern; this measures whether the discretion
layered on top of it is worth anything.

Reads ONLY visible.jsonl. Imports C's signal generator so the base population is
identical and the comparison is within-sample on the same bars.
"""
import json, os, sys
from collections import Counter

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
os.chdir(D)                                    # C_regime resolves paths relative to itself
import importlib.util
spec = importlib.util.spec_from_file_location("creg", os.path.join(D, "C_regime.py"))
creg = importlib.util.module_from_spec(spec)
_stdout = sys.stdout
sys.stdout = open(os.devnull, "w")             # C prints its own report; suppress it
spec.loader.exec_module(creg)
sys.stdout = _stdout

rows, ATR = creg.rows, creg.ATR
sigs = [s for s in creg.sigs if not creg.filt(s)]
for s in sigs:
    r = creg.simulate(s["f"], s["side"], s["S"])
    s["r"] = None if r is None else r[0]
sigs = [s for s in sigs if s["r"] is not None]


def crossings(i, L, n=6):
    """How many times price crossed the level in the n bars before the signal.
    The desk's bar-1502 objection: >2 makes it a chop midpoint, not a level."""
    c = 0
    for j in range(max(1, i - n), i + 1):
        if (rows[j - 1]["c"] - L) * (rows[j]["c"] - L) < 0:
            c += 1
    return c


def trend_depth(i):
    """Sessions of directional travel, as 40-bar close change in ATR units."""
    if i < 40 or ATR[i] is None:
        return 0.0
    return (rows[i]["c"] - rows[i - 40]["c"]) / ATR[i]


FILTERS = {
    "clean level (<=2 crossings/6 bars)": lambda s: crossings(s["i"], s["L"]) <= 2,
    "liquid signal bar (v >= 50k)":       lambda s: rows[s["i"]]["v"] >= 50_000,
    "trend >= 1.5 ATR with the trade":    lambda s: (trend_depth(s["i"]) <= -1.5
                                                     if s["side"] == "SHORT"
                                                     else trend_depth(s["i"]) >= 1.5),
}

m = lambda v: sum(v) / len(v) if v else 0.0


def sd(v):
    if len(v) < 2: return 0.0
    mu = m(v)
    return (sum((x - mu) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def z(a, b):
    if len(a) < 2 or len(b) < 2: return 0.0
    se = (sd(a) ** 2 / len(a) + sd(b) ** 2 / len(b)) ** 0.5
    return (m(a) - m(b)) / se if se else 0.0


base = [s["r"] for s in sigs]
print(f"BASE (agent C's naked pattern, resolvable)  n={len(base):>3}  mean {m(base):+.3f}R  "
      f"win {sum(1 for x in base if x>0)/len(base):.0%}")
print("\nEACH FILTER ALONE — kept subset vs the signals it REJECTED (within-sample):")
for name, f in FILTERS.items():
    keep = [s["r"] for s in sigs if f(s)]
    drop = [s["r"] for s in sigs if not f(s)]
    print(f"  {name:<36} keep n={len(keep):>3} {m(keep):+.3f}R  "
          f"drop n={len(drop):>3} {m(drop):+.3f}R   z {z(keep, drop):+.2f}")

allf = [s for s in sigs if all(f(s) for f in FILTERS.values())]
allr = [s["r"] for s in allf]
rest = [s["r"] for s in sigs if not all(f(s) for f in FILTERS.values())]
print(f"\nALL THREE together                     keep n={len(allr):>3} "
      f"{m(allr):+.3f}R  drop n={len(rest):>3} {m(rest):+.3f}R   z {z(allr, rest):+.2f}")
if allr:
    print(f"   win rate {sum(1 for x in allr if x>0)/len(allr):.0%}   "
          f"bars per signal {len(rows)/len(allr):.0f}")
    print(f"   the surviving signals: {[s['i'] for s in allf]}")
print(f"\nthe desk's two REAL trades were at signal bars 452 and 1337 - "
      f"{'both' if all(b in [s['i'] for s in allf] for b in (452,1337)) else 'NOT both'} "
      f"survive all three filters.")
print("""
HOW TO READ THIS. A positive z means the discretion separates winners from losers
WITHIN the pattern's own population - the filters are doing work. A z near zero
means the desk's judgement is decoration on a pattern that has no edge, and the two
live wins were luck. n is small either way; this cannot prove the filters work, it
can only fail to find that they do.""")
