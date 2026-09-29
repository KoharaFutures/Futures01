# EF2 / Burst 11 — Tier A2: the one form of the deliverable whose width this span can settle

Pre-registered **before** any expectancy was measured, in response to `EF6-01`'s search-budget
arithmetic. Recorded in `EF2/code/plan.py` as `TIER_A2` and emitted to `EF2/data/plan.json`.

## The arithmetic that forces it

Inverting `free_t = sqrt(2·ln n)` against `t = SR·sqrt(Y)` gives the widest search a span can settle at
a given **true** Sharpe: `n_max = exp(SR²·Y/2)`. On 718.83 days (Y = 1.968):

| assumed true annual Sharpe | max answerable search width |
|---|---|
| 1.0 | **2** |
| 1.5 | **9** |
| 2.0 | **51** |
| 3.0 | 7,022 |

**My strategy-level screen is 5,152 MGC / 5,584 MCL arms**, so a strategy-level top 10 is answerable
only at a true Sharpe near 3. The fix is **not** to screen less — the deflation cost is paid on what was
screened, not on what was reported — but to *also* pre-register a question whose natural width is small
enough. Aggregating the **same trades** to a coarser unit does that without running a second search:

| unit | n per symbol | `free_t` | required annual Sharpe | answerable at SR 2? |
|---|---|---|---|---|
| 2 timeframes × 2 `rth` arms | 4 | 1.665 | **1.19** | yes |
| Tier A, the 6 hypotheses | 6 | 1.893 | **1.35** | yes |
| 4 cells × 2 `rth` arms | 8 | 2.039 | **1.45** | yes |
| **13 groups × 2 primary timeframes** | **26** | **2.553** | **1.82** | **yes** |
| 13 groups × 2 tfs × 2 `rth` arms | 52 | 2.811 | 2.00 | borderline |
| 13 groups × 4 cells × 2 arms | 104 | 3.048 | 2.17 | no |
| the strategy-level screen | 5,152 | 4.135 | **2.95** | no |

`[measured: EF6/code/deflation.threshold(n, 718.83)]`

**26 is the cut I am registering.** A Sharpe of 1.82 is high but ordinary for a real futures edge; 2.95
is not a thing that exists sustainably. Going finer than 26 (to 52 or 104) buys resolution I cannot pay
for; going coarser than 26 stops answering the question the brief asks, which is per-symbol **and**
per-timeframe.

## Why this is the right unit and not a convenience

**It is the form the published corpus already reports.** `scan_reports/2026-09-24` Part B is a
per-symbol **group** table — *"MCL: MOMENTUM, 60m and 240m, 66 observations, 97% positive, beat its
control on both arms"*; *"MGC: VWAP, TREND, MOMENTUM, MULTI_TIMEFRAME, 60m only"*. So Tier A2 is
directly comparable to the published claim, and that claim becomes a **testable prediction** rather than
a summary. That is worth more than a fresh strategy ranking, because the corpus's own verdict is that
strategy-level ranking does not persist (Jaccard 0.081; the top-ranked strategy changed in 58 of 70
walk-forward folds) while nobody has tested whether the **group-level** read persists under this
session rule.

**One directional call, and it is the only prior EF2 borrows.** MCL MOMENTUM at 60m and 240m is
registered as predicted **positive**. Everything else in Tier A2 is two-sided and un-directed.
`DISC2`'s counter is carried with it: a borrowed idea's honest `n` is not 1 either, because the
literature's survivors are the output of a large undocumented collective search.

## The pooling rule, fixed now because it is the place a result could be manufactured

**Trade-weighted mean of net R over every arm in the pair.** An equal-weighted mean over arms lets a
3-trade arm count as much as a 300-trade one, and F4 measured medians of 4–5 fires per live MCL 60m arm
against a p90 of 111 — so the weighting choice is not cosmetic on this substrate. Both are computed; the
trade-weighted one is the **registered** statistic and the equal-weighted one is reported beside it as a
sensitivity.

**The control is pooled the same way**, so a group's expectancy is read against a group-sized control
rather than against a single row's.

## Two structural holes in the table, which are reported as VOID and not as zero

From burst 03's population: **5 of the 52 (group, cell) combinations have zero surviving arms, identically
on both symbols** — `MULTI_TIMEFRAME` in `f60__p60`, `f240__p240` and `f60_240__p240`, and
`VOLUME_PROFILE` in both 240m cells.

And one of them is worse than a hole in my frames — it is unaskable in this programme:

> **`MULTI_TIMEFRAME` at 240m cannot be tested on MCL at all.** Its two required SIGNALs are VOID at the
> frame's top timeframe, so making them live at 240m needs a timeframe **above** 240m in the frame. The
> only candidate is 1440m, and **`MCL_1440m.jsonl` holds exactly one row** `[measured]`. `CL=F` is not a
> substitute (0.95¢ mean close difference, 4¢ at worst — fine for context, wrong for a stop).

So the honest Tier A2 table for MCL has 13 × 2 = 26 slots of which `MULTI_TIMEFRAME @ 240m` is
structurally empty, and `VOLUME_PROFILE @ 240m` likewise on both symbols. **A `VOID` cell is reported as
`VOID`, never as 0.00R** — that is the distinction the shared vocabulary was extended for, and it is the
distinction that makes the difference between "we measured absence" and "the detector never fired".

## What this does not change

The strategy-level top 10 is still produced, still ranked on expectancy in R, still carrying
`free_t = 4.135 / 4.154` and "needs Sharpe 2.95 / 2.96" on every row, still with a placebo beside each
row and its forward behaviour. Tier A2 sits **beside** it as the tier that can actually carry a claim,
and the two are reported with their different thresholds visible rather than pooled into one list.
