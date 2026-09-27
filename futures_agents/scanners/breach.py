"""Key-level breach scanning: three playbooks, one honest classifier.

A level being "broken" is not one event with one trade. It is three, and they
point in different directions:

* **BREAKOUT** - price closes beyond the level and keeps going. Trade with it.
* **FAILED BREACH** - price trades through the level and closes back inside.
  This is the liquidity sweep, and the trade is *against* the break.
* **RETEST** - price breaks, returns to the level, and the level holds from the
  other side. Trade with the break, from a better price.

A scanner that fires on "level broken" without separating these is taking all
three trades at once, which is how a breakout system ends up short at the low.
So this module's job is not to detect breaches - that part is trivial - but to
classify them, and to say how often each classification actually paid.

**What this is not.** ``CALLOUT.md`` records that ORB did not pay here, that
FVG and order-block fill rates are reproduced by random zones, and that the
ICT sweep/shift/retrace sequence "is real, common, and adds nothing over its
parts". None of that is contradicted by this module. A breach is *structure* -
a place where a decision gets made and where stops are parked - not a measured
edge. :mod:`futures_agents.scanners.measure` runs every setup found here
against a placebo of random levels, and the honest reading of an opportunity is
whatever that comparison says.

Two rules from the measurement are enforced in code rather than left to
judgement:

* a breach needs a **close** beyond the level by a buffer, not a wick. Wicks
  through levels are the norm, not the signal;
* the structural stop is never tighter than **0.5 ATR** (rule 4), so a breach
  whose natural stop is inside that floor is reported as untradeable rather
  than quietly widened.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

from ..config import ContractSpec, get_contract
from ..data.bars import Bar, BarSeries
from ..indicators.core import atr
from ..indicators.structure import (SessionLevels, session_levels,
                                    support_resistance)
from ..schema import Direction
from ..timeutil import to_et, trading_day

__all__ = ["KeyLevel", "BreachEvent", "Opportunity", "collect_levels",
           "find_breaches", "scan_symbol", "PLAYBOOKS"]


# --------------------------------------------------------------------------
# Levels
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class KeyLevel:
    """One reference price, and where it came from.

    ``weight`` is a prior on how much attention a level gets, not a prediction.
    A prior-day high is watched by everyone with a chart; a minor swing from
    forty bars ago is not. Keeping it explicit means the ranking can be argued
    with instead of being buried in a sort key.
    """

    name: str
    price: float
    kind: str            # RESISTANCE | SUPPORT | PIVOT
    source: str          # session | structure | round
    weight: float = 1.0

    def to_dict(self) -> dict:
        return {"name": self.name, "price": round(self.price, 6),
                "kind": self.kind, "source": self.source, "weight": self.weight}


#: Session levels, and how much weight each carries. The prior-day extremes and
#: the overnight range sit at the top because that is where resting stops
#: actually cluster - every retail platform draws them by default.
_SESSION_WEIGHTS: Dict[str, Tuple[str, float]] = {
    "prev_day_high":        ("RESISTANCE", 1.00),
    "prev_day_low":         ("SUPPORT",    1.00),
    "overnight_high":       ("RESISTANCE", 0.90),
    "overnight_low":        ("SUPPORT",    0.90),
    "prev_day_close":       ("PIVOT",      0.70),
    "initial_balance_high": ("RESISTANCE", 0.65),
    "initial_balance_low":  ("SUPPORT",    0.65),
    "session_high":         ("RESISTANCE", 0.55),
    "session_low":          ("SUPPORT",    0.55),
    "day_open":             ("PIVOT",      0.45),
}


def _round_levels(spec: ContractSpec, price: float, count: int = 2) -> List[KeyLevel]:
    """Whole-number levels near price.

    Round numbers matter because people place orders at them, not because of
    anything in the price series. The step is scaled to the contract so MNQ
    gets hundreds and MCL gets whole dollars.
    """
    if price <= 0:
        return []
    step = 100.0 if price > 5000 else 10.0 if price > 500 else 1.0 if price > 20 else 0.5
    base = round(price / step) * step
    out: List[KeyLevel] = []
    for k in range(-count, count + 1):
        lvl = base + k * step
        if lvl <= 0 or abs(lvl - price) < spec.tick_size:
            continue
        out.append(KeyLevel(f"round_{lvl:g}", lvl,
                            "RESISTANCE" if lvl > price else "SUPPORT",
                            "round", 0.40))
    return out


def collect_levels(bars: Sequence[Bar], *, symbol: str,
                   as_of: Optional[datetime] = None,
                   include_round: bool = True,
                   sr_lookback: int = 300) -> List[KeyLevel]:
    """Every level worth watching, computed only from bars at or before ``as_of``."""
    if not bars:
        return []
    spec = get_contract(symbol)
    cutoff = to_et(as_of) if as_of else bars[-1].ts
    visible = [b for b in bars if b.ts <= cutoff]
    if not visible:
        return []
    price = visible[-1].close

    levels: List[KeyLevel] = []
    sl: SessionLevels = session_levels(visible, as_of=cutoff,
                                       open_hhmm=spec.rth_open,
                                       close_hhmm=spec.rth_close)
    for name, (kind, weight) in _SESSION_WEIGHTS.items():
        value = getattr(sl, name, None)
        if value is None:
            continue
        levels.append(KeyLevel(name, float(value), kind, "session", weight))

    # Prior week's extremes. Weekly levels are watched by a different, slower
    # set of participants than the daily ones, so they are worth carrying
    # separately rather than folding into support/resistance.
    today = trading_day(cutoff)
    week_now = today.isocalendar()[:2]
    prior = [b for b in visible if to_et(b.ts).isocalendar()[:2] < week_now]
    if prior:
        last_week = max(to_et(b.ts).isocalendar()[:2] for b in prior)
        wk = [b for b in prior if to_et(b.ts).isocalendar()[:2] == last_week]
        if wk:
            levels.append(KeyLevel("prev_week_high", max(b.high for b in wk),
                                   "RESISTANCE", "session", 0.85))
            levels.append(KeyLevel("prev_week_low", min(b.low for b in wk),
                                   "SUPPORT", "session", 0.85))

    for sr in support_resistance(visible[-sr_lookback:]):
        levels.append(KeyLevel(f"sr_{sr.kind.lower()}_{sr.price:g}", sr.price,
                               sr.kind, "structure",
                               min(0.80, 0.35 + 0.12 * sr.touches)))

    if include_round:
        levels.extend(_round_levels(spec, price))

    # Collapse levels that sit within a tick of each other, keeping the heaviest.
    levels.sort(key=lambda l: (-l.weight, l.price))
    kept: List[KeyLevel] = []
    for lvl in levels:
        if any(abs(lvl.price - k.price) <= spec.tick_size for k in kept):
            continue
        kept.append(lvl)
    return sorted(kept, key=lambda l: l.price)


# --------------------------------------------------------------------------
# Breaches
# --------------------------------------------------------------------------

@dataclass
class BreachEvent:
    """One level, broken, classified by what happened next."""

    symbol: str
    timeframe: int
    level: KeyLevel
    direction: Direction          # LONG = broke up through, SHORT = broke down
    index: int                    # bar index of the breaching close
    ts: datetime
    breach_close: float
    penetration_atr: float        # how far beyond the level the close landed
    outcome: str = "PENDING"      # BREAKOUT | FAILED | RETEST | PENDING
    bars_to_outcome: int = 0
    excursion_atr: float = 0.0    # best move beyond the level, in ATR
    adverse_atr: float = 0.0      # worst move back through it, in ATR
    atr: float = 0.0

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
        d["level"] = self.level.to_dict()
        d["direction"] = self.direction.value
        d["ts"] = to_et(self.ts).isoformat()
        return d


def _atr_series(bars: Sequence[Bar], period: int = 14) -> List[Optional[float]]:
    return atr([b.high for b in bars], [b.low for b in bars],
               [b.close for b in bars], period)


def find_breaches(bars: Sequence[Bar], levels: Sequence[KeyLevel], *,
                  symbol: str, timeframe: int,
                  buffer_atr: float = 0.10,
                  horizon: int = 12,
                  failure_atr: float = 0.25) -> List[BreachEvent]:
    """Detect and classify every level breach in ``bars``.

    A breach requires a **close** beyond the level by ``buffer_atr``. A wick
    through a level is the normal state of affairs around round numbers and
    prior-day extremes, and counting one as a break produces a scanner that
    fires constantly and means nothing.

    Classification over the next ``horizon`` bars:

    * **FAILED** - price closes back through the level by ``failure_atr``. The
      break was a sweep; the trade is the other way.
    * **BREAKOUT** - price extends at least ``failure_atr`` beyond the level and
      never closes back inside by that margin.
    * **RETEST** - it does neither: it comes back to the level and hovers.
      Reported separately rather than being forced into one of the other two,
      because "undecided" is the honest label and it is common.
    """
    if len(bars) < 30 or not levels:
        return []
    atrs = _atr_series(bars)
    out: List[BreachEvent] = []

    for lvl in levels:
        for i in range(20, len(bars) - 1):
            a = atrs[i]
            if not a or a <= 0:
                continue
            prev_c, cur = bars[i - 1].close, bars[i]
            buf = buffer_atr * a

            if prev_c <= lvl.price and cur.close > lvl.price + buf:
                direction = Direction.LONG
            elif prev_c >= lvl.price and cur.close < lvl.price - buf:
                direction = Direction.SHORT
            else:
                continue

            ev = BreachEvent(
                symbol=symbol, timeframe=timeframe, level=lvl,
                direction=direction, index=i, ts=cur.ts,
                breach_close=cur.close,
                penetration_atr=abs(cur.close - lvl.price) / a, atr=a)

            fwd = bars[i + 1:i + 1 + horizon]
            best = worst = 0.0
            for n, b in enumerate(fwd, start=1):
                if direction is Direction.LONG:
                    best = max(best, (b.high - lvl.price) / a)
                    worst = min(worst, (b.low - lvl.price) / a)
                    failed = b.close < lvl.price - failure_atr * a
                else:
                    best = max(best, (lvl.price - b.low) / a)
                    worst = min(worst, (lvl.price - b.high) / a)
                    failed = b.close > lvl.price + failure_atr * a
                if failed:
                    ev.outcome, ev.bars_to_outcome = "FAILED", n
                    break
            ev.excursion_atr = round(best, 3)
            ev.adverse_atr = round(worst, 3)
            if ev.outcome == "PENDING":
                if best >= failure_atr:
                    ev.outcome = "BREAKOUT"
                    ev.bars_to_outcome = len(fwd)
                else:
                    ev.outcome = "RETEST"
                    ev.bars_to_outcome = len(fwd)
            out.append(ev)

    out.sort(key=lambda e: (e.index, -e.level.weight))
    return out


# --------------------------------------------------------------------------
# Playbooks - the "different strategies" part
# --------------------------------------------------------------------------

@dataclass
class Opportunity:
    """A tradeable proposal derived from a breach, with its stop already sane."""

    playbook: str
    symbol: str
    timeframe: int
    direction: Direction
    level: KeyLevel
    entry: float
    stop: float
    target: float
    ts: datetime
    atr: float
    rationale: str
    stop_atr: float = 0.0
    reward_risk: float = 0.0
    tradeable: bool = True
    reject_reason: str = ""

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items()}
        d["level"] = self.level.to_dict()
        d["direction"] = self.direction.value
        d["ts"] = to_et(self.ts).isoformat()
        return d


def _finalise(o: Opportunity, spec: ContractSpec) -> Opportunity:
    """Snap to tick, enforce the 0.5-ATR stop floor, compute R:R."""
    o.entry = spec.round_to_tick(o.entry)
    o.stop = spec.round_to_tick(o.stop)
    o.target = spec.round_to_tick(o.target)
    risk = abs(o.entry - o.stop)
    o.stop_atr = round(risk / o.atr, 3) if o.atr else 0.0
    o.reward_risk = round(abs(o.target - o.entry) / risk, 3) if risk else 0.0

    if risk <= 0:
        o.tradeable, o.reject_reason = False, "stop is at the entry"
    elif o.stop_atr < 0.5:
        # Measured rule 4: below 0.5 ATR a structural stop is noise, and the
        # tighter stop is hit more often than the better ratio is worth.
        o.tradeable = False
        o.reject_reason = (f"stop is {o.stop_atr:.2f} ATR, inside the 0.50 ATR "
                           "floor - widen it or skip the trade")
    elif spec.ticks_between(o.entry, o.stop) < spec.min_stop_ticks:
        o.tradeable = False
        o.reject_reason = (f"stop is {spec.ticks_between(o.entry, o.stop):.0f} "
                           f"ticks, inside {spec.symbol}'s {spec.min_stop_ticks}-"
                           "tick noise floor")
    return o


def _breakout_go(ev: BreachEvent, bars: Sequence[Bar], spec: ContractSpec
                 ) -> Optional[Opportunity]:
    """Trade with the break, stop back inside the level."""
    bar = bars[ev.index]
    long = ev.direction is Direction.LONG
    entry = bar.close
    stop = (ev.level.price - 0.55 * ev.atr) if long else (ev.level.price + 0.55 * ev.atr)
    risk = abs(entry - stop)
    target = entry + 2.0 * risk if long else entry - 2.0 * risk
    return _finalise(Opportunity(
        playbook="BREAKOUT_GO", symbol=ev.symbol, timeframe=ev.timeframe,
        direction=ev.direction, level=ev.level, entry=entry, stop=stop,
        target=target, ts=bar.ts, atr=ev.atr,
        rationale=(f"close {entry:g} broke {ev.level.name} at {ev.level.price:g} by "
                   f"{ev.penetration_atr:.2f} ATR; stop sits back inside the level")),
        spec)


def _failed_breach_fade(ev: BreachEvent, bars: Sequence[Bar], spec: ContractSpec
                        ) -> Optional[Opportunity]:
    """Trade *against* a break that closed back inside - the sweep.

    Only offered once the failure has actually printed. Anticipating a failure
    while price is still beyond the level is just fading a breakout.
    """
    if ev.outcome != "FAILED":
        return None
    j = min(ev.index + ev.bars_to_outcome, len(bars) - 1)
    bar = bars[j]
    long = ev.direction is Direction.SHORT          # broke DOWN and failed -> long
    entry = bar.close
    extreme = min(b.low for b in bars[ev.index:j + 1]) if long else \
              max(b.high for b in bars[ev.index:j + 1])
    stop = extreme - 0.25 * ev.atr if long else extreme + 0.25 * ev.atr
    risk = abs(entry - stop)
    target = entry + 2.0 * risk if long else entry - 2.0 * risk
    return _finalise(Opportunity(
        playbook="FAILED_BREACH_FADE", symbol=ev.symbol, timeframe=ev.timeframe,
        direction=Direction.LONG if long else Direction.SHORT, level=ev.level,
        entry=entry, stop=stop, target=target, ts=bar.ts, atr=ev.atr,
        rationale=(f"{ev.level.name} at {ev.level.price:g} was breached and "
                   f"reclaimed within {ev.bars_to_outcome} bars; stop beyond the "
                   f"sweep extreme {extreme:g}")), spec)


def _retest_hold(ev: BreachEvent, bars: Sequence[Bar], spec: ContractSpec
                 ) -> Optional[Opportunity]:
    """Trade with the break, entered on the pullback to the level."""
    if ev.outcome != "BREAKOUT":
        return None
    long = ev.direction is Direction.LONG
    entry = ev.level.price + 0.10 * ev.atr if long else ev.level.price - 0.10 * ev.atr
    stop = ev.level.price - 0.60 * ev.atr if long else ev.level.price + 0.60 * ev.atr
    risk = abs(entry - stop)
    target = entry + 2.0 * risk if long else entry - 2.0 * risk
    return _finalise(Opportunity(
        playbook="RETEST_HOLD", symbol=ev.symbol, timeframe=ev.timeframe,
        direction=ev.direction, level=ev.level, entry=entry, stop=stop,
        target=target, ts=bars[ev.index].ts, atr=ev.atr,
        rationale=(f"{ev.level.name} at {ev.level.price:g} broke and extended "
                   f"{ev.excursion_atr:.2f} ATR; this is a resting bid/offer back "
                   "at the level, not a chase")), spec)


PLAYBOOKS = {
    "BREAKOUT_GO": _breakout_go,
    "FAILED_BREACH_FADE": _failed_breach_fade,
    "RETEST_HOLD": _retest_hold,
}


def scan_symbol(bars: Sequence[Bar], *, symbol: str, timeframe: int,
                as_of: Optional[datetime] = None,
                playbooks: Optional[Sequence[str]] = None
                ) -> Tuple[List[BreachEvent], List[Opportunity]]:
    """Find every breach and every opportunity each playbook derives from it."""
    spec = get_contract(symbol)
    levels = collect_levels(bars, symbol=symbol, as_of=as_of)
    events = find_breaches(bars, levels, symbol=symbol, timeframe=timeframe)
    wanted = list(playbooks or PLAYBOOKS)
    opps: List[Opportunity] = []
    for ev in events:
        for name in wanted:
            fn = PLAYBOOKS.get(name)
            if fn is None:
                continue
            o = fn(ev, bars, spec)
            if o is not None:
                opps.append(o)
    return events, opps
