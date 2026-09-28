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


def session_end(f):
    """Index of the 16:00 ET bar that closes the cycle containing bar f, or None
    if the cycle has not finished inside the visible tape."""
    for j in range(f, len(rows)):
        if rows[j]["ts"][11:13] == "16":
            return j
    return None


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
          f">=1.5R {hit(rs):5.1%}   vs control {mean(rs)-mean(ctrl_rs):+.3f}R  "
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
