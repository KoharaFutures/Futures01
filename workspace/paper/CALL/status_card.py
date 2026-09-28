#!/usr/bin/env python3
"""The desk's state as a CARD, for the checks where there is no plan to render.

Owned by agent CALL. Built 2026-09-28 at the owner's instruction: *"keep in mind that i am
busy and i would typically only look at the call out cards."*

THE FAILURE THIS FIXES. `card_png.py` renders a PLAN. Between 12:43 and 14:30 the book was
empty, so it rendered nothing, so the owner - who reads cards and not paragraphs - received
NO signal of any kind for nearly two hours while the desk wrote long reports into a terminal
he was not looking at. An empty book is a decision, and a decision that never reaches the
person whose account it is has not been communicated. Every check now emits a card.

COLOURS ARE CALLOUT.md's AND ARE NOT A CHOICE. NO TRADE is grey (xterm 250 -> laser 190),
LONG blue, SHORT orange. A status card is a NO TRADE card and therefore grey, so it can
never be mistaken in peripheral vision for a direction.
"""
from __future__ import annotations

import json
import math
import pathlib
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402
import card_png as C  # noqa: E402
from chart import load, bias  # noqa: E402
import regime as R  # noqa: E402

SPEC = {"MGC": {"pv": 10.0, "line": 10.0}, "MNQ": {"pv": 2.0, "line": 58.0}}
PERMITTED, CAP = 240.0, 120.0


def atr14(sym: str) -> float:
    b = load(sym, 15)
    trs = [max(b[i]["h"] - b[i]["l"], abs(b[i]["h"] - b[i - 1]["c"]),
               abs(b[i]["l"] - b[i - 1]["c"])) for i in range(1, len(b))]
    return sum(trs[-14:]) / 14.0


def gather() -> dict:
    st = json.loads((HERE / "state.json").read_text())
    plans = [json.loads(l) for l in (HERE / "pending.jsonl").read_text().splitlines() if l.strip()]
    pending = [p for p in plans if p.get("status") == "PENDING"]
    rows = []
    for sym in ("MGC", "MNQ"):
        b = load(sym, 15)
        bi = bias(b[-40:])
        a = atr14(sym)
        rows.append({
            "sym": sym, "px": b[-1]["c"], "bar": b[-1]["ts"][11:16],
            "head": bi["headline"], "tally": f"{bi['bull']}-{bi['bear']}",
            "unan": bi["unanimous"], "atr": a, "line": SPEC[sym]["line"],
            "stood": a > SPEC[sym]["line"],
            "cap_x": CAP / (a * SPEC[sym]["pv"]),
        })
    basis = (HERE / "BASIS").read_text().strip()
    return {"state": st, "pending": pending, "rows": rows, "basis": basis}


