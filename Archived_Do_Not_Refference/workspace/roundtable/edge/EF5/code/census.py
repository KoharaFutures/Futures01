"""EF5 burst 01/02 -- firing-rate census for the six SCALP cells.

MES/MNQ x 5m/15m/30m. For every one of the 79 conditions, at every timeframe
present in the cell's frame, count the bars on which it fires, under three
bar gates:

  ALL      every bar of the substrate
  SESSION  bars inside 18:00 ET -> 16:00 ET (the programme rule; excludes only
           16:00-18:00 ET). This is the gate a ``rth_only=False`` strategy sees.
  RTH      bars inside 09:30-16:00 ET. This is the gate a ``rth_only=True``
           strategy sees, and every strategy the combinator emits is
           ``rth_only=True``.

A verdict is per (symbol, timeframe, gate) and never global -- VOID at 5m may be
alive at 30m, and VOID under RTH may be alive under SESSION. That distinction is
the whole point of the census: ``Strategy.evaluate`` is a strict AND
(base.py:670-684) with no ``min_signals``, so ONE condition that cannot fire
under the gate the strategy actually runs under makes the whole strategy
structurally zero-trade.

No backtest anywhere in this file. No entries, no exits, no P&L.
"""
from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from ef5_data import (CELL_FRAMES, PRIMARY_TFS, SYMBOLS, REPO, build_frame,  # noqa: E402
                      in_session)

from futures_agents.strategies.base import ConditionKind               # noqa: E402
from futures_agents.strategies.library import CONDITIONS               # noqa: E402
from futures_agents.strategies.base import CONDITION_ERRORS            # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")


def census_cell(symbol: str, primary_tf: int) -> dict:
    frame = build_frame(symbol, primary_tf)
    tfs = sorted(frame.frames)
    # gate -> tf -> cond -> {fires, long, short, flat}
    tally = {g: {tf: defaultdict(lambda: [0, 0, 0, 0]) for tf in tfs}
             for g in ("ALL", "SESSION", "RTH")}
    gate_bars = {g: 0 for g in ("ALL", "SESSION", "RTH")}

    n = len(frame.base)
    for i in range(n):
        snap = frame.snapshot(i)
        if snap is None:
            continue
        ts = frame.base.bars[i].ts
        gates = ["ALL"]
        if in_session(ts):
            gates.append("SESSION")
        if snap.is_rth:
            gates.append("RTH")
        for g in gates:
            gate_bars[g] += 1
        cache = {}
        for name, cond in CONDITIONS.items():
            for tf in tfs:
                res = _eval_at(cond, snap, tf, cache)
                if not res.triggered:
                    continue
                d = res.direction.value
                slot = 1 if d == "LONG" else 2 if d == "SHORT" else 3
                for g in gates:
                    row = tally[g][tf][name]
                    row[0] += 1
                    row[slot] += 1

    out = {
        "symbol": symbol, "primary_tf": primary_tf, "frame_tfs": tfs,
        "base_bars": n, "gate_bars": gate_bars,
        "kinds": {k: ("SIGNAL" if c.kind is ConditionKind.SIGNAL else "FILTER")
                  for k, c in CONDITIONS.items()},
        "groups": {k: c.group for k, c in CONDITIONS.items()},
        "fires": {g: {str(tf): {k: v for k, v in sorted(tally[g][tf].items())}
                      for tf in tfs} for g in tally},
    }
    return out


def _eval_at(cond, snap, tf, cache):
    """Evaluate ``cond`` at timeframe ``tf``, memoised, exactly as
    ``Condition.evaluate`` does when the strategy's primary tf is ``tf``."""
    key = (cond.name, tf)
    hit = cache.get(key)
    if hit is not None:
        return hit
    res = cond.evaluate(snap, tf, None)
    cache[key] = res
    return res


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    all_out = {}
    for sym in SYMBOLS:
        for tf in PRIMARY_TFS:
            CONDITION_ERRORS.clear()
            c = census_cell(sym, tf)
            c["condition_errors"] = {f"{k[0]}:{k[1]}": v
                                     for k, v in CONDITION_ERRORS.items()}
            all_out[f"{sym}_{tf}m"] = c
            print(f"done {sym} {tf}m  bars={c['base_bars']} "
                  f"gates={c['gate_bars']} errors={len(c['condition_errors'])}",
                  flush=True)
    with open(os.path.join(OUT, "census.json"), "w") as fh:
        json.dump(all_out, fh)
    print("wrote", os.path.join(OUT, "census.json"))


if __name__ == "__main__":
    main()
