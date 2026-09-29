"""BT4 — the per-store accounting of results that ran on a 1440m frame.

`tf1440_census.py` sweeps blindly and double counts (a `cells/` row is counted
again inside `all_rows.json`). This module knows each store's schema and counts
its **native unit** once, so the totals can be added up.

The load-bearing definition, stated because everything downstream rests on it:

> A stored result "ran on a 1440m frame" iff it was produced with a primary
> timeframe of 1440. Every harness in this repository resolves its timeframe
> list from a `FRAMES`-shaped map keyed on the primary and then keeps only the
> strategies whose `primary_tf` equals that key, so a primary of 1440 implies
> the frame `[1440, 7200]` and therefore the collapse.

Two things that do NOT count, and both were checked rather than assumed:

* A 60m result is run against `FRAMES[60] = [60, 240, 1440]`, so it *contains*
  a 1440 member. That member is a genuine daily series — the collapse needs a
  request above 1440 — so 60m rows are unaffected and are not counted.
* A 240m result runs `[240, 1440]`: two voters, but the confirming series is
  genuine. Degenerate under D17 / R4-MT2, not under R4-M3. Not counted.
"""
from __future__ import annotations

import collections
import json
import os
from typing import Dict, List

REPO = os.path.dirname(os.path.abspath(__file__)).split("/workspace/")[0]


def j(rel: str):
    return json.load(open(os.path.join(REPO, rel)))


def rows_by_tf(path: str, row_key: str = "rows") -> collections.Counter:
    d = j(path)
    rows = d[row_key] if isinstance(d, dict) else d
    return collections.Counter(r.get("tf") for r in rows)


