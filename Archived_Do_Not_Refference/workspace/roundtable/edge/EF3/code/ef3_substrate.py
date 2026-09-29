"""EF3 burst 01 - substrate verification for MES/MNQ at 60m and 240m.

Checks, in order:
  1. archive 60m vs csv/raw 60m, UTC-normalised, with a TOLERANCE not ==.
  2. resample(archive 60m -> 240m) vs archive 240m, same way.
  3. bar-grid facts the 18:00->16:00 rule depends on.
"""
from __future__ import annotations
import csv, sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/home/user/Futures01")
from futures_agents.data.archive import BarArchive
from futures_agents.data.bars import resample
from futures_agents.timeutil import to_et

ROOT = Path("/home/user/Futures01")
TOL = 1e-6


def load_csv_raw(sym: str, label: str):
    p = ROOT / "csv" / "raw" / f"{sym}_{label}.csv"
    out = {}
    with p.open() as fh:
        for row in csv.DictReader(fh):
            ts = datetime.fromisoformat(row["open_time"]).astimezone(timezone.utc)
            out[ts] = (float(row["open"]), float(row["high"]),
                       float(row["low"]), float(row["close"]), float(row["volume"]))
    return out


def compare(a: dict, b: dict, name: str):
    common = sorted(set(a) & set(b))
    exact = 0
    worst = 0.0
    volmis = 0
    for ts in common:
        ca, cb = a[ts][3], b[ts][3]
        if ca == cb:
            exact += 1
        worst = max(worst, abs(ca - cb))
        if a[ts][4] != b[ts][4]:
            volmis += 1
    print(f"  {name}: overlap {len(common)}  bit-exact closes {exact}/{len(common)}"
          f"  max|dclose| {worst:.3e}  volume mismatches {volmis}"
          f"  -> {'AGREE (tol 1e-6)' if worst < TOL else 'DISAGREE'}")
    return worst


def main():
    arch = BarArchive(str(ROOT / "data" / "archive"))
    for sym in ("MES", "MNQ"):
        print(f"== {sym} ==")
        s60 = arch.load(sym, 60)
        s240 = arch.load(sym, 240)
        a60 = {b.ts.astimezone(timezone.utc):
               (b.open, b.high, b.low, b.close, b.volume) for b in s60.bars}
        c60 = load_csv_raw(sym, "1h")
        compare(a60, c60, "archive 60m vs csv/raw 1h")

        r240 = resample(s60, 240, keep_partial=False)
        ar240 = {b.ts.astimezone(timezone.utc):
                 (b.open, b.high, b.low, b.close, b.volume) for b in s240.bars}
        rr240 = {b.ts.astimezone(timezone.utc):
                 (b.open, b.high, b.low, b.close, b.volume) for b in r240.bars}
        print(f"  archive 240m bars {len(ar240)}   resample(60m->240m) bars {len(rr240)}"
              f"   stamp sets identical: {set(ar240) == set(rr240)}")
        compare(rr240, ar240, "resample(60m) vs archive 240m")

        # --- grid facts the session rule depends on
        et = [to_et(b.ts) for b in s60.bars]
        print("  60m minute histogram:", sorted(Counter(t.minute for t in et).items()))
        half = [t for t in et if t.minute == 30]
        print(f"  60m bars off the :00 grid: {len(half)}"
              f"  hours {sorted(Counter(t.hour for t in half).items())}")
        print(f"  60m bars stamped 16:00-17:59 ET (inside the flat window): "
              f"{sum(1 for t in et if 16 <= t.hour < 18)}")
        print(f"  60m bars stamped 17:00-17:59 ET: {sum(1 for t in et if t.hour == 17)}")
        et240 = [to_et(b.ts) for b in s240.bars]
        print("  240m hour histogram:", sorted(Counter(t.hour for t in et240).items()))
        print(f"  240m buckets whose span [ts, ts+4h) straddles 16:00 ET: "
              f"{sum(1 for t in et240 if t.hour == 16 or (t.hour < 16 < t.hour + 4))}")
        d = (s60.bars[-1].ts - s60.bars[0].ts).total_seconds() / 86400
        print(f"  span {d:.1f} calendar days = {d/365.25:.3f} yr, sqrt = {(d/365.25)**0.5:.3f}")


if __name__ == "__main__":
    main()
