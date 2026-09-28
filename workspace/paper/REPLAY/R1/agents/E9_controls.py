#!/usr/bin/env python3
"""E9: audit the CONTROLS the R1 desk's nulls rest on.

Read-only. Touches ONLY visible.jsonl and callouts.jsonl inside R1's lane, plus
re-implementations of missed.py / levels.py logic (copied, not imported, so that
nothing in this file can advance a cursor or rewrite missed.jsonl).

Four questions:
  1. Is missed.py's "every eligible bar" control balanced against the stand-down
     population on hour-of-day, ATR regime, day-of-week and bars-to-session-close?
     If not, re-run every arm MATCHED and report whether any published z moves.
  2. Is levels.py's random-price-line control comparable to real pivot levels on
     (a) where in the trailing range the line sits and (b) touch counts?
  3. Is bar-index parity independent of the tape (the "coin flip")?
  4. What question does the all-bars control actually answer?
"""
import json, os, random, math
from collections import Counter, defaultdict

D = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.dirname(D)
rows = [json.loads(l) for l in open(os.path.join(R1, "visible.jsonl"))]
calls = [json.loads(l) for l in open(os.path.join(R1, "callouts.jsonl"))]
N = len(rows)

TICK, STOP_ATR, RR, PIVOT_K = 0.25, 1.0, 2.0, 3

# ---------------------------------------------------------------- missed.py core
def atr(i, n=14):
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3:
        return None
    trs = [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
           for p, c in zip(seg, seg[1:])]
    return sum(trs) / len(trs)

def session_end(f):
    for j in range(f, N):
        if rows[j]["ts"][11:13] == "16":
            return j
    return None

def simulate(f, side, S):
    end = session_end(f)
    if end is None or S is None or S <= 0:
        return None
    sgn = 1 if side == "LONG" else -1
    fill = rows[f]["o"] + sgn * TICK
    stop, targ = fill - sgn * S, fill + sgn * RR * S
    mfe = 0.0
    for j in range(f, end + 1):
        b = rows[j]
        mfe = max(mfe, sgn * (b["h"] - fill) if sgn > 0 else sgn * (b["l"] - fill))
        if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop):
            return -1.0, mfe / S, j, "STOP"
        if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ):
            return RR, mfe / S, j, "TARGET"
    return sgn * (rows[end]["c"] - fill) / S, mfe / S, end, "SESSION_CLOSE"

def is_pivot(f, tol=1):
    a, b = f - PIVOT_K, f + PIVOT_K
    if a < 0 or b >= N:
        return None
    seg = list(range(a, b + 1))
    lo = min(seg, key=lambda j: rows[j]["l"])
    hi = max(seg, key=lambda j: rows[j]["h"])
    if abs(lo - f) <= tol:
        return "LOW"
    if abs(hi - f) <= tol:
        return "HIGH"
    return None

def evaluate(f):
    a = atr(f - 1)
    if a is None:
        return None
    S = STOP_ATR * a
    L, Sh = simulate(f, "LONG", S), simulate(f, "SHORT", S)
    if L is None or Sh is None:
        return None
    end = session_end(f)
    return {"bar": f, "atr": a, "long": L, "short": Sh, "pivot": is_pivot(f),
            "best": max(L[0], Sh[0]), "hour": int(rows[f]["ts"][11:13]),
            "dow": dow(f), "ttc": end - f,
            "flip": L[0] if f % 2 == 0 else Sh[0]}

_DOWN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
def dow(f):
    import datetime
    d = datetime.date(int(rows[f]["ts"][0:4]), int(rows[f]["ts"][5:7]), int(rows[f]["ts"][8:10]))
    return _DOWN[d.weekday()]

# ---------------------------------------------------------------- stats
def mean(v): return sum(v) / len(v) if v else 0.0
def sd(v):
    if len(v) < 2: return 0.0
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
def welch(a, b):
    if len(a) < 2 or len(b) < 2: return 0.0
    se = (sd(a) ** 2 / len(a) + sd(b) ** 2 / len(b)) ** 0.5
    return (mean(a) - mean(b)) / se if se > 0 else 0.0

