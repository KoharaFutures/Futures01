#!/usr/bin/env python3
"""Agent C: regime classification + exhaustive sweep of the desk's one live pattern.
Reads ONLY visible.jsonl (+ callouts.jsonl for the 2 real trades). No harness.

REGIME (stated plainly, no tuning):
  vol  = percentile rank of ATR14(i) within the trailing 250 ATR14 values (i-249..i)
         LO <33, MID 33-67, HI >67
  trend= (c[i] - c[i-40]) / ATR14(i)
         DOWN < -1.5, FLAT -1.5..+1.5, UP > +1.5
  bars with <250 bars of ATR history are labelled WARMUP and excluded from the grid.

PATTERN "failed retest of a broken level" (the desk's thesis 5), mechanised from the
two real callouts' own wording:
  SHORT: a confirmed fractal pivot LOW L (k=3, known only from j+3, lookback 300)
         was BROKEN downward - some bar b in (i-24, i) closed below L-0.25*ATR -
         and bar i RETESTS it from below: h[i] >= L and c[i] < L.
  LONG : mirror on a confirmed pivot HIGH broken upward.
  Entry next bar's open -/+ 1 tick; stop = bar i's opposite extreme +/- 1 tick;
  require stop >= 0.50*ATR14 (desk's floor); target 2.0R; flat at the 16:00 ET bar;
  no entry whose FILL bar is 15:00 or 16:00 ET (desk rule 5).
"""
import json, os, statistics as st
from collections import Counter, defaultdict

D = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(D, os.pardir, "visible.jsonl"))]
N = len(rows)
TICK, RR, K, LOOKBACK, HORIZON = 0.25, 2.0, 3, 300, 24
STOP_FLOOR = 0.50

TR = [0.0] + [max(rows[i]["h"]-rows[i]["l"], abs(rows[i]["h"]-rows[i-1]["c"]),
                  abs(rows[i]["l"]-rows[i-1]["c"])) for i in range(1, N)]
ATR = [None]*N
for i in range(N):
    if i >= 14:
        ATR[i] = sum(TR[i-13:i+1])/14

def pct_rank(i, w=250):
    hist = [ATR[j] for j in range(max(14, i-w+1), i+1) if ATR[j] is not None]
    if len(hist) < w:
        return None
    a = ATR[i]
    return 100.0*sum(1 for x in hist if x < a)/len(hist)

def regime(i):
    if ATR[i] is None or i < 40: return ("WARMUP", "WARMUP")
    p = pct_rank(i)
    if p is None: return ("WARMUP", "WARMUP")
    v = "LO" if p < 33 else ("MID" if p <= 67 else "HI")
    t = (rows[i]["c"] - rows[i-40]["c"]) / ATR[i]
    d = "DOWN" if t < -1.5 else ("UP" if t > 1.5 else "FLAT")
    return (v, d)

# ---------------- 1. regime census --------------------------------------
cells = Counter(); vols = Counter(); trs = Counter()
regs = [regime(i) for i in range(N)]
for r in regs:
    cells[r] += 1; vols[r[0]] += 1; trs[r[1]] += 1
graded = sum(v for k, v in cells.items() if k[0] != "WARMUP")
print(f"bars {N}   WARMUP (no 250-bar ATR history) {cells[('WARMUP','WARMUP')]}   graded {graded}")
print("\nREGIME GRID  (share of the %d graded bars)" % graded)
print("            DOWN         FLAT          UP        | row total")
for v in ("LO","MID","HI"):
    line = f"  {v:4s}"
    tot = 0
    for d in ("DOWN","FLAT","UP"):
        n = cells[(v,d)]; tot += n
        line += f"  {n:4d} {100*n/graded:5.1f}%"
    line += f"  |  {tot:4d} {100*tot/graded:5.1f}%"
    print(line)
line = "  tot "
for d in ("DOWN","FLAT","UP"):
    n = sum(cells[(v,d)] for v in ("LO","MID","HI"))
    line += f"  {n:4d} {100*n/graded:5.1f}%"
print(line)

# calendar distribution
print("\nREGIME OVER CALENDAR TIME (by ET week-start; dominant cell and its share)")
wk = defaultdict(Counter)
import datetime as dt
for i in range(N):
    if regs[i][0] == "WARMUP": continue
    d = dt.date.fromisoformat(rows[i]["ts"][:10])
    wk[(d - dt.timedelta(days=d.weekday())).isoformat()][regs[i]] += 1
for w in sorted(wk):
    c = wk[w]; n = sum(c.values())
    top = c.most_common(3)
    s = "  ".join(f"{a}/{b} {100*k/n:3.0f}%" for (a,b),k in top)
    print(f"  {w}  n={n:3d}  {s}")

