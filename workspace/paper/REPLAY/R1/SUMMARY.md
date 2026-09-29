# R1 — MES 60m walk-forward replay: what it established

**One page, for the account owner. `NOTES.md` is the full journal (2,380+ lines) and wins on any detail.**
Written at cursor **6050/11316**, 2026-09-29 (the source series is live-appending — 11287 → 11316 between firings, so the denominator is provisional). **PAPER — UNVALIDATED throughout.**

> **One thing needs your ruling, not mine.** The branch's head commit is a CALL-desk stop — *"stop your call
> outs for now"* — which deleted that desk's crons. It says nothing about REPLAY, and it was said in a CALL
> session about live actionable cards on MGC/MNQ. My "callouts" are journal rows inside a replay of 2025
> history that nobody can act on, so I read the stop as scoped to that desk and kept going. **If you meant it
> desk-wide, say so and this stops immediately.**

## The result

| | |
|---|---|
| bars traded forward | **6,050** of 11,316 (2024-10-06 → 2025-10-24) |
| decisions journalled | **57** (2 trades, 55 stand-downs) |
| trades taken | **2 — both winners, +1.895R and +1.854R** |
| equity | **$50,000 → $50,688.86** (+1.38%), peak = current, **drawdown $0** |
| placebo separation | **z +1.021** vs a 4.5 stop-condition and `free_t(20)` 2.448 — **does not clear**, and it is **one** measurement (n=2 vs n=2), unchanged since bar ~1400, not a repeated confirmation |

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
4. **Volatility cuts the cost 4.4× and does NOT make this instrument tradeable. This closes the one door
   the record had left open.** Commission is fixed while R scales with ATR, so the friction floor falls from
   **0.1102R** in the quietest quartile to **0.0252R** in the loudest (1.0-ATR stop; on a 0.5-ATR stop the
   figures double). Earlier versions of this page said *"if this instrument is ever tradeable it is in
   high-ATR regimes"*. **Tested across all 6,020 eligible bars and it is not.** Directional efficiency
   (`|close−open| / range`) is **flat at 0.436–0.448 in every ATR quartile** — high volatility buys range and
   no extra direction. The 2R target gets *less* reachable as ATR rises (**57.9% → 49.4%**). And every honest
   arm is **negative in every bucket**, with always-long non-monotone and peaking in Q3, not Q4. Net of
   friction a coin flip runs **−0.202R in Q1 and −0.054R in Q4**: less bad, never positive. **Waiting for
   volatility reduces the loss rate; there is no positive gross for cheaper friction to rescue.** The
   October 2025 window shows it plainly — daily ranges of 129/115/119/147 points and ~7 points of net
   movement across four closes. In a tape whose returns are a random walk (finding 2), volatility being
   predictable while direction is not is exactly what produces this.
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
   +0.1272 tape-wide**, so I decline in stretches rising **2.3× faster** than average. The long arm briefly crossed |z| 2 and has **fully decayed** as n grew: all-bar **+2.09 → +2.01 → +1.92**
   across n=51/52/53, paired-local **+1.77 → +1.65 → +1.52**. Reported when it crossed because the brief
   requires it; watched out of the region since — **reported because the brief requires it,
   and not a finding**: it fails `free_t(297)` = 3.375, fails even `free_t(12)` = 2.229 counting only the
   controls run on this one sample, weakens to **+1.77** under the strictest (period-matched) control, and
   above all **is not a rule** — "go long where I declined" describes a sample defined by my own
   non-reproducible discretion. A drift-removed arm built to settle it gave the biggest z yet (+2.08) and
   was **withdrawn**: prior-window drift correlates **−0.093** with realised forward drift (R² 0.86%), so it
   subtracts noise, not trend. It is kept in the code labelled INVALID rather than deleted. **What survives
   is a standing note, not an edge: my stand-downs skew long-favourable.** 16% of stand-downs were bars
   where **both** directions would have lost.
6. **The contract merges are the QUARTERLY ROLL — four of them now — and ~5% of this tape is calendar
   spread, not price.** December 2024, March 2025 (**75 bars**), June 2025 and September 2025, each the
   Monday–Tuesday of a roll week. **The one pre-registered test this desk has run resolved here and it
   split: the prediction was right and the instrument was wrong.** At bar 4450 I predicted a September
   merge near bar 5450 (window 5350–5600); it is at **5396–5398**, three ~63-point bars oscillating between
   two bands 60 points apart, after which the tape sits permanently at the upper level. **Both detectors
   missed it** — one needs 4+ consecutive bars (this is 3), both need a boundary *jump* (here the two
   contract bands appear *within* single bars). Their parameters were set when the only known merges
   happened to be long and to jump. **I did not retune them** — that would be a third fitting round with no
   independent test left. A third screen was added on a physical argument instead (**range explodes,
   volume does not** — a merged bar is wide because it spans two instruments, so its width carries no
   trade): 13 flagged bars over 5650, all 13 inside merge regions, **but in-sample on all four merges and
   explicitly a screen, not a verdict.** **Pre-registered at bar 5650: the December 2025 roll must show a
   merge near bar 6829, window 6700–6950.** `SERIES_AUDIT.md` passes MES 60m as eligible and is blind to
   all of this.
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

**Nothing in this record clears its own deflated threshold.** Desk-wide search width is **310**
(`free_t` 3.39). The largest |z| anywhere is **+4.30**, and it belongs to **a broken volume field** — not to
a trade, a level, a filter or an hour.

**What would change the answer:** a different instrument or timeframe where 1R is large relative to
$2.69 + one tick, or a pre-registered predicate that survives out-of-sample. Neither exists here yet, and
**the desk will not trade this instrument again until one does.**
