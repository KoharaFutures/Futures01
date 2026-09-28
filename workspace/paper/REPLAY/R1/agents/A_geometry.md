# Agent A — geometry sweep of the stand-down null

**Closed-market window, REPLAY desk, R1 lane.** Script: `agents/A_grid.py` (new; `missed.py` untouched).
Inputs: `visible.jsonl` (1,635 bars) and `callouts.jsonl` only. Retrospective over bars the cursor has
already passed; no harness run, no cursor advanced.

## The question

`missed.py` reports that R1's stand-downs are indistinguishable from arbitrary bars — on a **1.0-ATR stop
with a 2R target**, all three honest direction arms sit at |z| < 1 against a control run at every eligible
bar. That is the desk's headline conclusion and it was measured at **one** geometry. This sweep asks
whether the null belongs to the stand-downs or to that cell: 4 stops × 3 targets = **12 cells**, three
honest arms each.

## Verdict, stated first

**The null holds everywhere on the grid. 0 of 36 cell × arm combinations reach |z| ≥ 2.0.** The largest
|z| anywhere on the honest grid is **1.33** (1.0 ATR stop, 3R target, always-LONG). The headline
conclusion is **not** an artefact of the 1.0-ATR / 2R cell — it survives a 3× range of stop width and a
2× range of target distance, and it survives an off-grid 0.25-ATR probe as well.

There is therefore **no significant cell, no significant region, and nothing for the multiple-testing
correction to correct.** The threshold is recorded below anyway, because it is what would have been
needed had anything fired.

```
cells x arms with |z| >= 2.0 : 0 of 36
largest |z| anywhere on the honest grid: 1.33 at stop 1.0 ATR, 3.0R, always LONG
top 5 by |z|:
|z| 1.33   stop 1.0 ATR  3.0R  always LONG
|z| 1.18   stop 0.75 ATR  3.0R  always LONG
|z| 1.13   stop 1.0 ATR  3.0R  coin flip (parity)
|z| 1.12   stop 1.5 ATR  2.0R  always LONG
|z| 0.99   stop 1.0 ATR  2.0R  always LONG
```

## Conventions — identical to `missed.py`, verified

Fill at the next bar's open plus one tick of slippage (tick 0.25); **stop wins a same-bar stop/target
tie**; flat at the session close (the first 16:00 ET bar at or after the fill); ATR14 from bars at or
before the **decision** bar, i.e. `atr(f-1)`; any stand-down whose forward window is not fully inside the
visible tape is PENDING and skipped. Control = the same simulation at every eligible bar, `range(20,
len(rows))`.

**Sample: 42 stand-downs, 41 scoreable, 1 pending. Control: 1,613 bars.** Identical at every cell — the
stop/target geometry does not change eligibility, only the outcome.

`A_grid.py` re-implements those mechanics rather than importing `missed.py`, because `missed.py` does all
its work at module scope: importing it runs the register, prints it and **rewrites `missed.jsonl`**.
Importing it twelve times would clobber that file. The re-implementation is validated against
`missed.py`'s own published figures at the baseline cell:

```
always LONG          mine +0.211/-0.009 z +0.99   published +0.211/-0.009 z +0.99   MATCH
always SHORT         mine +0.085/-0.003 z +0.41   published +0.085/-0.003 z +0.41   MATCH
coin flip (parity)   mine +0.177/-0.011 z +0.85   published +0.177/-0.011 z +0.85   MATCH
n_sd 41 (published 41)   n_ct 1613 (published 1613)
baseline reproduction: PASS
```

All three arms and both sample sizes reproduce to the printed precision, so the 11 other cells are
comparable to the published one.

## The 12 cells

`_sd` = R1's stand-downs, `_ct` = the all-bars control. `diff` = mean_sd − mean_ct. `z` = two-sample
(Welch-form) z on the difference of means, the same statistic `missed.py` prints.

