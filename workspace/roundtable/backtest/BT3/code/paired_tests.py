"""Paired tests over the seed ensemble. Named, because PIPELINE §4 requires it.

Every arm of ALGO-1 is run over the **same 200 within-timestamp permutations**,
so the arms are paired by seed and the ordering - which is the single largest
source of variance in this replay, a 2x spread in `taken` - is common to both
sides of every comparison. An unpaired test would throw that away, which is the
same error D28 records for `T.ab`.

Two tests, both exact, both on the paired design:

  * **McNemar's exact test** for the binary outcome "did this seed's account
    reach the absorbing state". Only the discordant pairs carry information, and
    with n_discordant in the tens an exact binomial is right and a chi-square
    approximation is not.
  * **The exact sign test** (a two-sided binomial on the sign of the per-seed
    difference) for `taken`. Distribution-free, which matters because the
    per-seed `taken` distribution is bimodal - it partly encodes whether and
    when the account died - so a t-test on it would be testing a mixture.

No z is produced for anything pooled across the 176 strategies: those are
correlated variants of two base conditions and their inflation factor is not
established here.
"""
from __future__ import annotations

import json
import math
import os
import sys

ROOT = "/home/user/Futures01"
REPORT = os.path.join(ROOT,
                      "workspace/roundtable/backtest/BT3/code/algo1_report.json")


def binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Exact two-sided binomial p-value by the method of small likelihoods."""
    if n == 0:
        return 1.0

    def pmf(i: int) -> float:
        return math.comb(n, i) * p ** i * (1.0 - p) ** (n - i)

    obs = pmf(k)
    # Sum every outcome no more likely than the observed one. Exact, and it is
    # the definition that does not assume symmetry.
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs * (1 + 1e-12)))


def mcnemar(a: list, b: list) -> dict:
    """Exact McNemar over paired binary outcomes ``a`` and ``b``."""
    assert len(a) == len(b)
    b01 = sum(1 for x, y in zip(a, b) if (not x) and y)
    b10 = sum(1 for x, y in zip(a, b) if x and (not y))
    n_disc = b01 + b10
    return {"test": "McNemar exact (paired binomial on discordant seeds)",
            "n_pairs": len(a), "a_only": b10, "b_only": b01,
            "n_discordant": n_disc,
            "p_two_sided": binom_two_sided(b10, n_disc) if n_disc else 1.0}


def sign_test(a: list, b: list) -> dict:
    """Exact two-sided sign test on the per-seed difference ``a - b``."""
    pos = sum(1 for x, y in zip(a, b) if x > y)
    neg = sum(1 for x, y in zip(a, b) if x < y)
    n = pos + neg
    return {"test": "exact sign test (two-sided binomial, ties dropped)",
            "n_pairs": len(a), "a_greater": pos, "b_greater": neg,
            "ties": len(a) - n,
            "median_diff": (sorted(x - y for x, y in zip(a, b))[len(a) // 2]),
            "p_two_sided": binom_two_sided(pos, n) if n else 1.0}


def main() -> None:
    rep = json.load(open(REPORT))
    pr = rep["primary"]
    real = pr["vol_aware_barrier"]
    out = {}

    for name, other in (("placebo_ensemble", "neutral vs placebo (R permuted)"),
                        ("vol_pinned_control", "neutral vs volatility pinned"),
                        ("barrier_off_leak", "neutral vs barrier removed"),
                        ("honest_arm_live_eligible_False",
                         "neutral vs honest (is_live_eligible=False)")):
        o = pr[name]
        out[name] = {
            "comparison": other,
            "absorbing": mcnemar(real["absorbing_by_seed"],
                                 o["absorbing_by_seed"]),
            "taken": sign_test(real["taken_by_seed"], o["taken_by_seed"]),
            "absorbing_rate_real": real["pct_absorbing"],
            "absorbing_rate_other": o["pct_absorbing"],
            "taken_median_real": real["taken_pct_median"],
            "taken_median_other": o["taken_pct_median"],
        }

    dest = os.path.join(ROOT,
                        "workspace/roundtable/backtest/BT3/code/paired_tests.json")
    json.dump(out, open(dest, "w"), indent=1)

    #: **Search size: 8.** Four arm comparisons x two statistics each, and that
    #: is every test run in this burst - nothing was tried and discarded.
    #: `sqrt(2*ln 8)` = 2.039 free t-units, against the programme-wide 5.46.
    #: Stated up front because PIPELINE §4 obligation 2 requires it with any
    #: number, and because a p-value of 0.029 against 1.893 free units is not a
    #: finding, while 7e-10 is.
    print(f"search size: 8 tests (4 comparisons x 2 statistics); free_t = "
          f"{math.sqrt(2 * math.log(8)):.3f}; programme-wide free_t = 5.46\n")
    for k, v in out.items():
        print(f"{v['comparison']}")
        a = v["absorbing"]
        print(f"   absorbing: real {v['absorbing_rate_real']}% vs "
              f"{v['absorbing_rate_other']}%  |  {a['n_discordant']} discordant "
              f"({a['a_only']} real-only, {a['b_only']} other-only)  "
              f"McNemar exact p = {a['p_two_sided']:.3g}")
        t = v["taken"]
        print(f"   taken:     median {v['taken_median_real']}% vs "
              f"{v['taken_median_other']}%  |  real greater in {t['a_greater']}, "
              f"other in {t['b_greater']}, {t['ties']} ties  "
              f"sign test p = {t['p_two_sided']:.3g}  "
              f"(median per-seed diff {t['median_diff']:+d} trades)")
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
