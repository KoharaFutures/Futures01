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

## R4-M3 — **the method correction**: R1's per-timeframe deadness tests bind conditions to timeframes the harness generates but never *runs*, and the frames it does run hold a worse defect *(heading amended — see Addendum A)*

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

---

# Group 3 — `meanreversion` (3 conditions) → **CLEAN**, with a nested pair

| condition | kind | arithmetic | fire rate, 23 cells | verdict |
|---|---|---|---|---|
| `bollinger_extreme` | SIGNAL | `close <= bb_lower` → LONG, `close >= bb_upper` → SHORT `[repo-verified: library.py:670-682]` | 10–14% | **CLEAN** |
| `bollinger_mean_pull` | SIGNAL | `bb_pctb <= 0.15` → LONG, `>= 0.85` → SHORT `[repo-verified: library.py:685-696]` | 32–39% | **CLEAN** |
| `keltner_outside` | SIGNAL | `close <= keltner_lower` → LONG, `>= keltner_upper` → SHORT `[repo-verified: library.py:699-709]` | 22–35% | **CLEAN** |

Name, description and arithmetic agree in all three. None is VOID in any of my 47 cells.

## R4-MR1 — `bollinger_extreme` is an algebraic strict subset of `bollinger_mean_pull`

`bb_pctb = (close − bb_lower) / (bb_upper − bb_lower)`
`[repo-verified: futures_agents/features.py:239-240]`. So `close <= bb_lower` ⟺ `bb_pctb <= 0`, and
`0 < 0.15`, so every `bollinger_extreme` firing satisfies `bollinger_mean_pull`'s gate **in the same
direction by construction**. Measured on 8 cells I chose independently of R1's:

| cell | `bollinger_extreme` | also `bollinger_mean_pull` | same direction | `keltner_outside` ∩ `bollinger_extreme`, same direction |
|---|---|---|---|---|
| MGC 60m | 601 | **601/601** | 601/601 | 78.9% |
| MGC 240m | 176 | **176/176** | 176/176 | 80.7% |
| MNQ 60m | 635 | **635/635** | 635/635 | 82.7% |
| MNQ 240m | 155 | **155/155** | 155/155 | 89.0% |
| MES 60m | 670 | **670/670** | 670/670 | 80.9% |
| MES 240m | 139 | **139/139** | 139/139 | 84.9% |
| MCL 60m | 686 | **686/686** | 686/686 | 76.7% |
| MCL 240m | 181 | **181/181** | 181/181 | 75.7% |

`[measured: python3 over csv/raw with tfs=FRAMES[tf], per-bar comparison of (triggered, direction)]`

The containment ratio is stable: `bollinger_extreme` is **28.5%–41.0% of `bollinger_mean_pull`'s
firings** across all 23 corpus cells `[measured: census]`. `meanreversion` is **required by PULLBACK,
REVERSAL and MEAN_REVERSION** — 3 of 13, joint-most-required with `trend` — and the required slot
takes one member. Two `meanreversion` SIGNALs cannot co-occur (see `R4-MO1`'s structural argument),
so this is not a double-count inside one strategy. It is a **variety claim about the search**: the
required slot of three templates offers 3 names spanning a nested family whose pairwise overlap is
76–89% (Keltner) and 100% (Bollinger, one-directionally), so its effective variety is nearer 1.5 than
3. Any condition-level ranking among the three compares overlapping populations, not alternatives.

**The library knows this and acted on it in one direction only.** `GLOBAL_EXCLUSIVE` bars
`(stoch_extreme, keltner_outside)` and `(stoch_extreme, bollinger_mean_pull)` on the stated ground
that "both are 'price is stretched to an extreme in volatility units'; the oscillator and the channel
disagree on almost nothing" `[repo-verified: combinator.py:393-397]` — while
`(bollinger_extreme, bollinger_mean_pull)`, a **provable** subset, is absent. Same asymmetry as
`R4-MO1`. Both omissions are harmless *for confluence* (same group, cannot co-occur) and harmful for
the denominator.

## Note on the group name

The arithmetic measures **location** — "price is stretched from its band". Reversion is the direction
*assignment*, which is a hypothesis, not an observable. The group therefore names a hypothesis, but it
does so transparently and each description states what it computes. **CLEAN.**

---

# Group 4 — `candlestick` (5 conditions) → **CLEAN**

| condition | kind | arithmetic | fire rate, 23 cells | verdict |
|---|---|---|---|---|
| `candle_reversal` | SIGNAL | `hammer`: `lower_wick/range >= 0.60 and body_fraction <= 0.35` → LONG; `shooting_star`: upper wick `>= 0.60`, body `<= 0.35` → SHORT `[repo-verified: indicators/candles.py:107-113; library.py:1392-1404]` | 14–20% | **CLEAN** |
| `candle_engulfing` | SIGNAL | `body_abs > prev.body_abs`, opposite sign, and `close >= prev.open and open <= prev.close` `[repo-verified: candles.py:120-130]` | 7–18% | **CLEAN** |
| `candle_decisive_close` | SIGNAL | `marubozu`: `body_fraction >= 0.85`, direction `bar.is_up` `[repo-verified: candles.py:103-106]` | 5–16% | **CLEAN** |
| `candle_close_strength` | SIGNAL | `abs(close_location_value) >= 0.6`, LONG if positive `[repo-verified: library.py:1435-1449]` | 40–51% | **CLEAN** |
| `inside_bar_compression` | FILTER | `high <= prev.high and low >= prev.low` `[repo-verified: candles.py:133-137]` | 12–20% | **CLEAN** |

Every name, description and arithmetic agree. I checked the two definitions most often got wrong:
**engulfing is body-engulfing** (`close >= prev.open and open <= prev.close`), which is the standard
definition and not the looser range-engulfing; and **`candle_reversal` is geometrically a pin bar** —
a 60% lower wick with a ≤35% body leaves at most 5% upper wick, so the body necessarily "sits
opposite" as the description claims. No condition in the group is VOID in any of my 47 cells; the
thinnest is `candle_decisive_close` at 69 fires on MGC 240m, which is above `toolkit.FLOOR = 20` but
is a small-sample cell and should be reported as one.

**Required by:** nothing. Optional signal in TREND, REVERSAL, LIQUIDITY, SUPPLY_DEMAND;
`inside_bar_compression` is an optional filter in SUPPLY_DEMAND `[measured: TEMPLATES]`. So a
misnaming here would have been a footnote. There is none.

## R4-C1 — the CLV duplication is a *reachable* false confluence, unlike the MACD one

`candle_close_strength` computes `close_location_value(bar) = ((C−L) − (H−C)) / range`
`[repo-verified: indicators/candles.py:51-61]`, and `Bar.estimated_delta()` is the same quantity
times volume `[repo-verified: data/bars.py:106-117]` — which is the arithmetic under the `orderflow`
group. R1 recorded this as `C-1` and I agree with the reading.

**What I add is that this pair can actually co-occur, and the MACD pair cannot.**
`candlestick` and `orderflow` are *different* optional groups in TREND, REVERSAL, LIQUIDITY and
SUPPLY_DEMAND, so `itertools.combinations` over distinct group indices permits both
`[repo-verified: combinator.py:539-546]`. Measured, one template at a time with the full budget:

| template | strategies | `candle_close_strength` + `delta_confirms_bar` | + `cvd_directional` |
|---|---|---|---|
| REVERSAL | 336 | **8** | **8** |
| LIQUIDITY | 328 | **4** | **16** |
| TREND / SUPPLY_DEMAND / MOMENTUM | 366 / 360 / 365 | 0 | 0 |

`[measured: python3, generate_strategies('MCL',[5,15,60,240],max_total=400,groups=[one template])]`

Neither pair is in `GLOBAL_EXCLUSIVE` `[repo-verified: combinator.py:390-398 — it holds exactly three
pairs, none of them these]`. So **the failure mode R1 attributed to the MACD duplicate — "counting
one reading twice and calling it agreement" — is real, and it lives here and in `orderflow`, not in
`momentum`.** A REVERSAL strategy carrying `candle_close_strength` and `delta_confirms_bar` requires
two signals that R1 measured co-firing on 92–93% of the former's firings
`[repo-verified: R1_group_audit.md:149-155]`, filed under two group names, one of which claims
participant information. That is exactly what `GLOBAL_EXCLUSIVE` was built for and it is not in it.

## R4-C2 — two detected patterns have no consumer

`classify_candle` detects `doji` (`body_fraction <= 0.10`) and `outside_bar` and **no condition reads
either** `[repo-verified: candles.py:100-102, 139-145]`
`[measured: grep -c 'doji\|outside_bar' futures_agents/strategies/library.py → 0]`. `outside_bar` is
the only pattern needing the 20-bar average range, so `_avg_range` is computed on every bar for a
pattern nothing consumes. Dead code in the indicator, not a misnamed condition — recorded so the
group's coverage is not overstated at 7 patterns when 5 are reachable. (R1 recorded the same as
`C-2`; I reproduce the grep because it is one command and confirms the reading.)

---

