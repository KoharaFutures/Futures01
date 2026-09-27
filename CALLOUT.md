# Live callout session — operating brief

This session exists to make **live trade callouts** on micro futures for a **$50,000 account**,
using the principles measured in this repository. Read this file first, every session.

## Colour convention (set in `futures_agents/alerts.py`)

- **BUY / LONG → blue background** (ANSI 256 colour 27, white text)
- **SELL / SHORT → orange background** (208, black text)
- NO TRADE → grey (250). SIGNAL → slate (61).

NO_TRADE was deliberately moved off orange and SIGNAL off bright blue, so that neither can be
mistaken for a direction in peripheral vision. Render callouts with
`futures_agents.alerts.alert(Priority.LONG | Priority.SHORT | Priority.NO_TRADE, headline, body)`.
`futures_agents/dashboard.py` derives its HTML colours from these codes, so both surfaces agree.

## The single most important constraint

**CORRECTED 2026-09-27. The previous version of this section said "there is no live data feed in
this environment; outbound egress to every data vendor is blocked at the proxy." That is false and
was false when a session acted on it.** Yahoo Finance is reachable through
`futures_agents/data/yahoo.py` — verified by a 157,000-bar pull into `data/archive/` on 2026-09-26.

**What is true is narrower and still binding:**

- **Data is reachable but not real-time.** The archive's newest bar is `2026-09-25T16:00-04:00`.
  Anything fresher must be pulled at the moment of the callout, and the pull must be *stated* — the
  timestamp of the newest bar you actually hold goes on the callout, every time.
- **`csv/raw/` ends 2026-09-22, is read-only and immutable.** Never write to `csv/`.
- **Vendor caveats that will bite:** futures need the `=F` suffix; every interval has a hard
  lookback cap and asking beyond it returns an **empty frame with no error**; there is no native 3m
  or 4h bar; `MCL` has no daily history and full-size `CL=F` is not a substitute (0.95¢ mean close
  difference, 4¢ worst); `MNQ=F` is not TradingView's `MNQ1!`.
- **Never state a level as current unless you fetched it in this turn or the user gave it.** A price
  from the archive is a price from 2026-09-25, and saying otherwise is the one error that costs money.

If a pull fails, say so and fall back to asking the user for the picture. Do not silently serve a
stale level as live.

## What the research actually established

Roughly 3 million strategy evaluations across this repo. **Nothing is live-eligible.** Not one
strategy has ever cleared its own multiple-testing threshold; the highest t-statistic anywhere is
3.92 against a required 5.13. Placebo entries — random bars through the same exits — rank
alongside real strategies. Trading the previous period's top-10 list returns **−0.0155R per trade
against a −0.0104R null**, and **selecting the top 10 underperforms trading the whole qualifying
universe.**

**This does not mean "say nothing".** It means every callout carries an honest confidence, and
the framework below is used as *structure for a discretionary read*, not as a system with a
measured edge. Say which it is.

## The framework, per symbol

**RETRACTED AND REPLACED 2026-09-27.** The previous version of this table named a best family per
symbol — "MCL: MOMENTUM (66 obs, 97% positive, beat control on both)" and "MGC: VWAP, TREND,
MOMENTUM, MULTI_TIMEFRAME all modestly above control". **Both rows have since been measured against
proper controls and neither survives.** Do not use that table; it is the most dangerous thing that
was in this file, because it was the session's entire basis for ranking confidence.

What replaced it, per symbol, measured on `data/archive` by the edge programme:

| symbol | largest *t* found anywhere | its own threshold | verdict |
|---|---|---|---|
| **MGC** | **+2.62** (scalp) — implies an annualised Sharpe of 6.58, a figure that does not occur in real futures | 4.441 | **41% short.** Separately, an adversarial harness attacked a real MGC 60m top 10 and **killed all ten rows** (largest +1.965 vs `free_t` 3.505); two pairs were exact clones, so it was a top 7. |
| **MCL** | **+1.12** | 1.177 | **Fails even the single-pre-registered floor**, the most generous threshold in the codebase. On MCL the answer is nothing at *every* threshold. |
| **MES** | largest *real* **3.116** | — | **Rank 1 is a placebo in 7 of 12 arm-cells.** No ranked list is publishable. |
| **MNQ** | sign z **+3.41** on 15m with `rth_only=False`; survives a leak-free holdout | 2.229 | **Deflated sign z 2.17 — misses.** And the one down-tape third has **none** of the effect (z +0.19). |

