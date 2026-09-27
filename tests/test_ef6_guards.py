"""EF6 regression tests for the three silent-failure guards this programme needs.

1. **D48** — `dataclasses.replace` on a `Strategy` inherits the memoised `_id`,
   so two arms collide into one `BacktestResult` and their difference measures
   exactly zero. `BRIEF.md` records that every existing call site remembers to
   pass `_id=None` and that nothing in the test suite stops the next author
   forgetting. These tests are that guard.

2. **The 18:00 ET → 16:00 ET window predicate.** A control measured on a
   different bar set from the thing it controls is easier than the thing it
   controls. The predicate is shared, so it is tested.

3. **Deflation accounting.** `free_t = sqrt(2·ln n)` on *this* programme's `n`,
   with the span beside it. The failure mode is quoting 5.46 out of habit, so
   the test pins the arithmetic and pins the scalp/swing cells.
"""

from __future__ import annotations

import dataclasses
import math
import os
import sys
from datetime import datetime, timedelta

import pytest

EF6 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "workspace", "roundtable", "edge", "EF6", "code")
if EF6 not in sys.path:
    sys.path.insert(0, EF6)

import arms                       # noqa: E402
import deflation as D             # noqa: E402
import window as W                # noqa: E402

from futures_agents.strategies.base import Strategy  # noqa: E402
from futures_agents.strategies.combinator import generate_strategies  # noqa: E402
from futures_agents.timeutil import ET  # noqa: E402


# ---------------------------------------------------------------- D48
@pytest.fixture(scope="module")
def base_strategy() -> Strategy:
    gen = generate_strategies("MGC", [60], max_total=40)
    assert gen, "combinator produced nothing"
    s = gen[0]
    _ = s.strategy_id          # memoise, which is what makes D48 reachable
    return s


def test_d48_bare_replace_still_collides(base_strategy):
    """The defect is live. If this ever fails, base.py changed and the guard
    below can be reconsidered — until then, `respec` is mandatory."""
    bad = dataclasses.replace(
        base_strategy,
        filters=dataclasses.replace(base_strategy.filters, rth_only=False))
    assert bad.strategy_id == base_strategy.strategy_id, (
        "D48 appears fixed upstream; re-read base.py:585,611-623 before "
        "relaxing anything")
    assert bad.filters.rth_only is not base_strategy.filters.rth_only


def test_respec_produces_a_distinct_id(base_strategy):
    good = arms.refilter(base_strategy, rth_only=False)
    assert good.strategy_id != base_strategy.strategy_id
    assert good.filters.rth_only is False
    assert base_strategy.filters.rth_only is True


def test_respec_refuses_an_explicit_id(base_strategy):
    with pytest.raises(ValueError):
        arms.respec(base_strategy, _id="MGC-60m-deadbeef")


def test_assert_unique_catches_a_collision(base_strategy):
    bad = dataclasses.replace(
        base_strategy,
        filters=dataclasses.replace(base_strategy.filters, rth_only=False))
    with pytest.raises(AssertionError, match="D48"):
        arms.assert_unique([base_strategy], [bad], labels=["ctl", "trt"])


def test_assert_unique_passes_on_safe_arms(base_strategy):
    good = arms.refilter(base_strategy, rth_only=False)
    shape = arms.assert_unique([base_strategy], [good], labels=["ctl", "trt"])
    assert shape == {"ctl": 1, "trt": 1}


def test_two_arms_shape_and_uniqueness():
    gen = generate_strategies("MGC", [60], max_total=60)
    for s in gen:
        _ = s.strategy_id
    ctl, trt, shape = arms.two_arms(gen, rth_only=False)
    assert shape["control"] == shape["treatment"] == len(gen)
    assert len({s.strategy_id for s in ctl} & {s.strategy_id for s in trt}) == 0


def test_arm_report_detects_a_shared_result_object(base_strategy):
    """The post-hoc D48 signature: two arms pointing at one result object."""
    good = arms.refilter(base_strategy, rth_only=False)
    shared = object()
    results = {base_strategy.strategy_id: shared, good.strategy_id: shared}
    with pytest.raises(AssertionError, match="D48 after the fact"):
        arms.arm_report(results, [base_strategy], [good], labels=["a", "b"])


# ---------------------------------------------------------------- window rule
def _et(h, m=0, day=15):
    return datetime(2026, 9, day, h, m, tzinfo=ET)


@pytest.mark.parametrize("hh,mm,expected", [
    (18, 0, True), (18, 1, True), (23, 59, True), (0, 0, True),
    (9, 30, True), (15, 59, True),
    (16, 0, False), (16, 30, False), (17, 0, False), (17, 59, False),
])
def test_in_window_boundaries(hh, mm, expected):
    assert W.in_window(_et(hh, mm)) is expected


