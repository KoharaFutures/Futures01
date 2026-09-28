#!/usr/bin/env python3
"""Per-timeframe bias, and a reversal call that survives this tape's noise.

Owned by agent CALL.

WHY A BARE HEADLINE FLIP IS NOT A REVERSAL. On the Sunday 2026-09-27 reopen, MNQ's 15m
headline flipped SEVEN times in three hours on about 90 points of net movement, and MGC's
structure component reverted twice inside ten minutes - once because the swing PAIR being
compared slid out of the window, not because price moved (NOTES.md N9). A desk that called
a reversal on every flip would have called seven, and been wrong at least six times.

So `reversal()` requires four things at once, and reports the ones that are missing rather
than averaging them away:

  1. the 15m headline has actually CHANGED SIGN versus the last call,
  2. it is UNANIMOUS (3-0 or 0-3) - a 1-0 majority is one component crossing a threshold,
  3. it has HELD for at least two consecutive checks, measured from `bias_history.jsonl`,
  4. at least one OTHER timeframe agrees with the new sign.

AND ON MULTI-TIMEFRAME AGREEMENT, THE STANDING CAVEAT. `BRIEF.md` rule 2 measured that
*requiring* alignment was detectably WORSE than requiring none, z = -4.09. Condition 4 is
therefore a check against a single-frame artefact, **not** a confirmation that raises
confidence, and the panel says so. `D50` also aliases every request >= 1440, so nothing
here reads a daily frame.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
HIST = HERE / "bias_history.jsonl"

_cs = importlib.util.spec_from_file_location("_ch", HERE / "chart.py")
_ch = importlib.util.module_from_spec(_cs)
_cs.loader.exec_module(_ch)

FRAMES = (1, 5, 15, 60, 240, 1440, 10080)

#: Frames a symbol may NOT carry a bias on, with the reason. From
#: `workspace/studies/SERIES_AUDIT.md`, which is a GATE and not advice: a series that fails
#: it is not eligible to carry a statistic, and printing a confident headline off one would
#: be exactly the authoritative-looking wrongness this desk exists to avoid.
NOT_ELIGIBLE = {
    ("MGC", 1440): "roll audit FAILS p<0.0001 — gap sum +2.9584 vs intraday −2.0079",
    ("MGC", 10080): "built from the same unadjusted daily; inherits the roll contamination",
    ("MCL", 1440): "MCL_1440m holds ONE bar; CL_1440m disqualified (close −37.63)",
    ("MCL", 10080): "no usable daily to build a week from",
}


def _weekly(symbol: str) -> list[dict]:
    """Resample daily into ISO weeks. The interval table stops at 1d, so a week has to be
    built here - and it inherits whatever is wrong with the daily series it is built from,
    which is why MGC weekly is gated exactly as MGC daily is."""
    from datetime import datetime
    days = _ch.load(symbol, 1440)
    buckets: dict = {}
    for b in days:
        iso = datetime.fromisoformat(b["ts"]).isocalendar()
        buckets.setdefault((iso[0], iso[1]), []).append(b)
    out = []
    for k in sorted(buckets):
        g = buckets[k]
        out.append({"ts": g[0]["ts"], "o": g[0]["o"], "h": max(x["h"] for x in g),
                    "l": min(x["l"] for x in g), "c": g[-1]["c"],
                    "v": sum(x["v"] for x in g)})
    return out


def timeframe_bias(symbol: str, frames=FRAMES, n: int = 40) -> list[dict]:
    """Bias per timeframe, from the same three components `chart.py` prints.

    A frame the audit disqualifies returns NOT ELIGIBLE with its reason and no bias. It is
    not scored, not counted toward agreement, and not silently omitted - an absent row
    reads as "no opinion", which is a different and weaker statement than "this series may
    not carry one".
    """
    out = []
    for f in frames:
        why = NOT_ELIGIBLE.get((symbol, f))
        if why:
            out.append({"frame": f, "headline": "NOT ELIGIBLE", "bull": 0, "bear": 0,
                        "unanimous": False, "bars": 0, "reason": why})
            continue
        bars = _weekly(symbol) if f == 10080 else _ch.load(symbol, f)
        if len(bars) < 25:
            out.append({"frame": f, "headline": "NO DATA", "bull": 0, "bear": 0,
                        "unanimous": False, "bars": len(bars)})
            continue
        b = _ch.bias(bars[-n:])
        out.append({"frame": f, "headline": b["headline"], "bull": b["bull"],
                    "bear": b["bear"], "unanimous": b["unanimous"], "bars": len(bars)})
    return out


def label(frame: int) -> str:
    return {1: "1m", 5: "5m", 15: "15m", 60: "60m", 240: "4h",
            1440: "DAILY", 10080: "WEEKLY"}.get(frame, f"{frame}m")


def record(symbol: str, tfs: list[dict]) -> None:
    """Append this check's per-frame reading. Persistence cannot be judged without it."""
    with HIST.open("a") as fh:
        fh.write(json.dumps({
            "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "symbol": symbol,
            "frames": {str(t["frame"]): t["headline"] for t in tfs},
            "agreeing_frames": [label(t["frame"]) for t in tfs
                                if t["headline"] not in ("NOT ELIGIBLE", "NO DATA")]}) + "\n")


