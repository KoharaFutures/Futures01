"""EF7: validation of the 18:00 ET -> 16:00 ET session-window rule.

The rule is at ``workspace/roundtable/edge/EF7/code/window.py``. This file is the
deliverable: the rule is only worth as much as the checks that could have
rejected it, so every clause of every component gets a known-answer test that is
fed a deliberate breach and shown to fail on it. A harness never shown to reject
anything is untested.

Layout, by component id:

* ``test_h1_*``  the clock predicate - boundaries, DST, and the two timezone
  traps this repository's two data stores set for each other.
* ``test_h2_*``  which bar ends a cycle - including the known-answer test for the
  defect the obvious implementation carries.
* ``test_h3_*``  the engine - exits, vetoes, precedence, costs, determinism, and
  the realised-trade invariant over real archive bars for all four symbols.
* ``test_detector_*``  the violation detector itself, shown rejecting each of the
  three ways a trade can breach the rule.

Everything runs offline against ``data/archive/`` and needs no API key.
"""

from __future__ import annotations

import os
import sys
from dataclasses import replace
from datetime import date, datetime, time, timedelta, timezone

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
_EF7 = os.path.join(_ROOT, "workspace", "roundtable", "edge", "EF7", "code")
if _EF7 not in sys.path:
    sys.path.insert(0, _EF7)

from futures_agents.backtest.costs import CostModel, FillModel, SlippageModel
from futures_agents.backtest.engine import BacktestEngine, ExitReason, Trade
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.data.bars import Bar, BarSeries
from futures_agents.features import SymbolFrame
from futures_agents.schema import Direction
from futures_agents.strategies.base import (Condition, ConditionKind,
                                            ConditionResult, ExitModel,
                                            StopKind, Strategy, StrategyFilters,
                                            TargetKind)
from futures_agents.timeutil import ET, to_et, trading_day

# Named ``ef7_window`` and not ``window``: EF6's code directory also contains a
# ``window.py``, and because every agent's test file prepends its own code dir to
# ``sys.path``, a bare ``window`` resolves to whichever agent pytest collected
# first. Running the whole suite, that was EF6's, and this file failed to import
# with ``cannot import name 'SESSION_WINDOW' from
# '.../EF6/code/window.py'``. Prefixing the module name makes the collision
# impossible rather than order-dependent.
import ef7_window
from ef7_window import (SESSION_WINDOW, SESSION_WINDOW_EXIT, SessionWindow,
                        SessionWindowEngine, cycle_keys, entry_veto_flags,
                        flat_flags, trade_violations)

assert os.path.abspath(ef7_window.__file__) == os.path.join(_EF7, "ef7_window.py"), (
    f"imported the wrong window module: {ef7_window.__file__}")

ARCHIVE = BarArchive(os.path.join(_ROOT, "data", "archive"))
SYMBOLS = ("MGC", "MCL", "MES", "MNQ")


# ==========================================================================
# Fixtures
# ==========================================================================

def et(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=ET)


def _bar(ts, o, h, l, c, minutes=60, v=1000.0):
    return Bar(ts=ts, open=o, high=h, low=l, close=c, volume=v, minutes=minutes)


def hourly_cycle(day: date, *, base: float = 100.0, drift: float = 0.1,
                 include_1600: bool = True, include_1700: bool = False,
                 skip_hours: tuple = ()):
    """One 18:00 -> 16:00 cycle of contiguous hourly bars, terminating at ``day``.

    ``day`` is the cycle key: bars run 18:00 on ``day - 1`` through the bar
    opening 15:00 on ``day``, then optionally the forbidden 16:00 and 17:00 bars.
    Prices drift up by ``drift`` per bar so a long is always mildly profitable
    and never reaches a distant target.
    """
    out = []
    px = base
    stamps = [et(day.year, day.month, day.day, 18) - timedelta(days=1) + timedelta(hours=k)
              for k in range(22)]
    for ts in stamps:
        h = to_et(ts).hour
        if h in skip_hours:
            px += drift
            continue
        out.append(_bar(ts, px, px + drift + 0.05, px - 0.05, px + drift))
        px += drift
    if include_1600:
        ts = et(day.year, day.month, day.day, 16)
        out.append(_bar(ts, px, px + drift + 0.05, px - 0.05, px + drift))
        px += drift
    if include_1700:
        ts = et(day.year, day.month, day.day, 17)
        out.append(_bar(ts, px, px + drift + 0.05, px - 0.05, px + drift))
    return out


def always(direction: Direction = Direction.LONG, name: str = "ef7_always"):
    """A SIGNAL condition that fires on every bar. Deterministic by construction.

    Using a synthetic condition rather than a library one is deliberate: a
    fixture whose signal depends on an indicator's warm-up cannot distinguish
    "the rule vetoed the entry" from "the indicator had not warmed up yet".
    """
    return Condition(name=name, group="time", kind=ConditionKind.SIGNAL,
                     fn=lambda snap, tf: ConditionResult.yes(
                         direction, detail="fixture"),
                     warmup_bars=0)


