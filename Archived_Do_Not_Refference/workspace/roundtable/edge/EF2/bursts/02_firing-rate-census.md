# EF2 / Burst 02 — the firing-rate census for the four swing cells

Run **before** any population was constructed, per the brief. Substrate: `data/archive/{MGC,MCL}_60m.jsonl`,
**11,297 / 10,934 bars, 718 calendar days**, 240m resampled up (bit-identical to the native
`_240m.jsonl`, Burst 01). Every one of the 79 conditions evaluated at every bar at every timeframe
binding the frame admits. Code: `EF2/code/census.py`; raw: `EF2/data/census.json`;
verdicts: `EF2/data/census_verdicts.json`.

## The denominator matters, so here it is first

| cell | base bars | RTH bars | swing-admissible bars | **RTH ∩ swing** |
|---|---|---|---|---|
| MGC (all frames) | 11,297 | 2,477 (21.9%) | 10,319 (91.3%) | **2,477** |
| MCL (all frames) | 10,934 | 2,881 (26.3%) | 9,993 (91.4%) | **2,881** |

**`RTH ∩ swing == RTH`, exactly, on both symbols.** Every RTH bar is admissible under 18:00→16:00, so
`rth_only=True` is strictly the binding constraint and the session rule adds no entry opportunity
(Burst 01 §2b). The denominator I score "usable fires" against is therefore **2,477 (MGC) / 2,881
(MCL)** — 22–26% of the tape, not all of it.

## The three verdicts I distinguish, and why the middle one exists

- **`VOID_RAW`** — 0 fires on any of the 11,297 / 10,934 bars. Structurally impossible.
- **`VOID_IN_STRATEGY`** — fires somewhere, but **never on a bar a strategy could act on**: never on
  an RTH bar (`rth_only=True` on 100% of generated strategies, Burst 01), never on a
  swing-admissible bar, or — for a SIGNAL — never with a LONG/SHORT direction, which
  `Strategy.evaluate` also requires `[repo-verified: base.py:678-679]`. R1's `DEGRADED` understates
  this and `VOID_RAW` mislabels it. Both are zero-trade; only the first is a property of the
  detector alone.
- **`LIVE`** — at least one usable fire.

`Strategy.evaluate` is a strict AND with no `min_signals`
`[repo-verified: futures_agents/strategies/base.py:670-684]`, so **one condition in either VOID class
kills the whole strategy.**

## Result

| cell | `VOID_RAW` | `VOID_IN_STRATEGY` | **total VOID / 79** |
|---|---|---|---|
| `MGC:f60__p60` | 6 | 1 | **7** |
| `MGC:f60_240__p60` | 4 | 1 | **5** |
| `MGC:f240__p240` | 12 | 0 | **12** |
| `MGC:f60_240__p240` | 12 | 0 | **12** |
| `MCL:f60__p60` | 4 | 1 | **5** |
| `MCL:f60_240__p60` | 2 | 1 | **3** |
| `MCL:f240__p240` | 10 | 0 | **10** |
| `MCL:f60_240__p240` | 10 | 0 | **10** |

Names, per cell, at the **primary** binding:

| cell | VOID conditions |
|---|---|
| `MGC:f60__p60` | `mtf_aligned` `mtf_strongly_aligned` `oi_expanding` `oi_price_confirmation` `opening_range_breakout` `opening_range_fade` · *in-strategy:* `session_extreme_sweep` |
| `MGC:f60_240__p60` | `oi_expanding` `oi_price_confirmation` `opening_range_breakout` `opening_range_fade` · *in-strategy:* `session_extreme_sweep` |
| `MGC:f240__p240` | `away_from_hvn` `lvn_rejection` `mtf_aligned` `mtf_strongly_aligned` `oi_expanding` `oi_price_confirmation` `open_outside_value` `opening_range_breakout` `opening_range_fade` `poc_reversion` `value_area_breakout` `value_area_edge` |
| `MGC:f60_240__p240` | identical 12 to `f240__p240` |
| `MCL:f60__p60` | `mtf_aligned` `mtf_strongly_aligned` `oi_expanding` `oi_price_confirmation` · *in-strategy:* `session_extreme_sweep` |
| `MCL:f60_240__p60` | `oi_expanding` `oi_price_confirmation` · *in-strategy:* `session_extreme_sweep` |
| `MCL:f240__p240` | `away_from_hvn` `lvn_rejection` `mtf_aligned` `mtf_strongly_aligned` `oi_expanding` `oi_price_confirmation` `open_outside_value` `poc_reversion` `value_area_breakout` `value_area_edge` |
| `MCL:f60_240__p240` | identical 10 to `f240__p240` |

Plus, for `f60_240` only, the **bound-upward** binding the combinator creates for a `structure`
SIGNAL when a strategy carries ≥3 signals `[repo-verified: combinator.py:612-625]`: at that binding
the p60 cell inherits the 240m VOID set and the p240 cell inherits the 60m one. Recorded in
`census_verdicts.json` as `bound_240m_VOID` / `bound_60m_VOID` and applied in the population filter.

## Checked against the brief's list of known VOID configurations — 4 confirmed, 1 extended, 2 corrected

