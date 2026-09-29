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


# ============================================================ 2. ATR WINDOWS
hdr("2. ATR14 RANGES QUOTED PER BURST (min/max over the burst's own bars, inclusive)")
WINDOWS = [
    ("B16 2600-2999  claim 'ATR14 at 21.59' at bar 3000", 2600, 2999),
    ("B18 3400-4049  claim 'bar 3800 ATR14 hit 8.02, quietest stretch'", 3400, 4049),
    ("B19 4050-4449  claim 'ATR ran 8.93-15.29'", 4050, 4449),
    ("B20 4450-4849  claim 'ATR ran 5.50 -> 22.61 -> 8.82'", 4450, 4849),
    ("B21 4850-5249  claim 'ATR ran 7.23 -> 23.95 -> 9.86'", 4850, 5249),
    ("B22 5250-5649", 5250, 5649),
    ("B23 5650-6049  claim 'ATR reached 27.50 around 2025-10-19'", 5650, 6049),
    ("B24 6050-6449  claim 'ATR14 reached 31.98, highest of the entire tape'", 6050, 6449),
]
for lbl, a, b in WINDOWS:
    vals = [(atr(ALL, i), i) for i in range(a, b + 1)]
    vals = [(v, i) for v, i in vals if v]
    mn, mx = min(vals), max(vals)
    print(f"  {lbl}")
    print(f"     min ATR {mn[0]:6.2f} at bar {mn[1]} ({ALL[mn[1]]['ts'][:16]})   "
          f"max ATR {mx[0]:6.2f} at bar {mx[1]} ({ALL[mx[1]]['ts'][:16]})   "
          f"first {vals[0][0]:.2f} last {vals[-1][0]:.2f}")
    print(f"     friction on 0.5-ATR stop over that ATR span: "
          f"{1.576/mx[0]:.4f}R .. {1.576/mn[0]:.4f}R")
gmax = max((atr(ALL, i), i) for i in range(20, 6450))
print(f"\n  MAX ATR14 over bars 20..6449 (the published tape): {gmax[0]:.2f} at bar {gmax[1]} "
      f"({ALL[gmax[1]]['ts'][:16]})")
print(f"  ATR14 at 2025-10-19 bars: ", end="")
print([f"{i}:{atr(ALL,i):.2f}" for i in range(20, 6450) if ALL[i]['ts'][:10] == '2025-10-19'])
print(f"  ATR14 at 2025-08-01 bars (max): ",
      max((atr(ALL, i), i) for i in range(20, 6450) if ALL[i]['ts'][:10] == '2025-08-01'))
print(f"  ATR14 at 2025-09-02 bars (max): ",
      max((atr(ALL, i), i) for i in range(20, 6450) if ALL[i]['ts'][:10] == '2025-09-02'))
print(f"  bars whose ATR14 == 8.02 near 3800: ",
      [(i, round(atr(ALL, i), 2)) for i in range(3780, 3821)])
print(f"  median ATR14 over first 1635 bars (B16 claim 10.43): "
      f"{st.median([atr(ALL,i) for i in range(20,1635)]):.3f}")
print(f"  ATR quartile cuts over first 1635 bars (B13 E5 7.73 / 10.43 / 14.30): ", end="")
v = sorted(atr(ALL, i) for i in range(20, 1635))
print([f"{st.quantiles(v, n=4)[k]:.2f}" for k in range(3)])


# ============================================================ 3. MERGES
hdr("3. MERGE CLAIMS")


def boundary_gaps(a, b):
    return [(i, ALL[i]["o"] - ALL[i - 1]["c"]) for i in range(a, b + 1)]


print("3a. MARCH 2025 -- claim: bars 2517-2591, 2025-03-18 04:00 -> 03-21 09:00")
print(f"   bar 2517 ts {ALL[2517]['ts']}   bar 2591 ts {ALL[2591]['ts']}   span {2591-2517+1} bars")
print(f"   B15 claims 'March cost 75' bars: 2591-2517+1 = {2591-2517+1}")
print("   claim: ranges 4.5-8.5 immediately BEFORE:")
print("     ", [f"{rng(ALL[i]):.2f}" for i in range(2511, 2517)])
print("   claim: ranges 35/31/25/13 immediately AFTER:")
print("     ", [f"{rng(ALL[i]):.2f}" for i in range(2592, 2598)])
print("   claim: '55-99 points throughout'  -> actual range stats over 2517-2591:")
rr = [rng(ALL[i]) for i in range(2517, 2592)]
print(f"     min {min(rr):.2f} max {max(rr):.2f} mean {st.mean(rr):.2f} median {st.median(rr):.2f} "
      f"n<55 {sum(1 for x in rr if x<55)} n>99 {sum(1 for x in rr if x>99)}")
