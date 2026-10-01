#!/usr/bin/env python3
"""ANCH1 shared harness: one loader, one profile/anchor toolkit, ONE scoring engine.

Everything in `workspace/anchors/run_*.py` scores through `score()` here, so no family can win
by having a friendlier exit. See `workspace/anchors/HYPOTHESES.md` for the pre-registration this
implements; the numbers in §2 of that file are the constants at the top of this module.
"""
from __future__ import annotations

import math
import pathlib
import random
import statistics as st
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "DATA_HUB" / "tools"))
from futures_agents.config import get_contract              # noqa: E402
from bounce_levels import load, tday, atr_series            # noqa: E402
from vp_levels import build_profile, Profile                # noqa: E402

SYMS = ("MES", "MNQ", "MGC", "MCL")
# RTH hours on 60m bars, from each contract spec's rth_open/rth_close (ET).
RTH_HOURS = {"MES": range(9, 16), "MNQ": range(9, 16), "MGC": range(8, 14), "MCL": range(9, 15)}
STOP_ATR = 0.5          # stop sits 0.5 ATR + 1 tick beyond the level
TARGET_R = 1.5          # one target geometry for every arm
HOLD = 12               # time exit, in bars
BE_TRIGGER = 0.8        # PERSYM1 track A: move the stop to breakeven at +0.8R
IS_FRAC = 0.60          # in-sample = first 60% of bars
N_PLACEBO_SEEDS = 10
N_SHIFTS = 200

ACCOUNT = 50_000.0
FLOOR_DD = 2_800.0
RISK_CAP = 120.0        # halved budget while nothing is proven (RULES_AND_PITFALLS Part A)


# ----------------------------------------------------------------- data layer
@dataclass
class Tape:
    sym: str
    bars: list
    atr: list
    day: list            # trading day per bar
    rth: list            # bool: inside the symbol's measured session
    close_bar: list      # bool: last RTH bar of its trading day
    last_rth: list       # bool: final RTH hour (no new entries)
    spec: object
    tick: float
    cost_pts: float
    min_stop: float
    bin_w: float
    is_end: int          # first OOS index
    tf: int = 60
    hold: int = HOLD

    def __len__(self):
        return len(self.bars)


def tape(sym: str, tf: int = 60) -> Tape:
    """tf 60 or 240 = intraday (RTH gating applies). tf 1440 = daily: every bar is its own
    session, so there is no 'last RTH hour' and no intraday session exit."""
    bars = load(sym, tf)
    atr = atr_series(bars)
    spec = get_contract(sym)
    day = [tday(b.ts) for b in bars]
    if tf >= 240:
        # swing timeframes: no intraday gating, no session exit (HYPOTHESES_PERSYM1.md 5b)
        rth = [True] * len(bars)
        bin_ticks = max(1, round(0.02 * spec.typical_atr_points / spec.tick_size))
        return Tape(sym=sym, bars=bars, atr=atr, day=day, rth=rth,
                    close_bar=[False] * len(bars), last_rth=[False] * len(bars), spec=spec,
                    tick=spec.tick_size,
                    cost_pts=2 * (spec.commission_per_side + spec.exchange_fee_per_side) / spec.point_value,
                    min_stop=spec.min_stop_ticks * spec.tick_size,
                    bin_w=bin_ticks * spec.tick_size, is_end=int(IS_FRAC * len(bars)),
                    tf=tf, hold=(10 if tf >= 1440 else HOLD))
    hours = RTH_HOURS[sym]
    rth = [b.ts.hour in hours for b in bars]
    # last RTH bar of each trading day, and the final RTH hour of each trading day
    last_idx: dict = {}
    for i, b in enumerate(bars):
        if rth[i]:
            last_idx[day[i]] = i
    close_bar = [False] * len(bars)
    last_rth = [False] * len(bars)
    for i in last_idx.values():
        close_bar[i] = True
        last_rth[i] = True
    # bin width ~2% of a typical ATR, rounded to whole ticks (>=1)
    bin_ticks = max(1, round(0.02 * spec.typical_atr_points / spec.tick_size))
    return Tape(sym=sym, bars=bars, atr=atr, day=day, rth=rth, close_bar=close_bar,
                last_rth=last_rth, spec=spec, tick=spec.tick_size,
                cost_pts=2 * (spec.commission_per_side + spec.exchange_fee_per_side) / spec.point_value,
                min_stop=spec.min_stop_ticks * spec.tick_size,
                bin_w=bin_ticks * spec.tick_size,
                is_end=int(IS_FRAC * len(bars)), tf=tf, hold=HOLD)


