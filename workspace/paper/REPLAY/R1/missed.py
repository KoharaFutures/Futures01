#!/usr/bin/env python3
"""Backtest every bar at which R1 took NO position, and price the opportunity cost.

Reads ONLY visible.jsonl and callouts.jsonl - both inside R1's own lane. It is a
RETROSPECTIVE measurement over bars the cursor has ALREADY passed, so it cannot
leak: every bar it touches was visible when it ran, and any stand-down whose
forward window is not yet fully visible is reported as PENDING and skipped.

WHAT IT MEASURES, and the honest framing (read this before quoting a number):

  For each stand-down it simulates the trade I did NOT take, in BOTH directions,
  under the engine's own rules (fill at the next bar's open plus one tick of
  slippage, stop wins a same-bar stop/target tie, flat at the 16:00 ET session
  close) with a 1.0-ATR stop and a 2R target. It reports the R each direction
  would have returned.

  THAT IS HINDSIGHT. "2R was available" is not "I should have caught it", because
  in any tape with drift a large share of ARBITRARY bars offer 2R in one
  direction or the other. So the register carries a CONTROL: the same simulation
  run at every eligible bar in the tape, not just the ones I stood down at. If my
  stand-down bars are no better than arbitrary bars, my stand-downs cost nothing
  specific and the opportunity-cost figure is an artefact of drift.

  The number that means something is the DIFFERENCE, and its sign.

TAXONOMY - three kinds of miss, which deserve different responses:
  ARMED      I had specified a trigger that fired and I was not there. A genuine
             process failure; the fix is cadence.
  REVERSAL   the bar sat at a local pivot and price then ran away from it. An
             opportunity my process never NAMED. The fix is a new detector, and
             only if it survives the control.
  UNNAMED    a move no rule of mine addresses. Not a miss - just the market.
"""
import json, os, sys
from datetime import datetime

D = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(D, "visible.jsonl"))]
calls = [json.loads(l) for l in open(os.path.join(D, "callouts.jsonl"))]

TICK, STOP_ATR, RR, PIVOT_K = 0.25, 1.0, 2.0, 3


def atr(i, n=14):
    """ATR over the n bars ending at index i. Uses only bars <= i."""
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3:
        return None
    trs = [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
           for p, c in zip(seg, seg[1:])]
    return sum(trs) / len(trs)


# NEXT-18:00 INDEX, built once. The 18:00 ET bar starts each daily cycle, so the bar
# BEFORE the next 18:00 is where that cycle ends, whatever hour it happens to be.
_next18 = [None] * len(rows)
_nxt = None
for _i in range(len(rows) - 1, -1, -1):
    _next18[_i] = _nxt
    if rows[_i]["ts"][11:13] == "18":
        _nxt = _i


def session_end(f):
    """Last bar of the 18:00->16:00 cycle containing bar f, or None if that cycle has
    not finished inside the visible tape.

    FIXED (burst 25). This used to scan forward for the first bar whose hour is "16".
    On a normal day that IS the cycle end and the two agree. But 67 of the tape's 355
    ET dates have NO 16:00 bar, and four of them are half-day sessions that trade
    09:30-12:30 and close early (2024-11-29, 2024-12-24, 2025-07-03, 2025-11-28), with
    more around holidays (2025-01-09, 2025-05-26, 2025-06-19, 2025-07-04, 2025-07-27).
    On those the old scan ran past the early close and returned a LATER day's 16:00, so
    the counterfactual held the position across a session boundary and through an
    overnight gap - up to 32 bars instead of 9 - while the report claimed "flat at the
    session close". Measured reach: 236 of 6,680 eligible bars (3.5%) and 2 of 56
    stand-downs (bars 874 and 1343). Both arms were affected at similar rates, which is
    why the published z-values moved little, but "the error was small" is a measurement
    and not a defence: the instrument was not doing what its own docstring said.

    NOTE ON SCOPE: this fixes MY counterfactual only. Whether the harness itself has the
    same half-day blind spot I cannot check - reading its source is outside this desk's
    reading whitelist - so it is flagged for the owner rather than assumed either way."""
    n = _next18[f]
    if n is None:
        return None
    return n - 1 if n - 1 >= f else None


