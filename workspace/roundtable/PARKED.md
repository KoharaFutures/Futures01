# Parked agents — resume on the account owner's word only

The account owner asked on 2026-09-27 for the first three BT and EF pairs to finish the subtask in
flight and then sit idle until told otherwise. **Do not resume these without that instruction.**

| agent | lane | parked after | resumption note |
|---|---|---|---|
| **BT3** | `backtest/BT3/` | governor replay, cycle 2 + the placebo-threshold question | `BT3/ALGOS.md` → `## PARKED` |
| **EF1** | `edge/EF1/` | the flat-enforcement fix on `EF1-H1` | `EF1/FINDINGS.md` → `## PARKED` |
| **EF2** | `edge/EF2/` | population + firing census, MGC/MCL 60m | `EF2/FINDINGS.md` → `## PARKED` |
| **EF3** | `edge/EF3/` | population + firing census, MES/MNQ 60m | `EF3/FINDINGS.md` → `## PARKED` |

Each was told to complete only what was in flight, bank everything to disk, and write a
`## PARKED <date>` section written for a reader arriving cold: current state, what remains, the
single next step, and anything that existed only in its head.

## Still running

**BT4** (`align_bucket` blast radius, D50) · **BT5** (R5's S2 activity stratification) ·
**BT6** (daily VWAP collapse, D52) · **EF4** (scalp MGC+MCL) · **EF5** (scalp MES+MNQ) ·
**EF6** (controls: `EF6-H1..H4`) · **EF7** (independent session harness).

## Why EF7 was not parked with EF1

EF1 is the harness gate for EF4 and EF5, which continue. With EF1 parked, **EF7 is the only harness
work left**, and the gate cannot be abandoned while two agents still depend on it. EF7 has been
reimplementing the rule independently without reading EF1's code — which is exactly the arrangement
that caught EF1's defect in the first place, three times over from EF2, EF3 and EF4.

## What changed under the parked agents while they ran

Both matter to whoever resumes them, and both are in `edge/EDGE_BRIEF.md`:

1. **The 240m and 1440m cells cannot carry the session rule.** The window is 22 h = 1320 min and
   `1320 = 2³·3·5·11`, so 5/15/30/60/120 divide it while 240 gives 5.5 and 1440 gives 0.917. This
   withdrew **half of EF2's and half of EF3's assignment** through no fault of theirs, and it
   explains EF3's observation that EF1's violations were all at 240m. The swing programme is 60m
   only.
2. **The thresholds are harder than the brief first said.** `EF6-H3` computes them from actual
   search size: swing 60m needs an annualised Sharpe of **2.498**, scalp **9.59**. The earlier 2.96
   was the floor for a single pre-registered hypothesis, not for a search.

## State of the edge programme at parking

No profitability number has been reported by any agent, and that is correct rather than incomplete:
board rule `R-13` applies `R-5` to a harness exactly as to an algorithm, and `EF1-H1` has not
validated. Five agents hold populations and censuses. The gate is `MGR-T19`.
