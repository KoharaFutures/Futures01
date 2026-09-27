"""Tests for ALGO-1's event clock and gates.

Run: ``python -m pytest -q workspace/roundtable/backtest/BT2/code/test_algo1.py``

The tests are grouped by what they defend, and the grouping is the point:

* **Fidelity** - the clock reproduces ``features.py``'s three news fields bar for
  bar on real MGC and MCL series. Without this the gates are a second opinion
  about the calendar rather than a generalisation of the library's, and no
  measurement made with them could be compared with F11's.
* **Look-ahead** - appending a future bar cannot change a historical reading, and
  the reading for one bar does not depend on the series it sits in.
* **Silent-wrong-answer guards** - the two mechanisms that would make a wrong
  number look like a right one: the ``(name, tf)`` condition cache collapsing two
  parameterisations into one, and ``strategy_id`` collapsing two arms into one.
* **Structural zeros** - configurations in which a gate can never fire, asserted
  so they are known rather than discovered as "the idea does not work".
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from futures_agents.data.bars import BarSeries                          # noqa: E402
from futures_agents.econ_calendar import Impact                         # noqa: E402
from futures_agents.features import (NEWS_BLACKOUT_AFTER_MIN,           # noqa: E402
                                     NEWS_BLACKOUT_BEFORE_MIN,
                                     build_symbol_frame)
from futures_agents.schema import Direction                             # noqa: E402
from futures_agents.strategies.base import (Condition, ConditionKind,    # noqa: E402
                                            ConditionResult, ExitModel,
                                            Strategy, StrategyFilters)
from futures_agents.timeutil import ET, UTC, is_rth                     # noqa: E402

import algo1                                                            # noqa: E402
import event_gate as G                                                  # noqa: E402
from event_clock import EventClock, EventClockError, census              # noqa: E402

TF = 60
SLICE = 1200        # bars; enough to span several event days, fast enough to run


def _frame(symbol: str, tf: int = TF, n: int = SLICE):
    """A frame over the LAST ``n`` bars of a csv/raw series."""
    series = algo1.load_series(symbol, tf)
    bars = list(series.bars)[-n:]
    return build_symbol_frame(BarSeries(symbol, tf, bars), [tf])


# ==========================================================================
# Fidelity: the clock is the library's clock, generalised
# ==========================================================================

#: ``features.py:955`` projects events from ``bars[0].ts - 2 days`` only, against
#: ``+45 days`` forward. So ``minutes_since_high_impact`` is ``inf`` on every bar
#: before the series' own first HIGH print, however long ago the real previous
#: print was. See ``test_features_news_lookback_is_two_days_and_why_it_is_inert``.
_FEATURES_LOOKBACK_MIN = 2 * 24 * 60


@pytest.mark.parametrize("symbol", ["MGC", "MCL", "MNQ"])
def test_clock_reproduces_the_librarys_news_fields_bar_for_bar(symbol):
    """min_impact=HIGH, offset 0 == features.py, on every bar of a real series.

    ``features.py`` walks a pointer over a locally-sliced event list; this clock
    bisects the exact list. Agreement on every bar is what licenses using the
    generalised clock in place of the library's.

    One documented exception, asserted rather than excused: at the head of a
    series ``features.py`` reports ``since = inf`` where the true gap exceeds its
    2-day lookback. Those bars are checked against the exact form of the
    artefact, so a *different* disagreement would still fail this test.
    """
    frame = _frame(symbol)
    clock = EventClock(symbol, min_impact=Impact.HIGH)
    before, after = float(NEWS_BLACKOUT_BEFORE_MIN), float(NEWS_BLACKOUT_AFTER_MIN)
    checked = agreed = artefact = 0
    for i in range(len(frame.base.bars)):
        snap = frame.snapshot(i)
        r = clock.read_bar(snap.ts, 0.0)
        assert r.to_next == pytest.approx(snap.minutes_to_high_impact), \
            f"{symbol} bar {i} {snap.ts}: to_next"
        if snap.minutes_since_high_impact == float("inf") and \
                r.since_prev != float("inf"):
            # The lookback artefact, and it may ONLY appear beyond the lookback.
            assert r.since_prev > _FEATURES_LOOKBACK_MIN, \
                f"{symbol} bar {i} {snap.ts}: inf inside the 2-day lookback"
            artefact += 1
        else:
            assert r.since_prev == pytest.approx(snap.minutes_since_high_impact), \
                f"{symbol} bar {i} {snap.ts}: since_prev"
            agreed += 1
        # The blackout flag must match on EVERY bar without exception: both of
        # its bounds are far inside the 2-day lookback, so the artefact cannot
        # reach it.
        mine = (r.since_prev <= after) or (r.to_next <= before)
        assert mine == snap.in_news_blackout, \
            f"{symbol} bar {i} {snap.ts}: blackout"
        checked += 1
    assert checked == SLICE
    assert agreed > 0.9 * SLICE, f"{symbol}: only {agreed}/{SLICE} bars agreed"


def test_features_news_lookback_is_two_days_and_why_it_is_inert():
    """Pin the artefact, and pin the reason it changes no library answer.

    ``_build_news_proximity`` projects ``bars[0].ts - 2 days .. bars[-1].ts + 45
    days`` (``features.py:955-959``). The forward side carries a comment
    explaining why 45 days; the backward side is 2 days with no comment, and it
    is the asymmetry that gives it away. Consequence:
    ``minutes_since_high_impact`` reads ``inf`` - "no high-impact release has ever
    happened" - on the bars before the first print inside that window.

    It is **behaviourally inert for the library**, and that is worth asserting
    rather than assuming: the artefact can only fire when the true gap exceeds
    2,880 minutes, and every window any library condition uses is at most 60
    (``outside_news_blackout`` 10/15, ``no_imminent_release`` 30,
    ``post_news_window`` 15/60). So a hidden value is always already outside
    every window. It stops being inert for any condition with a window wider
    than two days - which is why ALGO-1 reads its own clock rather than the
    snapshot fields.
    """
    from futures_agents.strategies.library import CONDITIONS
    series = algo1.load_series("MGC", TF)
    frame = build_symbol_frame(series, [TF])
    hidden = []
    clock = EventClock("MGC")
    lib_gates = [CONDITIONS[n] for n in ("outside_news_blackout",
                                         "no_imminent_release",
                                         "post_news_window")]
    mine = [G.avoid_event(), G.into_event(0, 30), G.after_event()]
    for i in range(len(series.bars)):
        snap = frame.snapshot(i)
        if snap.minutes_since_high_impact == float("inf"):
            hidden.append(clock.read_bar(snap.ts).since_prev)
        # The three library gates and their three generalisations must agree on
        # every bar of the whole series, artefact bars included.
        for lib, g in zip(lib_gates, mine):
            if lib.name == "no_imminent_release":
                continue        # into_event is its NEGATION, not its twin
            assert lib.evaluate(snap, TF).triggered is \
                g.evaluate(snap, TF).triggered, f"bar {i} {snap.ts} {lib.name}"
    assert hidden, "no artefact bars found - has features.py changed?"
    assert min(hidden) > _FEATURES_LOOKBACK_MIN
    # Measured on MGC_1h: 56 of 5,000 bars carry the artefact and the largest
    # hidden gap is 10,050 minutes - 6.98 days, i.e. a whole CPI-to-NFP interval
    # reported as "no release has ever happened".
    assert max(hidden) > 6 * 24 * 60


def test_avoid_gate_at_library_settings_matches_outside_news_blackout():
    """The avoid gate is ``outside_news_blackout``, on every bar."""
    from futures_agents.strategies.library import CONDITIONS
    lib = CONDITIONS["outside_news_blackout"]
    gate = G.avoid_event()          # defaults ARE the library's 10 / 15
    frame = _frame("MGC")
    for i in range(len(frame.base.bars)):
        snap = frame.snapshot(i)
        assert gate.evaluate(snap, TF).triggered is lib.evaluate(snap, TF).triggered


def test_after_gate_at_library_settings_matches_post_news_window():
    """The after gate is ``post_news_window``, on every bar."""
    from futures_agents.strategies.library import CONDITIONS
    lib = CONDITIONS["post_news_window"]
    gate = G.after_event()          # defaults ARE the library's 15 / 60
    for symbol in ("MGC", "MCL"):
        frame = _frame(symbol)
        for i in range(len(frame.base.bars)):
            snap = frame.snapshot(i)
            assert gate.evaluate(snap, TF).triggered is \
                lib.evaluate(snap, TF).triggered, f"{symbol} bar {i} {snap.ts}"


# ==========================================================================
# Look-ahead
# ==========================================================================

def test_appending_a_bar_never_changes_a_historical_reading():
    """Invariant 1, on the calendar axis.

    The clock is read over a short prefix and then over the full series; every
    reading in the prefix must be identical. A calendar that projected only as
    far as the data reached would fail this at the tail, which is exactly why
    ``features.py`` projects ``+45d`` past its last bar.
    """
    series = algo1.load_series("MGC", TF)
    bars = list(series.bars)[-400:]
    clock = EventClock("MGC")
    short = [clock.read_bar(b.ts) for b in bars[:200]]
    full = [clock.read_bar(b.ts) for b in bars]
    assert short == full[:200]


def test_a_reading_does_not_depend_on_the_series_it_sits_in():
    """Span independence: per-year caching, not per-series projection."""
    clock = EventClock("MCL")
    ts = datetime(2026, 3, 18, 15, 0, tzinfo=ET)
    a = clock.read(ts)
    # Ask about a distant instant first, forcing other years into the cache,
    # then re-ask. A span-dependent implementation would drift.
    clock.read(datetime(2019, 1, 2, 9, 0, tzinfo=ET))
    clock.read(datetime(2027, 12, 31, 9, 0, tzinfo=ET))
    assert clock.read(ts) == a


def test_events_shifted_across_a_year_boundary_are_kept_exactly_once():
    """Per-year caching with padding must not lose or duplicate an event.

    ``_rule_dates`` does not month-filter weekly/eia/empsit patterns
    (``econ_calendar.py:366-372``) precisely so a holiday shift can move an event
    into the neighbouring month; the year boundary is the same problem one level
    up. Counted against a single uninterrupted projection.
    """
    from futures_agents.econ_calendar import project_events
    clock = EventClock("MCL")
    lo = datetime(2025, 12, 1, tzinfo=ET)
    hi = datetime(2026, 2, 1, tzinfo=ET)
    direct = [e for e in project_events(lo, hi, symbol="MCL")
              if e.impact.rank >= Impact.HIGH.rank]
    mine = clock.events(lo, hi)
    assert [(e.name, e.when) for e in mine] == [(e.name, e.when) for e in direct]


# ==========================================================================
# Silent-wrong-answer guards
# ==========================================================================

def test_every_parameterisation_gets_its_own_condition_name():
    """The ``(name, tf)`` cache (base.py:120) collapses same-named conditions.

    Two gates differing only in window width must not share a name, or the
    second silently receives the first's answer for the whole bar - R2's
    ``R2_expressibility_wall.md`` §1.5 mechanism, and the same shape as D38.
    """
    gates = [
        G.avoid_event(), G.avoid_event(30, 30), G.avoid_event(offset_min=60),
        G.after_event(), G.after_event(15, 120), G.after_event(cluster_minutes=60),
        G.after_event(min_impact=Impact.MEDIUM), G.after_event(offset_min=60),
        G.into_event(), G.into_event(0, 60),
    ]
    names = [g.name for g in gates]
    assert len(set(names)) == len(names), names


def test_two_gates_in_one_shared_cache_do_not_contaminate_each_other():
    """The collision above, exercised through the engine's actual cache object."""
    frame = _frame("MCL", n=400)
    narrow, wide = G.after_event(15, 60), G.after_event(15, 600)
    disagreements = 0
    for i in range(len(frame.base.bars)):
        snap = frame.snapshot(i)
        cache = {}                       # one per bar, exactly as run_many does
        a = narrow.evaluate(snap, TF, cache).triggered
        b = wide.evaluate(snap, TF, cache).triggered
        if a != b:
            disagreements += 1
        assert not (a and not b), "a narrower window fired where a wider did not"
    assert disagreements > 0, "the two windows never differed - test is vacuous"


