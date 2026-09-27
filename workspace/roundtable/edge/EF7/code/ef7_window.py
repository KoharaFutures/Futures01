"""EF7: the 18:00 ET -> 16:00 ET session window, built from the specification only.

This is an **independent second implementation** of the rule EF1 is also building.
Its purpose is to be written without reading the first one, so that where the two
agree the agreement is evidence and where they disagree there is something to look
at. The independence declaration lives in ``../FINDINGS.md`` section 0.

The specification, restated so the code can be read against it:

    A position may exist only inside 18:00 ET -> 16:00 ET the following day.
    Nothing may be held across 16:00-18:00 ET. No new position opened in that
    window.

Three components, with ids:

* **EF7-H1** :class:`SessionWindow` - the clock predicate. Pure, offset-agnostic,
  DST-correct because it works in ``America/New_York`` wall time via
  :func:`futures_agents.timeutil.to_et` rather than off a fixed UTC offset. The
  archive carries both ``-04:00`` and ``-05:00`` stamps (switching 2024-11-03)
  and ``csv/raw`` carries ``+00:00``, so anything that reads ``ts.hour`` directly
  is right on one store and four hours wrong on the other.

* **EF7-H2** :func:`cycle_keys` / :meth:`SessionWindowEngine._flat_at` - which bar
  is the last bar of a cycle. This is the part the obvious implementation gets
  wrong; see the note on ``end_ts >= 16:00`` below.

* **EF7-H3** :class:`SessionWindowEngine` - the engine. A subclass, not a fork:
  every shipped invariant (signal on closed bars, entry at the next bar's open,
  stop before target, gaps fill at the open, costs charged once) is inherited
  rather than re-implemented, because re-implementing them is how they get lost.

Why the rule cannot be configured, verified independently (see burst 01):

* ``exit_at_session_close`` fires at ``minutes_since_open(bar.ts, spec.rth_open)
  + bar.minutes >= self._rth_minutes`` (``engine.py:470-473``), i.e. at the
  *contract's own* RTH close: 13:30 for MGC, 14:30 for MCL, 16:00 for MES/MNQ.
* it is gated on ``not self.allow_overnight``, so enabling overnight **removes**
  the exit instead of moving it.
* ``allow_overnight`` defaults to ``False`` and nothing inside ``futures_agents/``
  passes ``True``.

So this engine forces ``allow_overnight=True`` - which makes the shipped exit
inert - and installs the 16:00 ET flat in its place.

**The naive flat is wrong and this is the reason for EF7-H2.** "Close when
``bar.end_ts >= 16:00``" reads correctly and is correct on 489 of 506 MGC 60m
cycles. On the other 17 - and 35 of 505 on MCL - the cycle's last printed bar
ends at 14:00, 13:30 or 00:00, no bar satisfies ``end_ts >= 16:00`` until one that
*opens* at 16:00 or later, and the position exits inside the forbidden window or
is carried straight across it. The flat therefore has to know whether the next
bar is still in the same cycle. That reads the successor bar's **timestamp** and
nothing else - no successor price, high, low, close or volume - and the claim is
discharged by test (``tests/test_ef7_session_window.py``:
``test_h2_flat_decision_ignores_successor_prices`` and the prefix-invariance
tests), not asserted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

from futures_agents.backtest.costs import CostModel
from futures_agents.backtest.engine import (BacktestEngine, BacktestResult,
                                            ExitReason, Trade, _OpenPosition)
from futures_agents.data.bars import Bar
from futures_agents.features import SymbolFrame
from futures_agents.strategies.base import Strategy
from futures_agents.timeutil import ET, is_rth, to_et

__all__ = [
    "SessionGridError", "WindowExitReason", "SESSION_WINDOW_EXIT", "SessionWindow", "SESSION_WINDOW",
    "cycle_keys", "flat_flags", "entry_veto_flags", "WindowStats",
    "SessionWindowEngine",
]


class SessionGridError(ValueError):
    """The base grid cannot express a 16:00 ET flat at all.

    Raised up front by :meth:`SessionWindowEngine._audit_grid` rather than
    discovered as a violation at bar 9,000. Adopted from EF1 (`EF1-F3`) - see
    that method's docstring for why raising beats counting here.
    """


class WindowExitReason(str, Enum):
    """The one exit reason the shipped :class:`ExitReason` does not have.

    Deliberately a separate enum rather than an edit to
    ``futures_agents/backtest/engine.py``: reusing ``SESSION_CLOSE`` would make
    the 16:00 ET flat indistinguishable from the contract-RTH exit it replaces,
    and the whole point of measuring this rule is being able to count how often
    it fires. It is a ``str`` enum for the same reason the shipped one is, so
    ``metrics.py:244``'s ``t.exit_reason.value`` and ``storage.py``'s TEXT column
    both keep working untouched.
    """

    SESSION_WINDOW = "SESSION_WINDOW"


SESSION_WINDOW_EXIT = WindowExitReason.SESSION_WINDOW


# --------------------------------------------------------------------------
# EF7-H1 - the clock
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class SessionWindow:
    """The 18:00 ET -> 16:00 ET holding window, as a pure predicate on instants.

    A *cycle* runs from 18:00 ET on one calendar day to 16:00 ET the next, and is
    named by the **date of its terminating 16:00 flat** - so the cycle opening
    18:00 Monday is cycle Tuesday. The complement, ``[16:00, 18:00)``, is the
    forbidden window: no position may exist in it and no position may be opened
    in it.

    Every method takes an arbitrary ``datetime`` and normalises it with
    :func:`to_et` first. That is not defensive politeness - the two stores in
    this repository disagree about offsets (``data/archive/`` is ET with both
    ``-04:00`` and ``-05:00``; ``csv/raw`` is ``+00:00``) and half the bars in the
    archive are on the other side of a DST switch from the other half. Reading
    ``ts.hour`` is correct on one store, one hour out on 3,807 of 11,297 MGC
    archive bars if a fixed ``-04:00`` is assumed, and four hours out on
    ``csv/raw``.
    """

    #: Wall-clock ET time at which a cycle opens.
    open_time: time = time(18, 0)
    #: Wall-clock ET time at which every position must be flat.
    flat_time: time = time(16, 0)

    # ---- the three primitives ---------------------------------------
    def is_forbidden(self, ts: datetime) -> bool:
        """``True`` inside ``[flat_time, open_time)`` - 16:00-18:00 ET."""
        t = to_et(ts).time()
        if self.flat_time <= self.open_time:
            return self.flat_time <= t < self.open_time
        # A window that wraps midnight; not the configured case, handled anyway.
        return t >= self.flat_time or t < self.open_time

    def is_admissible(self, ts: datetime) -> bool:
        """``True`` when a position may exist at, or be opened at, ``ts``."""
        return not self.is_forbidden(ts)

    def cycle_key(self, ts: datetime) -> Optional[date]:
        """Date of the 16:00 ET flat terminating ``ts``'s cycle, or ``None``.

        ``None`` means ``ts`` is inside the forbidden window and belongs to no
        cycle. That distinction is the reason this is not
        :func:`futures_agents.timeutil.trading_day`, which returns the *same*
        date for a 16:30 bar as for the 15:30 bar before it and so would silently
        glue the forbidden window onto the end of the preceding cycle. For every
        **admissible** instant the two agree, and
        ``test_h1_cycle_key_matches_trading_day_where_defined`` asserts it.
        """
        d = to_et(ts)
        if self.is_forbidden(d):
            return None
        if d.time() >= self.open_time:
            return (d + timedelta(days=1)).date()
        return d.date()

    def flat_instant(self, ts: datetime) -> Optional[datetime]:
        """The exact ET instant by which a position held at ``ts`` must be flat."""
        key = self.cycle_key(ts)
        if key is None:
            return None
        return datetime.combine(key, self.flat_time, tzinfo=ET)

    def open_instant(self, ts: datetime) -> Optional[datetime]:
        """The 18:00 ET instant at which ``ts``'s cycle opened."""
        key = self.cycle_key(ts)
        if key is None:
            return None
        return datetime.combine(key - timedelta(days=1), self.open_time, tzinfo=ET)

    def max_hold_minutes(self, ts: datetime) -> Optional[float]:
        """Minutes left in the cycle - the hold budget, for a sanity check.

        The full cycle is 22 hours, so no strategy under this rule can hold
        longer than 1,320 minutes, and a "multi-day swing" cannot be expressed
        at all. That is arithmetic, not an interpretation.
        """
        fi = self.flat_instant(ts)
        if fi is None:
            return None
        return (fi - to_et(ts)).total_seconds() / 60.0


