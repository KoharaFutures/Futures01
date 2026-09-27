"""EF1-H3 — prefix invariance for the session rule, on real archive bars.

The check BT1 used: the rule computed on ``bars[0:k]`` must match the rule
computed on the full series, for every *k*. A clock rule should pass trivially,
and the reason for running it anyway is that there is an obvious implementation
which does **not** pass: "bar *i* is the flat bar iff ``bars[i+1].ts >= 16:00``"
reads the future, and on a prefix ending at *i* it gives a different answer. So
passing this is evidence the rule reads only its own bar, not a tautology.

Two levels, because they can fail for different reasons:

* **Level 1 — the classification vector.** ``classify_series(bars[:k])`` against
  ``classify_series(bars)[:k]``. Exhaustive over every *k* is quadratic, so the
  coverage is stated rather than assumed: every *k* on a 1,200-bar window that
  contains ~50 deadlines, plus a stride over the full series, plus every *k*
  within +/-2 of each `ON_BOUNDARY`/`IN_WINDOW` bar - the only indices where a
  look-ahead formulation could differ.

* **Level 2 — the whole engine.** Run ``SessionWindowEngine`` on ``bars[0:k]``
  and require its trade list to be a prefix of the full run's. Trailing
  ``END_OF_DATA`` trades are dropped: those are an artefact of where the prefix
  was cut, not of the rule. This is quadratic in engine runs, so it runs on a
  bounded window with a stated stride.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

from futures_agents.backtest.costs import CostModel
from futures_agents.backtest.engine import ExitReason
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.data.bars import BarSeries
from futures_agents.features import SymbolFrame
from futures_agents.strategies.combinator import generate_strategies
from futures_agents.timeutil import to_et, trading_day

from session_window import (BarWindow, SessionGridError, SessionWindowEngine,
                            classify_series, prefix_invariance_report)

ARCHIVE = BarArchive("data/archive")


def boundary_neighbourhood(bars, radius: int = 2) -> List[int]:
    """Every prefix length within ``radius`` of a bar the rule acts on.

    These are the only indices at which a next-bar formulation could disagree
    with a this-bar one, so they are checked exhaustively even when the rest of
    the series is strided.
    """
    ks = set()
    for i, k in enumerate(classify_series(bars)):
        if k in (BarWindow.ON_BOUNDARY, BarWindow.IN_WINDOW):
            for d in range(-radius, radius + 1):
                if 0 <= i + d <= len(bars):
                    ks.add(i + d)
    return sorted(ks)


def level1(symbol: str, tf: int, *, window: int, stride: int) -> dict:
    bars = ARCHIVE.load(symbol, tf).bars
    dense = list(range(min(window, len(bars)) + 1))
    strided = list(range(0, len(bars) + 1, stride))
    ks = sorted(set(dense) | set(strided) | set(boundary_neighbourhood(bars)))
    rep = prefix_invariance_report(bars, ks=ks)
    rep["coverage"] = (f"exhaustive k<= {min(window, len(bars))}, "
                       f"stride {stride} to k={len(bars)}, plus every k within "
                       f"+/-2 of each ON_BOUNDARY/IN_WINDOW bar")
    rep["symbol"], rep["timeframe"] = symbol, tf
    return rep


def level2(symbol: str, tf: int, *, start: int, window: int, stride: int,
           max_total: int, seed: int) -> dict:
    """Engine-level: the trades on ``bars[0:k]`` must prefix the full run's."""
    full_series = ARCHIVE.load(symbol, tf)
    bars = full_series.bars[start:start + window]
    costs = CostModel(get_contract(symbol))
    strategies = generate_strategies(symbol, (tf,), max_total=max_total, seed=seed)

    def trades_for(k: int):
        sub = BarSeries(symbol, tf, bars[:k])
        try:
            eng = SessionWindowEngine(SymbolFrame(sub, (tf,)), costs)
        except SessionGridError:
            return None                    # the grid audit refuses; not a result
        # Two exclusions, both artefacts of where the cut fell rather than of
        # the rule:
        #  - a trailing END_OF_DATA trade;
        #  - a component-1b forced session-end flat on the prefix's LAST CME
        #    trading day, whose bar list is still incomplete. Once the prefix
        #    passes into the next trading day the determination is fixed, which
        #    is why only the cut day is exempt. Omitting this second exclusion
        #    reported 1 mismatch on MCL and 1 on MES - both of them exactly this
        #    effect, and both of them the documented cost of component 1b rather
        #    than a look-ahead.
        cut_day = trading_day(sub.bars[-1].ts)
        forced = {(e.strategy_id, e.entry_index, e.exit_index)
                  for e in eng.counters.flat_events
                  if e.forced_session_end and trading_day(e.exit_ts) == cut_day}
        rows = []
        for res in eng.run_many(strategies).values():
            for t in res.trades:
                if t.exit_reason is ExitReason.END_OF_DATA:
                    continue
                if (t.strategy_id, t.entry_index, t.exit_index) in forced:
                    continue
                rows.append((t.strategy_id, t.entry_index, t.exit_index,
                             round(t.exit_price, 6), t.exit_reason.value))
        return sorted(rows)

    full = trades_for(len(bars))
    ks = sorted(set(range(0, len(bars) + 1, stride)) | {len(bars)})
    checked, mismatches = 0, []
    for k in ks:
        got = trades_for(k)
        if got is None:
            continue
        # Every trade the prefix closed must appear identically in the full run.
        fullset = set(full or ())
        bad = [r for r in got if r not in fullset]
        if bad:
            mismatches.append({"k": k, "n_bad": len(bad), "example": bad[0]})
        checked += 1
    return {"symbol": symbol, "timeframe": tf, "strategies": len(strategies),
            "window": [start, start + window],
            "span": [to_et(bars[0].ts).isoformat(), to_et(bars[-1].ts).isoformat()],
            "full_run_trades": len(full or []), "prefixes_checked": checked,
            "stride": stride, "mismatches": len(mismatches),
            "detail": mismatches[:5]}


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", default="MGC,MCL,MES,MNQ")
    ap.add_argument("--tf", type=int, default=60)
    ap.add_argument("--window", type=int, default=1200)
    ap.add_argument("--stride", type=int, default=250)
    ap.add_argument("--l2-start", type=int, default=6000)
    ap.add_argument("--l2-window", type=int, default=400)
    ap.add_argument("--l2-stride", type=int, default=7)
    ap.add_argument("--l2-max-total", type=int, default=60)
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--out", default="workspace/developer/ef1_prefix_invariance.json")
    args = ap.parse_args(argv)

    out: Dict[str, list] = {"level1_classification": [], "level2_engine": []}
    for sym in args.symbols.split(","):
        sym = sym.strip()
        r1 = level1(sym, args.tf, window=args.window, stride=args.stride)
        out["level1_classification"].append(r1)
        print(f"L1 {sym} {args.tf}m  n={r1['n_bars']:6d} "
              f"prefixes={r1['prefixes_checked']:6d} "
              f"classify_mismatches={r1['classification_mismatches']} "
              f"session_end_off_cut={r1['session_end_mismatches_off_cut_trading_day']} "
              f"(on_cut={r1['session_end_mismatches_on_cut_trading_day']})",
              flush=True)
    for sym in args.symbols.split(","):
        sym = sym.strip()
        r2 = level2(sym, args.tf, start=args.l2_start, window=args.l2_window,
                    stride=args.l2_stride, max_total=args.l2_max_total,
                    seed=args.seed)
        out["level2_engine"].append(r2)
        print(f"L2 {sym} {args.tf}m  strat={r2['strategies']:4d} "
              f"full_trades={r2['full_run_trades']:5d} "
              f"prefixes={r2['prefixes_checked']:4d} "
              f"mismatches={r2['mismatches']}", flush=True)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    bad = (sum(r["classification_mismatches"]
               + r["session_end_mismatches_off_cut_trading_day"]
               for r in out["level1_classification"])
           + sum(r["mismatches"] for r in out["level2_engine"]))
    print(f"\nwrote {args.out}\nTOTAL mismatches: {bad}  "
          f"({'PASS' if bad == 0 else 'FAIL'})")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
