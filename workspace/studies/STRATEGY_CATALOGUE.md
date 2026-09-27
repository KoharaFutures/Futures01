# The tested strategy universe — what was actually searched

**Written by:** parent session, 2026-09-27, at the account owner's request ("list the strategies you
have tested"). **Every row extracted from the code**, not from prose:
`futures_agents/strategies/combinator.py` (`TEMPLATES`, `expand_exit_models`),
`futures_agents/strategies/library.py` (`CONDITIONS`), `futures_agents/strategies/profiles.py`
(`groups_for`). `BRIEF.md` calls this "the catalogue this repository does not have"; this is it for
the *tested* population, which is narrower than the strategy space that exists in the world.

**Nothing here is a hand-written strategy.** The population is generated combinatorially: a
**template** names condition *groups*, the combinator picks one condition from each required group
plus 0..n from the optional groups, crosses that with exit models and both directions, and emits a
`Strategy`. So "a strategy" here is one point in `template × conditions × exit × direction`, and the
~3M figure counts those points.

---

## 1. The thirteen strategy families (`TEMPLATES`)

`required_groups` takes exactly one condition from each named group. `optional_groups` adds
0..`max_optional` more from *distinct* groups. `base_filters` are **nailed on** — an assumption, not
a tested variable. `optional_filters` are switched on and off, producing a variant each way.

| family | required (one each) | optional (0..n) | nailed base filters | exits |
|---|---|---|---|---|
| **TREND** — trend continuation, structure and momentum aligned with the regime | trend, structure | 0..3 of momentum, orderflow, volume, multitimeframe, vwap, profile, imbalance, regime, candlestick | volatility_normal, volume_not_thin, **regime_trending** | 3 |
| **PULLBACK** — buy the dip inside an established trend | trend, meanreversion | 0..3 of structure, vwap, orderflow, multitimeframe, fibonacci, supplydemand | volatility_normal, volume_not_thin, **mtf_not_conflicted** | 4 |
| **VWAP** — VWAP as the session's fair-value reference | vwap | 0..3 of orderflow, momentum, structure, volume, trend, profile | volatility_normal, volume_not_thin | 9 |
| **REVERSAL** — exhaustion and absorption against the prevailing move | meanreversion, **orderflow** | 0..3 of momentum, liquidity, structure, vwap, supplydemand, profile, fibonacci, candlestick | volatility_normal, volume_not_thin, **avoid_lunch** | 4 |
| **MOMENTUM** — momentum ignition confirmed by participation | momentum, **volume** | 0..3 of trend, orderflow, structure, multitimeframe, imbalance, openinterest, regime | volatility_normal | 3 |
| **OPENING_RANGE** — opening-range breakout and failure | liquidity | 0..3 of volume, orderflow, momentum, trend, vwap, profile | volatility_normal, volume_not_thin, **opening_drive_window** | 9 |
| **LIQUIDITY** — stop runs at reference levels, then reversion | liquidity | 0..3 of orderflow, structure, vwap, momentum, volume, supplydemand, imbalance, candlestick | volatility_normal, volume_not_thin, **after_opening_range** | 9 |
| **MEAN_REVERSION** — fade statistical extension in a ranging market | meanreversion | 0..3 of momentum, vwap, orderflow, structure, profile, fibonacci | volatility_normal, volume_not_thin, **regime_ranging** | 4 |
| **BREAKOUT** — expansion out of compression | structure, **volume** | 0..3 of trend, momentum, orderflow, liquidity, imbalance, profile, openinterest | **volatility_compressed**, volume_not_thin | 3 |
| **MULTI_TIMEFRAME** — higher-timeframe alignment as the primary edge | multitimeframe, structure | 0..2 of trend, momentum, vwap, orderflow, fibonacci, supplydemand | volatility_normal, volume_not_thin | 3 |
| **VOLUME_PROFILE** — trade location against the prior session's volume distribution | profile | 0..3 of volume, orderflow, vwap, structure, trend, momentum | volatility_normal, volume_not_thin | 9 |
| **SUPPLY_DEMAND** — reaction at zones a decisive move departed from | supplydemand | 0..3 of structure, orderflow, imbalance, trend, momentum, volume, candlestick | volatility_normal, volume_not_thin | 9 |
| **FIBONACCI** — retracement of the last confirmed leg, in the trend's direction | fibonacci, trend | 0..2 of structure, momentum, vwap, orderflow, supplydemand | volatility_normal, volume_not_thin | 4 |

