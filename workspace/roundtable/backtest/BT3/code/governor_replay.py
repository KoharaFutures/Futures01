"""ALGO-1 - replay the live account governors over a stored trade stream.

What this is
------------
R3 established that nothing under ``futures_agents/backtest/`` imports anything
from ``futures_agents/risk/``, so the nineteen operating parameters that would
have governed a $50,000 account were never in the 2,975,629-evaluation
experiment `[repo-verified: R3_path_operation.md B-1, Q2]`. This module closes
that gap in the only direction available without a new experiment: it drives the
**real** ``RiskManager`` and ``AccountState`` over a **stored** trade stream and
records what they would have refused.

The load-bearing design decision is that **nothing here reimplements a
governor.** Every limit, ladder, multiplier and veto comes from
``futures_agents/risk/manager.py`` and ``futures_agents/risk/account.py`` by
import and by call. Reimplementing them would reintroduce exactly the
divergence the replay exists to measure. What this file supplies is the
adapter: a ``TradeProposal`` per stored trade, and an event loop that keeps the
account's clock monotonic.

Scope: which of ``RiskManager.assess``'s nine stages are in
------------------------------------------------------------
``assess`` runs nine stages `[repo-verified: risk/manager.py:222-376]`. Five of
them are account governors and four are setup-quality gates that the stored
artefact cannot inform. Rather than call the governors piecemeal - which would
mean copying their order and their short-circuiting - this replay calls
``assess`` **whole** and neutralises the four out-of-scope stages *by
construction*, through the proposal's own fields. Each neutralisation is one
field and is listed here so it can be argued with:

  stage 1  account hard stops .......... IN   (failure, buffer, daily loss limit,
                                              consecutive losses, trade cap,
                                              profit giveback)
  stage 2  structural sanity ........... IN   (the ``min_stop_ticks`` noise floor
                                              is real and computable from the
                                              reconstructed stop)
  stage 3  exposure .................... IN   (per-symbol, concurrent,
                                              correlated)
  stage 4  news ........................ OUT  ``news_risk=NewsRisk.NONE``.
                                              The artefact has no event calendar
                                              and A-6 shows the backtester could
                                              not have applied one anyway.
  stage 5  volatility band ............. OUT  ``atr=None`` disables the check
                                              `[repo-verified: manager.py:271]`.
                                              This is an *entry* filter on
                                              ATR/median, not an account rule.
  stage 6  setup quality ............... OUT  ``confidence=1.0`` and a
                                              ``HistoricalPerformance`` that
                                              clears every floor. See
                                              ``LIVE_ELIGIBLE`` below - this one
                                              is not cosmetic.
  stage 7  sizing ...................... IN   (``risk_budget`` ->
                                              ``min_dollar_risk`` ->
                                              ``contracts_for``, i.e. the
                                              integer floor)
  stage 8  cost against the edge ....... OUT  neutralised by a deliberately far
                                              synthetic target. It needs the
                                              trade's real first target, which
                                              the artefact does not carry, and
                                              it is a setup gate rather than an
                                              account rule.
  stage 9  effect on the buffer ........ IN   (single-stop buffer consumption and
                                              the remaining daily loss budget)

Stage 6 deserves its own sentence, and the sentence I first wrote was wrong. I
assumed leaving it in would empty the replay, because ``min_expectancy_r = 0.08``
and ``min_backtest_trades = 40`` `[repo-verified: config.py:377-379]` run against
a population the BRIEF settles as having nothing live-eligible. Measured, it
does not empty it: **9 of the 176 strategies clear both floors on their own
in-sample record** `[measured: measure_stage6() -> 9/176]`. So stage 6 is out of
scope because it is a *selection* rule - and selecting last period's best is the
one operation this repo has already measured as harmful - not because it is
vacuous. That is a weaker justification than the one I started with, and it is
the true one.

Two populations, never averaged together
----------------------------------------
Pooling inflation is a known defect at three levels in this repo, so this module
refuses to produce a single number over the file:

  ``POOLED``       all trades in one account. 176 strategies across 4 symbols
                   live simultaneously. This is **not a portfolio anyone would
                   run** - the arms are nested variants of two base conditions -
                   so it measures the *shape* of the governors' bite, not a
                   tradeable result.
  ``PER_STRATEGY`` 176 independent replays, one fresh $50,000 account each,
                   keyed by ``(symbol, tf, arm, exitm)``. The distribution
                   across the 176 is the non-pooled reading. The 176 are still
                   correlated variants, so no z-statistic is attached to it.

Usage
-----
    python3 workspace/roundtable/backtest/BT3/code/governor_replay.py
"""
from __future__ import annotations

import collections
import heapq
import json
import os
import random
import statistics as stats
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

ROOT = "/home/user/Futures01"
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from futures_agents.config import AccountConfig, get_contract      # noqa: E402
from futures_agents.risk.account import AccountState, OpenPosition  # noqa: E402
from futures_agents.risk.manager import RiskManager, TradeProposal  # noqa: E402
from futures_agents.schema import (Direction, HistoricalPerformance,  # noqa: E402
                                   NewsRisk)
from futures_agents.timeutil import trading_day                     # noqa: E402

CACHE = os.path.join(ROOT, "workspace/roundtable/backtest/BT3/code/stops_cache.json")