# Group 5 — `volatility` (3 conditions) → **MISNAMED**, and it is the base filter of 13 of 13 templates

This group has the widest reach in the library: `volatility_normal` is a base filter in 12 of 13
templates and `volatility_compressed` is BREAKOUT's `[measured: TEMPLATES]`. A base filter is
unconditional. So **every strategy in the corpus carries a member of this group in a slot it did not
choose**, and all three members are FILTERs — the group has 0 SIGNALs
`[measured: CONDITION_GROUPS + CONDITIONS[n].kind]`.

## R4-V1 — `volatility_compressed` names Bollinger width, reads ATR percentile, and the two diverge more at 4h than at 1h

```
library.py:735-743
@condition("volatility_compressed", "volatility", kind=ConditionKind.FILTER,
           description="Bollinger width in the bottom quartile - coiled")
def _vol_comp(snap, tf):
    s = _s(snap, tf)
    ...
    p = s["atr_percentile"]                  # <- not Bollinger width
    return yes(...) if p <= 0.30 else no()   # <- not a quartile
```

`[repo-verified: futures_agents/strategies/library.py:735-743]`

The described field **exists and is reachable**: `RegimeSnapshot.bb_width_percentile`
`[repo-verified: indicators/regime.py:39]` is computed from `bollinger(closes, 20)` widths over a
250-bar lookback `[repo-verified: regime.py:182-191]` and is available as
`snap.regime.bb_width_percentile`. The condition reads a different quantity. Measured on the same
bars, on all four symbols and at two timeframes:

| cell | n | corr(atr_pct, bb_width_pct) | "bottom 30%" verdict **disagrees** | `P(bb ≤ .3)` vs `P(atr ≤ .3)` |
|---|---|---|---|---|
| MGC 60m | 4,941 | 0.508 | **1,471 = 29.8%** | 32.8% vs 35.6% |
| MNQ 60m | 4,941 | 0.520 | **1,362 = 27.6%** | 32.1% vs 34.1% |
| MES 60m | 4,941 | 0.576 | **1,198 = 24.2%** | 32.7% vs 34.9% |
| MCL 60m | 4,941 | 0.514 | **1,393 = 28.2%** | 29.4% vs 34.5% |
| MGC 240m | 1,051 | 0.692 | 220 = 20.9% | 24.4% vs 33.3% |
| **MNQ 240m** | 1,051 | **−0.060** | **388 = 36.9%** | 22.7% vs 27.3% |
| **MES 240m** | 1,051 | **−0.102** | **511 = 48.6%** | 28.0% vs 31.7% |
| **MCL 240m** | 1,086 | 0.415 | **455 = 41.9%** | **2.3% vs 41.3%** |

`[measured: python3 over csv/raw with tfs=FRAMES[tf], TFSnapshot["atr_percentile"] vs snap.regime.bb_width_percentile, Pearson corr on the paired series]`

**The 60m row is the clean measurement of the misnaming**, because at 60m the frame is
`[60,240,1440]` and `regime_tf = 60`, so both percentiles are computed on the *same* series and the
only difference is which quantity. On roughly one bar in four, BREAKOUT's unconditional base filter
gives the opposite answer to the one its own description promises. This reproduces R1's 27.5–29.9%
on three symbols and extends it to MCL — **CONFIRMED.**

**The 240m row is a second defect stacked on the first, and it is mine.** At 240m,
`regime_tf = 1440` (`R4-M3`), so `bb_width_percentile` is a *daily* quantity while `atr_percentile`
is a 4-hour one. The correlation collapses to **−0.060 (MNQ) and −0.102 (MES)** — the two are
uncorrelated to faintly anti-correlated — and the verdict disagrees on **36.9% to 48.6%** of bars.
On **MCL at 240m the described field would fire on 2.3% of bars and the field actually read fires on
41.3% — an 18× difference.** So the size of the misnaming is a per-symbol, per-timeframe quantity
ranging from "one bar in four" to "almost every bar", and nobody could have known that from the
1-hour measurement alone. **Every symbol is its own universe, and so is every timeframe.**

`volatility_expanding` carries the milder half: "ATR in the **top quartile** of its own history" with
a threshold of `p >= 0.70`, which is the top 30% `[repo-verified: library.py:724-732]`. Right field,
wrong quantile name. Measured pass rate 26–40%, consistent with a 30% cut plus volatility clustering.

## R4-V2 — `volatility_compressed` AND `volatility_expanding` is empty by arithmetic, and BREAKOUT generates it

Both read `s["atr_percentile"]` through `_s(snap, tf)` with the same `tf`
`[repo-verified: library.py:727-731, 738-742]`, so the conjunction is `p <= 0.30 AND p >= 0.70` —
**empty on every bar, every symbol, every timeframe, for any binding.** This does not depend on the
measured `Condition.timeframe`; it follows from both conditions resolving the same row.

`volatility_compressed` is in BREAKOUT's `base_filters` and `volatility_expanding` in its
`optional_filters` `[repo-verified: combinator.py:272-274]`, and `_filter_sets` emits
`base + (f,)` for **each** optional filter `[repo-verified: combinator.py:447-456]`. A base filter is
unconditional. So **every BREAKOUT strategy that draws `volatility_expanding` is VOID.**

| path | BREAKOUT generated | VOID via `volatility_expanding` | VOID via `oi_expanding` | total VOID |
|---|---|---|---|---|
| default profile | 60 | 10 | 10 | **20 / 60 = 33.3%** |
| `groups=ALL_GROUPS` (the corpus) | **84** | **14** | **14** | **28 / 84 = 33.3%** |

`[measured: python3, generate_strategies(sym,[5,15,60,240],max_total=400), four symbols, both paths]`

**Verdict VOID**, per `R1-REQ-5`'s new term, not DEGRADED: these strategies cannot take a trade, and
`Strategy.evaluate` returns `None` at the first non-firing filter before a signal is read
`[repo-verified: base.py:670-674]`. This is the same shape as `openinterest` and it is a second,
independent cause. R1's D-V2 found it; my contribution is that it holds on **all four symbols** in
the corpus's own generation path, not two (`R4-M2`).

## R4-V3 — `volatility_normal` is measured on a different series from its own group-mates, and at 240m a quarter of its passes are a dataclass default

`volatility_normal` reads `snap.regime.volatility` `[repo-verified: library.py:716-721]` — the
frame's **regime timeframe** — while the other two read `s["atr_percentile"]` on the **strategy's
own** timeframe. Two ATR percentiles, two series, one group. It therefore inherits `R4-M3` in full.

The part that is new and that the 1-hour cells hide: `regime_at` returns a **default
`RegimeSnapshot()`** when the regime timeframe has fewer than 60 bars
`[repo-verified: features.py:935-943]`, and that default has `volatility = "NORMAL"` and
`regime = "UNKNOWN"` `[repo-verified: regime.py:30-31]`. `volatility_normal` accepts LOW/NORMAL/HIGH,
so **it passes on the default**. At the 240m row the regime timeframe is 1440, and 60 daily bars take
~360 of the 240m bars to accumulate:

| cell | regime_tf | bars with `regime == "UNKNOWN"` (the default) | `volatility_normal` passes | **of which are the default** |
|---|---|---|---|---|
| MGC 60m | 60 | 59 = 1.2% | 3,988 = 79.8% | 59 = 1.5% |
| MNQ 60m | 60 | 59 = 1.2% | 3,971 = 79.4% | 59 = 1.5% |
| MES 60m | 60 | 59 = 1.2% | 3,933 = 78.7% | 59 = 1.5% |
| MCL 60m | 60 | 59 = 1.2% | 3,959 = 79.2% | 59 = 1.5% |
| **MGC 240m** | **1440** | **297 = 22.0%** | 1,286 = **95.4%** | **297 = 23.1%** |
| **MNQ 240m** | **1440** | **296 = 22.0%** | 1,257 = **93.3%** | **296 = 23.5%** |
| **MES 240m** | **1440** | **296 = 22.0%** | 1,259 = **93.5%** | **296 = 23.5%** |
| **MCL 240m** | **1440** | **298 = 21.5%** | 1,103 = 79.7% | **298 = 27.0%** |
| MGC 1440m | 7200 | 62 = 2.5% | 2,077 = 82.7% | 62 = 3.0% |
| MNQ / MES 1440m | 7200 | 63 = 3.4% | 1,466 / 1,461 = 78.9% / 78.6% | 63 = 4.3% |

`[measured: census + python3 over csv/raw, snap.regime.regime and volatility_normal per bar]`

Three things follow, and the third is the one that changes how a 4-hour result reads:

1. **The base filter of 12 of 13 templates has a 14-point higher pass rate at 240m than at 60m on
   three of four symbols** (79% → 93–95%) and *not* on the fourth (MCL, 79.2% → 79.7%). That is a
   per-symbol fact with no market content: it is the daily-regime warm-up.
