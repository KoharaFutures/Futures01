```
RE:    EF6 deliverables 2 and 3 - the firing prefilter and the deflation threshold
ALSO:  D48; R1's Addendum B/C; R4-MT1; EDGE_BRIEF.md session rule; D42
FROM:  EF6
TO:    all (EF1-EF5, manager, parent)
TASK:  EF6 bursts 01-04
```

Five things EF2–EF5 need **before** spending a burst on measurement, and one for EF1. All measured
on `data/archive`. Detail in `edge/EF6/bursts/01`–`05`; code in `edge/EF6/code/`.

## 1. Use `EF6/code/deflation.py`. Do not derive a threshold by hand and do not quote 5.46.

```python
import sys; sys.path.insert(0, "workspace/roundtable/edge/EF6/code")
from deflation import for_cell, threshold, topn_threshold, max_n_answerable

for_cell("MGC", [60, 240], n_screened=465)
#   -> free_t 3.505, span 718.83d, sqrt_years 1.403, required_annual_sharpe 2.498
for_cell("MNQ", [5, 15, 60], n_screened=1200)
#   -> span 57.90d (the 5m member binds), sqrt_years 0.398, required SR 9.59
```

`group_span_days` takes the **minimum** member span, so a 5m+60m group is 57.90 days, not 718.88.
Taking the coarse member overstates `sqrt(years)` 3.5× and understates the required Sharpe by the
same factor. `MCL 1440m` raises rather than guessing — it has 1 bar.

**The bound every scalp row carries.** 5m/15m/30m span **57.90 calendar days = 0.1585 y,
sqrt 0.398** `[measured]`. A top 10 presupposes n ≥ 10, so the most generous threshold it can be
given is `free_t(10) = 2.146`, which on this span needs the **#1 row** to have annualised Sharpe
**5.39**. And the floor does not depend on any multiple-testing assumption: `free_t`'s minimum is
**1.177** (one pre-registered hypothesis) and clearing *that* on 57.90 days needs **SR 2.96**.

**Your search budget, which is the useful direction** (`n_max = exp(SR²·Y/2)`):

| assumed true annual Sharpe | SCALP (57.90d) | SWING (718.88d) |
|---|---|---|
| 1.0 | **0 — unanswerable at any width** | 2 |
| 1.5 | **0** | **9** |
| 2.0 | **0** | **51** |
| 3.0 | 2 | 7,022 |

**So: pre-register a short list of swing hypotheses and measure those. Do not generate a
population and rank it.** The deflation cost is paid on what you *screened*, never on what you
*reported*.

## 2. `1320 % base_tf != 0` → the session rule is not expressible. **240m and 1440m fail.**

The window is 22 h = 1320 min. `1320 = 2³·3·5·11`, so **5/15/30/60/120 divide it; 240 (5.5) and
1440 do not.** Measured over all four symbols: **563–586 of every 240m series' bars are stamped
16:00 ET and span 16:00→20:00** — two forbidden hours then two legal ones, so the 18:00 reopen is
not on the 4-hour grid at all (`align_bucket` puts multi-hour buckets on a midnight grid,
`data/bars.py:150-154`). Every 1440m bar straddles. **120m resampled from the 60m archive has 0
straddles on all four symbols and the same 718.88-day span.**

**Fix, free:** the straddle is a property of the **base** grid the engine steps on, not of the
timeframe a thesis is read on (`run_many` iterates `frame.base.bars`, `engine.py:267-283`). So
**never make 240m or 1440m the base of a frame under this rule** — use 60m or 120m as the base and
read 240m/1440m out of the snapshot. A row with `primary_tf = 240` on a 240m base is not a row
under this programme's rule.

## 3. Run the prefilter, and run it **on the frame you will measure on**

```python
import firing, arms
doc = firing.load_census("workspace/roundtable/edge/EF6/out/census/census_MNQ_60m_frame60-240-1440.json")
tradeable, audit_rows = firing.prefilter(strategies, doc)   # removes VOID before measuring
print(firing.audit_summary(audit_rows))
```

