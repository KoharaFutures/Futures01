"""End-to-end: build a top 10 the way EF2-EF5 would, then attack every row.

This is the harness EF2-EF5's rows go through, exercised on a real population so
it is demonstrated rather than asserted. Steps:

1. generate, build the `rth_only=False` window arm via `arms.refilter` (D48-safe);
2. **prefilter** against the census - VOID rows never enter the denominator;
3. run under `SessionWindowEngine` (18:00->16:00 enforced);
4. rank in-sample on the durability criterion, take the top 10;
5. build the window-safe placebo cohort for exactly those 10 and run it in the
   SAME pass, with arm-id uniqueness asserted (D48) before and after;
6. run `attack.attack` per row: G1 firing, G2 placebo, G3 threshold, G4 forward.

Usage: python3 run_attack_demo.py SYMBOL BASE_TF TF,TF,TF MAX_TOTAL
"""

from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, "/home/user/Futures01/workspace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np

from futures_agents.data.archive import BarArchive            # noqa: E402
from futures_agents.features import build_symbol_frame        # noqa: E402
from futures_agents.strategies.combinator import generate_strategies  # noqa: E402

import arms                                                   # noqa: E402
import attack as A                                            # noqa: E402
import deflation as D                                         # noqa: E402
import firing                                                 # noqa: E402
import forward as F                                           # noqa: E402
import placebo_w as PW                                        # noqa: E402
from session_engine import SessionWindowEngine                # noqa: E402

OUT = "workspace/roundtable/edge/EF6/out"


def t_stat(rs):
    rs = np.asarray(rs, dtype=float)
    if len(rs) < 2 or rs.std(ddof=1) == 0:
        return 0.0
    return float(rs.mean() / (rs.std(ddof=1) / math.sqrt(len(rs))))


def durability(rs, floor=20):
    rs = np.asarray(rs, dtype=float)
    if len(rs) < 2:
        return -1e9
    n = len(rs)
    return float(rs.mean() * (n / (n + floor)) / (1.0 + rs.std(ddof=1)))


