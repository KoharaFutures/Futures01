"""BT6 — the daily VWAP collapse (R6-D1), pinned so it cannot silently return.

`vwap_bands` resets its accumulation at every anchor boundary and emits a band
on the first bar of the new group, with no warm-up guard
(`futures_agents/indicators/volume.py:82-103`). On that bar the group holds one
observation, so the volume-weighted variance is ``tp**2 - tp**2`` and the band
has no width. That is `D45`.

On a **1440m** series every bar is the first bar of its own CME trading day, so
`D45` holds on 100% of bars rather than on 6-34% of them, and the `vwap`
condition group stops measuring volume-weighted value:

* `above_vwap`'s test ``close > vwap_u1`` becomes ``close > (H+L+C)/3``, i.e.
  ``2C > H+L``, i.e. ``sign(CLV)`` - the same arithmetic as
  `candle_close_strength` in the `candlestick` group;
* `vwap_band_extension` becomes the **negation** of that, because it tests
  ``close >= vwap_u2`` before ``close <= vwap_l2`` and on a zero-width band
  both hold;
* `vwap_band1_bounce` needs ``vwap_l1 < close < vwap``, which is empty when
  ``vwap_l1 == vwap``, so it is `VOID` in `BRIEF.md`'s sense - 0 of N bars,
  structurally, not rarely.

`vwap` is the **required** group of the VWAP template
(`futures_agents/strategies/combinator.py:189-200`), so this sits inside a
template's required slot. Measured blast radius, symbol by symbol, is in
`workspace/roundtable/backtest/BT6/bursts/01_r6-d1-daily-vwap-collapse.md`; this
file holds only what is provable without a tape.

**Two halves, deliberately.**

* **Half 1 - what is true today.** These pin the current arithmetic. Every
  published daily `vwap` row rests on it, so the moment one of these fails a
  published number has moved and somebody needs to know which.
* **Half 2 - what a warm-up guard must satisfy.** Marked
  ``xfail(strict=False)``. A guard on `vwap_bands` changes every frame at every
  timeframe and is a board decision (`BT6-REQ-1`), so these describe the
  intended behaviour and turn into ``XPASS`` the day it lands instead of
  breaking the build. A regression test for an unfixed defect has to be able to
  say "still unfixed" without failing.

Nothing here loads `csv/raw`. The collapse is exact arithmetic on one bar, so it
is provable on a handful of hand-written bars and the whole file runs in well
under a second. The per-symbol counts (2511/2511 MGC and 1859/1859 MES daily
bars sub-tick; 0 fires of `vwap_band1_bounce`; 2,126 generated daily strategies
that take zero trades) are measurements and live in the burst note.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Sequence, Tuple

import pytest

from futures_agents.config import get_contract
from futures_agents.data.bars import Bar, BarSeries
from futures_agents.features import SymbolFrame
from futures_agents.indicators.volume import vwap_bands
from futures_agents.schema import Direction
from futures_agents.scout import FRAMES
from futures_agents.strategies.combinator import TEMPLATES
from futures_agents.strategies.library import CONDITIONS
from futures_agents.timeutil import ET, trading_day

# Daily bars are stamped 00:00 ET in `csv/raw` (`MGC_1d.csv` carries
# `...T04:00:00+00:00`), and `trading_day` puts 00:00 ET inside the session that
# opened at 18:00 the previous evening. One bar per calendar day therefore lands
# in one distinct trading day, which is the whole mechanism.
DAY0 = datetime(2026, 3, 17, 0, 0, tzinfo=ET)

#: Hand-written daily OHLC with a deliberate mix of shapes: strong-up close,
#: strong-down close, mid close, an outside bar, and a doji. Prices are on
#: MGC's 0.10 grid.
DAILY_OHLC: Tuple[Tuple[float, float, float, float], ...] = (
    (2600.0, 2620.0, 2595.0, 2618.0),   # closes near the high
    (2618.0, 2625.0, 2590.0, 2593.0),   # closes near the low
    (2593.0, 2610.0, 2588.0, 2599.0),   # closes mid
    (2599.0, 2640.0, 2570.0, 2635.0),   # outside bar, closes high
    (2635.0, 2638.0, 2600.0, 2601.0),   # closes near the low
    (2601.0, 2612.0, 2597.0, 2604.5),   # closes mid
    (2604.5, 2630.0, 2602.0, 2629.0),   # closes near the high
    (2629.0, 2631.0, 2606.0, 2607.0),   # closes near the low
)


def daily_bars(rows: Sequence[Tuple[float, float, float, float]] = DAILY_OHLC,
               *, start: datetime = DAY0, volume: float = 1675.0) -> List[Bar]:
    """One 1440m bar per calendar day, so each lands in its own trading day."""
    return [Bar(ts=start + timedelta(days=i), open=o, high=h, low=l, close=c,
                volume=volume, minutes=1440)
            for i, (o, h, l, c) in enumerate(rows)]


def daily_frame(rows: Sequence[Tuple[float, float, float, float]] = DAILY_OHLC,
                *, symbol: str = "MGC") -> SymbolFrame:
    """A frame on the published daily timeframes, `FRAMES[1440] = [1440, 7200]`."""
    series = BarSeries(symbol, 1440, daily_bars(rows))
    return SymbolFrame(series, FRAMES[1440])


def hourly_bars(n_days: int = 6, per_day: int = 20,
                *, start: datetime = DAY0.replace(hour=18)) -> List[Bar]:
    """`n_days` CME sessions of 60m bars, so a session has bars 1..19 after its
    first. The control for every daily assertion below: the same code on a
    multi-bar anchor group must NOT collapse."""
    out: List[Bar] = []
    price = 2600.0
    ts = start
    for d in range(n_days):
        for k in range(per_day):
            o = price
            c = o + (3.7 if (d + k) % 3 else -2.9)
            h, l = max(o, c) + 1.4, min(o, c) - 1.1
            out.append(Bar(ts=ts, open=o, high=h, low=l, close=c,
                           volume=900.0 + 13 * k, minutes=60))
            price = c
            ts += timedelta(hours=1)
        ts += timedelta(hours=4)            # skip to the next Globex open
    return out


def half_widths(bars: Sequence[Bar]) -> List[float]:
    vb = vwap_bands(bars, "session", (1.0, 2.0))
    return [vb["upper_1"][i] - vb["vwap"][i] for i in range(len(bars))]


def first_of_anchor(bars: Sequence[Bar]) -> List[bool]:
    """True where `vwap_bands`' own anchor key changes - computed the way the
    indicator computes it (`volume.py:34-35`), not off a clock."""
    out, cur = [], None
    for b in bars:
        key = trading_day(b.ts)
        out.append(key != cur)
        cur = key
    return out


# ==========================================================================
# Half 1 - the mechanism, at one bar
# ==========================================================================

def test_band_has_no_usable_width_on_the_first_bar_of_an_anchor_group():
    """One observation cannot have a spread. This is `D45` in a single bar."""
    bars = daily_bars()
    hw = half_widths(bars)
    tick = get_contract("MGC").tick_size
    assert all(w is not None for w in hw), "no band is withheld: there is no warm-up guard"
    assert all(0.0 <= w < tick for w in hw), (
        f"expected every band-1 half-width under one tick ({tick}); got "
        f"max {max(hw):.6g}. If a warm-up guard has landed, Half 2 below is "
        f"the test that should now be passing.")


def test_the_band_collapse_is_not_an_artefact_of_one_tick_size():
    """The collapse is scale-free: it holds at MCL's 0.01 and MNQ's 0.25 alike."""
    hw = half_widths(daily_bars())
    for sym in ("MGC", "MES", "MNQ", "MCL"):
        tick = get_contract(sym).tick_size
        assert max(hw) < tick, f"{sym}: {max(hw):.6g} >= tick {tick}"


def test_zero_width_is_numerical_not_exact_so_no_test_may_assert_equality():
    """`var = max(0, pv2/vol - mean**2)` cancels two numbers near 7e6 here, so
    its absolute error is ~1e-9 and `sd` lands near 1e-5 - *not* zero.

    Measured on real data: the half-width is exactly `0.0` on 2300 of 2511 MGC
    and 1776 of 1859 MES daily bars, which means an assertion written as
    `sd == 0.0` would fail on roughly one daily bar in twelve. Pinned here with
    a hand-picked bar so the next author does not write that assertion.
    """
    b = Bar(ts=DAY0, open=2645.3, high=2650.4, low=2640.1, close=2645.3,
            volume=1675.0, minutes=1440)
    hw = half_widths([b])[0]
    assert hw > 0.0, ("this bar is the counter-example to 'sigma is exactly "
                      "zero'; if it has become 0.0 the arithmetic changed")
    assert hw < get_contract("MGC").tick_size


def test_every_bar_of_a_daily_series_is_the_first_bar_of_its_anchor_group():
    """The reason the rate is 100% at 1440m and 6-34% elsewhere."""
    bars = daily_bars()
    assert first_of_anchor(bars) == [True] * len(bars)
    assert len({trading_day(b.ts) for b in bars}) == len(bars)


def test_an_hourly_session_is_the_control_and_does_not_collapse():
    """Same function, multi-bar anchor groups: only bar 0 collapses.

    Without this the daily assertions would also pass under a change that
    zeroed every band at every timeframe, which is the opposite defect.
    """
    bars = hourly_bars()
    hw = half_widths(bars)
    tick = get_contract("MGC").tick_size
    firsts = first_of_anchor(bars)
    assert all(w < tick for w, f in zip(hw, firsts) if f), \
        "bar 0 of each session must still collapse"
    later = [w for w, f in zip(hw, firsts) if not f]
    assert sum(1 for w in later if w >= tick) > 0.5 * len(later), \
        "most non-first bars must have a band wider than a tick"


def test_appending_a_later_bar_never_changes_an_earlier_band():
    """No look-ahead. Band `i` must be a function of bars `<= i` only."""
    bars = daily_bars()
    full = half_widths(bars)
    for k in range(1, len(bars) + 1):
        prefix = half_widths(bars[:k])
        assert prefix == full[:k], f"band values changed when bar {k} was appended"


# ==========================================================================
# Half 1 - what the conditions become
# ==========================================================================

def _fire(frame: SymbolFrame, name: str, i: int):
    return CONDITIONS[name].fn(frame.snapshot(i), 1440)


def test_vwap_band1_bounce_is_VOID_at_1440m():
    """`vwap_l1 < close < vwap` with `vwap_l1 == vwap` is the empty set.

    `VOID`, not `DEGRADED`: it cannot fire, so a null from a strategy carrying
    it is "the detector never fired" and not "we measured absence".
    """
    frame = daily_frame()
    fired = [i for i in range(len(frame.base))
             if _fire(frame, "vwap_band1_bounce", i).triggered]
    assert fired == [], f"vwap_band1_bounce fired at daily on bars {fired}"


def test_above_vwap_reduces_to_the_sign_of_close_location():
    """`close > vwap_u1` with `vwap_u1 == vwap == (H+L+C)/3` is `2C > H+L`.

    The only shape that declines is a tie: `2C == H+L` to the tick, so the close
    sits exactly on its own VWAP. Two of the eight fixture bars are ties, both
    of them "closes mid" shapes. That tie is the *whole* of the condition's
    selectivity at 1440m, which is why it fires on 99.9% of real daily bars that
    have any range at all.
    """
    frame = daily_frame()
    fired = declined = 0
    for i, b in enumerate(frame.base.bars):
        res = _fire(frame, "above_vwap", i)
        clv_sign = (2.0 * b.close) - b.high - b.low
        if clv_sign == 0.0:
            declined += 1
            assert not res.triggered, f"bar {i}: 2C == H+L but the condition fired"
            continue
        fired += 1
        want = Direction.LONG if clv_sign > 0 else Direction.SHORT
        assert res.triggered, f"bar {i}: 2C-H-L = {clv_sign:+.4f} but no signal"
        assert res.direction is want, (
            f"bar {i}: above_vwap said {res.direction.name} but 2C-H-L = "
            f"{clv_sign:+.4f}")
    ties = sum(1 for o, h, l, c in DAILY_OHLC if 2.0 * c == h + l)
    assert ties >= 1, "the fixture must exercise the tie path"
    assert (declined, fired) == (ties, len(DAILY_OHLC) - ties)


def test_above_vwap_and_candle_close_strength_are_one_predicate_at_1440m():
    """Two condition *groups* (`vwap`, `candlestick`), one piece of evidence.

    `candle_close_strength` gates on `|CLV| >= 0.6` so it fires less often, but
    on every co-firing the direction is identical - measured 1092/1092 on MGC
    and 919/919 on MES daily bars. A confluence holding both counts one
    observation twice, which is the failure `GLOBAL_EXCLUSIVE` exists to
    prevent and which that list does not cover.
    """
    frame = daily_frame()
    co = 0
    for i in range(len(frame.base)):
        a = _fire(frame, "above_vwap", i)
        c = _fire(frame, "candle_close_strength", i)
        if a.triggered and c.triggered:
            co += 1
            assert a.direction is c.direction, f"bar {i}: {a.direction} vs {c.direction}"
    assert co >= 3, "the fixture must co-fire often enough for this to mean something"


def test_vwap_band_extension_is_the_exact_negation_of_above_vwap_at_1440m():
    """`close >= vwap_u2` is tested first, so on a zero-width band a strong
    close is read as *stretched* and returns SHORT. Measured: 0 of 2319 MGC and
    0 of 1854 MES daily co-firings agree on direction."""
    frame = daily_frame()
    co = 0
    for i in range(len(frame.base)):
        a = _fire(frame, "above_vwap", i)
        e = _fire(frame, "vwap_band_extension", i)
        if a.triggered and e.triggered:
            co += 1
            assert a.direction is not e.direction, (
                f"bar {i}: the two vwap signals agreed, which they cannot do on "
                f"a zero-width band")
    assert co >= 3


def test_a_bar_with_no_range_can_still_be_given_a_direction():
    """The sharpest consequence, and it is pure float noise.

    `typical = (high+low+close)/3` does not round-trip to `close` in binary
    floating point even when `high == low == close`, so a bar with **no range at
    all** can land off its own VWAP by ~2e-13 and `above_vwap` returns a
    direction. `csv/raw/MGC_1d.csv` carries 281 such bars (11.2%) and 91 of them
    emit a signal - 41 LONG, 50 SHORT - on the last bit of a float.

    The two prices here are taken from that file (2019-06-20 and 2019-08-09),
    where volume is 0 and `vwap_bands` substitutes 1.0.
    """
    flat_long, flat_short = 1392.900024, 1496.599976
    for price, want in ((flat_long, Direction.LONG), (flat_short, Direction.SHORT)):
        rows = DAILY_OHLC[:2] + ((price, price, price, price),)
        frame = daily_frame(rows)
        i = len(rows) - 1
        b = frame.base.bars[i]
        assert b.high == b.low == b.close, "the fixture bar must have no range"
        res = _fire(frame, "above_vwap", i)
        assert res.triggered, (
            "this rangeless bar no longer emits a signal - if a warm-up guard "
            "or a dead-band has landed, that is the fix, not a regression")
        assert res.direction is want
        assert abs(b.close - b.typical) < 1e-9, "the gap is float noise, not price"


# ==========================================================================
# Half 1 - the reach: `vwap` is a required group, and one signal kills a strategy
# ==========================================================================

def test_vwap_is_the_required_group_of_exactly_one_template():
    """Why a degenerate `vwap` group is not a cosmetic problem."""
    requires = [t.group for t in TEMPLATES if "vwap" in t.required_groups]
    offers = [t.group for t in TEMPLATES if "vwap" in t.optional_groups]
    assert requires == ["VWAP"]
    assert len(offers) == 9, f"expected 9 templates offering `vwap`, got {offers}"
    never = [t.group for t in TEMPLATES
             if "vwap" not in t.required_groups and "vwap" not in t.optional_groups]
    assert sorted(never) == ["BREAKOUT", "MOMENTUM", "SUPPLY_DEMAND"]


def test_no_template_can_draw_two_vwap_conditions_as_signals():
    """The conservative half: `above_vwap` and `vwap_band_extension` are exact
    opposites at 1440m, and `Strategy.evaluate` rejects disagreeing signals
    (`base.py:677-684`) - so a strategy holding both would be zero-trade. It
    cannot be generated: the combinator draws at most one condition per group
    (`combinator.py:538-541`) and no template lists `vwap` in both its required
    and optional groups. **No published null can be that artefact.**"""
    for t in TEMPLATES:
        assert not ("vwap" in t.required_groups and "vwap" in t.optional_groups), \
            f"{t.group} could draw two vwap conditions"


def test_the_engine_takes_zero_trades_from_a_daily_vwap_band1_bounce_strategy():
    """End to end, because "the condition never fires" and "the strategy never
    trades" are different claims and only the second one reaches a report.

    Measured on the real populations the published chronology used: 731 / 730 /
    665 generated MGC / MES / MNQ daily strategies carry `vwap_band1_bounce`,
    and all 2,126 take **zero** trades through `run_portfolio`.
    """
    from futures_agents.backtest.engine import run_portfolio
    from futures_agents.strategies.base import (Condition, ConditionKind,
                                                ExitModel, StopKind, Strategy)

    frame = daily_frame(DAILY_OHLC * 6)
    exit_model = ExitModel(stop_kind=StopKind.ATR, stop_mult=1.0,
                           targets_r=(2.0,), scale_out=(1.0,))

    def strat(name: str) -> Strategy:
        # `_id=None` explicitly, per `D48`: `dataclasses.replace` and a shared
        # default both carry a memoised id forward, and two arms colliding into
        # one `BacktestResult` measures exactly zero difference.
        cond = CONDITIONS[name]
        return Strategy(
            name=f"daily-{name}", group="VWAP", symbol="MGC", primary_tf=1440,
            conditions=(Condition(name=cond.name, group=cond.group,
                                  fn=cond.fn, kind=ConditionKind.SIGNAL),),
            exit=exit_model, _id=None)

    void = strat("vwap_band1_bounce")
    live = strat("above_vwap")
    res = run_portfolio(frame, [void, live])
    assert res[void.strategy_id].trades == [], (
        "vwap_band1_bounce produced a trade at 1440m, which the arithmetic "
        "forbids")
    assert res[live.strategy_id].trades, (
        "the control took no trades either, so the zero above says nothing "
        "about vwap_band1_bounce")


# ==========================================================================
# Half 2 - what a warm-up guard must satisfy. `xfail(strict=False)`.
# ==========================================================================

@pytest.mark.xfail(strict=False, reason="BT6-REQ-1: no warm-up guard exists yet")
def test_a_guarded_vwap_bands_withholds_the_band_on_a_one_observation_group():
    """The fix: a band computed from one observation is not a band. Emitting
    `None` makes every `vwap` condition abstain through its own
    `s.has(...)` check rather than fire on noise."""
    vb = vwap_bands(daily_bars(), "session", (1.0, 2.0))
    assert all(x is None for x in vb["upper_1"]), \
        "a guarded implementation withholds band-1 on every daily bar"
    assert all(x is None for x in vb["lower_1"])


@pytest.mark.xfail(strict=False, reason="BT6-REQ-1: no warm-up guard exists yet")
def test_a_guarded_vwap_line_still_exists_when_its_bands_do_not():
    """The guard must be on the *bands*, not on the line. A one-bar VWAP is a
    well-defined number (the typical price); its standard deviation is not."""
    vb = vwap_bands(daily_bars(), "session", (1.0, 2.0))
    assert all(x is not None for x in vb["vwap"])
    assert all(x is None for x in vb["upper_1"])


@pytest.mark.xfail(strict=False, reason="BT6-REQ-1: no warm-up guard exists yet")
def test_a_guarded_above_vwap_abstains_at_1440m_rather_than_firing_on_noise():
    """With the band withheld, `above_vwap`'s `s.has("vwap_u1", ...)` check
    returns `no()` and a daily VWAP strategy takes no trades instead of taking
    them on bar shape. That is a *smaller* published corpus, not a different
    one - which is why it is a board decision."""
    frame = daily_frame()
    fired = [i for i in range(len(frame.base))
             if _fire(frame, "above_vwap", i).triggered]
    assert fired == [], "a guarded above_vwap fires on no daily bar"