bg = [(i, g) for i, g in boundary_gaps(2517, 2591) if abs(g) >= 40]
print(f"   claim: 20 boundary gaps near 51pt. Actual |gap|>=40 inside 2517-2591: {len(bg)}")
print("     ", [f"{i}:{g:+.2f}" for i, g in bg])
print("   claim: the ten quoted magnitudes 52.00 52.25 50.75 51.50 51.50 50.00 51.00 50.25 50.00 49.50")
print("     sorted |actual| >=40 :", sorted(round(abs(g), 2) for i, g in bg))
zv = [i for i in range(2517, 2592) if ALL[i]["v"] == 0]
print(f"   claim: zero-volume bars at 09:00,14:00,18:00,20:00 ET. Actual zero-v bars in window: {len(zv)}")
from collections import Counter
print("     hours:", sorted(Counter(ALL[i]['ts'][11:13] for i in zv).items()))
print(f"   claim: 545,226 volume spike at bar 2524 -> actual v {ALL[2524]['v']:.0f} ts {ALL[2524]['ts']}")
print(f"   claim: March spread ~51pt vs December's ~74.5pt")
bgd = [(i, g) for i, g in boundary_gaps(1140, 1165) if abs(g) >= 40]
print("     December window 1140-1165 |gap|>=40:", [f"{i}:{g:+.2f}" for i, g in bgd])
mrr = [rng(ALL[i]) for i in range(1146, 1159)]
print(f"     December bars 1146-1158 ranges: {[f'{x:.2f}' for x in mrr]}")

print("\n3b. JUNE 2025 -- claim: run (3963, 3966, 64.69, 7.0, 4.75, 53.0)")
print(f"   mean range 3963-3966: {st.mean([rng(ALL[i]) for i in range(3963,3967)]):.2f}  (claim 64.69)")
print(f"   ranges: {[f'{rng(ALL[i]):.2f}' for i in range(3963,3967)]}")
print(f"   high band width max(h)-min(h) 3963-3966: "
      f"{max(ALL[i]['h'] for i in range(3963,3967))-min(ALL[i]['h'] for i in range(3963,3967)):.2f} (claim 7.0)")
print(f"   low  band width max(l)-min(l) 3963-3966: "
      f"{max(ALL[i]['l'] for i in range(3963,3967))-min(ALL[i]['l'] for i in range(3963,3967)):.2f} (claim 4.75)")
print(f"   max boundary gap in 3963..3966: "
      f"{max(abs(g) for i,g in boundary_gaps(3963,3966)):.2f} (claim 53.0)")
print("   B18 quoted 'largest boundary gaps in bars 3821-4049':")
top = sorted(boundary_gaps(3821, 4049), key=lambda t: -abs(t[1]))[:8]
for i, g in top:
    print(f"     [{i}] {ALL[i]['ts']}  {g:+.2f}")
print("   B18 quoted values: 3965 +53.00 / 3953 -28.00 / 4041 +10.75 / 3936 -7.25 / 4019 +7.00 / 4021 +7.50")
for i in (3965, 3953, 4041, 3936, 4019, 4021):
    g = ALL[i]["o"] - ALL[i - 1]["c"]
    print(f"     [{i}] actual {g:+.2f}")
n10 = [(i, g) for i, g in boundary_gaps(3821, 4049) if abs(g) >= 10]
print(f"   claim 'three gaps >=10pt in 230 bars': actual {len(n10)} -> {[f'{i}:{g:+.2f}' for i,g in n10]}")
print(f"   claim 'March showed 20 gaps near 51.0pt over 70 bars' (see 3a)")