def fixture_strategy(symbol="MGC", tf=60, *, direction=Direction.LONG,
                     stop_ticks=200.0, targets=(20.0,), time_stop=None,
                     name="EF7-fixture"):
    """A strategy that fires every bar with a wide FIXED_TICKS stop.

    ``FIXED_TICKS`` avoids the ATR warm-up entirely, and a 20R target is far
    enough away that only the session flat can close the position - which is
    what makes the known-answer assertions unambiguous.
    """
    return Strategy(
        name=name, symbol=symbol, group="TREND", primary_tf=tf,
        conditions=(always(direction),),
        exit=ExitModel(stop_kind=StopKind.FIXED_TICKS, stop_mult=stop_ticks,
                       target_kind=TargetKind.R_MULTIPLE, targets_r=targets,
                       scale_out=(1.0,), breakeven_at_r=None,
                       trail_atr_mult=None, time_stop_bars=time_stop,
                       exit_at_session_close=True),
        # rth_only=True would confine the fixture to the contract's RTH and make
        # every window assertion vacuous, so the fixture opens the scope. This is
        # the fixture's choice only; the generated default is measured separately.
        filters=StrategyFilters(rth_only=False),
        allowed_directions=(direction,),
        _id=None,
    )


def no_slip():
    """Costs with slippage and commission zeroed, so a price assertion is exact."""
    return CostModel(spec=get_contract("MGC"),
                     slippage=SlippageModel(base_ticks=0.0, stop_order_extra_ticks=0.0,
                                            volatility_coefficient=0.0,
                                            thin_book_extra_ticks=0.0,
                                            news_extra_ticks=0.0),
                     commission_override=0.0)


def frame_from(bars, symbol="MGC", tfs=(60,)):
    return SymbolFrame(BarSeries(symbol, 60, bars), tfs, get_contract(symbol))


# ==========================================================================
# EF7-H1 - the clock
# ==========================================================================

def test_h1_forbidden_window_is_half_open_at_both_ends():
    w = SESSION_WINDOW
    assert w.is_admissible(et(2025, 3, 12, 15, 59))
    assert w.is_forbidden(et(2025, 3, 12, 16, 0))     # the flat instant itself
    assert w.is_forbidden(et(2025, 3, 12, 17, 59))
    assert w.is_admissible(et(2025, 3, 12, 18, 0))    # the cycle reopens
    assert w.is_admissible(et(2025, 3, 12, 23, 59))
    assert w.is_admissible(et(2025, 3, 12, 0, 0))


def test_h1_cycle_key_names_the_terminating_flat():
    w = SESSION_WINDOW
    # 18:00 Monday belongs to the cycle that flats 16:00 Tuesday.
    assert w.cycle_key(et(2025, 3, 10, 18, 0)) == date(2025, 3, 11)
    assert w.cycle_key(et(2025, 3, 10, 23, 0)) == date(2025, 3, 11)
    assert w.cycle_key(et(2025, 3, 11, 2, 0)) == date(2025, 3, 11)
    assert w.cycle_key(et(2025, 3, 11, 15, 59)) == date(2025, 3, 11)
    assert w.cycle_key(et(2025, 3, 11, 16, 0)) is None      # forbidden
    assert w.cycle_key(et(2025, 3, 11, 18, 0)) == date(2025, 3, 12)
    assert w.flat_instant(et(2025, 3, 10, 18, 0)) == et(2025, 3, 11, 16, 0)
    assert w.open_instant(et(2025, 3, 11, 9, 0)) == et(2025, 3, 10, 18, 0)


def test_h1_hold_budget_is_22_hours_so_multiday_swing_cannot_exist():
    w = SESSION_WINDOW
    assert w.max_hold_minutes(et(2025, 3, 10, 18, 0)) == pytest.approx(22 * 60)
    assert w.max_hold_minutes(et(2025, 3, 11, 15, 0)) == pytest.approx(60)
    assert w.max_hold_minutes(et(2025, 3, 11, 16, 30)) is None


def test_h1_dst_correct_across_the_2024_11_03_switch():
    """The same wall-clock times classify identically on both sides of DST.

    The assertion on ``utcoffset`` is what makes this test mean something: if the
    two instants had the same offset, the test would pass for a hard-coded -04:00
    implementation too and would be measuring nothing.
    """
    edt = et(2024, 11, 1, 16, 30)     # EDT, -04:00
    est = et(2024, 11, 4, 16, 30)     # EST, -05:00
    assert edt.utcoffset() == timedelta(hours=-4)
    assert est.utcoffset() == timedelta(hours=-5)
    for t in (edt, est):
        assert SESSION_WINDOW.is_forbidden(t)
    for t in (et(2024, 11, 1, 18, 30), et(2024, 11, 4, 18, 30)):
        assert SESSION_WINDOW.is_admissible(t)
    # And the archive really does carry both offsets, so this is not hypothetical.
    bars = ARCHIVE.load("MGC", 60).bars
    offsets = {b.ts.utcoffset() for b in bars}
    assert timedelta(hours=-4) in offsets and timedelta(hours=-5) in offsets