def test_gate_arm_gives_the_arm_its_own_strategy_id():
    """``run_portfolio`` keys results on ``strategy_id`` (engine.py:277).

    Without ``_id=None`` the gated arm inherits the bare arm's cached id and one
    arm silently reports the other's trades.
    """
    from futures_agents.strategies.library import CONDITIONS
    base = Strategy(name="probe", symbol="MGC", group="CUSTOM", primary_tf=TF,
                    conditions=(CONDITIONS["ema_stack"],),
                    exit=ExitModel(), filters=StrategyFilters(rth_only=True))
    bare_id = base.strategy_id            # force the cache to populate
    armed = algo1.gate_arm(base, G.after_event())
    assert armed.strategy_id != bare_id
    assert len(armed.conditions) == len(base.conditions) + 1
    # Deterministic: the same arm built twice has the same id.
    assert algo1.gate_arm(base, G.after_event()).strategy_id == armed.strategy_id


def test_gate_arm_refuses_a_duplicate_gate_and_a_non_filter():
    from futures_agents.strategies.library import CONDITIONS
    base = Strategy(name="probe", symbol="MGC", group="CUSTOM", primary_tf=TF,
                    conditions=(CONDITIONS["ema_stack"], G.after_event()),
                    exit=ExitModel(), filters=StrategyFilters())
    with pytest.raises(EventClockError):
        algo1.gate_arm(base, G.after_event())
    with pytest.raises(EventClockError):
        algo1.gate_arm(base, CONDITIONS["ema_stack"])


