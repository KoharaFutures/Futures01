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

