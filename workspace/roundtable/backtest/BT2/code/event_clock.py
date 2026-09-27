"""A parameterised, look-ahead-free clock on the scheduled-event calendar.

Why this exists at all, given ``features.py`` already computes three news
fields. Two reasons, both structural rather than stylistic:

1. **The library's clock is hard-wired to HIGH impact.**
   ``futures_agents/features.py:972-973`` filters the projected list with
   ``if e.impact.rank >= Impact.HIGH.rank`` *before* computing proximity, so
   every MEDIUM and LOW rule in ``ECON_RULES`` is invisible to every condition
   in the library no matter what the calendar contains. The window widths are
   equally fixed: ``NEWS_BLACKOUT_BEFORE_MIN`` / ``NEWS_BLACKOUT_AFTER_MIN``
   (10 / 15) come off ``AccountConfig`` (``config.py:410-411``) and the
   post-event window's upper bound is the literal ``60.0`` at
   ``library.py:1358``. None of the three is a parameter anywhere.
2. **BT2 owns ``backtest/BT2/**`` and nothing else.** Making impact rank or
   window width variable inside ``features.py`` is not a change this agent may
   make, so the clock is re-derived here from the same public primitive
   (``econ_calendar.project_events``) instead.

The fidelity guarantee that makes that defensible is in ``test_algo1.py``:
configured with ``min_impact=HIGH`` and offset 0, this module reproduces
``FeatureSnapshot.minutes_to_high_impact``, ``minutes_since_high_impact`` and
``in_news_blackout`` **bar for bar** on real MGC and MCL series. It is a strict
generalisation of the library's clock, not a second opinion about it. Any
difference a measurement shows is therefore attributable to the parameter that
was changed and not to the plumbing.

Three correctness properties, each with a test:

* **No look-ahead.** The clock is a pure function of the bar's own timestamp and
  the recurrence rules, which project identically backwards and forwards
  (``econ_calendar.py:8-14``). Appending a future bar cannot change a
  historical value, and
  ``test_appending_a_bar_never_changes_a_historical_reading`` asserts the prefix
  is identical.
* **Span independence.** Events are cached per *calendar year*, padded 15 days
  either side and then filtered back to the year, so an event shifted across a
  year boundary by ``holiday_shift`` is neither lost nor duplicated. The answer
  for one bar does not depend on which series it happens to sit in - a property
  ``features.py`` does not have, because its projection window is
  ``bars[0] - 2d .. bars[-1] + 45d``.
* **Loud failure.** ``EventClockError`` derives from ``RuntimeError``, which is
  *not* in the tuple ``Condition.evaluate`` swallows (``base.py:131-133``:
  TypeError, ValueError, ZeroDivisionError, KeyError, IndexError). A
  misconfigured clock therefore aborts the sweep instead of returning ``no()``
  on every bar. That is the D38 lesson applied: D38's whole cost was that
  ``measure_custom`` returned zero rather than raising.

**Which instant inside a bar the clock is read at is an explicit parameter, not
an inference.** ``Bar.ts`` is the bar's OPEN (``bars.py:37``), and
``features.py`` reads the calendar there. But the signal decision is made at the
bar's *close* - ``snapshot(i)`` carries ``price=bar.close`` - and the entry fills
at the *next* bar's open (``engine.py:296-300``). So a clock read at the open is
stale by one bar length by the time the trade exists. ``offset_min`` exposes
that rather than hiding it: ``0.0`` reproduces ``features.py``, and passing the
bar length reads the clock at the decision instant. Nothing is inferred from the
snapshot, because a snapshot does not carry its own base bar length and guessing
it from ``min(snap.tfs)`` is wrong whenever the frame's base is finer than its
finest requested timeframe.
"""

from __future__ import annotations

import bisect
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from futures_agents.config import ContractSpec, get_contract          # noqa: E402
from futures_agents.econ_calendar import (EconEvent, Impact,          # noqa: E402
                                          project_events)
from futures_agents.timeutil import is_rth, to_et, trading_day        # noqa: E402

__all__ = ["EventClockError", "EventClock", "Reading", "census", "CensusRow"]


class EventClockError(RuntimeError):
    """Raised when the clock is asked for something it cannot answer.

    Deliberately a ``RuntimeError`` subclass so ``Condition.evaluate`` does not
    swallow it into ``ConditionResult.no()``. See the module docstring.
    """


#: Padding either side of a calendar year when projecting it. A weekly or
#: ``empsit`` rule shifted off a federal holiday can move a few days, and
#: ``_rule_dates`` deliberately does not month-filter those patterns
#: (``econ_calendar.py:366-372``), so an event can cross a year boundary.
#: Projecting the padded span and filtering back to the year keeps it.
_YEAR_PAD_DAYS = 15

