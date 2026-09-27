# EF2 / Burst 08 — EF6's placebo faults, re-measured on MCL (which EF6 did not cover)

`EF6/bursts/03_placebo-under-the-window.md` measured three faults in `workspace/newstrats/placebo.py`
under the 18:00→16:00 rule, on **MGC and MNQ**. MCL is one of my two symbols, the independence rule
says nothing transfers, and EF6's reason MGC escapes Fault 1 (RTH closes 13:30, so its last RTH bar
fills at 14:00) has an MCL analogue (RTH closes 14:30, last RTH bar stamped 14:00, fills at 15:00) that
is an **argument, not a measurement**. This measures it.

Code: `EF2/code/mcl_placebo_probe.py`. Artefact: `EF2/data/mcl_placebo_probe.json`. Run on the cells
EF2 publishes — a 60m base with frames `(60,)` and `(60,240)` — and **not** on a 240m base, because a
240m base is 19% `STRADDLE` bars (burst 05) and EF1's harness refuses such a grid.

| cell / arm | bases with ≥2 raw signals | base legal share | pool legal share | **mean expected legal gap** | mean long share | **mean dir-shuffle degeneracy** |
|---|---|---|---|---|---|---|
| `MCL:f60__p60` rth=T | **0** | — | — | — | — | — |
| `MCL:f60__p60` rth=F | 3 | 1.000 | 0.975 | **−0.12** | 0.400 | **0.520** |
| `MCL:f60_240__p240` rth=T | 15 | 1.000 | **1.000** | **+0.00** | 0.441 | **0.683** |
| `MCL:f60_240__p240` rth=F | 18 | 0.975 | 0.957 | **−0.81** | 0.422 | **0.649** |
| `MGC:f60__p60` rth=T | **0** | — | — | — | — | — |
| `MGC:f60__p60` rth=F | **0** | — | — | — | — | — |
| `MGC:f60_240__p240` rth=T | 4 | 1.000 | **1.000** | **+0.00** | 0.651 | **0.546** |
| `MGC:f60_240__p240` rth=F | 4 | 0.993 | 0.962 | **−3.07** | 0.643 | **0.541** |

## Three results

**1. Fault 1 is inert under `rth_only=True` on BOTH my symbols, and live under `rth_only=False`.**
Pool legal share is **1.000** with a legal gap of **exactly 0.00** in both `rth=T` cells — so under the
generated default the upstream count-matching is already correct on MGC and MCL, and EF6's MGC finding
replicates on MCL. Under `rth_only=False` the gap is **−0.81 on MCL and −3.07 on MGC**: the
count-matched placebo arrives with about one (MCL) to three (MGC) **fewer legal entries** than its base.
That is the arm the whole programme is about, so **EF6's `schedule_random_legal` is required, not
optional**, and the requirement is confirmed on my symbols rather than inherited.

Worth noting the sign: on both my symbols the gap is **negative** — the control is handicapped, which
biases in favour of the real strategies. EF6 measured the sign **reversing** on MNQ 15m. So "it is
conservative" is a per-cell fact and cannot be asserted generally; on MGC/MCL at 60m it happens to be
conservative, and I will say that rather than say it is safe.

**2. Fault 2 is worse on my symbols than EF6's headline suggests.** A direction shuffle leaves
**52–68% of labels unchanged** in every cell I measured — mean degeneracy 0.520, 0.649, 0.683, 0.541.
The formula's floor is 0.5 (at long share exactly 0.5) and the *mean* exceeds it because degeneracy is
convex in the long share and several rule sets are strongly one-sided. **So a direction-shuffle control
on an EF2 cell would be more than half identical to its treatment.** Dropping it is not a preference.

**3. A result about power, not about placebos, and it is the more important one.** In
`MGC:f60__p60` **not one of the first 30 surviving rule sets produced 2 raw signals** — in either arm.
`MCL:f60__p60` rth=T likewise zero, rth=F only three. Against that, `f60_240__p240` gave 15 and 18 on
MCL.

**Method caveat, stated because it changes how far this travels:** the probe takes the **first 30 rule
sets in sorted order**, not a random sample, and `rule_sets_for` sorts by group name — so the first 30
are BREAKOUT rule sets, whose base filter set is `('volatility_compressed', 'volume_not_thin')`
`[repo-verified: combinator.py, BREAKOUT template]`, the most restrictive in the catalogue. So the
zeros are partly BREAKOUT's thinness and not purely the cell's. **It is consistent with, but weaker
than, burst 04's random-free measurement**, which is the one to quote: ~67% of MGC `f60__p60` arms never
fire and the live median is 13.

The honest reading: **the 60m-alone cell is thin enough that a placebo cohort built on it will rest on a
handful of bases**, which reproduces EF6's own sample-size warning ("only 4 of 12–25 bases per cell had
≥2 raw legal signals") on a third and fourth symbol.

## Consequence, applied to the plan

- `EF2/code/plan.py` already records the switch to `EF6/code/placebo_w.py` with kinds
  `placebo_random_legal` and `placebo_session_shuffle`, both amendments made **before** any expectancy
  existed and both recorded as amendments.
- Every EF2 row carrying a control will state **the row's own long share**, so the reader can see what a
  direction-sensitive construction would have destroyed on that row. `placebo_session_shuffle` is
  direction-preserving by design, so this is a disclosure rather than a correction.
- The `rth_only=False` arm's controls must come from `schedule_random_legal`. If any row's control is
  built by the upstream `_schedule_random`, that row is not reportable.
