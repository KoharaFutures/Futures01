#!/usr/bin/env python3
"""Fetch MGC/MNQ bars for the CALL desk, log the feed lag, snapshot only when something moved.

Owned by agent CALL. Exists so every check runs IDENTICAL fetch logic instead of a heredoc
re-typed each time - a per-check transcription risk on the one step the whole record rests on.

TWO THINGS IT GETS RIGHT THAT A TIMESTAMP-ONLY FRESHNESS TEST DOES NOT:

1. STUB REJECTION. A bar with `volume == 0 AND high == low` is the vendor filling a hole with
   the previous close. Measured 2026-09-27: the 18:00 stub's price was wrong by 12.20 points on
   MGC - $122/contract, more than the entire risk budget of the position it would have opened.
   See NOTES.md N5a.

2. THE NEWEST BAR IS USUALLY STILL FORMING, AND ITS VALUES GET REVISED. Keying freshness on the
   timestamp alone means a revision to a bar we already hold is silently dropped. Usually
   self-healing - the next new timestamp rewrites the whole series including the finalised bar -
   but NOT at a session or weekend close, where no successor arrives. A bar frozen mid-formation
   has an incomplete high and low, and `resolve.py` resolves stops and targets against exactly
   those, so a stop touch late in that bar would never be seen. So freshness here is
   "a new timestamp OR any changed OHLCV on a bar we already hold".
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
DATA = HERE / "data"
LAG = HERE / "feed_lag.jsonl"

from futures_agents.data.yahoo import YahooFeed  # noqa: E402

SYMBOLS = ("MGC", "MNQ")
FRAMES = (5, 15)


def is_stub(bar) -> bool:
    return bar.volume == 0 and bar.high == bar.low


def stored(symbol: str, minutes: int) -> dict[str, tuple]:
    have: dict[str, tuple] = {}
    for p in sorted(DATA.glob(f"{symbol}_{minutes}m_fetched_*.jsonl")):
        for line in p.read_text().splitlines():
            if not line.strip():
                continue
            b = json.loads(line)
            have[b["ts"]] = (b["o"], b["h"], b["l"], b["c"], b["v"])
    return have


def main() -> int:
    now = datetime.now(timezone.utc)
    # SECONDS, not minutes. The stamp is the snapshot's filename, so minute granularity
    # means two fetches in the same minute OVERWRITE each other. That was survivable while
    # every snapshot held the full series - any clobbered bar existed in a dozen other files -
    # but a delta is the ONLY copy of the revisions it records, so an in-minute overwrite
    # would silently destroy them. Found by noticing the data directory SHRINK by 188 KB on
    # the run that introduced deltas: a 23:28Z delta had replaced a 23:28Z full series.
    stamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    DATA.mkdir(parents=True, exist_ok=True)
    feed = YahooFeed()
    lag_rows, wrote, failures = [], [], []

    for sym in SYMBOLS:
        for mins in FRAMES:
            try:
                res = feed.fetch(sym, minutes=mins, days=5)
            except Exception as exc:                      # a failed fetch is reported, not hidden
                failures.append(f"{sym} {mins}m: {type(exc).__name__}: {exc}")
                continue
            bars = [b for b in res.series if not is_stub(b)]
            stubs = sum(1 for b in res.series if is_stub(b))
            if not bars:
                failures.append(f"{sym} {mins}m: no real bars ({stubs} stub(s) dropped)")
                continue

            have = stored(sym, mins)
            new_ts = [b for b in bars if b.ts.isoformat() not in have]
            revised = [b for b in bars
                       if b.ts.isoformat() in have
                       and have[b.ts.isoformat()] != (b.open, b.high, b.low, b.close, b.volume)]
            # Write the DELTA, not the series. `resolve.py` and `chart.py` merge every
            # snapshot keyed on timestamp with the latest file winning, so a delta composes
            # to exactly the same series a full rewrite would give - and a full rewrite at
            # this cadence is ruinous. Measured 2026-09-27: 39 full snapshots reached 2.5 MB
            # in 40 minutes, because each one re-emitted ~3,700 bars to record ~3 changed
            # ones. That is ~90 MB/day of PERMANENT git history for a few hundred real bars.
            # A delta is also better evidence: the file records what changed at that fetch,
            # which is precisely how N5a's before/after stub comparison was possible.
            delta = new_ts + revised
            if delta:
                delta.sort(key=lambda b: b.ts)
                (DATA / f"{sym}_{mins}m_fetched_{stamp}.jsonl").write_text("\n".join(
                    json.dumps({"ts": b.ts.isoformat(), "o": b.open, "h": b.high,
                                "l": b.low, "c": b.close, "v": b.volume}) for b in delta) + "\n")
                wrote.append(f"{sym} {mins}m (+{len(new_ts)} new, {len(revised)} revised)")

            newest = bars[-1]
            lag = (now - newest.ts.astimezone(timezone.utc)).total_seconds() / 60.0
            lag_rows.append({"ts": now.replace(microsecond=0).isoformat(), "symbol": sym,
                             "frame": mins, "newest_real_bar": newest.ts.isoformat(),
                             "lag_minutes": round(lag, 1), "stubs_dropped": stubs,
                             "newest_real_close": newest.close,
                             "new_bars": len(new_ts), "revised_bars": len(revised)})
            if mins == 5:
                print(f"{sym} 5m newest {newest.ts.isoformat()}  c={newest.close:.2f} "
                      f"h={newest.high:.2f} l={newest.low:.2f}  lag={lag:.1f}m  "
                      f"new={len(new_ts)} revised={len(revised)}")

    if lag_rows:
        with LAG.open("a") as fh:
            for row in lag_rows:
                fh.write(json.dumps(row) + "\n")

    print(f"snapshots written: {', '.join(wrote) if wrote else 'none (nothing moved)'}")
    for f in failures:
        print(f"FETCH FAILURE  {f}")
    return 1 if failures and not lag_rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
