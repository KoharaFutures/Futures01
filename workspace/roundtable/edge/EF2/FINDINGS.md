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

## F9 — MCL's 60m series is missing 366 bars in two contiguous runs, in BOTH stores, and the 16:00 flat cannot fire in 34 of its 505 cycles

Prompted by `EF3-01`, which found EF1's `classify_bar` under-enforcing the flat on 19 of 507 MES/MNQ
sessions. **I re-measured on my own symbols rather than inheriting the count** — MGC is COMEX, MCL is
NYMEX, neither shares the equity complex's calendar. Detail: `bursts/06`.

| cell | bars | cycles | **cycles where the flat cannot fire** | share |
|---|---|---|---|---|
| MGC 60m | 11,297 | 506 | **17** | **3.36%** |
| MGC 240m | 3,052 | 602 | 9 | 1.50% |
| **MCL 60m** | 10,934 | 505 | **34** | **6.73%** |
| MCL 240m | 2,990 | 596 | 14 | 2.35% |

Zero `INTERIOR` bars in any cell, so `SessionGridError` never fires and the run proceeds while those
cycles go untested. **The audit is per series; the hole is per cycle.**

**16 of MGC's 17 and 16 of MCL's 34 are the same holiday dates.** MCL's other **18** are ordinary
weekdays on which MCL is simply missing bars:

```
MGC archive 60m 11,297 bars   MCL archive 60m 10,934 bars
bars MGC has that MCL lacks: 366, over 34 dates, in two contiguous runs:
    2026-01-09 -> 2026-01-16   and   2026-02-20 -> 2026-03-11
on those dates: MGC 442 bars, MCL 102 bars
csv/raw/MCL_1h.csv on those dates: 102 bars — bars csv/raw has that the archive LACKS: 0
```

**Absent from both stores.** So `BarArchive` behaved correctly, this is the vendor's MCL series, and
**every published MCL result in `scan_reports/` rests on the same gap.** The BRIEF's data policy
verified the two stores hold the *same* series over *overlapping* stamps; it never asked whether either
is *complete*. On MCL at 60m it is not — 3.3% of the series.

**Independently confirmed by EF1** on a different method and a different population:
*"a two-month hole in MCL 60m — 17 further dates, 2026-01-12 to 2026-03-10 … 1 to 5 bars each …
this is a substrate defect, not a calendar one"*. EF1's arm-C validation found **33 `SPANS_WINDOW`
violations, every one at `primary_tf = 240m`, 18 of them MCL.** Two agents, disjoint methods, agreeing.

Raised with the manager as a D-candidate (`msgs/EF2-03`); only the manager allocates `D` numbers.
Every MCL row will be reported **with and without** the two windows, named above before any expectancy
exists. `D40`'s consequence without `D40`'s cause: not splicing, absence — but the bar after a
multi-day hole still carries a multi-day return that a one-bar momentum rule reads as a one-hour move.

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