# ================================================================ populations
stand_calls = [c for c in calls if c.get("confidence") == "NO_TRADE"]
res, pending = [], 0
for c in stand_calls:
    f = c["visible_bars"]
    if f >= N or session_end(f) is None:
        pending += 1; continue
    e = evaluate(f)
    if e: res.append(e)

ctrl = []
for f in range(20, N):
    if session_end(f) is None: continue
    e = evaluate(f)
    if e: ctrl.append(e)

print("=" * 78)
print("E9 CONTROL AUDIT  --  R1 replay desk")
print(f"visible {N} bars | NO_TRADE callouts {len(stand_calls)} "
      f"({len(res)} scored, {pending} pending) | control population {len(ctrl)} bars")
print("=" * 78)

# ---------- reproduce the published arms ---------------------------------
ARMS = {
    "always LONG":  (lambda e: e["long"][0]),
    "always SHORT": (lambda e: e["short"][0]),
    "coin flip":    (lambda e: e["flip"]),
    "BEST (hindsight)": (lambda e: e["best"]),
}
print("\n[0] REPRODUCTION of the published all-bars comparison (missed.py as written)")
print(f"{'arm':<20} {'n':>4} {'stand-down':>11} {'control':>9} {'diff':>8} {'z':>7}")
published = {}
for lbl, fn in ARMS.items():
    a = [fn(e) for e in res]; b = [fn(e) for e in ctrl]
    published[lbl] = (mean(a), mean(b), mean(a) - mean(b), welch(a, b))
    print(f"{lbl:<20} {len(a):>4} {mean(a):>+10.3f}R {mean(b):>+8.3f}R "
          f"{mean(a)-mean(b):>+7.3f}R {welch(a,b):>+7.2f}")

# ================================================================ Q1 BALANCE
print("\n" + "=" * 78)
print("[1] BALANCE OF THE ALL-BARS CONTROL AGAINST THE STAND-DOWN POPULATION")
print("=" * 78)

def dist(pop, key):
    c = Counter(key(e) for e in pop)
    n = len(pop)
    return {k: v / n for k, v in c.items()}, c

def smd(a, b):
    """standardised mean difference, pooled sd (|SMD|>0.25 = imbalance by convention)"""
    s = math.sqrt((sd(a) ** 2 + sd(b) ** 2) / 2)
    return (mean(a) - mean(b)) / s if s > 0 else 0.0

def show(name, key, order=None, tvd_only=False):
    ds, cs = dist(res, key); dc, cc = dist(ctrl, key)
    keys = order or sorted(set(ds) | set(dc), key=lambda x: str(x))
    tvd = 0.5 * sum(abs(ds.get(k, 0) - dc.get(k, 0)) for k in keys)
    print(f"\n-- {name}   (total variation distance {tvd:.3f})")
    print(f"{'bucket':<10} {'stand-down':>12} {'control':>10} {'ratio':>8}")
    for k in keys:
        p, q = ds.get(k, 0.0), dc.get(k, 0.0)
        ratio = (p / q) if q else float('inf')
        flag = "  <<<" if q and (p / q > 1.6 or p / q < 0.6) and p > 0.02 else ""
        print(f"{str(k):<10} {p:>11.1%} ({cs.get(k,0):>3}) {q:>9.1%} {ratio:>8.2f}{flag}")
    return tvd

tvd_hour = show("HOUR OF DAY (ET)", lambda e: e["hour"], order=list(range(0, 24)))

# ATR quartiles from the CONTROL population
atrs = sorted(e["atr"] for e in ctrl)
q = [atrs[int(len(atrs) * f)] for f in (0.25, 0.50, 0.75)]
def aq(e):
    a = e["atr"]
    return "Q1" if a <= q[0] else "Q2" if a <= q[1] else "Q3" if a <= q[2] else "Q4"