def simulate(f, side, S):
    """The trade not taken. Engine rules: fill at bar f's open +/- one tick,
    stop wins a same-bar tie, flat at the session close."""
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
        hit_stop = b["l"] <= stop if sgn > 0 else b["h"] >= stop
        hit_targ = b["h"] >= targ if sgn > 0 else b["l"] <= targ
        if hit_stop:                       # stop wins the tie, per engine.py
            return -1.0, mfe / S, j, "STOP"
        if hit_targ:
            return RR, mfe / S, j, "TARGET"
    exit_c = rows[end]["c"]
    return sgn * (exit_c - fill) / S, mfe / S, end, "SESSION_CLOSE"


def is_pivot(f, tol=1):
    """Did bar f sit AT OR BESIDE a local extreme? Returns 'LOW', 'HIGH' or None.
    A +/-PIVOT_K window whose extreme falls within `tol` bars of f counts, because
    standing one bar off the turn is the same missed reversal as standing on it -
    which is the case the account owner specifically asked to be tracked."""
    a, b = f - PIVOT_K, f + PIVOT_K
    if a < 0 or b >= len(rows):
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
    """Best available R at bar f, both directions, plus the pivot tag."""
    # STOP_ATR WAS A DEAD CONSTANT (found by agent A, burst 12). It was declared,
    # PRINTED in the report header as "1.0 ATR stop", and never read - the stop was
    # bare ATR. The published numbers were right only because STOP_ATR happened to
    # be 1.0; setting it to 0.5 would have relabelled the header and changed nothing
    # in the arithmetic. A label that lies while the number stays right is the exact
    # defect family DEFECTS.md keeps cataloguing, so it is fixed here, not papered over.
    a = atr(f - 1)                          # ATR known at the DECISION bar
    if a is None:
        return None
    S = STOP_ATR * a
    L, Sh = simulate(f, "LONG", S), simulate(f, "SHORT", S)
    if L is None or Sh is None:
        return None
    return {"bar": f, "atr": a, "stop_pts": S, "long": L, "short": Sh, "pivot": is_pivot(f),
            "best": max(L[0], Sh[0]), "best_side": "LONG" if L[0] >= Sh[0] else "SHORT"}


# ---- the stand-downs -------------------------------------------------------
stand = [c for c in calls if c.get("confidence") == "NO_TRADE"]
res, pending = [], 0
for c in stand:
    f = c["visible_bars"]                    # the bar a fill would have landed on
    if f >= len(rows) or session_end(f) is None:
        pending += 1
        continue
    e = evaluate(f)
    if e:
        res.append((c, e))

# ---- the control: every eligible bar in the tape ---------------------------
ctrl = []
for f in range(20, len(rows)):
    if session_end(f) is None:
        continue
    e = evaluate(f)
    if e:
        ctrl.append(e)

mean = lambda v: sum(v) / len(v) if v else 0.0


def sd(v):
    if len(v) < 2:
        return 0.0
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def welch(a, b):
    """Two-sample z on the difference of means. Not a licence to call anything
    significant - it is here so the size of the difference can be read against
    its own noise instead of eyeballed."""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    se = (sd(a) ** 2 / len(a) + sd(b) ** 2 / len(b)) ** 0.5
    return (mean(a) - mean(b)) / se if se > 0 else 0.0


def arm(rs, label, ctrl_rs):
    hit = lambda v, t=1.5: sum(1 for x in v if x >= t) / len(v) if v else 0.0
    print(f"  {label:<26} n={len(rs):<5} mean {mean(rs):+.3f}R  sd {sd(rs):.2f}  "
          f">=1.5R {hit(rs):5.1%}   minus all-bar ctrl {mean(rs)-mean(ctrl_rs):+.3f}R  "
          f"z {welch(rs, ctrl_rs):+.2f}")


sd_long = [e["long"][0] for c, e in res]
sd_short = [e["short"][0] for c, e in res]
ct_long = [e["long"][0] for e in ctrl]
ct_short = [e["short"][0] for e in ctrl]
# coin-flip arm: direction fixed by a deterministic parity of the BAR INDEX, so it
# is chosen WITHOUT reference to the outcome - the placebo logic applied here.
#   FIXED (agent A, burst 12): the control used to key on enumerate() LIST POSITION
#   while the sample keyed on bar index. Equal in expectation on a symmetric sample,
#   so the published figures did not move - but they were not the same statistic, and
#   a control indexed by its own position in a list is not indexed by anything real.
sd_flip = [(e["long"][0] if e["bar"] % 2 == 0 else e["short"][0]) for c, e in res]
ct_flip = [(e["long"][0] if e["bar"] % 2 == 0 else e["short"][0]) for e in ctrl]
sd_best = [e["best"] for c, e in res]
ct_best = [e["best"] for e in ctrl]

