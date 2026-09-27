# R3 — The D15 pairing design for the eight §7-Q2 items

**Round 2, task 2.** My §7 Q2 returned 8 items against DIVISION §6's pre-registered ceiling of
2, with a caution attached that nobody has since solved: only **93 of 8,317** shipped rule sets
exist with two different exits `[repo-verified: workspace/studies/DEFECTS.md:184-187 (D15)]`, so
each item must be a **paired re-emission of the same rule sets** or the answer is confounded
with the entry. This file specifies how the pairing is actually done.

Item **1** (replay the governors) is excluded — it is running as BT3-ALGO-1 and I ruled on it in
`msgs/03_R3_BT3_re-verify-ALGO-1.md`. Items **2–8** are the subject here.

Claim markers are per DIVISION §3. `[repo-verified: path:line]`, `[measured: command → result]`,
`[general knowledge]`.

---

## 0. The answer, up front

**A clean paired re-emission is achievable today, with zero library changes, and the eight items
are NOT blocked on a generator change.** R3-A-5 is correct — `generate_combinations` passes
`template.filters` through unchanged `[repo-verified: combinator.py:581]` and there is no
enumeration over operating axes anywhere in the generator — but that does not block anything,
because **you do not need the generator to enumerate the axis.** You take the generator's output
and re-emit it with `dataclasses.replace`. The combinator itself already does this
`[repo-verified: combinator.py:694]`.

What *is* blocked, and what I did not know when I wrote §7 Q2:

1. **One keyword argument stands between this design and a silent false null.** See §2 — new
   finding **R3-A-13**. Omit `_id=None` and both arms of every pair merge into one
   `BacktestResult`, which reads as "the axis does nothing" and is indistinguishable from a real
   null. Every one of the seven items is a "does this axis do anything" test, so this is the
   worst possible failure mode for this exact programme.
2. **Trade-level pairing is not available on this engine for any axis.** Not for a single one of
   the seven. See §4 — new finding **R3-A-14**, with the magnitude measured in §4.3: in the one
   paired re-emission that already exists on disk, the two arms of a pair share a **median of
   61.8%** of their entry timestamps. The unit of pairing is therefore the **rule set**, never the
   trade. That changes which statistic is legitimate, not whether the test can be run.
3. **The confound is total, not severe, at the scale a researcher can actually run.** D15 measured
   93 of 8,317. At `max_total=400`, **0 of 314** rule sets carry two exits, and **0 of 314** carry
   two filter scopes `[measured: see §1.2]`. New finding **R3-A-15**. So the paired population
   must be *constructed*; there is no subset of the shipped population to salvage.

And the sentence the manager asked for, stated plainly here and justified in §6:

> **Yes. Items 3 ("half off at 1R, breakeven, trail the rest") and 4 (the trailing stop has
> never run) can both be paired cleanly.** They are gate-identical axes (§4.1), they share an R
> denominator with their control, and they belong in the same 2³ factorial (§6.1). Item 4 carries
> one hard prerequisite — the 4-line `ExitReason.TRAIL` fix — and §5.1 explains why that is a
> prerequisite rather than a nicety.

---

## 1. What "the same rule set" means, exactly

### 1.1 The identity that has to be held fixed

`Strategy.strategy_id` is a sha1 over **nine** parts `[repo-verified: base.py:607-623]`:

```
1  symbol
2  str(primary_tf)
3  group
4  "|".join(sorted(c.label for c in conditions))
5  exit.identity
6  filters.identity
7  "".join(sorted(d.value for d in allowed_directions))
8  ",".join(str(t) for t in sorted(confirm_tfs))
9  str(execution_tf or "") + "|".join(sorted(c.label for c in trigger_conditions))
```

Two facts about this that the pairing depends on:

- **`name` is not in the hash.** Two strategies differing only in `name` are the same object to
  `run_many`. So you cannot label an arm by renaming it; the label must live outside the
  `Strategy`.
- **`exit.identity` and `filters.identity` are both built from `dataclasses.fields`**
  `[repo-verified: base.py:249-265, 460-478]`, which is what the `ExitModel.identity` fix and
  then D43 established. So **every** behavioural field of `ExitModel` and `StrategyFilters` is in
  the hash, including the four this design varies (`scale_out`, `trail_atr_mult`,
  `time_stop_bars`, `stop_kind`) and the four D43 rescued (`rth_only`, `days_of_week`,
  `min_minutes_since_open`, `max_minutes_since_open`). **Post-D43, the two arms of every pair in
  this design are guaranteed distinct ids — provided §2 is respected.** Pre-D43 the filters-scope
  arms would all have collided, which is why item 7 was untestable before that fix and why
  nobody has tested it since.

**The pair key** is therefore the same nine parts with the varied slot blanked:

```python
def pair_key(s, varied):            # varied in {"exit", "filters"}
    parts = [s.symbol, str(s.primary_tf), s.group,
             "|".join(sorted(c.label for c in s.conditions)),
             "<VARIED>" if varied == "exit"    else s.exit.identity,
             "<VARIED>" if varied == "filters" else s.filters.identity,
             "".join(sorted(d.value for d in s.allowed_directions)),
             ",".join(str(t) for t in sorted(s.confirm_tfs)),
             str(s.execution_tf or ""),
             "|".join(sorted(c.label for c in s.trigger_conditions))]
    return hashlib.sha1("::".join(parts).encode()).hexdigest()[:12]
```

**But do not rely on it as the primary mechanism.** It reimplements a hash that lives in
`base.py`, and a field added to `Strategy` later would desynchronise the two silently — the same
class of defect as `ExitModel.label` and D43, for the third time. **Primary mechanism: carry the
pairing explicitly in a side table, built at emission time**, where it cannot drift:

```python
# arms: list[Strategy] handed to run_many;  index: arm_id -> (pair_id, arm_label)
arms, index = [], {}
for ctrl in generate_strategies(sym, tfs, max_total=400):
    pid = ctrl.strategy_id                      # the CONTROL's id IS the pair id
    for label, treat in emit_arms(ctrl):        # includes the control, label "CTRL"
        assert treat.strategy_id not in index, "arm id collision — see R3-A-13"
        index[treat.strategy_id] = (pid, label)
        arms.append(treat)
```

