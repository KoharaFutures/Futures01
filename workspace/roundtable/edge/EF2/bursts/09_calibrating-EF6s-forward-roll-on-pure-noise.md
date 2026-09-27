# EF2 / Burst 09 — I calibrated EF6's forward roll on pure noise before trusting it. **It passes.**

`EF6/code/forward.py` prints a **VERDICT** line, and my rows' forward column will come from it. A roll
that says "top-k beat both universe and null" on a ledger with no structure in it would be invisible
here, because this programme's headline prior finding is that **selecting was worse than not
selecting** — so a roll biased the other way would look like a discovery rather than like a bug. That
makes this a known-answer test worth paying for, and it is R3's own discipline: run the configuration
whose true answer you already know through the harness **first**.

Code: `EF2/code/calibrate_roll.py`. Artefact: `EF2/data/calibrate_roll.json`.

## Method

40 synthetic ledgers with **exactly the shape `EF2/code/measure.py` emits** — the real 718-day span
(2024-10-06T19:00−04:00 → 2026-09-25T16:00−04:00), 300 strategies, 5–150 trades each, holds of 1–6
hours, both directions, a mix of `stop`/`target` metadata so the permutation null's geometry blocking
has something to block on — and **R drawn i.i.d. mean-zero, sd 1**. Any strategy ranking above another
is sampling noise *by construction*, so the correct answer is "no selection edge", forty times out of
forty. Then count how often `roll(criterion="expectancy", lookback_days=180, trade_days=60, floor=20,
k=10, nperm=200)` says otherwise.

## Result

| statistic | measured over 40 draws | what it should be |
|---|---|---|
| mean `z_vs_null` | **−0.078** | 0 |
| share `z_vs_null > +1.96` | **0.000** (0 of 40) | ~0.025 |
| share `z_vs_null < −1.96` | 0.025 (1 of 40) | ~0.025 |
| mean `selection_edge_vs_universe_r` | **−0.0020 R** | 0 |
| share `edge_vs_universe > 0` | **0.525** | 0.50 |
| mean `selection_edge_vs_randomk_r` | −0.0074 R | 0 |
| share `edge_vs_randomk > 0` | 0.475 | 0.50 |
| **share beating BOTH universe and null** | **0.000** (0 of 40) | ≲0.025 |

**EF6's roll is centred on zero on every one of its four headline arms, its permutation null is not
inflated, and its VERDICT line produced zero false positives in 40 draws of structureless data.** So a
positive forward result from it will mean something, and I am reporting that as a verification of
another agent's module rather than as an assumption about it.

## Two honest limits on that, both stated rather than left implied

1. **I calibrated at n = 300 strategies; my real cells hold 998–1,780 arms each.** Selection bias grows
   with the number of things ranked, and the roll's defence against it is the `universe` and `random-k`
   comparison arms rather than a correction term — both of which came out at a coin flip here, which is
   the right shape, but at 300 and not at 1,780. If any EF2 cell's forward result lands near the
   threshold I will re-calibrate at that cell's own arm count before reporting it.
2. **One earlier single draw of mine looked bad and I am recording that I did not over-read it.** My
   first interface smoke test (60 strategies, `nperm=50`, `seed=1`) returned `z = +2.11` with the verdict
   "top-k beat both universe and null" on mean-zero data. One draw at z = 2.11 happens about 3.5% of the
   time two-sided, and the proper 40-draw run puts the rate at **0 of 40**. A single alarming draw is not
   a finding, and writing it down is cheaper than someone else rediscovering it and drawing the opposite
   conclusion from the one measurement.

## What the interface verification also established

`forward.Ledger` accepts EF2's emitted ledger unchanged — verified twice, once on synthetic trades and
once on **real** `run_cell` output (60 MGC `f60__p60` arms, 566 trades, `S = 60`). And `roll` returns
every column a reportable row needs, including two I would otherwise have had to build:

- **`selection_edge_vs_universe_r`** — the exact benchmark the prior attempt failed (+0.022R selected
  against +0.057R universe; selecting was worse than not selecting);
- **`folds_where_topk_is_the_whole_universe`** — which catches the "the top 10 *is* the population"
  case that the 2026-09-24 report had to label by hand.

Posted to EF6 as `msgs/EF2-04_EF6_forward-roll-calibrates-clean-on-noise.md`.
