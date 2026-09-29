"""EF5 -- trade-count feasibility census. PROVISIONAL: runs on EF1's harness.

The question this answers is not "what is profitable" but **"can a top 10 exist
at all in this cell"**. The signal census (``eliminate.py``) gave an upper bound:
60-277 strategies per cell reach 20 *signals*. Realised trades are strictly fewer
than signals, because ``max_concurrent_per_strategy = 1`` discards every signal
raised while a position is open, and because the 16:00 flat and the entry veto
remove more. So the binding number is the count of strategies that clear the
20-**trade** floor.

**This emits trade counts only.** No expectancy, no ranking, no per-row
profitability. Trade counts are a feasibility property of the detector and the
clock rule, in the same class as the firing census, and they are what decides
whether the deliverable can be ten rows or must be shorter. They are nonetheless
marked PROVISIONAL because they are produced on ``EF1/code/session_window.py``
before EF1 has published a VERIFY note, and EF3 has an open defect report against
it (``msgs/EF3-01_...``: 19 of 507 sessions at 60m have no bar for the flat to
fire on). That defect is verified NOT to reach my cell -- all 41 of my
18:00->16:00 cycles have a bar ending exactly at 16:00 ET at 5m, 15m and 30m, and
zero INTERIOR bars (burst 06) -- but the harness may change for other reasons.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(os.path.dirname(os.path.dirname(HERE)), "EF1", "code"),
          "/home/user/Futures01/workspace", "/home/user/Futures01"):
    if p not in sys.path:
        sys.path.insert(0, p)

from ef5_data import PRIMARY_TFS, REPO, SYMBOLS, build_frame        # noqa: E402
from population import base_population, session_arm                 # noqa: E402
from session_window import (SessionWindowEngine, assert_distinct_ids,  # noqa: E402
                            assert_hooks_reachable, violations)

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")
FLOOR = 20


def main() -> None:
    assert_hooks_reachable()
    out = {}
    for sym in SYMBOLS:
        for tf in PRIMARY_TFS:
            frame = build_frame(sym, tf)
            base = base_population(sym, tf)
            arms = {"RTH": base, "SESSION": session_arm(base)}
            assert_distinct_ids(arms["RTH"], arms["SESSION"])
            for arm, strats in arms.items():
                eng = SessionWindowEngine(frame)
                res = eng.run_many(strats)
                counts = {s.strategy_id: len(res[s.strategy_id].trades)
                          for s in strats}
                n = sorted(counts.values())
                floored = [s for s in strats if counts[s.strategy_id] >= FLOOR]
                # clone collapse on the realised ledger
                import hashlib
                seen = set()
                uniq = 0
                for s in floored:
                    tr = res[s.strategy_id].trades
                    key = "|".join(f"{t.entry_ts.isoformat()}:{t.direction.value}"
                                   for t in tr)
                    fp = hashlib.sha1(key.encode()).hexdigest()[:16]
                    if fp not in seen:
                        seen.add(fp)
                        uniq += 1
                allt = [t for r in res.values() for t in r.trades]
                key = f"{sym}_{tf}m_{arm}"
                out[key] = {
                    "symbol": sym, "primary_tf": tf, "arm": arm,
                    "population": len(strats),
                    "zero_trade": sum(1 for x in n if x == 0),
                    "trades_total": sum(n), "max_trades": n[-1] if n else 0,
                    "median_nonzero": (sorted(x for x in n if x)[
                        len([x for x in n if x]) // 2] if any(n) else 0),
                    "floored_20": len(floored),
                    "floored_20_clone_collapsed": uniq,
                    "floored_by_group": dict(Counter(s.group for s in floored)),
                    "engine_counters": {k: v for k, v in eng.counters.to_dict().items()
                                        if not isinstance(v, list)},
                    "rule_violations": len(violations(allt)),
                }
                print(f"{key}: pop={len(strats)} zero={out[key]['zero_trade']} "
                      f"total_trades={sum(n)} max_n={n[-1] if n else 0} "
                      f"floored>=20={len(floored)} (collapsed {uniq}) "
                      f"violations={out[key]['rule_violations']}", flush=True)
            del arms, base, frame
    with open(os.path.join(OUT, "floor_feasibility.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", os.path.join(OUT, "floor_feasibility.json"))


if __name__ == "__main__":
    main()
