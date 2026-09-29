# EF2 — FINDINGS

**Cell: SWING on MGC and MCL, at 60m and 240m.** Deliverable: a top 10 per symbol for the swing
setting. Status: **Burst 1 complete (needs neither EF1 nor EF6). No profitability number is reported
and none has been computed on a validated harness.**

Substrate label for every number below: **`data/archive/{MGC,MCL}_60m.jsonl`**, 11,297 / 10,934 bars,
**718 calendar days** (2024-10-06 -> 2026-09-25 ET), 240m resampled up from it and bit-identical to the
natively fetched `_240m.jsonl`. `sqrt(718/365.25) = 1.402`.

Bursts, each written when it was done:
`bursts/01_substrate-and-session-arithmetic.md`, `bursts/02_firing-rate-census.md`,
`bursts/03_population.md`, `bursts/04_fire-attrition-and-stop-fidelity.md`.

---

## F1 — The 22-hour swing window is not 22 hours, and with the generated default it is not overnight at all

**F1a.** The cycle is 18:00 ET -> 16:00 ET. A position opened at *T* must be flat at that cycle's
16:00, so the hold available is `16:00 - T`. **22 hours is reachable only from an 18:00 ET entry.**
From MGC's RTH open (08:20) the budget is **7h40m**; from MCL's (09:00), **7h00m**; from 15:00, one
hour. "Swing" here is a hold budget that shrinks linearly through the cycle, not a duration.

**F1b — the measured one.** `StrategyFilters.rth_only` defaults `True`
`[repo-verified: base.py:393]` and is `True` on **184/184 MGC and 167/167 MCL** generated strategies
at `[60,240]` `[measured]`. MGC RTH is 08:20-13:30 and MCL 09:00-14:30, both **wholly inside one
cycle**. The census confirms it arithmetically: the count of bars that are RTH **and**
swing-admissible equals the count of RTH bars **exactly** — 2,477/2,477 MGC, 2,881/2,881 MCL.

> **With the generated default, the 18:00->16:00 rule adds ZERO entry opportunity on MGC and MCL. It
> only lengthens the permitted hold, from the contract's own RTH close (13:30 / 14:30, which is what
> `exit_at_session_close` enforces, `engine.py:470-473`) out to 16:00 — +2h30m on MGC and +1h30m on
> MCL. Not +22 hours.**

The overnight regime the EDGE_BRIEF calls "genuinely unmeasured" is reachable only with
`rth_only=False`, a departure from the generated default that runs into **D24**. EF2 therefore carries
`rth_only` as an explicit **paired arm** (`EF2-HYP-1`). Posted to EF1 as
`msgs/EF2-01_EF1_rth-only-makes-the-overnight-switch-inert.md`.

**F1c — CORRECTED in Burst 05, after cross-checking against EF6's `window.signal_mask`.** My first
number (8.7% / 35.5% "inadmissible") was the **union** of two different sets, mislabelled as one of
them. EF6's vocabulary separates them and its convention is the engine-faithful one — it asks what the
**next bar in the series actually is** rather than assuming a contiguous grid, and the 17:00 bar mostly
does not exist, so a signal on the 16:00 bar fills legally at the 18:00 open.

| symbol | tf | bars | **position-illegal** | **signal-inadmissible** | `STRADDLE` | union |
|---|---|---|---|---|---|---|
| MGC | 60m | 11,297 | 495 = 4.4% | 496 = 4.4% | **0** | ~8.8% |
| MCL | 60m | 10,934 | 474 = 4.3% | 475 = 4.3% | **0** | ~8.7% |
| MGC | 240m | 3,052 | **586 = 19.2%** | 586 = 19.2% | **586** | ~35% |
| MCL | 240m | 2,990 | **563 = 18.8%** | 563 = 18.8% | **563** | ~35% |

The clean form, which is stronger than what I first wrote:

> **At 240m, 19.2% of MGC bars and 18.8% of MCL bars are `STRADDLE` — they contain 16:00 or 18:00
> strictly inside them. At 60m there are ZERO `STRADDLE` bars on either symbol.**

A `STRADDLE` bar is a defect report, not a third trading state: the rule cannot be applied to it
without breaking it or discarding a legal part of the bar. EF1 goes further and **refuses** such a grid
(`SessionGridError`). **So a 240m *base* series is not a valid substrate for this programme's rule on a
fifth of its bars, while a 240m *thesis* on a 60m base is entirely valid** — an independent and much
better justification for the substrate choice I made for span reasons, and the exact thing the three of
us would have disagreed about silently had I loaded `MGC_240m.jsonl` as a base. **The correction does
not touch any VOID verdict, the population, or F1b**: the census scores against `RTH ∩ swing`, the
16:00 bar is not RTH on either contract, so that intersection is unchanged at 2,477 / 2,881.

**F1d.** 22h / 4h = **5.5 bars of runway at 240m**, 22 at 60m. Every geometry in
`expand_exit_models()` carries `time_stop_bars` 30-120 `[repo-verified: combinator.py:52-110]` —
120-480 hours at 240m, 30-120 hours at 60m. **`time_stop_bars` is unreachable in this cell and must
not be reported as a tested axis.** Every position closes on the clock rule, the stop or the target.

---

## F2 — Firing-rate census: 3 to 12 of 79 conditions VOID, per cell, never global

Denominator for usable fires is the RTH-and-swing-admissible set: **2,477 (MGC) / 2,881 (MCL)**.

| cell | VOID_RAW | VOID_IN_STRATEGY | total / 79 |
|---|---|---|---|
| `MGC:f60__p60` | 6 | 1 | 7 |
| `MGC:f60_240__p60` | 4 | 1 | **5** |
| `MGC:f240__p240` | 12 | 0 | **12** |
| `MGC:f60_240__p240` | 12 | 0 | 12 |
| `MCL:f60__p60` | 4 | 1 | 5 |
| `MCL:f60_240__p60` | 2 | 1 | **3** |
| `MCL:f240__p240` | 10 | 0 | **10** |
| `MCL:f60_240__p240` | 10 | 0 | 10 |

`VOID_IN_STRATEGY` is a verdict EF2 needed and the vocabulary lacked: **fires somewhere, never on a
bar a strategy could act on.** `session_extreme_sweep` is the instance — fires only outside RTH at
60m, and `rth_only=True` vetoes all of it; **LIVE at 240m**, because a 240m bar's high spans pre-RTH
hours while the accumulator holds RTH bars only. So its deadness is a 60m artefact, not a property of
the condition. Zero swallowed exceptions in all six passes `[measured: condition_errors == {}]`.

### Against the brief's list of known VOID configurations

| # | claim | verdict |
|---|---|---|
| 1 | all six `profile` conditions VOID at 240m | **CONFIRMED, both symbols** |
| 2 | both MULTI_TIMEFRAME signals VOID at the frame's top timeframe | **CONFIRMED**; live in exactly 1 of 4 cells |
| 3 | `openinterest` VOID anywhere | **CONFIRMED**, all 8 cells |
| 4 | OPENING_RANGE VOID at 1h on 3 of 4 symbols | **CONFIRMED** — MGC VOID, MCL live |
| 5 | `StopKind.RANGE` collapses to ATR on MGC 60m (D49) | **UNREACHABLE — zero carriers in my population** |
| 6 | `StopKind.VWAP_BAND` -> FIXED_TICKS on 6-34% of bars (D45) | **reachable; measured, F6** |

**On #1, the part that matters more than the group name:** all 6 are VOID at 240m — the 4 SIGNALs
*and* the 2 FILTERs `away_from_hvn` / `open_outside_value`. `profile` is an **optional** group for
seven other templates and those two FILTERs are `optional_filters` of VOLUME_PROFILE and
MEAN_REVERSION, so a 240m strategy in **any of eight groups** can be killed by a `profile` condition
it drew as an optional extra. It does not have to be a VOLUME_PROFILE strategy.

**On #5.** `RANGE` and `FIXED_TICKS` appear only under
`expand_exit_models(include_aggressive=True)` `[repo-verified: combinator.py:100-106]`,
`DEFAULT_EXITS` leaves it `False` `[repo-verified: combinator.py:112]`, and no template's `exits`
tuple sets it. Measured stop kinds in the generated populations: MGC `{ATR: 143, STRUCTURE: 26,
VWAP_BAND: 15}`, MCL `{ATR: 132, STRUCTURE: 31, VWAP_BAND: 4}` — **no RANGE, no FIXED_TICKS**. D49 is
real and cannot touch an EF2 row. The reachable stop vocabulary here is **three** mechanisms, one of
which (VWAP_BAND) is itself a mixture.

### One extension, bearing on an open defect