#: The rule as specified. Constructed once; it is frozen and stateless.
SESSION_WINDOW = SessionWindow()


# --------------------------------------------------------------------------
# EF7-H2 - which bar is the last bar of a cycle
# --------------------------------------------------------------------------

def cycle_keys(bars: Sequence[Bar],
               window: SessionWindow = SESSION_WINDOW) -> List[Optional[date]]:
    """Per-bar cycle key. Index *i* uses only ``bars[i].ts``, so this is
    trivially prefix-invariant and is asserted to be."""
    return [window.cycle_key(b.ts) for b in bars]


def flat_flags(bars: Sequence[Bar], window: SessionWindow = SESSION_WINDOW,
               *, stop_at: Optional[int] = None) -> List[Optional[bool]]:
    """``flags[i]``: must a position open at bar *i* be closed at bar *i*'s close?

    ``None`` means **undetermined** rather than ``False``. The last bar of the
    series (or of the run window) has no successor, so whether it is the end of a
    cycle is genuinely unknowable from the data on hand; the engine closes it as
    ``END_OF_DATA``, which is what the shipped engine already does at
    ``engine.py:475-476``. Returning ``None`` rather than guessing is what makes
    the prefix-invariance statement exact: for every ``k``, the flags computed on
    ``bars[:k]`` agree with the flags computed on the whole series at every index
    where both are determined.

    The three ways a bar can be the last holdable bar of its cycle:

    1. the bar is itself inside the forbidden window - unreachable once the entry
       veto is in place, flagged anyway so the invariant cannot be violated by a
       path nobody thought of;
    2. the bar's own close is at or after the 16:00 deadline - impossible on this
       substrate (measured: 0 straddling bars at 15m/30m/60m/240m on all four
       symbols) but true of any bucketing that does not divide 16:00 evenly;
    3. the next bar belongs to a different cycle, or to no cycle. **This is the
       case that does the work**, and it is why the function needs the successor.
    """
    n = len(bars) if stop_at is None else min(int(stop_at), len(bars))
    keys = [window.cycle_key(bars[i].ts) for i in range(n)]
    out: List[Optional[bool]] = []
    for i in range(n):
        key = keys[i]
        if key is None:
            out.append(True)
            continue
        fi = window.flat_instant(bars[i].ts)
        if fi is not None and to_et(bars[i].end_ts) > fi:
            out.append(True)
            continue
        if i + 1 >= n:
            out.append(None)
            continue
        out.append(keys[i + 1] != key)
    return out