def main() -> int:
    sym, base, tfs, mt = sys.argv[1], int(sys.argv[2]), sys.argv[3], int(sys.argv[4])
    tfs = [int(x) for x in tfs.split(",")]
    tag = f"{sym}_{base}m_frame{'-'.join(str(t) for t in tfs)}"
    census_path = os.path.join(OUT, "census", f"census_{tag}.json")
    doc = firing.load_census(census_path)

    arch = BarArchive("data/archive")
    series = arch.load(sym, base)
    frame = build_symbol_frame(series, tfs)

    gen = [s for s in generate_strategies(sym, tfs, max_total=mt)
           if s.primary_tf == base]
    win = [arms.refilter(s, rth_only=False) for s in gen]
    arms.assert_unique(win, labels=["window_arm"])
    keep, audit_rows = firing.prefilter(win, doc)
    pf = firing.audit_summary(audit_rows)
    print(f"generated {len(gen)} -> prefilter removed {pf['n_void']} VOID "
          f"({pf['pct_void']}%) -> screened {len(keep)}")
    print("  causes:", pf["void_causes"])

    eng = SessionWindowEngine(frame)
    res = eng.run_many(keep)
    arms.arm_report(res, keep, labels=["real"])
    by_id = {s.strategy_id: s for s in keep}

    # ---- rank in-sample, exactly as a top 10 would be produced -------------
    FLOOR = 20
    rows = []
    for sid, r in res.items():
        rs = [t.net_r for t in r.trades]
        if len(rs) < FLOOR:
            continue
        rows.append((durability(rs, FLOOR), sid, rs, r.trades))
    rows.sort(key=lambda x: -x[0])
    top = rows[:10]
    print(f"\nqualifiers at floor {FLOOR}: {len(rows)}; reporting top {len(top)}")
    if len(rows) <= 10:
        print("  *** the top 10 IS the whole qualifying universe - no selection "
              "took place ***")

    # ---- placebo cohort for exactly those rows ----------------------------
    bases = [by_id[sid] for _, sid, _, _ in top]
    realised = {sid: len(rs) for _, sid, rs, _ in top}
    # median realised hold in BASE bars, so the control's entries are separated
    # the way the base's own positions were and the engine's culling has nothing
    # left to remove. Without this the placebo overshoots the base 2-3x.
    holds = {sid: int(np.median([t.bars_held for t in tr]) if tr else 0)
             for _, sid, _, tr in top}
    plc, meta, diag = PW.build_cohort(frame, bases, realised, hold_bars=holds)
    arms.assert_unique(bases, plc, labels=["real_top10", "placebos"])
    print("\nplacebo cohort:", json.dumps(diag))
    pres = SessionWindowEngine(frame).run_many(plc)
    arms.arm_report(pres, bases, plc, labels=["real_top10", "placebos"])

    by_base_kind = {}
    for pid, m in meta.items():
        by_base_kind.setdefault(m.base_id, {})[m.kind] = pid

    # ---- forward roll on the same population ------------------------------
    ledger = {"symbol": sym, "setting": "swing" if base >= 60 else "scalp",
              "base_tf": base, "substrate": "data/archive",
              "screened": len(keep),
              "t0": series.bars[0].ts.timestamp(),
              "t1": series.bars[-1].ts.timestamp(), "strategies": {}}
    for s in keep:
        r = res.get(s.strategy_id)
        if r is None or not r.trades:
            continue
        ledger["strategies"][s.strategy_id] = {
            "meta": {"group": s.group, "primary_tf": s.primary_tf,
                     "stop": s.exit.label.split("->")[0], "target": s.exit.label},
            "trades": [[t.entry_ts.timestamp(), t.exit_ts.timestamp(),
                        t.direction.sign, t.net_r] for t in r.trades]}
    roll = F.roll(F.Ledger(ledger), lookback_days=180, trade_days=30,
                  floor=FLOOR, k=10, criterion="durability", nperm=80)
    print("\n" + F.roll_report(roll))

    # ---- attack every row -------------------------------------------------
    print("\n" + "=" * 100)
    print("ATTACK: every row that reached the top 10")
    print("=" * 100)
    report = []
    for rank, (key, sid, rs, trades) in enumerate(top, 1):
        s = by_id[sid]
        kinds = by_base_kind.get(sid, {})
        pk = kinds.get("placebo_random_legal") or kinds.get("placebo_session_shuffle")
        ptr = pres.get(pk).trades if pk and pres.get(pk) else []
        row = {"id": f"#{rank} {sid}", "strategy": s, "census": doc,
               "base_trades": [(t.entry_ts, t.net_r) for t in trades],
               "placebo_trades": [(t.entry_ts, t.net_r) for t in ptr],
               "t": t_stat(rs), "n_screened": len(keep), "symbol": sym,
               "timeframes": tfs, "roll": roll}
        out = A.attack(row)
        wins = sum(1 for r_ in rs if r_ > 0)
        print(f"\n#{rank} {sid}  {s.group:<16} n={len(rs)}  "
              f"exp={np.mean(rs):+.4f}R  win={wins/len(rs):.1%}  "
              f"avg_win={np.mean([x for x in rs if x>0]) if wins else 0:+.3f}R  "
              f"avg_loss={np.mean([x for x in rs if x<=0]) if wins<len(rs) else 0:+.3f}R  "
              f"t={row['t']:+.3f}  durability_key={key:+.5f}")
        for g in out["gates"]:
            extra = ""
            if g["gate"] == "G2 PLACEBO":
                extra = (f" base {g['count_match']['base_trades']} vs placebo "
                         f"{g['count_match']['placebo_trades']} trades, "
                         f"diff {g['permutation'].get('observed_diff')}R, "
                         f"p={g['permutation'].get('p_two_sided')}, "
                         f"MDD {g['min_detectable_diff_R_at_80pct_power']}R")
            if g["gate"] == "G1 FIRING":
                extra = f" min_fires={g['min_fires']} void={g['void_conditions']}"
            if g["gate"] == "G3 THRESHOLD":
                extra = (f" t={g['t_observed']} vs free_t({g['n_screened']})="
                         f"{g['threshold_t']} -> needs ann. Sharpe "
                         f"{g['required_annual_sharpe']} (implied {g['implied_annual_sharpe']})")
            print(f"    {g['gate']:<14} {g['verdict']:<14} "
                  f"{'PASS' if g['pass'] else 'FAIL'}{extra}")
        print(f"    => {out['verdict']}   killed by: {out['killed_by'] or 'nothing'}")
        report.append({k: v for k, v in out.items() if k != "gates"} |
                      {"gates": [{kk: vv for kk, vv in g.items()
                                  if kk not in ("welch",)} for g in out["gates"]],
                       "rank": rank, "strategy_id": sid, "group": s.group,
                       "trades": len(rs), "expectancy_r": round(float(np.mean(rs)), 4),
                       "win_rate": round(wins / len(rs), 4)})

    with open(os.path.join(OUT, f"attack_{tag}.json"), "w") as fh:
        json.dump({"prefilter": pf, "placebo_diag": diag, "roll": roll,
                   "rows": report}, fh, indent=1, default=str)
    print("\nwritten", os.path.join(OUT, f"attack_{tag}.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
