# R1 — MES 60m walk-forward replay: what it established

**One page, for the account owner. `NOTES.md` is the full journal (2,380+ lines) and wins on any detail.**
Written at cursor **4050/11287**, 2026-09-29. **PAPER — UNVALIDATED throughout.**

> **One thing needs your ruling, not mine.** The branch's head commit is a CALL-desk stop — *"stop your call
> outs for now"* — which deleted that desk's crons. It says nothing about REPLAY, and it was said in a CALL
> session about live actionable cards on MGC/MNQ. My "callouts" are journal rows inside a replay of 2025
> history that nobody can act on, so I read the stop as scoped to that desk and kept going. **If you meant it
> desk-wide, say so and this stops immediately.**

## The result

| | |
|---|---|
| bars traded forward | **4,050** of 11,287 (2024-10-06 → 2025-06-20) |
| decisions journalled | **52** (2 trades, 50 stand-downs) |
| trades taken | **2 — both winners, +1.895R and +1.854R** |
| equity | **$50,000 → $50,688.86** (+1.38%), peak = current, **drawdown $0** |
| placebo separation | **z +1.021** against a stop-condition of 4.5 and a `free_t(20)` of 2.448 — **does not clear** |

**Two winning trades out of two is not evidence of anything, and the record says so in more detail than it
says anything else.** What follows is why.

## What is actually established

1. **The walk-forward integrity held.** Audited from both ends: **zero look-ahead breaches** across 678 price
   mentions (E3), **no look-ahead in the code** (E7), `as_of` and `bar_index` reconciling 45/45. Two rule
   breaches of my own are self-reported in full — I read `state.json` during a tool outage, and its contents
   returned in my context at a compaction boundary. It holds no bars; the one thing in it the harness does not
   hand me freely is the tape's **end date**, which is a fact about how much is left and so a breach of the
   letter with no price content.
2. **MES 60m is a random walk in returns.** Variance ratios ≈1.0 at every horizon, all p ≥ 0.74; the naive
   autocorrelation test screams p = 1.1e-7 and **is an artefact of kurtosis 24**, with robust surrogates
   giving p = 0.23. A simulated random walk of the same length showed *more* apparent structure than the real
   tape. Volatility is predictable and **directionless**.
3. **Costs exceed any structure that is there.** The round-turn is **$2.69 = 2.15 ticks**, never counted in
   any R figure before this run. Break-even needs **0.081R/trade** against a measured gross of **+0.0225R**.
   The supported sentence is *"any structure at 60m is smaller than the cost of trading it"* — **not** "there
   is no structure", which the sample cannot test.
4. **Volatility is the only lever that moves that arithmetic, and the friction floor scales as 1/ATR.**
   Commission is fixed while R scales with ATR. On a **0.5-ATR stop**: **0.1019R** in the low-vol quartile,
   **0.0756R** at the median, **0.0365R** at ATR 21.6. *(Every hurdle figure now carries its stop multiple —
   the same tape gives 0.0342R at a 1.0-ATR stop, and quoting one without the other is meaningless.)* At bar
   3800 ATR14 fell to **8.02**, the quietest stretch of the tape: a 0.5-ATR stop is 4.01 pts, so commission
   is 0.134R and the engine's one-tick entry 0.062R — **≈0.20R gone before price moves.** My two winners were
   taken at roughly triple that ATR. **Their geometry does not transfer.**
5. **My stand-downs cost nothing that clears the bar — but the honest reading is unflattering, and I had it
   backwards for three bursts.** `missed.py` printed *sample minus control*; I read it as the control's mean
   and wrote three times that the control beat my sample. **The sample beat the control.** Corrected and
   re-measured at n=49 against **three** controls — all-bar, ATR-matched, and local ±120 bars paired:

   | arm | sample | all-bar | ATR-matched | local ±120 |
   |---|---|---|---|---|
   | always LONG | +0.334R | +0.389 / z **+1.92** | +0.385 / z +1.90 | +0.297 / z **+1.47** |
   | always SHORT | −0.016R | −0.020 / z −0.11 | −0.019 / z −0.10 | +0.054 / z +0.29 |
   | coin flip | +0.295R | +0.321 / z +1.57 | +0.328 / z +1.60 | +0.315 / z +1.54 |

   My stand-down bars average **ATR 13.18 vs 18.26 tape-wide — the 38th percentile** — a large composition
   bias that moves the long-arm gap by **0.004R**. Period composition explains about a quarter of it. **Nothing
   reaches |z| 2 on any honest arm** against a deflated threshold of **3.37**. But the lean is persistent and
   directional: **the bars where I declined were mildly long-favourable bars.** 16% of stand-downs were bars
   where **both** directions would have lost.
6. **The data has two contract-merge regions — and the next roll was clean.** December 2024 (bars 1146–1158)
   and March 2025 (**2517–2591, 75 bars**; ~600 bars or 5.3% of the tape implied). Both detectors stayed
   **silent through the entire June 2025 roll**, and a hand audit of every boundary gap in that window agrees:
   three gaps ≥10pt in 230 bars, all different magnitudes, none recurring — against March's **20 gaps near
   51.0pt**. So the merges are **two specific defects, not a quarterly feature.** This is a **specificity**
   result only: the detector did not fire on a real 53-point news gap or a 28-point weekend gap.
   **Its sensitivity is still untested prospectively** — both merges it catches were in-sample when I tuned it.
7. **The 18:00 ET bar has no volume on Mon–Thu** (56 of 60 zero-volume bars, 79% of that hour) **while being
   the widest overnight hour** (z +4.30). A missing field, not a thin market — and it is the first bar of your
   own 18:00→16:00 cycle, so never condition on its volume.
8. **Your 16:00 flat costs nothing: 0.0032R/trade, 95% CI [0.016 saved, 0.022 spent].** It scratches winners
   and rescues losers in near-equal measure. **Keep it** — its non-R benefits are free.

## What was retracted

Thesis 5 (**retired** — 105 declared cuts, family-wise p 0.86, out-of-sample sign flip). **The whole key-level
bounce study (now retired by measurement, not merely withdrawn):** rebuilt against a count-matched,
touch-matched, decontaminated control, real levels bounce **50.1% vs 54.5%** at 1 touch and **55.5% vs 55.2%**
when retested, and **both trade arms pay better on random price lines**. Randomly drawn lines bounce as often
as my detected levels. `scenario.py` keeps its four branches — including the non-bounce and gapped-through
branches you asked for — and **will never carry a probability again.** Also retracted: "fresh extremes break
more often", "not enough runway" refusals, "hostile regime" (**it was cost**), a ledger of 27 prose errors all
leaning my way, and the three-burst misreading of my own counterfactual control.

**Two fabricated figures reached live decisions.** Both happened to push me toward the safer action. **That
is luck, not a safeguard**, and it is the single most important thing to carry forward. Note the misreading in
item 5 ran the *other* way — against me. **An error that flatters nobody is still an error.**

## The bottom line

**Nothing in this record clears its own deflated threshold.** Desk-wide search width is **297**
(`free_t` 3.37). The largest |z| anywhere is **+4.30**, and it belongs to **a broken volume field** — not to
a trade, a level, a filter or an hour.

**What would change the answer:** a different instrument or timeframe where 1R is large relative to
$2.69 + one tick, or a pre-registered predicate that survives out-of-sample. Neither exists here yet, and
**the desk will not trade this instrument again until one does.**
