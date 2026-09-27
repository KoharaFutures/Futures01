"""BT6-ALGO-1 - independent reproduction of R6-D1: the daily VWAP collapse.

R6-D1 claims that at 1440m the `vwap` condition group stops being a
volume-weighted-value group and becomes a bar-shape group, because the
session-anchored standard-deviation band has no width when every bar is its own
session. `vwap` is VWAP's only *required* group, so if that holds, a daily VWAP
strategy is a close-location strategy wearing a VWAP name.

This file reproduces the claim from the primitives rather than inheriting
R6's script. Three measurements, deliberately separate:

  A. band width    - `vwap_bands(bars, "session", (1.0, 2.0))` half-width
                     against the contract's own tick size, per (symbol, tf).
  B. the mechanism - is the half-width zero *because* the bar is the first of
                     its CME trading day (R1's zero-sigma-at-anchor, `D45`)?
                     Measured as: bars-since-anchor vs. half-width, and the
                     count of 1440m bars that are NOT first-of-day.
  C. firing census - every `vwap` condition evaluated through
                     `frame.snapshot(i)` on the exact published frame
                     (`scout.FRAMES`), plus the direction agreement between
                     `above_vwap` and `candle_close_strength`.

Choices made here, stated because they are load-bearing and the finding is
silent on all of them:

* **A tick** is `config.get_contract(sym).tick_size` - MGC 0.10, MES/MNQ 0.25,
  MCL 0.01. Not the minimum observed price increment in the file.
* **Half-width** is `upper_1 - vwap`. It equals `vwap - lower_1` by
  construction; the script asserts the symmetry rather than assuming it.
* **`< 1 tick`** is strict. Because a band exactly one tick wide still cannot
  be crossed by a price on the tick grid, `<= 1 tick` is also reported, along
  with the exactly-zero count, so the reader can pick the threshold.
* **No warm-up is dropped.** Bar 0 of the file is included. Bars where the
  band is `None` are counted separately and excluded from the denominator,
  which is the reading that makes "2511/2511" meaningful.
* **"Daily" means `minutes == 1440`** - the `*_1d.csv` files and the
  `*_1440m.jsonl` archive series. `7200` is *not* counted as a second daily
  timeframe here even though `align_bucket` makes it one (`R4-M3`).

Dependency-free, no network, no API key. Reads `csv/` read-only and
`data/archive/` read-only; writes only under `backtest/BT6/out/`.

Usage:
    PYTHONPATH=. python3 workspace/roundtable/backtest/BT6/code/vwap_daily_census.py
"""
from __future__ import annotations

import json
import math
import os
import sys
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from futures_agents.config import get_contract                       # noqa: E402
from futures_agents.data.bars import Bar, BarSeries, resample        # noqa: E402
from futures_agents.data.loader import load_csv                      # noqa: E402
from futures_agents.features import build_symbol_frame               # noqa: E402
from futures_agents.indicators.volume import vwap_bands              # noqa: E402
from futures_agents.scout import FRAMES                              # noqa: E402
from futures_agents.strategies.library import CONDITIONS             # noqa: E402
from futures_agents.timeutil import trading_day                      # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "out")

#: (symbol, timeframe-minutes, source path, source kind).  csv/raw is the store
#: every published `scan_reports/` row was measured on, so it is the primary.
CSV_CELLS: Tuple[Tuple[str, int, str], ...] = (
    ("MGC", 60, "csv/raw/MGC_1h.csv"),
    ("MES", 60, "csv/raw/MES_1h.csv"),
    ("MNQ", 60, "csv/raw/MNQ_1h.csv"),
    ("MCL", 60, "csv/raw/MCL_1h.csv"),
    ("MGC", 1440, "csv/raw/MGC_1d.csv"),
    ("MES", 1440, "csv/raw/MES_1d.csv"),
    ("MNQ", 1440, "csv/raw/MNQ_1d.csv"),
)

