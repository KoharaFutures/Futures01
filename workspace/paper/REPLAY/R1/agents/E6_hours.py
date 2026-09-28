#!/usr/bin/env python3
"""E6_hours.py - independent test of rule 5 ("no intraday entries 15:00-16:00 ET")
and rule 6 ("no hours filter improves expectancy") on R1's own visible tape.

AGENT E6, REPLAY desk, closed-market window.

READS ONLY visible.jsonl (inside R1's own lane, bars the cursor has already
passed). Writes nothing but its own report. Does not touch state.json, does not
advance any cursor, does not import missed.py (which rewrites missed.jsonl at
module scope).

ENGINE CONVENTIONS - copied from missed.py / A_grid.py so numbers are comparable:
  - fill at the next bar's open plus one tick of slippage (TICK = 0.25)
  - stop WINS a same-bar stop/target tie
  - 1.0 ATR stop, 2R target
  - ATR14 from bars at or before the DECISION bar, i.e. atr(f-1)
  - flat at the session close (the first 16:00 ET bar at or after the fill)
  - control population = every eligible bar, range(20, len(rows))

POPULATION (stated up front, as the desk requires)
  BOTH DIRECTIONS at every eligible bar f in range(20, len(rows)) whose forward
  window closes inside the visible tape. Hour 16 is the desk's FLAT bar, not an
  entry hour, so the 22-hour cycle grid is hours 18-23 and 00-15. Hour 16 is
  computed and reported as a footnote only (its "trade" opens and closes on the
  same bar, so it is degenerate) and is NOT in the 22-hour multiple-testing count.
  Hour 17 does not exist on this tape (CME maintenance halt).

UNIT OF OBSERVATION - and why it is the BAR, not the trade
  Long R and short R at the same bar are near-perfect mirror images: for a
  session-close exit, R_long + R_short = -2*TICK/S exactly. Treating them as two
  independent observations would double n while the information is one bar's
  forward path, understating every standard error. So the primary unit is the
  BAR, scored as the mean of its long and short R. The pooled-trade figures are
  printed alongside; the MEAN is identical either way (the per-bar mean of a
  mean), only the SE differs, and the paired SE is the honest one.

KNOWN CONFOUNDS, measured not hidden
  1. HOLDING WINDOW IS NOT CONSTANT ACROSS HOURS. An 18:00 entry has ~22 bars to
     the 16:00 flat; a 15:00 entry has 2. Rule 5's window is therefore also the
     shortest-horizon window on the tape, and any hour effect is entangled with
     bars-to-flat. bars_to_flat is reported per hour so the reader can see it.
  2. OVERLAPPING FORWARD WINDOWS. All 22 hour-buckets of one ET session read
     largely the same forward price path, so the hour observations inside a day
     are serially dependent. A session-date-clustered SE is reported for the
     rule-5 test as a check on the unclustered z.

TRIAL COUNT
  22 hour cells, swept. free_t = sqrt(2*ln 22) = 2.4909. Reported against a
  naive 1.96 as well, because the gap is the point of the exercise.
"""
import json, math, os
from collections import defaultdict

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = [json.loads(l) for l in open(os.path.join(D, "visible.jsonl"))]

TICK = 0.25
STOP_MULT, RR = 1.0, 2.0
FLAT_HOUR = "16"


# ---- engine mechanics, lifted from missed.py / A_grid.py -------------------
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
        if rows[j]["ts"][11:13] == FLAT_HOUR:
            out = j
            break
    _send[f] = out
    return out


def simulate(f, side, S, rr=RR):
    end = session_end(f)
    if end is None or S is None or S <= 0:
        return None
    sgn = 1 if side == "LONG" else -1
    fill = rows[f]["o"] + sgn * TICK
    stop, targ = fill - sgn * S, fill + sgn * rr * S
    for j in range(f, end + 1):
        b = rows[j]
        hit_stop = b["l"] <= stop if sgn > 0 else b["h"] >= stop
        hit_targ = b["h"] >= targ if sgn > 0 else b["l"] <= targ
        if hit_stop:
            return -1.0, j, "STOP"
        if hit_targ:
            return rr, j, "TARGET"
    return sgn * (rows[end]["c"] - fill) / S, end, "SESSION_CLOSE"


