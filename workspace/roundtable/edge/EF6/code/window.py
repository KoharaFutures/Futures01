"""EF6 — the 18:00 ET -> 16:00 ET window, as a bar-level predicate.

**Scope, so this is not mistaken for EF1's work.** EF1 owns the *engine* rule
that closes a position at 16:00 ET and refuses an entry between 16:00 and
18:00. This module owns the *accounting* predicate that every EF6 control and
every EF6 firing census applies, so that a placebo, a firing rate and a
realised backtest are all counted over the same set of bars. If EF1's engine
rule and this predicate ever disagree, the controls are measured on a different
universe from the thing they control, and the control is easier than the thing
it controls - which is exactly the failure the brief names.

The rule, restated as arithmetic:

* A position may exist only when the bar's ET time-of-day is in
  ``[18:00, 16:00)`` - i.e. **not** in ``[16:00, 18:00)``.
* ``timeutil.SESSIONS`` already names that forbidden span exactly:
  ``POST_CLOSE = 16:00 -> 18:00`` `[repo-verified: futures_agents/timeutil.py:120-122]`.
  So the predicate is not a new convention, it is the existing one negated.
* Entries fill at the **next** bar's open `[repo-verified:
  futures_agents/backtest/engine.py:293-299, _open_position fills at bar.open]`,
  so a signal on bar *i* is only legal if bar *i+1* is itself in the window.
  A census that forgets this over-counts eligible signals at the 15:00 slot.

## The measured problem this module exists to surface

A bar is the atom. If a bar *straddles* 16:00 or 18:00 the rule cannot be
expressed at that bar size at all, and the honest options are both wrong:

`[measured: python3 over data/archive, ET time-of-day histogram per timeframe]`

| tf | bars wholly inside 16:00-18:00 | bars STRADDLING a boundary |
|---|---|---|
| 5m, 15m, 30m, 60m | yes (60m: 489 stamped 16:00, 6 stamped 17:00) | none - every boundary falls on a bar edge |
| **240m** | none | **586 bars stamped 16:00 ET span 16:00-20:00**, i.e. two forbidden hours followed by two legal ones |
| 1440m | none | every bar (stamped 00:00 ET, spans 24h) |

At 240m the 18:00 reopen is **not on the bar grid**. Excluding the 16:00 bar
discards the Globex reopen, which is the one regime this programme says is
unmeasured; including it holds through 16:00-18:00, which the rule forbids.
:func:`straddle_report` returns this per (symbol, timeframe) so no one has to
discover it inside a result.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from futures_agents.timeutil import ET, to_et

__all__ = [
    "FLAT_AT", "REOPEN_AT", "MAX_HOLD_MINUTES",
    "in_window", "bar_status", "eligible_signal_index", "window_mask",
    "signal_mask", "straddle_report", "cycle_id",
]

FLAT_AT = time(16, 0)     # must be flat AT and after this, until...
REOPEN_AT = time(18, 0)   # ...this
#: The longest hold the rule permits: 18:00 -> 16:00 = 22 hours.
MAX_HOLD_MINUTES = 22 * 60


def in_window(ts: datetime) -> bool:
    """May a position exist on a bar stamped ``ts``? (Bar-open convention.)

    True everywhere except ET ``[16:00, 18:00)``.
    """
    t = to_et(ts).time()
    return not (FLAT_AT <= t < REOPEN_AT)


def bar_status(ts: datetime, minutes: int) -> str:
    """``"IN"``, ``"OUT"`` or ``"STRADDLE"`` for a bar of ``minutes`` duration.

    ``STRADDLE`` means the bar contains 16:00 or 18:00 strictly inside it, so
    the rule cannot be applied to it without either breaking the rule or
    discarding a legal part of the bar. It is a *defect report*, not a third
    trading state, and nothing in EF6 trades a STRADDLE bar.
    """
    d = to_et(ts)
    start = d
    end = d + timedelta(minutes=int(minutes))
    # Walk the boundaries that fall in (start, end).
    day = start.date()
    for off in (-1, 0, 1):
        base = datetime.combine(day + timedelta(days=off), time(0, 0), tzinfo=ET)
        for b in (FLAT_AT, REOPEN_AT):
            bt = datetime.combine(base.date(), b, tzinfo=ET)
            if start < bt < end:
                return "STRADDLE"
    return "IN" if in_window(ts) else "OUT"


def window_mask(bars: Sequence, minutes: Optional[int] = None) -> List[bool]:
    """Per-bar: may a position exist on this bar? STRADDLE counts as False."""
    out = []
    for b in bars:
        if minutes is None:
            out.append(in_window(b.ts))
        else:
            out.append(bar_status(b.ts, minutes) == "IN")
    return out


def signal_mask(bars: Sequence, minutes: Optional[int] = None) -> List[bool]:
    """Per-bar: may a SIGNAL on this bar produce a legal entry?

    The engine fills at the next bar's open, so the constraint is on bar
    ``i + 1``, not on bar ``i``. The last bar is always False - there is no
    next bar to fill on.
    """
    wm = window_mask(bars, minutes)
    return [wm[i + 1] if i + 1 < len(wm) else False for i in range(len(wm))]


def eligible_signal_index(bars: Sequence, minutes: Optional[int] = None) -> List[int]:
    """Indices of bars whose signal could legally be filled."""
    sm = signal_mask(bars, minutes)
    return [i for i, ok in enumerate(sm) if ok]


def cycle_id(ts: datetime) -> str:
    """Which 18:00->16:00 cycle a bar belongs to, as ``YYYY-MM-DD``.

    The cycle is labelled by the calendar date of its **16:00 close**, so an
    18:30 Monday bar and a 10:00 Tuesday bar share a label. This is the unit a
    "swing" trade lives inside and the unit a walk-forward fold should not cut
    through. Note it is *not* ``timeutil.trading_day``, which rolls at 18:00 to
    the CME's 17:00 close convention - close enough to be confused for this and
    different enough to misassign the 16:00-18:00 bars, which this function
    assigns to the *next* cycle because nothing may be held in them.
    """
    d = to_et(ts)
    if d.time() >= REOPEN_AT:
        return (d + timedelta(days=1)).date().isoformat()
    if d.time() >= FLAT_AT:          # 16:00-18:00: belongs to nothing tradeable
        return (d + timedelta(days=1)).date().isoformat()
    return d.date().isoformat()


def straddle_report(bars: Sequence, minutes: int) -> dict:
    """How much of a series the rule can and cannot be applied to."""
    n = len(bars)
    counts = {"IN": 0, "OUT": 0, "STRADDLE": 0}
    straddle_slots: Dict[str, int] = {}
    for b in bars:
        s = bar_status(b.ts, minutes)
        counts[s] += 1
        if s == "STRADDLE":
            k = to_et(b.ts).strftime("%H:%M")
            straddle_slots[k] = straddle_slots.get(k, 0) + 1
    sm = signal_mask(bars, minutes)
    return {
        "n_bars": n, "minutes": int(minutes),
        "in_window": counts["IN"], "out_of_window": counts["OUT"],
        "straddle": counts["STRADDLE"],
        "straddle_slots": straddle_slots,
        "pct_in_window": round(100.0 * counts["IN"] / max(1, n), 2),
        "eligible_signal_bars": sum(sm),
        "pct_eligible_signal": round(100.0 * sum(sm) / max(1, n), 2),
        "expressible": counts["STRADDLE"] == 0,
    }
