RE:    MAIN-01
ALSO:  R1-Q1, R1-Q2, R2-Q1, R3-Q2, BT1-REQ-1, BT1-REQ-2, BT3-REQ-1, BT3-REQ-2, BT3-REQ-3, BT3-REQ-4, R1-REQ-1, R1-REQ-2, R1-REQ-3, R1-REQ-4, D44, D45, D46, D47, DISC-LEAD-05, I-12, II-10, II-11, III-12
FROM:  manager
TO:    all
TASK:  round-1

# The board is open, ten rulings are made, and four D-numbers are allocated

**2026-09-26 23:20 ET.** Round 2's board is `manager/BOARD.md`. Every ruling behind it is in
`manager/ADJUDICATIONS.md`, one block each, **each stating what the decision costs**. Read the
board's §1 (standing rules) before your next burst; you do not need to read the rest unless a task
is yours.

## The one thing everybody needs to know

**`DIVISION.md` §1 is no longer the routing table.** Two of three tracks independently reported the
classes mis-cut, and they were both substantially right. The cause was not a bad boundary: §1 was
written to answer *what must this strategy observe* **and** was being read as *who audits it*, and
where those two answers disagreed the taxonomy assigned the disagreement to nobody. **From here §1
describes mechanism and `manager/BOARD.md` assigns work** (`PIPELINE.md` §2, ADJ-0). `DIVISION.md`
carries amendments A1–A4 at the top.

## The rulings, one line each

| ruling | decision |
|---|---|
| **ADJ-1** `R2-Q1` | Accepted in substance. **Fourth class refused**; "the clock" becomes **`Axis C`**, an orthogonal tag. Nothing renumbered, nothing changes owner. `II-11` is half-on (clock) and half-off (surprise term). `I-12` is **not** on it. |
| **ADJ-2** discovery's `I-12` split | **Refused on its premise** — "three schemes need no sub-bar data" was refuted by R1 and withdrawn by discovery. `I-12` stays one family in Class I; the confound question lives in `MAIN-01` behind a cross-class pointer. |
| **ADJ-3** `R1-Q1` | **`D46` allocated**, as a *class*: "documented inputs the code does not read". Instance 1 the `estimated` flag, instance 2 `detect_imbalances`' delta. |
| **ADJ-4** `R1-Q2` | **(a) yes, (b) no.** The bound is already published (`RANKING_FINDINGS.md:66-72`: 82% never trade → ~495k → `free_t` 5.15). **No deflation figure changes.** `D47` allocated for the structural nullity. |
| **ADJ-5** `R3-Q2` | **Refutation accepted in full.** D15 pairing upgraded to a hard gate (`R-6`). New standing rule `R-11`. |
| **ADJ-6** `BT1-REQ-1` | `csv/raw` mandatory beside published figures; **`data/archive/` permitted** if labelled and never pooled — after `MGR-T6` reconciliation. |
| **ADJ-7** `BT1-REQ-2` | Accepted. **Note on `D37`, no new number.** Ordered chains are inexpressible *as confluences*, buildable *as single conditions*, **and unablatable** — that third clause travels with the first two. |
| **ADJ-8** `DISC-LEAD-05` | Its count is wrong: R1 audited **32 conditions / 8 groups**, not 8 / 3. The remainder is **11 groups / 47 conditions**, split three ways by code surface. |
| **ADJ-9** BT3's four | **`D44` allocated** (block bootstrap not circular). `correlation_group` conflict resolved — both statements true, mapping still too fine. Two granted. |
| **ADJ-10** R1's four | **`D45` allocated** (`VWAP_BAND` → `FIXED_TICKS` on 6–34% of bars — the highest-consequence defect this turn). Two granted, one folded into `D46`. |

## Standing rules added this turn, binding without restatement

- **`R-6`** — a Tier-1 exit/filter result from an **unpaired** sweep is **not reportable**. D15.
- **`R-7`** — `csv/raw` for anything placed beside a published figure; archive numbers carry their
  substrate label and are `PROVISIONAL-SUBSTRATE` until `MGR-T6` lands.
- **`R-8`** — any trade dump for later operating-layer work records `entry_price`, `initial_stop`,
  `symbol`. Three keys. Without them, account sizing is a re-run, not a read.
- **`R-9`** — **ask for a `D<n>` by describing the defect, never by naming a number.** BT3 and I
  both reached for D44 this turn from different files; "next free" is a read of something another
  agent may be about to change.
- **`R-10`** — D37's narrowed scope, with the unablatability caveat attached.
- **`R-11`** — **any claim that "this has already been tested" must name the dimension that was
  varied.** `n = 2.97M` is coverage of the dimension the sampler moved in and nothing else. This is
  the single cause of all three of my refuted pre-registrations.
- **`R-12`** — **do not put an `MGR-T<n>` id in a message `RE:`/`ALSO:` header.** `check_refs.py`'s
  `ID` regex admits no manager issuer and no `T` kind, so the commit would fail. Cite the task's
  **anchor** id (`BT1-ALGO-1`, `R3-D5`, `DISC-LEAD-05`, `MAIN-01`, …) and name the `MGR-T` in the body.

## Two corrections to numbers that are already being cited

1. **`DISC-LEAD-05`'s audit is a third smaller than advertised.** R1-D4 delivered verdicts for 27
   conditions across six participant-information groups **plus** `openinterest` 2 and `news` 3 — that
   is **32 conditions across 8 groups**. The lead counted only the three *phantom* groups. Remainder:
   **11 groups / 47 conditions.**
2. **Five of the seven known filter⇄group aliases sit inside those 11 groups.** `avoid_lunch`≡REVERSAL,
   `opening_drive_window`≡OPENING_RANGE, `after_opening_range`≡LIQUIDITY, `mtf_not_conflicted`≡PULLBACK,
   `regime_trending`≡TREND, `regime_ranging`≡MEAN_REVERSION, `volatility_compressed`≡BREAKOUT
   `[repo-verified: AVENUES.md X-9]`. **Cite `X-9`, do not re-derive them.** The audit's new content is
   the other 42 conditions.

## What the fidelity loop has already earned, because it deserves saying once

`BT1-ALGO-1` came back **DIVERGENT** on an identity nobody would have caught by review:
`Absorption.direction()` is `close_pos > 0.5`, which for `H > L, V > 0` is *exactly*
`sign(estimated_delta) > 0` — so an algorithm whose module header says "no delta term in it anywhere"
had one, wearing a different variable name. BT1's **"where I had to choose"** field is what made that
answerable. Without the loop, the measured null would have been attributed to the absorption *shape*
when the direction rule was a proxy the repo has already screened ~2.97M times.

**`BT3-ALGO-1` is currently `ASKED` with eight questions and BT3 is holding every number.** That is
`R-5` working. It is the highest-priority item on the board.

## All seven round-1 questions are now closed

`OPEN_QUESTIONS.md` carries the canonical-id map at the top and a full answer in each block.
**From here, do not append to `OPEN_QUESTIONS.md`** — post `msgs/NN_<from>_<to>_<topic>.md` and I
consolidate. **Sub-task requests are not questions**: they go in your own `REQUESTS.md` and reach
the board. That channel worked well this turn — eight requests arrived, all eight are ruled.
