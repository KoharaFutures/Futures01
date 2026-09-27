# R6 — audit of the four published `scan_reports/` against round 1 and round 2

**Agent:** R6. **Owns:** `research/R6_*` only. **Reads:** everything.
**Started:** 2026-09-27. Appended as work proceeds (`BRIEF.md` rule 1).
**Task:** for each published report, which conclusions are invalidated, weakened or unaffected by
what rounds 1 and 2 established.
**I do not edit `scan_reports/`.** This file is the audit; the parent session applies retractions.
**`csv/` untouched** — every measurement below is a read-only census, no backtest, no expectancy.

Marking per `BRIEF.md` rule 3: `[repo-verified: path:line]`, `[measured: command → result]`,
`[general knowledge]`. Ids per `REGISTRY.md`.

---

## 0. The distinction this audit exists to hold

> There is a difference between **"we measured absence"** and **"the detector never fired"**.
> Both produce a null. Only the first is a result.

The published corpus does not mark the difference. It makes the distinction *once* — in
`2026-09-24_ORB-and-ICT.md`, about the **fill model** ("Resampling cannot detect a bias whose sign
is always favourable. Only auditing the fill model can.") — and then does not apply the same
reasoning to the **signal** model. Rounds 1 and 2 applied it, and found five configurations that
could never have produced a trade (`research/R1_group_audit.md`, "Structurally zero-trade
configurations found").

### Status vocabulary, exactly as dispatched, plus one sub-kind column

| status | meaning |
|---|---|
| `STANDS` | I cannot show the claim is broken. Conservative default. |
| `WEAKENED` | the claim survives but its scope, label or precision must change |
| `INVALID — measured nothing` | the published claim is about an object the measurement could not contain |
| `UNAFFECTED` | no round-1/2 finding touches it at all |

`INVALID — measured nothing` covers three mechanically distinct cases and I mark which, because
conflating them is the same error the reports made:

| sub-kind | mechanism | example |
|---|---|---|
| **ZERO-FIRE** | the detector never fired, so the null is not a result | `oi_expanding` never passes; `profile` at 240m fires 0% |
| **SUBSTITUTED** | the template silently drew a different condition from the required group, so the row is a real result about a different object | OPENING_RANGE on MGC/MES/NQ at 1h |
| **DEGENERATE** | the detector fired, but its arithmetic collapses to something other than its name | `above_vwap` at daily = `close > (H+L+C)/3` |

**A `WEAKENED` verdict is not a retraction.** Where I can only show that a *label* is wrong while
the *number* is real, the number stays and the heading changes. Over-retracting is as bad as
under-retracting.

---

## 1. Evidence base — the round-1/2 findings this audit cites, with paths

Every status below cites one of these by id. I verified the load-bearing ones independently; where
I did, it is marked.

| id | claim | path | I re-verified |
|---|---|---|---|
| **R1-D4 / `orderflow`** | `orderflow` is a bar-shape group; all 3 conditions are algebra on OHLCV; `delta_confirms_bar` is `close > (H+L)/2 and close > open` | `research/R1_flow_auction.md:44-56, 180-186` | — |
| **R1-D4a c.2** | `orderflow` is **required** by REVERSAL, so every REVERSAL strategy carries a proxy; 50.7% of a 284-strategy sample carries one; 20/20 REVERSAL did | `research/R1_flow_auction.md:300-352`; `[repo-verified: futures_agents/strategies/combinator.py:201-211 — required_groups=("meanreversion","orderflow")]` | **yes** |
| **R1-D4 / `openinterest`** | both conditions read a column that is `None` on every bar; `oi_expanding` is a FILTER returning `no()`, so it **vetoes every entry** | `research/R1_flow_auction.md:188-224` | — |
| **R1-D4a c.3** | `openinterest` reachability is per-symbol: MGC's default 6-group set cannot emit it; **MNQ's can** (MOMENTUM + BREAKOUT); MCL/NQ/ES unprofiled → all 13 | `research/R1_flow_auction.md:354-372` | — |
| **D-L1** | `or_minutes = 30` hard-coded; `opening_range_breakout`/`_fade` **DEAD at 1h on MGC (0/5000), MNQ, MES**; alive MCL 1h and all 5m | `research/R1_group_audit.md` Group 6; `[repo-verified: futures_agents/features.py:865]` | **yes** |
| **D-L2** | the template does not fail — it silently draws another `liquidity` condition. An "OPENING_RANGE" strategy on MGC 1h **contains no opening range** | same | — |
| **D-P1** | all six `profile` conditions DEAD at 240m (`prior_profile` None 100%); `profile` is **required** by VOLUME_PROFILE; the two FILTERs **block** rather than abstain | `research/R1_group_audit.md` Group 10 | **yes, and extended to daily** |
| **D-P2** | the value area is a function of which CSV was loaded: `in_value_area` disagrees on 6.0–10.5% of bars 5m-vs-60m; POC differs ~100 ticks on MNQ | same | — |
| **D-MTF1** | both MULTI_TIMEFRAME signals are DEAD at the frame's **top** timeframe (0/4965 MGC, 0/4999 MNQ at tf=240) | `research/R1_group_audit.md` Group 9 | **yes — and see §2, it has zero published blast radius** |
| **D-MTF2** | `mtf_strongly_aligned` is indistinguishable from `mtf_aligned` at the top two bindings | same | **yes, on the published frames** |
| **D-MTF3** | `mtf_not_conflicted` ignores its `tf` argument; it is a **base filter in PULLBACK**; pass rate swings with frame composition | same; `[repo-verified: futures_agents/strategies/library.py:837-841]` | **yes, and the swing is larger than stated** |
| **D-M1** | `macd_directional` ≡ `macd_hist_direction`, identical on 5000/5000 bars, five cells | `research/R1_group_audit.md` Group 8 | — |
| **D-M2** | 2 of 6 `momentum` conditions are mean-reversion conditions whose direction is momentum's negation | same | — |
| **D-T1** | `avoid_lunch` uses a hard-coded equity-index session table; on **MGC** it vetoes the **final 90 minutes of RTH**, not lunch; it is a **base filter in REVERSAL** | `research/R1_group_audit.md` Group 14 | — |
| **D-T2** | `after_opening_range` (base filter in LIQUIDITY) passes 56–61% of the time **outside RTH entirely** | same | — |
| **D-V1** | `volatility_compressed` says "Bollinger width", reads `atr_percentile`; verdicts disagree on 27.5–29.9% of bars; it is BREAKOUT's base filter | `research/R1_group_audit.md` Group 16 | — |
| **D-V2** | BREAKOUT + `volatility_expanding` is `p<=0.30 AND p>=0.70` — empty by arithmetic. 10 of 60 generated BREAKOUT strategies | same | — |
| **D-V3 / D-R1** | `volatility_normal`, `regime_trending`, `regime_ranging`, `regime_matches_direction` all accept `tf` and never read it; they read the frame's `regime_tf` chosen by `_default_regime_tf` | `research/R1_group_audit.md` Groups 11, 16 | — |
| **D-VW1** | `above_vwap` does not test above-VWAP and returns SHORT; MISNAMED | `research/R1_group_audit.md` Group 18 | **yes** |
| **D-VW2 / `D45`** | VWAP bands are zero-width on the first bar of every CME trading day; `VWAP_BAND` silently becomes `FIXED_TICKS` on 6–34% of bars | same; `research/R3_path_operation.md:2178-2182` | **yes, and extended to daily — see R6-D1** |
| **D-F1** | `swing_leg()` spans other confirmed swings on **14.4–17.2%** of bars, so every fib ratio is computed off the wrong base one bar in six | `research/R1_group_audit.md` Group 5 | — |
| **D-F2** | `fib_sr_confluence` passes 56.8–80.2% of bars; the four 0.8-ATR windows cover the whole leg on the median bar | same | — |
| **D-MR1** | `bollinger_extreme` is a strict subset of `bollinger_mean_pull`, 601/601, 686/686, 635/635 | `research/R1_group_audit.md` Group 7 | — |
| **D-R2** | `regime_matches_direction` adds **zero gating** over TREND's `regime_trending` base filter | `research/R1_group_audit.md` Group 11 | — |
| **`D45`** | `StopKind.VWAP_BAND` degenerates to `FIXED_TICKS` on 6–34% of bars | `msgs/13_manager_all_D48-D49-and-triage.md`; `research/R3_path_operation.md:2178-2182` | — |
| **`D49`** | `StopKind.RANGE` is byte-identical to `StopKind.ATR` on MGC/MES/MNQ at 60m; `opening_range` None on 5000/5000 MGC 1h | `msgs/13_manager_all_D48-D49-and-triage.md`; `research/R3_path_operation.md:2184-2200` | — |
| **`MGR-T17`** | `D45` + `D49` give "no stable best stop width — the ordering reverses by timeframe" **two measured artefactual candidate explanations** | `msgs/13_manager_all_D48-D49-and-triage.md` | — |
| **R3-B / geometric exits** | `_manage` receives a `Bar`, never a `FeatureSnapshot`; the snapshot is built *after* management; **nothing under `futures_agents/backtest/` imports `futures_agents/risk/`**; so every exit in the programme was geometric | `research/R3_path_operation.md:701-704, 1700-1706` | **yes** |
| **R3-B-4** | `run_portfolio` does not net positions; it is a batch runner | `research/R3_path_operation.md:626-637` | **yes** |
| **R2-A2/A3** | all three `news` conditions degenerate on every daily series: `post_news_window` identically FALSE (a carrier trades zero times), the other two identically TRUE; `outside_news_blackout` removes **0 of 1,093** MGC 60m bars — the identity filter | `research/R2_relational.md:1455-1530`; `msgs/06_R2_BT2_re-verify-ALGO-1.md:285-303` | — |
| **deflation wording** | "2,975,629 strategies were tested" → "**≥ 2,975,629 candidates were generated, of which an unmeasured subset could not trade**"; quote `free_t = 5.46` with its 495k/5.15 companion | `BRIEF.md:230-244` | — |
| **`D48`** | `dataclasses.replace` inherits the memoised `_id` — a forward hazard, **no published result affected**, every one of nine call sites passes `_id=None` | `BRIEF.md:200-228` | — |

### My own measurements, used below

All are availability/firing censuses on `csv/raw`, on the **exact frames the published scans used**
(`futures_agents/scout.py:58` → `FRAMES`), which is the thing the round-1 censuses did not pin down.

**R6-M1 — the published scans always trade the *lowest* timeframe of their frame.**
`[repo-verified: futures_agents/scout.py FRAMES = {5:[5,15,60], 15:[15,60,240], 30:[30,60,240],
60:[60,240,1440], 240:[240,1440], 1440:[1440,7200]}]` and all three scan harnesses filter
`if s.primary_tf == tf` `[repo-verified: workspace/bigscan/cell.py:88-90;
workspace/studies/toolkit.py:158-161; workspace/chrono/ledger.py:38-41]`.

**R6-M2 — MTF and profile censuses on the published frames.**
`[measured: PYTHONPATH=. python3 — load_csv csv/raw/{MGC,MES}_1h.csv, resample to 240 with
keep_partial=False, build_symbol_frame(ser, FRAMES[tf]), evaluate each condition at tf on every
snapshot]`

| cell | frame | `mtf_not_conflicted` passes | `aligned`≡`strongly` | `prior_profile is None` |
|---|---|---|---|---|
| MGC 60m | `[60,240,1440]` | 3128/5000 = **62.6%** | 4686/5000 = 93.7% | 151 = 3.0% |
| MGC 240m | `[240,1440]` | 1073/1348 = **79.6%** | 1348/1348 = **100.0%** | **1348 = 100.0%** |
| MES 60m | `[60,240,1440]` | 3218/5000 = **64.4%** | 4752/5000 = 95.0% | 172 = 3.4% |
| MES 240m | `[240,1440]` | 1094/1347 = **81.2%** | 1347/1347 = **100.0%** | **1347 = 100.0%** |
| MGC 1440m | `[1440,7200]` | 2489/2511 = **99.1%** | 2511/2511 = **100.0%** | **2511 = 100.0%** |
| MES 1440m | `[1440,7200]` | 1852/1859 = **99.6%** | 1859/1859 = **100.0%** | **1859 = 100.0%** |

All six `profile` conditions fire **0 times** on both daily series
`[measured: same run → poc_reversion 0, value_area_edge 0, value_area_breakout 0, lvn_rejection 0,
away_from_hvn 0, open_outside_value 0, on 2511 MGC and 1859 MES daily snapshots]`.

**R6-D1 (new) — at daily frequency the `vwap` group is a bar-shape group.** This extends `D-VW2` /
`D45` from "one bar per session" to "every bar", because on a 1440m series every bar *is* a session.

`[measured: vwap_bands(bars,"session",(1.0,2.0)) over csv/raw, band-1 half-width against the
contract's tick size]`

| cell | band-1 half-width **< 1 tick** |
|---|---|
| MGC 60m / MES 60m / MCL 60m / MNQ 60m | 7.5% / 8.4% / 8.9% / 7.5% |
| MGC 240m / MES 240m / MCL 240m / MNQ 240m | 20.0% / 20.5% / 21.8% / 19.8% |
| **MGC 1440m** | **2511 / 2511 = 100.0%** |
| **MES 1440m** | **1859 / 1859 = 100.0%** |

Condition census on the published daily frame `[1440,7200]`
`[measured: CONDITIONS[name].fn(frame.snapshot(i), 1440) on every snapshot]`:

| condition | MGC 1440m | MES 1440m |
|---|---|---|
| `above_vwap` (SIGNAL) | 2319 / 2511 = **92.4%** | 1854 / 1859 = **99.7%** |
| `vwap_band_extension` (SIGNAL) | 2506 = **99.8%** | 1859 = **100.0%** |
| `vwap_band1_bounce` (SIGNAL) | **0 = 0.0%** | **0 = 0.0%** |
| `vwap_reclaim` (SIGNAL) | 1691 = 67.3% | 1459 = 78.5% |
| `vwap_proximity` (FILTER) | 2418 = 96.3% | 1790 = 96.3% |
| `above_vwap` direction **==** `candle_close_strength` direction, on co-firings | **1092 / 1092** | **919 / 919** |

So on a daily series `above_vwap`'s test `px > vwap_u1` collapses to `px > vwap ≈ (H+L+C)/3`
`[repo-verified: futures_agents/strategies/library.py:314-324; futures_agents/indicators/volume.py:95-104]`
— which is `2C > H+L`, i.e. `sign(CLV)`, i.e. the same arithmetic as `candle_close_strength` and
`delta_confirms_bar` (R1 finding C-1). `vwap_band1_bounce` needs `vwap_l1 < close < vwap`, a
contradiction when `vwap_l1 == vwap`, and fires **zero times**. The docstring's own account of the
defect it fixed — "As `close != vwap` this fired on 99.99% of bars … and its rule sets averaged a
negative expectancy" `[repo-verified: library.py:296-305]` — describes the daily behaviour exactly:
**the fix is void at 1440m.** `vwap` is **required by VWAP**
`[repo-verified: combinator.py TEMPLATES → VWAP required_groups=('vwap',)]`, so this is inside a
template's required slot.

---

## 2. Findings with **zero published blast radius** — the conservative half of the audit

Over-retracting is as bad as under-retracting, so this section comes before the retractions. Five
round-1/2 findings are real properties of the library that **cannot have reached any row in the four
reports**, and one is narrower than round 2's framing implies. Saying so is part of the job.

> **Navigation note.** This file was appended as the work proceeded, per `BRIEF.md` rule 1, so
> §2.1–§2.2 sit here while **§2.3 (`R6-M3`, the 1h grid) appears after Report B** and **§2.4
> (`R6-M4`, the chronology universe) appears after Report C** — each was written at the moment it
> was measured, immediately before the report table that depends on it. Reading order is: §0, §1, §2,
> Report A, Report B, §2.3, Report C, §2.4, Report D, §5–§9. Nothing was reordered after the fact.

| finding | why it does not reach a published row |
|---|---|
| **D-MTF1** — both MULTI_TIMEFRAME signals DEAD at the frame's top timeframe | **R6-M1.** Every published harness trades the *lowest* timeframe of its frame and filters `s.primary_tf == tf` `[repo-verified: workspace/bigscan/cell.py:88-90; workspace/studies/toolkit.py:158-161; workspace/chrono/ledger.py:38-41]`, and `FRAMES` always places ≥1 timeframe above it `[repo-verified: futures_agents/scout.py:58]`. So **no published strategy ever traded at its frame's top timeframe.** Confirmed by measurement: `mtf_aligned` fires 1153/2511 (MGC) and 976/1859 (MES) at 1440m in `[1440,7200]` — alive, not dead (R6-M2). D-MTF1 is a **forward hazard for a study that builds a single-timeframe frame**, not a retraction. |
| **D-MTF3's timeframe-inertness half** — `mtf_not_conflicted` ignores `tf` | Same reason. With `primary_tf = min(frame)`, `{s for s in snap.tfs}` and `{s : tf ≥ primary_tf}` are the **same set**, so reading every timeframe is identical to reading `from_tf=primary_tf`. **The inertness is invisible in every published cell.** Its *other* half — frame-composition dependence — does bite, and harder than round 1 stated; see §2.1. |
| **`StrategyFilters.require_alignment` calls `snap.alignment()` with no argument** `[repo-verified: futures_agents/strategies/base.py:433-434]` — the **sixth** instance of R1's "accepts a timeframe, reads all of them" pattern, and the one R1 did not find, because it is a `StrategyFilters` field and not a condition. `features.py:725-741` names this exact call as the defect that made `mtf_aligned` blind. | Same reason again: harmless wherever `primary_tf = min(frame)`. **New finding, recorded as a forward hazard, not a retraction.** It matters because `require_alignment ≥ 0.5` on MES 240m is the ranking report's one controlled positive in the index complex, and it is *not* corrupted by this. |
| **`post_news_window`** is identically FALSE on every daily series, so a carrier trades zero times | **The combinator cannot emit a carrier.** `post_news_window` appears in **no** template's `base_filters` or `optional_filters` `[measured: python3 over combinator.TEMPLATES → post_news_window in templates: []]`, confirming `research/R1_group_audit.md:78`. It is reachable only by hand, and the only study that reached it by hand is `research/confluence/reversion_specialist.md` F11 — not a `scan_reports/` result. **So the daily-degeneracy finding invalidates nothing published.** It invalidates F11's null, which is R2's finding and already recorded. |
| **`D48`** — `dataclasses.replace` inherits the memoised `_id` | `BRIEF.md:200-228`: all nine `replace` call sites pass `_id=None`. **No published result is affected and no retraction is owed.** I re-read the list and did not re-verify the nine sites; I am citing the parent's verification. |

### 2.1 — but one half of D-MTF3 bites harder than round 1 stated, and it bites *across* the published timeframe tables

R1 measured `mtf_not_conflicted`'s pass rate swinging 25 points between `[60,240]` and
`[5,15,60,240]`. On the frames the reports actually used, the swing is **37 points**, and it is
monotone in the cell's timeframe (R6-M2):

```
MGC   60m  frame [60,240,1440]   passes 62.6%
MGC  240m  frame [240,1440]      passes 79.6%
MGC 1440m  frame [1440,7200]     passes 99.1%
```

`mtf_not_conflicted` is PULLBACK's **base filter** — unconditional
`[repo-verified: combinator.py TEMPLATES → PULLBACK base_filters=('volatility_normal','volume_not_thin','mtf_not_conflicted')]`.
So **every PULLBACK row in every published per-timeframe table carries a veto that loosens from
37% of bars to 1% of bars as the cell's timeframe rises** — a confound produced by the frame the
runner built, not by the strategy, and recorded in no report. This is the honest form of D-MTF3's
consequence for published work.

### 2.2 — a correction to R1-D4a consequence 3 that *widens* the `openinterest` blast radius

R1-D4a c.3 concludes MGC is immune to `openinterest` because its default group set is 6 groups with
no MOMENTUM or BREAKOUT `[measured: profiles.groups_for('MGC') → ('TREND','SUPPLY_DEMAND',
'FIBONACCI','MULTI_TIMEFRAME','MEAN_REVERSION','VOLUME_PROFILE')]`. That is right about a *default*
sweep and **wrong about all three published sweeps**, which pass `groups=` explicitly and therefore
bypass `profiles.groups_for` entirely:

```
workspace/bigscan/cell.py:89        groups=[t.group for t in TEMPLATES]      <- all 13
workspace/studies/toolkit.py:159    groups=list(groups) if groups else ALL_GROUPS
workspace/chrono/ledger.py:40       groups=[t.group for t in TEMPLATES]      <- all 13
```

`openinterest` is an optional group in MOMENTUM and BREAKOUT and `oi_expanding` an optional filter
in both `[measured: python3 over TEMPLATES → oi in optional_groups: ['MOMENTUM','BREAKOUT'];
oi_expanding in filters: [('MOMENTUM','oi_expanding'),('BREAKOUT','oi_expanding')]]`. So
**guaranteed-zero-trade `openinterest` carriers were generated on MGC, MES, NQ, MNQ and MCL alike**
in the deep scan, the 22-study programme and the chronology run. They cannot appear as a *row*
(zero trades, below the floor), so no reported number is wrong — but they are in the **screened
denominator**, which is exactly the deflation-wording problem, and they are in it on every symbol,
not only MNQ's.

---

# Report A — `scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md`

3 symbols × 6 timeframes × 4 windows, 554,441 screened, 2,452 at ≥20 trades.
Harness: `workspace/bigscan/cell.py`, frames from `futures_agents/scout.py:58`, `primary_tf == tf`.

| # | claim (as published) | status | finding that changes it | honest restatement |
|---|---|---|---|---|
| **A1** | "Nothing in this scan is statistically tradeable. 0 of 2,452 clear the threshold, and 0 clear even the most generous denominator defensible." | **STANDS** | nothing in rounds 1–2 touches the verdict. Every dead-detector finding removes candidates from the *numerator* of "things that could have cleared", which can only make a null verdict safer. | unchanged |
| **A2** | "MES is materially better than MGC on this data. MES TREND is profitable in 96.4% of its 137 strategies; MGC has no group with positive median expectancy." | **WEAKENED** (already retracted) | retracted by `2026-09-24_strategy-studies…md` as a trade-floor artefact (inverts at n≥40, z=−1.93; n≥60, z=−4.78). Rounds 1–2 add nothing that rescues or further breaks it. Cross-symbol comparison was already impossible for two reasons: `D14`/`D41` RNG seeding, and now also **§2.2** — the two symbols' populations differ in composition, not only in sampling. | already retracted; do not re-cite. The MGC half ("no group positive on median") survives on its own — see A12 |
| **A3** | "MES 1h TREND is the single most durable result — positive across all three window lengths." | **WEAKENED** (already retracted) | same retraction; and the report's own nesting correction already says the three windows are one observation. `structure` and `trend`, TREND's two required groups, are both **CLEAN** (`research/R1_group_audit.md` Groups 12, 15), so the retraction is a *measured* negative, not a dead detector. | already retracted. Worth noting the retraction is itself sound — see §6 survivors |
| **A4** | "Sub-hourly timeframes are structurally unprofitable for all three symbols. At 5 minutes, 11–16% of strategies make money." | **STANDS** | rounds 1–2 mostly *spare* 5m: `opening_range_*` are alive at 5m on all four symbols (`D-L1`), `prior_profile` is available at 5m, VWAP bands are sub-tick on 1 bar per session out of ~276, and the 5m frame `[5,15,60]` gives 3 voting timeframes. The degeneracies concentrate at 240m and 1440m, i.e. the *opposite* end. | unchanged. The dead-detector findings do not explain the sub-hourly graveyard |
| **A5** | "correlation(win rate, expectancy) = +0.745 … The +0.037 figure should not be cited." | **UNAFFECTED** | no round-1/2 finding touches a cross-sectional correlation over realised trade series. `D6` (floor selects on exit geometry) was already published as limitation 0b. | unchanged |
| **A6** | Method: "Clones collapsed on realised trades before counting. 1,112 of the qualifying strategies were duplicates." | **STANDS, and it absorbed a defect the report did not know about** | `D-M1`: `macd_directional` and `macd_hist_direction` return identical `(triggered, direction)` on 5000/5000 bars in five cells. Two strategies differing only in which MACD condition they carry therefore produce an **identical trade list** and were collapsed. Same for `D-MR1`'s nested Bollinger pair wherever the subset case bound, and `D-R2`'s zero-gating `regime_matches_direction`. | unchanged, and credit is owed: collapsing on realised trades neutralised the duplicate-condition defects at row level. It did **not** neutralise them in the screened count (A7) or in any condition-level attribution |
| **A7** | "Deflation charged against the full screened population … 13,000–19,700 screened per cell, **4.36 t-units**." | **WEAKENED (wording)** | `BRIEF.md:230-244`: candidates were **generated**, of which an unmeasured subset could not trade. There are now **five** known causes of a structurally zero-trade candidate (`research/R1_group_audit.md`, "Structurally zero-trade configurations found") plus `D-V2`'s empty BREAKOUT conjunction at 10 of 60, plus §2.2 putting `openinterest` carriers in the denominator on **every** symbol, not just MNQ. | "**≥ 13,000–19,700 candidates were *generated* per cell, of which an unmeasured subset could not trade.**" The threshold barely moves — `free_t = sqrt(2·ln n)` is logarithmic; removing 91% of *n* moves 5.46 to 5.00 — so **the verdict does not change, the sentence does** |
| **A8** | "Look-ahead discipline. Higher timeframes are visible only when closed. The 4-hour series is resampled from hourly with `keep_partial=False`." | **STANDS** | `[repo-verified: workspace/bigscan/cell.py DERIVED = {240: ("1h", 60)}]`; R1's audit of all 19 groups introduced **no** new look-ahead and found the three in-repo look-ahead bugs already fixed (`research/R1_group_audit.md`, anti-overfitting table). | unchanged |
| **A9** | Results table, the **4h row** for all three symbols (MES −0.052/23%, MGC +0.023/61%, NQ −0.020/39%). | **WEAKENED** | at 240m the population is materially different from its 60m sibling, for four independently measured reasons: `D-P1`/`D5` — all six `profile` conditions fire 0%, so VOLUME_PROFILE is structurally zero-trade (**R6-M2: `prior_profile` None on 1348/1348 MGC and 1347/1347 MES**); `D-VW2`/`D45` — **R6-D1: 20.0–21.8% of 240m bars have sub-tick VWAP bands**, on which `above_vwap` and `vwap_band_extension` fire unconditionally and `vwap_band1_bounce` cannot fire; `D22` — 240m REVERSAL is an exactly empty intersection; `D24` — `rth_only=True` shrinks every 4h population 2–12×. And **R6-M2: `mtf_strongly_aligned` ≡ `mtf_aligned` on 100% of 240m bars** in frame `[240,1440]`. | the 4h census is over a population that is missing one whole template, holds a degenerate VWAP required slot on a fifth of its bars, and offers one distinct MTF signal where the table implies two. **Not comparable to the 60m census as a like-for-like timeframe contrast** |
| **A10** | "MGC at 30m and 15m is the worst cell in the scan: fewer than one strategy in ten makes money." | **STANDS** | `D39`'s resolvability table gives MGC "none" at 15m and 30m as well as 60m, so MGC's OPENING_RANGE strategies contain no opening range at those timeframes either (`D-L2`) — but that relabels a minority of a cell-wide census, it does not reverse a 9%-profitable figure. | unchanged; add "MGC's OPENING_RANGE rows at 15m/30m/60m contain no opening range" as a label caveat |
| **A11** | Best-group table: "**NQ · OPENING_RANGE · 18 strategies · median exp +0.070 · 66.7% profitable**" — NQ's second-best group. | **INVALID — measured nothing** (sub-kind **SUBSTITUTED**) | `D-L1`/`D-L2` + `D30`: `or_minutes = 30` is hard-coded `[repo-verified: futures_agents/features.py:865]`; 09:30 = 570 is not divisible by 60, so no 1h bar satisfies `0 <= minutes_since_open < 30` and `opening_range_breakout` fires on **4 of 4,256** NQ 60m bars. `liquidity` is OPENING_RANGE's required group with 7 members, so the template **silently draws one of the other five** and does not fail. | "**NQ's second-best group at 1h is a prior-day / overnight / session-sweep / initial-balance group filed under the opening range's name.**" The 18 rows and their numbers stand as a `liquidity`-group result; the heading names an object the cell could not contain. The study programme said this for the *cross-window* row (A18) and **not for this table**, so the retraction is owed here |
| **A12** | "**MGC's best group loses money on median. Every one of its groups does.**" (MULTI_TIMEFRAME −0.040, LIQUIDITY −0.053, TREND −0.056) | **STANDS**, with two label caveats | TREND's required groups are both CLEAN. MULTI_TIMEFRAME at 60m in `[60,240,1440]` is alive (R6-M2) but `strongly` ≡ `aligned` on 93.7% of bars (`D-MTF2`). LIQUIDITY carries `after_opening_range` as a base filter, which `D-T2` shows passes 56–61% of the time **outside RTH entirely**, and 2 of its 7 required-group conditions are DEAD at 1h (`D-L1`). | verdict unchanged. "MGC LIQUIDITY" should read "MGC prior-day / overnight / initial-balance, gated by a filter that admits most of Globex" |
| **A13** | Table 1: "MGC 1h VOLUME_PROFILE n=28 win 71.4% (53–85) exp +0.295 t=1.53" | **WEAKENED** | `D-P2`: `in_value_area` — the gate of `poc_reversion`, the inverse gate of `value_area_breakout`, the whole of `open_outside_value` — **disagrees on 4.1–7.4% of MGC bars depending on which CSV built the profile**, and the median \|POC(5m) − POC(60m)\| is ~28 ticks on MGC. Plus the study programme's own "one condition wearing six names". At 60m the profile does exist (`prior_profile` None on only 3.0% of bars, R6-M2), so this is not a ZERO-FIRE case. | the row stands as measured; its **direction** is determined by the runner's timeframe choice rather than by the session's auction on ~1 bar in 20, and the group is effectively one condition |
| **A14** | Table 1: "MGC 1h VWAP n=21 win 71.4% exp +0.019 R:R 0.43" | **WEAKENED** | `D-VW1`: `above_vwap` neither tests above-VWAP nor is named for what it returns — it is a band test that returns SHORT below the lower band; MISNAMED. `D-VW2` + **R6-D1: 7.5% of MGC 60m bars have sub-tick band-1 half-width**, on which `above_vwap` fires unconditionally, `vwap_band_extension` becomes the CLV predicate with the *opposite* sign convention, and `vwap_band1_bounce` cannot fire. | the row stands as measured; "VWAP" at 60m is a σ-band-location group, degenerate on ~1 bar in 13 |
| **A15** | Table 2 and the per-timeframe table: **four separate 4h VWAP rows** (MES 4h 9mo R:R 3.10 exp +0.479; MES 4h 3mo 2.83 +0.050; "4h 6mo MES VWAP 60% n=52"; "4h 6mo MES VWAP 2.5:1") | **WEAKENED, strongly** | same mechanism, five times worse: **R6-D1 — 20.5% of MES 240m bars have sub-tick band-1 half-width**. On one 4h bar in five the required `vwap` slot is: `above_vwap` fires on every bar with a direction; `vwap_band_extension` reduces to `close ≥ (H+L+C)/3` and takes **SHORT** on a strong close; `vwap_band1_bounce` is arithmetically impossible. `vwap` is **required by VWAP** `[repo-verified: combinator.py TEMPLATES]`. | these rows are the most degenerate `vwap` results in the report. Restate as "a σ-band group whose band has no width on 20% of its bars", and treat the 4h VWAP R:R rows as unreliable rather than as a 4h finding |
| **A16** | Per-timeframe table, **daily VWAP rows**: "1d 9mo — best R:R **MGC VWAP 2.1:1** w=33% e=+0.00" and "1d 6mo — best win rate **MES VWAP 52% n=33 e=+0.04**" | **INVALID — measured nothing** (sub-kind **DEGENERATE**) | **R6-D1**, extending `D-VW2`/`D45` from one bar per session to every bar: band-1 half-width < 1 tick on **2511/2511 MGC** and **1859/1859 MES** daily bars. `above_vwap` fires on 92.4% / 99.7%; `vwap_band_extension` on 99.8% / 100.0%; `vwap_band1_bounce` on **0/2511 and 0/1859**; and `above_vwap`'s direction equals `candle_close_strength`'s on **1092/1092** and **919/919** co-firings. | "**A daily VWAP row is a close-location result.** At 1440m the session-anchored band has no width, so `above_vwap` degenerates to exactly the `close != vwap` condition its own docstring records as removed for firing on 99.99% of bars, and the group's only band-reversion signal cannot fire at all." These two rows are not about volume-weighted value |
| **A17** | Table 1 rows and the group table: "MES 1d MULTI_TIMEFRAME 74.1% n=27 e=+0.034"; "MES 1d MULTI_TIMEFRAME 73.3% n=30 e=+0.007"; "MES MULTI_TIMEFRAME 65 strategies +0.007" | **WEAKENED** | **R6-M2: at 1440m in frame `[1440,7200]`, `mtf_strongly_aligned` and `mtf_aligned` are identical on 2511/2511 and 1859/1859 bars** (`D-MTF2`, and `D17` already said it for a two-timeframe frame). So the group offers **one** distinct signal, not two, and any "graded vs binary alignment" reading of a daily MTF row is arithmetic. `mtf_not_conflicted` passes 99.1–99.6% at daily. **Not** dead — `D-MTF1` does not reach this cell (§2) | the rows stand; "MULTI_TIMEFRAME at daily" is a two-timeframe agreement test with one signal condition, and the report's reading of row 3 ("right three times in four and makes almost nothing") is unaffected |
| **A18** | Cross-window stability: "**NQ 1h OPENING_RANGE** 274d +0.07 / 180d +0.09 / 90d +0.26" as one of four combinations that "stay positive as the window is extended" | **INVALID — measured nothing** (sub-kind **SUBSTITUTED**) | already retracted by `2026-09-24_strategy-studies…md` ("One observation, three times … of 47 floored OR strategies, **one** is an OR breakout"). Rounds 1–2 supply the mechanism (`D-L1`, `features.py:865`) and extend it: **MGC 1h is 0/5000, total** — not merely rare — and MES/MNQ 1h signals come from **two holiday half-sessions** (2025-11-28, 2025-12-24), with R3 arguing from the `:00` grid that the correct figure is 0/5000 rather than 2/5000 `[research/R3_path_operation.md:2202-2213]`. | already retracted; the retraction should cite `features.py:865` and be stated **per symbol**, because MCL 1h is the one cell where the condition is alive |
| **A19** | Cross-window stability: "NQ 1h VOLUME_PROFILE 274d +0.04 / 180d +0.09 / 90d +0.07" and "NQ 1h VWAP +0.02 / +0.07 / +0.04" | **WEAKENED** | `D-P2` (value area depends on which CSV built it; **MNQ/NQ is the worst affected symbol — 10.5% disagreement 5m-vs-60m and ~100 ticks of POC difference**) and `D-VW1`/`D-VW2` (+ R6-D1: 7.5% of MNQ 60m bars sub-tick). The report's own nesting correction already removed the replication reading. | both stand as measured; neither is replication, and the VOLUME_PROFILE one is the most CSV-dependent of the four |
| **A20** | Limitation 0c: "**VOLUME_PROFILE cannot produce a strategy at 4h or daily at all.** … Every 'VOLUME_PROFILE absent at 4h/1d' reading in this report is an implementation gate, not a market fact." | **STANDS — and this is the report doing the audit's own job** | independently reproduced: `D-P1`, and **R6-M2 — `prior_profile` None on 1348/1348 MGC 240m, 1347/1347 MES 240m, 2511/2511 MGC 1440m, 1859/1859 MES 1440m, with all six conditions firing 0 times on both daily series**. R1 adds one thing the limitation does not say: the two FILTERs return `no()`, and **a FILTER returning `no()` vetoes the entry** `[repo-verified: futures_agents/strategies/library.py:1032-1033, 1050-1051]`, so at 4h/daily they do not abstain, they block. | unchanged, and it should be quoted as the model for every other absence in the corpus. Add: "and the two profile FILTERs block rather than abstain when the profile is missing" |
| **A21** | Limitation 0b: "The 20-trade floor selects on exit geometry, not signal quality … library-wide, not specific to any group." | **STANDS, and is now harder to correct for** | `D45` + `D49` + `MGR-T17`: two of the five nominal `StopKind`s do not realise their own mechanism — `RANGE` is byte-identical to `ATR` on MGC/MES/MNQ at 60m, and `VWAP_BAND` falls to a fixed-tick floor on 6–34% of bars. So "stratify by stop width before ranking", the report's own fix, cannot be done cleanly: two of the widths are not the widths they are labelled. | unchanged, plus: "and the stop-kind labels themselves are unreliable — see `D45`, `D49`" |
| **A22** | Limitation 5: "No walk-forward or period replication was run here. This is a screen." | **STANDS** | executed by the 22-study programme and by the ranking study; both negative. Nothing in rounds 1–2 touches it. | unchanged |
| **A23** | Recommendation: "Take **MES 1h TREND** through disjoint-period replication and anchored walk-forward." | **STANDS as advice, executed, and the result was negative** | superseded by `2026-09-24_strategy-studies…md`, not by rounds 1–2. `trend` and `structure` are both CLEAN, so the negative is a measured negative. | mark as executed and resolved negative |
| **A24** | "Leave MGC alone on this evidence … because **554,441 tested strategies** found no way to." | **WEAKENED (wording)** | the deflation wording (`BRIEF.md:230-244`) plus **§2.2**: the deep scan forced all 13 groups on every symbol, so MGC's screened population contained `openinterest` carriers that could never trade and BREAKOUT + `volatility_expanding` carriers that are empty by arithmetic (`D-V2`). | "**554,441 candidates were generated on MGC, MES and NQ, of which an unmeasured subset could not trade, and none of the rest found a way.**" The advice is unchanged |

**Report A counts:** STANDS 10 (A1, A4, A6, A8, A10, A12, A20, A21, A22, A23) ·
WEAKENED 10 (A2, A3, A7, A9, A13, A14, A15, A17, A19, A24) ·
INVALID 3 (A11, A16, A18) · UNAFFECTED 1 (A5) · **total 24**.
Of the 3 invalidations, 2 are SUBSTITUTED and 1 is DEGENERATE; **none is ZERO-FIRE**, because a
zero-firing detector cannot produce a row that clears a 20-trade floor — it can only distort the
screened denominator (A7, A24).

---

# Report B — `scan_reports/2026-09-24_strategy-studies_21-study-programme.md`

22 studies, 912 comparisons, Bonferroni |z| ≥ 4.03, 56 surviving claims.
Harness: `workspace/studies/toolkit.py`, frames from `scout.FRAMES`, `primary_tf == tf`.

## B.1 — the bottom line and the retractions

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **B1** | "Nothing in this library is tradeable, and the reason is not that we searched badly." | **STANDS** | nothing in rounds 1–2 produces a tradeable result; every dead-detector finding shrinks what was actually searched, which cannot create an edge. | unchanged |
| **B2** | "Cut into genuinely disjoint periods, 72 strategies are positive in all three against a permutation null of 70.1 — exactly chance. Excluding one cell it is 44 against 60.2, *below* chance." | **STANDS** | untouched. Both arms of a permutation null contain the same dead detectors. | unchanged |
| **B3** | "Best t-statistic anywhere in the programme: **3.92** against a free-search threshold of **4.15**." | **WEAKENED (wording only)** | `BRIEF.md:230-244` — the denominator counts generated candidates, an unmeasured subset of which could not trade; quote the 495k / `free_t = 5.15` companion alongside. | "**3.92 against a threshold of 4.15 charged on generated candidates**; discounting non-traders across the programme gives ~495k and 5.15, still uncleared." Verdict unchanged |
| **B4** | The three-row retraction table (MES 1h TREND; NQ 1h OPENING_RANGE; anchor/execution split) | **STANDS, and rounds 1–2 supply the mechanism for row 2** | `D-L1`/`D-L2` + `features.py:865`. The row already says `opening_range_breakout` fires on 4 of 4,256 bars — which is the ZERO-FIRE reading, stated correctly. Rounds 1–2 extend it: **MGC 1h is 0/5000**, and MES/MNQ 1h fire only on two holiday half-sessions. | keep; add the per-symbol table and `features.py:865`, and say explicitly that MCL 1h is the one cell where the condition is alive |

## B.2 — the six survivors "worth acting on"

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **B5** | Survivor 1: "Turn `exit_at_session_close` off — the largest single effect measured. Paired sign z = **+3.52** … median hold at 240m and daily is **0.0 minutes**. The 'anchored targets beat R-multiple' result is this flag wearing another name." | **STANDS, and it is one of the few survivors that is *about* the layer the programme actually varied** | `research/R3_path_operation.md:1700-1706`: twelve `ExitModel` fields are price levels, a clock and a session boundary; **`_manage` receives a `Bar`, never a `FeatureSnapshot`** `[repo-verified: futures_agents/backtest/engine.py:377-378, and the snapshot is built at :311 — *after* step 2's management loop]`, and **nothing under `futures_agents/backtest/` imports `futures_agents/risk/`** `[measured: grep -rn "from ..risk\|from futures_agents.risk\|import risk" futures_agents/backtest/ → no matches]`. `exit_at_session_close` is a clock boundary, so it is inside the experiment. | unchanged. Worth adding the scope sentence: this is an effect **on geometric exits**, which is the only exit kind the programme ever ran |
| **B6** | Survivor 2: "One exit model, stable at every floor … `ATRx1 → 2/4R anchored to 1/2.5 ATR` … **No stable best stop width exists — the ordering reverses by timeframe.**" | **WEAKENED — and this is the most consequential single weakening in Report B** | `MGR-T17` (`msgs/13_manager_all_D48-D49-and-triage.md`): `D45` and `D49` give that verdict **two independent measured artefactual candidate explanations**. `D49` — `StopKind.RANGE` falls through to `dist = stop_mult * atr`, **byte-identical** to the ATR branch and neither adds `pad` `[repo-verified: futures_agents/strategies/base.py:284-288 vs :301-309]`, and `opening_range` is None on 5000/5000 MGC 1h bars. `D45` — `VWAP_BAND` falls to the `min_stop_ticks` floor on 6–34% of bars, and **R6-D1** shows that rate is 7.5–8.9% at 60m, 19.8–21.8% at 240m and **100% at 1440m**. Both rates vary by symbol **and** by timeframe, which is exactly the pattern "the ordering reverses by timeframe" describes. The manager's own words: "the first time in this programme that a settled negative finding has a named, measured, artefactual candidate explanation." | "**No stable best stop width was found, and two of the five stop kinds do not realise their own mechanism at rates that vary by symbol and timeframe — so the instability is not yet established as a market fact.**" The rest of survivor 2 (one exit model best in 7 of 10 entry groups; three targets worse than two) is untouched |
| **B7** | Survivor 3: "Use the anchor/execution split **ONLY at a 4-hour anchor** with anchored targets (z = +3.20, 328 pairs; z = +4.07, 3 of 3 cells)." | **WEAKENED** | the 240m anchor cell is where the detector layer is most depleted: `D-P1` + **R6-M2** (`prior_profile` None on 1348/1348 and 1347/1347 240m bars, all six `profile` conditions fire 0%, VOLUME_PROFILE structurally zero-trade), `D22` (240m REVERSAL an exactly empty intersection), `D24` (`rth_only=True` costs every group 2–12× at 240m), `D-VW2`/`D45` + **R6-D1** (20.0–21.8% sub-tick VWAP bands), **R6-M2** (`mtf_strongly_aligned` ≡ `mtf_aligned` on 100% of 240m bars). | "it pays at a 240m anchor" is a claim about a cell missing one whole template, holding a degenerate VWAP required slot on a fifth of its bars and an MTF group with one distinct signal. **State the 240m population's composition before re-citing this.** The self-cancelling mechanism (payoff +9.59, win rate −6.79) is unaffected |
| **B8** | Survivor 4: "Do not open intraday positions **15:00–16:00 ET**. z = −4.43, median −0.617R, **replicated across symbols**." | **WEAKENED (per-symbol scope)** | `D-T1`'s mechanism, not its conclusion: a fixed ET clock window is a **different object on each contract**, because RTH differs — MGC 08:20–13:30, MCL 09:00–14:30, MNQ/MES 09:30–16:00 `[repo-verified: futures_agents/config.py:157,179 via get_contract]`. On MGC and MCL, 15:00–16:00 ET is **after the pit close**, i.e. a Globex window, not "the last hour of the cash session". The condition `power_hour` that targets that window is **CLEAN** (R1 Group 14 — it is the one that was fixed to use `_rth_minutes`), so the measurement itself is sound. | "**Do not open intraday positions 15:00–16:00 ET**" stands as a clock rule. It is **not** "avoid the close" on MGC or MCL, and "replicated across symbols" should say which symbols were in RTH at the time. The index-complex replications are also not independent (`D14`/`D41`) |
| **B9** | Survivor 5: "Do not fade extension on the bar spanning the cash open, at 60m. z = −10.64 … **It reverses at 15m, so it is a property of the hourly bar.**" | **STANDS, and rounds 1–2 name a candidate mechanism for the last clause** | `D-L1` / `D30` / `features.py:865`: the 60m grid is 4,992 bars at `:00` and 8 at `:30` `[measured by R1: Counter(to_et(b.ts).minute) over csv/raw/{MGC,MNQ,MCL}_1h.csv → {0: 4992, 30: 8}]`, and no contract's RTH open is on the hour except MCL's. So at 60m "the bar spanning the cash open" is a bar that *contains* the open in its interior; at 15m it can be a bar that *starts* on it (MES/MNQ/NQ 09:30, MCL 09:00). That is the same clock arithmetic as `D39`'s resolvability rule and it is a plausible reason the sign reverses. | verdict unchanged. Add: "the 60m/15m reversal is consistent with the open falling in a bar's interior at 60m and on a bar boundary at 15m — see `D39`". Also note NQ/MNQ/MES are one complex, so 3 of the 4 replications corroborate weakly (`D14`/`D41`, already published) |
| **B10** | Survivor 6: "`volatility_normal` earns its place — **but is symbol-specific**. Paired within 2,571 rule sets, sign z = **+9.64** … but it **detectably hurts MGC 60m** (z = −6.30). Not a universal rule." | **WEAKENED** | `D-V3` + `D-R1`: `volatility_normal` reads `snap.regime.volatility` `[repo-verified: futures_agents/strategies/library.py:719]`, which comes from `classify_regime` on the **frame's** `regime_tf`, selected by `_default_regime_tf` from `(15, 30, 5, 60, 10, 3, 1)` `[repo-verified: futures_agents/features.py:819-825, 928-943]` — **not** the strategy's timeframe, and the condition's `tf` argument is never read. It is also measured on a **different series** from the other two `volatility` conditions, which read the strategy's own `atr_percentile`. So "symbol-specific" is confounded with "which timeframe the frame happened to offer as `regime_tf`", and with the fact that `volatility_normal` **passes on a dataclass default during warm-up** while `regime_trending`/`regime_ranging` fail (`D16`). | "**`volatility_normal` is a filter on the frame's regime timeframe, not the strategy's.** Its +9.64 and its MGC-60m −6.30 are both measured against a series the strategy does not trade. The symbol-specificity is not yet separable from frame composition." Given it is a base filter in **12 of 13 templates**, this is the widest-reach weakening in the corpus |
| **B11** | Suggestive: "`fib_golden_pocket` beats `fib_shallow_retrace` **at 240m on all three symbols** … Deserves its own study." | **WEAKENED** (already closed) | closed as refuted by `2026-09-24_ORB-and-ICT.md` the same day. Rounds 1–2 add `D-F1`: `swing_leg()` returns the last confirmed low and the last confirmed high **independently**, so it spans other confirmed swings on **14.4–17.2%** of bars, and every fib ratio is computed off the wrong base one bar in six. | already closed. The restatement that matters is B16's |

## B.3 — the refuted premises

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **B12** | "**Confluence does not help.** 2 signals → 4 cuts median trade count 35% (65 → 42, matched z = +8.48) and does not move expectancy — the sign favours **two**. One filter beats three or four on every statistic. **2 signals, 1 filter.**" | **WEAKENED (the axis, not the sign)** | the count axis is contaminated by duplicates: `D-M1` (`macd_directional` ≡ `macd_hist_direction`, identical on 5000/5000 bars in five cells, and `momentum` is an optional group in **11 of 13** templates); `D-MR1` (`bollinger_extreme` ⊂ `bollinger_mean_pull`, 601/601, 686/686, 635/635); `D-R2` (`regime_matches_direction` adds **zero** gating over TREND's `regime_trending` base filter); plus the seven group-alias filters the report already lists. So some "4-signal" strategies make 3 independent readings. | "**More conditions is not better, and some of the extra conditions were not extra** — the 2-vs-4 axis overstates how much information a 4-signal strategy reads." The sign is unaffected and arguably reinforced: a duplicate adds count and no information, which is precisely what "no expectancy gain" would look like |
| **B13** | "**Multi-timeframe agreement does not help.** Requiring any alignment signal is detectably *worse* than requiring none (z = −4.09, 366 vs 1,151). **Unanimity versus majority: no detectable difference.** `mtf_aligned` is the strongest negative condition in the library (z = −2.53)." | **the second sentence is INVALID — measured nothing (DEGENERATE); the first and third are WEAKENED** | `D-MTF2` + **R6-M2**: on the frames the programme used, `mtf_strongly_aligned` and `mtf_aligned` return **identical `(triggered, direction)` on 100% of bars at 240m (1348/1348 MGC, 1347/1347 MES) and at 1440m (2511/2511, 1859/1859)**, and on 93.7–95.0% at 60m. "Unanimity versus majority" therefore **cannot be measured** in a two-timeframe frame and is near-unmeasurable in a three-timeframe one — which `D17` already recorded and this report restates as an empirical null. For the first and third sentences: `D-MTF3` — the PULLBACK base filter member is frame-composition dependent with a **37-point** pass-rate swing (§2.1), and `D-MTF1`'s dead-at-top case does not reach these cells (§2). R1's own verdict: "**Whether multi-timeframe alignment helps is therefore still an open question here, not a settled negative**" (`research/R1_group_audit.md` Group 9). | "**Unanimity versus majority is not a testable distinction on these frames — the two conditions are the same function.** Requiring alignment measured worse than not requiring it, in an implementation where the graded condition had no independent content at the two highest bindings and the group's filter member was frame-dependent." This also amends **`BRIEF.md` rule 2**, which is stated as settled |
| **B14** | "**Trend-following does not need a trending regime.** `regime_trending`: 3 cells positive, 3 negative, while halving trade count." | **WEAKENED** | `D-R1`: all three `regime` conditions accept `tf` and never read it `[repo-verified: futures_agents/strategies/library.py:752-754, 760-762, 768-774]`; `snap.regime` is read off the frame's `regime_tf`. With `FRAMES[240] = [240,1440]` the chosen `regime_tf` is 240; with `FRAMES[60] = [60,240,1440]` it is 60 — but `_default_regime_tf` prefers `(15, 30, 5, 60, …)`, so in any frame containing 15m or 30m the gate is the **15-minute** regime `[repo-verified: futures_agents/features.py:819-825]`. `regime_trending` is TREND's **base filter**. | "**A TREND strategy's regime gate is the frame's regime timeframe, not the strategy's.** Whether trend-following needs its *own* timeframe to be trending has not been tested." The measured 3+/3− and the halved trade count stand as facts about this implementation |
| **B15** | "**Compression does not precede tradeable expansion.** Requiring `volatility_compressed` scores up to z = **+12.20 in sample** and goes significantly negative out of sample in 6 of 12 cells … **The cleanest overfit in the programme.**" | **STANDS in verdict, WEAKENED in label** | `D-V1`: the condition's description says "Bollinger width in the bottom quartile" and the body reads **`atr_percentile <= 0.30`** `[repo-verified: futures_agents/strategies/library.py:735-743]`. `RegimeSnapshot.bb_width_percentile` **exists** and is unread `[repo-verified: futures_agents/indicators/regime.py:40, 182-191]`; the two disagree on the "bottom 30%" verdict on **27.5–29.9%** of bars, corr 0.506–0.522. It is BREAKOUT's **base filter**. And `D-V2`: BREAKOUT + `volatility_expanding` is `p<=0.30 AND p>=0.70`, **empty by arithmetic on every bar**, at **10 of 60** generated BREAKOUT strategies. | "**An ATR-percentile compression gate is the cleanest overfit in the programme.** Bollinger-width compression, which is what the condition's description names and what a practitioner would mean, has never been tested here." The IS/OOS instability is a real, measured result — the object it is about is not the one named |
| **B16** | "**Fibonacci levels carry no information here.** `fib_sr_confluence` fires on **48.6–81.0%** of all bars … Fib-level bars are indistinguishable from plain support/resistance bars … **Four conditions can leave the search space with no measured loss.**" | **`fib_sr_confluence` STANDS; the three retracement conditions WEAKENED** | `D-F2` independently reproduces the filter's near-unconditionality (56.8–80.2%, and the four 0.8-ATR windows cover **100% of the leg span on the median bar**). But `D-F1` is new and cuts the other way: `swing_leg()` `[repo-verified: futures_agents/features.py:119-131]` takes the last confirmed low and the last confirmed high **independently**, which is a single impulse leg only if nothing lies between them — false on 808/4784 MGC, 686/4759 MCL, 820/4763 MNQ bars. So `fib_golden_pocket`, `fib_shallow_retrace` and `fib_extension_reached` were computed off a multi-leg span one bar in six. | "**This library's fib conditions carry no information, and on 14–17% of bars they are not measuring the levels a trader drawing the same chart would draw.**" Keep the conclusion; do not generalise it to Fibonacci retracement as a technique. The fix needs no new data — `visible_swings()` already returns the ordered list `[repo-verified: features.py:421-425]` |
| **B17** | "**The lunch-hour folk claim is refuted.** Turning `avoid_lunch` on hurts (z = −3.25)." | **INVALID — measured nothing** (sub-kind **DEGENERATE**), on MGC; per-symbol elsewhere | `D-T1`: `SESSIONS` is a hard-coded ET table with `LUNCH = 12:00–13:30` and `classify_session(dt)` takes **no contract** `[repo-verified: futures_agents/timeutil.py:106-123, 127-133]`. Measured against each contract's own RTH, the bars `avoid_lunch` vetoes sit at `minutes_since_open` **220 / 250 / 280 on MGC — the final 90 minutes of the 310-minute COMEX pit session**; 180/210/240 of 330 on MCL (mid-to-late); 150/180/210 of 390 on MNQ (the middle, correct). And `avoid_lunch` is a **base filter in REVERSAL** `[repo-verified: combinator.py:208]`. This is the same defect `power_hour`'s docstring records as found and fixed `[repo-verified: library.py:896-902]`; `avoid_lunch` never got the fix. | "**On MNQ and MES, turning a lunch filter on hurts. On MGC the same condition excludes the last 90 minutes of the pit session, so the MGC arm is not a lunch test at all, and on MCL it is only approximately one.**" The broader rule — `BRIEF.md` rule 6, "no hours filter improves expectancy" — rests on more than this one condition and **survives**; this specific refutation does not, symbol-independently |

## B.4 — "Groups that cannot be evaluated as built"

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **B18a** | SUPPLY_DEMAND "**Unusable.** Zero strategies reach 20 trades in six cells; quadrupling budget moved 0 → 0. `fresh_zone_approach` fires on 0.5–3.8% of bars, scarcest in the library. Needs `min_signals=1` or demotion to a FILTER." | **STANDS, confirmed** | R1 Group 13 audits `supply_demand_zones` line by line and finds it **CLEAN** — a genuine base-plus-departure algorithm, not a relabelled swing — with `zone_touch` at 1.6–3.8% and `fresh_zone_approach` at 0.8–1.4%, 40–69 fires per 5,000 bars. `D-SD2`: the template's ceiling is ~27–130 signals per cell **by construction of its required group**. | unchanged. Add: "the detector is correct and the concept is scarce **as this library defines the zone** — `2026-09-24_ORB-and-ICT.md` measured a base-free order block at 40.5–51.5%, so the scarcity is definitional" |
| **B18b** | LIQUIDITY sweep side "**Never testable.** 156 rule sets with ≥1 trade, **0 with ≥20**, every cell every symbol. Every published LIQUIDITY number is 100% the breakout side." | **STANDS, sharpened** | `D36` (already published: `session_extreme_sweep` is self-referential, so its 0.61% is degeneracy not rarity) plus rounds 1–2: `D-L1` — 2 of the 7 `liquidity` conditions are DEAD at 1h on MGC/MNQ/MES; `D-T2` — LIQUIDITY's base filter `after_opening_range` passes 56–61% of the time **outside RTH entirely**, so "wait out the opening range" actually means "trade any hour except 00:00–09:59 ET". | "Every published LIQUIDITY number is the breakout side, **and on MGC/MNQ/MES at 1h it is the prior-day / overnight / initial-balance side specifically, gated by a filter that admits most of Globex.**" |
| **B18c** | VOLUME_PROFILE "One condition wearing six names — 100% of floor-clearing strategies carry `value_area_breakout`, which fires on ~51% of bars. Treat it as a trend proxy. **Cannot trade at 4h at all.**" | **STANDS, confirmed and extended** | `D-P1` + **R6-M2**: `prior_profile` None on 1348/1348 MGC 240m, 1347/1347 MES 240m, **and 2511/2511 MGC / 1859/1859 MES daily, with all six conditions firing 0 times on both daily series**. And the two FILTERs **block** rather than abstain `[repo-verified: library.py:1032-1033, 1050-1051]`. `D-P2` adds that on 4.1–10.5% of bars the value-area verdict — including direction — depends on which CSV built the profile. | "Cannot trade at 4h **or daily** at all, and the two profile filters veto rather than abstain when the profile is missing." Add `D-P2` as a caveat on every 60m VOLUME_PROFILE row |
| **B18d** | MEAN_REVERSION "The +0.070 was a floor artefact; floor-free it is **−0.141R, worst of 12 groups**." | **STANDS, with a population caveat** | `D-MR1` — the required `meanreversion` trio is a nested family, so the required slot's effective variety is nearer 1.5 than 3. `D-R1` — `regime_ranging` is MEAN_REVERSION's **base filter** and is timeframe-inert, with a 13-point pass-rate swing from changing the frame's timeframe list. | verdict unchanged; "worst of 12 groups" is measured on a template whose unconditional filter's strictness is a property of the frame |
| **B18e** | PULLBACK "`adx_trending` is **not offered to this template at all** — the library has no strength gate on the trend precondition." | **STANDS** | independently confirmed `[measured: python3 over combinator.TEMPLATES → PULLBACK optional_filters = ('outside_news_blackout','no_imminent_release','no_recent_imbalance'); adx_trending appears as MULTI_TIMEFRAME's optional filter]`. | unchanged. Add `D-MTF3` / §2.1: PULLBACK's base filter `mtf_not_conflicted` swings from 62.6% to 99.1% pass rate purely with the cell's frame, so **every cross-timeframe PULLBACK comparison in this report is confounded** |
| **B18f** | REVERSAL "`range_position_extreme` is a **guaranteed zero** inside it … 262–440 rule sets per cell, 0 trades, 12 of 12 cells." | **STANDS — and rounds 1–2 add a larger claim about the same template** | `D25` already published. The new one is **R1-D4a c.2**: `orderflow` is **required** by REVERSAL `[repo-verified: futures_agents/strategies/combinator.py:201-211]`, all three `orderflow` conditions are OHLCV bar-shape algebra, and `delta_confirms_bar` is literally `close > (high+low)/2 and close > open` `[repo-verified: library.py:455-467]`. 20 of 20 REVERSAL strategies in a 284-strategy sample carried one. So **every REVERSAL row in the corpus is a result about a close-location predicate, not about absorption**, despite the template's own description reading "Exhaustion and **absorption** against the prevailing move" `[repo-verified: combinator.py:203]`. Plus `D22` (240m REVERSAL empty) and `D-T1` (REVERSAL's `avoid_lunch` base filter inverted on MGC). | keep `D25`. **Add a row:** "REVERSAL — every strategy of this template carries a required `orderflow` condition, and `orderflow` reads no aggressor. Every REVERSAL result is about bar shape." That is the single largest name/arithmetic gap in the repository and it affects **1 of the 13 groups every published table is cut by** |

## B.5 — hard constraints and next steps

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **B19** | Constraint 3: "Seven filter names are exact aliases for group membership … A/B on them compares groups." | **STANDS, confirmed** | R1's full 19-group × 13-template requirement map reproduces all seven `[research/R1_group_audit.md`, "The template requirement map"]`. | unchanged |
| **B20** | Constraint 5: "**Cross-symbol comparison is currently impossible.** `generate_combinations` seeds RNG per symbol, so MES and MGC 60m populations share **0 of 204** rule sets." | **STANDS, and there is now a second independent reason** | `R1-D4a c.3`: `profiles.groups_for` returns a **different group set per symbol** — MGC 6, MES 7, MNQ 7, MCL/NQ/ES `None` → all 13 `[measured: python3 over profiles.groups_for]`. That does not affect the four reports (§2.2 — all three harnesses override `groups=`), but it means a *default* sweep compares different template sets, not only different rule sets. | unchanged, plus: "and on a default sweep the *group set* also differs per symbol — the four published reports override this, and any future one must say whether it did" |
| **B21** | Constraint 7: "Costs are under-charged on multi-target exits … 62–92% of 4h/daily exits pay no exit slippage." | **STANDS** | `D13`, already published. Nothing in rounds 1–2 touches costs; the one round-2 finding near them (`run_portfolio` does not net positions, `research/R3_path_operation.md:626-637`, `[repo-verified: engine.py:554-559 delegates to run_many]`) concerns exposure, not cost. | unchanged |
| **B22** | Priority 1: "fix the defect register. **26 defects** … D21–D26 are not [fixed]." | **STANDS, count superseded** | the register is now **D1–D49** plus four items R3 raised and the manager has not yet numbered `[research/R3_path_operation.md:25]`. Open at last count: D21, D24, D36, D37, D38, D39, D40, plus D44–D49. | update the count; the priority is unchanged and more urgent |
| **B23** | Priority 2: "a measurement harness that cannot produce these artefacts. Floor-free censuses by default; disjoint periods by default; matched controls by default; per-cell statistics; and a guard that refuses to report a condition as an effect when it is a group alias." | **STANDS, and rounds 1–2 show the list is missing its most important item** | five structurally zero-trade configurations (`research/R1_group_audit.md`) and three more degenerate ones (`D-V2`, `D-MTF2`, **R6-D1**) were all invisible to every guard on that list, because each of them produces a *null*, and the list has no null-provenance check. `workspace/newstrats/orb.py` is the only module in the repo that has one `[repo-verified: workspace/newstrats/orb.py:47, 118, 174-183 — `resolvable()` and the `INERT` counter]`. | **add a sixth item: a per-condition firing census on the exact frame, run before any null is reported, and a refusal to report a null from a condition that fired on zero bars.** That is the guard that would have caught `openinterest`, ORB at 1h, `profile` at 240m and VWAP at daily |
| **B24** | Priority 3's retraction: "`break_of_structure` at 240m … **does not reproduce**: median expectancy −0.0364R over 142 strategies, 37% profitable … A comparator artefact plus one favourable period. Do not build on it." | **STANDS — and it is a *measured* negative, not a dead detector** | R1 Group 12 finds `structure` **CLEAN**, all five conditions, arithmetic matching name and description, and `break_of_structure` firing on **31.4–37.2%** of bars `[measured: R1 census, 5 cells]`. A healthy population failing out of sample is exactly the "we measured absence" case. | unchanged. Worth flagging as a model retraction: the population was alive and the idea died |

**Report B counts:**
**STANDS 17** (B1, B2, B4, B5, B9, B18a, B18b, B18c, B18d, B18e, B18f, B19, B20, B21, B22, B23, B24) ·
**WEAKENED 10** (B3, B6, B7, B8, B10, B11, B12, B14, B15, B16) ·
**INVALID 2** (B13's "unanimity versus majority" sentence; B17 on MGC) ·
**UNAFFECTED 0** · **total 29**.

Two split verdicts, resolved as follows so the count is unambiguous: **B13** — the first and third
sentences are WEAKENED, the second is INVALID; I count the claim once, as INVALID, because that is
the sentence a reader would act on. **B15** — the verdict ("the cleanest overfit") STANDS and the
label is INVALID; I count it WEAKENED, because the overfit is real and only the named object is
wrong. Both splits are stated in the rows themselves.

Both invalidations are **DEGENERATE**, not ZERO-FIRE: `mtf_strongly_aligned` and `avoid_lunch` both
fire freely — they just do not compute what their names say. That is the harder failure mode to
catch, because a firing census does not flag it.


---

## 2.3 — R6-M3: the open R1-vs-R3 discrepancy on the `csv/raw` 1h grid, resolved in R1's favour

`msgs/11_R3_R1_re-stopkind-RANGE.md` and `research/R3_path_operation.md:2202-2213` record an
unresolved disagreement: R1 measured **2 of 5,000** MES and MNQ 1h bars inside the opening-range
window and attributed them to two holiday half-sessions; R3 measured the 1h grid as "**100% at
`:00`**" and argued the correct figure is 0. R3 concluded R1's finding was therefore *stronger* than
stated. **R1 is right and R3's grid count is wrong.** Neither conclusion changes, but the record
should.

`[measured: PYTHONPATH=. python3 — load_csv csv/raw/{MGC,MES,MNQ,MCL}_1h.csv, Counter(to_et(b.ts).minute),
and count bars with 0 <= minutes_since_open(b.ts, get_contract(s).rth_open) < 30]`

| symbol | minute histogram | `rth_open` | bars with `0 <= mso < 30` |
|---|---|---|---|
| MGC | `{0: 4992, 30: 8}` | 08:20 | **0** |
| MES | `{0: 4992, 30: 8}` | 09:30 | **2** |
| MNQ | `{0: 4992, 30: 8}` | 09:30 | **2** |
| MCL | `{0: 4992, 30: 8}` | 09:00 | **215** |

All four files carry **8 off-grid `:30` bars**, and they are the same eight dates in all four:

```
2025-11-28 09:30, 10:30, 11:30, 12:30   (Thanksgiving Friday half-session)
2025-12-24 09:30, 10:30, 11:30, 12:30   (Christmas Eve half-session)
```

The two MES/MNQ in-window bars are `2025-11-28 09:30` and `2025-12-24 09:30` exactly, confirming
R1's attribution verbatim. **So every opening-range signal MES and MNQ ever produced at 1h came from
two holiday half-sessions** — a two-date sample wearing a 5,000-bar denominator. Raised to R1 and R3
as `msgs/R6-01_R3_csv-1h-grid-discrepancy.md`.

---

# Report C — `scan_reports/2026-09-24_ORB-and-ICT.md`

6 studies, 5 symbols, and the report the dispatch flagged as most exposed. **It is the least
damaged of the four**, and the reason matters: it is the only report that audited a detector before
reporting a null.

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **C1** | "**Neither gives good reward for risk on this data. No algorithm was written, and I recommend against writing one.**" | **STANDS** | nothing in rounds 1–2 rescues either methodology. | unchanged |
| **C2** | "ORB: **median expectancy −0.092R** against a median **32R** max drawdown. 1,920 configurations, 194,005 trades, 18.8% profitable, best t = 2.137 against 3.888. **Negative at zero transaction cost**, so it is an absent edge rather than a cost problem." | **STANDS — and `D-L1` corroborates it rather than undermining it** | the dispatch flagged `D-L1` as bearing directly on this conclusion. It does not, because **this verdict was never measured on the library's `opening_range_breakout`.** It was measured on `workspace/newstrats/orb.py`, which implements the resolvability rule as `resolvable(symbol, tf, length)` — `tf <= length`, `length % tf == 0`, and `open_minutes % tf == 0` `[repo-verified: workspace/newstrats/orb.py:174-183]` — never silently widens a range, and counts unmeasurable cells in `INERT` `[repo-verified: :47, :118, :249]`. And the design ran at **tf ∈ {5, 15} only**, with each contract's own open `[measured: json.load(workspace/studies/out/orb_test.json)['findings']['design'] → timeframes [5, 15]; rth_only "YES, deliberately on … MGC 08:20, MCL 09:00, MES/MNQ/NQ 09:30 ET"]` — i.e. precisely the timeframes where `D39`'s resolvability rule says an opening range **can** be built. `D-L1` is a finding about the *library condition*, and its per-symbol table agrees with this module's own table line for line. | **unchanged.** Add one sentence so a future reader cannot mistake the scope: "this verdict is measured on a purpose-built ORB at 5m and 15m, not on `library.opening_range_breakout`, which cannot fire at 60m on three of four symbols (`D-L1`, `features.py:865`)" |
| **C3** | "ICT: **0 live-eligible** across every concept tested." | **STANDS** | untouched. | unchanged |
| **C4** | "Order blocks and fair value gaps **fail at bar level** before an exit is chosen." | **STANDS, reinforced** | R1 Group 12 audits `fair_value_gaps` and finds it a **textbook three-bar FVG with correct visibility**: a bullish gap is `bars[i+1].low > bars[i-1].high`, the gap is only knowable at `i+1`, and fill tracking scans forward from `g.index + 2` `[repo-verified: futures_agents/indicators/structure.py:409-440]`. **No look-ahead, correct definition.** So the FVG null is a measured null. | unchanged; cite R1 Group 12 as the detector check that licenses reading it as absence |
| **C5** | "The central **sweep→shift→retrace sequence is real and common and adds nothing**. 1,893–2,014 sweeps → 77–106 retraces per symbol in 10.5 months, 57–68 trades per cell, against the sweep family's previous zero rule sets reaching 20 trades. At matched distance, sweeping liquidity predicts the shift **slightly worse than never touching a level at all** (MH OR 0.86)." | **STANDS — and this is the corpus's best example of "we measured absence"** | the report states its own population size before its verdict and explicitly contrasts it with the starved failures. Round 1 confirms the starvation was the detector: `D36` (`session_extreme_sweep` self-referential) and R1's census putting it at **0.5–1.8%** of bars, 23–92 fires per 5,000 `[measured: R1 census, 5 cells]`. | unchanged. This claim should be the template for how every other null in the corpus is reported |
| **C6** | "**Kill zones are trade thinning.** Directional efficiency is flat across the entire clock (0.37–0.50 every hour) … **21:00 ET is +4.52** while **08:00 ET, inside its New York kill zone, is the worst hour of the day at −3.41**." | **WEAKENED (per-symbol scope)** | `D-T1`'s mechanism: an ET hour is a different object on each contract, because RTH differs — MGC 08:20–13:30, MCL 09:00–14:30, MNQ/MES 09:30–16:00 `[repo-verified: futures_agents/config.py:157,179]`. 08:00 ET is **pre-open** on every one of the five symbols; 21:00 ET is Globex on all of them. `D31` (kill zones arithmetically impossible at 240m) is already published. | the clock-flatness result stands. "08:00 ET is the worst hour" should read "the pre-open hour is the worst", and the per-symbol session must be stated, because ICT's kill zones are defined against the **equity** session and three of the five contracts do not have it |
| **C7** | "**OTE is an existing condition under another name, already refuted.** Jaccard 0.938–1.000, direction-aware identical — the seventh duplicate condition found in this project." | **the duplication STANDS; the "already refuted" WEAKENED** | `D-F1`: the condition OTE duplicates is `fib_golden_pocket`, and `swing_leg()` spans other confirmed swings on **14.4–17.2%** of bars, so the band tested is drawn off a multi-leg span one bar in six. The Jaccard identity is unaffected — two conditions computed off the *same* wrong leg are still identical. | "OTE is `fib_golden_pocket` under another name. **Both are computed off a mis-identified swing leg on 14–17% of bars**, so 'already refuted' means 'refuted as implemented', not 'refuted as drawn'" |
| **C8** | "**Five placebos, and each one wins.**" (yesterday's OR; ATR-matched sham zones; entries displaced 5 bars; the deliberately wrong order; every 24th bar by index) | **four STAND; the displaced-5-bars row WEAKENED** | not a round-1/2 finding, but a cross-report inconsistency worth recording: `D42` (published in `workspace/studies/DEFECTS.md:620-638` and in the ranking report, **dated after this report**) establishes that a 5-bar displacement **retains part of the signal** and is "a **degraded real strategy, not a placebo** … a *conservative* control". | the four clean placebos stand. For the displaced-5-bar row, say what `D42` says: a shifted placebo beating the real entries is a **weaker** result than a random or shuffled one doing so — it still points the same way, with less force |
| **C9** | "The famous **80–90% fill rate is true and carries no information**. Price returns to a random zone 87–90% of the time." | **STANDS** | untouched; `fvg_nearby`'s detector is CLEAN (C4). | unchanged |
| **C10** | "**The opening range was never constructed** at 60m or 240m … `T \| L` and `T \| RTH-open-in-minutes` … 4-hour ORB is arithmetically impossible. `snap.opening_range` was None on **4,990 of 5,000** MES 60m bars." | **STANDS, and rounds 1–2 sharpen it three ways** | (i) `D-L1` adds **MGC 1h = 0/5000** — total death, not 99.8%; (ii) **R6-M3** confirms R1's two MES/MNQ in-window bars are **2025-11-28 and 2025-12-24**, two holiday half-sessions, and resolves R3's contrary grid count against R3; (iii) `D-L2` adds the consequence the report does not draw — the OPENING_RANGE template **does not fail**, it silently draws one of the other five `liquidity` conditions. | keep, and add: "4,990 of 5,000 on MES, **5,000 of 5,000 on MGC**, and the 10 surviving MES/MNQ bars are two holiday half-sessions. And the template does not fail when the range is missing — it substitutes" |
| **C11** | "**The shipped ORB condition was not an ORB.** No first-break gate, no session gate — 18.5% of MES 15m bars, ~7 per day, including overnight bars. On MCL it silently built a 30-minute range **60 minutes wide** and was a Jaccard 0.993 duplicate of `initial_balance_break`." | **STANDS, confirmed** | `D-L1` reproduces the silent widening from the other direction: `OpeningRange.minutes` reports **30** while the MCL 1h range is 60 wide `[repo-verified: futures_agents/features.py:911]`, and `initial_balance_break` survives where the OR conditions die because it uses its own `mso < 60` accumulation, **not** gated on the 30-minute window `[repo-verified: features.py:888-890]`. | unchanged; add `features.py:911` and the reason `initial_balance_break` is the survivor |
| **C12** | "**The combinator cannot express a sequence at all.** `min_signals=2` requires two conditions on the same bar." | **STANDS** | `D37`, still open. R3 reconfirms from the other side: III-5 and the canonical stop-and-reverse are INEXPRESSIBLE-ARCHITECTURE `[research/R3_path_operation.md:1680-1690]`. | unchanged |
| **C13** | "**`session_extreme_sweep` is self-referential** — it compares each bar against a session high that includes that bar. Its 0.61% rate was degeneracy, not rarity." | **STANDS, confirmed** | R1's census independently gives 0.5–1.8% across five cells, 23–92 fires per 5,000, the thinnest of the seven `liquidity` conditions `[measured: R1 census]`. | unchanged |
| **C14** | "**SUPPLY_DEMAND's emptiness was its detector.** The library's zone fires on 0.56–1.38% of bars; ICT's base-free order block fires on **40.5–51.5%**." | **STANDS, confirmed** | R1 Group 13 verdict is **CLEAN** — `supply_demand_zones` is a genuine base-plus-departure algorithm with a 2.0× departure gate and a 400-bar expiry `[repo-verified: futures_agents/indicators/structure.py:622-690]` — and measures `fresh_zone_approach` at 0.8–1.4%. So the scarcity is **definitional, not a bug**, which is a stronger form of the report's own claim. | "the emptiness is its detector's **definition**, and the detector is correct code. A base-free zone is a different object, not a repaired one" |
| **C15** | "**Resampling cannot detect a bias whose sign is always favourable. Only auditing the fill model can.** … This is the one failure mode the entire programme's methodology is blind to, and it is now a required check." | **STANDS — and rounds 1–2 show the principle generalises past the fill model, which the report did not say** | rounds 1–2 are an audit of the **signal** model rather than the fill model, and they found five structurally zero-trade configurations plus three degenerate ones. Out-of-sample testing, disjoint periods and walk-forward all pass a detector that never fires, for exactly the reason the report gives about fills: the defect is present in every period. | keep the sentence and generalise it: "**Resampling cannot detect a defect that is present in every period. Only auditing the model can — the fill model *and* the signal model.**" That is the one-line statement of this entire audit, and this report is 90% of the way to it already |
| **C16** | "`fib_golden_pocket` vs `fib_shallow_retrace` **refuted** — neither band predicts anything at bar level (best \|t\| = 1.80); at 240m **zero matched pairs reach 20 trades** in any disjoint slice; the reported 60m loss has the **opposite sign** (+4.01)." | **WEAKENED** | `D-F1` (the leg) and `D-F2` (the confluence filter passes 56.8–80.2%, and its four 0.8-ATR windows cover the whole leg on the median bar). Also `FIBONACCI`'s required group is `fibonacci`, so **no FIBONACCI strategy can exist without one of the three `D-F1`-affected conditions** (R1 Group 5). | "**as implemented** — off a swing leg that spans other confirmed swings on 14–17% of bars — neither band predicts anything." The bar-level null and the 240m zero-pairs finding both stand |
| **C17** | "the repaired ORB module now counts unresolvable cells in `orb.INERT`, so **'unmeasurable' can never again be read as 'no signal'** — the mistake that hid all of this." | **STANDS, and it is the only such guard in the repository** | `[repo-verified: workspace/newstrats/orb.py:47, 118, 174-183, 249, 381, 395]`. Rounds 1–2 found four more cases of exactly the mistake this guard prevents, **none of them in `orb.py`** — `openinterest`, `profile` at 240m and daily, MULTI_TIMEFRAME at a frame's top timeframe, and `vwap` at daily. The library itself has no `INERT` counter, no `resolvable()`, and no equivalent. | keep, and narrow the scope of the guarantee: "**in this module.** Nothing in `futures_agents/` counts an inert cell, which is why four more were found three days later" |
| **C18** | Scope header: "60m/15m/5m plus a **352-session 1-minute archive**." | **WEAKENED (disclosure, and this is mine, not a round-1/2 consequence)** | the ORB verdict's per-symbol table is measured on `data/*_1m.csv`, which the study artefact discloses as "**Oanda CFD 1-minute bars 2019-01 to 2020-05** for the underlyings MGC/MES/MNQ are written on … the deep source is **the CFD underlying, not the futures contract: no basis, no roll, no CME volume**" `[measured: json.load(workspace/studies/out/orb_test.json)['caveats']]`, and the file header confirms a 2019 start `[measured: head -3 data/MGC_1m.csv → timestamp,open,high,low,close,volume / 2019-01-01T23:00:00+00:00,1282.645,…]`. **The published report says none of this.** It is disclosed in the artefact and in `ORB_ICT_FINDINGS.md`, so this is a report-writing omission, not a measurement fault. | add to the header: "**the deep 1-minute archive is Oanda CFD data on the underlying, 2019-01 to 2020-05 — not the futures contract, no basis, no roll, no CME volume. `csv/raw` gives only 18–19 usable RTH sessions per symbol.**" This matters because `BRIEF.md` treats cross-vendor substitution as fatal to a stop (MCL vs `CL=F`, 0.95¢ mean) and the same standard applies here |

**Report C counts:**
**STANDS 13** (C1, C2, C3, C4, C5, C9, C10, C11, C12, C13, C14, C15, C17) ·
**WEAKENED 5** (C6, C7, C8, C16, C18) · **INVALID 0** · **UNAFFECTED 0** · **total 18**.
Three of the five WEAKENED are per-symbol-scope or disclosure items, not measurement faults.

**Report C holds the only zero-invalidation record of the four, and it is not luck.** It is the one
report that measured its detector's firing rate before reporting its null, built a purpose-made
module when the library's condition turned out not to be the object, and counted the cells it could
not measure.

---

## 2.4 — R6-M4: the chronology test's group universe is 6 / 4 / 3, not thirteen

This is my largest single measurement and it belongs before Report D's table because three of that
report's Part C claims depend on it. It is a re-analysis of a committed artefact — **no backtest, no
new sweep** — and it reproduces the published persistence table exactly, which is what licenses the
rest of it.

`[measured: python3 over workspace/chrono/ledgers/{MGC,MES,MNQ}_1440.json, replicating
workspace/chrono/analyse.py:28-29 (MIN_TRADES=20, MIN_MONTHS=24) and :71-86 (winner = argmax of
monthly mean R among groups present that month, months with ≥3 candidates only)]`

**Replication check first — my numbers must match the published table before I may reason from them:**

| symbol | published "winner repeats" | my replication |
|---|---|---|
| MGC daily | 20 / 95 | **20 / 95** |
| MES daily | 17 / 56 | **17 / 56** |
| MNQ daily | 18 / 60 | **18 / 60** |

Exact. Now the part the report does not state:

| symbol | groups with **any** daily trade | groups clearing 24 months of ≥20-trade cells — **the actual candidate set** |
|---|---|---|
| MGC daily | 10 of 13 | **6** — BREAKOUT, MOMENTUM, MULTI_TIMEFRAME, REVERSAL, TREND, VWAP |
| MNQ daily | 10 of 13 | **4** — MOMENTUM, MULTI_TIMEFRAME, REVERSAL, VWAP |
| **MES daily** | 10 of 13 | **3** — MOMENTUM, MULTI_TIMEFRAME, VWAP |

**Three of the thirteen groups take zero trades on every daily series, all three symbols:**
**VOLUME_PROFILE, OPENING_RANGE, LIQUIDITY**
`[measured: same run → groups with trades are VWAP, MOMENTUM, MULTI_TIMEFRAME, TREND, REVERSAL,
BREAKOUT, FIBONACCI, PULLBACK, MEAN_REVERSION, SUPPLY_DEMAND on all three ledgers]`.
Each absence has a named implementation cause, none of them a market fact:

- **VOLUME_PROFILE** — `prior_session_profile` requires ≥10 bars in the prior session and a daily
  series has one, so all six `profile` conditions fire **0 times on 2511 MGC and 1859 MES daily
  snapshots** (R6-M2), and `profile` is VOLUME_PROFILE's **required** group. This is `D5` and `D-P1`.
- **OPENING_RANGE and LIQUIDITY** — `D23`: `_build_session_state` derives previous-day levels from
  bars flagged `is_rth(b.ts)`, and **`is_rth` is False on 100% of daily bars**; `D20` records daily
  LIQUIDITY at 1068/1068 and daily OPENING_RANGE at 972/972 zero-trade.

**The report's own pair counts already encode this and its prose contradicts them.** Part C reports
the cross-lag test as "MGC **20** pairs, MNQ **12** pairs, MES **6** pairs". Ordered pairs among *k*
groups is `k(k−1)`: 12 = 4×3 and **6 = 3×2**. So the artefact says 4 and 3 groups while the prose
says thirteen.

**And the programme's own analysis script prints the group count on every line.** I re-ran it
unmodified — the only command I executed that produces the report's numbers directly:

`[measured: PYTHONPATH=. python3 workspace/chrono/analyse.py]`

```
MES 1440m   89 months  2019-05-03..2026-09-21   34,027 trades   groups with >=24 months: 3
   winner repeats next month: 17/56 vs 18.3 shuffled   z=-0.37
   most frequent monthly winner: VWAP 22x, MOMENTUM 18x, MULTI_TIMEFRAME 17x
   cross-lag A(t) -> B(t+1): 6 pairs tested, Bonferroni needs |z|>=2.64, 0 survive

MGC 1440m  117 months  2016-09-26..2026-09-21   56,670 trades   groups with >=24 months: 6
   winner repeats next month: 20/95 vs 18.2 shuffled   z=+0.49
   most frequent monthly winner: MULTI_TIMEFRAME 29x, VWAP 20x, MOMENTUM 18x, REVERSAL 12x
   cross-lag A(t) -> B(t+1): 20 pairs tested, Bonferroni needs |z|>=3.02, 0 survive

MNQ 1440m   89 months  2019-05-03..2026-09-21   39,373 trades   groups with >=24 months: 4
   winner repeats next month: 18/60 vs 14.7 shuffled   z=+1.00
   most frequent monthly winner: MULTI_TIMEFRAME 18x, MOMENTUM 16x, VWAP 16x, REVERSAL 11x
   cross-lag A(t) -> B(t+1): 12 pairs tested, Bonferroni needs |z|>=2.87, 0 survive
```

`groups with >=24 months: 3 / 6 / 4` is printed by `workspace/chrono/analyse.py:65` on every run.
Every z, every repeat count and every pair count in Part C reproduces exactly. **The number was on
stdout the whole time and the prose says thirteen.** Note also that `REVERSAL` is the 4th-most
frequent winner on both MGC and MNQ — so on those two symbols "the same three groups" is the top 3
of 6 and of 4 candidates, and on MES it is the top 3 of **3**.

---

# Report D — `scan_reports/2026-09-24_MGC-MCL_ranking-persistence-and-chronology.md`

516,651 evaluations on MGC+MCL, 692 top-10 rows, 27 cells, plus the MES/MNQ contaminated comparison
and the daily chronology. Harness: `workspace/newstrats/rank_audit.py`, `workspace/chrono/*`.

## D.1 — the four mandatory statements

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **D1** | "**516,651 evaluations** on the clean MGC+MCL population … Programme-wide: **2,975,629**." / "`free_t = 5.13`; programme-wide `free_t = 5.46`. **Zero of 692 top-10 rows clear it.**" | **WEAKENED (wording only)** | `BRIEF.md:230-244`, per the manager's `R1-Q2` ruling. Plus §2.2: this run also forced all 13 groups, so `openinterest` carriers that can never trade are inside 516,651 on **both** clean contracts, not only on MNQ. | "**≥ 516,651 candidates were *generated*, of which an unmeasured subset could not trade**"; quote `free_t = 5.46` with its **495k / 5.15** companion from `RANKING_FINDINGS.md:66-72`. *n* would have to fall to ~2,197 to meet the largest t ever found (3.923), so **the verdict does not change, the sentence does** |
| **D2** | "Largest t on clean contracts: **3.27**. Largest t in the project: **3.923**. Nothing is close, and nothing here is live-eligible." | **STANDS** | untouched by rounds 1–2. | unchanged |
| **D3** | "Sample size on every row … The median trade count inside a disjoint third is **7–15**, which is why the replication column is weak evidence." | **STANDS** | untouched, and it is the report's most useful piece of self-discipline. | unchanged |
| **D4** | Mandatory statement 4: "The hourly files carry 11–12 months, which cannot support a transition matrix over **thirteen strategy groups** — the chronology test is reported on **daily** series only." | **WEAKENED** | **R6-M4**: the daily series cannot support thirteen either. The candidate set is **6 on MGC, 4 on MNQ, 3 on MES**, and three groups (VOLUME_PROFILE, OPENING_RANGE, LIQUIDITY) take **zero** daily trades for named implementation reasons (`D5`/`D-P1`, `D20`, `D23`). | "the hourly files cannot support a thirteen-group transition matrix, **and neither can the daily files: 3 of 13 groups cannot trade a daily bar at all, and only 6 / 4 / 3 groups clear the 24-month × 20-trade requirement on MGC / MNQ / MES.** The test is reported on daily series over that reduced universe" |
| **D5** | Mandatory statement 4 cont.: "MES/MNQ/NQ/ES are one index complex (D14/D41) … the grain CSVs splice contract months (D40) … Nested windows make window agreement arithmetic, not replication." | **STANDS, and a second reason exists for the first clause** | `R1-D4a c.3` adds that `profiles.groups_for` returns different group sets per symbol on a *default* sweep — not applicable here (§2.2), but it should be stated as a standing caveat. | unchanged |

## D.2 — Part A, the recurring top-10 list

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **D6** | "**The table is not meaningless, but it is worthless.** Out of sample it carries about **0.7 extra names out of ten** on the contaminated population, and on clean contracts that excess disappears." | **STANDS** | untouched. | unchanged |
| **D7** | A.1: "`rth_only=False` 13,171 OOS trades, realised **−0.0155R** against a **−0.0104R** no-edge null, excess **−0.0050R**. `rth_only=True`: excess 0.0000R." | **WEAKENED (scope statement only)** | `research/R3_path_operation.md:1700-1718`: every exit in the programme was **geometric** — `_manage` receives a `Bar`, never a `FeatureSnapshot` `[repo-verified: engine.py:377-378, snapshot built at :311 *after* the management loop]`, and **nothing under `futures_agents/backtest/` imports `futures_agents/risk/`** `[measured: grep → no matches]`. `run_portfolio` also does not net positions — it is a batch runner `[repo-verified: engine.py:554-559 → run_many]`. | the numbers stand. Add the scope sentence R3 supplies: "**this is a statement about signals run flat, one at a time, with geometric exits and no account layer.** Nineteen `AccountConfig` operating parameters sit on the far side of an import boundary from every number in this report" |
| **D8** | "**The single cleanest statement in the whole exercise:** at a 6-month lookback the selected top 10 **underperforms trading the entire qualifying universe**, in both arms — +0.022R against +0.057R, and −0.024R against +0.064R. *Selecting is worse than not selecting.*" | **STANDS** | nothing in rounds 1–2 touches it, and structurally nothing can: both arms are drawn from the **same** population, measured the same way, over the same bars. Every dead detector is in both arms or in neither. | unchanged. This is the strongest survivor in the corpus and should be cited in preference to any ranking table |
| **D9** | "MGC daily is negative at every lookback. **The top-ranked strategy changes in 58 of 70 walk-forward folds.**" | **STANDS** | untouched. | unchanged |
| **D10** | A.2: "**Controls reach the top 10 less often than chance** — 12.3 observed vs 18.6 null, z = −2.63 (`rth_only=False`); 13.6 vs 14.0, z = −0.21 (True). So the ranking does separate signal from noise — a little. `placebo_shift` leaks (D42) and the two honest kinds rank *worse* than uniform." | **STANDS, and I checked the mechanism that could have broken it** | I tested whether dead detectors give placebos an unfair edge and **they do not**: `placebo_random` matches the base's **raw signal count** — "every bar it would have fired on, position state ignored" — and `extract_signals` counts a signal only where "scope filters passed, **every FILTER condition passed**, the signals agreed on a direction" `[repo-verified: workspace/newstrats/placebo.py:49-72, 203-222, 289-313]`. So a base whose SIGNAL never fires *or* whose FILTER never passes has a raw count of zero and yields a **zero-trade placebo**. Dead detectors remove real and control symmetrically. | unchanged, and the symmetry should be stated: "because placebos are count-matched to the base's own raw signals and inherit its filters, a structurally zero-trade base produces a structurally zero-trade placebo — so the control cohort is not inflated by the dead-detector findings" |
| **D11** | A.3: "**Nested windows: no excess anywhere** (274d→180d 13 observed vs 17.2 forced by nesting). **Disjoint thirds: breaks on clean data** — overlap 15 against 16.9 by chance, sign z = −0.58, Jaccard **0.081**." | **STANDS** | untouched. | unchanged |
| **D12** | **A.4, the power control:** "A deliberate look-ahead cheat … ranks **1st in all four 274-day cells** … **The harness detects a signal that is really there. That licenses reading the null results above as real absence rather than an insensitive test.**" | **WEAKENED — and this is the most serious item in the whole audit** | the licence is granted to the wrong scope. A look-ahead cheat that fires like a normal strategy demonstrates that the **ranking and measurement pipeline discriminates among strategies that trade**. It demonstrates nothing about whether a strategy's **detector fired at all**, and the two failures are indistinguishable in the output: both produce a strategy that is absent from the top 10. Rounds 1–2 found **five** structurally zero-trade configurations (`research/R1_group_audit.md`, "Structurally zero-trade configurations found": `openinterest`; MULTI_TIMEFRAME at a frame's top tf; VOLUME_PROFILE at 240m; OPENING_RANGE at 1h on MGC; BREAKOUT + `volatility_expanding`) plus three degenerate ones (`D-MTF2`; `D-V1`; **R6-D1**), and **R6-M4** shows three whole strategy groups taking zero daily trades in this report's own chronology. None of those would have been caught by a power control, because the cheat is a *different strategy* and its firing rate says nothing about theirs. | "**The harness's ranking and measurement layer detects a signal that is really there. That licenses reading a null as real absence *for a strategy that traded*. It does not license reading a null as absence for a strategy, condition or group whose detector never fired — that requires a per-condition firing census on the same frame, which this study did not run.**" This is the sentence in the published corpus that most directly asserts "our nulls are results", and it is the exact sentence the audit's distinction breaks |
| **D13** | A.5: "Clean on **42,279 trades**: entry is the fill bar's *open* plus adverse slippage, **never a bar extreme**; **0 favourable-slippage fills**; 321 trades hit a target on their entry bar and in **0** was the stop also touched — the D35 shape is absent. Boundary look-ahead measured: 2.47% straddle an edge, requiring both ends inside moves the pooled figure by −0.004R." | **STANDS** | independently repo-checked: `entry = spec.round_to_tick(bar.open + sign * slip)` `[repo-verified: futures_agents/backtest/engine.py:355]`, and the engine's own header states every snapshot "contains no data from after bar *i*" `[repo-verified: engine.py:6]`. R1's 19-group audit introduced no new look-ahead and found the three in-repo look-ahead bugs already fixed. | unchanged. This is a model audit paragraph — it is the fill-model half of what `2026-09-24_ORB-and-ICT.md` C15 demands |
| **D14** | A.5: "**MCL is the cost-fragile contract, MGC is not.** Costs flip **8 of 183** MCL 60m rows and 3 of 37 MCL 240m rows from positive gross to negative net, against **1 of 259** for MGC." | **STANDS** | untouched. Worth noting MCL is also the one symbol where `opening_range_breakout` is alive at 1h and `StopKind.RANGE` is genuinely distinct on 34% of bars (`D-L1`, `D49`) — so MCL's rows are the *least* affected by the dead-detector findings of any symbol in the corpus. | unchanged, and MCL's relative immunity is worth stating as a per-symbol independence result |
| **D15** | A.6: "On the index complex the placebo result is far worse: best placebo ranked 1st in **12 of 16 cells**; **96 of 160 top-10 slots are placebos**; on **MES 30d/240m no real strategy appears in the top 10 at all**. Tag-blindness verified — relabelling random reals reproduces the analytic null to within 0.04." | **STANDS** | I specifically tested the hypothesis that the 240m result is a dead-detector artefact and **rejected it** — see `D10`: placebos are count-matched to the base's raw signals and inherit its filters, so a depleted 240m real population depletes the control population identically. The tag-blindness check already rules out a code cause. | unchanged. The 240m cells *are* the most detector-depleted in the corpus (`D-P1`, `D22`, `D24`, R6-D1's 20% sub-tick bands), but that depletion does not favour placebos |

## D.3 — Part B, the per-symbol framework

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **D16** | "**MCL — MOMENTUM** (66 observations, 97% positive, beat its control on both arms), 60m and 240m, strongest in the study, still not live-eligible; cost-fragile." | **WEAKENED (label)** | `D-M1`: `macd_directional` and `macd_hist_direction` are **one condition with two names** — identical `(triggered, direction)` on 5000/5000 bars in five cells — so the required `momentum` slot offered 5 choices, not 6. `D-M2`: **2 of the 6 are mean-reversion conditions whose direction rule is momentum's negation** (`rsi_extreme_reversal` LONG at RSI ≤ 30, `stoch_extreme` LONG at %K ≤ 20), firing on 8.0–13.9% and 35.3–40.6% of bars, and the combinator satisfies a required group with **any one** member `[repo-verified: futures_agents/strategies/library.py:212-285]`. | "**MCL's best-measuring group is MOMENTUM**, a group in which one condition is an exact duplicate of another and two of six are mean-reversion triggers — so an unknown share of those 66 observations are mean-reversion strategies filed under MOMENTUM." The verdict (not live-eligible) is unchanged |
| **D17** | "**MGC — VWAP, TREND, MOMENTUM, MULTI_TIMEFRAME** — all modestly above control, **60m only**." | **WEAKENED (three of the four labels; TREND survives clean)** | **TREND**: required groups `trend` and `structure`, both **CLEAN** (R1 Groups 12, 15) — this label stands, with `D-TR1`'s note that four of eight `trend` conditions fire on 86–96% of bars. **VWAP**: `D-VW1` — `above_vwap` neither tests above-VWAP nor is named for the SHORT it returns; **R6-D1** — 7.5% of MGC 60m bars have sub-tick band-1 half-width. **MOMENTUM**: `D-M1`/`D-M2` as D16. **MULTI_TIMEFRAME**: **R6-M2** — at 60m in `[60,240,1440]`, `mtf_strongly_aligned` ≡ `mtf_aligned` on 93.7% of bars. | the framework stands as a discretionary read; three of its four labels need the caveat attached. **TREND is the one entry in the whole per-symbol framework with a fully clean required layer** |
| **D18** | "**MGC at 240m is worse than its own placebo.**" | **STANDS, with a composition caveat** | the placebo symmetry (D10) means this is not a dead-detector artefact. But the 240m real population is missing VOLUME_PROFILE entirely (**R6-M2**: `prior_profile` None on 1348/1348 MGC 240m bars, all six conditions 0%), is missing REVERSAL (`D22`), is 2–12× smaller under `rth_only=True` (`D24`), and holds a degenerate `vwap` required slot on 20.0% of bars (**R6-D1**). | verdict unchanged; state the composition, because "MGC at 240m" names a narrower population than a reader would assume |
| **D19** | "**MES / MNQ** — nothing beat its own placebo, including TREND at 154 observations and 100% positive. Default to no trade." | **STANDS** | TREND's required groups are CLEAN, so this is a measured negative on a healthy detector. | unchanged |
| **D20** | "The one controlled positive anywhere in the index complex — **`require_alignment ≥ 0.5` on MES 240m**, +0.047R IS and +0.077R OOS against a random-veto control — **helps in 1 of 4 cells, in a cell found by looking at 4.**" | **STANDS** — and I checked the mechanism that would have broken it | new finding, reported because it *could* have invalidated this and does not: `StrategyFilters.require_alignment` calls **`snap.alignment()` with no argument** `[repo-verified: futures_agents/strategies/base.py:433-434]`, which `features.py:725-741` names as the exact defect that made `mtf_aligned` timeframe-blind. It is the **sixth** instance of R1's "accepts a timeframe, reads all of them" pattern and the one R1 did not find, because it is a `StrategyFilters` field rather than a condition. **But it is harmless here:** `FRAMES[240] = [240,1440]` and the harness filters `primary_tf == tf`, so the set of all timeframes and the set at-or-above 240 are the same set (§2, R6-M1). | unchanged. Record `require_alignment`'s no-arg call as a **forward hazard** for any study that trades other than the lowest timeframe of its frame |

## D.4 — Part C, chronological rotation

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **D21** | "**Answer: no detectable chaining.** The one suggestive pattern is on MGC and it does not survive correction." | **STANDS** | **R6-M4** shrinks the universe to 6/4/3 groups, which *lowers* the Bonferroni bar (MES 6 pairs → \|z\| ≥ 2.64), so the negative is obtained against a **less** stringent correction and is therefore safer, not weaker. | unchanged |
| **D22** | "**Method.** Every trade from every generated strategy counts once — **no floor on strategies and no ranking** — because selecting before measuring would bake in the persistence the test looks for." | **STANDS, and it is the right design** | untouched, and it is the reason `D21` survives: with no ranking, the dead-detector findings cannot select the population. | unchanged |
| **D23** | "**Persistence of the winner — nothing.** MGC 20/95 z=+0.49, MNQ 18/60 z=+1.00, MES 17/56 z=−0.37." | **STANDS — replicated exactly** | **R6-M4** reproduces 20/95, 17/56 and 18/60 from the committed ledgers using `analyse.py`'s own thresholds. | unchanged |
| **D24** | "Which groups win most often is only mildly symbol-specific, and **the same three groups top all three symbols** (MULTI_TIMEFRAME, VWAP, MOMENTUM) — **shared structure, not a per-symbol signature.**" | **INVALID — measured nothing** (sub-kinds **ZERO-FIRE** + **DEGENERATE**) | **R6-M4.** On **MES those three groups are the entire candidate set** — 3 of 13 groups clear the 24-month × 20-trade requirement, so no other group *can* top MES. On MNQ the set is 4, on MGC 6. The shared "top three" is a shared **candidate set**, and the candidate set is small because of the detector layer: VOLUME_PROFILE, OPENING_RANGE and LIQUIDITY take **zero** daily trades (`D5`/`D-P1` measured at 0 fires on 2511 MGC and 1859 MES daily snapshots; `D20`; `D23`). And one of the three "winners" is degenerate at daily: **R6-D1** — `above_vwap` fires on 92.4% (MGC) and 99.7% (MES) of daily bars, its direction equals `candle_close_strength`'s on 1092/1092 and 919/919 co-firings, `vwap_band_extension` fires on 99.8–100.0%, and `vwap_band1_bounce` fires **0 times**. | "**On MES the three groups that top the table are the only three groups in the table.** The candidate set is 6 / 4 / 3 groups on MGC / MNQ / MES, three of the thirteen cannot trade a daily bar at all, and **'VWAP' at daily frequency is a close-location predicate** — the session-anchored band has no width when each bar is its own session. The overlap across symbols is a shared candidate set produced by the library's daily detector coverage, not evidence of shared market structure" |
| **D25** | "**Own-group autocorrelation — weak, positive, uncorrected.** Strongest are all on MGC (TREND r=+0.383 on n=25, MULTI_TIMEFRAME r=+0.249, VWAP r=+0.165 on 106 months). None reaches \|z\|=1.96 and there are 18 of them, so **zero survive any correction.**" | **STANDS** | verdict untouched. The VWAP row is about a close-location predicate at daily (**R6-D1**) and the MULTI_TIMEFRAME row about a group whose two signals are the same function at daily (**R6-M2**: identical on 2511/2511 and 1859/1859) — but the conclusion is negative either way. | verdict unchanged; relabel the VWAP and MULTI_TIMEFRAME rows |
| **D26** | "**Cross-lag — the direct test, and it fails.** 0 surviving pairs on every symbol (MGC 20 pairs, \|z\| ≥ 3.02; MNQ 12 pairs, 2.87; MES 6 pairs, 2.64). Largest: **VWAP(t) → TREND(t+1) r=+0.528, n=25, z=+2.75**." | **STANDS in verdict; the "closest the hypothesis comes to being true" framing WEAKENED** | the pair counts 20/12/6 are themselves the evidence for **R6-M4** (`k(k−1)`: 6=3×2, 12=4×3). The leading effect's antecedent leg, "VWAP", is a bar-shape group at daily (**R6-D1**), so the near-miss reads "a good close-location month predicts a good trend month", which is co-movement of two bar-shape reads rather than a handover between methodologies. | "0 surviving pairs, **over a universe of 6 / 4 / 3 groups rather than thirteen**. The largest near-miss has a degenerate antecedent and should not be described as the closest the hypothesis comes to being true" |
| **D27** | "**It is not a rotation:** all four leading effects are *positive*, so a good VWAP month predicts a good TREND month rather than a handover. That is co-movement, groups rising and falling together, which is what an underlying regime driving everything would produce." | **STANDS, and rounds 1–2 offer a cheaper explanation than a regime** | `D-VW2`/**R6-D1** plus R1 finding C-1: at daily, `above_vwap` and `candle_close_strength` and `delta_confirms_bar` are **the same CLV arithmetic in three different condition groups** (`vwap`, `candlestick`, `orderflow`), and `vwap_band_extension` also reduces to `close ≥ (H+L+C)/3` on a zero-width band. Groups that share arithmetic co-move by construction. | "co-movement, **and at daily frequency several of these groups share arithmetic** — `above_vwap`, `candle_close_strength` and `delta_confirms_bar` are one predicate in three groups — so co-movement does not require a common regime to explain it" |
| **D28** | "even had a chain been found, it would describe what already happened. Acting on it requires knowing which group leads *before* the month it leads in." | **STANDS** | untouched. | unchanged |

## D.5 — Net

| # | claim | status | finding | honest restatement |
|---|---|---|---|---|
| **D29** | Net: "the ranking separates signal from noise a little (controls below chance at z = −2.63), but there is **no out-of-sample name persistence**, **nothing clears deflation**, and **the realised expectancy of acting on the list is negative and worse than trading the whole qualifying universe**." | **STANDS** | every clause survives: D8, D10, D11, D1's wording fix. | unchanged |
| **D30** | Net: "**There is no chronological chain on any symbol.**" | **WEAKENED (scope)** | **R6-M4**: the test covered 6 / 4 / 3 groups. | "**There is no chronological chain among the strategy groups that can trade a daily bar** — 6 on MGC, 4 on MNQ, 3 on MES. Three of the thirteen were untestable at daily for implementation reasons, so the statement is not yet 'no chain among the thirteen'" |
| **D31** | "**Live eligibility: unchanged, and firmer.** Nothing in this library should be traded as a system." | **STANDS** | nothing in rounds 1–2 weakens it, and the dead-detector findings mean *less* was searched than claimed, which cannot create eligibility. | unchanged |
| **D32** | "Known-broken machinery is catalogued in `DEFECTS.md` (D1–D43); D21, D24, D36, D37, D38, D39 and D40 are open at the time of this report." | **STANDS, count superseded** | now D1–D49 plus four unnumbered R3 items `[research/R3_path_operation.md:25]`; D44–D49 added in round 2. | update the range |
| **D33** | "The eight measured operating rules … are carried in **`CALLOUT.md`**, which is the operating brief for the live-callout session." | **WEAKENED — and it propagates outside `scan_reports/`** | rule 2 ("multi-timeframe agreement is not a virtue") is weakened by B13/`D-MTF2`/`D-MTF3` and R1's own "still an open question, not a settled negative"; rule 6 ("no hours filter improves expectancy") survives but its `avoid_lunch` evidence does not, on MGC (B17/`D-T1`); rule 8's ORB half **stands** (C2); rules 1, 3, 4, 5, 7 stand. | the pointer stands. **`CALLOUT.md` carries two rules that need the same amendments as `BRIEF.md` rules 2 and 6** — flagged for the parent, since `CALLOUT.md` is outside `scan_reports/` and outside my ownership |

**Report D counts:**
**STANDS 24** (D2, D3, D5, D6, D8, D9, D10, D11, D13, D14, D15, D18, D19, D20, D21, D22, D23, D25,
D26, D27, D28, D29, D31, D32) ·
**WEAKENED 8** (D1, D4, D7, D12, D16, D17, D30, D33) ·
**INVALID 1** (D24) · **UNAFFECTED 0** · **total 33**.

`D25` and `D26` are split verdicts counted as STANDS: in both, the negative conclusion survives
intact and only the *framing* of a near-miss row needs relabelling. `D32` is STANDS with a stale
count. The one invalidation is the only claim in the corpus that is **both** ZERO-FIRE (three groups
took no daily trades) and DEGENERATE (one of the three "winners" is a bar-shape group at daily).

---

# 5. Cross-report totals

| report | STANDS | WEAKENED | INVALID | UNAFFECTED | claims audited |
|---|---|---|---|---|---|
| **A** `2026-09-23_MGC-MES-NQ_deep-scan.md` | 10 | 10 | **3** | 1 | 24 |
| **B** `2026-09-24_strategy-studies_21-study-programme.md` | 17 | 10 | **2** | 0 | 29 |
| **C** `2026-09-24_ORB-and-ICT.md` | 13 | 5 | **0** | 0 | 18 |
| **D** `2026-09-24_MGC-MCL_ranking-persistence-and-chronology.md` | 24 | 8 | **1** | 0 | 33 |
| **total** | **64** | **33** | **6** | **1** | **104** |

**62% of audited claims stand, 32% need a restatement, 6% are invalid as published.** The six
invalidations, by sub-kind:

| # | claim | sub-kind | one line |
|---|---|---|---|
| **A11** | NQ's second-best group is OPENING_RANGE (18 strategies, +0.070, 66.7% profitable) | SUBSTITUTED | the template drew another `liquidity` condition; no opening range exists at 1h on NQ |
| **A16** | the two daily VWAP rows in the per-timeframe table | DEGENERATE | at 1440m the session band has no width; `above_vwap` is `close > (H+L+C)/3` |
| **A18** | NQ 1h OPENING_RANGE positive across all three windows | SUBSTITUTED | already retracted by Report B; rounds 1–2 supply `features.py:865` and extend it to MGC/MES |
| **B13** | "Unanimity versus majority: no detectable difference" | DEGENERATE | the two conditions are the same function on 100% of 240m and 1440m bars |
| **B17** | "The lunch-hour folk claim is refuted" (`avoid_lunch` hurts, z = −3.25) | DEGENERATE | on MGC the condition vetoes the **final 90 minutes of the pit session**, not lunch |
| **D24** | "the same three groups top all three symbols — shared structure, not a per-symbol signature" | ZERO-FIRE + DEGENERATE | on MES those three are the **only** three groups in the test; 3 of 13 take zero daily trades |

**No invalidation reverses a sign, a verdict or the deflation conclusion.** All six are misattributed
objects: a real number filed under the wrong heading, or a comparison between two things that are
arithmetically one thing.

---

# 6. The single most serious item

**`D12` — Report D §A.4's power-control licence. It is graded `WEAKENED`, and it is still the most
serious thing in this audit.**

> "A deliberate look-ahead cheat … ranks **1st in all four 274-day cells** … **The harness detects a
> signal that is really there. That licenses reading the null results above as real absence rather
> than an insensitive test.**"

**Why it is the most serious.** It is the only sentence in the published corpus that grants the
programme permission to read its nulls as results. Every other null in all four reports inherits it
by implication. If the licence is over-broad, an unknown number of nulls across 104 claims are not
results — and the audit cannot say which, because the reports do not record firing rates.

**Why it is `WEAKENED` and not `INVALID`.** The power control is real and it works. A cheat entry
ranking 1st in 4 of 4 cells, and a second cheat ranking 1 of 147 / 1 of 106 / 1 of 21 / 1 of 24, does
establish that the **ranking and measurement layer** discriminates. The defect is the scope of the
inference, not the experiment. Over-retracting here would throw away a genuinely good control.

**What breaks it.** A look-ahead cheat is a *different strategy* that fires normally. Its firing rate
carries no information about whether any other strategy's detector fired, and the two failures are
indistinguishable in the output — a strategy absent from the top 10 could be absent because it was
measured and lost, or because it never traded. Rounds 1–2 then supplied the counterexamples:

- **five structurally zero-trade configurations** — `openinterest` (a FILTER that never passes vetoes
  every entry); MULTI_TIMEFRAME at a frame's top timeframe; VOLUME_PROFILE at 240m; OPENING_RANGE at
  1h on MGC; BREAKOUT + `volatility_expanding`
  `[research/R1_group_audit.md`, "Structurally zero-trade configurations found"]`;
- **three degenerate ones** — `mtf_strongly_aligned` ≡ `mtf_aligned` (`D-MTF2`, and **R6-M2** measures
  it at 100% on the published 240m and 1440m frames); `volatility_compressed` reading a field its
  description does not name (`D-V1`); and **R6-D1**, the `vwap` group at daily;
- **three whole strategy groups taking zero daily trades in this very report's own chronology**
  (**R6-M4**): VOLUME_PROFILE, OPENING_RANGE, LIQUIDITY.

**The restatement.**

> The harness's ranking and measurement layer detects a signal that is really there. That licenses
> reading a null as real absence **for a strategy that traded**. It does not license reading a null as
> absence for a strategy, condition or group whose detector never fired — and distinguishing the two
> requires a per-condition firing census on the same frame, which this study did not run.

**Most serious outright invalidation: `D24`**, because it is the only claim in the corpus that is both
ZERO-FIRE and DEGENERATE at once, because its evidence contradicts its own prose (the cross-lag pair
counts 20/12/6 *are* `k(k−1)` for 6/4/3 groups), and because it is a positive structural claim —
"shared structure" — rather than a null.

---

# 7. What survives everything

This list matters as much as the retractions, and it is longer.

**The programme's verdict is untouched, in every one of its forms.** A1, B1, B2, B3, D1, D2, D29,
D31. Nothing is live-eligible; nothing clears its own multiple-testing threshold; the largest t
anywhere is 3.923. Every dead-detector finding removes candidates from the set that *could* have
cleared, which can only make the null safer. **Only the denominator's wording changes**
(`BRIEF.md:230-244`): "generated", not "tested", and quote 5.46 with its 495k / 5.15 companion.

**The nine claims I would put weight on, in order:**

1. **D8 — "Selecting is worse than not selecting."** +0.022R against +0.057R and −0.024R against
   +0.064R at a 6-month lookback. **Structurally immune to this entire audit**: both arms are drawn
   from the same population, measured the same way, over the same bars, so every dead detector is in
   both arms or in neither. Cite this in preference to any ranking table.
2. **D13 — the fill and cost audit.** 42,279 trades; entry is the fill bar's *open* plus adverse
   slippage `[repo-verified: engine.py:355]`; **0 favourable-slippage fills**; the `D35` one-sided
   fill shape absent; boundary look-ahead **measured** at 2.47% and worth −0.004R. This is the
   fill-model half of C15 actually executed.
3. **C2 — ORB does not pay.** Measured on a purpose-built module that enforces the resolvability
   rule and counts inert cells `[repo-verified: workspace/newstrats/orb.py:174-183, 47, 118]`, at
   **tf ∈ {5, 15} only** — exactly where an opening range can be built. `D-L1` corroborates it.
4. **C5 — the sweep→shift→retrace sequence is real, common and worthless.** 77–106 completions per
   symbol, 57–68 trades per cell, and the Mantel-Haenszel OR collapses to 1.08 / 0.86 at matched
   distance. A healthy population that failed on its merits: the corpus's best "we measured absence".
5. **C15 — "Resampling cannot detect a bias whose sign is always favourable. Only auditing the fill
   model can."** Vindicated and generalised by rounds 1–2, which did the same thing to the *signal*
   model and found eight more cases. The generalised form is the one-line statement of this audit.
6. **A20 — the deep scan's limitation 0c.** "Every 'VOLUME_PROFILE absent at 4h/1d' reading in this
   report is an implementation gate, not a market fact." The corpus made the audit's own distinction,
   correctly, once, in 2026-09-23. **R6-M2** reproduces it at 1348/1348, 1347/1347, 2511/2511 and
   1859/1859. It should be the model for every other absence in the corpus.
7. **B24 — the `break_of_structure` retraction.** `structure` is **CLEAN** (R1 Group 12) and
   `break_of_structure` fires on 31.4–37.2% of bars, so a healthy detector failed out of sample.
   A model retraction.
8. **B5 — turn `exit_at_session_close` off.** Paired sign z = +3.52, and it is one of the very few
   survivors that is *about* a layer the programme actually varied — every exit was geometric and a
   session boundary is geometry (`research/R3_path_operation.md:1700-1706`).
9. **B9 — do not fade extension on the bar spanning the cash open, at 60m.** z = −10.64 per-strategy,
   reversing at 15m. Rounds 1–2 supply a candidate mechanism for the reversal (the 60m grid does not
   contain any contract's RTH open on a boundary except MCL's) without touching the result.

**Also standing, unqualified:** the "groups that cannot be evaluated as built" table in full (B18a–f,
four of six independently confirmed by R1's own group audit); the seven group-alias filters (B19);
cross-symbol comparison being impossible (B20, now for two reasons); cost under-charging on
multi-target exits (B21); the 20-trade floor's exit-geometry bias (A21); clone collapsing (A6, which
silently absorbed `D-M1`); the sub-hourly graveyard (A4); the look-ahead discipline (A8); MCL's
cost-fragility against MGC's (D14); the placebo cohort results (D10, D15 — I tested the dead-detector
explanation for these and **rejected** it); and the chronology's no-chaining verdict (D21, D23, D26,
replicated exactly by **R6-M4**).

**`BRIEF.md`'s eight rules:** 1, 3, 4, 5, 7 stand; **8's ORB half stands** (C2) and its ICT half
stands (C3–C5); **2 needs amendment** ("multi-timeframe agreement is not a virtue" → still an open
question in this implementation, per B13 and R1 Group 9's own verdict); **6 stands but its
`avoid_lunch` evidence does not, on MGC** (B17). `CALLOUT.md` carries the same eight and needs the
same two amendments — outside `scan_reports/` and outside my ownership, flagged for the parent.

---

# 8. Anti-overfitting checks on this audit itself

The mandate applies to my own work.

| risk | how I checked | what I found |
|---|---|---|
| **over-retraction** | every status defaults to `STANDS` unless I can name a finding and a path. I graded the corpus's most load-bearing sentence `WEAKENED` rather than `INVALID` (§6), kept a report at zero invalidations (C), and wrote §2 *before* the retractions | 64 STANDS against 6 INVALID. Four round-1/2 findings turned out to have **zero** published blast radius and are recorded as such (§2) |
| **under-retraction** | I read all four reports in full and audited every numbered claim, limitation, constraint and recommendation, not only the headlines | 104 claims; the 6 invalidations include one (D24) that no round-1/2 file had noticed |
| **manufacturing a contradiction from a definitional difference** | **this nearly happened.** My first recomputation of the chronology's monthly winners used "argmax over all groups present" and returned a top-3 that contradicted the published one on all three symbols. Before writing it up I read `workspace/chrono/analyse.py:28-29, 71-86` and re-ran with **its** thresholds (`MIN_TRADES=20`, `MIN_MONTHS=24`, ≥3 candidates) | the contradiction **vanished** — my replication then matched 20/95, 17/56, 18/60 exactly. The real finding (the 6/4/3 universe) only became visible *because* I replicated faithfully first. Recorded because it is exactly the failure the `BRIEF.md` timezone-trap note warns about |
| **look-ahead / future data in my own measurements** | every census uses `frame.snapshot(i)`, the same path the backtest uses, evaluated at bar *i*; `engine.py:6` states the snapshot contains no data after *i* | clean. No measurement of mine reads a later bar |
| **repainting / detector provenance** | I verified the load-bearing repo facts myself rather than inheriting them: `combinator.py:201-211`, `features.py:865`, `engine.py:377-378`, `engine.py:311` ordering, the absent `risk/` import, `base.py:433-434`, `scout.FRAMES`, and all three harnesses' `primary_tf == tf` | R1 confirmed on every point I checked except one, where R1 was right and **R3 was wrong** (R6-M3) |
| **insufficient sample in my own censuses** | 5,000 bars per 60m cell, 1,347–1,384 per 240m cell, 1,859–2,511 per daily cell, four contracts, per-symbol and per-timeframe throughout | nothing pooled across symbols or timeframes; every table is per-cell |
| **per-symbol independence** | every measurement is reported per contract. MCL is the one symbol where `opening_range_breakout` is alive at 1h and `StopKind.RANGE` is distinct; MGC is the one where `avoid_lunch` is inverted; MNQ is the worst affected by `D-P2` | **four of my findings are symbol-specific and I state them as separate facts** |
| **data-mining bias / multiple comparisons** | **no expectancy, no z, no t, no P&L is computed anywhere in this file.** Every number of mine is a firing rate, an availability count, a band width, or a replication of a published statistic. Nothing was selected on outcome | not applicable by construction. The one place I *could* have mined — picking which claims to audit — is neutralised by auditing all of them |
| **unrealistic fills / understated costs** | not applicable: **no trade is simulated anywhere in this file**, and no backtest, sweep or expectancy was run, per the dispatch | n/a |
| **survivorship in the audit's own selection** | I audited all 104 claims including every one that came back `STANDS`, and §7 is as long as §5 | the STANDS list is reportable because it was not selected |
| **`D48` (id collision)** | not applicable — I created no `Strategy` and called no `dataclasses.replace` | n/a |
| **`csv/` integrity** | every access is `load_csv(...)` read-only; no write, delete or `chattr` anywhere | `csv/` untouched |

**The limitation I cannot remove.** This audit answers "is the published claim about the object it
names". It does **not** answer "would the claim have been different with working detectors" — that
needs re-measurement, which is outside my dispatch. Six invalidations are therefore six claims to
restate, not six results reversed, and the honest position on each restated claim is **untested**,
not *refuted*.

---

# 9. For the parent session — what to apply, in priority order

1. **Report D §A.4** — replace the power-control licence sentence with §6's restatement. Highest
   priority: every other null in the corpus inherits it.
2. **Report D Part C** — "thirteen strategy groups" → the 6/4/3 universe, and "the same three groups
   top all three symbols" → on MES those three are the only three (R6-M4).
3. **Report B** — the `avoid_lunch` refutation (B17) and the "unanimity versus majority" sentence
   (B13) are the two outright retractions. B6 (`D45`/`D49`/`MGR-T17`) and B10 (`volatility_normal` on
   the frame's regime timeframe) are the two most consequential weakenings.
4. **Report A** — the NQ OPENING_RANGE best-group row (A11) and the two daily VWAP rows (A16).
   A18 is already retracted in Report B and only needs the mechanism and the per-symbol split added.
5. **Report C** — add the scope sentence to C2 (measured on `orb.py` at 5m/15m, not on the library
   condition), the CFD disclosure to the scope header (C18), and generalise C15 from the fill model
   to the model.
6. **Every report** — the deflation wording, per `BRIEF.md:230-244`. Four reports, one sentence each.
7. **`CALLOUT.md`** (outside `scan_reports/`) — rules 2 and 6 need the same amendments as
   `BRIEF.md`'s.
8. **Two new forward hazards for `DEFECTS.md`**, neither of which needs a retraction, both of which
   need a `D<n>` from the manager:
   - `StrategyFilters.require_alignment` calls `snap.alignment()` **with no argument**
     `[repo-verified: futures_agents/strategies/base.py:433-434]` — the sixth instance of R1's
     timeframe-inert pattern and the only one outside `library.py`. Harmless in every published cell
     (§2) and live the moment a study trades other than the lowest timeframe of its frame.
   - **R6-D1**: the session-anchored VWAP band has **sub-tick width on 100% of daily bars**, so the
     `vwap` group is a close-location group at 1440m. This is `D45`'s mechanism at its limit and
     `D45`'s current statement ("6–34% of bars") understates it.
9. **One correction to a research file I do not own** — R3's `csv/raw` 1h grid count is wrong (R6-M3);
   posted as `msgs/R6-01_R3_csv-1h-grid-discrepancy.md` rather than edited.

**Nothing in `scan_reports/` was edited by me.** `csv/` untouched. No commit, no push, no backtest,
no sweep, no expectancy.