**The opening range is a BASE-clock object, so on MCL it survives at 240m.** `snap.opening_range` is
built in `_build_session_state`, which iterates **`self.base.bars`** `[repo-verified:
features.py:867]` — the 60m series — not the primary timeframe's. Availability is decided by the
**base** timeframe against the contract's `rth_open` and inherited unchanged by a 240m-primary
strategy. Measured: `opening_range_breakout`/`opening_range_fade` **VOID on MGC at 60m AND 240m**,
**LIVE on MCL at 60m AND 240m**. So "the opening range does not exist at 240m" is frame-dependent,
not timeframe-dependent, and **`D30` as worded does not hold on MCL on a 60m base.** Flagged, not
adjudicated.

---

## F3 — The population: 5,092 MGC arms and 5,584 MCL arms

| | MGC | MCL |
|---|---|---|
| rule sets drawn (seed 20260927, `max_total=2000`, **13 groups explicitly**) | 972 | 973 |
| candidate arms = rule sets x 4 cells x 2 `rth_only` arms | 7,776 | 7,784 |
| **removed by the VOID gate** | **2,684 = 34.5%** | **2,200 = 28.3%** |
| **published population** | **5,092** | **5,584** |
| `free_t = sqrt(2*ln n)` | **4.132** | **4.154** |
| **annualised Sharpe needed on 1.402 sqrt-years** | **2.95** | **2.96** |
| `free_t` on the pre-gate denominator | 4.233 | 4.233 |

Both denominators published, so `free_t` can be recomputed either way; it moves 0.10 t-units. The
34.5% / 28.3% is far above the programme-wide 19.0%, and it should be: that figure averaged over 5m,
15m, 60m and 240m, and `profile`/`opening_range` conditions are live at the finer timeframes that
diluted it. Per-cell removal runs **8.5% to 48.7% inside one symbol** — 5.7x.

| cell | MGC kept / removed | rate | MCL kept / removed | rate |
|---|---|---|---|---|
| `f60__p60` | 1,440 / 504 | 25.9% | 1,564 / 382 | 19.6% |
| `f60_240__p60` | 1,656 / 288 | **14.8%** | 1,780 / 166 | **8.5%** |
| `f240__p240` | 998 / 946 | **48.7%** | 1,120 / 826 | **42.4%** |
| `f60_240__p240` | 998 / 946 | **48.7%** | 1,120 / 826 | **42.4%** |

`opening_range_*` accounts for **608 removed MGC arms and 0 MCL arms** — the largest symbol-specific
difference in the gate, and it is 08:20 vs 09:00 against a hard-coded `or_minutes = 30`, nothing to do
with gold versus oil.

**Groups that cannot be tested at all, identical on both symbols:** MULTI_TIMEFRAME has zero surviving
arms in `f60__p60`, `f240__p240` and `f60_240__p240`; VOLUME_PROFILE has zero in both 240m cells. So
**MULTI_TIMEFRAME is answerable in exactly one of four cells** and **VOLUME_PROFILE is inexpressible
at 240m**. `scan_reports/2026-09-24` Part B lists MULTI_TIMEFRAME among the four things that "measured
best" on MGC; in three of four EF2 cells it cannot fire, so that claim is about a frame.

**D48 discipline, asserted not trusted.** `_id=None` on every `replace`; `population.py` **raises**
unless `max_arms_sharing_an_id_within_cell_and_arm == 1`. It passes on both symbols. Arms are keyed
`cell|rth|strategy_id`, because `f240__p240` and `f60_240__p240` hold **content-identical**
strategies (`confirm_tfs=()` in both) that legitimately share an id — which is what makes `EF2-HYP-3` a
clean single-variable test of `_default_regime_tf`.

**Construction decisions that fix a confound, stated because each is a place a silent one would live.**
(i) 13 groups passed explicitly — `groups_for` returns **6 for MGC and all 13 for MCL**, so the
default would have narrowed MGC to 6/13 while MCL got the lot. (ii) Rule sets drawn **once per symbol**
and instantiated in all four cells, because `generate_combinations` re-samples when the timeframe list
changes and a naive cell comparison would compare two unrelated samples — D14's shape, which left MES
and MGC 60m sharing 0 of 204 rule sets. (iii) Rule sets **not** shared across symbols (independence
rule). (iv) `rth_only` a paired arm, not an inherited default.

---

## F4 — Fire attrition: the VOID gate is necessary and nowhere near sufficient

Raw fire counts are **harness-independent** — `Strategy.evaluate` reads only `snap`
`[repo-verified: base.py:658-660]` — so this was measurable before EF1 validated.
`BacktestResult.signals_generated` is **not** this number (the engine skips evaluation while
positioned, `engine.py:306-307`).

| cell | arms the VOID gate kept | arms with >=1 raw fire | **arms that still never fire** | median fires (live) | p90 |
|---|---|---|---|---|---|
| `MGC:f60__p60` | 1,440 | 481 | **959 = 66.6%** | 13 | 347 |
| `MGC:f60_240__p60` | 1,656 | 635 | **1,021 = 61.7%** | 12 | 287 |
| `MGC:f240__p240` | 998 | 333 | **665 = 66.6%** | 26 | 361 |
| `MGC:f60_240__p240` | 998 | 324 | **674 = 67.5%** | 23 | 339 |
| `MCL:f60__p60` | 1,564 | 507 | **1,057 = 67.6%** | **5** | 111 |
| `MCL:f60_240__p60` | 1,780 | 602 | **1,178 = 66.2%** | **4** | 95 |
| `MCL:f240__p240` | 1,120 | 321 | **799 = 71.3%** | 22 | 315 |
| `MCL:f60_240__p240` | 1,120 | 327 | **793 = 70.8%** | 20 | 381 |

**The VOID gate removes about a third of the candidates and roughly two thirds of what it passes still
never fires.** Two different findings; only the first is what the 19.0% figure describes. A VOID
condition is a *structural* zero; these are *conjunctive* zeros — every condition fires somewhere, but
the strict AND of 2–4 signals (which must also agree on direction) plus 2–4 filters plus `rth_only` is
empty over 718 days.

### The effective search size

| floor on raw fires | MGC arms | free_t | Sharpe | MCL arms | free_t | Sharpe |
|---|---|---|---|---|---|---|
| — (published population) | 5,092 | 4.132 | **2.95** | 5,584 | 4.154 | **2.96** |
| >= 1 | **1,773** | 3.868 | 2.76 | **1,757** | 3.866 | 2.76 |
| >= 20 | 814 | 3.661 | 2.61 | 590 | 3.572 | 2.55 |
| >= 30 | **712** | 3.624 | **2.59** | **502** | 3.527 | **2.52** |
| >= 100 | 408 | 3.467 | 2.47 | 264 | 3.339 | 2.38 |

Both denominators travel on every row. Discounting the non-firers moves the threshold 0.26 t-units —
0.19 of annualised Sharpe. The gates are about not reporting a null that was never a measurement,
**not** about lowering the bar. And a fire floor is an **upper bound** on a trade floor, because the
engine refuses a signal while positioned and the swing rule makes holds longer: the qualifying pool
will be **smaller** than 712 / 502, so the top 10 will be drawn from a few hundred arms at most.
Stated before the measurement so it cannot look like an excuse afterwards.

### Three caveats, one of which invalidates an obvious comparison

**(i) Raw fire counts are NOT comparable between a p60 and a p240 cell.** A 240m-primary strategy is
evaluated at every **60m** base bar against the last *completed* 240m bar
`[repo-verified: features.py:828-847]`, so one 240m reading persists across up to four consecutive
decision bars and is counted four times. That is why the 240m median (20–26) exceeds the 60m median
(4–13) despite a quarter of the bars. Realised trades do not inherit the factor of four
(`signals_skipped_in_position` absorbs it); **fire counts do**. So "240m fires more often" is an
artefact of the decision clock. `EF2-HYP-4` is registered on expectancy in R, not counts, and is
unaffected.

**(ii) MCL at 60m is the thinnest cell in the study: a median of 4–5 fires per live arm over 718
days**, i.e. ~2.5 a year, against MGC's 12–13. MCL is also the cost-fragile contract and the one with
366 missing bars (F9). All three point the same way.

**(iii) Gate signatures equalled arm counts in all eight cells**, so **no two surviving rule sets
differ only by their exit geometry**. The exit dimension is spread *across* rule sets rather than
nested *inside* them, so "which geometry suits this rule set" is **not answerable from the screen** and
would need a deliberate paired re-emission on R3's recipe.

## F5 — Anti-overfitting: checked, with findings

