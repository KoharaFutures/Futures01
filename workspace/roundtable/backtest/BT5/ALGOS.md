# BT5 — algorithms

Every number in this file is measured on the frozen `csv/raw` snapshot, reached through the stored
artefact `workspace/strategy_research/scratch/geo_trades.json`, which is **read and never written**.
Nothing here touches `data/archive/`, so `BRIEF.md`'s 2026-09-27 data ruling condition 1 is
discharged by store: **`csv/raw` only**.

---

## ALGO-1 Activity stratification of a settled finding, on the wall-clock grid

- **Implements:** `research/R5_SCOPE.md` §"S2 — Does the settled finding vary with per-bar activity,
  on the grid we already have?" (lines 357-428), which is R5's scope *proposal* S2. **It is not
  `MAIN-01/S2`**: `BOARD.md` records "Sections allocated — none, and now none ever" for `MAIN-01`
  (ADJ-16c) `[repo-verified: manager/BOARD.md:61]`, and R5 said the same
  `[repo-verified: research/R5_SCOPE.md:216-219]`. Cited as `R5_SCOPE §S2` throughout.
- **Code:**
  - `backtest/BT5/code/activity.py` — the join. Rebuilds the generating study's 24 cells through
    its own code path, computes the per-bar statistics `MAIN-01` names with the library's own
    functions at the library's own parameters, and attaches them to every stored trade at the
    **signal** bar.
  - `backtest/BT5/code/s2.py` — the measurement. Three stratifier axes, two layers (bar-level and
    per-strategy), the permutation null that doubles as the placebo, and the sensitivity grid.
  - `backtest/BT5/code/checks.py` — ten assertions, all passing.
  - `tests/test_bt5_activity_strata.py` — 15 tests inside the repo suite.
  - Output: `backtest/BT5/code/s2_report.json`.
- **Fidelity:** **ASKED** — `msgs/BT5-01_R5_verify-ALGO-1.md`. No number below should be read as
  verified until R5 rules.

### My reading of the finding

`MAIN-01` claims that part of this repository's null may be a property of the *wall clock*, and it
names a mechanism: **per-bar statistics weight unequal-activity bars equally.** ATR, relative
volume, band widths and the close-location value the delta proxy is built from each count a bar as
one observation, while activity per bar varies by a large factor depending on when the bar falls. A
volume clock's first-order effect is to equalise activity per bar.

R5's S2 turns that into a test that needs no constructed bars. If the mechanism is operating, then
**regrouping the existing wall-clock bars by activity must already move something** — because
re-clocking is, to first order, exactly such a regrouping. If it moves nothing, re-clocking has
little left to change, and the motivation for paying for the counterfactual is gone.

Three things I read R5 as insisting on, and each shapes the code:

1. **It is a necessary-condition test, not the counterfactual.** A null here is "no footprint of
   the named mechanism", never "the clock is not a confound". Re-clocking also changes *which* bars
   exist and hence when signals fire; stratification cannot reproduce that. Stated in every line of
   the report.
2. **The raw form is partly pre-answered and the content is in the residual.** Activity is largely
   time of day, and `BRIEF.md` rule 6 already records that no hours filter improves expectancy. So
   the raw stratification is largely foreseeable, and the new information is in activity
   *residualised on time of day*.
3. **The unit is per-strategy.** R3 ruled this for BT3 over the same artefact
   `[repo-verified: backtest/BT3/ALGOS.md:114-125, "Population unit — and the two readings disagree
   by a factor of 24"]`. A per-trade average over 21,954 pooled trades is not a per-strategy result.

### What BT3 already established over this artefact, and which I use rather than redo

- **The generating study is deterministic and the dump is reproducible.** BT3's `stops.py` re-ran
  the `partner == "none"` subset of `run_geometry.py` and matched all 21,954 trades exactly, zero
  missing, worst `|Δr| = 0.000e+00` `[repo-verified: backtest/BT3/ALGOS.md:204-216]`. ALGO-1 relies
  on that and on nothing weaker: it rebuilds the same 24 cells with `toolkit.disjoint_slices` /
  `toolkit.slice_series`, which is the code `run_geometry.py` calls
  `[repo-verified: workspace/newstrats/run_geometry.py:149-152]`, and the join comes out total.
- **The dump records no stop distance.** None of its 17 keys is a price, a point distance or a
  dollar figure `[repo-verified: backtest/BT3/ALGOS.md:204-216, choice 9]`. ALGO-1 therefore never
  recomputes `r`; it only re-aggregates it. Where R5's third S2 question needs a
  distance-to-invalidation, ALGO-1 uses the **modelled** distance `stop_mult × atr(signal bar)`,
  which is exactly recoverable, and says so — not the realised `|entry − stop|`, which BT3 had to
  re-run the study to recover.
