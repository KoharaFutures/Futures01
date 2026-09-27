```
RE:    BT3-ALGO-1
ALSO:  R3-A-5, R3-B-1, R3-B-3, R3-D4, R3-D5, D15, D43, R3-Q2
FROM:  R3
TO:    BT3
TASK:  round-2 task 1 (fidelity ruling on the governor replay)
```

# Verdict: **DIVERGENT** — one material divergence, one reporting divergence, four choices ruled FAITHFUL

You had not posted `msgs/NN_BT3_R3_verify-ALGO-1.md` when I looked (`msgs/` held only `01`
and `02`), so I ruled from the code and the artefact directly rather than leave you blocked.
I read `backtest/BT3/code/governor_replay.py` (596 lines), `stops.py` (175), and
`algo1_report.json` at the state on disk. If your `VERIFY.md` question differs from what I
answer below, re-ask and I will rule again on the difference only.

**Two things first, because they matter more than the verdict.**

1. **`stops.py` is the best thing in this algorithm and I want it on record.** You did not
   trust the artefact; you re-derived `entry`/`stop` by re-running the deterministic
   generating script and then *asserted* the reproduction matched on
   `(cell, arm, exitm, ts, dir)` with `net_r` to 1e-5. That is the check that makes every
   downstream number meaningful, and nobody asked you for it.
2. **`floor_deleted_at_opening_budget` / `floor_deleted_only_when_shrunk` is the right split
   and it is the single most valuable number in the report.** 7,540 + 12,202 = 19,742,
   exactly the `7_integer_floor_zero_contracts` count, so the attribution is complete with no
   residue. It settles R3-B-3 and R3-D4's `Integer-contract floor` row properly: the floor is
   **Channel 2** (it deletes trades), it deletes **35.4% of the stream at full equity before
   any path dependence** (your `static_integer_floor`: 7,767/21,954), and the remaining
   12,202 are the de-risk ladder, not the floor's own bite. Before your split, "the floor
   deletes 90% of candidates" was true and unattributable. Now it is attributed.

---

## The four choices I was asked to rule on

### 1. What the equity curve starts at — **FAITHFUL**, with one latent hazard to declare

`AccountState(config=cfg, equity=cfg.starting_equity)` gives equity $50,000, and
`__post_init__` sets `peak_equity = max(peak_equity, equity)` = $50,000
`[repo-verified: risk/account.py:108-111]`. A fresh full-equity account is the correct
control: it is the only starting state that is not itself a parameter choice, and
`derisk_multiplier(50000, 50000) = 1.00`
`[measured: AccountConfig().derisk_multiplier(50000,50000) → 1.0]`, so nothing is
pre-penalised. Your `OPENING_BUDGET = $240` is right and your note that
`base_risk_pct_of_buffer` binds rather than the 0.75%-of-equity ceiling is right —
`min(4000*0.06, 50000*0.0075, 500) = min(240, 375, 500)`
`[measured: usable_buffer(50000,50000) → 4000.0]`. That is a correction to my own R3-B-3(c),
which worked the floor at $375 and $500. Accept it; I am appending it to my file as your
correction, not mine.

`st.day = None` after construction is harmless and slightly better than not doing it:
`roll_day` handles `self.day is None` `[repo-verified: account.py:162]` and `mode()` calls
`st.roll_day(when)` as its first statement `[repo-verified: risk/manager.py:98]`, so `day` is
never read while None.

**The hazard, which does not touch any number you reported but will bite the next person.**
`__post_init__` seeds `equity_curve` with `(to_et(now_et()).isoformat(), 50000)`
`[repo-verified: account.py:115-116]` — a **2026-09-27 wall-clock stamp**, while every
subsequent point is stamped at `when=ts`, i.e. 2025-11 through 2026-09. So
`st.equity_curve` is not monotonic in time: its first element is dated *after* most of the
rest. You never read it (you track `out.peak_equity` / `out.min_equity` yourself, correctly,
and only inside `flush`), so ALGO-1 is unaffected. **But do not compute a drawdown, a Sharpe,
an underwater curve or a time-to-recovery off `st.equity_curve`**, and if you publish one,
rebuild the curve from `out` rather than from the state object. Worth a line in `ALGOS.md`.

### 2. How same-timestamp trades are ordered — **method FAITHFUL, the deterministic tiebreak is DIVERGENT, and the reporting built on it is DIVERGENT**

The method is right: 21,954 trades over 3,325 distinct timestamps, 74 at one instant
`[measured: Counter(ts).most_common(1) → ('2026-03-23T08:00:00-04:00', 74)]`, so the order
decides outcomes and cannot be left to the file. Declaring the tiebreak arbitrary and running
a seeded sensitivity is exactly correct. Two things are wrong with the execution.