| risk | how checked | finding |
|---|---|---|
| **look-ahead on entry** | `evaluate` reads only `snap`; alignment pointer is the **last completed** bar per tf `[features.py:838-845]`; entries fill at the **next** bar's open `[engine.py:295-300]` | clean by construction; per-fold prefix check pending EF1 |
| **repainting indicators** | `find_swings` needs `right=3` bars of FUTURE confirmation `[indicators/structure.py:60-67]` — a genuine hazard. `_build_swing_pointers` gates on `confirmed_index <= i` `[features.py:362]`, so a swing at bar 100 is invisible until 103 | **CLEAN — the guard exists and is correct.** `StopKind.STRUCTURE` reads `last_swing_low/high` and is not repainted |
| **future-data leakage, FVGs** | `fair_value_gaps(..., as_of=n-1, track_fills=True)` stores each gap's eventual fill bar; `active_fvgs` **masks** `filled_index` when it postdates the asking bar `[features.py:496-505]` | **CLEAN — explicitly guarded** |
| **future-data leakage, S/D zones** | `active_zones` passes every zone through `as_of` `[features.py:515-540]` | **CLEAN** |
| **future-data leakage, resampling** | 240m resampled `keep_partial=False` `[features.py:811]`; bit-identical to the vendor's own 240m (3,052/3,052 and 2,990/2,990, `max|dc| = 0.0`) | **CLEAN** |
| **D48 arm-id collision** | `_id=None` everywhere + assert per (cell, arm) stratum, and again inside `run_cell` before `run_many` | **passes** |
| **R5's `BarSeries.append` collapse** | EF2 constructs no non-wall-clock series; resampled length asserted equal to native | **N/A by construction** |
| **D38 silent zeroing** | `toolkit.measure_custom` unused in EF2 | **N/A by construction** |
| **D28 `T.ab` inflation** | not used; every paired claim names its test in `plan.json` | **N/A by construction** |
| **data-mining bias** | `free_t` on the exact population; both denominators published | **4.132 / 4.154; Sharpe 2.95 / 2.96** |
| **insufficient sample size** | 30-trade floor + per-row t + span arithmetic | fixed in advance |
| **survivorship bias** | not applicable classically (one symbol per backtest, no cross-sectional universe). The analogue is the VOID gate shrinking the denominator | both denominators published |
| **understated costs** | 0.35 commission + 0.37 exchange per side, 1.0-tick typical slippage, both symbols `[config.py]`; gross **and** net on every row | `EF2-HYP-5` tests MCL's cost fragility |
| **unrealistic fills** | entry is the fill bar's **open** plus adverse slippage, never a bar extreme `[engine.py:341-347]`; thin-market slippage when the fill bar is outside RTH `[engine.py:339]` | matters much more in the `rth_only=False` arm; reported separately for it |
| **parameter sensitivity** | 12 distinct geometries, deliberately not a fine grid `[combinator.py:44-50]`; reported as the spread across geometries sharing one rule set | rule sets that work at one geometry only are flagged |

`csv/raw` holds **no 4h file for any symbol**, so the 240m half of my cell cannot be cross-verified
against the frozen store at all. What I verified instead: resampling archive 60m -> 240m is
bit-identical to the natively fetched `_240m.jsonl` on both symbols. 60m equivalence re-measured
independently and replicates the BRIEF's corrected table: MGC `max|dclose| = 3.4375e-07`, MCL
`4.8242e-08`, 2 volume mismatches each, compared in UTC on both sides.

---

## F6 — Stop-kind fidelity: D45 replicates, exceeds its published range, and is NOT confined to `VWAP_BAND`

`ExitModel.stop_price` ends **every** branch with `dist = max(dist, min_dist)` where
`min_dist = spec.min_stop_ticks * spec.tick_size` `[repo-verified: base.py:313-315]`. When the clamp
binds the stop is a **fixed number of ticks** whatever the enum says, and two arms differing only in
`stop_mult` become the same trade. Measured `min_dist`: MGC `25 x 0.1 = 2.5` points ($25); MCL
`15 x 0.01 = 0.15` ($15). Every distinct `ExitModel` any template can draw (9 of them), both
directions, every swing-admissible bar.

| cell | `VWAP_BAND` m1.0 | `STRUCTURE` m1.0 | `ATR` m0.75 | `ATR` m1.0–2.5 |
|---|---|---|---|---|
| MGC 60m | **19.2%** | 3.8% | 0.0% | 0.0% |
| MGC 240m | **12.4%** | 1.7% | 0.0% | 0.0% |
| MCL 60m | **37.2%** | **7.5%** | 1.0% | 0.0% |
| MCL 240m | **24.6%** | 3.7% | 0.0% | 0.0% |

**(a) D45's published range is 6–34%; MCL at 60m measures 37.2%** — outside the top of it, on a
718-day substrate rather than the 5,000-bar `csv/raw` window. Extends the finding.

**(b) `STRUCTURE` collapses too, and I have not seen that recorded.** The clamp is on the shared tail,
so the collapse belongs to the **floor**, not to `VWAP_BAND`. `STRUCTURE` hits the floor on 7.5% of MCL
60m bars, and it carries **17.6% of MGC arms and 23.4% of MCL arms** against `VWAP_BAND`'s 2.6% / 4.3%
— so in **arm-weighted** terms the `STRUCTURE` collapse touches more of the population than the
`VWAP_BAND` one does. Anyone re-reading `x_exits`' "no stable best stop width" (the open obligation the
manager recorded) should look at both.

**(c) The floor is what actually enforces BRIEF rule 4.** "Structural stops never tighter than ~0.5
ATR" is not a rule anywhere in the code; it is a consequence of `min_stop_ticks`. And on MCL the
catalogue's tightest ATR geometry (`m0.75`) does reach the floor, on 1.0% of bars — so `ATR m0.75` and
`ATR m1.0` are the same stop there.

**Reporting rule EF2 adopts:** every top-10 row states its `stop_kind`, and a row carrying `VWAP_BAND`
or `STRUCTURE` also states the measured collapse rate for **its own** cell. A `VWAP_BAND` row on MCL
60m is partly a result about a fixed-tick stop on 37% of its candidate bars and cannot be called a
VWAP-band strategy without that number beside it. Enforced in `rank.py` (`STOP_COLLAPSE`).

**The other silent route to a low trade count, quantified.** `stop_price` returns `None` when the stop
cannot be placed and the trade is then simply not taken. Rates: `ATR` 0.1% (60m) / 0.5% (240m),
`STRUCTURE` 0.1–0.4%, `VWAP_BAND` **0.0%** everywhere. Small, consistent with warm-up rather than a
structural hole, so it is **not** a material contributor to F4's two-thirds attrition — worth having
measured, since an unmeasurable-stop veto and a never-firing gate are the same null.

## F7 — What is ready to measure the moment EF1 validates

1. `EF2/code/measure.py --engine session` — drop-in against `EF1/code/session_window.py`'s
   `SessionWindowEngine`, **one `rth_only` stratum at a time** (asserted, because one `run_many` over
   both strata would collide ids and measure a between-arm difference of exactly zero, D48). My 60m
   base passes EF1's `_audit_grid`: no 60m bar contains 16:00 strictly inside it, so **zero
   `INTERIOR` bars** and no `SessionGridError`.
2. Every metric the task asks for, from one R series: expectancy in R, win rate **and** payoff
   together, average win and loss, profit factor, per-trade Sharpe and Sortino, t of the R series, max
   and average drawdown in R, max consecutive wins and losses, average and max duration, MAE, MFE,
   gross vs net and the cost drag, trade count, per-fold expectancy and per-fold trade count.
3. Controls: `workspace/newstrats/placebo.py` reused, **`placebo_random` + `placebo_shuffle` only**
   (`placebo_shift` excluded, D42 — it leaks), 20 seeds x 2 kinds = 40 control observations per row,
   plus the cell-level "where did the best placebo land" against
   `null_rank_distribution`'s `E[R] = (N+1)/(k+1)`.
4. Forward roll: 6 contiguous blocks over 718 days, anchored, 5 test folds, none re-used, a trade
   counted in the fold containing its **entry** bar.
5. The benchmark the prior attempt failed, pre-registered as a **required** output: expectancy of the
   selected top 10 against expectancy of the **entire qualifying universe** over the same folds.
6. Six pre-registered hypotheses `EF2-HYP-1..H6` with directions fixed in writing, at Bonferroni
   `|t| >= 2.39` — Sharpe **1.70** needed, against the screen's 2.96.

**Rank key: expectancy in R, and nothing else.** Win rate, payoff and profit factor are reported
beside it and never rank. The trade floor and the t-statistic **gate** a row; they do not reorder it.

## F8 — Out of scope by arithmetic, stated rather than truncated

- **Any thesis needing more than one 18:00->16:00 cycle.** Untestable under the programme rule.
- **1440m as a primary or a confirmation timeframe.** `MCL_1440m.jsonl` holds **exactly 1 row**, so no
  daily frame exists for MCL; MGC's spans 2010-2026, a different era; and a daily bar is
  `>= _SESSION_MINUTES = 390` `[base.py:379]` so it contains the break.
- **`execution_tf` — "hone the entry on a finer timeframe".** `DEFAULT_EXECUTION_MAP` offers
  `240 -> 15` and `60 -> 5` `[combinator.py:443]`, but archive 15m span is **57 days** against 718 at
  60m, so including one truncates the swing substrate by 92%. `execution_tf` is `None` on every EF2
  arm and **this axis is not tested in the swing cell.**
