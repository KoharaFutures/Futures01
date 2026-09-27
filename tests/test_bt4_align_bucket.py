"""BT4 ALGO-1 — `align_bucket` above 1440m, and the daily frame that confirms itself.

`R4-M3` found that :func:`align_bucket` takes its ``minutes >= 1440`` branch for
*every* coarser request, so ``align_bucket(ts, 7200) == align_bucket(ts, 1440)``
and ``scout.FRAMES[1440] = [1440, 7200]`` holds the daily series twice. `scout.py`
says what it meant — "7200 minutes is five sessions" — and the code has never
been checked against the comment.

These tests exist because the defect is **silent in both directions**. Today it
silently produces a duplicate series; when it is fixed, every consumer of a
coarse bucket silently changes, including the `regime_tf` a daily strategy reads.
Either way the suite should say so rather than a later agent discovering it by
hand a third time.

So the file is deliberately in two halves:

* **Half 1 — what is true today.** These pin the current arithmetic, and the
  reduction ALGO-1 rests on. They must keep passing until `align_bucket`
  changes; the moment one fails, a published number moved.
* **Half 2 — what a fix must satisfy.** Marked ``xfail(strict=False)`` and
  describing the *intended* behaviour: a 7200m bucket spans five sessions and the
  daily frame's two members are not the same series. They turn into ``XPASS`` the
  day the fix lands rather than breaking the suite — a regression test for an
  unfixed defect has to be able to say "still unfixed" without failing the build.

Nothing here loads `csv/raw`: the collapse is exact arithmetic on timestamps and
is provable on a few hundred synthetic bars, so the whole file runs in
milliseconds. The measured per-symbol counts live in
`workspace/roundtable/backtest/BT4/ALGOS.md`, not here.
"""
from __future__ import annotations

import collections
import math
from datetime import datetime, timedelta

import pytest

from futures_agents.data.bars import Bar, BarSeries, align_bucket, resample
from futures_agents.features import SymbolFrame
from futures_agents.scout import FRAMES
from futures_agents.strategies.library import CONDITIONS
from futures_agents.timeutil import ET, trading_day

# A Tuesday in March 2026, matching `conftest.SESSION_OPEN`'s choice of a date
# well clear of any DST transition.
TS = datetime(2026, 3, 17, 10, 30, tzinfo=ET)
# A stamp that no two of {5, 15, 30, 60, 240} bucket the same way, so a test can
# tell "reads minutes" from "happens to agree at :30".
TS_ODD = datetime(2026, 3, 17, 10, 37, tzinfo=ET)

#: Every `minutes` value above a day that `align_bucket` currently cannot tell
#: apart. 2880 = 2 days, 4320 = 3, 7200 = 5 (the "week" `FRAMES` asks for),
#: 10080 = 7, 43200 = 30, 525600 = 365.
COARSE = (1440, 2880, 4320, 7200, 10080, 43200, 525600)


def flat_bars(n: int = 40, *, start: datetime = TS, price: float = 2000.0) -> list:
    """`n` daily bars, one per calendar day, drifting up. Bucketing tests only.

    `structure_trend` is UNDEFINED on a monotone run because there are no fractal
    pivots, which is fine here and is exactly why the frame tests below need
    :func:`swing_bars` instead.
    """
    out = []
    for i in range(n):
        o = price + i
        out.append(Bar(ts=start + timedelta(days=i), open=o, high=o + 4.0,
                       low=o - 1.0, close=o + 3.0, volume=1000.0 + i, minutes=1440))
    return out


