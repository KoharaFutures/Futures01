"""EF3 burst 03 - operating-layer collapse census: how many distinct stop
mechanisms actually exist on MES/MNQ at 60m and 240m.

Checks, per (symbol, timeframe), on every base bar and both directions:
  D49  StopKind.RANGE  vs StopKind.ATR   at matched stop_mult -> identical?
  D45  StopKind.VWAP_BAND -> does the min_stop_ticks floor bind (i.e. is it
       FIXED_TICKS in disguise)?
  STRUCTURE availability (stop = None means the trade is simply not taken).
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "/home/user/Futures01")
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.features import build_symbol_frame
from futures_agents.schema import Direction
from futures_agents.strategies.base import ExitModel, StopKind

OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF3/out")
TFS = (60, 240)

# the exact geometries in the shipped catalogue that use each kind
E_ATR10 = ExitModel(StopKind.ATR, 1.0)
E_RANGE10 = ExitModel(StopKind.RANGE, 1.0, targets_r=(1.0, 2.0, 3.5))
E_VWAP = ExitModel(StopKind.VWAP_BAND, 1.0, stop_pad_ticks=3, targets_r=(1.0, 2.0))
E_STRUCT = ExitModel(StopKind.STRUCTURE, 1.0, stop_pad_ticks=4)


def run(sym: str) -> dict:
    arch = BarArchive("/home/user/Futures01/data/archive")
    base = arch.load(sym, 60)
    spec = get_contract(sym)
    frame = build_symbol_frame(base, list(TFS), spec)
    min_dist = spec.min_stop_ticks * spec.tick_size
    c = Counter()
    out = {"symbol": sym, "min_stop_ticks": spec.min_stop_ticks,
           "tick_size": spec.tick_size, "min_stop_dist": min_dist,
           "bars": len(base.bars)}
    for i in range(len(base.bars)):
        snap = frame.snapshot(i)
        if snap is None:
            continue
        entry = spec.round_to_tick(snap.price)
        for tf in TFS:
            s = snap.tf(tf)
            if s is None:
                continue
            c[f"eval_tf{tf}"] += 1
            for d in (Direction.LONG, Direction.SHORT):
                a = E_ATR10.stop_price(snap, tf, d, entry, spec)
                r = E_RANGE10.stop_price(snap, tf, d, entry, spec)
                v = E_VWAP.stop_price(snap, tf, d, entry, spec)
                st = E_STRUCT.stop_price(snap, tf, d, entry, spec)
                k = f"tf{tf}"
                c[f"{k}_n"] += 1
                if a is None:
                    c[f"{k}_atr_none"] += 1
                if r is None:
                    c[f"{k}_range_none"] += 1
                if a is not None and r is not None:
                    if abs(a - r) < 1e-12:
                        c[f"{k}_range_eq_atr"] += 1
                if st is None:
                    c[f"{k}_struct_none"] += 1
                if v is None:
                    c[f"{k}_vwap_none"] += 1
                else:
                    dist = abs(entry - v)
                    if abs(dist - min_dist) < 1e-9:
                        c[f"{k}_vwap_at_floor"] += 1
                    # what the raw (pre-floor) distance was
                    band = s["vwap_l1"] if d.sign > 0 else s["vwap_u1"]
                    if band is not None:
                        raw = abs(entry - band) * 1.0 + E_VWAP.stop_pad_ticks * spec.tick_size
                        if raw <= min_dist + 1e-12:
                            c[f"{k}_vwap_raw_below_floor"] += 1
    out["counts"] = dict(c)
    for tf in TFS:
        n = c[f"tf{tf}_n"] or 1
        out[f"tf{tf}_RANGE_identical_to_ATR_pct"] = round(100.0 * c[f"tf{tf}_range_eq_atr"] / n, 3)
        out[f"tf{tf}_VWAPBAND_on_floor_pct"] = round(100.0 * c[f"tf{tf}_vwap_at_floor"] / n, 3)
        out[f"tf{tf}_STRUCTURE_unplaceable_pct"] = round(100.0 * c[f"tf{tf}_struct_none"] / n, 3)
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    res = {}
    for sym in sys.argv[1:] or ["MES", "MNQ"]:
        res[sym] = run(sym)
        print(json.dumps(res[sym], indent=1))
    (OUT / "stopcensus.json").write_text(json.dumps(res, indent=1))