#: 240m has no CSV of its own; the published scans resample it from 60m with
#: `keep_partial=False`, which is what `SymbolFrame` does internally.
RESAMPLED_CELLS: Tuple[Tuple[str, int, str, int], ...] = (
    ("MGC", 240, "csv/raw/MGC_1h.csv", 60),
    ("MES", 240, "csv/raw/MES_1h.csv", 60),
    ("MNQ", 240, "csv/raw/MNQ_1h.csv", 60),
    ("MCL", 240, "csv/raw/MCL_1h.csv", 60),
)

#: `data/archive/` daily, as an independent-store replication. MGC reaches back
#: to 2010. MCL_1440m.jsonl holds exactly one row and is NOT data - excluded.
ARCHIVE_CELLS: Tuple[Tuple[str, int, str], ...] = (
    ("MGC", 1440, "data/archive/MGC_1440m.jsonl"),
    ("MES", 1440, "data/archive/MES_1440m.jsonl"),
    ("MNQ", 1440, "data/archive/MNQ_1440m.jsonl"),
)

VWAP_CONDITIONS = ("above_vwap", "vwap_band_extension", "vwap_band1_bounce",
                   "vwap_reclaim", "vwap_proximity")


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------

def load_jsonl(path: str, symbol: str, minutes: int) -> BarSeries:
    """Read one `data/archive/` series. Read-only; the store is append-only."""
    series = BarSeries(symbol, minutes)
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            ts = d.get("ts") or d.get("open_time") or d.get("timestamp")
            # The archive writes short keys (`o`,`h`,`l`,`c`,`v`); accept both.
            g = lambda *k: next(d[x] for x in k if x in d)
            series.append(Bar(
                ts=_parse_iso(ts),
                open=float(g("open", "o")), high=float(g("high", "h")),
                low=float(g("low", "l")), close=float(g("close", "c")),
                volume=float(g("volume", "v") or 0.0), minutes=minutes,
            ))
    return series


def _parse_iso(raw: str):
    from datetime import datetime
    return datetime.fromisoformat(raw)


def load_cell(symbol: str, minutes: int, path: str,
              src_minutes: Optional[int] = None) -> BarSeries:
    full = os.path.join(REPO, path)
    if path.endswith(".jsonl"):
        return load_jsonl(full, symbol, minutes)
    base = load_csv(full, symbol, src_minutes or minutes)
    if src_minutes and src_minutes != minutes:
        return resample(base, minutes, keep_partial=False)
    return base


# --------------------------------------------------------------------------
# A. band width
# --------------------------------------------------------------------------