print(f"\nATR quartile cuts (from control): {q[0]:.2f} / {q[1]:.2f} / {q[2]:.2f} pts")
tvd_atr = show("ATR QUARTILE", aq, order=["Q1", "Q2", "Q3", "Q4"])
print(f"   mean ATR: stand-down {mean([e['atr'] for e in res]):.2f}  "
      f"control {mean([e['atr'] for e in ctrl]):.2f}  "
      f"SMD {smd([e['atr'] for e in res],[e['atr'] for e in ctrl]):+.3f}")

tvd_dow = show("DAY OF WEEK", lambda e: e["dow"],
               order=["Mon", "Tue", "Wed", "Thu", "Fri", "Sun"])

def ttcb(e):
    t = e["ttc"]
    return "0 (16:00)" if t == 0 else "1-3" if t <= 3 else "4-8" if t <= 8 else "9-16" if t <= 16 else "17+"
tvd_ttc = show("BARS TO SESSION CLOSE (the holding window)", ttcb,
               order=["0 (16:00)", "1-3", "4-8", "9-16", "17+"])
print(f"   mean bars-to-close: stand-down {mean([e['ttc'] for e in res]):.2f}  "
      f"control {mean([e['ttc'] for e in ctrl]):.2f}  "
      f"SMD {smd([e['ttc'] for e in res],[e['ttc'] for e in ctrl]):+.3f}")

pr = sum(1 for e in res if e["pivot"]) / len(res)
pc = sum(1 for e in ctrl if e["pivot"]) / len(ctrl)
print(f"\n-- PIVOT RATE   stand-down {pr:.1%}   control {pc:.1%}   ratio {pr/pc:.2f}")

# ---------- matched re-run ----------------------------------------------
print("\n" + "=" * 78)
print("[1b] MATCHED RE-RUN  --  post-stratified on (hour-of-day x ATR quartile)")
print("=" * 78)
print("Estimator: for each stand-down bar, the benchmark is the MEAN of every control")
print("bar in its own (hour, ATR-quartile) cell; z = mean(d)/SE(d) over the n paired")
print("differences. Cells with no control bar fall back to (hour) then (ATR quartile).")

def build_cells(keyfn):
    cells = defaultdict(list)
    for e in ctrl:
        cells[keyfn(e)].append(e)
    return cells

cell_ha = build_cells(lambda e: (e["hour"], aq(e)))
cell_h  = build_cells(lambda e: e["hour"])
cell_a  = build_cells(lambda e: aq(e))
cell_hat = build_cells(lambda e: (e["hour"], aq(e), ttcb(e)))

def matched(fn, keyfns):
    ds, fell = [], 0
    for e in res:
        pool = None
        for kf, cells in keyfns:
            p = cells.get(kf(e))
            if p and len(p) >= 2:
                pool = p; break
            fell += 1
        if pool is None:
            continue
        ds.append(fn(e) - mean([fn(x) for x in pool]))
    if len(ds) < 2:
        return None
    se = sd(ds) / math.sqrt(len(ds))
    return mean(ds), se, (mean(ds) / se if se else 0.0), len(ds)