print(f"R1 missed-opportunity register   visible {len(rows)} bars   "
      f"stand-downs {len(stand)} ({len(res)} scored, {pending} pending)")
print(f"geometry: {STOP_ATR} ATR stop, {RR}R target, engine fill/tie/session rules")

print("\nMY STAND-DOWN BARS, by how the direction was chosen:")
arm(sd_long, "always LONG", ct_long)
arm(sd_short, "always SHORT", ct_short)
arm(sd_flip, "coin flip (bar parity)", ct_flip)
arm(sd_best, "BEST of both (HINDSIGHT)", ct_best)

print("\nCONTROL, the same four arms at EVERY eligible bar in the tape:")
for lbl, v in (("always LONG", ct_long), ("always SHORT", ct_short),
               ("coin flip (bar parity)", ct_flip), ("BEST of both (HINDSIGHT)", ct_best)):
    hit = sum(1 for x in v if x >= 1.5) / len(v) if v else 0
    print(f"  {lbl:<26} n={len(v):<5} mean {mean(v):+.3f}R  sd {sd(v):.2f}  >=1.5R {hit:5.1%}")

print("""
  NOTE ON THE COLUMN ABOVE, and a correction. The figure after each sample arm is
  the DIFFERENCE sample-minus-control, not the control's mean. It used to print as
  "vs control X", and in bursts 15, 16 and 17 this desk read X as the control's own
  mean and wrote three times that "the control exceeds the sample". The opposite was
  true: the sample exceeded the control by X. The label is now unambiguous. The error
  ran AGAINST me - it reported my stand-downs as worse than random when they measured
  better - which is worth saying plainly, because an error that flatters nobody is
  still an error and I found it by re-reading my own print statement, not by insight.
""")

# ---- WINDOW-MATCHED control (burst 18) -------------------------------------
# WHY THIS EXISTS. The all-bar control answers "how did this arm do on the average
# bar of the whole tape?". My stand-downs are not spread evenly over the tape, so a
# gap against that control can be nothing but period composition: if I happened to
# decline mostly in stretches where buying paid, an always-long arm at my bars beats
# the all-bar mean with no judgement involved. This control asks the narrower and
# harder question - on the average ELIGIBLE BAR NEAR each of my stand-downs, how did
# the same arm do? It is paired: one control number per stand-down, from that
# stand-down's own neighbourhood. If the gap survives this, composition does not
# explain it. If it collapses, the all-bar gap was a calendar artefact.
WIN = 120
ctrl_by_bar = {e["bar"]: e for e in ctrl}
ctrl_bars = sorted(ctrl_by_bar)


def paired_local(pick):
    """(sample values, local-control values) aligned one-to-one by stand-down."""
    sv, cv = [], []
    for c, e in res:
        b = e["bar"]
        vals = [pick(ctrl_by_bar[x]) for x in ctrl_bars
                if x != b and abs(x - b) <= WIN]
        if not vals:
            continue
        sv.append(pick(e))
        cv.append(sum(vals) / len(vals))
    return sv, cv


PICKS = [
    ("always LONG", lambda e: e["long"][0]),
    ("always SHORT", lambda e: e["short"][0]),
    ("coin flip (bar parity)", lambda e: e["long"][0] if e["bar"] % 2 == 0 else e["short"][0]),
    ("BEST of both (HINDSIGHT)", lambda e: e["best"]),
]

print(f"\nWINDOW-MATCHED CONTROL (+/-{WIN} bars, paired, excludes the stand-down bar):")
print("  does the all-bar gap survive being compared against LOCAL tape instead?")
for lbl, pick in PICKS:
    sv, cv = paired_local(pick)
    d = [a - b for a, b in zip(sv, cv)]
    m, s_ = mean(d), sd(d)
    z = m / (s_ / len(d) ** 0.5) if len(d) > 1 and s_ > 0 else 0.0
    print(f"  {lbl:<26} n={len(d):<5} sample {mean(sv):+.3f}R  local ctrl {mean(cv):+.3f}R  "
          f"paired gap {m:+.3f}R  z {z:+.2f}")
print("  A paired z here is not comparable to the all-bar z: the paired test has the "
      "\n  period effect removed, so it is the stricter of the two.")

