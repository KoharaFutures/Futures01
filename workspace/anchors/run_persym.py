#!/usr/bin/env python3
"""PERSYM1 — one track per symbol, from DATA_HUB/OPEN_QUESTIONS.md.
Pre-registration: HYPOTHESES_PERSYM1.md (incl. the 5b amendment). 15 confirmations, bar 2.327."""
from __future__ import annotations

import json
import math
import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import core                                              # noqa: E402
import structures as S                                   # noqa: E402
from levels import touch_signals                         # noqa: E402
from stage import confirm                                # noqa: E402
from vp_levels import build_profile                      # noqa: E402

N_CONF = 15
BAR = math.sqrt(2 * math.log(N_CONF))


def tstat(v):
    if len(v) < 2:
        return None
    sd = st.stdev(v)
    return (st.fmean(v) / (sd / math.sqrt(len(v)))) if sd > 0 else None


# ---------------------------------------------------------------- track A
def neutral_signals(t, kind):
    """Every eligible bar; direction fixed with no selection. 'mom' = follow the prior bar."""
    sig = []
    for i in range(1, len(t.bars)):
        if not t.rth[i] or t.last_rth[i] or t.atr[i] is None:
            continue
        up = t.bars[i].c > t.bars[i - 1].c
        side = (1 if up else -1) if kind == "mom" else (-1 if up else 1)
        sig.append((i, side, t.bars[i].c, kind))
    return sig


def track_a(sym):
    t = core.tape(sym, 60)
    out = {}
    for kind in ("mom", "rev"):
        sig = neutral_signals(t, kind)
        books = {}
        for pol in ("base", "be08", "x08"):
            books[pol] = core.score(t, sig, t.is_end, len(t), one_at_a_time=False, policy=pol)
        key = {pol: {x.i: x for x in bk.trades} for pol, bk in books.items()}
        common = sorted(set(key["base"]) & set(key["be08"]) & set(key["x08"]))
        rows = {}
        for pol in ("base", "be08", "x08"):
            v = [key[pol][i].r for i in common]
            rows[pol] = {"n": len(v), "avg_r": st.fmean(v) if v else None, "t": tstat(v),
                         "win": (sum(1 for x in v if x > 0) / len(v)) if v else None,
                         "exits": {w: sum(1 for i in common if key[pol][i].why == w)
                                   for w in sorted({key[pol][i].why for i in common})}}
        for pol in ("be08", "x08"):
            d = [key[pol][i].r - key["base"][i].r for i in common]
            half = len(d) // 2
            rows[pol]["paired_diff"] = st.fmean(d) if d else None
            rows[pol]["paired_t"] = tstat(d)
            rows[pol]["diff_h1"] = st.fmean(d[:half]) if half else None
            rows[pol]["diff_h2"] = st.fmean(d[half:]) if d else None
            rows[pol]["pct_improved"] = (sum(1 for x in d if x > 0) / len(d)) if d else None
        # account realism: the same policies with one position at a time
        rows["account"] = {pol: core.account(core.score(t, sig, t.is_end, len(t), policy=pol), t)
                           for pol in ("base", "be08", "x08")}
        out[kind] = rows
    return out


# ---------------------------------------------------------------- track B
def b1_breakout(t, n=20):
    sig = []
    c = [b.c for b in t.bars]
    for i in range(n, len(t.bars)):
        if t.atr[i] is None:
            continue
        w = c[i - n:i]
        if c[i] > max(w):
            sig.append((i, 1, c[i], "brk_hi"))
        elif c[i] < min(w):
            sig.append((i, -1, c[i], "brk_lo"))
    return sig


def b2_reversion(t, n=20, k=2.0):
    sig = []
    c = [b.c for b in t.bars]
    for i in range(n, len(t.bars)):
        if t.atr[i] is None:
            continue
        w = c[i - n:i]
        m, sd = st.fmean(w), (st.stdev(w) if len(w) > 1 else 0.0)
        if sd <= 0:
            continue
        if c[i] < m - k * sd:
            sig.append((i, 1, c[i], "below"))
        elif c[i] > m + k * sd:
            sig.append((i, -1, c[i], "above"))
    return sig


def track_b(sym):
    t = core.tape(sym, 1440)
    res = {}
    for name, gen in (("B1_breakout20", b1_breakout), ("B2_reversion2sd", b2_reversion)):
        sig = gen(t)
        kw = dict(stop_atr=1.0, target_r=2.0)
        is_s = core.summary(core.score(t, sig, 0, t.is_end, **kw))
        bk = core.score(t, sig, t.is_end, len(t), **kw)
        real = core.summary(bk)
        dp = [core.direction_placebo(t, sig, t.is_end, len(t), seed=s) for s in range(10)]
        dpa = [p["avg_r"] for p in dp if p["n"]]
        sh = core.shift_placebo(t, sig, t.is_end, len(t))
        res[name] = {"is": is_s, "oos": real, "dir_placebo_avg": st.fmean(dpa) if dpa else None,
                     "dir_placebo_beaten": sum(1 for p in dp if p["n"] and real.get("n") and real["avg_r"] > p["avg_r"]),
                     "shift": sh, "z_shift": core.z_shift(real, sh),
                     "account": core.account(bk, t),
                     "span": f"{t.bars[0].ts.date()}..{t.bars[-1].ts.date()}"}
    return res


