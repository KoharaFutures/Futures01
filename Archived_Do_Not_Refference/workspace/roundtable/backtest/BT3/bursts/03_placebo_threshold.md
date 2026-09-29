# BT3 burst 03 — the placebo threshold, and park

**2026-09-27.** One measurement, one withdrawal, then parked by the account owner. No new algorithm.

## The challenge

The coordinator checked my own arithmetic and got a different answer. I had reported the placebo
comparison as a null because "p = 0.0288 (deaths) and p = 0.0131 (`taken`) do not clear 2.039 free
t-units". Converted through the normal quantile those are **|z| = 2.186 and 2.480** — both *above*
the threshold. It offered three possibilities: my conversion accounted for discreteness in a way
the report did not state; the placebo faces a different threshold; or it genuinely clears and my
conclusion needs weakening.

## The answer: the third, and the premise needs correcting too

**(1) is not it.** I did not account for discreteness — I simply compared a p-value to a t-value,
which is an operation with no meaning. And discreteness pushes *against* me, not for me: the mid-p
correction gives |z| = 2.250 and 2.511, i.e. **larger**, because an exact test on a discrete lattice
is conservative `[measured: code/paired_tests.py mid_p() vs binom_two_sided()]`. So discreteness
could never have been the explanation.

**(2) is not it.** The placebo is one of the comparisons I counted in my own search size, so it
faces the same threshold.

**(3), and the sentence is withdrawn rather than weakened.** But before weakening anything I checked
whether my placebo could ever have licensed the conclusion, and it could not.

## The second error, which is the one that mattered

**A global permutation of R is not a signal-layer placebo.** It destroys three associations at
once, and only the first is anywhere near the entry `[measured over the 21,954 cached rows]`:

| destroyed | real | after global permutation |
|---|---|---|
| R ↔ exit reason | STOP **−0.870**, TARGET **+1.478** | −0.063 / −0.069 |
| R ↔ duration | `mins == 0` → −0.792, `> 1440` → +0.348 | flat |
| R ↔ symbol (dollar risk per contract varies 3×, $98.5 MCL to $289 MGC) | −0.111 … −0.033 | flat |

The second and third are exit-geometry and contract facts. PIPELINE §4 asks for the *signal* layer
replaced; I had replaced the *outcome* layer and then drawn a conclusion about the entry from it.

## What I did instead of arguing about the threshold

Added two **stratified** placebos — permute R only within strata holding those associations fixed,
so a STOP's R can land only on another STOP of the same symbol and timeframe, and the only thing
destroyed is the time-ordering of outcomes. Verified to work: both stratified arms reproduce STOP
−0.870 / TARGET +1.478 exactly while the global arm flattens them. Search size rose from 8 to 12,
so `free_t` rose from 2.039 to **2.229** — I raised my own bar rather than defend the arm I had, and
it does not rescue the failed comparison.

| placebo | deaths \|z\| | `taken` \|z\| | `taken` diff |
|---|---|---|---|
| global | 2.186 (mid-p 2.250) | **2.480 CLEARS** | −19 |
| stratified (symbol, tf, reason) — 40 strata, median 236 | 1.549 | **0.000** (100 vs 99) | +3 |
| stratified (strategy, reason) — 695 strata, median 10 | 1.239 | **4.161 CLEARS** | −19 |

**On deaths all three fail to clear and all three agree** in direction and magnitude (discordant
25/11, 22/12, 20/12 — the real stream always dies more). The global arm's 2.186 against 2.229, with
mid-p 2.250, is **on the threshold and I claim neither side of it.**

**On `taken` the three constructions disagree across the threshold, from 0.000 to 4.161**, and the
disagreement is explicable, which is why I recorded the mechanism rather than averaging it away:
the medium strata are large, so permuting within them mostly exchanges R **between the 22 correlated
arms firing at the same instant** — which the account cannot distinguish, since whichever arm wins
the symbol slot draws a similar R either way, hence the exact null. The tight strata are confined to
one strategy, so permuting within them moves R **across time**, between the three disjoint slices,
changing *when* that strategy's losses arrive. **The account is sensitive to the temporal clustering
of one strategy's own outcomes, not to the cross-sectional assignment of outcomes at an instant.**
That is your pooling finding turning up on a third instrument.

## What I withdrew, and what replaces it

Withdrawn: *"which trades the governors delete is a property of the stop distribution and the
calendar, not of the entry."* Replaced by a statement of what the design can and cannot separate:
the deletion count **does** depend on the sequence of realised outcomes, every arm that differs
from the real one differs in the same direction, **and this design cannot attribute that to the
entry** because no arm replaces the signal layer. Entry-dependence is **untested here, not
refuted**; settling it needs random entry bars through the same exits and governors, i.e. a new
backtest.

Direction, recorded because it is unflattering under every reading: the real stream dies more often
and takes fewer trades than every placebo that differs from it. Nothing here is an edge claim.

## What survives untouched

The two survival results are comparisons between **governor configurations**, not against a
placebo: volatility multiplier |z| = **6.164**, eligibility multiplier |z| = **5.543**, against
free_t = 2.229. Tier A and Tier B are derived from `config.py`, `risk/manager.py` and the stop
distribution alone.

## The methodological fix, so this cannot recur silently

`code/paired_tests.py` now has `z_from_p` and `mid_p`, and **every row of every table prints the z
beside the p with an explicit `CLEARS / does not` verdict against the computed `free_t`.** The
docstring states the error in the operation directly, because "0.029 is not less than 2.039" is the
kind of thing that reads as a comparison when it is not one.

## What I banked before parking

- `ALGOS.md` — controls section rewritten with the error, the three placebo arms and the
  withdrawal; the search-size bullet corrected to 12 tests and |z|-against-free_t; and a
  `## PARKED 2026-09-27` section written for a cold reader.
- `code/governor_replay.py` — `permute_r()` with optional stratification; three placebo ensembles.
- `code/paired_tests.py` — `z_from_p`, `mid_p`, six comparisons, explicit verdicts.
- `msgs/16_BT3_R3_placebo-correction.md` — withdrawing the claim to R3 before it rules on it, since
  my cycle-2 ask stated the placebo as a null, and telling it that the 0.362 I gave it for the
  look-ahead was my bug and needs replacing if cited.

## Where I stopped

At the in-flight question, as instructed. No ALGO-2, no `CONTROL`/`CONTROL_FADE`, no gated
block-vs-iid re-run. **ALGO-1's Tier C remains UNREPORTABLE pending R3's cycle-2 ruling**, which is
the single next step recorded in `PARKED`.

`python3 code/checks.py` → all 5 pass. `python3 -m pytest -q tests/test_bt3_governor_replay.py` →
10 passed.