# ---- ATR-MATCHED all-bar control (burst 18) --------------------------------
# WHY. R is normalised by ATR (the stop IS one ATR), so a fixed point move is worth
# more R on a quiet bar than a loud one. Measured at bar 4050: my stand-down bars
# average ATR 13.18 against 18.26 for all bars, sitting at the 38th percentile of the
# tape's own ATR distribution. That is a large composition difference, and it biases
# every R-denominated arm in a tape that drifts upward. So the all-bar control is
# re-weighted onto the sample's own ATR mix before being compared. This does not fix
# the sample; it stops the control from being a different population.
def bar_atr(i, n=14):
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3:
        return None
    trs = [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
           for p, c in zip(seg, seg[1:])]
    return max(sum(trs) / len(trs), 0.5)


s_atr = [bar_atr(e["bar"] - 1) for c, e in res]
cuts = sorted(x for x in s_atr if x)
Q = [cuts[int(f * (len(cuts) - 1))] for f in (0.25, 0.50, 0.75)]
bucket = lambda a: 0 if a <= Q[0] else 1 if a <= Q[1] else 2 if a <= Q[2] else 3

s_w = [0, 0, 0, 0]
for a in s_atr:
    if a:
        s_w[bucket(a)] += 1
tot = sum(s_w) or 1

c_buckets = [[] for _ in range(4)]
for e in ctrl:
    a = bar_atr(e["bar"] - 1)
    if a:
        c_buckets[bucket(a)].append(e)

print(f"\nATR-MATCHED ALL-BAR CONTROL (post-stratified on the sample's own ATR mix)")
print(f"  sample ATR quartile cuts {Q[0]:.2f} / {Q[1]:.2f} / {Q[2]:.2f}   "
      f"control bars per bucket {[len(b) for b in c_buckets]}")
for lbl, pick in PICKS:
    sv = [pick(e) for c, e in res]
    num = den = 0.0
    for k in range(4):
        if c_buckets[k] and s_w[k]:
            num += (s_w[k] / tot) * mean([pick(e) for e in c_buckets[k]])
            den += s_w[k] / tot
    cm = num / den if den else 0.0
    # se of the weighted control mean, plus the sample's own se
    var = 0.0
    for k in range(4):
        if len(c_buckets[k]) > 1 and s_w[k]:
            var += (s_w[k] / tot) ** 2 * sd([pick(e) for e in c_buckets[k]]) ** 2 / len(c_buckets[k])
    se = (sd(sv) ** 2 / len(sv) + var) ** 0.5
    z = (mean(sv) - cm) / se if se > 0 else 0.0
    print(f"  {lbl:<26} n={len(sv):<5} sample {mean(sv):+.3f}R  ATR-matched ctrl {cm:+.3f}R  "
          f"gap {mean(sv) - cm:+.3f}R  z {z:+.2f}")

# ---- DRIFT-REMOVED ARM (burst 20) ------------------------------------------
# WHY. Bursts 18 and 19 both found the always-LONG arm at my stand-downs running
# ~+0.3R above control and surviving an ATR match and a local-window match. The one
# explanation those controls cannot rule out is DRIFT: this tape rose 218.8 points
# over its first 4050 bars, and a long arm in a rising market beats a mixed control
# without any judgement being involved. So this arm removes the drift from the
# forward path and re-runs the identical barrier test.
#
# HOW, and why it is not look-ahead. The drift estimate mu is the mean close-to-close
# over the DRIFT_W bars ENDING AT THE DECISION BAR - strictly past data, the same
# information the ATR stop already uses. Each forward bar j is then shifted by
# -mu*(j-f): the fill is untouched (j=f), and the path is tilted back to flat. If the
# long-arm gap is drift, it collapses here. If it survives, drift is not the story.
#
# SYMMETRY CHECK, built in: de-drifting must hurt the long arm and help the short arm
# by a similar amount. If both move the same way, the adjustment is broken, not the
# finding - so both are printed.
DRIFT_W = 120


def local_mu(f):
    """Mean close-to-close over the DRIFT_W bars ending at the decision bar f-1."""
    a = max(1, f - DRIFT_W)
    if f - 1 <= a:
        return None
    ch = [rows[i]["c"] - rows[i - 1]["c"] for i in range(a, f)]
    return sum(ch) / len(ch) if ch else None


