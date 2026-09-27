# EF4 — SCALP on MGC and MCL at 5m / 15m / 30m

**Cell:** MGC and MCL, 5-minute / 15-minute / 30-minute, inside 18:00 ET → 16:00 ET with
nothing held across 16:00–18:00.
**Substrate:** `data/archive/` — `MGC|MCL_{5,15,30}m.jsonl`, 2026-07-29T19:20−04:00 →
2026-09-25T16:55−04:00. Every number on this page is measured on that store. Nothing here is
measured on `csv/raw`, and no number here may be pooled with a `csv/raw`-measured one.
**Harness:** EF1's `SessionWindowEngine`. **Until EF1 declares validation, every
profitability number on this page is provisional and is not a programme result.**

---

# The answer, first, because it is the answer and not a preamble

**This cell cannot forecast. A top-10 list from it describes 41 sessions of one two-month
window and carries no information about the next one. That is arithmetic about the span, it
was established before any strategy was run, and no result below changes it.**

The bound, exactly: the span is **57.90 calendar days = 0.1585 years**, √years = **0.398**,
identical to the minute across all six cells. `t ≈ SR × √years`, so:

| to reach | annualised Sharpe required |
|---|---|
| `free_t = 1.177` — **one** pre-registered hypothesis | **2.96** |
| `free_t = 2.677` — EF4's 36-arm pre-registered Track A | **6.73** |
| `free_t = 4.441` — EF4's 19,152-arm Track B screen | **11.16** |
| largest *t* ever found in this programme (3.923) | 9.85 |

**And one correction to how that bound should be read, because it changes what is and is not
reachable.** `t = SR_ann·√years` and `t = (µ/σ)·√N` are the *same* identity — for N trades in
Y years the trade rate is N/Y, so `SR_ann·√Y = (µ/σ)·√N` exactly. A scalp cell's
annualisation factor is therefore large, and "annualised Sharpe 2.96" restated per trade is
not a wall:

| trades in the window | per-trade µ/σ for `free_t = 1.177` | for Track A's 2.677 | for Track B's 4.441 |
|---|---|---|---|
| 100 | 0.118 | 0.268 | 0.444 |
| 400 | 0.059 | 0.134 | 0.222 |
| 800 | 0.042 | 0.095 | 0.157 |

So **a single pre-registered hypothesis at 400 trades needs net expectancy ≈ +0.06R** (σ≈1R).
That is an ordinary number. **Track B's 19,152-arm screen needs +0.22R net sustained over 400
scalp trades**, which is not. The bound is not "impossible" — it is **"one pre-registered
hypothesis, at high trade count, or nothing"**, and it is the *search width*, not the span
alone, that closes the door.

Then costs close it again. All-in cost per round trip in this cell, measured from the
contract spec and the measured ATR (burst 02), is **0.115R (MGC 5m, 1.0 ATR, thin book)** to
**0.266R (MCL 5m)**, and the spec's own `min_stop_ticks` floor makes **0.218R (MGC)** and
**0.363R (MCL)** the *minimum possible* cost at the tightest legal stop. So the gross
expectancy needed for a pre-registered row to clear at 400 trades is **+0.28R on MGC and
+0.42R on MCL**. This repository has never measured a gross edge of that size at any
timeframe.

**Two honest rows and a clear power statement is the deliverable. Ten rows would be a
description of 41 sessions wearing a forecast's clothing.**

## What that produced, stated here rather than buried

| | MGC | MCL |
|---|---|---|
| distinct signal sets reaching 30 trades in the full sample **and** in both halves | 401 | 360 |
| sign-consistent in-sample/out-of-sample, positive, and positive in every walk-forward fold | **19** | **3** |
| **clearing their own declared threshold (`free_t` = 4.441)** | **0** | **0** |
| largest *t* anywhere in the cell | **+2.62** | **+1.12** |

**I hand you 5 candidate rows for MGC and 3 for MCL, and the statement that none of them is
live-eligible.** MCL's best (+1.12) fails even `free_t = 1.177`, the code's own floor for a single
pre-registered hypothesis and the most generous threshold in this repository — **so on MCL the
answer is nothing, at every threshold.** MGC's best row achieves an annualised Sharpe of **6.58**,
a number that does not exist in real futures trading, and is **still 41% short** of the 11.16 its
search width demands.

And the negatives, which are the results this span *can* produce, because a rejection needs the
same power as a confirmation: **three of six pre-registered hypotheses are significantly negative
at MGC 5m** (|t| = 4.00, 4.32, 5.14 against a threshold of 2.677), two of them **worse than their
own count-matched placebos** at z = −2.99 and −2.69; the published **ORB negative replicates** on a
different substrate under a session rule that did not exist when it was measured; and rule 7's
**"sub-hourly graveyard" replicates at 5 minutes and nowhere else** — 12.2% of MGC 5m and 2.9% of
MCL 5m arms profitable, against 36–38% at MGC 15m/30m.

---

## Contents

| burst | subject |
|---|---|
| `bursts/01_power-bound.md` | the exact power bound per cell, and the per-trade restatement |
| `bursts/02_cost-in-R.md` | cost as a fraction of R per cell; the `min_stop_ticks` floor |
| `bursts/03_census.md` | the firing-rate census, 79 conditions × 8 cells |
| `bursts/04_session-rule-degeneracy.md` | always-on filters, duplicates, and what the 16:00–18:00 rule removes |
| `bursts/05_population-declared.md` | the population and its exact size, declared before measuring |
| `bursts/06_measurement.md` | rule 7, the split sample, the selection test, walk-forward, placebos |
| `bursts/07_anti-overfitting-audit.md` | every hazard the brief names: what was checked, what was found |

**Code:** `code/power.py`, `cost_in_r.py`, `census.py`, `degeneracy.py`, `or_resolvability.py`,
`population.py`, `session_clock.py` (EF4's second harness implementation, for differential
checking only), `run_cell.py`, `placebo.py`, `run_placebo.py`, `mtf_arms.py`, `analyse.py`,
`analyse2.py`, `selection_control.py`, `selection_direction.py`, `rank_final.py`,
`audit_lookahead.py`, `audit_fills.py`, `audit_stale_fills.py`, `audit_adverse_selection.py`,
`trim_out.py`. **Data:** `out/*.json`.

---

# 1. The power bound, per cell

`bursts/01_power-bound.md`, `code/power.py`, `out/power_bound.json`.

All six cells share one span to the minute: **2026-07-29T19:20−04:00 → 2026-09-25T16:55−04:00**,
**57.90 calendar days**, **41 complete 18:00→16:00 sessions**, **0.1585 years**, **√years = 0.398**.

| cell | bars | bars in the 16:00–18:00 prohibition | bars per session | 18:00→16:00 sessions |
|---|---|---|---|---|
| MGC 5m | 11,216 | 495 | 261.5 | 41 |
| MGC 15m | 3,746 | 167 | 87.3 | 41 |
| MGC 30m | 1,875 | 85 | 43.7 | 41 |
| MCL 5m | 11,212 | 493 | 261.4 | 41 |
| MCL 15m | 3,744 | 165 | 87.3 | 41 |
| MCL 30m | 1,873 | 83 | 43.7 | 41 |

**The three timeframes do not share one power bound.** `max_concurrent_per_strategy = 1`
`[repo-verified: engine.py:231]`, so trade count is capped by bars:

| cell | tradeable bars | N_max @4-bar hold | @8-bar hold | @16-bar hold |
|---|---|---|---|---|
| 5m | ~10,720 | ~2,144 | ~1,191 | ~631 |
| 15m | ~3,579 | ~716 | ~398 | ~211 |
| 30m | ~1,790 | ~358 | ~199 | ~105 |

Since `t = (µ/σ)·√N`, **5m is the best-powered of my three cells on trade count and the worst
on cost.** Those pull in opposite directions and the net answer is measured, not assumed
(section 4).

## 1a. The 16:00 flat is reachable in 41 of 41 cycles, in all six cells

This is where EF2's and EF3's defect does **not** reproduce. `EF3-01` found the flat
under-enforced on 19 of 507 MES/MNQ sessions and `EF2-02` on 17 of 506 MGC 60m cycles and 34
of 505 MCL 60m. At 5/15/30 on both my symbols:

`[measured: per 18:00→16:00 cycle, bars b with b.ts.hour < 16 and b.ts + tf == 16:00 ET]`

| cell | cycles | cycles with a bar ending exactly at 16:00 ET |
|---|---|---|
| MGC 5m / 15m / 30m | 41 / 41 / 41 | **41 / 41 / 41** |
| MCL 5m / 15m / 30m | 41 / 41 / 41 | **41 / 41 / 41** |