#: ``risk_budget`` at full equity with no penalty of any kind:
#: ``min(usable_buffer * 0.06, equity * 0.0075, max_dollar_risk)``
#: = ``min(4000 * 0.06, 50000 * 0.0075, 500)`` = **$240**, and note that it is
#: ``base_risk_pct_of_buffer`` that binds, not the 0.75%-of-equity ceiling. R3's
#: B-3(c) worked the floor at $375 and $500; the account never gets that much.
_CFG0 = AccountConfig()
OPENING_BUDGET = min(
    _CFG0.usable_buffer(_CFG0.starting_equity, _CFG0.starting_equity)
    * _CFG0.base_risk_pct_of_buffer,
    _CFG0.starting_equity * _CFG0.max_risk_pct_of_equity,
    _CFG0.max_dollar_risk)

#: How many within-timestamp permutations the primary result averages over.
#: Five is not enough: the distribution is bimodal, because whether a run
#: crosses the absorbing boundary is close to a coin flip at these parameters.
N_ORDER_SEEDS = 200

#: The ``HistoricalPerformance`` attached to every proposal. ``trades`` and
#: ``expectancy_r`` exist only to get past stage 6; they are not claims about
#: this population.
#:
#: ``is_live_eligible`` is a *property*, not a field, and it is False unless six
#: separate conditions hold `[repo-verified: schema.py:244-254]`. When it is
#: False, ``risk_budget`` multiplies the budget by 0.5
#: `[repo-verified: manager.py:181-183]`. Since the BRIEF settles that nothing
#: in this repository is live-eligible, the honest arm is the one where it is
#: False - so the replay runs both and reports both.
def _hist(live_eligible: bool) -> HistoricalPerformance:
    h = HistoricalPerformance(trades=999, expectancy_r=1.0)
    if live_eligible:
        h.sample_is_sufficient = True
        h.out_of_sample_trades = 999
        h.out_of_sample_expectancy_r = 1.0
        h.robustness_score = 1.0
    return h


# --------------------------------------------------------------------------
# Ordering
# --------------------------------------------------------------------------
#: 21,954 trades share only 3,325 distinct timestamps and one timestamp carries
#: 74 of them `[measured]`. With ``max_concurrent_positions = 2`` and one
#: position per symbol, the within-timestamp order *decides which trades
#: survive*, so it cannot be left to the file's own order.
#:
#: **The seeded order is primary and the lexicographic one is only an anchor.**
#: That is R3's ruling (`msgs/03_R3_BT3_re-verify-ALGO-1.md` item 3) and it is
#: right: any *fixed* key on a field correlated with sizeability biases the
#: result. `sorted(set(symbol)) == ['MCL','MES','MGC','MNQ']` hands the first
#: slot to MCL and MES, which are exactly the two symbols that survive the
#: integer floor (MCL 60m loses 5.1%, MES 60m 2.2%, against MGC 240m's 99.4%),
#: so a `symbol`-second tiebreak front-loads the account with the trades it can
#: afford. `str(tf)` sorting '240' before '60' has the same shape of problem.
#: The lexicographic run is retained, labelled, as a reproducibility anchor
#: only - never as the headline.
ORDER_KEY_FIELDS = ("ts", "symbol", "tf", "base", "arm", "exitm", "dir")


def order_key(row: dict) -> tuple:
    #: ``ts`` is parsed, not stringified. Offsets vary (`-05:00` and `-04:00`
    #: both occur), and lexicographic string order over local-time ISO stamps
    #: with a variable offset is not in general absolute-time order. R3 checked
    #: that no pair actually inverts in this data, so the string version was
    #: correct by accident; parsing makes it correct by construction.
    return (parse_ts(row["ts"]),) + tuple(str(row[f])
                                          for f in ORDER_KEY_FIELDS[1:])


def sort_stream(rows: Sequence[dict], *, seed: Optional[int] = None) -> List[dict]:
    """Absolute-time order, with a seeded or anchored within-timestamp order."""
    if seed is None:
        return sorted(rows, key=order_key)
    rng = random.Random(seed)
    # Shuffle first, then a stable sort on the parsed instant alone: the shuffle
    # survives inside each timestamp group, the across-timestamp order is fixed.
    shuffled = list(rows)
    rng.shuffle(shuffled)
    return sorted(shuffled, key=lambda r: parse_ts(r["ts"]))


def parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s)


# --------------------------------------------------------------------------
# One replay
# --------------------------------------------------------------------------
@dataclass
class ReplayResult:
    label: str
    n_candidates: int = 0
    n_taken: int = 0
    vetoes: Dict[str, int] = field(default_factory=dict)
    #: R of every trade the governors permitted, in the order taken.
    taken_r: List[float] = field(default_factory=list)
    #: R of every trade they refused.
    refused_r: List[float] = field(default_factory=list)
    contracts: List[int] = field(default_factory=list)
    final_equity: float = 0.0
    peak_equity: float = 0.0
    min_equity: float = 0.0
    halted_days: int = 0
    days_seen: int = 0
    #: ``(trading_day, count)`` of trades taken, for the trade-cap question.
    per_day_taken: Dict[str, int] = field(default_factory=dict)
    failed: bool = False
    #: Of the trades the integer floor deleted, how many would *also* have been
    #: deleted at the opening budget. The complement is the de-risk ladder and
    #: the day-penalties shrinking the budget, not the floor's own bite, and
    #: without this split the floor count is unattributable.
    floor_deleted_at_opening_budget: int = 0
    floor_deleted_only_when_shrunk: int = 0
    #: Every permitted risk budget ``risk_budget`` returned, for diagnosis.
    budgets: List[float] = field(default_factory=list)

    # ---- the absorbing state (R3's item 2) ------------------------------
    #: ``risk_budget(None)`` - the account-level budget with no proposal
    #: multiplier - falls below ``min_dollar_risk`` at a drawdown from peak of
    #: about $2,800, and stage 7 then vetoes every proposal *before*
    #: ``contracts_for`` is reached `[repo-verified: risk/manager.py:325-329]`.
    #: Equity can then only move via already-open positions; once they close it
    #: is frozen, ``peak_equity`` never falls, so the budget never recovers.
    #: The account is dead and ``has_failed`` is still False.
    death_index: Optional[int] = None
    death_ts: Optional[str] = None
    death_drawdown: Optional[float] = None
    absorbing: bool = False
    last_taken_index: int = -1
    taken_before_death: int = 0
    max_drawdown: float = 0.0

    def summary(self) -> str:
        return (f"{self.label}: {self.n_taken}/{self.n_candidates} taken "
                f"({100.0 * self.n_taken / max(1, self.n_candidates):.1f}%), "
                f"final ${self.final_equity:,.0f}, "
                f"min ${self.min_equity:,.0f}, failed={self.failed}")


