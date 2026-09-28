# E5 — How much of this desk's results are transaction cost?

**Agent E5, REPLAY desk, closed-market window.** Read-only on `visible.jsonl`. No harness run, no
cursor advanced, `state.json` untouched, nothing committed. Script: `agents/E5_costs.py`
(self-contained, re-runnable; raw output mirrored to `agents/E5_raw.txt`).

## Sample and geometry — stated up front

| | |
|---|---|
| bars in `visible.jsonl` | 1685 |
| eligible decision bars (forward window closes inside the tape, ATR14 defined) | 1659 |
| **trials — both directions at every eligible bar** | **3318** |
| independent blocks (16:00-to-16:00 sessions) | 72 |
| geometry | 1.0 ATR stop, 2R target, stop wins a same-bar tie, flat at the 16:00 ET bar |
| ATR14 over eligible bars | min 3.38 · q1 7.72 · **median 10.46** · q3 14.32 · max 79.36 |
| 1R at median ATR | 10.46 pts = **$52.32** per MES contract |

Conventions (ATR14 from bars ≤ f−1, session-end rule, tie rule, eligibility) are lifted from
`missed.py` / `A_grid.py` so the numbers sit alongside Agent A's.

### The one methodological choice that matters

There are two ways to denominate R, and the desk has only ever used one.

- **(A) Fill-relative** — what `missed.py` and `A_grid.py` do. The bracket hangs off the *actual*
  fill: `stop = fill ∓ S`. A stop-out is therefore exactly −1.0R however much you slipped, because
  the slippage moved the stop by the same amount it moved the entry. Cost can only appear indirectly,
  through which bars get touched.
- **(B) Signal-relative** — correct cost accounting. The bracket hangs off the price you *decided* at
  and sized against, `P0` = the next bar's open: `stop = P0 ∓ S`, and you fill at `P0 ± slip`. A
  stop-out now costs `1 + slip/S` and a target pays `2 − slip/S`. Because the brackets no longer move
  with slip, the touch sequence is identical at every slippage level, so `net_R = gross_R − slip/S`
  **exactly, trade for trade**. The slope is `mean(1/S)` per point.

**I expected (A) to hide the cost. It does not**, and I am recording that against my own hypothesis:
over the 0–3 tick sweep the two models land 0.002 R apart. Shifting the whole bracket adverse raises
the stop-touch probability by very nearly what the direct deduction would have cost. **So the desk's
fill-relative convention is not the accounting error.** The accounting error is simpler and larger:
commission was never entered at all.

---

## 1. Slippage sweep on entry

| entry slip | points | (A) fill-relative mean R | (B) signal-relative mean R | (B) Δ vs zero |
|---|---|---|---|---|
| 0 tick | 0.000 | +0.0225 | +0.0225 | — |
| 0.5 tick | 0.125 | +0.0119 | +0.0096 | −0.0129 |
| **1 tick (desk convention)** | 0.250 | **−0.0032** | **−0.0032** | −0.0258 |
| 2 tick | 0.500 | −0.0278 | −0.0290 | −0.0516 |
| 3 tick | 0.750 | −0.0532 | −0.0548 | −0.0773 |

> **Cost per tick = 0.25 pts × mean(1/S) = 0.25 × 0.1031 = 0.0258 R per tick.**
> Per *point* of adverse fill: 0.1031 R. At the median stop (10.46 pts) one tick is
> **0.0239 R = 2.39% of 1R**.

Linear by construction in model B, and empirically linear in model A too (spread 0.0757 vs 0.0773 R
over the full sweep). One tick is where the desk's headline sits: gross +0.0225 R becomes net
−0.0032 R. **The single modelled tick is, by itself, enough to flip this tape's baseline
expectancy through zero.**

## 2. Commission — never once included in an R on this desk

**Conversion, stated:** `$2.69 round turn ÷ $5.00 per point = 0.5380 points`. That is
`0.5380 ÷ 0.25 = 2.152 ticks`. **Commission alone is worth 2.15 ticks — more than double the one tick
the engine models.** In R: `0.5380 / S`, which is 0.0514 R at the median stop and **0.0555 R**
averaged per trade over the sample (mean 1/S).