| stop | targ | arm | n_sd | mean_sd | sd_sd | >=1.5R_sd | n_ct | mean_ct | sd_ct | >=1.5R_ct | diff | z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.50 | 1.5R | always LONG | 41 | -0.094 | 1.19 | 34.1% | 1613 | -0.113 | 1.18 | 33.8% | +0.019 | +0.10 |
| 0.50 | 1.5R | always SHORT | 41 | -0.287 | 1.11 | 26.8% | 1613 | -0.134 | 1.17 | 33.2% | -0.153 | -0.87 |
| 0.50 | 1.5R | coin flip (parity) | 41 | -0.210 | 1.14 | 29.3% | 1613 | -0.106 | 1.18 | 34.2% | -0.104 | -0.58 |
| 0.50 | 2.0R | always LONG | 41 | +0.077 | 1.42 | 34.1% | 1613 | -0.085 | 1.35 | 28.8% | +0.162 | +0.72 |
| 0.50 | 2.0R | always SHORT | 41 | -0.226 | 1.29 | 24.4% | 1613 | -0.098 | 1.35 | 28.4% | -0.128 | -0.63 |
| 0.50 | 2.0R | coin flip (parity) | 41 | -0.064 | 1.37 | 29.3% | 1613 | -0.080 | 1.35 | 29.0% | +0.017 | +0.08 |
| 0.50 | 3.0R | always LONG | 41 | +0.174 | 1.77 | 26.8% | 1613 | -0.002 | 1.68 | 23.6% | +0.176 | +0.63 |
| 0.50 | 3.0R | always SHORT | 41 | -0.035 | 1.66 | 22.0% | 1613 | -0.054 | 1.65 | 22.1% | +0.020 | +0.08 |
| 0.50 | 3.0R | coin flip (parity) | 41 | +0.034 | 1.73 | 24.4% | 1613 | -0.011 | 1.67 | 23.3% | +0.045 | +0.17 |
| 0.75 | 1.5R | always LONG | 41 | -0.034 | 1.20 | 36.6% | 1613 | -0.027 | 1.19 | 36.1% | -0.007 | -0.04 |
| 0.75 | 1.5R | always SHORT | 41 | -0.150 | 1.14 | 29.3% | 1613 | -0.077 | 1.17 | 33.9% | -0.073 | -0.41 |
| 0.75 | 1.5R | coin flip (parity) | 41 | -0.152 | 1.17 | 31.7% | 1613 | -0.045 | 1.18 | 35.3% | -0.107 | -0.58 |
| 0.75 | 2.0R | always LONG | 41 | +0.043 | 1.39 | 31.7% | 1613 | +0.009 | 1.37 | 30.4% | +0.034 | +0.15 |
| 0.75 | 2.0R | always SHORT | 41 | -0.077 | 1.33 | 26.8% | 1613 | -0.040 | 1.35 | 29.0% | -0.037 | -0.18 |
| 0.75 | 2.0R | coin flip (parity) | 41 | -0.067 | 1.37 | 29.3% | 1613 | +0.002 | 1.36 | 30.2% | -0.068 | -0.32 |
| 0.75 | 3.0R | always LONG | 41 | +0.343 | 1.83 | 31.7% | 1613 | +0.003 | 1.64 | 22.3% | +0.340 | +1.18 |
| 0.75 | 3.0R | always SHORT | 41 | -0.080 | 1.55 | 19.5% | 1613 | +0.015 | 1.65 | 23.1% | -0.095 | -0.38 |
| 0.75 | 3.0R | coin flip (parity) | 41 | +0.055 | 1.69 | 24.4% | 1613 | +0.008 | 1.64 | 22.6% | +0.047 | +0.17 |
| 1.00 | 1.5R | always LONG | 41 | +0.034 | 1.17 | 36.6% | 1613 | -0.009 | 1.17 | 34.9% | +0.043 | +0.23 |
| 1.00 | 1.5R | always SHORT | 41 | +0.118 | 1.18 | 39.0% | 1613 | -0.037 | 1.16 | 34.2% | +0.155 | +0.83 |
| 1.00 | 1.5R | coin flip (parity) | 41 | +0.062 | 1.19 | 39.0% | 1613 | -0.017 | 1.17 | 34.7% | +0.079 | +0.42 |
| 1.00 | 2.0R | always LONG | 41 | +0.211 | 1.40 | 36.6% | 1613 | -0.009 | 1.33 | 28.1% | +0.220 | +0.99 |
| 1.00 | 2.0R | always SHORT | 41 | +0.085 | 1.36 | 31.7% | 1613 | -0.003 | 1.33 | 28.8% | +0.089 | +0.41 |
| 1.00 | 2.0R | coin flip (parity) | 41 | +0.177 | 1.41 | 36.6% | 1613 | -0.011 | 1.33 | 28.0% | +0.189 | +0.85 |
| 1.00 | 3.0R | always LONG | 41 | +0.450 | 1.79 | 34.1% | 1613 | +0.075 | 1.63 | 23.6% | +0.374 | +1.33 |
| 1.00 | 3.0R | always SHORT | 41 | +0.162 | 1.62 | 26.8% | 1613 | +0.025 | 1.59 | 21.8% | +0.136 | +0.53 |
| 1.00 | 3.0R | coin flip (parity) | 41 | +0.355 | 1.75 | 31.7% | 1613 | +0.044 | 1.60 | 22.3% | +0.311 | +1.13 |
| 1.50 | 1.5R | always LONG | 41 | +0.165 | 1.17 | 39.0% | 1613 | -0.016 | 1.12 | 30.3% | +0.181 | +0.98 |
| 1.50 | 1.5R | always SHORT | 41 | +0.105 | 1.13 | 34.1% | 1613 | -0.020 | 1.11 | 30.9% | +0.125 | +0.70 |
| 1.50 | 1.5R | coin flip (parity) | 41 | +0.061 | 1.14 | 34.1% | 1613 | -0.018 | 1.11 | 30.1% | +0.079 | +0.44 |
| 1.50 | 2.0R | always LONG | 41 | +0.292 | 1.36 | 34.1% | 1613 | +0.051 | 1.27 | 25.0% | +0.240 | +1.12 |
| 1.50 | 2.0R | always SHORT | 41 | +0.164 | 1.29 | 26.8% | 1613 | +0.012 | 1.26 | 24.7% | +0.152 | +0.74 |
| 1.50 | 2.0R | coin flip (parity) | 41 | +0.164 | 1.32 | 29.3% | 1613 | +0.033 | 1.26 | 24.6% | +0.131 | +0.63 |
| 1.50 | 3.0R | always LONG | 41 | +0.229 | 1.55 | 22.0% | 1613 | +0.110 | 1.45 | 20.0% | +0.119 | +0.49 |
| 1.50 | 3.0R | always SHORT | 41 | +0.278 | 1.60 | 22.0% | 1613 | +0.081 | 1.49 | 19.8% | +0.197 | +0.78 |
| 1.50 | 3.0R | coin flip (parity) | 41 | +0.163 | 1.50 | 19.5% | 1613 | +0.094 | 1.46 | 19.6% | +0.069 | +0.29 |

