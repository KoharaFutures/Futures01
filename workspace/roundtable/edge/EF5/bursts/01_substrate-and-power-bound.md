# EF5 burst 01 — the substrate for the SCALP cell, and the power bound it fixes

Cell: **SCALP, MES + MNQ, 5m / 15m / 30m.** Six cells. Written before any strategy was built.

## 1. Substrate, named and verified

Every EF5 number is measured on **`data/archive/{SYM}_{TF}m.jsonl`** — the append-only ET-stamped
store — loaded by `EF5/code/ef5_data.py:load_series`. Native bars per timeframe, no resampling of
the primary series.

`[measured: EF5/code/ef5_data.py → EF5/out/substrate.json]`

| cell | bars | first (ET) | last (ET) | calendar days | 18:00→16:00 cycles | in-session bars |
|---|---|---|---|---|---|---|
| MES 5m | 11,182 | 2026-07-29 19:20 | 2026-09-25 16:55 | 57 | **41** | 10,689 |
| MES 15m | 3,744 | 2026-07-29 19:15 | 2026-09-25 16:45 | 57 | 41 | 3,579 |
| MES 30m | 1,873 | 2026-07-29 19:00 | 2026-09-25 16:30 | 57 | 41 | 1,790 |
| MNQ 5m | 11,182 | same stamps | same stamps | 57 | 41 | 10,689 |
| MNQ 15m | 3,744 | | | 57 | 41 | 3,579 |
| MNQ 30m | 1,873 | | | 57 | 41 | 1,790 |

Matches the EDGE_BRIEF substrate table (5m ~11,215 / 15m ~3,745 / 30m ~1,874) to within 33 bars,
so the brief's table is the archive, not `csv/raw`.

### Store equivalence, verified for MY symbols and MY timeframes (data-policy condition 2)

`[measured: /tmp scratch script, both stores normalised to UTC before comparison]`

| cell | archive | csv/raw | overlap | close bit-exact | max abs Δclose | archive bars **before** csv/raw starts |
|---|---|---|---|---|---|---|
| MES 5m | 11,182 | 5,000 | 5,000 | 4,999 / 5,000 | 2.500e-01 | **5,370** |
| MES 15m | 3,744 | 3,753 | 3,472 | 3,472 / 3,472 | 0.0 | 0 |
| MES 30m | 1,873 | 1,877 | 1,737 | 1,737 / 1,737 | 0.0 | 0 |
| MNQ 5m | 11,182 | 5,000 | 5,000 | 4,999 / 5,000 | 7.500e-01 | **5,369** |
| MNQ 15m | 3,744 | 3,752 | 3,471 | 3,471 / 3,471 | 0.0 | 0 |
| MNQ 30m | 1,873 | 1,876 | 1,736 | 1,736 / 1,736 | 0.0 | 0 |

**Two corrections to how the data policy generalises, both specific to my timeframes.**

1. **The single non-bit-exact close at 5m is not float noise and is not a vendor discrepancy — it is
   the *last bar* of the `csv/raw` snapshot, caught developing.** Located exactly: on both symbols
   the only disagreeing close is `2026-09-22T23:00Z`, MES 7832.25 (archive, v=309) vs 7832.00 (raw,
   v=225); MNQ 31048.50 (v=2331) vs 31047.75 (v=2016). Archive volume is strictly larger — a
   finalised bar against a partial one. Two further bars differ in volume only
   (`2026-09-22T04:05Z` raw v=0, `2026-09-22T22:00Z` archive v=0). Everything else is bit-exact.
   **Do not assert `==` across the two stores on the boundary bar.**
2. **The archive extends the span at 5m and NOT at 15m/30m.** At 5m it adds ~5,370 bars *before*
   `csv/raw` begins. At 15m and 30m `csv/raw` starts **three days earlier** than the archive
   (2026-07-26 vs 2026-07-29), so the archive adds zero prior history — same shape as R5's
   correction at 1m. The archive is still the right substrate for 15m/30m because it is *longer
   overall* (ends 2026-09-25 vs 2026-09-22) and because it is the store the rest of the programme
   uses; but "the archive extends the span" is a **5-minute** fact in my cell, not a 15m/30m one.

## 2. The power bound — identical in all six cells, and it is the headline

`t ≈ SR_ann · sqrt(years)`. Exactly, if a strategy takes *n* trades over *T* years with per-trade
mean μ and s.d. σ, then the trade-level `t = (μ/σ)·sqrt(n)` and the equity-curve annualised Sharpe
is `SR_ann = (μ/σ)·sqrt(n/T)`, so **`t = SR_ann · sqrt(T)` regardless of n**. The span, not the
trade count, is what buys statistical confidence.

`[measured: EF5/out/substrate.json]`

```
span            = 0.1585 years   (57.9 calendar days, 41 x 18:00->16:00 cycles)
sqrt(span)      = 0.3981
```

| threshold | annualised Sharpe an EF5 row must sustain to clear it |
|---|---|
| `free_t = 1.177` — ONE pre-registered hypothesis | **2.96** |
| `free_t = 3.00` — a ~90-variant search | 7.54 |
| `free_t = 4.00` — a ~3,000-variant search | 10.05 |
| `free_t = 4.40` — a ~15,000-variant search | 11.05 |
| largest *t* ever found in this programme, 3.923 | 9.85 |

**A search-width threshold is arithmetically unreachable in this cell and I am not going to pretend
otherwise.** A sustained annualised Sharpe of 7.5 is not a thing that exists in listed futures; 2.96
is at the outer edge of what a genuinely good intraday programme achieves, and it is the bar for a
*single* hypothesis fixed in writing in advance — which a top-10 ranking, by construction, is not.

So the honest form of the EF5 deliverable is: **a description of 41 sessions, with the forward
behaviour of that description measured and reported beside it.** Anything stronger than that is not
available at 0.1585 years and no amount of trade count fixes it, because trade count does not enter
the relation above.

### The other half of the bound: cost as a share of R

The EDGE_BRIEF states cost is 15.0% of R at 5m against 4.6% at 60m. That is the same direction as
the span problem: at 5m a strategy must earn 0.15R before it earns anything, so the expectancy
distribution the ranking sorts is shifted left by more than the effect most rows would claim.
**Every EF5 row is ranked on expectancy in R net of costs**, never gross.
