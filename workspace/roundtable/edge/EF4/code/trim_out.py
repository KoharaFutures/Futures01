"""EF4 - shrink the per-arm dumps to what a reviewer needs, then gzip the rest.

Each `run_<sym>_<tf>m_both.json` is ~21 MB: 2,800-3,600 arms x four metric blocks. The whole
set is ~120 MB, which does not belong uncompressed in a repository. Nothing is deleted: the
full dumps are gzipped in place and a trimmed summary carrying every field any EF4 table or
`FINDINGS.md` claim is computed from is written beside them, so every number remains
reproducible from this directory alone.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF4/out")
KEEP = ("strategy_id", "name", "group", "symbol", "tf", "conditions", "trades", "signals",
        "win_rate", "avg_win_r", "avg_loss_r", "rr_realised", "profit_factor",
        "expectancy_net_r", "expectancy_gross_r", "cost_commission_r", "cost_slippage_r",
        "cost_total_r", "sd_r", "t_stat", "sharpe_per_trade", "sharpe_annualised",
        "sortino_per_trade", "max_dd_r", "avg_dd_r", "max_consec_wins",
        "max_consec_losses", "avg_minutes_held", "avg_mae_r", "avg_mfe_r",
        "sessions_with_a_trade", "pct_entries_outside_rth", "exit_mix")
SLICE_KEEP = ("trades", "expectancy_net_r", "expectancy_gross_r", "t_stat", "win_rate")

for p in sorted(OUT.glob("run_*_both.json")):
    d = json.loads(p.read_text())
    rows = []
    for r in d["rows"]:
        o = {k: r.get(k) for k in KEEP}
        for half in ("is", "oos"):
            o[half] = {k: r[half].get(k) for k in SLICE_KEEP}
        o["folds"] = [{k: f.get(k) for k in SLICE_KEEP} for f in r["folds"]]
        rows.append(o)
    trimmed = {k: v for k, v in d.items() if k != "rows"}
    trimmed["rows"] = rows
    t = p.with_name(p.stem + "_summary.json")
    t.write_text(json.dumps(trimmed, separators=(",", ":")))
    g = p.with_suffix(".json.gz")
    with p.open("rb") as fi, gzip.open(g, "wb", compresslevel=9) as fo:
        fo.writelines(fi)
    p.unlink()
    print(f"{p.name}: summary {t.stat().st_size/1e6:.2f} MB, gz {g.stat().st_size/1e6:.2f} MB")
