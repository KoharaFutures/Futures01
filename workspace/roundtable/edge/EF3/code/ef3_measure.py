"""EF3 burst 05 - run the population through the session harness and record
everything a row needs. Protocol pre-registered in bursts/04_protocol_preregistered.md.

Stages, each written to disk so a crash costs one stage:
  1  run   : the live population over IS and over the full span, per symbol
  2  plc   : placebos for every row clearing the IS gates
  3  wf    : anchored walk-forward folds
"""
from __future__ import annotations

import json
import math
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, "/home/user/Futures01/workspace")
sys.path.insert(0, "/home/user/Futures01/workspace/roundtable/edge/EF3/code")

from ef3_population import build
from ef3_session import SessionEngine, flat_exit_keys, violations
from futures_agents.backtest.engine import Trade
from futures_agents.config import get_contract
from futures_agents.data.archive import BarArchive
from futures_agents.features import build_symbol_frame
from futures_agents.schema import Direction
from futures_agents.timeutil import to_et
from newstrats import placebo as PL

OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF3/out")
IS_FRAC = 0.60
MIN_IS_TRADES = 30
MIN_OOS_TRADES = 10
SEED = 20260922


# ----------------------------------------------------------------- metrics
def metrics(trades: Sequence[Trade]) -> dict:
    n = len(trades)
    if n == 0:
        return {"trades": 0}
    r = [t.net_r for t in trades]
    g = [t.gross_r for t in trades]
    wins = [x for x in r if x > 0]
    losses = [x for x in r if x < 0]
    mean = sum(r) / n
    sd = statistics.stdev(r) if n > 1 else 0.0
    dn = [x for x in r if x < 0]
    dsd = (math.sqrt(sum(x * x for x in dn) / len(dn)) if dn else 0.0)
    eq, peak, dds, cur, maxdd, ddlen, maxddlen = 0.0, 0.0, [], 0.0, 0.0, 0, 0
    for x in r:
        eq += x
        if eq > peak:
            peak = eq
            ddlen = 0
        else:
            ddlen += 1
            maxddlen = max(maxddlen, ddlen)
        d = peak - eq
        dds.append(d)
        maxdd = max(maxdd, d)
    cw = cl = bw = bl = 0
    for x in r:
        if x > 0:
            cw += 1; cl = 0
        elif x < 0:
            cl += 1; cw = 0
        bw = max(bw, cw); bl = max(bl, cl)
    aw = sum(wins) / len(wins) if wins else 0.0
    al = sum(losses) / len(losses) if losses else 0.0
    gp = sum(wins); gl = -sum(losses)
    hrs = [(to_et(t.exit_ts) - to_et(t.entry_ts)).total_seconds() / 3600
           for t in trades if t.exit_ts]
    return {
        "trades": n,
        "expectancy_r": round(mean, 5),
        "gross_expectancy_r": round(sum(g) / n, 5),
        "total_r": round(sum(r), 4),
        "win_rate": round(len(wins) / n, 4),
        "avg_win_r": round(aw, 4), "avg_loss_r": round(al, 4),
        "payoff": round(aw / abs(al), 4) if al else None,
        "profit_factor": round(gp / gl, 4) if gl else None,
        "std_r": round(sd, 4),
        "t_stat": round(mean / (sd / math.sqrt(n)), 4) if sd > 0 else None,
        "sharpe_per_trade": round(mean / sd, 4) if sd > 0 else None,
        "sortino_per_trade": round(mean / dsd, 4) if dsd > 0 else None,
        "max_dd_r": round(maxdd, 4),
        "avg_dd_r": round(sum(dds) / len(dds), 4),
        "max_dd_trades": maxddlen,
        "max_consec_wins": bw, "max_consec_losses": bl,
        "avg_hours_held": round(sum(hrs) / len(hrs), 3) if hrs else None,
        "max_hours_held": round(max(hrs), 3) if hrs else None,
        "avg_mfe_r": round(sum(t.mfe_r for t in trades) / n, 4),
        "avg_mae_r": round(sum(t.mae_r for t in trades) / n, 4),
        "long_trades": sum(1 for t in trades if t.direction is Direction.LONG),
        "exit_reasons": dict(Counter(t.exit_reason.value for t in trades)),
    }


def slices(trades: Sequence[Trade]) -> dict:
    out = {}
    for key, fn in (("session", lambda t: t.session),
                    ("regime", lambda t: t.regime),
                    ("volatility", lambda t: t.volatility),
                    ("time_bucket", lambda t: t.time_bucket),
                    ("exit_reason", lambda t: t.exit_reason.value)):
        g = defaultdict(list)
        for t in trades:
            g[fn(t)].append(t.net_r)
        out[key] = {k: {"n": len(v), "exp_r": round(sum(v) / len(v), 4)}
                    for k, v in sorted(g.items()) if v}
    return out


# ----------------------------------------------------------------- stage 1
def frame_for(sym: str):
    arch = BarArchive("/home/user/Futures01/data/archive")
    base = arch.load(sym, 60)
    return build_symbol_frame(base, [60, 240], get_contract(sym)), base