# ---------------------------------------------------------------- track C
def c_momentum(t, look=3, net=10):
    sig = []
    for i in range(max(look, net), len(t.bars)):
        if not t.rth[i] or t.last_rth[i] or t.atr[i] is None:
            continue
        hi = max(b.h for b in t.bars[i - look:i])
        lo = min(b.l for b in t.bars[i - look:i])
        d = t.bars[i].c - t.bars[i - net].c
        if t.bars[i].c > hi and d > 0:
            sig.append((i, 1, t.bars[i].c, "mom_up"))
        elif t.bars[i].c < lo and d < 0:
            sig.append((i, -1, t.bars[i].c, "mom_dn"))
    return sig


def track_c(sym="MCL"):
    res = {}
    for tf in (240, 60):
        t = core.tape(sym, tf)
        sig = c_momentum(t)
        kw = dict(stop_atr=1.0, target_r=core.TARGET_R)
        is_s = core.summary(core.score(t, sig, 0, t.is_end, **kw))
        bk = core.score(t, sig, t.is_end, len(t), **kw)
        real = core.summary(bk)
        dp = [core.direction_placebo(t, sig, t.is_end, len(t), seed=s) for s in range(10)]
        dpa = [p["avg_r"] for p in dp if p["n"]]
        sh = core.shift_placebo(t, sig, t.is_end, len(t))
        res[f"{tf}m"] = {"is": is_s, "oos": real, "dir_placebo_avg": st.fmean(dpa) if dpa else None,
                         "dir_placebo_beaten": sum(1 for p in dp if p["n"] and real.get("n") and real["avg_r"] > p["avg_r"]),
                         "shift": sh, "z_shift": core.z_shift(real, sh), "account": core.account(bk, t)}
    return res


# ---------------------------------------------------------------- track D
def va_edge_signals(t):
    """Prior RTH session's profile: tag VAH/VAL, close back inside, target the prior POC."""
    from collections import defaultdict
    byday = defaultdict(list)
    for i, b in enumerate(t.bars):
        if t.rth[i]:
            byday[t.day[i]].append(b)
    order = sorted(byday)
    prof = {}
    for k in range(1, len(order)):
        src = byday[order[k - 1]]
        if len(src) < 3:
            continue
        pf = build_profile(src)
        if pf:
            prof[order[k]] = pf
    sig, rngs, lvl = [], {}, {}
    for i in range(len(t.bars)):
        pf = prof.get(t.day[i])
        if pf is None or not t.rth[i] or t.last_rth[i] or t.atr[i] is None:
            continue
        b = t.bars[i]
        rngs[t.day[i]] = (pf.lo, pf.hi)
        lvl.setdefault(t.day[i], [(pf.vah, "VAH", -1), (pf.val, "VAL", 1)])
        if b.h >= pf.vah and b.c < pf.vah and pf.poc < pf.vah:
            sig.append((i, -1, pf.vah, "VAH", None, pf.poc))
        elif b.l <= pf.val and b.c > pf.val and pf.poc > pf.val:
            sig.append((i, 1, pf.val, "VAL", None, pf.poc))
    return sig, lvl, rngs


def track_d(sym="MGC"):
    t = core.tape(sym, 60)
    sig, lvl, rngs = va_edge_signals(t)
    is_s = core.summary(core.score(t, sig, 0, t.is_end))
    r = confirm(t, sig, {"variant": "va_edge_to_poc"}, lvl, rngs, "hint", False)
    r["is"] = is_s
    return r


# ---------------------------------------------------------------- track E (diagnostic)
def track_e(sym="MGC"):
    t = core.tape(sym, 60)
    out = {}
    for name, fr in (("golden", S.GOLDEN), ("only_0786", (0.786,))):
        lv, _rg = S.fib_levels(t, "prior_week", fr)
        sig = touch_signals(t, lv, "anti_hint")
        mkt = core.score(t, sig, t.is_end, len(t))
        for lb in (2, 4, 8):
            lim = core.score(t, sig, t.is_end, len(t), limit=True, limit_bars=lb)
            out[f"{name}_limit{lb}"] = {
                **core.summary(lim),
                "fill_rate": len(lim.trades) / max(1, len(mkt.trades)),
                "median_risk_pts": st.median([x.risk for x in lim.trades]) if lim.trades else None,
                "median_risk_usd": (st.median([x.risk for x in lim.trades]) * t.spec.point_value) if lim.trades else None,
                "account": core.account(lim, t)}
        out[f"{name}_market"] = {
            **core.summary(mkt),
            "median_risk_pts": st.median([x.risk for x in mkt.trades]) if mkt.trades else None,
            "median_risk_usd": (st.median([x.risk for x in mkt.trades]) * t.spec.point_value) if mkt.trades else None,
            "account": core.account(mkt, t)}
    return out


if __name__ == "__main__":
    res = {"bar": BAR, "n_conf": N_CONF,
           "A": {s: track_a(s) for s in core.SYMS},
           "B": {s: track_b(s) for s in ("MES", "MNQ")},
           "C": track_c("MCL"),
           "D": track_d("MGC"),
           "E": track_e("MGC")}
    (HERE / "results" / "persym1.json").write_text(json.dumps(res, indent=1, default=str))
    print(f"wrote results/persym1.json  | bar sqrt(2 ln {N_CONF}) = {BAR:.3f}")
