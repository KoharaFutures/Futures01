#!/usr/bin/env python3
"""WATCH — what would open the gate, per symbol, in each direction, as a LEVEL.

Owner, 2026-09-28 20:19 ET: *"keep in mind i want you to be looking for future positions too and
not only concentrate on the positions you do have, this is incase you see a possible reversal."*

The failure this prevents. With a position on, every check was reporting the position and then
restating `regime.py`'s refusal -- "15m is 1-2, not unanimous" -- which is true and useless. It
says a gate is shut without saying what would open it, so the next check re-derives the same
sentence and nobody is actually watching for anything. Tunnel vision on the open book is how N194
says the desk missed the morning trend, and holding a winner is no excuse to stop scanning.

This prints, for each symbol and each direction, the components that DISSENT and the PRICE that
would flip each one. Three components must agree for `reversal()` to fire:

  trend      close vs EMA20(15m)          -> the level is the EMA20 itself
  structure  last two pivot highs / lows  -> the level is the pivot that must be taken out
  location   position in the 40-bar range -> the level is the 60% / 40% boundary (chart.py's own cut)

A level here is a TRIGGER TO WATCH, never a plan. Pre-registering still requires the gate to
actually fire, both vetoes clear, and a written plan with its weakness stated -- and `capacity`
below must have room, because two open trades already hold $90 of the $120 discretionary cap.

Owned by agent CALL.
"""
from __future__ import annotations
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from chart import load, bias  # noqa: E402
from status_card import atr14, SPEC, PERMITTED, CAP  # noqa: E402

PV = {"MGC": 10.0, "MNQ": 2.0}


def ema20(bars):
    k = 2 / 21
    e = bars[0]["c"]
    for b in bars[1:]:
        e = b["c"] * k + e * (1 - k)
    return e


def pivots(bars, k=2):
    hi, lo = [], []
    for i in range(k, len(bars) - k):
        w = bars[i - k:i + k + 1]
        if bars[i]["h"] == max(x["h"] for x in w):
            hi.append(bars[i]["h"])
        if bars[i]["l"] == min(x["l"] for x in w):
            lo.append(bars[i]["l"])
    return hi, lo


def report(sym: str) -> None:
    b = load(sym, 15)
    w = b[-40:]
    bi = bias(w)
    px, e = w[-1]["c"], ema20(w)
    hi_r, lo_r = max(x["h"] for x in w), min(x["l"] for x in w)
    rng = hi_r - lo_r
    hs, ls = pivots(w)
    a, line = atr14(sym), SPEC[sym]["line"]

    print(f"\n{sym}  15m {bi['headline']} {bi['bull']}-{bi['bear']}"
          f"{'  UNANIMOUS' if bi['unanimous'] else ''}   px {px:.2f}")
    print(f"   ATR14 {a:.2f} vs {line:g} -> {'STOOD DOWN' if a > line else 'clear'}")

    for side, want in (("BULL", +1), ("BEAR", -1)):
        need = []
        # trend
        if (px > e) != (want > 0):
            need.append(f"trend: close {'above' if want > 0 else 'below'} EMA20 {e:.2f}"
                        f" ({abs(px - e):.2f} away)")
        # structure: needs the relevant last pivot taken out
        if want > 0 and len(hs) >= 1:
            tgt = hs[-1]
            if not (len(hs) >= 2 and hs[-1] > hs[-2]):
                need.append(f"structure: take out pivot high {tgt:.2f} ({tgt - px:+.2f} away)")
        if want < 0 and len(ls) >= 1:
            tgt = ls[-1]
            if not (len(ls) >= 2 and ls[-1] < ls[-2]):
                need.append(f"structure: take out pivot low {tgt:.2f} ({tgt - px:+.2f} away)")
        # location
        if rng > 0:
            loc = (px - lo_r) / rng
            # N228: these MUST match chart.py's own location thresholds, which are
            # 60/40, not 66/34. They did not, and this tool reported a bear-location
            # level ~22 MNQ points further away than the gate actually needed all
            # evening. chart.py/regime.py are the authority; this is a display fix
            # to agree with them, and it changes no rule and authorises no trade.
            if want > 0 and loc < 0.60:
                lvl = lo_r + 0.60 * rng
                need.append(f"location: above {lvl:.2f} = 60% of [{lo_r:.2f}, {hi_r:.2f}]"
                            f" ({lvl - px:+.2f} away)")
            if want < 0 and loc > 0.40:
                lvl = lo_r + 0.40 * rng
                need.append(f"location: below {lvl:.2f} = 40% of [{lo_r:.2f}, {hi_r:.2f}]"
                            f" ({lvl - px:+.2f} away)")
        if not need:
            print(f"   {side}: all three components already agree")
        else:
            print(f"   {side} needs {len(need)}:")
            for n in need:
                print(f"      - {n}")


