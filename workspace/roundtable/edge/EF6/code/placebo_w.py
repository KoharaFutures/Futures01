"""EF6 deliverable 1 — the placebo cohort, under the session rule.

``workspace/newstrats/placebo.py`` is the existing machinery and it is good
work: it keeps the base's exits, filters, scope and sizing and replaces only the
signal, it matches on *raw* signals rather than realised trades, it passes
``_id=None`` on both of its ``replace`` calls (so it is D48-clean), and it
derives the scripted condition's name from a hash of the schedule so two
placebos cannot collide through ``Condition.evaluate``'s memo. This module does
not replace it. It **fixes three things that the 18:00 ET -> 16:00 ET window
breaks, and adds the control the brief asks for that does not exist there.**

## 1. Count-matching does not survive the window. Measured, both directions.

``_schedule_random`` draws ``k = len(real_signals)`` bars uniformly from the
base's own eligible pool. Neither ``k`` nor the pool knows about the window,
because the window lives in the engine and not in ``Strategy.evaluate``. So the
base and its control arrive at the engine with **different numbers of legal
entries**.

`[measured: EF6/code/probe_placebo.py -> out/placebo_window_probe.json,
data/archive, 60m and 15m, MGC and MNQ, rth_only True and False]`

| cell | base legal share | pool legal share | realised legal-count gap |
|---|---|---|---|
| MGC 60m `rth_only=True` | 1.000 | 1.000 | 0 |
| MGC 60m `rth_only=False` | 1.000 | 0.964 | 0 |
| **MNQ 60m `rth_only=True`** | 0.964 | **0.838** | **−4, −2, 0, 0** |
| MNQ 60m `rth_only=False` | 0.988 | 0.950 | −2, −1, −2, −2 |
| **MNQ 15m `rth_only=False`** | 0.849 | **0.954** | **+1, +1, +2, +2** |

The mechanism is arithmetic, not luck. At 60m under ``rth_only=True`` MNQ has
six RTH bars a day and the **15:00** one fills at 16:00, so exactly 1/6 = 16.7%
of pool bars are illegal - while the real signal happens to fire at 15:00 far
less often, losing only 0-5%. A uniform draw from the pool therefore loses ~17%
of its entries where the base loses ~4%: on a base of 16 legal signals the
control arrived with 12, a **25% sample deficit**. And on MNQ 15m the sign
*reverses* - the control gets more legal entries than the base. So this is not a
conservative bias that can be waved through.

**Fix:** match on **legal** signals and draw from the **legal** pool. Both sides
of the match are intersected with :func:`window.signal_mask` before anything is
counted.

## 2. ``placebo_shuffle`` is not a control for a one-sided signal. It is the base.

``_schedule_shuffle`` permutes the *direction labels* across the base's own bars
(its docstring says so). For a random permutation of a multiset with long share
``p``, the expected share of positions that keep their label is ``p² + (1−p)²``,
so:

| base long share | direction labels destroyed |
|---|---|
| 1.00 or 0.00 (one-sided) | **0%** - the control *is* the base |
| 0.90 | 18% |
| 0.50 (the best case) | **50%** |

`[measured: MGC 60m rth_only=True, 4 MEAN_REVERSION bases, long_share 0.000 ->
shuffle_direction_changed **0.0000**. MNQ 60m rth_only=True, long_share 0.905 ->
0.1905, against the formula's 0.172. MNQ 15m, long_share 0.5 -> 0.667 on n=6.]`

So the strongest form this control can ever take destroys **half** of one
channel, and on a directional rule set it destroys nothing. This matters beyond
tidiness: the programme's headline is that "five separate placebo constructions
matched or beat the real thing", and a control that is 50-100% identical to its
treatment is *expected* to match it. That is a re-reading of the existing
finding, not a new measurement, and it is stated as such.

## 3. The brief asks for a **timestamp shuffle**, and there isn't one.

``placebo_shuffle`` shuffles directions on fixed timestamps. This module adds
:func:`schedule_session_shuffle`, which is the control the brief names and a
better one than a uniform random draw:

**Move each signal to the same time of day on a different 18:00->16:00 cycle.**
Count, direction, time-of-day distribution and intraday clustering are all
preserved exactly; what is destroyed is the pairing between the signal and the
price action of *that* cycle. A uniform random draw destroys the time-of-day
profile too, which confounds "the signal did nothing" with "the time of day did
it" - and this repo has two settled time-of-day effects to confound with
(no entries 15:00-16:00, z = −4.43; opening-range behaviour). Because the
intraday slot is preserved and the slot was legal, the shuffled entry is legal
by construction, which is the second reason it is the right control here.

Every schedule this module produces is asserted legal before it is returned.
"""

