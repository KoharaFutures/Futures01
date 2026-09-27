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
