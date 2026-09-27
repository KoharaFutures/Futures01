"""ALGO-1 — the absorption shape: high volume, LOW range.

What this implements
--------------------
R1's §7 Q2 item 1 and R1-D1 I-2. ``detect_imbalances`` fires on a bar whose
**range** is >= 2.0x its trailing norm **and** whose **volume** is >= 1.2x its
trailing norm `[repo-verified: futures_agents/indicators/structure.py:452-462]`
- a displacement bar. R1's point is that the *inverse* shape, volume >= 2x norm
with range <= norm, is the defining shape of absorption (I-2) and that **no
condition in the library computes it** - while both inputs sit in the CSV
header.

Why the existing delta column is not a substitute, and the limit of that claim
------------------------------------------------------------------------------
``Bar.delta`` falls back to ``CLV * volume`` and returns exactly ``0.0`` when
``high == low`` `[repo-verified: futures_agents/data/bars.py:106-113]`, which is
absorption's limiting case - large aggression, no displacement. R1 calls that
"the proxy returns its minimum in the family's defining case", and the
arithmetic is exactly right *at that point*.

It is worth recording where the claim stops, because this module's direction
rule depends on it. ``CLV`` is normalised **by** range, so for a bar with a
small-but-nonzero range the proxy does not degenerate at all: a high-volume bar
closing on its extreme yields ``delta`` near +/-volume however narrow it is.
Zero-range bars are 0.000-0.600% of bars
`[measured: awk over csv/raw/{MGC,MCL}_{1m,5m,15m,1h}.csv -> MGC 0.000/0.020/
0.053/0.080%, MCL 0.600/0.000/0.027/0.160%]`, so the singular case is a corner.

The general form of R1's objection survives that and is the one this module is
built against: CLV reads only *where the close sits*, so it cannot distinguish
"no aggression arrived" from "aggression arrived and was absorbed" - the two
states the family is entirely about. Volume, which is in the CSV, separates
them; CLV cannot.

What this deliberately is not
-----------------------------
- **Not the operating form of I-2.** R1's B.1.6/B.2 require a *sequence* -
  absorption, then a following bar that fails to extend beyond the absorbed
  extreme - and the entry is the failure bar, not the absorption bar. That is
  P9/D37 territory `[repo-verified: workspace/studies/DEFECTS.md:541-548]` and
  is not in the ~15-line item R1 costed. This module fires on the absorption
  bar itself.
- **Not context-gated.** B.1.1 ("context first, always") requires a reference
  level marked before the bar. A level is a separate condition in a rule set,
  not part of this shape.

Look-ahead discipline
---------------------
:func:`absorption_series` returns a list the same length as its input with
``None`` in every warm-up position, and index ``i`` is a function of
``bars[i-window:i]`` (the norm) and ``bars[i]`` (the bar) only. The trailing
window **excludes** bar ``i``, exactly as ``detect_imbalances`` does
(``prior = bars[i - window:i]``, structure.py:452). Appending a bar cannot
change any earlier value; :func:`selftest` asserts that on real bars.

Registration rather than reloading, i.e. D38
--------------------------------------------
A condition receives a ``FeatureSnapshot``, which carries no bars, so the
column has to be precomputed and looked up by ``(symbol, timeframe, bar ts)``.
It must be populated from the very ``SymbolFrame`` the backtest runs on
(:func:`register_frame`). ``toolkit.measure_custom`` **never calls
register_frame**, so a custom condition routed through it returns ``no()`` on
every bar and the strategy reports zero trades - indistinguishable from "the
idea does not work" `[repo-verified: workspace/studies/DEFECTS.md:549-556]`.
Any runner in this directory registers first. Lookup misses are counted in
:data:`MISSES` so a grid mismatch is visible instead of silent.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from futures_agents.schema import Direction
from futures_agents.strategies.base import ConditionKind, ConditionResult
from futures_agents.strategies.library import condition

LONG, SHORT, FLAT = Direction.LONG, Direction.SHORT, Direction.NEUTRAL

#: Trailing bars the norm is measured over. 20 is not a tuned number: it is
#: ``detect_imbalances``' own hardcoded window (structure.py:451), so this
#: condition and the displacement condition it inverts are measured on the
#: same axes and the two are comparable.
WINDOW = 20

#: Thresholds, taken verbatim from R1 §7 Q2 item 1 ("volume >= 2x norm with
#: range <= norm") and consistent with R1-D1 I-2's operating text ("volume per
#: bar 2-4x the recent norm ... range at or below the norm"). Not searched.
VOL_MULT = 2.0
RANGE_MULT = 1.0

#: (symbol, tf, ts) -> Absorption or None. **Every bar of a registered frame
#: gets a key**, warm-up bars included, with the value ``None``. The first
#: version stored only populated bars and the miss counter then reported the 20
#: warm-up bars as grid mismatches - a key that exists and holds ``None`` says
#: "warming up", an absent key says "wrong grid, or nobody registered", and
#: those two have to be distinguishable or :data:`MISSES` is not a mismatch
#: counter.
_MAP: Dict[Tuple[str, int, object], Optional["Absorption"]] = {}

_ABSENT = object()

#: (condition name, symbol, tf) -> lookups whose bar was not on the registered
#: grid at all. Any nonzero entry invalidates the run it came from.
MISSES: Dict[Tuple[str, str, int], int] = {}


class Absorption:
    """The shape as of one bar. Every field is causal at that bar.

    ``v_mult`` and ``r_mult`` are the bar's volume and range over the mean of
    the previous :data:`WINDOW` bars. ``ratio`` is ``v_mult / r_mult``, the
    "volume per unit of displacement" form of the same reading - R1 describes
    the defining measurement as "a ratio of two things" (I-2), so it is carried
    here even though the gate below is two thresholds, not a ratio.
    ``close_pos`` is where the close sat in the bar's own range, in [0, 1], and
    is ``None`` on a zero-range bar because it is undefined there.
    """

    __slots__ = ("v_mult", "r_mult", "close_pos", "volume", "bar_range")

    def __init__(self, v_mult: float, r_mult: float, close_pos: Optional[float],
                 volume: float, bar_range: float):
        self.v_mult = v_mult
        self.r_mult = r_mult
        self.close_pos = close_pos
        self.volume = volume
        self.bar_range = bar_range

    @property
    def ratio(self) -> Optional[float]:
        return None if self.r_mult <= 0 else self.v_mult / self.r_mult

    def fires(self, vol_mult: float = VOL_MULT,
              range_mult: float = RANGE_MULT) -> bool:
        """The shape gate: heavy participation, no displacement to show for it."""
        return self.v_mult >= vol_mult and self.r_mult <= range_mult

    def direction(self) -> Optional[Direction]:
        """Which side was absorbed, read off the close's position in the bar.

        This is the only visible half of R1's B.2 ("the bar closes in its upper
        half"): its other half, "strongly negative delta", needs the aggressor
        flag (P1) and is not here. A close exactly at the midpoint, and a
        zero-range bar where the position is undefined, return ``None`` rather
        than a coin flip.
        """
        if self.close_pos is None or self.close_pos == 0.5:
            return None
        return LONG if self.close_pos > 0.5 else SHORT

    def __repr__(self) -> str:
        cp = "n/a" if self.close_pos is None else f"{self.close_pos:.2f}"
        return (f"Absorption(v={self.v_mult:.2f}x, r={self.r_mult:.2f}x, "
                f"close_pos={cp})")


def absorption_series(bars: Sequence, window: int = WINDOW
                      ) -> List[Optional[Absorption]]:
    """Per-bar shape column, same length as ``bars``, ``None`` while warming up.

    ``None`` covers three cases and they are deliberately not distinguished,
    because a consumer can do nothing different with any of them: fewer than
    ``window`` prior bars; a prior window whose mean range is <= 0; a prior
    window whose mean volume is <= 0. The last two are the same guard
    ``detect_imbalances`` uses (``if avg_range <= 0 or avg_vol <= 0: continue``,
    structure.py:456-457).
    """
    n = len(bars)
    out: List[Optional[Absorption]] = [None] * n
    if n <= window:
        return out
    for i in range(window, n):
        # Re-summed slice rather than a rolling sum. A rolling sum is O(n)
        # instead of O(n*window) and drifts by accumulated float error, so its
        # r_mult would not be bit-identical to the same quantity computed by
        # ``detect_imbalances`` (which re-sums, structure.py:452-454) - and a
        # threshold comparison can flip on that. At 5,000 bars and window 20
        # the saving is ~100k float adds, which is not worth being a hair
        # different from the function this one inverts.
        prior = bars[i - window:i]
        avg_vol = sum(b.volume for b in prior) / window
        avg_rng = sum(b.range for b in prior) / window
        if avg_vol <= 0 or avg_rng <= 0:
            continue
        b = bars[i]
        rng = b.range
        close_pos = None if rng <= 0 else (b.close - b.low) / rng
        out[i] = Absorption(b.volume / avg_vol, rng / avg_rng,
                            close_pos, b.volume, rng)
    return out


# --------------------------------------------------------------------------
# Registration
# --------------------------------------------------------------------------

def register_frame(frame, window: int = WINDOW) -> Dict[int, int]:
    """Index every timeframe of a ``SymbolFrame`` by bar timestamp.

    Returns ``{timeframe: bars indexed}``. Safe to call repeatedly; a later
    registration overwrites the same keys, which is what a caller running
    several disjoint slices of one symbol wants.
    """
    counts: Dict[int, int] = {}
    sym = frame.symbol.upper()
    for tf, tff in frame.frames.items():
        bars = tff.series.bars
        col = absorption_series(bars, window)
        for b, a in zip(bars, col):
            _MAP[(sym, int(tf), b.ts)] = a
        counts[int(tf)] = len(bars)
    return counts


def frame_column(frame, tf: int) -> List[Optional[Absorption]]:
    """The shape column for one timeframe of a registered frame."""
    return [_MAP.get((frame.symbol.upper(), int(tf), b.ts))
            for b in frame.frames[tf].series.bars]


def lookup(symbol: str, tf: int, ts) -> Optional[Absorption]:
    """The shape at one bar, or ``None`` for warm-up **or** an unregistered bar.

    Callers that need to tell those apart use :func:`is_registered`.
    """
    v = _MAP.get((symbol.upper(), int(tf), ts), _ABSENT)
    return None if v is _ABSENT else v


def is_registered(symbol: str, tf: int, ts) -> bool:
    return (symbol.upper(), int(tf), ts) in _MAP


def clear() -> None:
    _MAP.clear()
    MISSES.clear()


def _read(snap, tf: int, name: str) -> Optional[Absorption]:
    """Look the bar up, and count a miss rather than returning a silent no().

    A miss means the frame the condition is running on is not the frame that
    was registered - a different bar grid, or no registration at all (D38).
    Both are bugs in the runner, and the only way they become visible is this
    counter, because the return value is indistinguishable from warm-up. Note
    that "the bar is on the grid but still warming up" is **not** a miss: the
    key is present and holds ``None``.
    """
    s = snap.tf(tf)
    if s is None:
        return None
    v = _MAP.get((snap.symbol.upper(), int(tf), s.bar.ts), _ABSENT)
    if v is _ABSENT:
        k = (name, snap.symbol.upper(), int(tf))
        MISSES[k] = MISSES.get(k, 0) + 1
        return None
    return v


# --------------------------------------------------------------------------
# Conditions
#
# One detector, two consumption shapes, mirroring how the library exposes its
# own imbalance column as a SIGNAL (``imbalance_bar``) and a FILTER
# (``no_recent_imbalance``) - library.py:1168-1202. They are not two
# parameterisations: the gate is identical and only the direction claim
# differs, which is the one part of this R1 has to rule on.
# --------------------------------------------------------------------------

@condition("absorption_bar", "absorption", warmup=WINDOW + 5,
           description="High volume, low range - aggression that bought no displacement")
def _absorption_bar(snap, tf):
    """The signal form: the shape, plus a direction read off the close.

    Direction is the half of R1's B.2 long entry that OHLCV can see. Note
    plainly what that costs: ``close > midpoint`` is also the first clause of
    ``delta_confirms_bar`` `[repo-verified:
    futures_agents/strategies/library.py:455-467]`, so the *novel* content of
    this condition is entirely in the volume-high/range-low gate, and the
    direction half is a bar-shape predicate the library already screens.
    """
    a = _read(snap, tf, "absorption_bar")
    if a is None or not a.fires():
        return ConditionResult.no()
    d = a.direction()
    if d is None:
        return ConditionResult.no()
    return ConditionResult.yes(
        d, f"absorbed: vol {a.v_mult:.1f}x, range {a.r_mult:.2f}x, "
           f"close {a.close_pos:.2f} of bar",
        round(a.v_mult, 3), min(1.0, a.v_mult / 4.0))


@condition("absorption_present", "absorption", kind=ConditionKind.FILTER,
           warmup=WINDOW + 5,
           description="This bar took heavy volume without extending its range")
def _absorption_present(snap, tf):
    """The direction-free form: the shape and nothing else.

    Exists because the shape alone genuinely does not say which side was
    absorbed - that reading needs the aggressor flag (P1). Used as a filter
    beside a direction condition, this keeps the novel part of the algorithm
    separable from the bar-shape part.
    """
    a = _read(snap, tf, "absorption_present")
    if a is None or not a.fires():
        return ConditionResult.no()
    return ConditionResult.yes(
        FLAT, f"vol {a.v_mult:.1f}x, range {a.r_mult:.2f}x",
        round(a.v_mult, 3))


def names() -> List[str]:
    """Every condition name this module registers."""
    return ["absorption_bar", "absorption_present"]