EF1's own `_audit_grid` agrees from the other side: `bars_on_boundary = 41`,
`bars_interior = 0` — exactly one boundary bar per cycle. The thinnest cycle in the window,
`2026-09-08` (204 of a typical 261 5m bars, the Labor Day short session), still carries its
16:00 bar. **So the flat-unreachability defect is a coarse-grid and sparse-data problem, not a
property of the rule**, and no EF4 row needs the gap-fill branch. Posted to EF1 as
`msgs/EF4-01_EF1_flat-reachable-at-scalp-tfs-and-the-weekend-gap-stale-fill.md`.

---

# 2. The census, and what it removed

`bursts/03_census.md`, `code/census.py`, `out/census.json` (632 rows: 79 conditions × 8 cells).
Run **before** any population was constructed.

| cell | snapshots | VOID | NEAR_VOID (<30 fires) | THIN (<2%) | LIVE |
|---|---|---|---|---|---|
| MGC 5m | 11,216 | 4 | 0 | 7 | 68 |
| MGC 15m | 3,746 | 4 | 2 | 4 | 69 |
| MGC 30m | 1,875 | 4 | 4 | 1 | 70 |
| MCL 5m | 11,212 | 4 | 1 | 5 | 69 |
| MCL 15m | 3,744 | 4 | 1 | 6 | 68 |
| MCL 30m | 1,873 | 4 | 4 | 2 | 69 |
| MGC 5+15+30 | 11,216 | 2 | 0 | 7 | 70 |
| MCL 5+15+30 | 11,212 | 2 | 1 | 5 | 71 |

**How many conditions the census removed: 4 per 5m cell, 6–7 per 15m cell, 8 per 30m cell** —
5.1% of the library at MGC 5m rising to 10.1% at 30m. The 30m cells lose twice as much as the
5m cells and the reason is only sample: fewer bars means fewer fires of a rare condition, so
part of any "30m is a cleaner timeframe" impression is 30m being unable to see rare things.

**Then the arms.** Census gating cut the never-trade rate hard: **5.0–13.7% of my declared arms
took zero trades**, against the programme-wide figure of 82% of generated strategies never
trading. That is the census doing its job.

## 2a. But the per-condition census under-counts, and I can say by how much

**Every single zero-trade arm in every cell is a TWO-SIGNAL arm. Not one single-signal arm took
zero trades anywhere**, and 95–99% of the zero-trade arms generated **zero signals** — meaning
their two LIVE conditions never co-fired with an agreeing direction on any bar.

`[measured: over out/run_*_both.json]`

| cell | zero-trade arms | all of which are 2-signal | jointly-VOID pairs as a share of 2-signal arms |
|---|---|---|---|
| MGC 5m | 183 | 183 | 183 / 2,800 = **6.5%** |
| MGC 15m | 290 | 290 | 277 / 3,150 = **8.8%** |
| MGC 30m | 493 | 493 | 469 / 3,360 = **14.0%** |
| MCL 5m | 150 | 150 | 142 / 2,793 = **5.1%** |
| MCL 15m | 207 | 207 | 205 / 2,597 = **7.9%** |
| MCL 30m | 413 | 413 | 411 / 3,150 = **13.0%** |

`Strategy.evaluate` is a strict AND **and** requires every SIGNAL to name the *same* direction
`[repo-verified: base.py:670-703]`. **So two LIVE conditions can be jointly VOID, and a
per-condition census cannot see it.** The programme's "19.0% of generated strategies carry a
condition that can never fire" is therefore a *lower bound* on the dead population; the
pairwise term adds **5–14%** more on top in my cells, rising monotonically with the timeframe
(5m → 15m → 30m: 6.5 → 8.8 → 14.0% on MGC, 5.1 → 7.9 → 13.0% on MCL), because a coarser grid has
fewer bars on which two conditions can coincide. **That monotonicity is the signature of a sample
effect rather than a content effect** — the same pairs are jointly VOID at 30m and jointly live at
5m.

**Recommendation for the next agent: the census must be run pairwise, not just per condition.**
It is one extra pass over the same snapshots.

## 2b. The four verdicts the dispatch asked for

1. **`openinterest`: VOID, 0/N, in 8 of 8 cells.** `oi_price_confirmation` and `oi_expanding`
   never fire at 5m, 15m, 30m or on the group frame, on either symbol. The CSV has no
   open-interest column. Any strategy carrying either is a non-result, not a negative result.
2. **`profile`: NOT dead at 5/15/30 — the 240m verdict does not transfer.** `poc_reversion`
   22.8–40.4%, `value_area_breakout` 44.8–61.4%, `away_from_hvn` 69.5–83.9%,
   `open_outside_value` 18.2–27.4%, `value_area_edge` 1.9–5.2%. Only `lvn_rejection` is thin
   (MCL 0.12–0.32%, NEAR_VOID; MGC 30m 21 fires, NEAR_VOID). The mechanism: every profile
   condition reads the **prior** session's profile and asks only whether the close is near one
   of its levels `[repo-verified: library.py:935-939]`; it never needs the current bar to fill
   bins, so R1's "median bar touches 3 of 40 value-area bins" does not gate it. **The opposite
   caution applies: `away_from_hvn` and `value_area_breakout` fire so often they are close to
   information-free, and three of the six are FILTERs in that range.**
3. **`OPENING_RANGE`: resolvable at all six, but MGC 15m and 30m are shifted 10 minutes late.**
   Width is exactly 30 minutes in all six cells — the scan report's "30-minute range built 60
   minutes wide" does **not** replicate here. What fails is placement: MGC opens 08:20 = 500
   minutes, not divisible by 15 or 30, so the constructed range covers **minutes 10–40 after
   the open, 41 of 41 days**, excluding the first ten minutes of gold's RTH. MCL opens 09:00 =
   540, divisible by 5, 15 and 30, and is clean at all three. MGC 30m's range is a single bar,
   so `opening_range_fade` cannot fire until a later bar. Verdict: **MGC 15m / 30m `DEGRADED`**;
   MGC 5m and all MCL **CLEAN**.
4. **`StopKind.VWAP_BAND` (D45): inputs present in every cell.** `stop_price` returns `None`
   when `vwap_l1`/`vwap_u1` are missing `[repo-verified: base.py:296-300]`; the vwap-band
   conditions fire 9.7–24.5% everywhere, so the columns are populated and the stop is
   resolvable at 5/15/30 on both symbols. Whether it is an ATR band in disguise is R3-Q1 and
   EF5 owns it; I record only that a null from it here would be a measurement, not an absence.

## 2c. Three degeneracies a firing-rate table cannot show

`bursts/04_session-rule-degeneracy.md`, `code/degeneracy.py`, `out/degeneracy.json`.

- **ALWAYS_ON.** `mtf_not_conflicted` fires on **100.00%** of bars in all six single-timeframe
  cells — a filter that cannot veto, counted by the combinator as a filter. `outside_news_blackout`
  and `no_imminent_release` pass on 99.1–99.6% and are **Jaccard 0.992–1.000 with each other**
  (exactly 1.000 at 30m on both symbols). *Independently reproduces R1-D-MTF3, R4 and R2;
  priority theirs.*
- **DUPLICATE.** `macd_directional` ≡ `macd_hist_direction` and
  `regime_trending` ≡ `regime_matches_direction`, **Jaccard 1.0 in all six cells**. Replicates
  R1's `D-M1` and R6's `D-R2` in six cells they did not report. A caution of my own: 11–16
  further pairs per cell exceed Jaccard 0.95 and nearly all involve an always-on member —
  **two conditions each passing on 99% of bars are necessarily ~98% identical whatever they
  compute, so a Jaccard de-duplication gate must condition on fire rate.**
- **UNTRADEABLE WINDOW.** The entry fills at the next bar's open, so a fire on the bar before
  the prohibition is not actionable. `session_extreme_sweep` loses **28.1% (MGC 5m) to 65.4%
  (MCL 30m)** of its fires this way, and **fires 100% outside RTH in all six cells** — because
  `lv.session_high` is the running RTH extreme updated *with* the current bar
  `[repo-verified: features.py:881-885]`, so during RTH the comparison is arithmetically
  impossible and it can only fire after the contract's close and before `trading_day` rolls at
  18:00. **It is MISNAMED in this cell** (it detects a sweep of the *completed* RTH extreme in
  the post-close extension), and after the session rule it falls below the 30-trade floor in
  **four of six cells**: legal fires 41 / 26 / 19 / 30 / 14 / 9 for MGC 5m/15m/30m and MCL
  5m/15m/30m. That is a census verdict changed by the programme's own defining rule, which has
  never been measurable here before.

---

# 3. Costs — the dominant term on this cell, and larger than the dispatch states

`bursts/02_cost-in-R.md`, `code/cost_in_r.py`, `out/cost_in_r.json`.

**Three findings, in order of how much they matter.**