def ledger_of(res) -> dict:
    """Compact per-trade ledger: every window is a slice of one run."""
    return {sid: [[t.entry_index, t.exit_index, round(t.net_r, 6),
                   round(t.gross_r, 6), 1 if t.direction.value == "LONG" else 0,
                   t.exit_reason.value, round(t.mfe_r, 4), round(t.mae_r, 4),
                   round((to_et(t.exit_ts) - to_et(t.entry_ts)).total_seconds() / 3600, 3),
                   t.session, t.regime, t.volatility, t.time_bucket]
                 for t in r.trades]
            for sid, r in res.items()}


def run_stage1(sym: str, max_total: int = 4000, gap: bool = True,
               verify_n: int = 300) -> dict:
    """ONE full-span run for the live population, plus two small true-window runs
    on a random subsample so the ledger-slicing approximation is MEASURED rather
    than inherited from RANKING_FINDINGS' -0.004R audit."""
    import random
    fr, base = frame_for(sym)
    n = len(base.bars)
    cut = int(n * IS_FRAC)
    pop = build(sym, max_total)
    live = [s for sid, s in pop["pop"].items() if sid not in pop["dead"]]
    deadS = [s for sid, s in pop["pop"].items() if sid in pop["dead"]]
    print(f"{sym}: population {len(pop['pop'])}, live {len(live)}, census-dead {len(deadS)}",
          flush=True)

    eng = SessionEngine(fr, enforce_session_gap=gap)
    t0 = time.time()
    res_full = eng.run_many(live, progress=lambda a, b: print(f"   {sym} bar {a}/{b} {time.time()-t0:.0f}s", flush=True) if a % 4000 == 0 else None)
    print(f"  full-span run {time.time()-t0:.0f}s", flush=True)
    allt = [t for r in res_full.values() for t in r.trades]
    v = violations(allt, flat_exits=flat_exit_keys(eng))

    # census falsification: do the census-removed strategies really never trade?
    engD = SessionEngine(fr, enforce_session_gap=gap)
    sample = deadS[:300]
    res_dead = engD.run_many(sample)
    dead_trades = sum(len(r.trades) for r in res_dead.values())
    print(f"  census falsification: {len(sample)} removed strategies -> {dead_trades} trades",
          flush=True)

    # slicing-bias measurement on a random subsample
    rng = random.Random(f"verify:{sym}")
    sub = rng.sample(live, min(verify_n, len(live)))
    eIS = SessionEngine(fr, enforce_session_gap=gap)
    rIS = eIS.run_many(sub, end=cut)
    eOO = SessionEngine(fr, enforce_session_gap=gap)
    rOO = eOO.run_many(sub, start=cut)
    print("  true-window verification runs done", flush=True)

    led = ledger_of(res_full)
    verify = {}
    for s in sub:
        sid = s.strategy_id
        rows = led.get(sid, [])
        verify[sid] = {
            "true_IS": metrics(rIS[sid].trades), "true_OOS": metrics(rOO[sid].trades),
            "sliced_IS_n": sum(1 for t in rows if t[0] < cut),
            "sliced_IS_exp": (round(sum(t[2] for t in rows if t[0] < cut)
                                    / max(1, sum(1 for t in rows if t[0] < cut)), 5)),
            "sliced_OOS_n": sum(1 for t in rows if t[0] >= cut),
            "sliced_OOS_exp": (round(sum(t[2] for t in rows if t[0] >= cut)
                                     / max(1, sum(1 for t in rows if t[0] >= cut)), 5)),
        }

    rows = {}
    for s in live:
        sid = s.strategy_id
        rows[sid] = {
            "strategy_id": sid, "name": s.name, "group": s.group,
            "primary_tf": s.primary_tf, "confirm_tfs": list(s.confirm_tfs),
            "rth_only": s.filters.rth_only,
            "stop_kind": s.exit.stop_kind.value, "stop_mult": s.exit.stop_mult,
            "target_kind": s.exit.target_kind.value,
            "n_signals": len(s.signal_conditions),
            "signals": sorted(c.label for c in s.signal_conditions),
            "filters": sorted(c.label for c in s.filter_conditions),
            "signals_generated_full": res_full[sid].signals_generated,
        }
    return {
        "symbol": sym, "bars": n, "is_cut": cut,
        "span_et": [to_et(base.bars[0].ts).isoformat(), to_et(base.bars[-1].ts).isoformat()],
        "population": len(pop["pop"]), "live": len(live), "census_dead": len(deadS),
        "enforce_session_gap": gap, "violations": len(v),
        "engine_counters": eng.counters.to_dict(), "forced_flats": eng.forced_flats,
        "census_falsification": {"sampled_dead": len(sample), "trades": dead_trades},
        "zero_trade_live_full": sum(1 for r in res_full.values() if not r.trades),
        "slicing_verification": verify,
        "rows": rows, "ledger": led,
    }


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    gap = "--nogap" not in sys.argv
    tag = "gap" if gap else "nogap"
    for sym in [a for a in sys.argv[1:] if not a.startswith("--")] or ["MES", "MNQ"]:
        d = run_stage1(sym, gap=gap)
        (OUT / f"stage1_{sym}_{tag}.json").write_text(json.dumps(d))
        print(f"{sym}: violations={d['violations']} dead-sample trades="
              f"{d['census_falsification']} zero-trade live={d['zero_trade_live_full']}"
              f"/{d['live']}", flush=True)
