# EF2 / Burst 01 — substrate, and the session arithmetic that reshapes the cell

Cell: **SWING, MGC + MCL, 60m and 240m.** Needs neither EF1's harness nor EF6's controls.

## 1. Substrate, fixed and labelled

Every EF2 number is measured on **`data/archive/{MGC,MCL}_60m.jsonl`** as the base series, with
240m **resampled up from it** by `SymbolFrame` `[repo-verified: futures_agents/features.py:811]`.

| symbol | 60m bars | span | distinct dates |
|---|---|---|---|
| MGC | 11,297 | 2024-10-06T19:00−04:00 → 2026-09-25T16:00−04:00, **718 calendar days** | 596 |
| MCL | 10,934 | same window, **718 calendar days** | 590 |

`[measured: workspace/roundtable/edge/EF2/code/substrate.py → data/substrate.json]`

`sqrt(718/365.25) = 1.402`. So `t ≈ SR × 1.402`: clearing `free_t = 1.177` (one pre-registered
hypothesis) needs annualised Sharpe **0.84**; clearing a search-width threshold of 4.0 needs **2.85**.
Quote both with every row.

### Equivalence against `csv/raw`, re-measured independently (BRIEF data policy, condition 2)

| symbol | tf | overlap | bit-exact closes | max abs Δclose | volume mismatches | verdict |
|---|---|---|---|---|---|---|
| MGC | 60m | 4,987 | 1,063 | **3.4375e-07** | 2 | same series, within tol 1e-5 |
| MCL | 60m | 4,987 | 221 | **4.8242e-08** | 2 | same series, within tol 1e-5 |

Compared in **UTC on both sides** (`csv/raw` is `+00:00`, the archive `-04:00`). Replicates the
BRIEF's corrected table exactly, including the 2-bar volume mismatch on both symbols.

### **`csv/raw` has no 4h file for any symbol, so the 240m cell cannot be cross-verified against it**

`[measured: ls csv/raw → MCL_{15m,1h,1m,30m,5m}.csv, MGC_{15m,1d,1h,1m,30m,5m}.csv; no *_4h.csv
anywhere in the directory]`. The 240m half of my cell is **archive-only by necessity**, not by choice.
What I could verify instead, and did:

**Resampling archive 60m → 240m is bit-identical to the natively fetched `_240m.jsonl`:**
MGC 3,052/3,052 closes bit-exact, `max|Δclose| = 0.0`, `max|Δhigh| = 0.0`, zero bars on either side
only; MCL 2,990/2,990 identically
`[measured: python3, resample(archive 60m, 240) vs BarArchive.load(sym,240), UTC-keyed]`.
So the 240m series I measure on is the vendor's own 4h series, and my resample path introduces
nothing. It is still a **single-store number** and is labelled as one.

### What I excluded, and why — stated rather than silently truncated

- **1440m is out of the swing cell on both symbols.** `MCL_1440m.jsonl` holds **exactly 1 row**
  `[measured]`, so no daily confirmation timeframe can be built for MCL at all; building one for MGC
  alone would make the two symbols' frames asymmetric, and MGC's daily file spans 2010-10-04 →
  2026-09-25, a different era from the 60m window. A daily bar is also `>= _SESSION_MINUTES = 390`
  `[repo-verified: base.py:379]`, so it contains the 16:00–18:00 break and cannot be a swing primary
  under this programme's rule by arithmetic.
- **15m/5m are out as confirmation or execution timeframes.** Archive span at 15m is **57 calendar
  days** against 718 at 60m `[measured]`. Adding one truncates the swing substrate by 92%. So
  `DEFAULT_EXECUTION_MAP`'s `240 → 15` and `60 → 5` `[repo-verified: combinator.py:443]` are
  **unavailable to me**: my frames contain no timeframe finer than the primary, so
  `execution_tf` is `None` on every EF2 strategy and the "hone the entry on a finer timeframe" axis
  is **not testable in the swing cell**. That is a scope limit, reported, not worked around.

### Frames

| frame key | timeframes | primary | confirm_tfs | base |
|---|---|---|---|---|
| `f60__p60` | (60,) | 60 | () | 60m |
| `f240__p240` | (240,) | 240 | () | 60m |
| `f60_240__p60` | (60,240) | 60 | (240,) | 60m |
| `f60_240__p240` | (60,240) | 240 | () | 60m |

Each of the four required cells (MGC/MCL × 60m/240m) therefore appears **twice**: alone, and inside
the 60m+240m group. That is the brief's "on its own and in groups" with the group held to the two
timeframes that actually have span.

**Named honestly:** in `f240__p240` and `f60_240__p240` the base clock is still 60m, so a 240m thesis
is *decided* at 60m resolution against the last **completed** 240m bar
`[repo-verified: features.py:828-847, alignment pointer is last completed]`. That is the engine's own
design (`BacktestEngine.base_minutes` exists to convert a strategy's bar-denominated time stop to base
bars, `engine.py:231`), not an EF2 choice. It means a 240m signal can be present on up to 4
consecutive decision bars; `signals_skipped_in_position` is what stops that becoming 4 trades.

---

## 2. The session rule is much tighter than "22 hours", and it interacts with `rth_only`

