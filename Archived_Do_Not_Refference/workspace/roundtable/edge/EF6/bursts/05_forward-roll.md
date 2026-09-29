# EF6 burst 05 — the forward roll, and the two things the prior study could not distinguish

**Built:** `EF6/code/forward.py` (the roll), `EF6/code/make_ledger.py` (the interchange artefact),
`EF6/code/session_engine.py` (an independent 18:00→16:00 clock so the ledger is honest before
EF1's version lands).

## Design, and the two additions over the prior study

Rank on the trailing window **ending the instant the trading period starts**, trade the top k for
the period, roll forward. Causality is **asserted per fold**, not trusted:
`assert led.ts[rank_window].max() < fold_start`.

Four arms, because one number is not interpretable:

1. **top-k** — what a trader following the list earns.
2. **whole qualifying universe** — every strategy the top-k was *chosen from*, scored on the next
   period. (Not "qualifiers in the scoring window", which would compare two different
   populations.)
3. **random-k** — k qualifiers drawn at random from the same candidate set. **New.** The prior
   study had no such arm, so it could not separate "the ranking is uninformative" from "a
   k-sized portfolio is worse than a wide one". Those are different findings with different
   consequences.
4. **cycle-blocked permutation null** — realised R reassigned within (exit geometry × time
   block), holding every trade count, every timestamp and the pooled R of every geometry in every
   block fixed. Method from `w4_core.permute_r`, reimplemented so nothing depends on a scratch
   directory.

**Additions.** (a) The **ranking criterion is a variable**: `expectancy`, `t`, and `durability`
(= `exp · n/(n+floor) / (1+sd)`, a shrink that takes a profit factor over 18 trades down by
18/38 = 0.47 while the same expectancy over 200 trades keeps 0.91). The mandate says rank on
durability; whether that survives forward where expectancy did not is answerable on the same
folds. (b) **Fold boundaries snapped to 18:00 ET**, so no holding period is split across the
rank/score line — a boundary mid-session lets the score window inherit a position the rank window
opened, which is a soft look-ahead available for free.

## Demonstration — MGC 60m, the overnight regime, which has never been measured

`data/archive`, 718.9 days, 11,297 bars, 18:00→16:00 enforced by `SessionWindowEngine`.

```
generated 465 (primary_tf=60), prefiltered out 0, screened 465,
with trades 205, total trades 8,150, 152.8s
engine: in_window 10,802 / out 495 bars; entries vetoed by the window 1,139;
        positions closed at the window boundary 3,763; allow_overnight true
```

**3,763 of 8,150 trades (46.2%) exit at the window boundary.** On the smaller 84-strategy run it
was 693 of 1,310 = **52.9%**. So the 22-hour cap is the binding exit on roughly half of all swing
trades, and any swing row's exit statistics are substantially statistics about the clock rather
than about its thesis. That must be stated on every swing row.

### Result

| criterion | lookback / fold | rank-window qualifiers | top-10 | **universe** | random-k | null (sd) | z |
|---|---|---|---|---|---|---|---|
| expectancy | 180d / 30d | 16.2 | +0.0255R | **+0.0302R** | +0.0069R | +0.0218 (0.0258) | **+0.14** |
| durability | 180d / 30d | 16.2 | +0.0275R | **+0.0302R** | −0.0029R | +0.0211 (0.0256) | **+0.25** |
| expectancy | 360d / 90d | 29.3 | +0.0946R | **+0.1192R** | +0.1527R | +0.1190 (0.0565) | −0.43 |
| durability | 360d / 90d | 29.3 | +0.0756R | **+0.1192R** | +0.1431R | +0.1151 (0.0572) | −0.69 |

`threshold: n=465, free_t=3.505 on 718.88d (sqrt y 1.403) → needs annualised Sharpe 2.498`

**Three findings, in order of how much they change what anyone should do.**

**(1) Selecting is still worse than not selecting, on the regime nobody had measured.** Selection
edge vs universe is **−0.0047R, −0.0027R, −0.0246R, −0.0436R** — negative in all four
configurations. The programme's settled negative (`−0.0155R` vs a `−0.0104R` null, underperforming
the whole universe at +0.022R against +0.057R) **replicates under the 18:00→16:00 rule on
`data/archive` at 60m on MGC.** It was never a property of the RTH-only regime or of `csv/raw`.

**(2) But the ranking is *not* noise, and the prior study could not have seen this.** Against a
**random 10 from the same candidate set**, the top 10 wins by **+0.0186R (expectancy) and
+0.0305R (durability)** at the 180d/30d setting. So the failure is not "the ranking is
uninformative". It is: **concentrating into 10 names loses more to concentration than the ranking
gains.** That is a different diagnosis with a different remedy — it argues for a *wider* selected
set, not for abandoning ranking — and it is only visible because the random-k arm exists.
**Caveat, stated because it matters:** at 360d/90d the sign reverses (top-10 loses to random-k by
−0.058R and −0.068R) on **3 folds**. With 3 folds that is noise, so the random-k result is a
180d/30d, 17-fold finding on one symbol and not a general claim.

