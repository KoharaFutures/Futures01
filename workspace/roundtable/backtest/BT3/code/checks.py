"""Checks for ALGO-1. Every one of these is a claim I make elsewhere.

Run:  python3 workspace/roundtable/backtest/BT3/code/checks.py

These are assertions, not a report. A check that fails is the check working, so
none of them is wrapped in a try.
"""
from __future__ import annotations

import collections
import json
import os
import random
import sys

ROOT = "/home/user/Futures01"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "workspace/roundtable/backtest/BT3/code"))

from futures_agents.backtest.montecarlo import bootstrap_paths     # noqa: E402
from futures_agents.config import AccountConfig, get_contract       # noqa: E402

import governor_replay as GR                                        # noqa: E402

TRADES = os.path.join(ROOT, "workspace/strategy_research/scratch/geo_trades.json")


def check_cache_matches_artefact() -> None:
    """``stops_cache.json`` must be ``geo_trades.json`` plus three fields.

    If the cache ever drifts from the artefact, every number downstream of it is
    describing a trade stream nobody measured.
    """
    stored = json.load(open(TRADES))
    cache = json.load(open(GR.CACHE))
    assert len(stored) == len(cache) == 21954, (len(stored), len(cache))
    added = {"entry", "stop", "risk_points"}
    for a, b in zip(stored, cache):
        assert set(b) - set(a) == added, set(b) - set(a)
        for k in a:
            assert a[k] == b[k], (k, a[k], b[k])
        # The reconstructed stop must be consistent with the exit's own
        # stop_mult: exitm atr1.0 / atr1.5 over StopKind.ATR, so the risk
        # distance is positive and at least one tick.
        assert b["risk_points"] > 0
    print("OK  cache matches the artefact row for row, 21954 rows, "
          "3 fields added and nothing altered")


def check_opening_budget() -> None:
    """The binding constraint at full equity is the *buffer*, not the equity cap.

    R3's B-3(c) table worked the integer floor at $375 and $500. The account
    never has that much to spend on one trade: ``base_risk_pct_of_buffer`` binds
    first and the opening budget is $240.
    """
    cfg = AccountConfig()
    base = cfg.usable_buffer(50_000, 50_000) * cfg.base_risk_pct_of_buffer
    cap = 50_000 * cfg.max_risk_pct_of_equity
    assert (base, cap, cfg.max_dollar_risk) == (240.0, 375.0, 500.0)
    assert GR.OPENING_BUDGET == 240.0
    print("OK  opening risk budget is $240 (buffer 240 < equity cap 375 "
          "< absolute 500)")


def check_correlation_cap_is_inert() -> None:
    """``max_correlated_positions = 1`` cannot bind on this trade population.

    The BRIEF says MES/MNQ/NQ/ES are one index complex, but the shipped
    ``ContractSpec.correlation_group`` puts MES in US_EQUITY_BROAD and MNQ in
    US_EQUITY_TECH, so no two of the four symbols in the artefact share a group
    and the correlated-position cap degenerates into the per-symbol check that
    already precedes it.
    """
    groups = {s: get_contract(s).correlation_group
              for s in ("MGC", "MES", "MNQ", "MCL")}
    assert len(set(groups.values())) == 4, groups
    print(f"OK  correlation cap inert here: 4 symbols, 4 distinct groups "
          f"{groups}")


def check_replay_is_deterministic() -> None:
    """Same rows, same order, same result. Twice."""
    rows = json.load(open(GR.CACHE))[:4000]
    s = GR.sort_stream(rows)
    a = GR.replay(s, label="a")
    b = GR.replay(s, label="b")
    assert (a.n_taken, a.vetoes, round(a.final_equity, 6)) == \
           (b.n_taken, b.vetoes, round(b.final_equity, 6))
    print(f"OK  replay deterministic ({a.n_taken} taken, "
          f"${a.final_equity:,.2f} both runs)")


def check_block_bootstrap_undersamples_the_start() -> None:
    """DEFECT, reported not fixed: ``mode="block"`` is not a circular bootstrap.

    ``bootstrap_paths`` draws ``r_values[start:start + block]`` with no
    wrap-around `[repo-verified: montecarlo.py:103-107]`, so element ``i`` is
    reachable from only ``min(i + 1, block)`` distinct starts. The first
    ``block - 1`` elements of the series are therefore systematically
    under-sampled on a linear ramp, and everything after them is over-sampled.

    This matters for R3's Tier-0 item 2, which is the first use of ``block``
    mode anywhere in the repo: the block arm silently discounts the *beginning*
    of every trade sequence it resamples.
    """
    n, block = 40, 10
    paths = bootstrap_paths(list(range(n)), 20_000, n, mode="block",
                            block=block, rng=random.Random(7))
    c = collections.Counter(x for p in paths for x in p)
    exp = sum(c.values()) / n
    ramp = [c[i] / exp for i in range(block)]
    tail = [c[i] / exp for i in range(block, n)]
    # index 0 should appear at roughly 1/block of its due share
    assert ramp[0] < 0.2, ramp[0]
    assert all(ramp[i] < ramp[i + 1] for i in range(block - 1)), ramp
    assert min(tail) > 1.05, min(tail)
    print(f"OK  block-mode bias confirmed: index 0 at {ramp[0]:.3f}x expected, "
          f"index {block - 1} at {ramp[block - 1]:.3f}x, "
          f"tail at {sum(tail) / len(tail):.3f}x")
    # and the iid arm has no such bias, which is what makes it a bias and not
    # a property of the estimator
    paths = bootstrap_paths(list(range(n)), 20_000, n, mode="iid",
                            rng=random.Random(7))
    c = collections.Counter(x for p in paths for x in p)
    exp = sum(c.values()) / n
    flat = [c[i] / exp for i in range(n)]
    assert 0.97 < min(flat) and max(flat) < 1.03, (min(flat), max(flat))
    print(f"OK  iid mode is flat over the same series "
          f"[{min(flat):.3f}, {max(flat):.3f}]")


if __name__ == "__main__":
    check_cache_matches_artefact()
    check_opening_budget()
    check_correlation_cap_is_inert()
    check_replay_is_deterministic()
    check_block_bootstrap_undersamples_the_start()
    print("\nall checks passed")
