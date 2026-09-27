"""Tests for the Yahoo feed and the append-only archive.

No network. Every test drives :class:`YahooFeed` through its ``row_source``
hook, which supplies the same tuples ``yfinance`` would. The fragile part - the
forming-bar drop, the timezone refusal, the NaN handling, the OHLC repair - is
downstream of that hook and is therefore exercised for real rather than mocked
past.

The lookback-cap tests matter most. Yahoo reports an out-of-range request as an
empty frame with no error, so a project that asks past a cap looks like a
project whose market is closed. These pin the clamp.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from futures_agents.data.archive import BarArchive
from futures_agents.data.bars import Bar, BarSeries
from futures_agents.data.yahoo import (INTERVALS, RESAMPLE_FROM, YahooError,
                                       YahooFeed, YahooProvider, plan_request,
                                       ticker_for)
from futures_agents.timeutil import ET, to_et

NOW = datetime(2026, 9, 25, 15, 0, tzinfo=ET)


def rows(start: datetime, count: int, minutes: int, *, price: float = 100.0,
         volume: float = 500.0):
    """Well-formed vendor rows, timezone-aware as Yahoo returns them."""
    out = []
    for i in range(count):
        ts = start + timedelta(minutes=minutes * i)
        o = price + i
        out.append((ts, o, o + 1.0, o - 1.0, o + 0.5, volume))
    return out


# ------------------------------------------------------------- ticker

def test_futures_roots_get_the_f_suffix():
    """A bare root returns an empty frame from this vendor, not an error."""
    assert ticker_for("MNQ") == "MNQ=F"
    assert ticker_for("mcl") == "MCL=F"


def test_already_qualified_tickers_pass_through():
    assert ticker_for("^GSPC") == "^GSPC"
    assert ticker_for("EURUSD=X") == "EURUSD=X"


# ----------------------------------------------------- lookback caps

@pytest.mark.parametrize("minutes,cap_days", [
    (1, 7), (5, 59), (15, 59), (30, 59), (60, 720),
])
def test_lookback_is_clamped_to_the_interval_cap(minutes, cap_days):
    plan = plan_request("MCL", minutes, days=5_000, now=NOW)
    assert plan.granted_days == cap_days
    assert plan.clamped is True
    assert any("clamped" in n for n in plan.notes)
    assert plan.start == NOW - timedelta(days=cap_days)


def test_a_request_inside_the_cap_is_not_clamped():
    plan = plan_request("MCL", 5, days=10, now=NOW)
    assert plan.clamped is False
    assert plan.granted_days == 10


def test_one_minute_bars_stop_at_seven_days():
    """The cap that catches most people: 1m history is a week, full stop."""
    assert INTERVALS[1][1] == timedelta(days=7)
    assert plan_request("MNQ", 1, days=8, now=NOW).granted_days == 7


# ------------------------------------------- intervals Yahoo lacks

def test_four_hour_bars_are_resampled_from_hourly():
    """MCL's measured framework needs 240m; this vendor has no 4h bar."""
    plan = plan_request("MCL", 240, days=100, now=NOW)
    assert plan.resampled is True
    assert plan.fetch_minutes == 60
    assert plan.interval == "1h"
    assert any("no 240m bar" in n for n in plan.notes)


def test_an_underivable_timeframe_says_what_is_available():
    with pytest.raises(YahooError) as exc:
        plan_request("MCL", 7, days=5, now=NOW)
    msg = str(exc.value)
    assert "no 7m bar" in msg and "Served directly" in msg


def test_every_resample_source_is_a_real_interval():
    for wanted, source in RESAMPLE_FROM.items():
        assert source in INTERVALS, f"{wanted}m resamples from a missing {source}m"


# --------------------------------------------------- the conversion

def test_the_forming_bar_is_dropped():
    """Its high, low and close are not final; including it is lookahead bias."""
    start = NOW - timedelta(minutes=60 * 4)
    feed = YahooFeed(row_source=lambda plan: rows(start, 5, 60))
    res = feed.fetch("MCL", minutes=60, days=5, now=NOW)

    assert res.dropped_forming == 1
    assert res.bars_kept == 4
    last = res.series.last
    assert last.ts + timedelta(minutes=60) <= NOW


def test_the_forming_bar_can_be_kept_deliberately():
    start = NOW - timedelta(minutes=60 * 4)
    feed = YahooFeed(row_source=lambda plan: rows(start, 5, 60),
                     keep_forming_bar=True)
    res = feed.fetch("MCL", minutes=60, days=5, now=NOW)
    assert res.dropped_forming == 0
    assert res.bars_kept == 5


