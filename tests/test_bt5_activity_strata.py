"""BT5 regression tests for the activity-stratification machinery (BT5-ALGO-1).

Three groups, and the first two are repo-level gaps rather than tests of BT5's
own code:

1. **`relative_volume` look-ahead.** `tests/test_indicators.py` sweeps sixteen
   indicators for the "appending a future bar never changes history" invariant
   but cannot reach `relative_volume`, which takes `Bar` objects rather than
   float sequences, so it is absent from that parametrisation
   [repo-verified: tests/test_indicators.py:53-73]. BT5-ALGO-1 residualises
   activity on time of day *using* `relative_volume`, so the invariant it
   depends on had no guard. These tests add one.

2. **`Trade.entry_ts` is the fill bar, not the signal bar.** The whole of S2
   turns on stratifying the bar the strategy *read* rather than the bar it was
   *filled* on, and those are different bars
   [repo-verified: futures_agents/backtest/engine.py:290-295, :372]. If that
   relationship ever changed, BT5-ALGO-1 would silently start conditioning on
   information the decision did not have. Pinned here.

3. **BT5's own stratifier and permutation primitives**, on synthetic input:
   tie handling, count balance, block-preservation and determinism.

Everything here runs on synthetic bars and touches no file under `csv/`.
"""
from __future__ import annotations

import os
import random
import sys
from collections import Counter
from datetime import timedelta

import pytest

from futures_agents.backtest.engine import BacktestEngine
from futures_agents.data.bars import Bar
from futures_agents.indicators.volume import relative_volume

from conftest import (SESSION_OPEN, StubStrategy, frame_from_rows,
                      zero_cost_model)

_BT5 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "workspace", "roundtable", "backtest", "BT5", "code")
sys.path.insert(0, _BT5)
import s2 as S2  # noqa: E402


# --------------------------------------------------------------------------
# 1. relative_volume look-ahead
# --------------------------------------------------------------------------
def _hourly(n: int, seed: int = 5):
    """`n` hourly bars whose volume varies by clock hour and by day.

    A same-clock-bucket norm is only exercised when the bucket repeats, so the
    series has to span several days. 24 bars a day, 6 days.
    """
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        ts = SESSION_OPEN + timedelta(hours=i)
        # A U-shape in the clock hour plus day-level noise: exactly the
        # structure the norm exists to remove.
        base = 100.0 + 400.0 * abs(12 - (ts.hour % 24)) / 12.0
        out.append(Bar(ts=ts, open=100.0, high=101.0, low=99.0, close=100.5,
                       volume=round(base * rnd.uniform(0.5, 1.5)), minutes=60))
    return out


def test_relative_volume_never_changes_a_historical_value():
    """THE invariant, for the one indicator the suite's sweep cannot reach."""
    bars = _hourly(144)
    bad = []
    for k in range(2, len(bars)):
        short, long_ = relative_volume(bars[:k], 20), relative_volume(bars[:k + 1], 20)
        for i in range(k):
            a, b = short[i], long_[i]
            if a is None and b is None:
                continue
            if a is None or b is None or abs(a - b) > 1e-12:
                bad.append(f"k={k} i={i}: {a!r} -> {b!r}")
    assert not bad, (f"relative_volume: appending a bar changed {len(bad)} "
                     f"historical value(s); first: {bad[:5]}")


def test_relative_volume_returns_one_value_per_bar_with_none_in_warm_up():
    """Same length as the input, and None until the clock bucket has a prior."""
    bars = _hourly(72)
    rv = relative_volume(bars, 20)
    assert len(rv) == len(bars)
    # The first 24 bars are each the first appearance of their clock bucket.
    assert all(v is None for v in rv[:24]), rv[:24]
    assert all(v is not None for v in rv[24:]), rv[24:30]


def test_relative_volume_excludes_the_current_bar_from_its_own_norm():
    """The bar being measured must not be inside the average it is divided by.

    Built so the answer is exact: two prior same-hour bars of volume 100 and
    300, then one of 400. 400 / 200 == 2.0. If the current bar leaked into the
    denominator the answer would be 400/266.67 == 1.5.
    """
    vols = {0: [100.0, 300.0, 400.0]}
    bars = []
    for day in range(3):
        for hour in range(24):
            ts = SESSION_OPEN.replace(hour=0, minute=0) + timedelta(
                days=day, hours=hour)
            v = vols.get(hour, [50.0, 50.0, 50.0])[day]
            bars.append(Bar(ts=ts, open=1.0, high=1.0, low=1.0, close=1.0,
                            volume=v, minutes=60))
    rv = relative_volume(bars, 20)
    assert rv[48] == pytest.approx(2.0)


