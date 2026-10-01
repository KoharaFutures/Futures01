# Results: LVN fade (#17) and sweep & reclaim (#18) — walk-forward, 2026-09-30

_Pre-registration: `PREREG_2026-09-30_lvn.md` (written 21:40 ET before any run; one crash-fix addendum at
21:55 ET, before any result). Rules: `DATA_HUB/tools/rules/lvn17_deep_first_lvn_fade.py` (sha b1a5a1f521de),
`DATA_HUB/tools/rules/lvn18_sweep_reclaim_1w60.py` (sha 0cd0322bf6f1). Driver:
`workspace/paper/CALL/research/run_lvn_2026-09-30.py`. Every number below is pasted from its output
(`DATA_HUB/walkforward/LVN1718/tables.md`, `results.json`, `trades_*.jsonl`). Data: 15m/5m bars
2026-07-29 → 2026-09-30 (about 2 months); 60m bars 2024-10-06 → 2026-09-30. Paper only._

## What was tested, in plain English

- **A (#17) — fade the first thin spot outside "fair value".** Build a volume profile (how much traded
  at each price) over the last 24/48/72 hours. The **value area** is the 70% busiest band (top = VAH,
  bottom = VAL). An **LVN** is a thin, little-traded price between two busy ones; **depth** = how thin
  (0.35 = a third of the volume of the busy shelf next to it). When price leaves value and reaches the
  first deep LVN above (below), sell (buy) it. **A1** = resting limit order at the LVN. **A2** = wait for a
  15-minute bar to touch the LVN and close back inside value, then enter at the next bar.
  Stop just beyond the LVN (0.25 ATR + 1 tick; ATR = typical bar size), target 1.8× the risk, out after
  16 bars (4 h) or 16:00 ET.
