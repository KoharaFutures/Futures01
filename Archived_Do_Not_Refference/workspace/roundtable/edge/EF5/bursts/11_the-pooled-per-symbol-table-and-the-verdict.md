# EF5 burst 11 — the pooled per-symbol table, and the sentence that ends it

The deliverable asked for is "a top 10 per symbol for the scalp setting". A per-symbol list pools that
symbol's three timeframes and both `rth_only` arms into one table, so the search width is the symbol's
whole declared population and the threshold follows.

`[measured: EF5/out/PROVISIONAL_measure_all.json, pooled by symbol, reals and placebos in one table,
ranked on the pre-registered score]`

## MES, pooled — search 10,134, `free_t = 4.295`, required annualised Sharpe **10.79**

```
pooled table: 90 reals + 41 placebos = 131   placebo share 0.31
best placebo rank 4   |   E[best placebo rank] under the null = (N+1)/(k+1) = 3.14
```

| rank | kind | cell | group | n | exp R net | t | implied ann. SR | win | PF | R/R | maxDD/avgDD | Sortino | CW/CL | avg min | MAE/MFE | L/S | stop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | real | MES 15m RTH | MOMENTUM | 42 | +0.3370 | 2.11 | 5.29 | .619 | 2.09 | 1.29 | 5.95/2.56 | 0.61 | 10/5 | 102 | +0.66/+1.49 | 21/21 | ATR |
| 2 | real | MES 15m RTH | LIQUIDITY | 29 | +0.4023 | 2.09 | 5.24 | .655 | 2.50 | 1.32 | 4.50/2.14 | 0.75 | 6/4 | 83 | +0.68/+1.56 | 18/11 | ATR |
| 3 | real | MES 15m SESSION | LIQUIDITY | 29 | +0.4023 | 2.09 | 5.24 | .655 | 2.50 | 1.32 | 4.50/2.14 | 0.75 | 6/4 | 83 | +0.68/+1.56 | 18/11 | ATR |
| **4** | **placebo_random** | MES 30m SESSION | LIQUIDITY | 43 | +0.3256 | 2.08 | 5.23 | .628 | 2.11 | 1.25 | 3.34/1.39 | 0.59 | 4/4 | 213 | +0.66/+1.54 | 22/21 | ATR |
| **5** | **placebo_random** | MES 15m RTH | TREND | 21 | +0.4886 | **2.60** | **6.53** | .714 | 3.56 | 1.42 | 1.16/0.67 | 1.18 | 5/2 | 159 | +0.43/+1.18 | 13/8 | ATR |
| 6 | placebo_random | MES 15m SESSION | LIQUIDITY | 61 | +0.2722 | 1.88 | 4.72 | .574 | 1.72 | 1.28 | 5.03/1.71 | 0.42 | 7/3 | 139 | +0.79/+1.50 | 33/28 | ATR |
| 7 | placebo_random | MES 5m RTH | MULTI_TIMEFRAME | 49 | +0.2914 | 1.74 | 4.38 | .531 | 1.78 | 1.58 | 6.25/2.74 | 0.45 | 4/7 | 40 | +0.88/+1.66 | 33/16 | ATR |
| 8 | real | MES 30m SESSION | MULTI_TIMEFRAME | 20 | +0.4236 | 1.37 | 3.44 | .650 | 2.11 | 1.13 | 2.81/1.07 | 0.65 | 6/2 | 296 | +0.90/+2.07 | 10/10 | ATR |
| 9 | real | MES 30m SESSION | MULTI_TIMEFRAME | 23 | +0.3861 | 1.39 | 3.50 | .652 | 2.02 | 1.08 | 2.50/0.95 | 0.60 | 6/2 | 305 | +0.88/+2.07 | 12/11 | ATR |
| 10 | real | MES 30m SESSION | MOMENTUM | 59 | +0.2219 | 1.78 | 4.46 | .644 | 1.69 | 0.93 | 4.92/2.15 | 0.39 | 5/4 | 236 | +0.70/+1.38 | 27/32 | ATR |

**Best placebo at rank 4 against a null of 3.14 — indistinguishable from chance.** And the **largest t in
MES's whole pooled table belongs to a placebo** (2.60, rank 5) — larger than every real row.

**A defect in the pooling itself, found here and worth carrying.** Ranks 2 and 3 are the **same rule set,
in the two different `rth_only` arms, with byte-identical metrics** (n=29, exp +0.4023, t +2.09,
maxDD 4.50). Every one of its entries was inside RTH anyway, so flipping `rth_only` changed nothing and it
appears twice. My clone collapse is **per cell**, so it cannot see a cross-arm duplicate. **Pooling arms
requires cross-arm clone collapse on the realised ledger, and without it a pooled top 10 double-counts.**
This is D48's failure *signature* arriving by a different route — two arms whose difference is exactly
zero — except here it is not an id collision, it is a genuine behavioural identity, and the correct
handling is to collapse it and report the pair as one row with a note that the arm made no difference to
it.