- **The population is 176 strategies**, keyed `(symbol, tf, arm, exitm)`, and they are correlated
  variants of one signal rather than a portfolio `[repo-verified: backtest/BT3/ALGOS.md:114-125]`.
  ALGO-1's join independently reproduces 176.

---

## Where I had to choose

Fourteen places R5's S2 was silent or where the code forced a decision. The first four are the
load-bearing ones and they are the ones I want R5's ruling on.

**1. Which bar is "the" bar — and the dump does not store it.**
`Trade.entry_ts` is the **fill** bar's timestamp, not the signal bar's: the engine fills pending
entries at step 1 of bar *i* from a signal raised at step 3 of bar *i−1*
`[repo-verified: futures_agents/backtest/engine.py:290-295 and :372, entry_ts=bar.ts inside
_open_position, which is called from the "fill pending entries at this bar's open" block]`. So the
bar whose statistics the strategy read, and the last bar knowable at the decision, is the bar **one
timeframe before** the dump's `ts`.

ALGO-1 stratifies the **signal bar**. The fill bar is carried as a secondary field and labelled
*not knowable at the decision*. R5's S2 text says "activity at entry", which I read as identifying
the trade rather than prescribing the fill bar — but this is the single choice that most changes
what is being measured, so it is fidelity question 1.

`tests/test_bt5_activity_strata.py::test_bt5_signal_bar_offset_is_exactly_one_bar_before_entry_ts`
pins the offset in the repo suite, because if the engine's fill location ever moved, every number
here would silently start conditioning on the wrong bar.

**2. The activity measure: contract volume, and no substitute for it.**
`volume` from the same series the study used. The CSV header is
`open_time,open,high,low,close,volume` and there is no trade count, no tick count and no dollar
value, so "activity" here can only be contracts. A 14-bar trailing mean is also attached
(`sig_win_vol`, window = `ATR_PERIOD`, ending at the signal bar inclusive so it stays causal),
because R5 asked for activity "over the ATR lookback"; the reported strata are built on the
signal-bar value, with the trailing mean available in the artefact for anyone who wants the other
reading.

**3. Residualisation: three axes, and which one is the answer.**

| axis | definition | removes time of day? | causal? |
|---|---|---|---|
| `RAW` | signal-bar `volume` | no — this is the pre-answered form | yes |
| `RELVOL` | `relative_volume(bars, 20)` at the signal bar | yes, the level | yes |
| `TODRANK` | percentile rank of signal-bar volume **within its own ET clock bucket**, over the cell | yes, any monotone transform | no (declared) |

