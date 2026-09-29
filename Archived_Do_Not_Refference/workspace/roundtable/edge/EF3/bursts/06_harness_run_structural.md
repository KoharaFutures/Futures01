# EF3 burst 06 — the full-population harness run: structural results only

**No profitability number appears in this file.** EF1's harness never declared validation, so per my
dispatch every expectancy is embargoed. Everything below is a count, a rate or a compliance check.
The expectancies exist on disk in `out/stage1_{MES,MNQ}_gap.json`, which carry the complete trade
ledger (entry index, exit index, net R, gross R, direction, exit reason, MFE, MAE, hold hours,
session, regime, volatility, time bucket) for every trade.

**Command:** `python3 code/ef3_measure.py MES MNQ`. One full-span run per symbol over the live
population, plus a 300-strategy census-falsification run and two 300-strategy true-windowed runs per
symbol. MES full-span run 646 s, MNQ 562 s, at roughly one third of one core.

## Compliance

| | MES | MNQ |
|---|---|---|
| live strategies run | 4,912 | 4,314 |
| trades | 53,252 | 49,939 |
| **violations under EF1's `violations()`, no carve-out** | **0** | **0** |
| max hold | **21.0 h** | **21.0 h** |
| holds > 22 h | **0** | **0** |
| median hold | 2.0 h | 3.0 h |

## Engine counters

| counter | MES | MNQ |
|---|---|---|
| entries vetoed, fill bar in [16:00, 18:00) ET | 9,965 | 12,213 |
| flats on boundary (the 16:00 print) | 20,563 | 23,832 |
| flats forced by EF1 component 1b (ET-date rule) | 617 | 655 |
| **flats forced by EF3's `trading_day` clause** | **63** | **135** |
| flats in window (the hole branch) | 0 | 0 |
| flats re-labelled `STOP` (gapped through) | 4 | 22 |
| stale fills (> 3 base bars after the signal) | 1,038 | 1,523 |
| bars on boundary / in window / interior | 488 / 493 / **0** | 488 / 497 / **0** |

The 63 + 135 = **198 forced flats** are the measured cost of the residual disagreement between my
engine and EF1's: 198 positions that EF1's current rule would carry across a 16:00 deadline on the
nine 23:00-ET holiday-eve bars. On the 400-strategy probe in burst 05 this figure was 0, which is
why a probe is not a population.

## Exit mix — and the confirmation that the time stop is dead

| exit | MES | MNQ |
|---|---|---|
| `STOP` | 23,005 (43.2%) | 18,669 (37.4%) |
| **`SESSION_CLOSE` (the 16:00 flat)** | **21,176 (39.8%)** | **24,465 (49.0%)** |
| `TARGET` | 5,136 (9.6%) | 3,468 (6.9%) |
| `BREAKEVEN` | 3,935 (7.4%) | 3,337 (6.7%) |
| **`TIME`** | **0** | **0** |

**0 of 103,191 trades exited on the time stop**, confirming burst 02's arithmetic: the catalogue's
smallest `time_stop_bars` is 30 *primary* bars against a 22-bar cap at 60m. And the flat is the
largest single exit on MNQ at **49.0%** — which is why adopting EF1's market-order slippage on it
rather than the stock engine's zero-slippage `bar.close` was not a detail.

## The census, falsified rather than assumed

**300 census-removed strategies per symbol, run through the same engine: 0 trades on MES, 0 trades
on MNQ.** Every strategy the burst-02 census removed is genuinely structurally zero-trade.

## The three populations that must not be pooled

| | MES | MNQ |
|---|---|---|
| generated | 6,022 | 5,904 |
| **(a) cannot fire** — removed by census | 1,110 (18.4%) | 1,590 (26.9%) |
| **(b) could fire, took no trade** | 3,224 (53.5%) | 2,713 (45.9%) |
| **(c) traded** | 1,688 (28.0%) | 1,601 (27.1%) |
| (c) with IS n ≥ 30 | 275 | 254 |
| (c) with IS n ≥ 30 and IS expectancy > 0 | **50** | **83** |

(a) and (b) both produce a null and only (b) is evidence. At 60m alone, 1,203 of MNQ's 3,180 live
strategies traded (37.8%); at 240m, 398 of 1,134 (35.1%).

## Window slicing is exact here, and that is the session rule's one gift

| | MES | MNQ |
|---|---|---|
| trades straddling the IS/OOS cut | **17 / 53,252 = 0.032%** | **2 / 49,939 = 0.004%** |
| true-windowed runs checked | 300 | 300 |
| pairs with ≥ 5 trades both ways (IS / OOS) | 41 / 35 | — |
| mean sliced-minus-true expectancy in R | **0.0** | — |
| max abs difference | **0.0** | — |
| mean trade-count difference | **0.0** | — |

Because no position can span more than 22 hours, almost nothing crosses a window boundary. The prior
programme measured 2.47% of trades straddling a period edge and a −0.004R effect from tightening the
rule; here the straddle rate is **77× lower** and the sliced ledger reproduces a true windowed run
**exactly at 5 decimal places on every checked pair**. So every walk-forward fold can be a slice of
the one run already on disk, at no cost in fidelity.

## What was written and deliberately not run

`code/ef3_stage2.py` (placebo cohort), `code/ef3_rank.py` (ranking, controls, walk-forward) and
`code/ef3_audit.py` (sibling parameter sensitivity, cost arms, roll exposure, fill realism) are
complete and import cleanly. They were not run: the programme parked, EF1 never declared its harness
validated, and a row without its placebo is not reportable under my own pre-registered protocol
(burst 04) or the EDGE_BRIEF's first guardrail. Run order and expected cost are in the
`## PARKED` section of `FINDINGS.md`.
