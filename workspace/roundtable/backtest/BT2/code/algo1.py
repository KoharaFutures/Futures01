"""ALGO-1 runner: the scheduled-event gate on the contracts whose own session
contains the prints.

What this file is for. R2's Q2 answer ranks "II-11 filter on MGC and MCL" as the
cheapest untried thing in its whole track, on the grounds that the one published
test of the family (F11:
``research/confluence/reversion_specialist.md:366-386``) ran on MNQ, whose own
RTH contains **7** in-session HIGH-impact event days, while MGC's contains 32 and
MCL's 49. This module is that test's apparatus. It deliberately does not search:
the arms are pre-declared, the parameters default to the library's own constants,
and the control is the same base population with no gate at all.

Three things it does NOT do, each for a stated reason.

* **It does not call ``toolkit.measure_custom``.** D38: ``measure_custom`` builds
  its own frame internally and never calls ``register_frame``, so a custom
  condition that needs the frame returns ``no()`` on every bar and the strategy
  reports zero trades - indistinguishable from "the idea does not work". ALGO-1's
  gates need no frame at all (they read ``snap.ts`` and ``snap.symbol`` only), so
  D38 cannot bite them; the frame is nonetheless built here, in the open, and
  handed to ``run_portfolio`` directly, so there is no hidden frame anywhere in
  the path.
* **It does not default ``rth_only=False``.** ``toolkit.make_strategy`` does, and
  D24 (the correction, DEFECTS.md:610) measured what that costs: trades rise
  2.1-4.2x and *paired median expectancy falls*, on three separate cells. For an
  event test ``rth_only`` is not a nuisance parameter - it is the variable that
  decides which prints the strategy can see at all, and R2's 7/32/49 counts are
  in-session counts. So the primary arm is ``rth_only=True``, which is both the
  library default (``base.py:393``) and the configuration F11 ran under, and
  ``rth_only=False`` is a separately declared secondary.
* **It does not size, rank or select.** Arms are compared pairwise on the same
  base strategies over the same bars; there is no league table.

**Store.** ``csv/raw`` is the default because it is the frozen snapshot every
published result in ``scan_reports/`` was measured on, which is what makes a
comparison against F11 meaningful. ``data/archive`` is supported because it
roughly doubles the span (60m: 2024-10-06 -> 2026-09-25 against
2025-10/11 -> 2026-09-22) and therefore roughly doubles the event count, and
because its earlier half is genuinely disjoint from ``csv/raw`` - which is what a
replication needs. Timestamps differ between the stores (``csv/raw`` is UTC,
``data/archive`` Eastern) and both are timezone-aware, so ``to_et`` reconciles
them; a naive string comparison across the two would be off by 4-5 hours.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[5]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from futures_agents.data.bars import Bar, BarSeries                     # noqa: E402
from futures_agents.data.loader import load_csv                         # noqa: E402
from futures_agents.econ_calendar import Impact                         # noqa: E402
from futures_agents.features import build_symbol_frame                  # noqa: E402
from futures_agents.scout import FRAMES                                 # noqa: E402
from futures_agents.strategies.base import (Condition, ConditionKind,    # noqa: E402
                                            Strategy)
from futures_agents.timeutil import is_rth, to_et                        # noqa: E402

from event_clock import EventClock, EventClockError, census              # noqa: E402
import event_gate as G                                                  # noqa: E402

__all__ = ["load_series", "load_frame", "gate_arm", "preflight", "PreflightRow"]

#: ``csv/raw`` filename suffix per timeframe, matching ``toolkit.SUFFIX``.
CSV_SUFFIX: Dict[int, str] = {1440: "1d", 60: "1h", 30: "30m", 15: "15m", 5: "5m",
                              1: "1m"}


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------

def _load_jsonl(path: Path, symbol: str, minutes: int) -> BarSeries:
    """``data/archive`` series. One JSON object per line, Eastern timestamps."""
    series = BarSeries(symbol, minutes)
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            series.append(Bar(
                ts=datetime.fromisoformat(d["ts"]), open=float(d["o"]),
                high=float(d["h"]), low=float(d["l"]), close=float(d["c"]),
                volume=float(d.get("v") or 0.0), minutes=minutes))
    return series


def load_series(symbol: str, tf: int, *, store: str = "csv") -> BarSeries:
    """Bars for one (symbol, timeframe) from the named store.

    Absolute paths throughout: the repo idiom is to assume the process was
    started at the repository root, which silently loads nothing when it was not.
    """
    sym = symbol.upper()
    if store == "csv":
        suffix = CSV_SUFFIX.get(int(tf))
        if suffix is None:
            raise EventClockError(f"no csv/raw suffix for {tf}m")
        path = REPO_ROOT / "csv" / "raw" / f"{sym}_{suffix}.csv"
        if not path.exists():
            raise EventClockError(f"missing {path}")
        return load_csv(str(path), sym, int(tf))
    if store == "archive":
        path = REPO_ROOT / "data" / "archive" / f"{sym}_{int(tf)}m.jsonl"
        if not path.exists():
            raise EventClockError(f"missing {path}")
        return _load_jsonl(path, sym, int(tf))
    raise EventClockError(f"unknown store {store!r}; expected 'csv' or 'archive'")


def load_frame(symbol: str, tf: int, *, store: str = "csv",
               timeframes: Optional[Sequence[int]] = None):
    """A ``SymbolFrame`` whose ``spec`` is the contract's own.

    ``SymbolFrame.__init__`` resolves ``spec or get_contract(base.symbol)``
    (``features.py:802``), so MGC gets 08:20-13:30 and MCL 09:00-14:30 without
    being told - provided the series carries the right symbol, which is the one
    thing to get right here. The equity 09:30-16:00 default is what R2's first
    pass applied to all four contracts before self-correcting, and it is also
    what ``timeutil.is_rth``'s own signature defaults to, so the failure mode is
    one forgotten argument away at all times.
    """
    series = load_series(symbol, tf, store=store)
    tfs = list(timeframes) if timeframes else FRAMES.get(int(tf), [int(tf)])
    return build_symbol_frame(series, tfs)


# --------------------------------------------------------------------------
# Arms
# --------------------------------------------------------------------------

def gate_arm(base: Strategy, gate: Condition) -> Strategy:
    """``base`` with one gate appended, as a genuinely distinct strategy.

    ``_id=None`` is mandatory and not cosmetic. ``Strategy._id`` is a cached
    field (``base.py:588``) and ``dataclasses.replace`` copies field values, so
    without it the gated arm inherits the bare arm's ``strategy_id``. Both arms
    then collide in ``run_portfolio``'s results dict, which is keyed on
    ``strategy_id`` (``engine.py:277``), and one arm silently reports the other's
    trades. The repo already uses this idiom in four places, e.g.
    ``combinator.py:694`` and ``newstrats/rank.py:142``.
    """
    if gate.kind is not ConditionKind.FILTER:
        raise EventClockError(
            f"{gate.name}: a gate must be a FILTER, got {gate.kind}")
    if any(c.name == gate.name for c in base.conditions):
        raise EventClockError(
            f"{base.name} already carries {gate.name}")
    return replace(base, conditions=base.conditions + (gate,), _id=None)


# --------------------------------------------------------------------------
# Pre-flight: the sample ceiling, before any backtest is run
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class PreflightRow:
    """How many bars a gate can admit at all, on one series.

    This is arithmetic on the bar clock and the recurrence rules. It reads no
    price, opens no position and computes no expectancy - the only inputs are
    bar timestamps and the calendar. It exists because it bounds the sample
    *before* any of it is spent: the engine takes at most one signal per bar and
    never while positioned (``engine.py:305-307``), so realised trades can never
    exceed the admissible-bar count, and a gate whose ceiling is below the
    20-trade reporting floor is answered before it is run.
    """

    symbol: str
    tf: int
    store: str
    bars: int
    first_ts: str
    last_ts: str
    rth_only: bool
    gate: str
    #: Bars the scope gate alone leaves, i.e. the denominator the gate acts on.
    eligible_bars: int
    admissible_bars: int
    admissible_days: int
    #: Admissible bars divided by the number of qualifying prints in the span -
    #: how many entry opportunities one print actually creates on this grid.
    bars_per_event: Optional[float]
    #: Of the admissible bars, how many are anchored on a print that landed
    #: OUTSIDE this contract's own session. On MCL an 08:30 CPI print is out of
    #: session (RTH opens 09:00) yet the 09:00 bar sits 30 minutes after it, so
    #: the gate admits an in-session bar off an out-of-session print. Whether
    #: that should count is a modelling choice, not an implementation detail, so
    #: it is reported rather than silently included.
    admissible_from_out_of_session_print: int


def _gate_passes(gate: Condition, snap, tf: int) -> bool:
    return gate.evaluate(snap, tf).triggered


def preflight(symbol: str, tf: int, gates: Dict[str, Condition], *,
              store: str = "csv", rth_only: bool = True,
              min_impact: Impact = Impact.HIGH) -> Tuple[dict, List[PreflightRow]]:
    """Census plus admissible-bar ceiling for each named gate.

    Returns ``(census_dict, rows)``. No strategy is constructed and no backtest
    is run.
    """
    frame = load_frame(symbol, tf, store=store)
    bars = frame.base.bars
    spec = frame.spec
    row = census(symbol, bars, min_impact=min_impact)
    n_events = row.events_in_rth if rth_only else row.events_in_span

    # Bar eligibility mirrors the engine: a signal can only be taken on bar i
    # when a bar i+1 exists to fill at (``engine.py:305``), and the scope gate
    # ``rth_only`` is applied by ``StrategyFilters.passes`` before any condition
    # is evaluated (``base.py:414``).
    eligible = [i for i in range(len(bars) - 1)
                if (not rth_only)
                or is_rth(bars[i].ts, spec.rth_open, spec.rth_close)]

    clock = EventClock(symbol, min_impact=min_impact)
    out: List[PreflightRow] = []
    for label, gate in gates.items():
        hits = []
        for i in eligible:
            snap = frame.snapshot(i)
            if snap is None:
                continue
            if _gate_passes(gate, snap, int(tf)):
                hits.append(i)
        days = {to_et(bars[i].ts).date() for i in hits}
        # Which side of the session the anchoring print was on. Only meaningful
        # for a gate anchored on a past print; for the avoidance gate it counts
        # the same thing about whichever print is nearest behind.
        out_of_session = 0
        for i in hits:
            r = clock.read_bar(bars[i].ts)
            if r.prev_name is None:
                continue
            # Recover the print's own timestamp from the reading.
            when = to_et(bars[i].ts) - timedelta(minutes=r.since_prev)
            if not is_rth(when, spec.rth_open, spec.rth_close):
                out_of_session += 1
        out.append(PreflightRow(
            symbol=symbol.upper(), tf=int(tf), store=store, bars=len(bars),
            first_ts=to_et(bars[0].ts).isoformat(),
            last_ts=to_et(bars[-1].ts).isoformat(),
            rth_only=rth_only, gate=label,
            eligible_bars=len(eligible),
            admissible_bars=len(hits), admissible_days=len(days),
            bars_per_event=(round(len(hits) / n_events, 3) if n_events else None),
            admissible_from_out_of_session_print=out_of_session,
        ))
    return _census_dict(row), out


def _census_dict(row) -> dict:
    d = asdict(row)
    d["first_ts"] = row.first_ts.isoformat()
    d["last_ts"] = row.last_ts.isoformat()
    return d


# --------------------------------------------------------------------------
# The pre-flight report, which is all this burst runs
# --------------------------------------------------------------------------

#: The gates ALGO-1's PRIMARY arms use. Exactly the library's own two windows,
#: so the comparison against F11 is a change of contract and nothing else.
def primary_gates() -> Dict[str, Condition]:
    return {
        "avoid@lib(10,15)": G.avoid_event(),                 # outside_news_blackout
        "after@lib(15,60]": G.after_event(),                 # post_news_window
    }


#: Declared secondaries. Each one is a variant and each costs deflation when
#: measured, which is why they are listed separately and counted.
def secondary_gates() -> Dict[str, Condition]:
    return {
        "after@lib+cluster60": G.after_event(cluster_minutes=60.0),
        "after@lib+offset(bar)": G.after_event(offset_min=60.0),
        "after@MEDIUM": G.after_event(min_impact=Impact.MEDIUM),
        "into(0,10]": G.into_event(),
    }


def report(symbols: Sequence[str] = ("MNQ", "MGC", "MCL"), tf: int = 60,
           *, store: str = "csv", include_secondary: bool = False) -> dict:
    """Census + ceiling for each symbol. MNQ is included as the reference arm:
    reproducing its 7 in-session event days is what shows the clock agrees with
    R2-D5, and reproducing MGC's 32 and MCL's 49 is what shows the contract's own
    session is being used rather than the equity one."""
    gates = dict(primary_gates())
    if include_secondary:
        gates.update(secondary_gates())
    out: dict = {"tf": tf, "store": store, "gates": sorted(gates),
                 "symbols": {}}
    for sym in symbols:
        cen_high, rows = preflight(sym, tf, gates, store=store,
                                   min_impact=Impact.HIGH)
        cen_med = _census_dict(census(sym, load_series(sym, tf, store=store).bars,
                                      min_impact=Impact.MEDIUM))
        out["symbols"][sym.upper()] = {
            "census_HIGH": cen_high,
            "census_MEDIUM_and_up": cen_med,
            "preflight": [asdict(r) for r in rows],
        }
    return out


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--symbols", default="MNQ,MGC,MCL")
    ap.add_argument("--tf", type=int, default=60)
    ap.add_argument("--store", default="csv", choices=("csv", "archive"))
    ap.add_argument("--secondary", action="store_true")
    a = ap.parse_args()
    print(json.dumps(report([s.strip() for s in a.symbols.split(",") if s.strip()],
                            a.tf, store=a.store,
                            include_secondary=a.secondary),
                     indent=2, default=str))
