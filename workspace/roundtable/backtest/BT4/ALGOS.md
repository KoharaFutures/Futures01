# BT4 — algorithms

Ids per `REGISTRY.md`: `BT4-ALGO-<n>`, my own prefix. One entry per algorithm, appended as I go.

---

## BT4-ALGO-1 the daily-frame reduction

- **Implements:** `R4-M3` from `research/R4_group_audit.md:212-297`, with `R4-MT2`
  (`:1028-1057`), `R4-MT4` (`:1086-1134`) and `R4-REQ-1` as the supporting statements.
- **Code:**
  - `backtest/BT4/code/daily_mtf_reduction.py` — the reduction and its 240m control
  - `backtest/BT4/code/regime_lag_at_1440.py` — the second channel, `regime_tf = 7200`
  - `backtest/BT4/code/rule2_leave_1440_out.py` — rule 2's evidence, re-aggregated
  - `backtest/BT4/code/stores_at_1440.py` — the per-store census
  - `tests/test_bt4_align_bucket.py` — 17 regression checks in the repo suite
- **Fidelity:** **ASKED** — `msgs/BT4-01_R4_verify-ALGO-1.md`, five questions in `VERIFY.md`.
  **No number below is verified.**

### My reading of the finding

R4-M3 says three things, and I read them as separable:

1. `align_bucket` takes its `minutes >= 1440` branch for every coarser request, so every timeframe
   above a day is the same bucketing. `[repo-verified: futures_agents/data/bars.py:138-156]`
2. Consequently `FRAMES[1440] = [1440, 7200]` holds the daily series twice, OHLCV bit-identical,
   with the second copy lagged 2–4 bars because `end_ts = ts + 7200 min` on a one-session bar.
   `[repo-verified: futures_agents/scout.py:58-67, features.py:828-847, data/bars.py:50-52]`
3. Therefore *"every daily multi-timeframe statement in this repository is a lagged-autocorrelation
   test on one series."*

(1) and (2) are mechanical and I reproduce both. (3) is the interesting one and it is stated as a
consequence rather than measured, so this algorithm is built to test (3) as a falsifiable claim:
**if the three conditions can be reproduced exactly from one series and one lag, (3) holds; if they
cannot, R4 has overstated it.**

### Where I had to choose

Every silent point in the finding, and what I decided:

| the finding was silent on | I chose | why, and what it would change |
|---|---|---|
| **what counts as "a daily MTF result"** | a stored row whose **primary timeframe is 1440**. Not a row whose frame merely contains 1440 | a 60m row runs `[60, 240, 1440]`, and that 1440 member is a **genuine** daily series — the collapse needs a request *strictly above* 1440. Counting 60m rows would multiply the blast radius ~30× and would be wrong |
| **whether 240m is affected** | **no.** `[240, 1440]` is degenerate under `D17`/`R4-MT2` (two voters) but its confirming series is real | merging the two defects is the single easiest way to over-retract here. R6's audit found 62% of published claims survive; I am not adding to the retraction pile on a conflation |
| **how to treat the 2–4 bar lag** | as **content**, and as the reduction's only free parameter | the alternative — calling the lag noise and the two series "identical" — would predict `mtf_aligned` fires on 100% of directional bars. It does not: it fires on 45.9% (MGC). The lag is what the condition is actually reading |
| **whether the reduction may read the 7200 series** | **no** for the load-bearing leg. The confirm pointer is rebuilt from the daily bars and the calendar alone | reading `frame._align[7200]` makes the reduction circular: of course a vector derived from the second series reproduces a condition computed from the second series. Both legs are reported; the non-circular one is the claim |
| **what a control looks like for a structural claim** | the same reduction at 240m, fitted over 25 candidate lags and reported at its **best** | a reduction that succeeds everywhere proves nothing about 1440m. Giving the control 25 tries and having it still fail is the statement that the method has teeth |
| **which statistic to re-aggregate for rule 2** | the study's own per-cell `z`, Stouffer, equal weights — **reproduced first** (−4.0931 vs published −4.093) before any cell was dropped | if I could not reproduce the published combination I would not know what was combined, and no leave-out number would mean anything |
| **whether to run a new comparative test** | **no.** Re-aggregation only | `D28` — a fresh rank sum over strategies within a cell inflates \|z\| ~3.3×, and `T.ab` is explicitly barred |
| **whether the regime channel is in scope** | **yes**, and it is the part R4 flagged but did not size | `R4-M3`'s own table records `regime_tf = 7200` at the daily row. That channel reaches every 1440m strategy through `volatility_normal`, a base filter on 12 of 13 templates — a much larger population than MULTI_TIMEFRAME's |
| **which store to measure on** | `csv/raw/` only, read-only | every published 1440m result was measured there, and `MCL_1d.csv` does not exist so MCL is absent by construction, not by choice |