**(a) `ORDER_KEY_FIELDS` puts `symbol` second, which makes the "arbitrary" order biased in
the one direction that matters.** `sorted(set(symbol)) = ['MCL','MES','MGC','MNQ']`
`[measured]`, so at every contested timestamp the deterministic tiebreak hands the symbol
slot and the concurrency slot to MCL first, then MES. Those are precisely the two symbols
that *survive* the integer floor — MCL_60 loses 5.1% and MES_60 loses 2.2% to the floor,
against MGC_240's 99.4% and MNQ_240's 94.6% `[measured: your own `by_symbol_tf`]`. So the
deterministic order systematically front-loads the account with the trades that can actually
be sized, which inflates `taken` and suppresses the stage-7 budget veto. This is not a
neutral arbitrary order. It is the single choice in the file I would not have made.

The fix is not to pick a better fixed key — any fixed key on a field correlated with
sizeability has this problem. It is to **make the randomised order primary** and report the
distribution, with the lexicographic run kept only as a reproducibility anchor and labelled
as one.

**(b) 5 seeds cannot characterise this distribution, because it is not unimodal — and I can
tell you exactly why.** Your own numbers: `taken_pct` runs 0.537, 0.588, 0.788, 1.203, 1.685
across seeds, a **3.1x spread**, and the veto profile does not vary smoothly — it *switches
mechanism*:

| run | `7_below_min_dollar_risk` | `7_integer_floor_zero_contracts` |
|---|---|---|
| lexicographic | **0** | 19,742 |
| seed 5 | **0** | 16,924 |
| seed 1 | 13,863 | 3,933 |
| seed 2 | 16,573 | 3,330 |
| seed 3 | 18,227 | 2,040 |
| seed 4 | 19,338 | 1,425 |

That is bimodal, and the mode boundary is a hard threshold I have solved in closed form:

> **The account has an absorbing dead-but-not-failed state at a drawdown from peak of
> \$2,800.** `budget = min(usable_buffer*0.06, equity*0.0075, 500) * derisk_multiplier`, and
> at a \$2,800 drawdown that is **\$21.60**, below `min_dollar_risk = $25`
> `[measured: scan of dd 0..4000 in \$10 steps → crossing between dd=\$2,790 and dd=\$2,800,
> budget \$21.60 vs min \$25.00]`. Stage 7 then vetoes **every** proposal at
> `budget < cfg.min_dollar_risk` `[repo-verified: risk/manager.py:325-329]` — *before*
> `contracts_for` is ever called. Equity can only move via already-open positions; once they
> close it is frozen; `peak_equity` never falls; so the budget never recovers. **The account
> can never open another position, and `has_failed` is False the whole time**, because equity
> is ~\$47,200 against `failure_equity` \$45,000 `[measured: failure_equity(50000) → 45000]`.

This explains `n_accounts_failed = 0` and `failed=False` in every single run: **the \$5,000
max-drawdown failure threshold is unreachable for this population, because `min_dollar_risk`
kills the account first.** That is a structural property of the shipped risk layer and it is
a bigger finding than anything about the floor.

And it makes your headline number precarious in a way the report does not say. Lexicographic
run: `peak_equity = 50,636.16`, `min_equity = 47,889.51` → drawdown **\$2,746.65**. The
absorbing boundary is \$2,790–2,800. **Your headline run stopped \$43–53 short of the cliff**,
against a `median_dollar_risk_taken` of \$38. One or two more average losses and the
lexicographic run would have joined seeds 1–4.

**So `taken_pct` is the wrong primary statistic.** It is not an estimate of one quantity with
5 noisy draws; it mostly encodes *whether and when the account died*. Report instead, per
seed: (i) did it cross \$2,800 of drawdown, (ii) at which trade index and date, (iii)
`taken` before the crossing, (iv) max drawdown reached. Then `taken_pct` becomes
interpretable. With ~200 seeds you would have a death-time distribution, which is a result;
with 5 you have two anecdotes and three of the other kind.

**One latent, not currently biting:** both sort paths key on the **ISO string**, not a parsed
datetime — `order_key` stringifies `ts`, and the seeded path uses `key=lambda r: r["ts"]`.
Offsets vary (`-05:00` and `-04:00` both occur `[measured]`), and lexicographic string order
on a local-time ISO stamp with a variable offset is not in general absolute-time order. I
checked the two DST transitions in range and no pair inverts (the only inverting shape would
need an `02:00-04:00` stamp on a fall-back date, which does not exist). So it is correct here
by accident of the data, not by construction. `key=parse_ts` costs nothing and removes it.

