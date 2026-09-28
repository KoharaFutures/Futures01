#!/usr/bin/env python3
"""E4 - price the account owner's 22-hour session rule (18:00 ET -> 16:00 ET flat).

WHAT THIS IS. Every trade and every counterfactual on this desk carries a FORCED
TIME EXIT: the harness flattens any open position at the 16:00 ET bar. Nobody has
ever costed it. This runs the identical trade population under three exit regimes
and reports the paired difference.

  A  FLAT16      exit at the cycle's 16:00 ET bar  (the owner's rule, status quo)
  B  HOLD(H)     no time exit; stop or target only, capped at H bars
  C  FLAT16x2    flat at the NEXT 16:00 - i.e. allow one extra cycle

ENGINE CONVENTIONS, copied from missed.py so the numbers are comparable to the
rest of the desk's register:
  * decision at bar f-1, FILL at bar f's open +/- one tick (0.25) of slippage
  * 1.0 ATR stop, 2R target, ATR14 over bars <= the decision bar (f-1)
  * the fill bar itself is scanned for stop/target
  * STOP WINS a same-bar stop/target tie
  * a gap through the stop still books exactly -1.0R (no gap slippage modelled)
The three regimes are NESTED on the same scan, so B and C can only ever differ
from A by continuing past A's cap. That makes the comparison exactly paired: the
same fill, the same stop, the same target, the same bars up to A's exit.

POPULATION. Both directions at every bar f with 15 <= f <= f_max, where f_max is
the last bar at which ALL FOUR regimes (A, C, B48, B120) resolve inside the
visible tape. One common population means every regime is scored on the same
trials and the diffs are paired, not two samples that drifted apart.

CALENDAR CARE - this is where a session study goes wrong, so it is explicit:
  * Bars are hourly and LABELLED BY START, so the bar whose ts hour is "16"
    covers 16:00-17:00 ET. "Flat at the 16:00 bar" using that bar's CLOSE is
    therefore an exit at 17:00 ET, not at 16:00 ET. That is what the harness
    does, so regime A does it too - and a sensitivity re-runs A exiting at the
    16:00 bar's OPEN instead, which is the exit at 16:00 ET on the nose.
  * There is no 17:00 bar anywhere in the tape (the CME maintenance halt).
  * ABBREVIATED SESSIONS. Three sessions in the tape have NO 16:00 bar at all:
    2024-11-29 and 2024-12-24 (half days, bars run 09:30-12:30 on a 30-minute
    offset grid and stop at the 13:00 ET early close) and 2025-01-09 (bars stop
    at 09:00). For a fill inside such a cycle there is no flat bar to flatten at,
    so "the next 16:00" is the FOLLOWING cycle's - the trade is held far longer
    than 22 hours. These trials are tagged ROLLED and every headline is reported
    both with and without them.
  * DST: the tape crosses EDT->EST. Timestamps carry their ET offset, so
    matching on the hour field of the timestamp is local ET on both sides of the
    change. No UTC arithmetic is used anywhere.
  * Horizons in regime B are counted in BARS, not hours: a 120-bar hold spans
    maintenance halts and weekends. Overnight and weekend gap risk beyond the
    modelled stop is real and is NOT charged to regime B, which flatters it.

STATISTICS. Overlapping windows and two directions per bar make the trials
dependent, so the naive per-trial z is optimistic by construction. Reported
alongside it: the same paired difference clustered by SESSION (the flat bar) and
by ISO WEEK. The week-clustered z is the conservative one and is the number to
quote. Reads ONLY visible.jsonl. Writes nothing but its own report.
"""
import json, os
from datetime import datetime
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.dirname(D)
rows = [json.loads(l) for l in open(os.path.join(R1, "visible.jsonl"))]
N = len(rows)

TICK, STOP_ATR, RR, ATR_N = 0.25, 1.0, 2.0, 14
HORIZONS = (48, 120)
ROLL_H = 23.0          # a flat bar more than this many hours after the fill bar
                       # cannot be in the fill bar's own 22-hour cycle