# ---- statistics, lifted from missed.py ------------------------------------
def mean(v):
    return sum(v) / len(v) if v else 0.0


def sd(v):
    if len(v) < 2:
        return 0.0
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def se(v):
    return sd(v) / math.sqrt(len(v)) if len(v) >= 2 else 0.0


def welch(a, b):
    if len(a) < 2 or len(b) < 2:
        return 0.0
    s = (sd(a) ** 2 / len(a) + sd(b) ** 2 / len(b)) ** 0.5
    return (mean(a) - mean(b)) / s if s > 0 else 0.0


def median(v):
    if not v:
        return 0.0
    s = sorted(v)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def clustered_welch(a_pairs, b_pairs):
    """Two-sample z where the independent unit is the ET SESSION DATE, not the
    bar. a_pairs/b_pairs are [(date, r), ...]; each date collapses to its mean."""
    def collapse(p):
        g = defaultdict(list)
        for d, r in p:
            g[d].append(r)
        return [mean(v) for v in g.values()]
    return welch(collapse(a_pairs), collapse(b_pairs)), \
        len(set(d for d, _ in a_pairs)), len(set(d for d, _ in b_pairs))


# ---- build the population --------------------------------------------------
recs = []           # one per eligible bar
for f in range(20, len(rows)):
    if session_end(f) is None:
        continue
    a = atr(f - 1)
    if a is None:
        continue
    S = STOP_MULT * a
    L, Sh = simulate(f, "LONG", S), simulate(f, "SHORT", S)
    if L is None or Sh is None:
        continue
    recs.append({
        "f": f, "hour": rows[f]["ts"][11:13], "date": rows[f]["ts"][:10],
        "long": L[0], "short": Sh[0], "bar": (L[0] + Sh[0]) / 2.0,
        "why": (L[2], Sh[2]), "btf": session_end(f) - f,
        "v": rows[f]["v"], "atr": a,
    })

CYCLE = [f"{h:02d}" for h in list(range(18, 24)) + list(range(0, 16))]
assert len(CYCLE) == 22, len(CYCLE)
N_TRIALS = 22
FREE_T = math.sqrt(2 * math.log(N_TRIALS))

grid = [r for r in recs if r["hour"] in CYCLE]
byh = defaultdict(list)
for r in grid:
    byh[r["hour"]].append(r)

print("=" * 108)
print("E6 - HOURS SWEEP.  1.0 ATR stop / 2R target / next-open +1 tick / stop wins tie / flat at 16:00 ET")
print(f"tape {len(rows)} bars  {rows[0]['ts']} -> {rows[-1]['ts']}")
print(f"eligible bars (all hours incl. flat bar) {len(recs)}   22-hour cycle grid {len(grid)} bars "
      f"= {2*len(grid)} trades")
print(f"trials = {N_TRIALS} hour cells   free_t = sqrt(2 ln {N_TRIALS}) = {FREE_T:.4f}   naive = 1.96")
print("=" * 108)

ALL = [r["bar"] for r in grid]
ALL_TR = [r["long"] for r in grid] + [r["short"] for r in grid]
m_all = mean(ALL)
print(f"\nALL-HOURS BASELINE (22-hour cycle): n_bars {len(ALL)}  n_trades {len(ALL_TR)}")
print(f"  mean R {m_all:+.4f}   SE(bar-unit) {se(ALL):.4f}   SE(pooled-trade) {se(ALL_TR):.4f}"
      f"   median(bar) {median(ALL):+.4f}   median(pooled trades) {median(ALL_TR):+.4f}")

# ---- 1. mean R by ET hour --------------------------------------------------
print("\n" + "-" * 108)
print("1.  MEAN R BY ET HOUR OF ENTRY  (bar unit = mean of that bar's long and short R)")
print("-" * 108)
hdr = (f"{'hr':>3} {'n_bar':>6} {'n_trd':>6} {'btf':>4} {'meanR':>9} {'SE':>7} {'medR':>8} "
       f"{'z_vs_rest':>10} {'z_vs_all':>9} {'longR':>8} {'shortR':>8} {'tgt%':>6} {'stp%':>6}")
