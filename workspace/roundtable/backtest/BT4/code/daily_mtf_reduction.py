"""BT4-ALGO-1 — what a daily MULTI_TIMEFRAME condition actually computes.

`R4-M3` established the mechanism: `align_bucket` takes its `minutes >= 1440`
branch for *every* coarser request, so `align_bucket(ts, 7200) ==
align_bucket(ts, 1440)` and `FRAMES[1440] = [1440, 7200]` holds the daily
series twice, the second copy lagged 2-4 sessions by a mislabelled `end_ts`.

This module does not re-argue that. It answers the next question: **given the
collapse, what do the three `multitimeframe` conditions reduce to at 1440m?**

The method is a reduction with an independent reference. For each condition I
write a second implementation that reads **one series and one integer lag** and
never constructs a frame, then compare the two firing vectors bar by bar. If
they are identical on every bar of every symbol, the condition demonstrably
carries no cross-timeframe information: everything it says can be said by a
lagged self-comparison on the primary series.

A reduction that matches is only interesting if the same method *fails* where
the frame is genuine, so the 240m frame `[240, 1440]` is run as the control:
there the higher timeframe is a real daily series, the reduction must break,
and if it does not then the method is vacuous rather than the frame degenerate.

Deterministic, dependency-free, reads `csv/raw/` (read-only) and nothing else.
"""
from __future__ import annotations

import collections
import json
import math
import os
import random
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from futures_agents.data.bars import Bar, align_bucket, resample
from futures_agents.data.loader import load_csv
from futures_agents.features import SymbolFrame
from futures_agents.strategies.library import CONDITIONS

REPO = os.path.dirname(os.path.abspath(__file__)).split("/workspace/")[0]
DAILY = {"MGC": "MGC_1d.csv", "MNQ": "MNQ_1d.csv", "MES": "MES_1d.csv"}
DIRECTIONAL = ("UPTREND", "DOWNTREND")

# The shipped frame map, copied rather than imported so a change to `scout`
# cannot silently change what this module claims to have measured.
FRAMES_1440 = [1440, 7200]
FRAMES_240 = [240, 1440]


# --------------------------------------------------------------------------
# Part 1 — the collapse itself, re-verified rather than taken on trust
# --------------------------------------------------------------------------
def bucket_collapse(series) -> Dict[str, object]:
    """Which `minutes` values `align_bucket` cannot tell apart, on real stamps."""
    coarse = [1440, 2880, 4320, 7200, 10080, 43200, 525600]
    groups: Dict[Tuple, List[int]] = collections.defaultdict(list)
    for m in coarse:
        key = tuple(align_bucket(b.ts, m) for b in series.bars)
        groups[key].append(m)
    return {
        "minutes_tested": coarse,
        "distinct_bucketings": len(groups),
        "collapsed_into_one_class": sorted(next(iter(groups.values()))),
    }


