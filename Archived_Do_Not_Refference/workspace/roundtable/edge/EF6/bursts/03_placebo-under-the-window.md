# EF6 burst 03 — does the placebo machinery survive the window constraint? **No, in three separate ways.**

**Read:** `workspace/newstrats/placebo.py` (485 lines) in full.
**Built:** `EF6/code/probe_placebo.py` (the measurement) and `EF6/code/placebo_w.py` (the fix).

## What the existing machinery gets right, so the three faults are read in proportion

`placebo.py` is careful work and four of its decisions are the right ones:

* it keeps the base's **exit model, scope filters, FILTER conditions, confirm
  timeframes, execution timeframe, symbol, primary timeframe and allowed directions**
  and replaces only the SIGNAL layer `[repo-verified: placebo.py:make_placebo]`;
* it matches on **raw** signals rather than `signals_generated`, which is a realised-trade
  count in disguise `[repo-verified: placebo.py:extract_signals docstring]`;
* both of its `dataclasses.replace` calls on a `Strategy` pass `_id=None`, so it is
  **D48-clean** `[repo-verified: placebo.py:make_placebo, _probes]`;
* the scripted condition's name is a hash of the schedule, because `Condition.evaluate`
  memoises on `(name, timeframe)` and two placebos with one name would return each other's
  answers `[repo-verified: placebo.py:scripted_condition docstring; base.py:105-145]`.

None of the three faults below is carelessness. All three are the window rule arriving after
the module was written.

---

## Fault 1 — count-matching does not survive the window, and the bias goes **both ways**

The window lives in the engine, not in `Strategy.evaluate`. So `placebo.scan` counts signals
and builds pools over bars that include the 16:00–18:00 prohibition, and `_schedule_random`
draws `k = len(real_signals)` bars uniformly from that pool. Base and control then arrive at the
engine with **different numbers of legal entries**.

`[measured: EF6/code/probe_placebo.py → EF6/out/placebo_window_probe.json; substrate
data/archive; 4 bases per cell surviving `len(real) >= 2`]`

| cell | base legal share | pool legal share | per-placebo legal-count gap |
|---|---|---|---|
| MGC 60m `rth_only=True` | 1.000 | 1.000 | 0, 0, 0, 0 |
| MGC 60m `rth_only=False` | 1.000 | 0.964 | 0, 0, 0, 0 |
| **MNQ 60m `rth_only=True`** | 0.964 | **0.838** | **−4, −2, 0, 0** |
| MNQ 60m `rth_only=False` | 0.988 | 0.950 | −2, −1, −2, −2 |
| MNQ 15m `rth_only=True` | 1.000 | 0.954 | 0, 0, 0, 0 |
| **MNQ 15m `rth_only=False`** | **0.849** | 0.954 | **+1, +1, +2, +2** |

**The mechanism is arithmetic and it is per-symbol.** At 60m under `rth_only=True` MNQ has six
RTH bars a session and the **15:00** one fills at 16:00, so exactly 1/6 = 16.7% of pool bars are
illegal — while the real signal fires at 15:00 far less often and loses 0–5%. Hence pool 0.838 vs
base 0.964. On a base of 16 legal signals the control arrived with 12: a **25% sample deficit**.
MGC is untouched because its RTH close is 13:30, so its last RTH bar fills at 14:00, legally.

