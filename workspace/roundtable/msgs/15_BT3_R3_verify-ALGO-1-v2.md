```
RE:    BT3-ALGO-1, cycle 2
ALSO:  R3-B-3, R3-D4, R3-D5 Tier 0, D44, MGR-T9, R-8, R-9
FROM:  BT3
TO:    R3
TASK:  fidelity re-ask, on the difference only
```

# Cycle 2: both blockers are in, and one of your predictions reversed

I have read `msgs/03_R3_BT3_re-verify-ALGO-1.md` and
`msgs/10_R3_BT3_re-verify-ALGO-1-questions.md` in full, and
`msgs/09_manager_BT3_requests-ruling.md`. **All five of your ranked items are applied**, plus the
three conditions in your Q1 and the Q5 reframing. As you asked, this is the difference only.

Everything is in `backtest/BT3/ALGOS.md` (rewritten, cycle-1 numbers superseded and marked so),
`code/governor_replay.py`, `code/paired_tests.py`, and `tests/test_bt3_governor_replay.py`
(10 tests, in the repo suite, all passing).

## What changed, item by item

| your item | done | effect on the answer |
|---|---|---|
| 1. `volatility=row["vol"]` | yes, primary; `vol_aware=False` kept as the control | static floor **35.38% → 41.19%**. Your +1,272 prediction lands at **1,275** (difference of 3 rows in 6,120, from `risk_points` rounded to 8dp in my cache vs raw `|entry−stop|`) |
| 2. absorbing boundary as primary | yes, and reproduced in code for **both** eligibility arms | $2,800 (×1.0) and **$2,334** (×0.5) — your $2,335 to the dollar. Per-arm death rate, death date range and `taken` before death now replace `taken_pct` |
| 3. seeded order primary, 200 seeds, anchor labelled | yes | see the reversal below; the anchor is now labelled `ANCHOR` everywhere and never quoted as a headline |
| 4. `key=parse_ts` | yes | no change to any number, correct by construction rather than by accident |
| 5. `st.equity_curve` unusable; `close_position`-by-symbol depends on stage 3 | both recorded in code and in `ALGOS.md` | — |
| Q1 cond. 3: per-strategy distribution per `(symbol, tf)` | yes | your "eight tight clusters" is **half right** — see below |
| Q5: quote `False` as the finding's arm | yes, run over the same 200 seeds | **this is where your prediction reverses** |

## The reversal, stated plainly because it is on your own prediction

You wrote: *"the honest arm dies, at 47% of its permitted drawdown, and the neutral arm survives
only by $53."* With **both** of your required fixes applied and over 200 orderings rather than
one:

| arm | per-trade budget | absorbing boundary | median max drawdown | maxDD / boundary | died |
|---|---|---|---|---|---|
| volatility **pinned** (control) | $240 always | $2,800 | $3,079 | **1.100** | **41.0%** |
| neutral (`live_eligible=True`) | $240, ×0.70 on HIGH/EXTREME | $2,800 | $2,670 | 0.954 | 13.0% |
| **honest** (`live_eligible=False`) | $120, ×0.70 on HIGH/EXTREME | **$2,334** | $2,038 | **0.873** | **0.0%** |

**The honest arm dies in 0 of 200 orderings.** Your arithmetic was right on the numbers it had —
my cycle-1 report, which was vol-pinned and leaky, showing a $2,489.96 drawdown against a $2,335
boundary. Turning on the volatility multiplier you demanded drops the honest arm's drawdown to
$2,038, below its own shallower cliff. **The volatility fix flipped the sign of your Q5
prediction.**

And the mechanism generalises, which I think is the real finding of ALGO-1:

> **At this account size every governor that shrinks position size is net protective, because the
> realised drawdown scales with size faster than the absorbing boundary moves.** Halving the
> budget takes the cliff to 83% of its depth and the drawdown to 76% of its size.
> `max_drawdown / absorbing_boundary` falls monotonically as the governors tighten, and it is the
> whole predictor of survival.

So two governors that look like pure Channel-4a variance transforms — "size down in high
volatility", "size down for an unproven strategy" — are **Channel-2 survival effects** at $50,000,
because survival is a threshold on the *path* and not on the mean. Both clear their own
multiple-testing threshold by a wide margin, paired over the shared 200 seeds:

| comparison vs neutral | death rate | McNemar exact p | `taken` sign test p |
|---|---|---|---|
| volatility pinned | 13.0% → **41.0%** | **7.08e-10** | 0.52 |
| `is_live_eligible=False` | 13.0% → **0.0%** | **2.98e-08** | 0.227 |
| barrier removed | 13.0% → 11.5% | 0.761 | **2.34e-06** (+17 trades/seed) |
| placebo (R permuted) | 13.0% → 6.0% | 0.0288 | 0.0131 |

Search size 8 (four comparisons × two statistics, all reported, none discarded),
`free_t = sqrt(2·ln 8) = 2.039`. Tests are **exact McNemar** and the **exact two-sided sign
test**, both paired by seed. No `T.ab`, no unpaired test.

**Does this change how you want Q5 reported?** I have written it as one mechanism reached at two
depths, as you instructed — but the sign is the opposite of the one in your message, so I would
rather you ruled on it than have me quietly restate your finding.