#: Each veto string from ``risk/manager.py`` is mapped to a short stable label,
#: because the raw strings interpolate dollar amounts and would never group.
_VETO_LABELS = (
    ("account has reached its failure threshold", "1_account_failed"),
    ("usable risk buffer exhausted", "1_buffer_exhausted"),
    ("daily loss limit reached", "1_daily_loss_limit"),
    ("consecutive losses - observation only", "1_consecutive_losses"),
    ("daily trade cap reached", "1_trade_cap"),
    ("protecting the day", "1_profit_giveback"),
    ("noise floor", "2_stop_inside_noise_floor"),
    ("stop is at or beyond the entry", "2_undefined_risk"),
    ("already holding a position in", "3_symbol_already_held"),
    ("at the concurrent-position limit", "3_concurrent_limit"),
    ("a second position there is one larger position", "3_correlated_limit"),
    ("minimum - the account cannot take this trade", "7_below_min_dollar_risk"),
    ("the stop is too wide for this account", "7_integer_floor_zero_contracts"),
    ("of the remaining risk buffer", "9_buffer_consumed_by_one_stop"),
    ("left in today's loss budget", "9_daily_loss_budget"),
    ("not worth the risk", "8_cost_vs_reward"),
)


def veto_label(vetoes: Sequence[str]) -> str:
    """The short label of the *first* veto, which is the one that fired."""
    if not vetoes:
        return "none"
    v = vetoes[0]
    for needle, label in _VETO_LABELS:
        if needle in v:
            return label
    return "UNMAPPED:" + v[:60]


