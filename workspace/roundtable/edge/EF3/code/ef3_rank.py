"""EF3 stage 3 - rank, control, walk-forward. Protocol: bursts/04.

Nothing here chooses a gate or a sort key; all of those are fixed in burst 04.
Every window metric is computed twice where possible - once from stage 1's true
windowed runs and once from the stage 2 full-span ledger sliced - and the two are
reported side by side so the slicing approximation is visible, not assumed.
"""
from __future__ import annotations

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF3/out")
IS_FRAC = 0.60
MIN_IS_TRADES = 30
MIN_OOS_TRADES = 10
FOLD_CUTS = (0.40, 0.50, 0.60, 0.70, 0.80, 1.00)
SPAN_YEARS = 718.9 / 365.25


def free_t(n: int) -> float:
    return math.sqrt(2.0 * math.log(max(2, int(n))))


def wmetrics(rows: Sequence[Sequence], lo: int, hi: int, strict: bool = False) -> dict:
    """Metrics over trades whose ENTRY index is in [lo, hi).

    ``strict=True`` also requires the exit inside the window - the arm
    RANKING_FINDINGS measured at -0.004R against the loose rule.
    """
    sel = [t for t in rows if lo <= t[0] < hi and (not strict or t[1] < hi)]
    n = len(sel)
    if n == 0:
        return {"trades": 0}
    r = [t[2] for t in sel]
    wins = [x for x in r if x > 0]
    losses = [x for x in r if x < 0]
    mean = sum(r) / n
    sd = statistics.stdev(r) if n > 1 else 0.0
    aw = sum(wins) / len(wins) if wins else 0.0
    al = sum(losses) / len(losses) if losses else 0.0
    gl = -sum(losses)
    eq = peak = maxdd = 0.0
    dds = []
    cl = bl = cw = bw = 0
    for x in r:
        eq += x
        peak = max(peak, eq)
        dds.append(peak - eq)
        maxdd = max(maxdd, peak - eq)
        if x > 0:
            cw += 1; cl = 0
        elif x < 0:
            cl += 1; cw = 0
        bw = max(bw, cw); bl = max(bl, cl)
    dn = [x for x in r if x < 0]
    dsd = math.sqrt(sum(x * x for x in dn) / len(dn)) if dn else 0.0
    return {
        "trades": n, "expectancy_r": round(mean, 5),
        "gross_expectancy_r": round(sum(t[3] for t in sel) / n, 5),
        "total_r": round(sum(r), 3),
        "win_rate": round(len(wins) / n, 4),
        "avg_win_r": round(aw, 4), "avg_loss_r": round(al, 4),
        "payoff": round(aw / abs(al), 4) if al else None,
        "profit_factor": round(sum(wins) / gl, 4) if gl else None,
        "std_r": round(sd, 4),
        "t_stat": round(mean / (sd / math.sqrt(n)), 4) if sd > 0 else None,
        "sharpe_per_trade": round(mean / sd, 4) if sd > 0 else None,
        "sortino_per_trade": round(mean / dsd, 4) if dsd > 0 else None,
        "max_dd_r": round(maxdd, 4), "avg_dd_r": round(sum(dds) / len(dds), 4),
        "max_consec_wins": bw, "max_consec_losses": bl,
        "avg_hours_held": round(sum(t[8] for t in sel) / n, 3),
        "max_hours_held": round(max(t[8] for t in sel), 3),
        "avg_mfe_r": round(sum(t[6] for t in sel) / n, 4),
        "avg_mae_r": round(sum(t[7] for t in sel) / n, 4),
        "long_share": round(sum(t[4] for t in sel) / n, 3),
        "exit_reasons": dict(Counter(t[5] for t in sel)),
    }


def slice_by(rows, lo, hi, field_ix) -> dict:
    g = defaultdict(list)
    for t in rows:
        if lo <= t[0] < hi:
            g[t[field_ix]].append(t[2])
    return {k: {"n": len(v), "exp_r": round(sum(v) / len(v), 4)}
            for k, v in sorted(g.items())}