def test_h1_fixed_offset_reading_is_wrong_and_the_window_is_not():
    """The trap a hard-coded -04:00 sets, on a real winter bar.

    17:00 EST is inside the forbidden window. Read through a fixed -04:00 the
    same instant presents as 18:00 and looks admissible - a position carried
    straight through the break.
    """
    winter = et(2024, 12, 2, 17, 0)
    assert winter.utcoffset() == timedelta(hours=-5)
    naive_fixed = winter.astimezone(timezone(timedelta(hours=-4)))
    assert naive_fixed.hour == 18                       # the wrong reading
    assert SESSION_WINDOW.is_forbidden(winter)          # the right one


def test_h1_utc_stamped_bar_is_classified_on_et_wall_clock():
    """``csv/raw`` stamps are ``+00:00``; reading ``ts.hour`` there is 4-5h out."""
    utc = datetime(2025, 6, 10, 17, 0, tzinfo=timezone.utc)   # = 13:00 ET
    assert utc.hour == 17                                # would look forbidden
    assert SESSION_WINDOW.is_admissible(utc)             # 13:00 ET: admissible
    assert SESSION_WINDOW.cycle_key(utc) == date(2025, 6, 10)


def test_h1_naive_datetime_is_treated_as_et():
    """``to_et`` assumes a naive stamp is already Eastern (``timeutil.py:45-47``)."""
    assert SESSION_WINDOW.is_forbidden(datetime(2025, 6, 10, 16, 30))
    assert SESSION_WINDOW.is_admissible(datetime(2025, 6, 10, 18, 30))


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_h1_cycle_key_agrees_with_trading_day_where_both_are_defined(symbol):
    """Independent cross-check against the repo's own CME-day arithmetic.

    ``timeutil.trading_day`` has been in this codebase since long before this
    rule and uses the same 18:00 boundary. It must agree on every admissible bar,
    and it must be the one that *disagrees* inside the forbidden window - that
    disagreement is exactly why ``cycle_key`` exists rather than reusing it.
    """
    bars = ARCHIVE.load(symbol, 60).bars
    assert bars
    disagreements = 0
    forbidden_seen = 0
    for b in bars:
        k = SESSION_WINDOW.cycle_key(b.ts)
        if k is None:
            forbidden_seen += 1
            assert trading_day(b.ts) is not None      # trading_day still answers
            continue
        if k != trading_day(b.ts):
            disagreements += 1
    assert disagreements == 0
    assert forbidden_seen > 0


# ==========================================================================
# EF7-H2 - which bar ends a cycle
# ==========================================================================

def test_h2_known_answer_flat_flags_on_a_contiguous_cycle():
    bars = hourly_cycle(date(2025, 6, 10), include_1600=True)
    flags = flat_flags(bars)
    # 22 admissible bars 18:00..15:00, then the forbidden 16:00 bar.
    assert len(bars) == 23
    assert to_et(bars[21].ts).hour == 15 and to_et(bars[22].ts).hour == 16
    assert flags[:21] == [False] * 21          # nothing closes mid-cycle
    assert flags[21] is True                   # 15:00-16:00 is the flat bar
    assert flags[22] is True                   # forbidden bar: cannot hold, ever


def test_h2_last_element_is_undetermined_not_false():
    bars = hourly_cycle(date(2025, 6, 10), include_1600=False)
    flags = flat_flags(bars)
    assert flags[-1] is None
    assert all(f is False for f in flags[:-1])


def test_h2_naive_end_ts_rule_violates_the_spec_and_flat_flags_does_not():
    """The known-answer test for the defect the obvious implementation carries.

    Measured on the real substrate: 17 of 506 MGC 60m cycles and 35 of 505 MCL
    cycles have no printed bar between some earlier hour and 16:00. This fixture
    reproduces one - bars stop at 14:00 and resume at 16:00. The naive rule
    "close when ``bar.end_ts >= 16:00``" then picks the **16:00-17:00** bar,
    exiting inside the forbidden window.
    """
    bars = hourly_cycle(date(2025, 6, 10), include_1600=True,
                        skip_hours=(14, 15))
    hours = [to_et(b.ts).hour for b in bars]
    assert 14 not in hours and 15 not in hours and 16 in hours

    def naive_flat(b):
        """"Close when the bar's end reaches the cycle's 16:00 deadline", with
        the cycle keyed off ``trading_day`` the way the rest of this repository
        keys a CME session. Reads correctly. Is wrong."""
        deadline = datetime.combine(trading_day(b.ts), time(16, 0), tzinfo=ET)
        return to_et(b.end_ts) >= deadline

    naive = [i for i, b in enumerate(bars) if naive_flat(b)]
    # The naive rule's first - and only - firing bar is the forbidden 16:00 one,
    # so the position exits at 17:00 ET, inside the window it must not be in.
    assert naive, "naive rule never fired; fixture no longer exercises the defect"
    assert to_et(bars[naive[0]].ts).hour == 16
    assert SESSION_WINDOW.is_forbidden(bars[naive[0]].ts)

    flags = flat_flags(bars)
    fired = [i for i, f in enumerate(flags) if f is True]
    # ...while ours fires on the 13:00-14:00 bar, the last bar in the cycle.
    assert to_et(bars[fired[0]].ts).hour == 13
    assert SESSION_WINDOW.is_admissible(bars[fired[0]].ts)
    assert to_et(bars[fired[0]].end_ts) <= SESSION_WINDOW.flat_instant(bars[fired[0]].ts)