def replay(rows: Sequence[dict], *, label: str, live_eligible: bool = True,
           cap_on_open: bool = False, barrier: bool = True,
           vol_aware: bool = True,
           r_override: Optional[Sequence[float]] = None) -> ReplayResult:
    """Drive the real ``RiskManager`` over ``rows`` in absolute-time order.

    ``rows`` must already be sorted. ``r_override`` replaces each trade's R with
    a supplied value, positionally - that is the placebo hook.

    ``barrier`` closes an intra-timestamp look-ahead R3 found and I had missed.
    2,900 of 21,954 rows have ``mins == 0.0`` - same-bar exits, mean R **-0.79**
    - and one timestamp carries 74 rows. Flushing exits at ``<= ts`` therefore
    let the governors assess row #40 at instant *T* while the account already
    held the realised outcomes of rows #1-39 that entered *and exited* at that
    same *T*. A live account handed 74 simultaneous signals knows none of their
    outcomes, and because the zero-duration set has a strongly negative mean the
    leak was directionally biased: it drove the account into de-risk and
    OBSERVATION_ONLY within the instant. With ``barrier=True`` the whole
    timestamp group is assessed against the state as of *T-*, all approved opens
    are applied, and only then are exits at ``<= T`` realised.

    Opens *within* the group are still visible to later rows in the group, which
    is correct and necessary: the concurrency and per-symbol caps must count
    simultaneous positions. Only *outcomes* are hidden.

    ``vol_aware`` passes the artefact's own ``vol`` label into stage 7, where
    ``proposal.volatility in ("HIGH","EXTREME")`` applies x0.70
    `[repo-verified: risk/manager.py:177-179]`. That multiplier is inside stage
    7, which is IN scope, so pinning it to "NORMAL" suppressed a governor the
    artefact can inform - 27.9% of the stream carries HIGH or EXTREME. False
    keeps it pinned, as the held-constant control arm.

    ``cap_on_open`` exists because ``DayState.trades_taken`` is incremented by
    ``DayState.record``, which only runs on *close*
    `[repo-verified: risk/account.py:67-79, 201, 219]`, so the shipped
    ``max_trades_per_day`` counts completed trades, not started ones. False
    replays the code as shipped. True adds an explicit pre-veto on opens - a
    declared DIVERGENCE from ``risk/manager.py``, not a silent one, and the only
    place in this module where a governor is applied outside ``assess``.
    """
    cfg = AccountConfig()
    st = AccountState(config=cfg, equity=cfg.starting_equity)
    st.day = None                      # forced to roll on the first event's date
    rm = RiskManager(cfg, st)
    hist = _hist(live_eligible)

    out = ReplayResult(label=label, n_candidates=len(rows))
    out.peak_equity = out.min_equity = cfg.starting_equity
    vetoes: Dict[str, int] = collections.Counter()

    # (exit_ts, seq, symbol, pnl)
    pending: List[Tuple[datetime, int, str, float]] = []
    seq = 0
    days: set = set()
    extra_taken_today = collections.Counter()

    def flush(until: datetime, *, strict: bool = False) -> None:
        """Realise exits up to ``until``, in time order.

        ``strict`` excludes exits at exactly ``until``, which is what makes the
        barrier a barrier. ``out.peak_equity`` / ``out.min_equity`` are tracked
        here rather than read off ``st.equity_curve``, because that list is
        seeded in ``__post_init__`` with a wall-clock stamp
        `[repo-verified: risk/account.py:115-116]` and is therefore not
        monotonic in time for a replay - see ALGOS.md.
        """
        while pending and (pending[0][0] < until if strict
                           else pending[0][0] <= until):
            ts_, _, sym_, pnl_ = heapq.heappop(pending)
            st.close_position(sym_, pnl_, when=ts_)
            out.peak_equity = max(out.peak_equity, st.equity)
            out.min_equity = min(out.min_equity, st.equity)
            out.max_drawdown = max(out.max_drawdown, st.peak_equity - st.equity)

    n = len(rows)
    k = 0
    while k < n:
        ts = parse_ts(rows[k]["ts"])
        group_end = k
        while group_end < n and parse_ts(rows[group_end]["ts"]) == ts:
            group_end += 1

        # Under the barrier, exits at exactly ``ts`` are not yet knowable.
        flush(ts, strict=barrier)

        day = str(trading_day(ts))
        days.add(day)

        for j in range(k, group_end):
            row = rows[j]
            sym = row["symbol"]
            spec = get_contract(sym)
            sign = 1 if row["dir"] == "LONG" else -1
            entry, stop = row["entry"], row["stop"]
            risk_pts = abs(entry - stop)
            r = float(row["r"]) if r_override is None else float(r_override[j])

            # The synthetic target sits 20R away purely to neutralise stages 6
            # and 8; the artefact does not carry the real target. It touches
            # nothing else - ``targets`` is read only by ``reward_risk`` and by
            # stage 8.
            prop = TradeProposal(
                symbol=sym,
                direction=Direction.LONG if sign > 0 else Direction.SHORT,
                entry=entry, stop=stop,
                targets=[entry + sign * risk_pts * 20.0],
                confidence=1.0, strategy_id=f"{row['symbol']}_{row['tf']}_"
                                            f"{row['arm']}_{row['exitm']}",
                timeframe=int(row["tf"]), regime=row["regime"],
                volatility=(row["vol"] if vol_aware else "NORMAL"),
                # ``session`` and ``regime`` are carried for provenance only:
                # nothing in ``assess`` reads either
                # `[repo-verified: risk/manager.py:208-376]`. Which is as well,
                # because the artefact's ``session`` and ``ts`` are on different
                # clocks - row 0 is 20:00 ET labelled POST_CLOSE, and 20:00 ET
                # is ASIA. Do not cut any ALGO-1 result by ``session``.
                session=row["session"], news_risk=NewsRisk.NONE,
                historical=hist, atr=None, atr_median=None,
                analyst_agreement=0.0)

            if cap_on_open and extra_taken_today[day] >= cfg.max_trades_per_day:
                vetoes["1_trade_cap_on_open(DIVERGENT)"] += 1
                out.refused_r.append(r)
                continue

            ra = rm.assess(prop, when=ts)

            # The account-level budget, with no proposal multiplier at all. This
            # is the quantity that defines the absorbing state, and it has to be
            # read separately because the per-proposal budget also carries the
            # volatility and live-eligibility factors.
            acct_budget, _, _ = rm.risk_budget(None)
            if acct_budget < cfg.min_dollar_risk and out.death_index is None:
                out.death_index = j
                out.death_ts = row["ts"]
                out.death_drawdown = st.peak_equity - st.equity
                out.taken_before_death = out.n_taken

            if not ra.approved:
                lab = veto_label(ra.vetoes)
                vetoes[lab] += 1
                out.refused_r.append(r)
                if lab == "7_integer_floor_zero_contracts":
                    if risk_pts * spec.point_value > OPENING_BUDGET:
                        out.floor_deleted_at_opening_budget += 1
                    else:
                        out.floor_deleted_only_when_shrunk += 1
                continue

            contracts = ra.contracts
            dollar_risk = contracts * risk_pts * spec.point_value
            out.budgets.append(dollar_risk)
            # ``net_dollars = net_r * risk_dollars`` is exactly the engine's own
            # conversion `[repo-verified: engine.py:507]`, and cost-in-R is
            # size-invariant because commission and slippage are both linear in
            # ``contracts`` `[repo-verified: costs.py:104-110, 119-122]`, so no
            # cost is charged twice and none is dropped.
            pnl = r * dollar_risk

            # ``close_position`` resolves by symbol
            # `[repo-verified: risk/account.py:203-208]`, which is unambiguous
            # only because stage 3 forbids a second same-symbol position. If
            # stage 3 is ever taken out of scope this becomes wrong.
            st.open_position(OpenPosition(
                symbol=sym, direction=prop.direction, contracts=contracts,
                entry=entry, stop=stop, targets=list(prop.targets),
                opened_et=row["ts"], strategy_id=prop.strategy_id,
                dollar_risk=dollar_risk))
            out.n_taken += 1
            out.last_taken_index = j
            out.contracts.append(contracts)
            out.taken_r.append(r)
            out.per_day_taken[day] = out.per_day_taken.get(day, 0) + 1
            extra_taken_today[day] += 1

            seq += 1
            heapq.heappush(pending,
                           (ts + timedelta(minutes=float(row["mins"])),
                            seq, sym, pnl))

        # Now the barrier lifts: exits at exactly ``ts`` are realised.
        if barrier:
            flush(ts)
        k = group_end

    if pending:
        flush(max(p[0] for p in pending))

    out.vetoes = dict(vetoes)
    out.final_equity = st.equity
    out.days_seen = len(days)
    out.failed = st.has_failed
    out.max_drawdown = max(out.max_drawdown, st.peak_equity - st.equity)
    if out.death_index is None:
        out.taken_before_death = out.n_taken
    else:
        # Absorbing means the account opened nothing after the budget first fell
        # below ``min_dollar_risk``. If it did open something later, the state
        # was transient - the budget recovered - and this run did not die.
        out.absorbing = out.last_taken_index < out.death_index
    return out