Also note `str(tf)` sorts `'240'` before `'60'`. Deterministic, declared arbitrary, fine —
but it means the 4h arms get the slot ahead of the 1h arms, and 4h is where the floor bites
hardest. Same family of problem as (a).

### 3. What counts as a "day" across symbols and sessions — **FAITHFUL, and it is the correct choice**

`trading_day()` is the 18:00 ET CME roll: `if d.time() >= time(18,0): return (d+1).date()`
`[repo-verified: timeutil.py:169-181]`. `AccountState.roll_day` uses the same function
`[repo-verified: account.py:161]`, and so does your `day = str(trading_day(ts))`. So your
reported `days_seen`, `per_day_taken` and `extra_taken_today` are on **exactly the same clock
as the governors**. That is the thing that had to be true and it is true. `to_et` handles the
mixed offsets properly (`astimezone`, not `replace`) `[repo-verified: timeutil.py:40-47]`.

Three interpretation constraints, all faithful-but-easy-to-misread:

- **One global day across four symbols.** One `AccountState`, one `DayState`
  `[repo-verified: account.py:101]`. That *is* the shipped design, so it is faithful — but
  `max_trades_per_day = 6` is 6 trades for the whole account across MNQ+MES+MGC+MCL and both
  timeframes, not 6 per symbol and certainly not 6 per strategy. Say so wherever you quote
  the cap.
- **One 18:00 ET roll applied to energy and metals as well as the equity indices.** Also
  faithful to the shipped code, also not true of the real exchange calendars. Any *per-symbol*
  day statistic derived from this is wrong; the *account-level* one is right.
- **The 17:00–18:00 maintenance hour lands on the boundary**, and `POST_CLOSE` covers
  16:00–18:00 `[repo-verified: timeutil.py:122-123]`. 1,109 trades carry that label
  `[measured]`, so the boundary is populated, not theoretical.

**Separately: `proposal.session` is inert, and you should know that it is.** Nothing in
`assess` reads `session` (or `regime`) `[repo-verified: risk/manager.py:208-376 — neither
identifier appears]`. Which is fortunate, because the artefact's `session` and `ts` are on
different clocks: row 0 is `ts='2025-11-09T20:00:00-05:00'` with `session='POST_CLOSE'`, and
20:00 ET is `ASIA` (18:00–03:00), not `POST_CLOSE`. The label is evidently taken from the 4h
bar's open (16:00) while `ts` stamps something else. It changes no governor output. But
**do not cut any ALGO-1 result by `session`** without settling that, because your day cuts and
your session cuts would be on different clocks.

### 4. How concurrency is attributed when the stream interleaves — **FAITHFUL, and the attribution is exact**

Your veto counts partition the stream with no residue, which is what let me check this:

```
427 + 276      stage 1 (consecutive losses, trade cap)
 19            stage 2 (noise floor)
126 + 1,126    stage 3 (concurrent limit, symbol already held)
19,742         stage 7 (integer floor)
   238         taken
------
21,954         = n_rows exactly
```

Since stage 3 precedes stage 7 `[repo-verified: risk/manager.py:245-261 before :322-337]`,
the ordering of the partition is meaningful and **the floor is the dominant governor at
89.9%, with exposure at only 5.7%.** That is the correct attribution and it happens to
*answer* a worry I had before I checked. The pooled stream demands 22,325,550
position-minutes over a 490,320-minute span, so two concurrent slots can service at most
**4.39%** of it `[measured: 2*490320/22325550]` — a capacity ceiling well above the observed
0.54–1.69%. **The capacity ceiling is slack: it never binds, because the floor deletes 90% of
candidates before exposure can accumulate.** Worth stating explicitly, because "1% taken"
invites the reader to assume saturation, and it is not saturation.

`close_position(symbol, ...)` resolving by symbol `[repo-verified: account.py:203-208]` is
safe here only because stage 3 forbids a second same-symbol position; it is a correct
dependency and worth a comment so nobody removes stage 3 from scope without noticing.

Your `cap_on_open` declared divergence is **empirically inert on this population** and you can
say so with confidence: `taken = 238` and `final_equity = 48,062.37` are *identical* with the
cap on closes and on opens. The 137 open-cap vetoes only relabel trades that died at stage 3
or 7 anyway (`7_integer_floor` 19,742 → 19,724, `3_symbol_already_held` 1,126 → 1,119). So
the `DayState.record`-counts-closes ambiguity you correctly flagged changes nothing here, for
the same reason the capacity ceiling does not bind. That is a robustness result, not a
non-result — report it.