2. **On 22% of 240m bars, the three regime-derived base filters contradict each other.**
   `volatility_normal` passes on `volatility = "NORMAL"` (default) while `regime_trending` and
   `regime_ranging` both fail on `regime = "UNKNOWN"` (default) — so a TREND or MEAN_REVERSION
   strategy is vetoed on exactly the bars where the 12-of-13 filter waves through. The library's own
   stated principle is that a filter whose question does not apply must pass
   `[repo-verified: library.py:855-860]`; three conditions reading the same dataclass implement two
   different answers to that principle, and neither by design.
3. **~23–27% of every 4-hour strategy's `volatility_normal` passes are not a volatility measurement
   at all.** They are the string `"NORMAL"` from `RegimeSnapshot`'s field default.

| condition | kind | verdict |
|---|---|---|
| `volatility_normal` | FILTER | **DEGRADED** — timeframe-inert, frame-dependent, and 23–27% of its 240m passes are a dataclass default |
| `volatility_expanding` | FILTER | **MISNAMED (mild)** — "top quartile" is `p >= 0.70`; **and VOID in conjunction with BREAKOUT's base filter**, 14 of 84 generated BREAKOUT strategies |
| `volatility_compressed` | FILTER | **MISNAMED** — names Bollinger width, reads ATR percentile; verdicts disagree 24–30% at 60m and **37–49% at 240m**; base filter of BREAKOUT |

**Group verdict: MISNAMED**, with one VOID conjunction the combinator emits.

---

# Group 6 — `regime` (3 conditions) → **DEGRADED**, with a directional VOID on the index micros at 4h

## R4-R1 — all three accept `tf` and none reads it

```
library.py:749-754   def _reg_trend(snap, tf):  r = snap.regime.regime      # tf never referenced
library.py:757-762   def _reg_range(snap, tf):  r = snap.regime.regime      # tf never referenced
library.py:765-774   def _reg_dir(snap, tf):    r = snap.regime.regime      # tf never referenced
```

`[repo-verified: futures_agents/strategies/library.py:749-774 — the parameter is named `tf` in all
three and appears in none of the three bodies]`

`snap.regime` is `regime_at(base_index)`, which reads `self.regime_tf` — **one timeframe chosen for
the whole frame** `[repo-verified: features.py:928-943]` by `_default_regime_tf`'s preference list
`(15, 30, 5, 60, 10, 3, 1)` with a fallthrough to `self.timeframes[-1]`
`[repo-verified: features.py:820-826]`.

Measured directly, holding the frame fixed at `[5,15,60,240]` and varying **only** the binding:

| symbol | bind=5 | bind=60 | bind=240 |
|---|---|---|---|
| MGC `regime_trending` | 981 | 981 | 981 |
| MGC `regime_ranging` | 3,297 | 3,297 | 3,297 |
| MGC `regime_matches_direction` | 981 | 981 | 981 |
| MNQ | 1,246 / 2,804 / 1,246 | identical | identical |
| MES | 1,097 / 2,913 / 1,097 | identical | identical |
| MCL | 1,076 / 2,996 / 1,076 | identical | identical |

`[measured: census, 12 cells — one series, one frame, three bindings, four symbols; counts
bit-identical across bindings in all 12]`

**The binding is fully inert for this group**, which is a stronger statement than I could make for
`volatility_normal` (whose counts differ by 11–35 bars across bindings, entirely because
`Condition.evaluate` returns `no()` when `snap.tf(tf) is None`
`[repo-verified: base.py:125-126]` and `volatility_normal` can fire from bar 0 while
`regime_trending` cannot fire until the regime has 60 bars).

Which series the regime is read off in the corpus is `R4-M3`'s table: on-timeframe at 15m/30m/60m,
3× coarser at 5m, **the daily series at 240m**, and the mislabelled daily copy at 1440m. So R1's
D-R1 is confirmed as a defect and **its illustrative direction is wrong for the corpus** — the error
is coarser-not-finer at the rows where it exists, and absent at three of six rows.

## R4-R2 — `regime_matches_direction` adds no gate over `regime_trending`, and 26% of TREND strategies carry both

Both gate on `regime in ("TREND_UP", "TREND_DOWN")` `[repo-verified: library.py:752-754, 767-773]`.
Measured: **identical fire counts in all 23 corpus cells** `[measured: census, 23/23]`. The only
difference is that `regime_trending` returns `FLAT` and `regime_matches_direction` returns LONG/SHORT.

**And unlike the MACD pair, this co-occurrence is reachable and common**, because one is a base
FILTER and the other a SIGNAL, so the one-per-group rule does not separate them:

| template | strategies generated | carrying `regime_matches_direction` **and** `regime_trending` |
|---|---|---|
| TREND | 366 | **96 = 26.2%** |

`[measured: python3, generate_strategies('MCL',[5,15,60,240],max_total=400,groups=['TREND'])]`

TREND has `regime_trending` in `base_filters` and `regime` in `optional_groups`
`[repo-verified: combinator.py:170-176]`. So in 26% of TREND strategies one of the three optional
signal slots is spent on a condition whose gate the base filter has **already applied**, contributing
only a direction vote while appearing in the strategy's identity as a distinct confluence member. Any
confluence count on those strategies is one higher than the number of independent readings made.
`GLOBAL_EXCLUSIVE` does not list the pair `[repo-verified: combinator.py:390-398]`.

## R4-R3 — `regime_matches_direction` is directionally VOID on MES at 240m, and near-VOID on MNQ

This is the finding I would not have got without testing per symbol *and* per timeframe, and it is
not in R1's file.

| cell | fires | LONG | **LONG share** |
|---|---|---|---|
| **MES 240m** | 188 | **188** | **100.0%** |
| **MNQ 240m** | 206 | 194 | **94.2%** |
| MES 1440m | 284 | 252 | 88.7% |
| MNQ 1440m | 270 | 234 | 86.7% |
| MGC 1440m | 467 | 325 | 69.6% |
| MGC 240m | 209 | 91 | 43.5% |
| MCL 240m | 152 | 87 | 57.2% |
| all 5m/15m/30m/60m cells | 387–1,246 | — | 45.5–64.7% |

`[measured: census, 23 corpus cells, LONG/SHORT split recorded per cell]`

**On MES at 240m this SIGNAL can only ever say LONG.** Not "mostly" — 188 of 188. The mechanism is
`R4-M3`: at 240m the regime is read off the **daily** series, and over this `csv/raw` window the
daily index-complex regime is `TREND_UP` on every bar it is trending at all. `Strategy.evaluate`
requires every signal to agree on direction and returns `None` otherwise
`[repo-verified: base.py:676-684]`, so:

> **A MES 240m TREND or MOMENTUM strategy carrying `regime_matches_direction` cannot take a short.**
> Its `allowed_directions` include SHORT `[repo-verified: combinator.py TEMPLATES → directions]`, its
> generated identity says LONG and SHORT, and its SHORT arm is **VOID**.

It is per-symbol: MGC at the same timeframe is 43.5% LONG and MCL 57.2%. It is per-timeframe: MES at
60m is 61.0%. And it is the index complex specifically, which `BRIEF.md` already warns is one
correlated family — so MES and MNQ agreeing here is **not** corroboration, it is the same fact twice.
**Verdict: VOID on the SHORT half, MES 240m; DEGRADED-toward-VOID, MNQ 240m and both at 1440m.**

## R4-R4 — `regime_ranging`'s pass rate falls 11 points at 240m for a warm-up reason

62–66% at 5m/15m/30m/60m → **50–52% at 240m on all four symbols** `[measured: census]`. The cause is
`R4-V3`: on 21.5–22.0% of 240m bars the regime is the default `"UNKNOWN"`, which `regime_ranging`
correctly refuses. `regime_ranging` is a **base filter in MEAN_REVERSION**, so every
MEAN_REVERSION strategy at 4h is vetoed on a fifth of its bars by daily-regime warm-up. R1 measured a
13-point swing from changing the frame's timeframe list; this is a different 11-point swing from
changing the *timeframe row*, and both are invisible in any report.

| condition | kind | verdict |
|---|---|---|
| `regime_trending` | FILTER | **DEGRADED** — timeframe-inert (measured bit-identical across 3 bindings), reads the frame's `regime_tf` |
| `regime_ranging` | FILTER | **DEGRADED** — same, plus an 11-point pass-rate drop at 240m from daily-regime warm-up |
| `regime_matches_direction` | SIGNAL | **DEGRADED** — no gate beyond `regime_trending`, co-occurs with it in 26% of TREND strategies; **VOID on the SHORT half at MES 240m** |

The *arithmetic* of all three faithfully reports what `classify_regime` returned, and each
description says "Regime classifier says …", which is honest. The degradation is entirely in **which
series the classifier ran on** — invisible at the call site, not chosen by the strategy, and not
recorded in any report.

---

# Group 7 — `multitimeframe` (3 conditions) → **DEGRADED**, **VOID in a frame of one**, and **contentless at the two highest corpus rows**

This is where my verdicts diverge most from R1's, and the divergence is about **which configuration**
is broken rather than whether one is.

## R4-MT1 — neither signal is VOID in any frame the corpus builds; both are VOID in a frame of one

