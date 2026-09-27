# EF2 / Burst 03 — the population, its exact size, and the thresholds it faces

Code: `EF2/code/population.py`. Artefact: `EF2/data/population.json`.
Pre-registered plan: `EF2/code/plan.py` → `EF2/data/plan.json`.

## Four construction decisions, each fixing a confound

**1. All thirteen groups, explicitly, on both symbols.** `generate_combinations` with `groups=None`
falls through to `groups_for(symbol, ...)` `[repo-verified: combinator.py:489-494]`, which returns
**6 groups for MGC** (`TREND, SUPPLY_DEMAND, FIBONACCI, MULTI_TIMEFRAME, MEAN_REVERSION,
VOLUME_PROFILE`) and **`None` — i.e. all 13 — for MCL** `[measured: profiles.groups_for]`. Defaulting
would have narrowed MGC to 6/13 of the strategy space while MCL got the lot, and any MGC-vs-MCL
difference would partly have been that. Passed explicitly.

**2. Rule sets drawn ONCE per symbol, instantiated in all four cells.** `generate_combinations` builds
`rule_sets` as the product of names × timeframes × exits and then `rng.sample`s it
`[repo-verified: combinator.py:539-560]`, so calling it with `[60]` and with `[60,240]` draws
*different* rule sets. Comparing "60m alone" to "60m in a group" that way compares two unrelated
samples and attributes the difference to the frame — D14's exact shape, which left MES and MGC 60m
sharing **0 of 204** rule sets. One draw, rebuilt per cell, makes a between-cell difference a cell
difference. Rule sets are **not** shared across symbols: the independence rule, and
`strategies_for_symbols`' own docstring forbids a cross-symbol league table
`[repo-verified: combinator.py:646-676]`.

**3. `rth_only` is a paired arm, not an inherited default.** Burst 01 §2b: with `True` the
18:00→16:00 rule adds zero entry opportunity on these two contracts.

**4. D48 asserted, not trusted.** Every `dataclasses.replace` on a `Strategy` passes `_id=None`, and
`population.py` **raises** unless every arm id is unique within its (cell, `rth_only`) stratum.
`generate_strategies` reads `strategy_id` in its own dedupe `[repo-verified: combinator.py:719]`, so
every strategy it returns already has `_id` populated and a bare `replace` would carry it forward.
**The assert passes: `max_arms_sharing_an_id_within_cell_and_arm = 1` on both symbols.**

A note that is *not* a collision and must not be read as one: `f240__p240` and `f60_240__p240` hold
**content-identical** strategies (`confirm_tfs=()` in both), so they legitimately share
`strategy_id`. Arms are therefore keyed `cell|rth|strategy_id`, and the uniqueness assert is scoped
*within* a (cell, arm) stratum. This is what makes hypothesis **EF2-H3** possible: the two 240m cells
differ **only** in the frame they are evaluated in, so the comparison is a single-variable test of
`_default_regime_tf` (60 for `(60,240)`, falling through to 240 for `(240,)`
`[repo-verified: features.py:820-826]`) plus the alignment vote's membership.

## The population

| | MGC | MCL |
|---|---|---|
| rule sets drawn (seed 20260927, `max_total=2000`, 13 groups) | **972** | **973** |
| candidate arms = rule sets × 4 cells × 2 `rth_only` arms | **7,776** | **7,784** |
| removed by the VOID gate | **2,684 (34.5%)** | **2,200 (28.3%)** |
| `_build_strategy` returned `None` | 0 | 0 |
| **published population** | **5,092 arms** | **5,584 arms** |
| `free_t = sqrt(2·ln n)` | **4.132** | **4.154** |
| Sharpe needed, on `sqrt(718/365.25) = 1.402` | **2.95** | **2.96** |
| `free_t` if the pre-gate denominator is used instead | 4.233 | 4.233 |

**Both denominators are published** so `free_t` can be recomputed either way. It barely matters —
`free_t` is logarithmic, and removing 34.5% of the candidates moves the threshold by 0.10 t-units.
That is the point the manager made closing `R1-Q2` and it holds here: the VOID gate is not a way to
lower the bar, it is a way to stop reporting a null that was never a measurement.

### VOID removal by cell — this is where the census pays

| cell | MGC kept | MGC removed | rate | MCL kept | MCL removed | rate |
|---|---|---|---|---|---|---|
| `f60__p60` | 1,440 | 504 | 25.9% | 1,564 | 382 | 19.6% |
| `f60_240__p60` | 1,656 | 288 | **14.8%** | 1,780 | 166 | **8.5%** |
| `f240__p240` | 998 | 946 | **48.7%** | 1,120 | 826 | **42.4%** |
| `f60_240__p240` | 998 | 946 | **48.7%** | 1,120 | 826 | **42.4%** |

**Nearly half of every 240m candidate is structurally incapable of trading**, against 8.5–15% of the
60m-in-group candidates. A 240m top 10 drawn without this gate would be selected from a pool whose
composition is set by which conditions happen to exist at 4 hours, not by the market. The
per-timeframe spread — 8.5% to 48.7%, a 5.7× range within one symbol — is exactly why `VOID` is a
per-(symbol, timeframe) verdict and why the programme-wide "19.0%" does not transfer to a cell.

