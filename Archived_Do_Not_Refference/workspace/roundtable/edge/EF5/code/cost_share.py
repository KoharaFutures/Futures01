"""EF5 -- cost as a share of one R, measured for MES/MNQ at 5m/15m/30m.

The EDGE_BRIEF states cost is 15.0% of R at 5m against 4.6% at 60m. That figure
is not symbol-specific and my cell is two symbols with a 2x difference in
``point_value`` and a 2x difference in ``min_stop_ticks``, so it has to be
re-measured here. It is the number that decides the ranking: the mandate ranks on
expectancy in R **net of costs**, and at 5m the haircut may exceed anything the
signal contributes.

Method: for every bar, compute the stop distance each of the population's stop
geometries would place, then ``CostModel.cost_in_r(risk_points)``. Reported as
the distribution over bars, per (symbol, timeframe, stop geometry), because a
single median hides that the tight geometries are where the haircut lives.

No backtest. Pure arithmetic over the realised stop distances.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from ef5_data import PRIMARY_TFS, REPO, SYMBOLS, build_frame, in_session  # noqa: E402
from futures_agents.backtest.costs import CostModel                        # noqa: E402
from futures_agents.config import get_contract                             # noqa: E402
from futures_agents.schema import Direction                                # noqa: E402
from futures_agents.strategies.combinator import (ANCHORED_EXITS,          # noqa: E402
                                                  expand_exit_models)

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")

GEOMETRIES = list(expand_exit_models()) + list(ANCHORED_EXITS)


def main() -> None:
    res = {}
    for sym in SYMBOLS:
        spec = get_contract(sym)
        costs = CostModel(spec)
        for tf in PRIMARY_TFS:
            frame = build_frame(sym, tf)
            acc = defaultdict(list)
            for i in range(len(frame.base)):
                snap = frame.snapshot(i)
                if snap is None or not in_session(frame.base.bars[i].ts):
                    continue
                s = snap.tf(tf)
                if s is None:
                    continue
                entry = s.close
                ap = s.get("atr_percentile")
                for gi, ex in enumerate(GEOMETRIES):
                    stop = ex.stop_price(snap, tf, Direction.LONG, entry, spec)
                    if stop is None:
                        continue
                    risk = abs(entry - stop)
                    if risk <= 0:
                        continue
                    acc[(str(ex.stop_kind).split(".")[-1], ex.stop_mult, gi)].append(
                        costs.cost_in_r(risk, atr_percentile=ap,
                                        exit_is_stop=True, thin=False))
            rows = {}
            allv = []
            for k, v in sorted(acc.items()):
                v.sort()
                allv.extend(v)
                rows[f"{k[0]}x{k[1]}#{k[2]}"] = {
                    "n": len(v), "median": round(st.median(v), 4),
                    "p10": round(v[len(v) // 10], 4),
                    "p90": round(v[9 * len(v) // 10], 4),
                }
            allv.sort()
            res[f"{sym}_{tf}m"] = {
                "pooled_median_cost_r": round(st.median(allv), 4),
                "pooled_p10": round(allv[len(allv) // 10], 4),
                "pooled_p90": round(allv[9 * len(allv) // 10], 4),
                "by_geometry": rows,
            }
            print(f"{sym} {tf}m pooled cost/R  median={res[f'{sym}_{tf}m']['pooled_median_cost_r']:.4f} "
                  f"p10={res[f'{sym}_{tf}m']['pooled_p10']:.4f} "
                  f"p90={res[f'{sym}_{tf}m']['pooled_p90']:.4f}", flush=True)
    with open(os.path.join(OUT, "cost_share.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
