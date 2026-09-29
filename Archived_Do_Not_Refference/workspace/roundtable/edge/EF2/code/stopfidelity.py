"""EF2 Burst 03c: D45 — how often does a named stop kind become a different one?

``ExitModel.stop_price`` ends every branch with ``dist = max(dist, min_dist)``
where ``min_dist = spec.min_stop_ticks * spec.tick_size``
[repo-verified: futures_agents/strategies/base.py:313-315]. When that clamp binds,
the stop is **a fixed number of ticks** whatever the enum says, and two arms that
differ only in ``stop_mult`` become the same trade. That is D45, and it is not
confined to ``VWAP_BAND``: the clamp is on the shared tail, so every kind can
collapse.

Also measured: how often each kind returns ``None`` (the stop cannot be placed, so
the trade is silently not taken - a second, invisible route to a low trade count).

Measured per (symbol, cell, stop kind, stop_mult) at the **stop multipliers the
generated population actually carries**, on both LONG and SHORT, at every
swing-admissible bar.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

REPO = "/home/user/Futures01"
if REPO not in sys.path:
    sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from futures_agents.config import get_contract                      # noqa: E402
from futures_agents.schema import Direction                         # noqa: E402
from futures_agents.strategies.base import ExitModel, StopKind      # noqa: E402
from futures_agents.strategies.combinator import (TEMPLATES,        # noqa: E402
                                                  exits_for)
from substrate import CELLS, SYMBOLS, frame_for                     # noqa: E402
from census import entry_admissible                                 # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")


def catalogue() -> List[ExitModel]:
    """Every distinct ExitModel any template can draw."""
    seen: Dict[str, ExitModel] = {}
    for t in TEMPLATES:
        for e in exits_for(t):
            seen.setdefault(e.identity, e)
    return sorted(seen.values(), key=lambda e: (e.stop_kind.value, e.stop_mult,
                                                e.stop_pad_ticks))


def main() -> None:
    cat = catalogue()
    out: dict = {"catalogue": [{"identity": e.identity,
                                "stop_kind": e.stop_kind.value,
                                "stop_mult": e.stop_mult,
                                "pad_ticks": e.stop_pad_ticks,
                                "target_kind": e.target_kind.value}
                               for e in cat],
                 "cells": {}}
    for sym in SYMBOLS:
        spec = get_contract(sym)
        min_dist = spec.min_stop_ticks * spec.tick_size
        for key, tfs, ptf in CELLS:
            fr = frame_for(sym, tfs)
            ck = f"{sym}:{key}"
            tally: Dict[str, Counter] = defaultdict(Counter)
            n = 0
            for i in range(len(fr.base)):
                snap = fr.snapshot(i)
                if snap is None:
                    continue
                bar = fr.base.bars[i]
                if not entry_admissible(bar.ts, fr.base.minutes):
                    continue
                n += 1
                entry = bar.close
                for e in cat:
                    for d in (Direction.LONG, Direction.SHORT):
                        k = f"{e.stop_kind.value}|m{e.stop_mult}|p{e.stop_pad_ticks}"
                        stop = e.stop_price(snap, ptf, d, entry, spec)
                        t = tally[k]
                        t["n"] += 1
                        if stop is None:
                            t["none"] += 1
                            continue
                        dist = abs(entry - stop)
                        # The clamp binds when the raw distance was below the
                        # floor; after tick rounding the result then sits at the
                        # floor to within half a tick.
                        if dist <= min_dist + spec.tick_size * 0.5:
                            t["at_floor"] += 1
            out["cells"][ck] = {
                "symbol": sym, "primary_tf": ptf, "frame_tfs": list(tfs),
                "bars_scored": n, "min_stop_ticks": spec.min_stop_ticks,
                "tick_size": spec.tick_size, "min_dist": min_dist,
                "by_geometry": {k: dict(v) for k, v in sorted(tally.items())},
            }
            sys.stderr.write(f"{ck}: {n} bars scored\n")
            sys.stderr.flush()
    with open(os.path.join(OUT, "stopfidelity.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print("| cell | geometry | evals | stop=None | at min-stop floor | "
          "floor rate | None rate |")
    print("|---|---|---|---|---|---|---|")
    for ck, c in out["cells"].items():
        for k, v in c["by_geometry"].items():
            nn = v["n"]
            print(f"| `{ck}` | `{k}` | {nn} | {v.get('none',0)} | "
                  f"{v.get('at_floor',0)} | {v.get('at_floor',0)/nn*100:.1f}% | "
                  f"{v.get('none',0)/nn*100:.1f}% |")


if __name__ == "__main__":
    main()
