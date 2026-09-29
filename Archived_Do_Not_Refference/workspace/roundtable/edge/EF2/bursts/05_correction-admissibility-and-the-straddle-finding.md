# EF2 / Burst 05 — CORRECTION to my own Burst 01 §2c, and the clean form of the 240m finding

I cross-checked my `entry_admissible` against EF6's `window.signal_mask` because EF6 owns the control
surface and a disagreement between us would silently split the programme's two halves. There is one,
it is **482 bars on MGC and 468 on MCL**, and **EF6 is right.** Correcting in place.

## The disagreement

```
MGC 60m: EF6 signal-legal 10,801/11,297 (95.61%)   EF2 (old) 10,319   agree 10,815/11,297
MCL 60m: EF6 signal-legal 10,459/10,934 (95.66%)   EF2 (old)  9,993   agree 10,466/10,934
first disagreements: 2024-10-07T16:00-04:00, 2024-10-08T16:00, 2024-10-09T16:00, ... (all 16:00 stamps)
```
`[measured: python3, EF6/code/window.signal_mask vs EF2/code/census.entry_admissible, archive 60m]`

**Every disagreement is a bar stamped 16:00 ET.** My test computed the signal bar's own end on a
*contiguous* grid: 16:00 + 60m = 17:00, which is inside `[16:00, 18:00)`, so I called it inadmissible.
EF6's test asks what the **next bar in the series actually is** — and the 17:00 bar mostly does not
exist (6 of 11,297 on MGC), so the fill lands at the **18:00** open, which is legal.

**EF6's convention is the engine-faithful one** and mine was an idealisation: `run_many` fills pending
entries at the open of the next bar it iterates `[repo-verified: engine.py:295-300]`, not at a
hypothetical grid position. A signal read off a 16:00–17:00 bar and filled at 18:00 breaks nothing —
the position never exists inside the forbidden window. The rule constrains position existence, not
what a strategy is allowed to look at.

## What this changes, and what it does not

**It does NOT change any VOID verdict, the population, or the headline `rth_only` finding.** The
census scores "usable fires" against `RTH ∩ swing-admissible`, and the 16:00-stamped bar is **not
RTH** on either contract (MGC RTH closes 13:30, MCL 14:30). So the intersection is unchanged at
**2,477 (MGC) / 2,881 (MCL)**, every VOID verdict stands, the 5,092 / 5,584 population stands, and
`RTH ∩ swing == RTH` exactly still holds. Verified by construction rather than asserted: the
corrected mask differs from mine only on non-RTH bars.

**It does change Burst 01 §2c**, which conflated two different quantities into one percentage.

## The corrected arithmetic — and it is two questions, not one

EF6's vocabulary makes the distinction I was missing. `bar_status` returns `IN`, `OUT` or `STRADDLE`;
`window_mask` asks *may a position exist on this bar*; `signal_mask` asks *may a signal on this bar
produce a legal entry* (which is a question about bar `i+1`). They are near-disjoint sets:

| symbol | tf | bars | **position-illegal** (`OUT`/`STRADDLE`) | **signal-inadmissible** | union |
|---|---|---|---|---|---|
| MGC | 60m | 11,297 | 495 = **4.4%** (stamps 16:00, 17:00) | 496 = **4.4%** (stamps 15:00 ×489, 16:00 ×7) | ~8.8% |
| MCL | 60m | 10,934 | 474 = **4.3%** | 475 = **4.3%** | ~8.7% |
| MGC | 240m | 3,052 | **586 = 19.2%**, all `STRADDLE` | 586 = 19.2% (stamps 12:00 ×494, 16:00 ×90, 20:00 ×2) | ~35% |
| MCL | 240m | 2,990 | **563 = 18.8%**, all `STRADDLE` | 563 = 18.8% | ~35% |

`[measured: EF6/code/window.{bar_status,window_mask,signal_mask} over archive 60m and its 240m resample]`

So Burst 01's "35.5% of MGC 240m bars are inadmissible as signal bars" was **the union of the two
sets, mislabelled as one of them.** The union is right (~35%); the label was wrong. The 60m figure
(8.7%) was the same union and is also ~8.8%, so that line was right by accident.

## The clean form of the finding, which is stronger than what I first wrote

> **At 240m, 586 MGC bars and 563 MCL bars — 19.2% and 18.8% — are `STRADDLE`: they contain 16:00 or
> 18:00 strictly inside them. At 60m there are ZERO `STRADDLE` bars on either symbol.**