def test_a_runtime_error_inside_a_condition_is_not_swallowed():
    """The premise behind ``EventClockError``.

    ``Condition.evaluate`` catches TypeError/ValueError/ZeroDivisionError/
    KeyError/IndexError and returns ``no()`` (``base.py:131-133``). A
    ``RuntimeError`` subclass is outside that tuple, so a misconfigured clock
    aborts the sweep instead of reporting zero trades. If this test ever fails,
    every ``EventClockError`` in this package has quietly become a silent zero.
    """
    def boom(snap, tf):
        raise EventClockError("configured wrong")

    bad = Condition(name="boom", group="news", fn=boom,
                    kind=ConditionKind.FILTER)
    frame = _frame("MGC", n=200)
    with pytest.raises(EventClockError):
        bad.evaluate(frame.snapshot(10), TF)


# ==========================================================================
# Window semantics
# ==========================================================================

def test_avoid_window_is_asymmetric_in_the_documented_direction():
    """``[-before, +after]``, not ``[-after, +before]``.

    ``features.py:979-986`` calls this the trap: written the wrong way round the
    filter initiates straight into the print and stands aside afterwards. Probed
    on the 2026-09-16 FOMC statement at 14:00 ET, a date in
    ``_FOMC_DECISION_DAYS``.
    """
    gate = G.avoid_event(10, 15)
    clock = EventClock("MNQ")
    print_ts = datetime(2026, 9, 16, 14, 0, tzinfo=ET)
    assert clock.read(print_ts).since_prev == 0.0

    def blocked(minutes):
        r = clock.read(print_ts + timedelta(minutes=minutes))
        return not (r.since_prev > 15 and r.to_next > 10)

    assert blocked(-11) is False        # 11m before: outside the 10m pre-window
    assert blocked(-10) is True         # 10m before: inclusive bound
    assert blocked(0) is True
    assert blocked(15) is True          # 15m after: inclusive bound
    # 16m after the statement the 14:30 press conference is 14m ahead, so the
    # bar is blocked by the NEXT print, not by the previous one. That is the
    # overlap case, and it is why cluster_minutes exists.
    r = clock.read(print_ts + timedelta(minutes=16))
    assert r.since_prev == 16.0 and r.to_next == 14.0