def swing_bars(n: int = 180, leg: int = 20, *, start: datetime = TS,
               price: float = 2000.0, amp: float = 12.0, period: int = 8,
               drift: float = 3.0) -> list:
    """Daily bars that actually resolve a structural trend, deterministically.

    A trend label needs fractal swing pivots, so the series carries a short
    zigzag (`period`) on top of a directional leg that flips sign every `leg`
    bars. `leg=20` gives long UPTREND and DOWNTREND stretches; `leg=10` flips
    fast enough that two labels 2-4 bars apart can be outright opposed, which is
    the only way to exercise `mtf_not_conflicted`'s veto path.

    No RNG: same bars on every machine, per the suite's convention.
    """
    out, base = [], price
    for i in range(n):
        d = drift if (i // leg) % 2 == 0 else -drift
        base += d
        v = base + amp * math.sin(2 * math.pi * i / period)
        o, c = v, v + d
        out.append(Bar(ts=start + timedelta(days=i), open=o, high=max(o, c) + 2.0,
                       low=min(o, c) - 2.0, close=c, volume=1000.0 + i, minutes=1440))
    return out


def daily_frame(n: int = 180, leg: int = 20) -> SymbolFrame:
    return SymbolFrame(BarSeries("MGC", 1440, swing_bars(n, leg)), FRAMES[1440])


def rebuild_confirm_pointer(series: BarSeries) -> list:
    """`_align[7200]`, rebuilt from the daily bars and the calendar alone.

    This is the step that makes ALGO-1's reduction non-circular: `resample`
    stamps the copy at `align_bucket(ts, 7200)` — the trading-day start, by the
    collapse — and `Bar.end_ts` adds 7200 minutes to it, so the pointer
    `_build_alignment` produces is a function of the daily timestamps and nothing
    else. No second series is read here.
    """
    ends = [align_bucket(b.ts, 7200) + timedelta(minutes=7200) for b in series.bars]
    ptr, k, j = [], -1, 0
    for b in series.bars:
        while j < len(ends) and ends[j] <= b.end_ts:
            k = j
            j += 1
        ptr.append(k)
    return ptr


# --------------------------------------------------------------------------
# Half 1 — the collapse as it stands today
# --------------------------------------------------------------------------
def test_every_bucket_above_a_day_collapses_onto_the_trading_day():
    """`minutes` is read once, as a threshold, and then discarded.

    `bars.py:145-149` branches on `minutes >= 1440` and returns the CME
    trading-day start without ever using the value again, so a two-day, weekly,
    monthly and annual bucket are one bucket.
    """
    buckets = {m: align_bucket(TS, m) for m in COARSE}
    assert len(set(buckets.values())) == 1, buckets
    assert buckets[7200] == buckets[1440]


def test_the_daily_bucket_is_18_00_the_previous_evening():
    """The value all coarse requests collapse onto, pinned exactly."""
    got = align_bucket(TS, 1440)
    assert got.hour == 18 and got.minute == 0
    assert got.date() == trading_day(TS) - timedelta(days=1)
    assert got == datetime(2026, 3, 16, 18, 0, tzinfo=ET)


def test_sub_daily_buckets_do_read_minutes():
    """The bug is confined to the coarse branch — the other two are fine.

    Without this the file would not distinguish "align_bucket ignores minutes"
    from "align_bucket ignores minutes above a day", and the first is false.
    """
    assert align_bucket(TS, 60) == datetime(2026, 3, 17, 10, 0, tzinfo=ET)
    assert align_bucket(TS, 240) == datetime(2026, 3, 17, 8, 0, tzinfo=ET)
    assert align_bucket(TS_ODD, 15) == datetime(2026, 3, 17, 10, 30, tzinfo=ET)
    assert align_bucket(TS_ODD, 5) == datetime(2026, 3, 17, 10, 35, tzinfo=ET)
    assert len({align_bucket(TS_ODD, m) for m in (5, 15, 30, 60, 240)}) == 4


def test_a_weekly_bucket_holds_exactly_one_daily_bar():
    """One bar per bucket is the collapse in its plainest form."""
    bars = flat_bars(40)
    per_bucket = collections.Counter(align_bucket(b.ts, 7200) for b in bars)
    assert set(per_bucket.values()) == {1}
    assert len(per_bucket) == len(bars)


def test_resampling_daily_to_7200_reproduces_the_daily_ohlcv_in_order():
    """The "weekly" series is the daily series, bar for bar, field for field."""
    series = BarSeries("MGC", 1440, flat_bars(40))
    weekly = resample(series, 7200, keep_partial=False)
    # One input is dropped: `count >= expected` fails on the last bucket because
    # `expected = 7200 // 1440 = 5` and every bucket holds 1.
    assert len(weekly) == len(series) - 1
    for a, b in zip(weekly.bars, series.bars):
        assert (a.open, a.high, a.low, a.close, a.volume) == \
               (b.open, b.high, b.low, b.close, b.volume)


def test_the_7200_copy_is_mislabelled_in_both_duration_and_timestamp():
    """The two rewrites that turn a duplicate series into a *lagged* duplicate.

    `minutes` is stamped 7200 on a one-session bar and `ts` is moved to the
    trading-day start, so `Bar.end_ts` lands five days past a bar that covers
    one. That is the whole mechanism by which the alignment pointer trails.
    """
    series = BarSeries("MGC", 1440, flat_bars(40))
    weekly = resample(series, 7200, keep_partial=False)
    assert weekly.bars[0].minutes == 7200
    assert weekly.bars[0].ts != series.bars[0].ts
    assert weekly.bars[0].ts == align_bucket(series.bars[0].ts, 1440)
    assert weekly.bars[0].end_ts - weekly.bars[0].ts == timedelta(minutes=7200)
    assert series.bars[0].end_ts - series.bars[0].ts == timedelta(minutes=1440)


def test_the_shipped_daily_frame_asks_for_a_timeframe_above_1440():
    """`FRAMES[1440]` is the only exposure, and every other row is clean.

    If a future frame map adds another coarse member this fails, which is the
    early warning: the defect's blast radius is exactly
    `{tf: [m for m in FRAMES[tf] if m > 1440]}`.
    """
    assert FRAMES[1440] == [1440, 7200]
    exposed = {tf: [m for m in tfs if m > 1440] for tf, tfs in FRAMES.items()}
    assert exposed == {5: [], 15: [], 30: [], 60: [], 240: [], 1440: [7200]}
    # Every frame's primary is its own lowest member, which is why only the
    # daily row is exposed rather than every row containing a 1440 member.
    assert all(tfs[0] == tf for tf, tfs in FRAMES.items())


def test_the_daily_frames_two_members_hold_identical_bars():
    """Inside a built `SymbolFrame`, not just in `resample`'s output."""
    frame = daily_frame()
    lo = frame.frames[1440].series.bars
    hi = frame.frames[7200].series.bars
    assert len(hi) == len(lo) - 1
    for a, b in zip(hi, lo):
        assert (a.open, a.high, a.low, a.close) == (b.open, b.high, b.low, b.close)


def test_the_confirming_pointer_trails_the_primary_by_a_few_bars():
    """`_build_alignment` advances on `end_ts`, and the copy's `end_ts` is +5 days.

    The primary pointer is the identity because `frames[1440] is base`; the
    confirming pointer is a handful of bars behind it. That lag is the only
    content the "higher timeframe" can carry. On the real daily files the
    distribution is 1-4 with a mode at 2 (`backtest/BT4/ALGOS.md`); on a
    calendar-dense synthetic series it concentrates at 4.
    """
    frame = daily_frame()
    assert frame._align[1440] == list(range(len(frame.base)))
    lags = collections.Counter(a - b for a, b in
                               zip(frame._align[1440], frame._align[7200]))
    assert set(lags) <= {1, 2, 3, 4, 5}
    assert max(lags, key=lags.get) >= 2


def test_the_confirming_pointer_needs_no_second_series_to_reconstruct():
    """ALGO-1's non-circularity check, in the suite.

    If the pointer is a function of the daily timestamps alone, then so is every
    value the confirming timeframe reports, and "the higher timeframe" is a
    derived object rather than a second observation of the market.
    """
    frame = daily_frame()
    assert rebuild_confirm_pointer(frame.base) == frame._align[7200]


def test_regime_tf_at_the_daily_frame_is_the_mislabelled_copy():
    """`_default_regime_tf` misses every member and falls through to the top.

    This is the channel that reaches *every* 1440m strategy rather than only the
    MULTI_TIMEFRAME ones, because `volatility_normal` is a base filter on 12 of
    13 templates.
    """
    frame = daily_frame()
    assert frame.regime_tf == 7200
    assert 7200 not in (15, 30, 5, 60, 10, 3, 1)
    # And the override still works, which is what ALGO-1's control arm needs.
    override = SymbolFrame(BarSeries("MGC", 1440, swing_bars()), FRAMES[1440],
                           regime_timeframe=1440)
    assert override.regime_tf == 1440


def test_the_alignment_score_can_only_take_two_values_at_the_daily_frame():
    """The decision table ALGO-1's reduction rests on.

    Two voters weighted `log(1441)` and `log(7201)`: agreeing gives |a| = 1.0,
    opposed gives 0.0996, and `mtf_aligned`'s threshold is 0.4. So "opposed" can
    never fire, and the only reachable firing state is "both directional and
    equal" — lagged self-agreement on one series.
    """
    w_lo, w_hi = math.log(1441.0), math.log(7201.0)
    opposed = abs(w_lo - w_hi) / (w_lo + w_hi)
    assert round(opposed, 4) == 0.0996
    assert opposed < 0.4 < 1.0


def test_the_two_mtf_signals_are_the_same_function_at_the_daily_frame():
    """With two voters, "0.4 weighted majority" and "unanimous" coincide.

    `R4-MT2` proves it from the weights; this pins it per bar. The two agree on
    every bar of the real daily files too (2511/2511 MGC, 1859/1859 MNQ and MES —
    `backtest/BT4/ALGOS.md`), which is why the published "unanimous versus
    majority" comparison at 1440m measured nothing.
    """
    frame = daily_frame()
    a, s = CONDITIONS["mtf_aligned"], CONDITIONS["mtf_strongly_aligned"]
    fired = 0
    for i in range(len(frame.base)):
        snap = frame.snapshot(i)
        ra, rs = a.fn(snap, 1440), s.fn(snap, 1440)
        assert (ra.triggered, ra.direction) == (rs.triggered, rs.direction), i
        fired += ra.triggered
    assert fired > 0, "the series must actually fire, or this proves nothing"


def test_mtf_aligned_at_1440m_reduces_to_one_series_and_one_lag():
    """**The central ALGO-1 claim.** Nothing cross-timeframe is being measured.

    The reference reads the daily series' own trend labels and the reconstructed
    pointer, and never touches the 7200 series. If it reproduces the condition on
    every bar, then `mtf_aligned` at 1440m is exactly "the daily structure trend
    is directional now and was the same direction a few sessions ago".
    """
    frame = daily_frame()
    tf = frame.frames[1440]
    trend = [tf.snapshot(j).structure_trend for j in range(len(tf.series))]
    ptr = rebuild_confirm_pointer(frame.base)
    a = CONDITIONS["mtf_aligned"]
    directional = ("UPTREND", "DOWNTREND")
    fired = 0
    for i in range(len(frame.base)):
        now = trend[i]
        then = trend[ptr[i]] if ptr[i] >= 0 else None
        want = now in directional and now == then
        assert a.fn(frame.snapshot(i), 1440).triggered is want, i
        fired += want
    assert fired > 0


def test_mtf_not_conflicted_at_1440m_reduces_to_a_label_flip():
    """Same reduction for the filter, on a series whose veto path is reachable.

    It vetoes only on an outright UP<->DOWN flip across the lag. `structure_trend`
    has a RANGE state between the two poles, so on the real daily files this
    passes 99.1-99.6% of bars. A fast-flipping synthetic series is used here so
    that both branches are exercised rather than only the passing one.
    """
    frame = daily_frame(leg=10)
    tf = frame.frames[1440]
    trend = [tf.snapshot(j).structure_trend for j in range(len(tf.series))]
    ptr = rebuild_confirm_pointer(frame.base)
    ok = CONDITIONS["mtf_not_conflicted"]
    vetoed = 0
    for i in range(len(frame.base)):
        pair = (trend[i], trend[ptr[i]] if ptr[i] >= 0 else None)
        conflicted = "UPTREND" in pair and "DOWNTREND" in pair
        assert ok.fn(frame.snapshot(i), 1440).triggered is (not conflicted), i
        vetoed += conflicted
    assert vetoed > 0, "the veto branch must be reachable, or this proves nothing"
    assert vetoed < len(frame.base) * 0.1


def test_mtf_not_conflicted_ignores_its_timeframe_argument():
    """`_mtf_ok` reads every member of the frame regardless of `tf`.

    `R4-MT4`. Kept here because a fix to `align_bucket` would change this
    filter's pass rate at 1440m without touching this inertness, and the two must
    not be confused for each other.
    """
    frame = daily_frame()
    ok = CONDITIONS["mtf_not_conflicted"]
    for i in range(0, len(frame.base), 7):
        snap = frame.snapshot(i)
        assert ok.fn(snap, 1440).triggered == ok.fn(snap, 7200).triggered


# --------------------------------------------------------------------------
# Half 2 — what a corrected `align_bucket` must satisfy
# --------------------------------------------------------------------------
@pytest.mark.xfail(strict=False, reason="R4-M3 / BT4-REQ-1: align_bucket ignores "
                                        "minutes above 1440. XPASS means fixed.")
def test_FIX_a_weekly_bucket_differs_from_a_daily_one():
    assert align_bucket(TS, 7200) != align_bucket(TS, 1440)


@pytest.mark.xfail(strict=False, reason="R4-M3 / BT4-REQ-1: coarse buckets collapse. "
                                        "XPASS means fixed.")
def test_FIX_coarse_buckets_are_distinct_from_each_other():
    assert len({align_bucket(TS, m) for m in COARSE}) == len(COARSE)


@pytest.mark.xfail(strict=False, reason="R4-M3 / BT4-REQ-1: a 7200m bucket holds one "
                                        "session. XPASS means fixed.")
def test_FIX_a_weekly_bucket_spans_about_five_sessions():
    per_bucket = collections.Counter(align_bucket(b.ts, 7200) for b in flat_bars(40))
    assert max(per_bucket.values()) >= 4


@pytest.mark.xfail(strict=False, reason="R4-M3 / BT4-REQ-1: the daily frame holds one "
                                        "series twice. XPASS means fixed.")
def test_FIX_the_daily_frames_two_members_are_different_series():
    frame = daily_frame()
    assert len(frame.frames[7200].series) < len(frame.frames[1440].series) / 2
