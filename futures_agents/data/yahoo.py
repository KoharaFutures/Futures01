"""A Yahoo Finance feed, and the six things that make one return nothing.

The network call is five lines. Everything else in this module exists because a
naive reader of this vendor fails *silently* - it returns an empty frame or a
subtly wrong bar rather than an error, so the failure shows up weeks later as a
backtest that flatters itself.

The six, each pinned by a test:

1. **Futures need the ``=F`` suffix.** ``MNQ`` is not a Yahoo symbol; ``MNQ=F``
   is. Asking for the bare root returns an empty frame, not an error. Note also
   that ``MNQ=F`` is not TradingView's ``MNQ1!`` - different vendor, different
   roll convention, so the two are not interchangeable in a backtest.

2. **Every interval has a hard lookback cap.** One-minute bars exist for seven
   days and no further. Ask for eight and you get nothing back, with no
   complaint. :func:`plan_request` clamps the window and *reports* the clamp
   rather than performing it quietly, because a caller who asked for 90 days of
   1m data has a misconception worth correcting.

3. **Yahoo has no 3m and no 4h bar.** This repository's MCL framework is
   specified at 240m, which this vendor cannot serve directly. Rather than fail,
   :meth:`YahooFeed.fetch` drops to the nearest finer interval it does have and
   resamples, and says so in the result.

4. **The last row is the forming bar.** Its high, low and close are not final.
   Including it is lookahead bias, and it is the most common way a backtest
   flatters itself. It is dropped unless explicitly requested.

5. **Timestamps are exchange-local and timezone-aware.** This codebase stores
   bar times in Eastern (see :class:`~futures_agents.data.bars.Bar`), so they are
   converted explicitly. A naive stamp is refused rather than assumed to be UTC -
   guessing shifts every session boundary by four or five hours.

6. **Missing volume arrives as NaN, not as zero.** Coercing it to ``0.0`` yields
   bars with a real price range and no volume, which quietly breaks any filter
   that reads volume as liquidity. Rows with no *price* are dropped; rows with no
   *volume* are kept, counted, and reported in
   :attr:`FetchResult.bars_missing_volume` so the caller can decide.

This module performs network I/O and is therefore never imported by the
deterministic core. ``yfinance`` is an optional dependency: absent, the import
below raises a message naming the install command rather than an ImportError
from three frames deep.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..config import CONTRACTS
from ..timeutil import ET, now_et, to_et
from .bars import Bar, BarSeries
from .providers import DataProvider

__all__ = ["YahooError", "YahooFeed", "YahooProvider", "FetchResult",
           "RequestPlan", "plan_request", "ticker_for", "INTERVALS"]


class YahooError(RuntimeError):
    """A request this feed cannot serve, with the reason spelled out."""


# --------------------------------------------------------------------------
# Interval table
# --------------------------------------------------------------------------

#: ``minutes -> (yahoo interval string, maximum lookback)``.
#:
#: The caps are one day inside Yahoo's published limits (7d for 1m, 60d for
#: intraday, 730d for hourly). The margin matters: the limit is enforced against
#: the vendor's clock, not ours, and a request sitting exactly on the boundary
#: intermittently returns empty depending on which side of midnight UTC it
#: lands. A day of slack costs nothing and removes a class of flake.
INTERVALS: Dict[int, Tuple[str, timedelta]] = {
    1:    ("1m",  timedelta(days=7)),
    2:    ("2m",  timedelta(days=59)),
    5:    ("5m",  timedelta(days=59)),
    15:   ("15m", timedelta(days=59)),
    30:   ("30m", timedelta(days=59)),
    60:   ("1h",  timedelta(days=720)),
    90:   ("90m", timedelta(days=59)),
    1440: ("1d",  timedelta(days=365 * 25)),
}

#: Timeframes this repository uses that Yahoo does not serve, and the finer
#: interval each is built from. 240m is the important one: MCL's measured
#: framework is specified at 60m *and* 240m, and there is no 4h bar here.
RESAMPLE_FROM: Dict[int, int] = {
    3:   1,
    10:  5,
    120: 60,
    240: 60,
}


def ticker_for(symbol: str) -> str:
    """Yahoo's ticker for a contract root.

    Known contracts get their root plus ``=F``. Anything already carrying a
    Yahoo suffix (``=F``, ``=X``, ``^GSPC``) is passed through untouched, so a
    caller can reach an index or an FX pair without this table growing to cover
    every instrument on the vendor.
    """
    key = symbol.upper().strip()
    if not key:
        raise YahooError("empty symbol")
    if key.startswith("^") or "=" in key:
        return key
    if key in CONTRACTS:
        return f"{key}=F"
    # Unknown root: still almost certainly a future, but say what was assumed.
    return f"{key}=F"


# --------------------------------------------------------------------------
# Request planning - pure, and therefore testable without a network
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class RequestPlan:
    """What will actually be asked of the vendor, and how it differs from the ask."""

    symbol: str
    ticker: str
    requested_minutes: int
    fetch_minutes: int            # may be finer, when resampling is needed
    interval: str                 # the vendor's interval string
    requested_days: float
    granted_days: float
    start: datetime
    end: datetime
    resampled: bool
    clamped: bool

    @property
    def notes(self) -> List[str]:
        out: List[str] = []
        if self.clamped:
            out.append(
                f"lookback clamped from {self.requested_days:.0f} to "
                f"{self.granted_days:.0f} days - Yahoo serves {self.interval} bars "
                f"no further back than that, and returns an EMPTY frame rather "
                f"than an error if you ask past it")
        if self.resampled:
            out.append(
                f"Yahoo has no {self.requested_minutes}m bar, so "
                f"{self.fetch_minutes}m bars are fetched and resampled")
        return out

    def to_dict(self) -> dict:
        d = {k: getattr(self, k) for k in
             ("symbol", "ticker", "requested_minutes", "fetch_minutes", "interval",
              "requested_days", "granted_days", "resampled", "clamped")}
        d["start"] = self.start.isoformat()
        d["end"] = self.end.isoformat()
        d["notes"] = self.notes
        return d


def plan_request(symbol: str, minutes: int, days: float, *,
                 now: Optional[datetime] = None) -> RequestPlan:
    """Work out the vendor request for a desired timeframe and lookback.

    Pure: no network, no clock unless ``now`` is omitted. This is where the
    lookback caps and the missing-interval substitutions are applied, so both
    can be tested exhaustively without touching Yahoo.
    """
    if minutes <= 0:
        raise YahooError(f"timeframe must be positive, got {minutes}")
    if days <= 0:
        raise YahooError(f"lookback must be positive, got {days}")

    fetch_minutes = minutes
    resampled = False
    if minutes not in INTERVALS:
        source = RESAMPLE_FROM.get(minutes)
        if source is None:
            supported = ", ".join(f"{m}m" for m in sorted(INTERVALS))
            derivable = ", ".join(f"{m}m" for m in sorted(RESAMPLE_FROM))
            raise YahooError(
                f"Yahoo has no {minutes}m bar and no rule for deriving one. "
                f"Served directly: {supported}. Derived by resampling: {derivable}.")
        fetch_minutes = source
        resampled = True

    interval, cap = INTERVALS[fetch_minutes]
    wanted = timedelta(days=float(days))
    granted = min(wanted, cap)
    end = to_et(now or now_et())
    return RequestPlan(
        symbol=symbol.upper().strip(),
        ticker=ticker_for(symbol),
        requested_minutes=minutes,
        fetch_minutes=fetch_minutes,
        interval=interval,
        requested_days=wanted.total_seconds() / 86400.0,
        granted_days=granted.total_seconds() / 86400.0,
        start=end - granted,
        end=end,
        resampled=resampled,
        clamped=granted < wanted,
    )


# --------------------------------------------------------------------------
# Result
# --------------------------------------------------------------------------

@dataclass
class FetchResult:
    """Bars, plus an honest account of what was discarded on the way.

    The counters are not diagnostics for a developer - they are the difference
    between "this symbol is quiet" and "this feed is broken", and the caller
    cannot tell those apart from the bar list alone.
    """

    series: BarSeries
    plan: RequestPlan
    rows_returned: int = 0
    bars_kept: int = 0
    dropped_forming: int = 0
    dropped_no_price: int = 0
    repaired_ohlc: int = 0
    bars_missing_volume: int = 0
    warnings: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return self.bars_kept == 0

    def summary(self) -> str:
        bits = [f"{self.plan.ticker} {self.plan.interval}",
                f"{self.bars_kept} bars"]
        if self.dropped_forming:
            bits.append(f"-{self.dropped_forming} forming")
        if self.dropped_no_price:
            bits.append(f"-{self.dropped_no_price} no-price")
        if self.repaired_ohlc:
            bits.append(f"{self.repaired_ohlc} OHLC repaired")
        if self.bars_missing_volume:
            bits.append(f"{self.bars_missing_volume} missing volume")
        return ", ".join(bits)

    def to_dict(self) -> dict:
        return {
            "plan": self.plan.to_dict(),
            "rows_returned": self.rows_returned,
            "bars_kept": self.bars_kept,
            "dropped_forming": self.dropped_forming,
            "dropped_no_price": self.dropped_no_price,
            "repaired_ohlc": self.repaired_ohlc,
            "bars_missing_volume": self.bars_missing_volume,
            "warnings": list(self.warnings),
        }


# --------------------------------------------------------------------------
# The feed
# --------------------------------------------------------------------------

def _import_yfinance():
    try:
        import yfinance                                     # noqa: F401
    except ImportError as exc:                              # pragma: no cover
        raise YahooError(
            "yfinance is not installed. This is an optional dependency - the "
            "deterministic core does not need it. Install with:\n"
            "    pip install yfinance"
        ) from exc
    return yfinance


class YahooFeed:
    """Fetches bars from Yahoo Finance and converts them to this repo's ``Bar``.

    ``row_source`` exists so the conversion can be tested without a network: it
    is any callable returning an iterable of
    ``(timestamp, open, high, low, close, volume)`` tuples. The default calls
    ``yfinance``. Everything downstream of the call - the forming-bar drop, the
    timezone conversion, the OHLC repair - is identical either way, which is the
    point: the fragile part is tested, not mocked past.
    """

    def __init__(self, *, prepost: bool = False,
                 keep_forming_bar: bool = False,
                 row_source: Optional[Any] = None):
        self.prepost = prepost
        self.keep_forming_bar = keep_forming_bar
        self._row_source = row_source

    # ---- the network call ---------------------------------------------
    def _rows(self, plan: RequestPlan) -> List[Tuple[Any, ...]]:
        if self._row_source is not None:
            return list(self._row_source(plan))
        yfinance = _import_yfinance()
        frame = yfinance.Ticker(plan.ticker).history(
            start=plan.start,
            end=plan.end,
            interval=plan.interval,
            auto_adjust=False,
            prepost=self.prepost,
            raise_errors=False,
        )
        if frame is None or frame.empty:
            return []
        return [
            (idx, row.get("Open"), row.get("High"), row.get("Low"),
             row.get("Close"), row.get("Volume"))
            for idx, row in frame.iterrows()
        ]

    @staticmethod
    def _transport_hint(plan: "RequestPlan", exc: Exception) -> str:
        """Turn a transport failure into something the reader can act on."""
        text = f"{type(exc).__name__}: {exc}"
        lines = [f"could not reach Yahoo for {plan.ticker}: {text}"]
        low = text.lower()
        if "403" in low and "connect" in low:
            lines.append(
                "The CONNECT tunnel was refused with 403, which is an egress "
                "policy denying the host - not a Yahoo error and not a bug in "
                "this code. Allow query1.finance.yahoo.com and "
                "query2.finance.yahoo.com, or widen the network access level, "
                "then retry.")
        elif "resolve" in low or "name or service" in low or "dns" in low:
            lines.append("DNS could not resolve the host - check network access.")
        elif "timed out" in low or "timeout" in low:
            lines.append("The request timed out. Yahoo rate-limits; retry shortly.")
        lines.append(
            "Nothing was written to the archive, so no history was affected.")
        return " ".join(lines)

    # ---- conversion ----------------------------------------------------
    def fetch(self, symbol: str, minutes: int = 60, days: float = 30.0, *,
              now: Optional[datetime] = None) -> FetchResult:
        """Fetch ``symbol`` at ``minutes`` resolution over ``days`` of history."""
        plan = plan_request(symbol, minutes, days, now=now)
        clock = to_et(now or now_et())
        try:
            rows = self._rows(plan)
        except YahooError:
            raise
        except Exception as exc:
            # `raise_errors=False` suppresses the vendor's own error responses
            # but not a transport failure underneath the HTTP client - a refused
            # proxy, no DNS, no route. Those surface as a stack trace from three
            # libraries down, which tells the reader nothing they can act on.
            #
            # Wrapping here rather than inside `_rows` means an injected
            # `row_source` travels the identical path, so the tests exercise
            # this handling instead of stepping around it.
            raise YahooError(self._transport_hint(plan, exc)) from exc

        result = FetchResult(series=BarSeries(plan.symbol, plan.fetch_minutes),
                             plan=plan, rows_returned=len(rows))
        result.warnings.extend(plan.notes)

        bars: List[Bar] = []
        for stamp, o, h, l, c, v in rows:
            ts = self._to_et(stamp)
            # A bar whose close time is in the future is still forming: its
            # high, low and close can all still move.
            close_time = ts + timedelta(minutes=plan.fetch_minutes)
            if close_time > clock and not self.keep_forming_bar:
                result.dropped_forming += 1
                continue

            prices = [self._number(x) for x in (o, h, l, c)]
            if any(p is None for p in prices):
                # Thin overnight bars arrive with NaN prices. Zeroing them would
                # put a 0.0 low into a range calculation and corrupt every
                # indicator downstream.
                result.dropped_no_price += 1
                continue
            op, hi, lo, cl = prices                       # type: ignore[misc]

            volume = self._number(v)
            if volume is None:
                result.bars_missing_volume += 1
                volume = 0.0

            # Float noise in the vendor's own aggregation occasionally puts the
            # open or close a hair outside the high/low. Widen the range to
            # contain them rather than discarding an otherwise good bar;
            # Bar.validate would reject it, and silently dropping real bars is
            # worse than a sub-tick adjustment.
            fixed_hi = max(hi, op, cl)
            fixed_lo = min(lo, op, cl)
            if fixed_hi != hi or fixed_lo != lo:
                result.repaired_ohlc += 1
                hi, lo = fixed_hi, fixed_lo

            bar = Bar(ts=ts, open=op, high=hi, low=lo, close=cl,
                      volume=max(0.0, volume), minutes=plan.fetch_minutes,
                      complete=True)
            bar.validate()
            bars.append(bar)

        bars.sort(key=lambda b: b.ts)
        series = BarSeries(plan.symbol, plan.fetch_minutes, bars)

        if plan.resampled and len(series):
            # keep_partial=False: a resampled bucket that is not yet full is the
            # same lookahead problem as the vendor's forming bar.
            series = series.resample(plan.requested_minutes, keep_partial=False)

        result.series = series
        result.bars_kept = len(series)

        if result.rows_returned == 0:
            result.warnings.append(
                f"Yahoo returned no rows for {plan.ticker} at {plan.interval}. "
                "This vendor reports an out-of-range request as an empty frame, "
                "not an error - check the ticker suffix and the lookback cap "
                "before assuming the market is closed.")
        if result.bars_missing_volume:
            result.warnings.append(
                f"{result.bars_missing_volume} bar(s) had no volume and are "
                "recorded as 0.0. They have a real price range, so any filter "
                "reading volume as liquidity should test `volume > 0` rather "
                "than trusting the field.")
        return result

    # ---- helpers -------------------------------------------------------
    @staticmethod
    def _to_et(stamp: Any) -> datetime:
        """Convert a vendor timestamp to Eastern, refusing a naive one.

        Yahoo returns exchange-local, timezone-aware stamps. A naive value means
        something upstream has already stripped the zone, and assuming UTC at
        that point shifts every session boundary by four or five hours - the
        kind of bug that produces plausible-looking garbage for weeks.
        """
        dt = stamp.to_pydatetime() if hasattr(stamp, "to_pydatetime") else stamp
        if not isinstance(dt, datetime):
            raise YahooError(f"expected a datetime index, got {type(dt).__name__}")
        if dt.tzinfo is None:
            raise YahooError(
                f"naive timestamp {dt!r} from the feed. Yahoo returns "
                "timezone-aware stamps; a naive one means the zone was dropped "
                "upstream, and guessing it would shift every session boundary.")
        return dt.astimezone(ET)

    @staticmethod
    def _number(value: Any) -> Optional[float]:
        """Float, or ``None`` for NaN/missing - never a silent zero."""
        if value is None:
            return None
        try:
            out = float(value)
        except (TypeError, ValueError):
            return None
        if math.isnan(out) or math.isinf(out):
            return None
        return out


# --------------------------------------------------------------------------
# Provider adapter
# --------------------------------------------------------------------------

class YahooProvider(DataProvider):
    """Serves the existing :class:`DataProvider` interface from Yahoo.

    Fetches once per symbol and caches, because the orchestrator asks for the
    same series repeatedly within a cycle and this vendor is rate-limited.
    Call :meth:`refresh` to go back to the network.
    """

    def __init__(self, symbols: Sequence[str], *, minutes: int = 60,
                 days: float = 60.0, feed: Optional[YahooFeed] = None):
        self._symbols = [s.upper().strip() for s in symbols]
        self.minutes = minutes
        self.days = days
        self.feed = feed or YahooFeed()
        self._cache: Dict[str, BarSeries] = {}
        self._results: Dict[str, FetchResult] = {}

    def symbols(self) -> Sequence[str]:
        return list(self._symbols)

    def base_series(self, symbol: str) -> BarSeries:
        key = symbol.upper().strip()
        if key not in self._cache:
            res = self.feed.fetch(key, minutes=self.minutes, days=self.days)
            self._results[key] = res
            self._cache[key] = res.series
        return self._cache[key]

    def result_for(self, symbol: str) -> Optional[FetchResult]:
        """The fetch report for ``symbol``, including everything discarded."""
        return self._results.get(symbol.upper().strip())

    def refresh(self, symbol: Optional[str] = None) -> None:
        if symbol is None:
            self._cache.clear()
            self._results.clear()
        else:
            key = symbol.upper().strip()
            self._cache.pop(key, None)
            self._results.pop(key, None)