**And on MNQ 15m with `rth_only=False` the sign reverses** — the control gets *more* legal
entries than the base. So this is not a conservative bias that can be waved through. A control
with a systematically different sample size is not a control; `placebo.py`'s own docstring makes
exactly this argument for a different reason ("a handicapped control makes the real strategies
look better than they are") and the window reintroduces the fault it was written to avoid.

**Fix, in `placebo_w.schedule_random_legal`:** intersect *both* sides with
`window.signal_mask` before counting anything — match on **legal** signals, draw from the
**legal** pool, per direction. Verified: `count_matched 4/4`, `pool_short_by 0`, and every
scheduled entry asserted legal before the cohort is returned
`[measured: build_cohort on MNQ 60m, 12 bases, rth_only=False → per_kind
{'placebo_random_legal': {'built': 4, 'count_matched': 4, 'short': 0},
'placebo_session_shuffle': {'built': 4, 'count_matched': 4, 'short': 0}}, id_collisions 0]`.

---

## Fault 2 — `placebo_shuffle` is not a control for a directional signal. **It is the base.**

`_schedule_shuffle` permutes the **direction labels** across the base's own bars; its own
docstring says so. For a uniform permutation of a multiset with long share `p`, the expected
share of positions that keep their label is `p² + (1−p)²`:

| base long share | direction information destroyed |
|---|---|
| 1.00 or 0.00 (one-sided) | **0% — the control is bit-for-bit the base** |
| 0.90 | 18% |
| 0.50 (best case) | **50%** |

`[measured: MGC 60m rth_only=True, 4 MEAN_REVERSION bases, long_share **0.000** →
shuffle_direction_changed **0.0000**. MNQ 60m rth_only=True, long_share 0.905 → 0.1905 against
the formula's 0.172. MNQ 15m rth_only=True, long_share 0.500 → 0.667 on n = 6.
Across 4 surviving MNQ 60m bases with rth_only=False the mean degeneracy is **0.553**.]`

So the **strongest form this control can ever take destroys half of one channel**, and on a
one-sided rule set it destroys nothing at all. `KINDS` in `placebo.py` presents it beside
`placebo_random` as one of three peers, and nothing at the call site reports the degeneracy.

**This is a re-reading of a published finding, and I am flagging it as a re-reading rather than
a new measurement.** `BRIEF.md` reports that "five separate placebo constructions matched or beat
the real thing". A control that is 50–100% identical to its treatment is *expected* to match it.
`RANKING_FINDINGS.md:250-256` already separates the honest kinds from the leaky one for
`placebo_shift` (D42) and finds the two honest kinds rank *worse* than uniform; the same
separation has never been applied to `placebo_shuffle`'s degeneracy. **What I can say is that
one of the five constructions cannot support the claim; what I cannot say is what the other four
would show re-measured.** `placebo_w.KINDS` therefore excludes both `placebo_shift` (leaks, D42,
conservative-only) and the direction shuffle, and `shuffle_degeneracy(long_share)` is exported so
anyone who wants it must report what it destroyed.

---

## Fault 3 — the brief asks for a **timestamp shuffle** and `placebo.py` has none

`placebo_shuffle` shuffles *directions* on fixed timestamps. The control the brief names does not
exist in the repository. `placebo_w.schedule_session_shuffle` adds it, and it is a better control
than a uniform random draw for a specific reason:

> **Move each signal to the same time of day on a different 18:00→16:00 cycle.**

Preserved exactly: count, direction mix, **time-of-day distribution**, intraday clustering.
Destroyed: the pairing between the signal and *that cycle's* price action.

A uniform draw from the eligible pool destroys the time-of-day profile as well, which confounds
"the signal contributed nothing" with "the time of day did it" — and this repo has two settled
time-of-day effects to be confounded with (`BRIEF.md` rule 5: no entries 15:00–16:00, z = −4.43,
replicated; and the opening-range family). Second reason it is the right control here: because
the intraday slot is unchanged and the slot was legal, **the shuffled entry is legal by
construction**, so the window cannot re-open Fault 1 through the back door.

Both kinds are asserted legal before the cohort is returned; `dropped_no_slot` and
`slot_collisions` are reported per placebo so the count match is auditable rather than assumed.

---

## A fourth thing, and it is a finding for EF2–EF5 rather than a fault

**`rth_only=True` on 314/314 generated strategies** `[measured: generate_strategies('MGC'|'MNQ',
[5,15,60,240], max_total=400) → Counter({True: 314}) each; allowed_directions
(LONG, SHORT) on 314/314]`, which reproduces R1's count exactly. So **nothing the combinator
emits can trade the 18:00→16:00 window as generated** — every agent here must build an
`rth_only=False` arm, which is a `dataclasses.replace` on a `Strategy` and therefore the exact
D48 shape. `EF6/code/arms.py` is the guard and `tests/test_ef6_guards.py` pins it; the
collision is reproduced live in `test_d48_bare_replace_still_collides`:

```
base id (read once) : MGC-60m-510cb40223fb
bare replace id     : MGC-60m-510cb40223fb   <- COLLIDES
arms.refilter id    : MGC-60m-1ea2ee06e491   <- distinct
```

**And the window arm buys sample, substantially.** Turning `rth_only` off multiplied the raw
signal count per strategy by **2.5× on MGC 60m (2 → 5), 2.9× on MNQ 60m (21 → 61) and 2.8× on
MNQ 15m (6 → 17)** `[measured: same probe, paired by base strategy]`. That is the first concrete
evidence in this programme that the overnight regime is not merely unmeasured but *materially
larger*, and it is the only lever available against the power problem in burst 01 — more trades
raise `t` for a fixed per-trade edge, since `t = sqrt(N)·mean/sd`. It does not lengthen the span,
so it does not change `required_annual_sharpe`; it changes how precisely a given cell's expectancy
is estimated.

## Anti-overfitting checks in this burst

| hazard | checked | finding |
|---|---|---|
| understated control sample (handicapped placebo) | **yes, and found** | Fault 1: up to a 25% legal-entry deficit, sign reversing by cell |
| a control identical to its treatment | **yes, and found** | Fault 2: 0% destruction on a one-sided signal, measured at exactly 0.0000 |
| look-ahead in the control | yes | `placebo_shift` excluded — it leaks (D42) and is conservative-only, so it cannot support "the row beat its control" |
| D48 arm collision | yes | `placebo_w.make_placebo` **asserts** `out.strategy_id != base.strategy_id` rather than relying on `_id=None` staying in place |
| condition-cache cross-talk between placebos | yes | schedule-derived condition names, inherited from `placebo.py`; two placebos can only collide by being identical, and `build_cohort` counts `id_collisions` (0 observed) |
| sample size | **yes, and it is bad** | only **4 of 12–25** bases per cell had ≥ 2 raw legal signals. 8 of 12 MNQ 60m bases were dropped for `< 2` legal signals. Consistent with the settled "82% of generated strategies never trade", and it means a placebo cohort at these cell sizes is built on a handful of bases |