def paired_sign_and_t(diffs: Sequence[float]) -> dict:
    """Paired test on (real - placebo) differences. NOT T.ab (D28)."""
    n = len(diffs)
    if n < 2:
        return {"n": n}
    m = sum(diffs) / n
    sd = statistics.stdev(diffs)
    pos = sum(1 for d in diffs if d > 0)
    # normal approximation to the sign test
    z = (pos - n / 2) / math.sqrt(n / 4) if n else 0.0
    return {"n": n, "mean_diff_r": round(m, 5),
            "paired_t": round(m / (sd / math.sqrt(n)), 3) if sd > 0 else None,
            "wins": pos, "sign_z": round(z, 3)}


def slicing_bias(s1: dict) -> dict:
    """How much the ledger-slice approximation differs from a true windowed run.

    Measured on stage 1's random subsample rather than inherited from
    RANKING_FINDINGS' -0.004R audit, because that audit was on a different
    substrate, a different session rule and a different population.
    """
    v = s1.get("slicing_verification") or {}
    ds, dn = [], []
    for sid, d in v.items():
        for win, tk, sk, nk in (("IS", "true_IS", "sliced_IS_exp", "sliced_IS_n"),
                                ("OOS", "true_OOS", "sliced_OOS_exp", "sliced_OOS_n")):
            t = d[tk]
            if t.get("trades", 0) >= 5 and d[nk] >= 5:
                ds.append((d[sk] - t["expectancy_r"], win))
                dn.append((d[nk] - t["trades"], win))
    out = {"n_checked": len(v)}
    for win in ("IS", "OOS"):
        e = [x for x, w in ds if w == win]
        c = [x for x, w in dn if w == win]
        out[win] = {
            "pairs": len(e),
            "mean_exp_r_sliced_minus_true": round(sum(e) / len(e), 5) if e else None,
            "max_abs_exp_diff": round(max(abs(x) for x in e), 5) if e else None,
            "mean_trade_count_diff": round(sum(c) / len(c), 3) if c else None,
        }
    return out