def sessions(t: Tape) -> list[tuple]:
    """[(trading_day, first_idx, last_idx)] over ALL bars of the day (Globex included)."""
    bounds: dict = {}
    for i, d in enumerate(t.day):
        lo, hi = bounds.get(d, (i, i))
        bounds[d] = (min(lo, i), max(hi, i))
    return sorted((d, a, b) for d, (a, b) in bounds.items())


# ------------------------------------------------------------ anchored VWAP
def avwap(t: Tape, a: int, b: int) -> tuple[float, float] | None:
    """Volume-weighted mean typical price and its volume-weighted sd over bars [a, b]."""
    sv = sp = 0.0
    for i in range(a, b + 1):
        r = t.bars[i]
        v = r.v or 0.0
        if v <= 0:
            continue
        tp = (r.h + r.l + r.c) / 3.0
        sv += v
        sp += v * tp
    if sv <= 0:
        return None
    m = sp / sv
    sq = sum((r.v or 0.0) * (((r.h + r.l + r.c) / 3.0) - m) ** 2 for r in t.bars[a:b + 1])
    return m, math.sqrt(sq / sv)


def fractal_pivots(t: Tape, k: int = 2) -> list[tuple]:
    """(known_from_index, kind, price, bar_index). A pivot at j is confirmed once bar j+k closes."""
    out = []
    h = [r.h for r in t.bars]
    lo = [r.l for r in t.bars]
    for j in range(k, len(t.bars) - k):
        if h[j] == max(h[j - k:j + k + 1]):
            out.append((j + k + 1, "H", h[j], j))
        if lo[j] == min(lo[j - k:j + k + 1]):
            out.append((j + k + 1, "L", lo[j], j))
    return out


# ---------------------------------------------------------------- the engine
@dataclass
class Trade:
    i: int                  # signal bar (entry is i+1's open)
    side: int               # +1 long, -1 short
    fill: float
    stop: float
    risk: float
    exit_i: int
    exit_px: float
    why: str
    r: float
    tag: str = ""


@dataclass
class Book:
    trades: list = field(default_factory=list)
    signals: int = 0
    skipped_late: int = 0
    skipped_overlap: int = 0
    skipped_nodata: int = 0


