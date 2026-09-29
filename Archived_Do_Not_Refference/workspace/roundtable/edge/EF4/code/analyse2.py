"""EF4 - split-sample, the selection test, walk-forward, and the final ranking.

Reads `out/run_<sym>_<tf>m_both.json`, which already carries per-arm metrics on the full
sample, on the in-sample and out-of-sample halves (60/40 by 18:00->16:00 session), and on
three contiguous walk-forward folds.

Four questions, in the order that decides what may be published:

1. **Does an in-sample rank survive?** Spearman between IS and OOS net expectancy over all
   arms meeting a trade floor in BOTH halves, plus top-decile persistence.

2. **The selection test.** The programme's central negative: trading last period's top 10
   returned -0.0155R against a -0.0104R null and UNDERPERFORMED trading the whole
   qualifying universe (+0.022R vs +0.057R). Re-run here: rank on IS, then compare the
   OOS expectancy of the IS-top-10 against the OOS expectancy of the whole qualifying
   universe. If selecting loses again under a session rule never previously run, that is
   the same negative reproduced in a new regime.

3. **Walk-forward.** Sign agreement across three folds, with fold trade counts beside it.

4. **The ranking.** Durability, not profit: net expectancy in R, with a sample-size penalty,
   the t-statistic of the R series, max drawdown and max consecutive losses. Rank score is
   reported; rows are NOT promoted on it alone - every row carries its t against the
   declared threshold of its own track.
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path
from typing import Dict, List, Sequence

ROOT = Path("/home/user/Futures01")
OUT = ROOT / "workspace/roundtable/edge/EF4/out"
CELLS = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]
FREE_T_A, FREE_T_B = 2.677, 4.441
N_A, N_B = 36, 19152
MIN_TRADES = 30


def spearman(xs, ys):
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(list(xs)), rank(list(ys))
    n = len(rx)
    if n < 3:
        return 0.0
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n))
                    * sum((ry[i] - my) ** 2 for i in range(n)))
    return num / den if den else 0.0


def durability(r: dict, free_t: float) -> float:
    """Rank score. Never highest profit.

    expectancy in R, shrunk toward zero by a sample-size penalty, then penalised for
    drawdown and for consecutive losses. The shrink is
    ``n / (n + k)`` with ``k = 50`` - at 30 trades an expectancy is worth 37% of its face
    value, at 200 trades 80%. k = 50 is declared, not tuned: it is the trade count at which
    the required per-trade mu/sigma for free_t = 1.177 (0.166, burst 01) is still an
    unusual number, so below it an expectancy should not be believed.
    """
    n = r["trades"]
    if n == 0:
        return -9.9
    shrink = n / (n + 50.0)
    e = r["expectancy_net_r"] * shrink
    dd_pen = 0.02 * r.get("max_dd_r", 0.0) / max(1.0, math.sqrt(n))
    cl_pen = 0.01 * r.get("max_consec_losses", 0)
    t_bonus = 0.02 * max(0.0, r.get("t_stat", 0.0) - free_t)
    return e - dd_pen - cl_pen + t_bonus


def main() -> None:
    report = {"cells": [], "selection_test": [], "walkforward": []}
    print("=" * 108)
    print("SPLIT-SAMPLE (60/40 by 18:00->16:00 session) AND THE SELECTION TEST")
    print("=" * 108)
    for sym, tf in CELLS:
        p = OUT / f"run_{sym}_{tf}m_both.json"
        if not p.is_file():
            print(f"{sym} {tf}m: MISSING")
            continue
        d = json.loads(p.read_text())
        arms = d["rows"]
        scr = [a for a in arms if a["group"] == "EF4_SCREEN"]
        both = [a for a in scr
                if a["is"]["trades"] >= MIN_TRADES and a["oos"]["trades"] >= MIN_TRADES]
        rho = spearman([a["is"]["expectancy_net_r"] for a in both],
                       [a["oos"]["expectancy_net_r"] for a in both]) if len(both) > 2 else 0.0
        # selection test
        sel = None
        if len(both) >= 30:
            ranked = sorted(both, key=lambda a: -a["is"]["expectancy_net_r"])
            top10 = ranked[:10]
            def pooled(rows, half):
                num = sum(r[half]["expectancy_net_r"] * r[half]["trades"] for r in rows)
                den = sum(r[half]["trades"] for r in rows)
                return num / den if den else 0.0
            sel = {
                "symbol": sym, "tf": tf,
                "qualifying_arms": len(both),
                "top10_is_expectancy": pooled(top10, "is"),
                "top10_oos_expectancy": pooled(top10, "oos"),
                "universe_is_expectancy": pooled(both, "is"),
                "universe_oos_expectancy": pooled(both, "oos"),
                "selection_beat_universe_oos": pooled(top10, "oos") > pooled(both, "oos"),
                "top10_oos_trades": sum(r["oos"]["trades"] for r in top10),
                "universe_oos_trades": sum(r["oos"]["trades"] for r in both),
                "spearman_is_oos": rho,
            }
            report["selection_test"].append(sel)
            print(f"{sym} {tf}m  qualifying={len(both):<5} rho(IS,OOS)={rho:+.4f}   "
                  f"top10 IS={sel['top10_is_expectancy']:+.4f} -> OOS="
                  f"{sel['top10_oos_expectancy']:+.4f}   "
                  f"universe IS={sel['universe_is_expectancy']:+.4f} -> OOS="
                  f"{sel['universe_oos_expectancy']:+.4f}   "
                  f"selection {'WINS' if sel['selection_beat_universe_oos'] else 'LOSES'}")
        else:
            print(f"{sym} {tf}m  qualifying={len(both)} - below 30, selection test not run")
        report["cells"].append({"symbol": sym, "tf": tf,
                                "arms": len(arms), "screen_arms": len(scr),
                                "qualifying_both_halves": len(both),
                                "spearman_is_oos": rho,
                                "sessions": d.get("sessions"),
                                "is_sessions": d.get("is_sessions"),
                                "oos_sessions": d.get("oos_sessions"),
                                "counters": d["counters"]})

    print()
    print("=" * 108)
    print("WALK-FORWARD: sign agreement across three contiguous folds (screen arms)")
    print("=" * 108)
    for sym, tf in CELLS:
        p = OUT / f"run_{sym}_{tf}m_both.json"
        if not p.is_file():
            continue
        d = json.loads(p.read_text())
        scr = [a for a in d["rows"] if a["group"] == "EF4_SCREEN"]
        ok = [a for a in scr if all(f["trades"] >= 10 for f in a["folds"])]
        if not ok:
            print(f"{sym} {tf}m: no arm reaches 10 trades in all three folds "
                  f"({len(scr)} screen arms)")
            continue
        all3 = sum(1 for a in ok
                   if all(f["expectancy_net_r"] > 0 for f in a["folds"]))
        none3 = sum(1 for a in ok
                    if all(f["expectancy_net_r"] <= 0 for f in a["folds"]))
        med = [st.median(a["folds"][k]["expectancy_net_r"] for a in ok) for k in range(3)]
        print(f"{sym} {tf}m  arms with >=10 trades in all 3 folds = {len(ok):<5} "
              f"positive in all 3 = {all3} ({all3/len(ok):.2%})  "
              f"negative in all 3 = {none3} ({none3/len(ok):.2%})  "
              f"median fold expectancy = "
              f"{med[0]:+.4f} / {med[1]:+.4f} / {med[2]:+.4f}")
        report["walkforward"].append({
            "symbol": sym, "tf": tf, "arms": len(ok),
            "positive_all_three": all3, "negative_all_three": none3,
            "median_fold_expectancy": med,
            "expected_all_three_if_coinflip": 0.125})

    (OUT / "analysis_split.json").write_text(json.dumps(report, indent=2))
    print(f"\nwrote {OUT / 'analysis_split.json'}")


if __name__ == "__main__":
    main()
