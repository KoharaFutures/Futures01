"""Tests for ALGO-1 (``absorption.py``). Run: python3 code/test_absorption.py

These are engineering checks, not results. They answer "does this compute what
the module says, causally, and is it wired into the condition layer at all" -
the last one because D38 turns an unwired custom condition into a silent zero
`[repo-verified: workspace/studies/DEFECTS.md:549-556]`, and a null from an
unwired condition is not a null, it is nothing.

No expectancy, win rate, R or trade count is computed anywhere in this file.
ALGO-1 is UNVERIFIED until R1 answers, and a number from an unverified
algorithm is an unknown quantity (PIPELINE §4).
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", "..", "..", "..", ".."))
sys.path.insert(0, _ROOT)

import absorption as A                                     # noqa: E402
from futures_agents.data.bars import Bar, BarSeries         # noqa: E402
from futures_agents.data.loader import load_csv             # noqa: E402
from futures_agents.features import build_symbol_frame      # noqa: E402
from futures_agents.indicators.structure import detect_imbalances  # noqa: E402
from futures_agents.schema import Direction                 # noqa: E402
from futures_agents.scout import FRAMES                     # noqa: E402
from futures_agents.strategies.library import get_condition  # noqa: E402

FAILED: list = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}{(' - ' + detail) if detail else ''}")
    if not ok:
        FAILED.append(name)


def synth(rows, minutes=60):
    """``rows`` of (open, high, low, close, volume) into a bar list."""
    t0 = datetime(2025, 1, 2, 9, 0)
    return [Bar(t0 + timedelta(minutes=minutes * i), o, h, l, c, v, minutes)
            for i, (o, h, l, c, v) in enumerate(rows)]


def flat(n, rng=1.0, vol=100.0):
    """``n`` identical bars: range ``rng``, volume ``vol``, close at mid."""
    return [(100.0, 100.0 + rng, 100.0, 100.0 + rng / 2.0, vol)] * n


# --------------------------------------------------------------------------
print("\n1. Shape of the column, and warm-up")
# --------------------------------------------------------------------------
bars = synth(flat(30))
col = A.absorption_series(bars)
check("length equals input", len(col) == len(bars), f"{len(col)} == {len(bars)}")
check("first WINDOW positions are None",
      all(c is None for c in col[:A.WINDOW]), f"WINDOW={A.WINDOW}")
check("position WINDOW is populated", col[A.WINDOW] is not None)
short = A.absorption_series(synth(flat(A.WINDOW)))
check("series shorter than the window is all None",
      len(short) == A.WINDOW and all(c is None for c in short))
check("empty input returns empty", A.absorption_series([]) == [])

# --------------------------------------------------------------------------
print("\n2. The gate fires on the researched shape and not on its inverse")
# --------------------------------------------------------------------------
# 20 bars of range 1.0 / volume 100, then one bar to test.
def one(o, h, l, c, v):
    return A.absorption_series(synth(flat(A.WINDOW) + [(o, h, l, c, v)]))[A.WINDOW]

a = one(100.0, 100.5, 100.0, 100.4, 300.0)       # vol 3x, range 0.5x
check("high volume + low range fires", a.fires(),
      f"v={a.v_mult:.2f}x r={a.r_mult:.2f}x")
d = one(100.0, 103.0, 100.0, 102.9, 300.0)       # vol 3x, range 3x
check("displacement bar (high vol + HIGH range) does not fire", not d.fires(),
      f"v={d.v_mult:.2f}x r={d.r_mult:.2f}x")
q = one(100.0, 100.5, 100.0, 100.4, 50.0)        # vol 0.5x, range 0.5x
check("quiet narrow bar does not fire", not q.fires(),
      f"v={q.v_mult:.2f}x r={q.r_mult:.2f}x")
e = one(100.0, 101.0, 100.0, 100.9, 200.0)       # vol exactly 2x, range exactly 1x
check("boundary is inclusive on both sides (v>=2.0, r<=1.0)", e.fires(),
      f"v={e.v_mult:.2f}x r={e.r_mult:.2f}x")
u = one(100.0, 101.01, 100.0, 100.9, 199.0)      # just inside both
check("just under either threshold does not fire", not u.fires(),
      f"v={u.v_mult:.3f}x r={u.r_mult:.3f}x")

# --------------------------------------------------------------------------
print("\n3. Direction, ties and the zero-range corner")
# --------------------------------------------------------------------------
up = one(100.0, 100.5, 100.0, 100.45, 300.0)     # close high in the bar
check("close in upper half -> LONG", up.direction() is Direction.LONG,
      f"close_pos={up.close_pos:.2f}")
dn = one(100.0, 100.5, 100.0, 100.05, 300.0)     # close low in the bar
check("close in lower half -> SHORT", dn.direction() is Direction.SHORT,
      f"close_pos={dn.close_pos:.2f}")
mid = one(100.0, 100.5, 100.0, 100.25, 300.0)    # close exactly at the midpoint
check("close exactly at the midpoint -> no direction",
      mid.direction() is None, f"close_pos={mid.close_pos:.2f}")
z = one(100.0, 100.0, 100.0, 100.0, 300.0)       # zero range, heavy volume
check("zero-range bar fires the shape gate", z.fires(),
      f"v={z.v_mult:.2f}x r={z.r_mult:.2f}x")
check("zero-range bar has no close position", z.close_pos is None)
check("zero-range bar has no direction", z.direction() is None)
check("Bar.delta returns 0.0 on that bar (bars.py:110-111, R1's point)",
      synth([(100.0, 100.0, 100.0, 100.0, 300.0)])[0].delta == 0.0)
check("ratio is None when r_mult is 0 rather than dividing by zero",
      z.ratio is None)
check("ratio is v/r otherwise",
      abs(a.ratio - a.v_mult / a.r_mult) < 1e-12)

# --------------------------------------------------------------------------
print("\n4. Degenerate windows return None, not a division by zero")
# --------------------------------------------------------------------------
zero_vol = A.absorption_series(synth(flat(A.WINDOW, vol=0.0) + [(100.0, 100.5, 100.0, 100.4, 300.0)]))
check("prior window with zero volume -> None", zero_vol[A.WINDOW] is None)
zero_rng = A.absorption_series(synth([(100.0, 100.0, 100.0, 100.0, 100.0)] * A.WINDOW
                                     + [(100.0, 100.5, 100.0, 100.4, 300.0)]))
check("prior window with zero range -> None", zero_rng[A.WINDOW] is None)

# --------------------------------------------------------------------------
print("\n5. No look-ahead, on real bars: prefix invariance")
# --------------------------------------------------------------------------
REAL = [("MGC", "csv/raw/MGC_1h.csv", 60), ("MCL", "csv/raw/MCL_15m.csv", 15)]
for sym, path, tf in REAL:
    series = load_csv(os.path.join(_ROOT, path), sym, tf)
    rb = list(series.bars)
    full = A.absorption_series(rb)
    worst = 0.0
    mismatch = 0
    for k in (A.WINDOW + 1, 200, 977, len(rb) // 2, len(rb) - 1):
        if k > len(rb):
            continue
        pref = A.absorption_series(rb[:k])
        for j in range(k):
            x, y = pref[j], full[j]
            if (x is None) != (y is None):
                mismatch += 1
            elif x is not None:
                worst = max(worst, abs(x.v_mult - y.v_mult),
                            abs(x.r_mult - y.r_mult))
    check(f"{sym} {tf}m: prefix column identical to full column",
          mismatch == 0 and worst == 0.0,
          f"{len(rb)} bars, mismatches={mismatch}, max|delta|={worst}")

# --------------------------------------------------------------------------
print("\n6. Determinism, and disjointness from detect_imbalances")
# --------------------------------------------------------------------------
series = load_csv(os.path.join(_ROOT, "csv/raw/MGC_1h.csv"), "MGC", 60)
rb = list(series.bars)
c1 = A.absorption_series(rb)
c2 = A.absorption_series(rb)
check("same bars twice -> identical v_mult/r_mult",
      all((x is None and y is None)
          or (x is not None and y is not None
              and x.v_mult == y.v_mult and x.r_mult == y.r_mult)
          for x, y in zip(c1, c2)))
imb = {i for i, _dirn, _m in detect_imbalances(rb)}
mine = {i for i, x in enumerate(c1) if x is not None and x.fires()}
check("no bar is both a displacement bar and an absorption bar",
      not (imb & mine),
      f"displacement={len(imb)}, absorption={len(mine)}, overlap={len(imb & mine)}")

# --------------------------------------------------------------------------
print("\n7. Wiring: the conditions are registered and actually evaluate (D38)")
# --------------------------------------------------------------------------
check("both conditions are in the library registry",
      all(get_condition(n) is not None for n in A.names()),
      ", ".join(A.names()))

A.clear()
tf = 60
frame = build_symbol_frame(BarSeries("MGC", tf, rb[-1500:]), FRAMES[tf])
counts = A.register_frame(frame)
check("register_frame indexed every timeframe of the frame",
      set(counts) == set(frame.frames), str(counts))

cond_sig = get_condition("absorption_bar")
cond_flt = get_condition("absorption_present")
fired_sig = fired_flt = evaluated = 0
for snap in frame.iter_snapshots():
    if snap is None:
        continue
    evaluated += 1
    if cond_sig.evaluate(snap, tf).triggered:
        fired_sig += 1
    if cond_flt.evaluate(snap, tf).triggered:
        fired_flt += 1
check("no lookup misses - the registered grid is the frame's grid, and a "
      "warm-up bar is not counted as a mismatch",
      not A.MISSES, str(dict(A.MISSES)))
check("warm-up bars are registered with a None value, not left absent",
      A.is_registered("MGC", tf, frame.frames[tf].series.bars[0].ts)
      and A.lookup("MGC", tf, frame.frames[tf].series.bars[0].ts) is None)
check("the SIGNAL condition fires at least once (i.e. it is not D38-zeroed)",
      fired_sig > 0, f"{fired_sig} of {evaluated} bars evaluated")
check("the FILTER condition fires at least as often as the SIGNAL",
      fired_flt >= fired_sig, f"filter={fired_flt}, signal={fired_sig}")

A.clear()
missing = 0
for snap in frame.iter_snapshots():
    if snap is not None and cond_sig.evaluate(snap, tf).triggered:
        missing += 1
check("with registration cleared the condition returns no() AND counts misses "
      "(D38 is detectable here, not silent)",
      missing == 0 and sum(A.MISSES.values()) > 0,
      f"fired={missing}, misses={sum(A.MISSES.values())}")

# --------------------------------------------------------------------------
print("\n8. frequency.py's time-of-day norm really is relative_volume's")
# --------------------------------------------------------------------------
# The verify message quotes a 5-27x population difference between the two
# volume norms, off a reimplementation in frequency.py. If that
# reimplementation is not the library's arithmetic, the number is about my code
# rather than about the library's choice, so it is checked rather than asserted.
from futures_agents.indicators.volume import relative_volume     # noqa: E402

import frequency as F                                            # noqa: E402

lib = relative_volume(rb, 20)
mine = F.tod_volume_mult(rb, 20)
worst = 0.0
disagree = 0
for x, y in zip(lib, mine):
    if (x is None) != (y is None):
        disagree += 1
    elif x is not None:
        worst = max(worst, abs(x - y))
check("tod_volume_mult reproduces relative_volume exactly on MGC 1h",
      disagree == 0 and worst == 0.0,
      f"{len(rb)} bars, None-disagreements={disagree}, max|delta|={worst}")

# --------------------------------------------------------------------------
print("\n" + ("ALL CHECKS PASSED" if not FAILED
              else f"{len(FAILED)} FAILED: " + ", ".join(FAILED)))
sys.exit(1 if FAILED else 0)