### 3a. `Trade.gross_r` is not gross, and the repo reports it as if it were

The engine charges **slippage into the fill price** (`engine.py:352` entry, `:414` stop exit)
and **commission as dollars** in `_close` (`:494-499`). So `net_r − gross_r` is the commission
term alone and **`gross_r` is already net of slippage.** Any row quoting `gross_r` as "gross"
understates true gross by the whole slippage term, which in this cell is **1.5–3.5× the
commission**. Every gross figure in this file is reconstructed from the fill geometry
(`code/run_cell.py::_metrics_from_trades`), never taken from `gross_r`.

### 3b. The thin-book regime is the normal case under this session rule

`thin = not is_rth(bar.ts, ...)` `[repo-verified: engine.py:351, :411]` adds
`thin_book_extra_ticks = 1.0` per side. Measured RTH share of bars: **MGC 22.7/21.9/21.9%,
MCL 24.1% at all three** — so **76–78% of every scalp trade is in the thin-book regime**. MGC's
RTH is 310 minutes and MCL's 330 out of a 1,320-minute cycle. No prior run in this repository
traded those bars, so this cost has never been priced here.

### 3c. All-in cost in R, and a hard floor the spec imposes

Median Wilder-14 ATR on the cell's own timeframe: MGC 4.752 / 8.626 / 12.503 points;
MCL 0.2044 / 0.3560 / 0.5115. Both contracts: `tick_value = $1.00`, round-turn
commission + fee `$1.44`.

| cell | stop | commission only | all-in RTH (stop exit) | all-in **thin** (stop exit) |
|---|---|---|---|---|
| MGC 5m | 0.5 ATR | 0.061 R | 0.145 R | **0.229 R** |
| MGC 5m | 1.0 ATR | 0.030 R | 0.072 R | 0.115 R |
| MGC 30m | 1.0 ATR | 0.012 R | 0.028 R | 0.044 R |
| **MCL 5m** | **0.5 ATR** | **0.141 R** | **0.337 R** | **0.532 R** |
| MCL 5m | 1.0 ATR | 0.070 R | 0.168 R | 0.266 R |
| MCL 30m | 1.0 ATR | 0.028 R | 0.067 R | 0.106 R |

**The dispatch's "15.0% of R at 5m" is commission-only.** My commission-only figure for MCL 5m
at 0.5 ATR is 14.1%, which identifies its provenance. The all-in figure for the same cell is
**33.7% RTH / 53.2% thin** — direction right, magnitude **2.4–3.8× too small**.

**And the floor.** `stop_price` ends with `dist = max(dist, min_stop_ticks × tick_size)`
`[repo-verified: base.py:313-314]` — silently. MGC's floor is 25 ticks = $25, MCL's 15 ticks =
$15, and **0.5 ATR at 5m is below both** (23.8 ticks MGC, 10.2 MCL). So:

| cell | tightest legal stop | min all-in cost RTH | min all-in cost **thin** |
|---|---|---|---|
| MGC, any tf | $25 | 0.138 R | **0.218 R** |
| MCL, any tf | $15 | 0.229 R | **0.363 R** |

These are floors. **No MCL scalp under this cost model can pay less than 22.9% of R per round
trip, or less than 36.3% in the overnight regime this programme runs in.** Two consequences:
a "0.5 ATR" arm at 5m in this repository is not testing 0.5 ATR, it is testing the floor with
no warning; and there is no free direction, because tightening explodes cost/R while widening
buys no expectancy (BRIEF rule 3, measured four times).

**What that does to the bound.** Burst 01: net +0.06R at 400 trades clears a *single*
pre-registered hypothesis. Adding the floor, the **gross** needed is **+0.28R on MGC and
+0.42R on MCL** — a size this repository has never measured at any timeframe.

---

# 4. The pre-registered hypotheses (Track A) — and three of them fail *significantly*

`bursts/05_population-declared.md`. n = 36, `free_t = 2.677`. One fixed exit for every arm.
All numbers gross-reconstructed; **provisional until EF1 validates.**

## MGC 5m — all six negative, three beyond their own threshold

| arm | n | win rate | **gross E** | cost | **net E** | t | IS (n) | OOS (n) | hold | % entries outside RTH |
|---|---|---|---|---|---|---|---|---|---|---|
| `A3_VA_EDGE` | 132 | 0.386 | +0.0052 | 0.1021 | −0.0969 | −0.91 | −0.110 (82) | −0.076 (50) | 20 m | 84% |
| `A5_ORB` | 489 | 0.378 | −0.0563 | 0.0759 | −0.1322 | −2.46 | −0.020 (302) | −0.313 (187) | 20 m | 40% |
| `A2_PD_SWEEP` | 250 | 0.360 | −0.0609 | 0.0902 | −0.1511 | −1.98 | −0.185 (148) | −0.101 (102) | 19 m | 74% |
| **`A4_VWAP_BAND`** | 641 | 0.348 | −0.1045 | 0.1011 | **−0.2056** | **−4.32** | −0.216 (376) | −0.191 (265) | 19 m | 80% |
| **`A6_ON_COMPRESSION`** | 264 | 0.299 | −0.2252 | 0.1329 | **−0.3582** | **−5.14** | −0.333 (180) | −0.413 (84) | 16 m | 97% |
| **`A1_ON_SWEEP`** | 87 | 0.230 | −0.4099 | 0.0469 | **−0.4568** | **−4.00** | −0.537 (56) | −0.312 (31) | 18 m | 1% |

**Three of six pre-registered hypotheses are significantly negative at their own declared
threshold** (|t| ≥ 2.677 at n = 36), with consistent signs in-sample and out-of-sample. That is a
result, not a null — it is the shape of result this cell can actually produce, because a
*rejection* needs the same power as a confirmation and these have the trade counts for it.

Read carefully: a two-sided rejection of a stated direction is evidence for its negation at the
same |t|. `A1_ON_SWEEP` loses **0.41 R gross** per trade over 87 trades taking the *reversal*
side of an overnight-extreme sweep; the continuation side is thereby supported at |t| = 4.00.
**But the negation was not the pre-registered hypothesis and I only know it because I looked.**
A strategy built on the inverse is a new hypothesis owing a new sample, not a row for RESULTS.md.

## MGC 15m and 30m — the same six, all negative, one clearing in the negative

| arm | 15m net E (n, t) | 30m net E (n, t) |
|---|---|---|
| `A3_VA_EDGE` | −0.032 (79, −0.24) | **+0.149** (60, +0.95) |
| `A2_PD_SWEEP` | −0.119 (140, −1.19) | −0.015 (106, −0.13) |
| `A5_ORB` | −0.129 (201, −1.60) | −0.208 (131, −2.21) |
| `A4_VWAP_BAND` | **−0.217 (330, −3.38)** | −0.099 (192, −1.17) |
| `A6_ON_COMPRESSION` | −0.258 (101, −2.23) | −0.265 (69, −1.93) |
| `A1_ON_SWEEP` | −0.317 (50, −2.02) | −0.271 (39, −1.62) |

`A3_VA_EDGE` at MGC 30m is the only positive pre-registered arm anywhere: **+0.149 R net over 60
trades, t = +0.95** — which is 1.7 t-units short of its own threshold and cannot be reported as
more than "did not fail".

## `A5_ORB` — the published ORB negative replicates, and it is an absent edge rather than a cost problem

`A5_ORB` is negative on every MGC cell: −0.132 (5m, t = −2.46), −0.129 (15m), −0.208 (30m,
t = −2.21), and **negative gross too** (−0.056 at 5m). The scan report's verdict — median
expectancy −0.092 R, negative at zero transaction cost, R6's audit finding it **STANDS** — is
reproduced here on a different substrate (`data/archive/`, 41 sessions), under a session rule
that never existed when it was measured, on a condition the census confirms is LIVE
(22.0–24.2% of bars) and on MCL where the opening range is arithmetically clean. **It is not a
resolvability artefact and it is not a cost artefact.** It is the cleanest confirmation in my
cell.

---

# 5. What the session rule itself costs, and one hazard it creates

The 18:00→16:00 rule has never been run in this repository, so everything here is new
measurement rather than a re-reading.

## 5a. The prohibition removes signals, unevenly, and worst where the sample is thinnest

`out/degeneracy.json`. Entries vetoed because the fill bar lands in [16:00, 18:00) ET:
**12.9 per arm at MGC 5m** (38,794 over 3,016 arms), **5.2 per arm at MGC 15m**. By condition the
loss ranges from ~7% to **65.4%** of fires (table in burst 04), and the conditions worst hit are
exactly the session-level ones: `session_extreme_sweep`, `initial_balance_break`,
`opening_range_breakout`, `open_outside_value`.