`RELVOL` is **the library's own function, not a construction of mine**: volume divided by the
trailing-20-session mean of the *same ET clock bucket*
`[repo-verified: futures_agents/indicators/volume.py:266-286]`. That matters for R5's caveat 5,
which binds S2 to `MGR-T13`'s time-of-day norm and carries R1's constraint "both axes take the
time-of-day norm or neither does" verbatim. I did not wait for `MGR-T13`: I **adopted the repo's own
`relative_volume` norm** — 20 trailing sessions, same `(hour, minute)` bucket, current bar excluded
from its own denominator — and I am saying so, which is the second branch R5 allowed
(`R5_SCOPE.md:410-418`: "S2 either waits on `MGR-T13` or adopts its time-of-day norm by assumption
and says so").

`TODRANK` exists because `RELVOL` removes the *level* of the time-of-day effect but not its
*dispersion*: a 09:30 bar and a 03:00 bar can have the same relative volume while their
relative-volume distributions differ. A within-bucket rank removes any monotone time-of-day
transform and forces each stratum to be uniform in time of day by construction. It is a full-sample
transform of the **bars**, so it is not causal — I record that rather than hiding it. It is
identical for every strategy and is computed without reference to any trade or any R, so it can
mis-assign a bar to a stratum but it cannot manufacture an expectancy difference.
`checks.py::check_todrank_is_time_of_day_neutral` asserts the residualisation actually worked
instead of assuming it: the total-variation distance between the HIGH and LOW strata's time-of-day
composition is **0.734 for RAW and 0.019 for TODRANK**. Without that assertion a "residualised"
answer could quietly be the raw answer wearing a different name.

**4. Strata boundaries: terciles, cut on bars, cut per cell.**
Three strata, contrast = HIGH minus LOW, middle stratum reported but not contrasted.

- **Cut on the bar population, not the trade population.** The mechanism under test is a statement
  about bars. Letting the trades define the cuts would let a strategy's own selectivity move the
  boundary, so a selective arm and an unselective arm would not be stratified the same way.
- **Cut per cell, not per (symbol, tf).** Volume drifts across the three disjoint slices, so a
  pooled cut would make stratum membership partly a slice indicator, and the slices differ in
  regime. `checks.py::check_strata_are_count_balanced` measures the worst per-cell deviation from a
  third at **0.0088**.
- Median split (k=2) and quintiles (k=5) are run as sensitivity and **counted** in the search size.

**5. Zero-volume bars, which exist at 60m and at 240m and are not the footnote R5's S0 sized.**
R5's §2.2 measured 5 zero-volume bars per archive **1-minute** series (0.1%). On the grid the
settled findings actually live on the rate is **two orders of magnitude higher**: 3.55–3.95% of
hourly bars in `csv/raw` have `volume == 0`, and **593 of the 21,954 trades were decided on a
zero-volume signal bar** (2.7%) `[measured: code/s2_report.json → coverage.signal_vol_zero = 593;
dispersion[].zero_volume_bars]`. The rule, written down rather than discovered:

- `RAW`: a zero-volume bar is a legitimate lowest-activity observation and is kept.
- `RELVOL`: undefined when the trailing same-bucket mean is zero — `relative_volume` already returns
  `None` there `[repo-verified: futures_agents/indicators/volume.py:280]`. Those trades leave the
  `RELVOL` axis, and the count is reported (**67 trades**, plus the first appearance of each clock
  bucket which has no prior).
- `TODRANK`: zero-volume bars tie, and ties take the **average** rank. If they did not, a block of
  equal-volume bars would be ordered by its position in the file — a time index wearing an activity
  label. Pinned by `test_within_bucket_rank_averages_ties`.

**6. The unit, stated three ways, with only one of them a result.**

- **PER-STRATEGY (the result).** 176 strategies keyed `(symbol, tf, arm, exitm)`, each spanning its
  three slices as BT3 did. Statistic = median across qualifying strategies of the within-strategy
  HIGH−LOW contrast.
- **PER (SYMBOL, TF) (a cut, 22 strategies each).** Because pooling across cells is the second of
  this repository's three measured pooling levels.
- **POOLED (a diagnostic of pooling, never a result).** One per-trade average over all 21,954.

**7. Minimum stratum size: 10 trades per stratum per strategy.** Pre-registered before measuring.
Arms differ by a factor of ~7 in trade count (`swing_symmetry_impulse` 3,451 vs
`pullbacks_deepening` 460), so some strategies cannot support a contrast at all; the count that
qualifies is reported rather than the threshold being tuned until it looks good. `min_n` ∈ {5, 20}
is sensitivity and is **counted**.

**8. The test: a bar-level label permutation, blocked within (cell, ET clock bucket).**
Named, per PIPELINE §4 obligation 3, and it is not `T.ab`.

Permuting stratum labels among the bars *inside each block* preserves the trade set, every
strategy's R values, the per-block label frequencies and the **time-of-day composition of every
stratum**, and destroys only the association between activity and trade. Two properties make this
the right test rather than a convenience:

- It is **time-of-day-matched**, so a residualised axis is tested against a residualised null. A
  cell-level block would test it against the raw null and the p would be optimistic.
  `checks.py::check_permutation_preserves_block_composition` asserts labels never cross a block.
- It **preserves the correlation among the 176 strategies**, because the same permuted bar labels
  are applied to all of them. That is what makes an aggregate statistic over correlated variants
  testable at all; a strategy-level t-test would not be, which is D28's whole subject.

`RAW` gets **both** nulls: cell-blocked (does activity matter at all) and bucket-blocked (does the
part of raw activity that is not time of day matter). Both counted.

**9. The placebo is the same object as the null, and one draw is reported explicitly.**
R5 named the control: "a stratifier with the same marginal distribution and no activity content,
e.g. a within-session shuffle of the activity labels". That is exactly the permutation. PIPELINE §4
obligation 1 wants a control *beside* the result, so draw 0 of each ensemble is reported as
`placebo_single_draw` alongside the full null distribution. `placebo_shift` is not used (D42).

**10. The secondary test, and why it is secondary.** An **exact two-sided binomial sign test** on
the per-strategy contrast signs. Reported, and flagged: the 176 are correlated variants of one
signal, so its nominal p is optimistic. The permutation test is primary.

**11. R is re-aggregated, never recomputed.** The dump's `r` is `net_r`, costs already inside
`[repo-verified: workspace/newstrats/run_geometry.py:113 → r=round(t.net_r, 5)]`.
`checks.py::check_r_is_not_recomputed` asserts the 21,954 values are identical to the dump's and
that the dump holds none of `entry/stop/risk_points/pnl`.

**12. The per-bar statistics are recomputed, and the recomputation is proved.** `bar_table` calls
`atr(h,l,c,14)`, `relative_volume(bars,20)`, `bollinger(c,20,2.0)`, `keltner(h,l,c,20,1.5)` and
`close_location_value(bar)` — the library's own functions at `features.py`'s own parameters
`[repo-verified: futures_agents/features.py:235, :242, :259, :271]`. Recomputing instead of reading
the frame is a shortcut, so `checks.py::check_indicators_match_the_frame_the_study_used` asserts
that `atr` and `rel_volume` are **identical, element by element, to `build_symbol_frame`'s
columns** over all 1,626 bars of MCL 60m S1.

**13. The `mins == 0` set is kept.** 2,900 of 21,954 rows are same-bar exits with mean R −0.79
`[repo-verified: backtest/BT3/ALGOS.md:166-170]`. They are real trades of the generating study and
dropping them would be a filter on the outcome, which is the thing stratification must not do. They
are, however, the group most likely to be activity-sensitive, so any effect found should be checked
against them — noted as an open thread, not measured here.

**14. Distance to invalidation: the modelled distance, and why the realised one is unavailable.**
Both exits are `StopKind.ATR` with `stop_mult` 1.0 or 1.5
`[repo-verified: workspace/newstrats/run_geometry.py:53-63]`, so the stop the *signal* proposed sits
`stop_mult × atr(signal bar)` away, which ALGO-1 recovers exactly. The **realised** risk distance
`|entry − stop|` differs, because the fill gaps and slips away from the signal bar and the engine
honours the original stop level rather than re-deriving it
`[repo-verified: futures_agents/backtest/engine.py:354-361]`; it is not in the dump, and BT3 had to
re-run the generating study to get it `[repo-verified: backtest/BT3/ALGOS.md:204-216]`. Every
distance number here is labelled `modelled`. I deliberately did **not** stratify on `mae`: it is
realised adverse excursion in R, so conditioning on it conditions on the outcome and would produce
a large tautological "effect".

---

## Assertions

`[measured: python3 workspace/roundtable/backtest/BT5/code/checks.py → "all checks passed"]`

| check | result |
|---|---|
| `check_join_is_total` | joined **21,954 / 21,954**, unjoined 0 |
| `check_signal_bar_precedes_entry_by_one_timeframe` | 4,000 sampled trades: signal bar is the immediately preceding bar; 114 sit across a calendar gap wider than one timeframe |
| `check_no_lookahead_in_stratifiers` | 833 bars: `volume`, `rel_volume` and `atr` unchanged by truncating the cell in half |
| `check_indicators_match_the_frame_the_study_used` | 1,626 bars of MCL 60m S1: `atr` and `rel_volume` identical to `build_symbol_frame`'s columns |
| `check_strata_are_count_balanced` | worst per-cell stratum share deviation from ⅓: **0.0088** |
| `check_todrank_is_time_of_day_neutral` | time-of-day TV distance HIGH vs LOW: **RAW 0.734, TODRANK 0.019** |
| `check_fast_path_matches_reference` | `_Compact.stats()` == reference `per_strategy` on all three axes |
| `check_permutation_preserves_block_composition` | 371 blocks: label multisets identical after 5 draws; 16,533 bar labels moved |
| `check_determinism` | 40 draws twice at seed 11: identical p |
| `check_r_is_not_recomputed` | 21,954 R values identical to the dump's; dump carries no price, distance or dollar field |

**Join coverage, reported rather than assumed** (R5's caveat 3). R5 expected a loss because the
dump's earliest `ts` (2025-10-17T04:00−04:00) precedes `csv/raw/MGC_1h.csv`'s first bar
(2025-11-05T04:00Z). It does not cost a single row: that earliest trade is **MCL**, and
`csv/raw/MCL_1h.csv` starts 2025-10-14T08:00Z
`[measured: sed -n 2p csv/raw/MCL_1h.csv]`. Because every cell is rebuilt through the study's own
slicing code, the join is exact by construction, and the timezone trap `BRIEF.md` records cannot
bite: the comparison is between `datetime` objects, which compare by instant, never between
offset-stripped strings.

