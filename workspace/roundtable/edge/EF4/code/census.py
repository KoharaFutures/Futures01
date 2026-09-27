"""EF4 / burst 03 - the firing-rate census for the six scalp cells.

MGC and MCL x 5m / 15m / 30m, single-timeframe frames, plus the 5+15+30 group.

Why this runs before any population is constructed. ``Strategy.evaluate`` is a strict
AND (base.py:670-684), so one condition that cannot fire kills the whole strategy and
produces a null indistinguishable from "we measured absence". The programme's shared
vocabulary calls a structurally-zero configuration VOID, and VOID is per (symbol,
timeframe) - never global. Six cells therefore need six censuses, not one.

Output per (cell, condition): fire count, long/short/neutral split, and a verdict of
VOID (0 fires), NEAR_VOID (<0.25% - a rate too low to build a 30-trade sample from on
this span), THIN (<2%), or LIVE.

The NEAR_VOID threshold is derived, not chosen: this span carries 41 sessions of
18:00->16:00, so a condition firing on fraction p of the cell's N bars can supply at
most p*N entries to a *single* strategy holding one position at a time. At 5m,
0.25% of 11,216 bars is 28 signals - below the 30-trade floor every prior study in
this repo used. So NEAR_VOID means "cannot reach a reportable sample here", which is a
statement about this cell and this span, and is not a claim about the condition.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))

from futures_agents.data.archive import BarArchive          # noqa: E402
from futures_agents.features import SymbolFrame              # noqa: E402
from futures_agents.strategies.library import CONDITIONS     # noqa: E402
from futures_agents.schema import Direction                  # noqa: E402

SYMBOLS = ("MGC", "MCL")
TFS = (5, 15, 30)
MIN_SAMPLE = 30          # the trade floor every prior study here used


def build(symbol: str, base_tf: int, tfs):
    arch = BarArchive(str(ROOT / "data" / "archive"))
    series = arch.load(symbol, base_tf)
    return SymbolFrame(series, tfs)


def census_one(symbol: str, base_tf: int, tfs, label: str):
    frame = build(symbol, base_tf, tfs)
    n = len(frame.base)
    primary = base_tf
    counts = {name: Counter() for name in CONDITIONS}
    snaps = 0
    for i in range(n):
        snap = frame.snapshot(i)
        if snap is None:
            continue
        snaps += 1
        cache = {}
        for name, cond in CONDITIONS.items():
            res = cond.evaluate(snap, primary, cache)
            c = counts[name]
            if res.triggered:
                c["fire"] += 1
                if res.direction is Direction.LONG:
                    c["long"] += 1
                elif res.direction is Direction.SHORT:
                    c["short"] += 1
                else:
                    c["neutral"] += 1
    rows = []
    for name, cond in CONDITIONS.items():
        c = counts[name]
        fire = c["fire"]
        rate = fire / snaps if snaps else 0.0
        if fire == 0:
            verdict = "VOID"
        elif fire < MIN_SAMPLE:
            verdict = "NEAR_VOID"
        elif rate < 0.02:
            verdict = "THIN"
        else:
            verdict = "LIVE"
        # A SIGNAL condition that never names a direction cannot drive an entry.
        directional = c["long"] + c["short"]
        rows.append({
            "cell": label, "symbol": symbol, "base_tf": base_tf,
            "frames": list(tfs), "condition": name, "group": cond.group,
            "kind": cond.kind.value, "snapshots": snaps,
            "fire": fire, "rate": round(rate, 6),
            "long": c["long"], "short": c["short"], "neutral": c["neutral"],
            "directional": directional,
            "verdict": verdict,
            "signal_without_direction": bool(cond.kind.value == "SIGNAL"
                                             and fire > 0 and directional == 0),
        })
    return rows, snaps


def main() -> None:
    all_rows = []
    cells = [(s, tf, (tf,), f"{s}-{tf}m") for s in SYMBOLS for tf in TFS]
    cells += [(s, 5, (5, 15, 30), f"{s}-5+15+30") for s in SYMBOLS]
    for sym, base_tf, tfs, label in cells:
        rows, snaps = census_one(sym, base_tf, tfs, label)
        all_rows.extend(rows)
        v = Counter(r["verdict"] for r in rows)
        print(f"{label:<16} snapshots={snaps:<6} "
              f"VOID={v['VOID']:<3} NEAR_VOID={v['NEAR_VOID']:<3} "
              f"THIN={v['THIN']:<3} LIVE={v['LIVE']:<3}")
        dead = sorted(r["condition"] for r in rows if r["verdict"] in ("VOID", "NEAR_VOID"))
        print(f"   not usable here ({len(dead)}): {', '.join(dead)}")
        nodir = sorted(r["condition"] for r in rows if r["signal_without_direction"])
        if nodir:
            print(f"   SIGNAL that fires but never names a direction: {', '.join(nodir)}")
        print()

    out = ROOT / "workspace/roundtable/edge/EF4/out/census.json"
    out.write_text(json.dumps(all_rows, indent=2))
    print(f"wrote {out}  ({len(all_rows)} rows)")


if __name__ == "__main__":
    main()