print("\n3c. SEPTEMBER 2025 -- claim: bars 5396-5398, 8.4x local median range 7.50")
for i in range(5395, 5400):
    b = ALL[i]
    print(f"   [{i}] {b['ts']}  o {b['o']} h {b['h']} l {b['l']} c {b['c']} "
          f"range {rng(b):5.2f} v {b['v']:.0f}")
loc = [rng(ALL[i]) for i in range(5396 - 50, 5396)]
print(f"   local median range (50 bars before 5396): {st.median(loc):.2f}   (claim 7.50)")
mr3 = st.mean([rng(ALL[i]) for i in range(5396, 5399)])
print(f"   mean range of the 3 bars: {mr3:.2f}; ratio to median {mr3/st.median(loc):.2f}x  (claim 8.4x)")
print(f"   claim bands 6595-6602 and 6656-6667:")
print(f"     lows  of 5396-5398: {[ALL[i]['l'] for i in range(5396,5399)]}")
print(f"     highs of 5396-5398: {[ALL[i]['h'] for i in range(5396,5399)]}")
print(f"     band separation (min high-band - max low-band): "
      f"{min(ALL[i]['h'] for i in range(5396,5399)) - max(ALL[i]['l'] for i in range(5396,5399)):.2f} (claim 'sixty points above')")
print(f"   claim 'internal gaps are +0.50 and +0.00':")
print(f"     {[format(ALL[i]['o']-ALL[i-1]['c'],'+.2f') for i in (5397,5398)]}")
print(f"   claim 'band geometry 17%/12% of mean range, June 11%/7%':")
hb = max(ALL[i]['h'] for i in range(5396,5399))-min(ALL[i]['h'] for i in range(5396,5399))
lb = max(ALL[i]['l'] for i in range(5396,5399))-min(ALL[i]['l'] for i in range(5396,5399))
print(f"     Sep high-band {hb:.2f} = {hb/mr3:.1%} of mean range {mr3:.2f}; low-band {lb:.2f} = {lb/mr3:.1%}")
mrj = st.mean([rng(ALL[i]) for i in range(3963,3967)])
hbj = max(ALL[i]['h'] for i in range(3963,3967))-min(ALL[i]['h'] for i in range(3963,3967))
lbj = max(ALL[i]['l'] for i in range(3963,3967))-min(ALL[i]['l'] for i in range(3963,3967))
print(f"     Jun high-band {hbj:.2f} = {hbj/mrj:.1%}; low-band {lbj:.2f} = {lbj/mrj:.1%}")
print(f"   claim: 'afterwards the tape sits permanently at the upper level'")
print(f"     min low over 5399..6449: {min(ALL[i]['l'] for i in range(5399,6450)):.2f}")


# ============================================================ 4. COUNTERFACTUAL ENGINE
# Reimplementation of missed.py's simulate/session_end so the tape can be truncated.
def build(nbars):
    rows = ALL[:nbars]
    nxt18 = [None] * len(rows)
    nx = None
    for i in range(len(rows) - 1, -1, -1):
        nxt18[i] = nx
        if rows[i]["ts"][11:13] == "18":
            nx = i

    def session_end_new(f):
        n = nxt18[f]
        if n is None:
            return None
        return n - 1 if n - 1 >= f else None

    def session_end_old(f):
        # pre-burst-25 behaviour: scan forward for first hour == "16"
        for j in range(f, len(rows)):
            if rows[j]["ts"][11:13] == "16":
                return j
        return None

    def _atr(i, n=14):
        seg = rows[max(0, i - n):i + 1]
        if len(seg) < 3:
            return None
        return sum(max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
                   for p, c in zip(seg, seg[1:])) / (len(seg) - 1)

    def sim(f, side, S, send):
        end = send(f)
        if end is None or S is None or S <= 0:
            return None
        sgn = 1 if side == "LONG" else -1
        fill = rows[f]["o"] + sgn * TICK
        stop, targ = fill - sgn * S, fill + sgn * RR * S
        for j in range(f, end + 1):
            b = rows[j]
            if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop):
                return -1.0
            if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ):
                return RR
        return sgn * (rows[end]["c"] - fill) / S

    def ev(f, send):
        a = _atr(f - 1)
        if a is None:
            return None
        L, S_ = sim(f, "LONG", a, send), sim(f, "SHORT", a, send)
        if L is None or S_ is None:
            return None
        return {"bar": f, "atr": a, "long": L, "short": S_, "best": max(L, S_)}

    return rows, session_end_new, session_end_old, _atr, ev


