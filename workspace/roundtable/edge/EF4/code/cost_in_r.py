"""EF4 / burst 02 - cost as a fraction of R, measured per cell, gross vs net.

Why this runs before any strategy. The programme's rule 8 says costs always; the
scalp brief says costs may be the dominant term. Neither is a number. This is the
number, and it is knowable from the contract spec and the measured ATR alone -
no backtest, nothing to overfit.

Two things here that the engine does and a naive cost table does not:

* ``BacktestEngine`` charges slippage into the FILL PRICE (engine.py:352, :414)
  and commission as dollars in ``_close`` (engine.py:494-499). So the engine's own
  ``gross_r`` is *already net of slippage* and only ``commission`` is subtracted to
  reach ``net_r``. A row reported as "gross" straight off ``Trade.gross_r`` therefore
  understates the true gross by the slippage term. Every gross figure EF4 reports is
  reconstructed, not taken from ``gross_r``.
* ``SlippageModel.thin_book_extra_ticks = 1.0`` fires whenever the bar is outside the
  contract's own RTH (engine.py:351, :411 -> ``is_rth``). The 18:00->16:00 rule this
  programme is built on puts the MAJORITY of every cell's bars outside RTH, so the
  thin-book penalty is the normal case here, not an edge case. MGC RTH is 08:20-13:30
  and MCL 09:00-14:30 - 310 and 330 minutes out of a 1320-minute cycle.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import median

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))

from futures_agents.config import get_contract          # noqa: E402
from futures_agents.backtest.costs import CostModel, SlippageModel  # noqa: E402
from futures_agents.timeutil import is_rth              # noqa: E402

CELLS = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]


def load(symbol: str, minutes: int):
    p = ROOT / "data" / "archive" / f"{symbol}_{minutes}m.jsonl"
    bars = []
    for line in p.read_text().splitlines():
        if line.strip():
            d = json.loads(line)
            bars.append((datetime.fromisoformat(d["ts"]), d["o"], d["h"], d["l"], d["c"]))
    bars.sort(key=lambda b: b[0])
    return bars


def wilder_atr(bars, period: int = 14):
    trs = []
    for k in range(1, len(bars)):
        _, o, h, l, c = bars[k]
        pc = bars[k - 1][4]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    out = []
    a = None
    for k, tr in enumerate(trs):
        if k < period - 1:
            out.append(None); continue
        if a is None:
            a = sum(trs[:period]) / period
        else:
            a = (a * (period - 1) + tr) / period
        out.append(a)
    return out


def main() -> None:
    rows = []
    for sym, tf in CELLS:
        spec = get_contract(sym)
        cm = CostModel(spec)
        bars = load(sym, tf)
        atrs = [a for a in wilder_atr(bars) if a is not None]
        med_atr = median(atrs)
        rth_flags = [is_rth(b[0], spec.rth_open, spec.rth_close) for b in bars]
        rth_share = sum(rth_flags) / len(rth_flags)
        tick_value = spec.tick_size * spec.point_value
        comm_rt = 2.0 * cm.commission_per_side()

        for mult in (0.5, 1.0, 1.5):
            risk_points = mult * med_atr
            risk_dollars = risk_points * spec.point_value
            for thin in (False, True):
                # commission only (what net_r - gross_r measures in the engine)
                comm_r = comm_rt / risk_dollars
                slip_entry = cm.slippage_dollars(is_stop=False, thin=thin)
                slip_stop = cm.slippage_dollars(is_stop=True, thin=thin)
                slip_lim = cm.slippage_dollars(is_stop=False, thin=thin)
                # exit on a stop is the pessimistic, dominant case
                all_in_stop = (comm_rt + slip_entry + slip_stop) / risk_dollars
                all_in_tgt = (comm_rt + slip_entry + slip_lim) / risk_dollars
                rows.append({
                    "symbol": sym, "tf": tf, "atr_median_points": round(med_atr, 4),
                    "stop_atr_mult": mult, "risk_points": round(risk_points, 4),
                    "risk_dollars": round(risk_dollars, 2),
                    "thin_book": thin,
                    "rth_share_of_bars": round(rth_share, 4),
                    "min_stop_ticks": spec.min_stop_ticks,
                    "min_stop_dollars": round(spec.min_stop_ticks * tick_value, 2),
                    "commission_only_R": round(comm_r, 4),
                    "all_in_R_stop_exit": round(all_in_stop, 4),
                    "all_in_R_target_exit": round(all_in_tgt, 4),
                })

    hdr = (f"{'cell':<9}{'medATR':>9}{'x':>5}{'riskPts':>9}{'risk$':>8}{'thin':>6}"
           f"{'comm_R':>9}{'allin_R(stop)':>15}{'allin_R(tgt)':>14}")
    print(hdr)
    for r in rows:
        print(f"{r['symbol']+' '+str(r['tf'])+'m':<9}{r['atr_median_points']:>9.4f}"
              f"{r['stop_atr_mult']:>5.1f}{r['risk_points']:>9.4f}{r['risk_dollars']:>8.2f}"
              f"{str(r['thin_book']):>6}{r['commission_only_R']:>9.4f}"
              f"{r['all_in_R_stop_exit']:>15.4f}{r['all_in_R_target_exit']:>14.4f}")

    print()
    for sym, tf in CELLS:
        rr = [r for r in rows if r["symbol"] == sym and r["tf"] == tf][0]
        print(f"{sym} {tf}m: RTH share of bars = {rr['rth_share_of_bars']:.1%}  "
              f"-> thin-book slippage applies to {1-rr['rth_share_of_bars']:.1%} of bars")

    out = ROOT / "workspace/roundtable/edge/EF4/out/cost_in_r.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
