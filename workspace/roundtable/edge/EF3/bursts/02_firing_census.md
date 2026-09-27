# EF3 burst 02 — the firing-rate census for MES/MNQ × 60m/240m

**Before any population was constructed, and before any P&L exists anywhere in my directory.**
No entries, no exits, no expectancy in this burst. Every number is a firing rate or an
availability count.

**Code:** `EF3/code/ef3_census.py`, `EF3/code/ef3_stopcensus.py`.
**Raw output:** `EF3/out/census_MES.json`, `census_MNQ.json`, `stopcensus.json`.
**Substrate:** `data/archive` 60m base, `SymbolFrame(base, [60, 240])`, regime_tf = 60.
MES 11,287 bars, MNQ 11,291 bars, 2024-10-06 → 2026-09-25 ET, 718.9 days.
All 79 `CONDITIONS` evaluated at binding tf=60 **and** tf=240 on every base bar, both symbols.
`CONDITION_ERRORS` empty in all four cells `[measured: errors={} for MES and MNQ]`, so nothing
below is the silent-exception failure mode.

## The six known VOID configurations — checked, every one

| # | configuration | MES 60m | MES 240m | MNQ 60m | MNQ 240m | verdict |
|---|---|---|---|---|---|---|
| 1 | `openinterest` (`oi_price_confirmation`, `oi_expanding`) | 0 fires | 0 fires | 0 fires | 0 fires | **VOID ×4.** `bar.open_interest is None` on 11,287/11,287 and 11,291/11,291 archive bars |
| 2 | all six `profile` conditions | **alive** | **0 fires ×6** | **alive** | **0 fires ×6** | **VOID at 240m only.** `prior_profile is None` on 11,287/11,287 at the 240m binding; present on 11,050 (MES) / 11,054 (MNQ) of 11,287 at 60m |
| 3 | `mtf_aligned`, `mtf_strongly_aligned` | alive | **0 fires ×2** | alive | **0 fires ×2** | **VOID at the frame's top tf.** `agreeing_timeframes(from_tf=240)` returns `voting = 1` on every bar (measured: `ge2` count = 0 of 11,287); at 60m `voting ≥ 2` on 4,021 (MES) / 3,930 (MNQ) bars |
| 4 | `StopKind.RANGE` collapsing to ATR (D49) | **99.699%** | 99.344% | **99.699%** | 99.345% | **collapse confirmed and quantified** — and see the correction below |
| 5 | `StopKind.VWAP_BAND` → `min_stop_ticks` floor (D45) | **15.376%** | 9.227% | **7.471%** | 4.411% | floor binds; D45's "6–34%" holds in 3 of 4 cells and **fails low for MNQ 240m (4.41%)** |
| 6 | `opening_range_*` at 1h (D-L1) | `fade` **0**, `breakout` **15** | `fade` 0, `breakout` 14 | `fade` **0**, `breakout` **14** | `fade` 1, `breakout` 13 | **`opening_range_fade` VOID at 60m on both symbols**; `opening_range_breakout` NEAR-VOID at 0.11–0.13% |

Percentages in rows 4 and 5 are over (bar × direction) pairs, 22,574 (MES) / 22,582 (MNQ) per
timeframe, computed by calling `ExitModel.stop_price` directly at matched `stop_mult = 1.0`.

### Corrections and refinements I owe on rows 4, 5 and 6

**Row 4 — D49 is real but it never reaches a generated strategy.** `StopKind.RANGE` is byte-identical
to `StopKind.ATR` on 99.70% (60m) / 99.34% (240m) of pairs — the residue is exactly the 20
half-session `:30` bars where `snap.opening_range` exists (40 = 20 bars × 2 directions, at both
timeframes, on both symbols). **But `RANGE` is unreachable from every template**: it lives only
behind `expand_exit_models(include_aggressive=True)` and no template or call site sets that
`[measured: exits_for(t) over all 13 TEMPLATES → stop kinds reachable anywhere = {ATR, STRUCTURE,
VWAP_BAND}]`. So D49 removes **zero** strategies from my population. What it does supply is R3's
known-answer calibration test — a RANGE-vs-ATR pair at matched `stop_mult` whose true difference is
zero on 99.3–99.7% of bars — and I use it as the first thing through the harness (burst 03).

**Row 5 — the two D45 quantities are different and move in opposite directions.** Band width exactly
zero: MES 506/11,287 = 4.48% at 60m and 2,283/11,287 = **20.23%** at 240m; MNQ 4.39% and 19.98%.
The `min_stop_ticks` floor actually binding: MES **15.38%** at 60m and 9.23% at 240m; MNQ 7.47% and
4.41%. **The floor binds more often at 60m even though the band is degenerate more often at 240m**,
because a non-degenerate 240m band is wide enough in points to clear the floor. Anyone quoting a
single D45 rate is quoting one of two different measurements. MES's floor binds roughly twice as
often as MNQ's at both timeframes, which is a `min_stop_ticks`/price-scale fact (MES 8 ticks = 2.00
pts on a ~6,000 index; MNQ 16 ticks = 4.00 pts on a ~22,000 index), not a market fact.

**Row 6 — my substrate is less dead than `csv/raw` here, and it is the store's doing.** The archive
holds 20 bars off the `:00` grid, and they are the five early-close half-sessions (burst 01). A
09:30 `:30` bar has `minutes_since_open = 0` against the 09:30 RTH open, so the 30-minute
opening-range window is reachable on 5 sessions of 507. That turns `opening_range_breakout` from
R1's DEAD-in-effect into **NEAR-VOID at 13–15 fires in ~11,290 bars**, all on those 5 dates.
`opening_range_fade` is still strictly **VOID at 60m on both symbols** (0 of 11,287 / 11,291). A
strategy whose entire sample is five holiday half-sessions is not a strategy; I treat NEAR-VOID as
reportable-but-not-rankable and say so beside any row that carries it.

## What else the census turned up in my four cells

- **`STRUCTURE` stops are placeable**: unplaceable on 0.137% (60m) and 0.394% (240m) of pairs, both
  symbols. So the three reachable stop kinds are all genuinely available; the vocabulary size in my
  cell is **3, not 5** — ATR, STRUCTURE, and a VWAP_BAND that is a fixed-tick stop 4.4–15.4% of the
  time. `FIXED_TICKS` and `RANGE` are unreachable.
- **`time_stop_bars` is arithmetically inert in the swing cell.** The smallest value in the whole
  catalogue is 30 **primary** bars `[repo-verified: combinator.py expand_exit_models]`, and
  `primary_bars_held = (i − entry_index)//step + 1` `[repo-verified: engine.py:388-390]`. The 22-hour
  cap gives at most 22 primary bars at 60m and 6 at 240m. **So every exit in this cell is STOP,
  TARGET or the 16:00 flat — the time stop can never fire**, and any variation across the catalogue's
  time-stop values is measuring nothing.
- **MES and MNQ agree on every single verdict above, to the bar count in most rows.** That is not
  corroboration. They are one index complex sharing 0.5–0.8% of rule sets (D14/D41); the agreement
  is the *same instrument* answering twice. The one place they differ materially — the D45 floor rate
  — differs because of `min_stop_ticks` and price scale, i.e. the contract spec, not the tape.