# ---------------- 2. pattern sweep --------------------------------------
def pivots_known_at(i):
    """(price, kind) confirmed fractal pivots usable at bar i: pivot at j needs j+K<=i-1."""
    out = []
    for j in range(max(K, i-LOOKBACK), i-K):
        seg = rows[j-K:j+K+1]
        if rows[j]["h"] == max(x["h"] for x in seg) and \
           all(rows[j]["h"] > x["h"] for x in seg if x is not rows[j]):
            out.append((rows[j]["h"], "HIGH", j))
        if rows[j]["l"] == min(x["l"] for x in seg) and \
           all(rows[j]["l"] < x["l"] for x in seg if x is not rows[j]):
            out.append((rows[j]["l"], "LOW", j))
    return out

def session_end(f):
    for j in range(f, N):
        if rows[j]["ts"][11:13] == "16":
            return j
    return None

def simulate(f, side, S):
    end = session_end(f)
    if end is None or S is None or S <= 0: return None
    sgn = 1 if side == "LONG" else -1
    fill = rows[f]["o"] + sgn*TICK
    stop, targ = fill - sgn*S, fill + sgn*RR*S
    for j in range(f, end+1):
        b = rows[j]
        if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop): return -1.0, j, "STOP"
        if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ): return RR, j, "TARGET"
    return sgn*(rows[end]["c"]-fill)/S, end, "SESSION_CLOSE"

sigs = []
for i in range(60, N-1):
    a = ATR[i]
    if a is None or a <= 0: continue
    r = rows[i]
    for L, kind, j in pivots_known_at(i):
        if kind == "LOW":
            # broken downward earlier, retested from below, closed back below
            if not (r["h"] >= L and r["c"] < L): continue
            brk = [b for b in range(max(j+K+1, i-HORIZON), i) if rows[b]["c"] < L - 0.25*a]
            if not brk: continue
            side, stop_px = "SHORT", r["h"] + TICK
        else:
            if not (r["l"] <= L and r["c"] > L): continue
            brk = [b for b in range(max(j+K+1, i-HORIZON), i) if rows[b]["c"] > L + 0.25*a]
            if not brk: continue
            side, stop_px = "LONG", r["l"] - TICK
        f = i+1
        fill = rows[f]["o"] + (TICK if side == "LONG" else -TICK)
        S = abs(stop_px - fill)
        sigs.append(dict(i=i, f=f, L=L, side=side, piv=j, brk=max(brk), S=S, atr=a,
                         hr=int(rows[f]["ts"][11:13]), reg=regs[i]))

# de-duplicate: one signal per (bar, side) keeping the nearest level
byb = {}
for s in sigs:
    k = (s["i"], s["side"])
    if k not in byb or abs(s["L"]-rows[s["i"]]["c"]) < abs(byb[k]["L"]-rows[byb[k]["i"]]["c"]):
        byb[k] = s
sigs = sorted(byb.values(), key=lambda s: s["i"])
print(f"\n\nPATTERN SWEEP: raw signal bars (bar,side unique) = {len(sigs)}")

def filt(s):
    reasons = []
    if s["hr"] in (15, 16): reasons.append("fill in 15:00/16:00 forbidden window")
    if s["S"] < STOP_FLOOR*s["atr"]: reasons.append("stop below 0.5xATR floor")
    if 1146 <= s["i"] <= 1158 or 1146 <= s["f"] <= 1158: reasons.append("inside roll-merge")
    return reasons

tradeable = [s for s in sigs if not filt(s)]
rej = Counter(x for s in sigs for x in filt(s))
print(f"  rejected by the desk's own rules: {len(sigs)-len(tradeable)}   {dict(rej)}")
print(f"  TRADEABLE signals = {len(tradeable)}  over {N} bars = 1 per {N/max(1,len(tradeable)):.1f} bars")
print(f"  by side: {Counter(s['side'] for s in tradeable)}")

for s in tradeable:
    res = simulate(s["f"], s["side"], s["S"])
    s["r"] = None if res is None else res[0]
    s["exit"] = None if res is None else res[2]
res_ok = [s for s in tradeable if s["r"] is not None]
print(f"  resolvable inside the visible tape: {len(res_ok)}")

def stats(ss, label):
    if not ss:
        print(f"  {label:26s} n=  0"); return
    rs = [s["r"] for s in ss]
    w = sum(1 for x in rs if x > 0)
    print(f"  {label:26s} n={len(rs):4d}  mean {st.mean(rs):+6.3f}R  "
          f"median {st.median(rs):+6.3f}R  win {100*w/len(rs):5.1f}%  "
          f"sum {sum(rs):+8.2f}R  targets {sum(1 for s in ss if s['exit']=='TARGET')}")

