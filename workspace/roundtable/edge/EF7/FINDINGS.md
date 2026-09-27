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
