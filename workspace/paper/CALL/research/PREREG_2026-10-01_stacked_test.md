# Pre-registration: stacked-level TEST trades (owner "option 2", 2026-10-01 19:20 ET)

Written before any such trade is taken.

**What gets traded.** A REVERSAL_CALLED / COUNTER_TREND_QUALIFIES / level setup that the desk would decline
ONLY because its level is stacked (2+ levels within 1/4 ATR, lesson #23). Taken as a 1-contract TEST via
`plan_builder.py --test`. Every hard gate still applies (G1 stand-down … G10 data age), as do the hard
don'ts (breakout chasing, fading the first 60m bar after 09:30, gold overnight-sweep fades) and the
sweep & reclaim exclusion.

**Hypothesis.** H0: expectancy of these TESTs is <= 0R (the desk's current belief, from the 2026-10-01
log: 4 stacked declines were broken through, 2 bounced). H1: expectancy > 0R.

**When to judge.** After 20 closed TESTs, not before. Report win rate and payoff together, plus
expectancy in R and its t-stat.

**Comparisons.**
- Baseline: B60 sweep & reclaim walk-forward, -0.17R (research/RESULTS_2026-09-30_lvn.md).
- Placebo: the same fade (same side, stop and target in ATR) at a random price 0.5-1.5 ATR from the real
  level, on the same bars, computed after the fact with the same resolver.
- Luck bar: sqrt(2 ln N), N = every variant tried on this setup (starts at N = 1; add one per tweak).

**Decision.** Keep it only if expectancy > 0R, it beats the placebo, and the t-stat clears the luck bar.
Otherwise drop it and keep declining stacked levels.

**Record.** TEST trades are reported separately from the measured record.
