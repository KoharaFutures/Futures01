#!/usr/bin/env python3
"""Key levels, and what ACTUALLY happens when price reaches them.

Reads ONLY visible.jsonl. Walk-forward throughout: the levels active at bar i are
built from confirmed pivots strictly BEFORE i, and a k-bar fractal pivot at bar j
is only treated as known from bar j+k. Nothing here can see the future of the bar
it is deciding at; the OUTCOME measurement deliberately does look forward, because
that is the point, and it only ever looks at bars the cursor has already passed.

WHY IT EXISTS. The account owner asked for the thing chartists do - draw the level,
then draw both branches out of it - and specifically asked that a level which does
NOT hold be accounted for. So this does not draw anything. It detects levels the
way a chartist would (clustered swing pivots), waits for price to reach one, and
then MEASURES which branch happened: bounce, break, or neither.

THE CONTROL IS THE WHOLE POINT. BRIEF.md rule 8 records that FVG and order-block
fill rates here are reproduced by RANDOM zones. So every statistic below is run a
second time against random price lines drawn in the same range, in the same count,
tested by the same procedure. A bounce rate of 60% means nothing until the random
lines' bounce rate is known. If they match, the levels are decoration.
"""
import json, os, random, sys
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(D, "visible.jsonl"))]
N = len(rows)

K = 3                # fractal half-width; a pivot at j is known from j+k
LOOKBACK = 300       # bars of history a level may be built from
TOL_ATR = 0.30       # pivots within this many ATR cluster into one level
BAND_ATR = 0.25      # price is "at" a level inside this band
BREAK_ATR = 0.40     # a close this far beyond the level is a break
BOUNCE_ATR = 0.40    # a close this far back from the level is a bounce
#   SYMMETRY MATTERS AND THE FIRST VERSION GOT IT WRONG. It scored a bounce on a
#   HIGH/LOW touch at 0.75 ATR against a break on a CLOSE at 0.40 ATR - two
#   different bars-worth of evidence at two different distances. That reported an
#   83% bounce rate at detected levels, and random lines scored 77%, which was the
#   clue: the DEFINITION was doing the work, not the levels. Both branches are now
#   judged on a CLOSE at the SAME distance, so "bounce" and "break" are the same
#   strength of claim and the split is not rigged before the data arrives.
HORIZON = 24         # bars to resolve a test (roughly one 22h cycle)
STOP_ATR, RR = 1.0, 2.0
TICK = 0.25


def atr(i, n=14):
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3:
        return None
    return sum(max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
               for p, c in zip(seg, seg[1:])) / (len(seg) - 1)


def levels_at(i, a):
    """Clustered pivot levels known at bar i. Uses bars < i only."""
    lo = max(K, i - LOOKBACK)
    piv = []                                       # (price, bar) so touches can be
    for j in range(lo, i - K):                     # j+K <= i-1  => confirmed
        seg = rows[j - K:j + K + 1]
        if rows[j]["h"] == max(r["h"] for r in seg):
            piv.append((rows[j]["h"], j))
        if rows[j]["l"] == min(r["l"] for r in seg):
            piv.append((rows[j]["l"], j))
    if not piv:
        return []
    piv.sort()
    tol, out, cur = TOL_ATR * a, [], [piv[0]]

    def emit(cl):
        # DISTINCT touches, not pivot count. The first version counted every pivot
        # in the cluster and reported levels with "56 touches", which is not a
        # chart level, it is a tight range swallowing dozens of adjacent swings.
        # A touch only counts if it is separated from the last counted one by more
        # than 2K bars - the same way a chartist counts times price CAME BACK.
        bars = sorted(b for _, b in cl)
        t, last = 1, bars[0]
        for b in bars[1:]:
            if b - last > 2 * K:
                t += 1
                last = b
        return (sum(pp for pp, _ in cl) / len(cl), t)

    for p in piv[1:]:
        if p[0] - cur[-1][0] <= tol:
            cur.append(p)
        else:
            out.append(emit(cur))
            cur = [p]
    out.append(emit(cur))
    return out


def resolve(i, L, side, a):
    """side = +1 price approached from ABOVE (level is support), -1 from below.
    Returns (outcome, bars_to_resolve)."""
    brk = L - side * BREAK_ATR * a
    bnc = L + side * BOUNCE_ATR * a
    for j in range(i, min(i + HORIZON, N)):
        c = rows[j]["c"]
        if (side > 0 and c <= brk) or (side < 0 and c >= brk):
            return "BREAK", j - i
        if (side > 0 and c >= bnc) or (side < 0 and c <= bnc):
            return "BOUNCE", j - i
    return "NEITHER", HORIZON


