"""EF2 Burst 1: the firing-rate census for the four swing cells.

Why this runs BEFORE any population is constructed. ``Strategy.evaluate`` is a
strict AND with no ``min_signals`` [repo-verified: futures_agents/strategies/
base.py:670-684], so ONE condition that can never fire makes the whole strategy
structurally incapable of trading. A top-10 drawn from a pool containing such
strategies measures the pool's dead weight, not the market: a never-firing
strategy and a strategy that traded and lost both produce a null, and only the
second is evidence.

This census is per (symbol, frame, primary_tf, bound timeframe) - VOID is never
a global property. It produces four counts per condition:

``fires``        triggered on any base bar
``fires_rth``    triggered on a bar with ``snap.is_rth`` True. 314/314 generated
                 strategies carry ``rth_only=True`` [R1, D-L4], so a condition
                 that fires only outside RTH is dead INSIDE a strategy even
                 though its raw rate is non-zero.
``fires_swing``  triggered on a bar that is an admissible ENTRY bar under this
                 programme's 18:00 ET -> 16:00 ET rule: the bar must not lie
                 wholly inside 16:00-18:00 and must not close at/after 16:00
                 and before 18:00. This is the count that matters here, because
                 the swing harness will never act on any other bar.
``fires_both``   RTH and swing-admissible.

It also reports the direction split, because a SIGNAL that only ever returns
NEUTRAL cannot satisfy ``evaluate``'s direction check either.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from typing import Dict, List, Optional, Tuple

REPO = "/home/user/Futures01"
if REPO not in sys.path:
    sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from futures_agents.schema import Direction                        # noqa: E402
from futures_agents.strategies.base import (ConditionKind,         # noqa: E402
                                            CONDITION_ERRORS,
                                            reset_condition_errors)
from futures_agents.strategies.library import CONDITIONS           # noqa: E402
from futures_agents.timeutil import to_et                          # noqa: E402

from substrate import CELLS, SYMBOLS, frame_for                    # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")

#: EF6 owns the control/window surface, so EF2 uses EF6's mask rather than its
#: own. My first version computed the signal bar's end on a CONTIGUOUS grid
#: (16:00 + 60m = 17:00, inside the forbidden window) and called the 16:00 bar
#: inadmissible. EF6's asks what the NEXT BAR IN THE SERIES actually is, and the
#: 17:00 bar mostly does not exist, so the fill lands at the 18:00 open and is
#: legal. EF6's is the engine-faithful one - run_many fills pending entries at the
#: open of the next bar it ITERATES [repo-verified: engine.py:295-300], not at a
#: hypothetical grid position. Disagreement was 482 MGC / 468 MCL bars, all stamped
#: 16:00; see EF2/bursts/05.
sys.path.insert(0, os.path.join(REPO, "workspace", "roundtable", "edge", "EF6", "code"))
from window import signal_mask as _ef6_signal_mask                 # noqa: E402

BREAK_START = 16 * 60      # 16:00 ET, minute of day
BREAK_END = 18 * 60        # 18:00 ET


def entry_admissible(ts, minutes: int) -> bool:
    """DEPRECATED - EF2's own first-cut mask, kept only so burst 04's stop-fidelity
    denominator stays reproducible. It is STRICTER than the rule: it rejects the
    16:00-stamped bar, whose fill actually lands legally at the 18:00 open.
    Superseded by EF6's ``window.signal_mask``; do not use it for a new number."""
    et = to_et(ts)
    end = (et.hour * 60 + et.minute + minutes) % 1440
    return not (BREAK_START <= end < BREAK_END)


