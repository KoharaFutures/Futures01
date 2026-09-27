#!/usr/bin/env python3
"""Render CALL desk cards as a PNG, in the desk's exact colours.

Owned by agent CALL. ANSI escapes do not render as colour in every surface the account
owner reads this on, so the card is also emitted as an image where the blue and the orange
are actually visible.

THE COLOURS ARE THE SHIPPED ONES, CONVERTED EXACTLY, NOT PICKED BY EYE. `alerts.py` uses
xterm-256 indices and `CALLOUT.md` forbids changing them, so this resolves each index
through the xterm-256 cube rather than guessing a hex value:

    index 27  -> #005FFF   BUY / LONG    background, white text
    index 208 -> #FF8700   SELL / SHORT  background, black text
    index 250 -> #BCBCBC   NO TRADE      background, black text

Reads the same `pending.jsonl` and `state.json` as `card.py`, through `card.py` itself, so
the image and the terminal card cannot disagree about the numbers.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE))

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

INK = "#1c1c1c"
PAPER = "#fbfbf9"
DIM = "#6b6b6b"


def xterm(i: int) -> str:
    """Resolve an xterm-256 index to hex. Not a guess - the actual cube arithmetic."""
    if i < 16:
        base = [(0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0), (0, 0, 128),
                (128, 0, 128), (0, 128, 128), (192, 192, 192), (128, 128, 128),
                (255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 0, 255), (255, 0, 255),
                (0, 255, 255), (255, 255, 255)]
        r, g, b = base[i]
    elif i < 232:
        n = i - 16
        lv = [0, 95, 135, 175, 215, 255]
        r, g, b = lv[n // 36], lv[(n % 36) // 6], lv[n % 6]
    else:
        v = 8 + (i - 232) * 10
        r = g = b = v
    return f"#{r:02x}{g:02x}{b:02x}"


LONG_BG, LONG_FG = xterm(27), xterm(231)
SHORT_BG, SHORT_FG = xterm(208), xterm(16)
FLAT_BG, FLAT_FG = xterm(250), xterm(16)


def strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def card_lines(call_id: str) -> tuple[str, list[str], str]:
    """Reuse card.py so the image and the terminal card cannot drift apart."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("cardmod", HERE / "card.py")
    cm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cm)
    plans = [json.loads(l) for l in (HERE / "pending.jsonl").read_text().splitlines()
             if l.strip()]
    plan = next(p for p in plans if p["call_id"] == call_id)
    raw = strip_ansi(cm.pending_card(plan)).splitlines()
    # drop the alerts timestamp line, the banner line, and the trailing rule
    body = [l for l in raw[2:] if not set(l.strip()) <= {"-"} and l.strip() != ""
            or l.strip() == ""]
    while body and body[-1].strip() == "":
        body.pop()
    side = plan["side"]
    banner = (f"{'^^ BUY / LONG ^^' if side == 'LONG' else 'vv SELL / SHORT vv'}"
              f"   {plan['symbol']} {side}   "
              f"{'above' if side == 'LONG' else 'below'} {plan['trigger_price']}")
    return banner, body, side


def render(call_ids: list[str], out: pathlib.Path, size: int = 15) -> pathlib.Path:
    f = ImageFont.truetype(MONO, size)
    fb = ImageFont.truetype(MONO_B, size)
    fbig = ImageFont.truetype(MONO_B, size + 5)
    ch = size + 6
    pad, gap = 18, 26

    cards = [card_lines(c) for c in call_ids]
    width_chars = max(max(len(l) for l in body) for _, body, _ in cards)
    width_chars = max(width_chars, max(len(b) for b, _, _ in cards) + 2)
    W = pad * 2 + int(width_chars * (size * 0.6025)) + 24
    H = pad
    for _, body, _ in cards:
        H += (size + 18) + 10 + len(body) * ch + gap
    H += pad

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = pad
    for (banner, body, side), _cid in zip(cards, call_ids):
        bg, fg = ((LONG_BG, LONG_FG) if side == "LONG" else
                  (SHORT_BG, SHORT_FG) if side == "SHORT" else (FLAT_BG, FLAT_FG))
        bh = size + 18
        d.rectangle([pad, y, W - pad, y + bh], fill=bg)
        d.text((pad + 12, y + 7), banner, font=fbig, fill=fg)
        y += bh + 10
        for line in body:
            col = INK
            st = line.strip()
            if st.startswith(("PAPER", "WHY", "THE WEAKNESS", "CONFIDENCE")):
                d.text((pad + 12, y), line, font=fb, fill=INK)
                y += ch
                continue
            if st.startswith(("basis:", "(a gap")) or line.startswith("               "):
                col = DIM
            d.text((pad + 12, y), line, font=f, fill=col)
            y += ch
        y += gap
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("call_ids", nargs="+")
    ap.add_argument("--out", default=str(HERE / "cards.png"))
    a = ap.parse_args()
    p = render(a.call_ids, pathlib.Path(a.out))
    print(f"wrote {p}  ({p.stat().st_size // 1024} KB)")
    print(f"LONG bg {LONG_BG} fg {LONG_FG} | SHORT bg {SHORT_BG} fg {SHORT_FG} "
          f"| NO_TRADE bg {FLAT_BG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