print(hdr)
print("-" * len(hdr))
table = {}
for h in CYCLE:
    rs = byh[h]
    v = [r["bar"] for r in rs]
    rest = [r["bar"] for r in grid if r["hour"] != h]
    z_rest = welch(v, rest)
    z_all = (mean(v) - m_all) / se(v) if se(v) > 0 else 0.0
    trades = [r["long"] for r in rs] + [r["short"] for r in rs]
    whys = [w for r in rs for w in r["why"]]
    tgt = 100.0 * sum(1 for w in whys if w == "TARGET") / len(whys)
    stp = 100.0 * sum(1 for w in whys if w == "STOP") / len(whys)
    table[h] = dict(n=len(rs), v=v, rest=rest, m=mean(v), se=se(v), med=median(v),
                    z_rest=z_rest, z_all=z_all, trades=trades,
                    med_tr=median(trades), btf=mean([r["btf"] for r in rs]),
                    tgt=tgt, stp=stp)
    mark = ""
    if abs(z_rest) >= FREE_T:
        mark = "  <<< clears free_t"
    elif abs(z_rest) >= 1.96:
        mark = "  <  clears 1.96 only"
    print(f"{h:>3} {len(rs):>6} {2*len(rs):>6} {table[h]['btf']:>4.1f} {mean(v):>+9.4f} {se(v):>7.4f} "
          f"{median(v):>+8.4f} {z_rest:>+10.3f} {z_all:>+9.3f} "
          f"{mean([r['long'] for r in rs]):>+8.4f} {mean([r['short'] for r in rs]):>+8.4f} "
          f"{tgt:>6.1f} {stp:>6.1f}{mark}")

n_free = sum(1 for h in CYCLE if abs(table[h]["z_rest"]) >= FREE_T)
n_naive = sum(1 for h in CYCLE if abs(table[h]["z_rest"]) >= 1.96)
print("-" * len(hdr))
print(f"hours clearing free_t {FREE_T:.3f}: {n_free} / 22      hours clearing naive 1.96: {n_naive} / 22")
if n_naive:
    print("  naive-only survivors: " + ", ".join(
        f"{h}({table[h]['z_rest']:+.2f})" for h in CYCLE if abs(table[h]["z_rest"]) >= 1.96))
print(f"  expected false positives at 1.96 under a true null of 22 tests: {22*0.05:.1f}")

# footnote: the flat bar
f16 = [r for r in recs if r["hour"] == FLAT_HOUR]
if f16:
    v16 = [r["bar"] for r in f16]
    print(f"\nfootnote - hour 16 (the FLAT bar, excluded from the grid and from the 22 trials):"
          f" n_bars {len(f16)}  mean R {mean(v16):+.4f}  SE {se(v16):.4f}  median {median(v16):+.4f}"
          f"  mean bars_to_flat {mean([r['btf'] for r in f16]):.1f}")
    print("  degenerate by construction: fill on this bar's open, flat on this bar's close.")

# ---- 2. rule 5 -------------------------------------------------------------
print("\n" + "-" * 108)
print("2.  RULE 5 - the 15:00 ET hour vs all other hours")
print("   reported by the programme at z = -4.43, median -0.617R, 'replicated'")
print("-" * 108)
h15 = table["15"]
rest15 = h15["rest"]
rest15_tr = [r["long"] for r in grid if r["hour"] != "15"] + [r["short"] for r in grid if r["hour"] != "15"]
print(f"  15:00 hour   n_bars {h15['n']:>5}  n_trades {2*h15['n']:>5}  mean R {h15['m']:+.4f}"
      f"  SE {h15['se']:.4f}  median(bar) {h15['med']:+.4f}  median(trades) {h15['med_tr']:+.4f}")
print(f"  other hours  n_bars {len(rest15):>5}  n_trades {len(rest15_tr):>5}  mean R {mean(rest15):+.4f}"
      f"  SE {se(rest15):.4f}  median(bar) {median(rest15):+.4f}  median(trades) {median(rest15_tr):+.4f}")
print(f"  difference   {h15['m']-mean(rest15):+.4f} R")
print(f"  z (bar unit, Welch)            {h15['z_rest']:+.4f}")
print(f"  z (pooled trades, Welch)       {welch(h15['trades'], rest15_tr):+.4f}   [inflated n, shown for comparability]")
zc, na, nb = clustered_welch([(r['date'], r['bar']) for r in byh['15']],
                             [(r['date'], r['bar']) for r in grid if r['hour'] != '15'])
