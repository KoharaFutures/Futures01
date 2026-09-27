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
  - `backtest/BT3/code/stops.py` — reconstructs the per-trade stop distance the artefact does
    not carry, and proves the reconstruction.
  - `backtest/BT3/code/governor_replay.py` — the replay. `replay()`, `static_integer_floor()`,
    `floor_by_volatility()`, `absorbing_boundary()`, `measure_stage6()`, ordering at
    `order_key`/`sort_stream`.
  - `backtest/BT3/code/paired_tests.py` — exact McNemar and exact sign test over the shared
    200-seed ensemble. Named, per PIPELINE §4 obligation 3.
  - `backtest/BT3/code/checks.py` — five assertions, all passing
    `[measured: python3 code/checks.py → "all checks passed"]`.
  - `tests/test_bt3_governor_replay.py` — 10 tests inside the repo suite, including the two that
    pin the barrier semantics `[measured: python3 -m pytest -q tests/test_bt3_governor_replay.py
    → 10 passed]`.
  - Output: `code/algo1_report.json`, `code/paired_tests.json`, `code/stops_cache.json`.
- **Fidelity:** **DIVERGENT → corrected → RE-ASKED.**
  - Cycle 1: asked in `msgs/04_BT3_R3_verify-ALGO-1.md`. R3 ruled **DIVERGENT** in
    `msgs/03_R3_BT3_re-verify-ALGO-1.md` — one material divergence (a suppressed stage-7
    governor), one look-ahead I had missed, one biased tiebreak, and four choices ruled
    FAITHFUL. R3 ruled from the code and the artefact directly because my question had not
    landed when it looked.
  - Cycle 2: all five of R3's ranked items applied, plus the two it asked me to *report*
    (the absorbing boundary, and the capacity slack). **Everything below is the corrected
    version and the cycle-1 numbers are superseded.** Re-asked in
    `msgs/15_BT3_R3_verify-ALGO-1-v2.md` — on the difference only, as R3 asked.

### What R3 ruled DIVERGENT, and what I changed

| # | R3's finding | what I did |
|---|---|---|
| 1 | **Material divergence.** `volatility="NORMAL"` was pinned, suppressing stage 7's ×0.70 for HIGH/EXTREME (`manager.py:177-179`). Stage 7 is IN scope, the artefact carries `vol`, and 27.9% of the stream is HIGH or EXTREME — so the replay *understated* the floor's bite, which is the claim it exists to test. | `volatility=row["vol"]` is now primary; `vol_aware=False` retained as the held-constant control arm. **The static floor deletion rate rises from 35.38% to 41.19%.** |
| 2 | **Intra-timestamp look-ahead I had missed.** 2,900 of 21,954 rows have `mins == 0.0` (mean R **−0.79**) and one timestamp carries 74 rows, so flushing exits at `<= ts` let the governors assess row #40 at instant *T* holding the realised outcomes of rows #1–39 that entered *and exited* at *T*. Directionally biased: it drove de-risk and OBSERVATION_ONLY *within* the instant. | Implemented R3's **barrier**: the whole timestamp group is assessed against the state as of *T−*, all approved opens are applied, then exits at `<= T` are realised. Opens within the group stay visible to later rows in the group — the concurrency caps must count simultaneous positions; only *outcomes* are hidden. `barrier=False` retained to price the leak. |
| 3 | **The "arbitrary" tiebreak was biased.** `sorted(set(symbol)) == ['MCL','MES','MGC','MNQ']` hands the first slot to exactly the two symbols that survive the floor, so a `symbol`-second key front-loads the account with affordable trades. And `taken_pct` is not one quantity with 5 noisy draws — it mostly encodes *whether and when the account died*, so the distribution is bimodal and 5 seeds is two anecdotes. | **Seeded order is now primary over 200 permutations**; lexicographic kept as a labelled reproducibility anchor only. Report per-arm death rate, death date range and `taken` before death. |
| 4 | `order_key` sorted on the **ISO string**, and offsets vary (`-05:00`/`-04:00`), so it was absolute-time-correct by accident of the data rather than by construction. | `key=parse_ts`. |
| 5 | `AccountState.equity_curve` is seeded in `__post_init__` with a **wall-clock** stamp while every later point is stamped at `when=ts`, so it is not monotonic in time for a replay. | Noted in the code and here: **never compute a drawdown, Sharpe or time-to-recovery off `st.equity_curve`.** ALGO-1 tracks peak/min/max-drawdown itself inside `flush`. A comment also records that `close_position`-by-symbol is only unambiguous because stage 3 stays in scope. |

R3 also confirmed four choices FAITHFUL (the $50,000 fresh-account start and the $240 budget;
`trading_day` as the day unit; the concurrency attribution, whose veto counts partition the
stream with no residue; and `pnl = r × dollar_risk` charging cost exactly once), and confirmed
independently that `mins` recovers the absolute exit instant to within 3 seconds so DST-spanning
trades are attributed to the right trading day. Two of its checks caught things I should
report rather than bury: `proposal.session` and `proposal.regime` are **read by nothing** in
`assess`, and the artefact's `session` label is on a different clock from its `ts` (row 0 is
20:00 ET labelled `POST_CLOSE`; 20:00 ET is `ASIA`) — so **no ALGO-1 result may be cut by
`session`.**

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

