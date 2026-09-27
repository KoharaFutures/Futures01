# R3-D2 — The operating-vocabulary matrix

**Track R3, DIVISION §3 (R3-D2).** One row per operating axis a real futures operator uses.
Anchored on `futures_agents/strategies/base.py` — `TargetKind` (:165), `StopKind` (:187),
`ExitModel` (:195), `StrategyFilters` (:380) — the exit catalogue at
`futures_agents/strategies/combinator.py:43-128`, the position lifecycle at
`futures_agents/backtest/engine.py:158-188, 331-517`, the cost model at
`futures_agents/backtest/costs.py`, and the live risk layer at
`futures_agents/risk/manager.py` + `futures_agents/config.py:340-410`.

**Verdict vocabulary** (DIVISION §3 R3-D2 plus §4):

| verdict | meaning |
|---|---|
| `EXPRESSIBLE-VARIED` | a handle exists **and** at least one completed study varied it |
| `EXPRESSIBLE-NEVER-VARIED` | the handle exists and is pinned to one value in every generated strategy |
| `EXPRESSIBLE-CONFOUNDED` | the handle is varied but only jointly with another, so its effect is unidentifiable |
| `PARTIAL` | a degraded or reconstructible version exists; the loss is stated |
| `INEXPRESSIBLE-ARCH` | the data exists, the code cannot carry it; **the one missing primitive is named** |
| `DEAD-HANDLE` | a parameter or field exists, is settable, and is never read — worse than absent |

**Authoritative field lists**
`[measured: python3 -c "import dataclasses; from futures_agents.strategies.base import
ExitModel, StrategyFilters; print([f.name for f in dataclasses.fields(ExitModel)]);
print([f.name for f in dataclasses.fields(StrategyFilters)])"
→ ExitModel: stop_kind, stop_mult, target_kind, anchor_mult, min_reward_risk,
stop_pad_ticks, targets_r, scale_out, breakeven_at_r, trail_atr_mult, time_stop_bars,
exit_at_session_close (12 fields)
→ StrategyFilters: sessions, regimes, volatility, days_of_week, rth_only,
min_minutes_since_open, max_minutes_since_open, require_alignment (8 fields)]`

**Total axes catalogued: 62.** Split at the foot of this file.

---

## 1. Entry execution (6 axes)

| # | axis | what operators do `[general knowledge]` | library handle | verdict | evidence |
|---|---|---|---|---|---|
| E1 | Order type at entry | market, marketable limit, resting limit, buy-stop, stop-limit, MIT — chosen per setup; a breakout is a stop order, a pullback is a resting limit | none. There is no order-type object anywhere. The entry is *implicitly* a marketable limit: `SlippageModel.base_ticks = 0.5  # marketable limit into a normal book` | `INEXPRESSIBLE-ARCH` | `[repo-verified: futures_agents/backtest/costs.py:29]`; `[measured: grep -rn "OrderType\|order_type" --include=*.py futures_agents/ → no match]`. **Missing primitive: an `OrderKind` enum on `StrategySignal` and a branch in `_open_position` that fills a resting limit only if the bar traded through it.** Today `_open_position` unconditionally fills at `bar.open + sign*slip` `[repo-verified: engine.py:344-355]` |
| E2 | Entry timing relative to signal | at the close, at the next open, on a pullback to a level, on a retest after a break | fixed: next bar's open | `EXPRESSIBLE-NEVER-VARIED` | `[repo-verified: costs.py:54-61 `entry_on_next_open: bool = True`; engine.py:290-295]`. The flag is settable and **no caller ever sets it False** `[measured: grep -rn "entry_on_next_open" --include=*.py . → costs.py:61 definition only]` — and nothing reads it either, so it is also a `DEAD-HANDLE`: `engine.py:290-295` fills at next open unconditionally without consulting it |
| E3 | Partial fills | a 50-lot fills in pieces; a micro rarely does | none; every fill is complete | `INEXPRESSIBLE-ARCH` | `[measured: grep -rn "partial_fill" --include=*.py . → no match]`. **Missing primitive: `_OpenPosition.remaining` tracks *scale-out*, not fill completion; there is no `filled_fraction` distinct from `remaining` `[repo-verified: engine.py:170]`** |
| E4 | Slippage budget / max chase | "if I cannot get it within 2 ticks I do not want it" | none. Slippage is charged, never used as a veto | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:353-355 — slip is added to the fill price; there is no comparison against a budget]`. **Missing primitive: `FillModel.max_slippage_ticks` plus a `return None` branch in `_open_position`** |
| E5 | Cancel-if-unfilled-within-N-bars | working orders expire | `pending` is always drained on the very next bar | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:290-295 — the pending dict is unconditionally emptied]`. **Missing primitive: a `bars_pending` counter on the `pending` tuple.** Note the flip side: the current behaviour makes stale signals impossible, which is conservative |
| E6 | Cost-aware skip | "cost is 20% of my R on this one — pass" | `CostModel.cost_in_r` exists and computes exactly this number; nothing calls it as a gate | `DEAD-HANDLE` | `[repo-verified: costs.py:112-122]`; `[measured: grep -rn "cost_in_r(" --include=*.py . → costs.py:112 definition; robustness.py passes a precomputed `cost_r` for *reporting*, never as a veto]`. **This is a one-line gate in `Strategy.evaluate` and would be a genuine Channel-3 operating rule** |

