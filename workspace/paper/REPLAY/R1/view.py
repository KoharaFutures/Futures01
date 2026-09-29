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

# --- roll-merge detector -------------------------------------------------
# Added burst 7. Bars 1146-1158 (2024-12-17) were two contract months merged
# into one bar series: 13 consecutive bars each spanning the SAME ~84-point
# envelope, highs clustered in 13.5 pts and lows in 20.75 pts. See NOTES.md
# burst 6. SERIES_AUDIT.md's four checks all pass on such bars, so this is the
# fifth check: envelope constancy. Real volatility MOVES the envelope.
def roll_flags(rows, k=4, band_frac=0.30, blow=3.0, min_range=25.0, jump_frac=0.50):
    """Runs of >=k consecutive bars whose high-band and low-band are both tight
    relative to the mean bar range, while that range is >= blow x the prior
    median AND >= min_range absolute. Returns (start,end,mean_range,hi,lo).

    Thresholds: band_frac 0.30 and min_range 25.0. At band_frac 0.45 this also
    flagged bars 1081-1086 (mean range 13.96, bands 4.5/6.0 = 0.32/0.43 of it) -
    an ordinary balanced consolidation, a FALSE POSITIVE. The real merge sits at
    0.16/0.25 of an 84-point range. NOTE: tuning a detector on a single positive
    example is overfitting, so treat this as a SCREEN THAT MAKES ME LOOK, never
    as a verdict - every flag gets read by eye before it changes a decision.

    SECOND FALSE POSITIVE, burst 8: bars 1446-1449 (mean range 29.31, bands
    8.25/7.0) - an ordinary RTH balance area after a 110-point session, with
    normal continuity. The missing discriminator is that a MERGE must jump
    between its two bands at some boundaries: max |open[i] - close[i-1]| is
    74.5 there, 0.88 of the mean range, against 0.25 (0.009) in both false
    positives. Median is the wrong statistic - half the real merge's
    boundaries are continuous - so this tests the MAX. That is now two
    tuning rounds against one positive example; the overfitting caveat above
    is stronger, not weaker, for having been fixed twice."""
    out, i = [], 25
    med = lambda v: sorted(v)[len(v) // 2]
    while i < len(rows) - k:
        base = med([r["h"] - r["l"] for r in rows[i - 20:i]])
        j = i
        while j < len(rows):
            seg = rows[i:j + 1]
            mr = sum(r["h"] - r["l"] for r in seg) / len(seg)
            hs = max(r["h"] for r in seg) - min(r["h"] for r in seg)
            ls = max(r["l"] for r in seg) - min(r["l"] for r in seg)
            if not (mr >= blow * max(base, 0.25) and mr >= min_range
                    and hs <= band_frac * mr and ls <= band_frac * mr):
                break
            j += 1
        if j - i >= k:
            seg = rows[i:j]
            mr = sum(r["h"] - r["l"] for r in seg) / len(seg)
            # A merge must JUMP between its two bands at some boundary. Tested on
            # the completed run, never inside the growth loop: half of the real
            # merge's boundaries are continuous, so an in-loop test kills the run
            # at its first continuous bar and the detector goes silent entirely.
            gaps = [abs(rows[x]["o"] - rows[x - 1]["c"]) for x in range(i + 1, j)]
            if gaps and max(gaps) >= jump_frac * mr:
                out.append((i, j - 1, round(mr, 2),
                            round(max(r["h"] for r in seg) - min(r["h"] for r in seg), 2),
                            round(max(r["l"] for r in seg) - min(r["l"] for r in seg), 2),
                            round(max(gaps), 2)))
            i = j
        else:
            i += 1
    return out

_f = roll_flags(rows)
print(f"\nroll-merge detector: {len(_f)} suspect run(s) in {len(rows)} visible bars")
for a, b, mr, hs, ls, mg in _f:
    print(f"  !! bars {a}-{b}  {rows[a]['ts'][:16]} -> {rows[b]['ts'][:16]}  "
          f"mean range {mr}  high-band {hs}  low-band {ls}  max-jump {mg}  << DO NOT TRADE")


# --- gap-cluster merge detector (added after the March 2025 roll) ------------
# The envelope test above CAUGHT the March 2025 merge but UNDER-BOUNDED it 5x:
# it flagged 15 bars of a 75-bar merge (2517-2591, 2025-03-18 04:00 -> 03-21 09:00).
# The flaw is structural: envelope constancy assumes the merged instrument is not
# trending. In March the underlying moved ~60 points across the roll window, so the
# high/low bands drift, the run breaks, and only the flattest stretches flag.
#
# The robust signature is the BOUNDARY GAP, because it is a DIFFERENCE and so is
# immune to drift. Across the March merge |open[i] - close[i-1]| recurs at 52.00,
# 52.25, 50.75, 51.50, 51.50, 50.00, 51.00, 50.25, 50.00, 49.50, 50.00, 49.50,
# 50.25 - the Mar->Jun calendar spread, printing over and over. December's did the
# same at ~74.5. A real market does not gap the same distance a dozen times.
def gap_clusters(rows, min_gap=20.0, tol=0.15, min_hits=4, max_span=200,
                 min_density=0.15):
    """Runs where |open[i]-close[i-1]| repeatedly lands near one non-zero value.
    Returns (start, end, n_hits, median_gap). Immune to trend, unlike the envelope
    test, because it keys on a difference rather than a level.

    FALSE POSITIVE ON THE FIRST VERSION, recorded because this is the third
    detector on this desk to need a false-positive round: at min_gap=8.0 with no
    density requirement it flagged bars 2139-2283 - four 9.5pt gaps spread over 145
    bars, which are ordinary session boundaries. The principled fix is DENSITY: a
    merge gaps at the spread on a large FRACTION of its boundaries (March 20/71 =
    28%, December 5/7 = 71%) while coincidental gaps do not (4/145 = 2.8%). min_gap
    is also raised to 20pt, since an index calendar spread is tens of points and a
    session gap is not - but density is the fix that does not depend on the
    instrument."""
    gaps = [(i, abs(rows[i]["o"] - rows[i - 1]["c"])) for i in range(1, len(rows))]
    big = [(i, g) for i, g in gaps if g >= min_gap]
    out, used = [], set()
    for k, (i, g) in enumerate(big):
        if i in used:
            continue
        hits = [(j, h) for j, h in big[k:] if j - i <= max_span and abs(h - g) <= tol * g]
        if len(hits) >= min_hits:
            a, b = hits[0][0], hits[-1][0]
            if (b - a + 1) <= 0 or len(hits) / (b - a + 1) < min_density:
                continue
            med = sorted(h for _, h in hits)[len(hits) // 2]
            out.append((a, b, len(hits), round(med, 2)))
            used.update(range(a, b + 1))
    return out


_g = gap_clusters(rows)
print(f"\ngap-cluster detector: {len(_g)} run(s) — the drift-immune test")
for a, b, n, med in _g:
    print(f"  !! bars {a}-{b}  {rows[a]['ts'][:16]} -> {rows[b]['ts'][:16]}  "
          f"{n} gaps near {med}pt  << DO NOT TRADE (contract merge)")