def simulate_dd(f, side, S, mu):
    """simulate(), with the forward path tilted back to zero drift."""
    end = session_end(f)
    if end is None or S is None or S <= 0 or mu is None:
        return None
    sgn = 1 if side == "LONG" else -1
    fill = rows[f]["o"] + sgn * TICK
    stop, targ = fill - sgn * S, fill + sgn * RR * S
    for j in range(f, end + 1):
        b, d = rows[j], mu * (j - f)
        h, l, c = b["h"] - d, b["l"] - d, b["c"] - d
        hit_stop = l <= stop if sgn > 0 else h >= stop
        hit_targ = h >= targ if sgn > 0 else l <= targ
        if hit_stop:
            return -1.0
        if hit_targ:
            return RR
    return sgn * (rows[end]["c"] - mu * (end - f) - fill) / S


def dd_arm(bars):
    """(long R's, short R's) on de-drifted paths for the given fill bars."""
    lo, sh = [], []
    for f in bars:
        a = atr(f - 1)
        mu = local_mu(f)
        if a is None or mu is None:
            continue
        L = simulate_dd(f, "LONG", STOP_ATR * a, mu)
        Sx = simulate_dd(f, "SHORT", STOP_ATR * a, mu)
        if L is None or Sx is None:
            continue
        lo.append(L); sh.append(Sx)
    return lo, sh


sd_bars = [e["bar"] for c, e in res]
ct_bars = [e["bar"] for e in ctrl]
s_L, s_S = dd_arm(sd_bars)
c_L, c_S = dd_arm(ct_bars)

# VALIDITY TEST, RUN BEFORE THE ARM IS ALLOWED TO PRINT A NUMBER.
# The arm only removes forward drift if the prior-window estimate PREDICTS forward
# drift. Measured on this tape: corr(prior-120-bar drift, next-24-bar realised drift)
# = -0.093, R^2 0.86% - and NEGATIVE. So mu is very nearly uncorrelated with what the
# path actually does, and subtracting it adds a noise term (sd 1.22 pts/bar) to a
# forward drift whose own sd is 3.12. THE ARM DOES NOT DO WHAT IT WAS BUILT TO DO.
# It is kept, printed, and labelled INVALID rather than deleted, because it produced
# this desk's first honest-arm |z| above 2 (+2.08) and a deleted instrument is one a
# later burst rebuilds and believes.
def _drift_validity(W=DRIFT_W, H=24):
    xs, ys = [], []
    for f in range(W + 2, len(rows) - H):
        m = local_mu(f)
        if m is None:
            continue
        xs.append(m); ys.append((rows[f + H]["c"] - rows[f]["c"]) / H)
    n = len(xs); mx, my = mean(xs), mean(ys)
    sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    sxx = sum((a - mx) ** 2 for a in xs); syy = sum((b - my) ** 2 for b in ys)
    r = sxy / (sxx * syy) ** 0.5 if sxx and syy else 0.0
    return n, r


_n_v, _r_v = _drift_validity()
print(f"\nDRIFT-REMOVED ARM  ***INVALID - DO NOT QUOTE THE z BELOW***")
print(f"  validity test: corr(prior-{DRIFT_W}-bar drift, next-24-bar realised drift) = {_r_v:+.4f} "
      f"(R2 {_r_v * _r_v:.2%}, n={_n_v}, sign NEGATIVE)")
print(f"  -> the estimate explains under 1% of forward drift, so this arm subtracts NOISE,")
print(f"     not trend. Its numbers do not test what they were built to test.")
print(f"  (the arm's own correlation t looks large only because the windows overlap;")
print(f"   ~24-bar blocks cut the effective n by about 24x and the t with it.)")
print(f"  shown for the record, path tilted using the {DRIFT_W} bars BEFORE the decision:")
mu_all = [local_mu(f) for f in sd_bars]
mu_all = [m for m in mu_all if m is not None]
print(f"  mean local drift at my stand-downs {mean(mu_all):+.4f} pts/bar "
      f"(tape-wide {sum(rows[i]['c'] - rows[i-1]['c'] for i in range(1, len(rows))) / (len(rows) - 1):+.4f})")
for lbl, sv, cv in (("always LONG", s_L, c_L), ("always SHORT", s_S, c_S)):
    print(f"  {lbl:<26} n={len(sv):<5} sample {mean(sv):+.3f}R  ctrl {mean(cv):+.3f}R  "
          f"gap {mean(sv) - mean(cv):+.3f}R  z {welch(sv, cv):+.2f}")
