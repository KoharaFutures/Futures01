# EF7 burst 01 — the clock geometry of the substrate, before any code

Independent re-implementation of the 18:00→16:00 ET session-window rule.
**Independence declaration is in `FINDINGS.md` §0 and is the first thing to read.**

## What the engine actually does (all four claims in my dispatch, verified myself)

| claim | verdict | evidence |
|---|---|---|
| `exit_at_session_close` fires at the *contract's own* RTH close | **confirmed** | `futures_agents/backtest/engine.py:470-473`: `elapsed = minutes_since_open(bar.ts, spec.rth_open) + bar.minutes; if elapsed >= self._rth_minutes`. `_rth_minutes` is `rth_close - rth_open` in minutes (`:244-247`) |
| that close is 13:30 MGC / 14:30 MCL, not 16:00 | **confirmed** | `futures_agents/config.py:157,164` MGC `rth_open="08:20", rth_close="13:30"`; `:179,186` MCL `"09:00"/"14:30"`; MES `:240` and MNQ `:249` are `"09:30"/"16:00"` |
| it is gated on `not self.allow_overnight`, so overnight *removes* the exit | **confirmed** | `engine.py:470` |
| `allow_overnight` default `False`, no call site passes `True` | **confirmed for `futures_agents/`** | `[measured: grep -rn allow_overnight --include=*.py . → futures_agents only at engine.py:233,241,470]`. Other agents' `workspace/` code now passes `True`; nothing in the shipped package does |
| time/session/end-of-data exits close at `bar.close` with zero slippage | **confirmed** | `engine.py:467,473,476` all pass `bar.close` straight to `_close`, which never touches `self.costs.slippage_price` (`:479-517`). Only the entry (`:353`) and the stop (`:416`) charge slippage |

So the rule has to be built. Agreed.

## The clock geometry, measured — and it is not uniform

`[measured: scratchpad/probe_bars.py, probe2.py over data/archive/, all four symbols]`

**1. No bar at any timeframe straddles 16:00 ET.** 60m/30m/15m align to the hour, and
`align_bucket` snaps ≥60m buckets to midnight (`futures_agents/data/bars.py:150-153`), so 240m
falls on 00/04/08/12/16/20 and the 12:00–16:00 bar ends exactly on the deadline. Straddle count
is **0** for 60m, 240m, 30m and 15m on all four symbols. That is a real convenience and it is
worth knowing it is luck of the bucket alignment, not a guarantee.

**2. Bars DO exist inside the forbidden window**, so the veto has something to reject:

| tf | MGC | MCL | MES | MNQ |
|---|---|---|---|---|
| 60m bars opening in [16:00,18:00) | 495 | 474 | 493 | 497 |
| of which open at 17:00 | 6 | 3 | 5 | 9 |
| 240m bars opening at 16:00 | 586 | 563 | 585 | 585 |

The 17:00 bar is nearly always absent (the maintenance break), so at 60m the forbidden window is
usually exactly one printed bar.

**3. The finding that kills the naive rule: cycles do not all end at 16:00.**
Partitioning bars into cycles keyed by the 16:00 ET flat that terminates them:

| 60m | cycles | last bar ends exactly 16:00 | ends **earlier** |
|---|---|---|---|
| MGC | 506 | 489 | **17** (00:00 ×8, 13:30 ×5, 15:00 ×2, 13:00, 11:00) |
| MCL | 505 | 470 | **35** (14:00 ×13, 00:00 ×7, 13:30 ×5, 06:00 ×3, …) |
| MES | 507 | 488 | **19** |
| MNQ | 507 | 488 | **19** |

**Consequence.** The obvious implementation — *close when `bar.end_ts >= 16:00`* — is provably
wrong on those cycles. On an MCL cycle whose last bar ends 14:00, no bar satisfies
`end_ts >= 16:00` until one that opens at 16:00 or later, so the position exits at **17:00 or
later — inside the forbidden window** — or, if the next print is 18:00, it is held straight
across the break. That is 35/505 MCL cycles and 17/506 MGC cycles where a rule that looks right
silently violates the spec. I am recording it before writing the fix so the order is auditable.

The fix has to consult the **successor bar's timestamp** (not its prices): flat at bar *i* when
bar *i+1* is not in the same cycle. That is a look-ahead claim I have to discharge by test, not
assert — see EF7-H4.

## Component ids
- **EF7-H1** `SessionWindow` — pure clock predicate, DST-correct, offset-agnostic.
- **EF7-H2** successor-based flat decision over a bar list.
- **EF7-H3** `SessionWindowEngine` — flat exit with market-order slippage + entry veto.
- **EF7-H4** validation: known-answer, realised-trade invariant, prefix-invariance, closure counts.
