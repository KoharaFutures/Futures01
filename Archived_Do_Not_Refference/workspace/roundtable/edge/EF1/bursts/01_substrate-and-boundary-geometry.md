# EF1 burst 01 — verifying the brief's three premises, and measuring where 16:00 ET actually falls

Written before any code. Everything below is measured on `data/archive/` (the programme substrate).

## 1. The three premises in my dispatch — all three verified, one with a correction

**(a) `exit_at_session_close` fires at the contract's own RTH close, not 16:00.**
`[repo-verified: futures_agents/backtest/engine.py:470-473]`

```python
if exit_model.exit_at_session_close and not self.allow_overnight:
    elapsed = minutes_since_open(bar.ts, spec.rth_open) + bar.minutes
    if elapsed >= self._rth_minutes:
        return self._close(pos, i, bar, bar.close, ExitReason.SESSION_CLOSE)
```

`_rth_minutes` is `rth_close − rth_open` in minutes (`engine.py:244-247`), so `elapsed >=
_rth_minutes` is reached exactly at `rth_close`:

| symbol | `rth_open` | `rth_close` | session minutes |
|---|---|---|---|
| MGC | 08:20 | **13:30** | 310 |
| MCL | 09:00 | **14:30** | 330 |
| MES | 09:30 | 16:00 | 390 |
| MNQ | 09:30 | 16:00 | 390 |

`[measured: python -c over futures_agents.config.CONTRACTS → the table above]`

So the shipped session exit is 2h30m early on MGC and 1h30m early on MCL. On MES/MNQ it
*coincidentally* lands on 16:00 — which is a trap, not a solution: it is RTH-relative, so it
would move if anyone edited `rth_close`, and it is still gated off by `allow_overnight`.

**(b) It is gated on `not self.allow_overnight`** — so enabling overnight *removes* the rule.
Verified in the snippet above.

**(c) `allow_overnight=True` has no call site.**
`[measured: grep -rn "allow_overnight" --include="*.py" . → engine.py:233 (default False),
engine.py:241 (assignment), engine.py:470 (the gate). Three hits, no other file in the tree.]`

Confirms the EDGE_BRIEF: the overnight-hold regime has never been run here.

## 2. Where 16:00 ET falls relative to the bar grid — the thing that decides the fill

`Bar.ts` is the bar **OPEN** time `[repo-verified: futures_agents/data/bars.py:38]` and duration
is `Bar.minutes`, so a bar covers `[ts, ts + minutes)`. I classified every archive bar by ET
wall-clock minute-of-day (`tod`), against 960 (16:00) and 1080 (18:00):

- `tod < 960 and tod+minutes == 960` → **ON_BOUNDARY**: the bar's close is the 16:00 print.
- `tod < 960 < tod+minutes` → **INTERIOR**: 16:00 falls strictly inside the bar. The bar's close
  is a *post-16:00* price, so using it is look-ahead across the deadline.
- `960 <= tod < 1080` → **IN_WINDOW**: the bar itself lives in the forbidden window.

`[measured: python over data/archive/*.jsonl → ]`

| timeframe | ON_BOUNDARY bars | INTERIOR bars | IN_WINDOW bars | verdict |
|---|---|---|---|---|
| 5m | 41 per symbol | **0** | 493–495 | expressible |
| 15m | 41 | **0** | 165–167 | expressible |
| 30m | 41 | **0** | 83–85 | expressible |
| 60m | 470–489 | **0** | 474–497 | expressible |
| 240m | 491–497 | **0** | 563–586 | expressible |
| **1440m** | **0** | **4008 (MGC) / 1863 (MES,MNQ) / 1 (MCL)** | 0 | **NOT expressible** |

### 1440m is not expressible, and this is a hard finding for EF2–EF5

`align_bucket` puts a daily bucket at 18:00 ET the previous evening
`[repo-verified: futures_agents/data/bars.py:139-143]`, so **every** daily bar spans
`[18:00, 18:00)` and 16:00 ET falls 22 hours into it. The entry fill and the 16:00 flat land
inside the *same* bar, and nothing in OHLC tells you the price at hour 22. A daily-bar strategy
cannot be honestly evaluated under this rule at all. `EF1_FLAT` raises on such a grid rather than
inventing a price.

### The 60m grid is not uniformly on the hour

`[measured: 20 of ~11,000 60m bars per symbol are stamped :30]` — all four symbols, identical
dates, all half-day holiday sessions (2024-11-29 Black Friday, 2024-12-24 Christmas Eve, …),
Yahoo stamping the shortened session on a :30 grid, all between 09:30 and 12:30. None of them
touches 16:00, so INTERIOR is 0 at 60m — **but only by luck**. The rule must classify per bar and
never assume the grid, which is why `classify_bar` exists instead of a modular-arithmetic
shortcut.

## 3. The gap at the flat is real, not hypothetical — one instance justifies the whole branch

I looked for sessions with an IN_WINDOW bar but no bar ending at/through 16:00 (a hole straddling
the deadline). At 60m there is exactly one across all four symbols: **MCL, 2026-03-06.**

`[measured: python over data/archive/MCL_60m.jsonl →]`

```
13:00  o=91.15  c=91.28  v=198,258
16:00  o=90.90  c=90.90  v=0            <- 14:00 and 15:00 bars do not exist
```

A position open into that hole has no bar closing at 16:00. Closing it at `bar.close` of the last
bar before (91.28) **pretends the 38-cent gap did not happen** — $38 a contract on MCL, and on a
1.0-point (=100-tick) stop that is a third of an R invented out of nothing. The gap-honest fill is
the 16:00 bar's **open**, 90.90, plus adverse slippage. That is the `LATE` branch, and it exists
because of this bar.

At 240m the same shape appears 91–96 times per symbol, and every one is a **Sunday**: the
`[16:00, 20:00)` bucket exists because Globex reopens at 18:00, while no `[12:00, 16:00)` bucket
exists because Friday's session ended. No position can be open across it (Friday's was flattened
at Friday 16:00), so it costs nothing on the exit side — but it does mean the 240m veto blocks a
Sunday-18:00 entry whose bucket is stamped 16:00. Reported as a cost of the 240m grid, not hidden.

## 4. DST

`data/archive/` stamps carry explicit UTC offsets that switch at the 2024-11-03 / 2025-03-09 /
2025-11-02 / 2026-03-08 transitions. Every DST transition in the span happens at 02:00 ET on a
Sunday, so none of them lands near 16:00 — but the *offset* does change, which is precisely why
the rule compares **ET wall-clock minute-of-day** (via `to_et`, which uses
`ZoneInfo("America/New_York")`, `futures_agents/timeutil.py:20`) and never a UTC offset or a
`timedelta` across the boundary. Adding a `timedelta` to a zoneinfo-aware datetime does wall-clock
arithmetic without re-normalising the offset, so `end_ts` is computed as `tod + minutes` in
integer ET minutes instead. Test `test_dst_boundary_*` asserts the same ET time-of-day maps to
different UTC hours either side of 2024-11-03 and that the rule fires identically on both.