### 2a. The 22-hour maximum is available only to an 18:00 ET entry

The cycle is **18:00 ET → 16:00 ET next day**. A position opened at time *T* inside a cycle must be
flat at that cycle's **16:00**, so the hold available is `16:00 − T`, not 22 hours:

| entry (ET) | cycle ends | max hold |
|---|---|---|
| 18:00 | 16:00 +1d | **22h 00m** |
| 22:00 | 16:00 +1d | 18h 00m |
| 02:00 | 16:00 same d | 14h 00m |
| 08:20 (MGC RTH open) | 16:00 same d | **7h 40m** |
| 09:00 (MCL RTH open) | 16:00 same d | **7h 00m** |
| 12:00 | 16:00 same d | 4h 00m |
| 15:00 | 16:00 same d | **1h 00m** |

So "swing" here is not one number. It is a **hold budget that shrinks linearly through the cycle**,
and any family whose thesis needs a fixed multi-hour runway is only testable on entries early in the
cycle. Multi-day theses are out of scope by arithmetic (BRIEF §15.1) and I am not truncating any.

### 2b. **With `rth_only=True` the overnight-hold regime is unreachable for entries — measured**

`StrategyFilters.rth_only` defaults to `True` `[repo-verified: base.py:393]` and is `True` on
**184/184 MGC and 167/167 MCL** strategies the combinator generates at `[60,240]`
`[measured: generate_strategies(sym,[60,240],max_total=400) → Counter({True: 184}) / Counter({True: 167})]`.
MGC's RTH is **08:20–13:30** and MCL's **09:00–14:30** `[repo-verified: config.py, get_contract]`.

Both windows sit **entirely inside** one 18:00→16:00 cycle, and the census confirms the consequence
arithmetically: on MGC 60m, `bars_rth_and_swing == bars_rth` exactly
`[measured: census, MGC:f60__p60 → 69 RTH bars, 69 RTH-and-swing-admissible of a 306-bar step sample]`.

**Therefore, for a default-filter strategy on MGC or MCL, the 18:00→16:00 rule adds no entry
opportunity at all — it only lengthens the permitted hold, from the contract's own RTH close (13:30
MGC / 14:30 MCL, which is what `exit_at_session_close` enforces today, `engine.py:470-473`) out to
16:00 ET the same day.** That is +2h30m on MGC and +1h30m on MCL, not +22 hours.

Reaching the genuinely unmeasured overnight regime requires **`rth_only=False`**, which is a
departure from the generated default and runs into **D24** ("`rth_only=False` buys sample and costs
expectancy"). I am therefore going to carry `rth_only` as an **explicit, paired arm** of my
population — `True` and `False` on the same rule set, `_id=None`, ids asserted distinct — rather than
inherit the default. Without that arm, an EF2 "swing" result is a slightly-longer-RTH result wearing
the swing label.

**Posted to EF1 as `EF2-01`,** because it changes what its harness has to support: not "allow
overnight" as a single switch, but a clock rule that admits non-RTH *entries* as well as non-RTH
*holds*, otherwise the switch is inert on these two contracts.

### 2c. 240m loses ~35% of its bars as entry bars; 60m loses ~8.7%

The 16:00–18:00 break is 2 hours wide, which a 240m bar cannot straddle cleanly:

| symbol | tf | bars | wholly inside the break | spanning the break | closing exactly at 16:00 ET | **inadmissible as a signal bar** |
|---|---|---|---|---|---|---|
| MGC | 60m | 11,297 | 495 (4.4%) | 0 | 489 (4.3%) | 984 = **8.7%** |
| MGC | 240m | 3,052 | 0 | **586 (19.2%)** | 497 (16.3%) | 1,083 = **35.5%** |
| MCL | 60m | 10,934 | 474 (4.3%) | 0 | 470 (4.3%) | 944 = **8.6%** |
| MCL | 240m | 2,990 | 0 | **563 (18.8%)** | 491 (16.4%) | 1,054 = **35.3%** |

`[measured: substrate.py session_arithmetic]`

The 240m grid is 00/04/08/12/16/20 ET. The bar stamped **12:00 closes at exactly 16:00** — the flat
deadline, so a fill at the next bar's open is a fill at or after 16:00 and is inadmissible. The bar
stamped **16:00 spans 16:00–20:00**, i.e. the entire no-position window. The 586-vs-489 excess at the
16:00 stamp is the Sunday 18:00 week open landing in the 16:00 bucket: 586 − 489 = 97 ≈ 102 weeks in
718 days.

**Consequence for the cell:** a 240m swing strategy has at most `22h / 4h = 5.5` bars of runway, and
loses a third of its decision bars to the clock rule. Every 240m exit geometry in
`expand_exit_models()` carries `time_stop_bars` of 30–120 `[repo-verified: combinator.py:52-110]`,
i.e. 120–480 **hours** at 240m, so **on 240m the time stop is unreachable and every position is
closed by the clock rule or by stop/target — the `time_stop_bars` axis is inert at 240m and must not
be reported as a tested variable there.** At 60m, 22 bars of runway against a 30–120 bar time stop:
same conclusion, `time_stop_bars` is inert at 60m too for the two tightest geometries and
near-inert for the rest.
