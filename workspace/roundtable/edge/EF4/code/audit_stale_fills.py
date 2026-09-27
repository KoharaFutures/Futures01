"""EF4 - the weekend-gap stale fill, a hazard created by the session rule itself.

EF1's ``SessionWindowEngine`` vetoes an entry whose FILL bar is inside [16:00, 18:00) ET, and
its docstring is explicit that a signal *computed* on a 16:00-17:00 bar whose fill lands at
18:00 is legal under the rule as written (`veto_signals_in_window=False` by default). That is
the correct reading of the rule. It also opens a specific hole, and the substrate says how big:

`data/archive/` carries a full set of bars in ET hour 16 and essentially none in hour 17
`[measured: bar counts by hour]`. So the bar after MGC's 16:55 bar is **18:00 the same day on
a weekday and 18:00 SUNDAY after a Friday**. The largest bar-to-bar price discontinuities in
the whole substrate are exactly there: **+37.20 points on MGC at 2026-09-13T18:10**, 24.70 at
2026-08-02, 23.90 at 2026-08-30; on MCL 4.63, 3.06 and 1.86 at the same three reopens
`[measured: code/audit_fills.py]`. On a 47.5-tick MGC 5m stop, 37.2 points is **7.8 R** of gap.

So: a signal fired inside the prohibition window, filled at the next available open, can pick
up a whole weekend gap - in either direction - and the rule as written permits it. This
measures how often it happens and what it is worth, per cell, so the choice between
`veto_signals_in_window=False` and `True` is made on a number.
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
from futures_agents.timeutil import to_et             # noqa: E402
from session_window import SessionWindowEngine        # noqa: E402
from population import build_track_a, build_track_b   # noqa: E402
from run_cell import frame_for, metrics               # noqa: E402

OUT = ROOT / "workspace/roundtable/edge/EF4/out"
rows = []
for sym in ("MGC", "MCL"):
    spec = get_contract(sym)
    cost = CostModel(spec)
    for tf in (5, 15, 30):
        frame = frame_for(sym, tf)
        bars = frame.base.bars
        # a wide but bounded sample of the declared screen, plus all of Track A
        arms = build_track_a(sym, tf) + build_track_b(sym, tf)[:400]
        eng = SessionWindowEngine(frame, cost)
        res = eng.run_many(arms)
        n = stale = weekend = 0
        stale_r, weekend_r, normal_r = [], [], []
        for r in res.values():
            for t in r.trades:
                n += 1
                lag = (to_et(bars[t.entry_index].ts)
                       - to_et(bars[t.signal_index].ts)).total_seconds() / 60.0
                if lag > 2 * tf:
                    stale += 1
                    stale_r.append(t.net_r)
                    if lag > 24 * 60:
                        weekend += 1
                        weekend_r.append(t.net_r)
                else:
                    normal_r.append(t.net_r)
        row = {
            "symbol": sym, "tf": tf, "arms": len(arms), "trades": n,
            "stale_fills": stale, "stale_share": stale / n if n else 0.0,
            "weekend_gap_fills": weekend,
            "weekend_share": weekend / n if n else 0.0,
            "mean_net_r_stale": st.mean(stale_r) if stale_r else None,
            "mean_net_r_weekend": st.mean(weekend_r) if weekend_r else None,
            "mean_net_r_normal": st.mean(normal_r) if normal_r else None,
            "sd_net_r_weekend": (st.pstdev(weekend_r) if len(weekend_r) > 1 else None),
            "max_abs_net_r_weekend": (max(abs(x) for x in weekend_r) if weekend_r else None),
        }
        rows.append(row)
        print(f"{sym} {tf:>2}m  trades={n:<6} stale={stale} ({row['stale_share']:.2%}) "
              f"weekend-gap={weekend} ({row['weekend_share']:.3%})  "
              f"E(normal)={row['mean_net_r_normal']:+.4f} "
              f"E(stale)={(row['mean_net_r_stale'] if row['mean_net_r_stale'] is not None else 0):+.4f} "
              f"E(weekend)={(row['mean_net_r_weekend'] if row['mean_net_r_weekend'] is not None else 0):+.4f} "
              f"max|R|(weekend)={(row['max_abs_net_r_weekend'] or 0):.2f}")

p = OUT / "audit_stale_fills.json"
p.write_text(json.dumps(rows, indent=2))
print(f"\nwrote {p}")