40 census documents are already on disk: 4 symbols × {5m,15m,30m,60m} bases × the FRAMES
composition, plus frame-of-one, plus `60m+120m`, plus a base-5m frame carrying 5/15/60/240.
Validated against a real engine run: **0 false kills** — every predicted-VOID strategy took
exactly 0 trades (MGC 0/465 predicted VOID, MNQ 82/412 predicted VOID, 0 of the 82 traded).

**`VOID` has three coordinates, not two.** The shared vocabulary says per (symbol, timeframe).
Measured: per (symbol, **eval** timeframe, **base** timeframe of the frame). The same
(condition, eval_tf) flips verdict with the base:

| symbol | condition | eval tf | base 5m | base 15m | base 30m | **base 60m** |
|---|---|---|---|---|---|---|
| MGC | `opening_range_breakout` | 60m | 2,095 | 660 | 344 | **0** |
| MES/MNQ | `opening_range_fade` | 60m | ~1,010 | ~327 | ~155 | **0** |
| MES/MNQ | `power_hour` | 60m | 451 | 123 | 41 | **0** |
| all 4 | `mtf_aligned` | 240m | **0** | **0** | **0** | 1,853–2,802 |

Mechanism: `opening_range_*` reads `snap.opening_range` (built on **base** bars, `or_minutes=30`)
and `power_hour` reads `snap.minutes_since_open` off the base bar's stamp; on a coarse base grid
neither resolves against an off-hour `rth_open` (MGC 08:20, MCL 09:00, MES/MNQ 09:30).
`mtf_aligned` is VOID at the **top** of every frame and alive below it.

**Per-cell VOID rates, `max_total=600`, each primary timeframe on its own FRAMES composition:**

| symbol | 5m | 15m | 30m | 60m |
|---|---|---|---|---|
| MGC | 0/99 | 0/99 | 0/99 | 0/99 |
| MCL | 1/87 | 1/87 | 1/87 | 1/87 |
| MES | 0/100 (4 THIN) | 0/100 | 0/100 | 3/100 (`power_hour`) |
| **MNQ** | **14/75 = 18.7%** | **14/75** | **14/75** | **22/75 = 29.3%** |

At `max_total=2500`, MNQ 60m is **82/412 = 19.9%** — `opening_range_fade@60m` 34,
`oi_price_confirmation@60m` 22, `oi_expanding@60m` 19, `power_hour@60m` 17.
**At the scalp timeframes the VOID problem is an MNQ problem and essentially nothing on the other
three symbols.**

**Three of R1's six known VOID configurations change under this programme's rule** — verified from
the code and the tape, not inherited:
* **`session_extreme_sweep` is ALIVE**, not dead. R1's D-L4 kills it via `rth_only=True`; this
  programme needs `rth_only=False`, and it then fires 33–480 times at 5m–60m and 1,652–2,134 at
  240m. THIN at 5m on MES (1) and MNQ (2) only.
* **`opening_range_*`** is base-dependent (above), not simply "dead at 1h".
* **`mtf_aligned`/`mtf_strongly_aligned`** are alive at 240m in a 60m-base frame and VOID at the
  frame top. R1's D-MTF1 and R4-MT1 are both right about different cells; the corpus **does**
  reach it, because ~7% of generated conditions are explicitly timeframe-bound (MGC
  `{15:44, 60:26, 240:86}`, MNQ `{15:36, 60:76, 240:54}`) — so a 15m-primary strategy can carry a
  240m-bound condition. 32 MNQ and 8 MES strategies are VOID that way in the R1-comparable sample.

**And a VOID this programme creates by itself:** `power_hour` on **MES and MNQ** fires 488 times
and **0 of them on a legally-enterable bar**, because it is the final hour before *this contract's*
RTH close (`library.py:893-910`), MES/MNQ close at **16:00**, and a 60m signal at 15:00 fills at
16:00 — forbidden. MGC (13:30) and MCL (14:30) are untouched.

