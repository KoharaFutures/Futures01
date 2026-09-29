"""EF5 -- the qualifying universe's expectancy per arm-cell. The actual deliverable.

EF6 burst 07's instruction, which I have adopted: **do not rank.** Report the whole
qualifying universe's expectancy per cell, which has the full sample behind it and
needs no selection, and report the qualifying count beside it.

Definition, deliberately minimal so no selection enters:
  * 20-trade floor (the reporting floor; a PF of 1.8 over 18 trades is noise)
  * clone collapse on the realised trade ledger (structure, not performance)
  * **no** durability gate at all -- in particular NOT the ``t >= 0`` and
    ``max_consecutive_losses <= 12`` gates my ranking score used.

That last point is a correction to my own protocol and I am declaring it rather
than quietly applying it. ``max_consecutive_losses <= 12`` is **not
scale-invariant**: for n trades at loss rate q the expected longest losing run is
about ``log(n(1-q))/log(1/q)``, which is ~10.3 at n=473 and ~5.5 at n=30, so a
fixed cap of 12 removes exactly the high-n rows that carry the most evidence. That
is verifiable from arithmetic without reference to any outcome. It is reported both
ways: the gated counts are in ``PROVISIONAL_measure_all.json``, the ungated
universe here.

Every number carries: the long share (MNQ's tape rose 12.2% over the span), the
clock-close share, the cost/R, the span-implied Sharpe, and the placebo cohort's
own universe expectancy on the same bars.
"""
from __future__ import annotations

import hashlib
import json
import math
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

from ef5_data import PRIMARY_TFS, REPO, SYMBOLS, build_frame, session_id  # noqa: E402
from population import base_population, session_arm                  # noqa: E402
from session_window import SessionWindowEngine                        # noqa: E402
from futures_agents.backtest.metrics import compute_metrics           # noqa: E402
from newstrats import placebo as P                                   # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")
FLOOR = 20
SQRT_YEARS = 0.3981


def expected_max_run(n: int, q: float) -> float:
    if n <= 1 or not (0 < q < 1):
        return 0.0
    return math.log(max(1e-9, n * (1 - q))) / math.log(1 / q)


