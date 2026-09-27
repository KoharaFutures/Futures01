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

---

## Contents

| burst | subject |
|---|---|
| `bursts/01_power-bound.md` | the exact power bound per cell, and the per-trade restatement |
| `bursts/02_cost-in-R.md` | cost as a fraction of R per cell; the `min_stop_ticks` floor |
| `bursts/03_census.md` | the firing-rate census, 79 conditions × 8 cells |
| `bursts/04_session-rule-degeneracy.md` | always-on filters, duplicates, and what the 16:00–18:00 rule removes |
| `bursts/05_population-declared.md` | the population and its exact size, declared before measuring |
| `bursts/06_measurement.md` | rule 7, the split sample, the selection test, walk-forward |

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

**Then the arms.** Census gating cut the never-trade rate hard: **6.1–13.7% of my declared arms
took zero trades**, against the programme-wide figure of 82% of generated strategies never
trading. That is the census doing its job.

## 2a. But the per-condition census under-counts, and I can say by how much

**Every single zero-trade arm in every cell is a TWO-SIGNAL arm. Not one single-signal arm took
zero trades anywhere**, and 95–99% of the zero-trade arms generated **zero signals** — meaning
their two LIVE conditions never co-fired with an agreeing direction on any bar.

`[measured: over out/run_*_both.json]`

| cell | zero-trade arms | all of which are 2-signal | jointly-VOID pairs as a share of 2-signal arms |
|---|---|---|---|
| MGC 15m | 290 | 290 | 277 / 3,150 = **8.8%** |
| MGC 30m | 493 | 493 | 469 / 3,360 = **14.0%** |
| MCL 15m | 207 | 207 | 205 / 2,597 = **7.9%** |
| MCL 30m | 413 | 413 | 411 / 3,150 = **13.0%** |

`Strategy.evaluate` is a strict AND **and** requires every SIGNAL to name the *same* direction
`[repo-verified: base.py:670-703]`. **So two LIVE conditions can be jointly VOID, and a
per-condition census cannot see it.** The programme's "19.0% of generated strategies carry a
condition that can never fire" is therefore a *lower bound* on the dead population; the
pairwise term adds 8–14% more on top in my cells, and it is again worse at 30m.

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
| MGC 15m | 653 | **+0.042** | +0.381 → **+0.147** | −0.032 → −0.089 | selection wins |
| MGC 30m | 348 | +0.221 | +0.220 → **+0.122** | −0.043 → −0.060 | selection wins |
| MCL 15m | 552 | +0.309 | +0.256 → **−0.147** | −0.131 → −0.136 | selection **loses** |
| MCL 30m | 420 | +0.207 | +0.185 → **−0.021** | −0.075 → −0.120 | selection wins |

## The four controls, and the one that settles it

**Control 1 — RANDOM-10** (draw 10 arms uniformly from the same universe, pool the same way,
2,000 draws). Random-10 lands within 0.0003 R of the trade-weighted universe every time, so the
pooling itself is not broken. The real top 10 sits at **percentile 1.000, 1.000, 0.402, 0.985**.

**Control 2 — MATCHED-10** (10 arms whose in-sample trade counts match the top 10's, 2,000
draws). This matters because the top 10 trade *less* than the universe (median IS trades 60 vs
96, 66 vs 83, 47 vs 84, 54 vs 64). After matching, the top 10 sits at percentile **1.000, 0.995,
0.729, 0.960**. So trade count is not the explanation.

**Control 3 — direction.** Over this window MGC ran 4151 → 4321 (+4.1%) and MCL 84.63 → 92.41
(+9.2%), so a long-biased arm is favoured for a reason that has nothing to do with its rule. It
is not the explanation either: the top 10's long share is **0.478 / 0.533 / 0.467 / 0.539**
against random-40's **0.498 / 0.519 / 0.535 / 0.522**, and forcing the top 10 LONG-only and
SHORT-only gives **both signs positive** on MGC (15m +0.284 / +0.285; 30m +0.126 / +0.216) and on
MCL 30m (+0.057 / +0.103). Only MCL 15m splits (+0.200 long, −0.065 short). **The effect is
direction-symmetric, so it is not drift.**

**Control 4 — REVERSE TIME, and this is the one that settles it.** Select on the *last* 16
sessions and score on the *first* 25. **Selection wins in all four cells** (MGC 15m −0.008 vs
−0.032; MGC 30m +0.050 vs −0.043; MCL 15m −0.117 vs −0.131; MCL 30m +0.005 vs −0.075).

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

Nine to twelve distinct conditions across ten "different" rows, mean pairwise condition Jaccard
0.12–0.33. **So the top 10 is one or two conditions and eight variants of them**, their trade
lists overlap heavily, and the pooled 351–505 out-of-sample trades are nowhere near 351–505
independent observations — the standard error on that +0.147 R is understated by an unknown but
large factor. This is precisely the ORB/ICT report's lesson: *"a league table of the best rule
sets containing a condition measures the search, not the condition."*

**Verdict on the selection test.** The programme's "selecting is worse than not selecting" does
**not** reproduce in this cell — but the correct replacement claim is not "selecting works". It
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
   **gross** degradation at 5 minutes — the signal is worse there, not just more expensive. Cost
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
