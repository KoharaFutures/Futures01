# CALL desk notes — things the parent session may need to correct

Owner: `CALL` (live paper callout desk). I own `workspace/paper/CALL/**` and nothing else.
Everything below was measured this turn, in this repository, at the basis sha named.

---

## N1 — `RiskManager.evaluate()` vetoes every callout this desk can ever make, and CALLOUT.md tells me to respect it

**basis: 1948339, 2026-09-27. Status: a genuine conflict between two instructions, not a defect.**

`CALLOUT.md` § "Risk, non-negotiable" says to "respect the risk engine's limits
(`futures_agents/risk/`)". `PAPER MODE` says the confidence line is one of exactly three words and
"almost always `DISCRETIONARY`". **Those two cannot both be satisfied through
`RiskManager.evaluate()`.** Stage 6 of that method is a hard veto wall
`[repo-verified: futures_agents/risk/manager.py:286-313]`:

| line | gate | what a DISCRETIONARY paper card can supply |
|---|---|---|
| `:287` | `proposal.confidence < cfg.min_confidence` (0.58) | nothing — the paper vocabulary is three words, not a float |
| `:292` | `proposal.reward_risk < cfg.min_reward_risk` (1.6) | satisfiable, and I will honour it |
| `:298-302` | `hist is None or hist.trades == 0` → *"no measured history for this strategy - an unmeasured edge is not an edge"* | **nothing. By construction.** |
| `:304` | `hist.trades < 40` | — unreachable, `:298` already returned |
| `:310` | `hist.expectancy_r < +0.08R` | — unreachable |

The `:298` veto is **correct** and is the engine agreeing with the programme's own central finding.
But it is unconditional here: a discretionary chart read has `historical=None` by definition, and
nothing in this repository has a measured history that clears deflation anyway (largest *t* 3.923 vs
`free_t` 5.46). So `evaluate()` returns `NO TRADE` on **every** card this desk could write, and the
only way to get a non-veto out of it is to **fabricate a `HistoricalPerformance` record** — which is
the one thing `PAPER MODE` and BRIEF.md rule 4 forbid.

**The ordering makes it worse, and this is the part worth the parent's attention.** Stage 6 returns
*before* stage 7, so the sizing path — the de-risk ladder, the drawdown budget, and the
`budget < min_dollar_risk` absorbing-state check at `:329-334` — **is never reached** for a
discretionary proposal. The engine cannot size what it has already refused. So "respect the risk
engine" read literally means the ladder never runs, and the ladder is the one thing in this
programme that clears its own threshold (|z| 6.164 / 5.543 vs `free_t` 2.2293).

**How I am resolving it until told otherwise.** I use the engine's *arithmetic* and not its
*verdict*: I compute the budget from `AccountConfig` directly (`usable_buffer` ×
`base_risk_pct_of_buffer`, capped by `max_risk_pct_of_equity` and `max_dollar_risk`, times
`derisk_multiplier`), honour `min_reward_risk` 1.6 and `min_dollar_risk` 25 as live constraints, and
record the stage-6 veto as a **standing, expected condition named on every card** rather than
something I have cleared or worked around. I do not construct a `TradeProposal` with a synthetic
`historical` field. If the parent wants the opposite — route through `evaluate()` and emit `NO TRADE`
on everything — that is a one-line change to my posture and it is the parent's call, not mine.

## N2 — the absorbing state reproduces exactly, and the cliff is one $100 step wide

Reproduced from the shipped `AccountConfig` alone, not cited
`[measured: futures_agents/risk/account.py via AccountConfig(), this turn]`:

```
   dd    equity  usable_buf    base   mult   budget   tradeable
 2600     47400      1400.0   84.00   0.50    42.00   YES
 2700     47300      1300.0   78.00   0.50    39.00   YES
 2800     47200      1200.0   72.00   0.30    21.60   NO - DEAD
 2900     47100      1100.0   66.00   0.30    19.80   NO - DEAD
```

CALLOUT.md § 1 is correct to the cent. Two things it does not say that I want on the record:

1. **The ladder fraction is taken over the *usable* buffer, not `max_total_drawdown`.**
   `5000 × (1 − 0.20) = 4000`, and `2800 / 4000 = 0.70` lands **exactly** on the `[0.70, 0.30]`
   rung. The death point is not an emergent property of a smooth decay — it is a single rung
   boundary, and it is hit dead-on. A `protected_buffer_pct` of 0.19 or 0.21 moves it.
2. **The transition is one step, not a glide.** $39 permitted at $2,700 and $21.60 at $2,800: the
   account goes from tradeable to permanently dead across $100 of drawdown, which is **less than one
   losing trade at the $240 budget available at full health.** There is no zone in which the desk
   can see itself dying. That is the practical form of the constraint, and it is why I will treat
   $2,600 of drawdown as the operational floor rather than $2,800.

## N3 — at full health the budget is $240, and that is smaller than one ATR on two of the four symbols

`[measured: futures_agents/config.py CONTRACTS, this turn]`. Budget at zero drawdown is **$240**.
Against the shipped `typical_atr_points` (these are daily figures, so the 60m constraint is looser —
the point is the ceiling, not the exact stop):

| symbol | point value | 1 ATR ≈ | 1 ATR in $ | 0.5 ATR in $ (rule 4 floor) | contracts at $240 / 1 ATR |
|---|---|---|---|---|---|
| MGC | $10 | 28.0 pt | **$280** | $140 | **0** — one contract does not fit |
| MNQ | $2 | 120 pt | **$240** | $120 | 1, exactly, with zero headroom |
| MES | $5 | 45 pt | $225 | $112.50 | 1 |
| MCL | $100 | 1.85 pt | $185 | $92.50 | 1 |

So **on a healthy account this desk is a one-contract desk**, and on MGC at a daily-ATR stop it is a
*zero*-contract desk. Any card quoting 2+ contracts is quoting an intraday stop well inside 1 ATR,
and must show the stop distance in points so that is visible rather than implied. Rule 4's ~0.5 ATR
floor and the $240 ceiling together define a narrow corridor, and on MGC they nearly close it.

## N4 — as-of confirmed, and MCL's sub-hourly substrate is two months, not two years

`[measured: data/archive/*.jsonl, this turn]`. Newest bar across every 60m series is
**`2026-09-25T16:00-04:00`**, matching CALLOUT.md exactly. But the depth is not uniform, and the
brief's "~11,300 hourly bars per symbol" does not extend to the finer frames:

- 60m and 240m: ~10,900–11,300 bars back to **2024-10-06** on all four. Deep.
- 15m / 30m / 5m: start **2026-07-29** on all four — **under two months.**
- 1m: starts 2026-09-20 — ~6.6 trading days, per BRIEF.md's R5 correction.
- `MCL_1440m`: **1 bar.** `CL_1440m` reaches 2002 and is disqualified (negative price).

Consequence for a card: a 15m or 5m read on any symbol rests on ~2 months of history, which is
**shorter than the 0.88-year published span** that BRIEF.md already shows was too short to clear
anything. Combined with rule 7 (sub-hourly is a graveyard), a sub-hourly card should say both.

## N5 — the vendor stamps a live timestamp on a stale price at the Sunday reopen, and it is invisible in the clean path

**basis: 8c8bdab, 2026-09-27. Measured this turn at 18:15 ET, 15 minutes after the Globex reopen.**

CALLOUT.md warns that the archive is not real-time. The failure at a session reopen is worse than
staleness, because it comes dressed as freshness:

```
MGC=F 5m  2026-09-27 18:00-04:00   o=h=l=c=4321.200195   volume 0
MNQ=F 5m  2026-09-27 18:00-04:00   o=h=l=c=30889.25      volume 0
MGC=F quote  lastPrice 4321.2001953125 == previousClose   regularMarketTime 18:05:10 ET
MNQ=F quote  lastPrice 30889.25        == previousClose   regularMarketTime 18:05:14 ET
```

`lastPrice == previousClose` **exactly**, on two uncorrelated contracts, with a timestamp ten minutes
old at the time of reading. That is a carry-forward, not a coincidence, and `marketState` reads
`REGULAR` on a Sunday evening. **A desk that trusts `regularMarketTime` and quotes `lastPrice` has
just quoted Friday's close as a live level** — the one error CALLOUT.md says costs money.

**Two things make this worth a note rather than a shrug.**

1. **`YahooFeed.fetch` does not protect you.** It reported `-1 forming` and dropped the 18:15 bar,
   which is correct, but it **kept** the 18:00 stub: the 15m snapshot's last row is the zero-volume
   zero-range bar. So the stub survives into the clean path and is the newest bar a caller sees.
   It was the only such bar in five days of 15m data on either symbol, so a contiguity or gap check
   will not flag it — only `volume == 0 AND high == low` will. `resolve.py` drops it, by that test,
   everywhere (rule 1 in its docstring).
2. **This is `SERIES_AUDIT.md` §5 arriving live.** The audit recorded 3.5–4.0% zero-volume bars on
   every 60m micro series and judged them "the thin overnight hour, not a hole", which was right for
   history. At a reopen the same shape is a *placeholder*, and the audit's benign reading would wave
   it through. The discriminator is the conjunction with `h == l`: on MGC daily, 334 of 355
   zero-volume bars were also rangeless, which the audit itself noted and called synthetic. That is
   the same object.

**Consequence I am adopting:** no entry is ever quoted from a bar or quote failing
`volume > 0 or high != low`, and the newest bar I hold is reported as the newest bar that *passes*
it. Both symbols got `NO TRADE` this turn on exactly this ground.

## N6 — five of the nine shipped exit models cannot be executed at this account size, and three more only at rule 4's stop floor

Falls straight out of N3's $240 budget and is worth stating because `STRATEGY_CATALOGUE.md` §3
presents all nine as the exit dimension the programme searched.

The tightest stop BRIEF.md rule 4 permits is ~0.5 ATR. Measured this turn: ATR14(60m) is **16.45 on
MGC** and **95.71 on MNQ**, so rule 4's floor is $82/contract on MGC and $96/contract on MNQ.

| exit models | scale-out | contracts for an exact integer split | risk at rule 4's floor | vs $240 budget |
|---|---|---|---|---|
| **0, 2, 4, 7, 8** (five) | three tiers — .5/.3/.2 or .4/.3/.3 | **10** | MGC $820 · MNQ $960 | **4×. Also above `max_dollar_risk` $500.** |
| — same, rounded to 5 lots | 2/1.5/1.5 is not integer | 5 | MGC $410 · MNQ $480 | **~2×. Unreachable.** |
| **1, 5, 6** (three) | two tiers — .6/.4 or .5/.5 | 2 | MGC $164 · MNQ $192 | fits, but **only at the stop floor** |
| **3** (one) | single target | 1 | MGC $82 · MNQ $96 | fits — and `D8` records it cannot trade |

**So at a $240 full-health budget, the three-tier exit models are structurally unreachable on both
symbols, the two-tier ones survive only with a stop at or very near rule 4's minimum, and the one
single-target model is the one D8 says cannot trade.** This is the same class as `D49`
(`FIXED_TICKS` and `RANGE` have zero carriers) and `D19` (session control confounded with target
kind): a dimension the programme treats as searched, which this account cannot reach. It is also
why `CALL-0001` carries one target and not three — not a simplification, an arithmetic limit.

