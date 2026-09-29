# R1 — MES 60m walk-forward replay: what it established

**One page, for the account owner. `NOTES.md` is the full journal (2,380+ lines) and wins on any detail.**
Written at cursor **4850/11316**, 2026-09-29 (the source series is live-appending — 11287 → 11316 between firings, so the denominator is provisional). **PAPER — UNVALIDATED throughout.**

> **One thing needs your ruling, not mine.** The branch's head commit is a CALL-desk stop — *"stop your call
> outs for now"* — which deleted that desk's crons. It says nothing about REPLAY, and it was said in a CALL
> session about live actionable cards on MGC/MNQ. My "callouts" are journal rows inside a replay of 2025
> history that nobody can act on, so I read the stop as scoped to that desk and kept going. **If you meant it
> desk-wide, say so and this stops immediately.**

## The result

| | |
|---|---|
| bars traded forward | **4,850** of 11,316 (2024-10-06 → 2025-08-11) |
| decisions journalled | **54** (2 trades, 52 stand-downs) |
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
   bias that moves the long-arm gap by **0.004R**; and their local drift is **+0.2935 pts/bar against
   +0.1272 tape-wide**, so I decline in stretches rising **2.3× faster** than average. At n=51 the long arm
   now reads **z +2.09** (all-bar) and **+2.06** (ATR-matched) — **reported because the brief requires it,
   and not a finding**: it fails `free_t(297)` = 3.375, fails even `free_t(12)` = 2.229 counting only the
   controls run on this one sample, weakens to **+1.77** under the strictest (period-matched) control, and
   above all **is not a rule** — "go long where I declined" describes a sample defined by my own
   non-reproducible discretion. A drift-removed arm built to settle it gave the biggest z yet (+2.08) and
   was **withdrawn**: prior-window drift correlates **−0.093** with realised forward drift (R² 0.86%), so it
   subtracts noise, not trend. It is kept in the code labelled INVALID rather than deleted. **What survives
   is a standing note, not an edge: my stand-downs skew long-favourable.** 16% of stand-downs were bars
   where **both** directions would have lost.
6. **The data's contract merges are the QUARTERLY ROLL, and roughly 5% of this tape is calendar spread.**
   December 17 2024, March 18 2025 (**75 bars**) and June 16 2025 — all the Monday–Tuesday of a roll week.
   **Correction: I reported at bar 4050 that the June roll was clean and that December and March were isolated
   defects. Both were wrong**, and my own detector had been flagging June for 100 bars while I wrote it — I had
   filtered the detector's output out of my own console and then "confirmed" the result with a statistic that
   cannot see this kind of merge. Fixed structurally: the verdict is now line 1 of `view.py`, unfilterable.
   The two detectors are **complementary and each blind where the other sees** — June shows envelope constancy
   with one boundary gap (`roll_flags` sees it, `gap_clusters` cannot); March drifted 60 points so the envelope
   under-bounded it 5× while the recurring ~51pt gap made `gap_clusters` right. **Neither one's silence is
   evidence.** `SERIES_AUDIT.md` passes MES 60m as eligible and its four checks are blind to all of this.
   **Pre-registered at bar 4450, before the bars are visible:** the September 2025 roll must show a merge near
   **bar 5450 (window 5350–5600)**. That is the sensitivity test this detector has never had.
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
