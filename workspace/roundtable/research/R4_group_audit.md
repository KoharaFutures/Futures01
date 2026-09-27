# R4_group_audit — the condition-group audit over R3's surface (`MGR-T4`)

**Task:** board item `MGR-T4` — 7 groups, 31 conditions: `trend` (8), `momentum` (6),
`meanreversion` (3), `volatility` (3), `regime` (3), `multitimeframe` (3), `candlestick` (5).
`[measured: python3 -c "from futures_agents.strategies.library import CONDITIONS; ..." → 8+6+3+3+3+3+5 = 31]`
**Anchor id:** `DISC-LEAD-05`. **Holder on the board:** R3, reassigned to R4 because R3 is loaded
with `MGR-T17` `[repo-verified: manager/BOARD.md:130]`.

**Method and vocabulary:** R1's, from `research/R1_group_audit.md:15-25` —
CLEAN / HONEST-DERIVED / PROXY / DEGRADED / DEAD / MISNAMED. Every claim carries
`[repo-verified: path:line]`, `[measured: cmd → result]` or `[general knowledge]`.

---

## The first thing a reader needs to know: this surface has already been audited once

`MGR-T4` was cut on 2026-09-26 as R3's third of a three-way split (ADJ-8,
`msgs/07_manager_discovery_lead05-and-x15.md`), on the assumption that R1 would audit only
`structure`, `supplydemand`, `fibonacci` (`MGR-T5`, 12 conditions). **R1 audited all 16 remaining
groups instead** — its own 12 plus my 31 plus R2's 4 — and `research/R1_group_audit.md` carries a
verdict for every one of my 31 conditions:
`candlestick` at `:110-160`, `meanreversion` at `:329-372`, `momentum` at `:374-430`,
`multitimeframe` at `:432-506`, `regime` at `:568-628`, `trend` at `:690-726`, `volatility` at
`:728-800` `[repo-verified: research/R1_group_audit.md, section headers "Group 4/7/8/9/11/15/16"]`.

**So `MGR-T4` as written is already done, and re-doing it would produce a second opinion nobody
asked for.** What has *not* been done is the thing an audit most needs and almost never gets: an
**independent replication** by someone who did not write the first verdicts. That is what this file
is. Three modes:

| mode | what it means |
|---|---|
| **CONFIRMED** | I re-derived R1's verdict from the code and/or re-measured it, independently, and agree |
| **REFINED** | R1's verdict stands; a load-bearing part of its stated *consequence* is wrong or incomplete |
| **CONTRADICTED** | I read the same lines and reach a different verdict |

Every CONTRADICTED and REFINED entry names the R1 line it disagrees with, per `REGISTRY.md`
("quote the id you are disagreeing with and the path you read it at").

I also add the two things the dispatch asks for that R1's file does not fully carry for these
7 groups: the **template requirement map measured from `TEMPLATES` for my 31**, and
**structural deadness per symbol AND per timeframe against the frames the corpus actually builds**
— R1 measured 2 of 4 symbols for `multitimeframe` and `regime`, and measured timeframe bindings the
harness never generates. That last point is `R4-M1` below and it is the one finding here that
contradicts R1's *method*.

---

## R4-M0 — the template requirement map for my 31 conditions, measured

`[measured: python3 -c "from futures_agents.strategies.combinator import TEMPLATES; from futures_agents.strategies.library import CONDITIONS; ..." → the table below]`

| template | required (mine) | optional signal group (mine) | base filter (mine) — unconditional | optional filter (mine) |
|---|---|---|---|---|
| TREND | **`trend`** | momentum, multitimeframe, regime, candlestick | `volatility_normal`, `regime_trending` | `adx_trending`, `efficiency_high` |
| PULLBACK | **`trend`, `meanreversion`** | multitimeframe | `volatility_normal`, `mtf_not_conflicted` | — |
| VWAP | — | momentum, trend | `volatility_normal` | — |
| REVERSAL | **`meanreversion`** | momentum, candlestick | `volatility_normal` | — |
| MOMENTUM | **`momentum`** | trend, multitimeframe, regime | `volatility_normal` | — |
| OPENING_RANGE | — | momentum, trend | `volatility_normal` | — |
| LIQUIDITY | — | momentum, candlestick | `volatility_normal` | — |
| MEAN_REVERSION | **`meanreversion`** | momentum | `volatility_normal`, `regime_ranging` | — |
| BREAKOUT | — | trend, momentum | **`volatility_compressed`** | **`volatility_expanding`** |
| MULTI_TIMEFRAME | **`multitimeframe`** | trend, momentum | `volatility_normal` | `adx_trending` |
| VOLUME_PROFILE | — | trend, momentum | `volatility_normal` | — |
| SUPPLY_DEMAND | — | trend, momentum, candlestick | `volatility_normal` | `inside_bar_compression` |
| FIBONACCI | **`trend`** | momentum | `volatility_normal` | `efficiency_high` |

