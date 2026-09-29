# EF6 burst 07 — the scalp forward test, and the one configuration that "worked"

The arithmetic in burst 01 says a scalp top 10 is unanswerable at 57.90 days. This burst checks it
on the tape, and finds the same answer by two further independent routes — and then finds the one
configuration out of nine that produced a "success", which is the most instructive row in the whole
exercise.

**Ledgers:** MGC 15m and MNQ 15m, `data/archive`, 57.9 days, 18:00→16:00 enforced, `max_total=2500`.

```
MGC 15m: generated 465, prefiltered out   0 (0.0%),  screened 465, with trades 190, 2,026 trades
MNQ 15m: generated 412, prefiltered out  37 (9.0%),  screened 375, with trades 128, 1,663 trades
         MNQ causes: oi_price_confirmation@15m 22, oi_expanding@15m 19; groups BREAKOUT 19, MOMENTUM 18
         MNQ also 33 THIN
engine (MGC 15m): in_window 3,579 / out 167 bars; entries vetoed 160; closed at the boundary 365
engine (MNQ 15m): in_window 3,579 / out 165 bars; entries vetoed 197; closed at the boundary 230
```

## Route 2 — structurally, the ranking window does not hold ten qualifiers

| symbol | lookback / fold / floor | folds traded | rank-window qualifiers | top-10 was the whole universe |
|---|---|---|---|---|
| MNQ | 28d / 7d / 20 | 4 of 8 | **4.5** | **4 of 4** |
| MNQ | 28d / 7d / 10 | 4 of 8 | **7.2** | **4 of 4** |
| MNQ | 21d / 7d / 10 | 5 of 8 | **5.2** | **5 of 5** |
| MNQ | 14d / 7d / 5 | 6 of 8 | **7.8** | **6 of 6** |
| MGC | 28d / 7d / 20 | 4 of 8 | 7.5 | **3 of 4** |
| MGC | 28d / 7d / 10 | 4 of 8 | 17.0 | 0 of 4 |
| MGC | 14d / 7d / 5 | 6 of 8 | 15.5 | 0 of 6 |

**On MNQ 15m the top 10 is not a selection in any configuration tested.** On MGC it becomes one
only by dropping the trade floor to 10 or 5 — i.e. by ranking on samples whose 95% interval on a
win rate spans ~30 percentage points.

## Route 3 — operationally, there are only 4 to 6 folds

57.9 days will not carry a walk-forward. Even at the most aggressive setting (14-day lookback,
7-day folds) the roll produces **6 folds**. With four to six folds, the pooled expectancy is one
number with a standard error of its own, and the fold-level counts ("2 of 4 profitable") carry no
information at all.

## And then: the one configuration out of nine that produced a success

```
MGC scalp 15m  durability  lookback=28d  trade=7d  floor=10  k=10
  folds traded 4/8   oos trades 197
  top-10  0.1346R   universe 0.0306R   random-k 0.0029R   null -0.0244R (sd 0.0641)   z=2.48
  selection edge vs universe +0.1040R   vs random-k +0.1317R
  rank-window qualifiers mean 17.0   top-k was the whole universe in 0 of 4 folds
  beating universe 3 of 4
  VERDICT: top-k beat both universe and null
```

**This is the row a reader would want to believe, and it is the one to look hardest at. Five
reasons it is not a result, in descending order of how badly each one hurts:**

1. **The sign flips with the trade floor, on the same ledger, same symbol, same folds.** floor 20 →
   selection edge **−0.0191R**. floor 10 → **+0.1040R**. floor 5 → **−0.0364R**. A result that
   changes sign twice across three neighbouring values of a nuisance parameter is a description of
   one sample.
2. **Four folds.** 197 out-of-sample trades, 4 of 8 folds traded, "3 of 4 beating universe".
3. **It does not clear its own threshold.** z = 2.48 against `free_t(465) = 3.505`.
4. **The Sharpe it implies is not physically available.** z = 2.48 on a 0.1585-year span implies an
   annualised Sharpe of **2.48 / 0.398 = 6.23**. The threshold for this cell demands **8.80**.
   Numbers in that range are the signature of a small sample, not of an edge.
5. **I searched nine configurations to find it, and that search has its own deflation cost.**
   9 roll settings across 2 symbols → `free_t(9) = 2.10` **on top of** the 3.505 already owed for
   the 465 rule sets. The configuration search is a search. I paid for it by reporting all nine.

**This is what data-mining bias looks like from the inside**, and it is worth having in writing:
nine honest configurations, one of which returns z = +2.48 with a positive selection edge on both
comparison arms. Reported alone it would read as the programme's first live-eligible finding.

## The verdict on the scalp half, by three independent routes

| route | statement |
|---|---|
| arithmetic | `free_t(10)/sqrt(0.1585) = 5.39` required annualised Sharpe for the #1 row; the n=1 floor of 1.177 already needs **2.96** |
| structural | the ranking window holds **4.5–7.8** qualifiers on MNQ, so the "top 10" is the whole universe in **every** fold |
| operational | **4–6 folds** exist in total; there is no walk-forward to run |

**A scalp top 10 on this substrate is a description of 41 trading sessions. It is not a forecast and
must not be labelled as one.** That is the finding; it is not a failure to find something.

## What EF2–EF5 should do with the scalp half instead

The instruction I would give, and it is a research instruction rather than a reporting one:

* **Do not rank.** Pre-register **one or two** scalp hypotheses in writing, measure exactly those,
  and report the result against the 1.177 floor with "this needs a sustained annualised Sharpe of
  2.96 on 57.9 days" attached. That is the only statement the substrate can carry.
* **Report the whole qualifying universe's expectancy per cell**, not a top 10. It has the full
  sample behind it, it needs no selection, and it is the arm that beat the top 10 in 4 of the 5
  configurations where a selection existed at all.
* **State the fold count on every scalp claim.** Four folds is the honest headline, not a footnote.

## Anti-overfitting checks in this burst

| hazard | checked | finding |
|---|---|---|
| **parameter sensitivity** | **yes, and found** | the MGC selection edge flips sign twice across floor ∈ {5, 10, 20} |
| **data-mining bias over configurations** | **yes, and found in my own work** | 9 configurations searched; 1 "success"; `free_t(9) = 2.10` owed on top of the row's own threshold. All nine reported |
| insufficient sample | yes | 4–6 folds; 181–598 OOS trades; qualifier counts 4.5–17.0 |
| vacuous selection | yes | detected and named in 4 of 7 configurations |
| structural zero rows | yes | prefilter removed 37/412 on MNQ 15m (9.0%) before measurement; 0 on MGC |
| implausible implied Sharpe as a plausibility check | yes | 6.23 implied vs 8.80 required; both outside what futures delivers |
