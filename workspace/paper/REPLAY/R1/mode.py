#!/usr/bin/env python3
"""Which desk mode applies right now: 1 agent or 3.

Account owner's rule (2026-09-28): run 3 agents while the futures market is
CLOSED, and drop back to 1 agent 30 minutes before it opens.

CME equity index futures (MES) trade Sunday 18:00 ET -> Friday 17:00 ET with a
daily maintenance halt 17:00-18:00 ET. So CLOSED means:
  * the daily halt, 17:00-18:00 ET Monday-Thursday
  * the weekend, Friday 17:00 ET -> Sunday 18:00 ET
and the 30-minute pre-open cutback puts the desk back to 1 agent from 17:30 ET
(daily) and from Sunday 17:30 ET (weekend).

ASSUMPTION WORTH CHECKING WITH THE OWNER: "closed" is read as the exchange's own
close (17:00 ET), not the RTH close (16:00 ET) and not the account's own 16:00
flat deadline. If the owner meant the RTH session, change CLOSE_H to 16 - the
daily 3-agent window then runs 16:00-17:30 instead of 17:00-17:30. One constant.
"""
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
CLOSE_H, OPEN_H, PRE_OPEN_MIN = 17, 18, 30


def mode(now=None):
    """Returns (agents, state, reason)."""
    n = (now or datetime.now(ET)).astimezone(ET)
    dow, hm = n.weekday(), n.hour * 60 + n.minute      # Mon=0 .. Sun=6
    close, open_, cut = CLOSE_H * 60, OPEN_H * 60, OPEN_H * 60 - PRE_OPEN_MIN

    # weekend: Fri from 17:00 -> Sun 18:00
    if (dow == 4 and hm >= close) or dow == 5 or (dow == 6 and hm < open_):
        if dow == 6 and hm >= cut:
            return 1, "PRE_OPEN", "within 30 min of the Sunday 18:00 ET reopen"
        return 3, "CLOSED_WEEKEND", "weekend close, Fri 17:00 ET -> Sun 18:00 ET"

    # daily maintenance halt, Mon-Thu (and Sun evening is already open)
    if dow <= 3 and close <= hm < open_:
        if hm >= cut:
            return 1, "PRE_OPEN", "within 30 min of the 18:00 ET reopen"
        return 3, "CLOSED_HALT", "daily maintenance halt, 17:00-18:00 ET"

    return 1, "OPEN", "futures market open"


if __name__ == "__main__":
    n = datetime.now(ET)
    a, st, why = mode(n)
    print(f"ET now {n:%Y-%m-%d %H:%M %a}   ->  {a} AGENT(S)   [{st}]   {why}")
    print("\nnext 8 transitions:")
    prev = (a, st)
    t = n
    shown = 0
    while shown < 8:
        t += timedelta(minutes=1)
        cur = mode(t)[:2]
        if cur != prev:
            print(f"  {t:%a %Y-%m-%d %H:%M ET}  ->  {cur[0]} agent(s)  [{cur[1]}]")
            prev = cur
            shown += 1
