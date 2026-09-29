# MAIN_TASKS — discovery's output

**Owner:** discovery (`OWNERSHIP.md`). One entry per avenue judged worth depth, stated at altitude.
**Discovery does not decompose these.** The manager's first move is to ask the researcher what
sub-task breakdown it needs; the breakdown is the researcher's, per `PIPELINE.md` §2–§3.

---

## MAIN-01 — The sampling clock: is part of this repo's null result a property of wall-clock bars?

**Raised by:** discovery burst 01 (`bursts/01_seed.md`), 2026-09-27.
**Avenue:** `AVENUES.md` I-12 — alternative bar sampling (tick, volume, range, dollar, imbalance
and run bars). Marked `CLOSED-FOUND`; this task carries it.

### What the avenue is

Every bar in this repository is a **wall-clock interval**. `BarSeries` is documented as "an
append-only, time-ordered series of **same-duration** bars"
`[repo-verified: futures_agents/data/bars.py:160]`; `Bar.minutes: int = 1` is commented "bar
duration" `[repo-verified: futures_agents/data/bars.py:43]`; every timeframe in a `SymbolFrame` is
produced by `resample(base, tf)` with `tf` an integer number of minutes
`[repo-verified: futures_agents/features.py:795-812]`, bucketed on the clock by `align_bucket`,
which aligns intraday buckets to the hour and daily ones to the 18:00 ET CME roll
`[repo-verified: futures_agents/data/bars.py:138-156]`. `[measured: grep -rn "\.minutes"
futures_agents/ --include=*.py | grep -v __pycache__ | wc -l → 74]`.

The alternative is a literature, not a gadget. Sampling a price series on a clock is a *modelling
choice*; the classical result is that financial returns look closer to well-behaved when the series
is sampled on a **subordinator** — cumulative volume, cumulative traded value, or cumulative price
movement — rather than on time: Mandelbrot–Taylor's subordinated process, Clark (1973) using volume
as the directing process, Ané–Geman (2000) on the number of trades, and the modern practitioner
statement in López de Prado, *Advances in Financial Machine Learning*, ch. 2, which argues time bars
oversample quiet periods and undersample active ones and recommends volume or dollar bars for better
statistical properties `[general knowledge]`. **None of that claim is verified here and this task
must not assume it.** The reason to test it is the next section.

**Six schemes, and they do not share one blocker — which is the structural point.** Tick bars,
imbalance bars and run bars need the tape and are blocked by data (BLOCK-SUBBAR in `AVENUES.md`).
**Volume bars, dollar bars and range bars need only `(high, low, close, volume)` per minute, which
this repo has.** So half of family I-12 is blocked by *architecture*, with the data already present
— which is the rarest and most actionable cell in the manager's own expressibility matrix, where
almost everything else is expected to land on INEXPRESSIBLE-DATA (`DIVISION.md` §6).

### Why it plausibly matters *here*, given this repo's data and settled findings

1. **The dispersion is measured and it is large.** `[measured: python3 -c over data/MGC_1m.csv,
   data/MES_1m.csv, data/MNQ_1m.csv and csv/raw/{MGC,MES,MCL}_1m.csv → per-1-minute volume
   p10/median/p90 = 3/14/96 (MGC deep), 2/9/57 (MES deep), 7/56/286 (MNQ deep), 68/177/470 (MGC
   frozen), 63/248/1863 (MES frozen)]`. A one-minute bar therefore carries **between 3 and 96 units
   of activity, a 30-fold swing, depending on when in the day it occurs** — and every per-bar
   statistic in the library treats those as one observation each. ATR, `relative_volume_high`,
   `volume_surge`, the close-location value that `estimated_delta` is built from, the regime labels,
   the Bollinger and Keltner widths: all are computed per bar, over a bar whose information content
   varies by an order of magnitude within the session.
2. **It offers a mechanism for the placebo result rather than an argument against it.** Random
   entry bars run through the base's own exits rank alongside real signals, five separate
   constructions `[repo-verified: BRIEF.md]`. One reading of that is that the entry carries no
   information. Another, compatible with it, is that the **bar grid plus the exit geometry
   dominates the R distribution**, in which case which bar inside the grid you pick *should* be
   close to irrelevant — exactly what was measured. If that is right, the informative experiment
   is to change the grid, which has never been done. This does not contradict any of the eight
   rules; it proposes a cause for one of the observations behind them.
3. **The geometry finding points the same way.** The win-rate/payoff cancellation was shown to be
   geometric, not informational: with stop and target held fixed, win rate is flat at 0.370–0.423
   across every distance-to-invalidation bucket `[repo-verified:
   workspace/studies/STRUCTURE_FINDINGS.md:14-33]`. Geometry here is denominated in ATR, and ATR is
   a per-bar quantity — so the geometry that was held fixed is itself a function of the sampling
   clock. Whether the cancellation is invariant to the clock is unknown and is the sharpest single
   question in this task.
