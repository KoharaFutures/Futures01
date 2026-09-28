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

FRAME = 58          # width of the machined bezel around the card


def brushed_metal(W: int, H: int) -> Image.Image:
    """A machined bezel: vertical tone ramp, horizontal brush striations, diagonal sheen.

    Deterministic by construction - a fixed seed and pure arithmetic - because a card that
    renders differently on each run cannot be compared against the one that was sent.
    """
    import random
    rng = random.Random(20260927)
    img = Image.new("RGB", (W, H))
    px = img.load()
    # per-row brush jitter, drawn once and reused across the width
    jitter = [rng.randint(-9, 9) for _ in range(H)]
    for y in range(H):
        fy = y / H
        # tone ramp: dark at top, bright shoulder at a third, mid below
        base = 58 + int(120 * (1.0 - abs(fy - 0.33) * 2.1)) if fy < 0.78 else 46 + int(26 * (1 - fy))
        base = max(28, min(196, base)) + jitter[y]
        for x in range(0, W, 2):
            sheen = int(26 * max(0.0, 1.0 - abs((x / W) + fy - 0.85) * 2.4))
            v = max(18, min(228, base + sheen))
            c = (v, v, int(v * 1.03) if v < 240 else v)
            px[x, y] = c
            if x + 1 < W:
                px[x + 1, y] = c
    return img


def bevel(d, box, light=(226, 230, 238), dark=(16, 18, 22), w=3):
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
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(74, 78, 86, 255),
              outline=(210, 216, 226, 190), width=2)
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


