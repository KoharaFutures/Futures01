"""BT3 ALGO-1 — the claims in `backtest/BT3/ALGOS.md` that must not drift.

These are here rather than only in `backtest/BT3/code/checks.py` so that
`python -m pytest -q tests` catches it if a later change to `futures_agents/`
silently invalidates a number BT3 published. Four of the five are pure library
facts and run in milliseconds; the two that need the reconstructed trade cache
skip cleanly when it is absent, because the cache is a generated artefact and a
fresh clone will not have run `code/stops.py` yet.
"""
from __future__ import annotations

import collections
import json
import os
import random

import pytest

from futures_agents.backtest.montecarlo import bootstrap_paths
from futures_agents.config import AccountConfig, get_contract

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(REPO, "workspace/roundtable/backtest/BT3/code/stops_cache.json")
ARTEFACT = os.path.join(REPO, "workspace/strategy_research/scratch/geo_trades.json")


# --------------------------------------------------------------------------
# Library facts ALGO-1's numbers rest on
# --------------------------------------------------------------------------
def test_opening_risk_budget_is_240_not_375():
    """The buffer binds before the equity cap, so one trade gets $240.

    R3's B-3(c) worked the integer-contract floor at $375 and $500. Neither is
    ever available: `risk_budget` takes
    `min(usable_buffer * base_risk_pct_of_buffer, equity * max_risk_pct_of_equity,
    max_dollar_risk)` and the first term is the smallest at full equity. If this
    ever changes, every deletion count in BT3/ALGOS.md moves with it.
    """
    cfg = AccountConfig()
    buffer_term = cfg.usable_buffer(50_000, 50_000) * cfg.base_risk_pct_of_buffer
    equity_term = 50_000 * cfg.max_risk_pct_of_equity
    assert buffer_term == 240.0
    assert equity_term == 375.0
    assert cfg.max_dollar_risk == 500.0
    assert min(buffer_term, equity_term, cfg.max_dollar_risk) == 240.0


def test_trade_cap_counts_closes_not_opens():
    """`max_trades_per_day` is incremented on close, so it does not cap opens.

    `DayState.record` is the only writer of `trades_taken`, and `open_position`
    deliberately adds zero. ALGO-1 replays the rule both ways because of this;
    the test exists so the "both ways" is not quietly reduced to one.
    """
    from futures_agents.risk.account import AccountState, OpenPosition
    from futures_agents.schema import Direction

    cfg = AccountConfig()
    st = AccountState(config=cfg, equity=cfg.starting_equity)
    for i in range(10):
        st.open_position(OpenPosition(symbol="MGC", direction=Direction.LONG,
                                      contracts=1, entry=2000.0 + i, stop=1990.0))
    assert st.day.trades_taken == 0, "opening positions must not move the counter"
    st.close_position("MGC", -10.0)
    assert st.day.trades_taken == 1, "closing one must move it by exactly one"


def test_correlation_cap_cannot_bind_across_the_four_micro_symbols():
    """MGC/MES/MNQ/MCL are four distinct correlation groups.

    So `max_correlated_positions = 1` degenerates into the per-symbol check that
    precedes it on any population drawn from these four. BT3 REQ-3 asks the
    manager to adjudicate this against the BRIEF's "MES/MNQ are one index
    complex"; until then, the fact is pinned here.
    """
    groups = {s: get_contract(s).correlation_group
              for s in ("MGC", "MES", "MNQ", "MCL")}
    assert len(set(groups.values())) == 4, groups


def test_block_bootstrap_undersamples_the_start_of_the_series():
    """BT3 REQ-2: `mode="block"` is not circular, so the head is under-sampled.

    `bootstrap_paths` slices `r_values[start:start + block]` with no wrap, so
    element ``i`` is reachable from only ``min(i + 1, block)`` starts. This is a
    DEFECT report, not a fixed behaviour: the test asserts the bias is *present*
    so that fixing it fails here loudly and the fix gets noticed rather than
    silently changing every block-mode number.
    """
    n, block = 40, 10
    paths = bootstrap_paths(list(range(n)), 20_000, n, mode="block",
                            block=block, rng=random.Random(7))
    c = collections.Counter(x for p in paths for x in p)
    exp = sum(c.values()) / n
    ramp = [c[i] / exp for i in range(block)]
    tail = [c[i] / exp for i in range(block, n)]

    assert ramp[0] < 0.2, f"index 0 at {ramp[0]:.3f}x - has block mode been fixed?"
    assert all(ramp[i] < ramp[i + 1] for i in range(block - 1)), ramp
    assert min(tail) > 1.05, min(tail)

    # iid over the same series is flat, which is what makes the above a bias in
    # `block` rather than a property of bootstrapping.
    paths = bootstrap_paths(list(range(n)), 20_000, n, mode="iid",
                            rng=random.Random(7))
    c = collections.Counter(x for p in paths for x in p)
    exp = sum(c.values()) / n
    flat = [c[i] / exp for i in range(n)]
    assert 0.97 < min(flat) and max(flat) < 1.03, (min(flat), max(flat))


