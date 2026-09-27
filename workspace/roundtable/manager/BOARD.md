# BOARD — the task board the pipeline runs on

**Owner:** manager (`OWNERSHIP.md`). **Opened:** 2026-09-26 22:11 ET. **Updated:** 2026-09-27 04:05 ET, round 3.
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
| R-6 | **A Tier-1 exit/filter result from an unpaired sweep is NOT reportable.** D15: only 93 of 8,317 shipped rule sets exist with two different exits, so an unpaired exit comparison is confounded with the entry. Paired re-emission of the same rule sets, or nothing. **Amended (ADJ-11a): a paired re-emission that does not pass `_id=None` on every `replace` and assert arm-id uniqueness at emission is not a paired re-emission** — `D48` makes both arms collide into one `BacktestResult` with a measured between-arm difference of exactly zero. **Amended again (ADJ-16a): a paired re-emission reports its entry-timestamp overlap beside its result.** On the only one on disk the two arms share a median of **61.8%** of entries, 17 of 258 pairs reach 90%, median trade-count ratio 1.332 — because a positioned strategy does not look for signals (`engine.py:304-309`), so any axis changing holding duration changes which later bars the arm is flat for. A pair below a stated overlap floor is a **population** comparison, not an exit comparison. | ADJ-5, ADJ-11a, ADJ-16a |
| R-7 | **`csv/raw/` is mandatory for any number placed beside a published `scan_reports/` figure.** `data/archive/` is permitted for a number that is **labelled with its substrate** and **never pooled with a `csv/raw` number inside one statistic** — and only after `MGR-T6` lands. Before then, archive numbers are `PROVISIONAL-SUBSTRATE`. | ADJ-6 |
| R-8 | **Any trade dump intended for later operating-layer work records `entry_price`, `initial_stop` and `symbol`.** Three keys; without them account sizing is a re-run, not a read, and the link dies the moment the slicing or the snapshot changes. | ADJ-9d |
| R-9 | **An agent wanting a `D<n>` describes the defect and does not name a number.** "Next free" is a read of a file another agent may be about to change; it nearly collided this turn. | ADJ-9 numbering note |
| R-10 | **Ordered chains are inexpressible as confluences and buildable as single conditions** — but a sequence built as one condition **cannot be ablated leg-by-leg**. Anyone building one owes that caveat up front. D37's scope, narrowed. | ADJ-7 |
| R-11 | **Any claim of the form "this has already been tested" must name the dimension that was varied.** `n = 2.97M` is coverage of the dimension the sampler moved in and nothing else. This is the round-1 error that produced three wrong pre-registrations. | ADJ-5 |
| ~~R-12~~ | **RETIRED 2026-09-27 04:05 ET (ADJ-16d).** The parent extended `check_refs.py`'s grammar and I verified it: `MGR-T<n>`, `ADJ-<n>`, `R-<n>`, `D-L1`-style notes, `X-<n>`, `M<n>` and `EF<n>-H<n>` all resolve, with issuers `(R[1-6]\|BT[1-6]\|EF[1-7]\|DISC2?)`. **`MGR-T` and `ADJ` ids may now appear in a `RE:`/`ALSO:` header.** The old workaround stays valid so no existing message is malformed, but nobody should cite `R-12` again except historically. | ADJ-16d |
| R-13 | **`R-5` applies to a harness component exactly as it applies to an algorithm.** A profitability number from an unvalidated session harness is **not weak, it is unknown** — nobody can say what rule the trades obeyed. Validation means EF1's `violations()` returns **zero**, or returns a **named, enumerated carve-out** with the sessions listed and the information it consumes stated. Behind it: two independent harnesses measured 43 and 0 `SPANS_WINDOW` violations on the same 400 strategies. | ADJ-15a |
| R-14 | **A `VOID` verdict is stated per (symbol, timeframe, *frame*) — plus the value of any scope flag that decides it — and carries a reachability line: `REACHED` (the corpus builds this configuration; a published row may be affected) or `FORWARD` (it does not; a hazard for future work).** A VOID verdict with no reachability line is incomplete, as a result with no placebo is incomplete under `R-2`. Behind it: `mtf_aligned` VOID in 23 of 23 frame-of-one cells and alive in 23 of 23 corpus cells at the same (symbol, timeframe). | ADJ-13a |