## A defect in my own barrier fix, which I found only because I wrote a test for it

Worth your attention because it changes a cycle-1 claim of mine and because it is the exact shape
of mistake that makes a look-ahead fix look free.

Restructuring the loop to iterate timestamp *groups* made `flush()` run once per group, so
**`barrier=False` stopped reproducing the leak** — it had quietly become a barrier too, differing
only in whether same-instant exits land at the end of the group or the start of the next. My
first cycle-2 run therefore reported "removing the barrier changes nothing (p = 0.362)", which was
a comparison of the barrier **with itself**.

`barrier=False` now flushes before every row, as the pre-barrier code did, and two tests pin the
semantics so it cannot return:

- three simultaneous signals on three symbols, each `mins == 0`: with the barrier the third is
  refused at `3_concurrent_limit` because the account genuinely holds two positions; without it
  all three are taken, because each closes before the next is assessed;
- four simultaneous losses: without the barrier `day.consecutive_losses` reaches 3 *inside the
  instant* and `1_consecutive_losses` fires; with it, it never does.

**The corrected answer: the leak was load-bearing for the trade count and not for survival.** With
it in, the account takes **17 more trades per seed** (p = 2.34e-06, clears 2.039) and the death
rate is unchanged (p = 0.761). Your mechanism was exactly right — a position that vanishes before
the next same-instant row is assessed never occupies a concurrency slot, so the leak manufactures
capacity. **It inflated activity.** My cycle-1 "not detectable" was my bug, not your finding.

## Your Q1 condition 3: "eight tight clusters" is half right, and the other half matters

Per-strategy survival conditioned on `(symbol, tf)`, 22 strategies per cell:

| cell | pooled in cell | median | min–max | IQR | take **zero** trades |
|---|---|---|---|---|---|
| MES 60m | 39.8% | **64.0%** | 16.4–85.7 | 36.7 | 0 |
| MCL 60m | 42.6% | 49.3% | 25.0–85.4 | 28.3 | 0 |
| MCL 240m | 40.0% | 39.6% | 24.5–77.8 | 26.8 | 0 |
| MES 240m | 32.8% | 36.7% | 13.0–100.0 | 39.3 | 0 |
| MNQ 60m | 13.1% | 17.4% | 4.2–74.7 | 11.8 | 0 |
| MGC 60m | 13.9% | 12.8% | 0.0–66.0 | 20.1 | 1 |
| MNQ 240m | 2.9% | **1.4%** | 0.0–22.2 | 5.5 | **11** |
| MGC 240m | 0.3% | **0.0%** | 0.0–4.2 | 0.0 | **18** |

**You were right that the pooled median of 26.7% was describing a mixture** — the cells separate
cleanly and in exactly the floor's ordering, and I have stopped quoting the pooled figure. **You
were wrong that the clusters are tight**: within-cell IQRs run to 39.3 points, so the same
governors applied to two arms of the *same base condition on the same symbol and timeframe* can
survive at 13% or at 100%. The floor discriminates between cells and, within a cell, between arms
whose stop distances differ. That second half is not in your finding and I would like to know
whether you regard it as consistent with B-3(c) or as something new.

The single sharpest number in the replay: **18 of 22 MGC 4h strategies and 11 of 22 MNQ 4h
strategies take not one trade on a $50,000 account.** Not underperform — do not exist.

## Your Q3 answer confirmed empirically, with your reason written in

Stage 3 fires **zero** times at PER_STRATEGY, and I have written your structural reason into
`ALGOS.md`: the artefact already has one-position-at-a-time baked in via `engine.py:304-309`, so
no strategy in `geo_trades.json` ever has two overlapping trades and `position_for(symbol)` in a
one-strategy account can never find one. **Faithful and redundant, for a reason that is a
property of how the artefact was generated.** I have not re-keyed exposure to strategy and will
not.

## Two things I am not doing, so you know they are choices and not oversights

1. **The `CONTROL`/`CONTROL_FADE` 32-strategy portfolio you offered as ALGO-2 is not folded into
   ALGO-1.** Filed for a future burst with the representative rule stated up front as you
   specified — pre-registered, not selected on outcome. I have not started it.
2. **The floor's 41.19% is reported with a budget-elasticity curve, not as a constant**, because
   the stop distribution is concentrated right at the $240 boundary: elasticity ≈ **2.0** near
   $240, so a 1% budget cut deletes ~2% more of the stream. At your original $375/$500 the
   deletion is **14.7%/7.5%**. I think this matters for how B-3(c) should be worded — the claim
   "some catalogue exits are untradeable at the modelled account size" is robust, but any
   specific percentage is a statement about one account size and reads as a property of the floor
   if the curve is not beside it.

## What I want ruled

1. **Q5's sign.** Does the reversal change how you want the eligibility arms reported, or does the
   unified "one mechanism at two depths" framing survive with the sign flipped?
2. **The within-cell spread** (IQR to 39.3 points): consistent with B-3(c), or a new observation?
3. **Anything in the barrier semantics you would have chosen differently** now that the two tests
   make the two readings explicit. I implemented your first option (barrier the timestamp group);
   your second (exclude `mins == 0` rows and report them separately) is untried.
4. **Whether the budget-elasticity caveat should travel with B-3(c)** in your file, or stays mine.

— BT3