- **B (#18) — sweep & reclaim.** A bar pokes through a 1-week LVN or value edge (60m-built profile) and
  closes back on the side it came from; enter next bar in the reclaim direction, stop 1 tick past the
  poke, target 1.8R. **B15** on 15m bars (primary), **B60** on 60m bars for 2 years of history.
- **Stacked** = 3+ hub levels (prior-day/week highs-lows, VWAP, POC, round numbers, 1-week profile levels)
  within 0.5 ATR of the entry.

**How to read a row.** *R* = one unit of risk. *Avg R* = average result per trade after costs
(+0.10 = you keep 10% of what you risk per trade). *Win %* and *payoff* (average win ÷ average loss)
always go together: with a 1.8R target, costs pull the realised payoff to about 1.5, so you need roughly 40% wins to break even. *t* = how
far avg R is from zero in standard errors. *P1 placebo* = the same trades with a coin-flip direction.
*Level placebo* = the whole rule rerun with the LVNs/levels swapped for random prices (10 runs).
**Luck bar** = √(2·ln N) for the N things tried: the ledger counts **210** trials for this family
(120 planned + 90 for the re-registered fixed rule), so the bar is **3.27**. A result needs t ≥ 3.27,
z vs P1 ≥ 3.27, ≥ 30 trades and to beat the level placebo in ≥ 9/10 runs.

## Hypothesis A — deep first-LVN fade (all trades)

| variant | symbol | subset | N | win % | payoff | avg R | t | P1 placebo avg R | z vs P1 | level-placebo avg R (avg N) | real beats level placebo | 1st / 2nd half avg R | passes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1-24h | MGC | all | 1 | 100.0 | — | 1.7187 | — | 0.3495 | — | -0.1293 (2.4) | 8/9 | 0.0 / 1.7187 | no |
| A1-24h | MNQ | all | 8 | 25.0 | 1.565 | -0.3961 | -0.855 | -0.071 | -0.701 | -0.254 (8.4) | 3/10 | -1.1057 / 0.3136 | no |
| A1-24h | MES | all | 1 | 0.0 | — | -1.1537 | — | -1.1537 | — | -0.7359 (1.7) | 6/9 | 0.0 / -1.1537 | no |
| A1-24h | MCL | all | 0 | — | — | — | — | — | — | -0.1106 (0.8) | 0/7 | — / — | no |
| A1-24h | POOLED | all | 10 | 30.0 | 1.552 | -0.2603 | -0.601 | -0.1631 | -0.224 | -0.2827 (13.3) | 6/10 | -1.1153 / 0.5946 | no |
| A1-48h | MGC | all | 0 | — | — | — | — | — | — | -0.6069 (0.7) | 0/7 | — / — | no |
| A1-48h | MNQ | all | 4 | 0.0 | — | -1.0931 | -50.206 | -0.227 | -26.712 | -0.2751 (6.2) | 0/10 | -1.1271 / -1.0591 | no |
| A1-48h | MES | all | 1 | 0.0 | — | -1.1655 | — | 0.1886 | — | 0.4374 (2.0) | 3/9 | 0.0 / -1.1655 | no |
| A1-48h | MCL | all | 0 | — | — | — | — | — | — | 0.0535 (0.7) | 0/6 | — / — | no |
| A1-48h | POOLED | all | 5 | 0.0 | — | -1.1076 | -49.82 | -0.1434 | -31.34 | -0.061 (9.6) | 0/10 | -1.1574 / -1.0744 | no |
| A1-72h | MGC | all | 0 | — | — | — | — | — | — | -1.0832 (1.0) | 0/7 | — / — | no |
| A1-72h | MNQ | all | 9 | 33.3 | 2.999 | 0.3619 | 0.48 | 0.2091 | 0.203 | -0.1475 (5.1) | 8/10 | -1.0946 / 1.527 | no |
| A1-72h | MES | all | 0 | — | — | — | — | — | — | -0.2625 (0.3) | 0/3 | — / — | no |
| A1-72h | MCL | all | 1 | 0.0 | — | -1.1525 | — | 0.2534 | — | 0.0477 (0.9) | 0/6 | 0.0 / -1.1525 | no |
| A1-72h | POOLED | all | 10 | 30.0 | 2.973 | 0.2104 | 0.304 | 0.2082 | 0.003 | -0.3258 (7.3) | 7/10 | -1.0912 / 1.512 | no |
| A2-24h | MGC | all | 1 | 0.0 | — | -1.0344 | — | -1.0344 | — | -1.0306 (0.8) | 1/7 | 0.0 / -1.0344 | no |
| A2-24h | MNQ | all | 2 | 100.0 | — | 1.7749 | 601.644 | 0.3868 | 44.112 | 1.2942 (1.5) | 6/10 | 1.7719 / 1.7778 | no |
| A2-24h | MES | all | 1 | 100.0 | — | 1.632 | — | 0.2085 | — | 0.5845 (0.8) | 3/8 | 0.0 / 1.632 | no |
| A2-24h | MCL | all | 3 | 33.3 | 1.572 | -0.1566 | -0.166 | 0.3134 | -0.499 | -0.1299 (1.0) | 4/8 | 1.7277 / -1.0987 | no |
| A2-24h | POOLED | all | 7 | 57.1 | 1.603 | 0.5254 | 0.927 | 0.11 | 0.732 | 0.3441 (4.1) | 7/10 | 0.8217 / 0.3031 | no |
| A2-48h | MGC | all | 0 | — | — | — | — | — | — | — (0.0) | 0/0 | — / — | no |
| A2-48h | MNQ | all | 2 | 50.0 | 1.731 | 0.3754 | 0.268 | -0.3025 | 0.483 | 0.7676 (0.8) | 3/7 | -1.0271 / 1.7778 | no |
| A2-48h | MES | all | 1 | 100.0 | — | 1.632 | — | 0.2085 | — | 0.4353 (1.6) | 6/10 | 0.0 / 1.632 | no |
| A2-48h | MCL | all | 2 | 0.0 | — | -1.0987 | -62.966 | 0.3162 | -39.403 | -0.5077 (0.7) | 0/6 | -1.1162 / -1.0813 | no |
| A2-48h | POOLED | all | 5 | 40.0 | 1.586 | 0.037 | 0.054 | 0.0628 | -0.038 | 0.3694 (3.1) | 4/10 | 0.2579 / -0.1102 | no |
| A2-72h | MGC | all | 0 | — | — | — | — | — | — | -1.0317 (0.1) | 0/1 | — / — | no |
| A2-72h | MNQ | all | 3 | 66.7 | 0.881 | 0.26 | 0.318 | 0.0849 | 0.214 | -0.3314 (0.5) | 3/4 | -1.0244 / 0.9022 | no |
| A2-72h | MES | all | 0 | — | — | — | — | — | — | — (0.0) | 0/0 | — / — | no |
| A2-72h | MCL | all | 2 | 50.0 | 1.505 | 0.2819 | 0.202 | 0.291 | -0.007 | 1.1321 (0.5) | 1/5 | 1.68 / -1.1162 | no |
| A2-72h | POOLED | all | 5 | 60.0 | 1.085 | 0.2687 | 0.427 | 0.1692 | 0.158 | 0.3279 (1.1) | 4/9 | 0.3278 / 0.2294 | no |

A almost never trades: across 4 symbols and ~2 months, the most any A cell produced was 10 trades. Most A1
signals were skipped because the bar had already opened beyond the stop (the profile shifted and the LVN
moved under price) or the 1-contract stop was below the contract's minimum. t-values like −50 or 601 are
what 2–4 near-identical trades produce; they mean nothing.

## Hypothesis B — sweep & reclaim (all trades)

| variant | symbol | subset | N | win % | payoff | avg R | t | P1 placebo avg R | z vs P1 | level-placebo avg R (avg N) | real beats level placebo | 1st / 2nd half avg R | passes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B15 | MGC | all | 59 | 25.4 | 1.675 | -0.3355 | -2.091 | -0.2448 | -0.565 | -0.1793 (69.7) | 2/10 | -0.4644 / -0.2109 | no |
| B15 | MNQ | all | 91 | 35.2 | 1.539 | -0.112 | -0.823 | -0.2816 | 1.245 | -0.2528 (80.2) | 8/10 | -0.2086 / -0.0174 | no |
| B15 | MES | all | 63 | 36.5 | 1.401 | -0.1367 | -0.826 | -0.1876 | 0.308 | -0.182 (81.9) | 8/10 | -0.0719 / -0.1994 | no |
| B15 | MCL | all | 56 | 33.9 | 1.455 | -0.1844 | -1.054 | -0.1478 | -0.209 | -0.0505 (85.2) | 2/10 | 0.1715 / -0.5403 | no |
| B15 | POOLED | all | 269 | 33.1 | 1.51 | -0.1819 | -2.32 | -0.223 | 0.524 | -0.1615 (317.0) | 3/10 | -0.1027 / -0.2604 | no |
| B60 | MGC | all | 134 | 30.6 | 1.587 | -0.2168 | -1.991 | -0.1832 | -0.308 | 0.0134 (245.6) | 0/10 | -0.1808 / -0.2528 | no |
| B60 | MNQ | all | 125 | 30.4 | 1.645 | -0.2076 | -1.788 | -0.1574 | -0.432 | -0.214 (132.7) | 5/10 | -0.0069 / -0.4051 | no |
| B60 | MES | all | 106 | 32.1 | 1.424 | -0.2463 | -1.99 | -0.1676 | -0.636 | -0.2811 (122.6) | 7/10 | -0.0641 / -0.4284 | no |
| B60 | MCL | all | 245 | 37.6 | 1.453 | -0.08 | -0.988 | -0.1296 | 0.612 | -0.148 (200.1) | 8/10 | -0.0415 / -0.1181 | no |
| B60 | POOLED | all | 610 | 33.6 | 1.506 | -0.1651 | -3.205 | -0.1559 | -0.179 | -0.1148 (701.0) | 2/10 | -0.1158 / -0.2143 | no |

**B60 blew the account on every symbol.** Under the desk's sizing ladder each run reached the $2,800
drawdown floor and stopped (MES 2025-06-23, MNQ 2025-07-15, MCL 2026-02-10, MGC 2026-07-20), so B60
results cover only the trades taken before that.

## Stacked vs not stacked (pooled across symbols, and B per symbol)

| variant | symbol | subset | N | win % | payoff | avg R | t | P1 placebo avg R | z vs P1 | level-placebo avg R (avg N) | real beats level placebo | 1st / 2nd half avg R | passes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A1-24h | POOLED | stacked | 2 | 50.0 | 1.561 | 0.3097 | 0.219 | 0.3259 | -0.011 | -0.2018 (1.5) | 6/9 | -1.1049 / 1.7244 | no |
| A1-24h | POOLED | not stacked | 8 | 25.0 | 1.551 | -0.4029 | -0.868 | -0.2644 | -0.298 | -0.3343 (11.8) | 6/10 | -1.1147 / 0.309 | no |
| A1-48h | POOLED | stacked | 1 | 0.0 | — | -1.1049 | — | 0.3314 | — | 0.0445 (1.7) | 0/8 | 0.0 / -1.1049 | no |
| A1-48h | POOLED | not stacked | 4 | 0.0 | — | -1.1082 | -38.631 | -0.2822 | -22.203 | -0.0568 (7.9) | 0/10 | -1.1574 / -1.0591 | no |
| A1-72h | POOLED | stacked | 2 | 0.0 | — | -1.0691 | -194.382 | -0.2822 | -25.227 | -0.5924 (1.1) | 3/9 | -1.0746 / -1.0636 | no |
| A1-72h | POOLED | not stacked | 8 | 37.5 | 2.944 | 0.5303 | 0.636 | 0.2941 | 0.283 | -0.3062 (6.2) | 8/10 | -1.0953 / 2.1559 | no |
| A2-24h | POOLED | stacked | 1 | 0.0 | — | -1.0344 | — | -1.0344 | — | -0.8001 (0.7) | 0/6 | 0.0 / -1.0344 | no |
| A2-24h | POOLED | not stacked | 6 | 66.7 | 1.572 | 0.7853 | 1.317 | 0.3349 | 0.755 | 0.6294 (3.4) | 7/10 | 1.7105 / -0.1399 | no |
| A2-48h | POOLED | stacked | 1 | 0.0 | — | -1.0271 | — | -1.0271 | — | -0.4737 (0.3) | 1/3 | 0.0 / -1.0271 | no |
| A2-48h | POOLED | not stacked | 4 | 50.0 | 1.552 | 0.3031 | 0.374 | 0.2962 | 0.009 | 0.4662 (2.8) | 3/9 | 0.2579 / 0.3483 | no |
| A2-72h | POOLED | stacked | 0 | — | — | — | — | — | — | — (0.0) | 0/0 | — / — | no |
| A2-72h | POOLED | not stacked | 5 | 60.0 | 1.085 | 0.2687 | 0.427 | 0.1692 | 0.158 | 0.3279 (1.1) | 4/9 | 0.3278 / 0.2294 | no |
| B15 | MGC | stacked | 4 | 0.0 | — | -1.0517 | -86.929 | -0.3392 | -31.308 | -0.2963 (11.8) | 0/10 | -1.051 / -1.0524 | no |
| B15 | MGC | not stacked | 55 | 27.3 | 1.676 | -0.2834 | -1.667 | -0.2344 | -0.288 | -0.1476 (57.9) | 1/10 | -0.421 / -0.1508 | no |
| B15 | MNQ | stacked | 23 | 34.8 | 1.463 | -0.1502 | -0.553 | -0.3061 | 0.574 | -0.1749 (16.8) | 7/10 | 0.0784 / -0.3597 | no |
| B15 | MNQ | not stacked | 68 | 35.3 | 1.565 | -0.099 | -0.625 | -0.2764 | 1.119 | -0.2807 (63.4) | 8/10 | -0.0569 / -0.1412 | no |
| B15 | MES | stacked | 5 | 20.0 | 1.574 | -0.54 | -0.942 | 0.0 | -0.941 | -0.502 (12.4) | 5/10 | -1.15 / -0.1334 | no |
| B15 | MES | not stacked | 58 | 37.9 | 1.393 | -0.1019 | -0.588 | -0.2165 | 0.661 | -0.1253 (69.5) | 4/10 | 0.0007 / -0.2045 | no |
| B15 | MCL | stacked | 8 | 25.0 | 1.129 | -0.5042 | -1.299 | 0.0211 | -1.353 | -0.1004 (11.3) | 1/10 | -0.6321 / -0.3763 | no |
| B15 | MCL | not stacked | 48 | 35.4 | 1.489 | -0.1311 | -0.676 | -0.1705 | 0.203 | -0.0293 (73.9) | 2/10 | 0.3006 / -0.5627 | no |
| B15 | POOLED | stacked | 40 | 27.5 | 1.407 | -0.3599 | -1.906 | -0.1993 | -0.85 | -0.2913 (52.3) | 3/10 | -0.4981 / -0.2216 | no |
| B15 | POOLED | not stacked | 229 | 34.1 | 1.523 | -0.1508 | -1.754 | -0.2282 | 0.9 | -0.139 (264.7) | 4/10 | -0.0206 / -0.2798 | no |
| B60 | MGC | stacked | 71 | 36.6 | 1.635 | -0.036 | -0.228 | -0.2382 | 1.282 | 0.0378 (144.5) | 2/10 | -0.0186 / -0.0529 | no |
| B60 | MGC | not stacked | 63 | 23.8 | 1.518 | -0.4205 | -2.89 | -0.1302 | -1.994 | -0.0277 (101.1) | 0/10 | -0.3357 / -0.5027 | no |
| B60 | MNQ | stacked | 49 | 28.6 | 1.636 | -0.2623 | -1.435 | -0.1512 | -0.607 | -0.0823 (66.9) | 1/10 | 0.1131 / -0.6226 | no |
| B60 | MNQ | not stacked | 76 | 31.6 | 1.651 | -0.1723 | -1.14 | -0.1606 | -0.077 | -0.3578 (65.8) | 8/10 | -0.013 / -0.3316 | no |
| B60 | MES | stacked | 37 | 32.4 | 1.376 | -0.2552 | -1.225 | -0.2015 | -0.258 | -0.3202 (51.3) | 5/10 | -0.0931 / -0.4087 | no |
| B60 | MES | not stacked | 69 | 31.9 | 1.45 | -0.2415 | -1.558 | -0.1503 | -0.588 | -0.261 (71.3) | 5/10 | -0.0153 / -0.4612 | no |
| B60 | MCL | stacked | 90 | 34.4 | 1.309 | -0.2163 | -1.675 | -0.2015 | -0.115 | -0.1293 (90.1) | 2/10 | -0.1786 / -0.254 | no |
| B60 | MCL | not stacked | 155 | 39.4 | 1.539 | -0.0008 | -0.008 | -0.0945 | 0.905 | -0.1673 (110.0) | 10/10 | 0.057 / -0.0578 | no |
| B60 | POOLED | stacked | 247 | 33.6 | 1.472 | -0.1794 | -2.223 | -0.2028 | 0.29 | -0.0689 (352.8) | 1/10 | -0.083 / -0.275 | no |
| B60 | POOLED | not stacked | 363 | 33.6 | 1.531 | -0.1553 | -2.318 | -0.1251 | -0.451 | -0.1629 (348.2) | 5/10 | -0.1326 / -0.1779 | no |
| B15 | MGC | 130 | 30 | 31 | 48053.48 | 2026-07-29..2026-09-30 |
| B15 | MNQ | 189 | 24 | 41 | 48855.9 | 2026-07-29..2026-09-30 |
| B15 | MES | 119 | 5 | 38 | 48849.32 | 2026-07-29..2026-09-30 |
| B15 | MCL | 131 | 22 | 30 | 48629.24 | 2026-07-29..2026-09-30 |
| B60 | MGC | 1398 | 1025 | 145 | 48284.32 | 2024-10-06..2026-09-30 |
| B60 | MNQ | 1148 | 188 | 120 | 48637.94 | 2024-10-06..2026-09-30 |
| B60 | MES | 899 | 83 | 123 | 48608.92 | 2024-10-06..2026-09-30 |
| B60 | MCL | 969 | 174 | 114 | 48928.04 | 2024-10-06..2026-09-30 |

Full table (every symbol × subset) and signal / refused / skipped counts: `DATA_HUB/walkforward/LVN1718/tables.md`.

## Verdict

No variant clears the luck bar of 3.27 or passes its placebos. The best t in any cell with 30+ trades
is −0.008 (B60 MCL not stacked) and every 30+-trade cell has a **negative** average R: B15 pooled
269 trades, 33.1% wins with payoff 1.51 → −0.18R per trade (t −2.32), and B60 pooled 610 trades,
33.6% wins / payoff 1.51 → −0.17R (t −3.21), which is *significantly losing*, not winning; both sit
at or below their coin-flip and random-level placebos (z vs P1 +0.52 and −0.18; beat the level placebo
in 3/10 and 2/10 runs). Stacked levels did not rescue B (pooled B15 stacked −0.36R, B60 stacked −0.18R).
The deep-LVN fade (A) produced 0–10 trades per cell, so it can't be judged: its few positive cells
(A1-72h MNQ +0.36R on 9 trades, A2-24h pooled +0.53R on 7) are anecdotes, not evidence, and A1-48h
lost on all 5 trades. This matches the hub's finding that levels alone don't beat random prices.
Practical reading: don't trade LVN sweep-and-reclaims mechanically (both CALL-0018/0019 losses fit this
picture); A needs many more months of 5m data (or a 60m-built version, which would be a new
pre-registration) before it can be tested at all.
