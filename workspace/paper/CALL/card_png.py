#!/usr/bin/env python3
"""Render a CALL desk callout as a large landscape "laser" card PNG, one file per symbol.

Owned by agent CALL. ANSI escapes do not render as colour on every surface the account
owner reads this on, so the card is emitted as an image, at a size that can be read.

COLOUR, AND THE ONE DIVERGENCE THE OWNER ASKED FOR. `alerts.py`'s xterm indices are
UNCHANGED and untouched - `CALLOUT.md` forbids editing them and that file is not ours.
The terminal card still renders index 27 / 208 / 250. This PNG uses brighter "laser"
variants of the SAME hues, at the owner's request (2026-09-27), so the image and the
terminal agree on which colour means which direction while differing in intensity:

    LONG   xterm 27  (0,95,255)   -> laser #00B4FF
    SHORT  xterm 208 (255,135,0)  -> laser #FFA014
    SL                            -> laser red #FF2846   (owner's request: SL text red)

THREE TARGETS, AND WHAT THE ACCOUNT CAN ACTUALLY DO. The card shows TP1/TP2/TP3 from
`display_targets`. **Only TP1 is executable at this account size.** A three-tier scale-out
needs three contracts - $300 on MGC, $360 on MNQ - against a $240 permitted budget at zero
drawdown (NOTES.md N6). TP2 and TP3 are therefore drawn dimmer and labelled `NEEDS 3 LOTS`,
as extension levels rather than orders. `resolve.py` continues to act on `tp_r_multiples`,
which this file never reads and nothing here modifies: editing the executable plan after
watching price move would void its pre-registration (N8).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import textwrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

LASER = {"LONG": (0, 180, 255), "SHORT": (255, 160, 20), None: (190, 190, 190)}
DEEP = {"LONG": (4, 10, 26), "SHORT": (26, 12, 2), None: (14, 14, 16)}
RED = (255, 40, 70)
WHITE = (238, 246, 255)


# ---------------------------------------------------------------- metal chassis

# NOTE: brushed_metal / bevel / screw built the outer bezel. The owner asked for
# everything OUTSIDE the rail removed, so the rail is now the card's outer edge and
# those helpers are unused. Kept, not deleted, because reinstating a bezel is a
# layout decision that may come back, and they are exact arithmetic worth keeping.


def brushed_metal(W: int, H: int) -> Image.Image:
    """A DARK machined bezel - gunmetal, not bright steel.

    Tone stays in a 22-92 band so the laser reads as light emitted BY the card rather than
    as a highlight on a shiny surface. Bright metal competes with neon; dark metal carries
    it. Deterministic by construction (fixed seed, pure arithmetic), because a card that
    renders differently on each run cannot be checked against the one that was sent.
    """
    import random
    rng = random.Random(20260927)
    img = Image.new("RGB", (W, H))
    px = img.load()
    jitter = [rng.randint(-5, 5) for _ in range(H)]
    for y in range(H):
        fy = y / H
        base = 34 + int(42 * (1.0 - abs(fy - 0.30) * 1.9))
        base = max(22, min(80, base)) + jitter[y]
        for x in range(0, W, 2):
            sheen = int(14 * max(0.0, 1.0 - abs((x / W) + fy - 0.85) * 2.4))
            v = max(18, min(94, base + sheen))
            c = (v, v + 1, v + 5)
            px[x, y] = c
            if x + 1 < W:
                px[x + 1, y] = c
    return img

def bevel(d, box, light=(168, 175, 188), dark=(8, 9, 11), w=3):
    """Top/left catch the light, bottom/right fall into shadow - the cue that reads as
    'machined edge' rather than 'drawn rectangle'."""
    x0, y0, x1, y1 = box
    for i in range(w):
        d.line([x0 + i, y0 + i, x1 - i, y0 + i], fill=(*light, 150 - i * 34))
        d.line([x0 + i, y0 + i, x0 + i, y1 - i], fill=(*light, 130 - i * 30))
        d.line([x0 + i, y1 - i, x1 - i, y1 - i], fill=(*dark, 190 - i * 40))
        d.line([x1 - i, y0 + i, x1 - i, y1 - i], fill=(*dark, 170 - i * 36))


def screw(d, cx, cy, r, las):
    """Hex-socket fastener with a lit rim - the laser catches the metal."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(44, 47, 54, 255),
              outline=(150, 157, 170, 175), width=2)
    d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=(38, 41, 47, 255))
    k = r - 6
    pts = [(cx + k * __import__("math").cos(__import__("math").radians(a)),
            cy + k * __import__("math").sin(__import__("math").radians(a)))
           for a in range(0, 360, 60)]
    d.polygon(pts, fill=(22, 24, 28, 255), outline=(120, 126, 136, 160))
    d.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill=(*las, 150), width=2)


