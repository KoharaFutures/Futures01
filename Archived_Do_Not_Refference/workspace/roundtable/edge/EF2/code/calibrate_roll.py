"""EF2: what is the false-positive rate of EF6's forward roll on pure noise?

A forward roll that says "top-k beat both universe and null" on a ledger with no
structure at all is not a forward roll, and the failure would be invisible: this
programme's headline prior finding is that selecting was WORSE than not selecting,
so a roll biased the other way would look like a discovery.

Method. Build synthetic ledgers with EXACTLY the shape EF2 emits - same span, same
strategy count, same trade-count distribution, same 18:00->16:00 cycle structure -
and R drawn i.i.d. mean-zero. Any strategy ranking above another is pure sampling
noise by construction, so the correct answer is "no selection edge", every time.
Then count how often ``forward.roll`` reports otherwise.

This is a known-answer test on somebody else's module, which is the only way to
know whether its verdict line means anything. It costs nothing and it is the
check R3's pairing design calls for: run the configuration whose true answer you
already know through the harness FIRST.
"""
from __future__ import annotations

import json
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone
from typing import Dict, List

REPO = "/home/user/Futures01"
for p in (REPO, os.path.join(REPO, "workspace", "roundtable", "edge", "EF6", "code"),
          os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

import forward as FW                                           # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")
ET = timezone(timedelta(hours=-4))
T0 = datetime(2024, 10, 6, 19, 0, tzinfo=ET).timestamp()
T1 = datetime(2026, 9, 25, 16, 0, tzinfo=ET).timestamp()


def synth(seed: int, n_strat: int, lo: int, hi: int, mean: float = 0.0,
          sd: float = 1.0) -> dict:
    rng = random.Random(seed)
    strat: Dict[str, dict] = {}
    for k in range(n_strat):
        n = rng.randint(lo, hi)
        tr = []
        for _ in range(n):
            e = rng.uniform(T0, T1 - 6 * 3600)
            tr.append([e, e + 3600 * rng.randint(1, 6),
                       rng.choice([1, -1]), rng.gauss(mean, sd)])
        tr.sort()
        strat[f"arm{k}"] = {
            "meta": {"stop": rng.choice(["ATR", "STRUCTURE", "VWAP_BAND"]),
                     "target": rng.choice(["R_MULTIPLE", "ANCHOR_ATR"])},
            "trades": tr}
    return {"symbol": "SYN", "setting": f"noise:seed{seed}", "base_tf": 60,
            "substrate": "synthetic mean-zero", "screened": 5092,
            "t0": T0, "t1": T1, "strategies": strat}


def main(draws: int = 40) -> None:
    rows: List[dict] = []
    for sd_i in range(draws):
        doc = synth(1000 + sd_i, n_strat=300, lo=5, hi=150)
        led = FW.Ledger(doc)
        res = FW.roll(led, lookback_days=180, trade_days=60, floor=20, k=10,
                      criterion="expectancy", nperm=200, seed=23)
        rows.append({
            "seed": 1000 + sd_i,
            "topk_exp_r": res["topk_exp_r"],
            "universe_exp_r": res["universe_exp_r"],
            "randomk_exp_r": res["randomk_exp_r"],
            "null_exp_r": res["null_exp_r"],
            "z_vs_null": res["z_vs_null"],
            "edge_vs_universe": res["selection_edge_vs_universe_r"],
            "edge_vs_randomk": res["selection_edge_vs_randomk_r"],
            "folds_traded": res["folds_traded"],
            "oos_trades": res["oos_trades"],
        })
        sys.stderr.write(f"draw {sd_i+1}/{draws} z={res['z_vs_null']}\n")
        sys.stderr.flush()

    def fin(xs):
        return [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]

    z = fin([r["z_vs_null"] for r in rows])
    eu = fin([r["edge_vs_universe"] for r in rows])
    er = fin([r["edge_vs_randomk"] for r in rows])
    summary = {
        "draws": len(rows),
        "true_answer": "no selection edge - R is i.i.d. mean-zero by construction",
        "mean_z_vs_null": sum(z) / len(z) if z else None,
        "share_z_gt_1.96": sum(1 for x in z if x > 1.96) / len(z) if z else None,
        "share_z_lt_-1.96": sum(1 for x in z if x < -1.96) / len(z) if z else None,
        "mean_edge_vs_universe_r": sum(eu) / len(eu) if eu else None,
        "share_edge_vs_universe_positive": (
            sum(1 for x in eu if x > 0) / len(eu) if eu else None),
        "mean_edge_vs_randomk_r": sum(er) / len(er) if er else None,
        "share_edge_vs_randomk_positive": (
            sum(1 for x in er if x > 0) / len(er) if er else None),
        "share_beating_BOTH_universe_and_null": (
            sum(1 for r in rows
                if (r["edge_vs_universe"] or 0) > 0 and (r["z_vs_null"] or 0) > 1.96)
            / len(rows)),
    }
    with open(os.path.join(OUT, "calibrate_roll.json"), "w") as fh:
        json.dump({"summary": summary, "rows": rows}, fh, indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
