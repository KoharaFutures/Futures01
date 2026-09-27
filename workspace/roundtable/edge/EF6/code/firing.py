"""EF6 deliverable 2 — the firing-rate prefilter. Run this BEFORE measuring.

19.0% of generated strategies carry a condition that can **never fire**, and
``Strategy.evaluate`` is a strict AND with no ``min_signals``
`[repo-verified: futures_agents/strategies/base.py:670-684]`, so **one dead
condition kills the whole strategy**. A strategy that never traded and a
strategy that traded and lost both produce a null. Only the second is a result.

## What this module does, and why it is two steps rather than one

**Step 1, once per (symbol, frame): the census.** One pass over the bars,
evaluating every condition in the library at every timeframe the frame carries,
counting fires. The expensive part of any sweep is ``SymbolFrame.snapshot(i)``,
which rebuilds the cross-timeframe snapshot from scratch, so the census pays for
the bars exactly once and writes a JSON artefact.

**Step 2, free, any number of times: the audit.** ``audit(strategies, census)``
reads the artefact and returns, per strategy, which of its conditions fire on
zero bars and therefore whether the strategy is structurally incapable of
trading. No data access, no backtest. This is what EF2-EF5 run before measuring.

## The window, and why it changes verdicts rather than just counts

Every count is reported three ways, because the denominator is the whole
argument:

* ``all``     - every bar. What R1's census measured.
* ``window``  - bars on which a position may exist under 18:00 ET -> 16:00 ET.
* ``signal``  - bars whose signal could be *filled* legally (the engine fills at
  the next bar's open, so this is ``window`` shifted by one).

``VOID`` is judged on the **signal** denominator, because a condition that fires
only on bars no legal entry can follow is void in operation even if its raw
count is non-zero. That reproduces R1's D-L4 mechanism
(``session_extreme_sweep`` fires only outside RTH, and ``rth_only=True``
vetoed every one of its fires) with the *new* window substituted - and the
substitution can flip a verdict in **either** direction, which is why this is
verified and not inherited:

* a condition R1 found VOID under ``rth_only=True`` may be **alive** here,
  because 18:00->16:00 admits the whole Globex session that RTH excluded;
* a condition alive on ``all`` bars may be **VOID** here if its fires sit in
  16:00-18:00.

## Verdicts, from the shared vocabulary (`BRIEF.md` "Shared audit vocabulary")

``VOID``    0 fires in this cell - structurally, not rarely. Per (symbol, tf).
``THIN``    fires, but below ``THIN_FIRES`` - a result built on it will not
            reach any trade floor. Not part of the shared vocabulary; local to
            this module and reported separately so it is never confused with
            VOID.
``ALIVE``   fires enough that the strategy carrying it can in principle trade.

A strategy is ``VOID`` if **any** of its conditions is VOID at the timeframe it
is evaluated on. That is the strict-AND consequence, and it is the only verdict
this module asserts about a strategy - "ALIVE" here means "not structurally
dead", never "good".
"""

from __future__ import annotations

import json
import os
from collections import Counter
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from futures_agents.features import SymbolFrame
from futures_agents.schema import Direction
from futures_agents.strategies.base import (Condition, ConditionKind, Strategy,
                                            condition_errors,
                                            reset_condition_errors)
from futures_agents.strategies.library import CONDITIONS

import window as W

__all__ = [
    "THIN_FIRES", "census", "save_census", "load_census", "condition_verdict",
    "audit", "audit_summary", "prefilter",
]

#: Below this many fires on the signal denominator, a condition cannot support a
#: strategy that reaches any sane trade floor. Deliberately small: the point of
#: THIN is to be a warning, and the point of VOID is to be a fact.
THIN_FIRES = 5


