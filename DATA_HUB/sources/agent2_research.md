# Agent 2 sweep: research findings, consolidated per symbol

**Lane:** `research/`, `scan_reports/`, `workspace/{newstrats,strategy_research,chrono,bigscan,studies}/`,
`docs/`, `desk/`, `scripts/`, `packaging/`, `README.md`, `futures_agents/{strategies,scanners}/` (read only).
**Swept:** 2026-09-29, branch `claude/admiring-heisenberg-doycyh`. Nothing moved, deleted or committed.
**Companion:** `DATA_HUB/_sweep/agent2_manifest.tsv` (KEEP/ARCHIVE decision for every path in the lane).

---

## 0. Bottom line, before any table

- **Nothing in this lane clears its deflated threshold, on any symbol.** Programme-wide:
  >= 2,975,629 candidates generated -> `free_t = sqrt(2 ln n) = 5.46`. Largest t anywhere: **3.923**
  (NQ 60m, 180d). Largest t on the clean independent contracts (MGC/MCL): **3.27**. Per-cell thresholds
  are 3.3 to 4.4. Zero rows clear even their own cell's threshold.
- **Selecting is worse than not selecting** (the claim most immune to the defect classes found later):
  6-month-lookback top 10 on MGC+MCL earned **+0.022R vs +0.057R** for the whole qualifying universe
  (`rth_only=False`), **-0.024R vs +0.064R** (`rth_only=True`).
- **Span caveat.** The intraday data span is ~322 calendar days (0.88 y). `t ~= SR * sqrt(years)`, so
  clearing `free_t 5.46` needed annualised Sharpe **5.82**. Roll-clean long daily history exists only for
  MES/MNQ (7.40 y, one index complex = one independent observation).
- **19.0%** of generated strategies carry a condition that cannot fire (MGC 11.5, MCL 13.9, MES 22.6,
  MNQ 27.4%), and **60-82%** never trade at all. "N strategies tested" overstates every count below.
