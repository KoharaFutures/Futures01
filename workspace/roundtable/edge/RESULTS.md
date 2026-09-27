# Edge programme — results

**Request:** find and test strategies for profitability, and produce a top 10 per symbol for a swing
setting and another for a scalp setting, with every position inside 18:00 ET → 16:00 ET and nothing
held across 16:00–18:00.

**Seven agents, four symbols. This is the answer.**

---

## The headline: the two requirements are arithmetically incompatible on this data

This is not "we searched and found nothing." A top 10 has to satisfy two conditions at once, and on
this data **no search width satisfies both.**

1. **It has to be a selection.** Ten names chosen from twelve is not a ranking. A population large
   enough that ten qualifiers is a genuine choice needed **≈465 screened** on MGC 60m — measured:
   465 screened gave 16.2 qualifiers at a 20-trade floor, while 84 screened gave **2.4**, at which
   point top-10, whole-universe and random-10 return **the identical number**.
2. **It has to clear its own threshold.** Searching *n* things costs `free_t = sqrt(2·ln n)`, and a
   real edge earns `t = SR × sqrt(years)`.

Put together, and verified independently:

| | swing 60m (718.88 d, √y 1.403) | scalp 5/15/30m (57.90 d, √y 0.398) |
|---|---|---|
| n ≈ 465 (enough for a real selection) costs | free_t 3.505 → **needs Sharpe 2.498** | free_t 3.505 → **needs Sharpe 8.803** |
| search budget if the true Sharpe is 1.5 | **9 variants** | **1** |
| search budget if the true Sharpe is 2.0 | **51 variants** | **1** |
| search budget if the true Sharpe is 3.0 | 7,022 | 2 |

**Read the two rows against each other.** To have ten qualifiers you must screen hundreds. To stay
inside the budget a reachable threshold permits, you may screen tens. **Those sets do not intersect
at 57.90 days, and on every measurement taken here they do not intersect at 718.88 days either.**

So the deliverable is not ten rows per symbol. It is this: **on this span, a ranked top 10 cannot be
evidence, whatever it contains** — and the reason is the width of the search it presupposes, not the
quality of the strategies in it.

---

## What was measured anyway, and what it returned

### The index complex at scalp timeframes — EF5, 21,060 strategies

**The largest t-statistic anywhere in EF5's search is 3.82 and it belongs to a placebo.** Largest
real t: 3.116. **No ranked top 10 is publishable for MES or MNQ.**

| | count |
|---|---|
| declared strategies | 21,060 |
| **never fire at all** | **60–82% per cell** |
| could possibly reach a 20-trade floor | **1,452 of 21,060 (6.9%)** |
| arm-cells where rank 1 is a placebo | **7 of 12** |
| arm-cells holding ≤ 8 qualifiers, so no ten exist | **3** |
| qualifying universes with negative expectancy net of costs | **7 of 12** |
| arm-cells where the **placebo universe beats the real one** | 3 (all MNQ RTH) |

So for most of this population the null is **"the detector never fired"**, not "we measured
absence" — separated per cell, with a positive control firing 3,096 times through the same
evaluator and a cross-check that VOID carriers are a strict subset of zero-signal strategies
(0 violations, 12/12 cells).

**One cell had real rules beating their own placebos: MNQ 15m with `rth_only=False`** (sign z +3.41,
Wilcoxon +2.82). EF5 stressed it four ways. It **survives** a leak-free chronological holdout
(OOS +0.2452R vs placebo −0.0141R, z +3.05, no decay) and a direction-matched drift control. It
**fails** two:

- **Effective sample size.** Mean pairwise trade-ledger Jaccard **0.0874** → `n_eff = 8.56` of 31.
  Deflated sign z = **2.17 against a threshold of 2.229** — it does not clear, at the most generous
  denominator available.
- **The tape.** Across contiguous thirds: +9.25% tape → z +4.38; **−1.69% tape → z +0.19**;
  +3.86% → z +2.69. **The one down-tape third has none of the effect.**

**And MULTI_TIMEFRAME tops that cell for a reason that is not a multi-timeframe finding.** Its eight
real rows are **0.59–0.82 long** on a **+12.186%** tape, and `mtf_aligned` fires when timeframes
agree — which in a persistently rising market *is* long. A direction-count-preserving shuffle reaches
ranks 7/9/11/14, and the effect vanishes in the down third. MES is the counter-example at 0.478–0.563
long, inside EF4's random baseline. **Reporting that cell as "multi-timeframe alignment works on MNQ
scalp" is precisely the error a top-10 table invites.**

