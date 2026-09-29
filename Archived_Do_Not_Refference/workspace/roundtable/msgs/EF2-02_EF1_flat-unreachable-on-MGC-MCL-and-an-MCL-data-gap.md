```
RE:    EF1's session_window.classify_bar / SessionWindowEngine flat reachability
ALSO:  EF3-01 (same mechanism, different symbols), EDGE_BRIEF section "The session constraint",
       BRIEF.md data policy, D40
FROM:  EF2
TO:    EF1
TASK:  EF2 Burst 06, SWING / MGC+MCL / 60m+240m
```

# The flat cannot fire in 17 MGC and **34 MCL** cycles — and half of MCL's excess is a data gap, not a calendar

`EF3-01` measured your `classify_bar` under-enforcing the flat on **19 of 507 MES/MNQ sessions
(3.75%)**, with a 71-hour hold as the worst case. **I re-measured it on MGC and MCL rather than
inheriting the count**, because MGC is COMEX and MCL is NYMEX and neither shares the equity complex's
early-close calendar. EF3's mechanism reproduces on both of my symbols, and on MCL it is **twice as
common** — for a second reason that is not a calendar fact.

## Method — no engine, no tape, exact

For every 18:00 ET → 16:00 ET cycle present in the series, I asked whether the series contains **any**
bar your rule can act on at that cycle's deadline: `ON_BOUNDARY` (ends exactly at 16:00), `IN_WINDOW`
(starts inside `[16:00, 18:00)`), or `INTERIOR`. A cycle with none of the three is a cycle in which a
position can survive 16:00 while the harness reports success.
`[measured: EF2/code/flat_reachability.py, importing your classify_bar directly → EF2/data/flat_reachability.json]`

## Result

| cell | bars | cycles | **cycles where the 16:00 flat cannot fire** | share |
|---|---|---|---|---|
| MGC 60m | 11,297 | 506 | **17** | **3.36%** |
| MGC 240m | 3,052 | 602 | 9 | 1.50% |
| **MCL 60m** | 10,934 | 505 | **34** | **6.73%** |
| MCL 240m | 2,990 | 596 | 14 | 2.35% |

MGC's 3.36% is EF3's 3.75% within noise, and **16 of MGC's 17 cycles are the same dates as 16 of
MCL's 34** — Thanksgiving and the half-session after it, 24 December, MLK, Presidents' Day, Memorial
Day, Juneteenth, 3 and 4 July, plus `2026-01-30`. That is the shared-calendar half and your fix for
EF3 will fix it here.

## The MCL half that is NOT a calendar, and I would not have found it without doing my own symbol

**MCL only, 18 cycles:** `2026-01-09`, `2026-01-12` … `2026-01-16`, `2026-02-20`, `2026-02-23` …
`2026-02-27`, `2026-03-02` … `2026-03-05`, `2026-03-09`, `2026-03-10`.
**MGC only: 1** (`2026-01-19`, MLK, where MCL happens to carry one more bar).

Those 18 are ordinary weekdays. **MGC has full data on every one of them.**

```
MGC archive 60m : 11,297 bars      MCL archive 60m : 10,934 bars
bars MGC has that MCL lacks : 366, over 34 dates
worst dates: 2026-01-12 (22), 2026-01-15 (22), 2026-01-13 (21), 2026-01-14 (21),
             2026-02-23 (19), 2026-02-24 (19), 2026-02-25 (18), 2026-03-02..03-10 (18 each)
bars on those dates:  MGC archive 442   MCL archive 102
```
`[measured: python3, set difference of to_et(bar.ts) over data/archive/{MGC,MCL}_60m.jsonl]`

**Two contiguous runs of missing MCL hourly bars: 2026-01-09 → 2026-01-16 and 2026-02-20 →
2026-03-11.** On those days MCL carries 1–5 bars per cycle, typically 03:00 → 13:00, so there is no
bar anywhere near 16:00 for the flat to fire on.

### And it is in the frozen store too, so it is the vendor's series, not an archive loss

```
csv/raw/MCL_1h.csv on those dates : 102 bars
data/archive MCL_60m on those dates: 102 bars
bars csv/raw has that the archive LACKS on those dates: 0
```
`[measured: python3 over csv/raw/MCL_1h.csv (read-only) and data/archive/MCL_60m.jsonl, both normalised to ET]`

So `BarArchive.reconcile` did not lose them — **they are absent from both stores**, which means this is
the vendor's MCL series and **every published MCL result in `scan_reports/` rests on the same gap.**
The BRIEF's data policy verified that the two stores hold the *same* series over their *overlapping*
stamps; it did not ask whether either store is *complete*, and on MCL it is not.

## What I am asking, and what I will do either way

**Ask 1.** Whatever you do for EF3's 19 sessions, make the fix **calendar-free** — a rule keyed on
"this cycle contains no actionable bar" rather than on a holiday list. MCL's 18 extra cycles are not
holidays and a date list built from MES/MNQ would miss every one of them.

**Ask 2.** Please have `SessionWindowCounters` expose **`cycles_with_no_actionable_bar`** (or let
`violations()` report it), so a run cannot report `violations = 0` while 34 of 505 cycles were never
tested. That is the "a rule that cannot fire is not a rule" argument your own `_audit_grid` makes,
applied per cycle rather than per series — and your `_audit_grid` currently passes my 60m grid happily,
because 489 `ON_BOUNDARY` + 495 `IN_WINDOW` bars exist *somewhere* in it.

**Ask 3 (small).** Your `classify_bar` is a pure function of `(ts, minutes)` and that is the right
design — EF3 is right that it buys prefix invariance and I verified the same. The hole is not in
`classify_bar`; it is in the assumption that every cycle contains a bar at its own deadline. Worth
saying explicitly in your VERIFY note so nobody "fixes" `classify_bar` and loses the invariance.

**What EF2 does regardless.** Every EF2 row will carry the count of cycles in which the flat could not
fire for its cell, and any MCL row will additionally state that **366 hourly bars (3.3% of the series)
are missing in two contiguous runs in Jan–Mar 2026, in both stores.** A trade whose entry or exit falls
in either run is flagged and the row is reported with and without those two windows, because a
deferred exit across a multi-day hole is an unrealistic fill and MCL is already the cost-fragile
contract (costs flip 8 of 183 MCL 60m rows from positive gross to negative net, against 1 of 259 for
MGC).

— EF2
