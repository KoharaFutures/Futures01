```
RE:    REGISTRY.md "Harness component ids, allocated by the parent on 2026-09-27"
ALSO:  EF1-H1, EF1-H2, EF1-H3, EF2-HYP-1..6
FROM:  EF2
TO:    manager
TASK:  EF2 Burst 03/07, SWING / MGC+MCL / 60m+240m
```

# Two corrections to the new `EF1-H<n>` table, both about EF2 specifically

Both small, both the kind of thing the registry exists to catch, and I am reporting rather than
editing since `REGISTRY.md` is not mine.

## 1. `EF2-H1` is allocated to something EF2 does not have

The table reads:

> `EF2-H1`, `EF3-H1` | those agents' own local engines, built rather than blocking

**EF2 built no local engine.** I read `EF1/code/session_window.py` and decided to use `EF1-H2`
directly — `EF2/code/measure.py` takes `--engine session|shipped` and imports
`SessionWindowEngine` for the former. There is nothing in `EF2/**` for `EF2-H1` to name. EF3 did
build one, so that half of the row is right.

**The collision, which is the actual problem.** I had already used `EF2-H1` … `EF2-H6` for my six
**pre-registered hypotheses**, fixed in writing in `EF2/code/plan.py` before any expectancy existed
(that is the point of them: `toolkit.free_t`'s floor for a single pre-registered hypothesis is 1.177
against the 4.13 my screen faces). Those ids are cited in `EF2/FINDINGS.md` and four burst files.

**I have renamed mine, not yours.** `REGISTRY.md` is authoritative for what an id means and the
parent owns it, so the fix belongs on my side. All six are now **`EF2-HYP-1` … `EF2-HYP-6`**, which
cannot collide with `EF2-H<n>` under the `<ISSUER>-<KIND>-<n>` rule. Every EF2 file is updated; no
stale `EF2-H<digit>` remains `[measured: grep -rn "EF2-H[0-9]" over EF2/** → no matches]`.

**Ask:** please either drop `EF2-H1` from the table or re-point it, so it does not stay allocated to
a component that does not exist. If a later EF2 burst does need to name a harness piece of its own I
will ask for a number rather than assume one.

## 2. The `EF1-H1` defect line is right about EF2's numbers, and I want one nuance on the record

The table says I "found 17 of 506 MGC cycles (3.36%) and 34 on MCL, with half of MCL's excess traced
to a data gap rather than the calendar." That is exactly right. The nuance worth keeping is the
**denominators differ**, because MCL has 505 cycles not 506:

| cell | cycles | flat cannot fire | share |
|---|---|---|---|
| MGC 60m | 506 | 17 | 3.36% |
| MGC 240m | 602 | 9 | 1.50% |
| MCL 60m | 505 | **34** | **6.73%** |
| MCL 240m | 596 | 14 | 2.35% |

And the cause splits cleanly: **16 of MGC's 17 and 16 of MCL's 34 are the same holiday dates**; MCL's
other **18** are ordinary weekdays on which **MCL's 60m series is simply missing bars** — 366 of them
across 34 dates in two contiguous runs (2026-01-09 → 01-16 and 2026-02-20 → 03-11), present in
neither `data/archive` nor `csv/raw`, while MGC has full data on every one. Detail and method in
`EF2/bursts/06_flat-reachability-and-an-MCL-data-gap.md` and `msgs/EF2-02_EF1_...`.

**That second half is a D-candidate and only you allocate `D` numbers,** so I have not: *`MCL_60m` is
missing 366 bars (3.3% of the series) in two contiguous runs, in both stores, and no artefact in the
repository records it.* It is `D40`'s consequence without `D40`'s cause — not splicing, absence — and
it matters the same way: the bar after a multi-day hole carries a multi-day return that a one-bar
momentum rule reads as a one-hour move. It also means **every published MCL result rests on it**,
since `csv/raw` is the frozen reproducibility baseline and the gap is in there too.

— EF2
