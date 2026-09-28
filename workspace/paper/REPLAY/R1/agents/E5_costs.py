#!/usr/bin/env python3
"""E5_costs.py - how much of every result on this desk is transaction cost?

AGENT E5, REPLAY desk, closed-market window. READ-ONLY on visible.jsonl.
Does not touch state.json, does not run the harness, advances no cursor.

THE QUESTION
  Agent A found control expectancy running -0.267R at a 0.25-ATR stop up to
  +0.033R at 1.5 ATR, tracking the tick from 9.4% of 1R down to 1.6%. That is a
  cost gradient, and it was never followed up. If the desk's nulls are
  cost-dominated then "no structure" and "structure smaller than the spread"
  are being conflated, and only one of them is a statement about the market.

CONVENTIONS - lifted from missed.py / A_grid.py so numbers stay comparable
  TICK 0.25, POINT_VALUE $5.00, round-turn commission $2.69/contract
  fill at the next bar's open; stop WINS a same-bar tie; flat at the first
  16:00 ET bar at or after the fill; ATR14 from bars <= f-1; eligible bars are
  range(20, len(rows)) whose forward window closes inside the visible tape.
  Fixed geometry for this study: 1.0 ATR stop, 2R target, BOTH directions at
  every eligible bar.

TWO ACCOUNTING MODELS - the crux of this report
  (A) FILL-RELATIVE (what missed.py and A_grid.py do). The bracket is hung off
      the ACTUAL fill: stop = fill -/+ S, target = fill +/- 2S. A stop-out is
      then exactly -1.0R no matter how much you slipped, because the slippage
      moved the stop by the same amount it moved the entry. Slippage can only
      show up indirectly, by shifting which bars get touched.
      I EXPECTED THIS TO HIDE THE COST AND IT DOES NOT. Section 1 measures the
      two models 0.002 R apart over a 0-3 tick sweep: moving the whole bracket
      adverse raises the stop-touch probability by very nearly the amount the
      direct deduction would have cost. So the desk's fill-relative convention
      is NOT the accounting error. The accounting error is that commission was
      never entered at all, and it is 2.15x the slippage.
  (B) SIGNAL-RELATIVE (correct cost accounting). The bracket is hung off the
      price you DECIDED at, P0 = the next bar's open, which is also the risk
      you sized against: stop = P0 -/+ S, target = P0 +/- 2S, and you get
      filled at P0 +/- slip. Now a stop-out costs (S + slip)/S = 1 + slip/S and
      a target pays (2S - slip)/S = 2 - slip/S. Because the brackets no longer
      depend on slip, the touch sequence is IDENTICAL at every slippage level,
      so net_R = gross_R - slip/S exactly, trade for trade. The cost is a clean
      linear deduction and the slope is mean(1/S) per point of slippage.
  Both are reported. (B) is the answer; (A) is the alibi.

AUTOCORRELATION
  Trades opened at consecutive bars inside one session overlap almost
  completely, so the 3226-trade sample holds far fewer than 3226 independent
  draws. Naive SE would overstate the desk's resolution and therefore
  understate the ambiguity. Confidence intervals here come from a bootstrap
  that resamples whole SESSIONS (the 16:00-to-16:00 cycle), keeping every trade
  inside a drawn session together.
"""
import json, math, os, random

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = [json.loads(l) for l in open(os.path.join(D, "visible.jsonl"))]

TICK = 0.25
POINT_VALUE = 5.00
COMMISSION_RT = 2.69          # $ per contract, round turn
COMM_POINTS = COMMISSION_RT / POINT_VALUE   # 0.538 points
STOP_MULT = 1.0
RR = 2.0
SLIP_TICKS = [0.0, 0.5, 1.0, 2.0, 3.0]


# ---- engine mechanics ------------------------------------------------------
def atr(i, n=14):
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3:
        return None
    trs = [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
           for p, c in zip(seg, seg[1:])]
    return sum(trs) / len(trs)


_send = {}
def session_end(f):
    if f in _send:
        return _send[f]
    out = None
    for j in range(f, len(rows)):
        if rows[j]["ts"][11:13] == "16":
            out = j
            break
    _send[f] = out
    return out


