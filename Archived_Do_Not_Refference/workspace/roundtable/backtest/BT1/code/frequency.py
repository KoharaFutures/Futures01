"""How often does the ALGO-1 shape actually occur? Run: python3 code/frequency.py

This is a **frequency census of the signal layer**, not a measurement of the
algorithm. No exit model, no fill, no cost, no expectancy, no R is computed
anywhere in this file, and none will be until R1 rules on fidelity
(PIPELINE §4: never report a number from an UNVERIFIED algorithm).

It exists for one reason. A signal that fires on 0.2% of bars cannot reach the
20-trade floor on a 5,000-bar series, and that is a fact about whether the
researched thresholds are *measurable here* - which R1 has to know before it
can answer whether taking them literally is faithful. Counting bars is how you
find that out without touching a P&L.

The variant columns are listed so the ruling can be made against numbers
instead of guesses. They are **not** arms I have measured and not a search: the
search size of anything I eventually run is stated in ALGOS.md and is 1 until
R1 answers.
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "..", "..", "..", ".."))
sys.path.insert(0, _ROOT)

import absorption as A                                     # noqa: E402
from futures_agents.data.loader import load_csv             # noqa: E402
from futures_agents.indicators.structure import detect_imbalances  # noqa: E402
from futures_agents.timeutil import to_et                   # noqa: E402

#: The two genuinely independent contracts (BRIEF: contract independence).
#: MES/MNQ/NQ/ES are one index complex and agreement between them is not
#: corroboration, so they are not counted here.
FILES = [("MGC", "1h", 60), ("MGC", "15m", 15), ("MGC", "5m", 5),
         ("MCL", "1h", 60), ("MCL", "15m", 15), ("MCL", "5m", 5)]


def tod_volume_mult(bars: Sequence, lookback_days: int = 20) -> List[Optional[float]]:
    """Volume over the same clock minute's mean on prior sessions.

    The library's other volume norm: this is ``relative_volume``'s arithmetic
    `[repo-verified: futures_agents/indicators/volume.py:266-285]`, strictly
    trailing (the current bar is appended to the history only after it is
    read). Reproduced here rather than imported so the count below is of *this*
    file's arithmetic and can be checked against the library's column.
    """
    out: List[Optional[float]] = [None] * len(bars)
    hist: Dict[tuple, List[float]] = defaultdict(list)
    for i, b in enumerate(bars):
        d = to_et(b.ts)
        key = (d.hour, d.minute)
        prior = hist[key]
        if prior:
            avg = sum(prior) / len(prior)
            out[i] = (b.volume / avg) if avg > 0 else None
        prior.append(b.volume)
        if len(prior) > lookback_days:
            prior.pop(0)
    return out


def census() -> None:
    print(f"{'cell':<12} {'bars':>6} {'zero-rng':>9} {'ALGO-1':>8} {'rate':>7} "
          f"{'+dir':>6} {'displ':>7} {'v>=1.5':>7} {'r<=0.8':>7} {'tod-v':>7}")
    print("-" * 92)
    for sym, suf, tf in FILES:
        bars = list(load_csv(os.path.join(_ROOT, f"csv/raw/{sym}_{suf}.csv"),
                             sym, tf).bars)
        col = A.absorption_series(bars)
        tod = tod_volume_mult(bars)
        live = [(i, a) for i, a in enumerate(col) if a is not None]

        n_zero = sum(1 for _i, a in live if a.bar_range <= 0)
        fired = [(i, a) for i, a in live if a.fires()]
        with_dir = [1 for _i, a in fired if a.direction() is not None]
        displ = len(detect_imbalances(bars))

        # Variant counts. Same gate, one input changed at a time.
        v15 = sum(1 for _i, a in live if a.fires(vol_mult=1.5))
        r08 = sum(1 for _i, a in live if a.fires(range_mult=0.8))
        tod_fire = sum(1 for i, a in live
                       if tod[i] is not None and tod[i] >= A.VOL_MULT
                       and a.r_mult <= A.RANGE_MULT)

        print(f"{sym + ' ' + suf:<12} {len(bars):>6} {n_zero:>9} {len(fired):>8} "
              f"{len(fired) / max(1, len(live)) * 100:>6.2f}% {sum(with_dir):>6} "
              f"{displ:>7} {v15:>7} {r08:>7} {tod_fire:>7}")

    print("\ncolumns")
    print("  zero-rng  bars with high == low among the non-warm-up bars")
    print(f"  ALGO-1    v_mult >= {A.VOL_MULT} and r_mult <= {A.RANGE_MULT}, "
          f"{A.WINDOW}-bar trailing means, R1 §7 Q2 item 1 taken literally")
    print("  rate      ALGO-1 as a share of non-warm-up bars")
    print("  +dir      of those, how many have a direction (close not at the midpoint)")
    print("  displ     detect_imbalances on the same bars, for scale: the shape "
          "this one inverts")
    print("  v>=1.5    ALGO-1 with the volume threshold at 1.5x instead of 2.0x")
    print("  r<=0.8    ALGO-1 with the range threshold at 0.8x instead of 1.0x")
    print("  tod-v     ALGO-1 with volume normalised by the same clock minute on "
          "prior sessions\n            (relative_volume's arithmetic) instead of a "
          "20-bar trailing mean")
    print("\nNo expectancy, win rate, R or trade count is computed in this file.")


def coupling() -> None:
    """Why the rate is what it is: volume and range are coupled at bar level.

    "High volume, LOW range" is rare here not because absorption is rare in the
    market but because a bar that takes 2x its normal volume almost always
    *moves*. This prints the conditional distribution of ``r_mult`` given
    ``v_mult >= 2``, which is the honest form of that statement and a data
    property rather than a property of the algorithm.
    """
    print(f"\n{'cell':<12} {'corr(v,r)':>10} {'n v>=2':>8} "
          f"{'r|v>=2: p10':>12} {'p50':>7} {'p90':>7} {'P(r<=1|v>=2)':>14}")
    print("-" * 78)
    for sym, suf, tf in FILES:
        bars = list(load_csv(os.path.join(_ROOT, f"csv/raw/{sym}_{suf}.csv"),
                             sym, tf).bars)
        live = [a for a in A.absorption_series(bars) if a is not None]
        v = [a.v_mult for a in live]
        r = [a.r_mult for a in live]
        mv, mr = sum(v) / len(v), sum(r) / len(r)
        num = sum((x - mv) * (y - mr) for x, y in zip(v, r))
        den = ((sum((x - mv) ** 2 for x in v) * sum((y - mr) ** 2 for y in r)) ** 0.5)
        c = num / den if den else 0.0
        hi = sorted(a.r_mult for a in live if a.v_mult >= A.VOL_MULT)
        if not hi:
            continue
        def q(p):
            return hi[min(len(hi) - 1, int(p * len(hi)))]
        share = sum(1 for x in hi if x <= A.RANGE_MULT) / len(hi)
        print(f"{sym + ' ' + suf:<12} {c:>10.3f} {len(hi):>8} {q(0.10):>12.2f} "
              f"{q(0.50):>7.2f} {q(0.90):>7.2f} {share * 100:>13.2f}%")
    print("\ncorr(v,r) is Pearson over every non-warm-up bar of the cell.")


if __name__ == "__main__":
    census()
    coupling()