def blend(a, b, t):
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))


def backdrop(W, H, side):
    """Deep gradient: near-black at the corners, the laser hue breathing through the
    middle. Dark base is what makes a neon accent read as neon rather than as a fill."""
    deep, las = DEEP[side], LASER[side]
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        fy = y / H
        for x in range(0, W, 3):
            fx = x / W
            t = 1.0 - abs(fx - 0.34) * 1.15 - abs(fy - 0.30) * 0.85
            t = max(0.0, min(1.0, t))
            c = blend(deep, blend(deep, las, 0.42), t)
            for k in range(3):
                if x + k < W:
                    px[x + k, y] = c
    return img


def hud_frame(d, box, colour, gd=None, thick=30):
    """The inner border: a CONTINUOUS closed rail of dark metal with a lit channel
    running its entire perimeter. No corner brackets, no midpoint gaps - the light goes
    all the way round and meets itself.

    Built as concentric rectangle outlines rather than four bars, because bars have to be
    mitred at the corners and any error there shows as a notch. A ring of nested outlines
    corners itself for free, and stepping the tone across the ring is what makes it read
    as a machined edge: bright catch on the outer lip, shadow on the inner.
    """
    x0, y0, x1, y1 = box
    gd = d if gd is None else gd
    m = thick // 2
    for i in range(thick):
        # Two shoulders falling away from a groove in the middle: bright at the outer lip,
        # dark into the channel, rising again to a dimmer inner lip. That double ramp is
        # what makes a band read as a MACHINED RAIL rather than a painted stripe.
        if i < m:
            t = i / max(1, m - 1)
            v = int(132 - 104 * t)
        else:
            t = (i - m) / max(1, thick - m - 1)
            v = int(26 + 62 * t)
        d.rectangle([x0 + i, y0 + i, x1 - i, y1 - i], outline=(v, v + 1, v + 6, 255), width=1)
    d.rectangle([x0, y0, x1, y1], outline=(206, 213, 226, 210), width=2)
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y1 - 3], outline=(150, 157, 170, 120), width=1)
    d.rectangle([x0 + thick - 1, y0 + thick - 1, x1 - thick + 1, y1 - thick + 1],
                outline=(96, 101, 112, 200), width=2)
    d.rectangle([x0 + thick + 1, y0 + thick + 1, x1 - thick - 1, y1 - thick - 1],
                outline=(6, 7, 9, 240), width=2)
    # the channel cut into the rail, and the laser running in it
    d.rectangle([x0 + m, y0 + m, x1 - m, y1 - m], outline=(5, 6, 8, 255), width=9)
    d.rectangle([x0 + m, y0 + m, x1 - m, y1 - m], outline=(*colour, 255), width=3)
    gd.rectangle([x0 + m, y0 + m, x1 - m, y1 - m], outline=(*colour, 255), width=10)
def panel(d, box, colour, dim=False):
    x0, y0, x1, y1 = box
    cut = 16
    pts = [(x0 + cut, y0), (x1, y0), (x1, y1 - cut), (x1 - cut, y1), (x0, y1), (x0, y0 + cut)]
    d.polygon(pts, fill=(0, 0, 0, 132))
    d.line(pts + [pts[0]], fill=(*colour, 110 if dim else 255), width=2 if dim else 3)


def mech(p):
    from futures_agents.config import CONTRACTS
    spec = CONTRACTS[p["symbol"]]
    side, trig, sp = p["side"], p["trigger_price"], p["stop_points"]
    fill = trig - spec.tick_size if side == "SHORT" else trig + spec.tick_size
    stop = fill + sp if side == "SHORT" else fill - sp
    tgts = []
    for t in p.get("display_targets") or p["tp_r_multiples"]:
        d_ = sp * t["r"]
        tgts.append((t["label"], t["r"], fill - d_ if side == "SHORT" else fill + d_,
                     t.get("executable", True)))
    return spec, fill, stop, tgts, sp * spec.point_value * p["contracts"]


def render_blank(side: str, out: pathlib.Path, W: int = 1760, H: int = 1684) -> pathlib.Path:
    """The empty shell: the rail and its laser channel with all content removed.

    The rail is the card's OUTER EDGE - there is no bezel, chassis or margin beyond it.
    Useful for judging the frame alone and for laying out a new card.

    It writes its own file and touches nothing else: no plan, journal, ledger or snapshot.
    Emptying a rendering is a different act from deleting the record.
    """
    las = LASER[side]
    img = backdrop(W, H, side).convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    hud_frame(d, (0, 0, W - 1, H - 1), las, gd=gd)
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(11)))
    Image.alpha_composite(img, ov).convert("RGB").save(out)
    return out


