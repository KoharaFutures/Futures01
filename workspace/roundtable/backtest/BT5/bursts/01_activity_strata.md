# BT5 burst 01 — R5_SCOPE §S2, activity stratification on the wall-clock grid

**Question:** does `MAIN-01`'s named mechanism — per-bar statistics weighting unequal-activity bars
equally — leave a footprint on the wall-clock grid this repository already has, and does that
footprint survive removing the time-of-day component?

**Stopping point declared before starting:** one algorithm, one fidelity question to R5, no second
algorithm. No constructed bars, no sweep, no engine run, no new strategies.

**Substrate:** `csv/raw` only, reached through `workspace/strategy_research/scratch/geo_trades.json`
(read, never written). Nothing from `data/archive/`.

---

## What I read first

`PIPELINE.md` (§4 in full), `workspace/roundtable/OWNERSHIP.md`, `BRIEF.md`, `REGISTRY.md`,
`research/R5_SCOPE.md` (§S2 in full, plus §2.1–2.5, §4, §5, §6.2, §7), `backtest/BT3/ALGOS.md`,
`backtest/BT3/bursts/`, `manager/BOARD.md` §`MAIN-01`.

Two things from that reading changed the work before any code was written:

1. **`MAIN-01` is already closed** `CLOSED-EMPTY / SUBSTRATE-1M` (ADJ-16c), no `MAIN-01/S<n>` section
   exists and none ever will `[repo-verified: manager/BOARD.md:61]`. So this is cited as
   `R5_SCOPE §S2`, never as a section id.
2. **`BOARD.md` re-filed S2 under `MGR-T13`, held by R1** `[repo-verified: manager/BOARD.md:78-82,
   :390]`, and lists BT5's recommended task as `MGR-T22` (verify `D51`) `[:191, :400]`. My dispatch
   assigned me S2 directly. I did the work as dispatched and flagged the overlap to R5 and to the
   manager rather than silently duplicating R1.

## What I did

Coded **`BT5-ALGO-1`** — full design and every silent choice in `ALGOS.md`. In outline:

- **The join.** Rebuilt the generating study's 24 cells through its own code path
  (`toolkit.disjoint_slices` / `slice_series`, which is what `run_geometry.py:149-152` calls),
  computed the per-bar statistics `MAIN-01` names with the library's own functions at
  `features.py`'s own parameters, and attached them to every stored trade at the **signal** bar —
  the bar one timeframe before the dump's `ts`, because `entry_ts` is the *fill* bar
  `[repo-verified: futures_agents/backtest/engine.py:290-295, :372]`.
- **Three stratifier axes.** `RAW` (signal-bar volume, the pre-answered form), `RELVOL` (the
  library's own `relative_volume(bars, 20)`, i.e. the trailing-20-session same-clock-bucket norm),
  `TODRANK` (percentile rank within the bar's own ET clock bucket — stricter, and time-of-day-neutral
  by construction).
- **Two layers.** Bar-level (do the statistics differ across strata) and per-strategy (does
  expectancy / win rate / payoff differ), with the pooled per-trade figure computed and labelled a
  diagnostic of pooling, never a result.
- **One null that is also the placebo.** Bar-level stratum-label permutation blocked within
  (cell, ET clock bucket), 2,000 draws, seed 20260927.

## Coverage, reported rather than assumed

`[measured: python3 code/activity.py]`

```
trades 21954   joined 21954   no_such_cell 0   ts_not_a_bar 0   entry_is_first_bar 0
signal_relvol_none 67   signal_atr_none 0   signal_vol_zero 593   entry_vol_zero 472
cells 24   bars 25316   strategies 176
```

R5's caveat 3 expected a join loss because the dump's earliest `ts` (2025-10-17T04:00−04:00) precedes
`csv/raw/MGC_1h.csv`'s first bar (2025-11-05T04:00Z). **It costs zero rows**: that earliest trade is
**MCL**, and `csv/raw/MCL_1h.csv` starts 2025-10-14T08:00Z
`[measured: sed -n 2p csv/raw/MCL_1h.csv]`. The join is exact by construction because the cells are
rebuilt through the study's own slicing code, and 176 strategies independently reproduces BT3's count.

## Ten assertions, all passing

`[measured: python3 code/checks.py → "all checks passed"]` — table in `ALGOS.md`. The two that
carry the most weight:

- `check_indicators_match_the_frame_the_study_used`: `atr` and `rel_volume` are **identical, element
  by element, to `build_symbol_frame`'s columns** over all 1,626 bars of MCL 60m S1. Recomputing
  instead of reading the frame is a shortcut and this is what makes it a safe one.
- `check_todrank_is_time_of_day_neutral`: time-of-day total-variation distance between the HIGH and
  LOW strata is **0.734 for RAW and 0.019 for TODRANK**. Without this assertion a "residualised"
  answer could quietly be the raw answer wearing a different name.

## One defect in my own first implementation, found and fixed before asking R5

The permutation statistic is a **median across qualifying strategies**, and "qualifying" was being
recomputed on every draw. Measured: on the `RAW` axis **116** strategies clear `min_n = 10` on the
observed labels and **~134** clear it on a permuted draw — because the real strata are correlated with
*which* strategies trade (high-activity bars are RTH bars, and some arms trade mostly overnight). A
null whose statistic is a median over a different, larger set of strategies **is not the same
statistic**, so the p was not a permutation p.

Fixed: the pool is now fixed to the strategies qualifying on the **observed** labels, and the
unpooled count is retained as a diagnostic. This is the same shape of mistake BT3 recorded in its
`barrier=False` restructuring — a fix that quietly changed what the control was — and it is worth
recording that it was caught by printing the count rather than by review.

## What I asked, and where I stopped

`msgs/BT5-01_R5_verify-ALGO-1.md`, seven questions. Three I think I could genuinely be wrong on:

- **Q1** — S2 says activity "at entry"; I stratify the **signal** bar, which is a different bar.
- **Q4** — I added a **bar-level** layer S2's "Answers" paragraph does not name. It is adjacent to
  S3 ("do the statistics differ between the two *clocks*") and I would rather be told I widened the
  sub-task than have it pass silently.
- **Q7** — caveat 6 says "count-match the strata"; I match on **bars** (equal-count terciles per
  cell) and let the permutation handle the trade-level imbalance inside each strategy, rather than
  subsampling.

**Stopped here.** Results are in `ALGOS.md` under "Result", marked `ASKED`. No second algorithm.

## What I deliberately did not measure, and why it bounds the conclusion

**Whether the bar-level footprint is a *within-day* or a *between-day* effect.** `TODRANK`
residualises on time of day but not on the trading day, so a stratum contrast could be "busy days are
volatile days" rather than "busy bars are volatile bars". Both are inside `MAIN-01`'s mechanism — a
volume clock equalises activity across days *and* within them — so neither reading overturns the
result. But they are different statements and I measured only their sum. A fourth axis would have
entered the search denominator for a question S2 did not ask, so it is recorded as a bound rather
than run.

**The `mins == 0` sub-population separately.** 2,900 rows are same-bar exits with mean R −0.79
`[repo-verified: backtest/BT3/ALGOS.md:166-170]`. They are kept in (dropping them would be a filter
on the outcome) but not analysed as their own stratum. They are the group most likely to be
activity-sensitive, so that is a live thread and not a finished one.
