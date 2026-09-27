# Scan reports

One dated, self-contained markdown report per strategy scan.

Each report is written to be readable months later without this session's context, and to
be re-runnable: the command that produced it is in the header, alongside the commit the
code was at. Row-level results live in `workspace/`; the bulky per-trade artefacts are run
output, but each study's own `FINDINGS.md` and its audit JSON are committed and are cited
by path in the report header. The reports carry the conclusions, the summary tables and the
cell inventory needed to judge them.

## Naming

```
YYYY-MM-DD_<symbols>_<kind>.md
```

## What every report must state

A scan can be made to say almost anything by choosing what to leave out, so these four are
not optional:

1. **How many strategies were screened.** Without it, a top row cannot be judged, because
   the free-search threshold depends entirely on the search size.
2. **The deflation verdict.** Searching *n* strategies buys roughly `sqrt(2·ln n)` free
   t-units. A report that ranks without saying so invites the reader to trade the top row.
3. **Sample size on every row, and a confidence interval on any win rate.** A 75% win rate
   on 20 trades is statistically compatible with 53%.
4. **What the data could not support.** Window labels the span cannot carry, timeframes
   with too little history, symbols that were excluded and why.
5. **Which nulls are absence and which are non-detection.** Added 2026-09-27 after an audit of
   all four reports found 6 claims invalid of 104, every one of them a misattributed object rather
   than a wrong number. A strategy that never traded and a strategy that traded and lost both
   produce a null, and only the second is a result. So a null needs a firing-rate check on its own
   conditions before it is reported as absence — the programme has now found **five structurally
   zero-trade configurations** and three degenerate ones. A look-ahead power control does **not**
   substitute for this: a cheat is a different strategy that fires normally, so ranking it first
   shows the harness can find an edge in a working detector and says nothing about whether any
   other strategy's detector fired.
6. **Candidates generated, not strategies tested.** 19.0% of generated strategies carry a
   condition that cannot fire, and `Strategy.evaluate` is a strict AND, so one dead condition
   kills the strategy. Write "≥ N candidates were generated, of which an unmeasured subset could
   not trade."
7. **The span, beside the search width.** `t ≈ SR × sqrt(years)`. On the 322-calendar-day span
   these reports rest on, clearing `free_t = 5.46` needed an annualised Sharpe of **5.82**. Quote
   the span with the threshold, or the null reads as a fact about the market when it is partly a
   fact about the window.

## Reading the tables

Both standard rankings mislead when read alone, in opposite directions:

- **Highest win rate** promotes strategies that are right often and earn nothing — high
  hit rate paired with a payoff ratio below 1. Always read the expectancy column beside it.
- **Highest reward:risk** promotes lottery tickets — a 6:1 payoff at a 4% win rate is a
  losing strategy with a beautiful ratio. Always read the win rate column beside it.

Expectancy in R is the column that decides whether a strategy makes money. The other two
describe its shape.

## Audit status

All four reports were audited claim-by-claim on 2026-09-27 against the round-1/2 findings
(`workspace/roundtable/research/R6_report_audit.md`, 104 claims): **64 STANDS, 33 WEAKENED,
6 INVALID, 1 UNAFFECTED**. No invalidation reverses a sign, a verdict, or the deflation
conclusion; all six are misattributed objects. Retractions are applied **in place** in each
report, marked and dated, never by deletion.

The claim to cite in preference to any ranking table is **"selecting is worse than not
selecting"** (+0.022R against +0.057R; −0.024R against +0.064R). It is structurally immune to this
whole class of defect: both arms are the same population on the same bars by the same method, so
every dead detector is in both arms or neither.

## Index

| date | scope | report |
|---|---|---|
| 2026-09-23 | MGC, MES, NQ — 39 cells, 554k strategies | [deep scan](2026-09-23_MGC-MES-NQ_deep-scan.md) |
| 2026-09-24 | 22 studies, 24 agents, 912 matched comparisons | [study programme](2026-09-24_strategy-studies_21-study-programme.md) |
| 2026-09-24 | ORB and ICT — 6 studies, 5 placebo controls | [ORB and ICT](2026-09-24_ORB-and-ICT.md) |
| 2026-09-24 | MGC, MCL — ranking persistence, per-symbol framework, chronological rotation | [ranking persistence and chronology](2026-09-24_MGC-MCL_ranking-persistence-and-chronology.md) |