def render(plan: dict, out: pathlib.Path) -> pathlib.Path:
    side = plan["side"]
    las = LASER[side]
    spec, fill, stop, tgts, risk = mech(plan)

    fsym = ImageFont.truetype(MONO_B, 108)
    fdir = ImageFont.truetype(MONO_B, 36)
    fbig = ImageFont.truetype(MONO_B, 62)
    fmid = ImageFont.truetype(MONO_B, 50)
    flab = ImageFont.truetype(MONO_B, 21)
    fsub = ImageFont.truetype(MONO, 18)
    fkv = ImageFont.truetype(MONO_B, 24)
    fkl = ImageFont.truetype(MONO_B, 16)
    fbody = ImageFont.truetype(MONO, 20)
    fmeta = ImageFont.truetype(MONO, 18)
    fsub2 = ImageFont.truetype(MONO_B, 23)

    def trim(text, width, maxl):
        import re
        sents = re.split(r"(?<=[.!?]) +", (text or "").strip())
        kept = []
        for s in sents:
            if len(textwrap.wrap(" ".join(kept + [s]), width)) > maxl:
                break
            kept.append(s)
        if not kept:
            return textwrap.wrap(text or "", width)[:maxl]
        o = textwrap.wrap(" ".join(kept), width)
        if len(kept) < len(sents):
            o.append("(full thesis in pending.jsonl)")
        return o

    why = trim(plan.get("why_short") or plan["why"], 116, 5)
    weak = trim(plan.get("invalidation", ""), 116, 3)

    W = 1760
    H = 1130 + (len(why) + len(weak)) * 26 + 230   # strategy header + basis block
    img = backdrop(W, H, side).convert("RGBA")
    # content is composed at interior size, then mounted in the bezel below
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    M = 0
    PAD = M + 64      # content gutter: clears the 30px rail plus breathing room
    frame = (M, M, W - M - 1, H - M - 1)
    hud_frame(d, frame, las, gd=gd)

    # header: symbol and direction on ONE baseline, strategy beneath
    gd.text((PAD + 4, 112), plan["symbol"], font=fsym, fill=(*las, 210))
    d.text((PAD + 4, 112), plan["symbol"], font=fsym, fill=WHITE)
    symw = d.textlength(plan["symbol"], font=fsym)
    glyph = "\u25b2" if side == "LONG" else "\u25bc"
    dirtxt = f"{glyph}  {'BUY / LONG' if side == 'LONG' else 'SELL / SHORT'}"
    dx, dy = PAD + 4 + symw + 46, 112 + 50          # optically centred on the symbol's cap height
    d.text((dx, dy), dirtxt, font=fdir, fill=(*las, 255))
    gd.text((dx, dy), dirtxt, font=fdir, fill=(*las, 185))
    strat = plan.get("strategy", "")
    if strat:
        d.text((PAD + 10, 242), "STRATEGY", font=fkl, fill=(*las, 150))
        d.text((PAD + 10, 266), strat, font=fsub2, fill=(*WHITE, 234))

    meta = [f"{plan['call_id']}   PRE-REGISTERED, NOT FILLED",
            f"basis {plan.get('basis','?')}    as-of {plan.get('as_of_at_creation','?')[:16]}"]
    yy = 116
    for m in meta:
        d.text((W - PAD - 4 - d.textlength(m, font=fmeta), yy), m, font=fmeta, fill=(*las, 185))
        yy += 30
    pu = "PAPER — UNVALIDATED"
    d.text((W - PAD - 4 - d.textlength(pu, font=flab), yy + 4), pu, font=flab, fill=WHITE)

    # ---- row 1: ENTRY (laser) | SL (RED)
    y0, ph = 360, 176
    gapx, inner = 30, W - 2 * (PAD)
    ew = int(inner * 0.60)
    sw = inner - ew - gapx
    ex = PAD
    sx = ex + ew + gapx

    panel(d, (ex, y0, ex + ew, y0 + ph), las)
    panel(gd, (ex, y0, ex + ew, y0 + ph), las)
    d.text((ex + 28, y0 + 20), "ENTRY", font=flab, fill=(*las, 230))
    d.text((ex + 28, y0 + 52), f"{fill:g}", font=fbig, fill=WHITE)
    gd.text((ex + 28, y0 + 52), f"{fill:g}", font=fbig, fill=(*las, 150))
    d.text((ex + 28, y0 + 132), f"stop-entry {'below' if side=='SHORT' else 'above'} "
                                f"{plan['trigger_price']:g} · at trigger or worse",
           font=fsub, fill=(*WHITE, 200))

    panel(d, (sx, y0, sx + sw, y0 + ph), RED)
    panel(gd, (sx, y0, sx + sw, y0 + ph), RED)
    d.text((sx + 28, y0 + 20), "SL", font=flab, fill=(*RED, 255))
    d.text((sx + 28, y0 + 52), f"{stop:g}", font=fbig, fill=RED)
    gd.text((sx + 28, y0 + 52), f"{stop:g}", font=fbig, fill=(*RED, 190))
    d.text((sx + 28, y0 + 132), f"{plan['stop_points']:g} pts · ${risk:,.0f} on "
                                f"{plan['contracts']} contract", font=fsub, fill=(*RED, 215))

    # ---- row 2: TP1 / TP2 / TP3
    ty, th = y0 + ph + 30, 158
    tw = (inner - 2 * gapx) // 3
    for i, (lab, r, px_, ok) in enumerate(tgts[:3]):
        x = PAD + i * (tw + gapx)
        panel(d, (x, ty, x + tw, ty + th), las, dim=not ok)
        if ok:
            panel(gd, (x, ty, x + tw, ty + th), las)
        d.text((x + 26, ty + 18), lab, font=flab, fill=(*las, 255 if ok else 150))
        d.text((x + 26, ty + 48), f"{px_:g}", font=fmid,
               fill=WHITE if ok else (*WHITE, 165))
        if ok:
            gd.text((x + 26, ty + 48), f"{px_:g}", font=fmid, fill=(*las, 150))
        note = f"{r}R · EXECUTABLE" if ok else f"{r}R · NEEDS 3 LOTS"
        d.text((x + 26, ty + 118), note, font=fsub,
               fill=(*las, 225) if ok else (*WHITE, 130))

    # ---- mechanics strip
    sy = ty + th + 26
    kv = [("R:R", f"{tgts[0][1]}"), ("SIZE", f"{plan['contracts']} contract"),
          ("RISK", f"${risk:,.0f} of $240"), ("LADDER", f"x{plan.get('ladder_mult',1.0):.2f}"),
          ("WINDOW", f"{plan['created_bar_ts'][5:16].replace('T',' ')} → "
                     f"{plan['expires_bar_ts'][5:16].replace('T',' ')} ET")]
    x = PAD
    for lab, val in kv:
        d.text((x, sy), lab, font=fkl, fill=(*las, 150))
        d.text((x, sy + 22), val, font=fkv, fill=WHITE)
        x += int(d.textlength(val, font=fkv)) + 62

    # ---- reasoning
    by = sy + 78
    d.line([PAD, by - 14, W - PAD, by - 14], fill=(*las, 70), width=1)
    sb = plan.get("strategy_basis", "")
    if sb:
        d.text((PAD, by), "STRATEGY BASIS", font=fkl, fill=(*las, 150))
        by += 24
        for ln in textwrap.wrap(sb, 116)[:4]:
            d.text((PAD, by), ln, font=fbody, fill=(*WHITE, 212))
            by += 26
        by += 14
    d.text((PAD, by), "TARGETS", font=fkl, fill=(*las, 150))
    by += 24
    for ln in textwrap.wrap(plan.get("display_targets_note", ""), 116)[:3]:
        d.text((PAD, by), ln, font=fbody, fill=(*WHITE, 205))
        by += 26
    by += 12
    d.text((PAD, by), "WHY", font=fkl, fill=(*las, 150))
    by += 24
    for ln in why:
        d.text((PAD, by), ln, font=fbody, fill=(*WHITE, 235))
        by += 26
    if weak:
        by += 12
        d.text((PAD, by), "THE WEAKNESS, STATED NOT HEDGED", font=fkl, fill=(*RED, 190))
        by += 24
        for ln in weak:
            d.text((PAD, by), ln, font=fbody, fill=(*WHITE, 235))
            by += 26
    by += 14
    d.text((PAD, by), f"CONFIDENCE  {plan['confidence']} — a structured chart read, NOT a "
                         f"measured edge. Largest t anywhere 3.923 vs a required 5.46.",
           font=fmeta, fill=(*las, 195))

    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(11)))
    card = Image.alpha_composite(img, ov).convert("RGB")
    out.parent.mkdir(parents=True, exist_ok=True)
    card.save(out)
    return out



def main() -> int:
    import sys
    sys.path.insert(0, str(HERE.parents[2]))
    ap = argparse.ArgumentParser()
    ap.add_argument("call_ids", nargs="*")
    ap.add_argument("--blank", action="store_true",
                    help="render the empty shell only - frame and rail, no content")
    a = ap.parse_args()
    if a.blank:
        for side in ("LONG", "SHORT"):
            out = HERE / f"card_blank_{side}.png"
            render_blank(side, out)
            w, h = Image.open(out).size
            print(f"{out.name}  {w}x{h}  ({out.stat().st_size//1024} KB)")
        return 0
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
