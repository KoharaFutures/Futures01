"""EF4 - a placebo beside every row that is reported.

For each named arm, k count-matched random-bar placebos are built with
``placebo.make_placebo`` and run through the arm's OWN exit, filters and sizing, in the same
``SessionWindowEngine`` on the same frame. The arm and its placebos go through
``run_many`` in ONE pass, so they see identical bars, identical slippage state and identical
one-position-at-a-time attrition.

Reported per arm: the real net expectancy, the placebo mean and sd, the arm's percentile in
its own placebo distribution, and a z against the placebo distribution. A row whose
percentile is not extreme is a row the placebo reproduces, which the programme has already
seen five separate times.

`_id=None` on every construction (D48); ids asserted distinct across the real arm and all
placebos before the run - a collision there would make the arm and its own control the same
`BacktestResult` and the difference exactly zero.

Usage: python3 run_placebo.py MGC 30 [--k 20]
"""
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF1/code"))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF4/code"))

from futures_agents.backtest.costs import CostModel          # noqa: E402
from futures_agents.config import get_contract               # noqa: E402
from futures_agents.schema import Direction                  # noqa: E402
from session_window import SessionWindowEngine               # noqa: E402
from placebo import make_placebo                             # noqa: E402
from population import assert_unique, build_track_a, build_track_b  # noqa: E402
from run_cell import frame_for, metrics                      # noqa: E402

OUT = ROOT / "workspace/roundtable/edge/EF4/out"


def main() -> None:
    sym, tf = sys.argv[1], int(sys.argv[2])
    k = 20
    for i, a in enumerate(sys.argv):
        if a == "--k":
            k = int(sys.argv[i + 1])
    spec = get_contract(sym)
    cost = CostModel(spec)
    frame = frame_for(sym, tf)
    n_bars = len(frame.base)

    # Which arms get a placebo: all of Track A, plus the top 15 screen arms by net
    # expectancy at >= 30 trades (the rows that could plausibly be reported).
    run_path = OUT / f"run_{sym}_{tf}m_both.json"
    prior = json.loads(run_path.read_text())
    by_name = {r["name"]: r for r in prior["rows"]}
    a_arms = build_track_a(sym, tf)
    screen = sorted((r for r in prior["rows"]
                     if r["group"] == "EF4_SCREEN" and r["trades"] >= 30),
                    key=lambda r: -r["expectancy_net_r"])[:15]
    want = {r["name"] for r in screen}
    b_arms = [s for s in build_track_b(sym, tf) if s.name in want]
    arms = a_arms + b_arms

    everything = list(arms)
    plc_of = {}
    for s in arms:
        row = by_name.get(s.name)
        if row is None or row["trades"] == 0:
            continue
        n_sig = max(1, row.get("signals") or row["trades"])
        # realised long share, so the control is matched on direction too
        long_share = 0.5
        ps = [make_placebo(s, n_bars=n_bars, n_signals=n_sig,
                           long_share=long_share, seed=1000 + j) for j in range(k)]
        plc_of[s.strategy_id] = [p.strategy_id for p in ps]
        everything += ps
    assert_unique(everything, f"placebo {sym} {tf}m")

    eng = SessionWindowEngine(frame, cost)
    res = eng.run_many(everything)

    rows = []
    for s in arms:
        r = res.get(s.strategy_id)
        if r is None:
            continue
        real = metrics(r, spec, cost)
        pids = plc_of.get(s.strategy_id, [])
        pl = [metrics(res[p], spec, cost) for p in pids if p in res]
        pl = [m for m in pl if m["trades"] > 0]
        if pl:
            es = [m["expectancy_net_r"] for m in pl]
            mu, sd = st.mean(es), (st.pstdev(es) if len(es) > 1 else 0.0)
            beat = sum(1 for e in es if real.get("expectancy_net_r", 0) > e)
            pct = beat / len(es)
            z = ((real["expectancy_net_r"] - mu) / sd) if sd > 0 else 0.0
        else:
            mu = sd = pct = z = 0.0
        rows.append({
            "symbol": sym, "tf": tf, "name": s.name, "group": s.group,
            "conditions": [c.name for c in s.conditions],
            "real": real,
            "placebo_n": len(pl),
            "placebo_mean_expectancy_net_r": mu,
            "placebo_sd_expectancy_net_r": sd,
            "placebo_mean_trades": st.mean([m["trades"] for m in pl]) if pl else 0,
            "real_percentile_in_placebo": pct,
            "z_vs_placebo": z,
        })
    p = OUT / f"placebo_{sym}_{tf}m.json"
    p.write_text(json.dumps({"symbol": sym, "tf": tf, "k": k,
                             "arms": len(arms), "rows": rows}, indent=2))
    print(f"{sym} {tf}m: {len(arms)} arms x {k} placebos")
    for r in sorted(rows, key=lambda x: -x["real"].get("expectancy_net_r", -9)):
        rr = r["real"]
        print(f"  {r['name'][:46]:<46} n={rr.get('trades',0):<4} "
              f"netE={rr.get('expectancy_net_r',0):+.4f} "
              f"plc={r['placebo_mean_expectancy_net_r']:+.4f}"
              f"+-{r['placebo_sd_expectancy_net_r']:.4f} "
              f"pctile={r['real_percentile_in_placebo']:.2f} "
              f"z={r['z_vs_placebo']:+.2f}")
    print(f"  -> {p}")


if __name__ == "__main__":
    main()