# --------------------------------------------------------------------------
# Facts about the reconstructed trade cache
# --------------------------------------------------------------------------
@pytest.fixture(scope="module")
def cache():
    if not os.path.exists(CACHE):
        pytest.skip("stops_cache.json not generated; run BT3/code/stops.py")
    return json.load(open(CACHE))


def test_cache_is_the_artefact_plus_exactly_three_fields(cache):
    """The cache must never diverge from `geo_trades.json`.

    If it does, every ALGO-1 number is describing a trade stream nobody
    measured. `geo_trades.json` belongs to an earlier study and is read-only.
    """
    if not os.path.exists(ARTEFACT):
        pytest.skip("geo_trades.json absent")
    stored = json.load(open(ARTEFACT))
    assert len(stored) == len(cache) == 21954
    for a, b in zip(stored, cache):
        assert set(b) - set(a) == {"entry", "stop", "risk_points"}
        assert all(a[k] == b[k] for k in a)
        assert b["risk_points"] > 0


def test_integer_floor_deletes_about_a_third_at_the_opening_budget(cache):
    """The headline mechanical claim: 7,767 of 21,954, and MGC/MNQ 4h wiped out.

    Stateless and hand-checkable: `floor(240 / (risk_points * point_value)) < 1`.
    """
    import math
    budget = 240.0
    per_cell = collections.defaultdict(lambda: [0, 0])
    for r in cache:
        pv = get_contract(r["symbol"]).point_value
        keep = math.floor(budget / (abs(r["entry"] - r["stop"]) * pv)) >= 1
        cell = per_cell[f"{r['symbol']}_{r['tf']}"]
        cell[0] += 1
        cell[1] += 1 if keep else 0

    total = sum(v[0] for v in per_cell.values())
    kept = sum(v[1] for v in per_cell.values())
    assert total == 21954
    assert total - kept == 7767, f"expected 7767 deleted, got {total - kept}"

    # The two cells BT3 reports as untradeable at $50,000.
    for cell, floor_pct in (("MGC_240", 99.0), ("MNQ_240", 94.0)):
        n, k = per_cell[cell]
        assert 100.0 * (n - k) / n > floor_pct, (cell, n, k)
    # ...and the two it reports as largely tradeable.
    for cell, ceiling_pct in (("MES_60", 5.0), ("MCL_60", 10.0)):
        n, k = per_cell[cell]
        assert 100.0 * (n - k) / n < ceiling_pct, (cell, n, k)


def test_integer_floor_selects_on_volatility_within_a_cell(cache):
    """R3's claim, tested the only way it is a claim about volatility.

    Held at fixed symbol and timeframe, EXTREME must survive the floor strictly
    less often than DEAD in the cells BT3 reports as unsaturated. Across the
    whole cell set it is monotone in 5 of 6; this asserts only the endpoints,
    which is the part that does not depend on small buckets.
    """
    import math
    budget = 240.0
    surv = collections.defaultdict(lambda: [0, 0])
    for r in cache:
        pv = get_contract(r["symbol"]).point_value
        keep = math.floor(budget / (abs(r["entry"] - r["stop"]) * pv)) >= 1
        b = surv[(f"{r['symbol']}_{r['tf']}", r["vol"])]
        b[0] += 1
        b[1] += 1 if keep else 0

    def pct(cell, vol):
        n, k = surv[(cell, vol)]
        return 100.0 * k / n if n else None

    for cell in ("MGC_60", "MNQ_60", "MES_60", "MCL_60"):
        dead, extreme = pct(cell, "DEAD"), pct(cell, "EXTREME")
        assert extreme < dead, (cell, dead, extreme)
    # The effect is large where the floor is not saturated.
    assert pct("MGC_60", "DEAD") - pct("MGC_60", "EXTREME") > 40.0
    assert pct("MNQ_60", "DEAD") - pct("MNQ_60", "EXTREME") > 40.0
