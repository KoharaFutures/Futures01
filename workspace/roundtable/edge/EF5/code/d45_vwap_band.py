"""EF5 burst 03 -- D45 re-measured for the SCALP cell (MES/MNQ at 5m/15m/30m).

D45: ``StopKind.VWAP_BAND`` silently becomes ``StopKind.FIXED_TICKS`` whenever
``|entry - band| * stop_mult + pad`` lands under ``min_stop_ticks * tick_size``
(``base.py:296-300`` then ``:314-316``). R1 measured 6.0% (MNQ) / 16.6% (MES) of
bars at 1h. D45 is explicitly per-symbol AND R1 stated the 1h rate does not
transfer, so it has to be re-measured here.

Two rates are reported and they answer different questions:
  ALL-BAR rate   -- comparable with R1's 1h table.
  IN-GATE rate   -- restricted to the bars a strategy could actually enter on,
                    which is the rate that reaches a published row.

The catalogue's only VWAP_BAND geometry is
``ExitModel(StopKind.VWAP_BAND, 1.0, stop_pad_ticks=3, ...)``
(``combinator.py:70-72``), so stop_mult = 1.0 and pad = 3 ticks throughout.
Entry is approximated by the signal bar's close, exactly as R1 did; real entries
are next-bar opens, so the figure is indicative for level and exact for the
zero-sigma-at-anchor mechanism.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from ef5_data import PRIMARY_TFS, REPO, SYMBOLS, build_frame, in_session  # noqa: E402
from futures_agents.config import get_contract                            # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")
STOP_MULT = 1.0
PAD_TICKS = 3


def main() -> None:
    res = {}
    for sym in SYMBOLS:
        spec = get_contract(sym)
        pad = PAD_TICKS * spec.tick_size
        floor = spec.min_stop_ticks * spec.tick_size
        for tf in PRIMARY_TFS:
            frame = build_frame(sym, tf)
            tot = {"ALL": 0, "SESSION": 0, "RTH": 0}
            collapse = {"ALL": 0, "SESSION": 0, "RTH": 0}
            band_none = {"ALL": 0, "SESSION": 0, "RTH": 0}
            for i in range(len(frame.base)):
                snap = frame.snapshot(i)
                if snap is None:
                    continue
                s = snap.tf(tf)
                if s is None:
                    continue
                ts = frame.base.bars[i].ts
                gates = ["ALL"]
                if in_session(ts):
                    gates.append("SESSION")
                if snap.is_rth:
                    gates.append("RTH")
                lo, up, c = s["vwap_l1"], s["vwap_u1"], s.close
                for g in gates:
                    tot[g] += 1
                if lo is None or up is None:
                    for g in gates:
                        band_none[g] += 1
                    continue
                # Long uses the lower band, short the upper. A bar collapses if
                # EITHER direction would fall through the floor; report the
                # long/short mean so the figure is direction-neutral.
                d_long = abs(c - lo) * STOP_MULT + pad
                d_short = abs(c - up) * STOP_MULT + pad
                hit = (1 if d_long < floor else 0) + (1 if d_short < floor else 0)
                for g in gates:
                    collapse[g] += hit / 2.0
            row = {
                "tick": spec.tick_size, "min_stop_ticks": spec.min_stop_ticks,
                "floor_points": floor, "pad_points": pad,
                "bars": tot, "band_none": band_none,
                "collapse_frac": {g: (round(collapse[g] / tot[g], 4) if tot[g] else None)
                                  for g in tot},
            }
            res[f"{sym}_{tf}m"] = row
            print(f"{sym} {tf}m floor={floor}pt pad={pad}pt  "
                  f"collapse ALL={row['collapse_frac']['ALL']:.3%} "
                  f"SESSION={row['collapse_frac']['SESSION']:.3%} "
                  f"RTH={row['collapse_frac']['RTH']:.3%}  "
                  f"band_none ALL={band_none['ALL']}", flush=True)
    with open(os.path.join(OUT, "d45_vwap_band.json"), "w") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
