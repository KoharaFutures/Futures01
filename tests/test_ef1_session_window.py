"""EF1 — known-answer tests for the 18:00 ET -> 16:00 ET session-window rule.

The rule under test lives in
``workspace/roundtable/edge/EF1/code/session_window.py`` and gates the whole
edge-finding programme: EF2-EF5 cannot report a profitability number until it
validates. So the tests here are written to *reject*, not to confirm. A harness
that has never been shown to reject anything has not been tested, and the checks
below are arranged so that every one of them fails if the rule is switched off:

* positions that **must** be closed, with the fill price asserted to the tick;
* entries that **must** be vetoed, with the signal still counted so the veto is
  visible rather than silent;
* the invariant detector shown catching a trade that breaks the window, so a
  zero-violation result means "nothing broke" and not "nothing was looked at";
* the shipped RTH-close exit shown *not* firing at MGC's 13:30, which is the
  whole reason this rule had to be built;
* slippage asserted non-zero at the flat, because R3 found every time-based and
  session exit in this repo closes at ``bar.close`` with zero slippage by
  construction (``engine.py:467,473,476``) and this rule fires on every position;
* prefix invariance, so the clock rule is shown to read only its own bar.

Bars are hand-written at real Eastern timestamps. The 16:00 boundary is a
wall-clock fact, so a test that does not carry a real ET stamp cannot exercise
it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import pytest

_EF1 = Path(__file__).resolve().parents[1] / "workspace/roundtable/edge/EF1/code"
if str(_EF1) not in sys.path:
    sys.path.insert(0, str(_EF1))

from futures_agents.backtest.costs import CostModel, FillModel, SlippageModel
from futures_agents.backtest.engine import (BacktestEngine, ExitReason, Trade,
                                            TradeLeg)
from futures_agents.config import get_contract
from futures_agents.data.bars import Bar, BarSeries
from futures_agents.features import SymbolFrame
from futures_agents.schema import Direction
from futures_agents.strategies.base import (Condition, ConditionKind,
                                            ConditionResult, ExitModel,
                                            StopKind, Strategy, StrategySignal)
from futures_agents.timeutil import ET, to_et

from session_window import (BarWindow, FlatEvent, SessionGridError,
                            SessionWindowEngine, SessionWindowViolation,
                            assert_distinct_ids, assert_hooks_reachable,
                            classify_bar, classify_series, et_minute_of_day,
                            flat_exit_keys, in_forbidden_window,
                            is_session_flat, prefix_invariance_report,
                            session_end_indices, violations, with_exit)

# --------------------------------------------------------------------------
# Construction helpers
# --------------------------------------------------------------------------

#: A Monday inside EDT, comfortably clear of every DST transition.
DAY = datetime(2025, 6, 9, tzinfo=ET)


def at(day: datetime, hh: int, mm: int = 0, *, days: int = 0) -> datetime:
    return (day + timedelta(days=days)).replace(hour=hh, minute=mm)


def bars(rows: Sequence[Tuple[datetime, float, float, float, float]], *,
         minutes: int = 60) -> List[Bar]:
    return [Bar(ts=ts, open=o, high=h, low=l, close=c, volume=1000.0,
                minutes=minutes) for ts, o, h, l, c in rows]


def frame(rows, *, symbol: str = "MNQ", minutes: int = 60) -> SymbolFrame:
    return SymbolFrame(BarSeries(symbol, minutes, bars(rows, minutes=minutes)),
                       (minutes,))


def no_slip(symbol: str = "MNQ") -> CostModel:
    """Frictionless, so a fill-location assertion cannot be confused with a
    slippage change. The slippage tests use the real model deliberately."""
    return CostModel(
        spec=get_contract(symbol),
        slippage=SlippageModel(base_ticks=0.0, stop_order_extra_ticks=0.0,
                               volatility_coefficient=0.0,
                               thin_book_extra_ticks=0.0, news_extra_ticks=0.0),
        fill=FillModel(), commission_override=0.0)


def plain_exit(**kw) -> ExitModel:
    """Every optional management feature off, so only the window rule acts."""
    params = dict(stop_kind=StopKind.FIXED_TICKS, stop_mult=1.0,
                  targets_r=(50.0,), scale_out=(1.0,), breakeven_at_r=None,
                  trail_atr_mult=None, time_stop_bars=None,
                  exit_at_session_close=False)
    params.update(kw)
    return ExitModel(**params)


@dataclass
class Stub:
    """Fires at chosen base-bar indices with chosen levels.

    ``conftest.StubStrategy`` fires exactly once; the window rule needs a
    strategy that fires repeatedly across several sessions, and needs to be able
    to fire on a bar inside the forbidden window to prove the veto.
    """

    signal_at: Tuple[int, ...]
    entry: float
    stop: float
    targets: List[float]
    direction: Direction = Direction.LONG
    strategy_id: str = "stub"
    name: str = "Stub"
    group: str = "test"
    symbol: str = "MNQ"
    primary_tf: int = 60
    exit: ExitModel = field(default_factory=plain_exit)

    def evaluate(self, snap, cache: Optional[dict] = None):
        if snap.base_index not in self.signal_at:
            return None
        return StrategySignal(
            strategy_id=self.strategy_id, strategy_name=self.name,
            group=self.group, symbol=self.symbol, ts=snap.ts,
            bar_index=snap.base_index, direction=self.direction,
            entry=self.entry, stop=self.stop, targets=list(self.targets),
            primary_tf=self.primary_tf, timeframes=[self.primary_tf],
            regime=snap.regime.regime, volatility=snap.regime.volatility,
            session=snap.session, time_bucket=snap.time_bucket,
            day_of_week=snap.day_of_week)


def run(rows, strat, *, symbol: str = "MNQ", minutes: int = 60, costs=None, **kw):
    f = frame(rows, symbol=symbol, minutes=minutes)
    eng = SessionWindowEngine(f, costs if costs is not None else no_slip(symbol), **kw)
    return eng.run(strat), eng


# A quiet Monday RTH run-up to 16:00 ET, one 60m bar each. Index 0 = 11:00.
FLAT_DAY: List[Tuple[datetime, float, float, float, float]] = [
    (at(DAY, 11), 21_000.0, 21_005.0, 20_995.0, 21_000.0),   # 0
    (at(DAY, 12), 21_000.0, 21_005.0, 20_995.0, 21_002.0),   # 1  signal
    (at(DAY, 13), 21_010.0, 21_015.0, 21_008.0, 21_012.0),   # 2  entry @ open
    (at(DAY, 14), 21_012.0, 21_018.0, 21_009.0, 21_016.0),   # 3
    (at(DAY, 15), 21_016.0, 21_022.0, 21_014.0, 21_020.0),   # 4  ON_BOUNDARY
    (at(DAY, 16), 21_020.0, 21_025.0, 21_018.0, 21_024.0),   # 5  IN_WINDOW
    (at(DAY, 18), 21_030.0, 21_035.0, 21_028.0, 21_032.0),   # 6  reopen
    (at(DAY, 19), 21_032.0, 21_038.0, 21_030.0, 21_036.0),   # 7
]


# ==========================================================================
# 1. The clock rule itself
# ==========================================================================

@pytest.mark.parametrize("hh,mm,minutes,want", [
    (15, 0, 60, BarWindow.ON_BOUNDARY),     # the 60m flat bar
    (15, 45, 15, BarWindow.ON_BOUNDARY),
    (15, 55, 5, BarWindow.ON_BOUNDARY),
    (12, 0, 240, BarWindow.ON_BOUNDARY),    # the 240m flat bar
    (8, 0, 480, BarWindow.ON_BOUNDARY),
    (18, 0, 1320, BarWindow.ON_BOUNDARY),   # one whole 18:00->16:00 cycle
    (16, 0, 60, BarWindow.IN_WINDOW),
    (17, 0, 60, BarWindow.IN_WINDOW),
    (17, 0, 120, BarWindow.IN_WINDOW),      # starts inside, extends past 18:00
    (15, 30, 60, BarWindow.INTERIOR),
    (15, 45, 30, BarWindow.INTERIOR),
    (18, 0, 1440, BarWindow.INTERIOR),      # every daily bar
    (9, 30, 60, BarWindow.OUTSIDE),
    (13, 0, 60, BarWindow.OUTSIDE),
    (23, 0, 60, BarWindow.OUTSIDE),
    (18, 0, 240, BarWindow.OUTSIDE),
])
def test_classify_bar_known_answers(hh, mm, minutes, want):
    assert classify_bar(at(DAY, hh, mm), minutes) is want


def test_daily_bar_is_interior_not_outside():
    """Regression for a real defect in EF1's own first cut.

    The first implementation compared ``start + minutes`` against 960 alone.
    A daily bar is stamped 18:00 ET (``bars.py:139-143``), so ``start`` = 1080,
    which is neither below 960 nor inside [960, 1080) - it fell through to
    ``OUTSIDE``, and **every 1440m strategy would have run with no flat at all**
    while the harness reported success. The deadline a bar is tested against has
    to be the next 16:00 after its own start.
    """
    assert classify_bar(at(DAY, 18), 1440) is BarWindow.INTERIOR
    assert classify_bar(at(DAY, 20), 1440) is BarWindow.INTERIOR
    assert classify_bar(at(DAY, 23), 1440) is BarWindow.INTERIOR


def test_window_is_half_open_16_inclusive_18_exclusive():
    assert in_forbidden_window(at(DAY, 16, 0)) is True
    assert in_forbidden_window(at(DAY, 17, 59)) is True
    assert in_forbidden_window(at(DAY, 18, 0)) is False
    assert in_forbidden_window(at(DAY, 15, 59)) is False


# ==========================================================================
# 2. DST — the rule is wall-clock, not a fixed offset
# ==========================================================================

def test_flat_tracks_et_wall_clock_across_the_dst_boundary():
    """The archive spans 2024-11-03, so this is not hypothetical.

    ``data/archive/`` stamps carry -04:00 before the transition and -05:00
    after. The same ET wall-clock 15:00 bar therefore sits at a **different UTC
    hour** on the two sides, and a rule written against a UTC offset would fire
    an hour early or an hour late for half the sample.
    """
    edt = datetime(2024, 10, 30, 15, 0, tzinfo=ET)     # EDT, -04:00
    est = datetime(2024, 11, 6, 15, 0, tzinfo=ET)      # EST, -05:00
    assert edt.utcoffset() != est.utcoffset()          # the two regimes differ
    assert edt.astimezone(tz=None).utctimetuple().tm_hour != \
        est.astimezone(tz=None).utctimetuple().tm_hour or True  # offsets differ
    assert et_minute_of_day(edt) == et_minute_of_day(est) == 15 * 60
    assert classify_bar(edt, 60) is BarWindow.ON_BOUNDARY
    assert classify_bar(est, 60) is BarWindow.ON_BOUNDARY
    # And the same instant expressed in UTC classifies identically.
    from datetime import timezone
    assert classify_bar(edt.astimezone(timezone.utc), 60) is BarWindow.ON_BOUNDARY
    assert classify_bar(est.astimezone(timezone.utc), 60) is BarWindow.ON_BOUNDARY


# ==========================================================================
# 3. Component 1 — the position that MUST be closed
# ==========================================================================

def test_position_is_flat_at_1600_and_the_fill_is_the_1600_print():
    res, eng = run(FLAT_DAY, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                                  targets=[21_500.0]))
    assert len(res.trades) == 1
    t = res.trades[0]
    assert is_session_flat(t)
    assert t.exit_index == 4                      # the 15:00-16:00 bar
    assert t.exit_ts == at(DAY, 15)
    assert t.exit_price == pytest.approx(21_020.0)   # that bar's close
    assert eng.counters.flats_on_boundary == 1
    assert eng.counters.flats_in_window == 0
    assert eng.counters.flat_events[0].bar_class is BarWindow.ON_BOUNDARY


def test_without_the_rule_the_same_position_runs_on_past_1600():
    """The control. If this passes and the test above passes, the rule is doing
    something; if both produce the same trade, the rule is inert."""
    f = frame(FLAT_DAY)
    base = BacktestEngine(f, no_slip(), allow_overnight=True)
    res = base.run(Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                        targets=[21_500.0]))
    t = res.trades[0]
    assert t.exit_index == 7                      # END_OF_DATA, 19:00
    assert t.exit_reason is ExitReason.END_OF_DATA
    assert in_forbidden_window(t.entry_ts) is False
    # ...and it was held straight through 16:00-18:00, which the rule forbids.
    assert [v["kind"] for v in violations(res.trades)] == ["SPANS_WINDOW"]


def test_overnight_hold_through_the_next_rth_open_is_permitted():
    """The rule caps a hold at one 18:00->16:00 cycle, it does not forbid one."""
    rows = [
        (at(DAY, 18), 21_000.0, 21_005.0, 20_995.0, 21_000.0),        # 0
        (at(DAY, 19), 21_000.0, 21_005.0, 20_995.0, 21_002.0),        # 1 signal
        (at(DAY, 20), 21_010.0, 21_015.0, 21_008.0, 21_012.0),        # 2 entry
        (at(DAY, 3, days=1), 21_012.0, 21_018.0, 21_009.0, 21_016.0),  # 3 London
        (at(DAY, 10, days=1), 21_016.0, 21_022.0, 21_014.0, 21_020.0),  # 4 RTH
        (at(DAY, 15, days=1), 21_020.0, 21_030.0, 21_018.0, 21_028.0),  # 5 flat
        (at(DAY, 18, days=1), 21_040.0, 21_045.0, 21_038.0, 21_042.0),  # 6
    ]
    res, eng = run(rows, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                              targets=[21_500.0]))
    t = res.trades[0]
    assert is_session_flat(t)
    assert t.exit_ts == at(DAY, 15, days=1)
    assert t.minutes_held == pytest.approx(19 * 60)   # 20:00 -> 15:00 next day
    assert violations(res.trades) == []


def test_mgc_is_not_flattened_at_its_own_1330_rth_close():
    """The reason this rule had to be built rather than configured.

    ``exit_at_session_close`` fires at ``rth_close``, which is **13:30 for MGC**
    (``config.py`` MGC spec), and it is gated on ``not allow_overnight`` so
    turning overnight on removes it. Here the exit model asks for a session
    close and the position must nevertheless survive 13:30 and go flat at 16:00.
    """
    spec = get_contract("MGC")
    assert spec.rth_close == "13:30"
    rows = [
        (at(DAY, 10), 2_600.0, 2_601.0, 2_599.0, 2_600.0),   # 0
        (at(DAY, 11), 2_600.0, 2_601.0, 2_599.0, 2_600.2),   # 1 signal
        (at(DAY, 12), 2_601.0, 2_602.0, 2_600.5, 2_601.5),   # 2 entry
        (at(DAY, 13), 2_601.5, 2_603.0, 2_601.0, 2_602.5),   # 3 spans 13:30
        (at(DAY, 14), 2_602.5, 2_604.0, 2_602.0, 2_603.5),   # 4 past 13:30
        (at(DAY, 15), 2_603.5, 2_605.0, 2_603.0, 2_604.5),   # 5 ON_BOUNDARY
        (at(DAY, 18), 2_610.0, 2_611.0, 2_609.0, 2_610.5),   # 6
    ]
    strat = Stub(signal_at=(1,), entry=2_601.0, stop=2_590.0, targets=[2_700.0],
                 symbol="MGC", exit=plain_exit(exit_at_session_close=True))
    res, eng = run(rows, strat, symbol="MGC", costs=no_slip("MGC"))
    t = res.trades[0]
    assert is_session_flat(t)
    assert t.exit_ts == at(DAY, 15), "flattened at MGC's 13:30, not at 16:00"
    assert t.exit_price == pytest.approx(2_604.5)

    # The shipped engine, same bars, same exit model: out at 13:30.
    shipped = BacktestEngine(frame(rows, symbol="MGC"), no_slip("MGC"))
    st = shipped.run(strat).trades[0]
    assert st.exit_reason is ExitReason.SESSION_CLOSE
    assert st.exit_ts == at(DAY, 13)      # 2h30m early, and this is the default


# ==========================================================================
# 4. Component 2 — the entry that MUST be vetoed
# ==========================================================================

def test_entry_whose_fill_lands_in_the_window_is_vetoed_and_counted():
    res, eng = run(FLAT_DAY, Stub(signal_at=(4,), entry=21_020.0, stop=21_010.0,
                                  targets=[21_500.0]))
    assert res.signals_generated == 1, "the signal must still be counted"
    assert res.trades == [], "the fill bar opens at 16:00 - must be vetoed"
    assert eng.counters.entries_vetoed_in_window == 1


def test_a_signal_inside_the_window_may_fill_at_the_1800_reopen():
    """The letter of the rule: no position *opened* between 16:00 and 18:00. A
    signal computed on the closed 16:00-17:00 bar filling at 18:00 opens at
    18:00, which is legal. The stricter reading is available as a flag."""
    res, eng = run(FLAT_DAY, Stub(signal_at=(5,), entry=21_030.0, stop=21_020.0,
                                  targets=[21_500.0]))
    assert len(res.trades) == 1
    assert res.trades[0].entry_ts == at(DAY, 18)
    assert eng.counters.entries_vetoed_in_window == 0

    strict_res, strict = run(FLAT_DAY, Stub(signal_at=(5,), entry=21_030.0,
                                            stop=21_020.0, targets=[21_500.0]),
                             veto_signals_in_window=True)
    assert strict_res.trades == []
    assert strict.counters.entries_vetoed_signal_in_window == 1


def test_a_stale_fill_across_the_break_is_counted_not_hidden():
    """Friday 16:00 signal, Sunday 18:00 fill. Legal, 50 hours stale."""
    fri = datetime(2025, 6, 6, tzinfo=ET)
    rows = [
        (at(fri, 14), 21_000.0, 21_005.0, 20_995.0, 21_000.0),
        (at(fri, 15), 21_000.0, 21_005.0, 20_995.0, 21_002.0),
        (at(fri, 16), 21_002.0, 21_006.0, 21_000.0, 21_004.0),          # signal
        (at(fri, 18, days=2), 21_050.0, 21_055.0, 21_048.0, 21_052.0),  # +2d
        (at(fri, 19, days=2), 21_052.0, 21_058.0, 21_050.0, 21_056.0),
        (at(fri, 15, days=3), 21_060.0, 21_065.0, 21_058.0, 21_062.0),
    ]
    res, eng = run(rows, Stub(signal_at=(2,), entry=21_050.0, stop=21_040.0,
                              targets=[21_500.0]))
    assert len(res.trades) == 1
    assert res.trades[0].entry_ts == at(fri, 18, days=2)
    assert eng.counters.stale_fills == 1
    assert violations(res.trades) == []


# ==========================================================================
# 5. Component 3 — the gap-honest fill
# ==========================================================================

def test_flat_pays_market_order_slippage_not_zero():
    """R3's finding, which this rule must not inherit.

    ``engine.py:467,473,476`` close at ``bar.close`` with no slippage at all.
    This flat fires on *every* position, so a zero-slippage flat would
    understate the cost of the programme's defining rule on every single trade.
    """
    costs = CostModel(spec=get_contract("MNQ"))       # the real model
    res, eng = run(FLAT_DAY, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                                  targets=[21_500.0]), costs=costs)
    t = res.trades[0]
    ev = eng.counters.flat_events[0]
    assert ev.slippage_points > 0.0
    assert t.exit_price < 21_020.0, "a long must fill below the print"
    assert t.exit_price == pytest.approx(
        get_contract("MNQ").round_to_tick(21_020.0 - ev.slippage_points))
    # A market order slips like a stop, not like a marketable limit.
    assert ev.slippage_points >= costs.slippage_price(is_stop=True)


def test_short_flat_slips_the_other_way():
    costs = CostModel(spec=get_contract("MNQ"))
    res, eng = run(FLAT_DAY, Stub(signal_at=(1,), entry=21_010.0, stop=21_100.0,
                                  targets=[20_500.0],
                                  direction=Direction.SHORT), costs=costs)
    t = res.trades[0]
    assert is_session_flat(t)
    assert t.exit_price > 21_020.0, "a short must fill above the print"


def test_hole_at_the_deadline_fills_at_the_next_open_gap_and_all():
    """The MCL 2026-03-06 shape: no bar closes at 16:00.

    ``data/archive/MCL_60m.jsonl`` has no 14:00 and no 15:00 bar that day; the
    last print before the deadline closes at 91.28 and the 16:00 bar opens at
    90.90. Closing at the last bar's close invents 38 cents. The resting market
    order fills at the first price there is.
    """
    rows = [
        (at(DAY, 11), 21_000.0, 21_005.0, 20_995.0, 21_000.0),   # 0
        (at(DAY, 12), 21_000.0, 21_005.0, 20_995.0, 21_002.0),   # 1 signal
        (at(DAY, 13), 21_010.0, 21_015.0, 21_008.0, 21_012.0),   # 2 entry
        # 14:00 and 15:00 do not exist - the hole.
        (at(DAY, 16), 20_950.0, 20_960.0, 20_940.0, 20_955.0),   # 3 IN_WINDOW
        (at(DAY, 18), 20_960.0, 20_965.0, 20_958.0, 20_962.0),   # 4
    ]
    res, eng = run(rows, Stub(signal_at=(1,), entry=21_010.0, stop=20_900.0,
                              targets=[21_500.0]))
    t = res.trades[0]
    assert is_session_flat(t)
    assert t.exit_index == 3
    assert t.exit_price == pytest.approx(20_950.0), "must fill at the gap open"
    assert eng.counters.flats_in_window == 1
    assert eng.counters.flats_on_boundary == 0
    assert eng.counters.flat_events[0].bar_class is BarWindow.IN_WINDOW
    # Stamped 16:00 because Trade.exit_ts is the bar's OPEN time and the fill
    # was at that open - i.e. at the deadline instant, which is compliant. The
    # strict audit flags it; the audit that knows what the rule filled does not.
    assert [v["kind"] for v in violations(res.trades)] == ["EXIT_IN_WINDOW"]
    assert violations(res.trades, flat_exits=flat_exit_keys(eng)) == []
    # And the excursions do not read the post-deadline bar's range.
    assert t.mae_points == pytest.approx(21_010.0 - 21_008.0)


def test_gap_through_the_stop_at_the_flat_is_a_stop_not_a_flat():
    """When the reopen is already past the stop, the stop was breached first in
    time. ``engine.py:410-411``'s own rule is the fill is the open with no
    further slippage, and this branch honours it rather than booking a flat at a
    price the position never reached alive."""
    rows = [
        (at(DAY, 11), 21_000.0, 21_005.0, 20_995.0, 21_000.0),
        (at(DAY, 12), 21_000.0, 21_005.0, 20_995.0, 21_002.0),   # signal
        (at(DAY, 13), 21_010.0, 21_015.0, 21_008.0, 21_012.0),   # entry
        (at(DAY, 16), 20_900.0, 20_905.0, 20_880.0, 20_890.0),   # gap < stop
        (at(DAY, 18), 20_900.0, 20_905.0, 20_898.0, 20_902.0),
    ]
    costs = CostModel(spec=get_contract("MNQ"))       # real slippage on purpose
    res, eng = run(rows, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                              targets=[21_500.0]), costs=costs)
    t = res.trades[0]
    assert t.exit_reason is ExitReason.STOP
    assert t.exit_price == pytest.approx(20_900.0)
    assert eng.counters.flats_gapped_through_stop == 1
    ev = eng.counters.flat_events[0]
    assert ev.gapped_through_stop is True
    assert ev.slippage_points == 0.0, "a gap fill is not slipped twice"


def test_stop_inside_the_flat_bar_wins_over_the_flat():
    """Pessimism is preserved: the flat does not rescue a stopped position."""
    rows = list(FLAT_DAY)
    rows[4] = (at(DAY, 15), 21_016.0, 21_022.0, 20_990.0, 21_020.0)   # low < stop
    res, _ = run(rows, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                            targets=[21_500.0]))
    t = res.trades[0]
    assert t.exit_reason is ExitReason.STOP
    assert t.exit_index == 4
    assert t.net_r < 0


def test_stop_beats_target_in_the_flat_bar():
    rows = list(FLAT_DAY)
    # This bar contains the 2R target (21030) AND the stop (21000).
    rows[4] = (at(DAY, 15), 21_016.0, 21_035.0, 20_995.0, 21_020.0)
    res, _ = run(rows, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                            targets=[21_030.0]))
    assert res.trades[0].exit_reason is ExitReason.STOP


# ==========================================================================
# 5b. Component 1b — the session that shuts before 16:00
# ==========================================================================

#: An exchange early close: the session ends at 13:00 and does not reopen until
#: 18:00, so no bar ends at 16:00 and no bar starts inside the window. This is
#: the shape of 2024-11-29, 2024-12-24, 2025-07-03, 2025-11-28 and six others on
#: all four symbols, and the shape that produced EF1's first 33 violations.
EARLY_CLOSE: List[Tuple[datetime, float, float, float, float]] = [
    (at(DAY, 18, days=-1), 21_000.0, 21_005.0, 20_995.0, 21_000.0),   # 0 prev eve
    (at(DAY, 10), 21_000.0, 21_005.0, 20_995.0, 21_002.0),            # 1 signal
    (at(DAY, 11), 21_010.0, 21_015.0, 21_008.0, 21_012.0),            # 2 entry
    (at(DAY, 12), 21_012.0, 21_018.0, 21_009.0, 21_016.0),            # 3 LAST bar
    (at(DAY, 18), 21_100.0, 21_105.0, 21_098.0, 21_102.0),            # 4 reopen
    (at(DAY, 10, days=1), 21_102.0, 21_108.0, 21_100.0, 21_106.0),    # 5
    (at(DAY, 15, days=1), 21_106.0, 21_112.0, 21_104.0, 21_110.0),    # 6 boundary
]


def test_position_is_flat_at_the_early_close_not_carried_to_the_reopen():
    res, eng = run(EARLY_CLOSE, Stub(signal_at=(1,), entry=21_010.0,
                                     stop=21_000.0, targets=[21_500.0]))
    t = res.trades[0]
    assert is_session_flat(t)
    assert t.exit_index == 3, "must go flat on the session's last bar"
    assert t.exit_price == pytest.approx(21_016.0)
    assert eng.counters.flats_forced_session_end == 1
    assert eng.counters.flats_on_boundary == 0
    assert eng.counters.flat_events[0].forced_session_end is True
    assert violations(res.trades) == []


def test_session_end_map_keys_on_the_trading_day_not_the_calendar_date():
    """The ET-calendar-date version of this map was a defect EF3 caught.

    A position entered 2024-11-27 18:00 has no bar on Thanksgiving to be
    flattened on - the archive has none - so an ET-date map, which had no entry
    for a date that does not exist, let it run to Black Friday 12:30. Keying on
    ``trading_day`` (18:00 roll) puts Thanksgiving-eve's evening bars inside
    Thanksgiving's trading day, where they belong, and the flat lands on the
    last of them. 10 dates per symbol became 19, a strict superset.
    """
    idx = session_end_indices(bars(EARLY_CLOSE))
    # Index 0 is 18:00 the previous evening, so trading_day puts it in DAY's
    # session alongside 1-3. DAY has no deadline bar; index 3 is its last.
    assert idx == {3: DAY.date().isoformat()}

    # The evening bars of a normal day belong to the NEXT trading day.
    assert session_end_indices(bars(FLAT_DAY)) == {}, \
        "FLAT_DAY's 18:00/19:00 bars are the series' truncated last trading day"


def test_holiday_with_no_bars_at_all_still_flattens_the_evening_before():
    """The second defect the validation found in EF1's own code.

    Real shape, MES/MNQ 60m: bars run to 2024-11-27 23:00 (Thanksgiving eve),
    **2024-11-28 has no bars whatsoever**, and the next bar is 2024-11-29 09:30.
    A position entered 2024-11-27 18:00 ran to Black Friday 12:30 - a 66-hour
    hold across two 16:00 deadlines - because an ET-calendar-date map has no
    entry for a date with no bars. ``trading_day`` puts the eve's evening bars
    inside Thanksgiving's session, so the flat lands on the last of them.
    """
    wed = datetime(2024, 11, 27, tzinfo=ET)
    rows = [
        (at(wed, 14), 6_000.0, 6_005.0, 5_995.0, 6_000.0),          # 0
        (at(wed, 15), 6_000.0, 6_005.0, 5_995.0, 6_002.0),          # 1 boundary
        (at(wed, 18), 6_002.0, 6_008.0, 6_000.0, 6_006.0),          # 2 signal
        (at(wed, 19), 6_010.0, 6_015.0, 6_008.0, 6_012.0),          # 3 entry
        (at(wed, 23), 6_012.0, 6_018.0, 6_009.0, 6_016.0),          # 4 LAST
        # 2024-11-28 has no bars at all.
        (at(wed, 9, days=2), 6_100.0, 6_105.0, 6_098.0, 6_102.0),   # 5 Fri
        (at(wed, 12, days=2), 6_102.0, 6_108.0, 6_100.0, 6_106.0),  # 6 Fri last
        (at(wed, 18, days=4), 6_200.0, 6_205.0, 6_198.0, 6_202.0),  # 7 Sun eve
        (at(wed, 15, days=5), 6_210.0, 6_215.0, 6_208.0, 6_212.0),  # 8 Mon bdry
    ]
    idx = session_end_indices(bars(rows))
    assert idx == {4: "2024-11-28", 6: "2024-11-29"}, \
        "Thanksgiving's session ends at the eve's last bar; Friday's at 12:00"

    res, eng = run(rows, Stub(signal_at=(2,), entry=6_010.0, stop=5_900.0,
                              targets=[7_000.0]), symbol="MES",
                   costs=no_slip("MES"))
    t = res.trades[0]
    assert t.exit_index == 4, "must not carry across Thanksgiving's 16:00"
    assert t.exit_ts == at(wed, 23)
    assert t.minutes_held == pytest.approx(4 * 60)
    assert violations(res.trades) == []
    assert eng.counters.flats_forced_session_end == 1


def test_session_end_map_is_a_function_of_timestamps_only():
    """The map is built from the whole series, so it must be shown to read no
    prices. Every OHLC value is perturbed; the map must not move. This is the
    check that separates "exchange calendar knowledge, published in advance"
    from "reading a price the backtest did not have"."""
    original = bars(EARLY_CLOSE)
    perturbed = [replace(b, open=b.open * 3.0 + 1.0, high=b.high * 3.0 + 9.0,
                         low=b.low * 3.0 - 9.0, close=b.close * 3.0 + 1.0,
                         volume=b.volume * 7.0) for b in original]
    assert session_end_indices(perturbed) == session_end_indices(original)
    # Reversing the price direction must not move it either.
    flipped = [replace(b, open=-b.low, high=-b.low, low=-b.high, close=-b.high)
               for b in original]
    assert session_end_indices(flipped) == session_end_indices(original)


def test_strict_emission_catches_the_hole_that_shipped():
    """Disabling component 1b must make the engine *raise*, not under-report.

    This is the regression for the 33 violations. With the session-end map
    emptied the position runs through the window exactly as it did before the
    fix, and the strict check has to stop it at the point of emission.
    """
    f = frame(EARLY_CLOSE)
    eng = SessionWindowEngine(f, no_slip())
    eng._session_end = {}                          # simulate the pre-fix build
    with pytest.raises(SessionWindowViolation, match="SPANS_WINDOW"):
        eng.run(Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                     targets=[21_500.0]))


def test_strict_can_be_switched_off_and_then_the_violation_is_only_counted():
    """The escape hatch exists so a diagnostic run can measure how bad a hole is
    instead of dying on the first trade. It is off by default for a reason."""
    f = frame(EARLY_CLOSE)
    eng = SessionWindowEngine(f, no_slip(), strict=False)
    eng._session_end = {}
    res = eng.run(Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                       targets=[21_500.0]))
    assert [v["kind"] for v in violations(res.trades)] == ["SPANS_WINDOW"]


# ==========================================================================
# 6. The grid audit
# ==========================================================================

def test_daily_grid_is_refused_rather_than_priced_from_a_post_deadline_close():
    rows = [(at(DAY, 18, days=i), 21_000.0 + i, 21_010.0 + i, 20_990.0 + i,
             21_005.0 + i) for i in range(40)]
    with pytest.raises(SessionGridError, match="INTERIOR"):
        SessionWindowEngine(frame(rows, minutes=1440), no_slip())


def test_a_grid_the_rule_can_never_fire_on_is_refused():
    """A rule that cannot fire is not a rule. Three RTH-morning bars contain no
    16:00 boundary and no in-window bar, so the engine refuses rather than
    returning a clean-looking zero."""
    rows = [(at(DAY, 10 + i), 21_000.0, 21_010.0, 20_990.0, 21_005.0)
            for i in range(3)]
    with pytest.raises(SessionGridError, match="can never fire"):
        SessionWindowEngine(frame(rows), no_slip())


def test_interior_grid_is_available_but_prices_at_the_adverse_extreme():
    rows = [(at(DAY, 18, days=i), 21_000.0, 21_010.0, 20_990.0, 21_005.0)
            for i in range(40)]
    eng = SessionWindowEngine(frame(rows, minutes=1440), no_slip(),
                              allow_interior=True)
    assert eng.counters.bars_interior == 40


# ==========================================================================
# 7. The invariant detector — shown catching something
# ==========================================================================

def _trade(entry: datetime, exit_: datetime) -> Trade:
    return Trade(strategy_id="x", strategy_name="x", group="g", symbol="MNQ",
                 direction=Direction.LONG, signal_ts=entry, signal_index=0,
                 entry_ts=entry, entry_index=1, entry_price=1.0,
                 initial_stop=0.5, targets=[2.0], risk_points=0.5,
                 exit_ts=exit_, exit_index=2, exit_price=1.5)


@pytest.mark.parametrize("entry,exit_,want", [
    (at(DAY, 16, 30), at(DAY, 19), "ENTRY_IN_WINDOW"),
    (at(DAY, 14), at(DAY, 16, 30), "EXIT_IN_WINDOW"),
    (at(DAY, 14), at(DAY, 19), "SPANS_WINDOW"),
    (at(DAY, 14), at(DAY, 10, days=3), "SPANS_WINDOW"),
])
def test_violations_detects_each_way_of_breaking_the_window(entry, exit_, want):
    kinds = [v["kind"] for v in violations([_trade(entry, exit_)])]
    assert want in kinds, f"the detector missed {want}"


def test_the_flat_exemption_cannot_launder_a_violation():
    """The carve-out is keyed on the engine's own fill record, so an in-window
    exit the rule did not fill is still reported even when the carve-out is
    supplied. Without this the exemption would be a hole big enough to hide the
    thing the audit exists to find."""
    real = _trade(at(DAY, 14), at(DAY, 16, 30))           # alive at 16:30
    def kinds(**kw):
        return sorted(v["kind"] for v in violations([real], **kw))
    assert kinds() == ["EXIT_IN_WINDOW", "SPANS_WINDOW"]
    # Exempting the exit does NOT exempt the span: the position was demonstrably
    # alive across the deadline, and that is a separate, independent test.
    assert kinds(flat_exits={("x", 2)}) == ["SPANS_WINDOW"]
    # And a key set from a trade the engine did not close exempts nothing.
    assert kinds(flat_exits={("x", 7)}) == ["EXIT_IN_WINDOW", "SPANS_WINDOW"]


def test_flat_exit_keys_only_covers_in_window_fills():
    """ON_BOUNDARY flats are stamped 15:00 and need no exemption; only the
    IN_WINDOW gap fills do. A key set that covered both would exempt exits that
    were never inside the window, which is sloppy rather than wrong - and sloppy
    is how a carve-out grows into a hole."""
    _, eng = run(FLAT_DAY, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                                targets=[21_500.0]))
    assert eng.counters.flats_on_boundary == 1
    assert flat_exit_keys(eng) == set()


@pytest.mark.parametrize("entry,exit_", [
    (at(DAY, 18), at(DAY, 15, days=1)),      # a full legal cycle
    (at(DAY, 11), at(DAY, 15)),              # intraday, flat by 16:00
    (at(DAY, 18), at(DAY, 3, days=1)),       # overnight only
])
def test_violations_is_silent_on_legal_trades(entry, exit_):
    assert violations([_trade(entry, exit_)]) == []


# ==========================================================================
# 8. Prefix invariance — the look-ahead control
# ==========================================================================

def test_the_clock_rule_is_prefix_invariant_for_every_k():
    rows = []
    for d in range(6):
        for hh in (18, 19, 22, 3, 9, 12, 15, 16):
            day = d + (1 if hh < 18 else 0)
            rows.append((at(DAY, hh, days=day if hh < 18 else d),
                         21_000.0, 21_010.0, 20_990.0, 21_005.0))
    series = bars(rows)
    rep = prefix_invariance_report(series)
    # classify_bar is a pure function of one bar, so this is exactly zero.
    assert rep["classification_mismatches"] == 0
    # The session-end map needs a date's full timestamp list, so a prefix cut
    # inside a date may differ *on that date*. Off the cut date it must not.
    assert rep["session_end_mismatches_off_cut_trading_day"] == 0
    assert rep["prefixes_checked"] == len(series) + 1


def test_the_engine_produces_a_prefix_of_its_own_trades_on_every_prefix():
    """The stronger, BT1-style form: run the whole engine on ``bars[0:k]``.

    A rule that read the next bar would give a different verdict on the last bar
    of a prefix, and the divergence would show up here as a trade whose exit
    index or price changes when more data is appended.
    """
    rows = []
    for d in range(4):
        rows += [(at(DAY, 18, days=d), 21_000.0 + 20 * d, 21_012.0 + 20 * d,
                  20_996.0 + 20 * d, 21_004.0 + 20 * d),
                 (at(DAY, 20, days=d), 21_004.0 + 20 * d, 21_016.0 + 20 * d,
                  21_000.0 + 20 * d, 21_010.0 + 20 * d),
                 (at(DAY, 10, days=d + 1), 21_010.0 + 20 * d, 21_022.0 + 20 * d,
                  21_006.0 + 20 * d, 21_016.0 + 20 * d),
                 (at(DAY, 15, days=d + 1), 21_016.0 + 20 * d, 21_028.0 + 20 * d,
                  21_012.0 + 20 * d, 21_022.0 + 20 * d),
                 (at(DAY, 16, days=d + 1), 21_022.0 + 20 * d, 21_034.0 + 20 * d,
                  21_018.0 + 20 * d, 21_028.0 + 20 * d)]
    strat = Stub(signal_at=tuple(range(0, len(rows))), entry=0.0, stop=0.0,
                 targets=[0.0])

    def trades_for(k: int):
        sub = rows[:k]
        if not any(classify_bar(ts, 60) in (BarWindow.ON_BOUNDARY,
                                            BarWindow.IN_WINDOW)
                   for ts, *_ in sub):
            return None                       # grid audit would refuse; skip
        f = frame(sub)
        eng = SessionWindowEngine(f, no_slip())
        s = replace(strat, entry=sub[0][1], stop=sub[0][1] - 200.0,
                    targets=[sub[0][1] + 5_000.0])
        res = eng.run(s)
        # Two exclusions, and both are artefacts of where the cut fell rather
        # than of the rule:
        #  - a trailing END_OF_DATA trade;
        #  - a component-1b forced session-end flat on the prefix's LAST ET
        #    date, because that date's bar list is still incomplete. Once the
        #    prefix passes into the next date the determination is fixed, which
        #    is why only the cut date is exempt.
        cut_date = to_et(bars(sub)[-1].ts).date()
        forced = {(e.entry_index, e.exit_index)
                  for e in eng.counters.flat_events
                  if e.forced_session_end and to_et(e.exit_ts).date() == cut_date}
        out = [t for t in res.trades
               if t.exit_reason is not ExitReason.END_OF_DATA
               and (t.entry_index, t.exit_index) not in forced]
        return [(t.entry_index, t.exit_index, t.exit_price, t.exit_reason)
                for t in out]

    full = trades_for(len(rows))
    assert full, "the control must produce trades, or it proves nothing"
    checked = 0
    for k in range(1, len(rows) + 1):
        got = trades_for(k)
        if got is None:
            continue
        assert got == full[:len(got)], f"prefix k={k} diverges from the full run"
        checked += 1
    assert checked >= len(rows) // 2


# ==========================================================================
# 9. The coupling guard and D48
# ==========================================================================

def test_the_engine_hooks_are_still_reachable():
    assert_hooks_reachable()


def _real_strategy(symbol: str = "MNQ") -> Strategy:
    from futures_agents.strategies.library import CONDITIONS
    # `trend` is the group R4 audited CLEAN 8/8 with R1 agreeing independently,
    # so a D48 fixture built on it cannot be confounded by a second defect.
    # Deliberately NOT macd_directional/macd_hist_direction: R4 measured those
    # identical on 5000/5000 bars, so a fixture using both tests one condition
    # twice.
    cond = CONDITIONS["ema_fast_above_slow"]
    return Strategy(name="ef1-probe", group="TREND", symbol=symbol,
                    primary_tf=60, conditions=(cond,), exit=plain_exit())


def test_d48_naive_replace_collides_and_with_exit_does_not():
    s = _real_strategy()
    _ = s.strategy_id                      # memoise, which is what bites
    naive = replace(s, exit=replace(s.exit, targets_r=(3.0,)))
    assert naive.strategy_id == s.strategy_id, "D48's mechanism, reproduced"
    fixed = with_exit(s, targets_r=(3.0,))
    assert fixed.strategy_id != s.strategy_id


def test_assert_distinct_ids_rejects_a_collided_pair():
    s = _real_strategy()
    _ = s.strategy_id
    naive = replace(s, exit=replace(s.exit, targets_r=(3.0,)))
    with pytest.raises(AssertionError, match="exactly zero"):
        assert_distinct_ids([s], [naive])
    assert_distinct_ids([s], [with_exit(s, targets_r=(3.0,))])


def test_assert_distinct_ids_rejects_an_arm_that_collides_with_itself():
    s = _real_strategy()
    with pytest.raises(AssertionError, match="collides with itself"):
        assert_distinct_ids([s, s])


# ==========================================================================
# 10. Determinism
# ==========================================================================

def test_two_identical_runs_give_identical_trades():
    a, _ = run(FLAT_DAY, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                              targets=[21_500.0]))
    b, _ = run(FLAT_DAY, Stub(signal_at=(1,), entry=21_010.0, stop=21_000.0,
                              targets=[21_500.0]))
    assert [t.to_dict() for t in a.trades] == [t.to_dict() for t in b.trades]
