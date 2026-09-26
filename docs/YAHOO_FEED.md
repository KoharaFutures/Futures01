# The Yahoo feed

`futures_agents/data/yahoo.py` — a real data feed for this repository. No API
key, no account. `yfinance` is an optional dependency:

```bash
pip install yfinance
python -m futures_agents.cli fetch --symbols MCL,MGC --timeframe 60 --days 60
```

## It needs network access to Yahoo

The feed is blocked in this container: `query1.finance.yahoo.com` is refused at
the egress proxy with a 403 on the CONNECT tunnel. That is an environment
setting, not a property of the code — `yfinance` installs and imports fine here,
and every line below is exercised by tests.

To allow it: the cloud environment menu in the session title bar → **Edit** →
**Network access**. Either raise the access level or add
`query1.finance.yahoo.com` and `query2.finance.yahoo.com` to the allowed
domains. Levels are described at
<https://code.claude.com/docs/en/claude-code-on-the-web>.

Run `--plan-only` to see exactly what would be requested without touching the
network.

## The six things that make a Yahoo reader return nothing

Each is a real failure mode and each has a test. The common thread is that this
vendor fails **silently** — it returns an empty frame or a subtly wrong bar
rather than an error, so the damage shows up weeks later.

**1. Futures need the `=F` suffix.** `MNQ` is not a Yahoo symbol; `MNQ=F` is.
The bare root returns an empty frame, not an error. And `MNQ=F` is not
TradingView's `MNQ1!` — different vendor, different roll convention, so the two
are not interchangeable in a backtest.

**2. Every interval has a hard lookback cap.**

| bars | interval | history |
|---|---|---|
| 1m | `1m` | **7 days** |
| 2m / 5m / 15m / 30m / 90m | `2m`…`90m` | ~60 days |
| 60m | `1h` | ~730 days |
| 1d | `1d` | decades |

Ask for 1-minute bars from eight days ago and you get nothing back, with no
complaint. `plan_request()` clamps the window and *reports* the clamp — a caller
asking for 90 days of 1m data has a misconception worth correcting, not a
request worth quietly truncating. The caps here sit one day inside Yahoo's
published limits, because the limit is enforced against the vendor's clock and a
request sitting exactly on the boundary flakes.

**3. There is no 3m and no 4h bar.** This matters here specifically: MCL's
measured framework is 60m **and 240m**, and Yahoo cannot serve 240m. The feed
fetches 1h and resamples, and says so. `RESAMPLE_FROM` holds the rules;
requesting something underivable names what *is* available rather than returning
empty.

**4. The last row is the forming bar.** Its high, low and close are not final.
Feeding it to a strategy is lookahead bias, and it is the single most common way
a backtest flatters itself. Dropped unless `keep_forming_bar=True`.

**5. Timestamps are exchange-local and timezone-aware.** This codebase stores
bar times in **Eastern** (see `Bar.ts`), so they are converted explicitly. A
naive timestamp is *refused* rather than assumed to be UTC — guessing shifts
every session boundary by four or five hours, which produces plausible-looking
garbage for weeks.

**6. Missing volume arrives as NaN.** `float(row.get("Volume") or 0.0)` turns it
into `0.0`, giving you bars with a real price range and no volume, which
silently breaks any filter reading volume as liquidity. Here, rows with no
*price* are dropped; rows with no *volume* are kept, counted in
`FetchResult.bars_missing_volume`, and warned about. **Filter on `volume > 0`
rather than trusting the field.**

Two smaller ones: NaN prices on thin overnight bars are dropped rather than
zeroed (a `0.0` low corrupts every range calculation downstream), and float
noise that puts the open or close a hair outside the high/low is repaired rather
than discarded — `Bar.validate()` would reject the bar, and silently dropping
real bars is worse than a sub-tick adjustment.

## Vendor retraction — why the archive exists

**This vendor takes bars back.** Its intraday window slides at both ends, so a
download taken today can be *missing* completed bars that yesterday's download
contained. A store that overwrites itself on each fetch loses that history, and
the loss is silent: the file just gets shorter.

`futures_agents/data/archive.py` is an append-only store that reconciles each
download against what is already on disk:

- a bar the archive has and the download lacks is **kept** and counted as a
  retraction;
- a bar both have that disagree keeps the version with real volume (a
  zero-volume re-issue is the usual cause and the less informative one), and the
  disagreement is reported;
- a bar only the download has is appended.

**The archive never shrinks.** That is the whole guarantee, and it is what makes
a backtest run today reproducible next month.

```
DAY 1 archive: MCL 60m, 30 bars, +30 new
DAY 2 archive: MCL 60m, 34 bars, +4 new, VENDOR RETRACTED 8 - kept from archive
```

### Pass the window

Use `archive.reconcile_result(fetch_result)` rather than `reconcile(series)`.
The fetch plan knows the window that was *requested*, which is what separates a
retraction from a bar that was simply never asked for.

Without it, the download's own first and last stamps are used — which finds
holes in the middle but **not bars falling off the front**, and the front is
exactly where a sliding window drops history. `reconcile_result` always passes
the window. There is a test named after this distinction.

## Storage

One JSON Lines file per symbol and timeframe, `data/archive/MCL_60m.jsonl`,
sorted by timestamp, written via a temp file and one atomic rename. Text rather
than a binary store, because a dataset you cannot inspect with `head` is a
dataset you cannot debug, and because a partial write should cost one line
rather than the file.

A corrupt line raises and names the file and line number. The archive is never
rewritten automatically — silently skipping a bad line loses a bar, and
rewriting loses the history.
