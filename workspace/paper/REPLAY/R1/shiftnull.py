#!/usr/bin/env python3
"""The empirical family-wise null, and why this desk stopped trusting free_t.

WHY THIS EXISTS. Every "does not clear its deflated threshold" verdict in NOTES.md was
measured against free_t = sqrt(2 * ln N), the expected maximum of N INDEPENDENT standard
normals. Two things make that the wrong bar here:

  * the cells of any grid search on one price series OVERLAP heavily, so there are far
    fewer effective independent trials than N - which pushes the true bar DOWN; and
  * the outcome distribution is heavy-tailed (kurtosis 24 on this tape, finding 2), so
    the maximum of a family of t-statistics runs well ABOVE its Gaussian expectation -
    which pushes the true bar UP, and by more.

The second dominates. Measured twice on independently built grids (burst 27):

    grid                        cells    free_t   null median   null 95th   best real
    341 cells, always-LONG      341      3.415    4.352         6.104       3.823 (p 0.695)
    61,272 cells, full search   61,272   4.695    5.164         7.561       7.652 (p 0.055)

free_t sits BELOW the null's MEDIAN in both. A grid with no content at all produces a
best cell above free_t more than half the time, so "clears free_t" means nothing on a
correlated search.

This does NOT flip any conclusion in the journal - everything failed a bar that was too
low, so against the right bar it fails by more. What it changes is the standard going
forward: report the shift-null, and treat free_t as a floor that is explicitly not
sufficient.

HOW THE NULL IS BUILT. Circular-shift the OUTCOME series while holding the features
fixed. That destroys any real relationship between feature and outcome while preserving
(a) the grid's exact correlation structure, (b) each cell's n, and (c) the outcome's own
fat tails and volatility clustering - all three of which a Gaussian formula ignores. The
family-wise p is the fraction of shifts whose best cell beats the real tape's best cell.

A shift is not a permutation: permuting would destroy the serial dependence that makes
the tails fat, which is the very thing being corrected for.

USAGE
  from shiftnull import family_wise
  p, bar, nulls = family_wise(outcomes, masks, n_shifts=200, seed=7)
where `outcomes` is a list of per-observation results and `masks` is a list of
(name, [indices]) cells. Reads nothing; it is pure arithmetic on what you hand it.
"""
import math
import random


def _max_abs_t(series, masks):
    """Largest |t| of any cell's mean against the grand mean."""
    gm = sum(series) / len(series)
    best = 0.0
    for _name, idx in masks:
        v = [series[i] for i in idx]
        if len(v) < 2:
            continue
        mu = sum(v) / len(v)
        var = sum((x - mu) ** 2 for x in v) / (len(v) - 1)
        if var <= 0:
            continue
        t = abs((mu - gm) / math.sqrt(var / len(v)))
        if t > best:
            best = t
    return best


def family_wise(outcomes, masks, n_shifts=200, seed=7):
    """(family_wise_p, empirical_5pct_bar, sorted_null_maxima).

    family_wise_p is the fraction of circular shifts whose best cell beats the real
    tape's best cell. The 5% bar is the 95th percentile of the null maxima - the |t| a
    result must exceed to be worth a second look on THIS grid.
    """
    real = _max_abs_t(outcomes, masks)
    m = len(outcomes)
    rng = random.Random(seed)
    nulls = []
    for _ in range(n_shifts):
        s = rng.randrange(m)
        nulls.append(_max_abs_t(outcomes[s:] + outcomes[:s], masks))
    nulls.sort()
    p = sum(1 for x in nulls if x >= real) / len(nulls)
    bar = nulls[int(0.95 * (len(nulls) - 1))]
    return p, bar, nulls


def report(outcomes, masks, label="", n_shifts=200, seed=7):
    real = _max_abs_t(outcomes, masks)
    p, bar, nulls = family_wise(outcomes, masks, n_shifts, seed)
    ft = math.sqrt(2 * math.log(len(masks))) if len(masks) > 1 else 0.0
    n = len(nulls)
    print(f"{label}  n_obs={len(outcomes)}  cells={len(masks)}")
    print(f"  free_t              = {ft:.3f}   <- a floor, NOT sufficient")
    print(f"  null max|t| median  = {nulls[n // 2]:.3f}")
    print(f"  null max|t| 95th    = {bar:.3f}   <- the bar that matters")
    print(f"  real best cell |t|  = {real:.3f}")
    print(f"  family-wise p       = {p:.3f}")
    if ft < nulls[n // 2]:
        print("  NOTE: free_t is below the null's MEDIAN on this grid - it is not a threshold here.")
    return p, bar
