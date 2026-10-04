#!/usr/bin/env python3
"""LTA CONCEPT CALLOUTS — level engine. The LTA "war map" for one symbol, from fetched bars (desk/live/, plus desk/archive/ if present).

Builds every key level the LTA Concepts 2.0 framework trades from (study/CONCEPTS_DIGEST.md),
each stamped with the bar it came from:

  weekly   Sunday Open (SO) and previous SO, prior week high/low/close (PWH/PWL/PWC),
           PW / EPW volume profiles (POC, VAH, VAL), and the current-week CW profile once
           Mon-Wed have closed (book ch.4: "only reliable after three trading days")
  daily    PD and EPD volume profiles (PD = the last full 18:00->17:00 session, EPD = the one
           before it, as the book's charts draw them), PDH/PDL
  swing    the profile of the latest 60m swing leg (Swing POC/VAH/VAL, book ch.7)
  context  the weekly-cycle phase, where price sits against PD value and the PW range,
           the intraday trend from two touch points on 60m and 30m (book ch.27), ATR,
           and CONFLUENCE flags (levels within 0.25 ATR of each other, book p48)
  setups   entry-model candidates EM1 / EM3 / EM4 on closed 30m and 60m bars at those levels

    python3 desk/lta_levels.py                 # MNQ MES MGC MCL, markdown
    python3 desk/lta_levels.py --symbols MGC --json

Nothing here is a signal with a measured edge. The detectors only say "the book's pattern is
present at the book's level". Never writes bar data.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lta_common import load, tday, atr_series, build_profile, zigzag_legs, get_contract  # noqa: E402

SYMS = ("MNQ", "MES", "MGC", "MCL")
STACK_ATR = 0.25          # levels this close count as one confluence zone (book p48)
NEAR_ATR = 3.0            # list levels within this many 60m ATRs of price
TOUCH_TICKS = 2           # a bar "touches" a level if it trades within this many ticks of it
WEEKDAY_PHASE = {
    0: ("MON", "trap-prone: early-week fakeouts, wait for confirmation (book ch.3)"),
    1: ("TUE", "trap-prone: early-week fakeouts, wait for confirmation (book ch.3)"),
    2: ("WED", "midweek: real directional move usually shows; CW profile valid after today's close"),
    3: ("THU", "midweek: institutions committed, data releases drive the move"),
    4: ("FRI", "unwind: profit-taking, read the close for next week's tone"),
}


# ------------------------------------------------------------------ helpers
def _iso(ts: datetime) -> str:
    return ts.isoformat()


def _r(x, tick):
    return None if x is None else round(round(x / tick) * tick, 6)


def _profile_dict(bars, label, tick):
    if len(bars) < 6:
        return None
    pf = build_profile(bars)
    if not pf:
        return None
    return {"label": label, "poc": _r(pf.poc, tick), "vah": _r(pf.vah, tick), "val": _r(pf.val, tick),
            "hvn": [_r(p, tick) for p in pf.hvn], "lvn": [_r(p, tick) for p in pf.lvn],
            "high": _r(pf.hi, tick), "low": _r(pf.lo, tick), "shape": pf.shape,
            "from_bar": _iso(bars[0].ts), "source_bar": _iso(bars[-1].ts), "n_bars": len(bars)}


def _week_key(d):
    """Trading week of a trading day. The Sunday 18:00 ET open belongs to Monday's session."""
    return d.isocalendar()[:2]


def _sessions(bars):
    by = defaultdict(list)
    for b in bars:
        by[tday(b.ts)].append(b)
    return by


def pivots(bars, k=2):
    """Fractal swing highs/lows: a bar whose high (low) is the extreme of k bars each side."""
    hs, ls = [], []
    for i in range(k, len(bars) - k):
        w = bars[i - k:i + k + 1]
        if bars[i].h == max(b.h for b in w):
            hs.append((i, bars[i].h))
        if bars[i].l == min(b.l for b in w):
            ls.append((i, bars[i].l))
    return hs, ls


