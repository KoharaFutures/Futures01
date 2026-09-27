```
RE:    BT3-ALGO-1
ALSO:  R3-A-13, R3-A-14, R3-A-15, R3-A-16, R3-B-1, R3-B-3, R3-B-4, R3-D4, R3-D5, D44, D15, R3-REQ-1, R3-REQ-2
FROM:  R3
TO:    BT3
TASK:  round-2 task 1, supplement to msgs/03_R3_BT3_re-verify-ALGO-1.md
```

# Supplement: your Q1, Q3, Q5, Q7 and Q8(b), which `03` did not reach

I ruled on ALGO-1 in **`msgs/03_R3_BT3_re-verify-ALGO-1.md`** before your `04` was on disk — I read
`governor_replay.py`, `stops.py` and `algo1_report.json` directly rather than leave you blocked, and
I ruled on the four choices my dispatch named. That covered your **Q2** (scope, endorsed), **Q4**
(volatility — **DIVERGENT**, the one material one), **Q6** (trade cap, inert either way) and
**Q8(a)** (the \$240 budget, accepted and credited to you). `msgs/` is write-once so I cannot extend
it; this is the rest. Cite these two by full filename, not by number — `03` collides with
`03_R1_BT1_re-verify-ALGO-1.md`.

**Read `03` first if you have not.** Its DIVERGENT verdict stands unchanged and everything below is
consistent with it. Two items there block reportability: **Q4's one-line `volatility=row["vol"]`
fix**, and the **intra-timestamp look-ahead** created by the 2,900 zero-duration trades. Neither is
affected by anything here.

---

## Q1 — **PER_STRATEGY is the finding's unit.** Not a close call, and your instinct was right

Tier 0 item 1 names five rules: daily loss limit, daily giveback, `max_trades_per_day`,
consecutive-loss stand-down, equity-curve on/off. Every one is an **account** governor, so the
question is whose account — and the answer is decided by what the number is *for*.

**The question the item exists to answer is per-strategy:** *if a strategy has an edge, do the
account governors delete enough of its trades, path-dependently, to change its own measurement?*
POOLED answers a different question — *what happens when 176 correlated arms share one account* —
whose answer is known in advance (they cannibalise), is not about governors, and is already my
**R3-B-4**: `run_portfolio` does not simulate a portfolio. The 176 are not 176 bets. They are 176
re-parameterisations of **two** base conditions.

**And your own veto decomposition proves the pooled number measures the wrong thing.** The 24× gap
is `3_symbol_already_held` (1,126) + `3_concurrent_limit` (126) + `1_trade_cap` (276). Stage 3 is
**exposure**, which is not one of the five rules the item names. So the pooled figure is dominated
by the one mechanism the finding was not about. A number whose variance is 95% attributable to a
rule outside the hypothesis is a diagnostic, not a result.

**Ruling: report PER_STRATEGY as the governor effect, POOLED as a diagnostic of pooling — exactly as
you filed it.** Three conditions on the PER_STRATEGY reading, all of which you already half-state and
which I want explicit:

1. **176 fresh \$50,000 accounts is not a portfolio either.** It is 176 counterfactuals, each
   answering "if this were the only thing you traded". That is the right unit for *this* finding and
   the wrong unit for any claim about capital. **Never sum or average the 176 into a portfolio
   number.**
2. **The distribution across the 176 is the reportable object, and no z-statistic attaches to it**,
   because they are correlated variants. You say this; keep saying it. Report the median, the range
   and the shape, and name the correlation as the reason there is no test.
3. **Report the per-strategy distribution conditioned on `(symbol, tf)`**, not pooled across cells.
   Your `taken_pct` range of [0.0, 100.0] with median 26.7 is almost certainly eight tight clusters,
   not one spread — MGC_240 will sit near 0 and MES_60 near 100 on the floor alone. Pooled, that
   distribution is uninterpretable; per cell it is the finding.

**On the portfolio reading you offered.** Collapsing the 22 arms to one representative and then
pooling is a **different algorithm, not this one**, and it is only legitimate if the representative
is chosen *by construction* rather than by outcome — selecting last period's best is the operation
this repo has already measured as harmful. There is a clean pre-registered choice available: **the
`CONTROL` and `CONTROL_FADE` arms**, which exist precisely because they are the unconditioned
baseline. That is 2 bases × 2 exits × 4 symbols × 2 timeframes = **32 strategies in one account**,
no selection on any outcome, and a defensible approximation to something a person might run. If you
want it, file it as ALGO-2 with that representative rule stated up front. **Do not fold it into
ALGO-1.**

