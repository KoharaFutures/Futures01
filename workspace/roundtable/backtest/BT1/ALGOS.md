# BT1 — algorithms built from R1's findings

One entry per algorithm, in the PIPELINE §4 shape. Fidelity is the only field
that gates reporting: **no number from a non-FAITHFUL algorithm is reportable**,
and "measurable at all" is not a number about the algorithm, it is a fact about
the data (see ALGO-1's frequency census).

---

## ALGO-1 absorption shape — high volume, LOW range

- **Implements:** R1 §7 Q2 item 1 (`research/R1_flow_auction.md:1743`) and the
  "closest expressible relative" paragraph of R1-D1 **I-2 Absorption and
  stopping volume** (`:639-677`), with the operating detail at R1-D2 **B.1.3 /
  B.2** (`:1430-1437`).
- **Code:** `backtest/BT1/code/absorption.py:1-315`
  - shape column, causal: `absorption.py:157-195` (`absorption_series`)
  - the gate: `absorption.py:133-136` (`Absorption.fires`)
  - direction: `absorption.py:138-150` (`Absorption.direction`)
  - registration, i.e. the D38 guard: `absorption.py:197-215`, `239-257`
  - conditions: `absorption.py:270-291` (`absorption_bar`, SIGNAL),
    `294-310` (`absorption_present`, FILTER)
  - tests: `backtest/BT1/code/test_absorption.py:1-241` — 33 checks, all pass
    `[measured: python3 code/test_absorption.py → ALL CHECKS PASSED]`
  - frequency census: `backtest/BT1/code/frequency.py:1-146`
- **My reading of the finding:** three claims, which I take as one algorithm.
  1. `detect_imbalances` fires on **high range AND high volume** — `r_mult >=
     2.0`, `v_mult >= 1.2` off a 20-bar trailing mean
     `[repo-verified: futures_agents/indicators/structure.py:452-462]`. That is
     a displacement bar.
  2. **Absorption is the inverse shape**: volume ≥ 2× its norm with range ≤ its
     norm — aggression arriving and buying no displacement. **Nothing in the
     library computes it**, and both inputs are in the CSV header.
  3. The library's delta column is not a substitute, because `estimated_delta`
     returns exactly `0.0` when range ≤ 0
     `[repo-verified: futures_agents/data/bars.py:110-111]` — the proxy is at
     its minimum in the family's limiting case.

  So ALGO-1 is the **direct volume/range form of the shape**, on one bar, with
  no delta term anywhere in it. It is not the operating form of I-2: R1's B.1.6
  makes the entry the *following* bar's failure to extend, which is a sequence
  (P9 / D37) and is not in the ~15 lines R1 costed.

- **Where I had to choose:** eleven places. The first four are the ones that
  decide whether this is still R1's object; C5–C11 are corners.

  - **C1 — what counts as "the norm": a 20-bar trailing mean, excluding the
    current bar.** `window = 20`, `prior = bars[i-window:i]`, arithmetic mean of
    `b.volume` and of `b.range`. Chosen to be *exactly* `detect_imbalances`'
    own normalisation (`structure.py:451-457`), including re-summing the slice
    per bar instead of a rolling sum, so `r_mult` here is bit-identical to
    `r_mult` there and the two shapes are measured on the same axes. **The
    alternative I rejected:** `relative_volume`, the library's *other* volume
    norm, which compares a bar to the same clock minute on the previous 20
    sessions `[repo-verified: futures_agents/indicators/volume.py:266-285]`.
    That is arguably the better norm for intraday futures — volume has a strong
    intraday U-shape, so a 2× rolling-mean surge at 03:00 and one at 09:35 are
    different animals — and it fires 5–27× more often (census below). I chose
    the `detect_imbalances` mirror because R1's claim is explicitly "the inverse
    of `detect_imbalances`". **R1 has to rule on this one.**
  - **C2 — thresholds taken literally: `v_mult >= 2.0`, `r_mult <= 1.0`,
    inclusive on both sides.** Verbatim from "volume ≥2× norm with range ≤
    norm" (`:1743`) and consistent with I-2's "2–4× the recent norm … range at
    or below the norm" (`:656-657`). **Not searched, not tuned.** Note the
    asymmetry this creates against `detect_imbalances`, which uses 2.0 on range
    and 1.2 on volume: ALGO-1 is not that function's exact mirror image, it is
    R1's sentence.
  - **C3 — direction comes from where the close sits in the bar.** `close_pos
    > 0.5` → LONG (selling was absorbed), `< 0.5` → SHORT. This is the only
    half of R1's B.2 long entry that OHLCV can see; its other half, "strongly
    negative delta", needs P1. **What this costs, stated plainly:** `close >
    midpoint` is also the first clause of `delta_confirms_bar`
    `[repo-verified: futures_agents/strategies/library.py:455-467]`, a
    condition R1 classes as PROXY and which has been screened ~2.97M times. So
    **the novel content of ALGO-1 is entirely the volume-high/range-low gate,
    and the direction half is a bar-shape predicate the repo already screens.**
    That is why `absorption_present` (FILTER, direction-free) exists beside
    `absorption_bar` (SIGNAL): it keeps the new part separable from the old
    part. Which of the two is the algorithm is R1's call, not mine.
  - **C4 — acts on the absorption bar itself.** The condition fires at the
    close of bar *i*; the engine then fills at bar *i+1*'s open
    `[repo-verified: futures_agents/backtest/engine.py:8,290-296,346-355]`.
    **No failure-to-extend confirmation**, which means ALGO-1 is R1's *shape*
    and not R1's *setup*. I can compute a two-bar sequence inside one
    precomputed column (registration sidesteps D37, which only binds
    `min_signals` across conditions on one bar) — but that is a second
    algorithm and I have not written it.
  - **C5 — zero-range bars fire the gate and carry no direction.** `r_mult = 0
    ≤ 1.0`, so the shape gate passes; `close_pos` is undefined, so
    `absorption_bar` returns `no()` and `absorption_present` fires. This is
    absorption's limiting case and the exact point where R1 says the delta
    proxy collapses, so the asymmetry is deliberate: the direction-free form
    sees it, the directional form cannot.
  - **C6 — close exactly at the bar's midpoint → no signal**, not a coin flip.
  - **C7 — warm-up is `None`, and the three ways of being unknowable are not
    distinguished:** fewer than 20 prior bars; prior mean range ≤ 0; prior mean
    volume ≤ 0. The last two are `detect_imbalances`' own guard
    (`structure.py:456-457`). Column length always equals input length.
  - **C8 — range is `high - low` (`Bar.range`)**, not a gap-inclusive true
    range. Same quantity `detect_imbalances` uses.
  - **C9 — one timeframe, the strategy's own.** No MTF term (BRIEF rule 2:
    multi-timeframe agreement measured *worse*).
  - **C10 — no context gate.** R1's B.1.1 is "context first, always": no level,
    no trade. I left the level out because Q2 item 1 is the bare shape and a
    level is a separate condition in a rule set. This makes ALGO-1 strictly
    weaker than the operated family, deliberately.
  - **C11 — `warmup_bars = 25`** on both conditions (20 + 5). `ratio = v_mult /
    r_mult` is carried on the column but **is not the gate**; R1 describes the
    defining measurement as "a ratio of two things" (`:653`), so it is there for
    a later ruling without new code.

- **Frequency census — the reason this entry cannot proceed to measurement yet**
  `[measured: python3 code/frequency.py]`. Two independent contracts only (MGC,
  MCL — the index complex is not corroboration):

  | cell | bars | ALGO-1 fires | rate | `detect_imbalances` on the same bars | tod-volume variant |
  |---|---|---|---|---|---|
  | MGC 1h | 5000 | **11** | 0.22% | 288 | 59 |
  | MGC 15m | 3755 | **2** | 0.05% | 212 | 56 |
  | MGC 5m | 5000 | **9** | 0.18% | 216 | 111 |
  | MCL 1h | 5000 | **41** | 0.82% | 336 | 164 |
  | MCL 15m | 3753 | **5** | 0.13% | 220 | 81 |
  | MCL 5m | 5000 | **11** | 0.22% | 277 | 222 |

  **Taken literally, R1's thresholds put 4 of 6 cells below `toolkit.FLOOR = 20`
  before an exit model has touched them, and the best cell is 41 signals.** The
  cause is not a coding choice, it is the data: volume and range are **Pearson
  0.537–0.885** correlated at bar level, and conditional on `v_mult >= 2` the
  median `r_mult` is **1.77–2.00**, with only **0.51–5.85%** of high-volume bars
  having range ≤ norm `[measured: python3 code/frequency.py → coupling table]`.
  A bar that takes double its normal volume almost always moves.

  I have deliberately **not** relaxed a threshold to manufacture sample. That is
  the winner-hunt this pipeline exists to avoid, and the honest reading of the
  census is a candidate finding in its own right: *as a single-bar OHLCV object,
  the absorption shape is close to absent at 5m–1h on these contracts.*

- **Search size so far: 1.** One parameterisation, R1's own numbers, zero
  variants measured. The variant *counts* in the census are a frequency census
  of the signal layer with no exit model, no fill, no cost and no P&L — if any
  of them is ever run as a strategy, the search size stated at that point will
  include it.

- **Placebo plan (not yet run, listed so it is pre-registered):**
  `placebo_random` count-matched on the same bars and `placebo_shuffle` on
  timestamps, both through ALGO-1's own exits, filters and sizing.
  **`placebo_shift` is not a clean control** — it retains part of the real
  signal and is conservative only `[repo-verified: workspace/studies/DEFECTS.md
  D42:620-633]`. With ≤41 signals in the best cell, a count-matched placebo is
  the only control that can say anything, and it will not say much.

- **Fidelity: ASKED** — `msgs/02_BT1_R1_verify-ALGO-1.md`, four questions
  (Q1 the volume norm, Q2 the direction rule, Q3 the near-empty census, Q4 the
  scope of the `estimated_delta` claim). Nothing measured until R1 answers.
