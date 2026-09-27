"""Tests for the key-level breach scanner.

The scanner's value is its classifier, so that is what these pin: a wick
through a level is not a break, a break that closes back inside is a FAILED
breach and points the other way, and a stop inside the 0.5-ATR floor is
reported as untradeable rather than quietly widened.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from futures_agents.data.bars import Bar
from futures_agents.scanners.breach import (KeyLevel, collect_levels,
                                            find_breaches, scan_symbol)
from futures_agents.schema import Direction
from futures_agents.timeutil import ET

START = datetime(2026, 9, 1, 9, 0, tzinfo=ET)


def mk(n, *, base=100.0, drift=0.0, rng=1.0, minutes=60):
    """A flat, well-formed series with a known range, for planting events in."""
    out = []
    for i in range(n):
        c = base + drift * i
        out.append(Bar(ts=START + timedelta(minutes=minutes * i), open=c,
                       high=c + rng, low=c - rng, close=c, minutes=minutes,
                       volume=100.0))
    return out


def test_a_wick_through_a_level_is_not_a_breach():
    bars = mk(40)
    # One bar spikes well above 101 but closes back at 100.
    i = 30
    b = bars[i]
    bars[i] = Bar(ts=b.ts, open=100.0, high=110.0, low=99.0, close=100.0,
                  minutes=60, volume=100.0)
    lvl = KeyLevel("test", 101.0, "RESISTANCE", "session", 1.0)
    evs = find_breaches(bars, [lvl], symbol="MES", timeframe=60)
    assert evs == [], "a wick through a level must not register as a break"


def test_a_close_beyond_the_level_is_a_breach():
    bars = mk(40)
    for i in range(30, 40):          # step decisively above 101
        c = 105.0
        bars[i] = Bar(ts=bars[i].ts, open=c, high=c + 1, low=c - 1, close=c,
                      minutes=60, volume=100.0)
    lvl = KeyLevel("test", 101.0, "RESISTANCE", "session", 1.0)
    evs = find_breaches(bars, [lvl], symbol="MES", timeframe=60)
    assert evs, "a decisive close beyond the level must register"
    assert evs[0].direction is Direction.LONG


def test_a_break_that_closes_back_inside_is_FAILED_and_points_the_other_way():
    bars = mk(40)
    bars[30] = Bar(ts=bars[30].ts, open=100, high=106, low=99, close=105,
                   minutes=60, volume=100.0)          # breaks up through 101
    for i in range(31, 40):                            # then closes back under
        bars[i] = Bar(ts=bars[i].ts, open=97, high=98, low=96, close=97,
                      minutes=60, volume=100.0)
    lvl = KeyLevel("test", 101.0, "RESISTANCE", "session", 1.0)
    evs = find_breaches(bars, [lvl], symbol="MES", timeframe=60)
    assert evs and evs[0].outcome == "FAILED"
    # The break was upward; the fade is therefore a short.
    _, opps = scan_symbol(bars, symbol="MES", timeframe=60,
                          playbooks=["FAILED_BREACH_FADE"])
    fades = [o for o in opps if o.playbook == "FAILED_BREACH_FADE"]
    if fades:
        assert all(o.direction is Direction.SHORT for o in fades)


def test_a_stop_inside_the_half_atr_floor_is_rejected_not_widened():
    """Measured rule 4: below 0.5 ATR a structural stop is noise."""
    from futures_agents.config import get_contract
    from futures_agents.scanners.breach import Opportunity, _finalise
    spec = get_contract("MES")
    # ATR 5.0 means the floor is 2.5 points. A 1.5-point stop is under it, and
    # is wide enough to survive tick-rounding so the earlier zero-risk guard
    # does not fire first.
    o = _finalise(Opportunity(
        playbook="X", symbol="MES", timeframe=60, direction=Direction.LONG,
        level=KeyLevel("l", 100.0, "SUPPORT", "session", 1.0),
        entry=100.5, stop=99.0, target=104.0, ts=START, atr=5.0,
        rationale=""), spec)
    assert o.tradeable is False
    assert "0.50 ATR floor" in o.reject_reason
    assert o.stop_atr == pytest.approx(0.3)
    # Reported, not silently widened: the stop is still where it was put.
    assert o.stop == 99.0


def test_a_zero_risk_stop_is_caught_before_the_atr_floor():
    """Tick-rounding can collapse a too-tight stop onto the entry."""
    from futures_agents.config import get_contract
    from futures_agents.scanners.breach import Opportunity, _finalise
    o = _finalise(Opportunity(
        playbook="X", symbol="MES", timeframe=60, direction=Direction.LONG,
        level=KeyLevel("l", 100.0, "SUPPORT", "session", 1.0),
        entry=100.5, stop=100.4, target=102.0, ts=START, atr=5.0,
        rationale=""), get_contract("MES"))
    assert o.tradeable is False
    assert o.reject_reason == "stop is at the entry"


def test_levels_are_computed_only_from_bars_at_or_before_as_of():
    """No look-ahead: a level cannot be built from a bar that has not printed."""
    bars = mk(80, drift=0.5)
    cutoff = bars[40].ts
    lv = collect_levels(bars, symbol="MES", as_of=cutoff)
    future_high = max(b.high for b in bars[41:])
    assert all(l.price <= future_high for l in lv)
    # The session-high level must not exceed anything visible at the cutoff.
    visible_high = max(b.high for b in bars[:41])
    for l in lv:
        if l.name in ("session_high", "prev_day_high", "overnight_high"):
            assert l.price <= visible_high + 1e-9


def test_duplicate_levels_within_a_tick_are_collapsed():
    bars = mk(60, drift=0.3)
    lv = collect_levels(bars, symbol="MES")
    prices = sorted(l.price for l in lv)
    spec_tick = 0.25
    for a, b in zip(prices, prices[1:]):
        assert (b - a) > spec_tick - 1e-9, "levels within a tick should be merged"


def test_scan_returns_opportunities_with_sane_reward_risk():
    bars = mk(120, drift=0.4)
    _, opps = scan_symbol(bars, symbol="MES", timeframe=60)
    for o in opps:
        assert o.reward_risk > 0
        if o.tradeable:
            assert o.stop_atr >= 0.5