def test_clustering_stops_the_press_conference_truncating_the_statements_drift():
    """The FOMC pair is 30 minutes apart, on every meeting day."""
    plain = EventClock("MNQ", cluster_minutes=0.0)
    clustered = EventClock("MNQ", cluster_minutes=60.0)
    ts = datetime(2026, 9, 16, 15, 0, tzinfo=ET)     # 60m after 14:00, 30m after 14:30
    assert plain.read(ts).since_prev == 30.0         # measured from the presser
    assert clustered.read(ts).since_episode == 60.0  # measured from the statement
    assert clustered.read(ts).episode_name == "FOMC Statement"


def test_after_window_lower_bound_is_strict_and_upper_bound_inclusive():
    """Copied from library.py:1356-1359, whose comment explains why."""
    clock = EventClock("MCL")
    eia = datetime(2026, 9, 16, 10, 30, tzinfo=ET)   # a Wednesday EIA print

    def admits(minutes):
        s = clock.read(eia + timedelta(minutes=minutes)).since_prev
        return 15.0 < s <= 60.0

    assert admits(15) is False
    assert admits(16) is True
    assert admits(60) is True
    assert admits(61) is False


# ==========================================================================
# The contract's own session, which is the whole point of ALGO-1
# ==========================================================================

def test_each_contract_gets_its_own_session_not_the_equity_one():
    for sym, (o, c) in {"MGC": ("08:20", "13:30"), "MCL": ("09:00", "14:30"),
                        "MNQ": ("09:30", "16:00")}.items():
        row = census(sym, algo1.load_series(sym, TF).bars)
        assert (row.rth_open, row.rth_close) == (o, c), sym