### 1 — the mechanism, re-verified

`[measured: PYTHONPATH=. python3 workspace/roundtable/backtest/BT4/code/daily_mtf_reduction.py]`

| check | MGC | MNQ | MES |
|---|---|---|---|
| daily bars / span | 2,511 (2016-09-26..2026-09-21) | 1,859 (2019-05-03..) | 1,859 (2019-05-03..) |
| distinct bucketings over `minutes ∈ {1440, 2880, 4320, 7200, 10080, 43200, 525600}` | **1** | **1** | **1** |
| bars per "7200m" bucket | `{1: 2511}` | `{1: 1859}` | `{1: 1859}` |
| `resample(daily, 7200)` **OHLCV** vs daily, in order | **2510/2510** | **1858/1858** | **1858/1858** |
| …its **`ts`** vs daily | **0/2510** | **0/1858** | **0/1858** |
| `Bar.minutes` on the copy | 7200 | 7200 | 7200 |
| pointer lag `idx(1440) − idx(7200)` | 1:71, 2:972, 3:546, 4:922 | 1:52, 2:720, 3:402, 4:685 | 1:52, 2:720, 3:402, 4:685 |
| primary pointer is the identity | 2511/2511 | 1859/1859 | 1859/1859 |

Two refinements on R4's table, both small and both worth recording:

- **R4 reported the OHLCV identity; the `ts` is *not* identical, and that is the causal link.**
  `resample` stamps the copy at `align_bucket(ts, 7200)` = the CME trading-day start (18:00 the
  previous evening), so `end_ts = ts + 7200 min` lands five days past a bar that covers one session.
  The lag is not a side effect of the collapse — it is the collapse plus the honest `end_ts`
  arithmetic in `Bar.end_ts` doing exactly what it is told.
- **The pointer lag counts are 71/972/546/922 for MGC, against R4's 70/971/545/921.** One bar each.
  R4's table excludes the 4 bars with no "7200" bar yet; mine includes them in the base and reports
  them under lag 1. Not a disagreement, a different denominator — R4's is the cleaner statement.

### 2 — what a daily MTF condition reduces to

With exactly two voters at 1440 and 7200, weights `log(1441) = 7.2731` and `log(7201) = 8.8820`
`[repo-verified: features.py:745-750]`, the arithmetic in `library.py:780-841` collapses to a table:

| the two trend labels | `agreeing_timeframes` | `alignment` | `mtf_aligned` | `mtf_strongly_aligned` | `mtf_not_conflicted` |
|---|---|---|---|---|---|
| both directional, **equal** | `(2, 2)` | `±1.0` | **fires** | **fires** | passes |
| both directional, **opposed** | `(1, 2)` | `±0.0996` | no (< 0.4) | no (`agree ≠ voting`) | **vetoes** |
| one directional | `(1, 1)` | — | no (`voting < 2`) | no | passes |
| neither directional | `(0, 0)` | — | no | no | passes |

So at 1440m — where the second label **is** the first label 2–4 sessions ago:

> `mtf_aligned` = `mtf_strongly_aligned` = **"the daily structure trend is directional now and was
> the same direction 2–4 sessions ago."**
> `mtf_not_conflicted` = **"the daily structure trend did not flip UP↔DOWN across those 2–4
> sessions."**

Neither reads a second observation of the market. Measured, against a reference that reads the
daily series and the calendar and nothing else:

