# EF5 burst 10 — the qualifying universe per cell (the deliverable), and why MULTI_TIMEFRAME tops MNQ 15m

## 1. A protocol correction I am declaring rather than quietly applying

My pre-registered ranking gate included `max_consecutive_losses <= 12`. **That gate is not
scale-invariant and it removes exactly the rows carrying the most evidence.** For n trades at loss rate
q the expected longest losing run is about `log(n(1−q))/log(1/q)`, so a fixed cap penalises high-n rows.
Measured across my own qualifying universes, observed against arithmetically expected:

| arm-cell | mean n | mean observed max consecutive losses | expected at that n and win rate |
|---|---|---|---|
| MES 5m SESSION | 87.4 | 7.22 | 6.21 |
| MNQ 5m SESSION | 98.0 | 7.32 | 6.63 |
| MNQ 15m RTH | 62.7 | **10.86** | 6.57 |
| MNQ 30m RTH | 41.5 | **9.62** | 6.25 |
| MES 30m SESSION | 35.4 | 3.69 | 3.58 |
| MNQ 15m SESSION | 60.7 | 5.44 | 5.14 |

Observed exceeds expected in every cell (so the rows are slightly *worse* than a coin flip on run
length — consistent with serial dependence in the trades), but the cap's effect is a function of n, not
of durability. **The gated counts stay on disk in `out/PROVISIONAL_measure_all.json` and the ungated
universe below is the reported deliverable.** Both are published; nothing is replaced silently. I am
stating that I noticed this after seeing the gate shrink MES 5m SESSION from 107 rows to 15.

## 2. The deliverable: the qualifying universe per arm-cell

`[measured: EF5/code/universe.py → EF5/out/universe.json; 20-trade floor, clone collapse on the realised
ledger, NO durability gate; EF1's `SessionWindowEngine`; expectancy net of costs (`Trade.net_r`)]`

EF6 burst 07's instruction, adopted: **do not rank; report the whole qualifying universe's expectancy
per cell with the qualifying count beside it.**

| arm-cell | qualifying universe | mean exp R **net** | median | % positive | **placebo universe** | IS 60% | OOS 40% | best row t | best row implied ann. Sharpe | long share | clock-close |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MES 5m RTH | 38 | **−0.0452** | −0.0562 | 34% | −0.1269 | −0.0687 | +0.0283 | 1.100 | 2.76 | 0.507 | 13.1% |
| MES 5m SESSION | 107 | **−0.1913** | −0.1634 | **14%** | −0.2116 | −0.2640 | −0.0864 | 1.277 | 3.21 | 0.537 | 5.0% |
| MES 15m RTH | **15** | +0.0745 | +0.0006 | 53% | −0.0433 | −0.0376 | +0.3088 | 2.105 | 5.29 | 0.524 | 36.2% |
| MES 15m SESSION | 50 | −0.0464 | −0.0291 | 34% | −0.1462 | −0.0262 | −0.0207 | 2.085 | 5.24 | 0.521 | 18.7% |
| MES 30m RTH | **7** | +0.1031 | +0.0621 | 100% | −0.1877 | +0.1376 | +0.0611 | 1.533 | 3.85 | 0.563 | **53.1%** |
| **MES 30m SESSION** | 35 | **+0.1211** | +0.1354 | 86% | −0.1458 | +0.1469 | +0.0984 | 1.869 | 4.70 | 0.478 | 34.1% |
| MNQ 5m RTH | 48 | −0.0439 | −0.0279 | 44% | **+0.0129** | −0.1423 | +0.1352 | 2.380 | 5.98 | 0.582 | 7.5% |
| MNQ 5m SESSION | 156 | −0.0530 | −0.0352 | 40% | −0.0555 | −0.1240 | +0.0460 | 2.396 | 6.02 | 0.551 | 2.8% |
| MNQ 15m RTH | **7** | +0.0112 | −0.1479 | 43% | **+0.1685** | −0.1229 | +0.1709 | 1.539 | 3.87 | 0.593 | 15.8% |
| **MNQ 15m SESSION** | 72 | **+0.0992** | +0.0909 | 65% | −0.0237 | +0.0268 | +0.1890 | **3.116** | **7.83** | 0.578 | 8.3% |
| MNQ 30m RTH | **8** | **−0.1539** | −0.2554 | 25% | **+0.0008** | −0.2909 | −0.0200 | 0.542 | 1.36 | 0.663 | 30.8% |
| MNQ 30m SESSION | 35 | +0.0294 | +0.0274 | 63% | +0.0067 | +0.0102 | +0.0182 | 1.577 | 3.96 | 0.625 | 19.0% |