Worth the manager's attention as a D-candidate: **the exit dimension was searched at a position size
the shipped `AccountConfig` never permits.** I have not measured whether the ~3M population's
expectancies depend on the scale-outs, so I am not claiming the results are wrong — only that their
exits are not executable here.

## N5a — the stub bar's price was wrong by MORE THAN A FULL POSITION'S RISK BUDGET. Measured, same bar, two fetches.

**basis: c1538d7, 2026-09-27. This is N5 confirmed in production, not against synthetic bars.**

The 5-minute loop's first live check caught the same bar before and after the vendor filled it in.
`2026-09-27T18:00:00-04:00`, 15m frame, fetched at 18:15Z and again at 22:52Z:

| symbol | 18:15Z — the stub | 22:52Z — the real bar | error in the stub's price |
|---|---|---|---|
| **MGC** | `o=h=l=c=4321.20`, **v=0** | `o 4309.00  h 4310.30  l 4301.20  c 4301.50`, **v 679** | **−12.20 pts = $122.00/contract** |
| **MNQ** | `o=h=l=c=30889.25`, **v=0** | `o 30844.50  h 30853.00  l 30815.25  c 30820.75`, **v 4328** | **−44.75 pts = $89.50/contract** |

**Read the MGC row against this account's own sizing.** The permitted risk at zero drawdown is
**$240** and `CALL-0001` was sized at **$120**. The stub's price was wrong by **$122 per contract**
— *more than the entire risk budget of the position it would have been used to open*, and more than
half of everything the account is permitted to risk on one trade at full health. A stop placed
relative to that level would have been not merely mis-set but **inverted in meaning**: the "entry"
was 12.20 points above where the session actually opened, so a long taken there began already
beyond a full stop's distance from its own premise.

MNQ's $89.50 is 75% of that position's risk budget.

**Three things this settles.**

1. **The stub is not a rounding artefact or a quiet bar — it is a fabricated price.** Both stubs
   carried the previous close exactly, and in both cases the session's real open was *lower*, on
   the same side, by a material amount. The vendor was not approximating; it was filling a hole
   with the only number it had.
2. **`volume == 0 AND high == low` is a sufficient guard, and nothing weaker is.** The stub had a
   plausible price, a plausible timestamp, and sat in correct chronological order in a series with
   no duplicate and no gap — `SERIES_AUDIT.md`'s clock and contiguity checks pass it, and 77 of 77
   series were clean on all four of those tests. Only the conjunction catches it.
3. **The snapshot-per-fetch design earned its keep on its first day.** Because `resolve.py` merges
   every snapshot and lets the newest fetch win per timestamp, the stub was *replaced* rather than
   frozen into the record, and the before/after comparison above is only possible because the
   earlier fetch was kept rather than overwritten. Had this desk written one rolling file, the
   evidence would have been destroyed by the very fetch that corrected it.

**The quote endpoint was wrong in the same direction and by the same mechanism** — it returned
`lastPrice == previousClose` on both symbols at a live 18:05 ET stamp, i.e. it too was serving
4321.20 and 30889.25 while the real session was trading 4309 and 30844.50.

## N7 — measured feed lag: ~13 minutes at the 5m frame, ~23 at 15m. The check interval is now faster than the data.

**basis: c1538d7, first live check, 2026-09-27 18:52 ET.** Recorded per-check to
`workspace/paper/CALL/feed_lag.jsonl`.

```
MGC/MNQ  5m   newest real bar 2026-09-27T18:40-04:00   lag 12.9 min
MGC/MNQ 15m   newest real bar 2026-09-27T18:30-04:00   lag 22.9 min
```

`CALLOUT.md` says only that the data "is not real-time". This is the number: **at the 5-minute
frame this vendor is ~13 minutes behind**, which is roughly one bar of delay plus the bar's own
width. The 15m figure is the same delay expressed at a coarser grain.

**Consequence for the 5-minute cadence the owner asked for.** A check every 5 minutes against a
feed that advances every ~13 means roughly **three of every five checks will see no new bar**. That
is not an argument against the cadence — a 5m bar does complete every 5 minutes, so nothing is
*missed*, and the loop cost is small and bounded. It is an argument about what the cadence can
deliver: **it cannot reduce reaction time below ~13 minutes**, because that floor is set by the
vendor and not by how often this desk looks. A stop-entry trigger will be detected 13–18 minutes
after it actually printed, whatever the interval.

So the honest recommendation, once — the owner has asked for 5 minutes and it is their call:
**the interval that matches this feed is 10–15 minutes**, and the accumulating `feed_lag.jsonl`
will say whether 12.9 minutes holds during RTH liquidity or is worse on a Sunday reopen. I will
report the distribution rather than re-raise the point.

## N8 — MNQ's bias flipped unanimously bearish against a pending LONG, and I am deliberately not touching the plan

**basis: f549f35, 2026-09-27 19:02 ET.** `chart.py` reads MNQ 15m **BEARISH 0-3** — trend (close
30789.25 below a falling EMA20 30864.05), structure (swing highs 30935.25→30922.50 lower, lows
30880.50→30797.25 lower) and location (35.7% of range) all bearish. `CALL-0001` is a **LONG**.

The thesis it was pre-registered on — uptrend, pullback complete, Friday's higher high and higher
low, so a break of 30998.50 is continuation — **has been contradicted** by a Sunday reopen that
gapped down and is now printing lower highs *and* lower lows on the 15m.

**The plan stays exactly as written. Unmodified, unwidened, untightened.**

The reason is not optimism, it is that **editing a pre-registered hypothesis after watching the price
move destroys the only statistical advantage it had.** The whole point of writing 30998.50 down
before the session opened is that it faces `free_t` 1.177 instead of 5.46. A level revised in light
of what price then did is not a pre-registered hypothesis at all — it is a searched one with a
sample size of one and a threshold four t-units higher, wearing the label of the thing it stopped
being. Adjusting it "because conditions changed" is the exact mechanism by which this programme's
2,975,629-candidate search became unreportable, reproduced in miniature.

**And the plan is self-invalidating anyway, which is why no action is needed.** It is a stop-entry
199 points *above* the market. It cannot fire unless MNQ rallies 199 points — and a rally of that
size would substantially rebuild the bullish condition the thesis requires. The trigger is
structurally incapable of filling into the tape that currently invalidates it.

**The residual risk, named rather than fixed:** if MNQ rallies 199 points *sharply*, the trigger
fires on a V-recovery rather than on the continuation-from-a-held-pullback I actually described.
Those are different setups and a bare stop-entry cannot tell them apart. That is a genuine weakness
of the plan as written — **and the honest response is to note it now and write a better entry
condition into the NEXT pre-registration, not to patch this one mid-flight.** The Monday 16:00
expiry bounds the exposure to one session either way.

## N9 — the three-component bias is unstable on a thin tape: two unanimous readings broke within ~30 minutes each

**basis: 5b94361, 2026-09-27 20:03 ET.** Recorded on the second occurrence, because one was an
anecdote and two is a property of the tool.

| symbol | unanimous at | broken by | what moved |
|---|---|---|---|
| MNQ | 19:02 ET, `0-3` | 19:18 ET, `0-2` | location crossed 40% into MIXED on ~20 pts of drift |
| MGC | 19:32 ET, `0-3` | 20:03 ET, `0-2` | structure went MIXED on a **higher** swing low, 4291.80 -> 4293.20 |

Both breaks came from a single component crossing a threshold on very little price movement, on
Sunday-reopen liquidity. Tonight MNQ also went `0-2` -> `0-1` in the same half hour, again on a
higher swing low.

**What this does and does not mean.**

- It does **not** invalidate the panel. It is a 40-bar description and it is describing a tape that
  is genuinely going sideways after a gap down. Unanimity breaking is the honest output.
- It **does** mean a unanimous reading is not a durable state and must never be treated as one.
  `chart.py` already prints the tally and the rule-1 reminder on every render precisely so a `0-3`
  cannot be quoted later as though it still held.
- It is the concrete argument for the fast-check rule against re-deriving the read every five
  minutes. A desk that re-decided on each render would have taken a bearish MGC position at 19:32
  and been looking at a broken premise by 20:03, having changed nothing about the market.

**Consequence for `CALL-0002`.** The unanimity that justified it has already weakened, 31 minutes
after it was written. The plan is **not** modified — same reasoning as N8: editing a pre-registered
level after watching price move destroys the threshold it was written for. And the RTH gate means
it cannot fire on this tape at all; it needs Monday 08:20-13:30 ET, by which time the read will
have been re-formed on liquid bars at the hourly full check. **This is the gate earning its keep
twice in one evening**: first refusing the trigger on thin liquidity, now refusing to act on a bias
that will not sit still.

## N10 — CALL-0002's trigger was touched 40 minutes after it was written, the RTH gate refused it, and the outcome is UNDETERMINED

**basis: 091e471, 2026-09-27 20:12 ET.** The gate's first live test. Recording it now, before the
result is known, so the record cannot be written to flatter the decision afterwards.

**What happened.** MGC's 5-minute bar at `2026-09-27T20:00-04:00` printed:

```
o 4294.40   h 4295.20   l 4288.30   c 4289.20   v 1635
```

The low is **0.80 points below the 4289.10 trigger**, and the close came straight back **above** it.
On the plan's own frame, 15m, the break has not registered at all — the newest completed 15m bar is
`19:45` with a low of 4293.40.

**The gate refused the fill, correctly and by construction.** `CALL-0002`'s window opens
`2026-09-28T08:20-04:00`; every bar that traded below the trigger is dated `2026-09-27`, before it.
`resolve.py` left the plan `PENDING` with no intervention.

**Three things worth separating, because they are easy to collapse into one.**

1. **The plan's named weakness materialised almost immediately.** Its `invalidation` field said
   *"4289.10 has now HELD TWICE, so it is support and a break of it may be a false break."* Forty
   minutes later the level was poked by 0.80 points and reclaimed on the same bar. That is evidence
   the weakness was **correctly identified**, not evidence the plan is wrong.
2. **The gate did its job as specified.** It exists to refuse fills on Sunday-reopen liquidity, and
   it refused one. That is the mechanism working, which is a different claim from the mechanism
   being *right*.
3. **Whether refusing was profitable is NOT KNOWN and must not be asserted.** A fill would have
   been near 4289.00; price is now 4289.20–4294.50, so as of this instant a hypothetical short
   would be roughly flat to slightly offside. It could be a saved loss or a missed winner, and the
   honest answer is that **neither is established**. Claiming the gate "saved" anything here would
   be the same error as writing an outcome before a trade resolves.

**The cost of the gate, restated because it is now concrete rather than hypothetical.** A stop-entry
below 4289.10 needs price to **cross** the level inside the window. If MGC spends the overnight
session below 4289.10 and opens Monday beneath it, `CALL-0002` never fills and expires as `NO_FILL`
— the move happens without the desk. That was accepted when the gate was written and it is not
being retro-fitted now.

**Also this check: MNQ's headline went CONFLICTED (1-1)** — its location component crossed to BULL
at 61.5% of range. First non-bearish headline of the evening, and a third instance of N9's finding
that these readings do not sit still.

## N11 — multi-family confluence, built to surface DISAGREEMENT, and it immediately found four families against CALL-0001

**basis: 5808aa1, 2026-09-27 20:40 ET.** The account owner asked for other strategies used as
confluence. Built as `confluence.py`, but **not** as a confluence score, because a score would
invert two of the programme's eight settled findings:

- **Rule 1**: going from 2 signals to 4 cuts trade count 35% with no expectancy gain. **More
  confluence is a worse trade**, not a safer one.
- **Rule 2**: *requiring* multi-timeframe alignment measured detectably **worse** than requiring
  none, z = −4.09.

So counting agreeing families and calling the total "confidence" would be reading both results
backwards. What a multi-family read is genuinely good for is the opposite: **naming the families
that contradict the setup**, and naming the ones never tested on that symbol. Every verdict is
computed from the bars; a family this desk cannot evaluate from OHLCV says `N/A` with a reason
rather than quietly counting as agreement.

**It paid immediately, and the finding is unflattering to my own call.**

| | CALL-0001 MNQ LONG | CALL-0002 MGC SHORT |
|---|---|---|
| AGREE | MEAN_REVERSION*, MULTI_TIMEFRAME | TREND, BREAKOUT*, LIQUIDITY*, MULTI_TIMEFRAME |
| **AGAINST** | **TREND, MOMENTUM, BREAKOUT, LIQUIDITY** | **MOMENTUM*, MEAN_REVERSION** |

`*` = never generated for that symbol, so its verdict rests on no evidence at all.

**On `CALL-0001`, four of the six evaluable families oppose the trade**, and all four are families
MNQ's profile *does* generate. Its two supporters are MEAN_REVERSION — which was never tested on
MNQ and is only "agreeing" in the weak sense that price is not extended — and MULTI_TIMEFRAME,
which rule 2 explicitly says is not a virtue. **Discount both and the long has zero support and
four named opponents.** That is a materially worse picture than the card showed an hour ago, and it
did not come from a new opinion; it came from asking the other twelve families.

**On `CALL-0002`, restrict to families actually tested on MGC and the score is 1–1**: TREND agrees,
MEAN_REVERSION disagrees (−1.53 sigma, extended — it would fade this exact break), with
MULTI_TIMEFRAME rule-2-discounted. Two of its four supporters, BREAKOUT and LIQUIDITY, were never
generated for MGC. And **MOMENTUM is against on both symbols for the same reason**: relative volume
0.43× and 0.57× of median. Neither break has participation.

**Both plans stay unmodified.** This is information about pre-registered hypotheses, not licence to
edit them (N8). What it does change is what the cards say: the opposition is now on their face, in
red, rather than living in a single confident STRATEGY line.

## N12 — the RTH gate cost a full winner on its first real test. Recording it against myself.

**basis: 9f1f609, 2026-09-27 20:45 ET.** N10 said the honest answer to "was refusing profitable?"
was *not known*. It is known now, for this instance, and it goes against the decision I defended
twice.

**What happened.** MGC broke down through `CALL-0002`'s trigger and ran straight to target:

```
20:20  h4290.20  l4286.50  c4287.10  v  849
20:25  h4288.80  l4283.70  c4283.70  v 1157
20:30  h4284.70  l4262.30  c4270.00  v 9074   <-- THROUGH TP1 4273.00
20:35  h4272.30  l4267.60  c4272.30  v    0
```

Session low **4262.30**. TP1 was 4273.00. **The stop at 4299.00 was never touched** — the high since
the trigger is 4291.90.

**The trade the gate refused would have been a clean win:** fill 4289.00, TP1 4273.00, +16.00 pts =
$160.00 gross, less $2.44 costs = **+$157.56 net, +1.58R**, resolved inside 15 minutes with no
adverse excursion past the entry.

**This is not journalled and never will be.** `journal.jsonl` records trades that happened;
`CALL-0002` did not fill and will expire `NO_FILL`, 0.0R. Writing +1.58R anywhere in the record
would be fabrication of exactly the kind `resolve.py` exists to prevent. The number above is an
argument, not a result.

**What it does and does not establish.**

- It **does** establish that the gate has a real, measured cost, and that the cost is not small: one
  full target, 1.58R, on the very first setup it governed.
- It **does** vindicate the *read*. Every element of the thesis played out — the break of
  twice-tested support, the trend continuation, the target sitting at the 30-day low. The
  pre-registered levels were right.
- It does **not** establish that the gate is wrong. One favourable outcome on a thin Sunday tape is
  a sample of one, and the gate exists because fills there are unreliable, not because moves there
  are unprofitable. N9 recorded the bias flipping four times in ninety minutes on this same tape;
  the reason to distrust it has not gone away because one break ran.
- And the one thing that looked most damning at 20:40 — MOMENTUM AGAINST on 0.97× median volume —
  **was wrong about what came next**: the 20:30 breakdown bar carried **9,074 contracts, roughly
  8× the preceding bars.** The participation arrived exactly when the level broke. That is a real
  limitation of evaluating momentum on the bar before the move.

**No change to either plan, and no change to the gate, on one observation.** What this earns is a
counter that gets carried: **gate refusals: 1, of which would-have-won: 1.** If that column keeps
reading this way over a meaningful number of setups, the gate is costing more than it protects and
the RTH restriction should be re-argued from the tally — not from tonight.

## N13 — no new call tonight, and the reason is that the setup is late, not that nothing is happening

**basis: ce6b0aa, 2026-09-27 22:03 ET.** The owner asked the desk to keep calling. This is the
record of a call **declined**, because a record that only contains the trades I liked is a record
of my memory, not my process.

**What the tape is doing.** MGC is at 4245.20, **−76.00 points from Friday's close** ($760 a
contract), bearish on all five frames it may carry a bias on, three of them unanimous. That is a
strong, clean downtrend.

**Why I am not shorting it.** RSI14 is **9.4** and price is **−1.74 sigma** from its 20-bar mean.
MEAN_REVERSION — one of the six families MGC's profile actually generates, unlike BREAKOUT or
LIQUIDITY — reads **AGAINST**, and it is right to: entering a short 76 points into a move, at an
RSI under 10, is paying for the part of the trend that has already happened. The five agreeing
families do not fix that, because **rule 1 says agreement is not confidence**, and three of the
five (BREAKOUT, LIQUIDITY, MOMENTUM) were never generated for MGC at all.

**Why I am not trading MNQ either.** Its frames are in open conflict: 1m/5m/15m unanimously
BEARISH against 4h/DAILY unanimously BULLISH. Under rule 1 that is a reason **not** to trade, not
a weaker reason to pick a side.

**`CALL-0002` is stranded and will almost certainly expire `NO_FILL`.** Its 4289.10 stop-entry sits
**43.90 points above** the market and can only fill inside Monday 08:20–13:30 ET. That is the RTH
gate's cost, already recorded in N12, now fully realised. I am **not** editing it (N8) and not
replacing it with a chase.

**What would produce a call.** A retest short — a bounce back into the broken 4289.10 shelf during
Monday's RTH, shorted at resistance with the trend rather than 76 points into it. That is a
TREND-family setup, and TREND **is** one of MGC's six generated families, so it is better grounded
than `CALL-0002` was. It needs a limit entry, which `resolve.py` does not yet support — it only
does stop-entries. **I am not building that speculatively at 22:00 on a Sunday**; it gets built
when a bounce actually forms, at a full check, on liquid bars.

## N14 — the reversal detector was defining "reversal" in a way that could almost never fire

**basis: ce6b0aa.** Found by watching it decline a call it should have been able to consider.

MNQ's 15m went `BULLISH → CONFLICTED → BEARISH`. The detector reported *"prior headline was
CONFLICTED, so this is a resolution, not a reversal"* — because it compared against the
**immediately prior differing** headline, which was the neutral state in the middle.

That is wrong, and structurally so: **on this tape a sign change almost always passes through
CONFLICTED on its way across**, so requiring the prior headline to be directional-and-adjacent
would have made nearly every genuine reversal unreportable. A reversal is a change of **sign**, and
CONFLICTED has no sign. Fixed: `prior` now skips CONFLICTED and finds the last **directional**
headline.

**It still declines, and now for an honest reason.** `bias_history.jsonl` only began at 21:14 ET,
and MNQ's recorded 15m sequence is ten CONFLICTED readings followed by two BEARISH — **the earlier
BULLISH state was never recorded**, so there is genuinely nothing on file to reverse *from*. The
detector is currently limited by its own history depth, not by its logic, and it will start doing
real work once a few hours of directional readings exist. Worth stating plainly rather than
letting a "no call" look like a considered verdict when it is partly an empty file.

## N15 — the reversal detector fired for the first time, and I am declining to trade it, because the trigger it handed me is lower than it was an hour ago

At 22:55 ET `reversal_setup("MNQ")` returned `qualifies: true` — the first
time it has ever done so since N14 rebuilt it. The structure is real:

```
sigma       -2.12          extended, past the 1.5 threshold
htf_support 4h, DAILY, WEEKLY    three frames bullish, needs two
trigger     30735.25       reclaim of the 40-bar swing high
climax_x    0.59           NO capitulation volume - a drift, not a flush
last        30701.75
```

The obvious move is to register it. I am not going to, and the reason is
worth writing down because it will recur every single time this detector
fires during a trend.

**The trigger is computed from the 40-bar swing high, and that high decays
as price falls.** CALL-0003 was pre-registered at 22:15-ish with a reclaim
trigger of **30767.25**. Forty minutes later the same detector, on the same
logic, offers **30735.25** — 32 points lower. Nothing improved. Price fell,
the window slid, and the level the detector calls "the reclaim" slid with
it. If I write a new plan at 30735.25 I have not found a better entry; I
have moved the goalposts 32 points toward the ball and then congratulated
myself on the shorter kick. That is precisely what N8's pre-registration
discipline exists to forbid, and it is more seductive here than in the
obvious case, because the number came out of a function rather than out of
my own wishful thinking. A mechanical source does not launder it.

**Second reason, independent of the first: correlation.** CALL-0001 (>30998.50,
$120) and CALL-0003 (>30767.25, $104) are both MNQ LONG stop-entries. A
third at 30735.25 would make three plans that all fill on one upward move.
Any rally big enough to trigger the top one has already triggered the other
two, so the combined position is $344 of risk against a $240 permitted
budget at $0 drawdown — the whole allowance, on one direction, on one
thesis, discovered by accident rather than chosen.

**Third, the detector itself is telling me what is missing.** `climax_x` is
0.59: volume on the low is *below* average. The setup passes on structure
and location and fails on participation. A drift into support is the version
of this pattern that keeps drifting.

So CALL-0003 **is** the reversal call. It was written before this leg
extended, it is not RTH-gated, and it needs 65.5 points of reclaim before
02:00 ET or it expires NO_FILL at 0.0R. That expiry is the honest outcome
and I will take it rather than rescue it with a cheaper trigger.

### A separate and more uncomfortable observation about CALL-0004

MGC printed **4237.80** at 22:45. CALL-0004's **TP3 is 4240.00**. The entire
move that plan was designed to capture — all three targets, the full 4.0R —
has now happened, and the plan captured none of it, because it is a SELL
LIMIT at 4287.60 that required a 50% retracement *first*. Price never
retraced; it just went.

This is the exact mirror of N10/N12, where a stop entry was too reactive and
got filled at the worst price. A limit entry solves being late by refusing
to participate at all. Both failures are real, they point in opposite
directions, and the plain reading is that neither trigger style is the
problem — the problem is that this desk has no measured edge telling it
*which* to use in *which* regime, so it is guessing, and each guess fails
in its own characteristic way. Registering more plans does not fix that.