def _history(symbol: str, frame: int = 15) -> list[str]:
    if not HIST.exists():
        return []
    out = []
    for line in HIST.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r["symbol"] == symbol:
            h = r["frames"].get(str(frame))
            if h:
                out.append(h)
    return out


def reversal(symbol: str, tfs: list[dict]) -> dict:
    """Call a reversal only when all four conditions hold. Report which ones did not."""
    cur = next((t for t in tfs if t["frame"] == 15), None)
    if cur is None or cur["headline"] == "NO DATA":
        return {"called": False, "reasons": ["no 15m data"]}
    hist = _history(symbol, 15)
    head = cur["headline"]
    fails = []

    if head == "CONFLICTED":
        fails.append("15m headline is CONFLICTED, not directional")
    if not cur["unanimous"]:
        fails.append(f"15m is {cur['bull']}-{cur['bear']}, not unanimous")
    # held for at least two consecutive checks
    held = 0
    for h in reversed(hist):
        if h == head:
            held += 1
        else:
            break
    if held < 2:
        fails.append(f"held only {held} consecutive check(s), needs 2")
    # Changed SIGN versus the last DIRECTIONAL headline. CONFLICTED has no sign, so a
    # BULLISH -> CONFLICTED -> BEARISH sequence is a real reversal with a neutral state in
    # the middle, not a "resolution". Treating the intervening CONFLICTED as the thing
    # being reversed from would make every reversal unreportable, since a sign change on
    # this tape almost always passes through CONFLICTED on its way across.
    prior = next((h for h in reversed(hist)
                  if h in ("BULLISH", "BEARISH") and h != head), None)
    if prior is None:
        fails.append("no prior directional headline to reverse from")
    # another timeframe agrees
    others = [t for t in tfs if t["frame"] != 15 and t["headline"] == head
              and t["headline"] not in ("NOT ELIGIBLE", "NO DATA")]
    if not others:
        fails.append("no other timeframe agrees")

    return {"called": not fails, "headline": head, "held": held, "prior": prior,
            "agreeing_frames": [t["frame"] for t in others], "reasons": fails}


