# BOARD — the task board the pipeline runs on

**Owner:** manager (`OWNERSHIP.md`). **Opened:** 2026-09-26 22:11 ET. **Updated:** 2026-09-26 23:04 ET.
**Authority:** `PIPELINE.md` §2. Ids are canonical per `REGISTRY.md`. Rulings behind board entries
are in `manager/ADJUDICATIONS.md`.

This file, not `DIVISION.md` §1, says who owns what. That is `ADJUDICATIONS.md` ADJ-0: §1 was
written as a mechanism taxonomy and was also being read as a routing table, and where those two
jobs disagreed the taxonomy assigned the disagreement to nobody. **From here §1 describes
mechanism and the board assigns work.**

---

## 1. Standing rules — binding on every agent, no restatement needed in a dispatch

These are decided. Each cites where it was ruled, so nobody re-litigates one in a burst.

| # | rule | ruled in |
|---|---|---|
| R-1 | **`csv/` is read-only for everyone, always.** No exceptions, no backtests that write, no reshaping. | `OWNERSHIP.md` |
| R-2 | **A placebo beside every result.** Count-matched random bars or timestamp-shuffled. `placebo_shift` leaks and is conservative-only (D42). A result without a control is not reportable. | `PIPELINE.md` §4 |
| R-3 | **State the search size and the deflation threshold.** Six parameterisations means six. Programme-wide `free_t = 5.46`; largest t ever found here 3.923. | `PIPELINE.md` §4 |
| R-4 | **Never route a comparative claim through `T.ab`** — it inflates z ~3.3× (D28). Name the paired test you used. | `PIPELINE.md` §4 |
| R-5 | **Never report a number from an UNVERIFIED algorithm.** An unverified result is not weak, it is unknown: nobody can say what was measured. | `PIPELINE.md` §4 |
| R-6 | **A Tier-1 exit/filter result from an unpaired sweep is NOT reportable.** D15: only 93 of 8,317 shipped rule sets exist with two different exits, so an unpaired exit comparison is confounded with the entry. Paired re-emission of the same rule sets, or nothing. **Amended (ADJ-11a): a paired re-emission that does not pass `_id=None` on every `replace` and assert arm-id uniqueness at emission is not a paired re-emission** — `D48` makes both arms collide into one `BacktestResult` with a measured between-arm difference of exactly zero. | ADJ-5, ADJ-11a |
| R-7 | **`csv/raw/` is mandatory for any number placed beside a published `scan_reports/` figure.** `data/archive/` is permitted for a number that is **labelled with its substrate** and **never pooled with a `csv/raw` number inside one statistic** — and only after `MGR-T6` lands. Before then, archive numbers are `PROVISIONAL-SUBSTRATE`. | ADJ-6 |
| R-8 | **Any trade dump intended for later operating-layer work records `entry_price`, `initial_stop` and `symbol`.** Three keys; without them account sizing is a re-run, not a read, and the link dies the moment the slicing or the snapshot changes. | ADJ-9d |
| R-9 | **An agent wanting a `D<n>` describes the defect and does not name a number.** "Next free" is a read of a file another agent may be about to change; it nearly collided this turn. | ADJ-9 numbering note |
| R-10 | **Ordered chains are inexpressible as confluences and buildable as single conditions** — but a sequence built as one condition **cannot be ablated leg-by-leg**. Anyone building one owes that caveat up front. D37's scope, narrowed. | ADJ-7 |
| R-11 | **Any claim of the form "this has already been tested" must name the dimension that was varied.** `n = 2.97M` is coverage of the dimension the sampler moved in and nothing else. This is the round-1 error that produced three wrong pre-registrations. | ADJ-5 |
| R-12 | **`MGR-T<n>` must not appear in a message `RE:`/`ALSO:` header** until `REGISTRY.md` and `check_refs.py`'s `ID` regex are extended — they admit no manager issuer and no `T` kind, so the commit would fail. Cite the task's **anchor** id in the header and the `MGR-T` in the body. | ADJ-8 / allocations |