# --------------------------------------------------------------------------
# Static reading of the integer floor - no account state at all
# --------------------------------------------------------------------------
def row_budget(row: dict, budget: float, *, vol_aware: bool) -> float:
    """The budget this row actually gets, after stage 7's x0.70.

    Stage 7 multiplies by 0.70 when ``proposal.volatility in ("HIGH","EXTREME")``
    `[repo-verified: risk/manager.py:177-179]`. That multiplier is inside stage
    7, which ALGO-1 declares IN scope, and the artefact carries the label - so
    suppressing it understates the floor. 27.9% of the stream is HIGH or EXTREME.
    """
    if vol_aware and row["vol"] in ("HIGH", "EXTREME"):
        return budget * 0.70
    return budget


def static_integer_floor(rows: Sequence[dict], *,
                         vol_aware: bool = True) -> dict:
    """How many trades ``contracts_for`` deletes at the *opening* budget.

    This is deliberately stateless. The full replay's floor count is confounded
    with every path-dependent penalty that came before it, whereas this number
    is a property of the stop-distance distribution alone and can be checked by
    hand: ``floor(budget / (risk_points * point_value)) < 1``.
    """
    import math
    cfg = AccountConfig()
    budget = min(cfg.usable_buffer(cfg.starting_equity, cfg.starting_equity)
                 * cfg.base_risk_pct_of_buffer,
                 cfg.starting_equity * cfg.max_risk_pct_of_equity,
                 cfg.max_dollar_risk)
    per_cell: Dict[str, List[int]] = collections.defaultdict(list)
    kept = 0
    for r in rows:
        pv = get_contract(r["symbol"]).point_value
        b = row_budget(r, budget, vol_aware=vol_aware)
        n = int(math.floor(b / (abs(r["entry"] - r["stop"]) * pv)))
        kept += 1 if n >= 1 else 0
        per_cell[f"{r['symbol']}_{r['tf']}"].append(n)
    return {
        "vol_aware": vol_aware,
        "budget": budget,
        "n": len(rows),
        "kept": kept,
        "deleted": len(rows) - kept,
        "deleted_pct": 100.0 * (len(rows) - kept) / max(1, len(rows)),
        "by_symbol_tf": {k: {
            "n": len(v),
            "kept": sum(1 for x in v if x >= 1),
            "deleted_pct": 100.0 * sum(1 for x in v if x < 1) / len(v),
            "median_contracts": stats.median(v),
        } for k, v in sorted(per_cell.items())},
    }


def floor_by_volatility(rows: Sequence[dict], *,
                        vol_aware: bool = True) -> dict:
    """Does the integer floor select on *volatility*, or only on symbol and bar?

    R3's claim is that ``contracts_for``'s floor is "an unintended
    volatility-regime entry filter" because it selects on stop distance and
    ``StopKind.ATR`` makes stop distance proportional to ATR
    `[repo-verified: base.py:284-288]`. That claim is only about volatility if
    survival still varies with the volatility regime *once symbol and timeframe
    are held fixed* - otherwise the floor is selecting on ``point_value`` and on
    bar size, which look like volatility only because they are confounded with
    it. So this conditions on ``(symbol, tf)`` and reports survival per
    ``vol`` bucket, which is the trade's own recorded regime label.

    With ``vol_aware=True`` the same ``vol`` label also drives stage 7's x0.70,
    which steepens exactly the HIGH and EXTREME columns and leaves DEAD and LOW
    untouched. That is not circular - it is the point. The budget penalty and the
    stop width are two independent channels through which volatility reaches the
    floor, and the two arms separate them: ``False`` is the stop-width channel
    alone, ``True`` is both, as the live path would apply them.
    """
    import math
    out: Dict[str, Dict[str, dict]] = {}
    buckets = ("DEAD", "LOW", "NORMAL", "HIGH", "EXTREME")
    for r in rows:
        cell = f"{r['symbol']}_{r['tf']}"
        pv = get_contract(r["symbol"]).point_value
        b = row_budget(r, OPENING_BUDGET, vol_aware=vol_aware)
        keep = int(math.floor(b / (abs(r["entry"] - r["stop"]) * pv))) >= 1
        d = out.setdefault(cell, {})
        b = d.setdefault(r["vol"], {"n": 0, "kept": 0})
        b["n"] += 1
        b["kept"] += 1 if keep else 0
    for cell, d in out.items():
        for b in d.values():
            b["kept_pct"] = round(100.0 * b["kept"] / b["n"], 2)
    return {c: {b: out[c][b] for b in buckets if b in out[c]}
            for c in sorted(out)}