**The largest *t* anywhere in a 21,060-strategy search on the index complex is 3.82 and it belongs
to a placebo.** Programme-wide: largest *t* ever found 3.923 against `free_t` **5.46** (5.15
discounting the 82% of generated strategies that never trade). The old "3.92 against a required
5.13" understated the threshold.

**So there is no per-symbol "what measured best" to rank confidence by.** A directional callout here
is a discretionary read using this framework as *structure*, and it must say so on the row. That is
not a reason to refuse to answer — it is a reason the confidence line is the most important line.

MGC and MCL are the only **independent** contracts. MES/MNQ/NQ/ES are one index complex, so
agreement between them is not corroboration.

**And a constraint on any per-symbol claim, found 2026-09-27:** each symbol was only ever tested on
the families its profile let through — MGC 6 of 13, MES 7, MNQ 7, MCL all 13. **MGC has never been
tested on BREAKOUT, MES never on MOMENTUM, MNQ never on VWAP.** An excluded family was not tried and
beaten; it was never generated. See `workspace/studies/STRATEGY_CATALOGUE.md` §1.

## Rules that came out of the measurements

1. **Two signals and one filter.** Going from 2 signals to 4 cuts trade count 35% and does not
   improve expectancy — the sign favours two. More confluence is a worse trade.
2. **Multi-timeframe agreement is not a virtue.** Requiring any alignment signal measured
   detectably *worse* than requiring none (z = −4.09). On a two-timeframe frame, "majority" and
   "unanimous" are the same statement. It wins months often and loses on average — fat tails, not
   an edge.
3. **Win rate and payoff cancel.** Moving a stop from a structure level to a wider ATR raises
   payoff ~89% and drops win rate ~14 points for **no** expectancy gain. Never quote one without
   the other.
4. **Structural stops: never tighter than ~0.5 ATR.** Below that they are noise, and the tighter
   stop is hit more often than the better ratio is worth.
5. **Do not open intraday positions 15:00–16:00 ET** (z = −4.43, median −0.617R, replicated).
6. **No hours filter improves expectancy.** The lunch-avoidance folk claim is refuted.
7. **Sub-hourly is a graveyard.** At 5 minutes, 11–16% of strategies make money.
8. **ORB and ICT do not pay here.** Yesterday's opening range beats today's; FVG/order-block fill
   rates are reproduced by random zones; the ICT sweep→shift→retrace sequence is real, common, and
   adds nothing over its parts.

## Risk, non-negotiable

$50,000 account. Size every callout from a defined stop, state risk in both R and dollars, and
respect the risk engine's limits (`futures_agents/risk/`). NQ and ES are **full-size** — a median
NQ trade risks ~$2,700, which is 5.4% of the account per contract. Prefer MNQ/MES/MGC/MCL.

## How to answer

Give the direction, the entry, the stop, the target, the R:R, the dollar risk, and **the
confidence with its basis**. Where the read is discretionary chart-reading rather than a measured
edge, say so in one line. A "no trade" is a legitimate and frequent answer — render it grey.

Known-broken machinery is catalogued in `workspace/studies/DEFECTS.md` (D1–D43); check it before
trusting any number a tool in this repo prints.

---

# Rule 2 restated, per ADJ-14 (2026-09-27)

Rule 2 read: **"Multi-timeframe agreement is not a virtue."** Two findings landed on it from
opposite directions and the ruling is that they do not conflict. R6 removed the *dead-detector*
explanation — `mtf_aligned` fires 1153/2511 on MGC and 976/1859 on MES at 1440m, so it is alive, and
`D-MTF1` reaches no published row because all three harnesses trade the lowest timeframe of their
frame. D50 supplies a *different* explanation: a live detector reading a **degenerate confirming
series**. A detector reading a series against a lagged copy of itself fires plenty; it simply is not
measuring agreement.

