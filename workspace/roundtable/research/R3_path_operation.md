# R3 — Path and operation: managing a position through time

**Track:** R3 (DIVISION §2). **Class:** III — the position's own path.
**Owner:** researcher R3. **Round:** 1. **Started:** 2026-09-27.
**Scope note:** `BRIEF.md` read in full; `DIVISION.md` read in full; `msgs/01` read.
Round 1 produces **no new expectancy numbers and no z-scores** (DIVISION §0, §8). Every
number below is either a read of the code, a read of an existing artefact, or a short
`python3 -c` inspection whose exact command is pasted beside it.

**Marking convention** (`BRIEF.md` rule 3): `[general knowledge]`, `[repo-verified: path:line]`,
`[measured: command → result]`.

**Two things I am explicitly NOT doing**, because DIVISION §5.9 and §6 forbid it:
re-deriving the win-rate/payoff cancellation (`BRIEF.md` rule 3, measured four times), and
re-arguing any of the eight settled rules. Where an operating axis lands on that
cancellation I label it `CANCELLING — settled` once and move on.

---

# Part A — The engine audit (what the operating layer actually does)

This part comes first because every expressibility verdict in Part B depends on it, and
because the manager's brief to me named the operating layer as the place "this library has
historically been wrong about *what it was even testing*". It was right. I found **eleven**
items; six of them are new (no entry in `workspace/studies/DEFECTS.md` D1–D43), four
sharpen an existing defect, and one is a clean bill of health I want on the record.

## A-1 (NEW) The trailing stop has never run. Not once.

`ExitModel.trail_atr_mult` defaults to `None`
`[repo-verified: futures_agents/strategies/base.py:220]`. The engine implements a
chandelier trail against it at `[repo-verified: futures_agents/backtest/engine.py:451-462]`.

**No exit model in the shipped catalogue ever sets it.**

`[measured: python3 -c "from futures_agents.strategies.combinator import expand_exit_models;
all_e=expand_exit_models(include_structure=True,include_aggressive=True,include_anchored=True);
print(len(all_e), sorted(set(repr(e.trail_atr_mult) for e in all_e)))"
→ 11 ['None']]`

`[measured: python3 -c "from futures_agents.strategies.combinator import generate_strategies;
S=generate_strategies('MGC',[5,15,60,240],max_total=400);
print(len(S), set(s.exit.trail_atr_mult for s in S))" → 314 {None}]`

Consequence: of the five trailing-stop variants a real operator chooses between (fixed ATR
trail, chandelier off the highest high, parabolic/SAR, structural trail under each higher
swing low, breakeven-then-trail) `[general knowledge]`, this repo implements exactly one and
has tested zero. Every statement anywhere in `scan_reports/` about "exit geometry" is a
statement about **stop width, target ladder, breakeven and time**, with the trail held at
off. That is not a small omission: trailing is the single most common way a discretionary
futures operator converts a 1R winner into a 4R winner `[general knowledge]`.

## A-2 (NEW) `ExitReason.TRAIL` is defined and can never be emitted.

`[repo-verified: futures_agents/backtest/engine.py:53]` declares it. It appears nowhere else
in the codebase.

`[measured: grep -rn "ExitReason.TRAIL" --include=*.py . → futures_agents/backtest/engine.py:53 only]`

The mechanism: the trail at `engine.py:451-462` mutates `pos.stop`. The exit then happens
through the ordinary stop branch at `engine.py:402-422`, which labels the reason
`BREAKEVEN` if the stop sits within one tick of entry and `STOP` otherwise
`[repo-verified: engine.py:419-421]`. So even if `trail_atr_mult` were switched on
tomorrow, a trailed-out trade would be reported as an ordinary stop-out. **The exit-reason
histogram in this repo structurally cannot tell a trail exit from an initial-stop exit.**
This is the vocabulary being wrong about what it is measuring, in the narrow literal sense.

## A-3 (NEW) `max_concurrent_per_strategy` is a dead knob.

`BacktestEngine.__init__` accepts it and stores it
`[repo-verified: futures_agents/backtest/engine.py:232, 240]`. `self.max_concurrent` is then
**never read anywhere**.

`[measured: grep -rn "max_concurrent" --include=*.py . → engine.py:232,240 (set);
ui/state.py:157, ui/api.py:168, config.py:373, risk/manager.py:249,252 (a DIFFERENT
field, `AccountConfig.max_concurrent_positions`, on the live path only)]`

The actual position-count rule is hard-coded as a single `continue` at
`[repo-verified: futures_agents/backtest/engine.py:304-309]`:

```
# --- 3. look for new signals (never while already positioned) ---
if i + 1 < stop_at:
    for s in strategies:
        sid = s.strategy_id
        if sid in open_pos or sid in pending:
            continue
```

**One position per strategy, always, with no way to ask for more.** This is the single line
that makes pyramiding (III-8) INEXPRESSIBLE-ARCHITECTURE, and the API surface advertising a
concurrency parameter that does nothing is worse than not having one — a future study could
pass `max_concurrent_per_strategy=3`, get no error, and believe it had tested unit adds.

## A-4 (NEW) `signals_skipped_in_position` is declared and never assigned.

`[repo-verified: futures_agents/backtest/engine.py:201]` declares the field on
`BacktestResult`, default 0. The `continue` at `engine.py:308-309` skips the signal without
incrementing it.

`[measured: grep -rn "signals_skipped_in_position" --include=*.py . → engine.py:201 only]`

So the **opportunity cost of the flat-only rule is not merely untested, it is unrecorded.**
The repo cannot answer "how many signals did being in a position cost me?" from any
existing artefact, because the counter that was built to answer it is always zero. That is
the cheapest possible fix in this whole audit — one line — and it is the prerequisite for
ever costing A-3.

## A-5 (NEW) The scope-filter vocabulary is inert in the generation path.

`StrategyFilters` carries eight behavioural fields: `sessions`, `regimes`, `volatility`,
`days_of_week`, `rth_only`, `min_minutes_since_open`, `max_minutes_since_open`,
`require_alignment` `[repo-verified: futures_agents/strategies/base.py:389-396]`.

`generate_combinations` attaches `filters=template.filters`
`[repo-verified: futures_agents/strategies/combinator.py:581]` and `_build_strategy` passes
it straight through `[repo-verified: futures_agents/strategies/combinator.py:648]`. There is
no enumeration over filter *scope* anywhere in the generator — `_filter_sets`
`[repo-verified: combinator.py:446-457]` enumerates **condition** filters (the lowercase
library tags), which is a different mechanism.

Measured on a real generation:

`[measured: python3 -c "from futures_agents.strategies.combinator import generate_strategies;
import collections; S=generate_strategies('MGC',[5,15,60,240],max_total=400);
print(len(S), len(collections.Counter(s.filters.identity for s in S)))" → 314 1]`

**One distinct `StrategyFilters` identity across 314 strategies**, namely
`days_of_week=None|max_minutes_since_open=None|min_minutes_since_open=None|regimes=None|require_alignment=None|rth_only=True|sessions=None|volatility=None`.

Only one of the thirteen templates sets any non-default scope at all — `OPENING_RANGE`, with
`max_minutes_since_open=150` `[measured: python3 -c "...for t in TEMPLATES: print(t.group,
non-default filter fields)" → 12 of 13 DEFAULT, OPENING_RANGE {'max_minutes_since_open': 150}]`.

This is the structural reason D43 mattered so much and the reason the hours-filter and
`rth_only` studies (D23, D24 and the D24 correction) all had to be run by hand outside the
generator. It is also why `BRIEF.md` rule 6 ("no hours filter improves expectancy") rests on
bespoke re-emission rather than on the shipped population.

## A-6 (NEW) The news slippage premium is unreachable from the backtester.

`SlippageModel.news_extra_ticks = 2.0` exists
`[repo-verified: futures_agents/backtest/costs.py:33]` and `ticks()` honours a `news=` flag
`[repo-verified: costs.py:35-47]`. The engine calls `slippage_price` in exactly two places —
entry `[repo-verified: engine.py:353-354]` and stop `[repo-verified: engine.py:416-417]` —
and **neither passes `news=`**.

`[measured: grep -rn "news=True" --include=*.py futures_agents/ → no match in backtest/]`
`[measured: grep -rn "slippage_price\|slippage_dollars" --include=*.py futures_agents/backtest/
→ engine.py:353, engine.py:416, costs.py definitions only]`

So a fill inside a high-impact release window is costed identically to a fill at 11:00 on a
quiet Tuesday. Two extra ticks on MNQ is $1.00/contract, against an all-in round turn of
roughly $1.94 `[repo-verified: costs.py:4-7]` — i.e. the unmodelled premium is about half a
round turn again, on precisely the bars where real slippage is worst `[general knowledge]`.
This understates cost for every event-window trade, and `econ_calendar.py` already exists to
supply the flag, so the gap is wiring, not data.

## A-7 (SHARPENS D13) Every time-based and session-based exit is slippage-free by construction.

D13 records that "scale-out legs are charged neither commission nor slippage" and that
"62–92% of 4h/daily exits pay no exit slippage at all"
`[repo-verified: workspace/studies/DEFECTS.md:169-173]`. The mechanism is more general than
partials, and naming it matters for my track because it hits exactly the axes the manager
predicted would be the real expectancy changers.

`_close` is called with an explicit price. Of its six call sites
`[repo-verified: futures_agents/backtest/engine.py:326, 422, 442, 467, 473, 476]`:

| site | reason | price passed | slipped? |
|---|---|---|---|
| 422 | STOP / BREAKEVEN | `pos.stop - sign*slip` or gap open | **yes** (`is_stop=True`) |
| 442 | TARGET | limit level `t`, or a favourable gap open | no — correct, a resting limit |
| 467 | TIME | `bar.close` | **no** |
| 473 | SESSION_CLOSE | `bar.close` | **no** |
| 476 | END_OF_DATA | `bar.close` | **no** |
| 326 | END_OF_DATA (tail) | `bars[last_i].close` | **no** |

A time stop and a session-close flatten are **market orders** `[general knowledge]`. Charging
them at the bar close with zero slippage and zero extra commission is the flattering reading
in exactly the direction that makes "turn `exit_at_session_close` off" (D12, z = +3.52)
and "hold time matters" look like cleaner results than they are. The fix is one call to
`self.costs.slippage_price(is_stop=True, ...)` at three sites.

## A-8 (SHARPENS D13) Scale-out assumes an infinitely divisible contract.

`ExitModel.scale_out` is a tuple of fractions `[repo-verified: base.py:217-218]`; the engine
takes `frac` of `pos.remaining`, which starts at exactly `1.0`
`[repo-verified: engine.py:374, 433-439]`. The catalogue's default is `(0.5, 0.3, 0.2)`
`[repo-verified: base.py:218]`.

You cannot sell 0.3 of a futures contract. A `(0.5, 0.3, 0.2)` ladder needs a minimum of ten
contracts to express without rounding, and MGC/MCL/MES/MNQ micros are the *small* unit
precisely because a retail account trades one to three of them `[general knowledge]`. So the
shipped default exit geometry is **only operable at a size the risk layer would rarely
approve**, and the backtest never notices because it works in R on a notional single
contract `[repo-verified: engine.py:22-25]`. Combined with D13's under-costing, the
multi-target ladder is flattered twice: it pays one round turn instead of three, and it
assumes a divisibility the instrument does not have.

**This is the first place sizing stops being admin.** Whether a 3-target ladder is even
*available* to you is a function of contract count, which is a sizing decision. The repo's
architecture makes that dependency invisible.

## A-9 (NEW) `_OpenPosition.atr_at_entry` is a dead field.

Declared `[repo-verified: engine.py:183]`, always constructed as `None`
`[repo-verified: engine.py:374]`, never read.
`[measured: grep -rn "atr_at_entry" --include=*.py . → engine.py:183, engine.py:374 only]`
Harmless, but it is the signature of a volatility-normalised-exit feature that was scaffolded
and abandoned — and it is the field a vol-targeted trail would need.

## A-10 (NEW) `allow_overnight` can never be True in any published result.

`BacktestEngine.__init__(..., allow_overnight: bool = False)`
`[repo-verified: engine.py:233]`, read once at `[repo-verified: engine.py:470]` where it
gates `exit_at_session_close`. No caller anywhere passes it.

`[measured: grep -rn "allow_overnight" --include=*.py . | grep -v "engine.py" → (empty)]`
`[measured: grep -rn "BacktestEngine(" --include=*.py . → 18 sites, none passing allow_overnight]`

So the engine-level override exists, has never been used, and the only way any result in
this repo ever held a position overnight was via a strategy setting
`exit_at_session_close=False` — which per D19 is an exact alias for anchored targets
`[repo-verified: workspace/studies/DEFECTS.md:236-241]`. The two knobs that could have
separated "hold overnight" from "target geometry" are one unused parameter and one
perfectly-collinear flag.

## A-11 (CLEAN BILL) No look-ahead in the position lifecycle. Checked five ways.

I went looking for repainting and future-data leakage in the management loop specifically,
because that is where it usually hides, and I did not find it. Recording that as a result:

1. **Entry.** Signals are computed from `snapshot(i)`; the fill is at bar `i+1`'s open with
   adverse slippage `[repo-verified: engine.py:290-295, 305, 344-355]`. The pending dict is
   drained at the *top* of the next bar, before management. Correct.
2. **Stop wins ties.** When a bar contains both stop and target, the stop fills
   `[repo-verified: engine.py:408-409, costs.py:62-65]`. Pessimistic, correct.
3. **Gaps.** A gap through the stop fills at the open, worse than the stop
   `[repo-verified: engine.py:410-412]`. A gap through a target fills at the open, better
   `[repo-verified: engine.py:430-432]` — which is the correct behaviour for a *resting
   limit* order in an opening auction, not a favour.
4. **Breakeven ordering.** `extreme_favourable` is updated from this bar's high/low at
   `engine.py:396-400`, i.e. *before* the stop check at `:402`. The breakeven move then
   happens at `:445-450`, **after**. So a bar cannot both make its excursion, move the stop
   to breakeven, and be stopped at that new breakeven in the same bar. Correct.
5. **Target re-projection.** Targets are recovered as R multiples from the signal's geometry
   and re-projected from the actual fill `[repo-verified: engine.py:369-370, 524-536]`, so a
   worse fill does not silently buy a nearer target.

6. **The higher-timeframe reads in the management loop are not look-ahead either.** The trail
   (`engine.py:451-462`) and the slippage scaler (`engine.py:334-342`) both index a
   higher-timeframe ATR column via `self.frame.tf_index(i, tf)`, which is the obvious place
   for a partially-formed higher bar to leak. It does not:
   `tf_index` returns the "*Index of the newest **completed** ``timeframe`` bar at
   ``base_index``*" `[repo-verified: futures_agents/features.py:921-926]`. I verified the
   contract from the docstring and signature only, not the construction of `self._align`,
   which is R1's surface under DIVISION §5; I am recording it as clean with that caveat
   stated rather than silently.

**So: on the five classic biases that live in a position-management loop — look-ahead fills,
repainting stops, optimistic tie-breaking, favourable gap handling and target
re-projection — this engine is clean.** The problems on my track are not correctness
problems. They are *coverage* problems: the vocabulary exists, is largely correct, and has
never been exercised.

## A-12 (NEW) The conviction score is a constant, so the only non-self-cancelling sizing channel has no input.

`ConditionResult` carries `strength: float = 1.0` described as "0-1, how emphatically the
condition fired" `[repo-verified: futures_agents/strategies/base.py:74]`, and
`ConditionResult.yes` defaults it to `1.0`
`[repo-verified: base.py:80-83]`. `Strategy.evaluate` averages it into
`StrategySignal.strength` `[repo-verified: base.py:686, 766]` and attaches it to every
`Evidence` as `weight` `[repo-verified: base.py:691]`.

**Four of the seventy-nine conditions ever set it. All four are in the `candlestick` group.
Three of those four are SIGNALs, so 50 of the 53 SIGNAL conditions return the default.**

`[measured: python3 -c "import inspect,re; from futures_agents.strategies.library import
CONDITIONS; graded=[n for n,c in sorted(CONDITIONS.items()) if
re.search('strength', inspect.getsource(c.fn).split('def ',1)[-1])]; print(len(graded),
graded)" → 4 ['candle_decisive_close', 'candle_engulfing', 'candle_reversal',
'inside_bar_compression'] — **this census is wrong, the true count is 5; see the CORRECTION
at the end of this file**]`
`[measured: grep -c "strength" futures_agents/strategies/library.py → 7, every occurrence
between library.py:1400 and :1460, i.e. inside the candlestick block]`

Consequences, in order of weight:

1. **`StrategySignal.strength` is exactly 1.0 for any strategy whose signals avoid the four
   graded candlestick SIGNALs** — and `x_confluence` already found candlesticks unevaluable, "4 of 5
   appear in under 20 floor-clearing strategies" `[repo-verified: DEFECTS.md:213]`. So in
   practice the conviction score is a constant across the whole ~2.98M-evaluation programme.
2. **Every `Evidence.weight` in this repo is 1.0**, which means the decision layer's
   evidence-weighting is weighting nothing.
3. **Conviction-weighted sizing — the one Channel-4b sizing scheme whose input looked like it
   already existed — has `Cov(strength, R) = 0` by construction.** See Part B-3(b)(1); I
   wrote that section claiming `Trade.strength` was the cheapest high-value build on my track,
   then measured this and corrected it in place rather than leaving the claim standing.
4. The missing primitive is therefore **not a field but a rewrite**: 49 of 53 SIGNAL
   conditions would have to report how emphatically they fired — how far past the band, how
   steep the slope, how far above average volume. The field to carry it already exists and the
   feature columns already hold the inputs `[repo-verified: features.py:221-286]`. Nobody
   filled it in.

This is the fifth item in this audit of the same shape — a capability that exists, is named,
and is never populated or never read. The pattern is the finding.

---

# Part B — Sizing as strategy, and the non-cancelling question

This is the part my brief asked me to pursue hard, so I am going to do it properly: first
establish where sizing lives in this repo, then derive — from first principles, not by
analogy — **which operating decisions can change expectancy and which can only reshape
variance**, and then say which of the non-cancelling ones this repo can and cannot reach.

