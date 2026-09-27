"""Build a trade ledger under the 18:00->16:00 rule, for the forward roll.

This is the interchange artefact. EF2-EF5 can emit the same shape from their own
sweeps; nothing in ``forward.py`` depends on how the trades were produced.

Usage:
    python3 make_ledger.py SYMBOL BASE_TF TF,TF,TF MAX_TOTAL OUT.json
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from futures_agents.data.archive import BarArchive            # noqa: E402
from futures_agents.features import build_symbol_frame        # noqa: E402
from futures_agents.strategies.combinator import generate_strategies  # noqa: E402

import arms                                                   # noqa: E402
import firing                                                 # noqa: E402
from session_engine import SessionWindowEngine                # noqa: E402


def build(symbol: str, base_tf: int, tfs, max_total: int, *,
          census_path: str = None) -> dict:
    arch = BarArchive("data/archive")
    series = arch.load(symbol, base_tf) if base_tf != 120 else \
        arch.load(symbol, 60).resample(120, keep_partial=False)
    frame = build_symbol_frame(series, list(tfs))

    gen = [s for s in generate_strategies(symbol, list(tfs), max_total=max_total)
           if s.primary_tf == base_tf]
    # The window regime is unreachable as generated: rth_only=True on all of them.
    win = [arms.refilter(s, rth_only=False) for s in gen]
    arms.assert_unique(win, labels=["window_arm"])

    # The prefilter is a HARD dependency, not an option. A silently-skipped
    # prefilter is exactly the failure it exists to prevent: the VOID rows stay
    # in `screened`, inflate free_t, and contribute a null that reads as a
    # market fact. This raised on the first MNQ run, where the census was still
    # being written - 82 of 412 MNQ 60m strategies (19.9%) were VOID and the
    # ledger recorded screened=412.
    if not census_path:
        raise ValueError("census_path is required - run run_census.py first")
    if not os.path.exists(census_path):
        raise FileNotFoundError(
            f"census {census_path} missing. Every strategy would enter the "
            "ledger unaudited and `screened` would count rows that cannot trade.")
    doc = firing.load_census(census_path)
    prefiltered, audit_rows = firing.prefilter(win, doc)

    eng = SessionWindowEngine(frame)
    t0 = time.time()
    res = eng.run_many(prefiltered)
    el = time.time() - t0
    arms.arm_report(res, prefiltered, labels=["window_arm"])

    out = {"symbol": symbol, "setting": "swing" if base_tf >= 60 else "scalp",
           "base_tf": base_tf, "frame": list(tfs), "substrate": "data/archive",
           "screened": len(prefiltered),
           "generated": len(gen), "prefiltered_out": len(win) - len(prefiltered),
           "t0": series.bars[0].ts.timestamp(),
           "t1": series.bars[-1].ts.timestamp(),
           "first_ts": str(series.bars[0].ts), "last_ts": str(series.bars[-1].ts),
           "n_bars": len(series.bars),
           "engine_audit": eng.audit(),
           "run_seconds": round(el, 1),
           "strategies": {}}
    for s in prefiltered:
        r = res.get(s.strategy_id)
        if r is None or not r.trades:
            continue
        out["strategies"][s.strategy_id] = {
            "meta": {"group": s.group, "primary_tf": s.primary_tf,
                     "stop": s.exit.label.split("->")[0],
                     "target": s.exit.label,
                     "name": s.name,
                     "conditions": [c.label for c in s.conditions]},
            "trades": [[t.entry_ts.timestamp(), t.exit_ts.timestamp(),
                        t.direction.sign, round(t.net_r, 6)] for t in r.trades],
        }
    out["with_trades"] = len(out["strategies"])
    out["total_trades"] = sum(len(v["trades"]) for v in out["strategies"].values())
    out["audit_rows"] = audit_rows[:0]   # counts only; full audit lives elsewhere
    out["prefilter_summary"] = (firing.audit_summary(audit_rows)
                                if audit_rows else None)
    return out


if __name__ == "__main__":
    sym, base, tfs, mt, path = sys.argv[1:6]
    census = sys.argv[6] if len(sys.argv) > 6 else None
    doc = build(sym, int(base), [int(x) for x in tfs.split(",")], int(mt),
                census_path=census)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(doc, fh, default=str)
    print(f"{sym} {base}m: generated {doc['generated']}, prefiltered out "
          f"{doc['prefiltered_out']}, screened {doc['screened']}, "
          f"with trades {doc['with_trades']}, total trades {doc['total_trades']}, "
          f"{doc['run_seconds']}s")
    print("engine:", json.dumps(doc["engine_audit"]))
    if doc.get("prefilter_summary"):
        print("prefilter:", json.dumps(doc["prefilter_summary"]))
    print("written", path)
