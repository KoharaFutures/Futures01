"""EF2: the look-ahead test, measured rather than read off the code.

The claim my anti-overfitting register makes is that ``Strategy.evaluate`` sees no
data from after its own bar. Every ingredient of that claim is verifiable by
reading (``snapshot`` uses the last COMPLETED bar per timeframe; ``find_swings``
needs ``right=3`` bars of future confirmation and ``_build_swing_pointers`` gates
visibility on ``confirmed_index <= i``; ``active_fvgs`` masks ``filled_index``;
``active_zones`` applies ``as_of``). Reading four guards is not the same as
measuring their conjunction, and the guards are exactly the kind of thing a later
change breaks silently.

**The test.** Build the frame on a PREFIX of the series (the first k bars) and on
the FULL series. For each strategy, its fire set on the prefix must equal its fire
set on the full series restricted to the first k bars - exactly, on every bar,
including direction. Any difference is data from after bar i reaching bar i,
because the prefix frame cannot see the bars the full frame can.

This is harness-independent - no engine, no session rule, no exits - so it does not
wait on EF1. It is also the strongest form of the check available, because it
perturbs the one thing that matters (what the future contains) and holds the past
byte-identical.

Known non-invariances that are NOT look-ahead, and are excluded by construction
rather than by judgement:
  * the last ``right`` bars of the prefix cannot have their swings confirmed yet,
    so a swing-dependent condition legitimately differs there. The comparison
    therefore stops ``GUARD_BARS`` before the cut.
  * ``atr_percentile`` is a 250-bar ROLLING rank [repo-verified: features.py:246],
    backward-looking, so it is invariant away from warm-up. Warm-up is at the
    START of the series and identical in both frames.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Tuple

REPO = "/home/user/Futures01"
for p in (REPO, os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

from futures_agents.config import get_contract                     # noqa: E402
from futures_agents.data.bars import BarSeries                     # noqa: E402
from futures_agents.features import build_symbol_frame             # noqa: E402
import population as P                                            # noqa: E402
from substrate import base_series                                 # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")

#: Bars of slack before the cut. The fractal swing detector needs 3 bars of future
#: confirmation (swing_right=3, features.py:193) and the FVG geometry needs 1, so
#: 8 is comfortably more than either and the choice cannot manufacture a pass -
#: a real look-ahead of any depth beyond 8 bars would still show.
GUARD_BARS = 8


def fire_set(frame, strategies, lo: int, hi: int) -> Dict[str, Dict[int, str]]:
    out: Dict[str, Dict[int, str]] = {s.strategy_id: {} for s in strategies}
    for i in range(lo, hi):
        snap = frame.snapshot(i)
        if snap is None:
            continue
        cache: Dict[Tuple[str, int], object] = {}
        for s in strategies:
            sig = s.evaluate(snap, cache)
            if sig is not None:
                out[s.strategy_id][i] = sig.direction.value
    return out


def check(symbol: str, cell: str, n_arms: int = 40,
          cut_frac: float = 0.70) -> dict:
    tfs, ptf, confirm = P.CELL_SPEC[cell]
    full_series = base_series(symbol, 60)
    n = len(full_series)
    k = int(n * cut_frac)

    rss = P.rule_sets_for(symbol)
    voids = P.void_sets()
    ck = f"{symbol}:{cell}"
    picked = []
    # pick arms that actually fire, otherwise the test is vacuous
    for rth in (True, False):
        for rs in rss:
            st = P.build(symbol, cell, rs, rth)
            if st is None or P.void_reason(st, ck, voids, rth_only=rth):
                continue
            picked.append(st)
            if len(picked) >= n_arms * 3:
                break
        if len(picked) >= n_arms * 3:
            break

    full = build_symbol_frame(full_series, tfs, get_contract(symbol))
    # keep only arms with at least one fire before the cut, then cap at n_arms
    probe = fire_set(full, picked, 0, k)
    live = [s for s in picked if probe[s.strategy_id]]
    live = live[:n_arms]
    if not live:
        return {"symbol": symbol, "cell": cell, "arms_tested": 0,
                "note": "no arm fired before the cut; test vacuous"}

    prefix_series = BarSeries(full_series.symbol, full_series.minutes,
                              list(full_series.bars[:k]))
    assert len(prefix_series) == k, (
        "BarSeries.append collapses bars sharing a timestamp (R5's D-candidate); "
        f"intended {k}, got {len(prefix_series)}")
    pre = build_symbol_frame(prefix_series, tfs, get_contract(symbol))

    stop = k - GUARD_BARS
    a = fire_set(full, live, 0, stop)
    b = fire_set(pre, live, 0, stop)

    mismatches = []
    tot_full = tot_pre = 0
    for s in live:
        sa, sb = a[s.strategy_id], b[s.strategy_id]
        tot_full += len(sa)
        tot_pre += len(sb)
        only_full = sorted(set(sa) - set(sb))
        only_pre = sorted(set(sb) - set(sa))
        flipped = sorted(i for i in (set(sa) & set(sb)) if sa[i] != sb[i])
        if only_full or only_pre or flipped:
            mismatches.append({
                "strategy_id": s.strategy_id, "group": s.group,
                "rth_only": s.filters.rth_only,
                "fires_full": len(sa), "fires_prefix": len(sb),
                "only_in_full_frame": only_full[:10],
                "only_in_prefix_frame": only_pre[:10],
                "direction_flipped": flipped[:10],
                "conditions": [c.label for c in s.conditions],
            })
    return {
        "symbol": symbol, "cell": cell, "primary_tf": ptf,
        "bars_full": n, "cut_at": k, "compared_to": stop,
        "guard_bars": GUARD_BARS,
        "arms_tested": len(live),
        "fires_full_frame": tot_full, "fires_prefix_frame": tot_pre,
        "arms_mismatched": len(mismatches),
        "verdict": "PREFIX-INVARIANT" if not mismatches else "LOOK-AHEAD PRESENT",
        "mismatches": mismatches[:20],
    }


def main() -> None:
    out = {"guard_bars": GUARD_BARS, "cells": {}}
    for sym in P.SYMBOLS:
        for cell in ("f60__p60", "f60_240__p240"):
            r = check(sym, cell)
            out["cells"][f"{sym}:{cell}"] = r
            sys.stderr.write(f"{sym}:{cell} -> {r.get('verdict')} "
                             f"({r['arms_tested']} arms, "
                             f"{r.get('fires_full_frame')} vs "
                             f"{r.get('fires_prefix_frame')} fires)\n")
            sys.stderr.flush()
    with open(os.path.join(OUT, "prefix_invariance.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("| cell | arms | fires (full frame) | fires (prefix frame) | "
          "arms mismatched | verdict |")
    print("|---|---|---|---|---|---|")
    for k, r in out["cells"].items():
        print(f"| `{k}` | {r['arms_tested']} | {r.get('fires_full_frame')} | "
              f"{r.get('fires_prefix_frame')} | {r.get('arms_mismatched')} | "
              f"**{r.get('verdict')}** |")


if __name__ == "__main__":
    main()