def intraday_trend(bars, k=2, lookback=60):
    """Book ch.27: a trend needs two touch points - HH + HL for up, LH + LL for down."""
    seg = bars[-lookback:]
    hs, ls = pivots(seg, k)
    if len(hs) < 2 or len(ls) < 2:
        return {"trend": "UNDEFINED", "why": "fewer than two swing highs and two swing lows"}
    (_, h1), (_, h2) = hs[-2], hs[-1]
    (_, l1), (_, l2) = ls[-2], ls[-1]
    last = seg[-1].c
    if h2 > h1 and l2 > l1:
        t = "UP"
    elif h2 < h1 and l2 < l1:
        t = "DOWN"
    else:
        t = "RANGE"
    # a close beyond the last swing extreme is a break of structure (BOS)
    bos = "UP" if last > h2 else "DOWN" if last < l2 else None
    return {"trend": t, "last_swing_highs": [round(h1, 4), round(h2, 4)],
            "last_swing_lows": [round(l1, 4), round(l2, 4)],
            "break_of_structure": bos, "source_bar": _iso(seg[-1].ts)}


# ------------------------------------------------------------------ the war map
def war_map(sym: str) -> dict:
    spec = get_contract(sym)
    tick = spec.tick_size
    b5 = load(sym, 5)
    b30 = load(sym, 30)
    b60 = load(sym, 60)
    b15 = load(sym, 15)
    if not b60:
        raise SystemExit(f"{sym}: no 60m bars: run desk/fetch.py first")
    # profile source: 5m where it covers the window, else 30m, else 60m
    src = b5 if b5 else (b30 or b60)
    newest = max((x[-1] for x in (b5, b30, b60) if x), key=lambda b: b.ts)
    last_close = newest.c
    a60 = next((a for a in reversed(atr_series(b60)) if a), None)
    a15 = next((a for a in reversed(atr_series(b15)) if a), None) if b15 else None

    ses = _sessions(src)
    days = sorted(ses)
    cur_day = tday(newest.ts)
    done = [d for d in days if d < cur_day]
    out = {"symbol": sym, "newest_bar": _iso(newest.ts), "newest_close": _r(last_close, tick),
           "trading_day": str(cur_day), "atr14_60m": a60 and round(a60, 4),
           "atr14_15m": a15 and round(a15, 4), "tick": tick, "point_value": spec.point_value,
           "profile_source_tf": 5 if src is b5 else 30 if src is b30 else 60}

    # ---- daily: PD / EPD
    pd = done[-1] if done else None
    epd = done[-2] if len(done) >= 2 else None
    out["PD"] = _profile_dict(ses[pd], f"PD {pd}", tick) if pd else None
    out["EPD"] = _profile_dict(ses[epd], f"EPD {epd}", tick) if epd else None
    if out["PD"]:
        out["PD"]["pdh"] = _r(max(b.h for b in ses[pd]), tick)
        out["PD"]["pdl"] = _r(min(b.l for b in ses[pd]), tick)
        out["PD"]["pdc"] = _r(ses[pd][-1].c, tick)

    # ---- weekly: SO, PW, EPW, CW (weeks built from 60m so they always cover the full week)
    s60 = _sessions(b60)
    weeks = defaultdict(list)
    for d in sorted(s60):
        weeks[_week_key(d)].append(d)
    wk = sorted(weeks)
    cw_key = _week_key(cur_day)
    prior = [k for k in wk if k < cw_key]

    def wbars(key, use_src=True):
        # finer bars when the source series covers that week
        ds = weeks[key]
        fine = [b for d in ds for b in ses.get(d, [])] if use_src else []
        coarse = [b for d in ds for b in s60[d]]
        return fine if fine and fine[0].ts <= coarse[0].ts + timedelta(hours=1) else coarse

    def sunday_open(key):
        ds = weeks.get(key)
        return (_r(s60[ds[0]][0].o, tick), _iso(s60[ds[0]][0].ts)) if ds else (None, None)

    so, so_bar = sunday_open(cw_key) if cw_key in weeks else (None, None)
    pso, pso_bar = sunday_open(prior[-1]) if prior else (None, None)
    out["SO"] = {"price": so, "source_bar": so_bar}
    out["PSO"] = {"price": pso, "source_bar": pso_bar}
    if prior:
        pwb = wbars(prior[-1])
        out["PW"] = _profile_dict(pwb, "PW %d-W%02d" % prior[-1], tick)
        if out["PW"]:
            out["PW"].update(pwh=_r(max(b.h for b in pwb), tick), pwl=_r(min(b.l for b in pwb), tick),
                             pwc=_r(pwb[-1].c, tick))
    else:
        out["PW"] = None
    out["EPW"] = _profile_dict(wbars(prior[-2]), "EPW %d-W%02d" % prior[-2], tick) if len(prior) >= 2 else None
    cw_days_closed = [d for d in weeks.get(cw_key, []) if d < cur_day]
    out["CW"] = None
    out["CW_note"] = f"{len(cw_days_closed)} session(s) of this week closed; CW levels need 3 (Mon-Wed)"
    if len(cw_days_closed) >= 3:
        cwb = [b for d in cw_days_closed for b in ses.get(d, s60[d])]
        out["CW"] = _profile_dict(cwb, "CW %d-W%02d (Mon-%s)" % (cw_key[0], cw_key[1], cw_days_closed[-1].strftime('%a')), tick)

    # ---- swing profile: latest completed 60m zigzag leg, profiled on the finer source
    legs = zigzag_legs(b60[-24 * 10:], a60) if a60 else []
    out["SWING"] = None
    if legs:
        d_, p0, p1, t0, t1 = legs[-1]
        sb = [b for b in src if t0 <= b.ts <= t1]
        sw = _profile_dict(sb, f"Swing leg {d_} {p0}->{p1}", tick)
        if sw:
            sw.update(direction=d_, swing_from=_r(p0, tick), swing_to=_r(p1, tick))
            sw["label"] = f"Swing leg {d_} {sw['swing_from']}->{sw['swing_to']}"
            out["SWING"] = sw

    # ---- context
    wd = cur_day.weekday()
    out["weekly_cycle"] = {"day": WEEKDAY_PHASE.get(wd, ("WKND", ""))[0],
                           "note": WEEKDAY_PHASE.get(wd, ("", "weekend"))[1]}
    pdp = out["PD"]
    if pdp:
        pos = ("ABOVE PD VAH: strength, look for longs on retests" if last_close > pdp["vah"] else
               "BELOW PD VAL: weakness, look for shorts on retests" if last_close < pdp["val"] else
               "INSIDE PD value: balance; near the POC expect chop until a break")
        out["vs_PD_value"] = pos
    pw = out["PW"]
    if pw:
        out["vs_PW_range"] = ("ABOVE PWH: new value accepted, momentum side is LONG" if last_close > pw["pwh"] else
                              "BELOW PWL: new value accepted, momentum side is SHORT" if last_close < pw["pwl"] else
                              "INSIDE the prior week's range: no weekly acceptance yet")
    if so is not None:
        out["vs_SO"] = "ABOVE Sunday Open" if last_close > so else "BELOW Sunday Open"
    out["trend_60m"] = intraday_trend(b60)
    out["trend_30m"] = intraday_trend(b30) if b30 else None

    # ---- the level list, nearest first, with STACKED flags
    lv = []

    def add(name, price, bar):
        if price is not None:
            lv.append({"name": name, "price": _r(price, tick), "source_bar": bar})
    for key in ("PD", "EPD", "PW", "EPW", "CW", "SWING"):
        p = out.get(key)
        if p:
            tag = "Swing" if key == "SWING" else key
            for f in ("poc", "vah", "val"):
                add(f"{tag} {f.upper()}", p[f], p["source_bar"])
    if pdp:
        add("PDH", pdp["pdh"], pdp["source_bar"])
        add("PDL", pdp["pdl"], pdp["source_bar"])
    if pw:
        add("PWH", pw["pwh"], pw["source_bar"])
        add("PWL", pw["pwl"], pw["source_bar"])
        add("PWC", pw["pwc"], pw["source_bar"])
    add("SO", so, so_bar)
    add("PSO", pso, pso_bar)
    atr = a60 or 1.0
    for x in lv:
        x["dist_atr"] = round((x["price"] - last_close) / atr, 2)
        x["side"] = "RES" if x["price"] > last_close else "SUP"
        x["stacked_with"] = [y["name"] for y in lv if y is not x and abs(y["price"] - x["price"]) <= STACK_ATR * atr]
    near = sorted([x for x in lv if abs(x["dist_atr"]) <= NEAR_ATR], key=lambda x: abs(x["dist_atr"]))
    out["levels"] = lv
    out["levels_near"] = near

    # ---- entry-model candidates on the last closed bars
    out["setups"] = []
    for tf, bars in ((30, b30), (60, b60)):
        if len(bars) >= 6:
            atr_tf = next((a for a in reversed(atr_series(bars)) if a), None) or (a60 or 1.0)
            out["setups"] += detect_setups(bars, tf, lv, tick, atr_tf)
    return out


