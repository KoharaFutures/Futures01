#!/usr/bin/env python3
"""H1 anchor construction: seven anchoring methodologies, O(1) AVWAP/sigma via prefix sums."""
from __future__ import annotations

import math

from core import Tape, sessions, fractal_pivots

MIN_SINCE_ANCHOR = 5          # bars needed before an AVWAP/sigma is usable
TRAIL_SESSIONS = 20           # lookback for the high-volume / wide-range anchors

ANCHOR_NAMES = ("rth_open", "globex_open", "week_open", "month_open",
                "hi_vol_bar", "wide_bar", "swing_pivot")


def prefixes(t: Tape):
    n = len(t.bars)
    cv = [0.0] * (n + 1)
    cp = [0.0] * (n + 1)
    cq = [0.0] * (n + 1)
    for i, r in enumerate(t.bars):
        v = r.v or 0.0
        tp = (r.h + r.l + r.c) / 3.0
        cv[i + 1] = cv[i] + v
        cp[i + 1] = cp[i] + v * tp
        cq[i + 1] = cq[i] + v * tp * tp
    return cv, cp, cq


def band(pre, a: int, i: int):
    """(mean, sigma) of the volume-weighted typical price over bars [a, i]."""
    cv, cp, cq = pre
    sv = cv[i + 1] - cv[a]
    if sv <= 0:
        return None
    m = (cp[i + 1] - cp[a]) / sv
    var = (cq[i + 1] - cq[a]) / sv - m * m
    return m, math.sqrt(var) if var > 0 else 0.0


def anchor_index(t: Tape, kind: str) -> list:
    """anchor_idx[i] = the bar index the AVWAP is anchored at, as known at bar i (no lookahead)."""
    n = len(t.bars)
    out = [None] * n
    sess = sessions(t)

    if kind == "globex_open":
        for _d, a, b in sess:
            for i in range(a, b + 1):
                out[i] = a
        return out

    if kind == "rth_open":
        for _d, a, b in sess:
            first = next((i for i in range(a, b + 1) if t.rth[i]), None)
            if first is None:
                continue
            for i in range(first, b + 1):
                out[i] = first
        return out

    if kind in ("week_open", "month_open"):
        cur = None
        key = None
        for _d, a, b in sess:
            ts = t.bars[a].ts
            k = ts.isocalendar()[:2] if kind == "week_open" else (ts.year, ts.month)
            if k != key:
                key, cur = k, a
            for i in range(a, b + 1):
                out[i] = cur
        return out

    if kind in ("hi_vol_bar", "wide_bar"):
        f = (lambda r: (r.v or 0.0)) if kind == "hi_vol_bar" else (lambda r: r.h - r.l)
        cur = None
        for s in range(len(sess)):
            _d, a, b = sess[s]
            lo = sess[max(0, s - TRAIL_SESSIONS)][1]
            if a > lo:
                cur = max(range(lo, a), key=lambda j: f(t.bars[j]))
            for i in range(a, b + 1):
                out[i] = cur
        return out

    if kind == "swing_pivot":
        piv = sorted(fractal_pivots(t, k=2))
        p = 0
        cur = None
        for i in range(n):
            while p < len(piv) and piv[p][0] <= i:
                cur = piv[p][3]
                p += 1
            out[i] = cur
        return out

    raise ValueError(kind)


def band_signals(t: Tape, pre, aidx: list, k: float, retest_only: bool = False,
                 min_since: int = MIN_SINCE_ANCHOR):
    """Tag AVWAP +- k*sigma and close back inside -> enter toward the AVWAP.
    k == 0 means the AVWAP line itself (touch and close on one side)."""
    sig = []
    touched: dict = {}
    for i in range(len(t.bars)):
        a = aidx[i]
        if a is None or i - a < min_since:
            continue
        bd = band(pre, a, i)
        if bd is None:
            continue
        m, s = bd
        r = t.bars[i]
        if k == 0:
            if not (r.l <= m <= r.h):
                continue
            seen = touched.get(a, 0)
            touched[a] = seen + 1
            if retest_only and seen == 0:
                continue
            side = 1 if r.c > m else -1
            sig.append((i, side, m, "avwap"))
            continue
        if s <= 0:
            continue
        up, dn = m + k * s, m - k * s
        if r.h >= up and r.c < up:
            seen = touched.get((a, "u"), 0)
            touched[(a, "u")] = seen + 1
            if not (retest_only and seen == 0):
                sig.append((i, -1, up, f"+{k:g}s"))
        if r.l <= dn and r.c > dn:
            seen = touched.get((a, "d"), 0)
            touched[(a, "d")] = seen + 1
            if not (retest_only and seen == 0):
                sig.append((i, 1, dn, f"-{k:g}s"))
    return sig


def band_break_signals(t: Tape, pre, aidx: list, k: float, min_since: int = MIN_SINCE_ANCHOR):
    """The INVERSE of band_signals: a bar CLOSES through AVWAP +- k*sigma -> go with the break.
    Formed after the fade arms came back reliably negative on in-sample; see REPORT.md 4.1."""
    sig = []
    for i in range(1, len(t.bars)):
        a = aidx[i]
        if a is None or i - a < min_since:
            continue
        bd = band(pre, a, i)
        if bd is None:
            continue
        m, s_ = bd
        if k > 0 and s_ <= 0:
            continue
        r, pc = t.bars[i], t.bars[i - 1].c
        up, dn = m + k * s_, m - k * s_
        if pc <= up < r.c:
            sig.append((i, 1, up, f"brk+{k:g}s"))
        elif pc >= dn > r.c:
            sig.append((i, -1, dn, f"brk-{k:g}s"))
    return sig