def test_h2_flat_decision_reads_the_successor_timestamp_and_no_successor_price():
    """Discharges the look-ahead claim rather than asserting it.

    Every OHLCV field of every bar after index 5 is replaced with nonsense. If
    the decision touched a future price at all, the flags would move.
    """
    bars = hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
    before = flat_flags(bars)
    mutated = list(bars[:6]) + [
        replace(b, open=9e4, high=9e4 + 1, low=9e4 - 1, close=9e4, volume=7.0)
        for b in bars[6:]]
    assert flat_flags(mutated) == before


def test_h2_prefix_invariance_on_synthetic_bars():
    bars = (hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
            + hourly_cycle(date(2025, 6, 12)))
    full = flat_flags(bars)
    for k in range(1, len(bars) + 1):
        assert flat_flags(bars[:k])[:k - 1] == full[:k - 1], f"prefix k={k}"


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_h2_prefix_invariance_on_real_bars(symbol):
    """Appending a future bar never changes a historical decision.

    Done with ``stop_at`` over the real series rather than by re-slicing 11,000
    times, which is the same statement and is O(n) instead of O(n^2). A small
    dense sweep of literal slices is done alongside it so the two formulations
    are cross-checked.
    """
    bars = ARCHIVE.load(symbol, 60).bars
    full = flat_flags(bars)
    for k in range(1, len(bars) + 1, 37):
        assert flat_flags(bars, stop_at=k)[:k - 1] == full[:k - 1], f"{symbol} k={k}"
    for k in range(1, 400):
        assert flat_flags(bars[:k])[:k - 1] == full[:k - 1], f"{symbol} slice k={k}"


@pytest.mark.parametrize("symbol", SYMBOLS)
def test_h2_cycle_keys_are_prefix_invariant_trivially(symbol):
    bars = ARCHIVE.load(symbol, 60).bars
    full = cycle_keys(bars)
    for k in (1, 2, 17, 500, 5000, len(bars)):
        assert cycle_keys(bars[:k]) == full[:k]


def test_h2_entry_veto_tests_the_fill_instant_not_the_signal_instant():
    """Off-by-one-bar here is silent and inverts the rule.

    A signal on the 15:00 bar fills at 16:00 and must be refused. A signal on the
    17:00 bar fills at 18:00 - the first admissible instant of the next cycle -
    and must be allowed.
    """
    bars = (hourly_cycle(date(2025, 6, 10), include_1600=True, include_1700=True)
            + hourly_cycle(date(2025, 6, 11)))
    veto = entry_veto_flags(bars)
    by_hour = {to_et(b.ts).hour: veto[i] for i, b in enumerate(bars[:24])}
    assert by_hour[15] is True     # fills 16:00 -> refused
    assert by_hour[16] is True     # fills 17:00 -> refused
    assert by_hour[17] is False    # fills 18:00 -> allowed (overnight entry)
    assert by_hour[14] is False
    assert veto[-1] is None


# ==========================================================================
# EF7-H3 - the engine
# ==========================================================================

def _run(bars, strategy, costs=None, **kw):
    frame = frame_from(bars, strategy.symbol)
    eng = SessionWindowEngine(frame, costs or no_slip(), **kw)
    res = eng.run(strategy)
    return eng, res


def test_h3_known_answer_every_position_closes_at_the_1600_flat():
    bars = (hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
            + hourly_cycle(date(2025, 6, 12)))
    eng, res = _run(bars, fixture_strategy())
    assert res.trades, "fixture produced no trades - the test would be vacuous"
    for t in res.trades[:-1]:
        assert t.exit_reason is SESSION_WINDOW_EXIT, t.exit_reason
        assert to_et(t.exit_ts).hour == 15          # exit bar 15:00-16:00
        assert to_et(t.exit_ts) + timedelta(minutes=60) == \
            SESSION_WINDOW.flat_instant(t.exit_ts)
    assert eng.stats.flat_exits >= 2
    assert eng.stats.flat_on_forbidden_bar == 0
    assert eng.stats.flat_on_late_bar == 0