| | MGC | MNQ | MES |
|---|---|---|---|
| confirm pointer rebuilt from daily + clock alone | **2511/2511** | **1859/1859** | **1859/1859** |
| confirm snapshot == an earlier value of the primary's own snapshot | 2507/2507 | 1857/1857 | 1857/1857 |
| **`mtf_aligned` reproduced, no second series read** | **2511/2511** | **1859/1859** | **1859/1859** |
| **`mtf_strongly_aligned` reproduced** | **2511/2511** | **1859/1859** | **1859/1859** |
| **`mtf_not_conflicted` reproduced** | **2511/2511** | **1859/1859** | **1859/1859** |
| `mtf_aligned` ≡ `mtf_strongly_aligned` per bar | 2511/2511 | 1859/1859 | 1859/1859 |
| `mtf_aligned` fires | 1,153 (45.9%) | 908 (48.8%) | 976 (52.5%) |
| `mtf_not_conflicted` passes | **99.12%** | **99.30%** | **99.62%** |

**R4-M3 (3) holds, exactly.** The three conditions carry zero cross-timeframe information at 1440m —
not "little", zero: every bar of every symbol is reproduced by a function of one series and one lag.

**Why `mtf_not_conflicted` passes 99%+, demonstrated rather than asserted.** It vetoes only on an
UP↔DOWN flip. `structure_trend` has a `RANGE` state between them
`[repo-verified: features.py:640-651]`, and a daily trend label reaching the opposite pole inside
2–4 sessions without passing through `RANGE` is close to impossible. The lag sweep shows it is the
*shortness* of the lag doing the work, against a count-matched label shuffle as the control:

| lag (sessions) | MGC not-conflicted | shuffled control | MGC aligned | shuffled control |
|---|---|---|---|---|
| 1 | 100.00% | 82.47% | 54.86% | 17.81% |
| **2** | **99.92%** | 82.90% | 50.26% | 18.45% |
| **3** | **99.44%** | 82.38% | 45.85% | 18.34% |
| **4** | **98.56%** | 82.17% | 41.68% | 17.63% |
| 5 | 97.45% | 81.96% | 38.11% | 17.56% |
| 10 | 90.28% | 83.61% | 25.91% | 17.75% |
| 20 | 83.54% | 82.62% | 19.03% | 17.86% |
| 60 | 82.54% | 82.42% | 17.46% | 18.44% |

The real arm converges on the shuffled arm by lag 20 and is indistinguishable by lag 60. **The 99%
pass rate is the autocorrelation of the label at a 2–4 bar lag, and nothing else.** A genuine weekly
series would sit somewhere around the lag-5-to-10 rows, i.e. would veto 3–10% of bars rather than
0.9% — but that is an interpolation from this table, not a measurement, and it is the gap named
below.

MNQ and MES reproduce the shape (2-session not-conflicted 100.00% / 99.89%, lag-60 83.55% / 84.21%).
MES and MNQ are one index complex, so that is not corroboration.

### 3 — the control, which is what makes the reduction a claim

Same reduction at MGC 240m, frame `[240, 1440]`, where 1440 is a genuine daily series. Given 25
candidate lags on the primary and reported at its best:

| | 1440m (treatment) | 240m (control) |
|---|---|---|
| primary trend == confirm trend | n/a (2–4 bar lag by construction) | 1505/5000 = 30.1% |
| best `mtf_aligned` reduction | **2511/2511 = 100%**, no fitting | **3441/5000 = 68.8%** at its best of 25 lags |
| best `mtf_strongly_aligned` | **100%** | 68.8% |
| best `mtf_not_conflicted` | **100%** | 82.1% at its best of 25 lags |

A reduction fitted over 25 lags that still misses 31% of bars is a reduction that failed. The method
is not vacuous, and the collapse is specific to `FRAMES[1440]`.

**Search size, per PIPELINE §4(2):** the treatment fits **nothing** — the reduction has no free
parameter once the pointer is reconstructed, so there is no multiplicity to deflate. The control
searched **25** lags × 3 conditions = 75 fits, all of which failed; a search that fails needs no
deflation either. No expectancy, Sharpe or t-statistic is produced anywhere in ALGO-1.

### 4 — how many stored results ran on a 1440m frame