All thirteen run **both directions** (LONG and SHORT). Four carry `exclusive` pairs the combinator
refuses to co-emit (VWAP 1, VOLUME_PROFILE 2, SUPPLY_DEMAND 2, FIBONACCI 3).

### Which families each symbol was actually tested with (`profiles.py`)

A profile is a prior about what to test, not a claim about what works. An **unprofiled symbol gets
all thirteen.**

| symbol | families tested | excluded by profile |
|---|---|---|
| **MGC** | 6 — TREND, SUPPLY_DEMAND, FIBONACCI, MULTI_TIMEFRAME, MEAN_REVERSION, VOLUME_PROFILE | PULLBACK, VWAP, REVERSAL, MOMENTUM, OPENING_RANGE, LIQUIDITY, BREAKOUT |
| **MES** | 7 — VWAP, VOLUME_PROFILE, MEAN_REVERSION, PULLBACK, REVERSAL, LIQUIDITY, MULTI_TIMEFRAME | TREND, MOMENTUM, OPENING_RANGE, BREAKOUT, SUPPLY_DEMAND, FIBONACCI |
| **MNQ** | 7 — MOMENTUM, TREND, BREAKOUT, OPENING_RANGE, MULTI_TIMEFRAME, LIQUIDITY, PULLBACK | VWAP, REVERSAL, MEAN_REVERSION, VOLUME_PROFILE, SUPPLY_DEMAND, FIBONACCI |
| **MCL** | **all 13** — `groups_for("MCL", …)` returns empty, so nothing is narrowed | none |

### What those two columns actually are — asked by the account owner, 2026-09-27

**"Families tested" is a generation filter, not a result.** `combinator.py:497-499` calls
`groups_for(symbol, [t.group for t in TEMPLATES])` and builds strategies **only** from the groups it
returns. So for a symbol, an excluded family means **zero strategies of that family were ever
generated, therefore zero were ever backtested, therefore it appears in no result, no ranking and no
top 10.** It does not mean the family was tried and lost. Nothing was measured about it at all.

**Where the lists come from.** `SYMBOL_PROFILES` in `profiles.py` — three hand-written priors (MNQ,
MES, MGC), each with a rationale. MCL has **no entry**, `groups_for` returns empty, and the
combinator's fallback gives it all thirteen, so *the only symbol tested broadly is the one nobody
wrote a prior for.* The file is explicit that this is "a prior about what to test, not a claim about
what works", and that `groups` can be overridden to check one — which is how a prior gets falsified
rather than trusted. **No study in this repository has overridden one.**

**The recorded reasons, verbatim from the code.** Each profile carries an `excluded` dict so an
omission is auditable:

| symbol | family | reason given |
|---|---|---|
| MGC | OPENING_RANGE | "gold's session opens at 08:20 and the template's 150-minute window is calibrated to the equity open" |
| MGC | MOMENTUM | "the 1m/5m ignition rules need the intraday range MNQ has and gold does not" |
| MGC | BREAKOUT | "compression-to-expansion at intraday scale; on a 23-hour product this mostly fires on session handoffs" |
| MES | MOMENTUM | "ignition is MNQ's trade; on MES the same rules fire into rotation" |
| MES | OPENING_RANGE | "the opening drive is tested on MNQ, which has the range to make the break mean something" |
| MNQ | MEAN_REVERSION | "fading the most persistent of the three index micros is the trade with the worst prior here; MES is where rotation is tested" |
| MNQ | FIBONACCI | "retracement depth needs a stable leg, and MNQ's legs are the shortest-lived — tested on MGC instead" |

**But `excluded` is a strict subset of what is absent, and the gap is exactly four per symbol.**
Verified:

```
MNQ: tested 7  absent 6  documented 2  NO RECORDED REASON 4 -> VWAP, REVERSAL, VOLUME_PROFILE, SUPPLY_DEMAND
MES: tested 7  absent 6  documented 2  NO RECORDED REASON 4 -> TREND, BREAKOUT, SUPPLY_DEMAND, FIBONACCI
MGC: tested 6  absent 7  documented 3  NO RECORDED REASON 4 -> PULLBACK, VWAP, REVERSAL, LIQUIDITY
```

**Twelve family-symbol cells were dropped with no recorded reason at all** — the profile simply does
not list them, and `excluded` exists precisely so that could not happen silently. The docstring's
`unknown_groups()` guard catches a *typo* in a listed name; nothing catches a family that is neither
listed nor excused.

