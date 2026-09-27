# BT3 burst 02 — ALGO-1 fidelity cycle 2: correct DIVERGENT, re-ask

**2026-09-27.** One fidelity cycle. No new algorithm.

## Why this burst exists

R3 ruled ALGO-1 **DIVERGENT** in `msgs/03_R3_BT3_re-verify-ALGO-1.md` and answered my eight
questions in `msgs/10_R3_BT3_re-verify-ALGO-1-questions.md`. PIPELINE §4 is explicit about what
follows a DIVERGENT verdict: fix the code, then ask again. That is this burst and nothing else.
I did not start ALGO-2 even though R3 pre-registered one for me.

## What I read

`msgs/03_R3_BT3_re-verify-ALGO-1.md` (348 lines), `msgs/10_R3_BT3_re-verify-ALGO-1-questions.md`
(266), `msgs/09_manager_BT3_requests-ruling.md` (126), and the updated `BRIEF.md` data ruling.

## What I changed

All five of R3's ranked items, plus the three conditions attached to its Q1 and the Q5 reframing.
The table is in `ALGOS.md` under "What R3 ruled DIVERGENT, and what I changed". The two that moved
numbers:

- **`volatility=row["vol"]`** — the material divergence. The ×0.70 for HIGH/EXTREME lives inside
  stage 7, which I had declared IN scope, and the artefact carries the label for 27.9% of the
  stream. Static floor deletion **35.38% → 41.19%**; R3's independently predicted +1,272 lands at
  **1,275**.
- **The intra-timestamp barrier** — 2,900 rows have `mins == 0.0` with mean R −0.79, and one
  timestamp carries 74 rows, so the governors had been assessing row #40 while holding the
  realised outcomes of rows #1–39 at the same instant.

And three that changed what the numbers *mean*: the seeded order is now primary over 200
permutations with the lexicographic key demoted to a labelled anchor (R3 showed the
`symbol`-second key front-loaded the account with exactly the symbols that survive the floor);
`key=parse_ts` instead of the ISO string; and the absorbing boundary is now a primary statistic,
reproduced in code for both eligibility arms.

## A defect in my own fix, which is the thing I most want on record

My first implementation of the barrier restructured the loop to iterate timestamp *groups*, which
made `flush()` run once per group — so **`barrier=False` silently became a barrier too.** That run
reported "removing the look-ahead changes nothing, p = 0.362", which was a comparison of the
barrier **with itself**. I only caught it while writing a synthetic test for the barrier
semantics, which is an argument for writing the test before believing the arm.

Fixed (per-row flush, as the pre-barrier code did) and pinned by two tests in
`tests/test_bt3_governor_replay.py`. **Corrected reading: the leak inflated the trade count by
~17 trades per seed (p = 2.34e-06) and did not affect survival (p = 0.761).** R3's mechanism was
exactly right — a position that vanishes before the next same-instant row is assessed never
occupies a concurrency slot, so the leak manufactures capacity.

## What the corrected replay says

Full detail in `ALGOS.md`, now split into three tiers by how much the fidelity verdict can move
it. The three things worth pulling out:

1. **The structural result, which needs no trade data: the shipped `AccountConfig` has a
   dead-but-not-failed absorbing state.** Past a $2,800 drawdown the budget is $21.60 against a
   $25 minimum, stage 7 refuses everything before `contracts_for` runs, equity freezes and
   `peak_equity` never falls — with **$2,200 of the $5,000 failure allowance never spendable**.
   R3 solved this; I reproduced it in code because it is now the headline, and extended it to the
   honest arm ($2,334, 46.7% of the allowance). **`max_total_drawdown` is unreachable from above
   the boundary**, so risk-of-ruin as this repo models it is measuring the wrong event.
2. **At this account size every governor that shrinks position size is net protective**, because
   realised drawdown scales with size faster than the absorbing boundary moves. Volatility
   multiplier pinned → 41.0% of orderings die; on → 13.0% (p = 7.08e-10). Eligibility ×0.5 →
   0.0% (p = 2.98e-08). `max_drawdown / absorbing_boundary` is 1.100 / 0.954 / 0.873 across the
   three arms and is the whole predictor. **Two governors that look like Channel-4a variance
   transforms are Channel-2 survival effects**, because survival is a threshold on the path.
3. **The integer floor does 98.58% of the refusing** (16,184 of 16,417) at the per-strategy unit,
   and the four daily governors the finding is named after do **1.26%**, two of them never firing.
   **18 of 22 MGC 4h strategies and 11 of 22 MNQ 4h strategies take not one trade.**

And one number I have deliberately hedged: the floor's 41.19% is reported with an elasticity
curve, not as a constant. Elasticity ≈ **2.0** near $240, and at R3's original $375/$500 the
figure is 14.7%/7.5%. The qualitative claim is robust; the percentage is a statement about one
account size.

## Where I had to contradict R3

Its Q5 prediction — *"the honest arm dies, at 47% of its permitted drawdown, and the neutral arm
survives only by $53"* — reverses once the volatility fix R3 itself demanded is in. The honest arm
dies in **0 of 200** orderings and the neutral arm in **26 of 200**. R3's arithmetic was correct on
the cycle-1 numbers it had. I reported the reversal rather than restating R3's finding, and made
it question 1 of the re-ask rather than deciding it myself.

Also: R3 predicted the per-strategy distribution would be "eight tight clusters". The cells do
separate cleanly and in the floor's own ordering — but within-cell IQRs run to **39.3 points**, so
two arms of the same base condition on the same symbol and timeframe survive at 13% and at 100%.
Half confirmation, half new observation, and I asked which.

## What I asked

`msgs/15_BT3_R3_verify-ALGO-1-v2.md`, four questions, on the difference only as R3 requested:
the reversed Q5 sign, the within-cell spread, whether R3 would have chosen its second barrier
option instead, and whether the budget-elasticity caveat belongs in R3's file or mine.

## Where I stopped and why

At one fidelity cycle. **ALGO-1 is ASKED again and Tier C remains unreportable.** Tier A and Tier
B are reportable independently of any verdict, because they are derived from `config.py`,
`risk/manager.py` and the stop distribution alone.

I did not start the `CONTROL`/`CONTROL_FADE` 32-strategy portfolio R3 pre-registered as ALGO-2,
did not touch any of R3's Tier-1 six (blocked by the manager's `R-6` pairing rule and the A-2
prerequisite), and did not re-run the block-vs-iid measurement (`MGR-T8` is GATED behind the D44
fix, which is the parent's `MGR-T16`).

`python -m pytest -q tests` → **827 passed**, of which 10 are mine.
