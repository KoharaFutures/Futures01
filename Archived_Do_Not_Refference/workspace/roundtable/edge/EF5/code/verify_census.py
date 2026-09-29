"""EF5 -- consistency checks between the condition census and the evaluator.

Three checks, each of which would catch a different way the census could be wrong:

1. **VOID carriers must be a SUBSET of zero-signal strategies.** If a strategy
   holds a condition the census says fires on 0 bars, and the evaluator
   nonetheless produces a signal for it, then either the census evaluated the
   condition at the wrong timeframe or ``Strategy.evaluate`` is not the strict
   AND it appears to be. Either way one of the two is wrong.
2. **A strategy whose every condition is non-VOID may still be zero-signal.**
   That is expected (conjunctions, direction agreement, filter gates) and the
   count of those is the part the condition-level census CANNOT see. Reported,
   not asserted.
3. **A hand-built positive control.** One strategy made of the single most
   frequently-firing SIGNAL plus no optional filters must produce many signals.
   If it does not, the harness is not evaluating anything and every null above
   is an artefact -- the ``_spans_sessions`` failure mode.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from ef5_data import REPO, build_frame, in_session               # noqa: E402
from population import base_population, session_arm              # noqa: E402
from eliminate import void_set                                   # noqa: E402
from futures_agents.schema import Direction                      # noqa: E402
from futures_agents.strategies.base import (ExitModel, StopKind,  # noqa: E402
                                            Strategy, StrategyFilters)
from futures_agents.strategies.library import get_condition       # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")


def check(symbol: str, primary_tf: int, arm: str, census: dict) -> dict:
    cell = f"{symbol}_{primary_tf}m"
    frame = build_frame(symbol, primary_tf)
    base = base_population(symbol, primary_tf)
    strats = base if arm == "RTH" else session_arm(base)
    voids = void_set(census, cell, arm)

    carriers, clean = [], []
    for s in strats:
        bad = any(c.name in voids.get(c.timeframe or s.primary_tf, ())
                  for c in s.conditions)
        (carriers if bad else clean).append(s)

    counts = {s.strategy_id: 0 for s in strats}
    for i in range(len(frame.base)):
        snap = frame.snapshot(i)
        if snap is None or not in_session(frame.base.bars[i].ts):
            continue
        cache = {}
        for s in strats:
            if s.evaluate(snap, cache) is not None:
                counts[s.strategy_id] += 1

    carrier_nonzero = [s.strategy_id for s in carriers if counts[s.strategy_id]]
    clean_zero = [s.strategy_id for s in clean if counts[s.strategy_id] == 0]

    # ---- check 3: positive control -----------------------------------
    # A single always-common SIGNAL, nothing else. Must fire abundantly.
    ctrl = Strategy(
        name="EF5_POSITIVE_CONTROL", symbol=symbol, group="TREND",
        primary_tf=primary_tf,
        conditions=(get_condition("price_above_ema50"),),
        exit=ExitModel(StopKind.ATR, 1.5, targets_r=(1.0,), scale_out=(1.0,)),
        filters=StrategyFilters(rth_only=(arm == "RTH")),
        allowed_directions=(Direction.LONG, Direction.SHORT))
    ctrl_n = 0
    for i in range(len(frame.base)):
        snap = frame.snapshot(i)
        if snap is None or not in_session(frame.base.bars[i].ts):
            continue
        if ctrl.evaluate(snap, {}) is not None:
            ctrl_n += 1

    return {
        "cell": cell, "arm": arm, "n": len(strats),
        "void_carriers": len(carriers),
        "CHECK1_carriers_with_signals": len(carrier_nonzero),
        "CHECK1_pass": len(carrier_nonzero) == 0,
        "clean_of_void": len(clean),
        "CHECK2_clean_but_zero_signal": len(clean_zero),
        "CHECK3_positive_control_signals": ctrl_n,
        "CHECK3_pass": ctrl_n > 100,
    }


def main() -> None:
    with open(os.path.join(OUT, "census.json")) as fh:
        census = json.load(fh)
    out = []
    for sym in ("MES", "MNQ"):
        for tf in (5, 15, 30):
            for arm in ("RTH", "SESSION"):
                r = check(sym, tf, arm, census)
                out.append(r)
                print(r, flush=True)
    with open(os.path.join(OUT, "verify_census.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    assert all(r["CHECK1_pass"] for r in out), "census/evaluator disagree"
    assert all(r["CHECK3_pass"] for r in out), "positive control did not fire"
    print("ALL CHECKS PASS")


if __name__ == "__main__":
    main()