def _walk(t: Tape, i: int, side: int, level: float,
          stop_px: float | None = None, target_px: float | None = None,
          policy: str = "base", target_r: float = TARGET_R,
          limit_px: float | None = None, limit_bars: int = 0,
          stop_atr: float = STOP_ATR) -> Trade | None:
    """Enter at bar i+1's open +- 1 adverse tick. Default geometry: stop is `level` displaced
    STOP_ATR*ATR + 1 tick, target 1.5R. `stop_px`/`target_px` override it (used only by the
    pre-registered naked-POC magnet arm, whose target IS the level)."""
    j = i + 1
    if j >= len(t.bars) or t.atr[i] is None:
        return None
    if limit_px is not None:
        # a resting limit: filled only if a later bar trades through it, within limit_bars
        hit = None
        for k in range(j, min(j + max(1, limit_bars), len(t.bars))):
            b = t.bars[k]
            if (side > 0 and b.l <= limit_px) or (side < 0 and b.h >= limit_px):
                hit = k
                break
            if t.close_bar[k]:
                break
        if hit is None:
            return None
        j = hit
        fill = limit_px          # a resting limit pays no adverse tick; it pays non-fills instead
    else:
        fill = t.bars[j].o + side * t.tick
    off = stop_atr * t.atr[i] + t.tick
    stop = (level - side * off) if stop_px is None else stop_px
    risk = abs(fill - stop)
    if risk < t.min_stop:
        risk = t.min_stop
        stop = fill - side * risk
    if policy == "x08":
        target_r = BE_TRIGGER
    target = (fill + side * target_r * risk) if target_px is None else target_px
    if side * (target - fill) <= 0:
        return None
    be_level = fill + side * BE_TRIGGER * risk
    armed = False
    for k in range(j, min(j + t.hold, len(t.bars))):
        b = t.bars[k]
        hit_s = (b.l <= stop) if side > 0 else (b.h >= stop)
        hit_t = (b.h >= target) if side > 0 else (b.l <= target)
        if limit_px is not None and k == j:
            # A resting limit fills mid-bar and an OHLC bar does not say whether the high came
            # before or after the low. Crediting the target on the fill bar assumes the favourable
            # ordering; 50.3% of trades took it that way and it was worth ~0.4R of pure artefact.
            # Allow only the adverse outcome on the fill bar.
            hit_t = False
        if hit_s:                               # the stop wins a same-bar tie
            return _mk(t, i, side, fill, stop, risk, k, stop, "be" if armed else "stop")
        if hit_t:
            return _mk(t, i, side, fill, stop, risk, k, target, "target")
        if t.close_bar[k]:
            return _mk(t, i, side, fill, stop, risk, k, b.c, "session")
        if policy == "be08" and not armed:
            # arm only on a bar that reached +0.8R without touching the stop; effective next bar
            if (b.h >= be_level) if side > 0 else (b.l <= be_level):
                armed, stop = True, fill
    k = min(j + t.hold, len(t.bars)) - 1
    return _mk(t, i, side, fill, stop, risk, k, t.bars[k].c, "time")


def _mk(t, i, side, fill, stop, risk, k, px, why) -> Trade:
    r = (side * (px - fill) - t.cost_pts) / risk
    return Trade(i, side, fill, stop, risk, k, px, why, r)


def score(t: Tape, signals, lo: int, hi: int, one_at_a_time: bool = True,
          policy: str = "base", target_r: float = TARGET_R,
          limit: bool = False, limit_bars: int = 0,
          stop_atr: float = STOP_ATR) -> Book:
    """signals: iterable of (bar_index, side, level, tag), scored on bars [lo, hi)."""
    bk = Book()
    free = -1
    for sg in sorted(signals, key=lambda s: s[0]):
        i, side, level, tag = sg[0], sg[1], sg[2], sg[3]
        stop_px = sg[4] if len(sg) > 4 else None
        target_px = sg[5] if len(sg) > 5 else None
        if not (lo <= i < hi):
            continue
        bk.signals += 1
        if t.last_rth[i] or not t.rth[i]:
            bk.skipped_late += 1
            continue
        if one_at_a_time and i <= free:
            bk.skipped_overlap += 1
            continue
        tr = _walk(t, i, side, level, stop_px, target_px, policy, target_r,
                   (level if limit else None), limit_bars, stop_atr)
        if tr is None:
            bk.skipped_nodata += 1
            continue
        tr.tag = tag
        bk.trades.append(tr)
        free = tr.exit_i
    return bk


# ------------------------------------------------------------------- statistics
def summary(bk: Book) -> dict:
    rs = [x.r for x in bk.trades]
    n = len(rs)
    if n == 0:
        return {"n": 0}
    m = st.fmean(rs)
    sd = st.stdev(rs) if n > 1 else 0.0
    wins = [x for x in rs if x > 0]
    losses = [-x for x in rs if x <= 0]
    half = n // 2
    return {
        "n": n, "avg_r": m, "sd": sd,
        "t": (m / (sd / math.sqrt(n))) if sd > 0 else None,
        "win": len(wins) / n,
        "payoff": (st.fmean(wins) / st.fmean(losses)) if wins and losses else None,
        "h1": st.fmean(rs[:half]) if half else None,
        "h2": st.fmean(rs[half:]) if n - half else None,
        "exits": dict(sorted(defaultdict(int, {w: sum(1 for x in bk.trades if x.why == w)
                                               for w in {x.why for x in bk.trades}}).items())),
        "signals": bk.signals, "late": bk.skipped_late,
        "overlap": bk.skipped_overlap, "nodata": bk.skipped_nodata,
    }


