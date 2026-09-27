"""EF4 / burst 01 - the exact power bound for the scalp cell.

Pure arithmetic on the substrate. No strategy, no backtest, nothing to overfit.

The bound. Lo (2002): for an i.i.d. return series observed over ``Y`` years at an
annualised Sharpe ``SR``,  ``t = SR * sqrt(Y)``.  Inverted, the Sharpe a cell must
sustain to produce a given t is ``SR = t / sqrt(Y)``.  ``Y`` is *calendar* years of
observation - not bar count - because a Sharpe is an annualisation and the clock is
what annualises it.  Cutting a 57-day window into 5-minute bars instead of 30-minute
bars multiplies the bar count by six and changes ``Y`` not at all, which is the whole
point and the thing a bar-count intuition gets wrong.

A second, independent bound is reported beside it, because on a scalp cell the binding
constraint is often the *trade* count rather than the span: for a per-trade R series of
mean ``mu`` and sd ``sigma`` over ``N`` trades, ``t = (mu/sigma) * sqrt(N)``.  That one
says what per-trade expectancy-to-noise ratio N trades can resolve.  Both are reported;
the honest statement is that a row must clear both.

Also computed here: the number of 18:00 ET -> 16:00 ET sessions actually present in the
substrate, which is the unit the programme's session rule makes a strategy live in, and
the one that bounds how many independent non-overlapping holds can exist.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))

CELLS = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]
YEAR_DAYS = 365.25


def load_ts(symbol: str, minutes: int):
    p = ROOT / "data" / "archive" / f"{symbol}_{minutes}m.jsonl"
    out = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            out.append(datetime.fromisoformat(json.loads(line)["ts"]))
    out.sort()
    return out


def session_key(ts: datetime) -> str:
    """The 18:00 ET -> 16:00 ET cycle a bar belongs to.

    A bar at or after 18:00 belongs to the cycle *labelled by the next calendar
    day*; a bar before 16:00 belongs to the cycle labelled by its own day.  Bars
    in the 16:00-18:00 maintenance gap belong to no cycle and are returned as
    ``GAP`` - under the programme rule no position may exist in them at all.
    """
    if ts.hour >= 18:
        return (ts.date() + timedelta(days=1)).isoformat()
    if ts.hour < 16:
        return ts.date().isoformat()
    return "GAP"


def free_t(n: int) -> float:
    return math.sqrt(2.0 * math.log(max(2, n)))


def main() -> None:
    rows = []
    for sym, tf in CELLS:
        ts = load_ts(sym, tf)
        n = len(ts)
        cal_days = (ts[-1] - ts[0]).total_seconds() / 86400.0
        years = cal_days / YEAR_DAYS
        keys = [session_key(t) for t in ts]
        sessions = sorted({k for k in keys if k != "GAP"})
        gap_bars = sum(1 for k in keys if k == "GAP")
        rows.append({
            "symbol": sym, "tf": tf, "bars": n,
            "first": ts[0].isoformat(), "last": ts[-1].isoformat(),
            "calendar_days": round(cal_days, 2),
            "years": round(years, 5),
            "sqrt_years": round(math.sqrt(years), 4),
            "sessions_18_16": len(sessions),
            "bars_in_1600_1800_gap": gap_bars,
            "bars_per_session": round((n - gap_bars) / len(sessions), 1),
            # Sharpe required to produce t, on this span
            "SR_for_t_1.177_single_prereg": round(1.177 / math.sqrt(years), 3),
            "SR_for_t_1.96_nominal_5pct": round(1.96 / math.sqrt(years), 3),
            "SR_for_t_3.923_largest_ever_here": round(3.923 / math.sqrt(years), 3),
        })

    print(f"{'cell':<10}{'bars':>7}{'cal.d':>8}{'years':>8}{'sqrtY':>7}"
          f"{'sess':>6}{'gapbar':>8}{'b/sess':>8}"
          f"{'SR@1.177':>10}{'SR@1.96':>9}{'SR@3.923':>10}")
    for r in rows:
        print(f"{r['symbol']+' '+str(r['tf'])+'m':<10}{r['bars']:>7}"
              f"{r['calendar_days']:>8.2f}{r['years']:>8.4f}{r['sqrt_years']:>7.3f}"
              f"{r['sessions_18_16']:>6}{r['bars_in_1600_1800_gap']:>8}"
              f"{r['bars_per_session']:>8.1f}"
              f"{r['SR_for_t_1.177_single_prereg']:>10.2f}"
              f"{r['SR_for_t_1.96_nominal_5pct']:>9.2f}"
              f"{r['SR_for_t_3.923_largest_ever_here']:>10.2f}")

    print()
    print("search-width thresholds, free_t = sqrt(2 ln n):")
    for k in (1, 10, 100, 1000, 5000, 20000, 100000):
        print(f"  n={k:>7}  free_t={free_t(k):.3f}   "
              f"SR needed on 0.157y = {free_t(k)/math.sqrt(0.157):.2f}")

    print()
    print("trade-count bound: per-trade (mu/sigma) needed for t = 1.177 and 1.96")
    for N in (20, 30, 50, 100, 200, 400, 800):
        print(f"  N={N:>4}  mu/sigma@1.177={1.177/math.sqrt(N):.4f}   "
              f"mu/sigma@1.96={1.96/math.sqrt(N):.4f}")

    out = ROOT / "workspace/roundtable/edge/EF4/out/power_bound.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
