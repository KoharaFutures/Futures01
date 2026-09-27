# EF2 / Burst 04 — fire attrition, and the stop kinds that are not the stop kind they say

Two measurements, both **harness-independent**, so both were available before EF1 validated.

---

## Part 1 — the strategy-level raw fire census

`Strategy.evaluate` reads only `snap` `[repo-verified: base.py:658-660]` and knows nothing about
position state, exits or session rules, so "on how many bars does this strategy's gate open" is a
property of the rule set and the data alone. **`BacktestResult.signals_generated` is not that number**
— the engine skips evaluation entirely while a position is open
`[repo-verified: engine.py:306-307]` — so it is harness-dependent and cannot substitute.

Code: `EF2/code/firecount.py`. Cost control: `evaluate` never touches the `ExitModel`, so arms sharing
a **gate signature** `(primary_tf, sorted condition labels, allowed directions, filters.identity)`
have identical fire sets and are evaluated once.

### Result — MGC, on post-VOID-gate arms

| cell | arms the VOID gate kept | arms with ≥1 raw fire | **arms that still never fire** |
|---|---|---|---|
| `MGC:f60__p60` | 1,440 | 481 | **959 = 66.6%** |
| `MGC:f60_240__p60` | 1,656 | 635 | **1,021 = 61.7%** |
| `MGC:f240__p240` | 998 | 333 | **665 = 66.6%** |
| `MGC:f60_240__p240` | 998 | 324 | **674 = 67.5%** |

**So the VOID gate removed about a third of the candidates and roughly two thirds of what it passed
still never fires over 718 days.** Those are two distinct findings and only the first is what the
programme's 19.0% figure describes:

- a **VOID** condition is a *structural* zero — the detector cannot fire in this (symbol, timeframe);
- these are *conjunctive* zeros — every condition fires somewhere, but the strict AND of 2–4 signals
  (which must also **agree on direction**) plus 2–4 filters plus `rth_only` is empty.

Both produce the same null and neither is a market fact. The practical consequence is the
**effective** search size: roughly a third of the published population, which lowers `free_t` by about
0.55 t-units — worth stating, and nowhere near enough to rescue a threshold of ~4.1.

Gate signatures equalled arm counts in every MGC cell (1,440 signatures for 1,440 arms, etc.), i.e.
**no two surviving rule sets differ only by their exit geometry** in this draw, so the dedupe bought
nothing. That is itself worth recording: it means the exit dimension in my population is spread across
distinct rule sets rather than nested inside them, so "which geometry is best for this rule set" is
**not** answerable from the screen and would need a deliberate re-emission.

---

## Part 2 — D45, and the finding that it is not confined to `VWAP_BAND`

`ExitModel.stop_price` ends **every** branch with `dist = max(dist, min_dist)`, where
`min_dist = spec.min_stop_ticks * spec.tick_size` `[repo-verified: base.py:313-315]`. When that clamp
binds, the stop is a **fixed number of ticks** whatever the enum says, and two arms differing only in
`stop_mult` become the same trade. Measured: MGC `min_stop_ticks = 25 × 0.1 = 2.5 points`
($25 at `point_value` 10); MCL `15 × 0.01 = 0.15` ($15 at 100).

Code: `EF2/code/stopfidelity.py`. Every distinct `ExitModel` any template can draw (**9** of them —
the same 9 seen from the population: no `RANGE`, no `FIXED_TICKS`), on **both directions**, at **every
swing-admissible bar**: 10,319 MGC bars and 9,993 MCL bars.

### The collapse rate

| cell | `VWAP_BAND` m1.0 p3 | `STRUCTURE` m1.0 p4 | `ATR` m0.75 | `ATR` m1.0–2.5 |
|---|---|---|---|---|
| MGC 60m (both frames) | **19.2%** | 3.8% | 0.0% | 0.0% |
| MGC 240m (both frames) | **12.4%** | 1.7% | 0.0% | 0.0% |
| MCL 60m (both frames) | **37.2%** | **7.5%** | 1.0% | 0.0% |
| MCL 240m (both frames) | **24.6%** | 3.7% | 0.0% | 0.0% |

**Three findings.**

**(a) D45 replicates, and its published range understates MCL at 60m.** The register entry says
`VWAP_BAND` silently becomes `FIXED_TICKS` on **6–34%** of bars; measured here **37.2% on MCL at
60m** — outside the top of the range. On a 718-day substrate rather than the 5,000-bar `csv/raw`
window, so this extends the finding rather than contradicting it.

**(b) `STRUCTURE` collapses too, and that is new as far as I can see.** The clamp is on the shared
tail, so the collapse is a property of the **floor**, not of `VWAP_BAND`. `STRUCTURE` hits the floor on
**7.5% of MCL 60m** bars and 3.8% of MGC 60m. `STRUCTURE` carries **17.6% of MGC arms and 23.4% of
MCL arms** — 6.7× as many as `VWAP_BAND` does on MGC — so in arm-weighted terms the `STRUCTURE`
collapse touches **more of the population** than the `VWAP_BAND` one does, even at a lower per-bar
rate. Anyone re-reading `x_exits`' "no stable best stop width" (the obligation the manager recorded as
open) should look at both, not only `VWAP_BAND`.

**(c) The floor is what actually enforces BRIEF rule 4.** "Structural stops: never tighter than ~0.5
ATR" is not implemented as a rule anywhere; it is a consequence of `min_stop_ticks` clamping. And on
MCL the tightest ATR geometry in the catalogue (`m0.75`) **does** reach the floor, on 1.0% of bars —
so `ATR m0.75` and `ATR m1.0` are the same stop on those bars, which is the same confound D45 names
in a different enum member.

### How much of the population this touches

| | MGC (5,092 arms) | MCL (5,584 arms) |
|---|---|---|
| `ATR` | 4,064 = 79.8% | 4,036 = 72.3% |
| `STRUCTURE` | 896 = **17.6%** | 1,308 = **23.4%** |
| `VWAP_BAND` | 132 = **2.6%** | 240 = **4.3%** |
| `R_MULTIPLE` targets | 2,548 = 50.0% | 2,840 = 50.9% |
| `ANCHOR_ATR` | 1,768 = 34.7% | 1,764 = 31.6% |
| `ANCHOR_STRUCTURE` | 776 = 15.2% | 980 = 17.6% |

**Reporting rule EF2 adopts as a result of this:** every top-10 row states its `stop_kind`, and any row
carrying `VWAP_BAND` or `STRUCTURE` also states the measured collapse rate for its cell, because that
row is partly a result about a fixed-tick stop. A row carrying `VWAP_BAND` on MCL 60m is a result about
a fixed-tick stop on **37% of its candidate bars** and cannot be described as a VWAP-band strategy
without that number beside it.

### The other silent route to a low trade count, quantified

`stop_price` returns `None` when the stop cannot be placed, and the trade is then **not taken** with no
record `[repo-verified: base.py:272-275 docstring, and every branch's early return]`. Measured rate:

| kind | MGC 60m | MGC 240m | MCL 60m | MCL 240m |
|---|---|---|---|---|
| `ATR` (any mult) | 0.1% | 0.5% | 0.1% | 0.5% |
| `STRUCTURE` | 0.1% | 0.3% | 0.2% | 0.4% |
| `VWAP_BAND` | **0.0%** | **0.0%** | **0.0%** | **0.0%** |

Small — 0.1–0.5%, consistent with ATR/swing warm-up at the start of each series rather than with a
structural hole — so it is **not** a material contributor to the two-thirds attrition in Part 1. Worth
having measured rather than assumed, since an unmeasurable-stop veto and a never-firing gate are again
the same null.
