#!/usr/bin/env python3
"""E9 part 2: rebuild levels.py's control FAIRLY and see whether the one kept
finding survives.

levels.py's control draws 12 uniform lines per bar and hands each a touch count
from rng.choice([2,2,3,4]). Consequences measured in E9_controls.py:
  * 100% of control lines clear touches>=2; only 41.3% of real levels do.
  * the control has NO 1-touch line and none above 4 touches, yet NOTES.md
    compares real 1-touch levels (45.7% bounce, n=162) to that control (55.0%).
  * 12 lines/bar vs 9.78 real eligible lines/bar - the counts are not matched
    either, though the docstring claims "in the same count".
  * 20.9% of uniform lines land inside the 0.25-ATR test band of a REAL level,
    so a fifth of the control IS the treatment.

This script re-runs the study with four control variants, holding the test
procedure identical, and reports whether the published z moves:
  A  as published                       (uniform x [2,2,3,4], 12/bar)
  B  count-matched                      (same number of lines as real levels)
  C  touch-matched                      (touch counts resampled from the REAL
                                         level touch distribution, incl. 1s)
  D  fair                               (count- and touch-matched, decontaminated:
                                         lines within 0.25 ATR of a real level are
                                         redrawn)
Read-only; touches visible.jsonl only.
"""
import json, os, random, math
from collections import Counter, defaultdict

D = os.path.dirname(os.path.abspath(__file__))
R1 = os.path.dirname(D)
rows = [json.loads(l) for l in open(os.path.join(R1, "visible.jsonl"))]
N = len(rows)

K, LOOKBACK, TOL_ATR = 3, 300, 0.30
BAND_ATR, BREAK_ATR, BOUNCE_ATR = 0.25, 0.40, 0.40
HORIZON, STOP_ATR, RR, TICK = 24, 1.0, 2.0, 0.25

def atr(i, n=14):
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

def resolve(i, L, side, a):
    brk = L - side * BREAK_ATR * a; bnc = L + side * BOUNCE_ATR * a
    for j in range(i, min(i + HORIZON, N)):
        c = rows[j]["c"]
        if (side > 0 and c <= brk) or (side < 0 and c >= brk): return "BREAK"
        if (side > 0 and c >= bnc) or (side < 0 and c <= bnc): return "BOUNCE"
    return "NEITHER"

def sim(f, sgn, a):
    if f >= N: return None
    fill = rows[f]["o"] + sgn * TICK; S = STOP_ATR * a
    stop, targ = fill - sgn * S, fill + sgn * RR * S
    for j in range(f, min(f + HORIZON, N)):
        b = rows[j]
        if (b["l"] <= stop) if sgn > 0 else (b["h"] >= stop): return -1.0
        if (b["h"] >= targ) if sgn > 0 else (b["l"] <= targ): return RR
    return sgn * (rows[min(f + HORIZON, N) - 1]["c"] - fill) / S

# --- first pass: harvest the REAL level population (for matching targets) -----
BARS = list(range(LOOKBACK + K + 20, N - 2))
real_cache, real_touch_pool, real_pos_pool, n_real = {}, [], [], []
for i in BARS:
    a = atr(i - 1)
    if not a: continue
    lv = levels_at(i, a)
    real_cache[i] = (a, lv)
    seg = rows[max(0, i - LOOKBACK):i]
    lo, hi = min(r["l"] for r in seg), max(r["h"] for r in seg)
    for L, t in lv:
        real_touch_pool.append(t)
        if hi > lo: real_pos_pool.append((L - lo) / (hi - lo))
    n_real.append(len(lv))
print(f"real level population: {len(real_touch_pool)} level-instances over {len(real_cache)} bars"
      f"  ({sum(n_real)/len(n_real):.2f} per bar, all touch counts)")
print(f"touch distribution (real): "
      + "  ".join(f"{t}:{c/len(real_touch_pool):.1%}" for t, c in sorted(Counter(real_touch_pool).items())[:6])
      + f"  ... max {max(real_touch_pool)}")

MIN_T = 1   # include 1-touch so the kept finding HAS a control

