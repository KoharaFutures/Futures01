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


def auto_reason() -> str:
    """Compose the binding-reason lines FROM MEASURED STATE, so no number is ever hand-typed.

    Installed 2026-09-28 at the owner's suggestion: *"would it be more beneifical for you to have
    a python script that will generate it while you provide its parameters."* For PLAN cards the
    answer was already yes -- `card_png.py <call_id>` reads the plan from pending.jsonl and takes
    no numbers from me at all. The gap was HERE: the status card took its three reason lines as a
    command-line string, so every check I retyped the two ATRs by hand into the one artefact the
    owner actually reads. One wrong digit and the card states a veto level that was never measured.

    The reasons are now DERIVED, in priority order, and the ATRs come from atr14() -- the same
    function that draws them on the card, so the text and the panel can never disagree.
    """
    import datetime, zoneinfo
    now = datetime.datetime.now(zoneinfo.ZoneInfo("America/New_York"))
    lines = []

    stood = []
    clear = []
    for sym in ("MGC", "MNQ"):
        a, line = atr14(sym), SPEC[sym]["line"]
        (stood if a > line else clear).append(f"{sym} {a:.2f}{'>' if a > line else '<'}{line:g}")
    if stood:
        lines.append("VOL STAND-DOWN: " + ", ".join(stood))
        if clear:
            lines.append("clear: " + ", ".join(clear))
    else:
        lines.append("ATRs CLEAR: " + ", ".join(clear) + " - vetoes off")

    if datetime.time(15, 0) <= now.time() < datetime.time(16, 0):
        lines.append("RULE 5: no intraday entry 15:00-16:00 (z -4.43)")

    gate = []
    for sym in ("MGC", "MNQ"):
        bi = bias(load(sym, 15)[-40:])
        if not bi["unanimous"]:
            gate.append(f"{sym} {bi['bull']}-{bi['bear']}")
    if gate:
        lines.append("GATE SHUT: 15m not unanimous (" + ", ".join(gate) + ")")
    else:
        lines.append("15m unanimous on both - gate open")

    return "\n".join(lines[:3])


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
    cost = ""
    try:
        cost = (HERE / "standdown_cost.txt").read_text().strip()
    except OSError:
        pass
    return {"state": st, "pending": pending, "rows": rows, "basis": basis, "cost": cost}


