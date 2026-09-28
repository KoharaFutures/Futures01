#!/usr/bin/env python3
"""CONT-1: the pre-registered continuation entry, tested out of sample.

Owned by agent CALL. The rule is specified in NOTES.md N195 and was committed to git BEFORE
this file was written, so the parameters cannot have been fitted to the output. Nothing in
here may be retuned after reading a result; if CONT-1 fails its declared t > 3.0 threshold,
it is reported as failed.

WHY IT EXISTS. N194 Cause 1: `regime.py reversal()` requires a prior directional headline that
DIFFERS from the current one, so a trend that never changes direction cannot satisfy it. On
2026-09-28 MGC's 15m headline was BEARISH at every bar from 07:00 to 11:00 while the symbol fell
90.20 points, and the gate was unsatisfiable the whole way down. CONT-1 is the missing path: a
mechanism that is *capable* of returning YES during a continuation. Capable, not proven.

DATA IS OUT OF SAMPLE BY CONSTRUCTION. It reads `data/archive/` only, which ends 2026-09-25.
Today's bars live under `data/` and are never loaded here.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys
from datetime import datetime

HERE = pathlib.Path(__file__).resolve().parent
ARCHIVE = HERE.parents[2] / "data" / "archive"

# point value, tick size, RTH window (ET) — MGC's real RTH is 08:20-13:30 per CALLOUT.md §3
SPEC = {
    "MGC": {"pv": 10.0, "tick": 0.10, "open": "08:20", "close": "13:30"},
    "MNQ": {"pv": 2.0, "tick": 0.25, "open": "09:30", "close": "15:00"},
}
COMMISSION_RT = 1.50          # dollars per contract, round turn
EMA_N, ATR_N = 20, 14
DISP_ATR = 0.5                # displacement threshold, |close-EMA20| > 0.5*ATR
SLOPE_BARS = 5
PULLBACK_BARS = 3             # trigger at the extreme of the last 3 bars
ARM_BARS = 4                  # trigger valid for the next 4 bars
STOP_ATR = 1.0
TARGET_R = 1.5


def load(sym: str, frame: int) -> list[dict]:
    p = ARCHIVE / f"{sym}_{frame}m.jsonl"
    out = []
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        b = json.loads(line)
        if b.get("v", 0) == 0 and b["h"] == b["l"]:
            continue                       # vendor stub, same test fetch.py uses
        out.append(b)
    return out


def indicators(bars: list[dict]) -> tuple[list[float], list[float]]:
    closes = [b["c"] for b in bars]
    k = 2.0 / (EMA_N + 1.0)
    ema = [closes[0]]
    for c in closes[1:]:
        ema.append(c * k + ema[-1] * (1 - k))
    trs = [bars[0]["h"] - bars[0]["l"]]
    for i in range(1, len(bars)):
        pc = bars[i - 1]["c"]
        trs.append(max(bars[i]["h"] - bars[i]["l"],
                       abs(bars[i]["h"] - pc), abs(bars[i]["l"] - pc)))
    atr = [trs[0]]
    for t in trs[1:]:
        atr.append(atr[-1] + (t - atr[-1]) / ATR_N)
    return ema, atr


def in_session(ts: str, sym: str) -> bool:
    hm = ts[11:16]
    return SPEC[sym]["open"] <= hm < SPEC[sym]["close"]


def run(sym: str, frame: int) -> dict:
    bars = load(sym, frame)
    ema, atr = indicators(bars)
    pv, tick = SPEC[sym]["pv"], SPEC[sym]["tick"]
    trades: list[dict] = []
    i = max(EMA_N, ATR_N, SLOPE_BARS, PULLBACK_BARS) + 1
    while i < len(bars) - 1:
        a = atr[i]
        if a <= 0:
            i += 1
            continue
        disp = bars[i]["c"] - ema[i]
        if abs(disp) <= DISP_ATR * a:                       # 1. displacement
            i += 1
            continue
        side = "LONG" if disp > 0 else "SHORT"
        slope = ema[i] - ema[i - SLOPE_BARS]
        if (slope <= 0) if side == "LONG" else (slope >= 0):  # 2. slope agrees
            i += 1
            continue
        win = bars[i - PULLBACK_BARS + 1:i + 1]
        trig = (max(b["h"] for b in win) if side == "LONG"
                else min(b["l"] for b in win))
        # 3. stop entry armed for the next ARM_BARS bars
        filled = None
        for j in range(i + 1, min(i + 1 + ARM_BARS, len(bars))):
            bar = bars[j]
            hit = bar["h"] > trig if side == "LONG" else bar["l"] < trig
            if not hit:
                continue
            if not in_session(bar["ts"], sym):               # 6. session filter
                break
            raw = max(trig, bar["o"]) if side == "LONG" else min(trig, bar["o"])
            entry = raw + (tick if side == "LONG" else -tick)   # stop fills at trig or worse
            filled = (j, entry)
            break
        if filled is None:
            i += 1
            continue
        j, entry = filled
        risk = STOP_ATR * atr[i]                             # 4. stop 1.0 ATR
        stop = entry - risk if side == "LONG" else entry + risk
        tgt = entry + TARGET_R * risk if side == "LONG" else entry - TARGET_R * risk  # 5.
        out_r, exit_k = None, None
        for k in range(j, len(bars)):
            bar = bars[k]
            if side == "LONG":
                hit_s, hit_t = bar["l"] <= stop, bar["h"] >= tgt
            else:
                hit_s, hit_t = bar["h"] >= stop, bar["l"] <= tgt
            if hit_s and hit_t:
                out_r, exit_k = -1.0, k       # ambiguous bar -> loss, same as resolve.py
                break
            if hit_s:
                out_r, exit_k = -1.0, k
                break
            if hit_t:
                out_r, exit_k = TARGET_R, k
                break
        if out_r is None:                      # still open at the end of the series: discard
            break
        gross = out_r * risk * pv
        net = gross - COMMISSION_RT - tick * pv   # exit slippage one tick
        trades.append({"r": net / (risk * pv), "net": net, "side": side,
                       "in": bars[j]["ts"], "out": bars[exit_k]["ts"]})
        i = exit_k + 1                          # one position at a time
    return summarise(sym, frame, trades)


def summarise(sym: str, frame: int, trades: list[dict]) -> dict:
    n = len(trades)
    if n < 2:
        return {"symbol": sym, "frame": frame, "n": n, "t": float("nan")}
    rs = [t["r"] for t in trades]
    mean = sum(rs) / n
    var = sum((r - mean) ** 2 for r in rs) / (n - 1)
    sd = math.sqrt(var)
    t = mean / (sd / math.sqrt(n)) if sd > 0 else float("nan")
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    payoff = ((sum(wins) / len(wins)) / abs(sum(losses) / len(losses))
              if wins and losses else float("nan"))
    return {"symbol": sym, "frame": frame, "n": n, "expectancy_r": mean, "sd_r": sd, "t": t,
            "win_rate": len(wins) / n, "payoff": payoff,
            "net_dollars": sum(t_["net"] for t_ in trades),
            "longs": sum(1 for t_ in trades if t_["side"] == "LONG"),
            "shorts": sum(1 for t_ in trades if t_["side"] == "SHORT"),
            "first": trades[0]["in"][:10], "last": trades[-1]["in"][:10]}


def main() -> int:
    print("CONT-1 — pre-registered in NOTES.md N195 before this file existed")
    print(f"data: {ARCHIVE} (ends 2026-09-25; today's bars are NOT loaded)")
    print(f"costs: {COMMISSION_RT:.2f} RT commission + 1 tick entry + 1 tick exit slippage")
    print("declared threshold: t > 3.0 or CONT-1 is a FAILURE.  free_t programme-wide is 5.46\n")
    print(f"{'sym':<5}{'frame':>6}{'n':>6}{'E[R]':>9}{'sd':>8}{'t':>8}"
          f"{'win%':>7}{'payoff':>8}{'net $':>11}{'L/S':>9}")
    rows = []
    for sym in ("MGC", "MNQ"):
        for frame in (15, 60):
            r = run(sym, frame)
            rows.append(r)
            if r["n"] < 2:
                print(f"{sym:<5}{frame:>6}{r['n']:>6}   too few trades")
                continue
            print(f"{sym:<5}{frame:>6}{r['n']:>6}{r['expectancy_r']:>9.4f}{r['sd_r']:>8.3f}"
                  f"{r['t']:>8.3f}{100*r['win_rate']:>7.1f}{r['payoff']:>8.2f}"
                  f"{r['net_dollars']:>11.2f}{r['longs']:>5}/{r['shorts']:<4}")
    print()
    best = max((r for r in rows if r["n"] >= 2), key=lambda r: r["t"], default=None)
    if best:
        verdict = "CLEARS 3.0" if best["t"] > 3.0 else "FAILS the declared 3.0 threshold"
        print(f"largest t across the 4 pre-declared cells: {best['t']:.3f} "
              f"({best['symbol']} {best['frame']}m) — {verdict}")
        print(f"against free_t 5.46: {'clears' if best['t'] > 5.46 else 'does not clear'}")
    (HERE / "cont1_results.json").write_text(json.dumps(rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