**What survives.** The 60m evidence, intact — D50 aliases only requests ≥ 1440, the two MTF signals
differ on 248–314 bars at 60m, and the comparison is within-population on the same bars, so D8's
structural immunity applies. And rule 2's **second** sentence survives as written: on a
two-timeframe frame "majority" and "unanimous" are the same *statement*, which is D17, an
arithmetic fact. Note the published claim and the rule diverge here — the report's "no detectable
difference" is INVALID, while the rule derived from it is right.

**Narrower than stated, three ways.**
1. The **1440m arm is not evidence about multi-timeframe agreement at all**, and its magnitude is
   unmeasured.
2. The **240m arm tested one signal, not two** — `mtf_strongly_aligned` and `mtf_aligned` are
   identical on 1348/1348 and 1347/1347 bars there.
3. The rule **must not be applied to `mtf_not_conflicted`**, whose veto runs 62.6% → 79.6% → 99.1%
   by *frame*, not by strategy.

**Do not cite rule 2 for any of these.** Unanimity-versus-majority as an *empirical* result. Any
daily-row claim. `mtf_aligned` being a dead detector. **Omitting an alignment arm from the edge
programme** — its frames are new, so that is rule `R-11`: a claim that something "has already been
tested" must name the dimension that was varied. And "multi-timeframe agreement does not work."

**The sentence to carry instead** is R1's: *an open question here, not a settled negative.*

z = −4.09 stands, nothing is retracted, and rule 2 stays on the list. Rules 1, 3, 4, 5, 6, 7 and 8
are untouched — and rule 5 is explicitly **not** narrowed by association, because the session
window makes 15:00–16:00 ET newly load-bearing.

---

# What this session must know that this brief did not, as of 2026-09-27

Five things landed after the section above was written, and a callout session that does not know
them will be confidently wrong in a way the colour coding makes look authoritative.

## 1. The account has an absorbing state at $2,800 of drawdown, and it is the one result that clears its own threshold

`absorbing_boundary()` reproduces it from the shipped `AccountConfig` alone: at a drawdown from peak
of **$2,800** the permitted dollar risk is **$21.60** against a `min_dollar_risk` of **$25**, because
the de-risk ladder steps from ×0.50 to ×0.30. **The account is then permanently unable to place a
trade while `has_failed` stays `False`, with $2,200 of the $5,000 failure buffer never spendable.**
A dead-but-not-failed state the risk engine does not report.

**Every callout must be sized with the current drawdown in hand**, because the distance to $2,800 is
a harder constraint than any expectancy estimate. And this is the one finding in the whole programme
that clears its own deflation threshold: **every governor that shrinks position size is net
protective, |z| = 6.164 and 5.543 against `free_t` 2.2293** — because survival is a threshold on the
*path*, not on the mean. When in doubt, size smaller; that is the measured result, not caution.

## 2. The session window: 18:00 ET → 16:00 ET, nothing held across 16:00–18:00

The account owner's standing rule. Two shipped defects sit under it and both change what a callout
can promise:

- **`engine.py:470-473` closes any position entered at or after 12:30 ET on its own entry bar**
  (MGC, `_rth_minutes = 310`), because `minutes_since_open` is measured from the RTH open of the
  bar's own date and never clamped. So the shipped "exit at session close" is not that — for the
  whole afternoon, evening and overnight it is an instant flat.
- **`exit_at_session_close` is `False` on 58 of 184 MGC and 90 of 185 MNQ** generated strategies, and
  it is False on **exactly** the three `ANCHOR_*` exit models — so session control is perfectly
  confounded with target kind and there was never an independent session arm.

**Do not tell the user a position will be flat at any particular time on the strength of the shipped
engine.** The rule is expressible at 5/15/30/60/120m and at 240m (with the earliest entry at 20:00,
so a 20-hour cycle, not 22); **1440m cannot carry it at all.**

## 3. `rth_only` is `True` on every generated strategy, including MGC's, whose own profile asks for False