**Verdict vocabulary for the condition-group audit — one vocabulary, ADJ-13a.** ADJ-8's four-term set
is **retired** (readable, mapped, not for new work). The canonical set is `BRIEF.md`'s, extended by one
term: **`CLEAN`** (arithmetic does what the group name claims) / **`PROXY`** (a correlate computed from
data that cannot contain the named object) / **`DEGRADED`** (the named object, with a loss that varies
by symbol or timeframe) / **`VOID`** (cannot fire in this configuration — 0 of N, structurally; see
`R-14`) / **`DEAD`** (its inputs are absent everywhere, so it never fires anywhere) / **`MISNAMED`**
(computes a different, well-defined thing than its name says) / **`MISFILED`** (arithmetic honest, its
**condition group** names a different mechanism, so a template requiring that group can be satisfied
by a predicate from another — ADJ-13b).

**R6's report-level vocabulary is orthogonal and is not merged** — `STANDS` / `WEAKENED` / `INVALID` /
`UNAFFECTED`, with sub-kinds `SUBSTITUTED` / `DEGENERATE` / `ZERO-FIRE`. It grades a published claim;
the table above grades a condition. Conflating them is how a retraction gets read as a verdict on a
condition, or the reverse.

---

## 2. Main tasks

**One exists.** Only discovery allocates `MAIN-<nn>` (`REGISTRY.md`).

### MAIN-01 — the sampling clock: is part of this repo's null result a property of wall-clock bars?

| field | value |
|---|---|
| **Raised by** | discovery burst 01, `discovery/MAIN_TASKS.md` |
| **Avenue** | `I-12`, `CLOSED-FOUND` |
| **Sections allocated** | **none, and now none ever** (ADJ-16c) |
| **Current state** | **CLOSED-EMPTY / reason `SUBSTRATE-1M`** — scope delivered by R5 (`research/R5_SCOPE.md`), ruled in ADJ-16c |
| **Killable** | it was, and it was killed — by one honest measurement, which is what ADJ-2 ruled the correct exposure |

> **Closed 2026-09-27 04:05 ET, and the reason is not the one I pre-registered.** R5's scope
> measured the substrate and the task dies **one gate earlier than pre-registration 1 predicted**.
> The total futures 1-minute substrate in this repository is **~6.5 RTH sessions per symbol**: the
> archive's 1m series **starts inside** `csv/raw`'s span and ends ~3 sessions after it, so the union
> is **9,069 unique minutes, overlap 2,812, span 9 calendar days** `[measured, R5: wc -l on both
> stores; set-union after normalising both to UTC]`, and the only deep 1-minute store is
> `data/MGC_1m.csv` — 465,232 rows, Oanda CFD, the wrong instrument. **The ledger must carry
> `SUBSTRATE-1M`, not approximation error**, because `AVENUES.md`'s revisit rule turns on the reason:
> a tape arriving does **not** create 1-minute history, and "the approximation was too poor" is a
> claim nobody has measured. The tape-blocked schemes stay `DEFERRED / BLOCK-SUBBAR` — that reason
> *can* change — which is discovery's file to write and is routed, not written by me.
>
> **`S2` survives the closure and moves.** It constructs nothing, so the substrate cannot kill it,
> and its content is the **time-of-day-residualised** activity stratum at the `(symbol, tf, ts)` join
> — which is exactly what **`MGR-T13`** was promoted to settle. Re-filed there, with R1's binding
> constraint verbatim: both axes take the time-of-day norm or neither does.
>
> **The substrate note in this section is corrected.** It said the usable substrates are
> `data/{MES,MGC,MNQ}_1m.csv` and `data/archive/*.jsonl`. **That is a 60-minute statement and it is
> false at 1 minute.** `BRIEF.md`'s "the archive extends the span by ~6,000 bars *before* everything
> searched" is true at 60m and false at 1m. **Third appearance of the substrate wall**, after
> `BT1-REQ-1` and `BT2-REQ-3`, at a third timeframe — which is why `MGR-T6` is extended to the 1m
> overlap (ADJ-16c) rather than left at 60m.

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
>
> **Round-3 status, 2026-09-27 04:05 ET. Twelve agents are live** and the board now carries **two
> programmes**: the research pipeline (§3, §4) and the **edge-finding programme** (§8, new), which
> came from the account owner and is not a `MAIN-<nn>`.
>
> **The holder column is advisory from here (ADJ-16e).** It went stale at dispatch time twice in one
> round — `MGR-T4` went to R4 when R1 had already audited all 11 groups, and `MAIN-01`'s scope went to
> R5 when this table names R1. Both agents handled it well (R4 converted its task into a declared
> independent replication; R5 proceeded and told me to merge rather than supersede), so nothing was
> lost — but twice is a mechanism, not luck, and the mechanism is that this file is written once per
> turn while twelve agents write continuously. **The dispatching parent reconciles against `ls` of the
> target's output directory before dispatch. The output directory is authoritative; this column is a
> hint.**

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
| `MGR-T4` | Condition-group audit — R3's surface: 7 groups, 31 conditions | **R4** (reassigned) | `DISC-LEAD-05` | `MGR-T13` | **DONE** — `research/R4_group_audit.md`, delivered as a **declared-anchor independent replication**; yielded `D50`, `D54`, `D58` |
| `MAIN-01` | **Mode SCOPE** | **R5** (reassigned) | `MAIN-01` | `MGR-T1` (done) | **DONE** — `research/R5_SCOPE.md`; `MAIN-01` now **CLOSED-EMPTY / SUBSTRATE-1M** (ADJ-16c), and it found `D51` |
| — | **Report audit** — 104 published claims across four `scan_reports/` files against rounds 1–2 | **R6** | `D12` | — | **DONE** — `research/R6_report_audit.md`: **64 STANDS / 33 WEAKENED / 6 INVALID / 1 UNAFFECTED**; yielded `D52` and `D53` instance 6 |
| — | **`MAIN-02`** — the cross-sectional universe; the region the sampler never moved in | **DISC2** | `MAIN-02` | — | **ALLOCATED by discovery** (`discovery2/MAIN_TASKS.md`). Framed diagnostically and killable at its first gate (the roll convention). **Not mine to decompose** (`PIPELINE.md` §2) |