## Is any positive region coherent, or isolated?

Moot — nothing is positive. But the **shape** of the z field is worth recording, because it is coherent
and it points at drift rather than judgement:

- z is **largest at the wide-stop / far-target corner** and on the **always-LONG** arm: +1.33 (1.0 ATR,
  3R), +1.18 (0.75 ATR, 3R), +1.13 (1.0 ATR, 3R coin-flip), +1.12 (1.5 ATR, 2R).
- z goes **negative at the tight-stop corner** on the short and coin-flip arms: −0.87 (0.5 ATR, 1.5R
  short), −0.58 (0.5 ATR, 1.5R flip).
- The gradient runs with **stop width and target distance**, not with anything about the stand-down bars.
  The tape trends up over this window, so a wider stop and a further target let a long ride further; the
  control's own long arm rises the same way (−0.113R at 0.5/1.5R → +0.110R at 1.5/3R). This is the
  always-LONG creep `missed.py`'s own notes already flagged, appearing across the grid.

**The multiple-testing threshold, for the record.** With n_trials = 12 cells × 3 honest arms = 36,
`free_t = sqrt(2*ln(36)) = 2.677`. Had a single cell come in at, say, |z| 2.1, it would have been an
isolated cell among 36 correlated looks and would **not** have cleared 2.68. Nothing came close, so the
distinction is not load-bearing here.