def render(out: pathlib.Path, reason: str) -> pathlib.Path:
    d = gather()
    side = None                                  # NO TRADE -> grey, always
    W, H = C.sc(1760), C.sc(704)                 # 2.5:1, same family as the plan card

    # SILVER, DIAGONAL, WITH A RADIAL HOTSPOT AT THE TOP-RIGHT CORNER. Owner's request,
    # 2026-09-28 14:56. Still inside CALLOUT.md's grey NO TRADE family - silver IS grey - so
    # the card cannot be read as a direction in peripheral vision, which is the only thing the
    # colour rule actually protects.
    #
    # Built small and upscaled. A radial falloff computed per-pixel at 5280x2112 is ~11M
    # Python-level operations; computed at 1/32 scale and resized with LANCZOS it is identical
    # to the eye, because a smooth gradient is exactly the signal an interpolating resize
    # reconstructs without artefact.
    import numpy as np
    LIGHT = np.array([222, 226, 232], dtype=np.float32)   # silver, at the hotspot
    DARK = np.array([22, 25, 30], dtype=np.float32)       # dark silver, everywhere else
    sw, sh = 220, 88
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    cx, cy = sw * 0.985, sh * 0.02                         # the corner itself, not near it
    r = np.hypot((xx - cx) / (sw * 0.52), (yy - cy) / (sh * 0.95))
    glow = np.clip(1.0 - r, 0.0, 1.0) ** 1.9               # smooth, tight falloff
    # a faint diagonal wash underneath so the card reads as lit from that corner rather than
    # as a dark rectangle with a lamp stuck on it
    diag = np.clip(((xx / sw) - (yy / sh) + 1.0) / 2.0, 0.0, 1.0) * 0.16
    t = np.clip(glow + diag, 0.0, 1.0)[..., None]
    small = (DARK + (LIGHT - DARK) * t).astype(np.uint8)
    img = Image.fromarray(small, "RGB").resize((W, H), Image.LANCZOS)
    dr = ImageDraw.Draw(img)

    px = img.load()

    def lum_at(x: int, y: int, span: int = 0) -> float:
        """Brightest background under the text. With the light in one corner a y-only rule
        (what the vertical version used) is wrong for every right-hand column, and a
        single-point sample is wrong for any string that STARTS on dark and ENDS in the
        glow - which is exactly the STOOD DOWN flag. Take the max across the run."""
        yi = min(max(int(y), 0), H - 1)
        best = 0.0
        steps = 6 if span else 1
        for k in range(steps):
            xi = min(max(int(x + (span * k) / max(steps - 1, 1)), 0), W - 1)
            r_, g_, b_ = px[xi, yi]
            best = max(best, 0.2126 * r_ + 0.7152 * g_ + 0.0722 * b_)
        return best

    CROSS = 140

    def ink(y, x=C.sc(44), span=0):
        return (16, 18, 22) if lum_at(x, y + C.sc(12), span) > CROSS else (238, 246, 255)

    def dim(y, x=C.sc(44), span=0):
        return (74, 78, 84) if lum_at(x, y + C.sc(10), span) > CROSS else (168, 170, 176)

    def accent(y, x=C.sc(44), span=0):
        return (70, 74, 82) if lum_at(x, y + C.sc(10), span) > CROSS else (194, 196, 202)

    def danger(y, x=C.sc(44), span=0):
        return (150, 8, 32) if lum_at(x, y + C.sc(10), span) > CROSS else C.RED

    def money(y, x=C.sc(44)):
        return (140, 84, 0) if lum_at(x, y + C.sc(10)) > CROSS else (255, 190, 90)

    las = accent(0)
    f_big = ImageFont.truetype(C.MONO_B, C.sc(58))
    f_hd = ImageFont.truetype(C.MONO_B, C.sc(30))
    f_row = ImageFont.truetype(C.MONO_B, C.sc(26))
    f_sm = ImageFont.truetype(C.MONO, C.sc(19))
    f_tiny = ImageFont.truetype(C.MONO, C.sc(16))

    dr.rectangle([0, 0, W - 1, H - 1], outline=(96, 100, 108), width=C.sc(3))
    now = datetime.now(ZoneInfo("America/New_York"))
    dr.text((C.sc(44), C.sc(34)), now.strftime("%-I:%M %p ET"), font=f_big, fill=ink(C.sc(34)))
    dr.text((C.sc(44), C.sc(112)), "NO TRADE — DESK STATUS", font=f_hd, fill=accent(C.sc(112)))

    y = C.sc(178)
    for r in d["rows"]:
        tag = "STOOD DOWN" if r["stood"] else "CLEAR"
        col = danger(y, C.sc(1230), C.sc(220)) if r["stood"] else accent(y, C.sc(1230), C.sc(220))
        dr.text((C.sc(44), y), f"{r['sym']}", font=f_row, fill=ink(y))
        dr.text((C.sc(150), y), f"{r['px']:>10.2f}", font=f_row, fill=ink(y, C.sc(150)))
        dr.text((C.sc(330), y), f"15m {r['head']:<10} {r['tally']}"
                                f"{'  UNANIMOUS' if r['unan'] else ''}", font=f_row, fill=accent(y, C.sc(330), C.sc(420)))
        dr.text((C.sc(830), y), f"ATR {r['atr']:>7.2f}", font=f_row, fill=ink(y, C.sc(830), C.sc(190)))
        dr.text((C.sc(1030), y), f"line {r['line']:>5.0f}", font=f_row, fill=accent(y, C.sc(1030), C.sc(160)))
        dr.text((C.sc(1230), y), tag, font=f_row, fill=col)
        y += C.sc(46)

    st = d["state"]
    y += C.sc(14)
    dr.text((C.sc(44), y), f"BOOK   {len(d['pending'])} pending   {len(st['open'])} open"
                           f"   drawdown ${st['drawdown']:,.2f}", font=f_row, fill=ink(y))
    y += C.sc(42)
    closed = [c for c in st["closed"] if c["call_id"] != "CALL-0002"]
    wins = [c for c in closed if c.get("r_multiple", 0) > 0]
    exp = sum(c.get("r_multiple", 0) for c in closed) / len(closed) if closed else float("nan")
    dr.text((C.sc(44), y),
            f"MEASURED  n={len(closed)}  wins {len(wins)}  losses {len(closed)-len(wins)}"
            f"   E[R] {exp:+.3f}   ${2800 - st['drawdown']:,.0f} to the floor",
            font=f_sm, fill=accent(y))
    y += C.sc(34)
    # THE PRICE OF THE CAUTION. A veto that is never costed always looks free (DECISIONS.md),
    # so when a stand-down binds the card carries what it has foreclosed since it went on -
    # the movement actually available, as an upper bound, beside the marginal cost given that
    # the reversal gate may not have fired at all. The owner should not have to ask.
    if any(r["stood"] for r in d["rows"]) and d.get("cost"):
        dr.text((C.sc(44), y), d["cost"], font=f_sm, fill=money(y))
        y += C.sc(32)
    for line in reason.split("\n")[:3]:
        dr.text((C.sc(44), y), line, font=f_sm, fill=ink(y))
        y += C.sc(30)

    # THE SEVEN-FRAME TABLE. The owner reads cards, not terminals, so the frame table has to
    # live here or it does not reach him. Compressed to two rows because a phone screen is the
    # target: symbol down the left, frames across, each cell the headline plus its tally so a
    # 2-0 can never be read as a 3-0 (chart.py's rule, carried onto the card).
    y += C.sc(10)
    frames = [(1, "1m"), (5, "5m"), (15, "15m"), (60, "60m"), (240, "4h"), (1440, "D")]
    x0, colw = C.sc(150), C.sc(200)
    dr.text((C.sc(44), y), "FRAMES", font=f_tiny, fill=accent(y))
    for i, (_, lbl) in enumerate(frames):
        dr.text((x0 + i * colw, y), lbl, font=f_tiny, fill=accent(y, x0 + i * colw))
    y += C.sc(28)
    for sym in ("MGC", "MNQ"):
        dr.text((C.sc(44), y), sym, font=f_sm, fill=ink(y))
        for i, (mins, _) in enumerate(frames):
            if sym == "MGC" and mins == 1440:
                # CALLOUT.md §4: MGC daily is unusable unadjusted in BOTH stores - intraday
                # sum -2.0079 against a boundary-gap sum of +2.9584, p<0.0001. Printing a
                # headline for it would put a number on the card that the brief forbids using.
                dr.text((x0 + i * colw, y), "NOT ELIG", font=f_sm, fill=dim(y, x0 + i * colw))
                continue
            try:
                bb = load(sym, mins)
                cell = "n/a" if len(bb) < 25 else None
                if cell is None:
                    bi2 = bias(bb[-40:])
                    hd = {"BULLISH": "BULL", "BEARISH": "BEAR"}.get(bi2["headline"], "CONF")
                    cell = f"{hd} {bi2['bull']}-{bi2['bear']}"
                    col = (C.LASER["LONG"] if hd == "BULL"
                           else C.LASER["SHORT"] if hd == "BEAR" else accent(y, x0 + i * colw))
                else:
                    col = dim(y, x0 + i * colw)
            except Exception:
                cell, col = "n/a", dim(y, x0 + i * colw)
            dr.text((x0 + i * colw, y), cell, font=f_sm, fill=col)
        y += C.sc(34)
    dr.text((C.sc(44), y), "MGC DAILY/WEEKLY NOT ELIGIBLE - roll audit fails p<0.0001 (CALLOUT.md §4)",
            font=f_tiny, fill=dim(y))

    dr.text((C.sc(44), H - C.sc(46)),
            f"PAPER — UNVALIDATED   basis {d['basis']}   as-of {d['rows'][0]['bar']} 15m bar"
            f"   win rate and payoff undefined at n={len(closed)} (rule 3)",
            font=f_tiny, fill=dim(H - C.sc(46)))
    img.save(out)
    return out


def main() -> int:
    C.SCALE = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
    arg = sys.argv[2] if len(sys.argv) > 2 else "--auto"
    reason = auto_reason() if arg == "--auto" else arg
    out = render(HERE / "card_STATUS.png", reason)
    w, h = Image.open(out).size
    print(f"{out.name}  {w}x{h}  ratio {w/h:.2f}:1  ({out.stat().st_size//1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
