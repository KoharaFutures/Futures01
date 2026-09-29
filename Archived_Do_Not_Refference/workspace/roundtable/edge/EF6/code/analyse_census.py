"""Turn the census artefacts into the per-(symbol, timeframe) VOID verdict table
and into the structural-VOID share of a generated population.

Two outputs:

* ``void_table.json`` / printed table — per cell, every (condition, eval tf)
  that fires on **0** signal-eligible bars, plus THIN ones, plus any condition
  whose zeros are accompanied by swallowed exceptions (which is a defect, not a
  market fact).
* ``prefilter_<sym>.json`` — the audit of an actual generated population through
  ``firing.prefilter``, which is the number EF2-EF5 quote: what share of what
  they generated cannot trade, per symbol and per primary timeframe.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "/home/user/Futures01")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from futures_agents.strategies.combinator import generate_strategies  # noqa: E402

import arms                                                 # noqa: E402
import firing                                                # noqa: E402

CENSUS_DIR = "workspace/roundtable/edge/EF6/out/census"
OUT_DIR = "workspace/roundtable/edge/EF6/out"


def void_table(docs):
    rows = []
    for doc in docs:
        cell = doc["cell"]
        errs = Counter(k.split(":")[0] for k in doc.get("condition_errors", {}))
        for key, rec in sorted(doc["fires"].items()):
            name, tf = key.rsplit("@", 1)
            kind = doc["kinds"][name]
            grp = doc["groups"][name]
            ev = doc["evaluable_bars_by_tf"].get(tf, 0)
            v = ("VOID" if rec["signal"] == 0
                 else "THIN" if rec["signal"] < firing.THIN_FIRES else "ALIVE")
            rows.append({
                "cell": cell, "symbol": doc["symbol"],
                "base_tf": doc["base_minutes"], "frame": doc["frame_requested"],
                "condition": name, "eval_tf": int(tf), "kind": kind, "group": grp,
                "fires_all": rec["all"], "fires_window": rec["window"],
                "fires_signal": rec["signal"],
                "signal_bars": doc["bars"]["signal_eligible"],
                "evaluable_bars": ev,
                "rate_signal": round(rec["signal"] / max(1, doc["bars"]["signal_eligible"]), 5),
                "verdict": v,
                "lost_to_window": rec["all"] - rec["signal"],
                "raised": errs.get(name, 0),
                "directions": doc.get("directions", {}).get(key, {}),
            })
    return rows


def main() -> int:
    docs = []
    for p in sorted(glob.glob(os.path.join(CENSUS_DIR, "census_*.json"))):
        with open(p) as fh:
            docs.append(json.load(fh))
    if not docs:
        print("no census documents yet")
        return 1
    rows = void_table(docs)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "void_table.json"), "w") as fh:
        json.dump(rows, fh, indent=1)

    # ---- per-cell VOID / THIN listing -------------------------------------
    print(f"# census cells: {len(docs)}   (condition, tf) pairs: {len(rows)}\n")
    by_cell = defaultdict(list)
    for r in rows:
        by_cell[r["cell"]].append(r)
    for cell in sorted(by_cell):
        rs = by_cell[cell]
        d = rs[0]
        voids = [r for r in rs if r["verdict"] == "VOID"]
        thins = [r for r in rs if r["verdict"] == "THIN"]
        print(f"## {cell}   signal-eligible bars = {d['signal_bars']}")
        if not voids:
            print("   VOID: none")
        for r in sorted(voids, key=lambda x: (x["eval_tf"], x["condition"])):
            extra = f"  [RAISED {r['raised']}x - DEFECT not a market fact]" if r["raised"] else ""
            allf = f"  (fires_all={r['fires_all']}"
            allf += f", lost to window={r['lost_to_window']})" if r["fires_all"] else ")"
            print(f"   VOID {r['condition']}@{r['eval_tf']}m [{r['kind']}/{r['group']}]"
                  f"{allf}{extra}")
        for r in sorted(thins, key=lambda x: (x["eval_tf"], x["condition"])):
            print(f"   THIN {r['condition']}@{r['eval_tf']}m [{r['kind']}/{r['group']}]"
                  f" {r['fires_signal']} fires")
        print()

    # ---- window-only kills: alive on all bars, VOID on signal bars --------
    wk = [r for r in rows if r["verdict"] == "VOID" and r["fires_all"] > 0]
    print("# conditions killed BY THE WINDOW ALONE (fire on some bar, never on a "
          "legal-entry bar)")
    if not wk:
        print("  none\n")
    for r in wk:
        print(f"  {r['cell']}: {r['condition']}@{r['eval_tf']}m - "
              f"{r['fires_all']} fires, 0 legal\n")

    # ---- cross-cell: is a VOID global or per-cell? ------------------------
    print("# is each VOID global or per (symbol, timeframe)?")
    per_cond = defaultdict(lambda: {"VOID": [], "ALIVE": [], "THIN": []})
    for r in rows:
        per_cond[(r["condition"], r["eval_tf"])][r["verdict"]].append(r["symbol"])
    mixed = {k: v for k, v in per_cond.items() if v["VOID"] and (v["ALIVE"] or v["THIN"])}
    allvoid = {k: v for k, v in per_cond.items() if v["VOID"] and not v["ALIVE"] and not v["THIN"]}
    print(f"  VOID in every cell measured : {len(allvoid)} (condition, tf) pairs")
    for k in sorted(allvoid):
        print(f"     {k[0]}@{k[1]}m  ({len(allvoid[k]['VOID'])} cells)")
    print(f"  VOID in SOME cells only     : {len(mixed)} - these are why VOID is "
          f"per (symbol, timeframe)")
    for k in sorted(mixed):
        v = mixed[k]
        print(f"     {k[0]}@{k[1]}m  VOID in {sorted(set(v['VOID']))} "
              f"alive in {sorted(set(v['ALIVE'] + v['THIN']))}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
