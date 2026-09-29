# BT6 — algorithms

Paired to **R6**. Ids per `REGISTRY.md`: `BT6-ALGO-<n>`.

**Standing rule for this file:** never report a number from an `UNVERIFIED`
algorithm. An unverified result is not a weak result, it is an unknown quantity.

---

## BT6-ALGO-1 — the daily VWAP collapse, measured

- **Implements:** `R6-D1` from `research/R6_report_audit.md:120-156`, with `D45`
  (`msgs/04_R1_R3_re-VWAP-BAND.md:108-145`) as the claimed mechanism.
- **Code:** `backtest/BT6/code/vwap_daily_census.py` (census),
  `backtest/BT6/code/vwap_blast_radius.py` (radius),
  `tests/test_bt6_vwap_daily.py` (regression pins, 14 pass + 3 xfail).
- **Output:** `backtest/BT6/out/vwap_daily_census.json`,
  `backtest/BT6/out/vwap_blast_radius.json`.
- **Burst:** `backtest/BT6/bursts/01_r6-d1-daily-vwap-collapse.md`.

### My reading of the finding

R6-D1 says three things, and they are separable:

1. **A width claim.** The session-anchored VWAP band-1 half-width is smaller
   than one tick on **every** 1440m bar, against 7.5–8.9% of 60m bars and
   19.8–21.8% of 240m bars. So the band is not a band at daily frequency.
2. **A consequence claim.** With `vwap_u1 == vwap_l1 == vwap ≈ (H+L+C)/3`,
   `above_vwap` becomes `2C > H+L` — bar shape, not value — and fires on
   92.4% / 99.7% of daily bars; `vwap_band_extension` on 99.8% / 100.0%; and
   `vwap_band1_bounce` on **0**. `above_vwap`'s direction equals
   `candle_close_strength`'s on every co-firing.
3. **A reach claim.** `vwap` is VWAP's *required* group, so a daily VWAP
   strategy is a bar-shape strategy wearing a VWAP name, and this is `D45`'s
   mechanism at its limit — `D45`'s "6–34% of bars" understates it.

### Where I had to choose

The finding is silent on all of these and each could have changed a number.

| choice | what I did | why, and what the alternative would have done |
|---|---|---|
| **what counts as a tick** | `config.get_contract(sym).tick_size` — MGC 0.10, MES/MNQ 0.25, MCL 0.01 | the alternative (the minimum observed price increment in the file) is a *data* property, not a contract one, and on MGC's float32-ish daily closes it is ~1e-6, which would have reported 0% sub-tick everywhere. Using the contract's tick is also what `D45` uses, through `min_stop_ticks * tick_size` |
| **which half-width** | `upper_1 − vwap`, with the symmetry against `vwap − lower_1` asserted per bar (max asymmetry 0.0 in every cell) | if they differed, "the half-width" would be ambiguous and the 100% could be an artefact of picking the smaller side |
| **strict or inclusive `< 1 tick`** | strict `<`, matching R6. Also report `<= 1 tick`, `< 0.5 tick` and `== 0.0` so the reader can move the threshold | at 1440m every threshold gives 100%, so nothing turns on it there; at 60m it would move the rate by a fraction of a point |
| **warm-up** | **none dropped.** Bar 0 of the file is included. Bars whose band is `None` are excluded from the denominator and counted separately (0 in every cell) | dropping bar 0 would remove one collapsed bar per cell and is exactly the guard whose absence is the defect. Excluding `None`s is what makes "2511/2511" a meaningful denominator rather than a coincidence |
| **which timeframes are "daily"** | `minutes == 1440` only: `csv/raw/*_1d.csv` and `data/archive/*_1440m.jsonl`. **7200 is not counted as a second daily timeframe** even though `align_bucket` makes it one (`R4-M3`) | counting 7200 would double every daily count and tangle R6-D1 with `R4-M3`, which is BT4's finding, not this one |
| **the first bar** | "first bar of its anchor group" is computed the way `vwap_bands` computes it — `trading_day(bar.ts)` changed — **not** off a wall clock | a clock rule would mis-classify the 18:00 ET Globex reopen and every holiday session, and the whole mechanism is about the anchor key |
| **store** | `csv/raw` primary (it is what every published row was measured on); `data/archive` daily as an independent-store replication | `BRIEF.md`'s data policy verified the two stores agree **at 60m**; I did not assume it at 1440m, I measured both. They agree on the finding |
| **`MCL_1440m`** | excluded. One row is not data | including it would have produced a meaningless 1/1 = 100% |
| **exactly-zero vs sub-tick** | reported separately, and the regression test asserts **sub-tick**, never `== 0.0` | `var = max(0, pv2/vol − mean²)` is a catastrophic cancellation; the half-width is exactly 0.0 on only 2300/2511 MGC and 1776/1859 MES daily bars. An `sd == 0.0` assertion fails on one daily bar in twelve |
| **"how many results" — rows or evaluations** | both, separately: 505 stored *rows* at tf=1440 (196 distinct strategy ids), and 23,309 *evaluated* strategies in the three daily chronology ledgers | rows alone understate the radius ~50×, because a row must clear a trade floor; evaluations alone overstate what any reader has seen. The two answer different questions |
| **the `possible` class** | not inferred. The stores record `group`, not condition names, so I re-generated the populations with the harnesses' own parameters (`seed=1`, `max_per_template=2400`) and matched the stored `strategies` count exactly (7875 / 7697 / 7737) before counting carriers | guessing a rate from the group mix would have been a number with no provenance |

### Fidelity

**ASKED** — `msgs/BT6-01_R6_verify-ALGO-1.md`.

Ten of ten of R6-D1's published figures reproduce to the printed digit
(burst 01 §1). I found nothing to disagree with, so the fidelity question is
about my *reading* and my silent choices, not about a divergence.

### Search size and controls, stated because every number must carry them

- **Search size: 1.** This is a single pre-registered reproduction of a finding
  fixed in writing before I measured. No variant was tried and nothing was
  selected on outcome. `toolkit.free_t` for one hypothesis is **1.177**.
- **No placebo is owed and none is reported.** Not one number here is an
  expectancy, a *t*, a *z* or a P&L. Every number is a band width, a firing
  count, a condition-direction agreement, a template-membership count or a
  trade count that is **zero**. There is no effect size for a control to
  bracket. The one backtest run (`run_portfolio` over 2,126 strategies) is used
  only to confirm a **zero**, and it carries its own control in the same run:
  the `above_vwap` arm on the same bars took 11,014 trades, so the zero is the
  condition and not a broken harness.
- **No `T.ab`** (`D28`). No comparative claim is made at all.
- **`_id=None`** on every `Strategy` construction and every `replace` (`D48`).
- **`csv/` untouched**, read-only. `data/archive/` read-only.