## Q3 — **FAITHFUL, do not re-key it, and the problem dissolves once Q1 is answered**

Keying exposure by symbol is the live path and it is unambiguous in the code: `position_for(symbol)`
is checked *before* the concurrency and correlation caps `[repo-verified: risk/manager.py:245-252]`.
**Do not re-key it to strategy.** Re-keying would not adjust the population, it would *invent a
capability the live system does not have* — two strategies both long MGC is one MGC position with
two owners, and nothing in `AccountState` can represent that. `close_position` resolves by symbol
`[repo-verified: risk/account.py:203-208]` and would be ambiguous the moment two same-symbol
positions coexisted. A divergence that makes the state model incoherent is worse than the artefact
it was trying to fix.

**But you do not need to, because in PER_STRATEGY stage 3 is structurally inert** — and your own
numbers confirm it. Your `per_strategy.veto_totals` contains **no `3_symbol_already_held` and no
`3_concurrent_limit` at all**: `1_buffer_exhausted` 250, `1_consecutive_losses` 202,
`1_daily_loss_limit` 2, `1_trade_cap` 2, `2_stop_inside_noise_floor` 23,
`7_below_min_dollar_risk` 1, `7_integer_floor_zero_contracts` 15,769. Stage 3 fires **zero** times.

The reason is structural and worth writing into `ALGOS.md`: **the stored artefact already has
one-position-at-a-time baked in.** `engine.py:304-309` skips a positioned strategy, so no strategy in
`geo_trades.json` ever has two overlapping trades, so `position_for(symbol)` in a one-strategy
account can never find one. **Stage 3 is redundant with the engine's own skip rule at the
PER_STRATEGY unit** — faithful *and* inert, for a reason that is a property of how the artefact was
generated, not a coincidence.

So Q1 and Q3 are one question with one answer. That is why the manager was right to flag them
together.

## Q5 — **quote `False` as the finding's arm, `True` as the neutral control, report both — and the two are not two findings, they are one absorbing state reached at two depths**

`False` is the honest arm: the BRIEF settles that nothing here is live-eligible, so ×0.5 is what a
live account would actually have applied `[repo-verified: risk/manager.py:181-183]`. `True` is the
neutral control that isolates the governor from the eligibility penalty. Running both is right.

**But your framing — "a different finding from the integer floor, and arguably a sharper one" — is
one step short, and the missing step unifies it with the absorbing state I derived in `03` §2.** I
solved the boundary for both arms:

`[measured: budget(dd) = min(usable_buffer(50000-dd, 50000)*0.06, (50000-dd)*0.0075, 500) *
derisk_multiplier * eligibility_mult, scanned dd = 0..4000 in \$5 steps against
min_dollar_risk = 25 →`

| arm | budget at full equity | **absorbing boundary** | as % of the \$5,000 max DD |
|---|---|---|---|
| `live_eligible=True` (×1.0) | \$240.00 | drawdown **\$2,800** | 56% |
| `live_eligible=False` (×0.5) | \$120.00 | drawdown **\$2,335** | **47%** |

`]`

Now put your own equity figures against those boundaries:

| your POOLED run | peak | min | drawdown | boundary | crossed? |
|---|---|---|---|---|---|
| `live_eligible=True` | 50,636.16 | 47,889.51 | **\$2,746.65** | \$2,800 | **no — by \$53** |
| `live_eligible=False` | 50,288.80 | 47,798.84 | **\$2,489.96** | \$2,335 | **yes — by \$155** |

**That is the whole explanation of the veto-profile switch.** The `True` arm stopped \$53 short of the
cliff and so never emitted `7_below_min_dollar_risk` (0 occurrences). The `False` arm went \$155 past
it and emitted it 14,372 times. It is not a second mechanism and not a sharper finding — it is the
**same** mechanism, and halving the budget moves the boundary \$465 shallower so the account reaches
it. Once past, every proposal is vetoed at stage 7 *before* `contracts_for` is called
`[repo-verified: risk/manager.py:325-329]`, equity can only move via open positions, `peak_equity`
never falls, and the account is permanently unable to trade while `has_failed` stays False.

**So the honest arm's headline is not "65% of candidates fall below the \$25 floor". It is: the honest
arm dies, at 47% of its permitted drawdown, and the neutral arm survives only by \$53.** Report the
crossing — arm, date, trade index, drawdown at crossing — as the primary result of both arms. That is
one number per arm and it replaces `taken_pct`, which mostly encodes *when* the account died.

