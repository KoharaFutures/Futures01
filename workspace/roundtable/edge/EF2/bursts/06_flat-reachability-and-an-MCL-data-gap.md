# EF2 / Burst 06 — the 16:00 flat cannot fire in 17 MGC and 34 MCL cycles, and half of MCL's excess is missing data

Prompted by `msgs/EF3-01_EF1_session-rule-misses-early-close-sessions.md`, which measured EF1's
`classify_bar` under-enforcing the flat on **19 of 507 MES/MNQ sessions (3.75%)** with a 71-hour hold
as the worst case. **I re-measured it on my own two symbols rather than inheriting the count.** MGC is
COMEX and MCL is NYMEX; neither shares the equity complex's early-close calendar, so nothing about
19/507 transfers. Code: `EF2/code/flat_reachability.py`; artefact: `EF2/data/flat_reachability.json`.
Posted to EF1 as `msgs/EF2-02_EF1_flat-unreachable-on-MGC-MCL-and-an-MCL-data-gap.md`.

## Method — exact, no engine and no tape

For every 18:00 ET → 16:00 ET cycle in the series, does the series contain **any** bar EF1's rule can
act on at that cycle's deadline — `ON_BOUNDARY` (ends exactly at 16:00), `IN_WINDOW` (starts inside
`[16:00, 18:00)`) or `INTERIOR`? A cycle with none of the three is one in which a position can survive
16:00 while the harness reports success. EF1's `classify_bar` is imported directly, so this measures
EF1's rule and not a re-implementation of it.

## Result

| cell | bars | cycles | **cycles where the flat cannot fire** | share |
|---|---|---|---|---|
| MGC 60m | 11,297 | 506 | **17** | **3.36%** |
| MGC 240m | 3,052 | 602 | 9 | 1.50% |
| **MCL 60m** | 10,934 | 505 | **34** | **6.73%** |
| MCL 240m | 2,990 | 596 | 14 | 2.35% |

Bar-class totals, which also show why EF1's series-level `_audit_grid` passes my grid happily:

| cell | OUTSIDE | ON_BOUNDARY | IN_WINDOW | INTERIOR |
|---|---|---|---|---|
| MGC 60m | 10,313 | 489 | 495 | **0** |
| MGC 240m | 1,969 | 497 | 586 | **0** |
| MCL 60m | 9,990 | 470 | 474 | **0** |
| MCL 240m | 1,936 | 491 | 563 | **0** |

**Zero `INTERIOR` bars anywhere**, so `SessionGridError` is never raised and the run proceeds — while
17 (MGC) and 34 (MCL) cycles inside it were never tested. The audit is per *series*; the hole is per
*cycle*.

MGC's 3.36% matches EF3's 3.75% within noise, and **16 of MGC's 17 cycles are the same dates as 16 of
MCL's 34**: Thanksgiving and the half-session after it, 24 December, MLK, Presidents' Day, Memorial
Day, Juneteenth, 3 and 4 July, plus `2026-01-30`. That is the shared-calendar half.

## The MCL half that is not a calendar — and it is in the frozen store too

**MCL only, 18 cycles:** `2026-01-09`, `2026-01-12`…`2026-01-16`, `2026-02-20`,
`2026-02-23`…`2026-02-27`, `2026-03-02`…`2026-03-05`, `2026-03-09`, `2026-03-10`.
**MGC only: 1** (`2026-01-19`, MLK, where MCL carries one extra bar).

All 18 are ordinary weekdays, and **MGC has full data on every one.**

```
MGC archive 60m : 11,297 bars       MCL archive 60m : 10,934 bars
bars MGC has that MCL lacks : 366, over 34 dates
bars on those dates:  MGC archive 442   MCL archive 102
worst: 2026-01-12 (22 missing), 01-15 (22), 01-13 (21), 01-14 (21),
       02-23 (19), 02-24 (19), 02-25 (18), 03-02 .. 03-10 (18 each)
```
`[measured: python3, set difference of to_et(bar.ts) over data/archive/{MGC,MCL}_60m.jsonl]`

**Two contiguous runs of missing MCL hourly bars — 2026-01-09 → 2026-01-16 and 2026-02-20 →
2026-03-11.** On those days MCL carries 1–5 bars per cycle, typically 03:00 → 13:00, so there is no bar
anywhere near 16:00.

And it is not an archive-reconciliation loss:

```
csv/raw/MCL_1h.csv on those dates : 102 bars
data/archive MCL_60m on those dates: 102 bars
bars csv/raw has that the archive LACKS on those dates: 0
```
`[measured: python3 over csv/raw/MCL_1h.csv (read-only) and data/archive/MCL_60m.jsonl, both ET-normalised]`

**They are absent from both stores.** So this is the vendor's MCL series, `BarArchive` behaved
correctly, and **every published MCL result in `scan_reports/` rests on the same gap.** The BRIEF's
data policy verified that the two stores hold the *same* series over their *overlapping* stamps; it
never asked whether either store is *complete*. On MCL at 60m it is not — **366 bars, 3.3% of the
series, in two runs.**

This is a substrate-quality asymmetry between my two symbols that no existing artefact records, and it
compounds the one economic asymmetry the corpus does record: MCL is the cost-fragile contract (costs
flip 8 of 183 MCL 60m rows from positive gross to negative net, against 1 of 259 for MGC).

## What EF2 does about it

1. **Every EF2 row states the count of cycles in which the flat could not fire for its cell** — 17
   (MGC 60m), 9 (MGC 240m), 34 (MCL 60m), 14 (MCL 240m). A row whose trades cluster in those cycles is
   not reportable.
2. **Every MCL row is reported twice: with and without the two gap windows.** A hold that runs into a
   multi-day hole has its exit deferred to the next available bar, which is an unrealistic fill, and it
   is exactly the "unrealistic fills" item on the anti-overfitting list — found here as a real instance
   rather than checked off.
3. **The exclusion is a pre-registered sensitivity, not a filter chosen after seeing the answer.** The
   two windows are named above, before any expectancy exists.
4. **`D40`'s shape, in a new instrument.** D40 excluded the grain CSVs because they splice contract
   months. This is not splicing — it is absence — but it has the same consequence for a momentum rule:
   the bar after the gap carries a multi-day return that a 1-bar change reads as a 1-hour move. Flagged
   for the manager as a D-candidate: *`MCL_60m` is missing 366 bars in two contiguous runs, in both
   stores, and no artefact records it.* Allocating a `D` number is the manager's, so I have not.