**1. All six `profile` conditions at 240m — CONFIRMED on both symbols, and this is stronger than
"VOLUME_PROFILE is dead".** All 6 are VOID at 240m: the 4 SIGNALs (`lvn_rejection`, `poc_reversion`,
`value_area_breakout`, `value_area_edge`) *and* the 2 FILTERs (`away_from_hvn`, `open_outside_value`).
The FILTERs matter more than the SIGNALs, because `profile` is an **optional** group for TREND, VWAP,
REVERSAL, OPENING_RANGE, MEAN_REVERSION, BREAKOUT and SUPPLY_DEMAND, and the two FILTERs are
**`optional_filters` of VOLUME_PROFILE and MEAN_REVERSION**
`[repo-verified: combinator.py, away_from_hvn in MEAN_REVERSION and VOLUME_PROFILE optional_filters]`.
So a 240m strategy in **any** of eight groups can be killed by a `profile` condition it drew as an
optional extra — it does not have to be a VOLUME_PROFILE strategy at all.

**2. Both MULTI_TIMEFRAME signals VOID at the frame's top timeframe — CONFIRMED, and the frame is
what decides it.** `mtf_aligned` / `mtf_strongly_aligned` are VOID in `f60__p60` (where 60 *is* the
top), LIVE in `f60_240__p60`, and VOID again in both p240 cells (where 240 is the top). So MULTI_TIMEFRAME
is expressible in **exactly one of my four cells per symbol** — 60m inside the 60m+240m group — and is
structurally void in the other three. That is the "does multi-timeframe alignment improve outcomes"
question answered partly by arithmetic before any expectancy is measured: on three of four cells the
question cannot be asked.

**3. `openinterest` anywhere — CONFIRMED, all 8 cells.** `oi_expanding` and `oi_price_confirmation`
VOID everywhere. `oi_expanding` is an `optional_filter` of MOMENTUM and BREAKOUT and
`oi_price_confirmation` sits in MOMENTUM's and BREAKOUT's `optional_groups`, so again the carriers are
not confined to one group.

**4. OPENING_RANGE at 1h — CONFIRMED for MGC, and MCL is clean, exactly as R1 measured.**
`opening_range_breakout` / `opening_range_fade` are VOID on MGC at 60m (RTH open 08:20 is off the
hourly grid; `or_minutes = 30` is hard-coded `[repo-verified: features.py:865]`) and **LIVE on MCL at
60m** (RTH open 09:00 is on the grid).

**5. EXTENDED, and new as far as I can tell: the opening range is a BASE-CLOCK object, so on MCL it
survives at 240m.** `MCL:f240__p240`'s VOID list does **not** contain the two opening-range
conditions, while `MGC:f240__p240`'s does. The cause is that `snap.opening_range` is built in
`_build_session_state`, which iterates **`self.base.bars`** `[repo-verified: features.py:867]` — the
60m series — not the primary timeframe's bars. So availability is set by the **base** timeframe and
the contract's `rth_open`, and is inherited unchanged by a 240m-primary strategy. Consequence: a
statement of the form "the opening range does not exist at 240m" is **frame-dependent, not
timeframe-dependent**, and `D30` as worded ("never constructed at 60m or 240m") does not hold on MCL
on a 60m base. I am not adjudicating D30 — flagging it, since it is in the open-defect list.

**6. CORRECTED — `StopKind.RANGE` (D49) has ZERO carriers in my population, so its collapse cannot
affect an EF2 row.** `StopKind.RANGE` appears only under `expand_exit_models(include_aggressive=True)`
`[repo-verified: combinator.py:100-106]`, `DEFAULT_EXITS = expand_exit_models()` leaves
`include_aggressive=False` `[repo-verified: combinator.py:112]`, and **no template's `exits` tuple
sets it**. Measured: `generate_strategies({MGC,MCL},[60,240],max_total=400)` yields stop kinds
`Counter({ATR: 143, STRUCTURE: 26, VWAP_BAND: 15})` on MGC and `Counter({ATR: 132, STRUCTURE: 31,
VWAP_BAND: 4})` on MCL — **no `RANGE`, no `FIXED_TICKS`**. D49 is real; it is unreachable from the
generator. The same measurement says `FIXED_TICKS` is never drawn either, so the three reachable
mechanisms are ATR, STRUCTURE and VWAP_BAND.

**7. `StopKind.VWAP_BAND` → `FIXED_TICKS` (D45) IS reachable — 15 MGC / 4 MCL carriers at
`max_total=400`, measured per cell in Burst 03.**

## Two verdicts of my own

**`session_extreme_sweep` is VOID_IN_STRATEGY at 60m on both symbols and LIVE at 240m.** It fires
only outside RTH at 60m — R1's D-L4 mechanism, replicated here on a different substrate and a
different span — and `rth_only=True` then vetoes every one. At 240m it becomes live, because a 240m
bar's high spans pre-RTH hours while the RTH accumulator only holds RTH bars, so the bar can exceed
the running session extreme on a bar that is itself inside RTH. **So its deadness is a 60m artefact,
not a property of the condition**, which is the per-(symbol, timeframe) point the `VOID` vocabulary
was introduced to make.

**Zero swallowed exceptions.** `CONDITION_ERRORS` is empty in all six census passes
`[measured: census.json, "condition_errors": {} for every frame]`. So no VOID verdict here is the
"fifteen conditions raised on every bar and were recorded as a 0% trigger rate" failure the code's own
docstring warns about `[repo-verified: base.py:131-146]`.