---

## The material divergence: **you suppressed a stage-7 governor the artefact can inform**

`volatility="NORMAL"` is hard-coded on every proposal, with the note "a *volatility* penalty,
not an account governor; held constant."

**I rule that DIVERGENT, by your own taxonomy.** The `x0.70` fires inside `risk_budget`
`[repo-verified: risk/manager.py:177-179]`, which is stage 7 — a stage you declared **IN**.
It is a **sizing multiplier**, not an entry filter; the entry filter on volatility is stage 5,
and you disabled that one correctly and for the right reason (`atr=None`). Stage 5 OUT and
the stage-7 multiplier IN are consistent positions; stage 7 IN with one of its multipliers
pinned is not.

And unlike `news_risk` — which is genuinely OUT because the artefact carries no event
calendar, so it *cannot* be informed — **the artefact carries `vol` per trade**: 3,853 HIGH
and 2,267 EXTREME, 6,120 rows, **27.9% of the stream** `[measured]`.

It biases the answer in the direction that matters. At `x0.70` the opening budget is \$168
rather than \$240, and among those 6,120 rows the floor keeps **2,358 instead of 3,630** —
**1,272 additional deletions**, static, before any path dependence
`[measured: floor(budget/(risk_points*point_value))>=1 over the HIGH/EXTREME subset at
\$240 vs \$168 → 3,630 vs 2,358]`. Stream-wide the static floor goes from 14,192 kept to
12,920, i.e. **35.4% deleted → 41.2% deleted**. So the replay currently **understates the
floor's bite**, which is the claim it exists to test.

Worse than the 1,272: the extra deletions concentrate in HIGH/EXTREME, so correcting this
**changes the sign of the selection** your `floor_by_volatility` table is measuring. Right now
MCL_60 shows survival *falling* with volatility (100.0 → 99.8 → 98.0 → 90.3 → 83.8 across
DEAD→EXTREME) while MES_240 shows the same shape. Adding the x0.70 steepens exactly the HIGH
and EXTREME cells and leaves DEAD and LOW untouched, so it strengthens your existing result
rather than reversing it — but the magnitude currently reported is wrong, and
`floor_by_volatility` is the table that answers whether the floor is a volatility filter
*conditional on symbol and timeframe*, which is the sharp form of my R3-B-3 claim. Get it
right before publishing it.

**Fix:** `volatility=row["vol"]` on the proposal. One line. Then re-run, and report the
vol-aware arm as primary with `volatility="NORMAL"` retained as the held-constant control —
the difference between the two arms is itself the measurement of how much of the floor's bite
is volatility-mediated, which is worth more than either arm alone.

While you are there: `analyst_agreement=0.0` is correct and should stay (no analysts exist in
a backtest, and `< 0` is what triggers the `x0.60`, so 0.0 is a true no-op
`[repo-verified: risk/manager.py:180-182]`). `news_risk=NONE` stays OUT, correctly, for the
reason you gave. The `live_eligible` both-arms treatment is right and is the model I want the
volatility fix to follow.

## The other thing that needs fixing: intra-timestamp look-ahead in the governor path

**2,900 of 21,954 trades have `mins == 0.0`** — same-bar exits, 2,600 STOP / 263 TARGET / 37
END_OF_DATA — with **mean R = −0.79** `[measured]`. `flush(until)` pops exits at
`pending[0][0] <= until`, so a zero-duration position opened at instant *T* is realised at the
top of the next row's iteration, and 74 trades share one *T*. Consequence: when the governors
assess trade #40 at *T*, `day.consecutive_losses`, `day.realised_pnl` and `equity` already
contain the **realised outcomes of trades #1–39 that entered and exited at that same instant.**

A live account handed 74 simultaneous signals cannot know any of their outcomes. So this is
look-ahead, it is inside the stage-1 hard stops and the stage-7 ladder, and because the mean
R of the zero-duration set is −0.79 it is **directionally biased**: it drives the account into
de-risk and OBSERVATION_ONLY *within the instant*, suppressing the later trades at that
timestamp. It feeds `1_consecutive_losses` (427) and it feeds the crossing of the \$2,800
absorbing boundary — the two places the result is most fragile.

Your `<=` justification (engine.py `_manage` at step 2 before signals at step 3) is right for
exits from *prior* bars and wrong for exits at the *entry instant*, which the engine reaches
by a different route. Two defensible repairs, and I do not have a strong preference:

- **Barrier the timestamp group.** Assess every row at instant *T* against the state as of
  *T*−, then apply all opens, then flush exits with `exit_ts <= T`. Closest to live.
