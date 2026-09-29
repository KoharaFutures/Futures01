# EF1 — the 18:00 ET → 16:00 ET session-window rule, and whether it can be trusted

**I am the gate. EF2–EF5 cannot report a profitability number until this harness validates.**
This file says what was built, what it was shown to reject, and where it is still weak.
Substrate: `data/archive/` throughout (the programme substrate per `BRIEF.md`'s BT1-REQ-1 ruling).
Every number names its timeframe, because archive span depth is a per-timeframe fact.

---

## Harness components — registry kind `EF1-H<n>`

**`REGISTRY.md:63-65` allocated `EF1-H1..H3` on my behalf while I was working, and its allocation
is authoritative — four agents are already citing it. I had numbered the same space differently in
an earlier draft of this file; the registry's numbering wins and this table is the reconciliation.**

| id | what it is | where |
|---|---|---|
| **EF1-H1** | `classify_bar` — the bar classifier (`OUTSIDE` / `ON_BOUNDARY` / `IN_WINDOW` / `INTERIOR`) | `edge/EF1/code/session_window.py` |
| **EF1-H2** | `SessionWindowEngine` — the engine wrapping it | same file |
| **EF1-H3** | `violations()` — the invariant auditor, plus `flat_exit_keys()` | same file |
| **EF1-H4** | `session_end_indices` — **component 1b**, the session-end forced flat. New; this is the fix for the defect `REGISTRY.md:80` records against `EF1-H1` | same file |
| **EF1-H5** | `prefix_invariance_report` — the look-ahead control, three numbers | same file |
| **EF1-H6** | `with_exit` / `assert_distinct_ids` — the D48 guard | same file |
| **EF1-H7** | `tests/test_ef1_session_window.py` — 57 known-answer / regression checks | `tests/` |
| **EF1-H8** | `saturate.py` — the saturation test: a position open on **every** bar | `edge/EF1/code/` |
| **EF1-H9** | `measure.py` — the three-arm validation run | `edge/EF1/code/` |
| **EF1-H10** | `prefix_check.py` — `EF1-H5` over real archive bars, two levels | `edge/EF1/code/` |

`REGISTRY.md:80` says "**`EF1-H1` is currently defective and it gates four agents**." That was
correct when written. It is fixed: the defect was not in `EF1-H1` (the classifier is exact and
prefix-invariant) but in the **absence** of `EF1-H4`, which is now present. See the `## PARKED`
note at the end of this file for the evidence.

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
exit is still gated on `allow_overnight`. `EF1-H7` runs it.

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

Found by `EF1-H8` on its first run, caught by the strict emission check at the offending trade:

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
`EF1-H8` removes the variable: a stub signals on every bar with a stop 50% away and a target 500R
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

`[measured: EF1-H9, data/archive 60m base, tfs 60m+240m, max_total=400, seed 20260922]`

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

**This is the veto working, not broken** — `EF1-H7` proves it by construction. But the measured
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
shared id, including an arm colliding with itself. `EF1-H7` reproduces the collision first
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

---

# PARKED 2026-09-27

Written for someone reading cold, and specifically for **EF7**, which is reimplementing the same
rule without having read my code. If you are EF7: read §"What I would keep and what I would drop"
last, after your own results are written, so this note cannot anchor you before then.

## 1. State of the harness: green. `EF1-H1` no longer under-enforces the flat.

`REGISTRY.md:80` records `EF1-H1` as defective and gating four agents. **That is now stale.** Two
separate defects existed and both are fixed and regression-tested:

| defect | what it was | fix | regression |
|---|---|---|---|
| **EF1-D3** | the pure per-bar rule can only fire on a bar that *exists*; a session shutting before 15:00 offers none, so the position ran through. **33 `SPANS_WINDOW` violations** (MCL 18, MES 9, MNQ 6), all 240m. EF3 measured **43** of the same at 60m with a 71-hour hold; EF2 measured 17 MGC / 34 MCL cycles | **`EF1-H4`** `session_end_indices` — component 1b | `test_strict_emission_catches_the_hole_that_shipped` |
| **EF1-D4** | the first version of `EF1-H4` keyed on the **ET calendar date** and caught only 10 of 19 dates. A date with *no bars at all* (Thanksgiving) has no map entry, so a 2024-11-27 18:00 entry ran to Black Friday 12:30 — 66h, two deadlines | key on the **CME trading day** (18:00 roll, the repo's own `trading_day`) | `test_holiday_with_no_bars_at_all_still_flattens_the_evening_before` |

### The four validations, all green, all reproducible

```
EF1-H7  tests/test_ef1_session_window.py                    57 passed
EF1-H8  saturate.py  --symbols MGC,MCL,MES,MNQ --tfs 5,15,30,60,240
        TOTAL violations under saturation: 0   over-cap holds: 0
        control (shipped engine) violations: 78   <- the test has power
EF1-H9  measure.py   --base-tf 60 --tfs 60,240 --max-total 400
        MGC 0 | MCL 0 | MES 0 | MNQ 0            TOTAL arm-C violations: 0  (PASS)
EF1-H10 prefix_check.py
        L1 all four: classify_mismatches=0  session_end_off_cut=0  (on_cut=4..5)
        L2 all four: mismatches=0            TOTAL: 0  (PASS)
```

Artefacts on disk: `workspace/developer/ef1_saturation.json`,
`ef1_validation_swing_60m.json`, `ef1_prefix_invariance.json`.

Reproduce with `PYTHONPATH=/home/user/Futures01 python3 workspace/roundtable/edge/EF1/code/<x>.py`.
Each takes 3–12 minutes. `measure.py` needs ~165 s per symbol.

### Full repo suite: `2 failed, 1018 passed, 7 xfailed`

The two failures are **`tests/test_bt6_vwap_daily.py`**, not mine, and I verified they are not caused
by EF1: that file passes 14/14 in isolation, and `test_ef1_session_window.py +
test_bt6_vwap_daily.py` together give **71 passed, 3 xfailed, 0 failed**. It is an order-dependent
interaction inside the grown suite and BT6 owns the file. I did not touch it.

Related hazard, checked and currently clear: EF7 named its module `ef7_window.py`, not
`session_window.py`, so the two agents' `sys.path.insert` do **not** collide. If anyone adds a
second `session_window.py` anywhere on the path, whichever pytest collects first silently wins and
both test files then exercise one engine. EF7's own test file already comments on this.

## 2. What remains owed — and the 240m answer is "nothing, the cells are fine"

**The relayed EF6 arithmetic is wrong about 240m, and I have posted the correction as
`msgs/EF1-02_manager_240m-is-expressible-ef6-divisor-is-the-wrong-one.md`. Read it before acting on
the withdrawal.** In short:

- The rule needs **two** instants on bar boundaries: **16:00 = 960 min** (the flat) and
  **18:00 = 1080 min** (the reopen). `1320` (the window *length*) is neither, and nothing requires an
  integral number of bars inside a holding period.
- `align_bucket` aligns multi-hour buckets to **midnight** (`bars.py:136-143`), so `960 % 240 == 0`:
  **16:00 IS a 240m boundary.** Measured: 491–497 `ON_BOUNDARY` bars per symbol at 240m and **zero
  `INTERIOR`**. `EF1-H8` at 240m: 506–507 trades, **0 violations strict**, max hold 960–1200 min.
- What 240m actually loses is `1080 % 240 == 120 ≠ 0`: the `[16:00,20:00)` bucket is `IN_WINDOW` and
  vetoed, so the earliest legal entry is **20:00**, not 18:00. Effective cycle **20 h, not 22**.
  That belongs beside every 240m row as a caveat; it is not an inability to hold the rule.
- **1440m genuinely cannot carry it** and there EF6 and I agree by two routes. `SessionWindowEngine`
  raises `SessionGridError`.
- **The 33 violations were never a grid problem.** EF3 measured 43 of the identical violations at
  **60m**, where `1320/60 = 22` exactly. The mechanism is holiday coverage. EF4's "41 of 41 cycles
  clean in all six 5m/15m/30m cells" is consistent with that and not with the divisor story: those
  series span 57 days and **41 sessions, none of them a holiday**, so there was nothing for the
  defect to bite on. **The defect is holiday-only, not coarse-timeframe-only.**

So: nothing remains owed on 240m. What remains unbuilt is listed in §4.

## 3. The single next step

**Run `EF1-H8` (`saturate.py`) against EF7's engine and against EF3's `SessionEngine`, and require
0 violations and `max_hold <= 1320` from all three.** One command each, no new code.

That is the next step rather than any measurement because the whole reason this harness cost two
defect cycles is that **a population audit's coverage is a property of its signals, not of the
engine** — EF3's `rth_only=False` population reached sessions my `rth_only=True` run never entered,
which is why we got different answers about the same code. Saturation removes the variable: a
position open on every bar of the series, so the only thing that can close one is the rule. It found
EF1-D4 on its first run, at the first offending bar, where EF3's population found it as 1 of 3,717
trades. Three independent engines agreeing under saturation is a statement about the **series**;
three agreeing on their own populations is not.

## 4. Things a reader would otherwise have to rediscover

1. **`strict=True` is the default on `SessionWindowEngine`** and it is the thing that caught EF1-D4.
   `_close` audits every trade before returning it and raises `SessionWindowViolation` naming the
   trade. Do not pass `strict=False` outside a diagnostic.
2. **`violations()` defaults to NO carve-out** and that is deliberate — it is then usable on any
   engine's trades. The only exemption is `flat_exits=flat_exit_keys(eng)`, which exempts flats the
   engine itself filled at a window bar's **open** (stamped 16:00, i.e. at the deadline instant,
   compliant). `Trade.exit_ts` is the bar's *open* time (`engine.py:505`) and says nothing about
   where in the bar the fill was, so the distinction is knowable only from the engine's record —
   never infer it from a `Trade`.
3. **Two of my own *assertions* were wrong before the rule was**, and both would have misled:
   - `EF1-H8`'s cap was `22*60 - tf`, right for an `ON_BOUNDARY` flat and wrong for the `IN_WINDOW`
     gap flat (whose exit stamp is 16:00 itself). It flagged MNQ 240m's legitimate 20:00→16:00 hold
     of 1200 min as over-cap. The cap is **1320**. An over-tight check in a gate misleads as much as
     a loose one, and this one would have had me withdraw a cell that was fine.
   - `EF1-H5` classified prefix mismatches against the **ET calendar date** while `EF1-H4` keys on
     the **trading day**, reporting 18 spurious off-cut mismatches — every bar stamped 18:00–23:59.
     And `EF1-H10`'s level 2 lacked the forced-session-end-on-cut-day exclusion, giving 1 spurious
     mismatch each on MCL and MES. Both fixed; both were vocabulary, not logic.
4. **The series' last trading day is excluded from `EF1-H4`'s map** — it is truncated by the end of
   the data, not by a holiday. Including it would close the final position as a flat the rule never
   reached and would make the flag move with prefix length, turning "where the data stops" into an
   apparent look-ahead.
5. **The one look-ahead in the harness, named.** `EF1-H4` reads the whole series' bar
   **timestamps** — never a price at any index — to find trading days with no deadline bar.
   `test_session_end_map_is_a_function_of_timestamps_only` perturbs every OHLC value and asserts the
   map does not move. Its live equivalent is the exchange session calendar, published weeks ahead.
   `EF1-H5` reports the cost as three numbers and the two that must be zero are zero.
6. **`ExitReason` has no member for the flat** and `futures_agents/` is not mine to edit, so the flat
   reuses `SESSION_CLOSE`. That is unambiguous *inside this engine only*, because `allow_overnight`
   is forced `True` and `engine.py:470` gates the shipped RTH-close exit on `not allow_overnight`.
   `assert_hooks_reachable()` checks that gate still exists for exactly this reason. Use
   `is_session_flat(trade)`, never a bare comparison.
7. **`EF1-H4`'s per-symbol counts at 60m:** MGC 17, MCL **27**, MES 19, MNQ 19. MCL's excess is
   EF1-F8, a two-month vendor hole (2026-01-12 → 2026-03-10, 1–5 bars a day), not a calendar effect.
   At 240m: MGC 9, MNQ 10.
8. **`EDGE_BRIEF.md:26-30` is wrong** that every prior evaluation was flat by its contract's RTH
   close — see EF1-F2. Roughly half the generated population carries
   `exit_at_session_close=False` and held overnight with no session control at all. Do not treat arm
   A as a clean intraday baseline.
9. **The biggest thing downstream has to carry:** the rule closes **59.6–86.3%** of all positions.
   MNQ's arm-C census is `SESSION_CLOSE 850, STOP 104, TARGET 28, BREAKEVEN 3`. A top-10 built here
   ranks **entry signals scored on a clock exit**, not strategies, and the exit axis is close to
   unmeasurable under this rule at the generated default.

## 5. What I would keep and what I would drop — for EF7, read after your own results

**Keep, and EF3 has already said it is adopting the first three:**
the gap-honest `IN_WINDOW` open fill; re-labelling a gapped flat as `STOP` at the open with no
second slippage (`engine.py:410-411`'s own rule); `assert_hooks_reachable`; the strict emission check
(`SessionWindowViolation`); `EF1-H4` keyed on `trading_day`; `EF1-H8` saturation; and
`violations()`' no-carve-out default.

**Drop / do not copy:** my first `session_end_indices` (ET-date keyed — EF1-D4); the `22*60 - tf`
cap; and any prefix report that collapses the classifier's guarantee together with `EF1-H4`'s
weaker one into a single number.

**Readings I considered and rejected, so you do not have to re-derive them:** a hard-coded
exchange early-close table (elegant, and *incomplete on this substrate* — it cannot cover MCL's
17-date vendor hole); and "fix the deadline at entry, flatten at the first bar past it" (gap-honest,
prefix-invariant, and it records the Christmas Eve hold as 36.5 hours, which **is** a position
existing inside 16:00–18:00 — it satisfies honesty and fails the invariant).

## 6. Verdict I am parking on

**Trustworthy for the invariant; not yet trustworthy for a profitability number, and the second
clause is not about the harness.** The window rule is enforced exactly — 0 violations under
saturation over 11,000 bars per symbol, both directions, five timeframes, with a control that
violates 78 times. What is missing before any row is published is everything downstream of the
gate: placebo arms, a stated search width and deflation threshold, a forward test, and the
firing-rate check. And the 59.6–86.3% clock-exit share (§4.9) has to be on every row, because it
changes what a ranked list is a list *of*.