**It also reproduced the programme's central negative inside its own best cell:** select the top 10
in sample, read out of sample → **+0.2202R against the whole qualifying universe's +0.2980R.**
Selecting is worse than not selecting, on the overnight regime nobody had measured.

**EF5 found and retracted a leak in its own first holdout** — it gated on `t ≥ 0` over the *full*
span then read expectancy on the last 40% of it, and withdrew a sign z of 6.19.

### Two corrections to figures this programme was using

1. **Cost is not "15.0% of R at 5m".** Measured per symbol and geometry: **MES 5m median 21.0%**,
   reaching **39.4%** at the tightest geometry, against **MNQ 5m 4.78%** — a **4.4× difference inside
   one index complex**, because MNQ's larger min-stop makes its R worth far more dollars against an
   identical fee.
2. **The 86.3% clock-close rate does not transfer to scalp.** I relayed EF1's 60m/240m figure to EF5
   as though it applied. In its cells the clock share is **2.8%–30.8%** and the **stop is the dominant
   exit in 11 of 12 arm-cells** (26.5–61.7%). So a ranked list there ranks strategies, not entry
   signals on a clock exit — **except MES 30m RTH at 53.1%**, where the warning holds verbatim, and
   that cell has 7 qualifiers anyway.

### Two more structurally-zero configurations, bringing the count to seven

- **`volatility_compressed` under `rth_only=True` is VOID at MES 15m** — 0 of 1,066 RTH bars, because
  `atr_percentile` is taken over the whole 24-hour history and an RTH bar is essentially never in its
  bottom 30%. BREAKOUT nails that condition into `base_filters`, so **all 138 MES 15m BREAKOUT
  strategies take zero trades.** EF5's measurement alone; needs replication.
- **`session_extreme_sweep` is VOID under this programme's own session rule.** All **48** fires across
  both symbols and three timeframes fall between **16:00 and 16:55 ET** — inside the forbidden window.
  A dead member of a required group, with a different cause from the previously recorded one.

### The hazard EF5 flags rather than clears

**No roll audit inside its 57 days.** `yahoo.py` has `auto_adjust=False` and no roll handling, so a
roll gap would read as a return — and **MNQ's +12.19% drift is doing real work in its conclusions.**
It names the cheapest possible follow-up: check ES/NQ front-month roll dates against its 41 cycles.

---

EF4 completed the other scalp cell (MGC + MCL, 5m/15m/30m):

| | MGC | MCL |
|---|---|---|
| distinct signal sets reaching the trade floor | 401 | 360 |
| sign-consistent IS/OOS, positive in every fold | 19 | 3 |
| **clearing their declared threshold (4.441)** | **0** | **0** |
| largest *t* anywhere | +2.62 | **+1.12** |

**MCL's best fails even `free_t = 1.177`** — the floor for a *single pre-registered* hypothesis, the
most generous number in the codebase. So on MCL the answer is nothing at every threshold.

**The best row anywhere states the bound in one line:** an annualised Sharpe of **6.58**, a figure
that does not occur in real futures, still produced only t = +2.62 on 0.1585 years — **41% short** of
what its search width demanded. Verified: 6.58 × 0.398 = 2.62.

EF6's adversarial harness then attacked a real MGC 60m top 10 and **killed all ten rows.** Its
deflation gate killed 10 of 10 on its own (largest t +1.965 against free_t 3.505), and 6 of 10 were
underpowered before that. Six of the ten were MULTI_TIMEFRAME and **two pairs were exact clones**, so
the "top 10" was effectively a top 7.

### The one configuration that looked like a result, and why it is not

EF6 searched nine forward-roll configurations. One — MGC 15m, 28-day lookback, 7-day folds, trade
floor 10 — gave top-10 **+0.1346R** against a universe of +0.0306R, **z = +2.48**, beating the
universe in 3 of 4 folds. Reported alone that is the programme's first live-eligible finding.

It is not, and EF6 demolished it itself: the selection edge **flips sign twice** across floors
{5, 10, 20} on the same ledger (−0.0191R, **+0.1040R**, −0.0364R); it rests on **4 folds and 197
trades**; z = 2.48 sits below free_t 3.505; the Sharpe it implies is 6.23 against 8.80 required; and
**nine configurations were searched to find it**, which owes free_t(9) = 2.10 on top. *That is what
data-mining bias looks like from the inside, and all nine are reported.*

---

## The session rule: what it actually bought

