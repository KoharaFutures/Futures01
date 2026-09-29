"""Turn EF2/data/census.json into the per-cell VOID verdict table."""
from __future__ import annotations

import json
import os
import sys

REPO = "/home/user/Futures01"
OUT = os.path.join(REPO, "workspace", "roundtable", "edge", "EF2", "data")
CELLS = [
    ("MGC:f60__p60", "MGC:f60", 60), ("MGC:f240__p240", "MGC:f240", 240),
    ("MGC:f60_240__p60", "MGC:f60_240", 60), ("MGC:f60_240__p240", "MGC:f60_240", 240),
    ("MCL:f60__p60", "MCL:f60", 60), ("MCL:f240__p240", "MCL:f240", 240),
    ("MCL:f60_240__p60", "MCL:f60_240", 60), ("MCL:f60_240__p240", "MCL:f60_240", 240),
]


def load():
    with open(os.path.join(OUT, "census.json")) as fh:
        return json.load(fh)


def cell_rows(d, frame_ref, primary_tf):
    """Rows at the binding a strategy in this cell actually uses for its
    PRIMARY conditions. Conditions bound upward by the combinator (structure
    SIGNALs when >=3 signals and confirm_tfs is non-empty) are reported
    separately by bound_tf."""
    rows = d["frames"][frame_ref]["rows"]
    return {(r["condition"], r["bound_tf"]): r for r in rows}


def main() -> None:
    d = load()
    report = {"cells": {}}
    for cell, frame_ref, ptf in CELLS:
        fr = d["frames"][frame_ref]
        by = cell_rows(d, frame_ref, ptf)
        prim = {k: v for k, v in by.items() if k[1] == ptf}
        void_raw = sorted(k[0] for k, v in prim.items() if v["verdict"] == "VOID_RAW")
        void_in = sorted(k[0] for k, v in prim.items() if v["verdict"] == "VOID_IN_STRATEGY")
        report["cells"][cell] = {
            "frame_ref": frame_ref, "primary_tf": ptf,
            "bars": fr["bars_evaluated"], "bars_rth": fr["bars_rth"],
            "bars_swing_admissible": fr["bars_swing_admissible"],
            "bars_rth_and_swing": fr["bars_rth_and_swing"],
            "n_conditions": len(prim),
            "VOID_RAW": void_raw, "VOID_IN_STRATEGY": void_in,
            "n_void": len(void_raw) + len(void_in),
        }
        # rates for the live ones, for the FINDINGS table
        report["cells"][cell]["live_rates"] = {
            k[0]: round(v["rate_usable"], 5)
            for k, v in sorted(prim.items()) if v["verdict"] == "LIVE"}
        # and the bound-upward bindings that exist in this frame
        other = sorted({k[1] for k in by} - {ptf})
        for tf in other:
            sub = {k: v for k, v in by.items() if k[1] == tf}
            report["cells"][cell][f"bound_{tf}m_VOID"] = sorted(
                k[0] for k, v in sub.items() if v["verdict"] != "LIVE")
    with open(os.path.join(OUT, "census_verdicts.json"), "w") as fh:
        json.dump(report, fh, indent=1)

    # ---- human table
    print("## Firing-rate census — EF2 four cells (archive 60m base, 718 days)\n")
    print("| cell | bars | RTH bars | swing-admissible | RTH and swing | VOID_RAW | VOID_IN_STRATEGY | total VOID / 79 |")
    print("|---|---|---|---|---|---|---|---|")
    for cell, _, _ in CELLS:
        c = report["cells"][cell]
        print(f"| `{cell}` | {c['bars']:,} | {c['bars_rth']:,} | "
              f"{c['bars_swing_admissible']:,} | {c['bars_rth_and_swing']:,} | "
              f"{len(c['VOID_RAW'])} | {len(c['VOID_IN_STRATEGY'])} | **{c['n_void']}/79** |")
    print()
    for cell, _, _ in CELLS:
        c = report["cells"][cell]
        print(f"**`{cell}`**")
        print(f"- VOID_RAW (0 fires on any bar): {', '.join('`'+x+'`' for x in c['VOID_RAW']) or 'none'}")
        print(f"- VOID_IN_STRATEGY (fires, but never on a bar a strategy could act on): "
              f"{', '.join('`'+x+'`' for x in c['VOID_IN_STRATEGY']) or 'none'}")
        for k in c:
            if k.startswith("bound_"):
                print(f"- {k}: {', '.join('`'+x+'`' for x in c[k]) or 'none'}")
        print()


if __name__ == "__main__":
    main()
