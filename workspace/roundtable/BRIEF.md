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

---

# Data policy — ruling on BT1-REQ-1 (2026-09-27)

**BT1-REQ-1 asked whether a backtester may measure on `data/archive/` rather than the frozen
`csv/raw/`.** It blocks measurement for every rare-signal algorithm all three backtesters will
build, so it is answered here rather than deferred to the board.

**Ruling: yes. Measure on `data/archive/` where you have verified the two stores agree for your
symbol AND timeframe.**

I checked the thing the ruling depends on — whether the two stores are even the same series,
since `csv/raw` was supplied as a zip and the archive was pulled from Yahoo. They are:

| symbol | archive 60m | csv/raw 60m | overlap | closes **bit-exact** | max abs close diff | archive-only bars |
|---|---|---|---|---|---|---|
| MGC | 11,297 | 5,000 | 4,987 | 1,063 / 4,987 | 3.437e-07 | 6,310 |
| MNQ | 11,291 | 5,000 | 4,988 | **4,988 / 4,988** | 0.0 | 6,303 |
| MES | 11,287 | 5,000 | 4,988 | **4,988 / 4,988** | 0.0 | 6,299 |
| MCL | 10,934 | 5,000 | 4,987 | 221 / 4,987 | 4.824e-08 | 5,947 |

**Corrected 2026-09-27, by BT2-REQ-4.** An earlier version of this table claimed every
overlapping close was bit-identical and that `max |close difference|` was 0.0000 on all four.
Both were artefacts of how I measured: an identity test at tolerance `1e-6` counted 3.4e-07 as
identical, and `:.4f` formatting printed it as `0.0000`. **MNQ and MES are bit-exact; MGC and MCL
are not** — they differ by 3.4e-07 and 4.8e-08, which is float32 round-trip noise, three to five
millionths of a tick, immaterial to any fill but **fatal to an exact-equality assertion**. Volume
differs on 2 of ~4,987 bars for **all four** contracts, not for MGC alone; I had only printed
MGC's. The ruling below is unchanged — the series are the same series — but compare with a
tolerance, never with `==`.

So `csv/raw` is a 5,000-bar window of the same series the archive holds more of —
not a second vendor's version of it — and the archive extends the span by ~6,000 bars per symbol
**before** everything the programme has ever searched. That is the only genuine answer this
project has to its nested-window problem, where 30 ⊂ 90 ⊂ 180 ⊂ 274 days all end on the same bar.

## The three conditions

1. **State which store every number was measured on.** Never pool or compare an
   archive-measured row against a `csv/raw`-measured one without saying the samples differ.
2. **Verify equivalence for your own symbol and timeframe before relying on it.** The table above
   is 60m only. **MCL has no usable daily history on this vendor — `MCL_1440m.jsonl` holds
   exactly one row**, and full-size `CL=F` is not a substitute (0.95¢ mean close difference,
   4¢ at worst: fine for context, wrong for a stop). Do not assume the 60m result generalises.
3. **`csv/raw` stays frozen and read-only.** It is the reproducibility baseline for every result
   already published in `scan_reports/`. **Never delete or edit any file under `csv/`, no matter
   what.** `data/archive/` is append-only.

## The timezone trap, recorded because it cost me a wrong answer first

**`csv/raw` timestamps are `+00:00` (UTC). `data/archive/` timestamps are `-04:00` (ET.)**

My first comparison sliced the offset off and matched `16:00` against `16:00` — bars four hours
apart. It reported 4,588 overlapping stamps with **zero** identical closes and a mean difference
of 23.0 points, which on micro gold is $230 a contract. That number was entirely an artefact of
my own comparison, and it is exactly the shape of mistake that gets written into a report as a
vendor discrepancy. Normalise both sides to UTC before you compare anything across the two
stores, and if a cross-store difference looks large, suspect your own alignment first.

---

# D48 — scope correction (2026-09-27)

`D48` says `dataclasses.replace` on a `Strategy` inherits the memoised `_id`, so a paired
comparison built that way collides into one `BacktestResult` and the between-arm difference
measures exactly zero. **The mechanism is real and I verified it:**

```
original exit targets: (1.5, 3.0, 5.0)   strategy_id: MGC-60m-510cb40223fb
replaced exit targets: (3.0,)            strategy_id: MGC-60m-510cb40223fb   <- identical
```

