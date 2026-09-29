# EF4 burst 06 — measurement: rule 7, the split sample, the selection test, walk-forward, placebos

All numbers on `data/archive/`, harness EF1 `SessionWindowEngine`, 41 sessions of
18:00 ET → 16:00 ET, 2026-07-29 → 2026-09-25. Declared population: Track A n = 36
(`free_t` 2.677), Track B n = 19,152 (`free_t` 4.441). **Provisional until EF1 validates.**

Full tables are in `../FINDINGS.md` §4, §7, §8, §9, §11, §12. This burst records the three
things that changed my reading of my own results while I was measuring them, because a burst
log is for the reasoning and the file is for the conclusion.

## 1. The selection test came out the wrong way round, and it took four controls to understand why

First reading: the in-sample top 10 beat the whole qualifying universe out of sample in 4 of 6
cells — the opposite sign to the programme's settled negative. I did not report that, because a
result reversing a settled finding on 41 sessions owes its controls first.

- **RANDOM-10** lands within 0.0003 R of the trade-weighted universe, so the pooling is sound and
  the top 10 sits at percentile 0.999, 1.000, 1.000, 0.417, 0.402, 0.985.
- **MATCHED-10** (matched on in-sample trade count, because the top 10 trade *less* than the
  universe: median 57.5 vs 131.5 at MGC 5m) leaves it at 0.980, 1.000, 0.995, 0.620, 0.729, 0.960.
- **Direction** is not it: top-10 long share 0.467–0.539 against random-40's 0.498–0.535, and both
  LONG-only and SHORT-only versions are positive on three of four cells tested.
- **REVERSE TIME kills it.** Select on the last 16 sessions, score on the first 25: **selection
  wins in all six cells.** A rule that works equally well backwards is not forecasting.

And then the interpretable part: **the top 10 is one condition wearing ten names** —
`candle_engulfing` 8/10 at MGC 15m, `imbalance_pullback` 9/10 at MGC 30m, 9–13 distinct conditions
across ten "different" rows, mean pairwise condition Jaccard 0.12–0.33. That is the ORB report's
lesson exactly: *a league table of the best rule sets containing a condition measures the search,
not the condition.* It is why the deliverable is de-duplicated by signal set, and why it collapses
from ten rows to five (MGC) and three (MCL).

## 2. Rule 7's "sub-hourly graveyard" is real at 5m — and the placebo says it is **not** a signal-quality effect

At a 30-trade floor the share of the screen with positive net expectancy is **12.2% (MGC 5m)** and
**2.9% (MCL 5m)** — inside and below rule 7's 11–16% — against **36.0% / 37.8%** at MGC 15m/30m and
23.9% at MCL 30m. So the graveyard is **5-minute-specific, not sub-hourly-generic**, and its
boundary sits one timeframe coarser on MCL than on MGC.

My first decomposition said gross was also degraded at 5m (32.1–32.5% positive against 43.9–50.7%
at 15m/30m) and I wrote that up as "the signal is worse at 5 minutes". **The placebos corrected
me.** Implied placebo gross by cell:

| cell | placebo mean **net** E | cell median cost | **implied placebo gross** |
|---|---|---|---|
| MGC 5m | −0.1309 | 0.0927 | **−0.038** |
| MGC 15m | −0.0123 | 0.0503 | +0.038 |
| MGC 30m | −0.0228 | 0.0346 | +0.012 |
| MCL 15m | −0.1115 | 0.1254 | +0.014 |
| MCL 30m | −0.0647 | 0.0835 | +0.019 |

**A count-matched random entry has negative gross expectancy at 5 minutes and positive gross at
15 and 30.** The entries carry no information by construction, so the 5-minute gross degradation
cannot be about signal quality. It is the exit geometry meeting a 5-minute bar grid: a 1.0-ATR stop
with a 1.5 R target, the engine's pessimistic stop-before-target tie rule
`[repo-verified: engine.py:398-403]`, and a 2-hour time stop, evaluated on bars six times finer.
**So "sub-hourly is a graveyard" is, in the part that is not cost, a statement about exits rather
than about signals — and it is measurable with random entries, which means it needs no search at
all to establish.**

## 3. Three pre-registered arms are significantly worse than their own placebos

MGC 5m, 20 count-matched controls each: `A1_ON_SWEEP` percentile **0.00**, z = **−2.99**;
`A6_ON_COMPRESSION` percentile **0.00**, z = **−2.69**; `A4_VWAP_BAND` percentile 0.05, z = −1.49.

A placebo beating a real signal has happened five times in this repository already. **A real signal
losing to its own placebo at z = −3 is a different statement**: the condition is not uninformative,
it is *anti*-informative at that timeframe on that symbol, and since both arms share the exit, the
sizing and the session rule, the difference is attributable to where the entry fires. It is also
the honest limit of what my span can produce — **rejections, not confirmations** — because a
rejection and a confirmation need the same power and only the rejections found it.
