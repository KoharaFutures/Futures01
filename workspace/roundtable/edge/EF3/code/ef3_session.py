"""EF3's 18:00->16:00 ET harness.

**It is now a two-line subclass of EF1's `SessionWindowEngine`**, so that every
fill convention, counter and audit is EF1's and the ONLY difference between the
two engines is the one clause I measured as missing. When EF1 adopts a fix,
`SessionEngine` becomes `SessionWindowEngine` and this file shrinks to nothing.

THE ONE DIFFERENCE, and it is measured, not argued
--------------------------------------------------
`session_window.classify_bar` is a pure function of one bar. A session whose
LAST bar is `OUTSIDE` therefore has no bar for the flat to fire on, and a
position is carried into the next session across 16:00 ET. On MES and MNQ at
60m that is **19 of 507 sessions (3.75%)**, every one a US holiday or early
close, and on a 400-strategy probe it produced **43 SPANS_WINDOW violations and
19 holds longer than 22 hours, the worst being 71.0 hours across two 16:00
deadlines**. Detail and the empirical comparison:
`workspace/roundtable/msgs/EF3-01_EF1_session-rule-misses-early-close-sessions.md`.

`SessionEngine` adds the missing clause: force the flat at the close of bar *i*
when `trading_day(bars[i+1].ts) != trading_day(bars[i].ts)`. That reads one bar
of the future - its TIMESTAMP only, never its prices - so it is exact at the cost
of prefix invariance at a session's last bar. The right fix is an exchange
calendar (`timeutil.MARKET_HOLIDAYS_2025_2027` exists), which is exact AND
prefix-invariant; this is the stopgap, and both readings are carried as arms.

Arithmetic that falls out of the rule and is worth stating once
--------------------------------------------------------------
* Max hold = 22 hours. Every `time_stop_bars` in the shipped catalogue is >= 30
  PRIMARY bars = >=30h at 60m and >=120h at 240m, so **the time stop is
  arithmetically inert in this cell** and every exit is STOP, TARGET or FLAT.
* `StrategyFilters.rth_only` defaults to **True** (`base.py:393`) and is True in
  both MES's and MNQ's research profile. It gates ENTRIES, not holding, so it
  caps the maximum hold at **6.5 hours**: the only legal entries are
  09:30-16:00 and the position must be flat at 16:00 the same day. The 22-hour
  window this programme exists to measure is reachable ONLY with
  `rth_only=False`. Both arms are in the population.
"""
from __future__ import annotations

import sys
from typing import List, Optional, Sequence, Tuple

sys.path.insert(0, "/home/user/Futures01/workspace/roundtable/edge/EF1/code")

from session_window import (BarWindow, SessionWindowEngine, classify_bar,  # noqa: E402
                            assert_hooks_reachable, flat_exit_keys, violations,
                            session_end_indices)

from futures_agents.backtest.engine import ExitReason, Trade, _OpenPosition  # noqa: E402
from futures_agents.data.bars import Bar  # noqa: E402
from futures_agents.timeutil import to_et, trading_day  # noqa: E402

__all__ = ["SessionEngine", "forced_flat_mask", "assert_hooks_reachable",
           "flat_exit_keys", "violations", "BarWindow", "classify_bar"]


def forced_flat_mask(bars: Sequence[Bar]) -> List[bool]:
    """``True`` on bar *i* when the session ends there without a 16:00 print.

    Exactly the gap `classify_bar` cannot see: bar *i* is the last bar of its
    trading day, bar *i*+1 belongs to a different trading day, and neither bar
    is ON_BOUNDARY or IN_WINDOW. Reads `bars[i+1].ts` and nothing else about it.
    """
    n = len(bars)
    tds = [trading_day(b.ts) for b in bars]
    kinds = [classify_bar(b.ts, b.minutes) for b in bars]
    out = [False] * n
    ef1 = set(session_end_indices(bars))   # EF1 component 1b, calendar-date based
    for i in range(n):
        if kinds[i] is not BarWindow.OUTSIDE:
            continue                      # EF1's per-bar rule handles this bar
        if i in ef1:
            continue                      # EF1's component 1b handles this bar
        if i == n - 1 or tds[i + 1] != tds[i]:
            out[i] = True
    return out


class SessionEngine(SessionWindowEngine):
    """EF1's engine plus the early-close clause."""

    def __init__(self, frame, *args, enforce_session_gap: bool = True, **kw):
        super().__init__(frame, *args, **kw)
        self.enforce_session_gap = bool(enforce_session_gap)
        self._forced = forced_flat_mask(frame.base.bars)
        self.forced_flats = 0
        self.forced_flat_bars = sum(self._forced)

    def _manage(self, pos: _OpenPosition, i: int, bar: Bar,
                *, is_last: bool) -> Optional[Trade]:
        trade = super()._manage(pos, i, bar, is_last=is_last)
        if trade is not None:
            return trade
        if self.enforce_session_gap and self._forced[i]:
            self.forced_flats += 1
            # Reuse EF1's flat, which prices the market order and relabels a
            # gapped fill as STOP. ON_BOUNDARY is the right class: the session
            # genuinely ended on this bar's close, earlier than 16:00.
            return self._flat(pos, i, bar, BarWindow.OUTSIDE, raw=bar.close,
                              forced_session_end=True)
        return None
