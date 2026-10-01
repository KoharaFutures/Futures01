# LVN/FIB AGENT — paper desk charter

**Symbols: MGC and MNQ. Paper only. $50,000 account, $2,800 drawdown floor, $120 risk cap per
trade while nothing is proven.** Own lane: `workspace/paper/LVNFIB/**`, writer `LVNFIB`.

This desk exists because of one line in my own report: *"needs bars this study has not seen."*
Every rule below is already pre-registered and already measured on 2024-10-06 → 2026-09-30. The
only clean out-of-sample data left is the future, so the desk's job is to generate callouts
forward, in real time, that nobody has fitted — and to resolve them honestly.

## 1. The gate: a rule is ARMED or OBSERVE-ONLY, by its measured prior

The desk risks the account **only** on arms with a positive measured out-of-sample prior that the
budget can fund. Everything else is logged, resolved and counted, at zero risk. This is not
timidity — an OBSERVE-ONLY arm accumulates exactly the same forward data, and the project has
already shown that forward data is the scarce input, not more rules.

| arm | symbol | structure | measured OOS prior | funded? | status |
|---|---|---|---|---|---|
| **A** | MGC | Fib trend-failure, prior-week golden pocket, **resting limit at the level** | n=24, **+0.2379R, t +1.027**, win 50.0%, payoff 1.58 | yes — median stop **$106** of a $120 budget, 14 of 24 sizable | **ARMED** |
| A-mkt | MGC | the same rule entered at the next open | n=33, **+0.4324R, t +2.705**, win 66.7%, payoff 1.54 | no — median stop **$204**, only 6 of 33 sizable | OBSERVE ONLY (unfundable) |
| **B** | MNQ | Fib trend-failure, overnight-range 0.382/0.5, resting limit | n=108, **−0.0240R, t −0.213** | yes | **OBSERVE ONLY** (null) |
| **C** | MNQ | Fib trend-failure, prior-week golden pocket (arm A ported) | n=57, **−0.2390R, t −1.932** | — | **OBSERVE ONLY** (measured losing) |
| **D** | both | LVN first touch from below on the 1-week 60m profile, fade | OQ1: +0.06R t 0.64; LVN1718 60m: **−0.165R t −3.21** | — | **OBSERVE ONLY** (measured null to losing) |

**So in plain terms: the desk trades one rule, on gold. MNQ is instrumented, not traded.** I am not
going to risk the account on arm C, which I measured at −0.2390R, just because MNQ was asked for;
MNQ earns its way in by what arms B, C and D do on forward bars.

**Nothing here clears its luck bar.** Arm A is under it (t +1.027 against 2.327 for its own study,
and the market version's t +2.705 against 2.521 for ANCH1's). The desk is a forward test, not a
claim of edge.

## 2. Arm A, stated exactly (the only armed rule)

1. Take the **prior calendar week's** high and low on MGC 60m.
2. Direction: if that week closed above where it opened, call it an **up week**; else a down week.
3. Levels: for an up week, **0.618 / 0.705 / 0.786** of the range measured **down from the high**
   (for a down week, measured up from the low).
4. Window: MGC day-session 60m bars only — the **08:00 to 12:00 ET** bars. No new trigger armed on
   the 13:00 bar (the session's last hour).
5. Trigger: a bar **trades into** a level and **closes against the prior week's direction**.
6. Entry: a **resting limit at the level**, good for **2 bars**, cancelled at the session close.
   It pays no adverse tick; it pays non-fills instead (24 fills from 33 triggers in the backtest).
7. Stop: the level, displaced **0.5 × ATR14 + 1 tick** to the far side, floored at 25 ticks.
8. Target: **1.5 R**. Time exit 12 bars. Flat at the session close.
9. Size: one contract if `risk_$ ≤ min(6% of room-to-floor, 0.75% of equity, $500, $120)`,
   else **refuse the trade and log the refusal**. No fractional contracts, no exceptions.

### Why against the week and not with it
The continuation version of this exact setup — retrace into the golden pocket, close *with* the
week, trade *with* the week — measures **−0.4429R at t −4.750**. The textbook read of this
structure is the losing side of it on gold. Arm A is the inverse.

## 3. Rules this desk inherits and will not relitigate

- **Flat by 16:00 ET**, nothing held 16:00–18:00. No new entries in the session's final hour.
- **Volatility stand-down:** no new plan if ATR14 on 15m > 10 (MGC) or > 58 (MNQ).
- **Never move an entry toward the market to get filled.** That was the old desk's largest leak
  (55–60% fill rate against 4% for the disciplined replay desk). Arm A's limit sits *at* the level
  and is allowed to miss.
- **Don't take the first touch of a level** — first touches measured worse than fake levels at
  z −3.7. Arm A's trigger needs the bar to close against the week, which is not a bare first touch.
- **Stacked levels are the worst place to fade** (z −5.1). If an arm-A level sits within ¼ ATR of
  another tracked level, the callout is tagged `STACKED` and dropped to observe-only.
- **No exit overlay.** Stop-to-breakeven at +0.8R was measured over ~8,000 paired trades: it
  changes 4–7% of trades and does nothing (best t +1.74). A full exit at +0.8R is worse on 8 of 8
  arms (t −3.12 to −8.60). The target stays 1.5R.
- **Every price carries the timestamp of the bar it came from.** The Yahoo feed lags ~13 min at 5m
  and the newest 1–2 bars revise for ~28 min, so a level "broken" on an unsettled bar is not broken.

## 4. Known limits of this desk, stated up front

- **No live feed in this container.** `yfinance` is not installed, so `levels.py` reads
  `data/archive/` and stamps every level with its source bar. Until someone runs
  `pip install yfinance && python3 DATA_HUB/tools/refresh_archive.py --fetch`, the newest bar is
  **2026-09-30** and the desk must not describe any level as current.
- **Arm A produced 33 triggers in two years on MGC** — roughly 1.4 a month, of which the budget
  funds about 60%. This desk will be quiet. Quiet is the correct behaviour, not a malfunction.
- **One position at a time per symbol**, and open plus pending both count against the budget. The
  old desk once believed it had $120 of room when $22 was left.
- The desk never writes outside `workspace/paper/LVNFIB/`, and never edits a callout after it is
  posted. Resolution appends; it does not rewrite.
