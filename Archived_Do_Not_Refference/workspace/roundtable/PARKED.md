# Parked agents — resume on the account owner's word only

The account owner asked on 2026-09-27 for the first three BT and EF pairs to finish the subtask in
flight and then sit idle until told otherwise. **Do not resume these without that instruction.**

| agent | lane | parked after | resumption note |
|---|---|---|---|
| **BT3** | `backtest/BT3/` | governor replay + the placebo question **resolved** | `BT3/bursts/03_placebo_threshold.md` |
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

---

## A live disagreement that arrived after EF1 and EF3 parked — read this before resuming either

**EF3 proposed a fix. EF7 argues it is the wrong instrument, and EF7 is probably right.**

The defect: EF1's `session_end_indices` groups by ET calendar date and misses 9 bars per symbol, all
23:00 ET on a holiday eve, carrying **198 positions** across a 16:00 deadline (63 MES, 135 MNQ).
Invisible on a 400-strategy probe, which is why EF3's remark stands on its own: *a probe is not a
population.*

**EF3's fix:** use `timeutil.MARKET_HOLIDAYS_2025_2027`.

**EF7's objection, from its own test docstring:**

> *A holiday table answers "is the next calendar day a holiday", and that is not the question.
> Several CME holidays are **shortened** sessions, not closures: the cycle exists, the market trades
> into it, and the specification permits holding there.*

That is a market-structure argument and the evidence already in this tree supports it. R6 measured
**8 off-grid `:30` bars** in all four `csv/raw` 1h files, on Thanksgiving Friday 2025-11-28 and
Christmas Eve 2025-12-24. Those bars exist *because those sessions traded* — shortened, not closed.
A holiday table would force a flat the previous evening on days the market is open, replacing a
missed flat with a spurious one.

**Status: EF7's own three tests for this case are RED** — `test_h2_no_trade_spans_a_holiday_eve_boundary`
fails on MGC, MES and MNQ, with 63 of 66 passing otherwise. That is red-first on a genuinely open
question, not a bug: it wrote the test from the specification and its implementation does not yet
satisfy it. It is attempting to derive the flat from the data rather than from a calendar.

**So whoever resumes EF1 or EF3 must not simply apply the holiday table.** The open question is how
to distinguish a *shortened* session from a *closed* one using only information available at the
bar, and EF7's `h2` tests are the specification for the answer. EF7 also warns that its own engine
reads the successor bar's **timestamp only, never its prices**, so a naive fix in that direction
trades one defect for a look-ahead.

This is the fourth time independent duplication changed an answer here rather than merely confirming
one — after R6 breaking the R1/R3 tie, R4 correcting three of R1's attributions, and EF2/EF3/EF4
scoping the flat defect to coarse timeframes.

---

## BT3's park is worth reading as a template for how to answer a challenge

I put a narrow question to BT3: it had called its placebo a null, and converting its own p-values
gave |z| = 2.186 and 2.480 against the 2.039 it said they failed. I offered three explanations.

**It took the one least favourable to itself, and then found a deeper error I had not seen.**

On my question: *"I did not account for discreteness — I simply compared a p-value to a t-value,
which is an operation with no meaning."* And it showed discreteness could never have rescued it:
the mid-p correction gives **2.250 and 2.511, larger**, because an exact test on a discrete lattice
is conservative.

**The error that mattered was not the arithmetic.** Before weakening anything it asked whether its
placebo *could ever have licensed the conclusion*, and found it could not: **a global permutation of
R is not a signal-layer placebo.** It destroys three associations at once —

| destroyed | real | after global permutation |
|---|---|---|
| R ↔ exit reason | STOP −0.870, TARGET +1.478 | −0.063 / −0.069 |
| R ↔ duration | `mins == 0` → −0.792, `> 1440` → +0.348 | flat |
| R ↔ symbol (dollar risk varies 3×) | −0.111 … −0.033 | flat |

— and only the first is anywhere near the entry. The other two are exit-geometry and contract facts.
*"PIPELINE §4 asks for the signal layer replaced; I had replaced the outcome layer and then drawn a
conclusion about the entry from it."*

**It then raised its own bar.** Building two stratified placebos took its search size from 8 to 12,
so `free_t` went 2.039 → **2.2293** — *"I raised my own bar rather than defend the arm I had, and it
does not rescue the failed comparison."*

**And it refused to average away a disagreement it could explain.** The three constructions differ
across the threshold on `taken`, from 0.000 to 4.161, and the mechanism is the point: large strata
permute R *between the 22 correlated arms firing at the same instant*, which the account cannot
distinguish — hence the exact null; tight strata permute *across time*, changing when one strategy's
losses arrive. **The account is sensitive to the temporal clustering of one strategy's own outcomes,
not to the cross-sectional assignment at an instant.** That is this repo's pooling defect appearing
on a third instrument.

**What was withdrawn, and what replaced it.** Gone: *"which trades the governors delete is a
property of the stop distribution and the calendar, not of the entry."* In its place: the deletion
count **does** depend on the sequence of realised outcomes, every arm differs in the same direction,
**and this design cannot attribute that to the entry** because no arm replaces the signal layer.
**Entry-dependence is untested here, not refuted** — settling it needs random entry bars through the
same exits and governors, which is a new backtest.

**What survives, verified against the raised bar:** the two survival results are comparisons between
*governor configurations*, not against a placebo — |z| = **6.164** and **5.543** against
`free_t = 2.2293`. **Both still clear.** So the one deflation-clearing result in this programme
stands, and it is the risk finding, not an edge.