**The substrate detail that makes this concrete.** `data/archive/` carries a **full** set of bars
in ET hour 16 and essentially none in hour 17 `[measured: MGC 5m hour 16 = 492 bars = 41 × 12;
hour 17 = 3]`. The real CME maintenance break for these contracts is **17:00–18:00**; the
programme's rule is one hour stricter and therefore forbids an hour of genuinely traded time,
about 4.4% of 5m bars. That is a property of the rule, not of the data, and it is worth the
manager knowing it is a choice rather than a constraint.

## 5b. `rth_only=True` is the default and would have deleted this cell

`StrategyFilters.rth_only` defaults to `True` `[repo-verified: base.py:393]`. In my cells that
vetoes **76–78% of all bars**. Every EF4 arm sets `rth_only=False`. **D24 measured
`rth_only=False` as buying sample and costing expectancy — but it measured that under the old
regime where the position was flattened at the contract's own RTH close, so its sign does not
transfer to a rule that permits the hold.** It should not be quoted against this programme's
overnight rows as if it did. (EF2-01 raised the same mechanism from the swing side; this is an
independent measurement of its size on the scalp side.)

## 5c. The hazard: a signal inside the prohibition can fill across the weekend gap

EF1's default is `veto_signals_in_window=False`, and its docstring is explicit that a signal
*computed* in 16:00–17:00 whose fill lands at 18:00 is legal under the rule as written. I agree
that is the rule. The hole it opens is larger than it sounds, because of 5a: the bar after MGC's
16:55 bar is 18:00 the same evening on a weekday and **18:00 Sunday after a Friday** — and the
three largest bar-to-bar discontinuities in the whole substrate are exactly those reopens:

```
MGC  +37.1997 pts 2026-09-13T18:10   +24.7002 2026-08-02   +23.8999 2026-08-30
MCL  + 4.63   pts 2026-08-02T18:10   + 3.06   2026-09-13   + 1.86   2026-08-30
```
`[measured: code/audit_fills.py → out/audit_fills.json]`

**I measured it rather than asserting the size, and the mechanism is not the one the gap
suggests.** `code/audit_stale_fills.py` → `out/audit_stale_fills.json`, over 406 arms per cell:

| cell | trades | stale fills (lag > 2 bars) | weekend-gap fills (lag > 24 h) | **E(normal)** | **E(stale)** | **E(weekend)** | max abs R, weekend |
|---|---|---|---|---|---|---|---|
| MGC 5m | 177,864 | 1,443 (0.81%) | 224 (0.126%) | −0.1080 | **−0.5851** | −0.1447 | 1.44 |
| MGC 15m | 68,958 | 1,620 (2.35%) | 244 (0.354%) | −0.0401 | **−0.3607** | −0.3299 | 1.50 |
| MGC 30m | 38,854 | 1,617 (4.16%) | 247 (0.636%) | −0.0256 | **−0.3828** | −0.6051 | 1.49 |
| MCL 5m | 145,434 | 1,307 (0.90%) | 261 (0.179%) | −0.2214 | **−0.5595** | −0.3856 | 1.11 |
| MCL 15m | 60,915 | 1,763 (2.89%) | 245 (0.402%) | −0.1364 | −0.1668 | −0.3023 | 2.11 |
| MCL 30m | 37,862 | 2,039 (5.39%) | 328 (0.866%) | −0.0954 | −0.0797 | −0.1859 | 1.47 |

**A stale fill is 3–14× worse than a normal one on MGC**, and the worst observed weekend outcome
is 1.44–2.11 R, not the 7.8 R the raw gap size suggests. **The mechanism is not gap loss — the gap
happens *before* the entry.** It is stop staleness: `_open_position` honours `sig.stop`, computed at
the signal bar, and re-derives the *risk distance* from the new fill
`[repo-verified: engine.py:363-370]`. After a 37-point favourable gap the trade is still taken and
its risk distance has ballooned, so the 1.5 R target is now 55 points away instead of 7. The
position is not gapped into a loss; it is entered with a thesis whose geometry no longer exists.

Removing stale fills would move pooled expectancy by ~+0.004 R at MGC 5m and **+0.015 R at MGC
30m** (0.81% and 4.16% of trades at a 0.48 R and 0.36 R deficit). Small, systematic, one-signed,
and it grows with the timeframe because a coarser grid has fewer bars between 16:55 and 18:00.

Raised to EF1 in `msgs/EF4-01_EF1_flat-reachable-at-scalp-tfs-and-the-weekend-gap-stale-fill.md`;
my recommendation is to veto fills whose lag exceeds one bar, which removes both the weekend
crossing and the ordinary stale-stop case while keeping the legitimate weekday 17:00→18:00 fill,
and to report the count either way.

---

# 6. The anti-overfitting audit — what was checked and what it found

Full detail in `bursts/07_anti-overfitting-audit.md`.