def test_a_naive_timestamp_is_refused_not_guessed():
    """Assuming UTC shifts every session boundary by four or five hours."""
    naive = datetime(2026, 9, 25, 10, 0)          # no tzinfo
    feed = YahooFeed(row_source=lambda plan: [(naive, 1.0, 2.0, 0.5, 1.5, 10.0)])
    with pytest.raises(YahooError, match="naive timestamp"):
        feed.fetch("MCL", minutes=60, days=5, now=NOW)


def test_utc_timestamps_are_converted_to_eastern():
    utc_ts = datetime(2026, 9, 25, 14, 0, tzinfo=timezone.utc)   # 10:00 ET
    feed = YahooFeed(row_source=lambda plan: [(utc_ts, 1.0, 2.0, 0.5, 1.5, 10.0)])
    res = feed.fetch("MCL", minutes=60, days=5, now=NOW)
    assert res.bars_kept == 1
    bar = res.series.last
    assert bar.ts.hour == 10
    assert bar.ts.tzinfo is not None


def test_rows_with_nan_prices_are_dropped_not_zeroed():
    """A 0.0 low would corrupt every range calculation downstream."""
    ts = NOW - timedelta(hours=3)
    feed = YahooFeed(row_source=lambda plan: [
        (ts, 100.0, 101.0, 99.0, 100.5, 500.0),
        (ts + timedelta(hours=1), float("nan"), float("nan"),
         float("nan"), float("nan"), 0.0),
    ])
    res = feed.fetch("MCL", minutes=60, days=5, now=NOW)
    assert res.dropped_no_price == 1
    assert res.bars_kept == 1
    assert all(b.low > 0 for b in res.series)


def test_missing_volume_is_counted_and_warned_about():
    """Zero volume on a bar with a real range breaks liquidity filters."""
    ts = NOW - timedelta(hours=3)
    feed = YahooFeed(row_source=lambda plan: [
        (ts, 100.0, 101.0, 99.0, 100.5, float("nan")),
    ])
    res = feed.fetch("MCL", minutes=60, days=5, now=NOW)
    assert res.bars_kept == 1
    assert res.bars_missing_volume == 1
    assert res.series.last.volume == 0.0
    assert any("volume > 0" in w for w in res.warnings)


def test_float_noise_in_ohlc_is_repaired_not_discarded():
    """A close a hair outside the high is the vendor's rounding, not a bad bar."""
    ts = NOW - timedelta(hours=3)
    feed = YahooFeed(row_source=lambda plan: [
        (ts, 100.0, 100.4999999, 99.0, 100.5, 250.0),
    ])
    res = feed.fetch("MCL", minutes=60, days=5, now=NOW)
    assert res.repaired_ohlc == 1
    assert res.bars_kept == 1
    bar = res.series.last
    assert bar.high >= bar.close and bar.low <= bar.open
    bar.validate()


def test_an_empty_frame_explains_itself():
    """The failure mode that looks like a closed market."""
    feed = YahooFeed(row_source=lambda plan: [])
    res = feed.fetch("MNQ", minutes=1, days=90, now=NOW)
    assert res.is_empty
    joined = " ".join(res.warnings)
    assert "empty frame" in joined and "lookback cap" in joined
    assert any("clamped" in w for w in res.warnings)


def test_resampling_produces_the_requested_timeframe():
    start = NOW.replace(minute=0, second=0, microsecond=0) - timedelta(hours=24)
    feed = YahooFeed(row_source=lambda plan: rows(start, 24, 60))
    res = feed.fetch("MCL", minutes=240, days=30, now=NOW)
    assert res.plan.resampled is True
    assert res.bars_kept > 0
    assert all(b.minutes == 240 for b in res.series)


# ------------------------------------------------------- provider

def test_provider_serves_the_data_provider_interface():
    start = NOW - timedelta(hours=10)
    feed = YahooFeed(row_source=lambda plan: rows(start, 10, 60))
    prov = YahooProvider(["MCL", "MGC"], minutes=60, days=30, feed=feed)

    assert list(prov.symbols()) == ["MCL", "MGC"]
    series = prov.base_series("MCL")
    assert len(series) > 0
    assert prov.result_for("MCL").bars_kept == len(series)
    # Cached: the same object comes back rather than a second fetch.
    assert prov.base_series("MCL") is series


# -------------------------------------------------------- archive

def _series(start: datetime, count: int, *, minutes: int = 60,
            volume: float = 100.0, symbol: str = "MCL") -> BarSeries:
    bars = []
    for i in range(count):
        ts = to_et(start + timedelta(minutes=minutes * i))
        o = 100.0 + i
        bars.append(Bar(ts=ts, open=o, high=o + 1, low=o - 1, close=o + 0.5,
                        volume=volume, minutes=minutes))
    return BarSeries(symbol, minutes, bars)


