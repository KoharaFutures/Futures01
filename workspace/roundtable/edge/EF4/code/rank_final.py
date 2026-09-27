"""EF4 - the honest ranked list: de-duplicated by signal set, OOS beside IS, placebo beside both.

Why de-duplication comes before ranking, and why it changes the answer. Inspecting the raw
top 10 per cell shows it is **one or two conditions wearing ten names**: MGC 30m's top 10
contains `imbalance_pullback` in 9 of 10 rows; MGC 15m's contains `candle_engulfing` in 8 of 10.
The ten rows differ only in which filter is bolted on, so they share most of their trades. The
ORB/ICT report already named this failure mode - *"a league table of the best rule sets
containing a condition measures the search, not the condition"* - and a top-10 list that does
not collapse it reports ten rows of which one or two are independent.

So: group every qualifying arm by its **signal set** (filters excluded), keep the variant with
the largest out-of-sample trade count, and rank the groups. The count of surviving groups is the
honest answer to "how many rows are there", and it is far below ten.

Ranking is by **net expectancy in R** with the EDGE_BRIEF's durability terms as a penalty.
Promotion requires, all four:
  1. >= 30 trades in BOTH halves (the sample floor every prior study here used);
  2. the same SIGN in-sample and out-of-sample (a sign flip is a failure, and a finding);
  3. positive in all three walk-forward folds that reach 10 trades;
  4. t on the full R series >= the declared free_t of its own track.
Rows failing (4) are still listed, labelled, because the dispatch asked for the list to say
what it is rather than for ten rows.
"""
from __future__ import annotations

import json
import math
import statistics as st
from pathlib import Path

ROOT = Path("/home/user/Futures01")
OUT = ROOT / "workspace/roundtable/edge/EF4/out"
CELLS = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]
FREE_T = {"A": 2.677, "B": 4.441}
N_DECL = {"A": 36, "B": 19152}
FILTERS = {"volatility_normal", "relative_volume_high", "adx_trending",
           "after_opening_range", "away_from_hvn", "volume_not_thin",
           "volatility_compressed"}


def signal_set(r):
    return tuple(sorted(c for c in r["conditions"] if c not in FILTERS))


def durability(r, ft):
    n = r["trades"]
    if n == 0:
        return -9.9
    return (r["expectancy_net_r"] * n / (n + 50.0)
            - 0.02 * r.get("max_dd_r", 0.0) / max(1.0, math.sqrt(n))
            - 0.01 * r.get("max_consec_losses", 0)
            + 0.02 * max(0.0, r.get("t_stat", 0.0) - ft))


