#!/usr/bin/env python3
"""Render an LVN/FIB callout as a landscape "laser" card PNG.

Owned by agent LVNFIB. Same visual language as the CALL desk's card (2026-09-27 owner
request): near-black gloss rail with a blown-out light seam, laser hues keyed to
direction. The geometry here is this desk's own because the CONTENT differs, and the
differences are the whole point of this desk:

  * THE GATE IS THE HEADLINE. CHARTER.md s1 risks the account on exactly one rule -
    MGC arm A. Every other arm logs and resolves at ZERO risk. A card for an
    observe-only arm must not look like a tradeable order, so the gate badge is the
    largest thing after the symbol and an OBSERVE card is drawn in grey, not laser.
  * ONE TARGET, NOT THREE. Arm A's target is 1.5R and there is no scale-out. Drawing
    TP2/TP3 would invent levels the rule does not have.
  * SIZING IS SHOWN EVEN WHEN IT IS A REFUSAL. x0 is a result, not a blank.
  * THE PRIOR TRAVELS WITH ITS WIN RATE AND PAYOFF. A 70% win rate at 0.4 payoff loses
    money, so neither number is ever drawn alone, and the card says the prior is under
    its luck bar.
  * EVERY PRICE CARRIES ITS SOURCE BAR. The feed lags and the newest 1-2 bars revise for
    ~28 min, so the card stamps the bar and states it is not a live quote.

Usage:
    python3 card_png.py <callout_id> [...]      # one PNG per id
    python3 card_png.py --latest [N]            # the newest N callouts
    python3 card_png.py --armed                 # only arms that may risk the account
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


def backdrop(W, H, las, deep):
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
    return img


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


def gate(c: dict) -> tuple:
    """(badge, colour, armed?) - read from the callout's own notes and contracts.

    ARMED means this rule may risk the account AND the budget could size it. An arm the
    charter arms but the budget refuses is still not risking anything, and the card says
    REFUSED rather than ARMED so the two cannot be confused at a glance.
    """
    observe = any(str(n).startswith("OBSERVE_ONLY") for n in c.get("notes") or [])
    if observe or c.get("status") == "OBSERVE":
        return "OBSERVE ONLY · ZERO RISK", GREY, False
    if not c.get("contracts"):
        return "REFUSED · OVER BUDGET", RED, False
    return "ARMED · AT RISK", GREEN, True


def outcome(c: dict):
    """How this callout actually ended, from resolutions.jsonl. None while open."""
    for r in jsonl("resolutions.jsonl"):
        if r.get("id") == c["id"]:
            return r
    return None


def render(c: dict, out: pathlib.Path) -> pathlib.Path:
    side = c.get("side")
    armed_badge, badge_col, armed = gate(c)
    # An observe-only card is deliberately NOT drawn in laser: the colour itself tells the
    # reader whether the account is exposed, before any text is read.
    las = LASER[side] if armed else LASER[None]
    deep = DEEP[side] if armed else DEEP[None]

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

    # ---- header: symbol, arm, direction, gate badge
    d.text((x, M - sc(6)), c["symbol"], font=fsym, fill=WHITE)
    sw = d.textlength(c["symbol"], font=fsym)
    d.text((x + sw + sc(22), M + sc(10)), f"ARM {c['arm']}", font=fdir, fill=las)
    aw = d.textlength(f"ARM {c['arm']}", font=fdir)
    if side:
        d.text((x + sw + aw + sc(44), M + sc(10)), side, font=fdir, fill=las)

    bw = d.textlength(armed_badge, font=fbadge)
    bx0 = W - M - bw - sc(28)
    d.rectangle([bx0, M + sc(4), W - M, M + sc(52)], fill=(0, 0, 0, 150),
                outline=(*badge_col, 255), width=sc(3))
    d.text((bx0 + sc(14), M + sc(14)), armed_badge, font=fbadge, fill=badge_col)

    d.text((x, M + sc(96)), (c.get("rule") or "").upper()[:86], font=fkv, fill=(206, 214, 226))
    d.text((x, M + sc(126)), f"PAPER · $50,000 account · $2,800 drawdown floor",
           font=fmeta, fill=(130, 138, 150))

    # ---- price ladder, highest price at the top so it reads like a chart
    top = M + sc(176)
    rows = [("TARGET  1.5R", c.get("target"), GREEN),
            ("ENTRY   limit at level", c.get("limit_entry"), las),
            ("STOP    0.5xATR14 past", c.get("stop"), RED)]
    rows = [r for r in rows if isinstance(r[1], (int, float))]
    rows.sort(key=lambda r: -r[1])

    lw = sc(760)
    rh = sc(104)
    for i, (label, price, col) in enumerate(rows):
        box = (x, top + i * (rh + sc(14)), x + lw, top + i * (rh + sc(14)) + rh)
        panel(d, box, col, dim=not armed)
        d.text((box[0] + sc(20), box[1] + sc(12)), label.split("  ")[0], font=flab, fill=col)
        d.text((box[0] + sc(20), box[1] + sc(36)), f"{price:,.2f}", font=fnum, fill=WHITE)
        note = label.split("  ", 1)[1].strip() if "  " in label else ""
        if note:
            d.text((box[0] + sc(330), box[1] + sc(50)), note, font=fmeta, fill=(146, 154, 166))

    # ---- sizing / risk block
    sy = top + len(rows) * (rh + sc(14)) + sc(10)
    risk_usd, budget = c.get("risk_usd"), c.get("budget_usd")
    n = c.get("contracts", 0)
    size_col = GREEN if n else RED
    d.text((x, sy), "SIZE", font=fkl, fill=(140, 148, 160))
    d.text((x, sy + sc(20)),
           f"{n} contract{'' if n == 1 else 's'}"
           + (f"   risk ${risk_usd:,.2f} of ${budget:,.0f} budget" if isinstance(risk_usd, (int, float)) else ""),
           font=fkv, fill=size_col)
    if not n and isinstance(risk_usd, (int, float)) and isinstance(budget, (int, float)):
        d.text((x, sy + sc(48)),
               f"refused: ${risk_usd:,.2f} > ${budget:,.0f}. The stop is never shrunk to fit.",
               font=fmeta, fill=(176, 120, 128))

    # ---- right column: anchor, prior, outcome, notes
    rx = x + lw + sc(52)
    rw = W - M - rx
    ry = top

    def kv(label, value, col=WHITE, f=fkv, sub=None, subcol=(126, 134, 146)):
        """One labelled block. `sub` is drawn BELOW the value - an earlier version drew it
        at ry - 22 after ry had already advanced, so it landed on the next label."""
        nonlocal ry
        d.text((rx, ry), label, font=fkl, fill=(140, 148, 160))
        for ln in textwrap.wrap(str(value), 56) or [""]:
            ry += sc(22)
            d.text((rx, ry), ln, font=f, fill=col)
        if sub:
            for ln in textwrap.wrap(str(sub), 68):
                ry += sc(20)
                d.text((rx, ry), ln, font=fmeta, fill=subcol)
        ry += sc(34)

    a = c.get("anchor") or {}
    if a:
        kv("ANCHOR",
           f"{a.get('direction','?')} week  hi {a.get('hi')}  lo {a.get('lo')}"
           + (f"  frac {c['frac']}" if c.get("frac") is not None else ""),
           sub=f"from bar {a.get('source_bar','?')}")

    prior = c.get("measured_prior")
    if prior:
        kv("MEASURED PRIOR (out of sample)", prior, (214, 222, 234), fbody,
           sub="win rate and payoff travel together; under its luck bar - a forward "
               "test, not an edge claim", subcol=(176, 150, 110))

    res = outcome(c)
    if res:
        why = (res.get("why") or res.get("exit") or "?").upper()
        r = res.get("r")
        txt = f"{why}" + (f"   r={r:+.4f}" if isinstance(r, (int, float)) else "   no r (no fill)")
        txt += f"   {res.get('contracts', n)}x   pnl ${res.get('pnl', 0.0):,.2f}"
        kv("RESOLVED", txt, GREEN if (r or 0) > 0 else (GREY if r is None else RED), fbody,
           sub=("a non-fill is a correct outcome: the limit sits AT the level and is "
                "allowed to miss" if why == "NO_FILL" else None))
    else:
        kv("STATUS", f"{c.get('status','?')}   limit good for "
                     f"{c.get('limit_good_for_bars','?')} bars, cancelled at the close")

    for note in (c.get("notes") or [])[:3]:
        d.text((rx, ry), "·  " + str(note)[:62], font=fmeta, fill=(166, 150, 120))
        ry += sc(22)

    # ---- footer: the feed caveat, never omitted.
    # The callout's stored `feed_warning` is NOT echoed. It is a frozen field on an
    # append-only record, and older callouts carry "no live feed in this container" from
    # before yfinance was installed - true when written, false now. The card states what
    # is checkable at render time instead, so it never repeats a stale claim; the stored
    # field stays exactly as posted.
    try:
        import yfinance  # noqa: F401
        feed = "live feed on (yfinance); Yahoo lags and the newest 1-2 bars revise ~28 min"
    except ModuleNotFoundError:
        feed = "NO LIVE FEED (yfinance absent) - levels come from data/archive/"
    d.text((x, H - M - sc(44)), f"as of bar {c.get('as_of_bar','?')}"
           + (f"   close {c['as_of_close']:,.2f}" if isinstance(c.get("as_of_close"), (int, float)) else ""),
           font=fmeta, fill=(146, 154, 166))
    d.text((x, H - M - sc(22)), feed + "  ·  stamped level, NOT a live quote",
           font=fmeta, fill=(176, 150, 110))
    d.text((W - M - d.textlength(c["id"], font=fmeta), H - M - sc(22)), c["id"],
           font=fmeta, fill=(110, 118, 130))

    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(7)))
    Image.alpha_composite(img, ov).convert("RGB").save(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--latest", nargs="?", type=int, const=1)
    ap.add_argument("--armed", action="store_true")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--outdir", default=str(HERE / "cards"))
    a = ap.parse_args()
    global SCALE
    SCALE = a.scale

    calls = jsonl("callouts.jsonl")
    by_id = {c["id"]: c for c in calls}
    picked = [by_id[i] for i in a.ids if i in by_id]
    if a.armed:
        picked += [c for c in calls if gate(c)[2]]
    if a.latest:
        picked += calls[-a.latest:]
    if not picked:
        print("no callouts selected (use ids, --latest N or --armed)")
        return 1

    outdir = pathlib.Path(a.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    seen = set()
    for c in picked:
        if c["id"] in seen:
            continue
        seen.add(c["id"])
        p = render(c, outdir / f"card_{c['symbol']}_{c['arm']}_{c['id']}.png")
        w, h = Image.open(p).size
        print(f"{p.name}  {w}x{h}  ({p.stat().st_size // 1024} KB)  {gate(c)[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
