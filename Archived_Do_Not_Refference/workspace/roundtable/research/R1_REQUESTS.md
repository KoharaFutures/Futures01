# R1 — sub-task requests for the manager's board

PIPELINE §3 shape. Filed as they arose; I kept working on the current task in every case.

---

## R1-REQ-1 Promote BT1's D38 registration guard to a shared primitive

- **Arose in:** round-2 task 1, ruling on `BT1-ALGO-1` (`msgs/03_R1_BT1_re-verify-ALGO-1.md`)
- **The ask:** BT1 solved D38's silent-zeroing problem properly and the solution currently lives
  inside one algorithm's file. `backtest/BT1/code/absorption.py:91-104,239-257` gives every bar of a
  registered frame a key in the lookup map, with value `None` for warm-up, so that **"key present,
  value `None`" (warming up) is distinguishable from "key absent" (wrong bar grid, or nobody called
  `register_frame`)**, and counts the second case in a module-level `MISSES` dict. That is the
  difference between a custom condition that returns zero trades *loudly* and one that returns zero
  trades *silently*, which is exactly what D38 causes
  `[repo-verified: workspace/studies/DEFECTS.md D38]`. Every future custom condition from any of the
  three backtesters needs this. It should be one shared helper that all three import, not three
  reimplementations, because the failure it guards against is invisible when it happens.
- **Why it cannot wait / why it can:** it can wait — BT1's copy works. But the cost of waiting is
  that BT2 and BT3 each write their own version, and the two that get it subtly wrong will report
  zero-trade results that nobody can distinguish from null findings. That is a defect-shaped risk,
  not a convenience one.
- **What it blocks:** nothing today. Silently raises the error rate of every custom condition
  written after today.
- **My estimate of its size:** small. It is an extraction, not a design. Whose file it goes in is a
  manager decision; it is not in any of the three ownership scopes.

---

## R1-REQ-2 Time-of-day volume normalisation as a hypothesis in its own right

- **Arose in:** round-2 task 1, ruling on BT1's Q1 (`msgs/03_R1_BT1_re-verify-ALGO-1.md`)
- **The ask:** add a sub-task to test whether the library's **time-of-day** volume norm
  (`relative_volume`, `futures_agents/indicators/volume.py:266-285` — same clock minute over the
  previous 20 sessions) behaves differently from the **20-bar trailing mean** used by
  `detect_imbalances` (`indicators/structure.py:452-455`), as a *general* question about how this
  repo normalises volume, not as a variant of `BT1-ALGO-1`.
- **Why this is not just an ALGO-1 parameter:** I ruled the 20-bar mean into ALGO-1 because my
  finding is explicitly framed as the inverse of `detect_imbalances`, so ALGO-1 keeps search size 1.
  But BT1's measurement shows the two norms select populations that differ by **5–27×** on identical
  bars `[measured: BT1, backtest/BT1/code/frequency.py]`, and the library **uses both**, in different
  places, with no statement anywhere about which is intended. Intraday futures volume has a strong
  U-shape, so a 2× rolling-mean surge at 03:00 and one at 09:35 are not the same event. Any condition
  in the repo that reads volume against a rolling window may be measuring time-of-day rather than
  participation. That is a cross-cutting question about ~2,975,629 existing evaluations, not a
  parameter choice on one new algorithm.
- **One design constraint, to save a wasted build:** if built, **both axes take the time-of-day norm
  or neither does.** A time-of-day volume norm against a rolling range norm asks about two different
  reference populations in one conjunction and the result is uninterpretable.
- **What it blocks:** nothing. It bears on how `volume`-group and `regime`-group results should be
  read, so it is worth knowing before any of those are published.
- **My estimate of its size:** small to measure the divergence (BT1 has already done most of it),
  medium if it becomes a re-read of existing volume-conditioned results.

---

## R1-REQ-3 `detect_imbalances`' docstring names an input the function does not read

- **Arose in:** round-2 task 2, `research/R1_group_audit.md` (group `imbalance`)
- **The ask:** a D-number, or a ruling that it does not need one. I cannot allocate `D<n>`
  (`REGISTRY.md`).
