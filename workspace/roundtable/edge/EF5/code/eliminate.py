"""EF5 -- what the census removes from the declared population, two ways.

(a) **VOID-carrier count** (R1's method, Addendum B / the 19.0% figure). A
    strategy is a VOID carrier when it holds at least one condition whose firing
    count is **0** at the timeframe that condition is actually evaluated at,
    under the gate that arm actually runs under. ``Strategy.evaluate`` is a
    strict AND with no ``min_signals`` (``base.py:670-684``), so one such
    condition makes the whole strategy structurally zero-trade.

(b) **Zero-signal count** (the direct measure). Run ``Strategy.evaluate`` over
    every admissible bar and count strategies that never once produce a signal.
    This is strictly stronger than (a): it also catches provably-empty filter
    conjunctions (D-V2: ``volatility_compressed`` AND ``volatility_expanding``),
    direction disagreements that can never resolve (D25:
    ``range_position_extreme`` inside REVERSAL), and ``StrategyFilters`` gates.

No entries, no exits, no P&L. This is a detector census, not a backtest. Its
whole purpose is to separate this programme's two nulls -- "we measured absence"
from "the detector never fired" (BRIEF.md, VOID vocabulary).
"""
from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict
from typing import Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from ef5_data import PRIMARY_TFS, REPO, SYMBOLS, build_frame, in_session  # noqa: E402
from population import ARMS, base_population, session_arm                 # noqa: E402
from futures_agents.strategies.base import ConditionKind                   # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")


def void_set(census: dict, cell: str, gate: str) -> Dict[int, set]:
    """tf -> set of condition names with ZERO fires at that tf under ``gate``."""
    c = census[cell]
    names = set(c["kinds"])
    out = {}
    for tf_s, fires in c["fires"][gate].items():
        out[int(tf_s)] = {n for n in names if fires.get(n, [0])[0] == 0}
    return out


def run_cell(symbol: str, primary_tf: int, census: dict) -> dict:
    cell = f"{symbol}_{primary_tf}m"
    frame = build_frame(symbol, primary_tf)
    base = base_population(symbol, primary_tf)
    arms = {"RTH": base, "SESSION": session_arm(base)}
    gate_of = {"RTH": "RTH", "SESSION": "SESSION"}

    res = {"symbol": symbol, "primary_tf": primary_tf, "arms": {}}

    # ---- (a) VOID carriers, per arm -------------------------------------
    for arm, strats in arms.items():
        voids = void_set(census, cell, gate_of[arm])
        carriers, causes = [], Counter()
        by_group_tot, by_group_void = Counter(), Counter()
        for s in strats:
            by_group_tot[s.group] += 1
            bad = []
            for c in s.conditions:
                tf = c.timeframe or s.primary_tf
                if c.name in voids.get(tf, ()):
                    bad.append(f"{c.name}@{tf}m")
            if bad:
                carriers.append(s.strategy_id)
                by_group_void[s.group] += 1
                for b in bad:
                    causes[b] += 1
        res["arms"][arm] = {
            "n": len(strats),
            "void_carriers": len(carriers),
            "void_carrier_frac": round(len(carriers) / len(strats), 4),
            "void_causes": dict(causes),
            "void_by_group": {g: [by_group_void[g], by_group_tot[g]]
                              for g in sorted(by_group_tot)},
        }

    # ---- (b) zero-signal census, per arm --------------------------------
    n_bars = len(frame.base)
    for arm, strats in arms.items():
        counts = defaultdict(int)
        admissible = 0
        for i in range(n_bars):
            snap = frame.snapshot(i)
            if snap is None:
                continue
            # Under the programme rule no position may be OPENED inside
            # 16:00-18:00 ET, so those bars are inadmissible as signal bars in
            # BOTH arms. (In the RTH arm they are already excluded by is_rth.)
            if not in_session(frame.base.bars[i].ts):
                continue
            admissible += 1
            cache = {}
            for s in strats:
                if s.evaluate(snap, cache) is not None:
                    counts[s.strategy_id] += 1
        zero = [s.strategy_id for s in strats if counts[s.strategy_id] == 0]
        sig = [counts[s.strategy_id] for s in strats]
        sig_sorted = sorted(sig)
        gz = [x for x in sig_sorted if x > 0]
        a = res["arms"][arm]
        a["admissible_bars"] = admissible
        a["zero_signal"] = len(zero)
        a["zero_signal_frac"] = round(len(zero) / len(strats), 4)
        a["signals_median_nonzero"] = (gz[len(gz) // 2] if gz else 0)
        a["signals_total"] = sum(sig)
        a["zero_by_group"] = dict(Counter(
            s.group for s in strats if counts[s.strategy_id] == 0))
        a["lt20_signal"] = sum(1 for x in sig if x < 20)
        # VOID carriers must be a SUBSET of zero-signal strategies. If not, the
        # census and the evaluator disagree and one of them is wrong.
        vc = set(res["arms"][arm].pop("_carriers", []) or [])
        a["_zero_ids_sample"] = zero[:5]
        print(f"  {symbol} {primary_tf}m [{arm}] n={len(strats)} "
              f"admissible_bars={admissible} void_carriers={a['void_carriers']} "
              f"zero_signal={a['zero_signal']} ({a['zero_signal_frac']:.1%}) "
              f"<20 signals={a['lt20_signal']}", flush=True)
        del vc
    return res


def main() -> None:
    with open(os.path.join(OUT, "census.json")) as fh:
        census = json.load(fh)
    out = {}
    for sym in SYMBOLS:
        for tf in PRIMARY_TFS:
            out[f"{sym}_{tf}m"] = run_cell(sym, tf, census)
    with open(os.path.join(OUT, "elimination.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", os.path.join(OUT, "elimination.json"))


if __name__ == "__main__":
    main()