def test_relative_volume_guards_a_zero_volume_norm():
    """A clock bucket whose prior bars are all zero yields None, not a
    ZeroDivisionError and not an infinity. 3.5-4.0% of the hourly bars in
    `csv/raw` have volume exactly zero, so this path is reached on real data."""
    bars = []
    for day in range(3):
        for hour in range(2):
            ts = SESSION_OPEN.replace(hour=0, minute=0) + timedelta(
                days=day, hours=hour)
            bars.append(Bar(ts=ts, open=1.0, high=1.0, low=1.0, close=1.0,
                            volume=0.0 if hour == 0 else 10.0, minutes=60))
    rv = relative_volume(bars, 20)
    assert rv[2] is None and rv[4] is None          # the all-zero bucket
    assert rv[3] == pytest.approx(1.0)              # the non-zero one


# --------------------------------------------------------------------------
# 2. entry_ts is the fill bar, one bar after the signal
# --------------------------------------------------------------------------
_ROWS = [
    (21_000.0, 21_005.0, 20_995.0, 21_000.0),   # 0
    (21_000.0, 21_005.0, 20_995.0, 21_000.0),   # 1
    (21_000.0, 21_005.0, 20_995.0, 21_002.0),   # 2  <- signal bar
    (21_010.0, 21_012.0, 21_008.0, 21_010.0),   # 3  <- fill bar, opens 21010
    (21_010.0, 21_035.0, 21_008.0, 21_032.0),   # 4  target
    (21_030.0, 21_032.0, 21_028.0, 21_030.0),   # 5
]


def test_bt5_signal_bar_offset_is_exactly_one_bar_before_entry_ts():
    """S2 stratifies the signal bar; the dump stores the fill bar. Pin the gap.

    `BT5-ALGO-1` takes the bar one timeframe *before* `Trade.entry_ts` as the
    bar whose statistics the strategy read, and `geo_trades.json` carries only
    `entry_ts`. `tests/test_backtest.py` already pins the engine's fill
    location; what is pinned here is the **offset BT5 relies on** - that
    `entry_index - 1` is the signal bar and not merely some earlier bar. If this
    fails, every number under `backtest/BT5/` conditions on the wrong bar.
    """
    frame = frame_from_rows(_ROWS)
    strat = StubStrategy(signal_at=2, entry=21_010.0, stop=21_000.0,
                         targets=[21_030.0])
    res = BacktestEngine(frame, zero_cost_model()).run(strat)
    trades = res.trades
    assert len(trades) == 1
    t = trades[0]
    assert t.entry_index - 1 == t.signal_index == 2
    assert t.entry_ts == frame.base.bars[3].ts
    bar_gap = frame.base.bars[3].ts - frame.base.bars[2].ts
    assert bar_gap == timedelta(minutes=frame.base.minutes)


# --------------------------------------------------------------------------
# 3. BT5's stratifier and permutation primitives
# --------------------------------------------------------------------------
def _cell(vols, buckets):
    return [dict(i=i, volume=v, bucket=b)
            for i, (v, b) in enumerate(zip(vols, buckets))]


def test_within_bucket_rank_averages_ties():
    """Equal volumes share a rank. Otherwise a block of zero-volume bars would
    be ordered by its position in the file, which is a time index wearing an
    activity label."""
    rows = _cell([0, 0, 0, 5], [1, 1, 1, 1])
    r = S2.within_bucket_rank(rows)
    assert r[0] == r[1] == r[2] == pytest.approx(1.0 / 3.0)
    assert r[3] == pytest.approx(1.0)


def test_within_bucket_rank_returns_none_for_a_singleton_bucket():
    """A rank over one observation carries no information; 0.5 would hand it the
    middle stratum for free."""
    rows = _cell([7, 1, 9], [1, 2, 2])
    r = S2.within_bucket_rank(rows)
    assert r[0] is None
    assert r[1] == pytest.approx(0.0) and r[2] == pytest.approx(1.0)


def test_within_bucket_rank_is_invariant_to_a_per_bucket_rescale():
    """This is what "residualised on time of day" has to mean: multiplying every
    bar in one clock bucket by a constant must not change any stratum."""
    vols = [3, 9, 27, 1, 2, 4]
    buckets = [1, 1, 1, 2, 2, 2]
    a = S2.within_bucket_rank(_cell(vols, buckets))
    scaled = [v * (100.0 if b == 1 else 0.01) for v, b in zip(vols, buckets)]
    b = S2.within_bucket_rank(_cell(scaled, buckets))
    assert a == b


