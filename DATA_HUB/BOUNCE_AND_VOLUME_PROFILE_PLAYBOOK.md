# Bounce levels & volume profile — the owner's playbook

**The owner's method (every agent must work from this):** scan each market on several timeframes,
build volume profiles over ranges of different lengths (a range can hold several trend legs), mark
the **low-volume prices (LVNs)** as key levels, and decide whether price will **continue through**
or **bounce off** each one. Classic levels (prior day/week high-low, overnight range, VWAP, POC,
round numbers) are tracked the same way.

This page covers what we know about that method, why a level should bounce, and what the data
says actually decides it. It ends with a checklist and today's levels.

Generated evidence: `levels/<SYM>_volume_profile.md` (LVNs, continuation vs bounce),
`levels/<SYM>_bounce.md` (classic levels), `levels/CONSISTENCY.md` (which results repeat on
all four symbols). Refresh with `bash DATA_HUB/tools/update_hub.sh`.

---

## 1. Why a level *should* bounce: the theory in plain English

| level | why traders expect a reaction |
|---|---|
| **LVN** (thin volume between two heavy areas) | Price moved through it fast last time. Nobody wanted to trade there, so it's where one trend leg handed over to the next. Coming back, it's either **rejected again** (bounce) or, if accepted, price **travels fast** through the thin area to the next heavy area (continuation). An LVN is a *decision point*, not a guaranteed bounce. |
| **HVN / POC** (heavy volume) | Price that both sides agreed on. It acts like a **magnet**: price slows down and chops there, which makes it a target more than a turning point. |
| **Value area edges (VAH/VAL)** | The boundary of "fair" price. Inside value, price tends to rotate to the other edge. Outside, it either gets rejected back in or is accepted and trends away. |
| **Prior-day/week high & low, overnight range** | Everyone can see them. Resting orders and stops sit there, so a reaction is likely, but so is a **stop run** (sweep) *first*. |
| **Round numbers** | Human anchoring. Orders and options strikes cluster there. |
| **VWAP / prior-day close** | Where the average participant's cost sits. Trapped traders defend it or bail out there. |

## 2. What the data actually says (≈45,000 real level touches, plus ≈250,000 fake/random ones as controls; 4 symbols, 5m & 60m)

We tested every level against **fake levels** (same lines shifted randomly) and **random prices in
the same profile range**, with the same entries, stops, targets and costs.

**Headline:** on its own, *where* the level is doesn't make price bounce or continue more than a
random price would. What decides the outcome is the context and how the trade is taken.

### What tilts toward a BOUNCE (best evidence first)

| condition | measured | strength |
|---|---|---|
| **LVN on a 60m-built 1-week profile, price rising into it (testing it as resistance)** | Continued 17 points *less* often than random prices in the same range. **Same direction on all 4 symbols** (MCL −12, MES −18, MGC −35, MNQ −11; n=177) | ●●○ best-supported form of your idea: **pre-register it** |
| **LVN with heavy volume on the touch (>1.5× normal), 1-week (60m) & 1-month profiles** | −9 and −19 points of continuation vs random, 4/4 symbols | ●●○ |
| **LVNs on 60m-built profiles in general** (1-week, 3-month) | −6 / −9 points vs random, 4/4 symbols | ●○○ small but consistent |
| **Prior day's VWAP or close acting as resistance** | Beat fake levels on 7/8 and 6/8 symbol-timeframes (combined z +1.9 / +1.6) | ●○○ |
| **Sweep & reclaim of prior-day / prior-session HIGH → short** | MNQ 5m: 62–66% win, +0.18 to +0.26R vs fake −0.14 to −0.25R (z 2.3); MGC 60m z 2.4; combined z +1.65 | ●○○ |
| **Level already tested before (retest)** vs first touch | Retests beat fake 5/8. First touches are *worse* than fake (combined z −3.7) | ●●○ as a *don't*: **skip first touches** |
| MGC: fade the value-area edge, revert toward prior POC (30m) | +0.149R / +0.199R (t 2.18), positive in 4/6 cells | ●●○ (MGC only) |

### What tilts toward CONTINUATION (the level breaks)