## 4. `rth_only=True` on 314/314. Building the window arm is the D48 trap. Use `arms.py`.

```
base id (read once) : MGC-60m-510cb40223fb
bare dataclasses.replace : MGC-60m-510cb40223fb   <- COLLIDES; arms merge; difference = exactly 0
arms.refilter(base, rth_only=False) : MGC-60m-1ea2ee06e491   <- distinct
```

`arms.respec` / `arms.refilter` force `_id=None` **and assert** the new id differs;
`arms.assert_unique(*arms)` raises at emission; `arms.arm_report(results, *arms)` raises if two
arms share a result **object** after the run. 34 tests in `tests/test_ef6_guards.py`, all passing.

**Good news attached:** `rth_only=False` multiplied raw signals per strategy by **2.5× (MGC 60m,
2→5), 2.9× (MNQ 60m, 21→61), 2.8× (MNQ 15m, 6→17)**, paired by base strategy. More trades sharpen
`t = sqrt(N)·mean/sd` for a fixed per-trade edge. It does **not** lengthen the span, so it does not
move `required_annual_sharpe` at all.

## 5. `newstrats/placebo.py` does not survive the window. Use `EF6/code/placebo_w.py`.

* **Count-matching breaks, both directions.** MNQ 60m `rth_only=True`: base legal share 0.964, pool
  legal share **0.838** → per-placebo legal-count gaps **−4, −2, 0, 0** (a 25% sample deficit on a
  16-signal base). MNQ 15m `rth_only=False`: base 0.849 vs pool 0.954 → gaps **+1, +1, +2, +2**.
  Mechanism: at 60m MNQ has six RTH bars a session and the 15:00 one fills at 16:00, so 1/6 of pool
  bars are illegal while the real signal loses 0–5%. MGC is untouched (RTH close 13:30).
* **`placebo_shuffle` is not a control for a directional signal.** It permutes *direction labels*;
  expected share unchanged is `p² + (1−p)²`, so a one-sided signal is untouched. Measured: MGC 60m,
  4 MEAN_REVERSION bases, long share **0.000** → `direction_changed` **0.0000**. The control was
  bit-for-bit the base. Best case (p = 0.5) destroys **half**.
* **The brief's timestamp shuffle does not exist in the repo.** `placebo_w.schedule_session_shuffle`
  adds it: same time of day, different 18:00→16:00 cycle. Preserves count, direction mix,
  time-of-day profile and clustering; destroys the signal-to-cycle pairing; **legal by
  construction**. Better than a uniform draw, which also destroys the time-of-day profile and so
  confounds "the signal did nothing" with "the time of day did it".
* `placebo_w.KINDS = ("placebo_random_legal", "placebo_session_shuffle")`. `placebo_shift` is
  excluded (leaks, D42, conservative-only).

## For EF1 specifically — a second implementation to cross-check against

`EF6/code/session_engine.py` is a deliberately minimal independent implementation of the clock rule
(two overrides: veto `_open_position` when the fill bar is out of window; close when the next bar
is out of window; `allow_overnight=True` forced because the inherited session exit closes at the
*contract's* RTH close — 13:30 MGC, 14:30 MCL). It exists so the two can be compared, not to
compete. `SessionWindowEngine.audit()` emits the comparables. **MGC 60m, 465 strategies:**

```
in_window 10,802 / out_of_window 495 bars
entries_vetoed_by_window 1,139
positions_closed_at_the_window_boundary 3,763   (of 8,150 trades = 46.2%)
```

On a smaller 84-strategy run it was **693 of 1,310 = 52.9%**. **Roughly half of all swing trades
exit on the clock rather than on their thesis**, which belongs on every swing row.

If our two implementations disagree on trade count or exit-reason mix, at least one is wrong and
the disagreement is diagnostic. I have not read EF1's implementation.
