# EF1 burst 03 — the gate failed. 33 violations, all on sessions with no bar at the deadline

First full three-arm run, `data/archive` 60m base, timeframes 60m+240m, `max_total=400`,
seed 20260922.

```
MGC  bars=11297 strat=184 | A trades= 626 viol= 139 | B trades= 463 viol= 360 | C trades= 554 viol= 0 flats= 420 (75.8%) vetoed=  0
MCL  bars=10934 strat=167 | A trades=2626 viol= 595 | B trades=2011 viol=1186 | C trades=2179 viol=18 flats=1283 (58.9%) vetoed=  0
MES  bars=11287 strat=190 | A trades=1292 viol= 986 | B trades=1292 viol=1056 | C trades=1368 viol= 9 flats= 823 (60.2%) vetoed=683
MNQ  bars=11291 strat=185 | A trades=1403 viol= 860 | B trades= 818 viol= 839 | C trades= 979 viol= 6 flats= 842 (86.0%) vetoed=424
TOTAL arm-C violations: 33   (FAIL)
```

**33 is not zero, so the rule as first built does not hold the invariant it exists to hold.**
Writing that down before fixing it, because the number is the finding.

## Every one of the 33 is `SPANS_WINDOW`, and every one is an early-close or data-hole session

`[measured: workspace/developer/ef1_validation_swing_60m.json → violation_detail]`

```
MCL-240m-...  entry 2026-01-09T12:00-05:00  exit 2026-01-12T03:00-05:00
MES-240m-...  entry 2025-07-03T10:30-04:00  exit 2025-07-04T03:00-04:00
MNQ-240m-...  entry 2024-12-24T12:30-05:00  exit 2024-12-26T15:00-05:00
```

All 33 are `primary_tf=240m`. The mechanism is exact: **the pure per-bar rule can only fire on a
bar that exists.** On a session that shuts before 15:00, no bar ends at 16:00 and no bar starts in
`[16:00, 18:00)`, so neither the `ON_BOUNDARY` branch nor the `IN_WINDOW` branch ever gets a bar to
act on, and the position runs straight through the forbidden window into the next session.

## How many such sessions there are, per symbol

ET dates carrying bars before 16:00 but **no** bar ending at 16:00 and **no** bar starting inside
the window `[measured: python over data/archive/*_60m.jsonl, classify_bar per bar]`:

| symbol | ET dates in archive | dates with no deadline bar |
|---|---|---|
| MGC | 596 | **9** |
| MCL | 590 | **27** |
| MES | 595 | **10** |
| MNQ | 595 | **10** |

Two distinct causes, and they need different words:

**(a) Genuine exchange early closes and holidays — 9-10 dates, all four symbols, identical dates.**
2024-11-29 (Black Friday), 2024-12-24, 2025-05-26 (Memorial Day), 2025-06-19 (Juneteenth),
2025-07-03, 2025-07-04, 2025-11-28, 2025-12-24, 2026-01-30. Plus 2025-01-09 on MES/MNQ only.
On these the last bar before the deadline is stamped 12:00-14:00 and the session does not reopen
until 18:00. **A position open at 12:30 on Black Friday physically cannot be flattened at 16:00 —
the market is shut.** Real-world compliance requires being flat by the early close, which a trader
knows in advance from the published exchange calendar.

**(b) A two-month hole in MCL 60m — 17 further dates, 2026-01-12 to 2026-03-10.** Those dates carry
**1 to 5 bars each**, starting at 03:00 or 05:00, against ~20 on a normal day. This is a substrate
defect, not a calendar one, and it is EF2-EF5's problem as much as mine: **MCL's 60m archive series
is structurally thin for roughly two months inside the 718-day span.** Flagged separately; it is
not fixed by anything EF1 does.

## The fix, and exactly what it costs in look-ahead terms

Component **1b: a session-end forced flat.** For each ET date, if the date carries bars before
16:00 but no `ON_BOUNDARY` and no `IN_WINDOW` bar, then the date's **last pre-16:00 bar** is the
last one a position may be held on, and a position open there is flattened at its close with the
same market-order slippage as any other flat.

**What information this uses.** Only bar **timestamps**. No price from any bar is read, at any
index. The price-look-ahead invariant holds absolutely and is unchanged.

**What it does cost.** The map is built from the whole series' timestamps, so it is not a pure
per-bar function the way `classify_bar` is. That is the honest position and it is stated rather
than buried:

- `classify_bar` stays exactly prefix-invariant — a pure function of `(ts, minutes)`.
- The session-end map needs a date's full timestamp list, so on a prefix that cuts *inside* an
  early-close date the map's last entry can differ from the full series'. The affected trade is the
  one still open at the cut, which is an `END_OF_DATA` artefact of where the cut fell and is
  excluded from the prefix comparison for that reason.
- The live-trading equivalent of this information is the exchange session calendar, published
  weeks ahead, so a trader has it in advance. `test_session_end_map_is_a_function_of_timestamps_only`
  perturbs every price in the series and asserts the map does not move, which is the check that
  distinguishes "calendar knowledge" from "reading tomorrow's close".

Also added: a **strict emission check**. `SessionWindowEngine._close` audits every trade it is about
to return and raises if it violates the window. A count reported after the fact tells you something
broke; an assertion at emission tells you *which trade*, and makes it impossible for a later change
to reintroduce this class of hole silently.