def test_h3_known_answer_entry_in_the_window_is_vetoed():
    bars = (hourly_cycle(date(2025, 6, 10), include_1600=True, include_1700=True)
            + hourly_cycle(date(2025, 6, 11), include_1600=True, include_1700=True)
            + hourly_cycle(date(2025, 6, 12)))
    eng, res = _run(bars, fixture_strategy())
    assert eng.stats.entries_vetoed > 0, "nothing was vetoed - the veto is untested"
    for t in res.trades:
        assert SESSION_WINDOW.is_admissible(t.entry_ts), t.entry_ts
    # And an entry does land at 18:00, so the veto is not just refusing everything.
    assert any(to_et(t.entry_ts).hour == 18 for t in res.trades)


def test_h3_known_answer_no_trade_spans_the_forbidden_window():
    bars = (hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
            + hourly_cycle(date(2025, 6, 12)))
    _, res = _run(bars, fixture_strategy())
    assert trade_violations(res.trades, base_minutes=60) == []


def test_h3_the_unmodified_engine_fails_this_same_assertion():
    """The control. Without the rule the invariant is breached, so the invariant
    is capable of failing and its zero on the real data means something."""
    bars = (hourly_cycle(date(2025, 6, 10), include_1600=True, include_1700=True)
            + hourly_cycle(date(2025, 6, 11), include_1600=True, include_1700=True)
            + hourly_cycle(date(2025, 6, 12)))
    frame = frame_from(bars)
    shipped = BacktestEngine(frame, no_slip(), allow_overnight=True)
    res = shipped.run(fixture_strategy())
    assert res.trades
    v = trade_violations(res.trades, base_minutes=60)
    assert v, "the shipped engine did not breach the rule - control is broken"
    assert {x["kind"] for x in v} & {"entry_in_window", "exit_in_window",
                                     "spans_window"}


def whole_tick_costs(symbol="MGC"):
    """Costs whose slippage is a whole number of ticks, so a price assertion is
    exact rather than blurred by ``round_to_tick``.

    ``volatility_coefficient=0`` is not a simplification for its own sake: with
    the shipped 0.6 the flat's slippage depends on the fixture's ATR percentile,
    and the test would then be asserting the ATR pipeline rather than the flat.
    ``test_h3_flat_slippage_includes_the_volatility_term`` covers the term that
    is switched off here.
    """
    return CostModel(spec=get_contract(symbol),
                     slippage=SlippageModel(base_ticks=1.0,
                                            stop_order_extra_ticks=1.0,
                                            volatility_coefficient=0.0,
                                            thin_book_extra_ticks=1.0),
                     commission_override=0.0)


@pytest.mark.parametrize("direction", [Direction.LONG, Direction.SHORT])
def test_h3_flat_charges_market_order_slippage_adversely(direction):
    """Component 3. The shipped time/session/end-of-data exits hand ``bar.close``
    straight through with no slippage (``engine.py:467,473,476``); a rule that
    fires on every position must not inherit that."""
    bars = hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
    spec = get_contract("MGC")
    strat = fixture_strategy(direction=direction)

    _, free = _run(bars, strat, no_slip())
    _, paid = _run(bars, strat, whole_tick_costs())
    flats_free = [t for t in free.trades if t.exit_reason is SESSION_WINDOW_EXIT]
    flats_paid = [t for t in paid.trades if t.exit_reason is SESSION_WINDOW_EXIT]
    assert flats_free and len(flats_free) == len(flats_paid)

    sign = direction.sign
    for a, b in zip(flats_free, flats_paid):
        # 16:00 ET is outside MGC's 08:20-13:30 RTH, so the thin-book term
        # applies: base 1 + market-order 1 + thin 1 = 3 ticks = 0.3 points.
        expected = spec.round_to_tick(a.exit_price - sign * 3.0 * spec.tick_size)
        assert b.exit_price == pytest.approx(expected, abs=1e-9), (
            f"{direction} flat: got {b.exit_price}, want {expected}")
        # Adverse in both directions, never favourable.
        assert (b.exit_price < a.exit_price) if sign > 0 else (b.exit_price > a.exit_price)
        assert b.net_r < a.net_r


def test_h3_flat_slippage_includes_the_volatility_term():
    """The shipped model widens slippage with the ATR percentile
    (``costs.py:41-42``) and the flat must not be exempt from that either.

    Run on real bars, not the synthetic fixture: the fixture's ranges are almost
    constant, so its ``atr_percentile`` never exceeds 0.36 and only the upper half
    of the distribution adds slippage. A synthetic fixture would pass this test by
    never exercising the term, which is the failure mode it exists to catch.
    """
    bars = ARCHIVE.load("MGC", 60).bars[:1500]
    spec = get_contract("MGC")
    flat_px = {}
    for coeff in (0.0, 0.6):
        costs = CostModel(spec=spec,
                          slippage=SlippageModel(volatility_coefficient=coeff),
                          commission_override=0.0)
        _, res = _run(bars, fixture_strategy(), costs)
        flat_px[coeff] = [(to_et(t.exit_ts), t.exit_price) for t in res.trades
                          if t.exit_reason is SESSION_WINDOW_EXIT]
    assert flat_px[0.0] and len(flat_px[0.0]) == len(flat_px[0.6])
    pairs = [(a[1], b[1]) for a, b in zip(flat_px[0.0], flat_px[0.6])
             if a[0] == b[0]]
    assert any(b < a for a, b in pairs), \
        "the volatility term never bit - no flat bar had atr_percentile > 0.5"


