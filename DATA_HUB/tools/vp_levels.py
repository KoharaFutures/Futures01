#!/usr/bin/env python3
"""Multi-timeframe volume-profile scanner: low-volume nodes (LVNs) - continuation or bounce?

The owner's method: build volume profiles over ranges of different lengths, mark the
LOW-volume prices inside them as key levels, and decide whether price will CONTINUE
through such a level or BOUNCE off it. A range can contain several trend legs; the LVNs
usually sit between them, where price moved fast and little volume traded.

For every symbol and profile window this tool
  1. builds the profile each day from PAST bars only (volume spread evenly over each
     bar's high-low; smoothed), and finds POC, value area (70%), high-volume nodes (HVN)
     and low-volume nodes (LVN = a valley with a clearly bigger peak on BOTH sides);
  2. describes the range: balanced vs trending, and its trend legs (zigzag of 3 ATR);
  3. at every fresh touch of an LVN/HVN/POC/VAH/VAL, records which comes first:
        CONTINUATION = price travels K ATR further in the direction it arrived from
        BOUNCE       = price travels K ATR back the way it came
     (a bar touching both is AMBIGUOUS and counts against either trade);
  4. does the same at PLACEBO prices - random prices inside the same range, fixed per day -
     so "LVNs make price continue" is compared with "any price in that range";
  5. splits the results by condition (window length, profile shape, approach with/against
     the range's trend, from inside/outside value, relative volume, session);
  6. prints the CURRENT profiles and each nearby LVN with the historical lean.

A continuation trade at the level with stop = target = K ATR earns (P_cont - P_bounce -
P_ambiguous) R before costs; a bounce trade earns (P_bounce - P_cont - P_ambiguous) R.
Both are reported net of costs.

    python3 DATA_HUB/tools/vp_levels.py                 # MNQ MES MGC MCL
    python3 DATA_HUB/tools/vp_levels.py --symbols MNQ --k 1.5

Writes DATA_HUB/levels/<SYM>_volume_profile.{json,md}. Read-only on data/archive.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
import sys
from collections import defaultdict
from dataclasses import dataclass

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from bounce_levels import ROOT, load, tday, atr_series, is_rth, get_contract  # noqa: E402

# (profile source timeframe, window in trading days, label)
WINDOWS = [(5, 1, "1-day"), (5, 3, "3-day"), (5, 5, "1-week"), (5, 10, "2-week"),
           (60, 5, "1-week(60m)"), (60, 20, "1-month"), (60, 60, "3-month")]
N_BINS = 80
LVN_RATIO = 0.5          # valley volume <= 50% of the SMALLER of its two neighbouring peaks
HVN_MIN = 0.25           # a peak must hold >= 25% of the POC's volume to count as an HVN
MIN_SEP_BINS = 4
ARM = 1.0
HOLD = {5: 48, 60: 24}
PLACEBO_PER_LEVEL = 2
ZIGZAG_ATR = 3.0
LEG_MIN_RANGE = 0.20


# ------------------------------------------------------------------ profile
@dataclass
class Profile:
    lo: float
    hi: float
    step: float
    vol: list
    poc: float
    vah: float
    val: float
    hvn: list
    lvn: list
    shape: str          # BALANCED / TREND_UP / TREND_DOWN
    net: float          # (last close - first open) / range


def build_profile(bars) -> Profile | None:
    lo, hi = min(b.l for b in bars), max(b.h for b in bars)
    if hi <= lo:
        return None
    step = (hi - lo) / N_BINS
    vol = [0.0] * N_BINS
    for b in bars:
        a = min(N_BINS - 1, int((b.l - lo) / step))
        z = min(N_BINS - 1, int((b.h - lo) / step))
        share = b.v / (z - a + 1) if b.v > 0 else 0
        for k in range(a, z + 1):
            vol[k] += share
    sm = [sum(vol[max(0, k - 1):k + 2]) / len(vol[max(0, k - 1):k + 2]) for k in range(N_BINS)]
    tot = sum(sm)
    if tot <= 0:
        return None
    price = lambda k: lo + (k + 0.5) * step
    pk = max(range(N_BINS), key=sm.__getitem__)
    # value area: expand from the POC toward the larger neighbour until 70% is inside
    a = z = pk
    acc = sm[pk]
    while acc < 0.7 * tot and (a > 0 or z < N_BINS - 1):
        up = sm[z + 1] if z < N_BINS - 1 else -1
        dn = sm[a - 1] if a > 0 else -1
        if up >= dn:
            z += 1
            acc += sm[z]
        else:
            a -= 1
            acc += sm[a]
    peaks = [k for k in range(1, N_BINS - 1) if sm[k] >= sm[k - 1] and sm[k] >= sm[k + 1] and sm[k] >= HVN_MIN * sm[pk]]
    peaks = _thin(peaks, sm, MIN_SEP_BINS, keep_max=True)
    lvns = []
    for p, q in zip(peaks, peaks[1:]):
        k = min(range(p + 1, q), key=sm.__getitem__, default=None)
        if k is not None and sm[k] <= LVN_RATIO * min(sm[p], sm[q]):
            lvns.append(k)
    net = (bars[-1].c - bars[0].o) / (hi - lo)
    shape = "TREND_UP" if net > 0.5 else "TREND_DOWN" if net < -0.5 else "BALANCED"
    return Profile(lo, hi, step, sm, price(pk), lo + (z + 1) * step, lo + a * step,
                   [price(k) for k in peaks], [price(k) for k in lvns], shape, round(net, 3))


def _thin(idx, sm, sep, keep_max):
    out = []
    for k in sorted(idx, key=lambda k: -sm[k] if keep_max else sm[k]):
        if all(abs(k - j) >= sep for j in out):
            out.append(k)
    return sorted(out)


def zigzag_legs(bars, atr):
    """Split a window into trend legs: a new leg starts when price reverses ZIGZAG_ATR x ATR."""
    if not bars or not atr:
        return []
    # a leg must be meaningful for THIS range: >= 3 ATR and >= 20% of the range's height
    th = max(ZIGZAG_ATR * atr, LEG_MIN_RANGE * (max(b.h for b in bars) - min(b.l for b in bars)))
    legs, piv, piv_p, direction = [], 0, bars[0].c, 0
    ext_i, ext_p = 0, bars[0].c
    for i, b in enumerate(bars):
        if direction == 1 and b.h > ext_p:
            ext_i, ext_p = i, b.h
        if direction == -1 and b.l < ext_p:
            ext_i, ext_p = i, b.l
        if direction == 0:
            if b.h - piv_p >= th:
                direction, ext_i, ext_p = 1, i, b.h
            elif piv_p - b.l >= th:
                direction, ext_i, ext_p = -1, i, b.l
            continue
        if direction == 1 and ext_p - b.l >= th:
            legs.append(("UP", piv_p, ext_p, bars[piv].ts, bars[ext_i].ts))
            piv, piv_p, direction, ext_i, ext_p = ext_i, ext_p, -1, i, b.l
        elif direction == -1 and b.h - ext_p >= th:
            legs.append(("DOWN", piv_p, ext_p, bars[piv].ts, bars[ext_i].ts))
            piv, piv_p, direction, ext_i, ext_p = ext_i, ext_p, 1, i, b.h
    if direction:
        legs.append(("UP" if direction == 1 else "DOWN", piv_p, ext_p, bars[piv].ts, bars[ext_i].ts))
    return legs


# ------------------------------------------------------------------ level map per day
def daily_profiles(bars, window_days):
    days = defaultdict(list)
    for b in bars:
        days[tday(b.ts)].append(b)
    order = sorted(days)
    out = {}
    for n, d in enumerate(order):
        if n < window_days:
            continue
        src = [b for dd in order[n - window_days:n] for b in days[dd]]
        pf = build_profile(src)
        if pf:
            out[d] = pf
    return out


def levels_of(pf: Profile):
    lv = [("LVN", p) for p in pf.lvn] + [("HVN", p) for p in pf.hvn if abs(p - pf.poc) > pf.step]
    lv += [("POC", pf.poc), ("VAH", pf.vah), ("VAL", pf.val)]
    return lv


# ------------------------------------------------------------------ first passage
def first_passage(bars, i, came_from_above, L, dist, hold):
    """Returns 'CONT', 'BOUNCE', 'AMBIG' or 'STALL' (neither within `hold` bars)."""
    s = -1 if came_from_above else 1          # continuation direction
    cont, bnc = L + s * dist, L - s * dist
    b = bars[i]
    if (s == -1 and b.l <= cont) or (s == 1 and b.h >= cont):
        return "CONT"                         # the touch bar can only prove continuation
    for j in range(i + 1, min(len(bars), i + 1 + hold)):
        x = bars[j]
        c = (x.l <= cont) if s == -1 else (x.h >= cont)
        r = (x.h >= bnc) if s == -1 else (x.l <= bnc)
        if c and r:
            return "AMBIG"
        if c:
            return "CONT"
        if r:
            return "BOUNCE"
    return "STALL"


@dataclass
class Touch:
    ts: str
    window: str
    kind: str
    price: float
    from_above: bool
    shape: str
    with_trend: bool      # arrived moving in the same direction as the range's net trend
    from_value: bool      # arrived from inside the value area
    hi_rvol: bool
    rth: bool
    outcome: str


def scan(bars, sym, tf, wdays, label, k_atr, placebo=False, seed=0):
    spec = get_contract(sym)
    atr = atr_series(bars)
    profiles = daily_profiles(bars, wdays)
    rng = random.Random(seed)
    hold = HOLD.get(tf, 24)
    state, touches = {}, []
    cache_day, lv = None, []
    for i in range(20, len(bars) - 1):
        b, pb = bars[i], bars[i - 1]
        a = atr[i - 1]
        d = tday(b.ts)
        pf = profiles.get(d)
        if not a or not pf:
            continue
        if d != cache_day:
            cache_day = d
            lv = levels_of(pf)
            if placebo:
                lv = [(k, rng.uniform(pf.lo, pf.hi)) for k, _ in lv for _ in range(PLACEBO_PER_LEVEL)]
        rv = b.v / (sum(x.v for x in bars[i - 20:i]) / 20 or 1)
        for kind, L in lv:
            key = (d, kind, round(L / spec.tick_size))
            st = state.setdefault(key, {"above": False, "below": False})
            if pb.l > L + ARM * a:
                st["above"] = True
            if pb.h < L - ARM * a:
                st["below"] = True
            for from_above in (True, False):
                armed = st["above"] if from_above else st["below"]
                if not armed or not ((b.l <= L) if from_above else (b.h >= L)):
                    continue
                st["above" if from_above else "below"] = False
                moving_up = not from_above
                trend_up = pf.shape == "TREND_UP"
                touches.append(Touch(
                    b.ts.isoformat(), label, kind, round(L, 4), from_above, pf.shape,
                    with_trend=(pf.shape != "BALANCED" and moving_up == trend_up),
                    from_value=pf.val <= pb.c <= pf.vah, hi_rvol=rv > 1.5, rth=is_rth(b.ts),
                    outcome=first_passage(bars, i, from_above, L, k_atr * a, hold)))
    return touches, profiles


# ------------------------------------------------------------------ statistics
def rates(ts, cost_r):
    n = len(ts)
    if not n:
        return dict(n=0)
    c = sum(t.outcome == "CONT" for t in ts) / n
    b = sum(t.outcome == "BOUNCE" for t in ts) / n
    amb = sum(t.outcome == "AMBIG" for t in ts) / n
    return dict(n=n, cont=round(c, 3), bounce=round(b, 3), ambig=round(amb, 3),
                stall=round(1 - c - b - amb, 3),
                go_with_R=round(c - b - amb - cost_r, 3), fade_R=round(b - c - amb - cost_r, 3))


def z_prop(p1, n1, p2, n2):
    if not n1 or not n2:
        return None
    p = (p1 * n1 + p2 * n2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2)) if 0 < p < 1 else 0
    return round((p1 - p2) / se, 2) if se else None


CONDITIONS = {
    "all": lambda t: True,
    "range is BALANCED": lambda t: t.shape == "BALANCED",
    "range is TRENDING": lambda t: t.shape != "BALANCED",
    "arrived WITH the range's trend": lambda t: t.with_trend,
    "arrived AGAINST the range's trend": lambda t: t.shape != "BALANCED" and not t.with_trend,
    "arrived from INSIDE value": lambda t: t.from_value,
    "arrived from OUTSIDE value": lambda t: not t.from_value,
    "high relative volume (>1.5x)": lambda t: t.hi_rvol,
    "normal volume": lambda t: not t.hi_rvol,
    "regular hours": lambda t: t.rth,
    "overnight": lambda t: not t.rth,
    "falling into it (support test)": lambda t: t.from_above,
    "rising into it (resistance test)": lambda t: not t.from_above,
}


def compare(real, plc, cost_r):
    r, p = rates(real, cost_r), rates(plc, cost_r)
    if r.get("n") and p.get("n"):
        r["z_cont_vs_random"] = z_prop(r["cont"], r["n"], p["cont"], p["n"])
        r["z_bounce_vs_random"] = z_prop(r["bounce"], r["n"], p["bounce"], p["n"])
    return dict(real=r, placebo=p)


# cells tested per symbol: windows x (level kinds + conditions) x two outcomes
FREE_Z = round(math.sqrt(2 * math.log(len(WINDOWS) * (5 + len(CONDITIONS)) * 2)), 2)


def lean(row):
    """Plain-English lean. 'beats random' needs |z| >= FREE_Z, the z this many tests give by luck."""
    r = row["real"]
    if not r.get("n") or r["n"] < 15:
        return "too few touches"
    edge = r["cont"] - r["bounce"]
    if abs(edge) < 0.05:
        return "coin-flip"
    side = "CONTINUATION" if edge > 0 else "BOUNCE"
    z = (r.get("z_cont_vs_random") if edge > 0 else r.get("z_bounce_vs_random")) or 0
    if z >= FREE_Z:
        return f"{side}, beats random prices"
    if z >= 2:
        return f"leans {side} (hint only: z {z} < luck bar {FREE_Z})"
    return f"leans {side}, but random prices do the same"


# ------------------------------------------------------------------ driver
def analyse(sym, k_atr):
    spec = get_contract(sym)
    series = {tf: load(sym, tf) for tf in {w[0] for w in WINDOWS}}
    res = dict(symbol=sym, k_atr=k_atr, windows=[], current=[])
    for tf, wdays, label in WINDOWS:
        bars = series[tf]
        atr_now = atr_series(bars)[-1]
        cost_r = spec.round_turn_cost / spec.point_value / (k_atr * atr_now)
        real, profiles = scan(bars, sym, tf, wdays, label, k_atr)
        plc = []
        for s in range(3):
            plc += scan(bars, sym, tf, wdays, label, k_atr, placebo=True, seed=7 + s)[0]
        kinds = {}
        for kind in ("LVN", "HVN", "POC", "VAH", "VAL"):
            kinds[kind] = compare([t for t in real if t.kind == kind], plc, cost_r)
        conds = {name: compare([t for t in real if t.kind == "LVN" and f(t)], [t for t in plc if f(t)], cost_r)
                 for name, f in CONDITIONS.items()}
        for row in list(kinds.values()) + list(conds.values()):
            row["lean"] = lean(row)
        res["windows"].append(dict(window=label, tf=tf, days=wdays, first=bars[0].ts.isoformat()[:10],
                                   last=bars[-1].ts.isoformat()[:16], by_kind=kinds, lvn_by_condition=conds))
        # current profile: the window ending with the LAST bar (including today's bars so far)
        days = sorted({tday(b.ts) for b in bars})[-wdays:]
        cur_bars = [b for b in bars if tday(b.ts) in set(days)]
        pf = build_profile(cur_bars)
        if not pf:
            continue
        last = bars[-1]
        legs = zigzag_legs(cur_bars, atr_now)
        near = []
        for L in pf.lvn:
            from_above = last.c > L
            moving_up = not from_above
            trend_up = pf.shape == "TREND_UP"
            with_trend = pf.shape != "BALANCED" and moving_up == trend_up
            key = ("arrived WITH the range's trend" if with_trend else
                   "arrived AGAINST the range's trend" if pf.shape != "BALANCED" else "range is BALANCED")
            near.append(dict(price=spec.round_to_tick(L), side="support" if from_above else "resistance",
                             dist_atr=round(abs(last.c - L) / atr_now, 2), condition=key,
                             history=conds[key]["real"], lean=conds[key]["lean"]))
        near.sort(key=lambda r: r["dist_atr"])
        res["current"].append(dict(window=label, tf=tf, asof=last.ts.isoformat(), close=spec.round_to_tick(last.c),
                                   atr=round(atr_now, 3), range=[spec.round_to_tick(pf.lo), spec.round_to_tick(pf.hi)],
                                   poc=spec.round_to_tick(pf.poc), vah=spec.round_to_tick(pf.vah),
                                   val=spec.round_to_tick(pf.val), shape=pf.shape, net=pf.net,
                                   hvn=[spec.round_to_tick(p) for p in pf.hvn],
                                   legs=[dict(dir=l[0], start=spec.round_to_tick(l[1]), end=spec.round_to_tick(l[2]),
                                              from_=l[3].isoformat()[:16], to=l[4].isoformat()[:16]) for l in legs],
                                   lvn=near))
    return res


def fr(r):
    if not r or not r.get("n"):
        return "—"
    return (f"{r['n']} · cont {r['cont']*100:.0f}% / bounce {r['bounce']*100:.0f}% / "
            f"both {r['ambig']*100:.0f}% · go-with {r['go_with_R']:+.2f}R, fade {r['fade_R']:+.2f}R")


def to_md(res):
    sym = res["symbol"]
    o = [f"# {sym} — volume-profile levels: continuation or bounce?\n",
         "_Generated by `python3 DATA_HUB/tools/vp_levels.py` (refresh data first with "
         "`python3 DATA_HUB/tools/refresh_archive.py --fetch`)._\n",
         f"**How to read this.** For each profile range we found the **low-volume nodes (LVNs)**: thin prices "
         f"between two heavy ones, usually where one trend leg handed over to the next. Every time price came back "
         f"to one, we checked what happened first: it **continued** {res['k_atr']} ATR further the way it was going, "
         f"or it **bounced** {res['k_atr']} ATR back. 'Both' = one bar did both, so you can't know which came first "
         f"(it counts as a loss for either trade). 'go-with' / 'fade' = average result, in units of risk and after "
         f"costs, of trading the continuation or the bounce with stop = target = {res['k_atr']} ATR. **Random** = "
         f"the same test at random prices inside the same range. If LVNs don't differ from random, the LVN is not "
         f"what decided it.\n"]
    o.append("\n## Right now (as of the last bar in the archive — refresh before trading)\n")
    for c in res["current"]:
        legs = " → ".join(f"{l['dir']} {l['start']}→{l['end']}" for l in c["legs"]) or "no leg > 3 ATR"
        o.append(f"\n### {c['window']} profile · range {c['range'][0]}–{c['range'][1]} · {c['shape']} "
                 f"· POC {c['poc']} · value {c['val']}–{c['vah']} · last {c['close']} @ {c['asof'][:16]}\n")
        o.append(f"Trend legs inside the range: {legs}\n")
        o.append(f"HVNs (heavy, 'magnet' prices): {', '.join(map(str, c['hvn'])) or '—'}\n")
        if c["lvn"]:
            o.append("| LVN | acts as | distance (ATR) | situation | history in this situation | lean |\n|---|---|---|---|---|---|")
            for l in c["lvn"][:8]:
                o.append(f"| {l['price']} | {l['side']} | {l['dist_atr']} | {l['condition']} | {fr(l['history'])} | {l['lean']} |")
        else:
            o.append("No LVN in this range: no valley deep enough between two heavy areas.")
    o.append("\n## Evidence by range length\n")
    for w in res["windows"]:
        o.append(f"\n### {w['window']} profile ({w['tf']}m bars, {w['first']} → {w['last']})\n")
        o.append("| level type | touches · outcomes · trade results | vs random: cont z / bounce z | lean |\n|---|---|---|---|")
        for k, row in w["by_kind"].items():
            r = row["real"]
            o.append(f"| {k} | {fr(r)} | {r.get('z_cont_vs_random')} / {r.get('z_bounce_vs_random')} | {row['lean']} |")
        o.append(f"| _random prices_ | {fr(w['by_kind']['LVN']['placebo'])} | — | — |")
        o.append("\n| LVN only, when… | touches · outcomes · trade results | vs random: cont z / bounce z | lean |\n|---|---|---|---|")
        for k, row in w["lvn_by_condition"].items():
            r = row["real"]
            o.append(f"| {k} | {fr(r)} | {r.get('z_cont_vs_random')} / {r.get('z_bounce_vs_random')} | {row['lean']} |")
    return "\n".join(o) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbols", nargs="+", default=["MNQ", "MES", "MGC", "MCL"])
    ap.add_argument("--k", type=float, default=1.0, help="ATR distance that decides continuation vs bounce")
    ap.add_argument("--out", default=str(ROOT / "DATA_HUB" / "levels"))
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for sym in a.symbols:
        res = analyse(sym, a.k)
        (out / f"{sym}_volume_profile.json").write_text(json.dumps(res, indent=1, default=str))
        (out / f"{sym}_volume_profile.md").write_text(to_md(res))
        for w in res["windows"]:
            r = w["by_kind"]["LVN"]
            print(f"{sym} {w['window']:12s} LVN {fr(r['real'])}  | random {fr(r['placebo'])} | {r['lean']}")


if __name__ == "__main__":
    main()