| accounting | mean R | vs gross |
|---|---|---|
| gross, zero cost | **+0.0225** | — |
| + 1 tick entry slip (the desk's current convention) | −0.0032 | −0.0258 |
| **+ 1 tick slip + $2.69 commission (all-in)** | **−0.0587** | **−0.0813** |
| + 1 tick in + 1 tick out + commission (realistic) | −0.0845 | −0.1070 |

**All-in drag = 0.0813 R per trade.** In dollars at the median stop: $1.25 slippage + $2.69
commission = **$3.94 against a 1R of $52.32**.

Every R this desk has published is therefore overstated by ~0.055 R — not by rounding, by a line item
that was in the spec (`round-turn cost 2.69`, noted at NOTES.md:482–487 and then filed as "sizing
machinery") and never carried into a result.

## 3. The number: gross edge required to clear zero

> **A strategy on this tape at a 1.0-ATR stop must find 0.081 R of gross edge per trade just to pay
> costs** — 0.026 R of entry slippage plus 0.056 R of commission. With a tick of exit slippage as
> well (which a stop exit really does pay), **0.107 R**.

Against that bar, the measured gross expectancy of the full 3318-trade sample is **+0.0225 R**, a
**shortfall of 0.059 R**. For scale: at the sample's 36.3% gross win rate on a 2R target, 0.081 R per
trade is the same as needing **2.71 percentage points of extra win rate** at fixed payoff.

**Break-even scale (§7 of the script).** All-in cost is 0.788 points. For the sample's gross point
estimate to cover it, 1R must be ≥ **34.97 points** — ATR14 ≥ 35 at a 1.0-ATR stop. That happens on
**16 of 1659 bars (1.0%)** of this tape, against a q3 of 14.32. The tape is almost never volatile
enough for its own baseline drift to pay its own costs.

**And the spec's floor makes the tight end worse (§8).** At `min_stop_ticks 8` = 2.00 points, one tick
is 12.5% of 1R and commission is 26.9%: **all-in cost is 39.4% of 1R.** A 0.25-ATR stop at this tape's
low-ATR quartile is 1.60 points — below that floor, so A's worst cell was partly unsizeable anyway.

## 4. Cost drag by ATR quartile — this is the clean result

| ATR quartile | n | median ATR | 1 tick as %1R | commission as %1R | all-in drag R | **gross** mean R | **net** mean R |
|---|---|---|---|---|---|---|---|
| Q1 (low vol) | 830 | 6.39 | 4.17% | 8.97% | **0.1314** | +0.0278 | **−0.1036** |
| Q2 | 836 | 9.12 | 2.77% | 5.97% | 0.0874 | +0.0337 | −0.0537 |
| Q3 | 824 | 12.05 | 2.07% | 4.45% | 0.0651 | +0.0174 | −0.0478 |
| Q4 (high vol) | 828 | 18.77 | 1.30% | 2.79% | **0.0409** | +0.0112 | **−0.0297** |

**Drag ratio Q1/Q4 = 3.21×.** And the decomposition is about as clean as this desk will ever get:

- **Gross spread across quartiles: 0.0225 R**, with no monotone trend — Q1 (+0.0278) is *above*
  Q4 (+0.0112), the opposite sign to the net ordering, and all four are positive.
- **Net spread across quartiles: 0.0739 R**, monotone in 1/ATR.

The prompt asked whether the nulls being worse in low-ATR regimes is a cost story or a market story,
and said it was testable here. **It is, and it tests as cost.** Gross expectancy is flat-to-noise
across volatility regimes; net expectancy fans out by 0.074 R in exact step with the tick-and-
commission fraction of 1R. There is no market mechanism in the regime-dependence. It is arithmetic.

## 5. Resolution — can the desk tell the two stories apart?

Trades opened at consecutive bars inside one session overlap almost completely, so 3318 trades are
nowhere near 3318 independent draws. Confidence intervals below resample **whole sessions** (72
blocks, 4000 replicates, seed 20260928), keeping each session's trades together.

| | |
|---|---|
| gross mean R | **+0.0225** |
| naive SE (n=3318, ignores overlap) | 0.0233 |
| session-block bootstrap SE (72 blocks) | **0.0276** (1.18× naive) |
| 95% block CI on gross mean R | **[−0.0325, +0.0756]** |
| all-in cost drag | 0.0813 R |
| CI contains 0? | **YES** |
| CI contains +0.0813 R (the edge needed to break even)? | **NO** |

Long-only gross +0.0388 (sd 1.346), short-only +0.0062 (sd 1.337). Gross outcome mix: STOP 58.8%,
TARGET 29.0%, CLOSE 12.2%.

**This is the crux.** The interval rules out a gross edge big enough to pay costs — the cost, 0.0813 R,
sits *above the entire 95% upper bound* of the gross edge. It does not rule out zero. So the two
hypotheses are distinguishable in exactly one direction: the desk can say the edge is too small to
trade, and cannot say it is absent.

## 6. Correction to Agent A: the stop-width gradient is only about half cost

A read the 0.25→1.5 ATR expectancy ladder as tracking slippage and concluded "the mechanism is
arithmetic, not market structure." Decomposed at zero cost (2R target, same 3318-trade sample per
cell):

| stop | median 1R pts | **gross (zero cost)** | 1-tick slip only | all-in | drag R |
|---|---|---|---|---|---|
| 0.25 ATR | 2.62 | −0.2051 | −0.3082 | −0.5302 | 0.3250 |
| 0.50 ATR | 5.23 | −0.0285 | −0.0801 | −0.1910 | 0.1625 |
| 0.75 ATR | 7.85 | +0.0258 | −0.0086 | −0.0826 | 0.1083 |
| 1.00 ATR | 10.46 | +0.0225 | −0.0032 | −0.0587 | 0.0813 |
| 1.50 ATR | 15.70 | +0.0463 | +0.0291 | −0.0079 | 0.0542 |
| 2.00 ATR | 20.93 | +0.0615 | +0.0486 | +0.0209 | 0.0406 |

Attribution of the 0.25→1.5 ATR gradient (all-in +0.5223 R):

| component | R | share |
|---|---|---|
| **gross — survives at zero cost** | +0.2514 | **48.1%** |
| slippage | +0.0859 | 16.5% |
| **commission (A never counted it)** | +0.1849 | **35.4%** |

So A is about half right, and the half that *is* arithmetic is mostly the line item A omitted. **The
tick A pointed at is the smallest of the three terms.** Tight stops against a 2R target are genuinely
worse before any cost at all — a 0.25-ATR stop gets knocked out by intrabar noise on its own merits —
and that half of the gradient is a real statement about the tape's bar structure. A's "continuous cost
drag, not a threshold" is right about the shape; the label "cost" is right for only ~52% of the size.

Also worth flagging: the ladder only turns net-positive at 1.5–2.0 ATR, where the stop is 16–21
points. That is not a cost-free win. It is the drag shrinking faster than the gross edge, and at
2.0 ATR the 1R risk is $105/contract.

---

## Verdict — which sentence does the evidence support?

> **"Any structure at 60m is smaller than the cost of trading it."**

That is the supported sentence, and the discrimination is one-sided, which I want stated rather than
smoothed over:

1. **What the evidence establishes.** The tape's baseline gross expectancy at 1.0 ATR / 2R is
   +0.0225 R with a session-block 95% CI of [−0.033, +0.076]. All-in cost is 0.0813 R. **Even the
   optimistic end of the gross interval does not clear the cost.** Whatever is there is too small to
   pay for itself on MES. That is a cost conclusion, and it is firm.
2. **What the evidence does *not* establish.** The CI contains zero, so "gross edge is exactly zero"
   is not rejected either. The desk cannot distinguish *no structure* from *0.02 R of structure*; it
   can only rule out *0.08 R of structure*. To separate +0.0225 R from 0 at two sigma would need the
   block SE down to ~0.011, i.e. **~430 sessions (≈1.7 years) of 60m tape against the 72 sessions
   here** — about 6× this tape.
3. **So the desk should stop writing sentence 1.** Every "indistinguishable from arbitrary bars" null
   on this desk was measured net of one tick and *gross of commission*, at a 1R of ~$52 against a
   ~$3.94 round-turn. Those nulls are consistent with a small real edge being eaten, and the desk has
   never had the resolution to say otherwise. "No structure" is a claim the measurements do not
   support; "not enough structure to trade at these costs" is a claim they do.
4. **The one thing that is fully settled.** The *regime-dependence* of the nulls is cost, not market.
   Gross is flat across ATR quartiles (0.0225 R spread, wrong-signed ordering); net fans out 0.0739 R
   monotonically with the tick's share of 1R. Any future result that looks worse in quiet tape should
   be assumed to be this until it is divided out.

### What instrument would be needed

The binding constraint is not the tick — it is commission, at 2.15 ticks. Cost in R is
`(slip + comm/point_value) / (stop_mult × ATR)`, so there are three levers and only one is any good:

- **Wider stops.** Works arithmetically (2.0 ATR drag is 0.0406 R) but buys the improvement with a
  $105 1R and does not change the dollar edge.
- **Wait for volatility.** Needs ATR ≥ 35 for the baseline to cover costs. 1.0% of bars. Not a plan.
- **Larger contract.** This is the real lever. Commission is roughly fixed per contract while point
  value scales, so on full-size ES the commission term falls by ~an order of magnitude: at $50/point
  a ~$4.00 round turn is 0.080 points = 0.32 ticks, and all-in drag at the median stop falls from
  **0.0753 R to ~0.0315 R** — *below* the gross CI upper bound, which is the difference between
  "cannot possibly pay" and "might pay if the edge is near the top of its interval."
  *(The $4.00 ES commission is my assumption for scaling, not a desk fact; the spec only carries
  MES's $2.69. The ratio, not the absolute, is the point.)*

Which means the desk's instrument problem has two halves and they need different fixes: **MES is the
wrong contract for a 0.02 R edge**, and **72 sessions is the wrong sample for deciding whether the
0.02 R is real.** Neither is a fact about the market at 60 minutes.
