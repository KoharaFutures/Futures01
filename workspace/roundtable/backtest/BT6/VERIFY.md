# BT6 — fidelity questions to R6

One numbered question per algorithm. A backtester's reading of a finding is
lossy, so no number from an `UNVERIFIED` or `ASKED` algorithm is reportable as a
verified quantity.

---

## V1 — `BT6-ALGO-1` against `R6-D1`

- **Asked:** `msgs/BT6-01_R6_verify-ALGO-1.md`
- **Status:** **ASKED** (awaiting `msgs/R6-NN_BT6_re-verify-ALGO-1.md`)
- **Algorithm:** `backtest/BT6/ALGOS.md` → `BT6-ALGO-1`

### What I believe R6-D1 claims, in my own words

At 1440m the session-anchored VWAP band has no usable width, so the `vwap`
condition group stops measuring volume-weighted value and starts measuring bar
shape. Concretely: `above_vwap` becomes `2C > H+L`, `vwap_band_extension` becomes
its negation, `vwap_band1_bounce` cannot fire at all, and because `vwap` is the
VWAP template's *required* group, a daily VWAP strategy is a close-location
strategy wearing a VWAP name. This is `D45`'s mechanism at its limit — every
daily bar is the first bar of its trading day — and `D45`'s "6–34% of bars"
understates it.

### What I measured, and whether it agreed

**Ten of ten of R6-D1's published figures reproduce to the printed digit**, from
code written against the primitives rather than from R6's script. Detail in
`bursts/01_r6-d1-daily-vwap-collapse.md` §1. I found nothing to disagree with,
so this question is about my reading and my silent choices, not a divergence.

### The five places the finding was silent and I had to decide

Summarised here; the full table with the alternative each choice rejected is in
`ALGOS.md` → "Where I had to choose".

1. **A tick** = `get_contract(sym).tick_size`, not the file's minimum observed
   increment.
2. **The first bar is kept**, not dropped as warm-up; `None` bands are excluded
   from the denominator (there are none).
3. **"Daily" = `minutes == 1440` only.** 7200 is not counted as a second daily
   timeframe, so R6-D1 stays disentangled from `R4-M3`.
4. **Sub-tick, never `== 0.0`.** The half-width is exactly zero on only
   2300/2511 MGC and 1776/1859 MES daily bars.
5. **"How many results" is answered twice** — 196 distinct stored rows and 23,309
   evaluated strategies — because the two differ by ~50× and answer different
   questions.

### Four things I found that R6-D1 does not state

Offered as candidate strengthenings, not corrections. Each is the kind of thing
that could also mean I have read the finding too broadly, which is why they are
in the question rather than in a report.

1. At 1440m the three `vwap` SIGNALs collapse to **two** statements and one is
   the exact negation of the other (0/2319 direction agreement) — while
   `above_vwap`, `vwap_reclaim`, `candle_close_strength` and `delta_confirms_bar`
   are **one** predicate in three condition groups (100% agreement, every pair).
2. `above_vwap`'s 92.4% on MGC is **not selectivity**: MGC's daily CSV has 281
   rangeless bars (11.2%). On bars with `high > low` it fires 2228/2230 = **99.91%**.
3. **91 of those 281 rangeless bars still emit a direction**, on a
   `|close − vwap|` of up to **9.1e-13** — a direction assigned by the last bit
   of a float.
4. `vwap_band1_bounce` at 1440m is **`VOID`**, and 2,126 of 23,309 generated
   daily strategies carry it and take **0 trades** through `run_portfolio`.

### The one thing I would call a friendly correction

R1's "σ is **exactly** zero on the first bar, by construction" is algebraically
true and numerically false: `max(0, pv2/vol − mean²)` is a catastrophic
cancellation and `sd` lands near 1e-5, not 0. Sub-tick, never zero. It changes no
conclusion and it does change how a test may be written.
