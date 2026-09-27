# BT3 — algorithms

Every number in this file comes from the frozen `csv/raw` snapshot, via the stored artefact
`workspace/strategy_research/scratch/geo_trades.json`, which is read and never written.
Nothing here touches `data/archive/` (BRIEF's 2026-09-27 data ruling, condition 1).

---

## ALGO-1 Account-governor replay over a stored trade stream

- **Implements:** R3-D3 Question 2 and Part B-1 (the `risk/` import boundary), Part B-3
  Channel 4 part (c) (the integer-contract floor), B-4 (`run_portfolio` is not a portfolio),
  III-14 and R3-D5 Tier 2 item 7 — all in `research/R3_path_operation.md`. Plus
  `R3_operating_vocabulary.md` axes S1, S2, S7, S8, P1, P2, P4, P5, P6, P7 and A3.
- **Code:**
  - `backtest/BT3/code/stops.py:1-175` — reconstructs the per-trade stop distance the
    artefact does not carry, and proves the reconstruction.
  - `backtest/BT3/code/governor_replay.py:1-596` — the replay. `replay()` at `:260-388`,
    `static_integer_floor()` at `:390-424`, `floor_by_volatility()` at `:426-456`,
    `measure_stage6()` at `:458-476`, ordering at `:160-186`.
  - `backtest/BT3/code/checks.py:1-140` — five assertions, all passing
    `[measured: python3 code/checks.py → "all checks passed"]`.
  - Output: `code/algo1_report.json`, `code/stops_cache.json`.
- **Fidelity:** **ASKED** — `msgs/04_BT3_R3_verify-ALGO-1.md`, eight questions. No stateful
  number below is reportable as a result until R3 answers Q1 and Q3.

### My reading of the finding

R3 claims four things and I read them as follows.

1. **The backtester and the account rules never meet.** Nothing under
   `futures_agents/backtest/` imports `futures_agents/risk/`, so `AccountConfig`'s nineteen
   operating parameters, the six-rung de-risk ladder, the correlation cap and the integer
   contract floor governed none of the 2,975,629 evaluations. Every published number is
   one-notional-contract, one-position-per-strategy, no account state.
2. **The governors are Channel 2, not Channel 4.** They do not *weight* trades, they *delete*
   them, path-dependently, and deletion moves expectancy where weighting cannot.
3. **The integer floor is the sharpest case.** `contracts_for` floors and never rounds up, so
   when one contract's risk exceeds the budget the trade does not exist. It selects on stop
   distance; under `StopKind.ATR` stop distance is `stop_mult × atr`; therefore integer sizing
   is an unintended volatility-regime entry filter, and some catalogue exits are untradeable
   at $50,000.
4. **It is all measurable with no new backtest**, because 21,954 trades with `ts` and `r` are
   already on disk.

I read (4) as **true for the daily governors and false for the integer floor.** The floor needs
`risk_points`; the artefact has no price, no point distance and no dollar figure among its 17
keys `[measured: sorted(d[0]) → ['arm','base','cell','dir','exitm','mae','mfe','mins','r',
'reason','regime','session','slice','symbol','tf','ts','vol']]`. So the floor half of R3's
Tier 0 item 1 required a reconstruction, which is what `stops.py` is.

### Where I had to choose

Fifteen places the finding was silent. The first five change the answer; the rest are recorded
so they can be overruled.

**1. What the equity curve starts at, and what "the budget" is.**
`AccountConfig.starting_equity = 50_000.0` as shipped. The consequence R3's write-up does not
have: the opening per-trade budget is
`min(usable_buffer × 0.06, equity × 0.0075, max_dollar_risk) = min(240, 375, 500)` =
**$240**, because `base_risk_pct_of_buffer` binds first, not the 0.75%-of-equity ceiling
`[repo-verified: risk/manager.py:155-161; config.py:358-364]`
`[measured: code/checks.py::check_opening_budget → (240.0, 375.0, 500.0)]`. R3's B-3(c) table
worked the floor at $375 and $500; **the account never has that much to spend on one trade**,
so the floor bites harder than the finding says.

**2. Which of `assess`'s nine stages are in.** `assess` runs nine stages
`[repo-verified: risk/manager.py:222-376]`. Calling them piecemeal would mean copying their
order and their short-circuiting, which is how a replay stops being the thing it replays — so
ALGO-1 calls `assess` **whole** and neutralises the four out-of-scope stages through the
proposal's own fields. Stages 1, 2, 3, 7, 9 are IN. Stage 4 (news) is out: `news_risk=NONE`,
no calendar in the artefact, and A-6 shows the backtester could not have applied one. Stage 5
(ATR/median band) is out: `atr=None` disables it `[repo-verified: manager.py:271]`, and it is
an entry filter rather than an account rule. Stage 6 (setup quality) is out, and my first
reason was wrong — I assumed it would empty the replay; measured, **9 of the 176 strategies
clear both floors** (`n ≥ 40` and mean R `≥ 0.08`)
`[measured: measure_stage6() → {'strategies': 176, 'clearing_stage6_floors': 9}]`. So it is out
because it is a *selection* rule and selection has a measured prior against it here, not
because it is vacuous. Stage 8 (cost vs reward) is out: it needs the trade's real first target,
which the artefact does not carry.

**3. Population unit — and the two readings disagree by a factor of 24.** Pooling inflation is
a known defect at three levels here, so ALGO-1 refuses to produce one number over the file:
  - **POOLED** — all 21,954 in one account. 176 strategies across 4 symbols live at once.
    They are 11 nested arms on two base conditions × 2 exits × 4 symbols × 2 timeframes, i.e.
    correlated variants of one signal, so **this is not a portfolio anybody would run.**
  - **PER_STRATEGY** — 176 independent replays, one fresh $50,000 account each, keyed by
    `(symbol, tf, arm, exitm)`. The three slices are disjoint in time and jointly cover the
    span, so one account can run all three.

  **Everything I report as a governor effect is the PER_STRATEGY reading.** The POOLED reading
  is reported as a diagnostic of pooling, never as a result. No z-statistic is attached to
  either: the 176 are correlated variants and D28 applies.

**4. Same-timestamp ordering, and it is not a detail.** 21,954 trades share 3,325 distinct
timestamps and one timestamp carries **74** of them `[measured]`. With
`max_concurrent_positions = 2` and one position per symbol, the within-timestamp order decides
*which* tied trades survive. Primary order is a fixed lexicographic tiebreak
`(ts, symbol, tf, base, arm, exitm, dir)` — deterministic, reproducible, and arbitrary. So I
measured the arbitrariness: five seeded permutations of the within-timestamp order move the
pooled survival rate over **[0.537%, 1.685%]**, a **3.1× spread**
`[measured: order sensitivity taken_pct = [1.203, 0.788, 0.588, 0.537, 1.685]]`. The pooled
reading is tiebreak-dominated. The per-strategy reading is not affected, because a single
strategy is never in a tie with itself.

**5. What a "day" is.** `futures_agents.timeutil.trading_day`, imported not reimplemented —
CME 18:00 ET → 17:00 ET, so an 18:30 Sunday bar is Monday `[repo-verified: timeutil.py:168-180]`.
**One day for the whole account, not one per symbol or per session**, which is what
`AccountState.roll_day` does `[repo-verified: risk/account.py:159-165]`. The artefact's `ts` is
already ET-offset ISO, so `to_et` is identity. 254 trading days over 2025-10-17 → 2026-09-22.

**6. When P&L is realised.** On the **exit's** trading day, not the entry's, because
`close_position` calls `roll_day(when).record(pnl)` with the close time
`[repo-verified: risk/account.py:203-220]`. Exit time `= ts + mins`, where `mins` is
`minutes_held = exit_bar.ts − entry_ts` `[repo-verified: engine.py:512]`. Median hold is short
but the maximum is 20,640 minutes (14 days), so a trade's loss can land on a day it did not
start. This is what makes the daily governors genuinely path-dependent rather than a
per-day partition of the file.

**7. Event order at a tie.** Exits are flushed **before** the entry at the same instant, which
frees the symbol slot. That is the engine's own order: `_manage` at step 2, signal generation at
step 3 of the same bar `[repo-verified: engine.py:296-303]`. `mins` can be 0.0, so this case is
real. Choosing the other way would refuse more trades; I took the engine's order over the
pessimistic one because fidelity to the engine is the point.

**8. Dollars per trade.** `pnl = r × contracts × risk_points × point_value`. `net_dollars =
net_r × risk_dollars` is exactly the engine's own conversion `[repo-verified: engine.py:507]`,
and **cost-in-R is size-invariant** because commission and slippage are both linear in
`contracts` `[repo-verified: costs.py:104-110, 119-122]`, so scaling by `contracts` charges
nothing twice and drops nothing. Costs are already inside the stored `r`.

**9. What I do when the stored trade has no dollar risk — which is all 21,954 of them.**
Reconstruct it, and prove the reconstruction. `stops.py` re-runs the `partner == "none"`
subset of `run_geometry.py` — 22 strategies per cell instead of 286
`[repo-verified: run_geometry.py:110-121]` — over the same deterministic slices of the same
frozen snapshot, then matches every trade back on `(cell, arm, exitm, entry_ts, direction)`.
**The match is exact: 21,954 of 21,954, zero missing, worst `|Δr| = 0.000e+00`**
`[measured: python3 code/stops.py → "stored trades not found in reproduction: 0";
"net_r disagrees by >1e-5: 0 (worst |dr| = 0.000e+00)"]`. `risk_points = |entry_price −
initial_stop|`, which is what the engine divides by to get R and what `contracts_for`
multiplies by `point_value`. The alternative — `stop_mult × atr(signal bar)` — is *not*
equivalent, because the entry gaps and slips away from the signal bar and the engine honours the
original stop level rather than re-deriving it `[repo-verified: engine.py:354-361]`.
**A faithful reconstruction had to use the realised distance, not the modelled one.**

**10. `is_live_eligible`, run both ways because it is not cosmetic.**
`HistoricalPerformance.is_live_eligible` is a property requiring six conditions
`[repo-verified: schema.py:244-254]`, and when it is False `risk_budget` applies **×0.5**
`[repo-verified: manager.py:181-183]`. The BRIEF settles that nothing in this repository is
live-eligible, so `False` is the honest arm and `True` is the neutral one. Both are reported.
`False` halves the budget to $120 and the dominant veto changes identity — see below.

**11. `max_trades_per_day` counts closes, not opens.** `DayState.trades_taken` is incremented
only by `DayState.record`, which runs only on close
`[repo-verified: risk/account.py:67-79, 203-220]`, and `open_position` carries the comment
`self.day.trades_taken += 0  # counted on close, not on open`
`[repo-verified: risk/account.py:198-201]`. **As shipped, the rule does not cap how many trades
a day starts.** I replay it as written (primary) and also as its name reads (`cap_on_open=True`,
labelled `1_trade_cap_on_open(DIVERGENT)` in the output, applied outside `assess` — the only
place in `code/` where a governor runs outside the shipped code, and it is labelled). The
shipped cap does leak: in the placebo arm, 2 days take 7 trades with the cap nominally at 6.

**12. `volatility` is held at `"NORMAL"`.** Stage 7 applies ×0.70 when
`proposal.volatility in ("HIGH","EXTREME")` `[repo-verified: manager.py:177-179]`. The artefact
*does* carry a `vol` label, but it is `Trade.volatility` from the backtester's own bucketing,
not the live layer's field, and feeding it in would mix a volatility penalty into an
account-governor measurement. Held constant. **This is VERIFY Q4 and it may be wrong.**

**13. Concurrency is attributed by symbol.** `assess` stage 3 checks
`st.position_for(proposal.symbol)` *before* the concurrent and correlated caps
`[repo-verified: manager.py:245-252]`, so the live path permits **one position per symbol**,
full stop. On the pooled stream that collapses 22 same-symbol arms into one slot and produces
1,126 `3_symbol_already_held` refusals. On the per-strategy stream it never fires. **The
per-symbol rule is unambiguous in the live code; whether it is the right rule to apply to a
pooled research artefact is VERIFY Q3.**

**14. The correlation cap cannot bind on this population, and that is a finding not a choice.**
`max_correlated_positions = 1` is enforced on `ContractSpec.correlation_group`, and the four
symbols in the artefact have four *distinct* groups: MGC `PRECIOUS_METALS`, MES
`US_EQUITY_BROAD`, MNQ `US_EQUITY_TECH`, MCL `ENERGY`
`[measured: code/checks.py::check_correlation_cap_is_inert]`. So the cap degenerates into the
per-symbol check that already precedes it and **fires zero times**. Note this contradicts the
BRIEF, which says MES/MNQ/NQ/ES are one index complex sharing 0.5–0.8% of rule sets (D14/D41).
Filed as REQ-3.

**15. The placebo.** PIPELINE §4 requires one. The governors' input is the *sequence* of
outcomes, so the control is: **permute the R values count-matched, leaving every timestamp,
stop distance and exposure clash identical.** That destroys any serial structure a
path-dependent governor could be reading while holding the entire static structure fixed. A
governor effect that survives the permutation is reading the calendar and the stop
distribution, not the signal. `placebo_shift` is not used (D42, leaks).

### What it measures

**Mechanical, and not contingent on the fidelity verdict** — properties of the stop
distribution and of `contracts_for` arithmetic, checkable by hand:

**The integer floor at the opening $240 budget deletes 7,767 of 21,954 trades — 35.4%**
`[measured: static_integer_floor() → deleted 7767/21954 (35.38%)]`, and it deletes them
selected on symbol and bar size:

| cell | n | deleted by the floor | median contracts |
|---|---|---|---|
| MGC 240m | 1,204 | **99.42%** | 0 |
| MNQ 240m | 1,293 | **94.59%** | 0 |
| MGC 60m | 4,276 | 53.27% | 0 |
| MNQ 60m | 4,374 | 46.98% | 1 |
| MCL 240m | 1,179 | 29.26% | 1 |
| MES 240m | 1,294 | 27.98% | 1 |
| MCL 60m | 4,243 | 5.09% | 2 |
| MES 60m | 4,091 | 2.22% | 2 |

**So R3's "some catalogue exits are untradeable at the modelled account size" is confirmed and
understated.** It is not one exit on one symbol: on this population **MGC at 4h is untradeable
at 99.4% of its signals and MNQ at 4h at 94.6%**, at both `atr1.0` and `atr1.5`, at a $50,000
account. Both cells have a median of **zero** contracts.

**R3's volatility-filter reading holds, conditioned on symbol and timeframe.** The claim is only
about volatility if survival still varies with the volatility regime once `point_value` and bar
size are held fixed — otherwise the floor is selecting on the contract, which merely *looks*
like volatility. Held fixed `[measured: floor_by_volatility()]`:

| cell | DEAD | LOW | NORMAL | HIGH | EXTREME |
|---|---|---|---|---|---|
| MGC 60m | 68.6 | 69.7 | 48.2 | 37.3 | **14.2** |
| MNQ 60m | 81.8 | 77.4 | 57.0 | 34.3 | **22.7** |
| MES 240m | 94.4 | 91.3 | 64.9 | 48.9 | — |
| MES 60m | 100 | 100 | 99.3 | 96.6 | 91.2 |
| MCL 60m | 100 | 99.8 | 98.0 | 90.3 | 83.8 |
| MCL 240m | 100 | 100 | **63.8** | 100 | 100 |
| MGC 240m | 0.0 | 0.0 | 0.8 | 0.0 | 0.0 |
| MNQ 240m | 0.0 | 0.0 | 6.7 | 0.0 | — |

(percent of trades surviving the floor at $240). **Monotone decreasing in 5 of the 6
unsaturated cells**, and MGC 60m loses 4.8× as many EXTREME trades as DEAD ones. MCL 240m does
not fit — NORMAL survives at 63.8% while DEAD, LOW, HIGH and EXTREME all survive at 100% — and I
am reporting that rather than smoothing it; HIGH there is n=16. So: **integer sizing at this
account size is a volatility filter, and it is a stronger symbol-and-timeframe filter than it is
a volatility one.**

**Stateful, therefore UNVERIFIED.** Reported so the shape is on record, not as results:

*PER_STRATEGY (176 fresh accounts, the non-pooled reading, `is_live_eligible=True`):*
**5,705 of 21,954 trades survive the governors — 26.0%.** Median survival per strategy 26.7%,
range [0%, 100%], 29 of 176 strategies take **no trade at all**. **Zero of 176 accounts failed**
over 254 trading days. And the refusals are almost entirely one governor:

| veto | count | share of 16,249 refusals |
|---|---|---|
| `7_integer_floor_zero_contracts` | 15,769 | **97.05%** |
| `1_buffer_exhausted` | 250 | 1.54% |
| `1_consecutive_losses` | 202 | 1.24% |
| `2_stop_inside_noise_floor` | 23 | 0.14% |
| `1_daily_loss_limit` | 2 | 0.01% |
| `1_trade_cap` | 2 | 0.01% |
| `7_below_min_dollar_risk` | 1 | 0.01% |
| `1_profit_giveback` | 0 | 0 |
| `3_*` (all exposure caps) | 0 | 0 |

**The daily governors R3's Tier 0 item 1 was about — daily loss limit, giveback, trade cap,
consecutive-loss stand-down — account for 206 of 16,249 refusals, 1.27%.** `max_trades_per_day
= 6` **never binds**: no strategy's busiest day exceeds 6 trades, so `days_over_6_taken = 0`
across all 176 `[measured]`. At 60m and 240m bars a single strategy does not generate seven
signals in a session. **The trade cap is inert at this timeframe and only bites when you pool.**

Of the 15,769 floor deletions, **7,728 fire at the opening $240 budget and 8,041 only after the
budget has shrunk** `[measured]`, so about half the floor's bite is the de-risk ladder and the
day-penalties, not the floor's static reach. Median dollar risk actually taken, across
strategies, is **$169** against a $240 opening budget.

*POOLED (the pooling diagnostic, not a result):* **238 of 21,954 taken — 1.08%**, against
26.0% unpooled. **A factor of 24, and it is pooling, not governance.** The extra refusals are
1,126 `3_symbol_already_held` + 126 `3_concurrent_limit` + 276 `1_trade_cap`, all of which exist
only because 22 correlated arms are competing for one symbol slot. Median dollar risk taken
falls to **$38**. Under the honest `is_live_eligible=False` arm the budget halves to $120 and
the dominant veto *changes identity*: `7_below_min_dollar_risk` fires 14,372 times — **the
account is below its own $25 minimum-meaningful-risk floor for 65% of candidates.**

*Placebo (R permuted, everything else identical):* **349 taken — 1.59%**, versus 1.08% real, and
inside the [0.537%, 1.685%] ordering interval. **The governors' deletion count is not reading
the signal.** The placebo also takes 7 trades on 2 days with the cap at 6, which is the
close-counting leak (choice 11) showing up.

### What it does not measure, stated so nobody reads it as more than it is

- **Not a portfolio result and not an expectancy claim.** I have deliberately not quoted the
  surviving series' expectancy as a finding. The equal-weighted per-strategy means are
  −0.1268R taken vs −0.0248R refused over the 113 strategies with ≥10 taken, i.e. **the
  governors kept the worse half** — but that comparison is UNVERIFIED, unpaired, and over
  correlated variants, so it is a number in a lab book, not a result.
- **Search size: 1.** One algorithm, one parameter set (the shipped `AccountConfig` defaults),
  no tuning of anything. The arms are not variants searched over — they are
  `live_eligible ∈ {T,F}` × `cap ∈ {open,close}` plus 5 ordering seeds and 1 placebo, all
  reported, none selected between. Nothing here is compared against `free_t = 5.46` because
  nothing here is a t-statistic.
- **No comparative claim is routed through `T.ab`** (D28). No comparative test is used at all.

---

## Side errand — R3 Tier 0 item 2, `bootstrap_paths(mode="block")` vs `"iid"`

- **Code:** `backtest/BT3/code/block_vs_iid.py`. Output `code/block_vs_iid.json`.
- **Is it one function call?** Yes, one per arm, so it is done. R3 was right about the cost.
- **Does it answer the question it was assigned?** **No, and this is the substantive point.**
  The question was "is the R series serially dependent", because Channel 4b's streak sizing
  needs `Cov(w,R) ≠ 0`. The two modes are two *resamplers*: `iid` destroys serial structure,
  `block` preserves runs of length 10. Comparing their outputs detects dependence only
  indirectly and only at the block scale. A direct test — lag-1 autocorrelation, a runs test,
  Ljung-Box — does not exist anywhere in this repository. REQ-1.

**Measured, at 2,000 runs, `block=10`, `seed=20260922` (montecarlo's own default):**

| unit | p95 max drawdown, iid → block | p95 losing streak, iid → block |
|---|---|---|
| ACCOUNT — pooled stream in `ts` order, n=21,954 | 1642.25R → 1764.37R (**+122.11R**) | 23 → 37 (**+14**) |
| STRATEGY — 155 series with n ≥ 20, 600 runs each | median **−1.11R**, worse in 60/155 | median **−1**, longer in 32, shorter in 104 |

**The two units give opposite answers, and the per-strategy one is the one that bears on
sizing.** At the unit a streak rule would actually run on — one strategy's own sequence — the
block bootstrap is *not* more severe than iid in 95 of 155 series, so there is **no positive
serial dependence detectable at a 10-trade block scale**. The pooled stream's large positive
dependence is what pooling looks like: a block of 10 consecutive elements in timestamp order is
often 10 correlated arms firing on the same bar, since one timestamp carries up to 74 trades.
**That is the pooling defect appearing as autocorrelation, and using it to argue that
equity-curve sizing can work would be wrong.**

**And the block arm has a measured sampling defect.** `bootstrap_paths` draws
`r_values[start:start + block]` with **no wrap-around** `[repo-verified: montecarlo.py:103-107]`,
so element *i* is reachable from only `min(i+1, block)` distinct starts. The first `block − 1`
elements are systematically under-sampled on a linear ramp: on a 40-element series, **index 0
appears at 0.122× its due frequency, index 9 at 1.121×, and the whole tail at 1.123×**, while
`iid` over the same series is flat within [0.988, 1.011]
`[measured: code/checks.py::check_block_bootstrap_undersamples_the_start]`. **The block
bootstrap silently discounts the beginning of every sequence it resamples.** No call site has
ever used `mode="block"`, so the defect has never touched a published number — this is its
first use. Filed as REQ-2; the fix is a circular block, one line.

**Fidelity:** this is not an ALGO and has no fidelity verdict. It is one measurement with its
caveats attached, and the caveats are larger than the measurement.