def sim(f, sgn, a):
    """Trade from bar f's open, sgn +1 long. Engine rules: next-open fill + tick,
    stop wins a same-bar tie, 1 ATR stop, 2R target, resolved inside HORIZON."""
    if f >= N:
        return None
    fill = rows[f]["o"] + sgn * TICK
    S = STOP_ATR * a
    stop, targ = fill - sgn * S, fill + sgn * RR * S
    for j in range(f, min(f + HORIZON, N)):
        b = rows[j]
        if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop):
            return -1.0
        if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ):
            return RR
    return sgn * (rows[min(f + HORIZON, N) - 1]["c"] - fill) / S


def study(random_levels=False, seed=7):
    rng = random.Random(seed)
    ev = []
    active = {}                                     # level -> last bar it was tested
    for i in range(LOOKBACK + K + 20, N - 2):
        a = atr(i - 1)
        if not a:
            continue
        if random_levels:
            seg = rows[max(0, i - LOOKBACK):i]
            lo, hi = min(r["l"] for r in seg), max(r["h"] for r in seg)
            lv = [(rng.uniform(lo, hi), rng.choice([2, 2, 3, 4])) for _ in range(12)]
        else:
            lv = levels_at(i, a)
        band = BAND_ATR * a
        for L, touches in lv:
            if touches < 2:
                continue
            key = round(L / max(band, 0.25))
            prev, cur = rows[i - 1]["c"], rows[i]["c"]
            if abs(cur - L) > band:
                continue
            if abs(prev - L) <= band:                # already in the band: not a new test
                continue
            if i - active.get(key, -99) < HORIZON:   # one test per level per horizon
                continue
            active[key] = i
            side = 1 if prev > L else -1             # +1 support, -1 resistance
            out, nb = resolve(i, L, side, a)
            ev.append({"bar": i, "L": L, "touches": touches, "side": side,
                       "outcome": out, "bars": nb, "atr": a,
                       "bounce_r": sim(i + 1, side, a),          # trade the bounce
                       "break_r": sim(i + 1, -side, a)})         # trade the break
    return ev


def report(ev, label):
    n = len(ev)
    if not n:
        print(f"{label}: no events"); return {}
    c = defaultdict(int)
    for e in ev:
        c[e["outcome"]] += 1
    m = lambda v: sum(v) / len(v) if v else 0.0
    br = [e["bounce_r"] for e in ev if e["bounce_r"] is not None]
    bk = [e["break_r"] for e in ev if e["break_r"] is not None]
    print(f"\n{label}   n={n} tests")
    for k in ("BOUNCE", "BREAK", "NEITHER"):
        print(f"   {k:<8} {c[k]:>5}  {c[k]/n:6.1%}")
    print(f"   trade the BOUNCE (away from the level): mean {m(br):+.3f}R  n={len(br)}")
    print(f"   trade the BREAK  (through the level)  : mean {m(bk):+.3f}R  n={len(bk)}")
    return {"n": n, "bounce": c["BOUNCE"] / n, "break": c["BREAK"] / n,
            "neither": c["NEITHER"] / n, "br": br, "bk": bk}


def sd(v):
    if len(v) < 2: return 0.0
    mu = sum(v) / len(v)
    return (sum((x - mu) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def z(a, b):
    if len(a) < 2 or len(b) < 2: return 0.0
    se = (sd(a) ** 2 / len(a) + sd(b) ** 2 / len(b)) ** 0.5
    return ((sum(a) / len(a)) - (sum(b) / len(b))) / se if se else 0.0


if __name__ == "__main__":
    print(f"R1 key-level study   visible {N} bars   "
          f"K={K} tol={TOL_ATR}ATR band={BAND_ATR}ATR break={BREAK_ATR}ATR "
          f"bounce={BOUNCE_ATR}ATR horizon={HORIZON}")
    real = report(study(False), "DETECTED PIVOT LEVELS")
    ctrl = report(study(True), "RANDOM PRICE LINES (control)")
    if real and ctrl:
        print(f"\nDIFFERENCE, real minus random:")
        print(f"   bounce rate  {real['bounce']-ctrl['bounce']:+.1%}")
        print(f"   break rate   {real['break']-ctrl['break']:+.1%}")
        print(f"   bounce trade {sum(real['br'])/len(real['br']) - sum(ctrl['br'])/len(ctrl['br']):+.3f}R"
              f"   z {z(real['br'], ctrl['br']):+.2f}")
        print(f"   break trade  {sum(real['bk'])/len(real['bk']) - sum(ctrl['bk'])/len(ctrl['bk']):+.3f}R"
              f"   z {z(real['bk'], ctrl['bk']):+.2f}")
        print("""
If the bounce/break split and both trade arms match the random lines, then the
levels carry no information and any scenario tree drawn on them is decoration.
Only a difference that clears its own noise says otherwise.""")
