# BT3 burst 01 — replay the account governors over the stored trade stream

**2026-09-27.** One algorithm (ALGO-1), one fidelity question posted, one side errand
(R3 Tier 0 item 2). Stopped there.

## What I was asked

R3's Tier 0 item 1: the backtester never consults `risk/`, so the nineteen operating
parameters that would have governed a $50,000 account were never in the 2,975,629-evaluation
experiment. Replay them over `geo_trades.json`'s 21,954 stored trades and find out what they
would have changed — in particular whether `contracts_for`'s integer floor is, as R3 believes,
an unintended volatility-regime entry filter.

## What I read

- `PIPELINE.md` §4, `OWNERSHIP.md`, `BRIEF.md`, `msgs/01`.
- `R3_path_operation.md`: B-1, B-2, B-3 Channel 4 (a/b/c), B-4, B-5, III-14, R3-D3 Q2,
  R3-D4, R3-D5 Tier 1/2/3, §7 Q2 and Q3.
- `R3_operating_vocabulary.md` §3 (S1–S9) and §7 (P1–P9), §10 (A1–A4).
- `futures_agents/config.py:350-440`, `risk/manager.py:84-376`, `risk/account.py:44-236`,
  `timeutil.py:168-180`, `backtest/engine.py:262-320, 343-380, 484-517`,
  `backtest/montecarlo.py:84-130`, `workspace/newstrats/run_geometry.py` (all 168 lines),
  `workspace/studies/toolkit.py:124-140, 246-280, 319-339`.

## The blocker I hit first, and how I got round it

**`geo_trades.json` records no stop distance.** Its 17 keys are
`['arm','base','cell','dir','exitm','mae','mfe','mins','r','reason','regime','session',
'slice','symbol','tf','ts','vol']` — not one of them is a price, a point distance or a dollar
figure `[measured: sorted(d[0])]`. `RiskManager.contracts_for` needs `risk_points`
`[repo-verified: risk/manager.py:197-203]`. So R3's "zero new code, zero new backtests" holds
for the *daily* governors, which need only `ts` and `r`, and **does not hold for the integer
floor**, which is the item R3 called its strongest non-cancelling result.

It is recoverable without a new experiment because the generating study is fully deterministic:
fixed condition list, fixed disjoint slices of the frozen `csv/raw` snapshot, no seed, no
sampling — and only the `partner == "none"` subset was ever dumped
`[repo-verified: run_geometry.py:110-121]`, which is 22 strategies per cell rather than 286.
`code/stops.py` re-runs that subset and matches every trade back to the artefact.

**The reproduction is exact.** 21,954 reproduced against 21,954 stored, zero not found, zero
whose `net_r` disagrees, worst `|Δr| = 0.000e+00`
`[measured: python3 code/stops.py → "stored trades not found in reproduction: 0 / net_r
disagrees by >1e-5: 0 (worst |dr| = 0.000e+00)"]`. That is also the strongest determinism
check available on this repo's engine, and it passed on the first attempt.

## What I chose

Full list in `ALGOS.md` under ALGO-1 "Where I had to choose". The five that most change the
answer:

1. **Call `RiskManager.assess` whole, never piecemeal.** Neutralise the four stages the
   artefact cannot inform (news, volatility band, setup quality, cost-vs-reward) through the
   proposal's own fields, so every governor that *does* run is the shipped code. No governor
   is reimplemented anywhere in `code/`.
2. **Two populations, never averaged.** POOLED (one account, 176 strategies) and PER_STRATEGY
   (176 fresh $50,000 accounts). They disagree by a factor of 24 on the survival rate, and the
   pooled number is the one that is mostly an artefact.
3. **Same-timestamp order is arbitrary and I measured its cost.** One timestamp carries 74
   trades. Five seeded permutations of the within-timestamp order move the pooled survival
   rate over `[0.537%, 1.685%]` — a 3.1× spread. The pooled reading is therefore
   tiebreak-dominated and I will not quote a single pooled number without that interval.
4. **A "day" is `timeutil.trading_day`, imported** — CME 18:00→17:00 ET, one day for the whole
   account, not one per symbol. That is what `AccountState.roll_day` uses.
5. **P&L lands on the *exit's* trading day**, because `close_position` calls
   `roll_day(when).record(pnl)` with the close time `[repo-verified: risk/account.py:203-220]`.
   Exit `= ts + mins`; exits are flushed before the entry at the same instant, matching the
   engine's manage-then-signal order `[repo-verified: engine.py:296-303]`.

## What I found

Headline counts are in `ALGOS.md`. Three things worth pulling out here.

**The integer floor is not one governor among nineteen — at this account size it is *the*
governor.** In the non-pooled reading it does 15,769 of 16,249 refusals, **97.0%**. Every
account-level rule R3's Tier 0 named — daily loss limit, giveback, trade cap, consecutive-loss
stand-down — fires 456 times between them, **2.8%**.

**R3's volatility-filter reading holds, conditionally.** Held at fixed symbol and timeframe,
survival under the floor falls monotonically across the volatility buckets in 5 of the 6
cells that are not saturated at 0% or 100%. MGC 60m: DEAD 68.6% → LOW 69.7% → NORMAL 48.2% →
HIGH 37.3% → EXTREME 14.2%. MCL 240m is the exception and does not fit.

**Two numbers I had to correct in R3's write-up, both making the effect stronger.** The
opening budget is **$240**, not the $375/$500 R3's B-3(c) table used — `usable_buffer × 0.06`
binds before the equity cap. And `max_trades_per_day` counts *closes*, not opens
`[repo-verified: risk/account.py:67-79, 201]`, so as shipped it does not cap how many trades a
day starts.

## What I asked

`msgs/02_BT3_R3_verify-ALGO-1.md` — eight numbered questions to R3, of which Q1 (population
unit) and Q3 (exposure keyed by symbol or by strategy) are the two that decide whether the
pooled reading means anything. `VERIFY.md` carries the same list.

## What I filed rather than fixed

`REQUESTS.md` REQ-1 … REQ-4: a sampling defect in `bootstrap_paths(mode="block")` measured
and confirmed, the close-counted trade cap, the inert correlation cap, and the fact that a
faithful integer-floor study needs `risk_points` on the dumped trade rather than a
reconstruction.

## Where I stopped and why

At one algorithm. **Every stateful number above is from an UNVERIFIED replay and none of it is
reportable as a result until R3 answers.** PIPELINE §4 is explicit that an unverified result is
an unknown quantity rather than a weak one. I did not code ALGO-2, did not sweep a parameter,
and did not look for a governor configuration that improves anything — the constraint is that I
am measuring what a researched idea does, not searching for a winner.

The one thing I did finish is R3's Tier 0 item 2, because it genuinely was one call per arm.
Result and its caveats in `ALGOS.md` under "Side errand".
