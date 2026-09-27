"""An append-only bar archive, because this vendor retracts completed bars.

Yahoo's intraday window slides at both ends and not always predictably: a
download taken today can be *missing* bars that yesterday's download contained,
including bars that were complete and carried real volume. A store that
overwrites itself on each fetch therefore loses history it already had, and the
loss is silent - the file simply gets shorter.

:class:`BarArchive` is the fix and it is deliberately unexciting. Every fetch is
reconciled against what is already on disk rather than replacing it:

* a bar the archive has and the download lacks is **kept** and counted as a
  retraction;
* a bar both have, with different values, keeps the version carrying real
  volume, and otherwise the newer one - a completed bar's values should not
  drift, so any disagreement is reported;
* a bar only the download has is appended.

The archive never shrinks. That is the entire guarantee, and it is what makes a
backtest run today reproducible next month.

Storage is one JSON Lines file per symbol and timeframe, sorted by timestamp.
Text, not a binary store, because a dataset you cannot inspect with ``head`` is
a dataset you cannot debug - and because a partial write should cost one line,
not the file.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..timeutil import to_et
from .bars import Bar, BarSeries

__all__ = ["BarArchive", "ReconcileReport"]


@dataclass
class ReconcileReport:
    """What one reconciliation changed, and what the vendor took away."""

    symbol: str
    minutes: int
    had: int = 0                  # bars already on disk
    offered: int = 0              # bars in the incoming download
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    retracted: int = 0            # on disk, absent from the download
    conflicts: List[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.had + self.added

    def summary(self) -> str:
        bits = [f"{self.symbol} {self.minutes}m", f"{self.total} bars"]
        if self.added:
            bits.append(f"+{self.added} new")
        if self.updated:
            bits.append(f"{self.updated} updated")
        if self.retracted:
            bits.append(f"VENDOR RETRACTED {self.retracted} - kept from archive")
        if self.conflicts:
            bits.append(f"{len(self.conflicts)} value conflicts")
        return ", ".join(bits)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol, "minutes": self.minutes,
            "had": self.had, "offered": self.offered, "added": self.added,
            "updated": self.updated, "unchanged": self.unchanged,
            "retracted": self.retracted, "total": self.total,
            "conflicts": list(self.conflicts[:50]),
        }


class BarArchive:
    """An append-only store of bars, one file per symbol and timeframe."""

    def __init__(self, root: str = "data/archive"):
        self.root = Path(root)

    # ---- layout --------------------------------------------------------
    def path_for(self, symbol: str, minutes: int) -> Path:
        return self.root / f"{symbol.upper().strip()}_{minutes}m.jsonl"

    # ---- read ----------------------------------------------------------
    def load(self, symbol: str, minutes: int) -> BarSeries:
        """Every bar on disk for this symbol and timeframe, oldest first."""
        path = self.path_for(symbol, minutes)
        series = BarSeries(symbol.upper().strip(), minutes)
        if not path.is_file():
            return series
        bars: List[Bar] = []
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                bars.append(self._bar_from_json(json.loads(line), minutes))
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                # One corrupt line must not cost the whole history. Skipping it
                # loses a bar; raising loses the archive.
                raise ValueError(
                    f"{path}:{lineno} is not a readable bar ({exc}). The archive "
                    "is append-only and is never rewritten automatically - fix or "
                    "delete this line by hand."
                ) from None
        bars.sort(key=lambda b: b.ts)
        return BarSeries(symbol.upper().strip(), minutes, bars)

    # ---- write ---------------------------------------------------------
    def reconcile(self, incoming: BarSeries, *,
                  symbol: Optional[str] = None,
                  minutes: Optional[int] = None,
                  window: Optional[Tuple[datetime, datetime]] = None
                  ) -> ReconcileReport:
        """Merge a download into the archive without ever losing a bar.

        ``window`` is the period the download claims to cover - normally
        ``(plan.start, plan.end)`` from the request that produced it. It decides
        which archived bars count as *retracted*: a bar inside the window that
        the download did not return is one the vendor has taken back, and one an
        overwriting store would have lost.

        Without it, the download's own first and last stamps are used, which
        detects holes in the middle but **not** bars falling off the front -
        and the front is exactly where Yahoo's sliding window drops history.
        Pass the window whenever you have it; :meth:`reconcile_result` does.
        """
        sym = (symbol or incoming.symbol).upper().strip()
        mins = minutes or incoming.minutes
        existing = self.load(sym, mins)

        by_ts: Dict[datetime, Bar] = {to_et(b.ts): b for b in existing}
        report = ReconcileReport(symbol=sym, minutes=mins, had=len(by_ts),
                                 offered=len(incoming))

        offered_stamps = set()
        for bar in incoming:
            ts = to_et(bar.ts)
            offered_stamps.add(ts)
            current = by_ts.get(ts)
            if current is None:
                by_ts[ts] = bar
                report.added += 1
                continue
            if self._same(current, bar):
                report.unchanged += 1
                continue
            # A completed bar's values should not move. When they do, prefer the
            # version that carries real volume - the vendor's zero-volume
            # re-issues are the usual cause, and they are the less informative
            # of the two.
            keep = current if (current.volume > 0 and bar.volume <= 0) else bar
            if keep is not current:
                by_ts[ts] = keep
                report.updated += 1
            else:
                report.unchanged += 1
            report.conflicts.append(
                f"{ts.isoformat()} archive=({current.open},{current.high},"
                f"{current.low},{current.close},v{current.volume:g}) "
                f"download=({bar.open},{bar.high},{bar.low},{bar.close},"
                f"v{bar.volume:g}) -> kept "
                f"{'archive' if keep is current else 'download'}")

        # A bar the archive holds inside the covered window, which the download
        # did not return, is a bar the vendor has retracted - and one an
        # overwriting store would now have lost.
        if window is not None:
            lo, hi = to_et(window[0]), to_et(window[1])
        elif offered_stamps:
            lo, hi = min(offered_stamps), max(offered_stamps)
        else:
            lo = hi = None
        if lo is not None:
            report.retracted = sum(
                1 for ts in by_ts
                if lo <= ts <= hi and ts not in offered_stamps)

        merged = [by_ts[ts] for ts in sorted(by_ts)]
        self._write(sym, mins, merged)
        report.had = len(existing)
        return report

    def reconcile_result(self, result) -> ReconcileReport:
        """Reconcile a :class:`~futures_agents.data.yahoo.FetchResult`.

        Preferred over :meth:`reconcile` for vendor downloads, because the fetch
        plan knows the window that was actually requested and so can tell a
        retraction from a bar that was simply never asked for.
        """
        return self.reconcile(
            result.series,
            symbol=result.plan.symbol,
            minutes=result.plan.requested_minutes,
            window=(result.plan.start, result.plan.end),
        )

    # ---- internals -----------------------------------------------------
    def _write(self, symbol: str, minutes: int, bars: Sequence[Bar]) -> None:
        path = self.path_for(symbol, minutes)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = "".join(json.dumps(self._bar_to_json(b)) + "\n" for b in bars)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name,
                                   suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    @staticmethod
    def _bar_to_json(bar: Bar) -> dict:
        return {"ts": to_et(bar.ts).isoformat(), "o": bar.open, "h": bar.high,
                "l": bar.low, "c": bar.close, "v": bar.volume}

    @staticmethod
    def _bar_from_json(d: dict, minutes: int) -> Bar:
        return Bar(ts=to_et(datetime.fromisoformat(d["ts"])),
                   open=float(d["o"]), high=float(d["h"]), low=float(d["l"]),
                   close=float(d["c"]), volume=float(d.get("v", 0.0) or 0.0),
                   minutes=minutes, complete=True)

    @staticmethod
    def _same(a: Bar, b: Bar) -> bool:
        return (a.open == b.open and a.high == b.high and a.low == b.low
                and a.close == b.close and a.volume == b.volume)
