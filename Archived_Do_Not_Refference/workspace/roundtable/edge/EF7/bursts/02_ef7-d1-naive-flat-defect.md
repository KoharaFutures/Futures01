# EF7 burst 02 — EF7-D1: the flat that reads correctly and exits inside the window

Written before the fix was coded, so the order is auditable.

## The rule a careful author writes

The shipped engine's own idiom for a session exit is *"has this bar's end passed the deadline"*
(`futures_agents/backtest/engine.py:471-472`). Transposed to 16:00 ET, and keying the cycle off
`trading_day` — which is how the rest of this repo keys a CME session
(`futures_agents/timeutil.py:169-180`) — it is two lines:

```python
deadline = datetime.combine(trading_day(bar.ts), time(16, 0), tzinfo=ET)
if to_et(bar.end_ts) >= deadline:
    close(bar.close)
```

It is correct on **489 of 506** MGC 60m cycles.

## Where it is not

`[measured: scratchpad/probe2.py over data/archive/*_60m.jsonl]`

| 60m | cycles | last bar ends 16:00 | **ends earlier** | the earlier ends |
|---|---|---|---|---|
| MGC | 506 | 489 | **17** (3.4%) | 00:00 ×8, 13:30 ×5, 15:00 ×2, 13:00, 11:00 |
| MCL | 505 | 470 | **35** (6.9%) | 14:00 ×13, 00:00 ×7, 13:30 ×5, 06:00 ×3, 15:00 ×2, 04:00 ×2, 11:00 ×2, 13:00 |
| MES | 507 | 488 | **19** (3.7%) | 00:00 ×9, 13:30 ×5, 13:00 ×3, 10:00, 11:00 |
| MNQ | 507 | 488 | **19** (3.7%) | 00:00 ×9, 13:30 ×5, 13:00 ×3, 10:00, 11:00 |

On one of those cycles **no bar satisfies `end_ts >= 16:00`** until a bar that *opens* at 16:00 or
later. So the naive rule fires on the 16:00–17:00 bar and the position exits at **17:00 ET, inside
the forbidden window**; where the 16:00 bar is also absent it fires on the 18:00 bar, having held
straight across the break. `trading_day` returns the same date for a 16:30 bar as for the 15:30 bar
before it, which is exactly what lets the forbidden bar be treated as part of the cycle it
terminates.

Note the shape of the failure: a minority of cycles, no exception, no log line, and the effect is a
position held *longer* than the rule allows — which on a trending cycle reads as a slightly better
number. This is the fifth member of the family this session keeps finding (D38, D42, D44, D48,
`BarSeries.append`): silent, and with a signature indistinguishable from a result.

## The fix, and the look-ahead it has to discharge

Flat at bar *i* when `cycle_key(bars[i+1].ts) != cycle_key(bars[i].ts)`, where `cycle_key` returns
`None` inside the forbidden window instead of gluing it to the preceding cycle. This reads the
**successor bar's timestamp**. Three checks, not assertions:

1. `test_h2_flat_decision_reads_the_successor_timestamp_and_no_successor_price` replaces every
   OHLCV field of every bar after index 5 with `9e4` and asserts the flags are unchanged.
2. `test_h2_prefix_invariance_on_real_bars` — for every *k*, the flags on `bars[:k]` agree with the
   flags on the whole series at every index where both are determined, on all four symbols,
   ~11,000 bars each.
3. `SessionWindowEngine.run_many` records `_stop_at`, so a run with `end=k` cannot read `bars[k]`;
   `test_h3_end_argument_does_not_leak_past_the_run_window` compares it against a physically
   truncated frame.

`flat_flags` returns **`None`, not `False`**, for the last bar of the run window. Whether the last
bar ends a cycle is genuinely unknowable without a successor, and answering `False` is what would
make the prefix statement false at the boundary — the engine already closes that position
`END_OF_DATA` (`engine.py:475-476`).

## The residual, stated rather than hidden

On those 17/35/19/19 cycles the flat fires **early** — 13:00 or 00:00 instead of 16:00. That is a
deviation caused by the data, not by the rule: there is no printed price at 16:00 to fill against.
Counted separately as `WindowStats.flat_before_deadline` so it never enters the headline flat count
silently.