### Four of the five substantive profile fields are read only by the test suite

`SymbolProfile` declares `groups`, `timeframes`, `timeframe_groups`, `rth_only`, `rationale` and
`excluded`. **The production path imports exactly one name from this module** — `groups_for`
(`combinator.py:497`). Grepping every consumer: the only other readers of `profile_for`,
`timeframes_for`, `SYMBOL_PROFILES.rth_only` or `.excluded` anywhere in the repository are
`tests/test_symbol_profiles.py` and two agents' population builders (EF5, EF3 — both importing
`groups_for` only, and EF5's header states the narrowing is deliberately not applied).

**So the tests assert these fields and the generator ignores them.** `test_symbol_profiles.py:98`
asserts `profile_for("MGC").rth_only is False`; `:91` asserts `min(timeframes_for("MGC")) >= 15`.
Both pass. Neither reaches a generated strategy.

**This is the mechanism behind a number the edge programme spent three agents measuring.** EF2 found
`rth_only` is `True` on **184/184 MGC and 167/167 MCL** generated strategies, and R1 on 314/314 — and
**MGC's own profile asks for `rth_only=False`**, with the longest rationale in the file behind it:

> *"Not an equity product and it should stop being tested like one. … because the real drivers — the
> dollar, real yields, the London fix — move it around the clock, confining it to any RTH throws away
> most of its information."*

That instruction was written, tested, and never executed. It is the same class as `D53`/`R3-A-5` —
the scope vocabulary is inert in the generation path — and it means **the `rth_only=False` paired arm
this programme identified as its one endorsed route is what MGC's profile asked for from the
beginning.** `timeframes` is inert the same way: MGC's profile says 15/60/240 and the scalp programme
generated MGC at 5m regardless, which was the right call and was not the profile's.

**Consequence for any per-symbol claim.** A symbol's "best strategy" can only ever be the best of
what its profile let through: MGC's could never be a BREAKOUT, MES's could never be a MOMENTUM,
MNQ's could never be a VWAP. And MCL — the one symbol tested across all thirteen families, the
widest search of the four — returned the **worst** result anywhere (largest *t* +1.12, failing even
`free_t = 1.177`). A wider search returning a worse best is what an absent edge looks like.

**Only MULTI_TIMEFRAME is tested on all four symbols.** MGC and MES share 3 families, MGC and MNQ
share 3, MES and MNQ share 3. So a large part of "per-symbol uniqueness" in this repo is the profile
table deciding what was *asked*, not the data deciding what *worked* — worth knowing before reading
any per-symbol comparison.

---

## 2. The 79 conditions, in 19 groups — **53 SIGNAL / 26 FILTER**

`[S]` = SIGNAL (can trigger an entry). `[F]` = FILTER (can only veto). `Strategy.evaluate` is a
**strict AND with no `min_signals`** (`base.py:670-684`), so one condition that cannot fire kills the
whole strategy rather than weakening it.

| group | n | conditions |
|---|---|---|
| candlestick | 5 | candle_close_strength[S], candle_decisive_close[S], candle_engulfing[S], candle_reversal[S], inside_bar_compression[F] |
| fibonacci | 4 | fib_extension_reached[S], fib_golden_pocket[S], fib_shallow_retrace[S], fib_sr_confluence[F] |
| imbalance | 3 | imbalance_bar[S], imbalance_pullback[S], no_recent_imbalance[F] |
| liquidity | 7 | initial_balance_break[S], opening_range_breakout[S], opening_range_fade[S], overnight_sweep[S], prior_day_breakout[S], prior_day_sweep[S], **session_extreme_sweep[S]** |
| meanreversion | 3 | bollinger_extreme[S], bollinger_mean_pull[S], keltner_outside[S] |
| momentum | 6 | macd_directional[S], macd_hist_direction[S], rsi_directional[S], rsi_extreme_reversal[S], stoch_directional[S], stoch_extreme[S] |
| multitimeframe | 3 | mtf_aligned[S], mtf_strongly_aligned[S], mtf_not_conflicted[F] |
| **news** | 3 | no_imminent_release[F], **outside_news_blackout[F]**, post_news_window[F] |
| **openinterest** | 2 | **oi_expanding[F], oi_price_confirmation[S]** |
| **orderflow** | 3 | cvd_directional[S], delta_confirms_bar[S], delta_divergence[S] |
| profile | 6 | lvn_rejection[S], poc_reversion[S], value_area_breakout[S], value_area_edge[S], away_from_hvn[F], open_outside_value[F] |
| regime | 3 | regime_matches_direction[S], regime_ranging[F], regime_trending[F] |
| structure | 5 | break_of_structure[S], **fvg_nearby[S]**, pullback_to_support[S], **range_position_extreme[S]**, structure_trend[S] |
| supplydemand | 3 | fresh_zone_approach[S], zone_touch[S], away_from_zone[F] |
| **time** | 4 | after_opening_range[F], avoid_lunch[F], opening_drive_window[F], power_hour[F] |
| trend | 8 | di_direction[S], ema_fast_above_slow[S], ema_stack[S], price_above_ema200[S], price_above_ema50[S], slope_directional[S], adx_trending[F], efficiency_high[F] |
| **volatility** | 3 | volatility_compressed[F], volatility_expanding[F], volatility_normal[F] |
| **volume** | 3 | relative_volume_high[F], volume_not_thin[F], volume_surge[F] |
| vwap | 5 | above_vwap[S], **vwap_band1_bounce[S]**, vwap_band_extension[S], vwap_reclaim[S], vwap_proximity[F] |