specs = [
    ("unmatched (published)", None),
    ("matched: hour",         [(lambda e: e["hour"], cell_h)]),
    ("matched: ATR quartile", [(lambda e: aq(e), cell_a)]),
    ("matched: hour x ATRq",  [(lambda e: (e["hour"], aq(e)), cell_ha),
                               (lambda e: e["hour"], cell_h),
                               (lambda e: aq(e), cell_a)]),
    ("matched: hour x ATRq x bars-to-close",
                              [(lambda e: (e["hour"], aq(e), ttcb(e)), cell_hat),
                               (lambda e: (e["hour"], aq(e)), cell_ha),
                               (lambda e: e["hour"], cell_h),
                               (lambda e: aq(e), cell_a)]),
]
for lbl, fn in ARMS.items():
    print(f"\n  ARM: {lbl}")
    print(f"    {'design':<38} {'diff':>9} {'z':>7}  {'n':>4}")
    a = [fn(e) for e in res]; b = [fn(e) for e in ctrl]
    print(f"    {'unmatched (published)':<38} {mean(a)-mean(b):>+8.3f}R {welch(a,b):>+7.2f}  {len(a):>4}")
    for slbl, kfs in specs[1:]:
        m = matched(fn, kfs)
        if m:
            print(f"    {slbl:<38} {m[0]:>+8.3f}R {m[2]:>+7.2f}  {m[3]:>4}")

# pivot arm, matched
print("\n  ARM: pivot stand-downs, trade WITH the turn (published z +0.06)")
piv_res = [e for e in res if e["pivot"]]
piv_ctrl = [e for e in ctrl if e["pivot"]]
alig = lambda e: e["long"][0] if e["pivot"] == "LOW" else e["short"][0]
pa = [alig(e) for e in piv_res]; pb = [alig(e) for e in piv_ctrl]
print(f"    {'unmatched (published)':<38} {mean(pa)-mean(pb):>+8.3f}R {welch(pa,pb):>+7.2f}  {len(pa):>4}")
pcell_ha = defaultdict(list); pcell_h = defaultdict(list); pcell_a = defaultdict(list)
for e in piv_ctrl:
    pcell_ha[(e["hour"], aq(e))].append(e); pcell_h[e["hour"]].append(e); pcell_a[aq(e)].append(e)
ds = []
for e in piv_res:
    pool = pcell_ha.get((e["hour"], aq(e))) or pcell_h.get(e["hour"]) or pcell_a.get(aq(e))
    if pool and len(pool) >= 2:
        ds.append(alig(e) - mean([alig(x) for x in pool]))
if len(ds) >= 2:
    se = sd(ds) / math.sqrt(len(ds))
    print(f"    {'matched: hour x ATRq':<38} {mean(ds):>+8.3f}R {mean(ds)/se:>+7.2f}  {len(ds):>4}")

# how much does the SHAPE of the control alone move its own mean?
print("\n[1c] HOW MUCH CAN COMPOSITION ALONE MOVE THE CONTROL MEAN?")
print("     Reweighting the control to the stand-downs' (hour x ATRq) mix:")
w = Counter((e["hour"], aq(e)) for e in res)
tot = sum(w.values())
for lbl, fn in ARMS.items():
    num, den = 0.0, 0.0
    for k, cnt in w.items():
        pool = cell_ha.get(k) or cell_h.get(k[0]) or cell_a.get(k[1])
        if pool:
            num += (cnt / tot) * mean([fn(x) for x in pool]); den += cnt / tot
    rew = num / den if den else 0.0
    raw = mean([fn(e) for e in ctrl])
    print(f"    {lbl:<20} raw control {raw:>+7.3f}R   reweighted {rew:>+7.3f}R   "
          f"shift {rew-raw:>+7.3f}R")

# ================================================================ Q3 PARITY
print("\n" + "=" * 78)
print("[3] IS BAR-INDEX PARITY A COIN FLIP ON THIS TAPE?")
print("=" * 78)
ev_h = Counter(e["hour"] for e in ctrl if e["bar"] % 2 == 0)
od_h = Counter(e["hour"] for e in ctrl if e["bar"] % 2 == 1)
ne, no = sum(ev_h.values()), sum(od_h.values())
print(f"control bars: even {ne}  odd {no}")
print(f"{'hour':<6} {'even%':>8} {'odd%':>8} {'even n':>7} {'odd n':>7}")
worst = 0.0
for h in range(24):
    pe, po = ev_h[h] / ne, od_h[h] / no
    worst = max(worst, abs(pe - po))
    if ev_h[h] or od_h[h]:
        print(f"{h:<6} {pe:>7.1%} {po:>7.1%} {ev_h[h]:>7} {od_h[h]:>7}")