def census_cell(symbol: str, frame_key: str, timeframes: Tuple[int, ...],
                primary_tf: int, step: int = 1) -> dict:
    fr = frame_for(symbol, timeframes)
    bars = fr.base.bars
    base_min = fr.base.minutes

    # every (condition, bound timeframe) pair a strategy in this frame could
    # hold: the primary, plus each confirmation timeframe the combinator may
    # bind a structure SIGNAL to [repo-verified: combinator.py:612-625].
    tf_bindings = sorted({primary_tf, *timeframes})

    stats: Dict[Tuple[str, int], Counter] = {
        (n, tf): Counter() for n in CONDITIONS for tf in tf_bindings}
    n_bars = 0
    n_rth = 0
    n_swing = 0
    n_both = 0

    smask = _ef6_signal_mask(bars, base_min)
    reset_condition_errors()
    for i in range(0, len(bars), step):
        snap = fr.snapshot(i)
        if snap is None:
            continue
        bar = bars[i]
        n_bars += 1
        rth = bool(snap.is_rth)
        swing = bool(smask[i])
        n_rth += rth
        n_swing += swing
        n_both += (rth and swing)
        cache: Dict[Tuple[str, int], object] = {}
        for name, cond in CONDITIONS.items():
            for tf in tf_bindings:
                res = cond.evaluate(snap, tf, cache) if cond.timeframe is None \
                    else cond.evaluate(snap, tf, cache)
                if not res.triggered:
                    continue
                c = stats[(name, tf)]
                c["fires"] += 1
                if rth:
                    c["fires_rth"] += 1
                if swing:
                    c["fires_swing"] += 1
                if rth and swing:
                    c["fires_both"] += 1
                c[f"dir_{res.direction.value}"] += 1

    rows = []
    for (name, tf), c in sorted(stats.items()):
        cond = CONDITIONS[name]
        usable = c["fires_both"]
        if cond.kind is ConditionKind.SIGNAL:
            # a SIGNAL must return LONG or SHORT; NEUTRAL fails evaluate()
            directional = c.get("dir_LONG", 0) + c.get("dir_SHORT", 0)
            usable = min(usable, directional)
        rows.append({
            "condition": name, "group": cond.group, "kind": cond.kind.value,
            "bound_tf": tf,
            "fires": c["fires"], "fires_rth": c["fires_rth"],
            "fires_swing": c["fires_swing"], "fires_both": c["fires_both"],
            "dir_LONG": c.get("dir_LONG", 0), "dir_SHORT": c.get("dir_SHORT", 0),
            "dir_NEUTRAL": c.get("dir_NEUTRAL", 0),
            "usable_fires": usable,
            "rate_all": c["fires"] / n_bars if n_bars else 0.0,
            "rate_usable": usable / n_both if n_both else 0.0,
            "verdict": "VOID" if usable == 0 else
                       ("VOID_IN_STRATEGY" if c["fires"] > 0 and usable == 0 else "LIVE"),
        })
    # second pass to distinguish "never fires at all" from "fires but never
    # where a strategy could act"
    for r in rows:
        if r["usable_fires"] == 0:
            r["verdict"] = "VOID_RAW" if r["fires"] == 0 else "VOID_IN_STRATEGY"
        else:
            r["verdict"] = "LIVE"

    return {
        "symbol": symbol, "frame_key": frame_key,
        "timeframes": list(timeframes), "primary_tf": primary_tf,
        "base_minutes": base_min, "step": step,
        "bars_evaluated": n_bars, "bars_rth": n_rth,
        "bars_swing_admissible": n_swing, "bars_rth_and_swing": n_both,
        "condition_errors": {f"{k[0]}:{k[1]}": v
                             for k, v in sorted(CONDITION_ERRORS.items())},
        "rows": rows,
    }


def main(step: int = 1) -> None:
    """One census pass per (symbol, FRAME).

    The rows are keyed by (condition, bound timeframe) and so do not depend on
    which primary_tf a strategy picks; frames (60,240) therefore serve both the
    p60 and p240 cells from one pass. Frames (60,) and (240,) are NOT derivable
    from (60,240): frame composition changes ``regime_tf``
    [repo-verified: features.py:820-826] and the alignment vote, which R1
    measured as up to a 13-point swing in a base filter's pass rate.
    """
    os.makedirs(OUT, exist_ok=True)
    frames = sorted({tfs for _, tfs, _ in CELLS})
    out = {"step": step, "frames": {}, "cells": {}}
    for sym in SYMBOLS:
        for tfs in frames:
            fk = "f" + "_".join(str(t) for t in tfs)
            ck = f"{sym}:{fk}"
            sys.stderr.write(f"census {ck} ...\n")
            sys.stderr.flush()
            out["frames"][ck] = census_cell(sym, fk, tfs, tfs[0], step=step)
    for sym in SYMBOLS:
        for key, tfs, ptf in CELLS:
            fk = "f" + "_".join(str(t) for t in tfs)
            out["cells"][f"{sym}:{key}"] = {
                "frame_ref": f"{sym}:{fk}", "timeframes": list(tfs),
                "primary_tf": ptf,
            }
    path = os.path.join(OUT, "census.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    sys.stderr.write(f"wrote {path}\n")


if __name__ == "__main__":
    main(step=int(sys.argv[1]) if len(sys.argv) > 1 else 1)