def analyse(sym: str, tag: str = "gap") -> dict:
    s1 = json.loads((OUT / f"stage1_{sym}_{tag}.json").read_text())
    LP = json.loads((OUT / f"ledger_placebo_{sym}_{tag}.json").read_text())
    n_bars = s1["bars"]
    cut = s1["is_cut"]
    real = s1["ledger"]
    plac = LP["ledger"]
    meta = LP["meta"]
    pop_n = s1["population"]
    ft = free_t(pop_n)

    # --- placebo metrics, keyed by (base_id, kind)
    pl_by_base: Dict[str, Dict[str, dict]] = defaultdict(dict)
    for pid, m in meta.items():
        rows = plac.get(pid, [])
        pl_by_base[m["base_id"]][m["kind"]] = {
            "placebo_id": pid,
            "IS": wmetrics(rows, 0, cut), "OOS": wmetrics(rows, cut, n_bars),
            "FULL": wmetrics(rows, 0, n_bars),
            "n_scheduled": m["n_scheduled"], "n_real_signals": m["n_real_signals"],
        }

    # --- window metrics for every live row, from the one full-span ledger
    W = {sid: {"IS": wmetrics(rows, 0, cut), "OOS": wmetrics(rows, cut, n_bars),
               "FULL": wmetrics(rows, 0, n_bars)}
         for sid, rows in real.items()}

    # --- candidates: gates G1 + G2 on IS
    cands = [sid for sid in W
             if W[sid]["IS"].get("trades", 0) >= MIN_IS_TRADES
             and (W[sid]["IS"].get("expectancy_r") or -1) > 0]
    cands.sort(key=lambda sid: -W[sid]["IS"]["expectancy_r"])

    def row_for(sid: str, rank: int) -> dict:
        r = s1["rows"][sid]
        rows = real.get(sid, [])
        pl = pl_by_base.get(sid, {})
        d = {
            "rank_IS": rank, "strategy_id": sid, "name": r["name"],
            "group": r["group"], "primary_tf": r["primary_tf"],
            "confirm_tfs": r["confirm_tfs"], "rth_only": r["rth_only"],
            "stop_kind": r["stop_kind"], "stop_mult": r["stop_mult"],
            "target_kind": r["target_kind"], "n_signals": r["n_signals"],
            "signals": r["signals"], "filters": r["filters"],
            "IS": W[sid]["IS"], "OOS": W[sid]["OOS"], "FULL": W[sid]["FULL"],
            "IS_strict": wmetrics(rows, 0, cut, strict=True),
            "by_session_FULL": slice_by(rows, 0, n_bars, 9),
            "by_regime_FULL": slice_by(rows, 0, n_bars, 10),
            "by_volatility_FULL": slice_by(rows, 0, n_bars, 11),
            "search_size": pop_n, "free_t_faced": round(ft, 3),
            "sharpe_needed": round(ft / math.sqrt(SPAN_YEARS), 3),
            "placebo": {k: {"IS_exp_r": v["IS"].get("expectancy_r"),
                            "IS_trades": v["IS"].get("trades", 0),
                            "OOS_exp_r": v["OOS"].get("expectancy_r"),
                            "OOS_trades": v["OOS"].get("trades", 0),
                            "FULL_exp_r": v["FULL"].get("expectancy_r")}
                        for k, v in pl.items()},
        }
        hp = [pl.get(k, {}).get("IS", {}).get("expectancy_r")
              for k in ("placebo_random", "placebo_shuffle")]
        d["G3_beats_both_honest_placebos"] = (
            all(x is not None for x in hp)
            and all(W[sid]["IS"]["expectancy_r"] > x for x in hp))
        d["G4_oos"] = (W[sid]["OOS"].get("trades", 0) >= MIN_OOS_TRADES
                       and (W[sid]["OOS"].get("expectancy_r") or -1) > 0)
        d["t_clears_free_t"] = ((W[sid]["FULL"].get("t_stat") or 0) >= ft)
        return d

    top = [row_for(sid, i + 1) for i, sid in enumerate(cands[:40])]

    # --- placebos ranked BESIDE the reals, the RANKING_FINDINGS measurement
    pool = []
    for sid in cands:
        pool.append(("real", sid, W[sid]["IS"]["expectancy_r"]))
    for bid, kinds in pl_by_base.items():
        for kind, v in kinds.items():
            if v["IS"].get("trades", 0) >= MIN_IS_TRADES and v["IS"].get("expectancy_r") is not None:
                pool.append((kind, v["placebo_id"], v["IS"]["expectancy_r"]))
    pool.sort(key=lambda x: -x[2])
    honest = [p for p in pool if p[0] in ("real", "placebo_random", "placebo_shuffle")]
    n_tot = len(honest)
    n_pl = sum(1 for p in honest if p[0] != "real")
    best_pl_rank = next((i + 1 for i, p in enumerate(honest) if p[0] != "real"), None)
    placebo_in_top10 = sum(1 for p in honest[:10] if p[0] != "real")
    e_best = (n_tot + 1) / (n_pl + 1) if n_pl else None

    # --- paired real vs placebo, IS and OOS
    paired = {}
    for kind in ("placebo_random", "placebo_shuffle", "placebo_shift"):
        for win in ("IS", "OOS"):
            ds = []
            for sid in cands:
                v = pl_by_base.get(sid, {}).get(kind)
                if not v or v[win].get("trades", 0) < 5:
                    continue
                rr = W[sid][win].get("expectancy_r")
                if rr is None:
                    continue
                ds.append(rr - v[win]["expectancy_r"])
            paired[f"{kind}|{win}"] = paired_sign_and_t(ds)

    # --- walk-forward, anchored, from the ledger
    cuts = [int(n_bars * c) for c in FOLD_CUTS]
    folds = []
    for k in range(len(cuts) - 1):
        tr_hi, te_hi = cuts[k], cuts[k + 1]
        qual = []
        for sid, rows in real.items():
            m = wmetrics(rows, 0, tr_hi)
            if m.get("trades", 0) >= MIN_IS_TRADES and m["expectancy_r"] > 0:
                qual.append((sid, m["expectancy_r"]))
        qual.sort(key=lambda x: -x[1])
        sel = [sid for sid, _ in qual[:10]]
        def pooled(ids):
            rs = [t[2] for sid in ids for t in real.get(sid, [])
                  if tr_hi <= t[0] < te_hi]
            return (round(sum(rs) / len(rs), 5), len(rs)) if rs else (None, 0)
        sel_r, sel_n = pooled(sel)
        uni_r, uni_n = pooled([sid for sid, _ in qual])
        all_r, all_n = pooled(list(real))
        pids = [v["placebo_id"] for b in pl_by_base.values() for v in b.values()]
        pl_rs = [t[2] for pid in pids for t in plac.get(pid, []) if tr_hi <= t[0] < te_hi]
        folds.append({
            "fold": k + 1, "train_bars": [0, tr_hi], "test_bars": [tr_hi, te_hi],
            "n_qualifying_train": len(qual),
            "selected_top10_test_exp_r": sel_r, "selected_test_trades": sel_n,
            "qualifying_universe_test_exp_r": uni_r, "universe_test_trades": uni_n,
            "whole_live_population_test_exp_r": all_r, "population_test_trades": all_n,
            "placebo_cohort_test_exp_r": (round(sum(pl_rs) / len(pl_rs), 5)
                                          if pl_rs else None),
            "placebo_test_trades": len(pl_rs),
            "selection_beat_universe": (sel_r is not None and uni_r is not None
                                        and sel_r > uni_r),
            "top1_train": qual[0][0] if qual else None,
        })

    return {
        "symbol": sym, "tag": tag, "population": pop_n,
        "live": s1["live"], "census_dead": s1["census_dead"],
        "free_t": round(ft, 3), "span_years": round(SPAN_YEARS, 3),
        "sharpe_needed_for_free_t": round(ft / math.sqrt(SPAN_YEARS), 3),
        "is_cut_bar": cut, "bars": n_bars,
        "engine_counters": s1["engine_counters"], "forced_flats": s1["forced_flats"],
        "violations_stage1": s1["violations"],
        "census_falsification": s1["census_falsification"],
        "zero_trade_live_full": s1["zero_trade_live_full"],
        "n_candidates_after_G1_G2": len(cands),
        "placebo_diag": LP["diag"],
        "slicing_verification": slicing_bias(s1),
        "placebo_ranking": {
            "n_honest_pool": n_tot, "n_placebos_in_pool": n_pl,
            "placebo_share": round(n_pl / n_tot, 3) if n_tot else None,
            "best_placebo_rank": best_pl_rank,
            "E_best_placebo_rank_under_null": round(e_best, 2) if e_best else None,
            "placebos_in_top10": placebo_in_top10,
            "expected_placebos_in_top10": round(10 * n_pl / n_tot, 2) if n_tot else None,
            "top10_kinds": [p[0] for p in honest[:10]],
        },
        "paired_real_minus_placebo": paired,
        "walk_forward": folds,
        "top": top,
    }


if __name__ == "__main__":
    tag = "gap"
    out = {}
    for sym in [a for a in sys.argv[1:] if not a.startswith("--")] or ["MES", "MNQ"]:
        out[sym] = analyse(sym, tag)
        (OUT / f"rank_{sym}_{tag}.json").write_text(json.dumps(out[sym], indent=1))
        d = out[sym]
        print(f"=== {sym}: pop {d['population']} live {d['live']} dead {d['census_dead']} "
              f"free_t {d['free_t']} candidates {d['n_candidates_after_G1_G2']}")
        print("   placebo ranking:", json.dumps(d['placebo_ranking']))
        print("   paired:", json.dumps(d['paired_real_minus_placebo']))
        for f in d['walk_forward']:
            print(f"   fold {f['fold']}: sel {f['selected_top10_test_exp_r']} "
                  f"univ {f['qualifying_universe_test_exp_r']} "
                  f"pop {f['whole_live_population_test_exp_r']} "
                  f"plc {f['placebo_cohort_test_exp_r']} beat={f['selection_beat_universe']}")
