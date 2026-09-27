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

* **Half 1 — what is true today.** These pin the current arithmetic exactly, with
  the numbers ALGO-1 published. They must keep passing until `align_bucket`
  changes, and the moment one fails, a published number moved.
* **Half 2 — what a fix must satisfy.** These are marked ``xfail(strict=False)``
  and describe the *intended* behaviour: a 7200m bucket spans five sessions, a
  weekly resample emits roughly one bar per five, and the daily frame's two
  members are not the same series. They pass the day the fix lands and turn into
  ``XPASS`` rather than breaking the suite, which is the point — a regression
  test for an unfixed defect has to be able to say "still unfixed" without
  failing the build.

Nothing here loads `csv/raw`: the collapse is exact arithmetic on timestamps and
is provable on a handful of synthetic bars, so the whole file runs in
milliseconds. The measured per-symbol counts live in
`workspace/roundtable/backtest/BT4/ALGOS.md`, not here.
"""
from __future__ import annotations

import collections
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

#: Every `minutes` value above a day that `align_bucket` currently cannot tell
#: apart. 2880 = 2 days, 4320 = 3, 7200 = 5 (the "week" `FRAMES` asks for),
#: 10080 = 7, 43200 = 30, 525600 = 365.
COARSE = (1440, 2880, 4320, 7200, 10080, 43200, 525600)


def daily_bars(n: int = 40, *, start: datetime = TS, price: float = 2000.0) -> list:
    """`n` synthetic daily bars, one per calendar day, deterministic and trending.

    A monotone drift is deliberate: it makes `structure_trend` resolve to
    UPTREND rather than UNDEFINED, which is what the frame tests need.
    """
    out = []
    for i in range(n):
        o = price + i
        out.append(Bar(ts=start + timedelta(days=i), open=o, high=o + 4.0,
                       low=o - 1.0, close=o + 3.0, volume=1000.0 + i, minutes=1440))
    return out


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
    assert align_bucket(TS, 15) == datetime(2026, 3, 17, 10, 30, tzinfo=ET)
    assert align_bucket(datetime(2026, 3, 17, 10, 37, tzinfo=ET), 15) == \
        datetime(2026, 3, 17, 10, 30, tzinfo=ET)
    assert len({align_bucket(TS, m) for m in (5, 15, 30, 60, 240)}) == 4


def test_a_weekly_bucket_holds_exactly_one_daily_bar():
    """One bar per bucket is the collapse in its plainest form."""
    bars = daily_bars(40)
    per_bucket = collections.Counter(align_bucket(b.ts, 7200) for b in bars)
    assert set(per_bucket.values()) == {1}
    assert len(per_bucket) == len(bars)


def test_resampling_daily_to_7200_reproduces_the_daily_ohlcv_in_order():
    """The "weekly" series is the daily series, bar for bar, field for field."""
    series = BarSeries("MGC", 1440, daily_bars(40))
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
    series = BarSeries("MGC", 1440, daily_bars(40))
    weekly = resample(series, 7200, keep_partial=False)
    assert weekly.bars[0].minutes == 7200
    assert weekly.bars[0].ts != series.bars[0].ts
    assert weekly.bars[0].ts == align_bucket(series.bars[0].ts, 1440)
    assert weekly.bars[0].end_ts - weekly.bars[0].ts == timedelta(minutes=7200)
    assert series.bars[0].end_ts - series.bars[0].ts == timedelta(minutes=1440)


def test_the_shipped_daily_frame_asks_for_a_timeframe_above_1440():
    """`FRAMES[1440]` is the only exposure, and every other row is clean.

    If a future frame map adds another coarse member this fails, which is the
    early warning: the defect's blast radius is exactly `{tf: [m for m in
    FRAMES[tf] if m > 1440]}`.
    """
    assert FRAMES[1440] == [1440, 7200]
    exposed = {tf: [m for m in tfs if m > 1440] for tf, tfs in FRAMES.items()}
    assert exposed == {5: [], 15: [], 30: [], 60: [], 240: [], 1440: [7200]}
    # Every frame's primary is its own lowest member, which is why only the
    # daily row is exposed rather than every row containing a 1440 member.
    assert all(tfs[0] == tf for tf, tfs in FRAMES.items())


def test_the_daily_frames_two_members_hold_identical_bars():
    """Inside a built `SymbolFrame`, not just in `resample`'s output."""
    frame = SymbolFrame(BarSeries("MGC", 1440, daily_bars(60)), FRAMES[1440])
    lo = frame.frames[1440].series.bars
    hi = frame.frames[7200].series.bars
    assert len(hi) == len(lo) - 1
    for a, b in zip(hi, lo):
        assert (a.open, a.high, a.low, a.close) == (b.open, b.high, b.low, b.close)


def test_the_confirming_pointer_trails_the_primary_by_two_to_four_bars():
    """`_build_alignment` advances on `end_ts`, and the copy's `end_ts` is +5 days.

    The primary pointer is the identity because `frames[1440] is base`; the
    confirming pointer is 2-4 behind it. That lag is the only content the
    "higher timeframe" can carry.
    """
    frame = SymbolFrame(BarSeries("MGC", 1440, daily_bars(60)), FRAMES[1440])
    assert frame._align[1440] == list(range(60))
    lags = collections.Counter(a - b for a, b in
                               zip(frame._align[1440], frame._align[7200]))
    assert set(lags) <= {1, 2, 3, 4, 5}
    assert max(lags, key=lags.get) in (2, 3, 4, 5)


def test_regime_tf_at_the_daily_frame_is_the_mislabelled_copy():
    """`_default_regime_tf` misses every member and falls through to the top.

    This is the channel that reaches *every* 1440m strategy rather than only the
    MULTI_TIMEFRAME ones, because `volatility_normal` is a base filter on 12 of
    13 templates.
    """
    frame = SymbolFrame(BarSeries("MGC", 1440, daily_bars(60)), FRAMES[1440])
    assert frame.regime_tf == 7200
    assert 7200 not in (15, 30, 5, 60, 10, 3, 1)
    # And the override still works, which is what ALGO-1's control arm needs.
    override = SymbolFrame(BarSeries("MGC", 1440, daily_bars(60)), FRAMES[1440],
                           regime_timeframe=1440)
    assert override.regime_tf == 1440


def test_the_two_mtf_signals_are_the_same_function_at_the_daily_frame():
    """With two voters, "0.4 weighted majority" and "unanimous" coincide.

    `R4-MT2` proves it from the weights; this pins it per bar. The two agree on
    every bar of a real daily series too (2511/2511 MGC, 1859/1859 MNQ and MES —
    `backtest/BT4/ALGOS.md`), which is why the published
    "unanimous versus majority" comparison at 1440m measured nothing.
    """
    frame = SymbolFrame(BarSeries("MGC", 1440, daily_bars(80)), FRAMES[1440])
    a, s = CONDITIONS["mtf_aligned"], CONDITIONS["mtf_strongly_aligned"]
    fired = 0
    for i in range(len(frame.base)):
        snap = frame.snapshot(i)
        ra, rs = a.fn(snap, 1440), s.fn(snap, 1440)
        assert (ra.triggered, ra.direction) == (rs.triggered, rs.direction), i
        fired += ra.triggered
    assert fired > 0, "the synthetic series must actually fire, or this proves nothing"


def test_the_alignment_score_can_only_take_two_values_at_the_daily_frame():
    """The decision table ALGO-1's reduction rests on.

    Two voters weighted `log(1441)` and `log(7201)`: agreeing gives |a| = 1.0,
    opposed gives 0.0996, and the condition's threshold is 0.4. So "opposed"
    can never fire and the only reachable firing state is "both directional and
    equal" — i.e. lagged self-agreement on one series.
    """
    import math
    w_lo, w_hi = math.log(1441.0), math.log(7201.0)
    opposed = abs(w_lo - w_hi) / (w_lo + w_hi)
    assert round(opposed, 4) == 0.0996
    assert opposed < 0.4 < 1.0


def test_mtf_not_conflicted_ignores_its_timeframe_argument():
    """`_mtf_ok` reads every member of the frame regardless of `tf`.

    `R4-MT4`. Kept here because a fix to `align_bucket` would change this
    filter's pass rate at 1440m without touching this inertness, and the two
    must not be confused for each other.
    """
    frame = SymbolFrame(BarSeries("MGC", 1440, daily_bars(60)), FRAMES[1440])
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
    bars = daily_bars(40)
    per_bucket = collections.Counter(align_bucket(b.ts, 7200) for b in bars)
    assert max(per_bucket.values()) >= 4


@pytest.mark.xfail(strict=False, reason="R4-M3 / BT4-REQ-1: the daily frame holds one "
                                        "series twice. XPASS means fixed.")
def test_FIX_the_daily_frames_two_members_are_different_series():
    frame = SymbolFrame(BarSeries("MGC", 1440, daily_bars(60)), FRAMES[1440])
    assert len(frame.frames[7200].series) < len(frame.frames[1440].series) / 2