- **`time_stop_bars`.** Unreachable inside a 22-hour ceiling (F1d).
- **MULTI_TIMEFRAME in 3 of 4 cells, VOLUME_PROFILE at 240m.** Structurally void (F3).


---

## F9 — Both archive hourly series are incomplete (MGC 93.3%, MCL 89.5% of cycles), and the 16:00 flat cannot fire in 17 MGC / 34 MCL cycles

Detail: `bursts/06` and the correction in `bursts/12`. Prompted by `EF3-01`, which found EF1's
`classify_bar` under-enforcing the flat on 19 of 507 MES/MNQ sessions. **I re-measured on my own symbols
rather than inheriting the count** — MGC is COMEX, MCL is NYMEX, neither shares the equity complex's
calendar.

| cell | bars | cycles | **cycles where the flat cannot fire** | share |
|---|---|---|---|---|
| MGC 60m | 11,297 | 506 | **17** | **3.36%** |
| MGC 240m | 3,052 | 602 | 9 | 1.50% |
| **MCL 60m** | 10,934 | 505 | **34** | **6.73%** |
| MCL 240m | 2,990 | 596 | 14 | 2.35% |

Zero `INTERIOR` bars in any cell, so `SessionGridError` never fires and the run proceeds while those
cycles go untested. **The audit is per series; the hole is per cycle.**
Independently confirmed by EF1's own arm-C validation: **33 `SPANS_WINDOW` violations, every one at
`primary_tf = 240m`, 18 of them MCL**, plus EF1 reaching the MCL hole by a different method. And by EF4
from the other side: at 5m/15m/30m the flat is reachable in **41 of 41** cycles on both symbols, so this
is a coarse-grid and sparse-data defect, not a property of the rule.

### The completeness measurement, and a correction to how I first framed it

Burst 06 measured MCL's missing bars **relative to MGC** — 366 bars MGC has that MCL lacks — which is
true and silently implies MGC is complete. **It is not.** Absolute completeness (distinct ET hours per
18:00→16:00 cycle, excluding the 16:00–17:00 break, so a full cycle is 22 bars):

| symbol | cycles | **complete (22/22)** | partial | bars short of 22 | cycles with ≤6 of 22 |
|---|---|---|---|---|---|
| MGC | 506 | **472 = 93.3%** | 34 | **330** | 11 |
| MCL | 505 | **452 = 89.5%** | 53 | **650** | **28** |

Most of MGC's 34 partials are **genuine** early closes and holidays and should be short. Two are not:
**`2026-02-02` is 3 of 22 hours on MGC** — a Monday, and a **51-hour hole** (every bar from
2026-01-30T11:00 to 2026-02-02T12:00 absent) — **and `2026-02-02` is 3 of 22 on MCL too, so that hole is
shared by both contracts**, which points at the vendor rather than either exchange. MCL additionally
carries two multi-day runs MGC does not: **2026-01-09 → 01-16** and **2026-02-20 → 03-11**.

All of it is in `csv/raw` as well as `data/archive` — `csv/raw/MCL_1h.csv` has the same 102 bars on
MCL's gap dates and **zero** bars the archive lacks — so `BarArchive` behaved correctly, this is the
vendor's series, and **every published result on these two contracts rests on it.** The BRIEF's data
policy verified the two stores hold the *same* series over *overlapping* stamps; it never asked whether
either is *complete*.

**Why the relative framing was the wrong measurement, which is the more useful lesson:** a cross-symbol
comparison can only find a hole in one series that the other fills. It cannot find a **shared** hole —
and a shared hole is precisely the blind spot created by only ever comparing two symbols to each other,
which is what the independence rule encourages. The absolute test costs the same and finds both.

Raised with the manager as a D-candidate (`msgs/EF2-03`); only the manager allocates `D` numbers. Every
MCL row will be reported **with and without** the two runs, named before any expectancy exists; `D40`'s
consequence without `D40`'s cause — not splicing, absence — but the bar after a multi-day hole still
carries a multi-day return that a one-bar momentum rule reads as a one-hour move.

## F9b — The gap-fill tail in R: MCL at 240m is the worst cell in my set, and EF4's 5m magnitude does not transfer

Detail: `bursts/12`. `EF4-01` measured that with `veto_signals_in_window=False` (EF1's default, the rule
as written) a signal on the 16:00–17:00 bar fills at the next bar's open — after a Friday, the Sunday
18:00 reopen — worth 7.8 R against a 1.0-ATR 5m stop. This is downstream of my own burst-05 mask
correction, which makes the 16:00 bar legal *precisely because* the fill is at 18:00. Both facts travel
together.

| cell | legal signal bars | non-contiguous next bar | share | max abs gap |
|---|---|---|---|---|
| MGC 60m | 10,801 | 503 | 4.66% | **405.70 pts** |
| MGC 240m | 2,466 | 23 | 0.93% | 405.70 pts |
| MCL 60m | 10,459 | 552 | 5.28% | 9.90 pts |
| MCL 240m | 2,427 | 41 | 1.69% | 9.90 pts |

In R, on the ATR stops the catalogue draws:

| cell | stop | median R | p90 R | **max R** | share >2R | share >5R |
|---|---|---|---|---|---|---|
| MGC 60m | ATR×0.75 | 0.07 | 1.10 | 8.60 | 5.8% | 0.6% |
| MGC 240m | ATR×0.75 | 0.78 | 2.03 | 4.65 | 13.0% | 0.0% |
| MCL 60m | ATR×0.75 | 0.15 | 1.99 | **15.45** | 9.8% | 2.4% |
| **MCL 240m** | ATR×0.75 | **1.08** | **4.34** | **12.97** | **26.8%** | **7.3%** |

**Four cells, four different answers** — which is what the independence rule predicts. MCL 240m's
*median* gap fill is 1.08 R and 7.3% exceed 5 R; MGC 60m's median is 0.07 R. **EF2 adopts EF4's option
(1):** every row states its gap-fill count and R distribution, and a row whose expectancy depends on
fewer than three gap fills is not reportable.

**The 405-point MGC figure was checked, not assumed.** It is a real multi-day crash (gold 5447 → 4676
over five days, with a genuine 395-point range hour on 279,898 contracts) **plus** the 51-hour hole. The
tape is internally consistent; the hole is the defect. An implausible number in a gap audit is usually
the audit's own timezone alignment (the BRIEF's own trap) and here it was neither that nor a bad print.

## F10 — In the swing setting the clock is the dominant exit, which constrains what the exit axis can mean

From EF1's arm-C validation run, `max_total=400` `[EF1/bursts/03]`:

```
MGC  184 strategies   554 trades   flats 420 = 75.8% of trades
MCL  167 strategies  2179 trades   flats 1283 = 58.9% of trades
```

**59–76% of all trades are closed by the 16:00 flat**, not by stop, target or time stop. So the
catalogue's twelve geometries are differentiated mostly by where their **stop** sits; the target is
usually never reached. Falsifiable prediction, registered before my own measurement: the spread of
expectancy across geometries sharing one rule set should be **narrower** in the swing setting than the
published RTH-only corpus reports, and `target_kind` (`R_MULTIPLE` 50% / `ANCHOR_ATR` 32–35% /
`ANCHOR_STRUCTURE` 15–18% of my population) should matter **less** than `stop_kind`. This is a **Tier B**
observation — it came from EF1's number rather than my own design, so it faces the screen's threshold,
not Tier A's. It also makes F1d harmless: `time_stop_bars` being unreachable costs nothing, because the
flat gets there first in three quarters of MGC trades.

## F11 — Id hygiene: `EF2-H1` collided and my hypotheses were renamed

`REGISTRY.md` allocated `EF2-H1` to "EF2's own local engine, built rather than blocking". **EF2 built no
local engine** — `measure.py` imports `EF1-H2` (`SessionWindowEngine`) directly. My six pre-registered
hypotheses were already `EF2-H1..H6`, so that was a live collision of exactly the kind the registry
exists to prevent. Renamed to **`EF2-HYP-1` … `EF2-HYP-6`** across every EF2 file; no stale
`EF2-H<digit>` remains `[measured: grep -rn "EF2-H[0-9]" over EF2/** → no matches]`. Raised as
`msgs/EF2-03_manager_id-collision-EF2-H1-and-no-local-engine.md`, since `REGISTRY.md` is not mine.
**RESOLVED 2026-09-27: the manager withdrew `EF2-H1`** — EF2 never built a local engine, it uses
`EF1-H2` directly, and the id is vacated. So `EF2-H<n>` names nothing and `EF2-HYP-1..6` are the
only EF2 hypothesis ids. Recorded because a vacated id that stays in a citation is the same hazard
as a colliding one.