def absorbing_boundary(step: float = 1.0) -> dict:
    """Find the drawdown at which the account can never open another position.

    R3 solved this and I am reproducing it rather than citing it, because it is
    now the headline of ALGO-1 and a headline should be measured in the code that
    produces it. The mechanism, entirely inside the shipped risk layer:

      ``budget = min(usable_buffer * base_risk_pct_of_buffer,
                     equity * max_risk_pct_of_equity, max_dollar_risk)
                 * derisk_multiplier``

    and stage 7 vetoes at ``budget < min_dollar_risk`` **before**
    ``contracts_for`` is ever called `[repo-verified: risk/manager.py:325-329]`.
    Past that drawdown, equity can only move through already-open positions;
    once they close it is frozen, ``peak_equity`` never falls, so the budget
    never recovers. **And ``has_failed`` is False the whole time**, because the
    account is nowhere near the $5,000 failure threshold.

    So the shipped configuration has a dead-but-not-failed absorbing state, and
    the ``max_total_drawdown`` failure threshold is unreachable from above it.
    """
    cfg = AccountConfig()
    peak = cfg.starting_equity
    prev = None
    dd = 0.0
    while dd <= cfg.max_total_drawdown:
        eq = peak - dd
        base = min(cfg.usable_buffer(eq, peak) * cfg.base_risk_pct_of_buffer,
                   eq * cfg.max_risk_pct_of_equity, cfg.max_dollar_risk)
        budget = base * cfg.derisk_multiplier(eq, peak)
        if budget < cfg.min_dollar_risk:
            return {
                "drawdown_at_which_the_account_dies": dd,
                "budget_there": round(budget, 2),
                "min_dollar_risk": cfg.min_dollar_risk,
                "last_live_drawdown": prev[0] if prev else None,
                "budget_one_step_earlier": prev[1] if prev else None,
                "failure_equity": cfg.failure_equity(peak),
                "equity_there": eq,
                "dollars_of_headroom_left_unused": round(
                    eq - cfg.failure_equity(peak), 2),
                "derisk_multiplier_there": cfg.derisk_multiplier(eq, peak),
            }
        prev = (dd, round(budget, 2))
        dd += step
    return {"drawdown_at_which_the_account_dies": None}


def measure_stage6(rows: Sequence[dict]) -> dict:
    """How many of the 176 strategies clear stage 6's quality floors.

    Measured, not assumed, because the whole replay is scoped on the claim that
    leaving stage 6 in would empty it.
    """
    cfg = AccountConfig()
    by: Dict[tuple, List[float]] = collections.defaultdict(list)
    for r in rows:
        by[(r["symbol"], r["tf"], r["arm"], r["exitm"])].append(float(r["r"]))
    clears = 0
    for k, rs in by.items():
        if len(rs) >= cfg.min_backtest_trades and stats.mean(rs) >= cfg.min_expectancy_r:
            clears += 1
    return {"strategies": len(by), "clearing_stage6_floors": clears,
            "min_trades": cfg.min_backtest_trades,
            "min_expectancy_r": cfg.min_expectancy_r}


