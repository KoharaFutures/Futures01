# AVENUES — the discovery ledger

**Owner:** discovery (`OWNERSHIP.md`). **Read in full before every burst; appended to before every
burst finishes** (`PIPELINE.md` §1). Every avenue carries a verdict. An avenue with no verdict is
a bug in this file.

| verdict | meaning | may a later burst revisit? |
|---|---|---|
| `CLOSED-EMPTY` | explored, nothing there | **no** — not without a new reason, stated |
| `CLOSED-FOUND` | explored, produced a main task | no — the main task carries it now |
| `OPEN-PARTIAL` | explored to a stated depth, more remains | yes, **from the recorded stopping point** |
| `DEFERRED` | out of reach for a named reason | only if that reason changes |

## Seeded from

Burst 01, 2026-09-27. Sources read in full or skimmed to headline as noted:
`DIVISION.md` §1 + Appendix A/B (53 families, three mechanism classes); `BRIEF.md`;
`PIPELINE.md`; `scan_reports/README.md` and the headline + conclusion of all four reports;
`workspace/studies/{RANKING,STRUCTURE,ORB_ICT}_FINDINGS.md` and `DEFECTS.md` headings;
`workspace/chrono/FINDINGS.md` via the report that carries it;
`workspace/roundtable/research/R1_flow_auction.md` as it stood at 2026-09-27 01:23
(the phantom-condition-groups headline only — R1 is writing live);
`workspace/roundtable/OPEN_QUESTIONS.md` (Q1–Q3, all from R1).
**No `R2_*` or `R3_*` file existed at read time**
`[measured: ls workspace/roundtable/research/ → R1_flow_auction.md only]`.

## The test I applied for "closed"

This is the load-bearing judgement in the file, so the rule is written down rather than left to
taste. An avenue is `CLOSED-EMPTY` only if **both** hold:

1. a study **in this repo measured the avenue itself**, and
2. it measured **the thing, not a broken detector for the thing.**

Condition 2 disqualifies a lot. This repo has repeatedly found that an apparently-null family was
a null *detector*: the LIQUIDITY sweep side was read as "the idea fails" when in fact
`session_extreme_sweep` compares a bar against a session high that includes that bar and so can
never fire; SUPPLY_DEMAND's emptiness was its own ATR-gated base definition; the shipped ORB
condition had no first-break gate and no session gate. `[repo-verified:
scan_reports/2026-09-24_ORB-and-ICT.md:92-117]` So "0 strategies reached 20 trades" is evidence
about the library, not about the family.

**A family the manager listed in a taxonomy and nobody investigated is `OPEN-PARTIAL` with a
stopping point of "named only".** Marking those `CLOSED` would make this ledger lie in the
direction of never looking again, which is the one failure it exists to prevent.

`DEFERRED` is used when the avenue cannot be *measured here* without acquiring a data object or
building a primitive **that I can name**. Where a named blocker could plausibly change — Yahoo is
reachable as of 2026-09-27 (`BRIEF.md`, corrected), so a second series is now purchasable with a
fetch — the change-condition is written into the row. A `DEFERRED` row with a vague blocker is a
complaint; a `DEFERRED` row with a named primitive is a build-and-acquire order.

## A note on in-flight work

Round-1 researchers R1/R2/R3 are writing `research/R{1,2,3}_*.md` **as this ledger is being
written**. Rows below say `IN FLIGHT (R<n>)` where a round-1 deliverable is assigned to the
avenue. That is a *claim on the avenue*, not a verdict — a later burst must re-read those files
before treating any such row as advanced past its recorded stopping point.

---

## Class I — participant and auction information (needs to see who is transacting)

Shared blocker for this class, measured once here and cited by row rather than repeated:
all 48 files under `csv/raw/` carry the header `open_time,open,high,low,close,volume`
— no bid/ask split, no open interest, no contract month, no settlement price — and **1 minute is
the finest bar available; no tick data, no time-and-sales, no depth**
`[repo-verified: DIVISION.md Appendix B #1, #2, itself marked measured]`. The 29 JSONL series in
`data/archive/` are the same six fields
`[measured: ls data/archive/ → 29 files, {CL,MCL,MES,MGC,MNQ} × {1,5,15,30,60,240,1440}m]`.
Call this **BLOCK-SUBBAR**.

