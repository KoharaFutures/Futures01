# Sweep agent 1: `workspace/roundtable/` + `workspace/developer/` + `workspace/focus/`

Written 2026-09-29 by sweep agent 1 of 3. Read-only sweep; nothing moved or deleted.
Lane contents: 419 files / 108 MB under `workspace/roundtable/`, 3 JSON under `workspace/developer/`, 1 txt under `workspace/focus/`.
The file-by-file decisions are in `agent1_manifest.tsv`, next to this file.

**What the roundtable was.** It ran on 2026-09-26/27 with 16+ agents:
- R1–R6 were researchers writing the strategy catalogue and condition audits.
- DISC1/DISC2 were discovery agents.
- BT1–BT6 were backtesters, each rebuilding one researcher finding.
- EF1–EF7 were the "edge programme". The account owner asked for a top-10 swing list and a top-10 scalp list per symbol, with every position held inside 18:00→16:00 ET.
- A manager adjudicated.

Most of the output is **harness forensics** (defects that manufacture false nulls), not edge. The only profitability measurements in the lane come from EF4 (MGC/MCL scalp), EF5 (MES/MNQ scalp) and EF6 (MGC 60m/15m top-10 attack and forward roll). EF2 and EF3 (swing 60m) built populations and then parked without reporting a number.

---

## 0. Bottom line

1. **No strategy in this lane cleared its multiple-testing threshold, on any symbol.**
   - Largest real t: +2.62 (MGC 15m, EF4), 3.116 (MNQ 15m, EF5), 1.965 (MGC 60m, EF6).
   - The largest t anywhere in EF5 (3.82) belongs to a **placebo**.