# ------------------------------------------------------------------ entry models (book ch.8)
def _touch(b, L, tol):
    return b.l - tol <= L <= b.h + tol


def detect_setups(bars, tf, levels, tick, atr, lookback=4):
    """Flag the book's entry models when they complete on one of the last `lookback` closed bars.

    EM1 double wick: two consecutive bars wick into the level and close back on the same side.
                     Entry after the second close; stop beyond both wicks.
    EM4 candle flip: bar 1 touches the level and closes on the bias side; bar 2 opens
                     against it and flips back (closes with the bias); bar 3 breaks bar 2's
                     extreme. Needs a bias already (book: "your bias must be defined first");
                     here the bias is the side of the level price is holding.
    EM3 CME break:   a bar pokes through the level (manipulation) and the next bars close
                     back and then beyond the high/low of the bar that made the poke
                     (break of internal structure). Entry on that close; stop beyond the poke.
    The newest bar may still be forming or revising (~28 min on Yahoo), so it is reported but
    flagged `unsettled`.
    """
    tol = TOUCH_TICKS * tick
    found = []
    n = len(bars)
    for end in range(max(3, n - lookback), n):
        b1, b2 = bars[end - 1], bars[end]
        for L in levels:
            p = L["price"]
            # EM1, resistance from below -> SHORT ; support from above -> LONG
            if _touch(b1, p, tol) and _touch(b2, p, tol):
                if b1.c < p and b2.c < p and b1.h >= p - tol and b2.h >= p - tol:
                    stop = max(b1.h, b2.h) + tick
                    found.append(_setup("EM1", "SHORT", tf, L, b2, b2.c, stop, atr, end == n - 1, tick))
                elif b1.c > p and b2.c > p and b1.l <= p + tol and b2.l <= p + tol:
                    stop = min(b1.l, b2.l) - tick
                    found.append(_setup("EM1", "LONG", tf, L, b2, b2.c, stop, atr, end == n - 1, tick))
            # EM4: needs three bars
            if end >= 2:
                b0 = bars[end - 2]
                # long: b0 holds above support, b1 is a flip candle (dips, closes up), b2 breaks b1 high
                if _touch(b0, p, tol) and b0.c > p and b1.l < b1.o and b1.c > b1.o and b2.h > b1.h and b2.c > b1.h:
                    found.append(_setup("EM4", "LONG", tf, L, b2, b2.c, min(b0.l, b1.l) - tick, atr, end == n - 1, tick))
                if _touch(b0, p, tol) and b0.c < p and b1.h > b1.o and b1.c < b1.o and b2.l < b1.l and b2.c < b1.l:
                    found.append(_setup("EM4", "SHORT", tf, L, b2, b2.c, max(b0.h, b1.h) + tick, atr, end == n - 1, tick))
            # EM3: poke through on b1, close back, b2 closes beyond b1's opposite extreme
            if b1.l < p - tol and b1.c > p and b2.c > b1.h:
                found.append(_setup("EM3", "LONG", tf, L, b2, b2.c, b1.l - tick, atr, end == n - 1, tick))
            if b1.h > p + tol and b1.c < p and b2.c < b1.l:
                found.append(_setup("EM3", "SHORT", tf, L, b2, b2.c, b1.h + tick, atr, end == n - 1, tick))
    # one line per (model, side, bar): stacked levels the same bar reacted to are listed together
    grp = {}
    for s in found:
        k = (s["model"], s["side"], s["bar"])
        if k not in grp:
            grp[k] = s
        elif s["level"] not in grp[k]["level"]:
            grp[k]["level"] += " + " + s["level"]
    return list(grp.values())