The control's own `strategy_id` is the pair id. It is stable, it is already computed, and the
`assert` is what turns R3-A-13 from a silent false null into a crash. **Keep the assert.** Use
`pair_key` only as an independent cross-check that the two mechanisms agree.

### 1.2 R3-A-15 — at the reachable scale the confound is total, not partial

D15's 93/8,317 invites the reading that a small paired subset exists and could be used. At the
generation size I am permitted to run, it does not:

`[measured: generate_strategies(sym,[5,15,60,240],max_total=400), rule sets counted by the
nine-part hash with one slot blanked →`

| symbol | strategies | distinct ids | rule sets with ≥2 exits | rule sets with ≥2 filter scopes | distinct exits used |
|---|---|---|---|---|---|
| MGC | 314 | 314 | **0** | **0** | 8 of 11 |
| MNQ | 314 | 314 | **0** | **0** | 8 of 11 |
| MES | 336 | 336 | **0** | **0** | 9 of 11 |
| MCL | 296 | 296 | **0** | **0** | 9 of 11 |

`]`

Every generated strategy is its own unique rule set, carrying exactly one exit and exactly one
filter scope. **There is no paired subset to find.** Two consequences, both good:

- The paired population must be constructed by re-emission. That is what §2 does.
- **n_pairs = the full generated population**, because every strategy contributes one pair:
  **314 / 314 / 336 / 296 = 1,260 pairs across the four symbols.** That is a serviceable n for a
  rule-set-level paired test, and it is far larger than the 93 D15 leaves on the table.

The zero in the filters column is R3-A-5 restated as its consequence rather than its cause:
the generator's scope vocabulary being inert means not just "scope is never varied" but
"**no two shipped strategies are ever a scope pair**", which is the form that matters for item 7.

---

## 2. R3-A-13 (NEW) — `dataclasses.replace` inherits the cached `_id` and silently merges both arms

**This is the single most dangerous thing in this design and it is one keyword argument.**

`Strategy._id` is a real dataclass field with default `None`
`[repo-verified: base.py:585]`, and `strategy_id` memoises into it via
`object.__setattr__(self, "_id", ...)` `[repo-verified: base.py:622]`. `dataclasses.replace`
copies every field, **including `_id`**. So a `replace` performed after `strategy_id` has been
read produces a strategy that *claims the original's id*.

And `generate_strategies` has already read it. Its dedupe step is
`seen.setdefault(st.strategy_id, st)` `[repo-verified: combinator.py:719]`, so **every strategy
the generator returns arrives with `_id` already populated**:

`[measured: S = generate_strategies('MGC',[5,15,60,240],max_total=400); S[0]._id →
'MGC-15m-668c0ed86d86' before anything touches strategy_id]`

`[measured: replace(S[0], exit=replace(S[0].exit, trail_atr_mult=2.0)).strategy_id ==
S[0].strategy_id → True]`

`[measured: replace(S[0], exit=replace(S[0].exit, trail_atr_mult=2.0), _id=None).strategy_id
!= S[0].strategy_id → True]`

### What happens when a pair collides

`run_many` keys three separate structures by `strategy_id`:

- `results = {s.strategy_id: BacktestResult(...) for s in strategies}`
  `[repo-verified: engine.py:277-281]` — a dict comprehension, so the two arms produce **one**
  row, and its `strategy_name` is whichever arm came later in the list.
- `open_pos` and `pending`, both `Dict[str, ...]` keyed by `sid`
  `[repo-verified: engine.py:282-283]`.
- the skip guard `if sid in open_pos or sid in pending: continue`
  `[repo-verified: engine.py:304-309]`.

So a colliding pair does not produce two comparable results and it does not produce two
independent trade streams either. **Whichever arm signals first blocks the other for the whole
holding period, `_manage` applies that arm's exit model to the position, and the trade is
appended to the shared row.** The output is one mongrel result whose trades are a
path-dependent interleaving of both arms' exits, labelled with one arm's name, and **the measured
difference between arms is exactly zero because there is only one row to difference.**

A false null. Indistinguishable from "the axis does nothing". On a programme whose every item
asks "does this axis do anything".

This is the third instance of the identity-collision family — `ExitModel.label`, then D43's
`StrategyFilters.label`, now the `_id` cache — and it is **not fixed by D43**, because D43
repaired what goes *into* the hash and this defeats the hash entirely by not recomputing it.
I have filed `R3-REQ-1` asking the manager for a `D<n>` number.

### The rule, stated so it cannot be got wrong

> **Every `replace` on a `Strategy` in this design passes `_id=None`. Every emission loop carries
> the `assert treat.strategy_id not in index`. No exceptions.** A `replace` on the inner
> `ExitModel` or `StrategyFilters` is not enough — those have no `_id` and recompute their
> `identity` correctly; it is the outer `Strategy` that caches.

---

## 3. The emission recipe

Zero library changes. `generate_strategies` at `max_total<=400` is the source of control arms.

```python
from dataclasses import replace
from futures_agents.strategies.base import ExitModel, StopKind, StrategyFilters
from futures_agents.strategies.combinator import generate_strategies

def arm(ctrl, label, *, exit_delta=None, filters=None):
    """One arm of a pair. Never called without _id=None."""
    ex = replace(ctrl.exit, **exit_delta) if exit_delta else ctrl.exit
    fl = filters if filters is not None else ctrl.filters
    return label, replace(ctrl, exit=ex, filters=fl, _id=None)

def emit_2x2x2(ctrl):
    """Items 4, 5, 6 as main effects + item 3 as the all-on cell. 8 arms."""
    for trail in (None, 2.0):                                   # item 4
        for runner in (False, True):                            # item 5
            for tstop in (ctrl.exit.time_stop_bars, None):      # item 6
                so = ctrl.exit.scale_out
                if runner:
                    so = tuple(list(so[:-1]) + [0.0]) if len(so) > 1 else (0.8,)
                yield arm(ctrl, f"T{int(trail or 0)}_R{int(runner)}_S{int(tstop is None)}",
                          exit_delta=dict(trail_atr_mult=trail, scale_out=so,
                                          time_stop_bars=tstop))
```

