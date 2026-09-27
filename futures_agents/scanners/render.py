"""Rendering a breach opportunity as a desk callout.

The colour convention is not re-derived here. Direction goes through
:func:`futures_agents.alerts.alert` with ``Priority.LONG`` / ``Priority.SHORT``
/ ``Priority.NO_TRADE``, so the terminal, the HTML dashboard and the risk
console all agree: blue is a buy, orange is a sell, grey is a stand-down.

Every callout carries its measured base rate and the placebo it is measured
against, in the body rather than a footnote. A scanner that shows a setup
without showing that random levels produce the same outcome distribution is
selling structure as if it were edge.
"""

from __future__ import annotations

from typing import List, Optional, Sequence

from ..alerts import Priority, alert
from ..config import get_contract
from ..schema import Direction
from ..timeutil import et_stamp, to_et
from .breach import Opportunity

__all__ = ["render_opportunity", "opportunity_body"]

#: Measured on this repository's own archive: 5,717 real key-level breaches
#: across MNQ/MES/MCL/MGC at 60m and 240m, against 4,729 placebo breaches on
#: random levels drawn from the same price ranges.
MEASURED = {
    "real_breakout_rate": 0.430,
    "placebo_breakout_rate": 0.426,
    "n_real": 5717,
    "n_placebo": 4729,
}


def opportunity_body(o: Opportunity, *, contracts: Optional[int] = None,
                     dollar_risk: Optional[float] = None,
                     base_rate: Optional[float] = None,
                     sample: Optional[int] = None) -> str:
    """The callout body: levels, arithmetic, and the honest confidence."""
    spec = get_contract(o.symbol)
    dp = max(0, min(6, len(str(spec.tick_size).split(".")[-1])))
    risk_pts = abs(o.entry - o.stop)
    lines = [
        f"{o.symbol}  {o.timeframe}m   playbook {o.playbook}",
        f"  level        {o.level.name} @ {o.level.price:.{dp}f}  "
        f"({o.level.kind.lower()}, {o.level.source}, weight {o.level.weight:.2f})",
        f"  entry        {o.entry:.{dp}f}",
        f"  stop         {o.stop:.{dp}f}   ({risk_pts:.{dp}f} pts, "
        f"{spec.ticks_between(o.entry, o.stop):.0f} ticks, {o.stop_atr:.2f} ATR)",
        f"  target       {o.target:.{dp}f}   (R:R {o.reward_risk:.2f})",
        f"  ${risk_pts * spec.point_value:,.2f} per contract at this stop",
    ]
    if contracts is not None and dollar_risk is not None:
        lines.append(f"  size         {contracts} contract(s), "
                     f"${dollar_risk:,.2f} at risk")
    lines += ["", f"  why          {o.rationale}"]

    if not o.tradeable:
        lines += ["", f"  REJECTED     {o.reject_reason}"]

    rate = base_rate if base_rate is not None else MEASURED["real_breakout_rate"]
    n = sample if sample is not None else MEASURED["n_real"]
    lines += [
        "",
        "  CONFIDENCE   discretionary chart-reading, not a measured edge.",
        f"    This setup's class resolved in the intended direction {rate:.1%} of "
        f"the time over {n:,} occurrences",
        f"    in this repository's own archive. Random levels drawn from the same "
        f"price range resolved",
        f"    {MEASURED['placebo_breakout_rate']:.1%} of the time over "
        f"{MEASURED['n_placebo']:,} occurrences. The two are indistinguishable.",
        "    Trade the structure if your read supports it; do not trade it because "
        "the scanner found it.",
    ]
    return "\n".join(lines)


def render_opportunity(o: Opportunity, **kw) -> str:
    """Render one opportunity in its direction colour."""
    if not o.tradeable:
        priority, head = Priority.NO_TRADE, f"NO TRADE  {o.symbol}  {o.playbook}"
    elif o.direction is Direction.LONG:
        priority, head = Priority.LONG, f"{o.symbol}  {o.playbook}  @ {o.entry}"
    elif o.direction is Direction.SHORT:
        priority, head = Priority.SHORT, f"{o.symbol}  {o.playbook}  @ {o.entry}"
    else:
        priority, head = Priority.NO_TRADE, f"NO TRADE  {o.symbol}"
    return alert(priority, head, opportunity_body(o, **kw))
