#!/usr/bin/env python3
"""Daily loss limit (owner, 2026-09-29 10:15 ET: "increase your drawdown to 1k" -> chose "Daily loss
limit $1,000"). The trading day runs 18:00 ET -> 18:00 ET. Once REALIZED net P&L of trades closed in the
current trading day is <= -$1,000, no new plans for the rest of that trading day. Per-trade sizing and the
$2,600 drawdown floor are unchanged.  python3 daily_loss.py  prints today's figure."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
ET = ZoneInfo("America/New_York")
DAILY_LOSS_LIMIT = 1000.0


def day_start(now_utc: datetime) -> datetime:
    et = now_utc.astimezone(ET)
    start = et.replace(hour=18, minute=0, second=0, microsecond=0)
    if et < start:
        start -= timedelta(days=1)
    return start


def day_realized(state: dict, now_utc: datetime | None = None) -> float:
    now_utc = now_utc or datetime.now(timezone.utc)
    s = day_start(now_utc)
    tot = 0.0
    for c in state.get("closed", []) or []:
        t = c.get("closed_at_utc")
        if t and datetime.fromisoformat(t) >= s:
            tot += float(c.get("net") or 0)
    return round(tot, 2)


def limit_hit(state: dict, now_utc: datetime | None = None) -> bool:
    return day_realized(state, now_utc) <= -DAILY_LOSS_LIMIT


if __name__ == "__main__":
    st = json.loads((HERE / "state.json").read_text())
    r = day_realized(st)
    print(f"trading day since {day_start(datetime.now(timezone.utc)):%Y-%m-%d %H:%M %Z}: realized ${r:,.2f} "
          f"vs limit -${DAILY_LOSS_LIMIT:,.0f} -> {'HIT: no new plans today' if r <= -DAILY_LOSS_LIMIT else 'ok'}")
