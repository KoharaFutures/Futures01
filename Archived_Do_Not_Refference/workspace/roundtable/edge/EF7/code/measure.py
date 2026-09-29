"""EF7-H4: what the session-window rule actually does, counted, on real bars.

Three arms over ``data/archive/`` 60m, all four symbols, same strategy list:

* **A — as shipped.** ``BacktestEngine(frame, costs)``. ``allow_overnight=False``,
  so ``exit_at_session_close`` flattens at the *contract's* RTH close: 13:30 MGC,
  14:30 MCL, 16:00 MES/MNQ. This is the regime all ~2.97M prior evaluations ran in.
* **B — overnight on, no window rule.** ``allow_overnight=True``. The naive way to
  "enable overnight": it *removes* the session exit rather than moving it, so
  positions run to stop, target, time stop or end of data. Kept as the control
  that the violation detector can fail on.
* **C — the rule.** ``SessionWindowEngine``. Arm B plus the 16:00 ET flat, the
  16:00–18:00 entry veto and the market-order flat fill.

Two strategy populations, because the answer differs between them and EF2's
measurement says it should:

* ``default`` — exactly what ``generate_strategies`` emits. ``rth_only`` defaults
  to ``True`` and the generators never vary it, so every entry is inside the
  contract's RTH, which sits wholly inside one 18:00→16:00 cycle.
* ``rth_off`` — the same strategies with ``rth_only=False``. This is the only way
  to reach an overnight *entry*, and D24 priced it: 2–4x the sample at a cost in
  expectancy. Built with ``dataclasses.replace(..., _id=None)`` and asserted
  unique, per D48.

The headline numbers this produces:

* ``flat_exits`` per symbol — positions the rule closes that had no other reason
  to close on that bar. This is the "how many positions does it actually close"
  number, and it is exact because the flat is checked *after* the whole shipped
  exit ladder.
* ``violations`` in arm C — must be 0.
* whether arm A and arm C produce identical trades on the ``default`` population —
  if they do, the rule is **inert** at the generated default and the programme
  needs to know that before anyone reports a profitability number.

Run: ``python3 workspace/roundtable/edge/EF7/code/measure.py [--max-total N]``
Writes ``workspace/roundtable/edge/EF7/measure.json``. No network, no API key.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time as _time
from collections import Counter
from dataclasses import replace
from typing import Dict, List, Sequence

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", "..", "..", ".."))
for p in (_ROOT, _HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from futures_agents.backtest.costs import CostModel
from futures_agents.backtest.engine import BacktestEngine, ExitReason
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.data.bars import BarSeries
from futures_agents.features import SymbolFrame
from futures_agents.strategies.combinator import generate_strategies
from futures_agents.timeutil import to_et

from ef7_window import (SESSION_WINDOW, SESSION_WINDOW_EXIT, SessionWindowEngine,
                    flat_flags, trade_violations)

SYMBOLS = ("MGC", "MCL", "MES", "MNQ")
TF = 60
SEED = 20260922


def population(symbol: str, max_total: int) -> Dict[str, List]:
    """The generated default, and the same strategies with ``rth_only`` off.

    D48: ``dataclasses.replace`` copies the memoised ``_id``, so without
    ``_id=None`` both populations collide onto the same ``strategy_id`` keys and
    the measured difference between them is exactly zero - indistinguishable from
    "the scope filter makes no difference". Asserted, not assumed.
    """
    base = generate_strategies(symbol, [TF], max_total=max_total, seed=SEED)
    ids = [s.strategy_id for s in base]              # forces memoisation
    assert len(set(ids)) == len(ids), f"{symbol}: duplicate ids in the base population"

    off = [replace(s, filters=replace(s.filters, rth_only=False), _id=None)
           for s in base]
    off_ids = [s.strategy_id for s in off]
    assert len(set(off_ids)) == len(off_ids), f"{symbol}: duplicate ids in rth_off"
    collisions = set(ids) & set(off_ids)
    assert not collisions, (
        f"{symbol}: {len(collisions)} arm-id collisions - D48 reproduced, "
        "the two populations would be measured as identical")
    return {"default": base, "rth_off": off}


def trade_rows(results) -> List:
    out = []
    for r in results.values():
        out.extend(r.trades)
    return out


def summarise(trades: Sequence) -> dict:
    reasons = Counter(t.exit_reason.value for t in trades)
    net = [t.net_r for t in trades]
    holds = [t.minutes_held for t in trades]
    return {
        "trades": len(trades),
        "exit_reasons": dict(sorted(reasons.items())),
        "sum_net_r": round(sum(net), 4),
        "mean_net_r": round(sum(net) / len(net), 5) if net else None,
        "median_minutes_held": round(sorted(holds)[len(holds) // 2], 1) if holds else None,
        "max_minutes_held": round(max(holds), 1) if holds else None,
        "violations": len(trade_violations(trades, base_minutes=TF)),
    }


def identical(a: Sequence, b: Sequence) -> bool:
    """Trade-for-trade equality, keyed on everything a fill can move."""
    key = lambda t: (t.strategy_id, to_et(t.entry_ts).isoformat(),
                     to_et(t.exit_ts).isoformat() if t.exit_ts else None,
                     t.exit_reason.value, round(t.entry_price, 10),
                     round(t.exit_price, 10), round(t.net_r, 10))
    return sorted(map(key, a)) == sorted(map(key, b))


def run_symbol(symbol: str, max_total: int) -> dict:
    arch = BarArchive(os.path.join(_ROOT, "data", "archive"))
    bars = arch.load(symbol, TF).bars
    spec = get_contract(symbol)
    frame = SymbolFrame(BarSeries(symbol, TF, bars), (TF,), spec)
    costs = CostModel(spec=spec)

    flags = flat_flags(bars)
    out: dict = {
        "symbol": symbol, "timeframe": TF, "store": "data/archive",
        "bars": len(bars),
        "first_bar": to_et(bars[0].ts).isoformat(),
        "last_bar": to_et(bars[-1].ts).isoformat(),
        "rth_open": spec.rth_open, "rth_close": spec.rth_close,
        "cycle_ends_in_series": sum(1 for f in flags if f is True),
        "bars_in_forbidden_window": sum(
            1 for b in bars if SESSION_WINDOW.is_forbidden(b.ts)),
        "populations": {},
    }

    pops = population(symbol, max_total)
    for pop_name, strategies in pops.items():
        t0 = _time.time()
        a = trade_rows(BacktestEngine(frame, costs).run_many(strategies))
        eng_b = BacktestEngine(frame, costs, allow_overnight=True)
        b = trade_rows(eng_b.run_many(strategies))
        eng_c = SessionWindowEngine(frame, costs)
        c = trade_rows(eng_c.run_many(strategies))

        flat = [t for t in c if t.exit_reason is SESSION_WINDOW_EXIT]
        # Of the positions the rule closed, how many were still open past the
        # contract's own RTH close - i.e. how many are hold-extensions rather
        # than trades arm A would have closed at the same bar anyway.
        out["populations"][pop_name] = {
            "strategies": len(strategies),
            "seconds": round(_time.time() - t0, 1),
            "A_shipped": summarise(a),
            "B_overnight_no_rule": summarise(b),
            "C_window_rule": summarise(c),
            "C_flat_exits": len(flat),
            "C_flat_share_of_trades": (round(len(flat) / len(c), 4) if c else None),
            "C_window_stats": eng_c.stats.to_dict(),
            "A_equals_C": identical(a, c),
            "B_equals_C": identical(b, c),
            "C_median_flat_minutes_held": (
                round(sorted(t.minutes_held for t in flat)[len(flat) // 2], 1)
                if flat else None),
            "C_entries_overnight": sum(
                1 for t in c if not _is_rth(t.entry_ts, spec)),
            "A_violations_detail": Counter(
                v["kind"] for v in trade_violations(a, base_minutes=TF)),
            "B_violations_detail": Counter(
                v["kind"] for v in trade_violations(b, base_minutes=TF)),
            "C_violations_detail": Counter(
                v["kind"] for v in trade_violations(c, base_minutes=TF)),
        }
        for k in ("A_violations_detail", "B_violations_detail", "C_violations_detail"):
            out["populations"][pop_name][k] = dict(out["populations"][pop_name][k])
    return out


def _is_rth(ts, spec) -> bool:
    from futures_agents.timeutil import is_rth
    return is_rth(ts, spec.rth_open, spec.rth_close)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-total", type=int, default=400)
    ap.add_argument("--symbols", default=",".join(SYMBOLS))
    ap.add_argument("--out", default=os.path.join(_HERE, "..", "measure.json"))
    args = ap.parse_args()

    payload = {"seed": SEED, "max_total": args.max_total, "symbols": {}}
    for sym in args.symbols.split(","):
        sym = sym.strip().upper()
        if not sym:
            continue
        print(f"--- {sym} ---", flush=True)
        payload["symbols"][sym] = run_symbol(sym, args.max_total)
        d = payload["symbols"][sym]["populations"]
        for name, p in d.items():
            print(f"  {name:8s} strat={p['strategies']:4d} "
                  f"A={p['A_shipped']['trades']:6d} "
                  f"B={p['B_overnight_no_rule']['trades']:6d} "
                  f"C={p['C_window_rule']['trades']:6d} "
                  f"flat={p['C_flat_exits']:6d} "
                  f"viol(C)={p['C_window_rule']['violations']} "
                  f"viol(B)={p['B_overnight_no_rule']['violations']} "
                  f"A==C={p['A_equals_C']}", flush=True)

    out = os.path.abspath(args.out)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
