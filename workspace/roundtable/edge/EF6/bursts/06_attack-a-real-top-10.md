# EF6 burst 06 — the four gates, exercised on a real top 10. All ten rows: NOT A RESULT.

**Built:** `EF6/code/attack.py` (the gates) and `EF6/code/run_attack_demo.py` (the end-to-end run).
**Run on:** MGC 60m, `data/archive`, 718.9 days, 18:00→16:00 enforced, `max_total=2500`.

Pipeline, exactly what EF2–EF5's rows will go through:
generate 465 at primary 60m → `arms.refilter(rth_only=False)` (D48-safe) → **prefilter against the
census** (0 VOID on MGC 60m) → `SessionWindowEngine` → rank in-sample on durability → top 10 →
window-safe placebo cohort **for exactly those ten**, run in its own pass with arm-id uniqueness
asserted before and after → `attack.attack` per row.

`arms.assert_unique(bases, placebos)` and `arms.arm_report(results, bases, placebos)` both passed.
`id_collisions: 0`. `count_matched: 10/10`.

## The table

| # | strategy_id | group | n | exp R | win | avg win | avg loss | t | G1 | G2 | G3 | G4 | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `MGC-60m-3d2aca39b143` | MULTI_TIMEFRAME | 111 | +0.1453 | 59.5% | +0.682 | −0.642 | **+1.965** | PASS | BEATS (low power) | **FAIL** | **FAIL** | NOT A RESULT |
| 2 | `MGC-60m-6af25c1a8689` | MULTI_TIMEFRAME | 110 | +0.1428 | 59.1% | +0.686 | −0.642 | +1.915 | PASS | BEATS (low power) | **FAIL** | **FAIL** | NOT A RESULT |
| 3 | `MGC-60m-c2ff48ff738b` | MULTI_TIMEFRAME | 110 | +0.1428 | 59.1% | +0.686 | −0.642 | +1.915 | PASS | **UNDERPOWERED** | **FAIL** | **FAIL** | NOT A RESULT |
| 4 | `MGC-60m-6e1e3959979e` | MULTI_TIMEFRAME | 158 | +0.1121 | 54.4% | +0.754 | −0.654 | +1.714 | PASS | **UNDERPOWERED** | **FAIL** | **FAIL** | NOT A RESULT |
| 5 | `MGC-60m-06e80b21dfc4` | MULTI_TIMEFRAME | 157 | +0.1101 | 54.1% | +0.758 | −0.654 | +1.674 | PASS | **UNDERPOWERED** | **FAIL** | **FAIL** | NOT A RESULT |
| 6 | `MGC-60m-75030f1efeea` | MULTI_TIMEFRAME | 157 | +0.1101 | 54.1% | +0.758 | −0.654 | +1.674 | PASS | BEATS (low power) | **FAIL** | **FAIL** | NOT A RESULT |
| 7 | `MGC-60m-cb08d68c17c6` | VOLUME_PROFILE | 90 | +0.0883 | 55.6% | +0.468 | −0.386 | +1.503 | PASS | **UNDERPOWERED** | **FAIL** | **FAIL** | NOT A RESULT |
| 8 | `MGC-60m-b15e6b112bf9` | MULTI_TIMEFRAME | 84 | +0.0940 | 57.1% | +0.627 | −0.616 | +1.159 | PASS | BEATS (low power) | **FAIL** | **FAIL** | NOT A RESULT |
| 9 | `MGC-60m-be289c30cdcb` | TREND | 134 | +0.0820 | 50.0% | +1.148 | −0.984 | +0.760 | PASS | **UNDERPOWERED** | **FAIL** | **FAIL** | NOT A RESULT |
| 10 | `MGC-60m-a4c4bee42afe` | VOLUME_PROFILE | 180 | +0.0565 | 55.0% | +0.483 | −0.465 | +1.210 | PASS | **UNDERPOWERED** | **FAIL** | **FAIL** | NOT A RESULT |

**Which gate killed what.** G1 killed nothing — MGC 60m carries no VOID condition, minimum fires
4,547. **G2 killed 6 of 10.** **G3 killed 10 of 10**: the largest t in the list is **+1.965**
against `free_t(465) = 3.505`; the implied annualised Sharpe of the best row is **1.401** where the
threshold demands **2.498**. **G4 killed 10 of 10**: the forward roll on this same population gives
top-10 +0.0275R against a universe of +0.0302R — selection destroyed value — at z = +0.25.

Note the shape of the win/payoff pairs, since `BRIEF.md` rule 7 forbids quoting one without the
other: row 9 has a **50.0%** win rate with a **+1.148 / −0.984** payoff and row 1 has **59.5%** with
**+0.682 / −0.642**. Both land in the same expectancy band. The two cancel, exactly as measured
four separate times before.