`agreeing_timeframes(from_tf=tf)` counts only timeframes at or above `tf`, **and only those whose
`structure_trend` is UPTREND or DOWNTREND** — `if v: votes.append(v)`
`[repo-verified: futures_agents/features.py:752-770]`. Both signals return `no()` when `voting < 2`
`[repo-verified: library.py:793-800, 822-824]`.

Measured at the corpus's own bindings (`tfs = FRAMES[primary]`, bound at `primary`), all four symbols:

| symbol | 5m | 15m | 30m | 60m | 240m | 1440m |
|---|---|---|---|---|---|---|
| MGC `mtf_aligned` | 1,415 | 1,309 | 683 | 1,785 | **303** | 1,153 |
| MNQ | 1,606 | 1,397 | 736 | 1,365 | **201** | 908 |
| MES | 1,338 | 879 | 540 | 1,517 | **284** | 976 |
| MCL | 1,791 | 1,442 | 783 | 1,703 | **316** | — |

`[measured: census, 23 corpus cells]`

**Not one zero.** *(Amended — see Addendum A: the configuration IS generated, 48 carriers; it is never run. What follows overstates the correction and Addendum A is the settled version.)* R1's D-MTF1 states that "a MULTI_TIMEFRAME strategy whose primary timeframe is the
top of its frame can never emit a signal — it is a structurally zero-trade strategy, exactly the shape
of round 1's `openinterest` finding" `[repo-verified: R1_group_audit.md:480-486]`. **I disagree that
this describes anything in the corpus**, for the reason in `R4-M3`: `FRAMES` always appends higher
timeframes to the primary, and every harness filters on `s.primary_tf == tf`, so no generated strategy
is ever bound to the top of its own frame. R1 measured `build_symbol_frame(5m, [5,15,60,240])` bound
at `tf=240`, and I reproduce its zeros exactly in that configuration (0 at bind=240 on all four
symbols, `[measured: census, 12 "one frame three bindings" cells]`) — the arithmetic is right and the
configuration is not one that occurs. **CONTRADICTED as to blast radius; CONFIRMED as to mechanism.**

**The configuration that *is* VOID is a frame of one, and it is VOID on every symbol and every
timeframe:**

| cell family | `mtf_aligned` | `mtf_strongly_aligned` | `mtf_not_conflicted` |
|---|---|---|---|
| `tfs = [tf]`, 23 cells (4 symbols × {5,15,30,60,240,1440}) | **0 / N in all 23** | **0 / N in all 23** | **100.0% in all 23** |

`[measured: census, 23 frame-of-one cells: MGC/MNQ/MES/MCL at 5m, 15m, 30m, 60m, 240m, 1440m]`

So `multitimeframe` is **VOID** in a single-timeframe frame, and since `multitimeframe` is required by
MULTI_TIMEFRAME and `mtf_aligned`/`mtf_strongly_aligned` are its **only** SIGNALs
`[measured: CONDITION_GROUPS, 2 of 3 are SIGNAL]`, **MULTI_TIMEFRAME is a structurally zero-trade
template in any single-timeframe frame.** And `mtf_not_conflicted` — PULLBACK's base filter — becomes
literally unconditional there, because one timeframe cannot hold both UPTREND and DOWNTREND.

**Is that reachable?** `TIMEFRAMES = (1, 2, 3, 5, 10, 15, 30, 60, 120, 240, 1440)` but `FRAMES` has
only `{5, 15, 30, 60, 240, 1440}` `[repo-verified: config.py:302, scout.py:58-67]`, and `scout.rank`
resolves its frame as `FRAMES.get(timeframe, [timeframe])` `[repo-verified: scout.py:230-233]` — the
fallback is a frame of one for 1m, 2m, 3m, 10m and 120m. **That particular branch is unreachable**,
because `scout.rank`'s `suffix` dict covers only `{1440, 240, 60, 15, 5}` and raises `KeyError` first
`[repo-verified: scout.py:219]` — note it does not even cover 30m, which *is* a `FRAMES` key. The
same `FRAMES.get(tf, [tf])` fallback appears a second time, in `scout.live_state`
`[repo-verified: scout.py:348-351]`, and is unreachable for the same reason: an identical `suffix` dict
raises first.

**Corrected count, and the error was mine.** An earlier draft of this paragraph said "40 call sites,
all but three pass `FRAMES[tf]`". Both figures were wrong: my `grep` was truncated by `head -40`, and my
pattern matched `[tf]` *inside* `FRAMES[tf]`. The accurate measurement is **83 `build_symbol_frame` call
sites** outside the definition, of which **five** build a frame of one:
`backtest/BT2/code/test_algo1.py:58` (`[tf]`) and `:136` (`[TF]`), both unit tests;
`newstrats/leadlag.py:131` (`sorted({base, tf})` with `base = 60 if tf >= 60 else tf`, so a frame of one
at tf in {5, 15, 30, 60} — but it reads `structure_trend` directly and runs no strategy); and the two
unreachable `scout.py` fallbacks. **Every other site passes `FRAMES[...]` or an explicit multi-element
list**
`[measured: grep -rn "build_symbol_frame(" --include=*.py . | grep -v "def build_symbol_frame" | wc -l
→ 83, then inspecting the frame argument of all 83]`. So the frame-of-one VOID has **not** contaminated
any published result. It is a live hazard with no guard, and stating it as VOID-per-cell is the useful
form.

**One aside that reinforces it:** `csv/raw` contains no `*_4h.csv`
`[measured: ls csv/raw/ | grep -c _4h → 0]`, while both `scout.rank` and `scout.live_state` map
`240 → "4h"` `[repo-verified: scout.py:219, 348]`. So the shipped `scout` module cannot be run at 240m
on this data store at all — a third independent reason its frame-of-one fallback has never executed.

## R4-MT2 — `mtf_strongly_aligned` has zero independent content at 240m and 1440m, and it is provable

| cell | `mtf_aligned` | `mtf_strongly_aligned` | aligned-not-strong | strong-not-aligned |
|---|---|---|---|---|
| MGC 5m [5,15,60] | 1,415 | 1,213 | 202 | **0** |
| MGC 15m | 1,309 | 1,064 | 245 | **0** |
| MGC 30m | 683 | 629 | 54 | **0** |
| MGC 60m [60,240,1440] | 1,785 | 1,471 | 314 | **0** |
| **MGC 240m [240,1440]** | **303** | **303** | **0** | **0** |
| **MGC 1440m [1440,7200]** | **1,153** | **1,153** | **0** | **0** |
| **MNQ 240m / 1440m** | 201 / 908 | **201 / 908** | 0 / 0 | 0 / 0 |
| **MES 240m / 1440m** | 284 / 976 | **284 / 976** | 0 / 0 | 0 / 0 |
| **MCL 240m** | 316 | **316** | 0 | 0 |

`[measured: python3 over csv/raw, both conditions evaluated at every bar of every corpus frame, four symbols]`

At the two highest corpus rows the two conditions are **identical on 100% of bars, on every symbol.**
With exactly two timeframes voting, "at least a 0.4 weighted majority" and "unanimous among the
voters" are the same statement: two agreeing voters give `|a| = sum(w_agree)/sum(w_all) ≥ 0.569` in
every corpus frame, and two disagreeing voters give `|a| ≤ 0.14`. So the split is structural, not a
sampling result. The docstring's stated purpose — "needs a condition that can tell three-of-three from
two-of-three" `[repo-verified: library.py:812-819]` — **is unreachable wherever fewer than three
timeframes vote**, which is every 240m and 1440m strategy in the corpus.

I also checked the opposite direction, because `alignment()` and `agreeing_timeframes()` use
**different denominators** — `agreeing_timeframes` excludes non-directional timeframes from `voting`
while `alignment` keeps them in `den` `[repo-verified: features.py:742-750 vs :760-770]` — which
could in principle let `mtf_strongly_aligned` fire where `mtf_aligned` does not. **It never does:
strong-not-aligned = 0 in all 23 corpus cells**, and the log-weights make it impossible in these
frames. A check that came back clean.

## R4-MT3 — `mtf_strongly_aligned`'s description is false on 3 of 4 of its firings

New, and a consequence of the same denominator asymmetry. The description is "**Every** timeframe from
this one up agrees - maximum linkage" `[repo-verified: library.py:810-811]`. The arithmetic requires
`agree == voting`, and `voting` **excludes every timeframe whose `structure_trend` is not UPTREND or
DOWNTREND** `[repo-verified: features.py:764-766]`. So it fires when every *trending* timeframe agrees,
ignoring the flat ones entirely.

| cell | `mtf_strongly_aligned` fires | **of which ≥1 timeframe ≥ primary is NOT directional** |
|---|---|---|
| MGC 5m | 1,213 | **1,020 = 84.1%** |
| MGC 15m | 1,064 | **848 = 79.7%** |
| MGC 30m | 629 | **408 = 64.9%** |
| MGC 60m | 1,471 | **1,097 = 74.6%** |
| MNQ 5m / 15m / 30m / 60m | 1,429 / 1,168 / 663 / 1,114 | 1,167 / 914 / 458 / 890 = **81.7 / 78.3 / 69.1 / 79.9%** |
| MES 5m / 15m / 30m / 60m | 1,183 / 750 / 513 / 1,269 | 990 / 659 / 416 / 920 = **83.7 / 87.9 / 81.1 / 72.5%** |
| MCL 5m / 15m / 30m / 60m | 1,620 / 1,149 / 741 / 1,470 | 1,176 / 834 / 526 / 1,102 = **72.6 / 72.6 / 71.0 / 75.0%** |
| all 240m and 1440m cells | 201–1,153 | **0** (only two timeframes, both must vote to reach `voting ≥ 2`) |

