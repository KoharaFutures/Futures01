# EF1 — the 18:00 ET → 16:00 ET session-window rule, and whether it can be trusted

**I am the gate. EF2–EF5 cannot report a profitability number until this harness validates.**
This file says what was built, what it was shown to reject, and where it is still weak.
Substrate: `data/archive/` throughout (the programme substrate per `BRIEF.md`'s BT1-REQ-1 ruling).
Every number names its timeframe, because archive span depth is a per-timeframe fact.

---

## Harness components — registry kind `EF1-H<n>`

| id | path | what it is |
|---|---|---|
| **EF1-H1** | `edge/EF1/code/session_window.py` | the rule: `classify_bar`, `session_end_indices`, `SessionWindowEngine`, `violations`, `prefix_invariance_report`, `with_exit`/`assert_distinct_ids` |
| **EF1-H2** | `edge/EF1/code/measure.py` | the three-arm validation run over real bars |
| **EF1-H3** | `edge/EF1/code/prefix_check.py` | prefix invariance on real bars, two levels |
| **EF1-H4** | `tests/test_ef1_session_window.py` | 57 known-answer / regression checks |
| **EF1-H5** | `edge/EF1/code/saturate.py` | the saturation test — a position open on **every** bar |

### How EF2–EF5 use it

```python
import sys; sys.path.insert(0, "workspace/roundtable/edge/EF1/code")
from session_window import (SessionWindowEngine, violations, flat_exit_keys,
                            is_session_flat, with_exit, assert_distinct_ids)

eng = SessionWindowEngine(frame, CostModel(spec))        # strict=True by default
results = eng.run_many(strategies)
trades  = [t for r in results.values() for t in r.trades]
assert violations(trades, flat_exits=flat_exit_keys(eng)) == []
```

- `strict=True` (default) makes the engine **raise** `SessionWindowViolation` rather than emit a
  trade that breaks the window. Do not pass `strict=False` except to diagnose.
- `is_session_flat(trade)` is true when the 16:00 flat closed it. It reuses
  `ExitReason.SESSION_CLOSE`, which is unambiguous inside this engine because `allow_overnight` is
  forced `True` and the shipped RTH-close exit at `engine.py:470` is gated on
  `not allow_overnight`, so it can never fire.
- Build paired arms with `with_exit(...)` and call `assert_distinct_ids(arm_a, arm_b)` **at
  emission** — D48.
- Base the frame on the **finest** series you have: the flat fires on base bars, so a 60m base puts
  it at the close of the 15:00–16:00 bar, which is the 16:00 print.

---

## EF1-F1 — the rule IS expressible without touching `futures_agents/`. Nothing in it was edited.

`SessionWindowEngine` subclasses `BacktestEngine` and overrides three methods:

- **`_open_position`** — the entry veto. `run_many` deletes the pending entry whether or not a
  position comes back `[repo-verified: engine.py:291-295]`, so returning `None` drops it cleanly and
  **leaves `signals_generated` incremented** — the veto is visible in the result, not silent.
- **`_manage`** — the flat. Delegates to `super()` first on every bar, so stop-before-target and
  stop-before-flat are inherited rather than reimplemented.
- **`_close`** — the strict emission audit.

`allow_overnight=True` is forced, not a parameter: under this rule a position is expected to survive
its contract's RTH close, and leaving the shipped 13:30/14:30 exit armed would flatten it there.

The coupling is real — three underscore-prefixed methods — and it is guarded, not hoped about.
`assert_hooks_reachable()` reads `BacktestEngine.run_many`'s source and fails if it stops calling
`_open_position` or `_manage`, checks `_manage`'s signature, and checks that the shipped RTH-close
exit is still gated on `allow_overnight`. `EF1-H4` runs it.

**Full repo suite: 878 → 884 passed** (the 6 new = my file's growth). No existing test touched.

---

## EF1-F2 — the dispatch's three premises verified; one EDGE_BRIEF premise is **wrong**

Verified (`bursts/01`): `exit_at_session_close` fires at the contract's own RTH close
`[engine.py:470-473]` — **13:30 MGC**, 14:30 MCL, 16:00 MES/MNQ; it is gated on
`not self.allow_overnight`; and `allow_overnight=True` has no call site
`[measured: grep → engine.py:233,241,470 only]`.

**The correction.** `EDGE_BRIEF.md:26-30` says "every one of ~2.97M prior evaluations was flat by
its contract's RTH close." **False, and falsified by the shipped default itself.** The gate is
`exit_model.exit_at_session_close and not self.allow_overnight` — an `and` — and
`ExitModel.exit_at_session_close` **varies across the generated population**
`[measured: generate_strategies(sym,(60,240),max_total=400,seed=20260922) → MGC 184 strategies, 84
with exit_at_session_close=False; MNQ 185, 90 with False]`. For those the session exit never fires
and the position runs until stop/target/time/EOD — i.e. **overnight, with no session control at
all.** On real bars, arm A (the shipped default) holds across 16:00–18:00 on 139/626 MGC trades,
595/2626 MCL, 986/1292 MES, 860/1403 MNQ, with max holds in the hundreds of days.

Honest form: **no prior evaluation had a 16:00 ET flat, and roughly half the generated population
had no session exit at all.** The regime is still unmeasured; the reason is not the one given. This
matters because "all prior work was intraday-only" would make arm A a clean intraday baseline, and
it is not one.

---

## EF1-F3 — the rule is NOT expressible on 1440m, and that is arithmetic

`align_bucket` puts a daily bucket at 18:00 ET the previous evening
`[repo-verified: futures_agents/data/bars.py:139-143]`, so 16:00 ET falls **22 hours into every
daily bar**; the entry fill and the flat land inside the same bar and OHLC cannot price hour 22.
`[measured: 4008/4008 MGC 1440m bars INTERIOR; 1863/1863 MES and MNQ; MCL's single row]`
`SessionWindowEngine` raises `SessionGridError` rather than inventing a price. With the EDGE_BRIEF's
own 22-hour arithmetic, **there is no daily-bar strategy in this programme.**

Every other grid is expressible: 5m/15m/30m/60m/240m have **zero** INTERIOR bars on all four
symbols. The 60m grid is not uniformly on the hour — 20 bars per symbol are stamped `:30`, all on
half-day holiday sessions — so the rule classifies per bar and never assumes the grid.

---

## EF1-F4 — the validation found **two** real defects in EF1's own code. Both are the gate working.

### EF1-D3: the first build shipped 33 violations (`bursts/03`)

The pure per-bar rule can only fire on a bar that **exists**. On a session that shuts before 15:00
neither branch gets a bar to act on and the position runs straight through. 33 `SPANS_WINDOW`
violations, all `primary_tf=240m`, all on early-close dates. EF3 found the same defect
independently, on a `rth_only=False` population, and measured a **71-hour hold** —
`msgs/EF3-01_EF1_session-rule-misses-early-close-sessions.md`.

### EF1-D4: the first *fix* keyed on the ET calendar date and caught only 10 of 19 dates

Found by `EF1-H5` on its first run, caught by the strict emission check at the offending trade:

```
SessionWindowViolation: MES: entry=2024-11-27T18:00-05:00 exit=2024-11-29T12:30-05:00
                        SPANS_WINDOW  reason=SESSION_CLOSE bar_class=OUTSIDE
```

**2024-11-28 has no bars at all**, so an ET-date map has no entry for a date that does not exist,
and a Thanksgiving-eve position ran to Black Friday 12:30 across two deadlines.

**The fix, component 1b — `session_end_indices`.** For each **CME trading day** (18:00 roll, the
repo's own `trading_day`) with no `ON_BOUNDARY`, `IN_WINDOW` or `INTERIOR` bar, the day's **last**
bar is the forced flat. This reproduces EF3's 19 dates exactly on MES and MNQ:

```
2024-11-28 2024-11-29 2024-12-24 2025-01-09 2025-01-20 2025-02-17 2025-05-26 2025-06-19
2025-07-03 2025-07-04 2025-11-27 2025-11-28 2025-12-24 2026-01-19 2026-01-30 2026-02-16
2026-04-03 2026-06-19 2026-07-03
```

MCL has **27** such trading days, because of EF1-F8.

**What component 1b costs, stated rather than buried.** It reads bar **timestamps only** — no price
at any index — so the price-look-ahead invariant is untouched, and
`test_session_end_map_is_a_function_of_timestamps_only` proves it by perturbing every OHLC value
and asserting the map does not move. But it is not a pure per-bar function, so
`prefix_invariance_report` returns **three** numbers:

| number | guarantee |
|---|---|
| `classification_mismatches` | must be **0** — `classify_bar` is a pure function of one bar |
| `session_end_mismatches_on_cut_trading_day` | the characterised boundary effect, counted |
| `session_end_mismatches_off_cut_trading_day` | must be **0** — once a prefix passes into the next trading day the day's bar list is complete and cannot change |

The live equivalent of this information is the exchange session calendar, published weeks ahead.
This is the **only** look-ahead of any kind in the harness.

**The series' last trading day is excluded from the map**, because it is truncated by the end of the
data rather than by an exchange holiday. Including it would close the final position as a flat the
rule never reached, and the flag would move with every prefix length — turning an artefact of where
the data stops into an apparent look-ahead.

### Why a population audit was the wrong instrument, and what replaced it

EF3's `rth_only=False` population reached sessions EF1's `rth_only=True` run never entered in.
**Coverage is a property of the signals, not of the engine**, so two agents with different
populations get different answers about the same code and cannot tell whose engine is wrong.
`EF1-H5` removes the variable: a stub signals on every bar with a stop 50% away and a target 500R
beyond it, so a position is open on every bar and the only thing that can close one is the session
rule. It found EF1-D4 on its first run, on the first offending bar.

---

## EF1-F5 — the gap-honest fill, and the one bar that justifies it

R3 found every time-based and session exit in this repo closes at `bar.close` with **zero slippage
by construction** `[repo-verified: engine.py:467,473,476]`. The 16:00 flat fires on 59.6–86.3% of
all positions, so inheriting that would understate the cost of the programme's defining rule on
most trades.

| bar class | fill | slippage |
|---|---|---|
| `ON_BOUNDARY` | `bar.close` — the 16:00 print | market-order (`is_stop=True`), adverse, + thin-book when outside the contract's RTH |
| `IN_WINDOW` | `bar.open` — the deadline passed with no print, so the resting order fills at the first one, gap and all | same, **except** none when the open already gapped through the stop, which is then a `STOP` at the open per `engine.py:410-411` |
| session-end (1b) | `bar.close` of the session's last bar | as `ON_BOUNDARY` |
| `INTERIOR` | — | raises |

**MCL 60m, 2026-03-06** has no 14:00 and no 15:00 bar; the last print before the deadline closes at
**91.28** and the 16:00 bar opens at **90.90**. Closing at `bar.close` of the last bar before would
invent 38 cents — $38/contract, a third of an R on a 100-tick stop
`[measured: data/archive/MCL_60m.jsonl]`. That single bar is why the `IN_WINDOW` branch exists.

The thin-book flag fires on MGC and MCL flats and not on MES/MNQ, because 15:00–16:00 ET is outside
MGC's 08:20–13:30 and MCL's 09:00–14:30 RTH and inside MES/MNQ's 09:30–16:00. That is correct —
gold's and crude's 15:00 book genuinely is post-settlement — and it means **the flat costs MGC and
MCL more than it costs the index complex.** Do not read that as a symbol effect.

---

## EF1-F6 — how much the rule does: it closes **59.6–86.3%** of all positions

`[measured: EF1-H2, data/archive 60m base, tfs 60m+240m, max_total=400, seed 20260922]`

| symbol | strategies | arm A trades / viol | arm B trades / viol | arm C trades / **viol** | closed by the rule | share | arm C median / max hold |
|---|---|---|---|---|---|---|---|
| MGC | 184 | 626 / 139 | 463 / 360 | 554 / **0** | 420 | **75.8%** | 180m / 300m |
| MCL | 167 | 2626 / 595 | 2011 / 1186 | 2186 / **0** | 1303 | **59.6%** | 120m / 1260m |
| MES | 190 | 1292 / 986 | 1292 / 1056 | 1380 / **0** | 832 | **60.3%** | 180m / 300m |
| MNQ | 185 | 1403 / 860 | 818 / 839 | 985 / **0** | 850 | **86.3%** | 180m / 900m |

Arm A = as shipped. Arm B = `allow_overnight=True`, no window rule. Arm C = the rule.

**The rule is emphatically not inert**, and every one of those closures is a position that had
**not** hit its stop, its target or its time stop on that bar — the `ON_BOUNDARY` branch runs
`super()._manage` first and only flattens when it returns nothing. So the count *is* the number of
positions closed that would otherwise have run on, with no counterfactual needed. The paired check
confirms it: `flats_where_arm_b_exited_on_the_same_bar = 0` on all four symbols.

How far they would have run, paired on `(strategy_id, entry_index)` against arm B, in **extra base
(60m) bars**:

| symbol | paired flats | min | median | mean | max | arm B's reason for those positions |
|---|---|---|---|---|---|---|
| MGC | 344 | 1 | **20.5** | 54.7 | 195 | STOP 135, BREAKEVEN 88, TARGET 64, TIME 49 |
| MCL | 1177 | 1 | **12** | 19.7 | 416 | STOP 617, BREAKEVEN 326, TARGET 221 |
| MES | 583 | 1 | **18** | 25.1 | 155 | STOP 263, BREAKEVEN 171, TARGET 142 |
| MNQ | 525 | 1 | **43** | 79.4 | 353 | STOP 201, BREAKEVEN 159, TARGET 127 |

### The consequence EF2–EF5 must carry on every single row

At 59.6–86.3% clock exits, **the strategy's stop-and-target geometry barely gets to act.** Arm C's
exit-reason census makes it plain — MNQ: `SESSION_CLOSE 850, STOP 104, TARGET 28, BREAKEVEN 3`. A
ranked top-10 built on this harness is ranking **entry signals scored on a clock exit**, not
strategies. It also means the exit axis is close to unmeasurable under this rule at the generated
default, and an "exits make no difference" result would be that, not a finding.

---

## EF1-F7 — the entry veto is inert on MGC and MCL at the generated default, and why

`[measured: entries_vetoed_in_window — MGC 0, MCL 0, MES 683, MNQ 424]`

`StrategyFilters.rth_only` defaults `True` and the generators never vary it (EF2 measured 184/184
MGC, 167/167 MCL; R3-A-5 and R1's 314/314 agree), and `passes` rejects any non-session-scale bar
outside `is_rth(ts, spec.rth_open, spec.rth_close)` `[repo-verified: base.py:413]`. MGC's RTH ends
13:30 and MCL's 14:30, both **before** 16:00, so no MGC or MCL fill can land in the window and there
is nothing to veto. MES/MNQ RTH runs to 16:00, so their last RTH bar's successor *is* the 16:00 bar.

**This is the veto working, not broken** — `EF1-H4` proves it by construction. But the measured
count is a property of `rth_only`, not of the rule, and a `rth_only=False` run vetoes far more (EF3
measured 626 on MES). D24 measured `rth_only=False` as buying 2–4× sample while **costing**
expectancy, so it is a paired arm to test, not a switch to flip.

The corollary the manager already flagged and I confirm: at the generated default the rule does not
unlock overnight *entries*; it unlocks holding an RTH entry past the contract's RTH close to 16:00 —
**+2.5h on MGC, +1.5h on MCL, and on MES/MNQ, whose RTH close already is 16:00, only the honest
slippage.** MGC's and MES's arm-C max hold of 300m (5h) is that constraint, visible.

---

## EF1-F8 — substrate defect: MCL 60m is structurally thin for two months

`[measured: bars per ET date over data/archive/MCL_60m.jsonl]` 2026-01-12 → 2026-03-10: **17 ET
dates carrying 1 to 5 bars each**, starting at 03:00 or 05:00, against ~20 on a normal day. MGC,
MES and MNQ do not have this. Not caused by anything EF1 does and not fixed here. Any MCL 60m
expectancy over that window is computed on a series with most of its bars missing, and MCL is
already the cost-fragile contract (EDGE_BRIEF guardrail 8).

---

## EF1-F9 — D48

`with_exit(strategy, **exit_fields)` passes `_id=None`; `assert_distinct_ids(*arms)` fails on any
shared id, including an arm colliding with itself. `EF1-H4` reproduces the collision first
(`test_d48_naive_replace_collides_and_with_exit_does_not` asserts the naive `replace` yields an
**identical** `strategy_id`) and then shows the fix. Assert at emission: after the run both arms
have already written to one key and the evidence is gone.

---

## Defect candidate for the manager — `futures_agents/` is not EF1's to edit

**Zero-slippage exits at `engine.py:467, 473, 476`.** `TIME`, `SESSION_CLOSE` and `END_OF_DATA` all
close at `bar.close` with no slippage term — R3's finding, sharpening D13. EF1's flat does not
inherit it. Measured exposure under this programme's rule:

- **60m / 240m: the time stop is inert.** `time_stop_bars` generates at 30–120 *primary* bars, and
  the rule caps a hold at 22h, so 30 primary bars (30h at 60m, 120h at 240m) is never reached. The
  swing half is not exposed. Arm C's census confirms: zero `TIME` exits on all four symbols.
- **5m / 15m: live.** 30 primary bars = 2.5h at 5m, well inside the cap.

So the recommendation is narrow: any **scalp** row whose exit reason is `TIME` carries an unmodelled
exit slippage of one market order — on MNQ (0.25 tick, $2/point) ~$0.75–2 a contract, which against
a 4-point ($8) stop is 9–25% of one R.

---

## What I do NOT claim

The `mean_net_r` columns in `workspace/developer/ef1_validation_swing_60m.json` are diagnostics, not
results. They come from 167–190 generated strategies with **no placebo, no deflation threshold and
no forward test**, and arm C beats arm B on two symbols and loses on two. Anyone quoting them as a
profitability finding is misusing this file. They are there so that a later run which disagrees is
detectable.
