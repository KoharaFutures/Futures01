# EF7 burst 07 — population scale, plus two latent hazards in the substrate

## Population scale: still zero

`[measured: code/population.py 4000 → population.json]` Arm C only, `data/archive/` 60m.

| symbol | strategies | trades | **violations** | flat exits | max hold | >22h |
|---|---|---|---|---|---|---|
| MGC | 1,984 | 9,725 | **0** | 6,362 (65.4%) | 300 min | 0 |
| MCL | 1,957 | 16,013 | **0** | 10,287 (64.2%) | 900 min | 0 |
| MES | 1,964 | 12,509 | **0** | 8,430 (67.4%) | 1,260 min | 0 |
| MNQ | 1,985 | 13,578 | **0** | 8,006 (59.0%) | 1,260 min | 0 |
| **total** | **7,890** | **51,825** | **0** | **33,085 (63.8%)** | | **0** |

Run because of EF3's lesson (relayed by the coordinator) that a cycle-boundary defect can be 0 on a
400-strategy probe and non-zero on a population. Worth adding the converse: **a probe samples cycle
boundaries and a saturating fixture does not.** `invariant.py`'s always-fire fixture holds a position
across essentially every boundary in the series, so a rare boundary is not rare to it; what it cannot
exercise is *interactions* — scale-outs, breakeven, trailing stops and anchored targets all touch
`_manage` before the flat. So the right coverage for a rare-path defect is a saturating control
**and** a population, not one or the other.

`TIME` exits: **0 of 51,825** on every symbol, matching EF3 independently. Cause is the same: the
smallest `time_stop_bars` in the catalogue is 30 *primary* bars = 30 hours against a 22-hour ceiling.
So the whole time-stop dimension measures nothing under this rule — and my deliberate choice to let
the time stop outrank the flat therefore changes **no** number on this population.

## EF7-D4 — a stale signal fills across a data gap, up to 52.5 hours later

`[measured: arm C, generated default, fill lag = bars[entry_index].ts − bars[signal_index].end_ts]`

| symbol | trades | non-contiguous fills | fills in a **different cycle** | worst |
|---|---|---|---|---|
| MGC | 2,143 | 0 | 0 | — |
| MCL | 3,343 | 6 (0.18%) | 2 (0.06%) | signal 2024-11-29 12:30 → fill 2024-12-01 18:00 = **3,150 min (52.5 h)** |
| MES | 2,554 | 14 (0.55%) | 14 (0.55%) | signal 2024-12-24 12:30 → fill 2024-12-26 00:00 = **2,070 min (34.5 h)** |
| MNQ | 1,536 | 16 (1.04%) | 16 (1.04%) | signal 2025-11-28 12:30 → fill 2025-11-30 18:00 = **3,150 min (52.5 h)** |

Inherited, not mine: `run_many` parks a signal in `pending` and fills it at whatever the **next
processed bar** is (`engine.py:290-295`). On contiguous data that is the next bar's open and correct.
Across a half-day close plus a weekend it is two and a half days later, and my veto correctly allows
it because 18:00 Sunday is an admissible instant.

**Not a spec violation** — every one of these fills is inside the window. It is a realism defect, and
it is the whole explanation for why my measured `rth_only=True` hold cap is **12 h on MES** rather
than the 6.5 h the arithmetic implies. One clause fixes it (refuse a fill whose cycle differs from
the signal's, or whose lag exceeds one bar duration). **I have not applied it**: silently making the
rule stricter than the specification is precisely the error I exist to catch in other people's work.
Offered, and routed to the manager.

## EF7-D5 — the archive contains off-grid 60m bars, which a 16:00 rule can straddle

`[measured: minute-of-hour histogram over data/archive/*_60m.jsonl]`

**20 of ~11,300 60m bars per symbol are stamped at `:30`**, identically on all four symbols, on
exactly five dates — **2024-11-29, 2024-12-24, 2025-07-03, 2025-11-28, 2025-12-24**, four bars each.
These are the half-day sessions; Yahoo appears to bucket backwards from a 13:00 close, so the grid
shifts by 30 minutes. They are at 09:30/10:30/11:30/12:30, there are **no overlapping consecutive
bars** (0 on all four symbols), and **none straddles 16:00 today** — `flat_on_late_bar` is 0 in every
run I have made.

It is a latent hazard rather than a live defect, and worth writing down because it is invisible until
it is not: a `:30`-stamped 60m bar in the afternoon would run 15:30 → 16:30 and **cross the
deadline**, and there would be no printed price at 16:00 to fill the flat against. My rule detects it
(`flat_flags` clause 2, `end_ts > flat_instant`) and counts it (`WindowStats.flat_on_late_bar`), and
the violation detector would flag the resulting exit as `exit_in_window` rather than let it through.
Anyone asserting "16:00 is always a bar boundary" from `align_bucket`'s midnight alignment should
know that the archive's 60m series is Yahoo's own bucketing, not a resample, so `align_bucket` does
not govern it.
