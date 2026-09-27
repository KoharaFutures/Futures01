"""EF5 -- fixing a selection leak in my own holdout, and testing the regime explanation.

Two defects found in ``stress_mnq15_session.py`` by reading its own output:

**Leak.** The paired cohort was gated on ``t_statistic >= 0`` measured over the
**full** span, then its expectancy was read on the last 40% of that same span. The
gate therefore used out-of-sample information. The OOS sign z of 6.19 is not a
clean holdout. Fixed here: the cohort is selected using the in-sample cycles ONLY,
and the out-of-sample cycles are never touched during selection.

**Implausibility.** The whole qualifying universe showed +0.298R per trade out of
sample. An index micro does not pay +0.3R per trade to an arbitrary universe. The
obvious structural explanation is that 41 consecutive sessions is one regime, and
the SESSION arm holds overnight, so a directional drift over the window pays every
long-biased overnight rule set at once. Tested directly: the realised drift, and
the long/short split of the cohort's expectancy.
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

from ef5_data import ET, REPO, build_frame, session_id             # noqa: E402
from population import base_population, session_arm               # noqa: E402
from session_window import SessionWindowEngine                     # noqa: E402
from futures_agents.backtest.metrics import compute_metrics        # noqa: E402
from newstrats import placebo as P                                 # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")
SYMBOL, TF = "MNQ", 15


def sign_z(w: int, n: int) -> float:
    return ((w - n / 2) / math.sqrt(n / 4)) if n else 0.0


def main() -> None:
    frame = build_frame(SYMBOL, TF)
    bars = frame.base.bars
    cycles = sorted({session_id(b.ts) for b in bars})
    cut = int(len(cycles) * 0.6)
    IS, OOS = set(cycles[:cut]), set(cycles[cut:])

    # ---- the regime test, first, because it may explain everything -----
    first, last = bars[0], bars[-1]
    is_bars = [b for b in bars if session_id(b.ts) in IS]
    oos_bars = [b for b in bars if session_id(b.ts) in OOS]
    drift = {
        "full_first_close": first.close, "full_last_close": last.close,
        "full_pct": round(100 * (last.close / first.close - 1), 3),
        "is_pct": round(100 * (is_bars[-1].close / is_bars[0].close - 1), 3),
        "oos_pct": round(100 * (oos_bars[-1].close / oos_bars[0].close - 1), 3),
        "thirds_pct": [],
    }
    for i in range(3):
        part = [b for b in bars
                if session_id(b.ts) in set(cycles[i * len(cycles) // 3:
                                                  (i + 1) * len(cycles) // 3])]
        drift["thirds_pct"].append(round(100 * (part[-1].close / part[0].close - 1), 3))

    # ---- run once, slice after -----------------------------------------
    strats = session_arm(base_population(SYMBOL, TF))
    res = SessionWindowEngine(frame).run_many(strats)

    # clone collapse on the FULL ledger (structure, not performance -- safe)
    seen, cands, realised = set(), [], {}
    for s in strats:
        tr = res[s.strategy_id].trades
        realised[s.strategy_id] = len(tr)
        fp = hashlib.sha1("|".join(
            f"{t.entry_ts.isoformat()}:{t.direction.value}" for t in tr).encode()
        ).hexdigest()[:16]
        if not tr or fp in seen:
            continue
        seen.add(fp)
        cands.append(s)

    # SELECTION uses in-sample cycles only.
    IS_FLOOR = 12          # 24 of 41 cycles, so the floor is scaled down from 20
    sel = []
    for s in cands:
        tr = [t for t in res[s.strategy_id].trades if session_id(t.entry_ts) in IS]
        if len(tr) < IS_FLOOR:
            continue
        m = compute_metrics(tr)
        if m.t_statistic < 0:
            continue
        sel.append(s)

    plcs, meta, _ = P.build_cohort(frame, sel, realised, seed=0,
                                   kinds=("placebo_random", "placebo_shuffle"))
    pres = SessionWindowEngine(frame).run_many(plcs)

    def paired(part, min_n):
        by_base: Dict[str, List[float]] = {}
        for p_ in plcs:
            tr = [t for t in pres[p_.strategy_id].trades
                  if session_id(t.entry_ts) in part]
            if len(tr) >= min_n:
                by_base.setdefault(meta[p_.strategy_id].base_id, []).append(
                    compute_metrics(tr).expectancy_r)
        diffs, wins, reals_exp, plc_exp = [], 0, [], []
        for s in sel:
            tr = [t for t in res[s.strategy_id].trades
                  if session_id(t.entry_ts) in part]
            own = by_base.get(s.strategy_id, [])
            if len(tr) < min_n or not own:
                continue
            e = compute_metrics(tr).expectancy_r
            c = st.fmean(own)
            reals_exp.append(e)
            plc_exp.append(c)
            diffs.append(e - c)
            wins += e > c
        n = len(diffs)
        return {"n_pairs": n, "reals_above": wins,
                "real_mean_exp_r": round(st.fmean(reals_exp), 5) if reals_exp else None,
                "placebo_mean_exp_r": round(st.fmean(plc_exp), 5) if plc_exp else None,
                "mean_diff_r": round(st.fmean(diffs), 5) if diffs else None,
                "sign_z": round(sign_z(wins, n), 3) if n else None}

    def direction_split(part):
        L, S = [], []
        for s in sel:
            for t in res[s.strategy_id].trades:
                if session_id(t.entry_ts) in part:
                    (L if t.direction.value == "LONG" else S).append(t.net_r)
        return {"long_n": len(L), "long_exp_r": round(st.fmean(L), 5) if L else None,
                "short_n": len(S), "short_exp_r": round(st.fmean(S), 5) if S else None}

    out = {
        "PROVISIONAL": "EF1 unvalidated; not publishable",
        "cell": f"{SYMBOL} {TF}m SESSION",
        "cycles": len(cycles), "is_cycles": cut, "oos_cycles": len(cycles) - cut,
        "price_drift": drift,
        "candidates_after_clone_collapse": len(cands),
        "selected_on_IS_only": len(sel),
        "selected_by_group": dict(Counter(s.group for s in sel)),
        "IS_paired": paired(IS, IS_FLOOR),
        "OOS_paired_CLEAN": paired(OOS, 8),
        "IS_direction": direction_split(IS),
        "OOS_direction": direction_split(OOS),
        "full_direction": direction_split(set(cycles)),
        "note": ("selection touched only the IS cycles; the OOS_paired_CLEAN row is "
                 "the only holdout number in EF5 with no selection leak"),
    }
    with open(os.path.join(OUT, "PROVISIONAL_stress2_MNQ15_SESSION.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
