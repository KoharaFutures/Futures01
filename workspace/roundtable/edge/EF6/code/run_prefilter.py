"""Audit a generated population through the firing census: what share cannot trade?

This is the number EF2-EF5 quote before they measure anything, and it is
**per (symbol, timeframe)** because the rate is not transferable — R1 measured
MGC 11.5%, MCL 13.9%, MES 22.6%, MNQ 27.4% on one sample.

Two populations are audited:

* **R1-comparable**: ``generate_strategies(sym, [5,15,60,240], max_total=400)``,
  the exact call R1 used, audited against a census built on a base-5m frame
  carrying all four timeframes. Like-for-like with R1's 19.0%.
* **per-cell**: the population at each primary timeframe on its own FRAMES
  composition, which is what a per-cell sweep would actually screen.

A strategy's conditions are judged at the timeframe they are **actually
evaluated on**: ``cond.timeframe`` if set, otherwise ``primary_tf``, and
``entry_tf`` for trigger conditions `[repo-verified: base.py:653-700]`.
``firing._eval_tf`` mirrors that. This matters: **156 of 2,183 MGC conditions and
166 of 2,240 MNQ conditions in the R1 call carry an explicit ``timeframe``**
`[measured: Counter(c.timeframe ...) → MGC {None: 2027, 15: 44, 60: 26, 240: 86},
MNQ {None: 2074, 15: 36, 60: 76, 240: 54}]`, so judging every condition at
``primary_tf`` would misattribute a sixth of the 240m VOIDs.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from futures_agents.strategies.combinator import generate_strategies  # noqa: E402

import firing                                                # noqa: E402

CENSUS = "workspace/roundtable/edge/EF6/out/census"
OUT = "workspace/roundtable/edge/EF6/out"
SYMBOLS = ["MGC", "MCL", "MES", "MNQ"]


def audit_population(symbol: str, gen_tfs, census_file: str, *,
                     max_total: int, primary_only=None) -> dict:
    path = os.path.join(CENSUS, census_file)
    if not os.path.exists(path):
        return {"error": f"missing census {census_file}"}
    doc = firing.load_census(path)
    have = {int(t) for t in doc["eval_timeframes"]}
    gen = generate_strategies(symbol, list(gen_tfs), max_total=max_total)
    if primary_only is not None:
        gen = [s for s in gen if s.primary_tf == primary_only]
    covered, uncovered = [], []
    for s in gen:
        need = set(s.timeframes) | {s.primary_tf, s.entry_tf}
        need |= {c.timeframe for c in s.conditions if c.timeframe}
        need |= {c.timeframe for c in s.trigger_conditions if c.timeframe}
        (covered if need <= have else uncovered).append(s)
    rows = firing.audit(covered, doc)
    summ = firing.audit_summary(rows)
    summ.update(symbol=symbol, census=census_file,
                census_span=[doc.get("first_ts"), doc.get("last_ts")],
                signal_eligible_bars=doc["bars"]["signal_eligible"],
                generated=len(gen), audited=len(covered),
                skipped_timeframe_not_in_census=len(uncovered),
                uncovered_needs=sorted({tuple(sorted(
                    (set(s.timeframes) | {s.primary_tf, s.entry_tf}) - have))
                    for s in uncovered})[:8])
    return {"summary": summ, "rows": rows}


def main() -> int:
    out = {"r1_comparable": {}, "per_cell": {}}
    print("# R1-comparable: generate_strategies(sym, [5,15,60,240], max_total=400)")
    print("#   audited against a base-5m census carrying 5/15/60/240 "
          "(57.90-day substrate)\n")
    tot_v = tot_n = 0
    for sym in SYMBOLS:
        r = audit_population(sym, [5, 15, 60, 240],
                             f"census_{sym}_5m_frame5-15-60-240.json",
                             max_total=400)
        if "error" in r:
            print(f"  {sym}: {r['error']}")
            continue
        s = r["summary"]
        out["r1_comparable"][sym] = s
        tot_v += s["n_void"]
        tot_n += s["n_strategies"]
        print(f"  {sym}: generated {s['generated']}, audited {s['audited']}, "
              f"skipped(tf not in census) {s['skipped_timeframe_not_in_census']}"
              f" -> VOID {s['n_void']}/{s['n_strategies']} = {s['pct_void']}%"
              f"   THIN {s['n_thin']}")
        print(f"      by primary tf: {s['void_by_primary_tf']}")
        print(f"      by group     : {s['void_by_group']}")
        for c, n in list(s["void_causes"].items())[:10]:
            print(f"      cause {c}: {n}")
        print()
    if tot_n:
        print(f"  POOLED (for comparison with R1's 19.0% only; the per-symbol "
              f"numbers are the result): {tot_v}/{tot_n} = "
              f"{100.0*tot_v/tot_n:.1f}%\n")

    print("# per-cell: each primary timeframe on its own FRAMES composition\n")
    cells = [(5, [5, 15, 60], "frame5-15-60"),
             (15, [15, 60, 240], "frame15-60-240"),
             (30, [30, 60, 240], "frame30-60-240"),
             (60, [60, 240, 1440], "frame60-240-1440")]
    for sym in SYMBOLS:
        for base, tfs, tag in cells:
            r = audit_population(sym, tfs, f"census_{sym}_{base}m_{tag}.json",
                                 max_total=600, primary_only=base)
            if "error" in r:
                print(f"  {sym} {base}m: {r['error']}")
                continue
            s = r["summary"]
            out["per_cell"][f"{sym}_{base}m"] = s
            print(f"  {sym} {base:>3}m frame{tfs}: audited {s['audited']}"
                  f"/{s['generated']} -> VOID {s['n_void']} "
                  f"({s['pct_void']}%)  THIN {s['n_thin']}  "
                  f"causes {list(s['void_causes'].items())[:4]}")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "prefilter_summary.json"), "w") as fh:
        json.dump(out, fh, indent=1, default=str)
    print("\nwritten", os.path.join(OUT, "prefilter_summary.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
