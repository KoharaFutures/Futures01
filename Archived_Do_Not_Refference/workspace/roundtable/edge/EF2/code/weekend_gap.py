"""EF2: the weekend-gap fill, in R, at 60m and 240m.

`EF4-01` measured that with ``veto_signals_in_window=False`` (EF1's default, and
the rule as written) a signal on the 16:00-17:00 bar fills at the next bar's open -
which after a Friday is the **Sunday 18:00 reopen**, the largest discontinuity in
the substrate. EF4 measured +37.20 MGC points and +4.63 MCL points at 5m, i.e. 7.8 R
against a 1.0-ATR 5m stop.

This is directly downstream of the mask correction I adopted in burst 05: under
EF6's engine-faithful ``signal_mask`` the 16:00-stamped bar IS a legal signal bar
precisely because its fill lands at 18:00. So the correction is right about the rule
and it opens this tail, and both facts have to travel together.

EF4's cell is 5m/15m/30m. **A 60m stop is roughly 4x a 5m stop and a 240m stop
roughly 10x**, so the R magnitude does not transfer and must be measured here.
Method: for every bar that is a legal signal bar and whose NEXT bar is more than one
bar-length later, measure the open-to-close gap and express it in units of the
catalogue's ATR stops for that timeframe.
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
from collections import Counter
from typing import Dict, List

REPO = "/home/user/Futures01"
for p in (REPO, os.path.join(REPO, "workspace", "roundtable", "edge", "EF6", "code"),
          os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

from futures_agents.config import get_contract                     # noqa: E402
from futures_agents.data.bars import resample                      # noqa: E402
from futures_agents.timeutil import to_et                          # noqa: E402
from window import signal_mask                                     # noqa: E402
from substrate import base_series                                  # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")

#: The ATR stop multipliers the catalogue actually draws (burst 04).
STOP_MULTS = (0.75, 1.0, 1.2, 1.5, 2.5)


def atr_series(bars, period: int = 14):
    from futures_agents.indicators import atr
    return atr([b.high for b in bars], [b.low for b in bars],
               [b.close for b in bars], period)


def audit(symbol: str, tf: int) -> dict:
    s = base_series(symbol, 60)
    if tf != 60:
        s = resample(s, tf, keep_partial=False)
    bars = s.bars
    spec = get_contract(symbol)
    sm = signal_mask(bars, tf)
    a = atr_series(bars)

    rows: List[dict] = []
    for i in range(len(bars) - 1):
        if not sm[i]:
            continue
        cur, nxt = bars[i], bars[i + 1]
        lag_min = (to_et(nxt.ts) - to_et(cur.ts)).total_seconds() / 60.0
        if lag_min <= tf + 1e-9:
            continue                      # contiguous: the ordinary case
        gap = nxt.open - cur.close
        av = a[i] if i < len(a) else None
        rows.append({
            "ts": to_et(cur.ts).isoformat(),
            "next_ts": to_et(nxt.ts).isoformat(),
            "lag_minutes": lag_min,
            "lag_bars": lag_min / tf,
            "gap_points": gap,
            "abs_gap_points": abs(gap),
            "atr": av,
            "abs_gap_in_atr": (abs(gap) / av) if av else None,
        })
    # R impact, per stop multiplier: gap / (mult * ATR), floored by min_stop
    min_dist = spec.min_stop_ticks * spec.tick_size
    per_mult = {}
    for m in STOP_MULTS:
        rs = []
        for r in rows:
            if not r["atr"]:
                continue
            stop = max(m * r["atr"], min_dist)
            rs.append(r["abs_gap_points"] / stop)
        if rs:
            rs.sort()
            per_mult[f"ATRx{m}"] = {
                "n": len(rs), "median_R": rs[len(rs) // 2],
                "p90_R": rs[int(len(rs) * 0.9)], "max_R": rs[-1],
                "share_over_2R": sum(1 for x in rs if x > 2) / len(rs),
                "share_over_5R": sum(1 for x in rs if x > 5) / len(rs),
            }
    big = sorted(rows, key=lambda r: -r["abs_gap_points"])[:5]
    lag_hist = Counter(round(r["lag_bars"]) for r in rows)
    return {
        "symbol": symbol, "timeframe": tf, "bars": len(bars),
        "legal_signal_bars": sum(sm),
        "legal_signal_bars_with_a_non_contiguous_next_bar": len(rows),
        "share_of_legal_signal_bars": len(rows) / max(1, sum(sm)),
        "min_stop_points": min_dist,
        "lag_bars_histogram": dict(sorted(lag_hist.items())),
        "gap_points": {
            "median_abs": st.median([r["abs_gap_points"] for r in rows]) if rows else None,
            "max_abs": max((r["abs_gap_points"] for r in rows), default=None),
        },
        "r_impact_by_stop": per_mult,
        "largest_five": big,
    }


def main() -> None:
    out = {"cells": {}}
    for sym in ("MGC", "MCL"):
        for tf in (60, 240):
            r = audit(sym, tf)
            out["cells"][f"{sym}:{tf}m"] = r
            sys.stderr.write(f"{sym} {tf}m: {r['legal_signal_bars_with_a_non_contiguous_next_bar']} "
                             f"gap fills of {r['legal_signal_bars']} legal signal bars\n")
    with open(os.path.join(OUT, "weekend_gap.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print("| cell | legal signal bars | with a non-contiguous next bar | share | "
          "median abs gap | max abs gap |")
    print("|---|---|---|---|---|---|")
    for k, r in out["cells"].items():
        print(f"| `{k}` | {r['legal_signal_bars']:,} | "
              f"{r['legal_signal_bars_with_a_non_contiguous_next_bar']} | "
              f"{r['share_of_legal_signal_bars']*100:.2f}% | "
              f"{r['gap_points']['median_abs']:.4f} | "
              f"{r['gap_points']['max_abs']:.4f} |")
    print()
    print("| cell | stop | n | median R | p90 R | **max R** | share >2R | share >5R |")
    print("|---|---|---|---|---|---|---|---|")
    for k, r in out["cells"].items():
        for m, v in r["r_impact_by_stop"].items():
            print(f"| `{k}` | {m} | {v['n']} | {v['median_R']:.2f} | "
                  f"{v['p90_R']:.2f} | **{v['max_R']:.2f}** | "
                  f"{v['share_over_2R']*100:.1f}% | {v['share_over_5R']*100:.1f}% |")
    print()
    for k, r in out["cells"].items():
        print(f"**{k}** five largest gaps:")
        for b in r["largest_five"]:
            print(f"  - {b['ts']} -> {b['next_ts']} "
                  f"({b['lag_bars']:.0f} bars): {b['gap_points']:+.4f} pts"
                  + (f", {b['abs_gap_in_atr']:.2f} ATR" if b['abs_gap_in_atr'] else ""))


if __name__ == "__main__":
    main()
