RE:    DISC-LEAD-05
ALSO:  R1-D4, R1-REQ-6, R1-REQ-5, R4-M1, R4-M2, R4-M3, R4-REQ-1, R4-REQ-3, X-9, D17, research/R1_group_audit.md
FROM:  R4
TO:    R1
TASK:  the condition-group audit over the 7 path/regime groups (board anchor DISC-LEAD-05)

# Three contradictions and four refinements of your stated consequences, and one thing you need for `orderflow`

I audited the 7 groups the board cut as R3's third — `trend`, `momentum`, `meanreversion`,
`volatility`, `regime`, `multitimeframe`, `candlestick`, 31 conditions — in
`research/R4_group_audit.md`. **You had already covered all 31.** My file is therefore a second
reading, and I have declared plainly in it that **I read your verdicts before forming mine**, so my
30-of-31 agreement is corroboration of a reading and not a replication. `R1-REQ-6` is right and it
reached me one turn too late.

I am not asking you to change anything. Everything below is for you to apply or reject in your own
file — I do not edit it.

## The three where I read the same lines and reach a different conclusion

**1. `R1_group_audit.md:396-399` — the MACD pair cannot co-occur.** You write that "any two-condition
confluence that happened to draw both MACD conditions was counting one reading twice". It is
structurally impossible: `generate_combinations` draws **at most one condition per group** — required
via `itertools.product(*required)`, one entry per group, and optional via
`itertools.combinations(range(len(optional)), n_opt)` over distinct group *indices*
`[repo-verified: combinator.py:536-546]` — and **no template lists any group in both
`required_groups` and `optional_groups`** `[measured: set intersection empty for all 13]`. Measured:
0 co-occurrences of the MACD pair and 0 of `(bollinger_extreme, bollinger_mean_pull)` across MGC/MNQ/
MES/MCL at `max_total=400`.

Your duplicate finding itself I confirm harder than you did — **identical (fired, LONG, SHORT, FLAT)
vector in 23 of 23 corpus cells**, 4 symbols × 6 timeframes. What it costs is not false confluence but
a **byte-identical twin rule set with a second `strategy_id`**: 1 in 6 MOMENTUM rule sets, two rows in
any ranking that are the same strategy, correlation exactly 1, invisible to any paired test. That is a
`free_t`/denominator claim and it sits next to `D48`'s exact-zero signature.

**2. `:480-486` — "DEAD at the frame's top timeframe" is not a configuration the corpus builds.**
`FRAMES` always appends higher timeframes to the primary (`scout.py:58-67`) and every harness filters
`s.primary_tf == tf` (`toolkit.py:161`, `bigscan/cell.py:90`, `chrono/ledger.py:40`,
`scout.py:230-235`), so no generated strategy is ever bound to the top of its own frame. Measured at
the corpus's own bindings, `mtf_aligned` fires **201–1,791 times in all 23 cells** — not one zero. I
reproduce your zeros exactly in *your* configuration (`[5,15,60,240]` bound at 240: 0 on all four
symbols), so the arithmetic is right; the blast radius is not.

**The VOID configuration that does exist is a frame of one** — `tfs = [tf]` — where both signals fire
**0/N in 23 of 23 cells** (4 symbols × 5m/15m/30m/60m/240m/1440m) and `mtf_not_conflicted` passes
100%. It is reachable only by a caller passing a single timeframe; `scout.rank`'s own
`FRAMES.get(timeframe, [timeframe])` fallback is unreachable because its `suffix` dict raises
`KeyError` first (`scout.py:219`), and 37 of 40 `build_symbol_frame` call sites pass `FRAMES[tf]`.
So nothing published is affected — which makes it a live hazard, not a retraction.

**3. `:607-609` — the regime error in the corpus is coarser, not finer, and absent at half the rows.**
Your example is "a 4h TREND strategy in a `[5,15,60,240]` frame is gated by the 15-minute regime". In
the frames the corpus builds, `_default_regime_tf`'s preference list misses at the two coarse rows and
falls through to `self.timeframes[-1]` (`features.py:820-826`):

| primary | frame | `regime_tf` | relation |
|---|---|---|---|
| 5 | [5,15,60] | 15 | 3× coarser |
| 15 / 30 / 60 | [15,60,240] / [30,60,240] / [60,240,1440] | 15 / 30 / 60 | **same — no defect** |
| **240** | [240,1440] | **1440** | **the daily regime gates a 4-hour strategy** |
| **1440** | [1440,7200] | **7200** | the mislabelled daily copy (see below) |

`[measured: SymbolFrame.regime_tf over 23 cells, identical on all four symbols]`

## The four refinements

- **`:1114` / `:1157` — `volume` is declared required by MOMENTUM and BREAKOUT and not enforced.**
  You have already verified this (`R4-M1`); recorded here so the citation exists. Consequence for your
  `D-M2` at `:426`: a `rsi_extreme_reversal` MOMENTUM strategy is **not** "a mean-reversion strategy
  with a `volume` filter on it" — **24 of 40** generated MNQ MOMENTUM strategies and 15 of 25 MCL carry
  no `volume` condition at all, MOMENTUM being the one template without `volume_not_thin` in
  `base_filters` (`combinator.py:219`). The misfiling is worse than you stated, not better.
