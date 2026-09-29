#!/usr/bin/env python3
"""Bounce-level scanner: which price levels hold, how often, and WHY - measured against a placebo.

For every symbol it
  1. builds the level map a trader would have had at each bar, using only past data:
     prior-day high/low/close (PDH/PDL/PDC), prior RTH high/low, prior-day volume POC and
     VWAP, prior-week high/low, overnight high/low (RTH bars only), confirmed 60m swing
     highs/lows, and round numbers;
  2. detects every fresh touch (price was >= ARM ATRs away, then returned to the level);
  3. simulates the bounce trade - limit at the level, stop STOP_ATR beyond it, target
     TARGET_R x risk - with next-bar-unknown rules: the stop wins any bar where both are
     touched, the fill bar can only lose, costs from futures_agents.config are charged;
  4. runs the identical pipeline on PLACEBO levels (each real level shifted by a random
     0.75-3 ATR, same bars, same exits) so "levels bounce" is compared with "any price
     bounces", which is the comparison the repo's earlier breach scanner failed;
  5. breaks results down by the reasons a level should hold - confluence, first touch vs
     retest, trend alignment, session, approach speed, volatility - each against placebo;
  6. lists the CURRENT levels near price with their measured history and the reasons.

    python3 DATA_HUB/tools/bounce_levels.py                       # all symbols, 5m and 60m
    python3 DATA_HUB/tools/bounce_levels.py --symbols MNQ --tf 5
    python3 DATA_HUB/tools/bounce_levels.py --out DATA_HUB/levels

Writes <out>/<SYM>_bounce.json and <out>/<SYM>_bounce.md. Read-only on data/archive.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import sys
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from futures_agents.config import get_contract  # noqa: E402

ARCHIVE = ROOT / "data" / "archive"
ROUND_STEP = {"MNQ": 100.0, "MES": 25.0, "MGC": 25.0, "MCL": 1.0, "M2K": 25.0}
POC_BINS = 40            # price bins per day for the volume point of control
ATR_N = 14
EMA_N = 50
ARM = 1.0                # ATRs price must travel away before a level can be touched again
STOP_ATR = 1.0           # stop distance beyond the level, in ATR
TARGET_R = (1.0, 2.0)    # targets reported, in R
HOLD = {1: 240, 5: 48, 15: 32, 60: 24}   # bars before a timed exit at the close
CONFLUENCE_ATR = 0.25
RECLAIM_BARS = 6          # bars allowed between the sweep and the reclaim close
PLACEBO_SEEDS = 5
RTH_OPEN, RTH_CLOSE = time(9, 30), time(16, 0)


# ------------------------------------------------------------------ data
@dataclass
class B:
    ts: datetime
    o: float
    h: float
    l: float
    c: float
    v: float


def load(sym: str, tf: int) -> list[B]:
    p = ARCHIVE / f"{sym}_{tf}m.jsonl"
    out = []
    for line in p.read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            if float(d.get("v", 0) or 0) == 0 and d["h"] == d["l"]:
                continue                       # vendor stub (CALL N5a)
            out.append(B(datetime.fromisoformat(d["ts"]), d["o"], d["h"], d["l"], d["c"], float(d.get("v", 0) or 0)))
    out.sort(key=lambda b: b.ts)
    return out


def tday(ts: datetime):
    """Trading day: the 18:00 ET open belongs to the next calendar day's session."""
    return (ts + timedelta(hours=6)).date()


def is_rth(ts: datetime) -> bool:
    return RTH_OPEN <= ts.time() < RTH_CLOSE