def entry_veto_flags(bars: Sequence[Bar], window: SessionWindow = SESSION_WINDOW,
                     *, stop_at: Optional[int] = None) -> List[Optional[bool]]:
    """``flags[i]``: must a signal fired on bar *i* be refused a fill?

    The signal is computed on bar *i*'s close and fills at bar *i+1*'s **open**
    (``engine.py:290-295`` and ``costs.py:61``), so the instant that has to be
    tested is ``bars[i+1].ts``, not ``bars[i].ts``. Getting that wrong by one bar
    is silent: it vetoes the 15:00 signal, which is legal, and admits the 16:00
    fill, which is not.

    Note what is **not** vetoed: a signal fired *on* a forbidden bar. The bar
    opening 17:00 closes at 18:00 and fills at the 18:00 bar's open, which is the
    first admissible instant of the next cycle. That is a legitimate overnight
    entry and refusing it would be stricter than the specification.
    """
    n = len(bars) if stop_at is None else min(int(stop_at), len(bars))
    out: List[Optional[bool]] = []
    for i in range(n):
        if i + 1 >= n:
            out.append(None)
            continue
        out.append(not window.is_admissible(bars[i + 1].ts))
    return out


# --------------------------------------------------------------------------
# EF7-H3 - the engine
# --------------------------------------------------------------------------