Four points of care in that snippet, each of which is a place a silent divergence would live:

- **`scale_out` must be edited relative to the control, not replaced with a literal.** The
  eleven catalogue exits carry five different ladder shapes — `(0.5,0.3,0.2)`, `(0.6,0.4)`,
  `(0.4,0.3,0.3)`, `(1.0,)`, `(0.5,0.5)` `[measured: expand_exit_models(include_structure=True,
  include_aggressive=True, include_anchored=True) → 11 exits, all five shapes summing to exactly
  1.0]`. Substituting one literal across all rule sets changes the ladder *and* the runner in one
  move, which reintroduces the confound the pairing exists to remove. Zeroing the **last**
  fraction leaves the ladder's earlier rungs untouched, which is the minimal edit, and
  `__post_init__` permits it — it checks `sum(scale_out) > 1.0 + 1e-9` only
  `[repo-verified: base.py:235-236]`.
- **`targets_r` must not be touched by items 4/5/6.** My D5 item 4 literal set
  `targets_r=(1.0,)`, which is a *fourth* change riding along with the three. Keep it out of the
  factorial; if the full recipe's `targets_r=(1.0,)` is wanted it is a separate arm and must be
  labelled as a fourth factor, not folded in.
- **`breakeven_at_r=1.0` in the D5 literal is not a change at all** — it is the `ExitModel`
  default `[repo-verified: base.py, field default]` and 6 of 11 catalogue exits already carry it
  `[measured]`. Do not count it as a factor; do record each rule set's control value of it,
  because the residual runner's fate depends on it.
- **`scale_out=(0.8,)` for a single-rung control** is a judgement I am making explicit: exit 3 of
  the catalogue (`ATRx1.2->1.2R`) has `scale_out=(1.0,)`, so "leave a residual" has no earlier
  rung to shrink. `(0.8,)` invents a 0.2 residual. That is a *different* intervention from
  zeroing a third rung, so **the 1-rung rule sets must be reported as their own stratum**, not
  pooled with the 2- and 3-rung ones.

For item 7 the same `arm()` helper is used with `filters=` instead, and the control arm is
`ctrl.filters` unmodified, which is `rth_only=True` and every other field `None` — **one distinct
identity across all 314** `[measured, R3-A-5]`, so the control is genuinely uniform.

---

## 4. R3-A-14 (NEW) — the unit of pairing is the rule set, never the trade

This is the part the eight items were silently assuming away, and it is why I am glad the design
was demanded before the runs.

### 4.1 Exactly which `ExitModel` fields can change the entry set

An exit model reaches the entry decision only through `Strategy.evaluate`, which can return
`None` at four exit-dependent points `[repo-verified: base.py:717-742]`:

```
717-719  stop = self.exit.stop_price(...);  if stop is None or |entry-stop| < tick_size: None
722      if |entry-stop| < spec.min_stop_ticks * tick_size: None      # the noise floor
726      targets = self.exit.target_prices(...);  if not targets: None
740-742  if target_kind is not R_MULTIPLE and reward/risk < min_reward_risk: None
```

Reading those against the field list gives a clean three-way split:

| `ExitModel` field | can it change the entry set? | via |
|---|---|---|
| `stop_kind`, `stop_mult`, `stop_pad_ticks` | **Yes, always** | 717-719 and the noise floor at 722 |
| `target_kind`, `anchor_mult`, `min_reward_risk` | **Yes, but only when `target_kind is not R_MULTIPLE`** | 740-742 |
| `targets_r` | **No** | the `if not targets` gate at 726 is **unreachable**: `__post_init__` forbids empty `targets_r` `[repo-verified: base.py:229-230]` and the R_MULTIPLE branch returns one price per element `[repo-verified: base.py:339]`, while an anchored kind that finds no anchor falls back to that same branch `[repo-verified: base.py:333-339]` |
| `scale_out`, `breakeven_at_r`, `trail_atr_mult`, `time_stop_bars`, `exit_at_session_close` | **No** | read only inside `_manage` `[repo-verified: engine.py:382-476]`; they appear nowhere in `evaluate` |

So the seven items split into three pairing classes:

- **Gate-identical** — items 3, 4, 5, 6. Given the same flat state at bar *i*, both arms emit the
  identical signal, with the identical `entry`, `stop` and `targets`. The R denominator
  (`risk_points`) is identical.
- **Gate-different, unit-identical** — item 7. `filters.passes` runs as the *first* statement of
  `evaluate` `[repo-verified: base.py:660-662]`, before any condition, so the arms deliberately
  see different bars. The R denominator is still identical on any bar both arms take.
- **Gate-different, unit-different** — item 8. `stop_kind=FIXED_TICKS` changes `stop_price`,
  which changes both the entry gate *and* `risk_points`. **The two arms do not share an R unit**,
  so R is not a comparable quantity between them. §5.4.

### 4.2 Gate-identical does not mean trade-identical, and the culprit is `engine.py:304-309`

`if sid in open_pos or sid in pending: continue` `[repo-verified: engine.py:304-309]` — a
strategy holding a position does not look for signals. So **any axis that changes holding
duration changes which later bars the strategy is flat for**, and every one of items 3–6 changes
holding duration; that is what they are for.

The consequence is sharp: **the two arms of a gate-identical pair agree on trade 1 and then
fork at the first trade whose duration differs.** After that their trade sequences are different
index sets, and matching trade *k* of arm A to trade *k* of arm B is matching two different
events.

Pairing on the **intersection** of entry timestamps is available but is not clean, and it is worth
saying why rather than just forbidding it: the intersection is the set of bars on which *both*
arms happened to be flat, which is determined by both arms' prior exits, which is determined by
prior outcomes. **Conditioning on the intersection conditions on the past of the very series
being tested.** It is a selection on the dependent variable. Do not do it.

### 4.3 How large is the fork? Measured, on the one paired re-emission that already exists

