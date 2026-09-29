# EF5 burst 05 — cost as a share of R, and the placebo test the cell actually needs

Two things measured before any profitability number, both of which change the deliverable's design.

## 1. Cost is 21.0% of R on MES 5m and 4.8% on MNQ 5m — a 4.4× difference inside one index complex

`[measured: EF5/code/cost_share.py → EF5/out/cost_share.json; every in-session bar, every stop
geometry the population uses, `CostModel.cost_in_r(risk_points, atr_percentile=…)`]`

**The EDGE_BRIEF's "cost is 15.0% of R at 5m" is not right for either of my symbols.** Measured:

| cell | pooled median cost / R | p10 | p90 |
|---|---|---|---|
| **MES 5m** | **0.2101** | 0.0737 | 0.3940 |
| MES 15m | 0.1212 | 0.0469 | 0.2425 |
| MES 30m | 0.0867 | 0.0346 | 0.1576 |
| **MNQ 5m** | **0.0478** | 0.0165 | 0.0976 |
| MNQ 15m | 0.0276 | 0.0102 | 0.0530 |
| MNQ 30m | 0.0197 | 0.0079 | 0.0351 |

By geometry, which is where it bites:

| geometry | MES 5m | MES 15m | MES 30m | MNQ 5m | MNQ 15m | MNQ 30m |
|---|---|---|---|---|---|---|
| `ATR × 0.75` (the tight/runner shapes) | **0.3499** | 0.1854 | 0.1261 | 0.0761 | 0.0424 | 0.0287 |
| `ATR × 1.0` | 0.2572 | 0.1391 | 0.0944 | 0.0568 | 0.0318 | 0.0215 |
| `ATR × 1.2` (the scalp geometry) | 0.2101 | 0.1167 | 0.0788 | 0.0474 | 0.0265 | 0.0179 |
| `ATR × 1.5` | 0.1677 | 0.0927 | 0.0630 | 0.0379 | 0.0212 | 0.0143 |
| `ATR × 2.5` (widest) | 0.1017 | 0.0562 | 0.0378 | 0.0228 | 0.0127 | 0.0086 |
| `STRUCTURE × 1.0` | 0.1313 | 0.0788 | 0.0534 | 0.0325 | 0.0178 | 0.0126 |
| `VWAP_BAND × 1.0` | 0.1051 | 0.1051 | 0.1051 | 0.0222 | 0.0224 | 0.0224 |

**Three readings, and the third is the one that changes the ranking.**

1. **On MES 5m with a tight stop, costs eat 35% of one R.** A row needs +0.35R of gross expectancy
   before it earns a cent. The MES p90 of **0.3940** is not noise, it is the **hard ceiling**: at MES's
   `min_stop_ticks = 8` (2.00 pt = $10 of risk) the round turn is $1.44 of fees plus ~$2.50 of
   slippage = $3.94, exactly **0.3940 R**. That ceiling binds at p90 for five of twelve geometries at
   5m, which means a substantial minority of MES 5m candidate entries carry a ~39% haircut.
2. **MNQ is a fundamentally different economic proposition at the same timeframe.** 4.78% against
   MES's 21.01%. MNQ's larger `min_stop_ticks` (16) and much larger ATR mean its typical R is worth
   far more dollars than MES's while the fee is identical. **So "the index complex at 5m" is not one
   statement.** Anything I conclude about MES 5m costs says nothing about MNQ 5m, which is D14/D41
   showing up in the cost model rather than in the rule sets.
3. **`VWAP_BAND` is the one geometry whose cost/R does not fall with timeframe** — 0.1051 on MES at
   all three, 0.0222–0.0224 on MNQ at all three. That is `D45` again: the cost is pinned because the
   *stop* is pinned to `min_stop_ticks` on the collapsed bars, and the fraction of collapsed bars is
   roughly timeframe-invariant (burst 03: 14.2/14.3/14.8% MES, 5.1/5.0/5.1% MNQ). **Two independent
   measurements of the same defect agreeing is worth more than either alone.**

**Consequence for the ranking, fixed in advance.** Ranking is on `expectancy_r_net`, which
`compute_metrics` reads from `Trade.net_r` (`metrics.py:151`) — commission already deducted and
slippage already inside the fill price. So costs are *in* the number I rank on. What the table above
adds is the **prior**: on MES 5m a tight-stop row must clear a 35% haircut, so seeing tight-stop MES
rows dominate a top 10 would be a red flag about the measurement, not a finding about the market. I
will carry `cost_r_median` as a column on every reported row.

