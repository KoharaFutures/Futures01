# EF7 — independent implementation and validation of the 18:00 ET → 16:00 ET session window

Written as I go. Bursts in `bursts/`. Code in `code/`. Repo tests in
`tests/test_ef7_session_window.py`. Measured numbers in `measure.json`.

---

## 0. Independence declaration — read this before any agreement claim

My dispatch instructed me to implement and validate the session-window rule **without reading
EF1's implementation**, so that agreement between us is evidence rather than one audit wearing two
names (`../BRIEF.md` → "Independence rule for duplicated audits"). I followed that, with one leak I
declare in full, because an undeclared anchor is unusable.

**What I read before writing my own code:** `EDGE_BRIEF.md`, `../BRIEF.md`, `../REGISTRY.md`,
`../OWNERSHIP.md`, my dispatch, and the repository itself (`futures_agents/**`, `data/archive/**`).

**The leak.** Verifying my dispatch's claim that no call site passes `allow_overnight=True`, I ran
`grep -rn "allow_overnight" --include="*.py" .` over the whole tree with no exclusions. The output
included **10 lines from `EF1/code/session_window.py`, 3 from `EF1/code/measure.py` and 2 line
numbers from `tests/test_ef1_session_window.py`** (plus EF4/EF5/EF6 lines, which I am not restricted
from). Exactly what those lines told me, before I wrote anything:

1. EF1 restates the same three facts about `engine.py:470` that my dispatch already stated verbatim.
   Not information.
2. EF1 forces `allow_overnight=True` and does not expose it as a parameter.
3. EF1 has a guard that string-matches `"not self.allow_overnight"` in
   `inspect.getsource(BacktestEngine._manage)`.
4. EF1's measurement has an arm A (as shipped) and an arm B (`allow_overnight=True`, no window rule).

**How I handled each.** (2) is convergent and forced — the shipped exit fires at the contract RTH
close and is gated on `not allow_overnight`, so any 16:00 rule must disable it; my dispatch says so
in the same words. I claim no independence credit for it. (3) I deliberately did **not** copy: a
source-string guard breaks on a whitespace change and passes a semantic one, so I wrote the
behavioural equivalent instead (`test_h3_shipped_contract_rth_close_exit_is_inert`, asserting no
`SESSION_CLOSE` survives and that the shipped engine *does* produce one as a control). That choice
is how I found EF7-D2. (4) is a natural arm split and I use the same one, again without credit.

**I did not read** any EF1 finding, verdict, burst note, closure count, violation count or test body,
nor any EF1 source beyond those 15 grep-matched lines. From that grep onward every search excluded
`EF1` and `test_ef1_*`. Everything in §1–§5 was written and executed before I opened EF1's
directory; §6 is the comparison and is marked with the time it was written.

---

## 1. The four "why it cannot be configured" claims, verified myself

Full table in `bursts/01_substrate-clock-geometry.md`. All four confirmed, with two additions.

**Narrowing.** "No call site passes `allow_overnight=True`" is true of `futures_agents/` (the
shipped package) and is **no longer true of the tree**: EF1, EF4 and EF6 all pass it from
`workspace/roundtable/edge/`. Anyone re-running the brief's grep will now get a different answer, so
the claim should be worded *"nothing in `futures_agents/` passes it"*.

**Addition that decides component 3.** `_close` never touches the cost model
(`engine.py:479-517`). Slippage is applied in exactly two places: the entry (`:353`) and the stop
(`:416`). So TIME, SESSION_CLOSE and END_OF_DATA are zero-slippage **by construction** — there is no
setting that fixes it, which is why the flat has to price itself rather than delegate.

## 2. The clock geometry of the substrate `[measured: data/archive/, all four symbols]`

1. **No bar straddles 16:00 ET** at 15m, 30m, 60m or 240m on any symbol (0 of ~11,300 at 60m, 0 of
   ~3,050 at 240m). At 240m this is luck of the bucketing — `align_bucket` snaps ≥60m buckets to
   midnight (`futures_agents/data/bars.py:150-153`), giving 00/04/08/12/16/20, so 12:00–16:00 lands
   exactly on the deadline. A 3h or 6h frame would straddle. The rule handles a straddler anyway and
   counts it (`WindowStats.flat_on_late_bar`).