| hazard | how checked | result |
|---|---|---|
| **look-ahead / future-data leakage** | full-pipeline prefix invariance: rebuild `SymbolFrame`, library, engine and session rule on `bars[0:k]` and require every trade closing inside the prefix to be bit-identical to the full run | **CLEAN — 5,274 trade comparisons over 12 prefix runs, 0 mismatches** |
| **repainting indicators** | the same test (a repaint changes on a prefix) | **CLEAN by the same evidence** |
| **unrealistic fills** | same-bar target credit, tie resolution, zero-slippage exits, gap accounting | **CLEAN** — 3.0–4.2% same-bar targets against the 51% that signalled the repo's known bug; **every** entry-bar stop/target tie resolved stop-first (29/29 across 6 cells); **0** stop exits filled at the level with no slippage; 58% filled *worse* than the stop, mean 0.020–0.120 R adverse |
| **understated costs / slippage** | reconstructed gross; thin-book share; the spec's stop floor | **FOUND — three separate understatements** (§3) |
| **insufficient sample size** | power bound per cell, trade-count ceiling per timeframe | **FOUND and quantified — binding, and binding differently at 5m than at 30m** (§1) |
| **data-mining bias** | *n* declared before measuring; placebo beside every reported row; random-10, trade-matched-10, reverse-time and direction controls on the selection test | **FOUND — §7** |
| **parameter sensitivity** | one fixed exit for all 19,188 arms, never searched | **removed by construction, not measured away** |
| **survivorship / roll bias** | gap census on the raw series | **unfixable substrate property, quantified** (§5c) |
| **adverse selection at the fill** (not on the brief's list; checked anyway) | signed signal-close → fill-open move, per cell | **CLEAN** — 35.9–42.9% of fills adverse, R effect −0.029 to +0.007 and not one-signed |

One substrate fact fell out of the last check and belongs in the record: **the median
discontinuity between one bar's close and the next bar's open is exactly 1 tick** on both contracts
at all three timeframes. Every backtest in this repository fills entries at `bar.open` after
computing the signal on the previous close, so that tick is inside every result here — unmodelled,
and measurably unbiased.

The prefix-invariance pass is the one worth reading twice. The ORB/ICT report records that this
repository once produced a **+0.354 R cluster at t = 5.19** that survived a 60/40 split **and all
three disjoint slices** and was a look-ahead in the author's own fill code, and drew the right
conclusion: *"Resampling cannot detect a bias whose sign is always favourable. Only auditing the
fill model can."* Out-of-sample testing is structurally blind to it. **Prefix invariance is not,
and this pipeline had never been checked end to end that way.** A clean pass is not proof of
absence — a bias that is a pure function of the bar would pass — but a failure would have been
proof of presence, and there was none in 5,274 comparisons.

---

# 7. The selection test: the programme's central negative does NOT reproduce here — and it is still not a forecast

`code/analyse2.py`, `code/selection_control.py`, `code/selection_direction.py` →
`out/analysis_split.json`, `out/selection_control.json`, `out/selection_direction.json`.

The programme's settled finding is that **selecting was worse than not selecting**: last period's
top 10 returned −0.0155 R against a −0.0104 R null and underperformed trading the whole
qualifying universe (+0.022 R vs +0.057 R), with Jaccard 0.081 name overlap across disjoint
thirds. I re-ran exactly that experiment under the 18:00→16:00 rule: rank on the first 25 of 41
sessions, score on the last 16.

**The first reading reverses the programme's sign, and I do not believe it, for reasons I can put
numbers on.**

| cell | qualifying arms | ρ(IS, OOS) | top-10 IS → OOS | universe IS → OOS | first reading |
|---|---|---|---|---|---|
| MGC 5m | 1,198 | **−0.146** | +0.286 → −0.040 | −0.106 → −0.155 | selection wins |
| MGC 15m | 653 | **+0.042** | +0.381 → **+0.147** | −0.032 → −0.089 | selection wins |
| MGC 30m | 348 | +0.221 | +0.220 → **+0.122** | −0.043 → −0.060 | selection wins |
| MCL 5m | 1,068 | +0.085 | +0.130 → −0.198 | −0.262 → −0.194 | selection **loses** |
| MCL 15m | 552 | +0.309 | +0.256 → **−0.147** | −0.131 → −0.136 | selection **loses** |
| MCL 30m | 420 | +0.207 | +0.185 → **−0.021** | −0.075 → −0.120 | selection wins |

**Note ρ = −0.146 at MGC 5m over 1,198 arms — an in-sample rank *negatively* correlated with
out-of-sample performance, in the cell where the sample is largest.** That is the programme's
original negative in its purest form, and it sits in the same row as "selection wins", because the
extreme tail and the rank correlation are different statistics and only one of them is a forecast.

## The four controls, and the one that settles it

**Control 1 — RANDOM-10** (draw 10 arms uniformly from the same universe, pool the same way,
2,000 draws). Random-10 lands within 0.0003 R of the trade-weighted universe every time, so the
pooling itself is not broken. The real top 10 sits at percentile **0.999 / 1.000 / 1.000** (MGC
5m / 15m / 30m) and **0.417 / 0.402 / 0.985** (MCL 5m / 15m / 30m).

**Control 2 — MATCHED-10** (10 arms whose in-sample trade counts match the top 10's, 2,000
draws). This matters because the top 10 trade *less* than the universe in every cell: median
in-sample trades **57.5 vs 131.5, 60 vs 96, 66 vs 83** (MGC 5m/15m/30m) and **40 vs 102, 47 vs 84,
54 vs 64** (MCL). After matching, the top 10 sits at percentile **0.980 / 1.000 / 0.995** and
**0.620 / 0.729 / 0.960**. So trade count is not the explanation.

**Control 3 — direction.** Over this window MGC ran 4151 → 4321 (+4.1%) and MCL 84.63 → 92.41
(+9.2%), so a long-biased arm is favoured for a reason that has nothing to do with its rule. It
is not the explanation either: the top 10's long share is **0.478 / 0.533 / 0.467 / 0.539**
against random-40's **0.498 / 0.519 / 0.535 / 0.522**, and forcing the top 10 LONG-only and
SHORT-only gives **both signs positive** on MGC (15m +0.284 / +0.285; 30m +0.126 / +0.216) and on
MCL 30m (+0.057 / +0.103). Only MCL 15m splits (+0.200 long, −0.065 short). **The effect is
direction-symmetric, so it is not drift.**

**Control 4 — REVERSE TIME, and this is the one that settles it.** Select on the *last* 16
sessions and score on the *first* 25. **Selection wins in all six cells**, reverse-selected top 10 against the
universe, both scored on the earlier half: MGC 5m **−0.088 vs −0.106**, MGC 15m **−0.008 vs
−0.032**, MGC 30m **+0.050 vs −0.043**, MCL 5m **−0.164 vs −0.262**, MCL 15m **−0.117 vs −0.131**,
MCL 30m **+0.005 vs −0.075**.

> **A selection rule that works equally well backwards in time is not forecasting.** It is
> detecting a property that is stationary across this one 41-session window. Two halves of one
> two-month regime are not two independent samples of the future.

## And what the "property" actually is: one condition wearing ten names

| cell | condition frequency in the in-sample top 10 |
|---|---|
| MGC 15m | `candle_engulfing` **8/10**, `structure_trend` 4, `break_of_structure` 3 |
| MGC 30m | `imbalance_pullback` **9/10**, `above_vwap` 4 |
| MCL 15m | `candle_reversal` 5, `adx_trending` 4, `bollinger_mean_pull` 3, `opening_range_fade` 3 |
| MCL 30m | `adx_trending` 4, `candle_engulfing` 4, `candle_close_strength` 3 |
| MGC 5m | 13 distinct conditions across 10 rows, mean pairwise Jaccard 0.204 |
| MCL 5m | 13 distinct conditions across 10 rows, mean pairwise Jaccard 0.190 |

Nine to twelve distinct conditions across ten "different" rows, mean pairwise condition Jaccard
0.12–0.33. **So the top 10 is one or two conditions and eight variants of them**, their trade
lists overlap heavily, and the pooled 351–505 out-of-sample trades are nowhere near 351–505
independent observations — the standard error on that +0.147 R is understated by an unknown but
large factor. This is precisely the ORB/ICT report's lesson: *"a league table of the best rule
sets containing a condition measures the search, not the condition."*

**Verdict on the selection test.** The programme's "selecting is worse than not selecting" does
**not** reproduce in four of six cells — but the correct replacement claim is not "selecting works". It
is: *the cross-section of arms is not homogeneous, one or two conditions are better than the rest
within this window in a way visible from either half, and neither the rank correlation
(ρ = +0.042 on 653 arms) nor the reverse-time test permits calling that a forecast.* The ranked
list must therefore be de-duplicated by signal set before it is reported at all, which is what
§8 does and which cuts it from ten rows to two or three.

---

# 8. BRIEF rule 7 — "sub-hourly is a graveyard" — REPLICATES at 5m, does NOT at 15m/30m on MGC, and the number is a cost number

`code/analyse.py` → `out/analysis_rule7.json`. Share of the declared Track B screen with
**positive expectancy**, at a 30-trade floor, gross and net reported separately.

| cell | arms | arms ≥30 trades | **% positive NET** | **% positive GROSS** | median net | median gross | median cost | median trades |
|---|---|---|---|---|---|---|---|---|
| **MGC 5m** | 3,010 | 1,864 | **12.2%** | 32.5% | −0.132 | −0.042 | 0.093 | 124 |
| MGC 15m | 3,374 | 1,376 | **36.0%** | 50.7% | −0.046 | +0.002 | 0.050 | 77 |
| MGC 30m | 3,591 | 998 | **37.8%** | 46.0% | −0.049 | −0.014 | 0.035 | 60 |
| **MCL 5m** | 3,003 | 1,749 | **2.9%** | 32.1% | −0.241 | −0.043 | **0.202** | 101 |
| MCL 15m | 2,800 | 1,081 | **12.6%** | 43.9% | −0.143 | −0.023 | 0.125 | 75 |
| MCL 30m | 3,374 | 970 | **23.9%** | 46.2% | −0.093 | −0.014 | 0.084 | 63 |

**Which way it came out, plainly.**

1. **At 5 minutes, rule 7 replicates and understates.** MGC 5m is **12.2%**, inside the quoted
   11–16% band. **MCL 5m is 2.9%** — well below it. So on 41 sessions of `data/archive/`, under a
   session rule that never existed when the rule was written, the 5-minute graveyard is real and on
   the cost-fragile contract it is deeper than stated.
2. **At 15 and 30 minutes it does not hold on MGC.** 36.0% and 37.8% positive — not a graveyard by
   rule 7's own standard. **So "sub-hourly" is too coarse a bucket: the effect is 5-minute-specific,
   not sub-hourly-generic.** On MCL, 15m (12.6%) is inside the band and 30m (23.9%) is above it, so
   MCL's boundary sits one timeframe coarser than MGC's — which is what the independence rule would
   predict and is why this had to be measured per symbol.
3. **The number decomposes cleanly, and both halves matter.** Gross is 32.1–32.5% positive at 5m on
   **both** symbols and 43.9–50.7% at 15m/30m. So there is a genuine, symbol-independent
   **gross** degradation at 5 minutes. **§11 then shows that the gross half is NOT a signal-quality
   effect** — count-matched random entries also have negative gross at 5m and positive gross at
   15m/30m, so it belongs to the exit geometry meeting a 5-minute bar grid. Cost
   then supplies the rest, and **cost is where the symbols differ**: median 0.093 R (MGC 5m) against
   **0.202 R (MCL 5m)**, a factor of 2.2. Rule 7's headline is therefore about half a signal-quality
   statement and half a cost statement, and the cost half is the one that makes MCL 5m the worst
   cell in this study at 2.9%.

**Walk-forward agrees and sharpens it.** Arms reaching 10 trades in all three contiguous folds,
share positive in **all three** (a coin flip would give 12.5%):

| cell | arms | positive in all 3 | negative in all 3 |
|---|---|---|---|
| MGC 5m | 1,669 | **2.04%** | **46.20%** |
| MGC 15m | 1,195 | 8.87% | 20.17% |
| MGC 30m | 785 | 5.99% | 20.25% |
| MCL 5m | 1,496 | **0.13%** | **76.40%** |
| MCL 15m | 885 | 1.02% | 50.06% |
| MCL 30m | 790 | 4.56% | 33.67% |

**Every cell is below the 12.5% coin-flip rate for all-three-positive and far above it for
all-three-negative.** MCL 5m is the extreme: **2 arms of 1,496 are positive in all three folds and
1,143 are negative in all three.** That is not a sampling accident; it is a population with a
consistently negative mean, which is exactly what a 0.20 R per-trade cost against a gross
expectancy near zero produces.

---

# 9. Does multi-timeframe alignment improve outcomes? Measured, not assumed — and no

`code/mtf_arms.py` → `out/mtf_arms.json`. A declared paired test, **not** a search.

**Why it needed a frame of three.** My census (§2c) shows the question cannot even be asked on a
single-timeframe frame: `mtf_aligned` and `mtf_strongly_aligned` are **0/N in all six**, and
`mtf_not_conflicted` fires on **100.00%** of their bars. On a frame of one the family either kills
the strategy or is a no-op. So the arms run on a **5 + 15 + 30 frame** on a 5-minute base, where
`mtf_aligned` fires on 39.7% (MGC) / 41.4% (MCL) of bars.

**Design, fixed before running.** Track A's six hypotheses × 2 symbols = **12 pre-registered
pairs**, each in two versions: without and with `mtf_aligned` added as a second SIGNAL (which is
exactly "require alignment", since `Strategy.evaluate` demands every signal name the same
direction). Both arms in one `run_many` pass over the same frame. Test: **Wilcoxon signed-rank on
the paired differences plus a plain sign test — named explicitly, and not `T.ab`, which D28
records as inflating z ~3.3×.** `_id=None` on every `replace` and ids asserted distinct.

| arm | n plain | n aligned | retention | E plain | E aligned | Δ |
|---|---|---|---|---|---|---|
| MGC `A1_ON_SWEEP` | 87 | **2** | 0.02 | −0.4568 | +0.2269 | +0.684 |
| MGC `A2_PD_SWEEP` | 250 | 17 | 0.07 | −0.1511 | +0.1217 | +0.273 |
| MGC `A3_VA_EDGE` | 132 | 14 | 0.11 | −0.0969 | +0.0028 | +0.100 |
| MGC `A4_VWAP_BAND` | 641 | 82 | 0.13 | −0.2056 | −0.3746 | −0.169 |
| MGC `A5_ORB` | 489 | 219 | 0.45 | −0.1322 | +0.0001 | +0.132 |
| MGC `A6_ON_COMPRESSION` | 264 | 99 | 0.38 | −0.3582 | −0.3035 | +0.055 |
| MCL `A1_ON_SWEEP` | 68 | **1** | 0.01 | −0.1281 | −1.0819 | −0.954 |
| MCL `A2_PD_SWEEP` | 174 | 19 | 0.11 | −0.4181 | −0.7410 | −0.323 |
| MCL `A3_VA_EDGE` | 117 | 20 | 0.17 | −0.1104 | +0.0653 | +0.176 |
| MCL `A4_VWAP_BAND` | 622 | 89 | 0.14 | −0.2617 | −0.3734 | −0.112 |
| MCL `A5_ORB` | 441 | 175 | 0.40 | −0.1990 | −0.1600 | +0.039 |
| MCL `A6_ON_COMPRESSION` | 202 | 100 | 0.50 | −0.2428 | −0.2680 | −0.025 |

**Result.** 7 of 12 pairs reach 20 trades on both arms. Over those: mean Δ = **+0.0137 R**,
median **+0.0390 R**, **4 of 7 positive**. **Wilcoxon signed-rank z = −0.507, p ≈ 0.61; sign test
p = 1.00.** No detectable effect in either direction.

**What is robust is the cost in sample: mean trade retention 0.31 — requiring alignment removes
69% of trades.** It is worse than that at the extremes: MGC `A1_ON_SWEEP` goes 87 → **2** and MCL
`A1_ON_SWEEP` 68 → **1**, and **five of twelve arms fall below the 30-trade floor purely by adding
the requirement.**

**Honest statement of what I can and cannot say.** The direction is consistent with BRIEF rule 2
("multi-timeframe agreement is not a virtue") but I **cannot** reproduce its z = −4.09: with 7
usable pairs I have no power to detect an effect of that size, so my null is a low-power null and
is not independent corroboration of the magnitude. **What my cell does establish on its own is the
sample arithmetic: on a 41-session span, a requirement that deletes 69% of trades is disqualifying
regardless of its sign, because it moves rows below the floor at which any expectancy can be
believed.** Rows like MGC `A1_ON_SWEEP`'s +0.227 R on **2 trades** are the reason the retention
column has to be read before the Δ column.

---

# 10. Recommendations to the programme, in order of what they would save

1. **Run the census pairwise, not per condition.** §2a: every zero-trade arm in every cell is a
   two-signal arm, and 8–14% of two-signal arms are jointly VOID even though both members are
   LIVE. The programme's "19.0% carry a condition that can never fire" is a lower bound. One extra
   pass over the same snapshots fixes it.
2. **Stop quoting `Trade.gross_r` as gross.** §3a. It is already net of slippage. Every
   gross-vs-net table in `scan_reports/` built from it understates gross by 1.5–3.5× the
   commission, which on a scalp cell is the difference between "costs ate a real edge" and "there
   was no edge".
3. **Assert arm-id uniqueness at emission, everywhere, not just `_id=None`.** §burst 07/6.
   `_id=None` is necessary and not sufficient: two *different* strategies whose condition
   **labels** hash the same collide anyway. My placebo construction produced 400–540 collisions per
   cell while passing `_id=None` correctly. The assertion caught it; nothing else would have.
4. **Veto fills whose lag exceeds one bar** under the session rule, and report the count either
   way. §5c: stale fills are 3–14× worse than normal ones on MGC and are 0.8–5.4% of trades, rising
   with the timeframe. Raised to EF1.
5. **Do not quote D24 against this programme's overnight rows.** §5b. It measured
   `rth_only=False` under the old regime where the position was flattened at the contract's own RTH
   close. The rule this programme runs permits the hold, so D24's sign does not transfer.
6. **Condition a Jaccard de-duplication gate on fire rate.** §2c: two filters each passing on 99%
   of bars are necessarily ~98% identical whatever they compute, and 11–16 pairs per cell exceed
   Jaccard 0.95 for that reason alone.
7. **De-duplicate any ranked list by signal set before reporting it.** §7: the raw top 10 in every
   cell is one or two conditions and eight variants. De-duplication cuts MGC from 10 rows to 2–3
   independent ones and is the single largest correction to the deliverable.
8. **Record that the 16:00–18:00 prohibition is one hour stricter than the exchange break.** §5a:
   the real CME maintenance window for MGC and MCL is 17:00–18:00, and `data/archive/` carries a
   full set of 16:00–17:00 bars. The rule forbids an hour of genuinely traded time (~4.4% of 5m
   bars). That is a choice the account owner may want to know is a choice.

---

# 11. The placebo beside every row

`code/placebo.py`, `code/run_placebo.py` → `out/placebo_<sym>_<tf>m.json`. 20 count-matched
random-bar placebos per arm, each running through the arm's **own** exit, filters and sizing in
the same `SessionWindowEngine` pass over the same frame. Signal-count matched (not trade-count
matched, so both arms face identical downstream attrition) and direction-matched.
`placebo_shift` was **not** used — D42 records that it leaks and it is conservative-only.

| cell | arms with a control | **placebo mean net E** | placebo mean trades | cell median cost | **implied placebo GROSS** | best real arm's z vs its own placebos | arms at placebo percentile 1.00 |
|---|---|---|---|---|---|---|---|
| MGC 5m | 28 | **−0.1309** | 87 | 0.0927 | **−0.038** | **+4.74** | 10 |
| MGC 15m | 34 | **−0.0123** | 61 | 0.0503 | +0.038 | +4.17 | 13 |
| MGC 30m | 30 | **−0.0228** | 49 | 0.0346 | +0.012 | +3.19 | 12 |
| MCL 15m | 28 | **−0.1115** | 52 | 0.1254 | +0.014 | +2.08 | 2 |
| MCL 5m | 26 | **−0.2203** | 62 | 0.2021 | **−0.018** | +2.39 | 3 |
| MCL 30m | 34 | **−0.0647** | 53 | 0.0835 | +0.019 | +2.04 | 5 |

**Three readings, and the second one corrected something I had already written.**

1. **The control behaves as the arithmetic says, which validates it.** At 15m and 30m implied
   placebo *gross* is **+0.012 to +0.038 R** — essentially zero, marginally positive, which is what
   a random entry with a 1.5 R target against a 1.0 R stop produces on a series with volatility
   clustering. Placebo *net* is then approximately minus the cell's cost. The control is measuring
   what it should and nothing else.

2. **At 5 minutes the placebo's gross is NEGATIVE on BOTH symbols (−0.038 R on MGC, −0.018 R on
   MCL), and that overturns my own first reading of rule 7.** In §8 I decomposed the 5-minute graveyard into a gross half and a cost half
   and called the gross half a signal-quality effect. **It is not.** The placebo entries carry no
   information by construction, so a negative *placebo* gross at 5m means the degradation belongs
   to the **exit geometry meeting a 5-minute bar grid** — a 1.0-ATR stop, a 1.5 R target, the
   engine's pessimistic stop-before-target tie rule `[repo-verified: engine.py:398-403]` and a
   2-hour time stop, all evaluated on bars six times finer. **So the non-cost half of "sub-hourly is
   a graveyard" is a statement about exits, not about signals, and it can be established with random
   entries and no search whatsoever.** §8's table stands; its interpretation is corrected here.

