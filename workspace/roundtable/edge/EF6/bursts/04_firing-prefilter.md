# EF6 burst 04 — the firing-rate prefilter. Verdicts per (symbol, timeframe), verified not inherited.

**Built:** `EF6/code/firing.py` (census + audit + `prefilter`), `run_census.py`, `analyse_census.py`,
`run_prefilter.py`.
**Measured:** 40 census documents — 4 symbols × 10 frames — over `data/archive`.
**6,715 (condition, eval-timeframe) pairs measured. 404 VOID instances across 17 conditions.**

## Architecture: two steps, because the audit must be free

**Step 1, once per (symbol, frame):** one pass over the bars evaluating all 79 conditions at every
timeframe the frame carries, counting fires on three denominators, writing JSON. `frame.snapshot(i)`
rebuilds the cross-timeframe snapshot from scratch and is the expensive thing in any sweep, so the
bars are paid for exactly once. Cost: **8–120 s per cell.**

**Step 2, free, any number of times:** `firing.audit(strategies, census)` returns per strategy
which conditions fire on zero bars and therefore whether it is structurally incapable of trading.
No data access, no backtest. `firing.prefilter(strategies, census)` returns
`(tradeable, audit_rows)` so the removals are reportable — a VOID strategy is a finding about the
generator, not a strategy that lost.

