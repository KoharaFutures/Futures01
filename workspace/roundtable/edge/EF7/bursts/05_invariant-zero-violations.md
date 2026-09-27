# EF7 burst 05 — the invariant on realised trades: zero violations, all four symbols

`[measured: python3 workspace/roundtable/edge/EF7/code/invariant.py → EF7/invariant.json]`
Substrate: `data/archive/` 60m, MGC 11,297 / MCL 10,934 / MES 11,287 / MNQ 11,291 bars,
2024-10-06 → 2026-09-25. Costs: shipped `CostModel` defaults.

## Why a saturating fixture and not a generated strategy

The strategy is a synthetic condition that fires on **every bar**, with a 200-tick fixed stop and a
20R target, `rth_only=False`. So a position exists in essentially every admissible bar of every
cycle and almost nothing but the flat can close it. That is the point: a selective strategy taking 30
trades cannot distinguish *"zero violations"* from *"almost no exposure"*. This maximises the number
of chances the rule has to breach the spec. Both directions, so a sign error cannot hide.

## Result

**TOTAL VIOLATIONS ACROSS ALL SYMBOLS AND DIRECTIONS: 0.**

| symbol | dir | trades | **violations** | flat exits | entries vetoed | early flats | same-bar entries | max hold (min) |
|---|---|---|---|---|---|---|---|---|
| MGC | LONG | 1,313 | **0** | 470 | 495 | 13 | 28 | 1,260 |
| MGC | SHORT | 2,037 | **0** | 440 | 495 | 16 | 51 | 1,260 |
| MCL | LONG | 650 | **0** | 501 | 474 | 33 | 8 | 1,260 |
| MCL | SHORT | 631 | **0** | 496 | 474 | 33 | 12 | 1,260 |
| MES | LONG | 718 | **0** | 488 | 493 | 18 | 14 | 1,260 |
| MES | SHORT | 678 | **0** | 491 | 493 | 18 | 12 | 1,260 |
| MNQ | LONG | 2,010 | **0** | 423 | 497 | 17 | 70 | 1,260 |
| MNQ | SHORT | 1,973 | **0** | 439 | 497 | 17 | 64 | 1,260 |

The three clauses tested are: entry instant inside 16:00–18:00 ET; exit bar inside it **or running
past the deadline**; and entry and exit in different cycles. The detector is separately shown
rejecting each clause on hand-built trades, and shown rejecting the *unmodified* engine on the same
fixture (`test_h3_the_unmodified_engine_fails_this_same_assertion`), so the zero is a pass rather
than a detector that never fires.

## Four cross-checks that fall out of the counters

1. **`entries_vetoed` equals the number of forbidden bars exactly** — 495/495 MGC, 474/474 MCL,
   493/493 MES, 497/497 MNQ. The saturating fixture attempts a fill on every bar, so the veto firing
   on exactly the forbidden set and nothing else is an independent confirmation that the veto tests
   the right instant. One bar off in either direction and these numbers would not match.
2. **`max_minutes_held` is 1,260 on every symbol and both directions, never once more.** The engine
   measures `minutes_held` between bar *open* times (`engine.py:512`), so a full 18:00→16:00 hold on
   60m bars reads as 21 hours, not 22. 1,260 minutes is therefore the exact ceiling the 22-hour cycle
   permits, hit but never exceeded — the hold budget is binding and nothing leaks past it.
3. **`end_of_data_exits` = 0 everywhere.** The last bar of every archive series is the 16:00
   forbidden bar, so the position always closed at the preceding 15:00 flat and the boundary case
   never had to be exercised. Good, but it means the END_OF_DATA path is covered only by the
   synthetic tests.
4. **Early flats**: 13/16 MGC, 33/33 MCL, 18/18 MES, 17/17 MNQ — the cycles from EF7-D1 whose data
   ends before 16:00. MCL is worst, as EF7-D1 predicted. These are honest deviations forced by the
   substrate, counted separately and never folded into the headline.

One reporting note on `invariant.json`: the field `cycle_ends` counts bars where `flat_flags` is
`True`, which is (cycle-terminating bars) **+** (bars inside the forbidden window, which can never be
held). Subtract `bars_in_forbidden_window` for the cycle count: MGC 1001 − 495 = **506**, matching
burst 01's independent partition exactly.