`workspace/strategy_research/scratch/geo_trades.json` is, structurally, exactly the design
this file specifies: **22 rule sets × 2 exits** per cell, the two exits differing only in
`stop_mult` (1.0 vs 1.5) `[repo-verified: workspace/roundtable/backtest/BT3/code/stops.py:56-64,
copied verbatim from run_geometry.py:53-65]`, over 8 symbol-timeframe cells × 3 disjoint slices
= **258 pairs**. So the fork can be measured rather than argued.

`[measured: over the 258 (symbol, tf, slice, arm) pairs in stops_cache.json, comparing the
entry-timestamp sets of exitm='atr1.0' and exitm='atr1.5' →`

| quantity | result |
|---|---|
| entry-timestamp Jaccard, median | **0.618** |
| Jaccard, mean / min / max | 0.637 / 0.333 / 1.000 |
| pairs reaching Jaccard ≥ 0.90 | **17 of 258** |
| pairs below Jaccard 0.50 | 39 of 258 |
| trade-count ratio \|A\|/\|B\|, median (min, max) | **1.332** (1.000, 2.000) |
| per-strategy occupancy (position-minutes / slice span), median | 0.193 |
| occupancy p90 / max | 0.717 / 0.860 |
| strategy-slices positioned > 50% of the time | **125 of 516** |

`]`

**Two arms of the same rule set, varying one exit field, share under two-thirds of their
entries.** The tighter stop takes 33% more trades at the median and twice as many at the worst.
That is `stop_mult`, a gate-*different* axis, so part of the 38% divergence is the noise-floor
gate at base.py:722 and part is the skip rule — and I cannot decompose them, because the
instrument that would (`signals_skipped_in_position`, my D5 item 9, one line at engine.py:308) is
**declared and never assigned** `[repo-verified: R3-A-4]`. But the magnitude settles the design
question on its own, and the occupancy row explains it: a quarter of strategy-slices are
positioned more than half the time, so the skip rule has ample opportunity to fork the sequences.

### 4.4 What this permits and forbids

**Permitted, today, zero new code:** one statistic per arm per rule set, differenced within the
pair, aggregated across rule sets. **n = 1,260 pairs** across four symbols (§1.2), and a
distribution-free paired test on the per-rule-set differences — Wilcoxon signed-rank, or a paired
bootstrap over rule sets. Name the test, per PIPELINE §4. **Never route it through `T.ab`**, which
inflates z roughly 3.3× `[repo-verified: workspace/studies/DEFECTS.md, D28]`.

**Forbidden:** per-trade paired tests, ΔR per matched trade, and anything computed on the
entry-timestamp intersection.