def _setup(model, side, tf, L, bar, entry, stop, atr, unsettled, tick):
    entry, stop = _r(entry, tick), _r(stop, tick)
    risk = abs(entry - stop)
    return {"model": model, "side": side, "tf": f"{tf}m", "level": L["name"], "level_price": L["price"],
            "level_source_bar": L["source_bar"], "stacked_with": L.get("stacked_with", []),
            "bar": _iso(bar.ts), "trigger_close": entry, "stop": stop,
            "risk_pts": round(risk, 6), "risk_atr_tf": round(risk / atr, 2) if atr else None,
            "stop_too_tight": bool(atr and risk < 0.5 * atr),     # RULES: never tighter than 0.5 ATR
            "unsettled": unsettled}


# ------------------------------------------------------------------ rendering
def to_md(m: dict) -> str:
    L = []
    L.append(f"## {m['symbol']} — LTA war map (newest bar {m['newest_bar']}, close {m['newest_close']})")
    L.append("")
    L.append(f"*NOT live unless fetched this turn. Trading day {m['trading_day']} · 60m ATR "
             f"{m['atr14_60m']} · 15m ATR {m['atr14_15m']} · profiles from {m['profile_source_tf']}m bars"
             + "*")
    L.append("")
    wc = m["weekly_cycle"]
    L.append(f"- **Weekly cycle:** {wc['day']}: {wc['note']}")
    for k in ("vs_SO", "vs_PW_range", "vs_PD_value"):
        if m.get(k):
            L.append(f"- **{k.replace('vs_', 'vs ')}:** {m[k]}")
    for k in ("trend_60m", "trend_30m"):
        t = m.get(k)
        if t:
            L.append(f"- **Intraday trend {k[6:]}:** {t['trend']}"
                     + (f" (break of structure {t['break_of_structure']})" if t.get('break_of_structure') else "")
                     + (f" — swing highs {t['last_swing_highs']}, lows {t['last_swing_lows']}" if 'last_swing_highs' in t else f" — {t.get('why', '')}"))
    L.append("")
    L.append("| profile | POC | VAH | VAL | LVNs | shape | built from → to |")
    L.append("|---|---|---|---|---|---|---|")
    for k in ("PD", "EPD", "PW", "EPW", "CW", "SWING"):
        p = m.get(k)
        if p:
            L.append(f"| {p['label']} | {p['poc']} | {p['vah']} | {p['val']} | {', '.join(map(str, p['lvn'])) or '—'} | "
                     f"{p['shape']} | {p['from_bar'][5:16]} → {p['source_bar'][5:16]} |")
    if not m.get("CW"):
        L.append(f"| CW | — | — | — | — | — | {m['CW_note']} |")
    L.append("")
    so, pso = m["SO"], m["PSO"]
    extra = []
    if so["price"] is not None:
        extra.append(f"SO {so['price']} ({so['source_bar'][5:16]})")
    if pso["price"] is not None:
        extra.append(f"PSO {pso['price']} ({pso['source_bar'][5:16]})")
    if m.get("PD"):
        extra.append(f"PDH {m['PD']['pdh']} · PDL {m['PD']['pdl']}")
    if m.get("PW"):
        extra.append(f"PWH {m['PW']['pwh']} · PWL {m['PW']['pwl']} · PWC {m['PW']['pwc']}")
    L.append("**Anchors:** " + " · ".join(extra))
    L.append("")
    L.append("**Levels within %.0f ATR, nearest first:**" % NEAR_ATR)
    L.append("")
    L.append("| level | price | side | ATR away | stacked with |")
    L.append("|---|---|---|---|---|")
    for x in m["levels_near"]:
        L.append(f"| {x['name']} | {x['price']} | {x['side']} | {x['dist_atr']:+} | {', '.join(x['stacked_with']) or '—'} |")
    L.append("")
    if m["setups"]:
        L.append("**Entry-model candidates on the last closed bars** (pattern present, edge NOT measured):")
        L.append("")
        L.append("| model | side | tf | at level(s) | bar | trigger | stop | risk (ATR of tf) | flags |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for s in m["setups"]:
            fl = []
            if s["stacked_with"]:
                fl.append("CONFLUENCE")
            if s["stop_too_tight"]:
                fl.append("STOP<0.5ATR")
            if s["unsettled"]:
                fl.append("UNSETTLED")
            L.append(f"| {s['model']} | {s['side']} | {s['tf']} | {s['level']} {s['level_price']} | {s['bar'][5:16]} | "
                     f"{s['trigger_close']} | {s['stop']} | {s['risk_atr_tf']} | {' '.join(fl) or '—'} |")
    else:
        L.append("**Entry-model candidates:** none on the last closed 30m/60m bars.")
    L.append("")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--symbols", nargs="+", default=list(SYMS))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--write", action="store_true", help="also write levels/<SYM>.{json,md} in this lane")
    a = ap.parse_args()
    maps = [war_map(s) for s in a.symbols]
    if a.json:
        print(json.dumps(maps, indent=1, default=str))
    else:
        print("\n".join(to_md(m) for m in maps))
    if a.write:
        d = pathlib.Path(__file__).resolve().parent / "levels"
        d.mkdir(exist_ok=True)
        for m in maps:
            (d / f"{m['symbol']}.json").write_text(json.dumps(m, indent=1, default=str))
            (d / f"{m['symbol']}.md").write_text(to_md(m))


if __name__ == "__main__":
    main()