## B-1 The architectural finding: sizing is not in the measured universe at all

**Nothing under `futures_agents/backtest/` imports anything from `futures_agents/risk/`, and
`AccountConfig` is never imported by the backtester.**

`[measured: grep -rn "risk" futures_agents/backtest/*.py | grep -i import → one hit,
`backtest/__init__.py:9: from .montecarlo import ... risk_of_ruin` — a local module name,
not the risk package]`
`[measured: grep -rn "AccountConfig" futures_agents/backtest/*.py → (empty)]`

`AccountConfig` carries **26 fields**, of which roughly nineteen are operating-layer
parameters — `base_risk_pct_of_buffer`, `max_risk_pct_of_equity`, `min_dollar_risk`,
`max_dollar_risk`, `daily_loss_limit`, `daily_soft_loss_limit`, `daily_profit_lockdown`,
`daily_giveback_pct`, `max_trades_per_day`, `max_consecutive_losses`,
`max_concurrent_positions`, `max_correlated_positions`, `derisk_ladder`,
`protected_buffer_pct`, `max/min_atr_multiple_of_median`, `min_reward_risk`,
`min_confidence`, `min_backtest_trades`, `min_expectancy_r`
`[repo-verified: futures_agents/config.py:355-400]`.

`[measured: python3 -c "<per-field reader census over futures_agents/**.py>" → 26 fields;
zero fields read anywhere under futures_agents/backtest/. The three apparent
backtest hits (starting_equity, trailing_drawdown, max_consecutive_losses) are plain
parameter names and a same-named attribute on `Metrics`, not AccountConfig reads —
confirmed by the AccountConfig import grep above.]`

So the answer to DIVISION §3's R3-D3 second question is unambiguous:
**`risk/manager.py` and `risk/account.py` serve the live proposal path only.** Their readers
are `ui/`, `orchestrator.py`, `bot.py`, `agents/` and `tests/`
`[measured: grep -rn "from.*risk\.(manager|account) import" → ui/state.py:36-37,
ui/api.py:35-36, agents/context.py:20-21, agents/decision.py:41, agents/risk_agent.py:44,
orchestrator.py:45-46, bot.py:36-37, tests/]`.

The consequence is stated plainly in the engine's own docstring
`[repo-verified: futures_agents/backtest/engine.py:22-25]`:

> The engine measures everything in R (multiples of the initial stop distance) with a
> notional one contract. Converting R into contracts is the risk layer's job, and keeping
> those separate is what lets the same research feed a $50,000 account and a $5,000 one
> without re-running anything.

That separation is a deliberate, defensible design choice **and it is also the reason this
repo has never tested sizing as strategy.** ~2,975,629 evaluations were all run at flat
one-notional-contract, one-position-at-a-time, no account state, no heat cap, no daily limit,
no de-risk ladder. Sizing is not "untested because nobody got round to it"; it is
*structurally outside the thing that was being tested*.

## B-2 The one sizing scheme that IS in the measured universe — and it is invisible

There is a sizing scheme baked into the unit of account, and because it is the unit it has
never been recognised as a scheme.

`ExitModel.stop_price` with `StopKind.ATR` sets `dist = stop_mult * atr`
`[repo-verified: futures_agents/strategies/base.py:284-288]`. One R is that distance. The
engine then reports every trade in R `[repo-verified: engine.py:484-495]`.

Therefore: **holding dollar risk constant per trade and reading results in R is exactly
ATR-normalised volatility-targeted sizing.** A trade in a high-ATR week gets a wider stop and
therefore fewer contracts for the same dollar risk; a trade in a quiet week gets more. That
is the definition of vol targeting `[general knowledge]`.

Two consequences, both findings:

1. **III-7's volatility-targeting sub-family is not inexpressible here. It is mandatory,
   universal, and therefore has no control arm.** Every result in `scan_reports/` is a
   vol-targeted result. The repo cannot compare vol-targeted against not-vol-targeted,
   because the alternative is not representable in its output.
2. **Constant-notional sizing — fixed contracts regardless of stop distance, which is what a
   very large share of retail futures traders actually do `[general knowledge]` — is the
   thing that is unreachable.** `Trade.net_dollars = net_r * risk_dollars`
   `[repo-verified: engine.py:507]`, i.e. dollars are *derived from* R by a per-trade scalar,
   so the two series are the same information. There is no per-contract points-P&L field on
   `Trade` `[measured: python3 -c "dataclasses.fields(Trade)" → 38 fields, none of them a
   points-per-contract P&L; `mfe_points`/`mae_points` are excursions, and `exit_price` is only
   the FINAL leg of a scale-out]`. **Named missing primitive: `Trade.points_pnl`** (or,
   equivalently, a `sum(leg.fraction * (leg.price - entry) * sign)` aggregate). It is
   reconstructible from `Trade.legs` `[repo-verified: engine.py:92, 60-72]`, so this is
   PARTIAL, not INEXPRESSIBLE — but no report in this repo has ever computed it, and until
   one does, "R" and "dollars" are one axis and constant-notional sizing has no home.

## B-3 The decomposition: four channels, and only two of them can move expectancy

Any operating decision reaches the realised outcome through exactly one of four channels.
I am writing them down because the win-rate/payoff cancellation the manager warned me about
is **Channel 1 only**, and conflating the four is what makes the operating layer feel like it
always cancels.

Let `R_i` be the net R of trade *i*, `w_i` the risk weight applied to it, `N` the number of
trades, `c` the per-trade cost expressed in R.

| # | channel | formal object it moves | can it move per-trade expectancy? |
|---|---|---|---|
| **1** | **Geometry at a fixed trade population** — where the stop and target sit | the *shape* of the distribution of `R_i` at fixed `i` set | **No.** Win rate and payoff are two parameterisations of one surface. `[settled: BRIEF.md rule 3, measured 4×]` |
| **2** | **Trade population** — *which* bars become trades | the index set `{i}` itself | **Yes, directly.** `E[R]` is a conditional expectation; change the conditioning set and it changes. |
| **3** | **Cost per unit of risk** — `c` | a deterministic subtraction from every `R_i` | **Yes, monotonically.** `c` is not a random variable; reducing it raises `E[R]` by exactly that amount. |
| **4** | **The weighting map** — `R_i → w_i R_i` and its compounding | terminal wealth `W_T` | **Only if `Cov(w, R) ≠ 0`.** Otherwise `E[wR] = E[w]E[R]`: sign-preserving, variance-only. |

### Channel 1 — self-cancelling. Labelled once, per DIVISION §5.9.

Stop width, stop kind, target ladder shape, `stop_pad_ticks`, R-multiple vs anchored target,
breakeven trigger, number of targets, scale-out fractions. All of these move the R
distribution's shape at a fixed trade population. `BRIEF.md` rule 3 and the `x_exits` verdict
`[repo-verified: workspace/studies/DEFECTS.md:210 verdict log round 2 — "Anchored targets
raise payoff (z=−13.83) but **not** expectancy"]` are the same statement.
**CANCELLING — settled. Not re-derived here.**

### Channel 3 — the residual Channel 1 leaves on the table, and it does NOT cancel.

This is the one place where I can sharpen a settled rule without contradicting it, so I want
to be careful about what I am and am not claiming.

The engine computes cost in R as `[repo-verified: futures_agents/backtest/engine.py:492-495]`:

```
commission   = 2.0 * self.costs.commission_per_side()
risk_dollars = pos.risk_points * spec.point_value
cost_r       = commission / risk_dollars
net_r        = gross_r - cost_r
```

`cost_r` is **inversely proportional to the stop distance**, exactly. So a wider stop does buy
one thing that does not cancel: a smaller cost in R. The repo has already measured the
magnitude — all-in cost is **15.0% of one R at 5m, 4.6% at 60m, 1.2% at daily**
`[repo-verified: workspace/studies/DEFECTS.md:209 verdict log round 2, `x_costs`]`.

What I am claiming: `BRIEF.md` rule 3 is a statement about **gross** geometry, and it is
correct. Channel 3 is a second, *monotone, non-cancelling* effect of the same knob, of
order 0.15R at 5 minutes. It is not an additional edge — it is a drag that shrinks as the
risk unit widens. **This is why `BRIEF.md` rule 4 ("never tighter than ~0.5 ATR") and rule 7
("sub-hourly is a graveyard") are the same inequality**, and it is the correct reading of why
the cancellation is a cancellation *gross* and a mild preference for width *net*.

What I am NOT claiming: that widening the stop is an edge. It is not. It buys back cost, and
the cost it buys back is bounded above by `c`, which is 1.2% of R on a daily bar. There is no
free lunch here, only an explanation of an asymmetry the repo already measured.

**Three further Channel-3 items, all non-cancelling and all under-modelled:**

- **Trade count.** Total cost paid is `N × c`. Any rule that reduces `N` reduces total cost
  linearly *without* changing per-trade `E[R]`. So "do less" is a P&L transform and not an
  expectancy transform — a distinction the repo's per-trade ranking metric structurally
  cannot see. `x_confluence`'s result (2→4 signals cuts count 65→42 and does not move
  expectancy `[repo-verified: DEFECTS.md:212 verdict log round 2]`) is exactly this: the
  count moved, the per-trade number did not, and the ranking metric read that as "no
  effect".
- **Exit-type cost asymmetry, unmodelled.** See A-7: TIME, SESSION_CLOSE and END_OF_DATA
  exits pay zero slippage. So any operating rule whose effect is to *change the mix of exit
  reasons* is measured on a cost model that charges the mix unevenly. Time stops and
  session-close flattening — the two axes the manager pre-registered as the likely real
  expectancy changers (DIVISION §6) — are precisely the two that are charged nothing.
- **Size-dependent slippage, absent entirely.** `SlippageModel` has five fields
  `[repo-verified: costs.py:29-33]`: `base_ticks`, `stop_order_extra_ticks`,
  `volatility_coefficient`, `thin_book_extra_ticks`, `news_extra_ticks`. **None of them is a
  function of order size.** `round_turn_dollars` multiplies slippage by `contracts` linearly
  `[repo-verified: costs.py:104-110]` and `cost_in_r` divides `risk_dollars` by `contracts`
  linearly `[repo-verified: costs.py:119-122]` — so in this model **cost in R is exactly
  size-invariant**. Market impact is the one channel through which sizing genuinely degrades
  expectancy at scale `[general knowledge]`, and it is structurally absent. **Named missing
  primitive: `SlippageModel.impact_ticks_per_contract` (or an ADV-relative participation
  term).** Without it, no sizing study in this repo can ever find a capacity limit.

### Channel 4 — sizing. Where the real answer is, and it has three parts.

Write the dollar outcome of trade *i* as `w_i × R_i × D` for a risk unit `D`.

**Part (a) — independent weights are a variance transform and nothing else.**
If `w_i` is measurable with respect to information available before trade *i* and is
uncorrelated with `R_i`, then `E[w R] = E[w] E[R] + Cov(w,R) = E[w] E[R]`. The sign of
expectancy is preserved and the per-unit-risk expectancy is *unchanged*. Fixed-fractional,
fixed-ratio, Kelly, fractional Kelly, risk parity and volatility targeting are all of this
form `[general knowledge]`. What they change is the path: terminal wealth is multiplicative,
`W_T = W_0 Π(1 + f R_i)`, and `E[log(1 + f R)]` is **concave in `f`** — so there is a unique
growth-optimal `f*`, over-betting is punished far harder than under-betting, and for
`E[R] ≤ 0` the optimum is `f* ≤ 0` `[general knowledge]`.

