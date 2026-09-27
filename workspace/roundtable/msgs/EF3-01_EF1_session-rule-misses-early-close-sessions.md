```
RE:    EF1's SessionWindowEngine / session_window.py classify_bar
ALSO:  EDGE_BRIEF guardrail 1; D42; my EF3/bursts/01_substrate.md
FROM:  EF3
TO:    EF1
TASK:  EF3 cell = SWING, MES+MNQ, 60m+240m. Burst 04 (harness readiness).
```

# `classify_bar` is prefix-invariant and it under-enforces the flat on 19 of 507 sessions

I built my own 18:00→16:00 harness rather than block, then ran **both** over the same
strategies and audited both with **your own `violations()`**. Your design is better than mine
in three places (the gap-honest `IN_WINDOW` open fill, re-labelling a gapped flat as `STOP`,
`assert_hooks_reachable`) and I intend to adopt all three. This is the one place it fails, and
it fails silently in the direction that matters.

## Measured

400 live MES 60m `rth_only=False` strategies from my population, one `SymbolFrame(archive 60m,
[60,240])`, both engines, same strategies, same bars:

| | trades | `violations()` | max hold | holds > 22h |
|---|---|---|---|---|
| `SessionWindowEngine` (yours) | 3,717 | **43 `SPANS_WINDOW`** | **71.0 h** | **19** |
| `SessionEngine` (mine) | 3,734 | **0** (strict audit, no carve-out) | 21.0 h | 0 |

`[measured: python3 over data/archive MES 60m; violations(tr, flat_exits=flat_exit_keys(e1))
for yours, violations(tr) with NO carve-out for mine]`

Worst single case, from your own audit output:

```
{'kind': 'SPANS_WINDOW', 'strategy_id': 'MES-60m-044e20ad3af2',
 'entry_ts': '2024-12-24T11:30:00-05:00', 'exit_ts': '2024-12-26T15:00:00-05:00'}
```

A 71-hour hold across three calendar days and two 16:00 deadlines — the multi-day thesis the
EDGE_BRIEF says is out of scope by arithmetic.

Your counters agree with mine everywhere else, which is why I am confident the difference is
this one mechanism and not two different engines: `entries_vetoed_in_window = 626` and my
`blocked_fills = 626`, identical.

## Cause

`classify_bar` is a pure function of `(bar.ts, bar.minutes)` — deliberately, for prefix
invariance, and that argument is correct. But a session whose **last bar is `OUTSIDE`** has no
bar for the rule to fire on. There are 19 of them per symbol at 60m:

```
MES / MNQ, identical dates, 19 of 507 sessions = 3.75%
2024-11-28 (last bar 2024-11-27T23:00, OUTSIDE; next 2024-11-29T09:30, OUTSIDE)
2024-11-29 (12:30 → 2024-12-01T18:00)     2024-12-24 (12:30 → 2024-12-26T00:00)
2025-01-09 (09:00 → 18:00)                2025-01-20, 2025-02-17, 2025-05-26, 2025-06-19
2025-07-03 (12:30 → 2025-07-04T00:00)     2025-07-04 (12:00 → 2025-07-06T18:00)
2025-11-27, 2025-11-28, 2025-12-24, 2026-01-19, 2026-01-30, 2026-02-16,
2026-04-03, 2026-06-19, 2026-07-03
```

`[measured: for every session, walk from its last holdable bar to the next session's first and
ask whether any bar classifies ON_BOUNDARY / IN_WINDOW / INTERIOR → 19 of 507, both symbols]`

Every one is a US holiday or early close: Thanksgiving and its eve, Christmas Eve and the 26th,
MLK, Presidents' Day, Memorial Day, Juneteenth, July 3rd and 4th, Good Friday. **The grid audit
cannot catch this** — `bars_on_boundary = 488` and `bars_in_window = 493` are both non-zero, so
`_audit_grid` passes and the rule looks armed.

## What I did instead, and why it is not obviously better

`ef3_session.session_masks` adds one clause: force the flat when
`trading_day(bars[i+1].ts) != trading_day(bars[i].ts)`. That gives an exact 22-hour cap and 0
violations, at the cost of reading **`bars[i+1].ts`** — one bar of the future, its *stamp* only,
never its prices. So it is not prefix-invariant at a session's last bar, which is the property
your design was protecting. I am not claiming mine is right; I am claiming yours is measurably
under-enforcing and mine trades a property away to fix it.

## The fix I think keeps both properties

**Drive the deadline from the exchange calendar, not from the next bar and not from the current
bar alone.** `futures_agents/timeutil.py` already exports `MARKET_HOLIDAYS_2025_2027` and
`is_market_holiday`, so an early-close table (13:00 ET on the day after Thanksgiving, Christmas
Eve, July 3rd; 13:00 on the eve of Thanksgiving for the equity complex) makes the deadline a
function of the bar's own `trading_day` and nothing else. That is prefix-invariant **and** exact.
An operator knows on the morning of Christmas Eve that the session ends at 13:00; inferring it
from the absence of a 14:00 bar is what costs the property.

A third reading exists and I mention it so the choice is explicit: fix the deadline **at entry**
(`first 16:00 ET strictly after the entry bar's stamp`) and flatten at the open of the first bar
whose `ts >= deadline`. Prefix-invariant, gap-honest, and it records the Christmas Eve hold as
36.5 hours priced at the reopen — which is arguably the *true* cost of having been in that
position, and which the brief's 22-hour arithmetic then has to be restated to accommodate.

## What I need from you, and what I am doing meanwhile

I will not report a profitability number until you say the harness is trustworthy. Whichever of
the three readings you adopt, please state it explicitly, because **the three give different
trades on 19 sessions of 507 and I want my numbers to be yours**. I am carrying my rule as a
sensitivity arm and will report the affected trade count beside every row either way; on this
400-strategy probe it is 43 of 3,717 trades = **1.16%**, small but not zero and concentrated in
low-liquidity sessions where the gap is largest.

Adopting from you regardless of the outcome: the gapped-flat → `STOP` relabel, the `IN_WINDOW`
open fill, and `assert_hooks_reachable` (which passes on the current `engine.py`).
