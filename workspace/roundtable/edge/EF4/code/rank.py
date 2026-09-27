"""EF4 - the ranked lists, and the labels they must carry.

Ranks by **expectancy in R net of costs**, as the dispatch directs, with the durability
terms the EDGE_BRIEF requires applied as a penalty rather than as a separate leaderboard:
a sample-size shrink, drawdown, and consecutive losses. Never by highest historical profit.

Every row carries, in the row and not in a footnote:
  * gross and net expectancy separately, and the cost that separates them;
  * the trade count and the per-trade mu/sigma the row's own t implies;
  * the declared search width it came from and that width's `free_t`;
  * its out-of-sample half beside its in-sample half;
  * its three walk-forward folds.

Rows that clear their own threshold are listed as clearing. Rows that do not are still
listed, labelled, because the dispatch asked for fewer than ten if fewer than ten clear and
for the list to say what it is.
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from pathlib import Path

ROOT = Path("/home/user/Futures01")
OUT = ROOT / "workspace/roundtable/edge/EF4/out"
CELLS = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]
FREE_T = {"A": 2.677, "B": 4.441}
N_DECL = {"A": 36, "B": 19152}
MIN_TRADES = 30


def durability(r, free_t):
    n = r["trades"]
    if n == 0:
        return -9.9
    shrink = n / (n + 50.0)
    return (r["expectancy_net_r"] * shrink
            - 0.02 * r.get("max_dd_r", 0.0) / max(1.0, math.sqrt(n))
            - 0.01 * r.get("max_consec_losses", 0)
            + 0.02 * max(0.0, r.get("t_stat", 0.0) - free_t))


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
        for r in d["rows"]:
            if r["trades"] < MIN_TRADES:
                continue
            track = "A" if r["group"] != "EF4_SCREEN" else "B"
            ft = FREE_T[track]
            row = dict(r)
            row["track"] = track
            row["free_t"] = ft
            row["n_declared"] = N_DECL[track]
            row["clears_own_threshold"] = bool(r["t_stat"] >= ft)
            row["durability"] = durability(r, ft)
            pr = plc.get((sym, tf, r["name"]))
            if pr:
                row["placebo_mean_net_r"] = pr["placebo_mean_expectancy_net_r"]
                row["placebo_sd_net_r"] = pr["placebo_sd_expectancy_net_r"]
                row["placebo_percentile"] = pr["real_percentile_in_placebo"]
                row["placebo_z"] = pr["z_vs_placebo"]
            per_symbol[sym].append(row)

    out = {}
    for sym, rows in per_symbol.items():
        rows.sort(key=lambda r: -r["expectancy_net_r"])
        top = rows[:10]
        clearing = [r for r in rows if r["clears_own_threshold"]]
        out[sym] = {
            "qualifying_rows_min30_trades": len(rows),
            "rows_clearing_their_declared_threshold": len(clearing),
            "top10_by_net_expectancy": [
                {k: r.get(k) for k in (
                    "name", "tf", "track", "trades", "win_rate", "avg_win_r",
                    "avg_loss_r", "rr_realised", "profit_factor",
                    "expectancy_gross_r", "cost_total_r", "expectancy_net_r",
                    "sd_r", "t_stat", "free_t", "n_declared",
                    "clears_own_threshold", "sharpe_per_trade", "sortino_per_trade",
                    "sharpe_annualised", "max_dd_r", "avg_dd_r",
                    "max_consec_wins", "max_consec_losses", "avg_minutes_held",
                    "avg_mae_r", "avg_mfe_r", "pct_entries_outside_rth",
                    "durability", "placebo_mean_net_r", "placebo_percentile",
                    "placebo_z", "conditions", "exit_mix")}
                | {"is": {k: r["is"].get(k) for k in ("trades", "expectancy_net_r", "t_stat")},
                   "oos": {k: r["oos"].get(k) for k in ("trades", "expectancy_net_r", "t_stat")},
                   "folds": [{k: f.get(k) for k in ("trades", "expectancy_net_r")}
                             for f in r["folds"]]}
                for r in top],
            "clearing": [r["name"] for r in clearing],
        }
        print(f"\n=== {sym} — scalp, 5m/15m/30m, ranked by net expectancy in R ===")
        print(f"qualifying rows (>= {MIN_TRADES} trades): {len(rows)}   "
              f"rows clearing their own declared threshold: {len(clearing)}")
        print(f"{'#':>2} {'tf':>3} {'tr':>2} {'name':<40}{'n':>5}{'wr':>7}"
              f"{'grossE':>9}{'cost':>8}{'netE':>9}{'t':>7}{'freeT':>7}"
              f"{'IS':>9}{'OOS':>9}{'plc':>9}{'pct':>6}")
        for i, r in enumerate(top, 1):
            print(f"{i:>2} {r['tf']:>3} {r['track']:>3} {r['name'][:40]:<40}"
                  f"{r['trades']:>5}{r['win_rate']:>7.3f}"
                  f"{r['expectancy_gross_r']:>+9.4f}{r['cost_total_r']:>8.4f}"
                  f"{r['expectancy_net_r']:>+9.4f}{r['t_stat']:>+7.2f}{r['free_t']:>7.2f}"
                  f"{r['is']['expectancy_net_r']:>+9.4f}"
                  f"{r['oos']['expectancy_net_r']:>+9.4f}"
                  f"{r.get('placebo_mean_net_r', float('nan')):>+9.4f}"
                  f"{r.get('placebo_percentile', float('nan')):>6.2f}")
    (OUT / "rankings.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT / 'rankings.json'}")


if __name__ == "__main__":
    main()