@dataclass
class WindowStats:
    """What the rule did, counted. A rule with no counters cannot be audited."""

    flat_exits: int = 0
    #: Base bars that contain 16:00 ET strictly inside them. Non-zero only when
    #: ``allow_straddling_grid=True``; otherwise the engine refuses to run.
    bars_straddling_deadline: int = 0
    #: Flats that fired on a bar whose own close is at or after the deadline.
    #: Must be 0 on this substrate; non-zero means a straddling bucket.
    flat_on_late_bar: int = 0
    #: Flats that fired on a bar inside the forbidden window. Must be 0 always;
    #: non-zero is a spec violation and means the entry veto leaked.
    flat_on_forbidden_bar: int = 0
    #: Flats that fired **early** because the cycle's data ended before 16:00.
    flat_before_deadline: int = 0
    entries_vetoed: int = 0
    #: Entries filled on a bar that is itself the cycle's last - a legal but
    #: degenerate one-bar trade. Counted because it is a plausible artefact.
    entries_flat_same_bar: int = 0
    #: Positions still open at the last bar of the run, closed END_OF_DATA.
    end_of_data_exits: int = 0
    #: Total slippage charged by the flat, in points, summed over flats.
    flat_slippage_points: float = 0.0

    def to_dict(self) -> dict:
        return {
            "bars_straddling_deadline": self.bars_straddling_deadline,
            "flat_exits": self.flat_exits,
            "flat_on_late_bar": self.flat_on_late_bar,
            "flat_on_forbidden_bar": self.flat_on_forbidden_bar,
            "flat_before_deadline": self.flat_before_deadline,
            "entries_vetoed": self.entries_vetoed,
            "entries_flat_same_bar": self.entries_flat_same_bar,
            "end_of_data_exits": self.end_of_data_exits,
            "flat_slippage_points": round(self.flat_slippage_points, 6),
        }