3. **The placebo matches or beats the median real strategy in every cell.**

| cell | placebo mean net E | **median net E of the real ≥30-trade population** | placebo verdict |
|---|---|---|---|
| MGC 5m | −0.131 | −0.132 | **ties** |
| MGC 15m | −0.012 | −0.046 | **placebo wins** |
| MGC 30m | −0.023 | −0.049 | **placebo wins** |
| MCL 5m | −0.220 | −0.241 | **placebo wins** |
| MCL 15m | −0.112 | −0.143 | **placebo wins** |
| MCL 30m | −0.065 | −0.093 | **placebo wins** |

That is the programme's own placebo finding ("five separate placebo constructions matched or beat
the real thing") reproduced under a session rule that has never been run — and in a sharper form,
because at 15m and 30m the placebo does not merely match the median, it **beats** it.

**And pre-registered arms are significantly WORSE than their own placebos on both symbols.**
MGC 5m: `A1_ON_SWEEP` percentile **0.00**, z = **−2.99**; `A6_ON_COMPRESSION` percentile **0.00**,
z = **−2.69**; `A4_VWAP_BAND` percentile 0.05, z = −1.49. MCL 5m: `A2_PD_SWEEP` percentile **0.00**,
z = **−2.32**; `A4_VWAP_BAND` percentile 0.15, z = −1.33. MGC 15m: `A1_ON_SWEEP` percentile **0.00**,
z = **−3.10**. Note `A1_ON_SWEEP` is z = −2.99 on MGC 5m and z = −3.10 on MGC 15m — the same
pre-registered hypothesis, beaten by its own control, on two independent timeframes of the same
symbol. A placebo beating a real signal has
happened five times in this repository. **A real signal losing to its own placebo at z = −3 is a
different and stronger statement**: both arms share the exit, the sizing and the session rule, so
the difference is attributable to where the entry fires, and the condition is not uninformative but
*anti*-informative in that cell.