def study(variant, seed=7):
    rng = random.Random(seed)
    ev = []; active = {}
    for i in BARS:
        if i not in real_cache: continue
        a, rlv = real_cache[i]
        seg = rows[max(0, i - LOOKBACK):i]
        lo, hi = min(r["l"] for r in seg), max(r["h"] for r in seg)
        if variant == "real":
            lv = rlv
        else:
            if variant == "A":
                lv = [(rng.uniform(lo, hi), rng.choice([2, 2, 3, 4])) for _ in range(12)]
            elif variant == "B":
                lv = [(rng.uniform(lo, hi), rng.choice([2, 2, 3, 4])) for _ in range(len(rlv))]
            elif variant == "C":
                lv = [(rng.uniform(lo, hi), rng.choice(real_touch_pool)) for _ in range(12)]
            elif variant == "D":
                lv = []
                for _ in range(len(rlv)):
                    for _try in range(25):
                        x = rng.uniform(lo, hi)
                        if not any(abs(x - L) <= BAND_ATR * a for L, _t in rlv):
                            break
                    lv.append((x, rng.choice(real_touch_pool)))
        band = BAND_ATR * a
        for L, touches in lv:
            if touches < MIN_T: continue
            key = round(L / max(band, 0.25))
            prev, cur = rows[i - 1]["c"], rows[i]["c"]
            if abs(cur - L) > band: continue
            if abs(prev - L) <= band: continue
            if i - active.get(key, -99) < HORIZON: continue
            active[key] = i
            side = 1 if prev > L else -1
            ev.append({"bar": i, "atr": a, "touches": touches, "side": side,
                       "outcome": resolve(i, L, side, a),
                       "bounce_r": sim(i + 1, side, a), "break_r": sim(i + 1, -side, a)})
    return ev

def rate(ev, pred=lambda e: True):
    s = [e for e in ev if pred(e)]
    if not s: return 0, 0.0
    return len(s), sum(1 for e in s if e["outcome"] == "BOUNCE") / len(s)

def zprop(p1, n1, p2, n2):
    if not n1 or not n2: return 0.0
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return (p1 - p2) / se if se else 0.0

def mean(v): return sum(v) / len(v) if v else 0.0
def sd(v):
    if len(v) < 2: return 0.0
    m = mean(v); return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5
def zc(a, b):
    if len(a) < 2 or len(b) < 2: return 0.0
    se = (sd(a)**2/len(a) + sd(b)**2/len(b))**0.5
    return (mean(a)-mean(b))/se if se else 0.0

real = study("real")
controls = {k: study(k) for k in ("A", "B", "C", "D")}
print(f"\nevent counts   real {len(real)}   " + "   ".join(f"{k} {len(v)}" for k, v in controls.items()))

print("\n" + "="*84)
print("THE KEPT FINDING: fresh single-touch swing extreme bounces LESS than control")
print("published: real 45.7% (n=162) vs control 55.0% (n=200), z ~ +1.76 (as a rate)")
print("="*84)
n1, p1 = rate(real, lambda e: e["touches"] == 1)
print(f"  real, touches==1                      n={n1:<5} bounce {p1:6.1%}")
LBL = {"A": "A  as published (uniform x [2,2,3,4], 12/bar)",
       "B": "B  count-matched to real levels",
       "C": "C  touch-matched (touches resampled from real)",
       "D": "D  FAIR: count+touch matched, decontaminated"}
print(f"\n  {'control variant':<46} {'n':>6} {'bounce':>8} {'diff':>8} {'z':>7}")
for k in ("A", "B", "C", "D"):
    ev = controls[k]
    # like-for-like: control lines carrying the SAME touch count as the claim
    n2, p2 = rate(ev, lambda e: e["touches"] == 1)
    n2p, p2p = rate(ev)                      # pooled control, as published
    print(f"  {LBL[k]:<46} {n2p:>6} {p2p:>7.1%} {p1-p2p:>+7.1%} {zprop(p1,n1,p2p,n2p):>+7.2f}   [pooled]")
    if n2 >= 10:
        print(f"  {'   ^ its 1-touch subset (the fair comparison)':<46} {n2:>6} {p2:>7.1%} "
              f"{p1-p2:>+7.1%} {zprop(p1,n1,p2,n2):>+7.2f}   <== LIKE FOR LIKE")

print("\n" + "="*84)
print("RETESTED (2+ touches), published 53.7% vs control 55.0% -> 'decoration'")
print("="*84)
n1b, p1b = rate(real, lambda e: e["touches"] >= 2)
print(f"  real, touches>=2                      n={n1b:<5} bounce {p1b:6.1%}")
for k in ("A", "B", "C", "D"):
    n2, p2 = rate(controls[k], lambda e: e["touches"] >= 2)
    print(f"  {LBL[k]:<46} {n2:>6} {p2:>7.1%} {p1b-p2:>+7.1%} {zprop(p1b,n1b,p2,n2):>+7.2f}")

print("\n" + "="*84)
print("TOUCH BUCKETS: which real buckets have ANY control counterpart?")
print("="*84)
print(f"  {'touches':<10} {'real n':>7} {'real bounce':>12} | " +
      "  ".join(f"{k}: n/bounce" for k in ("A", "D")))