## N16 — asked "MGC buy or sell right now at 4235", and the first honest answer is that 4235 is not a price you can trade

23:10 ET. The owner asked for a decision at 4235. Before any opinion, the
arithmetic:

```
22:50  o 4237.30  h 4239.20  l 4233.30  c 4234.70  v 2109
22:55  o 4234.70  h 4235.10  l 4227.30  c 4230.10  v 3090   <- high 4235.10
23:00  o 4230.10  h 4231.00  l 4228.20  c 4229.00  v    0   <- ZERO volume
```

**4235 traded, was rejected, and is now above the market.** The 22:55 bar
tagged 4235.10 and closed 4.90 lower at the 40-bar low of 4227.30. So "buy
or sell at 4235" is not a decision about the current price at all — it is a
sell-LIMIT 5.10 above the market, or a buy-STOP 5.10 above it. Answering
"sell, we're in a downtrend" without saying that would let the owner believe
he could get short at 4235 on a touch, when getting there requires a 1.0x
ATR(5m) rally first. Feed lag is 10.3 minutes, so even 4230.10 is ten
minutes old.

**Flagging the 23:00 bar: volume 0, range 2.80.** The stub guard is
`volume > 0 OR high != low`, so this bar passes — h 4231.00 != l 4228.20 —
and its 4229.00 close is what `chart.py` and `regime.py` are reading. But a
gold bar with a 2.80 range and *no* volume is not a bar anyone traded. This
is a shape N5 did not cover: N5's stub was `v==0 AND h==l`, the flat
placeholder. This one is `v==0 AND h!=l`. I do not yet know whether the
vendor is interpolating, or whether volume simply lags price on the forming
bar. **Every number I quote tonight therefore uses 22:55 (c 4230.10) as the
last bar with real participation**, and 4229.00 is labelled provisional.
Not changing the guard on one observation — logging it and watching whether
volume backfills on the next fetch.

### The read, and why it is NO TRADE on both sides

```
confluence at 4235   SHORT  5 AGREE / 1 AGAINST      LONG  1 AGREE / 5 AGAINST
frames               1m 0-3  5m 0-2  15m 0-3  60m 0-3  4h 0-2  (daily/weekly NOT ELIGIBLE)
RSI14                7.9
sigma                -1.82
climax_x             1.85    "flush"  <- volume 3090 on the 22:55 low
40-bar low           4227.30 on all of 5m / 15m / 60m
ATR14                4.93 (5m)  11.01 (15m)  19.77 (60m)
```

**Against selling.** Confluence is 5-1 for short and in this repository that
is an argument *against* the trade, not for it. Rule 1 was measured here:
two signals plus one filter is the ceiling, and beyond it more agreement is
worse, not better. Rule 2 puts MTF alignment at **z = -4.09** — alignment is
a negative coefficient. So "everything is bearish" is the single most
over-subscribed reason on this desk, and it is pointing at a sell-limit
5.10 above a 40-bar low, into RSI 7.9, on the bar that printed 1.85x median
volume. That is selling the capitulation candle. CALL-0004 is also already
a live MGC SHORT; a second one is one position described twice.

**Against buying.** The long is the more interesting side, and it is the one
that got *better* in the last twenty minutes: N15 recorded MNQ's setup
failing on participation at climax 0.59x, and MGC has now printed **1.85x —
a real flush.** RSI 7.9 and -1.82 sigma are genuine exhaustion. But
`reversal_setup("MGC")` returns `qualifies: false` for one reason:
**0 higher timeframes bullish, needs 2.**

And that veto is structural, not marginal. MGC's daily and weekly are
`NOT ELIGIBLE` — the roll audit fails at p<0.0001 (gap sum +2.9584 against
intraday -2.0079). So MGC has exactly **two** HTF frames it is allowed to
carry a bias on, 4h and 60m, and both are bearish. **MGC cannot satisfy a
"two higher timeframes agree" test tonight no matter what price does**, because
the data that would have to agree has been disqualified. The correct
response to a test that cannot be passed is to notice that and decline, not
to quietly lower it to one frame because the flush looks good. That is the
same failure as N15's sliding trigger, wearing better clothes.

So: **NO TRADE at 4235, both directions.** Not a hedge — the two vetoes are
different and each is sufficient on its own. The short is forbidden by what
this repo measured about confluence and by chasing a 40-bar low; the long is
forbidden by an HTF test MGC is structurally unable to pass. No new
pre-registration, and no edit to CALL-0004.

## N17 — the rolling reference frame decays toward price, and it has now broken BOTH halves of the reversal test

N15 declined MNQ's first qualifying reversal setup because its trigger had
slid 32 points in forty minutes. Two checks later there is a third reading,
and the slide is not noise — it is monotone and it tracks price almost
point for point:

```
time    price ref   reversal_setup trigger   slide
22:15   ~30800      30767.25   (CALL-0003, pre-registered)    —
22:55    30701.75   30735.25                                -32.00
23:58    30669.25   30704.75                                -30.50
                                             total          -62.50
```

Price fell ~131 points over that span; the "reclaim" level the detector asks
for fell 62.50. The trigger is derived from the 40-bar swing high, and in a
one-way market the 40-bar window keeps dropping its highest bars off the
back. **A reclaim level computed from a trailing window is not a fixed
obstacle — it descends to meet the market.** Anyone who re-registers on each
new reading is being handed a progressively cheaper entry precisely because
the trade is going progressively worse, which is the exact inversion of what
a threshold is for.

### The same pathology has now eaten the OTHER condition, on MGC

MGC's extension reading over the same window:

```
23:10   sigma -1.82   qualifies on extension, fails on HTF support
23:28   sigma -1.82
23:58   sigma -1.45   FAILS on extension too — "needs |1.5|"
```

MGC fell ~4 points between the second and third reading and its sigma got
*less* extreme. Nothing mean-reverted. The 20-bar mean walked down to where
price already was. `reasons` at 23:58 now lists **both** failures:

```
"only -1.45 sigma from the 20-bar mean, needs |1.5|"
"only 0 higher timeframe(s) bullish (none), needs 2"
```

**This is the general defect, and it is mine, not the vendor's.** Every
condition in `reversal_setup` is measured against a trailing window: the
extension against a 20-bar mean, the reclaim against a 40-bar high, the
climax against a rolling median volume. In a sustained trend all three
references migrate toward price. So the detector's sensitivity *falls* as
the move it is meant to catch gets larger, and a long enough one-way move
will eventually read as unremarkable on all three axes. That is the opposite
of the intended behaviour and it explains something I had been reading as
bad luck: the reason nothing has qualified cleanly tonight is partly that
the instrument keeps re-zeroing itself.

I am not fixing it at 00:00 on a live loop with four plans pending — a
reversal detector rewritten while watching a specific move is a
post-hoc-fitted detector, which is worth less than a broken one. Recording
the mechanism and the three measurements. The fix belongs in a full check and
must be specified before the next fetch: candidate is to anchor the
references to a **fixed** pivot (the session high, or the high at the moment
the down-leg was first identified) rather than a trailing window, and then
to check whether an anchored version would have fired anywhere in the
archive at a rate better than a random-level control — which rule 8 already
demands, since this repository measured FVG and order-block fill rates as
reproducible by random zones.

Meanwhile CALL-0003 stands at 30767.25, unmoved and 98 points out of reach,
expiring 02:00 ET. It will journal NO_FILL at 0.0R. That is the honest
outcome and it is *also* the cleanest possible illustration of this note: the
pre-registered number is the only one in the whole apparatus that did not
drift.

### Operational, and against myself

I told the owner at 23:28 that a 5-minute loop was live under cron job
`7a85b979`. At 23:58 the job list was **empty** and no check had fired in the
intervening thirty minutes. These cron jobs are explicitly session-only and
in-memory, and they are not surviving between turns in this environment. So
the "every 5 minutes" cadence is **not** self-sustaining, and I should not
have reported it as live without saying that. What is actually durable is the
hourly Routine `trig_01NZGwNRd8mftXdxyLvuVpdD` (next 00:52 ET), which has
survived every turn. The honest statement to the owner is: checks happen when
he prompts, plus hourly on the Routine.

## N18 — the vendor served a response three hours stale, the delta design absorbed it without loss, and N16's open question is answered

00:04 ET. `fetch.py` reported something I have not seen before:

```
MGC 5m newest 2026-09-27T21:05:00-04:00  lag=179.2m  new=0 revised=2
MNQ 5m newest 2026-09-27T20:55:00-04:00  lag=189.2m  new=0 revised=2
```

The newest real bar went **backwards by nearly three hours**. The 23:58 check
had 23:45 with lag 13.6m; six minutes later the vendor's response topped out
at 21:05. This is not a stub-bar problem — it is a truncated response window.

**Nothing was lost, and the reason is the delta design.** Checked directly:

```
stored('MGC',5)  886 keys, newest 2026-09-27T23:45:00-04:00
  23:25  o 4228.60 h 4230.30 l 4227.40 c 4228.90 v  945
  23:30  o 4228.90 h 4231.30 l 4224.20 c 4225.60 v 2094
  ...
  23:45  o 4226.20 h 4227.40 l 4224.10 c 4225.60 v  658
```

All present, all with real volume, no stubs. The 00:04 delta file contains
exactly two lines — a 09-23 placeholder and the 21:05 bar — because the
response **did not contain** the 22:00-23:45 timestamps at all, so there was
nothing to overwrite them with. A full-series snapshot would have written a
series ending at 21:05, and "latest fetch wins per timestamp" would then have
been fed a file whose *absence* of later bars is indistinguishable from
nothing-to-say. The delta records only what the response actually asserted.

That is a property I did not design for and should record honestly: the
delta change was justified on disk cost (105 bytes against 88,161, an ~840x
reduction) and on being better evidence of what changed. **Robustness to a
truncated vendor window was an accident of that design, not a reason for
it.** It is still the property that saved 21 bars of tonight's move.

**What this means for the read.** Every number in this check is stamped
**23:45**, which is 19 minutes old, because that is genuinely the newest bar
this desk holds. `chart.py` and `regime.py` read the merged store, so their
output is valid — but it is not 00:04 data and I am not going to describe it
as current. Counting this as **one degraded fetch**, not a failure: it
returned data and the store is intact. Two more consecutive and the stop
condition applies.

### N16's open question is answered: volume backfills

At 23:10 I flagged the 23:00 MGC bar as `v==0 AND h!=l` — a shape the N5 stub
guard (`v==0 AND h==l`) does not catch — and said I would watch whether volume
backfilled rather than change the guard on one observation. It backfilled:

```
23:10 fetch   23:00  o 4230.10 h 4231.00 l 4228.20 c 4229.00 v    0
00:04 store   23:00  o 4230.10 h 4234.60 l 4228.20 c 4232.50 v 1899
```

So `v==0 AND h!=l` is **the forming bar**, where this vendor publishes price
before volume — not interpolation, and not a stale-price stub. The guard is
correct as written and needs no change. Two consequences worth keeping:

1. The close on such a bar is provisional and the high is incomplete — 4231.00
   became 4234.60, a 3.60 extension upward. `resolve.py` resolves stops and
   targets against exactly those highs and lows, so **a trigger or stop inside
   that range would have been missed on the first read and seen on the
   second.** Quoting the last bar with real volume, as N16 did, was the right
   call and should be the standing habit rather than a one-off.