**What would unlock trade-level pairing**, for the record, since it is the strongest design and it
is out of reach: an **exogenous-entry replay harness** — run the control arm, harvest its
`(entry_index, entry_price, direction)` triples, and drive `_manage` over each treatment arm's
exit model from those fixed entries. That holds the population *exactly* fixed and reduces the
comparison to the pure exit effect. It is a new code path, not a configuration change, so it is
outside the "zero new code" framing of Tier 1 — but it is the single highest-leverage harness on
my track and I have filed it as `R3-REQ-2`. Note it is blocked on nothing except being written:
`_manage` already takes `(pos, i, bar, is_last)` and needs no `FeatureSnapshot`
`[repo-verified: engine.py:377-378]`, which is the same fact that makes condition-based exits
impossible (R3-Q3's subject) and makes *this* harness easy.

---

## 5. The control arm, per channel

My B-3 decomposition says Channel 1 is a variance transform, Channel 2 changes the conditioning
set, Channel 3 is a deterministic cost subtraction, Channel 4b moves expectancy only if
`Cov(w,R) ≠ 0`. **A test of a Channel-1 axis needs a different control from a Channel-3 one**,
and here is what each needs.

### 5.1 Channel-1 axes (items 3, 4, 5) — the control must prove the axis FIRED

For a Channel-1 axis the null hypothesis *is* the prediction: shape moves, expectancy does not
`[settled: BRIEF.md rule 3, measured 4×]`. So a null result is expected, and an axis that was
silently inert produces **the same null**. The two must be separable or the test measures nothing.

**Every Channel-1 arm therefore carries a positive control: a counter proving the axis engaged
on a non-trivial fraction of trades.**

- **Item 4** — count trades whose exit stop differs from `initial_stop` and from the breakeven
  level. This is not available today, and that is the whole of why the `ExitReason.TRAIL` fix is a
  **hard prerequisite** rather than a nicety. I audited the never-executed path to be sure:
  `reason = BREAKEVEN if pos.breakeven_moved and |pos.stop - entry| < tick_size else STOP`
  `[repo-verified: engine.py:419-421]`. Once the trail ratchets the stop away from entry, that
  condition fails and **a trail exit reports as `STOP`** — R3-A-2, confirmed at the line. So with
  the trail on, `STOP` becomes a **mixture of two mechanisms with opposite signs**: an initial-stop
  hit near −1R, and a trail hit that has locked in a gain. Every exit study in this repo reads the
  exit-reason histogram and its per-reason mean R. **That mean moves with the mixing weight even
  if nothing real changed**, so item 4 run without the fix produces a number that cannot be
  attributed. Four lines, per D5 item 13.
- **Item 5** — count trades closing with `remaining > 1e-9`, and report the residual fraction
  distribution. `_close(..., already_flat=True)` fires only when `pos.remaining <= 1e-9`
  `[repo-verified: engine.py:441-443]`, so a residual arm that never leaves one is detectable.
- **Item 6** — the `TIME` exit count must go to **exactly zero** in the treatment arm. That is the
  cleanest positive control on the list: `time_stop_bars=None` short-circuits at
  `if exit_model.time_stop_bars and ...` `[repo-verified: engine.py:465-466]`, so a non-zero TIME
  count in the treatment arm is a wiring bug, full stop.

**Also required for Channel 1: report the shape, not just the mean.** If expectancy is flat and
win rate and payoff have both moved, that is the Channel-1 prediction confirmed and it is a
*result*. If expectancy is flat and nothing moved, the axis was inert. The current ranking metric
cannot tell those apart, which is D5 item 10's underlying problem in a different costume.

### 5.2 Channel-2 axes (item 7) — the control must hold the cost of selection constant

Item 7 changes *which* bars become trades, by design, so the arms have different *n*. My B-3
Channel-3 analysis says total cost paid is `N × c`, so **any rule that reduces N reduces total
cost linearly without changing per-trade `E[R]`** — and the per-trade ranking metric is
structurally blind to that. `x_confluence` is the worked example: 2→4 signals cut the count 65→42
and did not move expectancy `[repo-verified: DEFECTS.md:212, verdict log round 2]`.

**Item 7 therefore needs two controls, not one:**

1. **The shipped-scope arm** (`rth_only=True`, everything else `None`) — the pair partner.
2. **A count-matched random-subset placebo**: from the control arm's trades, drop uniformly at
   random down to the treatment arm's *n*, repeated. This separates "this scope selects better
   trades" from "fewer trades is better". Without it, any item-7 result is confounded with the
   count.

Use `placebo_shuffle` or `placebo_random`, **never `placebo_shift`**, which leaks — it is a
degraded real signal because adjacent bars are correlated, and is a *conservative* control only
`[repo-verified: DEFECTS.md, D42]`.

One more item-7-specific control: `rth_only` is the one scope field whose control value is
non-default (`True`), and the D24 correction already exists in the repo. **Run `rth_only` as its
own stratum** and check the paired result reproduces D23/D24's hand-built answer. If it does not,
that is a finding about the bespoke re-emissions those studies rested on — and BRIEF rule 6 rests
on them.

### 5.3 Channel-3 content (item 6, and item 4 in the other direction) — the control is arithmetic

Channel 3 is a deterministic subtraction, not a random variable, so it does not need a
statistical control — it needs a **reconciliation**. Compute per-trade `cost_r` in both arms and
check that the arms' expectancy difference equals the cost difference. If it does, the axis is
pure Channel 3 and there is nothing further to explain. If it does not, the residual is the real
Channel-1-or-2 effect and *that* is the quantity to test.

This is how item 6 pays for itself twice, and it is the reason I rank it first. A-7 establishes
that `TIME`, `SESSION_CLOSE` and `END_OF_DATA` exits are **slippage-free by construction** —
they close at `bar.close` with no `slippage_price` call `[repo-verified: engine.py:467, 473, 476]`.
So switching the time stop off **removes a zero-cost exit channel** and forces those trades onto
correctly-costed exits. The expectancy change therefore has a *predictable* Channel-3 component,
computable in advance from the control arm's TIME-exit count and the stop-slippage model. **The
gap between the predicted and the observed change is a direct measurement of the A-7 defect's
size** — on the axis D12 identifies as carrying the largest single exit effect in the repo.

Item 4 moves the mix the *opposite* way: a trail exit is a stop-class exit and **does** pay
`slippage_price(is_stop=True, ...)` `[repo-verified: engine.py:414-419]`. So items 4 and 6
bracket A-7 from both sides, which is worth more than either alone.

### 5.4 Item 8 — the control must be in a unit both arms share

`stop_kind=FIXED_TICKS` changes `risk_points`, so **1R means a different number of dollars in
each arm** and differencing R across the pair is differencing two different units. Note also that
`stop_mult` is *reinterpreted as a tick count* under `FIXED_TICKS` — a units overload on a single
field, and a bug magnet.

The control has to re-base both arms onto one denominator. The right one is **the control arm's
`risk_points`**, which is available because `Trade` carries `entry_price` and `initial_stop`
`[repo-verified: engine.py:502-512]`:

```
R_rebased(trade)  =  (exit_price - entry_price) * sign  /  risk_points_of_the_CONTROL_rule_set
```

Both arms then live in the control's R unit and are differenceable. This is a post-processing
step over stored trades, not a library change, but it is **not** "zero new code" and item 8's
Tier-1 billing in my D5 was too generous. Correcting that here.

Item 8's *purpose* also needs restating, because it has two and they are different sizes. The one
I gave in D5 — a control arm for B-2's claim that this repo's R normalisation already **is**
volatility targeting — stands. The larger one arrived with BT3's ALGO-1 and is in §6.2.

---

## 6. The seven, ranked by what a clean answer would change

Not by cheapness. The criterion is value of information: how much already-published material a
clean answer re-licenses or invalidates, how much unreachable channel space it opens, and whether
the answer is decision-relevant regardless of which way it comes out.

| rank | item | pairable? | channel | what a clean answer would change |
|---|---|---|---|---|
| **1** | **6 — switch the time stop off** | **cleanly**, gate-identical | 1 **and** 2, with a computable 3 | The only route to identifying the largest exit effect in the repo. D12's session-close result (z=+3.52) is **unidentifiable** on the shipped population — D19 shows it is an exact alias for anchored targets `[repo-verified: DEFECTS.md:236-241]`. The time stop is the same *class* of axis (a forced exit at `bar.close` paying zero slippage) and it **is** separable: `time_stop_bars=None` is a one-field change nothing else aliases, and it is `None` in **0 of 11** catalogue exits `[measured]`. Per §5.3 it simultaneously bounds the A-7 zero-slippage defect, which contaminates every exit result the repo has published. **Two findings from one test, and one of them is retroactive.** |
| **2** | **7 — vary `StrategyFilters` scope** | **cleanly**, gate-different, unit-identical | **2 — the only reachable one** | My D4 labelled 33 axes and found 11 in Channel 2 — the channel that changes expectancy by construction — and concluded Channel 2 "is almost entirely unreachable here, which is why it has never shown up as a survivor." **Item 7 is the reachable one.** It also puts BRIEF rule 6 ("no hours filter improves expectancy") on the *shipped* population for the first time; it currently rests on bespoke re-emission outside the generator (D23, D24 and the D24 correction), precisely because of R3-A-5. And `days_of_week` is virgin — no study in the repo has ever varied it. **D43 made this testable and nobody has used it** `[repo-verified: DEFECTS.md:640-652]`. |
| ~~3~~ **VACATED — see §6.3** | **2 — `mode="block"` vs `mode="iid"`** | **needs no pairing at all** | gates all of 4b | The only one of the seven **entirely outside** the D15 problem: two resampling modes over one stored R series, no exit varied, no entry sampled, nothing to confound. It gates every streak and equity-curve rule (Channel 4b, 1 of its 3 members) and it **retroactively licenses or invalidates the repo's ruin machinery**, which *assumes* i.i.d. — `risk_of_ruin` has no `mode` parameter at all `[repo-verified: montecarlo.py:209-231]` and **zero call sites in the repo have ever passed `mode="block"`** `[measured: grep -rn 'mode="block"' --include=*.py → the docstring at montecarlo.py:91 only]`. Decision-relevant either way. BT3 already has `block_vs_iid.py` on disk. |
| **3** (was 4) | **4 — turn the trailing stop on** | **cleanly**, gate-identical | 1 in shape, 3 via exit-mix | Closes the largest never-executed gap in the engine — implementation present at `engine.py:451-462` since it was written, run **zero** times, because `trail_atr_mult` is `None` in **11 of 11** catalogue exits `[measured]`. Brackets A-7 from the opposite side to item 6 (§5.3). Prior is a Channel-1 null, so the *expected* answer changes little; a positive would be large and is unlikely. **Hard prerequisite: the `ExitReason.TRAIL` fix (§5.1), without which the result cannot be attributed.** |
| **4** (was 5) | **8 — `StopKind.FIXED_TICKS`** | **not on R.** Needs the re-based unit of §5.4 | 1, plus a control role | **Promoted from last by BT3's ALGO-1 — see §6.2.** Its D5 purpose (a control for B-2) stands; its new and larger purpose is as the control arm for the integer floor. Costs a post-processing step, and `stop_mult` is overloaded to a tick count. |
| **5** (was 6) | **3 — "half off at 1R, breakeven, trail the rest"** | **cleanly**, gate-identical — but **not as a pair** | 1 and 3 | The single most-operated discretionary futures exit recipe in existence `[general knowledge]`, accepted by the validator today, and **never once constructed** `[measured: the literal passes `__post_init__`; and trail=None 11/11, scale_out sums to 1.0 11/11, time_stop_bars never None 11/11]`. But it changes **three axes at once** (four, if `targets_r` rides along), so a single pair against the shipped exit is unattributable: a difference could be any of them or their interaction. **It is not a peer of items 4/5/6 — it is their factorial closure.** See §6.1. |
| **6** (was 7) | **5 — leave a residual runner** | **cleanly**, gate-identical | 1 in shape, 3 via exit-mix | Genuinely never generated: **all 11** catalogue `scale_out` ladders sum to exactly 1.0 `[measured]` while the validator permits sums below 1 `[repo-verified: base.py:235-236]`. Ranked last because its effect is bounded by the residual fraction (0.2 in the D5 literal) and because **it cannot be interpreted without item 6**: the residual's fate is decided by whichever of stop / trail / time / session fires, and the time stop is present in 11 of 11 controls, so in the control arm the runner is very often just a TIME exit. Also needs the 1-rung stratum of §3. |

### 6.1 Items 3, 4, 5 and 6 should be one 2³ factorial, not four separate tests

This is the design recommendation and it changes the cost arithmetic decisively.

Three separate pairs sharing one control = **4 distinct arms** per rule set (control + 3 singles)
and yields three main effects with **no** interaction terms. The full 2³ factorial = **8 arms**
and yields the three main effects, all three two-way interactions, the three-way interaction,
**and item 3 for free** — item 3 *is* the all-on cell.

**8 arms instead of 4 buys item 3 plus every interaction.** And the interactions are not
decoration here: item 5's interpretation is *conditional* on item 6 (a residual runner under a
time stop is a different object from a residual runner without one), and item 4's is too (a trail
that never gets to ratchet because the time stop fires first is inert). The factorial is the only
design in which items 4, 5 and 6 are individually interpretable at all.