Every harness resolves `FRAMES[tf]` and then keeps `primary_tf == tf`
`[repo-verified: workspace/studies/toolkit.py:157-161, workspace/bigscan/cell.py:86-90,
workspace/chrono/ledger.py:28+36-40]`, so a primary of 1440 implies the frame `[1440, 7200]`.

`[measured: PYTHONPATH=. python3 workspace/roundtable/backtest/BT4/code/stores_at_1440.py]`
and `[measured: … code/tf1440_census.py]` as the blind cross-check.

| store | native unit | at 1440m | of |
|---|---|---|---|
| **`workspace/chrono/ledgers/`** | strategies / trades / month-buckets | **23,309 strategies, 130,070 trades, 295 month-buckets** (MGC 7,875/56,670/117; MES 7,697/34,027/89; MNQ 7,737/39,373/89) | **3 of the 6 ledgers.** The whole chronology study's long-span arm |
| `workspace/bigscan/all_rows.json` | floored strategy rows | 94 (1.9%) | 4,957; **20 of 108 cell files** (MES/MGC/MNQ/QQQ/SPY × 30/90/180/274d) |
| `workspace/focus/all_rows.json` | floored strategy rows | 95 (2.7%) | 3,564; **4 of 39 cell files** (MES/MGC × 180/274d) |
| `workspace/studies/out/g_multi_timeframe.json` | floored rows in the study's cells | **569 (31.3%)** | 1,818; **3 of 23 cells** |
| `g_liquidity`, `g_momentum`, `g_opening_range`, `g_trend`, `g_vwap` | study cells | **3 of 23 cells each** | the same MGC/MES/MNQ 1440 cells. **6 of the 21 studies** carry a 1440m cell |
| `workspace/studies/out/x_robustness.json` | disjoint-period cells | **MGC daily and MNQ daily** | 24 cells — **and these are the two cells the study singles out as positive** |
| `workspace/studies/out/x_session.json` | toggle cells | `MES_1440_274`, `MGC_1440_274` | 10 toggle cells |
| `rank_persistence{,_realised,_disjoint,_nested,_mixed_league}` | cells | 3 each (`MGC/MES/MNQ_1440`) | 13–59 cells |
| `workspace/studies/out/ict_sweep_mss_census.json` | census rows | 45 (10.3%) | 435 |
| `scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md` | published cells | 4 (`MES_1440m_{274,180}d`, `MGC_1440m_{274,180}d`) | 31 cells in its inventory |
| `csv/raw/MCL_1d.csv` | — | **absent** | so every 1440m row here is MGC, MES, MNQ, QQQ or SPY, and MES/MNQ/QQQ/SPY are one index complex |

