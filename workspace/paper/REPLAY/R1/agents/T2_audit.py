#!/usr/bin/env python3
"""T2 adversarial audit of NOTES.md bursts 13-24 and SUMMARY.md.

Reads ONLY visible.jsonl and callouts.jsonl (both on T2's reading whitelist).
Reimplements missed.py's counterfactual so the tape can be TRUNCATED to the
cursor each published figure was written at -- visible.jsonl now holds 6950
bars while the published record stops at 6450, so running missed.py as shipped
cannot reproduce any burst before the last.
"""
import json, os, sys, statistics as st

D = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.dirname(D)
ALL = [json.loads(l) for l in open(os.path.join(R1, "visible.jsonl"))]
CALLS = [json.loads(l) for l in open(os.path.join(R1, "callouts.jsonl"))]

TICK, RR, PIVOT_K = 0.25, 2.0, 3
COMM, PV = 2.69, 5.00


def rng(b):
    return b["h"] - b["l"]


def atr(rows, i, n=14):
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3:
        return None
    trs = [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
           for p, c in zip(seg, seg[1:])]
    return sum(trs) / len(trs)


def friction(stop_pts):
    """commission + one tick, expressed in R, for a stop of stop_pts points."""
    return COMM / (PV * stop_pts) + TICK / stop_pts


def hdr(t):
    print("\n" + "=" * 78)
    print(t)
    print("=" * 78)


# ============================================================ 0. tape sanity
hdr("0. TAPE / STATE SANITY")
print(f"visible.jsonl bars             : {len(ALL)}")
print(f"callouts.jsonl rows            : {len(CALLS)}")
print(f"last callout visible_bars      : {CALLS[-1]['visible_bars']}")
print(f"NOTES.md/SUMMARY.md claim cursor 6450, 58 callouts")
print(f"callouts with visible_bars<=6450: {sum(1 for c in CALLS if c['visible_bars']<=6450)}")
print(f"first ts {ALL[0]['ts']}  last ts {ALL[-1]['ts']}")
dupes = {}
for c in CALLS:
    dupes.setdefault(c["visible_bars"], []).append(c["callout_id"])
print("duplicate visible_bars:", {k: v for k, v in dupes.items() if len(v) > 1})

# bar index -> date map for every quoted bar
hdr("0b. QUOTED BAR INDEX -> TAPE (ts, o/h/l/c/v, range)")
for i in (1734, 1735, 1884, 1999, 2000, 2249, 2517, 2519, 2520, 2522, 2524, 2527,
          2550, 2590, 2591, 2599, 2600, 2999, 3000, 3391, 3399, 3400, 3800, 3936,
          3953, 3963, 3964, 3965, 3966, 3967, 4019, 4021, 4041, 4049, 4050, 4248,
          4249, 4250, 4449, 4450, 4599, 4600, 4849, 4850, 5249, 5250, 5395, 5396,
          5397, 5398, 5399, 5449, 5649, 5650, 5879, 5880, 6049, 6050, 6448, 6449):
    if i >= len(ALL):
        continue
    b = ALL[i]
    a = atr(ALL, i)
    print(f"[{i:5d}] {b['ts']}  o {b['o']:>9} h {b['h']:>9} l {b['l']:>9} "
          f"c {b['c']:>9} rng {rng(b):6.2f} v {b['v']:>10.0f}  atr14(i) {a:6.2f}")


# ============================================================ 1. FRICTION
hdr("1. FRICTION FLOOR = commission $2.69 + one tick 0.25, point value $5.00\n"
    "   closed form: friction(R) = (2.69/5 + 0.25)/S = 0.788/S   (S = stop in points)")
