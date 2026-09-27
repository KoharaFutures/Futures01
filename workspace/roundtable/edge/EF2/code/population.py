"""EF2 Burst 03: construct and record the swing population, VOID-filtered.

Four design decisions, each of which is a place a silent confound would live.

**1. All thirteen groups, explicitly, on both symbols.** ``generate_combinations``
with ``groups=None`` falls through to ``groups_for(symbol, ...)``
[repo-verified: combinator.py:489-494], which returns **6 groups for MGC and
None (=13) for MCL** [measured: profiles.groups_for]. Letting it default would
silently narrow MGC to 6/13 of the strategy space while MCL got all 13, and any
MGC-vs-MCL difference would partly be that. Passed explicitly.

**2. Rule sets are drawn ONCE per symbol and instantiated across all four
cells.** ``generate_combinations`` builds ``rule_sets`` as the product of names x
timeframes x exits and then ``rng.sample``s it [repo-verified:
combinator.py:539-560], so calling it with ``[60]`` and with ``[60,240]`` draws
*different* rule sets. Comparing "60m alone" against "60m in a group" that way
compares two unrelated samples and attributes the difference to the frame -
exactly D14's shape, which made MES and MGC 60m share 0 of 204 rule sets. Here
one draw is rebuilt in every cell, so a between-cell difference is a cell
difference.

Rule sets are drawn per SYMBOL, not shared across symbols: the brief's
independence rule, and ``strategies_for_symbols``' own docstring forbids a
cross-symbol league table [repo-verified: combinator.py:646-676].

**3. ``rth_only`` is a paired arm, not an inherited default.** It is ``True`` on
100% of generated strategies and MGC/MCL RTH sits wholly inside one 18:00->16:00
cycle, so with ``True`` the overnight regime is unreachable for entries (Burst 01
section 2b). Both arms are built from the same rule set.

**4. D48 discipline, asserted rather than trusted.** Every ``dataclasses.replace``
on a ``Strategy`` passes ``_id=None``, and every emission asserts the id is not
already in the index. ``generate_strategies`` has already read ``strategy_id``
in its dedupe [repo-verified: combinator.py:719], so every strategy it returns
arrives with ``_id`` populated and a bare ``replace`` would inherit it.
"""
from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import replace
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

REPO = "/home/user/Futures01"
if REPO not in sys.path:
    sys.path.insert(0, REPO)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from futures_agents.strategies.base import Strategy, StrategyFilters   # noqa: E402
from futures_agents.strategies.combinator import (                     # noqa: E402
    TEMPLATES, CombinationSpec, TEMPLATES_BY_GROUP, _build_strategy,
    exits_for, generate_combinations)

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")
ALL_GROUPS = tuple(t.group for t in TEMPLATES)
SYMBOLS = ("MGC", "MCL")

#: cell key -> (timeframes of the frame, primary_tf, confirm_tfs)
CELL_SPEC: Dict[str, Tuple[Tuple[int, ...], int, Tuple[int, ...]]] = {
    "f60__p60":      ((60,),      60,  ()),
    "f60_240__p60":  ((60, 240),  60,  (240,)),
    "f240__p240":    ((240,),     240, ()),
    "f60_240__p240": ((60, 240),  240, ()),
}

#: The seed EF2 uses. Fixed here so the population is reproducible and so the
#: search size below is the real one - a re-draw with a different seed is a
#: second search and would have to be added to n.
SEED = 20260927
MAX_TOTAL = 2000


# ------------------------------------------------------------------ rule sets
def rule_sets_for(symbol: str, max_total: int = MAX_TOTAL,
                  seed: int = SEED) -> List[Tuple[str, Tuple[str, ...],
                                                  Tuple[str, ...], int]]:
    """The canonical draw: (group, signal names, filter names, exit index).

    Drawn from a ``[60]`` frame purely so the sampler sees one timeframe per
    rule set and the draw is not diluted across two; the timeframe is then
    supplied per cell.
    """
    specs = generate_combinations(symbol, [60], groups=list(ALL_GROUPS),
                                 max_total=max_total, seed=seed)
    seen = set()
    out = []
    for s in specs:
        k = (s.group, s.signal_conditions, s.filter_conditions, s.exit_index)
        if k in seen:
            continue
        seen.add(k)
        out.append(k)
    out.sort()
    return out


