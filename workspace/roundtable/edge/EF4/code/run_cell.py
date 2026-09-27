"""EF4 - run one cell's declared population under the 18:00->16:00 ET rule.

Harness: EF1's ``SessionWindowEngine`` (`workspace/roundtable/edge/EF1/code/session_window.py`)
is the programme harness and is used as primary. EF4's own ``ScalpSessionEngine``
(`code/session_clock.py`) is an independent second implementation of the same rule, run on
a subset as a differential check: two implementations that agree tell you the numbers are
not an artefact of one author's reading. **Until EF1 declares validation, no profitability
number produced here is a programme result.**

Metrics: every one the EDGE_BRIEF asks for, computed from the R series, plus the pieces the
scalp cell specifically needs - gross reconstructed rather than read off ``Trade.gross_r``
(which is already net of slippage, engine.py:352/:414), and cost decomposed.

Usage:  python3 run_cell.py MGC 30 [--track A|B|both] [--limit N]
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
import time
from pathlib import Path
from typing import Dict, List, Sequence

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF1/code"))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF4/code"))

from futures_agents.backtest.costs import CostModel              # noqa: E402
from futures_agents.config import get_contract                   # noqa: E402
from futures_agents.data.archive import BarArchive                # noqa: E402
from futures_agents.features import SymbolFrame                   # noqa: E402
from futures_agents.timeutil import is_rth, to_et                 # noqa: E402

from session_window import SessionWindowEngine                    # noqa: E402
from population import (build_track_a, build_track_b, assert_unique,
                        FIXED_EXIT)                               # noqa: E402

OUT = ROOT / "workspace/roundtable/edge/EF4/out"


def frame_for(symbol: str, tf: int) -> SymbolFrame:
    series = BarArchive(str(ROOT / "data/archive")).load(symbol, tf)
    return SymbolFrame(series, (tf,))


def drawdown(rs: Sequence[float]):
    peak = cum = 0.0
    maxdd = 0.0
    dds: List[float] = []
    cur = 0.0
    for r in rs:
        cum += r
        if cum > peak:
            peak = cum
            if cur > 0:
                dds.append(cur)
            cur = 0.0
        else:
            cur = peak - cum
            maxdd = max(maxdd, cur)
    if cur > 0:
        dds.append(cur)
    return maxdd, (st.mean(dds) if dds else 0.0)


def streaks(rs: Sequence[float]):
    bw = bl = cw = cl = 0
    for r in rs:
        if r > 0:
            cw += 1; cl = 0
        elif r < 0:
            cl += 1; cw = 0
        else:
            cw = cl = 0
        bw = max(bw, cw); bl = max(bl, cl)
    return bw, bl


SESSION_KEYS: list = []          # sorted 18:00->16:00 session labels for this cell


def session_key(ts) -> str:
    """The 18:00 ET -> 16:00 ET cycle a stamp belongs to.

    ``trading_day`` in the repo rolls at 18:00 and is the same boundary
    `[repo-verified: futures_agents/timeutil.py:169-180]`; this is spelled out locally so
    the split is legible beside the numbers it produces.
    """
    t = to_et(ts)
    if t.hour >= 18:
        from datetime import timedelta
        return (t + timedelta(days=1)).date().isoformat()
    return t.date().isoformat()


def slice_metrics(trades, spec, cost, keys_allowed):
    """Metrics over the subset of trades whose ENTRY session is in ``keys_allowed``.

    The entry session, not the exit session: a trade is attributed to the decision, and a
    22-hour hold can exit in the next session. Splitting on the exit would leak a
    later-period bar into an earlier-period score.
    """
    sub = [t for t in trades if session_key(t.entry_ts) in keys_allowed]
    return _metrics_from_trades(sub, spec, cost)


def _metrics_from_trades(tr, spec, cost: CostModel) -> dict:
    n = len(tr)
    if n == 0:
        return {"trades": 0}
    net = [t.net_r for t in tr]
    # Reconstruct TRUE gross: add back commission (already in net) and slippage
    # (already inside gross_r via the fill prices).
    comm_r = [t.commission_dollars / (t.risk_points * spec.point_value)
              if t.risk_points else 0.0 for t in tr]
    slip_r = []
    for t in tr:
        thin = not is_rth(t.entry_ts, spec.rth_open, spec.rth_close)
        entry_slip = cost.slippage_price(is_stop=False, thin=thin)
        exit_is_stop = t.exit_reason.value in ("STOP", "BREAKEVEN", "SESSION_CLOSE",
                                               "TIME", "TRAIL")
        thin_x = not is_rth(t.exit_ts or t.entry_ts, spec.rth_open, spec.rth_close)
        exit_slip = cost.slippage_price(is_stop=exit_is_stop, thin=thin_x)
        rp = t.risk_points or 1.0
        slip_r.append((entry_slip + exit_slip) / rp)
    gross = [net[i] + comm_r[i] + slip_r[i] for i in range(n)]

    wins = [r for r in net if r > 0]
    losses = [r for r in net if r <= 0]
    mu = st.mean(net)
    sd = st.pstdev(net) if n > 1 else 0.0
    t_stat = (mu / (sd / math.sqrt(n))) if sd > 0 else 0.0
    downside = [min(0.0, r) for r in net]
    dsd = math.sqrt(sum(d * d for d in downside) / n) if n else 0.0
    maxdd, avgdd = drawdown(net)
    bw, bl = streaks(net)
    gp = sum(wins); gl = -sum(losses)
    sessions_hit = len({to_et(t.entry_ts).date() for t in tr})
    return {
        "trades": n,
        "win_rate": len(wins) / n,
        "avg_win_r": st.mean(wins) if wins else 0.0,
        "avg_loss_r": st.mean(losses) if losses else 0.0,
        "rr_realised": (st.mean(wins) / abs(st.mean(losses))) if wins and losses and st.mean(losses) else 0.0,
        "profit_factor": (gp / gl) if gl > 0 else float("inf"),
        "expectancy_net_r": mu,
        "expectancy_gross_r": st.mean(gross),
        "cost_commission_r": st.mean(comm_r),
        "cost_slippage_r": st.mean(slip_r),
        "cost_total_r": st.mean(comm_r) + st.mean(slip_r),
        "sd_r": sd,
        "t_stat": t_stat,
        "sharpe_per_trade": (mu / sd) if sd else 0.0,
        "sharpe_annualised": (mu / sd) * math.sqrt(n / 0.15852) if sd else 0.0,
        "sortino_per_trade": (mu / dsd) if dsd else 0.0,
        "max_dd_r": maxdd, "avg_dd_r": avgdd,
        "max_consec_wins": bw, "max_consec_losses": bl,
        "avg_minutes_held": st.mean([t.minutes_held for t in tr]),
        "avg_mae_r": st.mean([t.mae_r for t in tr]),
        "avg_mfe_r": st.mean([t.mfe_r for t in tr]),
        "sessions_with_a_trade": sessions_hit,
        "pct_entries_outside_rth": sum(
            1 for t in tr if not is_rth(t.entry_ts, spec.rth_open, spec.rth_close)) / n,
        "exit_mix": {k: sum(1 for t in tr if t.exit_reason.value == k) / n
                     for k in sorted({t.exit_reason.value for t in tr})},
    }


def metrics(res, spec, cost: CostModel) -> dict:
    m = _metrics_from_trades(res.trades, spec, cost)
    m["signals"] = res.signals_generated
    return m


def run(symbol: str, tf: int, track: str, limit: int = 0) -> dict:
    spec = get_contract(symbol)
    cost = CostModel(spec)
    frame = frame_for(symbol, tf)
    strats = []
    if track in ("A", "both"):
        strats += build_track_a(symbol, tf)
    if track in ("B", "both"):
        strats += build_track_b(symbol, tf)
    if limit:
        strats = strats[:limit]
    assert_unique(strats, f"{symbol} {tf}m {track}")
    eng = SessionWindowEngine(frame, cost)
    t0 = time.time()
    results = eng.run_many(strats)
    dt = time.time() - t0
    by_id = {s.strategy_id: s for s in strats}
    all_keys = sorted({session_key(b.ts) for b in frame.base.bars
                       if session_key(b.ts) is not None})
    # drop the 16:00-18:00 orphan labels: a session with no tradeable bar is not a session
    n_s = len(all_keys)
    cut = int(round(n_s * 0.6))
    is_keys, oos_keys = set(all_keys[:cut]), set(all_keys[cut:])
    third = n_s // 3
    folds = [set(all_keys[:third]), set(all_keys[third:2 * third]),
             set(all_keys[2 * third:])]
    rows = []
    for sid, res in results.items():
        m = metrics(res, spec, cost)
        s = by_id[sid]
        m.update({"strategy_id": sid, "name": s.name, "group": s.group,
                  "symbol": symbol, "tf": tf,
                  "conditions": [c.name for c in s.conditions]})
        m["is"] = slice_metrics(res.trades, spec, cost, is_keys)
        m["oos"] = slice_metrics(res.trades, spec, cost, oos_keys)
        m["folds"] = [slice_metrics(res.trades, spec, cost, f) for f in folds]
        rows.append(m)
    payload = {
        "symbol": symbol, "tf": tf, "track": track,
        "n_arms": len(strats), "seconds": round(dt, 1),
        "harness": "EF1.SessionWindowEngine",
        "counters": eng.counters.to_dict(),
        "sessions": n_s, "is_sessions": cut, "oos_sessions": n_s - cut,
        "session_first": all_keys[0], "session_last": all_keys[-1],
        "rows": rows,
    }
    p = OUT / f"run_{symbol}_{tf}m_{track}.json"
    p.write_text(json.dumps(payload, indent=2))
    traded = [r for r in rows if r["trades"] > 0]
    print(f"{symbol} {tf}m track {track}: {len(strats)} arms in {dt:.0f}s, "
          f"{len(traded)} traded ({len(traded)/len(strats):.1%})")
    print(f"  -> {p}")
    return payload


if __name__ == "__main__":
    sym = sys.argv[1]
    tf = int(sys.argv[2])
    track = "both"
    limit = 0
    for k, a in enumerate(sys.argv):
        if a == "--track":
            track = sys.argv[k + 1]
        if a == "--limit":
            limit = int(sys.argv[k + 1])
    run(sym, tf, track, limit)