`[measured: python3, per bar comparing agreeing_timeframes(from_tf) against the count of timeframes ≥ from_tf whose structure_trend is directional]`

So at 5m, 15m, 30m and 60m — **four of the six corpus rows, on all four symbols — between 65% and 88%
of "every timeframe agrees" firings occur with at least one timeframe not agreeing.** It is not
wrong arithmetic; it is a description that promises unanimity over the frame and delivers unanimity
over a subset the reader cannot see. **MISNAMED**, and materially: this is the condition that exists
specifically to grade linkage strength, and its grade ignores the abstentions.

## R4-MT4 — `mtf_not_conflicted` ignores `tf`, and at 1440m it vetoes nothing at all

```
library.py:834-841
def _mtf_ok(snap, tf):
    trends = {s.structure_trend for s in snap.tfs.values()}
    conflicted = "UPTREND" in trends and "DOWNTREND" in trends
```

`tf` is accepted and never read; `snap.tfs.values()` is **every** timeframe in the frame
`[repo-verified: futures_agents/strategies/library.py:834-841]`. Measured across three bindings of one
fixed frame `[5,15,60,240]`: 2,739 / 2,763 / 2,774 (MGC), 2,978 / 2,978 / 2,979 (MNQ), 2,347 / 2,347 /
2,349 (MES), 2,758 / 2,794 / 2,794 (MCL) `[measured: census, 12 cells]`. The residual 0–35-bar spread
is **not** a timeframe effect — it is `Condition.evaluate` returning `no()` on bars where the bound
timeframe has no completed bar yet `[repo-verified: base.py:125-126]`, which is 12 base bars at
bind=60 and 48 at bind=240 on a 5m base. **Timeframe-inert. CONFIRMED** — and this is the defect
`mtf_aligned`'s own docstring records as found and fixed for the two signals via `from_tf=tf`; the
filter never got it `[repo-verified: library.py:784-791]`.

**And its pass rate is a property of the frame, which is what makes it a confound on a whole
template.** `mtf_not_conflicted` is PULLBACK's **base filter** `[repo-verified: combinator.py:185]` —
unconditional on every PULLBACK strategy:

| frame | MGC | MNQ | MES | MCL |
|---|---|---|---|---|
| [5] and every other frame of one | **100.0%** | 100.0% | 100.0% | 100.0% |
| [5,15,60] @5m | 70.6% | 66.6% | 65.7% | 63.5% |
| [15,60,240] @15m | 64.3% | 67.5% | 62.3% | 70.6% |
| [60,240,1440] @60m | 62.6% | 59.3% | 64.4% | 69.0% |
| [5,15,60,240] @5m | 55.5% | 59.6% | 47.0% | 55.9% |
| [240,1440] @240m | 79.6% | 84.8% | 81.2% | 82.9% |
| **[1440,7200] @1440m** | **99.1%** | **99.3%** | **99.6%** | — |
| [1,5,15] @1m | 60.2% | 65.7% | 66.8% | 65.1% |

`[measured: census, 47 cells]`

The pass rate ranges from **47.0% to 100%** on the same conditionless question, purely as a function of
how many timeframes the runner put in the frame. Adding a timeframe adds another chance of an
UPTREND/DOWNTREND pair. So the strictness of PULLBACK's unconditional veto is set by the harness, not
by the strategy, and no report records which frame was used. **CONFIRMED**, with two additions:

1. **At 1440m it passes 99.1–99.6% — it vetoes 22 bars (MGC), 13 (MNQ) and 7 (MES) out of 2,511 / 1,859 / 1,859.** A base filter that
   differs from no filter on one bar in 150 is not conditioning on anything. The cause is `R4-M3`:
   `FRAMES[1440] = [1440, 7200]` holds the **same daily series twice**, so the only bars on which the
   two can disagree are inside the 2–4-bar alignment lag. **VOID as a filter at 1440m**, on all three
   symbols that have daily data.
2. **At 240m it passes 79.6–84.8%, the loosest of the multi-timeframe rows**, again because only two
   timeframes can conflict.

| condition | kind | verdict |
|---|---|---|
| `mtf_aligned` | SIGNAL | **CLEAN** arithmetic; **VOID in a frame of one** (23/23 cells); alive in all 23 corpus cells |
| `mtf_strongly_aligned` | SIGNAL | **MISNAMED** (R4-MT3: "every timeframe" ignores abstentions, 65–88% of firings) + **DEGRADED** (zero independent content at 240m and 1440m) + **VOID in a frame of one** |
| `mtf_not_conflicted` | FILTER | **DEGRADED** — timeframe-inert; **VOID as a filter at 1440m** (passes 99.1–99.6%) and unconditional in a frame of one |

**Group verdict: DEGRADED**, VOID in two named configurations.

## What this does to `BRIEF.md` rule 2

Rule 2 says multi-timeframe agreement "measured detectably *worse* than requiring none (z = −4.09)",
and notes that "on a two-timeframe frame, 'majority' and 'unanimous' are the same statement (D17)".
**D17 is confirmed here and is stronger than stated**: it is not only that the two statements
coincide, it is that at the 240m and 1440m rows the *entire corpus* is a two-voter frame, so the
grading condition has no content there at all; and at the four finer rows the "unanimous" condition
ignores abstentions on 65–88% of its firings; and at 1440m the higher timeframe is the same series
lagged 2–4 sessions (`R4-M3`). **Whether multi-timeframe alignment helps is not answered by that
measurement** — what was measured is this implementation. I reach the same conclusion R1 does at
`R1_group_audit.md:503-506`, by three mechanisms it did not use, and I want to be explicit that this
is *not* a defence of the hypothesis: it is a statement that the null was measured against a
misconfigured treatment arm.

---

# Final tally — 7 groups, 31 conditions

## Per-condition verdict split

| group | group verdict | CLEAN | DEGRADED | MISNAMED | VOID (per cell) |
|---|---|---|---|---|---|
| `trend` (8) | **CLEAN** | **8** | — | — | — |
| `momentum` (6) | **MISNAMED** | 3 | 1 | 2 | — |
| `meanreversion` (3) | **CLEAN** | **3** | — | — | — |
| `volatility` (3) | **MISNAMED** | — | 1 | 2 | 1 (in conjunction) |
| `regime` (3) | **DEGRADED** | — | 3 | — | 1 (directional half) |
| `multitimeframe` (3) | **DEGRADED** | 1 | 2 | 1 | 3 (frame of one) |
| `candlestick` (5) | **CLEAN** | **5** | — | — | — |

**Primary verdict, one per condition (a condition is counted once, at its worst unconditional verdict;
VOID verdicts are conditional on a named cell and are listed separately below):**

| verdict | n | conditions |
|---|---|---|
| **CLEAN** | **20** | all 8 `trend`; `rsi_directional`, `macd_directional`, `stoch_directional`; all 3 `meanreversion`; all 5 `candlestick`; `mtf_aligned` |
| **DEGRADED** | **6** | `macd_hist_direction`; `volatility_normal`; `regime_trending`, `regime_ranging`, `regime_matches_direction`; `mtf_not_conflicted` |
| **MISNAMED** | **5** | `rsi_extreme_reversal`, `stoch_extreme` (wrong group); `volatility_compressed` (wrong field), `volatility_expanding` (wrong quantile); `mtf_strongly_aligned` (description ignores abstentions) |
| **PROXY** | **0** | — none of my 31 names an object the data does not contain. My surface has no participant-information group, which is the whole reason R1's round-1 rate was never going to replicate here |
| **DEAD** | **0** | superseded by VOID, which is per-cell and honest |

**Group verdicts: 3 CLEAN, 2 MISNAMED, 2 DEGRADED.** So **20 of 31 conditions are clean** and
**2 of 7 groups have a name that does not describe the arithmetic.**

## VOID configurations found — per symbol and per timeframe, never in general

| # | configuration | cause | scope |
|---|---|---|---|
| 1 | **BREAKOUT + `volatility_expanding`** | `atr_percentile <= 0.30 AND >= 0.70`, same field, same `tf` — empty by arithmetic | **all symbols, all timeframes**; 14 of 84 generated BREAKOUT strategies on the corpus path |
| 2 | **MULTI_TIMEFRAME in a single-timeframe frame** | `agreeing_timeframes` can reach at most 1 vote; both SIGNALs return `no()` | 0 fires in **23 of 23** frame-of-one cells (4 symbols × 6 timeframes). Not reachable in the published corpus |
| 3 | **`mtf_not_conflicted` at 1440m** | `FRAMES[1440] = [1440, 7200]` and 7200m is the daily series relabelled — the two can disagree only inside the 2–4-bar alignment lag | passes **99.1% MGC / 99.3% MNQ / 99.6% MES**; MCL has no daily CSV |
| 4 | **`regime_matches_direction` SHORT half, MES 240m** | regime read off the daily series (`regime_tf = 1440`); daily index-complex regime is `TREND_UP` throughout this window | **188 of 188 firings LONG on MES 240m**; 194/206 MNQ 240m. **Not** MGC (43.5%) or MCL (57.2%) |
| 5 | **`mtf_not_conflicted` in a frame of one** | one timeframe cannot hold UPTREND and DOWNTREND | passes 100.0% in **23 of 23** frame-of-one cells |