def build(symbol: str, cell: str, rs: Tuple[str, Tuple[str, ...],
                                            Tuple[str, ...], int],
          rth_only: bool) -> Optional[Strategy]:
    group, sigs, filts, ei = rs
    tfs, ptf, confirm = CELL_SPEC[cell]
    template = TEMPLATES_BY_GROUP[group]
    base_filters = template.filters                     # StrategyFilters
    spec = CombinationSpec(
        symbol=symbol.upper(), group=group, primary_tf=ptf,
        confirm_tfs=confirm, signal_conditions=sigs, filter_conditions=filts,
        exit_index=ei, filters=base_filters, execution_tf=None)
    st = _build_strategy(spec)
    if st is None:
        return None
    if st.filters.rth_only == rth_only:
        return st
    # D48: _id=None, always. The outer Strategy caches; the inner
    # StrategyFilters does not and recomputes its identity correctly.
    return replace(st, filters=replace(st.filters, rth_only=rth_only),
                   _id=None)


# ------------------------------------------------------------------ VOID gate
def void_sets() -> Dict[str, Dict[int, set]]:
    """cell key -> bound timeframe -> set of VOID condition names."""
    with open(os.path.join(OUT, "census.json")) as fh:
        cen = json.load(fh)
    out: Dict[str, Dict[int, set]] = {}
    for sym in SYMBOLS:
        for cell, (tfs, ptf, confirm) in CELL_SPEC.items():
            fk = f"{sym}:f" + "_".join(str(t) for t in tfs)
            rows = cen["frames"][fk]["rows"]
            per_tf: Dict[int, set] = defaultdict(set)
            for r in rows:
                if r["verdict"] != "LIVE":
                    per_tf[r["bound_tf"]].add(r["condition"])
            out[f"{sym}:{cell}"] = dict(per_tf)
    return out


def void_reason(st: Strategy, cell_key: str,
                voids: Dict[str, Dict[int, set]]) -> List[str]:
    """Every (condition, bound tf) in this strategy that cannot fire here."""
    per_tf = voids[cell_key]
    bad = []
    for c in st.conditions:
        tf = c.timeframe or st.primary_tf
        if c.name in per_tf.get(tf, set()):
            bad.append(f"{c.name}@{tf}m")
    return bad


# ------------------------------------------------------------------ assembly
def assemble(max_total: int = MAX_TOTAL, seed: int = SEED) -> dict:
    voids = void_sets()
    pop: Dict[str, Dict[str, Strategy]] = {s: {} for s in SYMBOLS}
    index: Dict[str, Dict[str, dict]] = {s: {} for s in SYMBOLS}
    removed: Dict[str, List[dict]] = {s: [] for s in SYMBOLS}
    build_fail: Dict[str, int] = {s: 0 for s in SYMBOLS}
    dup_collisions: Dict[str, int] = {s: 0 for s in SYMBOLS}
    rs_by_symbol: Dict[str, list] = {}

    for sym in SYMBOLS:
        rss = rule_sets_for(sym, max_total, seed)
        rs_by_symbol[sym] = rss
        for rs in rss:
            for cell in CELL_SPEC:
                ck = f"{sym}:{cell}"
                for rth in (True, False):
                    st = build(sym, cell, rs, rth)
                    if st is None:
                        build_fail[sym] += 1
                        continue
                    bad = void_reason(st, ck, voids)
                    arm_key = f"{ck}|rth{int(rth)}|{st.strategy_id}"
                    rec = {
                        "arm_key": arm_key, "cell": ck, "symbol": sym,
                        "strategy_id": st.strategy_id, "name": st.name,
                        "group": st.group, "primary_tf": st.primary_tf,
                        "confirm_tfs": list(st.confirm_tfs),
                        "frame_tfs": list(CELL_SPEC[cell][0]),
                        "rth_only": rth, "exit_index": rs[3],
                        "stop_kind": st.exit.stop_kind.value,
                        "target_kind": st.exit.target_kind.value,
                        "stop_mult": st.exit.stop_mult,
                        "n_signals": len(st.signal_conditions),
                        "n_filters": len(st.filter_conditions),
                        "signals": [c.label for c in st.signal_conditions],
                        "filters": [c.label for c in st.filter_conditions],
                        "rule_set": [rs[0], list(rs[1]), list(rs[2]), rs[3]],
                        "void": bad,
                    }
                    if bad:
                        removed[sym].append(rec)
                        continue
                    # D48 gate: arm ids must be distinct within a cell+arm.
                    if arm_key in index[sym]:
                        dup_collisions[sym] += 1
                        continue
                    index[sym][arm_key] = rec
                    pop[sym][arm_key] = st

    # ---- id-uniqueness audit, the D48 assertion, per cell and arm
    audit = {}
    for sym in SYMBOLS:
        by_cell_arm: Dict[Tuple[str, bool], Counter] = defaultdict(Counter)
        for rec in index[sym].values():
            by_cell_arm[(rec["cell"], rec["rth_only"])][rec["strategy_id"]] += 1
        worst = 0
        colliding = []
        for k, c in by_cell_arm.items():
            for sid, n in c.items():
                if n > 1:
                    colliding.append({"cell": k[0], "rth_only": k[1],
                                      "strategy_id": sid, "count": n})
                worst = max(worst, n)
        audit[sym] = {"max_arms_sharing_an_id_within_cell_and_arm": worst,
                      "collisions": colliding}
        assert worst <= 1, f"D48: {sym} has colliding arm ids: {colliding[:5]}"

    # ---- the cross-cell id note, which is NOT a collision
    cross = {}
    for sym in SYMBOLS:
        sid_cells = defaultdict(set)
        for rec in index[sym].values():
            sid_cells[rec["strategy_id"]].add((rec["cell"], rec["rth_only"]))
        cross[sym] = sum(1 for v in sid_cells.values() if len(v) > 1)

    return {
        "seed": seed, "max_total": max_total,
        "groups": list(ALL_GROUPS),
        "cells": {k: {"frame_tfs": list(v[0]), "primary_tf": v[1],
                      "confirm_tfs": list(v[2])} for k, v in CELL_SPEC.items()},
        "rule_sets_per_symbol": {s: len(rs_by_symbol[s]) for s in SYMBOLS},
        "population": {s: len(index[s]) for s in SYMBOLS},
        "removed_by_void": {s: len(removed[s]) for s in SYMBOLS},
        "build_failures": build_fail,
        "duplicate_arm_keys_dropped": dup_collisions,
        "id_uniqueness_audit": audit,
        "strategy_ids_appearing_in_more_than_one_cell_or_arm": cross,
        "index": index, "removed": removed,
        "_objects": pop,
    }