### Four groups contain **zero SIGNALs**: `volume`, `volatility`, `time`, `news`

Three of those are never required by a template, so they can only ever filter. **`volume` is
required by MOMENTUM and BREAKOUT** — and a required group with no SIGNAL member is **silently
dropped** (`combinator.py:361-369`, **D54**). Verified here:

```
volume   0/3 SIGNAL   required by: MOMENTUM, BREAKOUT   <-- never enforced
```

So MOMENTUM and BREAKOUT declare a volume requirement the generator does not apply — 24 of 40
generated MNQ MOMENTUM strategies carry no volume condition at all. **MNQ's profile includes both.**

---

## 3. The nine exit models (`expand_exit_models()`), and their two stop kinds

| # | stop | mult | target kind | targets (R) | scale-out | BE at | time stop | session close |
|---|---|---|---|---|---|---|---|---|
| 0 | ATR | 1.5 | R_MULTIPLE | 1.0, 2.0, 3.0 | .5/.3/.2 | 1.0R | 60 bars | **True** |
| 1 | ATR | 2.5 | R_MULTIPLE | 1.0, 2.0 | .6/.4 | 1.0R | 90 | **True** |
| 2 | ATR | 1.0 | R_MULTIPLE | 1.5, 3.0, 5.0 | .4/.3/.3 | 1.5R | 120 | **True** |
| **3** | ATR | 1.2 | R_MULTIPLE | **1.2 only** | 1.0 | — | 30 | **True** |
| 4 | STRUCTURE | 1.0 | R_MULTIPLE | 1.0, 2.0, 3.0 | .5/.3/.2 | 1.0R | 80 | **True** |
| 5 | VWAP_BAND | 1.0 | R_MULTIPLE | 1.0, 2.0 | .5/.5 | 1.0R | 60 | **True** |
| 6 | ATR | 1.0 | ANCHOR_ATR | 2.0, 4.0 | .5/.5 | 1.5R | 40 | **False** |
| 7 | ATR | 0.75 | ANCHOR_ATR | 2.0, 4.0, 8.0 | .4/.3/.3 | 2.0R | 60 | **False** |
| 8 | STRUCTURE | 1.0 | ANCHOR_STRUCTURE | 1.0, 2.0, 3.0 | .4/.3/.3 | 1.5R | 50 | **False** |

**Three structural facts in that table.**

1. **`exit_at_session_close=False` is exactly the three `ANCHOR_*` rows** — so session control is
   perfectly confounded with target kind (**D19**), and it is *why* the flag is False on 58 of 184
   MGC and 90 of 185 MNQ generated strategies. There was never an independent session arm.
2. **Only ATR (6), STRUCTURE (2) and VWAP_BAND (1) appear.** `StopKind.FIXED_TICKS` and
   `StopKind.RANGE` are declared in `base.py:187-192` and have **zero carriers** in any generated
   population — `RANGE` only under `include_aggressive=True`, which nothing sets (**D49**).
3. **The smallest `time_stop_bars` is 30**, against a 22-bar cap under the 18:00→16:00 rule — so
   `TIME` exits are **0 of 103,191 trades** and the time-stop dimension does not exist in the swing
   programme.

Exit **index 3** is the one `D8` records as unable to trade, and two exits collide on one id.

---

## 4. What in this catalogue could not have worked — read before any per-family claim