Your rule was never tested here before — `allow_overnight` is `False` by default and no call site
passes `True`. **But my stronger claim, that all ~2.97M prior evaluations were therefore flat by
their contract's RTH close, is false.** `engine.py:470`'s gate is an `and`, and
`exit_at_session_close` is False on **58 of 184 MGC and 90 of 185 MNQ** generated strategies — so a
third to a half of the prior population held overnight with **no session control at all**, violating
the window on 139/626 MGC and 986/1292 MES trades. There are three regimes to compare, not two.
Four things came out of testing it:

1. **It is expressible at 240m — I got this wrong and corrected it.** I withdrew the 240m cells on
   EF6's `1320 % tf` test. That is the wrong test: 1320 is the window *length*, and nothing requires
   a holding period to contain a whole number of bars. What the rule needs is the **flat (960 min)**
   and the **reopen (1080 min)** on boundaries. Verified: `960 % 240 == 0`, so **16:00 IS a 240m
   boundary** — 491–497 `ON_BOUNDARY` bars per symbol, zero `INTERIOR`, and EF1's saturation run
   gives 0 violations. `1080 % 240 == 120`, so the `[16:00,20:00)` bucket is vetoed and the earliest
   entry is 20:00: **the effective cycle is 20 hours, not 22.** A caveat per row, not an inability.
   **1440m genuinely cannot carry it** (4,008/4,008 MGC bars `INTERIOR`). The 240m arms are
   reinstated.
2. **At the generated default it changes exits, not entries.** `rth_only` defaults to `True` on
   **314/314** generated strategies, and MGC RTH (08:20–13:30) and MCL (09:00–14:30) sit wholly
   inside one cycle. So the rule buys **+2h30m on MGC, +1h30m on MCL, and nothing on MES/MNQ**,
   whose close already is 16:00. Reaching overnight entries needs `rth_only=False`.
3. **It made the data cleaner.** Only **17 of 53,252 MES trades (0.032%)** straddle a window
   boundary against the prior programme's 2.47% — a **77× reduction**, because nothing can span more
   than 22 hours.
4. **And it is one hour stricter than the exchange.** The real CME halt for MGC/MCL is 17:00–18:00,
   so the rule forbids ~4.4% of 5-minute bars that actually trade.

**The one genuine positive:** `rth_only=False` multiplies raw signals per strategy by **2.5–2.9×**,
and the SESSION arm is better populated than RTH in **every one of twelve** scalp cells. More trades
sharpen `t = √N·mean/sd` without lengthening the span. But D24 priced that route at a *loss* of
expectancy under the old regime — and EF4 notes D24's sign may not transfer, since it was measured
where the position was flattened at the contract's close. **That is the one open arm worth running.**

---

## Roughly half of every swing trade exits on the clock

`46.2%` of MGC 60m trades (3,763 of 8,150) close at the window boundary rather than on their thesis;
MCL 3,454, MES 4,001, MNQ 2,182. Under a 22-hour ceiling the time-stop dimension disappears
entirely — **`TIME` exits are 0 of 103,191 trades**, because the catalogue's smallest
`time_stop_bars` is 30 primary bars against a 22-bar cap.

So a swing row under this rule is substantially a statement about **when the clock ran out**, not
about the exit the strategy chose.

---

## What the controls were worth, which is the part that makes the rest trustworthy

Four faults were found in the placebo machinery, three created by the window and one original:

- **Count-matching broke, and the bias reverses sign by cell.** On MNQ 60m a 16-signal base got a
  12-signal control — a 25% deficit — because 1 in 6 RTH bars is illegal; on MNQ 15m the sign
  reverses. MGC untouched.
- **`placebo_shuffle` is not a control, it is the base.** It permutes direction *labels*, so on four
  MEAN_REVERSION bases with long share 0.000 it returned **bit-for-bit identical** results. This
  re-reads one of the five placebo constructions this programme cites.
- **The brief's timestamp shuffle did not exist in the repo.** Now built, preserving time-of-day
  profile — which matters, because this repo has two settled time-of-day effects to confound with.
- **Realised placebo counts overshoot 2.0–3.3×.** Real signals fire in bursts and the engine culls
  most of a burst; scattered placebo entries overlap nothing. **A control with 3× the sample has a
  √3-smaller standard error and wins anything scored on *t*.** Fixed by matching realised counts.

And EF6 found two faults in **its own** verifier: a single placebo draw gives a coin-flip verdict
(two statistical clones got opposite verdicts, p = 0.028 vs 0.1224), and its first power gate buried
four significant separations.