## F12 — EF6's placebo faults, re-measured on MCL (which EF6 did not cover), plus a power result

Detail: `bursts/08`. EF6's burst 03 measured three faults in `workspace/newstrats/placebo.py` under the
window rule, on **MGC and MNQ**. MCL is mine and nothing transfers.

| cell / arm | bases with >=2 raw signals | pool legal share | **expected legal gap** | **mean dir-shuffle degeneracy** |
|---|---|---|---|---|
| `MCL:f60__p60` rth=T | **0** | — | — | — |
| `MCL:f60__p60` rth=F | 3 | 0.975 | −0.12 | 0.520 |
| `MCL:f60_240__p240` rth=T | 15 | **1.000** | **+0.00** | 0.683 |
| `MCL:f60_240__p240` rth=F | 18 | 0.957 | **−0.81** | 0.649 |
| `MGC:f60__p60` rth=T / rth=F | **0 / 0** | — | — | — |
| `MGC:f60_240__p240` rth=T | 4 | **1.000** | **+0.00** | 0.546 |
| `MGC:f60_240__p240` rth=F | 4 | 0.962 | **−3.07** | 0.541 |

**(a) Fault 1 is inert under `rth_only=True` on both my symbols and live under `rth_only=False`.** Pool
legal share is exactly 1.000 and the gap exactly 0.00 in both `rth=T` cells — EF6's MGC result
replicates on MCL. Under `rth_only=False` the count-matched placebo arrives with **0.8 (MCL) to 3.1
(MGC) fewer legal entries** than its base. That is the arm the whole programme is about, so EF6's
`schedule_random_legal` is **required**. The sign is negative on both my symbols, i.e. the control is
handicapped and the bias favours the real strategies — but EF6 measured the sign **reversing** on MNQ
15m, so "it is conservative" is a per-cell fact and I will not state it generally.

**(b) Fault 2 is worse on my cells than the headline.** A direction shuffle leaves **52–68%** of labels
unchanged (mean degeneracy 0.520 / 0.649 / 0.683 / 0.541). The formula's floor is 0.5; the mean exceeds
it because degeneracy is convex in the long share and several rule sets are strongly one-sided. A
direction-shuffle control on an EF2 cell would be more than half identical to its treatment. Dropping it
is not a preference.

**(c) A power result.** Not one of the first 30 surviving rule sets in `MGC:f60__p60` produced 2 raw
signals, in either arm; `MCL:f60__p60` rth=T likewise zero. **Method caveat:** the probe takes the first
30 rule sets in sorted order and `rule_sets_for` sorts by group name, so those 30 are all BREAKOUT,
whose base filters are `('volatility_compressed', 'volume_not_thin')` — the most restrictive set in the
catalogue. So this is weaker than F4's unbiased measurement and F4 is the number to quote. It does
reproduce EF6's own sample-size warning ("only 4 of 12–25 bases per cell had >=2 raw legal signals") on
a third and fourth symbol.

## F13 — I calibrated EF6's forward roll on 40 mean-zero ledgers. **It passes.**

Detail: `bursts/09`. Code: `EF2/code/calibrate_roll.py`. Artefact: `EF2/data/calibrate_roll.json`.

EF6's `forward.roll` prints a VERDICT line and my rows' forward column comes from it. A roll that says
"top-k beat both universe and null" on a structureless ledger would be invisible here, because this
programme's headline prior finding is that **selecting was worse than not selecting** — a roll biased
the other way would look like a discovery rather than like a bug.

40 synthetic ledgers in exactly the shape `measure.py` emits (real 718-day span, 300 strategies, 5–150
trades each, 1–6 hour holds, both directions, mixed stop/target metadata so the permutation null has
geometry blocks), R drawn **i.i.d. mean-zero**, so the true answer is "no selection edge" 40 times out
of 40:

| statistic | measured | should be |
|---|---|---|
| mean `z_vs_null` | **−0.078** | 0 |
| share `z_vs_null > +1.96` | **0.000** (0 of 40) | ~0.025 |
| share `z_vs_null < −1.96` | 0.025 (1 of 40) | ~0.025 |
| mean `selection_edge_vs_universe_r` | **−0.0020 R** | 0 |
| share `edge_vs_universe > 0` | **0.525** | 0.50 |
| mean `selection_edge_vs_randomk_r` | −0.0074 R | 0 |
| share `edge_vs_randomk > 0` | 0.475 | 0.50 |
| **share beating BOTH universe and null** | **0.000** (0 of 40) | ≲0.025 |

**Centred on zero on all four arms, permutation null not inflated, zero false verdicts in 40 draws.**
The opposite of `T.ab`'s 3.3× inflation (D28), and worth having on record because EF6's module is now
load-bearing for four agents and nobody had tested it against a known answer.

**Two honest limits.** (i) I calibrated at **n = 300 strategies**; my real cells hold 998–1,780 arms
each, and selection bias grows with the number ranked. EF6's defence is the `universe`/`random-k`
comparison arms rather than a correction term — both came out at a coin flip, which is the right shape,
but at 300. Any borderline EF2 forward result gets re-calibrated at that cell's own arm count first, and
the n is stated. (ii) My **first single** interface draw (60 strategies, `nperm=50`, `seed=1`) returned
`z = +2.11` with the verdict firing on mean-zero data. That is a ~3.5% event; the 40-draw rate is 0/40.
One alarming draw is not a finding, and recording it is cheaper than someone rediscovering it and
drawing the opposite conclusion from one observation.

**Interface verified twice** — on synthetic trades and on **real** `run_cell` output (60 MGC `f60__p60`
arms, 566 trades, `S = 60` in `forward.Ledger`). And `roll` returns two columns I would otherwise have
had to build: `selection_edge_vs_universe_r`, the exact benchmark the prior attempt failed, and
`folds_where_topk_is_the_whole_universe`, which catches the "the top 10 *is* the population" case the
2026-09-24 report had to label by hand. Posted to EF6 as `msgs/EF2-04`.

## F14 — The deliverable's own arithmetic: a top 10 drawn from 5,000 arms is answerable only if the true edge has Sharpe ~3

`EF6-01` supplies the number that frames everything I will hand over, and I verified it against my own
arithmetic before adopting it. Inverting `free_t = sqrt(2·ln n)` against `t = SR·sqrt(Y)` gives the
**maximum search width that is answerable at a given true Sharpe**, `n_max = exp(SR²·Y/2)`. On the
swing span (718.83 days, Y = 1.968):

| assumed **true** annual Sharpe | max answerable search width, SWING |
|---|---|
| 1.0 | **2** |
| 1.5 | **9** |
| 2.0 | **51** |
| 3.0 | 7,022 |

**My screen is 5,152 MGC arms and 5,584 MCL arms.** So:

> **A top 10 selected from this population can only be a defensible claim if the underlying edge has an
> annualised Sharpe near 3.** At a plausible true Sharpe of 1.5 the widest search this span can settle
> is **nine** candidates. That is a property of 1.97 years of data, not of the market.

Adopted from EF6 rather than re-derived: `EF2/code/rank.py` now imports
`EF6/code/deflation.threshold`, so one implementation serves EF2–EF5 and a cross-cell comparison is not
a convention comparison. Verified first: at n = 5,152 EF6's module returns `free_t = 4.1345` and
required annualised Sharpe **2.947** against my own 4.135 / 2.95.

**What I am doing about it, rather than around it.** The deliverable is a top 10 per symbol and I will
produce one, with `free_t = 4.13 / 4.15` and "needs Sharpe 2.95 / 2.96" on **every row** — the brief's
guardrail 2, and the only honest way to hand over a ranked list on this span. But the tier that can
actually carry a live-eligible result is Tier A:

