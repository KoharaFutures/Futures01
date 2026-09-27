"""EF3 stage 2 - trade ledgers and the placebo cohort.

Full-span run for the live population, saved as a compact ledger so every
window (IS, OOS, walk-forward folds) is a SLICE of one run rather than N runs.
`RANKING_FINDINGS.md` audited that choice: 2.47% of trades straddle a period
edge and requiring both ends inside moves the pooled figure by -0.004R, so the
loose rule is mildly generous. Stage 1 ran the true IS and OOS windows, so the
two approaches can be cross-checked against each other here.

Placebos: `workspace/newstrats/placebo.py`, cohort built over the FULL span so
the placebo count-matches the real's full-span raw signal count and every window
comparison is like-for-like. Kinds:
  placebo_random   honest - destroys when and which way
  placebo_shuffle  honest - keeps when, destroys which way
  placebo_shift    LEAKS (D42), conservative-only, reported and never gated on
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, "/home/user/Futures01/workspace")
sys.path.insert(0, "/home/user/Futures01/workspace/roundtable/edge/EF3/code")

from ef3_measure import frame_for, IS_FRAC, MIN_IS_TRADES
from ef3_population import build
from ef3_session import SessionEngine, flat_exit_keys, violations
from futures_agents.timeutil import to_et
from newstrats import placebo as PL

OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF3/out")
SEED = 20260922


def ledger(res) -> dict:
    return {sid: [[t.entry_index, t.exit_index, round(t.net_r, 6),
                   round(t.gross_r, 6), 1 if t.direction.value == "LONG" else 0,
                   t.exit_reason.value, round(t.mfe_r, 4), round(t.mae_r, 4),
                   round((to_et(t.exit_ts) - to_et(t.entry_ts)).total_seconds() / 3600, 3),
                   t.session, t.regime, t.volatility, t.time_bucket]
                 for t in r.trades]
            for sid, r in res.items()}


def main(sym: str, gap: bool = True):
    tag = "gap" if gap else "nogap"
    s1 = json.loads((OUT / f"stage1_{sym}_{tag}.json").read_text())
    fr, base = frame_for(sym)
    pop = build(sym, 4000)
    live = {sid: s for sid, s in pop["pop"].items() if sid not in pop["dead"]}

    eng = SessionEngine(fr, enforce_session_gap=gap)
    t0 = time.time()
    res = eng.run_many(list(live.values()))
    print(f"{sym}: real full-span run {time.time()-t0:.0f}s, "
          f"violations {len(violations([t for r in res.values() for t in r.trades], flat_exits=flat_exit_keys(eng)))}, "
          f"forced_flats {eng.forced_flats}", flush=True)
    (OUT / f"ledger_real_{sym}_{tag}.json").write_text(json.dumps({
        "symbol": sym, "bars": len(base.bars), "is_cut": s1["is_cut"],
        "counters": eng.counters.to_dict(), "forced_flats": eng.forced_flats,
        "ledger": ledger(res)}))

    # --- candidates for a control: IS gates G1+G2 from stage 1
    cand = [sid for sid, r in s1["rows"].items()
            if r["IS"].get("trades", 0) >= MIN_IS_TRADES
            and (r["IS"].get("expectancy_r") or -1) > 0]
    print(f"{sym}: {len(cand)} candidates pass IS gates G1(n>={MIN_IS_TRADES})+G2(exp>0)",
          flush=True)
    bases = [live[sid] for sid in cand if sid in live]
    t0 = time.time()
    plc, meta, diag = PL.build_cohort(
        fr, bases, {sid: s1["rows"][sid]["FULL"].get("trades", 0) for sid in cand},
        seed=SEED, pool="eligible", kinds=PL.KINDS)
    print(f"{sym}: cohort {len(plc)} placebos from {len(bases)} bases "
          f"({time.time()-t0:.0f}s) diag={diag}", flush=True)
    engp = SessionEngine(fr, enforce_session_gap=gap)
    t0 = time.time()
    resp = engp.run_many(plc)
    print(f"{sym}: placebo run {time.time()-t0:.0f}s", flush=True)
    (OUT / f"ledger_placebo_{sym}_{tag}.json").write_text(json.dumps({
        "symbol": sym, "diag": diag,
        "meta": {k: vars(v) for k, v in meta.items()},
        "ledger": ledger(resp)}))
    print(f"{sym}: stage2 done", flush=True)


if __name__ == "__main__":
    gap = "--nogap" not in sys.argv
    for sym in [a for a in sys.argv[1:] if not a.startswith("--")] or ["MES", "MNQ"]:
        main(sym, gap)