| condition | measured | strength |
|---|---|---|
| **Stacked levels** (2+ levels within ¼ ATR, e.g. PDL = RTH low = swing low) | Worst place to fade: combined z **−5.1**; MES 60m −5.9, MCL 60m −4.8 | ●●● **the most reliable level finding in the project** |
| **Plain swing lows as support** | Worse than fake (combined −3.1); MGC 5m −3.2 | ●●○ |
| **Supports in general** vs resistances | Supports −3.2, resistances +1.0 (sample was a rising index market, Jul–Sep 2026) | ●○○ regime-dependent |
| **Crude oil (MCL) levels** | 44% of MCL days are trend days (MNQ 12%). Every MCL 60m level touch lost more than random (z −3.6) | ●●○ |
| **Price arrives fast / in a volatile market** | No reliable effect either way. Volatility changes the *size* of moves, not the direction | — |
| **Overnight-extreme sweeps on gold** | Fading them is worse than random, z −3.0 | ●●○ |

**Why stacked levels break:** the more obvious a level, the more stop orders sit just beyond it.
Price runs those stops (the sweep) before any bounce. So a bounce trader buying *at* the obvious
level gets stopped, and the bounce comes afterwards. That's why **"sweep & reclaim" was built as
a second entry mode.** It waits for the stop run and the close back. Today it only beats fake
levels at prior *highs*, not everywhere.

### What did NOT matter (measured, no effect)

Fibonacci levels · order blocks / fair-value gaps (random zones get "filled" 87–90% too) ·
multi-timeframe agreement (slightly *hurts*) · volume at 1m/5m bounces · time-of-day filters
beyond "no entries 15:00–16:00" · touch-count stories (a random-line control rises the same way).

## 3. Continuation-or-bounce checklist (use at every LVN or level)

Ask these in order. Each has the evidence behind it.

1. **Is it a stacked / obvious level?** Expect a sweep first. Don't rest a limit order on it.
   Wait for the poke-through and the close back (sweep & reclaim), or skip it.
2. **Which profile is it from?** Prefer LVNs from **60m-built profiles (1-week, 1-month,
   3-month)**. The bounce lean shows up there on all 4 symbols. 5m-built 1-day/3-day LVNs are
   coin-flips.
3. **Which side is price coming from?** Rising into an LVN from below (resistance test) is the
   strongest bounce lean measured. Falling into an LVN on a 3-month profile also leans bounce
   (4/4 symbols, −13 pts).
4. **Is this the first touch?** First touches break more often. Prefer a level that has already
   held once.
5. **Is volume heavy on the touch?** On 60m profiles a heavy-volume touch of an LVN leans bounce
   (4/4). Volume on 1m/5m bars told us nothing.
6. **Which market?** MCL trends and breaks levels, so be careful fading. MGC is the best market
   for profile levels (value-area edge, POC reversion). MES/MNQ are one market: agreement between
   them is not confirmation.
7. **Is the stop outside the sweep zone?** Never tighter than 0.5 ATR, and beyond the obvious
   level's stop cluster. Stand down if ATR(15m) is above 58 (MNQ) or 10 (MGC).
8. **Plan the exit before entry.** Every live paper trade reached +0.83R before most lost.
   Take partial profit or move the stop to breakeven around +0.8R (untested; see
   `OPEN_QUESTIONS.md`).

**Why it would bounce, in one line per case:**
- **LVN from below on a weekly/monthly profile:** sellers rejected this thin price last time.
  With heavy volume on the touch, they're showing up again → bounce lean (measured 4/4 symbols).
- **Prior-day high swept and reclaimed:** breakout buyers are trapped above yesterday's high and
  their stops sit below it → short-side bounce (measured on MNQ and MGC, not yet proven).
- **Prior-day VWAP / close from below:** yesterday's average trader is at breakeven there and
  sells → resistance holds more often than random (7/8 runs).
- **Stacked support:** everyone's stops are just below. Expect the flush first, and only then a
  possible bounce.

## 4. Levels near price — snapshot as of 2026-09-29 00:55 ET (NOT live, refresh first)

`ATR` below is the 60m ATR. "Leans" uses the checklist above. Full lists are in the `levels/` files.

