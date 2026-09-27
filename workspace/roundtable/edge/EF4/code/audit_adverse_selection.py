"""EF4 - adverse selection at the fill: is the next bar's open biased against the signal?

The engine's honest rule is that a signal computed on bar *i*'s close fills at bar *i+1*'s
open. The slippage model then charges 0.5 ticks (+1 thin) on top. What neither models is
whether the open itself is systematically *away* from the close in the direction the signal
wanted - which on a momentum-style trigger it should be, because the condition fires after
the move has begun.

If it is, the cost per trade is larger than the cost model says and the gap is not slippage:
it is the price of acting on a closed bar. Measured directly here, signed by the signal's
direction, so a positive number means the fill was *better* than the signal bar's close and a
negative number means worse.

Also measured: the raw contiguity of the series, because the engine's fill price is
``bar.open`` and if ``open[i+1] != close[i]`` by a material amount at every bar, that
discontinuity is inside every backtest in this repository whether or not anyone modelled it.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF1/code"))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF4/code"))

from futures_agents.backtest.costs import CostModel   # noqa: E402
from futures_agents.config import get_contract        # noqa: E402
from session_window import SessionWindowEngine        # noqa: E402
from population import build_track_a                  # noqa: E402
from run_cell import frame_for                        # noqa: E402

rows = []
for sym in ("MGC", "MCL"):
    spec = get_contract(sym)
    tick = spec.tick_size
    for tf in (5, 15, 30):
        frame = frame_for(sym, tf)
        bars = frame.base.bars
        disc = [abs(bars[i].open - bars[i - 1].close) / tick for i in range(1, len(bars))]
        eng = SessionWindowEngine(frame, CostModel(spec))
        res = eng.run_many(build_track_a(sym, tf))
        moves, moves_r = [], []
        for r in res.values():
            for t in r.trades:
                sc = bars[t.signal_index].close
                op = bars[t.entry_index].open
                sign = 1 if t.direction.sign > 0 else -1
                # favourable = the open moved the way the signal wanted
                fav_ticks = (op - sc) * sign / tick
                moves.append(fav_ticks)
                moves_r.append((op - sc) * sign / (t.risk_points or 1.0))
        rows.append({
            "symbol": sym, "tf": tf, "trades": len(moves),
            "median_bar_discontinuity_ticks": st.median(disc),
            "mean_bar_discontinuity_ticks": st.mean(disc),
            "mean_signal_to_fill_move_ticks": st.mean(moves) if moves else 0.0,
            "median_signal_to_fill_move_ticks": st.median(moves) if moves else 0.0,
            "mean_signal_to_fill_move_R": st.mean(moves_r) if moves_r else 0.0,
            "share_fills_adverse": (sum(1 for m in moves if m < 0) / len(moves)) if moves else 0.0,
            "modelled_entry_slippage_ticks_rth": 0.5,
            "modelled_entry_slippage_ticks_thin": 1.5,
        })
        r = rows[-1]
        print(f"{sym} {tf:>2}m  bar discontinuity median {r['median_bar_discontinuity_ticks']:.2f} "
              f"ticks / mean {r['mean_bar_discontinuity_ticks']:.2f}   "
              f"signal->fill move mean {r['mean_signal_to_fill_move_ticks']:+.3f} ticks "
              f"({r['mean_signal_to_fill_move_R']:+.4f} R), adverse on "
              f"{r['share_fills_adverse']:.1%} of {r['trades']} fills")

p = ROOT / "workspace/roundtable/edge/EF4/out/audit_adverse_selection.json"
p.write_text(json.dumps(rows, indent=2))
print(f"\nwrote {p}")