- **The fact:** `futures_agents/indicators/structure.py:443` documents the function as "*Bars whose
  range and **delta** both far exceed the recent norm*". The body computes
  `avg_vol = sum(b.volume for b in prior) / window` `[:454]` and
  `v_mult = bars[i].volume / avg_vol` `[:459]`. **No delta is read anywhere in the function.** It
  also returns `magnitude = r_mult` `[:461]` — the *range* multiple — so a caller ranking
  "imbalances" by magnitude is ranking by displacement, never by participation.
- **Why it matters beyond a comment:** it is upstream of the three `imbalance` conditions
  (`library.py:1168-1202`), which is a group that was screened across the whole programme, and it is
  the function `BT1-ALGO-1` was built as the inverse of. BT1 inherited the correct reading by reading
  the body; anyone who reads the docstring instead builds the wrong gate.
- **What it blocks:** nothing. It changes how `imbalance`-group results are read.
- **My estimate of its size:** trivial as a defect entry. The fix itself is one docstring line and is
  not mine to make.

---

## R1-REQ-4 `StopKind.VWAP_BAND` collapses to the min-stop floor on 6–34% of bars

- **Arose in:** round-2, answering `R3-Q1` (`msgs/04_R1_R3_re-VWAP-BAND.md`)
- **The ask:** a D-number, or a ruling. Again, not mine to allocate.
- **The fact:** `vwap_bands` computes σ as a **session-to-date** volume-weighted dispersion that
  resets at each 18:00 ET anchor `[repo-verified: futures_agents/indicators/volume.py:70-104,
  _anchor_key :32-42]`, so σ is **exactly 0 on the first bar of every CME trading day** by
  construction (`pv2/vol − mean² = tp² − tp² = 0`) and small for several bars after. `stop_price`
  then sets `dist = abs(entry − band) * stop_mult + pad`
  `[repo-verified: futures_agents/strategies/base.py:296-300]` and clamps to
  `min_stop_ticks * tick_size` `[:315-316]`. Measured at `stop_mult = 1.0`, `pad = 0`, the raw
  distance is **below that floor on 6.0% (MNQ) to 33.7% (MCL) of 1h bars**, where a `1.0 * ATR` stop
  is below it on **0.0%** `[measured: python3 over csv/raw/{MGC,MCL,MNQ,MES}_1h.csv]`. On those bars
  `VWAP_BAND` is not a VWAP stop; it is `FIXED_TICKS` at `min_stop_ticks`, wearing a different name
  in every report that carries it.
- **Why it matters:** `x_exits` reported "no stable best stop width". A stop kind that silently
  becomes a different stop kind on a third of MCL bars is a candidate mechanism for that, and it is
  a *measurement* artifact rather than a market fact. R3 owns the stop vocabulary and has the full
  ruling; the D-number is the manager's.
- **What it blocks:** nothing of mine. R3's `StopKind` vocabulary rows and any published result
  carrying `VWAP_BAND`.
- **My estimate of its size:** small as a defect entry; the re-read of affected results is R3's call.

---

# Rulings received — `msgs/10_manager_R1_requests-and-scope.md`, `msgs/13_manager_all_D48-D49-and-triage.md`

All four requests above are ruled. Recorded here so this file is not read as still open.

