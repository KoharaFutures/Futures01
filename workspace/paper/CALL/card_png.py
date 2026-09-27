#!/usr/bin/env python3
"""Render a CALL desk callout as a large landscape card PNG, one file per symbol.

Owned by agent CALL. ANSI escapes do not render as colour on every surface the account
owner reads this on, so the card is emitted as an image where the blue and orange are
actually visible, at a size that can be read without squinting.

THE COLOURS ARE THE SHIPPED INDICES, CONVERTED BY ARITHMETIC, NOT PICKED BY EYE.
`alerts.py` fixes them as xterm-256 indices and `CALLOUT.md` forbids changing them, so the
base of each gradient is resolved through the 6x6x6 colour cube and the light/dark stops
are blends of THAT, never a hand-chosen hex:

    27  -> #005FFF   BUY / LONG
    208 -> #FF8700   SELL / SHORT
    250 -> #BCBCBC   NO TRADE

LAYOUT. Symbol top-left at 96px, direction beneath it. Entry, TP1 and SL as three large
popout panels - those are the three numbers a reader acts on, so they are the three that
are big. Secondary mechanics in a strip below, then the thesis, the weakness and the
confidence. Every `CALLOUT.md` mandatory field is present; the card summarises and
`pending.jsonl` and `journal.jsonl` hold the full text.

The panels are a translucent dark wash rather than a solid, so the gradient still reads
through them and the numbers stay white on BOTH the blue and the orange card - a single
panel treatment that works for either direction, instead of two that must be kept in sync.
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


def xterm(i: int) -> tuple[int, int, int]:
    """The actual cube arithmetic. Never an eyeballed hex."""
    if i >= 232:
        v = 8 + (i - 232) * 10
        return (v, v, v)
    n = i - 16
    lv = [0, 95, 135, 175, 215, 255]
    return (lv[n // 36], lv[(n % 36) // 6], lv[n % 6])


def blend(c, other, t):
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c, other))


WHITE, BLACK = (255, 255, 255), (0, 0, 0)
STYLE = {
    "LONG":  dict(base=xterm(27),  label="BUY / LONG",   glyph="▲", ink=WHITE),
    "SHORT": dict(base=xterm(208), label="SELL / SHORT", glyph="▼", ink=WHITE),
    None:    dict(base=xterm(250), label="NO TRADE",     glyph="■", ink=WHITE),
}


def gradient(size, base, ink):
    """Diagonal gradient: a light blend of the base at top-left to a dark one at
    bottom-right. Both stops derive from the shipped index, so the card cannot drift
    off-palette."""
    W, H = size
    top = blend(base, WHITE, 0.22 if ink == WHITE else 0.30)
    bot = blend(base, BLACK, 0.62 if ink == WHITE else 0.34)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(0, W, 4):
            t = (x / W * 0.45 + y / H * 0.55)
            c = blend(top, bot, t)
            for k in range(4):
                if x + k < W:
                    px[x + k, y] = c
    return img


def mechanics(p: dict):
    from futures_agents.config import CONTRACTS
    spec = CONTRACTS[p["symbol"]]
    side, trig, sp = p["side"], p["trigger_price"], p["stop_points"]
    fill = trig - spec.tick_size if side == "SHORT" else trig + spec.tick_size
    stop = fill + sp if side == "SHORT" else fill - sp
    t0 = p["tp_r_multiples"][0]
    tp = fill - sp * t0["r"] if side == "SHORT" else fill + sp * t0["r"]
    return spec, fill, stop, tp, t0, sp * spec.point_value * p["contracts"]


def render(plan: dict, out: pathlib.Path) -> pathlib.Path:
    st = STYLE[plan["side"]]
    ink, base = st["ink"], st["base"]
    spec, fill, stop, tp, t0, risk = mechanics(plan)
    side = plan["side"]

    W = 1700
    fsym = ImageFont.truetype(MONO_B, 104)
    fdir = ImageFont.truetype(MONO_B, 38)
    fnum = ImageFont.truetype(MONO_B, 74)
    flab = ImageFont.truetype(MONO_B, 22)
    fsub = ImageFont.truetype(MONO, 20)
    fkv = ImageFont.truetype(MONO_B, 25)
    fkl = ImageFont.truetype(MONO_B, 17)
    fbody = ImageFont.truetype(MONO, 21)
    fmeta = ImageFont.truetype(MONO, 19)

    def trim(text: str, width: int, max_lines: int) -> list[str]:
        """Drop WHOLE SENTENCES to fit, never cut mid-sentence. A thesis truncated at
        'the down-tape third of that sample carries' reverses its own meaning - the
        clause that follows is the one that says the effect is absent."""
        import re
        sents = re.split(r"(?<=[.!?]) +", text.strip())
        kept = []
        for sn in sents:
            trial = " ".join(kept + [sn])
            if len(textwrap.wrap(trial, width)) > max_lines:
                break
            kept.append(sn)
        if not kept:                      # one sentence already too long: hard-wrap it
            return textwrap.wrap(text, width)[:max_lines]
        out = textwrap.wrap(" ".join(kept), width)
        if len(kept) < len(sents):
            out.append("(full thesis in pending.jsonl)")
        return out

    # Prefer a purpose-written summary. An automatic trim keeps the FIRST sentences,
    # which on CALL-0002 ended at "...and up close said otherwise" - the bullish
    # counterpoint - and dropped the resolution that follows, so the card argued the
    # opposite of the plan. No truncation rule can know which sentence is load-bearing.
    why = trim(plan.get("why_short") or plan["why"], 118, 6)
    weak = trim(plan.get("invalidation", ""), 118, 3)
    H = 300 + 210 + 120 + (len(why) + len(weak)) * 27 + 150

    img = gradient((W, H), base, ink).convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    muted = (*ink, 170)
    faint = (*ink, 110)

    # --- outline running the outside
    d.rounded_rectangle([10, 10, W - 11, H - 11], radius=26, outline=(*ink, 235), width=4)
    d.rounded_rectangle([24, 24, W - 25, H - 25], radius=18, outline=(*ink, 70), width=1)

    # --- symbol top-left, direction beneath
    d.text((66, 54), plan["symbol"], font=fsym, fill=(*ink, 255))
    d.text((72, 176), f"{st['glyph']}  {st['label']}", font=fdir, fill=(*ink, 232))

    # --- meta top-right
    meta = [f"{plan['call_id']}   PRE-REGISTERED, NOT FILLED",
            f"basis {plan.get('basis', '?')}    as-of {plan.get('as_of_at_creation','?')[:16]}",
            f"PAPER — UNVALIDATED"]
    yy = 62
    for i, m in enumerate(meta):
        fnt = flab if i == 2 else fmeta
        d.text((W - 66 - d.textlength(m, font=fnt), yy), m, font=fnt,
               fill=(*ink, 255) if i == 2 else muted)
        yy += 34 if i < 2 else 0

    # --- the three popout panels: ENTRY, TP1, SL
    py, ph = 262, 196
    gap, m = 26, 66
    pw = (W - 2 * m - 2 * gap) // 3
    panels = [
        ("ENTRY", f"{fill:g}", f"trig {plan['trigger_price']:g}  ·  at trigger or worse"),
        (t0["label"], f"{tp:g}", f"{t0['r']}R  ·  {abs(tp - fill):g} pts to target"),
        ("SL", f"{stop:g}", f"{plan['stop_points']:g} pts  ·  ${risk:,.0f} risk"),
    ]
    for i, (lab, num, sub) in enumerate(panels):
        x = m + i * (pw + gap)
        # The sub-line must not run past its own panel into the next one.
        while d.textlength(sub, font=fsub) > pw - 52 and len(sub) > 4:
            sub = sub[:-2] + "\u2026"
        d.rounded_rectangle([x, py, x + pw, py + ph], radius=16, fill=(0, 0, 0, 92),
                            outline=(*ink, 150), width=2)
        d.text((x + 26, py + 20), lab, font=flab, fill=muted)
        d.text((x + 26, py + 54), num, font=fnum, fill=(*ink, 255))
        d.text((x + 26, py + 146), sub, font=fsub, fill=(*ink, 205))

    # --- secondary strip
    sy = py + ph + 34
    kv = [("R:R", f"{t0['r']}"), ("SIZE", f"{plan['contracts']} contract"),
          ("RISK", f"${risk:,.0f} of $240"), ("LADDER", f"x{plan.get('ladder_mult',1.0):.2f}"),
          ("WINDOW", f"{plan['created_bar_ts'][5:16].replace('T',' ')} → "
                     f"{plan['expires_bar_ts'][5:16].replace('T',' ')} ET")]
    x = m
    for lab, val in kv:
        d.text((x, sy), lab, font=fkl, fill=faint)
        d.text((x, sy + 24), val, font=fkv, fill=(*ink, 244))
        x += int(d.textlength(val, font=fkv)) + 66

    # --- reasoning
    by = sy + 84
    d.line([m, by - 16, W - m, by - 16], fill=(*ink, 55), width=1)
    d.text((m, by), "WHY", font=fkl, fill=faint)
    by += 26
    for ln in why:
        d.text((m, by), ln, font=fbody, fill=(*ink, 238))
        by += 27
    if weak:
        by += 14
        d.text((m, by), "THE WEAKNESS, STATED NOT HEDGED", font=fkl, fill=faint)
        by += 26
        for ln in weak:
            d.text((m, by), ln, font=fbody, fill=(*ink, 238))
            by += 27
    by += 16
    d.text((m, by), f"CONFIDENCE  {plan['confidence']} — a structured chart read, NOT a "
                    f"measured edge. Largest t anywhere 3.923 vs a required 5.46.",
           font=fmeta, fill=muted)

    img = Image.alpha_composite(img, ov).convert("RGB")
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
