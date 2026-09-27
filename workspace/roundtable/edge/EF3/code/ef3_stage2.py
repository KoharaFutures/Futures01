"""EF3 stage 2 - the placebo cohort. Reads stage 1's ledger; runs only placebos.

Cohort built over the FULL span so a placebo count-matches its base's full-span
raw signal count and every window comparison is like-for-like. Kinds:
  placebo_random   honest - destroys when and which way
  placebo_shuffle  honest - keeps when, destroys which way
  placebo_shift    LEAKS (D42): conservative-only, reported, never gated on
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, "/home/user/Futures01/workspace")
sys.path.insert(0, "/home/user/Futures01/workspace/roundtable/edge/EF3/code")

from ef3_measure import frame_for, ledger_of, IS_FRAC, MIN_IS_TRADES
from ef3_population import build
from ef3_session import SessionEngine, flat_exit_keys, violations
from newstrats import placebo as PL

OUT = Path("/home/user/Futures01/workspace/roundtable/edge/EF3/out")
SEED = 20260922


def main(sym: str, gap: bool = True):
    tag = "gap" if gap else "nogap"
    s1 = json.loads((OUT / f"stage1_{sym}_{tag}.json").read_text())
    cut = s1["is_cut"]
    led = s1["ledger"]
    fr, base = frame_for(sym)
    pop = build(sym, 4000)
    live = {sid: s for sid, s in pop["pop"].items() if sid not in pop["dead"]}

    # candidates: IS gates G1 + G2 on the ledger's IS slice
    cand = []
    for sid, rows in led.items():
        isr = [t[2] for t in rows if t[0] < cut]
        if len(isr) >= MIN_IS_TRADES and sum(isr) / len(isr) > 0:
            cand.append(sid)
    print(f"{sym}: {len(cand)} candidates pass G1(n>={MIN_IS_TRADES})+G2(exp>0) on IS",
          flush=True)
    bases = [live[sid] for sid in cand if sid in live]
    t0 = time.time()
    plc, meta, diag = PL.build_cohort(
        fr, bases, {sid: len(led.get(sid, [])) for sid in cand},
        seed=SEED, pool="eligible", kinds=PL.KINDS)
    print(f"{sym}: cohort {len(plc)} placebos from {len(bases)} bases "
          f"({time.time()-t0:.0f}s) diag={diag}", flush=True)
    engp = SessionEngine(fr, enforce_session_gap=gap)
    t0 = time.time()
    resp = engp.run_many(plc)
    print(f"{sym}: placebo run {time.time()-t0:.0f}s "
          f"violations={len(violations([t for r in resp.values() for t in r.trades], flat_exits=flat_exit_keys(engp)))}",
          flush=True)
    (OUT / f"ledger_placebo_{sym}_{tag}.json").write_text(json.dumps({
        "symbol": sym, "diag": diag, "n_bases": len(bases),
        "meta": {k: vars(v) for k, v in meta.items()},
        "counters": engp.counters.to_dict(),
        "ledger": ledger_of(resp)}))
    print(f"{sym}: stage2 done", flush=True)


if __name__ == "__main__":
    gap = "--nogap" not in sys.argv
    for sym in [a for a in sys.argv[1:] if not a.startswith("--")] or ["MES", "MNQ"]:
        main(sym, gap)