#: (symbol, min_impact_rank, year) -> events in that calendar year, sorted.
_YEAR_CACHE: Dict[Tuple[str, int, int], Tuple[EconEvent, ...]] = {}


def _year_events(symbol: str, min_rank: int, year: int) -> Tuple[EconEvent, ...]:
    """Every qualifying event whose Eastern timestamp falls in ``year``.

    Cached, because a two-year hourly sweep asks for the same three years on
    every one of ~11,000 bars.
    """
    key = (symbol, min_rank, year)
    hit = _YEAR_CACHE.get(key)
    if hit is not None:
        return hit
    lo = datetime(year, 1, 1) - timedelta(days=_YEAR_PAD_DAYS)
    hi = datetime(year, 12, 31, 23, 59) + timedelta(days=_YEAR_PAD_DAYS)
    evs = tuple(e for e in project_events(lo, hi, symbol=symbol)
                if e.impact.rank >= min_rank and e.when.year == year)
    _YEAR_CACHE[key] = evs
    return evs


@dataclass(frozen=True)
class Reading:
    """The clock's answer at one instant."""

    #: Minutes to the next qualifying release; ``inf`` when none is known ahead.
    to_next: float
    #: Minutes since the most recent qualifying release; ``inf`` when none.
    since_prev: float
    #: Minutes since the FIRST print of the episode ``since_prev`` belongs to.
    #: Equal to ``since_prev`` unless ``cluster_minutes`` folded a run of
    #: closely-spaced prints together - see :class:`EventClock`.
    since_episode: float
    #: Name of the release ``since_prev`` is measured from, or ``None``.
    prev_name: Optional[str]
    #: Name of the first release of that episode, or ``None``.
    episode_name: Optional[str]
    #: Name of the release ``to_next`` is measured to, or ``None``.
    next_name: Optional[str]


_NOTHING = Reading(float("inf"), float("inf"), float("inf"), None, None, None)


class EventClock:
    """Event proximity for one symbol at any instant, from recurrence rules only.

    ``min_impact`` is the whole point of the class existing: the library is
    frozen at HIGH.

    ``cluster_minutes`` handles the overlap case, and it is reported as a
    *separate field* rather than by redefining ``since_prev``, because the two
    readings are wanted by different gates. Two qualifying prints can land close
    enough that the second resets the first's post-event window - the FOMC
    statement at 14:00 and its press conference at 14:30 do it on every meeting
    day, and on the nearest-print reading the statement's drift window is
    silently truncated at 30 minutes. With ``cluster_minutes=k``, prints within
    ``k`` minutes of their predecessor are folded into one *episode* anchored on
    the FIRST print of the run, which is what an operator watching one event
    range does. ``since_prev`` (nearest print) is what an *avoidance* gate must
    use, since clustering would shorten its blackout; ``since_episode`` is what
    a *drift* gate wants. Both are always present, so neither gate has to
    reconstruct the other's convention.
    """

    def __init__(self, symbol: str, *, min_impact: Impact = Impact.HIGH,
                 cluster_minutes: float = 0.0) -> None:
        self.symbol = symbol.upper()
        self.min_impact = min_impact
        self.min_rank = min_impact.rank
        if cluster_minutes < 0:
            raise EventClockError(
                f"cluster_minutes must be >= 0, got {cluster_minutes}")
        self.cluster_minutes = float(cluster_minutes)
        self.spec: ContractSpec = get_contract(self.symbol)

    # ---- event access -------------------------------------------------
    def events(self, lo: datetime, hi: datetime) -> List[EconEvent]:
        """Qualifying events in ``[lo, hi]``, Eastern, sorted."""
        a, b = to_et(lo), to_et(hi)
        if b < a:
            return []
        out: List[EconEvent] = []
        for year in range(a.year, b.year + 1):
            out.extend(e for e in _year_events(self.symbol, self.min_rank, year)
                       if a <= e.when <= b)
        return out

    def _window(self, ts: datetime) -> Tuple[List[EconEvent], List[datetime]]:
        """The three calendar years around ``ts``, and their timestamps.

        Three years rather than one so a bar in early January can see the
        previous December's prints and a bar in late December the next
        January's. The gap between two HIGH prints never approaches a year, so
        three is generous; the cost is one list concatenation per distinct year.
        """
        y = ts.year
        evs: List[EconEvent] = []
        for yr in (y - 1, y, y + 1):
            evs.extend(_year_events(self.symbol, self.min_rank, yr))
        evs.sort(key=lambda e: e.when)
        return evs, [e.when for e in evs]

    # ---- the reading --------------------------------------------------
    def read(self, when: datetime) -> Reading:
        """Proximity at one instant. Pure function of ``when`` and the rules."""
        ts = to_et(when)
        evs, stamps = self._window(ts)
        if not evs:
            return _NOTHING

        # bisect_left / bisect_right: an event landing exactly ON ``ts`` counts
        # as both ahead (to_next = 0) and behind (since_prev = 0), which is what
        # features.py does - its ``ahead`` test is ``e.when >= ts`` and its
        # ``behind`` test is ``e.when <= ts``. Reproducing that is deliberate: a
        # bar opening exactly at the print is on both sides of it.
        j = bisect.bisect_left(stamps, ts)
        next_ev = evs[j] if j < len(evs) else None

        i = bisect.bisect_right(stamps, ts) - 1
        prev_ev = evs[i] if i >= 0 else None

        head_ev = prev_ev
        if prev_ev is not None and self.cluster_minutes > 0:
            # Walk back to the head of the episode: keep stepping to the earlier
            # print while the gap to it is inside the cluster window.
            k = i
            while k > 0:
                gap = (evs[k].when - evs[k - 1].when).total_seconds() / 60.0
                if gap > self.cluster_minutes:
                    break
                k -= 1
            head_ev = evs[k]

        to_next = (float("inf") if next_ev is None
                   else (next_ev.when - ts).total_seconds() / 60.0)
        since = (float("inf") if prev_ev is None
                 else (ts - prev_ev.when).total_seconds() / 60.0)
        since_ep = (float("inf") if head_ev is None
                    else (ts - head_ev.when).total_seconds() / 60.0)
        return Reading(to_next, since, since_ep,
                       prev_ev.name if prev_ev else None,
                       head_ev.name if head_ev else None,
                       next_ev.name if next_ev else None)

    def read_bar(self, ts: datetime, offset_min: float = 0.0) -> Reading:
        """Proximity for a bar whose OPEN is ``ts``, read ``offset_min`` later.

        ``offset_min=0`` is ``features.py``'s convention. Passing the bar length
        reads the clock at the instant the signal decision is made, which is
        also the instant the entry fills when the next bar is contiguous.
        """
        return self.read(to_et(ts) + timedelta(minutes=float(offset_min)))