**Search size, stated as PIPELINE §4 requires: 8 arms.** That is `sqrt(2 ln 8) = 2.04` free
t-units, against the programme-wide `free_t = 5.46` and the largest t ever found here of 3.923.
Report 8, not 1, and not 4.

### 6.2 Does BT3's ALGO-1 change the ranking? Yes, in exactly one place

**Item 8 moves from 7th to 5th.** BT3's measurement is that `contracts_for`'s integer floor
deletes **35.4% of trades at the opening budget before any path dependence**, and that the
deletion rate is overwhelmingly conditional on stop distance — MGC_240 loses 99.4% and MES_60
loses 2.2% `[measured: BT3 algo1_report.json static_integer_floor.by_symbol_tf]`. My R3-B-3 claim
is that this makes the floor an **unintended volatility-regime entry filter**, because
`StopKind.ATR` makes stop distance proportional to ATR `[repo-verified: base.py:284-288]`.

`FIXED_TICKS` is **the only stop kind whose stop distance is not volatility-scaled.** So it is
the only arm in which the floor's selection is *decoupled* from volatility — which makes item 8
the natural control for BT3's own headline, not merely for B-2's. BT3's `floor_by_volatility`
table, which conditions on `(symbol, tf)` and reports survival per volatility bucket, is exactly
the right instrument; a `FIXED_TICKS` arm is the placebo that table currently lacks.

**Nothing else in the ranking moves.** BT3's other finding — the \$2,800 absorbing
dead-but-not-failed state I derived in `msgs/03` — is a property of the `risk/` layer, and
R3-B-1 establishes that nothing under `futures_agents/backtest/` imports anything from
`futures_agents/risk/`. So it cannot touch items 2–7, all of which live entirely inside the
backtester.

One hint that does **not** move a rank but is worth recording: BT3's placebo (R permuted,
timestamps and stops untouched) took 349 trades at mean R −0.006 against the real stream's 238 at
−0.108. A gap that size *hints* that the R sequence carries structure the governors respond to,
which would raise the prior that item 2 finds non-i.i.d. **It is not evidence**: the permutation
runs across all 176 nested variants, so it destroys cross-strategy structure as well as serial
structure, and the two cannot be separated in that design. Do not cite it as support for item 2.
It is a reason to run item 2, not a partial answer to it.

