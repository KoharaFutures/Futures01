# EF1 burst 05 — final state at parking

All four validations green. Full detail and the resumption note are in `FINDINGS.md` under
`## PARKED 2026-09-27`; this is the one-screen version.

```
EF1-H7   tests/test_ef1_session_window.py                                57 passed
EF1-H8   saturate.py MGC,MCL,MES,MNQ x 5,15,30,60,240 x LONG,SHORT
         violations 0   over-cap holds 0   control (shipped engine) violations 78
EF1-H9   measure.py --base-tf 60 --tfs 60,240 --max-total 400
         arm-C violations: MGC 0  MCL 0  MES 0  MNQ 0
EF1-H10  prefix_check.py
         L1 x4: classify_mismatches 0, session_end_off_cut 0 (on_cut 4-5)
         L2 x4: mismatches 0
full suite: 2 failed, 1018 passed, 7 xfailed  -- the 2 are tests/test_bt6_vwap_daily.py,
         which passes 14/14 alone and 0-failed alongside mine; not EF1's, BT6 owns it
```

## The three numbers the dispatch asked for

| question | answer |
|---|---|
| expressible without editing `futures_agents/`? | **yes** — subclass, three overrides, nothing in the package touched |
| violation count on real bars | **0**, on all four symbols, three separate instruments, strict audit |
| positions the rule closes that would otherwise have run on | **MGC 420 (75.8%), MCL 1303 (59.6%), MES 832 (60.3%), MNQ 850 (86.3%)** — median 12–43 extra 60m bars, max 416 |

## Two defects found in my own code by my own checks, in order

1. **EF1-D3** — 33 `SPANS_WINDOW` violations on early-close sessions. Found by `EF1-H9`.
   EF3 found the same mechanism independently and measured a 71-hour hold at 60m.
2. **EF1-D4** — the fix for D3 keyed on the ET calendar date and caught 10 of 19 dates, missing every
   full holiday (no bars on the date at all). Found by `EF1-H8` on its first run, at the first
   offending bar, and stopped at emission by the strict check rather than counted afterwards.

Plus two defects in my own **assertions**, which is the less obvious failure mode: an over-tight
hold cap (`22*60 - tf` instead of `1320`) that flagged a legal 20-hour 240m hold, and a prefix
report comparing against ET dates while the map keyed on trading days. An over-tight check in a gate
misleads as much as a loose one — the first of those would have had me withdraw a cell that was fine.

## The one correction I am leaving behind

**240m is expressible and should not be withdrawn** —
`msgs/EF1-02_manager_240m-is-expressible-ef6-divisor-is-the-wrong-one.md`. The divisor that matters
is `960 % tf` (the flat) and `1080 % tf` (the reopen), not `1320 % tf` (the window length). At 240m
`960 % 240 == 0`, so the flat lands exactly on the grid; `1080 % 240 == 120`, so what is lost is the
18:00–20:00 entry window and the effective cycle is 20h not 22h. 1440m genuinely cannot carry it.
And the 33 violations were holiday coverage, not grid arithmetic — EF3 measured 43 of the identical
violations at 60m, where `1320/60 = 22` exactly.
