# BT1 burst 01 — ALGO-1: the absorption shape, built and asked about

**One algorithm, then stop.** No second algorithm, no measurement.

## What I read

`PIPELINE.md` and `OWNERSHIP.md` in full, `BRIEF.md` in full, then R1's
`R1_flow_auction.md` selectively: §7 Q1–Q3 (`:1676-1790`), R1-D1 **I-2**
(`:639-677`), the `orderflow` and `imbalance` proxy audits (`:283-345`,
`:479-523`), the R1-D4 addendum (`:524-564`), R1-D2 **Part B** and **B.6**
(`:1405-1509`), and the **R1-D5** primitive ledger (`:1510-1547`). Then the code
each claim points at, plus `DEFECTS.md` D28/D36/D37/D38/D42.

**Every R1 citation I checked reproduced.** `detect_imbalances` really does gate
on `r_mult >= 2.0 and v_mult >= threshold * 0.6 = 1.2`
(`futures_agents/indicators/structure.py:452-462`); `estimated_delta` really does
return `0.0` when `rng <= 0` (`futures_agents/data/bars.py:110-111`);
`measure_custom` really does build a frame and run it without any registration
hook (`workspace/studies/toolkit.py:289-293`). I found nothing in R1's findings
that was wrong; I found one claim whose **scope** I think should be narrowed, and
that is Q4 of my verify message rather than a correction.

## What I chose to build, and whether it was the right candidate

I took the candidate as dispatched — §7 Q2 rank 1, high volume / LOW range —
and I did **not** find a better one in R1's findings. The runners-up are ranks
2–3, anchored and RTH-anchored VWAP, which R1 itself classes as
*implemented-but-unwired*: `build_anchor_vwap` and friends exist and nothing
consumes them. Those are a wire, not a build, and a wire is the weaker thing to
spend a fidelity loop on — the question "is my code what the research said" has
an almost trivial answer when the code already exists in the library. Rank 1 is
the only item on that list where the arithmetic has to be *decided*, which is
exactly where the fidelity loop earns its cost.

## What I built

`code/absorption.py` (315 lines), `code/test_absorption.py` (241),
`code/frequency.py` (146). The algorithm is ~40 lines of the first file; the rest
is the registration plumbing D38 makes mandatory, and the reasons.

One detector, `absorption_series`, causal and same-length-as-input, exposed as
two conditions: `absorption_bar` (SIGNAL, direction from close position) and
`absorption_present` (FILTER, direction-free). Both in a new `absorption`
condition group, which no template names — so importing this module cannot change
what any existing sweep builds `[repo-verified: CONDITION_GROUPS is read only via
`.get(group)` for groups a template names — combinator.py:366,
coverage.py:134]`.

`[measured: python3 -m pytest -q tests → 817 passed]` as a baseline. I have not
touched a line under `futures_agents/`.

## The eleven choices, and the four that need R1

Full list in `ALGOS.md`. The load-bearing ones:

1. **Norm = 20-bar trailing mean, excluding the current bar**, bit-identical to
   `detect_imbalances` (I re-sum the slice per bar rather than rolling a sum,
   specifically so the two `r_mult`s cannot differ by accumulated float error).
   The rejected alternative — `relative_volume`'s time-of-day norm — changes the
   population **5–27×**.
2. **Thresholds verbatim: `v >= 2.0`, `r <= 1.0`, inclusive.** Not searched.
3. **Direction from close position**, which is the only visible half of R1's
   B.2 — and is also `delta_confirms_bar`'s first clause, so the novel content of
   ALGO-1 is the gate alone.
4. **Fires on the absorption bar**, not on a following failure-to-extend bar.
   The sequence is the operating form and is a second algorithm.

## What I found that nobody asked for, and which is the burst's real content

Running the frequency census before asking anything, because a fidelity question
about thresholds is unanswerable without knowing what they select:

| cell | bars | ALGO-1 | rate | `detect_imbalances` |
|---|---|---|---|---|
| MGC 1h | 5000 | 11 | 0.22% | 288 |
| MGC 15m | 3755 | 2 | 0.05% | 212 |
| MGC 5m | 5000 | 9 | 0.18% | 216 |
| MCL 1h | 5000 | 41 | 0.82% | 336 |
| MCL 15m | 3753 | 5 | 0.13% | 220 |
| MCL 5m | 5000 | 11 | 0.22% | 277 |

**R1's thresholds, taken literally, put 4 of 6 cells below `FLOOR = 20` before an
exit model exists.** And the cause is not a coding choice: volume and range are
Pearson **0.537–0.885** correlated at bar level, conditional on `v_mult >= 2` the
median `r_mult` is **1.77–2.00**, and only **0.51–5.85%** of high-volume bars
have range ≤ norm. A bar that takes double its normal volume almost always moves.

So the candidate reading — and the one I put to R1 — is that *as a single-bar
OHLCV object the absorption shape is close to absent at 5m–1h on these
contracts*, which would be a complete result requiring no backtest. **I did not
relax a threshold to manufacture sample**, and that restraint is the whole point:
`v >= 1.5` would have handed me 38–117 signals per cell and a story.

## A check that failed, and the fix

My first `register_frame` stored only populated bars, so the miss counter
reported the 20 warm-up bars as grid mismatches — the very ambiguity `_read`'s
docstring claimed to resolve. Now **every** bar of a registered frame gets a key,
warm-up bars holding `None`, with a sentinel distinguishing absent-key from
None-value. An absent key now means only one thing: wrong grid, or nobody
registered (D38). Cleared registration ⇒ 0 firings **and** 1,500 logged misses.

## What I asked

`msgs/02_BT1_R1_verify-ALGO-1.md`, four questions: **Q1** which volume norm,
**Q2** whether the shape carries a direction and whether close-position is it,
**Q3** whether the near-empty census *is* the finding or whether the intent
tolerates one named relaxation, **Q4** whether the `estimated_delta` zero-range
claim should be narrowed (it is exact at `rng == 0`, which is 0.0–0.6% of bars,
and does not extend to the neighbourhood because CLV is normalised by range —
while the general "CLV cannot tell 'no aggression' from 'absorbed aggression'"
form is stronger and survives).

Two board items in `REQUESTS.md`: **REQ-1** may a backtester measure on
`data/archive/` rather than the frozen `csv/raw/` (the only sample increase that
does not touch thresholds); **REQ-2** D37 binds the template layer only — a
single precomputed condition can read as many bars as it likes, so ordered chains
are inexpressible *as confluences* and buildable *as single conditions*, and that
narrower statement should be on record before another burst re-derives it.

## Where I stopped, and why

At ASKED. ALGO-1 runs, passes 33 engineering checks, and has produced **no**
expectancy, win rate, R, trade count or t — by construction, not by omission:
none of my three files computes one. PIPELINE §4 says a number from an
UNVERIFIED algorithm is an unknown quantity rather than a weak result, and the
two choices most likely to be wrong (the volume norm, the direction rule) are
precisely the two that would change what such a number *meant*. Burst 2 begins
with R1's verdict.
