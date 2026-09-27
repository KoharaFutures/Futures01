"""EF2 measurement: runs the population, its placebos and the forward roll.

Written BEFORE EF1 declared its harness trustworthy, deliberately, so that no
choice in it can have been made after seeing a number. The only thing it waits
on is ``--engine session``: with ``--engine shipped`` it runs the vanilla
``BacktestEngine``, which is NOT the swing setting and whose output is labelled
``NOT_REPORTABLE_AS_SWING`` in the artefact so it can never be quoted as one.

Ranking, fixed here in code:

    rank key = expectancy in R

and nothing else. Win rate, payoff and profit factor are reported beside it and
are never rank keys - they cancel (BRIEF rules 3 and 7, measured four times).
The sample-size penalty is the trade floor plus the t-statistic of the R series,
both of which GATE a row; they do not reorder it.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import statistics as st
import sys
import time
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Sequence, Tuple

REPO = "/home/user/Futures01"
if REPO not in sys.path:
    sys.path.insert(0, REPO)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "workspace", "roundtable", "edge", "EF1", "code"))

from futures_agents.backtest.costs import CostModel                 # noqa: E402
from futures_agents.backtest.engine import BacktestEngine           # noqa: E402
from futures_agents.timeutil import to_et                           # noqa: E402

import population as P                                              # noqa: E402
from substrate import frame_for                                     # noqa: E402
from census import entry_admissible                                 # noqa: E402

OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")
SQRT_YEARS = math.sqrt(718 / 365.25)
MIN_TRADES = 30
PLACEBO_DRAWS = 200
N_BLOCKS = 6


# ------------------------------------------------------------------- metrics
def metrics(rs: Sequence[float], gross: Optional[Sequence[float]] = None,
            durations: Optional[Sequence[float]] = None,
            mae: Optional[Sequence[float]] = None,
            mfe: Optional[Sequence[float]] = None) -> dict:
    """Everything the task brief asks for, from one R series.

    Expectancy is the mean of net R. Win rate and payoff are reported TOGETHER
    and never separately, which is the point of putting them in one dict.
    """
    n = len(rs)
    if n == 0:
        return {"trades": 0}
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    aw = st.mean(wins) if wins else 0.0
    al = st.mean(losses) if losses else 0.0
    sd = st.pstdev(rs) if n > 1 else 0.0
    sd_s = st.stdev(rs) if n > 1 else 0.0
    gp = sum(wins)
    gl = -sum(losses)
    # drawdown on the cumulative R curve
    eq, cum, peak, mdd, dds = [], 0.0, 0.0, 0.0, []
    for r in rs:
        cum += r
        eq.append(cum)
        if cum > peak:
            peak = cum
            if dds and dds[-1] > 0:
                pass
        dd = peak - cum
        dds.append(dd)
        mdd = max(mdd, dd)
    cw = cl = bw = bl = 0
    for r in rs:
        if r > 0:
            cw += 1
            cl = 0
            bw = max(bw, cw)
        else:
            cl += 1
            cw = 0
            bl = max(bl, cl)
    exp = st.mean(rs)
    t = exp / (sd_s / math.sqrt(n)) if n > 1 and sd_s > 0 else 0.0
    neg = [r for r in rs if r < 0]
    dsd = math.sqrt(sum(r * r for r in neg) / n) if neg else 0.0
    out = {
        "trades": n,
        "expectancy_r": exp,
        "win_rate": len(wins) / n,
        "avg_win_r": aw, "avg_loss_r": al,
        "payoff": (aw / abs(al)) if al else float("inf"),
        "profit_factor": (gp / gl) if gl else float("inf"),
        "sharpe_per_trade": (exp / sd) if sd else 0.0,
        "sortino_per_trade": (exp / dsd) if dsd else 0.0,
        "t_stat": t,
        "max_drawdown_r": mdd,
        "avg_drawdown_r": st.mean(dds) if dds else 0.0,
        "max_consec_wins": bw, "max_consec_losses": bl,
        "total_r": sum(rs),
    }
    if gross is not None and len(gross) == n:
        out["expectancy_r_gross"] = st.mean(gross)
        out["cost_drag_r"] = st.mean(gross) - exp
    if durations:
        out["avg_duration_min"] = st.mean(durations)
        out["max_duration_min"] = max(durations)
    if mae:
        out["avg_mae_r"] = st.mean(mae)
    if mfe:
        out["avg_mfe_r"] = st.mean(mfe)
    return out


def trade_rows(trades) -> dict:
    """Pull the per-trade series the metrics need out of engine Trade objects."""
    net = [t.net_r for t in trades]
    gross = [t.gross_r for t in trades]
    dur, mae, mfe = [], [], []
    for t in trades:
        try:
            dur.append((to_et(t.exit_ts) - to_et(t.entry_ts)).total_seconds() / 60.0)
        except Exception:
            pass
        for attr, box in (("mae_r", mae), ("mfe_r", mfe)):
            v = getattr(t, attr, None)
            if v is not None:
                box.append(v)
    return {"net": net, "gross": gross, "dur": dur, "mae": mae, "mfe": mfe}


# ------------------------------------------------------------------- engines
def make_engine(frame, symbol: str, kind: str):
    costs = CostModel(frame.spec)
    if kind == "session":
        from session_window import SessionWindowEngine
        return SessionWindowEngine(frame, costs)
    if kind == "shipped":
        return BacktestEngine(frame, costs)
    raise ValueError(kind)


# ------------------------------------------------------------------- placebo
#
# EF6's placebo_w.py, NOT newstrats/placebo.py. Three reasons, all EF6's burst 03:
#  * count-matching in the upstream module does not survive the window rule - it
#    counts signals and builds pools over bars that include the 16:00-18:00
#    prohibition, so base and control reach the engine with different numbers of
#    LEGAL entries, and EF6 measured the sign of that gap REVERSING between cells;
#  * placebo_shuffle permutes DIRECTION LABELS, so on a one-sided rule set it
#    destroys nothing at all (measured 0.0000 on MGC 60m MEAN_REVERSION bases);
#  * the timestamp shuffle the EDGE_BRIEF asks for does not exist upstream.
# placebo_w keeps everything the upstream module got right - SIGNAL layer only,
# raw-signal matching, schedule-hashed condition names, _id=None - and asserts the
# placebo's id differs from its base's rather than trusting that _id=None stays.
sys.path.insert(0, os.path.join(REPO, "workspace", "roundtable", "edge", "EF6", "code"))

#: D42 excludes placebo_shift (it leaks). EF6 Fault 2 excludes the direction
#: shuffle (degenerate on a one-sided signal).
PLACEBO_KINDS = ("placebo_random_legal", "placebo_session_shuffle")
PLACEBO_SEEDS = tuple(range(20))


def build_placebos(frame, bases, realised: Dict[str, int]):
    """One placebo per (base, kind, seed): 20 seeds x 2 kinds = 40 controls/row."""
    import placebo_w as PW
    out, meta, diag = [], {}, {}
    for sd in PLACEBO_SEEDS:
        s, m, d = PW.build_cohort(frame, bases, realised, seed=sd,
                                  kinds=PLACEBO_KINDS)
        out.extend(s)
        meta.update(m)
        diag[sd] = d
    return out, meta, diag


# ------------------------------------------------------------------- ledger
def ledger_doc(symbol: str, setting: str, base_tf: int, screened: int,
               results, index: Dict[str, dict], arms: Dict[str, object]) -> dict:
    """EF6's forward-roll ledger format. EF2 computes no folds of its own.

    EF6's ``cycle_boundaries`` puts every fold edge at 18:00 ET so no holding
    period is split across the rank/score line, and ``Ledger.measure`` does clone
    collapse by default - without which a top 10 is routinely the top 2 listed ten
    times. Both are things EF2 would otherwise have had to get right twice.
    """
    strategies: Dict[str, dict] = {}
    for ak, stg in arms.items():
        r = results[stg.strategy_id]
        meta = index[ak]
        strategies[ak] = {
            "meta": {"stop": meta["stop_kind"], "target": meta["target_kind"],
                     "group": meta["group"], "cell": meta["cell"],
                     "primary_tf": meta["primary_tf"],
                     "rth_only": meta["rth_only"],
                     "strategy_id": meta["strategy_id"]},
            "trades": [[to_et(t.entry_ts).timestamp(),
                        to_et(t.exit_ts).timestamp(),
                        1 if t.direction.sign > 0 else -1,
                        float(t.net_r)] for t in r.trades],
        }
    return {"symbol": symbol, "setting": setting, "base_tf": base_tf,
            "substrate": "data/archive 60m, 718 calendar days",
            "screened": screened, "strategies": strategies}


# ------------------------------------------------------------------- folds
def fold_bounds(n_bars: int, blocks: int = N_BLOCKS) -> List[Tuple[int, int]]:
    """Equal-length blocks over the base INDEX. Diagnostic only.

    SUPERSEDED for any reported forward number by EF6's ``cycle_boundaries``,
    which puts every edge at 18:00 ET so no holding period is split across the
    rank/score line. Kept because a per-fold expectancy on a fixed index grid is
    a cheap stability read, and labelled so it cannot be mistaken for the roll.
    """
    edges = [round(k * n_bars / blocks) for k in range(blocks + 1)]
    return [(edges[k], edges[k + 1]) for k in range(blocks)]


# ------------------------------------------------------------------- main
def run_cell(sym: str, cell: str, arms: Dict[str, object], kind: str,
             index: Dict[str, dict]) -> dict:
    tfs = tuple(P.CELL_SPEC[cell][0])
    fr = frame_for(sym, tfs)
    eng = make_engine(fr, sym, kind)
    t0 = time.time()
    res = eng.run_many(list(arms.values()))
    el = time.time() - t0
    # arms keyed cell|rth|sid; results keyed sid. Within a (cell, rth) stratum
    # ids are unique (D48 assert), but the SAME sid appears in both rth arms, so
    # a single run_many over both arms would collide them. Callers must pass one
    # rth stratum at a time; asserted here.
    sids = [s.strategy_id for s in arms.values()]
    assert len(set(sids)) == len(sids), (
        "D48: run_many was handed two arms sharing a strategy_id; they would "
        "merge into one BacktestResult and the between-arm difference would "
        "measure exactly zero")
    rows = {}
    nb = len(fr.base)
    folds = fold_bounds(nb)
    for ak, stg in arms.items():
        r = res[stg.strategy_id]
        tr = trade_rows(r.trades)
        m = metrics(tr["net"], tr["gross"], tr["dur"], tr["mae"], tr["mfe"])
        m["signals_generated"] = r.signals_generated
        meta = dict(index[ak])
        # per-fold R, keyed on the ENTRY bar's fold
        per_fold = defaultdict(list)
        for t in r.trades:
            bi = getattr(t, "entry_index", None)
            if bi is None:
                continue
            for k, (a, b) in enumerate(folds):
                if a <= bi < b:
                    per_fold[k].append(t.net_r)
                    break
        m["fold_expectancy_r"] = {str(k): st.mean(v) for k, v in sorted(per_fold.items())}
        m["fold_trades"] = {str(k): len(v) for k, v in sorted(per_fold.items())}
        rows[ak] = {**meta, **m}
    counters = getattr(eng, "counters", None)
    return {"cell": f"{sym}:{cell}", "engine": kind, "seconds": round(el, 1),
            "bars": nb, "index_folds_diagnostic_only": [list(f) for f in folds],
            "counters": (counters.__dict__ if counters else None),
            "rows": rows, "_results": res}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=("session", "shipped"), required=True)
    ap.add_argument("--symbols", default="MGC,MCL")
    ap.add_argument("--cells", default=",".join(P.CELL_SPEC))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    res = P.assemble()
    objs = res.pop("_objects")
    doc = {"engine": a.engine, "seed": res["seed"],
           "population": res["population"],
           "removed_by_void": res["removed_by_void"],
           "free_t": {s: round(math.sqrt(2 * math.log(n)), 3)
                      for s, n in res["population"].items()},
           "span_days": 718, "sqrt_years": round(SQRT_YEARS, 4),
           "min_trades": MIN_TRADES, "cells": {}}
    if a.engine == "shipped":
        doc["NOT_REPORTABLE_AS_SWING"] = (
            "Measured on the shipped BacktestEngine, which flattens at the "
            "contract's own RTH close (13:30 MGC / 14:30 MCL) and never holds "
            "overnight. This is NOT the 18:00->16:00 swing setting and no number "
            "in this file may be quoted as a swing result.")
    for sym in a.symbols.split(","):
        for cell in a.cells.split(","):
            for rth in (True, False):
                arms = {ak: stg for ak, stg in objs[sym].items()
                        if res["index"][sym][ak]["cell"] == f"{sym}:{cell}"
                        and res["index"][sym][ak]["rth_only"] is rth}
                if not arms:
                    continue
                key = f"{sym}:{cell}|rth{int(rth)}"
                sys.stderr.write(f"{key}: {len(arms)} arms ...\n")
                sys.stderr.flush()
                cellres = run_cell(sym, cell, arms, a.engine,
                                   res["index"][sym])
                doc["cells"][key] = cellres
                # EF6 ledger, one per (symbol, cell, rth arm), for forward.roll
                led = ledger_doc(sym, key, 60, res["population"][sym],
                                 cellres.pop("_results"), res["index"][sym], arms)
                lp = os.path.join(OUT, "ledgers")
                os.makedirs(lp, exist_ok=True)
                with open(os.path.join(lp, f"{key.replace('|','__')}.json"), "w") as fh:
                    json.dump(led, fh)
    path = a.out or os.path.join(OUT, f"measure_{a.engine}.json")
    with open(path, "w") as fh:
        json.dump(doc, fh)
    sys.stderr.write(f"wrote {path}\n")


if __name__ == "__main__":
    main()