A `STRADDLE` bar is, in EF6's words, "a defect report, not a third trading state": the rule cannot be
applied to it without either breaking the rule or discarding a legal part of the bar, and nothing in
EF6 trades one. EF1's harness goes further and **refuses** a grid with `INTERIOR` bars outright —
`SessionGridError` `[repo-verified: EF1/code/session_window.py _audit_grid]`.

**Therefore a 240m-*base* series is not a valid substrate for this programme's rule on a fifth of its
bars, while a 240m *thesis* on a 60m base is entirely valid.** That is an independent and much better
justification for the substrate choice I made in Burst 01 for span reasons, and it is the specific
thing the three of us would have disagreed about silently if I had loaded `MGC_240m.jsonl` as a base.
My 60m base has zero `INTERIOR`/`STRADDLE` bars, so it passes EF1's `_audit_grid` and agrees with
EF6's masks.

**Downstream:** `EF2/code/census.py`'s `entry_admissible` is superseded by
`EF6/code/window.signal_mask` and `measure.py` will import EF6's. The census's
`bars_swing_admissible` column (10,319 / 9,993) is an EF2-internal, stricter mask and should be read
as such; `bars_rth_and_swing` — the column every VOID verdict depends on — is identical under both
conventions. `EF2/code/stopfidelity.py` scored 10,319 / 9,993 bars under the strict mask; the collapse
figures it reports are per-bar **rates**, and re-scoring on the 4.4% of bars the strict mask excluded
(all non-RTH 16:00 stamps) cannot move a rate measured on ~20,000 direction-evaluations by anything
material. Not re-run; the denominator is stated.

## Two things I am taking from EF6 rather than building

Read `EF6/bursts/03_placebo-under-the-window.md` after writing my own plan, and declaring it per the
independence rule. It changes two of my pre-registered choices, **before any expectancy was measured**:

1. **`placebo_shuffle` is dropped.** EF6 measured that `_schedule_shuffle` permutes *direction labels*,
   so on a one-sided rule set it destroys **nothing** — `shuffle_direction_changed = 0.0000` on MGC 60m
   MEAN_REVERSION bases with long share 0.000, and the best case at long share 0.5 destroys only half
   of one channel. A control that is 50–100% identical to its treatment is expected to match it. My
   plan had registered it as one of two honest kinds; that was wrong and it is corrected here rather
   than after seeing a number.
2. **EF2 will use `EF6/code/placebo_w.py`**, kinds `placebo_random_legal` and
   `placebo_session_shuffle` — the latter being the **timestamp shuffle the EDGE_BRIEF actually asks
   for**, which `newstrats/placebo.py` does not contain. `placebo_session_shuffle` moves each signal to
   the same time of day on a different 18:00→16:00 cycle, so it preserves the time-of-day profile,
   which matters here because this repo has two settled time-of-day effects (no entries 15:00–16:00,
   z = −4.43; and the opening-range family) that a uniform draw would confound with "the signal
   contributed nothing".
3. **The forward roll is EF6's `forward.roll`, not mine.** EF6's `cycle_boundaries` puts fold edges at
   **18:00 ET** so no holding period is split across the rank/score line, which my equal-index 6-block
   scheme did not guarantee, and `Ledger.measure` does **clone collapse** by default — without which,
   per its own citation, "a top 10 is routinely the top 2 listed ten times". `measure.py` will emit
   EF6's ledger format `{symbol, setting, base_tf, substrate, screened, t0, t1, strategies: {sid:
   {meta, trades: [[entry_ts, exit_ts, dir, r], ...]}}}` instead of computing its own folds.

## One number of EF6's that I need to re-measure on MCL rather than inherit

EF6's Fault 1 (count-matching breaks under the window) was measured on **MGC and MNQ only**. It found
MGC untouched — pool legal share 1.000 under `rth_only=True` — because MGC's RTH close is 13:30 so its
last RTH bar fills at 14:00, legally. **MCL was not measured.** The arithmetic says MCL is also
untouched: RTH 09:00–14:30, so the last RTH 60m bar is stamped 14:00 and fills at 15:00, which is
legal. But that is arithmetic, not a measurement, and the independence rule says MCL is its own
universe. **Open item: run EF6's `probe_placebo` on MCL 60m and 240m before any MCL row carries a
control.** Recorded here so it cannot be forgotten.