4. **The class boundary is why nobody looked.** `DIVISION.md` §1 files all of I-12 under Class I
   ("needs to see *who* is transacting"), so the R1 track meets the tape blocker, writes
   INEXPRESSIBLE-DATA, and is right to move on; R3 owns the OHLCV-only world but not this family.
   The volume/dollar/range half falls through the gap between two correctly-executed tracks. This
   is a taxonomy artefact and the manager may want to hear it as one.
5. **The data exists, but not where the published results are.** The frozen snapshot's 1-minute
   files are **5,000 bars ≈ 4 trading sessions** `[measured: csv/raw/{MGC,MES,MNQ,MCL}_1m.csv,
   5,000 rows each, 2026-09-17 → 2026-09-22]`, which cannot support this or anything else
   fine-grained. The usable substrates are `data/{MES,MGC,MNQ}_1m.csv` — 404k–470k genuine
   1-minute bars, **352 RTH sessions**, 2019-01-01 → 2020-05-14, including the Feb–Mar 2020 crash,
   but **Oanda CFD rather than the futures price and a different era, so not poolable with
   `csv/raw`** `[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:250-280]` — and
   `data/archive/{MCL,MES,MGC,MNQ}_1m.jsonl`, which is the futures price
   `[measured: ls data/archive/ → 29 series]`.

### What it would take to know

Stated as unknowns at altitude. The breakdown, the granularity and the order belong to whoever
scopes this (`PIPELINE.md` §3, Mode SCOPE) — including the right to come back and say this is three
sub-tasks, or one, or that it needs a prerequisite named below that nobody anticipated.

- **A provenance answer before any construction.** What does the `volume` field actually count in
  each store? `data/*_1m.csv` is CFD data and its volume is integer in 100.0% of 465k rows
  `[measured: same command as above]`, which is consistent with a *tick count* rather than contract
  volume. A volume bar built on a tick count is a tick bar on a different instrument, which is a
  legitimate object but not the one the literature describes. **If this question is not answered
  first, everything downstream is mislabelled** — and mislabelled-detector findings are this repo's
  most frequent failure mode (`AVENUES.md`, the honest-closure test).
- **An aggregation-error answer.** Building a volume or dollar bar from 1-minute OHLCV requires
  allocating each minute's volume and price path to bar boundaries that fall *inside* the minute.
  The size of that approximation, and whether it biases in a consistent direction, is unknown. Note
  that this repo already has the general lesson about favourable-signed bias: "resampling cannot
  detect a bias whose sign is always favourable; only auditing the fill model can"
  `[repo-verified: scan_reports/2026-09-24_ORB-and-ICT.md:117-133]`.
- **An architecture answer with a price attached.** Can a non-time series be carried by
  `BarSeries` / `SymbolFrame` / the engine at all, or does the wall-clock assumption reach into
  cross-timeframe alignment (`_build_alignment` compares `end_ts`), session state, `rth_only`, the
  `minutes`-keyed timeframe dict, and the Sharpe annualisation that scales by bars-per-year
  `[repo-verified: futures_agents/backtest/metrics.py:31-32,199-215]`? The verdict wanted is
  EXPRESSIBLE / PARTIAL / INEXPRESSIBLE-ARCHITECTURE with the **one specific missing primitive**
  named, per `DIVISION.md` §4 — and, if inexpressible, the cost of changing it.
- **A statistical answer, before any strategy answer.** Do the return distributions actually differ
  in the direction the literature claims, on *this* data — and is the effect large enough to matter
  relative to the sample the deep stores can support? This is a distributional measurement on price
  series, not a strategy sweep, and it either motivates the rest of the task or kills it cheaply.
  **A null here is a complete and valuable answer** and should be reported as one.
- **Only then, and only if the above survives: does any settled finding change under a different
  clock?** The candidates most exposed to the clock are the ones denominated per bar — the ATR-based
  stop geometry, the win-rate/payoff cancellation, and the sub-hourly verdict. This is the part that
  would produce comparative statistics, so it needs the manager's assignment, a paired test with the
  correlation accounted for (**D28**: `T.ab` inflates z by roughly 3.3×), and a deflation statement.

### What discovery deliberately did not investigate

- **Any performance number.** No backtest, no sweep, no expectancy, no z-score. Nothing in this
  task claims that volume bars, dollar bars or range bars make money anywhere, and if a scope
  begins from the assumption that they do it has mis-read this.
