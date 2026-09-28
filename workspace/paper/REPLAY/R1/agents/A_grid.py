#!/usr/bin/env python3
"""A_grid.py - geometry sweep of the missed-opportunity null.

AGENT A, REPLAY desk, closed-market window. Does NOT modify missed.py.

WHAT THIS IS FOR
  missed.py reports that R1's ~42 stand-downs are indistinguishable from
  arbitrary bars: on a 1.0-ATR stop with a 2R target, all three HONEST
  direction arms (always-long, always-short, coin-flip by bar parity) sit at
  |z| < 1 against a control run at every eligible bar. That null is the desk's
  headline conclusion, and it was measured at ONE geometry. This script asks
  whether the null is a property of the stand-downs or a property of that cell,
  by sweeping 4 stops x 3 targets = 12 cells.

CONVENTIONS - copied from missed.py verbatim so the numbers are comparable:
  - fill at the next bar's open plus one tick of slippage (TICK = 0.25)
  - stop WINS a same-bar stop/target tie
  - flat at the session close (the first 16:00 ET bar at or after the fill)
  - ATR14 from bars at or before the DECISION bar, i.e. atr(f-1)
  - any stand-down whose forward window is not fully inside the visible tape
    is PENDING and skipped
  - control = the same simulation at every eligible bar, range(20, len(rows))
  - reads ONLY visible.jsonl and callouts.jsonl, both inside R1's own lane;
    retrospective over bars the cursor has already passed, so it cannot leak

WHY IT RE-IMPLEMENTS RATHER THAN IMPORTS missed.py
  missed.py does all of its work at module scope: importing it runs the whole
  register, prints it, and REWRITES missed.jsonl. Importing it 12 times would
  clobber another agent's output file. The simulate/atr/session_end/sd/welch
  bodies below are byte-for-byte the same logic, with the two geometry numbers
  lifted out of the globals into arguments. Cell (1.0, 2.0) is asserted against
  missed.py's published figures at the bottom of the run as a cross-check.

DEFECT FOUND IN missed.py, RECORDED NOT FIXED (see A_geometry.md, "Bugs")
  missed.py defines STOP_ATR = 1.0 at line 41 and never reads it. simulate()
  uses the raw ATR as the stop distance. The published results are correct only
  because 1.0 x ATR == ATR; anyone who edited STOP_ATR expecting the stop to
  move would have got the 1.0-ATR answer back silently. This script therefore
  takes stop distance as S = stop_mult * atr(f-1) explicitly, which reduces to
  missed.py at stop_mult = 1.0.

HINDSIGHT DISCIPLINE
  The "best of both directions" arm is computed but printed only under a
  HINDSIGHT label and is excluded from every verdict and from the
  multiple-testing count. Picking the side after the outcome makes a 2R target
  reachable at most bars; it is an artefact, not a result.
"""
import json, math, os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = [json.loads(l) for l in open(os.path.join(D, "visible.jsonl"))]
calls = [json.loads(l) for l in open(os.path.join(D, "callouts.jsonl"))]

TICK = 0.25

# the 12-cell grid the desk asked for
STOPS = [0.5, 0.75, 1.0, 1.5]
TARGETS = [1.5, 2.0, 3.0]
# off-grid diagnostic ONLY, for the "sub-0.5-ATR stops are noise" question.
# Not part of the 12 cells and not counted in n_trials for the free threshold.
DIAG_STOPS = [0.25]


# ---- engine mechanics, lifted from missed.py -------------------------------
def atr(i, n=14):
    """ATR over the n bars ending at index i. Uses only bars <= i."""
    seg = rows[max(0, i - n):i + 1]
    if len(seg) < 3:
        return None
    trs = [max(c["h"] - c["l"], abs(c["h"] - p["c"]), abs(c["l"] - p["c"]))
           for p, c in zip(seg, seg[1:])]
    return sum(trs) / len(trs)


_send = {}


def session_end(f):
    """Index of the 16:00 ET bar that closes the cycle containing bar f, or None
    if the cycle has not finished inside the visible tape."""
    if f in _send:
        return _send[f]
    out = None
    for j in range(f, len(rows)):
        if rows[j]["ts"][11:13] == "16":
            out = j
            break
    _send[f] = out
    return out