**Three denominators, because the denominator is the whole argument.** `all` (every bar — what
R1's census measured), `window` (a position may exist under 18:00→16:00), and `signal` (a signal
here could be *filled* legally — `window` shifted one bar, because the engine fills at the next
bar's open). **VOID is judged on `signal`.**

## Validation against the engine — 0 false kills

The prefilter's only hard claim is that a VOID strategy cannot trade. Tested against an actual
`SessionWindowEngine` run over 11,29x bars:

| symbol | generated (primary 60m) | predicted VOID | **predicted-VOID that DID trade** | predicted-ALIVE that took 0 trades |
|---|---|---|---|---|
| MGC | 465 | 0 | **0** | 260 of 465 |
| MNQ | 412 | 82 | **0** | 185 of 330 |

`[measured: firing.audit vs ledger_{sym}_60m_big.json]`

So the prefilter is a **sound necessary condition**: it never kills a strategy that could trade,
and it is deliberately conservative in the other direction — conditions firing is necessary but
not sufficient, because stop feasibility, `min_stop_ticks`, the R:R floor and the engine's
refusal to re-signal while positioned all come *after* the conditions. It removes the rows that
are provably incapable and leaves the rest to be measured.

## The per-symbol VOID rate, on the exact call R1 used

`generate_strategies(sym, [5,15,60,240], max_total=400)`, 1,260 strategies (**R1's count exactly**),
audited on a base-5m census carrying 5/15/60/240, 57.90-day substrate:

| symbol | R1 reported | **EF6 measured** | by primary timeframe |
|---|---|---|---|
| MGC | 11.5% | **11.46%** (36/314) | 5m 0/54, 15m 0/54, 60m 0/136, **240m 36/70** |
| MCL | 13.9% | **10.14%** (30/296) | 5m 2/38, 15m 2/84, 60m 14/126, 240m 12/48 |
| MES | 22.6% | **16.67%** (56/336) | 5m 0/44, 15m 0/80, 60m 0/104, **240m 56/108** |
| MNQ | 27.4% | **18.79%** (59/314) | 5m 3/56, 15m 6/100, 60m 4/78, **240m 46/80** |
| pooled | 19.0% | **14.4%** (181/1260) | — |

**MGC replicates to two decimals. The other three do not, and the gap is explicable.** The largest
single cause is `session_extreme_sweep`: R1's D-L4 counts **46 strategies** as structurally dead
because the condition fires only outside RTH and `rth_only=True` vetoes every non-RTH bar. **Under
this programme's window rule `rth_only` must be False, and the condition comes back to life:**

| symbol | `session_extreme_sweep` fires on legal-entry bars (base-5m frame) |
|---|---|
| MGC | 5m **43**, 15m **163**, 60m **480**, 240m **1,652** |
| MCL | 5m **33**, 15m **114**, 60m **479**, 240m **2,134** |
| MES | 5m 1 (**THIN**), 15m **43**, 60m **316**, 240m **1,684** |
| MNQ | 5m 2 (**THIN**), 15m **45**, 60m **365**, 240m **1,951** |

So **a verdict flip in the favourable direction, and it is per (symbol, timeframe)** — THIN on the
index micros at 5m, alive everywhere else. That is the first thing "verify rather than inherit"
bought.

**And the per-symbol spread is largely a property of `profiles.groups_for`, not of the markets.**
`generate_strategies(..., groups=None)` uses a per-symbol template profile
`[repo-verified: combinator.generate_strategies → generate_combinations(..., groups=groups)]`:

```
groups_for(MGC) = TREND, SUPPLY_DEMAND, FIBONACCI, MULTI_TIMEFRAME, MEAN_REVERSION, VOLUME_PROFILE
groups_for(MNQ) = MOMENTUM, TREND, BREAKOUT, OPENING_RANGE, MULTI_TIMEFRAME, LIQUIDITY, PULLBACK
groups_for(MES) = LIQUIDITY, MEAN_REVERSION, MULTI_TIMEFRAME, PULLBACK, REVERSAL, VOLUME_PROFILE, VWAP
MCL → all 13
```

Measured consequence: **MGC generates 0 strategies carrying `oi_*` and 0 carrying
`opening_range_*`; MES generates 0 carrying `oi_*`.** Across the 1,260, `oi_*` carriers total
**23 — matching R1's count exactly — and not one of them is MGC or MES.** So `openinterest`
contributes *nothing* to MGC's or MES's VOID rate, and the 2.4× spread R1 measured (11.5%→27.4%)
is substantially "which templates the profile hands this symbol", not "what this market does".
A sweep passing `groups=ALL_GROUPS` gets different rates again (R4-M2 found the same for BREAKOUT).

**Correction to R1's Addendum C-3, verified.** It states that in this population "every one has
`confirm_tfs = ()` with `timeframe = None` on every condition". That is true only of the
`primary_tf = 240` subset. Measured over the whole call: `Counter(c.timeframe)` gives
**MGC `{None: 2027, 15: 44, 60: 26, 240: 86}`** and **MNQ `{None: 2074, 15: 36, 60: 76, 240: 54}`**,
and `(primary, execution, confirm)` includes `(15, 5, (60,240))`, `(60, 5, (240,))` and
`(240, 15, ())`. So **~7% of conditions are explicitly timeframe-bound and `execution_tf` is set on
roughly half the population.** An audit that judged every condition at `primary_tf` would
misattribute a sixth of the 240m VOIDs; `firing._eval_tf` mirrors `Strategy.evaluate` exactly.

---

## THE METHODOLOGICAL FINDING: VOID has **three** coordinates, not two

The shared vocabulary says "`VOID` is per (symbol, timeframe), never global". **Measured: it is per
(symbol, *evaluation* timeframe, *base* timeframe of the frame).** The same (condition, eval_tf)
gives opposite verdicts in different base frames:

| symbol | condition | eval tf | base 5m | base 15m | base 30m | **base 60m** |
|---|---|---|---|---|---|---|
| MGC | `opening_range_breakout` | 60m | 2,095 | 660 | 344 | **0** |
| MGC | `opening_range_fade` | 60m | 1,171 | 373 | 173 | **0** |
| MES | `opening_range_fade` | 60m | 1,015 | 327 | 155 | **0** |
| MNQ | `opening_range_fade` | 60m | 1,006 | 326 | 156 | **0** |
| MES | `power_hour` | 60m | 451 | 123 | 41 | **0** |
| MNQ | `power_hour` | 60m | 451 | 123 | 41 | **0** |
| MCL | `opening_range_breakout` | 60m | 2,135 | 734 | 383 | 1,731 (alive) |
| all 4 | `value_area_edge` | 240m | **0** | **0** | **0** | **0** |
| all 4 | `mtf_aligned` | 240m | **0** | **0** | **0** | 1,853–2,802 (alive) |

**Mechanism, and it is not subtle once seen.** `opening_range_*` read `snap.opening_range`, which
is built from **base** bars (`or_minutes = 30`), and `power_hour` reads `snap.minutes_since_open`
off the base bar's timestamp. On a coarse base grid the 30-minute opening range never completes
against an off-hour `rth_open` — MGC opens **08:20**, MCL **09:00**, MES/MNQ **09:30**
`[repo-verified: get_contract]` — and the last RTH hour lands on no bar boundary.
`mtf_aligned` is the mirror image: VOID at the **top** of every frame (voting can never reach 2) and
alive below it, so it is VOID at 240m in a 15m-base frame `[15,60,240]` and **alive** at 240m in a
60m-base frame `[60,240,1440]`.

**This settles the R1 / R4 dispute on `mtf_aligned` and both are right about different cells.**
R1's D-MTF1 ("VOID at the frame's top timeframe") is confirmed in **38 cells across all four
symbols, including the 3-timeframe FRAMES compositions the corpus builds** — not only in a
frame of one. R4's rebuttal is correct that a harness filtering `s.primary_tf == tf` never puts
the *primary* at the top; what R4's rebuttal misses is that **conditions are explicitly bound to
240m inside 15m- and 5m-primary strategies** (86 such bindings on MGC, 54 on MNQ), which is exactly
how the corpus reaches it. Measured consequence in the R1-comparable audit: **32 MNQ strategies
VOID via `mtf_aligned@240m` and 8 MES strategies via the same**.

> **Instruction to EF2–EF5: run the census on the frame you will measure on.** A census taken at
> one base timeframe and applied to strategies run at another is wrong in both directions — it
> will pass rows that cannot trade and kill rows that can.

---

## A VOID caused by this programme's session rule, and nothing else

`analyse_census.py` reports conditions that fire on some bar and on **no legally-enterable** bar:

```
MES 60m-base: power_hour@60m   488 fires, 0 legal
MES 60m-base: power_hour@120m  488 fires, 0 legal
MES 60m-base: power_hour@240m  488 fires, 0 legal
MNQ 60m-base: power_hour@60m   488 fires, 0 legal
MNQ 60m-base: power_hour@240m  488 fires, 0 legal
```

`power_hour` is "the final hour before **this contract's** RTH close"
`[repo-verified: library.py:893-910]`. MES and MNQ close at **16:00**, so their final hour is
15:00–16:00, and a 60m signal there fills at 16:00 — which the rule forbids. **MGC (13:30) and MCL
(14:30) are untouched**: their final hour fills legally. So this is a `VOID` that exists *only*
under this programme's session rule, only on the index complex, and only on a 60m-or-coarser base.

It also converges with `BRIEF.md` rule 5 ("no intraday entries 15:00–16:00 ET, z = −4.43,
replicated") from a completely different direction: the session rule now *enforces* on the index
micros what the empirical finding recommended.

## The full VOID inventory — 17 conditions, of which only **2** are VOID everywhere

| condition | group / kind | VOID cells | alive somewhere? |
|---|---|---|---|
| `oi_expanding` | openinterest / FILTER | **55 of 55** — all symbols, all bases, all eval tfs | **NO — VOID in every cell** |
| `oi_price_confirmation` | openinterest / SIGNAL | **55 of 55** | **NO — VOID in every cell** |
| `mtf_aligned` | multitimeframe / SIGNAL | 38 (frame-top) | yes, 36 cells |
| `mtf_strongly_aligned` | multitimeframe / SIGNAL | 38 (frame-top) | yes, 36 cells |
| `away_from_hvn` | profile / FILTER | 20 (eval 240m, 1440m) | yes, 35 |
| `lvn_rejection` | profile / SIGNAL | 20 (eval 240m, 1440m) | yes, 35 |
| `open_outside_value` | profile / FILTER | 20 | yes, 35 |
| `poc_reversion` | profile / SIGNAL | 20 | yes, 35 |
| `value_area_breakout` | profile / SIGNAL | 20 | yes, 35 |
| `value_area_edge` | profile / SIGNAL | 20 | yes, 35 |
| `opening_range_fade` | liquidity / SIGNAL | 8 — **MGC, MES, MNQ at base 60m only** | yes, 47 |
| `opening_range_breakout` | liquidity / SIGNAL | 4 — **MGC at base 60m only** | yes, 51 |
| `power_hour` | time / FILTER | 5 — **MES, MNQ at base 60m only** | yes, 50 |
| `fresh_zone_approach` | supplydemand / SIGNAL | 5 — MGC, MCL, MES at eval 240m/1440m | yes, 50 |
| `vwap_band1_bounce` | vwap / SIGNAL | 4 — all symbols at eval 1440m | yes, 51 |
| `pullback_to_support` | structure / SIGNAL | 3 — **MCL only**, eval 240m | yes, 52 |
| `zone_touch` | supplydemand / SIGNAL | 1 — **MGC only**, eval 1440m | yes, 54 |

**`CONDITION_ERRORS` was empty in all 40 cells** `[measured: census `condition_errors` field → `{}`
everywhere]`, so no VOID above is the silent-exception failure mode `base.py:180-215` warns about
(fifteen conditions once raised on every bar and were recorded as a 0% trigger rate). `THIN`
(1–4 fires) is reported separately from `VOID` so a rare condition is never called impossible.

## Per-cell rates on each timeframe's own FRAMES composition

`max_total=600`, filtered to that primary timeframe:

| symbol | 5m | 15m | 30m | 60m |
|---|---|---|---|---|
| MGC | 0/99 | 0/99 | 0/99 | 0/99 |
| MCL | 1/87 (1.1%) | 1/87 | 1/87 | 1/87 |
| MES | 0/100 (4 THIN) | 0/100 | 0/100 | **3/100 — all `power_hour@60m`** |
| **MNQ** | **14/75 (18.7%)** | **14/75** | **14/75** | **22/75 (29.3%)** |

And on a larger MNQ 60m population (`max_total=2500`, 412 strategies at primary 60m):
**82 VOID = 19.9%**, causes `opening_range_fade@60m` 34, `oi_price_confirmation@60m` 22,
`oi_expanding@60m` 19, `power_hour@60m` 17; by group LIQUIDITY 32, BREAKOUT 24, MOMENTUM 18,
OPENING_RANGE 8.

**At the scalp timeframes specifically: MGC 0%, MCL 1.1%, MES 0% (4 THIN), MNQ 18.7%.** The
scalp-timeframe VOID problem is **an MNQ problem**, driven by `oi_*` carriers (MNQ's profile gives
it MOMENTUM and BREAKOUT, which reach the `openinterest` conditions) and by nothing on the other
three symbols. Every symbol is its own universe and here the universes are not similar.

## The operational lesson that cost a rebuild

The first MNQ ledger recorded `prefiltered out 0, screened 412` — because `make_ledger` treated the
census as optional and the MNQ census was still being written. **82 of those 412 could not trade**,
so `screened` was overstated by 20% and 82 guaranteed nulls sat in the population. `make_ledger` now
**raises** when the census is missing. A silently-skipped prefilter is precisely the failure the
prefilter exists to prevent.

## Anti-overfitting checks in this burst

| hazard | checked | finding |
|---|---|---|
| **structural zero read as a market fact** | yes — the whole burst | 404 VOID instances; 82/412 on MNQ 60m alone |
| swallowed exceptions masquerading as 0% | yes | `CONDITION_ERRORS` empty in all 40 cells |
| inherited verdicts | yes | 3 of R1's 6 configurations **change** under this programme's rule or base frame: `session_extreme_sweep` is alive, `opening_range_*` depends on the base, `mtf_aligned` is alive at 240m in a 60m-base frame |
| rare vs impossible | yes | `THIN` (1–4 fires) reported separately from `VOID` (0) |
| directional VOID | yes, implemented | `audit(check_directions=True)` flags a strategy whose every allowed direction is dead on one SIGNAL condition (R4-R3's shape). None found in these populations |
| conjunction VOID (two conditions mutually exclusive) | **NOT covered** | the per-condition census cannot see `volatility_compressed ∧ volatility_expanding` (R1's D-V2, `atr_percentile <= 0.30 AND >= 0.70`). A pairwise co-fire pass would catch it; not built. **Stated as a gap.** The engine validation above bounds its impact: 0 false kills means the prefilter is under-inclusive, so a conjunction VOID would appear as a predicted-ALIVE strategy with 0 trades, which is where 260/465 MGC rows already sit |
| false kills | yes, validated | 0 on MGC and MNQ against a real engine run |
