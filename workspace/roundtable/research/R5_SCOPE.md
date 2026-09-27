# R5 — `MAIN-01` scope (Mode SCOPE)

**Agent:** R5. **Mode:** SCOPE (`PIPELINE.md` §3). **Task:** produce the sub-task breakdown for
`MAIN-01` — *is part of this repo's null result a property of wall-clock bars?*
**Opened:** 2026-09-27. **Owner of this file:** R5 (`OWNERSHIP.md`: `research/R5_*`).

**Mode discipline, stated up front so a reader can hold me to it.** No sweeps, no backtests, no
expectancy, no z-scores, no t-statistics appear below. What does appear is **inventory**: row
counts, spans, overlaps, file shapes, grep counts and four code reads, all of which exist only to
size a sub-task. Every one is labelled. Where an inventory number has an obvious implication for
whether a sub-task is worth running, I say so — that judgement *is* the deliverable — but I have
not measured a single approximation error, return distribution or performance statistic, and the
formal answers to the sub-tasks below remain unwritten.

**Read before writing:** `BRIEF.md` (in full), `PIPELINE.md` (in full, §3 Mode SCOPE),
`REGISTRY.md`, `OWNERSHIP.md`, `discovery/MAIN_TASKS.md` (`MAIN-01` and its amendment),
`manager/BOARD.md` (in full: `R-1`…`R-12`, §2 `MAIN-01`, §3 board, §6 blocking, §7
pre-registrations), `manager/ADJUDICATIONS.md` ADJ-2 and ADJ-6,
`research/R1_flow_auction.md` I-12 entry at `:1189-1240` and the `P11` primitive row at `:1619`,
`msgs/10_manager_R1_requests-and-scope.md` §"`MAIN-01` is assigned to you", `check_refs.py`.

---

## 0. Two process facts I must put on the record before the scope itself

**0.1 The board assigns this scope to R1, not to R5.** `BOARD.md` §3 row `MAIN-01` reads
"**Mode SCOPE** — what sub-task breakdown does it need … holder **R1**", and §5 lists R1's next
task as "**`MAIN-01` Mode SCOPE**"
`[repo-verified: workspace/roundtable/manager/BOARD.md, §3 table row MAIN-01 and §5 table row R1]`.
The dispatch that launched me assigned the same scope to R5. No `R1_SCOPE.md` or `R1/SCOPE.md`
exists on disk `[measured: ls workspace/roundtable/research/ → R1_REQUESTS.md,
R1_data_requirements.md, R1_flow_auction.md, R1_group_audit.md and no scope file for any agent]`,
so nothing is duplicated *yet*. I am proceeding because the dispatch is explicit and because an
absent scope blocks the board (`BOARD.md` §6: "`MAIN-01`'s sections | R1's `SCOPE.md`"), but the
manager should resolve ownership before allocating sections, and if R1 also delivers one, the two
should be merged rather than one silently superseding the other. Posted as `R5-01`.

**0.2 My own role brief conflicts with this task and the task wins.** R5's standing brief says the
workspace is `workspace/strategy_research/` and that it must publish `strategy_rankings.json`,
`performance_db.json` and `robustness_report.json`. Mode SCOPE forbids producing any of those —
they are sweep outputs — and the dispatch names `research/R5_SCOPE.md` as the deliverable, which
is also what `OWNERSHIP.md` grants me. **I have written nothing under
`workspace/strategy_research/` and published no rankings.** Recorded so nobody reads the absence
of those three files as an unfinished deliverable.

---

## 1. How I decomposed it, and why that shape