**Verdict vocabulary for the condition-group audit, fixed so three auditors stay comparable**
(R1's, from `R1-D4`): `PROXY` (name promises participant info, arithmetic is OHLCV) /
`DEGRADED` (right object, sampling materially changes its value) / `HONEST-DERIVED` (name matches
arithmetic) / `HONEST-DERIVED-BUT-BROKEN` (concept expressible, this implementation is not causal).

---

## 2. Main tasks

**One exists.** Only discovery allocates `MAIN-<nn>` (`REGISTRY.md`).

### MAIN-01 — the sampling clock: is part of this repo's null result a property of wall-clock bars?

| field | value |
|---|---|
| **Raised by** | discovery burst 01, `discovery/MAIN_TASKS.md` |
| **Avenue** | `I-12`, `CLOSED-FOUND` |
| **Sections allocated** | **none — by design** |
| **Current state** | awaiting **Mode SCOPE**, assigned to **R1**, queued behind `MGR-T1` (done) |
| **Killable** | **yes**, as `CLOSED-EMPTY` |

**Why no sections exist, and this is the part of round 2 that is most different from round 1.**
`PIPELINE.md` §2 forbids me decomposing it: "The manager reads a main task and **does not decompose
it either.** Its first move is to ask the researcher: *what sub-task breakdown do you need to
research this, and at what granularity?*" In round 1 I wrote six fixed deliverables per track from
my own map, and two of three tracks came back to tell me the map was mis-cut. So `MAIN-01` gets a
scope request and **no `MAIN-01/S<n>` id exists until R1's `SCOPE.md` comes back.** Sections are
mine to allocate and I am allocating none yet on purpose.

**Why R1 scopes it, over R3 which owns the settled findings it targets.** The task's own first gate
is the **approximation-error question**, and its two inputs are both R1's surface: the provenance of
the `volume` field (the CSV column schema, `DIVISION.md` §2) and the bar construction itself
(`I-12`, which R1 has already audited to nine layers). R3 owns the *targets* of the confound
question — ATR-denominated stop geometry, the win-rate/payoff cancellation, the sub-hourly verdict —
but those are only reached if the first gate is passed, and R3 is the most loaded track on the board.

**Three things the scope must carry, and the first can end the task:**

1. **The approximation-error question, first, before any construction.** Discovery's framing —
   volume/dollar/range bars "need only `(high, low, close, volume)` per minute" — was **too strong
   and has been withdrawn**. R1 established the mechanism: a volume-bar boundary is the moment
   cumulative volume crosses a threshold, which happens *inside* a minute, so from 1-minute bars it
   can only be snapped to a minute edge `[repo-verified: R1_flow_auction.md:1113-1116]`. The
   question is **not** "is the approximation exact" — it is not — but **"is the minute-snapped
   approximation good enough to answer the confound question, and in which direction does its error
   push?"** The error shrinks as the bar grows relative to a minute's volume; at the measured
   medians (14 contracts/min MGC, 9 MES, 56 MNQ) a bar sized for 50–200 bars/session spans many
   minutes, and at the fine end a snapped boundary is most of the bar. **There is a size range
   where the approximation is defensible and one where it is not, and nobody has drawn the line.**
2. **If the answer is "not good enough": close `CLOSED-EMPTY` and record the reason.** That is a
   complete result and the right one. **Do not quietly rescope to range bars only** — R1 called
   that approximation poor too. ADJ-2 rules this exposure correct: a task killable by one honest
   measurement is worth more than one rescoped until it cannot be.
3. **Do not re-ask the expressibility question.** R1 answered it: `INEXPRESSIBLE-ARCHITECTURE`,
   missing primitive "a bar-identity that is not an integer minute count", load-bearing at **nine**
   named layers `[repo-verified: R1_flow_auction.md:1098-1135]`. Discovery reached the same verdict
   and the same primitive independently within the hour. **What neither supplies is the price of
   changing it** — that is the open half. `MAIN-01` is also **not** on Axis C: a volume-bar boundary
   is a statement about cumulative volume, not about the bar's timestamp (ADJ-1).

**Substrate note for the scope:** `csv/raw`'s 1-minute files are 5,000 bars ≈ 4 sessions and cannot
support this. The usable substrates are `data/{MES,MGC,MNQ}_1m.csv` (404k–470k bars, 352 RTH
sessions, 2019-01-01 → 2020-05-14, **Oanda CFD not futures, not poolable with `csv/raw`**) and
`data/archive/*.jsonl`. R-7 applies.

---

## 3. The task board, in dependency order

`MGR-T<n>` is this board's task id. Status vocabulary: **DONE** / **IN FLIGHT** / **OPEN** (ready to
dispatch) / **QUEUED** (dependency unmet) / **GATED** (work may proceed, output not reportable).