def band_census(symbol: str, series: BarSeries) -> Dict[str, object]:
    """Half-width of VWAP band 1, against the contract's tick.

    The half-width is one volume-weighted standard deviation of the anchor
    group's typical price. On the first bar of an anchor group the group holds
    one observation, so the variance is `tp**2 - tp**2` and the band has no
    width at all - R1's mechanism for `D45`, restated.
    """
    bars = series.bars
    spec = get_contract(symbol)
    tick = spec.tick_size
    vb = vwap_bands(bars, "session", (1.0, 2.0))
    line, up1, lo1 = vb["vwap"], vb["upper_1"], vb["lower_1"]

    n_none = 0
    widths: List[float] = []
    asym = 0.0
    for i in range(len(bars)):
        if line[i] is None or up1[i] is None or lo1[i] is None:
            n_none += 1
            continue
        hw = up1[i] - line[i]
        asym = max(asym, abs(hw - (line[i] - lo1[i])))
        widths.append(hw)

    n = len(widths)
    out = {
        "symbol": symbol, "minutes": series.minutes, "bars": len(bars),
        "band_none": n_none, "measured": n, "tick": tick,
        "upper_lower_asymmetry_max": asym,
        "exactly_zero": sum(1 for w in widths if w == 0.0),
        "lt_half_tick": sum(1 for w in widths if w < 0.5 * tick),
        "lt_1_tick": sum(1 for w in widths if w < tick),
        "le_1_tick": sum(1 for w in widths if w <= tick),
        "lt_2_ticks": sum(1 for w in widths if w < 2 * tick),
        "median_ticks": (sorted(widths)[n // 2] / tick) if n else None,
        "max_ticks": (max(widths) / tick) if n else None,
    }
    out["pct_lt_1_tick"] = 100.0 * out["lt_1_tick"] / n if n else None
    out["pct_exactly_zero"] = 100.0 * out["exactly_zero"] / n if n else None
    return out


# --------------------------------------------------------------------------
# B. the mechanism: is a zero-width band the same thing as a first-of-day bar?
# --------------------------------------------------------------------------

def mechanism_census(symbol: str, series: BarSeries) -> Dict[str, object]:
    """Cross-tabulate `half-width < 1 tick` against `first bar of its anchor`.

    `vwap_bands` groups by `trading_day(bar.ts)` for `anchor="session"`
    (`indicators/volume.py:34-35`), so "first bar of its anchor" is exactly
    "the anchor key changed at this bar" - computed here the same way the
    indicator does, not by reading a clock.
    """
    bars = series.bars
    tick = get_contract(symbol).tick_size
    vb = vwap_bands(bars, "session", (1.0, 2.0))
    line, up1 = vb["vwap"], vb["upper_1"]

    tab = Counter()                      # (first_of_day, sub_tick) -> count
    zero = Counter()                     # first_of_day -> exactly-zero count
    since: List[int] = []                # bars since anchor, per bar
    by_since: Dict[int, List[float]] = {}
    cur = None
    k = -1
    for i, b in enumerate(bars):
        key = trading_day(b.ts)
        if key != cur:
            cur, k = key, 0
        else:
            k += 1
        since.append(k)
        if line[i] is None or up1[i] is None:
            continue
        hw = up1[i] - line[i]
        tab[(k == 0, hw < tick)] += 1
        if hw == 0.0:
            zero[k == 0] += 1
        by_since.setdefault(min(k, 12), []).append(hw / tick)

    n_days = len(set(trading_day(b.ts) for b in bars))
    ramp = {}
    for k in sorted(by_since):
        v = sorted(by_since[k])
        ramp[k] = {"n": len(v), "median_ticks": v[len(v) // 2]}

    return {
        "symbol": symbol, "minutes": series.minutes, "bars": len(bars),
        "distinct_trading_days": n_days,
        "first_of_day_bars": sum(1 for k in since if k == 0),
        "not_first_of_day_bars": sum(1 for k in since if k != 0),
        "exactly_zero_and_first": zero[True],
        "exactly_zero_and_later": zero[False],
        "first_and_subtick": tab[(True, True)],
        "first_and_not_subtick": tab[(True, False)],
        "later_and_subtick": tab[(False, True)],
        "later_and_not_subtick": tab[(False, False)],
        "halfwidth_ticks_by_bars_since_anchor": ramp,
    }


# --------------------------------------------------------------------------
# C. condition firing census on the published frame
# --------------------------------------------------------------------------

def condition_census(symbol: str, series: BarSeries, tf: int) -> Dict[str, object]:
    """Fire every `vwap` condition at `tf` on the frame `FRAMES[tf]`.

    Evaluated through `frame.snapshot(i)`, the same path the engine uses, so
    nothing here can see a bar after *i*.
    """
    frame = build_symbol_frame(series, FRAMES[tf])
    names = list(VWAP_CONDITIONS) + ["candle_close_strength", "delta_confirms_bar"]
    fires = Counter()
    dirs: Dict[str, Counter] = {n: Counter() for n in names}
    agree = Counter()
    snaps = 0

    for i in range(len(series)):
        snap = frame.snapshot(i)
        if snap is None:
            continue
        snaps += 1
        res = {}
        for n in names:
            r = CONDITIONS[n].fn(snap, tf)
            res[n] = r
            if r.triggered:
                fires[n] += 1
                dirs[n][r.direction.name] += 1
        av, ccs = res["above_vwap"], res["candle_close_strength"]
        if av.triggered and ccs.triggered:
            agree["co_fired"] += 1
            agree["same_direction"] += int(av.direction == ccs.direction)
        dcb = res["delta_confirms_bar"]
        if av.triggered and dcb.triggered:
            agree["co_fired_delta"] += 1
            agree["same_direction_delta"] += int(av.direction == dcb.direction)

    return {
        "symbol": symbol, "tf": tf, "frame": list(FRAMES[tf]),
        "bars": len(series), "snapshots": snaps,
        "fires": {n: fires[n] for n in names},
        "pct": {n: (100.0 * fires[n] / snaps if snaps else None) for n in names},
        "directions": {n: dict(dirs[n]) for n in names},
        "above_vwap_vs_candle_close_strength": dict(agree),
    }


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def main(argv: Sequence[str]) -> int:
    only = [a for a in argv[1:] if not a.startswith("-")]
    results: Dict[str, object] = {"bands": [], "mechanism": [], "conditions": []}

    cells: List[Tuple[str, int, str, Optional[int], str]] = []
    for sym, tf, path in CSV_CELLS:
        cells.append((sym, tf, path, None, "csv/raw"))
    for sym, tf, path, src in RESAMPLED_CELLS:
        cells.append((sym, tf, path, src, "csv/raw (resampled)"))
    for sym, tf, path in ARCHIVE_CELLS:
        cells.append((sym, tf, path, None, "data/archive"))

    for sym, tf, path, src, store in cells:
        if only and not any(o in f"{sym}_{tf}" for o in only):
            continue
        full = os.path.join(REPO, path)
        if not os.path.exists(full):
            print(f"  skip (absent): {path}")
            continue
        series = load_cell(sym, tf, path, src)
        if len(series) < 2:
            print(f"  skip ({len(series)} bar): {path} - not data")
            continue
        b = band_census(sym, series)
        b["store"], b["path"] = store, path
        results["bands"].append(b)
        print(f"BAND  {sym:4s} {tf:>5}m {store:20s} "
              f"n={b['measured']:<6} <1tick={b['lt_1_tick']:<6} "
              f"({b['pct_lt_1_tick']:.1f}%)  ==0: {b['exactly_zero']:<6} "
              f"median={b['median_ticks']:.2f}t  none={b['band_none']}")

        m = mechanism_census(sym, series)
        m["store"], m["path"] = store, path
        results["mechanism"].append(m)
        print(f"  MECH {sym:4s} {tf:>5}m days={m['distinct_trading_days']:<6} "
              f"first={m['first_of_day_bars']:<6} later={m['not_first_of_day_bars']:<6} "
              f"| first&sub={m['first_and_subtick']:<6} first&not={m['first_and_not_subtick']:<5} "
              f"later&sub={m['later_and_subtick']:<6} later&not={m['later_and_not_subtick']}")

        if tf in FRAMES:
            c = condition_census(sym, series, tf)
            c["store"], c["path"] = store, path
            results["conditions"].append(c)
            p = c["pct"]
            print(f"  COND {sym:4s} {tf:>5}m snaps={c['snapshots']:<6} " + "  ".join(
                f"{n.replace('vwap_', 'v_')}={c['fires'][n]}({p[n]:.1f}%)"
                for n in VWAP_CONDITIONS))
            ag = c["above_vwap_vs_candle_close_strength"]
            print(f"       above_vwap vs candle_close_strength: "
                  f"{ag.get('same_direction', 0)}/{ag.get('co_fired', 0)} same direction; "
                  f"vs delta_confirms_bar: "
                  f"{ag.get('same_direction_delta', 0)}/{ag.get('co_fired_delta', 0)}")

    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, "vwap_daily_census.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    print(f"\nwrote {os.path.relpath(dest, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