def main() -> int:
    out: List[Dict] = []

    # --- 1. bigscan: the 21-study-programme ranking corpus ------------------
    c = rows_by_tf("workspace/bigscan/all_rows.json")
    cells = [f for f in os.listdir(os.path.join(REPO, "workspace/bigscan/cells"))
             if "_1440m_" in f]
    out.append(dict(store="workspace/bigscan/all_rows.json",
                    unit="floored strategy rows", at_1440=c[1440], total=sum(c.values()),
                    detail=f"{len(cells)} of "
                           f"{len(os.listdir(os.path.join(REPO, 'workspace/bigscan/cells')))}"
                           f" cell files are 1440m: {sorted(cells)}"))

    # --- 2. focus: the second ranking corpus -------------------------------
    c = rows_by_tf("workspace/focus/all_rows.json")
    fcells = [f for f in os.listdir(os.path.join(REPO, "workspace/focus/cells"))
              if "_1440m_" in f]
    out.append(dict(store="workspace/focus/all_rows.json",
                    unit="floored strategy rows", at_1440=c[1440], total=sum(c.values()),
                    detail=f"{len(fcells)} 1440m cell files: {sorted(fcells)}"))

    # --- 3. chronology study ------------------------------------------------
    tot_s = tot_t = tot_m = 0
    chrono = []
    for sym in ("MGC", "MES", "MNQ"):
        d = j(f"workspace/chrono/ledgers/{sym}_1440.json")
        chrono.append(f"{sym}: {d['strategies']} strategies, {d['trades']:,} trades, "
                      f"{d['months']} months, {d['bars']} bars [{d['span']}]")
        tot_s += d["strategies"]
        tot_t += d["trades"]
        tot_m += d["months"]
    for sym, tf in (("MGC", 60), ("MES", 60), ("MNQ", 60), ("MCL", 60)):
        p = f"workspace/chrono/ledgers/{sym}_{tf}.json"
        if os.path.exists(os.path.join(REPO, p)):
            d = j(p)
            chrono.append(f"(not counted) {sym} {tf}m: {d['strategies']} strategies, "
                          f"{d['months']} months")
    out.append(dict(store="workspace/chrono/ledgers/*_1440.json",
                    unit="strategies / trades / month-buckets",
                    at_1440=f"{tot_s} strategies, {tot_t:,} trades, {tot_m} month-buckets",
                    total="3 of the 6 chrono ledgers are 1440m",
                    detail=" | ".join(chrono)))

    # --- 4. the MTF study that rule 2 rests on -----------------------------
    d = j("workspace/studies/out/g_multi_timeframe.json")
    by = d["findings"]["strategy_counts"]["by_cell"]
    dly = {k: v for k, v in by.items() if k.split("/")[1] == "1440"}
    out.append(dict(store="workspace/studies/out/g_multi_timeframe.json",
                    unit="floored strategy rows in the study's own cells",
                    at_1440=sum(v["all"] for v in dly.values()),
                    total=sum(v["all"] for v in by.values()),
                    detail=f"{len(dly)} of {len(by)} cells at 1440m: {sorted(dly)}"))

    # --- 4b. the 21-study programme, payload by payload ---------------------
    # A first pass of this counted only `g_*` files with a `cell` field shaped
    # `SYM/tf/window/confirm` and reported "6 of 21". That was wrong and
    # undercounted by eleven: the `x_*` studies name their daily arms
    # differently (`MES_1440_274`, `('MGC', 1440)`, `MES-1440m-<id>`, or just
    # "MNQ daily" in prose), so a single cell-key pattern misses them. The
    # correct sweep walks every dict key AND every cell/arm/name/id value.
    PROGRAMME = (["d_dead_groups"]
                 + [f"g_{x}" for x in ("breakout", "fibonacci", "liquidity",
                                       "mean_reversion", "momentum", "multi_timeframe",
                                       "opening_range", "pullback", "reversal",
                                       "supply_demand", "trend", "volume_profile",
                                       "vwap")]
                 + [f"x_{x}" for x in ("conditions", "confluence", "costs", "exits",
                                       "regime", "robustness", "session", "timeframes")])

    def names(o, acc):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(k, str):
                    acc.add(k)
                if k in ("cell", "arm", "name", "id") and isinstance(v, str):
                    acc.add(v)
                names(v, acc)
        elif isinstance(o, list):
            for v in o:
                names(v, acc)

    with_arm, without = [], []
    for sid in PROGRAMME:
        p = f"workspace/studies/out/{sid}.json"
        if not os.path.exists(os.path.join(REPO, p)):
            continue
        acc = set()
        names(j(p), acc)
        found = sorted(s for s in acc if "1440" in s or " daily" in s.lower())
        (with_arm if found else without).append((sid, len(found), found[:3]))
    out.append(dict(store="the 21-study programme (workspace/studies/out/{d,g,x}_*.json)",
                    unit="study payloads carrying a 1440m arm",
                    at_1440=len(with_arm), total=len(with_arm) + len(without),
                    detail="WITH: " + ", ".join(f"{s}({n})" for s, n, _ in with_arm)
                           + "  ||  WITHOUT: " + ", ".join(s for s, _, _ in without)))

    # --- 5. the 14 other per-group studies ---------------------------------
    gdir = os.path.join(REPO, "workspace/studies/out")
    grp = []
    for fn in sorted(os.listdir(gdir)):
        if not fn.startswith("g_") or fn == "g_multi_timeframe.json":
            continue
        d = j(f"workspace/studies/out/{fn}")
        hits = collections.Counter()
        stack = [d]
        while stack:
            o = stack.pop()
            if isinstance(o, dict):
                if isinstance(o.get("cell"), str) and len(o["cell"].split("/")) > 1:
                    hits[o["cell"].split("/")[1]] += 1
                stack.extend(v for v in o.values() if isinstance(v, (dict, list)))
            elif isinstance(o, list):
                stack.extend(v for v in o if isinstance(v, (dict, list)))
        if hits:
            grp.append(f"{fn}: 1440m cells {hits.get('1440', 0)}/{sum(hits.values())}")
    out.append(dict(store="workspace/studies/out/g_*.json (the other 13 group studies)",
                    unit="per-cell comparisons", at_1440="see detail", total="",
                    detail=" | ".join(grp)))

    # --- 6. research_plan position screens ---------------------------------
    for sym in ("MGC", "MNQ", "MES"):
        p = f"workspace/research_plan/screen_{sym}_position.json"
        if not os.path.exists(os.path.join(REPO, p)):
            continue
        d = j(p)
        rows = d if isinstance(d, list) else d.get("rows", d.get("results", []))
        c = collections.Counter(r.get("timeframe", r.get("tf")) for r in rows
                                if isinstance(r, dict))
        out.append(dict(store=p, unit="screened strategy rows",
                        at_1440=c.get(1440, 0), total=sum(c.values()),
                        detail=f"tf census {dict(c)}"))

    # --- 7. the ICT sweep programme ----------------------------------------
    d = j("workspace/studies/out/ict_sweep_mss_census.json")
    hits = collections.Counter()
    stack = [d]
    while stack:
        o = stack.pop()
        if isinstance(o, dict):
            if isinstance(o.get("tf"), int):
                hits[o["tf"]] += 1
            stack.extend(v for v in o.values() if isinstance(v, (dict, list)))
        elif isinstance(o, list):
            stack.extend(v for v in o if isinstance(v, (dict, list)))
    out.append(dict(store="workspace/studies/out/ict_sweep_mss_census.json",
                    unit="census rows", at_1440=hits.get(1440, 0), total=sum(hits.values()),
                    detail=f"tf census {dict(sorted(hits.items()))}"))

    for r in out:
        print(f"\n{r['store']}")
        print(f"  unit: {r['unit']}")
        print(f"  at 1440m: {r['at_1440']}   of {r['total']}")
        print(f"  {r['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