def sim_fill_relative(f, sgn, S, slip):
    """(A) bracket hung off the actual fill - missed.py / A_grid.py semantics."""
    end = session_end(f)
    fill = rows[f]["o"] + sgn * slip
    stop, targ = fill - sgn * S, fill + sgn * RR * S
    for j in range(f, end + 1):
        b = rows[j]
        if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop):
            return -1.0, "STOP"
        if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ):
            return RR, "TARGET"
    return sgn * (rows[end]["c"] - fill) / S, "CLOSE"


def sim_signal_relative(f, sgn, S):
    """(B) bracket hung off the decision price P0. Returns GROSS R (slip=0) and
    the outcome label. Net at any slippage is gross - slip/S, exactly, because
    the brackets - and therefore the touch sequence - do not move with slip."""
    end = session_end(f)
    p0 = rows[f]["o"]
    stop, targ = p0 - sgn * S, p0 + sgn * RR * S
    for j in range(f, end + 1):
        b = rows[j]
        if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop):
            return -1.0, "STOP"
        if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ):
            return RR, "TARGET"
    return sgn * (rows[end]["c"] - p0) / S, "CLOSE"


# ---- sample --------------------------------------------------------------
ELIGIBLE = []
for f in range(20, len(rows)):
    if session_end(f) is None:
        continue
    a = atr(f - 1)
    if a is None or a <= 0:
        continue
    ELIGIBLE.append((f, a))

# session id = the index of the 16:00 bar that closes the cycle. Used as the
# bootstrap block so overlapping trades are resampled together.
TRADES = []   # (f, sgn, S, gross_R, why, atr, session_id)
for f, a in ELIGIBLE:
    S = STOP_MULT * a
    for sgn in (1, -1):
        g, why = sim_signal_relative(f, sgn, S)
        TRADES.append((f, sgn, S, g, why, a, session_end(f)))

N = len(TRADES)
ATRS = sorted(a for _, a in ELIGIBLE)


def mean(v):
    return sum(v) / len(v) if v else 0.0
def sd(v):
    if len(v) < 2:
        return 0.0
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
def q(v, p):
    s = sorted(v); k = (len(s) - 1) * p
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


INV_S = [1.0 / t[2] for t in TRADES]
GROSS = [t[3] for t in TRADES]
R_PER_POINT = mean(INV_S)          # R of cost per point of adverse fill
R_PER_TICK = TICK * R_PER_POINT
R_COMM = COMM_POINTS * R_PER_POINT

out = []
def P(s=""):
    out.append(s); print(s)

P("# E5 - cost accounting for the R1 tape")
P()
P(f"bars in visible.jsonl        {len(rows)}")
P(f"eligible decision bars       {len(ELIGIBLE)}")
P(f"TRIALS (both directions)     {N}")
P(f"distinct sessions (blocks)   {len(set(t[6] for t in TRADES))}")
P(f"geometry                     {STOP_MULT} ATR stop, {RR}R target, stop wins tie, flat 16:00 ET")
P()
P("## ATR14 on this tape (the denominator of every R on this desk)")
P(f"  min {ATRS[0]:.2f}  q1 {q(ATRS,.25):.2f}  median {q(ATRS,.50):.2f}  "
  f"q3 {q(ATRS,.75):.2f}  max {ATRS[-1]:.2f}  mean {mean(ATRS):.2f}")
P(f"  1R at median ATR = {q(ATRS,.50):.2f} pts = ${q(ATRS,.50)*POINT_VALUE:,.2f} per contract")
P()

# ---- 1. slippage sweep ----------------------------------------------------
P("## 1. Slippage sweep on entry (fixed geometry, both accounting models)")
P()
P("| entry slip | pts | (A) fill-relative mean R | (B) signal-relative mean R | (B) delta vs 0 |")
P("|---|---|---|---|---|")
res_A, res_B = {}, {}
for st in SLIP_TICKS:
    slip = st * TICK
    a_vals = []
    for f, sgn, S, g, why, a, sid in TRADES:
        r, _ = sim_fill_relative(f, sgn, S, slip)
        a_vals.append(r)
    b_vals = [g - slip / S for f, sgn, S, g, why, a, sid in TRADES]
    res_A[st], res_B[st] = a_vals, b_vals
