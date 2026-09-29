# EF4 burst 05 — the population, declared with its exact size before measurement

`code/population.py` → `out/population_size.json`. Run and recorded **before** any
backtest in this cell. `[measured: python3 code/population.py]`

## Two tracks, deliberately different widths

| track | what it is | n | `free_t = √(2 ln n)` | annualised Sharpe that t needs on 0.1585 y |
|---|---|---|---|---|
| **A** | 6 named, pre-registered hypotheses × 2 symbols × 3 timeframes, one fixed exit | **36** | **2.677** | 6.73 |
| **B** | the census-gated broad screen: singles + distinct-group pairs × (no filter ∪ 6 declared filters), one fixed exit | **19,152** | **4.441** | 11.16 |
| combined | | 19,188 | 4.441 | 11.16 |

Per cell: MGC 5m 3,010 · MGC 15m 3,374 · MGC 30m 3,591 · MCL 5m 3,003 · MCL 15m 2,800 ·
MCL 30m 3,374 (Track B); 6 each (Track A).

**The two tracks exist because the difference between them *is* a result.** On this span the
only lever available is *n*, and `free_t` is logarithmic, so the entire distance between a
36-arm pre-registration and a 19,152-arm screen is **1.76 t-units** — worth an annualised
Sharpe of 4.4. Track A can in principle be cleared; Track B cannot. Declaring both, and
declaring which rows come from which, is the difference between a reportable result and a
ranked list.

## What was excluded, and why, before looking

1. **Census gate, per (symbol, timeframe).** LIVE or THIN only. VOID and NEAR_VOID removed
   in the cell where they are VOID or NEAR_VOID, never globally — `openinterest` (0/N in
   8 of 8 cells), `mtf_aligned`/`mtf_strongly_aligned` (0/N in every single-tf cell),
   `lvn_rejection` on MCL, `zone_touch`/`fresh_zone_approach` at 30m, `post_news_window`
   on MGC 15m/30m.
2. **Rate band: signals 2–60%, filters 2–90%.** Removes the always-on degenerates found in
   burst 04 — `mtf_not_conflicted` (100.00%), `outside_news_blackout` and
   `no_imminent_release` (99.1–99.6%). A filter that passes on 99% of bars is counted by
   the combinator as a filter and is not one.
3. **Duplicate halves dropped:** `macd_hist_direction`, `regime_matches_direction`
   (Jaccard 1.0 with their twins in all six cells).
4. **Two signals and one filter is the ceiling** (BRIEF rule 1). Singles and
   distinct-group pairs only.
5. **Exits are not searched.** One geometry for every arm in both tracks. The repo's own
   catalogue offers 11; sweeping them would multiply *n* by 11, cost 1.2 t-units, and buy a
   dimension BRIEF rule 3 says does not move expectancy. This is the cheapest
   anti-overfitting decision available in this cell and it was taken before measuring.

Result: eligible signals per cell 29–33 of 53, filters 6 of 26 by declaration.

## The fixed exit, with its reasons

`ExitModel(ATR, 1.0, targets_r=(1.5,), scale_out=(1.0,), breakeven_at_r=None,
time_stop_bars=24, exit_at_session_close=False)`

- **ATR 1.0 and not tighter.** Burst 02: 0.5 ATR at 5m is *below* `min_stop_ticks` on both
  contracts, and `stop_price` silently widens it to the floor
  `[repo-verified: base.py:313-314]` — so a "0.5 ATR" arm at 5m would not be testing
  0.5 ATR. At 1.0 ATR the floor does not bind (47.5 ticks MGC 5m, 20.4 MCL 5m).
- **One target, full size, no scale-out, no breakeven move.** Net R per trade is then one
  unambiguous number, so the R series' *t* means what it says. Scale-outs make `net_r` a
  weighted average of legs, which shrinks variance without adding edge and inflates *t*.
- **`time_stop_bars=24` in the strategy's own bars** `[repo-verified: engine.py:404-406]` =
  2 h at 5m, 6 h at 15m, 12 h at 30m — live at all three, inside the 22-hour maximum hold.
- **`exit_at_session_close=False`**, because the engine's session exit is the wrong clock
  (13:30 MGC / 14:30 MCL) and the harness's 16:00 ET flat is the rule.

## Two settings that are forced by the session rule and would otherwise silently gut the cell

- **`rth_only=False` on every arm.** The default is `True` `[repo-verified: base.py:393]`
  and would veto every bar outside 08:20–13:30 (MGC) / 09:00–14:30 (MCL) — **76–78% of the
  cell's bars** (burst 02), i.e. the entire overnight regime this programme exists to
  measure. D24 measured `rth_only=False` as buying sample and costing expectancy, but it
  measured that under the old regime where the position was flattened at the contract's RTH
  close, so **D24 does not transfer to this rule and is not assumed here.**
- **`allow_overnight=True`**, forced by the harness, so the shipped 13:30/14:30 exit is
  inert and the 16:00 flat is the only session exit.

## D48 guard

Every `Strategy` is constructed with `_id=None` and every `dataclasses.replace` in
`code/placebo.py` passes `_id=None`. `population.assert_unique` raises on any duplicate
`strategy_id` at emission, per cell and per track. It passed on all 12
(cell × track) emissions. Without it, two arms collide into one `BacktestResult` and the
measured difference between them is exactly zero — indistinguishable from this programme's
own finding that operating axes do not move expectancy.

## Harness

EF1's `SessionWindowEngine` (`edge/EF1/code/session_window.py`) is primary. EF4's
`code/session_clock.py` is an independent second implementation of the same rule, kept for a
differential check. **Until EF1 declares validation, no profitability number below is a
programme result.** EF1's own burst 01 and my burst 01 agree on the substrate geometry
independently — 41 bars ending exactly at 16:00 ET per symbol at 5/15/30, 0 bars containing
16:00 strictly inside them, 493–495 bars inside the prohibition at 5m — which is the first
cross-check between us and it passed.