- **Whether the literature's claim is true.** I cited it as `[general knowledge]` and explicitly did
  not verify it. Primary sources were not fetched and prior work in this repo has recorded that
  several were egress-blocked `[repo-verified: workspace/studies/ORB_ICT_FINDINGS.md:250-258]`.
- **Any construction.** I wrote no sampler, and I did not attempt to instantiate a non-time
  `BarSeries` to see what breaks. The architecture claim above is from reading four call sites and a
  grep count, not from execution — the 74 `.minutes` references are **counted, not classified**, and
  classifying them is the first thing an architecture answer needs.
- **The three tape-blocked schemes.** Tick, imbalance and run bars are out of reach here and I did
  not pursue them beyond confirming the blocker. If the tape ever arrives they rejoin this avenue.
- **`futures_agents/backtest/costs.py`.** A non-time bar changes the number of bars and therefore
  the number of decision points, which interacts with the cost model — and the cost model already
  has a known under-charging defect on multi-target exits. I did not open it; it is R3's surface.
- **Range bars specifically.** They are the cheapest of the three to construct and the least
  supported by the literature I can cite. I grouped them with volume and dollar bars for the
  blocker analysis and did not think about them separately. If a scope wants a cheap first probe,
  that is a candidate — and that judgement is the scope's, not mine.

---

### MAIN-01 amendment (same burst, 2026-09-27) — R1's I-12 entry, and the claim it contradicts

`R1_flow_auction.md` grew from 223 to 1,700+ lines while this task was being written, and now
carries a full §4-schema entry for I-12 at `:1098-1135`. **Read that entry before scoping this
task.** Three consequences, in order of importance:

**1. The expressibility question is answered; do not re-ask it.** R1's verdict is
**INEXPRESSIBLE-ARCHITECTURE**, missing primitive **"a bar-identity that is not an integer minute
count"**, load-bearing at **nine layers** `[repo-verified: R1_flow_auction.md:1098-1135]`. That is
the same verdict and the same primitive this task reached independently from four call sites and a
grep count, within the same hour, from the other side of the map. Convergence, not duplication — but
it means the third bullet of §"What it would take to know" above (the architecture answer) is now
**largely delivered by R1** and a scope should start from R1's nine layers rather than re-deriving
them. What R1 does *not* supply is the **price** of changing it.

**2. Discovery's claim that R1 contradicts, and the contradiction is load-bearing.** This task says
volume, dollar and range bars "need only `(high, low, close, volume)` per minute, which this repo
has." R1 says time-and-sales is **required** for tick/volume/dollar/imbalance/run bars, and that
"**Range bars alone** can be built from 1-minute OHLCV approximately — and the approximation is
**poor**, because the intrabar path is unknown and a range bar boundary is a path statement"
`[repo-verified: R1_flow_auction.md:1113-1116]`.

**R1 is right about the mechanism and my phrasing was too strong.** A volume-bar boundary is the
moment cumulative volume crosses a threshold; that moment is inside a minute; from 1-minute bars it
can only be snapped to a minute edge. So what is constructible here is a **minute-snapped
approximation** to a volume or dollar bar, not a volume or dollar bar.

**This is now the first question a scope must settle, and settling it may end the task.** The
question is not "is the approximation exact" — it is not — but **"is the minute-snapped
approximation good enough to answer the confound question, and in which direction does its error
push?"** Two notes for whoever answers it:
- The error shrinks as the bar gets large relative to a minute's volume. At the measured medians
  (14 contracts/minute on the MGC deep archive, 9 on MES, 56 on MNQ — `AVENUES.md` addendum), a bar
  sized to give 50–200 bars per session spans many minutes, so a snapped boundary is a small
  fraction of the bar. At the fine end it is most of it. **There is a size range where the
  approximation is defensible and one where it is not, and nobody has drawn the line.**
- If the answer is "not good enough", **that is a complete result and this task should be closed
  `CLOSED-EMPTY` with the reason recorded** — an avenue killed cheaply by an approximation-error
  argument, on the record, is exactly what this ledger is for. It should *not* be quietly rescoped
  to range bars only, because R1 has already called that approximation poor too.

**3. What this task still asks that R1's entry does not.** R1's row answers *what the family is* and
*whether this library can express it*. It does not ask whether the wall-clock sampling choice is a
**confound in findings this repo already treats as settled** — the ATR-denominated stop geometry,
the win-rate/payoff cancellation shown to be geometric rather than informational, and the sub-hourly
verdict whose sample basis is four to nineteen sessions on the frozen snapshot (`AVENUES.md`
addendum). That is this task's question, it is a question about *this repo's conclusions* rather than
about the family, and R1's entry supplies the "Already tested here? **No**" that it depends on.
