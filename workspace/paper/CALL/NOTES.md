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
