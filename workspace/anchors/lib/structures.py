#!/usr/bin/env python3
"""Structure builders: naked POCs (F2), Fibonacci legs (F3), merged-timeframe LVNs (F4).

Everything returned is keyed by trading day and knowable at the START of that day: the sources
are bars that had already closed. No level is ever built from the day it is traded on.
"""
from __future__ import annotations

from collections import defaultdict

from core import Tape, sessions
from vp_levels import build_profile, zigzag_legs

FIB = (0.382, 0.5, 0.618, 0.705, 0.786)
GOLDEN = (0.618, 0.705, 0.786)
SHALLOW = (0.382, 0.5)
WINDOWS = ((1, "1d"), (5, "1w"), (20, "1m"), (60, "3m"))
CONFLUENCE_ATR = 0.25
MAGNET_MIN_ATR = 1.0
REVISIT_SESSIONS = 10


def _day_bars(t: Tape, rth_only: bool):
    d = defaultdict(list)
    for i, b in enumerate(t.bars):
        if rth_only and not t.rth[i]:
            continue
        d[t.day[i]].append((i, b))
    return d


# --------------------------------------------------------------------- F2
def session_pocs(t: Tape):
    """[(formed_day, poc, lo, hi)] from each RTH session's own 60m profile."""
    out = []
    for d, items in sorted(_day_bars(t, True).items()):
        bars = [b for _i, b in items]
        if len(bars) < 3:
            continue
        pf = build_profile(bars)
        if pf:
            out.append((d, pf.poc, pf.lo, pf.hi))
    return out


def naked_pocs(t: Tape, pocs):
    """{trading_day: [(price, 'nPOC', None)]} - prior-session POCs not yet traded through, as
    known at the start of each day. Also returns the tested-by-day map for the revisit test."""
    order = [d for d, _a, _b in sessions(t)]
    pos = {d: k for k, d in enumerate(order)}
    live = []                        # [(poc, formed_day)]
    pending = {d: [] for d in order}
    for d, poc, _lo, _hi in pocs:
        pending.setdefault(d, []).append(poc)
    by_day, tested_at = {}, {}
    dbars = _day_bars(t, False)
    for d in order:
        by_day[d] = [(p, "nPOC", None) for p, _f in live]
        for _i, b in dbars.get(d, []):
            still = []
            for p, f in live:
                if b.l <= p <= b.h and f != d:
                    tested_at[(f, p)] = pos[d]
                else:
                    still.append((p, f))
            live = still
        live.extend((p, d) for p in pending.get(d, []))
    return by_day, tested_at, pos


def magnet_signals(t: Tape, npoc_by_day: dict):
    """One signal per bar: the nearest naked POC at least MAGNET_MIN_ATR away. Target IS the
    POC; stop is 1.5x the distance on the other side (the pre-registered magnet geometry)."""
    sig = []
    for i in range(len(t.bars)):
        lv = npoc_by_day.get(t.day[i])
        if not lv or t.atr[i] is None:
            continue
        c = t.bars[i].c
        cand = [p for p, _tg, _h in lv if abs(p - c) >= MAGNET_MIN_ATR * t.atr[i]]
        if not cand:
            continue
        p = min(cand, key=lambda x: abs(x - c))
        side = 1 if p > c else -1
        dist = abs(p - c)
        sig.append((i, side, p, "magnet", c - side * 1.5 * dist, p))
    return sig


def revisit_rates(t: Tape, pocs, tested_at, pos):
    """Fraction of naked POCs revisited within REVISIT_SESSIONS sessions, real vs random."""
    import random
    real_hit = real_n = 0
    for d, poc, _lo, _hi in pocs:
        if d not in pos:
            continue
        real_n += 1
        k = tested_at.get((d, poc))
        if k is not None and k - pos[d] <= REVISIT_SESSIONS:
            real_hit += 1
    # control: a uniform random price inside the same session's range, 10 draws
    order = [d for d, _a, _b in sessions(t)]
    opos = {d: k for k, d in enumerate(order)}
    dbars = _day_bars(t, False)
    ctrl_hit = ctrl_n = 0
    rng = random.Random(0)
    for d, _poc, lo, hi in pocs:
        if d not in opos or hi <= lo:
            continue
        for _ in range(10):
            p = rng.uniform(lo, hi)
            ctrl_n += 1
            k0 = opos[d]
            for dd in order[k0 + 1:k0 + 1 + REVISIT_SESSIONS]:
                if any(b.l <= p <= b.h for _i, b in dbars.get(dd, [])):
                    ctrl_hit += 1
                    break
    return {"real_n": real_n, "real_rate": real_hit / real_n if real_n else None,
            "ctrl_n": ctrl_n, "ctrl_rate": ctrl_hit / ctrl_n if ctrl_n else None}


# --------------------------------------------------------------------- F3
def _levels_from_leg(lo, hi, direction, fracs):
    """direction +1 = up leg (lo -> hi): retracements sit BELOW hi, continuation is up."""
    rng = hi - lo
    if rng <= 0:
        return []
    if direction > 0:
        return [(hi - f * rng, f, 1) for f in fracs]
    return [(lo + f * rng, f, -1) for f in fracs]