# --------------------------------------------------------------------------
# Census - how many events this contract's own session can actually see
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class CensusRow:
    """The event arithmetic for one (symbol, series) pair, before any backtest.

    This is R2-D5's table, recomputed independently. It is a count of calendar
    events against a bar clock; it contains no price, no trade and no
    expectancy. Reproducing R2's 7 / 32 / 49 is the cheapest available check
    that this module's event plumbing agrees with the research it implements.
    """

    symbol: str
    minutes: int
    bars: int
    first_ts: datetime
    last_ts: datetime
    rth_open: str
    rth_close: str
    min_impact: str
    events_in_span: int
    events_in_rth: int
    event_days_in_rth: int
    by_rule_in_rth: Dict[str, int]


def census(symbol: str, bars: Sequence, *, min_impact: Impact = Impact.HIGH
           ) -> CensusRow:
    """Count qualifying events over a bar series, split by the contract's own RTH.

    ``bars`` is any sequence of ``Bar``. The RTH test uses
    ``ContractSpec.rth_open`` / ``rth_close`` through ``timeutil.is_rth`` - the
    contract's own session, never a global 09:30-16:00. R2's first pass used the
    equity session and got MGC (08:20-13:30) and MCL (09:00-14:30) wrong before
    self-correcting; reading the spec is how that mistake is made unrepeatable
    rather than merely avoided.
    """
    if not bars:
        raise EventClockError(f"{symbol}: census on an empty series")
    clock = EventClock(symbol, min_impact=min_impact)
    spec = clock.spec
    first, last = to_et(bars[0].ts), to_et(bars[-1].ts)
    # The span a strategy could act inside runs to the END of the last bar.
    evs = clock.events(first, last + timedelta(minutes=int(bars[-1].minutes)))
    in_rth = [e for e in evs if is_rth(e.when, spec.rth_open, spec.rth_close)]
    by_rule: Dict[str, int] = {}
    for e in in_rth:
        by_rule[e.name] = by_rule.get(e.name, 0) + 1
    return CensusRow(
        symbol=symbol.upper(), minutes=int(bars[0].minutes), bars=len(bars),
        first_ts=first, last_ts=last,
        rth_open=spec.rth_open, rth_close=spec.rth_close,
        min_impact=min_impact.value,
        events_in_span=len(evs), events_in_rth=len(in_rth),
        event_days_in_rth=len({trading_day(e.when) for e in in_rth}),
        by_rule_in_rth=dict(sorted(by_rule.items())),
    )
