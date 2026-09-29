"""EF5 shared substrate loader for the SCALP cell (MES, MNQ at 5m/15m/30m).

One loader, so every EF5 number is measured on the same bars and the substrate
is named in one place.

Substrate: ``data/archive/{SYM}_{TF}m.jsonl`` (append-only store, ET-stamped).
Verified against the frozen ``csv/raw`` snapshot in
``bursts/01_census_scope_and_power.md`` -- bit-exact on close for every
overlapping bar at 5m/15m/30m on both symbols except the final (developing)
bar of the csv/raw snapshot.

Session rule of this programme: a position may exist only inside
18:00 ET -> 16:00 ET. So the ONLY excluded clock window is 16:00-18:00 ET.
:func:`in_session` is that predicate and nothing more; it is deliberately
separate from ``rth_only``, which is a far narrower gate (09:30-16:00).
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
from typing import Dict, List, Sequence, Tuple
from zoneinfo import ZoneInfo

REPO = "/home/user/Futures01"
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from futures_agents.data.bars import Bar, BarSeries          # noqa: E402
from futures_agents.features import build_symbol_frame        # noqa: E402

ET = ZoneInfo("America/New_York")
ARCHIVE = os.path.join(REPO, "data", "archive")

#: EF5's cell. Primary timeframes, each with the frame it is read inside.
#: These are the repo's own ``futures_agents.scout.FRAMES`` entries for 5/15/30,
#: adopted unchanged so the census and the population share a configuration with
#: prior work rather than inventing a new one.
CELL_FRAMES: Dict[int, List[int]] = {
    5: [5, 15, 60],
    15: [15, 60, 240],
    30: [30, 60, 240],
}
#: The "timeframe alone" control arm: the same primary tf with no companions.
SOLO_FRAMES: Dict[int, List[int]] = {5: [5], 15: [15], 30: [30]}
#: The explicit scalp group arm named in the programme brief.
GROUP_FRAMES: Dict[int, List[int]] = {5: [5, 15, 30], 15: [5, 15, 30], 30: [5, 15, 30]}

SYMBOLS = ("MES", "MNQ")
PRIMARY_TFS = (5, 15, 30)


def load_series(symbol: str, tf: int) -> BarSeries:
    """Native archive bars for one (symbol, timeframe). No resampling."""
    path = os.path.join(ARCHIVE, f"{symbol}_{tf}m.jsonl")
    bars: List[Bar] = []
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            bars.append(Bar(
                ts=dt.datetime.fromisoformat(r["ts"]), minutes=tf,
                open=float(r["o"]), high=float(r["h"]), low=float(r["l"]),
                close=float(r["c"]), volume=float(r["v"]),
            ))
    bars.sort(key=lambda b: b.ts)
    # D-candidate (BarSeries.append collapses equal timestamps, BRIEF.md):
    # assert the constructed length equals the intended length rather than
    # trusting the container.
    n_intended = len(bars)
    series = BarSeries(symbol, tf, bars)
    assert len(series) == n_intended, (
        f"{symbol} {tf}m: BarSeries collapsed {n_intended - len(series)} bars "
        "sharing a timestamp")
    return series


def build_frame(symbol: str, primary_tf: int, frames: Dict[int, List[int]] = None):
    """Frame for one cell, based on that cell's own native bars."""
    frames = frames or CELL_FRAMES
    series = load_series(symbol, primary_tf)
    return build_symbol_frame(series, frames[primary_tf])


def in_session(ts: dt.datetime) -> bool:
    """True when a position may exist under the 18:00 ET -> 16:00 ET rule.

    The rule excludes exactly one window: 16:00 <= t < 18:00 ET. A bar stamped
    at 16:00 opens the excluded window, so it is out.
    """
    t = ts.astimezone(ET)
    mins = t.hour * 60 + t.minute
    return not (16 * 60 <= mins < 18 * 60)


def session_id(ts: dt.datetime) -> dt.date:
    """The 18:00->16:00 cycle a bar belongs to, keyed by its END date.

    18:30 Monday and 10:00 Tuesday are the same cycle. Matches
    ``futures_agents.timeutil.trading_day`` for the 18:00 boundary.
    """
    t = ts.astimezone(ET)
    if t.hour >= 18:
        return (t + dt.timedelta(days=1)).date()
    return t.date()


def span_years(series: BarSeries) -> float:
    a, b = series.bars[0].ts, series.bars[-1].ts
    return (b - a).total_seconds() / (365.25 * 86400.0)


def et_stats(series: BarSeries) -> dict:
    ts = [b.ts for b in series.bars]
    sess = sorted({session_id(t) for t in ts})
    return dict(
        bars=len(ts), first=ts[0].astimezone(ET).isoformat(),
        last=ts[-1].astimezone(ET).isoformat(),
        calendar_days=(ts[-1] - ts[0]).days,
        span_years=round(span_years(series), 4),
        sessions_18_16=len(sess),
        in_session_bars=sum(1 for t in ts if in_session(t)),
    )