P_ROWS = []
for st in SLIP_TICKS:
    mb = mean(res_B[st])
    P(f"| {st:g} tick | {st*TICK:.3f} | {mean(res_A[st]):+.4f} | {mb:+.4f} | "
      f"{mb - mean(res_B[0.0]):+.4f} |")
P()
P(f"(A) mean R spread across the whole 0-3 tick sweep: "
  f"{max(mean(res_A[s]) for s in SLIP_TICKS) - min(mean(res_A[s]) for s in SLIP_TICKS):+.4f} R")
P(f"(B) mean R spread across the whole 0-3 tick sweep: "
  f"{max(mean(res_B[s]) for s in SLIP_TICKS) - min(mean(res_B[s]) for s in SLIP_TICKS):+.4f} R")
P()
P(f"COST PER TICK (model B, exact)  = {TICK:.2f} pts x mean(1/S) = "
  f"{TICK:.2f} x {R_PER_POINT:.6f} = {R_PER_TICK:.4f} R per tick")
P(f"  and per point of adverse fill = {R_PER_POINT:.4f} R")
P(f"  at the MEDIAN stop ({q(ATRS,.50):.2f} pts): one tick = {TICK/q(ATRS,.50):.4f} R "
  f"({100*TICK/q(ATRS,.50):.2f}% of 1R)")
P()

# ---- 2. commission --------------------------------------------------------
P("## 2. Commission, which no R on this desk has ever included")
P()
P(f"  ${COMMISSION_RT:.2f} round turn / ${POINT_VALUE:.2f} per point = {COMM_POINTS:.4f} points")
P(f"  {COMM_POINTS:.4f} pts / {TICK} = {COMM_POINTS/TICK:.3f} ticks  <-- commission alone is worth "
  f"{COMM_POINTS/TICK:.2f} ticks, i.e. MORE THAN DOUBLE the single tick the engine models")
P(f"  as R at the median stop ({q(ATRS,.50):.2f} pts): {COMM_POINTS/q(ATRS,.50):.4f} R")
P(f"  as R averaged per trade (mean 1/S):             {R_COMM:.4f} R")
P()
base = mean(res_B[1.0])
P("| accounting | mean R | vs gross |")
P("|---|---|---|")
P(f"| gross, zero cost | {mean(res_B[0.0]):+.4f} | - |")
P(f"| + 1 tick entry slip (desk convention) | {base:+.4f} | {base-mean(res_B[0.0]):+.4f} |")
P(f"| + 1 tick slip + ${COMMISSION_RT} commission | {base-R_COMM:+.4f} | {base-R_COMM-mean(res_B[0.0]):+.4f} |")
P(f"| + 1 tick in + 1 tick out + commission | {mean(res_B[0.0])-2*R_PER_TICK-R_COMM:+.4f} | "
  f"{-2*R_PER_TICK-R_COMM:+.4f} |")
P()
TOTAL_DRAG = R_PER_TICK + R_COMM
P(f"ALL-IN DRAG (1 tick entry + commission) = {TOTAL_DRAG:.4f} R per trade")
P(f"  in dollars at the median stop: 1 tick {TICK*POINT_VALUE:.2f} + commission "
  f"{COMMISSION_RT:.2f} = ${TICK*POINT_VALUE+COMMISSION_RT:.2f} against 1R = "
  f"${q(ATRS,.50)*POINT_VALUE:,.2f}")
P()

# ---- 3. the break-even number --------------------------------------------
P("## 3. The number: gross edge required to clear zero")
P()
P(f"  A strategy on this tape at a 1.0-ATR stop must find "
  f"{TOTAL_DRAG:.3f} R of GROSS edge per trade just to pay costs")
P(f"  (1 tick entry {R_PER_TICK:.4f} R + ${COMMISSION_RT} commission {R_COMM:.4f} R).")
P(f"  Realistic round-turn slippage (a tick in AND a tick out) raises the bar to "
  f"{2*R_PER_TICK + R_COMM:.3f} R.")