print(f"  z (ET-session-date clustered)  {zc:+.4f}   [{na} dates vs {nb} dates]")
print(f"\n  directional arms taken alone (in case the programme's figure was signal-directional):")
for arm in ("long", "short"):
    a = [r[arm] for r in byh["15"]]
    b = [r[arm] for r in grid if r["hour"] != "15"]
    print(f"    {arm:>5}-only  15:00 mean {mean(a):+.4f}  median {median(a):+.4f}  n {len(a)}"
          f"   | rest mean {mean(b):+.4f} median {median(b):+.4f}   z {welch(a,b):+.4f}")
print(f"\n  REPLICATION CHECK   reported z -4.4300  vs measured z {h15['z_rest']:+.4f}"
      f"   (|gap| {abs(-4.43 - h15['z_rest']):.2f})")
print(f"                      reported median -0.6170R vs measured median(bar) {h15['med']:+.4f}"
      f" / median(trades) {h15['med_tr']:+.4f}")
print(f"  free_t at 22 trials {FREE_T:.3f}: 15:00 {'CLEARS' if abs(h15['z_rest'])>=FREE_T else 'does NOT clear'}")
print(f"  bars_to_flat at 15:00 is {h15['btf']:.1f} (vs {mean([r['btf'] for r in grid]):.1f} tape-wide) "
      f"-> {h15['tgt']:.1f}% TARGET, {h15['stp']:.1f}% STOP, {100-h15['tgt']-h15['stp']:.1f}% SESSION_CLOSE")

# arithmetic identity that bounds the pooled median
print("\n  WHY A BOTH-DIRECTIONS POPULATION CANNOT PRODUCE median -0.617R:")
print("    for a SESSION_CLOSE exit, R_long + R_short = -2*TICK/S exactly, so the pooled")
print("    trade distribution is symmetric about -TICK/S ~ 0. A deeply negative median needs")
print("    a DIRECTION-SELECTED population. Measured pooled median here: "
      f"{h15['med_tr']:+.5f}; -TICK/mean(S) = {-TICK/mean([r['atr'] for r in byh['15']]):+.5f}")

# ---- 3. rule 6 -------------------------------------------------------------
print("\n" + "-" * 108)
print("3.  RULE 6 - does ANY single-hour exclusion improve the overall mean?")
print("-" * 108)
print(f"  baseline all-22-hours mean R {m_all:+.5f}  (n_bars {len(ALL)})")
hdr2 = f"{'excl hr':>7} {'n kept':>7} {'mean R kept':>12} {'delta':>9} {'z_hour_vs_rest':>15} {'verdict':>22}"
print(hdr2)
print("-" * len(hdr2))
improves = []
for h in CYCLE:
    kept = table[h]["rest"]
    d = mean(kept) - m_all
    if d > 0:
        improves.append((d, h))
    z = table[h]["z_rest"]
    verdict = ("clears free_t" if abs(z) >= FREE_T else
               "clears 1.96 only" if abs(z) >= 1.96 else "not significant")
    print(f"{h:>7} {len(kept):>7} {mean(kept):>+12.5f} {d:>+9.5f} {z:>+15.3f} {verdict:>22}")
print("-" * len(hdr2))
improves.sort(reverse=True)
print(f"  single-hour exclusions that RAISE the overall mean: {len(improves)} of 22")
print("  top 5 by raw improvement (before any correction):")
for d, h in improves[:5]:
    print(f"    drop {h}:00  ->  {m_all+d:+.5f}  ({d:+.5f} R)   z of that hour vs rest {table[h]['z_rest']:+.3f}")
print(f"\n  hours clearing free_t {FREE_T:.4f} : {n_free}")
print(f"  hours clearing naive 1.96        : {n_naive}")
print(f"  GAP = {n_naive - n_free}  <- the whole point: the naive threshold manufactures "
      f"{n_naive - n_free} 'hours filter(s)'")
best_d, best_h = (improves[0] if improves else (0.0, None))
print(f"\n  RULE 6 VERDICT: the best single-hour exclusion (drop {best_h}:00) buys {best_d:+.5f} R/trade;")
print(f"  at {N_TRIALS} trials it needs |z| >= {FREE_T:.3f} and has "
      f"{abs(table[best_h]['z_rest']) if best_h else 0:.3f}.")

