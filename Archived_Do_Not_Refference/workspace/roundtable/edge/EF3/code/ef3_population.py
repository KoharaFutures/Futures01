"""EF3 burst 04 - construct and record the population, with its exact size.

Pre-registered, in writing, BEFORE any expectancy is computed:

FRAME      F2 = SymbolFrame(archive 60m base, timeframes=[60, 240]); regime_tf=60
           (verified: _default_regime_tf prefers 15,30,5,60 -> 60 for this frame,
           so the regime/volatility base filters read the SAME series in both
           the 60m and the 240m cell and cannot confound the comparison)

CELLS      (symbol, primary_tf) for symbol in {MES, MNQ}, primary_tf in {60, 240}
           Every symbol is its own universe. MES and MNQ are ONE index complex,
           so a rule set ranking in both is one observation, not two.

ARMS       confirm : primary 60 gets confirm_tfs=() and confirm_tfs=(240,)
                     primary 240 gets confirm_tfs=() only - 240 is the top of
                     this frame, so no confirmation arm EXISTS, which is
                     exactly why MULTI_TIMEFRAME's two SIGNALs are VOID there
           rth     : rth_only=True (the repo default, and the MES/MNQ research
                     profile's setting) and rth_only=False
                     -> rth_only=True caps the maximum hold at 6.5h, because
                     the only legal entries are 09:30-16:00 and the position
                     must be flat at 16:00 the same day. The 22-hour window the
                     programme exists to measure is reachable ONLY with
                     rth_only=False. Both arms are carried; the pair is the
                     central question of the swing cell.

GROUPS     the symbol's own research profile (profiles.groups_for), which is
           the repository's default generation path:
             MES  VWAP VOLUME_PROFILE MEAN_REVERSION PULLBACK REVERSAL
                  LIQUIDITY MULTI_TIMEFRAME
             MNQ  MOMENTUM TREND BREAKOUT OPENING_RANGE MULTI_TIMEFRAME
                  LIQUIDITY PULLBACK
           MNQ's profile admits MOMENTUM and BREAKOUT, the only two templates
           offering the `openinterest` group - which is why MNQ's dead-condition
           rate is the worst of the four symbols.

SEED       20260922 (the repository default), fixed, recorded.

D48 GUARD  every dataclasses.replace passes _id=None, and arm-id uniqueness is
           asserted at emission. Without it both arms collide into one
           BacktestResult and the measured difference is exactly zero.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, "/home/user/Futures01")

from futures_agents.strategies.base import ConditionKind, Strategy
from futures_agents.strategies.combinator import (_build_strategy,
                                                  generate_combinations)
from futures_agents.strategies.library import CONDITIONS
from futures_agents.strategies.profiles import groups_for
from futures_agents.strategies.combinator import TEMPLATES

OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF3/out")
SEED = 20260922
TFS = (60, 240)
ALL_GROUPS = [t.group for t in TEMPLATES]


def _void_map() -> Dict[Tuple[str, str, int], bool]:
    """(symbol, condition, binding_tf) -> is it VOID on frame F2 (0 fires)."""
    out = {}
    for sym in ("MES", "MNQ"):
        d = json.loads((OUT / f"census_{sym}.json").read_text())
        for r in d["conditions"]:
            for tf in TFS:
                out[(sym, r["condition"], tf)] = (r[f"fires_{tf}"] == 0)
    return out


def bindings(s: Strategy) -> List[Tuple[str, int]]:
    """(condition name, the tf it will actually be evaluated at)."""
    return [(c.name, c.timeframe or s.primary_tf) for c in s.conditions]


def build(sym: str, max_total: int) -> dict:
    groups = list(groups_for(sym, ALL_GROUPS) or ALL_GROUPS)
    specs = []
    # two confirm arms, same seed -> the SAME rule sets are sampled, so the
    # pair is paired by construction rather than by coincidence.
    for cmap in ({60: (), 240: ()}, {60: (240,), 240: ()}):
        specs += generate_combinations(sym, list(TFS), groups=groups,
                                       confirm_map=cmap, max_total=max_total,
                                       seed=SEED)
    built: Dict[str, Strategy] = {}
    for sp in specs:
        st = _build_strategy(sp)
        if st is not None:
            built.setdefault(st.strategy_id, st)

    # --- rth arm, with the D48 guard
    pop: Dict[str, Strategy] = {}
    for st in built.values():
        pop[st.strategy_id] = st
        alt = replace(st, filters=replace(st.filters, rth_only=not st.filters.rth_only),
                      _id=None)
        aid = alt.strategy_id
        assert aid != st.strategy_id, (
            f"D48: arm ids collided for {st.name} - the replace inherited _id")
        pop.setdefault(aid, alt)
    ids = [s.strategy_id for s in pop.values()]
    assert len(ids) == len(set(ids)), "arm-id uniqueness assertion failed"

    # --- dead-condition census
    void = _void_map()
    dead_reason: Dict[str, List[str]] = {}
    for st in pop.values():
        bad = []
        for name, tf in bindings(st):
            if void.get((sym, name, tf)):
                bad.append(f"{name}@{tf}m")
        if bad:
            dead_reason[st.strategy_id] = bad
    return {"symbol": sym, "groups": groups, "pop": pop, "dead": dead_reason}


def summarise(res: dict) -> dict:
    sym, pop, dead = res["symbol"], res["pop"], res["dead"]
    by_cell = defaultdict(lambda: {"n": 0, "dead": 0, "dead_by_cause": Counter(),
                                   "groups": Counter(), "dead_groups": Counter()})
    cause_names = Counter()
    for sid, st in pop.items():
        key = (st.primary_tf, "confirm" if st.confirm_tfs else "noconfirm",
               "rth" if st.filters.rth_only else "allhours")
        c = by_cell[key]
        c["n"] += 1
        c["groups"][st.group] += 1
        if sid in dead:
            c["dead"] += 1
            c["dead_groups"][st.group] += 1
            for b in dead[sid]:
                c["dead_by_cause"][b] += 1
                cause_names[b] += 1
    out = {"symbol": sym, "total": len(pop), "total_dead": len(dead),
           "dead_pct": round(100.0 * len(dead) / max(1, len(pop)), 2),
           "cause_census": dict(cause_names.most_common()),
           "cells": {}}
    for k in sorted(by_cell):
        c = by_cell[k]
        out["cells"]["|".join(map(str, k))] = {
            "n": c["n"], "dead": c["dead"],
            "dead_pct": round(100.0 * c["dead"] / max(1, c["n"]), 2),
            "live": c["n"] - c["dead"],
            "groups": dict(c["groups"].most_common()),
            "dead_groups": dict(c["dead_groups"].most_common()),
            "dead_by_cause": dict(c["dead_by_cause"].most_common()),
        }
    return out


if __name__ == "__main__":
    max_total = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    OUT.mkdir(parents=True, exist_ok=True)
    allsum = {"max_total": max_total, "seed": SEED, "frame": "[60,240] base 60m"}
    keep = {}
    for sym in ("MES", "MNQ"):
        res = build(sym, max_total)
        allsum[sym] = summarise(res)
        keep[sym] = res
        print(json.dumps(allsum[sym], indent=1)[:4000])
    (OUT / f"population_{max_total}.json").write_text(json.dumps(allsum, indent=1))
    # the id manifest, so the population is reproducible and citable
    man = {sym: sorted(keep[sym]["pop"]) for sym in keep}
    (OUT / f"population_ids_{max_total}.json").write_text(json.dumps(man))
    print("total population:", sum(len(v) for v in man.values()))
