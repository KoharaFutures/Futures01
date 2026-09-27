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

EF4 completed the only cell that ran end to end (scalp, MGC + MCL, 5m/15m/30m):

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

Your rule was never tested here before — `allow_overnight` is `False` by default and **no call site
in the repository passes `True`**, so all ~2.97M prior evaluations were flat by their contract's RTH
close. Four things came out of testing it:

1. **It is not expressible at 240m or 1440m.** The window is 22 h = 1320 min = 2³·3·5·11, so
   5/15/30/60/120 divide it and **240 gives 5.5**. Measured: 563–586 bars of every 240m series are
   stamped 16:00 ET and span 16:00→20:00. **The swing programme is 60m only** — which withdrew half
   of two agents' assignments. The better framing, from EF6: never make 240m the *base* grid;
   **120m resampled from the 60m archive has zero straddles and the same 718.88-day span.**
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

## Provenance

EF1 (session harness, parked mid-fix) · EF2 (swing MGC/MCL, parked) · EF3 (swing MES/MNQ, parked) ·
EF4 (scalp MGC/MCL, complete) · EF5 (scalp MES/MNQ) · EF6 (controls, thresholds, forward roll,
adversarial harness) · EF7 (independent harness, running).

Every number above is from an agent's own measurement on `data/archive`, never pooled with
`csv/raw`. No row anywhere is live-eligible. **EF6 could not write its own `FINDINGS.md`** — the
harness refuses report-shaped markdown from subagents — so its content lives in its seven burst
files and in this document.