### Round-3 tasks

| id | task | holder | anchor id | depends on | status |
|---|---|---|---|---|---|
| `MGR-T19` | **Reconcile EF1's and EF3's session harnesses bar-for-bar on the 19 sessions where they disagree.** Not argued — measured. EF1 owns the harness; EF3 supplies its arm and its 0-violation audit | **EF1** + EF3 | `EF1-H1` | — | **OPEN — and it is the gate on every EF profitability number (`R-13`)** |
| `MGR-T20` | **`D50`'s blast radius** — every published row whose frame contains a timeframe > 1440, **plus the two numbers `BRIEF.md` rule 2 now depends on**: the count of `primary_tf = 1440` rows inside the 366 and 1,151 populations behind z = −4.09, and the same z recomputed with those rows excluded | **BT4** | `D50` | — | **IN FLIGHT — highest-value measurement on the board** |
| `MGR-T21` | **Verify `D52`** (`R6-D1`) — the sub-tick band census and the daily condition census, re-measured independently | **BT6** | `D52` | — | **IN FLIGHT** |
| `MGR-T22` | **R5's `S2` — the activity-stratification confound test.** Corrected at 04:20 ET: `LEDGER.md` records no scope for BT5, but **BT5's own code does** — `backtest/BT5/code/activity.py` and `s2.py` are `BT5-ALGO-1` parts 1 and 2, executing `S2` in two layers (unit = bar, then unit = strategy, the latter per R3's `PER_STRATEGY` ruling over the 176 strategies). This is the board's holder column going stale again, in the same round I ruled it advisory (ADJ-16e) — **found by reading the output directory, which is exactly the remedy** | **BT5** | `MAIN-01` | `MGR-T13` for the volume norm | **IN FLIGHT** |
| `MGR-T28` | **Verify `D51`** — the `BarSeries.append` collapse floor. Exact, needs no tape, and it is the one new false-null mechanism of the three with **no verifier assigned**: BT4 has `D50`, BT6 has `D52`, BT5 has `S2` | **unassigned** | `D51` | — | **OPEN — the only round-3 defect with no verification in flight** |
| `MGR-T23` | `scout.rank`'s `suffix` dict covers `{1440,240,60,15,5}` against `FRAMES`' `{5,15,30,60,240,1440}`, so `rank(sym, timeframe=30)` raises. **Fix it and the frame-of-one VOID together** — the unreachable `FRAMES.get` fallback at `scout.py:230` is currently the only thing preventing that VOID from contaminating anything | parent | `R4-REQ-4` | — | **OPEN, trivial, with a warning attached** |
| `MGR-T24` | **Exogenous-entry replay harness** — the only route to trade-level pairing. Granted, **ranked low on purpose**: it touches `engine.py`'s hottest loop with twelve agents live, and `R-6`'s new overlap number gets most of the value at none of the risk. **Read `edge/EF1/code/` first** — EF1 has built the same kind of object | R3 | `R3-REQ-2` | `MGR-T19` (so the two are not built twice) | **OPEN, low priority** |
| `MGR-T25` | Retro-fit `R-6`'s entry-timestamp-overlap number into `MGR-T3`'s pairing design and into the paired results already computed | R3 | `R3-REQ-2` | — | **OPEN, cheap** |
| `MGR-T26` | **`D52`'s reporting consequence for `scan_reports/`** — two rows INVALID (`A16`), four strongly WEAKENED (`A15`). R6 delivered the restatements; nobody owns applying them, and `scan_reports/` is outside every agent's ownership | parent | `D52` | `MGR-T21` | **OPEN — the one obligation ADJ-12 creates and does not discharge** |
| `MGR-T27` | **`R-14` retro-fit**: a reachability pass (`REACHED` / `FORWARD`) over the six VOID verdicts already on the record. R6 has in effect done four of them; the gap is the other two | R1 | `R1-REQ-5` | — | **OPEN, small** |

**Shape:** 1 main task **closed `CLOSED-EMPTY`** with 0 sections ever allocated; 1 further main task
(`MAIN-02`) allocated by discovery and not decomposed by me; **28 standalone research tasks** — 8
done, 5 in flight, 12 open, 2 gated, 1 queued; **plus a second programme of 7 agents in §8.**

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

> ### All twelve requests are now ruled (ADJ-16, 2026-09-27 04:05 ET). Nothing is `RECEIVED`
>
> **The promise was kept and one of my own triage guesses was wrong**, which is the argument for
> labelling guesses as guesses:
>
> | request | triage said | **ruling** |
> |---|---|---|
> | `R2-REQ-1` | likely `D48` family | **`D55` — wrong family.** `D48` is an id not recomputed; this is a behaviour-bearing field never in the hash, i.e. the **`D43`** family. Fourth instance |
> | `R2-REQ-2` | likely a `D46` instance | **`D46` instance 3.** Confirmed |
> | `R2-REQ-3` | numbers next turn | **defect 1 → `D56` inst. 1; defect 2(a) → `D47` inst. 2 (and `D47` becomes a class); defect 2(b) → `D57`** |
> | `R3-REQ-2` | do not build before I rule | **granted as `MGR-T24`, ranked low, and `R-6` amended a second time** — the cheap half (report the entry overlap) is available today |
> | `R3-REQ-3` | accepted | closed |
> | `BT2-REQ-1` | likely a `D<n>` | **`D56` instance 2**, not its own number — the same object, the news proximity clock |
> | `BT2-REQ-2` | likely a missing primitive | **confirmed, declined as a defect** — and EF1 has since built the clock-event form of it |
> | `BT2-REQ-3` | raises `MGR-T6` | **(a) run it with its placebo** (69/164 admissible bars is BT1's situation and gets ADJ-6's framing); **(b) needs no sub-task — the edge programme already measured archive 15m** at 3,746 bars / 57.90 days with store equivalence verified |
> | `R4-REQ-1`…`5` | — | **`D50` / `D54` / `D58` / declined (`MGR-T23`) / `D53` inst. 3–4** |
> | `R1-REQ-5` / `R1-REQ-6` | — | **`VOID` adopted with a three-part amendment (`R-14`)** / **the 8 overlapping groups are ONE audit** (ADJ-16b) |
> | R5's four | — | ADJ-16c: `CLOSED-EMPTY / SUBSTRATE-1M`; §2's substrate note corrected; `S2` → `MGR-T13`; 1m overlap → `MGR-T6` |

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

**Twelve agents live, two programmes.** Holder column is advisory — reconcile against the output
directory before dispatch (ADJ-16e).

| agent | in flight | next | queued behind |
|---|---|---|---|
| **R1** | `MGR-T5` (group audit, 12 conditions) | `MGR-T13` (+ R5's `S2`), then `MGR-T27` (`R-14` reachability pass); **apply `MISFILED` to the `momentum` group verdict** | — |
| **R2** | `MGR-T7` (`time` audit + Axis C) | — | — |
| **R3** | — | `MGR-T17` (the `x_exits` re-read — **now carries `R4-REQ-5`/`D53`: the 240m regime is read off the daily series and 23–27% of `volatility_normal`'s 240m passes are a dataclass default**), then `MGR-T25`, then `MGR-T3`; `MGR-T24` last | — |
| **R4** | — | apply `MISFILED` to `rsi_extreme_reversal` / `stoch_extreme`; `R4-REQ-3`'s two fixes | — |
| **R5** | — | `MAIN-01` is closed; no open task | — |
| **R6** | — | the `CALLOUT.md` propagation it flagged is routed to the parent, not to R6 | — |
| **BT1** | — | `MGR-T14`, then `MGR-T6` (**now extended to the 1m overlap**, ADJ-16c) | — |
| **BT2** | `MGR-T15` (event gate, MGC/MCL) | **`BT2-REQ-3`(a) is ruled: run it with its placebo**; owes `D56` instance 2's bar count | `MGR-T6` for substrate |
| **BT3** | `MGR-T8`, `MGR-T9` (both GATED) | `MGR-T11` | `MGR-T16` |
| **BT4** | `MGR-T20` (`D50` blast radius + rule 2's two numbers) | — | — |
| **BT5** | — | **`MGR-T22` — scope unrecorded; recommended `D51` verification** | parent confirmation |
| **BT6** | `MGR-T21` (verify `D52`) | — | — |
| **discovery** | burst 02 | corrections routed in `msgs/07` | — |
| **DISC2** | `MAIN-02` burst 01 done | its own ledger; `MAIN-02`'s first gate (roll convention) | — |
| **EF1** | harness; **gate FAILED at 33** | **`MGR-T19` — reconcile against EF3** | — |
| **EF2**…**EF7** | cells per §8 | census and population done in 5 of 7; **no profitability number reportable until `MGR-T19`** | `MGR-T19` (`R-13`) |
| **parent** | dispatch | `MGR-T12`, `MGR-T16`, `MGR-T23`, `MGR-T26`, `DEFECTS.md` **D44–D58**, `BRIEF.md` rule 2 + `CALLOUT.md` restatement (ADJ-14 §4), `edge/RESULTS.md` | — |

**Nothing on this board is assigned to two agents**, with one deliberate exception: **`MGR-T19` is
joint by design** — a reconciliation between two harnesses cannot be owned by one of them without the
other's arm being taken on report. EF1 holds it; EF3 supplies its measurement and its dissent.

**No task requires an agent to write a file it does not own.** Where a ruling changes another agent's
verdict (ADJ-9b → R3's P2; ADJ-10a → R3's `R3-Q1`; ADJ-7 → R1's `P9` and R3's `R3-D6`; ADJ-13b →
R4's two `momentum` conditions and R1's group verdict; ADJ-14 → `BRIEF.md` and `CALLOUT.md`) it is
**routed as a message for the owner to apply**, never applied by me.

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
| ~~`MAIN-01`'s sections~~ | ~~R1's `SCOPE.md`~~ | **RESOLVED.** R5 delivered the scope; `MAIN-01` closes `CLOSED-EMPTY / SUBSTRATE-1M`; no section was ever allocated and none ever will be |
| ~~`MGR-T` ids in message headers~~ | ~~`check_refs.py` grammar~~ | **RESOLVED.** `R-12` retired (ADJ-16d) |
| **every EF profitability number, all seven agents** | **`MGR-T19`** — two harnesses measured 43 and 0 `SPANS_WINDOW` violations on the same 400 strategies | **a top-10 list handed to an account owner whose trades may have been held through a window the rule forbids.** Unlike a null read too broadly, this error is **not conservative**, which is why `R-13` is a gate |
| `BRIEF.md` rule 2's narrowing becoming a number rather than a caveat | **`MGR-T20`** — the count of `primary_tf = 1440` rows in the 366/1,151 and the z recomputed without them | rule 2 sits **narrowed-but-unquantified indefinitely**, which is worse than either end. This is ADJ-14's own stated risk |
| two INVALID and four strongly-WEAKENED `scan_reports/` rows | **`MGR-T26`** | `D52` is numbered and its reporting consequence is undischarged — the one obligation ADJ-12 creates and does not close |
| the six existing `VOID` verdicts' reachability | **`MGR-T27`** | `R-14` applies to new verdicts and the six on the record were written to the looser standard, so a `FORWARD` hazard can still be read as a `REACHED` retraction |

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

### Round 2's six pre-registrations, scored. **Two refuted, one confirmed, one refuted-in-mechanism, two open**

A pre-registration that is never scored is a prediction nobody made. Scoring at the first turn where
evidence exists, whether or not it flatters me.

| # | subject | verdict | the diagnosis, which is the part worth keeping |
|---|---|---|---|
| **1** | `MAIN-01` closes `CLOSED-EMPTY` because the defensible bar-size range and the useful range do not overlap | **OUTCOME RIGHT, MECHANISM REFUTED** | R5 measured the substrate and the task dies **one gate earlier**: ~6.5 RTH sessions of 1-minute futures data exist in this repository, total. I predicted an approximation-error death and **nobody has measured the approximation error** — so had I been allowed to record my own reason, the ledger would carry a claim with no measurement behind it. This is `R-11` in a new costume: I reasoned from a mechanism I found plausible instead of from a quantity |
| **2** | ≤8 of the 47 remaining conditions land on PROXY; most findings are DEGRADED or broken | **CONFIRMED, and by a wide margin** | R4's surface returned **PROXY: 0 of 31** — "my surface contains no participant-information group", which is the mechanism I guessed at. The verdicts landed 20 CLEAN / 6 DEGRADED / 5 MISNAMED-or-MISFILED. The prediction was right for the right reason: R1 had already audited the groups whose *names* promise participant information |
| **3** | R3 rules BT3's Q1 `PER_STRATEGY` and the 24× gap is the finding | **CONFIRMED** | ruled `PER_STRATEGY` in `msgs/10_R3_BT3…`. Recorded in §6's algorithm table |
| **4** | `MGR-T13` reframes at least one settled rule without contradicting it | **OPEN** — `MGR-T13` has not run | but the *shape* has been vindicated by another route: `D50` and `D52` each reframe a settled rule without contradicting it (rule 2, and the daily VWAP rows). The mechanism I bet on was the volume norm; the mechanism that delivered was degenerate sampling |
| **5** | at least one Tier-1 item never runs this programme, with a stated reason | **ON TRACK, and the reason has changed** | it is no longer `R-6`'s doubling that will strand one — it is ADJ-16a's finding that rule-set pairing shares a **median 61.8%** of entries, so the honest version of several Tier-1 items needs `MGR-T24`, which I have just ranked low on purpose |
| **6** | **against myself:** Axis C as a tag rather than a class is too weak to survive; confirmed if nobody but me mentions it again | **REFUTED, in the useful direction** | R2 used it **six times** in `research/R2_recut_contingency.md` and produced a membership table sharper than my own ruling: `Axis C` fully contains **one** of its nineteen families (II-10) and partially contains three (II-11, II-13, and the date half of II-1/II-2) — "a more precise statement than `R2-Q1`'s original, and the version I would now defend". The falsifying branch specified `MGR-T7` returning an actionable consolidation; it arrived from a different file, and the substance is what I asked for. **The tag survives** |

**Two of six refuted, and both refutations are the same error in different clothes: I predicted a
mechanism instead of measuring a quantity.** That is `R-11`, which I wrote, applied to myself for the
third and fourth time. The mitigation for round 3 is in the pre-registrations below: every one of them
names the measurement that settles it and who owes it.

### Round 3's pre-registrations

1. **`MGR-T20` restores rule 2's first sentence rather than narrowing it.** I predict the
   `primary_tf = 1440` rows are a small minority of the 366 and 1,151 behind z = −4.09 — because the
   published corpus is overwhelmingly 60m and 240m and the daily cells are its thinnest — and that
   **z survives their exclusion at |z| > 3**. **Falsified by** z falling below 1.96 on exclusion, in
   which case rule 2's first sentence is a 60m/240m result and must say so. *Owed by BT4.*
2. **EF1's validated harness lands with a named carve-out, not a true zero.** The 9–10 dates that
   break it are **genuine exchange early closes and holidays**, identical across all four symbols
   (Black Friday, Christmas Eve, Juneteenth, 3 and 4 July, Memorial Day), on which the last bar before
   the deadline is stamped 12:00–14:00 and the market is shut until 18:00 — **a position open at 12:30
   on Black Friday physically cannot be flattened at 16:00.** Real-world compliance is being flat by
   the early close, which a trader knows in advance from the published calendar. **Falsified by** a
   harness reporting zero violations with **no** carve-out on all four symbols — which is what EF3's
   already does, so this is a live disagreement between two implementations rather than a guess.
   *Settled by `MGR-T19`.*
3. **No scalp row clears `free_t = 1.177`, and the scalp top 10 ships as a labelled description of
   the sample.** The arithmetic is done — 57.90 days, √years 0.398, SR 2.96 needed for a *single*
   pre-registered hypothesis — and no strategy in this repository's history has shown a sustained
   annualised Sharpe near 3. **Falsified by** any scalp row with t > 1.177 **and** a placebo beside it
   **and** its search size stated. *Owed by EF4/EF5.*
4. **Against myself, fourth time: `D53`'s class framing is the thing I get wrong this turn.** A
   six-instance class with a deliberately split harm profile is too clever, and agents will keep citing
   the local notes (`D-R1`, `D-V3`, `D-MTF3`) they already have in their own files rather than a class
   number in a register they do not own. That is exactly how ADJ-1's Axis C was supposed to fail and
   did not — so I am betting the same way and expecting the opposite outcome. **Falsified by** any
   agent citing `D53` without my prompting. **Confirmed** if `D53` appears only in files I write.

---

# 8. The edge-finding programme — seven agents, one account-owner request

**Authority:** the account owner, directly, via `edge/EDGE_BRIEF.md`. **Not a `MAIN-<nn>`, and I am
not decomposing it** — the EF agents have already cut it into cells by (setting × symbol pair ×
timeframe band), the brief assigns the deliverable to the parent, and `PIPELINE.md` §2's prohibition on
decomposing a task I did not scope applies with **more** force here, because the requester is not in
the room to correct a bad cut. Ruled in **ADJ-15**.

**Deliverable:** per symbol (MGC, MCL, MES, MNQ), a top 10 for a **SWING** setting and a separate top
10 for a **SCALP** setting, inside **18:00 ET → 16:00 ET** with nothing held across 16:00–18:00. Final
lists go in `edge/RESULTS.md`, **which the parent owns and writes** — EF agents hand it rows with
controls, search size, span and forward behaviour.

## 8.1 The gate. One task blocks all seven agents

| id | what | why it is a gate |
|---|---|---|
| **`MGR-T19`** | Reconcile EF1's and EF3's harnesses bar-for-bar on the 19 sessions where they disagree | **EF1's own gate failed: 33 `SPANS_WINDOW` violations**, all at `primary_tf = 240m`, all on sessions with no bar at the deadline. EF3 built a second harness, ran both over the same 400 MES strategies, audited both with EF1's own `violations()`, and measured **EF1 43 violations / max hold 71.0h / 19 holds over 22h against EF3 0 / 21.0h / 0**. Two implementations of the defining rule disagree on whether it is enforced |

**`R-13` is the rule this created:** `R-5` applies to a harness exactly as to an algorithm — a number
from an unvalidated session harness is **not weak, it is unknown**. EF4 reached this unprompted and
wrote it into its own findings before any profitability number. **Five of seven agents have populations
built and censuses run and none may report a profitability number yet.** That is the programme working.

## 8.2 Five measured constraints, now board facts rather than findings in seven files

| # | constraint | measured |
|---|---|---|
| **1** | **Swing cannot exceed 22 hours, and the budget shrinks linearly through the cycle.** 22h is reachable **only from an 18:00 ET entry**; from MGC's RTH open (08:20) it is **7h40m**, MCL's (09:00) **7h00m**, from 15:00 one hour. "Swing" is a hold *budget*, not a duration — **a thesis needing three days is declined, never truncated** | EF2, `edge/EF2/FINDINGS.md` F1a |
| **2** | **The rule needs new code and cannot be expressed by the shipped engine.** `exit_at_session_close` fires at the **contract's** RTH close (13:30 MGC, 14:30 MCL) `[engine.py:470-473]` and is gated on `not allow_overnight`, so turning overnight on **removes** the session exit rather than moving it — and `allow_overnight` is `True` at **no call site anywhere** `[engine.py:233, 241, 470 only]`. All ~2.97M prior evaluations were flat by their contract's RTH close | EDGE_BRIEF, repo-verified |
| **3** | **The scalp band spans 57.90 days and needs an annualised Sharpe of 2.96 to clear the single-pre-registered floor.** 5m/15m/30m all **57.90 calendar days = 0.1585 years, √years 0.398** — this **corrects the brief's 57 days and its SR 2.98**. `free_t = 1.177` → **SR 2.96**; a 36-arm pre-registered track (`free_t` 2.677) → **SR 6.73**; a 19,152-arm screen (4.441) → **SR 11.16**; the largest *t* ever found here (3.923) → SR 9.85. **Canonical: 57.90 / 0.398 / 2.96.** Every scalp row carries this bound **on the row**, not once in a preamble | EF6 `bursts/01`, EF4 `FINDINGS.md` |
| **4** | **`rth_only=True` makes the rule inert for *entries*, and the overnight arm is not free.** `rth_only` defaults `True` `[base.py:393]` and is `True` on **184/184 MGC and 167/167 MCL** generated strategies; MGC RTH 08:20–13:30 and MCL 09:00–14:30 sit **wholly inside one cycle**, and swing-admissible RTH bars equal RTH bars exactly (2,477/2,477 MGC, 2,881/2,881 MCL). So the rule buys **+2h30m hold on MGC, +1h30m on MCL, and nothing at all on MES/MNQ** whose RTH close already is 16:00. Overnight entries need `rth_only=False`, which **`D24`** measured as buying 2–4× the sample while **costing** expectancy in every paired test | EF2, `msgs/EF2-01_EF1_…` |
| **5** | **Two substrate holes.** (a) **MCL 60m is structurally thin for ~2 months** inside the 718-day span — 17 ET dates, 2026-01-12 → 2026-03-10, carrying **1–5 bars each** against ~20 normally. (b) **MCL daily does not exist**: `MCL_1440m.jsonl` is one line, so any "per symbol" claim at daily is **three** symbols. EF6 was right to make `for_cell` **raise** on `("MCL", 1440)` rather than guess | EF1 `bursts/03`, EF6 `bursts/01` |

**Two rulings attached to those facts (ADJ-15b):**
- **The `rth_only` arm is a paired arm, never a swap.** `R-6` and `D48`'s discipline apply in full, and
  **every swing row declares which of the two it is** — a longer hold on an RTH entry, or an overnight
  entry bought at `D24`'s price. Binding on all seven, not only on EF2, which already carries it as
  `EF2-H1`.
- **Whoever reports an MCL 60m swing row states the thin window and whether its trades fall inside it.**

## 8.3 One question routed, not answered

**Does the 22-hour cap make the 1440m cell inexpressible?** Daily is the only cell with enough span to
answer anything at width **and** the cell where the session rule is nearly degenerate, because a
22-hour hold is about one daily bar. **Routed to EF6 and to whoever holds the daily arm, to be answered
before anything is built there.** I run no analysis and am not answering it.

## 8.4 What the edge programme inherits, in one place, so nobody re-derives it

`R-1` (`csv/` read-only, no exceptions) · `R-2` (a placebo beside every row; `placebo_shift` leaks per
`D42` and is conservative-only) · `R-3` (search size and deflation threshold, always) · `R-4` (never
`T.ab`) · `R-6` + `D48` (paired re-emission discipline, now including the entry-overlap number) · `R-7`
(substrate labelling — `data/archive/` is this programme's substrate, compared with a **tolerance**
never `==`, and never pooled with a `csv/raw` number inside one statistic) · `R-8` (`entry_price`,
`initial_stop`, `symbol` on every trade dump — this programme will want account sizing, which is
exactly why `R-8` exists) · `R-13` (the harness gate) · `R-14` (VOID coordinates and reachability —
immediately relevant: **19.0% of generated strategies carry a VOID condition**, MGC 11.5%, MCL 13.9%,
MES 22.6%, **MNQ 27.4%**, and `Strategy.evaluate` is a strict AND, so one VOID member is the whole
strategy's zero).

**And the two findings the deliverable is most exposed to.** **`D24`** — the measured price of
`rth_only=False`. And **`D8`** — *selecting was worse than not selecting*: trading last period's top 10
returned **−0.0155R against a −0.0104R null** and **underperformed trading the entire qualifying
universe** (+0.022R against +0.057R), with name overlap across disjoint thirds at or below chance
(Jaccard 0.081). `D8` is **structurally immune to R6's entire audit** — both arms are drawn from the
same population over the same bars, so every dead detector is in both arms or in neither — which makes
it the most robust claim in the corpus and the one this programme's deliverable must answer. The brief
already says the right thing: that is not a reason to refuse the task, it is the reason **every list
carries its forward behaviour and not only its in-sample rank.**
