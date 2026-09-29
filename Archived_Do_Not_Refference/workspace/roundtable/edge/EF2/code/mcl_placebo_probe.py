"""EF2: re-measure EF6's placebo Fault 1 on MCL, which EF6 did not cover.

EF6 burst 03 Fault 1 (count-matching breaks under the window rule) was measured
on MGC and MNQ only. MCL is one of EF2's two symbols, the independence rule says
nothing transfers, and the arithmetic reason MGC escapes the fault (RTH closes
13:30, so its last RTH bar fills at 14:00) has an MCL analogue (RTH closes 14:30,
last RTH bar stamped 14:00, fills at 15:00) that is an argument rather than a
measurement. This measures it.

Runs on BOTH of EF2's primary timeframes and BOTH rth_only arms, on the cells EF2
actually publishes - the 60m base with frames (60,) and (60,240) - not on a 240m
base, because a 240m base is 19% STRADDLE bars (EF2 burst 05) and EF1's harness
refuses a grid like that.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

REPO = "/home/user/Futures01"
for p in (REPO, os.path.join(REPO, "workspace"),
          os.path.join(REPO, "workspace", "roundtable", "edge", "EF6", "code"),
          os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

from futures_agents.schema import Direction                   # noqa: E402
from newstrats import placebo as PL                           # noqa: E402
import arms as ARMS                                           # noqa: E402
import window as W                                            # noqa: E402
from substrate import frame_for                               # noqa: E402
import population as P                                        # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")


def probe(symbol: str, cell: str, rth_only: bool, n_bases: int = 30) -> dict:
    tfs, ptf, confirm = P.CELL_SPEC[cell]
    frame = frame_for(symbol, tfs)
    bars = frame.base.bars
    base_min = frame.base.minutes
    wmask = W.window_mask(bars, base_min)
    smask = W.signal_mask(bars, base_min)

    rss = P.rule_sets_for(symbol)
    voids = P.void_sets()
    ck = f"{symbol}:{cell}"
    bases = []
    for rs in rss:
        st = P.build(symbol, cell, rs, rth_only)
        if st is None or P.void_reason(st, ck, voids):
            continue
        bases.append(st)
        if len(bases) >= n_bases:
            break
    ARMS.assert_unique(bases, labels=["arm"])

    real, pools = PL.scan(frame, bases, want_pool=True)
    rows = []
    for s in bases:
        sch = real.get(s.strategy_id, {})
        if len(sch) < 2:
            continue
        pl = pools.get(s.strategy_id, {})
        pool_all = list(pl.get(Direction.LONG, ())) + list(pl.get(Direction.SHORT, ()))
        if not pool_all:
            continue
        base_legal = sum(1 for i in sch if i < len(smask) and smask[i])
        pool_legal = sum(1 for i in pool_all if i < len(smask) and smask[i])
        cnt = Counter(sch.values())
        nl = cnt.get(Direction.LONG, 0)
        long_share = nl / max(1, len(sch))
        rows.append({
            "strategy_id": s.strategy_id, "group": s.group,
            "raw_signals": len(sch),
            "raw_signals_legal": base_legal,
            "base_legal_share": base_legal / len(sch),
            "pool": len(pool_all), "pool_legal": pool_legal,
            "pool_legal_share": pool_legal / len(pool_all),
            "long_share": long_share,
            "direction_shuffle_degeneracy": long_share ** 2 + (1 - long_share) ** 2,
            # the defect: expected legal count of a count-matched uniform draw
            # from the pool, minus the base's own legal count
            "expected_legal_gap": round(
                len(sch) * (pool_legal / len(pool_all)) - base_legal, 2),
        })
    return {"symbol": symbol, "cell": cell, "primary_tf": ptf,
            "frame_tfs": list(tfs), "rth_only": rth_only,
            "bases_probed": len(bases), "bases_with_ge2_signals": len(rows),
            "bars": len(bars),
            "bars_signal_legal": sum(smask), "bars_position_legal": sum(wmask),
            "rows": rows}


def main() -> None:
    out = {"cells": {}}
    for sym in ("MCL", "MGC"):
        for cell in ("f60__p60", "f60_240__p240"):
            for rth in (True, False):
                k = f"{sym}:{cell}|rth{int(rth)}"
                sys.stderr.write(f"{k} ...\n")
                sys.stderr.flush()
                out["cells"][k] = probe(sym, cell, rth)
    with open(os.path.join(OUT, "mcl_placebo_probe.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print("| cell | bases with >=2 sigs | base legal share | pool legal share | "
          "mean expected legal gap | mean long share | mean dir-shuffle degeneracy |")
    print("|---|---|---|---|---|---|---|")
    for k, c in out["cells"].items():
        r = c["rows"]
        if not r:
            print(f"| `{k}` | 0 | — | — | — | — | — |")
            continue
        f = lambda key: sum(x[key] for x in r) / len(r)
        print(f"| `{k}` | {len(r)} | {f('base_legal_share'):.3f} | "
              f"{f('pool_legal_share'):.3f} | {f('expected_legal_gap'):+.2f} | "
              f"{f('long_share'):.3f} | {f('direction_shuffle_degeneracy'):.3f} |")


if __name__ == "__main__":
    main()