def mean(v):
    return sum(v) / len(v) if v else 0.0


def sdv(v):
    if len(v) < 2:
        return 0.0
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def welch(a, b):
    if len(a) < 2 or len(b) < 2:
        return 0.0
    se = (sdv(a) ** 2 / len(a) + sdv(b) ** 2 / len(b)) ** 0.5
    return (mean(a) - mean(b)) / se if se > 0 else 0.0


def counterfactual(cursor, se="new"):
    rows, sen, seo, _atr, ev = build(cursor)
    send = sen if se == "new" else seo
    stand = [c for c in CALLS if c.get("confidence") == "NO_TRADE" and c["visible_bars"] <= cursor]
    res = []
    for c in stand:
        f = c["visible_bars"]
        if f >= len(rows) or send(f) is None:
            continue
        e = ev(f, send)
        if e:
            res.append(e)
    ctrl = []
    for f in range(20, len(rows)):
        if send(f) is None:
            continue
        e = ev(f, send)
        if e:
            ctrl.append(e)
    picks = {"long": lambda e: e["long"], "short": lambda e: e["short"],
             "flip": lambda e: e["long"] if e["bar"] % 2 == 0 else e["short"],
             "best": lambda e: e["best"]}
    out = {"n": len(res), "n_ctrl": len(ctrl)}
    cbb = {e["bar"]: e for e in ctrl}
    cbars = sorted(cbb)
    for k, p in picks.items():
        s = [p(e) for e in res]
        c = [p(e) for e in ctrl]
        out[k] = {"sample": mean(s), "ctrl": mean(c), "gap": mean(s) - mean(c),
                  "z": welch(s, c)}
        sv, cv = [], []
        for e in res:
            b = e["bar"]
            vals = [p(cbb[x]) for x in cbars if x != b and abs(x - b) <= 120]
            if not vals:
                continue
            sv.append(p(e))
            cv.append(sum(vals) / len(vals))
        d = [x - y for x, y in zip(sv, cv)]
        zp = mean(d) / (sdv(d) / len(d) ** 0.5) if len(d) > 1 and sdv(d) > 0 else 0.0
        out[k]["local_ctrl"] = mean(cv)
        out[k]["paired_gap"] = mean(d)
        out[k]["paired_z"] = zp
    return out


hdr("4. COUNTERFACTUAL REPRODUCTION (missed.py logic, tape truncated to each cursor)\n"
    "   'new' = post-burst-25 session_end (18:00-cycle); 'old' = pre-fix (next 16:00 scan)")
PUB = {
    2000: "B14 n=45: long +0.198 gap? z +0.95 | short +0.071 z +0.66 | flip +0.155 z +0.90",
    3000: "B16 n=47: long +0.263 'ctrl +0.352' z +1.72 | short +0.026 'ctrl -0.016' z -0.08 | flip +0.222 'ctrl +0.253' z +1.23",
    3400: "B17 n=48: long +0.299 'ctrl +0.383' z +1.88 | short +0.004 '-0.024' z -0.13 | flip +0.259 '+0.290' z +1.41",
    4050: "B18 n=49: long s+0.334 c-0.055 gap+0.389 z+1.92 | local c+0.038 gap+0.297 z+1.47 | short s-0.016 c+0.004 gap-0.020 z-0.11 | flip s+0.295 c-0.026 gap+0.321 z+1.57 | best s+1.240 c+0.896 gap+0.345 z+2.05",
    4450: "B19 n=50: long +0.367 gap+0.391 z+1.94 | paired +0.323 z+1.62 | short -0.036 gap-0.007 z-0.04 | paired +0.040 z+0.22 | flip +0.329 gap+0.354 z+1.75 | paired +0.349 z+1.71 | best z+2.18",
    4850: "B20 n=51: long s+0.399 c-0.018 gap+0.417 z+2.09 | paired c+0.049 gap+0.351 z+1.77",
    5250: "B21 n=52: long all-bar z+2.01 | ATR-matched +1.96 | paired +1.65",
    5650: "B22 n=53: long all-bar z+1.92 | paired +1.52 | short -0.002R vs local ctrl",
    6050: "B23 n=54: long all-bar z+1.84 | paired +1.43 | flip +1.69/+1.59 | short -0.021R vs local | best paired +1.41",
    6450: "B24 n=55: long all-bar z+2.06 | paired +1.59 | short -0.033R vs local",
}
for cur in sorted(PUB):
    print(f"\n--- cursor {cur} --- published: {PUB[cur]}")
    for se in ("new", "old"):
        o = counterfactual(cur, se)
        print(f"  [{se}] n={o['n']} n_ctrl={o['n_ctrl']}")
        for k in ("long", "short", "flip", "best"):
            a = o[k]
            print(f"     {k:<6} sample {a['sample']:+.3f}  allbar_ctrl {a['ctrl']:+.3f}  "
                  f"gap {a['gap']:+.3f}  z {a['z']:+.2f}   ||  local_ctrl {a['local_ctrl']:+.3f}  "
                  f"paired_gap {a['paired_gap']:+.3f}  paired_z {a['paired_z']:+.2f}")