def test_window_is_exactly_the_complement_of_post_close():
    """The forbidden span is `timeutil.SESSIONS`' POST_CLOSE, 16:00→18:00."""
    from futures_agents.timeutil import classify_session
    for minute in range(0, 24 * 60, 5):
        ts = _et(minute // 60, minute % 60)
        assert W.in_window(ts) == (classify_session(ts) != "POST_CLOSE")


def test_bar_status_straddle_at_240m():
    """A 4-hour bar stamped 16:00 ET spans 16:00→20:00 and therefore contains
    the 18:00 reopen. The rule is not expressible on that grid."""
    assert W.bar_status(_et(16, 0), 240) == "STRADDLE"
    assert W.bar_status(_et(12, 0), 240) == "IN"
    assert W.bar_status(_et(20, 0), 240) == "IN"
    assert W.bar_status(_et(16, 0), 60) == "OUT"
    assert W.bar_status(_et(15, 0), 60) == "IN"


def test_expressible_base_timeframes_divide_the_22_hour_window():
    """1320 minutes is the window. 240 and 1440 do not divide it; 5/15/30/60/120 do."""
    for tf in (1, 5, 15, 30, 60, 120):
        assert 1320 % tf == 0, tf
    for tf in (240, 1440):
        assert 1320 % tf != 0, tf


def test_signal_mask_is_window_shifted_by_one():
    """Entries fill at the NEXT bar's open, so legality is a property of i+1."""
    class B:
        def __init__(self, ts):
            self.ts = ts
    bars = [B(_et(14, 0)), B(_et(15, 0)), B(_et(16, 0)), B(_et(18, 0))]
    wm = W.window_mask(bars, 60)
    sm = W.signal_mask(bars, 60)
    assert wm == [True, True, False, True]
    # bar 1 (15:00) would fill at 16:00 -> illegal; bar 2 fills at 18:00 -> legal
    assert sm == [True, False, True, False]


def test_cycle_id_groups_an_evening_bar_with_the_next_morning():
    assert W.cycle_id(_et(18, 30, day=14)) == "2026-09-15"
    assert W.cycle_id(_et(10, 0, day=15)) == "2026-09-15"
    assert W.cycle_id(_et(15, 59, day=15)) == "2026-09-15"
    # 16:00-18:00 is tradeable by nothing, so it is assigned forward
    assert W.cycle_id(_et(16, 30, day=15)) == "2026-09-16"


def test_max_hold_is_22_hours():
    assert W.MAX_HOLD_MINUTES == 1320


# ---------------------------------------------------------------- deflation
def test_free_t_matches_the_repo_toolkit():
    from workspace.studies import toolkit as T  # noqa: F401  (import path guard)
    for n in (1, 2, 10, 1000, 2_975_629):
        assert abs(D.free_t(n) - T.free_t(n)) < 1e-12


def test_prereg_floor_is_1_177():
    assert abs(D.PREREG_FLOOR - 1.1774100225) < 1e-8


def test_free_t_at_the_historical_population():
    assert abs(D.free_t(2_975_629) - 5.46) < 0.005


def test_t_equals_sharpe_times_sqrt_years_identity():
    """Pin the identity the module converts through."""
    for span, sr in ((57.90, 2.0), (718.88, 1.0), (5835.0, 0.75)):
        y = D.span_years(span)
        t = sr * math.sqrt(y)
        assert abs(D.implied_annual_sharpe(t, span) - sr) < 1e-9


def test_scalp_cell_requires_sharpe_about_three_for_one_prereg_hypothesis():
    r = D.threshold(1, 57.90, preregistered=True)
    assert r["threshold_t"] == pytest.approx(1.1774, abs=1e-3)
    assert r["required_annual_sharpe"] == pytest.approx(2.96, abs=0.02)


def test_scalp_top10_needs_sharpe_over_five():
    r = D.topn_threshold(57.90, 10, 10)
    assert r["free_t_floor_from_list_size"] == pytest.approx(2.146, abs=1e-3)
    assert r["required_annual_sharpe_actual"] == pytest.approx(5.39, abs=0.02)


def test_swing_top10_is_answerable_only_at_a_narrow_search():
    narrow = D.topn_threshold(718.88, 10, 10)
    wide = D.topn_threshold(718.88, 10, 40_000)
    assert narrow["required_annual_sharpe_actual"] == pytest.approx(1.53, abs=0.02)
    assert wide["required_annual_sharpe_actual"] == pytest.approx(3.28, abs=0.02)


def test_scalp_is_unanswerable_at_every_believable_sharpe():
    for sr in (0.75, 1.0, 1.5, 2.0, 2.5):
        assert D.max_n_answerable(57.90, sr) is None
    assert D.max_n_answerable(57.90, 3.0) == 2


def test_group_span_takes_the_minimum_member():
    assert D.group_span_days("MGC", [5, 60]) == pytest.approx(57.90)
    assert D.group_span_days("MGC", [60, 240]) == pytest.approx(718.83)


def test_mcl_daily_span_is_absent_rather_than_guessed():
    with pytest.raises(KeyError):
        D.group_span_days("MCL", [1440])


def test_for_cell_names_the_binding_timeframe():
    r = D.for_cell("MES", [15, 60, 240], 500)
    assert r["span_binding_tf"] == 15
    assert r["span_days"] == pytest.approx(57.90)