## MNQ, pooled — search 10,926, `free_t = 4.313`, required annualised Sharpe **10.83**

```
pooled table: 154 reals + 138 placebos = 292   placebo share 0.47
best placebo rank 1   |   E[best placebo rank] under the null = 2.11
```

| rank | kind | cell | group | n | exp R net | t | implied ann. SR | win | PF | R/R | maxDD | L/S | stop |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **placebo_random** | MNQ 5m SESSION | MULTI_TIMEFRAME | 54 | **+0.7766** | **3.82** | **9.59** | .685 | 3.43 | 1.57 | 3.17 | 28/26 | ATR |
| 2 | real | MNQ 15m SESSION | MULTI_TIMEFRAME | 40 | +0.6449 | 3.12 | 7.83 | .625 | 2.93 | 1.76 | 3.15 | **29/11** | ATR |
| 3 | real | MNQ 15m SESSION | MULTI_TIMEFRAME | 41 | +0.5848 | 2.44 | 6.14 | .610 | 2.45 | 1.57 | 6.49 | **32/9** | ATR |
| 4 | real | MNQ 15m SESSION | MULTI_TIMEFRAME | 45 | +0.5199 | 2.66 | 6.68 | .578 | 2.40 | 1.75 | 5.62 | **34/11** | ATR |
| 5 | real | MNQ 15m SESSION | MULTI_TIMEFRAME | 46 | +0.4959 | 2.72 | 6.83 | .630 | 2.37 | 1.39 | 5.39 | **37/9** | ATR |
| **6** | **placebo_random** | MNQ 15m RTH | MOMENTUM | 21 | +0.7665 | 2.43 | 6.12 | .619 | 3.17 | 1.95 | 1.24 | 12/9 | ATR |
| 7 | real | MNQ 15m SESSION | MULTI_TIMEFRAME | 45 | +0.4776 | 2.11 | 5.31 | .578 | 2.10 | 1.53 | 8.87 | **36/9** | ATR |
| 8 | real | MNQ 15m SESSION | MULTI_TIMEFRAME | 49 | +0.4589 | 2.57 | 6.46 | .612 | 2.20 | 1.39 | 6.42 | **40/9** | ATR |
| **9** | **placebo_random** | MNQ 5m RTH | VOLUME_PROFILE | 38 | +0.5131 | 2.60 | 6.52 | .605 | 2.55 | 1.66 | 4.15 | 33/5 | ATR |
| **10** | **placebo_shuffle** | MNQ 15m SESSION | MOMENTUM | 50 | +0.4314 | 2.20 | 5.53 | .520 | 1.99 | 1.84 | 6.41 | 23/27 | ATR |

**A placebo tops MNQ's pooled table**, against a null that expected the best placebo at rank 2.11 — so
rank 1 is not even a surprise. **Four of MNQ's top 10 are placebos.** And every real row in the top 10 is
MULTI_TIMEFRAME at 15m SESSION with a long share of **0.73–0.82** on a tape that rose 12.19% (burst 10).

## The sentence that ends it

> **The largest t-statistic anywhere in EF5's 21,060-strategy search is 3.82, and it belongs to a
> placebo.** It sits below the MNQ cell threshold of 3.875 and well below the pooled 4.313, so nothing —
> real or control — clears deflation in either symbol. On a 0.1585-year span that t implies a sustained
> annualised Sharpe of 9.59, which is not a number that exists in listed futures; it is the signature of
> 41 trading sessions.

## Verdict, both symbols

**EF5 publishes no ranked top 10 for MES and none for MNQ.**

* **MES:** best placebo at rank 4 against a null of 3.14 — the ranking is indistinguishable from chance,
  and the table's largest t is a placebo's.
* **MNQ:** best placebo at **rank 1** against a null of 2.11, four of ten top slots are placebos, and the
  real rows that remain are a long-bias proxy on a rising tape.
* **Both:** zero rows clear `free_t` at any denominator — cell (3.855/3.875), pooled per symbol
  (4.295/4.313) or whole-EF5 (4.462). Largest real t is 3.116.
* **Three arm-cells hold ≤ 8 qualifiers, so a top 10 does not exist in them at all.**

**What EF5 hands over instead is burst 10 §2: the qualifying count and the universe's expectancy net of
costs per arm-cell, with the placebo universe beside it.** Seven of twelve of those are negative. That is
a real, cleanly-measured result about the index complex at scalp timeframes under the 18:00→16:00 rule,
and nobody has stated it before.