# ============================================================ 5. BURST 23 ATR-QUARTILE TABLE
hdr("5. BURST 23 ATR-QUARTILE TABLE, reproduced independently at cursor 6050\n"
    "   published: Q1 atr 7.15 fric .1102 eff .439 L -0.113 S -0.053 flip -0.092 >=1.5R 57.9%\n"
    "              Q2 atr10.62 fric .0742 eff .436 L -0.076 S -0.047 flip -0.043 >=1.5R 52.3%\n"
    "              Q3 atr15.21 fric .0518 eff .448 L +0.045 S -0.044 flip -0.028 >=1.5R 53.1%\n"
    "              Q4 atr31.28 fric .0252 eff .436 L +0.004 S -0.064 flip -0.029 >=1.5R 49.4%")
for CUR in (6050, 6450):
    rows, sen, seo, _atr, ev = build(CUR)
    for se_name, send in (("new", sen), ("old", seo)):
        elig = []
        for f in range(20, len(rows)):
            if send(f) is None:
                continue
            e = ev(f, send)
            if e:
                elig.append(e)
        print(f"\n  cursor {CUR}, session_end={se_name}: eligible bars n={len(elig)}")
        av = sorted(e["atr"] for e in elig)
        q = [av[int(len(av) * k / 4)] for k in (1, 2, 3)]
        print(f"    ATR quartile cuts: {q[0]:.2f} / {q[1]:.2f} / {q[2]:.2f}")
        print(f"    {'bucket':<7}{'n':>6}{'meanATR':>9}{'fric':>9}{'|c-o|/rng':>11}"
              f"{'LONG':>9}{'SHORT':>9}{'flip':>9}{'>=1.5R':>9}{'>=2.0R':>9}"
              f"{'net flip':>10}")
        for k, (lo, hi) in enumerate([(-1e9, q[0]), (q[0], q[1]), (q[1], q[2]), (q[2], 1e9)]):
            bk = [e for e in elig if lo < e["atr"] <= hi] if k else [e for e in elig if e["atr"] <= hi]
            if k == 3:
                bk = [e for e in elig if e["atr"] > lo]
            L = [e["long"] for e in bk]
            S_ = [e["short"] for e in bk]
            F = [e["long"] if e["bar"] % 2 == 0 else e["short"] for e in bk]
            eff = [abs(rows[e["bar"]]["c"] - rows[e["bar"]]["o"]) / rng(rows[e["bar"]])
                   for e in bk if rng(rows[e["bar"]]) > 0]
            ma = mean([e["atr"] for e in bk])
            hit15 = sum(1 for e in bk if max(e["long"], e["short"]) >= 1.5) / len(bk)
            hit20 = sum(1 for e in bk if max(e["long"], e["short"]) >= 2.0) / len(bk)
            fr = 0.788 / ma
            print(f"    Q{k+1:<6}{len(bk):>6}{ma:>9.2f}{fr:>9.4f}{mean(eff):>11.3f}"
                  f"{mean(L):>+9.3f}{mean(S_):>+9.3f}{mean(F):>+9.3f}{hit15:>8.1%}"
                  f"{hit20:>9.1%}{mean(F)-fr:>+10.3f}")

# ============================================================ 6. OTHER TAPE CLAIMS
hdr("6. OTHER QUANTITATIVE CLAIMS AGAINST THE TAPE")

