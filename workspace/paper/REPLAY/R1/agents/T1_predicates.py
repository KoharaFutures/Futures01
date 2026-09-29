#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T1_predicates.py  --  REPLAY desk R1, temp agent T1.

ONE QUESTION
------------
Is there ANY conditional entry predicate computable from PAST BARS ALONE that
survives (a) an ATR/hour-matched control, (b) a family-wise correction for the
size of the search, and (c) a 60/40 out-of-sample split?

READS   : ../visible.jsonl   (the only data file this script opens)
WRITES  : nothing -- all output goes to stdout
NEEDS   : numpy

RUN     : python3 agents/T1_predicates.py                # full study, ~10 min
          python3 agents/T1_predicates.py --draws 0      # skip the null
          python3 agents/T1_predicates.py --top 40

DESK CONVENTIONS, copied from missed.py / A_grid.py / E6_hours.py
----------------------------------------------------------------
  tick                      0.25 index points
  point value               $5.00 per contract
  round-turn commission     $2.69 per contract
  decision bar              d   (every predicate input uses bars <= d ONLY)
  fill bar                  d+1, at open(d+1) + 1 tick (long) / - 1 tick (short)
  stop distance S           k * ATR14(d)          k in {0.5, 1.0, 1.5}
  target distance           R * S                 R in {1.0, 1.5, 2.0, 3.0}
  same-bar stop/target tie  THE STOP WINS
  exit                      stop, target, or the close of the first 16:00 ET bar
                            at or after the fill bar (the owner's flat)
  cost in R                 2.69 / (5.00 * S), subtracted from every trade

NO-LOOK-AHEAD ENFORCEMENT  (report section 1)
---------------------------------------------
  * build_population() is the ONLY place features are made.  Every slice it
    takes ends at index d: x[d], x[d-k], or x[d-TRAIL:d].  There is no
    expression anywhere in it that indexes d+1 or later.
  * ATR14(d) = SMA of true range over bars d-13..d.
  * Regime buckets (ATR quartile, body/range tercile) are TRAILING percentile
    ranks over bars d-250..d-1.  A full-sample quantile would leak the future
    distribution of volatility into the label; it is not used anywhere.
  * simulate() is the ONLY place bars >= d+1 are touched.  It is handed
    (d, side, k) and never sees a feature; build_population() never sees a
    price past d.  The two functions share no index arithmetic.
  * the fill bar must be contiguous (<= 3h after the decision bar), so no
    "fill" is ever a Sunday reopen two days later.

WHY THE STATISTIC IS PAIRED AS WELL AS RAW
------------------------------------------
  A one-sided arm mixes two different things:
     symmetric  part  (edge_long + edge_short)/2 -- "both sides do badly/well
                      here", i.e. a stop-versus-realised-volatility effect.
                      A trader cannot monetise it with an ENTRY predicate; the
                      only action it licenses is standing down.
     antisymmetric part (edge_long - edge_short)/2 -- the DIRECTIONAL edge.
                      This is the only component an entry predicate can sell.
  Both are reported for every headline cell, and a third family of arms ("DIR")
  tests the antisymmetric component directly, bar-paired, which cancels the
  volatility effect exactly.
"""

import argparse
import datetime
import json
import math
import os
from collections import Counter, defaultdict

import numpy as np

# ----------------------------------------------------------------------------
TICK = 0.25
POINT_VALUE = 5.00
COMMISSION = 2.69
WARMUP = 280
TRAIL = 250
MIN_N = 60
IS_FRAC = 0.60
KS = (0.5, 1.0, 1.5)
RMULTS = (1.0, 1.5, 2.0, 3.0)
MAX_FILL_GAP_H = 3.0
VBASES = ("atr", "hatr")

HERE = os.path.dirname(os.path.abspath(__file__))
TAPE = os.path.join(HERE, os.pardir, "visible.jsonl")

FAMILIES = ["hour", "atrq", "pdir", "bodyq", "mom3", "mom10", "mom20",
            "distopen", "dow", "iobar", "streak", "gap"]

LVL = {
    "atrq": {0: "Q1quiet", 1: "Q2", 2: "Q3", 3: "Q4loud"},
    "pdir": {0: "down", 1: "up", 2: "doji"},
    "bodyq": {0: "T1chop", 1: "T2", 2: "T3trend"},
    "mom3": {0: "down", 1: "up", 2: "flat"},
    "mom10": {0: "down", 1: "up", 2: "flat"},
    "mom20": {0: "down", 1: "up", 2: "flat"},
    "distopen": {0: "below", 1: "near", 2: "above"},
    "dow": {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"},
    "iobar": {0: "inside", 1: "neither", 2: "outside"},
    "streak": {0: "1bar", 1: "2bar", 2: "3+bar"},
    "gap": {0: "down", 1: "up", 2: "flat"},
}


def lvl_name(fam, lab):
    return LVL.get(fam, {}).get(int(lab), "%02d" % int(lab))


def cell_name(spec, lab, nb2):
    if len(spec) == 1:
        return "%s=%s" % (spec[0], lvl_name(spec[0], lab))
    return "%s=%s & %s=%s" % (spec[0], lvl_name(spec[0], lab // nb2),
                              spec[1], lvl_name(spec[1], lab % nb2))


# ----------------------------------------------------------------------------
# 1. tape
# ----------------------------------------------------------------------------
def load():
    with open(TAPE) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def build_series(rows):
    n = len(rows)
    o = np.array([r["o"] for r in rows], float)
    h = np.array([r["h"] for r in rows], float)
    lo = np.array([r["l"] for r in rows], float)
    c = np.array([r["c"] for r in rows], float)

    hour = np.zeros(n, int)
    dow = np.zeros(n, int)
    utcmin = np.zeros(n, float)
    date = []
    for i, r in enumerate(rows):
        ts = r["ts"]
        d = datetime.date.fromisoformat(ts[:10])
        date.append(ts[:10])
        hour[i] = int(ts[11:13])
        dow[i] = d.weekday()                 # 0 = Monday
        off = ts[19:]
        omin = (1 if off[0] == "+" else -1) * (int(off[1:3]) * 60 + int(off[4:6]))
        utcmin[i] = d.toordinal() * 1440 + hour[i] * 60 - omin

    tr = np.empty(n)
    tr[0] = h[0] - lo[0]
    pc = c[:-1]
    tr[1:] = np.maximum.reduce([h[1:] - lo[1:], np.abs(h[1:] - pc),
                               np.abs(lo[1:] - pc)])
    atr = np.full(n, np.nan)
    cs = np.cumsum(tr)
    atr[13:] = (cs[13:] - np.concatenate(([0.0], cs[:-14]))) / 14.0

    # sessions: the owner's 18:00 -> 16:00 ET cycle
    sess = np.zeros(n, int)
    sid = 0
    for i in range(1, n):
        if hour[i] == 18 or (utcmin[i] - utcmin[i - 1]) > 60.0 * MAX_FILL_GAP_H:
            sid += 1
        sess[i] = sid
    sess_open = np.empty(n)
    seen = {}
    for i in range(n):
        seen.setdefault(sess[i], o[i])
        sess_open[i] = seen[sess[i]]

    flat_idx = np.full(n, -1, int)
    nxt = -1
    for i in range(n - 1, -1, -1):
        if hour[i] == 16:
            nxt = i
        flat_idx[i] = nxt

    # HOUR-CONDITIONAL VOLATILITY.  hvol[i] = mean true range of the previous
    # HWIN bars that share bar i's ET hour, all of them STRICTLY BEFORE i.
    # Used to size a stop for a trade that will be HELD through hour[i].
    # This reads bar i's clock hour but no price at or after bar i, so for a
    # decision at bar d the quantity hvol[d+1] uses only prices <= d plus the
    # exchange calendar (which is not price information).  Flagged in the report.
    HWIN = 20
    hvol = np.full(n, np.nan)
    hist = defaultdict(list)
    for i in range(n):
        hh = int(hour[i])
        if len(hist[hh]) >= HWIN:
            hvol[i] = float(np.mean(hist[hh][-HWIN:]))
        hist[hh].append(tr[i])

    return dict(o=o, h=h, l=lo, c=c, hour=hour, dow=dow, date=date, tr=tr,
                utcmin=utcmin, atr=atr, sess=sess, sess_open=sess_open,
                flat_idx=flat_idx, hvol=hvol, n=n)


# ----------------------------------------------------------------------------
# 2. population and features -- NOTHING here reads index > d
# ----------------------------------------------------------------------------
def build_population(S):
    o, h, lo, c = S["o"], S["h"], S["l"], S["c"]
    hour, dow, atr = S["hour"], S["dow"], S["atr"]
    flat_idx, utcmin, sess_open = S["flat_idx"], S["utcmin"], S["sess_open"]
    n = S["n"]
    bodyser = np.abs(c - o) / np.maximum(h - lo, 1e-9)

    dec, feats, drops = [], defaultdict(list), Counter()
    for d in range(WARMUP, n - 1):
        f = d + 1
        if utcmin[f] - utcmin[d] > 60.0 * MAX_FILL_GAP_H:
            drops["fill bar not contiguous (weekend / holiday gap)"] += 1
            continue
        if hour[f] == 16:
            drops["fill bar is the 16:00 flat bar (1-bar degenerate trade)"] += 1
            continue
        if flat_idx[f] < 0:
            drops["forward window unresolved inside the visible tape"] += 1
            continue
        if not np.isfinite(atr[d]) or atr[d] <= 0:
            drops["ATR14 missing or zero"] += 1
            continue
        if not np.isfinite(S["hvol"][f]) or S["hvol"][f] <= 0:
            drops["hour-conditional volatility not yet estimable"] += 1
            continue
        rng = h[d] - lo[d]
        if rng <= 0:
            drops["decision bar has zero range"] += 1
            continue

        atrq = int(min(3, np.mean(atr[d - TRAIL:d] < atr[d]) * 4))
        bodyq = int(min(2, np.mean(bodyser[d - TRAIL:d] < bodyser[d]) * 3))
        pdir = 1 if c[d] > o[d] else (0 if c[d] < o[d] else 2)
        mm = []
        for N in (3, 10, 20):
            mm.append(1 if c[d] > c[d - N] else (0 if c[d] < c[d - N] else 2))
        dz = (c[d] - sess_open[d]) / atr[d]
        distopen = 0 if dz < -0.5 else (2 if dz > 0.5 else 1)
        inside = (h[d] <= h[d - 1]) and (lo[d] >= lo[d - 1])
        outside = (h[d] >= h[d - 1]) and (lo[d] <= lo[d - 1])
        iobar = 0 if inside else (2 if outside else 1)
        s0 = np.sign(c[d] - c[d - 1])
        st = 1
        if s0 != 0:
            while st < 8 and np.sign(c[d - st] - c[d - st - 1]) == s0:
                st += 1
        streak = 0 if st == 1 else (1 if st == 2 else 2)
        g = o[d] - c[d - 1]
        gap = 1 if g > 0 else (0 if g < 0 else 2)

        dec.append(d)
        for k, v in (("hour", int(hour[d])), ("atrq", atrq), ("pdir", pdir),
                     ("bodyq", bodyq), ("mom3", mm[0]), ("mom10", mm[1]),
                     ("mom20", mm[2]), ("distopen", distopen),
                     ("dow", int(dow[d])), ("iobar", iobar),
                     ("streak", streak), ("gap", gap)):
            feats[k].append(v)

    return np.array(dec, int), {k: np.array(v, int) for k, v in feats.items()}, drops


# ----------------------------------------------------------------------------
# 3. simulator -- the ONLY code that touches bars >= d+1
# ----------------------------------------------------------------------------
def simulate(S, dec, k, rmult, side, vbase="atr"):
    """
    vbase = "atr"  : stop = k * ATR14(d)                    -- the desk default
    vbase = "hatr" : stop = k * hvol(d+1)                   -- hour-conditional,
            the mean true range of the fill bar's own ET hour over the previous
            20 occurrences of that hour.  Both are causal; see build_series().
    """
    o, h, lo, c = S["o"], S["h"], S["l"], S["c"]
    atr, flat_idx = S["atr"], S["flat_idx"]
    vol = S["atr"] if vbase == "atr" else S["hvol"]
    voff = 0 if vbase == "atr" else 1
    m = len(dec)
    rg = np.empty(m)
    cost = np.empty(m)
    spt = np.empty(m)
    for ix in range(m):
        d = int(dec[ix])
        f = d + 1
        st = k * vol[d + voff]
        entry = o[f] + side * TICK
        stop_px = entry - side * st
        targ_px = entry + side * rmult * st
        end = flat_idx[f]
        out = None
        if side > 0:
            for j in range(f, end + 1):
                if lo[j] <= stop_px:
                    out = -1.0
                    break
                if h[j] >= targ_px:
                    out = rmult
                    break
        else:
            for j in range(f, end + 1):
                if h[j] >= stop_px:
                    out = -1.0
                    break
                if lo[j] <= targ_px:
                    out = rmult
                    break
        if out is None:
            out = side * (c[end] - entry) / st
        rg[ix] = out
        cost[ix] = COMMISSION / (POINT_VALUE * st)
        spt[ix] = st
    return rg, rg - cost, cost, spt


# ----------------------------------------------------------------------------
# 4. grid plan -- labels precomputed once, so every arm and every null draw
#    is just a handful of bincounts
# ----------------------------------------------------------------------------
def group_specs():
    specs = [(f,) for f in FAMILIES]
    for i in range(len(FAMILIES)):
        for j in range(i + 1, len(FAMILIES)):
            specs.append((FAMILIES[i], FAMILIES[j]))
    return specs


class Plan(object):
    """Cell labels, stratum labels and cluster labels for one (spec, index set)."""

    def __init__(self, F, spec, idx, clu, min_n):
        self.spec = spec
        nb2 = int(F[spec[1]].max()) + 1 if len(spec) == 2 else 1
        self.nb2 = nb2
        if len(spec) == 1:
            cl = F[spec[0]][idx]
        else:
            cl = F[spec[0]][idx] * nb2 + F[spec[1]][idx]
        self.ncl = int(cl.max()) + 1
        self.cl = cl

        # matched control strata = ATRq x decision-hour, MINUS treatment dims
        use_atr = "atrq" not in spec
        use_hour = "hour" not in spec
        aq, hr = F["atrq"][idx], F["hour"][idx]
        if use_atr and use_hour:
            sl, nsl, nm = aq * 24 + hr, 96, "ATRq x hour"
        elif use_atr:
            sl, nsl, nm = aq.copy(), 4, "ATRq (hour is the treatment)"
        elif use_hour:
            sl, nsl, nm = hr.copy(), 24, "hour (ATRq is the treatment)"
        else:
            sl, nsl, nm = np.zeros(len(aq), int), 1, "none (both are treatment)"
        self.sl, self.nsl, self.smatch = sl, nsl, nm

        self.n1 = np.bincount(cl, minlength=self.ncl).astype(float)
        self.keep = np.where(self.n1 >= min_n)[0]
        self.pool_n = np.bincount(sl, minlength=nsl).astype(float)

        ucl, self.cinv = np.unique(clu, return_inverse=True)
        self.ncls = len(ucl)
        self.comb = cl * self.ncls + self.cinv
        self.nbc = self.ncl * self.ncls
        self.ccount = np.bincount(self.comb,
                                  minlength=self.nbc).reshape(self.ncl, self.ncls)
        self.g = (self.ccount > 0).sum(axis=1).astype(float)
        # share of each cell's matched strata that the cell itself occupies
        cs = np.bincount(cl * nsl + sl,
                         minlength=self.ncl * nsl).reshape(self.ncl, nsl)
        self.share = np.where(self.n1 > 0,
                              (cs * cs / np.maximum(self.pool_n, 1)).sum(axis=1)
                              / np.maximum(self.n1, 1), 0.0)

    def evaluate(self, r):
        """
        Returns (edge, z_clu, mean_cell) per cell label.

        edge  = cell mean of y, where y_i = r_i - mean(r over bar i's matched
                stratum).  That is exactly "cell mean minus its ATR/hour-matched
                control mean", with the control INCLUDING the cell's own bars,
                which shrinks |edge| by roughly (1 - share) and is therefore
                CONSERVATIVE.
        z_clu = edge / cluster-robust SE of y inside the cell, clusters = the
                owner's 18:00->16:00 ET trading sessions.  Overlapping forward
                windows inside one session are the dependence this removes; an
                i.i.d. SE inflates |z| by ~1.7x on this tape.
        """
        mu = np.bincount(self.sl, weights=r, minlength=self.nsl) / \
            np.maximum(self.pool_n, 1)
        y = r - mu[self.sl]
        s1 = np.bincount(self.cl, weights=y, minlength=self.ncl)
        edge = s1 / np.maximum(self.n1, 1)
        cs = np.bincount(self.comb, weights=y,
                         minlength=self.nbc).reshape(self.ncl, self.ncls)
        dev = cs - self.ccount * edge[:, None]
        ss = (dev * dev).sum(axis=1)
        gg = np.maximum(self.g, 2.0)
        var = ss * gg / (gg - 1.0) / np.maximum(self.n1, 1) ** 2
        se = np.sqrt(np.maximum(var, 0.0))
        z = np.where(se > 0, edge / np.maximum(se, 1e-12), 0.0)
        mean_cell = np.bincount(self.cl, weights=r,
                                minlength=self.ncl) / np.maximum(self.n1, 1)
        return edge, z, mean_cell


def wr_payoff(x):
    w, l = x[x > 0], x[x <= 0]
    wr = len(w) / len(x) if len(x) else float("nan")
    aw = w.mean() if len(w) else 0.0
    al = -l.mean() if len(l) else 0.0
    return wr, aw, al, (aw / al if al > 0 else float("inf"))


# ----------------------------------------------------------------------------
# 5. main
# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=150,
                    help="circular-shift null draws (0 = skip)")
    ap.add_argument("--top", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20260929)
    args = ap.parse_args()

    rows = load()
    S = build_series(rows)
    print("=" * 96)
    print("T1 -- systematic conditional entry predicate search, MES 60m, REPLAY R1")
    print("=" * 96)
    print("tape snapshot      : %d bars   %s -> %s"
          % (S["n"], rows[0]["ts"], rows[-1]["ts"]))
    print("sessions (18-16 ET): %d" % (S["sess"].max() + 1))
    print("costs              : tick %.2f   point value $%.2f   round turn $%.2f"
          % (TICK, POINT_VALUE, COMMISSION))

    dec, F, drops = build_population(S)
    m = len(dec)
    print("\n== POPULATION ==========================================================")
    print("eligible decision bars : %d  (bar %d .. %d)" % (m, dec[0], dec[-1]))
    for k, v in drops.most_common():
        print("   dropped %5d : %s" % (v, k))
    print("decision-hour levels   : %d" % len(set(F["hour"].tolist())))
    print("dow x hour confound    : Sunday bars exist only at hours 18-23 and "
          "Friday has none, so dow and hour are NOT independent -- the matched "
          "control absorbs the hour part of any dow cell.")

    cut = int(round(IS_FRAC * m))
    IS, OS = np.arange(cut), np.arange(cut, m)
    print("in-sample  : %4d bars  %s .. %s"
          % (len(IS), S["date"][dec[0]], S["date"][dec[cut - 1]]))
    print("out-sample : %4d bars  %s .. %s"
          % (len(OS), S["date"][dec[cut]], S["date"][dec[-1]]))

    # -- simulate every geometry once ---------------------------------------
    print("\n== GEOMETRY GRID (all eligible bars, cost-charged) =====================")
    print("vol = atr  : stop = k * ATR14(decision bar)   [the desk default]")
    print("vol = hatr : stop = k * mean TR of the FILL BAR's own ET hour over "
          "its previous 20 occurrences")
    print("%-5s %-5s %4s %4s %7s %7s %8s %8s %6s %7s"
          % ("vol", "side", "k", "R", "meanS", "costR", "grossR", "netR",
             "win%", "payoff"))
    netR = {}
    for vb in VBASES:
        for side, sn in ((1, "LONG"), (-1, "SHORT")):
            for k in KS:
                for rm in RMULTS:
                    rg, rn, cst, spt = simulate(S, dec, k, rm, side, vb)
                    netR[(side, k, rm, vb)] = rn
                    wr, aw, al, po = wr_payoff(rn)
                    print("%-5s %-5s %4.1f %4.1f %7.2f %7.4f %+8.4f %+8.4f "
                          "%5.1f%% %7.2f"
                          % (vb, sn, k, rm, spt.mean(), cst.mean(), rg.mean(),
                             rn.mean(), 100 * wr, po))
    # DIR arms: bar-paired antisymmetric score.  Cost cancels in the difference.
    for vb in VBASES:
        for k in KS:
            for rm in RMULTS:
                netR[(0, k, rm, vb)] = 0.5 * (netR[(1, k, rm, vb)] -
                                              netR[(-1, k, rm, vb)])

    for vb in VBASES:
        coin = 0.5 * (netR[(1, 1.0, 2.0, vb)] + netR[(-1, 1.0, 2.0, vb)])
        print("friction floor (coin flip, k=1.0 R=2.0, vol=%-4s) : %+0.4f R/trade"
              % (vb, coin.mean()))

    specs = group_specs()
    ARMS = [(s, k, rm, vb) for vb in VBASES for s in (1, -1, 0)
            for k in KS for rm in RMULTS]
    print("\ngrouping variables : %d marginals + %d pairs = %d"
          % (len(FAMILIES), len(specs) - len(FAMILIES), len(specs)))
    print("arms               : %d  = 2 vol bases x (2 sides + 1 paired DIR) x "
          "3 stops x 4 targets" % len(ARMS))

    # -- in-sample grid -----------------------------------------------------
    clu_is = S["sess"][dec[IS]]
    clu_os = S["sess"][dec[OS]]
    plans_is = {sp: Plan(F, sp, IS, clu_is, MIN_N) for sp in specs}
    plans_os = {sp: Plan(F, sp, OS, clu_os, 20) for sp in specs}

    cells = []
    N = 0
    for arm in ARMS:
        r = netR[arm][IS]
        for sp in specs:
            P = plans_is[sp]
            if len(P.keep) == 0:
                continue
            edge, z, mc = P.evaluate(r)
            for lab in P.keep:
                N += 1
                cells.append((abs(z[lab]), arm, sp, int(lab), int(P.n1[lab]),
                              float(edge[lab]), float(z[lab]), float(mc[lab]),
                              float(P.share[lab]), P.smatch, P.nb2))

    free_t = math.sqrt(2.0 * math.log(N))
    nz = np.array([c[0] for c in cells])
    print("\n== THE LUCK BAR ========================================================")
    print("cells EVALUATED in sample (n >= %d bars)   N       = %d" % (MIN_N, N))
    print("free_t = sqrt(2 * ln N)                            = %.4f" % free_t)
    print("breakdown by side : LONG %d  SHORT %d  paired-DIR %d"
          % (sum(1 for c in cells if c[1][0] == 1),
             sum(1 for c in cells if c[1][0] == -1),
             sum(1 for c in cells if c[1][0] == 0)))
    print("breakdown by stop : vol=atr %d   vol=hatr %d"
          % (sum(1 for c in cells if c[1][3] == "atr"),
             sum(1 for c in cells if c[1][3] == "hatr")))
    print("cells |z| >= 1.96 (nominal 5%%)             = %5d   (chance %.0f)"
          % (int((nz >= 1.96).sum()), 0.05 * N))
    print("cells |z| >= 3.00                          = %5d   (chance %.1f)"
          % (int((nz >= 3.0).sum()), 0.0027 * N))
    print("cells |z| >= free_t %.3f                   = %5d   (chance %.2f)"
          % (free_t, int((nz >= free_t).sum()),
             N * 2 * (1 - 0.5 * (1 + math.erf(free_t / math.sqrt(2))))))
    print("largest |z| anywhere on the grid           = %.3f" % nz.max())

    cells.sort(key=lambda c: -c[0])

    # -- symmetry decomposition for the headline cells ----------------------
    def sym_anti(sp, lab, k, rm, vb, index, plans):
        P = plans[sp]
        eL, _, _ = P.evaluate(netR[(1, k, rm, vb)][index])
        eS, _, _ = P.evaluate(netR[(-1, k, rm, vb)][index])
        if lab >= len(eL):
            return float("nan"), float("nan")
        return 0.5 * (eL[lab] + eS[lab]), 0.5 * (eL[lab] - eS[lab])

    print("\n== TOP %d CELLS IN-SAMPLE (ranked by |z| vs the matched control) ========"
          % args.top)
    print("side = L long, S short, D bar-paired directional score (R_L-R_S)/2")
    print("sym / anti = symmetric and antisymmetric parts of the long/short edge "
          "pair at the same cell and geometry.")
    print("KIND: DIR = the two sides disagree (a real directional claim).  "
          "SYM = both sides move the same way (a volatility/stop effect, not an "
          "entry edge).")
    print("-" * 96)
    print("%-4s %-3s %4s %4s %5s %8s %8s %7s %6s %7s %8s %8s %-4s %s"
          % ("vol", "sd", "k", "R", "n", "netR", "edgeR", "z_clu", "win%",
             "payoff", "sym", "anti", "kind", "predicate"))
    head = cells[:args.top]
    for (az, arm, sp, lab, n1, edge, z, mc, share, sm, nb2) in head:
        side, k, rm, vb = arm
        r = netR[arm][IS]
        mask = plans_is[sp].cl == lab
        wr, aw, al, po = wr_payoff(r[mask])
        sy, an = sym_anti(sp, lab, k, rm, vb, IS, plans_is)
        kind = "DIR" if abs(an) > abs(sy) else "SYM"
        print("%-4s %-3s %4.1f %4.1f %5d %+8.4f %+8.4f %+7.2f %5.1f%% %7.2f "
              "%+8.4f %+8.4f %-4s %s"
              % (vb, {1: "L", -1: "S", 0: "D"}[side], k, rm, n1, mc, edge, z,
                 100 * wr, po, sy, an, kind, cell_name(sp, lab, nb2)))

    # -- circular-shift null on the WHOLE grid ------------------------------
    if args.draws > 0:
        rng = np.random.default_rng(args.seed)
        nulls = np.empty(args.draws)
        base = {a: netR[a][IS] for a in ARMS}
        L = len(IS)
        for t in range(args.draws):
            off = int(rng.integers(50, L - 50))
            best = 0.0
            for arm in ARMS:
                rr = np.roll(base[arm], off)
                for sp in specs:
                    P = plans_is[sp]
                    if len(P.keep) == 0:
                        continue
                    _, z, _ = P.evaluate(rr)
                    zz = np.abs(z[P.keep])
                    if zz.size:
                        v = float(zz.max())
                        if v > best:
                            best = v
            nulls[t] = best
        print("\n== FAMILY-WISE NULL (%d circular shifts of the outcome series, "
              "features fixed) ==" % args.draws)
        print("The shift keeps the serial dependence of the R series intact and "
              "destroys only its alignment with the predicates -- the right null "
              "for a grid whose trials are heavily correlated.")
        print("observed max|z| over the whole grid : %.3f" % nz.max())
        print("null max|z| : median %.3f  90th %.3f  95th %.3f  99th %.3f  "
              "max %.3f" % (np.median(nulls), np.percentile(nulls, 90),
                            np.percentile(nulls, 95), np.percentile(nulls, 99),
                            nulls.max()))
        p = (1 + int((nulls >= nz.max()).sum())) / (args.draws + 1)
        print("family-wise p for the best cell on the grid : %.4f" % p)
        print("empirical family-wise 5%% threshold on |z|   : %.3f  "
              "(free_t says %.3f)" % (np.percentile(nulls, 95), free_t))

    # -- out of sample ------------------------------------------------------
    print("\n== OUT-OF-SAMPLE, last %d bars (%s .. %s) ==============================="
          % (len(OS), S["date"][dec[cut]], S["date"][dec[-1]]))
    print("%-4s %-3s %4s %4s %5s %8s %8s %7s %6s %7s %-5s %s"
          % ("vol", "sd", "k", "R", "n_os", "netR", "edgeR", "z_clu", "win%",
             "payoff", "flip?", "predicate"))
    flips = kept = 0
    for (az, arm, sp, lab, n1, edge, z, mc, share, sm, nb2) in head:
        side, k, rm, vb = arm
        P = plans_os[sp]
        if lab >= P.ncl or P.n1[lab] < 20:
            print("%-4s %-3s %4.1f %4.1f %5s  -- too few out-of-sample bars -- %s"
                  % (vb, {1: "L", -1: "S", 0: "D"}[side], k, rm, "-",
                     cell_name(sp, lab, nb2)))
            continue
        e2, z2, mc2 = P.evaluate(netR[arm][OS])
        mask = P.cl == lab
        wr, aw, al, po = wr_payoff(netR[arm][OS][mask])
        flip = (edge * e2[lab]) < 0
        flips += int(flip)
        kept += int(not flip)
        print("%-4s %-3s %4.1f %4.1f %5d %+8.4f %+8.4f %+7.2f %5.1f%% %7.2f "
              "%-5s %s"
              % (vb, {1: "L", -1: "S", 0: "D"}[side], k, rm, int(P.n1[lab]),
                 float(mc2[lab]), float(e2[lab]), float(z2[lab]), 100 * wr, po,
                 "FLIP" if flip else "same", cell_name(sp, lab, nb2)))
    print("sign flips : %d of %d  (chance %.1f)"
          % (flips, flips + kept, 0.5 * (flips + kept)))

    # -- the survivor funnel ------------------------------------------------
    print("\n== SURVIVOR FUNNEL =====================================================")
    surv = [c for c in cells if c[0] >= free_t]
    print("1. cells evaluated in sample                         : %d" % N)
    print("2. ... clearing free_t = %.3f in sample              : %d"
          % (free_t, len(surv)))
    st2 = []
    for c in surv:
        az, arm, sp, lab, n1, edge, z, mc, share, sm, nb2 = c
        side, k, rm, vb = arm
        sy, an = sym_anti(sp, lab, k, rm, vb, IS, plans_is)
        if side == 0 or abs(an) > abs(sy):
            st2.append(c)
    print("3. ... whose edge is DIRECTIONAL, not a symmetric "
          "volatility effect : %d" % len(st2))
    st3 = []
    for c in st2:
        az, arm, sp, lab, n1, edge, z, mc, share, sm, nb2 = c
        P = plans_os[sp]
        if lab >= P.ncl or P.n1[lab] < 20:
            continue
        e2, z2, mc2 = P.evaluate(netR[arm][OS])
        if edge * e2[lab] > 0:
            st3.append((c, float(e2[lab]), float(z2[lab]), float(mc2[lab]),
                        int(P.n1[lab])))
    print("4. ... keeping the sign of their edge out-of-sample   : %d"
          % len(st3))
    st4 = [x for x in st3 if x[3] > 0 or x[0][1][0] == 0]
    print("5. ... with a POSITIVE cost-adjusted net R out-of-sample (DIR arms "
          "exempt, they are not a P&L) : %d" % len(st4))
    st5 = [x for x in st4 if abs(x[2]) >= 1.96]
    print("6. ... and nominally significant out-of-sample (|z_os| >= 1.96): %d"
          % len(st5))
    for (c, e2, z2, mc2, n2) in st4:
        az, arm, sp, lab, n1, edge, z, mc, share, sm, nb2 = c
        side, k, rm, vb = arm
        print("   %-4s %-3s k=%.1f R=%.1f %-40s n_is=%4d edge_is %+0.4f z %+0.2f"
              " | n_os=%4d edge_os %+0.4f z_os %+0.2f netR_os %+0.4f"
              % (vb, {1: "L", -1: "S", 0: "D"}[side], k, rm,
                 cell_name(sp, lab, nb2), n1, edge, z, n2, e2, z2, mc2))

    # -- the strongest structure on the tape, whatever kind it is -----------
    print("\n== DIAGNOSTIC: the strongest SYMMETRIC cells (not entry edges) =========")
    print("These are the largest effects on the tape.  They are volatility-versus-"
          "stop effects: both sides lose (or both win) together, so no entry "
          "predicate can sell them.  Reported because they are real and they are "
          "the reason a naive one-sided grid lights up.")
    print("%-4s %-3s %4s %4s %5s %8s %8s %8s %8s %7s  %s"
          % ("vol", "sd", "k", "R", "n", "edgeL", "edgeS", "sym", "anti",
             "z_clu", "predicate"))
    shown = 0
    seen_sym = set()
    for (az, arm, sp, lab, n1, edge, z, mc, share, sm, nb2) in cells:
        side, k, rm, vb = arm
        if side == 0:
            continue
        sy, an = sym_anti(sp, lab, k, rm, vb, IS, plans_is)
        if abs(sy) <= abs(an):
            continue
        key = (sp, lab, vb)
        if key in seen_sym:
            continue
        seen_sym.add(key)
        P = plans_is[sp]
        eL, _, _ = P.evaluate(netR[(1, k, rm, vb)][IS])
        eS, _, _ = P.evaluate(netR[(-1, k, rm, vb)][IS])
        print("%-4s %-3s %4.1f %4.1f %5d %+8.4f %+8.4f %+8.4f %+8.4f %+7.2f  %s"
              % (vb, {1: "L", -1: "S"}[side], k, rm, n1, eL[lab], eS[lab], sy,
                 an, z, cell_name(sp, lab, nb2)))
        shown += 1
        if shown >= 15:
            break

    # -- the single-marginal table, for the record --------------------------
    print("\n== MARGINALS AT THE DESK'S REFERENCE GEOMETRY (k=1.0, R=2.0) ===========")
    print("Every level of every single feature, both sides, full tape.  This is "
          "the honest 'nothing here' table.")
    print("%-22s %5s %9s %9s %9s %9s %8s %8s"
          % ("predicate", "n", "netR_L", "netR_S", "edgeL", "edgeS", "zL", "zS"))
    full = np.arange(m)
    clu_f = S["sess"][dec]
    for fam in FAMILIES:
        P = Plan(F, (fam,), full, clu_f, MIN_N)
        eL, zL, mL = P.evaluate(netR[(1, 1.0, 2.0, "atr")])
        eS, zS, mS = P.evaluate(netR[(-1, 1.0, 2.0, "atr")])
        for lab in P.keep:
            print("%-22s %5d %+9.4f %+9.4f %+9.4f %+9.4f %+8.2f %+8.2f"
                  % (cell_name((fam,), lab, 1), int(P.n1[lab]), mL[lab], mS[lab],
                     eL[lab], eS[lab], zL[lab], zS[lab]))

    # -- the mechanism behind the symmetric cells ---------------------------
    print("\n== MECHANISM: realised range in the holding window vs the stop "
          "you sized from ==")
    print("For every decision hour: the excursion actually available after the "
          "fill, divided by ATR14(d) (the desk's stop scale) and by hvol(d+1) "
          "(the fill hour's own volatility).  A ratio >> 1 means a k=0.5 stop "
          "is inside the noise of the bar it will be held through, so BOTH "
          "sides get stopped and the cell looks 'significant' without any "
          "direction in it.")
    o_, h_, l_, c_ = S["o"], S["h"], S["l"], S["c"]
    fw_atr = defaultdict(list)
    fw_h = defaultdict(list)
    nb_hold = defaultdict(list)
    for ix in range(m):
        d = int(dec[ix])
        f = d + 1
        e = S["flat_idx"][f]
        hi = h_[f:e + 1].max()
        loo = l_[f:e + 1].min()
        ex = max(hi - o_[f], o_[f] - loo)
        fw_atr[int(S["hour"][d])].append(ex / S["atr"][d])
        fw_h[int(S["hour"][d])].append(ex / S["hvol"][f])
        nb_hold[int(S["hour"][d])].append(e - f + 1)
    print("%-6s %6s %10s %10s %10s %14s"
          % ("dec_hr", "n", "bars_held", "exc/ATR14", "exc/hvol", "ATR14/hvol"))
    for hh in sorted(fw_atr):
        a = np.array(fw_atr[hh])
        b = np.array(fw_h[hh])
        print("%-6d %6d %10.1f %10.2f %10.2f %14.2f"
              % (hh, len(a), np.mean(nb_hold[hh]), a.mean(), b.mean(),
                 (a / np.maximum(b, 1e-9)).mean()))

    print("\n== SYMMETRIC EDGE BY DECISION HOUR AND STOP WIDTH (in sample) =====")
    print("sym = (edge_long + edge_short)/2 at R=2.0.  Matched control = the "
          "ATR quartile mix (hour is the treatment, so it is dropped from the "
          "matching).  Read down a column: if the effect is a mis-sized stop it "
          "must shrink as k grows and vanish under vol=hatr.")
    Ph = Plan(F, ("hour",), IS, clu_is, MIN_N)
    cols = [(vb, k) for vb in VBASES for k in KS]
    print("%-6s %6s " % ("dec_hr", "n") +
          " ".join("%10s" % ("%s k=%.1f" % (vb, k)) for vb, k in cols))
    for lab in Ph.keep:
        row = []
        for vb, k in cols:
            eL, _, _ = Ph.evaluate(netR[(1, k, 2.0, vb)][IS])
            eS, _, _ = Ph.evaluate(netR[(-1, k, 2.0, vb)][IS])
            row.append(0.5 * (eL[lab] + eS[lab]))
        print("%-6s %6d " % (lvl_name("hour", lab), int(Ph.n1[lab])) +
              " ".join("%+10.4f" % v for v in row))

    print("\n== THE SAME SEARCH RESTRICTED TO DIRECTIONAL (paired) ARMS ONLY ====")
    dcells = [c for c in cells if c[1][0] == 0]
    dz = np.array([c[0] for c in dcells])
    ft_d = math.sqrt(2.0 * math.log(len(dcells)))
    print("directional cells evaluated  N_dir = %d   free_t = %.4f"
          % (len(dcells), ft_d))
    print("|z| >= 1.96 : %d (chance %.0f)   |z| >= 3.0 : %d (chance %.1f)   "
          "|z| >= free_t : %d"
          % (int((dz >= 1.96).sum()), 0.05 * len(dcells),
             int((dz >= 3.0).sum()), 0.0027 * len(dcells),
             int((dz >= ft_d).sum())))
    print("largest |z| among directional cells = %.3f" % dz.max())
    print("%-4s %4s %4s %5s %8s %8s %7s %6s %7s  %s"
          % ("vol", "k", "R", "n", "dirR", "edgeR", "z_clu", "win%", "payoff",
             "predicate"))
    for (az, arm, sp, lab, n1, edge, z, mc, share, sm, nb2) in dcells[:15]:
        side, k, rm, vb = arm
        side_pick = 1 if edge > 0 else -1
        rp = netR[(side_pick, k, rm, vb)][IS]
        mask = plans_is[sp].cl == lab
        wr, aw, al, po = wr_payoff(rp[mask])
        print("%-4s %4.1f %4.1f %5d %+8.4f %+8.4f %+7.2f %5.1f%% %7.2f  %s "
              "[trade %s]"
              % (vb, k, rm, n1, float(rp[mask].mean()), edge, z, 100 * wr, po,
                 cell_name(sp, lab, nb2), "LONG" if side_pick > 0 else "SHORT"))
    print("(dirR / win%% / payoff are for the side the in-sample edge points to, "
          "traded with costs charged.)")

    print("\ndone.")


if __name__ == "__main__":
    main()