**That last clause is the load-bearing one for this repository, and it is a negative result I
am obliged to report rather than soften.** This repo's settled verdict is that no strategy
anywhere clears its own multiple-testing threshold and that `E[R]` is negative essentially
everywhere measured (`BRIEF.md` §"What the research already established"; `x_costs`: "Every
other cell is negative **gross**" `[repo-verified: DEFECTS.md:209]`). A concave transform of
a non-positive input has a non-positive optimum. **No sizing scheme in category (a) can
convert this repo's measured R series into growth.** Sizing-as-strategy, in its classical
form, has nothing here to work with. That is the honest answer and I am not going to
manufacture a positive around it.

**Part (b) — dependent weights (`Cov(w,R) ≠ 0`) are NOT a variance transform, and this is
the genuine asymmetry.** If the weight correlates with the trade's own conditional
expectancy, `E[wR] = E[w]E[R] + Cov(w,R)`, and the covariance term survives even when
`E[R] = 0`. This is the only sizing that is strategy rather than admin, and it is *the same
object as meta-labelling* (III-17) with a continuous output instead of a binary one. Three
sub-cases are real and each has a different verdict here:

1. **Conviction sizing** — `w ∝` a per-signal score. **The input already exists and is
   thrown away.** `Strategy.evaluate` computes `strength = strength_sum / n_signals` from the
   mean of its signal conditions' strengths and puts it on the signal
   `[repo-verified: futures_agents/strategies/base.py:686, 766; field at base.py:515]`. The
   engine **never reads it** `[measured: grep -n "strength" futures_agents/backtest/engine.py
   → no match]` and `Trade` **has no strength field**
   `[measured: python3 -c "dataclasses.fields(Trade)" → 38 fields; `strength` is in the
   set-difference of StrategySignal-minus-Trade fields, along with `evidence`, `invalidation`,
   `bar_index`, `entry`, `stop`, `timeframes`, `ts`]`. So the repo computes a conviction
   score on every one of ~2.98M evaluations, and discards it at `engine.py:498-517`.
   **Named missing primitive: `Trade.strength` — one field, one assignment.**

   **SELF-CORRECTION, and it is the more interesting result.** I wrote the above, then checked
   whether the score actually varies — and it barely does. **Only 5 of the 79 conditions ever
   grade their own strength, all five in the `candlestick` group, and only 4 of those are
   SIGNALs. 49 of the 53 SIGNAL conditions return `ConditionResult.yes(...)` with the default
   `strength=1.0`, and ~74 of 79 return it overall** `[repo-verified: base.py:80-83 — the default; base.py:74 — the field
   default]`
   `[measured: python3 -c "import inspect,re; from futures_agents.strategies.library import
   CONDITIONS; graded=[n for n,c in sorted(CONDITIONS.items()) if re.search('strength',
   inspect.getsource(c.fn).split('def ',1)[-1])]; print(len(graded), graded)"
   → 5 ['candle_close_strength', 'candle_decisive_close', 'candle_engulfing',
   'candle_reversal', 'inside_bar_compression']; 49 of 53 SIGNAL conditions ungraded — this
   census first returned 4; see the CORRECTION at the end of this file]`
   `[measured: grep -c "strength" futures_agents/strategies/library.py → 7 lines, all at
   library.py:1400-1460, all in the candlestick block; the 5th graded condition passes its
   grade positionally and so does not appear in that grep]`

   Since `strength = strength_sum / n_signals` `[repo-verified: base.py:766]` and
   `strength_sum` adds `max(0.0, min(1.0, res.strength))` per signal
   `[repo-verified: base.py:686]`, **`StrategySignal.strength` is exactly 1.0 for any strategy
   whose signals are all drawn from the other 50** — which is nearly all of them, and the
   three that would vary are the candlesticks `x_confluence` already found unevaluable
   ("4 of 5 appear in under 20 floor-clearing strategies")
   `[repo-verified: workspace/studies/DEFECTS.md:213]`. The same applies to
   `Evidence(..., weight=res.strength)` `[repo-verified: base.py:691]`: every evidence weight
   in this repo is 1.0.

   **So `Trade.strength` is still worth 2 lines, but for diagnosis rather than for sizing:
   it would record a constant, and recording a constant is how you *prove* the conviction
   channel is empty rather than assuming it.** The real missing primitive for conviction
   sizing is one layer deeper and much more expensive: **49 of 53 SIGNAL conditions would have
   to be rewritten to grade their own firing** (how far past the band, how steep the slope, how
   far above the average volume) — the information exists in the feature columns, the
   `ConditionResult.strength` field exists to carry it, and nobody filled it in. Channel 4b's
   conviction sub-case is therefore **not one field away. It is fifty conditions away.**
   I am reporting this as an absence rather than leaving my first paragraph standing.
2. **Equity-curve / streak sizing** (III-14) — `w` a function of recent realised outcomes.
   `Cov(w,R) ≠ 0` **iff the R series is serially dependent**. This is therefore not a matter
   of opinion but a measurable property of a series the repo already has. And the repo's own
   risk machinery has *pre-committed to the answer without measuring it*: `monte_carlo`
   defaults to `mode="iid"`, which "deliberately breaks any serial dependence"
   `[repo-verified: futures_agents/backtest/montecarlo.py:13-15, 84-110]`; a `mode="block"`
   path exists explicitly "where a strategy's edge genuinely depends on streaks"
   `[repo-verified: montecarlo.py:14-15, 96-103]`; and **`risk_of_ruin` — the one consumer
   that a sizing decision would actually use — has no `mode` parameter at all and calls
   `monte_carlo` without one** `[repo-verified: montecarlo.py:209-219, 227-231]`.
   `[measured: grep -rn 'mode="block"' --include=*.py . → the docstring at montecarlo.py:91
   only; no call site anywhere]`. **So every risk-of-ruin number this repo has ever produced
   assumes zero autocorrelation in the R series, and the tool built to test that assumption
   is unreachable from the function that depends on it.**
3. **Regime-conditional sizing** — `w` a function of a measured per-regime expectancy.
   `Cov(w,R) ≠ 0` by construction, so it is formally in category (b). But it is also
   *exactly* the operation this repo has measured as harmful: trading last period's top 10
   returns −0.0155R against a −0.0104R null and underperforms trading the whole qualifying
   universe (`BRIEF.md` §"What the research already established"). **A regime-conditional
   sizing rule is a selection rule, and selection has a measured prior against it here.** I
   am not re-litigating that finding; I am pointing out that it transfers to sizing, which is
   a claim nobody in this repo has previously connected.

**Part (c) — the integer-contract floor makes sizing a Channel-2 operation, not a Channel-4
one. This is the strongest non-cancelling result I have.**

`RiskManager.contracts_for` returns
`int(math.floor(budget / (proposal.risk_points * spec.point_value)))`
`[repo-verified: futures_agents/risk/manager.py:197-203]`, and never rounds up — there is a
regression test asserting exactly that `[repo-verified: tests/test_risk.py:150-157,
"test_contracts_for_never_rounds_up"]`.

When `risk_points × point_value > budget`, that expression returns **0 contracts, i.e. no
trade.** So at any finite account size, sizing does not merely *weight* trades — it
**deletes** them, and it deletes them selected on stop distance, which under `StopKind.ATR`
means selected on **volatility**. Integer sizing at micro-account size is an unintended
volatility-regime entry filter. That is Channel 2, and Channel 2 moves expectancy.

Concretely, with the shipped account config — `max_risk_pct_of_equity = 0.0075` on $50,000 is
a $375 ceiling, `max_dollar_risk = 500` `[repo-verified: config.py:361-364]` — the largest
stop that yields even one contract is:

| symbol | `point_value` | max stop at $375 | max stop at $500 |
|---|---|---|---|
| MNQ | 2.0 | 187.5 pts | 250 pts |
| MES | 5.0 | 75 pts | 100 pts |
| MGC | 10.0 | 37.5 pts | 50 pts |
| MCL | 100.0 | 3.75 pts | 5 pts |

`[measured: python3 -c "from futures_agents.config import get_contract; ..." → MNQ
point_value=2.0 min_stop_ticks=16; MES 5.0/8; MGC 10.0/25; MCL 100.0/15]`

Now cross that with the repo's own measured MNQ stop distances: "the stop fell from **179
points** to 35" between a 240m and a 5m entry
`[repo-verified: futures_agents/strategies/combinator.py:87-89]`, which is a 1.0×ATR stop at
240m. The catalogue's second exit is `ATRx2.5` `[repo-verified: combinator.py:58-59]` — i.e.
roughly 2.5 × 179 ≈ 450 points on MNQ at 240m, or about **$900 of risk on one micro
contract.** Against a $375–$500 budget that is **zero contracts.**

**So catalogue exit index 1 (`ATRx2.5->1/2R`) is untradeable on MNQ at 4h at the account size
this repo models, and every backtest in `scan_reports/` reports its trades anyway.** Combine
with A-8 (a `(0.5,0.3,0.2)` scale-out ladder needs ten contracts to express without rounding,
and the budget above permits one) and the picture is consistent:

> **The R-space backtest describes a portfolio that no account of the modelled size could
> have traded.** Not because of a bug — because of a boundary. `engine.py:22-25` states the
> boundary as a virtue, and for comparing *signals* it is one. For evaluating the *operating
> layer* it is fatal, because the operating layer is where integer constraints, heat caps
> and daily limits live.

## B-4 `run_portfolio` does not simulate a portfolio

`run_portfolio` `[repo-verified: engine.py:554-559]` delegates to `run_many`, whose own
docstring says `[repo-verified: engine.py:262-267]`:

> Backtest many strategies in a single pass over the data. All strategies share one per-bar
> condition cache … **Each strategy still keeps completely independent position state.**

There is no netting of exposure, no shared account, no correlation grouping, no total-risk
cap. `AccountConfig.max_concurrent_positions = 2` and `max_correlated_positions = 1`
`[repo-verified: config.py:373-374]` are enforced only at `risk/manager.py:249-252`, on the
live path. **`run_portfolio` is a batch runner, not a portfolio simulator, and its name is
the single most misleading identifier on my track.**

**Named missing primitive:** `BacktestEngine` has no shared-state parameter — concretely,
there is no `account: AccountState` argument on `__init__`
`[repo-verified: engine.py:231-242]` and no per-bar aggregate of open risk keyed by
`correlation_group` inside `run_many` `[repo-verified: engine.py:282-283 — the only shared
dicts are `open_pos` and `pending`, both keyed by `strategy_id`]`. That one parameter plus a
`Dict[str, float]` of open risk by correlation group is what portfolio heat (III-14),
correlated-exposure limits and daily loss limits all need. It is the same primitive for all
three.

## B-5 Verdict table: which operating decisions are NOT self-cancelling

| operating decision | channel | self-cancelling? | reachable here? |
|---|---|---|---|
| Stop width / kind | 1 | **Yes** — settled, BRIEF r3 | yes, and measured to death |
| Target ladder shape, count, R vs anchored | 1 | **Yes** — settled | yes; but see D15 (no paired control) and D19 (confounded) |
| Breakeven trigger | 1 | **Yes** | yes, varied {1.0,1.5,2.0,None} |
| Scale-out fractions | 1 (+3 via D13) | mostly yes | yes, but always sum 1.0 (never a runner) |
| **Cost per R via the risk unit** | **3** | **No** — monotone | yes, already measured (`x_costs`) |
| **Trade-count reduction** | **3** | **No** — but it is a P&L transform, not an expectancy one | yes; invisible to the per-trade ranking metric |
| **Exit-reason mix (time / session-close)** | **3** | **No** | yes, but charged zero slippage (A-7) |
| **Market impact / capacity** | 3 | **No** | **NO** — `SlippageModel` has no size term |
| Fixed-fractional / Kelly / vol targeting | 4a | **variance only** (`Cov=0`) | vol targeting is mandatory & uncontrolled (B-2); the rest are outside the engine |
| **Conviction-weighted sizing** | **4b** | **No** | **PARTIAL** — input computed, discarded; needs `Trade.strength` |
| **Equity-curve / streak sizing** | **4b** | **No** — depends on R autocorrelation | **replayable from stored artefacts today** |
| Regime-conditional sizing | 4b | **No**, but measured prior against it (selection) | replayable; expect it to lose |
| **Integer-contract floor** | **2** | **No** — deletes trades on a volatility criterion | **NO** — engine never calls `contracts_for` |
| **Portfolio heat / correlated exposure** | **2** | **No** — forces selection | **NO** — no shared account in `run_many` |
| **Daily loss limit / max trades per day** | **2** | **No** — deletes trades path-dependently | **replayable from stored artefacts today** |
| **Re-entry policy after a stop** | **2** | **No** — changes the population | **NO** — no cooldown field anywhere |
| Pyramiding / unit adds | 1 and 2 | no (changes both) | **NO** — `engine.py:304-309` |
| Time stop magnitude | 1 and 2 | partly | yes, varied {30..120}; **never switched off** |
| Session-close flattening | 2 and 3 | **No** | yes, but D19: exact alias for anchored targets |
| Trailing stop | 1 | yes in shape | **never run at all** (A-1) |
| Directional restriction (long-only) | 2 | **No** | **NO** — all 13 templates are `(LONG, SHORT)` |

**Summary of the asymmetry the manager asked me to chase:** the non-self-cancelling operating
decisions are *not* the sizing schemes in the textbook sense. Category (4a) — every scheme
with a name, Kelly included — is a variance transform, and against a non-positive `E[R]` it
is a variance transform with a non-positive optimum. **The non-cancelling decisions are the
ones that change the trade population (Channel 2) or the cost per R (Channel 3).** Sizing
enters that set through exactly one door, and it is a door nobody expects: **the integer
floor**, which turns a weighting rule into an entry filter. Everything else about sizing in
this repo is admin, and the repo was right to treat it that way — but for a reason it has
never written down.

---

# Part C — R3-D1: the Class III family catalogue

Nineteen entries under the DIVISION §4 schema, split as DIVISION §3 requires into **entry
families (III-1 … III-6)** and **operating layers (III-7 … III-19)**. Two structural facts
apply to every entry below and are stated once here rather than nineteen times:

- **`Condition` has no parameter field.** `[measured: python3 -c
  "dataclasses.fields(Condition)" → ['name','group','fn','kind','description','timeframe',
  'warmup_bars']]`. Every lookback and threshold in all 79 conditions is a hard-coded constant
  inside a closure `[repo-verified: futures_agents/strategies/base.py:90-102]`. So "a 20-day
  vs a 55-day channel", "RSI(9) vs RSI(14)", "2σ vs 2.5σ" are **not expressible as
  variations** — only as new conditions. This is simultaneously a genuine anti-overfitting
  virtue (no entry-parameter grid to mine) and a genuine anti-overfitting failure (the
  parameter-sensitivity check that practice demands cannot be run on entries).
- **The management loop is blind to indicators.** `_manage(self, pos, i, bar, *, is_last)`
  receives a `Bar`, never a `FeatureSnapshot` `[repo-verified: engine.py:377-378]`; the
  snapshot is constructed only at `engine.py:310-311`, after management, and only for flat
  strategies. So no family below can have a condition-based exit. See
  `R3_operating_vocabulary.md` M6.

## III-1 Time-series momentum / CTA trend following

**Mechanism.** Futures prices exhibit positive serial dependence over horizons of roughly
1–12 months, so a rule that is long what has gone up and short what has gone down harvests
that autocorrelation; the payoff shape is a long-option profile — many small losses, a few
very large wins `[general knowledge]`.
**Who runs it, at what size.** The core of the managed-futures industry: AHL, Winton, Aspect,
Transtrend, Chesapeake, Millburn; $100m to $20bn+ AUM, and it is what "CTA" means to an
allocator. Also the single most-replicated academic futures result `[general knowledge]`.
**Where it lives.** 30–100 liquid futures across all sectors, **daily bars**, 20–300 day
lookbacks, holding weeks to months, no session concept at all `[general knowledge]`.
**Minimum data.** Daily settlement prices on a *properly back-adjusted continuous* series,
across a diversified universe, with 20+ years of history. Specifically: a roll-adjusted price
series and a contract-month label to build it from.
**How it is operated.** Entry: price makes a new N-day high (Donchian/Turtle), or a fast MA
crosses a slow MA, or 12-month total return is positive. Invalidation: the opposite
condition — **the exit *is* the inverse of the entry**, and the canonical form is
always-in-the-market stop-and-reverse. Sizing: ATR/volatility-normalised, target a constant
risk per instrument (the Turtle "N" unit). Typical hold: 1–6 months. Reported shape: **win
rate 30–40%, payoff 2.5–4:1, annual Sharpe 0.3–0.6 for a single-market system, 0.7–1.0 for a
diversified portfolio, max drawdown 20–40%, and long flat periods of 2–3 years**
`[general knowledge]`.
**How it dies.** Choppy, range-bound, mean-reverting regimes; whipsaw at turning points; and
crowding — the 2011–2019 CTA drawdown is the reference case. Falling realised volatility
compresses the ATR unit and forces size up into a reversal `[general knowledge]`.
**Expressibility here.** **PARTIAL, badly degraded.** Three separate cuts:
  1. *The entry does not exist.* There is **no channel-breakout condition** among the 79.
     `[measured: python3 -c "from futures_agents.strategies.library import CONDITIONS;
     print([n for n in CONDITIONS if 'break' in n])" → ['break_of_structure',
     'initial_balance_break', 'opening_range_breakout', 'prior_day_breakout',
     'value_area_breakout'] — all swing-based, session-based or level-based; none is an
     N-bar high]`. And the input is **already computed and unused**: `C["hh20"] =
     rolling_max(h, 20)`, `C["ll20"] = rolling_min(l, 20)`
     `[repo-verified: futures_agents/features.py:265-266]`, whitelisted at
     `[repo-verified: features.py:62]`, and read by **no condition** —
     `[measured: grep -rn "hh20\|ll20" --include=*.py . → features.py:62,265,266,269 and
     agents/analysts.py:1068 (narrative only); zero hits in strategies/library.py]`.
  2. *The exit does not exist.* Stop-and-reverse is impossible: `engine.py:304-309`.
  3. *The universe does not exist.* A diversified 30-market portfolio needs a multi-symbol
     frame; `engine.py:548` and `:554` each take one `frame: SymbolFrame` — that is R2's
     finding and I cite it rather than re-derive it. And only three futures symbols have a
     daily file at all `[repo-verified: DIVISION Appendix B.4]`.
  What survives is a single-symbol MA-crossover long/short with a geometric exit — which is
  what `ema_fast_above_slow` + `ema_stack` already is. **Named missing primitive for the
  canonical form: a `donchian_breakout` condition reading the existing `hh20`/`ll20`
  columns** (≈12 lines, no new data), plus `ExitModel.exit_conditions`.
**Already tested here?** The degraded form, yes: the TREND template is
`required_groups=("trend","structure")` `[repo-verified: combinator.py:167-170]` and
`x_conditions` found `ema_stack` the **single survivor** of 34 tests under
Benjamini-Hochberg (+0.028R vs −0.006R, Stouffer z=+3.10 over 7 cells)
`[repo-verified: workspace/studies/DEFECTS.md:211]`. The canonical Donchian form: **No.**

## III-2 Volatility breakout systems

**Mechanism.** Volatility clusters, so a contraction is followed by an expansion; entering on
the break of a compressed range captures the expansion leg `[general knowledge]`.
**Who runs it.** Retail systematic and small CTAs (Turtle derivatives, Crabel-style ORB,
Bollinger squeeze, NR7); prop desks for intraday variants. $10k to $50m `[general knowledge]`.
**Where it lives.** All liquid futures; daily for NR7/inside-day, intraday for squeeze and
range expansion `[general knowledge]`.
**Minimum data.** OHLC on one series. **This family's data requirement is genuinely met here.**
**How it is operated.** Entry: buy-stop above and sell-stop below a compressed range
(NR7, inside day, low Bollinger bandwidth, Keltner squeeze), often as an OCO bracket. Stop: the
other side of the range, or a fraction of the range. Target: a multiple of the range
("measured move"), or trail. Sizing: range-normalised. Hold: 1–10 bars. Reported shape:
**win rate 40–50%, payoff 1.5–2.5:1** `[general knowledge]`.
**How it dies.** False breaks in a persistent range; a compressed range that expands the other
way first (the classic double-stop); and, at intraday scale, costs — this is the highest-
turnover Class III family.
**Expressibility here.** **PARTIAL.** The *state* conditions exist:
`volatility_compressed`, `volatility_expanding`, `inside_bar_compression`, `keltner_outside`
`[repo-verified: DIVISION Appendix A]`, and BREAKOUT's `base_filters` is
`('volatility_compressed', 'volume_not_thin')` with `volatility_expanding` as an optional
filter `[measured: python3 -c "for t in TEMPLATES: print(t.group, t.base_filters,
t.optional_filters)" → BREAKOUT base=('volatility_compressed','volume_not_thin')
optional=('outside_news_blackout','no_imminent_release','volatility_expanding',
'volume_surge','oi_expanding')]`. What is lost: (a) the **OCO stop-entry bracket** — E1,
there is no order-type object, so the entry is a market fill at the next open rather than a
resting stop at the range edge, which is a materially different trade; (b) the **measured-move
target** — `TargetKind` has no range-derived kind, only R multiples and the two anchors
`[repo-verified: base.py:165-184]`; `StopKind.RANGE` exists for the *stop* but has no target
twin.
**Already tested here?** Yes, BREAKOUT is one of the 13 groups. Note D26: "BREAKOUT's volume
requirement silently disappears" `[repo-verified: DEFECTS.md:326-333]`. Not re-litigated.

## III-3 Volatility-regime-conditioned entry

**Mechanism.** The same signal has different expectancy in expansion and contraction regimes,
so conditioning on the regime raises the conditional expectancy `[general knowledge]`.
**Who runs it.** Nearly universal as an overlay rather than a standalone system; every
systematic desk has a vol filter `[general knowledge]`.
**Where it lives.** Any instrument, any timeframe; the regime is usually read on a higher
timeframe than the entry `[general knowledge]`.
**Minimum data.** ATR or realised-vol history long enough to percentile-rank the current
reading — concretely, several hundred bars.
**How it is operated.** Compute realised vol or ATR, percentile it against 1–2 years,
label {compressed, normal, expanding, extreme}, then enable/disable or resize. The operating
subtlety `[general knowledge]`: vol *regime* and vol *direction* are different variables, and
most desks gate on the level while sizing on the change.
**How it dies.** The regime label lags the regime. And the classifier's warm-up silently
mislabels.
**Expressibility here.** **EXPRESSIBLE, and this is the best-supported Class III family.**
`volatility_normal/expanding/compressed` are FILTERs, `C["atr_percentile"] =
self._percentile_of(a, 250)` exists `[repo-verified: features.py:246]`, and `StrategyFilters`
has a dedicated `volatility: Optional[FrozenSet[str]]` scope field
`[repo-verified: base.py:391]`. **But the scope field is never used** (A-5), and
`RegimeSnapshot()` defaults volatility to `NORMAL` when the classifier has no history, so
`volatility_normal` silently *passes* rather than reporting itself inert
`[repo-verified: DEFECTS.md:188-194 (D16)]`.
**Already tested here?** Yes. `x_regime`: "Not a usable knob… `volatility_normal` earns its
place overall (z=+9.64 over 2,571 pairs) but is symbol-specific — MGC 60m detectably negative
(z=−6.30)" `[repo-verified: DEFECTS.md:214]`. And M3: five of six regime/vol conditions are
template BASE filters present in 100% of their group, with an empty control arm in all 15
cells `[repo-verified: DEFECTS.md:196-201]`.

## III-4 Mean reversion to a band or anchor on one series

**Mechanism.** Short-horizon overextension from a reference (a moving average, a band, VWAP,
a z-score) reverts because liquidity providers are compensated for absorbing the impulse
`[general knowledge]`.
**Who runs it.** Prop intraday desks and retail; the payoff shape is the mirror of trend —
high win rate, small wins, occasional large loss `[general knowledge]`.
**Where it lives.** Index futures above all (ES/NQ mean-revert intraday more than commodities);
1m–60m; strongly session-dependent `[general knowledge]`.
**Minimum data.** OHLC plus volume for VWAP. **Met here.**
**How it is operated.** Entry: close outside a 2σ Bollinger or Keltner band, or |z| > 2 from
an anchor, ideally *into* a level and *against* a failing impulse. Invalidation: a
*second* extension in the same direction — the regime was trend, not range. Exit: the mean
itself (band mid / VWAP), usually a single target, no runner. Sizing: often scaled-in (adds
at deeper extensions), which is why this family and III-8 are linked in practice.
Reported shape: **win rate 60–75%, payoff 0.5–0.9:1, and a left tail that eats a year**
`[general knowledge]`.
**How it dies.** Trend. One un-stopped extension pays for fifty winners. Scaling in converts
that from a loss into a blow-up.
**Expressibility here.** **PARTIAL.** Entries exist: `bollinger_extreme`,
`bollinger_mean_pull`, `keltner_outside` `[repo-verified: DIVISION Appendix A]`, plus
`MEAN_REVERSION` with `base_filters=('volatility_normal','volume_not_thin','regime_ranging')`
`[measured: see III-2 command]`. Two losses: (a) **the target cannot be the mean.** There is
no `TargetKind.ANCHOR_VWAP` or band-mid target; the anchors are ATR and structure only
`[repo-verified: base.py:182-184]`. Exiting a band-reversion trade at 1R instead of at the
mean is a different strategy. (b) **scaling in is impossible** (M8). A continuous z-score
threshold is also not tunable (`Condition` has no parameters).
**Already tested here?** Yes, MEAN_REVERSION is one of the 13 groups; `g_mean_reversion`
produced D8–D10 `[repo-verified: DEFECTS.md:102-135]`.

## III-5 Pattern and sequence strategies

**Mechanism.** A specified *ordered* sequence of events (setup → trigger → confirmation)
identifies a context that a single-bar condition cannot `[general knowledge]`.
**Who runs it.** Discretionary and semi-systematic retail; the entire price-action and ICT
teaching industry; some prop desks as a checklist rather than a system
`[general knowledge]`.
**Where it lives.** 1m–4h, session-anchored `[general knowledge]`.
**Minimum data.** OHLC plus **ordered event memory across bars**.
**How it is operated.** Wait for A, then require B within N bars of A, then enter on C.
Invalidation is usually "the sequence broke", not a price level. Hold: intraday.
**How it dies.** The sequence is almost always assignable only in hindsight, and its
components are individually weak; conjoining three weak conditions with an ordering
constraint produces a rare event with a tiny sample.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE.** D37 is explicit: "the combinator
cannot express a sequence at all" `[repo-verified: DEFECTS.md:541-548]`. The structural
reason, in my own words and cited: `Strategy.evaluate` conjoins conditions **at one bar** —
every signal is evaluated against the same `snap` and all must agree *simultaneously*
`[repo-verified: base.py:670-695]`. There is no "within N bars of" operator and no
cross-bar state on `Strategy`. **Named missing primitive: `Condition` has no
`lookback_window` and `Strategy` has no ordered `stages: Tuple[Tuple[Condition, ...], ...]`
with a `max_bars_between`.** See R3-D6 below.
**Already tested here?** Yes, and settled negative: `BRIEF.md` rule 8 — the ICT
sweep→shift→retrace sequence "is real, common, and adds nothing over its parts"
`[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md]`.

## III-6 Opening range / initial balance systems

**Mechanism.** The first N minutes establish a reference; trading its break captures the
day's directional resolution, and trading its failure captures rotation `[general knowledge]`.
**Who runs it.** Retail and small prop, overwhelmingly on index futures; Crabel's ORB is the
documented origin `[general knowledge]`.
**Where it lives.** ES/NQ/CL, 1m–15m, first 30–120 minutes of RTH `[general knowledge]`.
**Minimum data.** Intraday bars with a **correct session boundary** and a cash-open
convention.
**How it is operated.** Define the range over the first 15/30/60 minutes; place OCO stop
orders at both edges; stop at the opposite edge or a fraction of the range; target a multiple
of the range; flatten at the close. Reported shape: **win rate 40–50%, payoff 1.2–2:1**
`[general knowledge]`.
**How it dies.** Wide opening ranges give a stop too far away to pay; narrow ones give
false breaks. Gap days invert the logic.
**Expressibility here.** **PARTIAL and heavily defect-laden.** The conditions exist
(`opening_range_breakout`, `opening_range_fade`, `initial_balance_break`,
`after_opening_range`, `opening_drive_window`) and `StopKind.RANGE` exists
`[repo-verified: base.py:192, 301-309]`. But: D30 — the opening range is never constructed at
60m or 240m `[repo-verified: DEFECTS.md:423-450]`; D39 — library ORB "is a state, not an
event, and silently widens" `[repo-verified: DEFECTS.md:557-582]`; D20 — daily
OPENING_RANGE is legitimately inapplicable `[repo-verified: DEFECTS.md:243-250]`. And the OCO
stop-entry bracket is unavailable (E1).
**Already tested here?** Yes, and settled negative: `BRIEF.md` rule 8 — "Yesterday's opening
range beats today's" `[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md]`.

---

## Operating layers III-7 … III-19

For these, "Mechanism" means *what the claim for this layer is*, and the critical field is
**"Expressibility here"** plus my Channel label from Part B-3.

## III-7 Position sizing as strategy

**Mechanism.** Sizing does not change the sign of an edge; it chooses a point on the
growth-versus-ruin curve, and choosing badly destroys a real edge `[general knowledge]`.
**Who runs it, at what size.** Everybody, and the sophistication scales with capital:
retail uses fixed-fractional; CTAs use volatility targeting to a portfolio vol number;
options and stat-arb desks use fractional Kelly and risk parity `[general knowledge]`.
**Where it lives.** Instrument-agnostic; the decision horizon is the account, not the bar.
**Minimum data.** Account equity, the peak equity, the per-trade risk in currency, a
contract multiplier, and — for anything Kelly-like — a *trustworthy* estimate of `E[R]` and
its variance, which is the binding constraint in practice.
**How it is operated.** Fixed fractional: risk f% of equity, so size compounds. Fixed ratio
(Jones): add a unit per fixed increment of profit, so size grows in the square root of
equity. Volatility targeting: set contracts so that `contracts × ATR × point_value` equals a
constant dollar figure; re-size as vol changes. Fractional Kelly: `f* = E[R]/E[R²]`-ish, then
take a quarter to a half of it because the estimate is noisy. Risk parity: equal risk
contribution per market. Typical: **0.25–1% of equity per trade for a discretionary book,
0.1–0.3% per market for a diversified CTA** `[general knowledge]`.
**How it dies.** Over-betting. The failure mode is not a bad trade, it is a correct edge
sized past `f*`, where the concavity of `E[log(1+fR)]` turns positive expectancy into
negative growth `[general knowledge]`.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE for every named scheme, with one
exception that is invisible.** The exception: volatility targeting is *mandatory* and baked
into the R unit (Part B-2). Everything else: **named missing primitive —
`BacktestEngine.__init__` has no `account: AccountState` parameter**
`[repo-verified: engine.py:231-242]`, and `futures_agents/backtest/` never imports
`futures_agents/risk/` `[measured: grep -rn "AccountConfig" futures_agents/backtest/*.py →
empty]`. Kelly specifically: **nothing in the repo computes it** `[measured: grep -rn -i
"kelly" --include=*.py . → no match]`.
**Already tested here?** **No.** Not once, in ~2,975,629 evaluations. Every one was flat
one-notional-contract. This is the single largest "never tested here" on my track and it is
an architectural consequence, not an oversight.

## III-8 Pyramiding / scaling in

**Mechanism.** Adding to a winner raises the average size on the trades that work, which
lengthens the right tail — the anti-martingale argument. Adding to a loser improves the
average price, which shortens the left tail until it does not `[general knowledge]`.
**Who runs it.** Turtle-lineage CTAs (add 1 unit per 0.5N in favour, 4 units max); trend
discretionaries; and — in the averaging-down form — the population of blown retail accounts
`[general knowledge]`.
**Where it lives.** Daily trend systems for the adds-on-strength form; intraday mean
reversion for the adds-on-weakness form.
**Minimum data.** OHLC, plus the ability to hold **more than one entry per idea** with
independent stops.
**How it is operated.** Turtle: initial unit at the breakout, add at +0.5N, +1.0N, +1.5N, move
*all* stops to 2N below the *most recent* entry, maximum 4 units per market and 12 correlated
`[general knowledge]`. Scale-in mean reversion: half size at 2σ, half at 3σ, stop beyond a
level that invalidates the whole thesis, exit the *whole* position at the mean.
**How it dies.** Adds-on-strength converts a won trade into a scratch when the last add is
stopped — the "give back the win" failure. Adds-on-weakness has unbounded loss unless the
total campaign risk is capped in advance, which is the one discipline that separates scaling
in from martingale.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE, outright**, exactly as the manager
pre-registered. `[repo-verified: engine.py:304-309]`: `if sid in open_pos or sid in pending:
continue`. One position per strategy, always. **Named missing primitive: `_OpenPosition` is
stored as `Dict[str, _OpenPosition]` keyed by `strategy_id`
`[repo-verified: engine.py:282]` — it would have to become
`Dict[str, List[_OpenPosition]]`, and `max_concurrent_per_strategy` — which already exists as
a dead parameter at `engine.py:232, 240` — would have to be read.** Cost estimate: the
lifecycle functions `_open_position`, `_manage` and `_close` are all single-position by
signature, and `Trade` is a single round trip with one `entry_price` and one `risk_points`
`[repo-verified: engine.py:75-118]`, so `Trade` would need a campaign identifier too. This is
a 200-line change, not a 5-line one — which makes "the interesting content is the cost of
changing it" (DIVISION §6) the right read.
**Already tested here?** **No**, and it cannot be.

## III-9 Scaling out, partial profit-taking, runner management

**Mechanism.** Taking part of the position at a near target raises the hit rate and funds the
runner psychologically; it also caps the right tail `[general knowledge]`.
**Who runs it.** Near-universal among discretionary intraday traders; unusual among CTAs,
which typically exit all at once on the reverse signal `[general knowledge]`.
**Where it lives.** Intraday, any instrument, minimum 2–3 contracts.
**Minimum data.** OHLC. **Met.**
**How it is operated.** "Half off at 1R, stop to breakeven, trail the rest" is the single most
common futures exit recipe in existence `[general knowledge]`. Note it is *three* decisions
bundled: a partial, a breakeven move, and a trail.
**How it dies.** The runner is the whole expectancy in a trend system, and scaling out
removes it. In a mean-reverting book it is nearly free.
**Expressibility here.** **EXPRESSIBLE, and one configuration of it has never been
generated.** `scale_out` + `breakeven_at_r` + `trail_atr_mult` are exactly the three
decisions `[repo-verified: base.py:217-220]`. The gap: **the residual runner is legal and
never generated.** `__post_init__` checks only `sum(scale_out) > 1.0`
`[repo-verified: base.py:235-236]`, so a sum below 1 is valid; `_scale_fraction` returns 0.0
past the end of the tuple `[repo-verified: engine.py:539-541]`; and the catalogue's five
`scale_out` shapes all sum to exactly 1.0.
`[measured: python3 -c "from futures_agents.strategies.base import ExitModel; from
futures_agents.backtest.engine import _scale_fraction; e=ExitModel(targets_r=(1.0,2.0,3.0),
scale_out=(0.5,0.3)); print(sum(e.scale_out), [_scale_fraction(e,i) for i in range(3)])"
→ 0.8 [0.5, 0.3, 0.0], leaving a 0.2 residual that runs to stop/trail/time/session]`
So the canonical recipe "half off at 1R, breakeven, trail the rest" is **constructible today
with zero new code** and, because `trail_atr_mult` has never been set (A-1) and no
`scale_out` has ever summed below 1.0, **has never been run.**
**Already tested here?** The all-out ladders, yes (`x_exits`: three targets worse than two,
z=−2.87 `[repo-verified: DEFECTS.md:210]`). The runner form: **No.**

## III-10 Stop discipline

**Mechanism.** The stop defines R and therefore every statistic downstream of it.
**Who runs it.** Everybody.
**Where it lives.** Everywhere.
**Minimum data.** OHLC; for structural stops, a swing detector.
**How it is operated.** Initial placement at the level that falsifies the idea (not at a
dollar amount); breakeven once the trade has paid for itself; trail by ATR, chandelier,
parabolic, or under each successive higher swing low; and *never* widen. Stop-hunt avoidance
means placing the stop beyond the obvious cluster rather than inside it `[general knowledge]`.
**How it dies.** A stop inside the noise floor converts a valid idea into a coin flip; a stop
beyond the noise floor but inside the liquidity cluster gets swept.
**Expressibility here.** **EXPRESSIBLE for placement, EXPRESSIBLE-NEVER-VARIED for
trailing — PENDING Q2 on whether there are five mechanisms or four.** Five `StopKind`s
`[repo-verified: base.py:187-192]` — though `VWAP_BAND` may be a re-scaled volatility band
rather than a distinct mechanism; asked as Q2 in `OPEN_QUESTIONS.md` because
`indicators/volume.py` is R1's surface — a per-contract noise floor
`[repo-verified: base.py:313-315, 719-723]`, and the one-way ratchet
`[repo-verified: engine.py:449, 462]`. The trail has never been switched on (A-1); the trail
*reason* is unreachable (A-2); parabolic and structural trails are absent (missing primitive:
`ExitModel.trail_kind`); and a trail-activation threshold is absent (missing primitive:
`ExitModel.trail_from_r`).
**Already tested here?** Yes, exhaustively for placement, and settled: `BRIEF.md` rules 3 and
4. Trailing: **No, never once.**

## III-11 Target discipline

**Mechanism.** Where you take profit determines the payoff half of the win-rate/payoff pair.
**Who runs it.** Everybody; CTAs mostly answer "no target".
**Where it lives.** Everywhere.
**Minimum data.** OHLC; for a structural objective, a swing detector; for a measured move,
the range being projected.
**How it is operated.** Fixed R (1.5–3R typical), measured move (project the setup's own
range), structural objective (the prior swing / the untested level), trail-only, or no target
at all. The operating rule that matters: a target that sits *behind* a large liquidity pool
will not be reached `[general knowledge]`.
**How it dies.** A fixed-R target in a trending market truncates the only trades that pay.
**Expressibility here.** **PARTIAL.** `TargetKind` covers fixed R and two anchors
`[repo-verified: base.py:165-184]`. Two absences: **no measured-move target** (there is a
`StopKind.RANGE` but no `TargetKind.RANGE`) and — this is the sharp one — **"no target" is
forbidden by the validator**: `if not self.targets_r: raise ValueError("at least one target
is required")` `[repo-verified: base.py:229-230]`. So the CTA exit ("no target, trail only")
cannot be constructed at all. **Named missing primitive: `targets_r` must be allowed to be
empty.**
**Already tested here?** Yes, and settled: `x_exits` — anchored raises payoff (z=−13.83) and
not expectancy `[repo-verified: DEFECTS.md:210]`.

## III-12 Time-based exits

**Mechanism.** An idea has a horizon; past it the position is holding risk with no thesis.
Also: time in the market is exposure to the unmodelled.
**Who runs it.** Intraday desks universally (flat at the close); event traders (out N minutes
after the release); systematic books with explicit holding-period targets
`[general knowledge]`.
**Where it lives.** Intraday above all. Session-close flattening is the single most common
operating rule in futures `[general knowledge]`.
**Minimum data.** Bar timestamps and a correct session definition.
**How it is operated.** Time stop: "N bars and I am out at market". Session close: flatten in
the last 5–15 minutes, before the close, not at it. Week-end: flat by Friday afternoon to
avoid weekend gap and headline risk. Holding-period targeting: exit at a fixed horizon
regardless.
**How it dies.** A time stop that is short relative to the thesis's horizon converts every
trade into a random exit — which this repo has already measured as a catastrophic defect.
**Expressibility here.** **EXPRESSIBLE for the time stop and session close;
INEXPRESSIBLE-ARCHITECTURE for week-end flattening.** `time_stop_bars` and
`exit_at_session_close` `[repo-verified: base.py:221-224; engine.py:464-473]`. Three caveats
that are mine rather than settled: the time stop is **never switched off** in the catalogue
`[measured: time_stop_bars is None in 0 of 11]`; `exit_at_session_close` is an exact alias
for anchored targets (D19); and **both exit types pay zero slippage** (A-7). Week-end:
**named missing primitive — `ExitModel` has no calendar term; the clock exists
(`timeutil.trading_day`, used at `engine.py:129-130`) so this is wiring, not data.**
**Already tested here?** Yes, and this is where the repo's largest single exit effect lives:
D12 — "Median hold at 240m and 1440m is 0.0 minutes… Turning it off is the single largest
exit effect measured (paired sign z = +3.52)… Every 4h and daily result in this project is
contaminated by it" `[repo-verified: DEFECTS.md:160-167]`. Also D1, D4, D21. Not
re-litigated.

## III-13 Re-entry after a stop-out

**Mechanism.** A stop-out is often noise rather than falsification; the setup can still be
valid, and re-entering restores the position at a better price. The counter-argument is that
re-entry is where over-trading begins `[general knowledge]`.
**Who runs it.** Discretionary intraday traders constantly; systematic books rarely, and when
they do it is capped explicitly.
**Where it lives.** Intraday.
**Minimum data.** OHLC plus **the memory of the previous exit**.
**How it is operated.** Rules real operators use: at most two attempts per setup; re-enter
only on a *fresh* trigger, not the same one; re-enter only at a price better than the first
entry; cap the *campaign* risk at 1R total rather than 1R per attempt; and a cooldown of N
bars or until a new swing forms `[general knowledge]`.
**How it dies.** Uncapped re-entry in a range is a loss machine — the same setup fires, stops,
fires, stops.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE, and the current behaviour is the
worst case.** After a stop, the position is deleted from `open_pos`
`[repo-verified: engine.py:300-302]` and the same `strategy_id` is eligible again in the very
same bar's step 3 `[repo-verified: engine.py:304-309]`. So **re-entry in this repo is
unconditionally maximal and has never been varied**, and the disciplined forms are all
unreachable. **Named missing primitive: `StrategyFilters` has no `cooldown_bars` field
`[measured: dataclasses.fields(StrategyFilters) → 8 fields, none temporal-since-exit]`, and
`run_many` keeps no `last_exit_index: Dict[str, int]`
`[repo-verified: engine.py:282-283 — only `open_pos` and `pending`]`.** Estimated cost: one
field plus one dict plus one comparison — roughly six lines, the cheapest architectural gap
on my track.
**Already tested here?** **No.**

## III-14 Portfolio heat, correlated exposure, loss limits, equity-curve trading

**Mechanism.** Total risk, not per-trade risk, is what ruins an account; and correlated
positions are one position wearing several names.
**Who runs it.** Every professional book. Prop-firm evaluation accounts enforce it
mechanically, which is why it dominates retail futures operating discipline
`[general knowledge]`.
**Where it lives.** Account level.
**Minimum data.** Open positions with their risk, a correlation grouping, realised P&L by
day, and equity history.
**How it is operated.** Heat: cap the sum of open risk at 2–6% of equity. Correlated
exposure: one position per correlation group (ES and NQ are one bet). Daily loss limit: stop
for the session at −X. Giveback: stop if 40% of the day's peak profit is lost. Drawdown
governor: cut size in steps as the buffer is consumed. Equity-curve trading: stand the system
down when its own equity is below its own moving average.
**How it dies.** Every one of these is a **selection rule**, and selection truncates the right
tail as well as the left. A daily loss limit guarantees you are flat on the worst day and also
flat on the day that would have recovered it.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE in research; fully specified on the
live path.** Nineteen parameters at `[repo-verified: config.py:355-400]` enforced at
`[repo-verified: risk/manager.py:140-195, 249-252]`, and **zero visible to the backtester**
`[measured: grep -rn "AccountConfig" futures_agents/backtest/*.py → empty]`. And
`run_portfolio` is a batch runner: "Each strategy still keeps completely independent position
state" `[repo-verified: engine.py:262-267]`. **Named missing primitive: one
`account: AccountState` parameter on `BacktestEngine.__init__` plus a
`Dict[str, float]` of open risk keyed by `ContractSpec.correlation_group` — the same
primitive unlocks heat, correlated exposure, daily limits, giveback, trade caps,
consecutive-loss stand-down and equity-curve trading, i.e. seven sub-families at once.**
**Two things that are reachable without it, and are the strongest positives on my track:**
(a) the path-dependent limits (daily loss, max trades/day, consecutive-loss stand-down,
equity-curve on/off) are all **replayable over stored trade artefacts** — 21,954 trades with
`ts` and `r` exist at `workspace/strategy_research/scratch/geo_trades.json`
`[measured: python3 -c "import json; d=json.load(open('workspace/strategy_research/scratch/
geo_trades.json')); print(len(d), sorted(d[0]))" → 21954 ['arm','base','cell','dir','exitm',
'mae','mfe','mins','r','reason','regime','session','slice','symbol','tf','ts','vol']]`;
(b) whether streak-based rules can work at all reduces to the autocorrelation of the R
series, and `bootstrap_paths(mode="block")` already exists to test it
`[repo-verified: montecarlo.py:84-110]` — but `risk_of_ruin` cannot reach it
`[repo-verified: montecarlo.py:209-231 — no `mode` parameter]` and no call site anywhere
passes `mode="block"` `[measured: grep -rn 'mode="block"' → docstring at montecarlo.py:91
only]`.
**Already tested here?** **No** — with one adjacent exception: `risk_of_ruin` /
`monte_carlo` are wired into `assess_robustness` `[repo-verified: robustness.py:323-328]`,
but at a **flat** `dollar_risk_per_trade` scalar and always in i.i.d. mode. And the *selection*
half is settled negative: `BRIEF.md` — trading last period's top 10 underperforms trading the
whole qualifying universe.

## III-15 Roll management

**Mechanism.** A futures position must be moved to the next expiry or it expires; the roll is
a trade with its own cost and its own information (the spread).
**Who runs it.** Everybody holding beyond expiry; the mechanics are a specialism at size.
**Where it lives.** All futures. For micros, quarterly (MES/MNQ/MGC) or monthly (MCL).
**Minimum data.** A **contract-month label**, two expiries quoted simultaneously, and volume
or open interest per expiry to time the roll.
**How it is operated.** Roll when front-month volume or OI is overtaken by the next month
(typically 3–8 days before expiry), as a **calendar spread in one ticket** rather than two
legs, and size the roll to the position, not to the signal. Discretionary desks roll into
liquidity windows `[general knowledge]`.
**How it dies.** Legging the roll in a fast market; rolling into the illiquid hour; and
back-adjustment error corrupting the history you researched on.
**Expressibility here.** **INEXPRESSIBLE-DATA.** Every one of the 48 `csv/raw/` files has the
header `open_time,open,high,low,close,volume` `[repo-verified: DIVISION Appendix B.1]`
`[measured: head -1 csv/raw/MGC_1h.csv → open_time,open,high,low,close,volume]` — no
contract-month column, no open interest, no settlement. **Named missing primitive: a
contract-month or expiry-date column on the bar schema.** Where a roll *is* visible in this
data it is a defect, not a feature: D40, the spliced grain CSVs
`[repo-verified: DEFECTS.md:583-601]`. Boundary note: the curve/carry half of this belongs to
R2 (DIVISION §5.6); I claim only the operational half and I am not annexing anything.
**Already tested here?** No, and it cannot be.

## III-16 Execution mechanics

**Mechanism.** The difference between the backtest price and the fill price is a real,
recurring cost, and choosing the order type is how you trade certainty of fill against price.
**Who runs it.** Everybody; it is the whole job at market-making scale (R1's I-5).
**Where it lives.** Everywhere, and it dominates at sub-hourly scale.
**Minimum data.** For honest modelling: the bid/ask spread and queue position. For a
usable approximation: a per-order-type slippage assumption conditioned on volatility and
liquidity.
**How it is operated.** Breakouts go in on stop orders (certainty over price); pullbacks on
resting limits (price over certainty); exits on stops are market orders and slip most; targets
are resting limits and slip not at all. A slippage budget vetoes the trade rather than chasing
it. Costs are budgeted per trade as a fraction of R, and any strategy whose cost exceeds ~10%
of R at its own stop distance is not tradeable at that stop distance `[general knowledge]`.
**How it dies.** Under-modelled slippage. It is the most common reason a backtest does not
replicate `[general knowledge]`.
**Expressibility here.** **PARTIAL, and this is the best-modelled operating layer in the
repo.** What is right: adverse slippage on both sides `[repo-verified: engine.py:353-355,
416-418]`, extra slippage for stop orders, a volatility term, a thin-book term
`[repo-verified: costs.py:29-47]`, honest gap handling, pessimistic tie-breaking, and entry at
the next open `[repo-verified: costs.py:50-67]`. What is missing, and each is a named
primitive: **no order-type object** (E1); **no size/impact term on `SlippageModel`** (S9);
**no slippage on TIME/SESSION_CLOSE/END_OF_DATA exits** (A-7); **`news=` never passed** (A-6);
**`FillModel.entry_on_next_open` is never read** (E2); **`cost_in_r` is never used as a
veto** (E6).
**Already tested here?** Yes, and the result is one of the cleanest in the repo: `x_costs` —
"Costs decide **MES 5m and nothing else**… All-in cost is 15.0% of one R at 5m, 4.6% at 60m,
1.2% at daily. Every other cell is negative **gross**"
`[repo-verified: DEFECTS.md:209]`. Not re-litigated.

## III-17 Meta-labelling and model-based filtering

**Mechanism.** Split the problem: a primary model decides *direction*, a secondary model
decides *whether to act and how large*. The secondary model can use features the primary
cannot (including the primary's own output), and it improves precision at the cost of recall
`[general knowledge]`.
**Who runs it.** Quantitative funds; the framing is López de Prado's
`[general knowledge]`.
**Where it lives.** Any instrument; it is a layer, not a strategy.
**Minimum data.** Labelled outcomes per signal **plus the features present at signal time**.
That pairing is the whole requirement.
**How it is operated.** Generate signals with a simple primary rule; label each with its
realised outcome; fit a classifier on the features-at-signal-time to predict that label; then
take only signals above a probability threshold, or size in proportion to the probability.
The operating trap: the labels must be generated out-of-sample or the secondary model learns
the primary's overfit `[general knowledge]`.
**How it dies.** Leakage from the labelling window, and a secondary model with fewer
effective observations than parameters.
**Expressibility here.** **PARTIAL, and one field short of reachable.** The repo generates
exactly the required pairing on every signal and then throws away the feature half.
`Strategy.evaluate` builds `Evidence(kind="indicator", name=..., value=res.value, ...,
weight=res.strength, ...)` per signal condition `[repo-verified: base.py:688-691]` and a
scalar `strength = strength_sum / n_signals` `[repo-verified: base.py:766]`. Both are on
`StrategySignal` `[repo-verified: base.py:509, 515]` and **neither reaches `Trade`**
`[measured: set(StrategySignal fields) − set(Trade fields) → {'bar_index','entry','evidence',
'invalidation','stop','strength','timeframes','ts'}]`. The engine never reads `strength` at
all `[measured: grep -n "strength" futures_agents/backtest/engine.py → no match]`.
**Named missing primitive: `Trade.strength` (and, for the richer version,
`Trade.evidence`)** — but see the correction below, which is the real finding.

**The secondary model has no features to learn from.** I checked whether the discarded
conviction score actually varies. It does not: **only **5** of the 79 conditions ever grade their
own strength — all five in the `candlestick` group, 4 of them SIGNALs — so 49 of 53 SIGNAL
conditions return the default `strength=1.0`**
`[measured: python3 -c "<inspect.getsource census over CONDITIONS>" → 5 graded:
candle_close_strength, candle_decisive_close, candle_engulfing, candle_reversal,
inside_bar_compression — see the CORRECTION at the end of this file for why my first census
returned 4]`
`[repo-verified: base.py:80-83 — `ConditionResult.yes(..., strength: float = 1.0)`]`. So
`strength` is a constant, and every `Evidence.weight` is 1.0
`[repo-verified: base.py:691]`. **The binding primitive for III-17 is not `Trade.strength`;
it is that 49 of 53 SIGNAL conditions do not report *how emphatically* they fired, even though
`ConditionResult.strength` exists to carry it and the feature columns contain the
information.** That is a ~50-condition rewrite. Meta-labelling here is not one field away.
Note also that a `ConditionKind.FILTER` is *not* a meta-label: filters are evaluated **before**
the signal and short-circuit it `[repo-verified: base.py:670-675]`, so they cannot condition
on the primary's output.
**Already tested here?** **No.**

## III-18 Discretionary overlay and operating discipline

**Mechanism.** Most realised underperformance against a system's backtest is operator error,
not model error; a journal, a review cadence and an error taxonomy make the error rate
measurable and therefore reducible `[general knowledge]`.
**Who runs it.** Every professional discretionary trader; prop firms enforce it.
**Where it lives.** Not in the market. In the operator.
**Minimum data.** A per-trade record of *intended* versus *executed*, plus a reason code.
**How it is operated.** Pre-trade plan written before entry; post-trade classification into
{followed plan and won, followed plan and lost, deviated and won, deviated and lost} — the
third quadrant being the dangerous one; weekly review of deviation rate, not of P&L; and an
explicit error taxonomy (early entry, no entry, moved stop, oversized, revenge).
**How it dies.** It does not die; it is abandoned.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE by category, and correctly so.** This is
the one Class III family that is not a property of price at all: it needs an *intended* action
to compare the *executed* action against, and a backtest has no intent that differs from its
execution. The repo has the nearest analogue —
`[repo-verified: workspace/journal/]` exists as a directory and `CALLOUT.md` documents live
operation — but there is no field anywhere pairing an intended trade with an executed one.
**Named missing primitive: `Trade` has no `deviation_reason` and no link to a prior intent
record `[measured: dataclasses.fields(Trade) → 38 fields, none of them an intent or
deviation code]`.** I record this as a genuine category boundary rather than a gap to fill: a
deterministic backtester cannot deviate from itself.
**Already tested here?** Not applicable.

## III-19 Anti-strategy: what operationally destroys expectancy

**Mechanism.** The inverse question. If a rule reliably destroys expectancy, its negation is
information, and testing the destroyer is cheaper than testing every constructive idea
`[general knowledge]`.
**Who runs it.** Nobody runs it deliberately. Everybody has run it accidentally.
**Where it lives.** Retail accounts.
**Minimum data.** Whatever the destroyer needs — usually account state, not price.
**How it is operated.** The canonical four: **moving a stop away from price** to avoid the
loss; **martingale** (double after a loss); **over-trading** (no cap on frequency); and
**revenge trading** (size up immediately after a loss). Two more worth naming: **removing the
stop entirely**, and **cutting winners while holding losers** (the disposition effect).
**How it dies.** It does not die. It kills.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE in the direction that matters — and the
reason is that the library is structurally incapable of indiscipline.** Full audit in
`R3_operating_vocabulary.md` §10. Summary: the stop ratchet is one-way
`[repo-verified: engine.py:449, 462]`; size is fixed at `remaining=1.0`
`[repo-verified: engine.py:374]` and the live layer states "It is never scaled up: a winning
streak is not information about edge" `[repo-verified: risk/manager.py:146-147]`; a trade
whose stop cannot be computed is simply not taken `[repo-verified: base.py:271-275, 717-723]`.
**The one destroyer the library expresses by default is over-trading**, because there is no
trade cap of any kind in the backtester `[repo-verified: engine.py:304-309 — no counter]`. So
the shipped population *is* the over-trading arm, and the disciplined arm is the one that
cannot be built. **Named missing primitive: the same `account: AccountState` on
`BacktestEngine` — you cannot measure indiscipline without modelling the thing discipline
protects.**
**Already tested here?** **No**, and — this is the finding — mostly *cannot* be. The
deliberate-inversion idea the manager named in my brief (invert a losing rule) is partly
reachable by a different route: `allowed_directions` is a `Strategy` field
`[repo-verified: base.py:559, checked at base.py:693]`, so "take the opposite side of a
condition" is expressible; but all 13 templates ship `(LONG, SHORT)`
`[measured: python3 -c "set(tuple(d.value for d in s.allowed_directions) for s in
generate_strategies('MGC',[5,15,60,240],max_total=400))" → {('LONG','SHORT')}]`, so
directional inversion has never been generated either.

### Class III catalogue split

| verdict | families |
|---|---|
| `EXPRESSIBLE` | 2 — III-3 (vol regime), III-10 (stop placement half) |
| `PARTIAL` | 7 — III-1, III-2, III-4, III-6, III-9, III-11, III-16, III-17 *(8 — see note)* |
| `INEXPRESSIBLE-ARCHITECTURE` | 8 — III-5, III-7, III-8, III-12 (week-end half), III-13, III-14, III-18, III-19 |
| `INEXPRESSIBLE-DATA` | 1 — III-15 |

*Note: III-12 splits — the time stop and session close are EXPRESSIBLE (and confounded),
week-end flattening is INEXPRESSIBLE-ARCH. III-17 is PARTIAL by one field. Counting
III-12 as EXPRESSIBLE and III-17 as PARTIAL gives 3 / 8 / 7 / 1 = 19.*

**The headline: of nineteen Class III families, exactly one is blocked by missing data.
Eighteen of nineteen are blocked, if at all, by code.** That is the opposite of what I
expected before reading, and it is the sharpest contrast this roundtable will produce against
R1 (participant data) and R2 (a second series), whose blocks are overwhelmingly data. See my
answer to §7 Q1.

---

# R3-D3 — Sizing and pyramiding as strategy: the two specific questions answered

The full argument is Part B. This section answers the two questions DIVISION §3 named, each
with a path.

## Question 1 — the engine's position-lifecycle rule at `engine.py:303-308`

The rule sits at `[repo-verified: futures_agents/backtest/engine.py:304-309]` (the line
numbers shifted by one from DIVISION's reference; the comment header is at :304 and the guard
at :308-309):

```
# --- 3. look for new signals (never while already positioned) ---
if i + 1 < stop_at:
    for s in strategies:
        sid = s.strategy_id
        if sid in open_pos or sid in pending:
            continue
```

**Answer: one position per `strategy_id`, always, and the parameter that appears to control it
does nothing.** Five consequences, in descending order of how badly they hurt:

1. **Pyramiding (III-8) is INEXPRESSIBLE-ARCHITECTURE.** Confirmed exactly as DIVISION §6
   pre-registered.
2. **Stop-and-reverse / always-in-the-market (III-1's canonical operating mode) is
   INEXPRESSIBLE-ARCHITECTURE** — a consequence nobody in this repo has recorded. A strategy
   holding a long cannot see the short signal that should flip it, because
   `s.evaluate(snap, cache)` is never called for a positioned strategy. *This is a bigger loss
   than pyramiding*, because stop-and-reverse is how the largest systematic futures programmes
   on earth actually run `[general knowledge]`.
3. **Re-entry discipline (III-13) is INEXPRESSIBLE-ARCHITECTURE, and the default is the
   undisciplined extreme** — the same `sid` is eligible again on the same bar it was stopped
   `[repo-verified: engine.py:300-302 then :304-309]`.
4. **`max_concurrent_per_strategy` is a `DEAD-HANDLE`.** Accepted and stored
   `[repo-verified: engine.py:232, 240]`, read nowhere
   `[measured: grep -rn "max_concurrent" --include=*.py . → set at engine.py:240; every other
   hit is `AccountConfig.max_concurrent_positions`, a different field, consumed only at
   risk/manager.py:249-252]`. A future study can pass `max_concurrent_per_strategy=3`, receive
   no error, and believe it tested unit adds.
5. **The cost of the rule is unrecorded.** `BacktestResult.signals_skipped_in_position` is
   declared `[repo-verified: engine.py:201]` and never assigned
   `[measured: grep -rn "signals_skipped_in_position" --include=*.py . → engine.py:201 only]`.
   Worse, `signals_generated` is incremented only inside the flat branch
   `[repo-verified: engine.py:317]`, so **"signals generated" actually means "signals
   generated while flat"** — a second vocabulary error in the same six lines.

**Cost to change.** Not small. `open_pos: Dict[str, _OpenPosition]`
`[repo-verified: engine.py:282]` becomes `Dict[str, List[_OpenPosition]]`; `_open_position`,
`_manage` and `_close` are all single-position by signature
`[repo-verified: engine.py:344, 377, 479]`; and `Trade` is one round trip with one
`entry_price` and one `risk_points` `[repo-verified: engine.py:75-118]`, so it needs a campaign
identifier before multi-entry P&L can be attributed. Order 200 lines, plus every downstream
metric that assumes one entry per trade. **DIVISION §6's framing was right: the interesting
content here is the cost, not the verdict.**

## Question 2 — does the backtester ever consult `risk/manager.py` or `risk/account.py`?

**Answer: no. Never. They serve the live proposal path only.**

`[measured: grep -rn "AccountConfig" futures_agents/backtest/*.py → (empty)]`
`[measured: grep -rn "import" futures_agents/backtest/*.py | grep -i risk → one hit,
`backtest/__init__.py:9: from .montecarlo import MonteCarloResult, monte_carlo, risk_of_ruin`
— a local module symbol, not the `risk` package]`
`[measured: grep -rn "from .*risk\.(manager|account) import" --include=*.py . →
ui/state.py:36-37, ui/api.py:35-36, agents/context.py:20-21, agents/decision.py:41,
agents/risk_agent.py:44, orchestrator.py:45-46, bot.py:36-37, tests/test_risk.py:22-23,
tests/conftest.py:30-31 — no file under backtest/]`

Per-field confirmation: of the 26 `AccountConfig` fields, **zero** are read anywhere under
`futures_agents/backtest/`
`[measured: python3 -c "<per-field reader census across futures_agents/**.py, excluding
config.py>" → 26 fields; the three apparent backtest hits (`starting_equity`,
`trailing_drawdown`, `max_consecutive_losses`) are plain function parameters in
`montecarlo.py`/`robustness.py` and a same-named attribute on `Metrics`
(`backtest/metrics.py:71-72`), not AccountConfig reads — which the import grep above proves]`

The one place the two worlds touch is `robustness.py:323-327`, which feeds the R series into
`monte_carlo` with a **flat scalar** `dollar_risk_per_trade`
`[repo-verified: futures_agents/backtest/robustness.py:323-327]` and without a `mode=`
argument, so always the i.i.d. bootstrap `[repo-verified: montecarlo.py:113-120]`. That is
constant-risk sizing — the only scheme that, by construction, does nothing.

**So the whole sizing vocabulary in this repository is enforced downstream of every number it
has ever published.** Nineteen operating parameters, a six-rung de-risk ladder, a
correlation-group cap and an integer-contract floor, all sitting on the far side of an import
boundary from the 2,975,629 evaluations they were meant to govern.

---

# R3-D4 — Variance versus expectancy, per axis

Per DIVISION §3: for every axis, is the claim *changes expectancy* or *only reshapes the
distribution*, and which has this repo already measured. I use the Channel labels from Part
B-3. **Nothing already settled is re-argued** — settled items get a citation and a full stop.

| axis | the claim made for it | actual channel | already measured here? |
|---|---|---|---|
| Stop width | "the right stop finds the edge" | **1 — reshapes only** | Yes, 4×. `BRIEF.md` r3: payoff +89%, win rate −14pts, no expectancy gain. **Settled.** |
| Stop kind (ATR vs structure) | "structure is where risk really is" | **1 — reshapes only** | Yes. `x_exits`: "No stable best stop width — the ordering reverses by timeframe" `[repo-verified: DEFECTS.md:210]`. **Settled.** |
| Stop noise floor | "below the floor it is a coin flip" | 1, but a hard **2** at the boundary (the trade is refused) | Yes. `BRIEF.md` r4. **Settled.** |
| Target R multiple | "let winners run" | **1 — reshapes only** | Yes. `x_exits`: three targets worse than two, z=−2.87. **Settled.** |
| Anchored vs R-multiple target | "decoupling target from stop buys reward for risk" | **1 — reshapes only.** The mechanism is real (payoff z=−13.83) and expectancy does not follow | Yes, and **confounded**: the headline "anchored beats R_MULTIPLE" (z=−5.87) **is** the session-close flag; crossing them drops target-kind to z=−1.80/+1.24 `[repo-verified: DEFECTS.md:160-167 (D12), :236-241 (D19)]`. **Settled.** |
| Breakeven trigger | "never let a winner become a loser" | **1 — reshapes only**, and it is the purest example: it converts left-tail mass into a point mass at 0 | Partially — varied {1.0,1.5,2.0,None} in the catalogue but never isolated (D15: only 93 of 8,317 rule sets exist with two exits). |
| Scale-out ladder | "bank some, hold some" | **1**, plus a real **3** via D13 (under-costed ~2×) | Yes for shape; D13 is the cost caveat `[repo-verified: DEFECTS.md:169-173]`. |
| **Residual runner** (sum < 1) | "the runner is the whole expectancy" | **1** in shape, but it changes the **exit-reason mix**, which is a **3** | **No — never generated.** |
| **Trailing stop** | "convert 1R winners into 4R winners" | **1** in shape; **3** via exit-mix | **No — never run once** (A-1). |
| Time stop magnitude | "if it has not worked it is not working" | **1 and 2** — it truncates the distribution *and* forces an exit that changes the population of outcomes | Yes, catastrophically: D12, and the primary-bars fix at `engine.py:386-393` (before it, 100% of 4h exits were TIME exits). **Settled.** |
| **Time stop presence** (None vs set) | as above | **1 and 2** | **No — `time_stop_bars` is never None in the catalogue.** |
| Session-close flattening | "do not carry unmeasured gap risk" | **2 and 3** — genuinely changes the population and the cost | Yes — largest single exit effect (z=+3.52) — but **unidentifiable** on the shipped population (D19). |
| **Week-end flattening** | same | **2 and 3** | **No — inexpressible.** |
| Cost per R via risk unit | "costs decide everything at 5m" | **3 — changes expectancy, monotonically** | Yes. `x_costs`: 15.0% of R at 5m, 4.6% at 60m, 1.2% at daily. **Settled**, and it is the cleanest non-cancelling result in the repo. |
| Trade-count reduction | "be selective" | **3 for total P&L; NOT an expectancy transform** | Indirectly: `x_confluence` — 2→4 signals cuts count 65→42 and does not move expectancy. The distinction (P&L vs per-trade) is not drawn anywhere in the repo. |
| Slippage on time/session exits | — | **3 — understated** | Partially: D13 notes "62–92% of 4h/daily exits pay no exit slippage". A-7 names the mechanism generally. |
| **Market impact / capacity** | "size has a price" | **3** | **No — `SlippageModel` has no size term.** |
| Fixed fractional / fixed ratio | "compound the edge" | **4a — variance only.** `E[wR]=E[w]E[R]` | **No.** |
| Kelly / fractional Kelly | "maximise growth" | **4a — variance only**, and against `E[R] ≤ 0` the optimum is `f* ≤ 0` | **No.** Nothing in the repo computes it. |
| Volatility targeting | "constant risk per trade" | **4a — variance only**, and **already mandatory** (Part B-2) | Universal, therefore never controlled. |
| Risk parity | "equal risk contribution" | **4a** | **No.** |
| **Conviction-weighted sizing** | "bigger on the A+ setup" | **4b — CAN change expectancy** iff `Cov(strength, R) ≠ 0` | **No, and it currently has no input.** The score is computed at `base.py:766`, discarded before `Trade`, **and is a constant 1.0** because 49 of 53 SIGNAL conditions never grade their firing `[measured]`. So `Cov(strength, R) = 0` by construction today. |
| **Equity-curve / streak sizing** | "cut size in a losing streak" | **4b — CAN change expectancy** iff the R series is autocorrelated | **No**, and the repo's ruin machinery *assumes* it cannot (i.i.d. bootstrap, `mode="block"` unreachable from `risk_of_ruin`). |
| Regime-conditional sizing | "size up where it works" | **4b**, formally — but it is a selection rule | Indirectly settled **negative**: selecting last period's best underperforms trading everything (`BRIEF.md`). |
| **Integer-contract floor** | usually treated as rounding | **2 — changes the trade population**, selected on stop distance ⇒ on volatility | **No.** The engine never calls `contracts_for`. |
| **Portfolio heat / correlated cap** | "total risk is what ruins you" | **2 — forces selection** | **No.** `run_portfolio` nets nothing. |
| **Daily loss limit / trade cap / stand-down** | "protect the account" | **2 — path-dependent deletion of trades** | **No**, but **replayable from stored artefacts.** |
| **Re-entry policy** | "the setup is still valid" | **2 — changes the population** | **No.** Default is unconditionally maximal. |
| Pyramiding | "add to winners" | **1 and 2** | **No — inexpressible.** |
| Directional restriction | "only trade the long side of an uptrending market" | **2** | **No** — all 13 templates are `(LONG, SHORT)`. |
| Meta-label gate | "skip the low-quality signal" | **2** | **No.** A `FILTER` is not a meta-label: filters run *before* the signal `[repo-verified: base.py:670-675]`. |
| Order type at entry | "stop for breakouts, limit for pullbacks" | **2 and 3** — a resting limit changes *which* signals become trades | **No — no order-type object exists.** |
| Cost-aware skip | "do not take a trade whose cost is 20% of R" | **2 and 3** | **No.** `cost_in_r` exists and is never used as a veto. |

**Count.** 33 axes labelled. **Channel 1 (reshapes only): 8. Channel 3 (cost, changes
expectancy): 5. Channel 2 (population, changes expectancy): 11. Channel 4a (variance only):
4. Channel 4b (can change expectancy): 3.** Two axes carry a mixed 1-and-2 label.

**So DIVISION §6's central prediction is confirmed with one correction.** The manager
predicted "most of the operating layer is a variance transform, not an expectancy transform"
and that the survivors would be "the ones that change costs or change the number of trades —
session-close flattening, time stops, cost-aware execution — not the ones that move stops and
targets around." That is right, and the correction is that **the survivor set is larger than
the manager's three**, because the whole Channel-2 block (11 axes) is also non-cancelling —
and Channel 2 is almost entirely unreachable here, which is why it has never shown up as a
survivor. The reason the operating layer *looks* self-cancelling in this repo is not that it
is; it is that **the only parts of it this harness can reach are the Channel-1 parts.**

---

# R3-D5 — The untested-and-cheap list

**Search method, stated as DIVISION §3 requires.** Three passes:

1. Enumerate every field of `ExitModel`, `StrategyFilters` and `Strategy` that changes
   behaviour `[measured: dataclasses.fields on all three → 12 + 8 + 11]`.
2. For each, measure the set of values it actually takes across (a) the full exit catalogue
   `expand_exit_models(include_structure=True, include_aggressive=True, include_anchored=True)`
   and (b) a real generation, `generate_strategies('MGC', [5,15,60,240], max_total=400)`
   → 314 strategies. A field with one distinct value has never been varied.
3. Cross-check each candidate against `workspace/studies/DEFECTS.md` (D1–D43) and the four
   `scan_reports/` verdict logs to confirm no completed study varied it by hand outside the
   generator.

**Result: the list is NOT empty. Six items qualify under the strict definition** (an existing
field of `ExitModel` or `StrategyFilters`, pinned to one value, requiring **zero new code**),
plus two artefact-replay items that need no library change at all. **This refutes DIVISION
§6's pre-registration of "≤2".** I am flagging that loudly, as the cover note asked.

## Tier 1 — zero new code, pure configuration (6 items, cheapest first)

| # | rule | the change | why it has never been tested | cost |
|---|---|---|---|---|
| 1 | **Turn the trailing stop on** | `replace(exit, trail_atr_mult=2.0)` | every one of the 11 catalogue exits leaves it `None` `[measured]`; the implementation has existed all along at `engine.py:451-462` | one field; but note the exit *reason* will report as STOP (A-2), so add the 2-line fix at `engine.py:419-421` first or the result is uninterpretable |
| 2 | **Leave a residual runner** | `ExitModel(targets_r=(1.0,2.0,3.0), scale_out=(0.5,0.3))` | all 5 catalogue `scale_out` shapes sum to exactly 1.0 `[measured]`; the validator permits sums below 1 `[repo-verified: base.py:235-236]` | one field. `[measured: sum=0.8, fractions [0.5,0.3,0.0], 0.2 residual runs to stop/trail/time/session]` |
| 3 | **Switch the time stop off** | `replace(exit, time_stop_bars=None)` | `time_stop_bars is None` in 0 of 11 `[measured]`. Given D12 measured the session-close flag as the largest exit effect in the repo, the time stop's *presence* is the obvious untested twin | one field |
| 4 | **Combine 1+2+3** — "half off at 1R, breakeven, trail the rest, no target on the runner, no time stop" | `ExitModel(stop_kind=ATR, stop_mult=1.5, targets_r=(1.0,), scale_out=(0.5,), breakeven_at_r=1.0, trail_atr_mult=2.0, time_stop_bars=None)` | **this is the single most common discretionary futures exit recipe in existence `[general knowledge]` and it has never been constructed here** | one `ExitModel` literal. `[measured: ExitModel(trail_atr_mult=2.0, time_stop_bars=None) is accepted by __post_init__]` |
| 5 | **Vary `StrategyFilters` scope** — `days_of_week`, `min/max_minutes_since_open`, `sessions`, `volatility` as a *scope* gate | `replace(strategy, filters=StrategyFilters(days_of_week=frozenset({"MON"})), _id=None)` | **exactly one `StrategyFilters` identity exists across 314 generated strategies** `[measured]`, because `generate_combinations` passes `template.filters` unchanged `[repo-verified: combinator.py:581]`. And there is a second reason: **before the D43 fix these variants all hashed to the same `strategy_id` and would have silently merged** `[repo-verified: DEFECTS.md:640-652]`. **D43's fix made this testable for the first time and nobody has used it since.** | one `replace` per arm |
| 6 | **`StopKind.FIXED_TICKS`** | `replace(exit, stop_kind=StopKind.FIXED_TICKS, stop_mult=40)` | 4 of the 5 stop kinds appear in the catalogue; FIXED_TICKS appears in none `[measured]`. It is also the only stop kind whose R unit is *not* volatility-scaled, so it is the natural control arm for Part B-2's claim that R normalisation is already vol targeting | one field; note `stop_mult` is reinterpreted as a tick count, a units overload |

**A caution I attach to all six**, from D15: "The exit index is sampled jointly with the rule
set, so only **93 of 8,317** shipped rule sets exist with two different exits. Exit
comparisons on the shipped population are confounded with the entry; a paired test requires
re-emitting entries across every exit" `[repo-verified: DEFECTS.md:184-187]`. So each of these
must be run as a **paired re-emission** — the same rule sets with the flag on and off — not as
a fresh sample. Any of them run as an unpaired sweep will produce a confounded answer.

## Tier 2 — zero new code AND zero new backtests (2 items)

| # | rule | how | evidence it is reachable |
|---|---|---|---|
| 7 | **Replay the path-dependent governors** over stored trades: daily loss limit, daily giveback, `max_trades_per_day`, consecutive-loss stand-down, equity-curve on/off | sort the stored trades by `ts`, apply the rule, compare the surviving R series against the full one | 21,954 trades with `ts` and `r` at `workspace/strategy_research/scratch/geo_trades.json` `[measured: json.load → 21954 rows; keys include 'ts','r','symbol','tf','exitm','reason','session','regime','vol','mae','mfe','mins']`. A second copy at `geo_trades_6040.json`. Parameter values are already specified at `config.py:367-372` |
| 8 | **Test whether streak-based sizing can work at all** — i.e. is the R series serially dependent? | `bootstrap_paths(r, runs, length, mode="block")` versus `mode="iid"` on the same series | `[repo-verified: montecarlo.py:84-110]` — both modes already implemented. `[measured: grep -rn 'mode="block"' --include=*.py . → the docstring at montecarlo.py:91 only; zero call sites]`. This is the precondition for every Channel-4b streak rule, and `risk_of_ruin` cannot reach it `[repo-verified: montecarlo.py:209-231 — no `mode` parameter]` |

## Tier 3 — one field or a handful of lines (6 items, for the round-2 build order)

Ranked by (value / lines):

| # | change | lines | unlocks |
|---|---|---|---|
| 9 | `signals_skipped_in_position += 1` at `engine.py:308` | **1** | the only measurement of what the one-position-at-a-time rule costs. Prerequisite for costing III-8 and III-13 |
| 10 | `Trade.strength` field + `strength=sig.strength` at `engine.py:498` | **2** | **Downgraded after checking — see the self-correction in Part B-3(b)(1).** The score is a constant 1.0 for ~all strategies, because only 5 of 79 conditions grade strength and 49 of 53 SIGNALs return the default `[measured]`. Worth 2 lines to *prove* the conviction channel is empty; worth nothing for sizing until the conditions are graded, which is a ~50-condition rewrite, not a field |
| 11 | slippage on the three `bar.close` exits (`engine.py:467, 473, 476`) | **3** | corrects A-7; makes time-stop and session-close results honest. Affects the largest measured exit effect in the repo (D12) |
| 12 | `news=` passed to `slippage_price` at `engine.py:353, 416` | **2** | A-6; the `econ_calendar` flag already exists |
| 13 | `ExitReason.TRAIL` emitted when the exit stop differs from `initial_stop` and breakeven | **4** | makes A-1/item-1 interpretable |
| 14 | `StrategyFilters.cooldown_bars` + `last_exit_index: Dict[str,int]` in `run_many` | **~6** | III-13 re-entry discipline, currently the undisciplined extreme |
| 15 | a `donchian_breakout` condition over the existing `hh20`/`ll20` columns | **~12** | III-1's canonical entry; **the feature is already computed on every bar of every timeframe and read by no condition** `[repo-verified: features.py:62, 265-266]` |

---

# R3-D6 (stretch) — Sequence support

D37: "the combinator cannot express a sequence at all"
`[repo-verified: workspace/studies/DEFECTS.md:541-548]`. My contribution is the *why*, the
*who needs it*, and the *minimum primitive*.

**Why.** `Strategy.evaluate` conjoins every signal condition against **one** `FeatureSnapshot`
and requires simultaneous agreement `[repo-verified: base.py:676-695]`. There is no cross-bar
state on `Strategy`, no "within N bars of" operator, and `Condition.evaluate` is a pure
function of `(snap, tf)` `[repo-verified: base.py:87, 108-131]`. So a sequence is not merely
unsupported by the combinator — it is unrepresentable by the `Condition` type.

**Which Class III families require one.**

| family | needs a sequence? | why |
|---|---|---|
| III-5 pattern/sequence | **Yes, definitionally** | it *is* the family |
| III-2 volatility breakout | **Yes, for the canonical form** | "NR7, *then* a break of its range" is ordered. Today it is approximated as the simultaneous state `volatility_compressed` AND a breakout signal, which is a different and weaker statement |
| III-6 opening range | **Yes, for the canonical form** | "range forms, *then* breaks, *then* retests" — and D39 records that library ORB is "a state, not an event" `[repo-verified: DEFECTS.md:557-582]`, which is this exact substitution |
| III-4 mean reversion | **Partly** | "extends, *then* stalls, *then* turns" is the disciplined entry; the simultaneous version enters into a running impulse |
| III-13 re-entry | **Yes** | "stopped out, *then* a fresh trigger" is inherently ordered — it is a sequence whose first element is an *exit*, which no sequence primitive over entry conditions would even cover |
| III-1, III-3, III-7…III-12, III-14…III-19 | No | they are states, geometries or account rules |

**Count: 3 families require a sequence for their canonical form (III-2, III-5, III-6),
2 more are degraded without one (III-4, III-13).**

**The minimum primitive.** Not a general event language. Two fields:

```
# on Condition
lookback_window: int = 0      # 0 = this bar only (today's behaviour);
                              # n = "fired on any of the last n bars"
# on Strategy
stages: Tuple[Tuple[Condition, ...], ...] = ()   # ordered; stage k must have
                                                 # fired before stage k+1
max_bars_between: int = 0                        # gap ceiling between stages
```

`lookback_window` alone buys ~80% of the value and is the cheaper half: it needs a per-bar
ring buffer of `ConditionResult` keyed by `(name, tf)`, which the existing per-bar `cache`
at `[repo-verified: engine.py:288]` is already shaped like — it is a `Dict[Tuple[str,int],
ConditionResult]` rebuilt each bar, so making it a deque of the last *n* such dicts is a small
change to `run_many` and no change to any condition. `stages` is the expensive half because it
needs per-strategy state across bars, which `Strategy` (a frozen-ish dataclass of pure
functions) deliberately does not have.

**One caution, and it is the reason I would not rank this first.** `BRIEF.md` rule 8 already
disposed of the best-documented sequence in this space: the ICT sweep→shift→retrace chain "is
real, common, and adds nothing over its parts". Building sequence support would let us express
III-2's and III-6's canonical forms — and the prior from the one sequence already measured is
that the ordering adds nothing over the conjunction. **That is a reason to build
`lookback_window` (cheap, and it fixes D39's state-versus-event substitution) and to be
sceptical of `stages` (expensive, and the one data point we have says ordering is not where
the information is).**

---

# Bonus — resolving DIVISION Appendix B.6's unexplained drift

Appendix B.6 notes that `coverage.py`'s docstring says the brief named **thirty-eight**
variables while `SPEC_CONFLUENCES` holds **thirty-nine**, and assigns it to nobody. It is
cheap to resolve, so here it is.

The specification's own variable list lives at
`[repo-verified: .claude/agents/strategy-research.md:17-24]` and contains **37** items:
`[measured: python3 -c "<regex-split of the 'Build and test strategies across …' sentence>"
→ n items = 37]`.

`SPEC_CONFLUENCES` reaches 39 by two independent edits to that list
`[measured: python3 -c "from futures_agents.strategies.coverage import SPEC_CONFLUENCES;
print(len(SPEC_CONFLUENCES)); print([k for k in SPEC_CONFLUENCES if 'candle' in k]);
print([k for k in SPEC_CONFLUENCES if 'previous day' in k or 'overnight' in k])"
→ 39; ['candlestick patterns']; ['previous day high/low', 'overnight high/low']]`:

1. the specification's single item **"previous-day and overnight levels"** is split into two
   entries, `"previous day high/low"` and `"overnight high/low"`; and
2. **`"candlestick patterns"`** is added, and is not in the specification's variable list at
   all.

**37 + 1 + 1 = 39.** The docstring's "thirty-eight" is consistent with the source after
exactly one of the two edits, so the drift is one undocumented addition on top of one
defensible split. Caveat: I compared against the specification as it exists in this repo at
that path; if an earlier version of the spec existed elsewhere, the split may have been in it.
Neither edit is a defect — the extra variable is *covered* by five real conditions
(`candlestick` group, DIVISION Appendix A) — but the count in the docstring should read 39,
and the added variable should be marked as an addition rather than left to look like part of
the brief.

---

# Part D — Anti-overfitting audit of my own code surface

My standing mandate names eleven hazards to hunt. Here is what I checked on the R3 surface
(`base.py` exits/filters, `engine.py` lifecycle, `costs.py`, `risk/`, `montecarlo.py`,
`robustness.py`) and what I found. **Four found, five clean, two not applicable.**

| hazard | checked? | finding |
|---|---|---|
| **Overfitting** | not re-measured (settled: programme-wide `free_t = 5.46`, largest t 3.923) | but I found a **structural immunity** nobody has recorded: `Condition` has no parameter field `[measured: dataclasses.fields(Condition) → 7 fields, none a parameter vector]`, so every entry lookback and threshold is a hard-coded constant. There is **no entry-parameter grid to mine.** The exit catalogue is likewise "deliberately modest… Exit parameters are the easiest place to overfit" `[repo-verified: combinator.py:46-52]`. On my surface, overfitting risk is unusually low — and see the next row for the price paid |
| **Data-mining bias** | yes | handled: `deflated_expectancy(m, report.trials_searched)` `[repo-verified: robustness.py:322]`. Nothing to add |
| **Parameter sensitivity** | yes | **FOUND, two ways.** (a) `parameter_sensitivity` perturbs only `stop_mult` and a scale on `targets_r`, plus a doubled-slippage stress `[repo-verified: robustness.py:221-240]` — **2 of `ExitModel`'s 12 fields**, and zero entry parameters (impossible, see above). `time_stop_bars`, `breakeven_at_r`, `scale_out`, `trail_atr_mult` and `exit_at_session_close` are never perturbed. (b) Worse: `rel = m.expectancy_r / baseline.expectancy_r if baseline.expectancy_r > 0 else 0.0` `[repo-verified: robustness.py:212-213]`, so when the baseline expectancy is non-positive **every ratio is exactly 0.0**, `worst_relative = 0.0`, and the bias check `worst >= 0.4` at `[repo-verified: robustness.py:154-159]` always fires. Since this repo's population is overwhelmingly non-positive, **the parameter-sensitivity flag is a constant and carries no information about any strategy** |
| **Insufficient sample size** | yes | handled (`sample_gate = min(1.0, m.trades/60)` and a 30-trade penalty `[repo-verified: robustness.py:334-337]`). One existing caveat I cite rather than re-derive: D6 — "The 20-trade floor selects on exit geometry, not signal" `[repo-verified: DEFECTS.md:63-69]`, which is a *sizing-adjacent* selection effect because exit geometry sets the risk unit |
| **Unrealistic fills** | yes | **FOUND.** A-8 / X6: `scale_out` assumes an infinitely divisible contract — `remaining` starts at `1.0` and is decremented by fractions like 0.3 `[repo-verified: engine.py:374, 433-439; base.py:218]`. A `(0.5,0.3,0.2)` ladder needs ≥10 contracts; the modelled budget permits about one `[repo-verified: config.py:361-364]`. Also E1: with no order-type object, a breakout is filled at the next bar's open rather than at a resting stop on the range edge — **this one is conservative, not flattering**, and I record it as such |
| **Understated costs and slippage** | yes | **FOUND, three new plus one known.** A-7: TIME, SESSION_CLOSE and END_OF_DATA exits are closed at `bar.close` with zero slippage `[repo-verified: engine.py:467, 473, 476, 326]` — and these are market orders. A-6: `SlippageModel.news_extra_ticks = 2.0` exists and the engine never passes `news=` `[repo-verified: costs.py:33; engine.py:353, 416]`. S9: no size or impact term anywhere, so cost in R is exactly size-invariant `[repo-verified: costs.py:29-33, 104-110, 119-122]`. Known: D13 (scale-out legs pay one round turn) `[repo-verified: DEFECTS.md:169-173]` |
| **Look-ahead bias** | yes, five ways | **CLEAN.** Full detail at A-11: next-open fills, stop-wins-ties, honest gaps, breakeven ordered after the stop check, targets re-projected from the actual fill. All correct |
| **Survivorship bias** | yes | **NOT APPLICABLE in the classical sense**, and I want that on the record rather than left implied: every backtest is one symbol `[repo-verified: engine.py:548, 554]`, so there is no cross-sectional universe from which losers could have been dropped. The two analogous risks on my surface are already catalogued and belong to others: D14 (per-symbol RNG seeding → MES and MGC 60m share 0 of 204 rule sets, so cross-run comparisons compare different strategies) and D40 (spliced grain CSVs) |
| **Repainting indicators** | yes, on the management path | **CLEAN.** The trail and the slippage scaler both index via `tf_index`, documented as "Index of the newest **completed** timeframe bar" `[repo-verified: features.py:921-926]`, and `atr_percentile` is a **causal trailing** percentile — `_percentile_of` computes `out[i]` from the buffer *before* appending `val` and trims to a 250-bar window `[repo-verified: features.py:316-325, called at features.py:246]`. The indicator library itself is R1's surface |
| **Future-data leakage** | yes | **CLEAN** on my surface, same evidence as the two rows above plus the engine's structural rule `[repo-verified: engine.py:5-6]` |
| **Identity collisions** (the manager pointed me here specifically) | yes | **BOTH FIXED, AND THE FIX IS SOUND.** `ExitModel.identity` `[repo-verified: base.py:248-267]` and `StrategyFilters.identity` `[repo-verified: base.py:459-484]` are each built from `sorted(dataclasses.fields(self))`, so a field added later cannot silently reintroduce the collision — that is the correct construction and I verified it reads all fields rather than a hand-written list. `Strategy.strategy_id` `[repo-verified: base.py:611-622]` includes symbol, primary_tf, group, condition labels, `exit.identity`, `filters.identity`, `allowed_directions`, `confirm_tfs`, `execution_tf` and `trigger_conditions` — complete. And the `_id` cache is invalidated correctly at both sites that mutate a Strategy: `replace(strategy, exit=exit_model, _id=None)` `[repo-verified: robustness.py:208]` and `replace(x, symbol=s, _id=None)` `[repo-verified: combinator.py:694]` `[measured: grep for replace() on a Strategy → only those two sites, both passing _id=None]`. **Clean bill.** |

**One consequence worth pulling out of that table.** The manager's brief to me said the
operating layer "is where this library has historically been wrong about *what it was even
testing*". That is true, and the audit shows the errors are of a specific and consistent
type: **not incorrect arithmetic, but vocabulary that does not mean what it says.**
`ExitReason.TRAIL` never fires. `signals_generated` means "generated while flat".
`max_concurrent_per_strategy` does nothing. `signals_skipped_in_position` is always zero.
`run_portfolio` is a batch runner. `exit_at_session_close` is an alias for the target kind.
`news_extra_ticks` is unreachable. `parameter_sensitivity`'s flag is a constant. Every one of
those is a name that a reader — or a future study — would reasonably trust.

---

## Answers to the manager's three questions

### Q1 — Is our null result a property of the market, or of our information set?

**For Class III, it is a property of neither the market nor the data. It is a property of the
code.**

Of nineteen Class III families, **exactly one — III-15, roll management — is blocked by
missing data.** `csv/raw/` supplies no contract-month label
`[repo-verified: DIVISION Appendix B.1]` and there is no substitute. That is the whole
data-blocked list.

**Eighteen of nineteen are blocked, if at all, by the harness.** Eight land on
INEXPRESSIBLE-ARCHITECTURE (III-5, III-7, III-8, III-13, III-14, III-18, III-19, plus the
week-end half of III-12) and eight more are PARTIAL with the loss stated. Every one of those
eight architectural blocks resolves to a named, small-to-medium code change: an
`account: AccountState` parameter, a `FeatureSnapshot` in `_manage`, an
`ExitModel.exit_conditions` field, a `cooldown_bars` field, a
`Dict[str, List[_OpenPosition]]`, a `Trade.strength` field, a `lookback_window` on
`Condition`.

**So my track's answer is the opposite of what the roundtable-wide risk (DIVISION §9) feared.**
The merged catalogue will not read "we only have OHLCV on one contract" from R3. Class III
*only needs* OHLCV on one contract — that is its definition — and the data is present. What is
absent is the ability to manage the position once it is open:

> **This harness can shape a trade and cannot manage one.** Twelve `ExitModel` fields describe
> price levels, a clock and a session boundary `[measured: dataclasses.fields(ExitModel) →
> stop_kind, stop_mult, target_kind, anchor_mult, min_reward_risk, stop_pad_ticks, targets_r,
> scale_out, breakeven_at_r, trail_atr_mult, time_stop_bars, exit_at_session_close]`; none of
> them is a condition; and `_manage` receives a `Bar`, never a `FeatureSnapshot`
> `[repo-verified: engine.py:377-378]`. So every exit in ~2,975,629 evaluations was
> geometric, and none was informational.

One further item belongs in this answer because it is neither data nor architecture but
**unwritten code**: `ConditionResult.strength` exists, is averaged into every signal, and is
populated by only 5 of the 79 conditions (A-12). So the repo's information set is also smaller
than its own schema advertises — not because the data is missing, but because 49 of 53 SIGNAL
conditions return a hard-coded `1.0` where a graded reading was intended.

And on the specific question of whether the null is *about* the operating layer: **it cannot
be, because the operating layer was never in the experiment.** Nineteen `AccountConfig`
operating parameters sit on the far side of an import boundary from every published number
`[measured: grep -rn "AccountConfig" futures_agents/backtest/*.py → empty]`. "Nothing here is
live-eligible" is a statement about *signals run flat, one at a time, with geometric exits*.
It is not yet a statement about futures trading operated by a desk.

### Q2 — Any family expressible with today's combinator, widely operated, and never tested here?

**Yes — this is not empty, and it is larger than DIVISION §6 pre-registered.** Ranked, cheapest
first. Full detail and the search method are in R3-D5.

**Tier 0 — zero new code, zero new backtests (2):**

1. **Replay the account governors over stored trades.** Daily loss limit, daily giveback,
   `max_trades_per_day`, consecutive-loss stand-down, equity-curve on/off. These are among the
   most widely operated rules in futures — every prop-firm evaluation account enforces them
   `[general knowledge]` — and none has ever been measured here. The artefact exists: 21,954
   trades with `ts` and `r` `[measured: workspace/strategy_research/scratch/geo_trades.json →
   21954 rows, keys include 'ts','r','symbol','tf','exitm','reason','session','regime','vol']`.
   The parameter values are already specified `[repo-verified: config.py:367-372]`. Cost: one
   script over one file.
2. **Test whether the R series is serially dependent** — `bootstrap_paths(..., mode="block")`
   versus `mode="iid"` `[repo-verified: montecarlo.py:84-110]`. This single measurement decides
   whether *any* streak-based sizing or equity-curve rule can work, and **no call site in the
   repo has ever passed `mode="block"`** `[measured: grep -rn 'mode="block"' → docstring only]`.
   Cost: one function call.

**Tier 1 — zero new code, configuration only (6):**

3. **"Half off at 1R, breakeven, trail the rest."** The single most common discretionary
   futures exit recipe in existence `[general knowledge]`, constructible today as
   `ExitModel(targets_r=(1.0,), scale_out=(0.5,), breakeven_at_r=1.0, trail_atr_mult=2.0,
   time_stop_bars=None)` `[measured: that literal is accepted by __post_init__; the 0.5
   residual runs to stop/trail/time/session]`, and **never once constructed** — because
   `trail_atr_mult` is `None` in all 11 catalogue exits, every `scale_out` sums to exactly
   1.0, and `time_stop_bars` is never `None` `[measured, all three]`.
4. **Turn the trailing stop on at all.** Implementation has existed all along at
   `engine.py:451-462`; never exercised.
5. **Leave a residual runner** (`sum(scale_out) < 1`). Legal `[repo-verified: base.py:235-236]`,
   never generated.
6. **Switch the time stop off.** Never `None`.
7. **Vary `StrategyFilters` scope** — `days_of_week`, minutes-since-open, `sessions`,
   `volatility` as a scope gate. **One distinct identity across 314 generated strategies**
   `[measured]`. And the D43 fix is what made this safe to do; nobody has done it since
   `[repo-verified: DEFECTS.md:640-652]`.
8. **`StopKind.FIXED_TICKS`** — the one stop kind whose R unit is not volatility-scaled, and
   therefore the natural control arm for B-2's claim that this repo's R normalisation *is*
   volatility targeting. Present in the enum, absent from the catalogue.

**The caution that applies to every Tier-1 item, from D15:** the exit index is sampled jointly
with the rule set, so only 93 of 8,317 shipped rule sets exist with two different exits
`[repo-verified: DEFECTS.md:184-187]`. Each of these must be run as a **paired re-emission of
the same rule sets**, not as a fresh sample, or the answer is confounded with the entry.

**What is NOT on this list, and why.** No entry family qualifies. III-1's canonical Donchian
entry needs a new condition (≈12 lines over the already-computed `hh20`/`ll20`), III-2's OCO
bracket needs an order-type object, III-5 needs sequence support, III-6 is settled negative.
**The whole of Q2's answer on my track is operating rules, not signals** — which is exactly
what a track called "path and operation" should return, and it is the strongest argument for
DIVISION's decision to cut by mechanism.

### Q3 — Which single missing primitive unlocks the most families in your class?

**By the letter of the question (families): `ExitModel.exit_conditions` plus a
`FeatureSnapshot` in `_manage` — 5 of 19 Class III families.**

Unlocks III-1 (the canonical CTA exit and stop-and-reverse), III-2 (exit on expansion
exhaustion rather than a fixed R), III-4 (exit *at the mean*, which is the whole point of a
band-reversion trade and is currently impossible — `TargetKind` has no anchor to a band or
VWAP `[repo-verified: base.py:182-184]`), III-11 (condition-based and no-target/trail-only
exits), III-13 (re-entry on a *fresh* trigger rather than the same one). Partially III-5.
The plumbing is cheap: `self.frame.snapshot(i)` is already built once per bar at
`[repo-verified: engine.py:310-311]` — it only needs hoisting above step 2.

**But I am flagging a unit inversion, because the manager said this answer should be decided
by measurement rather than taste and the measurement depends on the unit.** Counted in
**operating axes** — which is the unit my track actually works in, and the unit
`R3_operating_vocabulary.md` enumerates — the winner is different and by a wide margin:

| primitive | families unlocked (of 19) | operating axes unlocked (of 62) |
|---|---|---|
| `ExitModel.exit_conditions` + `snap` in `_manage` | **5** | 6 (M6, M7, X2, C5, plus two target variants) |
| **`account: AccountState` on `BacktestEngine` + open-risk-by-correlation-group** | 3 | **17** (S1, S2, S4, S5, S7, S8, P1–P9, A2, A3) |
| `Dict[str, List[_OpenPosition]]` (multi-position) | 2 | 3 (M8, M9, and half of M7) |
| `Condition.lookback_window` | 1 fully, 4 degraded | 2 |

The reason for the inversion is structural and worth the manager knowing: **DIVISION's Class
III list collapses the entire portfolio-and-governance block into one row (III-14) while
splitting the entry families finely.** III-14 alone contains seven distinct operating
sub-families (heat, correlated exposure, daily loss limit, giveback, trade cap,
consecutive-loss stand-down, equity-curve trading), each of which a real desk treats as a
separate rule.

**My recommendation, stated plainly so the manager can reconcile it against R1's and R2's
answers:** for the build-and-acquire order, rank `account: AccountState` first. It is the
primitive that makes my track's *subject* — the operating layer — measurable at all, it is
one constructor parameter plus one dict, and it converts 17 of 62 operating axes from
unmeasurable to measurable. `ExitModel.exit_conditions` ranks second: it unlocks more
*families*, and those families are entry families whose expressibility is a signal question
rather than an operating one.

**And a note on the reconciliation the manager wants to run.** If sequence support (D37)
unlocks *n*, a multi-series frame unlocks *m*, and an aggressor flag unlocks *k*, then my
track's honest contribution to that arithmetic is: **sequence support unlocks 1 family fully
and degrades 4 more in Class III — it is not the answer for my class.** The answer for my
class is not a data primitive at all. It is a constructor parameter.

---

# Appendix — claim-marker census

The manager's cover note said he would read the ratio between the three markers, so here it is
measured rather than asserted.

`[measured: for f in R3_path_operation.md R3_operating_vocabulary.md; do grep -o
"\[general knowledge\]" $f | wc -l; grep -o "\[repo-verified:" $f | wc -l; grep -o
"\[measured:" $f | wc -l; done]`

| file | `[general knowledge]` | `[repo-verified: path:line]` | `[measured: cmd → result]` |
|---|---|---|---|
| `R3_path_operation.md` | 64 | **188** | 60 |
| `R3_operating_vocabulary.md` | 2 | **74** | 33 |
| **total** | **66** | **262** | **93** |

262 path-cited repo claims and 93 measured commands against 66 general-knowledge claims. The
general-knowledge claims are concentrated in the "How it is operated" and "How it dies" fields
of the R3-D1 catalogue, which is where DIVISION §4 requires them and marks them as such.

**What I ran, in full** (DIVISION §8 compliance). Every command was a read, a `grep`, a
`dataclasses.fields` inspection, one `json.load` of an existing artefact, or
`generate_strategies('MGC', [5,15,60,240], max_total=400)` — used once, for reachability, and
`max_total` was 400. **I ran no `run_backtest`, no `run_portfolio`, no sweep, and produced no
expectancy or z-score of my own.** Every comparative statistic quoted in this file is cited
from an existing artefact with its path. **I made no write of any kind under `csv/`**; the only
`csv/` access was `head -1 csv/raw/MGC_1h.csv`.

## Things I deliberately did not do

- **I did not re-derive the win-rate/payoff cancellation** (`BRIEF.md` rule 3, DIVISION §5.9).
  It is labelled once as Channel 1 in Part B-3 and eight axes are assigned to it in R3-D4
  without re-argument.
- **I did not re-argue any of the eight settled rules.** Where my Channel-3 analysis touches
  rule 3 I state explicitly what I am and am not claiming (Part B-3): rule 3 is a statement
  about gross geometry and remains correct; the cost channel is a second, monotone effect the
  rule leaves on the table, and it is a drag rather than an edge.
- **I did not audit another track's surface.** I read `features.py:921-926` and `:246, 316-325`
  only to close a look-ahead question about *my* code (`engine.py`'s trail and slippage
  scaler), and I say so at A-11 point 6 with the caveat that `_align`'s construction is R1's.
  I touched no `vwap`, `profile`, `orderflow`, `volume`, `liquidity` or `imbalance` condition
  (DIVISION §5.3, §5.4).
- **I did not annex a family.** III-15's curve and carry half is R2's (DIVISION §5.6) and I
  claim only the operational half, saying so in the entry.
- **I did not re-derive the 79 conditions or the 19 groups** (DIVISION §5.8). Appendix A is
  cited.

---

# ROUND-2 APPENDIX — corrections to this file, and four new findings

Appended in round 2. Everything above is round-1 text with the citation fixes described in
CORRECTION 1 applied in place. The design work these findings feed is in
`research/R3_pairing_design.md`; the fidelity ruling on BT3-ALGO-1 is
`msgs/03_R3_BT3_re-verify-ALGO-1.md`. My two questions are canonically **R3-Q1** and **R3-Q2**
per `REGISTRY.md` — a bare `Q2` or `Q3` from me above this line is malformed and resolves via
that table.

## CORRECTION 1 — the strength census: 4 was wrong, 5 is right, and only 4 of the 5 can reach `Strategy.strength`

I reported **4** conditions grading `strength`. The manager measured **5**. The manager is right.
Every citation above is corrected; this records why I was wrong, because the root cause is a
measurement method that quietly excluded a case rather than a transcription slip.

My census was

```
graded = [n for n,c in sorted(CONDITIONS.items())
          if re.search('strength', inspect.getsource(c.fn).split('def ',1)[-1])]
```

`.split('def ',1)[-1]` strips the decorator, and the fifth condition is
**`candle_close_strength`**, whose function is `_candle_clv` and which passes its grade
**positionally and unnamed** as the fifth argument to `ConditionResult.yes`:

```
return ConditionResult.yes(LONG if clv > 0 else SHORT,
                           f"close at {clv:+.2f} of range", round(clv, 3),
                           abs(clv))
```

`[repo-verified: futures_agents/strategies/library.py:1447-1449]`. The literal string
`strength` never appears in the body, and the one place it *did* appear — the condition's own
name in the decorator — is exactly what my split discarded. A textual census for a value passed
positionally is the wrong instrument, and mine would have missed any other condition doing the
same.

**The corrected finding, measured properly:**

`[measured: from futures_agents.strategies.library import CONDITIONS → len(CONDITIONS) = 79;
Counter(c.kind.name) = {SIGNAL: 53, FILTER: 26}; group 'candlestick' = exactly
['candle_reversal','candle_engulfing','candle_decisive_close','candle_close_strength',
'inside_bar_compression']; kinds = SIGNAL, SIGNAL, SIGNAL, SIGNAL, **FILTER**]`

**And the correction sharpens the conclusion rather than only fixing a number.** `strength_sum`
is accumulated **only inside the `signal_conditions` loop** `[repo-verified: base.py:686]`; the
`filter_conditions` loop discards `res.strength` entirely `[repo-verified: base.py:670-675]`.
`inside_bar_compression` is `kind=ConditionKind.FILTER` `[repo-verified: library.py:1452]`. So:

> **5 of 79 conditions grade `strength`. Only 4 of them are SIGNALs, so only 4 can ever reach
> `Strategy.strength = strength_sum / n_signals` `[repo-verified: base.py:766]`. The fifth is
> computed on every bar it fires and thrown away.** 49 of 53 SIGNAL conditions return the 1.0
> default; ~74 of 79 conditions return it overall.

`Cov(strength, R) = 0` by construction still holds, and now has a second mechanism behind it:
one of the five graded conditions is structurally unable to contribute at all. The Channel-4b
verdict in R3-D4 and the `~50-condition rewrite` sizing in D5 item 10 are unaffected — 49 is
still ~50.

## CORRECTION 2 — B-3(c) worked the sizing floor at the wrong budget. BT3 measured it; the real figure is $240

B-3(c) computed the integer-contract floor against "a $375 ceiling, `max_dollar_risk = 500`" and
tabulated max stop distances at $375 and $500. **The account never gets that much.** At full
equity the binding term is `base_risk_pct_of_buffer`, not the 0.75%-of-equity ceiling:

```
risk_budget = min(usable_buffer * 0.06, equity * 0.0075, max_dollar_risk)
            = min(4000 * 0.06,       50000 * 0.0075,  500)
            = min(240,               375,             500)   = $240
```

`[repo-verified: risk/manager.py:153-158]`, `[measured: AccountConfig().usable_buffer(50000,
50000) → 4000.0]`. **Credit to BT3**, who derived this while scoping ALGO-1 and whose
`OPENING_BUDGET` constant is correct. My tables at the $375 and $500 columns overstate the
permitted stop by 56% and 108% respectively, which made the floor look *less* binding than it
is. The direction of the error is against my own claim, and the corrected figure strengthens it:
BT3 measures **35.4% of 21,954 stored trades deleted by `contracts_for`'s integer floor at the
opening budget, before any path dependence** `[measured: BT3 algo1_report.json
static_integer_floor → 7,767 / 21,954 deleted at $240]`.

Two further things from BT3's replay that bear on Part B and that I am recording here because
they are measurements my file predicted the need for but could not supply:

- **The floor's bite is overwhelmingly conditional on symbol and bar size**, ranging from 2.2%
  (MES_60) to 99.4% (MGC_240) `[measured: BT3 `static_integer_floor.by_symbol_tf`]`. This is
  R3-D4's `Integer-contract floor` row — Channel 2, selecting on stop distance — confirmed with
  a number for the first time.
- **The account has an absorbing dead-but-not-failed state at a drawdown from peak of \$2,800**,
  where the permitted budget falls to \$21.60 against `min_dollar_risk = 25` and stage 7 vetoes
  every proposal *before* `contracts_for` is reached `[repo-verified: risk/manager.py:325-329]`,
  `[measured: budget scan over drawdown 0..4000 in \$10 steps → crossing between \$2,790 and
  \$2,800]`. Equity can then only move via already-open positions, `peak_equity` never falls, and
  `has_failed` stays False because equity (~\$47,200) is above `failure_equity` (\$45,000). **So
  the \$5,000 max-drawdown failure threshold is unreachable for this population; `min_dollar_risk`
  kills the account first.** Derived in `msgs/03_R3_BT3_re-verify-ALGO-1.md`. It does not touch
  any finding above, because R3-B-1 establishes that nothing under `futures_agents/backtest/`
  imports anything from `futures_agents/risk/` — but it is the sharpest illustration of why
  B-1 matters.

## CORRECTION 3 — D5 item 6 (`StopKind.FIXED_TICKS`) is not a zero-new-code item

I billed it Tier 1, "one field". The field is one field, but the *comparison* is not free:
`FIXED_TICKS` changes `stop_price`, which changes `risk_points`, which changes **the R unit
itself**. The two arms of a `FIXED_TICKS` pair do not share a denominator, so differencing R
between them differences two different quantities. It needs a re-based statistic — both arms'
dollar outcome divided by the **control** rule set's `risk_points`, computable from
`Trade.entry_price` and `Trade.initial_stop` `[repo-verified: engine.py:502-512]` but a
post-processing step, not a configuration change. Specified in `R3_pairing_design.md` §5.4.
It is the only one of the eight items with this property.

## A-13 (NEW) `dataclasses.replace` inherits the cached `_id`, silently merging both arms of a pair

Full statement and measurements in `research/R3_pairing_design.md` §2; filed for a defect number
as `R3-REQ-1`. In one paragraph: `Strategy._id` is a real dataclass field
`[repo-verified: base.py:585]` memoised by `strategy_id` via `object.__setattr__`
`[repo-verified: base.py:622]`; `generate_strategies` populates it before returning, because its
dedupe is `seen.setdefault(st.strategy_id, st)` `[repo-verified: combinator.py:719]`; so
`replace(s, exit=...)` **without `_id=None`** yields a strategy claiming `s`'s id
`[measured: replace(S[0], exit=replace(S[0].exit, trail_atr_mult=2.0)).strategy_id ==
S[0].strategy_id → True]`. `run_many` keys `results` `[engine.py:277-281]`, `open_pos` and
`pending` `[engine.py:282-283]` and the skip guard `[engine.py:304-309]` all by that id, so the
two arms collapse into one row whose trades are a path-dependent interleaving of both exit
models. **The measured difference between arms is exactly zero — a false null, indistinguishable
from the axis doing nothing.** Third instance of the identity family after `ExitModel.label` and
D43, and **not fixed by D43**, which repaired what goes into the hash while this defeats the hash
by not recomputing it.

## A-14 (NEW) The unit of pairing on this engine is the rule set, never the trade

`engine.py:304-309` skips a positioned strategy, so any axis that changes holding duration
changes which later bars the arm is flat for. Two arms of a gate-identical pair therefore agree
on trade 1 and **fork at the first trade whose duration differs**. Measured on the only paired
re-emission that exists on disk — the geo study's 22 rule sets × 2 exits × 8 cells × 3 slices =
258 pairs — the arms share a **median 61.8% of their entry timestamps**, only 17 of 258 reach
90%, and the median trade-count ratio is 1.332 `[measured: entry-timestamp Jaccard over
stops_cache.json; full table in R3_pairing_design.md §4.3]`. Pairing on the intersection is
forbidden: it conditions on which bars both arms were flat for, which is a function of prior
outcomes — a selection on the dependent variable. Trade-level pairing needs an exogenous-entry
harness (`R3-REQ-2`), which is cheap precisely because `_manage` needs no `FeatureSnapshot`
`[repo-verified: engine.py:377-378]`.

A-14 also fixes exactly which `ExitModel` fields can move the entry set, which round 1 left
implicit: `stop_kind`, `stop_mult`, `stop_pad_ticks` always; `target_kind`, `anchor_mult`,
`min_reward_risk` only when `target_kind is not R_MULTIPLE`; **`targets_r` never** (the
`if not targets: return None` gate at `[repo-verified: base.py:726]` is unreachable, because
`__post_init__` forbids an empty `targets_r` `[repo-verified: base.py:229-230]` and both the
R_MULTIPLE branch and the anchored fallback return one price per element
`[repo-verified: base.py:333-339]`); and `scale_out`, `breakeven_at_r`, `trail_atr_mult`,
`time_stop_bars`, `exit_at_session_close` never, because they are read only inside `_manage`
`[repo-verified: engine.py:382-476]`.

## A-15 (NEW) At the reachable generation scale the D15 confound is total, not partial

D15's "93 of 8,317 rule sets exist with two different exits" invites the reading that a small
paired subset could be salvaged. At `max_total=400` there is none:

`[measured: generate_strategies(sym,[5,15,60,240],max_total=400); rule sets counted by the
nine-part `strategy_id` hash with one slot blanked →`

| symbol | strategies | rule sets with ≥2 exits | rule sets with ≥2 filter scopes |
|---|---|---|---|
| MGC | 314 | **0** | **0** |
| MNQ | 314 | **0** | **0** |
| MES | 336 | **0** | **0** |
| MCL | 296 | **0** | **0** |

`]`

Every generated strategy is its own unique rule set carrying exactly one exit and one filter
scope. The zero in the right-hand column is **A-5 restated as its consequence**: the scope
vocabulary being inert in the generation path means not merely "scope is never varied" but "no
two shipped strategies are ever a scope pair". The compensation is that n_pairs equals the whole
generated population — **1,260 pairs across four symbols** — which is more than an order of
magnitude better than the 93 D15 leaves behind.

## A-16 (NEW) The trailing-stop path audited: clean on look-ahead, lagged by one bar, and A-2's consequence is a signed mixture

A-11 gave the position lifecycle a clean bill on look-ahead, checked five ways. That bill could
not cover the trailing stop, because the trail **has never executed** (A-1) and so had never
been read by anyone. I read it, because item 4 of §7 Q2 depends on it.

**Clean on look-ahead.** The trail's ATR comes from
`a = col[self.frame.tf_index(i, pos.signal.primary_tf)]`
`[repo-verified: engine.py:453-457]`, and `tf_index` is documented and implemented as "index of
the newest **completed** `timeframe` bar at `base_index`" `[repo-verified: features.py:921-926]`.
No forming-bar ATR, no future data. A-11's bill extends to this path.

**Lagged by one bar, and it must be declared with any item-4 number.** The trail is computed from
`bar.high` / `bar.low` at step 3 `[repo-verified: engine.py:458-462]`, *after* step 1 already
ran this bar's stop check `[repo-verified: engine.py:404-422]`. So a stop the trail tightens is
first tested on bar *i+1*. That is **conservative** — favourable to the strategy — and makes the
engine's trail strictly coarser than a live intrabar trail, so it will systematically
under-capture. Not a defect; a fidelity statement that changes how a null is read.

**A-2's consequence is worse than "the label is wrong".** `reason = BREAKEVEN if
pos.breakeven_moved and |pos.stop - entry| < tick_size else STOP`
`[repo-verified: engine.py:419-421]`. Once the trail ratchets the stop away from entry that
condition fails, so **a trail exit reports as `STOP`**. `STOP` then becomes a mixture of two
mechanisms with **opposite signs** — an initial-stop hit near −1R, and a trail hit that has
locked in a gain. Every exit study in this repo reads the exit-reason histogram and its
per-reason mean R, and that mean moves with the mixing weight even when nothing real has
changed. **So D5 item 13's four-line `ExitReason.TRAIL` fix is a hard prerequisite for item 4,
not a nicety**: without it an item-4 result is not weak, it is unattributable.