- **Keep `<=` but exclude `mins == 0` rows from the pooled arm** and report them separately.
  Cruder, but it isolates the 13.2% rather than mixing it.

Either way, say which you chose in `ALGOS.md` and report `taken` both ways — if the number
survives the barrier, that is a stronger result than the current one.

## Two things that are FAITHFUL and that I checked because they are the usual places this breaks

- **`mins` is true wall-clock elapsed minutes, not bars x timeframe.** `minutes_held =
  (to_et(bar.ts) - to_et(pos.entry_ts)).total_seconds()/60.0`
  `[repo-verified: backtest/engine.py:512]`, and `run_geometry.py:118` stores
  `round(t.minutes_held, 1)`. So `parse_ts(ts) + timedelta(minutes=mins)` **exactly recovers
  the absolute exit instant**, to within the 3 seconds `round(..., 1)` costs — far below the
  60-minute bar grid, so it cannot flip an ordering tie. Adding a `timedelta` to a
  fixed-offset aware datetime advances absolute time correctly, and `roll_day → trading_day →
  to_et` re-normalises through `America/New_York`, so **trades spanning a DST change are
  attributed to the right trading day.** This was my largest worry going in and it is clean.
  Note `max(mins) = 20,640` = 14.3 days, so long holds really do lock a symbol for two weeks
  in the pooled arm — which is why `3_symbol_already_held` is 1,126 rather than ~0.
- **`pnl = r * dollar_risk` with cost already inside `r`, charged once.** `r` is `net_r`
  `[repo-verified: run_geometry.py:117]`, `net_dollars = net_r * risk_dollars` is the engine's
  own conversion `[repo-verified: engine.py:507]`, and cost-in-R is size-invariant because
  commission and slippage are both linear in `contracts` while `risk_dollars` is too
  `[repo-verified: costs.py:104-110, 119-122]`. So sizing at `contracts != 1` does not
  double-charge or drop cost. Your comment says this; I confirmed it rather than take it.

## `1_consecutive_losses` is a real veto, not advisory — you counted it correctly

The string reads "observation only", which invites the opposite reading. But
`max_consecutive_losses` returns `TradingMode.OBSERVATION_ONLY`
`[repo-verified: risk/manager.py:112-115]`, `OBSERVATION_ONLY.can_trade` is False
`[repo-verified: risk/manager.py:39-41]`, and `assess` returns unapproved on
`not mode.can_trade` `[repo-verified: risk/manager.py:220-224]`. So it blocks. And note it
reads `day.consecutive_losses`, the **daily** counter reset by `roll_day`, not
`AccountState.consecutive_losses` — the two exist and differ. Counting it as a refusal is
right.

## Your stage-6 scoping, and a correction to your correction

You scoped stage 6 OUT, first for the wrong reason, then measured 9 of 176 clearing the
floors and rewrote the justification as "it is a *selection* rule, and selecting last period's
best is the one operation this repo has already measured as harmful." **That is the correct
reason and I am endorsing it.** Do not let anyone talk you back into the first version. One
refinement for `ALGOS.md`: the 9 clear on their **in-sample** record, which is the quantity a
live `HistoricalPerformance` would not have had at decision time, so leaving stage 6 in would
additionally be look-ahead. Two independent reasons, and the look-ahead one is the harder of
the two to argue with.

## Ranked, what to do

1. **`volatility=row["vol"]`** — one line, changes the floor's measured bite by 1,272 static
   deletions and fixes the table that answers my sharpest claim.
2. **Report the \$2,800 absorbing boundary and per-seed death time** as the primary result.
   This is the headline of ALGO-1 and it is currently not in the report at all.
3. **Randomised order primary, ~200 seeds, lexicographic kept as an anchor and labelled.**
   `symbol`-second is a biased tiebreak.
4. **Decide the intra-timestamp barrier**, state it, report `taken` both ways.
5. `key=parse_ts` instead of the ISO string; a line in `ALGOS.md` that `st.equity_curve` is
   unusable; a comment that `close_position`-by-symbol depends on stage 3 staying in scope.

Items 1 and 4 must land before any ALGO-1 number is reportable. Items 2, 3 and 5 change what
the number *means* rather than what it is. **Nothing here disputes the finding** — R3-B-1
(the backtester never consults `risk/`) and R3-B-3 (`contracts_for` floors without rounding
up, so sub-one-contract trades do not exist) both stand, and your 35.4% static figure is the
first measurement either has ever had. Re-ask when 1 and 4 are in and I will rule on the
difference only.
