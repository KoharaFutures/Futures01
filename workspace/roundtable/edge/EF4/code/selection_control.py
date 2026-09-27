"""EF4 - controls for the selection test, because its first reading is almost certainly wrong.

The raw result (`analyse2.py`) is that the in-sample top 10 BEAT the whole qualifying universe
out of sample in 3 of 4 cells - the opposite sign to the programme's own settled negative
(-0.0155R for last period's top 10 against +0.022R for the universe). A result that reverses a
settled finding on 41 sessions needs its controls before it needs a headline, and there are
three specific ways it could be an artefact:

**Artefact 1 - the universe average is trade-weighted.** Pooling by trade count makes the
universe number dominated by the arms that trade MOST. Those are the arms whose signal fires
often, which on a scalp cell are also the arms paying the most cost per unit of R. So
"top 10 beats the universe" may be nothing but "arms that trade rarely have better expectancy
than arms that trade constantly", which is a cost fact, not a selection skill.
Control: **RANDOM-10** - draw 10 arms uniformly from the same qualifying universe and pool
their OOS the same way, 2,000 times. If random 10 also beats the universe, the comparison is
broken rather than the selection informative.

**Artefact 2 - trade count is confounded with expectancy.** Control: **MATCHED-10** - draw 10
arms whose in-sample trade counts match the real top 10's (nearest-neighbour on IS trades,
sampled without replacement), 2,000 times. This holds the confound and lets selection show
whatever is left.

**Artefact 3 - the top 10 are not 10 independent things.** Ten arms sharing a signal condition
have near-identical trade lists, so pooling 366 of their trades is not 366 independent
observations and its standard error is understated. Measured directly: the number of DISTINCT
conditions across the top 10, and the mean pairwise overlap of their condition sets.

**And the direction test.** A forward-predictive selection must work forwards only. Selecting
on the LAST 40% and scoring on the FIRST 60% reverses the arrow of time; if selection "wins"
in both directions it is picking up a stationary property of the arms, not persistence.
"""
from __future__ import annotations

import json
import random
import statistics as st
import sys
from pathlib import Path

ROOT = Path("/home/user/Futures01")
OUT = ROOT / "workspace/roundtable/edge/EF4/out"
CELLS = [(s, tf) for s in ("MGC", "MCL") for tf in (5, 15, 30)]
MIN_TRADES = 30
DRAWS = 2000


def pooled(rows, half):
    num = sum(r[half]["expectancy_net_r"] * r[half]["trades"] for r in rows)
    den = sum(r[half]["trades"] for r in rows)
    return num / den if den else 0.0


def unweighted(rows, half):
    xs = [r[half]["expectancy_net_r"] for r in rows if r[half]["trades"] > 0]
    return st.mean(xs) if xs else 0.0


def main() -> None:
    out = []
    for sym, tf in CELLS:
        p = OUT / f"run_{sym}_{tf}m_both.json"
        if not p.is_file():
            continue
        d = json.loads(p.read_text())
        uni = [r for r in d["rows"] if r["group"] == "EF4_SCREEN"
               and r["is"]["trades"] >= MIN_TRADES and r["oos"]["trades"] >= MIN_TRADES]
        if len(uni) < 40:
            continue
        rng = random.Random(4242)
        top = sorted(uni, key=lambda r: -r["is"]["expectancy_net_r"])[:10]
        real_oos = pooled(top, "oos")
        uni_oos = pooled(uni, "oos")

        # control 1: random 10
        rnd = []
        for _ in range(DRAWS):
            rnd.append(pooled(rng.sample(uni, 10), "oos"))
        # control 2: trade-count matched 10
        by_is = sorted(uni, key=lambda r: r["is"]["trades"])
        counts = [r["is"]["trades"] for r in top]
        matched = []
        for _ in range(DRAWS):
            pick, used = [], set()
            for c in counts:
                cands = sorted((abs(r["is"]["trades"] - c), i)
                               for i, r in enumerate(by_is) if i not in used)[:25]
                if not cands:
                    break
                _, i = cands[rng.randrange(len(cands))]
                used.add(i); pick.append(by_is[i])
            if len(pick) == len(counts):
                matched.append(pooled(pick, "oos"))

        # control 3: independence of the top 10
        condsets = [frozenset(r["conditions"]) for r in top]
        distinct = len(set().union(*condsets)) if condsets else 0
        ov = []
        for i in range(len(condsets)):
            for j in range(i + 1, len(condsets)):
                u = len(condsets[i] | condsets[j])
                ov.append(len(condsets[i] & condsets[j]) / u if u else 0.0)

        # reverse-time selection
        rtop = sorted(uni, key=lambda r: -r["oos"]["expectancy_net_r"])[:10]
        rev_is = pooled(rtop, "is")
        uni_is = pooled(uni, "is")

        row = {
            "symbol": sym, "tf": tf, "universe": len(uni),
            "top10_oos": real_oos, "universe_oos": uni_oos,
            "random10_oos_mean": st.mean(rnd), "random10_oos_sd": st.pstdev(rnd),
            "top10_percentile_in_random10": sum(1 for x in rnd if real_oos > x) / len(rnd),
            "matched10_oos_mean": (st.mean(matched) if matched else None),
            "matched10_oos_sd": (st.pstdev(matched) if matched else None),
            "top10_percentile_in_matched10": (sum(1 for x in matched if real_oos > x) / len(matched)) if matched else None,
            "top10_is_trades": sum(r["is"]["trades"] for r in top),
            "top10_oos_trades": sum(r["oos"]["trades"] for r in top),
            "median_is_trades_top10": st.median(counts),
            "median_is_trades_universe": st.median(r["is"]["trades"] for r in uni),
            "top10_distinct_conditions": distinct,
            "top10_mean_pairwise_condition_jaccard": (st.mean(ov) if ov else 0.0),
            "reverse_time_top10_is": rev_is, "universe_is": uni_is,
            "reverse_selection_also_wins": rev_is > uni_is,
            "unweighted_universe_oos": unweighted(uni, "oos"),
            "unweighted_top10_oos": unweighted(top, "oos"),
        }
        out.append(row)
        print(f"\n--- {sym} {tf}m  universe={len(uni)}")
        print(f"  top10 OOS  = {real_oos:+.4f}   universe OOS (trade-weighted) = {uni_oos:+.4f}")
        print(f"  RANDOM-10  OOS = {row['random10_oos_mean']:+.4f} +- "
              f"{row['random10_oos_sd']:.4f}   top10 percentile = "
              f"{row['top10_percentile_in_random10']:.3f}")
        if matched:
            print(f"  MATCHED-10 OOS = {row['matched10_oos_mean']:+.4f} +- "
                  f"{row['matched10_oos_sd']:.4f}   top10 percentile = "
                  f"{row['top10_percentile_in_matched10']:.3f}")
        print(f"  median IS trades: top10 {row['median_is_trades_top10']:.0f} vs "
              f"universe {row['median_is_trades_universe']:.0f}")
        print(f"  top10 independence: {distinct} distinct conditions across 10 arms, "
              f"mean pairwise condition Jaccard {row['top10_mean_pairwise_condition_jaccard']:.3f}")
        print(f"  REVERSE TIME (select on OOS, score on IS): {rev_is:+.4f} vs universe IS "
              f"{uni_is:+.4f} -> {'ALSO WINS' if rev_is > uni_is else 'loses'}")
        print(f"  unweighted universe OOS = {row['unweighted_universe_oos']:+.4f} "
              f"(vs trade-weighted {uni_oos:+.4f})")
    (OUT / "selection_control.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT / 'selection_control.json'}")


if __name__ == "__main__":
    main()
