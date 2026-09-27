"""Scheduled-event entry gates, as ``Condition`` objects the combinator accepts.

Three gates, and the fact that there are exactly three FILTERs and no SIGNAL is
the finding they implement. R2-D1 II-11 records that the library's whole event
vocabulary is three FILTER conditions (``library.py:1326,1334,1345``, all
``ConditionKind.FILTER``), so **the library can decline to trade an event and
can never trade one.** These gates keep that limitation honestly - they are
FILTERs too - and turn the three fixed windows into parameters:

=================  =========================================  ===========================
gate               permits an entry when                      library analogue
=================  =========================================  ===========================
``avoid_event``    NOT inside ``[-before, +after]``            ``outside_news_blackout`` 10/15
``after_event``    ONLY inside ``(lo, hi]`` after a print      ``post_news_window`` 15/60
``into_event``     ONLY inside ``[lo, hi]`` before a print     ``no_imminent_release``, negated
=================  =========================================  ===========================

``into_event`` has no library analogue in this direction: ``no_imminent_release``
declines when a print is close and nothing permits *only* then. It costs four
lines here and it is the pre-positioning arm of II-11, so it is included. It is
**not** in ALGO-1's primary arm set and the ALGOS.md entry says so - an arm that
exists in code and is never measured costs no deflation.

**A gate is a permission, not an entry.** ``after_event`` does not say "buy the
break of the event range"; it says "if your own signal fires in the 15-60 minutes
after the print, you may take it". R2-D2c's operator entry (mark the 10:30-10:35
range, enter on a decisive close beyond it) is a two-step sequence and therefore
D37-blocked as well as SIGNAL-blocked. That divergence is recorded in ALGOS.md
rather than papered over.

**Every parameterisation gets its own ``name``, and that is load-bearing.**
``Condition.evaluate`` memoises on ``key = (self.name, tf)`` (``base.py:120``)
and ``run_many`` allocates one such cache per bar (``engine.py:284``). Two gates
sharing a name but differing in window width would collide on that key and the
second would silently receive the first's answer - the exact mechanism R2
identified for relational conditions in ``R2_expressibility_wall.md`` §1.5, and
the same silent-wrong-answer shape as D38. So ``_slug`` bakes every parameter
that changes the answer into the name, and ``test_algo1.py`` asserts that no two
differently-parameterised gates share one. The name also flows into
``Strategy.strategy_id`` via ``c.label`` (``base.py:615``), so two arms of the
same base strategy cannot collide in ``run_portfolio``'s results dict either -
which they silently would, because that dict is keyed on ``strategy_id``
(``engine.py:277``) and a collision means one arm reads the other's trades.

**``cluster_minutes`` is offered only where it is meaningful.** It shortens
``since`` by re-anchoring on the first print of an episode, which is right for a
drift window and wrong for a blackout - clustering must never let an avoidance
gate open five minutes after the FOMC press conference because the statement
printed thirty minutes earlier. So ``avoid_event`` and ``into_event`` do not take
it, rather than taking it and ignoring it: a parameter that is accepted and has
no effect manufactures two names for one behaviour, which is the alias family
DEFECTS.md lists under M1.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Tuple

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from futures_agents.econ_calendar import Impact                        # noqa: E402
from futures_agents.schema import Direction                            # noqa: E402
from futures_agents.strategies.base import (Condition, ConditionKind,   # noqa: E402
                                            ConditionResult)

from event_clock import EventClock, Reading                            # noqa: E402

__all__ = ["avoid_event", "after_event", "into_event",
           "LIB_BEFORE_MIN", "LIB_AFTER_MIN", "LIB_POST_HI_MIN"]

#: The library's own three window constants, restated so an arm can be declared
#: "the library's setting" without a magic number.
#: ``AccountConfig.news_blackout_before_min`` / ``_after_min``
#: (``config.py:410-411``), and the literal ``60.0`` at ``library.py:1358``.
LIB_BEFORE_MIN = 10.0
LIB_AFTER_MIN = 15.0
LIB_POST_HI_MIN = 60.0

#: Clocks are shared across gates so the per-year event cache is shared.
_CLOCKS: dict = {}


def _clock(symbol: str, min_impact: Impact, cluster_minutes: float) -> EventClock:
    key = (symbol.upper(), min_impact.value, float(cluster_minutes))
    hit = _CLOCKS.get(key)
    if hit is None:
        hit = EventClock(symbol, min_impact=min_impact,
                         cluster_minutes=cluster_minutes)
        _CLOCKS[key] = hit
    return hit


def _num(x: float) -> str:
    """Compact, stable rendering for a name. ``15.0`` -> ``15``, ``7.5`` -> ``7p5``."""
    return str(int(x)) if float(x).is_integer() else str(x).replace(".", "p")


def _make(kind: str, a: float, b: float, *, min_impact: Impact,
          cluster_minutes: float, offset_min: float, description: str,
          predicate: Callable[[Reading], Tuple[bool, str]]) -> Condition:
    """One FILTER condition whose name carries every parameter that matters."""
    name = (f"evt_{kind}_{_num(a)}_{_num(b)}_{min_impact.value}"
            f"_c{_num(cluster_minutes)}_o{_num(offset_min)}")
    imp, clu, off = min_impact, float(cluster_minutes), float(offset_min)

    def fn(snap, tf):
        # snap.ts is the BASE bar's open (features.py:1035 passes bar.ts), so the
        # offset is applied to that and nothing is inferred from ``tf``. A gate
        # bound to a coarser timeframe than the frame's base would otherwise
        # silently offset by the wrong bar length.
        r = _clock(snap.symbol, imp, clu).read_bar(snap.ts, off)
        ok, detail = predicate(r)
        return ConditionResult.yes(Direction.NEUTRAL, detail) if ok \
            else ConditionResult.no()

    return Condition(
        name=name, group="news", fn=fn, kind=ConditionKind.FILTER,
        description=description,
        # The calendar needs no price history, so there is no warm-up. Nothing
        # in the engine reads this field, but stating 0 rather than inheriting
        # the 50-bar default keeps it from being read as a window this gate does
        # not have.
        warmup_bars=0,
    )


# --------------------------------------------------------------------------
# The three gates
# --------------------------------------------------------------------------

def avoid_event(before_min: float = LIB_BEFORE_MIN,
                after_min: float = LIB_AFTER_MIN, *,
                min_impact: Impact = Impact.HIGH,
                offset_min: float = 0.0) -> Condition:
    """Decline to initiate inside ``[-before_min, +after_min]`` of a print.

    Generalises ``outside_news_blackout``. The sign convention is the trap
    ``features.py:979-986`` documents at length: ``ts - event`` is *negative*
    before the release, so the window is ``[-before, +after]``. Written the other
    way round the filter stands aside after the print and initiates straight into
    it, which is the opposite of its purpose.

    Boundaries inclusive, matching ``features.py``'s ``-before <= d <= after``.
    Testing only the nearest print each side is exact, not an approximation: the
    nearest print behind has the smallest ``since`` and the nearest ahead the
    smallest ``to_next``, so if any print is inside the window the nearest one
    is too. That is the same set ``features.py``'s ``any(...)`` over its local
    slice produces.
    """
    def pred(r: Reading) -> Tuple[bool, str]:
        if r.since_prev <= after_min or r.to_next <= before_min:
            return False, ""
        return True, (f"clear of the calendar (next in {r.to_next:.0f}m)"
                      if r.to_next != float("inf") else "calendar empty ahead")

    return _make("avoid", before_min, after_min, min_impact=min_impact,
                 cluster_minutes=0.0, offset_min=offset_min,
                 description=(f"not within {before_min:g}m before or "
                              f"{after_min:g}m after a {min_impact.value}-impact "
                              "scheduled release"),
                 predicate=pred)


def after_event(lo_min: float = LIB_AFTER_MIN, hi_min: float = LIB_POST_HI_MIN, *,
                min_impact: Impact = Impact.HIGH,
                cluster_minutes: float = 0.0,
                offset_min: float = 0.0) -> Condition:
    """Permit an entry ONLY in ``(lo_min, hi_min]`` after a print.

    Generalises ``post_news_window``. Lower bound **strictly** greater, upper
    bound inclusive - copied from ``library.py:1356-1359``, whose comment
    explains why: the blackout's own bound is inclusive, so sharing the endpoint
    left exactly one bar per event inside both windows at once.

    This is the arm F11 measured on MNQ
    (``research/confluence/reversion_specialist.md:366-386``: 112.6 trades ->
    1.5, zero publishable) and the arm R2 says was never asked on MGC or MCL.

    With ``cluster_minutes > 0`` the window is measured from the first print of
    an episode rather than the nearest print, so the FOMC press conference stops
    truncating the statement's drift window.
    """
    def pred(r: Reading) -> Tuple[bool, str]:
        s = r.since_episode if cluster_minutes > 0 else r.since_prev
        name = r.episode_name if cluster_minutes > 0 else r.prev_name
        if s == float("inf") or not (lo_min < s <= hi_min):
            return False, ""
        return True, f"{s:.0f}m after {name}"

    return _make("after", lo_min, hi_min, min_impact=min_impact,
                 cluster_minutes=cluster_minutes, offset_min=offset_min,
                 description=(f"between {lo_min:g}m and {hi_min:g}m after a "
                              f"{min_impact.value}-impact scheduled release"),
                 predicate=pred)


def into_event(lo_min: float = 0.0, hi_min: float = LIB_BEFORE_MIN, *,
               min_impact: Impact = Impact.HIGH,
               offset_min: float = 0.0) -> Condition:
    """Permit an entry ONLY when a print is ``[lo_min, hi_min]`` minutes ahead.

    The pre-positioning arm of II-11, and the mirror of ``no_imminent_release``,
    which declines when a print is near and has no counterpart permitting only
    then. Present for completeness; **not** in ALGO-1's primary arm set.
    """
    def pred(r: Reading) -> Tuple[bool, str]:
        n = r.to_next
        if n == float("inf") or not (lo_min <= n <= hi_min):
            return False, ""
        return True, f"{n:.0f}m before {r.next_name}"

    return _make("into", lo_min, hi_min, min_impact=min_impact,
                 cluster_minutes=0.0, offset_min=offset_min,
                 description=(f"between {lo_min:g}m and {hi_min:g}m before a "
                              f"{min_impact.value}-impact scheduled release"),
                 predicate=pred)
