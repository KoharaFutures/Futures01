# EF6 burst 01 — deflation accounting for THIS programme, and the answer to "is a top 10 answerable at 57 days"

**Built:** `EF6/code/deflation.py`. One function, `threshold(n, span_days)`, plus
`for_cell(symbol, timeframes, n)`, `max_n_answerable(span, assumed_SR)` and
`topn_threshold(span, n_reported, n_screened)`.

## The spans, measured rather than inherited

`[measured: python3 over data/archive/*.jsonl, first and last ts per (symbol, tf), 2026-09-27]`

| tf | n bars (MGC/MCL/MES/MNQ) | first → last | calendar days | years | sqrt(years) |
|---|---|---|---|---|---|
| 1m | 6881 / 6872 / 6845 / 6846 | 2026-09-20 → 2026-09-25 | **4.95** | 0.014 | 0.116 |
| 5m | 11216 / 11212 / 11182 / 11182 | 2026-07-29 → 2026-09-25 | **57.90** | 0.159 | 0.398 |
| 15m | 3746 / 3744 / 3744 / 3744 | 2026-07-29 → 2026-09-25 | **57.90** | 0.159 | 0.398 |
| 30m | 1875 / 1873 / 1873 / 1873 | 2026-07-29 → 2026-09-25 | **57.90** | 0.159 | 0.398 |
| 60m | 11297 / 10934 / 11287 / 11291 | 2024-10-06 → 2026-09-25 | **718.88** | 1.968 | 1.403 |
| 240m | 3052 / 2990 / 3050 / 3050 | 2024-10-06 → 2026-09-25 | **718.83** | 1.968 | 1.403 |
| 1440m | 4008 / **1** / 1863 / 1863 | MGC 2010-10-04, MES/MNQ 2019-05-03 | MGC **5835**, MES/MNQ **2702**, MCL n/a | 15.98 / 7.40 | 3.997 / 2.720 |

The brief's 57 and 718 are confirmed to two decimals. **Two corrections to the brief's
substrate table, both measured:**

1. **1440m is not one row.** MGC daily is 15.98 years, MES/MNQ 7.40 years, and **MCL daily does
   not exist** (`MCL_1440m.jsonl` = 1 line). The brief lists only MGC's 5,835 days. The daily
   cell is the *only* cell in this programme with enough span to answer anything at width —
   see the budget table below — and it is also the cell where the 18:00→16:00 rule is nearly
   degenerate, because the 22-hour hold cap is about one daily bar.
2. `SPAN_DAYS[("MCL", 1440)]` is deliberately **absent** from the module and `for_cell` raises
   on it rather than guessing. An agent that silently got 5835 for MCL daily would understate
   the required Sharpe by 4.5×.

## Convention check — calendar days vs trading sessions does not matter here

`BRIEF.md` annualises with calendar days / 365.25 (322/365.25 = 0.939), so I kept that. Checked
against the alternative: the 5m series holds **49 distinct calendar dates** ≈ 41 18:00→16:00
sessions → 41/252 = 0.163 y, sqrt **0.403** against 0.398. The 60m series holds **596 dates**
≈ 490 sessions → 1.944 y, sqrt **1.394** against 1.403. `[measured: distinct ts[:10] counts]`
Three-decimal agreement. The convention is not load-bearing, so no one needs to argue about it.

## The identity, so nobody treats it as a rule of thumb

`t ≈ SR × sqrt(years)` is **exact** given the usual definitions, not an approximation:

```
t          = mean(R) / se(mean R) = sqrt(N) · mean(R)/sd(R)
SR_annual  = (mean(R)/sd(R)) · sqrt(N / Y)        # N trades over Y years
⇒  t       = SR_annual · sqrt(Y)
```

So dividing a threshold in *t* by `sqrt(Y)` gives the **annualised Sharpe that threshold
demands**, which is the number a reader can actually judge.

## What the function returns for the programme's cells

`free_t(n) = sqrt(2·ln max(2,n))`, `required annual Sharpe = free_t / sqrt(Y)`:

