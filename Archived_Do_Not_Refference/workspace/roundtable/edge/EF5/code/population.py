"""EF5 -- the SCALP population, declared before anything is measured.

Pre-registration, fixed here and not changed afterwards:

* **Symbols**  MES, MNQ. Independent universes. Nothing measured on one is ever
  claimed for the other, and because they are one index complex (D14/D41, 0.5-0.8%
  shared rule sets) agreement between them is not corroboration either.
* **Primary timeframes**  5, 15, 30. Each read inside the repo's own frame for
  that timeframe (``scout.FRAMES``): 5 -> [5,15,60], 15 -> [15,60,240],
  30 -> [30,60,240]. Adopted unchanged rather than invented.
* **Groups**  all **13** templates, for both symbols. The per-symbol
  ``SYMBOL_PROFILES`` narrowing is deliberately NOT applied: its timeframe lists
  are (1,5,15,60) for MNQ and (5,15,60) for MES, so the profile has no opinion at
  all about 30m, and applying a 7-group prior written for a different question
  would be a narrowing I could not defend later. Profile membership is carried as
  a column instead. Cost: free_t rises by ~0.1 t-units, which is nothing against
  a required Sharpe of 2.96.
* **Budget**  ``max_per_template=800``, ``max_total=999999``, ``seed=20260922``
  (the library default seed, unchanged).
* **Arms**  two, paired on the identical rule set:
    ``RTH``      -- ``rth_only=True``, as the combinator emits it. Entries
                    09:30-16:00 ET only. Comparable with all prior work.
    ``SESSION``  -- ``rth_only=False``. Entries anywhere inside 18:00->16:00 ET.
                    This is the regime the programme's session rule actually
                    describes and it has never been run here.
  Built with ``_id=None`` on the ``dataclasses.replace`` and an arm-id
  uniqueness assertion at emission (D48: without both, the two arms collide into
  one ``BacktestResult`` and the between-arm difference is exactly zero, which
  reads as "no effect").

Nothing in this module measures profitability. It emits the manifest and the
Strategy objects; EF1's validated harness does the rest.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from dataclasses import replace
from typing import Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from ef5_data import CELL_FRAMES, PRIMARY_TFS, REPO, SYMBOLS       # noqa: E402
from futures_agents.strategies.base import ConditionKind, Strategy  # noqa: E402
from futures_agents.strategies.combinator import (TEMPLATES,        # noqa: E402
                                                  generate_strategies)
from futures_agents.strategies.profiles import groups_for           # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")

ALL_GROUPS: List[str] = [t.group for t in TEMPLATES]
BUDGET = 800
SEED = 20260922
ARMS = ("RTH", "SESSION")


def base_population(symbol: str, primary_tf: int) -> List[Strategy]:
    """The RTH arm for one cell, exactly as the combinator emits it."""
    strats = generate_strategies(
        symbol, CELL_FRAMES[primary_tf], groups=ALL_GROUPS,
        max_total=999999, max_per_template=BUDGET, seed=SEED)
    return [s for s in strats if s.primary_tf == primary_tf]


def session_arm(strats: List[Strategy]) -> List[Strategy]:
    """The SESSION arm: identical rule sets with ``rth_only=False``.

    ``_id=None`` on BOTH replaces -- the outer one because ``Strategy._id`` is a
    dataclass field that ``replace`` copies (D48), the inner one is a
    ``StrategyFilters`` which has no memoised id.
    """
    out = []
    for s in strats:
        out.append(replace(s, filters=replace(s.filters, rth_only=False),
                           _id=None))
    return out


def build_all() -> Dict[Tuple[str, int, str], List[Strategy]]:
    pop: Dict[Tuple[str, int, str], List[Strategy]] = {}
    for sym in SYMBOLS:
        for tf in PRIMARY_TFS:
            base = base_population(sym, tf)
            pop[(sym, tf, "RTH")] = base
            pop[(sym, tf, "SESSION")] = session_arm(base)
    return pop


def assert_arm_ids_unique(pop: Dict[Tuple[str, int, str], List[Strategy]]) -> None:
    """D48 guard. Two things are asserted, not one.

    1. Within a cell, the RTH and SESSION arms must share NO strategy_id. If
       they do, the two arms are one arm and every paired difference is a
       mechanical zero.
    2. Globally, no strategy_id may appear twice under different (cell, arm)
       keys, which would merge two populations inside one result dict.
    """
    seen: Dict[str, Tuple[str, int, str]] = {}
    for key, strats in pop.items():
        ids = [s.strategy_id for s in strats]
        assert len(ids) == len(set(ids)), f"{key}: duplicate ids inside one arm"
        for sid in ids:
            prev = seen.get(sid)
            assert prev is None, (
                f"D48 arm-id collision: {sid} appears in {prev} and {key}. "
                "The two arms would collapse into one BacktestResult and the "
                "measured difference would be exactly zero.")
            seen[sid] = key
    # explicit pairwise check for the paired arms, stated separately so the
    # failure message names the design it protects
    for sym in SYMBOLS:
        for tf in PRIMARY_TFS:
            a = {s.strategy_id for s in pop[(sym, tf, "RTH")]}
            b = {s.strategy_id for s in pop[(sym, tf, "SESSION")]}
            assert not (a & b), f"{sym} {tf}m: RTH and SESSION arms share ids"


def manifest(pop: Dict[Tuple[str, int, str], List[Strategy]]) -> dict:
    cells = {}
    for (sym, tf, arm), strats in pop.items():
        prof = set(groups_for(sym, ALL_GROUPS) or ())
        cells[f"{sym}_{tf}m_{arm}"] = {
            "symbol": sym, "primary_tf": tf, "arm": arm,
            "frame_tfs": CELL_FRAMES[tf],
            "n": len(strats),
            "by_group": dict(Counter(s.group for s in strats)),
            "in_symbol_profile": sum(1 for s in strats if s.group in prof),
            "by_stop_kind": dict(Counter(str(s.exit.stop_kind) for s in strats)),
            "by_exec_tf": dict(Counter(str(s.execution_tf) for s in strats)),
            "n_signals": dict(Counter(
                len([c for c in s.conditions if c.kind is ConditionKind.SIGNAL])
                for s in strats)),
            "ids": [s.strategy_id for s in strats],
        }
    tot = sum(c["n"] for c in cells.values())
    return {
        "pre_registered": {
            "symbols": list(SYMBOLS), "primary_tfs": list(PRIMARY_TFS),
            "frames": {str(k): v for k, v in CELL_FRAMES.items()},
            "groups": ALL_GROUPS, "budget_max_per_template": BUDGET,
            "seed": SEED, "arms": list(ARMS),
            "substrate": "data/archive/{SYM}_{TF}m.jsonl",
        },
        "total_strategies": tot,
        "cells": cells,
    }


def main() -> None:
    pop = build_all()
    assert_arm_ids_unique(pop)
    man = manifest(pop)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "population.json"), "w") as fh:
        json.dump(man, fh)
    for k in sorted(man["cells"]):
        c = man["cells"][k]
        print(f"{k:22s} n={c['n']:5d} in_profile={c['in_symbol_profile']:5d}")
    print("TOTAL strategies (both arms, six cells):", man["total_strategies"])


if __name__ == "__main__":
    main()