for t in (1, 2, 3, 4, "5+"):
    pred = (lambda e, t=t: e["touches"] >= 5) if t == "5+" else (lambda e, t=t: e["touches"] == t)
    nr, pr = rate(real, pred)
    cells = []
    for k in ("A", "D"):
        nc, pc = rate(controls[k], pred)
        cells.append(f"{nc:>4}/{pc:5.1%}" if nc else f"{0:>4}/  n/a")
    print(f"  {str(t):<10} {nr:>7} {pr:>11.1%} | " + "   ".join(cells))

print("\n" + "="*84)
print("TRADE ARMS (published bounce z +0.08, break z +1.17)")
print("="*84)
rb = [e["bounce_r"] for e in real if e["bounce_r"] is not None]
rk = [e["break_r"] for e in real if e["break_r"] is not None]
print(f"  real   bounce {mean(rb):+.3f}R (n={len(rb)})   break {mean(rk):+.3f}R (n={len(rk)})")
for k in ("A", "B", "C", "D"):
    cb = [e["bounce_r"] for e in controls[k] if e["bounce_r"] is not None]
    ck = [e["break_r"] for e in controls[k] if e["break_r"] is not None]
    print(f"  {LBL[k]:<46} bounce {mean(rb)-mean(cb):+.3f}R z {zc(rb,cb):+.2f}   "
          f"break {mean(rk)-mean(ck):+.3f}R z {zc(rk,ck):+.2f}")

# ---------------------------------------------------------------------------
# ROBUSTNESS: variant D's bounce arm jumped to z +3.32. Before reporting that as
# a moved z, check it is not itself a composition artefact - the exact error this
# audit exists to catch. Two checks: (1) seed stability, (2) support/resistance
# mix, since "trade the bounce" is LONG at support and SHORT at resistance and
# this tape drifts up.
print("\n" + "="*84)
print("ROBUSTNESS OF VARIANT D (the only z that moved into significance)")
print("="*84)
def sidemix(ev):
    n = len(ev); return sum(1 for e in ev if e["side"] > 0) / n if n else 0
print(f"  support share (side=+1, bounce arm = LONG):  real {sidemix(real):.1%}   "
      + "   ".join(f"{k} {sidemix(v):.1%}" for k, v in controls.items()))
for k in ("A", "D"):
    ev = controls[k]
    for s, nm in ((1, "support"), (-1, "resistance")):
        sub = [e["bounce_r"] for e in ev if e["side"] == s and e["bounce_r"] is not None]
        rsub = [e["bounce_r"] for e in real if e["side"] == s and e["bounce_r"] is not None]
        print(f"    {k} {nm:<11} control {mean(sub):+.3f}R (n={len(sub):>3})   "
              f"real {mean(rsub):+.3f}R (n={len(rsub):>3})   diff {mean(rsub)-mean(sub):+.3f}R "
              f"z {zc(rsub,sub):+.2f}")
print("\n  side-MATCHED difference (average of the within-side differences, weighted")
print("  by the REAL side mix) - removes any support/resistance composition effect:")
for k in ("A", "B", "C", "D"):
    ev = controls[k]; num = 0.0; ok = True
    for s in (1, -1):
        w = sum(1 for e in real if e["side"] == s) / len(real)
        sub = [e["bounce_r"] for e in ev if e["side"] == s and e["bounce_r"] is not None]
        rsub = [e["bounce_r"] for e in real if e["side"] == s and e["bounce_r"] is not None]
        if len(sub) < 2: ok = False; break
        num += w * (mean(rsub) - mean(sub))
    print(f"    {k}  side-matched bounce diff {num:+.3f}R" if ok else f"    {k}  n/a")

print("\n  SEED STABILITY of variant D's bounce arm (10 seeds):")
zs, ds = [], []
for s in range(101, 111):
    ev = study("D", seed=s)
    cb = [e["bounce_r"] for e in ev if e["bounce_r"] is not None]
    zs.append(zc(rb, cb)); ds.append(mean(rb) - mean(cb))
print(f"    diff mean {mean(ds):+.3f}R  range {min(ds):+.3f}..{max(ds):+.3f}")
print(f"    z    mean {mean(zs):+.2f}   range {min(zs):+.2f}..{max(zs):+.2f}   sd {sd(zs):.2f}")
print("\n  and variant A's bounce arm over the same 10 seeds, for scale:")
zsA = []
for s in range(101, 111):
    ev = study("A", seed=s)
    cb = [e["bounce_r"] for e in ev if e["bounce_r"] is not None]
    zsA.append(zc(rb, cb))
print(f"    z    mean {mean(zsA):+.2f}   range {min(zsA):+.2f}..{max(zsA):+.2f}   sd {sd(zsA):.2f}")