def census(frame: SymbolFrame, *, conditions: Optional[Dict[str, Condition]] = None,
           timeframes: Optional[Sequence[int]] = None,
           start: int = 0, end: Optional[int] = None,
           progress: Optional[object] = None) -> dict:
    """One pass over ``frame``: fire counts per (condition, eval timeframe).

    Counts are split by the three denominators (all / window / signal) and, for
    SIGNAL conditions, by direction, because a condition can be alive LONG and
    VOID SHORT - ``regime_matches_direction`` on MES 240m is R4's measured
    example. A directional VOID matters because ``allowed_directions`` on the
    generated strategy may name only the dead half.
    """
    conds = dict(CONDITIONS) if conditions is None else dict(conditions)
    tfs = list(timeframes) if timeframes else list(frame.frames.keys())
    bars = frame.base.bars
    n = len(bars)
    stop_at = n if end is None else min(end, n)
    start = max(0, start)
    base_min = int(frame.base.minutes)

    wmask = W.window_mask(bars, base_min)
    smask = W.signal_mask(bars, base_min)

    keys = [(name, tf) for name in conds for tf in tfs]
    fires = {k: {"all": 0, "window": 0, "signal": 0} for k in keys}
    dirs = {k: Counter() for k in keys}
    evaluable = {tf: 0 for tf in tfs}      # bars where snap.tf(tf) is not None
    n_all = n_window = n_signal = 0

    reset_condition_errors()
    for i in range(start, stop_at):
        snap = frame.snapshot(i)
        if snap is None:
            continue
        n_all += 1
        in_w = wmask[i]
        in_s = smask[i]
        n_window += in_w
        n_signal += in_s
        cache: Dict[Tuple[str, int], object] = {}
        for tf in tfs:
            if snap.tf(tf) is None:
                continue
            evaluable[tf] += 1
            for name, cond in conds.items():
                res = cond.evaluate(snap, tf, cache)
                if not res.triggered:
                    continue
                k = (name, tf)
                fires[k]["all"] += 1
                if in_w:
                    fires[k]["window"] += 1
                if in_s:
                    fires[k]["signal"] += 1
                    if cond.kind is ConditionKind.SIGNAL:
                        dirs[k][res.direction.value] += 1
        if progress is not None and (i - start) % 500 == 0:
            progress(i - start, stop_at - start)

    errs = {f"{nm}:{tp}": c for (nm, tp), c in condition_errors().items()}
    return {
        "symbol": frame.symbol,
        "base_minutes": base_min,
        "frame_timeframes": sorted(frame.frames.keys()),
        "eval_timeframes": [int(t) for t in tfs],
        "bars": {"total": n, "evaluated": n_all, "in_window": n_window,
                 "signal_eligible": n_signal},
        "first_ts": str(bars[start].ts) if stop_at > start else None,
        "last_ts": str(bars[stop_at - 1].ts) if stop_at > start else None,
        "evaluable_bars_by_tf": {str(t): v for t, v in evaluable.items()},
        # A condition that raised on EVERY evaluation is a defect, not a 0% rate
        # [repo-verified: base.py:180-215 explains exactly this failure].
        "condition_errors": errs,
        "straddle": W.straddle_report(bars, base_min),
        "fires": {f"{nm}@{tf}": v for (nm, tf), v in fires.items()},
        "directions": {f"{nm}@{tf}": dict(v) for (nm, tf), v in dirs.items() if v},
        "kinds": {nm: c.kind.value for nm, c in conds.items()},
        "groups": {nm: c.group for nm, c in conds.items()},
    }


def save_census(doc: dict, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, f"census_{doc['symbol']}_{doc['base_minutes']}m.json")
    with open(p, "w") as fh:
        json.dump(doc, fh, indent=1, default=str)
    return p


