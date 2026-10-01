"""#17: fade the first DEEP LVN outside value on a rolling 5m-built profile (24/48/72 h).

Pre-registered 2026-09-30 21:40 ET in workspace/paper/CALL/research/PREREG_2026-09-30_lvn.md, before
this file was run. Profile maths is copied verbatim from workspace/paper/CALL/preopen.py (profile +
summarize) so the desk map and this test agree.

  level   U = first LVN above VAH with depth < 0.35; D = first LVN below VAL with depth < 0.35,
          from the profile as of the PREVIOUS 15m bar's close (5m bars closed by then, last H hours)
  arming  a 15m close inside value arms both sides; a close at/above U disarms up, at/below D disarms
          down; a signal disarms its side until the next inside-value close
  A1      resting limit at U (SHORT) / D (LONG), live <= 16 bars after the latest arming close
  A2      bar touches U (D) and closes back inside value -> market order at the next open
  stop    LVN +/- (0.25 ATR14 + 1 tick), target 1.8 R from the fill, 16-bar time exit

Because A1 needs limit fills and every variant has a 16-bar time exit, this rule runs through
workspace/paper/CALL/research/run_lvn_2026-09-30.py, which imports walkforward.py's fills, sizing,
costs and scoring and adds only those two things. `signals()` is the causal rule.
"""
from __future__ import annotations

import datetime as dt
import random

NAME = "LVN17_deep_first_lvn_fade"
WARMUP = 0
USES_LEVELS = True
PREREG = {"family": "LVN1718", "trials": 90,
          "text": "Fade the first LVN outside value (depth<0.35) on rolling 24/48/72h 5m profiles, arriving "
                  "from inside value; A1 limit at LVN, A2 15m touch+close back inside then next open; stop LVN "
                  "+-(0.25ATR+1tick), target 1.8R, 16-bar time exit; MGC MNQ MES MCL 15m; all/stacked/not; "
                  "6 variants x 5 (4 symbols+pooled) x 3 subsets = 90 trials."}

BIN = {"MNQ": 5.0, "MGC": 1.0, "MES": 1.0, "MCL": 0.02}
DEPTH_MAX = 0.35
STOP_ATR = 0.25
TARGET_R = 1.8
LIMIT_LIFE = 16
WINDOWS = (24, 48, 72)


