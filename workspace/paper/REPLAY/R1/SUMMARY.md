# R1 — MES 60m walk-forward replay: what it established

**One page, for the account owner. `NOTES.md` is the full journal (2,100+ lines) and wins on any detail.**
Written at cursor **3400/11287**, 2026-09-29. **PAPER — UNVALIDATED throughout.**

## The result

| | |
|---|---|
| bars traded forward | **3,400** of 11,287 (2024-10-06 → 2025-05-12) |
| decisions journalled | **51** (2 trades, 49 stand-downs) |
| trades taken | **2 — both winners, +1.895R and +1.854R** |
| equity | **$50,000 → $50,688.86** (+1.38%), peak = current, **drawdown $0** |
| placebo separation | **z +1.021** against a stop-condition of 4.5 and a `free_t(20)` of 2.448 — **does not clear** |

**Two winning trades out of two is not evidence of anything, and the record says so in more detail than it
says anything else.** What follows is why.

## What is actually established

1. **The walk-forward integrity held.** Audited from both ends: **zero look-ahead breaches** across 678 price
   mentions (E3), **no look-ahead in the code** (E7), `as_of` and `bar_index` reconciling 45/45. One rule
   breach of my own — I read `state.json` during a tool outage — is self-reported in full; it contains no
   bars, so no future prices were obtained.
2. **MES 60m is a random walk in returns.** Variance ratios ≈1.0 at every horizon, all p ≥ 0.74; the naive
   autocorrelation test screams p = 1.1e-7 and **is an artefact of kurtosis 24**, with robust surrogates
   giving p = 0.23. A simulated random walk of the same length showed *more* apparent structure than the real
   tape. Volatility is predictable and **directionless**.
3. **Costs exceed any structure that is there.** The round-turn is **$2.69 = 2.15 ticks**, never counted in
   any R figure before this run. Break-even needs **0.081R/trade** against a measured gross of **+0.0225R**.
   The supported sentence is *"any structure at 60m is smaller than the cost of trading it"* — **not** "there
   is no structure", which the sample cannot test.
4. **Volatility is the only lever that moves that arithmetic, and it moves it 3×.** The hurdle is **0.1019R**
   in the low-vol quartile, **0.0756R** at the median, **0.0365R** at ATR 21.6. If this instrument is ever
   tradeable it is in high-ATR regimes — a **cost** claim, not an edge claim.
5. **My stand-downs cost nothing measurable.** Across 36 stop/target geometries × 3 honest direction arms,
   **0 of 36 reach |z| 2**. Under a fair, hour- and ATR-matched control, unchanged. 19% of stand-downs were
   bars where **both** directions would have lost.
6. **The data has two contract-merge regions and they are bigger than I first said.** December 2024
   (bars 1146–1158) and March 2025 (**2517–2591, 75 bars**). I told this record each roll cost ~13 bars, ~1%
   of the tape; **March cost 75, implying ~600 bars or 5.3%.** Any MES 60m result spanning a roll week is
   measuring the calendar spread. `SERIES_AUDIT.md` passes MES 60m as eligible and its four checks are blind
   to this.
7. **The 18:00 ET bar has no volume on Mon–Thu** (56 of 60 zero-volume bars, 79% of that hour) **while being
   the widest overnight hour** (z +4.30). A missing field, not a thin market — and it is the first bar of your
   own 18:00→16:00 cycle, so never condition on its volume.
8. **Your 16:00 flat costs nothing: 0.0032R/trade, 95% CI [0.016 saved, 0.022 spent].** It scratches winners
   and rescues losers in near-equal measure. **Keep it** — its non-R benefits are free.

## What was retracted

Thesis 5 (**retired** — 105 declared cuts, family-wise p 0.86, out-of-sample sign flip). All key-level and
touch-count claims (**withdrawn** — my control fabricated touch counts and tested at 31% higher ATR). "Fresh
extremes break more often" (**z 1.76 → −0.73** under a fair control). "Not enough runway" refusals
(**unsupported in R**). "Hostile regime" (**it was cost**). A ledger of 27 prose errors, all leaning my way.

**Two fabricated figures reached live decisions.** Both happened to push me toward the safer action. **That
is luck, not a safeguard**, and it is the single most important thing to carry forward.

## The bottom line

**Nothing in this record clears its own deflated threshold.** Desk-wide search width is **297**
(`free_t` 3.37). The largest |z| anywhere is **+4.30**, and it belongs to **a broken volume field** — not to
a trade, a level, a filter or an hour.

**What would change the answer:** a different instrument or timeframe where 1R is large relative to
$2.69 + one tick, or a pre-registered predicate that survives out-of-sample. Neither exists here yet, and
**the desk will not trade this instrument again until one does.**
