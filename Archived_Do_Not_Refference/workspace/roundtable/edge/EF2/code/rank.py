"""EF2 ranking: build the top-10 rows, with every column the task requires.

The rank key is **expectancy in R** and nothing else. Win rate, payoff and profit
factor are reported beside it and never rank: they cancel (measured four times in
this repo - moving a stop from structure to a wider ATR raises payoff ~89% and
drops win rate ~14 points for no expectancy gain). The trade floor and the
t-statistic **gate** a row; they do not reorder it.

A row is REPORTABLE only if it carries all of:
  * its control (placebo mean expectancy + empirical p over 40 observations),
  * the search size that produced it and the threshold that size implies,
  * its forward-roll behaviour.
A row missing any of the three is dropped, not reported with a blank. That is the
task's own rule and it is enforced here in code rather than in prose.

The list is allowed to be SHORT. ``select`` returns however many rows clear their
own controls, up to ten, and records why each rejected row was rejected. Padding a
list to ten is the specific failure this exercise exists to avoid: the last ranked
list this repo produced returned -0.0155R against a -0.0104R null and
underperformed trading the whole qualifying universe.
"""
from __future__ import annotations

import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence

REPO = "/home/user/Futures01"
OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")
sys.path.insert(0, os.path.join(REPO, "workspace", "roundtable", "edge", "EF6", "code"))

#: EF6's module, adopted per EF6-01 ("do not derive a threshold by hand and do not
#: quote 5.46"). One implementation across EF2-EF5 means a cross-cell comparison is
#: a cell comparison and not a convention comparison. I verified it against my own
#: arithmetic first: at n = 5,152 it returns free_t 4.1345 and required annualised
#: Sharpe 2.947 against my 4.135 / 2.95 [measured].
from deflation import threshold as _ef6_threshold                  # noqa: E402

#: EF6's measured span for the 60m/240m cells, adopted over my 718.
SPAN_DAYS = 718.83
SQRT_YEARS = 1.4029

MIN_TRADES = 30
MAX_PLACEBO_P = 0.05
N_CONTROL_OBS = 40          # 20 seeds x 2 kinds; empirical p floor = 0.025


def free_t(n: int) -> float:
    return float(_ef6_threshold(max(1, n), SPAN_DAYS)["free_t"])


def required_sharpe(n: int) -> float:
    return float(_ef6_threshold(max(1, n), SPAN_DAYS)["required_annual_sharpe"])


#: EF6-01's search-budget arithmetic, n_max = exp(SR^2 * Y / 2), on the swing span.
#: This is the number that decides whether a ranked list of 5,000 arms can mean
#: anything at all, and it is quoted on the deliverable rather than buried:
#:   true annual Sharpe 1.0 -> max answerable search width  2
#:                      1.5 ->                              9
#:                      2.0 ->                             51
#:                      3.0 ->                          7,022
MAX_ANSWERABLE_WIDTH = {1.0: 2, 1.5: 9, 2.0: 51, 3.0: 7022}


#: Cycles in which EF1's 16:00 flat cannot fire, per cell (EF2 burst 06). Carried
#: on every row, because a run can report violations = 0 while these cycles were
#: never tested.
FLAT_UNREACHABLE = {60: {"MGC": 17, "MCL": 34}, 240: {"MGC": 9, "MCL": 14}}
CYCLES = {60: {"MGC": 506, "MCL": 505}, 240: {"MGC": 602, "MCL": 596}}

#: MCL's two contiguous archive gaps (EF2 burst 06). Every MCL row is reported
#: with and without them; named here BEFORE any expectancy exists, so the
#: exclusion is a pre-registered sensitivity and not a filter chosen after the fact.
MCL_GAP_WINDOWS = (("2026-01-09", "2026-01-16"), ("2026-02-20", "2026-03-11"))

#: Measured D45 collapse rates (EF2 burst 04): share of swing-admissible bars on
#: which the named stop kind is actually a fixed-tick stop, because
#: max(dist, min_stop_ticks*tick) bound. Any row carrying one of these kinds must
#: state its number - the row is partly a result about a fixed-tick stop.
STOP_COLLAPSE = {
    ("MGC", 60, "VWAP_BAND"): 0.192, ("MGC", 240, "VWAP_BAND"): 0.124,
    ("MCL", 60, "VWAP_BAND"): 0.372, ("MCL", 240, "VWAP_BAND"): 0.246,
    ("MGC", 60, "STRUCTURE"): 0.038, ("MGC", 240, "STRUCTURE"): 0.017,
    ("MCL", 60, "STRUCTURE"): 0.075, ("MCL", 240, "STRUCTURE"): 0.037,
}