def test_h3_flat_slippage_can_be_priced_as_a_limit_for_comparison():
    """``flat_is_market_order=False`` prices it as a marketable limit instead.

    Kept as a parameter so the cost assumption can be varied and reported rather
    than buried; the default is the market-order reading because that is what a
    mandatory 16:00 flat actually is.
    """
    bars = hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
    spec = get_contract("MGC")
    costs = whole_tick_costs()
    _, mkt = _run(bars, fixture_strategy(), costs, flat_is_market_order=True)
    _, lim = _run(bars, fixture_strategy(), costs, flat_is_market_order=False)
    a = [t for t in mkt.trades if t.exit_reason is SESSION_WINDOW_EXIT]
    b = [t for t in lim.trades if t.exit_reason is SESSION_WINDOW_EXIT]
    assert a and len(a) == len(b)
    # A market order costs exactly one extra tick (stop_order_extra_ticks=1.0).
    for x, y in zip(a, b):
        assert y.exit_price - x.exit_price == pytest.approx(spec.tick_size, abs=1e-9)


def test_h3_stop_wins_over_the_flat_in_the_same_bar():
    """Invariant 4 must survive the new exit: the pessimistic reading, always."""
    bars = hourly_cycle(date(2025, 6, 10))
    # Make the 15:00-16:00 bar - the flat bar - trade through a tight stop.
    i = next(k for k, b in enumerate(bars) if to_et(b.ts).hour == 15)
    bars[i] = replace(bars[i], low=bars[i].low - 50.0)
    strat = fixture_strategy(stop_ticks=40.0)      # 4.0 points on MGC
    eng, res = _run(bars, strat)
    assert res.trades
    last = res.trades[-1]
    assert last.exit_reason is ExitReason.STOP, last.exit_reason
    assert eng.stats.flat_exits == 0


def test_h3_target_wins_over_the_flat_in_the_same_bar():
    bars = hourly_cycle(date(2025, 6, 10))
    i = next(k for k, b in enumerate(bars) if to_et(b.ts).hour == 15)
    bars[i] = replace(bars[i], high=bars[i].high + 50.0)
    strat = fixture_strategy(stop_ticks=40.0, targets=(1.0,))
    eng, res = _run(bars, strat)
    assert res.trades
    assert res.trades[-1].exit_reason is ExitReason.TARGET
    assert eng.stats.flat_exits == 0


def test_h3_time_stop_wins_over_the_flat_in_the_same_bar():
    """Deliberate ordering choice, recorded as a test so it is not accidental.

    The flat is checked *after* the shipped ladder, so a time stop landing on the
    flat bar keeps its own attribution. That is what makes ``flat_exits`` mean
    "positions the rule closed that had no other reason to close on that bar",
    which is the number the closure count is supposed to report. The cost is that
    such a trade exits at ``bar.close`` with no slippage - inherited from
    ``engine.py:467``, not introduced here.
    """
    bars = hourly_cycle(date(2025, 6, 10))
    # Entry fills on the 19:00 bar; a 21-bar time stop lands on 15:00-16:00.
    strat = fixture_strategy(time_stop=21)
    eng, res = _run(bars, strat)
    assert res.trades
    t = res.trades[0]
    assert t.exit_reason is ExitReason.TIME
    assert to_et(t.exit_ts).hour == 15
    assert eng.stats.flat_exits == 0


def test_h3_shipped_contract_rth_close_exit_is_inert():
    """Behavioural, not a source-string match. MGC's RTH close is 13:30
    (``config.py:164``); if the shipped exit were live, every trade would end
    there and no 15:00 flat would ever be reached."""
    bars = (hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11)))
    eng, res = _run(bars, fixture_strategy())
    assert res.trades
    assert all(t.exit_reason is not ExitReason.SESSION_CLOSE for t in res.trades)
    assert any(to_et(t.exit_ts).hour == 15 for t in res.trades)
    assert eng.allow_overnight is True

    # And the control: with the shipped engine the session exit DOES fire.
    shipped = BacktestEngine(frame_from(bars), no_slip())
    sres = shipped.run(fixture_strategy())
    assert any(t.exit_reason is ExitReason.SESSION_CLOSE for t in sres.trades)
    assert all(t.exit_reason is ExitReason.SESSION_CLOSE for t in sres.trades)