print(f"{'claim':<52}{'stop pts':>9}{'comm R':>9}{'tick R':>9}{'total R':>9}  quoted")
CLAIMS = [
    # (label, stop_pts, quoted_comm, quoted_tick, quoted_total)
    ("B13 E5 low-vol quartile 1R=7.73", 7.73, 0.0696, 0.0323, 0.1019),
    ("B13 E5 median 1R=10.43", 10.43, 0.0516, 0.0240, 0.0756),
    ("B13 E5 high-vol quartile 1R=14.30", 14.30, 0.0376, 0.0175, 0.0551),
    ("B16 this regime ATR 21.59 (1.0 ATR)", 21.59, 0.0249, 0.0116, 0.0365),
    ("B16 ATR 21.59 IF 0.5-ATR stop (B18 claim)", 0.5 * 21.59, None, None, 0.0365),
    ("B18 quoted '0.0342R at a 1.0-ATR stop'", 21.59, None, None, 0.0342),
    ("B18 bar3800 0.5 ATR = 4.01 pts", 4.01, 0.134, 0.062, 0.196),
    ("B18 bar3800 1.0 ATR = 8.02 pts", 8.02, 0.067, 0.031, 0.098),
    ("B19 bar4250 ATR 8.93, 0.5-ATR stop", 0.5 * 8.93, None, None, 0.18),
    ("B20 bar4600 0.5 ATR = 2.75 pts", 2.75, 0.196, 0.091, 0.287),
    ("B20 bar4600 1.0 ATR = 5.50 pts", 5.50, 0.098, 0.045, 0.143),
    ("B21 ATR 7.23, 0.5-ATR stop (loud end of claim 0.30)", 0.5 * 7.23, None, None, 0.30),
    ("B21 ATR 23.95, 0.5-ATR stop (quiet end of claim 0.09)", 0.5 * 23.95, None, None, 0.09),
    ("B23 bar5880 1.0-ATR stop", None, None, None, 0.0279),
    ("B23 Q1 mean ATR 7.15 (1.0 ATR)", 7.15, None, None, 0.1102),
    ("B23 Q2 mean ATR 10.62", 10.62, None, None, 0.0742),
    ("B23 Q3 mean ATR 15.21", 15.21, None, None, 0.0518),
    ("B23 Q4 mean ATR 31.28", 31.28, None, None, 0.0252),
    ("B24 1.0-ATR stop = 32 pts", 32.0, None, None, 0.0246),
    ("B24 ATR14 31.98, 1.0-ATR stop", 31.98, None, None, 0.0246),
]
for lbl, S, qc, qt, qtot in CLAIMS:
    if S is None:
        print(f"{lbl:<52}{'-':>9}{'-':>9}{'-':>9}{'-':>9}  quoted {qtot}  "
              f"-> implies ATR {0.788/qtot:.2f}")
        continue
    c, t = COMM / (PV * S), TICK / S
    tot = c + t
    flag = "" if abs(tot - qtot) <= 0.0006 + 0.02 * abs(qtot) * 0 + (0.005 if qtot >= 0.1 else 0.0006) else "   <<< MISMATCH"
    print(f"{lbl:<52}{S:9.3f}{c:9.4f}{t:9.4f}{tot:9.4f}  quoted {qtot}{flag}")
print("\n  exact ratio check: 0.5-ATR friction / 1.0-ATR friction must be 2.000 for any ATR")
for a in (7.15, 21.59, 31.28):
    print(f"    ATR {a:6.2f}: 1.0-ATR {0.788/a:.4f}  0.5-ATR {0.788/(0.5*a):.4f}  ratio {(0.788/(0.5*a))/(0.788/a):.3f}")
print("\n  friction ratio Q1/Q4 (claim '4.4x'):", f"{(0.788/7.15)/(0.788/31.28):.3f}")

# what ATR does each ATR-range endpoint in B20/B21 imply?
hdr("1b. B20/B21 ATR-range endpoints -> friction floor on a 0.5-ATR stop (=1.576/ATR)")
for lbl, lo, hi, claim in (("B20 ATR 5.50 .. 22.61 .. 8.82", 5.50, 22.61, "0.287 quoted at 5.50 only"),
                           ("B21 ATR 7.23 .. 23.95 .. 9.86", 7.23, 23.95, "claimed range 0.09R to 0.30R")):
    print(f"  {lbl}: ATR {lo} -> {1.576/lo:.4f}R ; ATR {hi} -> {1.576/hi:.4f}R   [{claim}]")
print(f"  ATR needed for 0.30R on a 0.5-ATR stop: {1.576/0.30:.2f}")
print(f"  ATR needed for 0.09R on a 0.5-ATR stop: {1.576/0.09:.2f}")
