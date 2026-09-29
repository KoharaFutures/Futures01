"""EF7-H4c: the invariant at POPULATION scale, not probe scale.

EF3's lesson, relayed by the coordinator: a defect in the cycle-boundary rule can
be **0 on a 400-strategy probe and 198 on a population**. So the assertion has to
be run at population scale even though it is cheap, because the failure is
invisible below some sample size.

Note on coverage, because it cuts the other way too. ``invariant.py``'s saturating
fixture has a position open in essentially *every* admissible bar of *every* cycle,
so it cannot miss a cycle boundary by sampling - a rare boundary is not rare to it.
What it *can* miss is an interaction: scale-outs, breakeven moves, trailing stops
and anchored targets all touch ``_manage`` before the flat does. That is what a
real population tests and a single fixture does not, so the two are complements
rather than substitutes.

Arm C only. Arms A and B are known to violate and are measured in ``measure.py``.

Run: ``python3 workspace/roundtable/edge/EF7/code/population.py [max_total]``
Writes ``workspace/roundtable/edge/EF7/population.json``.
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import time as _time
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
from futures_agents.strategies.combinator import generate_strategies
from futures_agents.timeutil import to_et

from ef7_window import SESSION_WINDOW_EXIT, SessionWindowEngine, trade_violations

SYMBOLS = ("MES", "MNQ", "MGC", "MCL")
TF = 60
SEED = 20260922


def main() -> int:
    max_total = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    arch = BarArchive(os.path.join(_ROOT, "data", "archive"))
    out = {"max_total": max_total, "seed": SEED, "timeframe": TF,
           "store": "data/archive", "symbols": {}}
    grand_trades = grand_viol = 0
    for sym in SYMBOLS:
        bars = arch.load(sym, TF).bars
        spec = get_contract(sym)
        frame = SymbolFrame(BarSeries(sym, TF, bars), (TF,), spec)
        pop = generate_strategies(sym, [TF], max_total=max_total, seed=SEED)
        t0 = _time.time()
        eng = SessionWindowEngine(frame, CostModel(spec=spec))
        res = eng.run_many(pop)
        trades = [t for r in res.values() for t in r.trades]
        v = trade_violations(trades, base_minutes=TF)
        holds = sorted(t.minutes_held for t in trades)
        grand_trades += len(trades)
        grand_viol += len(v)
        row = {
            "strategies": len(pop), "trades": len(trades),
            "violations": len(v),
            "violation_kinds": dict(Counter(x["kind"] for x in v)),
            "first_violations": v[:5],
            "zero_trade_strategies": sum(1 for r in res.values() if not r.trades),
            "exit_reasons": dict(sorted(Counter(
                t.exit_reason.value for t in trades).items())),
            "flat_exits": sum(1 for t in trades
                              if t.exit_reason is SESSION_WINDOW_EXIT),
            "hold_min_med_max_minutes": [holds[0], statistics.median(holds), holds[-1]]
            if holds else None,
            "holds_over_22h": sum(1 for h in holds if h > 22 * 60),
            "window_stats": eng.stats.to_dict(),
            "seconds": round(_time.time() - t0, 1),
        }
        out["symbols"][sym] = row
        print(f"{sym}: strategies={row['strategies']:5d} trades={row['trades']:7d} "
              f"VIOLATIONS={row['violations']} flat={row['flat_exits']:7d} "
              f"maxhold={holds[-1] if holds else None}min over22h={row['holds_over_22h']} "
              f"zero_trade={row['zero_trade_strategies']:5d} {row['seconds']}s",
              flush=True)
        print(f"    exits {row['exit_reasons']}", flush=True)
        print(f"    stats {row['window_stats']}", flush=True)
    out["grand_total_trades"] = grand_trades
    out["grand_total_violations"] = grand_viol
    p = os.path.join(_HERE, "..", "population.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print(f"\nGRAND TOTAL: {grand_trades} trades, {grand_viol} violations")
    print(f"wrote {os.path.abspath(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
