"""EF7-H4: the realised-trade invariant, printed, on real bars, all four symbols.

Separate from ``measure.py`` on purpose. ``measure.py`` runs the *generated*
strategy population, which is what the closure count has to be about; this script
runs a **saturating** fixture - a signal that fires on every bar with a 200-tick
stop and a 20R target, so a position exists in essentially every admissible bar
of every cycle and only the flat can close it. That maximises the number of
chances the rule has to violate the specification, which is what an invariant
check wants. A selective strategy that happens to take 30 trades cannot
distinguish "zero violations" from "almost no exposure".

Run: ``python3 workspace/roundtable/edge/EF7/code/invariant.py``
Writes ``workspace/roundtable/edge/EF7/invariant.json``. No network, no API key.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "..", ".."))
for p in (_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from futures_agents.backtest.costs import CostModel
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.data.bars import BarSeries
from futures_agents.features import SymbolFrame
from futures_agents.schema import Direction
from futures_agents.strategies.base import (Condition, ConditionKind,
                                            ConditionResult, ExitModel, StopKind,
                                            Strategy, StrategyFilters, TargetKind)
from futures_agents.timeutil import to_et

from ef7_window import (SESSION_WINDOW, SESSION_WINDOW_EXIT, SessionWindowEngine,
                        flat_flags, trade_violations)

SYMBOLS = ("MGC", "MCL", "MES", "MNQ")
TF = 60


def saturating(symbol: str, direction: Direction) -> Strategy:
    cond = Condition(name="ef7_always", group="time", kind=ConditionKind.SIGNAL,
                     fn=lambda snap, tf: ConditionResult.yes(direction, detail="fixture"),
                     warmup_bars=0)
    return Strategy(
        name=f"EF7-saturating-{direction.value}", symbol=symbol, group="TREND",
        primary_tf=TF, conditions=(cond,),
        exit=ExitModel(stop_kind=StopKind.FIXED_TICKS, stop_mult=200.0,
                       target_kind=TargetKind.R_MULTIPLE, targets_r=(20.0,),
                       scale_out=(1.0,), breakeven_at_r=None, trail_atr_mult=None,
                       time_stop_bars=None, exit_at_session_close=True),
        filters=StrategyFilters(rth_only=False),
        allowed_directions=(direction,), _id=None)


def main() -> int:
    arch = BarArchive(os.path.join(_ROOT, "data", "archive"))
    payload = {"store": "data/archive", "timeframe": TF, "symbols": {}}
    total_viol = 0
    for sym in SYMBOLS:
        bars = arch.load(sym, TF).bars
        spec = get_contract(sym)
        frame = SymbolFrame(BarSeries(sym, TF, bars), (TF,), spec)
        flags = flat_flags(bars)
        row = {
            "bars": len(bars),
            "first": to_et(bars[0].ts).isoformat(),
            "last": to_et(bars[-1].ts).isoformat(),
            "rth": f"{spec.rth_open}-{spec.rth_close}",
            "cycle_ends": sum(1 for f in flags if f is True),
            "bars_in_forbidden_window": sum(
                1 for b in bars if SESSION_WINDOW.is_forbidden(b.ts)),
            "directions": {},
        }
        for d in (Direction.LONG, Direction.SHORT):
            eng = SessionWindowEngine(frame, CostModel(spec=spec))
            res = eng.run(saturating(sym, d))
            v = trade_violations(res.trades, base_minutes=TF)
            total_viol += len(v)
            row["directions"][d.value] = {
                "trades": len(res.trades),
                "exit_reasons": dict(sorted(Counter(
                    t.exit_reason.value for t in res.trades).items())),
                "violations": len(v),
                "violation_kinds": dict(Counter(x["kind"] for x in v)),
                "stats": eng.stats.to_dict(),
                "max_minutes_held": round(max(
                    (t.minutes_held for t in res.trades), default=0.0), 1),
            }
            print(f"{sym} {d.value:5s}: trades={len(res.trades):5d} "
                  f"flat={eng.stats.flat_exits:5d} "
                  f"vetoed={eng.stats.entries_vetoed:5d} "
                  f"early_flat={eng.stats.flat_before_deadline:3d} "
                  f"max_hold_min={row['directions'][d.value]['max_minutes_held']:7.1f} "
                  f"VIOLATIONS={len(v)}", flush=True)
        payload["symbols"][sym] = row
    payload["total_violations"] = total_viol
    out = os.path.join(_HERE, "..", "invariant.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    print(f"\nTOTAL VIOLATIONS ACROSS ALL SYMBOLS AND DIRECTIONS: {total_viol}")
    print(f"wrote {os.path.abspath(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
