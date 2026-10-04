#!/usr/bin/env python3
"""LTA CONCEPT CALLOUTS — render a callout (and its outcome) as a landscape PNG card.

Same visual language as the other desks' cards (near-black gloss rail, light seam, laser hue
keyed to direction: LONG blue, SHORT orange, refused/closed grey) so a colour means the same
thing on every card the owner sees. The CONTENT is this desk's own: the LTA layers.

  * header: symbol, entry model + timeframe, direction, status badge (PAPER · OPEN / REFUSED /
    TARGET / STOP / BREAKEVEN / FLAT 16:00 / EXPIRED)
  * price ladder: TARGET 2R / ENTRY / STOP, highest at the top
  * size: contracts, $ risk, budget, FULL or HALF risk (book 2/2/2)
  * right column: the LTA stack — macro bias, weekly position (vs PW range, vs SO),
    PD value, intraday trend, the level with the bar it came from, archetype, weekly cycle,
    management, and the outcome once resolved
  * footer: as-of bar, "stamped level, NOT a live quote", PAPER — UNVALIDATED · DISCRETIONARY



    python3 desk/card_png.py --new          # cards for callouts/outcomes not drawn yet
    python3 desk/card_png.py <callout_id>
    python3 desk/card_png.py --latest 3
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

SCALE = 1.0


def sc(n) -> int:
    """Scale a geometry value only. Character counts for textwrap stay unscaled."""
    return max(1, int(round(n * SCALE)))


# Laser hues, matching the CALL desk so the two desks agree on what a colour means.
LASER = {"LONG": (0, 180, 255), "SHORT": (255, 160, 20), None: (190, 190, 190)}
DEEP = {"LONG": (4, 10, 26), "SHORT": (26, 12, 2), None: (14, 14, 16)}
RED = (255, 40, 70)
GREEN = (60, 220, 130)
WHITE = (238, 246, 255)
GREY = (150, 156, 166)


def blend(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


_BACKDROP_CACHE: dict = {}


def backdrop(W, H, las, deep):
    """Deep gradient behind the card.

    Cached: this is a pure per-pixel loop in Python and it dominated render cost (~1.5s a
    card), but it depends only on (W, H, hue, base) and there are three variants in total
    - LONG, SHORT and the grey observe-only card. Rendering a backlog of 90 callouts was
    taking minutes and would have stalled a 2-minute cycle. The copy is essential: callers
    composite onto it.
    """
    key = (W, H, las, deep)
    if key in _BACKDROP_CACHE:
        return _BACKDROP_CACHE[key].copy()
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        fy = y / H
        for x in range(0, W, sc(3)):
            fx = x / W
            t = 1.0 - abs(fx - 0.34) * 1.15 - abs(fy - 0.30) * 0.85
            t = max(0.0, min(1.0, t))
            c = blend(deep, blend(deep, las, 0.24), t)
            for k in range(sc(3)):
                if x + k < W:
                    px[x + k, y] = c
    _BACKDROP_CACHE[key] = img
    return img.copy()


def hud_frame(d, box, colour, gd=None, img=None, thick=None):
    """Near-black gloss rail with a light seam whose core blows out to white."""
    x0, y0, x1, y1 = box
    gd = d if gd is None else gd
    thick = sc(30) if thick is None else thick
    seam = int(thick * 0.46)
    for i in range(thick):
        t = i / max(1, thick - 1)
        if t < 0.34:
            v = int(30 - 22 * (t / 0.34))
        elif t < 0.62:
            v = int(5 + 4 * abs(t - 0.48) / 0.14)
        else:
            v = int(7 + 21 * ((t - 0.62) / 0.38))
        d.rectangle([x0 + i, y0 + i, x1 - i, y1 - i], outline=(v, v + 1, v + 3, 255), width=1)
    if img is not None:                       # specular sweep: the cue for gloss
        W, H = img.size
        spec = Image.new("L", (W, H), 0)
        sd = ImageDraw.Draw(spec)
        for k in range(0, W + H, sc(6)):
            f = k / (W + H)
            a = int(205 * max(0.0, 1.0 - abs(f - 0.30) * 3.0)
                    + 130 * max(0.0, 1.0 - abs(f - 0.74) * 4.4))
            if a > 0:
                sd.line([k, 0, k - H, H], fill=a, width=sc(7))
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).rectangle([x0, y0, x1, y1], outline=255, width=thick)
        hl = Image.new("RGBA", (W, H), (210, 216, 228, 255))
        hl.putalpha(ImageChops.multiply(spec, mask))
        img.alpha_composite(hl)
    d.rectangle([x0, y0, x1, y1], outline=(62, 66, 74, 210), width=1)
    d.rectangle([x0 + thick - 1, y0 + thick - 1, x1 - thick + 1, y1 - thick + 1],
                outline=(4, 5, 7, 240), width=2)
    sb = [x0 + seam, y0 + seam, x1 - seam, y1 - seam]
    d.rectangle(sb, outline=(2, 3, 4, 255), width=sc(10))
    d.rectangle(sb, outline=(*colour, 200), width=sc(6))
    d.rectangle(sb, outline=(*blend(colour, (255, 255, 255), 0.55), 255), width=sc(4))
    d.rectangle(sb, outline=(255, 255, 255, 255), width=2)
    gd.rectangle(sb, outline=(*colour, 255), width=sc(13))


def panel(d, box, colour, dim=False):
    x0, y0, x1, y1 = box
    cut = sc(14)
    pts = [(x0 + cut, y0), (x1, y0), (x1, y1 - cut), (x1 - cut, y1), (x0, y1), (x0, y0 + cut)]
    d.polygon(pts, fill=(0, 0, 0, 132))
    d.line(pts + [pts[0]], fill=(*colour, 110 if dim else 255),
           width=sc(2) if dim else sc(3))


def jsonl(name):
    p = HERE / name
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def outcome(c: dict):
    for r in jsonl("resolutions.jsonl"):
        if r.get("id") == c.get("id"):
            return r
    return None


def badge(c, res):
    if c.get("verdict") == "NO_TRADE":
        return "REFUSED · NO POSITION", RED, False
    if res:
        o = res["outcome"]
        col = GREEN if res["r"] > 0 else (GREY if res["r"] == 0 else RED)
        return f"CLOSED · {o.replace('_', ' ')}", col, False
    return "PAPER · POSITION OPEN", GREEN, True


def render(c: dict, out: pathlib.Path) -> pathlib.Path:
    side = c.get("side")
    res = outcome(c)
    btxt, bcol, live = badge(c, res)
    las = LASER[side] if c.get("verdict") != "NO_TRADE" else LASER[None]
    deep = DEEP[side] if c.get("verdict") != "NO_TRADE" else DEEP[None]

    W, H = sc(1760), sc(1000)
    img = backdrop(W, H, las, deep).convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    hud_frame(d, (0, 0, W - 1, H - 1), las, gd=gd, img=ov)

    fsym = ImageFont.truetype(MONO_B, sc(84))
    fdir = ImageFont.truetype(MONO_B, sc(46))
    fbadge = ImageFont.truetype(MONO_B, sc(30))
    fnum = ImageFont.truetype(MONO_B, sc(44))
    flab = ImageFont.truetype(MONO_B, sc(18))
    fkv = ImageFont.truetype(MONO_B, sc(21))
    fkl = ImageFont.truetype(MONO_B, sc(15))
    fbody = ImageFont.truetype(MONO, sc(17))
    fmeta = ImageFont.truetype(MONO, sc(15))
    M = sc(58)
    x = M

    # ---- header
    d.text((x, M - sc(6)), c["symbol"], font=fsym, fill=WHITE)
    sw = d.textlength(c["symbol"], font=fsym)
    tag = f"LTA {c.get('model')} {c.get('tf')}"
    d.text((x + sw + sc(22), M + sc(10)), tag, font=fdir, fill=las)
    tw = d.textlength(tag, font=fdir)
    d.text((x + sw + tw + sc(44), M + sc(10)), side or "", font=fdir, fill=las)
    bw = d.textlength(btxt, font=fbadge)
    bx0 = W - M - bw - sc(28)
    d.rectangle([bx0, M + sc(4), W - M, M + sc(52)], fill=(0, 0, 0, 150), outline=(*bcol, 255), width=sc(3))
    d.text((bx0 + sc(14), M + sc(14)), btxt, font=fbadge, fill=bcol)

    lvl = f"{c.get('level') or '?'} {c.get('level_price') or ''}".strip()
    d.text((x, M + sc(96)), f"AT {lvl.upper()} · {c.get('archetype', '?')} · {c.get('ts_et', '')[:16].replace('T', ' ')} ET"[:86],
           font=fkv, fill=(206, 214, 226))
    d.text((x, M + sc(126)), "PAPER — UNVALIDATED · DISCRETIONARY · $50,000 account · $2,800 drawdown floor",
           font=fmeta, fill=(130, 138, 150))

    # ---- price ladder
    top = M + sc(176)
    rows = [(f"TARGET  {c.get('rr', 2)}R", c.get("target"), GREEN),
            ("ENTRY   " + ("on the close of the trigger bar"), c.get("entry_price"), las),
            ("STOP    beyond the wick / manipulation", c.get("initial_stop"), RED)]
    rows = [r for r in rows if isinstance(r[1], (int, float))]
    rows.sort(key=lambda r: -r[1])
    lw, rh = sc(760), sc(104)
    for i, (label, price, col) in enumerate(rows):
        box = (x, top + i * (rh + sc(14)), x + lw, top + i * (rh + sc(14)) + rh)
        panel(d, box, col, dim=not live)
        d.text((box[0] + sc(20), box[1] + sc(12)), label.split("  ")[0], font=flab, fill=col)
        d.text((box[0] + sc(20), box[1] + sc(36)), f"{price:,.2f}", font=fnum, fill=WHITE)
        note = label.split("  ", 1)[1].strip() if "  " in label else ""
        if note:
            d.text((box[0] + sc(330), box[1] + sc(50)), note[:40], font=fmeta, fill=(146, 154, 166))

    # ---- size
    sy = top + len(rows) * (rh + sc(14)) + sc(10)
    n = c.get("contracts", 0)
    d.text((x, sy), "SIZE  (book 2/2/2, scaled to the $2,800 floor)", font=fkl, fill=(140, 148, 160))
    d.text((x, sy + sc(20)),
           f"{n} contract{'' if n == 1 else 's'}   risk ${c.get('risk_dollars', 0):,.2f} of "
           f"${c.get('budget_dollars', 0):,.0f} · {c.get('risk_mode')} risk",
           font=fkv, fill=GREEN if n else RED)
    acct = c.get("account") or {}
    d.text((x, sy + sc(48)), f"equity ${acct.get('equity', 0):,.0f} · room to floor ${acct.get('room_to_floor', 0):,.0f}",
           font=fmeta, fill=(146, 154, 166))
    yy = sy + sc(74)
    for r in (c.get("refusals") or [])[:3]:
        for ln in textwrap.wrap("REFUSED: " + r, 84)[:2]:
            d.text((x, yy), ln, font=fmeta, fill=(230, 110, 120))
            yy += sc(20)

    # ---- right column: the LTA stack
    rx = x + lw + sc(52)
    ry = top

    def kv(label, value, col=WHITE, f=fbody, sub=None, subcol=(126, 134, 146), width=60):
        nonlocal ry
        d.text((rx, ry), label, font=fkl, fill=(140, 148, 160))
        for ln in (textwrap.wrap(str(value), width) or [""])[:2]:
            ry += sc(22)
            d.text((rx, ry), ln, font=f, fill=col)
        if sub:
            for ln in textwrap.wrap(str(sub), 70)[:1]:
                ry += sc(20)
                d.text((rx, ry), ln, font=fmeta, fill=subcol)
        ry += sc(28)

    kv("1 MACRO BIAS", c.get("macro_bias") or "NONE",
       sub=c.get("macro_detail"))
    kv("2 WEEKLY / HTF", c.get("vs_PW_range") or "—", sub=c.get("htf_zone"))
    kv("3 INTRADAY TREND", f"60m {c.get('intraday_trend_60m')} · 30m {c.get('intraday_trend_30m')} · "
       f"{c.get('weekly_cycle')}", sub=c.get("vs_PD_value"))
    kv("4 EXECUTION", f"{c.get('model')} {c.get('tf')} at {lvl}",
       sub=f"level from bar {c.get('level_source_bar') or '?'}")
    if res:
        kv("RESOLVED", f"{res['outcome']}   {res['r']:+.2f}R   ${res['pnl']:+,.2f}",
           GREEN if res["r"] > 0 else (GREY if res["r"] == 0 else RED), fkv, sub=f"at bar {res.get('bar')}")
    else:
        kv("MANAGE", "; ".join(m.split(" (")[0] for m in (c.get("management") or [])[:3]), width=62)
    for w in (c.get("warnings") or [])[:2]:
        d.text((rx, ry), "·  " + str(w)[:66], font=fmeta, fill=(166, 150, 120))
        ry += sc(22)

    # ---- footer
    d.text((x, H - M - sc(44)), f"as of bar {c.get('as_of_bar', '?')}", font=fmeta, fill=(146, 154, 166))
    d.text((x, H - M - sc(22)), "Yahoo feed lags ~13 min; newest bars revise ~28 min · stamped level, NOT a live quote",
           font=fmeta, fill=(176, 150, 110))
    cid = c.get("id", "")
    d.text((W - M - d.textlength(cid, font=fmeta), H - M - sc(22)), cid, font=fmeta, fill=(110, 118, 130))

    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(7)))
    Image.alpha_composite(img, ov).convert("RGB").save(out)
    return out


def card_path(c, outdir):
    res = outcome(c)
    return pathlib.Path(outdir) / f"card_{c['id']}{'_' + res['outcome'] if res else ''}.png"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--latest", type=int)
    ap.add_argument("--new", action="store_true", help="cards (open or resolved) not on disk yet")
    ap.add_argument("--outdir", default=str(HERE / "cards"))
    a = ap.parse_args()
    calls = [c for c in jsonl("callouts.jsonl") if c.get("id")]
    picked = [c for c in calls if c["id"] in a.ids]
    if a.latest:
        picked += calls[-a.latest:]
    if a.new:
        picked += [c for c in calls if not card_path(c, a.outdir).exists()]
    pathlib.Path(a.outdir).mkdir(parents=True, exist_ok=True)
    seen = set()
    for c in picked:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        p = render(c, card_path(c, a.outdir))
        print(f"CARD {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
