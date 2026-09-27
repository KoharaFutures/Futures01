"""EF4 - the fill-model audit, and the three biases prefix invariance cannot see.

Prefix invariance catches a look-ahead in *time*. It cannot catch a look-ahead *inside a
bar*, because the bias is present in every prefix. That is exactly the failure the ORB/ICT
report recorded: a retest limit filling mid-bar at the bar's extreme, then crediting the same
bar's opposite extreme as a target hit, manufactured +0.354R at t = 5.19 and survived a 60/40
split and all three disjoint slices. So these are checked directly.

1. **Same-bar target credit.** Count trades whose target was credited on the ENTRY bar. The
   engine's stated rule is entry at the next bar's open, then the same bar's stop is checked
   first (engine.py:398-403). A large same-bar target share is the signature of the bug above.
2. **Stop-before-target on a tie.** Count trades where the entry bar's range contained both
   the stop and a target, and verify the stop won every time.
3. **Zero-slippage exits.** Count exits whose fill price equals the exact level (no adverse
   slippage applied). R3 found every TIME and session exit in this repo closes at
   ``bar.close`` with zero slippage by construction; EF1's harness fixes the session flat,
   so the residue is TIME and TARGET.
4. **Gap-through-stop accounting.** Count exits filled worse than the stop (honour_gaps) and
   the mean amount, so "the fill model is pessimistic" is a number rather than a claim.
5. **Roll discontinuity (D40 wearing a new instrument).** `yahoo.py` applies no roll handling
   of any kind, so a front-month series gaps at every roll and a momentum rule reads the gap
   as a return. Count bar-to-bar close gaps above 4 x the median absolute gap, and report
   where they fall in the clock: a cluster at 18:00 is a session boundary, a cluster mid-session
   is a roll or a vendor artefact.
"""
from __future__ import annotations

import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF1/code"))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF4/code"))

from futures_agents.backtest.costs import CostModel     # noqa: E402
from futures_agents.config import get_contract          # noqa: E402
from futures_agents.data.archive import BarArchive       # noqa: E402
from futures_agents.timeutil import to_et                # noqa: E402
from session_window import SessionWindowEngine           # noqa: E402
from population import build_track_a                     # noqa: E402
from run_cell import frame_for                           # noqa: E402

rows = []
for sym in ("MGC", "MCL"):
    spec = get_contract(sym)
    cost = CostModel(spec)
    # ---- roll / gap audit, on the raw series -------------------------------
    for tf in (5, 15, 30):
        bars = BarArchive(str(ROOT / "data/archive")).load(sym, tf).bars
        gaps = [abs(bars[i].open - bars[i - 1].close) for i in range(1, len(bars))]
        med = st.median(g for g in gaps if g > 0) if any(gaps) else 0.0
        big = [(to_et(bars[i + 1].ts), gaps[i]) for i in range(len(gaps))
               if med and gaps[i] > 4 * med]
        hours = Counter(t.hour for t, _ in big)
        rows.append({"kind": "gap_audit", "symbol": sym, "tf": tf,
                     "bars": len(bars), "median_abs_gap": med,
                     "gaps_over_4x_median": len(big),
                     "share": len(big) / max(1, len(gaps)),
                     "by_et_hour": dict(sorted(hours.items())),
                     "largest": sorted(((round(g, 4), t.isoformat())
                                        for t, g in big), reverse=True)[:5]})
        print(f"{sym} {tf}m  median|gap|={med:.4f}  gaps>4x = {len(big)} "
              f"({len(big)/max(1,len(gaps)):.3%})  by hour {dict(sorted(hours.items()))}")

    # ---- fill-model audit, on Track A trades -------------------------------
    for tf in (30, 15, 5):
        frame = frame_for(sym, tf)
        eng = SessionWindowEngine(frame, cost)
        res = eng.run_many(build_track_a(sym, tf))
        bars = frame.base.bars
        n = same_bar_target = tie_stop_won = tie_total = zero_slip = gap_worse = 0
        gap_amounts = []
        for r in res.values():
            for t in r.trades:
                n += 1
                if t.exit_index == t.entry_index and t.exit_reason.value == "TARGET":
                    same_bar_target += 1
                eb = bars[t.entry_index]
                sign = 1 if t.direction.sign > 0 else -1
                tgt = t.targets[0] if t.targets else None
                hit_stop = (eb.low <= t.initial_stop) if sign > 0 else (eb.high >= t.initial_stop)
                hit_tgt = tgt is not None and ((eb.high >= tgt) if sign > 0 else (eb.low <= tgt))
                if hit_stop and hit_tgt:
                    tie_total += 1
                    if t.exit_index == t.entry_index and t.exit_reason.value in ("STOP", "BREAKEVEN"):
                        tie_stop_won += 1
                if t.exit_reason.value in ("STOP", "BREAKEVEN"):
                    if abs(t.exit_price - t.initial_stop) < 1e-9:
                        zero_slip += 1
                    worse = (t.initial_stop - t.exit_price) * sign
                    if worse > 1e-9:
                        gap_worse += 1
                        gap_amounts.append(worse / (t.risk_points or 1.0))
        rows.append({"kind": "fill_audit", "symbol": sym, "tf": tf, "trades": n,
                     "same_bar_target_credit": same_bar_target,
                     "entry_bar_stop_and_target_both_touched": tie_total,
                     "of_which_stop_won": tie_stop_won,
                     "stop_exits_with_zero_slippage": zero_slip,
                     "stop_exits_filled_worse_than_stop": gap_worse,
                     "mean_adverse_fill_in_R": (st.mean(gap_amounts) if gap_amounts else 0.0)})
        print(f"{sym} {tf}m fills: trades={n} same-bar TARGET={same_bar_target} "
              f"ties={tie_total} (stop won {tie_stop_won}) "
              f"zero-slip stops={zero_slip} worse-than-stop={gap_worse} "
              f"mean adverse={(st.mean(gap_amounts) if gap_amounts else 0):.4f}R")

p = ROOT / "workspace/roundtable/edge/EF4/out/audit_fills.json"
p.write_text(json.dumps(rows, indent=2))
print(f"\nwrote {p}")