def test_archive_round_trips(tmp_path):
    arc = BarArchive(str(tmp_path))
    start = datetime(2026, 9, 1, 9, 0, tzinfo=ET)
    rep = arc.reconcile(_series(start, 10))
    assert rep.added == 10 and rep.total == 10

    back = arc.load("MCL", 60)
    assert len(back) == 10
    assert back.bars[0].open == 100.0


def test_a_vendor_retraction_never_deletes_history(tmp_path):
    """The whole reason this class exists.

    Yahoo's window slides at both ends. A later download that is MISSING bars
    an earlier one contained must not shorten the archive - a store that
    overwrites itself loses that history silently.
    """
    arc = BarArchive(str(tmp_path))
    start = datetime(2026, 9, 1, 9, 0, tzinfo=ET)
    arc.reconcile(_series(start, 20))

    # The vendor re-issues the same window, minus its first five bars - the
    # sliding-window case, where the retraction is at the FRONT.
    partial = BarSeries("MCL", 60, list(_series(start, 20).bars[5:]))
    window = (start, start + timedelta(minutes=60 * 20))
    rep = arc.reconcile(partial, window=window)

    assert rep.retracted == 5
    assert "VENDOR RETRACTED 5" in rep.summary()
    assert len(arc.load("MCL", 60)) == 20, "the archive must never shrink"


def test_a_hole_in_the_middle_is_caught_without_an_explicit_window(tmp_path):
    """Interior retractions are detectable from the download's own span."""
    arc = BarArchive(str(tmp_path))
    start = datetime(2026, 9, 1, 9, 0, tzinfo=ET)
    arc.reconcile(_series(start, 10))

    full = _series(start, 10).bars
    holed = BarSeries("MCL", 60, full[:3] + full[6:])      # bars 3,4,5 missing
    rep = arc.reconcile(holed)

    assert rep.retracted == 3
    assert len(arc.load("MCL", 60)) == 10


def test_without_a_window_a_front_retraction_is_invisible(tmp_path):
    """Documents exactly why reconcile_result passes the plan's window.

    The download's own first stamp cannot reveal that earlier bars were
    dropped - from the download's point of view, history simply starts there.
    """
    arc = BarArchive(str(tmp_path))
    start = datetime(2026, 9, 1, 9, 0, tzinfo=ET)
    arc.reconcile(_series(start, 20))

    partial = BarSeries("MCL", 60, list(_series(start, 20).bars[5:]))
    rep = arc.reconcile(partial)                # no window

    assert rep.retracted == 0, "the span heuristic cannot see a front retraction"
    assert len(arc.load("MCL", 60)) == 20, "but nothing is lost either way"


def test_a_zero_volume_reissue_does_not_overwrite_a_real_bar(tmp_path):
    arc = BarArchive(str(tmp_path))
    start = datetime(2026, 9, 1, 9, 0, tzinfo=ET)
    arc.reconcile(_series(start, 5, volume=750.0))

    arc.reconcile(_series(start, 5, volume=0.0))
    kept = arc.load("MCL", 60)
    assert all(b.volume == 750.0 for b in kept), \
        "a zero-volume re-issue is less informative than the bar already held"


def test_new_bars_extend_the_archive(tmp_path):
    arc = BarArchive(str(tmp_path))
    start = datetime(2026, 9, 1, 9, 0, tzinfo=ET)
    arc.reconcile(_series(start, 10))
    rep = arc.reconcile(_series(start + timedelta(minutes=60 * 10), 5))
    assert rep.added == 5
    assert len(arc.load("MCL", 60)) == 15


def test_a_corrupt_line_is_reported_not_silently_skipped(tmp_path):
    arc = BarArchive(str(tmp_path))
    start = datetime(2026, 9, 1, 9, 0, tzinfo=ET)
    arc.reconcile(_series(start, 3))
    path = arc.path_for("MCL", 60)
    path.write_text(path.read_text() + "{ not a bar }\n")
    with pytest.raises(ValueError, match="not a readable bar"):
        arc.load("MCL", 60)


# ------------------------------------------------- transport failures

def test_a_blocked_egress_is_explained_not_a_stack_trace():
    """A refused proxy is an environment problem, and must read as one."""
    def boom(plan):
        raise ConnectionError(
            "Failed to perform, curl: (7) CONNECT tunnel failed, response 403")

    feed = YahooFeed(row_source=boom)
    with pytest.raises(YahooError) as exc:
        feed.fetch("MCL", minutes=60, days=5, now=NOW)
    msg = str(exc.value)
    assert "egress policy" in msg
    assert "not a bug in this code" in msg
    assert "no history was affected" in msg


def test_a_timeout_suggests_retrying():
    def slow(plan):
        raise TimeoutError("request timed out")

    feed = YahooFeed(row_source=slow)
    with pytest.raises(YahooError, match="rate-limits"):
        feed.fetch("MCL", minutes=60, days=5, now=NOW)
