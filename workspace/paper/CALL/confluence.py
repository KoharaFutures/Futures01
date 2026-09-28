#!/usr/bin/env python3
"""Evaluate a setup against the 13 strategy families - to surface DISAGREEMENT, not to stack agreement.

Owned by agent CALL.

WHY THIS IS NOT A CONFLUENCE SCORE. `BRIEF.md` rule 1 measured that going from 2 signals
to 4 cuts trade count 35% and does not improve expectancy - **more confluence is a worse
trade**, not a safer one. Rule 2 measured that *requiring* multi-timeframe alignment was
detectably worse than requiring none (z = -4.09). So counting families that agree and
calling the total "confidence" would invert two of this programme's eight settled findings.

What a multi-family read IS good for is the opposite: **finding the families that
CONTRADICT the setup**, and naming the ones that were never tested on this symbol at all.
A setup that MEAN_REVERSION would fade is a setup with a named opponent, and that is worth
seeing. A family absent from a symbol's profile was never generated, never backtested and
appears in no ranking (`STRATEGY_CATALOGUE.md` §1) - so its silence is a hole in the
evidence, not a vote in favour.

Every verdict below is computed from the bars or marked N/A with a reason. Nothing is
asserted from memory, and a family this desk cannot evaluate from OHLCV says so rather
than quietly counting as agreement.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

_spec = importlib.util.spec_from_file_location("_rs", HERE / "resolve.py")
_rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rs)

AGREE, AGAINST, NA = "AGREE", "AGAINST", "N/A"


def ema(v, n):
    k = 2.0 / (n + 1.0)
    o = [v[0]]
    for x in v[1:]:
        o.append(x * k + o[-1] * (1 - k))
    return o


def rsi(closes, n=14):
    if len(closes) < n + 1:
        return 50.0
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(0.0, d))
        losses.append(max(0.0, -d))
    ag = sum(gains[-n:]) / n
    al = sum(losses[-n:]) / n
    return 100.0 if al == 0 else 100 - 100 / (1 + ag / al)


def atr(rows, n=14):
    trs = [max(rows[i]["h"] - rows[i]["l"], abs(rows[i]["h"] - rows[i - 1]["c"]),
               abs(rows[i]["l"] - rows[i - 1]["c"])) for i in range(1, len(rows))]
    return sum(trs[-n:]) / n if trs else 0.0


def stdev(v):
    m = sum(v) / len(v)
    return (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5


def evaluate(symbol: str, side: str, level: float, frame: int = 15, n: int = 40) -> list[dict]:
    """Return one row per family: verdict, the arithmetic behind it, and whether the
    family was ever generated for this symbol."""
    from futures_agents.strategies.profiles import SYMBOL_PROFILES

    prof = SYMBOL_PROFILES.get(symbol)
    tested = set(prof.groups) if prof is not None else set()
    bars = _rs.load_bars(symbol, frame)[-max(n, 60):]
    b5 = _rs.load_bars(symbol, 5)[-60:]
    c = [x["c"] for x in bars]
    e20, e50 = ema(c, 20), ema(c, 50)
    a = atr(bars)
    last, prev = bars[-1], bars[-2]
    short = side == "SHORT"
    sgn = -1 if short else 1
    vols = [x["v"] for x in bars if x["v"] > 0]
    medv = sorted(vols)[len(vols) // 2] if vols else 0.0
    r = rsi(c)
    win = c[-20:]
    sd = stdev(win)
    mid = sum(win) / len(win)
    rows = []

    def add(fam, verdict, why):
        rows.append({"family": fam, "verdict": verdict, "why": why,
                     "tested": fam in tested})

    # TREND - price against EMA20/50 and their slope
    below20, below50 = c[-1] < e20[-1], c[-1] < e50[-1]
    falling = e20[-1] < e20[-6]
    ok = (below20 and below50 and falling) if short else ((not below20) and (not below50) and not falling)
    add("TREND", AGREE if ok else AGAINST,
        f"close {c[-1]:.2f} vs EMA20 {e20[-1]:.2f} / EMA50 {e50[-1]:.2f}, "
        f"EMA20 {'falling' if falling else 'rising'}")

    # MOMENTUM - requires participation as well as direction
    relv = (last["v"] / medv) if medv else 0.0
    mom_dir = (r < 45) if short else (r > 55)
    add("MOMENTUM", AGREE if (mom_dir and relv >= 1.0) else AGAINST,
        f"RSI14 {r:.1f}, relative volume {relv:.2f}x median "
        f"({'participation present' if relv >= 1.0 else 'NO participation'})")

    # MEAN_REVERSION - the named opponent: it fades what a breakout buys
    z = (c[-1] - mid) / sd if sd else 0.0
    add("MEAN_REVERSION", AGAINST if (z < -1.0 if short else z > 1.0) else AGREE,
        f"{z:+.2f} sigma from the 20-bar mean - "
        f"{'extended, MEAN_REVERSION would FADE this' if abs(z) > 1.0 else 'not extended'}")

    # BREAKOUT - expansion through the level
    rng = last["h"] - last["l"]
    beyond = c[-1] < level if short else c[-1] > level
    add("BREAKOUT", AGREE if (beyond and rng > a * 0.6) else AGAINST,
        f"close {'below' if short else 'above'} {level:g}: {beyond}; "
        f"bar range {rng:.2f} vs ATR14 {a:.2f}")

    # LIQUIDITY - is the level a prior-session extreme being swept
    add("LIQUIDITY", AGREE if beyond else AGAINST,
        f"{level:g} is the prior session extreme; price is "
        f"{'through it' if beyond else 'not through it'}")

    # MULTI_TIMEFRAME - 5m against 15m. Rule 2: agreement here is NOT a virtue.
    c5 = [x["c"] for x in b5]
    e5 = ema(c5, 20)
    agree5 = (c5[-1] < e5[-1]) == short
    add("MULTI_TIMEFRAME", AGREE if agree5 else AGAINST,
        f"5m close {c5[-1]:.2f} vs its EMA20 {e5[-1]:.2f} - "
        f"{'same side as 15m' if agree5 else 'OPPOSES 15m'}; rule 2: alignment is not a virtue")

    for fam, why in (
        ("PULLBACK", "entry is a level break, not a retracement entry - different setup"),
        ("REVERSAL", "requires orderflow, which is a PROXY here: no delta or tick data"),
        ("VWAP", "session VWAP not computed by this desk; daily VWAP is D52-degenerate"),
        ("VOLUME_PROFILE", "no prior-session volume distribution built by this desk"),
        ("SUPPLY_DEMAND", "no zone model built by this desk"),
        ("FIBONACCI", "no confirmed leg measured by this desk"),
        ("OPENING_RANGE", "outside RTH, and D30/D31 make it unconstructable at 60m/240m"),
    ):
        add(fam, NA, why)
    return rows


def summary(rows):
    ag = [r for r in rows if r["verdict"] == AGREE]
    ag_ = [r for r in rows if r["verdict"] == AGAINST]
    na = [r for r in rows if r["verdict"] == NA]
    untested = [r["family"] for r in rows if r["verdict"] != NA and not r["tested"]]
    return {"agree": [r["family"] for r in ag], "against": [r["family"] for r in ag_],
            "na": [r["family"] for r in na], "untested_on_symbol": untested}


def main() -> int:
    plans = {json.loads(l)["call_id"]: json.loads(l)
             for l in (HERE / "pending.jsonl").read_text().splitlines() if l.strip()}
    for cid in (sys.argv[1:] or list(plans)):
        p = plans[cid]
        rows = evaluate(p["symbol"], p["side"], p["trigger_price"])
        s = summary(rows)
        print(f"\n=== {cid}  {p['symbol']} {p['side']}  trigger {p['trigger_price']} ===")
        for r in rows:
            if r["verdict"] == NA:
                continue
            flag = "" if r["tested"] else "   [NEVER TESTED ON THIS SYMBOL]"
            print(f"  {r['verdict']:8s} {r['family']:17s} {r['why']}{flag}")
        print(f"  N/A: {', '.join(s['na'])}")
        print(f"  -> agree {len(s['agree'])}, against {len(s['against'])}. "
              f"Agreement is NOT confidence (rule 1).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# ---------------------------------------------------------------- level context

def levels(symbol: str, frame: int = 15) -> list[tuple[str, float]]:
    """Structural levels this desk can actually point at, from bars it holds."""
    b15 = _rs.load_bars(symbol, frame)
    b60 = _rs.load_bars(symbol, 60)
    out: list[tuple[str, float]] = []
    if b60:
        out.append(("30-day high", max(x["h"] for x in b60)))
        out.append(("30-day low", min(x["l"] for x in b60)))
    # prior completed ET session
    from datetime import datetime
    byd: dict = {}
    for x in b15:
        byd.setdefault(datetime.fromisoformat(x["ts"]).date(), []).append(x)
    days = sorted(byd)
    if len(days) >= 2:
        prev = byd[days[-2]]
        out.append(("prior session high", max(x["h"] for x in prev)))
        out.append(("prior session low", min(x["l"] for x in prev)))
    # swing points in the recent window
    w = b15[-60:]
    for i in range(1, len(w) - 1):
        if w[i]["h"] > w[i - 1]["h"] and w[i]["h"] > w[i + 1]["h"]:
            out.append(("swing high", w[i]["h"]))
        if w[i]["l"] < w[i - 1]["l"] and w[i]["l"] < w[i + 1]["l"]:
            out.append(("swing low", w[i]["l"]))
    return out


def level_context(symbol: str, price: float, frame: int = 15) -> str:
    """Say whether a target sits on a level, or is pure arithmetic.

    The account owner asked why the TPs are where they are. The honest answer differs per
    target and must not be smoothed over: TP1 was PLACED on a level, TP2 and TP3 are R
    multiples that land wherever the arithmetic puts them. Claiming structure for all three
    would be inventing significance, which is the same failure as a confluence score.
    """
    bars = _rs.load_bars(symbol, frame)
    if not bars:
        return "no bars"
    a = atr(bars[-60:]) or 1.0
    near = [(abs(price - v), n, v) for n, v in levels(symbol, frame)]
    near.sort()
    if near and near[0][0] <= a * 0.5:
        d, n, v = near[0]
        return f"{n} {v:g}, {d:+.2f} away (within 0.5 ATR {a:.2f})"
    if near:
        d, n, v = near[0]
        return f"NO level within 0.5 ATR — nearest is {n} {v:g}, {d:.2f} away. Pure R multiple."
    return "no levels found"