def fib_levels(t: Tape, anchoring: str, fracs) -> tuple[dict, dict]:
    """{day: [(price, tag, hint)]}, {day: (lo, hi)}."""
    order = [d for d, _a, _b in sessions(t)]
    rth = _day_bars(t, True)
    allb = _day_bars(t, False)
    out, rngs = {}, {}

    def put(d, lo, hi, direction):
        lv = _levels_from_leg(lo, hi, direction, fracs)
        if lv:
            out[d] = [(p, f"fib{f:g}", h) for p, f, h in lv]
            rngs[d] = (lo, hi)

    if anchoring == "prior_rth":
        for k in range(1, len(order)):
            prev = rth.get(order[k - 1]) or []
            if len(prev) < 3:
                continue
            bs = [b for _i, b in prev]
            put(order[k], min(b.l for b in bs), max(b.h for b in bs),
                1 if bs[-1].c > bs[0].o else -1)
        return out, rngs

    if anchoring == "prior_week":
        weeks = defaultdict(list)
        for d in order:
            weeks[t.bars[allb[d][0][0]].ts.isocalendar()[:2]].append(d)
        wk = sorted(weeks)
        for k in range(1, len(wk)):
            prev = [b for d in weeks[wk[k - 1]] for _i, b in allb[d]]
            if len(prev) < 5:
                continue
            lo, hi = min(b.l for b in prev), max(b.h for b in prev)
            direction = 1 if prev[-1].c > prev[0].o else -1
            for d in weeks[wk[k]]:
                put(d, lo, hi, direction)
        return out, rngs

    if anchoring == "overnight":
        for d in order:
            pre = [b for i, b in allb.get(d, []) if not t.rth[i] and
                   b.ts.hour >= 18 or (not t.rth[i] and b.ts.hour < min(
                       h for h in (t.bars[i].ts.hour,) ) )]
            pre = []
            for i, b in allb.get(d, []):
                if t.rth[i]:
                    break
                pre.append(b)
            if len(pre) < 5:
                continue
            put(d, min(b.l for b in pre), max(b.h for b in pre),
                1 if pre[-1].c > pre[0].o else -1)
        return out, rngs

    if anchoring == "zigzag":
        for k in range(20, len(order)):
            src = [b for d in order[k - 20:k] for _i, b in allb[d]]
            a = t.atr[allb[order[k - 1]][-1][0]]
            if a is None or len(src) < 40:
                continue
            legs = zigzag_legs(src, a)
            if not legs:
                continue
            kind, p0, p1, _t0, _t1 = legs[-1]
            lo, hi = min(p0, p1), max(p0, p1)
            put(order[k], lo, hi, 1 if kind == "UP" else -1)
        return out, rngs

    raise ValueError(anchoring)


# --------------------------------------------------------------------- F4
def merged_lvns(t: Tape):
    """{day: [(price, tag, None)]} for confluent LVNs (>=2 windows agree) and for
    single-window LVNs, plus the profile range per day."""
    order = [d for d, _a, _b in sessions(t)]
    allb = _day_bars(t, False)
    conf, single, rngs = {}, {}, {}
    maxw = max(w for w, _n in WINDOWS)
    for k in range(maxw, len(order)):
        d = order[k]
        a = t.atr[allb[order[k - 1]][-1][0]]
        if a is None:
            continue
        sets = []
        lo = hi = None
        for w, name in WINDOWS:
            src = [b for dd in order[k - w:k] for _i, b in allb[dd]]
            if len(src) < 3:
                continue
            pf = build_profile(src)
            if not pf or not pf.lvn:
                continue
            sets.append((name, pf.lvn))
            lo = pf.lo if lo is None else min(lo, pf.lo)
            hi = pf.hi if hi is None else max(hi, pf.hi)
        if not sets or lo is None:
            continue
        rngs[d] = (lo, hi)
        tol = CONFLUENCE_ATR * a
        allp = [(p, nm) for nm, ps in sets for p in ps]
        cf, sg = [], []
        for p, nm in allp:
            agree = {m for q, m in allp if abs(q - p) <= tol}
            (cf if len(agree) >= 2 else sg).append((p, f"LVN:{nm}", None))
        # de-duplicate confluent prices that are the same level seen from two windows
        cf2 = []
        for p, tg, h in sorted(cf):
            if not cf2 or abs(p - cf2[-1][0]) > tol:
                cf2.append((p, tg, h))
        conf[d] = cf2
        single[d] = sg
    return conf, single, rngs


def week_pocs(t: Tape):
    """[(first_day_of_next_week, poc, lo, hi)] from each ISO week's RTH profile."""
    order = [d for d, _a, _b in sessions(t)]
    rth = _day_bars(t, True)
    allb = _day_bars(t, False)
    weeks = defaultdict(list)
    for d in order:
        weeks[t.bars[allb[d][0][0]].ts.isocalendar()[:2]].append(d)
    wk = sorted(weeks)
    out = []
    for k in range(len(wk) - 1):
        src = [b for d in weeks[wk[k]] for _i, b in rth.get(d, [])]
        if len(src) < 10:
            continue
        pf = build_profile(src)
        if pf:
            out.append((weeks[wk[k + 1]][0], pf.poc, pf.lo, pf.hi))
    return out