2. **Bars do exist inside the forbidden window**, so the veto has something to refuse: 495 MGC,
   474 MCL, 493 MES, 497 MNQ 60m bars open in [16:00, 18:00). The 17:00 bar is nearly always absent
   (6/3/5/9) — the maintenance break — so at 60m the forbidden window is usually one printed bar.
3. **Cycles do not all end at 16:00**, which breaks the obvious implementation. → §3.

## 3. EF7-D1 — the naive flat exits *inside* the forbidden window on 3–7% of cycles

**The substantive defect, found before the fix was written.** Detail in
`bursts/02_ef7-d1-naive-flat-defect.md`.

The implementation that reads correctly is *"close when the bar's end reaches the cycle's 16:00
deadline"*, with the cycle keyed off `trading_day` the way the rest of this repo keys a CME session.
Correct on 489 of 506 MGC 60m cycles. On the rest:

| 60m | cycles | last bar ends 16:00 | **ends earlier** |
|---|---|---|---|
| MGC | 506 | 489 | **17** (3.4%) |
| MCL | 505 | 470 | **35** (6.9%) |
| MES | 507 | 488 | **19** (3.7%) |
| MNQ | 507 | 488 | **19** (3.7%) |

On one of those cycles no bar satisfies `end_ts >= 16:00` until a bar that *opens* at 16:00 or later,
so the naive rule fires there and the position **exits at 17:00 ET, inside the forbidden window** —
or on the 18:00 bar, having held straight across the break. Silent; a minority of cycles; and the
effect is a *longer* hold, which on a trending cycle reads as a better number.

**Fix (EF7-H2):** flat at bar *i* when `cycle_key(bars[i+1].ts) != cycle_key(bars[i].ts)`, with
`cycle_key` returning `None` inside the forbidden window rather than gluing it to the cycle it
terminates. That reads the successor's **timestamp**; the look-ahead claim is discharged by three
tests (price-mutation, prefix-invariance on real bars, and `end=k` window containment), not asserted.
`flat_flags` returns `None` — not `False` — for the last bar of the run, because whether it ends a
cycle is genuinely unknowable without a successor.

**Residual, stated not hidden:** on those cycles the flat fires **early** (13:00, 00:00). No printed
price exists at 16:00 to fill against. Counted as `WindowStats.flat_before_deadline`, never folded
into the headline.

## 4. EF7-D2 — the shipped session exit closes an evening entry on its *entry bar*

Found because I built the "shipped exit is inert" control behaviourally instead of by string-match.
Detail in `bursts/03_ef7-d2-shipped-session-exit-kills-evening-entries.md`.

`elapsed = minutes_since_open(bar.ts, spec.rth_open) + bar.minutes` (`engine.py:471`) is measured
from the RTH open of the bar's **own calendar date** and never clamped. For MGC (`_rth_minutes`=310)
`elapsed >= 310` reduces to *the bar opens at or after 12:30 ET*, and stays true all evening —
19:00 → 700, 23:00 → 940. It goes negative again after midnight, so 00:00–12:29 ET holds normally.

`[measured: two-cycle fixture, rth_only=False, 19 trades]` → `bars_held` = **{1: 17, 14: 2}**, all
`SESSION_CLOSE`. An evening entry never reaches a second bar.

Three consequences:
1. `../BRIEF.md`'s point 2 is understated. Not "flat by its contract's RTH close" — the shipped
   engine **cannot carry an overnight position at all**.
2. Any arm-A baseline on an `rth_only=False` population is partly measuring this artefact, not
   intraday trading.
3. It is a candidate explanation for **D24** ("`rth_only=False` buys sample and costs expectancy")
   that has nothing to do with overnight liquidity. I have not re-measured D24 and am not claiming it
   is wrong; its paired tests should be re-read with this in front of them. **Routed to the manager.**

Not fixed — `futures_agents/` is not mine to change and the branch is dead inside
`SessionWindowEngine` (which forces `allow_overnight=True`). Regression test:
`test_ef7_d2_shipped_session_exit_closes_an_evening_entry_on_its_entry_bar`, which pins the
post-midnight half too so the mechanism is caught rather than the symptom.

