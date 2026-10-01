#!/usr/bin/env python3
"""H1 - anchored VWAP and its sigma bands. IS: search 7 anchors x 3 k. OOS: one test per symbol."""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import core                                      # noqa: E402
from anchors import ANCHOR_NAMES, anchor_index, band_signals, prefixes   # noqa: E402

KS = (0.0, 1.0, 2.0)
MIN_IS_TRADES = 20


def run(sym: str) -> dict:
    t = core.tape(sym)
    pre = prefixes(t)
    aidx = {a: anchor_index(t, a) for a in ANCHOR_NAMES}
    cache = {}
    rows = []
    for a in ANCHOR_NAMES:
        for k in KS:
            sig = band_signals(t, pre, aidx[a], k, retest_only=(k == 0))
            cache[(a, k)] = sig
            s = core.summary(core.score(t, sig, 0, t.is_end))
            rows.append({"anchor": a, "k": k, **{x: s.get(x) for x in
                        ("n", "avg_r", "t", "win", "payoff", "h1", "h2", "signals")}})
    ok = [r for r in rows if (r["n"] or 0) >= MIN_IS_TRADES and r["t"] is not None]
    pick = max(ok, key=lambda r: r["t"]) if ok else None
    out = {"symbol": sym, "family": "F1", "is_trials": len(rows), "is_rows": rows,
           "min_is_trades": MIN_IS_TRADES, "pick": pick}
    if pick is None:
        out["oos"] = None
        return out

    sig = cache[(pick["anchor"], pick["k"])]
    bk = core.score(t, sig, t.is_end, len(t))
    real = core.summary(bk)
    plc = []
    for seed in range(core.N_PLACEBO_SEEDS):
        plc.append(core.direction_placebo(t, sig, t.is_end, len(t), seed=seed))
    sh = core.shift_placebo(t, sig, t.is_end, len(t))
    out["oos"] = {
        "spec": {"anchor": pick["anchor"], "k": pick["k"]},
        "real": real,
        "dir_placebo_avg": core.st.fmean([p["avg_r"] for p in plc if p["n"]]) if any(p["n"] for p in plc) else None,
        "dir_placebo_beaten": sum(1 for p in plc if p["n"] and real["n"] and real["avg_r"] > p["avg_r"]),
        "shift": sh,
        "z_shift": core.z_shift(real, sh),
        "account": core.account(bk, t),
    }
    return out


if __name__ == "__main__":
    res = [run(s) for s in core.SYMS]
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "f1.json").write_text(json.dumps(res, indent=1, default=str))
    for r in res:
        print(f"\n=== {r['symbol']}  F1  (IS variants: {r['is_trials']}) ===")
        print(f"{'anchor':12s} {'k':>4s} {'n':>5s} {'avgR':>8s} {'t':>7s} {'win':>5s} {'payoff':>7s} {'h1':>8s} {'h2':>8s}")
        for q in sorted(r["is_rows"], key=lambda q: -(q["t"] or -9)):
            f = lambda v, p=4: ("%*.*f" % (8, p, v)) if isinstance(v, float) else "    --  "
            print(f"{q['anchor']:12s} {q['k']:4g} {q['n'] or 0:5d} {f(q['avg_r'])} "
                  f"{(('%7.3f'%q['t']) if q['t'] is not None else '     --')} "
                  f"{(('%5.2f'%q['win']) if q['win'] is not None else '   --')} "
                  f"{(('%7.2f'%q['payoff']) if q['payoff'] is not None else '     --')} "
                  f"{f(q['h1'])} {f(q['h2'])}")
        o = r["oos"]
        if not o:
            print("  no IS arm reached the trade floor")
            continue
        rl = o["real"]
        print(f"  OOS pick {o['spec']}: n={rl['n']} avgR={rl.get('avg_r')} t={rl.get('t')} "
              f"win={rl.get('win')} payoff={rl.get('payoff')}")
        print(f"  dir-placebo avg {o['dir_placebo_avg']} beaten {o['dir_placebo_beaten']}/10 | "
              f"shift-null mean {o['shift'].get('mean')} sd {o['shift'].get('sd')} -> z {o['z_shift']}")
        print(f"  halves {rl.get('h1')} / {rl.get('h2')} | exits {rl.get('exits')} | account {o['account']}")
