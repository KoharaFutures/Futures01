"""R3 Tier 0 item 2 - ``bootstrap_paths(mode="block")`` versus ``mode="iid"``.

R3's claim: this is "one function call" and it "decides whether *any* streak-based
sizing or equity-curve rule can work", because no call site in the repo has ever
passed ``mode="block"`` `[repo-verified: montecarlo.py:84-110]`
`[measured: grep -rn 'mode="block"' --include=*.py . -> montecarlo.py:91 docstring only]`.

It *is* one call per arm, so it is done here. What it is not, and I am saying so
before the numbers rather than after, is a **test of serial dependence**. The two
modes are two resamplers. ``iid`` destroys serial structure by construction;
``block`` preserves runs of length ``block`` (default 10). Comparing their output
distributions detects dependence only *indirectly* and only at the block scale -
if the two agree, the reading is "no dependence detectable at a 10-trade scale by
this resampler", which is weaker than "the series is i.i.d.". The direct tests
(lag-1 autocorrelation, a runs test, a Ljung-Box over several lags) are not in
this repository and are not one call. That gap is filled in ``REQUESTS.md``.

Second, and this one changes the answer rather than hedging it: **the unit
matters and the pooled stream is the wrong unit.** ``geo_trades.json`` interleaves
176 strategies, so two adjacent trades in timestamp order are usually different
strategies on different symbols. Serial dependence in that stream is a property
of the calendar, not of a strategy. Two units are therefore reported:

  ``ACCOUNT``  the pooled stream in timestamp order. This is what an
               equity-curve or consecutive-loss rule on one account would
               actually see, so it is the right unit for governors P7/P8.
  ``STRATEGY`` each of the 176 ``(symbol, tf, arm, exitm)`` series separately.
               This is the right unit for "can streak sizing work on a
               strategy", and its 176 answers are correlated variants of two
               base conditions, so the count of significant ones is reported
               and no z is attached to their mean.
"""
from __future__ import annotations

import collections
import json
import os
import statistics as stats
import sys

ROOT = "/home/user/Futures01"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from futures_agents.backtest.montecarlo import monte_carlo   # noqa: E402

CACHE = os.path.join(ROOT, "workspace/roundtable/backtest/BT3/code/stops_cache.json")
OUT = os.path.join(ROOT, "workspace/roundtable/backtest/BT3/code/block_vs_iid.json")

RUNS = 2000
BLOCK = 10
SEED = 20260922      # montecarlo.py's own default, so this is reproducible


def arms(r, *, runs=RUNS):
    a = monte_carlo(r, runs=runs, mode="iid", block=BLOCK, seed=SEED)
    b = monte_carlo(r, runs=runs, mode="block", block=BLOCK, seed=SEED)
    return a, b


def delta(a, b) -> dict:
    """Block minus iid on the three statistics dependence would move."""
    return {
        "n": len(getattr(a, "_r", [])) or None,
        "iid_maxdd_p95": round(a.max_dd_p95, 4),
        "block_maxdd_p95": round(b.max_dd_p95, 4),
        "d_maxdd_p95": round(b.max_dd_p95 - a.max_dd_p95, 4),
        "iid_streak_p95": a.longest_losing_streak_p95,
        "block_streak_p95": b.longest_losing_streak_p95,
        "d_streak_p95": b.longest_losing_streak_p95 - a.longest_losing_streak_p95,
        "iid_final_p05": round(a.final_r_p05, 4),
        "block_final_p05": round(b.final_r_p05, 4),
        "d_final_p05": round(b.final_r_p05 - a.final_r_p05, 4),
    }


def main() -> None:
    rows = json.load(open(CACHE))
    rows.sort(key=lambda r: (r["ts"], r["symbol"], r["tf"], r["base"],
                             r["arm"], r["exitm"], r["dir"]))
    out: dict = {"runs": RUNS, "block": BLOCK, "seed": SEED}

    # ---- ACCOUNT: the pooled stream in timestamp order ------------------
    pooled = [float(r["r"]) for r in rows]
    a, b = arms(pooled)
    out["account"] = delta(a, b) | {"n": len(pooled)}
    print("ACCOUNT (pooled, ts order, n=%d):" % len(pooled))
    for k, v in out["account"].items():
        print("   ", k, v)

    # ---- STRATEGY: 176 series, each on its own ---------------------------
    by: dict = collections.defaultdict(list)
    for r in rows:
        by[(r["symbol"], r["tf"], r["arm"], r["exitm"])].append(float(r["r"]))
    per = []
    for k, rs in sorted(by.items()):
        if len(rs) < 20:
            continue
        a, b = arms(rs, runs=600)
        per.append({"strategy": "|".join(str(x) for x in k), "n": len(rs),
                    **delta(a, b)})
    out["strategy"] = {
        "n_series": len(per),
        "d_maxdd_p95_median": round(stats.median(p["d_maxdd_p95"] for p in per), 4),
        "d_maxdd_p95_mean": round(stats.mean(p["d_maxdd_p95"] for p in per), 4),
        "n_block_worse_maxdd": sum(1 for p in per if p["d_maxdd_p95"] > 0),
        "d_streak_p95_median": stats.median(p["d_streak_p95"] for p in per),
        "n_block_longer_streak": sum(1 for p in per if p["d_streak_p95"] > 0),
        "n_block_shorter_streak": sum(1 for p in per if p["d_streak_p95"] < 0),
        "rows": per,
    }
    s = out["strategy"]
    print(f"\nSTRATEGY ({s['n_series']} series with n>=20, 600 runs each):")
    print(f"    median d_maxdd_p95 (block - iid) = {s['d_maxdd_p95_median']:+.4f}R, "
          f"mean = {s['d_maxdd_p95_mean']:+.4f}R")
    print(f"    block's p95 drawdown is worse in {s['n_block_worse_maxdd']}"
          f"/{s['n_series']} series")
    print(f"    median d_streak_p95 = {s['d_streak_p95_median']:+g} trades; "
          f"longer in {s['n_block_longer_streak']}, "
          f"shorter in {s['n_block_shorter_streak']}")

    json.dump(out, open(OUT, "w"), indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