print("6a. B13 resume: bar 1734 '03:00 ET on 23,918, price mid a 5948.0-6163.0 range'")
for w in (100, 150, 200, 250, 300):
    seg = ALL[1735 - w:1735]
    print(f"     last {w:3d} bars to 1734: low {min(b['l'] for b in seg):.2f} high {max(b['h'] for b in seg):.2f}")

print("\n6b. B14: 'chop inside 5935.5-6154.5', 'narrowing 6011.5-6123.25 at the end'")
seg = ALL[1735:2000]
print(f"     bars 1735-1999: low {min(b['l'] for b in seg):.2f} high {max(b['h'] for b in seg):.2f}")
for w in (30, 40, 50, 60):
    s2 = ALL[2000 - w:2000]
    print(f"     last {w} bars to 1999: low {min(b['l'] for b in s2):.2f} high {max(b['h'] for b in s2):.2f}")

print("\n6c. B16: 'a 619.5-point window range (4909.25-5528.75)' over bars 2600-2999")
seg = ALL[2600:3000]
print(f"     low {min(b['l'] for b in seg):.2f} high {max(b['h'] for b in seg):.2f} "
      f"span {max(b['h'] for b in seg)-min(b['l'] for b in seg):.2f}")

print("\n6d. B18: 'the tape rose +218.8 pts over 4050 bars (+0.054/bar)'")
print(f"     close[4049]-close[0] = {ALL[4049]['c']-ALL[0]['c']:+.2f}   per bar {(ALL[4049]['c']-ALL[0]['c'])/4050:+.4f}")
print(f"     close[4049]-open[0]  = {ALL[4049]['c']-ALL[0]['o']:+.2f}")
print("6d2. B20: 'a tape that has now risen from 5800 to 6419'")
print(f"     open[0] {ALL[0]['o']}  close[4849] {ALL[4849]['c']}")

print("\n6e. B18/B20: stand-down composition (ATR 13.18 vs 18.26 all bars, 38.4th pct;")
print("     local drift +0.2935 pts/bar vs +0.1272 tape-wide)")
for CUR in (4050, 4850):
    rows, sen, seo, _atr, ev = build(CUR)
    stand = [c["visible_bars"] for c in CALLS
             if c.get("confidence") == "NO_TRADE" and c["visible_bars"] <= CUR]
    sa = [_atr(f - 1) for f in stand if f < len(rows) and seo(f) is not None and _atr(f - 1)]
    alla = [_atr(i) for i in range(20, len(rows))]
    alla = [x for x in alla if x]
    pct = sum(1 for x in alla if x <= mean(sa)) / len(alla)
    print(f"     cursor {CUR}: n={len(sa)} stand-down mean ATR {mean(sa):.2f}   "
          f"all-bar mean ATR {mean(alla):.2f}   sample-mean percentile {pct:.1%}")
    # local drift: mean close-to-close over the 120 bars ending at the decision bar
    def mu(f, W=120):
        a = max(1, f - W)
        seg = rows[a - 1:f]
        d = [seg[i]["c"] - seg[i - 1]["c"] for i in range(1, len(seg))]
        return mean(d)
    sd_mu = [mu(f - 1) for f in stand if f < len(rows) and seo(f) is not None]
    all_mu = [mu(i) for i in range(140, len(rows))]
    print(f"                 stand-down local drift {mean(sd_mu):+.4f} pts/bar   "
          f"tape-wide {mean(all_mu):+.4f}   ratio {mean(sd_mu)/mean(all_mu):.2f}x")

print("\n6f. FINDING 7 / zero-volume bars by hour")
for CUR in (1685, 6450):
    z = [i for i in range(CUR) if ALL[i]["v"] == 0]
    ch = Counter(ALL[i]["ts"][11:13] for i in z)
    print(f"     bars 0..{CUR-1}: {len(z)} zero-volume bars; by hour {sorted(ch.items())}")
    h18 = [i for i in range(CUR) if ALL[i]["ts"][11:13] == "18"]
    print(f"        18:00 bars {len(h18)}, of which zero-v {sum(1 for i in h18 if ALL[i]['v']==0)}"
          f" ({sum(1 for i in h18 if ALL[i]['v']==0)/len(h18):.1%})")
    import datetime as dt
    wd = Counter(dt.date.fromisoformat(ALL[i]['ts'][:10]).strftime('%a')
                 for i in h18 if ALL[i]['v'] == 0)
    wdall = Counter(dt.date.fromisoformat(ALL[i]['ts'][:10]).strftime('%a') for i in h18)
    print(f"        18:00 zero-v by weekday {dict(wd)}  / all 18:00 by weekday {dict(wdall)}")