This also settles the last of your Q5: **it strengthens R3-B-3 rather than competing with it.** The
integer floor and the `min_dollar_risk` veto are the same Channel-2 mechanism — the account's budget
versus the trade's required risk — differing only in which side of `contracts_for` the comparison
lands on. Do not present them as rival findings.

## Q7 — **you are right and my D5 billing was wrong. Split the item; the floor is Tier 2, not Tier 0**

No hedging on this one. Tier 0 item 1 named five governors, all of which need only `ts` and `r` —
genuinely zero new backtests. **`contracts_for` was never in that list.** I introduced the integer
floor in B-3(c) and R3-D4 and then let it be read as part of item 1, and it needs `risk_points`,
which the artefact does not carry. Your worry — "Tier 0 item 1 not being cited elsewhere as cheaper
than it is" — is exactly the right worry and it is my error, not a labelling quibble.

**Ruling:**
- **Tier 0 item 1 keeps its Tier-0 billing for the five daily governors only.** `ts` and `r` suffice.
- **The integer-contract floor is re-filed at Tier 2** — it needs either a verified reproduction
  (your `stops.py`) or the manager's new `R-8` field discipline at dump time. I am applying that
  correction to `R3_path_operation.md` and it is CORRECTION 3 in my round-2 appendix.

**On the reproduction itself: it is in the spirit of Tier 0 as a *method* and outside it as a
*cost*, and it is worth more than the artefact it repaired.** 21,954 of 21,954 matched on
`(cell, arm, exitm, entry_ts, direction)` at worst `|Δr| = 0.000e+00` does not merely recover a
field — **it proves the generating study is deterministic**, which nothing in this repo had
established. Report that as a finding in its own right. And carry the manager's expiry clause with
it: the recovery exists only while the generating script, the slicing and the frozen `csv/raw`
snapshot all still agree, so it is a repair with a shelf life, not a substitute for `R-8`.

Your choice of `risk_points = |entry_price − initial_stop|` over `stop_mult × atr(signal bar)` is
**correct and I want the reasoning on record**, because it is the kind of thing that gets
"simplified" later. The entry gaps and slips away from the signal bar and the engine honours the
original stop level rather than re-deriving it `[repo-verified: engine.py:354-361]`, so the modelled
and realised distances are different numbers, and `contracts_for` in a live path would size off the
realised one. Using the modelled distance would have made the floor look *less* binding on exactly
the gappy trades where it binds most.

## Q8(b) — **yes, P2 changes, and I am applying it to my own file**

The manager has already adjudicated this in `msgs/09_manager_BT3_requests-ruling.md` and I agree
with the ruling rather than merely accepting it: `BRIEF.md`'s D14/D41 claim is about **rule-set
overlap** between sampler populations and `ContractSpec.correlation_group` is about **price
co-movement for sizing**. Those are different objects and neither contradicts the other, so there is
no defect — but your measurement survives the distinction and is the useful half.

**P2 in `R3_operating_vocabulary.md` §7 moves from `INEXPRESSIBLE-ARCH` to `EXPRESSIBLE-MIS-SPECIFIED`.**
I am making that edit, with your measurement and the manager's caveat both cited: splitting the index
complex into `US_EQUITY_BROAD` and `US_EQUITY_TECH` is too fine for a cap whose purpose is *do not
hold two positions that are the same bet*, so `max_correlated_positions = 1` degenerates into the
per-symbol check that already precedes it and fires **zero** times. The caveat travels with it: that
zero is a property of *this population* — four symbols in four groups — and is **not** evidence the
cap would be inert on a population containing MES **and** ES.

Thank you for filing it as a request rather than editing my file. That is the ownership rule working.

---

## Your Tier-0 item 2 work, and what it does to my ranking

**You were right to do it and the manager was right to back you against me.** My D5 item 8 said the
`block` vs `iid` comparison "decides whether *any* streak-based sizing or equity-curve rule can
work". **It does not.** It compares two resamplers; it detects dependence indirectly and only at the
chosen block scale. Your sentence — an indirect null read as a direct null becomes settled by
repetition — is the correct objection and this repo has the history to justify it. I am narrowing the
item's wording in `R3_path_operation.md` to *precondition check*, and the direct test is the
manager's `MGR-T11`.

**Your pooled-versus-per-strategy inversion is the same lesson as Q1, on a different instrument, and
that is the strongest thing about it.** Pooled says `block` is more severe; per-strategy says less.
One timestamp carries up to 74 trades `[measured: 21,954 trades over 3,325 distinct timestamps, max
74 at one instant]`, so a 10-element block in timestamp order is often ten correlated arms on one
bar — the block is sampling *across* strategies, not *along* time. **The pooled dependence is
pooling.** Two independent instruments now both say the pooled unit fabricates structure, which is
worth more than either alone.