class SessionWindowEngine(BacktestEngine):
    """:class:`BacktestEngine` under the 18:00 ET -> 16:00 ET session window.

    Three behavioural differences from the shipped engine and nothing else:

    1. ``allow_overnight`` is forced ``True``. It is not a constructor parameter,
       because every value of it other than ``True`` makes the shipped
       contract-RTH exit fire *before* the 16:00 flat could and silently converts
       this back into the regime the programme has already measured 2.97M times.
       ``test_h3_shipped_session_exit_is_inert`` asserts behaviourally - not by
       reading the source - that no ``SESSION_CLOSE`` exit survives.

    2. A flat at the end of every cycle, filled at the bar's close **with
       market-order slippage**. The shipped time, session and end-of-data exits
       all hand ``bar.close`` straight to ``_close`` with no slippage term
       (``engine.py:467,473,476``); only the entry (``:353``) and the stop
       (``:416``) are charged. That is defensible for an exit that fires on a
       minority of trades and indefensible for one that fires on *every* trade
       that does not stop or target out first, which is what this flat is. A
       market-on-close order is a market order, so it is priced through the same
       ``is_stop=True`` branch the engine uses for stops - ``base_ticks`` plus
       ``stop_order_extra_ticks``, plus the volatility and thin-book terms
       (``costs.py:35-47``).

    3. An entry veto: a fill whose instant lies in ``[16:00, 18:00)`` is refused.

    Everything else is inherited: signals from ``snapshot(i)``, entry at the next
    bar's open, stop checked before target in the same bar, gaps filled at the
    open, one commission per side. The insertion point is chosen so the shipped
    precedence is preserved exactly - the parent's ``_manage`` is run to
    completion first, so a stop, a target, a breakeven, a trail or a time stop on
    the flat bar all still win, and the flat only fires on a position that had no
    other reason to close on that bar. That is deliberate: it is what makes
    ``WindowStats.flat_exits`` mean "positions the rule closed that would
    otherwise have run on" rather than a re-attribution of exits that were
    already happening.
    """

    def __init__(self, frame: SymbolFrame, cost_model: Optional[CostModel] = None,
                 *, max_concurrent_per_strategy: int = 1,
                 window: SessionWindow = SESSION_WINDOW,
                 flat_is_market_order: bool = True,
                 allow_straddling_grid: bool = False):
        super().__init__(frame, cost_model,
                         max_concurrent_per_strategy=max_concurrent_per_strategy,
                         allow_overnight=True)
        self.window = window
        self.flat_is_market_order = bool(flat_is_market_order)
        self.allow_straddling_grid = bool(allow_straddling_grid)
        self.stats = WindowStats()
        bars = frame.base.bars
        # Pure per-bar, no successor: safe to precompute once.
        self._keys: List[Optional[date]] = [window.cycle_key(b.ts) for b in bars]
        self._stop_at: int = len(bars)
        self._audit_grid()

    # ---- grid audit, before any number is produced ----------------------
    def _audit_grid(self) -> None:
        """Refuse a base grid on which the flat cannot be priced at all.

        **Adopted from EF1 (`EF1-F3`) after my own results were written**, and it
        is a genuine gap in my first build: I *counted* a straddling bar
        (``WindowStats.flat_on_late_bar``) and carried on, which means the run
        would have produced a post-deadline fill and reported a number beside it.
        Counting a violation you could have refused to produce is the weaker of
        the two designs, so this raises.

        The case that matters is the daily grid. ``align_bucket`` puts a 1440m
        bucket at 18:00 ET the previous evening
        (``futures_agents/data/bars.py:145-149``), so 16:00 ET falls **22 hours
        inside every daily bar** - the entry fill and the flat land in the same
        bar and OHLC cannot price hour 22. Independently reproduced on my own
        clock: `[measured: MGC 4008/4008, MES 1863/1863, MNQ 1863/1863, MCL 1/1
        daily bars straddle 16:00 ET]`. So **there is no daily-bar strategy under
        this rule**, which is arithmetic rather than a preference.

        Every finer grid is clean: 15m/30m/60m/240m have **zero** straddling bars
        on all four symbols, even though the 60m grid is not uniformly on the hour
        (20 bars per symbol are stamped ``:30``, on the five half-day sessions).
        That is why the rule classifies per bar and never assumes the grid.
        """
        bars = self.frame.base.bars
        straddling = 0
        first: Optional[Bar] = None
        for b in bars:
            fi = self.window.flat_instant(b.ts)
            if fi is not None and to_et(b.end_ts) > fi:
                straddling += 1
                if first is None:
                    first = b
        self.stats.bars_straddling_deadline = straddling
        if straddling and not self.allow_straddling_grid:
            raise SessionGridError(
                f"{self.frame.symbol}: {straddling} of {len(bars)} base bars "
                f"({self.base_minutes}m) contain 16:00 ET strictly inside them, "
                f"first {to_et(first.ts).isoformat()} -> "
                f"{to_et(first.end_ts).isoformat()}. The close of such a bar is a "
                "post-deadline price, so the 16:00 flat cannot be priced from its "
                "OHLC. A 1440m grid is 100% straddling by construction. Use a "
                "finer base series, or pass allow_straddling_grid=True and accept "
                "that the flat is then priced at the bar's adverse extreme."
            )

    # ---- run -----------------------------------------------------------
    def run_many(self, strategies: Sequence[Strategy], *, start: int = 0,
                 end: Optional[int] = None,
                 progress: Optional[Any] = None) -> Dict[str, BacktestResult]:
        """Record the run window, then defer entirely to the shipped loop.

        ``_stop_at`` matters: without it a run with ``end=k`` would decide bar
        ``k-1``'s flat from ``bars[k]``, which is outside the window it was asked
        to test. That is exactly the leak the prefix-invariance check looks for,
        so it is closed here rather than tested around.
        """
        n = len(self.frame.base.bars)
        self._stop_at = n if end is None else max(0, min(int(end), n))
        self.stats = WindowStats()
        return super().run_many(strategies, start=start, end=end,
                               progress=progress)

    # ---- EF7-H2, evaluated inside the run window ------------------------
    def _flat_at(self, i: int) -> Optional[bool]:
        """Must a position open at base bar *i* close at bar *i*'s close?

        Reads ``bars[i+1].ts`` and nothing else about bar *i+1*.
        """
        bars = self.frame.base.bars
        key = self._keys[i]
        if key is None:
            return True
        fi = self.window.flat_instant(bars[i].ts)
        if fi is not None and to_et(bars[i].end_ts) > fi:
            return True
        j = i + 1
        if j >= self._stop_at:
            return None
        return self._keys[j] != key

    # ---- component 2: the entry veto ------------------------------------
    def _open_position(self, strategy: Strategy, sig, i: int,
                       bar: Bar) -> Optional[_OpenPosition]:
        """Refuse any fill whose instant is inside 16:00-18:00 ET.

        ``bar`` is the *entry* bar and the fill is at ``bar.open``
        (``engine.py:355``), so ``bar.ts`` is the fill instant.
        """
        if not self.window.is_admissible(bar.ts):
            self.stats.entries_vetoed += 1
            return None
        pos = super()._open_position(strategy, sig, i, bar)
        if pos is not None and self._flat_at(i) is True:
            self.stats.entries_flat_same_bar += 1
        return pos

    # ---- components 1 and 3: the flat, and its fill ---------------------
    def _flat_fill(self, pos: _OpenPosition, bar: Bar,
                   *, raw: Optional[float] = None) -> Tuple[float, float]:
        """(fill price, slippage in points) for the market flat.

        ``raw`` is the pre-slippage reference price and defaults to ``bar.close``,
        which is the right one on the normal case: the flat fires on the bar whose
        close *is* 16:00. The caller overrides it to ``bar.open`` on the two
        degenerate bars where the close is a **post-deadline** price - a bar
        inside the forbidden window, or one straddling the deadline. Filling at
        the close there would report a price the order could never have got, and
        it is the difference between a compliant exit and a violation. **Adopted
        from EF1** after my own results were written; both paths are unreachable
        in my design (the entry veto closes the first, ``_audit_grid`` the
        second), and "unreachable" is a claim about today's data, not a guarantee.
        """
        atr_pct = self._atr_percentile(pos.signal)
        thin = not is_rth(bar.ts, self.spec.rth_open, self.spec.rth_close)
        slip = self.costs.slippage_price(is_stop=self.flat_is_market_order,
                                         atr_percentile=atr_pct, thin=thin)
        base = bar.close if raw is None else raw
        return self.spec.round_to_tick(base - pos.sign * slip), slip

    def _manage(self, pos: _OpenPosition, i: int, bar: Bar,
                *, is_last: bool) -> Optional[Trade]:
        """Run the shipped ladder, then the flat, then end-of-data.

        ``is_last=False`` is passed down on purpose. The parent's last action is
        an unconditional ``END_OF_DATA`` close (``engine.py:475-476``), which
        would pre-empt the flat on the final bar and mislabel it; the flat is
        checked here and end-of-data is re-applied afterwards, so the ordering is
        stop -> target -> breakeven/trail -> time -> **flat** -> end-of-data.
        """
        trade = super()._manage(pos, i, bar, is_last=False)
        if trade is not None:
            return trade

        if self._flat_at(i) is True:
            st = self.stats
            raw: Optional[float] = None
            if self._keys[i] is None:
                # Inside the forbidden window: the close is post-deadline, so the
                # resting market order fills at the first print there is - the
                # open - gap and all. Unreachable while the entry veto holds.
                st.flat_on_forbidden_bar += 1
                raw = bar.open
            else:
                fi = self.window.flat_instant(bar.ts)
                end = to_et(bar.end_ts)
                if fi is not None and end > fi:
                    # Straddles the deadline: same reasoning. Unreachable unless
                    # allow_straddling_grid was passed.
                    st.flat_on_late_bar += 1
                    raw = bar.open
                elif fi is not None and end < fi:
                    st.flat_before_deadline += 1
            fill, slip = self._flat_fill(pos, bar, raw=raw)
            st.flat_exits += 1
            st.flat_slippage_points += slip
            return self._close(pos, i, bar, fill, SESSION_WINDOW_EXIT)

        if is_last:
            self.stats.end_of_data_exits += 1
            return self._close(pos, i, bar, bar.close, ExitReason.END_OF_DATA)
        return None