Also recorded, not VOID but adjacent: **23–27% of `volatility_normal`'s passes at 240m are the string
`"NORMAL"` from `RegimeSnapshot`'s field default**, not a volatility measurement, on all four symbols
(`R4-V3`).

## Which templates require a group I found broken

Measured from `TEMPLATES`, not inherited `[measured: python3, required_groups / base_filters per template]`.

**Through a REQUIRED group** — a strategy of that template cannot exist without a member of it:

| template | required group of mine | its verdict | what that makes every published row of this template |
|---|---|---|---|
| **MOMENTUM** | `momentum` | **MISNAMED** | 1 of its 6 required options is an exact duplicate of another, and **2 of 6 are mean-reversion conditions**. A MOMENTUM strategy whose `momentum` condition is `stoch_extreme` (35–54% of bars) is a fade filed under MOMENTUM — **and per `R4-M1` its other declared requirement, `volume`, is not enforced, so 24 of 40 generated MNQ MOMENTUM strategies contain no volume condition at all** |
| **MULTI_TIMEFRAME** | `multitimeframe` | **DEGRADED** | at 240m and 1440m `mtf_strongly_aligned` has **zero** content distinct from `mtf_aligned` (identical on 100% of bars, 4 symbols); at 5m–60m `mtf_strongly_aligned` fires with a non-agreeing timeframe present on **65–88%** of its firings; at 1440m the higher timeframe is the daily series lagged 2–4 sessions |
| **TREND** | `trend` | CLEAN | — but its base filters `regime_trending` (DEGRADED) and `volatility_normal` (DEGRADED) are not, and **26% of TREND strategies carry `regime_matches_direction` on top of the identical `regime_trending` base filter** |
| **PULLBACK** | `trend`, `meanreversion` | both CLEAN | — but its base filter `mtf_not_conflicted` is DEGRADED and timeframe-inert, with a pass rate of **47.0%–100%** set by the frame |
| **REVERSAL** | `meanreversion` | CLEAN | — |
| **MEAN_REVERSION** | `meanreversion` | CLEAN | — but its base filter `regime_ranging` is DEGRADED, and at 240m it vetoes a fifth of bars on daily-regime warm-up |
| **FIBONACCI** | `trend` | CLEAN | — |

**So 2 of the 13 templates require a group I judge broken** (MOMENTUM, MULTI_TIMEFRAME), and 5 more
require only clean groups of mine.

**Through a BASE FILTER** — unconditional, the strategy does not choose it:

| template(s) | base filter of mine | verdict |
|---|---|---|
| **all except BREAKOUT — 12 of 13** | `volatility_normal` | **DEGRADED** — measured on the frame's regime timeframe, not the strategy's; 23–27% of its 240m passes are a dataclass default |
| **BREAKOUT** | `volatility_compressed` | **MISNAMED** — names Bollinger width, reads ATR percentile; verdict differs on **24–30% of 60m bars and 37–49% of 240m bars** |
| **TREND** | `regime_trending` | **DEGRADED** — timeframe-inert (bit-identical across 3 bindings) |
| **MEAN_REVERSION** | `regime_ranging` | **DEGRADED** — same, plus an 11-point 240m pass-rate drop |
| **PULLBACK** | `mtf_not_conflicted` | **DEGRADED** — ignores `tf`; pass rate 47.0%–100% by frame composition; **VOID as a filter at 1440m** |

**All 13 of 13 templates carry a DEGRADED or MISNAMED condition from my seven groups in a slot the
strategy cannot avoid** — 12 via `volatility_normal`, BREAKOUT via `volatility_compressed`. That is a
property of the base-filter lists, not of any strategy, and it is the single most consequential line
here. It is also the same conclusion R1 reached from the same two conditions; I reproduce it because it
is the one claim in this audit that every published row depends on.

---

# Comparison against `R1_group_audit.md` — agreements and disagreements, reported separately

Per the coordinator's correction. **Read the DECLARED ANCHOR section first: I saw R1's verdicts before
forming mine, so the agreements below are corroboration of a reading, not an independent replication.**

## Per-condition verdicts: 30 of 31 agree, 1 is stricter

| R1's verdict | my verdict | n | conditions |
|---|---|---|---|
| CLEAN | CLEAN | 19 | all 8 `trend`; `rsi_directional`, `macd_directional`, `stoch_directional`; all 3 `meanreversion`; all 5 `candlestick` |
| CLEAN (w/ DEAD-at-top caveat) | CLEAN (w/ VOID-in-frame-of-one) | 1 | `mtf_aligned` — same verdict, different cell named |
| DEGRADED | DEGRADED | 6 | `macd_hist_direction`, `volatility_normal`, `regime_trending`, `regime_ranging`, `regime_matches_direction` (additionally VOID on one directional half at MES 240m), `mtf_not_conflicted` |
| MISNAMED | MISNAMED | 4 | `rsi_extreme_reversal`, `stoch_extreme`, `volatility_compressed`, `volatility_expanding` |
| **DEGRADED** | **MISNAMED + DEGRADED** | **1** | **`mtf_strongly_aligned`** — see `R4-MT3` |

**All 7 group verdicts agree**: `trend` CLEAN, `momentum` MISNAMED, `meanreversion` CLEAN,
`volatility` MISNAMED, `regime` DEGRADED, `multitimeframe` DEGRADED, `candlestick` CLEAN.

The one stricter verdict: R1 filed `mtf_strongly_aligned` DEGRADED for having no independent content at
the top bindings. I add that its **description is false on 65–88% of its firings** at four of six
corpus rows on all four symbols — "every timeframe from this one up agrees" is computed over only the
*directional* timeframes, because `agreeing_timeframes` drops abstentions from `voting`
`[repo-verified: features.py:764-766]`. A reader is actively misled about what agreed, which is R1's
own bar for MISNAMED `[repo-verified: R1_group_audit.md:24]`.

## Three CONTRADICTIONS — same lines read, different conclusion

| # | R1's claim | where | what I find |
|---|---|---|---|
| 1 | "any two-condition confluence that happened to draw **both** MACD conditions was counting one reading twice and calling it agreement" | `R1_group_audit.md:396-399` | **Structurally impossible.** One condition per group, and no template lists a group in both required and optional. Measured 0 co-occurrences on 4 symbols. The duplication's real cost is a **byte-identical twin rule set with a second `strategy_id`** — denominator inflation, not false confluence. `R4-MO1` |
| 2 | **SUPERSEDED — see Addendum A; amended from CONTRADICTION to REFINEMENT after R1's rebuttal in `msgs/14_R1_R4_re-signal-pools.md`.** "a MULTI_TIMEFRAME strategy whose primary timeframe is the top of its frame can never emit a signal — **structurally zero-trade**, exactly the shape of round 1's `openinterest` finding" | `R1_group_audit.md:480-486` | **Not a configuration the corpus builds.** `FRAMES` always appends higher timeframes and every harness filters `s.primary_tf == tf`; both signals fire in **all 23** corpus cells (201–1,791 times). The VOID configuration is a **frame of one**, 0/N in 23 of 23 cells, and it is unreachable via `scout.rank` (its `suffix` dict raises first) and absent from all 40 `build_symbol_frame` call sites. `R4-MT1` |
| 3 | "a 4h TREND strategy in a `[5,15,60,240]` frame is gated by the **15-minute** regime" | `R1_group_audit.md:607-609` | The defect is real; **its direction in the corpus is the opposite and its scope is half.** `FRAMES` gives `regime_tf` = the strategy's own timeframe at 15m/30m/60m, **coarser** at 5m (15), **the daily series** at 240m, and the mislabelled daily copy at 1440m. A 4h TREND strategy is gated by the **daily** regime, never the 15-minute one. `R4-M3` |

## Four REFINEMENTS — R1's verdict stands, a load-bearing part of its consequence does not

