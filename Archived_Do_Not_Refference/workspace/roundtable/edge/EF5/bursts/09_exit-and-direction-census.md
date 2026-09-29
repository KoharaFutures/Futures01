# EF5 burst 09 — what actually closes a trade in my cell, and how long the rows are

Two cell-level properties the coordinator requires beside every row.
`[measured: EF5/code/exit_census.py → EF5/out/exit_and_direction_census.json; full declared
population, EF1's `SessionWindowEngine`, rows with ≥ 20 trades]`

## 1. **EF1's 86.3% clock-close figure for MNQ does NOT transfer to scalp timeframes.** It is a 60m/240m fact.

| arm-cell | **clock close** | stop | target + breakeven | time stop |
|---|---|---|---|---|
| MES 5m RTH | 13.1% | 48.1% | 34.3% | 4.5% |
| MES 5m SESSION | **5.0%** | 53.7% | 34.3% | 6.9% |
| MES 15m RTH | 36.2% | 37.5% | 26.4% | 0% |
| MES 15m SESSION | 18.7% | 46.0% | 33.3% | 2.0% |
| **MES 30m RTH** | **53.1%** | 26.5% | 20.4% | 0% |
| MES 30m SESSION | 34.1% | 33.6% | 32.0% | 0.3% |
| MNQ 5m RTH | 7.5% | 61.7% | 28.8% | 2.0% |
| **MNQ 5m SESSION** | **2.8%** | 59.5% | 33.3% | 4.4% |
| MNQ 15m RTH | 15.8% | 60.5% | 23.6% | 0% |
| MNQ 15m SESSION | 8.3% | 53.4% | 36.9% | 1.4% |
| MNQ 30m RTH | 30.8% | 58.6% | 10.6% | 0% |
| MNQ 30m SESSION | 19.0% | 55.5% | 25.3% | 0.1% |

**EF1 measured MNQ at 86.3% clock-close with `SESSION_CLOSE 850, STOP 104, TARGET 28, BREAKEVEN 3`.
In my cell MNQ's clock share is 2.8% to 30.8%** — a 3× to 30× difference, in the direction that
*restores* the exit geometry. The mechanism is arithmetic: reaching 16:00 from an entry takes up to
~276 five-minute bars but only ~13 thirty-minute bars, so at 5m the stop or the target is reached first
almost always, and at 30m the clock competes.

**Consequence, and it is the opposite of the warning I was given:** in **eleven of my twelve arm-cells
the stop is the dominant exit (26.5–61.7%)** and the clock is a minority. So a ranked list in my cell
**is** ranking strategies — entry *and* exit — and an "exits make no difference" finding here would be a
result rather than a restatement of the clock.

**The one exception is MES 30m RTH at 53.1% clock-close**, where the clock is the majority exit and the
warning does apply verbatim. That cell also has only 7 qualifying rule sets, so it was already
unreportable.

The gradient is monotone in timeframe and in the gate, both ways it should be: clock share rises with
timeframe (5m → 30m) and is roughly halved by `rth_only=False` (SESSION admits overnight entries, which
have more room before 16:00 relative to... no — which are *further* from 16:00 in bar count, so the
stop/target resolves first more often). **Time stops are near-inert** — 0–6.9%, and exactly 0% in all
four 15m/30m RTH cells — which is EF2's finding for the swing cell reproduced here: `time_stop_bars`
30–120 against a ceiling of 41 (30m) to 264 (5m) primary bars per cycle.

## 2. Long share — MNQ's rows are materially long-biased and MNQ's tape rose 12.2%

| arm-cell | span drift | long share, qualifying universe | per-row median | p10 | p90 |
|---|---|---|---|---|---|
| MES 5m RTH | +5.77% | 0.515 | 0.500 | — | — |
| MES 5m SESSION | +5.77% | 0.532 | 0.526 | | |
| MES 15m RTH | +5.77% | 0.532 | 0.533 | | |
| MES 15m SESSION | +5.77% | 0.523 | 0.512 | | |
| MES 30m RTH | +5.77% | 0.547 | 0.524 | | |
| MES 30m SESSION | +5.77% | **0.482** | 0.464 | | |
| MNQ 5m RTH | +12.27% | **0.586** | 0.556 | | |
| MNQ 5m SESSION | +12.27% | **0.561** | 0.560 | | |
| MNQ 15m RTH | +12.19% | **0.598** | 0.581 | | |
| MNQ 15m SESSION | +12.19% | **0.591** | 0.590 | | |
| **MNQ 30m RTH** | +12.19% | **0.647** | 0.628 | | |
| MNQ 30m SESSION | +12.19% | **0.606** | 0.614 | | |

**MES sits at 0.482–0.547 — inside EF4's 0.467–0.539 range and inside its random baseline of
0.498–0.535, so MES's direction is not distinguishable from drift-neutral. MNQ sits at 0.561–0.647,
clearly outside both.** MNQ's tape rose 12.2% over the same 41 cycles and MES's 5.8%, and the long-share
ordering follows the drift ordering exactly.

**So every MNQ row's absolute expectancy in my cell is drift-inflated and must be read that way.** What
that does *not* invalidate is the **paired** comparison against `placebo_shuffle`, which holds the
long/short count exactly fixed and permutes only which bar gets which direction (burst 08) — drift
cannot survive that control. The two statements coexist: MNQ's absolute numbers are inflated by a rising
tape, and its *paired* difference against a direction-count-matched control is not. Both go on the row.

## 3. Cross-check against EF6's independent prefilter, and one discrepancy to flag

EF6 burst 07 prefiltered MNQ 15m and removed **37 of 412 (9.0%)**, causes
`oi_price_confirmation@15m 22, oi_expanding@15m 19`, groups `BREAKOUT 19, MOMENTUM 18`. I removed
**133 of 1,821 (7.3%)** with causes `oi_expanding 56, oi_price_confirmation 49,
session_extreme_sweep 44`, groups BREAKOUT 47 / MOMENTUM 54 / LIQUIDITY 16 / OPENING_RANGE 12 /
REVERSAL 4. **The `openinterest` half agrees on rate, cause and group.**

**The discrepancy: EF6's cause list contains no `session_extreme_sweep`.** My census makes it VOID under
the in-window gate on MNQ 15m (0 of 3,579 bars; all 11 fires are 16:00–16:45 ET). EF6's prefilter uses an
in-window gate too, so it should have seen the same zero. Two innocent explanations — EF6's population is
4.4× smaller (412 vs 1,821) so it may hold few carriers, or its prefilter checks a narrower condition
list — and one that would matter, which is that one of us has the gate wrong. **Worth one cross-check
between EF5 and EF6 before either number is published.** I am not treating it as a defect in EF6's work;
the `openinterest` agreement is close enough that the method is clearly sound.