def main() -> None:
    plc = {}
    for sym, tf in CELLS:
        p = OUT / f"placebo_{sym}_{tf}m.json"
        if p.is_file():
            for r in json.loads(p.read_text())["rows"]:
                plc[(sym, tf, r["name"])] = r

    per_symbol = {"MGC": [], "MCL": []}
    for sym, tf in CELLS:
        p = OUT / f"run_{sym}_{tf}m_both.json"
        if not p.is_file():
            continue
        d = json.loads(p.read_text())
        groups = {}
        for r in d["rows"]:
            if r["trades"] < 30 or r["is"]["trades"] < 30 or r["oos"]["trades"] < 30:
                continue
            k = (tf, signal_set(r))
            cur = groups.get(k)
            if cur is None or r["oos"]["trades"] > cur["oos"]["trades"]:
                groups[k] = r
        for (tf_, sigs), r in groups.items():
            track = "A" if r["group"] != "EF4_SCREEN" else "B"
            ft = FREE_T[track]
            folds = [f for f in r["folds"] if f["trades"] >= 10]
            row = {
                "symbol": sym, "tf": tf_, "signals": list(sigs), "name": r["name"],
                "track": track, "n_declared": N_DECL[track], "free_t": ft,
                "trades": r["trades"], "win_rate": r["win_rate"],
                "avg_win_r": r["avg_win_r"], "avg_loss_r": r["avg_loss_r"],
                "rr_realised": r["rr_realised"], "profit_factor": r["profit_factor"],
                "expectancy_gross_r": r["expectancy_gross_r"],
                "cost_total_r": r["cost_total_r"],
                "cost_commission_r": r["cost_commission_r"],
                "cost_slippage_r": r["cost_slippage_r"],
                "expectancy_net_r": r["expectancy_net_r"],
                "sd_r": r["sd_r"], "t_stat": r["t_stat"],
                "sharpe_per_trade": r["sharpe_per_trade"],
                "sharpe_annualised": r["sharpe_annualised"],
                "sortino_per_trade": r["sortino_per_trade"],
                "max_dd_r": r["max_dd_r"], "avg_dd_r": r["avg_dd_r"],
                "max_consec_wins": r["max_consec_wins"],
                "max_consec_losses": r["max_consec_losses"],
                "avg_minutes_held": r["avg_minutes_held"],
                "avg_mae_r": r["avg_mae_r"], "avg_mfe_r": r["avg_mfe_r"],
                "pct_entries_outside_rth": r["pct_entries_outside_rth"],
                "exit_mix": r["exit_mix"],
                "is_trades": r["is"]["trades"], "is_expectancy_net_r": r["is"]["expectancy_net_r"],
                "oos_trades": r["oos"]["trades"], "oos_expectancy_net_r": r["oos"]["expectancy_net_r"],
                "oos_t_stat": r["oos"]["t_stat"],
                "folds": [{"trades": f["trades"], "expectancy_net_r": f["expectancy_net_r"]}
                          for f in r["folds"]],
                "sign_agrees_is_oos": bool(
                    (r["is"]["expectancy_net_r"] > 0) == (r["oos"]["expectancy_net_r"] > 0)),
                "positive_in_all_usable_folds": bool(
                    folds and all(f["expectancy_net_r"] > 0 for f in folds)),
                "usable_folds": len(folds),
                "clears_own_threshold": bool(r["t_stat"] >= ft),
                "durability": durability(r, ft),
            }
            pr = plc.get((sym, tf_, r["name"]))
            if pr:
                row["placebo_n"] = pr["placebo_n"]
                row["placebo_mean_net_r"] = pr["placebo_mean_expectancy_net_r"]
                row["placebo_sd_net_r"] = pr["placebo_sd_expectancy_net_r"]
                row["placebo_percentile"] = pr["real_percentile_in_placebo"]
                row["placebo_z"] = pr["z_vs_placebo"]
            per_symbol[sym].append(row)

    out = {}
    for sym, rows in per_symbol.items():
        rows.sort(key=lambda r: -r["expectancy_net_r"])
        survivors = [r for r in rows
                     if r["sign_agrees_is_oos"] and r["expectancy_net_r"] > 0
                     and r["positive_in_all_usable_folds"]]
        clearing = [r for r in survivors if r["clears_own_threshold"]]
        out[sym] = {
            "distinct_signal_sets_meeting_the_sample_floor": len(rows),
            "surviving_sign_agreement_and_all_folds": len(survivors),
            "clearing_their_declared_threshold": len(clearing),
            "top_by_net_expectancy": rows[:10],
            "survivors": survivors[:10],
        }
        print(f"\n{'='*118}\n{sym} — SCALP, 5m/15m/30m, de-duplicated by signal set\n{'='*118}")
        print(f"distinct signal sets with >=30 trades in the full sample AND in both halves: "
              f"{len(rows)}")
        print(f"of those, sign-consistent IS/OOS, positive, and positive in every usable fold: "
              f"{len(survivors)}")
        print(f"of those, clearing their own declared free_t: {len(clearing)}")
        print(f"\n{'tf':>3} {'tr':>2} {'signals':<44}{'n':>5}{'wr':>6}{'grossE':>9}"
              f"{'cost':>7}{'netE':>9}{'t':>6}{'freeT':>6}{'ISn':>5}{'ISE':>8}"
              f"{'OOSn':>5}{'OOSE':>8}{'folds (E)':>26}")
        for r in rows[:12]:
            fs = " ".join(f"{f['expectancy_net_r']:+.2f}/{f['trades']}" for f in r["folds"])
            mark = "  <-- survives" if r in survivors else ""
            print(f"{r['tf']:>3} {r['track']:>2} {','.join(r['signals'])[:44]:<44}"
                  f"{r['trades']:>5}{r['win_rate']:>6.2f}{r['expectancy_gross_r']:>+9.4f}"
                  f"{r['cost_total_r']:>7.4f}{r['expectancy_net_r']:>+9.4f}"
                  f"{r['t_stat']:>+6.2f}{r['free_t']:>6.2f}"
                  f"{r['is_trades']:>5}{r['is_expectancy_net_r']:>+8.3f}"
                  f"{r['oos_trades']:>5}{r['oos_expectancy_net_r']:>+8.3f}{fs:>26}{mark}")
    (OUT / "rank_final.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT / 'rank_final.json'}")


if __name__ == "__main__":
    main()
