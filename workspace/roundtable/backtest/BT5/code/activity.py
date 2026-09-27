"""BT5-ALGO-1, part 1: the activity join.

R5's sub-task S2 asks whether `MAIN-01`'s named mechanism - per-bar statistics
weighting unequal-activity bars equally - leaves a footprint on the wall-clock
grid this repository already has. Answering it needs no constructed bars: it
needs the activity of the bar each stored trade was decided on, attached to the
stored trade.

This module does exactly that and nothing else. It:

  * rebuilds the 24 cells of the generating study (4 symbols x 2 timeframes x 3
    disjoint slices) through the study's own code path, so the bars are the
    bars the strategies saw;
  * computes the per-bar statistics `MAIN-01` names - ATR, relative volume,
    band widths, close-location value - with the library's own functions at the
    library's own parameters;
  * joins `geo_trades.json` on (symbol, tf, slice, ts), reporting coverage
    rather than assuming it.

**Which bar is "the" bar, and why it is not the one in the dump.**
`Trade.entry_ts` is the *fill* bar's timestamp, not the signal bar's: the engine
fills pending entries at step 1 of bar *i* from a signal raised at step 3 of bar
*i-1* [repo-verified: futures_agents/backtest/engine.py:290-295, :372]. So the
bar whose statistics the strategy actually read, and the last bar knowable at
the decision, is the bar **one timeframe earlier** than the dump's `ts`. That
bar is the primary subject here; the fill bar is carried as a secondary axis and
labelled as not-knowable-at-decision.

Nothing here writes to `csv/` or to `geo_trades.json`. Both are read-only.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   *([os.pardir] * 5)))
for p in (REPO, os.path.join(REPO, "workspace", "studies"),
          os.path.join(REPO, "workspace", "newstrats")):
    if p not in sys.path:
        sys.path.insert(0, p)

from futures_agents.indicators.candles import close_location_value  # noqa: E402
from futures_agents.indicators.core import atr, bollinger, keltner  # noqa: E402
from futures_agents.indicators.volume import relative_volume  # noqa: E402
from futures_agents.timeutil import classify_session, to_et, trading_day  # noqa: E402

TRADES = "workspace/strategy_research/scratch/geo_trades.json"

SYMBOLS = ["MGC", "MES", "MNQ", "MCL"]
TFS = [240, 60]
SLICES = 3

#: Library parameters, not choices of mine. `features.py` builds every frame
#: with exactly these [repo-verified: futures_agents/features.py:235, :242,
#: :259, :271].
ATR_PERIOD = 14
RELVOL_LOOKBACK_DAYS = 20
BB_PERIOD, BB_MULT = 20, 2.0
KC_PERIOD, KC_MULT = 20, 1.5


# --------------------------------------------------------------------------
# Cells
# --------------------------------------------------------------------------
def build_cells() -> Dict[Tuple[str, int, str], "object"]:
    """The 24 (symbol, tf, slice) BarSeries of the generating study.

    Rebuilt through `toolkit.disjoint_slices` / `toolkit.slice_series`, which is
    the code `run_geometry.py` calls [repo-verified:
    workspace/newstrats/run_geometry.py:149-152]. Both are pure functions of the
    frozen `csv/raw` snapshot, so this is a reproduction and not an
    approximation - BT3 established that the generating study is deterministic
    by reproducing all 21,954 trades from it exactly
    [cite: backtest/BT3/ALGOS.md, choice 9].
    """
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        import toolkit as T  # noqa: E402  (needs REPO as cwd for csv/raw paths)
        out = {}
        for sym in SYMBOLS:
            for tf in TFS:
                for k, (lo, hi) in enumerate(T.disjoint_slices(sym, tf, SLICES), 1):
                    out[(sym, tf, f"S{k}")] = T.slice_series(sym, tf, lo, hi)
        return out
    finally:
        os.chdir(cwd)


def bar_table(series) -> List[dict]:
    """Per-bar activity and per-bar statistics for one cell.

    Every column is a pure function of this cell's own bars, computed with the
    library's own indicator at the library's own parameter, so it equals what
    `build_symbol_frame` put in front of the strategies. `checks.py` asserts
    that equality rather than asserting it here.
    """
    bars = series.bars
    h = [b.high for b in bars]
    lo = [b.low for b in bars]
    c = [b.close for b in bars]
    a = atr(h, lo, c, ATR_PERIOD)
    rv = relative_volume(bars, RELVOL_LOOKBACK_DAYS)
    bu, bm, bl = bollinger(c, BB_PERIOD, BB_MULT)
    ku, _, kl = keltner(h, lo, c, KC_PERIOD, KC_MULT)

    rows = []
    for i, b in enumerate(bars):
        et = to_et(b.ts)
        bbw = None if (bu[i] is None or bl[i] is None or not bm[i]) else (bu[i] - bl[i]) / bm[i]
        kcw = None if (ku[i] is None or kl[i] is None or not c[i]) else (ku[i] - kl[i]) / c[i]
        rows.append(dict(
            i=i,
            ts=b.ts.isoformat(),
            volume=b.volume,
            # --- the per-bar statistics MAIN-01 names ---
            atr=a[i],
            atr_over_close=None if (a[i] is None or not c[i]) else a[i] / c[i],
            rel_volume=rv[i],
            bb_width=bbw,
            kc_width=kcw,
            clv=close_location_value(b),
            abs_ret=None if i == 0 else abs(c[i] - c[i - 1]) / c[i - 1],
            # --- time-of-day handles ---
            bucket=et.hour * 60 + et.minute,
            session=classify_session(b.ts),
            day=trading_day(b.ts).isoformat(),
        ))
    return rows


# --------------------------------------------------------------------------
# Trailing activity window
# --------------------------------------------------------------------------
def trailing_mean_volume(rows: Sequence[dict], i: int, window: int) -> Optional[float]:
    """Mean volume over the `window` bars ending at `i` inclusive.

    Ending at `i` inclusive, where `i` is the *signal* bar, keeps the measure
    strictly causal: bar `i` has closed by the time the signal is raised
    [repo-verified: futures_agents/backtest/engine.py:304-316, signals are read
    from `snapshot(i)` after bar `i` is complete].
    """
    if i + 1 < window:
        return None
    seg = rows[i + 1 - window:i + 1]
    return sum(r["volume"] for r in seg) / float(window)


# --------------------------------------------------------------------------
# The join
# --------------------------------------------------------------------------
def join(trades_path: str = TRADES, *, window: int = ATR_PERIOD
         ) -> Tuple[List[dict], Dict[Tuple[str, int, str], List[dict]], dict]:
    """Attach activity to every stored trade. Returns (joined, bars, coverage).

    A trade joins when its `ts` is a bar in its own cell **and** that bar is not
    the cell's first (a signal bar must exist one timeframe earlier). Anything
    that fails either test is counted, not dropped silently: an unreported join
    loss is a survivorship filter on the strata.
    """
    with open(os.path.join(REPO, trades_path)) as fh:
        dump = json.load(fh)

    cells = build_cells()
    bars = {k: bar_table(v) for k, v in cells.items()}
    index = {k: {datetime.fromisoformat(r["ts"]): r["i"] for r in v}
             for k, v in bars.items()}

    cov = dict(trades=len(dump), joined=0, no_such_cell=0, ts_not_a_bar=0,
               entry_is_first_bar=0, signal_relvol_none=0, signal_atr_none=0,
               signal_vol_zero=0, entry_vol_zero=0)
    out = []
    for t in dump:
        key = (t["symbol"], t["tf"], t["slice"])
        if key not in index:
            cov["no_such_cell"] += 1
            continue
        ei = index[key].get(datetime.fromisoformat(t["ts"]))
        if ei is None:
            cov["ts_not_a_bar"] += 1
            continue
        if ei == 0:
            cov["entry_is_first_bar"] += 1
            continue
        rows = bars[key]
        sig, ent = rows[ei - 1], rows[ei]
        cov["joined"] += 1
        if sig["rel_volume"] is None:
            cov["signal_relvol_none"] += 1
        if sig["atr"] is None:
            cov["signal_atr_none"] += 1
        if sig["volume"] == 0:
            cov["signal_vol_zero"] += 1
        if ent["volume"] == 0:
            cov["entry_vol_zero"] += 1
        rec = dict(t)
        rec["strategy"] = "|".join([t["symbol"], str(t["tf"]), t["arm"], t["exitm"]])
        rec["cell"] = "_".join([t["symbol"], str(t["tf"]), t["slice"]])
        rec["sig_i"] = ei - 1
        rec["sig_vol"] = sig["volume"]
        rec["sig_relvol"] = sig["rel_volume"]
        rec["sig_bucket"] = sig["bucket"]
        rec["sig_session"] = sig["session"]
        rec["sig_day"] = sig["day"]
        rec["sig_atr"] = sig["atr"]
        rec["sig_atr_over_close"] = sig["atr_over_close"]
        rec["sig_bb_width"] = sig["bb_width"]
        rec["sig_kc_width"] = sig["kc_width"]
        rec["sig_clv"] = sig["clv"]
        rec["sig_win_vol"] = trailing_mean_volume(rows, ei - 1, window)
        rec["entry_vol"] = ent["volume"]
        rec["entry_bucket"] = ent["bucket"]
        out.append(rec)
    return out, bars, cov


# --------------------------------------------------------------------------
if __name__ == "__main__":
    joined, bars, cov = join()
    print(json.dumps(cov, indent=1))
    print("cells", len(bars), "bars", sum(len(v) for v in bars.values()))
    print("strategies", len(set(r["strategy"] for r in joined)))
