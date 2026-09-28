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

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

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
            c = blend(deep, blend(deep, las, 0.24), t)
            for k in range(3):
                if x + k < W:
                    px[x + k, y] = c
    return img


def hud_frame(d, box, colour, gd=None, thick=34, img=None):
    """The outer rail: near-black gloss panel with a blown-out light seam cut into it.

    Modelled on the reference the owner gave - a dark car body where the panels are almost
    black and the only colour is a thin, intensely bright strip running along the seam.
    Three things make that read, and all three matter:

    1. THE PANEL IS NEARLY BLACK (tone 10-46), not mid-grey. Bright metal competes with the
       light; near-black surrenders to it, which is why the strip looks like a light source
       rather than a painted line.
    2. THE SEAM CORE BLOWS OUT TO WHITE. A real emitter overexposes at its centre, so the
       core is white and the colour sits in the falloff either side. Drawing the strip in
       flat colour is what makes neon look like a highlighter pen.
    3. A SPECULAR SWEEP RUNS ALONG THE RAIL. A broad soft highlight travelling diagonally
       across the panel is the cue for gloss; without it a dark band reads as matte card.

    The sweep needs the composed image, so `img` is passed in and the panel is drawn
    through a ring mask rather than as flat outlines.
    """
    x0, y0, x1, y1 = box
    gd = d if gd is None else gd
    seam = int(thick * 0.46)

    # --- panel: a dark gloss profile across the rail's thickness
    for i in range(thick):
        t = i / max(1, thick - 1)
        if t < 0.34:                      # outer lip, a faint catch only
            v = int(30 - 22 * (t / 0.34))
        elif t < 0.62:                    # the seam trough, essentially black
            v = int(5 + 4 * abs(t - 0.48) / 0.14)
        else:                             # inner shoulder
            v = int(7 + 21 * ((t - 0.62) / 0.38))
        d.rectangle([x0 + i, y0 + i, x1 - i, y1 - i], outline=(v, v + 1, v + 3, 255), width=1)

    # --- specular sweep: a broad diagonal highlight, masked to the rail only
    if img is not None:
        W, H = img.size
        spec = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(spec)
        for k in range(0, W + H, 6):
            f = k / (W + H)
            a = int(205 * max(0.0, 1.0 - abs(f - 0.30) * 3.0)
                    + 130 * max(0.0, 1.0 - abs(f - 0.74) * 4.4))
            if a > 0:
                sd.line([k, 0, k - H, H], fill=a, width=7)
        mask = Image.new("L", (W, H), 0)
        md = ImageDraw.Draw(mask)
        md.rectangle([x0, y0, x1, y1], outline=255, width=thick)
        spec = ImageChops.multiply(spec, mask)
        hl = Image.new("RGBA", (W, H), (210, 216, 228, 255))
        hl.putalpha(spec)
        img.alpha_composite(hl)

    # --- crisp edges either side of the panel
    d.rectangle([x0, y0, x1, y1], outline=(62, 66, 74, 210), width=1)
    d.rectangle([x0 + thick - 1, y0 + thick - 1, x1 - thick + 1, y1 - thick + 1],
                outline=(4, 5, 7, 240), width=2)

    # --- the light seam: colour falloff, then a white core that overexposes
    sb = [x0 + seam, y0 + seam, x1 - seam, y1 - seam]
    d.rectangle(sb, outline=(2, 3, 4, 255), width=11)
    d.rectangle(sb, outline=(*colour, 200), width=7)
    d.rectangle(sb, outline=(*blend(colour, (255, 255, 255), 0.55), 255), width=4)
    d.rectangle(sb, outline=(255, 255, 255, 255), width=2)
    gd.rectangle(sb, outline=(*colour, 255), width=14)

    # --- a second, dimmer strip nearer the inner edge, as on the reference
    ib = [x0 + thick - 4, y0 + thick - 4, x1 - thick + 4, y1 - thick + 4]
    d.rectangle(ib, outline=(*colour, 120), width=2)
    gd.rectangle(ib, outline=(*colour, 150), width=4)
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
    hud_frame(d, (0, 0, W - 1, H - 1), las, gd=gd, img=ov)
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(7)))
    Image.alpha_composite(img, ov).convert("RGB").save(out)
    return out