print(f"max |even%-odd%| across hours: {worst:.3f}   "
      f"TVD {0.5*sum(abs(ev_h[h]/ne - od_h[h]/no) for h in range(24)):.4f}")
for nm, fn in (("ATR", lambda e: e["atr"]), ("bars-to-close", lambda e: e["ttc"]),
               ("LONG R", lambda e: e["long"][0]), ("SHORT R", lambda e: e["short"][0]),
               ("bar return (c-o)/atr", lambda e: (rows[e["bar"]]["c"]-rows[e["bar"]]["o"])/e["atr"])):
    a = [fn(e) for e in ctrl if e["bar"] % 2 == 0]
    b = [fn(e) for e in ctrl if e["bar"] % 2 == 1]
    print(f"  {nm:<22} even {mean(a):>+8.3f}  odd {mean(b):>+8.3f}  "
          f"z {welch(a,b):>+6.2f}  SMD {smd(a,b):>+6.3f}")
# parity balance within the STAND-DOWN sample
sde, sdo = sum(1 for e in res if e["bar"] % 2 == 0), sum(1 for e in res if e["bar"] % 2 == 1)
print(f"\nstand-down sample parity split: even {sde} / odd {sdo} "
      f"(a fair flip on n={len(res)} has sd {0.5*math.sqrt(len(res)):.1f})")
print("  -> the flip arm's direction mix differs between sample and control:")
print(f"     sample  {sde/len(res):.1%} long-side / {sdo/len(res):.1%} short-side")
print(f"     control {ne/len(ctrl):.1%} long-side / {no/len(ctrl):.1%} short-side")
# true randomised flip, many seeds, for comparison
rng = random.Random(11)
zs = []
for s in range(400):
    r2 = random.Random(s)
    a = [(e["long"][0] if r2.random() < .5 else e["short"][0]) for e in res]
    b = [(e["long"][0] if r2.random() < .5 else e["short"][0]) for e in ctrl]
    zs.append(welch(a, b))
print(f"\n  400 genuinely-randomised flips: z mean {mean(zs):+.2f} sd {sd(zs):.2f} "
      f"range {min(zs):+.2f}..{max(zs):+.2f}   (parity flip gave {published['coin flip'][3]:+.2f})")

# ================================================================ Q2 LEVELS
print("\n" + "=" * 78)
print("[2] levels.py  --  IS THE RANDOM-PRICE-LINE CONTROL COMPARABLE?")
print("=" * 78)
K, LOOKBACK, TOL_ATR = 3, 300, 0.30

def latr(i, n=14):
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3: return None
    return sum(max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
               for p, c in zip(seg, seg[1:])) / (len(seg) - 1)

def levels_at(i, a):
    lo = max(K, i - LOOKBACK); piv = []
    for j in range(lo, i - K):
        seg = rows[j - K:j + K + 1]
        if rows[j]["h"] == max(r["h"] for r in seg): piv.append((rows[j]["h"], j))
        if rows[j]["l"] == min(r["l"] for r in seg): piv.append((rows[j]["l"], j))
    if not piv: return []
    piv.sort(); tol, out, cur = TOL_ATR * a, [], [piv[0]]
    def emit(cl):
        bars = sorted(b for _, b in cl); t, last = 1, bars[0]
        for b in bars[1:]:
            if b - last > 2 * K: t += 1; last = b
        return (sum(pp for pp, _ in cl) / len(cl), t)
    for p in piv[1:]:
        if p[0] - cur[-1][0] <= tol: cur.append(p)
        else: out.append(emit(cur)); cur = [p]
    out.append(emit(cur)); return out

