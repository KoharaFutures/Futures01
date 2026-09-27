# BT6 burst 01 — R6-D1 reproduced, and the mechanism confirmed in the code

**Agent:** BT6 (paired to R6). **Burst question:** does R6-D1 — "at daily frequency the `vwap`
group is a bar-shape group" — reproduce independently, is `D45`'s zero-σ-on-the-first-bar the
mechanism, and how many stored or published results does it reach?

**Code:** `backtest/BT6/code/vwap_daily_census.py` (written from the primitives, not from R6's
script; I did not read R6's script and it is not in the tree). Output:
`backtest/BT6/out/vwap_daily_census.json`.

**Store:** `csv/raw` is primary — it is what every published `scan_reports/` row was measured on.
`data/archive/` daily is carried as an independent-store replication. `csv/` untouched, read-only.
No backtest, no expectancy, no sweep: every number below is a firing rate, a band width or a count.

---

## 1. R6-D1 reproduces exactly — every published figure, to the digit

`[measured: PYTHONPATH=. python3 workspace/roundtable/backtest/BT6/code/vwap_daily_census.py]`

### Band-1 half-width `< 1 tick`, against `get_contract(sym).tick_size`

| cell | store | measured | `< 1 tick` | R6-D1 said | agrees |
|---|---|---|---|---|---|
| MGC 60m | csv/raw | 5000 | 376 = **7.5%** | 7.5% | yes |
| MES 60m | csv/raw | 5000 | 422 = **8.4%** | 8.4% | yes |
| MNQ 60m | csv/raw | 5000 | 377 = **7.5%** | 7.5% | yes |
| MCL 60m | csv/raw | 5000 | 445 = **8.9%** | 8.9% | yes |
| MGC 240m | csv/raw resampled | 1348 | 269 = **20.0%** | 20.0% | yes |
| MES 240m | csv/raw resampled | 1347 | 276 = **20.5%** | 20.5% | yes |
| MNQ 240m | csv/raw resampled | 1347 | 267 = **19.8%** | 19.8% | yes |
| MCL 240m | csv/raw resampled | 1384 | 302 = **21.8%** | 21.8% | yes |
| **MGC 1440m** | csv/raw | 2511 | **2511 = 100.0%** | 2511/2511 | yes |
| **MES 1440m** | csv/raw | 1859 | **1859 = 100.0%** | 1859/1859 | yes |
| **MNQ 1440m** | csv/raw | 1859 | **1859 = 100.0%** | *not measured by R6* | **extends it** |
| MGC 1440m | data/archive | 4008 | **4008 = 100.0%** | — | replicates |
| MES 1440m | data/archive | 1863 | **1863 = 100.0%** | — | replicates |
| MNQ 1440m | data/archive | 1863 | **1863 = 100.0%** | — | replicates |

Band `None` count is **0 in every cell** — `vwap_bands` emits a band on the first bar rather than
withholding it, which is the absence of the warm-up guard, measured.

### Condition census on the published daily frame `[1440, 7200]`

| condition | MGC 1440m | R6 | MES 1440m | R6 | MNQ 1440m (new) |
|---|---|---|---|---|---|
| `above_vwap` | 2319 = **92.4%** | 92.4% | 1854 = **99.7%** | 99.7% | 1858 = **99.9%** |
| `vwap_band_extension` | 2506 = **99.8%** | 99.8% | 1859 = **100.0%** | 100.0% | 1859 = **100.0%** |
| `vwap_band1_bounce` | **0 = 0.0%** | 0 | **0 = 0.0%** | 0 | **0 = 0.0%** |
| `vwap_reclaim` | 1691 = **67.3%** | 67.3% | 1459 = **78.5%** | 78.5% | 1438 = 77.4% |
| `vwap_proximity` | 2418 = **96.3%** | 96.3% | 1790 = **96.3%** | 96.3% | 1788 = 96.2% |
| `above_vwap` dir == `candle_close_strength` dir | **1092 / 1092** | 1092/1092 | **919 / 919** | 919/919 | **939 / 939** |

**Ten of ten of R6's published R6-D1 figures reproduce to the printed digit, from independent code.**
I found no figure to disagree with. Per `BRIEF.md`'s independence rule and R6's own method note, I
replicated first and only then looked for more; the four items in §3 are what that turned up.

---

## 2. The mechanism is `D45`, confirmed, and the confirmation is exact

R1's claim (`msgs/04_R1_R3_re-VWAP-BAND.md:108-115`): on the first bar after an anchor reset
`pv2/vol − mean² = tp² − tp² = 0`, so `sd = 0` and `upper_1 = lower_1 = vwap = tp`, with no warm-up
guard `[repo-verified: futures_agents/indicators/volume.py:88-102]`.

I cross-tabulated `half-width < 1 tick` against `the anchor key changed at this bar`, computing the
anchor key the way the indicator does (`trading_day(bar.ts)`, `volume.py:34-35`) rather than off a
clock:

| cell | trading days | first-of-day bars | first & sub-tick | first & **not** sub-tick | later & sub-tick |
|---|---|---|---|---|---|
| MGC 60m | 226 | 226 | 226 | **0** | 150 |
| MES 60m | 227 | 227 | 227 | **0** | 195 |
| MNQ 60m | 227 | 227 | 227 | **0** | 150 |
| MCL 60m | 241 | 241 | 241 | **0** | 204 |
| MGC 240m | 267 | 267 | 267 | **0** | 2 |
| MES 240m | 267 | 267 | 267 | **0** | 9 |
| MNQ 240m | 267 | 267 | 267 | **0** | 0 |
| MCL 240m | 280 | 280 | 280 | **0** | 22 |
| **MGC 1440m** | **2511** | **2511** | **2511** | **0** | **0** |
| **MES 1440m** | **1859** | **1859** | **1859** | **0** | **0** |
| **MNQ 1440m** | **1859** | **1859** | **1859** | **0** | **0** |

Two things fall out, and they answer the question:

1. **`first & not sub-tick` is 0 in every cell, on every symbol, at every timeframe.** Every
   first-bar-of-a-trading-day has a sub-tick band-1. `D45`'s stated mechanism is the mechanism.
2. **At 1440m `distinct_trading_days == bars` and `not_first_of_day == 0`.** Every daily bar *is*
   the first bar of its trading day, so the 100% rate is not an empirical rate at all — it is the
   1-bar case of `D45` holding on 100% of bars by construction. **Confirmed, not refuted.**

**One refinement `D45` does not carry.** Sub-tick bands are *not* only first-of-day bars at 60m:
150 of MGC's 376 (40%), 195 of MES's 422 (46%), 204 of MCL's 445 (46%) are later bars, which is
R1's own σ ramp (`0.00 0.00 0.18 0.29 …` σ/ATR by bars since anchor) crossing the tick threshold on
bar 1 and sometimes bar 2. At 240m the ramp has already cleared a tick by bar 1 (2/269 on MGC,
0/267 on MNQ). So the right statement is **"zero on bar 0, sub-tick for the first one-to-two bars,
and at 1440m there is no bar 1"** — the 100% is a limit, and the limit is reached because the
series has no later bars, not because the ramp got worse.

### The one place I part company with R1's wording, and it matters for the test

R1 says σ is "**exactly** zero on the first bar … by construction". Algebraically yes. In floating
point, **no**: `var = max(0.0, pv2/vol − mean²)` is a catastrophic cancellation of two quantities
near 1.8e6 on MGC, so its absolute error is ~2e-10 and `sd = sqrt(var)` lands near **1e-5 price
units**, not 0.

`[measured: same run → half-width exactly == 0.0 on 2300/2511 MGC, 1776/1859 MES, 1765/1859 MNQ
daily bars; sub-tick on 2511/2511, 1859/1859, 1859/1859]`

So **8.4% of MGC daily bars and 4.5% of MES's have a band that is non-zero and sub-tick.** Nothing
about the finding changes — `1e-5` on a `0.1` tick is a band no price can be on either side of —
but an assertion written as `sd == 0.0` would fail on one daily bar in twelve, and the regression
test in `tests/test_bt6_vwap_daily.py` is written against the tick, not against zero, because of
this.

---

## 3. Four things the replication turned up that R6-D1 does not state

### 3.1 At 1440m the three `vwap` SIGNALs collapse to two statements, one the negation of the other

`[measured: pairwise direction agreement over co-firings, frame [1440,7200]]`

| pair | MGC 1440m | MES 1440m |
|---|---|---|
| `above_vwap` × `vwap_reclaim` | 1689/1689 = **100%** | 1455/1455 = **100%** |
| `above_vwap` × `candle_close_strength` | 1092/1092 = **100%** | 919/919 = **100%** |
| `above_vwap` × `delta_confirms_bar` | 1829/1829 = **100%** | 1602/1602 = **100%** |
| `vwap_reclaim` × `delta_confirms_bar` | 1678/1678 = **100%** | 1450/1450 = **100%** |
| `candle_close_strength` × `delta_confirms_bar` | 1014/1014 = **100%** | 898/898 = **100%** |
| **`above_vwap` × `vwap_band_extension`** | **0/2319 = 0%** | **0/1854 = 0%** |
| **`vwap_band_extension` × `delta_confirms_bar`** | **0/1829 = 0%** | **0/1602 = 0%** |

So at daily frequency `above_vwap`, `vwap_reclaim`, `candle_close_strength` and `delta_confirms_bar`
are **one directional predicate spread across three condition groups** (`vwap`, `candlestick`,
`orderflow`), and `vwap_band_extension` is its **exact negation** — because `close >= vwap_u2` is
tested before `close <= vwap_l2` and on a zero-width band both hold. This is R6-D1's claim about
`candle_close_strength` extended to the whole group, and it is R1 finding C-1 at 1440m.

**Consequence for the generator, and it is the conservative direction.** `GLOBAL_EXCLUSIVE`
(`combinator.py:391-402`) holds three pairs and **none of these**, so a daily VWAP strategy drawing
`above_vwap` (required `vwap`) plus `delta_confirms_bar` (optional `orderflow`) is a two-signal
confluence counting one observation twice — the exact failure the diversity rule exists to prevent,
recorded in that list's own docstring. But the *opposite-sign* pair cannot be generated:
`itertools.combinations(range(len(optional)), n_opt)` draws at most one condition per group
`[repo-verified: futures_agents/strategies/combinator.py:538-541]`, and no template carries `vwap`
in both `required_groups` and `optional_groups` `[measured: python3 over combinator.TEMPLATES → 1
required (VWAP), 9 optional, 0 both]`. So `above_vwap` + `vwap_band_extension` is **unreachable by
the generator** and no published null can be that artefact. Reachable by hand only.

### 3.2 `above_vwap`'s 92.4% on MGC is not selectivity — it is MGC's flat daily bars

`csv/raw/MGC_1d.csv` carries **281 bars with `high == low`** (11.2% of 2511) against **1 of 1859**
on MES and MNQ `[measured: csv.DictReader over the three files]`. A flat bar has
`typical == close`, so the bar has no shape for the predicate to read.

| MGC 1440m | `above_vwap` LONG | SHORT | no fire |
|---|---|---|---|
| bars with `high > low` (2230) | 1127 | 1101 | **2** |
| bars with `high == low` (281) | **41** | **50** | 190 |

**On MGC daily bars that have any range at all, `above_vwap` fires on 2228 / 2230 = 99.91%** — and
on MES, 1854/1858 = 99.78%. That is R6-D1 made *stronger*: the condition's own docstring records
the pre-fix version as firing on "99.99% of bars" and calls that the defect the band was introduced
to fix `[repo-verified: futures_agents/strategies/library.py:296-305]`. At 1440m the fixed version
is back to 99.9%. R6's "the fix is void at 1440m" is right, and 92.4% understates it because the
shortfall is a data property of MGC's daily file, not selectivity.

**And 91 of those 281 flat bars still emit a direction.** The largest `|close − vwap|` among them is
**9.1e-13 price units** — nine femto-ticks. `typical = (h+l+c)/3` does not round-trip to `c` in
binary floating point even when `h == l == c`, so on a bar with no range at all `above_vwap` returns
LONG 41 times and SHORT 50 times **on the last bit of a float**. That is not a degenerate signal,
it is noise wearing a direction, and it is not in R6-D1.

### 3.3 `vwap_band1_bounce` is `VOID` at 1440m by arithmetic, and I checked the arithmetic

`vwap_band1_bounce` needs `b.low <= vwap_l1 < b.close and b.close < vwap`
`[repo-verified: futures_agents/strategies/library.py:355-366]`. With `vwap_l1 == vwap` that is
`vwap < close AND close < vwap` — empty for any real `close`, at any tick size, on any symbol. The
0/2511, 0/1859, 0/1859 and 0/4008, 0/1863, 0/1863 are `VOID` in `BRIEF.md`'s sense, not `DEGRADED`
and not "rare". It cannot fire, and the float-noise σ does not rescue it: the band would have to be
wider than the close-to-vwap distance *and* the bar would have to trade through it.

### 3.4 A data defect in `data/archive/MGC_1440m.jsonl` — not mine to fix, reported

Using the archive daily as a replication store surfaced this, so it is recorded rather than dropped.
`[measured: python3 over data/archive/MGC_1440m.jsonl]`

- **A 10× scale break at index 384.** `2012-04-25 c=164.10` → `2012-04-27 c=1664.80`. The first
  **384 of 4008** bars (2010-10-04 → 2012-04-25) sit in a 131.70–188.90 range; the remaining 3624
  sit in 1050.80–5318.40. A momentum rule reads the 2012-04-27 bar as a **+914%** return.
- **551 of 4008 bars have `high == low`** and **355 have `volume == 0`**.

This is `D40`'s shape (a spliced series read as one) on the store `DISC2`'s 25-year span proposal
depends on, and `BRIEF.md`'s data policy verified archive-vs-`csv/raw` agreement **at 60m only**.
It does not touch R6-D1 — the daily collapse reproduces identically on both stores and on either
side of the break — but anyone computing a *return* from archive MGC daily must handle it. Filed as
`BT6-REQ-2`.

---

## 4. Where I stopped

Blast radius (§4 of this burst's dispatch) and the regression test are below/next in this file's
companion sections; the fidelity question to R6 is `msgs/BT6-01_R6_verify-ALGO-1.md`.
`futures_agents/` **unpatched** this burst, per dispatch: a warm-up guard on `vwap_bands` changes
every frame at every timeframe. Proposed as `BT6-REQ-1` with the radius measured.