**Where the real rows do separate.** The top rows are not reproduced by their own controls:
placebo z = +1.2 to +2.9 for MGC's survivors, +1.1 to +1.3 for MCL's. That is a real distinction
and it is **not a licence to report them**, because the row was selected as the extreme of a
2,800–3,600-arm screen and its 20-placebo z carries no multiple-testing correction at all. A z of
+2.9 against 20 controls, for the best of 3,591 arms, is what noise looks like at that width.

---

# 12. What I hand you: the rows, and the count of them

`code/rank_final.py` → `out/rank_final.json`. De-duplicated by **signal set** (filters excluded),
keeping the variant with the largest out-of-sample trade count, because §7 shows the raw top 10 in
every cell is one or two conditions and eight variants of them.

Promotion required all four of: ≥30 trades in the full sample **and** in both halves; the same
**sign** in-sample and out-of-sample; positive in **every** walk-forward fold reaching 10 trades;
and **t ≥ the declared `free_t` of its own track**.

## The count, which is the answer

| symbol | distinct signal sets meeting the sample floor | sign-consistent, positive, positive in every fold | **clearing their declared threshold (`free_t` = 4.441)** |
|---|---|---|---|
| **MGC** | 401 | **19** | **0** |
| **MCL** | 360 | **3** | **0** |

**Zero rows are live-eligible. I am handing you a candidate list of 5 for MGC and 3 for MCL, and
the statement that none of them clears.** Largest t anywhere in my cell is **+2.62** against a
required **4.441**; MCL's largest is **+1.12**, which fails even `free_t = 1.177` — the code's own
floor for a *single pre-registered* hypothesis, the most generous threshold available anywhere in
this repository. **On MCL the answer is nothing, at every threshold.**

## MGC — 5 candidates, none live-eligible

All Track B (n = 19,152 declared, `free_t` = 4.441). Gross reconstructed from the fill geometry;
`cost` is commission + slippage in R. Every number `[measured: out/rank_final.json]`.

| # | tf | signal set | n | win rate | avg win R | avg loss R | R/R | PF | **gross E** | cost | **net E** | **t** | Sharpe/trade | **Sharpe ann.** | Sortino | max DD | avg DD | max cons W / L | hold | avg MAE | avg MFE | % outside RTH | exits (STOP / TARGET / 16:00 flat) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 15m | `candle_engulfing + structure_trend` | 121 | 0.537 | +1.441 | −1.030 | 1.399 | 1.624 | +0.3504 | 0.0531 | **+0.2973** | **+2.62** | 0.238 | **6.58** | 0.421 | 7.04 R | 0.96 R | 7 / 5 | 55 m | 0.942 | 1.423 | 73.6% | 45.5 / 52.1 / 2.5% |
| 2 | 30m | `candle_close_strength + poc_reversion` | 78 | 0.513 | +1.468 | −0.967 | 1.519 | 1.599 | +0.3189 | 0.0369 | **+0.2820** | +2.02 | 0.229 | 5.08 | 0.407 | 6.01 R | 1.00 R | 4 / 5 | 87 m | 0.899 | 1.358 | 83.3% | 44.9 / 50.0 / 5.1% |
| 3 | 15m | `above_vwap + poc_reversion` | 87 | 0.506 | +1.483 | −1.031 | 1.439 | 1.472 | +0.2999 | 0.0593 | **+0.2406** | +1.78 | 0.191 | 4.47 | 0.330 | 8.20 R | 1.01 R | 5 / 4 | 57 m | 0.917 | 1.310 | 94.3% | 48.3 / 50.6 / 1.1% |
| 4 | 15m | `poc_reversion + pullback_to_support` | 159 | 0.491 | +1.439 | −1.010 | 1.425 | 1.372 | +0.2474 | 0.0560 | **+0.1914** | +1.95 | 0.155 | 4.90 | 0.263 | 7.57 R | 0.97 R | 10 / 6 | 57 m | 0.915 | 1.250 | 78.6% | 47.8 / 46.5 / 5.7% |
| 5 | 30m | `imbalance_pullback` | 170 | 0.529 | +1.250 | −1.008 | 1.240 | 1.395 | +0.2174 | 0.0299 | **+0.1875** | +2.08 | 0.159 | 5.22 | 0.270 | 5.23 R | 0.94 R | 5 / 5 | 112 m | 0.923 | 1.175 | 50.0% | 45.3 / 39.4 / 14.7% |

Split sample, walk-forward and control, same five rows:

| # | IS net E (n) | **OOS net E (n)** | fold 1 | fold 2 | fold 3 | **placebo mean E** | placebo percentile | **placebo z** |
|---|---|---|---|---|---|---|---|---|
| 1 | +0.347 (75) | **+0.216 (46)** | +0.17 / 32 | +0.46 / 47 | +0.22 / 42 | +0.010 | 1.00 | **+2.34** |
| 2 | +0.098 (46) | **+0.546 (32)** | +0.01 / 25 | +0.21 / 21 | +0.55 / 32 | −0.001 | 0.95 | +1.68 |
| 3 | +0.301 (55) | **+0.137 (32)** | +0.15 / 28 | +0.45 / 27 | +0.14 / 32 | −0.003 | 1.00 | +2.16 |
| 4 | +0.087 (97) | **+0.355 (62)** | +0.15 / 42 | +0.02 / 56 | +0.38 / 61 | −0.027 | 1.00 | +2.03 |
| 5 | +0.202 (95) | **+0.169 (75)** | +0.09 / 47 | +0.28 / 55 | +0.18 / 68 | −0.009 | 1.00 | +1.90 |

**The power bound, made vivid by row 1.** Its annualised Sharpe is **6.58** — a number that does
not exist in real futures trading — and on a 0.1585-year span that still only produces t = +2.62
against the **4.441** its 19,152-arm search width demands. `6.58 × 0.398 = 2.62`. **The row would
need a sustained annualised Sharpe of 11.16 to clear.** That is the bound, in a row, not in a
footnote.

Two further rows survive the sign and fold tests but are weaker and live in `out/rank_final.json`
rather than here: `candle_engulfing + value_area_breakout` (15m, n = 111, net +0.1799, t = +1.54,
OOS +0.019, placebo z = +1.20) and `above_vwap + imbalance_pullback` (30m, n = 92, net +0.1673,
t = +1.35, OOS +0.008, placebo z = +1.94).

