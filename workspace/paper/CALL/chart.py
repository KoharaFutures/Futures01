#!/usr/bin/env python3
"""ANSI candle chart and bias panel for the CALL desk, in the desk's own colours.

Owned by agent CALL. Renders from the snapshots under `data/`, stub-free.

COLOURS ARE NOT A CHOICE HERE. `CALLOUT.md` fixes them and forbids changing them:
BUY/LONG is 256-colour 27 (blue, white text), SELL/SHORT is 208 (orange, black text),
NO TRADE is 250 (grey). So **bullish renders BLUE and bearish renders ORANGE** - not
green and red. The brief moved NO_TRADE off orange and SIGNAL off bright blue precisely
so that nothing could be mistaken for a direction in peripheral vision, and a chart that
introduced a second colour language would undo that.

THE BIAS IS A DESCRIPTION, NOT A SIGNAL. Three mechanical components are computed and all
three are always shown with the tally, so a 2-1 reading can never be mistaken for a 3-0.
Nothing here is backtested and nothing here clears a threshold; the largest t-statistic
anywhere in this repository is 3.923 against a required 5.46. Where the components
disagree the headline says CONFLICTED, which under BRIEF.md rule 1 - two signals and one
filter is the ceiling, and more confluence measured WORSE - is a reason not to trade
rather than a weaker reason to trade.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "live"   # base layer: symlinks to data/archive (0000-archive); fetch deltas land beside them, gitignored

BLUE_BG, WHITE_FG = "\x1b[48;5;27m", "\x1b[38;5;231m"
ORANGE_BG, BLACK_FG = "\x1b[48;5;208m", "\x1b[38;5;16m"
GREY_BG = "\x1b[48;5;250m"
BLUE_FG, ORANGE_FG, GREY_FG, DIM = ("\x1b[38;5;27m", "\x1b[38;5;208m",
                                    "\x1b[38;5;250m", "\x1b[38;5;244m")
R = "\x1b[0m"


def load(symbol: str, minutes: int) -> list[dict]:
    merged: dict[str, dict] = {}
    for p in sorted(DATA.glob(f"{symbol}_{minutes}m_fetched_*.jsonl")):
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            b = json.loads(line)
            if b.get("v", 0) == 0 and b["h"] == b["l"]:
                continue                      # vendor stub, not a bar
            merged[b["ts"]] = b
    return [merged[k] for k in sorted(merged)]


def ema(vals: list[float], n: int) -> list[float]:
    k = 2.0 / (n + 1.0)
    out = [vals[0]]
    for v in vals[1:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def swings(bars: list[dict]) -> tuple[list[float], list[float]]:
    hi = [bars[i]["h"] for i in range(1, len(bars) - 1)
          if bars[i]["h"] > bars[i - 1]["h"] and bars[i]["h"] > bars[i + 1]["h"]]
    lo = [bars[i]["l"] for i in range(1, len(bars) - 1)
          if bars[i]["l"] < bars[i - 1]["l"] and bars[i]["l"] < bars[i + 1]["l"]]
    return hi, lo


def bias(bars: list[dict]) -> dict:
    """Three transparent components. All three are reported, always, with the tally."""
    closes = [b["c"] for b in bars]
    e = ema(closes, 20)
    comp = []

    # 1. trend: close against EMA20, and the EMA's own slope over 5 bars
    above = closes[-1] > e[-1]
    rising = e[-1] > e[-6] if len(e) > 6 else e[-1] > e[0]
    d = "BULL" if (above and rising) else ("BEAR" if (not above and not rising) else "MIXED")
    comp.append(("trend", d, f"close {closes[-1]:.2f} {'>' if above else '<'} EMA20 "
                             f"{e[-1]:.2f}, EMA20 {'rising' if rising else 'falling'}"))

    # 2. structure: the last two swing highs and the last two swing lows
    hi, lo = swings(bars)
    if len(hi) >= 2 and len(lo) >= 2:
        hh, hl = hi[-1] > hi[-2], lo[-1] > lo[-2]
        d = "BULL" if (hh and hl) else ("BEAR" if (not hh and not hl) else "MIXED")
        comp.append(("structure", d,
                     f"swing highs {hi[-2]:.2f}->{hi[-1]:.2f} "
                     f"({'higher' if hh else 'lower'}), lows {lo[-2]:.2f}->{lo[-1]:.2f} "
                     f"({'higher' if hl else 'lower'})"))
    else:
        comp.append(("structure", "MIXED", "too few swings to judge"))

    # 3. location: where price sits in the window's own range
    hh, ll = max(b["h"] for b in bars), min(b["l"] for b in bars)
    pos = 100.0 * (closes[-1] - ll) / (hh - ll) if hh > ll else 50.0
    d = "BULL" if pos > 60 else ("BEAR" if pos < 40 else "MIXED")
    comp.append(("location", d, f"{pos:.1f}% of the {len(bars)}-bar range "
                                f"[{ll:.2f}, {hh:.2f}]"))

    nb = sum(1 for c in comp if c[1] == "BULL")
    nr = sum(1 for c in comp if c[1] == "BEAR")
    if nb > nr:
        head, unanimous = "BULLISH", nb == 3
    elif nr > nb:
        head, unanimous = "BEARISH", nr == 3
    else:
        head, unanimous = "CONFLICTED", False
    return {"headline": head, "unanimous": unanimous, "bull": nb, "bear": nr,
            "components": comp, "pos": pos, "ema20": e[-1]}


def render(symbol: str, bars: list[dict], height: int = 14) -> str:
    hh, ll = max(b["h"] for b in bars), min(b["l"] for b in bars)
    span = (hh - ll) or 1.0
    row_of = lambda p: int(round((hh - p) / span * (height - 1)))
    cols = []
    for b in bars:
        up = b["c"] > b["o"]
        flat = b["c"] == b["o"]
        col = GREY_FG if flat else (BLUE_FG if up else ORANGE_FG)
        rh, rl = row_of(b["h"]), row_of(b["l"])
        rb, rt = row_of(min(b["o"], b["c"])), row_of(max(b["o"], b["c"]))
        cells = []
        for r in range(height):
            if rt <= r <= rb:
                cells.append(f"{col}█{R}")
            elif rh <= r <= rl:
                cells.append(f"{col}│{R}")
            else:
                cells.append(" ")
        cols.append(cells)

    bi = bias(bars)
    bg, fg = ((BLUE_BG, WHITE_FG) if bi["headline"] == "BULLISH"
              else (ORANGE_BG, BLACK_FG) if bi["headline"] == "BEARISH"
              else (GREY_BG, BLACK_FG))
    tally = f"{bi['bull']}-{bi['bear']}" + ("" if bi["unanimous"] else "  NOT UNANIMOUS")
    out = [f"{bg}{fg}  {symbol}  {bi['headline']}  ({tally})  {R}"]

    for r in range(height):
        price = hh - (r / (height - 1)) * span
        out.append(f"{DIM}{price:>10.2f}{R} " + "".join(c[r] for c in cols))
    out.append(f"{'':>10} " + f"{DIM}{'└' * len(bars)}{R}")
    out.append(f"{'':>11}{DIM}{bars[0]['ts'][5:16]}"
               f"{' ' * max(1, len(bars) - 22)}{bars[-1]['ts'][5:16]}{R}")
    out.append("")
    for name, d, why in bi["components"]:
        mark = (f"{BLUE_FG}BULL{R}" if d == "BULL"
                else f"{ORANGE_FG}BEAR{R}" if d == "BEAR" else f"{GREY_FG}MIXED{R}")
        out.append(f"   {name:<10} {mark:<22} {DIM}{why}{R}")
    if not bi["unanimous"]:
        out.append(f"   {GREY_FG}components disagree -> under rule 1 that is a reason NOT to "
                   f"trade, not a weaker reason to trade{R}")
    out.append(f"   {DIM}last {bars[-1]['ts']}  close {bars[-1]['c']:.2f}  "
               f"DESCRIPTION, NOT A SIGNAL - nothing here is backtested{R}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbols", nargs="+")
    ap.add_argument("--frame", type=int, default=15)
    ap.add_argument("--bars", type=int, default=44)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    for s in a.symbols:
        bars = load(s, a.frame)
        if len(bars) < 25:
            print(f"{s}: only {len(bars)} real bars at {a.frame}m - too few to chart")
            continue
        w = bars[-a.bars:]
        if a.json:
            print(json.dumps({s: bias(w)}, indent=2))
        else:
            print(render(f"{s} {a.frame}m", w))
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
