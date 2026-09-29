# EF4 burst 02 — cost as a fraction of R, per cell, and the hard floor the spec imposes

`code/cost_in_r.py` → `out/cost_in_r.json`. Contract spec + measured median ATR. No backtest.

## First, a correction to how "gross vs net" is read off this engine

`BacktestEngine` charges **slippage into the fill price** (`engine.py:352` entry,
`engine.py:414` stop exit) and **commission as dollars** in `_close`
(`engine.py:494-499`: `commission = 2.0 * commission_per_side(); cost_r = commission /
risk_dollars; net_r = gross_r - cost_r`).

So `Trade.gross_r` is **already net of slippage**. `net_r − gross_r` is the commission
term alone. **A row reported as "gross" straight off `gross_r` understates the true gross
by the whole slippage term**, which on these cells is 1.5–3.5× the commission. Every
gross figure EF4 reports is reconstructed from the fill geometry, never taken from
`gross_r`.

## The thin-book penalty is the normal case here, not an edge case

`SlippageModel.thin_book_extra_ticks = 1.0` and the engine sets `thin = not is_rth(...)`
`[repo-verified: engine.py:351, :411]`. Measured share of bars inside each contract's own
RTH: `[measured: code/cost_in_r.py]`

| cell | in RTH | **outside RTH → +1 tick each side** |
|---|---|---|
| MGC 5m | 22.7% | **77.3%** |
| MGC 15m / 30m | 21.9% | 78.1% |
| MCL 5m / 15m / 30m | 24.1% | 75.9% |

MGC's RTH is 310 minutes and MCL's 330, out of a 1,320-minute 18:00→16:00 cycle. So the
programme's own session rule puts roughly **three quarters of every scalp trade in the
thin-book slippage regime**. Any cost table quoted at the RTH rate understates this cell.

## All-in cost in R (commission + entry slippage + exit slippage)

Median Wilder-14 ATR on the cell's own timeframe: MGC 4.752 / 8.626 / 12.503 points at
5/15/30m; MCL 0.2044 / 0.3560 / 0.5115. Both contracts have `tick_value = $1.00` and
round-turn commission+fee `$1.44`.

| cell | stop | commission only | all-in, RTH, stop exit | all-in, **thin**, stop exit |
|---|---|---|---|---|
| MGC 5m | 0.5 ATR | 0.061 R | 0.145 R | **0.229 R** |
| MGC 5m | 1.0 ATR | 0.030 R | 0.072 R | 0.115 R |
| MGC 15m | 0.5 ATR | 0.033 R | 0.080 R | 0.126 R |
| MGC 30m | 0.5 ATR | 0.023 R | 0.055 R | 0.087 R |
| **MCL 5m** | **0.5 ATR** | **0.141 R** | **0.337 R** | **0.532 R** |
| MCL 5m | 1.0 ATR | 0.070 R | 0.168 R | 0.266 R |
| MCL 15m | 0.5 ATR | 0.081 R | 0.193 R | 0.306 R |
| MCL 30m | 0.5 ATR | 0.056 R | 0.135 R | 0.213 R |

The dispatch quoted "15.0% of R at 5m against 4.6% at 60m". My MCL 5m commission-only
figure at a 0.5-ATR stop is **14.1%**, so that number was **commission-only**. The all-in
number for the same cell is **33.7–53.2%**. The dispatch's direction is right and its
magnitude is roughly **2.4–3.8× too small** for MCL at 5m.

## The floor: `min_stop_ticks` makes the worst cost regime unavoidable

`StopModel.stop_price` ends with `dist = max(dist, spec.min_stop_ticks * spec.tick_size)`
`[repo-verified: base.py:313-314]` — every stop is floored at the contract's noise floor,
silently. MGC's floor is **25 ticks = $25**; MCL's is **15 ticks = $15**.

That floor is *binding at 5m on both symbols*: 0.5 ATR is 23.8 ticks on MGC 5m and 10.2
ticks on MCL 5m, both below the floor. So a 5m strategy asking for a tight stop gets the
floor instead, and the floor sets a hard minimum cost:

| cell | tightest legal stop | min all-in cost, RTH | min all-in cost, **thin** |
|---|---|---|---|
| MGC any tf | $25 | 0.138 R | **0.218 R** |
| MCL any tf | $15 | 0.229 R | **0.363 R** |

**These are floors, not estimates.** No MCL scalp under this cost model can pay less than
**22.9% of R** per round trip, and in the overnight regime this programme runs in, not less
than **36.3%**. Combined with BRIEF rule 3 (widening the stop raises payoff and drops win
rate for no expectancy gain), there is no free direction: tighten and cost/R explodes,
widen and expectancy does not move.

## What this does to the power bound

Burst 01: a pre-registered hypothesis needs net µ/σ ≈ 0.059 at 400 trades. With σ ≈ 1.0R
that is **net +0.06R**. Adding the cost floor, the **gross** expectancy required is:

| cell | cost floor (thin) | gross expectancy needed for net +0.06R |
|---|---|---|
| MGC | 0.218 R | **+0.28 R** |
| MCL | 0.363 R | **+0.42 R** |

A gross edge of +0.28R/+0.42R per trade sustained over 400 scalp trades is not a number
this repository has ever produced at any timeframe. **On the cost arithmetic alone, before
any search penalty, MCL 5m is the least likely cell in the entire programme to yield a
live-eligible row, and MCL is the cost-fragile contract precisely because its noise floor
is 15 ticks on a $1 tick.**
