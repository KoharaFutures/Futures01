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