def test_ef7_d2_shipped_session_exit_closes_an_evening_entry_on_its_entry_bar():
    """EF7-D2. The shipped exit is not "flat at the RTH close".

    ``elapsed = minutes_since_open(bar.ts, spec.rth_open) + bar.minutes``
    (``engine.py:471``) is measured from the RTH open **of the bar's own calendar
    date** and is never clamped, so for MGC (``_rth_minutes`` = 310) it is
    ``>= 310`` for every bar opening at or after 12:30 ET and stays true all
    evening: 19:00 gives 760, 23:00 gives 940. It goes *negative* again after
    midnight, so 00:00-12:29 ET holds normally.

    The consequence is not cosmetic. A position entered in the evening session is
    closed on its **entry bar** - one bar held, a full round turn paid. Measured
    on the fixture: 17 of 19 trades exit at ``bars_held == 1``. So the shipped
    engine cannot carry an overnight position at all, which is a stronger
    statement than "every prior evaluation was flat by its contract's RTH close",
    and it means an arm-A baseline on a ``rth_only=False`` population is measuring
    that artefact rather than overnight trading.
    """
    bars = hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
    shipped = BacktestEngine(frame_from(bars), no_slip())
    res = shipped.run(fixture_strategy())
    assert res.trades
    evening = [t for t in res.trades if to_et(t.entry_ts).hour >= 18]
    assert evening, "fixture took no evening entries"
    assert all(t.bars_held == 1 for t in evening), \
        [(str(t.entry_ts), t.bars_held) for t in evening]
    assert all(t.exit_reason is ExitReason.SESSION_CLOSE for t in evening)
    # Post-midnight entries are held normally, which is the other half of the bug.
    small_hours = [t for t in res.trades if to_et(t.entry_ts).hour < 12]
    assert small_hours and max(t.bars_held for t in small_hours) > 5

    # Under the window rule the same evening entries are held to the 16:00 flat.
    eng, wres = _run(bars, fixture_strategy())
    w_evening = [t for t in wres.trades if to_et(t.entry_ts).hour >= 18]
    assert w_evening and all(t.bars_held > 1 for t in w_evening)


def test_h3_end_argument_does_not_leak_past_the_run_window():
    """A run with ``end=k`` must not decide bar ``k-1`` from ``bars[k]``.

    Compared against the same strategy run over a frame physically truncated to
    ``k`` bars - if the engine peeked past ``end``, the two would differ.
    """
    bars = (hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
            + hourly_cycle(date(2025, 6, 12)))
    strat = fixture_strategy()
    for k in (25, 26, 44, 47, 60):
        eng_a = SessionWindowEngine(frame_from(bars), no_slip())
        a = eng_a.run(strat, end=k)
        eng_b = SessionWindowEngine(frame_from(bars[:k]), no_slip())
        b = eng_b.run(strat)
        assert [(t.entry_ts, t.exit_ts, t.exit_reason, round(t.net_r, 9))
                for t in a.trades] == \
               [(t.entry_ts, t.exit_ts, t.exit_reason, round(t.net_r, 9))
                for t in b.trades], f"end={k} leaked"


def test_h3_prefix_invariance_of_realised_trades():
    """The engine-level form of invariant 1: a closed trade never changes when
    later bars arrive. Only the final, still-open position may differ."""
    bars = (hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
            + hourly_cycle(date(2025, 6, 12)))
    strat = fixture_strategy()
    full = SessionWindowEngine(frame_from(bars), no_slip()).run(strat)
    key = lambda t: (to_et(t.entry_ts), to_et(t.exit_ts), t.exit_reason.value,
                     round(t.exit_price, 9), round(t.net_r, 9))
    ref = [key(t) for t in full.trades]
    for k in range(3, len(bars) + 1):
        part = SessionWindowEngine(frame_from(bars[:k]), no_slip()).run(strat)
        got = [key(t) for t in part.trades]
        # Drop the last trade of the prefix: it may be an END_OF_DATA truncation
        # of a position the full series carried further.
        assert got[:-1] == ref[:len(got) - 1], f"prefix k={k}"


def test_h3_determinism():
    bars = hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
    strat = fixture_strategy()
    runs = []
    for _ in range(3):
        eng, res = _run(bars, strat, CostModel(spec=get_contract("MGC")))
        runs.append(([t.to_dict() for t in res.trades], eng.stats.to_dict()))
    assert runs[0] == runs[1] == runs[2]


def test_h3_commission_is_charged_exactly_once_on_a_flat_exit():
    bars = hourly_cycle(date(2025, 6, 10)) + hourly_cycle(date(2025, 6, 11))
    spec = get_contract("MGC")
    costs = CostModel(spec=spec)
    _, res = _run(bars, fixture_strategy(), costs)
    flats = [t for t in res.trades if t.exit_reason is SESSION_WINDOW_EXIT]
    assert flats
    for t in flats:
        assert t.commission_dollars == pytest.approx(
            2.0 * costs.commission_per_side())


def test_h3_arm_ids_are_unique_when_built_by_replace():
    """D48 guard. ``dataclasses.replace`` inherits the memoised ``_id``, so two
    arms silently collide into one ``BacktestResult`` and the measured difference
    is exactly zero - indistinguishable from "this makes no difference"."""
    base = fixture_strategy()
    _ = base.strategy_id                      # memoise it, as D48 requires
    bad = replace(base, exit=replace(base.exit, targets_r=(3.0,)))
    assert bad.strategy_id == base.strategy_id, "D48 no longer reproduces"
    good = replace(base, exit=replace(base.exit, targets_r=(3.0,)), _id=None)
    assert good.strategy_id != base.strategy_id
    assert len({base.strategy_id, good.strategy_id}) == 2


