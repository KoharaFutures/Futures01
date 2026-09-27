"""EF2 Burst 03b: the strategy-level raw fire census — harness-independent.

Why this is measurable before EF1 validates. ``Strategy.evaluate`` reads only
``snap`` [repo-verified: base.py:658-660] and knows nothing about position state,
session rules or exits. So "on how many bars does this strategy's gate open" is a
property of the rule set and the data alone. ``BacktestResult.signals_generated``
is NOT this number - the engine skips evaluation entirely while a position is
open [repo-verified: engine.py:306-307] - so it is harness-dependent and cannot
be used here.

What it buys: the **effective** search size. An arm with 0 raw fires is a
guaranteed zero trade under every harness, so it is not a hypothesis that was
tested and it must not sit in the denominator of a deflation threshold. That is
the distinction the programme's own wording correction is about
("candidates generated, of which an unmeasured subset could not trade").

Cost control: ``evaluate`` depends only on (conditions, allowed_directions,
rth_only, primary_tf) - never on the ExitModel. Arms are therefore grouped into
**gate signatures** and each signature is evaluated once.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from typing import Dict, List, Tuple

REPO = "/home/user/Futures01"
if REPO not in sys.path:
    sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from substrate import frame_for                                    # noqa: E402
import population as P                                             # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")


def gate_sig(st) -> tuple:
    return (st.primary_tf,
            tuple(sorted(c.label for c in st.conditions)),
            tuple(sorted(d.value for d in st.allowed_directions)),
            st.filters.identity)


def main() -> None:
    res = P.assemble()
    objs = res.pop("_objects")
    out = {"seed": res["seed"], "max_total": res["max_total"], "cells": {}}

    for sym in P.SYMBOLS:
        # group arms by (cell, gate signature)
        by: Dict[Tuple[str, tuple], List[str]] = defaultdict(list)
        for ak, st in objs[sym].items():
            by[(res["index"][sym][ak]["cell"], gate_sig(st))].append(ak)
        # one frame pass per cell
        cells = sorted({k[0] for k in by})
        for ck in cells:
            cellname = ck.split(":", 1)[1]
            tfs = tuple(res["cells"][cellname]["frame_tfs"])
            fr = frame_for(sym, tfs)
            sigs = [k[1] for k in by if k[0] == ck]
            reps = {}
            for k in by:
                if k[0] == ck:
                    reps[k[1]] = objs[sym][by[k][0]]
            t0 = time.time()
            fires = {s: 0 for s in sigs}
            long_ = {s: 0 for s in sigs}
            short = {s: 0 for s in sigs}
            n_bars = len(fr.base)
            for i in range(n_bars):
                snap = fr.snapshot(i)
                if snap is None:
                    continue
                cache: Dict[tuple, object] = {}
                for s in sigs:
                    out_sig = reps[s].evaluate(snap, cache)
                    if out_sig is None:
                        continue
                    fires[s] += 1
                    if out_sig.direction.value == "LONG":
                        long_[s] += 1
                    else:
                        short[s] += 1
            el = time.time() - t0
            arm_fires: Dict[str, dict] = {}
            for k, aks in by.items():
                if k[0] != ck:
                    continue
                s = k[1]
                for ak in aks:
                    arm_fires[ak] = {"fires": fires[s], "long": long_[s],
                                     "short": short[s]}
            nz = sum(1 for v in arm_fires.values() if v["fires"] > 0)
            out["cells"][ck] = {
                "symbol": sym, "frame_tfs": list(tfs),
                "primary_tf": res["cells"][cellname]["primary_tf"],
                "bars": n_bars, "gate_signatures": len(sigs),
                "arms": len(arm_fires), "arms_with_any_fire": nz,
                "arms_zero_fire": len(arm_fires) - nz,
                "seconds": round(el, 1),
                "arm_fires": arm_fires,
            }
            sys.stderr.write(f"{ck}: {len(sigs)} sigs, {len(arm_fires)} arms, "
                             f"{nz} live, {el:.0f}s\n")
            sys.stderr.flush()

    with open(os.path.join(OUT, "firecount.json"), "w") as fh:
        json.dump(out, fh)

    # ---- summary
    print("| cell | arms | gate sigs | arms with >=1 fire | arms with 0 fires | "
          "median fires (live) | p90 fires |")
    print("|---|---|---|---|---|---|---|")
    for ck, c in out["cells"].items():
        f = sorted(v["fires"] for v in c["arm_fires"].values() if v["fires"] > 0)
        med = f[len(f) // 2] if f else 0
        p90 = f[int(len(f) * 0.9)] if f else 0
        print(f"| `{ck}` | {c['arms']} | {c['gate_signatures']} | "
              f"{c['arms_with_any_fire']} | {c['arms_zero_fire']} | {med} | {p90} |")
    print()
    for sym in P.SYMBOLS:
        tot = sum(c["arms"] for c in out["cells"].values() if c["symbol"] == sym)
        live = sum(c["arms_with_any_fire"] for c in out["cells"].values()
                   if c["symbol"] == sym)
        for floor in (0, 20, 30, 50, 100):
            n = sum(1 for c in out["cells"].values() if c["symbol"] == sym
                    for v in c["arm_fires"].values() if v["fires"] >= max(1, floor))
            ft = math.sqrt(2 * math.log(max(2, n)))
            print(f"{sym}: arms with >= {floor or 1} raw fires = {n:5d} "
                  f"(of {tot}), free_t = {ft:.3f}, Sharpe needed = {ft/1.402:.2f}")
        print()


if __name__ == "__main__":
    main()