**(3) Ranking on durability does not rescue the forward test.** +0.0275R vs +0.0255R at 180d/30d
and +0.0756R vs +0.0946R at 360d/90d — one better, one worse, both inside the null's spread. The
honest statement is **no detectable difference between the three criteria; the verdict is
identical for all three.** The mandate's criterion is better hygiene than expectancy-ranking and
it does not buy an out-of-sample edge here.

**And nothing here is near a threshold.** z vs the no-edge null is **+0.14 to −0.69**. The
required annualised Sharpe at n = 465 on this span is **2.498**.

## The failure mode this exercise exposed, and why `roll` now refuses to hide it

The **first** run used a smaller population — 84 screened, 49 with trades — and produced this:

```
MGC swing 60m  durability  lookback=180d  trade=30d  floor=20  k=10
  top-10 0.0301R   universe 0.0301R   random-k 0.0301R   null 0.0844R  z=-0.92
  rank-window qualifiers mean 2.4   top-k was the whole universe in 17 of 17 folds
```

**Every arm identical, every difference exactly 0.0R.** The ranking window held a mean of **2.4
qualifiers**, so the top 10, the whole universe and a random 10 are the same set. That is not a
finding about selection; there was no selection. `RANKING_FINDINGS.md:271` hit the same wall on its
240m cells (1–9 qualifiers, "so the 'top 10' is the entire population"), and the diagnosis did not
make it into the machinery.

It does now: `roll` reports `folds_where_topk_is_the_whole_universe` and
`mean_rank_window_qualifiers`, and `roll_report` emits
**`TOP-10 IS NOT A SELECTION`** before it emits anything about expectancy.

**This is the third innocent explanation for an exact zero in this programme**, and they must be
excluded by name:

1. **D48** — two arms collided into one `BacktestResult`;
2. **vacuous selection** — the top-k *is* the universe, so the arms are the same set;
3. the settled finding that operating axes do not move expectancy.

An exact-zero between two arms reported without excluding (1) and (2) is not evidence for (3).

## Requirement on EF2–EF5: the population must be big enough for a top 10 to exist

Measured on MGC 60m at a 20-trade floor:

| screened | with trades | rank-window qualifiers (180d) | is a top 10 a selection? |
|---|---|---|---|
| 84 | 49 | **2.4** | **no** — 17 of 17 folds vacuous |
| 465 | 205 | **16.2** | yes — 0 of 17 folds vacuous |

And the trade distribution is brutally skewed: with 465 screened, the **median** strategy takes
**6** trades over 718 days and the 90th percentile takes 148 `[measured: bincount over the
ledger]`. So the 20-trade floor removes most of the population, which is correct and is also why
the qualifier count is so much smaller than the screened count.

**This collides head-on with HEADLINE 1.** A population large enough for a top 10 to be a
selection (≈465 screened) carries `free_t(465) = 3.505`, needing annualised Sharpe **2.498** at
60m. A population small enough to keep the threshold reachable (n ≤ 51 at SR 2.0) does not produce
enough qualifiers for a top 10 to mean anything. **The two requirements pull in opposite
directions, and at 57.90 days there is no n that satisfies both.** At 718.88 days the overlap is
narrow and probably empty; that is the finding, and it is arithmetic rather than pessimism.

## Anti-overfitting checks in this burst

| hazard | checked | finding |
|---|---|---|
| look-ahead | yes, asserted | `assert max(rank-window entry ts) < fold start` per fold; fold boundaries on 18:00 ET so no hold straddles the line |
| in-sample reporting | yes | nothing in-sample is reported as a result; `in_sample_key` is carried per fold only so the in/out gap is visible |
| clone inflation | yes | clone collapse on identical realised (timestamp, direction) sets inside the window, so one rule set listed ten times cannot fill a top 10 |
| null construction | yes | permutation blocked on time **and** on exit geometry. Without the time block the shuffle drags R across periods and the null acquires a different per-period baseline from the observation |
| parameter sensitivity | yes | 3 criteria × 3 (lookback, fold) settings; verdict invariant |
| understated costs | yes, as a requirement | `net_r` in the ledger is net of `CostModel`, inherited from `engine._close` (commission both sides, adverse slippage on entry) |
| unrealistic fills | partially | next-bar-open fills with adverse slippage and the contract `min_stop_ticks` floor. A gap *through* the 16:00 close is not modelled — the rule is enforced to bar granularity |
| vacuous selection read as "no effect" | **yes, and found** | the 84-strategy run. Now detected and named by the machinery |