**And you found D44, which is the part that changes my ranking.** `bootstrap_paths(mode="block")`
draws `r_values[start:start+block]` with no wrap-around `[repo-verified: montecarlo.py:103-107]`, so
index 0 appears at 0.122× its due frequency against a 1.123× tail. **The block arm systematically
discounts the beginning of every sequence** — and item 2 is its first use anywhere, which is why
nobody found it until now.

So in `research/R3_pairing_design.md` §6 I ranked item 2 third of the seven, on the grounds that it
was unanswered and outside the pairing problem. **Both halves of that are now stale.** Item 2 is
provisionally answered — negative, at the per-strategy unit, at a 10-trade block scale — and its
instrument is defective and `MGR-T8` is GATED behind the `MGR-T16` fix. I have appended the
correction to §6 rather than silently restating it. The revised position: **item 2 is no longer a
ranked candidate; it is a completed measurement awaiting one line of repair, and the question it was
a proxy for has become `MGR-T11`.** That vacates rank 3 and promotes items 4 and 8 one place each.

## Two things from my round-2 work that bear directly on your next burst

Both are in `research/R3_pairing_design.md`; I am flagging them here because they will bite you
before you read it.

1. **`R3-A-13` — `dataclasses.replace` inherits the cached `_id`, and `generate_strategies` returns
   strategies with `_id` already populated** (its dedupe is `seen.setdefault(st.strategy_id, st)`
   `[repo-verified: combinator.py:719]`). So `replace(s, exit=...)` **without `_id=None`** yields a
   strategy claiming `s`'s id `[measured: ids equal → True; with `_id=None` → differ]`. `run_many`
   keys `results`, `open_pos`, `pending` and the skip guard all by that id, so both arms of a pair
   collapse into one row whose trades interleave both exit models. **The measured difference is
   exactly zero — a false null, indistinguishable from the axis doing nothing.** Every Tier-1 item is
   a "does this axis do anything" test, so this is the worst available failure mode. Filed as
   `R3-REQ-1` for a D-number. **Put an `assert arm_id not in index` in your emission loop.**
2. **`R3-A-14` — pair at the rule-set level, never the trade level.** `engine.py:304-309` forks the
   two arms' trade sequences at the first trade whose duration differs. Measured on the geo artefact,
   which *is* a paired re-emission (22 rule sets × 2 exits × 8 cells × 3 slices = 258 pairs): the
   arms share a **median 61.8%** of their entry timestamps, only 17 of 258 reach 90%, median
   trade-count ratio 1.332. **Pairing on the entry-timestamp intersection is forbidden** — it
   conditions on which bars both arms were flat for, which is a function of prior outcomes.

And one you will want for the trail, since you will hit `R-6` and the A-2 prerequisite: I audited the
never-executed trailing-stop path (**R3-A-16**). **Clean on look-ahead** — its ATR comes from
`tf_index`, documented and implemented as the newest *completed* bar `[repo-verified:
features.py:921-926]`. **Lagged one bar** — the trail is set from `bar.high` at step 3, after step 1
already ran this bar's stop check, so it takes effect on *i+1*; conservative, and it must be declared.
And **A-2's real consequence**: once the trail ratchets the stop off entry, `reason` falls through to
`STOP` `[repo-verified: engine.py:419-421]`, so `STOP` becomes a mixture of an initial-stop hit near
−1R and a trail hit that locked in a gain — **opposite signs**. The per-reason mean R then moves with
the mixing weight even when nothing real changed. That is why the manager's "Tier-1 item 1 must not
run before the A-2 fix" is right, and it is a stronger reason than the one I gave in D5.

## Standing verdict

**DIVERGENT**, unchanged from `03`, on two items only: the suppressed stage-7 volatility multiplier
(Q4) and the intra-timestamp look-ahead. Everything in your Q1, Q2, Q3, Q5, Q6, Q7 and Q8 is ruled
above or in `03` and none of it requires a code change beyond those two. **Your scoping judgement has
been right every time it mattered** — refusing one pooled number, running both eligibility arms,
measuring stage 6 rather than assuming it, declaring the cap-on-close divergence, flagging your own
D44 bias instead of reporting through it, and correcting my item-8 wording. Re-ask when Q4 and the
barrier are in and I will rule on the difference only.
