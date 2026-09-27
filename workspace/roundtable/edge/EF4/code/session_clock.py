"""EF4's own 18:00 ET -> 16:00 ET harness.

**This is not the programme harness.** EF1 owns that, and until EF1 validates, no
profitability number measured here may be reported as a programme result. This exists so
that (a) EF4's population is runnable the moment EF1 validates, and (b) there are two
independent implementations of the same clock rule, which is the only way to tell an
implementation artefact from a market fact. Where the two disagree, EF1's is canonical
and the disagreement is the finding.

## What the rule is, and what the engine does instead

The rule: a position may exist only inside 18:00 ET -> 16:00 ET the next day; nothing
held across 16:00-18:00 ET; no new position opened in 16:00-18:00 ET; holding through
Globex and the next RTH open is permitted.

The shipped engine cannot say this `[repo-verified: engine.py:468-472]`:

    if exit_model.exit_at_session_close and not self.allow_overnight:
        elapsed = minutes_since_open(bar.ts, spec.rth_open) + bar.minutes
        if elapsed >= self._rth_minutes:
            return self._close(pos, i, bar, bar.close, ExitReason.SESSION_CLOSE)

- the clock is the CONTRACT's RTH close - 13:30 for MGC, 14:30 for MCL - not 16:00 ET;
- it is gated on `not allow_overnight`, so enabling overnight REMOVES the session exit
  rather than moving it;
- and it is further gated on the strategy's own `exit_at_session_close` flag, so a
  strategy with that flag off was never session-bounded at all.

## What this subclass adds

1. **A hard 16:00 ET flat.** On the bar whose END lands at or after 16:00 ET while its
   START is before it, the position is closed at that bar's close, reason
   `SESSION_CLOSE`. 16:00 ET = 960 minutes and 960 is divisible by 5, 15 and 30, so on
   the three scalp timeframes a bar ends exactly at 16:00 and no bar straddles it. That
   is asserted, not assumed (`assert_clean`).
2. **No entry in the prohibition window.** A pending entry whose fill bar is stamped in
   [16:00, 18:00) ET is dropped, and counted. Dropping is the correct reading: the
   signal existed and was not actionable.
3. **`allow_overnight=True` always**, so the contract-RTH exit above is inert and the
   16:00 clock is the only session exit.

## What it does NOT change

Entry still fills at the next bar's open; stop still wins a same-bar tie; gaps still
fill at the open; slippage still enters the fill price and commission still enters as
dollars. Those are the engine's correctness rules and this subclass leaves them alone.
"""
from __future__ import annotations

from datetime import time as dtime
from typing import Dict, Optional, Tuple

from futures_agents.backtest.engine import (BacktestEngine, ExitReason, Trade,
                                            _OpenPosition)
from futures_agents.data.bars import Bar
from futures_agents.timeutil import to_et

FLAT_AT = dtime(16, 0)
REOPEN_AT = dtime(18, 0)


def in_prohibition(ts) -> bool:
    """Is this stamp inside 16:00-18:00 ET, where no position may be opened?"""
    t = to_et(ts).time()
    return FLAT_AT <= t < REOPEN_AT


def is_flat_bar(bar: Bar) -> bool:
    """Does this bar's close land the 16:00 ET flat?

    True when the bar starts before 16:00 ET and ends at or after it. The bar's close
    is therefore the last price inside the session.
    """
    start = to_et(bar.ts).time()
    end_dt = to_et(bar.end_ts)
    if start >= FLAT_AT:
        return False
    # end_ts may roll past midnight only for bars far longer than 30m; guard anyway.
    if to_et(bar.ts).date() != end_dt.date():
        return True
    return end_dt.time() >= FLAT_AT


class ScalpSessionEngine(BacktestEngine):
    """``BacktestEngine`` under the 18:00->16:00 ET rule."""

    def __init__(self, frame, cost_model=None, **kw):
        kw.pop("allow_overnight", None)
        super().__init__(frame, cost_model, allow_overnight=True, **kw)
        #: diagnostics, so a suppressed signal is never invisible
        self.entries_suppressed_prohibition = 0
        self.entries_into_flat_bar = 0
        self.forced_flat_exits = 0

    def _open_position(self, strategy, sig, i: int, bar: Bar):
        if in_prohibition(bar.ts):
            self.entries_suppressed_prohibition += 1
            return None
        pos = super()._open_position(strategy, sig, i, bar)
        if pos is not None and is_flat_bar(bar):
            # A legal entry that the 16:00 flat closes on its own bar. Counted, kept:
            # dropping it after seeing it would be narrowing the rule post hoc.
            self.entries_into_flat_bar += 1
        return pos

    def _manage(self, pos: _OpenPosition, i: int, bar: Bar, *, is_last: bool):
        trade = super()._manage(pos, i, bar, is_last=is_last)
        if trade is not None:
            return trade
        if is_flat_bar(bar):
            self.forced_flat_exits += 1
            return self._close(pos, i, bar, bar.close, ExitReason.SESSION_CLOSE)
        return None


def assert_clean(frame, results) -> Dict[str, int]:
    """Post-conditions this harness must satisfy. Raises on violation.

    1. No bar in the base series straddles 16:00 ET (would make the flat ambiguous).
    2. No trade is entered inside [16:00, 18:00) ET.
    3. No trade is held across the prohibition: for every trade, no bar strictly between
       entry and exit is stamped in the window, and the exit itself is not in it.
    """
    straddle = 0
    for b in frame.base.bars:
        s, e = to_et(b.ts).time(), to_et(b.end_ts).time()
        if s < FLAT_AT < e:
            straddle += 1
    if straddle:
        raise AssertionError(
            f"{straddle} bars straddle 16:00 ET on a {frame.base.minutes}m series; "
            "the flat rule is ambiguous and must be defined explicitly")

    bars = frame.base.bars
    bad_entry = bad_hold = 0
    n_trades = 0
    for res in results.values():
        for t in res.trades:
            n_trades += 1
            if in_prohibition(t.entry_ts):
                bad_entry += 1
            # Exact: walk the bar grid the position actually occupied.
            lo, hi = t.entry_index, max(t.entry_index, t.exit_index)
            if any(in_prohibition(bars[k].ts) for k in range(lo, hi + 1)):
                bad_hold += 1
    if bad_entry or bad_hold:
        raise AssertionError(f"session rule violated: {bad_entry} illegal entries, "
                             f"{bad_hold} illegal holds over {n_trades} trades")
    return {"trades": n_trades, "bars_straddling_1600": straddle}