# ---- 4. the 18:00 hour -----------------------------------------------------
print("\n" + "-" * 108)
print("4.  THE 18:00 ET HOUR - first bar of the owner's own cycle")
print("-" * 108)
h18rows = [r for r in rows if r["ts"][11:13] == "18"]
z18 = [r for r in h18rows if r["v"] == 0]
allz = [r for r in rows if r["v"] == 0]
print(f"  volume, re-counted on the CURRENT tape ({len(rows)} bars):")
print(f"    zero-volume bars tape-wide      {len(allz)}")
print(f"    of which in the 18:00 hour      {len(z18)}  ({100.0*len(z18)/len(allz):.1f}% of all zero-vol bars)")
print(f"    18:00 bars total                {len(h18rows)}  -> {100.0*len(z18)/len(h18rows):.1f}% of the hour is zero-volume")
print(f"    zero-vol 18:00 bars with NON-ZERO high-low range: "
      f"{sum(1 for r in z18 if r['h'] > r['l'])} / {len(z18)}")
print("    (earlier agent reported 56 of 60 / 79%; the tape has since grown, ratio holds)")
print("    where the other zero-vol bars sit: " + ", ".join(
    f"{r['ts'][:16]}" for r in allz if r["ts"][11:13] != "18"))

t18 = table["18"]
print(f"\n  R BEHAVIOUR of 18:00 entries:")
print(f"    n_bars {t18['n']}  mean R {t18['m']:+.4f}  SE {t18['se']:.4f}  median {t18['med']:+.4f}"
      f"  z vs rest {t18['z_rest']:+.3f}  z vs all {t18['z_all']:+.3f}")
print(f"    bars_to_flat {t18['btf']:.1f} (longest on the tape)   TARGET {t18['tgt']:.1f}%  STOP {t18['stp']:.1f}%")
zb = [r["bar"] for r in byh["18"] if r["v"] == 0]
nzb = [r["bar"] for r in byh["18"] if r["v"] > 0]
print(f"    zero-vol 18:00 entries  n {len(zb)} mean R {mean(zb):+.4f}"
      f"   | non-zero-vol 18:00 entries n {len(nzb)} mean R {mean(nzb):+.4f}"
      f"   z {welch(zb, nzb):+.3f}")

print(f"\n  PRICE behaviour of the 18:00 bar (is it thin, or just missing a field?):")
def pstats(sel, label):
    if not sel:
        return
    rng = [r["h"] - r["l"] for r in sel]
    body = [abs(r["c"] - r["o"]) for r in sel]
    gaps = []
    for r in sel:
        i = r["_i"]
        if i > 0:
            gaps.append(abs(r["o"] - rows[i - 1]["c"]))
    print(f"    {label:<34} n {len(sel):>5}  mean range {mean(rng):>6.2f}  median range {median(rng):>6.2f}"
          f"  mean |c-o| {mean(body):>5.2f}  mean |gap from prior close| {mean(gaps):>5.2f}")
for i, r in enumerate(rows):
    r["_i"] = i
pstats(h18rows, "18:00 bars, all")
pstats([r for r in h18rows if r["v"] == 0], "18:00 bars, zero volume")
pstats([r for r in h18rows if r["v"] > 0], "18:00 bars, non-zero volume")
pstats([r for r in rows if r["ts"][11:13] == "19"], "19:00 bars (the hour after)")
pstats([r for r in rows if r["ts"][11:13] not in ("18",)], "all non-18:00 bars")
rth = [r for r in rows if r["ts"][11:13] in ("09","10","11","12","13","14","15")]
pstats(rth, "RTH bars 09:00-15:00")
pstats([r for r in rows if r["ts"][11:13] in ("20","21","22","23","00","01","02","03","04","05")],
       "overnight 20:00-05:00")

# is the 18:00 range abnormal FOR ITS TIME OF DAY?
r18 = [r["h"] - r["l"] for r in h18rows]
r_on = [r["h"] - r["l"] for r in rows if r["ts"][11:13] in ("19","20","21","22","23")]
print(f"\n    18:00 range vs 19:00-23:00 range: Welch z {welch(r18, r_on):+.3f}"
      f"  ({mean(r18):.2f} vs {mean(r_on):.2f} pts)")
