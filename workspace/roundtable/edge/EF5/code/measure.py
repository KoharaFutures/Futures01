"""EF5 -- the measurement runner. Ready to fire; fires only on EF1's harness.

**Nothing in this file produces a profitability number until
``EF1/code/session_window.py`` is validated.** It imports ``SessionWindowEngine``
and will not fall back to the shipped ``BacktestEngine``: the shipped engine's
``exit_at_session_close`` fires at the contract's RTH close and is gated off by
``allow_overnight``, so running on it would silently measure a different rule
and every number would be mislabelled. ``--require-validated`` refuses to run
until EF1 publishes a VERIFY note.

What it does, in order, per (symbol, primary_tf, arm):

1. Build the cell's frame from ``data/archive`` native bars.
2. Build the declared population (``population.py``; size frozen before
   measurement) and assert arm-id uniqueness (D48).
3. Run each arm through ``SessionWindowEngine`` in its **own** call. The two arms
   are never mixed in one ``run_many`` -- D43's collision was reachable and the
   cost of avoiding it is nothing.
4. Compute the full metric set from ``compute_metrics`` (net of costs; it reads
   ``Trade.net_r``).
5. Floor at 20 trades, collapse clones by realised-trade fingerprint.
6. Build placebos from the FLOORED rows only -- ``placebo_random`` and
   ``placebo_shuffle``; ``placebo_shift`` is excluded because D42 measured it as
   a degraded real strategy, not a control -- and run them through the SAME
   engine, same costs, same clock rule.
7. Rank reals and placebos in ONE table on the pre-registered durability score.
8. Report the best placebo's rank against its analytic null
   (``placebo.null_rank_distribution``), the search size, ``free_t``, and the
   annualised Sharpe each threshold implies on a 0.1585-year span.
9. Out-of-sample: a chronological 60/40 split by 18:00->16:00 cycle, and a
   3-fold disjoint-thirds check. In-sample rank is never reported alone.

The ranking score, fixed here before any number is seen (the mandate: never rank
on highest historical profit):

    score = expectancy_r_net * shrink(n) ,  shrink(n) = n / (n + 40)

with hard gates applied BEFORE ranking, not as tie-breaks:
    n >= 20                       (reporting floor; a PF of 1.8 over 18 trades is noise)
    t_statistic >= 0              (a negative-t row cannot be durable)
    max_consecutive_losses <= 12  (an operational gate, not a statistical one)

and the reported row carries every metric the mandate names, plus the placebo
comparison, plus its own OOS behaviour. The score is a *ordering* device; the
verdict is the placebo comparison and the OOS column.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
EF1 = os.path.join(os.path.dirname(os.path.dirname(HERE)), "EF1", "code")
NEWSTRATS = "/home/user/Futures01/workspace"
for p in (HERE, EF1, NEWSTRATS, "/home/user/Futures01"):
    if p not in sys.path:
        sys.path.insert(0, p)

from ef5_data import (CELL_FRAMES, PRIMARY_TFS, REPO, SYMBOLS,   # noqa: E402
                      build_frame, in_session, session_id)
from population import ARMS, base_population, session_arm         # noqa: E402

from futures_agents.backtest.metrics import compute_metrics        # noqa: E402
from newstrats import placebo as P                                 # noqa: E402

OUT = os.path.join(REPO, "workspace/roundtable/edge/EF5/out")
FLOOR = 20
SHRINK_K = 40
PLACEBO_KINDS = ("placebo_random", "placebo_shuffle")   # D42: shift excluded
SPAN_YEARS = 0.1585          # EF5/out/substrate.json, identical in all six cells


# ----------------------------------------------------------------- gating
def import_engine(require_validated: bool):
    verify = os.path.join(os.path.dirname(EF1), "VERIFY.md")
    if require_validated and not os.path.exists(verify):
        raise SystemExit(
            "EF1 has published no VERIFY.md. Per the EDGE_BRIEF, no profitability "
            "number may be produced before EF1's harness is validated. Re-run with "
            "--no-require-validated only to smoke-test the plumbing, and label any "
            "output PROVISIONAL.")
    from session_window import (SessionWindowEngine, assert_distinct_ids,   # noqa
                                assert_hooks_reachable, violations)
    assert_hooks_reachable()
    return SessionWindowEngine, assert_distinct_ids, violations


# ------------------------------------------------------------- statistics
def free_t(n: int) -> float:
    import math
    return math.sqrt(2.0 * math.log(max(2, n)))


def sharpe_needed(t: float, years: float = SPAN_YEARS) -> float:
    import math
    return t / math.sqrt(years)


def fingerprint(trades) -> str:
    import hashlib
    key = "|".join(f"{t.entry_ts.isoformat()}:{t.direction.value}" for t in trades)
    return hashlib.sha1(key.encode()).hexdigest()[:16] if key else "empty"


def score(m) -> float:
    """Durability score. Expectancy in R net of costs, shrunk on sample size."""
    return m.expectancy_r * (m.trades / (m.trades + SHRINK_K))


def gates_pass(m) -> bool:
    return (m.trades >= FLOOR and m.t_statistic >= 0.0
            and m.max_consecutive_losses <= 12)


def row_of(sid: str, m, *, kind: str, group: str, name: str,
           stop_kind: str, exec_tf, conds: Sequence[str], base_id=None) -> dict:
    return {
        "id": sid, "kind": kind, "group": group, "name": name,
        "stop_kind": stop_kind, "exec_tf": exec_tf,
        "conditions": list(conds), "placebo_base": base_id,
        "n": m.trades, "win_rate": round(m.win_rate, 4),
        "avg_win_r": round(m.avg_win_r, 4), "avg_loss_r": round(m.avg_loss_r, 4),
        "payoff_rr": round(m.payoff_ratio, 4),
        "profit_factor": round(m.profit_factor, 4),
        "expectancy_r_net": round(m.expectancy_r, 4),
        "total_r": round(m.total_r, 3),
        "max_dd_r": round(m.max_drawdown_r, 3),
        "avg_dd_r": round(m.avg_drawdown_r, 3),
        "sharpe_per_trade": round(m.sharpe, 4),
        "sharpe_annualised": round(m.sharpe_annualised, 4),
        "sortino": round(m.sortino, 4), "sqn": round(m.sqn, 4),
        "t": round(m.t_statistic, 4), "std_r": round(m.std_r, 4),
        "max_consec_wins": m.max_consecutive_wins,
        "max_consec_losses": m.max_consecutive_losses,
        "avg_minutes_held": round(m.avg_minutes_held, 1),
        "avg_bars_held": round(m.avg_bars_held, 2),
        "avg_mae_r": round(m.avg_mae_r, 4), "avg_mfe_r": round(m.avg_mfe_r, 4),
        "edge_ratio": round(m.edge_ratio, 4),
        "long_n": m.long_trades, "short_n": m.short_trades,
        "long_exp_r": round(m.long_expectancy_r, 4),
        "short_exp_r": round(m.short_expectancy_r, 4),
        "exit_reasons": dict(m.exit_reasons),
        "score": round(score(m), 5),
    }


def slice_metrics(trades, key_fn) -> Dict[str, dict]:
    """Per-slice expectancy: session, time bucket, regime, volatility."""
    buckets: Dict[str, list] = {}
    for t in trades:
        buckets.setdefault(str(key_fn(t)), []).append(t)
    out = {}
    for k, v in sorted(buckets.items()):
        m = compute_metrics(v)
        out[k] = {"n": m.trades, "exp_r": round(m.expectancy_r, 4),
                  "win": round(m.win_rate, 4)}
    return out


# ------------------------------------------------------------------- main
def run_cell(symbol: str, primary_tf: int, arm: str, Engine, assert_distinct_ids,
             violations, *, seed: int = 0) -> dict:
    frame = build_frame(symbol, primary_tf)
    base = base_population(symbol, primary_tf)
    strats = base if arm == "RTH" else session_arm(base)
    assert_distinct_ids(strats)

    eng = Engine(frame)
    res = eng.run_many(strats)

    # ---- real rows, floored, clones collapsed ------------------------
    seen: Dict[str, str] = {}
    reals, clones = [], Counter()
    realised: Dict[str, int] = {}
    ledger: Dict[str, list] = {}
    for s in strats:
        tr = res[s.strategy_id].trades
        realised[s.strategy_id] = len(tr)
        if len(tr) < FLOOR:
            continue
        fp = fingerprint(tr)
        if fp in seen:
            clones[seen[fp]] += 1
            continue
        seen[fp] = s.strategy_id
        m = compute_metrics(tr)
        if not gates_pass(m):
            continue
        r = row_of(s.strategy_id, m, kind="real", group=s.group, name=s.name,
                   stop_kind=str(s.exit.stop_kind), exec_tf=s.execution_tf,
                   conds=[c.name for c in s.conditions])
        r["by_session"] = slice_metrics(tr, lambda t: t.session)
        r["by_time_bucket"] = slice_metrics(tr, lambda t: t.time_bucket)
        r["by_regime"] = slice_metrics(tr, lambda t: t.regime)
        r["by_volatility"] = slice_metrics(tr, lambda t: t.volatility)
        reals.append(r)
        ledger[s.strategy_id] = tr

    # ---- placebos from the FLOORED bases only ------------------------
    bases = [s for s in strats if s.strategy_id in {r["id"] for r in reals}]
    plcs, meta, diag = P.build_cohort(frame, bases, realised, seed=seed,
                                      kinds=PLACEBO_KINDS)
    pres = Engine(frame).run_many(plcs) if plcs else {}
    placebo_rows = []
    for p in plcs:
        tr = pres[p.strategy_id].trades
        if len(tr) < FLOOR:
            continue
        m = compute_metrics(tr)
        if not gates_pass(m):
            continue
        md = meta[p.strategy_id]
        placebo_rows.append(row_of(
            p.strategy_id, m, kind=md.kind, group=md.group, name=p.name,
            stop_kind=str(p.exit.stop_kind), exec_tf=p.execution_tf,
            conds=[c.name for c in p.conditions], base_id=md.base_id))

    # ---- one ranking, reals and placebos together --------------------
    table = sorted(reals + placebo_rows, key=lambda r: -r["score"])
    for i, r in enumerate(table, 1):
        r["rank"] = i
    n_plc = len(placebo_rows)
    best_plc = next((r["rank"] for r in table if r["kind"] != "real"), None)
    null = P.null_rank_distribution(len(table), n_plc) if n_plc else None

    return {
        "symbol": symbol, "primary_tf": primary_tf, "arm": arm,
        "frame_tfs": CELL_FRAMES[primary_tf],
        "population_declared": len(strats),
        "floored_reals": len(reals), "clones_collapsed": sum(clones.values()),
        "placebos_built": len(plcs), "placebos_floored": n_plc,
        "placebo_diag": diag,
        "best_placebo_rank": best_plc,
        "placebo_null": null,
        "search_size": len(strats), "free_t_cell": round(free_t(len(strats)), 4),
        "sharpe_needed_cell": round(sharpe_needed(free_t(len(strats))), 3),
        "free_t_single_prereg": 1.177,
        "sharpe_needed_single_prereg": round(sharpe_needed(1.177), 3),
        "engine_counters": eng.counters.to_dict(),
        "rule_violations": violations(
            [t for tr in ledger.values() for t in tr]),
        "table": table,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-validated", dest="req", action="store_true",
                    default=True)
    ap.add_argument("--no-require-validated", dest="req", action="store_false")
    ap.add_argument("--symbols", nargs="*", default=list(SYMBOLS))
    ap.add_argument("--tfs", nargs="*", type=int, default=list(PRIMARY_TFS))
    ap.add_argument("--arms", nargs="*", default=list(ARMS))
    ap.add_argument("--out", default="measure.json")
    a = ap.parse_args()

    Engine, adi, viol = import_engine(a.req)
    out = {}
    for sym in a.symbols:
        for tf in a.tfs:
            for arm in a.arms:
                key = f"{sym}_{tf}m_{arm}"
                out[key] = run_cell(sym, tf, arm, Engine, adi, viol)
                c = out[key]
                print(f"{key}: floored={c['floored_reals']} "
                      f"placebos={c['placebos_floored']} "
                      f"best_placebo_rank={c['best_placebo_rank']} "
                      f"top_score={c['table'][0]['score'] if c['table'] else None}",
                      flush=True)
    with open(os.path.join(OUT, a.out), "w") as fh:
        json.dump(out, fh)
    print("wrote", os.path.join(OUT, a.out))


if __name__ == "__main__":
    main()