print("\nOUTCOME, ALL TRADEABLE SIGNALS (engine rules: next open +/-1 tick, stop wins tie, flat 16:00)")
stats(res_ok, "ALL")
stats([s for s in res_ok if s["side"]=="SHORT"], "SHORT only")
stats([s for s in res_ok if s["side"]=="LONG"], "LONG only")

print("\nBY REGIME CELL")
for v in ("LO","MID","HI"):
    for d in ("DOWN","FLAT","UP"):
        stats([s for s in res_ok if s["reg"]==(v,d)], f"{v}/{d}")
stats([s for s in res_ok if s["reg"][0]=="WARMUP"], "WARMUP (ungraded)")

print("\nSHORTS ONLY, BY REGIME CELL (the desk only ever took shorts)")
for v in ("LO","MID","HI"):
    for d in ("DOWN","FLAT","UP"):
        stats([s for s in res_ok if s["reg"]==(v,d) and s["side"]=="SHORT"], f"{v}/{d} SHORT")

print("\nSIGNAL DENSITY PER REGIME CELL (signals per 100 bars in that cell)")
for v in ("LO","MID","HI"):
    for d in ("DOWN","FLAT","UP"):
        nb = cells[(v,d)]
        ns = sum(1 for s in tradeable if s["reg"]==(v,d))
        if nb: print(f"  {v}/{d:5s}  bars {nb:4d}  signals {ns:3d}  = {100*ns/nb:5.2f} per 100 bars")

# ---------------- 3. the two real trades --------------------------------
print("\n\nTHE DESK'S TWO REAL TRADES")
for bi, ent, lvl, note in [(452, 5791.75, 5801.0, "rejection bar 452, entry bar 453"),
                           (1337, 5973.25, 5982.75, "rejection bar 1337, desk entered bar 1340 (late)"),
                           (1339, 5973.25, 5982.75, "the bar the desk actually decided at")]:
    v, d = regs[bi]
    p = pct_rank(bi)
    t = (rows[bi]["c"]-rows[bi-40]["c"])/ATR[bi]
    print(f"  bar {bi}  {rows[bi]['ts'][:16]}  level {lvl}  entry {ent}")
    print(f"     REGIME {v}/{d}   ATR14 {ATR[bi]:.2f} = {p:.1f}th pct of trailing 250   "
          f"40-bar change {rows[bi]['c']-rows[bi-40]['c']:+.2f} = {t:+.2f} ATR   ({note})")
    hit = [s for s in sigs if s["i"] == bi]
    print(f"     my scanner found it: {'YES' if hit else 'NO'}"
          + (f"  level(s) {[s['L'] for s in hit]}  tradeable={[not filt(s) for s in hit]}" if hit else ""))

# ---------------- 4. full signal list -----------------------------------
print(f"\n\nEVERY TRADEABLE SIGNAL ({len(res_ok)} resolvable)")
print("  bar   ts                side  level     stopR   regime      R     exit")
for s in res_ok:
    mark = "  <== DESK TRADE" if s["i"] in (452, 1337) else ""
    print(f"  {s['i']:4d}  {rows[s['i']]['ts'][:16]}  {s['side']:5s} {s['L']:<9} "
          f"{s['S']:5.2f}  {s['reg'][0]:3s}/{s['reg'][1]:4s} {s['r']:+6.2f}  {s['exit']:13s}{mark}")

# ---------------- 5. DESK-FAITHFUL TIER + CONTROL ------------------------
# Tier A above is the loose mechanical shape. The desk's own wording adds three
# preconditions, so Tier B applies them and the comparison is then fair:
#   (a) direction agrees with the 40-bar trend (SHORT only when trend bucket DOWN,
#       LONG only when UP) - both real trades cite "lower highs and lower lows";
#   (b) FIRST retest after a given break episode only (level+break de-duplicated),
#       so one shelf cannot contribute seven signals;
#   (c) the break must be recent - within 12 bars - so the level is still live.
print("\n\n" + "="*72)
print("TIER B - DESK-FAITHFUL: trend-aligned, first-retest-only, break within 12 bars")
print("="*72)
tierB, seen_ep = [], set()
for s in sorted(tradeable, key=lambda s: s["i"]):
    v, d = s["reg"]
    if v == "WARMUP": continue
    if s["side"] == "SHORT" and d != "DOWN": continue
    if s["side"] == "LONG" and d != "UP": continue
    if s["i"] - s["brk"] > 12: continue
    ep = (round(s["L"], 2), s["side"])
    if any(abs(e[0]-ep[0]) < 1e-9 and e[1] == ep[1] and s["i"] - e[2] < 48 for e in seen_ep):
        continue
    seen_ep.add((ep[0], ep[1], s["i"]))
    tierB.append(s)