**The biggest by far is the chronology study**, and it is the one whose *entire long-span arm* is
1440m: the 117/89/89-month depth that made a transition matrix possible at all exists only on the
daily files. Its published conclusion is **negative** ("no chronological chaining of strategy groups
exists, on any symbol" — `BRIEF.md`), and an inert confirming timeframe cannot manufacture a
negative. That verdict is not threatened. What is now unavailable is the reading that the daily arm
was a *multi-timeframe* test of chaining.

**The one place a positive claim sits on a collapsed frame.** `x_robustness`'s headline is
*"the one cell that beats chance is **MNQ daily** (9 of 53 rule-set families vs 2.7 expected,
z = +4.56, p < 0.0005)"*, and its first caveat is *"**MGC daily** is the one cell whose walk-forward
returns `is_credible=True`"* `[repo-verified: workspace/studies/out/x_robustness.json headline +
caveats]`. Both are 1440m cells. Neither is reached through `multitimeframe` — all 9 MNQ-daily
families are MOMENTUM or VWAP — but **all 9 carry `volatility_normal` as a filter**, which is §5's
channel. The study already discounted both cells on its own grounds (pooled `t = 1.99` against
`free_t = 4.23`; the `is_credible` result collapses if one 21-trade fold is removed), so this adds a
reason and overturns nothing.

### 5 — the channel R4 flagged and nobody sized: `regime_tf = 7200`

`_default_regime_tf`'s preference list `(15, 30, 5, 60, 10, 3, 1)` misses both members of
`[1440, 7200]` and falls through to `return self.timeframes[-1]`
`[repo-verified: features.py:820-826]`, so at the daily frame the regime is read off **the lagged
copy**. `regime_at` slices `frames[regime_tf].series.bars[:ri+1][-400:]`
`[repo-verified: features.py:928-943]`, and those bars are the daily bars, so the regime a daily
strategy sees is its own daily regime 2–4 sessions stale.

This reaches **every 1440m strategy**, because `volatility_normal` is a base filter on 12 of 13
templates and `regime_trending`/`regime_ranging` are TREND's and MEAN_REVERSION's.

`[measured: PYTHONPATH=. python3 workspace/roundtable/backtest/BT4/code/regime_lag_at_1440.py —
shipped frame vs the same frame with `regime_timeframe=1440`]`

| | MGC | MNQ | MES |
|---|---|---|---|
| `regime` label differs | 509/2511 = **20.27%** | 336/1859 = **18.07%** | 325/1859 = **17.48%** |
| `volatility` label differs | 655/2511 = 26.09% | 364/1859 = 19.58% | 424/1859 = 22.81% |
| **`volatility_normal` pass/veto flips** | 257/2511 = **10.23%** | 193/1859 = **10.38%** | 178/1859 = **9.58%** |
| `regime_trending` flips | 284 = 11.31% | 149 = 8.02% | 134 = 7.21% |
| `regime_ranging` flips | 466 = 18.56% | 325 = 17.48% | 321 = 17.27% |
| `volatility_normal` **pass rate**, shipped vs on-timeframe | 82.72% vs 82.36% | 78.86% vs 78.48% | 78.59% vs 78.16% |

**The shape of the damage is a timing error, not a distribution error**, and that distinction is the
useful part: the aggregate pass rate moves by 0.36–0.43 points, so nothing in the *marginal*
behaviour of these filters looks wrong, while the per-bar decision is different on one bar in ten
(`volatility_normal`) to one in five (`regime_ranging`). A study that checked pass rates would have
seen nothing. That is why this survived.

The comparison arm here is the **on-timeframe daily** regime, which is *not* the same thing as the
correct answer — see the gap below.

### 6 — how much of `BRIEF.md` rule 2 is affected, and how much survives

**This section answers a pre-registration, which is the strongest form available here.** `ADJ-14` §5
(`manager/ADJUDICATIONS.md:1437-1452`, ruled 2026-09-27 04:05 ET, before I measured) says:

> **BT4 owes two numbers as part of `D50`'s blast radius:** the count of `primary_tf = 1440` rows
> inside the 366-strategy and 1,151-strategy populations behind z = −4.09, and **the same z
> recomputed with those rows excluded.**
> — If z survives exclusion, narrowing (a) **costs nothing** and rule 2's first sentence is restored
> to its full published scope with a footnote.
> — If z does not survive, rule 2's first sentence is a **60m/240m result** and must say so.

**Both numbers are below. The verdict is: z survives. 249/366 and 320/1,151; −4.093 → −3.053.**
By `ADJ-14`'s own decision rule, **narrowing (a) costs nothing** — same sign, same order of
magnitude, on 11 cells that cannot be `D50` casualties. Rule 2's first sentence is a real result on
the frames that could disagree, and the footnote is the population share.

**One reading I had to fix before answering.** "The same z recomputed with those rows excluded" has a
trap: the published −4.09 is **not** a pooled statistic, it is a Stouffer combination over cells, so
re-pooling the surviving rows through a fresh rank sum would be a *new* comparative test and would hit
`D28` head-on. I recompute the **published combination** on the surviving cells instead. That is
exact rather than approximate here, because a cell is `(symbol, tf, window, confirm_tfs)` and every
`primary_tf = 1440` row therefore lives inside one of the three daily cells and nowhere else —
**excluding the rows and excluding the cells are the same operation.**

`[measured: PYTHONPATH=. python3 workspace/roundtable/backtest/BT4/code/rule2_leave_1440_out.py]`

Rule 2 has three sentences and they fare differently. All of the evidence is one artefact,
`workspace/studies/out/g_multi_timeframe.json`, published as
`scan_reports/2026-09-24_strategy-studies_21-study-programme.md:85`.

**Sentence 1 — "requiring any alignment measured detectably worse than requiring none (z = −4.09)".**
Source: `findings.ab_any_mtf_condition_vs_none`, 23 cells of which 14 compared and 9 skipped for a
thin arm. **3 of the 14 are 1440m.** Published Stouffer reproduces exactly (−4.0931 vs −4.093).

| subset | k | Stouffer z | cells negative | sign-test p |
|---|---|---|---|---|
| all 14 (published) | 14 | **−4.0931** | 9/14 | 0.424 |
| **1440m cells removed** | 11 | **−3.0531** | 7/11 | 0.549 |
| the 3 1440m cells alone | 3 | −2.9959 | 2/3 | 1.000 |

The three daily cells: MES −2.862, **MGC +1.516**, MNQ −3.843.

**Verdict: the sign survives; the magnitude drops 25.4%; the population share is the real story.**

| arm | all 14 | of which 1440m | share |
|---|---|---|---|
| has an mtf signal (the treatment) | 366 | **249** | **68.0%** |
| no mtf signal (the control) | 1,151 | 320 | 27.8% |

So the headline's "366 vs 1,151" is a **mixture comparison**: two thirds of the strategies that
"required alignment" required it on a frame that confirms against itself, against a control arm only
a quarter of which sat there. The pooled medians (−0.0218R vs +0.0228R) are therefore partly a
frame-composition difference, and the per-cell Stouffer — which cannot mix frames — is the figure to
quote.

**Three reasons not to retract more than that**, because over-retracting is the other failure:

1. **The daily cells are not where the sign comes from.** MGC's daily cell is *positive* (+1.516), so
   dropping it *strengthens* the finding to −4.668. Leave-one-out over all 14: dropping `MGC/60/180`
   gives −5.188 and dropping `MNQ/15/58` gives −5.223, both larger than any 1440m drop. No cell
   dominates, and the 1440m cells are not the load-bearing ones.
2. **11 uncontaminated cells still combine to −3.05** on five symbols and four timeframes.
3. **A degenerate treatment arm biases this finding toward the null, not toward the result.** At
   1440m the "alignment" requirement is a lagged self-agreement filter — a weaker constraint than
   genuine alignment, and one that passes on 46–53% of bars. If cross-timeframe agreement helped,
   including cells where it was not tested would *dilute* a positive, and the measured direction is
   negative anyway.

**What is *not* recoverable is the interpretation.** With 68% of the treatment arm on a collapsed
frame, "requiring multi-timeframe alignment" is not what 68% of that arm required. Rule 2's first
sentence should read as **"requiring this library's alignment conditions measured worse than
requiring none (z = −3.05 on 11 cells where the frame could disagree; −4.09 on all 14)"**, which is
weaker than a statement about multi-timeframe agreement as a practice.

`ADJ-14` §4 already restated rule 2 as *"measured worse than requiring none on the **60-minute frames
the corpus built** (z = −4.09, 366 vs 1,151)"*. That is very nearly right and slightly
**over**-narrow. The 11 surviving cells are **8 at 60m, 2 at 15m, 1 at 30m**, across **five symbols**
(MCL, MES, MGC, MNQ, NQ); no 5m or 240m cell reached the comparison, all of those were skipped for a
thin arm. So "60-minute" understates it by three cells and two timeframes. The exact qualifier is
*"on the frames whose members are distinct series"*. That correction runs **against** my own
direction of travel — it makes rule 2 broader, not narrower — and it belongs in the record as such.

**Sentence 2 — "on a two-timeframe frame, 'majority' and 'unanimous' are the same statement (D17)".**
The payload has the comparison in two arms, and the author already knew:
`ab_unanimous_vs_majority_2tf_frames_**DEGENERATE**` — **all 3 of its cells are 1440m**, z = +0.241.
My own measurement is the strongest available form of it: `mtf_aligned` and `mtf_strongly_aligned`
are the **same function** at 1440m on 2511/2511, 1859/1859, 1859/1859 bars. That sub-finding measured
literally nothing, which is exactly what its key says. **Unaffected as a claim — it is the claim.**
The surviving evidence for "unanimity vs majority" is the 3-timeframe arm, 5 cells, z = +1.84, with
**zero** 1440m cells — and `R4-MT3` says even there "unanimous" ignores abstentions on 65–88% of its
firings.

**Sentence 3 — "`mtf_aligned` is the strongest negative condition in the library (z = −2.53)".**
Different artefact: `workspace/studies/out/x_conditions.json`, `findings.ranked_table[33]`, summarised
at `workspace/studies/DEFECTS.md:210`. Its own row reads
`z_within_group = -2.528`, `cells = 7`, `cells_agreeing = 5`, **`survives_BH = false`**, and its
`fire_rate_by_cell` names `MES_1440` among the five cells it recorded
`[repo-verified: workspace/studies/out/x_conditions.json → findings.ranked_table[33]]`. So **at least
1 of 7 cells is 1440m**, and the sentence was already the weakest of the three: it is a claim about
*rank order* among negatives, and its own study says no negative condition survives
Benjamini-Hochberg. Affected, not decisively — I cannot recover the per-cell z values from this
payload to do the leave-out arithmetic, which is the one place in this section where I could not.

**A fourth claim in the same payload, outside rule 2 but travelling with it.** "The MULTI_TIMEFRAME
group is detectably worse than the rest of the population (z = −3.55 over 11 cells)"
`[repo-verified: workspace/studies/DEFECTS.md:271]`. **3 of 11 cells are 1440m and 67.2% of the
group's floored rows (158/235) are.** Removing them: **−3.545 → −2.585.** Same shape as sentence 1:
sign survives, magnitude down 27%, population share the real issue.

**The caveat that applies to every z on this page, mine included.** The per-cell `z` is a rank sum
over *strategies within a cell*, and the rows carry a `clones` column, so correlated variants are
being treated as independent observations. **`D28` measured that as inflating |z| ~3.3×.** So
−4.09, −3.05, −3.55 and −2.59 are all inflated by an unknown factor. The **ratio** between them is
what this section is for; the absolute levels are not trustworthy, and the sign test across cells —
which does not depend on the within-cell unit — **is not significant either way, before or after**
(p = 0.424 → 0.549).

### Does R4's mechanism hold everywhere, or only in `FRAMES[1440]`?

It is a defect in `align_bucket` and therefore **everywhere a request above 1440 is made**. Where
those requests are:

| site | request above 1440? | reached? |
|---|---|---|
| `futures_agents/scout.py:67` `FRAMES[1440] = [1440, 7200]` | **yes, 7200** | **yes** — the shipped daily frame, and the only production path |
| `FRAMES[5/15/30/60/240]` | no (max member 1440) | the 1440 member is a **genuine** daily series. Unaffected |
| `align_bucket` itself for 2880/4320/10080/43200/525600 | all collapse | **unreached** — no call site requests any of them `[measured: grep -rn "10080\|43200\|525600" --include=*.py . → 0 hits; grep -rn "7200" → exactly 2 live sites, scout.py:66 and chrono/ledger.py:28, both the same map]` |
| `workspace/chrono/ledger.py:28` `{1440: [1440, 7200]}` | **yes** | **yes** — its own copy of the map, same values |
| `data/archive/` daily series | n/a — no resample above 1440 in the archive path | not reached |

So: **the mechanism is general, the exposure is `FRAMES[1440]` only, and that single frame is the
daily arm of six of the twenty-one studies, three of six chronology ledgers, 24 bigscan/focus cell
files and four published cells.** `scout.py:65-66` even documents the intent — *"7200 minutes is
five sessions"* — which makes this a case of the comment being right and the code never having been
checked against it.

### The gap I did not close

The comparison arm in §5 is the **on-timeframe daily** regime. The correct counterfactual is a
**genuine weekly** regime, which cannot be built through `resample` while the collapse stands. So §5
bounds the size of the discrepancy and does **not** sign the error: I can say the label is different
on one bar in five, not which one was right. The same limitation applies to §2's lag table — the
lag-5-to-10 rows are where a real weekly vote would plausibly sit, and that is an interpolation.
Closing it means constructing a weekly series outside `resample` and re-running both, which is the
next burst if the board wants it.
