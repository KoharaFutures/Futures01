"""EF2: can the 16:00 flat FIRE in every cycle, on MGC and MCL?

EF3 measured that EF1's ``classify_bar`` under-enforces the flat on **19 of 507
MES/MNQ sessions (3.75%)**: a session whose last bar is ``OUTSIDE`` has no bar for
the rule to fire on, so a position runs through the deadline - EF3's worst case was
a **71-hour** hold across two 16:00 deadlines, which is the multi-day thesis the
EDGE_BRIEF says is out of scope by arithmetic.

EF3's cell is MES+MNQ. **MGC is COMEX and MCL is NYMEX, and their early-close and
holiday calendars are not the equity complex's**, so the count does not transfer
and the independence rule says measure it. This does.

Method, which needs no engine and no tape:
  For each 18:00 ET -> 16:00 ET cycle present in the series, ask whether the series
  contains at least one bar EF1's rule can act on at that cycle's deadline - i.e.
  a bar classified ON_BOUNDARY (ends exactly at 16:00) or IN_WINDOW (starts inside
  [16:00, 18:00)). A cycle with neither is a cycle in which a position opened can
  survive past 16:00 with the rule reporting success.
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import timedelta
from typing import Dict, List

REPO = "/home/user/Futures01"
for p in (REPO, os.path.join(REPO, "workspace", "roundtable", "edge", "EF1", "code"),
          os.path.dirname(os.path.abspath(__file__))):
    if p not in sys.path:
        sys.path.insert(0, p)

from futures_agents.data.bars import resample                  # noqa: E402
from futures_agents.timeutil import to_et                      # noqa: E402
from session_window import BarWindow, classify_bar             # noqa: E402
from substrate import base_series                              # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")


def cycle_key(ts) -> str:
    """The 18:00->16:00 cycle a bar belongs to, named by its END date (ET).

    A bar stamped at or after 18:00 belongs to the cycle ending the NEXT day;
    anything earlier belongs to the cycle ending today.
    """
    et = to_et(ts)
    end = et.date() + timedelta(days=1) if et.hour >= 18 else et.date()
    return end.isoformat()


def check(symbol: str, tf: int) -> dict:
    s = base_series(symbol, 60)
    if tf != 60:
        s = resample(s, tf, keep_partial=False)
    bars = s.bars
    per: Dict[str, Counter] = {}
    first_last: Dict[str, List[str]] = {}
    for b in bars:
        k = cycle_key(b.ts)
        c = per.setdefault(k, Counter())
        c[classify_bar(b.ts, b.minutes).value] += 1
        fl = first_last.setdefault(k, [None, None])
        et = to_et(b.ts).isoformat()
        if fl[0] is None:
            fl[0] = et
        fl[1] = et
    unreachable = []
    for k in sorted(per):
        c = per[k]
        if c.get(BarWindow.ON_BOUNDARY.value, 0) == 0 and \
           c.get(BarWindow.IN_WINDOW.value, 0) == 0 and \
           c.get(BarWindow.INTERIOR.value, 0) == 0:
            unreachable.append({"cycle_ends": k, "bars": sum(c.values()),
                                "first_bar": first_last[k][0],
                                "last_bar": first_last[k][1],
                                "classes": dict(c)})
    return {
        "symbol": symbol, "timeframe": tf, "bars": len(bars),
        "cycles": len(per),
        "cycles_where_the_flat_cannot_fire": len(unreachable),
        "share": round(len(unreachable) / max(1, len(per)), 4),
        "detail": unreachable,
        "class_totals": dict(sum(per.values(), Counter())),
    }


def main() -> None:
    out = {"cells": {}}
    for sym in ("MGC", "MCL"):
        for tf in (60, 240):
            r = check(sym, tf)
            out["cells"][f"{sym}:{tf}m"] = r
    with open(os.path.join(OUT, "flat_reachability.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("| cell | bars | cycles | **cycles where the 16:00 flat cannot fire** | share |")
    print("|---|---|---|---|---|")
    for k, r in out["cells"].items():
        print(f"| `{k}` | {r['bars']:,} | {r['cycles']} | "
              f"**{r['cycles_where_the_flat_cannot_fire']}** | {r['share']*100:.2f}% |")
    print()
    for k, r in out["cells"].items():
        print(f"**{k}** bar classes: {r['class_totals']}")
        if r["detail"]:
            print(f"  cycles with no actionable bar ({len(r['detail'])}):")
            for d in r["detail"][:40]:
                print(f"   - cycle ending {d['cycle_ends']}: {d['bars']} bars, "
                      f"{d['first_bar']} -> {d['last_bar']}, {d['classes']}")
        print()


if __name__ == "__main__":
    main()
