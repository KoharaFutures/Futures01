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


def z_from_p(p: float) -> float:
    """The two-sided normal deviate with the same tail mass as ``p``.

    **This is the operation my first report omitted, and the omission was the
    error.** The deflation rule is stated in t-units: searching ``n`` variants
    buys about ``sqrt(2*ln n)`` free ones. So a result is judged by comparing
    **its own statistic** to that threshold. Comparing a *p-value* to a t-value
    is not that operation and is not a comparison of anything - 0.029 is not
    "less than 2.039" in any meaningful sense. Every table in ALGOS.md now
    carries this z beside the p.

    Bisection on ``erfc`` because the deterministic core is dependency-free.
    """
    if p <= 0.0:
        return float("inf")
    if p >= 1.0:
        return 0.0
    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if math.erfc(mid / math.sqrt(2.0)) > p:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def pmf(k: int, n: int, p: float = 0.5) -> float:
    return math.comb(n, k) * p ** k * (1.0 - p) ** (n - k)


def mid_p(k: int, n: int) -> float:
    """Exact two-sided p less half the observed point mass.

    The standard correction for the conservatism a discrete test carries. It is
    reported because discreteness was the first thing I had to rule out as an
    excuse for my own error - and it pushes the *other* way: mid-p is smaller
    than the exact p, so the z is larger, so discreteness cannot rescue a
    comparison that fails on the exact p.
    """
    if n == 0:
        return 1.0
    return max(0.0, binom_two_sided(k, n) - 0.5 * pmf(k, n))


def binom_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Exact two-sided binomial p-value by the method of small likelihoods."""
    if n == 0:
        return 1.0

    def _pt(i: int) -> float:
        return math.comb(n, i) * p ** i * (1.0 - p) ** (n - i)

    obs = _pt(k)
    # Sum every outcome no more likely than the observed one. Exact, and it is
    # the definition that does not assume symmetry.
    return min(1.0, sum(_pt(i) for i in range(n + 1) if _pt(i) <= obs * (1 + 1e-12)))


def mcnemar(a: list, b: list) -> dict:
    """Exact McNemar over paired binary outcomes ``a`` and ``b``."""
    assert len(a) == len(b)
    b01 = sum(1 for x, y in zip(a, b) if (not x) and y)
    b10 = sum(1 for x, y in zip(a, b) if x and (not y))
    n_disc = b01 + b10
    return {"test": "McNemar exact (paired binomial on discordant seeds)",
            "n_pairs": len(a), "a_only": b10, "b_only": b01,
            "n_discordant": n_disc,
            "p_two_sided": binom_two_sided(b10, n_disc) if n_disc else 1.0,
            "mid_p": mid_p(b10, n_disc) if n_disc else 1.0,
            "z": z_from_p(binom_two_sided(b10, n_disc)) if n_disc else 0.0,
            "z_mid_p": z_from_p(mid_p(b10, n_disc)) if n_disc else 0.0}


def sign_test(a: list, b: list) -> dict:
    """Exact two-sided sign test on the per-seed difference ``a - b``."""
    pos = sum(1 for x, y in zip(a, b) if x > y)
    neg = sum(1 for x, y in zip(a, b) if x < y)
    n = pos + neg
    return {"test": "exact sign test (two-sided binomial, ties dropped)",
            "n_pairs": len(a), "a_greater": pos, "b_greater": neg,
            "ties": len(a) - n,
            "median_diff": (sorted(x - y for x, y in zip(a, b))[len(a) // 2]),
            "p_two_sided": binom_two_sided(pos, n) if n else 1.0,
            "mid_p": mid_p(pos, n) if n else 1.0,
            "z": z_from_p(binom_two_sided(pos, n)) if n else 0.0,
            "z_mid_p": z_from_p(mid_p(pos, n)) if n else 0.0}


def main() -> None:
    rep = json.load(open(REPORT))
    pr = rep["primary"]
    real = pr["vol_aware_barrier"]
    out = {}

    for name, other in (
            ("vol_pinned_control", "neutral vs volatility pinned"),
            ("honest_arm_live_eligible_False",
             "neutral vs honest (is_live_eligible=False)"),
            ("barrier_off_leak", "neutral vs barrier removed"),
            ("placebo_global",
             "neutral vs placebo GLOBAL (ordering control, not signal-layer)"),
            ("placebo_by_symbol_tf_reason",
             "neutral vs placebo stratified (symbol, tf, reason)"),
            ("placebo_by_strategy_reason",
             "neutral vs placebo stratified (strategy, reason)")):
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

    #: **Search size is the number of tests, and it is now 12** - six arm
    #: comparisons x two statistics - so `free_t = sqrt(2*ln 12) = 2.229`. It
    #: went up because I added two stratified placebos rather than defend the
    #: one I had; raising my own threshold was the cost of doing that honestly,
    #: and it does not rescue the comparison that failed, which is the point.
    n_tests = 2 * len(out)
    free_t = math.sqrt(2.0 * math.log(n_tests))
    print(f"search size: {n_tests} tests ({len(out)} comparisons x 2 "
          f"statistics); free_t = sqrt(2*ln {n_tests}) = {free_t:.3f}; "
          f"programme-wide free_t = 5.46")
    print("CLEARS means |z| > free_t. z is the two-sided normal deviate with "
          "the same tail mass as the exact p.\n")
    for k, v in out.items():
        print(f"{v['comparison']}")
        for lab, t, extra in (
                ("deaths", v["absorbing"],
                 f"{v['absorbing_rate_real']}% vs {v['absorbing_rate_other']}%"),
                ("taken ", v["taken"],
                 f"median {v['taken_median_real']}% vs "
                 f"{v['taken_median_other']}%, "
                 f"per-seed diff {v['taken']['median_diff']:+d}")):
            verdict = "CLEARS  " if abs(t["z"]) > free_t else "does not"
            print(f"   {lab}  {extra:<44s} p={t['p_two_sided']:.4g} "
                  f"|z|={t['z']:.3f} (mid-p |z|={t['z_mid_p']:.3f})  "
                  f"{verdict} free_t={free_t:.3f}")
        v["free_t"] = free_t
        v["n_tests"] = n_tests
        v["absorbing"]["clears"] = abs(v["absorbing"]["z"]) > free_t
        v["taken"]["clears"] = abs(v["taken"]["z"]) > free_t
    json.dump(out, open(dest, "w"), indent=1)
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()