| # | R1's statement | refinement |
|---|---|---|
| 4 | template map lists `volume` as "required by **MOMENTUM, BREAKOUT**" (`:1114`, `:1157`) | **Not enforced.** `_signal_pools` filters to SIGNAL, `volume` has 0 of 3, and the empty pool is dropped. `R4-M1`. R1 has since verified and accepted this |
| 5 | D-M2: a `rsi_extreme_reversal` MOMENTUM strategy is a mean-reversion strategy "**with a `volume` filter on it**" (`:426`) | No volume filter in **24 of 40** generated MNQ MOMENTUM strategies and 15 of 25 MCL. MOMENTUM is the one template without `volume_not_thin` in `base_filters` `[repo-verified: combinator.py:219]` |
| 6 | D-V2: "MGC and MES did not **in this sample**" (`:793`) | Not sampling — `profiles.groups_for` gives MGC and MES no BREAKOUT template at all. On the corpus path (`groups=ALL_GROUPS`) all four symbols produce it: **84 BREAKOUT, 28 VOID = one third**, not 60/20. `R4-M2` |
| 7 | D-MTF2: `mtf_strongly_aligned` identical to `mtf_aligned` "at `tf=60`" | Correct for R1's frame. In the corpus the 100%-identity rows are **240m and 1440m**, and at 60m the two differ on 248–314 bars. And it is **provable, not measured**: two agreeing voters give `\|a\| ≥ 0.569` and two disagreeing give `\|a\| ≤ 0.14` in every corpus frame. `R4-MT2` |

## Findings absent from R1's file

`R4-M1` (required group silently dropped), `R4-M2` (per-symbol template profile),
`R4-M3` (**`align_bucket` ignores `minutes` above 1440, so `FRAMES[1440]`'s "weekly" timeframe is the
daily series lagged 2–4 sessions** — the largest single item here), `R4-C1` (the CLV duplicate is a
*reachable* cross-group false confluence and is not in `GLOBAL_EXCLUSIVE`, while the two provable
same-group duplicates are also not in it), `R4-MT3` (the abstention bug in `mtf_strongly_aligned`),
`R4-MT4`'s second half (`mtf_not_conflicted` VOID as a filter at 1440m), `R4-R3` (`regime_matches_direction`
is 188/188 LONG on MES 240m), `R4-V3` (23–27% of `volatility_normal`'s 240m passes are a dataclass
default), `R4-V1`'s 240m half (correlation collapses to −0.06/−0.10; MCL 2.3% vs 41.3%), `R4-T2`
(the deadband silently voids five conditions when ATR is unavailable), and the prefix-invariance test
over all 31 conditions.

---

# Anti-overfitting and validity checks on this audit itself

| risk | how I checked | what I found |
|---|---|---|
| **look-ahead / repainting** | **Direct prefix-invariance test**, not inspection: rebuild the frame from `bars[:i+1]`, evaluate all 31 conditions at bar `i`, compare verdict **and** direction against the full series. 3 cells (MGC 60m, MNQ 5m, MCL 60m), 16 probes | **all 31 prefix-invariant at every probe.** No repainting, no future-data read |
| **future-data leakage in my own measurements** | every census used `SymbolFrame.iter_snapshots()`, the same path a backtest uses; no measurement reads a bar after the one being evaluated | clean |
| **silent-exception masking** | `reset_condition_errors()` before every cell; `CONDITION_ERRORS` read after | **empty in all 47 cells** — no condition is the "raised on every bar, recorded as 0% trigger rate" failure `base.py:129-147` warns about |
| **data-mining bias / multiple comparisons** | **no expectancy, no z, no t, no Sharpe, no P&L, no trade is simulated anywhere in this file.** Every number is a fire count, a pass rate, a correlation, an availability count or a generated-strategy count. Nothing was selected on outcome | **not applicable by construction.** No deflation to apply; `free_t` does not enter |
| **parameter sensitivity** | I varied **no** threshold. Where one is part of a finding (`p <= 0.30`, `0.4` alignment, `>= 60` regime bars, `0.05` deadband) it is quoted exactly as the repo sets it | n/a |
| **survivorship** | none of the 7 groups was selected on outcome; **all 31 conditions audited**, including the 20 that came back CLEAN | clean — which is why 20 CLEAN verdicts are reportable |
| **insufficient sample** | 47 cells; every table per-cell, **nothing pooled**. Thin cells flagged rather than aggregated (`candle_decisive_close` 69 fires on MGC 240m; `mtf_aligned` 201 on MNQ 240m — both above `toolkit.FLOOR = 20` and both small-sample) | flagged, not hidden |
| **per-symbol independence** | **4 contracts, every table per-symbol, never pooled.** 4 findings are symbol-specific: `regime_matches_direction` 100% LONG on MES 240m and 43.5% on MGC; `volatility_normal` 93–95% at 240m on MGC/MNQ/MES and 79.7% on MCL; `volatility_compressed`'s described field fires on 2.3% of MCL 240m bars and 24.4% of MGC's; MCL has no daily CSV so three of my 1440m rows have three symbols not four | **nothing pooled across symbols.** Where MES and MNQ agree I say so is *not* corroboration (`BRIEF.md`: one index complex) |
| **per-timeframe independence** | 6 timeframes individually (frame-of-one), 6 corpus frame groups, the dispatch's 1m+5m+15m group, and one frame read at three bindings. **5 findings change verdict with timeframe** | **nothing pooled across timeframes.** `mtf_strongly_aligned` has content at 5m–60m and none at 240m–1440m; `volatility_compressed`'s error is 24–30% at 60m and 37–49% at 240m; `regime_ranging` drops 11 points at 240m; `mtf_not_conflicted` is a real filter at 5m–60m and VOID at 1440m; MTF signals are alive in every corpus frame and VOID in every frame of one |
| **multi-timeframe *groups*, not only single timeframes** | the dispatch asks whether alignment helps. I did not answer that — it needs expectancy, which I am not permitted to compute — but I established that **the treatment arm is misconfigured at 240m and 1440m (two voters, one of them a lagged copy of the other) and misdescribed at 5m–60m (abstentions dropped)**, which is a prerequisite for the question being answerable at all | the question is **open**, not settled negative |
| **unrealistic fills / costs / slippage** | **not applicable** — no trade, no fill, no cost model anywhere in this file |
| **my own anchoring bias** | **the largest specific risk here and it is not fully mitigated.** I read R1's verdicts first. Mitigations: my census uses a different cell design (47 cells vs R1's 5, corpus frames rather than an illustrative frame); I looked for and found 10 findings R1 does not have; I recorded 3 contradictions and 4 refinements of its stated consequences; and I re-derived every verdict from source with my own line citations | **declared, not eliminated.** 30 of 31 agreements should be read as one audit plus one confirmation, not two audits |
| **confirmation bias toward "broken"** | R1 warned its round-1 3-of-3 rate was a biased sample. My surface contains **no** participant-information group, so the prior should be *lower*, not higher | **20 of 31 CLEAN and 3 of 7 groups CLEAN.** The two cleanest groups (`trend` 8/8, `candlestick` 5/5) are the two I checked hardest for a naming defect and found none |

**One limitation I cannot remove, restated because it is easy to misread this file.** This audit
answers "does the arithmetic do what the group name claims". It does **not** answer "is the object
worth trading", and nothing here raises or lowers the prior on any strategy. `trend` is the cleanest
group in my surface and four of its eight members fire on 84–96% of bars.

---

# Addendum A — R1 rebutted my method objection and is half right. The resolution is a mechanism neither of us had

`msgs/14_R1_R4_re-signal-pools.md` §2 answers `R4-M3`/`R4-MT1` with a measurement: "I measured it
against the harness and **it does generate them**." I checked R1's claim before deciding, and it
reproduces exactly on my run.

## What I got wrong

My sentence "R1's DEAD-at-top verdict describes a frame nobody builds" and the implication that the
configuration is not **generated** are **wrong**. `generate_strategies(sym, [5,15,60,240], max_total=400)`
emits strategies at **every** timeframe in the list, not only the lowest:

| symbol | n | `primary_tf` distribution | MULTI_TIMEFRAME @ `primary_tf = 240` |
|---|---|---|---|
| MGC | 314 | {5: 54, 15: 54, 60: 136, 240: 70} | 0 |
| MNQ | 314 | {5: 56, 15: 100, 60: 78, 240: 80} | **32** |
| MES | 336 | {5: 44, 15: 80, 60: 104, 240: 108} | **8** |
| MCL | 296 | {5: 38, 15: 84, 60: 126, 240: 48} | **8** |

`[measured: python3, generate_strategies(sym,[5,15,60,240],max_total=400) → 48 MULTI_TIMEFRAME carriers
at primary_tf=240, all with confirm_tfs=() and Condition.timeframe None on every condition —
R1's figures reproduced exactly]`

So the top-of-frame binding **exists in the generated population**, and R1's D-MTF1 is a statement
about 48 counted carriers, not a theoretical corner. I withdraw the word "generates" and the
framing that went with it.

## What I still hold, and the evidence is stronger than my first statement

**No harness runs them in that frame.** Every one of the **13** `generate_strategies` call sites in the
repository filters `primary_tf == tf` and passes `FRAMES[tf]` as the timeframe list
`[measured: grep over workspace/{chrono/ledger,bigscan/cell,studies/toolkit,newstrats/rank,
strategy_research/w3_rank(×2),w3_audit,w3_cleanfeed,w3_rth,w2/w2rank,scratch/w4_placebo,w4_ledger,
w4b_placebo,w4b_ledger}.py → 13 of 13 carry `primary_tf ==`, 0 exceptions]`, and
**`FRAMES[tf][0] == tf` for all six keys** `[measured: python3 over scout.FRAMES]`. So a
`primary_tf = 240` strategy is always run against `FRAMES[240] = [240, 1440]`, in which 240 is **not**
the top — `agreeing_timeframes(from_tf=240)` sees `{240, 1440}`, `voting = 2`, and both signals are
alive. My 23-cell census confirms it: `mtf_aligned` fires **201–1,791 times, zero zeros**.

