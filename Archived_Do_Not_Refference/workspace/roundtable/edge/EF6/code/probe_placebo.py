"""Does workspace/newstrats/placebo.py's count-matching survive the window rule?

The brief's hypothesis, stated precisely: **a base whose signals are vetoed by
the 18:00->16:00 window will hand you a count-matched placebo of the wrong
size.** This measures it rather than arguing it.

What is measured, per (symbol, timeframe):

1. ``rth_only`` on generated strategies. If it is True the window rule is never
   reached at all, because ``StrategyFilters.passes`` already vetoes every bar
   outside the contract's own RTH.
2. The **in-window share of the base's raw signal schedule** vs the **in-window
   share of the placebo's draw pool** (the base's own eligible bars). These two
   numbers being different *is* the defect: ``_schedule_random`` draws ``k``
   bars uniformly from the pool, so if the pool's legal share differs from the
   schedule's legal share, the placebo arrives at the engine with a different
   number of *legal* entries than the base.
3. Whether ``placebo_shuffle`` destroys anything. Its docstring admits a
   lopsided direction mix leaves most bars unchanged; this reports the realised
   ``direction_changed`` fraction so the weakness is a number, not a caveat.
"""

from __future__ import annotations

import json
import os
import random
import sys
from collections import Counter

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, "/home/user/Futures01/workspace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from futures_agents.data.archive import BarArchive            # noqa: E402
from futures_agents.features import build_symbol_frame        # noqa: E402
from futures_agents.schema import Direction                   # noqa: E402
from futures_agents.strategies.combinator import generate_strategies  # noqa: E402
from newstrats import placebo as P                            # noqa: E402

import arms                                                   # noqa: E402
import window as W                                            # noqa: E402


def probe(symbol: str, base_tf: int, tfs, *, max_total: int = 200,
          n_bases: int = 25, rth_only=None) -> dict:
    arch = BarArchive("data/archive")
    series = arch.load(symbol, base_tf)
    frame = build_symbol_frame(series, tfs)
    bars = frame.base.bars
    wmask = W.window_mask(bars, base_tf)
    smask = W.signal_mask(bars, base_tf)

    gen = [s for s in generate_strategies(symbol, list(tfs), max_total=max_total)
           if s.primary_tf == base_tf]
    rth_counter = Counter(s.filters.rth_only for s in gen)
    if rth_only is not None:
        gen = [arms.refilter(s, rth_only=bool(rth_only)) for s in gen]
        arms.assert_unique(gen, labels=["arm"])
    bases = gen[:n_bases]
    if not bases:
        return {"symbol": symbol, "base_tf": base_tf, "error": "no strategies"}

    real, pools = P.scan(frame, bases, want_pool=True)

    rows = []
    for s in bases:
        r = real.get(s.strategy_id, {})
        pl = pools.get(s.strategy_id, {})
        pool_ix = list(pl.get(Direction.LONG, ())) + list(pl.get(Direction.SHORT, ()))
        if len(r) < 2 or not pool_ix:
            continue
        sig_legal = sum(1 for i in r if smask[i])
        pool_legal = sum(1 for i in pool_ix if smask[i])
        # what _schedule_random would actually produce, at this seed
        rng = random.Random(f"probe:{s.strategy_id}")
        sched = P._schedule_random(r, pl, len(bars), rng, "eligible")
        sched_legal = sum(1 for i in sched if smask[i])
        # what placebo_shuffle destroys
        sh = P._schedule_shuffle(r, random.Random(7))
        changed = sum(1 for i in sh if r.get(i) is not sh[i]) / max(1, len(sh))
        mix = Counter(r.values())
        rows.append({
            "strategy_id": s.strategy_id, "group": s.group,
            "rth_only": s.filters.rth_only,
            "n_real_signals": len(r),
            "real_legal": sig_legal,
            "real_legal_share": round(sig_legal / len(r), 4),
            "pool_bars": len(pool_ix),
            "pool_legal_share": round(pool_legal / len(pool_ix), 4),
            "placebo_scheduled": len(sched),
            "placebo_legal": sched_legal,
            "placebo_legal_share": round(sched_legal / max(1, len(sched)), 4),
            "legal_count_gap": sched_legal - sig_legal,
            "shuffle_direction_changed": round(changed, 4),
            "long_share": round(mix.get(Direction.LONG, 0) / len(r), 3),
        })

    def mean(k):
        v = [x[k] for x in rows if x[k] is not None]
        return round(sum(v) / len(v), 4) if v else None

    return {
        "symbol": symbol, "base_tf": base_tf, "frame": list(tfs),
        "substrate": "data/archive",
        "bars": len(bars),
        "bars_in_window": sum(wmask),
        "bars_signal_eligible": sum(smask),
        "window_share_of_all_bars": round(sum(smask) / len(bars), 4),
        "generated_rth_only": {str(k): v for k, v in rth_counter.items()},
        "n_bases_probed": len(rows),
        "mean_real_legal_share": mean("real_legal_share"),
        "mean_pool_legal_share": mean("pool_legal_share"),
        "mean_placebo_legal_share": mean("placebo_legal_share"),
        "mean_legal_count_gap": mean("legal_count_gap"),
        "total_real_legal": sum(x["real_legal"] for x in rows),
        "total_placebo_legal": sum(x["placebo_legal"] for x in rows),
        "mean_shuffle_direction_changed": mean("shuffle_direction_changed"),
        "mean_long_share": mean("long_share"),
        "rows": rows,
    }


if __name__ == "__main__":
    out = []
    jobs = [("MGC", 60, [60, 240, 1440]), ("MNQ", 60, [60, 240, 1440]),
            ("MGC", 15, [15, 60, 240]), ("MNQ", 15, [15, 60, 240])]
    for sym, tf, tfs in jobs:
        for ro in (True, False):
            d = probe(sym, tf, tfs, rth_only=ro)
            d["arm"] = f"rth_only={ro}"
            out.append(d)
            print(f"{sym} {tf}m rth_only={ro}: bases={d.get('n_bases_probed')} "
                  f"real_legal_share={d.get('mean_real_legal_share')} "
                  f"pool_legal_share={d.get('mean_pool_legal_share')} "
                  f"placebo_legal_share={d.get('mean_placebo_legal_share')} "
                  f"gap={d.get('mean_legal_count_gap')} "
                  f"shuffle_changed={d.get('mean_shuffle_direction_changed')}",
                  flush=True)
    p = "workspace/roundtable/edge/EF6/out/placebo_window_probe.json"
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("written", p)