| n screened | SCALP 5/15/30m (sqrt y = 0.398) | SWING 60/240m (sqrt y = 1.403) |
|---|---|---|
| 1 (single pre-registered) — floor 1.177 | **2.96** | **0.84** |
| 10 — the floor for *any* top 10 | 5.39 | **1.53** |
| 100 | 7.62 | 2.16 |
| 1,000 | 9.34 | 2.65 |
| 10,000 | 10.78 | 3.06 |
| 40,000 | 11.56 | 3.28 |
| 2,975,629 (the historical number — **not this programme's**) | 13.71 | 3.89 |

**Nobody should quote 5.46.** It is the threshold for a search this programme has not run. At
40,000 variants the number is 4.60; at 1,000 it is 3.72.

## The inverse, which is the operationally useful direction — your search budget

`n_max = exp(SR² · Y / 2)`. A strategy whose *true* annualised Sharpe is SR produces an expected
t of `SR·sqrt(Y)`; if that is below `free_t(n)` the search is wider than the evidence can pay for.

| assumed **true** annual Sharpe | SCALP: max n screenable | SWING: max n screenable | MGC DAILY: max n |
|---|---|---|---|
| 0.75 | **0 — unanswerable at any width** | **0** | 89 |
| 1.00 | **0** | 2 | 2,944 |
| 1.50 | **0** | 9 | 6.4 × 10⁷ |
| 2.00 | **0** | 51 | 7.5 × 10¹³ |
| 2.50 | **0** | 468 | — |
| 3.00 | 2 | 7,022 | — |

1m (4.95 days) is **0 at every Sharpe up to 3.0**. There is no question the 1-minute substrate
can answer.

## The answer the caller asked for early: **a scalp top 10 is not answerable at 57 days**

This is arithmetic, and it does not depend on any assumption about the market:

1. **A top 10 presupposes n ≥ 10.** There is no top 10 of one candidate. So the *most generous*
   threshold any top-10 list can be given is `free_t(10) = 2.146`.
2. On the scalp span, clearing 2.146 requires the **#1 row** to have a sustained annualised
   Sharpe of **5.39**. At a realistic search width of 1,000 it is **9.34**.
3. **And the strong form: the scalp verdict does not depend on the multiple-testing
   assumption at all.** `free_t`'s floor is 1.177 — the threshold for one hypothesis fixed in
   writing before looking — and clearing *that* on 57.90 days needs **SR 2.96**. Correlation
   between rule sets, clone collapse, effective-vs-nominal n: none of it can lower the bar
   below 1.177, because 1.177 *is* the bar at n = 1.

So the scalp half of this task is a **description of 41 trading sessions**, not a forecast, and
every scalp row must carry that sentence. This is the same conclusion `EDGE_BRIEF.md:50-54`
reached; I have verified it from the measured span rather than inheriting it, and I have added
the part that makes it binding — the `n ≥ 10` floor, which removes the escape route of
"we only report ten so our n is ten".

**The swing half is different and the difference is actionable.** `free_t(10)/1.403 = 1.53`. A
sustained annualised Sharpe of 1.53 is demanding but it is a real number that real systematic
futures strategies reach. **So a swing top 10 is answerable — and only if the search that
produced it is about ten wide.** Screen 40,000 to pick 10 and the required Sharpe is 3.28 and
the answer is gone. The deflation cost is paid on what you *screened*, never on what you
*reported*, so this is a constraint on EF2–EF5's method rather than on their write-up:

> **Pre-register a short list of swing hypotheses and measure those. Do not generate a
> population and rank it.** At 60m/240m the budget is 9 variants at an assumed SR of 1.5 and
> 51 at SR 2.0.

## Anti-overfitting checks made in this burst

| hazard | checked | finding |
|---|---|---|
| quoting a stale threshold | yes | 5.46 belongs to ~2.98M historical evaluations; the module refuses to hardcode it as a threshold and exposes it only as `PROGRAMME_WIDE_FREE_T` for context |
| span overstated for a multi-timeframe group | yes | `group_span_days` takes the **minimum** member span. A 5m+60m group is 57.90 days, not 718.88 — taking the coarse member would overstate `sqrt(years)` 3.5× and understate the required Sharpe by the same factor |
| a missing span silently defaulting | yes | MCL 1440m is absent from `SPAN_DAYS` and `for_cell` raises `KeyError` naming the reason |
| independence of the n statistics | yes, and it is the one assumption in the module | `sqrt(2·ln n)` is the expected max of n *independent* normals. Rule sets in a cell are heavily correlated, so effective n < nominal n and the true threshold is somewhat below `free_t(n)`. Direction of the error is *known* and the magnitude is small because the function is logarithmic (`BRIEF.md`: removing 91% of the denominator moves 5.46 → 5.00). **It cannot rescue the scalp cells, because the n=1 floor of 1.177 already requires SR 2.96.** |
| survivorship / look-ahead / repainting | n/a | no price data touched in this burst beyond first and last timestamps |