def render(out: pathlib.Path, reason: str) -> pathlib.Path:
    d = gather()
    side = None                                  # NO TRADE -> grey, always
    las, deep = C.LASER[side], C.DEEP[side]
    W, H = C.sc(1760), C.sc(704)                 # 2.5:1, same family as the plan card
    img = Image.new("RGB", (W, H), deep)
    dr = ImageDraw.Draw(img)
    f_big = ImageFont.truetype(C.MONO_B, C.sc(58))
    f_hd = ImageFont.truetype(C.MONO_B, C.sc(30))
    f_row = ImageFont.truetype(C.MONO_B, C.sc(26))
    f_sm = ImageFont.truetype(C.MONO, C.sc(19))
    f_tiny = ImageFont.truetype(C.MONO, C.sc(16))

    dr.rectangle([0, 0, W - 1, H - 1], outline=las, width=C.sc(3))
    now = datetime.now(ZoneInfo("America/New_York"))
    dr.text((C.sc(44), C.sc(34)), now.strftime("%-I:%M %p ET"), font=f_big, fill=C.WHITE)
    dr.text((C.sc(44), C.sc(112)), "NO TRADE — DESK STATUS", font=f_hd, fill=las)

    y = C.sc(178)
    for r in d["rows"]:
        tag = "STOOD DOWN" if r["stood"] else "CLEAR"
        col = C.RED if r["stood"] else las
        dr.text((C.sc(44), y), f"{r['sym']}", font=f_row, fill=C.WHITE)
        dr.text((C.sc(150), y), f"{r['px']:>10.2f}", font=f_row, fill=C.WHITE)
        dr.text((C.sc(330), y), f"15m {r['head']:<10} {r['tally']}"
                                f"{'  UNANIMOUS' if r['unan'] else ''}", font=f_row, fill=las)
        dr.text((C.sc(830), y), f"ATR {r['atr']:>7.2f}", font=f_row, fill=C.WHITE)
        dr.text((C.sc(1030), y), f"line {r['line']:>5.0f}", font=f_row, fill=las)
        dr.text((C.sc(1230), y), tag, font=f_row, fill=col)
        y += C.sc(46)

    st = d["state"]
    y += C.sc(14)
    dr.text((C.sc(44), y), f"BOOK   {len(d['pending'])} pending   {len(st['open'])} open"
                           f"   drawdown ${st['drawdown']:,.2f}", font=f_row, fill=C.WHITE)
    y += C.sc(42)
    closed = [c for c in st["closed"] if c["call_id"] != "CALL-0002"]
    wins = [c for c in closed if c.get("r_multiple", 0) > 0]
    exp = sum(c.get("r_multiple", 0) for c in closed) / len(closed) if closed else float("nan")
    dr.text((C.sc(44), y),
            f"MEASURED  n={len(closed)}  wins {len(wins)}  losses {len(closed)-len(wins)}"
            f"   E[R] {exp:+.3f}   ${2800 - st['drawdown']:,.0f} to the floor",
            font=f_sm, fill=las)
    y += C.sc(38)
    for line in reason.split("\n")[:3]:
        dr.text((C.sc(44), y), line, font=f_sm, fill=C.WHITE)
        y += C.sc(30)

    # THE SEVEN-FRAME TABLE. The owner reads cards, not terminals, so the frame table has to
    # live here or it does not reach him. Compressed to two rows because a phone screen is the
    # target: symbol down the left, frames across, each cell the headline plus its tally so a
    # 2-0 can never be read as a 3-0 (chart.py's rule, carried onto the card).
    y += C.sc(10)
    frames = [(1, "1m"), (5, "5m"), (15, "15m"), (60, "60m"), (240, "4h"), (1440, "D")]
    x0, colw = C.sc(150), C.sc(200)
    dr.text((C.sc(44), y), "FRAMES", font=f_tiny, fill=las)
    for i, (_, lbl) in enumerate(frames):
        dr.text((x0 + i * colw, y), lbl, font=f_tiny, fill=las)
    y += C.sc(28)
    for sym in ("MGC", "MNQ"):
        dr.text((C.sc(44), y), sym, font=f_sm, fill=C.WHITE)
        for i, (mins, _) in enumerate(frames):
            if sym == "MGC" and mins == 1440:
                # CALLOUT.md §4: MGC daily is unusable unadjusted in BOTH stores - intraday
                # sum -2.0079 against a boundary-gap sum of +2.9584, p<0.0001. Printing a
                # headline for it would put a number on the card that the brief forbids using.
                dr.text((x0 + i * colw, y), "NOT ELIG", font=f_sm, fill=(120, 120, 124))
                continue
            try:
                bb = load(sym, mins)
                cell = "n/a" if len(bb) < 25 else None
                if cell is None:
                    bi2 = bias(bb[-40:])
                    hd = {"BULLISH": "BULL", "BEARISH": "BEAR"}.get(bi2["headline"], "CONF")
                    cell = f"{hd} {bi2['bull']}-{bi2['bear']}"
                    col = (C.LASER["LONG"] if hd == "BULL"
                           else C.LASER["SHORT"] if hd == "BEAR" else las)
                else:
                    col = (120, 120, 124)
            except Exception:
                cell, col = "n/a", (120, 120, 124)
            dr.text((x0 + i * colw, y), cell, font=f_sm, fill=col)
        y += C.sc(34)
    dr.text((C.sc(44), y), "MGC DAILY/WEEKLY NOT ELIGIBLE - roll audit fails p<0.0001 (CALLOUT.md §4)",
            font=f_tiny, fill=(150, 150, 155))

    dr.text((C.sc(44), H - C.sc(46)),
            f"PAPER — UNVALIDATED   basis {d['basis']}   as-of {d['rows'][0]['bar']} 15m bar"
            f"   win rate and payoff undefined at n={len(closed)} (rule 3)",
            font=f_tiny, fill=(150, 150, 155))
    img.save(out)
    return out


def main() -> int:
    C.SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    reason = sys.argv[2] if len(sys.argv) > 2 else "No plan: both symbols stood down on volatility."
    out = render(HERE / "card_STATUS.png", reason)
    w, h = Image.open(out).size
    print(f"{out.name}  {w}x{h}  ratio {w/h:.2f}:1  ({out.stat().st_size//1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