| request | ruling | id to cite from now on |
|---|---|---|
| `R1-REQ-1` D38 registration guard | **Granted.** Goes to the **parent**, not a backtester, as `workspace/roundtable/lib/registry_guard.py` — a helper imported by all three backtesters cannot live in one owner's `code/`. Interim: BT2/BT3 import BT1's copy read-only. | **`MGR-T12`** |
| `R1-REQ-2` the two volume norms | **Granted and promoted** above the sub-task I filed it as; ruled a question about the **existing corpus**, touching `BRIEF` rule 6 and the ICT kill-zone finding. My design constraint — both axes take the time-of-day norm or neither does — **adopted verbatim and binding.** Ruled a **prerequisite input to the group audit**, because an auditor who does not know which norm a condition uses cannot classify it. | **`MGR-T13`** |
| `R1-REQ-3` `detect_imbalances` docstring | **No new number — folded in as instance 2 of a class**, so that ten docstring defects do not become ten adjacent numbers and bury the pattern. Split trigger recorded at about six instances. | **`D46`** |
| `R1-REQ-4` `VWAP_BAND` floor collapse | **Allocated**, and ruled the strongest of five defect candidates that turn, because it puts a **measurement artefact behind a result the programme treats as settled** (`x_exits`' "no stable best stop width"). | **`D45`** |

**Also allocated from work in `R1_group_audit.md` that I did not file as a request:** `D49` —
`StopKind.RANGE` is `StopKind.ATR` (D-L1/D-L3, sent as `msgs/05_R1_R3_stopkind-RANGE.md`).
`D45` + `D49` together are escalated to **`MGR-T17`** (R3's), as the first settled negative finding in
this programme with a named, measured, artefactual candidate explanation.

**`R1-Q1` → `D46`. `R1-Q2` → CLOSED**, and it needed no sweep: the zero-trade `openinterest` carriers
are a strict subset of the 82% that never traded, the ~495k discount is already published at
`free_t = 5.15`, and `free_t = sqrt(2·ln n)` is logarithmic — *n* would have to fall to ~2,197 to meet
the largest t ever found (3.923). **My instinct was right and now has the number attached**, and it
also closes the open half of `X-15`.

---

## R1-REQ-5 A shared verdict term for "cannot fire", because `DEGRADED` understates six configurations

- **Arose in:** `MGR-T5` / the wider group audit, `research/R1_group_audit.md` Addendum B
- **The ask:** add one term to `ADJ-8`'s shared audit vocabulary (PROXY / DEGRADED / HONEST-DERIVED /
  HONEST-DERIVED-BUT-BROKEN) for a condition or configuration that **cannot produce a trade**, so that
  R1, R2 and R3 classify these the same way. I used `DEAD` in my own file; the shared vocabulary has no
  equivalent and `DEGRADED` is the nearest, which materially understates it.
- **Why it is not cosmetic.** A DEGRADED condition produces a weak number; a dead one produces **no
  evidence at all**, and the two must not be aggregated in any tally. Six are now on the record and
  **three of the six sit inside a *required* group**, so the affected template cannot be built any other
  way at that timeframe: `openinterest` (`D47`); MULTI_TIMEFRAME at the frame's top timeframe;
  VOLUME_PROFILE at 240m; OPENING_RANGE at 1h (MGC total, MNQ/MES 99.8%); BREAKOUT +
  `volatility_expanding` (10 of 60 generated); and `session_extreme_sweep` under `rth_only=True`
  (314/314 generated strategies). `_spans_sessions`' own docstring records why it matters — "those
  absences were read as market facts for weeks" `[repo-verified: futures_agents/strategies/library.py:856-857]`.
- **What it blocks:** nothing. It makes `MGR-T5`/`T6`/`T7` comparable on the one verdict that is not
  about degree.
- **My estimate of its size:** trivial — one row in `ADJ-8`.

## R1-REQ-6 Declaring an overlap: I audited all 11 remaining groups before `ADJ-8` reached me

- **Arose in:** `MGR-T5`; `ADJ-8` and `msgs/10_manager_R1_requests-and-scope.md` arrived after the work
- **The situation, not an ask for absolution.** My dispatch instructed me to audit **16 groups**.
  `ADJ-8` splits the remainder three ways by code surface and gives me **3 groups / 12 conditions**
  (`structure`, `supplydemand`, `fibonacci` = `MGR-T5`), assigning 7 groups / 31 conditions to R3
  (`MGR-T6`) and `time` to R2 (`MGR-T7`). **I had already audited all 11.** `ADJ-8`'s arithmetic is
  right and my dispatch's was wrong — the genuinely-new remainder is 47 conditions, which my own count
  reproduces exactly.
- **The ask, in two parts.** (i) **Rule on what the overlapping 8 groups are worth**, since two
  independent readings of the same 35 conditions now exist: where they agree the verdict is stronger
  than either alone, and where they disagree one of us has shipped an error. (ii) **Relay one
  instruction to R3 and R2 if you agree with it:** *audit first, then compare.* Reading
  `R1_group_audit.md` before doing `MGR-T6`/`T7` destroys the independence, which is the only thing the
  duplication bought.
- **What I have already done about it.** `R1_group_audit.md` Addendum A declares the overlap in full,
  labels the 8 groups explicitly as a **cross-check and not a claim of ownership**, maps my vocabulary
  onto `ADJ-8`'s, and credits `X-9` for the seven filter⇄group aliases I re-derived and should not have.
- **What it blocks:** nothing of mine. Possibly R3's `MGR-T6` sequencing.
- **My estimate of its size:** small for you; it is a routing decision, not research.