`MAIN-01` is **explicitly killable** (`BOARD.md` §2 "Killable: **yes**, as `CLOSED-EMPTY`"; ADJ-2
"a task that can be killed by one honest measurement is worth more than one that has been rescoped
until it cannot be"). So I did not decompose by topic. **I decomposed by kill-gate, cheapest
killer first.** Each sub-task below is a gate that either closes the task, deflates it, or passes
it on with a stated price.

One further cut runs through the whole breakdown and it is the thing I most want the manager to
take from this file:

> **Separate the sub-tasks that need a constructed alternative-bar series from the ones that do
> not.** The mandatory approximation-error gate (constraint 1) binds *only* on the former. There
> is at least one route to the confound question that constructs no bars at all, and therefore
> cannot be killed by the approximation error. If the scope does not name it, the task dies on
> constraint 1 while still having an answerable question left inside it — which would be a wrong
> close, not a cheap one.

**What `MAIN-01` is asking, restated so the sub-tasks are checkable against it.** Not "do volume
bars pay" (no sub-task below measures that, and `MAIN_TASKS.md` §"What discovery deliberately did
not investigate" forbids assuming it). Not "can the library express them" — R1 answered that
(`INEXPRESSIBLE-ARCHITECTURE`, missing primitive "a bar-identity that is not an integer minute
count", nine layers `[repo-verified: research/R1_flow_auction.md:1242-1259, §"I-12 … Expressibility here", and the
`P11` row at :1642 — but see §6.1, that file is being appended to and its line numbers drift]`) and constraint 3 forbids re-asking it. The question is whether the wall-clock grid is a
**confound in findings this repo treats as settled**, with a specific named mechanism: per-bar
statistics (ATR, relative volume, band widths, the CLV the delta proxy is built from, the regime
labels) count each bar as one observation while bars carry an order of magnitude different amounts
of activity `[repo-verified: discovery/MAIN_TASKS.md, MAIN-01 §"Why it plausibly matters here"
point 1]`.

**A confound claim with a named mechanism is testable through the mechanism's footprint, not only
through the counterfactual.** That is the whole reason S2 exists below.

---

## 2. The sizing inventory. Five facts that set every sub-task's cost

These are inventory measurements taken to size the work. None of them answers `MAIN-01`. Two of
them **change the shape of the task**, and one **corrects a substrate statement that is currently
load-bearing in two places**.

### 2.1 The futures 1-minute substrate is ~6.6 trading days in total, and that is the whole of it

Every constructed-bar route needs 1-minute source data on the instrument the published findings
were measured on. What exists:

| store | 1m bars (MGC) | span | instrument | poolable with `scan_reports/` |
|---|---|---|---|---|
| `csv/raw/MGC_1m.csv` | **5,000** | 2026-09-17T07:31Z → 2026-09-22T23:03Z | CME micro futures, frozen | yes — it *is* the baseline |
| `data/archive/MGC_1m.jsonl` | **6,881** | 2026-09-20T18:10-04:00 → 2026-09-25T16:59-04:00 | same futures series | only as `PROVISIONAL-SUBSTRATE` (`R-7`) |
| **union of the two** | **9,069 unique minutes** | 2026-09-17T07:31Z → 2026-09-25T20:59Z (**9 calendar days**) | futures | mixed — must be labelled per store |
| `data/MGC_1m.csv` | **465,232** | 2019-01-01T23:00Z → 2020-05-14T07:59Z | **Oanda CFD**, different era | **no** |

`[measured: wc -l and first/last row on csv/raw/MGC_1m.csv → 5,000 rows, header
open_time,open,high,low,close,volume]`
`[measured: wc -l data/archive/{MGC,MES,MNQ,MCL}_1m.jsonl → 6881 / 6845 / 6846 / 6872, first ts
2026-09-20T18:10:00-04:00 and last 2026-09-25T16:59:00-04:00 on all four]`
`[measured: python3 — parse both MGC 1m stores, normalise to UTC, set-union → raw 5,000, archive
6,881, overlap 2,812, union 9,069, span 2026-09-17T07:31:00+00:00 → 2026-09-25T20:59:00+00:00]`
`[measured: wc -l data/MGC_1m.csv → 465,232 data rows, header timestamp,open,high,low,close,volume,
first 2019-01-01T23:00:00+00:00, last 2020-05-14T07:59:00+00:00]`

**The correction.** `BOARD.md` §2's substrate note and my own dispatch both say `data/archive/`
adds "~6,000 never-searched bars per symbol **before** the published span". **That is a 60-minute
fact and it is false at 1 minute.** `BRIEF.md`'s own table is explicitly 60m only ("~11,300 hourly
bars per symbol (60m back to 2024-10-06)"), and at 1 minute the Yahoo lookback cap — which
`BRIEF.md` itself records as "1m exists for 7 days only" — means the archive's 1m series starts
**2026-09-20**, i.e. *inside* `csv/raw`'s span, and ends 2026-09-25, i.e. **~3 sessions after** it.
So at 1 minute the archive does not extend the searched span backwards at all; it appends three
sessions to the front edge and duplicates 2,812 minutes of what is already frozen.

**Consequence, and it is the single most important line in this scope.** The total futures
1-minute substrate in this repository is **9 calendar days / ~6.6 CME trading days per symbol** (9,069 minutes / ~1,380 minutes per
Globex day; ~7 calendar trading dates, of which the RTH content is ~2,700 minutes). The
only deep 1-minute store is a **different instrument in a different era** whose `volume` column
discovery already measured as integer in 100.0% of 465k rows — consistent with a *tick count*
rather than contract volume `[repo-verified: discovery/MAIN_TASKS.md §"What it would take to know",
first bullet]`. So a constructed volume-bar series can be measured either on ~6.6 trading days of the
right instrument or on 352 sessions of the wrong one. **No approximation-error result can rescue
either of those.** I think this kills the construction half of `MAIN-01` before the
approximation-error gate is even reached — see §5.

### 2.2 Zero-volume 1-minute bars exist, which a volume clock has to have a rule for

`[measured: python3 over data/archive/{MGC,MES,MNQ,MCL}_1m.jsonl → exactly 5 bars with v == 0.0 in
each of the four series (0.1%); volume integer in 100.0% of rows in all four]`. A volume clock
stalls on a zero-volume minute (the accumulator does not advance) and a dollar clock does too. At
0.1% this is a footnote, not a blocker, but it is a construction rule that must be written down
rather than discovered, because the failure mode is a bar with an arbitrarily long duration.

**Same measurement, labelled `PROVISIONAL-SUBSTRATE` per `R-7`:** archive 1-minute volume
p10 / median / p90 is 62 / 163 / 440 (MGC), 58 / 225 / 2,098 (MES), 273 / 809 / 4,300 (MNQ),
28 / 102 / 361 (MCL). I report these **only** to note that the dispersion figure `MAIN-01` is built
on (3 / 14 / 96, a "~30× range") was measured on the **Oanda CFD** store, not on the futures store,
and that the futures 1-minute dispersion is a different number per symbol. **Establishing what the
real per-bar dispersion is, on the right instrument and at the timeframes the settled findings
actually live on, is sub-task S0 below — it is not settled by the numbers in this paragraph.**

### 2.3 Exactly one trade-level artefact with timestamps exists on disk, and it is 60m/240m only

This decides which of `MAIN-01`'s three named targets is reachable without a sweep.

- `workspace/strategy_research/scratch/geo_trades.json` — **21,954 trades**, keys
  `arm, base, cell, dir, exitm, mae, mfe, mins, r, reason, regime, session, slice, symbol, tf, ts,
  vol`; symbols MNQ 5,667 / MGC 5,480 / MCL 5,422 / MES 5,385; **tf ∈ {60: 16,984, 240: 4,970}**;
  arms include `CONTROL` 5,108 and `CONTROL_FADE` 5,161; slices S1/S2/S3; ts 2025-10-17T04:00-04:00
  → 2026-09-22T16:00-04:00 `[measured: python3 json.load + collections.Counter]`. A sibling
  `geo_trades_6040.json` exists at similar size.
- The sub-hourly verdict's artefacts are **aggregate only**:
  `workspace/focus/cells/MES_5m_27d.json` holds `bars: 4877, screened: 13235, cleared: 352,
  distinct: 191, floor: 15, free_t: 4.357` and **191 per-strategy rows** whose keys are
  `avg_loss, avg_win, clones, exec_tf, exp, group, id, maxdd, n, pf, rr, t, tf, win, win_hi,
  win_lo` — **no trades, no timestamps** `[measured: python3 json.load]`. 39 such cell files exist.
- The structure study's outputs are aggregated findings documents, not trade dumps
  `[measured: python3 over workspace/studies/out/s_*.json → every file has keys
  study_id, title, question, headline, caveats, findings]`.

**So:** the win-rate/payoff-cancellation and ATR-stop-geometry target has a 21,954-trade dump on
disk. The sub-hourly target does not, and reaching it means re-running a 13,235-strategy-per-cell
sweep — which `BRIEF.md` rule 5 and `PIPELINE.md` §4 put behind the manager's assignment.

### 2.4 Two of discovery's four named architecture costs are not real, and a third is worse than stated

Constraint 3 forbids re-asking expressibility, so this is **not** that. It is the *price* half that
`BOARD.md` §2 says neither R1 nor discovery supplied, sized rather than answered:

- **`costs.py` does not depend on bar duration at all.** `[measured: grep -c "minutes"
  futures_agents/backtest/costs.py → 0]`. The cost model is per-trade. The clock reaches it only
  *indirectly*, through `atr_percentile` and `thin` in `SlippageModel.ticks`
  `[repo-verified: futures_agents/backtest/costs.py:35-47]` — and ATR is a per-bar quantity, so
  that coupling is real and is exactly the confound mechanism, not a separate cost.
- **The Sharpe annualisation is clock-robust, and its own comment says otherwise.**
  `metrics.py:31` reads "*Bars per year* used to annualise the Sharpe/Sortino of a trade series"
  above `TRADING_DAYS_PER_YEAR = 252` `[repo-verified: futures_agents/backtest/metrics.py:31-32]`,
  but the code computes `per_year = m.trades_per_calendar_day * TRADING_DAYS_PER_YEAR` and
  `sharpe_annualised = sharpe * sqrt(max(1.0, per_year))` `[repo-verified: :214-215]`, and
  `trades_per_calendar_day` is derived from **trade timestamps** in business days `[repo-verified:
  :199-208]`. Trade timestamps survive a reclocking, so the annualisation does not scale by bar
  count. `MAIN_TASKS.md` §"What it would take to know" lists "the Sharpe annualisation that scales
  by bars-per-year" as an architecture cost; **the comment says that, the code does not.** This is
  the same shape as `D46` (a documented input the code does not read) and I am describing it, not
  naming a number, per `R-9`.
- **`BarSeries` has a silent bar-loss path that nobody has named, and it is specific to this
  construction.** `append` raises on a duration mismatch `[repo-verified:
  futures_agents/data/bars.py:192-195]`, but on an **equal timestamp** it silently replaces:
  "`# Same bucket: replace (a developing bar being finalised)`" → `self._bars[-1] = b; return`
  `[repo-verified: :203-207]`. It does **not** enforce contiguity — only non-decreasing `ts` — so
  an irregularly spaced series loads without complaint. **Therefore: any two snapped
  volume-bar boundaries that land on the same minute collapse into one bar, with no error and no
  warning.** That makes the fine end of the bar-size range a *correctness* failure, not merely an
  accuracy one, and it gives S1 a hard floor that is computable exactly. Alongside it,
  `end_ts = ts + timedelta(minutes=self.minutes)` `[repo-verified: :50-51]` makes every irregular
  bar's end time a fiction, and `_build_alignment` consumes exactly that: `while j < len(tf_bars)
  and tf_bars[j].end_ts <= end` `[repo-verified: futures_agents/features.py:841-842]`.

### 2.5 Injection is cheap; it is the semantics that are expensive

`load_csv(path, symbol, minutes=1, *, max_bars=None)` `[repo-verified:
futures_agents/data/loader.py:93-94]` builds a `BarSeries` from any CSV with a resolvable header,
stamping a constant `minutes` on every bar. So *getting* a synthetic series into the library is one
call with a fabricated `minutes`. R1's verdict stands unchanged and I am not re-litigating it: what
breaks is everything that reads `minutes` as a duration. **The practical consequence for scoping is
that a sub-task which recomputes indicators on a constructed series pays almost none of the
nine-layer price, while a sub-task that runs the engine and the combinator pays all of it.** That
is why S3 and S5 below are separate sub-tasks and not one.

---

## 3. The scope: six sub-tasks, of which I recommend running three

Numbered `S0`–`S5` as *proposals*. Section ids are the manager's to allocate (`REGISTRY.md`: "Only
the manager allocates `D<n>` numbers and `MAIN-<nn>/S<n>` sections"), so these are not
`MAIN-01/S<n>` and should not be cited as such until the board says so.

```
  S0  substrate + provenance          small       KILL GATE 1  (substrate)
   |
   +--> S1  snap-error envelope       medium      KILL GATE 2  (approximation)   <- constraint 1
   |     |
   |     +--> S3  per-bar statistics  medium      DEFLATE GATE (mechanism)
   |           |
   |           +--> S4  price of the nine layers   medium   (only if S3 passes)
   |                 |
   |                 +--> S5  re-run a settled finding   LARGE  (manager assignment required)
   |
   +--> S2  activity stratification   small       INDEPENDENT OF S1 ENTIRELY
```

**S2 hangs off S0, not off S1.** That is the load-bearing feature of this breakdown.

---

### S0 — What the clock is sampling, and how much of it exists. **Mandatory, first, small**

**Answers.** (a) What does `volume` count in each of the three 1-minute stores — contract volume,
tick count, or something else — stated per store with the evidence? (b) What is the total usable
1-minute substrate, per symbol, on the instrument the published findings were measured on? (c) Do
`csv/raw` and `data/archive` agree at **1 minute**, on the 2,812-bar overlap? (d) What is the real
per-bar activity dispersion, per symbol, **at the timeframes the settled findings live on** (60m and
240m), not only at 1m?

**Why (c) is not already done.** `MGR-T6` is the store reconciliation and ADJ-6 scopes it to the
overlap, but `BRIEF.md`'s ruling table is **60m only** and its own condition 2 says "Verify
equivalence for your own symbol *and timeframe* before relying on it. The table above is 60m only …
Do not assume the 60m result generalises." `MAIN-01`'s only futures substrate is a **union of the
two stores at 1 minute**, so this is a genuine prerequisite and not a duplicate. It is also cheap:
2,812 overlapping bars for MGC `[measured, §2.1]`. **Compare with a tolerance, never `==`** —
`BRIEF.md` records MGC and MCL differing by 3.4e-07 and 4.8e-08 at 60m, and volume differing on 2 of
~4,987 bars on all four contracts. **Normalise to UTC first**: `csv/raw` is `+00:00`,
`data/archive` is `-04:00`, and `BRIEF.md` records that slicing the offset off produced a fictitious
23.0-point mean discrepancy on MGC.

**Why (d) matters more than it looks.** `MAIN-01`'s motivating dispersion figure (p10/median/p90 =
3/14/96, "a 30-fold swing") is a **1-minute figure on the Oanda CFD store** `[repo-verified:
discovery/MAIN_TASKS.md §"Why it plausibly matters here" point 1]`, while the settled findings it
proposes to re-examine were measured at **60m and 240m** `[repo-verified:
workspace/studies/STRUCTURE_FINDINGS.md:10-11 — "MGC/MES/NQ/MNQ/MCL × {60m, 240m} × 3 disjoint
slices = 30 cells"]` and at 5m for the sub-hourly verdict `[repo-verified:
scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:23-24]`. Aggregation shrinks relative dispersion.
**If the dispersion at 60m/240m is small, the confound mechanism is small there by construction, and
that is a cheaper and more direct deflation of `MAIN-01` than anything in S1.** This is the one
measurement in the whole task I would most want done first.

**Reads / runs.** `csv/raw/*_1m.csv` and `*_1h.csv` (read-only, `R-1`), `data/archive/*_1m.jsonl`,
`data/{MES,MGC,MNQ}_1m.csv`, `futures_agents/data/loader.py`, `BRIEF.md`'s data policy. Arithmetic
only: counts, spans, set-overlaps, quantiles of `volume` per timeframe. No engine, no strategies.

**Size.** **Small** — one burst. Perhaps 40% of it is already on disk in §2 of this file, but §2 is
one symbol deep on the overlap and does not answer (a) or (d) at all.

**Kill criterion (KILL GATE 1).** If the futures 1-minute substrate is under roughly 10 sessions
per symbol — and §2.1 measures **~6.5** — then no constructed-bar route can produce a statement
about a published finding, because the published findings span 274 days and this spans nine.
`MAIN-01`'s construction half closes here. **That is a `CLOSED-EMPTY` trigger and it fires before
the approximation-error gate.**

**Risk to watch.** The temptation is to substitute the 465k-bar Oanda store and carry on. That
substitution changes the instrument *and* the era *and* (probably) the meaning of the `volume`
column, so a result on it is a statement about a 2019–20 CFD, not about this repo's findings. If
S0 licenses that store for anything, it must say so in exactly those words.

---

### S1 — The snap-error envelope, and the constructibility floor. **Mandatory second, medium**

This is constraint 1, the gate the board says must be settled first, and I am placing it second only
because S0 is its input (you cannot state a bar size in contracts until you know what the column
counts, and you cannot choose a substrate until you know what exists). **If the manager prefers
constraint 1 literally first, S0(a) alone is its prerequisite and S0(b)-(d) can run beside S1.**

**Answers.** Over what range of target bar sizes, per symbol and per substrate, is a minute-snapped
volume (or dollar) bar a defensible approximation to a volume bar — and in which direction does its
error push? And does that range overlap the range that produces a useful number of bars per session?

**Three methods, in the order I would run them. The first two need no ground truth, which is the
point, because there is no finer object than a 1-minute bar in this repository.**

- **S1a — the constructibility floor, exactly computable.** A snapped boundary lands on a minute
  edge. Two boundaries inside one minute therefore collapse, silently, via the equal-`ts` replace at
  `bars.py:203-207` (§2.4). So the floor is: **the fraction of a series' volume arriving in minutes
  whose own volume ≥ the target bar size**, as a function of target size, per symbol. Below that
  size, bars are *lost*, not mis-timed, and any statistic computed on the series is computed on a
  series with an unknown number of missing observations. This is arithmetic over a single volume
  column and it is exact — no tape, no assumption. It produces the hard lower end of the "size range
  nobody has drawn".
- **S1b — the bracketing envelope, which is the honest form of "how wrong is it".** The true
  boundary time `t*` lies strictly inside some minute `m`. Construct **two** series: *early-snap*
  (boundary at the start of `m`, `m`'s volume goes to the next bar) and *late-snap* (boundary at the
  end of `m`, all of `m`'s volume goes to this bar). Every admissible true volume-bar series has its
  boundaries bracketed by these two. Then report, as a function of target size, how far apart the
  two series are **in the quantities the confound claim actually uses** — ATR, bar range,
  volume-per-bar, close-location value, band width. **This replaces an unanswerable question
  ("what is the error?") with an answerable and strictly more useful one ("how much can the answer
  move across the entire admissible set?").** If the envelope is narrow at a usable size, the
  approximation is defensible *for this purpose* regardless of its absolute error. If it is wide,
  the task closes and no further work is needed.
  **Caveat the sub-task must verify rather than assume:** bracketing is clean for cumulative volume
  and for high/low (monotone in which minutes are included) and is *not* automatically clean for
  `close`, since the true close is a price inside minute `m` rather than one of the two endpoints.
  The sub-task owes either a proof that `[min(low_m, close_{m-1}), max(high_m, close_{m-1})]` bounds
  it or an explicit statement that the close is bounded but not bracketed.
- **S1c — the degradation curve, only if S1b is inconclusive.** Build the snapped series from 1m,
  then from 5m, then from 15m source, and measure how the envelope widens as the source coarsens.
  That gives an empirical slope from which the 1m→tape step can be *extrapolated*. **It is an
  extrapolation and must be labelled one**, never reported as a measured tape error.

**Reads / runs.** Whichever substrate S0 licensed; a bar constructor of maybe 80 lines; the
library's own ATR and band functions applied to the constructed series (no engine). `R-1` applies:
read `csv/` , write nothing under it.

**Size.** **Medium.** S1a is one burst. S1b is one to two. S1c is one, and probably never runs.

**Kill criterion (KILL GATE 2, the one the board named).** The task closes `CLOSED-EMPTY` if
**either** (i) S1a's collision-free floor is above the size that yields ~50 bars per session, so
every constructible series is either silently lossy or too coarse to carry an intraday finding, or
(ii) S1b's envelope on ATR — the quantity every stop and every target in this repo is denominated in
— is wide enough at every admissible size that the two brackets would not agree about the sign of
the confound. Concretely, my recommended pre-registered threshold: **if the early/late brackets'
median per-bar ATR differs by more than the effect being hunted, the approximation cannot resolve
it.** The sub-task should state that threshold *before* measuring, in the S1a/S1b burst notes.

**What must not happen here.** Rescoping to range bars. `BOARD.md` §2 constraint 2 and ADJ-2 both
forbid it explicitly and R1 called that approximation poor too `[repo-verified:
research/R1_flow_auction.md:1228-1230, §"I-12 … Minimum data"]`. A range-bar boundary is the same class of statement — a
path statement inside a minute — so it inherits the same error, with the additional problem that the
intrabar path determines *whether the boundary happened at all*, not merely when.

---

### S2 — Does the settled finding vary with per-bar activity, on the grid we already have? **Small, and immune to S1**

**This is the sub-task I would keep if the manager kept only one.** It constructs no bars, so
constraint 1 cannot kill it, and it reads an artefact that is already on disk.

**The logic.** `MAIN-01`'s confound claim has a named mechanism: per-bar statistics weight
unequal-activity bars equally. A volume clock's first-order effect is precisely to **equalise
activity per bar**. So if the mechanism is operating, the settled finding must differ across
activity strata *measured on the existing wall-clock grid* — and if it does not, re-clocking has
very little left to change, because re-clocking is to first order a regrouping of the same minutes
by activity.

**Answers.** Conditional on entry-bar (and trailing-window) activity, does the win-rate/payoff
cancellation still cancel; is the flat win rate across distance-to-invalidation buckets still flat;
does average R differ between the low-activity and high-activity strata for the same arm?

**Reads / runs.** `workspace/strategy_research/scratch/geo_trades.json` — 21,954 trades with `ts`,
`r`, `mae`, `mfe`, `mins`, `session`, `regime`, `vol`, `reason`, `exitm`, `arm`, `dir`, `slice`
(§2.3) — joined on `(symbol, tf, ts)` to the `volume` column of `csv/raw/*_1h.csv` (and a
resampled 240m) to attach activity at entry and over the ATR lookback. Then stratify and re-test.
No sweep, no engine, no new strategies, no new bars.

**Six caveats it must carry, and the fifth is the one that decides how much this sub-task is worth.**

1. **It is a necessary-condition test, not the counterfactual.** A null here does not *prove* the
   clock is not a confound — it removes the motivation for paying for the counterfactual. Reclocking
   also changes *which* bars exist and hence when signals fire; stratification does not reproduce
   that. **The finding must be stated as "no footprint of the named mechanism", never as "the clock
   is not a confound".**
2. **Timezone.** Dump `ts` is ET (`-04:00`/`-05:00`); `csv/raw` is UTC. Normalise both to UTC before
   joining, per `BRIEF.md`'s recorded 23.0-point mistake.
3. **Join coverage must be verified and reported, not assumed.** The dump's earliest `ts` is
   2025-10-17T04:00-04:00 while `csv/raw/MGC_1h.csv` starts 2025-11-05T04:00Z `[measured: §2.3 and
   first data row of csv/raw/MGC_1h.csv]`, so some rows will not join. An unreported join loss is a
   silent survivorship filter on the strata.
4. **240m has no native file.** `csv/raw` holds no 4h or 240m CSV `[measured: ls csv/raw/ → 48
   files, none named *_4h.csv or *_240m.csv]`; `BRIEF.md` states the 240m framework is resampled.
   So 240m activity must be built by `resample`, and `align_bucket` aligns multi-hour buckets to
   midnight `[repo-verified: futures_agents/data/bars.py:150-154 — "Align multi-hour buckets to midnight so 4h
bars fall on 00/04/08/12/16/20"]` — the join key must match how the
   dump's cells were built, or the strata are mislabelled.
5. **Its raw form is partly pre-answered, and only the residual is new.** Intraday volume has a
   strong U-shape, so per-bar activity is largely a function of time of day — and `BRIEF.md` rule 6
   already records that **no hours filter improves expectancy**, refuting the folk claim, while rule
   5 records the one time-of-day prohibition that survived (15:00–16:00 ET, z = −4.43). If
   expectancy does not vary by hour and activity is mostly hour, then expectancy mostly does not
   vary by activity, and the raw stratification is largely foreseeable. **The content is therefore
   in activity residualised on time of day** — variation in participation *within* a clock-minute
   bucket. That is exactly the distinction `MGR-T13` was promoted to settle (the 20-bar trailing mean
   in `detect_imbalances` versus the same-clock-minute-over-20-sessions norm in `relative_volume`,
   which select populations differing 5–27× on identical bars), and R1's binding constraint there —
   both axes take the time-of-day norm or neither does — **applies verbatim here.** So S2 either
   waits on `MGR-T13` or adopts its time-of-day norm by assumption and says so.
6. **Statistics.** Stratifying an existing trade set is post-hoc conditioning: count-match the
   strata, use a paired test with the correlation accounted for and **name it** (`R-4`/D28: never
   `T.ab`, which inflates z ~3.3×), state the number of stratifications tried against `free_t`
   (`R-3`), and put a control beside it (`R-2`) — here the natural control is a stratifier with the
   same marginal distribution and no activity content, e.g. a within-session shuffle of the activity
   labels. Also note the dump records `r` but **not** `entry_price` or `initial_stop` — `ADJ-9d`
   exists precisely because dumps lacked them — so R cannot be recomputed, only re-aggregated.

**Size.** **Small to medium**: one burst for the join and the coverage report, one for the
stratified re-test. The join itself is also reusable by `MGR-T13`, which wants the same quantity.

**Ownership problem the manager must settle.** S2 reads R3's target (the geometry study's dump) and
depends on R1's `MGR-T13` norm, while `BOARD.md` §2 assigns `MAIN-01` scoping on the grounds that
the first gate is R1's surface and "R3 owns the *targets* of the confound question". **S2 is the
cheapest sub-task here and the one most likely to need an adjudication before it can be dispatched.**
Asked in `R5-01`.

---

### S3 — Do the per-bar statistics actually differ under the two clocks? **Medium, gated on S1**

**Answers.** discovery's "statistical answer, before any strategy answer": on a licensed bar size
and substrate, do ATR, relative volume, band width, close-location value and the return
distribution differ between the wall-clock series and the snapped volume-clock series — and is any
difference larger than S1b's envelope? Does the literature's claim (returns better behaved on a
subordinator) hold *on this data*, which discovery explicitly did not verify and labelled
`[general knowledge]`?

**Reads / runs.** The S1 constructor; the library's own indicator functions applied directly to
both series. **No engine, no combinator, no strategies** — so it pays essentially none of the
nine-layer price (§2.5).

**Size.** **Medium**, one to two bursts, entirely dependent on S1 having licensed a size.

**Deflate criterion.** If every difference sits inside S1b's envelope, the confound has no
measurable mechanism on this data and `MAIN-01` closes with a null. `MAIN_TASKS.md` is explicit that
this is a complete answer: "**A null here is a complete and valuable answer** and should be reported
as one." I agree, and I would add: a null here plus a null in S2 is a *stronger* close than S1
killing the task, because it closes the question rather than only the method.

**Risk.** Comparing distributions across two series with different bar counts invites an n-driven
artefact: the volume-clock series will have a different number of observations than the wall-clock
one by construction, and almost every test statistic here is n-sensitive. Count-match, or compare
quantiles and shape rather than test statistics, and say which.

---

### S4 — The price of the nine layers. **Medium, independent, and worth nothing unless S3 passes**

**Answers.** What would it cost to give this library "a bar-identity that is not an integer minute
count"? R1 delivered the verdict and named the nine layers; `BOARD.md` §2 says "**What neither
supplies is the price of changing it** — that is the open half."

**Shape of the answer I would want.** A minimum-viable variant, not a refactor: the smallest change
that lets a non-time series be *carried* honestly, with the list of things it deliberately leaves
broken. §2.4 already moves two of the four costs discovery listed off the ledger (`costs.py` has no
`minutes` dependence; the Sharpe annualisation keys off trade timestamps, not bar count) and adds
one that is worse than stated (the equal-`ts` silent replace). A plausible minimal shape is a
duration-carrying field per bar plus an explicit `end_ts`, leaving `resample` and `TIMEFRAME_GROUPS`
unsupported for non-time series — but that is a guess and pricing it is the sub-task.

**Size.** **Medium**, one to two bursts of code reading. **Independent of S0–S3**, so it *can* run
early — and should not. Pricing a change nobody will make is the most wasteful thing in this scope.

**Recommendation.** Do not authorise until S3 has passed. If S1 or S3 kills the task, S4's answer
is "unknown, and nobody needs it", which is the correct outcome.

---

### S5 — Re-run a settled finding under the alternative clock. **Large. I recommend not authorising it**

**Answers.** The literal form of `MAIN-01`: does the win-rate/payoff cancellation, the ATR stop
geometry, or the sub-hourly verdict change under a volume clock?

**Why it is large and why I would not authorise it now.** It requires the constructed series *and*
the engine *and* the combinator, so it pays the whole nine-layer price; it is the only sub-task
producing comparative performance statistics, so it needs `R-2` (placebo), `R-3` (search size and
deflation), `R-4` (a named paired test), `R-6` (paired re-emission with `_id=None` and an arm-id
assert, per `D48`) and the manager's assignment; and §2.1 and §2.3 say the two reachable targets
are each blocked on substrate or artefact:

| target | clock exposure | blocker |
|---|---|---|
| win-rate/payoff cancellation, ATR stop geometry | 60m/240m, ATR-denominated `[repo-verified: workspace/studies/STRUCTURE_FINDINGS.md:32-35 — win rate "flat at 0.370-0.423 across
every bucket" with geometry held fixed]` | needs 1m source to reclock → ~6.5 futures sessions (§2.1), or the wrong instrument |
| sub-hourly verdict (5m, 11–16% profitable) `[repo-verified: scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:23-24]` | 5m | no trade-level artefact; needs a 13,235-strategy-per-cell sweep re-run (§2.3) |
| placebo-ranks-alongside-real result | all | this is a programme-wide result over ~2.97M candidates; reclocking it is not a sub-task, it is a second programme |

**If it ever runs, the anti-overfitting obligations it inherits.** Out-of-sample split and
walk-forward before anything is called live-eligible; explicit checks for data-mining bias across
bar sizes (**bar size is a free parameter with no natural value — R1's own "how it dies" note
`[repo-verified: research/R1_flow_auction.md:1238-1240, §"I-12 … How it dies"]` — so the size sweep is itself a
data-mining surface and must be counted in `R-3`'s denominator**); parameter sensitivity across
sizes; unrealistic fills (a non-time bar's close "is not a moment", R1, same lines — so next-bar-open
entry means something different on a volume clock and the fill model must be re-audited, not
inherited); look-ahead and repainting (a snapped boundary is *decided* using the whole minute's
volume, which is information not available at the minute's open — **this is a genuine look-ahead
channel unique to the construction and it must be checked, not assumed away**); and the survivorship
question of whether a contract roll inside the series changes bar character.

---

## 4. Dependency order, and what each gate costs

| order | sub-task | size | depends on | gate |
|---|---|---|---|---|
| 1 | **S0** substrate + provenance + 1m store reconciliation + dispersion at 60m/240m | small | — | **KILL GATE 1** — substrate |
| 2 | **S1** constructibility floor (S1a) then snap-error envelope (S1b) | medium | S0 | **KILL GATE 2** — approximation (constraint 1) |
| 2′ | **S2** activity stratification on the existing grid | small | S0 (+ `MGR-T13`'s norm) | independent; cannot be killed by S1 |
| 3 | **S3** per-bar statistics and return distributions under both clocks | medium | S1 licensing a size | **DEFLATE GATE** — mechanism |
| 4 | **S4** price of the nine layers | medium | none technically; **S3 passing** practically | — |
| 5 | **S5** re-run a settled finding | large | S3 + S4 + manager assignment | — |

**S2 runs in parallel with S1 and does not wait for it.** That is the only parallelism in the
breakdown and it is deliberate: it is the one sub-task whose answer survives the task being killed.

---

## 5. What result kills `MAIN-01`, stated so it can be checked against later

`BOARD.md` §2 requires this and `BOARD.md` §7 pre-registration 1 predicts the outcome. Four
distinct triggers, in the order they can fire:

| # | trigger | fires in | verdict |
|---|---|---|---|
| **K1** | The futures 1-minute substrate is under ~10 trading days per symbol, and the only deep 1m store is a different instrument in a different era with a differently-defined `volume` column. | **S0** | `CLOSED-EMPTY` — construction half. **§2.1 measures ~6.6 CME trading days, so this trigger is already very likely met.** |
| **K2** | S1a's collision-free floor (target size > every boundary minute's volume) sits above the size that yields ~50 bars/session — i.e. every constructible series is either silently lossy or too coarse for an intraday finding. | **S1a** | `CLOSED-EMPTY` — "the defensible range and the useful range do not overlap", which is exactly `BOARD.md` §7 pre-registration 1. |
| **K3** | S1b's early/late bracket differs, on ATR at every admissible size, by more than the effect being hunted — so the two brackets cannot agree about the confound's sign. | **S1b** | `CLOSED-EMPTY` — the approximation cannot resolve the question. This is the board's named gate. |
| **K4** | S2 finds no activity footprint **and** S3 finds no per-bar-statistic or return-distribution difference beyond S1b's envelope. | **S2 + S3** | Closed with a **null**, which is a stronger close than K1–K3: it closes the *question*, not merely the method. |

**What would falsify the board's pre-registration** (`BOARD.md` §7.1: "the defensible range and the
useful range do not overlap"): S1 naming a target bar size, per symbol, at which (i) the collision
rate is ~0, (ii) the early/late ATR envelope is narrower than the effect size in question, and
(iii) the series yields ≥50 bars per session. All three, with the bound stated. That is the exact
falsification condition the board asked for and S1 should report it in that form.

**Two further outcomes that are not kills and should not be reported as failures.** `PIPELINE.md` and
`BRIEF.md` rule 4 both say absence is a result; the parallel here is that **a sub-task discovering
that a *different* sub-task is impossible is a finding**. If S0 says the substrate cannot carry S5,
that is the most valuable single sentence `MAIN-01` can produce, because it retires an avenue with a
reason rather than a shrug.

---

## 6. My honest judgement: is this worth running at all?

**Short answer: run S0, run S2, and expect to close `MAIN-01`'s construction half on S0 rather than
on the approximation error the board named.** I would not authorise S1c, S4 or S5 now.

### 6.1 The board's pre-registration is probably right in outcome and wrong in mechanism

`BOARD.md` §7 pre-registration 1 predicts `CLOSED-EMPTY` because "the defensible range and the
useful range do not overlap" — an *approximation-error* argument. My sizing says the task dies
**one gate earlier and for a different reason**: there are **9 calendar days / ~6.6 CME trading days**
of futures 1-minute data in this repository, total, across both stores, and the only deep 1-minute
store is an Oanda CFD from 2019–20 whose `volume` column is integer in 100% of 465k rows
(§2.1, §2.2). The published findings `MAIN-01` proposes to re-examine span 274 days at 60m/240m and
27 days at 5m. **A perfect volume-bar constructor cannot make a statement about a 274-day finding
from nine days of data**, so the approximation-error question — however it resolves — is not what
decides this. That distinction matters for the record: if the task closes and the reason is written
down as "the approximation was too poor", the ledger will carry a claim nobody measured, and the
avenue will be reopenable on the wrong grounds (a tape arriving would not fix a substrate problem,
and `AVENUES.md`'s revisit rule turns on the *stated* reason).

I want to be precise about what I am and am not claiming. **I have not measured any approximation
error**, so I am not saying the board is wrong about it; I am saying it is no longer the binding
constraint, and that a cheaper constraint fires first. S1 remains worth running *if* S0 licenses a
substrate, because constraint 1 is mandatory and because S1a's collision floor is a genuinely new
correctness result (§2.4) that is cheap and reusable.

### 6.2 The part of `MAIN-01` that is worth running is the part that needs no new bars

S2 costs one to two bursts, constructs nothing, reads a 21,954-trade dump that is already on disk,
has **zero** approximation error, and tests the mechanism `MAIN-01` actually named. Its output is
also reusable: the activity join it builds is the same join `MGR-T13` needs. **If `MAIN-01` closes
`CLOSED-EMPTY` as a whole, S2 should not die with it** — it should be re-filed, most naturally as a
sub-task of `MGR-T13`, which already owns the volume-normalisation question at the same join and
already carries R1's binding "both axes take the time-of-day norm or neither does" constraint.

I should be equally honest about S2's ceiling. Its raw form is **partly pre-answered**: activity is
largely time of day, and `BRIEF.md` rule 6 already records that no hours filter improves expectancy.
So I expect S2's headline to be a null, and its real content to be in the time-of-day-residualised
stratum — which is a narrower and more technical result than `MAIN-01`'s framing promises. **A
one-burst sub-task with a foreseeable null and a narrow residual is still worth running here**,
because the alternative is a `CLOSED-EMPTY` on a question nobody tested, and because the residual is
the only version of `MAIN-01`'s question this repository's data can actually answer.

### 6.3 The recommendation, in the manager's vocabulary

| what | recommendation |
|---|---|
| `MAIN-01` as discovery framed it (build alternative bars; re-clock settled findings) | **`CLOSED-EMPTY`**, on the **substrate** finding (K1), with the reason recorded as substrate and *not* as approximation error |
| S0 | **allocate and run** — one burst; it is what produces the close, and it also discharges a real gap (`MGR-T6` is 60m-only and the data policy requires per-timeframe verification) |
| S1a | **allocate and run** if S0 licenses any substrate; the collision floor is new, cheap and reusable, and constraint 1 is mandatory |
| S1b, S1c | run S1b only if S1a licenses a size; S1c almost certainly never |
| S2 | **allocate and run**, or re-file under `MGR-T13`. **Do not let it die with the main task.** Needs an ownership ruling first (it reads R3's artefact and R1's norm) |
| S3 | queued behind S1; likely never reached |
| S4 (price of the nine layers) | **do not authorise.** Pricing a change nobody will make. §2.4 already retires two of the four costs discovery listed, which is most of the cheap value |
| S5 | **do not authorise.** Large, needs a sweep, and the substrate is not there |

**The shape I am recommending is: a main task that dies on its first sub-task, with one sub-task
surviving it and moving to another holder.** `BOARD.md` §2 calls a cheaply-killable task the right
shape; ADJ-2 calls this exposure correct. I am agreeing with both and adding that the *reason* on
the death certificate is the part worth getting right.

### 6.4 One thing in the verdict vocabulary that does not fit, and I cannot fix from here

`PIPELINE.md` §1's verdicts are whole-avenue: `CLOSED-EMPTY` / `CLOSED-FOUND` / `OPEN-PARTIAL` /
`DEFERRED`. What I am recommending is a **split** verdict: `CLOSED-EMPTY` on the construction half
(substrate, and a tape would not fix it — so not `DEFERRED`) plus one live sub-task moving to
another board task. The closest honest single label for `I-12`'s parent avenue is **`DEFERRED`** for
the tape-blocked schemes (`AVENUES.md` `BLOCK-SUBBAR` already covers those, and that reason *could*
change) and **`CLOSED-EMPTY`** for the minute-snapped construction on the current substrate. Only
discovery writes `AVENUES.md` and only the manager writes `BOARD.md`, so this is a routing question,
not something I can record myself. Asked in `R5-01`.

---

## 7. The anti-overfitting surface, checked at scope level

My standing brief requires me to state which of the standard failure modes I checked and what I
found. At Mode SCOPE these are checks on the *proposed designs*, not on results — there are no
results. I checked ten and found five live hazards.

| hazard | checked | finding |
|---|---|---|
| **insufficient sample size** | yes | **LIVE, and it is the task's binding constraint.** ~6.6 CME trading days of futures 1m data (§2.1). Also: the 5m cell artefact's own `floor: 15`, `free_t: 4.357` on 13,235 screened `[measured: §2.3]` — the deflation threshold is already unmet there before any reclocking. |
| **data-mining bias / parameter sensitivity** | yes | **LIVE.** Bar size is a free parameter with no natural value — R1's own note `[repo-verified: research/R1_flow_auction.md:1238-1240]`. Any size sweep enters `R-3`'s denominator and must be counted. S1's job is to *narrow* the admissible range on correctness grounds before anyone sweeps it. |
| **look-ahead / future-data leakage** | yes | **LIVE and specific to this construction.** A snapped boundary is decided using the *whole* minute's volume, which is not known at that minute's open. Any signal evaluated at a snapped bar's close therefore consumes end-of-minute information — a leakage channel that does not exist on the wall-clock grid and that must be checked, not assumed away. Named in S5; it also touches S3 if indicators are evaluated bar-by-bar. |
| **unrealistic fills** | yes | **LIVE.** "A bar's close is not a moment" on a non-time bar `[repo-verified: research/R1_flow_auction.md:1238-1240]`, so next-bar-open entry means something different and the fill model must be re-audited rather than inherited. The repo's own recorded lesson applies: "resampling cannot detect a bias whose sign is always favourable; only auditing the fill model can" `[repo-verified: scan_reports/2026-09-24_ORB-and-ICT.md:125-126; discovery/MAIN_TASKS.md cites it as :117-133]`. |
| **understated costs and slippage** | yes | Partly retired. `costs.py` has **no** bar-duration dependence `[measured: grep -c "minutes" futures_agents/backtest/costs.py → 0]`; the coupling runs through `atr_percentile`/`thin` in `SlippageModel.ticks` `[repo-verified: futures_agents/backtest/costs.py:35-47]`, which is the confound mechanism itself rather than an independent cost error. |
| **repainting indicators** | yes | **LIVE in a form unique to the construction.** A snapped series' *last* bar repaints: whether the current minute belongs to the open bar or closes it is unknown until the minute ends. `BarSeries.completed` exists for exactly this on the time grid `[repo-verified: futures_agents/data/bars.py:225-233]` but it is defined by the trailing bar, not by a volume threshold, so it does not cover the volume-clock case. |
| **silent data loss** | yes | **LIVE, new, and nobody in the roundtable has named it.** `BarSeries.append` silently replaces on an equal timestamp `[repo-verified: futures_agents/data/bars.py:203-207]`, so two snapped boundaries inside one minute collapse into one bar with no warning. This is S1a's whole subject. |
| **survivorship bias** | yes | Not live for the bar question as posed (fixed symbol list, no selection on outcome), but the **contract-roll** question is: a volume clock's bar character changes across a roll, and `BRIEF.md` records that the grain CSVs splice contract months (D40) and that `MNQ=F` is not `MNQ1!`. Any multi-month constructed series owes a roll statement. |
| **substrate pooling** | yes | **LIVE.** `R-7` forbids pooling an archive number with a `csv/raw` number inside one statistic, and §2.1's union of the two stores at 1m is exactly such a pool. S0 must either label every number by store or verify equivalence at 1m first. |
| **false-null mechanisms** | yes | Four are already on the programme's record (`D38` silent zeroing, `D42` placebo leak, `D44` bootstrap, `D48` `_id` collision). S1a adds a **fifth** with the same signature — an exact-zero or attenuated difference produced by silently missing bars — and it lands in the same place: a "no effect" conclusion that is an artefact. Any S3/S5 code needs the `_id=None` + arm-id assert discipline of `R-6` and the `register_frame` guard of `D38`. |

Two I did **not** check, because Mode SCOPE cannot: whether any specific reclocked statistic
survives out-of-sample (there is nothing to test), and walk-forward stability (same). Both are S5's
obligations and both are among the reasons I recommend against authorising S5.

---

## 8. Questions posted, and what is blocked on them

Posted as `msgs/R5-01_manager_main01-scope-substrate.md`. Nothing in this scope is blocked on the
answers — the breakdown stands either way — but three routing decisions are the manager's:

1. **Who owns `MAIN-01`'s scope**, given `BOARD.md` assigns it to R1 and R5 was dispatched to do it
   (§0.1). If R1 also delivers, merge rather than supersede.
2. **Who owns S2**, which reads R3's artefact (`geo_trades.json`) and depends on R1's `MGR-T13`
   norm, while `BOARD.md` §2 splits gate-ownership from target-ownership.
3. **Whether a split verdict is expressible** (§6.4), and if not, which single verdict the ledger
   should carry so the avenue is reopenable on the right grounds.

Plus one correction the manager should hear because it is load-bearing in a file I do not own:
**`BOARD.md` §2's substrate note is a 60-minute statement being read as a 1-minute one** (§2.1).

---

## 9. Log

- **Burst 1 (this file).** Read the eight required files in full plus R1's `I-12` entry, ADJ-2,
  ADJ-6 and `check_refs.py`. Took the inventory in §2 — eleven measurements, all counts/spans/greps,
  no sweep and no statistic. Wrote §0–§8. Posted `R5-01`. **Stopped.** No research on `MAIN-01`'s
  question was performed and none of S0–S5 was executed.
- **Note on citation drift.** `research/R1_flow_auction.md` was being appended to while I read it:
  the `I-12` heading moved from line 1189 to 1212 between two reads in the same session
  `[measured: grep -n "^## I-12" research/R1_flow_auction.md, twice, → 1189 then 1212]`. Every
  citation of that file above therefore carries its **section heading** as well as its line number.
  This is a general hazard for the whole roundtable while files are live, and `REGISTRY.md`'s "say
  the id and the path you read it at, so the owner can tell whether you read the current version"
  is the mitigation.
- **One precision correction to my own `R5-01`, recorded here because `msgs/` is write-once and the
  parent has already committed it** (`5f8fd91`). `R5-01` §2 says the substrate is "~6.5 **RTH**
  sessions per symbol". The exact statement is **9,069 unique minutes = ~6.6 CME trading days**
  (~1,380 minutes per Globex day), across ~7 calendar trading dates, of which the *RTH* content is
  only ~2,700 minutes. "RTH" in that sentence is loose — the repo's own prose is loose the same way
  (`MAIN_TASKS.md` calls 465,232 minutes "352 RTH sessions", i.e. ~1,322 minutes per "session") —
  and `BOARD.md`'s "5,000 bars ≈ 4 trading sessions" uses the trading-day convention, which is the
  one I intend. **The load-bearing numbers in `R5-01` are exact and unchanged:** 5,000 / 6,881 /
  overlap 2,812 / union 9,069 / span 2026-09-17 → 2026-09-25. §2.1 above carries the corrected
  wording. Nothing in the conclusion moves.