2. Restraint was right. Had I "fixed" the guard at 23:10 to reject
   `v==0 AND h!=l`, I would have taught it to throw away every forming bar —
   which is the one bar a live desk most needs — on the basis of a single
   observation I had not yet explained.

## N19 — N18 was wrong about the scope: the 5m endpoint is truncated, the 1m endpoint is live. It is a per-frame failure, not a feed outage.

00:09 ET, second consecutive degraded fetch:

```
MGC 5m newest 2026-09-27T21:05:00-04:00  lag=184.0m  new=0 revised=1
MNQ 5m newest 2026-09-27T20:55:00-04:00  lag=194.0m  new=0 revised=0
snapshots written: MGC 1m (+4 new, 2 revised), ... MNQ 1m (+4 new, 2 revised)
```

The line I should have read at 00:04 and did not: **the 1m frames took new
bars on both symbols while 5m took none.** Measured per frame just now:

```
MGC   1m newest_real 23:58  lag 11.2m      MNQ   1m newest_real 23:58  lag 11.2m
MGC   5m newest_real 23:45  lag 24.2m      MNQ   5m newest_real 23:45  lag 24.2m
MGC  15m newest_real 23:30  lag 39.2m      MNQ  15m newest_real 23:30  lag 39.2m
```

N18 said "the vendor served a response three hours stale" and treated it as
one thing. It is not one thing. **The 1m endpoint is healthy at 12.4 minutes,
which is the normal lag for this vendor; the 5m and 15m endpoints are serving
a truncated window.** Same vendor, same request cycle, different frames,
different health. Correcting the record because the wrong version has an
operational consequence: under N18's reading there is no current price and the
desk is blind, and under the correct reading the 1m frame gives a usable one.

Newest 1m bars **with real volume** (the N18 habit, applied):

```
MGC  23:57  o 4231.10 h 4231.30 l 4230.80 c 4230.80 v   48   lag 12.4m
MNQ  23:57  o30651.25 h30652.75 l30645.25 c30651.75 v  868   lag 12.4m
```

So MGC is **4230.80** and MNQ **30651.75**, and MNQ printed a new low at
30645.25 on that bar — information the 5m frame cannot see and the 15m frame
will not see for another twenty minutes.

**This does not trip the stop condition, and saying why matters.** The
condition is *three consecutive checks fail to fetch*. Two checks have now
returned a truncated 5m window, but the fetch is not failing — it is
succeeding on 1m and partially on 5m. Stopping a live desk on a
frame-specific degradation while a healthy frame is delivering current price
would be the wrong call, and counting these toward a limit meant for a dead
feed would get there by miscounting rather than by judgement.

**What was at risk, checked rather than assumed.** With 5m and 15m frozen,
`resolve.py` sees no new bars for plans keyed to those frames and correctly
does nothing — but a trigger touched since 23:45 would be invisible to it.
So I checked the range actually traded on the live 1m frame against every
pending trigger:

```
traded 23:45-23:58   MGC 4229.50 - 4232.60      MNQ 30645.25 - 30673.00
CALL-0001  MNQ 30998.50  (15m)   far above
CALL-0002  MGC  4289.10  (15m)   58.3 above
CALL-0003  MNQ 30767.25  ( 5m)   94.3 above  <- expires 02:00 ET
CALL-0004  MGC  4287.60  (15m)   56.8 above
```

Nothing came near anything. **No trigger was missed** — that is a verified
statement, not an inference from resolve.py's silence. The distinction is the
whole point: resolve.py reporting "nothing resolved" while its input frame is
frozen is not evidence that nothing happened, and I should never again report
a quiet check without checking the live frame when a frozen one is feeding
the resolver.

The standing fix, if this recurs: give `resolve.py` a **staleness assertion**
per plan — if the newest bar on a plan's own frame is older than some multiple
of that frame, it should say so loudly rather than return a silent no-op that
reads identically to a genuinely quiet market. Specifying it here rather than
writing it mid-loop, same discipline as N17.

### The frame split is also showing up in the bias table, and it is an artefact

```
MGC   1m BULLISH 3-0 unanimous   <- reading a LIVE frame, price up from 4225.60
MGC   5m BEARISH 0-3 unanimous   <- reading a FROZEN frame, stuck at 23:45
```

MGC's 1m headline is the only frame tonight looking at bars newer than 23:45,
and it has gone unanimously bullish off a 4.60-point bounce. That is not a
disagreement between timeframes — it is a disagreement between *times*. Any
multi-timeframe reading taken right now is comparing 00:09 data against 23:30
data and calling the difference structure. Not trading off it, and not
reporting the split as though it meant something about the market.

## N20 — the 5m endpoint recovered and left a permanent 15-minute hole behind it. The 1m frame is a superset and can repair it.

00:13 ET. The truncated window healed after two checks:

```
MGC 5m newest 2026-09-28T00:00:00-04:00  lag=13.7m  new=1 revised=1
MNQ 5m newest 2026-09-28T00:00:00-04:00  lag=13.7m  new=1 revised=1
```

Lag is back to 13.7 minutes, which is normal. But `new=1` is the tell, and it
is not good news. The store held 23:45; the vendor resumed at 00:00. **It never
served 23:50 or 23:55, and it has now moved past them.** Gap scan, both symbols:

```
GAP 15m  23:45 -> 00:00
```

So the 5m series has a permanent 15-minute hole in it. This is the cost of the
truncation that N18 and N19 described, and it is a different cost from the one
I was watching for: I checked that nothing already stored was *overwritten*,
and it wasn't — but bars that were never delivered cannot be protected by a
merge rule. **The delta design defends the past. It cannot manufacture a
present the vendor declined to send.**

### Checked the hole for a missed trigger rather than assuming it was empty

The 1m frame stayed live throughout (N19), so the window is fully observable
from it — 13 bars, 23:46 through 23:58, all with real volume:

```
MGC  reconstructed 23:46-23:58 envelope   high  4232.60   low  4224.10
MNQ  reconstructed 23:46-23:58 envelope   high 30681.75   low 30645.25
```

Against the four pending triggers:

```
CALL-0002  MGC  4289.10   56.50 above the reconstructed high
CALL-0004  MGC  4287.60   55.00 above
CALL-0003  MNQ 30767.25   85.50 above
CALL-0001  MNQ 30998.50  316.75 above
```

**Nothing was in the hole.** Verified from 1m, not inferred from the resolver's
silence — the same standard N19 set, and the reason it was set. Tonight the
hole is harmless. On a night when a trigger sat inside one, `resolve.py` would
have reported a quiet market forever, and the trade would have been silently
deleted rather than won or lost. That is the worst failure mode this desk has:
not a wrong outcome, an absent one.

### The repair, specified and deliberately not written now

The 1m frame is a **superset** of the 5m frame — five 1m bars aggregate to one
5m bar exactly (open of the first, max high, min low, close of the last, summed
volume), and tonight all thirteen needed bars are present with real volume. So
the fix is not a heuristic, it is arithmetic:

- add a `backfill` step that, after each fetch, finds gaps in the 5m and 15m
  series and reconstructs the missing bars **by aggregation from 1m** where the
  1m coverage is complete;
- mark every reconstructed bar with a provenance flag (`src: "agg1m"`), because
  a bar this desk computed is not a bar the vendor asserted, and `NOTES.md` N5a
  only worked because the raw snapshots were kept distinguishable;
- refuse to reconstruct where 1m coverage is partial, and leave the gap visible
  instead of filling it with something plausible.

Not writing it at 00:13 with four plans pending. The rule I am following is the
one from N17 and N19: code that touches the resolver's input while a live
position could depend on it gets specified first and written at a full check.
Writing it now would also mean the first thing it ever did was modify the
series underneath a trade I am currently watching.

### Standing note on the two frames

`resolve.py` keys each plan to its own frame — three of the four live plans are
15m, one is 5m. The 15m series is now the *most* exposed frame, because a
15-minute vendor hole destroys exactly one 15m bar and that bar's high and low
are the only thing a 15m plan is resolved against. The 1m frame, which is the
one I have been treating as supplementary, is the only frame that has not lost
a bar tonight.

## N21 — the hole is in ALL THREE frames, N20's "1m lost nothing" was wrong, and partial 1m coverage makes reconstruction asymmetrically unsafe

00:18 ET. Feed healthy — newest 5m bar 00:05, lag 13.5m, +1 new on 5m and 15m.
The 15m frame's `+1 new` looked like the hole filling. It was not: the new bar
is **00:00**, and the 23:45 bar is absent. Gap scan across every frame, since
20:00 ET, identical on both symbols:

```
 1m   248 bars   gap 23:58 -> 00:00  ( 2m)   <- 23:59 missing
 5m    48 bars   gap 23:45 -> 00:00  (15m)   <- 23:50, 23:55 missing
15m    16 bars   gap 23:30 -> 00:00  (30m)   <- 23:45 missing
```

**Every frame lost the same wall-clock window, 23:46-23:59, expressed in its
own granularity.** N20 closed with "the 1m frame is the only frame that has not
lost a bar tonight." That is wrong and I am correcting it: 1m lost 23:59. It
lost the *least* — one minute against fifteen and thirty — but the difference
between "least" and "nothing" is exactly what the backfill plan rests on.

### The correction breaks the repair I specified one check ago, in a useful way

N20's rule was: reconstruct 5m and 15m gaps by aggregating 1m, and *refuse
where 1m coverage is partial*. Applied to tonight:

```
5m  23:50  needs 1m 23:50-23:54   5 of 5 present   -> reconstructible
5m  23:55  needs 1m 23:55-23:59   4 of 5 present   -> REFUSED (23:59 missing)
15m 23:45  needs 1m 23:45-23:59  14 of 15 present   -> REFUSED (23:59 missing)
```

So the rule as written repairs one bar out of three and declines the two that
matter most — including the 15m bar that three of the four live plans would be
resolved against. A single missing minute at the right-hand boundary vetoes the
whole containing bar.

**And loosening it is not symmetric, which is the finding.** An aggregate built
from 14 of 15 minutes yields a high and a low that are a **subset** of the true
envelope: the range can only be understated, never overstated. For the two
things `resolve.py` does with a bar, that cuts opposite ways:

- **Trigger detection.** Understating the range can only cause a *missed* fill,
  never a phantom one. A trade that should have filled is recorded NO_FILL at
  0.0R. Conservative, and it costs a winner or saves a loser at random.
- **Stop detection.** Understating the range can only cause a *missed stop*.
  A position that was actually stopped out keeps running to its target on the
  next bar and gets journalled as a **win**. That is not conservative. That is
  the ledger flattering itself, and it is the same class of error as N5a
  ($122/contract from a stub) and the reason resolve.py already gives the stop
  priority when one bar holds both.

So the spec from N20 needs a clause it did not have: **a reconstructed bar with
incomplete 1m coverage may be used to decline a fill, and must never be used to
decline a stop.** Where coverage is partial and a position is open, the honest
outcome is `UNDETERMINED` — the same verdict N10 reached — not a resolved one.
Writing that down now, before the code exists, so the code cannot be shaped by
whatever tonight's trades happen to need.

Still not implementing at 00:18 with four plans pending. Same rule as N17, N19,
N20: specified here, written at a full check.

### What actually changed in the read

The 15m EMA20 and location updated for the first time in three checks now that
a 15m bar finally landed:

```
MGC  location 1.8% -> 4.8% of range [4224.20, 4332.30]   structure lows 4227.30 -> 4224.20
MNQ  location 8.1% -> 5.8% of range [30637.50, 30935.25]  new low 30637.50
```

MGC's 1m headline has fallen apart — BULLISH 3-0 two checks ago, CONFLICTED 1-1
now — which is N9's finding repeating: the 15m headline flipped seven times in
three hours on ~90 points, and the 1m is worse. MNQ's 1m is BEARISH 1-2, also
not unanimous. Nothing to trade off either.

## N22 — the extension test decays on BOTH price paths, so a correct reversal call switches the detector off. Measured, not argued.

00:23 ET. Feed healthy, newest 5m bar 00:10, lag 13.2m. Both symbols are
bouncing — MNQ 30678.75, up 41.25 from its 30637.50 low; MGC 4232.00, up 7.80
from 4224.20. MNQ's 1m has gone BULLISH 3-0 and so has MGC's.

**MNQ's reversal setup no longer qualifies, and it now fails for the opposite
reason it used to.** At 22:55 and 23:58 it passed extension and the HTF test.
Now:

```
reasons: ["only -1.27 sigma from the 20-bar mean, needs |1.5|"]
htf_support: ["4h", "DAILY", "WEEKLY"]     <- still three, unchanged
trigger: 30704.75                           <- unchanged from 23:58
```

The HTF support it always needed is intact. What broke is the extension — and
it broke *because price bounced*. The detector was pointing at a reversal; the
reversal began; the detector switched off.

### The measurement that makes this more than a complaint

N17 recorded sigma decaying while price kept falling, and attributed it to the
20-bar mean chasing price down. Tonight's full sequence shows the decay is
indifferent to direction:

```
MNQ    22:55  price 30701.75   sigma -2.12
       23:58  price 30669.25   sigma -1.55     price FELL  32.50, sigma decayed 0.57
       00:23  price 30678.75   sigma -1.27     price ROSE   9.50, sigma decayed 0.28

MGC    23:10  price  4229.00   sigma -1.82
       23:28  price  4225.60   sigma -1.82     price fell,  sigma flat
       23:58  price  4225.60   sigma -1.45     price flat,  sigma decayed 0.37
       00:23  price  4232.00   sigma -1.09     price ROSE,  sigma decayed 0.36
```

**Falling, flat and rising price all produced decay.** So the accurate statement
is not "the mean chases price down" — it is that a z-score against a trailing
mean measures *acceleration*, not displacement. It stays extended only while
price keeps outrunning its own 20-bar average. The moment price merely
continues, stalls, or turns, the reading relaxes toward zero.

That is a real defect for this specific job. A reversal detector gated on
|sigma| >= 1.5 is therefore structurally incapable of confirming a reversal: it
can only fire during acceleration *away* from the mean, which is precisely when
a reversal has not yet started. Every configuration of it either fires too
early (mid-plunge, no evidence of a turn) or not at all (after the turn, when
the evidence exists). This is not a threshold to tune. It is the wrong
statistic for the question.

The fix belongs with N20/N21's backfill work at a full check, and it is the same
shape: **anchor the reference.** Measure displacement from a *fixed* pivot — the
high at which the down-leg was identified — rather than from a trailing mean.
A fixed anchor does not relax when price turns, so an extension measured against
it survives the bounce it is meant to catch. Then test it against a random-level
control before believing anything, per rule 8.

I am not going to pretend this makes tonight's non-calls look better. Two
qualifying setups were declined for reasons I still hold — N15's sliding trigger
and correlated stacking, N16's structural HTF veto on MGC. But the honest
addition is that the instrument was also miscalibrated for the task, in a way I
can now state precisely, and some of what I read as "nothing qualified" was the
statistic relaxing rather than the market being quiet.

### State

MNQ has retraced 41.25 of its decline and MGC 7.80, both on non-unanimous
lower-frame readings and with 5m/15m/60m still bearish on both. `reversal()`
returns no call on either. CALL-0003 sits at 30767.25 with 88.50 to go and
expires at 02:00 ET; the bounce has made it *closer* for the first time tonight,
which is exactly the situation N8 exists for — the trigger stays where it was
written.

## N23 — N22's prediction came true one check later, and it is now the reason there is no call

00:32 AM EDT. Keeping this short because it is a confirmation of a claim already
written, not a new finding — but it is the first time this desk has made a
falsifiable prediction about its own instrument and then watched it happen.

N22 said a `|sigma| >= 1.5` gate "can only fire during acceleration away from the
mean, which is precisely when a reversal has not yet started", and that every
setting therefore fires too early or not at all. Measured now:

```
MNQ  reversal_setup  trigger 30704.75   price 30689.50   distance  15.25
                     htf_support 4h, DAILY, WEEKLY       (three, intact)
                     reasons ["only -1.02 sigma ... needs |1.5|"]
     5m headline     BEARISH 0-1        (was 0-3 at 00:18, 0-2 at 00:27)
     1m headline     BULLISH 3-0
```

**The trigger is finally within 15.25 points — and the extension test has decayed
out from under it.** Every other condition is satisfied: three higher timeframes
bullish, the 5m bear case down to one component of three, the 1m unanimously
bullish. The single blocker is a statistic that relaxed *because the bounce it was
supposed to detect is happening.* That is the "not at all" branch of N22, arriving
one check after it was written down.

One nuance N17 did not have: **the trigger has stopped sliding.** 30767.25 →
30735.25 → 30704.75 → 30704.75 → 30704.75, stable across the last three checks.
The slide was never about time, it was about new lows — the 40-bar window only
drops its highest bars when price keeps making lower ones. So the descent halts
the moment the move does, which means an anchored reference (the N22 fix) and the
trailing one agree during a bounce and diverge only during a plunge. That narrows
where the fix actually matters and is worth knowing before writing it.

### Still no call, and the reasons are the ones already on the record

Not calling a reversal: the test does not return true on all conditions, and the
procedure permits a REVERSAL call only when it does. Not pre-registering an MNQ
long at ~30705 either, for N15's two reasons unchanged — CALL-0001 and CALL-0003
are already MNQ LONG stop-entries, so a third fills on the same move and stacks
correlated risk; and a new long 62.50 points below CALL-0003's trigger is the
cheaper-entry-as-the-trade-improves inversion N15 declined, just pointing the
other way now that price is rising into it rather than falling away from it.

CALL-0003 stands at 30767.25, 77.75 away, expiring 02:00 ET in about 88 minutes.
If the bounce carries another 78 points it fills on its own terms, at the number
written before any of this was visible. That is the outcome I want, and the only
reason it is available is that nobody moved it.

## N24 — added a status badge and a letter grade to the card. The grade's first version was worthless and I had to rebuild it.

00:46 AM EDT, at the owner's request: a live status badge (`AWAITING FILL` /
`ACTIVE · IN POSITION` / `CLOSED ±xR`), a letter grade in glyphs as large as the
symbol, and larger type for BUY/LONG and SCALP/SWING.

The badges are mechanical: `live_status()` reads `state.json` and the plan's own
`status`, so the badge answers "is money at risk right now" from the account
rather than from how the callout is worded.

### The grade needed two attempts and the first one was a fake

Version one scored each criterion and mapped `int(round(pts)) + 3` onto a ten-step
scale. Every one of the four live plans came out **B+**, the ceiling. A grade that
assigns the same letter to four different plans is not measuring anything — it is
decoration that flatters the book. The cap was doing all the work and the criteria
none of it.

Rebuilt to score as a **fraction of the credit actually available** (`CREDITS_MAX
= 11.0`, declared next to the criteria so adding one without updating it would be
obvious rather than silently inflating every grade ever printed). Result:

```
CALL-0001  MNQ LONG  SWING   C
CALL-0002  MGC SHORT SCALP   C+
CALL-0003  MNQ LONG  SWING   C
CALL-0004  MGC SHORT SCALP   C
```

Those are honest letters for DISCRETIONARY plans built from untested families, and
they discriminate, which the first version did not.

### The ceiling is B+ and it is unreachable by design

`GRADE_CEILING = "B+"`. Nothing in this repository has a measured edge — largest
*t* 3.923 against `free_t` 5.46, and the best of a 21,060-strategy index search is
3.82 and belongs to a placebo. So the grade measures **construction only** and
stops where construction runs out. "A" and "A+" cannot be earned, not because
tonight's plans fell short but because no measurement here could justify printing
them. The card prints `GRADE · CEILING B+` directly under the letter so it can
never be read as validation. The owner asked for "+A or something" and is getting
a scale whose top is deliberately shut; that is a change to what he asked for and
it is stated rather than quietly imposed.

### Cross-checked the grader against a callout it did not come from

The grader has to apply to this desk on the same terms it applied to someone
else's call, or the letter is worthless. Fed it the Discord MGC long I scored
**4/10 by hand** forty minutes ago:

```
DISCORD  MGC LONG  4230 / SL 4224.2 / TP 4300   ->  C-
   · stop 0.65xATR clears rule 4 but only just
   · stop sits 0.10 from the 40-bar extreme - on the cluster
   · risk $58 is 24% of permitted, inside the 50% cap
   · LIMIT entry - price must come to it, not chased
   · SCALP label vs reach 7.88xATR - mislabelled
   · 2 agree / 4 against - at rule 1's 2+1 ceiling
```

It found the same three faults I found by eye — stop on the cluster, rule 4 only
just cleared, horizon mislabelled — and landed at C- against my 4/10. It also
correctly credited the two things I said were good, the limit entry and the small
size. That the mechanical score agrees with the manual one on a call the criteria
were not written around is the only evidence available that the grade is reading
the plan rather than reciting my opinion.

**And it ranks my own book one notch above it, not five.** CALL-0001 through 0004
grade C to C+ against the Discord call's C-. That is the honest gap and I would
rather print it than a flattering one: the desk's plans are better constructed in
where the stop sits, and worse in that three of four use families never generated
for their symbol.

### The criterion that will look wrong and is not

Criterion 6 scores confluence with a PEAK, not a slope: 2-3 agreeing families earns
full credit and **4 or more loses a point.** That inverts the intuition that more
agreement is better, and it is rule 1 — measured in this repository — that two
signals plus one filter is the ceiling and past it more agreement is worse. So
CALL-0002 and CALL-0004 are each docked for having four families agree. Anyone
reading the card will think that is a bug. It is the finding.

## N25 — full check: the journal audit found two real defects in my own record-keeping, and one false alarm I raised myself

00:55 AM EDT, hourly full check. `CALLOUT.md` unchanged since `1948339`, no
contradiction with `CHECK_PROCEDURE.md`, nothing to reconcile. Feed healthy,
newest 5m bar 00:45, lag 10.3m. Nothing triggered, nothing resolved, zero closed
trades, drawdown $0.

The full check is the one that audits the record rather than the market, and this
time the record was wrong.

### False alarm, mine, corrected before acting on it

My first pass matched journal entries to plans on `symbol` + `side` + timestamp
and reported **CALL-0001 unjournalled**. That was wrong. CALL-0001 *is* in the
journal — inside `CALL-NT-0002`, a NO TRADE entry carrying
`pre_registered_instead: CALL-0001`. My matcher missed it because that entry has
`side: null`. Recording this because I nearly reported a missing callout to the
owner, and the cause was my audit query, not the journal. **An audit that can
produce a false positive on the desk's own compliance is worse than no audit**, and
the fix is that a compliance check must match on `call_id`, never on a reconstructed
key.