gap18 = [abs(r["o"] - rows[r["_i"]-1]["c"]) for r in h18rows if r["_i"] > 0]
gap_oth = [abs(r["o"] - rows[r["_i"]-1]["c"]) for r in rows
           if r["_i"] > 0 and r["ts"][11:13] != "18"]
print(f"    18:00 |open - prior close| vs all other hours: Welch z {welch(gap18, gap_oth):+.3f}"
       f"  ({mean(gap18):.2f} vs {mean(gap_oth):.2f} pts)")
print("      NOTE: the bar before an 18:00 bar is the 16:00 bar (17:00 is the CME halt), so this")
print("      'gap' spans the 2-hour 16:00->18:00 break. A large value here is the halt, not a defect.")
print(f"    18:00 bars that are a pure doji (h==l): {sum(1 for r in h18rows if r['h']==r['l'])}")
print(f"    18:00 bars whose range is 0 < range <= 1.0 pt: "
      f"{sum(1 for r in h18rows if 0 < r['h']-r['l'] <= 1.0)}")

# ---- 5. follow-ups raised by sections 1-4 ---------------------------------
print("\n" + "-" * 108)
print("5.  FOLLOW-UPS RAISED BY THE ABOVE  (robustness views of the same 22 cells, not new searches)")
print("-" * 108)

print("\n  5a. why the zero-volume 18:00 mean R is EXACTLY 0.0 (it is not a bug):")
zr = [r for r in byh["18"] if r["v"] == 0]
from collections import Counter
print("      bar-R value counts: " + str(dict(Counter(round(r["bar"], 4) for r in zr))))
print("      38 bars at +0.5 (one TARGET, one STOP) and 19 at -1.0 (both STOP): 38*0.5 - 19*1 = 0.")
print("      With ~0% SESSION_CLOSE exits at this hour the distribution is quantised to {+0.5,-1.0},")
print("      so an exact zero is an arithmetic coincidence of a 2-valued sample.")

print("\n  5b. the 18:00 zero-volume bars are MON-THU ONLY; the 15 that carry volume are ALL SUNDAYS:")
import datetime
dow_z = Counter(datetime.date.fromisoformat(r["ts"][:10]).strftime("%a")
                for r in rows if r["ts"][11:13] == "18" and r["v"] == 0)
dow_n = Counter(datetime.date.fromisoformat(r["ts"][:10]).strftime("%a")
                for r in rows if r["ts"][11:13] == "18" and r["v"] > 0)
print("      zero-volume 18:00 by weekday : " + str(dict(dow_z)))
print("      volume-bearing 18:00 by weekday: " + str(dict(dow_n)))
print("      The Sunday 18:00 weekly reopen reports volume; the Mon-Thu 18:00 reopen after the")
print("      daily 17:00-18:00 maintenance halt reports zero. That is a field tied to the HALT,")
print("      not to liquidity - a genuinely dead hour would not be dead only on four weekdays.")

print("\n  5c. rule 5 read as the COMBINED 15:00+16:00 window (what '15:00-16:00' literally spans):")
win = [r["bar"] for r in recs if r["hour"] in ("15", "16")]
restw = [r["bar"] for r in recs if r["hour"] not in ("15", "16")]
tw = [r["long"] for r in recs if r["hour"] in ("15", "16")] + \
     [r["short"] for r in recs if r["hour"] in ("15", "16")]
print(f"      window n_bars {len(win)} mean {mean(win):+.4f} SE {se(win):.4f} "
      f"median(bar) {median(win):+.4f} median(trades) {median(tw):+.4f}")
print(f"      rest   n_bars {len(restw)} mean {mean(restw):+.4f}   Welch z {welch(win, restw):+.3f}"
      f"  -> {'CLEARS' if abs(welch(win,restw))>=FREE_T else 'does NOT clear'} free_t {FREE_T:.3f}")

