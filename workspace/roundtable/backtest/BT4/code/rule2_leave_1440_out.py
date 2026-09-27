"""BT4 — how much of `BRIEF.md` rule 2's evidence came from the collapsed daily frame.

Rule 2 ("multi-timeframe agreement is not a virtue") cites `z = -4.09, 366 vs
1,151`. The single artefact behind that number is

    workspace/studies/out/g_multi_timeframe.json
      -> findings.ab_any_mtf_condition_vs_none

which reports 23 cells, 14 of them compared and 9 skipped for a thin arm, a
per-cell `z`, and a Stouffer combination over the 14.

**This script introduces no new comparative test.** It re-aggregates the study's
own per-cell statistics with the collapsed-frame cells removed, and verifies the
published combination reproduces before doing so — if I cannot reproduce -4.093
from the per-cell z values, I do not know what combination was used and no
leave-out figure I compute would mean anything.

Three caveats that travel with every number below:

* **D28.** The per-cell `z` is a rank sum over *strategies within a cell*, and
  correlated variants inside an arm are not independent observations, so every
  |z| here — the published one and the leave-out one — is inflated by an unknown
  factor whose measured central estimate is ~3.3x. The *ratio* between them is
  what this script is for; the absolute levels are not trustworthy.
* The sign test across cells is reported alongside, because it is the one figure
  in the payload that does not depend on the within-cell unit at all.
* Only the 1440m cells are treated as affected. The 240m frame `[240, 1440]` has
  the same two-voter degeneracy (D17, R4-MT2) but its confirming series is a
  genuine daily series, so it is NOT an `align_bucket` casualty and is left in.
"""
from __future__ import annotations

import collections
import json
import math
import os
from typing import Dict, List, Sequence

REPO = os.path.dirname(os.path.abspath(__file__)).split("/workspace/")[0]
PAYLOAD = os.path.join(REPO, "workspace/studies/out/g_multi_timeframe.json")


def stouffer(zs: Sequence[float]) -> float:
    return sum(zs) / math.sqrt(len(zs)) if zs else float("nan")


def binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Exact two-sided binomial p, by summing every outcome no likelier than k."""
    def pmf(i: int) -> float:
        return math.comb(n, i) * p ** i * (1 - p) ** (n - i)
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs + 1e-15))


def is_1440(cell: str) -> bool:
    """`symbol/tf/window/confirm_tfs` — the second field is the primary timeframe."""
    return cell.split("/")[1] == "1440"


def main() -> int:
    doc = json.load(open(PAYLOAD))
    f = doc["findings"]["ab_any_mtf_condition_vs_none"]
    cells = f["per_cell"]
    compared = [c for c in cells if "z" in c]
    skipped = [c for c in cells if "skipped" in c]

    published_z = f["stouffer_z"]
    repro = stouffer([c["z"] for c in compared])
    print(f"cells in payload: {len(cells)}  compared: {len(compared)}  "
          f"skipped: {len(skipped)}")
    print(f"published stouffer_z: {published_z}   reproduced from per-cell z: "
          f"{repro:.4f}   -> {'REPRODUCES' if abs(repro - published_z) < 5e-3 else 'DOES NOT REPRODUCE'}")

    daily = [c for c in compared if is_1440(c["cell"])]
    rest = [c for c in compared if not is_1440(c["cell"])]
    print(f"\ncollapsed-frame (1440m) cells among the 14 compared: {len(daily)}")
    for c in daily:
        print(f"    {c['cell']:<22} n_a={c['n_a']:>4} n_b={c['n_b']:>4} "
              f"delta={c['delta']:+.4f} z={c['z']:+.3f}")

    print(f"\n{'arm':<22}{'all 14':>12}{'1440m only':>14}{'11 non-1440':>14}")
    for arm, key in (("has_mtf_signal", "n_a"), ("no_mtf_signal", "n_b")):
        tot = sum(c[key] for c in compared)
        dly = sum(c[key] for c in daily)
        print(f"{arm:<22}{tot:>12}{dly:>14}{tot - dly:>14}"
              f"   ({100.0 * dly / tot:.1f}% of the arm is 1440m)")
    # The headline quotes 366 / 1151, which includes the thin arms of the nine
    # skipped cells. Reconcile, so the share is stated against the right base.
    print(f"\nheadline arm sizes: has={f['has_mtf_signal']['n_strategies']} "
          f"no={f['no_mtf_signal']['n_strategies']};  "
          f"sum over the 14 compared cells: has={sum(c['n_a'] for c in compared)} "
          f"no={sum(c['n_b'] for c in compared)}")

    print("\n--- Stouffer, published combination recomputed on subsets ---")
    for name, group in (("all 14 cells (published)", compared),
                        ("11 cells, 1440m removed", rest),
                        ("the 3 1440m cells alone", daily)):
        zs = [c["z"] for c in group]
        neg = sum(1 for z in zs if z < 0)
        print(f"  {name:<28} k={len(zs):>3}  stouffer z = {stouffer(zs):+.4f}   "
              f"cells negative {neg}/{len(zs)}  sign-test p = "
              f"{binom_two_sided(len(zs) - neg, len(zs)):.3f}")

    # What the surviving cells actually are. `ADJ-14` §4's restatement calls them
    # "the 60-minute frames"; they are not only 60m and saying so is a correction
    # in the un-conservative direction, which is the kind most worth stating.
    tfs = collections.Counter(c["cell"].split("/")[1] for c in rest)
    syms = sorted({c["cell"].split("/")[0] for c in rest})
    print(f"\n  the 11 surviving cells: timeframes {dict(sorted(tfs.items(), key=lambda kv: int(kv[0])))}"
          f"  symbols {syms}")

    print("\n--- leave-one-cell-out, for context on how much any single cell carries ---")
    for c in sorted(compared, key=lambda r: r["cell"]):
        others = [x["z"] for x in compared if x is not c]
        print(f"  drop {c['cell']:<22} -> stouffer z = {stouffer(others):+.4f}"
              f"{'   <- collapsed frame' if is_1440(c['cell']) else ''}")

    print("\n--- how much of the FLOORED population sat on a collapsed daily frame ---")
    sc = doc["findings"]["strategy_counts"]
    by = sc["by_cell"]
    tot_all = sum(v["all"] for v in by.values())
    dly_all = sum(v["all"] for k, v in by.items() if is_1440(k))
    tot_mtf = sum(v["mtf_group"] for v in by.values())
    dly_mtf = sum(v["mtf_group"] for k, v in by.items() if is_1440(k))
    tot_carry = sum(v["aligned"] + v["strong"] for v in by.values())
    dly_carry = sum(v["aligned"] + v["strong"] for k, v in by.items() if is_1440(k))
    print(f"  floored rows           {dly_all}/{tot_all} = {100.0*dly_all/tot_all:.1f}% at 1440m")
    print(f"  MULTI_TIMEFRAME group  {dly_mtf}/{tot_mtf} = {100.0*dly_mtf/tot_mtf:.1f}% at 1440m")
    print(f"  carrying an mtf SIGNAL {dly_carry}/{tot_carry} = "
          f"{100.0*dly_carry/tot_carry:.1f}% at 1440m")

    print("\n--- the other two rule-2 sentences ---")
    for key in ("ab_unanimous_vs_majority_3tf_frames",
                "ab_unanimous_vs_majority_2tf_frames_DEGENERATE",
                "ab_MTF_group_vs_rest"):
        g = doc["findings"].get(key)
        if not isinstance(g, dict):
            continue
        cc = [c for c in g.get("per_cell", []) if "z" in c]
        d = [c for c in cc if is_1440(c["cell"])]
        print(f"  {key}")
        print(f"      cells compared {len(cc)}, of which 1440m {len(d)}"
              f"   stouffer {g.get('stouffer_z')}"
              f"   -> without 1440m: "
              f"{stouffer([c['z'] for c in cc if not is_1440(c['cell'])]):+.4f}"
              if cc else "      no per-cell comparison in this payload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