**Reach of my 7 groups, counted:** `trend` required by 3 (TREND, PULLBACK, FIBONACCI) + optional
signal in 7; `meanreversion` required by 3 (PULLBACK, REVERSAL, MEAN_REVERSION); `momentum` required
by 1 and optional in 11 — the widest optional reach in the library; `multitimeframe` required by 1 +
base filter in PULLBACK; `regime` base filter in 2 + optional signal in 2; `volatility` base filter
in **13 of 13** (`volatility_normal` in 12, `volatility_compressed` in BREAKOUT); `candlestick`
required by none, optional signal in 4. **This agrees with R1's map at `R1_group_audit.md:45-64`
on every row for my groups** — CONFIRMED — with two additions R1's map omits, both filters:
`adx_trending` is an optional filter in TREND and MULTI_TIMEFRAME, and `efficiency_high` in TREND
and FIBONACCI `[repo-verified: combinator.py:176, 285, 325]`. R1's map leaves `trend`'s
optional-filter column empty.

## R4-M1 — a required group with no SIGNAL member is silently dropped, and `volume` is one

This is new, it is structural, and it changes two rows of R1's map.

`_signal_pools` builds each group's pool from **SIGNAL conditions only**, then discards empty pools:

```
combinator.py:361-369
def _signal_pools(template):
    def pool(group):
        return sorted(n for n in CONDITION_GROUPS.get(group, [])
                      if CONDITIONS[n].kind is ConditionKind.SIGNAL)
    required = [pool(g) for g in template.required_groups]
    optional = [pool(g) for g in template.optional_groups]
    return [p for p in required if p], [p for p in optional if p]
```

`[repo-verified: futures_agents/strategies/combinator.py:361-369]`

**Four groups contain zero SIGNAL conditions:** `volatility` (0/3), `volume` (0/3), `time` (0/4),
`news` (0/3) `[measured: python3 over CONDITION_GROUPS + CONDITIONS[n].kind → candlestick 4/5,
fibonacci 3/4, imbalance 2/3, liquidity 7/7, meanreversion 3/3, momentum 6/6, multitimeframe 2/3,
news 0/3, openinterest 1/2, orderflow 3/3, profile 4/6, regime 1/3, structure 5/5, supplydemand 2/3,
time 0/4, trend 6/8, volatility 0/3, volume 0/3, vwap 4/5]`.

`volume` is declared in `required_groups` for two templates, and **in both the requirement is inert**:

| template | `required_groups` as declared | actually enforced | dropped |
|---|---|---|---|
| **MOMENTUM** | `('momentum', 'volume')` `[repo-verified: combinator.py:215]` | `momentum` only | **`volume`** |
| **BREAKOUT** | `('structure', 'volume')` `[repo-verified: combinator.py:268]` | `structure` only | **`volume`** |

`[measured: python3, for each template comparing required_groups against the groups with ≥1 SIGNAL]`

MOMENTUM is also the **one template of thirteen without `volume_not_thin` in `base_filters`** —
its base set is `('volatility_normal',)` alone `[repo-verified: combinator.py:219]`. So a generated
MOMENTUM strategy can contain **no volume condition of any kind**, in a template whose own
`required_groups` names one. Measured on the default profile path:

| symbol | MOMENTUM generated | of those, **zero `volume` conditions** |
|---|---|---|
| MNQ | 40 | **24** |
| MCL | 25 | **15** |
| MGC / MES | 0 (see `R4-M2`) | n/a |

`[measured: python3, generate_strategies(sym,[5,15,60,240],max_total=400), group=='MOMENTUM', counting conditions whose CONDITIONS[n].group=='volume']`
example MNQ rule set: `['break_of_structure','delta_divergence','price_above_ema50','rsi_directional','volatility_normal']`.

**Consequence for R1's map, which is the reason this is a REFINED and not a footnote.**
`R1_group_audit.md:1114` lists `volume` as "required by **MOMENTUM, BREAKOUT**" and
`:1157` lists MOMENTUM's required group as clean via `volume`. Both rows describe a requirement the
combinator does not enforce. It matters twice over:

1. **R1-D-M2's stated consequence is overstated.** R1 writes that a MOMENTUM strategy whose only
   `momentum` condition is `rsi_extreme_reversal` is "a mean-reversion strategy published under the
   MOMENTUM template's name, **with a `volume` filter on it**" `[repo-verified: R1_group_audit.md:426]`.
   For 24 of 40 MNQ MOMENTUM strategies there is no volume filter on it. The misfiling is real and
   worse than stated: the template's *entire* declared content beyond `momentum` is absent.
