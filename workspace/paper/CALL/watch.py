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
  location   position in the 40-bar range -> the level is the 66% / 34% boundary

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
            if want > 0 and loc < 0.66:
                lvl = lo_r + 0.66 * rng
                need.append(f"location: above {lvl:.2f} = 66% of [{lo_r:.2f}, {hi_r:.2f}]"
                            f" ({lvl - px:+.2f} away)")
            if want < 0 and loc > 0.34:
                lvl = lo_r + 0.34 * rng
                need.append(f"location: below {lvl:.2f} = 34% of [{lo_r:.2f}, {hi_r:.2f}]"
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


def main() -> int:
    print("WATCH — levels that would open a gate. A level is something to watch, NOT a plan.")
    for sym in ("MGC", "MNQ"):
        report(sym)
    capacity()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