P(f"  Measured gross expectancy of the both-directions sample: {mean(res_B[0.0]):+.4f} R.")
P(f"  Shortfall to break even at all-in cost: {TOTAL_DRAG - mean(res_B[0.0]):+.4f} R.")
P()
wr = sum(1 for g in GROSS if g > 0) / N
P(f"  For scale: at the sample's {100*wr:.1f}% gross win rate on a 2R target, "
  f"{TOTAL_DRAG:.3f} R/trade is the same")
P(f"  as needing {100*TOTAL_DRAG/(RR+1):.2f} points of extra win rate at fixed payoff.")
P()

# ---- 4. ATR quartiles ----------------------------------------------------
P("## 4. Cost drag by ATR quartile")
P()
b1, b2, b3 = q(ATRS, .25), q(ATRS, .50), q(ATRS, .75)
def qof(a):
    return 1 if a <= b1 else 2 if a <= b2 else 3 if a <= b3 else 4
QT = {1: [], 2: [], 3: [], 4: []}
for t in TRADES:
    QT[qof(t[5])].append(t)
P("| ATR quartile | n | median ATR | 1 tick as %1R | comm as %1R | all-in drag R | "
  "gross mean R | net mean R (all-in) |")
P("|---|---|---|---|---|---|---|---|")
qsum = {}
for k in (1, 2, 3, 4):
    ts = QT[k]
    invs = mean([1.0 / t[2] for t in ts])
    g = mean([t[3] for t in ts])
    drag = TICK * invs + COMM_POINTS * invs
    med = q([t[5] for t in ts], .5)
    qsum[k] = (len(ts), med, invs, g, drag, g - drag)
    P(f"| Q{k} | {len(ts)} | {med:.2f} | {100*TICK*invs:.2f}% | "
      f"{100*COMM_POINTS*invs:.2f}% | {drag:.4f} | {g:+.4f} | {g-drag:+.4f} |")
P()
P(f"  drag ratio Q1/Q4 = {qsum[1][4]/qsum[4][4]:.2f}x   "
  f"(ATR {qsum[1][1]:.2f} vs {qsum[4][1]:.2f})")
P(f"  GROSS spread across quartiles: {max(qsum[k][3] for k in qsum) - min(qsum[k][3] for k in qsum):.4f} R")
P(f"  NET   spread across quartiles: {max(qsum[k][5] for k in qsum) - min(qsum[k][5] for k in qsum):.4f} R")
P()

# ---- 5. resolution: can the desk tell the two stories apart? -------------
P("## 5. Resolution - session-block bootstrap on GROSS expectancy")
P()
SESS = {}
for t in TRADES:
    SESS.setdefault(t[6], []).append(t[3])
keys = list(SESS)
random.seed(20260928)
B = 4000
boots = []
for _ in range(B):
    acc, n = 0.0, 0
    for _ in range(len(keys)):
        v = SESS[keys[random.randrange(len(keys))]]
        acc += sum(v); n += len(v)
    boots.append(acc / n)
boots.sort()
lo, hi = boots[int(.025 * B)], boots[int(.975 * B)]
naive_se = sd(GROSS) / math.sqrt(N)
block_se = sd(boots)
P(f"  gross mean R                {mean(GROSS):+.4f}")
P(f"  naive SE (n={N}, ignores overlap)   {naive_se:.4f}")
P(f"  session-block bootstrap SE ({len(keys)} blocks)  {block_se:.4f}  "
  f"-> {block_se/naive_se:.2f}x the naive SE")
P(f"  95% block CI on gross mean R   [{lo:+.4f}, {hi:+.4f}]  (half-width {(hi-lo)/2:.4f} R)")
P(f"  all-in cost drag               {TOTAL_DRAG:.4f} R")
P(f"  CI half-width / cost drag      {((hi-lo)/2)/TOTAL_DRAG:.2f}x")
P()
P(f"  Does the CI contain 0?          {'YES' if lo <= 0 <= hi else 'NO'}")
P(f"  Does it contain +{TOTAL_DRAG:.4f} R (the edge needed to break even)?  "
  f"{'YES' if lo <= TOTAL_DRAG <= hi else 'NO'}")
