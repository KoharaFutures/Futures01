# Archived_Do_Not_Refference — index

**Agents: do not open, search or re-analyse anything in this folder.** Every item here was
reviewed during the 2026-09-29 consolidation; its findings are already folded into
`DATA_HUB/` (start at `DATA_HUB/README.md`). The one-line summaries below tell you what each
item contained so you never need to re-explore it. If you believe something here is needed,
say so to the owner instead of reading it.

Paths are the ORIGINAL repo paths; the file now lives at `Archived_Do_Not_Refference/<path>`.

| original path | what it contained | why archived |
|---|---|---|
| `.claude/agents` | The previous 10-agent team definitions (manager, developer, news-macro, strategy-research, analyst-a/b/c, decision, risk, journal): role prompts only; their measured findings are in DATA_HUB | Owner is restructuring the agent team (2026-09-29) |
| `research/backtests/cross_symbol_timeframes.md` | Synthetic MES/MGC/MCL + tf groups: HTF confirmation keeps 28-44% trades, -0.033R t -1.81; cost 5.4% (MCL) vs 1.7% (MGC) of risk; time_stop in 1m bars defect | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/backtests/momentum_trend.md` | Synthetic MNQ MOMENTUM/TREND/PULLBACK/MTF: seed-5 winner fails on 3/5 paths, pooled OOS +0.0149R t 0.77; n=39 really n=25 (session-boundary round trips) | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/backtests/profile_vwap.md` | Synthetic MNQ VWAP/VOLUME_PROFILE: VWAP WF IS +0.132 -> OOS -0.029R; above_vwap fires 100%; best rule +0.0263R t 2.142 withheld | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/backtests/reversion_breakout.md` | Synthetic MNQ MEAN_REVERSION/REVERSAL/BREAKOUT/FIB: volatility_compressed starves BREAKOUT (3.1% bars), fib leg anchor broken (52.9% agreement), MR 13/19 rule sets zero signals | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/backtests/supply_demand_liquidity.md` | Synthetic MNQ S/D, LIQUIDITY, OR: zones 0->0 rule sets >=30 trades, stop inside zone 83-93%, LIQUIDITY WF credible on 1 path of 3, OR 1-3 fires/120d | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/confluence/analyst_b.md` | Audit of '38 of 38' coverage: 22/38 distinct, 17/38 exercised; 14/73 conditions never generated; 70% of strategies never fire (synthetic) | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/confluence/developer.md` | Adversarial correctness audit f82bd35: S/R cache leaked future (3,803/4,000 snapshots), inverted news blackout, fib mirror bug - fixed at 5583805 | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/confluence/news_macro.md` | econ_calendar audit: FOMC rule reproduced 52/72 decisions + 20 phantom; fixed to published dates; core PCE 6/15; 2025-26 shutdown breaks schedule | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/confluence/reversion_specialist.md` | Synthetic review of profile/zone/fib conditions: poc_reversion 61.6% unreachable, lvn empty 34/59, zone_touch not a sweep relabel, no level-referenced exits | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/confluence/strategy_research.md` | Synthetic audit of 21 new conditions: WF OOS -0.120R t -3.04; value_area_breakout = prior_day_breakout (J 0.831); news filters byte-identical 124/126 | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `research/confluence/trend_specialist.md` | Synthetic trend-seat review: fib leg is a bounding box, imbalance_pullback has no pullback (+0.219 vs -0.016 ATR with real retrace), FIB/SD 6 and 1 rankable per 400 | superseded synthetic-data seat report; findings captured in agent2_research.md |
| `workspace/bigscan/rerun.txt` | 46 queued cells for MZC/MZS/MZW/QQQ/SPY; no results for QQQ/SPY exist in lane | one-off job list |
| `workspace/chrono/FINDINGS.md` | No chronological chaining (MGC/MNQ/MES daily); says 'thirteen groups' (actually 6/4/3); MGC daily roll-contaminated | superseded by scan_reports ranking report Part C; captured |
| `workspace/chrono/MCL_60.log` | 5 one-line logs: strategies/trades/months per ledger (e.g. MGC 60m 5,443 strategies, 15,657 trades, 11 months) | raw run logs |
| `workspace/chrono/MES_1440.log` | 5 one-line logs: strategies/trades/months per ledger (e.g. MGC 60m 5,443 strategies, 15,657 trades, 11 months) | raw run logs |
| `workspace/chrono/MES_60.log` | 5 one-line logs: strategies/trades/months per ledger (e.g. MGC 60m 5,443 strategies, 15,657 trades, 11 months) | raw run logs |
| `workspace/chrono/MGC_60.log` | 5 one-line logs: strategies/trades/months per ledger (e.g. MGC 60m 5,443 strategies, 15,657 trades, 11 months) | raw run logs |
| `workspace/chrono/MNQ_1440.log` | 5 one-line logs: strategies/trades/months per ledger (e.g. MGC 60m 5,443 strategies, 15,657 trades, 11 months) | raw run logs |
| `workspace/chrono/ledgers` | 6 ledgers (MCL_60, MES_60/1440, MGC_60/1440, MNQ_1440): month -> group -> list of trade R | raw result dump |
| `workspace/developer` | ef1_saturation.json (0 violations 40 runs), ef1_prefix_invariance.json, ef1_validation_swing_60m.json | EF1 validation artefacts, cited by EF1 FINDINGS |
| `workspace/focus/cells.txt` | 39 (symbol, tf, window-days) cells MGC/MES/NQ for the old focus ranking corpus | orphan cell list; focus/cells dir and all_rows.json referenced by studies/toolkit.py are absent |
| `workspace/newstrats/analyse.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/analyse_orb_w2.py` | Analysis of the worker-2 ORB census: joint distribution, paired arms, OOS. | one-off driver/analysis; findings captured |
| `workspace/newstrats/analyse_wf.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/analyze.py` | Per-cell analysis of the geometry experiment. | one-off driver/analysis; findings captured |
| `workspace/newstrats/census.py` | Firing-rate + geometry census. No strategies, no exits - just how often each | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_analyse.py` | Per-cell paired ablation.  No T.ab anywhere (defect D28). | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_bias.py` | Bias audit: look-ahead, repainting, cost understatement, fill realism. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_census.py` | Floor-free census of the ICT sequence.  Counts first, performance later. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_jaccard.py` | Bar-level identity check against the library. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_lift.py` | Is the sequence a mechanism, or two independent events that sometimes land near each other? | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_lift2.py` | The lift, with the mechanical confound removed. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_limit.py` | The strongest objection to this study's negative verdict, tested rather than argued. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_mtf.py` | Multi-timeframe: higher-timeframe liquidity, lower-timeframe entry. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_perf.py` | Ablation backtest of the ICT sequence, out of sample by construction. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_publish.py` | Publish the three deliverables. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_regime.py` | Where, when and in what regime the full chain's trades happen - and whether it matters. | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_sens.py` | Parameter sensitivity: how many bars may elapse between the sweep and the MSS? | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_time.py` | ICT time-of-day (kill zones) and Optimal Trade Entry (OTE). | one-off driver/analysis; findings captured |
| `workspace/newstrats/ict_wf.py` | Walk-forward on the one thing a user of this idea would actually tune: the timing tolerance. | one-off driver/analysis; findings captured |
| `workspace/newstrats/leadlag_measure.py` | Measurement: does the lower timeframe change structure before the higher one? | one-off driver/analysis; findings captured |
| `workspace/newstrats/oos_orb_w2.py` | Out-of-sample for every headline claim: 60/40 temporal split + 3 disjoint slices. | one-off driver/analysis; findings captured |
| `workspace/newstrats/publish.py` | Publish the geometry results into the three workspace files. | one-off driver/analysis; findings captured |
| `workspace/newstrats/robust_orb_w2.py` | Robustness: parameter sensitivity, cost sensitivity, regime split, and a | one-off driver/analysis; findings captured |
| `workspace/newstrats/robustness.py` | Anti-overfitting checks for the geometry conditions. | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_bt.py` | Matched arm comparison: early entry vs confirmation entry vs the incumbent. | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_freshness.py` | Driver for the structure-freshness / distance-to-invalidation study. | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_geometry.py` | Matched-arm experiment for swing geometry. | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_measure.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_orb_w2.py` | Worker-2 ORB census: firing rates first, then the joint (win, payoff, exp) distribution. | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_rank.py` | Worker 1's cells: MGC and MCL, 60m and 240m, four nested windows + three | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_rates.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_stress.py` | Parameter sensitivity + cost stress + a search-gap demonstration. | one-off driver/analysis; findings captured |
| `workspace/newstrats/run_wf.py` | Walk-forward (6 sequential disjoint blocks) + the 240m structure-signal shootout. | one-off driver/analysis; findings captured |
| `workspace/newstrats/save_arms.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/save_measure.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/save_mech.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/save_robust.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/save_wf.py` | driver/analysis script (no docstring) | one-off driver/analysis; findings captured |
| `workspace/newstrats/sensitivity.py` | Parameter sensitivity of the geometry conditions. | one-off driver/analysis; findings captured |
| `workspace/newstrats/store.py` | Incremental save under the single study id ``s_geometry``. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w4_arms.py` | Does trading the return to an order block / fair value gap pay, after costs? | one-off driver/analysis; findings captured |
| `workspace/newstrats/w4_audit.py` | Leakage audit. Every claim in the ICT studies rests on these being true. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w4_barlevel.py` | Bar-level test of the ICT claim itself, before any strategy is built. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w4_barlevel_oos.py` | The bar-level test again, split 60/40 in time. In sample, then out. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w4_freshness.py` | Does freshness matter - an untested block versus one price has already used? | one-off driver/analysis; findings captured |
| `workspace/newstrats/w4_perf.py` | Full statistics for the ICT block/gap conditions - the performance database. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w4_publish.py` | Publish the three deliverables for the ICT order-block / FVG study. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w4_rates.py` | Firing rates, bar-level Jaccard against the library, and parameter sensitivity. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_analyse.py` | Combine matched-arm cells: per-cell sign z, Stouffer, and a declared OOS split. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_arms.py` | Matched-arm harness: same bars, same base rule set, same exit, one thing swapped. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_bars.py` | Part A, step 1: BAR-LEVEL hour-of-day census, before any strategy exists. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_bars2.py` | Part A, step 2: the control that decides whether the ICT clock adds anything. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_deliver.py` | Publish the three deliverables, ranked on durability rather than on profit. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_fibbars.py` | The untested lead, tested the cleanest way first: golden pocket vs shallow | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_ict_time.py` | ICT time-of-day (kill zones) and Optimal Trade Entry (OTE). | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_publish.py` | Publication run: 6-fold walk-forward at 60m, full metric set, durability ranking. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_rates.py` | Firing rates and bar-level Jaccard overlap - before any performance number. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_robust.py` | Robustness report: the anti-overfitting audit, stated as what was checked and found. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_run_cost.py` | Cost control: rerun the hour census with the thin-book slippage tick removed. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_run_fib.py` | The only untested lead in the programme, given the out-of-sample test nobody ran. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_run_fibplacebo.py` | Rate-matched placebo for the fib bands. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_run_kz.py` | Part A, step 3: the kill zones as matched strategy filters. | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_run_placebo.py` | Count-matched placebo: does ANY 1-in-24 entry filter beat no filter? | one-off driver/analysis; findings captured |
| `workspace/newstrats/w6_store.py` | Incremental save for the ICT study. | one-off driver/analysis; findings captured |
| `workspace/newstrats/walkforward.py` | Anchored walk-forward: does picking the best geometry arm in-sample help next period? | one-off driver/analysis; findings captured |
| `workspace/paper/CALL/DECISIONS.md` | 39 priced decisions (foreclosed/marginal/realized) incl. cron UTC bug, stand-down costs, owner stop | session decision log; lessons extracted |
| `workspace/paper/CALL/NOTES.md` | Chronological findings N1-N264 of the live CALL desk 2026-09-27..29 | session notes (10,325 lines); durable content extracted to DATA_HUB/_sweep/agent3_desks.md and FINDINGS_INDEX.md; keep as N-number source |
| `workspace/paper/CALL/bias_history.jsonl` | 1,578 rows of per-frame headlines per check 2026-09-28..29 | runtime log appended per regime.py call; held-counter counts invocations (N248); regime.py works without it |
| `workspace/paper/CALL/card_MGC_CALL-0002.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MGC_CALL-0004.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MGC_CALL-0007.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MGC_CALL-0009.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MGC_CALL-0011.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MNQ_CALL-0001.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MNQ_CALL-0005.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MNQ_CALL-0006.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MNQ_CALL-0008.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_MNQ_CALL-0010.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_STATUS.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_blank_LONG.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/card_blank_SHORT.png` | Callout cards CALL-0001,2,4,5,6,7,8,9,10,11, STATUS, blank LONG/SHORT | rendered card images (13 PNGs), regenerable by card_png.py/status_card.py |
| `workspace/paper/CALL/confluence.py` | evaluate plan vs 13 strategy families + levels() | early one-off 13-family disagreement tool; superseded |
| `workspace/paper/CALL/data` | MGC/MNQ 1m(446 files each), 5m(474/470), 15m(414/411), 60m(101/100), 240m(46), 1440m(3); fetched 2026-09-27T18:15Z..2026-09-29T04:57Z; merged coverage 1m 09-20..09-29 00:47 ET, 15m 09-22..09-29 00:30, 60m 08-30..09-28 22:00 | raw fetch fragments: 2,960 delta snapshots (16MB) + fetch_manifest.json; deltas are the only copy of revisions, so archive whole dir, never prune |
| `workspace/paper/CALL/feed_lag.jsonl` | 5,488 rows symbol/frame/newest bar/lag_minutes | raw per-fetch lag log; summarised in N7/N57/N60 (median 12.9 min at 5m) |
| `workspace/paper/CALL/standdown_cost.txt` | 'BOTH ATRs CLEAR - the vetoes are off...' | stale one-line status text read by status_card.py |
| `workspace/paper/CALL/vol1.py` | pivot-bar volume vs forward direction, 200-draw placebo | one-off VOL-1 test (null, N221) |
| `workspace/paper/REPLAY/R1/NO_TRADE.jsonl` | 1 NO TRADE row at bar 40 (2024-10-08 11:00) | dead: burst-1 hand-written stand-down, superseded by harness callout R1-00001 |
| `workspace/paper/REPLAY/R1/agents/E5_raw.txt` | E5 raw printout | dead raw output mirror of E5_costs.py (regenerable) |
| `workspace/roundtable/DIVISION.md` | Manager division of 53 families across R1-R3 tracks, round-2 amendments | round-1 task division; process only |
| `workspace/roundtable/LEDGER.md` | Per-round context burn and rate-limit window type log | dispatch/rate-limit log |
| `workspace/roundtable/OPEN_QUESTIONS.md` | Researcher-to-researcher questions R1-Q1..R3-Q2 with collision note | routed Q&A, resolved or captured in md |
| `workspace/roundtable/PARKED.md` | Which agents parked (BT3,EF1,EF2,EF3), EF3-vs-EF7 holiday-flat disagreement, BT3 placebo self-correction | park state captured in md |
| `workspace/roundtable/PIPELINE.md` | Discovery->scope->sectioned research pipeline rules, PIPELINE sec4 obligations | process design only |
| `workspace/roundtable/REGISTRY.md` | ID naming rules; EF1-H*, EF6-H1..H4 component ids; msg filename rules | id registry for roundtable citations |
| `workspace/roundtable/THROTTLE.md` | Session-limit gating rules (ccr_promotional window, 850k cutoff) | stale rate-limit throttle note |
| `workspace/roundtable/backtest/BT1/ALGOS.md` | BT1-ALGO-1 absorption shape (vol>=2x, range<=1x); unmeasurable (2-41 fires/series) | captured |
| `workspace/roundtable/backtest/BT1/REQUESTS.md` | BT1 requests (store ruling, D37 scope, D38 guard) | process |
| `workspace/roundtable/backtest/BT1/VERIFY.md` | BT1 fidelity questions to R1 | fidelity ASKED, never ruled |
| `workspace/roundtable/backtest/BT1/bursts` | absorption shape burst | burst log |
| `workspace/roundtable/backtest/BT1/code/frequency.py` | absorption frequency census | one-off |
| `workspace/roundtable/backtest/BT2/ALGOS.md` | BT2-ALGO-1 scheduled-event gate on MGC/MCL; in-session HIGH events MGC 32/69, MCL 49/164; no backtest | captured |
| `workspace/roundtable/backtest/BT2/REQUESTS.md` | BT2 requests | process |
| `workspace/roundtable/backtest/BT2/VERIFY.md` | BT2 fidelity questions to R2 | fidelity ASKED |
| `workspace/roundtable/backtest/BT2/bursts` | event gate burst | burst log |
| `workspace/roundtable/backtest/BT3/REQUESTS.md` | BT3 requests (D44 block bootstrap, dump fields) | process |
| `workspace/roundtable/backtest/BT3/VERIFY.md` | BT3 fidelity log | fidelity cycle 2 unanswered |
| `workspace/roundtable/backtest/BT3/bursts` | governor replay cycles 1-2, placebo threshold correction | burst log |
| `workspace/roundtable/backtest/BT3/code/algo1_report.json` | governor replay report | raw output |
| `workspace/roundtable/backtest/BT3/code/block_vs_iid.json` | block vs iid numbers | raw output, D44-biased |
| `workspace/roundtable/backtest/BT3/code/block_vs_iid.py` | block vs iid bootstrap comparison | one-off, runs on D44-biased bootstrap |
| `workspace/roundtable/backtest/BT3/code/paired_tests.json` | paired test results | raw output |
| `workspace/roundtable/backtest/BT4/ALGOS.md` | BT4-ALGO-1 daily-frame reduction: FRAMES[1440] self-confirms; rule-2 leave-1440-out | captured (D50, rule2 z -4.09 -> -3.05) |
| `workspace/roundtable/backtest/BT4/REQUESTS.md` | BT4 requests | process |
| `workspace/roundtable/backtest/BT4/VERIFY.md` | BT4 fidelity log | fidelity ASKED |
| `workspace/roundtable/backtest/BT4/bursts` | align_bucket collapse burst | burst log |
| `workspace/roundtable/backtest/BT4/code` | daily_mtf_reduction, regime_lag_at_1440, rule2_leave_1440_out, stores_at_1440, tf1440_census + json | one-off; regression in tests/test_bt4_align_bucket.py |
| `workspace/roundtable/backtest/BT5/ALGOS.md` | BT5-ALGO-1 activity stratification: bar-level footprint large, strategy-level dE +0.018R p 0.58 | captured (activity strat null) |
| `workspace/roundtable/backtest/BT5/REQUESTS.md` | BT5 requests | process |
| `workspace/roundtable/backtest/BT5/VERIFY.md` | BT5 fidelity log | fidelity ASKED |
| `workspace/roundtable/backtest/BT5/bursts` | activity strata burst | burst log |
| `workspace/roundtable/backtest/BT5/code/s2_report.json` | S2 report | raw output |
| `workspace/roundtable/backtest/BT6/ALGOS.md` | BT6-ALGO-1: daily VWAP band sub-tick 100%, vwap_band1_bounce 0 fires, 2,126 zero-trade daily strategies | captured (D52 daily VWAP collapse) |
| `workspace/roundtable/backtest/BT6/REQUESTS.md` | BT6 requests incl MGC_1440 splice discovery | process |
| `workspace/roundtable/backtest/BT6/VERIFY.md` | BT6 fidelity log | fidelity |
| `workspace/roundtable/backtest/BT6/bursts` | daily VWAP collapse + blast radius | burst log |
| `workspace/roundtable/backtest/BT6/code` | vwap_daily_census.py, vwap_blast_radius.py | one-off; regression in tests/test_bt6_vwap_daily.py |
| `workspace/roundtable/backtest/BT6/out` | vwap_daily_census.json, vwap_blast_radius.json | raw output |
| `workspace/roundtable/check_refs.py` | Fails commit if a msgs/ file lacks RE: header | roundtable msgs lint, one-off process tool |
| `workspace/roundtable/discovery/AVENUES.md` | 69 strategy-family avenues (I-*,II-*,III-*,X-*) with OPEN/CLOSED/DEFERRED status and blockers | avenue ledger; open avenues summarised in md sec3/8 |
| `workspace/roundtable/discovery/MAIN_TASKS.md` | MAIN-01: are nulls a wall-clock-bar artefact (volume/range bars) | MAIN-01 sampling-clock task; answered null by BT5 |
| `workspace/roundtable/discovery/bursts` | Discovery seed burst: csv/raw span per tf (1m=5d, 5m=27d, 15/30m=58d, 1h=322d) | burst log |
| `workspace/roundtable/discovery/claims` | DISC2 claim on II-7 cross-sectional momentum | claim marker |
| `workspace/roundtable/discovery2/AVENUES.md` | DISC2: II-7 blocker lifted (25.7y daily reachable), Lo t=SR*sqrt(y), free_t single-hypothesis 1.177 | span arithmetic captured in BRIEF/md |
| `workspace/roundtable/discovery2/MAIN_TASKS.md` | MAIN-02: 25-year ten-sector daily cross-section; blocked on roll audit and ContractSpecs | MAIN-02 proposal, not run |
| `workspace/roundtable/discovery2/bursts` | DISC2 cross-sectional universe probe (row counts, spans) | burst log |
| `workspace/roundtable/edge/EDGE_BRIEF.md` | Owner request: top 10 swing/scalp per symbol within 18:00-16:00 ET; guardrails | edge programme brief |
| `workspace/roundtable/edge/EF1/FINDINGS.md` | EF1 session harness: components H1-H10, defects D3/D4 fixed, 240m expressible, 59.6-86.3% clock closes | captured in md sec5/6 |
| `workspace/roundtable/edge/EF1/bursts` | EF1 bursts 1-5: boundary geometry, known-answer tests, 33 early-close violations, saturation, park | burst log |
| `workspace/roundtable/edge/EF2/FINDINGS.md` | EF2 swing MGC/MCL 60m: populations 3156/3408, VOID census, D45 extends to STRUCTURE, 93.3%/89.5% completeness | no profitability numbers; facts captured |
| `workspace/roundtable/edge/EF2/bursts` | EF2 bursts 1-13: session arithmetic, census, population, stop fidelity, flat reachability, roll calibration, 240m withdrawal | burst log |
| `workspace/roundtable/edge/EF2/code` | EF2 census/firecount/population/rank/plan/calibrate_roll/flat_reachability/weekend_gap scripts | one-off census/population scripts |
| `workspace/roundtable/edge/EF2/data` | EF2 JSON outputs: census, firecount, population (17MB), calibrate_roll, flat_reachability, weekend_gap | raw outputs (17MB population.json) |
| `workspace/roundtable/edge/EF3/FINDINGS.md` | EF3 swing MES/MNQ 60m: populations, 17.79% MNQ VOID via openinterest, engine reconciliation; embargoed ledger | captured in md |
| `workspace/roundtable/edge/EF3/bursts` | EF3 bursts 1-6: substrate, census, population, pre-registered protocol, harness reconciliation | burst log |
| `workspace/roundtable/edge/EF3/code/ef3_census.py` | EF3 79-condition firing census | one-off |
| `workspace/roundtable/edge/EF3/code/ef3_measure.py` | EF3 stage-1 measurement runner | one-off |
| `workspace/roundtable/edge/EF3/code/ef3_population.py` | EF3 population builder seed 20260922 | one-off |
| `workspace/roundtable/edge/EF3/code/ef3_stopcensus.py` | D45 floor rate census MES/MNQ | one-off |
| `workspace/roundtable/edge/EF3/code/ef3_substrate.py` | archive vs csv/raw equivalence check MES/MNQ | one-off |
| `workspace/roundtable/edge/EF3/out/census_MES.json` | MES condition census | raw output |
| `workspace/roundtable/edge/EF3/out/census_MNQ.json` | MNQ condition census | raw output |
| `workspace/roundtable/edge/EF3/out/population_4000.json` | population summary | raw output |
| `workspace/roundtable/edge/EF3/out/stopcensus.json` | D45 floor rates 15.38% MES / 7.47% MNQ | raw output |
| `workspace/roundtable/edge/EF4/bursts` | EF4 bursts 1-7: power bound, cost in R, census, degeneracy, population, measurement, anti-overfitting audit | burst log, captured in FINDINGS |
| `workspace/roundtable/edge/EF4/code/analyse.py` | rule-7 share-positive analysis | one-off |
| `workspace/roundtable/edge/EF4/code/analyse2.py` | split-sample selection analysis | one-off |
| `workspace/roundtable/edge/EF4/code/census.py` | 79x8 firing census | one-off |
| `workspace/roundtable/edge/EF4/code/mtf_arms.py` | paired MTF alignment test | one-off |
| `workspace/roundtable/edge/EF4/code/or_resolvability.py` | opening-range placement check | one-off |
| `workspace/roundtable/edge/EF4/code/population.py` | Track A/B population declaration | one-off (defines Track A arms A1-A6) |
| `workspace/roundtable/edge/EF4/code/power.py` | power bound per cell | one-off |
| `workspace/roundtable/edge/EF4/code/rank_final.py` | de-duplicated final ranking | one-off |
| `workspace/roundtable/edge/EF4/code/selection_direction.py` | long/short-only selection control | one-off |
| `workspace/roundtable/edge/EF4/code/session_clock.py` | EF4 independent session clock | one-off second harness for diff-check |
| `workspace/roundtable/edge/EF4/code/trim_out.py` | trims run outputs to summaries | one-off |
| `workspace/roundtable/edge/EF4/out` | run_*_summary.json per-arm metrics (19k arms), placebo_*.json, rank_final, cost_in_r, census, audits | raw outputs (54MB); key numbers captured in md sec2.1/2.2/3.2 |
| `workspace/roundtable/edge/EF5/bursts` | EF5 bursts 1-11: power, census, D45, population, cost share, MNQ15 SESSION stress, universe, pooled table | burst log; captured in md sec2.3/2.4 |
| `workspace/roundtable/edge/EF5/code/census.py` | EF5 census | one-off |
| `workspace/roundtable/edge/EF5/code/cost_share.py` | cost share per cell | one-off |
| `workspace/roundtable/edge/EF5/code/d45_vwap_band.py` | D45 at 5/15/30m MES/MNQ | one-off |
| `workspace/roundtable/edge/EF5/code/ef5_data.py` | loader | one-off |
| `workspace/roundtable/edge/EF5/code/eliminate.py` | VOID elimination | one-off |
| `workspace/roundtable/edge/EF5/code/exit_census.py` | exit and direction census | one-off |
| `workspace/roundtable/edge/EF5/code/floor_feasibility.py` | top-10 floor feasibility | one-off |
| `workspace/roundtable/edge/EF5/code/measure.py` | EF5 main measurement | one-off |
| `workspace/roundtable/edge/EF5/code/population.py` | population builder | one-off |
| `workspace/roundtable/edge/EF5/code/stress_mnq15_session.py` | first MNQ15 stress incl leaky holdout | one-off (superseded by stress2) |
| `workspace/roundtable/edge/EF5/code/universe.py` | qualifying-universe table | one-off |
| `workspace/roundtable/edge/EF5/code/verify_census.py` | census cross-check | one-off |
| `workspace/roundtable/edge/EF5/out` | PROVISIONAL_measure_all.json (per-cell tables incl placebos), universe, census, elimination, stress outputs | raw outputs; captured in md |
| `workspace/roundtable/edge/EF6/bursts` | EF6 bursts 1-7: deflation, window expressibility, placebo faults, prefilter, forward roll, top-10 attack, scalp forward test | burst log; captured in md/RESULTS |
| `workspace/roundtable/edge/EF6/code/analyse_census.py` | census analysis | one-off |
| `workspace/roundtable/edge/EF6/code/probe_placebo.py` | placebo fault probe | one-off |
| `workspace/roundtable/edge/EF6/code/run_attack_demo.py` | MGC 60m top-10 attack demo | one-off |
| `workspace/roundtable/edge/EF6/out` | census/ (40 cell censuses), ledgers MGC/MCL/MES/MNQ 60m+15m, roll_*.json, attack_MGC_60m, void_table (3MB), prefilter_summary | raw outputs; captured in md |
| `workspace/roundtable/edge/EF7/FINDINGS.md` | EF7 independent harness: 0 violations, EF7-D2 12:30 entry-bar exit, EF7-D3, stale fill across gap, EF1 comparison | captured in md sec5/6 |
| `workspace/roundtable/edge/EF7/bursts` | EF7 bursts 1-7 | burst log |
| `workspace/roundtable/edge/EF7/code/compare_ac.py` | arm A vs C comparison | one-off |
| `workspace/roundtable/edge/EF7/code/measure.py` | closure counts | one-off |
| `workspace/roundtable/edge/EF7/code/population.py` | population-scale invariant run | one-off |
| `workspace/roundtable/edge/EF7/compare_ac.json` | arm comparison | raw output |
| `workspace/roundtable/edge/EF7/invariant.json` | 0 violations 4 symbols | raw output |
| `workspace/roundtable/edge/EF7/measure.json` | closure counts | raw output |
| `workspace/roundtable/edge/EF7/population.json` | population invariant | raw output |
| `workspace/roundtable/manager/ADJUDICATIONS.md` | Manager rulings ADJ-0..ADJ-16: defect allocations D44-D58, VOID vocabulary, rule-2 narrowing, edge-programme gate | rulings captured in md (defects D44-D58, ADJ-14 rule2, ADJ-15 edge gate) |
| `workspace/roundtable/manager/BOARD.md` | Standing rules R-1..R-13, MGR-T tasks, pre-registrations, edge programme constraints | task board, process |
| `workspace/roundtable/msgs` | 45 messages: fidelity verify threads (BT<->R), defect reports (D45,D48,D49), EF1-02 240m correction, EF4-01 stale fills, EF2 MCL data gap | inter-agent message log; conclusions captured |
| `workspace/roundtable/research/R1_REQUESTS.md` | R1 requests REQ-1..6 | process |
| `workspace/roundtable/research/R1_data_requirements.md` | Class I data requirements vs csv header | data ledger |
| `workspace/roundtable/research/R1_flow_auction.md` | Class I families I-1..I-15, phantom groups orderflow/openinterest/news, TPO opening/day types with per-symbol day-type frequencies | Class I catalogue; level/profile/VWAP/day-type content captured in md sec3 |
| `workspace/roundtable/research/R2_REQUESTS.md` | R2 requests | process |
| `workspace/roundtable/research/R2_expressibility_wall.md` | Two walls: one SymbolFrame per backtest (Wall A) and one-position spread (Wall B) | catalogue |
| `workspace/roundtable/research/R2_recut_contingency.md` | R2-Q1 recut consequences | process |
| `workspace/roundtable/research/R2_relational.md` | II-1..II-19 families, seasonality power arithmetic, event inventory (HIGH calendar mostly outside RTH) | Class II catalogue |
| `workspace/roundtable/research/R3_REQUESTS.md` | R3 requests | process |
| `workspace/roundtable/research/R3_operating_vocabulary.md` | Operating-axis matrix (entry, risk, size, management, exit, re-entry, portfolio, roll) | catalogue |
| `workspace/roundtable/research/R3_pairing_design.md` | D15 paired re-emission design, R3-A-13 replace/_id hazard | design, not run |
| `workspace/roundtable/research/R3_path_operation.md` | Trailing stop never ran, TRAIL unreachable, dead knobs, sizing channels, run_portfolio not a portfolio, III-1..III-19 | Class III + engine facts; captured in md sec5 |
| `workspace/roundtable/research/R4_REQUESTS.md` | R4 requests | process |
| `workspace/roundtable/research/R4_group_audit.md` | R4 audit: D54 volume, MACD dup, bollinger subset, volatility misnamed, regime tf-inert, MTF at 240/1440 | second audit of 7 groups; key items in md |
| `workspace/roundtable/research/R5_SCOPE.md` | Sampling-clock scope, 1m substrate ~6.6 days, D51 BarSeries collapse | MAIN-01 scope; answered by BT5 |
| `workspace/strategy_research/ict_blocks_fvg_performance_db.json` | performance_db: ICT OB/FVG study: firing rates, sham touch rates, paired arms IS/OOS, 387 rule sets ranked by durability (placebo OB ranks 2nd) | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/ict_blocks_fvg_robustness_report.json` | robustness_report: ICT OB/FVG study: firing rates, sham touch rates, paired arms IS/OOS, 387 rule sets ranked by durability (placebo OB ranks 2nd) | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/ict_blocks_fvg_strategy_rankings.json` | strategy_rankings: ICT OB/FVG study: firing rates, sham touch rates, paired arms IS/OOS, 387 rule sets ranked by durability (placebo OB ranks 2nd) | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/ict_killzones_ote_performance_db.json` | performance_db: Kill zones + OTE: hour census, 24-hour placebo, 206 rule sets 6-fold WF, 0 live-eligible, best deflated t -0.80 | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/ict_killzones_ote_robustness_report.json` | robustness_report: Kill zones + OTE: hour census, 24-hour placebo, 206 rule sets 6-fold WF, 0 live-eligible, best deflated t -0.80 | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/ict_killzones_ote_strategy_rankings.json` | strategy_rankings: Kill zones + OTE: hour census, 24-hour placebo, 206 rule sets 6-fold WF, 0 live-eligible, best deflated t -0.80 | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/ict_sweep_mss_performance_db.json` | performance_db: Sweep->MSS->retrace: census, lift/MH odds ratios, 6-arm ablation, wrong-order and 5-bar placebo, WF tuning bias | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/ict_sweep_mss_robustness_report.json` | robustness_report: Sweep->MSS->retrace: census, lift/MH odds ratios, 6-arm ablation, wrong-order and 5-bar placebo, WF tuning bias | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/ict_sweep_mss_strategy_rankings.json` | strategy_rankings: Sweep->MSS->retrace: census, lift/MH odds ratios, 6-arm ablation, wrong-order and 5-bar placebo, WF tuning bias | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/leadlag_performance_db.json` | performance_db: LTF->HTF lead (6-17 bars), false-positive 78-81%, strategy arms null, BOS@240 retraction | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/leadlag_robustness_report.json` | robustness_report: LTF->HTF lead (6-17 bars), false-positive 78-81%, strategy arms null, BOS@240 retraction | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/leadlag_strategy_rankings.json` | strategy_rankings: LTF->HTF lead (6-17 bars), false-positive 78-81%, strategy arms null, BOS@240 retraction | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/nested_performance_db.json` | performance_db: Nested pullback/resumption: 17 bases x 8 arms x 14 frames, IS/OOS, depth, tf pair, distinctness | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/nested_robustness_report.json` | robustness_report: Nested pullback/resumption: 17 bases x 8 arms x 14 frames, IS/OOS, depth, tf pair, distinctness | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/nested_strategy_rankings.json` | strategy_rankings: Nested pullback/resumption: 17 bases x 8 arms x 14 frames, IS/OOS, depth, tf pair, distinctness | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/orb_test_performance_db.json` | performance_db: ORB 1,920 configs 194k trades per symbol (deep/raw), payoff-win cancellation, yesterday-range placebo, top-30 NOT endorsed | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/orb_test_robustness_report.json` | robustness_report: ORB 1,920 configs 194k trades per symbol (deep/raw), payoff-win cancellation, yesterday-range placebo, top-30 NOT endorsed | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/orb_test_strategy_rankings.json` | strategy_rankings: ORB 1,920 configs 194k trades per symbol (deep/raw), payoff-win cancellation, yesterday-range placebo, top-30 NOT endorsed | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/performance_db.json` | byte-identical duplicate of rank_w2_performance_db.json (8.3 MB) | duplicate raw dump |
| `workspace/strategy_research/rank_mgc_mcl_performance_db.json` | performance_db: Worker 1 ranking MGC/MCL 60/240 (28 cells incl. thirds): placebo ranks, disjoint replication, fill/cost/power audits | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_mgc_mcl_robustness_report.json` | robustness_report: Worker 1 ranking MGC/MCL 60/240 (28 cells incl. thirds): placebo ranks, disjoint replication, fill/cost/power audits | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_mgc_mcl_selftest.json` | selftest: Worker 1 ranking MGC/MCL 60/240 (28 cells incl. thirds): placebo ranks, disjoint replication, fill/cost/power audits | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_mgc_mcl_strategy_rankings.json` | strategy_rankings: Worker 1 ranking MGC/MCL 60/240 (28 cells incl. thirds): placebo ranks, disjoint replication, fill/cost/power audits | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_nq_es_grains_performance_db.json` | performance_db: Worker 3 ranking NQ/ES/MZC/MZS/MZW 60/240: deflation per cell (max t 3.923 NQ 60m 180d), grains data audit (D40), D24 RTH arm | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_nq_es_grains_robustness_report.json` | robustness_report: Worker 3 ranking NQ/ES/MZC/MZS/MZW 60/240: deflation per cell (max t 3.923 NQ 60m 180d), grains data audit (D40), D24 RTH arm | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_nq_es_grains_strategy_rankings.json` | strategy_rankings: Worker 3 ranking NQ/ES/MZC/MZS/MZW 60/240: deflation per cell (max t 3.923 NQ 60m 180d), grains data audit (D40), D24 RTH arm | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_persistence_performance_db.json` | performance_db: Pooled ranking persistence (all workers) + mgc_mcl_rescope verdicts | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_persistence_robustness_report.json` | robustness_report: Pooled ranking persistence (all workers) + mgc_mcl_rescope verdicts | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_persistence_strategy_rankings.json` | strategy_rankings: Pooled ranking persistence (all workers) + mgc_mcl_rescope verdicts | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_w2_performance_db.json` | performance_db: Worker 2 ranking MES/MNQ 60/240: placebo in top 10, WF folds, MTF alignment paired | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_w2_robustness_report.json` | robustness_report: Worker 2 ranking MES/MNQ 60/240: placebo in top 10, WF folds, MTF alignment paired | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/rank_w2_strategy_rankings.json` | strategy_rankings: Worker 2 ranking MES/MNQ 60/240: placebo in top 10, WF folds, MTF alignment paired | raw result dump; findings captured in agent2_research.md |
| `workspace/strategy_research/robustness_report.json` | byte-identical duplicate of rank_persistence_robustness_report.json | duplicate raw dump |
| `workspace/strategy_research/strategy_rankings.json` | byte-identical duplicate of rank_persistence_strategy_rankings.json | duplicate raw dump |
| `workspace/strategy_research/w2/audit.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/cells` | MES/MNQ 60/240 x 30/90/180/274d + slices + rth cells, wf_*, mtf*_*, audit_{costs,lookahead,sens,tagblind} | raw result dump (~91 MB, tracked because the cells/ ignore rule is one level deep) |
| `workspace/strategy_research/w2/drive.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/mtf.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/mtf2.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/mtf3.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/publish.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/save_rest.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/tagblind.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/w2rank.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w2/wf.py` | w2rank (uses symbol profiles), drive, wf, mtf/mtf2/mtf3 (require_alignment), tagblind, audit, publish, save_rest | one-off worker-2 (MES/MNQ ranking) scripts; findings captured |
| `workspace/strategy_research/w3_audit.py` | Worker 3 audits: fill model, dollar arithmetic, costs, look-ahead, OOS, sensitivity. | one-off worker-3 driver/publisher; findings captured |
| `workspace/strategy_research/w3_cleanfeed.py` | Does the micro-grain data defect drive the micro-grain rankings? | one-off worker-3 driver/publisher; findings captured |
| `workspace/strategy_research/w3_publish.py` | Assemble worker 3's three published artefacts from the saved cells + audits. | one-off worker-3 driver/publisher; findings captured |
| `workspace/strategy_research/w3_rank.py` | Worker 3 — recurring profitability ranking for NQ, ES, MZC, MZS, MZW at 60m/240m. | one-off worker-3 driver/publisher; findings captured |
| `workspace/strategy_research/w3_rth.py` | D24 arm: the same rule sets with the RTH gate flipped off. | one-off worker-3 driver/publisher; findings captured |
| `workspace/strategy_research/w3_run.py` | Driver: one symbol's eight cells (60m/240m x 30/90/180/274d) plus replication. | one-off worker-3 driver/publisher; findings captured |
| `workspace/strategy_research/w3_summary.py` | Compact console summary of every cell, for the written report. | one-off worker-3 driver/publisher; findings captured |
| `workspace/studies/BRIEF.md` | Study-programme brief: use toolkit, T.ab, deflation, minimum coverage (MGC/MES/NQ x 240/60 x 274/180/90) | one-off agent brief |
| `workspace/studies/BRIEF_ORB_ICT.md` | ORB/ICT brief: known prior measurements table, paired tests (D28), firing rates, Jaccard, OOS rules | one-off agent brief |
| `workspace/studies/BRIEF_RANKING.md` | Top-10 ranking brief: placebo cohort required in every cell | one-off agent brief |
| `workspace/studies/BRIEF_STRUCTURE.md` | Structure-studies brief: full paired/OOS method; several priors in it measured backwards | one-off agent brief |
| `workspace/studies/ORB_ICT_FINDINGS.md` | 6 ORB/ICT studies in full (firing rates, sham zones, sweep chain, kill zones, OTE alias); still carries unretracted 'nulls are real absence' and 'NQ=MNQ' lines | detail superseded by scan_reports/2026-09-24_ORB-and-ICT.md; captured |
| `workspace/studies/RANKING_FINDINGS.md` | Top-10 ranking: 112-cell placebo counts, nested overlap, disjoint thirds, realised roll, worker 1/2 detail, MGC+MCL re-scope | detail superseded by scan_reports ranking report; captured |
| `workspace/studies/aggregate_studies.py` | Merges workspace/studies/out/*.json (gitignored, absent) into merged.json | one-off merger |