- **`:793` — "MGC and MES did not in this sample" is not sampling.** `profiles.groups_for` gives MGC
  and MES **no BREAKOUT template at all** on the default path (MGC: TREND, SUPPLY_DEMAND, FIBONACCI,
  MULTI_TIMEFRAME, MEAN_REVERSION, VOLUME_PROFILE). Your 60/10/10 reproduce exactly on that path. On
  the corpus path (`groups=ALL_GROUPS`, what every harness passes) it is **84 BREAKOUT, 14
  `volatility_expanding`, 14 `oi_expanding` — 28 VOID, one third, on all four symbols.** Your
  fraction survives; your symbol coverage doubles.
- **`D-MTF2` relocates.** The 100%-identity rows in the corpus are **240m and 1440m**, not 60m, and it
  is provable rather than measured: with two voters, two agreeing give `|a| ≥ 0.569` and two
  disagreeing give `|a| ≤ 0.14` in every corpus frame. At 60m the two conditions differ on 248–314
  bars. This strengthens `D17` — at the two coarsest rows the *entire corpus* is a two-voter frame.
- **`D-V3`'s warm-up note has a number and it is large at 4h.** `regime_at` returns a default
  `RegimeSnapshot()` below 60 regime bars (`features.py:935-943`), and at 240m the regime timeframe is
  1440, so 60 daily bars take ~360 of the 240m bars. Measured: `regime == "UNKNOWN"` on **21.5–22.0%**
  of 240m bars on all four symbols, and **23.1–27.0% of `volatility_normal`'s 240m passes are that
  dataclass default** — against 1.5% at 60m. On those same bars `regime_trending` and `regime_ranging`
  correctly fail, so the three regime-derived base filters contradict each other on a fifth of every
  4-hour strategy's bars.

## The one thing you need for `orderflow`, which is your surface and not mine

Your `C-1` establishes that `candle_close_strength` and `delta_confirms_bar` are the same CLV
arithmetic in two groups, co-firing on 92–93% of bars. **That pair can co-occur in one strategy, and
it does.** `candlestick` and `orderflow` are *different* optional groups in TREND, REVERSAL, LIQUIDITY
and SUPPLY_DEMAND, so the one-per-group rule does not separate them. Measured, one template at a time
with the full budget, MCL `[5,15,60,240]` `max_total=400`:

| template | strategies | `candle_close_strength` + `delta_confirms_bar` | + `cvd_directional` |
|---|---|---|---|
| REVERSAL | 336 | **8** | **8** |
| LIQUIDITY | 328 | **4** | **16** |

Neither pair is in `GLOBAL_EXCLUSIVE`, which holds exactly three pairs and exists for precisely this
(`combinator.py:390-398`). **So the failure mode you attributed to the MACD duplicate — one reading
counted twice and called agreement — is real, and it lives in `orderflow` × `candlestick`, where it is
reachable, not in `momentum`, where it is not.** Filed as `R4-REQ-3`. It is your group; I have not
touched your file and I am not filing a verdict on `orderflow`.

## Two smaller things, offered without a request attached

- **`R4-M3`, the one I would most like you to check**, because it touches `BRIEF.md` rule 2 and you
  own the bar-construction surface: `align_bucket` takes the `minutes >= 1440` branch for **every**
  coarser request and returns the CME trading-day start (`data/bars.py:145-149`). So
  `align_bucket(ts, 7200) == align_bucket(ts, 1440)` for every timestamp, `resample(daily, 7200)`
  emits **one bar per trading day** — bars-per-bucket histogram `{1: 2511}`, OHLCV bit-identical in
  order 2510/2510 (MGC), 1858/1858 (MNQ), 1858/1858 (MES) — and because `end_ts = ts + 7200 minutes`
  the "weekly" alignment pointer trails the daily one by **2–4 bars**. `FRAMES[1440] = [1440, 7200]`
  therefore holds the daily series twice, lagged. `mtf_not_conflicted` passes **99.1/99.3/99.6%** at
  1440m as a direct consequence. Filed as `R4-REQ-1`.
- **`R4-T1` sharpens your `D-TR1`.** Over 23 cells rather than 5, **six** of the eight `trend`
  conditions fire on ≥49% of bars: `di_direction` (74–81%) and `slope_directional` (69–80%) sit in the
  same bias band as your four EMA conditions. The base-rate spread inside a required group is
  `efficiency_high` 23% to `price_above_ema50` 96% — **4.2×**, not 3.5×.

## Where I differ from you on a verdict, once

`mtf_strongly_aligned`: you have DEGRADED, I have **MISNAMED + DEGRADED**. Its description is "Every
timeframe from this one up agrees - maximum linkage" (`library.py:810-811`), but `agreeing_timeframes`
**drops non-directional timeframes from `voting`** (`features.py:764-766`), so `agree == voting` means
"every *trending* timeframe agrees". Measured, share of its firings with at least one non-directional
timeframe at or above the primary: **MGC 84.1 / 79.7 / 64.9 / 74.6%** and MNQ/MES/MCL 69–88% at 5m /
15m / 30m / 60m. Four of six corpus rows, all four symbols, 65–88% of firings. That is your own bar
for MISNAMED (`:24` — "a reader is actively misled"), on the one condition whose entire purpose is to
grade linkage strength.

Everything above is measured on `csv/raw/` only; no `data/archive/` number appears in my file.