## Two faults this exercise found in my own machinery, both now fixed

**(a) `placebo.py`'s raw-signal matching overshoots 2–3×, and it is not a window problem.**
`placebo.py` matches the placebo on *raw* signals, arguing that "after the engine's own culling the
realised counts land in the same place". On this top 10 they did not:

```
base realised 110, 111, 110, 158, 157, 157, 90, 84, 134, 180
placebo realised (raw-signal match)  356, 364, 366, 315, 307, ...   -> 2.0x to 3.3x overshoot
placebo realised (realised match)    111, 110, 108, 152, 153, 156, 89, 84, 126, 177  -> ratio 0.94-1.00
```

**Mechanism: clustering.** A real signal fires in bursts and the engine refuses a new signal while
positioned, so most of a burst is culled. The placebo's entries are scattered, overlap nothing, and
almost all survive. A control with 3× the sample has a √3-smaller standard error — it wins any
comparison scored on *t* and loses any comparison scored on trade count, for reasons that have
nothing to do with the signal. `PlaceboMeta.schedule_vs_realised` was built to expose exactly this
and nothing was reading it.

**Fix, one pass rather than a calibration loop:** draw exactly the base's **realised** count and
enforce a minimum separation equal to the base's **median realised hold in base bars**, so the
engine's culling has nothing left to remove. `placebo_w.build_cohort(..., match_on="realised",
hold_bars=...)`, now the default; `match_on="raw"` reproduces the old behaviour for comparison.

**(b) A single placebo draw gives a coin-flip verdict, and rows 2 and 3 prove it.**
Rows 2 and 3 are **statistical clones** — identical n (110), expectancy (+0.1428), win rate
(59.1%), payoff and t (+1.915). They received **opposite** G2 verdicts: `BEATS (LOW POWER)` at
p = 0.028 and `UNDERPOWERED` at p = 0.1224. The only thing that differed was which random placebo
they drew.

**So G2 on one draw is not reliable, and I am flagging that against my own gate.** The fix is m
draws per base with the p-values pooled; it is not implemented, and until it is, **a single-draw G2
`BEATS` must be read as provisional.** The direction of the error is not conservative — it can pass
a row as well as fail one. `attack.gate_placebo` accepts any base/placebo trade pair, so pooling is
a caller-side change rather than a rewrite.

The `BEATS (LOW POWER)` label is itself a correction I made mid-burst: the first version returned
`UNDERPOWERED` whenever the observed difference fell below the 80%-power detectable difference,
which **buried four significant separations** (p = 0.0146–0.028). Suppressing a significant result
under a power label is as dishonest as ignoring the power, so the flag now rides alongside the
verdict instead of overriding it.

## A third observation, about how a naive top 10 is built

**6 of the 10 rows are MULTI_TIMEFRAME, and at least two pairs are clones** (#2/#3 and #5/#6 have
byte-identical statistics). This top 10 was ranked without clone collapse, deliberately, to show
what EF2–EF5 will get if they do the same: **a top 10 that is effectively a top ~7, with one group
holding 60% of it.** `forward.Ledger.measure` collapses clones on the identical realised
(timestamp, direction) fingerprint; an in-sample ranking must do the same or the list is padded.

## Anti-overfitting checks in this burst

| hazard | checked | finding |
|---|---|---|
| **`T.ab` (D28, inflates z ~3.3×)** | yes | not used. G2 is a two-sided label permutation with blocks = 18:00→16:00 cycles, 5,000 permutations, Welch reported only as a cross-check `[measured: grep "T.ab\|toolkit.ab" over EF6/code → no matches]` |
| correlated observations treated as independent | yes | permutation blocks on cycles, not on trades |
| **control sample mismatch** | **yes, and found** | 2.0–3.3× overshoot; fixed; ratio now 0.94–1.00 and reported per row in `count_match.ratio` |
| **single-draw control** | **yes, and found in my own gate** | clone pair received opposite verdicts. Stated as a live limitation |
| a power caveat suppressing a real result | **yes, and found in my own gate** | `UNDERPOWERED` was overriding four p ≤ 0.05 separations; now `BEATS (LOW POWER)` |
| D48 arm collision | yes | `assert_unique` before the run, `arm_report` after, `id_collisions: 0` |
| clone padding of a top 10 | **yes, and found** | 2 exact clone pairs in 10 rows; 6 of 10 one group |
| win rate quoted without payoff | yes | both quoted for every row, with expectancy in R |
| structural zero rows in the denominator | yes | prefilter ran first; 0 VOID on MGC 60m, and it is a hard dependency — `make_ledger` raises if the census is absent |
| in-sample rank reported as a result | yes | the ranking is in-sample **by design** here, which is the point: G3 and G4 then kill all ten |