def test_h3_flat_fires_early_when_the_cycle_data_ends_early_and_says_so():
    """Measured on the archive: 17/506 MGC and 35/505 MCL 60m cycles end before
    16:00. The flat must fire at the last printed bar - not later - and the
    counter must record that it was early, because an early flat is a real
    deviation from the rule caused by the data, not by the rule."""
    bars = (hourly_cycle(date(2025, 6, 10), include_1600=False,
                         skip_hours=(14, 15))
            + hourly_cycle(date(2025, 6, 11)))
    eng, res = _run(bars, fixture_strategy())
    early = [t for t in res.trades
             if t.exit_reason is SESSION_WINDOW_EXIT and to_et(t.exit_ts).hour == 13]
    assert early, "the early-cycle-end path was never exercised"
    assert eng.stats.flat_before_deadline >= 1
    assert trade_violations(res.trades, base_minutes=60) == []


# ==========================================================================
# The violation detector, shown rejecting each clause
# ==========================================================================

def _fake_trade(entry, exit_, reason=ExitReason.TIME):
    return Trade(strategy_id="X", strategy_name="X", group="G", symbol="MGC",
                 direction=Direction.LONG, signal_ts=entry, signal_index=0,
                 entry_ts=entry, entry_index=1, entry_price=100.0,
                 initial_stop=99.0, targets=[102.0], risk_points=1.0,
                 exit_ts=exit_, exit_reason=reason)


def test_detector_catches_an_entry_inside_the_window():
    t = _fake_trade(et(2025, 6, 10, 16, 0), et(2025, 6, 10, 18, 0))
    kinds = {v["kind"] for v in trade_violations([t], base_minutes=60)}
    assert "entry_in_window" in kinds


def test_detector_catches_an_exit_inside_the_window():
    t = _fake_trade(et(2025, 6, 10, 12, 0), et(2025, 6, 10, 16, 0))
    kinds = {v["kind"] for v in trade_violations([t], base_minutes=60)}
    assert "exit_in_window" in kinds


def test_detector_catches_an_exit_bar_that_runs_past_the_deadline():
    """A 240m bar opening 14:00 would end at 18:00; the fill could be anywhere
    inside, so the whole bar has to be rejected even though 14:00 is legal."""
    t = _fake_trade(et(2025, 6, 10, 10, 0), et(2025, 6, 10, 14, 0))
    assert trade_violations([t], base_minutes=120) == []      # ends 16:00: legal
    kinds = {v["kind"] for v in trade_violations([t], base_minutes=240)}
    assert "exit_in_window" in kinds                          # ends 18:00: not


def test_detector_catches_a_trade_spanning_the_window():
    t = _fake_trade(et(2025, 6, 10, 12, 0), et(2025, 6, 11, 12, 0))
    kinds = {v["kind"] for v in trade_violations([t], base_minutes=60)}
    assert "spans_window" in kinds


def test_detector_passes_a_legal_trade():
    t = _fake_trade(et(2025, 6, 9, 18, 0), et(2025, 6, 10, 15, 0))
    assert trade_violations([t], base_minutes=60) == []
    t2 = _fake_trade(et(2025, 6, 10, 15, 0), et(2025, 6, 10, 15, 0))
    assert trade_violations([t2], base_minutes=60) == []


# ==========================================================================
# The invariant on realised trades, over real bars, all four symbols
# ==========================================================================

@pytest.mark.parametrize("symbol", SYMBOLS)
def test_invariant_holds_on_real_archive_bars(symbol):
    """The headline check: zero violations over ~11,000 real 60m bars per symbol.

    Run with the fixture's always-fire signal rather than a generated strategy on
    purpose - it opens a position at the first admissible instant of every cycle
    and so exercises the flat on essentially every cycle in the series, which a
    selective strategy would not. Both directions, so a sign error cannot hide.
    """
    bars = ARCHIVE.load(symbol, 60).bars
    assert len(bars) > 10_000
    frame = SymbolFrame(BarSeries(symbol, 60, bars), (60,), get_contract(symbol))
    for direction in (Direction.LONG, Direction.SHORT):
        eng = SessionWindowEngine(frame, CostModel(spec=get_contract(symbol)))
        res = eng.run(fixture_strategy(symbol, direction=direction,
                                       name=f"EF7-inv-{direction.value}"))
        assert len(res.trades) > 100, f"{symbol} {direction}: too few trades"
        v = trade_violations(res.trades, base_minutes=60)
        assert v == [], f"{symbol} {direction}: {len(v)} violations, first {v[:3]}"
        assert eng.stats.flat_on_forbidden_bar == 0
        assert eng.stats.flat_on_late_bar == 0
        assert eng.stats.entries_vetoed > 0
