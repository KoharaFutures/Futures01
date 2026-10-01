# Pre-registration — PERSYM1, one track per symbol

**Written 2026-10-01 BEFORE any arm was run.** Committed before any result file exists.
Follows `DATA_HUB/OPEN_QUESTIONS.md` rather than repeating `HYPOTHESES.md` (ANCH1), whose 24
out-of-sample confirmations all failed. Scored through the same harness (`workspace/anchors/lib/`)
so PERSYM1 and ANCH1 numbers are directly comparable.

## 0. Data audit run before writing this (my own numbers, not the hub's)

| symbol | 240m | 1440m | verdict |
|---|---|---|---|
| MES | 3080 bars, 2024-10-06→2026-09-30, 0 dup, 1 zero-vol, largest gap 1.88% | 1865 bars, **2019-05-03→2026-09-29 (7.4y)**, 0 dup, largest gap 8.92% | both usable |
| MNQ | 3080 bars, same span, largest gap 2.09% | 1865 bars, 7.4y, largest gap 7.62% | both usable |
| MGC | 3081 bars, largest gap 2.24% | 4010 bars but **largest gap 909.99%** | **daily UNUSABLE** — the splice `RULES_AND_PITFALLS.md` §5 names, confirmed independently |
| MCL | 3019 bars, largest gap 10.89% (crude's real gaps) | **1 bar** | **no daily history**, as recorded |

The 8.92%/7.62% daily gaps are March 2020, not rolls. 30m holds only 2013 bars (~60 days), so
OQ3 is moved from 30m to 60m and that deviation is declared here, before running.

## 1. Track A — exit management (all four symbols). OQ2, the hub's own top untested idea.

The claim: all six of the old desks' live paper fills reached ≥ +0.83R before most of them lost,
and losers' mean best point was +1.23R. So moving the stop to breakeven at +0.8R should convert
losers into scratches.

**Design.** Three exit policies scored on the *same trades*, so the comparison is paired and entry
quality cancels exactly:
- `base` — stop as in ANCH1, target 1.5R
- `be08` — identical, except once a bar has traded +0.8R in favour **without** touching the stop,
  the stop moves to the fill price from the **next** bar onward (never within the arming bar)
- `x08` — full exit at +0.8R

**Entries are deliberately unselected**, so the overlay is the only thing under test: every
eligible RTH bar, direction fixed two ways — `mom` (prior bar closed up → long, down → short) and
`rev` (the mirror). `one_at_a_time` is OFF for the paired test so the same trade exists under all
three policies; the account-realistic version is reported separately.
**Prediction:** paired mean(be08 − base) > 0 at t ≥ the §6 bar, on each symbol.

## 2. Track B — MES and MNQ daily, 7.4 years, roll-clean. OQ6.

At 1865 daily bars a single pre-registered test needs far less than an intraday one. Two rules,
one parameter each, both standard, neither tuned:
- `B1 breakout`: close above the highest close of the prior **20** sessions → long (mirror short on
  a 20-session low). Stop 1 ATR14, target 2R, 10-bar time exit.
- `B2 reversion`: close below the **2σ** band of a 20-session mean → long (mirror short above).
  Same stop, target, time exit.

**Prediction:** B1 clears the bar on both MES and MNQ (trend-following is the one thing that has
ever worked on index futures at daily horizon); B2 does not.

## 3. Track C — MCL momentum on 240m and 60m. OQ5.

The parked finding: 97% of observations positive, beat control on both session arms, t 2.97 — never
pre-registered or retested. Stated now as a rule: a bar closes beyond the prior **3**-bar range in
the direction of the 10-bar net move → enter next open with the move, stop 1 ATR, target 1.5R,
12-bar time exit. Run on MCL 240m and MCL 60m.
**Prediction:** positive on both timeframes, 240m stronger than 60m.

## 4. Track D — MGC value-area edge fade. OQ3, moved from 30m to 60m (declared in §0).

Build the prior session's 60m profile. When price trades to the value-area high and closes back
inside, short with target = the prior session's POC; mirror at the value-area low. Stop beyond the
edge by 0.5·ATR + 1 tick.
**Prediction:** positive on MGC (the only symbol where classic profile levels had a positive sign
on 4/6 cells).

## 5. Track E — MGC fib trend-failure, resting limit instead of a market order. DIAGNOSTIC ONLY.

`OPEN_QUESTIONS` #8. The ANCH1 candidate (`ANCH1_MGC_fib_trend_failure`, OOS n=33, +0.4324R,
t +2.705) failed on funding: a next-open market fill gave a median 20.4-point stop ($204) against a
$120 budget, so the account took 6 of 33 trades. A resting limit **at the level** removes the fill
gap and should take the stop to ≈0.5·ATR.

**This is not a confirmation and is not counted in §6.** The rule was selected using these same
out-of-sample bars, so re-scoring them cannot re-establish significance. The only question asked
here is mechanical: *does the limit entry make the stop fundable, and at what cost in fill rate?*
Any expectancy figure it produces is quoted as in-sample-contaminated and needs new bars.
Also reported: the 0.786-only split (`OPEN_QUESTIONS` #9) under the same caveat.

## 5b. AMENDMENT, made before any PERSYM1 arm was scored

On wiring the harness I found that applying ANCH1's intraday session gating to 240m bars leaves
**one eligible entry bar per session** (a 240m bar labelled 08:00 spans 08:00–12:00, so for MES only
the 08:00 and 12:00 bars touch RTH, and the "no entry in the final session bar" rule removes the
second), and the session-exit rule closes every 240m trade at the first session-close bar — so a
12-bar hold could never run. That makes Tracks B and C unmeasurable for mechanical reasons rather
than market ones.

**Amendment:** for **tf ≥ 240m** there is no intraday session gating and no session exit. Those are
swing timeframes — a 240m bar is 4 hours and a 12-bar hold is 2 trading days — so trades end on the
stop, the target, or the time exit only. 60m keeps ANCH1's gating unchanged, because that is the
timeframe on which this project's session rules were measured.

No PERSYM1 result had been computed when this was written; the only thing I had seen was the bar
census in §0 and the eligible-bar counts above.

## 6. Trial count and the bar

New confirmation tests, each run once on its out-of-sample slice:
Track A 2 policies × 4 symbols = 8 · Track B 2 rules × 2 symbols = 4 · Track C 2 · Track D 1 =
**15**. Luck bar √(2·ln 15) = **2.327**. Track E adds 0 (diagnostic).

Scoring, controls and the account model are unchanged from `HYPOTHESES.md` §2–§3: next open ±1
tick, stop wins same-bar ties, φ per round turn from the contract spec, 60/40 time split, direction
placebo ×10, level placebo ×10 where a level exists, 200-shift shift-null, $50,000 account with a
$120 risk cap. A result is an edge only if it clears the bar **and** beats its placebos **and**
holds sign in both halves of its out-of-sample slice.