---

## 7. Anti-overfitting: what I checked in this design and what I found

Per my mandate, stating which hazards I actually checked rather than listing the catalogue.

| hazard | checked | finding |
|---|---|---|
| **Look-ahead in the treatment arms** | Yes, on the one path R3-A-11's clean bill could not cover — the trailing stop, which has never executed and so has never been audited | **Clean.** The trail reads `a = col[self.frame.tf_index(i, primary_tf)]`, and `tf_index` returns "index of the newest **completed** timeframe bar at `base_index`" `[repo-verified: features.py:921-926]`. No forming-bar ATR. |
| **Repainting** | Yes, same path | **Not repainting, but lagged, and it must be declared.** The trail is computed from `bar.high` (a completed high) at step 3, *after* step 1 already ran this bar's stop check `[repo-verified: engine.py:404-422 then 451-462]`. So a tightened stop takes effect on bar *i+1*. That is **conservative** (favourable to the strategy) and makes the engine's trail coarser than a live intrabar trail — it will systematically under-capture. State it with any item-4 number. |
| **Future-data leakage via the pairing** | Yes | **Found and forbidden.** Pairing on the entry-timestamp intersection conditions on which bars both arms were flat for, which is a function of prior outcomes — a selection on the dependent variable. §4.2. |
| **Silent merging / identity collision** | Yes | **Found: R3-A-13**, §2. The most dangerous hazard in the design and it produces a *false null*, the exact shape of every one of these seven results. |
| **Data-mining bias / search size** | Yes | 8 arms for the factorial, `sqrt(2 ln 8) = 2.04` free t-units. Item 7's search size is the number of scopes tested and must be declared per scope family, not once. `free_t = 5.46` programme-wide. |
| **Insufficient sample size** | Yes | n_pairs = 1,260 across four symbols at `max_total=400` (§1.2) — adequate at the **rule-set** level. Per-symbol it is 296–336, and **every symbol must be tested separately**: MNQ's answer is MNQ's. |
| **Parameter sensitivity** | Yes | `trail_atr_mult=2.0` and the 0.2 residual are single arbitrary points. Both need at least a second value before any non-null is believed; both are inside the factorial's cells, so the sensitivity run multiplies the search size and must be declared when it happens. |
| **Understated costs / unrealistic fills** | Yes | **This is item 6's second deliverable, not a caveat on it.** A-7's zero-slippage TIME/SESSION_CLOSE/END_OF_DATA exits `[repo-verified: engine.py:467, 473, 476]`; A-8's infinitely-divisible scale-out; D13's ~2× under-costing of scale-outs. §5.3 turns the first of these into a measurement. |
| **Confounding with the entry (the D15 problem itself)** | Yes | This whole file. Resolved at the rule-set level by construction (§3), **unresolvable at the trade level** without the R3-REQ-2 harness (§4.4). |
| **Survivorship bias** | Not applicable | The population is generated, not selected from survivors. But note items 3–6 are *exit* axes evaluated on entries chosen by a generator that has already been searched ~3,000,000 times — so the *entry* population is survivorship-contaminated relative to a fresh universe. The pairing cancels this, because both arms inherit the same contaminated entries. That is a genuine virtue of the paired design and worth stating. |

---

## 8. What is blocked on what

- **Nothing here is blocked on a generator change.** R3-A-5 stands as a description of the
  generator and is not a blocker: `replace` on the generator's output is the whole mechanism.
- **Item 4 is blocked on the 4-line `ExitReason.TRAIL` fix** (D5 item 13). Not a nicety — §5.1.
- **Items 4, 5, 6 are interpretable-but-not-decomposable without `signals_skipped_in_position`**
  (D5 item 9, one line at engine.py:308). Without it the gate-versus-skip split of §4.3 cannot be
  made on the new runs either.
- **Item 8 needs the re-based R of §5.4** — a post-processing step, so its Tier-1 billing in D5
  was too generous. Corrected here.
- **Trade-level pairing is blocked on the exogenous-entry harness, `R3-REQ-2`.** Everything in
  this file is designed to work without it.

### 6.3 CORRECTION — item 2 is vacated from the ranking. BT3 answered it while I was writing this

I ranked item 2 third on the grounds that it was unanswered and outside the pairing problem.
**Both halves of that were stale before I finished the file.** BT3 ran it as part of its ALGO-1
burst and reported in `msgs/04_BT3_R3_verify-ALGO-1.md`. Two results, and the second is the one
that matters for a ranking:

1. **Provisionally answered, negative, at the unit that counts.** The two units disagree in
   direction: pooled in `ts` order, `block` is much more severe than `iid` (p95 max DD 1642→1764R);
   across the 155 per-strategy series it is *less* severe (median Δ p95 DD −1.11R, streak shorter
   in 104 of 155, longer in 32). The explanation is the one that also decides item 1's population
   unit: **one timestamp carries up to 74 trades**, so a 10-element block in timestamp order is
   often ten correlated arms on a single bar — the block samples *across strategies*, not *along
   time*. **The pooled dependence is pooling.** At the per-strategy unit there is no positive
   serial dependence detectable at a 10-trade block scale, which points Channel 4b's streak
   sub-case negative.
2. **The instrument is defective — `D44`.** `bootstrap_paths(mode="block")` draws
   `r_values[start:start+block]` with no wrap-around `[repo-verified: montecarlo.py:103-107]`, so
   index 0 appears at 0.122× its due frequency against a 1.123× tail while `iid` over the same
   series is flat within `[0.988, 1.011]`. **The block arm systematically discounts the beginning
   of every sequence.** Item 2 was its first use anywhere in the repo, which is why nobody had
   found it. `MGR-T8` is GATED behind the one-line fix (`MGR-T16`), so the number exists and is
   **not reportable**.