from __future__ import annotations

import dataclasses
import hashlib
import random
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

from futures_agents.schema import Direction
from futures_agents.strategies.base import ConditionKind, Strategy
from futures_agents.timeutil import to_et

import window as W

# The existing machinery, reused rather than reimplemented.
from newstrats.placebo import (PlaceboMeta, SignalSchedule, scan,
                               scripted_condition)

__all__ = [
    "KINDS", "shuffle_degeneracy", "schedule_random_legal",
    "schedule_session_shuffle", "make_placebo", "build_cohort",
]

#: The two the brief requires, plus the direction shuffle kept only so its
#: degeneracy can be reported rather than silently inherited.
#: ``placebo_shift`` is deliberately absent: it leaks (D42) and is
#: conservative-only, so it cannot support a claim that a row beat its control.
KINDS = ("placebo_random_legal", "placebo_session_shuffle")


def shuffle_degeneracy(long_share: float) -> float:
    """Expected share of direction labels a direction-shuffle leaves UNCHANGED.

    ``p² + (1−p)²``. Minimum 0.5 at p = 0.5; 1.0 at p = 0 or 1.
    """
    p = float(long_share)
    return p * p + (1.0 - p) * (1.0 - p)


# --------------------------------------------------------------------------
# The two window-safe schedules
# --------------------------------------------------------------------------

def _legal(real: SignalSchedule, smask: Sequence[bool]) -> SignalSchedule:
    return {i: d for i, d in real.items() if i < len(smask) and smask[i]}


def schedule_random_legal(real: SignalSchedule,
                          pool: Dict[Direction, Sequence[int]],
                          smask: Sequence[bool], rng: random.Random,
                          *, n_realised: Optional[int] = None,
                          hold_bars: int = 0) -> Tuple[SignalSchedule, dict]:
    """Count-matched random bars, on **legal** signals from the **legal** pool.

    Matched per direction, because stop placement (``STRUCTURE``, ``VWAP_BAND``)
    and anchored targets are not symmetric - a bar can be a legal long entry and
    an illegal short one, which is why ``placebo.scan`` builds two probes.

    **``n_realised`` and ``hold_bars`` fix a second count-matching fault, and it
    is in the original design rather than in the window.** ``placebo.py`` matches
    on RAW signals on the argument that "after the engine's own culling the
    realised counts land in the same place". Measured on a real top 10 - MGC 60m,
    10 bases - they do not: the base realised **110-158** trades and its
    count-matched placebo realised **307-366**, a **2.0x to 3.3x overshoot**.
    The reason is clustering. A real signal fires in bursts, and the engine
    refuses a new signal while positioned, so most of a burst is culled; the
    placebo's entries are scattered, overlap nothing, and almost all survive.

    A placebo with 3x the sample is not a fair control: its standard error is
    sqrt(3) smaller, so it wins any comparison scored on *t* and loses any
    comparison scored on trade count, for reasons that have nothing to do with
    the signal.

    The fix is one pass, not a calibration loop: draw exactly ``n_realised``
    entries and enforce a minimum separation of ``hold_bars`` between them, so
    the engine's own culling has almost nothing left to remove and realised
    lands on the target by construction. ``hold_bars`` should be the base's
    median realised holding period in base bars.
    """
    legal_real = _legal(real, smask)
    want = Counter(legal_real.values())
    target = len(legal_real) if n_realised is None else int(n_realised)
    if target != len(legal_real) and len(legal_real):
        scale = target / len(legal_real)
        want = Counter({d: max(0, int(round(c * scale))) for d, c in want.items()})
        # keep the total exactly on target after rounding
        drift = target - sum(want.values())
        if drift and want:
            d0 = max(want, key=lambda d: want[d])
            want[d0] = max(0, want[d0] + drift)
    out: SignalSchedule = {}
    taken: List[int] = []
    short_by = 0
    sep = max(0, int(hold_bars))

    def ok(i: int) -> bool:
        return all(abs(i - j) > sep for j in taken)

    for d in (Direction.LONG, Direction.SHORT):
        k = want.get(d, 0)
        if k <= 0:
            continue
        cand = [i for i in pool.get(d, ()) if smask[i]]
        rng.shuffle(cand)
        placed = 0
        for i in cand:
            if placed >= k:
                break
            if i in out or not ok(i):
                continue
            out[i] = d
            taken.append(i)
            placed += 1
        short_by += k - placed
    diag = {"n_real": len(real), "n_real_legal": len(legal_real),
            "target_realised": target, "min_separation_bars": sep,
            "n_scheduled": len(out), "pool_short_by": short_by,
            "legal_pool_long": sum(1 for i in pool.get(Direction.LONG, ()) if smask[i]),
            "legal_pool_short": sum(1 for i in pool.get(Direction.SHORT, ()) if smask[i])}
    return out, diag


