# LTA Concepts 2.0, digested for this desk

**Source:** *LTA Concepts 2.0* e-book (XLimitless, 314 pages, PDF supplied by the owner on
2026-10-02). Below is a paraphrase in plain English. Every rule carries the PDF page it came from, written `[pN]`.
The book itself is **not** committed to the repo (69 MB, and it is the author's copyrighted work).
The owner keeps the original.

**Page numbers (owner's copy, 2026-10-04):** the owner's PDF is 304 pages: cover on p1, blanks on p2–15,
the TOC on p16–17, then the book. **PDF page = the page number printed in the book** (Chapter 1 = p18,
glossary = p294–303). The `[pN]` cites below are from the ORIGINAL 314-page PDF. Subtract 10 to get the
book/PDF page the owner sees, e.g. `[p36]` → page 26. The Introduction (book pages 1–16) isn't in the
owner's copy. Its content is summarised in §1.

**Where this lives:** `LTA_Concepts/`, the separate LTA study area (see its README).

**Who uses this page:** the **LTA Concept Callouts** agent (`.claude/agents/lta-concept-callouts.md`,
lane `workspace/paper/LTA/`) and anyone checking that agent's reasoning.

**The one thing to know first:** the book's method sits very close to the owner's own style
(multi-timeframe volume profiles, key levels, continuation vs bounce). This repo has already
**measured** several of its building blocks, and most of them did not beat random prices on their
own (§10). So the agent treats the book as **a structured way to make a discretionary read**,
not as a system with a proven edge. Every callout it makes is labelled `DISCRETIONARY` and is paper only.

---

## 1. The framework in one picture

The book stacks five layers, top-down, and says you should never skip a layer [p21–p25]:

| # | layer | question it answers | where it comes from |
|---|---|---|---|
| 1 | **Macro fundamentals** | *Which way should I even be looking?* | COT positioning, sentiment, seasonality, valuation vs a related market |
| 2 | **Macro technicals** | *Where would big money act?* | Supply and demand zones on monthly, weekly, 3-day, daily, 12h and 8h charts |
| 3 | **Intraday trend** | *Is the big idea starting to play out now?* | Two swing points (higher high + higher low, or lower high + lower low), breaks of structure, the prior week's range |
| 4 | **Micro execution** | *Exactly where and when do I enter?* | Volume-profile levels (PD, EPD, PW, EPW, CW, fixed range, swing) and four entry models on 15m–1h |
| 5 | **Trade management** | *How much, and how do I handle it?* | 2:1 reward-to-risk, 2% / 1% risk, two-strike rule, breakeven for contrarian trades |

**Order of work (decision sequence):** macro → sentiment → seasonality → valuation → technical
zone → execution → risk [p25]. "Walk away" is a valid answer at every step. The book says the
layers build up **over days or weeks**, not in a single top-down pass. First an alert plants a bias, then
price reaches a weekly zone, then an intraday trend forms, and only then are trades taken. One
bias can then produce many trades [p268].

---

## 2. Volume analysis: the levels (Section I)

### 2.1 Building blocks [p31–p39]
- **Volume profile:** how much traded at each *price* over a chosen stretch of time.
  The book prefers it to time-based Market Profile because one heavy, brief fight can matter more
  than a lot of idle time [p29].
- **POC (point of control):** the busiest price. It acts like a **magnet**. Price above the POC treats
  it as support on a retest, and price below treats it as resistance. Price sitting at the POC means balance and chop [p37].
- **Value area (VAH/VAL):** the band holding about 70% of the volume. Inside it the market is
  balanced. A move outside it can start a breakout or a trend [p38].
- **HVN (high-volume node):** a heavy shelf. When price returns there, expect it to pause or bounce [p38].
- **LVN (low-volume node):** a thin area. Price tends to **travel quickly through** it to the next
  HVN [p38]. *(The owner and this repo treat LVNs as decision points. See §10.)*
- **Use futures volume, not CFD volume.** Futures volume is centralised, so everyone sees the same map [p29].
- **Combining with zones:** a supply zone that sits on an HVN makes a strong wall. A demand zone
  over an LVN may get sliced through, so expect the reaction deeper, at the real volume [p39].

### 2.2 The weekly cycle and the Sunday Open [p41–p44]
- **Sunday Open (SO):** the first price of the futures week (18:00 ET Sunday). It sets the week's
  liquidity map. An open beyond last week's high or low is often a **trap**. The worked example has gold
  opening under last week's low, panic selling, then reclaiming the level by Monday's NY session [p42].
- **Rhythm:** Monday and Tuesday bring traps and fakeouts. Wednesday and Thursday show the real move
  (with the big data releases). Friday is unwinding, and its close hints at next week [p43].
- **Practical rules:** watch the SO for liquidity grabs; treat last week's high and low as magnets;
  stay cautious early in the week; want a midweek confirmation; read the Friday close [p43].
- **SO reclaim example:** price dips under the SO in Asia, then reclaims it hard in London, and that
  reclaim is the long trigger [p44].

### 2.3 Weekly profiles [p46–p49]
- **EPW** (early previous week, the week before last), **PW** (previous week) and **CW**
  (current week), each with POC, VAH and VAL.
- PW levels are the main weekly reaction zones. For example, above the PW VAL you look for a bounce,
  and a break below it signals weakness [p47].
- **CW** levels are only reliable once **Monday–Wednesday have closed** ("mid-week volume range") [p48].
  *(The glossary says 2 days [p304]. The desk uses the stricter 3.)*
- Confluence example: a CW POC lining up with the PW VAH [p48].

### 2.4 Daily profiles [p51–p54]
- **PD** = the previous full session. **EPD** = the session before that (the book's charts draw
  EPD as the day before PD) [p53]. The futures day resets at **18:00 ET** [p53].
- **Don't trade current-day levels early**, because there isn't enough data yet [p52].
- **PD levels lead** in a clean trend with no overnight shock. **EPD levels matter more** after a big
  overnight move [p52].
- **Reading:** price above PD VAH = strength, so buy retests. Below PD VAL = weakness, so sell retests.
  Around PD POC = balance, so expect chop until a break [p52]. An EPD level that is touched and quickly left
  is being defended. An EPD level broken on strong volume tends to bring follow-through [p52].

### 2.5 Fixed-range profiles: ranges [p56–p60]
- Draw a profile by hand over a **consolidation**. Inside it, big players are either
  **accumulating** (to go up) or **distributing** (to go down) [p56].
- Two ways a range breaks [p57]:
  - **CERC:** Consolidation → Expansion → Retracement (into the range's fixed POC, VAH or VAL) → Continuation.
  - **CME:** Consolidation → Manipulation (a fake break, often into a key level) → Expansion the other way.
- After the break, the **Fixed POC / VAH / VAL** are the retest entries [p58–p60].

### 2.6 Swing profiles: strong trends [p62–p64]
- When a trend never pulls back to yesterday's or last week's levels, draw the profile over the latest
  **swing (wick high to wick low)**. The **Swing POC** is the most common turning point. A reclaimed
  and held Swing VAH means continuation. A rejected Swing VAL in a downtrend means momentum is still down [p63–p64].

---

## 3. The four entry models [p66–p80]

All four require price to have **"mitigated"** (touched) a key level first.

| model | timeframe | what you see | entry | stop |
|---|---|---|---|---|
| **EM1 Double Wick** | medium–high (30m–4h) | Candle 1 touches the level and closes back, leaving a wick. Candle 2 wicks into it again and flips | after the second close, or on the third candle's flip | beyond the wick or the prior high/low [p67] |
| **EM2 Internal Swing** | medium–low (15m) | After the touch, draw a profile on the internal swing. Wait for price to return to the **LTF Swing POC**, then apply EM1 on the lower timeframe | the flip at the LTF Swing POC ("A" = aggressive at the POC, "B" = wait for expansion) | below the internal candle [p68, p74–p75] |
| **EM3 Internal-structure break** | any | Consolidation near the level → manipulation (a fake break of the level) → price breaks the high/low that started the manipulation | on the break | beyond the manipulation extreme [p69–p70, p75–p76] |
| **EM4 Continuation / candle flip** | any | Three bars: bar 1 touches and hesitates, bar 2 flips, bar 3 confirms. **Only with a bias already set** | on bar 3, not on the trap candle | under the flip candle's wick [p70–p71] |

**Timing rules for execution [p73]:**
- Low volume means waiting for a higher-timeframe close. High volume means closes at the level confirm better.
- Be careful before the **London and NY opens** (manipulation) and before **red-folder news**. Use small risk if you are in early.
- A second visit to a level calls for extra confirmation (a higher-timeframe close, or EM2).
- **Don't enter in the last 10 minutes before a 30m/1h close.** Wait for the close and the next candle.
  Within 30 minutes of a 4h close, wait for that close.
- **Fractal escalation:** if a 15m model fails, check 30m, then 1h, 2h, 4h. Higher timeframes give
  stronger confirmation [p80].
- **Targets:** liquidity or the next key level. Skip the trade if a level blocks the target and the
  R:R turns unfavourable [p79].

---

## 4. Macro and sentiment (Section II)

### 4.1 COT basics [p15, p86–p95]
- The CFTC report comes out on **Friday** and shows positions **as of the prior Tuesday**. Stamp it with the Tuesday date [p15].
- **Commercials** (hedgers) are most reliable at extremes. **Large Specs** (funds) are trend fuel.
  **Retail** (non-reportables) tends to be wrong at extremes [p87–p88].
- **COT is context, not a timing tool** [p93]. If positioning already reflects the news, price often
  moves *against* the headline [p83].

### 4.2 Extremes: the core contrarian rule [p97–p104]
- The **highest-value setup** is Commercials at one extreme while Retail is at the **opposite** extreme [p97, p99].
- **Oscillator extreme:** net position scaled 0–100 over **26 weeks** (or 1 year, or several years).
  **≥80 or ≤20** counts as extreme [p98]. Example: DXY in Sep 2024, Commercials 100 / Retail 0 → dollar bottom [p99].
- **Net-position extreme:** raw net position at multi-year highs or lows. Slower, and suited to bigger turns [p97].
- Example thresholds: British pound Retail net **+16.9k to +26.8k** = bullish extreme (bearish reversal);
  **−20.6k to −30k** = bearish extreme (short-term bounce) [p103, p258].

### 4.3 Trend health: Large Spec "laddering" [p106–p109]
- **3 or more weekly reports in a row** of Large Specs adding in the trend direction, with **open interest
  rising**, means the trend is alive. When OI stalls, specs trim, and retail piles in last, the trend is late [p108–p109].

### 4.4 Open interest [p111–p116]

| price | open interest | reading |
|---|---|---|
| up | up | new buyers, strong trend |
| up | down | short covering, trend weakening |
| down | up | new shorts, strong downtrend |
| down | down | longs leaving, possible bottom |

- A fast drop in the 26-week OI oscillator from about 80–100 to about 0–10 signals **exhaustion** [p113, p115].
- Sell template: a strong uptrend, plus OI dropping, plus price into macro resistance, plus Commercials at a bearish extreme [p116].

### 4.5 Futures expiry [p118–p121]
- OI rises into the quarterly expiry (Mar/Jun/Sep/Dec), falls in expiry week, then rebuilds. The
  direction of the rebuild hints at the next trend. Treat this as confluence only. Take the dates from the
  exchange calendar: the book's 2025 dates are the Thursday before the third-Friday expiry.

---

## 5. Seasonality, correlation and valuation (Section III)

- **Seasonality is a confluence, not a trigger, and you must test it before you trust it** [p126, p128].
  The book's model averages 5-, 10-, 20- and 30-year paths [p127].
- **Windows the book states:**

| market | firm | weak | page |
|---|---|---|---|
| Gold | Sep–Feb (Q4, Q1) | Q2–Q3 | p124–p128 |
| Silver | Dec–Apr | May–Aug | p133 |
| Crude | May–Jun (driving season) | Oct–Dec | p134–p135 |
| Nasdaq | Apr–Jul, Oct–Jan | Aug–Sep | p131–p132 |
| S&P 500 | May–Aug | Aug–Oct (Alerts library) | p265–p266 |
| Dollar | Aug–Oct | Nov–Feb (the book contradicts itself on January) | p135–p136 |

- **Correlation gate:** before using valuation, check the correlation coefficient. Near 0 means do not
  use it, and correlations can flip [p144, p146]. No cut-off is given. The desk pre-registers |r| ≥ 0.30.
- **Valuation** (the book's "Stealth Valuation Index"): the asset's % change over N bars minus the
  reference's % change, rescaled to −100…+100 over a window [p148]. References: **gold vs DXY**
  (N=10 daily, window 50); **indices vs 30-year bonds ZB** (N=13 weekly, window 50); **crude vs DXY** [p147–p150].
- **Use valuation in the direction of the macro trend:** undervalued in an uptrend means buy, and
  overvalued in a downtrend means sell. Counter-trend readings need extra confirmation [p260–p261].
  No numeric extreme is given. The desk pre-registers ±80.

---

## 6. Supply and demand (Section IV)

- **Auction Market Theory:** price spends time in **balance** (a range, where both sides are matched and big
  players quietly position) and then breaks into **imbalance** (one side overwhelms, candles stretch,
  volume expands). **Zones are built in the balance, before the breakout** [p158–p160].
- **Fundamentals give the "why", technicals give the "when."** Bias without timing is early; patterns
  without context are fragile [p156].
- **Four patterns** [p164–p166]: Rally-Base-Rally (continuation demand), Drop-Base-Drop
  (continuation supply), Drop-Base-Rally (reversal demand), Rally-Base-Drop (reversal supply).
- **Three-candle bar play:** a base becomes a zone when candle 3 closes beyond candle 1's range [p166].
- **Strong zones** form after sharp moves, are untested (the first retest is strongest), and show high volume in the base [p166].
- **Timeframes:** mark zones from the top down: monthly, weekly, 3-day, daily, 12h, 8h. Higher means more reliable [p167].
- **Macro structural shift:** a new demand zone that **takes out** a prior supply zone means buyers are in
  control. Expect a pullback to that demand, then continuation. The mirror applies for supply [p170–p171].
- **Validate zones with macro "stacks":** COT, valuation, seasonality and OI. One or two can be enough;
  two or three aligned gives conviction [p173–p178].
- **Intraday trend** [p180–p184]: it needs **two touch points** (HH + HL, or LH + LL). Before a break of
  structure you are in the **preparation phase** (plan, don't trigger). After it you are in the **execution phase**.
  A **break of the previous week's high or low** is one of the most reliable markers that new value is accepted.
- **Accumulation and distribution at macro zones:** don't expect a V-turn. Expect a range, failed breaks,
  slowing momentum, then CERC or CME [p186–p189]. A **news failure** (the market uses the news to shake people
  out, then reverses) strengthens the reversal [p189]. Head-and-shoulders and W bottoms count **only in that context** [p189–p191].

---

## 7. The execution framework (Section V)

- **Two archetypes** [p193–p198]:
  - **Contrarian:** COT and sentiment extreme, plus smart money stepping in, plus a macro zone, plus valuation.
    You fade the crowd at the zone. Risk is lower, and you move to breakeven sooner.
  - **Momentum:** after the macro structure shifts (a zone takes out the opposite zone), with breakouts on
    volume, OI rising and Large Specs laddering. You ride the trend and give it room.
  - **Momentum usually starts where extremes end.** Once positioning is back to neutral, follow the Large Specs [p196].
- **Giants and snipers** [p200–p205]: higher-timeframe **supply and demand** (8h–monthly) sets the
  battleground and the bias. Lower-timeframe **volume profile** (15m–1h) times the entry.
- **Hybrid model** [p207–p212]: one bias, two timelines. Swing it from the zone, and/or day-trade the
  intraday trend inside the same zone.

---

## 8. Risk, money management and psychology (Sections VI–VII)

- **Fixed 2:1 reward-to-risk.** It keeps the data clean and the mind calm. The break-even win rate is about 33%
  (the book's table shows 35%), versus 51% at 1:1 [p216]. Only stretch toward 2.5:1 or 3:1 after 50–100 trades of data [p217].
- **The 2/2/2 rule** [p219]:
  1. Every trade offers **at least 2R**.
  2. **At most 2% risk** per trade, and **1%** when contrarian, counter-trend, at an unconfirmed zone, or
     while building a buffer [p221].
  3. **Two losses in a row means stop for the day**, unless the day is already up. Two correlated trades
     count as one bet [p222].
- **Earn size:** the first 30 rule-following trades come first. Keep size constant through win and loss streaks [p222, p236–p237].
- **Win-rate yardstick after 30 trades** (at 2:1): under 33% means something is broken; 40%+ means the strategy is working;
  50%+ means the edge is solid [p225]. *This is the book's yardstick. This repo also requires a placebo before any edge is claimed.*
- **Trade management** [p229–p230]: contrarian trades move to **breakeven at +1R**; momentum trades do not.
  Scale in on **swing trades only**. If you were in from London and are not in profit near the NY open, cut the trade. Late in NY with no
  progress, close it. Close before high-impact news (examples: a trade closed at 1.85R ahead of CPI [p288]).
- **Bias checks** [p232–p241]:
  - Confirmation bias: what would invalidate this idea?
  - Overconfidence: has size crept up after wins?
  - Anchoring: "just get back to breakeven" thinking.
  - Loss aversion: cutting winners at 1R.
  - Illusion of control: is this trade in the plan, or am I trying to feel in control?
- **Scenario map at every zone** [p244]:
  - Sharp rejection: it's confirmed, so drop to the lower timeframe.
  - Slow grind into the zone: wait.
  - Clean break plus a structure shift: scrap the plan.
- **Journal fields** [p251–p252]: asset; macro bias; technical context; intraday state; contrarian or
  momentum; screenshots; stop, target, R:R and size; session; duration; outcome and whether the plan was followed; mindset.

---

## 9. The book's "Alerts library" claims, flagged

The book quotes win rates for its COT, valuation and seasonal signals [p256–p266]:

| signal | claim |
|---|---|
| Dollar, Commercials vs Retail at opposite 26-week extremes | ~75% since 2015 |
| Pound, Retail at a bullish extreme | 88% |
| Pound, Retail at a bearish extreme | 80% |
| Gold, undervalued vs DXY in an uptrend | 75% |
| Gold, overvalued vs DXY in a downtrend | 69% |
| Natural gas, Retail at a bullish extreme in a downtrend | 77% |
| S&P 500 seasonal | weak Aug–Oct |

**None of these figures comes with a sample size, a payoff, a placebo or a multiple-testing
adjustment.** This repo's rule is that a win rate means nothing without the payoff and a random-entry
comparison. **Do not quote these numbers as edges.** They are hypotheses (see the charter, §5).

All of the book's 10 worked trades follow the same template: alert (COT, valuation or seasonal), then a
weekly or daily zone reaction, then an intraday trend, then **EM1 at a PD/PW/Fixed POC, VAH or VAL on 30m or 1h**, then a
**2R target**, with BE at 1R only when contrarian [p271–p301]. That template is what the callout agent applies.

---

## 10. How the book lines up with what this repo already measured

| book says | repo measured | so the agent… |
|---|---|---|
| PD/PW POC, VAH and VAL are high-probability reaction levels | Levels (incl. POC, VWAP, prior day H/L, LVNs) **do not bounce or break more often than random prices** (≈45k touches vs ≈250k controls) | treats a level as *where to look*, never as the edge |
| A first retest of an untested zone is strongest | **First touches are worse than fake levels** (combined z −3.7); retests beat fake on 5 of 8 | flags first touches and prefers EM3, EM1 or EM4 confirmation over a bare touch |
| Stacked confluence (CW POC = PW VAH) is a strong zone | **Stacked levels are the worst place to fade** (z −5.1): stops sit beyond them and get swept | flags `STACKED` and prefers sweep-and-reclaim (EM3) |
| BE at +1R for contrarian trades | Stop-to-BE at +0.8R **changed 4–7% of trades and did nothing** (best t +1.74) | applies the book's rule and tracks it, while telling the owner it is unproven |
| 2% risk per trade | The $2,800 floor makes 2% ($1,000) fatal in 3 losses; **size-shrinking governors are the one result that clears its bar** (\|z\| 6.2) | maps the book's "2%" to **min(0.5% equity, 10% of room to the floor)** and "1%" to half of that |
| Avoid manipulation around the opens | **No entries 15:00–16:00 ET** (z −4.43) is the measured time rule; other hour filters did nothing | enforces 15:00–18:00 no-entry, plus the book's candle-close and news cautions |
| Multi-timeframe confirmation | Requiring MTF agreement measured **slightly worse** (z −4.09, rule 2, narrowed in ADJ-14) | doesn't add timeframes for comfort; the escalation in [p80] is used only to re-check a failed model |
| CME/manipulation, then expansion | Sweep & reclaim of the **prior-day high → short** is one of the better-scoring level ideas (z 2.3–2.4, not proven) | EM3 is the model it trusts most at obvious levels |
| COT, OI and seasonality layers | Not testable here: **cftc.gov is blocked** by the network policy; the `openinterest` conditions in the package are dead | asks the owner for COT reads (`cot_inputs.json`); seasonal and valuation proxies come from Yahoo |

---

## 11. What the agent can and cannot compute here

| layer | status | tool |
|---|---|---|
| PD/EPD/PW/EPW/CW profiles, SO/PSO, PDH/PDL, PWH/PWL/PWC, swing profile | **computed** from `data/archive` | `workspace/paper/LTA/lta_levels.py` |
| Intraday trend (2 touch points, BOS), weekly-cycle phase, PW-range acceptance | **computed** | `lta_levels.py` |
| EM1 / EM3 / EM4 candidates on closed 30m/60m bars | **detected**; EM2 needs a chart-reader's judgement | `lta_levels.py` |
| Valuation vs reference, correlation gate, macro trend, seasonality | **computed** from Yahoo daily/weekly (public proxies, not the LTA indicators) | `macro.py` |
| COT, Retail and OI extremes | **manual**: the owner fills `cot_inputs.json`, else `UNKNOWN` | `macro.py` |
| Higher-timeframe supply/demand zones (monthly→8h) | **judgement**: the agent reads them off the bars or asks the owner | — |
| Gating, 2/2/2 sizing, two strikes, journal, resolution | **computed** | `callout.py`, `ledger.py` |

_This is research and decision support, not financial advice. Paper only._