2. **It is a latent trap with no guard.** Nothing warns that moving a condition from SIGNAL to
   FILTER silently deletes a template's requirement. `if not required: continue` at
   `combinator.py:513` means a template whose every required pool emptied would be skipped in
   silence rather than raising — the same failure shape as `D38` and as the `openinterest` FILTER.

`volume` is also a declared **optional** signal group in 6 templates where it can contribute nothing:
TREND, VWAP, OPENING_RANGE, LIQUIDITY, VOLUME_PROFILE, SUPPLY_DEMAND
`[measured: same run, optional pools that come back empty]`. Lower stakes — an optional slot that
cannot be filled just narrows the search — but it means published "optional group" counts overstate
the reachable variety by one group in six templates.

**Not my group to rule on.** `volume` is R1's surface (audited at `R1_group_audit.md:728-800`
region / Group 17). Posted to R1 rather than asserted into its file.

## R4-M2 — `generate_strategies`' default path narrows templates per symbol, and that is why R1's BREAKOUT sample had two empty symbols

R1's D-V2 reachability probe reports "**BREAKOUT strategies generated: 60**" with "10 carrying
`volatility_expanding`" and notes "MGC and MES did not **in this sample**"
`[repo-verified: R1_group_audit.md:785-793]`. **I reproduced those numbers exactly** — and the cause
is not the RNG.

`generate_combinations` falls back to a per-contract template profile whenever the caller does not
name groups:

```
combinator.py:495-500
    if groups:
        wanted = list(groups)
    else:
        from .profiles import groups_for
        wanted = list(groups_for(symbol, [t.group for t in TEMPLATES])
                      or [t.group for t in TEMPLATES])
```

`[repo-verified: futures_agents/strategies/combinator.py:495-500; futures_agents/strategies/profiles.py]`

| symbol | templates on the default path | BREAKOUT present? |
|---|---|---|
| MGC | TREND, SUPPLY_DEMAND, FIBONACCI, MULTI_TIMEFRAME, MEAN_REVERSION, VOLUME_PROFILE (6) | **no** |
| MNQ | MOMENTUM, TREND, BREAKOUT, OPENING_RANGE, MULTI_TIMEFRAME, LIQUIDITY, PULLBACK (7) | yes |
| MES | VWAP, VOLUME_PROFILE, MEAN_REVERSION, PULLBACK, REVERSAL, LIQUIDITY, MULTI_TIMEFRAME (7) | **no** |
| MCL | *no profile* → all 13 | yes |

`[measured: python3, futures_agents.strategies.profiles.groups_for(sym, ALL_GROUPS)]`

So MGC and MES produce **zero** BREAKOUT strategies on that path, at any `max_total`, for a reason
that has nothing to do with sampling. R1's "in this sample" is an under-attribution.

**And the correction cuts the other way for the corpus.** Every published harness passes
`groups=` explicitly and therefore bypasses the profile:
`workspace/studies/toolkit.py:158-160` (`groups=list(groups) if groups else ALL_GROUPS`),
`workspace/bigscan/cell.py:88-90` and `workspace/chrono/ledger.py:38-40`
(both `groups=[t.group for t in TEMPLATES]`), `futures_agents/scout.py:232-235` (same)
`[repo-verified: those four call sites]`. So the corpus generated all 13 templates for all four
symbols, and the structurally-zero-trade BREAKOUT population is **larger** than R1's probe implies:

