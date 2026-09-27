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