**A third innocent explanation for an exact zero now exists.** Between two arms, an exact zero can
mean a D48 id collision, a **vacuous selection** (top-10 *is* the universe), or the settled finding
that operating axes do not move expectancy. The first two must now be excluded by name.

---

## What is now known about the null itself

The programme's settled negative **replicates under the new rule, on the new substrate, at 60m** —
selection-versus-universe is negative on MGC and everything sits at or below its null. It was never
a property of the RTH-only regime or of `csv/raw`.

But one nuance the prior study could not see: on MGC the top 10 **does** beat a random 10 from the
same candidate set, by +0.019R to +0.031R. **So the ranking is not uninformative — concentrating
into ten names costs more than the ranking gains.** That is a different and more useful statement
than "selection does not work", and it points at position count rather than at rule quality.

---

## What I would do instead, in order

1. **Stop ranking at scalp timeframes.** Pre-register one or two hypotheses, measure exactly those,
   and report against the 1.177 floor with the required Sharpe attached. **Report the whole
   qualifying universe's expectancy per cell instead of a top 10** — it uses the full sample, needs
   no selection, and beat the top 10 in 4 of the 5 configurations where a selection existed.
2. **Run the `rth_only=False` paired arm at 60m.** It is the one route the measurements actually
   endorse: 2.5–2.9× the signals, better-populated cells, and a regime nothing in this repo has ever
   tested. Paired, never swapped — and D24's sign needs re-measuring under a rule that permits the
   hold.
3. **Buy span, not width.** `free_t(10)/1.403 = 1.53` is demanding but real at 60m; the same
   threshold at ten years needs Sharpe 1.40 and at twenty-five years 0.89. The blocker is that
   `yahoo.py` has `auto_adjust=False` and **no roll handling**, so a longer span buys D40 at every
   roll. **The roll audit is the highest-value unbuilt thing in this repository.**
4. **Fix the guard, not the search.** `_id=None` is not sufficient — `strategy_id` hashes condition
   *names*, so a fresh id can still collide, and EF4 measured 400–540 collisions per cell in its own
   controls. The guard is an arm-id uniqueness assertion at emission.

---

## EF7: killed by the session limit, with its findings intact

EF7 was terminated mid-sentence by the API rate limit — the exact failure the throttle was built to
prevent, and it fired anyway, on the one agent whose job was to independently validate the harness.
**Its work survived in full** — 35 KB of findings, seven bursts, four JSON artefacts, the last
written two minutes before it died. Only its closing three-engine comparison was lost. That is the
write-as-you-go rule paying for itself; without it the session limit would have cost a whole agent.

Its validation is green: **0 violations** across four symbols on `data/archive`, with 474–497 bars
per symbol inside the forbidden window and 979–1,004 cycle ends identified.

**And it found a defect nobody else did, while building a control that failed.** `engine.py:470-473`
measures `minutes_since_open` from the RTH open of the bar's own calendar date and **never clamps
it**, so with the shipped `exit_at_session_close=True` **every position entered at or after 12:30 ET
closes on its own entry bar** — the whole afternoon, evening and overnight session on MGC. Verified.

Combined with EF1's finding that `exit_at_session_close` is False on roughly a third to a half of
generated strategies, **the prior programme had two incoherent session regimes and no coherent one**:
half with no session control at all, half unable to hold an afternoon or evening position for a
single bar. Neither is "flat at the RTH close", which is the claim I made and have now retracted
twice — once on EF1's evidence, and now with the mechanism.

**The outstanding item EF7 named as its own next step:** run its saturation instrument against its
engine, EF1's and EF3's, and require 0 violations and `max_hold <= 1320` from all three. One command
each. *Three engines agreeing under saturation is a statement about the series; three agreeing on
their own populations is not* — which is precisely how this harness cost two defect cycles.

## Provenance

EF1 (session harness, parked mid-fix) · EF2 (swing MGC/MCL, parked) · EF3 (swing MES/MNQ, parked) ·
EF4 (scalp MGC/MCL, complete) · EF5 (scalp MES/MNQ) · EF6 (controls, thresholds, forward roll,
adversarial harness) · EF7 (independent harness, running).

Every number above is from an agent's own measurement on `data/archive`, never pooled with
`csv/raw`. No row anywhere is live-eligible. **EF6 could not write its own `FINDINGS.md`** — the
harness refuses report-shaped markdown from subagents — so its content lives in its seven burst
files and in this document.