| id | avenue | verdict | reason / stopping point / blocker |
|---|---|---|---|
| I-1 | Order flow / footprint reading (bid-ask footprint, stacked imbalances, delta at extremes) | `DEFERRED` | **Blocker: no per-trade aggressor flag.** BLOCK-SUBBAR. `Bar.bid_volume`/`ask_volume` are `Optional=None` and `Bar.delta` falls back to a close-location proxy on every bar of every file `[repo-verified: research/R1_flow_auction.md → data/bars.py:44-45,91-104]`. The family is **untested here**, not refuted — what was tested is Chaikin A/D. Change-condition: a tape/aggressor source. Operating-knowledge half IN FLIGHT (R1-D2). |
| I-2 | Absorption and stopping volume | `DEFERRED` | **Blocker: same, and worse than generic.** R1 established the proxy returns `0.0` when bar range is zero — i.e. exactly the absorption case, where true delta is at its maximum `[repo-verified: research/R1_flow_auction.md → data/bars.py:111]`. So even a degraded version is sign-blind in the family's central setup. Do not proxy this one. |
| I-3 | Iceberg / hidden size detection; passive size discovery | `DEFERRED` | **Blocker: no order-level or queue data.** `[measured: grep -ril "iceberg" workspace futures_agents scan_reports research docs desk reports scripts (excl. roundtable) → 0 files]`. Never mentioned in this repo outside the taxonomy. |
| I-4 | DOM and book pressure; spoof-and-go; queue-position scalping | `DEFERRED` | **Blocker: no L2 depth snapshot, at any frequency.** BLOCK-SUBBAR. |
| I-5 | Market making / liquidity provision / spread capture | `DEFERRED` | **Blocker: no queue position and no passive-fill model.** Whether `futures_agents/backtest/costs.py` can even express a maker fill or rebate is **unverified by me** (R3's code surface per `DIVISION.md` §"Primary code surface"). Logged as a lead, not a claim. |
| I-6 | Tape scalping (aggressive, sub-minute, size-driven) | `DEFERRED` | **Blocker: sub-minute horizon; 1m is the finest bar in either store.** BLOCK-SUBBAR. |
| I-7 | Market profile / TPO: day types and opening types | `OPEN-PARTIAL` | **Stopping point: named only on the TPO side.** `[measured: grep -ril "TPO" … → 0 files]`; "market profile" appears in `coverage.py`, `library.py` and four `research/confluence/*.md` docs but as a label, not a study. The manager pre-registered that this dissolves into post-hoc labelling like "Power of Three" (`DIVISION.md` §6) — **that prediction has not been tested.** IN FLIGHT (R1-D2). |
| I-8 | Auction market theory: initiative vs responsive, excess, poor high/low, single prints, value migration | `OPEN-PARTIAL` | **Stopping point: named only.** `[measured: "poor high" → 0 files, "naked poc" → 0, "value migration" → 0; "initiative"/"responsive" → only `indicators/structure.py` + `library.py` as prose]`. No object in the library represents excess, a single print, or a value shift. |
| I-9 | Volume profile: POC / VAH / VAL / HVN / LVN, composite vs session, naked POC | `OPEN-PARTIAL` | **Stopping point: measured at group level only, with a known confound.** VOLUME_PROFILE was scanned and is "one condition wearing six names — 100% of floor-clearing strategies carry `value_area_breakout`, which fires on ~51% of bars… cannot trade at 4h at all" `[repo-verified: scan_reports/2026-09-24_strategy-studies_21-study-programme.md:105-118]`. The confound: each bar's volume is spread **uniformly** across every price bin its range touches `[repo-verified: research/R1_flow_auction.md → indicators/volume.py:225-232]`, and that approximation is flagged by no field. Composite (multi-session) profile, naked POC and HVN/LVN as distinct objects: named only. |
| I-10 | VWAP as institutional benchmark; TWAP; anchored VWAP; execution-algo footprints | `OPEN-PARTIAL` | **Stopping point: session VWAP measured; anchored VWAP built, tested, and never wired to a strategy; TWAP absent.** VWAP is one of the 13 strategy groups and is among the three that top all three symbols in the chronology study `[repo-verified: scan_reports/2026-09-24_MGC-MCL_…:164-200]`. But `indicators/volume.py:25-26` exports `AnchorVWAP`, `build_anchor_vwap`, `major_move_anchors`, `swing_anchors`, `anchored_vwap`, with a dedicated test file, and **no condition, feature snapshot or backtest reads any of them** `[measured: grep -rn "build_anchor_vwap\|swing_anchors\|major_move_anchors\|AnchorVWAP\|anchored_vwap" --include=*.py . (excl. __pycache__, indicators/volume.py) → only tests/test_anchored_vwap.py and indicators/__init__.py:19,40]`. `[measured: "TWAP" → 0 files]`. **LEAD-01, see MAIN_TASKS.md.** IN FLIGHT (R1, `DIVISION.md` §5.3 gives R1 anchored VWAP). |
| I-11 | Liquidity mapping and stop-run harvesting (session / PDH / PDL / ONH / ONL); relative-liquidity models | `OPEN-PARTIAL` | **Stopping point: one sequence tested and null; the map never built.** The ICT sweep→shift→retrace sequence was tested with a bespoke detector and "is real, common, and adds nothing over its parts"; ablation showed no stage adds anything and the **wrong order trades the same and ranks first** `[repo-verified: scan_reports/2026-09-24_ORB-and-ICT.md:11-27; workspace/studies/ORB_ICT_FINDINGS.md:173-237]`. But the library's own sweep side was **never testable** — 156 rule sets with ≥1 trade, 0 with ≥20, every cell every symbol — and `session_extreme_sweep` is arithmetically degenerate `[repo-verified: 21-study-programme.md:105-118; ORB-and-ICT.md:92-117]`. A *relative-liquidity model* (a ranked map of resting-liquidity levels, rather than one sweep flag) does not exist in any form here. |
| I-12 | Alternative bar sampling: tick, volume, range, dollar, imbalance and run bars | `CLOSED-FOUND` | **Burst 01 Part B. Carried by MAIN-01 in `MAIN_TASKS.md`.** Genuinely unexplored: `[measured: grep -rn "tick_bar\|volume_bar\|dollar_bar\|range_bar\|renko\|constant.volume\|bar_type\|BarType" futures_agents/ --include=*.py (excl. __pycache__) → no matches]`; `[measured: "tick bar" → 0 files, "dollar bar" → 0]`. Three of the six schemes need nothing this repo lacks. Do not re-explore; extend MAIN-01. |
| I-13 | Cumulative-delta divergence; footprint shape (P / b distributions) | `DEFERRED` | **Blocker: aggressor flag (CVD half) and within-bar volume-at-price (shape half).** The condition named `delta_divergence` is **not** CVD divergence — it compares a 20-bar price high against a 20-bar Chaikin A/D high and fires on upper-wick rejection at a range extreme `[repo-verified: research/R1_flow_auction.md → indicators/volume.py:144-170, library.py:469-478]`. That real price-action pattern **is** in scans; the family as named is not. |
| I-14 | Block and large-print detection; time-and-sales filtering | `DEFERRED` | **Blocker: no time-and-sales.** BLOCK-SUBBAR. The finest per-bar size information is one aggregate `volume` per minute. |
| I-15 | Opening auction and settlement-window behaviour; MOC-imbalance analogues | `OPEN-PARTIAL` | **Stopping point: one prohibition measured, the auction objects absent.** "No intraday entries 15:00–16:00 ET (z = −4.43, median −0.617R, replicated)" `[repo-verified: BRIEF.md rule 5]` is in fact a settlement-window result that nobody labelled as one — worth stating, because the settled rule is currently filed as a time-of-day quirk. No settlement price and no imbalance feed exist `[DIVISION.md Appendix B #1]`, so the auction mechanism behind the prohibition is unexplained. |

---

## Class II — a second observable (needs something other than this contract's own path)

Two shared blockers, cited by row rather than repeated:

- **BLOCK-ONEFRAME.** `futures_agents/backtest/engine.py:548` and `:554` each take one
  `frame: SymbolFrame`; one backtest sees one symbol `[repo-verified: DIVISION.md Appendix B #5]`.
  This blocks *trading* a relational signal. It does **not** block *measuring* whether a relational
  signal exists, which is an offline computation on two CSVs. Several rows below turn on that
  distinction and the manager's §6 pre-registration ("the expressibility verdict for most of Class
  II is trivially no… the risk is R2 delivers that and stops") is the reason to keep it sharp.
- **BLOCK-NOSECONDEXPIRY.** No contract-month label, no second expiry, no settlement price, no
  open interest in any file `[repo-verified: DIVISION.md Appendix B #1]`. The only place a roll is
  visible in this data is the spliced grain CSVs, which is defect **D40**, not a feature.

And one shared *un*-blocker that an earlier brief denied and that changes several rows:
**Yahoo is reachable** (`futures_agents/data/yahoo.py`, 157k bars pulled 2026-09-26)
`[repo-verified: BRIEF.md, correction dated 2026-09-27]`. So "we have no series for X" is now a
*purchase order*, subject to the vendor caveats BRIEF lists (hard lookback caps, no native 3m/4h,
MCL has no daily, `MNQ=F` ≠ `MNQ1!`).

**What is actually on disk, since three rows below depend on it:**
`[measured: ls csv/raw/ → 48 files over ES MCL MES MGC MNQ MZC MZS MZW NQ QQQ SPY; SPY and QQQ
each have 1d + 1h + 5m]`. There *are* two simultaneously-observable series for the index complex
at intraday resolution (SPY/QQQ ETF vs MES/MNQ futures) and for energy at daily
(`data/archive/CL_1440m.jsonl` vs MCL).

| id | avenue | verdict | reason / stopping point / blocker |
|---|---|---|---|
| II-1 | Calendar spreads (expiry-to-expiry), butterflies, condors on the curve | `DEFERRED` | **Blocker: BLOCK-NOSECONDEXPIRY.** Change-condition: a per-expiry series with contract-month labels. `[measured: "calendar spread" → 2 files, both incidental (DEFECTS.md, workspace/strategy_research/w3_cleanfeed.py)]`. |
| II-2 | Carry / roll-yield harvesting; contango vs backwardation; term-structure slope | `DEFERRED` | **Blocker: BLOCK-NOSECONDEXPIRY.** `[measured: "contango" → 0 files, "backwardation" → 0, "roll yield" → 0, "term structure" → 0]`. Zero footprint in this repo of any kind. |
| II-3 | Basis and cash-futures arbitrage; index arbitrage; EFP | `OPEN-PARTIAL` | **Stopping point: named only — and the data is already here.** SPY/QQQ at 5m, 1h and 1d sit beside MES/MNQ at the same resolutions, and `CL_1440m` sits beside MCL. Nobody has ever computed a basis series from them. BLOCK-ONEFRAME blocks trading it, not measuring it. BRIEF's own MCL-vs-`CL=F` note (109 overlapping hourly bars, closes differ 0.95c mean / 4c worst) is itself an unlabelled basis measurement. IN FLIGHT (R2 owns the `csv/raw` inventory). |
| II-4 | Inter-commodity spreads: crack (CL/RB/HO), crush (ZS/ZM/ZL), spark, gold-silver, wheat-corn | `DEFERRED` | **Blocker: only one leg of each pair is present, and the two that are present are broken.** No RB, HO, ZM, ZL, SI series in either store. Wheat-corn *is* nominally constructible from `MZW`/`MZC` — but the grain CSVs splice contract months (D40) and are excluded `[repo-verified: BRIEF.md]`. `[measured: "crack spread" → 0 files]`. |
| II-5 | Inter-market and cross-asset relationships (rates vs index, dollar vs metals, risk-on/off) | `DEFERRED` | **Blocker: no rates, FX or dollar-index series in either store.** Inventory above: equity index, gold, crude, grains, two equity ETFs. Change-condition: one fetch via `yahoo.py` (`^TNX`, `DX=F`, `6E=F`) plus an archive write. Cheapest `DEFERRED`→`OPEN` conversion in Class II. |
| II-6 | Statistical arbitrage: cointegration and pairs, ratio mean reversion, basket vs component | `OPEN-PARTIAL` | **Stopping point: named only.** `[measured: "cointegrat" → 0 files]`. ES/NQ at 1h and 5m, MES/MNQ across seven intervals, SPY/QQQ — several candidate pairs are on disk. Note the trap: D14/D41's 0.5–0.8% figure is *rule-set* overlap between scan populations, **not** price correlation; nothing here has measured the price relationship between two contracts. BLOCK-ONEFRAME blocks execution only. |
| II-7 | Cross-sectional momentum and cross-sectional carry across a futures universe | `DEFERRED` | **Blocker: the universe is too small and too ragged.** 11 symbols, of which 4 are the same index complex, 3 are D40-excluded grains and 2 are ETFs; only MGC/MES/MNQ have daily history, and their spans start 2016/2019/(unknown) `[repo-verified: DIVISION.md Appendix B #3, #4]`. Cross-sectional ranking needs a cross-section. Change-condition: ≥10 independent contracts with a common span. |
| II-8 | Lead-lag between contracts: index complex, cash/ETF vs futures, one commodity leading another | `OPEN-PARTIAL` | **Stopping point: named only, and do not confuse it with the closed one.** Cross-*timeframe* lead-lag inside one symbol is settled and `DIVISION.md` §5.5 forbids re-opening it (`s_leadlag`: "the lead is real, large and stable — and not tradeable"; `break_of_structure`@240m **retracted** on its first out-of-sample test) `[repo-verified: workspace/studies/STRUCTURE_FINDINGS.md:166-213]`. Cross-*contract* lead-lag has never been touched. The precedent is discouraging in a specific, useful way: the one lead this repo did measure was real and still not tradeable. |
| II-9 | Correlation-regime trading; correlation breakdown; dispersion | `OPEN-PARTIAL` | **Stopping point: named only.** Measurable offline from the inventory above with no new primitive. Same rule-set-vs-price conflation warning as II-6. |
| II-10 | Seasonality: annual, monthly, time-of-month, day-of-week, expiry-week, roll-window | `OPEN-PARTIAL` | **Stopping point: named only, and the manager pre-registered it as one of two genuine Class II positives** (`DIVISION.md` §6, Track R2). `StrategyFilters.days_of_week` already exists `[measured: grep -ril "days_of_week" → base.py + 3 workspace scripts + DEFECTS.md]`; `MGC_1d.csv` carries 2,511 bars from 2016-09-26. `[measured: "seasonal" → 0 files]` — not one study in ~2.98M evaluations conditioned on a calendar position. The expiry-week and roll-window sub-avenues are additionally blocked by BLOCK-NOSECONDEXPIRY. IN FLIGHT (R2-D5 area). |
| II-11 | Scheduled-event trading: pre-positioning, straddle-the-number, fade-the-spike, post-release drift | `OPEN-PARTIAL` | **Stopping point: the clock is audited, the event is not.** R1 established that all three `news` conditions read only *minutes to / since a projected timestamp* — no actual, no consensus, no surprise — so `news` is structurally a `time` group `[repo-verified: research/R1_flow_auction.md → library.py:1325-1362, features.py:946-1000]`, and that the plumbing filters to `impact.rank >= HIGH` before computing proximity, so every MEDIUM/LOW `ECON_RULES` entry is invisible to every condition `[repo-verified: features.py:972-973]`. The surprise term does not exist as a data object anywhere. Event *response* conditional on surprise: `DEFERRED` sub-avenue, blocker = no released-value/consensus store. Rule inventory IN FLIGHT (R2-D5, per OPEN_QUESTIONS Q3). |
| II-12 | Unscheduled news and headline-driven; latency-sensitive event reaction | `DEFERRED` | **Blocker: no point-in-time news archive**, and a scraped one would import look-ahead — the repo's own design note says conditioning on a scraped headline "would mean reading an article written after the bar" `[repo-verified: library.py:1325-1331 via R1]`. Change-condition: a timestamped, point-in-time wire archive. This is the hardest `DEFERRED` in the class to convert honestly. |
| II-13 | Inventory and fundamental-driven (storage, stocks-to-use, weather, OPEC) | `DEFERRED` | **Blocker: no fundamental store of any kind**, and the release-then-revision structure of this data makes point-in-time correctness the real cost, not the download. |
| II-14 | Options-informed: gamma exposure / dealer hedging levels, 0DTE pinning, skew, IV vs RV | `DEFERRED` | **Blocker: no options chain, no implied-vol series.** `[measured: "gamma" → 0 files, "0DTE" → 0]`. Change-condition: an options chain with greeks or enough to compute them. Note the asymmetry worth recording: the *realised* half of IV-vs-RV is fully computable here; only the implied half is missing. |
| II-15 | Delta-neutral futures positioning: futures as the hedge leg, gamma scalping, delta hedging | `DEFERRED` | **Blocker: an options leg, plus no multi-leg position object.** Compound of II-14 and BLOCK-ONEFRAME. |
| II-16 | Volatility as a traded object: VX term structure, contango roll-down, variance risk premium | `DEFERRED` | **Blocker: no VX or VIX series.** `[measured: "variance risk" → 0 files]`. Change-condition: one fetch (`^VIX`, and VX futures for the term structure — the latter has the same per-expiry problem as II-1). |
| II-17 | Positioning and flow data: COT/CFTC, open-interest change taxonomy, commercial vs speculative | `DEFERRED` | **Blocker: no open-interest column and no COT file.** `[measured: grep -ril "\bCOT\b" → 0 files]`; `open_interest` is `None` on every bar, and R1 showed the two `openinterest` conditions are therefore a **guaranteed-null pair** — the SIGNAL never fires and the FILTER, returning `no()`, vetoes every entry `[repo-verified: research/R1_flow_auction.md → library.py:1281-1282,1309-1310]`. Change-condition: an OI column (weekly COT is free and public; daily OI is a vendor field). |
| II-18 | Term-structure-conditioned trend (trend filtered by the sign of carry) | `DEFERRED` | **Blocker: depends entirely on II-2.** Listed separately because it is the cheapest Class II family to build *once* carry is observable — it is a filter over machinery that already exists. |
| II-19 | Macro-regime overlays (rate cycle, inflation regime, liquidity conditions) | `DEFERRED` | **Blocker: no macro series.** Also the hardest to power-test: a regime with a multi-year period gives single-digit independent observations over an 11-month intraday span. |

---

## Class III — the position's own path (needs only this contract's OHLCV)

This class is where the ~2,975,629 evaluations actually live, so the temptation to mark it all
`CLOSED` is strongest here and is mostly wrong. Two facts set the frame:

- **What the programme varied:** entry rule sets (13 templates over 79 conditions), five
  `StopKind`s, three `TargetKind`s, timeframe, symbol, window
  `[repo-verified: DIVISION.md Appendix A + §9]`.
- **What the programme held constant:** size. The manager's own dispatch says it plainly —
  "No position-sizing scheme other than one flat risk unit"
  `[repo-verified: workspace/roundtable/msgs/01_manager_all_division.md]`. So the settled negative
  verdict is a verdict about **rule selection at fixed size**, and every row below about sizing is
  genuinely unexplored rather than refuted.

One shared blocker: **BLOCK-NOSEQUENCE** — "the combinator cannot express a sequence at all.
`min_signals=2` requires two conditions on the *same bar*, and a sweep and its consequence never
co-occur. Every 'A then B' idea is inexpressible" `[repo-verified:
scan_reports/2026-09-24_ORB-and-ICT.md:92-117; defect D37]`.

And one shared **counterweight to the whole class**, which every row should be read against: this
repo has measured the win-rate/payoff cancellation **four separate times** — moving a stop from
structure to a wider ATR raises payoff ~89% and drops win rate ~14 points for *no* expectancy gain
`[repo-verified: BRIEF.md rule 3]` — and the mechanism was shown to be geometric rather than
informational (with geometry held fixed, win rate is flat at 0.370–0.423 across every distance
bucket) `[repo-verified: workspace/studies/STRUCTURE_FINDINGS.md:14-33]`. The manager's central
Class III prediction is that **most of the operating layer is a variance transform, not an
expectancy transform** (`DIVISION.md` §6). Nothing below contradicts that; the rows record which
parts of it have actually been put to the test.

| id | avenue | verdict | reason / stopping point / blocker |
|---|---|---|---|
| III-1 | Time-series momentum / CTA trend following (Donchian, MA crossover, 12-month momentum) | `OPEN-PARTIAL` | **Stopping point: the EMA/ADX-shaped version is measured; the classic CTA version is named only.** TREND is one of the 13 groups and was scanned heavily — and its headline result was **retracted** as a trade-floor artefact (MES 1h TREND +0.252R "real inside the 20–40 trade band only… inverts at n≥40 and n≥60") `[repo-verified: scan_reports/2026-09-24_strategy-studies_21-study-programme.md:12-34]`. But `[measured: "donchian" → 0 files, "12-month\|12 month momentum" → 0]`. A Donchian channel is not an EMA stack, and a 12-month momentum signal needs the daily files (MGC 2,511 bars from 2016-09-26) that the intraday scans never used. |
| III-2 | Volatility breakout systems (Turtle, NR7 / inside-day expansion, squeeze release, ATR channel) | `OPEN-PARTIAL` | **Stopping point: the library's own breakout detectors are measured; the compression-*conditioned* version is not.** `inside_bar_compression`, `volatility_compressed` and `keltner_outside` exist `[repo-verified: DIVISION.md Appendix A]` — but `volatility_compressed` **is an exact alias for BREAKOUT group membership**, so any A/B on it compares groups, not conditions `[repo-verified: 21-study-programme.md:118-141, hard constraint 3]`. `[measured: "NR7"/"NR4" → 2 files, both the ORB report's *definitions* paragraph, never tested; "Turtle" → 0]`. Crabel's conditioning filter is named in `workspace/studies/ORB_ICT_FINDINGS.md:252-258` as literature and is the one ORB axis the 1,920-configuration sweep did not carry. |
| III-3 | Volatility-regime-conditioned entry: expansion vs contraction cycles on the traded series | `OPEN-PARTIAL` | **Stopping point: three volatility *filters* measured; the *cycle* never expressed.** `volatility_normal` "earns its place — but is symbol-specific" and survived programme-wide Bonferroni correction `[repo-verified: 21-study-programme.md:66-70]`. A contraction→expansion *transition* is an A-then-B statement and is therefore BLOCK-NOSEQUENCE. |
| III-4 | Mean reversion to a band or anchor on one series (Bollinger, Keltner, VWAP, z-score) | `CLOSED-EMPTY` | Measured, and the thing itself was measured: MEAN_REVERSION's apparent +0.070 "was a floor artefact; floor-free it is **−0.141R, worst of 12 groups**" `[repo-verified: 21-study-programme.md:105-118]`. Reopen only with a new reason; `regime_ranging` being an exact alias for the group is one candidate reason, recorded here so a later burst does not have to rediscover it. |
| III-5 | Pattern and sequence strategies: multi-bar sequences, setup → trigger → confirmation chains | `OPEN-PARTIAL` | **Stopping point: exactly one sequence has ever been tested, by a bespoke detector outside the combinator, and it was null.** sweep→MSS→retrace: "the first link does not cause the second", no stage adds anything on ablation, and **the wrong order ranks first** `[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:173-237]`. One instance does not close a family. The general primitive is absent (BLOCK-NOSEQUENCE / D37) and that is the blocker to exploring it at scale. |
| III-6 | Opening range / initial balance systems | `CLOSED-EMPTY` | Measured properly, at length, after the detector was repaired: 1,920 configurations, 194,005 trades, floor-free, median expectancy **−0.092R** against a median 32R max drawdown, 18.8% profitable, best t 2.137 vs a 3.888 threshold, and **negative at zero transaction cost** — an absent edge, not a cost problem. Yesterday's opening range beats today's. The range is broken in 74–100% of RTH sessions (median 99.3%), so the entry is not a condition. 4-hour ORB is arithmetically impossible `[repo-verified: scan_reports/2026-09-24_ORB-and-ICT.md:11-27, 92-117; workspace/studies/ORB_ICT_FINDINGS.md:100-172]`. **One axis not carried: NR4/NR7 compression conditioning — logged at III-2, not here**, so that this closure is not quietly reopened as an ORB question. |
| III-7 | Position sizing as strategy: fixed fractional, fixed ratio, volatility targeting, ATR-normalised, Kelly, fractional Kelly, risk parity | `OPEN-PARTIAL` | **Stopping point: named only — and it is the single largest named-only avenue in the ledger.** `[measured: "Kelly" → 0 files, "fixed fractional" → 0, "volatility target"/"vol target" → 0]`. Every one of ~2.98M evaluations ran one flat risk unit. **The honest caution, recorded so nobody oversells it:** expectancy measured *in R* is invariant to any sizing scheme that scales the risk unit, so most of this avenue cannot move the statistic the programme ranked on. The part that can is the part that changes *which trades are taken or skipped* (a vol-target floor that declines a trade when the stop is too wide) or that changes the compounded path. Stating which of those two a sizing study is about is the first thing a scope needs to settle. IN FLIGHT (R3, `DIVISION.md` §5.6 gives R3 sizing exclusively). |
| III-8 | Pyramiding / scaling in: add on strength, add on weakness, anti-martingale, Turtle unit adds, averaging down | `DEFERRED` | **Blocker: one open position per strategy id, structurally.** `engine.py:304-311`: `# --- 3. look for new signals (never while already positioned)` then `if sid in open_pos or sid in pending: continue` `[repo-verified: futures_agents/backtest/engine.py:304-311]`. `[measured: "pyramid" → 0 files]`. Change-condition: a multi-entry position object. The manager pre-registered this verdict and cited `engine.py:303-308`; my read of the current file puts it at 304–311 — same mechanism, and the discrepancy is noted rather than resolved (R3's surface). |
| III-9 | Scaling out, partial profit-taking, runner management | `OPEN-PARTIAL` | **Stopping point: expressible, exercised, and its measured results are cost-contaminated.** Multi-target exits exist and run — and "costs are under-charged on multi-target exits: a three-target scale-out pays **one** round turn, and the partials pay zero slippage. 62–92% of 4h/daily exits pay no exit slippage" `[repo-verified: 21-study-programme.md:118-141, hard constraint 7]`. So every published scale-out number is optimistic by an unquantified amount, and the direction of the bias is known. That is a fixable-then-remeasure avenue, not an empty one. |
| III-10 | Stop discipline: initial placement, breakeven moves, trailing (ATR, chandelier, parabolic, structural), stop-hunt avoidance | `OPEN-PARTIAL` | **Stopping point: structural-vs-ATR is settled; three named trailing variants and the breakeven move are not present.** Settled: "structural stops never tighter than ~0.5 ATR", and the honest form is "*if* you use structural stops" — an ungated structural stop is *worse* than a plain 1-ATR stop out of sample (z = −2.24, sign 2/8) and the floor only restores parity `[repo-verified: workspace/studies/STRUCTURE_FINDINGS.md:34-54]`. `[measured: "chandelier" → 0 files]`; "trailing" appears in 36 files so some trailing exists. Whether a breakeven move or a parabolic trail is expressible at all is R3's to verify. |
| III-11 | Target discipline: fixed R, measured move, structural objective, trail-only, no target | `OPEN-PARTIAL` | **Stopping point: three `TargetKind`s measured; the anchor/execution split settled null; "measured move", "trail-only" and "no target" named only.** The anchor/execution claim was retracted twice over — it "**never ran**" (`execution_tf` was `None` in 8,521 of 8,521 scanned strategies), and rebuilt properly gave pooled z = −0.00; it survives only "at a 4-hour anchor with anchored targets" `[repo-verified: 21-study-programme.md:12-58]`. |
| III-12 | Time-based exits: time stops, session-close flattening, week-end flattening, hold-period targeting | `OPEN-PARTIAL` | **Stopping point: one member measured and it is the programme's largest single effect; the rest named only.** "Turn `exit_at_session_close` off — the largest single effect measured" `[repo-verified: 21-study-programme.md:40-46]`. This is also the manager's pre-registered class of exception (rules that change costs or the number of trades, rather than moving stops around) and it came back positive, which raises rather than lowers the value of testing time stops, week-end flattening and hold-period targeting — none of which has been varied. |
| III-13 | Re-entry after a stop-out; scratch and breakeven exits; trade-campaign management | `OPEN-PARTIAL` | **Stopping point: named only.** `[measured: "cooldown" → 0 files, "min_bars_between" → 0]`; the six "re-entry" hits are unrelated (`storage.py`, three `workspace/newstrats/*.py` run scripts, one `research/confluence` doc). Note the interaction with III-8's blocker: one-position-per-strategy means a re-entry rule is expressible *in principle* (the position is closed before the next signal is considered) where pyramiding is not — so this avenue may be cheap where its neighbour is impossible. Unverified; R3's surface. |
| III-14 | Portfolio heat, correlated-exposure limits, daily loss limits, drawdown governors, equity-curve trading | `OPEN-PARTIAL` | **Stopping point: named only as strategy.** `futures_agents/risk/manager.py` and `risk/account.py` exist (R3's surface, unaudited by me). `[measured: "equity curve" → 3 files, all incidental: `metrics.py`, `workspace/newstrats/geometry.py`, `docs/DESK_UI.md`]` — so equity-curve *trading* (switching a system on and off by its own drawdown) has never been tested. Also note `correlation_group` exists in `config.py` and D14/D41 measured index-complex contamination, so the *inputs* to a correlated-exposure limit are partly present. |
| III-15 | Roll management as an operational task | `DEFERRED` | **Blocker: BLOCK-NOSECONDEXPIRY** — same as II-1. No contract-month label means the roll is invisible except as D40's splicing defect. |
| III-16 | Execution mechanics: limit vs market vs stop-limit, partial fills, slippage budget, cost-aware entry | `OPEN-PARTIAL` | **Stopping point: the fill model has been audited in one direction and found to have produced the project's sharpest artefact; order types and partial fills are unexplored.** The artefact: a retest limit filling mid-bar at the bar's extreme, with the same bar's opposite extreme credited as a target hit, manufactured a **+0.354R cluster at t = 5.19** that survived a 60/40 split **and all three disjoint slices**; 51% of its winners "hit target" on the entry bar `[repo-verified: scan_reports/2026-09-24_ORB-and-ICT.md:117-133]`. The conclusion generalises and is now a required check: **resampling cannot detect a bias whose sign is always favourable; only auditing the fill model can.** |
| III-17 | Meta-labelling and model-based filtering — deciding whether to take a signal you already have | `OPEN-PARTIAL` | **Stopping point: named only, and this repo holds an unusually good substrate for it.** `[measured: "meta.label" → 0 files]`. ~2.98M evaluations with per-trade artefacts is exactly the labelled dataset a meta-labeller consumes, and `workspace/studies/out/*.json` plus the per-study audit JSONs are committed. **The counter-evidence to weigh first, and it is heavy:** trading last period's top 10 returns −0.0155R against a −0.0104R null and *underperforms trading the whole qualifying universe* — selecting is worse than not selecting `[repo-verified: BRIEF.md]`. A meta-label is a selection rule, and the repo's one measurement of a selection rule is negative. **LEAD-02, see MAIN_TASKS.md.** |
| III-18 | Discretionary overlay and operating discipline: journal, review cadence, error taxonomy | `OPEN-PARTIAL` | **Stopping point: named only as a family.** `workspace/journal/` exists and `CALLOUT.md` documents how the desk is currently operated live. Partly not a backtestable avenue at all, which is worth saying once so a later burst does not scope it as if it were. |
| III-19 | Anti-strategy: what operationally destroys expectancy (over-trading, revenge trading, moving stops, martingale) | `OPEN-PARTIAL` | **Stopping point: several members measured, never assembled as a family.** Already established destructive operations: `exit_at_session_close` **on** (largest single effect, wrong way), `rth_only=False` (**D24** — "buys sample and costs expectancy, the opposite of what an earlier brief claimed"), intraday entries 15:00–16:00 ET (z = −4.43), requiring multi-timeframe alignment (z = −4.09), entering near structural invalidation (dose-response z = −7.69, OOS sign 0/8) `[repo-verified: BRIEF.md rules 2 and 5; workspace/studies/STRUCTURE_FINDINGS.md:14-33]`. **This is the most under-rated avenue in the ledger**: it is the only Class III family where this repo already has five independent positive results, all of them prohibitions, and nobody has written them up as one object. |

---

## Cross-cutting avenues — not in the 53, but explored (or not) and therefore owed a verdict

These are avenues about the *method*, the *measurement* and the *data* rather than about a strategy
family. They belong in this ledger because they are where most of the ~2.98M evaluations' effort
actually went, and because two of them gate whole families in the tables above. Numbering is `X-`
to keep it clearly distinct from the manager's 53.

| id | avenue | verdict | reason / stopping point / blocker |
|---|---|---|---|
| X-1 | Selection as a strategy: trade last period's top-N | `CLOSED-EMPTY` | Measured directly and at scale: 692 top-10 rows, **zero clear deflation** or even their own cell's threshold; realised expectancy of acting on the list is **−0.0155R against a −0.0104R null**, and it **underperforms trading the whole qualifying universe** `[repo-verified: BRIEF.md; scan_reports/2026-09-24_MGC-MCL_…:22-48, 218-230]`. Selecting is worse than not selecting. |
| X-2 | Chronological rotation / chaining of strategy-group efficacy | `CLOSED-EMPTY` | Measured three ways in increasing power on daily series (MGC 117 months / 56,670 trades; MES and MNQ 89 months each), floor-free and rank-free by design. Winner persistence z = +0.49 / +1.00 / −0.37; own-group autocorrelation none surviving correction; **cross-lag 0 surviving pairs on every symbol**. The largest effects are *positive*, i.e. co-movement, not handover `[repo-verified: scan_reports/2026-09-24_MGC-MCL_…:164-217]`. And even a true chain would need to be known *before* the month it leads in. |
| X-3 | Multi-timeframe agreement as a virtue | `CLOSED-EMPTY` | Requiring any alignment measured detectably **worse** than requiring none (z = −4.09), independently reproduced in the structure programme, and on a two-timeframe frame "majority" and "unanimous" are the same statement (D17) `[repo-verified: BRIEF.md rule 2; workspace/studies/STRUCTURE_FINDINGS.md:69-74]`. |
| X-4 | Timeframe selection and grouping — *which* timeframes, in what combination | `OPEN-PARTIAL` | **Stopping point: the per-timeframe ranking is measured; group composition is not, and two open defects corrupt the coarse end.** Settled: "sub-hourly is a graveyard — at 5 minutes, 11–16% of strategies make money" `[repo-verified: BRIEF.md rule 7]`. Not settled: `TIMEFRAME_GROUPS` exists in `config.py` (≈line 312 per `DIVISION.md` §9) and nothing has tested whether *composition* matters once the alignment *requirement* (X-3) is dropped. **D21** (the session-scale guard never reaches 4h) and **D24** (`rth_only`) mean "every 4h population is 2–12× smaller than it should be" `[repo-verified: 21-study-programme.md:142-160]`, so the 4h and daily ends have never been measured at full sample. |
| X-5 | Confluence depth / how many signals and filters | `CLOSED-EMPTY` | "Two signals and one filter is the ceiling. 2→4 signals cuts trade count 35% and does not improve expectancy; the sign favours two" `[repo-verified: BRIEF.md rule 1]`. |
| X-6 | Hours-of-day and session-window filters as expectancy improvers | `CLOSED-EMPTY` | "No hours filter improves expectancy. The lunch-avoidance folk claim is refuted" `[repo-verified: BRIEF.md rule 6]`; and ICT kill zones "have more range and volume, and no more direction — the effect is trade thinning, not time of day" `[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:280-315]`. **Not closed by this:** the 15:00–16:00 ET *prohibition*, which is a different claim (an interval to avoid, not a filter to add) and is logged at I-15 and III-19. |
| X-7 | The ICT / Inner Circle Trader concept set | `CLOSED-EMPTY` | 0 live-eligible across every concept tested; order blocks and FVGs fail at bar level before an exit is chosen; five placebo zone constructions match or beat them; OTE is `fib_golden_pocket` under another name (Jaccard 0.938–1.000, the **seventh** duplicate condition found in the project) `[repo-verified: scan_reports/2026-09-24_ORB-and-ICT.md:11-27, 134-146]`. **Residue, recorded so it is not mistaken for tested:** four concepts were judged **not falsifiable as stated** and were never tested — Power of Three, the Judas swing, MSS (two incompatible published detectors) and the mitigation block `[repo-verified: ORB-and-ICT.md:28-48]`. |
| X-8 | Condition naming vs condition arithmetic — the "phantom group" audit | `OPEN-PARTIAL` | **Stopping point: three groups audited by R1 (`orderflow`, `openinterest`, `news` — 8 conditions, 10% of the library); sixteen groups not.** R1's result is that all three name information the data does not contain, and that the `estimated` flag which exists to say so is **set and never read** by any consumer `[repo-verified: research/R1_flow_auction.md]`. Two consequences are logged as unanswered questions rather than findings: `OPEN_QUESTIONS.md` Q1 (does this warrant a D-number) and Q2 (did structurally-null `openinterest` strategies enter the 2,975,629 denominator). **Strong candidate for a future main task** — a name-vs-arithmetic audit of the remaining 71 conditions has never been run. |
| X-9 | Redundancy census: do two conditions compute the same thing | `OPEN-PARTIAL` | **Stopping point: seven duplicates found, every one of them by accident, one at a time.** Known: OTE ≡ `fib_golden_pocket` (Jaccard 0.938–1.000, "the seventh duplicate condition found in this project"); the shipped ORB condition was a **Jaccard 0.993 duplicate of `initial_balance_break`** on MCL; and **seven filter names are exact aliases for group membership** (`avoid_lunch`≡REVERSAL, `opening_drive_window`≡OPENING_RANGE, `after_opening_range`≡LIQUIDITY, `mtf_not_conflicted`≡PULLBACK, `regime_trending`≡TREND, `regime_ranging`≡MEAN_REVERSION, `volatility_compressed`≡BREAKOUT), so A/B on any of them compares groups `[repo-verified: 21-study-programme.md:118-141; ORB-and-ICT.md:134-146, 92-117]`. **No systematic pairwise firing-overlap census over all 79 conditions has ever been run.** Cheap, and it would change how every existing result is read. |
| X-10 | Detector validity census: does a condition fire at a usable rate, and can it fire at all | `OPEN-PARTIAL` | **Stopping point: four degenerate detectors found ad hoc; no census.** `session_extreme_sweep` compares a bar against a session high that includes that bar (arithmetically cannot fire); `range_position_extreme` is a **guaranteed zero inside REVERSAL** (returns LONG at the range top, so it can never agree with the required mean-reversion signal — 262–440 rule sets per cell, 0 trades, 12 of 12 cells); `opening_range_breakout` fires on **4 of 4,256 bars**; at the other extreme `value_area_breakout` fires on ~51% of bars and ICT order blocks on 40.5–51.5% — "by this library's own standard, over 95% firing is not a condition" `[repo-verified: 21-study-programme.md:105-118; ORB-and-ICT.md:92-117, 100-113]`. A firing-rate-plus-degeneracy census across all 79 conditions × symbols × timeframes is arithmetic, not a sweep. |
| X-11 | The defect register itself | `OPEN-PARTIAL` | **Stopping point: 43 catalogued, 7 open (D21, D24, D36, D37, D38, D39, D40).** The 21-study programme's own Priority 1 is "fix the defect register… several of which corrupt results rather than merely wasting budget" `[repo-verified: 21-study-programme.md:142-160; BRIEF.md]`. Two open defects gate families in the tables above rather than merely degrading numbers: **D37** (no sequence support → III-5, III-3, I-11) and **D21** (4h guard → X-4). **D38** (`toolkit.measure_custom` silently zeroes custom conditions) is the one most likely to have silently produced a null someone believed. |
| X-12 | The new data stores: `data/archive/` and a reachable vendor | `OPEN-PARTIAL` | **Stopping point: named only, and nothing in `scan_reports/` has ever been measured on it.** All four reports predate it `[measured: newest scan_reports mtime 2026-09-25 06:08 vs data/archive added 2026-09-26]`. 29 JSONL series, ~157,000 bars, newest 2026-09-25, **≈11,300 hourly bars per symbol reaching back to 2024-10-06** against the ~5,000-bar / 274-day hourly files in `csv/raw` (MGC_1h spans 2025-11-05 → 2026-09-22) `[repo-verified: BRIEF.md; DIVISION.md Appendix B #3]`. So the archive **contains** the published span and adds roughly thirteen months *before* it. **That prior period is the only genuinely disjoint, never-searched out-of-sample data this project has**, and it is the natural answer to the nested-window problem (30 ⊂ 90 ⊂ 180 ⊂ 274 days, all ending on the same bar, "arithmetic, not replication"). Highest-leverage unexploited resource in the repo; flagged, deliberately not pursued in burst 01. |
| X-13 | Cross-symbol comparability of scan populations | `DEFERRED` | **Blocker: a shared rule-set population does not exist.** "`generate_combinations` seeds RNG per symbol, so MES and MGC 60m populations share **0 of 204** rule sets" — cross-symbol comparison is currently impossible `[repo-verified: 21-study-programme.md:118-141, hard constraint 5]`. Change-condition: generate the population once and evaluate it on every symbol. Cheap to fix, and until it is fixed, every per-symbol comparison in this repo compares two different searches. |
| X-14 | Placebo and null-control methodology | `OPEN-PARTIAL` | **Stopping point: five placebo *entry* constructions built; all matched or beat the real signals; no placebo has ever been built for the exit side.** The placebos are "random bars run through the base's own exits, filters and sizing" `[repo-verified: BRIEF.md]` — so they hold the exit constant and randomise the entry. The mirror experiment (real entries, randomised exits) has never been run, and it is the experiment that would say *where* in the rule the information is or is not. Cheap, and it directly attacks the project's central negative result without re-litigating it. |
| X-15 | Deflation and multiple-testing accounting | `OPEN-PARTIAL` | **Stopping point: the verdict is settled; the denominator is not verified.** `free_t = 5.46` programme-wide, largest t anywhere **3.923**, nothing close `[repo-verified: BRIEF.md]`. But `OPEN_QUESTIONS.md` Q2 (R1, unanswered) asks whether structurally-null candidates — every strategy carrying `oi_price_confirmation` or `oi_expanding` takes zero trades by construction — entered the 2,975,629 count. Direction of the error is known and safe (an inflated denominator makes the threshold *more* conservative), so this cannot rescue anything; the number should still be right. |
| X-16 | The 352-session 1-minute archive (`data/{MES,MGC,MNQ}_1m.csv`) | `OPEN-PARTIAL` | **Stopping point: used by exactly one study.** 404k–470k genuine 1-minute bars covering **352 RTH days, 2019-01-01 → 2020-05-14**, resampling to any grid including MGC's 08:20 open; contains the Feb–Mar 2020 crash; **it is Oanda CFD data, real market structure but not the futures price**, and a different era, so it **cannot be pooled with `csv/raw`** `[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:250-280, 100-121]`. It was built to escape ORB's 18–19-session sample trap and has been used for nothing else. It is the substrate MAIN-01 needs. |

---

## Burst 01 addendum — a measurement that changes two rows above

Made while sweeping I-12 (Part B), recorded here because it bears on X-4 and X-12 rather than on
the main task alone. **It is a sample-basis statement, not a contradiction of a settled rule.**

`[measured: python3 -c over every csv/raw file, counting rows and first/last timestamp →]`

| grid | bars per file | calendar span | ≈ trading sessions |
|---|---|---|---|
| 1m (MGC, MES, MNQ, MCL) | 5,000 | **5 days** (2026-09-17 → 09-22) | ≈ 4 |
| 5m (micros) | 5,000 | **27 days** (2026-08-26 → 09-22) | ≈ 19 |
| 5m (ES, NQ) | 5,000 | 25 days | ≈ 18 |
| 15m / 30m | 3,753 / 1,877 | **58 days** (2026-07-26 → 09-22) | ≈ 41 |
| 1h | 5,000 | ≈ 322 days (MGC_1h 2025-11-05 → 2026-09-22) | ≈ 274 (the published figure) |

The ~5,000-bar cap is already recorded as `DIVISION.md` Appendix B #3, but only its *hourly*
consequence was spelled out. **Its sub-hourly consequence is that the frozen snapshot carries about
nineteen trading sessions at 5 minutes and about four at 1 minute.** The ORB study found the same
thing from its own side and said so plainly — "`csv/raw` gives 18–19 RTH sessions per symbol,
median 16 trades per configuration — an anecdote, exactly as D30 predicted"
`[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:114-121]` — and went to
`data/*_1m.csv` to escape it.

**Consequence for X-4, recorded as a stopping point and not as a refutation.** BRIEF rule 7
("sub-hourly is a graveyard. At 5 minutes, 11–16% of strategies make money") is stated as a general
rule about timeframes; on the frozen snapshot it is measured over ≈19 sessions per symbol. I am
**not** claiming sub-hourly works — the 11–16% figure may well be right, and the ORB study's deep
1-minute replication was also negative. I am recording that the rule's sample basis is four to
nineteen sessions where its phrasing implies a timeframe law, that two deeper sub-hourly stores now
exist (X-12, X-16) and that neither has been used for it. A later burst resuming X-4 starts here.

**Consequence for X-12.** `data/archive/` holds `{MCL,MES,MGC,MNQ}_1m.jsonl` and `_5m.jsonl`. Those
are the only sub-hourly series in the repo that are both (a) the futures price and (b) longer than a
month. Everything fine-grained either uses them or uses `data/*_1m.csv`, which is a different
instrument and a different era.

**One corroborating datum handed to R1, not pursued** (R1 owns the delta/CVD arithmetic): zero-range
1-minute bars are **12.28% of `data/MES_1m.csv`** and 3.54% of `data/MGC_1m.csv`
`[measured: same command]`. R1 established that `estimated_delta()` returns exactly `0.0` when bar
range ≤ 0. So on a 1-minute MES series, roughly one bar in eight has a delta of exactly zero by
construction rather than by measurement. Logged for R1; not mine.

---

## Rows I was tempted to close and did not

The honest-closure test at the top of this file is only worth something if it is applied against
the temptation. These are the rows where a `CLOSED` verdict was available and I declined it, with
the reason, so a later burst can disagree with me on the record rather than by accident.

| id | the closure that was available | why I declined it |
|---|---|---|
| I-11 | "The sweep family was tested and adds nothing." | Two different things were tested: a **bespoke** sweep→MSS→retrace detector (null, properly measured) and the **library's** sweep conditions (0 of 156 rule sets ever reached 20 trades, and one of them cannot fire at all). The second is a detector result. A liquidity *map* was never built. |
| I-9 | "VOLUME_PROFILE was scanned; it is one condition wearing six names." | That is a finding about the six conditions, not about the profile. The underlying volume-at-price object is built by spreading each bar's volume **uniformly** across its range, which is unflagged and unmeasured. |
| III-1 | "TREND was scanned to death and the headline was retracted." | What was scanned was EMA/ADX-shaped trend on intraday frames. Donchian and 12-month momentum appear **nowhere** in the repo, and the daily files that a long-horizon momentum signal needs were used only by the chronology study. |
| III-2 | "BREAKOUT was scanned." | `volatility_compressed` **is** BREAKOUT group membership, so the one condition that would express compression-gating is an alias. Crabel's NR4/NR7 conditioning is cited in the repo as literature and was never a sweep axis. |
| III-5 | "The sequence idea was tested and the wrong order ranked first." | One sequence, one construction. That result is strong evidence against *that* sequence and near-zero evidence about a family the combinator structurally cannot express (D37). |
| III-12 | "Session-close flattening is settled." | It is — and it is the *positive* one. Time stops, week-end flattening and hold-period targeting share its mechanism (change costs / change trade count, which is the manager's own pre-registered class of exception) and none of them has been varied. |
| X-6 | "No hours filter improves expectancy; kill zones are trade thinning." | True for *adding* a filter. The 15:00–16:00 prohibition is the opposite claim and it survived replication, so the avenue is not symmetric and closing it in one direction would hide the other. |
| X-4 | "Sub-hourly is a graveyard — rule 7." | See the addendum above. The rule may be right; its sample is 4–19 sessions on the frozen snapshot and two deeper stores now exist. |

## Leads logged in burst 01 and deliberately not pursued

| lead | where it sits | why not now |
|---|---|---|
| **LEAD-01 — anchored VWAP is built, tested, and wired to nothing.** `indicators/volume.py:25-26` exports `AnchorVWAP`, `build_anchor_vwap`, `major_move_anchors`, `swing_anchors`, `anchored_vwap`; `tests/test_anchored_vwap.py` exercises all of them; **no condition, feature snapshot or backtest reads any of them** `[measured: grep -rn over all *.py excluding __pycache__ and indicators/volume.py → only the test file and indicators/__init__.py:19,40]`. | I-10 | This is a direct hit on the manager's §7 Q2 ("expressible with today's vocabulary, widely operated, never tested here") — but `DIVISION.md` §5.3 gives R1 anchored VWAP explicitly and R1 is writing now. Pursuing it would duplicate live work. |
| **LEAD-02 — the repo holds an unusually good meta-labelling substrate and one strongly negative precedent for using it.** ~2.98M evaluations with committed per-trade artefacts is the labelled dataset a meta-labeller consumes; and the one selection rule this repo ever measured (trade last period's top 10) underperformed trading everything. | III-17 | Class III is R3's, and the interesting version of this question needs the comparative statistics round 1 is not producing. Also: the negative precedent is strong enough that a scope should start by asking why this selection rule would differ from that one. |
| **LEAD-03 — no placebo has ever been built for the exit side.** All five placebo constructions randomise the **entry** and hold the exit fixed. | X-14 | Cheap, sharp, and it attacks the central negative result from the one side nobody has tried — but it is one experiment, not an avenue, and it produces a comparative statistic. Better as a sub-task under someone's section than as a main task. |
| **LEAD-04 — `data/archive/` extends hourly history ~13 months *before* everything ever searched.** | X-12 | Not an avenue needing depth; a decision needing a manager. Logged at altitude with the numbers so it can be acted on without a research round. |

---

## Burst 01 reconciliation — R2 and R3 landed after the rows above were written

`R2_relational.md`, `R2_expressibility_wall.md`, `R3_path_operation.md` and
`R3_operating_vocabulary.md` did not exist when I read `research/` at 01:23 and were on disk by
01:40 `[measured: ls -la workspace/roundtable/research/ → 5 files, mtimes 01:28–01:40]`. The Class II
and Class III rows above therefore record the state *before* those files, and **a later burst must
re-read them before resuming any Class II or Class III row.** I am recording pointers, not
re-summarising live work that is still being appended to, and I have not edited a row to claim
credit for someone else's finding.

**One of my own framings is superseded and I am saying so rather than leaving it to be found.** My
Class II preamble treats `BLOCK-ONEFRAME` (`engine.py:548,554`) as *the* wall. R2's headline is that
this "is true and it is the **wrong** wall": there are **two** walls with very different costs
unlocking disjoint family sets — **Wall A**, one `FeatureSnapshot` per symbol (`features.py:687`,
`base.py:87`), eight additive edits, no breaking signature change, unlocking **6** families from data
already on disk and **3** more after a vendor fetch needing zero code change; and **Wall B**, one
instrument per position (`base.py:552,499`; `engine.py:159,233`), needing a multi-leg position
object, leg ratios, per-leg costs and R redefined on the spread, unlocking **5**, none without A
`[repo-verified: workspace/roundtable/research/R2_relational.md:9-26]`. Read my Class II rows against
that, not against my preamble.

**Independently reached the same conclusion I did, which strengthens both:** R2 concludes Class II
*was* mis-cut in one specific place — II-10 (seasonality) and II-11 (scheduled events) need no second
series at all `[repo-verified: R2_relational.md:22-25]`. That is the same kind of taxonomy artefact I
logged for I-12 in `MAIN_TASKS.md` §"Why it plausibly matters here" point 4, found from the other
side of the map. Two of three tracks independently finding a mis-cut is worth the manager's
attention as a pattern, not as two isolated boundary disputes.

**Rows above whose stopping point R2/R3 have already advanced** — pointers only:

| my row | advanced by | in one line |
|---|---|---|
| II-1 … II-19 (all) | `R2_relational.md:261+`, one section per family | Full catalogue entries under the §4 schema, plus R2-D0 (data inventory), R2-D4 (seasonality power arithmetic) and R2-D5 (event inventory, with the finding that "the HIGH calendar is almost entirely outside RTH, and the one test that was run was run on the symbol where it is emptiest"). |
| II-3, II-6, II-8, II-9 | `R2_expressibility_wall.md:172+` | Per-family proxy ledger: the cheapest *valid* proxy, or the named reason there is none. Supersedes my "measurable offline, named only". |
| III-7 | `R3_path_operation.md:269-550` (Parts B-1…B-4) | Sizing is **not in the measured universe at all** (B-1); the one scheme that *is* in it is invisible (B-2); a four-channel decomposition in which only two channels can move expectancy (B-3). This is the avenue I called the largest named-only row in the ledger; it is no longer named-only. |
| III-8 | `R3_path_operation.md` A-3, and B-5 | `max_concurrent_per_strategy` is a dead knob; confirms `engine.py:304-309`. My row noted a 304-311 vs 303-308 line discrepancy — R3 owns it and cites 304-309. |
| III-9 | A-8 | Scale-out assumes an infinitely divisible contract; scale-out fractions always sum to 1.0, so **a runner was never tested**. |
| III-10 | **A-1, A-2** | **"The trailing stop has never run. Not once."** and `ExitReason.TRAIL` is defined and can never be emitted. My row guessed trailing was "partially present" from a 36-file grep on the word; it is not present in any result. |
| III-11 | B-5 | Target ladder shape self-cancelling and settled, with D15 (no paired control) and D19 (confounded) attached. |
| III-12 | A-7, A-10, B-5 | Every time-based and session-based exit is **slippage-free by construction**; `allow_overnight` can never be True in any published result; time stop magnitude varied {30..120} but **never switched off**. |
| III-13 | B-5 | Re-entry policy: **no cooldown field anywhere** — confirms my `[measured: "cooldown" → 0 files]` from the code side and makes it architectural rather than merely untested. |
| III-14 | B-4, B-5 | **`run_portfolio` does not simulate a portfolio**; no shared account in `run_many`; but daily-loss-limit and equity-curve sizing are **replayable from stored artefacts today**. |
| III-16 | **A-11** | **Clean bill: no look-ahead in the position lifecycle, checked five ways.** My row cited the ORB study's fill-model artefact as an open worry about the production engine; R3 has now checked the production engine and it is clean. Also: `SlippageModel` has **no size term**, so market impact and capacity are unreachable. |
| III-17, III-19, and all of III-7…III-19 | `R3_operating_vocabulary.md` | A ten-section operating-vocabulary matrix (entry execution, initial risk, size, in-trade management, exit, re-entry/campaign, portfolio/governance, roll, meta-labelling, anti-strategy) with per-axis coverage. My LEAD-02 (meta-labelling) and my "III-19 is the most under-rated row" both land inside it; §9 and §10 respectively. |

**What none of the five files touches:** bar sampling. `MAIN-01` is unaffected — no R1, R2 or R3
section addresses what a bar is. `[measured: grep -il "tick bar\|volume bar\|dollar bar\|volume-bar\|
bar sampling\|subordinat" workspace/roundtable/research/*.md → no matches]`

### CORRECTION to the line immediately above — R1 does cover I-12, and it disagrees with me

The sentence "**What none of the five files touches:** bar sampling" is **wrong**, and I am
appending the correction rather than editing it away, because a ledger that quietly repairs its own
false claims is worse than one that carries them visibly. The grep I pasted to support it returned
`R1_data_requirements.md` and `R1_flow_auction.md`
`[measured: grep -il "tick bar\|volume bar\|dollar bar\|volume-bar\|bar sampling\|subordinat"
workspace/roundtable/research/*.md → 2 files]`. `R1_data_requirements.md` did not exist at my 01:23
read either, and `R1_flow_auction.md` grew from 223 to 1,700+ lines while I worked.

**What R1 actually wrote, at `R1_flow_auction.md:1098-1135` (§I-12) and `:1690-1700` (§7 answers):**

- A full §4-schema catalogue entry for I-12, verdict **INEXPRESSIBLE-ARCHITECTURE**, missing
  primitive named as **"a bar-identity that is not an integer minute count"**, load-bearing at
  **nine separate layers**, citing `bars.py:43`, `:164`, `:302`, `:309-311`, `:138-156` and
  `features.py:83` among others.
- R1 calls it "the one that surprised me" and reports it against the manager's pre-registration:
  9 on INEXPRESSIBLE-DATA plus 2 on INEXPRESSIBLE-ARCHITECTURE, "and the data/architecture split is
  not where he put it."

**This converges with my sweep on the architecture verdict and on the missing primitive — reached
independently, from two directions, within the same hour.** It also means the *catalogue* question
for I-12 is now answered and `MAIN-01` must not be read as asking it again.

**And R1 makes one substantive claim against mine, which is the more useful half of this
correction.** R1's "Minimum data" field says time-and-sales is **REQ** for tick / volume / dollar /
imbalance / run bars, and that "**Range bars alone** can be built from 1-minute OHLCV approximately —
and the approximation is **poor**, because the intrabar path is unknown and a range bar boundary is a
path statement" `[repo-verified: R1_flow_auction.md:1113-1116]`. My `MAIN-01` framing — that volume,
dollar and range bars "need only `(high, low, close, volume)` per minute, which this repo has" — is
**too strong**, and R1 is right about the mechanism: a volume-bar boundary is the moment cumulative
volume crosses a threshold, which occurs *inside* a minute, so from 1-minute bars the boundary can
only be snapped to a minute edge.

I am **not** withdrawing `MAIN-01`, for a reason stated there in full: my task asks a different
question (is the clock a confound in findings this repo treats as settled?) than R1's row answers
(can this library express the family?), and R1's own §I-12 supplies the "Already tested here? No"
that `MAIN-01` depends on. But the disagreement is now the **first** thing `MAIN-01` hands to a
scope, and if R1's "poor" is quantitatively right then `MAIN-01` is cheaply killed — which is a good
property for a main task to have. `MAIN_TASKS.md` records this under
§"What it would take to know" and §"Discovery's claim that R1 contradicts".

**Lead recorded, not pursued (burst 01 has had its one sweep).** R1 audited **3 of 19** condition
groups for name-vs-arithmetic and found **3 of 3** misnamed, and reports that "**half a generated
strategy set carries one of these proxies** (50.7% of a 284-strategy sample, and 100% of the REVERSAL
group)" `[repo-verified: R1_flow_auction.md:1700-1705]`. The remaining **16 groups / 71 conditions
have never been audited the same way** (`X-8` above). Given a 3-of-3 hit rate on the first sample and
a 50.7% carry rate from those three alone, this is the strongest candidate for burst 02's sweep, and
it needs no data and no new code. **LEAD-05.**
