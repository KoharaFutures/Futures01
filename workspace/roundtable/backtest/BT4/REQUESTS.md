# BT4_REQUESTS — sub-task requests arising from `backtest/BT4`

Shape per `PIPELINE.md` §3. Ids per `REGISTRY.md`: `BT4-REQ-<n>`, my own prefix, allocated by me.
Per standing rule **R-9** I describe each defect and do not name a `D<n>`.

---

## BT4-REQ-1 the `align_bucket` fix is **not** safe-and-additive, and here is why — with the blast radius measured

- **Arose in:** `BT4-ALGO-1`, quantifying `R4-M3`.
- **The ask:** do **not** apply the obvious fix. Decide between two candidates, on the measurements
  below, and pair whichever is chosen with the decision about the 1440m results already on disk.
  `R4-REQ-1` already asks for the fix; this entry is the blast-radius half of it, which it could not
  size.

### Why it is not additive, which is the part I was asked to establish

My dispatch allowed me to propose the fix "if you believe a fix is safe and additive". **I do not.**
Three measured reasons:

**(a) The obvious fix is wrong in a new way.** The natural implementation — take `days = minutes //
1440` and group calendar days in blocks of `days` from a fixed epoch — produces buckets holding
**3.44 daily bars on average**, not five, because five *calendar* days is 3.57 *sessions*. It would
replace one mislabelling with another and the new one would be harder to see:

| candidate | MGC buckets from 2,511 daily bars | mean bars/bucket | histogram |
|---|---|---|---|
| **A** calendar-day blocks of `minutes // 1440` | 730 | **3.44** | `{2: 60, 3: 378, 4: 203, 5: 89}` |
| **B** `7200 →` the ISO week's Monday (one trading week) | **522** | **4.81** | `{1: 1, 4: 95, 5: 426}` |
| today | 2,510 | **1.00** | `{1: 2511}` |

`[measured: PYTHONPATH=. python3, both candidates over csv/raw/{MGC,MNQ,MES}_1d.csv; MNQ and MES
give 540 / 3.44 and 387 / 4.80]`

Candidate **B** is what `scout.py:65` says it wanted ("7200 minutes is five sessions"). Only B should
be considered, and **B is not expressible as "divide by 1440"** — it needs a weekday calendar, which
is a new concept in `align_bucket`.

**(b) Both candidates leave the daily branch byte-identical, which is the one piece of good news.**
`[measured: fixed_bucket(b.ts, 1440) == align_bucket(b.ts, 1440) on 2511/2511, 1859/1859, 1859/1859]`
So nothing at 5m/15m/30m/60m/240m moves, and `EF1`'s dependence on the 18:00 daily bucket
(`edge/EF1/code/session_window.py:77`) is untouched. The blast radius is confined to requests
strictly above 1440, and there is exactly one live one.

**(c) Fixing it does not make the daily MTF row measurable — it makes it thin.** Under candidate B a
published 274-day daily cell (187 daily bars — `scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:270`)
has about **39 weekly bars** above it. `g_multi_timeframe`'s own caveat already recorded the problem
in the arm it built by hand: *"the weekly timeframe is built by resampling 60m bars over 274 days,
which is about 55 weekly bars — too few for a 200-period average."* So a corrected `align_bucket`
turns every short-window 1440m cell from *misconfigured* into *warm-up starved*, which is a different
verdict, not a better number. The full-history daily files (2,511 / 1,859 bars → 522 / 387 weekly)
are the only cells where a corrected weekly member would have enough bars, and those are the
chronology ledgers.

### The blast radius, measured

| what changes | measured |
|---|---|
| call sites of `align_bucket` in the library | **1** — `bars.py:341`, inside `resample` `[repo-verified]` |
| live requests above 1440 anywhere in the repo | **2**, both the same map: `futures_agents/scout.py:66` and `workspace/chrono/ledger.py:28` `[measured: grep -rn "7200" --include=*.py . → 2 live sites; grep for 10080/43200/525600 → 0]` |
| frames affected | `FRAMES[1440]` only. `{tf: [m for m in FRAMES[tf] if m > 1440]}` = `{1440: [7200]}` |
| stored results that would change | **every 1440m row**: 23,309 chrono strategies / 130,070 trades / 295 month-buckets; 94 bigscan rows (20 cell files); 95 focus rows (4 cell files); 3 cells in each of 6 of the 21 studies; 2 `x_robustness` cells; 2 `x_session` cells; 3 cells in each of 5 `rank_persistence` payloads; 4 published cells in the deep-scan report |
| stored results that would **not** change | everything at 5m/15m/30m/60m/240m — i.e. ~98% of every ranking corpus |
| the test that already pins both states | `tests/test_bt4_align_bucket.py` — 16 passing checks on today's behaviour and 4 `xfail(strict=False)` that become `XPASS` the moment the fix lands |

- **Why it cannot wait / why it can:** **it can wait, and it should.** Nothing new is being measured
  on a 1440m frame today, and the two candidate fixes give materially different series. What cannot
  wait is the **labelling**: `R4-M3` is on `BRIEF.md` and `BRIEF.md` rule 2 is not yet amended, so an
  agent reading the brief today still reads "multi-timeframe agreement is not a virtue" as settled at
  z = −4.09 when 68% of that measurement's treatment arm sat on the collapsed frame (ALGO-1 §6).
- **What it blocks:** nothing of mine. It blocks any re-ask of "does alignment help" at the daily
  frame, and it is a prerequisite for the chronology study's daily arm being describable as
  multi-timeframe.
