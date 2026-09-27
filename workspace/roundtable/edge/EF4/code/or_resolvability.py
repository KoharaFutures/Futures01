"""EF4 / burst 04 - is the OPENING_RANGE object the library builds actually a
30-minute opening range, per cell?

The scan report ``scan_reports/2026-09-24_ORB-and-ICT.md`` states the rule: an
L-minute range resolves on a T-minute frame iff ``T | L`` and ``T | RTH-open-in-minutes``.
It also records that on MCL the library "silently built a 30-minute range 60 minutes
wide". Both are claims about other timeframes; neither was measured at 5/15/30 on MGC
and MCL, which is my cell. So this measures the object directly rather than deducing it.

``SymbolFrame._build_session_state`` (features.py:862-895) hard-codes ``or_minutes = 30``
and accumulates every RTH bar whose ``minutes_since_open < 30``, marking the range
complete on the first RTH bar at or past 30 minutes. So the constructed window is
whatever set of base bars happens to land inside that test - not necessarily a
30-minute window, and not necessarily starting at the open.

MGC opens 08:20 = 500 minutes; 500 % 15 = 5 and 500 % 30 = 20, so MGC 15m and 30m fail
the divisibility rule and MGC 5m passes. MCL opens 09:00 = 540; 540 is divisible by
5, 15 and 30, so all three MCL cells pass. This script checks whether the arithmetic
prediction matches the object on disk.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))

from futures_agents.config import get_contract      # noqa: E402
from futures_agents.data.archive import BarArchive   # noqa: E402
from futures_agents.features import SymbolFrame      # noqa: E402
from futures_agents.timeutil import is_rth, minutes_since_open, trading_day  # noqa: E402

rows = []
for sym in ("MGC", "MCL"):
    spec = get_contract(sym)
    oh, om = (int(x) for x in spec.rth_open.split(":"))
    open_min = oh * 60 + om
    for tf in (5, 15, 30):
        series = BarArchive(str(ROOT / "data/archive")).load(sym, tf)
        # which base bars land in the OR accumulation window, per trading day
        per_day = {}
        for b in series.bars:
            if not is_rth(b.ts, spec.rth_open, spec.rth_close):
                continue
            mso = minutes_since_open(b.ts, spec.rth_open)
            if 0 <= mso < 30:
                per_day.setdefault(trading_day(b.ts), []).append((mso, b))
        widths = Counter()
        firsts = Counter()
        nbars = Counter()
        for day, lst in per_day.items():
            lst.sort()
            msos = [m for m, _ in lst]
            span = (msos[-1] + tf) - msos[0]
            widths[span] += 1
            firsts[msos[0]] += 1
            nbars[len(lst)] += 1
        divisible = (30 % tf == 0) and (open_min % tf == 0)
        rows.append({
            "symbol": sym, "tf": tf, "rth_open": spec.rth_open,
            "rth_open_minutes": open_min,
            "resolvable_by_rule": divisible,
            "days_with_an_OR": len(per_day),
            "OR_width_minutes_histogram": dict(widths),
            "OR_first_bar_mso_histogram": dict(firsts),
            "OR_bar_count_histogram": dict(nbars),
        })
        print(f"{sym} {tf:>2}m  open={spec.rth_open} ({open_min}m)  "
              f"rule-resolvable={str(divisible):<5} days={len(per_day):<3} "
              f"width(min)={dict(widths)}  first_mso={dict(firsts)}  bars={dict(nbars)}")

out = ROOT / "workspace/roundtable/edge/EF4/out/or_resolvability.json"
out.write_text(json.dumps(rows, indent=2))
print(f"\nwrote {out}")