## 2. Initial risk placement (7 axes)

| # | axis | what operators do | library handle | verdict | evidence |
|---|---|---|---|---|---|
| R1 | Stop basis | volatility (ATR), structure (beyond the swing), fixed ticks, band, range, % of price, fixed dollar | `StopKind` = {ATR, STRUCTURE, FIXED_TICKS, VWAP_BAND, RANGE} | `EXPRESSIBLE-VARIED` | `[repo-verified: base.py:187-192]`. 4 of the 5 appear in the catalogue `[measured: 11 exit models → {ATR, STRUCTURE, VWAP_BAND, RANGE}; FIXED_TICKS never used]` |
| R2 | `FIXED_TICKS` specifically | the tick-scalper's stop | implemented at `base.py:294-295` | `EXPRESSIBLE-NEVER-VARIED` | `[measured: python3 -c "...set(e.stop_kind for e in expand_exit_models(...))" → no FIXED_TICKS in any of the 11]`. Note `stop_mult` is reinterpreted as a *tick count* for this kind — a units overload worth flagging |
| R3 | Stop width | 1–3 ATR typical; wider in trend systems | `stop_mult` | `EXPRESSIBLE-VARIED` | `[measured: 5 distinct values {0.75, 1.0, 1.2, 1.5, 2.5}]`. **CANCELLING — settled** (BRIEF r3) |
| R4 | Noise floor on the stop | never inside the spread/noise | `ContractSpec.min_stop_ticks`, enforced twice | `EXPRESSIBLE-VARIED` | `[repo-verified: base.py:313-315 and base.py:719-723]`. Per-contract: MNQ 16, MES 8, MGC 25, MCL 15 `[measured: python3 -c "get_contract(s).min_stop_ticks"]`. Settled by BRIEF r4 |
| R5 | Padding beyond a structural level | 2–5 ticks past the swing so the level itself is not the stop | `stop_pad_ticks` | `EXPRESSIBLE-VARIED` | `[repo-verified: base.py:215]`; `[measured: {2,3,4}]`. But confounded with `stop_kind` — only structural/band exits set it |
| R6 | Working stop vs disaster stop | two levels: the one you manage and the one that is never moved | one stop only; `initial_stop` is recorded but only for reporting | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:167-168 — `stop` and `initial_stop`; only `pos.stop` is ever compared against price at engine.py:403]`. **Missing primitive: a second price level on `_OpenPosition` that the trail and breakeven logic may not cross** |
| R7 | Mental stop / discretionary invalidation | exit on a *reason*, not a price | `StrategySignal.invalidation` is a **human-readable string** | `PARTIAL` (decorative) | `[repo-verified: base.py:516, base.py:770-774]` — it is formatted prose, never parsed or evaluated. It is also **dropped before the Trade**: `invalidation` is in the StrategySignal-minus-Trade field set `[measured: dataclasses.fields diff → {bar_index, entry, evidence, invalidation, stop, strength, timeframes, ts}]` |

## 3. Size (9 axes)

Every row here inherits one fact: **`futures_agents/backtest/` never imports
`futures_agents/risk/` and never imports `AccountConfig`**
`[measured: grep -rn "AccountConfig" futures_agents/backtest/*.py → empty]`. So each of these
either exists on the *live* path only, or nowhere.

| # | axis | what operators do | library handle | verdict | evidence |
|---|---|---|---|---|---|
| S1 | Risk-per-trade basis | % of equity, % of the drawdown buffer, fixed dollar, fixed contracts | `RiskManager.risk_budget` — `min(usable_buffer × base_risk_pct_of_buffer, equity × max_risk_pct_of_equity, max_dollar_risk)` | `INEXPRESSIBLE-ARCH` (in research) | `[repo-verified: risk/manager.py:140-195; config.py:361-364]`. **Missing primitive: `BacktestEngine.__init__` has no `account: AccountState` parameter `[repo-verified: engine.py:231-242]`** |
| S2 | Integer rounding of size | always floor; a 0-contract answer means no trade | `contracts_for` → `int(math.floor(...))`, never rounds up | `INEXPRESSIBLE-ARCH` (in research), and **the most consequential row in this table** | `[repo-verified: risk/manager.py:197-203]`, `[repo-verified: tests/test_risk.py:150-157]`. See `R3_path_operation.md` §B-3 part (c): the floor deletes wide-stop trades, so it is a volatility filter on entries, i.e. a Channel-2 effect |
| S3 | Volatility normalisation of size | risk N ticks where N ∝ ATR | **already mandatory and invisible**: R is defined as `stop_mult × atr` | `EXPRESSIBLE-NEVER-VARIED` (no control arm exists) | `[repo-verified: base.py:284-288, engine.py:22-25, engine.py:484-495]`. See `R3_path_operation.md` §B-2 |
| S4 | Kelly / fractional Kelly | f* from measured win rate and payoff, then halved | **nothing** | `INEXPRESSIBLE-ARCH` | `[measured: grep -rn -i "kelly" --include=*.py . → no match anywhere in the repo]`. **Missing primitive: nothing computes `E[log(1+fR)]`; `montecarlo.py` walks a path at a *flat* `dollar_risk_per_trade` scalar `[repo-verified: montecarlo.py:118-120, 213]`** |
| S5 | Risk parity across strategies | equal risk contribution, not equal dollars | nothing | `INEXPRESSIBLE-ARCH` | same missing primitive as S1 plus a covariance matrix across strategies, which requires a shared timeline the batch runner does not build `[repo-verified: engine.py:262-267]` |
| S6 | Conviction / strength scaling | bigger on the A+ setup | `StrategySignal.strength` is **computed and discarded** | `PARTIAL` — 1 field from reachable | `[repo-verified: base.py:515 (field), base.py:686+766 (computed)]`; `[measured: grep -n "strength" futures_agents/backtest/engine.py → no match]`. **Missing primitive: `Trade.strength`.** This is the cheapest high-value build on the track |
| S7 | Equity-curve / streak scaling | halve after 2 losses; stand down after 3 | exists live: `day.consecutive_losses ≥ 2 → × 0.75^(n−1)`; `max_consecutive_losses = 3 → observation-only` | `INEXPRESSIBLE-ARCH` (in research), **but replayable from stored artefacts** | `[repo-verified: risk/manager.py:168-171; config.py:372]`. Replayable: `workspace/strategy_research/scratch/geo_trades.json` holds 21,954 trades with `ts` and `r` `[measured: python3 -c "json.load(...)" → 21954 rows, keys ['arm','base','cell','dir','exitm','mae','mfe','mins','r','reason','regime','session','slice','symbol','tf','ts','vol']]` |
| S8 | Drawdown de-risk ladder | cut size as the buffer is consumed | `AccountConfig.derisk_ladder`, 6 rungs from ×1.00 to ×0.00 | `INEXPRESSIBLE-ARCH` (in research) | `[repo-verified: config.py:386-396, config.py:430-440, risk/account.py:151-152]`. Note the ladder is read by `ui/` and `config.py` only — `risk/manager.py` consumes the *derived* multiplier `[measured: grep -rn "derisk_ladder" → config.py, ui/state.py, ui/api.py; risk/manager.py reads `st.derisk_multiplier` at :160]` |
| S9 | Capacity / market impact | participation rate caps size long before risk does | **nothing**. `SlippageModel` has no size term; cost in R is exactly size-invariant | `INEXPRESSIBLE-ARCH` | `[repo-verified: costs.py:29-33 (five fields, none size-dependent); costs.py:104-110 and :119-122 (both linear in `contracts`, so the ratio is constant)]`. **Missing primitive: `SlippageModel.impact_ticks_per_contract`** |

## 4. In-trade management (9 axes)

| # | axis | what operators do | library handle | verdict | evidence |
|---|---|---|---|---|---|
| M1 | Breakeven move | move to entry at +1R, or after the first partial | `breakeven_at_r` | `EXPRESSIBLE-VARIED` | `[repo-verified: base.py:219; engine.py:445-450]`; `[measured: {1.0, 1.5, 2.0, None}]`. **CANCELLING — Channel 1** |
| M2 | Trailing stop | ATR trail, chandelier off the highest high, parabolic, structural (under each new swing), % trail | one only: chandelier at `bar.high − mult × atr` | `EXPRESSIBLE-NEVER-VARIED` — **never run once** | `[repo-verified: base.py:220 (`trail_atr_mult=None`); engine.py:451-462 (the implementation)]`; `[measured: all 11 catalogue exits → trail_atr_mult ∈ {None}; 314 generated MGC strategies → {None}]`. Parabolic and structural trails: `INEXPRESSIBLE-ARCH`, **missing primitive: `ExitModel.trail_kind`** |
| M3 | Trail *reason* reporting | you need to know a trail exit from a stop-out | `ExitReason.TRAIL` is declared and unreachable | `DEAD-HANDLE` | `[repo-verified: engine.py:53]`; `[measured: grep -rn "ExitReason.TRAIL" → engine.py:53 only]`. A trailed exit is labelled STOP or BREAKEVEN `[repo-verified: engine.py:419-421]` |
| M4 | Trail activation threshold | "start trailing only after +1R" | none — the trail, if set, is active from bar 1 | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:451 — `if exit_model.trail_atr_mult:` with no R gate]`. **Missing primitive: `ExitModel.trail_from_r`** |
| M5 | Time-decay stop | tighten the stop the longer it goes nowhere | none | `INEXPRESSIBLE-ARCH` | **Missing primitive: `ExitModel` has no bars-held term in its stop computation; `stop_price` is called once, at signal time `[repo-verified: base.py:716]`** |
| M6 | **Exit on a signal / indicator** | the exit half of *every* MA-crossover and Donchian system: exit when the condition that got you in stops holding | **none.** `ExitModel` has 12 fields and not one is a condition | `INEXPRESSIBLE-ARCH` — **the largest gap on this track** | `[measured: dataclasses.fields(ExitModel) → 12 fields, all prices/clocks/flags]`; `[measured: grep -rn "exit_condition" --include=*.py . → no match]`. **Two named missing primitives: (1) `ExitModel.exit_conditions: Tuple[Condition, ...]`; (2) `_manage` takes `bar: Bar` and has no `FeatureSnapshot` — `[repo-verified: engine.py:377-378]` — so it is structurally blind to every indicator. The snapshot is built only at `engine.py:310-311`, *after* management, and only when a strategy is flat.** The plumbing fix is cheap: hoist `self.frame.snapshot(i)` above step 2 |
| M7 | Stop-and-reverse / always-in-the-market | the dominant CTA trend operating mode: you are always long or short, and the exit *is* the opposite entry | impossible — the engine does not evaluate a strategy while it holds a position | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:304-309 — "look for new signals (never while already positioned)"; the `continue` at :308-309]`. Same missing primitive as M6 plus a same-bar close-and-open path |
| M8 | Pyramiding / unit adds | Turtle adds at +0.5N, four units max; anti-martingale | impossible — one position per strategy | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:304-309]`. `max_concurrent_per_strategy` is accepted and **never read** — a `DEAD-HANDLE` that would let a future study believe it had tested this `[repo-verified: engine.py:232, 240]`; `[measured: grep -rn "max_concurrent" → set at engine.py:240, read nowhere]` |
| M9 | Averaging down / martingale adds | the classic destroyer | impossible, same line | `INEXPRESSIBLE-ARCH` — and here the constraint is a *feature* | `[repo-verified: engine.py:304-309]`. See §7 A4 |

## 5. Exit (10 axes)

| # | axis | what operators do | library handle | verdict | evidence |
|---|---|---|---|---|---|
| X1 | Target basis | fixed R, measured move, structural objective, ATR anchor, no target at all | `TargetKind` = {R_MULTIPLE, ANCHOR_ATR, ANCHOR_STRUCTURE} | `EXPRESSIBLE-VARIED` | `[repo-verified: base.py:165-184]`. **CANCELLING — settled**; `x_exits`: anchored raises payoff (z=−13.83), not expectancy `[repo-verified: workspace/studies/DEFECTS.md:210]` |
| X2 | No target / trail-only | let it run, exit only on the trail | `ExitModel.__post_init__` **forbids it**: `if not self.targets_r: raise ValueError("at least one target is required")` | `INEXPRESSIBLE-ARCH` | `[repo-verified: base.py:229-230]`. **Missing primitive: `targets_r` must be permitted to be empty, which in turn requires M2 to work.** A pure trend-following exit (no target, trail only) — the most common CTA exit `[general knowledge]` — cannot be constructed |
| X3 | Number of targets | 1–3 | `len(targets_r)` | `EXPRESSIBLE-VARIED` | `[measured: 7 distinct ladders, lengths 1–3]`. `x_exits`: three targets worse than two (z=−2.87) `[repo-verified: DEFECTS.md:210]` |
| X4 | Scale-out fractions | thirds, halves, "sell half and hold the rest" | `scale_out` | `EXPRESSIBLE-VARIED` in shape, but see X5 | `[repo-verified: base.py:217-218; engine.py:433-439]` |
| X5 | **Residual runner** (`sum(scale_out) < 1`) | the single most common real exit: bank some, leave a runner with no target | **permitted by the validator, never generated** | `EXPRESSIBLE-NEVER-VARIED` | `[repo-verified: base.py:235-236 — the check is `sum > 1.0`, so a sum below 1 is legal]`; `[measured: all 11 catalogue exits → scale_out sums = {1.0}; 314 generated strategies → {1.0}]`. The runner would then exit on stop/trail/time/session-close. **This is the single cheapest untested operating rule in the library** |
| X6 | Divisibility of the position | you cannot sell 0.3 of a contract | `remaining` starts at exactly `1.0` and is decremented by fractions | `PARTIAL` (unrealistic) | `[repo-verified: engine.py:374, 433-439]`. `(0.5, 0.3, 0.2)` requires ≥10 contracts to express without rounding; the shipped budget permits ~1 `[repo-verified: config.py:361-364]` |
| X7 | Time stop | "if it has not worked in N bars, it is not working" | `time_stop_bars`, counted in the strategy's own bars | `EXPRESSIBLE-VARIED` in magnitude; **never switched off** | `[repo-verified: base.py:221; engine.py:392-393, 464-467]`; `[measured: {30,40,45,50,60,80,90,100,120}; time_stop_bars is None in 0 of 11]`. So "no time stop" is not in the hypothesis space |
| X8 | Session-close flatten | intraday desks are flat at the bell | `exit_at_session_close`, ANDed with `not engine.allow_overnight` | `EXPRESSIBLE-CONFOUNDED` | `[repo-verified: base.py:224; engine.py:469-473]`. **D19: it is an exact alias for anchored targets — zero overlap** `[repo-verified: workspace/studies/DEFECTS.md:236-241]`. And `allow_overnight` is never passed by any of the 18 `BacktestEngine(` call sites `[measured: grep → none]` |
| X9 | Week-end / month-end flatten | flat into the weekend; flat over a roll | nothing | `INEXPRESSIBLE-ARCH` | `[measured: dataclasses.fields(ExitModel) → no day-of-week or calendar term]`. **Missing primitive: `ExitModel.exit_before_weekend: bool`; the clock exists (`timeutil.trading_day`, used at `engine.py:129-130`) so this is wiring** |
| X10 | Hold-period targeting | "this is a 3-day trade" — exit on a horizon, not a bar count | approximated by `time_stop_bars × primary_tf`; not a wall-clock horizon | `PARTIAL` | `[repo-verified: engine.py:392-393]` — the conversion is `primary_tf // base_minutes`, so a horizon expressed in *calendar* time drifts with session gaps. `Trade.minutes_held` records the truth `[repo-verified: engine.py:512]` but nothing acts on it |

## 6. Re-entry and campaign management (5 axes)

| # | axis | what operators do | library handle | verdict | evidence |
|---|---|---|---|---|---|
| C1 | Cooldown after a stop | "no re-entry for N bars / not until a new swing forms" | **none.** After a stop the strategy is flat and re-fires on the very next bar its conditions hold | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:298-309 — the position is deleted from `open_pos` at :302 and the same `sid` is eligible again at :306 on the same bar]`. **Missing primitive: `StrategyFilters.cooldown_bars` (the field) plus a `last_exit_index: Dict[str, int]` in `run_many` (the state).** So re-entry in this repo is **unconditionally maximal** and has never been varied |
| C2 | Re-entry limit per setup / per day | two attempts and done | none | `INEXPRESSIBLE-ARCH` | same missing primitive as C1, plus a per-day counter |
| C3 | Re-entry only at a better price | re-enter only if the second entry is better than the first | none | `INEXPRESSIBLE-ARCH` | same primitive plus a `last_exit_price` |
| C4 | Campaign risk | total risk across all attempts on one idea is capped at 1R, not 1R each | none. Each re-entry is a fresh, full-size 1R | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:371-375 — `remaining=1.0` on every new position, unconditionally]`. **Missing primitive: a campaign identifier on `_OpenPosition` grouping re-entries** |
| C5 | Scratch / breakeven discretionary exit | "this is not behaving — I am out at flat" | `ExitReason.BREAKEVEN` exists but is only reachable via the breakeven *stop* being hit | `PARTIAL` | `[repo-verified: engine.py:52, 419-421]`. A discretionary scratch needs M6 |

## 7. Portfolio and governance (9 axes)

Every row: **exists on the live path, unreachable from the backtester** — one shared missing
primitive, stated once at the foot.

| # | axis | what operators do | library handle | verdict | evidence |
|---|---|---|---|---|---|
| P1 | Max concurrent positions | 2–5 for a discretionary intraday book | `AccountConfig.max_concurrent_positions = 2`, enforced at `risk/manager.py:249-252` | `INEXPRESSIBLE-ARCH` (research) | `[repo-verified: config.py:373; risk/manager.py:249-252]` |
| P2 | Max correlated positions | one per correlation group — MES and MNQ are one bet | `max_correlated_positions = 1`; `ContractSpec.correlation_group` exists | `INEXPRESSIBLE-ARCH` (research) | `[repo-verified: config.py:374]`. Relevant here because BRIEF says MES/MNQ/NQ/ES are one index complex |
| P3 | Total portfolio heat | sum of open risk capped at X% of equity | nothing, at any layer | `INEXPRESSIBLE-ARCH` everywhere | `[measured: grep -rn -i "heat\|total_open_risk" --include=*.py futures_agents/ → no match]` |
| P4 | Daily loss limit | hard stop for the session | `daily_loss_limit = 1000`, `daily_soft_loss_limit = 600` | `INEXPRESSIBLE-ARCH` (research); **replayable from artefacts** | `[repo-verified: config.py:367-368; risk/manager.py:165-167]` |
| P5 | Daily profit lockdown / giveback | protect a good day | `daily_profit_lockdown = 1500`, `daily_giveback_pct = 0.40` | `INEXPRESSIBLE-ARCH` (research); replayable | `[repo-verified: config.py:369-370]` |
| P6 | Max trades per day | 6 | `max_trades_per_day = 6` | `INEXPRESSIBLE-ARCH` (research); replayable | `[repo-verified: config.py:371]` |
| P7 | Consecutive-loss stand-down | 3 and you are done for the day | `max_consecutive_losses = 3` | `INEXPRESSIBLE-ARCH` (research); replayable | `[repo-verified: config.py:372]`. Note the *metric* `Metrics.max_consecutive_losses` is a different object with the same name `[repo-verified: backtest/metrics.py:71-72]` — a name collision that inflates any grep-based census |
| P8 | Equity-curve trading (system on/off) | stop trading the system when its curve is below its own MA | nothing | `INEXPRESSIBLE-ARCH`; replayable | `[measured: grep -rn -i "equity_curve" → `BacktestResult.equity_curve_r` at engine.py:210-215 (reporting only) and `storage.py:641`]` |
| P9 | Netting across strategies | two strategies long the same contract is one position | none — `run_many` keeps "completely independent position state" | `INEXPRESSIBLE-ARCH` | `[repo-verified: engine.py:262-267, 282-283]`. **`run_portfolio` is a batch runner, not a portfolio simulator** `[repo-verified: engine.py:554-559]` |

**The one shared missing primitive for all nine:** `BacktestEngine.__init__` has no
`account: AccountState` parameter `[repo-verified: engine.py:231-242]`, and `run_many`'s only
shared state is `open_pos` and `pending`, both keyed by `strategy_id`
`[repo-verified: engine.py:282-283]`. Add an account object plus a `Dict[str, float]` of open
risk keyed by `ContractSpec.correlation_group` and **P1–P9 all become reachable at once.**

## 8. Roll mechanics (3 axes)

| # | axis | what operators do | library handle | verdict | evidence |
|---|---|---|---|---|---|
| L1 | When to roll | on volume crossover, on OI crossover, N days before expiry, on the exchange roll date | nothing — there is no contract-month label in the data | `INEXPRESSIBLE-DATA` | `[repo-verified: DIVISION Appendix B.1 — every one of the 48 `csv/raw/` files has header `open_time,open,high,low,close,volume`]`; `[measured: head -1 csv/raw/MGC_1h.csv → open_time,open,high,low,close,volume]`. **Missing primitive: a contract-month or expiry column.** Boundary note: the *curve* side of this is R2's (DIVISION §5.6); I claim only the operational half |
| L2 | How to roll | as a calendar spread, one ticket, never legged | nothing | `INEXPRESSIBLE-DATA` | same. Two expiries do not exist in one frame `[repo-verified: engine.py:548, 554 — each takes one `frame: SymbolFrame`]` |
| L3 | Carrying a position through a roll | close and reopen, or hold the spread | the continuous series hides the event entirely; where it is visible it is a **defect** (D40, spliced grain CSVs) | `INEXPRESSIBLE-DATA` | `[repo-verified: workspace/studies/DEFECTS.md:583-601 (D40)]` |

## 9. Meta-labelling and strategy selection (4 axes)

| # | axis | what operators do | library handle | verdict | evidence |
|---|---|---|---|---|---|
| T1 | Binary meta-label ("take this signal or not") | a second model gates the primary | closest analogue is a `ConditionKind.FILTER`, which gates *before* the signal, not after | `PARTIAL` | `[repo-verified: base.py:670-675 — filters are evaluated first and short-circuit]`. A true meta-label needs the primary's own features as input; `Evidence` objects carrying exactly that are built at `base.py:688-691` and **dropped before the Trade** `[measured: field diff includes `evidence`]` |
| T2 | Continuous meta-label → size | see S6 | `StrategySignal.strength`, discarded | `PARTIAL` | `[repo-verified: base.py:515, 766]`; **missing primitive `Trade.strength`** |
| T3 | Strategy on/off by recent performance | trade only what has been working | this is precisely what the repo measured and **refuted**: last period's top 10 returns −0.0155R vs a −0.0104R null and underperforms trading everything | `EXPRESSIBLE-VARIED` — settled negative | `[repo-verified: BRIEF.md §"What the research already established"; workspace/studies/RANKING_FINDINGS.md]`. Not re-litigated |
| T4 | Minimum expected-RR gate | "I do not take anything under 1.5:1" | `ExitModel.min_reward_risk`, but applied **only when the target is anchored** | `EXPRESSIBLE-CONFOUNDED` | `[repo-verified: base.py:741-743]` — the R_MULTIPLE exclusion is the D8 fix; with R-multiple targets the ratio is static, so the floor deleted whole exits on every bar `[repo-verified: DEFECTS.md:102-118 (D8)]` |

## 10. Anti-strategy: what operationally destroys expectancy (4 axes)

DIVISION III-19. The interesting result here is **inverted**: this library is structurally
incapable of expressing most of the classic destroyers, which is a form of safety, and it
means "anti-strategy" cannot be tested here either.

| # | axis | the destroyer | can this library do it? | evidence |
|---|---|---|---|---|
| A1 | Moving the stop away from price | widen the stop to avoid taking the loss | **No.** The trail is monotone: `pos.stop = max(pos.stop, trail)` long / `min` short, and breakeven only ever moves the stop *toward* entry from a losing position's perspective | `[repo-verified: engine.py:462, 449]`. Structurally one-way |
| A2 | Martingale after a loss | double up | **No.** One position, fixed `remaining=1.0`; and the live layer is explicitly one-way down: *"It is never scaled up: a winning streak is not information about edge"* | `[repo-verified: engine.py:374; risk/manager.py:146-147]` |
| A3 | Over-trading | no cap on trades per day | **Partly yes** — no cap exists in the backtester, so the shipped population is the over-trading arm by default. The *disciplined* arm is the one that cannot be expressed (P6) | `[repo-verified: engine.py:304-309 — no counter of any kind]` |
| A4 | Removing the stop | "it will come back" | **No.** `Strategy.evaluate` returns `None` when the stop cannot be computed — "an unmeasurable stop means an unmeasurable risk, and the trade is simply not taken" | `[repo-verified: base.py:271-275, 717-723]` |

**So the anti-strategy family is INEXPRESSIBLE in the direction that matters**, and the one
destroyer the library *does* express by default is over-trading, because it has no trade cap.
Named missing primitive for the whole family: the same `account: AccountState` on
`BacktestEngine` (§7) — you cannot test indiscipline without modelling the thing the
discipline protects.

---

## Split

| verdict | count |
|---|---|
| `EXPRESSIBLE-VARIED` | **9** (R1, R3, R4, R5, X1, X3, X4, X7, T3) |
| `EXPRESSIBLE-NEVER-VARIED` | **5** (E2, R2, S3, M2, X5) |
| `EXPRESSIBLE-CONFOUNDED` | **2** (X8, T4) |
| `PARTIAL` | **6** (R7, S6, X6, X10, C5, T1/T2 counted once as T1) |
| `DEAD-HANDLE` | **4** (E2 also, E6, M3, M8's `max_concurrent_per_strategy`) |
| `INEXPRESSIBLE-ARCH` | **30** |
| `INEXPRESSIBLE-DATA` | **3** (L1, L2, L3) |
| **total axes** | **62** |

(E2 and M8 each carry two verdicts — the handle exists and is also never read — so the column
sums to 63 labels over 62 axes.)

**Three sentences that summarise the whole matrix.**

1. **This library can shape a trade and cannot manage one.** Twelve `ExitModel` fields
   describe price levels, a clock and a session boundary; none of them is a condition, and
   `_manage` never receives a `FeatureSnapshot` `[repo-verified: engine.py:377-378]`. So every
   exit is geometric and none is informational.
2. **The operating layer that exists is on the wrong side of an import boundary.** Nineteen
   `AccountConfig` operating parameters are enforced at `risk/manager.py` and zero are visible
   to `backtest/` `[measured: grep -rn "AccountConfig" futures_agents/backtest/*.py → empty]`.
3. **Where the vocabulary exists it is usually pinned.** Of the 62 axes, 9 have ever been
   varied. The exit catalogue holds one chandelier trail that has never been switched on, one
   scale-out shape that always sums to 1.0, one time stop that is never None, and one
   `StrategyFilters` identity across 314 generated strategies
   `[measured: python3 -c "generate_strategies('MGC',[5,15,60,240],max_total=400)" → 314
   strategies, 1 distinct filters.identity, trail_atr_mult ∈ {None}, scale_out sums ∈ {1.0},
   time_stop_bars is None in 0]`.