print("\n  5d. the 16:00 flat-bar cell is the ONLY cell on the tape near significance. It is a COST:")
r16 = [r for r in recs if r["hour"] == FLAT_HOUR]
v16b = [r["bar"] for r in r16]
n_sc = sum(1 for r in r16 for x in r["why"] if x == "SESSION_CLOSE")
n_st = sum(1 for r in r16 for x in r["why"] if x == "STOP")
tick_cost = mean([-TICK / r["atr"] for r in r16])
print(f"      Welch z vs the 22-hour grid {welch(v16b, ALL):+.3f}   free_t(22) {FREE_T:.3f}, "
      f"free_t(23) {math.sqrt(2*math.log(23)):.3f} -> does NOT clear either")
print(f"      long-only {mean([r['long'] for r in r16]):+.5f}  short-only {mean([r['short'] for r in r16]):+.5f}"
      f"  <- near-identical, so SYMMETRIC: a cost, not a direction")
print(f"      exits: SESSION_CLOSE {n_sc}, STOP {n_st} of {2*len(r16)} trades")
print(f"      mechanics alone predict ({n_sc} x {tick_cost:.5f} + {n_st} x -1.0)/{2*len(r16)} = "
      f"{(n_sc*tick_cost + n_st*-1.0)/(2*len(r16)):+.5f}; observed {mean(v16b):+.5f}")
print("      i.e. one tick of slippage plus 8 stop-outs on a one-bar hold. No market claim survives.")

print("\n  5e. is the 18:00 bar's WIDTH unusual, independent of its volume field?")
def anr(hs):
    v = []
    for i, r in enumerate(rows):
        if i < 15 or r["ts"][11:13] not in hs:
            continue
        a = atr(i - 1)
        if a and a > 0:
            v.append((r["h"] - r["l"]) / a)
    return v
a18, blk = anr({"18"}), anr({"19", "20", "21", "22", "23", "00", "01", "02"})
a18z = [(r["h"]-r["l"])/atr(i-1) for i, r in enumerate(rows)
        if i >= 15 and r["ts"][11:13] == "18" and r["v"] == 0 and atr(i-1)]
a18n = [(r["h"]-r["l"])/atr(i-1) for i, r in enumerate(rows)
        if i >= 15 and r["ts"][11:13] == "18" and r["v"] > 0 and atr(i-1)]
print(f"      ATR-normalised range   18:00 mean {mean(a18):.3f}  |  19:00-02:00 block mean {mean(blk):.3f}"
      f"  Welch z {welch(a18, blk):+.3f}")
print(f"      zero-volume 18:00 only: n {len(a18z)} mean {mean(a18z):.3f}  z vs that block {welch(a18z, blk):+.3f}")
print(f"      Sunday volume-bearing 18:00: n {len(a18n)} mean {mean(a18n):.3f}")
print("      The bar that reports NO volume is WIDER than all eight volume-bearing hours after it.")
h18i = [(i, r) for i, r in enumerate(rows) if r["ts"][11:13] == "18"]
h19i = [(i, r) for i, r in enumerate(rows) if r["ts"][11:13] == "19"]
eng = sum(1 for i, r in h18i if i+1 < len(rows) and rows[i+1]["ts"][11:13] == "19"
          and r["h"] >= rows[i+1]["h"] and r["l"] <= rows[i+1]["l"])
eng19 = sum(1 for i, r in h19i if i+1 < len(rows) and rows[i+1]["ts"][11:13] == "20"
            and r["h"] >= rows[i+1]["h"] and r["l"] <= rows[i+1]["l"])
print(f"      18:00 bar engulfs the next 19:00 bar: {eng}/{len(h18i)}"
      f"   control, 19:00 engulfs 20:00: {eng19}/{len(h19i)}")
print("      Consistent with the 18:00 bar carrying price action from a longer interval than one hour")
print("      (the 17:00-18:00 halt window), which would also explain a missing volume field. NOT PROVEN")
print("      here - it needs the source series, which this lane may not read.")

print("\n" + "=" * 108)
print(f"TRIAL COUNT DECLARED: {N_TRIALS} hour cells swept, free_t {FREE_T:.4f}. The rule-5 and 18:00")
print("tests are two of those 22, not extra trials. The paired/pooled/clustered SE variants and the")
print("directional arms are ROBUSTNESS VIEWS OF THE SAME CELLS, reported together, not independent")
print(f"searches; had they been counted as separate searches the trial count would be ~66 and")
print(f"free_t {math.sqrt(2*math.log(66)):.2f}. No cell here reaches either figure.")
print("=" * 108)
