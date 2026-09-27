# EF1 burst 04 — the fix had a second hole. Saturation found it; so did EF3, independently.

## The measurement that mattered, and why my first one had no power over it

My post-fix three-arm run came back **0 violations on all four symbols** and I was one write away
from calling the harness trustworthy. EF3 then reported **43 `SPANS_WINDOW` violations and a 71-hour
hold** on the same engine `[msgs/EF3-01_EF1_session-rule-misses-early-close-sessions.md]`, audited
with **my own `violations()`**. Both runs were correct. The difference was the population:

- mine: the generated default, `rth_only=True` on 184–190 strategies per symbol;
- EF3's: 400 MES strategies with `rth_only=False`.

`rth_only=False` lets a signal fire overnight, so EF3's population held positions through sessions
mine never entered in. **Coverage is a property of the signals, not of the engine.** Two agents
auditing the same code through different populations get different answers and neither can tell
whose engine is wrong. That is a methodological finding independent of this defect, and it is the
reason `EF1-H5` exists.

## EF1-H5 — the saturation test

`code/saturate.py`. One stub signals on **every** bar, with the stop 50% away and the target 500R
beyond it, so a position is open on every bar the series contains and the **only** thing that can
ever close one is the session rule. Run long and short, on every symbol and timeframe.

It found the remaining hole on its **first run, at the first offending bar**, and the strict
emission check named the trade rather than adding to a count:

```
SessionWindowViolation: MES: the engine was about to emit a trade that breaks the session window:
  [{'kind': 'SPANS_WINDOW', 'strategy_id': 'ef1-saturate',
    'entry_ts': '2024-11-27T18:00:00-05:00', 'exit_ts': '2024-11-29T12:30:00-05:00'}]
  reason=SESSION_CLOSE bar_class=OUTSIDE
```

## EF1-D4 — my fix keyed on the ET calendar date and caught 10 of 19

Thanksgiving-eve entry at 18:00, exit Black Friday 12:30 — **66 hours across two 16:00 deadlines.**

`[measured: 2024-11-28 has zero bars in data/archive/MES_60m.jsonl]`

An ET-calendar-date map cannot have an entry for a date that does not exist. My map found 10 dates
per symbol; EF3's trading-day walk found 19, and mine was a strict subset. The nine it missed are
exactly the **full** holidays — Thanksgiving, MLK, Presidents' Day, Good Friday, Juneteenth — where
the archive carries no bars at all for the date, only the previous evening's 18:00–23:00 session.

**Fix:** key on the **CME trading day**, which rolls at 18:00 ET — the repo's own `trading_day`
(`futures_agents/timeutil.py`), and the same boundary the whole rule is built on. Thanksgiving-eve's
evening bars then belong to Thanksgiving's trading day, and the flat lands on the last of them.
Within a trading day that has no deadline bar, **every** bar precedes that day's 16:00 (a bar at or
after 16:00 and before 18:00 would classify `IN_WINDOW`; a bar at 18:00 belongs to the next trading
day), so the forced flat is simply the day's **last** bar — no further filter, and no place for an
off-by-one to hide.

Reproduces EF3's 19 dates exactly, on both MES and MNQ
`[measured: set(session_end_indices(archive 60m).values()) == EF3's list]`:

```
2024-11-28 2024-11-29 2024-12-24 2025-01-09 2025-01-20 2025-02-17 2025-05-26 2025-06-19
2025-07-03 2025-07-04 2025-11-27 2025-11-28 2025-12-24 2026-01-19 2026-01-30 2026-02-16
2026-04-03 2026-06-19 2026-07-03
```

MGC 17 at 60m, 9 at 240m; MCL 27, because of EF1-F8's two-month vendor hole.

Regression: `test_holiday_with_no_bars_at_all_still_flattens_the_evening_before`.

## A third thing the trading-day key exposed: the series' last trading day

Keying on `trading_day` made the **final** trading day of any series get flagged, because it is
truncated by the end of the data. That would close the final open position as a flat the rule never
reached, and — worse — the flag would move with every prefix length, turning an artefact of where
the data stops into an apparent look-ahead. The final trading day is therefore excluded, and a
position still open at the end is closed as `END_OF_DATA`, which is what it is.

The same change caught a bug in my **own prefix report**: it classified mismatches against the ET
calendar date while the map keys on the trading day, which reported **18 spurious off-cut
mismatches** — every bar stamped 18:00–23:59, whose trading day is the next date. The two
vocabularies have to match.

## Post-fix saturation, all four symbols, five timeframes, both directions

`[measured: python3 code/saturate.py --symbols MGC,MCL,MES,MNQ --tfs 5,15,30,60,240]`

```
MGC    5m  trades=  41 viol=0 (strict 0) 1b= 0 maxhold=1315m/cap1315 over=0 | control viol=2 maxhold=  83,370m
MGC   15m  trades=  41 viol=0 (strict 0) 1b= 0 maxhold=1305m/cap1305 over=0 | control viol=2 maxhold=  83,355m
MGC   30m  trades=  41 viol=0 (strict 0) 1b= 0 maxhold=1290m/cap1290 over=0 | control viol=2 maxhold=  83,340m
MGC   60m  trades= 506 viol=0 (strict 0) 1b=17 maxhold=1260m/cap1260 over=0 | control viol=2 maxhold=1,035,120m
MGC  240m  trades= 506 viol=0 (strict 0) 1b= 9 maxhold= 960m/cap1080 over=0 | control viol=1 maxhold=1,034,880m
MES   60m  trades= 507 viol=0 (strict 0) 1b=19 maxhold=1260m/cap1260 over=0 | control viol=2 maxhold=1,035,120m
```

Three things to read off it:

1. **`viol=0` under the *strict* audit with no carve-out**, on every cell. Not the exempted audit —
   the one usable on any engine's trades.
2. **`maxhold` sits exactly on the cap** at 5m/15m/30m/60m: 22h minus one base bar, because trade
   stamps are bar *open* times. `over=0` everywhere. At 240m it is 960m (16h) rather than 1080m,
   which is the grid: the flat lands on the `[12:00,16:00)` bucket, the `[16:00,20:00)` bucket is
   `IN_WINDOW` and vetoed, so the earliest re-entry is 20:00 → 12:00, 16 hours.
3. **The control has power.** The same stub through the shipped `BacktestEngine` holds one position
   for **1,035,120 minutes = 719 days** and violates. A saturation test whose control came back
   clean would prove nothing.

`trades = 506/507` at 60m and 240m is one trade per session over 718 days, which is the rule doing
exactly what it says: one 18:00→16:00 cycle, every cycle, for the whole span.