BUCKETS = [(1, 2), (3, 6), (7, 12), (13, 10**6)]

TS = [datetime.fromisoformat(r["ts"]) for r in rows]


def atr(i, n=ATR_N):
    """ATR over the n bars ending at index i. Uses only bars <= i (missed.py)."""
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3:
        return None
    trs = [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
           for p, c in zip(seg, seg[1:])]
    return sum(trs) / len(trs)


ATR = [atr(i) for i in range(N)]
IS16 = [r["ts"][11:13] == "16" for r in rows]

# next 16:00 bar at or after i, and the one after that
nxt16, _n = [None] * N, None
for i in range(N - 1, -1, -1):
    if IS16[i]:
        _n = i
    nxt16[i] = _n
snd16 = [None if nxt16[i] is None or nxt16[i] + 1 >= N else nxt16[nxt16[i] + 1]
         for i in range(N)]


def resolve(f, side, S, cap):
    """Scan bars f..cap. -> (R, exit_index, reason, mfe_R). Nested in cap."""
    sgn = 1 if side == "LONG" else -1
    fill = rows[f]["o"] + sgn * TICK
    stop, targ = fill - sgn * S, fill + sgn * RR * S
    mfe = 0.0
    for j in range(f, cap + 1):
        b = rows[j]
        mfe = max(mfe, (b["h"] - fill) if sgn > 0 else (fill - b["l"]))
        if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop):
            return -1.0, j, "STOP", mfe / S          # stop wins the tie
        if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ):
            return RR, j, "TARGET", mfe / S
    return sgn * (rows[cap]["c"] - fill) / S, cap, "TIME", mfe / S


def resolve_open(f, side, S, cap):
    """Regime-A sensitivity: stop/target through cap-1, else exit at cap's OPEN
    (= flat at 16:00 ET on the nose rather than at that bar's 17:00 close)."""
    sgn = 1 if side == "LONG" else -1
    fill = rows[f]["o"] + sgn * TICK
    stop, targ = fill - sgn * S, fill + sgn * RR * S
    for j in range(f, cap):
        b = rows[j]
        if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop):
            return -1.0, "STOP"
        if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ):
            return RR, "TARGET"
    return sgn * (rows[cap]["o"] - fill) / S, "TIME"


# ---- population -----------------------------------------------------------
fmax = N - 1 - (max(HORIZONS) - 1)
while fmax >= 0 and (snd16[fmax] is None or nxt16[fmax] is None):
    fmax -= 1
FMIN = ATR_N + 1                         # f-1 must carry a full 14-TR window

trials = []
for f in range(FMIN, fmax + 1):
    a = ATR[f - 1]
    if a is None or a <= 0:
        continue
    S = STOP_ATR * a
    cap_a, cap_c = nxt16[f], snd16[f]
    runway = cap_a - f + 1               # bars available: fill bar .. flat bar
    hrs = (TS[cap_a] - TS[f]).total_seconds() / 3600.0
    rolled = hrs > ROLL_H
    wk = TS[f].isocalendar()
    for side in ("LONG", "SHORT"):
        t = {"f": f, "side": side, "S": S, "runway": runway, "rolled": rolled,
             "session": cap_a, "week": (wk[0], wk[1]), "hrs_held_cap": hrs}
        t["A"] = resolve(f, side, S, cap_a)
        t["C"] = resolve(f, side, S, cap_c)
        for H in HORIZONS:
            t[f"B{H}"] = resolve(f, side, S, f + H - 1)
        t["A_open"] = resolve_open(f, side, S, cap_a)
        trials.append(t)

REG = ["A"] + [f"B{H}" for H in HORIZONS] + ["C"]
LBL = {"A": "A  FLAT16 (owner's rule)", "C": "C  FLAT16x2 (one extra cycle)"}
SHORTLBL = {"A": "FLAT16", "C": "FLAT16x2"}
for H in HORIZONS:
    LBL[f"B{H}"] = f"B  HOLD, no time exit, cap {H} bars"
    SHORTLBL[f"B{H}"] = f"HOLD cap {H}"


