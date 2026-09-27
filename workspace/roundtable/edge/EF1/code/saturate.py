"""EF1-H5 — the saturation test: hold a position on every bar the series has.

Why this is the strongest check available, and why it replaces arguing about
which strategy population to audit
-----------------------------------------------------------------------------
EF3 audited ``SessionWindowEngine`` with a 400-strategy ``rth_only=False``
population and found 43 ``SPANS_WINDOW`` violations that EF1's own
``rth_only=True`` run did not reach `[msgs/EF3-01_EF1_session-rule-misses-early-
close-sessions.md]`. EF3 was right, and the reason the two runs disagreed is the
reason a population audit is the wrong instrument: **a population only exercises
the sessions its signals happen to fire in.** Two agents with different
populations get different coverage of the same engine and cannot tell whose
engine is wrong.

A saturating stub removes the variable. It signals on **every** bar, with a stop
and a target placed so far away that they can never be hit, so a position is open
on every bar the series contains and the *only* thing that can ever close one is
the session rule. If the rule has a hole anywhere in 11,000 bars - an early
close, a full holiday, a vendor gap, a DST week, a Sunday reopen after a long
weekend - a perpetually open position walks straight into it. Zero violations
under saturation is a statement about the **series**, not about a sample of it.

It also gives the two numbers the brief asks for, exactly:

* every bar-to-bar transition in the series is covered, so the count of forced
  session-end flats is the count of sessions that shut before the deadline;
* ``max_minutes_held`` is the hard cap the rule actually delivers, which must
  not exceed one 18:00->16:00 cycle.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from futures_agents.backtest.costs import CostModel
from futures_agents.backtest.engine import BacktestEngine, ExitReason
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.features import SymbolFrame
from futures_agents.schema import Direction
from futures_agents.strategies.base import (ExitModel, StopKind,
                                            StrategySignal)
from futures_agents.timeutil import to_et

from session_window import (SessionWindowEngine, flat_exit_keys,
                            is_session_flat, violations)

ARCHIVE = BarArchive("data/archive")


def unreachable_exit() -> ExitModel:
    """An exit model whose stop and target can never be hit.

    Every management feature is off and the target sits 500R away, so the only
    thing that can close a position is the session rule. If a stop or a target
    fires, the fixture is wrong and the run says so.
    """
    return ExitModel(stop_kind=StopKind.FIXED_TICKS, stop_mult=1.0,
                     targets_r=(500.0,), scale_out=(1.0,), breakeven_at_r=None,
                     trail_atr_mult=None, time_stop_bars=None,
                     exit_at_session_close=False)


@dataclass
class Saturating:
    """Signals on every bar, long, with levels derived from the bar itself."""

    symbol: str
    primary_tf: int
    direction: Direction = Direction.LONG
    strategy_id: str = "ef1-saturate"
    name: str = "EF1 saturating stub"
    group: str = "EF1"
    exit: ExitModel = field(default_factory=unreachable_exit)

    def evaluate(self, snap, cache: Optional[dict] = None):
        px = snap.price
        sign = self.direction.sign
        # A stop 50% away and a target 500R beyond it: unreachable in both
        # directions on any real bar, so only the clock can close the trade.
        stop = px * (1.0 - 0.5 * sign)
        return StrategySignal(
            strategy_id=self.strategy_id, strategy_name=self.name,
            group=self.group, symbol=self.symbol, ts=snap.ts,
            bar_index=snap.base_index, direction=self.direction,
            entry=px, stop=stop, targets=[px + sign * abs(px - stop) * 500.0],
            primary_tf=self.primary_tf, timeframes=[self.primary_tf],
            regime=snap.regime.regime, volatility=snap.regime.volatility,
            session=snap.session, time_bucket=snap.time_bucket,
            day_of_week=snap.day_of_week)


def saturate(symbol: str, tf: int, *, direction: Direction) -> dict:
    base = ARCHIVE.load(symbol, tf)
    if not len(base):
        raise SystemExit(f"no data/archive/{symbol}_{tf}m.jsonl")
    frame = SymbolFrame(base, (tf,))
    costs = CostModel(get_contract(symbol))
    stub = Saturating(symbol=symbol, primary_tf=tf, direction=direction)

    eng = SessionWindowEngine(frame, costs)
    res = eng.run(stub)
    tr = res.trades
    v = violations(tr, flat_exits=flat_exit_keys(eng))
    v_strict = violations(tr)
    holds = [t.minutes_held for t in tr]
    reasons = Counter(t.exit_reason.value for t in tr)

    # The control: the same saturating stub through the shipped engine. If this
    # also came back clean the test would prove nothing about the rule.
    ctrl = BacktestEngine(frame, costs).run(stub)
    ctrl_v = violations(ctrl.trades)

    #: One 18:00->16:00 cycle is 22 hours = 1320 minutes, and that is the cap.
    #:
    #: A first cut used ``22*60 - tf``, reasoning that trade stamps are bar OPEN
    #: times so the exit stamp is the ON_BOUNDARY bar's open, 16:00 minus one
    #: bar. That is right for an ON_BOUNDARY flat and **wrong for the IN_WINDOW
    #: gap flat**, whose exit stamp is 16:00 itself. It reported MNQ 240m's
    #: legitimate 20:00 -> 16:00 hold of 1200 minutes as over-cap. The assertion
    #: was too tight, not the rule - recorded because an over-tight check in a
    #: gate is as misleading as a loose one, and this one would have had me
    #: withdraw a cell that was fine.
    cap = 22 * 60
    over = [t for t in tr if t.minutes_held > cap]

    return {
        "symbol": symbol, "timeframe": tf, "direction": direction.value,
        "bars": len(base),
        "span": [to_et(base.bars[0].ts).isoformat(),
                 to_et(base.bars[-1].ts).isoformat()],
        "trades": len(tr),
        "violations": len(v),
        "violations_strict_no_carveout": len(v_strict),
        "violation_detail": v[:10],
        "exit_reasons": dict(sorted(reasons.items())),
        "closed_by_the_rule": sum(1 for t in tr if is_session_flat(t)),
        "counters": eng.counters.to_dict(),
        "hold_minutes": {
            "median": statistics.median(holds) if holds else None,
            "max": max(holds) if holds else None,
            "cap_22h": cap,
            "trades_over_cap": len(over),
            "over_cap_detail": [
                {"entry": to_et(t.entry_ts).isoformat(),
                 "exit": to_et(t.exit_ts).isoformat(),
                 "minutes": t.minutes_held} for t in over[:10]],
        },
        "control_shipped_engine": {
            "trades": len(ctrl.trades), "violations": len(ctrl_v),
            "violation_kinds": dict(sorted(Counter(x["kind"]
                                                   for x in ctrl_v).items())),
            "max_hold_minutes": max((t.minutes_held for t in ctrl.trades),
                                    default=None),
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", default="MGC,MCL,MES,MNQ")
    ap.add_argument("--tfs", default="5,15,30,60,240")
    ap.add_argument("--out", default="workspace/developer/ef1_saturation.json")
    args = ap.parse_args(argv)

    rows: List[dict] = []
    for sym in args.symbols.split(","):
        for tf in (int(x) for x in args.tfs.split(",")):
            for d in (Direction.LONG, Direction.SHORT):
                r = saturate(sym.strip(), tf, direction=d)
                rows.append(r)
                h = r["hold_minutes"]
                print(f"{sym:4s} {tf:4d}m {d.value:5s} bars={r['bars']:6d} "
                      f"trades={r['trades']:5d} viol={r['violations']:3d} "
                      f"(strict {r['violations_strict_no_carveout']:3d}) "
                      f"rule={r['closed_by_the_rule']:5d} "
                      f"1b={r['counters']['flats_forced_session_end']:3d} "
                      f"gap={r['counters']['flats_in_window']:3d} "
                      f"maxhold={h['max']:6.0f}m/cap{h['cap_22h']} "
                      f"over={h['trades_over_cap']:3d} "
                      f"| control viol={r['control_shipped_engine']['violations']:5d} "
                      f"maxhold={r['control_shipped_engine']['max_hold_minutes']:.0f}m",
                      flush=True)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(rows, indent=2) + "\n")
    bad = sum(r["violations"] for r in rows)
    over = sum(r["hold_minutes"]["trades_over_cap"] for r in rows)
    ctrl = sum(r["control_shipped_engine"]["violations"] for r in rows)
    print(f"\nwrote {args.out}")
    print(f"TOTAL violations under saturation: {bad}   over-cap holds: {over}")
    print(f"control (shipped engine) violations: {ctrl} - non-zero means the "
          f"test has power")
    return 0 if (bad == 0 and over == 0 and ctrl > 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