# --------------------------------------------------------------------------
def main() -> None:
    rows = json.load(open(CACHE))
    report: dict = {"source": CACHE, "n_rows": len(rows)}

    report["static_integer_floor"] = static_integer_floor(rows, vol_aware=True)
    report["static_integer_floor_vol_pinned"] = static_integer_floor(
        rows, vol_aware=False)
    report["floor_by_volatility"] = floor_by_volatility(rows, vol_aware=True)
    report["floor_by_volatility_vol_pinned"] = floor_by_volatility(
        rows, vol_aware=False)
    report["stage6"] = measure_stage6(rows)

    report["absorbing_boundary"] = absorbing_boundary()

    pooled = sort_stream(rows)      # the labelled anchor, not the headline

    # ---- POOLED anchor runs: the 2x2x2 arm grid -------------------------
    runs = {}
    for le in (True, False):
        for cap_open in (False, True):
            for barrier in (True, False):
                lbl = (f"ANCHOR live_eligible={le} "
                       f"cap={'open' if cap_open else 'close'} "
                       f"barrier={barrier}")
                runs[lbl] = replay(pooled, label=lbl, live_eligible=le,
                                   cap_on_open=cap_open, barrier=barrier)
    # and the held-constant volatility control, on the anchor order
    runs["ANCHOR vol_aware=False (control)"] = replay(
        pooled, label="ANCHOR vol_aware=False (control)", vol_aware=False)

    # ---- PRIMARY: the seeded-order distribution ------------------------
    # R3's ruling: any *fixed* tiebreak on a field correlated with sizeability
    # biases the result, and `taken_pct` is not one quantity measured with noise
    # - it mostly encodes whether and when the account crossed the absorbing
    # boundary. So the seeded distribution is the result and the anchor is a
    # reproducibility aid.
    order_runs = [replay(sort_stream(rows, seed=s),
                         label=f"SEED {s}", live_eligible=True)
                  for s in range(1, N_ORDER_SEEDS + 1)]
    # the same seeds with the volatility multiplier pinned, as the control arm
    order_ctrl = [replay(sort_stream(rows, seed=s),
                         label=f"SEED {s} vol_aware=False", live_eligible=True,
                         vol_aware=False)
                  for s in range(1, N_ORDER_SEEDS + 1)]
    # the same seeds with the barrier off, to price the look-ahead
    order_leak = [replay(sort_stream(rows, seed=s),
                         label=f"SEED {s} barrier=False", live_eligible=True,
                         barrier=False)
                  for s in range(1, N_ORDER_SEEDS + 1)]

    # ---- placebo: R values permuted, timestamps and stops untouched -----
    # The governors' input is the *sequence* of outcomes. Permuting R
    # count-matched destroys any serial structure while leaving every stop
    # distance, every timestamp and every exposure clash identical, so a
    # governor effect that survives the permutation is not reading the
    # signal - it is reading the calendar and the stop distribution.
    # It is run over the *same seed ensemble* as the primary arm, because a
    # single placebo run against a 200-seed distribution is not a control - the
    # ordering spread is larger than most effects here.
    placebos = []
    for s in range(1, N_ORDER_SEEDS + 1):
        srt = sort_stream(rows, seed=s)
        perm = [float(r["r"]) for r in srt]
        random.Random(90000 + s).shuffle(perm)
        placebos.append(replay(srt, label=f"PLACEBO seed={s}",
                               live_eligible=True, r_override=perm))
    rng = random.Random(20260927)
    perm = [float(r["r"]) for r in pooled]
    rng.shuffle(perm)
    placebo = replay(pooled, label="ANCHOR placebo (R permuted)",
                     live_eligible=True, r_override=perm)

    # ---- PER_STRATEGY: 176 fresh accounts ------------------------------
    by_strat: Dict[tuple, List[dict]] = collections.defaultdict(list)
    for r in rows:
        by_strat[(r["symbol"], r["tf"], r["arm"], r["exitm"])].append(r)
    per = []
    for k, rs in sorted(by_strat.items()):
        per.append(replay(sort_stream(rs), label="|".join(str(x) for x in k),
                          live_eligible=True))

    def pack(res: ReplayResult) -> dict:
        return {
            "label": res.label, "candidates": res.n_candidates,
            "taken": res.n_taken,
            "taken_pct": round(100.0 * res.n_taken / max(1, res.n_candidates), 3),
            "vetoes": dict(sorted(res.vetoes.items())),
            "final_equity": round(res.final_equity, 2),
            "peak_equity": round(res.peak_equity, 2),
            "min_equity": round(res.min_equity, 2),
            "failed": res.failed, "days_seen": res.days_seen,
            "mean_contracts": (round(stats.mean(res.contracts), 3)
                               if res.contracts else 0.0),
            "max_contracts": max(res.contracts) if res.contracts else 0,
            "mean_r_taken": (round(stats.mean(res.taken_r), 5)
                             if res.taken_r else None),
            "mean_r_refused": (round(stats.mean(res.refused_r), 5)
                               if res.refused_r else None),
            "max_taken_in_a_day": (max(res.per_day_taken.values())
                                   if res.per_day_taken else 0),
            "days_over_6_taken": sum(1 for v in res.per_day_taken.values() if v > 6),
            "floor_deleted_at_opening_budget": res.floor_deleted_at_opening_budget,
            "floor_deleted_only_when_shrunk": res.floor_deleted_only_when_shrunk,
            "median_dollar_risk_taken": (round(stats.median(res.budgets), 2)
                                         if res.budgets else None),
            "absorbing": res.absorbing,
            "death_index": res.death_index,
            "death_ts": res.death_ts,
            "death_drawdown": (round(res.death_drawdown, 2)
                               if res.death_drawdown is not None else None),
            "taken_before_death": res.taken_before_death,
            "max_drawdown": round(res.max_drawdown, 2),
        }

    def pack_dist(name: str, rs: List[ReplayResult]) -> dict:
        """The statistics R3 asked for, over a seed ensemble."""
        tp = sorted(100.0 * p.n_taken / max(1, p.n_candidates) for p in rs)
        dead = [p for p in rs if p.absorbing]
        return {
            "arm": name, "n_seeds": len(rs),
            "taken_pct_median": round(stats.median(tp), 3),
            "taken_pct_p05": round(tp[int(0.05 * len(tp))], 3),
            "taken_pct_p95": round(tp[min(len(tp) - 1, int(0.95 * len(tp)))], 3),
            "taken_pct_min": round(tp[0], 3), "taken_pct_max": round(tp[-1], 3),
            "n_absorbing": len(dead),
            "pct_absorbing": round(100.0 * len(dead) / len(rs), 1),
            "n_failed_hard": sum(1 for p in rs if p.failed),
            "death_index_median": (stats.median(p.death_index for p in dead)
                                   if dead else None),
            "death_ts_earliest": min((p.death_ts for p in dead), default=None),
            "death_ts_latest": max((p.death_ts for p in dead), default=None),
            "taken_before_death_median": (
                stats.median(p.taken_before_death for p in dead)
                if dead else None),
            "max_drawdown_median": round(
                stats.median(p.max_drawdown for p in rs), 2),
            "max_drawdown_max": round(max(p.max_drawdown for p in rs), 2),
            "mean_r_taken_median": round(stats.median(
                stats.mean(p.taken_r) for p in rs if p.taken_r), 5),
            # Per-seed, so the arms can be compared *paired*. The seeds are
            # shared across arms, so an unpaired test would ignore the largest
            # source of common variance - the ordering itself - and D28 is this
            # repo's standing warning about exactly that failure.
            "absorbing_by_seed": [p.absorbing for p in rs],
            "taken_by_seed": [p.n_taken for p in rs],
        }

    report["anchor"] = {k: pack(v) for k, v in runs.items()}
    report["primary"] = {
        "vol_aware_barrier": pack_dist("vol_aware=True barrier=True", order_runs),
        "vol_pinned_control": pack_dist("vol_aware=False barrier=True",
                                        order_ctrl),
        "barrier_off_leak": pack_dist("vol_aware=True barrier=False",
                                      order_leak),
        "placebo_ensemble": pack_dist("PLACEBO (R permuted), same 200 seeds",
                                      placebos),
        "seeds": [pack(v) for v in order_runs],
    }
    report["placebo"] = pack(placebo)
    report["per_strategy"] = {
        "n_strategies": len(per),
        "taken_pct_median": round(stats.median([
            100.0 * p.n_taken / max(1, p.n_candidates) for p in per]), 3),
        "taken_pct_min": round(min(100.0 * p.n_taken / max(1, p.n_candidates)
                                   for p in per), 3),
        "taken_pct_max": round(max(100.0 * p.n_taken / max(1, p.n_candidates)
                                   for p in per), 3),
        "n_accounts_failed": sum(1 for p in per if p.failed),
        "n_accounts_absorbing": sum(1 for p in per if p.absorbing),
        "taken_total": sum(p.n_taken for p in per),
        "candidates_total": sum(p.n_candidates for p in per),
        "veto_totals": dict(sorted(
            sum((collections.Counter(p.vetoes) for p in per),
                collections.Counter()).items())),
        "rows": [pack(p) for p in per],
    }
    per_ctrl = [replay(sort_stream(rs), label="ctrl", vol_aware=False)
                for _, rs in sorted(by_strat.items())]
    report["per_strategy_vol_pinned"] = {
        "taken_total": sum(p.n_taken for p in per_ctrl),
        "veto_totals": dict(sorted(
            sum((collections.Counter(p.vetoes) for p in per_ctrl),
                collections.Counter()).items())),
    }

    out = os.path.join(ROOT,
                       "workspace/roundtable/backtest/BT3/code/algo1_report.json")
    json.dump(report, open(out, "w"), indent=1, default=str)

    ab = report["absorbing_boundary"]
    print("ABSORBING STATE: the account can open nothing past a drawdown of "
          f"${ab['drawdown_at_which_the_account_dies']:,.0f} "
          f"(budget ${ab['budget_there']:.2f} < min ${ab['min_dollar_risk']:.0f}), "
          f"with ${ab['dollars_of_headroom_left_unused']:,.0f} of the $5,000 "
          "failure buffer still unused\n")

    for name, key in (("vol-aware", "static_integer_floor"),
                      ("vol-pinned", "static_integer_floor_vol_pinned")):
        f = report[key]
        print(f"static integer floor, {name}, base ${f['budget']:.0f}: "
              f"{f['deleted']}/{f['n']} deleted ({f['deleted_pct']:.2f}%)")
    f = report["static_integer_floor"]
    for k, v in f["by_symbol_tf"].items():
        print(f"   {k:10s} n={v['n']:5d} deleted={v['deleted_pct']:6.2f}% "
              f"median_contracts={v['median_contracts']}")
    print(f"stage 6: {report['stage6']}\n")

    for k in ("vol_aware_barrier", "vol_pinned_control", "barrier_off_leak",
              "placebo_ensemble"):
        d = report["primary"][k]
        print(f"PRIMARY {d['arm']:<34s} taken% median={d['taken_pct_median']:6.3f} "
              f"[p05 {d['taken_pct_p05']:.3f}, p95 {d['taken_pct_p95']:.3f}]  "
              f"absorbing {d['n_absorbing']}/{d['n_seeds']} ({d['pct_absorbing']}%)  "
              f"hard-failed {d['n_failed_hard']}  "
              f"maxDD median ${d['max_drawdown_median']:,.0f}")
        if d["n_absorbing"]:
            print(f"        death: median index {d['death_index_median']}, "
                  f"{d['death_ts_earliest'][:10]} .. {d['death_ts_latest'][:10]}, "
                  f"median {d['taken_before_death_median']} taken before it")
    print()
    print("ANCHOR runs (reproducibility only, biased tiebreak):")
    for k, v in runs.items():
        p = pack(v)
        print(f"   {k:<52s} taken={p['taken']:4d} absorbing={p['absorbing']!s:5s} "
              f"maxDD=${p['max_drawdown']:,.0f} deathDD="
              f"{p['death_drawdown']}")
    p = pack(placebo)
    print(f"\nplacebo (R permuted): taken={p['taken']} "
          f"absorbing={p['absorbing']} maxDD=${p['max_drawdown']:,.0f}")
    ps = report["per_strategy"]
    print(f"\nPER_STRATEGY over {ps['n_strategies']} accounts: "
          f"taken {ps['taken_total']}/{ps['candidates_total']} "
          f"({100.0 * ps['taken_total'] / ps['candidates_total']:.2f}%), "
          f"median {ps['taken_pct_median']}% "
          f"[{ps['taken_pct_min']}, {ps['taken_pct_max']}], "
          f"hard-failed={ps['n_accounts_failed']}, "
          f"absorbing={ps['n_accounts_absorbing']}")
    print("   vetoes:", ps["veto_totals"])
    print(f"   vol-pinned control taken {report['per_strategy_vol_pinned']['taken_total']}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
