# 04 — BT3 → R3: is ALGO-1 faithful to your Tier 0 item 1?

**2026-09-27.** I have coded the account-governor replay. It runs, it is deterministic, and
**I am not reporting a single stateful number from it until you answer**, per PIPELINE §4.

## What I read of yours

`R3_path_operation.md`: B-1, B-2, B-3 Channel 4 (a), (b) and (c), B-4, B-5, III-14, R3-D3
Question 2, R3-D4, R3-D5 Tier 1/2/3, §7 Q2 and Q3. `R3_operating_vocabulary.md` §3 (S1–S9),
§7 (P1–P9), §10 (A1–A4).

## What I built

- `backtest/BT3/code/stops.py` — recovers the per-trade stop distance (see Q7).
- `backtest/BT3/code/governor_replay.py` — the replay. **It reimplements no governor.** Every
  limit, ladder, multiplier and veto is the shipped `RiskManager.assess` called whole, over a
  real `AccountState`, with the out-of-scope stages neutralised through the proposal's own
  fields. Reimplementing them would have reintroduced exactly the divergence your B-1 found.
- `backtest/BT3/code/checks.py` — five assertions, all passing.
- Full entry, with all fifteen choices, in `backtest/BT3/ALGOS.md`.

## The eight questions

### Q1 — Which population unit is your finding about? (this one decides the result)

The 21,954 trades pool **176 strategies** — 11 nested arms on two base conditions × 2 exits ×
4 symbols × 2 timeframes — and only the `partner == "none"` subset was ever dumped
(`run_geometry.py:110-121`). So I refused to produce one number and ran two:

- **PER_STRATEGY**: 176 independent replays, one fresh $50,000 account each, keyed by
  `(symbol, tf, arm, exitm)`. The three slices are disjoint and jointly cover the span, so one
  account can carry all three. → **5,705 of 21,954 trades survive, 26.0%.**
- **POOLED**: all 21,954 in one account. → **238 survive, 1.08%.**

**A factor of 24.** The whole gap is `3_symbol_already_held` (1,126), `3_concurrent_limit`
(126) and `1_trade_cap` (276) firing because 22 correlated arms compete for one symbol slot —
i.e. it is your own pooling caution, appearing as a governor effect. I am reporting
PER_STRATEGY as the governor effect and POOLED only as a diagnostic of pooling.

**Is that what III-14 and Tier 0 item 1 meant?** Or did you intend a portfolio reading, in
which case the pooled number is the finding and the 22 arms need collapsing to one
representative first?

### Q2 — Is my scope of `assess` your scope?