## 5. Design decisions, each with the reason it could have gone the other way

| decision | chosen | why not the alternative |
|---|---|---|
| where the flat sits in the exit ladder | **after** stop, target, breakeven, trail and time stop | Putting it first re-attributes exits that were already happening and inflates the closure count. Last makes `flat_exits` mean *"positions the rule closed that had no other reason to close on that bar"* — the number asked for. Cost: a time stop on the flat bar keeps `engine.py:467`'s zero slippage. Counted, not hidden. |
| flat fill price | `bar.close` ∓ slippage, `is_stop=True` | `is_stop=True` is the market-order branch (`costs.py:38-39`: *"stops are market orders; they slip more"*). A mandatory 16:00 flat **is** a market order. Exposed as `flat_is_market_order` so the limit reading can be measured; the difference is exactly `stop_order_extra_ticks` = 1 tick. |
| what instant the entry veto tests | `bars[i+1].ts`, the **fill** instant | Testing the signal bar is off by one and inverts the rule: it refuses the legal 15:00 signal and admits the illegal 16:00 fill. |
| signals on forbidden bars | **allowed** | The 17:00 bar closes at 18:00 and fills at the 18:00 open — the first admissible instant of the next cycle, a legitimate overnight entry. Vetoing it would be stricter than the spec. |
| new exit reason | separate `WindowExitReason.SESSION_WINDOW` str-enum | Reusing `SESSION_CLOSE` makes the 16:00 flat indistinguishable from the contract-RTH exit it replaces, and counting it is the point. A `str` enum keeps `metrics.py:244` and `storage.py`'s TEXT column working untouched. |
| implementation shape | **subclass** of `BacktestEngine`, 3 overrides | A fork re-implements next-open entry, stop-before-target, gap fills and charge-once costs — which is how they get lost. `_manage` runs the parent to completion with `is_last=False`, then the flat, then end-of-data. |
| `futures_agents/` edits | **none** | Nothing in the shipped package is touched. |

### 0a. Two further leaks, declared (appended at the time they happened)

