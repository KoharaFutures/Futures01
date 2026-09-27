"""EF6 — D48 guard: build an arm without collapsing it into the arm it came from.

`D48`: ``_id`` is a dataclass *field* on ``Strategy`` (`base.py:585`) that
``strategy_id`` memoises into (`:611-623`), and ``dataclasses.replace`` copies
fields - so once the id has been read **even once**, every later ``replace``
carries the stale id forward. Two arms then share one ``strategy_id``,
``run_many`` keys both its results dict and its open-position state by that id
`[repo-verified: engine.py:271-283, 301-318]`, and the two arms **collide into
one BacktestResult**. The measured between-arm difference is then *exactly
zero*, which is indistinguishable from "this makes no difference" - the
conclusion this programme is most exposed to.

**Why this lands here specifically.** The 18:00->16:00 window cannot be run on
combinator output as generated: ``StrategyFilters.rth_only`` defaults to True
`[repo-verified: base.py:393]` and is True on **314/314** generated strategies
`[measured: generate_strategies('MGC'|'MNQ',[5,15,60,240],max_total=400) ->
Counter({True: 314}) on each]`. Every agent in this programme therefore has to
build an ``rth_only=False`` arm by ``replace``-ing the filters, which is the
exact D48 shape. And ``StrategyFilters.identity`` *does* include ``rth_only``
(`base.py:459-484`), so the two arms would have distinct ids **if** the id were
recomputed - the collision is purely the stale memo.

Use :func:`respec` and never bare ``dataclasses.replace`` on a ``Strategy``.
Call :func:`assert_unique` at emission, every time, even when you are sure.
"""

from __future__ import annotations

import dataclasses
from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from futures_agents.strategies.base import Strategy, StrategyFilters

__all__ = ["respec", "refilter", "assert_unique", "two_arms", "arm_report"]


def respec(strategy: Strategy, **changes) -> Strategy:
    """``dataclasses.replace`` with ``_id=None`` forced, and the id re-read.

    Re-reading ``strategy_id`` on the way out is deliberate: it makes the new
    id materialise here rather than at some later call site, so a downstream
    ``replace`` on *this* object is itself caught by the same guard.
    """
    if "_id" in changes and changes["_id"] is not None:
        raise ValueError("respec refuses an explicit _id - that is the D48 bug")
    changes["_id"] = None
    out = dataclasses.replace(strategy, **changes)
    _ = out.strategy_id
    if out.strategy_id == strategy.strategy_id and _differs(strategy, out):
        raise AssertionError(
            f"D48: arm id collided with its base ({out.strategy_id}) despite "
            "_id=None - StrategyFilters.identity or ExitModel.identity is not "
            "covering a field that changed")
    return out


def _differs(a: Strategy, b: Strategy) -> bool:
    """Do these two differ in anything ``strategy_id`` is supposed to cover?"""
    fields = ("symbol", "primary_tf", "group", "conditions", "exit", "filters",
              "allowed_directions", "confirm_tfs", "execution_tf",
              "trigger_conditions")
    for f in fields:
        if getattr(a, f) != getattr(b, f):
            return True
    return False


def refilter(strategy: Strategy, **filter_changes) -> Strategy:
    """Change ``StrategyFilters`` fields safely. The common case in this programme.

        window_arm = refilter(base, rth_only=False)

    ``StrategyFilters`` is frozen, so its own ``replace`` is safe; the hazard is
    only on ``Strategy``, and :func:`respec` handles it.
    """
    return respec(strategy,
                  filters=dataclasses.replace(strategy.filters, **filter_changes))


def assert_unique(*groups: Sequence[Strategy], labels: Optional[Sequence[str]] = None
                  ) -> Dict[str, int]:
    """Assert every strategy id across every arm is distinct. Raise, loudly.

    Called at **emission**, not at construction, because the failure mode is a
    collision between two objects built at different times by different code
    paths. Returns ``{arm_label: n}`` so the caller can log the shape it
    asserted, which is how a silently-empty arm gets noticed.
    """
    labels = list(labels) if labels else [f"arm{i}" for i in range(len(groups))]
    ids: Counter = Counter()
    owner: Dict[str, List[str]] = {}
    for lab, g in zip(labels, groups):
        for s in g:
            ids[s.strategy_id] += 1
            owner.setdefault(s.strategy_id, []).append(lab)
    dup = {k: owner[k] for k, v in ids.items() if v > 1}
    if dup:
        sample = list(dup.items())[:5]
        raise AssertionError(
            f"D48: {len(dup)} strategy_id collisions across arms. "
            f"Each collision merges two arms into one BacktestResult and makes "
            f"their difference exactly zero. Examples: {sample}")
    return {lab: len(g) for lab, g in zip(labels, groups)}


def two_arms(bases: Sequence[Strategy], **filter_changes
             ) -> Tuple[List[Strategy], List[Strategy], Dict[str, int]]:
    """(control arm, treatment arm, shape) with uniqueness asserted.

    The control arm is the bases **as given**; the treatment arm is each base
    with ``filter_changes`` applied. Both lists are returned so the caller runs
    them in one ``run_many`` pass and the comparison is paired by base.
    """
    treat = [refilter(s, **filter_changes) for s in bases]
    shape = assert_unique(list(bases), treat, labels=["control", "treatment"])
    if shape["control"] != shape["treatment"]:
        raise AssertionError(f"arms are different sizes: {shape}")
    return list(bases), treat, shape


def arm_report(results: Dict[str, object], *arms: Sequence[Strategy],
               labels: Optional[Sequence[str]] = None) -> dict:
    """Post-run check: every arm actually received its own result object.

    The D48 signature after the fact is two arms whose ``BacktestResult`` is the
    *same object*. Checking identity catches a collision that slipped past
    construction - e.g. one introduced by a third ``replace`` inside a helper.
    """
    labels = list(labels) if labels else [f"arm{i}" for i in range(len(arms))]
    seen: Dict[int, str] = {}
    shared = []
    out = {}
    for lab, g in zip(labels, arms):
        got = 0
        for s in g:
            r = results.get(s.strategy_id)
            if r is None:
                continue
            got += 1
            key = id(r)
            if key in seen and seen[key] != lab:
                shared.append((seen[key], lab, s.strategy_id))
            seen[key] = lab
        out[lab] = {"n": len(g), "with_result": got}
    out["shared_result_objects"] = len(shared)
    out["examples"] = shared[:5]
    if shared:
        raise AssertionError(
            f"D48 after the fact: {len(shared)} result objects are shared "
            f"between arms. The between-arm difference is not measurable.")
    return out