print("\n  DECOMPOSITION - which single change to the control moves the bounce arm?")
for k, nm in (("A", "published"), ("B", "+count-match"), ("C", "+touch-match"), ("D", "+both+decontam")):
    cb = [e["bounce_r"] for e in controls[k] if e["bounce_r"] is not None]
    print(f"    {nm:<18} control bounce mean {mean(cb):+.3f}R (n={len(cb):>3})  "
          f"vs real {mean(rb):+.3f}R")

# ---------------------------------------------------------------------------
# ISOLATE the decontamination, and test whether variant D's events are drawn
# from a different REGIME than real level tests (momentum / ATR). If they are,
# D's +0.338R is a composition effect too and must not be reported as a result.
print("\n" + "="*84)
print("ISOLATING THE DECONTAMINATION, AND CHECKING D's EVENTS FOR REGIME DRIFT")
print("="*84)

def study2(mode, seed=7, tag=False):
    """mode: 'decon_only' = 12 lines, [2,2,3,4] touches, but decontaminated.
             'ct'         = count+touch matched, NOT decontaminated."""
    rng = random.Random(seed); ev = []; active = {}; contam = [0, 0]
    for i in BARS:
        if i not in real_cache: continue
        a, rlv = real_cache[i]
        seg = rows[max(0, i - LOOKBACK):i]
        lo, hi = min(r["l"] for r in seg), max(r["h"] for r in seg)
        nline = 12 if mode == "decon_only" else len(rlv)
        lv = []
        for _ in range(nline):
            if mode == "ct":
                x = rng.uniform(lo, hi)
            else:
                for _t in range(25):
                    x = rng.uniform(lo, hi)
                    if not any(abs(x - L) <= BAND_ATR * a for L, _u in rlv): break
            contam[0] += 1
            if any(abs(x - L) <= BAND_ATR * a for L, _u in rlv): contam[1] += 1
            t = rng.choice([2, 2, 3, 4]) if mode == "decon_only" else rng.choice(real_touch_pool)
            lv.append((x, t))
        band = BAND_ATR * a
        for L, touches in lv:
            if touches < MIN_T: continue
            key = round(L / max(band, 0.25))
            prev, cur = rows[i - 1]["c"], rows[i]["c"]
            if abs(cur - L) > band or abs(prev - L) <= band: continue
            if i - active.get(key, -99) < HORIZON: continue
            active[key] = i
            side = 1 if prev > L else -1
            ev.append({"bar": i, "atr": a, "touches": touches, "side": side,
                       "outcome": resolve(i, L, side, a),
                       "bounce_r": sim(i + 1, side, a), "break_r": sim(i + 1, -side, a)})
    return ev, contam

for mode, nm in (("decon_only", "decontamination ONLY (else as published)"),
                 ("ct", "count+touch matched, NOT decontaminated")):
    ev, contam = study2(mode)
    cb = [e["bounce_r"] for e in ev if e["bounce_r"] is not None]
    print(f"  {nm:<46} n={len(cb):>4}  bounce {mean(cb):+.3f}R  "
          f"diff {mean(rb)-mean(cb):+.3f}R  z {zc(rb,cb):+.2f}")
    print(f"     residual contamination after drawing: {contam[1]}/{contam[0]} = {contam[1]/contam[0]:.1%}")

# regime comparison at the EVENT bars
evD = controls["D"]; evA = controls["A"]
def bvel(e):
    b = rows[e["bar"]]; return abs(b["c"] - b["o"]) / e["atr"]
# real events need bar/atr recorded - rebuild quickly
realx, activex = [], {}
for i in BARS:
    if i not in real_cache: continue
    a, rlv = real_cache[i]; band = BAND_ATR * a
    for L, t in rlv:
        if t < MIN_T: continue
        key = round(L / max(band, 0.25)); prev, cur = rows[i-1]["c"], rows[i]["c"]
        if abs(cur - L) > band or abs(prev - L) <= band: continue
        if i - activex.get(key, -99) < HORIZON: continue
        activex[key] = i
        realx.append({"bar": i, "atr": a})
print(f"\n  regime at the EVENT bars (are we comparing like tape?)")
print(f"  {'population':<40} {'n':>5} {'mean ATR':>9} {'|c-o|/ATR':>11} {'mean bar idx':>13}")
for nm, ev in (("real level tests", realx), ("control A (published)", evA), ("control D (fair)", evD)):
    if not ev: continue
    hasv = [e for e in ev if "atr" in e and "bar" in e]
    print(f"  {nm:<40} {len(hasv):>5} {mean([e['atr'] for e in hasv]):>9.2f} "
          f"{mean([bvel(e) for e in hasv]):>11.3f} {mean([e['bar'] for e in hasv]):>13.0f}")