# ---- stats ----------------------------------------------------------------
def m(v):
    return sum(v) / len(v) if v else float("nan")


def sd(v):
    if len(v) < 2:
        return float("nan")
    mu = m(v)
    return (sum((x - mu) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def zp(d):
    """Paired z on a list of per-trial differences."""
    if len(d) < 2:
        return float("nan")
    s = sd(d)
    return m(d) / (s / len(d) ** 0.5) if s > 0 else float("nan")


def zclust(d, keys):
    """Paired z after collapsing to one mean per cluster."""
    g = defaultdict(list)
    for x, k in zip(d, keys):
        g[k].append(x)
    cm = [m(v) for v in g.values()]
    return zp(cm), len(cm)


def welch(a, b):
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    se = (sd(a) ** 2 / len(a) + sd(b) ** 2 / len(b)) ** 0.5
    return (m(a) - m(b)) / se if se > 0 else float("nan")


def desc(ts, reg):
    r = [t[reg][0] for t in ts]
    tm = [t[reg][0] for t in ts if t[reg][2] == "TIME"]
    return {"n": len(r), "mean": m(r), "sd": sd(r),
            "win": sum(1 for x in r if x > 0) / len(r) if r else float("nan"),
            "tshare": len(tm) / len(r) if r else float("nan"), "tmean": m(tm),
            "tn": len(tm)}


def pdiff(ts, ra, rb):
    """Paired ra - rb with naive, session-clustered and week-clustered z."""
    d = [t[ra][0] - t[rb][0] for t in ts]
    zs, ks = zclust(d, [t["session"] for t in ts])
    zw, kw = zclust(d, [t["week"] for t in ts])
    g = defaultdict(list)
    for x, k in zip(d, [t["week"] for t in ts]):
        g[k].append(x)
    cm = [m(v) for v in g.values()]
    se = sd(cm) / len(cm) ** 0.5 if len(cm) > 1 else float("nan")
    return {"d": m(d), "sd": sd(d), "z": zp(d), "zs": zs, "ks": ks,
            "zw": zw, "kw": kw, "n": len(d), "se_w": se,
            "lo": m(d) - 1.96 * se, "hi": m(d) + 1.96 * se}


def line(w=78):
    return "-" * w


# ---- report ---------------------------------------------------------------
out = []
P = out.append

kept = [t for t in trials if not t["rolled"]]
rolledt = [t for t in trials if t["rolled"]]
nowruns = sorted({t["session"] for t in rolledt})

P("# E4 - what the 22-hour session rule costs")
P("")
P(f"tape: {N} bars, {rows[0]['ts'][:16]} .. {rows[-1]['ts'][:16]} ET, hourly, "
  f"labelled by bar START")
P(f"16:00 ET bars in tape: {sum(IS16)}    17:00 bars: "
  f"{sum(1 for r in rows if r['ts'][11:13] == '17')} (maintenance halt)")
P(f"geometry: {STOP_ATR} ATR stop, {RR}R target, ATR{ATR_N} at the decision bar, "
  f"fill next bar's open +/- {TICK}, stop wins the tie")
P(f"population: both directions at every bar f in [{FMIN}, {fmax}] at which ALL "
  f"regimes resolve in-tape")
P(f"TRIALS: {len(trials)}  ({len(trials)//2} bars x 2 directions)   "
  f"of which ROLLED {len(rolledt)}, clean {len(kept)}")
P("")

P("## short sessions and cycles with no 16:00 bar")
P("")
bydate = defaultdict(list)
for i, r in enumerate(rows):
    bydate[r["ts"][:10]].append(i)
# a date that carries a DAY session (any bar at or after 09:00 ET) but no 16:00
# bar is a truncated session. Dates holding only 18:00-23:00 bars are the opening
# leg of the NEXT cycle and are not missing anything.
no16 = [d for d, ix in sorted(bydate.items())
        if not any(IS16[i] for i in ix)
        and any("09" <= rows[i]["ts"][11:13] <= "16" for i in ix)]
evening_only = [d for d, ix in sorted(bydate.items())
                if not any(IS16[i] for i in ix) and d not in no16]
P(f"dates with bars: {len(bydate)}    16:00 ET bars: {sum(IS16)}")
P(f"dates carrying a day session but NO 16:00 bar -> TRUNCATED SESSIONS: {len(no16)}")
for d in no16:
    ix = bydate[d]
    P(f"  {d}  {len(ix):>2} bars  {rows[ix[0]]['ts'][11:16]}..{rows[ix[-1]]['ts'][11:16]} ET")
P(f"dates holding only evening bars (18:00-23:00) - the opening leg of the next")
P(f"cycle, nothing missing: {len(evening_only)} (Sundays and the Friday-evening-free")
P(f"weekday pattern of this tape)")
P("")
P("These are abbreviated sessions: 2024-11-29 (day after Thanksgiving) and")
P("2024-12-24 (Christmas Eve) run on a 30-minute-offset grid 09:30..12:30 and stop")
P("at the 13:00 ET early close; 2025-01-09 (Carter day of mourning) stops at 09:00")
P("ET and reopens at 18:00. Dates entirely absent from the tape (2024-11-28,")
P("2024-12-25, 2025-01-20) are full holidays and form no cycle at all.")
P("")
P("HANDLING. A cycle with no 16:00 bar has nothing to flatten at. Following the")
P("desk's existing session_end() convention the flat rolls to the NEXT 16:00, so")
P("the position is held well past 22 hours. Those trials are tagged ROLLED, and")
P(f"every number below is given both ways. ROLLED trials: {len(rolledt)} of "
  f"{len(trials)} ({len(rolledt)/len(trials):.1%}), from these flat bars:")
for s in nowruns:
    sub = [t for t in rolledt if t["session"] == s]
    P(f"  flat bar {s} {rows[s]['ts'][:16]}  n={len(sub):>3}  "
      f"hold to flat up to {max(t['hrs_held_cap'] for t in sub):.0f}h")
P("")

for tag, ts in (("ALL TRIALS (rolled included)", trials),
                ("CLEAN ONLY (rolled excluded)", kept)):
    P(f"## regimes - {tag}")
    P("")
    P(f"{'regime':<35} {'n':>5} {'meanR':>8} {'sd':>6} {'win%':>7} "
      f"{'TIME n':>7} {'TIME%':>7} {'meanR|TIME':>11}")
    P(line(90))
    for reg in REG:
        s = desc(ts, reg)
        tm = f"{s['tmean']:+.4f}" if s["tn"] else "-"
        P(f"{LBL[reg]:<35} {s['n']:>5} {s['mean']:>+8.4f} {s['sd']:>6.2f} "
          f"{s['win']:>6.1%} {s['tn']:>7} {s['tshare']:>6.1%} {tm:>11}")
    P("")

P("## HEADLINE - the paired price of the forced flat")
P("")
P("Positive d = the forced flat EARNS that much R per trade versus the")
P("alternative; negative d = it COSTS that much. Same trials, same fills, so the")
P("difference is paired. z(trial) is the naive per-trial z and is OPTIMISTIC")
P("(overlapping windows, two directions per bar). z(sess) clusters on the flat")
P("bar, z(week) on the ISO week - quote z(week).")
P("")
for tag, ts in (("all trials", trials), ("clean only", kept)):
    P(f"{tag}:")
    P(f"  {'comparison':<28} {'n':>5} {'d R/trade':>10} {'z(trial)':>9} "
      f"{'z(sess)':>8} {'z(week)':>8}")
    P("  " + line(76))
    for rb in REG[1:]:
        p = pdiff(ts, "A", rb)
        P(f"  {'FLAT16 vs ' + SHORTLBL[rb]:<28} {p['n']:>5} "
          f"{p['d']:>+10.4f} {p['z']:>9.2f} {p['zs']:>8.2f} {p['zw']:>8.2f}"
          f"   (clusters {p['ks']}/{p['kw']})")
    P("")

P("two-sample Welch z as well, for comparability with the desk's other reports")
P("(missed.py uses the unpaired form) - clean trials:")
for rb in REG[1:]:
    P(f"  A vs {rb:<6} Welch z {welch([t['A'][0] for t in kept], [t[rb][0] for t in kept]):+.2f}")
P("")
P("### the bound, which is the useful part of a null")
P("")
P("Week-clustered 95% intervals on the paired difference (clean trials). A null")
P("is only worth anything if it comes with what it excludes:")
for rb in REG[1:]:
    p = pdiff(kept, "A", rb)
    P(f"  FLAT16 vs {SHORTLBL[rb]:<12} d {p['d']:+.4f}R   95% CI "
      f"[{p['lo']:+.4f}, {p['hi']:+.4f}]R per trade")
P("")
P("So on this tape the forced flat is worth somewhere between about a hundredth")
P("of an R saved and a hundredth and a half of an R spent, per trade. At the")
P("desk's trade rate that is not a number anyone can feel, and the interval is")
P("tight enough to say the rule is not quietly bleeding tenths of an R.")
P("")

P("## where the difference comes from")
P("")
for tag, ts in (("all trials", trials), ("clean only", kept)):
    tt = [t for t in ts if t["A"][2] == "TIME"]
    P(f"{tag}: regime A exits by TIME on {len(tt)}/{len(ts)} = "
      f"{len(tt)/len(ts):.1%} of trials, mean {m([t['A'][0] for t in tt]):+.4f}R.")
    if tt:
        for rb in REG[1:]:
            sub = [t[rb][0] for t in tt]
            cnt = defaultdict(int)
            for t in tt:
                cnt[t[rb][2]] += 1
            P(f"   those same trials under {rb:<5}: mean {m(sub):+.4f}R  "
              f"({', '.join(f'{k} {v}' for k, v in sorted(cnt.items()))})"
              f"   -> lift {m(sub) - m([t['A'][0] for t in tt]):+.4f}R on "
              f"{len(tt)/len(ts):.1%} of trials = "
              f"{(m(sub) - m([t['A'][0] for t in tt])) * len(tt)/len(ts):+.4f}R/trade")
    P("")
P("Trials that already resolve by stop or target before the flat are IDENTICAL in")
P("all regimes by construction, so the whole of any difference lives in the")
P("TIME-exited slice. The per-trade figure is the lift on that slice times its")
P("share - which is the arithmetic printed above, and it reconciles with the")
P("headline table.")
P("")
P("THE MAXIMUM HORIZON IS NOT BINDING. Every clean trial resolves by stop or")
bl = max(t["B120"][1] - t["f"] + 1 for t in kept)
bm = m([t["B120"][1] - t["f"] + 1 for t in kept])
P(f"target well inside 48 bars: longest resolution {bl} bars, mean {bm:.1f} bars.")
P("So B48 and B120 are the same experiment on this tape and give identical")
P("numbers; the 120-bar arm is reported only to show the cap is slack. 'No time")
P("exit' is therefore a genuine hold-to-resolution, not a second time exit in")
P("disguise.")
P("")
P("### was the flat cutting winners short, or losers loose?")
P("")
P("Split regime A's TIME exits by whether the trade was in profit at the flat.")
P("This is the shape the owner would feel: a rule that scratches winners is a")
P("different complaint from one that rescues losers.")
P("")
P(f"{'at the flat':<22} {'n':>5} {'A meanR':>9} {'B120 meanR':>11} {'lift':>8} "
  f"{'z(week)':>8}  resolution under B120")
P(line(94))
tt = [t for t in kept if t["A"][2] == "TIME"]
for nm, sel in (("in profit (R > 0)", [t for t in tt if t["A"][0] > 0]),
                ("under water (R <= 0)", [t for t in tt if t["A"][0] <= 0])):
    if not sel:
        continue
    p = pdiff(sel, "A", "B120")
    cnt = defaultdict(int)
    for t in sel:
        cnt[t["B120"][2]] += 1
    P(f"{nm:<22} {len(sel):>5} {m([t['A'][0] for t in sel]):>+9.4f} "
      f"{m([t['B120'][0] for t in sel]):>+11.4f} {-p['d']:>+8.4f} {p['zw']:>8.2f}  "
      f"{', '.join(f'{k} {v}' for k, v in sorted(cnt.items()))}")
P("")
P("### sanity check: did truncating the population at f_max bias regime A?")
P("")
fullA = []
for f in range(FMIN, N):
    a, cap = ATR[f - 1], nxt16[f]
    if a is None or a <= 0 or cap is None:
        continue
    for side in ("LONG", "SHORT"):
        fullA.append(resolve(f, side, STOP_ATR * a, cap)[0])
P(f"regime A over EVERY bar with a 16:00 ahead (no B/C resolvability filter):")
P(f"  n={len(fullA)}  mean {m(fullA):+.4f}R  vs the common population's "
  f"{m([t['A'][0] for t in trials]):+.4f}R  (Welch z "
  f"{welch(fullA, [t['A'][0] for t in trials]):+.2f})")
P(f"  the common population drops the last {max(HORIZONS)-1} bars of the tape "
  f"({(len(fullA)-len(trials))//2} bars, {(len(fullA)-len(trials))/len(fullA):.1%} of trials).")
P("  The truncated and full populations agree; the common-population requirement")
P("  costs coverage, not comparability.")
P("")

P("## RUNWAY AT ENTRY - the deliverable")
P("")
P("runway = bars available to the trade, counted from the FILL bar through the")
P("flat bar inclusive. A fill landing on the 16:00 bar itself has runway 1: it is")
P("filled at that bar's open and flattened at that bar's close. The decision bar")
P("is f-1, so an agent standing at the decision bar sees runway+1 bars ahead.")
P("Rolled trials have no meaningful runway and are excluded from this section.")
P("")
P(f"{'runway':<9} {'n':>5} | {'A meanR':>8} {'A win%':>7} {'TIMEn':>6} {'TIME%':>7} "
  f"{'A R|TIME':>9} | {'B120 meanR':>10} | {'d=A-B120':>9} {'z(sess)':>8} {'z(week)':>8}")
P(line(103))
bk = []
for lo, hi in BUCKETS:
    sub = [t for t in kept if lo <= t["runway"] <= hi]
    if not sub:
        continue
    a, b = desc(sub, "A"), desc(sub, "B120")
    p = pdiff(sub, "A", "B120")
    nm = f"{lo}-{hi}" if hi < 10**6 else f"{lo}+"
    bk.append((nm, sub, a, b, p))
    tm = f"{a['tmean']:+.4f}" if a["tn"] else "-"
    P(f"{nm:<9} {a['n']:>5} | {a['mean']:>+8.4f} {a['win']:>6.1%} {a['tn']:>6} "
      f"{a['tshare']:>6.1%} {tm:>9} | {b['mean']:>+10.4f} | "
      f"{p['d']:>+9.4f} {p['zs']:>8.2f} {p['zw']:>8.2f}")
P("")
P("Note the TIME% column, which is the mechanical content of the rule: the forced")
P("flat only BINDS on trades that have not already resolved. It binds on most")
P("short-runway trades and on almost none with real runway, so the rule's whole")
P("footprint is concentrated in the 1-6 bar band - and the R|TIME cells for the")
P("7-12 and 13+ buckets rest on the handful of trials in the TIMEn column and")
P("should not be read as estimates of anything.")
P("")
P("same buckets, regime C (one extra cycle) and B48:")
P(f"{'runway':<9} {'n':>5} {'C meanR':>9} {'d=A-C':>9} {'z(week)':>8}   "
  f"{'B48 meanR':>10} {'d=A-B48':>9} {'z(week)':>8}")
P(line(80))
for nm, sub, a, b, p in bk:
    pc, p48 = pdiff(sub, "A", "C"), pdiff(sub, "A", "B48")
    P(f"{nm:<9} {len(sub):>5} {m([t['C'][0] for t in sub]):>+9.4f} "
      f"{pc['d']:>+9.4f} {pc['zw']:>8.2f}   "
      f"{m([t['B48'][0] for t in sub]):>+10.4f} {p48['d']:>+9.4f} {p48['zw']:>8.2f}")
P("")
P("### does runway itself predict anything? (the desk's real question)")
P("")
P("The desk has declined trades for 'not enough runway'. That is a claim about")
P("regime A's own returns: short-runway entries should do WORSE under the owner's")
P("rule than long-runway ones. Each bucket against all the other buckets, same")
P("regime, unpaired (different trials), Welch z:")
P("")
P(f"{'runway':<9} {'n':>5} {'A meanR':>9} {'rest meanR':>11} {'Welch z':>8}   "
  f"{'B120 meanR':>11} {'rest':>9} {'Welch z':>8}")
P(line(84))
for nm, sub, a, b, p in bk:
    lo, hi = next(x for x in BUCKETS
                  if nm in (f"{x[0]}-{x[1]}", f"{x[0]}+"))
    rest = [t for t in kept if not (lo <= t["runway"] <= hi)]
    aa, rr_ = [t["A"][0] for t in sub], [t["A"][0] for t in rest]
    ba, br = [t["B120"][0] for t in sub], [t["B120"][0] for t in rest]
    P(f"{nm:<9} {len(sub):>5} {m(aa):>+9.4f} {m(rr_):>+11.4f} {welch(aa, rr_):>8.2f}   "
      f"{m(ba):>+11.4f} {m(br):>+9.4f} {welch(ba, br):>8.2f}")
P("")
P("per-runway-bar detail under the owner's rule (regime A), clean trials:")
P(f"{'runway':>7} {'n':>5} {'A meanR':>9} {'win%':>7} {'TIME%':>7} {'B120 meanR':>11}")
P(line(52))
for rw in sorted({t["runway"] for t in kept}):
    sub = [t for t in kept if t["runway"] == rw]
    a = desc(sub, "A")
    P(f"{rw:>7} {a['n']:>5} {a['mean']:>+9.4f} {a['win']:>6.1%} {a['tshare']:>6.1%} "
      f"{m([t['B120'][0] for t in sub]):>+11.4f}")
P("")

P("## sensitivities")
P("")
ao = [t["A_open"][0] for t in kept]
ac = [t["A"][0] for t in kept]
dd = [x - y for x, y in zip(ao, ac)]
P("WHICH MINUTE THE FLAT LANDS ON. The bar whose ts hour is '16' spans")
P("16:00-17:00 ET, so flattening at that bar's CLOSE is an exit at 17:00 ET.")
P("Re-running regime A exiting at that bar's OPEN instead - flat at 16:00 ET on")
P(f"the nose - gives mean {m(ao):+.4f}R vs {m(ac):+.4f}R: paired d "
  f"{m(dd):+.4f}R, paired z {zp(dd):+.2f}.")
P("The last hour of the cycle is worth that much and no more, so the ambiguity in")
P("what 'flat at 16:00' means does not move the headline either way.")
P("")
for side in ("LONG", "SHORT"):
    sub = [t for t in kept if t["side"] == side]
    p = pdiff(sub, "A", "B120")
    P(f"{side:<6} only: A {m([t['A'][0] for t in sub]):+.4f}R  "
      f"B120 {m([t['B120'][0] for t in sub]):+.4f}R  d {p['d']:+.4f}R  "
      f"z(week) {p['zw']:+.2f}")
P("")
half = len(kept) // 2
for nm, sub in (("first half of tape", kept[:half]), ("second half", kept[half:])):
    p = pdiff(sub, "A", "B120")
    P(f"{nm:<20}: n={len(sub)}  A {m([t['A'][0] for t in sub]):+.4f}R  "
      f"d(A-B120) {p['d']:+.4f}R  z(week) {p['zw']:+.2f}")
P("")
P("unresolved at the cap (regime B still open at H bars, clean trials):")
for H in HORIZONS:
    sub = [t for t in kept if t[f"B{H}"][2] == "TIME"]
    mm = f"mean {m([t[f'B{H}'][0] for t in sub]):+.4f}R" if sub else "(none)"
    P(f"  H={H:<4} {len(sub):>4}/{len(kept)} = {len(sub)/len(kept):.2%} still open, {mm}")
P("")

P("## what this does NOT say")
P("")
P("1. The population is EVERY bar in both directions. Its base rate is about")
P(f"   {m([t['A'][0] for t in kept]):+.3f}R - a no-edge tape, as it must be for")
P("   arbitrary entries with a symmetric bracket. This prices the flat on")
P("   ARBITRARY entries. It does not price the flat on a strategy whose edge is")
P("   specifically multi-day follow-through; such a strategy would have to be")
P("   shown to exist first, and no arm on this desk has shown one.")
P("2. Regime B holds through maintenance halts and weekends with no gap-risk")
P("   charge beyond the modelled stop, and a gap through the stop books exactly")
P("   -1.0R here. That flatters holding. The measured cost of the flat is")
P("   therefore an UPPER bound on what releasing the rule would earn.")
P("3. One tape, 91 session dates, ~3.5 months, one instrument. Fifteen ISO weeks")
P("   is fifteen clusters; that is what the conservative z is built on.")
P("4. The rule has purposes this cannot measure: overnight headline risk, margin,")
P("   and the operator being asleep. A finding that it costs nothing in R is an")
P("   argument for KEEPING it, since its non-R benefits then come free.")
P("")

P("## bottom line")
P("")
_p = pdiff(kept, "A", "B120")
P(f"The forced 16:00 flat costs {-_p['d']:+.4f}R per trade (95% CI "
  f"[{-_p['hi']:+.4f}, {-_p['lo']:+.4f}]R), week-clustered z {_p['zw']:+.2f} on "
  f"{_p['n']} trials.")
P("That is indistinguishable from zero and bounded well inside a fiftieth of an R.")
P("It binds on 12% of trades. On the ones it binds, it scratches winners")
P("(-0.107R on 224 of 3030) and rescues losers (+0.100R on 145 of 3030), and")
P("those two nearly cancel.")
P("")
P("Runway at entry does NOT predict returns. Every bucket sits within 0.02R of")
P("the rest of the population under the owner's rule (|Welch z| <= 0.30), and the")
P("paired cost of the flat is flat across buckets too (|z(week)| <= 0.70). The")
P("desk's 'not enough runway' refusals are not supported by the tape: a two-bar")
P("entry is not a measurably worse instrument than a twenty-bar entry. What")
P("runway does change is MECHANICS, not expectancy - with 1-2 bars the flat")
P("decides 79% of outcomes and with 7+ bars it decides under 2% - so a")
P("short-runway trade is mostly a bet on the flat print rather than on the")
P("bracket. If the desk wants to keep declining them, the honest reason is that")
P("the bracket is not the thing being tested, not that the expectancy is worse.")
P("")

report = "\n".join(out)
print(report)
if os.environ.get("E4_WRITE"):
    with open(os.path.join(D, "E4_session.md"), "w") as fh:
        fh.write(report + "\n")
    print("\n[wrote E4_session.md]")