**Read the list as three condition families, not five rows.** `poc_reversion` carries rows 2, 3 and
4; `imbalance_pullback` carries row 5; `candle_engulfing` carries row 1. **Rows 2–4 are not
independent evidence for each other**, and neither is row 5 for the sixth row in the paragraph
above.

## MCL — 3 candidates, none live-eligible, and none clearing even `free_t = 1.177`

| # | tf | signal set | n | win rate | avg win R | avg loss R | R/R | PF | **gross E** | cost | **net E** | **t** | Sharpe/trade | Sharpe ann. | Sortino | max DD | avg DD | max cons W / L | hold | avg MAE | avg MFE | % outside RTH | exits (STOP / TARGET / 16:00 flat) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 30m | `delta_divergence + keltner_outside` | 95 | 0.463 | +1.424 | −0.992 | 1.435 | 1.238 | +0.2116 | 0.0846 | **+0.1270** | +1.00 | 0.102 | 2.51 | 0.169 | 8.38 R | 0.89 R | 4 / 7 | 99 m | 0.951 | 1.135 | 70.5% | 48.4 / 42.1 / 9.5% |
| 2 | 30m | `bollinger_extreme` | 152 | 0.474 | +1.408 | −1.051 | 1.340 | 1.206 | +0.2009 | 0.0871 | **+0.1138** | **+1.12** | 0.091 | 2.81 | 0.148 | 10.59 R | 0.69 R | 8 / 6 | 83 m | 1.041 | 1.131 | 73.7% | 50.7 / 43.4 / 5.9% |
| 3 | 30m | `candle_engulfing + value_area_breakout` | 74 | 0.473 | +1.324 | −1.017 | 1.302 | 1.169 | +0.1765 | 0.0861 | **+0.0903** | +0.63 | 0.073 | 1.57 | 0.113 | 4.28 R | 1.17 R | 4 / 3 | 87 m | 0.868 | 1.078 | 77.0% | 45.9 / 41.9 / 12.2% |

| # | IS net E (n) | **OOS net E (n)** | fold 1 | fold 2 | fold 3 | placebo mean E | placebo percentile | placebo z |
|---|---|---|---|---|---|---|---|---|
| 1 | +0.085 (58) | **+0.193 (37)** | +0.06 / 34 | +0.22 / 26 | +0.12 / 35 | −0.041 | 0.85 | +1.13 |
| 2 | +0.105 (86) | **+0.125 (66)** | +0.04 / 42 | +0.20 / 49 | +0.10 / 61 | −0.035 | 0.90 | +1.18 |
| 3 | +0.142 (44) | **+0.014 (30)** | +0.08 / 26 | +0.15 / 20 | +0.05 / 28 | −0.065 | 0.90 | +1.23 |

**MCL's largest t anywhere is +1.12, which fails `free_t = 1.177`** — the code's own floor for a
single pre-registered hypothesis and the most generous threshold available in this repository.
**On MCL the answer is nothing, at every threshold, including the one nobody has ever had to use.**

**All three are 30-minute rows. Nothing at MCL 5m or 15m survives** — the same boundary rule 7 drew
in §8, arriving from a different direction. And the cost column is the mechanism: **0.085–0.087 R
against MGC's 0.030–0.059 R.** MCL's gross expectancies (+0.18 to +0.21) are comparable to MGC's
(+0.22 to +0.35) and its net ones are roughly half. That is MCL's cost-fragility as arithmetic
rather than as a warning.

---

# 13. The one thing I would ask the parent session to carry into `RESULTS.md`

Not the eight rows. **The count.** 401 distinct MGC signal sets and 360 MCL ones reached the sample
floor; 19 and 3 survived sign-consistency and every walk-forward fold; **0 and 0 cleared their own
declared threshold.** Largest t in the cell is +2.62 against a required 4.441, and MCL's largest is
+1.12 against 1.177.

And the reason, which is not "the market is efficient" and not "these rules do not work". It is:
**0.1585 years, √0.1585 = 0.398, and a search width of 19,152.** On that span, clearing the
threshold would have needed a sustained annualised Sharpe of **11.16**. The best row in my cell
achieved **6.58** — extraordinary, and 41% short. **That is a property of the experiment, not a
discovery about MGC or MCL.**

If the programme wants a scalp answer that can clear anything, it needs one of two things and
neither is a harder search:

1. **Span.** At 10 years, `free_t = 4.441` needs an annualised Sharpe of 1.40; at 25 years, 0.89.
   Row 1's measured 6.58 clears both by a wide margin. The scalp timeframes cannot get there —
   Yahoo caps 5-minute lookback far below it — so this is a swing-timeframe route, not mine.
2. **A genuinely pre-registered hypothesis, written down before looking, at n = 1.** `free_t` =
   1.177 needs an annualised Sharpe of 2.96, which is 45% of what row 1 measured. **That is the
   only route available on 57 days**, and it costs the right to search: the hypothesis must be
   fixed in writing first, and each one spends its single shot. My Track A was exactly this attempt
   with n = 36; its result was that **three of six MGC 5m hypotheses were significantly
   *negative*.** That is what a pre-registered scalp study on this span can produce: rejections.

---

# Appendix — reproduction, and where the numbers live

`out/run_<sym>_<tf>m_both.json` (~21 MB each) are **gzipped in place** as `.json.gz` and a
`_summary.json` beside each carries every field any table above is computed from. Nothing was
deleted. `code/trim_out.py` did it and says exactly what it kept.

| artefact | produced by | what it holds |
|---|---|---|
| `out/power_bound.json` | `code/power.py` | span, sessions, √years, required Sharpe per cell |
| `out/cost_in_r.json` | `code/cost_in_r.py` | all-in cost in R by cell × stop × thin-book |
| `out/census.json` | `code/census.py` | 79 conditions × 8 cells, fire counts and verdicts |
| `out/degeneracy.json` | `code/degeneracy.py` | always-on, duplicates, fires lost to the prohibition |
| `out/or_resolvability.json` | `code/or_resolvability.py` | the opening-range object, per cell |
| `out/population_size.json` | `code/population.py` | the declared *n* for each track |
| `out/run_*_both*.json*` | `code/run_cell.py` | every arm, full sample + IS + OOS + 3 folds |
| `out/placebo_*.json` | `code/run_placebo.py` | 20 controls per reported arm |
| `out/mtf_arms.json` | `code/mtf_arms.py` | the 12 pre-registered alignment pairs |
| `out/analysis_rule7.json` | `code/analyse.py` | the rule-7 replication |
| `out/analysis_split.json` | `code/analyse2.py` | split sample, selection test, walk-forward |
| `out/selection_control.json` | `code/selection_control.py` | random-10, matched-10, reverse-time |
| `out/selection_direction.json` | `code/selection_direction.py` | the drift control |
| `out/rank_final.json` | `code/rank_final.py` | the de-duplicated ranked lists |
| `out/audit_lookahead.json` | `code/audit_lookahead.py` | prefix invariance, 5,274 comparisons |
| `out/audit_fills.json` | `code/audit_fills.py` | fill model + gap census |
| `out/audit_stale_fills.json` | `code/audit_stale_fills.py` | the weekend-gap stale fill |

## Every claim's provenance, in one place

Repo facts are marked `[repo-verified: path:line]` inline. The load-bearing ones:
`engine.py:231` (one position per strategy), `:291-297` (fill at next open), `:351,:411`
(thin-book), `:352,:414` (slippage into the fill price), `:363-370` (stop honoured, risk
re-derived), `:398-403` (stop wins a tie), `:404-406` (time stop in primary bars),
`:468-472` (the wrong session clock), `:494-499` (commission in `_close`);
`base.py:154-155` (`Condition.label`), `:296-300` (VWAP_BAND inputs), `:301-306` (RANGE reads
the opening range), `:313-314` (the silent stop floor), `:393` (`rth_only` default True),
`:585,:606-623` (the memoised `_id`), `:670-703` (strict AND + direction agreement);
`features.py:862-895` (the hard-coded 30-minute opening range), `:881-885` (the
self-referential session extreme), `library.py:935-939` (profile reads the prior session);
`timeutil.py:169-180` (`trading_day` rolls at 18:00).

## What is NOT claimed here

- **No profitability number above is a programme result until EF1 declares validation.** They are
  measured on EF1's `SessionWindowEngine`, which changed once mid-study (§burst 07/7 shows the
  change was a no-op in my cells), and EF1 owns the verdict on it.
- **No number here transfers to MES or MNQ**, or between MGC and MCL, or between 5m, 15m and 30m.
  Every table is per (symbol, timeframe) for that reason.
- **No claim that any of the 8 candidate rows will make money.** Zero cleared their declared
  threshold. The row-level statistics are reported so the parent session can see exactly how far
  short they fall, not so they can be traded.
