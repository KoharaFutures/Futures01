"""A minimal, independent implementation of the 18:00 ET -> 16:00 ET clock rule.

**EF1 owns the engine rule for this programme. This is not it.** This is a
second, deliberately small implementation whose only purposes are

1. to let EF6 produce an honest ledger for the forward-test machinery before
   EF1's version lands, and
2. to be a **cross-check** on EF1's version afterwards. Two independent
   implementations that agree on trade counts and on exit-reason mix are
   evidence; one implementation is not. If they disagree, at least one is wrong
   and the disagreement is diagnostic.

The rule, as two overrides and nothing else:

* **No position opened while the fill bar is out of window.** Entries fill at
  the next bar's open `[repo-verified: engine.py:287-299]`, so vetoing in
  ``_open_position`` - which receives the *fill* bar - is exactly "no new
  position between 16:00 and 18:00 ET".
* **Flat at 16:00.** If the **next** bar is out of window, this bar is the last
  one the position may exist on, so it closes at this bar's close. On the 60m
  grid the bar before the 16:00 bar is the 15:00 bar, which ends at 16:00, so
  this is flat *at* 16:00 exactly rather than approximately.

``allow_overnight=True`` is forced, because the inherited session exit closes at
the **contract's own RTH close** - 13:30 for MGC, 14:30 for MCL
`[repo-verified: engine.py:470-473, EDGE_BRIEF.md:31-36]` - and leaving it on
would close every position hours before 16:00 and delete the overnight hold this
programme exists to measure.

A "next bar out of window" test is also satisfied by a **data gap**, which is
the right behaviour: if the series has no bar covering the next interval the
position cannot be managed, and holding through an unobserved interval is a
fill assumption, not a measurement.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from futures_agents.backtest.engine import BacktestEngine, ExitReason
from futures_agents.features import SymbolFrame

import window as W

__all__ = ["SessionWindowEngine"]


class SessionWindowEngine(BacktestEngine):
    """``BacktestEngine`` with the 18:00->16:00 window enforced on the base grid."""

    def __init__(self, frame: SymbolFrame, cost_model=None, *,
                 max_concurrent_per_strategy: int = 1):
        super().__init__(frame, cost_model,
                         max_concurrent_per_strategy=max_concurrent_per_strategy,
                         allow_overnight=True)
        bars = frame.base.bars
        minutes = int(frame.base.minutes)
        if 1320 % minutes != 0:
            raise ValueError(
                f"{minutes}m does not tile the 22-hour window (1320 minutes), so "
                "the rule cannot be enforced on this grid. 240m and 1440m are "
                "excluded; use 5/15/30/60/120m as the base and read the coarser "
                "timeframe out of the snapshot instead.")
        self._in_window: List[bool] = W.window_mask(bars, minutes)
        #: True when the NEXT bar may not hold a position, i.e. this bar is the
        #: last one before 16:00 (or before a gap, or the end of data).
        self._last_before_close: List[bool] = [
            (not self._in_window[i + 1]) if i + 1 < len(bars) else True
            for i in range(len(bars))]
        self.vetoed_entries = 0
        self.window_closes = 0

    # -- no new position while the fill bar is out of window ---------------
    def _open_position(self, strategy, sig, i, bar):
        if not self._in_window[i]:
            self.vetoed_entries += 1
            return None
        return super()._open_position(strategy, sig, i, bar)

    # -- flat at 16:00 -----------------------------------------------------
    def _manage(self, pos, i, bar, *, is_last: bool):
        trade = super()._manage(pos, i, bar, is_last=is_last)
        if trade is not None:
            return trade
        if self._last_before_close[i]:
            self.window_closes += 1
            return self._close(pos, i, bar, bar.close, ExitReason.SESSION_CLOSE)
        return None

    def audit(self) -> dict:
        """What the rule actually did, so it can be compared with EF1's."""
        return {"base_minutes": self.base_minutes,
                "bars": len(self._in_window),
                "in_window_bars": sum(self._in_window),
                "out_of_window_bars": len(self._in_window) - sum(self._in_window),
                "entries_vetoed_by_window": self.vetoed_entries,
                "positions_closed_at_the_window_boundary": self.window_closes,
                "allow_overnight": self.allow_overnight,
                "inherited_rth_session_exit_active": False}