# ------------------------------------------------------------------ level map
def day_levels(bars: list[B], sym: str) -> dict:
    """{trading_day: {level_name: price}} known at the START of that trading day, plus
    {trading_day: {ONH, ONL}} known from 09:30 of that day."""
    days: dict = defaultdict(list)
    for b in bars:
        days[tday(b.ts)].append(b)
    order = sorted(days)
    info = {}
    for d in order:
        bs = days[d]
        hi, lo = max(b.h for b in bs), min(b.l for b in bs)
        rth = [b for b in bs if is_rth(b.ts)]
        on = [b for b in bs if not is_rth(b.ts) and b.ts.time() < RTH_OPEN or b.ts.time() >= time(18, 0)]
        vol = sum(b.v for b in bs)
        vwap = sum((b.h + b.l + b.c) / 3 * b.v for b in bs) / vol if vol > 0 else None
        poc = None
        if vol > 0 and hi > lo:
            w = (hi - lo) / POC_BINS
            hist = [0.0] * POC_BINS
            for b in bs:
                i = min(POC_BINS - 1, int(((b.h + b.l + b.c) / 3 - lo) / w))
                hist[i] += b.v
            k = max(range(POC_BINS), key=hist.__getitem__)
            poc = lo + (k + 0.5) * w
        info[d] = dict(H=hi, L=lo, C=bs[-1].c, RH=max((b.h for b in rth), default=None),
                       RL=min((b.l for b in rth), default=None), VWAP=vwap, POC=poc,
                       ONH=max((b.h for b in on), default=None), ONL=min((b.l for b in on), default=None),
                       wk=d.isocalendar()[:2])
    weeks: dict = defaultdict(list)
    for d in order:
        weeks[info[d]["wk"]].append(info[d])
    wk_order = sorted(weeks)
    wk_hl = {w: (max(x["H"] for x in weeks[w]), min(x["L"] for x in weeks[w])) for w in wk_order}

    step = ROUND_STEP.get(sym, 0)
    start, intraday = {}, {}
    for i, d in enumerate(order):
        if i == 0:
            continue
        p = info[order[i - 1]]
        lv = {"PDH": p["H"], "PDL": p["L"], "PDC": p["C"], "PD_POC": p["POC"], "PD_VWAP": p["VWAP"],
              "P_RTH_H": p["RH"], "P_RTH_L": p["RL"]}
        wi = wk_order.index(info[d]["wk"])
        if wi > 0:
            lv["PWH"], lv["PWL"] = wk_hl[wk_order[wi - 1]]
        if step:
            base = math.floor(p["C"] / step) * step
            for k in (-1, 0, 1, 2):
                lv[f"ROUND{k}"] = base + k * step
        start[d] = {k: v for k, v in lv.items() if v is not None}
        intraday[d] = {k: info[d][k] for k in ("ONH", "ONL") if info[d][k] is not None}
    return start, intraday


def swing_pivots(sym: str, k: int = 3):
    """Confirmed 60m swing highs/lows: (known_from_ts, kind, price). A pivot at bar j is only
    known once bar j+k has CLOSED, so it is usable from ts[j+k] + 60m."""
    h = load(sym, 60)
    out = []
    for j in range(k, len(h) - k):
        win = h[j - k:j + k + 1]
        if h[j].l == min(b.l for b in win):
            out.append((h[j + k].ts + timedelta(minutes=60), "SWING_L", h[j].l))
        if h[j].h == max(b.h for b in win):
            out.append((h[j + k].ts + timedelta(minutes=60), "SWING_H", h[j].h))
    return out


# ------------------------------------------------------------------ indicators
def atr_series(bars: list[B]) -> list[float | None]:
    out, trs, prev = [], [], None
    for b in bars:
        tr = b.h - b.l if prev is None else max(b.h - b.l, abs(b.h - prev), abs(b.l - prev))
        trs.append(tr)
        prev = b.c
        out.append(sum(trs[-ATR_N:]) / ATR_N if len(trs) >= ATR_N else None)
    return out


def ema_series(vals: list[float], n: int) -> list[float]:
    a, out, e = 2 / (n + 1), [], None
    for v in vals:
        e = v if e is None else e + a * (v - e)
        out.append(e)
    return out


# ------------------------------------------------------------------ event engine
@dataclass
class Event:
    i: int
    ts: str
    level: str
    side: str          # SUPPORT (long) / RESISTANCE (short)
    price: float
    touch_no: int
    confluence: int
    aligned: bool
    rth: bool
    fast: bool
    hivol: bool
    r: dict = field(default_factory=dict)   # "mode:target_R" -> net R (missing = no entry)


