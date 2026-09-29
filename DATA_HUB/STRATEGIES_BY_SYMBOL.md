# Top strategies by symbol

**Read this first:** no strategy below has a *proven* edge. Every one fell short of the luck bar
for the number of things tested. They're ranked by **how much evidence supports them**, so you
know where to look first and what to test next. Treat them as structure for your own read,
not as signals.

**Evidence rating**
- ●●● — held up on fresh (out-of-sample) data *and* beat a placebo, but still under the luck bar
- ●●○ — beat a placebo, or held up out-of-sample, but not both; or small samples
- ●○○ — a hint only: in-sample, tiny sample, or random did about as well
- ⛔ — **measured as harmful.** These are the strongest findings in the whole project.

"Bounce view" in each section comes from this hub's scanners (`levels/<SYM>_bounce.md`,
`levels/<SYM>_volume_profile.md`), run on data through 2026-09-29 00:58 ET.

---

## Rules that apply to every symbol (best-evidenced results in the project)

| rule | evidence | why it matters |
|---|---|---|
| ⛔ **Don't buy/sell a breakout in the direction of the move** ("CONT-1") | Worse than random entries in 4/4 tests on MGC & MNQ, z −2.6 to −4.7, expectancy −0.23 to −0.36R | Chasing the break is the single most reliably losing entry the desks found |
| ⛔ **Don't fade the first 60-minute bar after the 09:30 cash open** | z −10.6 pooled (NQ −7.8, MNQ −7.8, MES −5.6, MGC −5.4) | The opening drive tends to keep going |
| ⛔ **No new entries 15:00–16:00 ET** | z −4.43, median −0.62R | Late-day entries have no runway and get chopped |
| **Stand down when volatility is too big for your stop** | MNQ ATR(15m) > 58, MGC ATR(15m) > 10. Above that, >25% chance the feed-lag blind spot alone hits the stop | Not an edge. It stops the account bleeding on wild days |
| **Size at ≤ 50% of allowed risk while nothing is proven** | The *only* result that clears its luck bar: shrinking size after losses improves account survival (z 6.2 / 5.5 vs bar 2.2) | Protects the $2,800 drawdown floor |
| **Flat by 16:00 ET** | Costs only 0.003R/trade | Keep it. It's nearly free insurance |
| Structural stop never tighter than ~0.5 ATR | +0.014R vs −0.106R (z +2.0) | Tighter stops just get tagged by noise |

---

## MNQ — Micro Nasdaq-100

