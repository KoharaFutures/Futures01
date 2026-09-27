"""EF1 — the 18:00 ET -> 16:00 ET session-window rule.

The rule, in one sentence
-------------------------
A position may exist only inside 18:00 ET -> 16:00 ET the following day: flat at
16:00 ET, no new position opened between 16:00 and 18:00 ET, holding through the
Globex session and the next RTH open permitted.

Why this is code and not a flag
-------------------------------
``ExitModel.exit_at_session_close`` closes at the *contract's own RTH close* -
``minutes_since_open(bar.ts, spec.rth_open) + bar.minutes >= self._rth_minutes``
`[repo-verified: futures_agents/backtest/engine.py:470-473]` - which is **13:30
for MGC** and 14:30 for MCL, not 16:00. And it is gated on
``not self.allow_overnight``, so enabling overnight *removes* the session exit
rather than moving it. ``allow_overnight`` is ``False`` by default and no call
site in the tree passes ``True``
`[measured: grep -rn allow_overnight --include=*.py . -> engine.py:233,241,470 only]`,
so the regime this programme needs has never run here.

Three components, built here rather than configured
---------------------------------------------------
1. **A flat at 16:00 ET on wall-clock time.** ``classify_bar`` compares the
   bar's **ET minute-of-day**, taken through ``to_et`` (``ZoneInfo`` -
   ``futures_agents/timeutil.py:20``), against 960 and 1080. It is not
   RTH-relative and it is not UTC-offset arithmetic, so it is correct on both
   sides of the 2024-11-03 / 2025-03-09 / 2025-11-02 / 2026-03-08 transitions
   that ``data/archive/`` spans.

2. **An entry veto for 16:00-18:00 ET.** Applied at the **fill** bar, which is
   where the position is actually opened. A signal *computed* on the 16:00-17:00
   bar whose fill lands at 18:00 is legal under the rule as written; set
   ``veto_signals_in_window=True`` for the stricter reading.

3. **A gap-honest fill at the flat.** R3 found every time-based and session exit
   in this repo closes at ``bar.close`` with **zero slippage by construction**
   (`engine.py:467,473,476`). The 16:00 flat is a market order and it fires on
   *every* position, so inheriting that defect would understate the cost of the
   defining rule of the programme. Here:

   ===================  ===========================================  =========
   bar class            fill                                         slippage
   ===================  ===========================================  =========
   ``ON_BOUNDARY``      ``bar.close`` - the 16:00 print               market-order slippage, adverse
   ``IN_WINDOW``        ``bar.open`` - the deadline passed with no    market-order slippage, adverse;
                        print, so the resting order fills at the      **none** if the open already
                        first one, gap and all                       gapped through the stop, which
                                                                     is then a STOP at the open
   ``INTERIOR``         16:00 falls strictly inside the bar, so       n/a - raises
                        ``bar.close`` is a post-deadline price
   ===================  ===========================================  =========

   The ``IN_WINDOW`` branch is not hypothetical. ``MCL 60m 2026-03-06`` has no
   14:00 and no 15:00 bar; the last print before the deadline closes at 91.28
   and the 16:00 bar opens at 90.90. Closing at ``bar.close`` of the last bar
   before would invent 38 cents - $38 a contract, a third of an R on a
   100-tick stop `[measured: data/archive/MCL_60m.jsonl]`.

What this deliberately does not do
----------------------------------
- **It does not touch ``futures_agents/``.** ``SessionWindowEngine`` subclasses
  ``BacktestEngine`` and overrides two methods. ``run_many`` calls
  ``_open_position`` for every pending fill and ``_manage`` for every open
  position `[repo-verified: engine.py:291-302]`, and returning ``None`` from
  ``_open_position`` cleanly drops the entry while leaving
  ``signals_generated`` incremented - so a veto is visible in the result rather
  than silent. Depending on two underscore-prefixed methods is real coupling;
  :func:`assert_hooks_reachable` fails loudly if a future refactor of
  ``engine.py`` routes around either of them, which is the difference between a
  gate and a rubber stamp.

- **It does not fix the zero-slippage TIME exit** (``engine.py:467``). That is a
  pre-existing defect in code EF1 does not own; it is reported to the manager
  with its measured exposure instead. Under this rule a hold is capped at 22
  hours, so ``time_stop_bars=60`` is inert at 60m and 240m and live at 5m/15m.

- **It does not work on 1440m.** ``align_bucket`` puts a daily bucket at 18:00
  ET the previous evening `[repo-verified: futures_agents/data/bars.py:139-143]`,
  so 16:00 falls 22 hours into *every* daily bar and the entry and the flat land
  inside the same bar. That is ``INTERIOR``, and it raises.

Look-ahead discipline
---------------------
:func:`classify_bar` is a pure function of ``(bar.ts, bar.minutes)`` - one bar,
no neighbours, no series. That is deliberate: a formulation like "bar *i* is the
flat bar iff ``bars[i+1].ts >= 16:00``" reads the future and would give a
different answer on a prefix ending at *i*. The hole case is handled by the
``IN_WINDOW`` branch, which also reads only its own bar, rather than by
"there is no bar ending at 16:00", which cannot be known without the future.
:func:`prefix_invariance_report` proves this over real bars.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from futures_agents.backtest.costs import CostModel
from futures_agents.backtest.engine import (BacktestEngine, ExitReason, Trade,
                                            _OpenPosition)
from futures_agents.data.bars import Bar
from futures_agents.features import SymbolFrame
from futures_agents.strategies.base import Strategy
from futures_agents.timeutil import is_rth, to_et

__all__ = [
    "FLAT_ET_MINUTE", "REOPEN_ET_MINUTE", "BarWindow", "SessionGridError",
    "et_minute_of_day", "classify_bar", "classify_series", "in_forbidden_window",
    "SessionWindowEngine", "SessionWindowCounters", "FlatEvent",
    "is_session_flat", "assert_hooks_reachable", "violations", "flat_exit_keys",
    "prefix_invariance_report", "with_exit", "assert_distinct_ids",
    "SessionWindowViolation", "session_end_indices",
]

#: 16:00 ET, in minutes since ET midnight. The deadline.
FLAT_ET_MINUTE = 16 * 60          # 960
#: 18:00 ET, in minutes since ET midnight. The reopen.
REOPEN_ET_MINUTE = 18 * 60        # 1080


class BarWindow(str, Enum):
    """Where one bar sits relative to the 16:00-18:00 ET forbidden window."""

    #: Entirely before 16:00 or entirely at/after 18:00. No action.
    OUTSIDE = "OUTSIDE"
    #: Ends exactly at 16:00. Its close is the 16:00 print; flatten there.
    ON_BOUNDARY = "ON_BOUNDARY"
    #: 16:00 falls strictly inside it. Its close is a post-deadline price.
    INTERIOR = "INTERIOR"
    #: Starts inside [16:00, 18:00). No position may exist on it and none may
    #: be opened on it.
    IN_WINDOW = "IN_WINDOW"


class SessionWindowViolation(AssertionError):
    """The engine was about to emit a trade that breaks the session window.

    Raised at emission rather than counted after the run. A count tells you
    something broke; this tells you *which trade*, and it makes it impossible
    for a later change to reintroduce a hole silently - which is exactly how
    EF1's own first build shipped 33 violations on early-close sessions.
    """


class SessionGridError(ValueError):
    """The bar grid cannot express a 16:00 ET flat.

    Raised rather than guessing a price, because the alternative - reading a
    daily bar's close as the 16:00 price - is a 22-hour look-ahead that would
    silently flatter every number downstream.
    """


# --------------------------------------------------------------------------
# The clock rule. Pure functions of one bar.
# --------------------------------------------------------------------------

def et_minute_of_day(ts: datetime) -> int:
    """Minutes since ET midnight for ``ts``.

    Goes through ``to_et``, so a stamp carrying ``-04:00`` and a stamp carrying
    ``-05:00`` both resolve to their true Eastern wall-clock time. This is the
    whole DST correctness argument: the comparison is against a wall-clock
    minute, never against a UTC offset.
    """
    d = to_et(ts)
    return d.hour * 60 + d.minute


def classify_bar(ts: datetime, minutes: int) -> BarWindow:
    """Classify one bar against the forbidden window. Reads nothing else.

    ``minutes`` arithmetic is done on the ET minute-of-day rather than with a
    ``timedelta`` on the timestamp: adding a ``timedelta`` to a zoneinfo-aware
    datetime does wall-clock arithmetic without re-normalising the offset, which
    is wrong across a DST transition. Integer minute arithmetic on the already
    converted ET representation has no such hazard.

    Bars that cross ET midnight are handled explicitly rather than by accident.
    A first cut compared ``start + minutes`` against 960 alone, which classified
    a daily bar stamped 18:00 as ``OUTSIDE`` - 1080 is neither below 960 nor
    inside [960, 1080) - and would have silently let every 1440m strategy run
    with no flat at all. The deadline a bar is tested against is therefore the
    **next** 16:00 after its own start, which for a bar starting at or after
    18:00 is tomorrow's.
    """
    start = et_minute_of_day(ts)
    end = start + int(minutes)
    if FLAT_ET_MINUTE <= start < REOPEN_ET_MINUTE:
        return BarWindow.IN_WINDOW
    # The next 16:00 strictly after this bar opens.
    deadline = FLAT_ET_MINUTE if start < FLAT_ET_MINUTE else FLAT_ET_MINUTE + 1440
    if end > deadline:
        return BarWindow.INTERIOR
    if end == deadline:
        return BarWindow.ON_BOUNDARY
    return BarWindow.OUTSIDE


def classify_series(bars: Sequence[Bar]) -> List[BarWindow]:
    """The classification of every bar, in order. Same length as the input."""
    return [classify_bar(b.ts, b.minutes) for b in bars]


def session_end_indices(bars: Sequence[Bar]) -> Dict[int, str]:
    """Bar indices that are a session's last chance to go flat before 16:00.

    Component **1b**, and it exists because the first build of this rule shipped
    33 violations. The per-bar rule can only fire on a bar that exists; on a
    session that shuts before 15:00 there is no bar ending at 16:00 and no bar
    starting inside the window, so neither branch ever gets a bar to act on and
    the position runs straight through into the next session. Measured on
    ``data/archive`` 60m: **9 such ET dates on MGC, 10 on MES and MNQ, 27 on
    MCL** - the exchange's early closes (Black Friday, both Christmas Eves,
    July 3rd, Juneteenth, Memorial Day, the day after Thanksgiving) plus, on
    MCL, a two-month stretch in early 2026 carrying 1-5 bars a day.

    A position open at 12:30 on Black Friday cannot be flattened at 16:00: the
    market is shut. Real-world compliance is to be flat by the early close, and
    a trader knows the early-close calendar weeks ahead.

    **What this reads, precisely.** Timestamps only. No price at any index is
    consulted, so the price-look-ahead invariant is untouched. What it is *not*
    is a pure per-bar function: it needs a date's full timestamp list, so on a
    prefix cut inside an early-close date the last entry can differ. That is
    stated rather than buried, and
    ``test_session_end_map_is_a_function_of_timestamps_only`` pins it down by
    perturbing every price and asserting the map does not move.

    Returns ``{bar_index: ET date iso}`` - a dict so the engine's per-bar test is
    a hash lookup rather than a scan.
    """
    by_date: Dict[object, List[int]] = {}
    kinds = classify_series(bars)
    for i, b in enumerate(bars):
        by_date.setdefault(to_et(b.ts).date(), []).append(i)
    out: Dict[int, str] = {}
    for day, idxs in by_date.items():
        if any(kinds[i] in (BarWindow.ON_BOUNDARY, BarWindow.IN_WINDOW)
               for i in idxs):
            continue                      # the normal rule has a bar to act on
        pre = [i for i in idxs
               if et_minute_of_day(bars[i].ts) < FLAT_ET_MINUTE]
        if pre:
            out[pre[-1]] = day.isoformat()
    return out


def in_forbidden_window(ts: datetime) -> bool:
    """Whether an *instant* falls in [16:00, 18:00) ET.

    The invariant assertion on realised trades uses this on entry and exit
    stamps. 18:00 itself is allowed; 16:00 itself is not.
    """
    return FLAT_ET_MINUTE <= et_minute_of_day(ts) < REOPEN_ET_MINUTE


# --------------------------------------------------------------------------
# Instrumentation
# --------------------------------------------------------------------------

@dataclass
class FlatEvent:
    """One firing of the 16:00 flat, recorded so the rule can be audited."""

    strategy_id: str
    entry_index: int
    exit_index: int
    exit_ts: datetime
    bar_class: BarWindow
    raw_price: float            # before slippage
    fill_price: float           # after slippage
    slippage_points: float
    gapped_through_stop: bool
    #: True when this was the session-end forced flat (component 1b) rather
    #: than a 16:00 deadline the session actually reached.
    forced_session_end: bool = False


@dataclass
class SessionWindowCounters:
    """Everything the rule did, so "it never rejected anything" is detectable."""

    entries_vetoed_in_window: int = 0
    entries_vetoed_signal_in_window: int = 0
    flats_on_boundary: int = 0
    flats_in_window: int = 0
    #: Component 1b: the session shut before 16:00, so the flat happened at the
    #: last bar it offered.
    flats_forced_session_end: int = 0
    flats_gapped_through_stop: int = 0
    bars_on_boundary: int = 0
    bars_in_window: int = 0
    bars_interior: int = 0
    bars_session_end: int = 0
    #: Fills whose bar starts more than two base bars after the signal bar
    #: closed - a stale entry, which the letter of the rule permits across the
    #: Friday-17:00-to-Sunday-18:00 break.
    stale_fills: int = 0
    flat_events: List[FlatEvent] = field(default_factory=list)

    @property
    def flats_total(self) -> int:
        return (self.flats_on_boundary + self.flats_in_window
                + self.flats_forced_session_end)

    def to_dict(self) -> dict:
        return {
            "entries_vetoed_in_window": self.entries_vetoed_in_window,
            "entries_vetoed_signal_in_window": self.entries_vetoed_signal_in_window,
            "flats_on_boundary": self.flats_on_boundary,
            "flats_in_window": self.flats_in_window,
            "flats_forced_session_end": self.flats_forced_session_end,
            "flats_total": self.flats_total,
            "flats_gapped_through_stop": self.flats_gapped_through_stop,
            "bars_on_boundary": self.bars_on_boundary,
            "bars_in_window": self.bars_in_window,
            "bars_interior": self.bars_interior,
            "bars_session_end": self.bars_session_end,
            "stale_fills": self.stale_fills,
        }


def is_session_flat(trade: Trade) -> bool:
    """Whether a trade was closed by the 16:00 flat.

    ``ExitReason`` is an enum in ``futures_agents`` and EF1 does not edit that
    package, so the flat reuses ``ExitReason.SESSION_CLOSE``. Inside
    :class:`SessionWindowEngine` that is unambiguous: the engine forces
    ``allow_overnight=True``, and the shipped RTH-close exit at
    ``engine.py:470`` is gated on ``not allow_overnight``, so it can never fire.
    ``SessionWindowCounters.flat_events`` carries the sub-classification.
    """
    return trade.exit_reason is ExitReason.SESSION_CLOSE


# --------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------

class SessionWindowEngine(BacktestEngine):
    """``BacktestEngine`` with the 18:00->16:00 ET session window enforced.

    ``allow_overnight`` is forced ``True`` and is not a parameter: under this
    rule a position is *expected* to survive its contract's RTH close, and
    leaving the shipped 13:30/14:30 exit armed would flatten it there instead.
    """

    def __init__(self, frame: SymbolFrame, cost_model: Optional[CostModel] = None,
                 *, max_concurrent_per_strategy: int = 1,
                 allow_interior: bool = False,
                 veto_signals_in_window: bool = False,
                 stale_fill_base_bars: int = 2,
                 strict: bool = True):
        super().__init__(frame, cost_model,
                         max_concurrent_per_strategy=max_concurrent_per_strategy,
                         allow_overnight=True)
        self.allow_interior = bool(allow_interior)
        self.veto_signals_in_window = bool(veto_signals_in_window)
        self.stale_fill_base_bars = int(stale_fill_base_bars)
        #: Audit every trade at the moment it is emitted rather than counting
        #: violations after the run. A count tells you something broke; an
        #: assertion tells you which trade, and makes it impossible for a later
        #: change to reintroduce the early-close hole silently.
        self.strict = bool(strict)
        self.counters = SessionWindowCounters()
        #: Set for the duration of one ``_flat`` -> ``_close`` call so the
        #: strict check knows the fill was at the bar's open.
        self._filling_at_open = False
        self._session_end = session_end_indices(frame.base.bars)
        self.counters.bars_session_end = len(self._session_end)
        self._audit_grid()

    # ---- grid audit, up front -------------------------------------------
    def _audit_grid(self) -> None:
        """Refuse a grid the rule cannot be expressed on, before any number.

        Counting first and raising once is deliberate: discovering at bar 9,000
        that the timeframe was never expressible wastes the run, and discovering
        it *never* is how a 22-hour look-ahead ships.
        """
        c = self.counters
        for b in self.frame.base.bars:
            k = classify_bar(b.ts, b.minutes)
            if k is BarWindow.ON_BOUNDARY:
                c.bars_on_boundary += 1
            elif k is BarWindow.IN_WINDOW:
                c.bars_in_window += 1
            elif k is BarWindow.INTERIOR:
                c.bars_interior += 1
        if c.bars_interior and not self.allow_interior:
            raise SessionGridError(
                f"{self.frame.symbol}: {c.bars_interior} of "
                f"{len(self.frame.base.bars)} base bars ({self.base_minutes}m) "
                "contain 16:00 ET strictly inside them, so their close is a "
                "post-deadline price and a 16:00 flat cannot be priced from "
                "OHLC. A 1440m grid is 100% INTERIOR by construction "
                "(align_bucket puts the daily bucket at 18:00 ET). Use a finer "
                "base series, or pass allow_interior=True and accept that the "
                "flat is then priced at the bar's adverse extreme.")
        if c.bars_on_boundary == 0 and c.bars_in_window == 0 and not c.bars_interior:
            raise SessionGridError(
                f"{self.frame.symbol}: no base bar ends at 16:00 ET, none starts "
                "inside [16:00, 18:00) ET and none contains 16:00, so the rule "
                "can never fire on this series. A rule that cannot fire is not a "
                "rule - it is an unmeasured regime wearing a rule's name.")

    # ---- component 2: the entry veto ------------------------------------
    def _open_position(self, strategy: Strategy, sig, i: int,
                       bar: Bar) -> Optional[_OpenPosition]:
        """Fill at this bar's open, unless the rule forbids opening here.

        ``bar`` is the *fill* bar, which is where the position actually comes
        into existence, so that is what the veto tests. ``run_many`` deletes the
        pending entry whether or not a position comes back
        `[repo-verified: engine.py:291-295]`, so returning ``None`` drops it
        cleanly and ``signals_generated`` stays incremented - the veto is
        visible in the result rather than silent.
        """
        if classify_bar(bar.ts, bar.minutes) is BarWindow.IN_WINDOW:
            self.counters.entries_vetoed_in_window += 1
            return None
        if self.veto_signals_in_window:
            sig_bar = self.frame.base.bars[sig.bar_index]
            if classify_bar(sig_bar.ts, sig_bar.minutes) is BarWindow.IN_WINDOW:
                self.counters.entries_vetoed_signal_in_window += 1
                return None
        # Staleness is measured in wall-clock minutes, not in bar indices. A
        # first cut compared ``i - sig.bar_index`` and reported zero stale fills
        # on the very case it exists for: a Friday-16:00 signal filling at
        # Sunday 18:00 is one index apart and fifty hours apart.
        sig_bar = self.frame.base.bars[int(sig.bar_index)]
        lag = (to_et(bar.ts) - to_et(sig_bar.ts)).total_seconds() / 60.0
        if lag > (self.stale_fill_base_bars + 1) * self.base_minutes:
            # Not a veto - the rule permits it. Counted because downstream
            # expectancy should know how many entries are this stale.
            self.counters.stale_fills += 1
        return super()._open_position(strategy, sig, i, bar)

    # ---- components 1 and 3: the flat, priced honestly -------------------
    def _manage(self, pos: _OpenPosition, i: int, bar: Bar,
                *, is_last: bool) -> Optional[Trade]:
        kind = classify_bar(bar.ts, bar.minutes)

        if kind is BarWindow.OUTSIDE:
            if i in self._session_end:
                # Component 1b: the session shuts before 16:00 and does not
                # reopen until 18:00, so this bar is the last chance to be flat.
                # Real exits get it first, exactly as on a normal boundary bar.
                trade = super()._manage(pos, i, bar, is_last=False)
                if trade is not None:
                    return trade
                return self._flat(pos, i, bar, kind, raw=bar.close,
                                  forced_session_end=True)
            return super()._manage(pos, i, bar, is_last=is_last)

        if kind is BarWindow.IN_WINDOW:
            # The deadline passed with no bar closing on it - a hole in the
            # series. The resting market order fills at the first print there
            # is, gap and all. Deliberately does NOT call super(): this bar's
            # high/low are post-deadline, so they must not move the stop check
            # or the excursions.
            return self._flat(pos, i, bar, kind, raw=bar.open)

        if kind is BarWindow.INTERIOR:
            if not self.allow_interior:
                raise SessionGridError(
                    f"{self.frame.symbol}: bar {to_et(bar.ts).isoformat()} "
                    f"({bar.minutes}m) contains 16:00 ET strictly inside it; "
                    "its close is a post-deadline price.")
            sign = pos.sign
            return self._flat(pos, i, bar, kind,
                              raw=(bar.low if sign > 0 else bar.high))

        # ON_BOUNDARY. Let the real exits have this bar first - stop before
        # target before flat - then flatten at the 16:00 print. ``is_last`` is
        # passed as False so an END_OF_DATA close, which is an accounting
        # artefact, cannot pre-empt a rule that would really have fired.
        trade = super()._manage(pos, i, bar, is_last=False)
        if trade is not None:
            return trade
        return self._flat(pos, i, bar, kind, raw=bar.close)

    def _flat(self, pos: _OpenPosition, i: int, bar: Bar, kind: BarWindow,
              *, raw: float, forced_session_end: bool = False) -> Trade:
        """Close ``pos`` at the flat, with market-order slippage applied once."""
        sign = pos.sign
        spec = self.spec
        # Reporting fields super()._manage would normally have set. The
        # IN_WINDOW path skips super() on purpose, so set them here.
        pos.bars_held = i - pos.entry_index + 1
        step = max(1, int(pos.strategy.primary_tf) // max(1, self.base_minutes))
        pos.primary_bars_held = (i - pos.entry_index) // step + 1

        gapped = (raw <= pos.stop) if sign > 0 else (raw >= pos.stop)
        if gapped and self.costs.fill.honour_gaps:
            # The market reopened through the stop. The engine's own rule for
            # this is fill at the open with no further slippage
            # `[repo-verified: engine.py:410-411]`, and the trade is a STOP,
            # not a flat - the stop was breached first in time.
            fill = spec.round_to_tick(raw)
            slip = 0.0
        else:
            slip = self.costs.slippage_price(
                is_stop=True,                       # a flat is a market order
                atr_percentile=self._atr_percentile(pos.signal),
                thin=not is_rth(bar.ts, spec.rth_open, spec.rth_close))
            fill = spec.round_to_tick(raw - sign * slip)

        c = self.counters
        if forced_session_end:
            c.flats_forced_session_end += 1
        elif kind is BarWindow.IN_WINDOW:
            c.flats_in_window += 1
        else:
            c.flats_on_boundary += 1
        if gapped:
            c.flats_gapped_through_stop += 1
        c.flat_events.append(FlatEvent(
            strategy_id=pos.strategy.strategy_id, entry_index=pos.entry_index,
            exit_index=i, exit_ts=bar.ts, bar_class=kind, raw_price=raw,
            fill_price=fill, slippage_points=slip, gapped_through_stop=gapped,
            forced_session_end=forced_session_end))

        reason = ExitReason.STOP if gapped else ExitReason.SESSION_CLOSE
        self._filling_at_open = (kind is BarWindow.IN_WINDOW)
        try:
            return self._close(pos, i, bar, fill, reason)
        finally:
            self._filling_at_open = False

    # ---- the strict emission check ---------------------------------------
    def _close(self, pos: _OpenPosition, i: int, bar: Bar, price: float,
               reason: ExitReason, *, already_flat: bool = False) -> Trade:
        trade = super()._close(pos, i, bar, price, reason,
                              already_flat=already_flat)
        if self.strict:
            # The flat that fills at a window bar's OPEN is stamped at the
            # deadline instant and is compliant; nothing else inside the window
            # is. ``_filling_at_open`` is set by :meth:`_flat` immediately
            # before the call, which is the only place the distinction is
            # knowable - a Trade alone cannot say where in its bar it filled.
            exempt = {(trade.strategy_id, i)} if self._filling_at_open else set()
            bad = violations([trade], flat_exits=exempt)
            if bad:
                raise SessionWindowViolation(
                    f"{self.frame.symbol}: the engine was about to emit a trade "
                    f"that breaks the session window: {bad}. entry="
                    f"{to_et(trade.entry_ts).isoformat()} exit="
                    f"{to_et(trade.exit_ts).isoformat()} reason={reason.value} "
                    f"bar_class={classify_bar(bar.ts, bar.minutes).value}")
        return trade


# --------------------------------------------------------------------------
# The coupling guard
# --------------------------------------------------------------------------

def assert_hooks_reachable() -> None:
    """Fail if ``run_many`` stops routing through the two overridden methods.

    ``SessionWindowEngine`` enforces the rule by overriding ``_open_position``
    and ``_manage``. If a later refactor of ``engine.py`` inlines either, the
    subclass keeps importing, keeps running, and silently stops enforcing
    anything - the exact failure shape this repository has catalogued five times
    (D38, D42, D44, D48, and BarSeries.append). A source-level check is crude
    and it is the only thing that catches a bypass rather than a break.
    """
    src = inspect.getsource(BacktestEngine.run_many)
    for hook in ("self._open_position(", "self._manage("):
        if hook not in src:
            raise AssertionError(
                f"BacktestEngine.run_many no longer calls {hook} - "
                "SessionWindowEngine's override is dead code and the session "
                "window is NOT being enforced. Re-derive the subclass.")
    sig = inspect.signature(BacktestEngine._manage)
    if list(sig.parameters) != ["self", "pos", "i", "bar", "is_last"]:
        raise AssertionError(
            f"BacktestEngine._manage signature changed to {list(sig.parameters)}; "
            "SessionWindowEngine._manage must be re-derived.")
    if "not self.allow_overnight" not in inspect.getsource(BacktestEngine._manage):
        raise AssertionError(
            "engine.py's RTH-close exit is no longer gated on allow_overnight, "
            "so it may now fire alongside the 16:00 flat and "
            "is_session_flat() can no longer distinguish them.")


# --------------------------------------------------------------------------
# The invariant, asserted on realised trades
# --------------------------------------------------------------------------

def flat_exit_keys(engine: "SessionWindowEngine") -> set:
    """``{(strategy_id, exit_index)}`` for flats the rule filled at a bar's OPEN.

    Needed because ``Trade`` records ``exit_ts = bar.ts``, the bar's *open* time
    (`engine.py:505`), and says nothing about *where in the bar* the fill
    happened. A flat filled at the open of the 16:00 bar is stamped 16:00 and is
    compliant - the position ceased to exist at the deadline instant. A trade
    that merely *ended up* on that bar (target hit at 16:40, say) is stamped
    16:00 too and is a genuine violation. The two are distinguishable only from
    the engine's own record of what it filled, which is what this returns.
    """
    return {(e.strategy_id, e.exit_index) for e in engine.counters.flat_events
            if e.bar_class is BarWindow.IN_WINDOW}


def violations(trades: Iterable[Trade], *,
               flat_exits: Optional[set] = None) -> List[dict]:
    """Every way a realised trade can break the session window.

    Three separate tests, because they fail for different reasons:

    * ``ENTRY_IN_WINDOW`` - a position was opened between 16:00 and 18:00 ET.
      The endpoint is included: 16:00 itself is forbidden for an entry.
    * ``EXIT_IN_WINDOW`` - a position was still alive inside the window.
    * ``SPANS_WINDOW`` - entry before 16:00, exit after it, so the position was
      held straight through. Walks every ET day the trade touches, so a
      multi-day hold trips on the first deadline it crosses.

    ``flat_exits`` is the carve-out and the **default is no carve-out**: with
    ``None`` this is the strict audit, usable on trades from any engine. Pass
    :func:`flat_exit_keys` to exempt the flats the rule itself filled at a bar's
    open, which are stamped at the deadline instant and are compliant. The
    exemption is keyed on the engine's own record of the fill, never inferred
    from the trade, so it cannot launder a violation: an exit inside the window
    that the rule did not fill is still reported.
    """
    exempt = flat_exits or set()
    out: List[dict] = []
    for t in trades:
        ent = to_et(t.entry_ts)
        ex = to_et(t.exit_ts) if t.exit_ts else None
        if in_forbidden_window(ent):
            out.append({"kind": "ENTRY_IN_WINDOW", "strategy_id": t.strategy_id,
                        "entry_ts": ent.isoformat(),
                        "exit_ts": ex.isoformat() if ex else None})
        if ex is not None and in_forbidden_window(ex) \
                and (t.strategy_id, t.exit_index) not in exempt:
            out.append({"kind": "EXIT_IN_WINDOW", "strategy_id": t.strategy_id,
                        "entry_ts": ent.isoformat(), "exit_ts": ex.isoformat(),
                        "exit_reason": t.exit_reason.value})
        if ex is not None and _spans_window(ent, ex):
            out.append({"kind": "SPANS_WINDOW", "strategy_id": t.strategy_id,
                        "entry_ts": ent.isoformat(), "exit_ts": ex.isoformat()})
    return out


def _spans_window(entry: datetime, exit_: datetime) -> bool:
    """Whether [entry, exit] contains a whole 16:00-18:00 ET window.

    Walks the ET calendar days the trade touches and asks whether any day's
    16:00 lies strictly inside the holding period. Cheap, and it does not
    assume the trade is short: a three-day hold trips on the first day it
    crosses.
    """
    from datetime import date as _date, timedelta as _td
    from futures_agents.timeutil import ET
    day = entry.date()
    while day <= exit_.date():
        flat = datetime.combine(day, datetime.min.time(), tzinfo=ET).replace(hour=16)
        if entry < flat < exit_:
            return True
        day = day + _td(days=1)
    return False


# --------------------------------------------------------------------------
# Prefix invariance, the BT1 check
# --------------------------------------------------------------------------

def prefix_invariance_report(bars: Sequence[Bar], *,
                             ks: Optional[Sequence[int]] = None) -> dict:
    """Assert the rule on ``bars[0:k]`` matches the rule on the full series.

    A clock rule should pass trivially, and the point of running it is that
    there is a natural implementation which does *not*: "bar *i* is the flat
    bar iff ``bars[i+1].ts >= 16:00``" is look-ahead, and on a prefix ending at
    *i* it gives a different answer. Passing this is evidence the
    implementation reads only its own bar.

    Two things are checked separately, because they have different guarantees
    and collapsing them would hide the weaker one:

    * ``classification_mismatches`` - ``classify_bar`` is a pure function of one
      bar, so this must be **0**, always.
    * ``session_end_mismatches_off_cut_date`` - the session-end map (component
      1b) needs a date's full timestamp list, so a prefix cut *inside* an
      early-close date can classify that date's last bar differently. Those are
      counted separately as ``session_end_mismatches_on_cut_date``. Once the
      prefix passes into the next date the day's bar list is complete and cannot
      change, so **off-cut must be 0** - that is the real assertion, and it is
      the exact statement of what component 1b costs.

    ``ks`` defaults to every prefix length, which is quadratic - pass a stride
    for a long series and say which coverage you used.
    """
    full_cls = classify_series(bars)
    full_se = session_end_indices(bars)
    todo = list(range(len(bars) + 1)) if ks is None else list(ks)
    cls_bad: List[dict] = []
    se_off: List[dict] = []
    se_on = 0
    for k in todo:
        pref = bars[:k]
        got = classify_series(pref)
        if got != full_cls[:k]:
            for j, (a, b) in enumerate(zip(got, full_cls[:k])):
                if a != b:
                    cls_bad.append({"k": k, "index": j, "prefix": a.value,
                                    "full": b.value})
        if not pref:
            continue
        se = session_end_indices(pref)
        cut_date = to_et(pref[-1].ts).date().isoformat()
        for idx in set(se) ^ {i for i in full_se if i < k}:
            day = se.get(idx) or full_se.get(idx)
            if day == cut_date:
                se_on += 1
            else:
                se_off.append({"k": k, "index": idx, "date": day,
                               "cut_date": cut_date})
    return {"n_bars": len(bars), "prefixes_checked": len(todo),
            "classification_mismatches": len(cls_bad),
            "classification_detail": cls_bad[:20],
            "session_end_mismatches_on_cut_date": se_on,
            "session_end_mismatches_off_cut_date": len(se_off),
            "session_end_detail": se_off[:20],
            # Kept for callers that only want one number: the sum of the two
            # things that must be zero.
            "mismatches": len(cls_bad) + len(se_off)}


# --------------------------------------------------------------------------
# D48 — arm construction that cannot collide
# --------------------------------------------------------------------------

def with_exit(strategy: Strategy, **exit_fields) -> Strategy:
    """``strategy`` with ``exit`` fields overridden and a **fresh id**.

    D48: ``Strategy._id`` is a dataclass field that ``strategy_id`` memoises
    into (`base.py:585,606-623`), and ``dataclasses.replace`` copies fields - so
    once the id has been read even once, every later ``replace`` carries the
    stale one forward, both arms land on the same ``BacktestResult`` key, and
    the measured difference between them is **exactly zero**. That signature is
    indistinguishable from this programme's own settled finding that operating
    axes do not move expectancy, which is what makes it dangerous rather than
    merely wrong. ``_id=None`` is the whole fix; this function exists so no
    downstream agent has to remember it.
    """
    return replace(strategy, exit=replace(strategy.exit, **exit_fields), _id=None)


def assert_distinct_ids(*groups: Sequence[Strategy]) -> None:
    """Fail if any two arms share a ``strategy_id``.

    ``with_exit`` prevents the D48 collision; this proves it happened. Assert at
    emission, not after the run - after the run the two arms have already been
    written to one key and the evidence is gone.
    """
    seen: Dict[str, Tuple[int, str]] = {}
    for arm, group in enumerate(groups):
        ids = [s.strategy_id for s in group]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise AssertionError(
                f"arm {arm} contains {len(dupes)} duplicated strategy_id(s), "
                f"e.g. {sorted(dupes)[:3]} - the arm collides with itself.")
        for sid, s in zip(ids, group):
            if sid in seen:
                prev_arm, prev = seen[sid]
                raise AssertionError(
                    f"strategy_id {sid} appears in arm {prev_arm} ({prev}) and "
                    f"arm {arm} ({s.exit.identity}). D48: both arms will write "
                    "to one BacktestResult and their difference will measure "
                    "exactly zero. Build arms with with_exit(), which passes "
                    "_id=None.")
            seen[sid] = (arm, s.exit.identity)