rngL = random.Random(7)
real_pos, rand_pos, real_t, rand_t = [], [], [], []
real_per_bar, rand_per_bar = [], []
for i in range(LOOKBACK + K + 20, N - 2):
    a = latr(i - 1)
    if not a: continue
    seg = rows[max(0, i - LOOKBACK):i]
    lo, hi = min(r["l"] for r in seg), max(r["h"] for r in seg)
    lv = levels_at(i, a)
    real_per_bar.append(sum(1 for L, t in lv if t >= 2))
    for L, t in lv:
        real_t.append(t)
        if t >= 2 and hi > lo: real_pos.append((L - lo) / (hi - lo))
    rl = [(rngL.uniform(lo, hi), rngL.choice([2, 2, 3, 4])) for _ in range(12)]
    rand_per_bar.append(sum(1 for L, t in rl if t >= 2))
    for L, t in rl:
        rand_t.append(t)
        if hi > lo: rand_pos.append((L - lo) / (hi - lo))

def decile(v):
    c = Counter(min(9, int(x * 10)) for x in v); n = len(v)
    return [c[d] / n for d in range(10)]
dr, dc_ = decile(real_pos), decile(rand_pos)
print("\n-- (a) WHERE IN THE TRAILING 300-BAR RANGE THE LINE SITS")
print(f"{'decile':<12} {'real levels':>12} {'random lines':>13} {'ratio':>8}")
for d in range(10):
    print(f"{d/10:.1f}-{d/10+0.1:.1f}   {dr[d]:>11.1%} {dc_[d]:>12.1%} "
      f"{(dr[d]/dc_[d] if dc_[d] else float('inf')):>8.2f}")
print(f"TVD(real, random) over deciles = {0.5*sum(abs(dr[d]-dc_[d]) for d in range(10)):.3f}")
print(f"share in outer 20% of range: real {dr[0]+dr[9]:.1%}   random {dc_[0]+dc_[9]:.1%}")
print(f"mean |position - 0.5|: real {mean([abs(x-.5) for x in real_pos]):.3f}  "
      f"random {mean([abs(x-.5) for x in rand_pos]):.3f}")

print("\n-- (b) TOUCH COUNTS: earned vs fabricated")
cr, cc2 = Counter(real_t), Counter(rand_t)
nr, nc = len(real_t), len(rand_t)
print(f"{'touches':<10} {'real':>10} {'random':>10}")
for t in sorted(set(cr) | set(cc2)):
    print(f"{t:<10} {cr[t]/nr:>9.1%} {(cc2[t]/nc if nc else 0):>9.1%}")
print(f"real mean touches {mean(real_t):.2f} (max {max(real_t)}), "
      f"random mean {mean(rand_t):.2f} (max {max(rand_t)})")
print(f"real levels with touches>=2: {sum(1 for t in real_t if t>=2)/nr:.1%}   "
      f"random: {sum(1 for t in rand_t if t>=2)/nc:.1%}")
print(f"eligible (touches>=2) lines per bar: real {mean(real_per_bar):.2f}   "
      f"random {mean(rand_per_bar):.2f}")

print("\n-- (c) does a random line CO-LOCATE with a real level? (contamination check)")
hits = 0; tot2 = 0
rngL2 = random.Random(7)
for i in range(LOOKBACK + K + 20, N - 2, 7):
    a = latr(i - 1)
    if not a: continue
    seg = rows[max(0, i - LOOKBACK):i]
    lo, hi = min(r["l"] for r in seg), max(r["h"] for r in seg)
    lv = [L for L, t in levels_at(i, a) if t >= 2]
    for _ in range(12):
        x = rngL2.uniform(lo, hi); tot2 += 1
        if any(abs(x - L) <= 0.25 * a for L in lv): hits += 1
print(f"random lines landing within the 0.25-ATR test band of a REAL level: "
      f"{hits}/{tot2} = {hits/tot2:.1%}")

print("\ndone.")