def render(plan: dict, out: pathlib.Path) -> pathlib.Path:
    """A 2.5:1 landscape card: price panels stacked left, reasoning right.

    The five numbers a reader acts on - SL, ENTRY, TP1, TP2, TP3 - run down a single
    column so they can be read as a ladder, top to bottom, in the order price would meet
    them. Everything that explains them sits to the right.

    EACH TARGET SAYS WHY IT IS THERE. The owner asked whether the TPs are key levels, and
    the answer differs per target, so the card states it per target: TP1 was PLACED on a
    structural level, while TP2 and TP3 are R multiples that land wherever the arithmetic
    puts them. `confluence.level_context` measures the distance to the nearest real level
    and says "pure R multiple" when there is none within half an ATR. Claiming structure
    for all three would be inventing significance.
    """
    side = plan["side"]
    las = LASER[side]
    spec, fill, stop, tgts, risk = mech(plan)

    fsym = ImageFont.truetype(MONO_B, 92)
    fdir = ImageFont.truetype(MONO_B, 34)
    fnum = ImageFont.truetype(MONO_B, 46)
    flab = ImageFont.truetype(MONO_B, 19)
    fsub = ImageFont.truetype(MONO, 15)
    fkv = ImageFont.truetype(MONO_B, 22)
    fkl = ImageFont.truetype(MONO_B, 15)
    fbody = ImageFont.truetype(MONO, 17)
    fmeta = ImageFont.truetype(MONO, 16)
    fstrat = ImageFont.truetype(MONO_B, 21)

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

    W, H = 2500, 1000                      # 2.5 : 1
    PAD = 78
    img = backdrop(W, H, side).convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    hud_frame(d, (0, 0, W - 1, H - 1), las, gd=gd, img=ov)

    # ---- header: symbol and direction on one baseline
    gd.text((PAD, 52), plan["symbol"], font=fsym, fill=(*las, 210))
    d.text((PAD, 52), plan["symbol"], font=fsym, fill=WHITE)
    symw = d.textlength(plan["symbol"], font=fsym)
    glyph = "\u25b2" if side == "LONG" else "\u25bc"
    dtxt = f"{glyph}  {'BUY / LONG' if side == 'LONG' else 'SELL / SHORT'}"
    d.text((PAD + symw + 40, 52 + 44), dtxt, font=fdir, fill=(*las, 255))
    gd.text((PAD + symw + 40, 52 + 44), dtxt, font=fdir, fill=(*las, 185))

    yy = 58
    for m in (f"{plan['call_id']}   PRE-REGISTERED, NOT FILLED",
              f"basis {plan.get('basis','?')}    as-of {plan.get('as_of_at_creation','?')[:16]}"):
        d.text((W - PAD - d.textlength(m, font=fmeta), yy), m, font=fmeta, fill=(*las, 185))
        yy += 26
    pu = "PAPER — UNVALIDATED"
    d.text((W - PAD - d.textlength(pu, font=flab), yy + 2), pu, font=flab, fill=WHITE)

    d.text((PAD + 4, 160), "STRATEGY", font=fkl, fill=(*las, 150))
    d.text((PAD + 4, 182), plan.get("strategy", ""), font=fstrat, fill=(*WHITE, 236))

    # ---- mechanics strip
    sy = 224
    x = PAD + 4
    for lab, val in (("R:R", f"{tgts[0][1]}"), ("SIZE", f"{plan['contracts']} contract"),
                     ("RISK", f"${risk:,.0f} of $240"),
                     ("LADDER", f"x{plan.get('ladder_mult', 1.0):.2f}"),
                     ("WINDOW", f"{plan['created_bar_ts'][5:16].replace('T',' ')} → "
                                f"{plan['expires_bar_ts'][5:16].replace('T',' ')} ET")):
        d.text((x, sy), lab, font=fkl, fill=(*las, 145))
        d.text((x, sy + 20), val, font=fkv, fill=WHITE)
        x += int(d.textlength(val, font=fkv)) + 54

    # ---- left column: the price ladder, in the order price would meet it
    try:
        import importlib.util as _iu
        _cs = _iu.spec_from_file_location("_cf", HERE / "confluence.py")
        _cf = _iu.module_from_spec(_cs)
        _cs.loader.exec_module(_cf)
    except Exception:
        _cf = None

    def why_level(px):
        if _cf is None:
            return ""
        try:
            return _cf.level_context(plan["symbol"], px)
        except Exception:
            return ""

    rows = [("SL", stop, RED, f"{plan['stop_points']:g} pts · ${risk:,.0f} risk", True)]
    rows.append(("ENTRY", fill, las,
                 f"trigger {plan['trigger_price']:g} · at trigger or worse", True))
    for lab, r, px_, ok in tgts[:3]:
        rows.append((lab, px_, las, f"{r}R · {why_level(px_)}", ok))
    if side == "SHORT":
        rows = [rows[0], rows[1]] + rows[2:]

    cw, ph, gap = 600, 122, 9
    cy = 300
    for lab, px_, col, sub, ok in rows:
        panel(d, (PAD, cy, PAD + cw, cy + ph), col, dim=not ok)
        if ok:
            panel(gd, (PAD, cy, PAD + cw, cy + ph), col)
        d.text((PAD + 22, cy + 12), lab, font=flab,
               fill=(*col, 255) if ok else (*col, 150))
        d.text((PAD + 22, cy + 36), f"{px_:g}", font=fnum,
               fill=col if lab == "SL" else (WHITE if ok else (*WHITE, 160)))
        if ok:
            gd.text((PAD + 22, cy + 36), f"{px_:g}", font=fnum, fill=(*col, 140))
        # Keep the level reason on EVERY target. The owner asked why the TPs are where
        # they are, and "not executable" is a separate fact from "sits on no level" -
        # dropping the first to show the second answers a question nobody asked.
        tag = sub if ok else f"{sub}  ·  NEEDS 3 LOTS"
        for i, ln in enumerate(textwrap.wrap(tag, 68)[:2]):
            d.text((PAD + 22, cy + 88 + i * 17), ln, font=fsub,
                   fill=(*WHITE, 205) if ok else (*WHITE, 135))
        cy += ph + gap

    # ---- right column: confluence, then the reasoning
    rx = PAD + cw + 46
    rw = (W - rx - PAD) // 10
    by = 300
    crows = []
    if _cf is not None:
        try:
            crows = _cf.evaluate(plan["symbol"], side, plan["trigger_price"])
        except Exception:
            crows = []
    if crows:
        d.text((rx, by), "CONFLUENCE ACROSS THE 13 FAMILIES — agreement is NOT confidence "
                         "(rule 1: more confluence measured WORSE; rule 2: alignment is not a virtue)",
               font=fkl, fill=(*las, 150))
        by += 22
        for r in crows:
            if r["verdict"] == "N/A":
                continue
            col = (*las, 240) if r["verdict"] == "AGREE" else (*RED, 235)
            d.text((rx, by), f"{r['verdict']:8s}", font=fkv, fill=col)
            d.text((rx + 104, by + 2), f"{r['family']:17s}", font=fbody, fill=(*WHITE, 238))
            tail = r["why"] if r["tested"] else r["why"] + "   [NEVER TESTED ON THIS SYMBOL]"
            d.text((rx + 104 + 200, by + 3), tail[:118], font=fmeta,
                   fill=(*WHITE, 150) if r["tested"] else (*RED, 190))
            by += 25
        na = ", ".join(r["family"] for r in crows if r["verdict"] == "N/A")
        d.text((rx, by), f"N/A (not evaluable from OHLCV here): {na}", font=fmeta,
               fill=(*WHITE, 125))
        by += 30

    for hdr, txt, col, lines in (
            ("STRATEGY BASIS", plan.get("strategy_basis", ""), (*las, 150), 3),
            ("TARGETS", plan.get("display_targets_note", ""), (*las, 150), 2),
            ("WHY", plan.get("why_short") or plan["why"], (*las, 150), 4),
            ("THE WEAKNESS, STATED NOT HEDGED", plan.get("invalidation", ""), (*RED, 190), 2)):
        if not txt:
            continue
        d.text((rx, by), hdr, font=fkl, fill=col)
        by += 21
        for ln in trim(txt, rw, lines):
            d.text((rx, by), ln, font=fbody, fill=(*WHITE, 232))
            by += 22
        by += 9
    d.text((rx, by), f"CONFIDENCE  {plan['confidence']} — a structured chart read, NOT a "
                     f"measured edge. Largest t anywhere 3.923 vs a required 5.46.",
           font=fmeta, fill=(*las, 195))

    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(7)))
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