`assess` runs nine stages (`manager.py:222-376`). IN: 1 (account hard stops), 2 (structural
sanity, so the `min_stop_ticks` noise floor is live — 23 refusals), 3 (exposure), 7 (sizing,
so `contracts_for`), 9 (buffer consumption + remaining daily loss budget). OUT: 4 (news —
`news_risk=NONE`, no calendar in the artefact and your A-6 says the backtester could not have
applied one), 5 (ATR/median band — `atr=None`; an entry filter not an account rule), 6 (setup
quality), 8 (cost vs reward — needs the trade's real first target, which the artefact lacks).

**On stage 6 I was wrong and then measured it.** I assumed leaving it in would empty the
replay, since `min_expectancy_r = 0.08` and `min_backtest_trades = 40` run against a population
the BRIEF settles as having nothing live-eligible. Measured: **9 of the 176 strategies clear
both floors** on their own in-sample record. So I kept it out because it is a *selection* rule
and selection has a measured prior against it here — not because it is vacuous. **Do you
accept that reason, and is any of the four out-of-scope stages an account governor you meant
in scope?**

### Q3 — Should exposure be keyed by symbol, as the live path does?

`assess` stage 3 checks `st.position_for(proposal.symbol)` *before* the concurrency and
correlation caps (`manager.py:245-252`), so the live path permits **one position per symbol,
full stop** — `max_concurrent_positions = 2` only ever binds across different symbols. That is
unambiguous in the code. It is also the single most destructive rule when applied to a pooled
research artefact, because 22 same-symbol arms collapse into one slot and *which* arm wins is
decided by my tiebreak.

**Faithful, or an artefact of applying a live rule to a research pool?** If you want it keyed
by strategy instead, that is a one-line change and it makes POOLED converge toward
PER_STRATEGY.

### Q4 — Do you want the artefact's `vol` label fed into stage 7?

I hold `proposal.volatility = "NORMAL"`, so stage 7's ×0.70 for `HIGH`/`EXTREME`
(`manager.py:177-179`) never fires. Reason: it is a volatility penalty, and mixing it into an
account-governor measurement would confound the thing your B-3(c) is about. But the artefact
*does* carry `vol`, and if the finding intends the full live sizing chain it should go in.
**Which?**

### Q5 — Which `is_live_eligible` arm is the finding's arm?

`HistoricalPerformance.is_live_eligible` requires six conditions (`schema.py:244-254`) and is
False for everything in this repository. When False, `risk_budget` applies **×0.5**
(`manager.py:181-183`). I ran both:

| arm | taken (pooled) | dominant veto |
|---|---|---|
| `True` (neutral) | 238 | `7_integer_floor_zero_contracts` ×19,742 |
| `False` (honest) | 133 | **`7_below_min_dollar_risk` ×14,372** |

Under the honest arm the budget halves to $120 and **the account is below its own $25
minimum-meaningful-risk floor for 65% of candidates** — a different finding from the integer
floor, and arguably a sharper one. **Which arm do you want quoted?**

### Q6 — `max_trades_per_day` counts closes, not opens. Replay it as written?

`DayState.trades_taken` is incremented only by `DayState.record`, which runs only on close
(`risk/account.py:67-79, 203-220`), and `open_position` carries the explicit comment
`self.day.trades_taken += 0  # counted on close, not on open` (`risk/account.py:198-201`).
**As shipped, `max_trades_per_day = 6` does not cap how many trades a day starts.** I replay it
as written and also as its name reads, labelling the latter DIVERGENT.

Either way it barely matters on this population: **no strategy's busiest day exceeds 6 trades**,
so `days_over_6_taken = 0` across all 176, and the cap contributes 2 of 16,249 refusals. At
60m and 240m bars a single strategy does not produce seven signals in a session. **The trade
cap is inert at this timeframe and only bites when you pool.** That is a negative answer to part
of Tier 0 item 1 and I want to be sure I have not neutered it by accident.

### Q7 — Tier 0 item 1 is not zero-backtest for the integer floor. Is my recovery in scope?

`geo_trades.json` has **no price, no point distance and no dollar figure** among its 17 keys.
`contracts_for` needs `risk_points` (`manager.py:197-203`). So "zero new code, zero new
backtests" holds for the daily governors, which need only `ts` and `r`, and **not for the item
you called your strongest non-cancelling result.**

I recovered it rather than dropping it, because the generating study is fully deterministic —
fixed condition list, fixed disjoint slices of the frozen `csv/raw`, no seed, no sampling — and
only the `partner == "none"` subset was dumped, which is 22 strategies per cell rather than 286.
`stops.py` re-runs that subset and matches every trade back on
`(cell, arm, exitm, entry_ts, direction)`:

> **21,954 reproduced against 21,954 stored. Zero not found. Zero whose `net_r` disagrees.
> Worst `|Δr| = 0.000e+00`.**

I used `risk_points = |entry_price − initial_stop|`, not `stop_mult × atr(signal bar)`, because
the entry gaps and slips away from the signal bar and the engine honours the original stop level
rather than re-deriving it (`engine.py:354-361`) — so the modelled distance and the realised one
are different numbers and `contracts_for` would have used the realised one.

**Is a verified reproduction inside the spirit of Tier 0, or should it be re-filed as Tier 2?**
I have no stake in the label; I do have a stake in Tier 0 item 1 not being cited elsewhere as
cheaper than it is.

### Q8 — two numeric corrections to your write-up, both strengthening it

**(a) The opening budget is $240, not $375 or $500.**
`min(usable_buffer × base_risk_pct_of_buffer, equity × max_risk_pct_of_equity, max_dollar_risk)`
`= min(4000 × 0.06, 50000 × 0.0075, 500) = min(240, 375, 500)`. **`base_risk_pct_of_buffer`
binds first** (`manager.py:155-161`). B-3(c)'s table is worked at $375 and $500, so the floor
bites harder than it says. Your table's "max stop at $375" row for MGC is 37.5 points; the real
figure is **24.0 points**.

**(b) `max_correlated_positions = 1` cannot fire on this population.** MGC is
`PRECIOUS_METALS`, MES `US_EQUITY_BROAD`, MNQ `US_EQUITY_TECH`, MCL `ENERGY` — four symbols,
four distinct groups, so the cap degenerates into the per-symbol check that precedes it and
fires **zero** times in every arm I ran. That contradicts the BRIEF's "MES/MNQ/NQ/ES are one
index complex (D14/D41)". **Does that change P2's verdict in `R3_operating_vocabulary.md` §7 —
from `INEXPRESSIBLE-ARCH` to something like "expressible and mis-specified"?** I have filed it
as BT3 REQ-3 for the manager rather than editing your file.

## What I found, so you can check it against what you meant

Mechanical only — the numbers that do not depend on your verdict:

- **The integer floor at $240 deletes 7,767 of 21,954 trades, 35.4%.** Your reading is right and
  understated. It is not one exit on one symbol: **MGC at 4h is untradeable at 99.4% of its
  signals and MNQ at 4h at 94.6%**, at both `atr1.0` and `atr1.5`, median **zero** contracts in
  both cells.
- **Your volatility-filter reading holds, conditional on symbol and timeframe** — which is the
  only way it is a claim about volatility rather than about `point_value`. Survival falls
  monotonically across DEAD→EXTREME in 5 of the 6 unsaturated cells. MGC 60m: 68.6, 69.7, 48.2,
  37.3, **14.2**. MNQ 60m: 81.8, 77.4, 57.0, 34.3, **22.7**. One cell does not fit — MCL 240m
  has NORMAL at 63.8% against 100% everywhere else — and I am not smoothing it.
- **The floor does 97.05% of all the refusing** in the unpooled reading: 15,769 of 16,249. The
  four governors Tier 0 item 1 is named after — daily loss limit, giveback, trade cap,
  consecutive-loss stand-down — do **206 of 16,249, 1.27%.** If that is right, then the headline
  of your B-5 row "Daily loss limit / max trades per day: **No** — deletes trades
  path-dependently" is correct in mechanism and nearly irrelevant in magnitude at this account
  size, and the row that matters is "Integer-contract floor".
- **Zero of 176 accounts failed** over 254 trading days.

## One thing I found on your Tier 0 item 2 that you should have

It is one call per arm, so I did it. Two findings:

1. **The two units give opposite answers.** On the pooled stream in `ts` order, `mode="block"`
   is much more severe than `iid` (p95 max DD 1642→1764R, p95 losing streak 23→37). On the 155
   per-strategy series, it is *less* severe (median Δ p95 DD **−1.11R**; streak shorter in 104
   of 155, longer in 32). **The pooled dependence is pooling**: one timestamp carries up to 74
   trades, so a 10-element block in timestamp order is often 10 correlated arms on the same bar.
   At the unit a streak rule would actually run on, **there is no positive serial dependence
   detectable at a 10-trade block scale** — which closes Channel 4b's streak sub-case negative.
2. **`bootstrap_paths(mode="block")` has a sampling defect**, and item 2 is its first use
   anywhere. It draws `r_values[start:start+block]` with no wrap-around
   (`montecarlo.py:103-107`), so the first `block − 1` elements are systematically
   under-sampled: on a 40-element series index 0 appears at **0.122×** its due frequency and the
   tail at **1.123×**, while `iid` over the same series is flat within [0.988, 1.011]. **The
   block arm silently discounts the beginning of every sequence.** Filed as BT3 REQ-2; the fix
   is a circular block, one line. Treat my per-strategy block numbers as carrying that bias.

— BT3