# ===========================================================================
print("\n" + "=" * 78)
print("[1d] THE SPECIFIC WORRY: are the stand-downs an OVERNIGHT sample?")
print("=" * 78)
def sess(e):
    h = e["hour"]
    return "RTH 09-16" if 9 <= h <= 16 else "eve 18-23" if h >= 18 else "o/n 00-08"
for nm in ("o/n 00-08", "eve 18-23", "RTH 09-16"):
    ps = sum(1 for e in res if sess(e) == nm) / len(res)
    pc = sum(1 for e in ctrl if sess(e) == nm) / len(ctrl)
    print(f"  {nm:<12} stand-down {ps:>6.1%}   control {pc:>6.1%}   ratio {ps/pc:.2f}")
print("  -> the feared '60% overnight vs 25% control' is NOT what this sample is.")
print(f"  16:00 forbidden bars: stand-down {sum(1 for e in res if e['hour']==16)}/{len(res)}"
      f" = {sum(1 for e in res if e['hour']==16)/len(res):.1%}   "
      f"control {sum(1 for e in ctrl if e['hour']==16)/len(ctrl):.1%}")
h16 = [e for e in ctrl if e["hour"] == 16]
print(f"  a 16:00 bar's whole trade is ONE bar: control 16:00 bars return "
      f"long {mean([e['long'][0] for e in h16]):+.3f}R vs {mean([e['long'][0] for e in ctrl]):+.3f}R overall")

print("\n" + "=" * 78)
print("[3b] THE REAL PARITY PROBLEM: the SAMPLE's parity mix, not the tape's")
print("=" * 78)
sde = sum(1 for e in res if e["bar"] % 2 == 0)
p = 0.5; n = len(res)
zbin = (sde - n * p) / math.sqrt(n * p * (1 - p))
print(f"  stand-down bars: {sde} even / {n-sde} odd.  Binomial z vs 50/50 = {zbin:+.2f}")
print("  The flip arm therefore reads 69% LONG-side on the sample and 50% on the control.")
print(f"  On a tape where long {mean([e['long'][0] for e in ctrl]):+.3f}R and short "
      f"{mean([e['short'][0] for e in ctrl]):+.3f}R at an arbitrary bar, that mix alone shifts")
ctrl_flip_matched = (sde/n) * mean([e["long"][0] for e in ctrl]) + \
                    ((n-sde)/n) * mean([e["short"][0] for e in ctrl])
raw = mean([e["flip"] for e in ctrl])
a = [e["flip"] for e in res]
print(f"  the control's own flip mean from {raw:+.3f}R to {ctrl_flip_matched:+.3f}R "
      f"(shift {ctrl_flip_matched-raw:+.3f}R).")
se = (sd(a)**2/len(a) + sd([e['flip'] for e in ctrl])**2/len(ctrl))**0.5
print(f"  coin-flip arm published    diff {mean(a)-raw:+.3f}R   z {welch(a,[e['flip'] for e in ctrl]):+.2f}")
print(f"  coin-flip arm PARITY-MATCHED diff {mean(a)-ctrl_flip_matched:+.3f}R   "
      f"z {(mean(a)-ctrl_flip_matched)/se:+.2f}")

print("\n" + "=" * 78)
print("[1e] ARE THE SEs HONEST? overlap + self-inclusion")
print("=" * 78)
print("  (i) the stand-down bars are THEMSELVES members of the control population:")
resbars = set(e["bar"] for e in res)
ctrl_ex = [e for e in ctrl if e["bar"] not in resbars]
for lbl, fn in ARMS.items():
    a2 = [fn(e) for e in res]
    print(f"      {lbl:<20} z with sample in control {welch(a2,[fn(e) for e in ctrl]):+.2f}"
          f"   z with it removed {welch(a2,[fn(e) for e in ctrl_ex]):+.2f}")
