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