def test_the_three_contracts_see_disjoint_in_session_event_sets():
    """R2-D5's structural finding, as an assertion.

    Four of the six HIGH rules print at 08:30 - before the 09:30 equity open and
    ten minutes after gold's 08:20 pit open. FOMC prints at 14:00/14:30, inside
    the equity session and after gold's 13:30 close. EIA prints at 10:30, inside
    crude's 09:00-14:30. So the event dimension MNQ can see and the one MGC can
    see do not overlap at all, and a result on one says nothing about the other.
    """
    seen = {s: set(census(s, algo1.load_series(s, TF).bars).by_rule_in_rth)
            for s in ("MNQ", "MGC", "MCL")}
    assert seen["MNQ"] == {"FOMC Statement", "FOMC Press Conference"}
    assert "US CPI" in seen["MGC"] and "FOMC Statement" not in seen["MGC"]
    assert "EIA Crude Oil Inventories" in seen["MCL"]
    assert not (seen["MNQ"] & seen["MGC"])


def test_medium_impact_events_are_invisible_to_the_library_and_visible_here():
    """features.py:972-973 filters to HIGH before computing proximity."""
    hi = census("MGC", algo1.load_series("MGC", TF).bars, min_impact=Impact.HIGH)
    med = census("MGC", algo1.load_series("MGC", TF).bars,
                 min_impact=Impact.MEDIUM)
    assert med.events_in_rth > hi.events_in_rth
    assert "US Initial Jobless Claims" in med.by_rule_in_rth
    assert "US Initial Jobless Claims" not in hi.by_rule_in_rth


# ==========================================================================
# Structural zeros - known, not discovered
# ==========================================================================