print(f"  TIER B signals = {len(tierB)}  = 1 per {N/max(1,len(tierB)):.1f} bars of tape")
print(f"  by side: {dict(Counter(s['side'] for s in tierB))}")
stats(tierB, "TIER B ALL")
stats([s for s in tierB if s["side"]=="SHORT"], "TIER B SHORT")
stats([s for s in tierB if s["side"]=="LONG"], "TIER B LONG")
print("  by regime cell:")
for v in ("LO","MID","HI"):
    for d in ("DOWN","FLAT","UP"):
        stats([s for s in tierB if s["reg"]==(v,d)], f"    {v}/{d}")
print("  did Tier B keep the two real trades?",
      {bi: any(s["i"]==bi for s in tierB) for bi in (452, 1337)})
print("\n  TIER B signal list:")
for s in tierB:
    mark = "  <== DESK TRADE" if s["i"] in (452, 1337) else ""
    print(f"    {s['i']:4d}  {rows[s['i']]['ts'][:16]}  {s['side']:5s} L={s['L']:<9} "
          f"stop {s['S']:5.2f}  {s['reg'][0]}/{s['reg'][1]:4s}  {s['r']:+6.2f}  {s['exit']}{mark}")

# ---------------- 6. PLACEBO CONTROL ------------------------------------
# The number that means something is the DIFFERENCE from an arbitrary bar. Same
# side mix, same stop sizes, same engine, random entry bars.
import random
random.seed(20260928)
print("\n" + "="*72)
print("PLACEBO CONTROL - identical engine/stop/side mix at RANDOM entry bars")
print("="*72)
for label, pool in [("Tier A (n=%d)" % len(res_ok), res_ok), ("Tier B (n=%d)" % len(tierB), tierB)]:
    if not pool: continue
    trials = []
    for _ in range(40):
        rs = []
        for s in pool:
            for _try in range(30):
                f = random.randrange(61, N-1)
                if int(rows[f]["ts"][11:13]) in (15, 16): continue
                res = simulate(f, s["side"], s["S"])
                if res: rs.append(res[0]); break
        if rs: trials.append(st.mean(rs))
    real = st.mean([s["r"] for s in pool])
    print(f"  {label:16s} REAL mean {real:+.3f}R   PLACEBO mean {st.mean(trials):+.3f}R "
          f"(sd of trial means {st.pstdev(trials):.3f}, {len(trials)} trials)")
    z = (real - st.mean(trials))/st.pstdev(trials) if st.pstdev(trials) > 0 else 0
    print(f"                   difference {real-st.mean(trials):+.3f}R  =  {z:+.2f} placebo-sd")

# ---------------- 7. the honest counterfactual ---------------------------
print("\n" + "="*72)
print("TIER B WITH THE TWO DESK TRADES REMOVED - what the other firings say")
print("="*72)
rest  = [s for s in tierB if s["i"] not in (452, 1337)]
restS = [s for s in rest if s["side"] == "SHORT"]
stats(rest,  "Tier B minus 2 desk")
stats(restS, "  ...SHORT only")
print(f"  the 2 desk trades are {2}/{len([s for s in tierB if s['side']=='SHORT'])} of all Tier B shorts "
      f"and 2/{sum(1 for s in tierB if s['exit']=='TARGET')} of all Tier B target-hits")
print("\nTIER B DENSITY PER REGIME CELL")
for v in ("LO","MID","HI"):
    for d in ("DOWN","FLAT","UP"):
        nb = cells[(v,d)]; ns = sum(1 for s in tierB if s["reg"]==(v,d))
        if nb: print(f"  {v}/{d:5s} bars {nb:4d}  TierB {ns:3d} = {100*ns/nb:5.2f}/100 bars   "
                     f"TierA {sum(1 for s in tradeable if s['reg']==(v,d)):3d}")
print("\nBOTH DESK TRADES' CELLS, side-matched:")
for cell in [("MID","DOWN"), ("LO","DOWN")]:
    a = [s for s in tradeable if s["reg"]==cell and s["side"]=="SHORT" and s["r"] is not None]
    b = [s for s in tierB if s["reg"]==cell and s["side"]=="SHORT"]
    print(f"  {cell[0]}/{cell[1]} SHORT:  TierA n={len(a)} mean {st.mean([x['r'] for x in a]):+.3f}R "
          f"win {100*sum(1 for x in a if x['r']>0)/len(a):.0f}%   "
          f"| TierB n={len(b)} mean {st.mean([x['r'] for x in b]):+.3f}R "
          f"win {100*sum(1 for x in b if x['r']>0)/len(b):.0f}%")