print("  SYMMETRY: de-drifting must push the long and short arms in OPPOSITE directions.")
print(f"    long arm moved  {mean(s_L) - mean([e['long'][0] for c, e in res]):+.3f}R   "
      f"short arm moved {mean(s_S) - mean([e['short'][0] for c, e in res]):+.3f}R   "
      "(same sign = the adjustment is broken, not the finding)")

print("""
READ THE 'BEST of both' ROW AS AN ARTEFACT, NOT A RESULT. Picking the direction
after seeing the outcome makes a 2R target with a 1-ATR stop reachable at most
bars: the control shows it at over half of ALL bars in the tape. The arms that
mean anything are the ones whose direction is fixed without hindsight - always
long, always short, and the coin flip. If my stand-down bars do not beat the
control on THOSE, then 'I missed 2R' is drift and direction-picking, not
judgement.""")

both_lose = [(c, e) for c, e in res if e["best"] <= -1.0]
print(f"\nSTAND-DOWNS WHERE BOTH DIRECTIONS WOULD HAVE LOST: {len(both_lose)} of {len(res)} "
      f"({len(both_lose)/len(res):.0%}) - unambiguously correct refusals.")
for c, e in both_lose:
    print(f"    bar {c['visible_bars']:>5}  {rows[c['visible_bars']]['ts'][:16]}  "
          f"long {e['long'][0]:+.2f}R  short {e['short'][0]:+.2f}R")

piv = [(c, e) for c, e in res if e["pivot"]]
print(f"\nLOCAL REVERSALS - stand-downs at or beside a {2*PIVOT_K+1}-bar pivot: "
      f"{len(piv)} of {len(res)}")
for c, e in sorted(piv, key=lambda x: -x[1]["best"]):
    f = c["visible_bars"]
    aligned = e["long"][0] if e["pivot"] == "LOW" else e["short"][0]
    print(f"    bar {f:>5}  {rows[f]['ts'][:16]}  pivot {e['pivot']:<4}  "
          f"trade-with-the-turn {aligned:+.2f}R   (best either way {e['best']:+.2f}R)")
piv_al = [(e["long"][0] if e["pivot"] == "LOW" else e["short"][0]) for c, e in piv]
ct_piv = [(e["long"][0] if e["pivot"] == "LOW" else e["short"][0]) for e in ctrl if e["pivot"]]
if piv_al:
    print(f"    trading WITH the turn at my pivot stand-downs: mean {mean(piv_al):+.3f}R "
          f"(n={len(piv_al)})   control at all pivots {mean(ct_piv):+.3f}R (n={len(ct_piv)})  "
          f"z {welch(piv_al, ct_piv):+.2f}")

ARMED = {414, 429, 607, 612, 1515, 1535, 1538, 1502}   # from NOTES.md, by fill bar
print("PER STAND-DOWN (worst first by forgone R):")
print(f"{'bar':>6} {'ts':<17} {'best':>7} {'side':<6} {'exit':<14} {'MFE':>6} {'pivot':<6} kind")
for c, e in sorted(res, key=lambda x: -x[1]["best"]):
    f = c["visible_bars"]
    r, mfe, _, why = e["long"] if e["best_side"] == "LONG" else e["short"]
    kind = "ARMED" if f in ARMED else ("REVERSAL" if e["pivot"] and e["best"] >= 1.5 else
                                       ("UNNAMED" if e["best"] >= 1.5 else "-"))
    print(f"{f:>6} {rows[f]['ts'][:16]:<17} {e['best']:>+7.2f} {e['best_side']:<6} "
          f"{why:<14} {mfe:>6.2f} {str(e['pivot'] or '-'):<6} {kind}")

with open(os.path.join(D, "missed.jsonl"), "w") as fh:
    for c, e in res:
        f = c["visible_bars"]
        r, mfe, xj, why = e["long"] if e["best_side"] == "LONG" else e["short"]
        fh.write(json.dumps({
            "callout_id": c["callout_id"], "fill_bar": f, "ts": rows[f]["ts"],
            "atr": round(e["atr"], 2), "best_r": round(e["best"], 3),
            "best_side": e["best_side"], "exit_reason": why, "mfe_r": round(mfe, 2),
            "long_r": round(e["long"][0], 3), "short_r": round(e["short"][0], 3),
            "pivot": e["pivot"],
            "kind": ("ARMED" if f in ARMED else
                     "REVERSAL" if e["pivot"] and e["best"] >= 1.5 else
                     "UNNAMED" if e["best"] >= 1.5 else "NONE"),
        }) + "\n")
print(f"\nwrote missed.jsonl ({len(res)} rows)")