def simulate(f, side, S, rr):
    """The trade not taken, at stop distance S (price points) and target rr*S.
    Engine rules: fill at bar f's open +/- one tick, stop wins a same-bar tie,
    flat at the session close."""
    end = session_end(f)
    if end is None or S is None or S <= 0:
        return None
    sgn = 1 if side == "LONG" else -1
    fill = rows[f]["o"] + sgn * TICK
    stop, targ = fill - sgn * S, fill + sgn * rr * S
    mfe = 0.0
    for j in range(f, end + 1):
        b = rows[j]
        mfe = max(mfe, sgn * (b["h"] - fill) if sgn > 0 else sgn * (b["l"] - fill))
        hit_stop = b["l"] <= stop if sgn > 0 else b["h"] >= stop
        hit_targ = b["h"] >= targ if sgn > 0 else b["l"] <= targ
        if hit_stop:                       # stop wins the tie, per engine.py
            return -1.0, mfe / S, j, "STOP"
        if hit_targ:
            return rr, mfe / S, j, "TARGET"
    exit_c = rows[end]["c"]
    return sgn * (exit_c - fill) / S, mfe / S, end, "SESSION_CLOSE"


# ATR is geometry-independent, so cache it once per bar.
_atr = {}


def atr_at(f):
    if f not in _atr:
        _atr[f] = atr(f - 1)
    return _atr[f]


def evaluate(f, stop_mult, rr):
    """Both directions at bar f under one geometry, or None if not scoreable."""
    a = atr_at(f)
    if a is None:
        return None
    S = stop_mult * a
    L, Sh = simulate(f, "LONG", S, rr), simulate(f, "SHORT", S, rr)
    if L is None or Sh is None:
        return None
    return {"f": f, "long": L[0], "short": Sh[0], "best": max(L[0], Sh[0]),
            "why": (L[3], Sh[3]), "S": S}


# ---- samples ---------------------------------------------------------------
stand = [c for c in calls if c.get("confidence") == "NO_TRADE"]
STAND_BARS, PENDING = [], 0
for c in stand:
    f = c["visible_bars"]                    # the bar a fill would have landed on
    if f >= len(rows) or session_end(f) is None:
        PENDING += 1
        continue
    STAND_BARS.append(f)

CTRL_BARS = [f for f in range(20, len(rows)) if session_end(f) is not None]


# ---- statistics, lifted from missed.py ------------------------------------
def mean(v):
    return sum(v) / len(v) if v else 0.0


