#!/usr/bin/env python3
"""Forward-projected levels: where price has NOT been yet, not where it has.

Owned by agent CALL.

THE DEFECT THIS FIXES. Every trigger this desk had written - MGC 4289.10, MNQ 30767.25 -
was a level price had ALREADY TRADED: a prior low, a prior swing high. Those are RECLAIM
levels. They are reactive by construction, they can only ever be placed behind the market,
and a desk that only quotes them is always describing where price has been.

A forward level is computed from the geometry of the CURRENT leg and projects to prices
that have not printed since the leg began. Three sources, all arithmetic:

  1. FIBONACCI RETRACEMENT of the live leg - 38.2 / 50.0 / 61.8 / 78.6% of the distance
     travelled. These sit ABOVE a down-leg's low and have not been touched since it formed.
  2. SESSION VWAP and its standard-deviation bands, rebuilt each bar from real volume. VWAP
     moves forward with the session; it is not a historical price.
  3. AN ATR REACH ENVELOPE - how far price can plausibly travel in the next N bars at the
     current ATR. This bounds the others: a level outside the reach is not a level this
     horizon can get to, however pretty the arithmetic.

WHAT THE REPOSITORY SAYS ABOUT THESE, WHICH IS NOT NOTHING.
  - FIBONACCI is one of the six families MGC's profile GENERATES. It is EXCLUDED on MNQ, and
    `profiles.py` records why: "retracement depth needs a stable leg, and MNQ's legs are the
    shortest-lived - tested on MGC instead." So a fib level on MNQ is untested here, and the
    author's stated reason is precisely that MNQ's legs do not hold.
  - VWAP is excluded on BOTH MGC and MNQ, and `D52` records that at 1440m the band-1
    half-width is under one tick, so every daily VWAP strategy is a bar-shape strategy
    wearing a VWAP name. Intraday session VWAP computed here from 5m volume does not inherit
    that defect, but it inherits the profile exclusion: never tested on either symbol.
  - Rule 8 kills ORB and ICT, and records that FVG and order-block fill rates are reproduced
    by RANDOM zones. That finding is about those constructions, not about fibs - but it is
    the standing warning that a zone which looks meaningful may be reproducible by chance,
    and nothing here has been tested against a random-level control.

So these are projections, not predictions, and the card must say which family each came
from and whether that family was ever generated for that symbol.
"""
from __future__ import annotations

import importlib.util
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("_rs", HERE / "resolve.py")
_rs = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_rs)

FIBS = ((0.382, "38.2%"), (0.5, "50.0%"), (0.618, "61.8%"), (0.786, "78.6%"))


def _atr(rows, n=14):
    t = [max(rows[i]["h"] - rows[i]["l"], abs(rows[i]["h"] - rows[i - 1]["c"]),
             abs(rows[i]["l"] - rows[i - 1]["c"])) for i in range(1, len(rows))]
    return sum(t[-n:]) / n if t else 0.0


def leg(symbol: str, frame: int = 15, lookback: int = 40):
    """The live leg: from the extreme that started the move to the extreme that ends it."""
    bars = _rs.load_bars(symbol, frame)[-lookback:]
    hi = max(bars, key=lambda x: x["h"])
    lo = min(bars, key=lambda x: x["l"])
    down = bars.index(lo) > bars.index(hi)
    return {"from": hi["h"] if down else lo["l"], "to": lo["l"] if down else hi["h"],
            "direction": "DOWN" if down else "UP",
            "from_ts": (hi if down else lo)["ts"], "to_ts": (lo if down else hi)["ts"],
            "size": abs(hi["h"] - lo["l"])}


def session_vwap(symbol: str, frame: int = 5, bars_back: int = 78):
    """Session VWAP and 1-sigma bands from real volume. Returns None if volume is absent -
    a VWAP computed over zero-volume bars is a mean wearing a VWAP name."""
    bars = [b for b in _rs.load_bars(symbol, frame)[-bars_back:] if b["v"] > 0]
    if len(bars) < 10:
        return None
    pv = sum(((b["h"] + b["l"] + b["c"]) / 3.0) * b["v"] for b in bars)
    vol = sum(b["v"] for b in bars)
    vwap = pv / vol
    var = sum(b["v"] * (((b["h"] + b["l"] + b["c"]) / 3.0) - vwap) ** 2 for b in bars) / vol
    sd = var ** 0.5
    return {"vwap": vwap, "upper": vwap + sd, "lower": vwap - sd, "bars": len(bars)}


def reach(symbol: str, frame: int = 5, bars_ahead: int = 6) -> float:
    """How far price can plausibly travel in the next `bars_ahead` bars at current ATR.
    Bounds every projection: a level outside the reach is not reachable on this horizon."""
    return _atr(_rs.load_bars(symbol, frame)) * bars_ahead


def forward_levels(symbol: str, frame: int = 15, horizon_bars: int = 6) -> dict:
    """Every forward level, each tagged with its family and whether that family was ever
    generated for this symbol."""
    from futures_agents.strategies.profiles import SYMBOL_PROFILES
    prof = SYMBOL_PROFILES.get(symbol)
    tested = set(prof.groups) if prof is not None else set()
    bars5 = _rs.load_bars(symbol, 5)
    last = bars5[-1]["c"]
    lg = leg(symbol, frame)
    rch = reach(symbol, 5, horizon_bars)
    out = []

    span = lg["from"] - lg["to"]          # positive on a down-leg
    for f, name in FIBS:
        px = lg["to"] + span * f
        out.append({"family": "FIBONACCI", "label": f"fib {name}", "price": round(px, 4),
                    "tested": "FIBONACCI" in tested,
                    "distance": round(px - last, 2),
                    "within_reach": abs(px - last) <= rch})

    vw = session_vwap(symbol)
    if vw:
        for key, name in (("vwap", "session VWAP"), ("upper", "VWAP +1σ"), ("lower", "VWAP −1σ")):
            out.append({"family": "VWAP", "label": name, "price": round(vw[key], 4),
                        "tested": "VWAP" in tested,
                        "distance": round(vw[key] - last, 2),
                        "within_reach": abs(vw[key] - last) <= rch})

    out.sort(key=lambda r: abs(r["distance"]))
    return {"last": last, "leg": lg, "reach": round(rch, 2),
            "horizon_bars": horizon_bars, "levels": out}


def main() -> int:
    import sys
    for sym in (sys.argv[1:] or ["MGC", "MNQ"]):
        d = forward_levels(sym)
        lg = d["leg"]
        print(f"\n=== {sym}  last {d['last']:.2f} ===")
        print(f"  live leg {lg['direction']}: {lg['from']:.2f} ({lg['from_ts'][5:16]}) -> "
              f"{lg['to']:.2f} ({lg['to_ts'][5:16]}), {lg['size']:.2f} pts")
        print(f"  ATR reach over the next {d['horizon_bars']} x 5m bars: ±{d['reach']:.2f} pts")
        for r in d["levels"]:
            flag = "" if r["tested"] else "  [family NEVER generated for this symbol]"
            mark = "reachable" if r["within_reach"] else "OUT OF REACH"
            print(f"    {r['label']:<14} {r['price']:>10.2f}  {r['distance']:+8.2f}  "
                  f"{mark:<12}{flag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