> **Status as of 2026-09-27 00:15 ET.** R1, R2 and R3 ran **in parallel with this board being
> written** and all three delivered before it was finished, along with BT2's and BT3's first bursts
> and nine further requests. The table below is reconciled against what is actually on disk, so
> several rows were **DONE before they were ever dispatched**. That is the pipeline working, not a
> bookkeeping failure — but it is why §3's statuses matter more than §4's prose.

| id | task | holder | anchor id (use in `RE:`) | depends on | status |
|---|---|---|---|---|---|
| `MGR-T1` | Rule on BT1's four fidelity questions for `BT1-ALGO-1` | R1 | `BT1-ALGO-1` | — | **DONE** — `msgs/03_R1_BT1…`, **DIVERGENT** on the direction half |
| `MGR-T2` | Wall A minimum-change spec (edits A1–A8) | R2 | `R2-D3` | — | **DONE** — `research/R2_wall_a_spec.md` |
| `MGR-T3` | Paired re-emission design for `R3-D5` Tier-1 items | R3 | `R3-D5` | — | **DONE** — `research/R3_pairing_design.md`; **and it found `D48`** |
| `MGR-T5` | Condition-group audit — R1's surface: `structure`, `supplydemand`, `fibonacci` (12) | R1 | `DISC-LEAD-05` | — | **IN FLIGHT** — `research/R1_group_audit.md`; **already yielded `D49`** |
| `MGR-T10` | Rule on the residual of BT3's eight fidelity questions | R3 | `BT3-ALGO-1` | — | **DONE** — `msgs/10_R3_BT3_re-verify-ALGO-1-questions.md` covers Q1, Q3, Q5, Q7, Q8(b); `msgs/03_R3_BT3…` had covered Q2, Q4, Q6, Q8(a). **All eight ruled.** |
| `MGR-T18` | Apply the two items that block `BT3-ALGO-1`'s reportability: the one-line `volatility=row["vol"]` fix (Q4, DIVERGENT) and the intra-timestamp look-ahead from 2,900 zero-duration trades | BT3 | `BT3-ALGO-1` | `MGR-T10` (done) | **OPEN — now the gate on every BT3 number** |
| `MGR-T17` | **Re-read `x_exits`' stop-kind comparison against `D45` and `D49`** | **R3** | `D49` | — | **OPEN — highest-value re-read available** |
| `MGR-T14` | Fix `absorption_bar`'s direction rule; re-ask fidelity | BT1 | `BT1-ALGO-1` | `MGR-T1` | **OPEN** |
| `MGR-T6` | Reconcile `data/archive/` against `csv/raw/` bar-for-bar on the overlap | BT1 | `BT1-REQ-1` | — | **OPEN — priority raised.** `BT2-REQ-3` is the second track to hit the substrate wall |
| `MGR-T16` | Fix `D44` (circular block bootstrap), 1 line + 1 test | parent | `D44` | — | **OPEN** |
| `MGR-T12` | Extract BT1's D38 registration guard to `roundtable/lib/registry_guard.py` | parent | `R1-REQ-1` | — | **OPEN** |
| `MGR-T13` | Time-of-day vs 20-bar-trailing volume normalisation, as a question about the corpus | R1 | `R1-REQ-2` | — | **OPEN** |
| `MGR-T15` | Event gate on MGC/MCL — the symbols where the HIGH calendar is not empty | BT2 | `R2-Q1` | `MGR-T6` for substrate | **IN FLIGHT** — `BT2-ALGO-1` ruled **FAITHFUL**, so BT2 may measure |
| `MGR-T8` | Tier-0 item 8: `mode="block"` vs `mode="iid"` on the R series | BT3 | `R3-D5` | `MGR-T16` | **GATED** — may run; **not reportable** until `D44` is fixed |
| `MGR-T9` | Tier-0 item 7: account-governor replay over `geo_trades.json` | BT3 | `R3-D5` | `MGR-T10` | **GATED** — no stateful number until Q1/Q3 are ruled |
| `MGR-T11` | Direct per-trade serial-dependence test (lag-1..10 / runs / Ljung-Box) | BT3 | `BT3-REQ-1` | `MGR-T10` | **QUEUED** |
| `MGR-T7` | Condition-group audit — R2's surface: `time` (4) **+ the Axis C consolidation** | R2 | `R2-Q1` | `MGR-T2` (done) | **OPEN** |
| `MGR-T4` | Condition-group audit — R3's surface: 7 groups, 31 conditions | R3 | `DISC-LEAD-05` | `MGR-T13` | **QUEUED** |
| `MAIN-01` | **Mode SCOPE** — what sub-task breakdown does it need, at what granularity | R1 | `MAIN-01` | `MGR-T1` (done) | **OPEN** |

