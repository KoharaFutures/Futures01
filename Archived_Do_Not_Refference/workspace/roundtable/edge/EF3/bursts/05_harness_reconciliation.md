# EF3 burst 05 — reconciling with EF1's harness, and the one defect I found in it

## What I did and why

I built my own 18:00→16:00 rule rather than wait, then ran **both** engines over the **same 400
live MES 60m all-hours strategies on the same `SymbolFrame`** and audited both with EF1's own
`violations()`. That is the only way two independent implementations of a clock rule can be
compared: not by reading each other's code, but by counting the trades where they disagree.

## Round 1 — EF1's first build under-enforced on 19 of 507 sessions

| engine | trades | `violations()` | max hold | holds > 22 h |
|---|---|---|---|---|
| `SessionWindowEngine` (EF1, first build) | 3,717 | **43 `SPANS_WINDOW`** | **71.0 h** | **19** |
| `SessionEngine` (EF3) | 3,734 | **0** (strict, no carve-out) | 21.0 h | 0 |

Cause: `classify_bar` is a pure function of one bar, so a session whose last bar is `OUTSIDE` has
no bar for the flat to fire on. Worst case: `MES-60m-044e20ad3af2`, entry 2024-12-24 11:30, exit
2024-12-26 15:00 — **71 hours across two 16:00 deadlines**, the multi-day thesis the EDGE_BRIEF
rules out by arithmetic. Reported as `msgs/EF3-01_EF1_session-rule-misses-early-close-sessions.md`
with the 19 dates.

## Round 2 — EF1 fixed it independently, and our engines now agree trade-for-trade

EF1 added `session_end_indices` (component 1b): group bars by **ET calendar date**, and if no bar
on that date is `ON_BOUNDARY` or `IN_WINDOW`, force the flat on that date's last pre-16:00 bar.

`[measured: same 400 strategies, same frame, EF1 current build vs EF3 →
both 3,734 trades, both 0 violations, both max hold 21.0 h, both 0 holds > 22 h]`

**So the two independent implementations now produce identical trade counts and identical
compliance.** I have rebuilt `SessionEngine` as a **subclass of `SessionWindowEngine`** adding one
clause, so every fill convention, counter and audit is EF1's and the delta between us is one flag
(`enforce_session_gap`). `enforce_session_gap=False` reproduces EF1 exactly.

## The residual difference, and it does not bite on this substrate

EF1 groups by ET **calendar date**; I group by CME **`trading_day`** (18:00 rolls forward). They
partition the same bars differently, and mine catches 9 bars EF1's does not:

| | MES | MNQ |
|---|---|---|
| EF1 `session_end_indices` | 10 | 10 |
| EF3 additional forced-flat bars | **9** | **9** |
| union | 19 | 19 |

The 9 are all `23:00 ET` on a holiday eve — 2024-11-27, 2025-01-19, 2025-02-16, 2025-11-26,
2026-01-18, 2026-02-15, 2026-04-02, 2026-06-18, 2026-07-02 — sessions where the archive's
pre-holiday overnight ends at midnight ET and does not resume until the next evening. EF1's rule
misses them because those bars sit on an ET date whose *earlier* bars already supplied a
forced-flat index, or on a date the market never reopened.

**On the 400-strategy probe none of the 9 bit** — trade counts are identical — because no strategy
happened to hold a position at 23:00 on any of those nine dates. The full-population run reports
`forced_flats` so this is a measured number, not an assumption. I keep the clause because it costs
nothing and closes the hole; I do **not** claim it changed a result.

## What I adopted from EF1 wholesale

1. The `IN_WINDOW` fill at `bar.open` rather than `bar.close`, and the refusal to let a
   post-deadline bar's high/low move the stop check or the excursions.
2. Re-labelling a flat that gapped through the stop as `ExitReason.STOP` — the stop was breached
   first in time. Measured on the probe: 1 such trade in 3,734.
3. Market-order slippage on the flat. The stock engine fills `SESSION_CLOSE` at `bar.close` with
   **zero** slippage `[repo-verified: engine.py:467,473,476]`, and the flat fires on 38.6% of
   trades in this cell, so inheriting that would have understated the cost of the programme's
   defining rule on four exits in ten.
4. `assert_hooks_reachable()` — passes on the current `engine.py`.

## Two facts about my cell that follow from the rule, and both remove a dimension

**`time_stop_bars` is inert.** Measured on the probe: `TIME` exits = **0 of 3,734**. The catalogue's
smallest value is 30 *primary* bars = 30 h at 60m, 120 h at 240m, against a 22-hour cap. Every
catalogue variation in time-stop length is measuring nothing here.

**`rth_only=True` caps the hold at 6.5 hours and so forbids the regime.** `StrategyFilters.rth_only`
defaults to **True** `[repo-verified: base.py:393]` and is `True` in both MES's and MNQ's research
profile `[repo-verified: profiles.py]`. It gates entries, not holding, so with it on the only legal
entries are 09:30–16:00 and the position must be flat at 16:00 the same day. **The 22-hour
18:00→16:00 window this programme exists to measure is unreachable with `rth_only=True`.** Both
arms are in my population and the pair is the central comparison of the swing cell. (EF2 reached
the same conclusion independently — `msgs/EF2-01_EF1_rth-only-makes-the-overnight-switch-inert.md`
— which for once *is* corroboration, because EF2 is on different symbols and the claim is about the
code, not the tape.)

## The 240m grid, and why my 240m cell runs on a 60m base

`align_bucket` anchors 4-hour buckets to ET midnight, so the bucket labelled **16:00 spans
16:00→20:00** and straddles both the flat and the reopen: 585 of 3,050 = **19.2%** of 240m bars.
EF1 records the cost of a 240m *base*: its veto "blocks a Sunday-18:00 entry whose bucket is
stamped 16:00", 91–96 times per symbol. **My 240m cell has a 60m base and a resampled 240m frame,
so it pays none of that** — and the resample is bit-identical to the vendor's own 240m series
(3,050/3,050 closes, max |Δ| 0.000e+00, burst 01). Any 240m result measured on a 240m base and any
measured on a 60m base are **different experiments** and must not be pooled.