# ---------------------------------------------------------------- verbatim from preopen.py
def profile(bars, step):
    vol = {}
    for b in bars:
        lo, hi, v = b["l"], b["h"], float(b.get("v") or 0)
        if v <= 0:
            continue
        k0, k1 = int(lo // step), int(hi // step)
        n = k1 - k0 + 1
        for k in range(k0, k1 + 1):
            vol[k] = vol.get(k, 0.0) + v / n
    return vol


def summarize(vol, step):
    ks = sorted(vol)
    tot = sum(vol.values())
    poc = max(vol, key=vol.get)
    lo = hi = poc
    acc = vol[poc]
    while acc < 0.7 * tot and (lo > ks[0] or hi < ks[-1]):
        dn = vol.get(lo - 1, 0.0) if lo > ks[0] else -1
        up = vol.get(hi + 1, 0.0) if hi < ks[-1] else -1
        if up >= dn:
            hi += 1; acc += max(up, 0)
        else:
            lo -= 1; acc += max(dn, 0)
    sm = {k: (vol.get(k - 1, 0) + vol.get(k, 0) + vol.get(k + 1, 0)) / 3 for k in ks}
    pv = vol[poc]
    lvns = []
    for k in ks[2:-2]:
        if sm[k] < sm[k - 1] and sm[k] <= sm[k + 1] and sm[k] < 0.5 * pv:
            left = max(sm[j] for j in ks if j < k)
            right = max(sm[j] for j in ks if j > k)
            if left > 1.5 * sm[k] and right > 1.5 * sm[k]:
                lvns.append(k)
    mid = lambda k: round((k + 0.5) * step, 2)
    W = 25
    scored = []
    for k in lvns:
        lp = max(sm.get(j, 0) for j in range(k - W, k))
        rp = max(sm.get(j, 0) for j in range(k + 1, k + W + 1))
        depth = sm[k] / max(1e-9, min(lp, rp))
        side = "above value" if k > hi else ("below value" if k < lo else "inside value")
        scored.append({"price": mid(k), "depth": round(depth, 2), "where": side})
    outside = [x for x in scored if x["where"] != "inside value"]
    first_up = min((x for x in outside if x["where"] == "above value"), key=lambda x: x["price"], default=None)
    first_dn = max((x for x in outside if x["where"] == "below value"), key=lambda x: x["price"], default=None)
    return {"poc": mid(poc), "vah": round((hi + 1) * step, 2), "val": round(lo * step, 2),
            "lvns": [mid(k) for k in lvns], "lvn_scored": scored, "first_lvn_above": first_up,
            "first_lvn_below": first_dn, "range": (round(ks[0] * step, 2), round((ks[-1] + 1) * step, 2))}
# ---------------------------------------------------------------- end verbatim


def profiles_by_bar(bars15, bars5, sym, hours):
    """summary[i] = profile of 5m bars that CLOSED by 15m bar i's close and opened within the last
    `hours` hours of it. Built from the same slice preopen.py would use; recomputed every bar."""
    step = BIN[sym]
    t5 = [dt.datetime.fromisoformat(b["ts"]) for b in bars5]
    out, a, z = [], 0, 0
    five = dt.timedelta(minutes=5)
    for b in bars15:
        close = dt.datetime.fromisoformat(b["ts"]) + dt.timedelta(minutes=15)
        while z < len(bars5) and t5[z] + five <= close:
            z += 1
        start = close - dt.timedelta(hours=hours)
        while a < z and t5[a] < start:
            a += 1
        w = bars5[a:z]
        vol = profile(w, step) if w else {}
        if vol:  # zero-fill empty bins inside the range: preopen's summarize indexes k+-1 (KeyError on gaps)
            vol = {k: vol.get(k, 0.0) for k in range(min(vol), max(vol) + 1)}
        out.append(summarize(vol, step) if vol else None)
    return out


def _qualifying(s):
    up = s["first_lvn_above"] if s and s["first_lvn_above"] and s["first_lvn_above"]["depth"] < DEPTH_MAX else None
    dn = s["first_lvn_below"] if s and s["first_lvn_below"] and s["first_lvn_below"]["depth"] < DEPTH_MAX else None
    return (up["price"] if up else None), (dn["price"] if dn else None)


def signals(bars, summaries, atr, tick, variant, level_seed=None):
    """Causal events {i: event}. A1 events: a limit FILLS on bar i at `limit`. A2 events: decided at
    bar i's close, market order for bar i+1's open. Levels come from summaries[i-1]."""
    ev = {}
    armed_up = armed_dn = False
    arm_i = None
    for i in range(1, len(bars)):
        s = summaries[i - 1]
        b = bars[i]
        if s is None or atr(i) is None:
            continue
        U, D = _qualifying(s)
        if level_seed is not None:
            hour = b["ts"][:13]
            rng = random.Random(f"{level_seed}:{hour}")
            ru, rd = rng.random(), rng.random()
            U = s["vah"] + ru * (s["range"][1] - s["vah"]) if U is not None else None
            D = s["range"][0] + rd * (s["val"] - s["range"][0]) if D is not None else None
        vah, val = s["vah"], s["val"]
        a = atr(i - 1) if variant == "A1" else atr(i)
        if variant == "A1":
            live = arm_i is not None and i - arm_i <= LIMIT_LIFE
            hit_up = live and armed_up and U is not None and b["h"] >= U
            hit_dn = live and armed_dn and D is not None and b["l"] <= D
            if hit_up and hit_dn:
                armed_up = armed_dn = False
            elif hit_up and a:
                ev[i] = {"side": "SHORT", "limit": U, "stop": U + STOP_ATR * a + tick, "level": U,
                         "why": f"A1 limit at LVN {U} (VAH {vah})"}
                armed_up = False
            elif hit_dn and a:
                ev[i] = {"side": "LONG", "limit": D, "stop": D - STOP_ATR * a - tick, "level": D,
                         "why": f"A1 limit at LVN {D} (VAL {val})"}
                armed_dn = False
        else:  # A2 confirmation
            inside = val <= b["c"] <= vah
            if armed_up and U is not None and b["h"] >= U and inside:
                ev[i] = {"side": "SHORT", "stop": U + STOP_ATR * a + tick, "level": U,
                         "why": f"A2 touch LVN {U}, close {b['c']} back inside (VAH {vah})"}
                armed_up = False
            elif armed_dn and D is not None and b["l"] <= D and inside:
                ev[i] = {"side": "LONG", "stop": D - STOP_ATR * a - tick, "level": D,
                         "why": f"A2 touch LVN {D}, close {b['c']} back inside (VAL {val})"}
                armed_dn = False
        # arming / disarming from this bar's close (profile as of the previous close)
        if val <= b["c"] <= vah:
            if i not in ev:
                armed_up = armed_dn = True
            arm_i = i
        if U is not None and b["c"] >= U:
            armed_up = False
        if D is not None and b["c"] <= D:
            armed_dn = False
    return ev