def schedule_session_shuffle(real: SignalSchedule, bars: Sequence,
                             smask: Sequence[bool], rng: random.Random,
                             *, slot_index: Optional[Dict[Tuple[str, str], int]] = None
                             ) -> Tuple[SignalSchedule, dict]:
    """Same time of day, different 18:00->16:00 cycle.

    Preserves count, direction, time-of-day distribution and intraday
    clustering. Destroys the pairing between the signal and that cycle's price.
    Legal by construction, because the intraday slot is unchanged.

    A signal is dropped only when no bar exists at its slot on the drawn cycle
    (a holiday or a vendor gap); ``dropped`` reports how often, so the count
    match is auditable rather than assumed.
    """
    if slot_index is None:
        slot_index = {}
        for i, b in enumerate(bars):
            d = to_et(b.ts)
            slot_index[(W.cycle_id(b.ts), d.strftime("%H:%M"))] = i
    cycles = sorted({c for c, _ in slot_index})
    out: SignalSchedule = {}
    dropped = 0
    collisions = 0
    for i, dirn in sorted(real.items()):
        if not smask[i]:
            continue                      # the real signal was itself illegal
        d = to_et(bars[i].ts)
        slot = d.strftime("%H:%M")
        # Draw a different cycle, up to a bounded number of attempts.
        own = W.cycle_id(bars[i].ts)
        placed = False
        for _ in range(12):
            c = cycles[rng.randrange(len(cycles))]
            if c == own:
                continue
            j = slot_index.get((c, slot))
            if j is None or not smask[j]:
                continue
            if j in out:
                collisions += 1
                continue
            out[j] = dirn
            placed = True
            break
        if not placed:
            dropped += 1
    return out, {"n_real": len(real), "n_real_legal": sum(1 for i in real if smask[i]),
                 "n_scheduled": len(out), "dropped_no_slot": dropped,
                 "slot_collisions": collisions, "n_cycles": len(cycles)}


# --------------------------------------------------------------------------
# Cohort
# --------------------------------------------------------------------------

def make_placebo(base: Strategy, kind: str, schedule: SignalSchedule,
                 ts_of: Sequence) -> Strategy:
    """Same as ``placebo.make_placebo`` but with the D48 guard asserted here.

    The upstream version already passes ``_id=None``; this one additionally
    *asserts* the resulting id differs from the base's, so a future change to
    ``Strategy.strategy_id``'s field list cannot silently reintroduce the
    collision.
    """
    key = f"{kind}|{base.strategy_id}|" + ",".join(
        f"{i}:{d.value}" for i, d in sorted(schedule.items()))
    digest = hashlib.sha1(key.encode()).hexdigest()[:12]
    cond = scripted_condition(
        f"plc_{kind}_{digest}",
        {ts_of[i]: d for i, d in schedule.items() if 0 <= i < len(ts_of)},
        group=base.signal_conditions[0].group)
    filters = tuple(c for c in base.conditions if c.kind is ConditionKind.FILTER)
    out = dataclasses.replace(
        base, name=f"{kind}__{base.name}"[:120],
        conditions=(cond,) + filters, trigger_conditions=(), _id=None)
    if out.strategy_id == base.strategy_id:
        raise AssertionError(
            f"D48: placebo id collided with its base ({out.strategy_id}). "
            "The control and the thing it controls would merge into one "
            "BacktestResult and their difference would measure exactly zero.")
    return out


