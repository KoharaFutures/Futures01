"""Run the firing census over every cell this programme can trade.

Usage:  python3 run_census.py <out_dir> [cellspec ...]
        cellspec = SYMBOL:BASE_TF:TF,TF,TF        e.g.  MGC:5:5,15,60
        no cellspec -> the default grid below.

Substrate: ``data/archive/`` (append-only, the programme's substrate per
`BRIEF.md` "Data policy"). Every output document records the substrate, the
first and last timestamp and the bar counts, so no number is quotable without
its span.
"""

from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from futures_agents.data.archive import BarArchive          # noqa: E402
from futures_agents.features import build_symbol_frame      # noqa: E402

import firing                                              # noqa: E402
import window as W                                          # noqa: E402

SYMBOLS = ["MGC", "MCL", "MES", "MNQ"]

#: (base_tf, frame timeframes). The base timeframe is where the engine steps,
#: so it is the one that must tile the 22-hour window: 1320 minutes has
#: divisors 1,5,15,30,60,120 among our grid and **NOT 240 or 1440**. Higher
#: timeframes appear as *reading* timeframes only, which is legal - the position
#: still opens and closes on the base grid.
GRID = [
    # scalp substrate, 57.90 days
    (5,  [5, 15, 60]),
    (5,  [5]),                       # frame-of-one: R4-MT1's VOID configuration
    (15, [15, 60, 240]),
    (15, [15]),
    (30, [30, 60, 240]),
    (30, [30]),
    # swing substrate, 718.88 days
    (60, [60, 240, 1440]),
    (60, [60]),
    (60, [60, 120]),                 # the expressible 4h alternative
]


def load_base(arch: BarArchive, symbol: str, tf: int):
    """Base series for a cell. 120m is resampled from the 60m archive."""
    if tf == 120:
        return arch.load(symbol, 60).resample(120, keep_partial=False)
    return arch.load(symbol, tf)


def main() -> int:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "workspace/roundtable/edge/EF6/out/census"
    specs = []
    for a in sys.argv[2:]:
        sym, base, tfs = a.split(":")
        specs.append((sym, int(base), [int(x) for x in tfs.split(",")]))
    if not specs:
        specs = [(s, b, tfs) for s in SYMBOLS for b, tfs in GRID]

    os.makedirs(out_dir, exist_ok=True)
    arch = BarArchive("data/archive")
    index = []
    for sym, base, tfs in specs:
        tag = f"{sym}_{base}m_frame{'-'.join(str(t) for t in tfs)}"
        path = os.path.join(out_dir, f"census_{tag}.json")
        if os.path.exists(path):
            print(f"skip {tag} (exists)", flush=True)
            index.append({"cell": tag, "path": path, "cached": True})
            continue
        t0 = time.time()
        series = load_base(arch, sym, base)
        if len(series.bars) < 50:
            print(f"SKIP {tag}: only {len(series.bars)} bars", flush=True)
            continue
        frame = build_symbol_frame(series, tfs)
        doc = firing.census(frame, timeframes=tfs)
        doc["substrate"] = "data/archive"
        doc["cell"] = tag
        doc["frame_requested"] = tfs
        doc["base_expressible"] = (1320 % base == 0)
        with open(path, "w") as fh:
            json.dump(doc, fh, indent=1, default=str)
        el = time.time() - t0
        nz = sum(1 for v in doc["fires"].values() if v["signal"] == 0)
        print(f"{tag}: {doc['bars']['evaluated']} bars, "
              f"{nz}/{len(doc['fires'])} (cond,tf) pairs VOID on the signal "
              f"denominator, {el:.0f}s", flush=True)
        index.append({"cell": tag, "path": path, "bars": doc["bars"],
                      "void_pairs": nz, "pairs": len(doc["fires"]),
                      "base_expressible": doc["base_expressible"],
                      "straddle": doc["straddle"]["straddle"],
                      "seconds": round(el, 1)})
    with open(os.path.join(out_dir, "index.json"), "w") as fh:
        json.dump(index, fh, indent=1, default=str)
    print("index written", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