| path | BREAKOUT generated | with `volatility_expanding` | with `oi_expanding` | with both |
|---|---|---|---|---|
| default profile (R1's probe) | 60 (MNQ 42, MCL 18, MGC 0, MES 0) | 10 | 10 | 0 |
| **`groups=ALL_GROUPS`** (the corpus's path) | **84** (MGC 24, MNQ 24, MCL 18, MES 18) | **14** | **14** | 0 |

`[measured: python3, generate_strategies(sym,[5,15,60,240],max_total=400) with and without groups=ALL_GROUPS, four symbols]`

**28 of 84 = exactly one third** of reachable BREAKOUT strategies are structurally zero-trade, on
**all four symbols**, not two. R1's headline fraction ("roughly a third") is right; its symbol
coverage was halved by an artefact of its own probe. **CONFIRMED with a wider blast radius.**

I also confirm the two emptiness mechanisms by reading, independently of R1:
`volatility_compressed` gates `p <= 0.30` and `volatility_expanding` gates `p >= 0.70`, **both on
`s["atr_percentile"]` resolved through the same `_s(snap, tf)`**
`[repo-verified: library.py:724-743]`, so the conjunction is empty by arithmetic for any `tf`, not
only for `timeframe=None`. That is a slightly stronger statement than R1's, which rested on the
measured binding.

## R4-M3 — **the method correction**: R1's per-timeframe deadness tests use timeframe bindings the harness never generates, and the frames it does generate hold a worse defect

This is the one place where I am not extending R1's method but disagreeing with it.

### The binding R1 measured does not occur in the corpus

R1's D-MTF1 ("both signal conditions are DEAD at the frame's top timeframe, so MULTI_TIMEFRAME
cannot exist there") and D-MTF2 and D-R1 are all measured as
`build_symbol_frame(series_5m, [5,15,60,240])` with the condition evaluated at `tf = 240` or `tf = 60`
`[repo-verified: R1_group_audit.md:441-455, 587-601]`. **The corpus never binds a strategy that way.**
The frame is chosen by primary timeframe from a fixed map, and in every row the primary timeframe is
the **lowest** member:

```
futures_agents/scout.py:58-67
FRAMES = {5: [5, 15, 60], 15: [15, 60, 240], 30: [30, 60, 240],
          60: [60, 240, 1440], 240: [240, 1440], 1440: [1440, 7200]}
```

`[repo-verified: futures_agents/scout.py:58-67, re-exported as workspace/studies/toolkit.py:FRAMES]`

and every runner then keeps only the strategies whose primary equals that key —
`if s.primary_tf == tf` `[repo-verified: toolkit.py:161, bigscan/cell.py:90, chrono/ledger.py:40,
scout.py:230-235]`. So **`agreeing_timeframes(from_tf=primary)` always has at least two members,
because `FRAMES` always appends higher timeframes to the primary.** R1's DEAD-at-top verdict describes
a frame nobody builds, and it is why the verdict reads as more consequential than it is.

My census, at the corpus's own bindings, on all four symbols:

| frame | bind | `mtf_aligned` fires | `mtf_strongly_aligned` fires |
|---|---|---|---|
| see the `multitimeframe` section below — **non-zero in every corpus cell on every symbol** | | | |

### What the corpus frames do hold: `FRAMES[1440]`'s "weekly" timeframe is the daily series again, lagged

`align_bucket` ignores `minutes` for anything `>= 1440`:

```
data/bars.py:145-149
d = to_et(ts)
if minutes >= 1440:
    day = trading_day(d)
    return datetime.combine(day - timedelta(days=1), datetime.min.time(),
                            tzinfo=ET).replace(hour=18)
```

`[repo-verified: futures_agents/data/bars.py:138-156]`

So `align_bucket(ts, 7200) == align_bucket(ts, 1440)` for every timestamp, and resampling a daily
series to 7200m produces **one bar per trading day**, not one per five:

| check | result |
|---|---|
| bars per "7200m" bucket, MGC daily | `Counter({1: 2511})` — **every bucket holds exactly one daily bar** |
| `resample(daily, 7200, keep_partial=False)` length | 2510 from 2511 inputs (the last is dropped because `count >= expected=5` fails) |
| OHLCV of the "7200m" series vs the daily series, in order | **2510 / 2510 bit-identical** (MGC); 1858/1858 (MNQ); 1858/1858 (MES) |
| `Bar.minutes` field | labelled **7200** on a one-session bar |

`[measured: python3 over csv/raw/{MGC,MNQ,MES}_1d.csv → align_bucket(b.ts,7200)==align_bucket(b.ts,1440) for all bars; Counter of bars-per-bucket; in-order OHLCV comparison]`

The two copies are **not** interchangeable inside the frame, and the reason is the mislabelled
`minutes`: `_build_alignment` advances a timeframe's pointer only when `tf_bars[j].end_ts <= bar.end_ts`
`[repo-verified: features.py:828-847]`, and `end_ts = ts + 7200 minutes` = five days after the bar's
own single session. So the "weekly" pointer trails the daily pointer:

| symbol | pointer lag `idx(1440) − idx(7200)` | bars with no "7200" bar yet |
|---|---|---|
| MGC | 1: 70, **2: 971, 3: 545, 4: 921** | 4 |
| MNQ | 1: 51, **2: 719, 3: 402, 4: 685** | 2 |
| MES | 1: 51, **2: 719, 3: 402, 4: 685** | 2 |

`[measured: python3, SymbolFrame._align[1440] vs _align[7200] over csv/raw/*_1d.csv]`

**So at the daily frame, "the higher timeframe" is the same series read 2–4 sessions late.** Every
multi-timeframe statement at 1440m — `mtf_aligned`, `mtf_strongly_aligned`, `mtf_not_conflicted` —
is therefore a **lagged-autocorrelation test on one series**, not a cross-timeframe test. Measured,
`structure_trend(1440) == structure_trend(7200)` on only 1846/2507 (MGC), 1403/1857 (MNQ),
1460/1857 (MES) bars `[measured: python3, SymbolFrame.snapshot(i).tfs[tf].structure_trend]` — the
disagreement is entirely the lag, because the underlying bars are identical.

This bears directly on **`BRIEF.md` rule 2** ("multi-timeframe agreement is not a virtue", z = −4.09).
At the daily frame the treatment being measured was not agreement between timeframes. R1 reached a
related conclusion from a different mechanism (`R1_group_audit.md:503-506`); this is a second,
independent reason the rule-2 measurement may not be about its stated subject, and it is a defect
in `align_bucket`, not in the conditions.

### And the regime timeframe in the corpus frames is *coarser* than the strategy, not finer

R1's D-R1 illustrates the defect as "a 4h TREND strategy in a `[5,15,60,240]` frame is gated by the
**15-minute** regime" `[repo-verified: R1_group_audit.md:607-609]`. In the frames the corpus actually
builds, `_default_regime_tf`'s preference list `(15, 30, 5, 60, 10, 3, 1)` misses entirely at the two
highest rows and falls through to `return self.timeframes[-1]` `[repo-verified: features.py:820-826]`:

| primary tf | frame built | **`regime_tf` chosen** | relation to the strategy's own timeframe |
|---|---|---|---|
| 5 | [5, 15, 60] | **15** | 3× **coarser** |
| 15 | [15, 60, 240] | 15 | same |
| 30 | [30, 60, 240] | 30 | same |
| 60 | [60, 240, 1440] | 60 | same |
| **240** | [240, 1440] | **1440** | **6× coarser — the daily regime gates a 4-hour strategy** |
| **1440** | [1440, 7200] | **7200** | the mislabelled daily copy, i.e. the lagged daily regime |

`[measured: census.py over csv/raw, 23 cells, `SymbolFrame.regime_tf` — identical on all four symbols]`

So the defect R1 found is real and I confirm it, but **its sign in the published corpus is the
opposite of R1's example** at the two coarse rows and **nil at three of six rows**. `volatility_normal`
(base filter in 12 of 13 templates), `regime_trending` (TREND) and `regime_ranging` (MEAN_REVERSION)
are on-timeframe at 15m, 30m and 60m, coarser-by-3× at 5m, and read the **daily** regime at 240m.
That is a smaller total blast radius than R1's framing implies and a much sharper single-cell one.
**REFINED.**

---

# DECLARED ANCHOR — read this before any verdict below

**2026-09-27, mid-task.** My dispatch told me to read `research/R1_group_audit.md` in full "for the
method and vocabulary you are continuing", and I did — **all 1,281 lines, including R1's
per-condition verdicts for all 31 of my conditions**, before forming any of my own. The coordinator
then corrected the dispatch (`R1-REQ-6`): verdicts must be formed independently and compared
afterwards, because one audit plus one agent anchored on it is one audit.

**I cannot unread it, so I am declaring it rather than pretending otherwise.**

> **Every verdict in this file was formed after seeing R1's verdict for the same condition.**
> None of the 31 is an independent verdict in the strict sense. Treat any agreement between this
> file and `R1_group_audit.md` as **corroboration of the reading, not replication of the audit.**

What is *not* anchored, and is therefore the part of this file with independent evidential value:

1. **The measurements.** My census is my own harness (`census.py`, 31 conditions × 47 cells) on a
   **different cell design** from R1's: the corpus's own `FRAMES` groups, all four symbols, six
   timeframes, plus single-timeframe frames. R1's five cells were MCL/MES/MGC/MNQ 1h (tfs 60,240)
   and MGC 5m (tfs 5,15,60). Where my number and R1's disagree, that is genuine independent
   evidence; where R1 measured nothing (MES and MCL for `multitimeframe` and `regime`; 30m; 1440m;
   single-timeframe frames), the number is new.
2. **`R4-M1`, `R4-M2`, `R4-M3`** — three structural findings absent from R1's file, two of which
   change what R1's own findings mean. Finding something the first auditor did not is the only
   available evidence that a second auditor is not merely agreeing.
3. **`R4-M4` onward** — where I disagree, I say so and quote the line.

A second reviewer who is told the first reviewer's answer is worth less than one who is not. I would
have preferred not to know. The honest mitigation is to make the disagreements and the additions
carry the weight, and to mark the agreements as what they are.

## One vocabulary addition, per `R1-REQ-5`: **VOID**

R1's six verdicts have no term for "cannot fire", and DEGRADED materially understates it. Adopting
the coordinator's term:

| verdict | meaning |
|---|---|
| **VOID** | the condition, or the configuration carrying it, **cannot fire by construction** — not rare, not weak, arithmetically impossible or structurally unreachable in the named cell |

VOID is always stated **per symbol and per timeframe**, never in general. It matters because
`Strategy.evaluate` is a strict AND with no `min_signals`: one non-firing FILTER returns `None`
before any signal is read, and one non-firing SIGNAL — or one that returns `Direction.NEUTRAL`, or
one that disagrees in direction — returns `None` too
`[repo-verified: futures_agents/strategies/base.py:670-684]`. So a single VOID member is not a weak
component, it is the whole strategy's zero.

---

# The census this file's verdicts rest on

`[measured: census.py, my own harness, 31 conditions × 47 cells, no backtest anywhere in it — no
entries, no exits, no P&L, no expectancy, no z]`

| cell family | cells | design |
|---|---|---|
| **corpus frames** | 23 | `tfs = FRAMES[primary]`, condition bound at `primary`, for `primary ∈ {5,15,30,60,240,1440}` × {MGC, MNQ, MES, MCL}. This is exactly what every published harness builds `[repo-verified: toolkit.py:157-161, bigscan/cell.py:86-90, chrono/ledger.py:37-40]`. MCL 1440 skipped: `csv/raw/` has no `MCL_1d.csv` |
| **frame-of-one** | 23 | `tfs = [primary]` — each timeframe strictly on its own, no higher timeframe to read |
| **one frame, three bindings** | 12 | `tfs = [5,15,60,240]` with the condition bound at 5, 60 and 240 — isolates timeframe-inertness from everything else |
| **extra groups** | 4 | `tfs = [1,5,15]` bound at 1m, per the dispatch's request for 1m+5m+15m |

`CONDITION_ERRORS` was **empty in all 47 cells** `[measured: reset_condition_errors() before each
cell, dict empty after → no cell hit the silent-exception path at base.py:129-147]`. So no verdict
below is the "raised on every bar and was recorded as a 0% trigger rate" failure that guard exists
to expose.

**Look-ahead / repainting, checked directly and not by inspection alone.** Prefix-invariance test:
rebuild the frame from `bars[:i+1]` only, evaluate every one of the 31 conditions at bar `i`, and
compare verdict **and direction** against the same bar evaluated inside the full series.

| cell | probes | result |
|---|---|---|
| MGC 60m, tfs [60,240,1440] | 8 | **all 31 prefix-invariant** |
| MNQ 5m, tfs [5,15,60] | 4 | **all 31 prefix-invariant** |
| MCL 60m, tfs [60,240,1440] | 4 | **all 31 prefix-invariant** |

`[measured: python3, build_symbol_frame on truncated vs full series, comparing (triggered, direction)]`
So none of my 31 conditions repaints and none reads a bar later than the one being evaluated. That is
a clean result and it is worth stating, because three of the four indicator families here (ADX,
Kaufman efficiency, the 20-bar regression slope) are ones where a naive implementation would.

---

# Group 1 — `trend` (8 conditions) → **CLEAN**

My reading of the arithmetic, from source, condition by condition:

| condition | kind | arithmetic | fire rate, 23 corpus cells | verdict |
|---|---|---|---|---|
| `ema_stack` | SIGNAL | `ema9 > ema21 > ema50` → LONG; reversed → SHORT `[repo-verified: library.py:112-122]` | 76–81% | **CLEAN** |
| `ema_fast_above_slow` | SIGNAL | `d = ema9 − ema21`, gated `abs(d) >= 0.10 × atr` `[repo-verified: library.py:125-133]` | 86–92% | **CLEAN** |
| `price_above_ema50` | SIGNAL | `d = close − ema50`, same 0.10 ATR deadband `[repo-verified: library.py:136-144]` | **92–96%** | **CLEAN** |
| `price_above_ema200` | SIGNAL | `d = close − ema200`, same deadband `[repo-verified: library.py:147-155]` | 84–95% | **CLEAN** |
| `adx_trending` | FILTER | `adx >= 22` `[repo-verified: library.py:158-168]` | 49–65% | **CLEAN** |
| `di_direction` | SIGNAL | `abs(+DI − −DI) >= 4`, sign gives direction `[repo-verified: library.py:171-182]` | 74–81% | **CLEAN** |
| `slope_directional` | SIGNAL | 20-bar regression slope / ATR, `abs(v) >= 0.05` `[repo-verified: library.py:185-195]` | 69–80% | **CLEAN** |
| `efficiency_high` | FILTER | Kaufman efficiency ratio `>= 0.35` `[repo-verified: library.py:198-208]` | **23–29%** | **CLEAN** |

Every name matches its arithmetic, every description matches its arithmetic, every condition reads
its own bound timeframe's feature row through `_s(snap, tf)`, and nothing in the group reads a
quantity from a different series. **No misnaming, no proxy, no degradation, VOID in no cell on any
symbol at any timeframe.** This is the cleanest group in my surface and it is required by 3 of 13
templates, which makes the clean verdict worth more than a broken one would be.

Two things worth recording that are *not* defects:

### R4-T1 — the base-rate spread inside a required group is 4.2×, not the 3.5× previously reported

Six of the eight fire on ≥ 49% of bars and two of those on ≥ 92%. `trend` is **required by TREND,
PULLBACK and FIBONACCI** and the combinator fills a required slot with **one** member drawn from the
6 SIGNALs (`adx_trending` and `efficiency_high` are FILTERs and cannot fill it —
`[repo-verified: combinator.py:361-369]`). So the required slot's selectivity ranges from
`price_above_ema50` at 92–96% to `ema_stack` at 76–81% among SIGNALs, and across the whole group
from `efficiency_high` at 23% to `price_above_ema50` at 96% — a **4.2× spread in base rate**.

Measured on 23 cells rather than 5, `di_direction` (74–81%) and `slope_directional` (69–80%) sit in
the same bias band as the four EMA conditions. A condition-level comparison inside `trend` is a
comparison of populations differing fourfold in size before any market question is asked.

The library says this about itself and is right to: `_deadband`'s docstring states these "are *bias*
conditions by nature and that is fine … inside a confluence that requires agreement they genuinely
gate" `[repo-verified: library.py:76-82]`. The point is only that a trade count from a TREND
strategy whose required condition is `price_above_ema50` carries essentially no information about
EMA50.

### R4-T2 — the deadband makes four of the eight silently non-firing whenever ATR is unavailable

`_deadband` returns `False` when `s.get("atr")` is falsy `[repo-verified: library.py:84-88]`, so
`ema_fast_above_slow`, `price_above_ema50`, `price_above_ema200` (and in `momentum`,
`macd_directional` and `macd_hist_direction`) return `no()` rather than raising or abstaining. A
SIGNAL returning `no()` returns the whole strategy to `None`
`[repo-verified: base.py:676-678]`. This is correct behaviour and the right direction to fail, but
it means **five of my 31 conditions are VOID on any bar where ATR is missing or zero**, which is
warm-up and any zero-range bar. It never appeared as an error in 47 cells, so its practical scope is
warm-up only. Recorded because "the deadband is what made it not fire" is invisible from a trade
count.

---

# Group 2 — `momentum` (6 conditions) → **MISNAMED**

Three separate problems. I reached the same two R1 did (declared anchor above) plus one it did not
state.

## R4-MO1 — `macd_directional` and `macd_hist_direction` are one condition with two names

By construction `macd_hist = macd_line − macd_signal`
`[repo-verified: futures_agents/indicators/core.py:198-199, hist = [a − b for a, b in zip(line, sig)]]`,
and the feature layer stores all three from one call `[repo-verified: features.py:233]`. Then:

- `macd_directional`: `d = s["macd"] − s["macd_signal"]`, gate `_deadband(s, d, 0.05)`, direction `sign(d)` `[repo-verified: library.py:240-249]`
- `macd_hist_direction`: `h = s["macd_hist"]`, gate `_deadband(s, h, 0.05)`, direction `sign(h)` `[repo-verified: library.py:252-260]`

Same number, same deadband fraction, same sign test. **Measured: the (fired, LONG, SHORT, FLAT)
vector is identical in all 23 corpus cells** — 4 symbols × 6 timeframes, 4132/4132 (MGC 5m) through
1127/1127 (MCL 240m) `[measured: census, exact vector equality, 23/23 cells]`. R1 measured 5 cells;
this extends it to every corpus timeframe on every symbol, including 30m, 240m and 1440m, which R1
did not cover.

**But the consequence R1 states for it is structurally impossible, and this is a CONTRADICTION.**
`R1_group_audit.md:396-399` writes: "any two-condition confluence that happened to draw **both**
MACD conditions was counting one reading twice and calling it agreement." It cannot happen.
`generate_combinations` draws **at most one condition per group**: required groups via
`itertools.product(*required)`, one entry per group, and optional groups via
`itertools.combinations(range(len(optional)), n_opt)` followed by `itertools.product(*(optional[g] …))`
— one condition per *distinct* group index `[repo-verified: combinator.py:536-546]`. And **no
template lists any group in both `required_groups` and `optional_groups`**
`[measured: python3, set(t.required_groups) & set(t.optional_groups) → empty for all 13]`. So two
`momentum` SIGNALs can never co-occur in one generated strategy.

Measured: **0 generated strategies carry both MACD conditions**, and 0 carry both `bollinger_extreme`
and `bollinger_mean_pull`, on all four symbols
`[measured: python3, generate_strategies(sym,[5,15,60,240],max_total=400) → MGC 314, MNQ 314, MES 336,
MCL 296 strategies; macd pair 0, bollinger pair 0 in every case]`.

**What the duplication actually costs is search-space inflation, and that is worse for this
programme than a false confluence would be.** The `momentum` required slot advertises 6 choices and
offers 5 distinct behaviours, so 1 in 6 MOMENTUM rule sets is a **byte-identical twin of another rule
set with a different `strategy_id`**. Two rows in any ranking can therefore be the same strategy
counted twice, with two ids, two entries in the denominator, and a correlation of exactly 1 that no
paired test can see. That lands directly on `BRIEF.md`'s `free_t` accounting and on `D48`'s
concern about exact-zero between-arm differences.

**The repo has a mechanism for exactly this and the pair is not in it.** `GLOBAL_EXCLUSIVE` exists
to bar "condition pairs that are the same statement wearing two names, enforced whatever template
draws them" and holds three pairs — `(value_area_breakout, prior_day_breakout)`,
`(stoch_extreme, keltner_outside)`, `(stoch_extreme, bollinger_mean_pull)`
`[repo-verified: combinator.py:390-398]`. **Neither of the two provable duplicates in my surface is
listed**: `(macd_directional, macd_hist_direction)`, identical by algebra and measured identical in
23/23 cells, and `(bollinger_extreme, bollinger_mean_pull)`, a strict algebraic subset. Its own
comment says entries need "a structural explanation" as the bar for entry — both of these have one,
and neither was added. Two of the three pairs that *are* listed involve my groups and are
cross-group, i.e. the cases `GLOBAL_EXCLUSIVE` can actually bite on; the two same-group cases it
omits are the two it cannot bite on anyway. The mechanism is therefore complete for its purpose and
**the duplication must be fixed by deleting a condition, not by an exclusion.**

## R4-MO2 — 2 of the 6 are mean-reversion conditions carrying the negation of the other 4's direction rule

| condition | direction rule | hypothesis |
|---|---|---|
| `rsi_directional` | `RSI > 53` → LONG, `< 47` → SHORT, `47..53` → no `[repo-verified: library.py:212-221]` | momentum |
| `macd_directional` / `macd_hist_direction` | `hist > 0` → LONG | momentum |
| `stoch_directional` | `%K > %D` by ≥ 2 → LONG `[repo-verified: library.py:263-272]` | momentum |
| **`rsi_extreme_reversal`** | **`RSI <= 30` → LONG, `>= 70` → SHORT** `[repo-verified: library.py:224-237]` | **mean reversion** |
| **`stoch_extreme`** | **`%K <= 20` → LONG, `>= 80` → SHORT** `[repo-verified: library.py:275-285]` | **mean reversion** |

On a bar with `RSI = 28`, `rsi_directional` returns **SHORT** and `rsi_extreme_reversal` returns
**LONG**, and both are `momentum`. `rsi_extreme_reversal`'s own description says
"mean-reversion trigger" `[repo-verified: library.py:225]` — honestly described, wrongly filed.
`stoch_extreme`'s description ("Stochastic below 20 / above 80") is silent on the direction it
assigns, which is worse: nothing warns a reader that it fades.

Measured firing mass, 23 cells: `rsi_extreme_reversal` 8–14%, `stoch_extreme` **35–54%**. The two
mean-reversion members are not a corner — `stoch_extreme` alone is the second most frequent member
of the group. `momentum` is **required by MOMENTUM** and the required slot takes one member, so a
strategy whose `momentum` condition is `stoch_extreme` is a fade published under MOMENTUM's heading.
And per `R4-M1`, MOMENTUM's other declared requirement (`volume`) is not enforced, so that strategy
is a pure fade with a `volatility_normal` filter and nothing else the template promised.

**GLOBAL_EXCLUSIVE confirms the library already knows `stoch_extreme` is a mean-reversion condition**
— it bars it against `keltner_outside` and `bollinger_mean_pull`, both in the `meanreversion` group,
on the stated ground that they are "both … price is stretched to an extreme in volatility units"
`[repo-verified: combinator.py:393-397]`. A condition whose declared near-duplicates are all in
`meanreversion` is in the wrong group.

## R4-MO3 — the group's two directional conditions have no independent content beyond MACD's sign

Not a defect; a fact needed to read the group's aggregate. `stoch_directional` fires 70–75% of bars
with a LONG share of **48.5–51.5%** in all 23 cells, and `macd_directional` 78–84% with a LONG share
of **46.6–52.7%** `[measured: census]`. Both are near-perfectly balanced coin-flips at high base
rate. `rsi_directional` is 79–85% at 44.5–72.9% LONG. So four of the six `momentum` SIGNALs are
high-base-rate bias conditions in exactly the sense `trend`'s docstring owns up to, and the group's
description does not.

**Per-condition verdicts:**

| condition | verdict |
|---|---|
| `rsi_directional` | **CLEAN** — description "RSI above/below 50", arithmetic is above 53 / below 47; the deadband is undocumented but names no wrong object |
| `macd_directional` | **CLEAN** |
| `macd_hist_direction` | **DEGRADED** — exact duplicate of `macd_directional`, zero independent content, 23/23 cells |
| `stoch_directional` | **CLEAN** |
| `rsi_extreme_reversal` | **MISNAMED (group)** — clean arithmetic, honest description, wrong group |
| `stoch_extreme` | **MISNAMED (group)** — clean arithmetic, description silent on the direction hypothesis |

**Group verdict: MISNAMED.** 4 distinct momentum conditions, 1 exact duplicate of one of them, 2
whose direction rule is momentum's negation.