def test_terciles_split_counts_evenly():
    vals = list(range(300))
    cuts = S2._terciles(vals, 3)
    got = Counter(S2._stratum(v, cuts) for v in vals)
    assert got[0] == got[1] == got[2] == 100, got


def test_sign_test_matches_the_exact_binomial():
    assert S2.sign_test([1, 1, 1])["p_two_sided"] == pytest.approx(0.25)
    assert S2.sign_test([1, -1])["p_two_sided"] == pytest.approx(1.0)
    assert S2.sign_test([0, 0])["n"] == 0
    r = S2.sign_test([1] * 8 + [-1] * 2)
    assert r == dict(n=10, positive=8, negative=2,
                     p_two_sided=pytest.approx(2 * 56 / 1024))


def _tiny():
    """One cell, two clock buckets, four bars each, labelled 0/1/2 + a spare."""
    bars = {("X", 60, "S1"): _cell([1, 2, 3, 4, 10, 20, 30, 40],
                                   [0, 0, 0, 0, 60, 60, 60, 60])}
    labels = {("X", 60, "S1"): [0, 0, 2, 2, 0, 0, 2, 2]}
    joined = [dict(symbol="X", tf=60, slice="S1", sig_i=i,
                   strategy="s%d" % (i % 2), r=float(i) - 3.5)
              for i in range(8)]
    return joined, bars, labels


def test_permutation_moves_labels_only_inside_a_clock_bucket_block():
    """If a draw leaked across buckets, the residualised axis would be tested
    against the raw null and its p would be wrong in the optimistic direction."""
    joined, bars, labels = _tiny()
    comp = S2._Compact(joined, bars, labels, "bucket", 3, 1)
    rng = random.Random(4)
    for _ in range(20):
        comp.shuffle(rng)
        lab = comp.lab[0]
        assert Counter(lab[:4]) == Counter([0, 0, 2, 2])
        assert Counter(lab[4:]) == Counter([0, 0, 2, 2])


def test_permutation_with_a_cell_block_may_move_labels_across_buckets():
    """The complement of the test above: `block="cell"` is a *different* null and
    is used only for the RAW axis, which deliberately carries time of day."""
    joined, bars, labels = _tiny()
    comp = S2._Compact(joined, bars, labels, "cell", 3, 1)
    rng = random.Random(4)
    crossed = False
    for _ in range(50):
        comp.shuffle(rng)
        if Counter(comp.lab[0][:4]) != Counter([0, 0, 2, 2]):
            crossed = True
            break
    assert crossed, "cell-blocked draws never crossed a bucket boundary"


def test_fast_path_reproduces_the_reference_statistic():
    """`_Compact.stats()` is a hand-rolled inner loop; the reference
    `per_strategy` is the definition. A silent disagreement between them would
    make the permutation p unfalsifiable."""
    joined, bars, labels = _tiny()
    ref = S2.per_strategy(joined, S2._gof(labels), 3, 1)
    a, b, c, q = S2._Compact(joined, bars, labels, "bucket", 3, 1).stats()
    assert q == ref["qualifying"]
    assert a == pytest.approx(ref["d_mean_r"]["median"])
    assert b == pytest.approx(ref["d_win"]["median"])


def test_permutation_test_is_deterministic_under_a_fixed_seed():
    joined, bars, labels = _tiny()
    kw = dict(draws=50, seed=99, k=3, min_n=1)
    a = S2.permutation_test(joined, bars, labels, "bucket", **kw)
    b = S2.permutation_test(joined, bars, labels, "bucket", **kw)
    assert a["d_mean_r"] == b["d_mean_r"]
    c = S2.permutation_test(joined, bars, labels, "bucket",
                            **{**kw, "seed": 100})
    assert c["d_mean_r"]["p_two_sided"] is not None


def test_permutation_p_is_never_zero():
    """`(ge + 1) / (draws + 1)`. A p of exactly 0 from a finite permutation
    ensemble is a reporting error, not a strong result."""
    joined, bars, labels = _tiny()
    out = S2.permutation_test(joined, bars, labels, "bucket", draws=30,
                              seed=1, k=3, min_n=1)
    for k in ("d_mean_r", "d_win"):
        p = out[k]["p_two_sided"]
        if p is not None:
            assert p >= 1.0 / 31.0