**Shape:** 1 main task carrying **0 allocated sections** (by design, §2) and one open Mode-SCOPE
request; **19 standalone tasks** — 4 done, 2 in flight, 8 open, 2 gated, 3 queued.

**Reconciled at 00:25 ET against what is on disk.** Four of these were completed by agents running in
parallel with the board being written, including two (`MGR-T2`, `MGR-T3`) that were done before they
were ever dispatched. `MGR-T3`'s output found `D48`, which then amended the gate that made `MGR-T3`
necessary — the tightest feedback loop this pipeline has produced so far, and an argument for
dispatching one section at a time rather than a whole main task.

### Requests received after this board was laid out — triaged, not ruled

Nine arrived while I was ruling the first eight. **Two got numbers immediately** because they bear on
gates set earlier in the same file: `R3-REQ-1` → **`D48`** (a `replace`d strategy inherits its `_id`,
so **both arms of a paired comparison collide into one result and the measured difference is exactly
zero** — a false null indistinguishable from the finding, and it defeats the `R-6` gate itself), and
R1's `StopKind.RANGE` finding → **`D49`**. **The other seven are `RECEIVED`** with a preliminary triage
line each in ADJ-11c, **none blocking its filer**:

| `R2-REQ-1` | `R2-REQ-2` | `R2-REQ-3` | `R3-REQ-2` | `R3-REQ-3` | `BT2-REQ-1` | `BT2-REQ-2` | `BT2-REQ-3` |
|---|---|---|---|---|---|---|---|
| likely `D48` family | likely `D46` instance | numbers next turn | **do not start building before I rule** | accepted, no ruling needed | likely a `D<n>` | likely a missing primitive | raises `MGR-T6` |

**`RECEIVED` is a promise.** If any of these is still `RECEIVED` two turns from now, that is a failure
of mine and not a backlog.

> **Numbering irregularity, recorded rather than tidied.** `MGR-T3`…`MGR-T13` were allocated inside
> `ADJUDICATIONS.md` while I was ruling, before the board was laid out, so the table above is in
> dependency order and the ids are not sequential. `MGR-T4` is the R3-surface audit and `MGR-T6` is
> the store reconciliation — **not** what a reader guessing from position would assume. Renumbering
> would break the `ADJUDICATIONS.md` citations that are the only record of why each task exists, so
> the ids stand. Read the table, not the numbers.

> **Numbering irregularity, recorded rather than tidied.** `MGR-T3`…`MGR-T13` were allocated inside
> `ADJUDICATIONS.md` while I was ruling, before the board was laid out, so the table above is in
> dependency order and the ids are not sequential. `MGR-T4` is the R3-surface audit and `MGR-T6` is
> the store reconciliation — **not** what a reader guessing from position would assume. Renumbering
> would break the `ADJUDICATIONS.md` citations that are the only record of why each task exists, so
> the ids stand. Read the table, not the numbers.

---