### Defect 1, real: R-8's mandatory fields were null on every pre-registration

`CALLOUT.md` makes `entry_price`, `initial_stop` and `symbol` mandatory under board
rule **R-8**, with the reason stated: "without those three, account sizing later is
a re-run rather than a read."

```
CALL-0002-PREREG  entry_price None  initial_stop None
CALL-0003-PREREG  entry_price None  initial_stop None
CALL-0004-PREREG  entry_price None  initial_stop None
```

The numbers were not lost — they are in each entry's `why` prose. But prose is not a
field, so a later sizing pass would have to parse English, which is exactly the
"re-run rather than a read" R-8 exists to forbid. Three of four pre-registrations
breached a mandatory board rule and I did not notice for three hours.

Fixed by **appending four `-AMEND-R8` records, not by rewriting the originals.** Two
reasons. The original entry with `entry_price: null` is the only evidence this desk
got it wrong, and editing it would delete the proof. And the desk already works
append-only everywhere it matters — deltas rather than snapshots, `resolve.py` as the
sole writer of outcomes — so mutating a journal line would be the one place history
gets rewritten. Nothing in the amendments is an outcome: the trigger and stop are the
pre-registered numbers, fixed at creation, unchanged (N8), and every plan is still
unfilled. CALL-0001 got an amendment too, closing the separate inconsistency that it
is the only plan without its own `-PREREG` line.

### Defect 2, real: NO TRADE decisions were reasoned, committed, and never journalled

`CALLOUT.md`: "`NO TRADE` gets journalled too, with `side: null` and the reason. A
record that only contains the trades you liked is a record of your memory, not of
your process."

Two of tonight's most consequential decisions were never journalled — only written
to `NOTES.md`:

- **N16**, declining both sides at 4235 (23:10 ET);
- **N15**, declining MNQ's first-ever qualifying reversal setup (22:55 ET).

Both are now in `journal.jsonl` as `CALL-NT-LATE-*`, with `late_entry: true`, the
real decision time in `decided_at_et`, and `late_entry_reason` saying plainly that
they were missed. **The `ts` is now, not then.** Backdating it would have made the
journal assert something false about when it was written, which is the precise
failure the journal exists to prevent — and it would have been a worse offence than
the omission it was covering.

The uncomfortable part: the omission was not random. Both missing entries are
*declines*. Every directional pre-registration got journalled the moment it was
made; the two hardest no-calls did not. That is the exact asymmetry CALLOUT.md names
— a record skewed toward the trades I found interesting — and it appeared in this
desk's own journal within four hours of the rule being read aloud.

### Ledger

```
journal records          11   (7 directional, 4 NO TRADE, 4 amendments)
pre-registered PENDING    4
open positions            0
closed trades             0
win rate                 N/A - zero closed trades
expectancy               N/A      ambiguous bars 0
equity            $50,000.00      drawdown $0.00
to the $2,600 operational floor    $2,600.00
to the $2,800 absorbing state      $2,800.00
ladder fraction   0.000 of the $4,000 usable buffer
```

Win rate is **N/A, not 0%**. With zero closed trades there is nothing to divide, and
rule 3 forbids quoting either win rate or payoff without the other — on an empty
denominator both are undefined rather than bad.

### Fresh read, and the 60m frame says something the 15m does not

```
MGC 60m BEARISH 0-3 unanimous   close 4230.10 < EMA20 4298.19   2.3% of [4227.30, 4351.60]
MNQ 60m BEARISH 0-2 NOT UNANIM  close 30680.25 < EMA20 30813.86  location MIXED 49.3%
```

MNQ's 60m **location is 49.3% of its 40-bar range** — dead centre of
[30370.75, 30998.50]. On the 15m it reads 15.9% and looks like a symbol pinned at its
lows. Both are true of their own windows, and the 60m one is the wider fact: MNQ is
mid-range on the hour and only extended on the quarter-hour. That is worth more than
either headline, and it is an argument against the MNQ long *and* the MNQ short.

Both `reversal_setup` calls still fail on extension — MGC -0.96, MNQ -1.01, decaying
further as N22 predicted. No call. Four plans stand unchanged; CALL-0003 expires at
02:00 ET, 84.75 points out of reach.

## N26 — both MGC grades rose two notches without either plan changing. The cause is a 3-point cliff I built into criterion 6.

01:04 AM EDT. Newest 5m bar 00:50, lag 14.3m. Nothing triggered, nothing resolved.
But the cards changed:

```
CALL-0002  C+ -> B
CALL-0004  C  -> B
```

Neither plan was edited. Both were pre-registered hours ago and their trigger,
stop, targets and size are untouched (N8). The letter moved because **the grade is a
live read, not a property of the plan** — it recomputes ATR, the 40-bar envelope and
the confluence tally from current bars every render. I knew that when I built it, and
I said so on the card. What I did not anticipate is how much a single input can move it.

The diff, isolated:

```
00:46 check   4 families agree  ->  "PAST rule 1's ceiling, a warning not support"   -1.0
01:04 check   3 families agree  ->  "at rule 1's 2+1 ceiling"                        +2.0
```

**One family stopped agreeing and the score moved 3.0 points**, which on an 11-point
denominator is 27% of the entire scale — two letter grades. Everything else barely
budged: CALL-0002's stop went 1.13 -> 1.22 xATR and its reach 1.80 -> 1.94 xATR as
ATR shrank, worth nothing in score terms.

**The direction of the move is correct and is not the defect.** Rule 1 was measured in
this repository: two signals plus one filter is the ceiling, and past it more agreement
is worse. So a plan whose confluence falls from four to three genuinely improves on
that criterion, and a grade that rose is the rule working. Anyone who expects a grade
to fall when support weakens is expecting the thing rule 1 disproves.

**The magnitude is the defect, and it is mine.** Criterion 6 is a step function with a
cliff at the 3/4 boundary: `<=3` earns +2.0, `>=4` loses 1.0, with nothing in between.
That makes a single family flipping its verdict — on OHLCV-derived heuristics, several
of which `confluence.py` itself marks untested — worth more than the stop placement and
the sizing put together. A grade that swings two letters on the least reliable input it
has is not measuring construction, it is amplifying noise.

Fix, specified and not written now (same rule as N17, N19, N20, and this one has the
extra reason that I am looking at a specific pair of cards while I write it): make
criterion 6 **continuous** rather than stepped — credit peaking smoothly at 2-3 agreeing
and tapering above, so one vote changes the score by a fraction of a point instead of
three. And cap any single criterion's contribution at some fraction of CREDITS_MAX so
no lever can move the letter two notches alone. Both belong at a full check, with the
before/after printed for all four plans so the recalibration can be seen rather than
asserted.

**Reporting the B to the owner with the caveat attached, not the B alone.** The letter
is real and mechanically derived, and it is also two notches up on a plan nobody
touched, for a reason that says more about my scoring function than about the trade.
Showing the grade without that would be showing an improvement that did not happen.

## N27 — the grade flickered two letters in ten minutes, so I fixed it mid-loop and I am stating why that was the right exception

01:09 AM EDT. Newest 5m bar 00:55, lag 14.0m. Nothing triggered, nothing resolved.

N26, one check ago, recorded both MGC grades rising C+/C -> B because confluence fell
4 AGREE -> 3 AGREE and criterion 6's step function turned a -1.0 penalty into a +2.0
credit. I specified the fix and deferred it to a full check. Five minutes later:

```
01:04   3 agree   CALL-0002 B    CALL-0004 B
01:09   4 agree   CALL-0002 C+   CALL-0004 C
```

**Straight back down, two letters, with both plans frozen.** So the cliff does not
merely make the grade coarse — it makes it *oscillate on the check cadence*. A number
shown to the owner every five minutes that swings two letters while nothing about the
trade changes is not a coarse measurement, it is a misleading one.

### Why I broke the defer-to-a-full-check discipline here, and where the line is

N17, N19, N20 and N26 all deferred a fix. That discipline exists for one specific
danger: code rewritten while watching a move gets fitted to that move. It applies to
anything feeding a decision or an outcome — `reversal_setup`, the 1m backfill, anything
`resolve.py` reads.

**The grade is display-only.** It cannot change whether a plan fills, what it fills at,
where its stop is, or how it resolves. It touches no pre-registered number (N8) and
`resolve.py` never reads it. So the post-hoc-fitting risk is not the same risk, and
against it sits a concrete cost: leaving a known-flickering figure in front of the owner
for an hour. Fixing display promptly and deferring signal code is the right way round,
and conflating the two would have been using a good rule as an excuse.

The residual risk is real though — I was changing a scoring function while looking at the
four cards it re-scores. Mitigation: **I wrote the formula from rule 1's shape and
committed it before evaluating it**, then printed before/after for all four plans.

### What changed

Criterion 6 is now continuous. Credit peaks at 2.5 agreeing families — two signals plus
one filter, the measured ceiling — and falls quadratically in *both* directions, because
zero support and excess agreement are each a reason not to trade. Clamped [-1.0, 2.0] so
this criterion can move at most 3.0 of `CREDITS_MAX` 11.0 and no single lever can swing
the letter two notches alone.

```
agreeing  0      1      2      3      4      5      6
credit   -1.00  +0.43  +1.82  +1.82  +0.43  -1.00  -1.00

3 -> 4 agreeing:   stepped 3.00 pts (2 letters)  ->  continuous 1.40 pts (~1 letter)
```

**I adjusted the coefficient once, and the reason was not the letters.** At 0.35 the
curve gave both "1 agrees" and "4 agree" +1.21 of a 2.00 maximum — 60% credit for two
states rule 1 says are bad — which fixed the sensitivity while inflating every grade a
notch. 0.70 keeps the peak at 2.00 and drops the off-peak states to +0.43, so hitting
the ceiling is clearly distinguished from missing it either way. That is the whole
argument, it is not "the numbers looked better", and I am not touching the coefficient
again.

### Before and after, all four

```
                     stepped (01:09)   continuous
CALL-0001  MNQ            C               C
CALL-0002  MGC            C+              B-
CALL-0003  MNQ            C               C
CALL-0004  MGC            C               B-
```

Both MGC plans still end a notch above where the stepped version had them at this
tally, so the change is not neutral and I am not going to present it as neutral: it
credits a 4-agree state at +0.43 where the old one penalised it -1.0. The defensible
part is that the penalty was arbitrary and the new number is on a stated curve; the
honest part is that my own book got slightly better-looking out of it. The ranking is
unchanged — MGC's two plans above MNQ's two, and all four still below the B+ ceiling.

## N28 — smoothing the mapping did not stop the grade moving, because the INPUT oscillates. The real error is that I put two different things in one letter.

01:13 AM EDT. Newest 5m bar 01:00, lag 13.8m. Nothing triggered, nothing resolved.
All four grades moved again — one notch each this time, not two:

```
              01:09   01:13
CALL-0001  C      -> B-      confluence 1 agree -> 2 agree
CALL-0002  B-     -> B       confluence 4 agree -> 3 agree
CALL-0003  C      -> B-      confluence 1 agree -> 2 agree
CALL-0004  B-     -> B       confluence 4 agree -> 3 agree
```

The continuous curve did exactly what N27 designed it to do — amplitude down from two
letters to one. But the letters are still moving every five minutes, and now the cause
is visible and it is not the mapping.