def direction_placebo(t: Tape, signals, lo, hi, seed=0) -> dict:
    rng = random.Random(seed)
    flip = [(sg[0], (1 if rng.random() < 0.5 else -1), sg[2], sg[3], *sg[4:]) for sg in signals]
    return summary(score(t, flip, lo, hi))


def shift_placebo(t: Tape, signals, lo, hi, n_shifts=N_SHIFTS, seed=7) -> dict:
    """Circularly shift the entry TIMES, keep side and geometry. 'Random entries, same exits,
    same bars' - but it preserves the clustering of the real signal set, which a plain
    permutation destroys."""
    sig = [s for s in signals if lo <= s[0] < hi]
    if not sig:
        return {"n": 0}
    span = hi - lo
    rng = random.Random(seed)
    means = []
    for _ in range(n_shifts):
        d = rng.randrange(1, span)
        sh = []
        for sg in sig:
            i, side, tag = sg[0], sg[1], sg[3]
            k = lo + ((i - lo + d) % span)
            if len(sg) > 5 and sg[5] is not None:
                # magnet geometry: keep the distance-to-target, re-sited on the shifted bar
                dist = abs(sg[5] - t.bars[sg[0] + 1].o) if sg[0] + 1 < len(t.bars) else None
                if dist is None:
                    continue
                base = t.bars[k].c
                sh.append((k, side, base, tag, base - side * 1.5 * dist, base + side * dist))
            else:
                sh.append((k, side, t.bars[k].c, tag))   # level becomes that bar's close
        s = summary(score(t, sh, lo, hi))
        if s["n"]:
            means.append(s["avg_r"])
    if len(means) < 10:
        return {"n": 0}
    mu, sd = st.fmean(means), st.stdev(means)
    return {"n": len(means), "mean": mu, "sd": sd, "p95": sorted(means)[int(0.95 * len(means))]}


def z_vs(real: dict, ctrl: dict) -> float | None:
    if not real.get("n") or not ctrl.get("n") or real["n"] < 2:
        return None
    sd = ctrl.get("sd")
    if sd is None or sd <= 0:
        return None
    se = math.sqrt(real["sd"] ** 2 / real["n"] + sd ** 2 / ctrl["n"])
    return (real["avg_r"] - ctrl["avg_r"]) / se if se > 0 else None


def z_shift(real: dict, sh: dict) -> float | None:
    if not real.get("n") or not sh.get("n") or not sh.get("sd"):
        return None
    return (real["avg_r"] - sh["mean"]) / sh["sd"]


def luck_bar(n_trials: int) -> float:
    return math.sqrt(2 * math.log(max(2, n_trials)))


def account(bk: Book, t: Tape) -> dict:
    """One contract where the risk budget allows it; report refusals rather than hiding them."""
    eq, peak, maxdd, taken, refused = ACCOUNT, ACCOUNT, 0.0, 0, 0
    for x in sorted(bk.trades, key=lambda x: x.i):
        room = eq - (ACCOUNT - FLOOR_DD)
        budget = min(0.06 * room, 0.0075 * eq, 500.0, RISK_CAP)
        if room <= 0 or x.risk * t.spec.point_value > budget:
            refused += 1
            continue
        eq += x.r * x.risk * t.spec.point_value
        taken += 1
        peak = max(peak, eq)
        maxdd = max(maxdd, peak - eq)
    return {"end_equity": round(eq, 2), "max_dd": round(maxdd, 2), "taken": taken, "refused": refused}