def run(bars, sym, tf, start, intraday, pivots, shift=None, rng=None):
    spec = get_contract(sym)
    cost_pts = spec.round_turn_cost / spec.point_value
    min_stop = spec.min_stop_ticks * spec.tick_size
    atr = atr_series(bars)
    ema = ema_series([b.c for b in bars], EMA_N)
    atr_med, med_cache = [], []
    hold = HOLD.get(tf, 24)
    plows = [p for p in pivots if p[1] == "SWING_L"]
    phighs = [p for p in pivots if p[1] == "SWING_H"]
    plow_ts, phigh_ts = [p[0] for p in plows], [p[0] for p in phighs]
    state: dict = {}           # level key -> dict(armed_s, armed_r, touches)
    day_shift: dict = {}
    events: list[Event] = []
    for i in range(max(ATR_N, 8), len(bars) - 1):
        b, pb = bars[i], bars[i - 1]
        a = atr[i - 1]
        if not a:
            continue
        atr_med.append(a)
        if i % 20 == 0 or not med_cache:
            med_cache[:] = [sorted(atr_med[-200:])[len(atr_med[-200:]) // 2]]
        med = med_cache[0]
        d = tday(b.ts)
        lv = dict(start.get(d, {}))
        if not lv:
            continue
        if is_rth(b.ts):
            lv.update(intraday.get(d, {}))
        nl, nh = bisect_right(plow_ts, b.ts), bisect_right(phigh_ts, b.ts)
        lows, highs = plows[max(0, nl - 4):nl], phighs[max(0, nh - 4):nh]
        for n, p in enumerate(lows):
            lv[f"SWING_L{n}"] = p[2]
        for n, p in enumerate(highs):
            lv[f"SWING_H{n}"] = p[2]
        if shift is not None:        # placebo: every level moved by a random 0.75-3 ATR, fixed per day+name
            for k in list(lv):
                key = (d, k)
                if key not in day_shift:      # fixed in PRICE for the day, like a real level
                    day_shift[key] = rng.choice((-1, 1)) * rng.uniform(0.75, 3.0) * a
                lv[k] = lv[k] + day_shift[key]
        prices = sorted(lv.values())
        for name, L in lv.items():
            kind = "SWING" if name.startswith("SWING") else ("ROUND" if name.startswith("ROUND") else name)
            key = (kind, round(L / spec.tick_size))
            st = state.setdefault(key, {"s": False, "r": False, "n": 0})
            # arm from the previous bar's position: price must have been >= ARM ATR away
            if pb.l > L + ARM * a:
                st["s"] = True
            if pb.h < L - ARM * a:
                st["r"] = True
            for side in ("SUPPORT", "RESISTANCE"):
                armed = st["s"] if side == "SUPPORT" else st["r"]
                if not armed:
                    continue
                touched = b.l <= L if side == "SUPPORT" else b.h >= L
                if not touched:
                    continue
                st["s" if side == "SUPPORT" else "r"] = False
                st["n"] += 1
                conf = sum(1 for p in prices if abs(p - L) <= CONFLUENCE_ATR * a) - 1
                up = pb.c > ema[i - 1]
                ev = Event(i, b.ts.isoformat(), kind, side, round(L, 4), st["n"], conf,
                           aligned=(up if side == "SUPPORT" else not up), rth=is_rth(b.ts),
                           fast=abs(pb.c - bars[i - 7].c) > 2.0 * a, hivol=a > med)
                risk = max(STOP_ATR * a, min_stop)
                for tr in TARGET_R:
                    ev.r[f"touch:{tr}"] = simulate(bars, i, side, L, risk, tr, hold) - cost_pts / risk
                    rc = reclaim(bars, i, side, L, a, tr, hold, spec.tick_size, min_stop)
                    if rc is not None:
                        ev.r[f"reclaim:{tr}"] = rc[0] - cost_pts / rc[1]
                events.append(ev)
    return events


def simulate(bars, i, side, L, risk, tr, hold) -> float:
    sgn = 1 if side == "SUPPORT" else -1
    b = bars[i]
    fill = L
    if (sgn == 1 and b.o < L) or (sgn == -1 and b.o > L):
        fill = b.o                                  # gapped through the limit: filled at the open
    stop, tgt = fill - sgn * risk, fill + sgn * tr * risk
    if (sgn == 1 and b.l <= stop) or (sgn == -1 and b.h >= stop):
        return -1.0                                 # fill bar can only lose
    for j in range(i + 1, min(len(bars), i + 1 + hold)):
        x = bars[j]
        if (sgn == 1 and x.o <= stop) or (sgn == -1 and x.o >= stop):
            return sgn * (x.o - fill) / risk        # gap through the stop fills at the open
        if (sgn == 1 and x.l <= stop) or (sgn == -1 and x.h >= stop):
            return -1.0                             # stop wins the ambiguous bar
        if (sgn == 1 and x.h >= tgt) or (sgn == -1 and x.l <= tgt):
            return tr
    last = bars[min(len(bars) - 1, i + hold)]
    return sgn * (last.c - fill) / risk


def reclaim(bars, i, side, L, a, tr, hold, tick, min_stop):
    """Sweep-and-reclaim entry. Price must PIERCE the level by >= 1 tick, then a bar must CLOSE
    back on the level's side within RECLAIM_BARS bars, without running more than 2 ATR through.
    Enter at the NEXT bar's open, stop 1 tick beyond the sweep extreme, target tr x risk.
    Returns (R before costs, risk in points) or None when no reclaim happened."""
    sgn = 1 if side == "SUPPORT" else -1
    extreme = None
    for j in range(i, min(len(bars) - 1, i + RECLAIM_BARS)):
        x = bars[j]
        ext = x.l if sgn == 1 else x.h
        extreme = ext if extreme is None else (min(extreme, ext) if sgn == 1 else max(extreme, ext))
        if sgn * (L - extreme) > 2 * a:
            return None                              # ran through: a break, not a sweep
        pierced = sgn * (L - extreme) >= tick
        if pierced and sgn * (x.c - L) > 0:
            e = bars[j + 1]
            fill = e.o
            stop = extreme - sgn * tick
            risk = sgn * (fill - stop)
            if risk < min_stop or risk > 3 * a:
                return None
            tgt = fill + sgn * tr * risk
            if (sgn == 1 and e.l <= stop) or (sgn == -1 and e.h >= stop):
                return (-1.0, risk)
            for k in range(j + 2, min(len(bars), j + 2 + hold)):
                y = bars[k]
                if (sgn == 1 and y.o <= stop) or (sgn == -1 and y.o >= stop):
                    return (sgn * (y.o - fill) / risk, risk)
                if (sgn == 1 and y.l <= stop) or (sgn == -1 and y.h >= stop):
                    return (-1.0, risk)
                if (sgn == 1 and y.h >= tgt) or (sgn == -1 and y.l <= tgt):
                    return (tr, risk)
            last = bars[min(len(bars) - 1, j + 1 + hold)]
            return (sgn * (last.c - fill) / risk, risk)
    return None


# ------------------------------------------------------------------ statistics
def summarise(evs, tr="touch:1.0"):
    rs = [e.r[tr] for e in evs if tr in e.r]
    n = len(rs)
    if not n:
        return dict(n=0)
    m = sum(rs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in rs) / (n - 1)) if n > 1 else 0
    wins = sum(1 for x in rs if x > 0)
    return dict(n=n, win=round(wins / n, 3), expR=round(m, 3), sd=round(sd, 3))


def zdiff(real, plc):
    if real.get("n", 0) < 2 or plc.get("n", 0) < 2:
        return None
    se = math.sqrt(real["sd"] ** 2 / real["n"] + plc["sd"] ** 2 / plc["n"])
    return round((real["expR"] - plc["expR"]) / se, 2) if se else None


FEATURES = {
    "all": lambda e: True,
    "first_touch": lambda e: e.touch_no == 1,
    "retest(2+)": lambda e: e.touch_no >= 2,
    "confluence>=2": lambda e: e.confluence >= 2,
    "confluence=0": lambda e: e.confluence == 0,
    "with_trend": lambda e: e.aligned,
    "counter_trend": lambda e: not e.aligned,
    "RTH": lambda e: e.rth,
    "overnight": lambda e: not e.rth,
    "slow_approach": lambda e: not e.fast,
    "fast_approach": lambda e: e.fast,
    "low_vol": lambda e: not e.hivol,
    "high_vol": lambda e: e.hivol,
    "support": lambda e: e.side == "SUPPORT",
    "resistance": lambda e: e.side == "RESISTANCE",
}


def table(real, plc, key_fn_map, tr):
    rows = []
    for name, fn in key_fn_map.items():
        r = summarise([e for e in real if fn(e)], tr)
        p = summarise([e for e in plc if fn(e)], tr)
        rows.append(dict(bucket=name, real=r, placebo=p, z=zdiff(r, p)))
    return rows


# ------------------------------------------------------------------ current levels
def current_levels(bars, sym, start, intraday, pivots, modes):
    spec = get_contract(sym)
    atr = atr_series(bars)[-1]
    ema = ema_series([b.c for b in bars], EMA_N)[-1]
    last = bars[-1]
    d = tday(last.ts)
    # the level map for the NEXT bar: today's start levels (+ON if in RTH), or tomorrow's if past 17:00
    lv = dict(start.get(d, {}))
    if is_rth(last.ts):
        lv.update(intraday.get(d, {}))
    for p in [p for p in pivots if p[0] <= last.ts][-12:]:
        lv[f"{p[1]}@{p[2]:.2f}"] = p[2]
    rows = []
    for name, L in lv.items():
        kind = "SWING" if name.startswith("SWING") else ("ROUND" if name.startswith("ROUND") else name)
        side = "SUPPORT" if L < last.c else "RESISTANCE"
        dist = abs(last.c - L) / atr
        if dist > 6:
            continue
        conf = [n for n, p in lv.items() if n != name and abs(p - L) <= CONFLUENCE_ATR * atr]
        aligned = (last.c > ema) if side == "SUPPORT" else (last.c < ema)
        hist = {m: v["_by_type"].get(kind, {}).get(side, {}) for m, v in modes.items()}
        reasons = []
        if conf:
            reasons.append(f"confluence with {', '.join(conf)}")
        reasons.append("with the trend (price vs EMA50)" if aligned else "COUNTER-trend (price vs EMA50)")
        feats = ["confluence>=2" if len(conf) >= 2 else "confluence=0" if not conf else None,
                 "with_trend" if aligned else "counter_trend"]
        rows.append(dict(level=name, type=kind, price=round(spec.round_to_tick(L), 4), side=side,
                         dist_atr=round(dist, 2), confluence=conf, aligned=aligned,
                         history=hist,
                         feature_history={m: {f: v["_by_feat"].get(f) for f in feats if f} for m, v in modes.items()},
                         reasons=reasons))
    rows.sort(key=lambda r: r["dist_atr"])
    return dict(asof=last.ts.isoformat(), close=spec.round_to_tick(last.c), atr=round(atr, 3), ema50=round(ema, 3), levels=rows)


# ------------------------------------------------------------------ driver
def analyse_mode(real, plc, tr):
    types = sorted({e.level for e in real})
    by_type_rows, by_type = [], {}
    for t in types:
        for side in ("SUPPORT", "RESISTANCE"):
            r = summarise([e for e in real if e.level == t and e.side == side], tr)
            p = summarise([e for e in plc if e.level == t and e.side == side], tr)
            row = dict(bucket=f"{t} {side}", real=r, placebo=p, z=zdiff(r, p))
            by_type_rows.append(row)
            by_type.setdefault(t, {})[side] = row
    feat_rows = table(real, plc, FEATURES, tr)
    n_cells = len(by_type_rows) + len(feat_rows)
    return dict(n_cells=n_cells, free_z=round(math.sqrt(2 * math.log(n_cells)), 2),
                targets={t: dict(real=summarise(real, f"{tr.split(':')[0]}:{t}"),
                                 placebo=summarise(plc, f"{tr.split(':')[0]}:{t}"),
                                 z=zdiff(summarise(real, f"{tr.split(':')[0]}:{t}"),
                                         summarise(plc, f"{tr.split(':')[0]}:{t}"))) for t in map(str, TARGET_R)},
                by_type=by_type_rows, by_feature=feat_rows, _by_type=by_type,
                _by_feat={r["bucket"]: r for r in feat_rows})


def analyse(sym, tf):
    bars = load(sym, tf)
    start, intraday = day_levels(bars, sym)
    pivots = swing_pivots(sym)
    real = run(bars, sym, tf, start, intraday, pivots)
    plc = []
    for s in range(PLACEBO_SEEDS):
        plc += run(bars, sym, tf, start, intraday, pivots, shift=True, rng=random.Random(1000 + s))
    modes = {m: analyse_mode(real, plc, f"{m}:1.0") for m in ("touch", "reclaim")}
    cur = current_levels(bars, sym, start, intraday, pivots, modes)
    for m in modes.values():
        m.pop("_by_type"), m.pop("_by_feat")
    return dict(symbol=sym, tf=tf, stop_atr=STOP_ATR, bars=len(bars), first=bars[0].ts.isoformat(),
                last=bars[-1].ts.isoformat(), modes=modes, current=cur)


def fmt(s):
    return "—" if not s or not s.get("n") else f"{s['n']} / {s['win']*100:.0f}% / {s['expR']:+.3f}R"


def verdict(z, free_z):
    if z is None:
        return "too few"
    if z >= free_z:
        return "**beats random**"
    if z >= 1.0:
        return "leans better"
    if z <= -free_z:
        return "**worse than random**"
    if z <= -1.0:
        return "leans worse"
    return "same as random"


MODE_TEXT = {
    "touch": "**Buy/sell AT the level** (limit order resting on the line, stop 1 ATR beyond it)",
    "reclaim": "**Sweep & reclaim** (wait for price to poke THROUGH the level and close back on the right "
               "side, enter next bar, stop just past the sweep's extreme)",
}


def to_md(res_list, sym) -> str:
    out = [f"# {sym} — bounce levels\n",
           "_Generated by `python3 DATA_HUB/tools/bounce_levels.py`. Re-run it after "
           "`python3 DATA_HUB/tools/refresh_archive.py --fetch` for fresh levels._\n",
           "**How to read this.** Every time price came back to a level it had moved away from, we "
           "pretended to trade the bounce two ways (below), charged real commissions and slippage, and "
           "counted the result in **R** (1R = the amount risked; +0.10R per trade means you'd make 10% "
           "of your risk per trade on average). Then we did exactly the same thing at **fake levels**: "
           "the same lines moved a random distance away. If real levels don't beat fake ones, the level "
           "itself isn't what's making price bounce. Cells read `trades / win rate / average R`.\n"]
    for res in res_list:
        out.append(f"\n## {res['tf']}-minute bars · {res['first'][:10]} → {res['last'][:16]} ET\n")
        for mode, m in res["modes"].items():
            t1, t2 = m["targets"]["1.0"], m["targets"]["2.0"]
            out.append(f"\n### {MODE_TEXT[mode]}\n")
            out.append(f"- Every touch, target 1R: real {fmt(t1['real'])} vs fake {fmt(t1['placebo'])} "
                       f"→ {verdict(t1['z'], m['free_z'])} (z={t1['z']})")
            out.append(f"- Every touch, target 2R: real {fmt(t2['real'])} vs fake {fmt(t2['placebo'])} "
                       f"→ {verdict(t2['z'], m['free_z'])} (z={t2['z']})")
            out.append(f"- {m['n_cells']} rows tested below, so a z of about ±{m['free_z']} shows up by luck alone.\n")
            out.append("| level (1R target) | real | fake | z | verdict |\n|---|---|---|---|---|")
            for r in sorted(m["by_type"], key=lambda r: -(r["z"] if r["z"] is not None else -99)):
                if r["real"].get("n", 0) >= 10:
                    out.append(f"| {r['bucket']} | {fmt(r['real'])} | {fmt(r['placebo'])} | {r['z']} | {verdict(r['z'], m['free_z'])} |")
            out.append("\n| when does it hold? (1R) | real | fake | z | verdict |\n|---|---|---|---|---|")
            for r in m["by_feature"]:
                out.append(f"| {r['bucket']} | {fmt(r['real'])} | {fmt(r['placebo'])} | {r['z']} | {verdict(r['z'], m['free_z'])} |")
        cur = res["current"]
        out.append(f"\n### Levels near price — as of the bar at {cur['asof']} (close {cur['close']}, "
                   f"typical bar range ATR {cur['atr']}). **Not live** unless you just re-ran the refresh.\n")
        out.append("| level | price | acts as | how far (ATRs) | at-level history | sweep&reclaim history | notes |\n|---|---|---|---|---|---|---|")
        for r in cur["levels"][:14]:
            h = r["history"]
            out.append(f"| {r['level']} | {r['price']} | {r['side'].lower()} | {r['dist_atr']} | "
                       f"{fmt(h['touch'].get('real'))} (fake {fmt(h['touch'].get('placebo'))}) | "
                       f"{fmt(h['reclaim'].get('real'))} (fake {fmt(h['reclaim'].get('placebo'))}) | {'; '.join(r['reasons'])} |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", nargs="+", default=["MNQ", "MES", "MGC", "MCL"])
    ap.add_argument("--tf", nargs="+", type=int, default=[5, 60])
    ap.add_argument("--out", default=str(ROOT / "DATA_HUB" / "levels"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for sym in a.symbols:
        res = [analyse(sym, tf) for tf in a.tf]
        (out / f"{sym}_bounce.json").write_text(json.dumps(res, indent=1, default=str))
        (out / f"{sym}_bounce.md").write_text(to_md(res, sym))
        for r in res:
            for mode, m in r["modes"].items():
                o = m["targets"]["1.0"]
                print(f"{sym} {r['tf']:>3}m {mode:8s} real {fmt(o['real'])}  placebo {fmt(o['placebo'])}  z={o['z']}")


if __name__ == "__main__":
    main()