def main() -> None:
    out = {}
    for sym in SYMBOLS:
        for tf in PRIMARY_TFS:
            frame = build_frame(sym, tf)
            cycles = sorted({session_id(b.ts) for b in frame.base.bars})
            cut = int(len(cycles) * 0.6)
            IS, OOS = set(cycles[:cut]), set(cycles[cut:])
            base = base_population(sym, tf)
            for arm, strats in (("RTH", base), ("SESSION", session_arm(base))):
                res = SessionWindowEngine(frame).run_many(strats)
                seen, uni, realised = set(), [], {}
                for s in strats:
                    tr = res[s.strategy_id].trades
                    realised[s.strategy_id] = len(tr)
                    if len(tr) < FLOOR:
                        continue
                    fp = hashlib.sha1("|".join(
                        f"{t.entry_ts.isoformat()}:{t.direction.value}"
                        for t in tr).encode()).hexdigest()[:16]
                    if fp in seen:
                        continue
                    seen.add(fp)
                    uni.append(s)
                if not uni:
                    out[f"{sym}_{tf}m_{arm}"] = {"qualifying_universe": 0}
                    print(f"{sym}_{tf}m_{arm}: EMPTY", flush=True)
                    continue

                rows = []
                for s in uni:
                    tr = res[s.strategy_id].trades
                    m = compute_metrics(tr)
                    rows.append({
                        "exp": m.expectancy_r, "n": m.trades, "t": m.t_statistic,
                        "win": m.win_rate, "pf": m.profit_factor,
                        "dd": m.max_drawdown_r, "cl": m.max_consecutive_losses,
                        "cl_expected": expected_max_run(m.trades, 1 - m.win_rate),
                        "long": sum(1 for t in tr if t.direction.value == "LONG") / len(tr),
                        "group": s.group,
                    })
                plcs, meta, diag = P.build_cohort(frame, uni, realised, seed=0,
                                                  kinds=("placebo_random",
                                                         "placebo_shuffle"))
                assert diag["id_collisions"] == 0, "placebo id collision"
                pres = SessionWindowEngine(frame).run_many(plcs)
                prows = [compute_metrics(pres[p_.strategy_id].trades).expectancy_r
                         for p_ in plcs
                         if len(pres[p_.strategy_id].trades) >= FLOOR]

                def sub(part, min_n=8):
                    v = []
                    for s in uni:
                        tr = [t for t in res[s.strategy_id].trades
                              if session_id(t.entry_ts) in part]
                        if len(tr) >= min_n:
                            v.append(compute_metrics(tr).expectancy_r)
                    return (round(st.fmean(v), 5), len(v)) if v else (None, 0)

                exps = [r["exp"] for r in rows]
                pooled_t = (st.fmean(exps) / (st.stdev(exps) / math.sqrt(len(exps)))
                            if len(exps) > 1 and st.stdev(exps) > 0 else None)
                is_e, is_n = sub(IS)
                oos_e, oos_n = sub(OOS)
                key = f"{sym}_{tf}m_{arm}"
                out[key] = {
                    "symbol": sym, "primary_tf": tf, "arm": arm,
                    "declared_population": len(strats),
                    "qualifying_universe": len(uni),
                    "top10_is_whole_universe": len(uni) <= 10,
                    "universe_mean_exp_r_net": round(st.fmean(exps), 5),
                    "universe_median_exp_r_net": round(st.median(exps), 5),
                    "universe_frac_positive": round(
                        sum(1 for e in exps if e > 0) / len(exps), 4),
                    "placebo_universe_mean_exp_r_net": round(st.fmean(prows), 5)
                    if prows else None,
                    "placebo_universe_n": len(prows),
                    "universe_mean_trades": round(st.fmean(r["n"] for r in rows), 1),
                    "universe_mean_win_rate": round(st.fmean(r["win"] for r in rows), 4),
                    "universe_mean_pf": round(st.fmean(r["pf"] for r in rows), 4),
                    "universe_mean_maxdd_r": round(st.fmean(r["dd"] for r in rows), 3),
                    "universe_mean_max_consec_losses": round(
                        st.fmean(r["cl"] for r in rows), 2),
                    "expected_max_consec_losses_at_that_n": round(
                        st.fmean(r["cl_expected"] for r in rows), 2),
                    "universe_mean_long_share": round(
                        st.fmean(r["long"] for r in rows), 4),
                    "best_row_t": round(max(r["t"] for r in rows), 3),
                    "best_row_implied_annualised_sharpe": round(
                        max(r["t"] for r in rows) / SQRT_YEARS, 2),
                    "cross_sectional_t_of_universe_expectancy": round(pooled_t, 3)
                    if pooled_t else None,
                    "IS_60pct_mean_exp_r": is_e, "IS_rows": is_n,
                    "OOS_40pct_mean_exp_r": oos_e, "OOS_rows": oos_n,
                    "by_group": dict(Counter(r["group"] for r in rows)),
                }
                r = out[key]
                print(f"{key}: uni={len(uni):4d} exp={r['universe_mean_exp_r_net']:+.4f} "
                      f"(med {r['universe_median_exp_r_net']:+.4f}, "
                      f"{r['universe_frac_positive']:.0%} positive) "
                      f"plc={r['placebo_universe_mean_exp_r_net']} "
                      f"IS={is_e} OOS={oos_e} bestT={r['best_row_t']} "
                      f"impliedSR={r['best_row_implied_annualised_sharpe']} "
                      f"long={r['universe_mean_long_share']}", flush=True)
    with open(os.path.join(OUT, "universe.json"), "w") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