P()
for name, sel in (("LONG only", 1), ("SHORT only", -1)):
    v = [t[3] for t in TRADES if t[1] == sel]
    P(f"  {name}: gross mean R {mean(v):+.4f}, sd {sd(v):.3f}, n {len(v)}")
P()
whys = {}
for t in TRADES:
    whys[t[4]] = whys.get(t[4], 0) + 1
P("  gross outcome mix: " + "  ".join(f"{k} {100*v/N:.1f}%" for k, v in sorted(whys.items())))
P()

# ---- 6. is Agent A's stop-width gradient actually cost? -------------------
P("## 6. Is Agent A's stop-width gradient actually cost? (gross vs net, 2R target)")
P()
P("| stop | median 1R pts | GROSS mean R (zero cost) | 1-tick slip only | "
  "+ commission (all-in) | drag R |")
P("|---|---|---|---|---|---|")
ladder = {}
for sm in [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]:
    g, inv = [], []
    for f, a in ELIGIBLE:
        S = sm * a
        for sgn in (1, -1):
            gr, _ = sim_signal_relative(f, sgn, S)
            g.append(gr); inv.append(1.0 / S)
    mi, mg = mean(inv), mean(g)
    drag = TICK * mi + COMM_POINTS * mi
    ladder[sm] = (mg, drag, mi)
    P(f"| {sm:.2f} ATR | {q([sm*a for _, a in ELIGIBLE], .5):.2f} | {mg:+.4f} | "
      f"{mg-TICK*mi:+.4f} | {mg-drag:+.4f} | {drag:.4f} |")
P()
_lo, _hi = 0.25, 1.5
gg = ladder[_hi][0] - ladder[_lo][0]
sl = (ladder[_hi][0] - TICK*ladder[_hi][2]) - (ladder[_lo][0] - TICK*ladder[_lo][2])
al = (ladder[_hi][0] - ladder[_hi][1]) - (ladder[_lo][0] - ladder[_lo][1])
P(f"  0.25 ATR -> 1.5 ATR change in mean R (A's reported gradient, all-in {al:+.4f} R):")
P(f"    GROSS (zero cost)   {gg:+.4f} R  = {100*gg/al:.1f}%  <- NOT cost: real geometry/noise effect")
P(f"    slippage component  {sl-gg:+.4f} R  = {100*(sl-gg)/al:.1f}%")
P(f"    commission component {al-sl:+.4f} R  = {100*(al-sl)/al:.1f}%")
P("  => A's 'the mechanism is arithmetic, not market structure' is about half right.")
P("     Roughly half the gradient is arithmetic, and MOST of that half is the")
P("     commission A never counted; the other half survives at zero cost.")
P()

# ---- 7. break-even scale -------------------------------------------------
P("## 7. Break-even scale")
P()
gpt = mean(res_B[0.0])
need = (TICK + COMM_POINTS) / gpt
P(f"  all-in cost = {TICK + COMM_POINTS:.4f} points. For the sample's gross point")
P(f"  estimate ({gpt:+.4f} R) to cover it, 1R must be >= {need:.2f} points,")
P(f"  i.e. ATR14 >= {need:.2f} at a 1.0-ATR stop.")
_n = sum(1 for a in ATRS if a >= need)
P(f"  bars on this tape with ATR14 >= {need:.2f}: {_n}/{len(ATRS)} = {100*_n/len(ATRS):.1f}%")
P(f"  (tape ATR q3 = {q(ATRS,.75):.2f}, max {ATRS[-1]:.2f})")
P()
P("## 8. The spec's min_stop_ticks 8 floor (2.00 pts) in cost terms")
P(f"  at a 2.00-pt stop: 1 tick = {100*TICK/2.0:.1f}% of 1R, commission = "
  f"{100*COMM_POINTS/2.0:.1f}% of 1R, all-in = {100*(TICK+COMM_POINTS)/2.0:.1f}% of 1R")
P(f"  0.25 ATR at the Q1 median ATR ({qsum[1][1]:.2f}) = {0.25*qsum[1][1]:.2f} pts "
  f"-> BELOW the 2.00-pt floor, so A's 0.25-ATR cell is partly unsizeable anyway")
P()
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "E5_raw.txt"), "w").write("\n".join(out))