# --------------------------------------------------------------------------
# Trade-level invariant, usable on any list of trades from any engine
# --------------------------------------------------------------------------

def trade_violations(trades: Sequence[Trade],
                     window: SessionWindow = SESSION_WINDOW,
                     *, base_minutes: int = 60) -> List[dict]:
    """Every way a realised trade can breach the rule, as a list of records.

    The list being empty is the deliverable, so the function is written to be
    able to find things: a check that has never rejected anything is untested,
    and ``tests/test_ef7_session_window.py`` feeds it deliberate breaches to
    prove each clause fires.

    Three clauses:

    * ``entry_in_window`` - the fill instant is inside 16:00-18:00 ET;
    * ``exit_in_window`` - the exit could have filled inside 16:00-18:00 ET.
      ``Trade.exit_ts`` is the exit **bar's open** time (``engine.py:505``), and
      the fill itself lands somewhere in that bar, so the whole bar has to be
      admissible: either it opens inside the window, or it runs past the 16:00
      deadline. A bar ending exactly *at* 16:00 is the flat and is not a breach.
      Testing ``exit_ts`` alone would pass a trade that filled at 16:59;
    * ``spans_window`` - entry and exit sit in different cycles, which means the
      position was held across at least one forbidden window even if neither
      endpoint is inside one. This is the clause that catches a rule that
      remembered to move the exit and forgot to fire it.
    """
    out: List[dict] = []
    for t in trades:
        entry = to_et(t.entry_ts)
        # Trade carries no bar duration, so it is supplied by the caller. The
        # engine manages positions on BASE bars, so base_minutes is the right
        # unit even for a 240m strategy running on a 60m base.
        exit_open = to_et(t.exit_ts) if t.exit_ts else entry
        exit_end = exit_open + timedelta(minutes=base_minutes)
        if window.is_forbidden(entry):
            out.append({"kind": "entry_in_window", "strategy_id": t.strategy_id,
                        "entry": entry.isoformat(), "exit": exit_open.isoformat()})
        fi = window.flat_instant(exit_open)
        if window.is_forbidden(exit_open) or (fi is not None and exit_end > fi):
            out.append({"kind": "exit_in_window", "strategy_id": t.strategy_id,
                        "entry": entry.isoformat(), "exit": exit_open.isoformat(),
                        "exit_bar_end": exit_end.isoformat(),
                        "reason": t.exit_reason.value})
        ck_in, ck_out = window.cycle_key(entry), window.cycle_key(exit_open)
        if ck_in is not None and ck_out is not None and ck_in != ck_out:
            out.append({"kind": "spans_window", "strategy_id": t.strategy_id,
                        "entry": entry.isoformat(), "exit": exit_open.isoformat(),
                        "entry_cycle": ck_in.isoformat(),
                        "exit_cycle": ck_out.isoformat(),
                        "reason": t.exit_reason.value})
    return out