These are not failures to find edge. They are configurations where the arithmetic forbids a trade,
so the budget spent on them was not a test that failed but a test that could not have succeeded.

| item | verdict | consequence |
|---|---|---|
| `openinterest` (both conditions) | **DEAD** | the column is absent from every CSV (`open_time,open,high,low,close,volume`). The SIGNAL yields zero trades; the FILTER `oi_expanding`, never passing, **vetoes every entry**. Optional on MOMENTUM and BREAKOUT — **both in MNQ's profile** (D47). |
| `orderflow` (all three) | **PROXY** | there is no delta or tick data; all three are computed from OHLCV. **REVERSAL requires this group**, so REVERSAL's defining signal is a proxy (`BRIEF.md`; D46 for `detect_imbalances`). |
| `session_extreme_sweep` | **VOID** under the session rule | all **48** fires across two symbols and three timeframes fall in 16:00–16:55 ET, inside the forbidden window. A dead member of a required group (EF5). |
| `volatility_compressed` under `rth_only=True` | **VOID** at MES 15m | 0 of 1,066 RTH bars, because `atr_percentile` is taken over 24-hour history. BREAKOUT **nails it into `base_filters`**, so all **138 MES 15m BREAKOUT strategies take zero trades** (EF5; needs replication). |
| `range_position_extreme` inside REVERSAL | **guaranteed zero** | D25. |
| `vwap_band1_bounce` at 1440m | **VOID**, fires 0/0 | band-1 half-width < 1 tick on 2511/2511 MGC and 1859/1859 MES daily bars. `vwap` is VWAP's *required* group, so **every daily VWAP strategy is a bar-shape strategy wearing a VWAP name** (D52). |
| `above_vwap` at 1440m | **MISNAMED** | collapses to `sign(CLV)`; matches `candle_close_strength` on 1092/1092 co-firings (D52). |
| `outside_news_blackout` | **identity filter** on a `:00` grid | a 25-minute window, five of six HIGH rules print at `:30`, 4,992 of 5,000 hourly bars open at `:00` → MGC **0 of 1,093** eligible bars removed. An A/B on it is a strategy against itself (D57). |
| all three `news` conditions at 1440m | **DEGENERATE** | bars stamped 00:00 ET, so `minutes_since` is never in (15,60]. Blast radius zero — the combinator can emit no carrier (D47). |
| `mtf_aligned` vs `mtf_strongly_aligned` at 240m | **identical** on 1348/1348 bars | the 240m MTF arm tested one signal, not two (ADJ-14). |
| the whole `multitimeframe` group at 1440m | **DEGENERATE** | `align_bucket` ignores `minutes` above 1440, so `FRAMES[1440] = [1440, 7200]` confirms the daily series against a **lagged copy of itself**, OHLCV bit-identical 2510/2510 MGC. Every daily MTF statement is a lagged-autocorrelation test (D50). |
| `OPENING_RANGE` at 60m and 240m | **never constructed** | `or_minutes = 30` against a per-symbol `rth_open` off the hourly grid (D30); kill-zone windows arithmetically impossible at 240m (D31). |
| `volume` as a **required** group | **silently dropped** | zero SIGNAL members; MOMENTUM and BREAKOUT's volume requirement is never enforced (D54). |
| `ExitModel` index 3 | cannot trade | D8, and two exits collide on one id. |
| `StopKind.FIXED_TICKS`, `StopKind.RANGE` | **zero carriers** | never emitted by the default generator (D49). |
| `TIME` exits under the 22-hour rule | **0 of 103,191** | min `time_stop_bars` 30 vs a 22-bar cap. |

**Aggregate, measured:** **19.0% of generated strategies carry at least one VOID condition** — MGC
11.5%, MCL 13.9%, MES 22.6%, **MNQ 27.4%** — and because `evaluate` is a strict AND, that is the
whole strategy's zero. Separately, **60–82% of generated strategies never fire at all**, and seven
structurally-zero configurations are on record.

---

## 5. What this list is not

It is the space that was **searched**, and its width is exactly why nothing in it is reportable:
`free_t = sqrt(2·ln n)`, and ≥ 2,975,629 candidates were generated. It is **not** the space of
futures strategies that exist. Families the combinator cannot express at all include every **ordered
sequence** (D37 — sweep→shift→retrace can only be built as a single condition, and then cannot be
ablated leg by leg, R-10), anything needing **order-flow or open-interest data**, and anything
needing a **roll-adjusted long series**, which §2 of `SERIES_AUDIT.md` shows does not exist here for
either independent contract.
