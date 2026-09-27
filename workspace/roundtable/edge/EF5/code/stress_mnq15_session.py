"""EF5 -- stressing the one arm-cell where reals beat placebos: MNQ 15m SESSION.

PROVISIONAL (EF1 unvalidated). Twelve arm-cells were measured; exactly one shows
reals above their own placebos (25 of 31, sign z = +3.41, Wilcoxon z = +2.82).
That is the same shape as the cautionary example in my dispatch -- MNQ 60m with
``rth_only=True``, the single favourable cell of 20, which failed its holdout and
its disjoint thirds. So it is stressed here before it is described as anything.

Four attacks, each of which killed a comparable finding somewhere in this repo:

1. **Effective sample size.** The sign test treats 31 paired rows as 31
   independent observations. They are not: they share bars, share conditions and
   share trades. Measured as mean pairwise Jaccard over realised trade ledgers,
   giving an effective n and a deflated z. This is the D28 shape (correlated arms
   inflate z ~3.3x) applied to the paired test rather than to ``T.ab``.
2. **Chronological holdout.** 60/40 split by 18:00->16:00 cycle. The rows are
   selected on the first 60% and their expectancy is read on the last 40%, with
   their own placebos carried through the same split.
3. **Disjoint thirds.** The cautionary example's best placebo landed 1st, 3rd and
   9th in disjoint thirds. Same test here.
4. **Multiple testing over the twelve arm-cells.** ``free_t(12) = 2.23``, and the
   span bound says any t on 0.1585 years implies ``SR_ann = t / 0.3981``.
"""
from __future__ import annotations

import json
import math
import os
import statistics as st
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
# EF5's own code dir FIRST: EF1/code also contains a module named measure.py and
# a bare `import measure` would silently pick up the wrong one.
sys.path.insert(0, HERE)
for p in (os.path.join(os.path.dirname(os.path.dirname(HERE)), "EF1", "code"),
          "/home/user/Futures01/workspace", "/home/user/Futures01"):
    if p not in sys.path:
        sys.path.append(p)

from ef5_data import REPO, build_frame, session_id                 # noqa: E402
from population import base_population, session_arm                # noqa: E402
from measure import FLOOR, gates_pass, score                       # noqa: E402
from session_window import SessionWindowEngine                     # noqa: E402
from futures_agents.backtest.metrics import compute_metrics         # noqa: E402
from newstrats import placebo as P                                 # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")
SYMBOL, TF = "MNQ", 15
SPAN_YEARS = 0.1585


def sign_z(wins: int, n: int) -> float:
    return ((wins - n / 2) / math.sqrt(n / 4)) if n else 0.0