**Six statements, all reportable.**

1. **Seven of twelve arm-cells have a negative universe expectancy net of costs**, including the two
   largest. **MES 5m SESSION is −0.1913R with only 14% of 107 rows positive** — the worst cell in my
   deliverable, and it is the cell where cost/R is 21.0% at the median (burst 05). At 5m on MES the cost
   model alone explains a large part of that.
2. **In three arm-cells the placebo universe beats the real universe** — MNQ 5m RTH (+0.013 vs −0.044),
   MNQ 15m RTH (+0.168 vs +0.011), MNQ 30m RTH (+0.001 vs −0.154). All three are MNQ `rth_only=True`.
3. **`free_t` is cleared nowhere.** The largest t on any row in any of my six cells is **3.116**
   (MNQ 15m SESSION), against a cell `free_t` of 3.855 (MES) / 3.875 (MNQ) and 4.462 for the whole EF5
   search. **Zero of ~1,452 floorable rows clear their own cell's threshold**, replicating the
   programme-wide verdict on an unmeasured regime.
4. **Every implied annualised Sharpe is in the implausible band** — 1.36 to 7.83. The bar for a single
   pre-registered hypothesis is 2.96 and for the cell is 9.68. A best-row implied Sharpe of 7.83 is not
   an encouraging number; it is the signature of 41 sessions.
5. **The two least-bad cells are MES 30m SESSION (+0.1211R, 86% positive, 35 rows, long share 0.478)
   and MNQ 15m SESSION (+0.0992R, 65% positive, 72 rows, long share 0.578)**, both positive in-sample
   and out-of-sample. Neither clears anything.
6. **Four arm-cells hold ≤ 10 qualifiers** (MES 30m RTH 7, MNQ 15m RTH 7, MNQ 30m RTH 8, MES 15m RTH 15
   at the boundary). In those cells a "top 10" **is** the whole universe — EF6's structural finding,
   reproduced independently from the full-span side rather than the fold side.

## 3. Why MULTI_TIMEFRAME occupies 8 of the top 10 on MNQ 15m SESSION — and why that is not a contradiction of BRIEF rule 2

`out/PROVISIONAL_measure_all.json`, MNQ 15m SESSION, top 10 of the joint real+placebo table:

```
 1 real            MULTI_TIMEFRAME n=40 exp=+0.6449 t=+3.12 win=.625 pf=2.93 RR=1.76 L/S=29/11
 2 real            MULTI_TIMEFRAME n=41 exp=+0.5848 t=+2.44 win=.610 pf=2.45 RR=1.57 L/S=32/9
 3 real            MULTI_TIMEFRAME n=45 exp=+0.5199 t=+2.66 win=.578 pf=2.40 RR=1.75 L/S=34/11
 4 real            MULTI_TIMEFRAME n=46 exp=+0.4959 t=+2.72 win=.630 pf=2.37 RR=1.39 L/S=37/9
 5 real            MULTI_TIMEFRAME n=45 exp=+0.4776 t=+2.11 win=.578 pf=2.10 RR=1.53 L/S=36/9
 6 real            MULTI_TIMEFRAME n=49 exp=+0.4589 t=+2.57 win=.612 pf=2.20 RR=1.39 L/S=40/9
 7 placebo_shuffle MOMENTUM        n=50 exp=+0.4314 t=+2.20 win=.520 pf=1.99 RR=1.84 L/S=23/27
 8 real            MULTI_TIMEFRAME n=50 exp=+0.4290 t=+2.42 win=.600 pf=2.09 RR=1.39 L/S=41/9
 9 placebo_shuffle MULTI_TIMEFRAME n=23 exp=+0.6011 t=+1.70 win=.565 pf=2.34 RR=1.80 L/S=15/8
10 real            MULTI_TIMEFRAME n=22 exp=+0.6102 t=+1.57 win=.500 pf=2.18 RR=2.18 L/S=13/9
```

