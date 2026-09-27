#!/usr/bin/env python3
"""Absolute integrity audit of every price series in this repository.

Why this exists
---------------
BT6 found that ``data/archive/MGC_1440m.jsonl`` - the longest series in the repo -
splices two instruments at index 383/384 with a 10.15x step, the pre-break series
being the post-break one at one tenth the scale.  ``yahoo.py`` sets
``auto_adjust=False`` and has no roll handling of any kind, so a longer span buys a
roll gap at every expiry and a momentum rule reads that gap as a return.

Per BRIEF.md's independence clause, this measures every series **absolutely** before
any series is compared with another: a relative test cannot find a hole two series
share, which is how a 51-hour vendor gap spanning COMEX and NYMEX was nearly missed.

What it checks, per series
-------------------------
  scale        the largest bar-to-bar close step, and whether the segments either
               side of it have DISJOINT price ranges (a change of instrument, not a
               return).  ``max(close)/min(close)`` is the one-line extremes check
               nobody had run.
  roll         the bar-boundary gap ``open[i+1] / close[i]``, bucketed.  An
               unadjusted front month gaps at every roll; adjusted series do not.
  shape        rangeless bars (h == l), zero-volume bars, OHLC ordering violations.
  clock        duplicate timestamps, non-monotonic timestamps, the largest calendar
               hole.

Nothing here is a trading statistic.  It is a gate: a series that fails is not
eligible to carry one.

Usage:
    python3 workspace/roundtable/lib/scale_audit.py [--json OUT.json] [paths ...]
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from datetime import datetime

REPO = pathlib.Path(__file__).resolve().parents[3]

# A step this large between two consecutive closes is not a return in any futures
# market; it is a candidate change of instrument.  3x is deliberately far below the
# 10.15x BT6 found, so a smaller splice cannot hide under the threshold.
SPLICE_RATIO = 3.0


def _load_jsonl(path: pathlib.Path) -> list[dict]:
    rows = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            rows.append(
                {"ts": d["ts"], "o": float(d["o"]), "h": float(d["h"]),
                 "l": float(d["l"]), "c": float(d["c"]), "v": float(d["v"])}
            )
    return rows


def _load_csv(path: pathlib.Path) -> list[dict]:
    rows = []
    with path.open() as fh:
        for d in csv.DictReader(fh):
            rows.append(
                {"ts": d["open_time"], "o": float(d["open"]), "h": float(d["high"]),
                 "l": float(d["low"]), "c": float(d["close"]), "v": float(d["volume"])}
            )
    return rows


def load(path: pathlib.Path) -> list[dict]:
    return _load_jsonl(path) if path.suffix == ".jsonl" else _load_csv(path)


def _dt(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def audit(path: pathlib.Path) -> dict:
    rows = load(path)
    n = len(rows)
    out: dict = {"path": str(path.relative_to(REPO)), "bars": n, "verdicts": []}
    if n == 0:
        out["verdicts"].append("EMPTY")
        return out
    if n < 3:
        out["verdicts"].append(f"DEGENERATE({n} bar(s))")
        out["first_ts"] = rows[0]["ts"]
        out["last_ts"] = rows[-1]["ts"]
        return out

    ts = [_dt(r["ts"]) for r in rows]
    close = [r["c"] for r in rows]
    open_ = [r["o"] for r in rows]

    out["first_ts"] = rows[0]["ts"]
    out["last_ts"] = rows[-1]["ts"]
    out["calendar_days"] = (ts[-1] - ts[0]).total_seconds() / 86400.0
    out["years"] = out["calendar_days"] / 365.25

    # ---- clock -------------------------------------------------------------
    dupes = sum(1 for a, b in zip(ts, ts[1:]) if b == a)
    backwards = sum(1 for a, b in zip(ts, ts[1:]) if b < a)
    deltas = [(b - a).total_seconds() / 60.0 for a, b in zip(ts, ts[1:]) if b > a]
    out["duplicate_ts"] = dupes
    out["non_monotonic_ts"] = backwards
    if deltas:
        med = sorted(deltas)[len(deltas) // 2]
        out["median_step_min"] = med
        gap_i = max(range(len(deltas)), key=lambda i: deltas[i])
        out["max_gap_min"] = deltas[gap_i]
        out["max_gap_at"] = rows[gap_i]["ts"]
        out["max_gap_x_median"] = deltas[gap_i] / med if med else None
    if dupes:
        out["verdicts"].append(f"DUPLICATE_TS({dupes})")
    if backwards:
        out["verdicts"].append(f"NON_MONOTONIC_TS({backwards})")

    # ---- scale: the one-line extremes check, then the splice test ----------
    lo, hi = min(close), max(close)
    out["close_min"], out["close_max"] = lo, hi
    out["close_max_over_min"] = hi / lo if lo > 0 else None

    steps = [abs(math.log(b / a)) for a, b in zip(close, close[1:]) if a > 0 and b > 0]
    if steps:
        k = max(range(len(steps)), key=lambda i: steps[i])
        out["max_close_step_ratio"] = max(close[k + 1] / close[k], close[k] / close[k + 1])
        out["max_close_step_pct"] = (close[k + 1] / close[k] - 1.0) * 100.0
        out["max_close_step_at"] = f"[{k}] {rows[k]['ts']} c={close[k]} -> [{k+1}] {rows[k+1]['ts']} c={close[k+1]}"
        for thresh, name in ((0.10, "gt_10pct"), (0.25, "gt_25pct"),
                             (0.50, "gt_50pct"), (1.00, "gt_100pct")):
            out[f"close_steps_{name}"] = sum(1 for s in steps if s > math.log(1 + thresh))

    # Every step above SPLICE_RATIO is tested for disjoint segment ranges.  A real
    # return, however violent, leaves the two segments overlapping; a change of
    # instrument or of price scale does not.
    splices = []
    for i, s in enumerate(steps):
        ratio = math.exp(s)
        if ratio < SPLICE_RATIO:
            continue
        pre, post = close[: i + 1], close[i + 1:]
        disjoint = (max(pre) < min(post)) or (min(pre) > max(post))
        splices.append({
            "index": i, "ts_before": rows[i]["ts"], "ts_after": rows[i + 1]["ts"],
            "close_before": close[i], "close_after": close[i + 1],
            "ratio": ratio, "disjoint_ranges": disjoint,
            "pre_range": [min(pre), max(pre)], "post_range": [min(post), max(post)],
            "pre_bars": i + 1, "post_bars": len(post),
        })
    out["splice_candidates"] = splices
    for s in splices:
        out["verdicts"].append(
            ("SPLICE" if s["disjoint_ranges"] else "JUMP")
            + f"({s['ratio']:.2f}x at {s['ts_after'][:10]})"
        )

    # ---- roll: the bar-boundary gap ---------------------------------------
    gaps = [abs(math.log(o / c)) for c, o in zip(close, open_[1:]) if c > 0 and o > 0]
    if gaps:
        g = max(range(len(gaps)), key=lambda i: gaps[i])
        out["max_bar_gap_pct"] = (open_[g + 1] / close[g] - 1.0) * 100.0
        out["max_bar_gap_at"] = rows[g + 1]["ts"]
        for thresh, name in ((0.01, "gt_1pct"), (0.02, "gt_2pct"),
                             (0.05, "gt_5pct"), (0.10, "gt_10pct")):
            out[f"bar_gaps_{name}"] = sum(1 for x in gaps if x > math.log(1 + thresh))

    # ---- shape -----------------------------------------------------------
    rangeless = sum(1 for r in rows if r["h"] == r["l"])
    zero_vol = sum(1 for r in rows if r["v"] == 0)
    bad_ohlc = sum(1 for r in rows
                   if r["h"] < max(r["o"], r["c"]) or r["l"] > min(r["o"], r["c"])
                   or r["h"] < r["l"])
    out["rangeless_bars"] = rangeless
    out["rangeless_pct"] = 100.0 * rangeless / n
    out["zero_volume_bars"] = zero_vol
    out["zero_volume_pct"] = 100.0 * zero_vol / n
    out["ohlc_violations"] = bad_ohlc
    if bad_ohlc:
        out["verdicts"].append(f"OHLC_VIOLATION({bad_ohlc})")
    if rangeless / n > 0.02:
        out["verdicts"].append(f"RANGELESS({rangeless}/{n}, {100.0*rangeless/n:.1f}%)")
    if zero_vol / n > 0.02:
        out["verdicts"].append(f"ZERO_VOLUME({zero_vol}/{n}, {100.0*zero_vol/n:.1f}%)")

    if not out["verdicts"]:
        out["verdicts"].append("CLEAN")
    return out


def default_paths() -> list[pathlib.Path]:
    paths = sorted((REPO / "data" / "archive").glob("*.jsonl"))
    paths += sorted((REPO / "csv" / "raw").glob("*.csv"))
    return paths


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--json", dest="json_out")
    args = ap.parse_args(argv)

    paths = [pathlib.Path(p) for p in args.paths] or default_paths()
    results = [audit(p) for p in paths]

    w = max(len(r["path"]) for r in results)
    print(f"{'series'.ljust(w)}  {'bars':>7} {'years':>6} {'max/min':>8} "
          f"{'maxstep':>8} {'g>2%':>5} {'rngls%':>7} {'zvol%':>6}  verdicts")
    for r in results:
        ratio = r.get("close_max_over_min")
        step = r.get("max_close_step_ratio")
        ratio_s = f"{ratio:.2f}" if ratio else "-"
        step_s = f"{step:.3f}" if step else "-"
        print(
            f"{r['path'].ljust(w)}  {r['bars']:>7} "
            f"{r.get('years', 0):>6.2f} {ratio_s:>8} {step_s:>8} "
            f"{r.get('bar_gaps_gt_2pct', 0):>5} "
            f"{r.get('rangeless_pct', 0):>7.2f} "
            f"{r.get('zero_volume_pct', 0):>6.2f}  "
            + ", ".join(r["verdicts"])
        )

    if args.json_out:
        pathlib.Path(args.json_out).write_text(json.dumps(results, indent=2))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