**Leak 2.** `ps aux` run to check whether my own background jobs were alive dumped every agent's
full command line. EF1's showed as: `EF1/code/saturate.py --symbols MGC,MCL,MES,MNQ --tfs
5,15,30,60,240`, `EF1/code/measure.py --base-tf 60 --tfs 60,240 --max-total 400`, and
`EF1/code/prefix_check.py`. That is **file names and CLI flags only** — no verdict, no number, no
code semantics. It tells me EF1 has a saturation sweep, a measurement with a base-tf/confirm-tf
split, and a prefix check. It did not change anything I had already written (all of §1–§5 and both
defects predate it) and it did not add anything to my design, which was finished. Declared for
completeness.

**Leak 3.** The same `ps aux` output contained large inline heredocs of **EF3's** source. EF3 is not
on my exclusion list, and I did not read it.

I switched to `ps -o pid,etime,cmd -C python3` and targeted `pgrep` afterwards.

---

## 5. Results

### 5.1 Test suite — `tests/test_ef7_session_window.py`

66 tests. Every component has a known-answer test that is fed a deliberate breach and shown to
reject it; the ones that matter most:

| what it proves | test |
|---|---|
| the detector can fail | `test_h3_the_unmodified_engine_fails_this_same_assertion` — the shipped engine breaches the invariant on the same fixture |
| each violation clause fires | `test_detector_catches_an_entry_inside_the_window`, `..._an_exit_inside_the_window`, `..._an_exit_bar_that_runs_past_the_deadline`, `..._a_trade_spanning_the_window` |
| EF7-D1 | `test_h2_naive_end_ts_rule_violates_the_spec_and_flat_flags_does_not` |
| EF7-D2 | `test_ef7_d2_shipped_session_exit_closes_an_evening_entry_on_its_entry_bar` |
| no look-ahead | `test_h2_flat_decision_reads_the_successor_timestamp_and_no_successor_price` (mutates all later OHLCV to 9e4), `test_h2_prefix_invariance_on_real_bars` (all four symbols, ~11,000 bars), `test_h3_engine_prefix_invariance_on_real_bars`, `test_h3_end_argument_does_not_leak_past_the_run_window` |
| DST | `test_h1_dst_correct_across_the_2024_11_03_switch` (asserts the two instants really do carry different offsets, so the test is not vacuous), `test_h1_fixed_offset_reading_is_wrong_and_the_window_is_not`, `test_h1_utc_stamped_bar_is_classified_on_et_wall_clock` |
| holiday eve | `test_h2_holiday_eve_2300_bar_ends_its_cycle`, `test_h2_no_trade_spans_a_holiday_eve_boundary`, `test_h2_holiday_flat_needs_no_holiday_table` |
| stop/target/time still outrank the flat | `test_h3_stop_wins_over_the_flat_in_the_same_bar`, `..._target_wins...`, `..._time_stop_wins...` |
| costs | `test_h3_flat_charges_market_order_slippage_adversely` (both directions), `test_h3_flat_slippage_includes_the_volatility_term`, `test_h3_commission_is_charged_exactly_once_on_a_flat_exit` |
| D48 | `test_h3_arm_ids_are_unique_when_built_by_replace` |

### 5.2 The invariant on realised trades — **zero violations**

`[measured: code/invariant.py → invariant.json]` Saturating fixture (signal on every bar), both
directions, `data/archive/` 60m, full series. Detail in `bursts/05_invariant-zero-violations.md`.

**Total violations across all four symbols and both directions: 0**, over 10,010 trades.
`max_minutes_held` is **1,260 on every symbol and direction and never once more** — exactly the
ceiling a 22-hour cycle permits on 60m bars measured between bar-open times. `entries_vetoed` equals
the number of forbidden-window bars **exactly** on all four symbols (495/495 MGC, 474/474 MCL,
493/493 MES, 497/497 MNQ), which pins the veto to the right instant to the bar.

### 5.3 The same at POPULATION scale — still zero

`[measured: code/population.py 4000 → population.json]` EF3's lesson relayed by the coordinator: a
cycle-boundary defect can be 0 on a 400-strategy probe and non-zero on a population.

| symbol | strategies | trades | **violations** | flat exits | max hold | holds > 22h |
|---|---|---|---|---|---|---|
| MES | 1,964 | 12,509 | **0** | 8,430 | 1,260 min | 0 |
| MNQ | 1,985 | 13,578 | **0** | 8,006 | 1,260 min | 0 |

A note on what covers what: a probe samples cycle boundaries, so it can miss a rare one; the
saturating fixture in §5.2 holds a position across essentially **every** boundary and cannot. What
the fixture misses is *interactions* — scale-outs, breakeven moves, trailing stops and anchored
targets all touch `_manage` before the flat does. The two are complements, and the right answer to a
rare-path defect is a saturating control, not only a larger population.

### 5.4 Closure counts — how many positions the rule actually closes

`[measured: code/measure.py --max-total 400 → measure.json]` Generated default population
(`rth_only=True`, untouched), `data/archive/` 60m, 2024-10-06 → 2026-09-25.

| symbol | strategies | arm C trades | **flat exits** | share | violations C / A / B |
|---|---|---|---|---|---|
| MGC | 184 | 2,143 | **1,483** | 69.2% | 0 / 1,259 / 1,276 |
| MCL | 167 | 3,343 | **1,868** | 55.9% | 0 / 1,041 / 1,762 |
| MES | 190 | 2,554 | **1,349** | 52.8% | 0 / 1,562 / 1,583 |
| MNQ | 185 | 1,536 | **884** | 57.6% | 0 / 929 / 1,024 |

**It is nowhere near zero.** The flat closes 53–69% of all trades on every symbol. At population
scale (§5.3) it is 8,430 of 12,509 MES (67%) and 8,006 of 13,578 MNQ (59%).

Two things this number is and is not. It **is** exact as "positions the rule closed that had no
other reason to close on that bar", because the flat is checked after the entire shipped exit
ladder. It is **not** the same as "hold extensions" — see §5.6.

### 5.5 EF7-D3 — the brief's "every prior evaluation was flat by its RTH close" is false

**This is the largest correction I have.** `BRIEF.md` and `EDGE_BRIEF.md` both argue that because
`allow_overnight` defaults to `False`, "every one of ~2.97M prior evaluations was flat by its
contract's RTH close" and "the overnight-hold regime is genuinely unmeasured."

`allow_overnight=False` only *enables* the session exit. The exit **also** requires
`exit_model.exit_at_session_close`, and the combinator sets it `False` on three exit models:
`futures_agents/strategies/combinator.py:94, 99, 106` — the three `ANCHORED_EXITS`. `exits_for`
adds `ANCHORED_EXITS` to **every template's catalogue** (`:130-133`), with a comment saying exactly
that.

`[measured: generate_strategies(sym,[60],max_total=400,seed=20260922)]`

| symbol | strategies | `exit_at_session_close=False` | share |
|---|---|---|---|
| MGC | 184 | 98 | **53.3%** |
| MCL | 167 | 78 | **46.7%** |
| MES | 190 | 102 | **53.7%** |
| MNQ | 185 | 75 | **40.5%** |

And the consequence, arm A (fully as shipped), MGC 60m generated default:

| bucket | trades | median hold | max hold | trades spanning 16:00–18:00 |
|---|---|---|---|---|
| `exit_at_session_close=True` | 17 | 0 min | 120 min | 0 (0.0%) |
| `exit_at_session_close=False` | **1,896** | **840 min (14 h)** | **8,040 min (5.58 days)** | **1,191 (62.8%)** |

**So 99.1% of the as-shipped MGC trades at the generated default come from strategies with no
session exit at all, they hold a median of 14 hours, up to 5.6 days, and 62.8% of them already
carry across a 16:00–18:00 break.** Arm A is not an intraday baseline. Programme-wide arm-A
violation counts: MGC 1,259 / MCL 1,041 / MES 1,562 / MNQ 929 breaches of the session rule out of
1,913 / 3,480 / 2,644 / 1,650 trades.

Three consequences:
1. The overnight-hold regime is **not** unmeasured. Roughly half the generated population has always
   held overnight — just with **no 16:00 discipline**, across weekends and for days. That is a
   *different* regime from the one specified, so no prior number transfers; but the brief's reason
   for saying so is the wrong reason, and the corrected reason is stronger.
2. Any "arm A vs the rule" comparison is not "intraday vs overnight". It is "unbounded multi-day
   holds vs a 22-hour cap", and on this population the rule mostly **shortens** holds.
3. `exit_at_session_close` is a live generator axis that no brief in this programme mentions.
   **Routed to the manager.**

### 5.6 Is the rule inert at the generated default? No — and not by EF2's mechanism

EF2 (`BRIEF.md` → EF2-01) predicted the rule unlocks only *holding past the contract RTH close to
16:00* — +2.5 h MGC, +1.5 h MCL, **"nothing at all on MES/MNQ"** — and no overnight entries.
I measured each clause. `[measured: code/compare_ac.py → compare_ac.json; scratchpad entry-hour probe]`

**Confirmed.** The hold-extension arithmetic is exactly right. Of MGC's 1,483 flats, **1,483 of
1,483 are past 13:30**; MCL 1,850 of 1,868 past 14:30; MES **0 of 1,349** and MNQ **0 of 884** past
16:00, because their RTH close already *is* the deadline. And the `later_exit` extension is exactly
one bar: median and max **+120 min on MGC, +60 min on MCL, none on MES/MNQ**.

**Not inert, and "nothing at all on MES/MNQ" is too strong.** A ≠ C on all four symbols. On MES/MNQ
the rule bites through the other two components, which EF2's framing does not cover:
* **The entry veto fires hard.** MES 1,053 and MNQ 405 entries vetoed at the generated default
  (4,057 and 4,184 at population scale). MGC and MCL: **0**. The asymmetry is exact: MES/MNQ RTH
  runs to 16:00, so the 15:00 bar is an RTH signal bar and its next-open fill lands at 16:00 —
  inside the forbidden window. MGC's last RTH signal bar is 13:00 and fills at 14:00, so nothing to
  veto.
* **The flat costs money.** MES 25 and MNQ 138 trades close on the *same bar at a different price*,
  mean ΔR **−0.0197 (MES)** and **−0.0030 (MNQ)** — pure cost, no timing change. MCL 94 trades,
  −0.0262. This is component 3 doing its job, and it is the only thing the rule changes on trades
  whose timing is unaffected.

**The honest summary: at the generated default the rule is a cap, not an unlock.** Max hold under the
rule is 300 min (MGC), 840 (MCL), 720 (MES), 240 (MNQ) — against a 1,320-minute budget. The 22-hour
regime is **unreachable with `rth_only=True`**, which corroborates EF2 and EF3 independently.
Reaching it needs `rth_only=False`, and D24 prices that.

### 5.7 EF7-D4 — a stale signal can fill across a data gap, into the next cycle

Measured while checking §5.6, and it is why my numbers disagree with EF3's "`rth_only=True` caps the
hold at 6.5 hours". I measure **12 hours on MES** and entries at 00:00 and 18:00 ET in a population
whose `rth_only` is `True` on every strategy.

The mechanism is inherited, not mine. `run_many` holds a signal in `pending` and fills it at
whatever the **next processed bar** is (`engine.py:290-295`). Contiguous data, that is the next bar's
open and correct. Across a data gap it is hours later — and my veto correctly allows it, because
18:00 is admissible. So a signal formed at 14:00 in cycle *D* can fill at 18:00 in cycle *D+1*.

`[measured: arm C, generated default]` MCL 2 of 3,343, MES 3 of 2,554, MNQ 8 of 1,536 entries land at
18:00; MES 11 and MNQ 8 land at 00:00. Small in count, and it is the whole explanation for the
`rth_only=True` hold cap being wrong by a factor of two.

Not a spec violation — the fill is in an admissible instant. It is a **realism** defect, and the fix
is one clause (refuse a fill whose cycle differs from the signal's, or whose lag exceeds one bar).
I have **not** applied it, because silently making the rule stricter than the specification is the
error I am here to catch in other people's work. Offered as an option and **routed to the manager**.

### 5.8 A cost the rule creates: one-bar trades against a mandatory flat

`entries_flat_same_bar` counts positions filled on a bar that is itself the cycle's last, so they
open at its open and close at its close. **MES 1,528 of 12,509 (12.2%) and MNQ 1,545 of 13,578
(11.4%) at population scale**; MGC 0 at the generated default (its last RTH fill is 14:00, two bars
clear of the flat). These are legal under the specification and are not violations. They are also
a full round turn plus market-order flat slippage for 60 minutes of exposure — a real drag that the
rule introduces and that no reported row should absorb silently. A `min_minutes_to_flat` entry guard
would remove them; that is a **specification** change, so I have not made it. **Routed to the
manager.**

### 5.3b Population-scale table, all four symbols

`[measured: code/population.py 4000 → population.json]`

| symbol | strategies | trades | **violations** | flat exits | share | max hold | >22h | vetoed | one-bar | early flats | zero-trade |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MGC | 1,984 | 9,725 | **0** | 6,362 | 65.4% | 300 min | 0 | 0 | 10 | 20 | 1,608 |
| MCL | 1,957 | 16,013 | **0** | 10,287 | 64.2% | 900 min | 0 | 0 | 1,856 | 147 | 1,502 |
| MES | 1,964 | 12,509 | **0** | 8,430 | 67.4% | 1,260 min | 0 | 4,057 | 1,528 | 181 | 1,525 |
| MNQ | 1,985 | 13,578 | **0** | 8,006 | 59.0% | 1,260 min | 0 | 4,184 | 1,545 | 182 | 1,599 |
| **total** | **7,890** | **51,825** | **0** | **33,085** | **63.8%** | | **0** | **8,241** | **4,939** | **530** | **6,234** |

`TIME` exits: **0 of 51,825**, on every symbol. Independently reached before the coordinator relayed
EF3's finding, and it has the same cause: the catalogue's smallest `time_stop_bars` is 30 *primary*
bars = 30 hours against a 22-hour ceiling, so the entire time-stop dimension measures nothing under
this rule. That also means my deliberate "the time stop outranks the flat" ordering choice (§5) has
**zero effect on any real number here** — it changes nothing on this population and is only load-
bearing for a catalogue with a sub-22-bar time stop.

`zero_trade_strategies`: 6,234 of 7,890 (**79.0%**) never trade — consistent with the programme's
82% figure, and a reminder that a null from this population is usually "the detector never fired".