def capacity() -> None:
    st = json.loads((HERE / "state.json").read_text())
    used = sum(p["risk_dollars"] for p in st["open"])
    room = CAP - used
    print(f"\nCAPACITY  open risk ${used:.2f} of the ${CAP:.0f} discretionary cap"
          f" (${PERMITTED:.0f} permitted) -> ${room:.2f} of room")
    if room <= 0:
        print("  NO ROOM: a new plan would breach the cap. Scan anyway, but do not register.")
        return
    for sym in ("MGC", "MNQ"):
        a = atr14(sym)
        floor_pts = 0.5 * a                      # rule 4
        cost = floor_pts * PV[sym]               # 1 contract at the minimum legal stop
        ok = "fits" if cost <= room else "DOES NOT FIT"
        print(f"  {sym}: rule-4 floor {floor_pts:.2f}pt x ${PV[sym]:g} = ${cost:.2f}"
              f" for 1 contract -> {ok}")


def counter_trend() -> None:
    """N234: run reversal_setup() on BOTH symbols, EVERY check, in the direction the
    15m headline is NOT pointing.

    Why this exists. `regime.reversal()` only ever looks the way the current 15m
    headline points, and `report()` above only measures distance to levels that would
    open a gate in that same direction. So on an evening where both symbols read 15m
    BEARISH, a LONG was mechanically invisible to this desk - not rejected, never
    examined. The owner caught MNQ bouncing off 30430.00 and MGC off 4145.00 while
    every line this tool printed was about the short side.

    reversal_setup() is the object CHECK_PROCEDURE.md already calls "what the account
    owner means by a confident reversal". It was in the procedure but not in the loop.
    This puts it in the loop. It authorises nothing on its own - it reports.

    It is also LATENCY-SENSITIVE, which is the second half of the miss: sigma is
    measured against the 20-bar mean of the CURRENT window, so a flush that has already
    bounced reads near zero. Running it once every forty minutes guarantees seeing it
    after the fact. Running it every check is the only way the number means anything.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("rg", str(HERE / "regime.py"))
    rg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rg)
    print("\nCOUNTER-TREND (reversal_setup) — the side the 15m headline is NOT on")
    for sym in ("MGC", "MNQ"):
        try:
            r = rg.reversal_setup(sym)
        except Exception as exc:                    # never let this kill the check
            print(f"  {sym}: reversal_setup FAILED — {exc}")
            continue
        mark = "QUALIFIES" if r.get("qualifies") else "no"
        print(f"  {sym}  {mark}  side {r.get('side')}  sigma {r.get('sigma')}"
              f"  htf {r.get('htf_support') or 'none'}")
        print(f"       reclaim trigger {r.get('trigger')}  last {r.get('last')}"
              f"  volume {r.get('climax_x')}x — {r.get('climax_note')}")
        for why in r.get("reasons", []):
            print(f"       fails: {why}")


def main() -> int:
    print("WATCH — levels that would open a gate. A level is something to watch, NOT a plan.")
    for sym in ("MGC", "MNQ"):
        report(sym)
    counter_trend()
    capacity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