**And my framing of the item was too strong**, which BT3 caught and the manager backed: comparing
two resamplers detects dependence only indirectly and only at the chosen block scale, so it is a
**precondition check**, not a verdict on whether streak sizing can work. The direct test — per-trade
lag-1..10 autocorrelation / runs / Ljung-Box, per strategy — is now `MGR-T11`. Narrowed in
`R3_path_operation.md` CORRECTION 5.

**Consequence for this file.** Item 2 is no longer a ranked candidate: it is a completed
measurement awaiting one line of repair, and the question it was a proxy for has become a board
task. Items 4, 8, 3 and 5 each move up one place, as marked in the §6 table. **The 2³ factorial
(§6.1) is unaffected and remains the first thing to build**, and item 7 remains the highest-value
item that is genuinely unanswered and genuinely needs this file's pairing machinery.

One thing item 2's result does *not* change: it says nothing about items 3–8, because it is a
statement about the R series of already-generated trades and every one of those items changes which
trades exist. It is not a partial answer to any of them.

---

## 9. The known-answer calibration test — run this through the harness before any of the seven

Everything above specifies a harness and then asks it to measure differences that are expected to be
near zero. **That is the worst possible situation to be in without a calibration test**, because
R3-A-13's silent merge, a mis-built pair key, a mis-keyed side table and a genuinely null axis all
produce the same output: no difference. A harness that returns zero is uninformative unless you have
first shown it returns zero *when it should* and non-zero *when it should not*.

R1's `msgs/05_R1_R3_stopkind-RANGE.md` handed me a configuration that supplies exactly this, and it is
the only one in the repository.

### 9.1 The positive control: a pair whose true difference is exactly zero

`StopKind.RANGE`'s fall-through when `snap.opening_range is None` is **byte-identical** to the ATR
branch — both compute `dist = self.stop_mult * a`, neither adds `pad`, and both pass through the same
`max(dist, min_dist)` tail `[repo-verified: base.py:284-288 vs 301-309]`. And the window RANGE needs
is **arithmetically unreachable** on an hourly grid when the RTH open is off the hour: `or_minutes = 30`
is hard-coded `[repo-verified: features.py:865]`, accumulation requires `0 <= minutes_since_open < 30`
`[repo-verified: features.py:891-895]`, and `[measured: {h : 0 <= 60h − open_minutes < 30} → MGC ∅,
MES ∅, MNQ ∅, MCL {9}; csv/raw/{MGC,MNQ,MCL}_1h.csv are 5000/5000 bars at minute :00]`.

**So on MGC, MES or MNQ at 60m:**

```
A = replace(ctrl, exit=replace(ctrl.exit, stop_kind=StopKind.RANGE, stop_mult=m), _id=None)
B = replace(ctrl, exit=replace(ctrl.exit, stop_kind=StopKind.ATR,   stop_mult=m), _id=None)
```

place **the same stop price on every bar**, therefore pass the same entry gates
(base.py:717-722), therefore emit the same signals, therefore hold for the same durations, therefore
never fork under `engine.py:304-309`. **The true difference is exactly zero at the trade level**, and
this is the **only** configuration in this repository where §4's fork does not apply — because it is
the only one where the two arms are the same function.

### 9.2 What it tests, and what each failure mode looks like

| observation | diagnosis |
|---|---|
| **one row instead of two** | **R3-A-13**: `_id=None` was omitted, the arms merged. This is the failure the test exists to catch, and note that it presents as a *missing arm*, not as a zero difference — which is why the `assert` of §1.1 must be on arm-id uniqueness and not on the result count alone. |
| two rows, **identical trade lists, difference exactly 0.0** | **PASS.** The pair key links the arms, the emission is correct, and the harness's zero is a real zero rather than a rounding of noise. |
| two rows, **different trade counts** | the arms are not the same function — so either the cell is wrong (MCL, or a non-60m timeframe), or `stop_mult` was not matched, or something else in `ExitModel` was perturbed by the `replace`. |
| two rows, same trade count, **non-zero difference** | a harness bug: the arms have been mixed, mislabelled, or the statistic is reading the wrong row. **Any non-zero result here is a defect, never a finding.** |

It also calibrates the *statistic*: run the §4.4 rule-set-level paired test over all 314 MGC pairs and
it must return an exact zero with zero variance. A test that returns a small non-zero "difference"
with a plausible-looking spread is reading noise it invented, and you would otherwise discover that
only by believing a null on item 5 or item 6.

### 9.3 The negative control that must accompany it

A test that only ever returns zero cannot distinguish a working harness from a dead one. So pair 9.1
with the same emission on **MCL at 60m**, where MCL's 09:00 RTH open lands on the hourly grid so
`minutes_since_open = 0` is reachable and `snap.opening_range` is populated on a real fraction of bars.
There `RANGE` and `ATR` are genuinely different functions and the harness **must** report a non-zero
difference. **Zero on MGC and non-zero on MCL, from the same code path with only the symbol changed,
is the pass condition.** Neither alone is sufficient.

This is also, incidentally, a clean demonstration of the independence rule the whole programme runs
on: the same two arms are the same strategy on one symbol and two different strategies on another,
purely because of where the RTH open falls relative to the bar grid. MNQ's answer really is not MCL's.

### 9.4 One consequence for anything already published that compared RANGE with ATR

Not my finding to chase and I am recording it rather than pursuing it. `x_exits` reported "no stable
best stop width — the ordering reverses by timeframe" `[repo-verified: DEFECTS.md:210]`. On MGC, MES
and MNQ at 60m a `RANGE`-versus-`ATR` comparison differs **only by `stop_mult`**, so any such
comparison measured the multiplier and not the mechanism, and its expected difference at matched
multiplier is zero by construction. The catalogue does contain a RANGE exit (`RANGEx1->1/2/3.5R`
`[measured: expand_exit_models(...) → 11 exits, one with stop_kind=RANGE]`), so the configuration was
reachable by the shipped population. Whether any published result rests on it is a re-read of
`x_exits`, which the manager has already recorded as an open obligation on account of `D45`. **The two
defects point at the same re-read**, which is worth saying because it makes that obligation cheaper to
discharge than either alone suggested.