def main() -> None:
    frame = build_frame(SYMBOL, TF)
    strats = session_arm(base_population(SYMBOL, TF))
    eng = SessionWindowEngine(frame)
    res = eng.run_many(strats)

    # ---- the floored, gated, clone-collapsed real cohort --------------
    import hashlib
    seen: Dict[str, str] = {}
    reals = []
    ledger: Dict[str, list] = {}
    realised = {}
    for s in strats:
        tr = res[s.strategy_id].trades
        realised[s.strategy_id] = len(tr)
        if len(tr) < FLOOR:
            continue
        fp = hashlib.sha1("|".join(
            f"{t.entry_ts.isoformat()}:{t.direction.value}" for t in tr
        ).encode()).hexdigest()[:16]
        if fp in seen:
            continue
        seen[fp] = s.strategy_id
        m = compute_metrics(tr)
        if not gates_pass(m):
            continue
        reals.append(s)
        ledger[s.strategy_id] = tr

    # ---- 1. effective sample size from trade-ledger overlap -----------
    keys = {s.strategy_id: {(t.entry_ts, t.direction.value) for t in ledger[s.strategy_id]}
            for s in reals}
    ids = list(keys)
    jac = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            A, B = keys[a], keys[b]
            u = len(A | B)
            if u:
                jac.append(len(A & B) / u)
    mean_j = st.fmean(jac) if jac else 0.0
    n_rows = len(ids)
    # Kish-style effective n under exchangeable correlation rho ~ mean Jaccard.
    n_eff = n_rows / (1.0 + (n_rows - 1) * mean_j) if n_rows else 0.0

    # ---- placebos, same engine ----------------------------------------
    plcs, meta, diag = P.build_cohort(frame, reals, realised, seed=0,
                                      kinds=("placebo_random", "placebo_shuffle"))
    pres = SessionWindowEngine(frame).run_many(plcs)

    def cohort_rows(split=None):
        """(real rows, placebo rows) restricted to a cycle set."""
        def m_of(tr):
            sub = [t for t in tr if split is None or session_id(t.entry_ts) in split]
            return (compute_metrics(sub), len(sub))
        rr, pp = [], []
        for s in reals:
            m, n = m_of(res[s.strategy_id].trades)
            rr.append({"id": s.strategy_id, "n": n, "exp": m.expectancy_r,
                       "t": m.t_statistic, "score": score(m), "kind": "real",
                       "group": s.group})
        for p_ in plcs:
            m, n = m_of(pres[p_.strategy_id].trades)
            pp.append({"id": p_.strategy_id, "n": n, "exp": m.expectancy_r,
                       "t": m.t_statistic, "score": score(m),
                       "kind": meta[p_.strategy_id].kind,
                       "base": meta[p_.strategy_id].base_id})
        return rr, pp

    def paired(rr, pp, min_n=10):
        by_base: Dict[str, List[dict]] = {}
        for x in pp:
            if x["n"] >= min_n:
                by_base.setdefault(x["base"], []).append(x)
        diffs, wins = [], 0
        for r in rr:
            own = by_base.get(r["id"], [])
            if not own or r["n"] < min_n:
                continue
            c = st.fmean(x["exp"] for x in own)
            diffs.append(r["exp"] - c)
            wins += r["exp"] > c
        n = len(diffs)
        return {"n_pairs": n, "reals_above": wins,
                "mean_diff_r": round(st.fmean(diffs), 5) if diffs else None,
                "sign_z": round(sign_z(wins, n), 3) if n else None}

    def best_placebo_rank(rr, pp, min_n=10):
        tab = sorted([x for x in rr + pp if x["n"] >= min_n],
                     key=lambda x: -x["score"])
        br = next((i for i, x in enumerate(tab, 1) if x["kind"] != "real"), None)
        nr = sum(1 for x in tab if x["kind"] == "real")
        npl = len(tab) - nr
        return {"best_placebo_rank": br, "n_reals": nr, "n_placebos": npl,
                "null": P.null_rank_distribution(len(tab), npl) if npl else None,
                "top1_kind": tab[0]["kind"] if tab else None}

    cycles = sorted({session_id(b.ts) for b in frame.base.bars})
    cut = int(len(cycles) * 0.6)
    is_, oos = set(cycles[:cut]), set(cycles[cut:])
    thirds = [set(cycles[i::3]) for i in range(3)]      # interleaved
    blocks = [set(cycles[i * len(cycles) // 3:(i + 1) * len(cycles) // 3])
              for i in range(3)]                        # contiguous

    full_r, full_p = cohort_rows(None)
    out = {
        "PROVISIONAL": "EF1 unvalidated; not publishable",
        "cell": f"{SYMBOL} {TF}m SESSION",
        "cycles": len(cycles), "span_years": SPAN_YEARS,
        "n_real_rows": n_rows,
        "mean_pairwise_trade_jaccard": round(mean_j, 4),
        "effective_n_rows": round(n_eff, 2),
        "full": {"paired": paired(full_r, full_p),
                 "ranking": best_placebo_rank(full_r, full_p)},
        "in_sample_60pct": None, "oos_40pct": None,
        "interleaved_thirds": [], "contiguous_thirds": [],
        "multiple_testing": {
            "arm_cells_searched": 12, "free_t_12": round(math.sqrt(2 * math.log(12)), 3),
            "note": "any t on this span implies SR_ann = t / 0.3981",
        },
    }
    r_is, p_is = cohort_rows(is_)
    r_oos, p_oos = cohort_rows(oos)
    out["in_sample_60pct"] = {"cycles": cut, "paired": paired(r_is, p_is),
                              "ranking": best_placebo_rank(r_is, p_is)}
    out["oos_40pct"] = {"cycles": len(cycles) - cut, "paired": paired(r_oos, p_oos),
                        "ranking": best_placebo_rank(r_oos, p_oos)}

    # top-10 selected IN SAMPLE, then read OUT of sample -- the exact artefact
    # RANKING_FINDINGS was burned by
    tab_is = sorted([x for x in r_is if x["n"] >= 10], key=lambda x: -x["score"])
    top10 = [x["id"] for x in tab_is[:10]]
    oos_by_id = {x["id"]: x for x in r_oos}
    sel = [oos_by_id[i]["exp"] for i in top10 if i in oos_by_id and oos_by_id[i]["n"] >= 5]
    allr = [x["exp"] for x in r_oos if x["n"] >= 5]
    pl_oos = [x["exp"] for x in p_oos if x["n"] >= 5]
    out["select_in_sample_read_out_of_sample"] = {
        "n_selected_with_oos_sample": len(sel),
        "selected_mean_exp_r_oos": round(st.fmean(sel), 5) if sel else None,
        "whole_universe_mean_exp_r_oos": round(st.fmean(allr), 5) if allr else None,
        "placebo_mean_exp_r_oos": round(st.fmean(pl_oos), 5) if pl_oos else None,
        "reading": ("selected < whole universe reproduces the programme's "
                    "'selecting is worse than not selecting' finding"),
    }

    for label, parts in (("interleaved_thirds", thirds),
                         ("contiguous_thirds", blocks)):
        for i, part in enumerate(parts):
            rr, pp = cohort_rows(part)
            out[label].append({"third": i, "paired": paired(rr, pp, min_n=6),
                               "ranking": best_placebo_rank(rr, pp, min_n=6)})

    with open(os.path.join(OUT, "PROVISIONAL_stress_MNQ15_SESSION.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