**MGC's confluence tally across four consecutive checks: 4 -> 3 -> 4 -> 3.** The input
itself oscillates on the check cadence. Smoothing a mapping cannot stabilise a figure
whose input flickers; all I did was halve the amplitude of the flicker. N26 diagnosed a
step function, N27 fixed the step function, and the thing I was actually chasing was
underneath both.

### The design error, stated plainly

I put **two different quantities in one letter**:

- **construction quality** — where the stop sits relative to ATR and the 40-bar
  extreme, whether the size is inside the cap, whether the entry is forward or
  reactive, whether the horizon label matches the arithmetic, whether the family was
  ever tested for that symbol. All of this was determined **when the plan was written**
  and cannot change afterwards, because N8 forbids changing any of it.
- **current context** — how many families agree right now, what today's ATR is. This
  moves by construction, and is supposed to.

A grade that mixes them is incoherent: it claims to score how well a plan was built,
then revises that score as the market moves, with the plan untouched. The owner is
being shown a letter that looks like a verdict on the callout and is partly a reading
of the last five minutes.

### The fix, and why implementing it right now would be the wrong kind of convenient

Split them. Compute the **construction grade once, at pre-registration, from the bars
available at that moment**, and never recompute it. Show current context separately —
the TIMEFRAMES column and confluence panel already do that job and are honestly
labelled as live.

The trap: if I froze the grades at *this* check, I would be locking in the highest
values they have taken all night — B-/B/B-/B, against C/C+/C/C forty minutes ago. That
is not a fix, that is picking a flattering snapshot and calling it permanent. Done
properly the construction grade for each plan must be computed from the bars **as of
that plan's own `created_bar_ts`**, which the archive supports but which is real work:
it needs the ATR and 40-bar envelope reconstructed at four different historical
timestamps, and `confluence.evaluate` called against each plan's creation state rather
than now.

Stored in a sidecar keyed by `call_id`, not written into `pending.jsonl` — a
pre-registered plan record should not grow fields after the fact, and N25 already
established that this desk amends by appending rather than mutating.

**Three changes to the grader in one hour is enough.** N26 diagnosed, N27 fixed the
mapping, and this is the third finding in the same component while I watch the letters
it produces. The pattern of repeatedly adjusting a scoring function in front of the
thing it scores is itself the risk, whatever each individual justification looks like.
Specified here, implemented at a full check, from historical bars.

### Until then, what the letter means

It is a live composite, not a verdict, and it will keep moving a notch as confluence
flickers. Ranking is stable and is the part worth reading: **MGC's two plans above
MNQ's two, every check tonight**, which comes from the fixed criteria — MGC's stops sit
~4x ATR clear of the 40-bar extreme, MNQ's CALL-0001 sits 3.50 points off it. That
ordering has not changed once, through two grader rewrites and four confluence flips.

## N29 — the Discord call I graded C- filled and stopped out inside 25 minutes, on exactly the flaw I named. One datum, and I made nothing being right.

01:18 AM EDT. MGC broke to a new low **4222.40** and closed 4223.00. That number
settles the callout the owner asked me to rate at 00:42.

```
Discord:  MGC LONG 4230 · SL 4224.2 · Target 4300 · 1 con        my grade: C- (4/10)

00:40  o 4228.80 h 4232.30 l 4228.80 c 4230.80   ENTRY 4230 touched  -> FILLED
00:45  o 4230.80 h 4231.50 l 4229.40 c 4230.10
00:50  o 4230.10 h 4230.40 l 4228.00 c 4228.80
00:55  o 4228.90 h 4229.70 l 4226.70 c 4227.40
01:00  o 4227.40 h 4230.80 l 4227.10 c 4228.00
01:05  o 4228.00 h 4228.20 l 4222.40 c 4223.00   SL 4224.2 TOUCHED   -> STOPPED
```

Filled at 4230, stopped at 4224.20. **-5.80 points, -$58 on one contract**, plus
$1.44 round-turn commission and exchange fees and ~$1 of stop slippage at this
vendor's one-tick assumption — call it **-$60, in about 25 minutes.** The 70-point
target never came within 68 points of being relevant.

### The critique was specific, and this is the specific thing that happened

What I wrote at 00:42: *"the stop is exactly on the 40-bar low — 0.00 away. That's not
near the low, that's at it... A one-tick probe ends the trade. This is the whole thing,
and it's why the 12R is an illusion: the geometry is only as good as the stop's survival
odds, and that stop is parked on the trapdoor."*

The low printed **4222.40** — **1.80 points** through the stop — and price closed
4223.00, back above it. It was a probe, not a collapse. The trade did not fail because
gold fell 70 points the wrong way; it failed because the stop sat on the one price every
other stop in the market was sitting on, and the market went there and came back.

I also proposed the fix: *"Move the stop under the low — 4221 or 4219."* Neither would
have been touched by 4222.40. The position would still be open.

### What this is worth, stated honestly, because the temptation is to overclaim

**It is n=1.** A stop 1.8 points lower surviving one probe is a single observation, and
a stop that survives a probe can still lose later. The general claim — that stops parked
on the obvious swing low get taken — is not proved by one instance, and this repository's
whole posture is that nothing here has a measured edge. Had the low printed 4218 instead
of 4222.40, my proposed stop would have gone too and the critique would look identical
while being equally unproven.

**What it does establish** is narrower and still worth having: the failure mode I named
was the failure mode that occurred, within the window I named it in, at the price I named
it at. That is the correct shape of evidence for a critique even at n=1, because the
prediction was specific enough to have been wrong.

**And I made nothing being right.** Both my MGC shorts are unfilled and now further away
than at any point tonight — CALL-0002 needs +66.10, CALL-0004 +64.60. My read of gold's
direction was correct for four straight hours and my own book has captured exactly $0 of
it, because both plans require a 60-point retracement first. That is the N18 lesson
again: a limit entry solves being late by refusing to participate. Being right about
someone else's trade and flat in your own is not a good night, it is a well-documented
one.

**No journal entry for this.** It is not this desk's trade and writing it into
`journal.jsonl` would inflate the record with a position nobody here took. It belongs in
NOTES as a graded critique that got tested, which is what it is.

### State

MGC is at **0.5% of its 40-bar range** [4222.40, 4332.30] — a new low, all five eligible
frames bearish. MNQ has diverged: its 15m dropped to **0-2 NOT UNANIMOUS** with structure
**MIXED** — swing lows **30637.50 -> 30666.75, HIGHER** — the first higher low on either
symbol tonight. `reversal()` explicitly names that as why there is still no call: *"15m
is 0-2, not unanimous."* Worth watching; not tradeable, because rule 1 makes component
disagreement a reason not to trade rather than a weaker reason to trade.

CALL-0003 is 87.00 out with 42 minutes left and will almost certainly journal NO_FILL.

## N30 — the owner was right that NO_FILL hides the diagnosis, and building the tool to show it exposed a plan that has never been evaluated at all

01:23 AM EDT. Newest 5m bar 01:10, lag 13.3m. Nothing triggered, nothing resolved.

### What the owner asked for, and why it matters more than it sounds

His point: when recording the result of a callout, account for the case where **the entry
never filled but price still went the predicted way.** Both cases journal 0.0R — correctly,
because no position was held and inventing a number would be fabrication — but 0.0R alone
collapses two opposite diagnoses into one symbol:

```
direction right, entry unreachable  ->  fix the TRIGGER
direction wrong                     ->  fix the READ
```

A ledger of nothing but 0.0R cannot tell you which repair you need. Built `thesis.py` to
measure it: for each live plan, the favourable and adverse excursion **from the price when
the plan was written**, against the plan's own target distance. Deliberately measured from
the reference price rather than the unfilled trigger, because the trigger is the thing
under suspicion. It writes nothing — not to the journal, not to state.json — and says so
in its own docstring: `resolve.py` remains the only writer of outcomes.

```
id          sym  side        ref      now     fav     adv    tgt  trig away  verdict
CALL-0001   MNQ  LONG   30889.25 30664.50   11.25  251.75   96.0     109.25  DIRECTION WRONG
CALL-0003   MNQ  LONG   30742.75 30664.50   17.25  105.25   83.2      24.50  DIRECTION WRONG
CALL-0004   MGC  SHORT   4248.30  4224.80   25.90    0.30  19.04      39.30  DIRECTION RIGHT,
                                                            TARGET DISTANCE COVERED
```

**CALL-0004 is the case he was describing, and it is worse than I had understood.** From
4248.30 the plan needed 19.04 points of downside for TP1. It got **25.90**, with an adverse
excursion of **0.30 points**. A short that would have gone almost immediately into profit,
never drawn more than a third of a point against, and paid its full first target — and it
captured nothing, because the sell limit sat **39.30 points above** the reference price
waiting for a retracement that never came. That is not a marginal miss. The read was right,
the risk was near zero, and the trigger made it unreachable.

The two MNQ longs are the opposite and the distinction earns its keep immediately:
CALL-0003's adverse excursion is **105.25** against a 52-point stop. Had it filled it would
almost certainly have stopped out. **Not filling saved money there and cost money on
CALL-0004**, and without this table both look like the same 0.0R.

### And building it found something I would not otherwise have caught

`thesis.py` reported `CALL-0002: no bars since creation`. The cause:

```
CALL-0002  created_bar_ts  2026-09-28T08:20:00-04:00     <- SEVEN HOURS IN THE FUTURE
```

08:20 is MGC's RTH open. When I wrote that plan I put the *window I wanted it to fire in*
into the field that means *the bar it was created on*. And `resolve.py` line 155 is:

```python
all_bars = [b for b in load_bars(sym, plan["bar_minutes"]) if b["ts"] > plan["created_bar_ts"]]
if not all_bars:
    continue
```

With a future stamp that list is empty and the plan is **skipped on every pass**. CALL-0002
has been PENDING for about six hours and has **never once been evaluated** — it cannot
trigger, fill, resolve or expire. Meanwhile its card has said `AWAITING FILL` at every
check. It was not awaiting anything. Nothing was looking at it.

This is the N20 failure class and the worst one this desk has: not a wrong outcome, an
absent one, displayed as live.

### What I fixed, and what I deliberately did not

**Fixed, because it is display and it was false:** `live_status()` now detects a
future-dated `created_bar_ts` and renders **`INERT · NOT EVALUATED`** in red instead of
`AWAITING FILL`. The card stops asserting something untrue.

**Did NOT fix the plan, and this one is important.** Setting `created_bar_ts` back to the
real creation bar would hand `resolve.py` six hours of bars it has never seen, and MGC
traded near 4299 in that window against a 4289.10 trigger — so the edit could manufacture a
triggered position, and possibly a resolved outcome, *from a change I made after watching
the price*. That is precisely N8. Repairing the metadata and repairing the trade are
different acts and only the first is available to me.

So CALL-0002 needs **retirement, not repair** — `CHECK_PROCEDURE.md` already says a stranded
plan gets said so and a fresh pre-registration considered rather than retro-fitted. It
should be retired with an honest non-outcome (`VOID — defective metadata, never evaluated`,
0.0R, no fill), and that is a record action, so it goes at a full check with the reasoning
attached rather than being done quietly mid-loop. Until then it stays in the book carrying
a label that tells the truth about it.

**The standing lesson for new plans:** `created_bar_ts` is the newest bar held at creation,
full stop. An RTH or session constraint belongs in `rth_note` and in the expiry, never in
the creation stamp — putting it there does not gate the plan, it disables it.
