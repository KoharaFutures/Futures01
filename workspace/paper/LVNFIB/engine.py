#!/usr/bin/env python3
"""LVN/FIB AGENT — level engine. Builds today's arm-A..D structures for MGC and MNQ.

Every level is returned with the timestamp of the bar it was computed from, so nothing can be
quoted as "current" by accident (CHARTER.md §4). Reads data/archive/ only; never writes there.
"""
from __future__ import annotations

import pathlib
import sys
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "DATA_HUB" / "tools"))
sys.path.insert(0, str(ROOT / "workspace" / "anchors" / "lib"))
import core                                              # noqa: E402
import structures as S                                   # noqa: E402
from vp_levels import build_profile                      # noqa: E402

SYMS = ("MGC", "MNQ")
ENTRY_HOURS = {"MGC": range(8, 13), "MNQ": range(9, 15)}   # last session hour excluded
STACK_ATR = 0.25
VOL_STANDDOWN = {"MGC": 10.0, "MNQ": 58.0}                 # ATR14 on 15m


def _weeks(t):
    byday = defaultdict(list)
    for i, b in enumerate(t.bars):
        byday[t.day[i]].append((i, b))
    order = sorted(byday)
    wk = defaultdict(list)
    for d in order:
        wk[t.bars[byday[d][0][0]].ts.isocalendar()[:2]].append(d)
    return byday, order, wk


def arm_a_levels(t, plan_week=None):
    """Prior calendar week's golden pocket, with the direction of that week.

    `plan_week` is the ISO (year, week) the desk is planning FOR; the levels come from the last
    complete week strictly before it. It defaults to the week of the newest visible bar, which is
    right whenever the desk runs during a session. It is NOT right if the desk runs after a week
    has ended but before the next week's first bar has printed (a Sunday afternoon, say) - then
    keys[-1] is still the finished week and the default would reach a week too far back. A self-test
    over 488 trading days caught exactly that: 99 days took the week-before-the-prior-week.
    Callers planning across a week boundary must pass `plan_week`.
    """
    byday, order, wk = _weeks(t)
    keys = sorted(wk)
    if len(keys) < 2:
        return None
    if plan_week is None:
        plan_week = keys[-1]
    prior = [k for k in keys if k < plan_week]
    if not prior:
        return None
    prev = [b for d in wk[prior[-1]] for _i, b in byday[d]]
    if len(prev) < 5:
        return None
    lo, hi = min(b.l for b in prev), max(b.h for b in prev)
    up = prev[-1].c > prev[0].o
    rng = hi - lo
    lv = [(hi - f * rng if up else lo + f * rng, f) for f in S.GOLDEN]
    return {"week": f"{prior[-1][0]}-W{prior[-1][1]:02d}", "lo": lo, "hi": hi,
            "direction": "UP" if up else "DOWN",
            "source_bar": prev[-1].ts.isoformat(),
            "levels": [{"price": round(p, 4), "frac": f,
                        "trade_side": ("SHORT" if up else "LONG")} for p, f in lv]}


def arm_b_levels(t):
    """Most recent completed overnight (Globex-to-RTH) range, shallow fibs."""
    byday, order, _wk = _weeks(t)
    for d in reversed(order):
        pre = []
        for i, b in byday[d]:
            if t.rth[i]:
                break
            pre.append(b)
        if len(pre) < 5:
            continue
        lo, hi = min(b.l for b in pre), max(b.h for b in pre)
        up = pre[-1].c > pre[0].o
        rng = hi - lo
        if rng <= 0:
            continue
        lv = [(hi - f * rng if up else lo + f * rng, f) for f in S.SHALLOW]
        return {"session": str(d), "lo": lo, "hi": hi, "direction": "UP" if up else "DOWN",
                "source_bar": pre[-1].ts.isoformat(),
                "levels": [{"price": round(p, 4), "frac": f,
                            "trade_side": ("SHORT" if up else "LONG")} for p, f in lv]}
    return None


def arm_d_levels(t, sessions_back=5):
    """LVNs of the 1-week (5-session) 60m profile, plus POC and value area."""
    byday, order, _wk = _weeks(t)
    src = [b for d in order[-sessions_back:] for _i, b in byday[d]]
    if len(src) < 10:
        return None
    pf = build_profile(src)
    if not pf:
        return None
    return {"window": f"{sessions_back} sessions", "source_bar": src[-1].ts.isoformat(),
            "poc": round(pf.poc, 4), "vah": round(pf.vah, 4), "val": round(pf.val, 4),
            "lvn": [round(p, 4) for p in pf.lvn], "hvn": [round(p, 4) for p in pf.hvn],
            "shape": pf.shape}


def stacked(price, others, atr):
    return [round(q, 4) for q in others if q != price and abs(q - price) <= STACK_ATR * atr]


def snapshot(sym, plan_week=None):
    t = core.tape(sym, 60)
    last = t.bars[-1]
    atr = next((a for a in reversed(t.atr) if a is not None), None)
    t15 = core.tape(sym, 15) if (ROOT / "data" / "archive" / f"{sym}_15m.jsonl").exists() else None
    atr15 = next((a for a in reversed(t15.atr) if a is not None), None) if t15 else None
    a, b, dd = arm_a_levels(t, plan_week), arm_b_levels(t), arm_d_levels(t)
    pool = ([x["price"] for x in a["levels"]] if a else []) + \
           ([x["price"] for x in b["levels"]] if b else []) + \
           ((dd["lvn"] + [dd["poc"], dd["vah"], dd["val"]]) if dd else [])
    for grp in (a, b):
        if grp:
            for x in grp["levels"]:
                x["stacked_with"] = stacked(x["price"], pool, atr or 1.0)
    return {"symbol": sym, "newest_bar": last.ts.isoformat(), "newest_close": last.c,
            "atr14_60m": round(atr, 4) if atr else None,
            "atr14_15m": round(atr15, 4) if atr15 else None,
            "vol_standdown_threshold": VOL_STANDDOWN[sym],
            "vol_standdown_active": bool(atr15 and atr15 > VOL_STANDDOWN[sym]),
            "arm_A_prior_week_golden": a, "arm_B_overnight_shallow": b,
            "arm_D_1week_profile": dd,
            "contract": {"tick": t.tick, "point_value": t.spec.point_value,
                         "min_stop_ticks": t.spec.min_stop_ticks,
                         "round_turn_cost_pts": round(t.cost_pts, 4)}}


if __name__ == "__main__":
    import json
    out = {s: snapshot(s) for s in SYMS}
    print(json.dumps(out, indent=1, default=str))