**Read the L/S column. The eight real rows are 0.59 to 0.82 long** — 41/9, 40/9, 37/9, 36/9, 34/11,
32/9, 29/11, 13/9. On a tape that rose **+12.19%** over the same 41 cycles.

`mtf_aligned` / `mtf_strongly_aligned` fire when the frame's timeframes agree on direction
(`agreeing_timeframes`, `voting >= 2`). **In a persistently rising market, timeframe alignment IS long,
nearly all the time.** So "MULTI_TIMEFRAME on MNQ 15m over these 41 sessions" is, to a first
approximation, *be long while the trend is up* — and in a +12.2% window that harvests drift.

**This is why it does not contradict BRIEF rule 2** ("requiring any multi-timeframe alignment measured
detectably worse than requiring none, z = −4.09"). Rule 2 is a paired statement about adding an
alignment requirement to otherwise-identical rule sets, measured across regimes. What I measure is a
*ranking* over 41 up-tape sessions, in which the family whose signal is a long-bias proxy on an up tape
ranks highest. Those are different questions and my result is not evidence against rule 2. **Reporting it
as "multi-timeframe alignment works on MNQ scalp" would be the error**, and it is the error a top-10
table invites.

**Two pieces of evidence that this reading is right rather than merely plausible.**

* **`placebo_shuffle` — which permutes direction labels among the row's own entry bars and therefore
  preserves its long/short count exactly — reaches ranks 7, 9, 11 and 14 with expectancies of +0.43R,
  +0.60R, +0.37R and +0.32R.** A control that keeps the drift exposure keeps most of the level. The
  reals' paired advantage over shuffle is +0.217R (burst 08); the rest of the +0.64R at rank 1 is
  available to a control.
* **In the one contiguous third where MNQ fell (−1.69%), the effect vanishes**: paired vs-random
  z = −0.93, LONG-only z = −0.39 (burst 08). The family's edge is conditional on the direction of the
  tape.

**And MES is the counter-example that makes the point cleanly.** MES drifted +5.77% and its qualifying
universes sit at long share **0.478–0.563** — inside EF4's 0.467–0.539 band and inside its random
baseline of 0.498–0.535. MES 30m SESSION, my other least-bad cell, is **0.478 long**, i.e. marginally
short-biased, and its universe is +0.1211R with 86% of rows positive. **So the two symbols' least-bad
cells have different causes**, which is D14/D41 doing exactly what it says: MES and MNQ are one
underlying and one observation, and here they do not even agree on the mechanism.

## 4. What I therefore recommend to the parent session

**Publish no ranked top 10 for either symbol in `RESULTS.md`.** Publish instead, per cell, the
qualifying count, the universe's expectancy net of costs, the placebo universe's expectancy beside it,
the long share, the clock-close share, the best row's t and its implied annualised Sharpe, and the
`free_t` it fails. That is the statement this substrate supports, and the table in §2 is it.

If a ranked list is required anyway, the only two cells with a defensible universe are **MES 30m
SESSION** and **MNQ 15m SESSION**, every row must carry `NOT LIVE-ELIGIBLE`, and the MNQ rows must carry
the long-share and drift note from §3 or they will be read as a multi-timeframe finding.
