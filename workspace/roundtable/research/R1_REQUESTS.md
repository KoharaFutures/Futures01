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
