"""EF6 — the four gates every row that reaches a top 10 has to pass.

A row failing any of these is **not a weaker row. It is not a result.** The
report says which gate killed it, by name.

    G1  FIRING       does every condition in it fire, at the timeframe it is
                     actually evaluated on, on a bar that could legally be
                     entered under 18:00->16:00?
    G2  PLACEBO      does it beat its own control - same exits, filters, scope
                     and sizing, signal layer replaced, count-matched on LEGAL
                     signals?
    G3  THRESHOLD    does its t clear free_t for the search that produced it,
                     on the span it was measured on?
    G4  FORWARD      does it survive the strictly-causal roll - ranked on the
                     trailing window, traded in the next period?

## The test used in G2, named, because `T.ab` is not it

`D28`: ``toolkit.ab`` inflates z by roughly 3.3x, so no comparative claim here
routes through it. G2 uses a **two-sided label permutation test on the
difference in mean net R**, with the label permuted in **18:00->16:00 cycle
blocks** rather than per trade. Trades inside one cycle share market state, so a
per-trade permutation would treat correlated observations as independent and
understate the null's spread - the same error `T.ab` makes by a different route.
Welch's t on the two R series is reported beside it as a distributional
cross-check, never as the headline.

The base and its placebo are **not** paired trade-by-trade: they trade different
bars by construction. So this is an unpaired two-sample test on matched
*populations*, and that is stated rather than implied.

## What G2 cannot do

A placebo comparison on a base with 20-60 trades has very little power. The
honest output is therefore three-valued: ``BEATS``, ``LOSES``, and
``UNDERPOWERED`` - the last when the minimum detectable difference at 80% power
exceeds the observed edge. Reporting ``UNDERPOWERED`` as ``BEATS`` is how a
placebo gate becomes decorative.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

import deflation as D
import firing
import window as W

__all__ = [
    "cycle_block_permutation", "welch", "min_detectable_difference",
    "gate_firing", "gate_placebo", "gate_threshold", "gate_forward", "attack",
]


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------

def cycle_block_permutation(a_r: Sequence[float], a_cyc: Sequence[str],
                            b_r: Sequence[float], b_cyc: Sequence[str],
                            *, n_perm: int = 5000, seed: int = 11) -> dict:
    """Two-sided label permutation on mean(a) - mean(b), permuted by cycle block.

    Every trade carries the 18:00->16:00 cycle it entered in. A permutation
    reassigns whole cycles between the two labels, so trades that shared market
    state move together. This is the test named in G2.
    """
    a_r = np.asarray(list(a_r), dtype=float)
    b_r = np.asarray(list(b_r), dtype=float)
    if len(a_r) < 2 or len(b_r) < 2:
        return {"test": "cycle_block_permutation", "n_a": len(a_r), "n_b": len(b_r),
                "observed_diff": None, "p_two_sided": None,
                "note": "fewer than 2 trades on one side"}
    obs = float(a_r.mean() - b_r.mean())
    # Pool trades by (label, cycle).
    blocks: Dict[str, List[Tuple[int, float]]] = defaultdict(list)
    for r, c in zip(a_r, a_cyc):
        blocks[c].append((0, float(r)))
    for r, c in zip(b_r, b_cyc):
        blocks[c].append((1, float(r)))
    keys = sorted(blocks)
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(n_perm):
        flip = rng.integers(0, 2, size=len(keys))
        sa, na, sb, nb = 0.0, 0, 0.0, 0
        for f, k in zip(flip, keys):
            for lab, r in blocks[k]:
                lab2 = lab if f == 0 else 1 - lab
                if lab2 == 0:
                    sa += r
                    na += 1
                else:
                    sb += r
                    nb += 1
        if na and nb and abs(sa / na - sb / nb) >= abs(obs) - 1e-12:
            hits += 1
    return {"test": "cycle_block_permutation (two-sided, blocks = 18:00->16:00 cycles)",
            "n_a": int(len(a_r)), "n_b": int(len(b_r)),
            "n_blocks": len(keys), "n_perm": int(n_perm),
            "mean_a": round(float(a_r.mean()), 4),
            "mean_b": round(float(b_r.mean()), 4),
            "observed_diff": round(obs, 4),
            "p_two_sided": round((hits + 1) / (n_perm + 1), 4)}


def welch(a: Sequence[float], b: Sequence[float]) -> dict:
    """Welch's unequal-variance t, as a distributional cross-check only."""
    a = np.asarray(list(a), dtype=float)
    b = np.asarray(list(b), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return {"test": "welch", "t": None, "df": None}
    va, vb = a.var(ddof=1), b.var(ddof=1)
    se = math.sqrt(va / len(a) + vb / len(b))
    if se <= 0:
        return {"test": "welch", "t": None, "df": None}
    t = float((a.mean() - b.mean()) / se)
    df = (va / len(a) + vb / len(b)) ** 2 / (
        (va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))
    return {"test": "welch (unpaired, unequal variance)", "t": round(t, 3),
            "df": round(float(df), 1)}


def min_detectable_difference(a: Sequence[float], b: Sequence[float],
                              *, power: float = 0.80, alpha: float = 0.05) -> Optional[float]:
    """Smallest difference in mean R this comparison could have detected.

    Two-sided, normal approximation: ``(z_{1-a/2} + z_{power}) * se``.
    A gate whose MDD exceeds the observed edge is UNDERPOWERED, not passed.
    """
    a = np.asarray(list(a), dtype=float)
    b = np.asarray(list(b), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return None
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    z_a = 1.959964 if abs(alpha - 0.05) < 1e-9 else _z(1 - alpha / 2)
    z_p = 0.8416212 if abs(power - 0.80) < 1e-9 else _z(power)
    return round((z_a + z_p) * se, 4)


def _z(p: float) -> float:
    """Inverse standard normal CDF, Acklam's rational approximation."""
    if not 0.0 < p < 1.0:
        return float("nan")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, pu = 0.02425, 1 - 0.02425
    if p < pl:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > pu:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


# --------------------------------------------------------------------------
# the four gates
# --------------------------------------------------------------------------

def gate_firing(strategy, census_doc: dict) -> dict:
    rows = firing.audit([strategy], census_doc)
    r = rows[0]
    return {"gate": "G1 FIRING", "verdict": r["verdict"],
            "pass": r["verdict"] != "VOID",
            "void_conditions": r["void_conditions"],
            "thin_conditions": r["thin_conditions"],
            "direction_void": r["direction_void"],
            "unmeasured_conditions": r["unmeasured_conditions"],
            "min_fires": r["min_fires"],
            "reason": ("a condition fires on 0 legal-entry bars; "
                       "Strategy.evaluate is a strict AND so the row cannot trade"
                       if r["verdict"] == "VOID" else "")}


def gate_placebo(base_trades, placebo_trades, *, n_perm: int = 5000) -> dict:
    """base_trades / placebo_trades: sequences of (entry_ts, net_r)."""
    a_r = [t[1] for t in base_trades]
    a_c = [W.cycle_id(t[0]) for t in base_trades]
    b_r = [t[1] for t in placebo_trades]
    b_c = [W.cycle_id(t[0]) for t in placebo_trades]
    perm = cycle_block_permutation(a_r, a_c, b_r, b_c, n_perm=n_perm)
    w = welch(a_r, b_r)
    mdd = min_detectable_difference(a_r, b_r)
    diff = perm.get("observed_diff")
    if diff is None:
        verdict, ok = "NO TEST", False
    elif mdd is not None and abs(diff) < mdd:
        verdict, ok = "UNDERPOWERED", False
    elif diff > 0 and (perm["p_two_sided"] or 1.0) <= 0.05:
        verdict, ok = "BEATS", True
    elif diff <= 0:
        verdict, ok = "LOSES", False
    else:
        verdict, ok = "NOT SEPARATED", False
    return {"gate": "G2 PLACEBO", "verdict": verdict, "pass": ok,
            "permutation": perm, "welch": w,
            "min_detectable_diff_R_at_80pct_power": mdd,
            "count_match": {"base_trades": len(a_r), "placebo_trades": len(b_r),
                            "ratio": round(len(b_r) / max(1, len(a_r)), 3)},
            "reason": ("the observed edge is smaller than the smallest "
                       "difference this comparison could detect"
                       if verdict == "UNDERPOWERED" else "")}


def gate_threshold(t_observed: float, n_screened: int, symbol: str,
                   timeframes, *, preregistered: bool = False) -> dict:
    span = D.group_span_days(symbol, [timeframes] if isinstance(timeframes, int)
                             else list(timeframes))
    v = D.verdict(t_observed, n_screened, span, preregistered=preregistered)
    return {"gate": "G3 THRESHOLD", "verdict": "CLEARS" if v["clears"] else "BELOW",
            "pass": bool(v["clears"]), **v,
            "reason": ("" if v["clears"] else
                       f"t={v['t_observed']} vs free_t({n_screened})="
                       f"{v['threshold_t']} on {v['span_days']}d; clearing it "
                       f"needs an annualised Sharpe of "
                       f"{v['required_annual_sharpe']}")}


def gate_forward(roll_result: dict) -> dict:
    t = roll_result.get("topk_exp_r")
    u = roll_result.get("universe_exp_r")
    z = roll_result.get("z_vs_null")
    vac = roll_result.get("folds_where_topk_is_the_whole_universe", "0 of 0")
    nv, nt = (int(x) for x in vac.split(" of "))
    fails = []
    if nt and nv == nt:
        fails.append("the top-k was the whole qualifying universe in every fold "
                     "- no selection took place")
    if t is None:
        fails.append("no fold traded")
    else:
        if u is not None and t <= u:
            fails.append(f"top-k {t}R <= universe {u}R - selecting was worse "
                         "than not selecting")
        if z is not None and z <= 0:
            fails.append(f"top-k at or below the no-edge null (z={z})")
    return {"gate": "G4 FORWARD", "verdict": "SURVIVES" if not fails else "FAILS",
            "pass": not fails, "reasons": fails,
            "topk_exp_r": t, "universe_exp_r": u, "randomk_exp_r":
                roll_result.get("randomk_exp_r"), "z_vs_null": z,
            "folds_traded": roll_result.get("folds_traded"),
            "folds_where_topk_is_the_whole_universe": vac}


def attack(row: dict) -> dict:
    """Run every gate that has its inputs, and name what killed the row.

    ``row`` keys, all optional except ``id``:
      ``strategy``, ``census``          -> G1
      ``base_trades``, ``placebo_trades`` -> G2
      ``t``, ``n_screened``, ``symbol``, ``timeframes`` -> G3
      ``roll``                          -> G4
    """
    gates = []
    if row.get("strategy") is not None and row.get("census") is not None:
        gates.append(gate_firing(row["strategy"], row["census"]))
    if row.get("base_trades") and row.get("placebo_trades"):
        gates.append(gate_placebo(row["base_trades"], row["placebo_trades"]))
    if row.get("t") is not None and row.get("symbol"):
        gates.append(gate_threshold(row["t"], row.get("n_screened", 2),
                                    row["symbol"], row.get("timeframes"),
                                    preregistered=row.get("preregistered", False)))
    if row.get("roll"):
        gates.append(gate_forward(row["roll"]))
    killed = [g["gate"] for g in gates if not g["pass"]]
    return {"id": row.get("id"), "gates": gates,
            "gates_run": [g["gate"] for g in gates],
            "gates_missing": [g for g in ("G1 FIRING", "G2 PLACEBO",
                                          "G3 THRESHOLD", "G4 FORWARD")
                              if g not in {x["gate"] for x in gates}],
            "killed_by": killed,
            "verdict": "NOT A RESULT" if killed else
                       ("PASSED EVERY GATE RUN" if gates else "UNTESTED")}
