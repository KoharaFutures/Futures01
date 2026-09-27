"""EF1 — the validation run. Three arms over real bars, on all four symbols.

What this measures, and why each number is here
-----------------------------------------------
``EF1-H1`` is the rule (``session_window.py``). This file is ``EF1-H2``, the
evidence that it works, which is the actual deliverable: a harness that has
never been shown to reject anything has not been tested.

Three arms, same strategies, same bars, same seed:

* **A — as shipped.** ``BacktestEngine(frame, costs)``. ``allow_overnight``
  defaults ``False``, so this is what all ~2.97M prior evaluations ran.
* **B — overnight on, no window rule.** ``allow_overnight=True``. The naive way
  to "turn on overnight", which per ``engine.py:470`` *removes* the session exit
  rather than moving it. Included because it is the arm a reader will assume EF1
  built, and because the difference between B and C is the rule.
* **C — the rule.** ``SessionWindowEngine``.

Reported per symbol:

1. ``violations`` in each arm. C must be **zero**. A and B are expected to be
   non-zero and are printed, because a validator that only ever reports zero has
   not demonstrated it can count.
2. ``flats`` in C — positions the rule closed. Every one of them is a position
   that had **not** hit its stop, its target or its time stop on that bar: the
   ON_BOUNDARY branch runs ``super()._manage`` first and only flattens when it
   returns nothing. So ``flats`` *is* the count of positions closed that would
   otherwise have run on, exactly, with no counterfactual needed.
3. The paired truncation, keyed on ``(strategy_id, entry_index)`` — the same
   position in arms B and C — giving the distribution of how many extra base
   bars B survived. This is the magnitude behind (2).
4. ``entries_vetoed`` in C.
5. Arm A's own violations, which test the EDGE_BRIEF's premise that every prior
   evaluation was flat by its contract's RTH close.

Determinism: one seed, one strategy list per symbol, sorted output. Rerunning
must produce a byte-identical JSON body.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

from futures_agents.backtest.costs import CostModel
from futures_agents.backtest.engine import (BacktestEngine, BacktestResult,
                                            ExitReason, Trade)
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.features import SymbolFrame
from futures_agents.strategies.base import Strategy
from futures_agents.strategies.combinator import generate_strategies
from futures_agents.timeutil import to_et

from session_window import (BarWindow, SessionWindowEngine, classify_series,
                            flat_exit_keys, is_session_flat,
                            prefix_invariance_report, violations)

SYMBOLS = ("MGC", "MCL", "MES", "MNQ")
ARCHIVE = BarArchive("data/archive")


def frame_for(symbol: str, base_tf: int, tfs: Sequence[int]) -> SymbolFrame:
    """A ``SymbolFrame`` over the append-only archive.

    The flat fires on **base** bars, so the base series decides the resolution
    of the deadline: a 60m base puts the flat at the close of the 15:00-16:00
    bar, which is the 16:00 print. A coarser base would put it at the close of
    whatever bucket happens to end at 16:00, which is why base is a parameter
    and not ``primary_tf``.
    """
    base = ARCHIVE.load(symbol, base_tf)
    if not len(base):
        raise SystemExit(f"data/archive has no {symbol}_{base_tf}m.jsonl")
    return SymbolFrame(base, tuple(sorted({base_tf, *tfs})))


def paired_truncation(arm_b: Dict[str, BacktestResult],
                      arm_c: Dict[str, BacktestResult]) -> dict:
    """How many extra base bars arm B survived, for positions both arms opened.

    Keyed on ``(strategy_id, entry_index)``: the same strategy entering at the
    same base bar is the same position. The arms diverge as soon as one of them
    closes early (an open position blocks new signals, ``engine.py:308``), so the
    paired set is a subset - its size is reported rather than assumed.
    """
    b_by: Dict[Tuple[str, int], Trade] = {}
    for res in arm_b.values():
        for t in res.trades:
            b_by[(t.strategy_id, t.entry_index)] = t
    deltas: List[int] = []
    same, paired = 0, 0
    reasons: Counter = Counter()
    for res in arm_c.values():
        for t in res.trades:
            if not is_session_flat(t):
                continue
            other = b_by.get((t.strategy_id, t.entry_index))
            if other is None:
                continue
            paired += 1
            d = other.exit_index - t.exit_index
            deltas.append(d)
            if d == 0:
                same += 1
            reasons[other.exit_reason.value] += 1
    return {
        "paired_flats": paired,
        "flats_where_arm_b_exited_on_the_same_bar": same,
        "extra_base_bars_arm_b_survived": {
            "min": min(deltas) if deltas else None,
            "median": statistics.median(deltas) if deltas else None,
            "mean": round(statistics.fmean(deltas), 3) if deltas else None,
            "max": max(deltas) if deltas else None,
        },
        "arm_b_exit_reason_for_those_positions": dict(sorted(reasons.items())),
    }


def r_summary(results: Dict[str, BacktestResult]) -> dict:
    rs = [t.net_r for res in results.values() for t in res.trades]
    return {"trades": len(rs),
            "mean_net_r": round(statistics.fmean(rs), 5) if rs else None,
            "sum_net_r": round(sum(rs), 3) if rs else None}


def measure_symbol(symbol: str, *, base_tf: int, tfs: Sequence[int],
                   max_total: int, seed: int) -> dict:
    spec = get_contract(symbol)
    frame = frame_for(symbol, base_tf, tfs)
    strategies = generate_strategies(symbol, tuple(tfs), max_total=max_total,
                                     seed=seed)
    ids = [s.strategy_id for s in strategies]
    assert len(set(ids)) == len(ids), f"{symbol}: duplicate strategy ids"

    costs = CostModel(spec)
    t0 = time.time()
    arm_a = BacktestEngine(frame, costs).run_many(strategies)
    arm_b = BacktestEngine(frame, costs, allow_overnight=True).run_many(strategies)
    eng_c = SessionWindowEngine(frame, costs)
    arm_c = eng_c.run_many(strategies)
    secs = time.time() - t0

    trades_a = [t for r in arm_a.values() for t in r.trades]
    trades_b = [t for r in arm_b.values() for t in r.trades]
    trades_c = [t for r in arm_c.values() for t in r.trades]

    v_a = violations(trades_a)
    v_b = violations(trades_b)
    v_c = violations(trades_c, flat_exits=flat_exit_keys(eng_c))
    v_c_strict = violations(trades_c)

    flats = [t for t in trades_c if is_session_flat(t)]
    holds_c = [t.minutes_held for t in trades_c]
    holds_a = [t.minutes_held for t in trades_a]

    return {
        "symbol": symbol,
        "substrate": f"data/archive {symbol}_{base_tf}m.jsonl",
        "base_tf": base_tf,
        "timeframes": list(tfs),
        "rth": f"{spec.rth_open}-{spec.rth_close}",
        "bars": len(frame.base),
        "span": [to_et(frame.base.bars[0].ts).isoformat(),
                 to_et(frame.base.bars[-1].ts).isoformat()],
        "strategies": len(strategies),
        "seconds": round(secs, 1),
        "grid": eng_c.counters.to_dict(),
        "arm_a_as_shipped": {
            **r_summary(arm_a), "violations": len(v_a),
            "violation_kinds": dict(sorted(Counter(v["kind"] for v in v_a).items())),
            "exit_reasons": dict(sorted(Counter(t.exit_reason.value
                                                for t in trades_a).items())),
            "median_minutes_held": statistics.median(holds_a) if holds_a else None,
        },
        "arm_b_overnight_no_rule": {
            **r_summary(arm_b), "violations": len(v_b),
            "violation_kinds": dict(sorted(Counter(v["kind"] for v in v_b).items())),
            "exit_reasons": dict(sorted(Counter(t.exit_reason.value
                                                for t in trades_b).items())),
        },
        "arm_c_session_window": {
            **r_summary(arm_c),
            "violations": len(v_c),
            "violations_strict_no_carveout": len(v_c_strict),
            "violation_kinds": dict(sorted(Counter(v["kind"] for v in v_c).items())),
            "violation_detail": v_c[:10],
            "exit_reasons": dict(sorted(Counter(t.exit_reason.value
                                                for t in trades_c).items())),
            "positions_closed_by_the_rule": len(flats),
            "share_of_trades_closed_by_the_rule":
                round(len(flats) / len(trades_c), 4) if trades_c else None,
            "median_minutes_held": statistics.median(holds_c) if holds_c else None,
            "max_minutes_held": max(holds_c) if holds_c else None,
        },
        "truncation_vs_arm_b": paired_truncation(arm_b, arm_c),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base-tf", type=int, default=60)
    ap.add_argument("--tfs", default="60,240")
    ap.add_argument("--max-total", type=int, default=400)
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--symbols", default=",".join(SYMBOLS))
    ap.add_argument("--out", default="workspace/developer/ef1_validation.json")
    args = ap.parse_args(argv)

    tfs = tuple(int(x) for x in args.tfs.split(","))
    out = {"generated_by": "EF1-H2 workspace/roundtable/edge/EF1/code/measure.py",
           "seed": args.seed, "max_total": args.max_total,
           "base_tf": args.base_tf, "timeframes": list(tfs), "symbols": []}
    for sym in args.symbols.split(","):
        row = measure_symbol(sym.strip(), base_tf=args.base_tf, tfs=tfs,
                             max_total=args.max_total, seed=args.seed)
        out["symbols"].append(row)
        c = row["arm_c_session_window"]
        print(f"{sym:4s} bars={row['bars']:6d} strat={row['strategies']:4d} "
              f"| A trades={row['arm_a_as_shipped']['trades']:6d} "
              f"viol={row['arm_a_as_shipped']['violations']:6d} "
              f"| B trades={row['arm_b_overnight_no_rule']['trades']:6d} "
              f"viol={row['arm_b_overnight_no_rule']['violations']:6d} "
              f"| C trades={c['trades']:6d} viol={c['violations']:3d} "
              f"flats={c['positions_closed_by_the_rule']:6d} "
              f"({0 if c['share_of_trades_closed_by_the_rule'] is None else c['share_of_trades_closed_by_the_rule']:.1%}) "
              f"vetoed={row['grid']['entries_vetoed_in_window']:5d} "
              f"[{row['seconds']}s]", flush=True)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2, sort_keys=False) + "\n")
    total_c = sum(r["arm_c_session_window"]["violations"] for r in out["symbols"])
    print(f"\nwrote {args.out}")
    print(f"TOTAL arm-C violations across all symbols: {total_c}  "
          f"({'PASS' if total_c == 0 else 'FAIL'})")
    return 0 if total_c == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