def sd(v):
    if len(v) < 2:
        return 0.0
    m = mean(v)
    return (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** 0.5


def welch(a, b):
    """Two-sample z on the difference of means."""
    if len(a) < 2 or len(b) < 2:
        return 0.0
    se = (sd(a) ** 2 / len(a) + sd(b) ** 2 / len(b)) ** 0.5
    return (mean(a) - mean(b)) / se if se > 0 else 0.0


def share(v, t=1.5):
    return sum(1 for x in v if x >= t) / len(v) if v else 0.0


def winshare(v):
    """Share of outcomes with R > 0 - the 'win rate' half of rule 3."""
    return sum(1 for x in v if x > 0) / len(v) if v else 0.0


# ---- one cell --------------------------------------------------------------
def cell(stop_mult, rr):
    sdn = [e for e in (evaluate(f, stop_mult, rr) for f in STAND_BARS) if e]
    ctl = [e for e in (evaluate(f, stop_mult, rr) for f in CTRL_BARS) if e]

    def arms(sample, parity_by_enum):
        lo = [e["long"] for e in sample]
        sh = [e["short"] for e in sample]
        if parity_by_enum:   # missed.py's control convention: enumerate index
            fl = [(e["long"] if i % 2 == 0 else e["short"])
                  for i, e in enumerate(sample)]
        else:                # missed.py's stand-down convention: bar index
            fl = [(e["long"] if e["f"] % 2 == 0 else e["short"]) for e in sample]
        fl_bar = [(e["long"] if e["f"] % 2 == 0 else e["short"]) for e in sample]
        bt = [e["best"] for e in sample]
        return {"long": lo, "short": sh, "flip": fl, "flip_bar": fl_bar, "best": bt}

    a_sd = arms(sdn, False)
    a_ct = arms(ctl, True)
    whys = [w for e in ctl for w in e["why"]]
    mix = {k: whys.count(k) / len(whys) for k in ("STOP", "TARGET", "SESSION_CLOSE")} \
        if whys else {}
    return {"stop": stop_mult, "rr": rr, "n_sd": len(sdn), "n_ct": len(ctl),
            "sd": a_sd, "ct": a_ct, "mix": mix,
            "S_med": sorted(e["S"] for e in ctl)[len(ctl) // 2] if ctl else 0.0}


ARMS = [("always LONG", "long"), ("always SHORT", "short"),
        ("coin flip (parity)", "flip")]

results = [cell(s, r) for s in STOPS for r in TARGETS]
diag = [cell(s, r) for s in DIAG_STOPS for r in TARGETS]

N_CELLS, N_ARMS = len(STOPS) * len(TARGETS), len(ARMS)
N_TRIALS = N_CELLS * N_ARMS
FREE_T = math.sqrt(2 * math.log(N_TRIALS))


def report(res, heading, note=""):
    print(f"\n{heading}")
    if note:
        print(note)
    print("\n| stop | targ | arm | n_sd | mean_sd | sd_sd | >=1.5R_sd | n_ct | "
          "mean_ct | sd_ct | >=1.5R_ct | diff | z |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in res:
        for label, key in ARMS:
            a, b = c["sd"][key], c["ct"][key]
            print(f"| {c['stop']:.2f} | {c['rr']:.1f}R | {label} | {len(a)} | "
                  f"{mean(a):+.3f} | {sd(a):.2f} | {share(a):.1%} | {len(b)} | "
                  f"{mean(b):+.3f} | {sd(b):.2f} | {share(b):.1%} | "
                  f"{mean(a)-mean(b):+.3f} | {welch(a,b):+.2f} |")


print("A_grid.py - geometry sweep of the stand-down null")
print(f"visible {len(rows)} bars   stand-downs {len(stand)} "
      f"({len(STAND_BARS)} scoreable, {PENDING} pending)   "
      f"control bars {len(CTRL_BARS)}")
print(f"grid {len(STOPS)} stops x {len(TARGETS)} targets = {N_CELLS} cells, "
      f"{N_ARMS} honest arms -> n_trials {N_TRIALS}, "
      f"free_t = sqrt(2*ln({N_TRIALS})) = {FREE_T:.3f}")

report(results, "### The 12 cells, three honest arms each")

# ---- verdict ---------------------------------------------------------------
print("\n### Verdict scan (honest arms only)")
flags = []
for c in results:
    for label, key in ARMS:
        z = welch(c["sd"][key], c["ct"][key])
        if abs(z) >= 2.0:
            flags.append((c["stop"], c["rr"], label, z))
zs = [(abs(welch(c["sd"][k], c["ct"][k])), c["stop"], c["rr"], lbl)
      for c in results for lbl, k in ARMS]
zs.sort(reverse=True)
print(f"cells x arms with |z| >= 2.0 : {len(flags)} of {N_TRIALS}")
for s, r, lbl, z in flags:
    print(f"    stop {s} ATR, {r}R target, {lbl}: z {z:+.2f}  "
          f"({'CLEARS' if abs(z) >= FREE_T else 'does NOT clear'} "
          f"free_t {FREE_T:.2f})")
print(f"largest |z| anywhere on the honest grid: {zs[0][0]:.2f} at "
      f"stop {zs[0][1]} ATR, {zs[0][2]}R, {zs[0][3]}")
print("top 5 by |z|:")
for z, s, r, lbl in zs[:5]:
    print(f"    |z| {z:.2f}   stop {s} ATR  {r}R  {lbl}")

# ---- the two repo rules this grid can speak to ----------------------------
print("\n### Rule 3 check (win rate and payoff cancel) - CONTROL only")
print("| stop | targ | ctrl win% | ctrl >=1.5R | ctrl mean R |")
print("|---|---|---|---|---|")
for c in results:
    b = c["ct"]["flip"]
    print(f"| {c['stop']:.2f} | {c['rr']:.1f}R | {winshare(b):.1%} | "
          f"{share(b):.1%} | {mean(b):+.3f} |")

print("\n### Tight-stop end vs wide-stop end - mean |z| of the honest arms")
for s in STOPS:
    grp = [abs(welch(c["sd"][k], c["ct"][k]))
           for c in results if c["stop"] == s for _, k in ARMS]
    ct = [mean(c["ct"]["flip"]) for c in results if c["stop"] == s]
    print(f"    stop {s:>4} ATR   mean |z| {mean(grp):.2f}   "
          f"max |z| {max(grp):.2f}   control coin-flip mean R {mean(ct):+.3f}")

print("\n### The noise tax: one tick of slippage as a fraction of 1R")
print("Median stop distance across control bars, and what the fixed 0.25-point")
print("slippage costs as a share of the R unit. This is the mechanical part of")
print("rule 4 and it does not depend on any edge existing.")
print("| stop | median stop (pts) | 1 tick as % of 1R | ctrl coin-flip mean R |")
print("|---|---|---|---|")
for s in DIAG_STOPS + STOPS:
    c = [x for x in (results + diag) if x["stop"] == s and x["rr"] == 2.0][0]
    print(f"| {s:.2f} ATR | {c['S_med']:.2f} | {TICK/c['S_med']:.1%} | "
          f"{mean(c['ct']['flip']):+.3f} |")

print("\n### Exit-reason mix, control, both legs pooled")
print("| stop | targ | STOP | TARGET | SESSION_CLOSE |")
print("|---|---|---|---|---|")
for c in results:
    m = c["mix"]
    print(f"| {c['stop']:.2f} | {c['rr']:.1f}R | {m['STOP']:.1%} | "
          f"{m['TARGET']:.1%} | {m['SESSION_CLOSE']:.1%} |")

report(diag, "### OFF-GRID DIAGNOSTIC - 0.25 ATR stop",
       "NOT one of the 12 cells. Included only to test the repo's rule that\n"
       "structural stops below ~0.5 ATR are noise. Any |z| here must be read\n"
       "against free_t for 15 cells x 3 arms = 45 trials, "
       f"sqrt(2*ln(45)) = {math.sqrt(2*math.log(45)):.2f}.")

# ---- hindsight arm, labelled -------------------------------------------
print("\n### HINDSIGHT ARM - best of both directions. NOT A RESULT.")
print("Direction picked after the outcome. Printed for completeness only; "
      "excluded from\nevery verdict above and from n_trials.")
print("| stop | targ | sd mean | ct mean | diff | z |")
print("|---|---|---|---|---|---|")
for c in results:
    a, b = c["sd"]["best"], c["ct"]["best"]
    print(f"| {c['stop']:.2f} | {c['rr']:.1f}R | {mean(a):+.3f} | {mean(b):+.3f} "
          f"| {mean(a)-mean(b):+.3f} | {welch(a,b):+.2f} |")

# ---- cross-check against missed.py's published cell ---------------------
print("\n### Cross-check: cell (1.0 ATR, 2R) vs missed.py's published table")
base = [c for c in results if c["stop"] == 1.0 and c["rr"] == 2.0][0]
pub = {"long": (+0.211, -0.009, +0.99), "short": (+0.085, -0.003, +0.41),
       "flip": (+0.177, -0.011, +0.85)}
ok = True
for lbl, key in ARMS:
    a, b = base["sd"][key], base["ct"][key]
    p = pub[key]
    d = (abs(mean(a) - p[0]) < 0.002 and abs(mean(b) - p[1]) < 0.002
         and abs(welch(a, b) - p[2]) < 0.02)
    ok = ok and d
    print(f"    {lbl:<20} mine {mean(a):+.3f}/{mean(b):+.3f} z {welch(a,b):+.2f}"
          f"   published {p[0]:+.3f}/{p[1]:+.3f} z {p[2]:+.2f}   "
          f"{'MATCH' if d else 'MISMATCH'}")
print(f"    n_sd {base['n_sd']} (published 41)   "
      f"n_ct {base['n_ct']} (published 1613)")
print(f"    baseline reproduction: {'PASS' if ok else 'FAIL'}")

# ---- convention check: control coin-flip parity by enum vs by bar index ---
print("\n### Convention check: control coin-flip parity")
worst = 0.0
for c in results:
    worst = max(worst, abs(mean(c["ct"]["flip"]) - mean(c["ct"]["flip_bar"])))
print(f"    max |mean(enumerate-parity) - mean(bar-index-parity)| over 12 "
      f"cells = {worst:.4f}")
print("    missed.py uses enumerate index for the control and bar index for the")
print("    stand-downs. Eligible control bars are contiguous from 20, so the two")
print("    parities coincide; reported above on missed.py's convention.")