- **My estimate of its size:** the code is small (one branch, plus a weekday calendar). **Choosing
  between A and B is small. Deciding what to do with the 23,309 chrono strategies and the six
  studies is not mine to size.**

---

## BT4-REQ-2 `Condition.warmup_bars` is written by every condition and read by nothing

- **Arose in:** `BT4-ALGO-1`, checking whether a corrected weekly member would be warm-up starved.
- **The ask:** allocate a defect number, and decide whether the field should be enforced or deleted.
  `Condition.warmup_bars: int = 50` `[repo-verified: futures_agents/strategies/base.py:102]` is set
  on every registration via `condition(..., warmup=50)`
  `[repo-verified: futures_agents/strategies/library.py:40,47]` and **never read anywhere in the
  deterministic core** `[measured: grep -rn "warmup" --include=*.py futures_agents/strategies/
  futures_agents/backtest/ futures_agents/features.py → 3 hits, all of them the field's own
  definition and assignment]`. It is also inert by content even if it were read: no call to
  `condition()` passes `warmup=`, so all 79 carry the same 50.
- **Why it cannot wait / why it can:** **it can wait.** Nothing measured is wrong. But this is the
  same shape as `R1-Q1` (the `estimated` flag set and never read), and it matters *now* for a
  specific reason: the only guard that would have caught a 39-bar weekly series feeding a 200-period
  average is the one that does not run. If `BT4-REQ-1` candidate B is ever applied, this field is
  what should have stopped the thin cells from reporting.
- **What it blocks:** nothing. It is context for `BT4-REQ-1`.
- **My estimate of its size:** trivial to delete; small to enforce; the interesting question is
  whether `Condition.evaluate` should return `no()` when the bound timeframe has fewer than
  `warmup_bars` completed bars, which is a behaviour change with its own blast radius.

---

## BT4-REQ-3 `ADJ-14` §5's pre-registered measurement is **delivered, and z survives** — so narrowing (a) costs nothing, and §4's restatement is slightly over-narrow

- **Arose in:** `BT4-ALGO-1` §6. Not a new ask so much as the discharge of an existing one.
- **The two numbers `ADJ-14` §5 asked for**
  (`manager/ADJUDICATIONS.md:1437-1452`, ruled *before* I measured):

  | asked | delivered |
  |---|---|
  | count of `primary_tf = 1440` rows in the **366**-strategy arm | **249 = 68.0%** |
  | …in the **1,151**-strategy arm | **320 = 27.8%** |
  | the same z with those rows excluded | **−3.0531** over 11 cells, vs the published **−4.0931** over 14 (reproduced exactly from the payload's own per-cell z before dropping anything) |

  `ADJ-14`'s own decision rule: *"If z survives exclusion, narrowing (a) costs nothing and rule 2's
  first sentence is restored to its full published scope with a footnote."* **z survives** — same
  sign, 75% of the magnitude, 7 of 11 cells negative, and the three daily cells are not the
  load-bearing ones (MGC's daily cell is *positive* at +1.516, so dropping it alone takes the
  combination to −4.668; leave-one-out shows `MGC/60/180` at −5.188 and `MNQ/15/58` at −5.223 carry
  more than any daily cell does).

- **One reading I had to fix, and it matters for whether the answer is admissible.** "The same z
  recomputed with those rows excluded" could mean re-pooling the surviving rows through a fresh rank
  sum. That would be a **new comparative test** and would hit `D28` directly (|z| inflated ~3.3×).
  The published −4.09 is not a pooled statistic — it is a Stouffer combination over cells — so I
  recomputed **the published combination** on the surviving cells. That is **exact, not approximate**:
  a cell is `(symbol, tf, window, confirm_tfs)`, so every `primary_tf = 1440` row lives inside one of
  the three daily cells and nowhere else, and excluding the rows and excluding the cells are the same
  operation.

- **The ask, which is now smaller than I expected:** `ADJ-14` §4's restatement says *"on the
  **60-minute frames** the corpus built"*. The 11 surviving cells are **8 at 60m, 2 at 15m, 1 at 30m,
  across five symbols** (MCL, MES, MGC, MNQ, NQ) `[measured: code/rule2_leave_1440_out.py → timeframes
  {15: 2, 30: 1, 60: 8}]`. No 5m or 240m cell reached the comparison; all were skipped for a thin arm.
  So §4 understates the surviving evidence by three cells and two timeframes. Suggested qualifier:
  **"on the frames whose members are distinct series"** rather than "the 60-minute frames". This is a
  correction **against** my own direction of travel and I am flagging it in that spirit.

- **Two things to carry with the number, both of which cut against quoting it confidently.** (i) The
  per-cell z is a rank sum over correlated strategy variants within a cell, so **both** −4.09 and
  −3.05 are inflated by an unknown factor (`D28`); the ratio is what my measurement establishes, not
  the levels. (ii) The **sign test across cells is not significant before or after** (p = 0.424 →
  0.549), and it is the one statistic in the payload that does not depend on the within-cell unit.
- **Why it cannot wait:** `ADJ-14` §"What this costs" states the risk explicitly — *"if BT4's count
  never lands, rule 2 sits in a narrowed-but-unquantified state indefinitely, which is a worse place
  than either end."* It has landed.
- **What it blocks:** nothing now. It unblocks `ADJ-14` narrowing (a).
- **My estimate:** done. Reproducible in under a second with
  `backtest/BT4/code/rule2_leave_1440_out.py`. The judgement about the final wording is the manager's
  and the parent's, not mine.
