# EF1 burst 02 — the known-answer tests, and the two defects they found in EF1's own first cut

`tests/test_ef1_session_window.py`, 51 checks, all passing. Full repo suite: **878 passed**
`[measured: python -m pytest -q tests → 878 passed in 102.49s]`.

The tests are written to *reject*. Every one of them fails if the rule is switched off, and four
of them assert the harness catches something rather than that it lets something through.

## The two defects the tests found in my own code, before any number was reported

### EF1-D1 — a daily bar classified as `OUTSIDE`, so 1440m would have run with no flat at all

The first cut of `classify_bar` compared `start + minutes` against 960 (16:00 in ET minutes):

```python
if FLAT_ET_MINUTE <= start < REOPEN_ET_MINUTE: return IN_WINDOW
if start < FLAT_ET_MINUTE < end:               return INTERIOR
if start < FLAT_ET_MINUTE and end == FLAT_ET_MINUTE: return ON_BOUNDARY
return OUTSIDE
```

A daily bar is stamped **18:00 ET** (`align_bucket`, `futures_agents/data/bars.py:139-143`), so
`start` = 1080 — neither below 960 nor inside `[960, 1080)`. It fell through to `OUTSIDE`. **Every
1440m strategy would have run with no flat whatsoever while the harness reported success**, which
is precisely the silent-null shape this repo has catalogued five times (D38, D42, D44, D48,
`BarSeries.append`).

Fix: the deadline a bar is tested against is the **next** 16:00 after its own start, which for a
bar opening at or after 18:00 is tomorrow's (`960 + 1440`). Regression:
`test_daily_bar_is_interior_not_outside`.

It also makes a nice check fall out for free: a bar stamped 18:00 with `minutes=1320` — one whole
18:00→16:00 cycle — classifies `ON_BOUNDARY`, which is the rule describing itself.

### EF1-D2 — staleness measured in bar indices reported zero on the only case it exists for

`stale_fills` counts entries filling long after their signal bar, which the letter of the rule
permits across the Friday-17:00-to-Sunday-18:00 break. The first cut compared
`i - sig.bar_index`. A Friday-16:00 signal filling at Sunday 18:00 is **one index apart and fifty
hours apart**, so the counter read 0 on exactly the case it was built for. Now measured in
wall-clock ET minutes. Regression: `test_a_stale_fill_across_the_break_is_counted_not_hidden`.

## The `Trade.exit_ts` ambiguity, and why the carve-out is keyed on the engine and not the trade

`Trade.exit_ts` is `bar.ts`, the bar's **open** time (`engine.py:505`), and the `Trade` says
nothing about *where in the bar* the fill happened. That matters at exactly one point:

- a flat filled at the **open** of the 16:00 bar (the gap branch) is stamped `16:00` and is
  **compliant** — the position ceased to exist at the deadline instant;
- a trade that merely *ended up* on that bar — a target hit at 16:40, say — is stamped `16:00`
  too and is a **genuine violation**.

They are indistinguishable from the `Trade` alone. So `violations()` defaults to **no carve-out**
(strict, usable on any engine's trades) and the exemption must be supplied as
`flat_exits=flat_exit_keys(engine)` — the engine's own record of the fills it made at a bar's open.
`flat_exit_keys` covers only `IN_WINDOW` fills; `ON_BOUNDARY` flats are stamped 15:00 and need no
exemption. `test_the_flat_exemption_cannot_launder_a_violation` shows the `SPANS_WINDOW` test is
independent and fires anyway, so exempting the exit stamp cannot hide a position that was
demonstrably alive across the deadline.

## What the tests pin down

| check | asserts |
|---|---|
| `test_classify_bar_known_answers` (16 cases) | the clock rule, incl. 240m/480m/1320m boundaries |
| `test_position_is_flat_at_1600_and_the_fill_is_the_1600_print` | closes, at the tick |
| `test_without_the_rule_the_same_position_runs_on_past_1600` | the **control** — same bars, vanilla engine, `SPANS_WINDOW` |
| `test_mgc_is_not_flattened_at_its_own_1330_rth_close` | the reason the rule exists; also runs the shipped engine and shows it out at **13:00** |
| `test_entry_whose_fill_lands_in_the_window_is_vetoed_and_counted` | vetoes, and `signals_generated` still 1 |
| `test_a_signal_inside_the_window_may_fill_at_the_1800_reopen` | the letter of the rule, plus the strict flag |
| `test_flat_pays_market_order_slippage_not_zero` | D13/R3 not inherited; long fills below the print |
| `test_hole_at_the_deadline_fills_at_the_next_open_gap_and_all` | the MCL 2026-03-06 shape |
| `test_gap_through_the_stop_at_the_flat_is_a_stop_not_a_flat` | reason STOP, fill at the open, **not slipped twice** |
| `test_stop_inside_the_flat_bar_wins_over_the_flat` | pessimism preserved |
| `test_stop_beats_target_in_the_flat_bar` | invariant 4 preserved |
| `test_daily_grid_is_refused_...` / `test_a_grid_the_rule_can_never_fire_on_is_refused` | it refuses |
| `test_violations_detects_each_way_of_breaking_the_window` (4) | the detector catches all three kinds |
| `test_the_clock_rule_is_prefix_invariant_for_every_k` | look-ahead, every prefix |
| `test_the_engine_produces_a_prefix_of_its_own_trades_on_every_prefix` | the BT1 form, engine-level |
| `test_the_engine_hooks_are_still_reachable` | the coupling guard |
| `test_d48_naive_replace_collides_and_with_exit_does_not` | D48 reproduced, then fixed |
| `test_flat_tracks_et_wall_clock_across_the_dst_boundary` | −04:00 and −05:00 classify the same |
| `test_two_identical_runs_give_identical_trades` | determinism |

The D48 fixture uses `ema_fast_above_slow`. `trend` is the group R4 audited CLEAN 8/8 with R1
agreeing independently, so the fixture cannot be confounded by a second defect; and deliberately
**not** `macd_directional`/`macd_hist_direction`, which R4 measured identical on 5000/5000 bars.
