"""EF2 substrate: load MGC/MCL 60m and 240m from data/archive, and verify.

Single source of truth for which bars EF2 measures on. Every EF2 number is
labelled with the cell key this module produces.

Substrate decision, recorded here because it constrains everything downstream:

* base series is ALWAYS the archive 60m file (718 calendar days, ~11k bars).
  240m frames are resampled UP from it by ``SymbolFrame``, never loaded from
  ``MGC_240m.jsonl`` directly, so the 60m and 240m cells sit on identical
  underlying bars and a difference between them is a timeframe difference and
  not a substrate difference.
* 1440m is NOT used, on either symbol. ``MCL_1440m.jsonl`` holds exactly one
  row [measured], so a daily confirmation timeframe cannot be built for MCL,
  and building it for MGC alone would make the two cells asymmetric. MGC's
  1440m file also spans 2010-2026, a different era from the 60m window.
* 15m/5m are NOT used as confirmation or execution timeframes here: their
  archive span is 57 calendar days against 718 at 60m, so adding one would
  truncate the swing substrate by 92%.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

REPO = "/home/user/Futures01"
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from futures_agents.config import get_contract                      # noqa: E402
from futures_agents.data.archive import BarArchive                  # noqa: E402
from futures_agents.data.bars import BarSeries, resample            # noqa: E402
from futures_agents.features import build_symbol_frame              # noqa: E402
from futures_agents.timeutil import to_et                           # noqa: E402

ARCHIVE_ROOT = os.path.join(REPO, "data", "archive")
SYMBOLS = ("MGC", "MCL")

#: (frame key, timeframe list, primary timeframe). The four cells EF2 owns,
#: each in its own single-timeframe frame and in the 60m+240m group frame.
CELLS: Tuple[Tuple[str, Tuple[int, ...], int], ...] = (
    ("f60__p60",      (60,),      60),    # 60m alone
    ("f240__p240",    (240,),     240),   # 240m alone
    ("f60_240__p60",  (60, 240),  60),    # group, thesis on 60m
    ("f60_240__p240", (60, 240),  240),   # group, thesis on 240m
)


@dataclass
class Cell:
    symbol: str
    key: str                     # e.g. "MGC:f60_240__p240"
    timeframes: Tuple[int, ...]
    primary_tf: int
    frame: object                # SymbolFrame
    n_bars: int

    @property
    def base_minutes(self) -> int:
        return self.frame.base.minutes


_ARCHIVE = BarArchive(ARCHIVE_ROOT)
_SERIES_CACHE: Dict[Tuple[str, int], BarSeries] = {}
_FRAME_CACHE: Dict[Tuple[str, Tuple[int, ...]], object] = {}


def base_series(symbol: str, minutes: int = 60) -> BarSeries:
    k = (symbol.upper(), minutes)
    if k not in _SERIES_CACHE:
        _SERIES_CACHE[k] = _ARCHIVE.load(symbol, minutes)
    return _SERIES_CACHE[k]


def frame_for(symbol: str, timeframes: Sequence[int]):
    tfs = tuple(sorted(set(int(t) for t in timeframes)))
    k = (symbol.upper(), tfs)
    if k not in _FRAME_CACHE:
        base = base_series(symbol, 60)
        if len(base) == 0:
            raise RuntimeError(f"no archive 60m bars for {symbol}")
        _FRAME_CACHE[k] = build_symbol_frame(base, tfs, get_contract(symbol))
    return _FRAME_CACHE[k]


def cells(symbols: Sequence[str] = SYMBOLS) -> List[Cell]:
    out: List[Cell] = []
    for sym in symbols:
        for key, tfs, ptf in CELLS:
            fr = frame_for(sym, tfs)
            out.append(Cell(symbol=sym.upper(), key=f"{sym.upper()}:{key}",
                            timeframes=tfs, primary_tf=ptf, frame=fr,
                            n_bars=len(fr.base)))
    return out


# ---------------------------------------------------------------- verification
def verify_against_csv_raw(symbol: str, minutes: int,
                           tol: float = 1e-5) -> dict:
    """Archive vs csv/raw for one symbol and timeframe, with a TOLERANCE.

    BRIEF data-policy condition 2: the published 60m equivalence table does not
    cover 240m, so 240m is checked here. Compared in UTC on both sides -
    csv/raw is +00:00, the archive is -04:00, and slicing the offset off
    manufactures a 23-point mean difference on MGC (BRIEF, timezone trap).
    """
    import csv
    from datetime import datetime, timezone

    path = os.path.join(REPO, "csv", "raw", f"{symbol}_{_csv_tf(minutes)}.csv")
    out = {"symbol": symbol, "minutes": minutes, "csv_path": path,
           "csv_exists": os.path.isfile(path)}
    if not out["csv_exists"]:
        return out

    raw: Dict[datetime, Tuple[float, float, float, float, float]] = {}
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            ts = datetime.fromisoformat(row["open_time"]).astimezone(timezone.utc)
            raw[ts] = (float(row["open"]), float(row["high"]), float(row["low"]),
                       float(row["close"]), float(row["volume"]))

    arc_series = base_series(symbol, 60)
    if minutes != 60:
        arc_series = resample(arc_series, minutes, keep_partial=False)
    arc = {b.ts.astimezone(timezone.utc):
           (b.open, b.high, b.low, b.close, b.volume) for b in arc_series}

    common = sorted(set(raw) & set(arc))
    max_close = 0.0
    bit_exact = 0
    vol_diff = 0
    for ts in common:
        r, a = raw[ts], arc[ts]
        d = abs(r[3] - a[3])
        max_close = max(max_close, d)
        if r[3] == a[3]:
            bit_exact += 1
        if r[4] != a[4]:
            vol_diff += 1
    out.update(csv_bars=len(raw), archive_bars=len(arc), overlap=len(common),
               bit_exact_closes=bit_exact, max_abs_close_diff=max_close,
               volume_mismatches=vol_diff,
               within_tol=max_close <= tol,
               archive_only=len(set(arc) - set(raw)))
    return out


def _csv_tf(minutes: int) -> str:
    return {1: "1m", 5: "5m", 15: "15m", 30: "30m", 60: "1h",
            240: "4h", 1440: "1d"}.get(minutes, f"{minutes}m")


def session_arithmetic(symbol: str) -> dict:
    """Bar-stamp arithmetic against the 18:00 -> 16:00 ET rule.

    Reported because it is a structural constraint on the swing cell and it is
    exact, not statistical: a 240m bar stamped 12:00 ET closes AT 16:00, the
    flat deadline, so its close is not an admissible entry; a bar stamped 16:00
    spans the 16:00-18:00 no-position window entirely.
    """
    out: dict = {"symbol": symbol}
    for tf in (60, 240):
        s = base_series(symbol, 60)
        if tf != 60:
            s = resample(s, tf, keep_partial=False)
        stamps: Dict[int, int] = {}
        close_at_1600 = 0
        spans_break = 0
        inside_break = 0
        for b in s:
            et = to_et(b.ts)
            stamps[et.hour] = stamps.get(et.hour, 0) + 1
            end = to_et(b.end_ts)
            start_min = et.hour * 60 + et.minute
            end_min = start_min + b.minutes
            if end_min == 16 * 60:
                close_at_1600 += 1
            # 16:00-18:00 ET is minute 960..1080
            if start_min < 1080 and end_min > 960 and not (start_min >= 1080 or end_min <= 960):
                if start_min >= 960 and end_min <= 1080:
                    inside_break += 1
                else:
                    spans_break += 1
        out[f"{tf}m"] = {
            "bars": len(s),
            "hour_stamps": dict(sorted(stamps.items())),
            "bars_closing_at_1600_ET": close_at_1600,
            "bars_spanning_the_1600_1800_break": spans_break,
            "bars_wholly_inside_the_break": inside_break,
        }
    return out


if __name__ == "__main__":
    import json
    rep = {"symbols": {}}
    for sym in SYMBOLS:
        rep["symbols"][sym] = {
            "spans": {},
            "csv_raw_equivalence": {
                "60m": verify_against_csv_raw(sym, 60),
                "240m": verify_against_csv_raw(sym, 240),
            },
            "session_arithmetic": session_arithmetic(sym),
        }
        for tf in (60, 240, 1440):
            s = _ARCHIVE.load(sym, tf)
            if len(s) == 0:
                rep["symbols"][sym]["spans"][f"{tf}m"] = {"bars": 0}
                continue
            b = s.bars
            rep["symbols"][sym]["spans"][f"{tf}m"] = {
                "bars": len(b),
                "first": to_et(b[0].ts).isoformat(),
                "last": to_et(b[-1].ts).isoformat(),
                "calendar_days": (b[-1].ts - b[0].ts).days,
                "distinct_dates": len({to_et(x.ts).date() for x in b}),
            }
    for c in cells():
        rep.setdefault("cells", {})[c.key] = {
            "timeframes": list(c.timeframes), "primary_tf": c.primary_tf,
            "base_minutes": c.base_minutes, "base_bars": c.n_bars,
        }
    print(json.dumps(rep, indent=2, default=str))