Two caveats on that threshold, both of which cut the same way:

1. **The 36 trials are heavily correlated** — every cell reuses the same 41 stand-downs and the same
   1,613 control bars, and adjacent geometries produce nearly the same trade outcomes. The effective
   number of independent looks is well below 36, so 2.68 is conservative and the honest threshold sits
   somewhere between 2.0 and 2.68. **1.33 fails both**, so the ambiguity does not matter.
2. The hindsight arm is **excluded** from n_trials, as it should be. See below.

## Question 3a — does the tight end behave differently from the wide end?

Yes, and it reproduces **rule 4** (structural stops below ~0.5 ATR are noise) mechanically, in the
control, without any edge needing to exist.

```
stop  0.5 ATR   mean |z| 0.43   max |z| 0.87   control coin-flip mean R -0.066
stop 0.75 ATR   mean |z| 0.38   max |z| 1.18   control coin-flip mean R -0.012
stop  1.0 ATR   mean |z| 0.75   max |z| 1.33   control coin-flip mean R +0.005
stop  1.5 ATR   mean |z| 0.69   max |z| 1.12   control coin-flip mean R +0.036
```

The mechanism is arithmetic, not market structure. Slippage is a **fixed** 0.25 points while 1R scales
with the stop, so the tax on every trade grows as the stop shrinks:

| stop | median stop (pts) | 1 tick as % of 1R | ctrl coin-flip mean R |
|---|---|---|---|
| 0.25 ATR | 2.66 | 9.4% | -0.267 |
| 0.50 ATR | 5.31 | 4.7% | -0.080 |
| 0.75 ATR | 7.97 | 3.1% | +0.002 |
| 1.00 ATR | 10.62 | 2.4% | -0.011 |
| 1.50 ATR | 15.94 | 1.6% | +0.033 |

Control expectancy climbs monotonically from **−0.267R at a 0.25-ATR stop to +0.033R at 1.5 ATR**, in
lockstep with the tick falling from 9.4% of 1R to 1.6%. Median ATR14 over the control bars is ~10.6
points, so a 0.25-ATR stop is a **2.66-point** stop on a 60-minute MES bar — inside the noise, exactly as
the repo's rule says.

**This is a partial reproduction and the limit should be stated.** The grid's tightest asked cell is
**0.5 ATR**, which is the rule's floor, not below it. The sub-floor evidence comes from the off-grid
0.25-ATR probe below. What the grid shows is the **gradient** — that expectancy degrades smoothly as the
stop tightens toward the floor — not a discontinuity at 0.5. I found no evidence of a knee or threshold
at 0.5 ATR; the decay is continuous. So the grid supports rule 4 as a *soft* cost gradient and does not
support it as a *sharp* floor.

The exit-reason mix explains the other half of the tight/wide difference:

| stop | targ | STOP | TARGET | SESSION_CLOSE |
|---|---|---|---|---|
| 0.50 | 1.5R | 63.2% | 33.5% | 3.3% |
| 0.50 | 2.0R | 67.4% | 28.5% | 4.1% |
| 0.50 | 3.0R | 72.2% | 22.1% | 5.7% |
| 0.75 | 1.5R | 58.8% | 35.0% | 6.2% |
| 0.75 | 2.0R | 62.8% | 29.4% | 7.8% |
| 0.75 | 3.0R | 68.4% | 21.2% | 10.3% |
| 1.00 | 1.5R | 55.5% | 34.5% | 10.0% |
| 1.00 | 2.0R | 59.8% | 28.1% | 12.1% |
| 1.00 | 3.0R | 63.6% | 19.9% | 16.5% |
| 1.50 | 1.5R | 49.9% | 30.6% | 19.5% |
| 1.50 | 2.0R | 51.7% | 24.2% | 24.1% |
| 1.50 | 3.0R | 52.9% | 14.3% | 32.8% |