Leading causes, by arm count (a strategy may carry two):

| MGC | | MCL | |
|---|---|---|---|
| `mtf_strongly_aligned` | 396 | `mtf_strongly_aligned` | 408 |
| `opening_range_fade` | 384 | `poc_reversion` | 348 |
| `value_area_breakout` | 344 | `mtf_aligned` | 282 |
| `mtf_aligned` | 300 | `value_area_edge` | 248 |
| `poc_reversion` | 284 | `oi_price_confirmation` | 240 |
| `value_area_edge` | 276 | `lvn_rejection` | 232 |
| `opening_range_breakout` | 224 | `oi_expanding` | 216 |
| `oi_expanding` | 216 | `value_area_breakout` | 172 |
| `lvn_rejection` | 180 | `away_from_hvn` | 136 |
| `away_from_hvn` | 136 | `session_extreme_sweep` | 128 |
| `session_extreme_sweep` | 128 | `open_outside_value` | 60 |
| `oi_price_confirmation` | 128 | | |
| `open_outside_value` | 60 | | |

`opening_range_*` accounts for **608 removed MGC arms and 0 MCL arms** — the single largest
symbol-specific difference in the whole gate, and it is the 08:20-vs-09:00 RTH open against a
hard-coded `or_minutes = 30`, nothing to do with gold versus oil.

### Groups that cannot be tested at all in a cell — identical on both symbols

| cell | groups with **zero** surviving arms |
|---|---|
| `f60__p60` | `MULTI_TIMEFRAME` |
| `f60_240__p60` | none — 13/13 |
| `f240__p240` | `MULTI_TIMEFRAME`, `VOLUME_PROFILE` |
| `f60_240__p240` | `MULTI_TIMEFRAME`, `VOLUME_PROFILE` |

**MULTI_TIMEFRAME is expressible in exactly one of four cells** (60m inside the 60m+240m group), on
both symbols, because its two required SIGNALs are VOID at the frame's top timeframe and both are in
a *required* group so no substitute exists. **VOLUME_PROFILE is inexpressible at 240m on both
symbols**, because all four `profile` SIGNALs are VOID there and `profile` is its only required group.

**This retires a published per-symbol claim before it is re-tested.** `scan_reports/2026-09-24`'s
Part B lists MULTI_TIMEFRAME among the four things that "measured best" on MGC. In three of my four
cells that group **cannot fire at all**; and R1 measured 48 of 1,260 generated strategies carrying a
top-timeframe MTF signal. So any MGC MULTI_TIMEFRAME row in the published corpus was measured in a
frame whose composition permitted it, and the claim is about a frame, not about MGC. I am not
retracting someone else's number — I am stating that in the EF2 cell it is unaskable in 3 of 4
configurations, and my `f60_240__p60` result will be the only place it is answered.

## Thresholds, stated before any measurement

| tier | n | threshold | Sharpe needed on 1.402 sqrt-years |
|---|---|---|---|
| Tier B screen, MGC | 5,092 | `free_t` = **4.132** | **2.95** |
| Tier B screen, MCL | 5,584 | `free_t` = **4.154** | **2.96** |
| Tier A, 6 pre-registered hypotheses | 6 | Bonferroni two-sided **\|t\| ≥ 2.39** | **1.70** |
| (the code's floor for ONE pre-registered hypothesis) | 1 | `free_t` = 1.177 | 0.84 |

Tier A is where a live-eligible result could actually come from on this span. Tier B at Sharpe 2.96 is
close to out of reach, and I am saying so before measuring rather than after.

## The six pre-registered hypotheses, fixed now

`EF2/data/plan.json` holds the full text with each one's predicted **direction** and named test.
In one line each:

- **EF2-H1** — `rth_only=False` does **not** improve expectancy in R (D24 predicts worse). Paired t
  on the per-rule-set difference. *This is the axis the programme's session rule exists to open.*
- **EF2-H2** — a 60m thesis in a 60m+240m frame is **not** better than in a 60m-only frame
  (BRIEF rule 2). Paired t, rule set held fixed.
- **EF2-H3** — the two 240m cells differ (prediction: **non-zero**, because frame composition alone
  moved a base filter's pass rate 13 points in R1). The only single-variable test available here.
- **EF2-H4** — 60m vs 240m, **two-sided, no direction registered**, because the published priors point
  opposite ways on my two symbols.
- **EF2-H5** — MCL's cost fragility replicates (prior: 8/183 MCL vs 1/259 MGC flipped by costs).
- **EF2-H6** — win rate and payoff cancel on **this** substrate: corr(win, payoff) < −0.5.

Controls, forward roll and the trade floor are pre-registered in the same file:
`placebo_random` + `placebo_shuffle` only (**`placebo_shift` excluded, D42 — it leaks**), 200 draws,
count-matched from the row's own admissible bar set with the row's own long/short split, run through
the row's own exits and the same clock rule; 6-block anchored walk-forward, 5 test folds, no test
fold re-used; 30-trade floor reported as a separate attrition step. And the benchmark this repo's
prior attempt failed is pre-registered as a required output: **selected top 10 versus the entire
qualifying universe**, because that is the comparison that showed selecting was worse than not
selecting.
