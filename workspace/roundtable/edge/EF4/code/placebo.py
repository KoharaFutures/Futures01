"""EF4 - the placebo beside every reported row.

The construction the EDGE_BRIEF requires: count-matched random bars, run through the
row's OWN exits, filters and sizing, under the same 18:00->16:00 rule. `placebo_shift`
is excluded - D42 records that it leaks, and it is conservative-only.

What is matched, and why signals rather than trades. The real row's `signals_generated`
is the number of bars on which its detector fired; its `trades` is what survived the
entry veto, the one-position-at-a-time rule and the risk floor. Matching on SIGNALS and
then letting the same machinery filter the placebo is the only construction where the
two arms face identical downstream attrition. Matching on trades would hand the placebo
a larger signal set and quietly make it the easier arm.

Direction is matched too. A placebo that is 50/50 long/short competing against a real row
that is 80% long is being compared on direction as well as on timing, and on a trending
sample the direction alone can carry it. The placebo draws its long/short split from the
real row's realised split.

`_id=None` is passed on every construction (D48) and arm ids are asserted distinct.
"""
from __future__ import annotations

import random
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))

from futures_agents.features import FeatureSnapshot                    # noqa: E402
from futures_agents.schema import Direction                            # noqa: E402
from futures_agents.strategies.base import (Condition, ConditionKind,
                                            ConditionResult, Strategy)  # noqa: E402


class _RandomBars:
    """Fires on a fixed, pre-drawn set of bar indices with fixed directions.

    Deterministic given (seed, n_bars, n_fire, long_share): the set is drawn once at
    construction, never per evaluation, so the same placebo evaluates identically in a
    re-run and in a split-sample slice. A placebo redrawn per call would be a different
    strategy in every fold, and its out-of-sample behaviour would be meaningless.
    """

    def __init__(self, fire: Set[int], direction: Dict[int, Direction], tag: str):
        self.fire = fire
        self.direction = direction
        self.tag = tag
        self.__doc__ = f"placebo random bars ({tag})"

    def __call__(self, snap: FeatureSnapshot, tf: int) -> ConditionResult:
        i = snap.base_index
        if i in self.fire:
            return ConditionResult.yes(self.direction[i], f"placebo {self.tag}")
        return ConditionResult.no()


def make_placebo(base: Strategy, *, n_bars: int, n_signals: int,
                 long_share: float, seed: int) -> Strategy:
    """``base`` with every SIGNAL replaced by one random-bar condition.

    FILTERs are kept exactly as they are - the brief says "run through the row's own
    exits, FILTERS and sizing", so the placebo inherits the row's gating and differs from
    it only in where the signal fires. Keeping the filters is what makes the comparison
    about the signal rather than about the whole strategy.
    """
    rng = random.Random(seed)
    k = min(max(1, n_signals), n_bars)
    fire = set(rng.sample(range(n_bars), k))
    direction = {i: (Direction.LONG if rng.random() < long_share else Direction.SHORT)
                 for i in fire}
    cond = Condition(
        name=f"placebo_s{seed}", group="placebo",
        fn=_RandomBars(fire, direction, f"seed={seed}"),
        kind=ConditionKind.SIGNAL,
        description=f"count-matched random bars, {k} of {n_bars}", warmup_bars=0)
    kept = tuple(c for c in base.conditions if c.kind is ConditionKind.FILTER)
    return replace(
        base, name=f"PLACEBO[{base.name}]#{seed}", group="PLACEBO",
        conditions=(cond,) + kept, _id=None,
    )
