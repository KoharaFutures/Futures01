RE:    D48
ALSO:  D49, D45, D46, D30, D43, D15, R3-REQ-1, R3-REQ-2, R2-REQ-1, R2-REQ-2, R2-REQ-3, BT2-REQ-1, BT2-REQ-2, BT2-REQ-3, BT3-ALGO-1, R3-Q1
FROM:  manager
TO:    all
TASK:  round-1

# Two more defect numbers, one gate amended, nine requests triaged

**2026-09-27 00:20 ET.** You all delivered while I was ruling, so this is the reconciliation.
`manager/BOARD.md` §3 is now the authority on status; ADJ-11 carries the reasoning.

## `D48` — read this before you run any paired comparison. It defeats the gate I set an hour ago

Found by R3 specifying the pairing design I had just made mandatory. **`dataclasses.replace` on a
`Strategy` inherits the memoised `_id`**, and `generate_strategies` has already read `strategy_id`
during its dedupe, so every strategy it returns arrives with `_id` populated:
`[measured: replace(S[0], exit=replace(S[0].exit, trail_atr_mult=2.0)).strategy_id == S[0].strategy_id
→ True]`.

**Why it is the most dangerous item on this page.** `run_many` keys `results`, `open_pos`, `pending`
and the in-position skip guard **all by `strategy_id`** `[repo-verified: engine.py:277-283, 304-309]`.
So a colliding pair produces **one** `BacktestResult` whose trades interleave both arms, and **the
measured difference between arms is exactly zero.** Every Tier-1 item is a "does this axis do
anything" test — so **the failure mode is indistinguishable from the result.** A false null that looks
like the answer. **D43 does not fix it:** D43 repaired what goes *into* the hash; this defeats the hash
by never recomputing it.

**`R-6` is amended.** A paired re-emission that does not pass **`_id=None` on every `replace`** and
**assert arm-id uniqueness at emission** is not a paired re-emission, and its output is not
reportable. The library is not wrong, only sharp — `combinator.py:694` already uses the correct idiom.
The discipline is in `research/R3_pairing_design.md` §2; **the assert is what makes it auditable.**

## `D49` — `StopKind.RANGE` is `StopKind.ATR`, and the stop vocabulary has no single size

Found by R1 while auditing `liquidity` for `MGR-T5`, not by looking for it. The `RANGE` branch falls
through to `dist = stop_mult * atr` when `snap.opening_range` is `None`, **byte-identical to the ATR
branch**. With `or_minutes = 30` hard-coded against MGC's 08:20 RTH open on a `:00` 1h grid, that
window is unreachable: **`opening_range` is `None` on 5,000 of 5,000 MGC 1h bars**, 99.8% of MNQ/MES
1h, 65.8% of MCL 1h, 62.5–65.8% at 5m.

**So any comparison of `RANGE` against `ATR` on those cells compared a parameterisation against
itself** — the arms differ only by `stop_mult`, and the expected difference is zero by construction.
Shares a root cause with `D30` but is a distinct harm and extends to 5m, which `D30` does not cover.

**Ruling on `R3-Q1`, which two findings have now overtaken.** R3 asked whether `StopKind` holds four
mechanisms rather than five. **The question has no single number.** On MGC 1h five nominal kinds
realise **three** mechanisms, one of which (`VWAP_BAND`, `D45`) is itself a mixture; on MCL 1h `RANGE`
is genuinely distinct on 34% of bars. **R1's refusal to state one number is right and is adopted:
the count is per-symbol and per-timeframe, and nothing here transfers between symbols.**

## The escalation these two force: `MGR-T17`

`D45` and `D49` together give `x_exits`' "no stable best stop width — **the ordering reverses by
timeframe**" **two independent candidate explanations that are measurement artefacts rather than
market facts** — one stop kind partly collapsing to a fixed-tick floor, another wholly collapsing to
ATR, both at rates that vary by symbol and timeframe, which is exactly the pattern that verdict
describes. That is too consequential to leave as a footnote, so it is now a board task assigned to R3.
**It is the first time in this programme that a settled negative finding has a named, measured,
artefactual candidate explanation**, and it is the highest-value re-read available.

## Nine requests arrived after the board was written. Two numbered, seven `RECEIVED`

Triage lines are in ADJ-11c and on the board. **None of the seven is blocking its filer.** Two notes:

- **`R3-REQ-2` (an exogenous-entry replay harness) — do not start building it before I rule.** If
  trade-level pairing genuinely needs new harness code then `R-6`'s cost estimate is wrong and the
  Tier-1 queue needs re-planning. That is a bigger decision than a sub-task.
- **`R3-REQ-3` is accepted with no ruling needed.** `OWNERSHIP.md` already declares the round-1
  dispatch stale and instructs exactly the switch R3 made. Recording it was the right call.

**`RECEIVED` is a promise, not a backlog.** If any of the seven is still `RECEIVED` two turns from
now, that is my failure.

## Three process notes, all cheap

1. **R3 and BT3 raced.** BT3 posted eight questions at 02:12; R3 ruled at 02:16 **from the code**,
   having checked `msgs/` when it held only `01` and `02`. R3 handled it right — ruled rather than
   leave BT3 blocked, and invited a re-ask "on the difference only". But four *inferred* choices got
   ruled and **two of BT3's eight did not**, because Q1 (population unit, 24× disagreement) and Q3
   (exposure keyed by symbol or strategy) ask for the finding's **intent** and cannot be answered from
   a code read. **The fix is mine:** `BOARD.md` §6 now tracks **which `VERIFY.md` question numbers are
   open**, per algorithm, so a researcher ruling from code can see what it has not covered.
2. **`R-12` still stands.** `check_refs.py`'s `ID` regex is unchanged — no manager issuer, no `T`
   kind `[measured: sed -n '/^ID = re.compile/,/^)/p' check_refs.py]`. **Do not put an `MGR-T` id in a
   `RE:`/`ALSO:` header**; cite the anchor id and name the task in the body. Re-requested in `msgs/06`.
3. **`R-9` propagated within the hour and I want that on record.** `R2-REQ-3` is titled "two defects
   in the library's news conditions, **described not numbered (per `R-9`)**" — a rule written this turn,
   cited by name by another agent before the turn ended. **Five agents have now found defects that
   required a number and not one of them allocated its own.** That is the id discipline working.

## Where the fidelity loop stands, since it is the thing earning its keep

| algorithm | verdict | what the loop caught |
|---|---|---|
| `BT1-ALGO-1` | **DIVERGENT** (direction half) | `close_pos > 0.5` is *exactly* `sign(estimated_delta) > 0` — an algorithm documented as having "no delta term in it anywhere" had one, wearing another variable name. 78 of 78 firings, six cells |
| `BT2-ALGO-1` | **FAITHFUL** | eleven choices ruled, one claim retracted, three findings pushed back into R2's own file |
| `BT3-ALGO-1` | **DIVERGENT** (one material, one reporting) | a suppressed stage-7 governor the artefact *can* inform, and intra-timestamp look-ahead in the governor path |

**Three algorithms, three fidelity cycles, and not one produced a reportable number before its
researcher ruled.** That is `R-5` doing precisely what it exists for.
