# R4_REQUESTS — sub-task requests arising from `MGR-T4`

Shape per `PIPELINE.md` §3. Ids per `REGISTRY.md`: `R4-REQ-<n>`, my own prefix, allocated by me.
Per standing rule **R-9** I describe each defect and do **not** name a `D<n>`.

---

## R4-REQ-1 `align_bucket` ignores `minutes` for anything above 1440, so `FRAMES[1440]`'s "weekly" timeframe is the daily series relabelled and lagged

- **Arose in:** `MGR-T4`, measuring `multitimeframe` deadness per timeframe against the frames the
  corpus actually builds.
- **The ask:** allocate a defect number, and add a sub-task to fix `align_bucket` plus a regression
  test. `data/bars.py:145-149` takes the `minutes >= 1440` branch for **every** coarser request and
  returns the CME trading-day start, so `align_bucket(ts, 7200) == align_bucket(ts, 1440)` for every
  timestamp. `resample(daily, 7200)` therefore emits **one bar per trading day**, OHLCV bit-identical
  to the daily series in order (2510/2510 MGC, 1858/1858 MNQ, 1858/1858 MES), labelled
  `Bar.minutes = 7200`. Because `end_ts = ts + 7200 minutes`, `_build_alignment` lags the "weekly"
  pointer **2–4 bars** behind the daily one.
- **Why it cannot wait:** `FRAMES[1440] = [1440, 7200]` is the shipped daily frame
  (`scout.py:58-67`), so **every daily-timeframe multi-timeframe statement in this repository is a
  lagged-autocorrelation test on one series.** `mtf_not_conflicted` — PULLBACK's base filter — passes
  99.1%/99.3%/99.6% at 1440m as a direct consequence, i.e. it is not a filter there. It also bears on
  `BRIEF.md` rule 2, whose z = −4.09 was measured with this arm included.
- **What it blocks:** nothing of mine; it invalidates the daily row of any multi-timeframe result and
  it is a prerequisite for anyone re-asking whether alignment helps.
- **My estimate of its size:** the fix is small (one branch, one `expected` check). Deciding what to do
  about results already measured on the 1440 row is not mine to size.

## R4-REQ-2 a required group with no SIGNAL member is silently dropped, and `volume` is one

- **Arose in:** `MGR-T4`, building the template requirement map from `TEMPLATES` rather than
  inheriting it.
- **The ask:** allocate a defect number for `_signal_pools`' silent drop (`combinator.py:361-369`,
  `[p for p in required if p]`, with `if not required: continue` at `:513`), and decide whether
  MOMENTUM's and BREAKOUT's declared `volume` requirement should be enforced, removed from
  `required_groups`, or documented as advisory. All three `volume` conditions are FILTERs, so both
  templates' effective requirement is one group, not two. Measured: **24 of 40** generated MNQ
  MOMENTUM strategies and 15 of 25 MCL contain no `volume` condition at all — MOMENTUM is also the one
  template without `volume_not_thin` in `base_filters`.
- **Why it cannot wait / why it can:** **it can wait.** Nothing measured is wrong; the heading
  overstates what was required. But the mechanism is silent and un-guarded, and moving any condition
  from SIGNAL to FILTER would delete a template's requirement with no error.
- **What it blocks:** nothing. It corrects two rows of the published requirement map.
- **My estimate:** small. R1 has already verified the finding independently.

## R4-REQ-3 `GLOBAL_EXCLUSIVE` omits the one duplicate pair that is actually reachable, and the two it omits that are provable

- **Arose in:** `MGR-T4`, auditing `momentum`, `meanreversion` and `candlestick` for duplication.
- **The ask:** add a sub-task to (a) add `(candle_close_strength, delta_confirms_bar)` and
  `(candle_close_strength, cvd_directional)` to `GLOBAL_EXCLUSIVE` or explain why not — they are the
  same CLV arithmetic in two groups, they **co-occur in generated strategies** (8 REVERSAL and 4/16
  LIQUIDITY in a 400-cap probe on MCL), and R1's `C-1` measured them co-firing on 92–93% of bars; and
  (b) resolve the two provable same-group duplicates by **deleting a condition**, since an exclusion
  cannot help there: `macd_hist_direction` is `macd_directional` (identical fire+direction vector in
  **23 of 23** cells) and `bollinger_extreme ⊂ bollinger_mean_pull` (601/601, 686/686, … in 8 of 8
  cells, same direction).
- **Why it cannot wait / why it can:** **it can wait.** (a) is a live false-confluence: two signals
  filed as independent evidence that are one reading. (b) is denominator inflation — every MOMENTUM
  rule set has a 1-in-6 chance of being a byte-identical twin of another with a different
  `strategy_id`, which is a `free_t` accounting question and adjacent to `D48`'s exact-zero signature.
- **What it blocks:** nothing. It changes how `momentum` and REVERSAL rows must be counted.
- **My estimate:** small for (a); (b) is a one-line deletion plus whatever citation repair it forces.

## R4-REQ-4 `scout.rank` cannot be called on 30m, which is a `FRAMES` key

- **Arose in:** `MGR-T4`, checking whether the frame-of-one VOID configuration is reachable.
- **The ask:** a one-line decision — `scout.rank`'s `suffix` dict covers `{1440, 240, 60, 15, 5}`
  (`scout.py:219`) while `FRAMES` covers `{5, 15, 30, 60, 240, 1440}` (`scout.py:58-67`), so
  `rank(sym, timeframe=30)` raises `KeyError` on a timeframe the module itself declares supported.
  The same mismatch is what makes the `FRAMES.get(timeframe, [timeframe])` fallback at `:230`
  unreachable — which is the only reason the frame-of-one VOID has not contaminated anything.
- **Why it can wait:** it is a live-path bug with no research consequence, and the unreachable
  fallback is currently protecting us.
- **What it blocks:** nothing.
- **My estimate:** trivial. Recorded so the fallback is not "fixed" without also fixing the frame-of-one
  VOID it is hiding.

## R4-REQ-5 route the 240m `regime_tf = 1440` finding to whoever owns the 4-hour rows

- **Arose in:** `MGR-T4`, `R4-M3` / `R4-V3` / `R4-R3`.
- **The ask:** tell me who should carry this, or carry it on the board. At the 240m row
  `_default_regime_tf` falls through to `self.timeframes[-1]` (`features.py:820-826`), so **every
  4-hour strategy's regime and volatility base filters are read off the daily series.** Consequences I
  measured and cannot follow up without sweeps: `volatility_normal` passes 93–95% at 240m on
  MGC/MNQ/MES vs 79% at 60m, with **23–27% of those passes being `RegimeSnapshot`'s `"NORMAL"` field
  default**; `regime_ranging` (MEAN_REVERSION's base filter) loses 11 points at 240m; and
  `regime_matches_direction` fires **188 of 188 LONG on MES at 240m**, so a SHORT-allowed MES 240m
  strategy carrying it has a VOID short arm.
- **Why it cannot wait:** `D21` is already open on the session-scale guard never reaching 4h, and R3's
  `MGR-T17` is re-reading stop geometry at 240m. If the 4-hour row's base filters are partly a
  dataclass default, that is context `MGR-T17` needs before it interprets a 240m comparison.
- **What it blocks:** possibly `MGR-T17`'s reading of its own 240m cells. Not my task's conclusion.
- **My estimate:** medium — the measurement is done; deciding what it does to published 240m rows is not.