**4. Same-timestamp ordering, and it is not a detail. [CORRECTED after R3's ruling.]**
21,954 trades share 3,325 distinct timestamps and one timestamp carries **74** of them
`[measured]`. With `max_concurrent_positions = 2` and one position per symbol, the
within-timestamp order decides *which* tied trades survive.

My first version made a fixed lexicographic key `(ts, symbol, tf, ...)` primary and ran five
seeds as a sensitivity. **R3 ruled that DIVERGENT and was right.** `sorted(set(symbol)) ==
['MCL','MES','MGC','MNQ']`, so the "arbitrary" key handed the first slot at every contested
instant to MCL then MES — precisely the two symbols that *survive* the integer floor (MCL 60m
loses 10.2%, MES 60m 9.4%, against MGC 240m's 99.4%). It front-loaded the account with the
trades it could afford. `str(tf)` sorting `'240'` before `'60'` has the same shape of problem.
**No fixed key on a field correlated with sizeability is neutral**, so the repair is not a
better key.

**Now: the seeded order is primary, over 200 permutations, and the lexicographic run is kept
only as a labelled reproducibility anchor.** And `taken_pct` is no longer the primary
statistic, because R3 showed it is not one quantity measured with noise — it mostly encodes
*whether and when the account died* (see choice 16), so its distribution is bimodal and
reporting a mean over it would be reporting a mixture. The primary statistics are the
per-arm death rate, the death date range, and `taken` before death.

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

**7. Event order at a tie. [CORRECTED — this was a look-ahead and R3 caught it.]**
My first version flushed exits at `<= ts`, justified by the engine's manage-then-signal order
`[repo-verified: engine.py:296-303]`. **That justification is right for exits from prior bars
and wrong for exits at the entry instant**, and the difference is not cosmetic: **2,900 of
21,954 rows have `mins == 0.0`** — same-bar exits, 2,600 STOP / 263 TARGET / 37 END_OF_DATA,
**mean R −0.79** — and one timestamp carries 74 rows. So the governors were assessing row #40
at instant *T* while the account already held the **realised outcomes** of rows #1–39 that
entered *and exited* at that same *T*. A live account handed 74 simultaneous signals knows none
of their outcomes. Because the zero-duration set has a strongly negative mean, the leak was
**directionally biased**: it drove the account into de-risk and OBSERVATION_ONLY *within the
instant*, suppressing the later trades at that timestamp, and it fed both
`1_consecutive_losses` and the crossing of the absorbing boundary — the two places the result
is most fragile.

**Now: the barrier.** The whole timestamp group is assessed against the state as of *T−*, all
approved opens are applied, and only then are exits at `<= T` realised. Opens *within* the
group remain visible to later rows in the group, which is correct and necessary — the
concurrency and per-symbol caps must count simultaneous positions. Only *outcomes* are hidden.
`barrier=False` is retained as an arm so the leak can be priced rather than merely removed.

**A defect in my own first implementation of this, found and fixed, because it is the exact
shape of mistake that makes a look-ahead fix look free.** Restructuring the loop to iterate
*timestamp groups* made `flush()` run once per group, so **`barrier=False` stopped reproducing
the leak** — it had become a barrier too, differing only in whether same-instant exits land at
the end of the group or the start of the next. The "removing the barrier changes nothing"
reading I got from that run was therefore an artefact of comparing the barrier with itself.
`barrier=False` now flushes **before every row**, which is what the pre-barrier code did, and
two tests pin the semantics so it cannot come back:
`tests/test_bt3_governor_replay.py::test_barrier_hides_same_instant_outcomes_from_same_instant_decisions`
(three simultaneous signals on three symbols: with the barrier the third is refused at
`3_concurrent_limit` because the account genuinely holds two positions; without it all three
are taken because each is closed out before the next is assessed) and
`::test_barrier_hides_same_instant_losses_from_the_daily_ledger` (four simultaneous losses:
without the barrier `day.consecutive_losses` reaches 3 *inside the instant* and
`1_consecutive_losses` fires; with it, it never does).

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

**12. `volatility` now comes from the artefact. [CORRECTED — this was the material divergence.]**
Stage 7 applies ×0.70 when `proposal.volatility in ("HIGH","EXTREME")`
`[repo-verified: manager.py:177-179]`. My first version pinned it to `"NORMAL"` on the grounds
that it is a volatility penalty rather than an account governor. **R3 ruled that DIVERGENT by
my own taxonomy, and it is right**: the multiplier fires *inside stage 7*, which I declared IN.
The volatility *filter* is stage 5, which I disabled correctly and for a different reason
(`atr=None`, and it needs an ATR/median ratio the artefact lacks). Stage 5 OUT with the stage-7
multiplier IN is a consistent position; stage 7 IN with one of its multipliers pinned is not.
And unlike `news_risk` — genuinely OUT because no event calendar exists to inform it — **the
artefact carries `vol` per trade: 3,853 HIGH and 2,267 EXTREME, 6,120 rows, 27.9% of the
stream** `[measured]`.

It also biased the answer in the direction that matters: at ×0.70 the opening budget is $168
rather than $240, which **deletes 1,275 more trades statically**, taking the floor from 35.38%
to **41.19%** of the stream. So the first version *understated* the floor's bite, which is the
claim the algorithm exists to test.

`vol_aware=True` is now primary; `vol_aware=False` is retained as the held-constant control,
because **the difference between the two arms is itself the measurement** — it separates the two
independent channels through which volatility reaches the floor (a wider ATR stop, and a
smaller budget). The `live_eligible` both-arms treatment was the model for this, and R3 asked
for the same shape. Alongside: `analyst_agreement=0.0` is a true no-op (the ×0.60 needs `< 0`)
and stays; `news_risk=NONE` stays OUT.

**13. Concurrency is attributed by symbol. [RULED FAITHFUL — do not re-key.]** `assess` stage 3
checks `st.position_for(proposal.symbol)` *before* the concurrent and correlated caps
`[repo-verified: manager.py:245-252]`, so the live path permits **one position per symbol**, full
stop, and `max_concurrent_positions = 2` only ever binds across different symbols. On the pooled
stream that collapses 22 same-symbol arms into one slot and dominates the pooled refusal count.

I asked whether that was the right rule to apply to a research pool. R3 ruled **FAITHFUL and
explicitly told me not to re-key it to strategy**: re-keying would not adjust the population, it
would *invent a capability the live system does not have* — two strategies long MGC is one MGC
position with two owners, which nothing in `AccountState` can represent, and `close_position`
resolves by symbol `[repo-verified: risk/account.py:203-208]` so it would be ambiguous the moment
two same-symbol positions coexisted. **A divergence that makes the state model incoherent is worse
than the artefact it was trying to fix.** Accepted.

And the question dissolves at the unit that matters: **at PER_STRATEGY stage 3 fires exactly zero
times, structurally.** `engine.py:304-309` skips an already-positioned strategy, so no strategy in
`geo_trades.json` ever has two overlapping trades, so `position_for(symbol)` in a one-strategy
account can never find one. Stage 3 is redundant with the engine's own skip rule here — faithful
*and* inert, for a reason that is a property of how the artefact was generated.

**14. The correlation cap cannot bind on this population, and that is a finding not a choice.**
`max_correlated_positions = 1` is enforced on `ContractSpec.correlation_group`, and the four
symbols in the artefact have four *distinct* groups: MGC `PRECIOUS_METALS`, MES
`US_EQUITY_BROAD`, MNQ `US_EQUITY_TECH`, MCL `ENERGY`
`[measured: code/checks.py::check_correlation_cap_is_inert]`. So the cap degenerates into the
per-symbol check that already precedes it and **fires zero times**. I filed the apparent conflict
with the BRIEF ("MES/MNQ/NQ/ES are one index complex", D14/D41) as REQ-3 rather than editing
anyone's file, and it is **ruled**
`[msgs/09_manager_BT3_requests-ruling.md]`: neither horn. The BRIEF's claim is about **rule-set
overlap between sampler populations**; `correlation_group` is about **price co-movement for
sizing**; different objects, no defect. But the measurement survives the distinction, and the
ruling is that splitting the index complex into `US_EQUITY_BROAD` and `US_EQUITY_TECH` is **too
fine for a cap whose purpose is "do not hold two positions that are the same bet"** — so the
mapping is mis-specified for this consumer. R3 has moved P2 in
`R3_operating_vocabulary.md` §7 from `INEXPRESSIBLE-ARCH` to `EXPRESSIBLE-MIS-SPECIFIED`
`[msgs/10_R3_BT3_re-verify-ALGO-1-questions.md]`.

**The caveat travels with the finding:** "the cap is inert" is measured on four symbols in four
groups, which is a property of *this population*. It is **not** evidence the cap would be inert on
a population containing MES **and** ES.

**15. The placebo.** PIPELINE §4 requires one. The governors' input is the *sequence* of
outcomes, so the control is: **permute the R values count-matched, leaving every timestamp,
stop distance and exposure clash identical.** That destroys any serial structure a
path-dependent governor could be reading while holding the entire static structure fixed. A
governor effect that survives the permutation is reading the calendar and the stop
distribution, not the signal. `placebo_shift` is not used (D42, leaks).

**It runs over the same 200 seeds as the primary arm**, not once. A single placebo run against
a 200-seed distribution is not a control when the ordering spread is larger than most of the
effects being measured. Sharing the seeds also makes every arm **paired**, which is what lets
`paired_tests.py` use an exact McNemar (on the binary "did this account die") and an exact sign
test (on per-seed `taken`) instead of an unpaired test that would discard the largest source of
common variance. D28 is this repo's standing warning about exactly that.

**16. The absorbing state, which I did not anticipate and which R3 solved.** R3 found, and
`absorbing_boundary()` reproduces from the shipped config alone, that
`budget = min(usable_buffer × 0.06, equity × 0.0075, 500) × derisk_multiplier` falls below
`min_dollar_risk = $25` at a **drawdown from peak of $2,800**, where it is **$21.60**
`[measured: absorbing_boundary() → {'drawdown_at_which_the_account_dies': 2800.0,
'budget_there': 21.6, 'dollars_of_headroom_left_unused': 2200.0,
'derisk_multiplier_there': 0.3}]`. Stage 7 then vetoes **every** proposal at
`budget < min_dollar_risk` *before* `contracts_for` is reached
`[repo-verified: risk/manager.py:325-329]`. Past that point equity can move only through
already-open positions; once they close it is frozen, `peak_equity` never falls, so the budget
never recovers.

**The account is dead and `has_failed` is False, with $2,200 of the $5,000 failure buffer
never spent.** So the shipped configuration has a **dead-but-not-failed absorbing state, and
`max_total_drawdown` is unreachable from above it** — which is why every run reports
`failed=False`. The step is also discontinuous: at a $2,799 drawdown the budget is $36.03, at
$2,800 it is $21.60, because the de-risk ladder steps from ×0.50 to ×0.30. ALGO-1 therefore
tracks and reports `absorbing`, `death_index`, `death_ts`, `death_drawdown` and
`taken_before_death` per run, and **the death rate is a primary statistic.**
### What it measures

All of it is the corrected (cycle-2) replay. Reported in three tiers by how much the fidelity
verdict can still move it.

#### Tier A — the structural result, which needs no trade data at all

**The shipped `AccountConfig` has a dead-but-not-failed absorbing state at a $2,800 drawdown,
and `max_total_drawdown` is unreachable from above it.**

Past a $2,800 drawdown from peak the per-trade budget is **$21.60**, below
`min_dollar_risk = $25`, and stage 7 vetoes every proposal *before* `contracts_for` is reached
`[repo-verified: risk/manager.py:325-329]`. Equity can then move only through already-open
positions; once they close it is frozen, `peak_equity` never falls, so the budget never
recovers. Equity there is $47,200 against a failure threshold of $45,000 —
**$2,200 of the $5,000 drawdown allowance is never spendable**
`[measured: absorbing_boundary() → {'drawdown_at_which_the_account_dies': 2800.0,
'budget_there': 21.6, 'equity_there': 47200.0, 'dollars_of_headroom_left_unused': 2200.0,
'derisk_multiplier_there': 0.3, 'last_live_drawdown': 2799.0,
'budget_one_step_earlier': 36.03}]`.

The boundary is a **discontinuity, not a fade**: $36.03 at a $2,799 drawdown, $21.60 at
$2,800, because the de-risk ladder steps ×0.50 → ×0.30 there. This is derived from
`config.py` and `risk/manager.py` alone — no trade data, no ordering choice, no fidelity
question can move it. **R3 found it; I reproduced it in code rather than citing it, because it
is now the headline.** It also explains why every arm reports `failed=False`: the account
cannot reach its own failure threshold, so risk-of-ruin as this repo models it is measuring the
wrong event.

#### Tier B — mechanical, checkable by hand, independent of the replay's path

**The integer floor at the opening $240 budget deletes 9,042 of 21,954 trades — 41.19%**
`[measured: static_integer_floor(vol_aware=True) → deleted 9042/21954 (41.19%)]`, against
**35.38%** with the volatility multiplier pinned
`[measured: static_integer_floor(vol_aware=False) → 7767/21954]`. So **the ×0.70 alone deletes
1,275 more trades** — and R3 independently predicted 1,272 from the HIGH/EXTREME subset, which
agrees to 3 rows out of 6,120 (the difference is `risk_points` rounded to 8dp in the cache
versus the raw `|entry − stop|`)
`[measured: HIGH/EXTREME n=6120, keeps 3627 at $240 and 2352 at $168 → 1275]`.

**But 41.19% is a knife-edge, not a constant, and the headline is wrong without this.** The
stop-distance distribution is concentrated right at the $240 boundary, so the deletion rate is
steeply elastic in the budget `[measured: floor_budget_sensitivity()]`:

| budget | $100 | $168 | **$240** | $375 | $500 | $1000 |
|---|---|---|---|---|---|---|
| deleted, vol-pinned | 78.1% | 57.0% | **35.4%** | 14.7% | 7.5% | 0.8% |
| deleted, vol-aware | 80.4% | 60.8% | **41.2%** | 20.0% | 10.5% | 1.6% |

**Elasticity near $240 is ≈ 2.0** — a 1% budget cut deletes about 2% more of the stream. Two
consequences worth stating plainly. First, R3's B-3(c) assumption of $375/$500 would have
measured **14.7%/7.5%**, so the $240 correction more than doubles the effect. Second, any
result of the form "the floor deletes X%" is a statement about one account size and must always
carry it.

Deletions by cell, vol-aware:

| cell | n | deleted by the floor | median contracts |
|---|---|---|---|
| MGC 240m | 1,204 | **99.42%** | 0 |
| MNQ 240m | 1,293 | **94.59%** | 0 |
| MGC 60m | 4,276 | 61.34% | 0 |
| MNQ 60m | 4,374 | 55.85% | 0 |
| MCL 240m | 1,179 | 30.11% | 1 |
| MES 240m | 1,294 | 29.60% | 1 |
| MCL 60m | 4,243 | 10.18% | 2 |
| MES 60m | 4,091 | 9.44% | 2 |

**R3's "some catalogue exits are untradeable at the modelled account size" is confirmed and
understated.** It is not one exit on one symbol: **MGC at 4h is untradeable at 99.4% of its
signals and MNQ at 4h at 94.6%**, at both `atr1.0` and `atr1.5`, on a $50,000 account, with a
median of **zero** contracts in both cells.

**R3's volatility-filter reading holds, and the corrected arm makes it a cliff.** The claim is
only about volatility if survival varies with the regime once `point_value` and bar size are
held fixed — otherwise the floor is selecting on the contract. Percent surviving the floor,
conditioned on `(symbol, tf)` `[measured: floor_by_volatility()]`:

| cell | DEAD | LOW | NORMAL | HIGH | EXTREME |
|---|---|---|---|---|---|
| MGC 60m | 68.6 | 69.7 | 48.2 | **2.5** | **1.3** |
| MNQ 60m | 81.8 | 77.4 | 57.0 | **4.8** | **1.1** |
| MES 240m | 94.4 | 91.3 | 64.9 | **2.2** | — |
| MES 60m | 100 | 100 | 99.3 | 80.3 | 64.6 |
| MCL 60m | 100 | 99.8 | 98.0 | 75.8 | 70.4 |
| MCL 240m | 100 | 100 | **63.8** | 75.0 | 88.5 |
| MGC 240m | 0.0 | 0.0 | 0.8 | 0.0 | 0.0 |
| MNQ 240m | 0.0 | 0.0 | 6.7 | 0.0 | — |

Monotone decreasing in **5 of the 6** unsaturated cells, and on MGC 60m a HIGH-volatility
signal is **27× less likely to be affordable than a DEAD one**. The two channels compound:
HIGH/EXTREME trades have wider ATR stops *and* a 30%-smaller budget, and because the stop
distribution sits on the boundary the second channel is what turns a gradient into a cliff —
the vol-pinned arm has MGC 60m HIGH at 37.3% rather than 2.5%.

**MCL 240m does not fit and I am not smoothing it**: NORMAL survives at 63.8% while DEAD, LOW,
HIGH and EXTREME all survive better. HIGH there is n=16 and EXTREME n=52 against NORMAL's
n=954, so it is plausibly small-sample, but it is one cell out of six behaving backwards and it
should be checked before the monotonicity is quoted as general.
#### Tier C — the stateful replay, corrected, with R3's cycle-2 conditions applied

**PER_STRATEGY — 176 fresh $50,000 accounts, keyed by `(symbol, tf, arm, exitm)`. R3 ruled this
the finding's unit, not a close call.** Its reasoning: Tier 0 item 1 names five *account*
governors, and the question the item exists to answer is "if a strategy has an edge, do the
account governors delete enough of its trades to change its own measurement?" The pooled figure
answers a different question whose answer was already known (correlated arms cannibalise) and is
already R3-B-4.

**5,537 of 21,954 trades survive — 25.22%**, against 5,705 (25.99%) with the volatility
multiplier pinned. **2 of 176 accounts reached the absorbing state; 0 of 176 hard-failed.** And
the refusals are one governor:

| veto | count | share of 16,417 refusals |
|---|---|---|
| `7_integer_floor_zero_contracts` | 16,184 | **98.58%** |
| `1_consecutive_losses` | 205 | 1.25% |
| `2_stop_inside_noise_floor` | 23 | 0.14% |
| `7_below_min_dollar_risk` | 3 | 0.02% |
| `1_trade_cap` | 2 | 0.01% |
| `1_daily_loss_limit`, `1_profit_giveback`, and **every `3_*` exposure cap** | **0** | 0 |

**So the four daily governors Tier 0 item 1 is named after — daily loss limit, giveback, trade
cap, consecutive-loss stand-down — account for 207 of 16,417 refusals, 1.26%, and two of the four
never fire at all.** At this account size the integer floor is not one governor among nineteen:
it is the governor.

**Why stage 3 fires exactly zero times here, which is structural rather than lucky** (R3's Q3):
the stored artefact already has one-position-at-a-time baked in, because
`engine.py:304-309` skips a strategy that is already positioned. **No strategy in
`geo_trades.json` ever has two overlapping trades**, so `position_for(symbol)` in a
one-strategy account can never find one. Stage 3 is faithful *and* redundant with the engine's
own skip rule at this unit. R3 ruled explicitly: **do not re-key exposure to strategy** — that
would invent a capability the live system does not have, since two strategies long MGC is one
MGC position with two owners and `close_position` resolves by symbol.

`max_trades_per_day = 6` **never binds on a single strategy.** No strategy's busiest day exceeds
6 and `days_over_6_taken = 0` across all 176; the modal busiest day is 2–3 trades
`[measured: max_taken_in_a_day {0:30, 1:15, 2:44, 3:45, 4:24, 5:13, 6:5}]`. At 60m and 240m bars
a single strategy does not generate seven signals in a session. **The cap is inert at this
timeframe and only bites when you pool.** And it is 6 for the *whole account across all four
symbols and both timeframes*, not 6 per symbol.

Of the 16,184 floor deletions, **7,766 fire at the opening budget and 8,418 only after the
budget has shrunk**, so roughly half the floor's bite is the de-risk ladder rather than its
static reach. Median dollar risk actually taken is **$166.50** against a $240 opening budget.

**Conditioned on `(symbol, tf)`, as R3 required — pooled across cells the [0%, 100%] range is
uninterpretable.** R3 predicted "eight tight clusters". **Half right, and the other half matters:**

| cell | strategies | pooled in cell | median | min–max | IQR | take **zero** trades |
|---|---|---|---|---|---|---|
| MES 60m | 22 | 39.8% | **64.0%** | 16.4–85.7 | 36.7 | 0 |
| MCL 60m | 22 | 42.6% | 49.3% | 25.0–85.4 | 28.3 | 0 |
| MCL 240m | 22 | 40.0% | 39.6% | 24.5–77.8 | 26.8 | 0 |
| MES 240m | 22 | 32.8% | 36.7% | 13.0–100.0 | 39.3 | 0 |
| MNQ 60m | 22 | 13.1% | 17.4% | 4.2–74.7 | 11.8 | 0 |
| MGC 60m | 22 | 13.9% | 12.8% | 0.0–66.0 | 20.1 | 1 |
| MNQ 240m | 22 | 2.9% | **1.4%** | 0.0–22.2 | 5.5 | **11** |
| MGC 240m | 22 | 0.3% | **0.0%** | 0.0–4.2 | 0.0 | **18** |

The cells are **well separated** — medians span 0.0% to 64.0% and the ordering is exactly the
floor's ordering — so the pooled median of 26.7% was indeed describing a mixture and should not
have been the headline. But they are **not tight**: within-cell IQRs run to 39.3 points, so the
same governors applied to two arms of the *same base condition on the same symbol and
timeframe* can survive at 13% or at 100%. The floor discriminates between cells and, within a
cell, between arms whose stop distances differ.

**The sharpest single statement in the whole replay: 18 of 22 MGC 4h strategies and 11 of 22
MNQ 4h strategies take not one trade on a $50,000 account.** Not "underperform" — do not exist.

**POOLED — 200 seeded within-timestamp orders. A diagnostic of pooling, never a result.**
Median survival **1.011%** of candidates, p05–p95 **[0.647%, 1.257%]**, versus 25.22% unpooled.
**A factor of 25, and R3's decomposition shows it is not about governors at all**: the gap is
`3_symbol_already_held` + `3_concurrent_limit` + `1_trade_cap`, and stage 3 is *exposure*, which
is not one of the five rules the finding names. A number whose variance is dominated by a rule
outside the hypothesis is a diagnostic. **26 of 200 orderings (13.0%) drove the account into the
absorbing state**, death dates 2026-01-22 … 2026-03-09, median 199.5 trades taken before it,
median max drawdown **$2,670** — $130 short of the $2,800 cliff, so the survivors survive
narrowly.

One capacity check, because "1% taken" invites the reader to assume saturation: the pooled
stream demands 22,325,550 position-minutes over a 490,320-minute span, so two concurrent slots
could service at most **4.39%** of it — comfortably above the observed 0.65–1.26%. **The
concurrency ceiling is slack and never binds, because the floor deletes most candidates before
exposure can accumulate.** Not saturation.
#### The controls and the tests — corrected, after the coordinator caught an invalid comparison

**First, the error, because it was mine and it was in the operation rather than the data.** Cycle 2
of this file reported the placebo comparison as a null on the grounds that "p = 0.0288 and
p = 0.0131 do not clear 2.039 free t-units". **That is not a comparison.** The deflation rule is
stated in t-units — searching *n* variants buys about `sqrt(2·ln n)` free ones — so a result is
judged by converting **its own statistic** to a z and comparing *that* to the threshold. I
compared a p-value to a t-value, which is an operation with no meaning, and it produced the
answer I would have got from eyeballing "0.029 looks weak".

Converted properly, `z = Φ⁻¹(1 − p/2)`: **|z| = 2.186 on deaths and 2.480 on `taken`.** Both are
*above* 2.039. And I checked the one excuse available — that an exact test on 200 discrete paired
seeds should not be read through a normal quantile — and it **pushes the other way**: the
mid-p correction gives |z| = 2.250 and 2.511, i.e. *larger*, because discreteness makes an exact
test conservative `[measured: code/paired_tests.py mid_p() vs binom_two_sided()]`. So discreteness
cannot rescue the claim and was never the explanation. `z_from_p` and `mid_p` are now in
`paired_tests.py` and **every table below carries the z beside the p**, with an explicit
`CLEARS / does not` verdict, so this cannot recur silently.

**Second, what I did about it rather than simply weakening a sentence.** The global R permutation
I had used is *not* a signal-layer placebo, and I should have caught that before quoting it.
Permuting R across the whole stream destroys three associations at once
`[measured: over the 21,954 cached rows]`:

| association destroyed | real | after global permutation |
|---|---|---|
| R ↔ exit reason | STOP **−0.870**, TARGET **+1.478** | STOP −0.063, TARGET −0.069 |
| R ↔ holding duration | `mins == 0` → −0.792, `> 1440` → +0.348 | flat |
| R ↔ symbol (and hence dollar risk per contract, which varies 3×: $98.5 MCL to $289 MGC) | MCL −0.111 … MGC −0.033 | flat |

Only the first of those is remotely near the entry; the other two are exit-geometry and contract
facts. **So a real-vs-global-placebo difference could never have been attributed to the entry, in
either direction.** PIPELINE §4 asks for the *signal layer* replaced; I had replaced the outcome
layer.

So I added two **stratified** placebos, which permute R only within strata that hold those
associations fixed — a STOP's R can land only on another STOP of the same symbol and timeframe —
leaving **only the time-ordering of outcomes** destroyed, which is the single thing a
path-dependent governor can read `[code: governor_replay.py permute_r()]`. Verified to work:
both stratified arms preserve STOP −0.870 / TARGET +1.478 exactly, while the global arm flattens
them `[measured]`.

**Third, the result. Search size is now 12** — six comparisons × two statistics, all reported, none
discarded — so `free_t = sqrt(2·ln 12) = **2.229**`. Raising my own threshold was the price of
adding arms rather than defending the one I had, and it does not rescue the failed comparison,
which is the point.

| comparison vs the neutral arm | deaths: rate, \|z\| | `taken`: median per-seed diff, \|z\| |
|---|---|---|
| **volatility multiplier pinned** | 13.0% → 41.0%, **\|z\| = 6.164 CLEARS** | −1 trade, \|z\| = 0.643 |
| **`is_live_eligible=False`** (honest) | 13.0% → 0.0%, **\|z\| = 5.543 CLEARS** | −5, \|z\| = 1.208 |
| barrier removed (look-ahead priced) | 13.0% → 11.5%, \|z\| = 0.304 | +17, **\|z\| = 4.721 CLEARS** |
| placebo **global** (ordering control, *not* signal-layer) | 13.0% → 6.0%, \|z\| = **2.186** (mid-p 2.250) | −19, **\|z\| = 2.480 CLEARS** |
| placebo **stratified (symbol, tf, reason)** | 13.0% → 8.0%, \|z\| = 1.549 | **+3, \|z\| = 0.000** |
| placebo **stratified (strategy, reason)** | 13.0% → 9.0%, \|z\| = 1.239 | −19, **\|z\| = 4.161 CLEARS** |

**The answer to "does the placebo clear": on `taken`, two of the three constructions clear and one
is a perfect null, and the spread straddles the threshold from 0.000 to 4.161. On deaths, none of
the three clears, and all three agree in direction and magnitude** (real dies more; discordant
pairs 25/11, 22/12, 20/12). The global arm's 2.186 sits a whisker below 2.229 and its mid-p a
whisker above: **that comparison is on the threshold and I am not claiming either side of it.**

**So the sentence I wrote must be withdrawn, and it cannot be replaced by its opposite either.**
What I previously wrote —

> ~~"Which trades the governors delete is a property of the stop distribution and the calendar,
> not of the entry."~~

— is **withdrawn**. The honest replacement is a statement of what the design can and cannot
separate:

> **The governors' deletion count does depend on the sequence of realised outcomes** — every arm
> that perturbs that sequence and differs from the real one differs in the same direction (the real
> stream takes ~19 fewer trades per seed and dies more often than its permutations). **But this
> design cannot attribute that to the entry**, because no arm here replaces the signal layer: they
> replace the outcome layer under different stratifications, and the stratification decides the
> answer. Testing entry-dependence needs random entry bars run through the same exits and the same
> governors — a new backtest, not a replay of a stored artefact.

**And the disagreement between the two stratified arms is itself informative, which is why I am
recording the mechanism rather than averaging over it.** The medium strata are 40 groups of median
size 236, so a within-stratum permutation mostly exchanges R **between the 22 correlated arms
firing at the same timestamp** — which the account cannot distinguish, since whichever arm wins
the symbol slot draws a similar R either way. Hence the perfect null (100 vs 99). The tight strata
are 695 groups of median size 10 confined to one strategy, so the permutation mostly moves R
**across time within a strategy**, between the three disjoint slices — which changes *when* a
given strategy's losses arrive. That arm clears at 4.161. **The quantity the account is sensitive
to is therefore the temporal clustering of one strategy's own outcomes, not the cross-sectional
assignment of outcomes at an instant.** That is a statement about the R sequence, and it points
away from the entry rather than towards it.

The tight arm carries one caveat that weakens it slightly: 124 of its 695 strata have size 1, so
**0.56% of trades keep their own R** and cannot be permuted `[measured]`. That biases it *towards*
the real arm, so it understates rather than overstates its own difference.

**Direction, stated because it is not flattering under any reading and should not be lost:** the
real stream **dies more often and takes fewer trades** than every placebo that differs from it.
Nothing here is an edge claim, and nothing here suggests the governors improve anything.

**Two results survive all of this untouched**, because they are comparisons between governor
configurations rather than against a placebo, and both clear by a wide margin on the statistic
they should be judged on:

**At this account size every governor that shrinks position size is net protective, because the
realised drawdown scales with size faster than the absorbing boundary moves.**

| arm | per-trade budget | absorbing boundary | median max drawdown | maxDD / boundary | died |
|---|---|---|---|---|---|
| volatility pinned | $240 always | $2,800 | $3,079 | **1.100** | 41.0% |
| neutral | $240, ×0.70 on HIGH/EXTREME | $2,800 | $2,670 | 0.954 | 13.0% |
| honest (`is_live_eligible=False`) | $120, ×0.70 on HIGH/EXTREME | **$2,334** | $2,038 | **0.873** | **0.0%** |

Halving the budget takes the cliff to 83% of its depth and the drawdown to 76% of its size, so the
arm with *less* headroom is the safer one. **`max_drawdown / absorbing_boundary` is the whole
predictor of survival and it falls monotonically as the governors tighten.** Two governors that
look like pure Channel-4a variance transforms are **Channel-2 survival effects** at $50,000,
because survival is a threshold on the *path* and not on the mean. |z| = 6.164 and 5.543 against
free_t = 2.229. **This is a risk-management result. It is not a trading edge and it does not make
anything profitable.**

**The look-ahead I removed inflated the trade count and did not affect survival.** With the leak
in, the account takes 17 more trades per seed (|z| = 4.721) while the death rate is unchanged
(|z| = 0.304). R3's mechanism: a position that vanishes before the next same-instant row is
assessed never occupies a concurrency slot, so the leak manufactures capacity. My cycle-1 reading
of this ("not detectable") was wrong for the reason recorded under choice 7 — a bug in my own fix.

One robustness result unchanged: **the `cap_on_open` divergence is empirically inert.** `taken` and
`final_equity` are identical with the cap counted on closes and on opens in every anchor arm.

#### The determinism proof, which R3 asked be reported as a finding in its own right

`stops.py` reproduces the generating study's 21,954 trades exactly: **zero not found, zero whose
`net_r` disagrees, worst `|Δr| = 0.000e+00`**, matched on
`(cell, arm, exitm, entry_ts, direction)`. R3's reading, which I accept: this does not merely
recover a missing field, **it establishes that the generating study is deterministic** — which
nothing in this repository had established. It carries an expiry clause: the recovery exists only
while `run_geometry.py`, `toolkit.disjoint_slices` and the frozen `csv/raw` snapshot all still
agree, so it is a repair with a shelf life and not a substitute for the manager's `R-8` field
discipline.

R3 also asked that the choice of `risk_points = |entry_price − initial_stop|` over
`stop_mult × atr(signal bar)` be on record, because it is the kind of thing that gets simplified
later: the entry gaps and slips away from the signal bar and the engine honours the original stop
level rather than re-deriving it `[repo-verified: engine.py:354-361]`, so the modelled and
realised distances are different numbers and a live `contracts_for` would size off the realised
one. **Using the modelled distance would have made the floor look less binding on exactly the
gappy trades where it binds most.**

### What it does not measure, stated so nobody reads it as more than it is

- **Not a portfolio result, and not an expectancy claim.** I have deliberately not promoted the
  surviving series' expectancy to a finding. The equal-weighted per-strategy means are roughly
  −0.13R taken against −0.02R refused, i.e. the governors appear to keep the *worse* half — but
  that comparison is over correlated variants with no paired control on the R series itself, and
  the population it is drawn from is settled negative everywhere anyway. **A governor cannot
  rescue a negative E[R] and nothing here suggests one did.** It is a lab-book number.
- **Nothing here is a search for a configuration that improves anything.** The
  `AccountConfig` defaults are used as shipped throughout; no parameter was tuned, scanned or
  chosen. Every arm exists to isolate a mechanism, and all arms are reported.
- **Search size: 12 tests**, all in `paired_tests.py`, all reported, none discarded.
  `free_t = sqrt(2·ln 12) = 2.229`, and **the comparison is |z| against that, not p against
  that** — see the controls section for the error I made here and its correction. Four of the
  twelve clear: the two size-reduction survival effects (|z| = 6.164 and 5.543), the look-ahead's
  effect on trade count (4.721), and the tight-stratified placebo's effect on trade count
  (4.161). **The claim that the deletions are entry-independent is withdrawn** — no arm in this
  design replaces the signal layer, so entry-dependence is untested here, not refuted.
- **Entry-dependence is out of reach for a replay.** Testing it needs random entry bars run
  through the same exits and the same governors — a new backtest, which is more than an artefact
  replay. All three placebos replace the *outcome* layer, and the stratification decides the
  answer (|z| on `taken` spans 0.000 to 4.161).
- **No comparative claim is routed through `T.ab`** (D28). Exact McNemar and an exact sign test,
  both paired on the shared seeds, are the only tests used and both are named in the table.
- **`session` cuts are forbidden on this artefact.** Its `session` label and its `ts` are on
  different clocks (row 0: 20:00 ET labelled `POST_CLOSE`; 20:00 ET is `ASIA`), so a day cut and
  a session cut would disagree. R3 found this; nothing in `assess` reads `session`, so no
  ALGO-1 number is affected, but no future cut may use it without settling it first.
- **`AccountState.equity_curve` is unusable for any path statistic here**: it is seeded with a
  wall-clock stamp while every later point is stamped at the replay's own `ts`, so it is not
  monotonic in time. ALGO-1 tracks peak, trough and max drawdown itself.
- **The two arms I could not inform remain uninformed**: stage 4 (news — no event calendar
  exists) and stage 5 (ATR/median volatility band — no `atr_median` in the artefact). Neither is
  an account governor, but both would delete further trades, so **every deletion count here is a
  lower bound.**

---

## Side errand — R3 Tier 0 item 2, `bootstrap_paths(mode="block")` vs `"iid"`

- **Code:** `backtest/BT3/code/block_vs_iid.py`. Output `code/block_vs_iid.json`.
- **Is it one function call?** Yes, one per arm, so it is done. R3 was right about the cost.
- **Does it answer the question it was assigned?** **No, and this is the substantive point.**
  The question was "is the R series serially dependent", because Channel 4b's streak sizing
  needs `Cov(w,R) ≠ 0`. The two modes are two *resamplers*: `iid` destroys serial structure,
  `block` preserves runs of length 10. Comparing their outputs detects dependence only
  indirectly and only at the block scale. Filed as REQ-1 and **granted as board task `MGR-T11`**,
  with the manager backing me against R3's wording and R3 accepting the correction: item 2 is a
  *precondition check*, not the verdict on Channel 4b's streak sub-case
  `[msgs/09_manager_BT3_requests-ruling.md; msgs/10_R3_BT3_re-verify-ALGO-1-questions.md]`.
  A direct test is cheaper than I first said — `workspace/chrono/analyse.py:92-103` already has
  `corr` and `fisher_z`, applied to a group's *monthly expectancy* rather than a *per-trade R
  sequence*.
- **Reportability: GATED, and I asked for the gate.** The manager has gated `MGR-T8` behind the
  D44 fix (`MGR-T16`, the parent's), because the instrument the measurement uses is defective —
  see below. **The numbers in this section are therefore provisional and carry the bias**, which
  is why they are stated with it rather than corrected silently.

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
ever used `mode="block"`, so the defect has never touched a published number — this is its first
use. Filed as REQ-2 and **allocated `D44`** `[msgs/09_manager_BT3_requests-ruling.md]`; the fix is
one line, a circular block:
`path.extend(r_values[(start + k) % n] for k in range(block))`. Assigned to the parent as
`MGR-T16`, and `MGR-T8` is gated behind it.

A process note the manager turned into board rule `R-9`, worth carrying: my REQUESTS entry said
"add it as D44 (next free)", and the manager was drafting a different D44 at the same moment. It
moved its own rather than edit my write-once file. **Describe the defect; do not name the number** —
"next free" is a read of a file another agent may be about to change.

**Fidelity:** this is not an ALGO and has no fidelity verdict. It is one measurement with its
caveats attached, the caveats are larger than the measurement, and it is gated. R3 has since
narrowed its own item-2 wording and dropped it from its ranked candidates
`[msgs/10_R3_BT3_re-verify-ALGO-1-questions.md]`, noting that my pooled-versus-per-strategy
inversion here and the same inversion in ALGO-1's population unit are **two independent
instruments both saying the pooled unit fabricates structure**.

---

# PARKED 2026-09-27

BT3 is parked mid-stream by the account owner, not stopped at a natural boundary. Written for
someone arriving cold: what is true, what is not yet true, and the one thing to do next.

## The one result that holds, stated so it cannot be misquoted

**At a $50,000 account size, every governor that shrinks position size is net protective, because
survival is a threshold on the *path* rather than on the mean. That makes two apparent variance
transforms — "size down in high volatility" and "size down for an unproven strategy" — into
Channel-2 survival effects.** |z| = 6.164 and 5.543 against `free_t = 2.229`.

**It is not a trading edge.** It does not make any strategy profitable, it does not contradict the
programme's settled negative verdict, and it says nothing about expectancy. It is a
risk-management result about *account survival* at a given size. Under every reading the real
trade stream dies more often and takes fewer trades than its own permutations. If this ever gets
restated as "we found something that works", that restatement is wrong.

The mechanism, which is the transportable part: `max_drawdown / absorbing_boundary` is the whole
predictor of survival, and it falls monotonically as the governors tighten — 1.100 (volatility
pinned, dies 41%), 0.954 (neutral, 13%), 0.873 (honest, 0%). Halving the per-trade budget takes
the cliff to 83% of its depth but the realised drawdown to 76% of its size.

## State of the three result tiers

**Tier A — the absorbing state. SOLID, and no fidelity verdict can move it.** Derived from
`config.py` and `risk/manager.py` alone, no trade data. Past a **$2,800** drawdown from peak the
per-trade budget is $21.60 against `min_dollar_risk = $25`, so stage 7 refuses everything
*before* `contracts_for` is reached; equity then moves only through open positions, freezes when
they close, `peak_equity` never falls, and the budget never recovers. **`has_failed` stays False
throughout, leaving $2,200 of the $5,000 failure allowance permanently unspendable.** On the
honest arm (`is_live_eligible=False`, ×0.5) the boundary is **$2,334** — 46.7% of the allowance —
and $2,666 is unspendable. The step is a discontinuity, not a fade: $36.03 at a $2,799 drawdown,
$21.60 at $2,800, because the de-risk ladder steps ×0.50 → ×0.30 there. **Consequence worth
carrying: `max_total_drawdown` is unreachable from above the boundary, so risk-of-ruin as this
repo models it is measuring an event that cannot occur.**

**Tier B — the integer floor. SOLID, mechanical, hand-checkable.** `9,042 of 21,954` deleted at
the opening $240 budget = **41.19%** (35.38% with the volatility multiplier pinned; the ×0.70
alone accounts for 1,275). By cell: **MGC 4h 99.42%, MNQ 4h 94.59%**, median **zero** contracts in
both. R3's volatility-filter reading holds conditioned on symbol and timeframe, monotone in 5 of 6
unsaturated cells; MGC 60m runs 68.6 → 69.7 → 48.2 → 2.5 → 1.3 across DEAD→EXTREME. **Always quote
the elasticity with the percentage:** ≈ **2.0** near $240, so the figure is 14.7%/7.5% at $375/$500.
The qualitative claim is robust; any specific percentage is a statement about one account size.

**Tier C — the stateful replay. UNREPORTABLE. Fidelity is ASKED, cycle 2, unanswered.**
Asked in `msgs/15_BT3_R3_verify-ALGO-1-v2.md`; R3 has not ruled. Four questions open, of which the
first matters most: **R3's Q5 prediction reversed under its own required fixes** — it predicted the
honest arm dies and the neutral survives by $53; measured over 200 orderings the honest arm dies
**0 of 200** and the neutral **26 of 200**. Do not quote Tier C until that is ruled.

What Tier C says, pending the ruling: at the per-strategy unit **5,537 of 21,954 trades survive
(25.22%)**, and the integer floor does **16,184 of 16,417 refusals — 98.58%**, while the four daily
governors this whole task was named after (daily loss limit, giveback, trade cap,
consecutive-loss stand-down) do **207 of 16,417 = 1.26%**, and **two of the four never fire at
all**. `max_trades_per_day = 6` **never binds on a single strategy** at 60m or 240m — no strategy's
busiest day exceeds 6, modal 2–3 — and only bites when you pool. **18 of 22 MGC 4h strategies and
11 of 22 MNQ 4h strategies take not one trade on a $50,000 account.** Not underperform: do not
exist.

## What is unreportable, and why

1. **All of Tier C** — fidelity ASKED, cycle 2. Not a weak result; an unknown quantity.
2. **The block-vs-iid side errand** — `MGR-T8` is **GATED** behind the D44 fix (`MGR-T16`, the
   parent's one-line circular-block repair). The instrument is defective: `mode="block"` draws
   `r_values[start:start+block]` with no wrap-around, so index 0 appears at **0.122×** its due
   frequency against a 1.123× tail. Numbers are on disk in `code/block_vs_iid.json` and carry the
   bias; they are provisional by design, not by accident.
3. **Entry-dependence of the governors' deletions — WITHDRAWN, not resolved.** Cycle 2 of this file
   claimed the deletions were entry-independent on the strength of a placebo comparison, using an
   invalid operation (p-value compared to a t-threshold). Corrected: the global placebo clears on
   `taken` at |z| = 2.480 > 2.229. But **no arm in this design replaces the signal layer** — all
   three placebos permute the *outcome* layer, and the stratification decides the answer (|z| spans
   0.000 to 4.161). Entry-dependence is **untested here, not refuted.** It needs random entry bars
   through the same exits and governors, i.e. a new backtest.

## Shelf life of the reproduction, which is load-bearing for everything above

`code/stops.py` recovers the per-trade stop distance the artefact does not carry, by re-running the
22 dumped strategies per cell. **The match is exact: 21,954 of 21,954, zero missing, worst
|Δr| = 0.000e+00.** R3's reading, which I accept: this establishes that the generating study is
**deterministic**, which nothing in this repo had established.

**It expires.** The recovery holds only while `workspace/newstrats/run_geometry.py`,
`toolkit.disjoint_slices` and the frozen `csv/raw` snapshot **all three still agree**. If any is
reshaped the link is gone and `code/stops_cache.json` becomes unverifiable — at which point
`code/checks.py::check_cache_matches_artefact` and
`tests/test_bt3_governor_replay.py::test_cache_is_the_artefact_plus_exactly_three_fields` will
fail, which is the intended alarm. That is the argument for the manager's board rule **`R-8`**
(dumps record `entry_price`, `initial_stop`, `symbol`): three keys now beats a reconstruction later
that may not be possible.

## Two figures worth keeping rather than superseding

The edge programme's session rule cannot be carried on 240m cells at all — the window is 22h =
1320 min and 1320/240 = 5.5 — so **MGC 4h at 99.42% deleted and MNQ 4h at 94.59% are, for now, the
only 240m numbers anyone has.** They are Tier B (mechanical, hand-checkable) and do not depend on
the fidelity verdict. Keep them.

## The warning for whoever resumes this

**I planted a defect in my own look-ahead fix and only caught it by writing a test for something I
had already "fixed".** Restructuring the replay loop to iterate timestamp *groups* made `flush()`
run once per group, so **`barrier=False` silently became a barrier too** — and my first cycle-2
result, "removing the look-ahead changes nothing (p = 0.362)", was a comparison of the barrier
**with itself**. The corrected answer is that the leak inflated the trade count by ~17 trades per
seed (|z| = 4.721) and did not affect survival.

This is the same failure family as D38, D42, D44, D48, D51 and D57: **a defect whose signature is a
null.** Every one of them presents as "this axis does nothing". The practical rule I would pass on:
when a fix produces a null, the null is a hypothesis about the fix before it is a result about the
world — write the synthetic test that would fail if the fix were inert. Two such tests now guard
this one (`test_barrier_hides_same_instant_outcomes_from_same_instant_decisions`,
`test_barrier_hides_same_instant_losses_from_the_daily_ledger`).

Also inherited, from R3, and it will bite any Tier-1 exit work before it bites anything else:
**R3-A-13** — `dataclasses.replace` inherits the cached `_id`, so `replace(s, exit=...)` without
`_id=None` yields a strategy claiming `s`'s id, and `run_many` keys everything by that id, so both
arms of a pair collapse into one row and the measured difference is **exactly zero**. ALGO-1 is not
exposed (no `replace` anywhere in `code/`, and `stops.py` asserts zero duplicate keys), but the
next algorithm will be.

## The single next step

**Get R3's cycle-2 ruling on `msgs/15_BT3_R3_verify-ALGO-1-v2.md`, then re-read Tier C against it.**
Nothing else should start first: Tier C is the only unresolved part of ALGO-1, and a second
algorithm built on an unruled first one is the mistake PIPELINE §4 exists to prevent.

After that, in order, and all currently blocked:
1. **ALGO-2**, pre-registered by R3: the `CONTROL`/`CONTROL_FADE` arms only — 2 bases × 2 exits × 4
   symbols × 2 timeframes = **32 strategies in one account**, representative chosen *by
   construction* so there is no selection on outcome. Must be a separate ALGO, never folded into
   ALGO-1.
2. **A real signal-layer placebo** for the entry-dependence question above. This is the one thing
   that needs a new backtest rather than a replay, and it is what would let the withdrawn sentence
   be settled either way.
3. **R3's Tier-1 six** — blocked twice over: the manager's `R-6` (unpaired sweeps are not
   reportable, D15: only 93 of 8,317 shipped rule sets exist with two exits) and, for the trailing
   stop specifically, the A-2 fix at `engine.py:419-421`, because `STOP` is otherwise a mixture of
   an initial-stop hit near −1R and a trail hit that locked in a gain — opposite signs, so the
   per-reason mean R moves with the mixing weight even when nothing real changed.
4. **Block-vs-iid**, once `MGR-T16` lands.

## Files

`ALGOS.md` (this file), `VERIFY.md`, `REQUESTS.md` (4 requests, all ruled),
`bursts/01_governor_replay.md`, `bursts/02_governor_replay_cycle2.md`,
`bursts/03_placebo_threshold.md`. Code: `code/stops.py`, `code/governor_replay.py`,
`code/paired_tests.py`, `code/block_vs_iid.py`, `code/checks.py`. Artefacts:
`code/stops_cache.json`, `code/algo1_report.json`, `code/paired_tests.json`,
`code/block_vs_iid.json`. Tests: `tests/test_bt3_governor_replay.py` (10). Messages out:
`msgs/04_BT3_R3_verify-ALGO-1.md`, `msgs/15_BT3_R3_verify-ALGO-1-v2.md`,
`msgs/16_BT3_R3_placebo-correction.md`.

`geo_trades.json` and everything under `csv/` were read and never written.