**And `confirm_tfs` cannot change that**, which is the piece that decides it. `confirm_tfs` does
exactly two things: it binds `structure` SIGNALs to `confirm_tfs[0]` when the strategy has ≥3 signals,
and it annotates conflicts non-bindingly `[repo-verified: combinator.py:618-633; base.py:747-755]`.
The code comment is explicit that multitimeframe conditions deliberately **stay on the primary
timeframe** — "binding them UPWARD drops the strategy's own timeframe out of its own alignment vote -
and at the top of the frame it leaves a single voter, which is how `mtf_aligned` came to duplicate
`structure_trend` exactly" `[repo-verified: combinator.py:621-627]`. So `voting` is decided by the
**frame**, never by the strategy's `confirm_tfs`, and a `confirm_tfs = ()` primary-240 strategy run
against `[240,1440]` behaves identically to a `confirm_tfs = (1440,)` one.

## The mechanism, which is better than either of our original claims

**`generate_strategies` is called with the frame's whole timeframe list and emits a strategy at every
timeframe in it; the harness then discards every strategy whose primary is not the frame's base.**

| symbol | frame | generated | **kept** (`primary_tf == tf`) | **discarded before any measurement** |
|---|---|---|---|---|
| MGC | [5,15,60] @5m | 284 | 52 | **232 = 82%** |
| MGC | [60,240,1440] @60m | 239 | 52 | **187 = 78%** |
| MGC | [240,1440] @240m | 167 | 82 | 85 = 51% |
| MNQ | [5,15,60] @5m | 304 | 32 | **272 = 89%** |
| MNQ | [240,1440] @240m | 167 | 87 | 80 = 48% |
| MES | [5,15,60] @5m | 289 | 43 | **246 = 85%** |
| MCL | [5,15,60] @5m | 268 | 66 | **202 = 75%** |
| all 24 cells | — | 166–304 | 32–87 | **48%–89%** |

`[measured: python3, generate_strategies(sym, FRAMES[tf], groups=ALL_GROUPS, max_total=400) then
filtering primary_tf==tf, 4 symbols × 6 timeframes]`

**R1's 48 VOID carriers live entirely inside the discarded portion.** At a three-timeframe frame
60–89% of the generated population is thrown away by design, and at a two-timeframe frame ~50%.

## So both statements are true, about different populations, and the distinction is `R1-Q2`'s

| question | population | answer |
|---|---|---|
| Did strategies that **cannot fire** enter the *generated* count? | generated, pre-filter | **Yes — R1 is right.** 48 MTF-at-top carriers, 98 `profile`-at-240m, 239 of 1,260 = 19.0% with at least one never-firing condition |
| Is any *measured* row — anything in `scan_reports/` — a MULTI_TIMEFRAME strategy bound to the top of its own frame? | run, post-filter | **No — I am right.** 13 of 13 call sites filter; `FRAMES[tf][0] == tf`; both signals alive in 23 of 23 corpus cells |

That is exactly the generated-versus-evaluated distinction `R1-Q2` turns on and that `ADJ-4` ruled on
by reading the figure as *evaluations*. **The discard rate above is a new input to it**: a large
majority of each generated population never reached `run_portfolio` at all, for reasons that have
nothing to do with whether it could trade. Neither of us can allocate a `D<n>`; it belongs in R1's
open question rather than as a new one.

**I amend my own CONTRADICTION #2 to a REFINEMENT.** R1's D-MTF1 mechanism and count are right; what
I add is that its carriers are unmeasured by construction, and that the VOID configuration which is
*reachable and un-discarded* is the frame of one (0/N in 23 of 23 cells).

## Two housekeeping items from the same message

**Vocabulary bridge to `ADJ-8`**, so the three audit files collate. My dispatch gave me
CLEAN / PROXY / DEGRADED / DEAD / MISNAMED; `ADJ-8` fixes
PROXY / DEGRADED / HONEST-DERIVED / HONEST-DERIVED-BUT-BROKEN. Mapping for my 31:

| mine | `ADJ-8` | my conditions |
|---|---|---|
| CLEAN (20) | **HONEST-DERIVED** | all 8 `trend`, 3 `momentum`, 3 `meanreversion`, 5 `candlestick`, `mtf_aligned` |
| DEGRADED (6) | **DEGRADED** | `macd_hist_direction`, `volatility_normal`, 3 `regime`, `mtf_not_conflicted` |
| MISNAMED — wrong field or window (3) | **HONEST-DERIVED-BUT-BROKEN** | `volatility_compressed`, `volatility_expanding`, `mtf_strongly_aligned` |
| MISNAMED — right arithmetic, **wrong group** (2) | **no `ADJ-8` term exists** | `rsi_extreme_reversal`, `stoch_extreme` |
| PROXY (0) | PROXY | **none.** My surface contains no participant-information group |
| VOID (5 configurations) | no term in either vocabulary before `R1-REQ-5` | see the VOID table above |

**Two gaps worth the manager's attention, not new requests:** `ADJ-8` has no term for a condition
whose arithmetic is honest and whose **group** is wrong — which is 2 of my 31 and the whole of R1's
`momentum` verdict — and neither vocabulary had a term for "cannot fire" until `R1-REQ-5`. I use
`R1-REQ-5`'s **VOID** and file no second request for it.

**R1's request that I mark post-anchor entries: already done**, in the DECLARED ANCHOR section above —
**all 31**, without exception, and stated before any verdict. R1's offer that my four-symbol coverage
supersedes its two-symbol coverage for `multitimeframe` and `regime`: accepted, and the numbers are in
those two group sections — 4 symbols × 6 corpus timeframes, plus 23 frame-of-one cells and 12
three-binding cells.

**`R4-M1`'s `D<n>`:** R1 asks whoever files it to say so. **I have filed it, as `R4-REQ-2`** — cite
that rather than opening a duplicate.

---

# What a reader should take from this file

1. **20 of 31 conditions are CLEAN and 3 of 7 groups are CLEAN.** `trend` (8/8) and `candlestick`
   (5/5) are the two I attacked hardest for a naming defect and found none. R1's round-1 3-of-3 rate
   was never going to replicate on this surface, because my seven groups contain **no**
   participant-information group and therefore no name that could overreach the data.

2. **The two MISNAMED groups are misnamed in different ways and only one is fixable by renaming.**
   `volatility` reads the wrong *field* (`volatility_compressed` names Bollinger width and reads ATR
   percentile — verdicts differ on 24–30% of 60m bars and 37–49% of 240m bars, and on MCL at 240m the
   described field fires on 2.3% of bars against 41.3%). `momentum` is misnamed by *filing*: two of its
   six members are mean-reversion conditions whose direction rule is the negation of the other four's,
   and one is an exact duplicate of another in 23 of 23 cells.

3. **The single most consequential item is not in any group — it is `align_bucket`.** For every
   request above 1440 minutes it returns the CME trading-day start, so `FRAMES[1440]`'s "weekly"
   timeframe **is the daily series**, bit-identical in OHLCV and lagged 2–4 sessions by a mislabelled
   `end_ts`. Every daily multi-timeframe statement in this repository is a lagged-autocorrelation test
   on one series, and PULLBACK's base filter passes 99.1–99.6% there as a direct consequence.
   `R4-REQ-1`.

4. **Every VOID verdict here is conditional on a named symbol and a named timeframe, and four of five
   would have been invisible from any single cell.** `regime_matches_direction` fires 188 times on MES
   at 240m and **all 188 are LONG** — while the same condition on MGC at the same timeframe is 43.5%
   LONG. That is not a weak signal, it is a one-sided detector, and it exists because at the 240m row
   the regime is read off the daily series. A SHORT-allowed MES 240m strategy carrying it cannot take
   a short.

5. **All 13 of 13 templates carry a DEGRADED or MISNAMED condition from these seven groups in a slot
   the strategy does not choose** — 12 via `volatility_normal`, BREAKOUT via `volatility_compressed`.
   At the 240m row, 23–27% of `volatility_normal`'s passes are the string `"NORMAL"` from a dataclass
   field default rather than a volatility measurement.

6. **Nothing here is evidence about whether any of these conditions is worth trading**, and nothing
   here computes an expectancy, a t, a z or a P&L. A correctly named condition is not a good
   condition: `trend` is the cleanest group in my surface and four of its eight members fire on 84–96%
   of bars.

7. **This file is one audit plus one confirmation, not two audits.** I read R1's verdicts before
   forming mine and have said so at the top and in every comparison table. The parts that carry
   independent weight are the ten findings R1's file does not have, the three contradictions and four
   refinements of its stated consequences (one of which R1 then corrected back — Addendum A), and a
   census with 47 cells against its five.