At 0.5 ATR / 1.5R, 63% of control legs end on the stop and only 3% survive to the session close. At
1.5 ATR / 3R, the stop rate falls to 53% but **33% of legs never resolve at all** and are marked out at
the 16:00 close. So the wide-stop / far-target corner is measuring "where did the session end up" more
than "did the trade work", which is a further reason not to read the mildly larger z's there as an edge.

### Off-grid diagnostic: 0.25-ATR stop

Not one of the 12 cells and not counted in n_trials. Included only to probe below rule 4's floor. If it
were counted, n_trials = 15 × 3 = 45 and `free_t = sqrt(2*ln(45)) = 2.76`.

| stop | targ | arm | n_sd | mean_sd | sd_sd | >=1.5R_sd | n_ct | mean_ct | sd_ct | >=1.5R_ct | diff | z |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 1.5R | always LONG | 41 | -0.152 | 1.17 | 31.7% | 1613 | -0.368 | 1.08 | 24.7% | +0.217 | +1.17 |
| 0.25 | 1.5R | always SHORT | 41 | -0.544 | 0.96 | 17.1% | 1613 | -0.274 | 1.13 | 28.5% | -0.270 | -1.77 |
| 0.25 | 1.5R | coin flip (parity) | 41 | -0.322 | 1.09 | 24.4% | 1613 | -0.313 | 1.11 | 27.0% | -0.009 | -0.05 |
| 0.25 | 2.0R | always LONG | 41 | +0.007 | 1.40 | 31.7% | 1613 | -0.316 | 1.25 | 22.2% | +0.322 | +1.46 |
| 0.25 | 2.0R | always SHORT | 41 | -0.458 | 1.14 | 17.1% | 1613 | -0.242 | 1.30 | 24.7% | -0.217 | -1.19 |
| 0.25 | 2.0R | coin flip (parity) | 41 | -0.200 | 1.30 | 24.4% | 1613 | -0.267 | 1.28 | 23.9% | +0.067 | +0.33 |
| 0.25 | 3.0R | always LONG | 41 | -0.066 | 1.67 | 22.0% | 1613 | -0.240 | 1.55 | 18.4% | +0.174 | +0.66 |
| 0.25 | 3.0R | always SHORT | 41 | -0.385 | 1.43 | 14.6% | 1613 | -0.172 | 1.60 | 20.2% | -0.213 | -0.94 |
| 0.25 | 3.0R | coin flip (parity) | 41 | -0.347 | 1.44 | 14.6% | 1613 | -0.199 | 1.58 | 19.5% | -0.148 | -0.65 |

The null holds here too — the largest |z| is **1.77** (0.25 ATR, 1.5R, always-SHORT), which clears
neither 2.0 nor 2.76. Note the sign: below the floor the stand-downs look *worse* than the control on the
short arm, not better.

## Question 3b — does the grid reproduce "win rate and payoff cancel"?

**Yes, and this is the cleanest result in the sweep.** Control only, so it is a statement about the tape
rather than about R1's decisions:

| stop | targ | ctrl win% | ctrl >=1.5R | ctrl mean R |
|---|---|---|---|---|
| 0.50 | 1.5R | 36.3% | 34.2% | -0.106 |
| 0.50 | 2.0R | 31.6% | 29.0% | -0.080 |
| 0.50 | 3.0R | 26.7% | 23.3% | -0.011 |
| 0.75 | 1.5R | 39.2% | 35.3% | -0.045 |
| 0.75 | 2.0R | 35.3% | 30.2% | +0.002 |
| 0.75 | 3.0R | 28.6% | 22.6% | +0.008 |
| 1.00 | 1.5R | 40.7% | 34.7% | -0.017 |
| 1.00 | 2.0R | 35.5% | 28.0% | -0.011 |
| 1.00 | 3.0R | 31.3% | 22.3% | +0.044 |
| 1.50 | 1.5R | 41.3% | 30.1% | -0.018 |
| 1.50 | 2.0R | 39.2% | 24.6% | +0.033 |
| 1.50 | 3.0R | 37.6% | 19.6% | +0.094 |