| # | strategy (plain English) | evidence | rating |
|---|---|---|---|
| 1 | **Trade any-hours 15m signals, not just 09:30–16:00** ("rth_only off"). A population of 15m rules traded around the clock beat its placebos on fresh data | z +3.05 out-of-sample, but after correcting for overlapping trades 2.17 vs a 2.23 bar. **Vanished in the one falling-market third.** It's really a long bias on a +12% up-trend | ●●○ |
| 2 | **Sweep & reclaim at prior-day high / prior-session high → SHORT** (price pokes above yesterday's high, closes back below, sell) | Hub scan, 5m: PDH n=34, 62% win, +0.18R vs fake −0.25R (z 2.3); prior RTH high n=38, 66% win, +0.26R (z 2.3). 60m: PDH z 2.3. Luck bar ≈ 2.7 | ●●○ |
| 3 | **60m trend-following rows** (90/180-day windows) | +0.66 to +0.70R on n=27–28, but placebos sat in the same top-10 and the list never repeated | ●○○ |
| 4 | **Buy the prior-day low (5m)** | n=42, 55% win, +0.05R vs fake −0.23R (z 1.7) | ●○○ |
| 5 | **Stop to breakeven at +0.8R** (exit overlay) | Both live MNQ fills went well into profit before losing. Untested on the archive | untested — test first |
| ⛔ | Round numbers as support (5m) | n=229, −0.18R vs fake −0.03R (z −2.1) | avoid |

**Bounce view.** On MNQ, prior-day/session **highs that get swept and reclaimed** are the most
promising bounce (short-side) levels. Buying round numbers and plain swing lows is worse than
random. Low-volume nodes on 1-month profiles lean continuation (55% vs 38%), but random prices
in that range lean the same way, so the LVN isn't the reason.
**Cost note:** round trip ≈ 4.9 ticks. The feed lags ~13 min at 5m, and MNQ's blind-spot risk is the worst of the four.

---

## MES — Micro S&P 500

| # | strategy | evidence | rating |
|---|---|---|---|
| 1 | **30m any-hours universe** (trade every qualifying 30m rule, don't pick a top 10) | +0.121R, 86% of 35 rule rows positive, vs placebo universe −0.146R. No single rule clears | ●●○ |
| 2 | **Fade detected support/resistance on 60m** (REPLAY desk, fair control) | Bounce trade beat random lines z +2.52, but earned **+0.043R, below the 0.081R cost hurdle** | ●●○ (unprofitable) |
| 3 | 60m volume-profile / 30m trend near-misses | t 3.04 / 3.18 on only 20 trades each, one window | ●○○ |
| 4 | **Prior RTH low as support (5m)** | n=36, 58% win, −0.00R vs fake −0.35R (z 2.0) | ●○○ |
| 5 | **LVN bounce on 3-day profile** | 60% bounce vs 50% for random prices (n=43). Below the luck bar | ●○○ |
| ⛔ | Everything at 60m level touches | 60m level touches lose *more* than random (all touches z −3.2; clustered levels z −5.9) | avoid |

**Bounce view.** MES 60m behaves like a random walk (the REPLAY desk measured this). The
structure you see at 60m is smaller than the cost of trading it. Short-term (5m) prior-session
lows and overnight lows are the least-bad supports. **Stacked levels (2+ within ¼ ATR) are the
worst place to fade on MES: z −5.9, the strongest level finding in the hub.** Obvious levels
attract stops, and price runs through them.
**Data trap:** MES 60m has contract-roll weeks glued together (≈5% of bars). Skip roll weeks.

---

## MGC — Micro Gold (independent of the index complex)

| # | strategy | evidence | rating |
|---|---|---|---|
| 1 | **Engulfing candle in the direction of 15m structure** | +0.297R, t 2.62, **held +0.216R on fresh data**, but needed t 4.44 | ●●● |
| 2 | **Revert toward the prior session's POC (30m)** + **fade the value-area edge** | +0.199R (n=180, t 2.18) and +0.149R. These are the only level ideas with a positive sign on 4/6 cells. **Matches your volume-profile style.** Top candidate to pre-register | ●●○ |
| 3 | **Opening-range (first 60 min) retest, 15m** | +0.191R, n=108, fresh data +0.167R, but only 20 of 72 neighbouring settings were positive (a spike, not a plateau) | ●●○ |
| 4 | **VWAP band-1 bounce with trend stack (60m)** | +0.317R, positive in 3/3 time slices, but n=24 | ●○○ |
| 5 | **Sweep & reclaim at prior RTH high → short (60m)**; prior-day POC as support (60m) | n=106, −0.03R vs fake −0.29R (z 2.4); POC support n=122, 57% win, +0.11R (z 1.7) | ●○○ |
| ⛔ | **Fading overnight-high/low sweeps** | Worse than random entries, z −3.0 (5m) / −3.1 (15m) | avoid |
| ⛔ | **Buying 5m swing lows** | n=307, −0.26R vs fake −0.06R (z −3.2) | avoid |

**Bounce view.** Gold is the best contract for level ideas. It's cheapest to trade relative to
its moves (costs ≈ 1.7% of risk), and it's the only symbol where **profile-based levels (POC,
value-area edge) lean positive**. Resistance holds better than support on MGC 5m (z +2.6 vs
−3.1). **Daily MGC bars are a different contract/roll: never mix daily and intraday MGC levels.**
Stand down above ATR(15m) 10.

---

## MCL — Micro Crude Oil (independent)

| # | strategy | evidence | rating |
|---|---|---|---|
| 1 | **Momentum on 60m/240m** | 97% of 66 observations positive and beat its control on both session settings, max t 2.97, but fragile to costs | ●●○ — **the one pre-registration candidate** |
| 2 | **Fade a 3-bar breakout (15m)** | +0.148R, beat placebo z +2.70, t only 1.25; dead at 60m | ●○○ |
| 3 | **Opening-range fade / Bollinger-band fade (30m)** | +0.131R (n=61) / +0.114R (n=152) | ●○○ |
| 4 | London-open range expansion (1.15× normal) | A fact about *size* of moves, not direction. Use it for stop sizing | info |
| ⛔ | **Any level bounce on 60m** | Every level touch loses more than random (z −3.6). Clustered levels z −4.8. Sweep & reclaim at swings −0.26R (z −3.0) | avoid |

**Bounce view.** Crude has the most trend days (44% of sessions vs 12% on MNQ), so **levels
break more than they bounce**. Fading levels on MCL is the worst idea in the hub. Costs are
3× gold's relative to risk, and nothing on MCL beats even the single-test bar (best t 1.12
vs 1.18). No usable daily history.

---

## Others

| symbol | status |
|---|---|
| **NQ / ES** (full size) | Same market as MNQ/MES, so they're **not** extra confirmation. NQ 60m holds the project's largest t (3.92, momentum: CVD + fast-EMA + MACD with volume surge, n=44, +0.29R), still under its 4.13 bar. Full-size contracts are too big for the $50k plan |
| **Grains** MZC/MZS/MZW | **Not usable.** The data glues contract months together, with 26–89% flat bars |
| **QQQ / SPY** | Not tested. Intraday volume is 58–59% zeros, so no volume-profile work is possible |

Full tables with every number and source file: `sources/agent1_roundtable.md` §2,
`sources/agent2_research.md` §1–7, `sources/agent3_desks.md` §3.
