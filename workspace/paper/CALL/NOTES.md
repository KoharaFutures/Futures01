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