def build_cohort(frame, bases: Sequence[Strategy], realised: Dict[str, int], *,
                 seed: int = 0, kinds: Sequence[str] = KINDS,
                 start: int = 0, end: Optional[int] = None,
                 hold_bars: Optional[Dict[str, int]] = None,
                 match_on: str = "realised"
                 ) -> Tuple[List[Strategy], Dict[str, PlaceboMeta], dict]:
    """``match_on="realised"`` (default) matches the base's REALISED trade count
    with a minimum separation of ``hold_bars[base_id]``; ``"raw"`` reproduces
    ``placebo.py``'s raw-signal match, which overshoots 2-3x on a clustered
    signal (see :func:`schedule_random_legal`). ``realised`` and ``hold_bars``
    come from the base's own run, so the control is built against what the base
    actually did rather than against what it proposed.
    """
    """One placebo per (base, kind), every schedule legal under the window rule."""
    bars = frame.base.bars
    base_min = int(frame.base.minutes)
    smask = W.signal_mask(bars, base_min)
    ts_of = [b.ts for b in bars]
    rng = random.Random(f"ef6-placebo:{seed}:{frame.symbol}:{base_min}")

    real_sched, pools = scan(frame, bases, want_pool=True, start=start, end=end)

    slot_index: Dict[Tuple[str, str], int] = {}
    for i, b in enumerate(bars):
        slot_index[(W.cycle_id(b.ts), to_et(b.ts).strftime("%H:%M"))] = i

    out: List[Strategy] = []
    meta: Dict[str, PlaceboMeta] = {}
    diag = {"kinds": list(kinds), "match_on": match_on,
            "n_bases": len(bases), "base_minutes": base_min,
            "signal_eligible_bars": sum(smask), "n_bars": len(bars),
            "dropped_base_too_few_legal": 0, "id_collisions": 0,
            "per_kind": {k: {"built": 0, "count_matched": 0, "short": 0} for k in kinds},
            "shuffle_degeneracy_if_used": []}

    for s in bases:
        real = real_sched.get(s.strategy_id, {})
        legal_real = _legal(real, smask)
        if len(legal_real) < 2:
            diag["dropped_base_too_few_legal"] += 1
            continue
        mix = Counter(legal_real.values())
        p_long = mix.get(Direction.LONG, 0) / len(legal_real)
        diag["shuffle_degeneracy_if_used"].append(
            round(shuffle_degeneracy(p_long), 3))
        pl = pools.get(s.strategy_id, {})
        for kind in kinds:
            if kind == "placebo_random_legal":
                nr = (int(realised.get(s.strategy_id, 0)) or None
                      if match_on == "realised" else None)
                hb = (hold_bars or {}).get(s.strategy_id, 0) if match_on == "realised" else 0
                sched, d = schedule_random_legal(real, pl, smask, rng,
                                                 n_realised=nr, hold_bars=hb)
            elif kind == "placebo_session_shuffle":
                sched, d = schedule_session_shuffle(real, bars, smask, rng,
                                                    slot_index=slot_index)
            else:
                raise ValueError(f"unknown kind {kind!r} - placebo_shift leaks "
                                 "(D42) and is not offered here")
            if len(sched) < 2:
                continue
            # Every scheduled entry must be legal. Assert, do not trust.
            bad = [i for i in sched if not smask[i]]
            if bad:
                raise AssertionError(
                    f"{kind} scheduled {len(bad)} illegal entries for "
                    f"{s.strategy_id} - the control would be measured on bars "
                    "the base cannot trade")
            p = make_placebo(s, kind, sched, ts_of)
            if p.strategy_id in meta:
                diag["id_collisions"] += 1
                continue
            cnt = Counter(sched.values())
            meta[p.strategy_id] = PlaceboMeta(
                strategy_id=p.strategy_id, kind=kind, base_id=s.strategy_id,
                base_name=s.name, group=s.group, n_real_signals=len(legal_real),
                n_scheduled=len(sched),
                n_long_scheduled=cnt.get(Direction.LONG, 0),
                n_short_scheduled=cnt.get(Direction.SHORT, 0),
                base_realised=int(realised.get(s.strategy_id, 0)), pool="legal")
            out.append(p)
            diag["per_kind"][kind]["built"] += 1
            tgt = int(d.get("target_realised", len(legal_real)))
            diag["per_kind"][kind]["count_matched"] += int(len(sched) == tgt)
            diag["per_kind"][kind]["short"] += max(0, tgt - len(sched))

    v = diag.pop("shuffle_degeneracy_if_used")
    diag["mean_shuffle_degeneracy_if_direction_shuffle_were_used"] = (
        round(sum(v) / len(v), 4) if v else None)
    diag["n_placebos"] = len(out)
    return out, meta, diag
