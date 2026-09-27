"""EF4 - full-pipeline prefix invariance: the one test the programme's methodology is blind to.

The ORB/ICT report states the lesson exactly: "Resampling cannot detect a bias whose sign is
always favourable. Only auditing the fill model can." Out-of-sample splits, disjoint slices
and walk-forward all PASS a bias that is present in every period. A +0.354R cluster at
t = 5.19 survived a 60/40 split and all three disjoint slices in this repository and was a
look-ahead in the author's own fill code.

The test that does catch it is **prefix invariance**: rebuild everything on ``bars[0:k]`` and
check that every trade entirely inside ``[0, k)`` is bit-identical to the corresponding trade
in the full run. Any quantity computed from the whole series - a percentile over all bars, a
swing confirmed by later bars, a profile built from the future, a repainting pointer - makes
the prefix run differ. A clean pass is not proof of no look-ahead, but a failure is proof of
one, and this pipeline has never been checked this way end to end.

EF1's ``prefix_invariance_report`` checks the *bar classification* only. This checks the whole
stack: ``SymbolFrame`` feature construction, the condition library, the engine and the
session rule.

Compared fields per trade: entry ts / price, initial stop, exit ts / price / reason, gross R,
net R, MAE, MFE. Tolerance 1e-9 on prices (floats), exact on timestamps and reasons.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF1/code"))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF4/code"))

from futures_agents.backtest.costs import CostModel       # noqa: E402
from futures_agents.config import get_contract            # noqa: E402
from futures_agents.data.archive import BarArchive         # noqa: E402
from futures_agents.data.bars import BarSeries             # noqa: E402
from futures_agents.features import SymbolFrame            # noqa: E402
from futures_agents.timeutil import to_et                  # noqa: E402
from session_window import SessionWindowEngine             # noqa: E402
from population import build_track_a                       # noqa: E402

TOL = 1e-9
FIELDS = ("entry_ts", "entry_price", "initial_stop", "exit_ts", "exit_price",
          "exit_reason", "gross_r", "net_r", "mae_r", "mfe_r", "risk_points")


def key(t):
    return (t.strategy_id, to_et(t.entry_ts).isoformat())


def snap(t) -> dict:
    d = {}
    for f in FIELDS:
        v = getattr(t, f)
        d[f] = (to_et(v).isoformat() if f.endswith("_ts")
                else (v.value if f == "exit_reason" else v))
    return d


def run(symbol: str, tf: int, fracs=(0.4, 0.6, 0.8)) -> dict:
    spec = get_contract(symbol)
    cost = CostModel(spec)
    full_series = BarArchive(str(ROOT / "data/archive")).load(symbol, tf)
    strats = build_track_a(symbol, tf)

    def one(series: BarSeries):
        frame = SymbolFrame(series, (tf,))
        eng = SessionWindowEngine(frame, cost)
        return eng.run_many(strats)

    full = one(full_series)
    full_trades = {}
    for sid, res in full.items():
        for t in res.trades:
            full_trades[key(t)] = (snap(t), t.exit_index)

    out = []
    for fr in fracs:
        k = int(len(full_series.bars) * fr)
        pref = BarSeries(symbol, tf, full_series.bars[:k])
        pres = one(pref)
        checked = mismatched = 0
        detail = []
        for sid, res in pres.items():
            for t in res.trades:
                # only trades that closed strictly inside the prefix are comparable;
                # the last one may have been cut short by END_OF_DATA
                if t.exit_index >= k - 1:
                    continue
                kk = key(t)
                if kk not in full_trades:
                    mismatched += 1
                    detail.append({"reason": "trade absent in full run",
                                   "key": [kk[0], kk[1]]})
                    continue
                a, b = snap(t), full_trades[kk][0]
                checked += 1
                diffs = {}
                for f in FIELDS:
                    x, y = a[f], b[f]
                    if isinstance(x, float) and isinstance(y, float):
                        if abs(x - y) > TOL:
                            diffs[f] = [x, y]
                    elif x != y:
                        diffs[f] = [x, y]
                if diffs:
                    mismatched += 1
                    if len(detail) < 12:
                        detail.append({"key": [kk[0], kk[1]], "diffs": diffs})
        out.append({"fraction": fr, "prefix_bars": k,
                    "trades_compared": checked, "mismatched": mismatched,
                    "detail": detail})
        print(f"  prefix {fr:.0%} ({k} bars): compared {checked} trades, "
              f"{mismatched} mismatched")
    return {"symbol": symbol, "tf": tf, "arms": len(strats), "prefixes": out}


if __name__ == "__main__":
    res = []
    for sym in ("MGC", "MCL"):
        for tf in (30, 15):
            print(f"{sym} {tf}m")
            res.append(run(sym, tf))
    p = ROOT / "workspace/roundtable/edge/EF4/out/audit_lookahead.json"
    p.write_text(json.dumps(res, indent=2))
    tot = sum(x["mismatched"] for r in res for x in r["prefixes"])
    cmp_ = sum(x["trades_compared"] for r in res for x in r["prefixes"])
    print(f"\nTOTAL: {cmp_} trade comparisons, {tot} mismatches")
    print(f"wrote {p}")