## 2. The placebo test as specified has **no power** in this cell, and I fixed it before measuring

This is the single most consequential design decision in my cell, so it is written down before any
number exists.

The brief asks for "a placebo beside every reported row". The natural implementation — two placebos
(`placebo_random`, `placebo_shuffle`) per floored real, all ranked in one table — puts the control
cohort at **two thirds of the table**. `placebo.null_rank_distribution` gives, for *k* placebos among
*N* rows and no edge anywhere, `E[best placebo rank] = (N+1)/(k+1)`. At a 67% share:

`[measured: EF5 scratch over newstrats.placebo.null_rank_distribution, using the ≥20-signal
candidate ceilings from burst 04 as the real-cohort size]`

| cell | reals ≤ | placebos (2/real) | N | share | **E[best placebo rank]** | **P(placebo ranks 1st)** | P(in top 10) |
|---|---|---|---|---|---|---|---|
| MES 5m RTH | 103 | 206 | 309 | 0.67 | **1.50** | **0.667** | 1.000 |
| MES 15m RTH | 72 | 144 | 216 | 0.67 | 1.50 | 0.667 | 1.000 |
| MES 30m RTH | 60 | 120 | 180 | 0.67 | 1.50 | 0.667 | 1.000 |
| MNQ 5m SESSION | 277 | 554 | 831 | 0.67 | 1.50 | 0.667 | 1.000 |
| … every one of the twelve arm-cells | | | | 0.67 | **1.50** | **0.667** | **1.000** |

**A placebo topping my table is the null's own two-to-one favourite, and a placebo inside the top 10
is a certainty under the null.** So "the best placebo ranked 1st" would carry exactly zero
information in this cell. That is not a finding about MES/MNQ — it is the arithmetic of a thin cell
with a fat control cohort, and it is precisely the inflation `RANKING_FINDINGS` worker 1 caught in its
own v1 (`mean normalised placebo rank 0.57`, "the void condition") and corrected in v3.

**So EF5 runs two tests, both pre-registered, and reports both.**

### PRIMARY — paired, each real against its own placebos

For every floored real row, compare its `expectancy_r_net` with the mean of **its own** two placebos.
The placebo carries the base's exit model, scope filters, FILTER conditions, confirmation timeframes,
execution timeframe, symbol, primary timeframe and allowed directions, and differs **only** in the
entry signal (`newstrats/placebo.py:175-201`), so the paired difference isolates the signal's
contribution. Reported as a **sign test and a Wilcoxon signed-rank on the paired differences**, with
both arms' means — **never through `T.ab`, which inflates z ~3.3× on correlated arms (D28)**.

Power comes from the number of real rows, not from the ranking:

| cell | real rows (ceiling) | sign z if the true split is 60/40 |
|---|---|---|
| MES 30m RTH | 60 | **1.55** |
| MES 15m RTH | 72 | 1.70 |
| MES 5m RTH | 103 | 2.03 |
| MNQ 5m SESSION | 277 | **3.33** |

So the paired test is **adequately powered at 5m and underpowered at 30m**, and I will say which when
I report it. Note that this is power against a *large* effect (a 60/40 split of rows); against the
0.5-percentage-point effects this programme usually finds, none of my cells has power at all.

### SECONDARY — the ranking, with the control cohort share-matched to 10%

500 draws of a 10%-share placebo cohort from the same pool, re-ranked each time, reporting the
observed rate that a placebo reaches rank 1 / top 5 / top 10 against the analytic null for **that**
share (E[best] ≈ 9.0–9.7, P(rank 1) ≈ 0.10). Observed ≫ null means the ranking cannot tell a real rule
set from a random entry; observed ≪ null means my control is handicapped and the placebo ranks are
understated (worker 1's v1 failure, which ran in the direction that *hid* the result).

Both tests are implemented in `EF5/code/measure.py` (`paired_placebo_test`, `share_matched_ranking`)
and neither is reachable until EF1 publishes a `VERIFY.md` — `measure.py:import_engine` refuses to run
without it.