`profiles.py` sets `rth_only=False` for MGC with the longest rationale in the file — *"not an equity
product and it should stop being tested like one… the real drivers move it around the clock."*
**Nothing in the generation path reads that field.** It is asserted by
`tests/test_symbol_profiles.py:98` and ignored by the combinator, which imports only `groups_for`.
Measured: `rth_only` True on **184/184 MGC and 167/167 MCL** generated strategies.

Consequence for a callout: MGC RTH is **08:20–13:30**, not the equity session. MCL is 09:00–14:30.
MES/MNQ close at 16:00, so the session rule buys them nothing. A callout outside a contract's RTH is
outside everything this repo has ever measured — say so.

## 4. The data substrate has holes, and one long series is unusable

From `workspace/studies/SERIES_AUDIT.md` (all 77 series, audited 2026-09-27):

- **MGC daily is unusable unadjusted, in both stores.** Its intraday sum is **−2.0079** against a
  boundary-gap sum of **+2.9584**: buying every open and selling every close loses 87% over 14.4
  years while the price rises 158%. Large gaps run 304 up / 194 down, **p < 0.0001**, with a 3.5×
  excess in the six active COMEX gold delivery months. That is the roll.
- **`data/archive/MGC_1440m.jsonl` bars 0–383 are a different instrument** (10.145× splice at
  2012-04-27, disjoint ranges). Never read them.
- **`CL_1440m` closes at −$37.63 on 2020-04-20.** Log returns and every band are undefined there. It
  is the series someone reaches for because MCL daily is one bar; do not.
- **MES/MNQ daily are clean over 7.40 years** and are the only roll-clean long series here.
- **The bars are not contiguous.** `open[i+1] != close[i]` on 57–80% of boundaries where no time
  passes; MGC 60m mean +0.50 bp, MGC daily median +3.81 bp. The engine fills entries at the next
  bar's open, so a level computed from a close is not a transaction price. **Quote entries from the
  price you actually fetched, not from a derived close.**
- **MCL 60m is structurally thin for ~2 months** inside the 718-day span — 17 ET dates, 2026-01-12 →
  2026-03-10, carrying 1–5 bars each against ~20 normally.

## 5. Machinery that will quietly return nothing

`workspace/studies/DEFECTS.md` is now **D1–D58** plus candidates, not D1–D43. The ones that matter to
a callout: `outside_news_blackout` removes **0 of 1,093** eligible MGC bars (identity filter on a
`:00` grid); every `openinterest` condition is dead and the FILTER `oi_expanding` **vetoes every
entry**; all three `orderflow` conditions are OHLCV proxies with no delta data; every daily VWAP
strategy is a bar-shape strategy wearing a VWAP name; every daily multi-timeframe statement is a
lagged-autocorrelation test on one series. **19.0% of generated strategies carry a condition that
cannot fire, and `evaluate` is a strict AND, so that is the whole strategy's zero.** 60–82% never
fire at all.

---

# How the basis stays current — the mechanism, not a hope

Sessions in this environment **cannot see each other's memory.** What they share is the git branch
`claude/intelligent-feynman-ongyjw`. So:

1. **At the top of every callout turn**, run `git fetch origin claude/intelligent-feynman-ongyjw &&
   git merge --no-edit FETCH_HEAD` (never rebase, never force-push — another session commits here),
   then re-read this file, `workspace/roundtable/BRIEF.md` and
   `workspace/studies/SERIES_AUDIT.md`.
2. **State the basis commit on the callout.** `basis: <short sha>, <date>`. A callout whose basis sha
   is older than the branch head is a stale callout and says so.
3. **Never carry a number forward from an earlier turn in the conversation.** Re-read it. Three
   numbers in this file were retracted between sessions; the next one will be too.
4. **This file is a brief, not a result.** If it disagrees with `BRIEF.md`, `DEFECTS.md` or
   `SERIES_AUDIT.md`, those win and the disagreement gets written down here.

The research sessions bank findings to disk as they go and the parent commits and pushes, so a
finding reaches this session at its next fetch. That is the whole mechanism. It works because of the
write-as-you-go rule, and it fails silently if this session skips step 1.