- **Bounce levels (the owner's style): no measured level type beats random lines once the control is
  fair.** Details in section 8.

Verdict key used below: **SURVIVED** = cleared deflation and OOS (none exist). **FAILED** = measured,
negative or indistinguishable from control. **INCONCLUSIVE** = sample too small, untestable as built,
or a positive that was never taken OOS / is below threshold but not refuted.

Data provenance keys: `raw` = `csv/raw/` real CME micro bars (~11-12 months intraday, 2025-10 to
2026-09-22; 15m/30m only 58 days, 5m 25-37 days). `deep` = `data/{MES,MGC,MNQ}_1m.csv` Oanda CFD
(NAS100/SPX500/XAU) 2019-01 -> 2020-05, 352 RTH sessions, **not futures prices**, gitignored and **absent
from this checkout** (re-fetch with `scripts/fetch_github_data.py`). `synth` = `synthetic_series` random
walk (all of `research/`): mechanical findings only, never market evidence.

---

## 1. MNQ (Micro Nasdaq)

| study / family | tf | one-line rule | n trades | exp R | win / payoff | t vs threshold | WF / OOS | placebo | verdict | source |
|---|---|---|---|---|---|---|---|---|---|---|
| ORB (240 configs, deep) | 5/15/30/60m | break of first 5-60 min RTH range, stops opp/mid/ATR, 1R-3R targets | median 310.5 per config | **-0.040** median | 40.4% / 1.377 | best 1.016 vs 3.888 | all 3 disjoint periods negative | yesterday's OR beats today's: -0.033 -> -0.020R, profitable share 18% -> 37% | FAILED | `workspace/studies/ORB_ICT_FINDINGS.md`, `workspace/strategy_research/orb_test_*.json` |
| ORB (raw csv) | 5-60m | same | median 16.5 (18-19 sessions) | -0.238 | 33.3% / 1.061 | best 0.706 | n/a | n/a | FAILED (anecdote-sized) | `orb_test_strategy_rankings.json` per_symbol_summary |
| ICT FVG reaction | 60m | 1-ATR barrier race after first touch | 32-158 per arm per cell | n/a | - | MNQ-60m IS +2.04 | **flipped negative OOS** | sham zones | FAILED | `ORB_ICT_FINDINGS.md` |
| ICT sweep->MSS->retrace (wrong-order control) | 60m | MSS then sweep (control) | ~57-68/cell | **+0.39** | - | t 2.10 vs 3.84 | - | *control* tops the durability ranking | FAILED (control wins) | `ict_sweep_mss_strategy_rankings.json` |
| Kill zones | 60m | trade only inside London/NY/Silver-Bullet hours | - | - | - | London-open range ratio 0.80, vol 0.36 | at 15m/5m filters invert sign | every-24th-bar placebo mean +2.25 | FAILED | `ORB_ICT_FINDINGS.md` |
| Top-10 ranking (worker 2, profiled) | 60m/240m | rank last 30/90/180/274d, trade top 10 | - | 30d: MOMENTUM +0.55 (n=24); 90d TREND +0.66 (n=28); 180d TREND +0.70 (n=27); 274d TREND +0.44 (n=44) | - | max 3.03 vs 4.29 | top-10 beat fold base rate in 4/16 folds (sign z -2.00) | placebos 2-9 of each top 10 | FAILED | `workspace/studies/RANKING_FINDINGS.md`, `rank_w2_*.json`, `w2/cells/` |
| MNQ 60m `rth_only=True` reals vs placebos | 60m | same ranking, RTH gate on | - | - | - | best placebo 17th of 322 (null 3.05), p=0.0015, host t +2.55 | 60/40 holdout below base rate (67% vs 72%); thirds: placebo 1st/3rd/9th | - | INCONCLUSIVE (post-hoc, 1 of 20 cells) | `RANKING_FINDINGS.md` |
| Fib golden pocket vs shallow | 240m | 0.618-0.786 vs shallow retrace entry | <20 per slice | - | - | MNQ Stouffer **-1.37** (MES +5.99) | 0 pairs reach 20 trades in any slice | rate-matched placebo | FAILED | `ORB_ICT_FINDINGS.md` |
| nested_pullback | 240/60 | HTF up, LTF down | 6,071 IS / 4,869 OOS (all sym) | - | - | MNQ +3.0 IS -> **-3.5** OOS | sign reversal | vs structure_trend@HTF | FAILED | `workspace/studies/STRUCTURE_FINDINGS.md` |
| LTF->HTF lead-lag | 60->240 | enter on 60m break before 240m confirms | - | - | - | lead 8 bars; false-positive 78-81% | - | - | FAILED (real, untradeable) | `STRUCTURE_FINDINGS.md`, `leadlag_*.json` |
| Fade extension on cash-open bar | 60m | don't fade the 09:30 bar | per-strategy | - | - | z **-7.84** (harmful) | replicates on 4 symbols | - | SURVIVED as a *prohibition* (Bonferroni 4.03), not an edge | `scan_reports/2026-09-24_strategy-studies_21-study-programme.md` |
| Chronology (daily, 89 months) | 1d | does last month's winning group win again | 39,373 trades | - | - | winner repeats 18/60 vs 14.7, z +1.00; cross-lag 0/12 pairs | - | month-shuffle null | FAILED | `workspace/chrono/FINDINGS.md` |
| synthetic MOMENTUM/TREND seat | 60m | e.g. BOS+EMA200+regime+RSI | 1,555 OOS pooled | +0.0149 | PF 1.051 | t +0.77 | 2/5 paths credible | seed replication | FAILED (synthetic) | `research/backtests/momentum_trend.md` |

**MNQ top 5 by strength of evidence (none clear deflation):**
1. MNQ 60m `rth_only=True` reals-over-placebo (p=0.0015) - post-hoc, fails holdout.
2. 180d/90d 60m TREND top rows (+0.66 to +0.70R, n 27-28) - placebos in the same top 10, no persistence.
3. Deep ORB median -0.040R (least-bad ORB symbol) - still negative at zero cost.
4. Lead-lag: 60m breaks lead 240m by 8 bars - a fact, 78-81% false positives.
5. Prohibition: do not fade the 60m cash-open bar (z -7.84).
**Honest read: nothing on MNQ is an edge.** 27.4% of MNQ generated strategies are VOID (highest).

---

## 2. MES (Micro S&P)

| study / family | tf | rule | n | exp R | win / payoff | t vs threshold | WF / OOS | placebo | verdict | source |
|---|---|---|---|---|---|---|---|---|---|---|
| Deep scan by timeframe (median, all groups) | 1d/4h/1h/30m/15m/5m | 13 families | 2,452 floored strategies (3 sym) | +0.008 / -0.052 / +0.015 / **+0.110 (84% pos)** / +0.072 / **-0.218 (11%)** | - | - | 30m = one 58-day window | none in that scan | INCONCLUSIVE (30m single regime) | `scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md` |
| MES 1h TREND | 1h | trend+structure aligned w/ regime | 137 strategies, 20-40 trades each | +0.252 median, 96.4% profitable | 53.3% median | top row t 2.95 vs 3.35 generous / 4.36 strict | nested windows only | later: nothing beat placebo | FAILED - **trade-floor artefact**: inverts at n>=40 (z -1.93), n>=60 (z -4.78) | deep scan + 21-study programme |
| near-miss: MES 30m 58d TREND | 30m | - | 20 | +0.794 | 60% / 3.70 | 3.18 vs 3.24 | none | none | INCONCLUSIVE | deep scan |
| near-miss: MES 1h 90d VOLUME_PROFILE | 1h | value_area_breakout (~51% of bars; trend proxy) | 20 | +0.448 | 70% / 3.19 | 3.04 vs 3.04 | none | none | INCONCLUSIVE | deep scan |
| near-miss: MES 15m 58d TREND | 15m | - | 27 | +0.849 | 74.1% / 1.40 | 2.99 vs 3.33 | none | none | INCONCLUSIVE | deep scan |
| ORB (deep) | 5-60m | as MNQ | median 295 | **-0.142** | 35.8% / 1.413 | best 0.266 | negative all periods | yesterday's OR: -0.128 -> -0.072 | FAILED (0.83% of configs profitable, maxDD 55R) | `orb_test_*.json` |
| Top-10 ranking (worker 2) | 60/240m | as MNQ | - | best reals: 274d 60m VOLUME_PROFILE +0.35 (n=56); 180d 240m VWAP +0.67 (n=27) | - | max 3.03 vs 4.29/4.38 | top strategy changes 6/6 folds at MES 60m; median sibling fraction positive **0.0** | placebo 1st in 12/16 cells; **MES 30d 240m: 10/10 top slots placebo** | FAILED | `RANKING_FINDINGS.md` |
| `require_alignment >= 0.5` | 240m | require MTF alignment | paired | +0.047 IS / **+0.077 OOS** | - | - | helps 1 of 4 cells (MES 60m -0.087 OOS) | random-veto control -0.004/-0.011 | INCONCLUSIVE (found by looking at 4) | `RANKING_FINDINGS.md`, `w2/cells/mtf3_*.json` |
| Fib golden pocket vs shallow | 240m / 60m | - | <20/slice | - | - | MES **+5.99** (240m), +4.01 carried by MES at 60m | no slice reaches 20 trades | - | INCONCLUSIVE (MES-only; MNQ twin contradicts) | `ORB_ICT_FINDINGS.md` |
| Cash-open-bar fade | 60m | - | - | - | - | z -5.60 | replicates | - | prohibition | 21-study report |
| 15m BREAKOUT | 15m | volatility_compressed base filter | **0 trades from 138 strategies** | - | - | - | - | - | INCONCLUSIVE (VOID: atr_percentile on 24h history, 0/1,066 RTH bars) | `workspace/studies/STRATEGY_CATALOGUE.md` sec 4 |
| Chronology (daily 89 mo) | 1d | - | 34,027 | - | - | 17/56 vs 18.3, z -0.37; 0/6 cross-lags | - | shuffle | FAILED | `workspace/chrono/FINDINGS.md` |
| (cross-lane) REPLAY R1 walk-forward | 60m | discretionary replay with control | 2 fills, 47 scored misses | - | - | placebo separation z +1.021 vs free_t(20) 2.448 | - | yes, every bar | FAILED; variance-ratio q2..q24 all p>=0.74 = random walk | `workspace/paper/REPLAY/R1/SUMMARY.md` (agent 3 lane) |

**MES top 5 by evidence:** (1) MES 1h VOLUME_PROFILE 90d t 3.04 = generous line, n=20; (2) MES 30m TREND
t 3.18, n=20, single window; (3) `require_alignment` MES 240m +0.077 OOS; (4) golden pocket MES-only +5.99;
(5) 30m median +0.110 (84% profitable) - one 58-day regime. **All INCONCLUSIVE-to-FAILED; nothing beat
its own placebo.** MES daily is roll-clean (7.40 y) - the only honest long-span substrate (with MNQ).

---

## 3. MGC (Micro Gold)

| study / family | tf | rule | n | exp R | win / payoff | t vs threshold | WF / OOS | placebo | verdict | source |
|---|---|---|---|---|---|---|---|---|---|---|
| Deep scan by tf (median) | 1d/4h/1h/30m/15m/5m | 13 families (bigscan passes all groups) | 554k screened, 3 sym | -0.003 / +0.023 / -0.017 / -0.137 (9%) / **-0.232 (9%)** / -0.185 | - | 0 clear | - | - | FAILED | deep scan |
| Best MGC group | mixed | MULTI_TIMEFRAME | 96 | -0.040 median (37.5% pos) | 42.9% | - | - | - | FAILED (no group positive on median) | deep scan |
| Clean ranking MGC 60m | 60m | VWAP / TREND / MOMENTUM / MTF | - | modestly above control | - | 0 clear free_t 4.03-4.13 (MGC+MCL) ; programme 5.13 | top strategy changes 58/70 folds (MGC+MCL) | reals > controls forward +0.0492 vs +0.0309 | INCONCLUSIVE ("framework for discretionary read") | `scan_reports/2026-09-24_MGC-MCL_...md` Part B |
| MGC 60m rank 2: `vwap_cvd_directional_ema_stack_structure_trend_vwap_band1_bounce` | 60m | VWAP band-1 bounce + trend stack | 24 | +0.317 | - | < 4.1 | disjoint thirds +0.049 / +0.605 / +0.088 (n 17/7/6) | - | INCONCLUSIVE | `rank_mgc_mcl_performance_db.json` summary.replication_disjoint_thirds |
| MGC 60m rank 4: `momentum_delta_confirms_bar_macd_directional_range_position_extreme` | 60m | - | 37 | +0.285 | - | < 4.1 | thirds +0.51 / +0.03 / +0.37 (n 13/19/10) | - | INCONCLUSIVE | same |
| MGC 240m | 240m | - | - | - | - | - | - | **MGC 240m/180d top 4 rows all placebos**; 240m worse than own placebo | FAILED | `RANKING_FINDINGS.md` |
| ORB best config (deep) | 15m | OR60, retest entry, mid-range stop, 1R target | 108 | **+0.191** | 59.3% / 1.077 | 2.137 vs 3.888 | IS 47 +0.222, OOS 61 +0.167; slices +0.17/+0.21/+0.18 | 20/72 neighbours positive; negative on MES/MNQ | FAILED (spike, not plateau) | `orb_test_strategy_rankings.json` |
| ORB (deep, all 240 configs) | 5-60m | - | median 93.5 | -0.064 | 41.6% / 1.266 | 2.137 | 27.8% of IS-profitable stay profitable OOS | yesterday's OR -0.041 -> +0.002R, profitable 38% -> 51% | FAILED | same |
| Chronology (daily, 117 mo) | 1d | VWAP(t) -> TREND(t+1) | 56,670 trades | r +0.528 (n=25 months) | - | z 2.75 vs Bonferroni 3.02 | - | shuffle | FAILED - **and MGC daily fails the roll audit** (see contradictions) | `workspace/chrono/FINDINGS.md`, `workspace/studies/SERIES_AUDIT.md` |
| `volatility_normal` filter | 60m | require normal ATR percentile | paired | - | - | +9.64 pooled but **MGC 60m z -6.30** | - | - | FAILED on MGC (symbol-specific) | 21-study report |
| Kill zones (London open) | 60m | - | - | - | - | range ratio 0.88, vol 0.79 | - | - | FAILED | `ORB_ICT_FINDINGS.md` |

**MGC economics:** most cost-robust contract (costs flip 1 of 259 60m rows positive->negative; round-turn
1.7% of median risk). **MGC data hazards:** daily fails roll audit (gap sum +313% of total return, even-month
excess p<0.0001); archive daily bars 0-383 are a different instrument (10.1x splice 2012-04-25); on 60m,
**112% of total log return accrues at zero-time bar boundaries** (open[i+1] != close[i]), a direction-
dependent fill asymmetry. Profile asked `rth_only=False`; generator emitted `rth_only=True` on 184/184.

**MGC top 5 by evidence:** (1) ORB 15m OR60 retest +0.191R n=108, OOS +0.167, t 2.14 (spike); (2) 60m
vwap_band1_bounce rule, positive in 3/3 thirds, n=24; (3) 60m momentum/range_position_extreme positive
3/3 thirds, n=37; (4) 60m VWAP/TREND/MOMENTUM/MTF above control (group-level); (5) chronology
VWAP->TREND co-movement z 2.75 (roll-contaminated). **None clears deflation.**

---

## 4. MCL (Micro Crude)

| study / family | tf | rule | n | exp R | win / payoff | t vs threshold | WF / OOS | placebo | verdict | source |
|---|---|---|---|---|---|---|---|---|---|---|
| MOMENTUM group | 60m & 240m | momentum + participation | 66 observations, 97% positive | - | - | largest MCL t 2.97 (60m 180d) vs 4.03-4.13 | beat its control on both `rth_only` arms | yes | INCONCLUSIVE - **strongest result in the MGC/MCL study**; cost-fragile | `scan_reports/2026-09-24_MGC-MCL_...md` Part B |
| MCL 240m/180d top rows | 240m | rank 1 = **placebo_shuffle** VWAP (+0.407, n=25); rank 2 real MOMENTUM `delta_confirms_bar_rsi_directional_slope_directional` +0.370 n=29 t 1.38 | - | - | 51.7% / 1.66 | 1.38 | - | placebo ranks 1st | FAILED | `rank_mgc_mcl_performance_db.json` |
| ORB (raw only, no deep archive) | 5-60m | MCL RTH opens 09:00 (on the hour) | median 18 | -0.089 | 36.8% / 1.528 | best 1.392 | - | - | FAILED | `orb_test_*.json` |
| Kill zone London open | 60m | - | - | - | - | range ratio **1.15, +12.4t, replicated** (only contract above average) | - | - | fact about range, not direction | `ORB_ICT_FINDINGS.md` |
| All 13 families (MCL unprofiled) | - | - | - | - | - | per catalogue: largest t +1.12 vs free_t 1.177 in one roundtable study | - | - | FAILED ("widest search, worst best") | `STRATEGY_CATALOGUE.md` sec 1 |
| News filter (EIA 10:30) | synth | outside_news_blackout | paired | +0.0037 diff | - | t +0.89 | - | - | INCONCLUSIVE (synthetic has no news) | `research/backtests/cross_symbol_timeframes.md` |

**MCL economics:** cost-fragile (8/183 60m and 3/37 240m rows flip to negative net; round-turn 5.4% of
median risk = 3.2x MGC). `MCL_1440m.jsonl` is one bar; `CL_1440m` has a negative price (-37.63,
2020-04-20) - no usable MCL daily history. `opening_range_breakout` actually fires on MCL 60m (17.3%)
because its RTH open is on the hour.

**MCL top 5:** (1) MOMENTUM 60/240m (97% positive, beats control); (2) MOMENTUM 240m rank-2 row +0.370
n=29; (3) London-open range expansion 1.15 (vol sizing, not direction); (4) VWAP group (placebo-topped);
(5) ORB -0.089 (least-bad raw ORB). **None clears deflation; MCL is the one symbol worth a
pre-registered MOMENTUM test.**

---

## 5. NQ and ES (full-size index; one complex with MES/MNQ)

| study | tf | rule | n | exp R | win / payoff | t vs threshold | OOS | placebo | verdict | source |
|---|---|---|---|---|---|---|---|---|---|---|
| **Largest t in the project** | NQ 60m 180d | MOMENTUM `cvd_directional + ema_fast_above_slow + macd_hist_direction`, filter `volume_surge`, ATR 2.5 stop, R-multiple targets | 44 | +0.289 | 68.2% / 2.48 | **3.923 vs 4.132** | not OOS-tested as a single row | best placebo rank 32 of 101 (null 15.4) | INCONCLUSIVE (below free_t; orderflow = OHLCV proxy) | `workspace/strategy_research/rank_nq_es_grains_strategy_rankings.json` cells.NQ_60m_180d |
| NQ 60m floor-20 population | 60m 180d/274d | all groups | 101 / 135 rows | median +0.075 / +0.041; 84.2% / 71.9% positive | - | best 3.923 / 3.426 | - | placebo rank 32 / 97 (worse than null) | INCONCLUSIVE (best index cells) | same, `rank_nq_es_grains_robustness_report.json` |
| NQ 1h OPENING_RANGE | 1h | "positive in all 3 windows" | 18 strategies | +0.070 | 52.4% | - | nested windows | - | **RETRACTED**: `opening_range_breakout` fires 4/4,256 bars; 1 of 47 floored OR strategies is an OR breakout | deep scan + 21-study report |
| NQ 1h TREND / VOLUME_PROFILE / VWAP | 1h | - | 26 / 108 / - | +0.081 (92.3%) / +0.046 / +0.02 | - | - | nested | - | INCONCLUSIVE | deep scan |
| ES 60m | 60m | all | 134 floored (274d) | median -0.012 | - | best 2.737 vs 4.138 | 60/40: top IS rows e.g. +0.37 IS -> -1.02 OOS | top-10 Jaccard across 3 seeds **0.0** | FAILED | `rank_nq_es_grains_robustness_report.json` |
| Index complex floor-free | 60/240 | - | 16 cells | median -0.064 | - | - | - | - | FAILED: 2/16 cells positive, sign p 0.0042 | same `grains_vs_index_complex` |
| ORB NQ (raw) | 5-60m | - | median 17 | -0.332 | 26.7% / 1.03 | 1.057 | - | - | FAILED (5% profitable) | `orb_test_*.json` |
| NQ cash-open-bar fade | 60m | - | - | - | - | z -7.84 | - | - | prohibition | 21-study report |

NQ fills are clean (stops realise -1.007R median; 0.9% worse than -1.2R). **D41:** NQ != MNQ (0.2% of 4,947
overlapping 1h bars share OHLC; NQ ends 2026-09-18, MNQ 2026-09-22). NQ is a full-size contract: stats
transfer, sizing does not ($50k account).

**NQ/ES top 5:** (1) NQ 60m 180d MOMENTUM t 3.923; (2) NQ 60m 274d best t 3.426; (3) NQ 60m population
84% positive at floor 20 (placebo rank 32/101); (4) ES 60m 274d best t 2.737; (5) NQ 1h TREND +0.081.
**Nothing clears; the complex is one observation.**

---

## 6. Grains MZC / MZS / MZW

| cell set | result | source |
|---|---|---|
| Deflation, 21 cells | 0 rows clear free_t 4.13-4.24; best t 1.955 (MZC 240m 274d, VWAP `above_vwap + cvd_directional + di_direction + macd_directional`, n=29, +0.169R) | `rank_nq_es_grains_robustness_report.json` deflation |
| Floor-free census | median -0.085R, 40% positive; 5/21 cells positive, sign p 0.027 | `grains_vs_index_complex` |
| RTH gate (D24) | MZC 240m 274d: RTH on +0.073 vs off -0.103 (p 0.001); MZC 60m -0.237 -> -0.387 | `rth_only_arm_D24` |
| Placebo | best placebo rank 1 in many cells (e.g. MZC 60m 180d/274d rank 1) | same |
| **Data verdict (D40): NOT ELIGIBLE** | CSVs splice contract months: MZC 60m 26.3% flat bars, 11.3% zero volume, 367 gaps >2% (47% reverse next bar); 1m 84-89% rangeless; stops realise -1.215R (MZC) vs -1.007 NQ; median 60m volume 11-17 contracts; fees 9.2% of R on MZC | `workspace/studies/DEFECTS.md` D40, `SERIES_AUDIT.md` sec 5 |

**Verdict: FAILED and untestable on this data.** Top 5 is meaningless; best row t 1.955.

---

## 7. QQQ / SPY and other

- QQQ/SPY cells (1440/60/5m x 30-274d) were queued in `workspace/bigscan/rerun.txt`; **no result for them
  exists in this lane** (row output is gitignored `workspace/focus/`). The 2026-09-23 "broad 11-symbol sweep"
  is cited only for corr(win rate, expectancy) = +0.718 on 3,453 strategies.
- **QQQ/SPY intraday volume is 58.2-59.4% zeros** -> not eligible as a volume input (SERIES_AUDIT sec 5).
- `CL_1440m` (24.64 y) not eligible (negative price). `MGC_1440m` archive: splice + roll failure.

---

## 8. BOUNCE LEVELS - every measured statistic on levels in this lane (+ two cross-lane sources)

**Headline: across every level definition measured, the rate at which price holds or breaks a level is
indistinguishable from random lines drawn in the same price range, and where a bounce trade separated
from control it was because the control was worse, not because the level paid.**

### 8.1 Key-level breach scanner ("session 99X1") - the 5,717 vs 4,729 result, located

- **Where:** `futures_agents/scanners/render.py` lines 25-34 (`MEASURED` dict, hard-coded) and
  `workspace/paper/CALL/CONSOLIDATION.md` lines 58 and 119. Session id `session_01DMSyFfv13VD63wAZx52uWd`.
- **Numbers:** **5,717 real key-level breaches** across **MNQ/MES/MCL/MGC at 60m and 240m** vs **4,729
  placebo breaches on random levels drawn from the same price ranges**. Breakout (continuation) rate
  **real 43.0% vs placebo 42.6%** -> "indistinguishable". No per-symbol, per-level-type, FAILED-rate or
  RETEST-rate split was persisted.
- **Missing code:** `breach.py`'s docstring says `futures_agents.scanners.measure` runs the placebo
  comparison - **that module does not exist on either branch**. Only `breach.py`, `render.py` and
  `tests/test_breach_scanner.py` exist. The 99X1 numbers cannot be re-run from the repo as is.
- **Definitions (breach.py):** levels = prev-day H/L (weight 1.00), overnight H/L (0.90), prev-week H/L
  (0.85), prev-day close (0.70), initial-balance H/L (0.65), session H/L (0.55), day open (0.45), swing
  S/R clusters over 300 bars (0.35 + 0.12 x touches, cap 0.80), round numbers (2 nearest); levels within
  1 tick collapsed. Breach = **close** beyond level by 0.10 ATR (wicks ignored). Next 12 bars: FAILED
  (close back through by 0.25 ATR = sweep), BREAKOUT (extends >=0.25 ATR, never fails), else RETEST.
  Playbooks: breakout-go, failed-breach fade, retest-hold; stop floor 0.5 ATR enforced.

### 8.2 REPLAY R1 level study (MES 60m, 2024-10 -> 2025-03; cross-lane, agent 3 owns)
`workspace/paper/REPLAY/R1/NOTES.md` lines 975-1016, 1780-1800; `agents/E9_levels_fair.py`.

| level type | n | bounce | break | bounce trade | break trade |
|---|---|---|---|---|---|
| fresh swing extreme (1 touch) | 162 | 45.7% | 54.3% | +0.048R | +0.045R |
| retested level (2+ touches) | 175 | 53.7% | 46.3% | +0.060R | +0.063R |
| random lines (control) | 200 | 55.0% | 45.0% | +0.036R | -0.127R |

- First run reported 83.1% bounce - artefact (bounce scored on a 0.75-ATR touch vs break on a 0.40-ATR
  close); random lines scored 77% under the same bias.
- Touch count 2/3/4/5/6+: 48.6/52.9/63.6/70.0/54.3% bounce; control 53.6/54.7/60.0 same shape; n=10 at 5.
- Support 59.4% vs resistance 47.9% bounce, but bounce **trade** -0.084R at support, +0.213R at resistance.
- With-trend 55.7% vs against 52.0%; control 54.3% vs 55.8%.
- "Fresh extremes break more often": z 1.76 -> **-0.73** under a fair control -> **retracted**.
- Control was unfair (fabricated touch counts, 31% higher ATR, 21-47% of random lines on real levels).
  Fair control: bounce-trade z +0.08 -> **+2.52** (10-seed range +1.57..+3.20), but real levels earn
  **+0.043R** vs fair control **-0.294R** - separation is the control losing, and 2.52 < desk free_t 3.37.
  "All key-level and touch-count claims withdrawn" (SUMMARY.md line 52).

### 8.3 Order blocks / FVG zones (supply-demand, ICT flavour) - real CME data, 5 symbols
`workspace/studies/ORB_ICT_FINDINGS.md`; `workspace/strategy_research/ict_blocks_fvg_*.json`.
- Firing: `ict_ob_return` 40.5-51.5% of bars; `ict_fvg_return` 50.3-56.1%; newest OB/FVG 18.3-24.6 /
  30.2-34.2%; fresh OB/FVG 5.1-6.4 / 10.6-13.5%; library `fresh_zone_approach` 0.56-1.38%.
- **Touch ("magnet") rate within 40 bars:** FVG real 87.3-90.1% vs sham 87.0-89.8% (Stouffer z -0.47);
  OB real 78.2-82.3% vs sham 79.9-83.1% (**z -2.05, real touched less**). Sham = matched ATR-distance,
  width, side, symbol, horizon, 12 draws/zone.
- **Reaction after touch** (symmetric 1-ATR barrier race): OB -0.93 (nothing); FVG IS +3.41 (8/9 cells)
  -> OOS **+0.13** (4/9); NQ-60m +2.21 and MNQ-60m +2.04 both flip negative OOS.
- **Freshness (first touch vs retested) - answerable here** (191-634 first touches, 1,372-2,180 later
  touches per cell): **does not matter**. OB freshness Stouffer +1.23; FVG +2.24 IS -> -1.34 OOS.
  `ict_ob_fresh` paired: +0.088R IS (7/9) -> **-0.064R OOS (2/9)**. `ict_fvg_fresh`: +0.078 IS (9/9) ->
  +0.026 OOS (6/9, z +1.45).
- Best OOS: `ict_fvg_newest` +0.022R, 8/9 cells, z +2.33 < free_t 3.48, chosen after looking at 8.
- **Median absolute expectancy negative in all 16 condition x period rows after costs (best -0.004R).**
- Breaker blocks / inversion FVGs (first retest): fire 5.6-6.7% / 11.8-14.3%, flat everywhere.
- A random-location `ict_placebo_ob + ema_stack` ranks **2nd of 387** (+0.433R OOS, n=35, t 2.12);
  3 of the 5 most durable rule sets contain the placebo.
- 48-corner OB parameter grid x 5 cells: no corner works, best OOS z +1.90.

### 8.4 Liquidity sweeps and reclaims
- **Sweep frequency:** 1,893-2,014 sweeps per symbol at 60m over 10.5 months = **37.9-40.3% of bars**.
  PDH+PDL sweep rate 12.2% (library `prior_day_sweep` 12.4%).
- **Sweep -> opposing MSS within 5 bars:** raw odds x1.46 (z +17.6) is tautological (sweep bar closes
  back inside, nearer the swing). Distance-matched Mantel-Haenszel OR **1.08**; vs bars touching no level
  **0.86** (z -4.03): sweeping predicts the shift slightly *worse* than touching nothing.
- Chain sweep->MSS->displacement FVG->retrace: 264-370 MSS, 136-184 imbalances, **77-106 retraces** per
  symbol (7-9/month), 57-68 trades/cell. Full chain **-0.045R/cell, 8/12 cells losing**; no ablation
  arm reaches |z| 1.96 (8 comparisons x 3 windows), sign flips IS->OOS in 6/8.
- 5-bar-displaced placebo **+0.08R, beats the real entries**. Wrong order (MSS then sweep) ranks 1-2.
- Gross +0.052R -> net -0.017R -> 4x slippage -0.062R. Resting limit at the imbalance: **-0.158R over
  741 trades**, 1/12 cells positive, win 39.9% -> 19.8%.
- 240m levels into 60m chain: -0.199R vs -0.060R, 8/8 cells negative.
- Tuning gap/retrace tolerance: walk-forward -0.11R/fold vs -0.00 never tuning; oracle +0.18R ->
  data-mining bias ~0.29R/fold.
- Library LIQUIDITY sweep side: 156 rule sets with >=1 trade, **0 with >=20**; `session_extreme_sweep`
  is self-referential (D36) and all 48 fires land 16:00-16:55 ET (void under the session rule).
- Synthetic (`research/backtests/supply_demand_liquidity.md`): LIQUIDITY's apparent WF edge replicated
  on 1 path in 3 (+0.261R t 4.06 on one, -0.121 and +0.082 on others; between-path t 0.67).

### 8.5 Supply/demand zones (library detector)
- `fresh_zone_approach` fires 0.5-3.8% of bars; SUPPLY_DEMAND: **0 strategies reach 20 trades in 6 cells**,
  budget x4 moved 0 -> 0 -> **INCONCLUSIVE, untestable as built** (D33: detector, not concept).
- Synthetic: zones 301->604 (5m) after fix, rule sets clearing 30 trades 0->0, busiest 11 trades/120 days;
  1.0-ATR stop lands **inside the zone on 88.0% / 82.6% / 93.3%** of firings (5/15/60m); stop beyond the
  distal edge + 4 ticks: -0.088R -> **-0.267R**. zone_touch trades coincide with a same-direction sweep
  entry within +/-3 bars 34% / 61% / **82%** (5/15/60m) - on 60m a zone touch *is* a sweep trade.
  `base_vs_departure` test unreachable at shipped defaults (811/812 bases bound by the norm term).

### 8.6 Prior-day / overnight high-low, initial balance
- Only direct outcome stat: breach scanner (8.1), PDH/PDL weighted highest; indistinguishable.
- `prior_day_breakout` vs `value_area_breakout` Jaccard **0.831**, phi +0.743, direction agreement 1.00
  (synthetic) - "volume profile breakout" is a prior-day-range breakout.
- `initial_balance_break` duplicates the library "ORB" on MCL (Jaccard 0.993, D39).
- ORB = opening-range level: broken in 74-100% of RTH sessions (median 99.3%); post-break MFE/MAE
  0.80-1.03 range-widths -> no directional information; yesterday's range beats today's.

### 8.7 VWAP and volume-profile levels
- `above_vwap` fires 100.0% of bars (synthetic), is misnamed (returns SHORT; D-VW1) and at daily reduces to
  sign(CLV) (D52). `vwap_band1_bounce` VOID at 1440m (band < 1 tick on 100% of daily bars).
- MGC 60m: VWAP group modestly above control; the vwap_band1_bounce rule is positive in 3/3 thirds
  (n=24, +0.317R) - best bounce-style row on a clean contract, t far below threshold.
- MES 240m 180d VWAP +0.67R n=27; MES 4h 9mo VWAP R:R 3.1 win 42.9% +0.479R (deep scan) - no OOS.
- Synthetic VWAP 60m `above_vwap+BOS+ema_stack+rsi` 4/5 paths positive, n=1,098, +0.0263R, t 2.142 vs
  deflation 3.462 / 2.537 -> withheld. VWAP walk-forward IS +0.132R -> OOS -0.029R.
- Volume profile: `value_area_breakout` fires ~51% of real bars (66.8% synthetic 15m): trend proxy, not a
  level. All six profile conditions DEAD at 240m/daily (profile needs >=10 bars of prior session).
  `poc_reversion`: 61.6% of signals target a POC unreachable within an hour (synthetic); `lvn_rejection`
  node set empty in 34/59 prior-day profiles; `value_area_edge` (0.35 ATR band) correctly specified but
  only 21 trades / 120 days.

### 8.8 Round numbers
- Present only as a level source in the breach scanner (2 nearest whole-number levels). **No isolated
  round-number statistic exists anywhere in this lane.** INCONCLUSIVE (never measured alone).

### 8.9 Fibonacci retracements
- `fib_sr_confluence` fires **48.6-81.0%** of bars (MNQ 60m 73.2%) - near-independent of what it claims to
  confluence with. Fib-level bars indistinguishable from plain S/R bars; neither beats a direction-matched
  random entry.
- Golden pocket (0.618-0.786) vs shallow: bar-level best |t| **1.80**; 240m Stouffer +1.93 vs free_t 2.70;
  0 matched pairs reach 20 trades in any slice; MES-only effect; **refuted**.
- OTE == `fib_golden_pocket` (Jaccard 0.938-1.000, 7th alias).
- `swing_leg()` spans other swings on 14.4-17.2% of bars (wrong base 1 bar in 6); synthetic leg flips every
  6.6 bars, 52.9% agreement with structure_trend. Fixing it moved -0.093R -> -0.095R.

### 8.10 Structural levels (swing invalidation) - where to put the stop
- Distance to invalidation median **1.57-2.68 ATR**; textbook structural trade (stop past invalidation,
  target prior extreme) has median R:R **0.60-1.10, below 1:1 in 26/30 cells**; prior extreme already behind
  price on 13-38% of bars.
- Entering near invalidation (<=0.5 ATR): payoff 3.00, win 0.194, exp -0.110 vs ungated -0.106 -
  payoff/win self-cancellation; win rate flat 0.370-0.423 across distance buckets at fixed geometry.
- **Rule that survived: structural stop never tighter than ~0.5 ATR** (30 cells, 1,600 trades, +0.0136 vs
  -0.1061R, OOS +0.0008 vs -0.2050, z +2.02) - restores parity with a 1-ATR stop, not an edge.
- 3-bar fractal confirmation consumes 50-60% of a median swing leg (D29).

### 8.11 WHY did levels hold - what each candidate explanation measured

| factor | measured effect | source |
|---|---|---|
| **Confluence** | 2 -> 4 signals cuts trades 35% (65 -> 42, z +8.48), expectancy unchanged, sign favours 2. `fib_sr_confluence` non-selective. MTF agreement *hurts* (z -4.09; independent rebuild z -2.68) | 21-study report; STRUCTURE_FINDINGS |
| **Freshness / first touch** | OB/FVG freshness: no effect OOS. Structure age: no monotonicity, best bucket is the *stalest*. REPLAY fresh extreme: retracted (z -0.73) | 8.3, STRUCTURE_FINDINGS, 8.2 |
| **Touch count** | REPLAY 2-5 touches rises 48.6 -> 70.0% but control rises the same way; n=10 at peak | 8.2 |
| **Time of day** | Avoid intraday entries 15:00-16:00 ET (z -4.43, median -0.617R); don't fade the 60m cash-open bar (z -10.64 pooled); kill zones = trade thinning (every-24th-bar placebo +2.25 mean); 21:00 ET +4.52 (ICT non-entry hour), 08:00 ET -3.41 (worst, 08:30 releases); avoid_lunch hurts (z -3.25); directional efficiency flat 0.37-0.50 every hour | 21-study report, ORB_ICT_FINDINGS |
| **Trend context** | REPLAY with-trend bounce 55.7% vs against 52.0% (control 54.3/55.8); regime_trending 3 cells +, 3 -; nested pullback worse than nothing (6.2% vs 11.2% profitable both periods) | 8.2, 21-study, STRUCTURE |
| **Volatility** | `volatility_normal` +9.64 pooled but hurts MGC 60m (-6.30); compression -> expansion z +12.20 IS, significantly negative OOS in 6/12 cells; volatility predictable (R^2 0.112, REPLAY) and **directionless** - use it to size / stand down, never to pick side; kill-zone hours have more range, not more direction | 21-study, CONSOLIDATION.md, ORB_ICT_FINDINGS |
| **Support vs resistance** | Support bounces more (59.4 vs 47.9%) but trade payoff inverts (-0.084 vs +0.213R) | 8.2 |
| **Stop placement at the level** | Stops inside zones 83-93% at shipped 1-ATR stops; widening beyond zone made it worse; 0.5-ATR floor restores parity only | 8.5, 8.10 |

**Honest summary for the owner:** no level type, confluence, freshness, time or trend filter produced a
hold/break rate or a bounce-trade expectancy that beats a fair random-level control out of sample. The
strongest level-shaped rows are MGC 60m `vwap_band1_bounce` (+0.317R, n=24, 3/3 thirds) and the REPLAY fair-
control bounce arm (z +2.52, +0.043R) - both below any deflated bar. Measurement infrastructure for levels
(`breach.py` + a restored `measure.py`) is the reusable asset.

---

## 9. Cross-symbol findings (what survived programme-wide correction)

**912 matched comparisons, Bonferroni |z| >= 4.03, 56 survive** (21-study programme). Actionable ones:
1. Turn `exit_at_session_close` **off** (paired sign z +3.52; median 4h/daily hold otherwise 0.0 min).
2. Exit model `ATRx1 -> 2/4R anchored to 1/2.5 ATR`: rank 0.447 vs 0.556 null over 352 blocks; best in
   7/10 entry groups. Three targets worse than two (z -2.87).
3. Anchor/execution split only at a 240m anchor with anchored targets (z +4.07); negative at daily
   anchor (-5.80) and with R-multiple targets (-2.85); payoff up z +9.59, win down z -6.79.
4. No intraday entries 15:00-16:00 ET (z -4.43).
5. Don't fade the cash-open 60m bar (z -10.64; NQ -7.84, MNQ -7.78, MES -5.60, MGC -5.39; reverses at 15m).
6. `volatility_normal` symbol-specific (+9.64 pooled, MGC 60m -6.30).

**Refuted premises:** confluence helps; MTF agreement helps (`mtf_aligned` strongest negative, z -2.53);
trend-following needs a trending regime; compression precedes expansion; fib levels carry information;
lunch avoidance; sub-hourly (5m: 11-16% of strategies profitable); ORB; ICT (OB/FVG/sweep/kill zones/OTE);
swing depth (worse than random discard, 28.7th percentile, z -6.57 IS / -3.49 OOS); geometry; nested
pullback; ranking persistence.

**Structural facts:** corr(win rate, expectancy) = **+0.745** on 2,452 strategies (+0.718 on 3,453);
payoff median 1.22 (IQR 0.95-1.58). Within ORB: corr(win, payoff) **-0.745** (-0.93 MES/MNQ) - wider stop
raises payoff 89% while win falls 13.8 pts, expectancy unchanged (replicated 4x in the project).
MES/MNQ generated populations share 0.5-0.8% of rule sets (per-symbol RNG seeding, D14): cross-symbol
"same strategy" comparisons are not available.

**Walk-forward / persistence:** disjoint thirds: 72 strategies positive in all three vs permutation null
70.1 (chance). OOS expectancy negative in 5/6 cells. Top 10 overlap across disjoint thirds on clean
contracts 15 vs 16.9 by chance (-11%); Jaccard 0.048-0.081. Realised causal roll on MGC+MCL -0.0155R
over 13,171 OOS trades (excess -0.0050R).

**Chronology:** no chaining on MGC/MNQ/MES daily (0 surviving cross-lags of 20/12/6). Only groups
reaching 24 months were candidates: 6 (MGC), 4 (MNQ), 3 (MES).

**Remaining untested leads (hypotheses, not edges):** `nested_resumption` (+0.118R on 157 OOS trades,
t +1.22, z +4.97 vs htf_trend; ablation shows both components needed; 0/224 OOS rows reach 20 trades);
MCL MOMENTUM; `sd_age_ge50` on 60m (+3.75 IS / +2.06 OOS, 4 cells, reverses on 240m - likely overfit).

---

## 10. Infrastructure facts and pitfalls future agents must know

1. **Nested windows.** 274/180/90/30d windows all end on the same bar; agreement is one observation. Use
   disjoint slices (`T.disjoint_slices`) or 60/40 temporal splits.
2. **20-trade floor selects on exit geometry** (0.75-ATR stop -> ~88 trades; 1.5-ATR -> ~11). Always
   report floor-free censuses (MES 1h TREND died on this).
3. **D28:** `toolkit.ab()` unpaired rank-sum inflates |z| ~3.3x (up to 8.7 on null data) when arms hold
   correlated variants. Use per-cell paired sign tests + Stouffer. Pooled trade-level z inflates ~3x;
   pooling per-strategy rows across cells inflates too.
4. **D35: one-sided fill bug** (limit fills at bar extreme, same-bar target credited) made +0.354R at
   t 5.19 that survived OOS and all slices. Resampling cannot catch always-favourable bias - audit fills.
5. **Look-ahead power control does not license nulls** (R6 retraction, 2026-09-27): a cheat that fires
   normally ranks 1st; it says nothing about detectors that never fired. Check per-condition firing rates.
6. **Dead/void conditions:** openinterest dead (no OI column); orderflow is an OHLCV proxy
   (`delta_confirms_bar` = close > mid and close > open); `session_extreme_sweep` self-referential and void;
   `volatility_compressed` void under RTH at MES 15m; `range_position_extreme` guaranteed zero in REVERSAL;
   `vwap_band1_bounce` void at daily; `above_vwap` misnamed; news filters identity on a :00 grid;
   multitimeframe at daily compares against a lagged copy of itself (D50); profile dead at 240m/daily;
   OPENING_RANGE never constructed at 60m/240m (range resolves iff T | L and T | RTH-open minutes; 09:30 =
   570 not divisible by 60; MGC 08:20 = 500 not divisible by 15/30/60; 240m ORB impossible); `volume`
   required group silently dropped (D54); ExitModel index 3 cannot trade (D8); StopKind FIXED_TICKS/RANGE
   zero carriers; TIME exits 0 of 103,191 trades.
7. **Seven+ aliases:** avoid_lunch = REVERSAL, opening_drive_window = OPENING_RANGE, after_opening_range =
   LIQUIDITY, mtf_not_conflicted = PULLBACK, regime_trending = TREND, regime_ranging = MEAN_REVERSION,
   volatility_compressed = BREAKOUT; `macd_directional` = `macd_hist_direction`; `sd_count_ge1` =
   `structure_trend`; `nested_aligned` = `mtf_aligned`; OTE = `fib_golden_pocket`; `bollinger_extreme`
   subset of `bollinger_mean_pull`. Jaccard-check every new condition.
8. **`exit_at_session_close=True`** reduces every 4h/daily trade to one bar; it is perfectly confounded with
   target kind (only the three ANCHOR exits have it False, D19).
9. **`rth_only`:** True costs 2-12x population at 240m (D24) but flatters expectancy (MZC 240m +0.073 vs
   -0.103). Never mix both arms in one `run_portfolio` call. Generator emits True regardless of profile.
10. **Profiles (`profiles.py`) only narrow generation when `groups` is omitted.** bigscan, chrono,
    `toolkit.measure`, w3 and newstrats/rank pass all 13 groups; only `w2/w2rank.py` (MES/MNQ ranking) used
    profiles. 12 family-symbol cells are dropped with no recorded reason when profiles apply.
11. **Costs under-charged on scale-outs** (D13): 3-target exit pays one round turn; 62-92% of 4h/daily exits
    pay no exit slippage.
12. **Data:** MGC daily fails roll audit (and archive bars 0-383 are another instrument); CL daily negative
    price; MCL daily = 1 bar; grains splice months and are 26-89% flat bars; QQQ/SPY intraday volume 58-59%
    zero; NQ != MNQ (D41); on 60m, open[i+1] != close[i] on 57-80% of contiguous boundaries (MGC 60m 112%
    of return at those boundaries) - fill asymmetry; ~3.5-4% zero-volume 60m bars are the thin overnight
    hour (benign). `data/*_1m.csv` Oanda archive is gitignored/absent. `csv/raw` is read-only (`chattr +i`).
13. **Placebo kinds:** `placebo_shift` leaks (mean normalised rank 0.37-0.47); use `placebo_shuffle`
    (uniform) and `placebo_random`. Share-match placebo cohorts before counting top-10 appearances.
14. `max_per_template` is not a strategy count (divided by max(2, 2 x len(filter_sets)), split across tfs).
15. `futures_agents/scanners/measure.py` is referenced but missing; `render.py` hard-codes the 99X1 rates.
16. Everything in `research/` ran on synthetic random-walk data at commits 5b3ae0c / f82bd35 on the other
    branch; README "Honest status" still says the system has only seen synthetic data (stale).

---

## 11. Contradictions between sources

| # | side A | side B | stronger evidence |
|---|---|---|---|
| 1 | corr(win rate, expectancy) = +0.037 (early 32-strategy sample; `bigscan/aggregate.py` docstring still quotes it) | +0.745 on 2,452 / +0.718 on 3,453 (deep scan) | **B** (n 75x larger); aggregate.py docstring stale |
| 2 | MES 1h TREND "strongest single result", 96.4% profitable (deep scan) | trade-floor artefact, inverts at n>=40/60; no index-complex group beat its placebo (21-study; ranking) | **B** |
| 3 | NQ 1h OPENING_RANGE positive in all three windows | nested windows; OR breakout fires 4/4,256 bars | **B** |
| 4 | `break_of_structure`@240 most promising lead (+4.4 to +5.0 IS) | OOS -0.036R, 37% profitable, 5+/5- OOS cells (s_leadlag) | **B** (retracted in place) |
| 5 | `fib_golden_pocket` beats shallow at 240m z +7.14/+5.65/+4.83, loses at 60m | bar-level |t| <= 1.80; 240m +1.93 vs 2.70; 60m sign actually +4.01; MES-only | **B** |
| 6 | "Power control licenses nulls as real absence" (RANKING_FINDINGS, ORB_ICT_FINDINGS ict_blocks audit - still unretracted in those two files) | R6 audit retraction (scan_reports) | **B**; the two workspace/studies files were not corrected in place |
| 7 | "A random entry outranks the real signal in a third of cells" / placebos 0.85x chance (pooled) | share-matched clean MGC/MCL: controls reach top 10 *less* than chance, z -2.63 | **B** for MGC/MCL; A still holds for MES/MNQ (12/16 cells placebo 1st) |
| 8 | Disjoint-thirds persistence +20% (149 vs 124.0, z +2.67) | clean MGC/MCL -11% (15 vs 16.9) | **B**; A driven by index complex / grains contamination |
| 9 | "NQ and MNQ are the same series" (ORB_ICT_FINDINGS orb_test section, unretracted) | D41: 0.2% of bars share OHLC | **B** |
| 10 | `ema_stack` sole Benjamini-Hochberg survivor (+3.10, 7 cells) | `g_pullback`: IS +4.27 -> OOS 0.00 (MES 60m), +2.25 -> -3.87 (MGC 240m) | **B** (has OOS); treat as unproven |
| 11 | Chronology tested "thirteen strategy groups" (chrono/FINDINGS.md) | only 6/4/3 groups reached 24 months (analyse.py stdout) | **B**; chrono FINDINGS.md not corrected in place |
| 12 | Chronology MGC daily VWAP->TREND z 2.75 is "the closest the hypothesis comes" | MGC daily fails the roll audit (gap sum 3.1x total return) | **B** - MGC daily chronology/ranking rows rest on a contaminated series |
| 13 | STRATEGY_CATALOGUE: "No study in this repository has overridden [a profile]" | `bigscan/cell.py:89`, `chrono/ledger.py:38`, `toolkit.py:159`, `w3_rank.py:144` all pass every group | **B** (code); only `w2/w2rank.py` used profiles |
| 14 | SUPPLY_DEMAND/freshness "unanswerable for lack of sample" | base-free OB gives 1,500-2,700 touches/cell; freshness answered: no effect | **B** (D33) |
| 15 | REPLAY: fresh extremes break more often (45.7%, z 1.76) | fair control z -0.73 | **B** (retracted by its author) |
| 16 | README: no real market data, only synthetic | csv/raw real CME micro bars used by every 2026-09-23+ study | **B**; README Honest status is stale |
| 17 | `anchored targets beat R-multiple` z -5.87 | is `exit_at_session_close` in disguise; held constant, z -1.80 / +1.24 | **B** |

---

## 12. Reusable tools vs one-off scripts

**Reusable (KEEP):**
- `futures_agents/scanners/breach.py` (+ `render.py`): key-level collection and breach classifier with
  placebo-aware callout text. Needs `measure.py` restored to re-measure.
- `workspace/studies/toolkit.py`: `measure`, `ab` (beware D28), `scan_rows`, `free_t`, `wilson`,
  `disjoint_slices`, `make_strategy`, `save`. Imported by roundtable code.
- `workspace/newstrats/placebo.py`: placebo cohort (random/shift/shuffle); imported by 8+ roundtable scripts.
- `workspace/newstrats/orb.py`: correct ORB conditions (`orb_break/touch/retest/fade_*`), `orb.INERT`,
  `orb.long_series(sym, tf)` for the Oanda 1m archive.
- Condition libraries: `ict_blocks.py` (OB/FVG/breaker/inversion + sham zones), `ict_sweep.py` (ordered
  sweep->MSS->retrace chain), `freshness.py`, `depth.py`, `geometry.py`, `leadlag.py`, `nested.py`,
  `orb_w2.py` (explicit ORB simulator).
- `workspace/newstrats/rank.py` + `rank_audit.py`: ranking with built-in placebo arm and three audits.
- `workspace/bigscan/cell.py` + `aggregate.py`: deep-scan cell runner (reproduce command in the deep-scan
  report). `workspace/chrono/ledger.py` + `analyse.py`: month x group ledger and chaining tests.
- `scripts/fetch_yahoo.py`, `scripts/fetch_github_data.py`; `packaging/`; `desk/`; `docs/`.

**One-off (ARCHIVE; findings captured above):** every `run_*`, `save_*`, `*_publish.py`, `analyse*.py`,
`w4_*`, `w6_*`, `ict_{analyse,bias,census,jaccard,lift,lift2,limit,mtf,perf,regime,sens,time,wf}.py`,
`robust*/sensitivity/walkforward/census/analyze/store` drivers in `workspace/newstrats/`; all
`workspace/strategy_research/*.py` and `w2/*.py`; `workspace/studies/aggregate_studies.py`.

**Duplicate JSON (byte-identical):** `strategy_research/robustness_report.json` =
`rank_persistence_robustness_report.json`; `strategy_rankings.json` = `rank_persistence_strategy_rankings.json`;
`performance_db.json` = `rank_w2_performance_db.json` (8.3 MB).