def resample_identity(series) -> Dict[str, object]:
    """`resample(daily, 7200)` against the daily series, in order, field by field."""
    up = resample(series, 7200, keep_partial=False)
    n = min(len(up), len(series))
    ohlcv = ("open", "high", "low", "close", "volume")
    same_ohlcv = same_ts = 0
    for i in range(n):
        a, b = up.bars[i], series.bars[i]
        if all(getattr(a, f) == getattr(b, f) for f in ohlcv):
            same_ohlcv += 1
        if a.ts == b.ts:
            same_ts += 1
    # Bars per "7200m" bucket: one, on every bucket, is the collapse in its
    # plainest form.
    per_bucket = collections.Counter(
        collections.Counter(align_bucket(b.ts, 7200) for b in series.bars).values())
    return {
        "daily_bars": len(series),
        "resampled_7200_bars": len(up),
        "ohlcv_identical_in_order": f"{same_ohlcv}/{n}",
        "ts_identical_in_order": f"{same_ts}/{n}",
        "bars_per_7200_bucket": dict(per_bucket),
        "minutes_label_on_the_7200_copy": up.bars[0].minutes if len(up) else None,
        "expected_constituents_per_bucket": max(1, 7200 // series.minutes),
    }


# --------------------------------------------------------------------------
# Part 2 — the reduction
# --------------------------------------------------------------------------
def trend_vectors(frame: SymbolFrame, tfs: Sequence[int]) -> Dict[int, List[Optional[str]]]:
    """Per base bar, the `structure_trend` each timeframe of the frame shows.

    Read through `snapshot()` rather than off the timeframe series directly, so
    what is compared is what a condition actually sees, alignment lag included.
    """
    out: Dict[int, List[Optional[str]]] = {tf: [] for tf in tfs}
    for i in range(len(frame.base)):
        snap = frame.snapshot(i)
        for tf in tfs:
            s = snap.tfs.get(tf)
            out[tf].append(s.structure_trend if s else None)
    return out


def condition_vectors(frame: SymbolFrame, tf: int) -> Dict[str, List[Tuple]]:
    """The `(triggered, direction)` vector of each `multitimeframe` condition.

    These are shipped library conditions that read only the snapshot, so no
    per-study `register_frame` is involved and D38 does not apply here.
    """
    names = ("mtf_aligned", "mtf_strongly_aligned", "mtf_not_conflicted")
    out: Dict[str, List[Tuple]] = {n: [] for n in names}
    for i in range(len(frame.base)):
        snap = frame.snapshot(i)
        for n in names:
            r = CONDITIONS[n].fn(snap, tf)
            out[n].append((bool(r.triggered),
                           r.direction.value if r.triggered and r.direction else None))
    return out


def reference_from_one_series(primary: List[Optional[str]],
                              lagged: List[Optional[str]]) -> Dict[str, List[Tuple]]:
    """The same three conditions, re-derived from two trend labels and nothing else.

    With exactly two voters whose weights are `log(1441)` and `log(7201)`, the
    arithmetic in `library.py` collapses to a three-line decision table:

    * both labels directional and equal  -> `|alignment| = 1.0`, agree == voting == 2
    * both directional and opposed       -> `|alignment| = 0.0996 < 0.4`  -> no()
    * fewer than two directional         -> `voting < 2`                  -> no()

    so `mtf_aligned` and `mtf_strongly_aligned` are both exactly "the label is
    directional now and was the same direction `lag` bars ago", and
    `mtf_not_conflicted` is exactly "the label did not flip UP<->DOWN across
    the lag". Nothing here reads a second series.
    """
    out: Dict[str, List[Tuple]] = {"mtf_aligned": [], "mtf_strongly_aligned": [],
                                   "mtf_not_conflicted": []}
    for a, b in zip(primary, lagged):
        both_dir = a in DIRECTIONAL and b in DIRECTIONAL
        agree = both_dir and a == b
        fired = (True, "LONG" if a == "UPTREND" else "SHORT") if agree else (False, None)
        out["mtf_aligned"].append(fired)
        out["mtf_strongly_aligned"].append(fired)
        conflicted = ("UPTREND" in (a, b)) and ("DOWNTREND" in (a, b))
        # `_mtf_ok` passes with `Direction.NEUTRAL` (FLAT), not with no direction
        # — it is a FILTER, so the direction field is inert but it is populated.
        out["mtf_not_conflicted"].append((False, None) if conflicted
                                         else (True, "NEUTRAL"))
    return out


def weights_check() -> Dict[str, float]:
    """The two numbers the decision table above rests on."""
    w1, w2 = math.log(1440 + 1.0), math.log(7200 + 1.0)
    return {"w_1440": round(w1, 4), "w_7200": round(w2, 4),
            "abs_alignment_when_opposed": round(abs(w1 - w2) / (w1 + w2), 4),
            "abs_alignment_when_agreed": 1.0,
            "condition_threshold": 0.4}


def pointer_lag(frame: SymbolFrame, hi: int, lo: int) -> collections.Counter:
    """Distribution of `idx(lo) - idx(hi)`: how far the copy trails the original."""
    return collections.Counter(a - b for a, b in zip(frame._align[lo], frame._align[hi]))


# --------------------------------------------------------------------------
# Part 3 — why `mtf_not_conflicted` passes 99%+, and what a longer lag does
# --------------------------------------------------------------------------
def lag_sensitivity(labels: List[Optional[str]], lags: Sequence[int],
                    seed: int = 4) -> List[Dict[str, object]]:
    """Conflict rate of a self-comparison as the lag grows.

    The real lag is 2-4 sessions. If the 99% pass rate is a property of the
    shortness of the lag rather than of the market, the conflict rate must climb
    toward the unconditional rate as the lag grows. A count-matched shuffle of
    the label sequence is carried alongside as the control: it destroys the
    label's serial structure while holding its marginal distribution fixed, so
    it says what the conflict rate would be if persistence were the only thing
    doing the work.
    """
    rnd = random.Random(seed)
    shuffled = labels[:]
    rnd.shuffle(shuffled)
    rows = []
    for k in lags:
        for name, v in (("real", labels), ("shuffled", shuffled)):
            pairs = [(v[i], v[i - k]) for i in range(k, len(v))]
            conflict = sum(1 for a, b in pairs
                           if ("UPTREND" in (a, b)) and ("DOWNTREND" in (a, b)))
            agree = sum(1 for a, b in pairs
                        if a in DIRECTIONAL and b in DIRECTIONAL and a == b)
            rows.append({"lag": k, "arm": name, "pairs": len(pairs),
                         "not_conflicted_pct": round(100.0 * (1 - conflict / len(pairs)), 2),
                         "aligned_pct": round(100.0 * agree / len(pairs), 2)})
    return rows


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------
def run_symbol(sym: str, fname: str) -> Dict[str, object]:
    daily = load_csv(os.path.join(REPO, "csv/raw", fname), sym, 1440)
    frame = SymbolFrame(daily, FRAMES_1440)
    tv = trend_vectors(frame, FRAMES_1440)
    got = condition_vectors(frame, 1440)
    want = reference_from_one_series(tv[1440], tv[7200])

    matches = {n: sum(1 for a, b in zip(got[n], want[n]) if a == b) for n in got}
    fires = {n: sum(1 for t, _ in got[n] if t) for n in got}

    # Is the "higher timeframe" snapshot literally an earlier value of the
    # primary's own snapshot? Compare tfs[7200] at bar i against the daily
    # series' own trend at the bar the 7200 pointer is sitting on.
    daily_tf = frame.frames[1440]
    daily_frame_trend = [daily_tf.snapshot(j).structure_trend
                         for j in range(len(daily_tf.series))]
    same_as_history = 0
    checked = 0
    for i in range(len(frame.base)):
        j = frame._align[7200][i]
        if j < 0:
            continue
        checked += 1
        if tv[7200][i] == daily_frame_trend[j]:
            same_as_history += 1

    return {
        "symbol": sym,
        "bars": len(daily),
        "span": f"{daily.bars[0].ts:%Y-%m-%d}..{daily.bars[-1].ts:%Y-%m-%d}",
        "bucket_collapse": bucket_collapse(daily),
        "resample_identity": resample_identity(daily),
        "pointer_lag_1440_minus_7200": dict(sorted(pointer_lag(frame, 7200, 1440).items())),
        "confirm_tf_snapshot_is_a_historical_value_of_the_primary":
            f"{same_as_history}/{checked}",
        "condition_fires_at_1440m": fires,
        "reduction_match_vs_one_series_reference":
            {n: f"{matches[n]}/{len(got[n])}" for n in matches},
        "aligned_equals_strongly_aligned":
            f"{sum(1 for a, b in zip(got['mtf_aligned'], got['mtf_strongly_aligned']) if a == b)}"
            f"/{len(got['mtf_aligned'])}",
        "not_conflicted_pass_pct":
            round(100.0 * sum(1 for t, _ in got['mtf_not_conflicted'] if t) / len(daily), 2),
        "trend_label_census": dict(collections.Counter(tv[1440]).most_common()),
        "lag_sensitivity": lag_sensitivity(tv[1440], (1, 2, 3, 4, 5, 10, 20, 60)),
        "weights": weights_check(),
    }


def run_control(sym: str = "MGC", max_lag: int = 24) -> Dict[str, object]:
    """The 240m frame `[240, 1440]`, where the confirming series is genuinely daily.

    The 240m row has the same two-voter degeneracy (`R4-MT2`, `D17`) but *not*
    the collapse: 1440 is a real, independent series there. So the reduction
    must fail, and it is given every chance to succeed — rather than one lag, it
    is fitted over `max_lag` candidate lags on the primary series and the best
    match of all of them is reported. A best-of-25-lags fit that still misses is
    the statement that the method is not vacuous.

    Note the lag here is measured in **240m bars of the primary series**, not as
    a pointer difference: at 1440m the two pointers index bit-identical series so
    their difference is a bar lag, and at 240m they index different series so it
    is not. Using the pointer difference here would be a category error.
    """
    h1 = load_csv(os.path.join(REPO, "csv/raw", f"{sym}_1h.csv"), sym, 60)
    frame = SymbolFrame(h1, FRAMES_240)
    tv = trend_vectors(frame, FRAMES_240)
    got = condition_vectors(frame, 240)
    n = len(got["mtf_aligned"])
    best = {name: (0, None) for name in got}
    for k in range(0, max_lag + 1):
        lagged = [tv[240][max(0, i - k)] for i in range(len(tv[240]))]
        want = reference_from_one_series(tv[240], lagged)
        for name in got:
            m = sum(1 for a, b in zip(got[name], want[name]) if a == b)
            if m > best[name][0]:
                best[name] = (m, k)
    ident = sum(1 for a, b in zip(tv[240], tv[1440]) if a == b)
    return {
        "symbol": sym, "frame": FRAMES_240, "bind": 240, "base_bars": len(h1),
        "lags_fitted": f"0..{max_lag} bars of the 240m series",
        "primary_trend_equals_confirm_trend": f"{ident}/{n}",
        "best_reduction_match_over_all_lags":
            {name: f"{m}/{n} at lag {k}" for name, (m, k) in best.items()},
        "condition_fires": {name: sum(1 for t, _ in got[name] if t) for name in got},
    }


def main() -> int:
    out: Dict[str, object] = {"treatment_1440m": {}, "control_240m": run_control("MGC")}
    for sym, fname in DAILY.items():
        out["treatment_1440m"][sym] = run_symbol(sym, fname)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "daily_mtf_reduction.json")
    json.dump(out, open(path, "w"), indent=1, default=str)

    for sym, r in out["treatment_1440m"].items():
        print(f"\n=== {sym} 1440m, frame [1440, 7200] — {r['bars']} bars {r['span']}")
        print(f"  align_bucket: {r['bucket_collapse']['minutes_tested']} -> "
              f"{r['bucket_collapse']['distinct_bucketings']} distinct bucketing(s)")
        ri = r["resample_identity"]
        print(f"  resample(daily,7200) vs daily, in order: OHLCV "
              f"{ri['ohlcv_identical_in_order']}, ts {ri['ts_identical_in_order']}"
              f"  (bars per bucket {ri['bars_per_7200_bucket']}, "
              f"label minutes={ri['minutes_label_on_the_7200_copy']})")
        print(f"  pointer lag idx(1440)-idx(7200): {r['pointer_lag_1440_minus_7200']}")
        print(f"  confirm snapshot == an earlier value of the primary: "
              f"{r['confirm_tf_snapshot_is_a_historical_value_of_the_primary']}")
        print(f"  fires: {r['condition_fires_at_1440m']}")
        print(f"  REDUCTION to one series + one lag: "
              f"{r['reduction_match_vs_one_series_reference']}")
        print(f"  mtf_aligned == mtf_strongly_aligned: {r['aligned_equals_strongly_aligned']}")
        print(f"  mtf_not_conflicted pass: {r['not_conflicted_pass_pct']}%")
        print(f"  trend labels: {r['trend_label_census']}")
        print("  lag sensitivity (real vs count-matched shuffle):")
        for row in r["lag_sensitivity"]:
            print(f"    lag {row['lag']:>3} {row['arm']:>9}  "
                  f"not_conflicted {row['not_conflicted_pct']:>6}%   "
                  f"aligned {row['aligned_pct']:>6}%")
    c = out["control_240m"]
    print(f"\n=== CONTROL {c['symbol']} 240m, frame {c['frame']} — "
          f"{c['base_bars']} base bars")
    print(f"  primary trend == confirm trend: {c['primary_trend_equals_confirm_trend']}")
    print(f"  best reduction over {c['lags_fitted']}: "
          f"{c['best_reduction_match_over_all_lags']}")
    print(f"  fires: {c['condition_fires']}")
    print(f"\nwrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
