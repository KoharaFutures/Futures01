# EF4 burst 01 — the exact power bound for the six scalp cells

`code/power.py` → `out/power_bound.json`. Pure arithmetic on the substrate; no strategy,
nothing to overfit. Substrate: `data/archive/` (`MGC|MCL_{5,15,30}m.jsonl`).

## The span, measured

`[measured: python3 workspace/roundtable/edge/EF4/code/power.py]`

| cell | bars | first → last | calendar days | years | √years | 18:00→16:00 sessions | bars in the 16:00–18:00 gap | bars/session |
|---|---|---|---|---|---|---|---|---|
| MGC 5m | 11,216 | 2026-07-29T19:20 → 2026-09-25T16:55 | 57.90 | 0.1585 | 0.398 | **41** | 495 | 261.5 |
| MGC 15m | 3,746 | same | 57.90 | 0.1585 | 0.398 | **41** | 167 | 87.3 |
| MGC 30m | 1,875 | same | 57.90 | 0.1585 | 0.398 | **41** | 85 | 43.7 |
| MCL 5m | 11,212 | same | 57.90 | 0.1585 | 0.398 | **41** | 493 | 261.4 |
| MCL 15m | 3,744 | same | 57.90 | 0.1585 | 0.398 | **41** | 165 | 87.3 |
| MCL 30m | 1,873 | same | 57.90 | 0.1585 | 0.398 | **41** | 83 | 43.7 |

All six cells share one span to the minute. **√years = 0.398**, so the Sharpe a cell
must sustain to produce a given *t* is:

| target | annualised Sharpe required on 0.1585 years |
|---|---|
| `free_t = 1.177` (one pre-registered hypothesis) | **2.96** |
| `t = 1.96` (nominal 5%, no deflation) | **4.92** |
| `t = 3.923` (largest *t* ever found in this programme) | **9.85** |
| `free_t` at n = 1,000 variants (3.717) | **9.38** |
| `free_t` at n = 5,000 variants (4.127) | **10.42** |
| `free_t` at n = 20,000 variants (4.451) | **11.23** |

The dispatch said 2.98; the exact span gives **2.96**. Same verdict.

## The correction that matters: the annualised-Sharpe bound is not the operative one

`t = SR_ann × √years` and `t = (µ/σ) × √N` are **the same identity**, not two bounds.
For *N* trades in *Y* years the trade rate is *N/Y*, so
`SR_ann = (µ/σ)·√(N/Y)` and `SR_ann·√Y = (µ/σ)·√N`. Exactly.

That matters because **a scalp cell's annualisation factor is large**. "Annualised
Sharpe 2.96" sounds unreachable; expressed per trade at the trade counts a scalp cell
can actually produce, it is not:

| trades in the window | per-trade µ/σ needed for `t = 1.177` | for `t = 4.127` (n = 5,000) |
|---|---|---|
| 50 | 0.166 | 0.584 |
| 100 | 0.118 | 0.413 |
| 200 | 0.083 | 0.292 |
| 400 | 0.059 | 0.206 |
| 800 | 0.042 | 0.146 |

So a single pre-registered hypothesis taking 400 trades needs **µ/σ = 0.059** — with a
typical σ near 1.0R, that is expectancy **+0.06R net**. An ordinary number. Whereas a
5,000-variant search needs **+0.21R net sustained over 400 trades**, which is not.

**The bound is therefore not "impossible" — it is "one pre-registered hypothesis, at
high trade count, or nothing."** Stated as an annualised Sharpe the bound looks like a
wall; stated per trade it is a specific, checkable requirement, and it is the second
form that a scalp deliverable has to be measured against.

## The per-cell part of the bound: 30m cannot get to the trade count

Trade count is capped by bars, because `max_concurrent_per_strategy = 1`
`[repo-verified: engine.py:231]` — one position at a time, so
`N_max ≈ tradeable_bars / (hold + 1)`.

| cell | tradeable bars (excl. 16:00–18:00) | N_max @4-bar hold | @8-bar hold | @16-bar hold |
|---|---|---|---|---|
| MGC/MCL 5m | ~10,720 | ~2,144 | ~1,191 | ~631 |
| MGC/MCL 15m | ~3,579 | ~716 | ~398 | ~211 |
| MGC/MCL 30m | ~1,790 | ~358 | ~199 | ~105 |

Cross-referencing the table above: at 30m with an 8-bar hold the ceiling is ~199 trades,
needing **µ/σ ≥ 0.083** for `t = 1.177` and **0.292** for a 5,000-variant search. At 5m
with an 8-bar hold the ceiling is ~1,191 trades, needing **µ/σ ≥ 0.034** and **0.120**.

**So the three timeframes do not share one power bound, and the finer one is the
stronger.** This inverts the intuition behind BRIEF rule 7: 5m is the *best*-powered of
my three cells on trade count and the *worst* on cost (burst 02). Those two pull in
opposite directions and neither is settled by assertion.

## What a top-10 can mean at this bound

A ranked list of ten rows drawn from a population of *n* carries the deflation penalty of
*n*, not of 10. At n = 1,000 the threshold is 3.717, needing µ/σ = 0.186 over 400 trades —
net expectancy about **+0.19R per trade sustained for 400 trades on 41 sessions.** Nothing
in this repository has ever produced that. So the honest statement, recorded before
measuring anything:

> **A top-10 list from this cell describes the sample. It cannot forecast, and its
> in-sample rank order is expected to be uninformative out of sample** — the programme's
> own prior is Jaccard 0.081 name overlap across disjoint thirds and last-period's
> top 10 returning −0.0155R against a −0.0104R null.

Pre-registered, before any backtest was run in this cell.