`_id: Optional[str] = None` is a dataclass *field* (`base.py:585`) that `strategy_id` memoises
into (`:611-623`), and `replace()` copies fields — so once the id has been read even once, every
later `replace` carries the stale one forward.

**But no published result is affected, and the round-2 framing risks implying otherwise.** I
checked every `dataclasses.replace` call site on a `Strategy` in this repository — nine of them,
across `newstrats/placebo.py` (×2), `newstrats/rank.py`, `w2/mtf2.py` (×2), `w2/mtf3.py`,
`w2/w2rank.py`, `w3_rth.py` and `scratch/w4b_placebo.py` — and **every one passes `_id=None`
explicitly.** So this is a trap that every author so far has remembered to step over, not a
defect that corrupted anything already measured. No retraction is owed.

**What it actually is: a forward-looking hazard with no guard.** Nothing in the code or the test
suite stops the next author forgetting it, the failure is silent, and its signature — an
exact-zero difference between two arms — is indistinguishable from this programme's own settled
finding that operating axes do not move expectancy. That makes it the **fourth** mechanism by
which a "no effect" conclusion here could be an artefact rather than a result, and it lands
precisely where R3's paired re-emission design is about to build. It needs a regression test, not
a retraction.

# Wording the programme owes, per the manager's R1-Q2 ruling

"**2,975,629 strategies were tested**" overstates what happened. `openinterest` carriers were
generated into the population and could never trade, and they are a subset of the 82% of generated
strategies that never trade at all. The honest form is:

> **≥ 2,975,629 candidates were *generated*, of which an unmeasured subset could not trade.**

The deflation verdict is unchanged, and the bound was already on disk before anyone asked:
`RANKING_FINDINGS.md:66-72` records that discounting the non-traders gives an effective search of
~495k and `free_t = 5.15`, still uncleared. `free_t = sqrt(2·ln n)` is logarithmic, so removing
91% of the denominator only moves the threshold to 5.00, and *n* would have to fall to about
**2,197** before it met the largest t ever found here (3.923). Quote 5.46 with its 495k/5.15
companion, not alone.

---

# Shared audit vocabulary — and VOID, the term it was missing (2026-09-27)

`R1-REQ-5` is right: the vocabulary had no word for "cannot fire", and `DEGRADED` materially
understates a structurally-zero configuration. Adding one, binding on every agent:

| verdict | meaning |
|---|---|
| `CLEAN` | the arithmetic does what the group name claims |
| `PROXY` | it computes a correlate of the named object from data that cannot contain it |
| `DEGRADED` | it computes the named object, but with a loss that varies by symbol or timeframe |
| **`VOID`** | **it cannot fire in this configuration — 0 of N bars, structurally, not rarely** |
| `DEAD` | the inputs it gates on are absent everywhere, so it never fires anywhere |
| `MISNAMED` | it computes a different, well-defined thing than its name says |

**`VOID` is per (symbol, timeframe), never global**, and that is why it needed its own term.
Almost every zero found so far is conditional: `profile` VOID at 240m, MULTI_TIMEFRAME's signals
VOID at the frame's top timeframe, OPENING_RANGE VOID at 1h on three symbols, BREAKOUT +
`volatility_expanding` provably empty, `session_extreme_sweep` VOID under `rth_only=True`.

**Why it matters more than a label.** `Strategy.evaluate` is a strict AND with no `min_signals`
(`base.py:670-684`), so **one VOID condition kills the entire strategy** — it does not weaken it.
R1 measures **239 of 1,260 generated strategies (19.0%) carrying one**, and the rate is
symbol-specific: MGC 11.5%, MCL 13.9%, MES 22.6%, **MNQ 27.4%**. Three of the six known VOID
configurations sit inside a *required* group.

So a VOID verdict is the difference between the two nulls this programme keeps confusing:
**"we measured absence" and "the detector never fired."** Say which one you have.

# Independence rule for duplicated audits

Where two agents cover overlapping ground, **audit first and compare second.** Take another
agent's *vocabulary* and *method* before you start; do not read its *verdicts* for a condition
before you have written your own. Two independent audits that agree are evidence; one audit plus
one agent anchored on it is one audit wearing two names. If you do read ahead, declare it and mark
which verdicts were formed afterwards — a declared anchor is usable, an undeclared one is not.