def summarise(res: dict) -> str:
    L: List[str] = []
    for sym in SYMBOLS:
        idx = res["index"][sym]
        rem = res["removed"][sym]
        n = len(idx)
        L.append(f"### {sym}")
        L.append(f"- rule sets drawn: **{res['rule_sets_per_symbol'][sym]}** "
                 f"(seed {res['seed']}, max_total {res['max_total']}, 13 groups)")
        L.append(f"- candidate arms = rule sets x 4 cells x 2 rth arms = "
                 f"**{res['rule_sets_per_symbol'][sym]*8}**")
        L.append(f"- removed by the VOID gate: **{len(rem)}** "
                 f"({len(rem)/max(1,len(rem)+n)*100:.1f}% of candidates)")
        L.append(f"- build failures (`_build_strategy` returned None): "
                 f"{res['build_failures'][sym]}")
        L.append(f"- **population: {n} arms**, free_t = "
                 f"sqrt(2 ln {n}) = **{math.sqrt(2*math.log(max(2,n))):.3f}**, "
                 f"Sharpe needed on 1.402 sqrt-years = "
                 f"**{math.sqrt(2*math.log(max(2,n)))/1.402:.2f}**")
        by_cell = Counter(r["cell"] for r in idx.values())
        by_cell_rm = Counter(r["cell"] for r in rem)
        L.append("")
        L.append("| cell | kept | removed VOID | removal rate | n groups kept |")
        L.append("|---|---|---|---|---|")
        for cell in CELL_SPEC:
            ck = f"{sym}:{cell}"
            k, r = by_cell[ck], by_cell_rm[ck]
            g = len({x["group"] for x in idx.values() if x["cell"] == ck})
            L.append(f"| `{cell}` | {k} | {r} | "
                     f"{r/max(1,k+r)*100:.1f}% | {g}/13 |")
        L.append("")
        cause = Counter()
        for r in rem:
            for b in r["void"]:
                cause[b.split("@")[0]] += 1
        L.append("VOID causes by condition (arm count, a strategy may carry two):")
        for name, c in cause.most_common():
            L.append(f"- `{name}`: {c}")
        gone = Counter()
        for r in rem:
            gone[(r["cell"], r["group"])] += 1
        killed_groups = []
        for cell in CELL_SPEC:
            ck = f"{sym}:{cell}"
            kept_groups = {x["group"] for x in idx.values() if x["cell"] == ck}
            for g in ALL_GROUPS:
                if g not in kept_groups:
                    killed_groups.append(f"{cell}/{g}")
        L.append("")
        L.append(f"Groups with **zero** surviving arms: "
                 f"{', '.join('`'+x+'`' for x in killed_groups) or 'none'}")
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    res = assemble()
    objs = res.pop("_objects")
    with open(os.path.join(OUT, "population.json"), "w") as fh:
        json.dump(res, fh, indent=1)
    print(summarise(res))
    sys.stderr.write(f"population written: "
                     f"{ {k: len(v) for k, v in res['index'].items()} }\n")