Control win rate moves over a 14.6-point range (**26.7% → 41.3%**) as the geometry moves from tight-stop
/ far-target to wide-stop / near-target. Across that whole range, control mean R stays inside
**−0.106R to +0.094R** — a 0.20R band straddling zero. Win rate and payoff cancel to within a fifth of an
R everywhere on the grid.

Read the two monotonicities against each other: for a fixed stop, widening the target from 1.5R to 3R
**lowers** the win rate (40.7% → 31.3% at 1.0 ATR) and **raises** the payoff, and mean R barely moves
(−0.017R → +0.044R). For a fixed target, widening the stop **raises** the win rate (36.3% → 41.3% at
1.5R) and lowers the R-per-point, and again mean R barely moves. That is rule 3 arriving as a
two-dimensional surface rather than a citation.

The residual drift — mean R creeping from about −0.1R to about +0.1R across the grid — is the noise tax of
question 3a, not a failure of cancellation.

## The hindsight arm — an artefact, not a result

Reported under label only, and **excluded from every verdict above and from n_trials**. Picking the
direction after seeing the outcome makes a target reachable at most bars.

| stop | targ | sd mean | ct mean | diff | z |
|---|---|---|---|---|---|
| 0.50 | 1.5R | +0.583 | +0.739 | -0.156 | -0.83 |
| 0.50 | 2.0R | +0.814 | +0.803 | +0.011 | +0.05 |
| 0.50 | 3.0R | +1.103 | +0.929 | +0.174 | +0.57 |
| 0.75 | 1.5R | +0.775 | +0.870 | -0.095 | -0.56 |
| 0.75 | 2.0R | +0.925 | +0.943 | -0.018 | -0.08 |
| 0.75 | 3.0R | +1.222 | +0.992 | +0.231 | +0.79 |
| 1.00 | 1.5R | +1.077 | +0.907 | +0.170 | +1.31 |
| 1.00 | 2.0R | +1.221 | +0.940 | +0.281 | +1.49 |
| 1.00 | 3.0R | +1.536 | +1.053 | +0.482 | +1.85 |
| 1.50 | 1.5R | +1.155 | +0.872 | +0.283 | +2.73 |
| 1.50 | 2.0R | +1.341 | +0.971 | +0.369 | +2.45 |
| 1.50 | 3.0R | +1.392 | +1.099 | +0.293 | +1.24 |

**This is the one place on the grid where |z| ≥ 2 appears** — z **+2.73** at 1.5 ATR / 1.5R and **+2.45**
at 1.5 ATR / 2R, the first of which would even clear `free_t` 2.68. **It is not a finding and must not be
quoted as one.** What it says is that at R1's stand-down bars, *one or the other* direction paid more
often than at arbitrary bars — i.e. those bars were somewhat wider-ranging or more decisive — while
**neither** honest arm can capture it, because which direction paid was not knowable from the bar. A
volatility/range effect masquerading as skill is precisely what the honest arms exist to strip out, and
they strip it to |z| ≤ 1.33.

If anything, this sharpens the null rather than weakening it: the stand-down bars were *not* ordinary
bars, they were somewhat more eventful ones — and R1 still gained nothing measurable by declining them,
because the event had no predictable sign.

## Bugs and defects, recorded rather than silently fixed

**1. `missed.py` has a dead constant — `STOP_ATR` is never read.** Line 41 sets
`TICK, STOP_ATR, RR, PIVOT_K = 0.25, 1.0, 2.0, 3`, but `simulate()` uses the raw ATR as the stop
distance: `stop, targ = fill - sgn * S, fill + sgn * RR * S` where `S = atr(f-1)`. `RR` is read;
`STOP_ATR` is not. The published results are correct **only because 1.0 × ATR == ATR**. Anyone who edited
`STOP_ATR` to 0.5 expecting the stop to tighten would have got the 1.0-ATR answer back with no error and
no warning — which is exactly the sweep this window was convened to run. I have **not** patched
`missed.py` (instructed not to modify it). `A_grid.py` takes the stop as `S = stop_mult * atr(f-1)`
explicitly, which reduces to `missed.py` at `stop_mult = 1.0`, as the cross-check confirms.