## 4. The open and queued tasks, in detail

### `MGR-T10` — R3 rules on `BT3-ALGO-1`'s eight fidelity questions. **Dispatch this first**

BT3 has posted eight questions (`msgs/04_BT3_R3_verify-ALGO-1.md`; `backtest/BT3/VERIFY.md` shows
`ASKED`) and states: "I am not reporting a single stateful number from it until you answer." Per
**R-5** that is correct and it means **every number BT3 can produce is blocked on one R3 turn.**
Two of the eight decide whether the result means anything at all:

- **Q1 — population unit.** 176 independent $50,000 accounts versus one pooled account **disagree
  by 24×**: 26.0% of trades survive unpooled, 1.08% pooled. Which reading does `III-14` intend?
- **Q3 — exposure keyed by symbol or strategy.** The live path permits one position per *symbol*
  before the concurrency cap (`manager.py:245-248`); on a pooled artefact of 22 correlated arms that
  collapses them to one slot and produces 1,126 refusals. Faithful, or an artefact of applying a
  live rule to a research pool?

The remaining six (replay scope, volatility multiplier, `is_live_eligible`, the trade cap counting
closes not opens, and two more) are each a one-edit correction. **R3 must not use this turn to argue
the finding** — `PIPELINE.md` §4: a disagreement with the finding is a `REQUESTS.md` entry, not a
fidelity dispute.

