"""EF5 -- the two tests that decide whether MNQ 15m SESSION is an edge or a drift.

From ``stress2``: MNQ rose **+12.19%** over the 41 cycles, and the one contiguous
third in which it FELL (-1.69%) is the one third where the paired effect reversed
(sign z = -1.90). That is a directional-regime explanation and it has to be tested,
not noted.

Three tests here:

1. **Per-third paired difference beside that third's price drift, split by
   direction.** If the effect is a long bias in a rising tape, the long leg carries
   it and the sign of the paired difference tracks the sign of the drift.
2. **Placebo kind separated.** ``placebo_random`` destroys timing AND direction;
   ``placebo_shuffle`` keeps the real timing and destroys only the direction
   labels. Beating shuffle means the DIRECTION call carries information; beating
   random but not shuffle means only the timing does.
3. **Effective sample size on the selected cohort**, from mean pairwise Jaccard of
   realised trade ledgers, and the deflated sign z against ``free_t(12) = 2.229``
   for the twelve arm-cells searched.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import statistics as st
import sys
from collections import Counter
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for p in (os.path.join(os.path.dirname(os.path.dirname(HERE)), "EF1", "code"),
          "/home/user/Futures01/workspace", "/home/user/Futures01"):
    if p not in sys.path:
        sys.path.append(p)

from ef5_data import REPO, build_frame, session_id                 # noqa: E402
from population import base_population, session_arm               # noqa: E402
from session_window import SessionWindowEngine                     # noqa: E402
from futures_agents.backtest.metrics import compute_metrics        # noqa: E402
from newstrats import placebo as P                                 # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")
SYMBOL, TF = "MNQ", 15
IS_FLOOR = 12


def sign_z(w: int, n: int) -> float:
    return ((w - n / 2) / math.sqrt(n / 4)) if n else 0.0


def main() -> None:
    frame = build_frame(SYMBOL, TF)
    bars = frame.base.bars
    cycles = sorted({session_id(b.ts) for b in bars})
    cut = int(len(cycles) * 0.6)
    IS = set(cycles[:cut])

    strats = session_arm(base_population(SYMBOL, TF))
    res = SessionWindowEngine(frame).run_many(strats)

    seen, realised, cands = set(), {}, []
    for s in strats:
        tr = res[s.strategy_id].trades
        realised[s.strategy_id] = len(tr)
        if not tr:
            continue
        fp = hashlib.sha1("|".join(
            f"{t.entry_ts.isoformat()}:{t.direction.value}" for t in tr).encode()
        ).hexdigest()[:16]
        if fp in seen:
            continue
        seen.add(fp)
        cands.append(s)

    sel = []
    for s in cands:
        tr = [t for t in res[s.strategy_id].trades if session_id(t.entry_ts) in IS]
        if len(tr) < IS_FLOOR:
            continue
        if compute_metrics(tr).t_statistic < 0:
            continue
        sel.append(s)

    plcs, meta, diag = P.build_cohort(frame, sel, realised, seed=0,
                                      kinds=("placebo_random", "placebo_shuffle"))
    pres = SessionWindowEngine(frame).run_many(plcs)

    # ---- 3. effective n on the selected cohort -------------------------
    keys = {s.strategy_id: {(t.entry_ts, t.direction.value)
                            for t in res[s.strategy_id].trades} for s in sel}
    ids = list(keys)
    jac = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            u = len(keys[a] | keys[b])
            if u:
                jac.append(len(keys[a] & keys[b]) / u)
    mj = st.fmean(jac) if jac else 0.0
    n_eff = len(ids) / (1 + (len(ids) - 1) * mj) if ids else 0.0

    def paired_by_kind(part, min_n, kind=None, direction=None):
        by_base: Dict[str, List[float]] = {}
        for p_ in plcs:
            md = meta[p_.strategy_id]
            if kind and md.kind != kind:
                continue
            tr = [t for t in pres[p_.strategy_id].trades
                  if session_id(t.entry_ts) in part
                  and (direction is None or t.direction.value == direction)]
            if len(tr) >= min_n:
                by_base.setdefault(md.base_id, []).append(
                    compute_metrics(tr).expectancy_r)
        diffs, wins, re_, pe = [], 0, [], []
        for s in sel:
            tr = [t for t in res[s.strategy_id].trades
                  if session_id(t.entry_ts) in part
                  and (direction is None or t.direction.value == direction)]
            own = by_base.get(s.strategy_id, [])
            if len(tr) < min_n or not own:
                continue
            e = compute_metrics(tr).expectancy_r
            c = st.fmean(own)
            re_.append(e); pe.append(c); diffs.append(e - c); wins += e > c
        n = len(diffs)
        return {"n_pairs": n, "reals_above": wins,
                "real_exp_r": round(st.fmean(re_), 5) if re_ else None,
                "placebo_exp_r": round(st.fmean(pe), 5) if pe else None,
                "mean_diff_r": round(st.fmean(diffs), 5) if diffs else None,
                "sign_z": round(sign_z(wins, n), 3) if n else None}

    out = {
        "PROVISIONAL": "EF1 unvalidated; not publishable",
        "cell": f"{SYMBOL} {TF}m SESSION",
        "selected_on_IS_only": len(sel),
        "selected_by_group": dict(Counter(s.group for s in sel)),
        "placebo_diag": diag,
        "effective_n": {
            "n_rows": len(ids), "mean_pairwise_trade_jaccard": round(mj, 4),
            "n_eff": round(n_eff, 2),
        },
        "by_placebo_kind_full_span": {
            "vs_placebo_random": paired_by_kind(set(cycles), 15, "placebo_random"),
            "vs_placebo_shuffle": paired_by_kind(set(cycles), 15, "placebo_shuffle"),
        },
        "by_direction_full_span": {
            "LONG_only": paired_by_kind(set(cycles), 10, None, "LONG"),
            "SHORT_only": paired_by_kind(set(cycles), 10, None, "SHORT"),
        },
        "contiguous_thirds": [],
    }
    for i in range(3):
        part = set(cycles[i * len(cycles) // 3:(i + 1) * len(cycles) // 3])
        pb = [b for b in bars if session_id(b.ts) in part]
        out["contiguous_thirds"].append({
            "third": i, "cycles": len(part),
            "price_drift_pct": round(100 * (pb[-1].close / pb[0].close - 1), 3),
            "all": paired_by_kind(part, 6),
            "LONG_only": paired_by_kind(part, 4, None, "LONG"),
            "SHORT_only": paired_by_kind(part, 4, None, "SHORT"),
            "vs_random": paired_by_kind(part, 6, "placebo_random"),
            "vs_shuffle": paired_by_kind(part, 6, "placebo_shuffle"),
        })

    z = out["by_placebo_kind_full_span"]["vs_placebo_shuffle"]["sign_z"]
    n = out["by_placebo_kind_full_span"]["vs_placebo_shuffle"]["n_pairs"]
    if z is not None and n:
        out["deflation"] = {
            "sign_z_vs_shuffle_raw": z,
            "sign_z_deflated_by_effective_n": round(z * math.sqrt(n_eff / n), 3),
            "free_t_12_arm_cells": 2.229,
            "free_t_population_21060": 4.462,
        }
    with open(os.path.join(OUT, "PROVISIONAL_stress3_MNQ15_SESSION.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