### MNQ — last 30,431.75 · below its 60m EMA50 (30,656), short-term down · 60m ATR 121
- **Supports:** 30,400 round (0.3 ATR below; round-number supports are worse than random on MNQ) ·
  **30,356.50–30,370.75 stacked** (prior-day low = prior RTH low = swing lows, set 09-28 10:45).
  *Stacked → expect a sweep below 30,356.50 before any bounce. Only a close back above is a
  bounce signal.* (The desk's owner level 30,430 bounced +107 pts on 09-28, then broke to
  30,412.50 and set a higher low at 30,427.75.)
- **Resistances:** prior-day POC 30,472 + 30,500 round (0.3–0.6 ATR) · 1-week value-area low
  **30,522.50** (price is below this week's value) · prior-day close **30,556.75** (1 ATR;
  prior close as resistance beat fake levels 6/8).
- **Profile view:** 1-week (60m) profile is TREND_DOWN with four legs:
  31,044→30,371 ↓, →30,999 ↑, →30,357 ↓, →30,722 ↑. The 1-month profile is balanced
  (POC 29,513.50). Its LVN at **30,026.25** sits 3.3 ATR below, and history there leans continuation
  (61% continued vs 32% bounced), but random prices did the same.

### MES — last 7,726.75 · below 60m EMA50 (7,763.6) · 60m ATR 19.4
- **Price is sitting on a stacked support: 7,725–7,726** (prior-day low = prior RTH low = swing
  low = 7,725 round). **On MES, stacked levels are the worst place to buy (z −5.9).** Treat a
  break below as likely, and look for the reclaim instead.
- **Supports below:** 2-week LVN 7,720.50 (history leans continuation 56/40, random the same) ·
  prior-week low / swing 7,710 (0.9 ATR). Overhead LVN on the 1-month profile: 7,816.
- **Resistances:** swing 7,739.25 · prior-day POC 7,743.50 · prior-day close 7,746 · 1-week value
  low 7,738.25 (price below value).

### MGC — last 4,158.40 · below 60m EMA50 (4,225.8), down-trend · 60m ATR 18.6
- **Right at the 3-month value-area low (4,160.90).** Fading the value-area edge is MGC's
  best-supported level idea (+0.149R at 30m, not proven). The 3-month profile is balanced
  (POC 4,393.60), so price at the bottom of value is a classic rotation-or-breakdown decision
  point.
- **Supports:** 4,150 round + prior-day close 4,148.70 (0.5 ATR) · **4,143.00–4,143.90 stacked**
  (prior-day low = RTH low = swing lows, 09-28). The desk's owner level **4,145** bounced +26.7 pts.
  Stacked → watch for a sweep under 4,143 and a reclaim.
- **Resistances:** prior-day POC 4,161.80 (0.2 ATR) · swing 4,172.60 / 4,175 round · prior RTH
  high **4,189.60**. On MGC 60m, a sweep & reclaim of the prior RTH high → short is the
  best-scoring level (z 2.4).
- **Profile view:** 1-week (60m) profile TREND_DOWN in three legs: 4,400.80→4,278.20 ↓,
  →4,351.60 ↑, →4,143.00 ↓. **LVN 4,273.60** sits between the legs as overhead resistance (6 ATR
  away). A rally into it from below is the situation that continues *less* often than random
  prices do (§3, step 3). On MGC alone, LVNs in this spot still ran 54% continue / 44% bounce, so
  treat it as a decision point, not a sure bounce. The 3-month profile also has an **LVN at
  4,215.40** overhead (3 ATR).
- ⚠ Daily MGC bars are a different contract. Don't mix them with these intraday levels.

### MCL — last 94.25 · above 60m EMA50 (93.61), up · 60m ATR 1.06
- **Price is at a swing high 94.25.** Resistances 94.72 swing and 95.00 round. Supports: prior-day
  VWAP 94.02 + 94.00 round (0.2 ATR), prior-day POC 93.43.
- **Profile view:** the 1-month profile is balanced (POC 92.18). Its **LVN 98.11** sits above
  (3.6 ATR) and leans continuation historically, but random prices do the same.
- **Crude breaks levels more than it bounces** (44% trend days, every 60m level type below
  random). Be the most sceptical of bounces here.

_Snapshot came from `data/archive` through 2026-09-29 00:58 ET. Run `bash DATA_HUB/tools/update_hub.sh`
and read `levels/` for current numbers._