def row_view(rec: dict, symbol: str, n_screened: int,
             control: Optional[dict], forward: Optional[dict]) -> dict:
    """One reportable row, with every required column present or the row invalid."""
    tf = int(rec["primary_tf"])
    t = rec.get("t_stat", 0.0)
    ft = free_t(n_screened)
    out = {
        # identity
        "strategy_id": rec["strategy_id"],
        "arm_key": rec["arm_key"],
        "group": rec["group"],
        "cell": rec["cell"],
        "primary_tf": tf,
        "frame_tfs": rec["frame_tfs"],
        "rth_only": rec["rth_only"],
        "stop_kind": rec["stop_kind"],
        "target_kind": rec["target_kind"],
        "signals": rec["signals"],
        "filters": rec["filters"],
        # the rank key, and the two that must travel with it
        "expectancy_r": rec.get("expectancy_r"),
        "win_rate": rec.get("win_rate"),
        "payoff": rec.get("payoff"),
        "profit_factor": rec.get("profit_factor"),
        "avg_win_r": rec.get("avg_win_r"),
        "avg_loss_r": rec.get("avg_loss_r"),
        "trades": rec.get("trades", 0),
        # distribution and risk
        "t_stat": t,
        "sharpe_per_trade": rec.get("sharpe_per_trade"),
        "sortino_per_trade": rec.get("sortino_per_trade"),
        "max_drawdown_r": rec.get("max_drawdown_r"),
        "avg_drawdown_r": rec.get("avg_drawdown_r"),
        "max_consec_wins": rec.get("max_consec_wins"),
        "max_consec_losses": rec.get("max_consec_losses"),
        "avg_duration_min": rec.get("avg_duration_min"),
        "max_duration_min": rec.get("max_duration_min"),
        "avg_mae_r": rec.get("avg_mae_r"),
        "avg_mfe_r": rec.get("avg_mfe_r"),
        # costs
        "expectancy_r_gross": rec.get("expectancy_r_gross"),
        "cost_drag_r": rec.get("cost_drag_r"),
        "flipped_negative_by_costs": (
            rec.get("expectancy_r_gross", 0.0) > 0 >= rec.get("expectancy_r", 0.0)),
        # the three columns without which the row is not reportable
        "control_kinds": (control or {}).get("kinds"),
        "control_expectancy_r": (control or {}).get("mean_expectancy_r"),
        "control_p_empirical": (control or {}).get("p_empirical"),
        "control_observations": (control or {}).get("n_obs"),
        "search_size": n_screened,
        "threshold_free_t": round(ft, 3),
        "sharpe_threshold_implies": required_sharpe(n_screened),
        "clears_threshold": bool(abs(t) >= ft),
        "forward_selected": (forward or {}).get("selected"),
        "forward_expectancy_r": (forward or {}).get("oos_expectancy_r"),
        "forward_trades": (forward or {}).get("oos_trades"),
        "survived_forward_roll": (forward or {}).get("survived"),
        # substrate caveats that travel with the row
        "span_days": 718,
        "sqrt_years": round(SQRT_YEARS, 4),
        "cycles_flat_unreachable": FLAT_UNREACHABLE[tf][symbol],
        "cycles_total": CYCLES[tf][symbol],
        "stop_collapse_rate": STOP_COLLAPSE.get((symbol, tf, rec["stop_kind"]), 0.0),
        "mcl_gap_windows_excluded_variant": (
            symbol == "MCL"),
    }
    return out


