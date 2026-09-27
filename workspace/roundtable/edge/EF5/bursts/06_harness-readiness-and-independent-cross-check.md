# EF5 burst 06 — harness readiness for my cell, and an independent cross-check of the census

## 1. The 16:00 ET flat is expressible in every one of my 41 cycles, at all three timeframes

`EF3-01_EF1_session-rule-misses-early-close-sessions.md` reports a real defect in EF1's harness: a
session whose last holdable bar is `OUTSIDE` has no bar for the flat to fire on, and at 60m there are
**19 of 507 such sessions** per symbol, producing holds up to 71 hours against a 22-hour ceiling.

**I checked whether that reaches my cell. It does not.**

`[measured: EF5 scratch over load_series(sym,tf), grouping bars by 18:00→16:00 cycle and asking
whether any bar ENDS exactly at 16:00 ET]`

| cell | 18:00→16:00 cycles | cycles with **no** bar ending at 16:00 ET | `INTERIOR` bars (16:00 strictly inside) |
|---|---|---|---|
| MES 5m | 41 | **0** | **0** |
| MES 15m | 41 | **0** | **0** |
| MES 30m | 41 | **0** | **0** |
| MNQ 5m | 41 | **0** | **0** |
| MNQ 15m | 41 | **0** | **0** |
| MNQ 30m | 41 | **0** | **0** |

Consistent with EF1's own burst 01 (`ON_BOUNDARY` 41 per symbol at 5m/15m/30m, `INTERIOR` 0).

**But I am safe by luck of span, not by construction, and that matters if the span is ever extended.**
EF3's early-close list includes 2026-07-03, which is three weeks *before* my substrate starts
(2026-07-29), and the next US early close after my span ends (2026-09-25) is in November. My 57-day
window happens to contain no shortened session. **Any extension of the EF5 span re-exposes this
defect and my census would have to be re-run.** Recorded so the exemption is not mistaken for
immunity.

## 2. End-to-end smoke test of EF1's harness — PROVISIONAL, plumbing only

`[measured: EF5 scratch, MNQ 30m, first 120 strategies of the declared population, both arms,
`SessionWindowEngine(frame).run_many(...)`]`

```
assert_hooks_reachable()          OK   (EF1's _open_position / _manage overrides are called)
assert_distinct_ids(RTH, SESSION) OK   (D48)

RTH arm      120 strategies ->    16 trades, max 1 per strategy, 0 floored at 20
             counters: bars_on_boundary=41  bars_in_window=83  bars_interior=0
                       flats_on_boundary=0  entries_vetoed_in_window=0
             violations(): 0

SESSION arm  120 strategies ->   102 trades, max 16 per strategy, 0 floored at 20
             counters: flats_on_boundary=23  flats_total=23
             violations(): 0
```

Three things this establishes, and one it does not.

* **The plumbing works and the rule is not violated.** `violations()` returns 0 on both arms.
* **`flats_on_boundary` is 0 in the RTH arm and 23 in the SESSION arm.** That is direct evidence of
  EF2's point in my cell: with `rth_only=True` **not one position in the sample survived to the 16:00
  deadline**, so the 18:00→16:00 rule does literally nothing to a `rth_only=True` MES/MNQ strategy —
  the contract's own RTH close is already 16:00. The overnight regime is reachable **only** through
  the `rth_only=False` arm. Without that arm, an EF5 deliverable would be an ordinary RTH intraday
  list wearing the session rule's name.
* **Trade counts are tiny.** 120 MNQ 30m strategies produced a maximum of 16 trades in the SESSION arm
  and 1 in the RTH arm, over 41 sessions. Zero cleared the 20-trade floor.
* **It does not establish any profitability number.** EF1 has published no `VERIFY.md`, and
  `EF5/code/measure.py:import_engine` refuses to run without one.

## 3. Independent cross-check of the census against EF6 — 0 mismatches in 48 comparisons

Per the BRIEF's independence rule I wrote my own census verdicts to disk (burst 02, `out/census.json`)
**before** reading EF6's. Declaring the order explicitly: mine first, comparison second.

EF6 independently censused the same six (symbol, frame) cells with its own code
(`EF6/out/census/census_{SYM}_{TF}m_frame*.json`). Comparing eight watched conditions per cell, on
both the all-bars count and the in-window (18:00→16:00) count:

`[measured: EF5 scratch comparing EF5/out/census.json against EF6/out/census/*.json]`

**48 of 48 all-bar counts identical. 48 of 48 in-window counts identical.** Spot values:
`session_extreme_sweep` MES 5m 7/7 all and 0/0 in-window; `volatility_compressed` MNQ 5m 3694/3694 and
3533/3533; `value_area_breakout` MES 5m 6133/6133 and 5754/5754; `oi_expanding` 0/0 in every cell.

Two independently written censuses agreeing exactly on 96 counts is evidence; it is also the only
validation either of us has that the counts are right at all.

**One verdict of mine is NOT cross-validated, and I flag it rather than let the agreement above cover
it.** EF6's census has no `RTH` gate — its gates are all / in-window / signal-eligible. My
`volatility_compressed` VOID at **MES 15m RTH** (0 of 1,066 bars), and therefore the finding that all
138 MES 15m BREAKOUT strategies are structurally zero-trade under `rth_only=True`, rests on **my
measurement alone**. It is reproducible from `EF5/out/census.json` (`fires.RTH.15.volatility_compressed`
absent = 0 fires) and from `EF5/out/elimination.json` (`MES_15m.arms.RTH.void_by_group.BREAKOUT =
[138, 138]`), and it should be replicated by someone else before it is quoted as settled.