@pytest.mark.parametrize("symbol", ["MGC", "MCL"])
def test_the_two_stores_are_the_same_series_on_the_overlap(symbol):
    """BRIEF.md's data-policy ruling, condition 2, for MY symbols and timeframe.

    The ruling permits measuring on ``data/archive`` where the two stores are
    verified to agree for the symbol *and* timeframe in use. The parent verified
    60m for all four contracts; this re-verifies the two ALGO-1 runs on, because
    "someone checked" is not the same artefact as a test that fails if it stops
    being true. Timestamps are compared after normalising to UTC - the trap the
    ruling records is that ``csv/raw`` stamps are ``+00:00`` and
    ``data/archive`` stamps are ``-04:00``, so a naive string match compares bars
    four hours apart.
    """
    csv_bars = {b.ts.astimezone(UTC): b for b in algo1.load_series(symbol, TF).bars}
    arc_bars = {b.ts.astimezone(UTC): b
                for b in algo1.load_series(symbol, TF, store="archive").bars}
    common = sorted(set(csv_bars) & set(arc_bars))
    assert len(common) > 4900, f"{symbol}: only {len(common)} overlapping bars"
    worst = max(abs(csv_bars[t].close - arc_bars[t].close) for t in common)
    assert worst == 0.0, f"{symbol}: closes differ by up to {worst}"
    # And the archive must genuinely extend the span BEFORE csv/raw starts,
    # which is the only reason to prefer it.
    assert min(arc_bars) < min(csv_bars)
    assert len(arc_bars) - len(common) > 5000


def test_the_archive_store_doubles_the_in_session_event_count():
    """The reason ALGO-1 reports both stores rather than picking one.

    Not a performance number: a count of calendar prints against a bar clock.
    """
    for symbol in ("MGC", "MCL"):
        small = census(symbol, algo1.load_series(symbol, TF).bars)
        big = census(symbol, algo1.load_series(symbol, TF, store="archive").bars)
        assert big.event_days_in_rth > 1.8 * small.event_days_in_rth, symbol


def test_the_after_gate_can_never_fire_on_a_daily_bar():
    """A daily bar is stamped at midnight ET, so ``since`` is never in (15, 60].

    Consequence: ``post_news_window`` is identically false on every daily series
    in this repository, including MGC_1d's ten years. R2-D5 counts 358 in-session
    HIGH event days there; none of them is reachable by this gate. A gate that
    cannot fire is a structural zero and must be known before it is run, not
    reported afterwards as "the idea does not work".
    """
    gate = G.after_event()
    series = algo1.load_series("MGC", 1440)
    frame = build_symbol_frame(BarSeries("MGC", 1440, list(series.bars)[-500:]),
                               [1440])
    fired = sum(1 for i in range(len(frame.base.bars))
                if gate.evaluate(frame.snapshot(i), 1440).triggered)
    assert fired == 0


def test_an_hourly_grid_admits_at_most_one_bar_per_print():
    """The 60m ceiling, stated as arithmetic rather than discovered as a null.

    Every HIGH rule prints at :00 or :30 and hourly bars open at :00, so the
    (15, 60] window contains exactly one bar open per print - and when two prints
    are within 60 minutes of each other they share it. So the admissible-bar
    count can never exceed the number of qualifying prints in the span, which
    bounds realised trades before a single one is taken.
    """
    for symbol in ("MGC", "MCL"):
        frame = _frame(symbol)
        gate = G.after_event()
        bars = frame.base.bars
        fired = [i for i in range(len(bars))
                 if gate.evaluate(frame.snapshot(i), TF).triggered]
        prints = EventClock(symbol).events(
            bars[0].ts, bars[-1].ts + timedelta(minutes=TF))
        assert len(fired) <= len(prints), symbol
        # and at most one admitted bar per calendar day per print
        assert len({bars[i].ts for i in fired}) == len(fired)