def hud_frame(d, box, colour, width=3, arm=58, radius=0):
    """Corner brackets rather than a closed rectangle - the frame reads as a HUD."""
    x0, y0, x1, y1 = box
    c = (*colour, 255)
    for (cx, cy, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([cx, cy, cx + dx * arm, cy], fill=c, width=width)
        d.line([cx, cy, cx, cy + dy * arm], fill=c, width=width)
    # thin connecting rails, inset, with a gap at the midpoint of each edge
    mid = (x0 + x1) // 2
    r = (*colour, 90)
    d.line([x0 + arm, y0, mid - 70, y0], fill=r, width=1)
    d.line([mid + 70, y0, x1 - arm, y0], fill=r, width=1)
    d.line([x0 + arm, y1, mid - 70, y1], fill=r, width=1)
    d.line([mid + 70, y1, x1 - arm, y1], fill=r, width=1)
    ymid = (y0 + y1) // 2
    d.line([x0, y0 + arm, x0, ymid - 60], fill=r, width=1)
    d.line([x0, ymid + 60, x0, y1 - arm], fill=r, width=1)
    d.line([x1, y0 + arm, x1, ymid - 60], fill=r, width=1)
    d.line([x1, ymid + 60, x1, y1 - arm], fill=r, width=1)


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
    H = 1130 + (len(why) + len(weak)) * 26 + 150   # strategy header + basis block
    img = backdrop(W, H, side).convert("RGBA")
    # content is composed at interior size, then mounted in the bezel below
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)

    M = 54
    frame = (M, M, W - M, H - M)
    hud_frame(gd, frame, las, width=4)
    hud_frame(d, frame, las, width=3)

    # header: symbol and direction on ONE baseline, strategy beneath
    gd.text((86, 84), plan["symbol"], font=fsym, fill=(*las, 210))
    d.text((86, 84), plan["symbol"], font=fsym, fill=WHITE)
    symw = d.textlength(plan["symbol"], font=fsym)
    glyph = "\u25b2" if side == "LONG" else "\u25bc"
    dirtxt = f"{glyph}  {'BUY / LONG' if side == 'LONG' else 'SELL / SHORT'}"
    dx, dy = 86 + symw + 46, 84 + 50          # optically centred on the symbol's cap height
    d.text((dx, dy), dirtxt, font=fdir, fill=(*las, 255))
    gd.text((dx, dy), dirtxt, font=fdir, fill=(*las, 185))
    strat = plan.get("strategy", "")
    if strat:
        d.text((92, 212), "STRATEGY", font=fkl, fill=(*las, 150))
        d.text((92, 236), strat, font=fsub2, fill=(*WHITE, 234))

    meta = [f"{plan['call_id']}   PRE-REGISTERED, NOT FILLED",
            f"basis {plan.get('basis','?')}    as-of {plan.get('as_of_at_creation','?')[:16]}"]
    yy = 92
    for m in meta:
        d.text((W - 86 - d.textlength(m, font=fmeta), yy), m, font=fmeta, fill=(*las, 185))
        yy += 30
    pu = "PAPER — UNVALIDATED"
    d.text((W - 86 - d.textlength(pu, font=flab), yy + 4), pu, font=flab, fill=WHITE)

    # ---- row 1: ENTRY (laser) | SL (RED)
    y0, ph = 320, 176
    gapx, inner = 30, W - 2 * (M + 32)
    ew = int(inner * 0.60)
    sw = inner - ew - gapx
    ex = M + 32
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
        x = M + 32 + i * (tw + gapx)
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
    x = M + 32
    for lab, val in kv:
        d.text((x, sy), lab, font=fkl, fill=(*las, 150))
        d.text((x, sy + 22), val, font=fkv, fill=WHITE)
        x += int(d.textlength(val, font=fkv)) + 62

    # ---- reasoning
    by = sy + 78
    d.line([M + 32, by - 14, W - M - 32, by - 14], fill=(*las, 70), width=1)
    sb = plan.get("strategy_basis", "")
    if sb:
        d.text((M + 32, by), "STRATEGY BASIS", font=fkl, fill=(*las, 150))
        by += 24
        for ln in textwrap.wrap(sb, 116)[:4]:
            d.text((M + 32, by), ln, font=fbody, fill=(*WHITE, 212))
            by += 26
        by += 14
    d.text((M + 32, by), "TARGETS", font=fkl, fill=(*las, 150))
    by += 24
    for ln in textwrap.wrap(plan.get("display_targets_note", ""), 116)[:3]:
        d.text((M + 32, by), ln, font=fbody, fill=(*WHITE, 205))
        by += 26
    by += 12
    d.text((M + 32, by), "WHY", font=fkl, fill=(*las, 150))
    by += 24
    for ln in why:
        d.text((M + 32, by), ln, font=fbody, fill=(*WHITE, 235))
        by += 26
    if weak:
        by += 12
        d.text((M + 32, by), "THE WEAKNESS, STATED NOT HEDGED", font=fkl, fill=(*RED, 190))
        by += 24
        for ln in weak:
            d.text((M + 32, by), ln, font=fbody, fill=(*WHITE, 235))
            by += 26
    by += 14
    d.text((M + 32, by), f"CONFIDENCE  {plan['confidence']} — a structured chart read, NOT a "
                         f"measured edge. Largest t anywhere 3.923 vs a required 5.46.",
           font=fmeta, fill=(*las, 195))

    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(11)))
    interior = Image.alpha_composite(img, ov)

    # ---- mount the card in a machined bezel with a recessed laser channel
    CW, CH = W + FRAME * 2, H + FRAME * 2
    chassis = brushed_metal(CW, CH).convert("RGBA")
    cg = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    cgd = ImageDraw.Draw(cg)
    co = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    cd = ImageDraw.Draw(co)

    # outer edge of the chassis
    cd.rounded_rectangle([3, 3, CW - 4, CH - 4], radius=22,
                         outline=(232, 236, 244, 120), width=2)
    bevel(cd, (6, 6, CW - 7, CH - 7))

    # recessed channel, cut into the metal, with the laser running in it
    ch = FRAME - 20
    cd.rounded_rectangle([ch, ch, CW - ch - 1, CH - ch - 1], radius=16,
                         fill=(14, 15, 18, 255), outline=(10, 11, 13, 255), width=2)
    for i, a in ((0, 255), (2, 120), (4, 55)):
        cd.rounded_rectangle([ch + 5 + i, ch + 5 + i, CW - ch - 6 - i, CH - ch - 6 - i],
                             radius=12, outline=(*las, a), width=2 if i == 0 else 1)
    cgd.rounded_rectangle([ch + 5, ch + 5, CW - ch - 6, CH - ch - 6], radius=12,
                          outline=(*las, 255), width=5)

    # inner lip where the bezel meets the card face
    bevel(cd, (FRAME - 5, FRAME - 5, CW - FRAME + 4, CH - FRAME + 4),
          light=(200, 206, 216), dark=(8, 9, 11), w=4)

    # fasteners at the four corners
    for sx2, sy2 in ((FRAME // 2 + 2, FRAME // 2 + 2), (CW - FRAME // 2 - 2, FRAME // 2 + 2),
                     (FRAME // 2 + 2, CH - FRAME // 2 - 2),
                     (CW - FRAME // 2 - 2, CH - FRAME // 2 - 2)):
        screw(cd, sx2, sy2, 15, las)

    chassis = Image.alpha_composite(chassis, cg.filter(ImageFilter.GaussianBlur(9)))
    chassis = Image.alpha_composite(chassis, co)
    chassis.paste(interior, (FRAME, FRAME), interior)
    chassis = chassis.convert("RGB")
    out.parent.mkdir(parents=True, exist_ok=True)
    chassis.save(out)
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