| tier | n | threshold t | required annual Sharpe | answerable? |
|---|---|---|---|---|
| Tier B screen, MGC | 5,152 | 4.135 | **2.95** | only if true SR ≈ 3 |
| Tier B screen, MCL | 5,584 | 4.154 | **2.96** | only if true SR ≈ 3 |
| Tier B, fire-discounted | 1,773 / 1,757 | 3.868 / 3.866 | 2.76 / 2.76 | no better in substance |
| **Tier A, 6 pre-registered hypotheses (`EF2-HYP-1..6`)** | 6 | `free_t` 1.893, and I hold them to **Bonferroni 2.39** | **1.35 at free_t, 1.70 at Bonferroni** | **yes, at an ordinary Sharpe** |
| (the code's floor, one pre-registered hypothesis) | 1 | 1.177 | 0.839 | — |

I am holding Tier A to **2.39** rather than to `free_t(6) = 1.893` — stricter than the deflation
arithmetic requires — because six hypotheses fixed in one document is a search of width six and
Bonferroni is the more conservative of the two accounts of it. Both numbers are reported.

**The consequence I will state plainly on the hand-over:** if the top 10 does not clear 4.13, the
correct reading is *not* "these are the ten best strategies". It is "these ten ranked highest in a
search whose width this span cannot settle, and here is each one's placebo, its threshold and its
forward behaviour." The prior attempt's failure — trading last period's top 10 returned −0.0155R
against a −0.0104R null and **underperformed trading the whole qualifying universe** — is what that
reading protects against, and EF6's `roll` reports `selection_edge_vs_universe_r` directly so the
comparison is on every list rather than in a footnote.

## F15 — Two defects in my OWN VOID gate, found by cross-checking, fixed before measuring

Detail: `bursts/10`.

**Defect A — the gate was arm-blind.** `census.py` scored usable fires as `fires_both` = RTH **and**
swing-admissible, which is right for `rth_only=True` and wrong for `rth_only=False`. So the
`rth_only=False` arm was losing carriers of conditions that fire only outside RTH — **the arm the
programme exists to open, losing the conditions the programme makes newly measurable**, silently, with
a result indistinguishable from "those strategies don't work". Found because EF6-01 stated
`session_extreme_sweep` is ALIVE and my census said VOID; both true, of different arms.
**Fixed:** `void_sets()` is now keyed `cell -> rth arm -> bound_tf`, `rth_only=True` uses `fires_both`
and `rth_only=False` uses `fires_swing`, and the per-arm split is a reported column so an arm-blind gate
is visible rather than assumed. MGC 5,092 → **5,152** arms.

**Defect B — the census used my own superseded mask.** Burst 05 established EF6's `window.signal_mask`
as the engine-faithful test and corrected the *prose*; I did not propagate it into `census.py`, which is
how a correction becomes a second defect. It bites precisely on conditions firing near a session close:

| cell | `session_extreme_sweep` fires | in RTH | swing-admissible (my strict mask) |
|---|---|---|---|
| MGC 60m | 200 | **0** | 72 |
| MCL 60m | 107 | **0** | **0** |
| MGC 240m | 1,891 | 1,414 | 1,701 |
| MCL 240m | 1,705 | 1,600 | 1,601 |

MCL's 107 fires are all on stamps my strict mask rejected — mechanically right, since MCL's RTH closes
14:30 so `session_high` stops accumulating there `[repo-verified: features.py:880-895]` and the
15:00/16:00 bars are the first that can exceed it, which are exactly the stamps the two masks disagree
about. **Fixed:** `census.py` imports `EF6/code/window.signal_mask`; `entry_admissible` is retained
marked `DEPRECATED` only so burst 04's stop-fidelity denominator stays reproducible, and that
denominator is stated on the table. Census re-run in full.

**Neither fix changes the threshold** (4.132 → 4.135). Both change whether the thing being reported was
ever measured. That is the whole reason the firing census runs before the population is built, and it
applies to my own gate as much as to the library's conditions.

**Third-party confirmation of the 240m half.** `session_extreme_sweep` at 240m: 1,891 MGC / 1,705 MCL
fires, 1,414 / 1,600 inside RTH; EF6 measured 1,652–2,134 at 240m across four symbols. So R1's D-L4
("structurally dead inside every strategy the combinator can build") is **true at 60m under
`rth_only=True` and false at 240m** — the per-(symbol, timeframe) point the `VOID` vocabulary was
invented for, landing on its own author's example.

---

# PARKED 2026-09-27

**Written for a reader arriving cold.** EF2's cell was *SWING on MGC and MCL at 60m and 240m*; the 240m
half was withdrawn by ruling on 2026-09-27 (below), so **the cell is MGC and MCL at 60m**. No
profitability number is reported anywhere in this file and none was ever computed on a validated
harness: `EF1-H2` had 33 `SPANS_WINDOW` violations when EF2 parked, fixed but not yet re-declared.

## 1. The two things that changed under EF2, both accepted

**(a) 240m is withdrawn and cannot exist.** The window is 22 h = 1,320 min and `1320 = 2³·3·5·11`, so
5/15/30/60/120 divide it and **240 gives 5.5**. A four-hour bar cannot align with a twenty-two-hour
window: arithmetic, not an implementation limit. Every 240m number EF2 measured is kept in
`bursts/13_240m-withdrawn-with-reason.md` rather than deleted, including the tape-level confirmation of
the same fact (**19.2% of MGC and 18.8% of MCL 240m bars are `STRADDLE`** — they contain 16:00 or 18:00
strictly inside them; at 60m there are **zero**).

Two of four cells go. **`f60_240__p60` survives**: its `primary_tf` is 60, its base grid is 60m, and
240m enters only as a *confirmation* timeframe read out of the snapshot. It is also the **only** cell in
the whole assignment where `MULTI_TIMEFRAME` is expressible at all.
Two of six pre-registered hypotheses die with the cells — **`EF2-HYP-3`** (the two 240m cells differ
only by `_default_regime_tf`, the one clean single-variable test of frame composition) and
**`EF2-HYP-4`** (60m vs 240m). Recorded as losses, not quietly dropped.

**(b) The threshold comes from `EF6-H3`, computed on EF2's own search size.** `rank.py` imports
`EF6/code/deflation.threshold`. **Nobody should quote 5.46** — it is the threshold for a search this
programme never ran.

## 2. The population, exactly

Seed `20260927`, `max_total=2000`, **all 13 groups passed explicitly** (the default `groups_for` gives
MGC 6 and MCL 13, which would have narrowed MGC to 6/13 while MCL got the lot). Rule sets drawn **once
per symbol** and rebuilt in every cell, so a between-cell difference is a cell difference and not two
unrelated samples (D14's shape). `rth_only` carried as a **paired arm**, `_id=None` on every
`dataclasses.replace`, and `population.py` **raises** unless every arm id is unique inside its
(cell, arm) stratum — it passes, `max_arms_sharing_an_id = 1` on both symbols.

### The live cell — 60m only

| symbol | candidates | removed by VOID gate | **population** | `free_t` | **required annual Sharpe** | groups |
|---|---|---|---|---|---|---|
| **MGC** | 3,888 | 732 (18.8%) | **3,156 arms** | **4.014** | **2.861** | 13/13 |
| **MCL** | 3,892 | 484 (12.4%) | **3,408 arms** | **4.033** | **2.875** | 13/13 |

Span 718.83 days, sqrt-years 1.403. Per cell and arm:

| cell | MGC rth=T | MGC rth=F | MCL rth=T | MCL rth=F |
|---|---|---|---|---|
| `f60__p60` | 720 | 750 | 782 | 814 |
| `f60_240__p60` | 828 | 858 | 890 | 922 |

The `rth=F` arm keeps ~30 more arms per cell than `rth=T`. That asymmetry is the **arm-aware VOID gate**
working (§5) and it is reported as a column so an arm-blind gate would be visible.

### The full population as built, for reproducibility of the withdrawn half

MGC **5,152** arms (2,624 removed, 33.7% of 7,776 candidates); MCL **5,648** (2,136 removed, 27.4% of
7,784). 240m cells accounted for 48.7% (MGC) and 42.4% (MCL) removal against 5.2–25.9% at 60m.

### Effective search size, which is the more honest denominator

Raw fire counts are **harness-independent** (`Strategy.evaluate` reads only `snap`,
`[repo-verified: base.py:658-660]`; `BacktestResult.signals_generated` is not this number because the
engine skips evaluation while positioned, `engine.py:306-307`):

| floor on raw fires | MGC 60m arms | `free_t` | Sharpe | MCL 60m arms | `free_t` | Sharpe |
|---|---|---|---|---|---|---|
| — (published) | 3,156 | 4.014 | **2.86** | 3,408 | 4.033 | **2.88** |
| ≥ 1 | **1,116** | 3.746 | 2.67 | **1,109** | 3.745 | 2.67 |
| ≥ 30 | **404** | 3.465 | 2.47 | **217** | 3.280 | 2.34 |
| ≥ 100 | 230 | 3.298 | 2.35 | 115 | 3.081 | 2.20 |

**Both denominators are published so `free_t` can be recomputed either way.** Discounting non-firers
moves the threshold ~0.27 t-units. It does not lower the bar; it stops a null being reported that was
never a measurement.

## 3. The firing-rate census, per cell — and what it removed

Substrate: `data/archive/{MGC,MCL}_60m.jsonl`, 11,297 / 10,934 bars, **718 calendar days**. All 79
conditions at every bar at every timeframe binding the frame admits. Admissibility from
`EF6/code/window.signal_mask`. Denominator for "usable fires" is the arm's own: RTH ∩ swing-admissible
for `rth_only=True` (**2,477 MGC / 2,880 MCL** bars, 22–26% of the tape) and swing-admissible alone for
`rth_only=False` (**10,801 / 10,459**).

| cell | `VOID_RAW` | `VOID_IN_STRATEGY` | total / 79 | arms removed (T / F) |
|---|---|---|---|---|
| `MGC:f60__p60` | 6 | 1 | **7** | 252 / 222 |
| `MGC:f60_240__p60` | 4 | 1 | **5** | 144 / 114 |
| `MCL:f60__p60` | 4 | 1 | **5** | 191 / 159 |
| `MCL:f60_240__p60` | 2 | 1 | **3** | 83 / 51 |
| *(withdrawn)* `MGC:f240__p240`, `MGC:f60_240__p240` | 12 | 0 | 12 | 473 / 473 each |
| *(withdrawn)* `MCL:f240__p240`, `MCL:f60_240__p240` | 10 | 0 | 10 | 413 / 413 each |

**Names at 60m.** MGC `f60__p60`: `mtf_aligned`, `mtf_strongly_aligned`, `oi_expanding`,
`oi_price_confirmation`, `opening_range_breakout`, `opening_range_fade`, + in-strategy
`session_extreme_sweep`. MGC `f60_240__p60`: the same minus the two `mtf_*` (the group frame rescues
them). MCL `f60__p60`: `mtf_aligned`, `mtf_strongly_aligned`, `oi_expanding`, `oi_price_confirmation`,
+ `session_extreme_sweep`. MCL `f60_240__p60`: `oi_*` only, + `session_extreme_sweep` — **3 of 79, the
cleanest cell in the study**.

**`VOID_IN_STRATEGY` is a verdict EF2 needed and the vocabulary lacked:** fires somewhere, never on a
bar a strategy could act on. Zero swallowed exceptions in any census pass, so no verdict here is the
"raised on every bar, recorded as 0% trigger rate" failure `base.py:131-146` warns about.

**Against the brief's known-VOID list:** all six `profile` conditions at 240m — CONFIRMED both symbols
(and it reaches **eight** strategy groups, not just VOLUME_PROFILE, because 2 of the 6 are FILTERs that
sit in other templates' `optional_filters`). Both MTF signals VOID at the frame's top timeframe —
CONFIRMED. `openinterest` — CONFIRMED, all cells. OPENING_RANGE at 1h — CONFIRMED on MGC, **and MCL is
clean** (RTH open 09:00 is on the hourly grid, 08:20 is not). **`StopKind.RANGE` (D49) — UNREACHABLE:
zero carriers in any generated population**, because it exists only under
`expand_exit_models(include_aggressive=True)` and nothing sets it; measured stop kinds are
`{ATR, STRUCTURE, VWAP_BAND}` only. `D45` — reachable and **worse than its published range** (§6).

## 4. The single most consequential measurement EF2 made

**With the generated default, the 18:00→16:00 rule adds ZERO entry opportunity on MGC and MCL.**
`rth_only=True` on **184/184 MGC and 167/167 MCL** generated strategies; MGC RTH **08:20–13:30** and MCL
**09:00–14:30** sit wholly inside one cycle; and the census confirms it arithmetically — the count of
bars that are RTH **and** swing-admissible equals the count of RTH bars exactly (2,477/2,477 MGC).
So the rule buys **hold time, not entry time**: from the contract's own RTH close out to 16:00, which is
**+2h30m on MGC and +1h30m on MCL**, not +22 hours.

And the 22-hour figure is only reachable from an 18:00 ET entry at all. The hold available to an entry at
time *T* is `16:00 − T`: **7h40m** from MGC's RTH open, **7h00m** from MCL's, one hour from 15:00.

Consequence, and it is now a board fact: reaching the genuinely unmeasured overnight regime requires
`rth_only=False`, carried as a **paired arm** (`EF2-HYP-1`).

## 5. Two defects EF2 found in its OWN gate, both fixed before any measurement

**A — the gate was arm-blind.** It scored usable fires as RTH **and** swing-admissible, right for
`rth_only=True` and wrong for `rth_only=False`. So the `rth_only=False` arm was losing carriers of
conditions that fire only outside RTH — **the arm the session rule exists to open, losing the conditions
it newly makes measurable**, silently, with a result indistinguishable from "those strategies don't
work". Found because `EF6-01` said `session_extreme_sweep` is ALIVE and EF2's census said VOID; both
true, of different arms. Fixed: `void_sets()` keyed `cell → rth arm → bound_tf`, per-arm split reported.

**B — the census used EF2's own superseded admissibility mask** after burst 05 had already corrected the
*prose* and not the code. Fixed: `census.py` imports `EF6/code/window.signal_mask`. `entry_admissible`
retained, marked `DEPRECATED`, only so burst 04's stop-fidelity denominator stays reproducible.

Neither moved the threshold (4.012 → 4.014 on MGC). Both changed whether the thing reported was ever
measured. **That is the firing census's own argument applied to the gate that implements it**, and it is
the most transferable thing in this file.

## 6. Findings that survive the park, ranked by how much they should change someone's behaviour

1. **`rth_only=True` makes the session rule an exit-time change, not an entry-time one** (§4).
2. **Both archive hourly series are incomplete, and one hole is shared.** MGC **93.3%** of cycles carry
   all 22 bars, MCL **89.5%** (472/506 and 452/505). MCL short 650 bars, MGC 330 — most of MGC's genuine
   holidays. MCL has two multi-day runs MGC does not (**2026-01-09→01-16**, **2026-02-20→03-11**) and
   **`2026-02-02` is 3 of 22 hours on *both*** — a 51-hour hole shared by COMEX and NYMEX, so it is the
   vendor. `csv/raw` has the same 102 bars on those dates and **zero** the archive lacks, so every
   published result on these contracts rests on it. *Methodological half, worth more than the numbers:*
   EF2's first measurement was MCL **relative to** MGC, and **a relative test cannot find a shared
   hole** — a blind spot the independence rule actively encourages. The absolute test costs the same.
3. **`D45` exceeds its published range and is not confined to `VWAP_BAND`.** Register says 6–34%;
   measured **37.2% on MCL at 60m**. And because the `max(dist, min_stop_ticks·tick)` clamp is on the
   **shared tail** of `stop_price` `[repo-verified: base.py:313-315]`, `STRUCTURE` collapses too — 7.5%
   of MCL 60m bars, 3.8% of MGC — and `STRUCTURE` carries **17.6% of MGC and 23.4% of MCL arms** against
   `VWAP_BAND`'s 2.6% / 4.3%, so in arm-weighted terms it touches **more** of the population. Whoever
   takes the open `x_exits` re-read obligation should look at both kinds.
4. **The flat cannot fire in 17 of 506 MGC and 34 of 505 MCL cycles**, measured by importing `EF1-H1`
   directly and asking per cycle whether any bar exists the rule could act on — no engine, no tape.
   EF1's post-fix `1b` counters return **17** on MGC 60m and **9** on MGC 240m: exact agreement.
   16 of MGC's 17 and 16 of MCL's 34 are shared holiday dates; MCL's other 18 are the data runs, so
   **any fix must be calendar-free**.
5. **After the VOID gate, 62–68% of surviving 60m arms still never fire.** Conjunctive zeros, not
   structural ones. **The median live MCL 60m arm fires 4–5 times in 718 days** (~2.5/year) against
   MGC's 12–13. MCL 60m is the thinnest cell in the study, and it is also the cost-fragile contract and
   the one with the data runs — three things pointing the same way.
6. **In the swing setting the clock is the dominant exit** — EF1's arm C closes **59–76% of trades** on
   the 16:00 flat. So the twelve exit geometries differ mostly in their **stop**; the target is usually
   never reached, and `time_stop_bars` (30–120 bars = 30–120 hours at 60m) is **unreachable** under a
   22-hour ceiling and must not be reported as a tested axis.
7. **`EF6`'s `forward.roll` is well calibrated on pure noise** — 40 mean-zero ledgers in EF2's own
   emitted shape: mean `z_vs_null` −0.078, **0 of 40** above +1.96, mean `selection_edge_vs_universe_r`
   −0.0020 R, `share edge > 0` 0.525, and **0 of 40** firing its "beat both universe and null" verdict.
   Limit: calibrated at n = 300; EF2's cells are 1,470–1,812 arms.
8. **The gap-fill tail differs by cell.** With `veto_signals_in_window=False` a signal on the 16:00–17:00
   bar fills at the next bar's open — after a Friday, the Sunday reopen. MGC 60m: 503 such fills, median
   0.07 R, max 8.60 R on ATR×0.75. MCL 60m: 552, median 0.15 R, **max 15.45 R**. (Withdrawn 240m cells
   were worse: MCL 240m median **1.08 R**, 7.3% over 5 R.) The 405.70-point MGC figure was **checked,
   not assumed**: a real crash (gold 5447→4676 over five days) **plus** the 51-hour hole.
9. **`session_extreme_sweep` is VOID at 60m and LIVE at 240m** (200/107 fires, **zero** in RTH at 60m;
   1,891/1,705 fires with 1,414/1,600 in RTH at 240m; EF6 independently 1,652–2,134 at 240m). R1's
   D-L4 is true at 60m under `rth_only=True` and false at 240m — the clearest instance in the corpus of
   why `VOID` had to be per-(symbol, timeframe), landing on its own author's example.
10. **`MULTI_TIMEFRAME` is expressible in exactly one EF2 cell** (`f60_240__p60`) and **unaskable at
    240m on MCL at all**, because making its signals live needs a timeframe above 240m and
    `MCL_1440m.jsonl` holds **one row**. `scan_reports/2026-09-24` Part B lists MULTI_TIMEFRAME among
    what "measured best" on MGC; that is a statement about the frame it was measured in.

## 7. What is ready to run the instant a validated harness exists

One command, then three calls. Everything below is on disk and tested end to end **except** where noted.

```
python3 workspace/roundtable/edge/EF2/code/measure.py --engine session   # the swing setting
python3 workspace/roundtable/edge/EF2/code/measure.py --engine shipped   # labelled NON-swing control
```
then, per (symbol, cell, `rth` arm) ledger the first command writes to `EF2/data/ledgers/`:
```
EF6/code/forward.roll(Ledger(json), lookback_days=180, trade_days=60, criterion="expectancy")
EF6/code/placebo_w.build_cohort(frame, shortlist, realised, seed=0..19)
EF2/code/rank.select(rows, k=10)
```

- **`measure.py`** is a drop-in against `EF1-H2`, **one `rth` stratum at a time** (asserted — one
  `run_many` over both strata would collide ids and measure a between-arm difference of exactly zero,
  D48). The 60m base passes `_audit_grid`: **zero `INTERIOR` bars**, so no `SessionGridError`.
  **Verified end to end on real output:** 60 MGC arms → 566 trades → a valid `forward.Ledger` with
  `S = 60`.
- **Metrics implemented and verified present on a real row:** expectancy in R, win rate **and** payoff
  together, avg win/loss, profit factor, per-trade Sharpe and Sortino, t of the R series, max and avg
  drawdown in R, max consecutive wins and losses, avg and max duration (from the engine's own
  `minutes_held`), MAE, MFE, gross vs net and the cost drag, trade count, per-fold expectancy and trade
  count, and **slices by session, regime, volatility, time bucket, day of week, exit reason and
  direction** — every one already carried on `Trade` `[repo-verified: engine.py:148-152]`.
- **Controls:** `EF6/code/placebo_w.py`, kinds `placebo_random_legal` + `placebo_session_shuffle`.
  **`placebo_shift` excluded (D42 — it leaks)** and **`placebo_shuffle` excluded** (EF6 Fault 2: it
  permutes *direction labels*, so on a one-sided rule set it destroys nothing; EF2 measured degeneracy
  **0.52–0.68** on its own cells). 20 seeds × 2 kinds = **40 control observations per row**, empirical
  p floored at 0.025.
- **`rank.py` enforces reportability in code:** a row missing its control, its search size or its
  forward result is **dropped**, not printed blank; `select` returns however many rows clear their own
  controls **up to** ten with every rejection reason counted; a defensive clone-collapse pass on
  (cell, signals, filters); and each row carries its cell's flat-unreachable count, the measured D45
  collapse rate for its own `stop_kind` and cell, gross-vs-net and whether costs flipped the sign, and —
  for MCL — a with-and-without variant for the two gap runs, **named before any expectancy exists**.
- **Pre-registered and fixed in writing:** `EF2-HYP-1` (`rth_only` paired arm, **two-sided** — amended
  before measurement because EF4 is right that **D24's sign does not transfer**: D24 measured
  `rth_only=False` under the old regime where a position was flattened at the contract's RTH close, so
  an overnight entry had no runway), `EF2-HYP-2` (60m alone vs 60m in the 60m+240m frame, rule set held
  fixed — now *cleaner* than the withdrawn 4-cell version, since both arms share a base grid, a primary
  timeframe and a hold ceiling), `EF2-HYP-5` (MCL cost fragility replicates), `EF2-HYP-6` (win rate and
  payoff cancel on this substrate). `EF2-HYP-3` and `EF2-HYP-4` withdrawn with the 240m cells.
- **`EF2-HYP-A2`, the answerable form of the deliverable** (`bursts/11`). At `n = 26` (13 groups × 2 surviving cells) the threshold is `free_t` 2.553 → **Sharpe 1.82**, against the
  strategy-level screen's 2.86–2.88. Trade-weighted pooling registered, equal-weighted reported beside
  it, controls pooled the same way, and a structurally empty (group, cell) reported as **VOID, never as
  0.00R**.
- **Not run:** `EF2/code/prefix_invariance.py` — written and importable, artefact not produced before the
  park. It is the look-ahead test done by measurement rather than by reading: build the frame on a
  prefix and on the full series and require the fire sets to match exactly, stopping 8 bars before the
  cut so the fractal swing detector's 3-bar confirmation lag cannot manufacture a pass. **Run it first
  on resumption.** The four guards it tests were verified by code reading and all pass
  (`_build_swing_pointers` gates on `confirmed_index <= i`; `active_fvgs` masks `filled_index`;
  `active_zones` applies `as_of`; 240m resampled `keep_partial=False`).

## 8. What I would do next, in order

1. **Run `prefix_invariance.py`.** It is the only anti-overfitting check on my register that is written
   and unmeasured, and it is the one that would catch a future change breaking one of the four
   look-ahead guards.
2. **Re-run the census and population once EF1 re-declares**, because `EF1-H1`'s component-1b
   session-end flat changes which bars are holdable and therefore could change `fires_swing` at the
   margin. Cheap (~15 min) and it is the foundation everything else sits on.
3. **Measure `EF2-HYP-A2` before the strategy-level screen.** It is the only tier whose width this span
   can settle (Sharpe 1.82 vs 2.86), and it makes `scan_reports/2026-09-24` Part B's per-symbol group
   claim a testable prediction instead of a summary. If MCL MOMENTUM at 60m does not reproduce, that is
   a clean, reportable negative on the corpus's strongest published claim.
4. **Then the strategy-level top 10**, with `free_t = 4.014 / 4.033` and "needs Sharpe 2.86 / 2.88" on
   every row, each row's placebo, and `selection_edge_vs_universe_r` from `forward.roll`. **Expect to
   hand over fewer than ten.** `rank.py` is built to; the prior attempt's list underperformed trading
   the whole qualifying universe, and a padded list is the specific failure being avoided.
5. **Ask the board for a ruling on one thing I deliberately did not act on:** `EF6`'s divisibility rule
   is stated about the **base** grid, EF2's 240m cells always used a 60m base, and EF1's post-fix
   saturation at 240m reports `viol = 0` under the strict audit with `over = 0`. What a 240m thesis
   could *not* do is reach the window's ceiling — **16 hours, not 22**, because the flat lands on the
   `[12:00,16:00)` bucket and `[16:00,20:00)` is `IN_WINDOW` and vetoed. That 16-vs-22 shortfall is the
   5.5-window misalignment expressed as hold time and is a **substantive** reason to drop the cell, not
   a technicality. Recorded in `bursts/13`; not contested.

## 9. Files

| path | what |
|---|---|
| `EF2/FINDINGS.md` | this file |
| `EF2/bursts/01`–`13` | one burst per unit of work, written as it was done |
| `EF2/code/substrate.py` | the substrate decision, the `csv/raw` equivalence check, the session arithmetic |
| `EF2/code/census.py` | the firing-rate census (uses `EF6/code/window.signal_mask`) |
| `EF2/code/census_report.py` | census → per-cell VOID verdicts |
| `EF2/code/population.py` | the population, the arm-aware VOID gate, the D48 uniqueness assert |
| `EF2/code/firecount.py` | the harness-independent raw-fire census |
| `EF2/code/stopfidelity.py` | D45 per cell, and the `stop=None` rate |
| `EF2/code/flat_reachability.py` | imports `EF1-H1`; cycles where the flat cannot fire |
| `EF2/code/weekend_gap.py` | the gap-fill tail in R |
| `EF2/code/mcl_placebo_probe.py` | EF6's placebo Faults 1 and 2 re-measured on MCL |
| `EF2/code/calibrate_roll.py` | `forward.roll` on 40 mean-zero ledgers |
| `EF2/code/prefix_invariance.py` | the look-ahead test — **written, not yet run** |
| `EF2/code/plan.py` | the pre-registered plan: `EF2-HYP-1..6`, `A2`, controls, forward roll, floor, the 15-item overfitting register |
| `EF2/code/measure.py` | the measurement run and the EF6 ledger emitter |
| `EF2/code/rank.py` | ranking on expectancy in R, reportability enforced in code |
| `EF2/data/*.json` | every artefact above |
| `msgs/EF2-01`…`EF2-05` | `rth_only`; flat reachability + the MCL gap; the id collision; the roll calibration; this handover |

**Nothing in EF2 was committed or pushed.** `csv/` was read only.