def load_census(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


def condition_verdict(doc: dict, name: str, tf: int, *,
                      denominator: str = "signal",
                      direction: Optional[str] = None) -> dict:
    """VOID / THIN / ALIVE for one condition at one timeframe in one cell."""
    k = f"{name}@{int(tf)}"
    rec = doc["fires"].get(k)
    if rec is None:
        return {"condition": name, "tf": int(tf), "verdict": "UNMEASURED",
                "fires": None, "reason": "not in this census"}
    fires = int(rec[denominator])
    if direction is not None:
        d = doc.get("directions", {}).get(k, {})
        fires = int(d.get(direction, 0))
    denom = {"all": doc["bars"]["evaluated"], "window": doc["bars"]["in_window"],
             "signal": doc["bars"]["signal_eligible"]}[denominator]
    if fires == 0:
        v = "VOID"
    elif fires < THIN_FIRES:
        v = "THIN"
    else:
        v = "ALIVE"
    # A condition that raised on every evaluation looks identical to VOID.
    raised = sum(c for kk, c in doc.get("condition_errors", {}).items()
                 if kk.split(":")[0] == name)
    return {"condition": name, "tf": int(tf), "verdict": v, "fires": fires,
            "denominator": denominator, "denominator_bars": denom,
            "rate": round(fires / max(1, denom), 5),
            "direction": direction,
            "evaluable_bars": doc["evaluable_bars_by_tf"].get(str(int(tf))),
            "raised_exceptions": raised,
            "note": ("RAISED on evaluations - a 0 here may be a defect, not a "
                     "market fact" if raised else "")}


def _eval_tf(strategy: Strategy, cond: Condition, *, trigger: bool = False) -> int:
    """Which timeframe a condition is actually evaluated on.

    Mirrors ``Strategy.evaluate`` exactly: ``cond.timeframe`` wins if set,
    otherwise ``primary_tf`` for conditions and ``entry_tf`` for triggers
    `[repo-verified: base.py:653-700]`. Getting this wrong is the whole audit -
    a condition alive at 60m and VOID at 240m must be judged at the timeframe
    the strategy will actually read it on.
    """
    if cond.timeframe:
        return int(cond.timeframe)
    return int(strategy.entry_tf if trigger else strategy.primary_tf)


def audit(strategies: Sequence[Strategy], doc: dict, *,
          denominator: str = "signal", check_directions: bool = True) -> List[dict]:
    """Per-strategy verdict. VOID if ANY condition is VOID at its own timeframe.

    ``check_directions`` additionally reports a strategy whose *every* allowed
    direction is void on one of its SIGNAL conditions - the R4-R3 shape, where
    a condition fires only LONG and the strategy is generated SHORT-only.
    """
    out = []
    for s in strategies:
        rows = []
        for c in s.conditions:
            rows.append((False, c, condition_verdict(
                doc, c.name, _eval_tf(s, c), denominator=denominator)))
        for c in s.trigger_conditions:
            rows.append((True, c, condition_verdict(
                doc, c.name, _eval_tf(s, c, trigger=True), denominator=denominator)))

        void = [r for _, _, r in rows if r["verdict"] == "VOID"]
        thin = [r for _, _, r in rows if r["verdict"] == "THIN"]
        unmeasured = [r for _, _, r in rows if r["verdict"] == "UNMEASURED"]

        dir_void = []
        if check_directions:
            allowed = {d.value for d in s.allowed_directions}
            for trig, c, r in rows:
                if c.kind is not ConditionKind.SIGNAL or r["verdict"] == "VOID":
                    continue
                tf = _eval_tf(s, c, trigger=trig)
                dd = doc.get("directions", {}).get(f"{c.name}@{tf}", {})
                if dd and not (allowed & {k for k, v in dd.items() if v > 0}):
                    dir_void.append({"condition": c.name, "tf": tf,
                                     "fires_by_direction": dd,
                                     "allowed_directions": sorted(allowed)})

        verdict_s = "VOID" if (void or dir_void) else ("THIN" if thin else "ALIVE")
        out.append({
            "strategy_id": s.strategy_id, "name": s.name, "group": s.group,
            "symbol": s.symbol, "primary_tf": s.primary_tf,
            "entry_tf": s.entry_tf, "execution_tf": s.execution_tf,
            "confirm_tfs": list(s.confirm_tfs),
            "n_conditions": len(s.conditions) + len(s.trigger_conditions),
            "verdict": verdict_s,
            "void_conditions": [f"{r['condition']}@{r['tf']}m" for r in void],
            "thin_conditions": [f"{r['condition']}@{r['tf']}m({r['fires']})"
                                for r in thin],
            "direction_void": dir_void,
            "unmeasured_conditions": [f"{r['condition']}@{r['tf']}m"
                                      for r in unmeasured],
            "min_fires": min((r["fires"] for _, _, r in rows
                              if r["fires"] is not None), default=None),
        })
    return out


def audit_summary(rows: Sequence[dict]) -> dict:
    """The number EF2-EF5 quote: what share of a population cannot trade."""
    n = len(rows)
    voids = [r for r in rows if r["verdict"] == "VOID"]
    cause = Counter()
    for r in voids:
        for c in r["void_conditions"]:
            cause[c] += 1
        for d in r["direction_void"]:
            cause[f"{d['condition']}@{d['tf']}m[direction]"] += 1
    by_group = Counter(r["group"] for r in voids)
    by_tf = Counter(r["primary_tf"] for r in voids)
    tot_tf = Counter(r["primary_tf"] for r in rows)
    return {
        "n_strategies": n,
        "n_void": len(voids),
        "pct_void": round(100.0 * len(voids) / max(1, n), 2),
        "n_thin": sum(1 for r in rows if r["verdict"] == "THIN"),
        "n_alive": sum(1 for r in rows if r["verdict"] == "ALIVE"),
        "void_causes": dict(cause.most_common()),
        "void_by_group": dict(by_group.most_common()),
        "void_by_primary_tf": {str(k): f"{by_tf.get(k, 0)}/{tot_tf[k]}"
                               for k in sorted(tot_tf)},
    }


def prefilter(strategies: Sequence[Strategy], doc: dict, *,
              denominator: str = "signal") -> Tuple[List[Strategy], List[dict]]:
    """The call site EF2-EF5 want: returns (tradeable strategies, audit rows).

    Anything VOID is removed **before measurement**, so it never enters a
    denominator, never enters a ranking, and never becomes a null that gets read
    as a market fact. The audit rows are kept so the removal is reportable -
    a VOID strategy is a finding about the generator, not a strategy that lost.
    """
    rows = audit(strategies, doc, denominator=denominator)
    bad = {r["strategy_id"] for r in rows if r["verdict"] == "VOID"}
    return [s for s in strategies if s.strategy_id not in bad], rows