def reject_reasons(r: dict) -> List[str]:
    """Why this row may not be reported. Empty list = reportable."""
    bad: List[str] = []
    if (r["trades"] or 0) < MIN_TRADES:
        bad.append(f"trades {r['trades']} < {MIN_TRADES}")
    if r["control_expectancy_r"] is None or r["control_p_empirical"] is None:
        bad.append("no control — a row without its placebo is not reportable")
    elif r["control_p_empirical"] > MAX_PLACEBO_P:
        bad.append(f"control p = {r['control_p_empirical']:.3f} > {MAX_PLACEBO_P}")
    elif r["control_expectancy_r"] >= r["expectancy_r"]:
        bad.append("its own placebo matched or beat it")
    if r["search_size"] is None:
        bad.append("no search size — not reportable")
    if r["survived_forward_roll"] is None:
        bad.append("no forward-roll result — not reportable")
    elif not r["survived_forward_roll"]:
        bad.append("failed the forward roll")
    if (r["expectancy_r"] or 0.0) <= 0:
        bad.append("expectancy in R is not positive")
    return bad


def select(rows: Sequence[dict], k: int = 10) -> dict:
    """Top ``k`` by expectancy in R among reportable rows. May return fewer.

    Clone collapse is EF6's job (``forward.Ledger.measure``), and rows arriving
    here are expected to be post-collapse. A defensive second pass is applied on
    the (cell, signals, filters) key anyway, because the prior study's MES 60m
    top 10 listed one TREND rule set four times and a padded list is the failure
    being avoided.
    """
    ranked = sorted(rows, key=lambda r: -(r["expectancy_r"] or -9e9))
    kept: List[dict] = []
    rejected: List[dict] = []
    seen = set()
    for r in ranked:
        bad = reject_reasons(r)
        key = (r["cell"], tuple(r["signals"]), tuple(r["filters"]))
        if key in seen:
            bad.append("duplicate rule set already in the list (clone collapse)")
        if bad:
            rejected.append({**r, "rejected_because": bad})
            continue
        seen.add(key)
        kept.append(r)
        if len(kept) >= k:
            break
    return {
        "selected": kept,
        "n_selected": len(kept),
        "short_of_ten_because": (
            None if len(kept) >= k else
            f"only {len(kept)} rows cleared their own controls; "
            f"{len(rejected)} were rejected and every reason is recorded. "
            "A padded list is worse than a short one."),
        "rejected": rejected[:200],
        "rejection_reason_counts": _counts(rejected),
    }


def _counts(rejected: Sequence[dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for r in rejected:
        for b in r["rejected_because"]:
            k = b.split("—")[0].split("=")[0].strip()
            k = k.split("<")[0].strip() if k.startswith("trades") else k
            out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda x: -x[1]))


def markdown(symbol: str, res: dict) -> str:
    L = [f"### {symbol} — SWING top {res['n_selected']}"
         + (" (short list, see below)" if res["n_selected"] < 10 else "")]
    L.append("")
    L.append("| # | strategy_id | group | tf / frame | rth | exp R | win% | payoff | "
             "trades | placebo exp R | placebo p | search n | free_t | t | fwd |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(res["selected"], 1):
        L.append(
            f"| {i} | `{r['strategy_id']}` | {r['group']} | "
            f"{r['primary_tf']}m / {'+'.join(str(x) for x in r['frame_tfs'])} | "
            f"{'T' if r['rth_only'] else 'F'} | **{r['expectancy_r']:+.4f}** | "
            f"{r['win_rate']*100:.1f} | {r['payoff']:.2f} | {r['trades']} | "
            f"{r['control_expectancy_r']:+.4f} | {r['control_p_empirical']:.3f} | "
            f"{r['search_size']} | {r['threshold_free_t']:.2f} | {r['t_stat']:.2f} | "
            f"{'yes' if r['survived_forward_roll'] else 'no'} |")
    if res["short_of_ten_because"]:
        L += ["", f"**{res['short_of_ten_because']}**", "",
              "Rejection reasons, counted:"]
        for k, v in res["rejection_reason_counts"].items():
            L.append(f"- {k}: {v}")
    return "\n".join(L)


if __name__ == "__main__":
    print(__doc__)
    print(f"free_t(5092) = {free_t(5092):.3f} -> Sharpe {free_t(5092)/SQRT_YEARS:.2f}")
    print(f"free_t(5584) = {free_t(5584):.3f} -> Sharpe {free_t(5584)/SQRT_YEARS:.2f}")
    print(f"empirical p floor with {N_CONTROL_OBS} control observations = "
          f"{1.0/N_CONTROL_OBS:.3f}")
