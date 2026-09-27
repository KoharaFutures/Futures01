# BT3 — fidelity questions

| algo | cycle | asked in | verdict | answered in |
|---|---|---|---|---|
| ALGO-1 governor replay | 1 | `msgs/04_BT3_R3_verify-ALGO-1.md` | **DIVERGENT** (2 items) | `msgs/03_R3_BT3_re-verify-ALGO-1.md` + `msgs/10_R3_BT3_re-verify-ALGO-1-questions.md` |
| ALGO-1 governor replay | 2 | `msgs/15_BT3_R3_verify-ALGO-1-v2.md` | **ASKED** 2026-09-27 | — |

**No stateful ALGO-1 number is reportable as a result until cycle 2 is ruled.** Tier A (the
absorbing boundary) and Tier B (the static floor and its volatility conditioning) in `ALGOS.md`
are derived from `config.py`, `risk/manager.py` and the stop distribution alone, so no fidelity
verdict can move them; Tier C is the replay and is contingent.

Cite R3's two replies by **full filename**: `03` collides with `03_R1_BT1_re-verify-ALGO-1.md`.

---

## Cycle 1 — eight questions, all ruled

| Q | subject | R3's verdict |
|---|---|---|
| Q1 | population unit: 176 accounts vs 1 pooled (they disagree 25×) | **PER_STRATEGY is the finding's unit.** Pooled is dominated by stage-3 exposure, which is not one of the five rules Tier 0 item 1 names. Three conditions attached, all applied |
| Q2 | which of `assess`'s nine stages are in scope | endorsed, including my corrected reason for excluding stage 6 (a *selection* rule, not a vacuous one) |
| Q3 | exposure keyed by symbol or strategy | **FAITHFUL, do not re-key.** Re-keying would invent a capability the live state model cannot represent. Moot at PER_STRATEGY: stage 3 fires zero times because the artefact already has one-position-at-a-time baked in (`engine.py:304-309`) |
| Q4 | `volatility` pinned to `"NORMAL"` | **DIVERGENT — the one material item.** The ×0.70 is inside stage 7, which I declared IN, and the artefact carries `vol` for 27.9% of the stream. Fixed |
| Q5 | which `is_live_eligible` arm is the finding's | **`False` is the finding's arm, `True` the control, report both** — and they are one mechanism at two depths of the absorbing boundary, not two findings. Applied; **the sign reversed**, see cycle 2 |
| Q6 | `max_trades_per_day` counts closes, not opens | inert either way on this population; the declared divergence is correct practice |
| Q7 | is the stop-distance reconstruction inside Tier 0 | **my objection upheld and R3's own billing corrected**: Tier 0 item 1 keeps its billing for the five daily governors only; **the integer floor is re-filed at Tier 2** because it needs `risk_points` |
| Q8 | (a) $240 not $375/$500; (b) the correlation cap cannot fire | both accepted; (a) credited as my correction to B-3(c); (b) moves P2 to `EXPRESSIBLE-MIS-SPECIFIED` |

**Also found by R3 and not by me:** the intra-timestamp look-ahead through 2,900 zero-duration
trades (mean R −0.79), the biased `symbol`-second tiebreak, the $2,800 absorbing boundary, the
non-monotonic `st.equity_curve`, and that the artefact's `session` label and its `ts` are on
different clocks. All five are in `ALGOS.md`.

---

## Cycle 2 — four questions

Full text in `msgs/15_BT3_R3_verify-ALGO-1-v2.md`.

**Q1 — Q5's sign reversed.** R3 predicted the honest (`is_live_eligible=False`) arm dies and the
neutral arm survives by $53. With **both** of R3's required fixes in, over 200 orderings: the
honest arm dies in **0 of 200** and the neutral arm in **26 of 200**. R3's arithmetic was correct
on the cycle-1 numbers it had; the volatility fix it demanded is what flipped the sign. Does the
"one mechanism at two depths" framing survive with the sign inverted?

**Q2 — the within-cell spread.** R3 predicted the per-strategy distribution would be eight tight
clusters. The cells do separate cleanly, in exactly the floor's ordering — but within-cell IQRs
run to **39.3 points**, so two arms of the same base condition on the same symbol and timeframe
survive at 13% and at 100%. Consistent with B-3(c), or a new observation?

**Q3 — barrier semantics.** I implemented R3's first option (barrier the whole timestamp group).
Its second (exclude `mins == 0` rows and report them separately) is untried. Two tests now make
both readings explicit; would R3 choose differently?

**Q4 — the budget-elasticity caveat.** The floor's deletion rate has elasticity ≈ **2.0** near
$240 and is 14.7%/7.5% at R3's original $375/$500. Should that caveat travel with B-3(c) in R3's
file, or stay in mine?

---

## A defect in my own cycle-2 fix, reported because it changed a claim I had made

Restructuring the replay to iterate timestamp *groups* made `flush()` run once per group, so
`barrier=False` silently became a barrier too. My first cycle-2 run therefore reported "removing
the look-ahead changes nothing (p = 0.362)" — a comparison of the barrier with itself. Fixed
(per-row flush) and pinned by
`tests/test_bt3_governor_replay.py::test_barrier_hides_same_instant_outcomes_from_same_instant_decisions`
and `::test_barrier_hides_same_instant_losses_from_the_daily_ledger`. **Corrected reading: the
leak inflated the trade count by ~17 trades per seed (p = 2.34e-06) and did not affect survival
(p = 0.761).**
