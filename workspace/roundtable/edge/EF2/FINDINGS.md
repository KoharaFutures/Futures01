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

**F1c.** A 240m bar cannot straddle the 2-hour break cleanly. The 240m ET grid is 00/04/08/12/16/20:
the bar stamped **12:00 closes at exactly 16:00** (so a next-bar-open fill lands at the deadline and is
inadmissible) and the bar stamped **16:00 spans the whole no-position window**.

| symbol | tf | bars inadmissible as a signal bar |
|---|---|---|
| MGC | 60m | 984 / 11,297 = **8.7%** |
| MGC | 240m | 1,083 / 3,052 = **35.5%** |
| MCL | 60m | 944 / 10,934 = **8.6%** |
| MCL | 240m | 1,054 / 2,990 = **35.3%** |

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

| cell | arms kept by the VOID gate | arms with >=1 raw fire | **arms that still never fire** |
|---|---|---|---|
| `MGC:f240__p240` | 998 | 333 | **665 = 66.6%** |
| `MGC:f60_240__p240` | 998 | 324 | **674 = 67.5%** |
| `MGC:f60_240__p60` | 1,656 | 635 | **1,021 = 61.7%** |

**The VOID gate removes about a third of the candidates and roughly two thirds of what it passes still
never fires.** Two different findings; only the first is what the 19.0% figure describes. A VOID
condition is a *structural* zero; these are *conjunctive* zeros — every condition fires somewhere, but
the strict AND of 2-4 signals plus 2-4 filters plus `rth_only` is empty over 718 days. It changes the
**effective** search size by a factor of three.

---

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

## F6 — Stop-kind fidelity (D45) per cell

See `bursts/04`.

---

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
