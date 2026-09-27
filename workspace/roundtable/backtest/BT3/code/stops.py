"""Reconstruct the per-trade dollar risk behind ``geo_trades.json``.

Why this exists
---------------
The governor replay (ALGO-1) needs two numbers per trade: the realised ``r``,
which the stored artefact has, and the **stop distance in points**, which it
does not. ``geo_trades.json`` carries no ``entry``, no ``stop``, no ``atr`` and
no dollar figure `[measured: sorted(d[0]) -> 17 keys, none of them a price]`,
so ``RiskManager.contracts_for`` - the one governor that *deletes* trades
rather than shrinking them - cannot be evaluated from the artefact alone.

It is recoverable without a new experiment, because the study that produced the
artefact is fully deterministic: ``workspace/newstrats/run_geometry.py`` builds
its strategies from a fixed condition list, over fixed disjoint slices of the
frozen ``csv/raw`` snapshot, with no seed and no sampling. Re-running the
``partner == "none"`` subset - the only subset whose trades were dumped
`[repo-verified: run_geometry.py:110-121]` - reproduces the same trades and
carries ``entry_price`` and ``initial_stop`` with them.

So this module **re-runs 22 strategies per cell instead of the original 286**
and then *proves* the reproduction by matching every trade back to the stored
file on ``(cell, arm, exitm, entry_ts, direction)`` and checking that ``net_r``
agrees to the 5 decimals the artefact stored. A reproduction that did not match
would make every number downstream of it meaningless, so the match is asserted,
not hoped for.

Output: ``stops_cache.json``, one row per stored trade, adding
``risk_points`` (= ``abs(entry_price - initial_stop)``, which is exactly what
the engine divides by to get R `[repo-verified: engine.py:359-361]` and exactly
what ``contracts_for`` multiplies by ``point_value``
`[repo-verified: risk/manager.py:197-203]``).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = "/home/user/Futures01"
os.chdir(ROOT)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "workspace/studies"))
sys.path.insert(0, os.path.join(ROOT, "workspace/newstrats"))

import geometry as G                                         # noqa: E402
import toolkit as T                                          # noqa: E402
from futures_agents.backtest.engine import run_portfolio      # noqa: E402
from futures_agents.features import build_symbol_frame        # noqa: E402
from futures_agents.scout import FRAMES                       # noqa: E402
from futures_agents.strategies.base import (ExitModel, StopKind,   # noqa: E402
                                            StrategyFilters, TargetKind)

TRADES = "workspace/strategy_research/scratch/geo_trades.json"
CACHE = "workspace/roundtable/backtest/BT3/code/stops_cache.json"

SYMBOLS = ["MGC", "MES", "MNQ", "MCL"]
TFS = [240, 60]

# Verbatim from run_geometry.py:53-65. Copied rather than imported because
# importing that module would re-run nothing but would tie this file to a
# script that is not mine to keep stable.
EXITS = {
    "atr1.0": ExitModel(StopKind.ATR, 1.0, targets_r=(2.0, 4.0),
                        scale_out=(0.5, 0.5), breakeven_at_r=1.5,
                        time_stop_bars=40, target_kind=TargetKind.ANCHOR_ATR,
                        anchor_mult=(1.0, 2.5), min_reward_risk=1.5,
                        exit_at_session_close=False),
    "atr1.5": ExitModel(StopKind.ATR, 1.5, targets_r=(2.0, 4.0),
                        scale_out=(0.5, 0.5), breakeven_at_r=1.5,
                        time_stop_bars=40, target_kind=TargetKind.ANCHOR_ATR,
                        anchor_mult=(1.0, 2.5), min_reward_risk=1.5,
                        exit_at_session_close=False),
}
FOLLOW = ["legs_expanding", "legs_contracting", "pullbacks_shallowing",
          "pullbacks_deepening", "swing_symmetry_impulse",
          "swing_symmetry_retrace"]
FADE = ["legs_contracting_fade", "pullbacks_deepening_fade",
        "swing_symmetry_retrace_fade"]


def build_none_partner(symbol, tf):
    """The 22 strategies whose trades run_geometry actually dumped."""
    out = []
    for base, arms in (("structure_trend_ctl", ["CONTROL"] + FOLLOW),
                       ("structure_trend_fade_ctl", ["CONTROL_FADE"] + FADE)):
        for arm in arms:
            conds = [G.get(base)]
            if not arm.startswith("CONTROL"):
                conds.append(G.get(arm))
            for ename, ex in EXITS.items():
                s = T.make_strategy(
                    symbol, tf, conds, group="GEOMETRY",
                    name=f"{arm}|none|{ename}", exit_model=ex,
                    filters=StrategyFilters(rth_only=False))
                out.append((arm, base, ename, s))
    return out


def run_cell(symbol, tf, lo, hi, label):
    series = T.slice_series(symbol, tf, lo, hi)
    if len(series) < 150:
        return []
    frame = build_symbol_frame(series, FRAMES[tf])
    G.clear()
    G.reset_stats()
    G.register_frame(frame)
    tagged = build_none_partner(symbol, tf)
    res = run_portfolio(frame, [t[-1] for t in tagged])
    out = []
    for arm, base, ename, s in tagged:
        for t in res[s.strategy_id].trades:
            out.append(dict(
                cell=f"{symbol}_{tf}_{label}", symbol=symbol, tf=tf,
                slice=label, arm=arm, base=base, exitm=ename,
                ts=t.entry_ts.isoformat(), dir=t.direction.value,
                r=round(t.net_r, 5),
                entry=t.entry_price, stop=t.initial_stop,
                risk_points=abs(t.entry_price - t.initial_stop)))
    return out


def key(row):
    return (row["cell"], row["arm"], row["exitm"], row["ts"], row["dir"])


def main():
    stored = json.load(open(TRADES))
    repro = []
    for sym in SYMBOLS:
        for tf in TFS:
            for k, (lo, hi) in enumerate(T.disjoint_slices(sym, tf, 3), 1):
                got = run_cell(sym, tf, lo, hi, f"S{k}")
                repro += got
                print(f"{sym} {tf}m S{k}: {len(got)} trades", flush=True)

    # ---- prove the reproduction before using any of it -----------------
    by_key = {}
    dupes = 0
    for r in repro:
        if key(r) in by_key:
            dupes += 1
        by_key[key(r)] = r
    print(f"\nstored={len(stored)} reproduced={len(repro)} "
          f"duplicate keys in reproduction={dupes}")

    missing, rmismatch = 0, 0
    worst = 0.0
    for s in stored:
        m = by_key.get(key(s))
        if m is None:
            missing += 1
            continue
        d = abs(m["r"] - s["r"])
        worst = max(worst, d)
        if d > 1e-5:
            rmismatch += 1
    print(f"stored trades not found in reproduction: {missing}")
    print(f"stored trades whose net_r disagrees by >1e-5: {rmismatch} "
          f"(worst |dr| = {worst:.3e})")
    assert missing == 0 and rmismatch == 0, "reproduction does not match the artefact"

    out = []
    for s in stored:
        m = by_key[key(s)]
        row = dict(s)
        row["entry"] = m["entry"]
        row["stop"] = m["stop"]
        row["risk_points"] = round(m["risk_points"], 8)
        out.append(row)
    json.dump(out, open(CACHE, "w"))
    print(f"wrote {CACHE}: {len(out)} rows with risk_points")


if __name__ == "__main__":
    main()