print("\n  (ii) control bars share forward windows, so 1659 is not 1659 independent")
print("       observations. Lag-1 autocorrelation of the control's arm values:")
for lbl, fn in ARMS.items():
    v = [fn(e) for e in ctrl]
    m = mean(v); num = sum((v[i]-m)*(v[i+1]-m) for i in range(len(v)-1))
    den = sum((x-m)**2 for x in v)
    print(f"      {lbl:<20} rho1 {num/den:+.3f}")
print("\n  (iii) stationary block bootstrap of the always-LONG arm (block=24 bars,")
print("        2000 resamples of the CONTROL) - a z that respects the overlap:")
vals = [e["long"][0] for e in ctrl]
obs = mean([e["long"][0] for e in res]) - mean(vals)
rngb = random.Random(3); B, L = 2000, 24
boot = []
for _ in range(B):
    s = []
    while len(s) < len(res):
        st = rngb.randrange(len(vals) - L)
        s.extend(vals[st:st + L])
    boot.append(mean(s[:len(res)]))
bm, bs = mean(boot), sd(boot)
print(f"        observed stand-down mean {mean([e['long'][0] for e in res]):+.3f}R")
print(f"        block-bootstrap null: mean {bm:+.3f}R  sd {bs:.3f}")
print(f"        z = {(mean([e['long'][0] for e in res]) - bm)/bs:+.2f}   "
      f"(Welch as published: {published['always LONG'][3]:+.2f})")
pv = sum(1 for x in boot if x >= mean([e['long'][0] for e in res])) / B
print(f"        one-sided bootstrap p = {pv:.3f}")

print("\n" + "=" * 78)
print("[1f] THE RIGHT NULL: a CIRCULAR-SHIFT PLACEMENT TEST")
print("=" * 78)
bars = sorted(e["bar"] for e in res)
gaps = [b - a2 for a2, b in zip(bars, bars[1:])]
print(f"  stand-down bars span {bars[0]}..{bars[-1]}; gaps: min {min(gaps)} median "
      f"{sorted(gaps)[len(gaps)//2]} max {max(gaps)}; "
      f"{sum(1 for g in gaps if g < 24)} of {len(gaps)} gaps under one session")
print("  So the SAMPLE is mostly non-overlapping - the block bootstrap above was")
print("  over-conservative. The honest null keeps the sample's OWN spacing and")
print("  slides the whole pattern along the tape (preserving the tape's serial")
print("  dependence and, when the shift is a multiple of 23 bars, the hour mix).")
lo_b, hi_b = 20, N - 1
byb = {e["bar"]: e for e in ctrl}
def placement(fn, step=1, label=""):
    obs = mean([fn(e) for e in res])
    span = bars[-1] - bars[0]
    null = []
    for off in range(-(bars[0] - lo_b), (hi_b - bars[-1]) + 1, step):
        v = [byb[b + off] for b in bars if (b + off) in byb]
        if len(v) < len(bars) * 0.9:
            continue
        null.append(mean([fn(e) for e in v]))
    if len(null) < 20:
        return None
    m2, s2 = mean(null), sd(null)
    pv = sum(1 for x in null if x >= obs) / len(null)
    return obs, m2, s2, (obs - m2) / s2 if s2 else 0.0, pv, len(null)

print(f"\n  {'arm':<20} {'design':<28} {'diff':>8} {'z':>7} {'p(1-sided)':>11} {'placements':>11}")
for lbl, fn in ARMS.items():
    for step, dn in ((1, "shift: any offset"), (23, "shift: whole sessions (hour-matched)")):
        r2 = placement(fn, step)
        if r2:
            print(f"  {lbl:<20} {dn:<28} {r2[0]-r2[1]:>+7.3f}R {r2[3]:>+7.2f} {r2[4]:>11.3f} {r2[5]:>11}")
    a3 = [fn(e) for e in res]
    print(f"  {lbl:<20} {'(published Welch)':<28} "
          f"{mean(a3)-mean([fn(e) for e in ctrl]):>+7.3f}R "
          f"{welch(a3,[fn(e) for e in ctrl]):>+7.2f}")
    print()