Two rulings R3 should carry into the reply, both already made: **ADJ-9b** (the shipped
`correlation_group` is mis-specified for `max_correlated_positions`' purpose, so P2 moves from
`INEXPRESSIBLE-ARCH` toward "expressible and mis-specified"), and **ADJ-9c** (Tier-0 item 8's claim
must narrow — it is a precondition check, not the verdict on Channel 4b's streak sub-case).

### `MGR-T14` — BT1 fixes `absorption_bar` and re-asks

R1 ruled `BT1-ALGO-1` **DIVERGENT in the direction half only**, and the reason is an identity, not a
judgement: `Absorption.direction()` is `close_pos > 0.5`, which for `H > L, V > 0` is *exactly*
`sign(estimated_delta) > 0` — verified algebraically and on 78 of 78 firings across all six cells
`[repo-verified: msgs/03_R1_BT1_re-verify-ALGO-1.md]`. So ALGO-1's module header claim "with no
delta term in it anywhere" is false: there is one, wearing another variable name. `absorption_present`
(the direction-free FILTER) is **FAITHFUL** and may proceed.

**This is the fidelity loop working exactly as designed** and it is worth naming as such: BT1's
"where I had to choose" field is what made the catch possible, and the cost of not having asked would
have been a measured null attributed to the absorption *shape* when the direction rule was a proxy
the repo has already screened ~2.97M times.

### `MGR-T6` — the store reconciliation. One task, once, for all three backtesters

Ruled in **ADJ-6**. Bar-for-bar on the overlapping window between `data/archive/` and `csv/raw/`,
written down, before any archive number is reported. Assigned to BT1 because it raised it
(`BT1-REQ-1`) and needs it first. **Three backtesters each doing this privately is the duplication
this board exists to prevent.**

**What BT1 should not expect from it.** It does not rescue `BT1-ALGO-1`'s power. ALGO-1 fires on
2–41 bars per `csv/raw` series; the archive is ~2.3×, so ~5–95, against `toolkit.FLOOR = 20`. BT1's
pre-registration — that no test will separate ALGO-1 from its placebo — most likely still holds, and
**that pre-registration surviving a 2.3× sample increase is a better result than the sweep would
have been.** Report it that way.

### `MGR-T5` / `MGR-T4` / `MGR-T7` — the condition-group audit, split three ways

`DISC-LEAD-05` proposed one auditor for "16 groups / 71 conditions". **Both numbers are wrong and
the task is a third smaller** (ADJ-8): R1-D4 delivered verdicts for **32 conditions across 8 groups**
(`orderflow` 3, `volume` 3, `profile` 6, `vwap` 5, `liquidity` 7, `imbalance` 3, plus `openinterest` 2
and `news` 3), not 8 conditions across 3. Discovery counted only the three *phantom* groups. The
remainder is **11 groups / 47 conditions**, split by code surface because the audit's value comes
from having read the indicator underneath:

| task | holder | groups | n |
|---|---|---|---|
| `MGR-T5` | R1 | `structure`, `supplydemand`, `fibonacci` | 12 |
| `MGR-T4` | R3 | `trend`, `momentum`, `meanreversion`, `volatility`, `regime`, `multitimeframe`, `candlestick` | 31 |
| `MGR-T7` | R2 | `time` | 4 |

**Do not re-derive the seven known aliases.** `X-9` records that seven filter names are exact
aliases for strategy-group membership — `avoid_lunch`≡REVERSAL, `opening_drive_window`≡OPENING_RANGE,
`after_opening_range`≡LIQUIDITY, `mtf_not_conflicted`≡PULLBACK, `regime_trending`≡TREND,
`regime_ranging`≡MEAN_REVERSION, `volatility_compressed`≡BREAKOUT — and **five of the seven sit
inside these 11 groups** `[repo-verified: AVENUES.md X-9, citing 21-study-programme.md:118-141]`.
Cite `X-9`. The audit's new content is the other 42 conditions.

`MGR-T4` is **queued behind `MGR-T13`**: `volatility` and `regime` both read volume against a
window, and an auditor who does not know which of the repo's two volume norms a condition uses
cannot classify it.

`MGR-T7` additionally carries **the Axis C consolidation** (ADJ-1) — the one thing that ruling
leaves unowned. For `II-10`, `II-11`'s clock half, `III-12` and the `time`+`news` groups: state what
is satisfiable by arithmetic on the bar's own timestamp and what is not. **`III-12` is cited from
R3's existing verdicts, not re-derived** — this is a cross-reference task, not a cross-track audit.

### `MGR-T13` — the two volume norms

Granted and promoted from a sub-task (ADJ-10d). The library holds two volume norms, uses both, in
different places, **with no statement anywhere about which is intended**, and they select populations
differing by **5–27× on identical bars**: the 20-bar trailing mean in `detect_imbalances`
`[repo-verified: indicators/structure.py:452-455]` versus the time-of-day norm in `relative_volume`
(same clock minute, previous 20 sessions) `[repo-verified: indicators/volume.py:266-285]`
`[measured: BT1, backtest/BT1/code/frequency.py]`.

Because intraday futures volume has a strong U-shape, **any condition in this repo that reads volume
against a rolling window may be measuring time of day rather than participation** — which touches
`BRIEF.md` rule 6 and the ICT kill-zone finding. **Binding design constraint, R1's, adopted
verbatim: if built, both axes take the time-of-day norm or neither does.** A time-of-day volume norm
against a rolling range norm conjoins two different reference populations and the result is
uninterpretable.

### `MGR-T3` — the paired re-emission design

Ruled in **ADJ-5**, and it is a design task, not a restatement. R3 has stated the D15 pairing
requirement twice; what is missing is **how** you re-emit the same rule sets across exit arms given
that `generate_combinations` samples the exit jointly with the rule set, and given D43's hash fix
(which is what made `StrategyFilters` variants distinguishable at all). Two orderings I added:

1. **Tier-1 item 1 (trailing stop on) must not run before A-2 is fixed.** The exit reason reports as
   `STOP`, so `ExitReason.TRAIL` can never be emitted. A trail arm run first yields numbers whose
   exit mix cannot be read — and exit mix is the Channel-3 quantity that makes the trail
   non-cancelling in the first place. The 2-line fix at `engine.py:419-421` is a prerequisite.
2. **Tier-0 needs no pairing and must not wait for this.** `MGR-T8` and `MGR-T9` are replays over
   existing artefacts; there is no exit arm to pair.

### `MGR-T12` / `MGR-T16` — the two parent-session tasks

`MGR-T12`: extract BT1's D38 registration guard to `workspace/roundtable/lib/registry_guard.py`.
It goes to the parent because a helper imported by all three backtesters cannot live in one owner's
`code/` without giving that owner a write on the others' dependency (ADJ-10c). **Until it exists,
BT2 and BT3 import BT1's copy read-only rather than re-implement it** — `OWNERSHIP.md` already
grants "read, and run" on another backtester's `code/*`. The guard distinguishes "key present, value
`None`" (warming up) from "key absent" (wrong bar grid, or `register_frame` never called) and counts
the second — the difference between a custom condition failing **loudly** and failing **silently**,
which is what D38 causes.

`MGR-T16`: the one-line D44 fix, `path.extend(r_values[(start + k) % n] for k in range(block))`.
Gates `MGR-T8`'s reportability.

---

## 5. Who holds what

| agent | in flight | next | queued behind |
|---|---|---|---|
| **R1** | `MGR-T5` (group audit, 12 conditions) | **`MAIN-01` Mode SCOPE**, then `MGR-T13` | — |
| **R2** | `MGR-T2` (Wall A spec) | `MGR-T7` (`time` audit + Axis C) | `MGR-T2` |
| **R3** | — | **`MGR-T10` (rule on BT3's eight questions) — dispatch first**, then `MGR-T3`, then `MGR-T4` | — |
| **BT1** | — | `MGR-T14` (fix direction rule, re-ask), then `MGR-T6` (reconciliation) | — |
| **BT2** | `MGR-T15` (event gate, MGC/MCL) | — | `MGR-T6` for substrate |
| **BT3** | `MGR-T8`, `MGR-T9` (both GATED) | `MGR-T11` | `MGR-T10`, `MGR-T16` |
| **discovery** | burst 02 | corrections routed in `msgs/07`: `DISC-LEAD-05`'s count, `X-15`'s open half, `I-12` | — |
| **parent** | dispatch | `MGR-T12`, `MGR-T16`, `DEFECTS.md` D44–D47, `REGISTRY.md` grammar | — |

**Nothing on this board is assigned to two agents, and no task requires an agent to write a file it
does not own.** Where a ruling changes another agent's verdict (ADJ-9b → R3's P2; ADJ-10a → R3's
`R3-Q1` row; ADJ-7 → R1's `P9` row and R3's `R3-D6`) it is **routed as a message for the owner to
apply**, never applied by me.

---

## 6. What is blocking what, in one place

**Which `VERIFY.md` questions are open, by number.** Added after R3 and BT3 raced: BT3 posted eight
questions at 02:12 and R3 ruled at 02:16 **from the code**, having checked `msgs/` when it held only
`01` and `02`. R3 handled that correctly — it ruled rather than leave BT3 blocked, and invited a re-ask
"on the difference only" — but four *inferred* choices got ruled while two of BT3's eight did not,
because they ask for the finding's **intent** and cannot be answered from a code read. So the board
now tracks question numbers, not just algorithm status:

| algorithm | verdict | open question numbers | note |
|---|---|---|---|
| `BT1-ALGO-1` | **DIVERGENT** (direction half) | none | all four ruled; `absorption_present` is FAITHFUL and may proceed |
| `BT2-ALGO-1` | **FAITHFUL** | none | eleven choices ruled; BT2 may measure, with four narrowing amendments |
| `BT3-ALGO-1` | **DIVERGENT** (one material, one reporting) | **none — all eight now ruled** | R3 closed the race itself, across two messages, and said so explicitly: `03` covered Q2/Q4/Q6/Q8(a) from the code, `10` covered Q1/Q3/Q5/Q7/Q8(b). **Q1 ruled PER_STRATEGY**, which confirms §7 pre-registration 3. Reportability now gates on `MGR-T18`, not on a question |

**The lesson survives the race being resolved.** R3 closed it unprompted, but only because it noticed
its own `03` had not reached BT3's posted list — and `msgs/` is write-once, so it needed a second
message to do it. **The board tracking question numbers is what makes that visible without depending
on the ruler noticing.** Keep the column.

| blocked | by | consequence if it stays blocked |
|---|---|---|
| every **stateful** number BT3 can produce | `MGR-T18` — the Q4 `volatility=row["vol"]` fix and the intra-timestamp look-ahead from 2,900 zero-duration trades | two of the cheapest real measurements in the programme stay unreportable. **`MGR-T10` is discharged**: all eight fidelity questions are ruled |
| every paired re-emission, all tracks | `D48` discipline (`_id=None` + arm-id assert) | **a false null indistinguishable from the finding.** This defeats `R-6` itself, which is why `R-6` is amended |
| the interpretation of `x_exits`' stop-kind verdict | `MGR-T17` | a settled negative finding keeps two named, measured, artefactual candidate explanations (`D45`, `D49`) and nobody has checked which |
| `MGR-T8`'s reportability | `MGR-T16` (D44 fix) | the block arm's drawdown/streak/p05 statistics are biased by construction; BT3 flagged rather than silently corrected |
| every archive-substrate number, all three backtesters | `MGR-T6` | rare-signal algorithms stay under `FLOOR = 20`; the only never-searched out-of-sample data in the repo stays unused |
| `MGR-T4` (R3-surface audit) | `MGR-T13` | `volatility` and `regime` cannot be classified without knowing which volume norm they read |
| Tier-1 item 1's interpretability | the A-2 fix at `engine.py:419-421` | a trail arm whose exit mix cannot be read, i.e. an uninterpretable number |
| `MAIN-01`'s sections | R1's `SCOPE.md` | correct — I am not allowed to decompose it (`PIPELINE.md` §2) |
| `MGR-T` ids in message headers | `REGISTRY.md` + `check_refs.py` grammar | commits fail on any message whose `RE:` names a board task; R-12 is the workaround |

---

## 7. Pre-registrations for round 2

Round 1's pre-registrations were the most useful thing `DIVISION.md` contained, because three of
them were refuted and the refutations were diagnosable. **R-11 is the lesson**: my error each time
was treating search volume as search width. So these are written before the tasks run, and they are
falsifiable.

1. **`MAIN-01` closes `CLOSED-EMPTY`.** I predict R1's scope finds the minute-snapped approximation
   defensible only at bar sizes so coarse that the resulting series has too few bars per session to
   test anything the confound question needs — i.e. the defensible range and the useful range do not
   overlap. **Falsified by** a scope that names a bar size where both hold, with the error bound.
2. **The group audit's hit rate falls well below R1's 3-of-3.** R1 audited the groups most likely to
   be misnamed — the ones whose names promise participant information. `trend`, `momentum` and
   `meanreversion` name arithmetic they actually do. I predict **≤8 of the 47 remaining conditions
   land on PROXY**, and that most findings are `DEGRADED` or `HONEST-DERIVED-BUT-BROKEN` instead.
   **Falsified by** ≥15 PROXY verdicts.
3. **R3's answer to BT3's Q1 is PER_STRATEGY, and the 24× gap is the finding.** I predict R3 rules
   the 176-independent-account reading faithful to `III-14` and the pooled reading a diagnostic of
   pooling — and that the 24× disagreement turns out to be more interesting than either number,
   because it measures what `run_portfolio` does not do (R3's own B-4: it "does not simulate a
   portfolio"). **Falsified by** R3 ruling the pooled reading the intended one.
4. **`MGR-T13` reframes at least one settled rule without contradicting it.** The two volume norms
   differing 5–27× on identical bars, plus `BRIEF.md` rule 6 and the kill-zone finding ("more range
   and volume, and no more direction"), are close enough that I expect the norm question to explain
   part of a settled result. **Falsified by** the two norms selecting populations whose expectancy
   distributions are indistinguishable.
5. **At least one Tier-1 item never runs this programme**, because R-6 doubles each one's cost and
   the queue behind `MGR-T10` is long. I am pre-registering that as an acceptable outcome: **an
   untested item with a stated reason beats a tested item that is confounded.**
6. **Against myself, third time:** ADJ-1 and ADJ-2 are boundary calls I made after two of three
   tracks told me my boundaries were wrong. The most likely error is that **Axis C as a tag rather
   than a class is too weak to survive** — a tag with no owner is a tag nobody applies, and I have
   put exactly one task (`MGR-T7`) behind it. **Falsified by** `MGR-T7` returning a consolidation
   that a reader can act on. **Confirmed** if Axis C is never mentioned again by anyone but me.
