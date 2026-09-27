"""EF4 - the analysis that decides what may be reported.

Five things, in the order they gate each other:

1. **The rule-7 replication.** BRIEF rule 7: "sub-hourly is a graveyard - at 5 minutes,
   11-16% of strategies make money." That was measured on the ~19-session `csv/raw`
   sample under the OLD regime (flat at the contract's RTH close, no overnight hold). Here
   it is re-measured on 41 sessions under the 18:00->16:00 rule, per timeframe, GROSS and
   NET separately - because "make money" is a different population gross and net, and on a
   scalp cell the gap is the dominant term.

2. **The split-sample forward test.** Sessions are split 60/40 by calendar order
   (in-sample = first 24 of 41 sessions, out-of-sample = last 17). Every arm is scored on
   each half separately. Rank correlation and top-decile persistence between the halves is
   what says whether an in-sample rank means anything.

3. **The selection test - the programme's own central negative, re-run.** Rank on the
   in-sample half, then compare the OOS expectancy of the top 10 against the OOS
   expectancy of the WHOLE qualifying universe. The programme measured selecting as worse
   than not selecting (-0.0155R vs +0.022R for the universe). If that reproduces here, a
   top-10 list is not merely underpowered - it is actively worse than its own population.

4. **Walk-forward.** Three contiguous folds of ~13 sessions. Reported with the fold trade
   counts beside it, because a fold with 9 trades is not a fold.

5. **Deflation.** `free_t = sqrt(2 ln n)` at the DECLARED n of the track the row came
   from, and the annualised Sharpe that t implies on 0.1585 years.

No row is promoted on in-sample rank alone. The output is the input to `FINDINGS.md`.
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

ROOT = Path("/home/user/Futures01")
OUT = ROOT / "workspace/roundtable/edge/EF4/out"
CELLS = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]
SPAN_YEARS = 0.15852


def free_t(n: int) -> float:
    return math.sqrt(2.0 * math.log(max(2, n)))


def load(symbol: str, tf: int, track: str):
    p = OUT / f"run_{symbol}_{tf}m_{track}.json"
    return json.loads(p.read_text()) if p.is_file() else None


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
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
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den = math.sqrt(sum((rx[i] - mx) ** 2 for i in range(n))
                    * sum((ry[i] - my) ** 2 for i in range(n)))
    return num / den if den else 0.0


def rule7() -> dict:
    """% of arms with positive expectancy, per cell, gross and net, with a sample floor."""
    rows = []
    for sym, tf in CELLS:
        d = load(sym, tf, "both") or load(sym, tf, "B")
        if d is None:
            continue
        arms = [r for r in d["rows"] if r["group"] == "EF4_SCREEN"]
        for floor in (0, 20, 30):
            elig = [a for a in arms if a["trades"] >= max(1, floor)]
            if not elig:
                continue
            pos_net = sum(1 for a in elig if a["expectancy_net_r"] > 0)
            pos_gross = sum(1 for a in elig if a["expectancy_gross_r"] > 0)
            rows.append({
                "symbol": sym, "tf": tf, "trade_floor": floor,
                "arms_total": len(arms), "arms_eligible": len(elig),
                "pct_positive_net": pos_net / len(elig),
                "pct_positive_gross": pos_gross / len(elig),
                "median_net_r": st.median(a["expectancy_net_r"] for a in elig),
                "median_gross_r": st.median(a["expectancy_gross_r"] for a in elig),
                "median_cost_r": st.median(a["cost_total_r"] for a in elig),
                "median_trades": st.median(a["trades"] for a in elig),
                "zero_trade_arms": sum(1 for a in arms if a["trades"] == 0),
            })
    return {"rows": rows}


def main() -> None:
    res = {"rule7": rule7()}
    p = OUT / "analysis_rule7.json"
    p.write_text(json.dumps(res, indent=2))
    print(f"{'cell':<10}{'floor':>6}{'arms':>7}{'elig':>7}{'%pos net':>10}"
          f"{'%pos gross':>12}{'med net':>10}{'med gross':>11}{'med cost':>10}"
          f"{'med n':>7}{'0-trade':>9}")
    for r in res["rule7"]["rows"]:
        print(f"{r['symbol']+' '+str(r['tf'])+'m':<10}{r['trade_floor']:>6}"
              f"{r['arms_total']:>7}{r['arms_eligible']:>7}"
              f"{r['pct_positive_net']*100:>9.1f}%{r['pct_positive_gross']*100:>11.1f}%"
              f"{r['median_net_r']:>10.4f}{r['median_gross_r']:>11.4f}"
              f"{r['median_cost_r']:>10.4f}{r['median_trades']:>7.0f}"
              f"{r['zero_trade_arms']:>9}")
    print(f"\nwrote {p}")


if __name__ == "__main__":
    main()
