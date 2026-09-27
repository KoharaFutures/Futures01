#!/usr/bin/env python3
"""Render a CALL desk callout as a LANDSCAPE card PNG, one file per symbol.

Owned by agent CALL. ANSI escapes do not render as colour on every surface the account
owner reads this on, so the card is emitted as an image where the blue and orange are
actually visible.

THE COLOURS ARE THE SHIPPED INDICES, CONVERTED BY ARITHMETIC, NOT PICKED BY EYE.
`alerts.py` fixes them as xterm-256 indices and `CALLOUT.md` forbids changing them, so
each is resolved through the 6x6x6 colour cube:

    27  -> #005FFF   BUY / LONG    background, white text
    208 -> #FF8700   SELL / SHORT  background, black text
    250 -> #BCBCBC   NO TRADE      background, black text

LAYOUT. Two columns, landscape: the mechanics on the left (the numbers a reader checks
first), the reasoning on the right (the thesis, the weakness, the confidence). Every
`CALLOUT.md` mandatory field is present - PAPER UNVALIDATED, basis, as-of, direction,
entry, stop, target, R:R, dollar risk, contracts, ladder multiplier, confidence with its
basis. The card summarises; `journal.jsonl` and `pending.jsonl` hold the full text.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import textwrap

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

INK, PAPER, DIM, RULE = "#16181d", "#fcfcfa", "#6d7076", "#d8d8d2"


def xterm(i: int) -> str:
    """The actual cube arithmetic. Never an eyeballed hex."""
    if i < 16:
        return "#000000"
    if i < 232:
        n = i - 16
        lv = [0, 95, 135, 175, 215, 255]
        r, g, b = lv[n // 36], lv[(n % 36) // 6], lv[n % 6]
    else:
        r = g = b = 8 + (i - 232) * 10
    return f"#{r:02x}{g:02x}{b:02x}"


STYLE = {"LONG": (xterm(27), "#ffffff", "BUY / LONG", "▲"),
         "SHORT": (xterm(208), "#000000", "SELL / SHORT", "▼"),
         None: (xterm(250), "#000000", "NO TRADE", "■")}


def mechanics(p: dict) -> list[tuple[str, str]]:
    from futures_agents.config import CONTRACTS
    spec = CONTRACTS[p["symbol"]]
    side, trig, sp = p["side"], p["trigger_price"], p["stop_points"]
    fill = trig - spec.tick_size if side == "SHORT" else trig + spec.tick_size
    stop = fill + sp if side == "SHORT" else fill - sp
    t0 = p["tp_r_multiples"][0]
    tp = fill - sp * t0["r"] if side == "SHORT" else fill + sp * t0["r"]
    rd = sp * spec.point_value * p["contracts"]
    w0, w1 = p["created_bar_ts"], p["expires_bar_ts"]
    return [
        ("TRIGGER", f"{'below' if side == 'SHORT' else 'above'}  {trig:g}"),
        ("ENTRY", f"~{fill:g}   at trigger or worse"),
        ("STOP", f"{stop:g}   ({sp:g} pts)"),
        (t0["label"], f"{tp:g}   ({t0['r']}R)"),
        ("R:R", f"{t0['r']}   vs desk floor 1.6"),
        ("SIZE", f"{p['contracts']} contract   ladder x{p.get('ladder_mult', 1.0):.2f}"),
        ("RISK", f"${rd:,.2f}   of ${240:,.2f} permitted"),
        ("WINDOW", f"{w0[5:16].replace('T', ' ')} -> {w1[5:16].replace('T', ' ')} ET"),
    ]


def render(plan: dict, out: pathlib.Path, W: int = 1480) -> pathlib.Path:
    bg, fg, label, glyph = STYLE[plan["side"]]
    f = ImageFont.truetype(MONO, 15)
    fb = ImageFont.truetype(MONO_B, 15)
    fk = ImageFont.truetype(MONO_B, 14)
    fh = ImageFont.truetype(MONO_B, 27)
    fs = ImageFont.truetype(MONO, 13)

    pad, band = 30, 66
    colx = pad + 26
    rcol = int(W * 0.44)
    rw = (W - rcol - pad - 26) // 9          # chars that fit in the right column
    mech = mechanics(plan)

    why = textwrap.wrap(plan["why"], rw)
    weak = textwrap.wrap(plan.get("invalidation", ""), rw)
    conf = textwrap.wrap(
        f"{plan['confidence']} — a structured chart read, NOT a measured edge. Nothing in "
        f"this repository has cleared its own threshold; the largest t anywhere is 3.923 "
        f"against a required 5.46.", rw)

    right_lines = 1 + len(why) + 2 + len(weak) + 2 + len(conf)
    H = band + 34 + max(len(mech) * 34 + 30, right_lines * 19 + 30) + 34
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # colour band
    d.rectangle([0, 0, W, band], fill=bg)
    d.text((colx, 18), f"{glyph}  {label}", font=fh, fill=fg)
    sym = f"{plan['symbol']} {plan['side']}"
    d.text((W - pad - 26 - d.textlength(sym, font=fh), 18), sym, font=fh, fill=fg)

    # status strip
    y = band + 9
    d.text((colx, y), "PAPER — UNVALIDATED", font=fb, fill=INK)
    strip = (f"{plan['call_id']}  ·  PRE-REGISTERED, NOT FILLED  ·  "
             f"basis {plan.get('basis', '?')}  ·  as-of {plan.get('as_of_at_creation', '?')[:16]}")
    d.text((W - pad - 26 - d.textlength(strip, font=fs), y + 2), strip, font=fs, fill=DIM)
    y += 24
    d.line([pad, y, W - pad, y], fill=RULE, width=1)
    d.line([rcol - 22, y + 10, rcol - 22, H - 26], fill=RULE, width=1)

    # left column: the mechanics
    ly = y + 20
    for k, v in mech:
        d.text((colx, ly + 3), k, font=fk, fill=DIM)
        d.text((colx + 108, ly), v, font=fb if k in ("TRIGGER", "STOP") else f, fill=INK)
        ly += 34

    # right column: the reasoning
    ry = y + 20
    d.text((rcol, ry), "WHY", font=fk, fill=DIM)
    ry += 19
    for ln in why:
        d.text((rcol, ry), ln, font=f, fill=INK)
        ry += 19
    ry += 12
    if weak:
        d.text((rcol, ry), "THE WEAKNESS, STATED NOT HEDGED", font=fk, fill=DIM)
        ry += 19
        for ln in weak:
            d.text((rcol, ry), ln, font=f, fill=INK)
            ry += 19
        ry += 12
    d.text((rcol, ry), "CONFIDENCE", font=fk, fill=DIM)
    ry += 19
    for ln in conf:
        d.text((rcol, ry), ln, font=f, fill=INK)
        ry += 19

    d.rectangle([0, 0, W - 1, H - 1], outline=RULE, width=1)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main() -> int:
    import sys
    sys.path.insert(0, str(HERE.parents[2]))
    ap = argparse.ArgumentParser()
    ap.add_argument("call_ids", nargs="+")
    a = ap.parse_args()
    plans = {json.loads(l)["call_id"]: json.loads(l)
             for l in (HERE / "pending.jsonl").read_text().splitlines() if l.strip()}
    for cid in a.call_ids:
        p = plans[cid]
        out = HERE / f"card_{p['symbol']}_{cid}.png"
        render(p, out)
        w, h = Image.open(out).size
        print(f"{out.name}  {w}x{h}  ratio {w/h:.2f}:1  ({out.stat().st_size//1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
