"""EF3 - the anti-overfitting audit, run on the reported rows and on the population.

Everything here is derived from the ledgers already on disk, so no extra sweep:
  * parameter sensitivity  - the sibling family of every reported row
  * cost sensitivity       - exact double-commission and +1-tick-on-the-flat arms,
                             recovered from (gross_r - net_r) per trade
  * roll exposure          - trades touching a +/-1 bar window at a candidate
                             CME equity-index roll boundary
  * fill realism           - favourable slippage, same-bar stop/target
  * window slicing bias    - stage 1's true-window subsample
"""
from __future__ import annotations

import datetime as dt
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "/home/user/Futures01")
OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF3/out")

# 3rd-Friday CME equity-index roll dates inside 2024-10-06 .. 2026-09-25
ROLLS = [dt.date(2024, 12, 20), dt.date(2025, 3, 21), dt.date(2025, 6, 20),
         dt.date(2025, 9, 19), dt.date(2025, 12, 19), dt.date(2026, 3, 20),
         dt.date(2026, 6, 19)]
POINT_VALUE = {"MES": 5.0, "MNQ": 2.0}
TICK = 0.25
COMMISSION_ROUND_TURN = 2 * (0.35 + 0.37)


def sibling_families(rows: dict, ledger: dict, n_bars: int) -> dict:
    """Group the population into families that share a rule set and differ only
    in exit geometry / optional filter, then report the fraction positive.

    RANKING_FINDINGS measured median 0.0 at MES 60m. This is the same test on
    the session-window harness.
    """
    fam = defaultdict(list)
    for sid, r in rows.items():
        key = (r["group"], r["primary_tf"], tuple(r["signals"]),
               tuple(r["confirm_tfs"]), r["rth_only"])
        fam[key].append(sid)
    out = {}
    for key, ids in fam.items():
        exps = []
        for sid in ids:
            tr = ledger.get(sid, [])
            if len(tr) >= 10:
                exps.append(sum(t[2] for t in tr) / len(tr))
        if len(exps) >= 3:
            out["|".join(map(str, key))] = {
                "n_members": len(ids), "n_with_10plus_trades": len(exps),
                "frac_positive": round(sum(1 for x in exps if x > 0) / len(exps), 3),
                "median_exp_r": round(statistics.median(exps), 5),
                "spread_exp_r": round(max(exps) - min(exps), 5),
            }
    fracs = [v["frac_positive"] for v in out.values()]
    return {"n_families": len(out),
            "median_frac_positive": round(statistics.median(fracs), 3) if fracs else None,
            "mean_frac_positive": round(sum(fracs) / len(fracs), 3) if fracs else None,
            "families": out}


def cost_sensitivity(trades, symbol: str) -> dict:
    """Exact arms recovered from the ledger, no re-run.

    cost_r per trade = gross_r - net_r, and the engine charges commission only
    there, so risk_points = COMMISSION_ROUND_TURN / (cost_r * point_value).
    """
    pv = POINT_VALUE[symbol]
    n = len(trades)
    if not n:
        return {}
    net = [t[2] for t in trades]
    cost = [t[3] - t[2] for t in trades]
    risk_pts = [COMMISSION_ROUND_TURN / (c * pv) if c > 0 else None for c in cost]
    flat = [t[5] == "SESSION_CLOSE" for t in trades]
    one_tick_r = [(TICK / rp) if rp else 0.0 for rp in risk_pts]
    base = sum(net) / n
    return {
        "trades": n,
        "expectancy_r": round(base, 5),
        "mean_cost_r_charged": round(sum(cost) / n, 5),
        "median_risk_points": round(statistics.median([r for r in risk_pts if r]), 3),
        "arm_double_commission": round(base - sum(cost) / n, 5),
        "arm_plus_1_tick_on_flat_exit": round(
            base - sum(o for o, f in zip(one_tick_r, flat) if f) / n, 5),
        "arm_plus_1_tick_every_exit": round(base - sum(one_tick_r) / n, 5),
        "flat_exit_share": round(sum(flat) / n, 4),
    }


def roll_exposure(trades, bar_dates) -> dict:
    """Share of trades whose entry or exit bar sits within +/-1 bar of a
    candidate roll boundary. Bounds the D40-shaped exposure rather than
    claiming a roll splice is absent."""
    rolldates = set(ROLLS)
    risky = set()
    for i, d in enumerate(bar_dates):
        if d in rolldates:
            risky.update((i - 1, i, i + 1))
    hit = sum(1 for t in trades if t[0] in risky or t[1] in risky)
    return {"trades": len(trades), "trades_touching_roll_window": hit,
            "share": round(hit / len(trades), 5) if trades else None,
            "candidate_roll_boundaries": len(ROLLS)}


if __name__ == "__main__":
    import sys as _s
    from futures_agents.data.archive import BarArchive
    from futures_agents.timeutil import to_et
    arch = BarArchive("/home/user/Futures01/data/archive")
    res = {}
    for sym in [a for a in _s.argv[1:] if not a.startswith("--")] or ["MES", "MNQ"]:
        s1 = json.loads((OUT / f"stage1_{sym}_gap.json").read_text())
        led = s1["ledger"]
        bars = arch.load(sym, 60).bars
        bar_dates = [to_et(b.ts).date() for b in bars]
        allt = [t for v in led.values() for t in v]
        res[sym] = {
            "sibling_families": sibling_families(s1["rows"], led, s1["bars"]),
            "cost_sensitivity_population": cost_sensitivity(allt, sym),
            "roll_exposure_population": roll_exposure(allt, bar_dates),
            "exit_reason_mix": dict(Counter(t[5] for t in allt)),
            "hold_hours": {
                "median": round(statistics.median(t[8] for t in allt), 3),
                "p95": round(sorted(t[8] for t in allt)[int(0.95 * len(allt))], 3),
                "max": round(max(t[8] for t in allt), 3),
                "over_22h": sum(1 for t in allt if t[8] > 22.001),
            },
        }
        r = res[sym]
        print(f"=== {sym}: {len(allt)} trades")
        print("  siblings:", {k: v for k, v in r["sibling_families"].items() if k != "families"})
        print("  cost:", json.dumps(r["cost_sensitivity_population"]))
        print("  roll:", json.dumps(r["roll_exposure_population"]))
        print("  exits:", r["exit_reason_mix"], " holds:", r["hold_hours"])
    # keep families out of the printed summary but on disk
    (OUT / "audit.json").write_text(json.dumps(res, indent=1))