2. **Placebos (random entries through the same exits) match or beat the median real strategy in every scalp cell.** This held in EF4 (6/6 cells) and in EF5 (placebo ranked #1 in 7 of 12 arm-cells).
3. **Selecting a top 10 underperforms trading the whole qualifying universe.** This replicated under the new session rule, both on MGC 60m (EF6) and inside MNQ 15m (EF5).
4. **Level/bounce trading, as this library implements it, does not pay at 5m–30m on 41 sessions.** VWAP-band bounces lose in 6/6 cells and are worse than placebo in 6/6. Overnight-extreme sweep reversals lose to their own placebo at z≈−3 on MGC. The weak positives are all at 30m: MGC POC reversion (+0.20R, t 2.18), MGC value-area edge (+0.15R), opening-range fade (+0.13R). None is significant after deflation.
5. **The only result in the lane that clears deflation is a risk result, not an edge.** BT3 found that size-shrinking governors improve account survival at $50k: |z| 6.16 and 5.54 against free_t 2.23.
6. **Structural reason nothing can clear.** The scalp spans are 57.9 days (0.1585 y), so a search of ~465 variants needs an annualised Sharpe of about 8.8. The swing span is 718.9 days (1.97 y) and needs about 2.5. More search width cannot fix this; more span or pre-registration can (§6).

---

## 1. Thresholds every row below had to clear

`free_t(n) = sqrt(2·ln n)`, and the required annualised Sharpe is `free_t / sqrt(years)`. Source: `edge/EF6/code/deflation.py` and `edge/EF6/bursts/01_deflation-and-span.md`.

| n screened | scalp 5/15/30m (57.9 d, √y 0.398) | swing 60m (718.9 d, √y 1.403) | MES/MNQ daily (7.40 y, √y 2.72) |
|---|---|---|---|
| 1 (pre-registered) → t 1.177 | SR 2.96 | 0.84 | 0.43 |
| 10 → t 2.146 | 5.39 | 1.53 | 0.79 |
| 465 → t 3.505 | 8.80 | 2.50 | 1.29 |
| ~3,200 (EF2 MGC/MCL 60m population) → t 4.01–4.03 | — | 2.86–2.88 | — |
| ~4,000 (EF3 MES/MNQ 60m population) → t 4.07–4.08 | — | 2.90–2.91 | — |
| 19,152 (EF4 Track B) → t 4.441 | 11.16 | 3.17 | — |
| 21,060 (EF5 total) → t 4.462 | 11.2 | — | — |
| 2,975,629 (historical programme) → t 5.46 | 13.7 | 3.89 | 2.01 |

- **Do not quote 5.46 for this programme's searches.** The honest wording is "≥2,975,629 candidates generated, an unmeasured subset could not trade". The effective n is about 495k (free_t 5.15). Source: `BRIEF.md:230-244`.
- A single pre-registered hypothesis faces t ≥ 1.177. At 400 scalp trades that is net +0.06R per trade (σ≈1R). After costs, a scalp arm needs **gross +0.28R on MGC and +0.42R on MCL**. Source: `edge/EF4/FINDINGS.md` §1 and §3.

---

## 2. Per-symbol findings

Column meanings:
- "t thr" is the threshold that row had to clear.
- "WF/OOS" is walk-forward or split-sample.
- "Plac" is the placebo comparison.

Verdicts: S = SURVIVED, F = FAILED, I = INCONCLUSIVE.

Substrate for all EF rows: `data/archive/`. Scalp = 2026-07-29→09-25 (41 sessions). Swing = 2024-10-06→2026-09-25.

Every EF4 row uses the same fixed exit: `ATR 1.0` stop, one 1.5R target, a 24-bar time stop, `rth_only=False`, and a forced flat at 16:00 ET.

### 2.1 MGC (micro gold)

**Pre-registered Track A (EF4).** n=36 arms, t thr 2.677. Placebo = 20 count-matched random-bar placebos per arm.
- Sources: `edge/EF4/FINDINGS.md` §4 and §11, `edge/EF4/out/placebo_MGC_*.json`.
- IS/OOS split = first 25 of the 41 sessions vs the last 16.

| arm (rule) | tf | n | win | net E R | t | IS→OOS | z vs plac | verdict |
|---|---|---|---|---|---|---|---|---|
| A1_ON_SWEEP: bar pierces overnight H/L and closes back inside → fade | 5m | 87 | .230 | −0.457 | −4.00 | −0.54 / −0.31 | **−2.99** | F (significantly negative; continuation side implied, not pre-registered) |
| same | 15m | 50 | .300 | −0.317 | −2.02 | — | **−3.10** | F |
| same | 30m | 39 | .333 | −0.271 | −1.62 | — | −1.37 | F |
| A2_PD_SWEEP: pierce PDH/PDL, close back inside → fade | 5m | 250 | .360 | −0.151 | −1.98 | −0.19 / −0.10 | −0.37 | F |
| same | 15m | 140 | .364 | −0.119 | −1.19 | — | −1.20 | F |
| same | 30m | 106 | .406 | −0.015 | −0.13 | — | −0.12 | F |
| A3_VA_EDGE: tag prior-session VAL/VAH within 0.35 ATR, close back inside → fade | 5m | 132 | .386 | −0.097 | −0.91 | −0.11 / −0.08 | −0.05 | F |
| same | 15m | 79 | .392 | −0.032 | −0.24 | — | −0.15 | F |
| same | 30m | 60 | .467 | **+0.149** | +0.95 | — | +0.98 | I (the only positive Track A arm; 1.7 t short) |
| A4_VWAP_BAND: tag the 1st VWAP band, close back inside, still beyond VWAP → fade toward VWAP | 5m | 641 | .348 | −0.206 | **−4.32** | −0.22 / −0.19 | −1.49 | F (significantly negative) |
| same | 15m | 330 | .333 | −0.217 | **−3.38** | — | −1.94 | F |
| same | 30m | 192 | .385 | −0.098 | −1.17 | — | −0.74 | F |
| A5_ORB: opening-range breakout, after the OR | 5m | 489 | .378 | −0.132 | −2.46 | −0.02 / −0.31 | −0.49 | F (replicates the published ORB negative; negative gross too) |
| same | 15m / 30m | 201 / 131 | — | −0.129 / −0.208 | −1.60 / −2.21 | — | −1.03 / −1.25 | F (the 15m/30m opening range starts 10 min late: 08:20 open vs the grid) |
| A6_ON_COMPRESSION: close beyond PDH/PDL, gated by `volatility_compressed` | 5m | 264 | .299 | −0.358 | **−5.14** | −0.33 / −0.41 | **−2.69** | F |
| same | 15m / 30m | 101 / 69 | — | −0.258 / −0.265 | −2.23 / −1.93 | — | −1.53 / −0.75 | F |

**Track B broad screen (EF4).** 3,010–3,591 arms per cell, free_t 4.441. After de-duplication by signal set, 5 survivors were positive in-sample, out-of-sample and in every fold, but **none cleared the threshold**. Source: `edge/EF4/FINDINGS.md` §12 and `edge/EF4/out/rank_final.json`.

| # | tf | signal set | n | net E | t | OOS E (n) | folds | plac z | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 15m | candle_engulfing + structure_trend | 121 | +0.297 | 2.62 | +0.216 (46) | +.17/+.46/+.22 | +2.34 | F (needs 4.441; implied SR 6.58) |
| 2 | 30m | candle_close_strength + poc_reversion | 78 | +0.282 | 2.02 | +0.546 (32) | +.01/+.21/+.55 | +1.68 | F |
| 3 | 15m | above_vwap + poc_reversion | 87 | +0.241 | 1.78 | +0.137 (32) | +.15/+.45/+.14 | +2.16 | F |
| 4 | 15m | poc_reversion + pullback_to_support | 159 | +0.191 | 1.95 | +0.355 (62) | +.15/+.02/+.38 | +2.03 | F |
| 5 | 30m | imbalance_pullback | 170 | +0.188 | 2.08 | +0.169 (75) | +.09/+.28/+.18 | +1.90 | F |

- Rows 2–4 share `poc_reversion`, so they are not independent evidence.
- The top 10 in every cell is really "one or two conditions + eight variants".
- The selection effect also works in **reverse time**, so it is not forecasting (§7).

**EF6, MGC 60m swing.** 465 generated, `rth_only=False`, 18:00→16:00 enforced, t thr 3.505. Sources: `edge/EF6/bursts/05_forward-roll.md` and `06_attack-a-real-top-10.md`.
- In-sample top 10: t from +0.76 to **+1.965**. Expectancy +0.057 to +0.145R, n 84–180. Six of the ten are MULTI_TIMEFRAME, and two pairs are exact clones.
- G3 (deflation) killed 10/10. G4 (forward roll) killed 10/10. **Verdict F.**
- Forward roll, 180d lookback / 30d fold, 17 folds:

| arm | E |
|---|---|
| top-10 | +0.0255R |
| universe | +0.0302R |
| random-10 | +0.0069R |
| null | +0.0218R, z +0.14 |

  Selection loses to the universe in 4/4 configurations. It beats random-10 by +0.019 to +0.031R, so **concentration costs more than the ranking gains**.
- 46.2% of 8,150 trades exit on the 16:00 clock, not on stop or target.

**EF6, MGC 15m forward roll: the one "success".**
- Config: durability ranking, 28d lookback, 7d fold, floor 10.
- Result: top-10 +0.1346R vs universe +0.0306R, z = 2.48.
- **Verdict F.** The sign flips with the trade floor (floor 20 → −0.019R, floor 10 → +0.104R, floor 5 → −0.036R). It rests on 4 folds and 197 trades, sits below free_t 3.505, and was 1 of 9 configurations tried. Source: `edge/EF6/bursts/07_scalp-forward-test-and-the-one-success.md`.

**EF2, MGC/MCL 60m swing.**
- Populations: MGC 3,156 arms and MCL 3,408 arms (free_t 4.014 / 4.033, SR 2.86 / 2.88).
- **No profitability number was computed.** The agent parked because the harness was not yet validated.
- Useful facts:
  - 62–68% of surviving arms never fire.
  - The median live MGC arm fires 12–13 times in 718 days.
  - VWAP_BAND stops collapse to the min-stop floor on 19.2% of MGC 60m bars. STRUCTURE stops collapse on 3.8%.
- Source: `edge/EF2/FINDINGS.md` §PARKED.

**Published claims about MGC that R6 audited** (they originate in `scan_reports/`, outside this lane; R6's status is given). Source: `research/R6_report_audit.md`.

| claim | R6 status | why |
|---|---|---|
| A12: "every MGC group loses money on median" | STANDS | — |
| A13: MGC 1h VOLUME_PROFILE n=28, win 71.4%, E +0.295, t 1.53 | WEAKENED | `in_value_area` flips on 4.1–7.4% of bars depending on which CSV built the profile |
| A10: MGC 15m/30m is the worst cell (<10% of strategies profitable) | STANDS on `csv/raw` | contradicted by EF4 on archive: 36–38% positive at MGC 15m/30m (§8) |

**BT3.** On a $50k account the integer-contract floor deletes **99.42% of MGC 4h trades** (the median position size is 0 contracts). So MGC 4h strategies cannot trade at that size. Source: `backtest/BT3/ALGOS.md` §PARKED.

**MGC top 5 by strength of evidence** (none cleared its threshold):
1. `candle_engulfing + structure_trend` 15m: t 2.62, OOS +0.216, placebo z +2.34.
2. `poc_reversion` family at 15m/30m: rows 2–4 plus the single-condition 30m result (+0.199R, t 2.18). Profile reversion toward POC is the one level concept with a consistent positive sign on MGC at 15–30m.
3. `imbalance_pullback` 30m: t 2.08, placebo z +1.90.
4. A3_VA_EDGE 30m: +0.149R, the only positive pre-registered arm.
5. The EF6 60m MULTI_TIMEFRAME cluster (+0.14R, t 1.9). This is a long-bias proxy on a rising gold tape.

### 2.2 MCL (micro crude)

**EF4 Track A (MCL).** t thr 2.677. Source: `edge/EF4/out/placebo_MCL_*.json`.

| arm | 5m n / net E / t / plac z | 15m | 30m |
|---|---|---|---|
| A1_ON_SWEEP | 68 / −0.128 / −0.85 / +0.96 | 42 / −0.151 / −0.83 / −0.25 | 32 / −0.038 / −0.19 / +0.02 |
| A2_PD_SWEEP | 174 / **−0.418 / −4.68 / −2.32** | 106 / −0.019 / −0.16 / +1.24 | 78 / −0.137 / −1.05 / −0.57 |
| A3_VA_EDGE | 117 / −0.110 / −0.94 / +0.55 | 75 / −0.282 / −2.11 / −1.04 | 51 / **+0.071** / +0.43 / +0.84 |
| A4_VWAP_BAND | 622 / −0.262 / **−5.29** / −1.33 | 359 / −0.209 / **−3.33** / −1.14 | 211 / −0.137 / −1.69 / −0.96 |
| A5_ORB | 441 / −0.199 / −3.43 / +0.10 | 206 / −0.122 / −1.51 / −0.40 | 147 / −0.121 / −1.33 / −0.30 |
| A6_ON_COMPRESSION | 202 / −0.243 / −2.76 / +0.13 | 101 / −0.235 / −1.93 / −0.34 | 58 / −0.163 / −1.03 / −0.27 |

All are F. MCL's opening range is clean on the grid because it opens at 09:00, so A5 is a genuine ORB test here.

**EF4 Track B (MCL).** Only 3 survivors, all at 30m, and all below even the n=1 floor of 1.177. **On MCL the answer is nothing, at every threshold.**

| # | signal set | n | net E | t | OOS E (n) | plac z |
|---|---|---|---|---|---|---|
| 1 | delta_divergence + keltner_outside 30m | 95 | +0.127 | 1.00 | +0.193 (37) | +1.13 |
| 2 | bollinger_extreme 30m | 152 | +0.114 | **1.12** | +0.125 (66) | +1.18 |
| 3 | candle_engulfing + value_area_breakout 30m | 74 | +0.090 | 0.63 | +0.014 (30) | +1.23 |

**MCL cost facts.** Source: `edge/EF4/FINDINGS.md` §3 and §8.
- The min-stop floor of 15 ticks makes **22.9% of R the minimum RTH cost and 36.3% the minimum thin-book cost**.
- Median cost at 5m is 0.20R.
- MCL 5m: 2.9% of arms are net-positive. 0.13% are positive in all 3 folds, and 76.4% are negative in all 3.

**MCL substrate.**
- MCL has no daily history on Yahoo (`MCL_1440m` = 1 row). `CL=F` is not a substitute: mean close difference 0.95¢, worst 4¢. Also `CL_1440m` has a negative-price region (−37.63 on 2020-04-20).
- The 60m series is 89.5% complete. It has runs missing on 2026-01-09→01-16 and 2026-02-20→03-11, and 2026-02-02 carries only 3 of 22 hours (shared with MGC, so it is a vendor gap).
- The median live 60m arm fires only 4–5 times in 718 days.
- Sources: `BRIEF.md` and `edge/EF2/FINDINGS.md` F9.

**MCL top 5 by evidence** (all F):
1. `bollinger_extreme` 30m (t 1.12).
2. `delta_divergence + keltner_outside` 30m.
3. Opening-range fade 30m (+0.131R, n 61, single condition).
4. A3_VA_EDGE 30m (+0.071R).
5. `vwap_reclaim` 30m (+0.072R, n 168).

Every one of them is a 30m, mean-reversion-to-level shape. At 5m and 15m, everything on MCL is cost-dominated.

### 2.3 MES (micro S&P)

**EF5 scalp, qualifying universe per arm-cell.** Floor 20 trades, clone-collapsed, net of costs. "SESSION" means `rth_only=False`. Source: `edge/EF5/bursts/10_*.md` §2.

| cell | n rows | mean net E | % positive | placebo universe | IS / OOS | best t |
|---|---|---|---|---|---|---|
| 5m RTH | 38 | −0.045 | 34% | −0.127 | −0.069 / +0.028 | 1.10 |
| 5m SESSION | 107 | **−0.191** | 14% | −0.212 | −0.264 / −0.086 | 1.28 |
| 15m RTH | 15 | +0.075 | 53% | −0.043 | −0.038 / +0.309 | 2.11 |
| 15m SESSION | 50 | −0.046 | 34% | −0.146 | — | 2.09 |
| 30m RTH | 7 | +0.103 | 100% | −0.188 | — | 1.53 |
| **30m SESSION** | 35 | **+0.121** | 86% | −0.146 | +0.147 / +0.098 | 1.87 |

**EF5 pooled MES table.**
- Search 10,134, free_t 4.295, required SR 10.79.
- Best placebo ranked 4th against a null of 3.14. The largest t in the pooled table (2.60) is a placebo's.
- Real #1: MOMENTUM 15m RTH, n 42, +0.337R, t 2.11.
- Real #2 and #3: the same LIQUIDITY rule in both `rth_only` arms (byte-identical double count), n 29, +0.402R, t 2.09.
- **Verdict F.** Source: `edge/EF5/bursts/11_*.md`.

**EF3, MES/MNQ 60m swing.** Populations: MES 4,168 and MNQ 3,868 at 60m (free_t 4.083 / 4.065, SR 2.91 / 2.90).
- The stage-1 ledger exists and is **embargoed**: 53,252 MES trades and 49,939 MNQ trades in `edge/EF3/out/stage1_*_gap.json`.
- **Placebo stage never run. Verdict I (unmeasured).** Next step: `python3 edge/EF3/code/ef3_stage2.py MES MNQ`, then `ef3_rank.py`.
- 50 MES / 83 MNQ rows clear IS n≥30 with IS E>0. Only 28.0% / 27.1% of each population traded at all.

**Published MES claims (R6 audit).**

| claim | R6 status |
|---|---|
| A3 "MES 1h TREND is the most durable result" | already retracted (a trade-floor artefact; inverts at n≥40, z −1.93) |
| A15 MES 4h VWAP rows | WEAKENED strongly (1 in 5 bars at 4h has zero-width bands) |
| A16/A17 daily VWAP and daily MTF | INVALID (degenerate) / WEAKENED (D50) |

R1 also cites from the deep scan (outside this lane): MES 1h VOLUME_PROFILE n=20, E +0.448, t 3.04; MES 15m VP n=24, +0.312, t 2.00. Both sit under the programme-wide null.

**MES substrate.** MES/MNQ daily (7.40 y, 2019-05→2026-09) is the **only roll-clean long series** in the repo. Source: `workspace/studies/SERIES_AUDIT.md`, via `BRIEF.md`.

**MES top 5 by evidence** (all F or I):
1. The 30m SESSION universe as a whole: +0.121R, 86% of 35 rows positive, positive in IS and OOS, far above its placebo universe (−0.146). This is the best-behaved cell-level result on the index.
2. MOMENTUM 15m RTH, +0.337R, t 2.11.
3. LIQUIDITY 15m (+0.402R, n 29), an `initial_balance_break`-type rule.
4. The EF3 60m ledger (unmeasured).
5. The published MES 1h VOLUME_PROFILE row (t 3.04, but weakened by D-P2).

### 2.4 MNQ (micro Nasdaq)

**EF5 universe.** Source: `edge/EF5/bursts/10_*.md`.

| cell | n rows | mean net E | % positive | placebo universe | IS / OOS | best t |
|---|---|---|---|---|---|---|
| 5m RTH | 48 | −0.044 | — | **+0.013** (placebo wins) | — | — |
| 5m SESSION | 156 | −0.053 | — | −0.056 | — | — |
| 15m RTH | 7 | +0.011 | — | **+0.169** (placebo wins) | — | — |
| **15m SESSION** | 72 | **+0.099** | 65% | −0.024 | +0.027 / +0.189 | 3.116 |
| 30m RTH | 8 | −0.154 | — | +0.001 (placebo wins) | — | — |
| 30m SESSION | 35 | +0.029 | — | +0.007 | — | — |

**MNQ 15m SESSION stress test** (the one cell in 12 where reals beat their own placebos; 25/31 pairs, sign z +3.41). Source: `edge/EF5/bursts/08_*.md`. **Verdict F** (a regime-conditional long bias).

| test | result | outcome |
|---|---|---|
| Leak-free holdout: select on 24 IS cycles, read 17 OOS | OOS real +0.245R vs placebo −0.014R, z +3.05 | survives |
| Direction-shuffle control | z +4.13; shorts also beat their placebo (z +4.32) | survives |
| Effective sample size | trade Jaccard 0.087 → n_eff 8.56 of 31 → deflated z 2.17 vs free_t(12) 2.229 | **fails** |
| Contiguous thirds | +9.25% tape → z +4.38; **−1.69% tape → z +0.19**; +3.86% tape → z +2.69 | **fails** (no effect in the down-tape third) |

- **Inside this cell, selection is worse than no selection:** the in-sample top 10 read OOS gives +0.220R vs the universe's +0.298R.
- The top 10 is all MULTI_TIMEFRAME with a long share of 0.73–0.82, on a tape that rose +12.19%.
- EF5 retracted its own first holdout (sign z 6.19) because it had gated on full-span t.

**EF5 pooled MNQ table.** A placebo ranks #1 (+0.777R, t 3.82, implied SR 9.59). 4 of the top 10 are placebos. Search 10,926, free_t 4.313.

**Roll hazard.** There is no roll audit inside the 57 days, and MNQ's +12.19% drift carries the result. Check ES/NQ roll dates against the 41 cycles.

**MNQ-specific defects.**
- 17.79% of the MNQ 60m population is VOID; the cause is `openinterest` via the MOMENTUM/BREAKOUT templates, not the market.
- VWAP_BAND stops collapse to the floor on 7.47% of 60m bars (vs 15.38% on MES).
- Source: `edge/EF3/FINDINGS.md`.

**MNQ top 5 by evidence:**
1. The MNQ 15m SESSION universe: +0.099R, 65% positive, OOS +0.189, real beats placebo z +3.05 OOS. **Fails** on n_eff and on the regime split.
2. The MULTI_TIMEFRAME 15m SESSION rows (+0.46 to +0.64R, t 2.1–3.1). These are a long-bias proxy.
3. `range_position_extreme` rows in EF5: 47 floored rows with mean +0.219R. They are selection-gated (t≥0), so not a clean estimate.
4. The MNQ 30m SESSION universe: +0.029R.
5. Nothing else.

### 2.5 NQ / ES (full size)

No measurement in this lane beyond R6's audit of published claims:
- A11/A18, "NQ 1h OPENING_RANGE +0.070 median, positive across windows": **INVALID (SUBSTITUTED)**. At 1h the opening range exists on only 10 bars, all on Thanksgiving Friday and Christmas Eve. The template silently drew another liquidity condition instead.
- A19, "NQ 1h VOLUME_PROFILE / VWAP positive across windows": WEAKENED. The value area disagrees on 10.5% of bars between 5m and 60m, and the POC differs by about 100 ticks.

Remember:
- NQ/ES/MNQ/MES are **one index complex**. Their populations share only 0.5–0.8% of rule sets, and agreement between them is one observation, not two.
- `MNQ=F` is not TradingView's `MNQ1!` (different roll convention).

### 2.6 Grains (MZC / MZS / MZW)

**NOT ELIGIBLE, and nothing was tested.** Two independent reasons:
- D40 contract-month splicing.
- Degenerate bars: `MZC_1m` 88.7% rangeless, `MZC_5m` 62.9%, `MZC_1h` 26.3% rangeless plus 11.3% zero-volume.

The wheat-corn spread (II-4) is nominally constructible but blocked on the same grounds. Sources: `BRIEF.md` roll/scale audit, `discovery/AVENUES.md` II-4.

### 2.7 Other series

- **SPY/QQQ intraday volume:** not eligible (58–59% of 1h/5m bars have volume 0).
- **MGC daily:** fails the roll audit in either store (gap sum +2.96 vs intraday −2.01; p<0.0001).
- **`data/archive/MGC_1440m` bars 0–383:** spliced at 10.145×.
- **`data/MGC_1m.csv` etc. (2019–2020):** Oanda CFD data, not futures. Its volume is a tick count.
- Source: `BRIEF.md` §"roll and scale audit" and `workspace/studies/SERIES_AUDIT.md`.

---

## 3. LEVELS: support/resistance, bounce, sweep, PDH/PDL, VWAP, S/D, fib, volume profile

### 3.1 What each level condition actually computes

Source: `futures_agents/strategies/library.py`, audited in `research/R1_group_audit.md`.

| condition | rule as coded | audit verdict and firing rate |
|---|---|---|
| `prior_day_sweep` | bar low < PDL ≤ close → LONG; high > PDH ≥ close → SHORT (a pierce-and-reclaim in one bar) | CLEAN arithmetic. Fires 4.3–13.2% of bars. PDH/PDL come from RTH bars, so unavailable on daily (D23). |
| `overnight_sweep` | same, on the overnight H/L | Fires 1.4–5.1%. **D36: the reference level includes the current bar** in the library. A causal reimplementation fires 9.3–12.3% vs the library's 4.7% RTH. EF4's A1 uses the library version. |
| `session_extreme_sweep` | same, on the running session H/L | **Broken/VOID.** It is self-referential, so it can only fire after the RTH close. All 48 fires in EF5 fall at 16:00–16:55 ET, inside the forbidden window. VOID under `rth_only=True`. |
| `prior_day_breakout` | close beyond PDH/PDL | A *state*, not an event: fires 41–52% of bars. |
| `initial_balance_break` | break of the first-60-minute range | 13.8–17.4%. Survives where the OR conditions die. |
| `opening_range_breakout/_fade` | 30-minute OR, hard-coded | **Dead at 1h on MGC (0/5000) and on MNQ/MES (2 holiday dates only).** On MCL 1h the range is 60 minutes wide but labelled 30. At 15/30m the MGC OR covers minutes 10–40 after the open. |
| `pullback_to_support` | close within 0.5 ATR of the nearest `sr_level` (≥2 touches, up to 12 levels), on the correct side | CLEAN. Touch count feeds a conviction score only; **no test by touch count exists.** |
| `zone_touch` / `fresh_zone_approach` | inside a demand/supply zone (base plus a 2× departure bar, 400-bar expiry) / an untested zone approached within [−0.1, 0.75] ATR | CLEAN, but **scarce: 1.6–3.8% and 0.8–1.4% of bars**. SUPPLY_DEMAND could never reach 20 trades (0 of 6 cells). Too scarce to test. |
| `poc_reversion` | inside the prior-session value area, POC ≥ 0.5 ATR away → trade toward POC | DEGRADED (D-P2). The profile smears each bar's volume uniformly over its range. The POC for the same day moves up to 2.02 ATR (MCL), 1.74 ATR (MES) or 0.47 ATR (MGC) depending on which CSV built it. **Dead at 4h and daily.** |
| `value_area_edge` | tag VAL/VAH within 0.35 ATR and close back inside → fade | Fires 1.9–5.2% of bars. |
| `value_area_breakout` | close beyond VAH/VAL by 0.25 ATR | 44.8–61.4%. Near-information-free; "one condition wearing six names". |
| `lvn_rejection` | at an LVN within 0.3 ATR, direction from the bar body | Near-VOID: 6–21 fires. |
| `vwap_band1_bounce` | tag the ±1σ session-VWAP band and close back inside, still beyond VWAP → trade toward VWAP | CLEAN, except **dead on the first bar of every trading day** (zero-width band, D-VW2) and **0 fires on daily (D52)**. |
| `vwap_reclaim` | reads VWAP only | CLEAN. |
| `above_vwap` | outside band 1 (can return SHORT) | **MISNAMED.** At daily frequency it equals `2C > H+L`. |
| `fib_golden_pocket` / `fib_shallow_retrace` | close in the 0.618–0.786 / 0.382–0.5 retrace of `swing_leg()` | DEGRADED. **`swing_leg` spans other swings on 14.4–17.2% of bars.** |
| `fib_sr_confluence` | any of 4 ratios within 0.4 ATR of any S/R level | Passes 56.8–80.2% of bars; covers **100% of the leg on the median bar**. Not a filter. |
| round numbers | — | **Not implemented as a condition anywhere.** `futures_agents/scanners/breach.py` mentions them. No measurement in this lane. |
| anchored VWAP | `indicators/volume.py:317-435` | **Built and tested, wired to nothing.** RTH-anchored and weekly VWAP are also unreachable (only the Globex session anchor is used). Never tested. |

### 3.2 Does a level bounce? The single-condition table

**This is new aggregation work by this sweep, not a published result.**
- Source: `edge/EF4/out/run_{MGC,MCL}_{5,15,30}m_both_summary.json`, rows whose `conditions` hold exactly that one condition and no filter.
- Exit: ATR 1.0 stop, 1.5R target, 24-bar time stop. `rth_only=False`. Data: 41 sessions (2026-07-29→09-25).
- Each cell shows **net E (n, t)**. Δ is net E minus that cell's count-matched placebo mean:

| cell | placebo mean net E |
|---|---|
| MGC 5m | −0.131 |
| MGC 15m | −0.012 |
| MGC 30m | −0.023 |
| MCL 5m | −0.220 |
| MCL 15m | −0.112 |
| MCL 30m | −0.065 |

The cell threshold is 4.441 and **nothing is near it**.

| condition | MGC 5m | MGC 15m | MGC 30m | MCL 5m | MCL 15m | MCL 30m | Δ vs placebo, sign count |
|---|---|---|---|---|---|---|---|
| vwap_band1_bounce | −.206 (641, −4.3) | −.217 (330, −3.4) | −.098 (192, −1.2) | −.262 (622, −5.3) | −.209 (359, −3.3) | −.137 (211, −1.7) | **0/6 above placebo** |
| prior_day_sweep (bounce) | −.151 (250) | −.119 (140) | −.015 (106) | −.418 (174, −4.7) | −.019 (106) | −.137 (78) | 2/6 |
| prior_day_breakout (break) | −.172 (1095, −4.7) | −.177 (431) | −.148 (253) | −.198 (1093) | −.116 (465) | −.124 (252) | 1/6 |
| overnight_sweep (bounce) | −.457 (87, −4.0) | −.317 (50) | −.271 (39) | −.128 (68) | −.151 (42) | −.038 (32) | 2/6; MGC z −3 |
| initial_balance_break | −.121 (371) | −.081 (159) | −.143 (103) | −.242 (358) | −.143 (161) | −.163 (121) | 1/6 |
| opening_range_fade | −.082 (155) | −.029 (95) | **+.125** (62) | −.297 (155) | +.002 (79) | **+.131** (61) | 4/6 |
| pullback_to_support (S/R) | −.158 (898, −3.9) | +.019 (323) | −.105 (171) | −.266 (844, −6.3) | −.070 (282) | −.043 (123) | 3/6 |
| range_position_extreme | −.105 (882) | +.003 (287) | −.078 (142) | −.212 (730) | −.232 (298) | −.107 (139) | 3/6 |
| zone_touch (S/D) | −.098 (82) | — | — | −.378 (119, −3.5) | — | — | 1/2 |
| poc_reversion | −.056 (1099) | +.026 (369) | **+.199 (180, +2.18)** | −.206 (666) | −.195 (264) | −.051 (139) | 4/6 |
| value_area_edge | −.097 (132) | −.032 (79) | **+.149** (60) | −.110 (117) | −.282 (75) | +.071 (51) | 4/6 |
| vwap_reclaim | −.063 (382) | +.092 (215) | +.035 (166) | −.268 (374) | −.153 (259) | +.072 (168) | 4/6 |
| fib_golden_pocket | −.168 (566) | −.152 (190) | −.292 (94) | −.183 (483) | −.314 (187, −3.8) | −.294 (92) | **1/6** |
| fib_shallow_retrace | −.035 (547) | −.039 (176) | +.020 (102) | −.260 (485) | −.063 (184) | −.093 (95) | 3/6 |
| fvg_nearby | −.122 (261) | −.009 (79) | −.073 (41) | −.224 (288) | −.078 (106) | +.041 (55) | 4/6 |
| bollinger_extreme (band fade) | −.164 (887) | −.032 (327) | +.008 (139) | −.182 (755) | −.044 (288) | **+.114** (152) | 4/6 |

**Gross-of-cost values** (same source) for the two best-known level trades:

| condition | MGC 5m | MGC 15m | MGC 30m | MCL 5m | MCL 15m | MCL 30m |
|---|---|---|---|---|---|---|
| prior_day_sweep | −0.061 | −0.066 | +0.021 | −0.221 | +0.100 | −0.050 |
| vwap_band1_bounce | −0.104 | −0.162 | −0.062 | −0.039 | −0.072 | −0.048 |

So **the VWAP-band bounce loses even before costs** in all 6 cells.

### 3.3 Why a level holds or breaks: what the measurements say

1. **At PDH/PDL neither side pays at 5–30m.**
   - Fading the pierce (`prior_day_sweep`) gives net −0.02 to −0.42R. Trading the acceptance (`prior_day_breakout`) gives −0.12 to −0.20R.
   - Gross, both sides sit near zero (breakout gross −0.13 to +0.00).
   - So on 41 sessions of MGC/MCL, a prior-day extreme is **not** a level where the next 1.5R move is predictable in either direction. Source: §3.2.
2. **A sweep predicts the move worse than no touch at all.**
   - Published ICT study (cited and upheld by R6 C5): 1,893–2,014 sweeps produced 77–106 retraces per symbol in 10.5 months.
   - "At matched distance, sweeping liquidity predicts the shift **slightly worse than never touching a level at all** (MH OR 0.86)."
   - Swapping the order of the stages trades the same and ranks first.
   - Source: `research/R6_report_audit.md` C5, from `workspace/studies/ORB_ICT_FINDINGS.md`.
3. **Fading an overnight-extreme sweep is anti-informative on MGC.**
   - Real vs its own random-entry placebo: z −2.99 (5m) and −3.10 (15m).
   - Same exits, same sizing, so the entry location itself is worse than random. The *continuation* side is implied at |t| = 4.00, but it was not pre-registered.
   - Caveat: EF4 used the library `overnight_sweep`, which D36 flags as self-referential. Source: EF4 §4 and §11.
4. **VWAP ±1σ bounces fail everywhere.**
   - Gross is negative in 6/6 cells, and the arm sits below placebo in 6/6.
   - Two mechanisms are documented. (a) The band is zero-width on the first bar of each trading day and on 19.8–20.2% of 4h bars. (b) A VWAP_BAND *stop* collapses to the fixed min-stop floor on 5.8–6.2% of MES RTH bars, 14.6% of MES session bars, 19.2% of MGC 60m and 37.2% of MCL 60m bars.
   - R1's operating note: on trend days VWAP stays beneath price all day and every fade loses. Sources: `research/R1_group_audit.md` D-VW2, `edge/EF5/bursts/03_*`, `edge/EF2/FINDINGS.md` F6.
5. **Profile reversion toward POC and the value-area edge are the only level shapes with a consistent positive sign, and only at 30m.**
   - MGC 30m: `poc_reversion` +0.199R (n 180, t 2.18); `value_area_edge` +0.149R.
   - MCL 30m: +0.071R. `poc_reversion` also carries 3 of MGC's top 5 Track-B rows.
   - At 5m the same conditions lose. Placebo gross is also negative at 5m on both symbols, so the 5m loss belongs to the **exit geometry on a 5m grid plus cost, not to the level**.
   - None clears 4.441. Also, POC/VA location depends on which CSV built the profile (D-P2).
6. **Day type decides hold vs break, and it is symbol-specific.**
   - Mechanical IB classification over 41 RTH sessions (IB = first hour; trend = one-sided extension ≥ 1×IB):

| symbol | trend | normal-variation | neutral |
|---|---|---|---|
| MCL | **43.9%** | 19.5% | — |
| MGC | 36.6% | 36.6% | — |
| MES | 14.6% | 51.2% | 29.3% |
| MNQ | 12.2% | 58.5% | — |

   - Level fades should fare worst on MCL, whose modal day is a trend day, and best on MES/MNQ. Descriptive only; no expectancy was attached. Source: `research/R1_flow_auction.md` §"five day types".
   - The four opening types (Open-Drive, Test-Drive, Rejection-Reverse, Auction) are forward-assignable if the classification window is fixed. `open_outside_value` implements one of them **and has never been reported**.
7. **Fib levels carry no information as implemented.**
   - `fib_golden_pocket` is negative in 6/6 cells (−0.15 to −0.31R) and below placebo in 5/6.
   - `fib_sr_confluence` passes 57–80% of bars. The published "Fib-level bars indistinguishable from plain S/R bars" STANDS.
   - The swing leg is wrong on about 1 bar in 6, so "fib as drawn by a trader" remains untested.
8. **Supply/demand zones are untestable at this sample size.**
   - Fires 0.8–3.8% of bars. 0 of 6 published cells reach 20 trades.
   - `zone_touch` gives MGC 5m −0.098R (n 82) and MCL 5m −0.378R (n 119).
   - ICT's base-free order block fires on 40.5–51.5% of bars. Random zones get revisited **87–90%** of the time, so the "80–90% fill rate" is true and carries no information (C9).
9. **Pullbacks to support/resistance** (`pullback_to_support`) are negative at 5m (−0.16 / −0.27R, t −3.9 / −6.3) and flat at 15–30m. No test separates levels by touch count, freshness or recency, even though `support_resistance()` stores `touches` and a `strength` value.
10. **Adding multi-timeframe alignment to level trades** (EF4 paired test, 12 pre-registered pairs, Wilcoxon z −0.51, p 0.61) has no detectable effect. It deletes 69% of trades: ON_SWEEP goes from 87 to 2 trades on MGC and from 68 to 1 on MCL.

**Level ideas never tested here:**
- anchored VWAP, RTH-anchored VWAP, weekly VWAP;
- composite/naked POC;
- round numbers;
- touch-count-conditioned S/R;
- multi-bar sequences (the combinator cannot express "sweep then reclaim within N bars", D37);
- sweeps conditioned on resting size (no depth data).

`discovery/AVENUES.md` rows I-9, I-10, I-11 and III-5 are the open avenues.

### 3.4 Index-complex level evidence (EF5)

EF5 gated rows at n≥20 and t≥0, so real and placebo are equally selected and only the comparison is meaningful. Mean net E, real vs placebo:

| symbol, group | real mean E (n rows) | placebo mean E (n rows) |
|---|---|---|
| MES LIQUIDITY | +0.162 (6) | +0.130 (7) |
| MES VOLUME_PROFILE | +0.169 (6) | **+0.197** (2) |
| MES VWAP | +0.118 (8) | +0.064 (3) |
| MNQ LIQUIDITY | +0.173 (4) | +0.164 (5) |
| MNQ VOLUME_PROFILE | +0.098 (30) | **+0.145** (20) |
| MNQ VWAP | +0.066 (11) | **+0.077** (9) |

**Level groups are indistinguishable from random entries on the index complex.** Source: `edge/EF5/out/PROVISIONAL_measure_all.json`, aggregated by this sweep.

---

## 4. Cross-symbol results

| finding | numbers | source |
|---|---|---|
| Selection (top-10) vs universe | MGC 60m: top-10 below universe in 4/4 configs. MNQ 15m: 0.220 vs 0.298. Historical: −0.0155R vs −0.0104R null. EF4 reverse-time selection "wins" 6/6 cells, so it detects within-window stationarity, not a forecast. | EF6 b05, EF5 b08, EF4 §7 |
| Placebo ≥ median real | EF4: placebo beats the median in 5/6 cells and ties 1. EF5: placebo universe beats real in 3 MNQ RTH cells; placebo is rank 1 in 7/12 arm-cells. | EF4 §11, EF5 b08/b10 |
| Rule 7 ("sub-hourly graveyard") | Holds at **5m only**: MGC 12.2% and MCL 2.9% of arms net-positive, vs MGC 15m/30m 36.0/37.8% and MCL 30m 23.9%. The gross half of the effect is **exit geometry on the 5m grid** (placebo gross −0.038 / −0.018 at 5m). | EF4 §8/§11 |
| Cost in R | MES 5m median 21.0% of R (39.4% at the tightest geometry); MNQ 5m 4.78%; MGC 5m 0.093R; MCL 5m 0.202R. The old "15% at 5m" figure was commission only. | EF4 §3, RESULTS.md |
| Multi-timeframe agreement | EF4 paired test: Δ +0.014R, p 0.61, retention 0.31. Rule 2's z −4.09 → **−3.05 without the daily cells** (D50), so the sign survives. | EF4 §9, BT4 §6 |
| Clock exits | Swing 60m: 46–76% of trades exit on the 16:00 flat. `TIME` exits: 0 of 103,191. Scalp: the stop is the dominant exit in 11/12 cells (the clock only 2.8–30.8%). | EF6 b05, EF2 F10, EF3, EF5 b09 |
| `rth_only=False` | 2.5–2.9× the raw signals; the SESSION arm is better populated in 12/12 scalp cells. D24's "costs expectancy" was measured under a different session regime and may not transfer. **The one open arm worth running (60m, paired).** | RESULTS.md |
| Win rate vs payoff cancel | Seen again in EF6 (50% / +1.15 / −0.98 vs 59.5% / +0.68 / −0.64, same E) and in BT5's activity strata. | EF6 b06, BT5 |
| Activity stratification (MAIN-01/S2) | Bar-level: high-activity bars move 2.1–3.3× further while ATR is only 1.14–1.75× wider. Strategy level: Δ E +0.018R, p 0.58. **Null for expectancy.** | BT5 ALGOS |
| Account governors (BT3) | $50k account: the integer floor deletes 41.19% of 21,954 trades (MGC 4h 99.42%, MNQ 4h 94.59%). Absorbing state at a $2,800 drawdown (budget $21.60 < $25 minimum), leaving $2,200 of the failure allowance unspendable. Size-shrinking governors improve survival at |z| 6.16 / 5.54 (**the only deflation-clearing result; a risk result, not an edge**). | BT3 ALGOS §PARKED |
| Scheduled events (BT2) | In-session HIGH-impact event days: MGC 32 and MCL 49 (`csv/raw`); 69 and 164 on the archive, vs MNQ's 7. `outside_news_blackout` is an exact no-op on MGC at 60m. **No backtest run.** | BT2 ALGOS/bursts |
| Absorption shape (BT1) | Volume ≥ 2× and range ≤ 1× the 20-bar norm fires only 2–41 times per series, under the 20-trade floor in 4/6 cells. Unmeasurable; fidelity never confirmed. | BT1 ALGOS/VERIFY |
| Session exit (`exit_at_session_close` off) | The largest single effect published (paired sign z +3.52). R6: STANDS. EF7: the shipped exit closes any entry at or after 12:30 ET on its **entry bar**. | R6 B5, EF7 |
| No entries 15:00–16:00 ET | z −4.43, median −0.617R (published); R6: WEAKENED to per-symbol scope. | R6 B8 |

---

## 5. Infrastructure facts and pitfalls

### Data and vendor
1. **Timezones differ between stores.** `csv/raw` is UTC (`+00:00`); `data/archive/` is ET (`-04:00`). Normalise to UTC before comparing, or you get fake 23-point MGC differences.
2. **The two stores agree bit-exactly only for MNQ/MES at 60m.** MGC/MCL differ by 3.4e-7 / 4.8e-8 (float32). Compare with a tolerance, never `==`.
3. **The archive adds history only at 60m.** At 60m it adds about 6,000 bars before `csv/raw`. At 1m it adds 0: Yahoo caps 1m at 7 days, so the total futures 1m substrate is about 6.6 trading days.
4. **Spans by timeframe:** 5/15/30m = 57.9 d; 60/240m = 718.9 d; daily MGC 15.98 y (but spliced and roll-dirty), MES/MNQ 7.40 y (clean), MCL none.
5. **Yahoo quirks:** futures need the `=F` suffix; asking beyond the lookback cap returns an empty frame with no error; there is no native 3m or 4h bar (240m is resampled); `auto_adjust=False` and **no roll handling**.
6. **Run `workspace/roundtable/lib/scale_audit.py` before using any long series.** It found MGC_1440m spliced at index 383/384 (10.145×).
7. **Archive hourly completeness:** MGC 93.3%, MCL 89.5%. 2026-02-02 has only 3 of 22 hours on both contracts (a vendor gap), and `csv/raw` has the same hole.
8. **Five early-close half-sessions** (e.g. 2024-11-29, 2025-12-24) put `:30` bars in the archive 60m grid. `csv/raw` has 8 such bars.
9. **`csv/raw` hourly bars with zero volume:** 3.55–3.95%.
10. **`open[i+1] ≠ close[i]`** on 57–80% of contiguous boundaries. On MGC 60m this sums to +0.5386, which is 112% of the series' total log return. Fills at the next open carry a direction-dependent asymmetry of about 1–1.5% of R at 60m. The median gap is 1 tick at scalp timeframes.

### Harness defects

Each of these either produces a **false null** or mislabels a result. Ids follow `workspace/studies/DEFECTS.md` and `manager/ADJUDICATIONS.md`.

- **D48 / D55.** `dataclasses.replace` inherits the memoised `_id`. Passing `_id=None` is necessary but not sufficient, because `strategy_id` hashes condition *names*; EF4 saw 400–540 placebo collisions per cell. **Assert arm-id uniqueness at emission.**
- **D45.** The `min_stop_ticks` clamp (`base.py:313-315`) silently turns VWAP_BAND and STRUCTURE stops into fixed-tick stops. Floors: MGC 25 ticks, MCL 15, MES 8, MNQ 16. At 5m, "0.5 ATR" is below the floor on MGC and MCL.
- **D49.** `StopKind.RANGE` equals `StopKind.ATR` at 1h.
- **D50.** `align_bucket` ignores `minutes` for requests ≥1440, so the "weekly" confirm series is the daily series lagged.
- **D51.** `BarSeries.append` silently replaces a bar on an equal timestamp.
- **D52.** Daily VWAP bands are zero-width, so the `vwap` group becomes a bar-shape group and `vwap_band1_bounce` fires 0/2,511. 2,126 daily strategies were certain zero-trade.
- **D36.** `session_extreme_sweep` and `overnight_sweep` are self-referential.
- **D-L1.** The opening range is hard-coded to 30 minutes and missing at 1h. **D30:** the OR is never built at 60m/240m.
- **D-P1 / D5.** The profile needs ≥10 prior-session bars, so it is dead at 4h and daily.
- **D23.** PDH/PDL are unavailable on daily bars.
- **D-F1.** The fib swing leg is wrong on about 1 bar in 6.
- **D-V1 / D-V2.** `volatility_compressed` reads ATR percentile, not Bollinger width. BREAKOUT combined with `volatility_expanding` is empty by arithmetic.
- **VOID at MES 15m under `rth_only=True`.** `volatility_compressed` is VOID there, so all 138 BREAKOUT strategies take 0 trades.
- **D-MTF1–3.** MTF conditions are VOID at the frame's top timeframe, and `mtf_not_conflicted` ignores `tf`.
- **D-T1.** `avoid_lunch` blocks MGC's last 90 minutes of RTH.
- **D-T2.** `after_opening_range` passes outside RTH.
- **D57.** `outside_news_blackout` is the identity filter on a `:00` grid.
- **D54.** A required group with no SIGNAL is silently dropped.
- **D44.** The block bootstrap does not wrap: index 0 is drawn at 0.122× its due rate.
- **D28.** `T.ab` inflates z about 3.3×; use a paired test.
- **D38.** `measure_custom` zeroes custom conditions (BT1 has the registration-guard pattern).
- **D42.** `placebo_shift` leaks.
- **`Strategy.evaluate` is a strict AND**, so one VOID condition kills a strategy. 19% of generated strategies carry one (MNQ 27.4%). EF4 found an extra 5–14% of two-signal arms **jointly VOID**, so **run the census pairwise**.

### Session and engine behaviour
- **`engine.py:470` (EF7-D2).** With `exit_at_session_close=True`, `minutes_since_open` is never clamped, so every entry at or after 12:30 ET exits on its entry bar. Meanwhile 58/184 MGC and 90/185 MNQ generated strategies have the flag False, i.e. no session control at all. The prior programme therefore had two incoherent session regimes.
- **Flat enforcement on holiday and early-close sessions** needs the CME trading-day key (EF1-D3/D4). EF1's `session_end_indices` still misses 9 holiday-eve 23:00 bars per symbol (198 positions). EF3 proposes a holiday table; EF7 objects that shortened sessions trade (see §6).
- **Stale fills across the weekend gap.** A signal at 16:55 can fill Sunday 18:00. These fills are 3–14× worse than normal on MGC because the stop geometry is stale. Veto any fill that lags by more than one bar.
- **`Trade.gross_r` is already net of slippage.** Reconstruct gross from the fill geometry.
- **Thin-book slippage** applies to every non-RTH bar: 76–78% of scalp trades under the session rule.
- **The 16:00–18:00 prohibition is one hour stricter** than the real CME 17:00–18:00 break, which forbids about 4.4% of 5m bars that genuinely trade.
- **`rth_only` defaults to True** on 314/314 generated strategies. At that default the 18:00→16:00 rule changes only hold time: +2h30 on MGC, +1h30 on MCL, 0 on MES/MNQ.
- **Engine features that do not exist in practice.** The trailing stop has never run and `ExitReason.TRAIL` cannot be emitted. `max_concurrent_per_strategy` is dead. Scale-outs pay one round turn. `run_portfolio` is not a portfolio. Time and session exits are slippage-free. Source: R3 A-1…A-10.
- **Look-ahead checks that are clean:** swing pointers gate on confirmation; FVG and S/D zones pass through `as_of`; the 240m resample is bit-identical to the vendor's; and EF4's full-pipeline prefix invariance found 0 mismatches in 5,274 comparisons.

### Method rules that survived
- Measure absolutely before relatively. A relative test cannot find a hole two series share.
- Report the qualifying universe per cell instead of a top 10.
- Match placebos on **realised** trade counts, not raw signals (raw matching overshoots 2–3.3×).
- Use multiple placebo draws per base; one draw gives a coin-flip verdict.
- `placebo_shuffle` is **not** a control on one-directional bases.
- Collapse clones across `rth_only` arms before pooling.
- State free_t together with the span.

---

## 6. Contradictions between agents

| topic | side A | side B | which evidence is stronger |
|---|---|---|---|
| **Can 240m carry the 18:00→16:00 rule?** | EF6, EF2, EF3, the manager and PARKED.md: withdrawn, because 1320 % 240 ≠ 0; EF3 saw a 19.2% straddle. | EF1 (`msgs/EF1-02`), accepted in `edge/RESULTS.md`: it needs 960 % 240 == 0 (true). 491–497 ON_BOUNDARY bars, 0 INTERIOR, 0 saturation violations. The effective cycle is 20h because the 16:00–20:00 bucket is vetoed. | **EF1** (a measured saturation test; the parent adopted it). The 240m cells are reinstated with a caveat. **1440m genuinely cannot carry the rule.** |
| Cause of the flat violations | EF3/EF2: a coarse-grid problem. | EF1: holiday-only; the 60m violations (43) had 1320/60 = 22 exactly. | **EF1** |
| Holiday-eve flat fix | EF3: use `timeutil.MARKET_HOLIDAYS_2025_2027`. | EF7: a holiday table forces a spurious flat on shortened sessions that do trade. EF7's own h2 tests are red. | **EF7** (the 8 off-grid `:30` bars prove shortened sessions trade). Unresolved. |
| "Selecting is worse than not selecting" | Programme and EF6/EF5: replicates. | EF4: selection wins in 4/6 cells. | **Both**, reconciled: EF4's reverse-time control also "wins" 6/6, so its edge is within-window stationarity, not a forecast. EF6's random-10 arm shows the ranking carries a little information but concentration loses. |
| Rule 7 (sub-hourly graveyard) | Brief: 11–16% at 5m, stated as a timeframe law. | EF4: holds at 5m only (MGC 12.2%, MCL 2.9%); **not** at MGC 15/30m (36–38%). DISC1: the rule's sample was 4–19 sessions. | **EF4** (archive, 41 sessions, placebo-decomposed). Also EF4 retracted its own "gross half = signal quality" claim: it is exit geometry. |
| D24 (`rth_only=False` costs expectancy) | Brief: yes. | EF4/RESULTS: measured under the RTH-close flat, so it does not transfer. | Open; needs a paired 60m test. |
| Rule 2 (MTF) | Published z −4.09 plus "unanimous vs majority" as an empirical result. | R4/BT4: daily cells are self-confirming (D50); the unanimity sentence is INVALID. | **Narrowed, not retracted.** BT4: z −3.05 without the daily cells (sign survives). EF4 has no power to confirm. |
| Prior evaluations "flat by RTH close" | Earlier manager claim. | EF1/EF7: false; 1/3 to 1/2 of strategies had no session control, and the rest could not hold past 12:30. | **EF7** (mechanism verified). The manager retracted twice. |
| MGC 15m/30m "worst cell" (published A10) | `csv/raw` scan: <10% profitable. | EF4 archive: 36–38% net-positive. | Different stores and spans. Neither is a forecast; EF4's placebo shows the 15/30m level is the exit geometry. |
| `session_extreme_sweep` | EF6-01: ALIVE. | EF2: VOID. | Both are true, for different `rth_only` arms (EF2's gate was arm-blind; fixed). EF5/EF4: every fire falls post-RTH, and 28–65% are lost to the window. |
| BT3 placebo verdict | BT3 cycle 2: governor deletions are entry-independent. | Manager/BT3 self-correction: it compared a p-value to a t; a global R permutation is not a signal placebo. | **Withdrawn**: entry-dependence is untested. The survival result (z 6.16 / 5.54) still stands. |
| EF5's first holdout | Sign z 6.19. | EF5 itself: the gate used full-span t (a leak). | Retracted; the clean value is z 3.05. |
| `volume` required by MOMENTUM/BREAKOUT | R1's row. | R4 (D54): the group has no SIGNAL member, so it is silently dropped. | **R4** (verified by R1, Addendum C). |

---

## 7. Scripts: reusable vs one-off

**Reusable (KEEP):**
- `roundtable/lib/scale_audit.py`: absolute per-series integrity audit (splice, roll, rangeless, clock). Run it before any long series.
- `roundtable/lib/replay.py`: a bar-at-a-time paper-replay harness with a journal, a placebo beside the agent, engine-faithful fills, the session rule and the $50k ladder. Used by `workspace/paper/REPLAY/R1`.
- `edge/EF1/code/session_window.py`: the 18:00→16:00 `SessionWindowEngine` (`classify_bar`, `violations`, `session_end_indices`, `with_exit`/`assert_distinct_ids`). Imported by `tests/test_ef1_session_window.py` and by EF3/EF4/EF5/EF6 code.
- `edge/EF1/code/saturate.py`, `prefix_check.py` and `measure.py`: the saturation invariant check (a position open on every bar), prefix-invariance (look-ahead) check, and the three-arm validation.
- `edge/EF7/code/ef7_window.py` and `invariant.py`: an independent reimplementation of the session rule, imported by `tests/test_ef7_session_window.py`.
- `edge/EF6/code/deflation.py`: `threshold(n, span)`, `max_n_answerable`, span table.
- `edge/EF6/code/forward.py`: a causal forward roll with top-k / universe / random-k / blocked-permutation arms. Calibrated clean on 40 mean-zero ledgers (EF2 F13).
- `edge/EF6/code/placebo_w.py`: a window-legal placebo cohort matched on *realised* counts.
- `edge/EF6/code/attack.py`: gates G1–G4.
- `edge/EF6/code/arms.py`: D48-safe `refilter` and `assert_unique`.
- `edge/EF6/code/firing.py`, `window.py`, `run_prefilter.py`, `run_census.py`: the firing-rate census and VOID prefilter, plus the signal-admissibility mask.
- `edge/EF6/code/make_ledger.py` and `session_engine.py`.
- `edge/EF4/code/audit_lookahead.py`: full-pipeline prefix invariance.
- `edge/EF4/code/audit_fills.py`, `audit_stale_fills.py`, `audit_adverse_selection.py`: fill-model audits.
- `edge/EF4/code/cost_in_r.py`: cost as a fraction of R, including the min-stop floor.
- `edge/EF4/code/run_cell.py`, `placebo.py`, `run_placebo.py`: a cell runner with gross reconstruction, count-matched placebos and IS/OOS/folds.
- `edge/EF4/code/degeneracy.py`: always-on / duplicate / untradeable-window census.
- `edge/EF4/code/selection_control.py`: random-10, matched-10 and reverse-time selection controls.
- `edge/EF5/code/stress2_clean_holdout.py` and `stress3_regime_and_kind.py`: leak-free holdout, n_eff deflation via Jaccard, and regime thirds.
- `edge/EF3/code/ef3_session.py`, `ef3_stage2.py`, `ef3_rank.py`, `ef3_audit.py`: ready to finish the embargoed MES/MNQ 60m measurement.
- `backtest/BT2/code/event_clock.py` and `event_gate.py`: a look-ahead-free economic-calendar clock and gate factories (26 tests).
- `backtest/BT3/code/governor_replay.py`, `stops.py`, `stops_cache.json`, `paired_tests.py`, `checks.py`: the account-governor replay. Imported by `tests/test_bt3_governor_replay.py`.
- `backtest/BT5/code/s2.py` and `activity.py`: activity stratification. Imported by `tests/test_bt5_activity_strata.py`.
- `backtest/BT1/code/absorption.py` and `test_absorption.py`: an absorption-shape condition plus the D38-safe custom-condition registration pattern.
- `roundtable/check_ownership.py`: cited by `workspace/paper/CALL/CHECK_PROCEDURE.md:186`.

**One-off (ARCHIVE; findings captured above):**
- EF2/code: census, firecount, flat_reachability, population, rank, plan, weekend_gap, calibrate_roll, mcl_placebo_probe, prefix_invariance, stopfidelity, substrate.
- EF3/code: ef3_audit (kept above), ef3_census, ef3_measure, ef3_population, ef3_stopcensus, ef3_substrate.
- EF4/code: analyse, analyse2, census, or_resolvability, population, power, mtf_arms, rank_final, selection_direction, session_clock, trim_out.
- EF5/code: everything except the two stress scripts.
- EF6/code: analyse_census, probe_placebo, run_attack_demo.
- EF7/code: compare_ac, measure, population.
- BT1/code: frequency.py.
- BT3/code: block_vs_iid.py (runs on the D44-biased bootstrap).
- BT4/code: all of it (D50 blast radius; the regression lives in `tests/test_bt4_align_bucket.py`).
- BT6/code: all of it (D52; the regression lives in `tests/test_bt6_vwap_daily.py`).
- `check_refs.py`: roundtable message-format lint.

---

## 8. Next steps the lane itself names (in priority order)

1. **Roll-adjusted MGC daily** plus span-based pre-registered tests on MES/MNQ daily (7.4 y; SR 0.43 is enough to clear n=1).
2. **A paired `rth_only=False` test at 60m.**
3. **Finish EF3's embargoed MES/MNQ 60m placebo stage** (`ef3_stage2.py`, then `ef3_rank.py`).
4. **Pre-register one or two scalp hypotheses** and report them against t 1.177. Candidates from the level evidence: MGC 30m `poc_reversion` and `value_area_edge`.
5. **Build the untested level primitives:** anchored VWAP, RTH/weekly VWAP, composite/naked POC, round numbers, touch-count S/R, and a sweep-then-reclaim sequence (needs D37 lifted).
