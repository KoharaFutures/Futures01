# Roundtable: the futures strategy universe, and how to use each one effectively

Every agent in this roundtable reads this file first, in full, before doing anything else.

## The job

Build the **catalogue this repository does not have**: what futures trading strategies exist,
how each is actually operated, and which of them this library can and cannot express.

This is *not* another ranking run. Three million backtest evaluations have already been spent
and the verdict is settled (below). What is missing is the map: the strategy space itself, the
mechanics of using each family well, and an honest note on where our harness is blind to it.

## What the research already established — do not re-litigate this

- **~2,975,629 strategy evaluations. Nothing is live-eligible.** Not one strategy has ever
  cleared its own multiple-testing threshold. Programme-wide `free_t = 5.46`; largest t
  anywhere = **3.923**.
- Placebo entries (random bars run through the base's own exits, filters and sizing) rank
  alongside real signals. Five separate placebo constructions matched or beat the real thing.
- Trading last period's top 10 returns **−0.0155R** against a **−0.0104R** null, and
  **underperforms trading the whole qualifying universe**. Selecting is worse than not selecting.
- No chronological chaining of strategy groups exists, on any symbol.
- Full detail: `workspace/studies/RANKING_FINDINGS.md`, `workspace/chrono/FINDINGS.md`,
  `scan_reports/2026-09-24_MGC-MCL_ranking-persistence-and-chronology.md`.

**So the value of this roundtable is descriptive and diagnostic, not a search for edge.** A
finding of the form "this family is widely used and our harness cannot express it" is worth
more than another expectancy table.

## The eight rules that came out of our own measurements

Any claim contradicting one of these needs evidence, not assertion:

1. **Two signals and one filter is the ceiling.** 2→4 signals cuts trade count 35% and does
   not improve expectancy; the sign favours two.
2. **Multi-timeframe agreement is not a virtue.** Requiring any alignment measured detectably
   *worse* than requiring none (z = −4.09). On a two-timeframe frame, "majority" and
   "unanimous" are the same statement (D17).
3. **Win rate and payoff cancel.** Moving a stop from structure to a wider ATR raises payoff
   ~89% and drops win rate ~14 points for *no* expectancy gain. Measured four separate times.
4. **Structural stops: never tighter than ~0.5 ATR.**
5. **No intraday entries 15:00–16:00 ET** (z = −4.43, median −0.617R, replicated).
6. **No hours filter improves expectancy.** The lunch-avoidance folk claim is refuted.
7. **Sub-hourly is a graveyard.** At 5 minutes, 11–16% of strategies make money.
8. **ORB and ICT do not pay here.** Yesterday's opening range beats today's; FVG and
   order-block fill rates are reproduced by random zones; the ICT sweep→shift→retrace
   sequence is real, common, and adds nothing over its parts.

## What the library currently holds

**Two taxonomies, and an earlier version of this brief conflated them.** They are different
things and the distinction matters — R1's track in particular turns on it:

- **13 *strategy* groups**, the uppercase labels the combinator assembles into
  (`futures_agents/strategies/combinator.py`, `group="..."`): BREAKOUT, FIBONACCI, LIQUIDITY,
  MEAN_REVERSION, MOMENTUM, MULTI_TIMEFRAME, OPENING_RANGE, PULLBACK, REVERSAL, SUPPLY_DEMAND,
  TREND, VOLUME_PROFILE, VWAP. These are what every `scan_reports/` result is grouped by.
- **19 *condition* groups**, the lowercase tags on the 79 conditions
  (`futures_agents/strategies/library.py` → `CONDITIONS`, a dict of 79): candlestick,
  fibonacci, imbalance, liquidity, meanreversion, momentum, multitimeframe, news, openinterest,
  orderflow, profile, regime, structure, supplydemand, time, trend, volatility, volume, vwap.
  Measured split: **53 SIGNAL / 26 FILTER.**

Three of those condition groups name information the data does not contain — **`orderflow`,
`openinterest`, `news`** — while the CSV header is `open_time,open,high,low,close,volume`. Work
out what those conditions are actually computing from OHLCV before treating any of them as what
its name claims. This is a finding waiting to be written down, not a trap to avoid.
**Stops:** ATR, STRUCTURE, FIXED_TICKS, VWAP_BAND, RANGE.
**Targets:** R_MULTIPLE, ANCHOR_ATR, ANCHOR_STRUCTURE.

**Data, and a correction to an earlier version of this brief.** Two stores now exist:

- `csv/raw/` — 48 files, ending 2026-09-22. **READ ONLY. Never delete or edit any file under
  `csv/`, no matter what.** This is the snapshot every published result in `scan_reports/` was
  measured on, so it stays frozen for reproducibility.
- `data/archive/` — 29 JSONL series, ~157,000 bars, added 2026-09-26 by the live-callout
  session. **Newest bar 2026-09-25T16:00-04:00**, and ~11,300 hourly bars per symbol (60m back
  to 2024-10-06) against the 274 days the `csv/raw` hourly files carry. Append-only.

**An earlier version of this brief said "there is no live data feed; egress to every
market-data vendor is blocked at the proxy." That is now false and was corrected on 2026-09-27.**
Yahoo Finance is reachable: `futures_agents/data/yahoo.py`, verified by the 157k-bar pull above.
Treat any claim in this repo's older prose about unreachable data as suspect and check it.

Vendor caveats already measured, which you should not rediscover the hard way: futures need the
`=F` suffix; every interval has a hard lookback cap (1m exists for 7 days only) and asking for
more returns an empty frame *with no error*; Yahoo has no native 3m or 4h bar, so our 240m
framework is resampled from a finer interval; **MCL has no daily history on this vendor** (one
row, not an error) and full-size `CL=F` is NOT a substitute — across 109 overlapping hourly bars
the closes differ 0.95 cents on average and 4 cents at worst, fine for context and not fine for
an entry or a stop. `MNQ=F` is not TradingView's `MNQ1!` — different vendor, different roll
convention, not interchangeable in a backtest.

**Contract independence is unchanged by any of this.** MGC and MCL are the only genuinely
independent, clean contracts. MES/MNQ/NQ/ES are one index complex (they share 0.5–0.8% of rule
sets — D14/D41), so agreement between them is *not* corroboration. The grain CSVs splice
contract months (D40) — excluded.

## Known-broken machinery — read before trusting any number a tool here prints

`workspace/studies/DEFECTS.md` catalogues D1–D43. Open at the time of writing: **D21** (the
session-scale guard never reaches 4h), **D24** (`rth_only=False` buys sample and costs
expectancy — the opposite of what an earlier brief of mine claimed), **D36**, **D37** (the
combinator cannot express a sequence at all), **D38** (`toolkit.measure_custom` silently zeroes
custom conditions), **D39**, **D40**.

**D28: `T.ab` inflates z by roughly 3.3×.** Route comparative claims through a paired test with
the correlation accounted for, and say which test you used.

## Hard rules for every agent here

1. **Write to disk as you go, not at the end.** This session has already been compacted once
   and had its container restarted once. An insight that exists only in your reply can be lost.
   Append to your own file under `workspace/roundtable/research/` after each substantive finding.
2. **Cite by path and line.** `file.py:123`. A claim about this repo with no path is an opinion.
3. **Separate what you know from what you measured.** Mark every claim `[general knowledge]`,
   `[repo-verified: path]`, or `[measured: command + result]`. Reviewers need the difference.
4. **Report absence as a result.** "This family cannot be expressed by the combinator" is a
   finding. Do not manufacture a positive.
5. **No new backtest sweeps** unless the manager assigns one. Reading existing artefacts and the
   code is the work. If you do run something, keep it small and state the exact command.
6. Do not commit or push. The parent session handles git.

## How the conversation works

You cannot call each other directly. The parent session relays, and the manager coordinates.

- `workspace/roundtable/msgs/` — the conversation log. One file per message, named
  `NN_from_to_topic.md` (e.g. `03_manager_r2_revise-scope.md`). Zero-padded, monotonic.
- `workspace/roundtable/research/` — the deliverables. One file per researcher, appended to.
- `workspace/roundtable/DIVISION.md` — the manager owns this: who has what, and why.
- `workspace/roundtable/OPEN_QUESTIONS.md` — anything a researcher wants another to answer.
  The manager routes these.

Read the whole `msgs/` directory before writing, so you are answering the current state of the
conversation rather than the state when you were launched.
