# BT4 burst 01 — quantifying R4-M3, the `align_bucket` collapse

**Task:** make R4-M3 executable and measure its consequence. Not a search for a winner; nothing in
this burst runs `run_portfolio` or produces an expectancy number.

**Stopped at:** ALGO-1 coded, measured, placebo/control beside it, regression test in the repo
suite, one fidelity question asked. No fix applied to `futures_agents/`.

## What I did

1. Re-verified the mechanism independently of R4's numbers (`code/daily_mtf_reduction.py`).
2. **Reduced** the three `multitimeframe` conditions at 1440m to a two-label decision table over one
   series and one integer lag, and proved the reduction exact bar for bar, on three symbols.
3. Ran a control at 240m, where the confirming series is genuine, to show the reduction method is
   not vacuous.
4. Counted the stored results that ran on a 1440m frame, per store, in each store's native unit
   (`code/stores_at_1440.py`).
5. Re-aggregated rule 2's own published per-cell statistics with the 1440m cells removed
   (`code/rule2_leave_1440_out.py`). No new comparative test; no `T.ab`. **This turned out to
   discharge `ADJ-14` §5, a pre-registration written before I measured** — it asks BT4 for exactly
   these two numbers and states the decision rule in advance. **z survives: narrowing (a) costs
   nothing.**
6. Found and measured a second channel nobody had counted: `regime_tf = 7200` at the daily frame,
   which reaches **every** 1440m strategy, not only the MULTI_TIMEFRAME ones
   (`code/regime_lag_at_1440.py`).
7. Wrote `tests/test_bt4_align_bucket.py` — **16 checks that pin the current behaviour + 4
   `xfail(strict=False)`** that pin the invariant a fix must satisfy, so the suite goes green today
   and the four flip to `XPASS` the moment `align_bucket` is corrected.
   **Full suite: `python -m pytest -q tests` → `1006 passed, 4 xfailed in 590.75s`, exit 0.** Nothing
   else in the suite moved.

## Where I chose, and it matters for reading every number below

- **"A daily MTF result" = a stored row whose primary timeframe is 1440.** Not "a row whose frame
  contains 1440": a 60m row runs `[60, 240, 1440]` and its 1440 member is a *genuine* daily series,
  because the collapse only bites on a request strictly above 1440. Counting 60m rows would have
  inflated the blast radius by an order of magnitude.
- **240m rows are not counted as affected.** `[240, 1440]` is a two-voter frame, so it is degenerate
  under `D17` / `R4-MT2`, but its confirming series is real. That is a different defect and merging
  the two would over-retract.
- **The 2–4 bar lag is treated as content, not as noise.** The two series are bit-identical, so the
  only thing the confirming channel can say is a *lagged* restatement of the primary. I did not
  quotient the lag out; I made it the reduction's only free parameter and then showed the reduction
  is exact with it.
- **Rule 2's z is re-aggregated, never re-tested.** I reproduce the published `-4.093` from the
  payload's own per-cell `z` values (Stouffer, equal weights) and only then drop cells. Recomputing
  the same combination on a subset is arithmetic; running a new rank sum would have been a new claim
  and would have hit `D28`.

## Results, in one place

| | |
|---|---|
| `align_bucket` distinct bucketings over `minutes ∈ {1440, 2880, 4320, 7200, 10080, 43200, 525600}` | **1** — all seven collapse |
| `resample(daily, 7200)` OHLCV vs daily, in order | **2510/2510** MGC, 1858/1858 MNQ, 1858/1858 MES |
| …and its `ts` | **0/2510** — rewritten to the CME trading-day start, which is what makes `end_ts` five days out |
| bars per "7200m" bucket | `{1: 2511}` MGC, `{1: 1859}` MNQ/MES |
| confirm pointer rebuilt from the daily series + the clock alone | **2511/2511, 1859/1859, 1859/1859** |
| **all three conditions reproduced by one series + one lag** | **2511/2511, 1859/1859, 1859/1859** |
| control, 240m, best fit over 25 candidate lags | **3441/5000 (68.8%)** signals, 4107/5000 (82.1%) filter — reduction fails |
| `mtf_aligned` ≡ `mtf_strongly_aligned` at 1440m | 2511/2511, 1859/1859, 1859/1859 |
| `mtf_not_conflicted` pass rate | 99.12 / 99.30 / 99.62% |
| rule 2 Stouffer, published | **−4.093** over 14 cells (reproduced exactly) |
| rule 2 Stouffer, 1440m cells removed | **−3.053** over 11 cells (8 at 60m, 2 at 15m, 1 at 30m; 5 symbols) |
| share of rule 2's treatment arm that is 1440m | **249/366 = 68.0%** (control arm 320/1151 = 27.8%) |
| sign test across cells, before → after | p = 0.424 → 0.549 — **not significant either way** |
| regime label at 1440m vs on-timeframe | differs on 20.3 / 18.1 / 17.5% of bars |
| `volatility_normal` decision flips | 10.23 / 10.38 / 9.58% of bars |

Full tables are in `../ALGOS.md`; raw payload in `code/daily_mtf_reduction.json`.

## What I did not do

- Did **not** touch `futures_agents/data/bars.py`. The fix is proposed in `REQUESTS.md` as
  `BT4-REQ-1` with the blast radius measured, because changing a bucketing function changes every
  frame in the repository and that is a board decision.
- Did **not** construct a genuine weekly series to measure what the *correct* answer would have
  been. That is the natural next burst and it is the only way to sign the error rather than bound
  it. Recorded as the open gap in `ALGOS.md`.
- Did **not** re-run any 1440m cell. Nothing here needs a backtest; every claim is a property of the
  bucketing arithmetic and of artefacts already on disk.
- **No `dataclasses.replace` on a `Strategy` anywhere in this burst** — no `Strategy` is constructed
  at all, so `D48` has no surface here. Stated rather than left silent, per the standing rule.

## Where I stopped

ALGO-1 is **ASKED**, not FAITHFUL. `VERIFY.md` holds five numbered questions and
`msgs/BT4-01_R4_verify-ALGO-1.md` is out to R4. No number from this burst should be quoted as
verified until that comes back.