**2. `missed.py` uses two different parities for its coin-flip arm** — bar index for the stand-down
sample (`c["visible_bars"] % 2`) and *enumeration* index for the control (`enumerate(ctrl)`). These are
not the same quantity. Here they coincide, because eligible control bars are contiguous from index 20 and
20 is even; `A_grid.py` computes both and the two control means agree to **0.0000** at every cell. It is
still a latent inconsistency: if eligibility ever becomes non-contiguous (a data gap, a changed session
filter) the control's flip arm would silently decorrelate from the sample's. Recorded, not fixed.

**3. A bug of my own, found and fixed during the run.** My first execution piped the script through
`tee ... | head -80`; `head` closed the pipe, `tee` took EPIPE and died, and the last five sections
(including the off-grid diagnostic and the cross-check) were truncated to their headers. I briefly read
the empty diagnostic table as "0.25 ATR produced no scoreable trades", which would have been a false
finding about the sub-floor region. The script was not at fault and was not changed; the invocation was.
Recording it because a truncated-output artefact is an easy way to manufacture an absence.

## What I could NOT determine

- **Whether the null generalises beyond this tape.** One instrument (MES 60-minute), one window (1,635
  visible bars, cursor 1635/11287), **n = 41** stand-downs. A 41-bar sample cannot resolve a difference
  smaller than roughly 0.4R at any of these geometries. The grid rules out a *large* stand-down effect at
  every geometry tested; it cannot rule out a small one, at any geometry.
- **Whether the desk's *intended* direction would have done better.** This is the arm I most wanted and
  could not build: all 42 `NO_TRADE` callouts carry `side: null`, `entry_price: null`, `initial_stop:
  null`. The direction under consideration exists only in the free-text `why` field. Parsing my own
  reading of that prose into a direction after knowing the outcome would be hindsight wearing a different
  hat, so I did not do it. **If the desk wants that arm, `NO_TRADE` callouts need to record the side that
  was being considered, at the time.** That is a cheap change to the callout schema and it would convert
  the strongest untestable question here into a testable one.
- **Anything about stop *management*.** Every cell is a fixed stop and a fixed target. Trailing stops,
  breakeven moves, partial exits, time stops and re-entries are all untested, and the null established
  here says nothing about them.
- **Whether a sharp floor exists at 0.5 ATR.** As noted in 3a, the decay is continuous from 0.25 to 1.5
  ATR with no knee. To locate a floor rather than a gradient would need finer stop resolution
  (0.3/0.4/0.5/0.6/0.7) and, more importantly, a far larger stand-down sample than 41.
- **Anything requiring the archive, the CSVs, the harness source or `state.json`.** I did not read them
  and did not want to; everything above comes from `visible.jsonl` and `callouts.jsonl`. No forward bar
  beyond the visible tape was touched, so nothing here can leak into a live decision.

## One-line summary for the consolidated notes

> **The headline null is not a single-geometry artefact.** Swept across 4 stops × 3 targets, all 36
> honest cell × arm combinations sit at |z| ≤ 1.33 — nowhere near 2.0, let alone `free_t` 2.68. The only
> |z| ≥ 2 on the whole grid is the hindsight arm at wide stops, which is a range effect with no
> predictable sign. The grid also reproduces rule 3 (win rate and payoff cancel to within 0.20R across a
> 14.6-point win-rate range) and the cost gradient behind rule 4 (control expectancy −0.267R at a
> 0.25-ATR stop → +0.033R at 1.5 ATR, tracking slippage from 9.4% to 1.6% of 1R), though as a smooth
> gradient rather than a floor at 0.5.
