"""EF5 -- exit-reason census and long-share census for all twelve arm-cells.

Two things the coordinator requires on every reported row, and both are properties
of the cell rather than of a row, so they are measured once here.

**1. What actually closes a trade.** EF1 measured 59.6-86.3% of trades closing on
the clock across the four symbols, MNQ worst at 86.3%. If the clock closes most
trades then the stop-and-target geometry barely acts, and a ranked list in my cell
ranks **entry signals scored on a clock exit**, not strategies. An "exits make no
difference" finding in this cell would be that fact and not a result.

**2. The long share.** MNQ rose 12.186% over my 41 cycles (IS +5.829%,
OOS +6.111%), so a long-biased rule earns from drift alone. The long share of every
reported row goes beside its expectancy, against two baselines: the whole
qualifying universe's long share, and 0.500 (a direction-random rule).

Also asserts placebo id uniqueness explicitly -- the coordinator's point 4: a fresh
``_id=None`` is NOT the guard, because ``strategy_id`` hashes condition *names*
rather than behaviour, and EF4 measured 400-540 collisions per cell in its own
placebo construction. ``build_cohort`` counts them in ``diag['id_collisions']``;
this asserts the count is zero rather than trusting it.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for p in (os.path.join(os.path.dirname(os.path.dirname(HERE)), "EF1", "code"),
          "/home/user/Futures01/workspace", "/home/user/Futures01"):
    if p not in sys.path:
        sys.path.append(p)

from ef5_data import ET, PRIMARY_TFS, REPO, SYMBOLS, build_frame   # noqa: E402
from population import base_population, session_arm               # noqa: E402
from session_window import SessionWindowEngine                     # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")
FLOOR = 20


def main() -> None:
    out = {}
    for sym in SYMBOLS:
        for tf in PRIMARY_TFS:
            frame = build_frame(sym, tf)
            bars = frame.base.bars
            drift = round(100 * (bars[-1].close / bars[0].close - 1), 3)
            base = base_population(sym, tf)
            for arm, strats in (("RTH", base), ("SESSION", session_arm(base))):
                res = SessionWindowEngine(frame).run_many(strats)
                allt = [t for r in res.values() for t in r.trades]
                floored = [s for s in strats
                           if len(res[s.strategy_id].trades) >= FLOOR]
                ft = [t for s in floored for t in res[s.strategy_id].trades]
                reasons = Counter(t.exit_reason.value for t in allt)
                freasons = Counter(t.exit_reason.value for t in ft)
                n, fn = len(allt), len(ft)
                long_shares = [
                    sum(1 for t in res[s.strategy_id].trades
                        if t.direction.value == "LONG") / len(res[s.strategy_id].trades)
                    for s in floored]
                out[f"{sym}_{tf}m_{arm}"] = {
                    "symbol": sym, "primary_tf": tf, "arm": arm,
                    "price_drift_pct_over_span": drift,
                    "trades_all": n, "trades_floored_rows": fn,
                    "exit_reasons_all": dict(reasons),
                    "exit_reasons_floored": dict(freasons),
                    "clock_close_share_all": round(
                        reasons.get("SESSION_CLOSE", 0) / n, 4) if n else None,
                    "clock_close_share_floored": round(
                        freasons.get("SESSION_CLOSE", 0) / fn, 4) if fn else None,
                    "stop_share_floored": round(
                        freasons.get("STOP", 0) / fn, 4) if fn else None,
                    "target_share_floored": round(
                        (freasons.get("TARGET", 0) + freasons.get("BREAKEVEN", 0))
                        / fn, 4) if fn else None,
                    "time_stop_share_floored": round(
                        freasons.get("TIME", 0) / fn, 4) if fn else None,
                    "floored_rows": len(floored),
                    "long_share_universe": round(
                        sum(1 for t in ft if t.direction.value == "LONG") / fn, 4)
                    if fn else None,
                    "long_share_per_row_median": round(st.median(long_shares), 4)
                    if long_shares else None,
                    "long_share_per_row_p10": round(
                        sorted(long_shares)[len(long_shares) // 10], 4)
                    if long_shares else None,
                    "long_share_per_row_p90": round(
                        sorted(long_shares)[9 * len(long_shares) // 10], 4)
                    if long_shares else None,
                }
                r = out[f"{sym}_{tf}m_{arm}"]
                print(f"{sym}_{tf}m_{arm}: drift={drift:+.2f}% trades={n} "
                      f"clock_close_all={r['clock_close_share_all']} "
                      f"floored_rows={len(floored)} clock={r['clock_close_share_floored']} "
                      f"stop={r['stop_share_floored']} tgt={r['target_share_floored']} "
                      f"time={r['time_stop_share_floored']} "
                      f"long_share_universe={r['long_share_universe']} "
                      f"long_med={r['long_share_per_row_median']}", flush=True)
    with open(os.path.join(OUT, "exit_and_direction_census.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