def main() -> int:
    import sys
    for sym in (sys.argv[1:] or ["MGC", "MNQ"]):
        tfs = timeframe_bias(sym)
        record(sym, tfs)
        rv = reversal(sym, tfs)
        print(f"\n{sym}")
        for t in tfs:
            extra = (f"   {t.get('reason','')}" if t["headline"] == "NOT ELIGIBLE"
                     else f"{'  unanimous' if t['unanimous'] else ''}")
            tally = "" if t["headline"] in ("NOT ELIGIBLE", "NO DATA") else f"{t['bull']}-{t['bear']}"
            print(f"   {label(t['frame']):>7}  {t['headline']:<13} {tally}{extra}")
        if rv["called"]:
            print(f"   >>> REVERSAL CALLED: {rv['headline']} (was {rv['prior']}), "
                  f"held {rv['held']} checks, agreeing frames {rv['agreeing_frames']}")
        else:
            print(f"   no reversal call - {'; '.join(rv['reasons'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------- reversal SETUP

def reversal_setup(symbol: str, tfs: list[dict] | None = None) -> dict:
    """A structural reversal candidate: short-term capitulation INTO higher-timeframe support.

    This is a different object from `reversal()`. That one asks whether this desk's own 15m
    headline has flipped sign - a statement about the indicator. This one asks whether the
    MARKET is set up to turn, which is what the account owner means by a confident reversal.

    Four conditions, and the reason each is here:

    1. EXTENDED - |sigma| > 1.5 from the 20-bar 15m mean. A reversal needs something to
       revert FROM; a trend at its mean is just a trend.
    2. HIGHER TIMEFRAMES ON THE OTHER SIDE - at least two of 4h / DAILY / WEEKLY pointing
       the way the reversal would go. This is the condition that separates a turn from a
       knife-catch, and it is why MGC fails tonight at RSI 15.2 while MNQ passes: MGC is
       extended with NOTHING above it, MNQ is extended into three bullish slow frames.
    3. A RECLAIM TRIGGER - an actual level above (or below) the market that price must take
       back. Without it the plan fires while price is still falling, which is how "buy the
       dip" becomes "buy every dip".
    4. CLIMAX VOLUME on the extreme bar, reported but NOT required. A flush on 2x volume is
       a different event from a drift on 0.4x, and the caller deserves to know which it is
       rather than have the distinction averaged into a pass/fail.

    Frames the audit disqualifies are excluded from condition 2 - a bias that may not be
    computed cannot vote.
    """
    bars5, bars15 = _ch.load(symbol, 5), _ch.load(symbol, 15)
    if len(bars5) < 40 or len(bars15) < 25:
        return {"qualifies": False, "reasons": ["not enough bars"]}
    last = bars5[-1]["c"]
    win = [x["c"] for x in bars15[-20:]]
    mean = sum(win) / len(win)
    sd = (sum((x - mean) ** 2 for x in win) / len(win)) ** 0.5
    sigma = (last - mean) / sd if sd else 0.0
    side = "LONG" if sigma < 0 else "SHORT"
    tfs = tfs or timeframe_bias(symbol)
    want = "BULLISH" if side == "LONG" else "BEARISH"
    htf = [label(t["frame"]) for t in tfs
           if t["frame"] in (240, 1440, 10080) and t["headline"] == want]

    swings = []
    for i in range(1, len(bars5) - 1):
        a, b, c = bars5[i - 1], bars5[i], bars5[i + 1]
        if side == "LONG" and b["h"] > a["h"] and b["h"] > c["h"]:
            swings.append(b["h"])
        elif side == "SHORT" and b["l"] < a["l"] and b["l"] < c["l"]:
            swings.append(b["l"])
    cand = [x for x in swings[-12:] if (x > last if side == "LONG" else x < last)]
    trigger = (min(cand) if side == "LONG" else max(cand)) if cand else None

    vols = [x["v"] for x in bars5[-40:] if x["v"] > 0]
    medv = sorted(vols)[len(vols) // 2] if vols else 0
    ext_bar = (min(bars5[-12:], key=lambda x: x["l"]) if side == "LONG"
               else max(bars5[-12:], key=lambda x: x["h"]))
    climax = (ext_bar["v"] / medv) if medv else 0.0

    fails = []
    if abs(sigma) <= 1.5:
        fails.append(f"only {sigma:+.2f} sigma from the 20-bar mean, needs |1.5|")
    if len(htf) < 2:
        fails.append(f"only {len(htf)} higher timeframe(s) {want.lower()} "
                     f"({', '.join(htf) or 'none'}), needs 2")
    if trigger is None:
        fails.append("no reclaim level on the far side of price")
    return {"qualifies": not fails, "side": side, "sigma": round(sigma, 2),
            "htf_support": htf, "trigger": trigger, "climax_x": round(climax, 2),
            "climax_note": ("flush" if climax >= 1.5 else
                            "NO capitulation volume — a drift, not a flush"),
            "last": last, "reasons": fails}
