"""EF7-H4b: separate the rule's TIMING effect from its COST effect, per symbol.

``measure.py`` answers "does the rule change the trades" (A == C?). On MES and MNQ
that answer is "yes" and it is misleading on its own, because their RTH close
already *is* 16:00 - so the shipped exit and the 16:00 flat can fire on the same
bar and the difference be entirely the flat's market-order slippage plus a handful
of vetoed degenerate entries. Reporting "not inert" without that split would
overstate what the rule does on the index complex, which is exactly the claim
EF2's measurement warns about.

So this script joins arm A to arm C on ``(strategy_id, entry_ts)`` and classifies
every trade:

* ``same_bar_same_price``  - identical; the rule did nothing to it.
* ``same_bar_diff_price``  - closed on the same bar, different fill. **Cost only.**
* ``later_exit``           - arm C held it longer. **Timing.** This is the effect
                             that requires the rule to exist.
* ``earlier_exit``         - arm C closed it sooner (a stop reached during the
                             extended hold can also do this; classified anyway).
* ``only_in_A`` / ``only_in_C`` - a trade one arm took and the other did not,
                             e.g. an entry the veto refused.

Run: ``python3 workspace/roundtable/edge/EF7/code/compare_ac.py``
Writes ``workspace/roundtable/edge/EF7/compare_ac.json``.
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
from futures_agents.backtest.engine import BacktestEngine
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.data.bars import BarSeries
from futures_agents.features import SymbolFrame
from futures_agents.strategies.combinator import generate_strategies
from futures_agents.timeutil import to_et

from ef7_window import SESSION_WINDOW_EXIT, SessionWindowEngine, trade_violations

SYMBOLS = ("MGC", "MCL", "MES", "MNQ")
TF = 60
SEED = 20260922


def classify(symbol: str, max_total: int) -> dict:
    arch = BarArchive(os.path.join(_ROOT, "data", "archive"))
    bars = arch.load(symbol, TF).bars
    spec = get_contract(symbol)
    frame = SymbolFrame(BarSeries(symbol, TF, bars), (TF,), spec)
    costs = CostModel(spec=spec)
    strategies = generate_strategies(symbol, [TF], max_total=max_total, seed=SEED)

    A = {}
    for r in BacktestEngine(frame, costs).run_many(strategies).values():
        for t in r.trades:
            A[(t.strategy_id, t.entry_index)] = t
    engC = SessionWindowEngine(frame, costs)
    C = {}
    for r in engC.run_many(strategies).values():
        for t in r.trades:
            C[(t.strategy_id, t.entry_index)] = t

    kinds = Counter()
    later_minutes = []
    cost_only_r_delta = []
    for k in set(A) | set(C):
        a, c = A.get(k), C.get(k)
        if a is None:
            kinds["only_in_C"] += 1
            continue
        if c is None:
            kinds["only_in_A"] += 1
            continue
        if c.exit_index > a.exit_index:
            kinds["later_exit"] += 1
            later_minutes.append((c.exit_index - a.exit_index) * TF)
        elif c.exit_index < a.exit_index:
            kinds["earlier_exit"] += 1
        elif abs(c.exit_price - a.exit_price) < 1e-12:
            kinds["same_bar_same_price"] += 1
        else:
            kinds["same_bar_diff_price"] += 1
            cost_only_r_delta.append(c.net_r - a.net_r)

    flat = [t for t in C.values() if t.exit_reason is SESSION_WINDOW_EXIT]
    # Of the flats, how many are held past the contract's own RTH close? That is
    # the hold-extension the rule unlocks, and EF2 predicts 0 for MES/MNQ.
    rth_close_min = (int(spec.rth_close[:2]) * 60 + int(spec.rth_close[3:]))
    past_rth = sum(1 for t in flat
                   if (to_et(t.exit_ts).hour * 60 + to_et(t.exit_ts).minute) + TF
                   > rth_close_min)
    return {
        "symbol": symbol, "strategies": len(strategies),
        "rth_close": spec.rth_close,
        "A_trades": len(A), "C_trades": len(C),
        "kinds": dict(sorted(kinds.items())),
        "C_flat_exits": len(flat),
        "C_flat_exits_past_contract_rth_close": past_rth,
        "later_exit_median_extra_minutes": (
            sorted(later_minutes)[len(later_minutes) // 2] if later_minutes else None),
        "later_exit_max_extra_minutes": max(later_minutes) if later_minutes else None,
        "cost_only_mean_net_r_delta": (
            round(sum(cost_only_r_delta) / len(cost_only_r_delta), 6)
            if cost_only_r_delta else None),
        "C_violations": len(trade_violations(list(C.values()), base_minutes=TF)),
        "C_window_stats": engC.stats.to_dict(),
    }


def main() -> int:
    max_total = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    out = {"max_total": max_total, "seed": SEED, "population": "generated default",
           "symbols": {}}
    for sym in SYMBOLS:
        row = classify(sym, max_total)
        out["symbols"][sym] = row
        print(f"{sym} (rth_close {row['rth_close']}): A={row['A_trades']} "
              f"C={row['C_trades']} flat={row['C_flat_exits']} "
              f"flat_past_rth_close={row['C_flat_exits_past_contract_rth_close']} "
              f"viol={row['C_violations']}", flush=True)
        print(f"    {row['kinds']}", flush=True)
        print(f"    later_exit median +{row['later_exit_median_extra_minutes']}min "
              f"max +{row['later_exit_max_extra_minutes']}min; "
              f"cost-only mean dR={row['cost_only_mean_net_r_delta']}", flush=True)
    p = os.path.join(_HERE, "..", "compare_ac.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print(f"wrote {os.path.abspath(p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
