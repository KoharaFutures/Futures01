# EF5 burst 02 — the firing-rate census for the six SCALP cells

`[measured: EF5/code/census.py → EF5/out/census.json]`. **No backtest anywhere in it** — no
entries, no exits, no P&L. All 79 conditions, evaluated at every timeframe in the cell's frame, on
every bar of the archive substrate. `CONDITION_ERRORS` was cleared per cell and came back **empty in
all six** — so no condition is silently raising and being recorded as a 0% trigger rate (the failure
`Condition.evaluate`'s comment at `base.py:131-147` records).

## The three gates, and why a verdict is meaningless without one

| gate | definition | bars, 5m | bars, 15m | bars, 30m |
|---|---|---|---|---|
| `ALL` | every bar | 11,182 | 3,744 | 1,873 |
| `SESSION` | inside 18:00 ET → 16:00 ET, i.e. **not** 16:00–18:00 ET | 10,689 | 3,579 | 1,790 |
| `RTH` | `snap.is_rth`, 09:30–16:00 ET | **3,198** | **1,066** | **533** |

Identical counts on both symbols (same Yahoo grid).

**`rth_only=True` discards 71.4% of the substrate at every one of my timeframes.** That is not a
detail: `StrategyFilters.rth_only` defaults to `True` (`base.py:393`) and the exit/filter catalogue
never varies it, so **every strategy the combinator emits sees only 28.6% of the bars**, and the
overnight half of the 18:00→16:00 window — the entire point of this programme's session rule — is
unreachable for *entries* without an explicit override. EF2 raised the same thing for MGC/MCL
(`msgs/EF2-01_EF1_...`); in my cell it is four times larger, because MES/MNQ RTH is 6.5 of 22 hours.

## Verdicts, per (symbol, timeframe, gate)

### 1. `openinterest` — **VOID in all six cells, under all three gates**

| condition | kind | MES 5m | MES 15m | MES 30m | MNQ 5m | MNQ 15m | MNQ 30m |
|---|---|---|---|---|---|---|---|
| `oi_price_confirmation` | SIGNAL | **0** | **0** | **0** | **0** | **0** | **0** |
| `oi_expanding` | FILTER | **0** | **0** | **0** | **0** | **0** | **0** |

0 of 11,182 / 3,744 / 1,873 bars. Independent confirmation of `D47` on a different substrate
(`data/archive`, not `csv/raw`) and at three timeframes it had not been measured at. The mechanism is
in the library's own comment: `s.has("oi_change","open_interest")` is false on every bar because the
archive header carries no OI column, and the condition then returns `ConditionResult.no()` —
deliberately, and for a FILTER `no()` **vetoes the entry** (`base.py:670-674`).

**This is the item my dispatch flagged as "the big one on MNQ", and the reason is the template map,
not the data.** `oi_expanding` is an `optional_filters` entry on **MOMENTUM** and **BREAKOUT**
(`combinator.py:224,272`) and `openinterest` is an `optional_groups` entry on both. MES and MNQ both
receive MOMENTUM and BREAKOUT in my population (I use all 13 groups), so the *carrier* count is
comparable between them; MNQ's published 27.4% figure came from a population where its **profile**
admits MOMENTUM and BREAKOUT while MES's profile excludes MOMENTUM. Exact carrier counts are in
burst 04.

### 2. `session_extreme_sweep` — **VOID under the programme's own session rule**, both symbols, all three timeframes

This is sharper than `D-L4`, which found it dead under `rth_only=True`. It is dead under
**18:00→16:00** as well, and the reason is not the RTH gate:

| gate | MES 5m | MES 15m | MES 30m | MNQ 5m | MNQ 15m | MNQ 30m |
|---|---|---|---|---|---|---|
| `ALL` | 7 | 5 | 4 | 14 | 11 | 7 |
| `SESSION` | **0** | **0** | **0** | **0** | **0** | **0** |
| `RTH` | **0** | **0** | **0** | **0** | **0** | **0** |

**All 48 fires across both symbols and all three timeframes land between 16:00 and 16:55 ET** —
inside the two-hour window the session rule forbids. Every single one:

```
MES 5m : 07-30 16:45, 08-17 16:05, 08-17 16:15, 08-17 16:50, 08-20 16:15, 08-26 16:20, 09-18 16:55
MES 15m: 07-30 16:45, 08-17 16:00, 08-20 16:15, 08-26 16:15, 09-18 16:45
MES 30m: 07-30 16:30, 08-20 16:00, 08-26 16:00, 09-18 16:30
MNQ 5m : 08-05 16:00/16:10/16:40/16:50/16:55, 08-12 16:25/16:35/16:40, 08-17 16:50,
          08-26 16:05/16:20, 08-27 16:00, 09-02 16:05, 09-18 16:55
MNQ 15m: 08-05 16:00/16:30/16:45, 08-12 16:15/16:30, 08-17 16:45, 08-26 16:00/16:15,
          08-27 16:00, 09-02 16:00, 09-18 16:45
MNQ 30m: 08-05 16:30, 08-12 16:00, 08-17 16:30, 08-26 16:00, 08-27 16:00, 09-02 16:00, 09-18 16:30
```
`[measured: EF5 scratch script over build_frame(sym,tf) → the ET stamps above]`

Mechanism: `session_extreme_sweep` asks whether price ran the *running* session high/low and closed
back inside (`library.py:595-600` → `_level_sweep`). The running RTH extreme cannot be swept while it
is still being set; the first bars on which it is a stable, breachable level are the bars just after
the RTH close. Those are exactly the bars 16:00–18:00. **So on MES/MNQ at scalp timeframes the
condition's entire support is the forbidden window.** `liquidity` is a *required* group for
OPENING_RANGE and LIQUIDITY, so this is a dead member of a required group in my cell, same shape as
`D-L4` but caused by the programme rule rather than by `rth_only`.

### 3. `volatility_compressed` — a **new** VOID configuration, and it kills all of BREAKOUT on MES 15m

Not in R1's Addendum B. `volatility_compressed` fires when `atr_percentile <= 0.30`
(`library.py:735-743`), and `atr_percentile` is a percentile over that timeframe's **whole** history,
which is 71% overnight bars. RTH bars are almost never in the bottom 30% of a 24-hour ATR
distribution:

| | MES 5m | MES 15m | MES 30m | MNQ 5m | MNQ 15m | MNQ 30m |
|---|---|---|---|---|---|---|
| `volatility_compressed`, `SESSION` | 32.8% | 34.5% | 34.7% | 33.1% | 35.8% | 38.7% |
| `volatility_compressed`, **`RTH`** | **0.3%** (11) | **0.0% — VOID (0/1066)** | 3.6% (19) | 5.4% (172) | 0.9% (10) | 4.1% (22) |
| `volatility_expanding`, `RTH` | 85.4% | 80.3% | 58.9% | 74.6% | 76.6% | 57.0% |

**BREAKOUT's `base_filters` are `("volatility_compressed","volume_not_thin")`**
(`combinator.py:266`), nailed in, not optional. So under `rth_only=True`:

* **MES 15m: every BREAKOUT strategy in the population is VOID** — 0 admissible bars, structurally.
* MES 5m (11 bars), MNQ 15m (10 bars), MES 30m (19), MNQ 30m (22): not literally VOID but
  **`DEGRADED` past the point of producing a sample** — the whole template has fewer candidate bars
  than the 20-trade reporting floor, before any signal is required to agree.
* Under the `SESSION` gate the same filter passes on ~33–39% of bars. **This VOID is created entirely
  by `rth_only`, not by the market.**

And the mirror image matters as much: `volatility_expanding` passes 57–85% of RTH bars, so in this
cell it is **close to a no-op** rather than a selective regime filter. Quoting a result as
"conditioned on expanding volatility" at 5m RTH is quoting a result conditioned on almost nothing.

### 4. `profile` — **alive at 5m/15m/30m.** The 240m VOID does not reach my cell

`D-P1` found all six `profile` conditions dead at 240m (`prior_session_profile` needs ≥ 10 bars per
session; 4h gives 5–6). At my timeframes there is no shortage of bars per session:

| condition | MES 5m | MES 15m | MES 30m | MNQ 5m | MNQ 15m | MNQ 30m | (gate `RTH`) |
|---|---|---|---|---|---|---|---|
| `poc_reversion` | 18.9% | 17.0% | 15.9% | 20.9% | 18.4% | 16.9% | |
| `value_area_edge` | 2.5% | 3.9% | 5.8% | 1.8% | 3.4% | 4.9% | |
| `value_area_breakout` | 71.7% | 70.5% | 69.0% | 68.2% | 67.3% | 64.9% | |
| `lvn_rejection` | 1.1% | 1.3% | 1.9% | 2.1% | 2.3% | 3.4% | |
| `away_from_hvn` (F) | 82.3% | 80.4% | 79.2% | 81.8% | 78.9% | 78.0% | |
| `open_outside_value` (F) | 75.6% | 73.2% | 70.7% | 75.6% | 70.7% | 70.7% | |

**Verdict `DEGRADED`, not `VOID`** — R2/R1's degradation findings (the profile is built from that
timeframe's own bars, so the same session yields a different value area at 5m than at 30m) still
apply and I have not re-measured them. But VOLUME_PROFILE **is expressible in my cell**, which is a
genuine difference from the 240m swing cells, and `value_area_breakout` firing on ~70% of RTH bars
means it is a weak location statement, not a rare one.

### 5. `OPENING_RANGE` — **alive at 5m/15m/30m, where `D-L1` found it dead at 1h**

`D-L1`: `or_minutes = 30` against an off-grid `rth_open` makes `snap.opening_range is None` on
**4,990 of 5,000** MNQ and MES 1h bars. At 5m/15m/30m the 09:30–10:00 window resolves exactly (six
5m bars, two 15m bars, one 30m bar), and it does:

| condition | MES 5m | MES 15m | MES 30m | MNQ 5m | MNQ 15m | MNQ 30m | (gate `RTH`) |
|---|---|---|---|---|---|---|---|
| `opening_range_breakout` | 53.3% | 53.8% | 54.0% | 47.6% | 49.0% | 49.5% | |
| `opening_range_fade` | 9.2% | 14.9% | 21.2% | 7.1% | 12.5% | 17.4% | |
| `initial_balance_break` | 36.3% | 36.3% | 36.4% | 29.4% | 29.9% | 30.4% | |
| `opening_drive_window` (F) | 24.4% | 26.9% | 30.8% | 24.4% | 26.9% | 30.8% | |

**This is the one place my cell has more expressive power than the swing cells, and it is exactly
where the dispatch predicted it.** Note the shape: `opening_range_breakout` is a *close beyond a
completed OR*, so it stays true for the rest of the day — 53% of RTH bars is "price is outside the
first 30 minutes' range", not "the breakout just happened". That is the `value_area_breakout` problem
again and it is a `DEGRADED`-on-selectivity finding, not a VOID one.

### 6. Filters that are near-no-ops in this cell, which changes how a "filtered" row reads

| filter | `RTH` pass rate, range over my six cells |
|---|---|
| `volume_not_thin` | **89.8% – 99.8%** (MES 15m 99.8%, MNQ 15m 99.8%) |
| `no_imminent_release`, `outside_news_blackout` | 99.6% everywhere |
| `after_opening_range` | 92.3% everywhere |
| `avoid_lunch` | 76.9% everywhere |
| `volatility_normal` | 77.8% – 84.4% |

`post_news_window` passes **0.5–1.5%** of RTH bars — matching the combinator's own note that it
cannot produce a sample — and the combinator already declines to offer it. `volume_not_thin` at 99.8%
is worth naming because it is in **12 of 13 templates' `base_filters`**: on MES/MNQ 15m RTH it
removes essentially nothing, so "volume regime" is not a tested axis in this cell.

### 7. `structure` SIGNALs bound to the confirmation timeframe — all alive

The combinator binds `structure` SIGNALs to `confirm_tfs[0]` when a strategy carries ≥ 3 signals
(`combinator.py:600-612`): 15m for my 5m cell, 60m for my 15m and 30m cells. Censused there too —
`structure_trend`, `break_of_structure`, `pullback_to_support`, `fvg_nearby`,
`range_position_extreme` all fire on 22–1,885 RTH bars in every cell. **No VOID from that route.**

### 8. `multitimeframe` — alive, because every frame in my cell has three timeframes

`D-MTF1` (`voting < 2` → both MTF signals `no()`) bites only at the **top** of a frame. My primary
timeframes are the *bottom* of their frames (5 of [5,15,60]; 15 of [15,60,240]; 30 of [30,60,240]),
so `agreeing_timeframes(from_tf=primary)` always has three voters. `mtf_aligned` fires 21.6–34.5% of
RTH bars, `mtf_strongly_aligned` 15.7–29.3%. **No VOID.**

## Summary table — verdicts, per (symbol, timeframe, gate)

| condition / group | MES 5m | MES 15m | MES 30m | MNQ 5m | MNQ 15m | MNQ 30m |
|---|---|---|---|---|---|---|
| `oi_price_confirmation`, `oi_expanding` | VOID | VOID | VOID | VOID | VOID | VOID |
| `session_extreme_sweep` (SESSION & RTH) | VOID | VOID | VOID | VOID | VOID | VOID |
| `volatility_compressed` (RTH only) | DEGRADED (11) | **VOID** | DEGRADED (19) | DEGRADED (172) | DEGRADED (10) | DEGRADED (22) |
| `volatility_compressed` (SESSION) | CLEAN | CLEAN | CLEAN | CLEAN | CLEAN | CLEAN |
| 6 × `profile` | DEGRADED | DEGRADED | DEGRADED | DEGRADED | DEGRADED | DEGRADED |
| `opening_range_*`, `initial_balance_break` | CLEAN | CLEAN | CLEAN | CLEAN | CLEAN | CLEAN |
| `mtf_aligned`, `mtf_strongly_aligned` | CLEAN | CLEAN | CLEAN | CLEAN | CLEAN | CLEAN |
| 5 × `structure` at bound tf | CLEAN | CLEAN | CLEAN | CLEAN | CLEAN | CLEAN |

Two of the eight rows above are new relative to R1's Addendum B: the `session_extreme_sweep` cause
(the programme rule, not `rth_only`) and `volatility_compressed` under `rth_only` (which makes MES
15m BREAKOUT a **seventh** structurally-zero-trade configuration in this repository).