print("\n6g. B22 range/volume dissociation: 'range >= 4x local median, volume < 1.5x'")
print("     claim: 13 bars over 5650 -> 1147 1151 1154 1157 | 2519 2520 2522 2527 2550 | 3963 3964 3965 | 5397")
print("     claim: '167 bars have range >=4x median; only these 15 also had flat volume'")


def dissoc(n, W=50, rmult=4.0, vmult=1.5):
    hits, wide = [], 0
    for i in range(W, n):
        seg = ALL[i - W:i]
        mr = st.median([rng(b) for b in seg])
        mv = st.median([b["v"] for b in seg])
        if mr > 0 and rng(ALL[i]) >= rmult * mr:
            wide += 1
            if ALL[i]["v"] < vmult * mv:
                hits.append(i)
    return hits, wide


for W in (30, 50, 100):
    h, w = dissoc(5650, W)
    print(f"     window {W}: wide bars {w}, dissociated {len(h)} -> {h}")

print("\n6h. B23: '2025-10-14 -> 10-17 daily ranges 129, 115, 119, 147 points; ~7 points net across four closes'")
days = {}
for i, r in enumerate(ALL[:6450]):
    d = days.setdefault(r["ts"][:10], {"h": r["h"], "l": r["l"], "c": r["c"], "o": r["o"]})
    d["h"] = max(d["h"], r["h"]); d["l"] = min(d["l"], r["l"]); d["c"] = r["c"]
for k in ("2025-10-13", "2025-10-14", "2025-10-15", "2025-10-16", "2025-10-17", "2025-10-20"):
    if k in days:
        d = days[k]
        print(f"     {k}: range {d['h']-d['l']:7.2f}  close {d['c']:.2f}")
cl = [days[k]["c"] for k in ("2025-10-14", "2025-10-15", "2025-10-16", "2025-10-17") if k in days]
print(f"     net across those four closes: {cl[-1]-cl[0]:+.2f}   (claim ~7 points)")

print("\n6i. B24: 'the tape fell 6900.5 -> 6594.0 across four sessions, -306 points'")
seg = ALL[6050:6450]
mx = max(range(6050, 6450), key=lambda i: ALL[i]["h"])
print(f"     max high in 6050-6449: {ALL[mx]['h']:.2f} at bar {mx} ({ALL[mx]['ts']})")
mn = min(range(6050, 6450), key=lambda i: ALL[i]["l"])
print(f"     min low  in 6050-6449: {ALL[mn]['l']:.2f} at bar {mn} ({ALL[mn]['ts']})")
print(f"     6900.5 - 6594.0 = {6900.5-6594.0:.2f}")
dts = sorted({ALL[i]['ts'][:10] for i in range(mx, mn + 1)})
print(f"     ET dates spanned from the high bar to the low bar: {len(dts)} -> {dts}")

print("\n6j. score-line arithmetic (B14/B16/B18/B23)")
a, b = 1.8949, 1.8540
m = (a + b) / 2
s = abs(a - b) / 2 ** 0.5
print(f"     two trades {a} {b}: mean {m:.4f} (claim +1.8744)  sd {s:.4f} (claim 0.0289)  "
      f"t {m/(s/2**0.5):.3f} (claim +91.660)")
pl, pls = 0.8935, 1.3584
print(f"     real-placebo {m-pl:+.4f} (claim +0.9810)   "
      f"Welch z {(m-pl)/((s**2/2+pls**2/2)**0.5):+.4f} (claim +1.021)")
import math
for n in (12, 20, 21, 105, 297, 310):
    print(f"     free_t({n}) = sqrt(2 ln {n}) = {math.sqrt(2*math.log(n)):.4f}")
print(f"     equity: 50000 + 2 trades. claim $50,688.86 (+1.38%)  "
      f"-> {(50688.86-50000)/50000:.4%}")
