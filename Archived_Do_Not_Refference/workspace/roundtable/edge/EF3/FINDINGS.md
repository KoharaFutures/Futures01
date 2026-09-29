# EF3 — SWING on MES and MNQ

**Cell as dispatched:** SWING, MES + MNQ, 60m **and** 240m, 718 days (~1.97 yr).
**Cell as it ended:** SWING, MES + MNQ, **60m only** — the 240m arm is withdrawn, see §0.
**Substrate:** `data/archive/`, 60-minute base series, verified against `csv/raw` with a tolerance.
**Deliverable asked for:** a top 10 per symbol. **Delivered:** no ranked rows. See §7 for why, and
for exactly what is ready to fire.

Burst records: `bursts/01_substrate.md`, `02_firing_census.md`, `03_population.md`,
`04_protocol_preregistered.md`, `05_harness_reconciliation.md`.
Code: `code/ef3_substrate.py`, `ef3_census.py`, `ef3_stopcensus.py`, `ef3_population.py`,
`ef3_session.py`, `ef3_measure.py`, `ef3_stage2.py`, `ef3_rank.py`, `ef3_audit.py`.
Data: `out/census_{MES,MNQ}.json`, `out/stopcensus.json`, `out/population_4000.json`,
`out/population_ids_4000.json`, `out/stage1_{MES,MNQ}_gap.json` (includes the full trade ledger).

---

## 0. The 240m arm does not exist, and my own measurement pointed at it first

EF6's arithmetic: the window is 18:00→16:00 = 22 h = **1,320 minutes**, and
**1,320 = 2³·3·5·11**. So 5, 15, 30, 60 and 120 divide it and **240 gives 5.5**. A four-hour bar
cannot align with a twenty-two-hour window. That is arithmetic, not implementation, and no harness
fix reaches it.

**It is consistent with what I measured before anyone had the arithmetic.** Burst 01 recorded that
`align_bucket` anchors 4-hour buckets to ET midnight, so the bucket labelled **16:00 spans
16:00→20:00** and straddles both the flat and the reopen — **585 of 3,050 = 19.2% of 240m bars**,
identically on MES and MNQ. And when I compared engines (burst 05), the `SPANS_WINDOW` violations
were concentrated at 240m. I read that as a symptom of the early-close bug. It was also the flat
being asked to land on a grid that cannot hold it. The observation located the boundary; EF6
supplied the reason.

**Everything below is therefore reported twice where it matters: as measured (60m + 240m), and as it
stands now (60m only).** I have not deleted the 240m measurements, because the census facts about
240m are the reason the 240m arm was never going to produce evidence, and they are worth keeping.

---

## 1. Substrate, verified before anything else

| symbol | archive 60m | csv/raw 1h | overlap | closes bit-exact | max abs Δclose | volume mismatches |
|---|---|---|---|---|---|---|
| MES | 11,287 | 5,000 | 4,988 | **4,988 / 4,988** | 0.000e+00 | 2 |
| MNQ | 11,291 | 5,000 | 4,988 | **4,988 / 4,988** | 0.000e+00 | 2 |

Span **718.9 calendar days = 1.968 yr, sqrt = 1.403**. Compared with a tolerance, never `==`, and
normalised to UTC on both sides first (the BRIEF's timezone trap).

`resample(archive 60m → 240m)` is **bit-identical** to the archive's own 240m series: 3,050 bars,
identical stamps, 3,050/3,050 closes equal, 0 volume mismatches. That is why a 60m base could carry
both cells.

**Three grid facts, all mine to carry.** (i) The 240m bucket labelled 16:00 straddles the flat —
§0. (ii) 493 (MES) / 497 (MNQ) 60m bars are stamped inside 16:00–17:59 ET; only 5 / 9 are stamped
17:00–17:59, so the CME break is genuinely empty and the prohibited window is essentially one bar
per session. (iii) The archive holds **20 bars off the `:00` grid and they are exactly five
early-close half-sessions** (2024-11-29, 2024-12-24, 2025-07-03, 2025-11-28, 2025-12-24; four `:30`
bars each at 09:30/10:30/11:30/12:30 ET; identical on MES and MNQ). `csv/raw` has none — R3
measured its 1h grid as 100% `:00`. This is a **store** difference and it changes two VOID verdicts
to NEAR-VOID.

---

## 2. The firing-rate census — all four cells, before any population was built

No entries, no exits, no P&L anywhere in it. All 79 `CONDITIONS` on every base bar at binding
tf = 60 **and** tf = 240, both symbols. `CONDITION_ERRORS` empty in all four cells, so nothing below
is the silent-exception failure mode.

| # | configuration | MES 60m | MES 240m | MNQ 60m | MNQ 240m |
|---|---|---|---|---|---|
| 1 | `openinterest` (both conditions) | **VOID** | **VOID** | **VOID** | **VOID** |
| 2 | all six `profile` conditions | alive | **VOID ×6** | alive | **VOID ×6** |
| 3 | `mtf_aligned`, `mtf_strongly_aligned` | alive | **VOID ×2** | alive | **VOID ×2** |
| 4 | `StopKind.RANGE` ≡ ATR (D49) | 99.699% | 99.344% | 99.699% | 99.345% |
| 5 | `StopKind.VWAP_BAND` on the min-stop floor (D45) | **15.376%** | 9.227% | **7.471%** | 4.411% |
| 6 | `opening_range_fade` / `_breakout` (D-L1) | **VOID** / 15 | VOID / 14 | **VOID** / 14 | 1 / 13 |

Mechanisms: `bar.open_interest is None` on 11,287/11,287 and 11,291/11,291 archive bars;
`prior_profile is None` on 11,287/11,287 at the 240m binding but present on 11,050 / 11,054 at 60m;
`agreeing_timeframes(from_tf=240)` returns `voting = 1` on **every** bar (`voting ≥ 2` count = 0),
against 4,021 / 3,930 bars at 60m. Rows 4 and 5 are over (bar × direction) pairs, 22,574 / 22,582
per timeframe, by calling `ExitModel.stop_price` directly at matched `stop_mult = 1.0`.

**Corrections and refinements I owe on the standing list:**

* **D49 is real and it reaches nothing.** RANGE is byte-identical to ATR on 99.70% (60m) of pairs —
  the residue is exactly the 20 half-session bars (40 = 20 × 2 directions, both timeframes, both
  symbols). **But RANGE is unreachable from every template**: it lives only behind
  `expand_exit_models(include_aggressive=True)` and nothing sets that. Reachable stop kinds are
  `{ATR, STRUCTURE, VWAP_BAND}` — **three mechanisms, not five**, and `FIXED_TICKS` is absent too.
  What D49 *is* good for is R3's known-answer calibration test, whose true difference is provably
  zero on 99.7% of bars.
* **D45's two quantities move in opposite directions and only one is the defect.** Band width
  exactly zero: MES 4.48% at 60m, **20.23%** at 240m; MNQ 4.39% and 19.98%. The `min_stop_ticks`
  floor actually binding: MES **15.38%** at 60m, 9.23% at 240m; MNQ **7.47%** and 4.41%. The floor
  binds *more* at 60m even though the band is degenerate more often at 240m, because a
  non-degenerate 240m band is wide enough in points to clear the floor. Anyone quoting one D45 rate
  is quoting one of two different measurements. D45's stated 6–34% holds in 3 of 4 cells and
  **fails low for MNQ 240m (4.41%)**. MES's floor binds ~2× as often as MNQ's at both timeframes,
  and that is `min_stop_ticks` and price scale (MES 8 ticks = 2.00 pts on ~6,000; MNQ 16 ticks =
  4.00 pts on ~22,000) — a contract-spec fact, not a market fact.
* **D-L1 is less dead on my store.** A 09:30 `:30` bar has `minutes_since_open = 0`, so the
  30-minute opening-range window is reachable on 5 sessions of 507. `opening_range_breakout` is
  therefore **NEAR-VOID at 13–15 fires in ~11,290 bars**, all on those five dates, rather than dead.
  `opening_range_fade` is still strictly VOID at 60m on both symbols. A strategy whose entire sample
  is five holiday half-sessions is not a strategy: I treat NEAR-VOID as reportable, not rankable.

**Two dimensions the census removes outright.**
`STRUCTURE` stops are placeable (unplaceable on 0.137% at 60m, 0.394% at 240m), so all three
reachable kinds are genuinely available. And **`time_stop_bars` is arithmetically inert**: the
catalogue's smallest value is 30 *primary* bars, `primary_bars_held = (i−entry)//step + 1`, and the
cap is 22 bars at 60m. Confirmed empirically — **`TIME` exits = 0 of 103,191 trades** across both
full-population runs. Every catalogue variation in time-stop length measures nothing here.

---

## 3. The population, its exact size, and what the census removed

`generate_combinations(sym, [60,240], groups=groups_for(sym), confirm_map=…, max_total=4000,
seed=20260922)`, called twice per symbol (`confirm_map={60:(),240:()}` and `{60:(240,),240:()}`, same
seed so the confirm pair is paired by construction), deduplicated by `strategy_id`, then doubled
into an `rth_only` pair with `_id=None` and an arm-id uniqueness assertion.

| | MES | MNQ | total |
|---|---|---|---|
| distinct rule sets after dedup | 3,011 | 2,952 | 5,963 |
| **× 2 `rth_only` arms = POPULATION** | **6,022** | **5,904** | **11,926** |
| of which **60m** (the surviving cell) | **4,168** | **3,868** | **8,036** |
| of which 240m (withdrawn) | 1,854 | 2,036 | 3,890 |

### Census removals

| cell | n | removed (VOID) | % | live |
|---|---|---|---|---|
| **MES 60m** | 4,168 | **96** | **2.30%** | 4,072 |
| MES 240m | 1,854 | 1,014 | 54.69% | 840 |
| **MNQ 60m** | 3,868 | **688** | **17.79%** | 3,180 |
| MNQ 240m | 2,036 | 902 | 44.30% | 1,134 |
| **MES all** | 6,022 | **1,110** | **18.43%** | 4,912 |
| **MNQ all** | 5,904 | **1,590** | **26.93%** | 4,314 |

**MNQ: 1,590 of 5,904 = 26.93% removed**, which independently reproduces R1's **27.4%** from a
different sample (max_total 400 vs 4,000), a different group set (the symbol's research profile vs
all 13 templates), a different store (`data/archive` vs `csv/raw`) and a different timeframe set.
Two independent measurements 0.5 points apart.

### `openinterest`, which is MNQ's and not MES's

| | MES | MNQ |
|---|---|---|
| carries a VOID `openinterest` condition | **0** | **610** (10.33% of the population) |
| removed by `openinterest` **and nothing else** | 0 | **538** |
| at 60m | 0 | **424** (106 per arm-cell × 4) |
| at 240m | 0 | 186 (93 × 2) |

**MES's zero is a property of its research profile, not of MES.** MES's profile admits VWAP,
VOLUME_PROFILE, MEAN_REVERSION, PULLBACK, REVERSAL, LIQUIDITY, MULTI_TIMEFRAME and **neither
MOMENTUM nor BREAKOUT**, which are the only two templates offering the `openinterest` group. MNQ's
profile admits both. So the entire 60m gap between the two dead rates (2.30% vs 17.79%) is
`openinterest` plus `opening_range_fade`, and it comes from the *search design*, not from the tape.

### Full cause attribution

| cause group | MES carriers | MES sole cause | MNQ carriers | MNQ sole cause |
|---|---|---|---|---|
| `multitimeframe` at 240m | 400 | 400 | 504 | 432 |
| `profile` at 240m | 590 | 582 | 288 | 248 |
| `openinterest` | 0 | 0 | **610** | **538** |
| `liquidity` (`opening_range_fade`) | 128 | 120 | 296 | 264 |

1,102 of MES's 1,110 and 1,482 of MNQ's 1,590 are killed by exactly one cause group, so the causes
are close to disjoint and each removal count is nearly its own marginal cost.

### The census is not a prediction — it is verified

**300 census-removed strategies were run through the harness on each symbol and took 0 trades.**
`[measured: stage1 census_falsification, MES 300 → 0, MNQ 300 → 0]` So every strategy the census
removed is genuinely structurally zero-trade, and "we measured absence" is distinguishable from
"the detector never fired" for this population by measurement rather than by argument.

### And beyond the census, the AND-collapse

| | MES | MNQ |
|---|---|---|
| population | 6,022 | 5,904 |
| removed by census (cannot fire) | 1,110 | 1,590 |
| **ran and took zero trades** | **3,224** | **2,713** |
| produced at least one trade | **1,688 (28.0%)** | **1,601 (27.1%)** |
| cleared IS n ≥ 30 | 275 | 254 |
| cleared IS n ≥ 30 **and** IS expectancy > 0 | **50** | **83** |

At 60m specifically, 1,203 of MNQ's 3,180 live strategies traded (37.8%) and 398 of 1,134 at 240m
(35.1%). So roughly **72–73% of everything generated never produced a single trade under this rule**,
for two distinct reasons that must not be pooled: one class could never fire, the other could and
did not.

---

## 4. Deflation, using EF6's module rather than a hand derivation

`EF6/code/deflation.py::threshold(n, 718.88)`:

| n | free_t | required annualised Sharpe on 1.968 yr |
|---|---|---|
| **MNQ 60m population, 3,868** | **4.065** | **2.897** |
| **MES 60m population, 4,168** | **4.083** | **2.910** |
| both symbols at 60m, 8,036 | 4.241 | 3.023 |
| MNQ all, 5,904 | 4.167 | 2.970 |
| MES all, 6,022 | 4.172 | 2.974 |
| EF6-H3's assumed swing-60m cell, ~465 | 3.505 | **2.498** |
| one pre-registered hypothesis | 1.177 | 0.839 |

**EF6-H3's 2.498 assumes a cell of ~465 screened variants. Mine is 3,868–4,168 per symbol, so my
row faces 2.897–2.910, not 2.498.** Quote whichever matches the search that actually happened; the
difference is 0.4 t-units and the honest number is the larger one.

**Two things worth saying rather than printing.** The span is doing real work for once: the
programme-wide requirement was a Sharpe of 5.82 on 0.88 years, mine is **2.90** on 1.97 years — a
factor of two, from 2.2× the span and a ~1,500× narrower search. It is still not a Sharpe that
exists in futures. And **narrowing further is nearly worthless**: n = 40,000 gives 4.60 and
n = 1,000 gives 3.72, so a fortyfold change in search width costs 0.88 t-units. There is no version
of this cell where trimming the population rescues a row. The only lever with real leverage is the
1.177 floor, which requires the hypothesis fixed in writing before looking, and **no row here has
earned it** because every row was selected from a search.

---

## 5. The harness — mine, EF1's, and what happened between them

### The finding, and how it was got

Told I could not report a profitability number until EF1's harness validated, I built my own rather
than idle, then ran **both engines over the same 400 live MES 60m all-hours strategies on the same
`SymbolFrame`** and audited both with **EF1's own `violations()`**.

| engine | trades | `violations()` | max hold | holds > 22 h |
|---|---|---|---|---|
| `SessionWindowEngine`, EF1's first build | 3,717 | **43 `SPANS_WINDOW`** | **71.0 h** | **19** |
| `SessionEngine`, mine | 3,734 | **0** (strict, no carve-out) | 21.0 h | 0 |

Worst case, from EF1's own audit output: `MES-60m-044e20ad3af2`, entry 2024-12-24 11:30, exit
2024-12-26 15:00 — 71 hours across two 16:00 deadlines. Cause: `classify_bar` is a pure function of
one bar (deliberately, for prefix invariance), so a session whose last bar is `OUTSIDE` has no bar
for the flat to fire on. **19 of 507 sessions at 60m, identically on MES and MNQ**, every one a US
holiday or early close. The grid audit cannot catch it: `bars_on_boundary = 488` and
`bars_in_window = 493` are both non-zero, so the rule looks armed.

Reported as `msgs/EF3-01_EF1_session-rule-misses-early-close-sessions.md`, with the 19 dates, the
mechanism, the property I traded away to fix it, and the fix I thought kept both properties (drive
the deadline from `timeutil.MARKET_HOLIDAYS_2025_2027` rather than from the neighbouring bar).

### Round 2 — EF1 fixed it and the two engines converged

EF1 added `session_end_indices` (component 1b), grouping by **ET calendar date**.
`[measured: same 400 strategies, same frame → both engines 3,734 trades, both 0 violations, both max
hold 21.0 h, both 0 holds > 22 h]` I then rebuilt `SessionEngine` as a **subclass of
`SessionWindowEngine`** so every fill convention, counter and audit is EF1's and the delta is one
flag: `enforce_session_gap=False` reproduces EF1 exactly.

### What I adopted from EF1, and what I did not — recorded because three implementations now exist

| EF1 component | adopted? | note |
|---|---|---|
| gap-honest `IN_WINDOW` fill at `bar.open`, and not letting a post-deadline bar's high/low move the stop check or the excursions | **YES**, by inheritance | fired 0 times in my cell (`flats_in_window = 0`), because entries are vetoed and the flat lands on the previous bar |
| re-label a flat that gapped through the stop as `ExitReason.STOP` | **YES**, by inheritance | fired **4** times on MES and **22** on MNQ across the full runs |
| `assert_hooks_reachable()` | **YES**, re-exported from `ef3_session` | passes on the current `engine.py` |
| market-order slippage on the flat | **YES**, by inheritance | the stock engine fills `SESSION_CLOSE` at `bar.close` with **zero** slippage (`engine.py:467,473,476`) and the flat is 38.6–49.0% of exits here, so inheriting that would have understated the cost of the programme's defining rule on four or five exits in ten |
| `classify_bar` as a pure one-bar function | **kept, and extended** | I add `trading_day(bars[i+1].ts) != trading_day(bars[i].ts)`. Reads one bar of the future — its **timestamp only, never its prices**. Exact, at the cost of prefix invariance at a session's last bar. |
| `session_end_indices` by ET calendar date | **kept, and it is not sufficient** | see below |

**The residual difference, and it bites.** EF1 groups by ET calendar date; I group by CME
`trading_day`. Mine catches **9 further bars per symbol**, all `23:00 ET` on a holiday eve —
2024-11-27, 2025-01-19, 2025-02-16, 2025-11-26, 2026-01-18, 2026-02-15, 2026-04-02, 2026-06-18,
2026-07-02 — where the archive's pre-holiday overnight ends at midnight ET and does not resume until
the next evening. On the 400-strategy probe none of the 9 bit. **On the full population they fired
63 times on MES and 135 times on MNQ** (`forced_flats`), i.e. EF1's current rule would carry 198
positions across a 16:00 deadline that mine flattens. That is the one place I believe my engine is
still more correct than EF1's, and it is measured, not argued.

### Do I consider my engine correct?

**Yes, for 60m on this substrate, with three stated caveats.** Evidence: **0 violations under EF1's
own `violations()` with no carve-out over the full live population on both symbols** (4,912 MES and
4,314 MNQ strategies, 103,191 trades); max hold **21.0 h** on both, **0 holds above 22 h**; and the
`entries_vetoed_in_window` counter agrees exactly with my independent `blocked_fills` count. Caveats:

1. **Not prefix-invariant at a session's last bar.** The right fix is a calendar, not a neighbour.
2. **Not valid at 240m or 1440m** — §0, and EF1 raises `SessionGridError` on a daily grid.
3. **The `enforce_session_gap=False` arm is a sensitivity, not a second opinion.** It reproduces
   EF1, which I believe under-enforces by 198 positions.

### Harness facts that follow from the rule and remove a dimension each

* **`TIME` exits = 0 of 103,191 trades.** §2.
* **`rth_only=True` caps the hold at 6.5 hours and so forbids the regime.**
  `StrategyFilters.rth_only` defaults to **True** (`base.py:393`) and is True in both MES's and
  MNQ's research profile. It gates entries, not holding, so with it on the only legal entries are
  09:30–16:00 and the position must be flat at 16:00 the same day. **The 22-hour window the
  programme exists to measure is unreachable with `rth_only=True`.** Both arms are in my population
  and the pair is the central comparison of the swing cell. EF2 reached this independently
  (`msgs/EF2-01_EF1_…`) — and *that* is corroboration, because EF2 is on different symbols and the
  claim is about the code, not the tape.
* **Window slicing is exact in this cell.** Only **17 of 53,252 MES trades (0.032%)** and **2 of
  49,939 MNQ trades (0.004%)** straddle the IS/OOS cut, because no position can span more than 22
  hours. Measured against 300 true-windowed runs per symbol, the sliced and true expectancies agree
  to **0.0 at 5 decimal places on every pair**, and the trade counts agree exactly. The prior
  programme's 2.47% straddle rate is reduced ~77×. So every window in my analysis is a slice of one
  run and that costs nothing — which is a genuine, if unglamorous, gift from the session rule.

### Engine counters, full population, for whoever resumes

| counter | MES | MNQ |
|---|---|---|
| entries vetoed, fill bar in [16:00,18:00) | 9,965 | 12,213 |
| flats on boundary | 20,563 | 23,832 |
| flats forced by EF1 component 1b | 617 | 655 |
| **flats forced by EF3's `trading_day` clause** | **63** | **135** |
| flats in window (the gap branch) | 0 | 0 |
| flats re-labelled STOP (gapped through) | 4 | 22 |
| stale fills (> 3 base bars after the signal) | 1,038 | 1,523 |
| violations under EF1's strict audit | **0** | **0** |
| trades | 53,252 | 49,939 |
| `SESSION_CLOSE` / `STOP` / `TARGET` / `BREAKEVEN` / `TIME` | 21,176 / 23,005 / 5,136 / 3,935 / **0** | 24,465 / 18,669 / 3,468 / 3,337 / **0** |
| median hold | 2.0 h | 3.0 h |

---

## 6. Anti-overfitting: what I checked and what I found

| risk | how checked | found |
|---|---|---|
| **dead conditions / false nulls** | full 79-condition census at both bindings, both symbols, **then falsified** by running 300 census-removed strategies per symbol | 1,110 MES / 1,590 MNQ removed; **0 trades** from the removed samples, so the census is verified not assumed |
| **look-ahead across the session deadline** | EF1's `violations()` (`ENTRY_IN_WINDOW`, `EXIT_IN_WINDOW`, `SPANS_WINDOW`) over the full population, **no carve-out** | **0** on both symbols |
| **look-ahead at a window boundary** | straddle count + 300 true-windowed runs per symbol against the sliced ledger | 0.032% / 0.004% straddle; sliced vs true expectancy identical to 5 dp on every pair |
| **repainting / future-data leakage** | every condition evaluated through `frame.snapshot(i)`, the same path the engine uses; placebo scripted conditions key on `snap.ts`, not on an index | clean; `CONDITION_ERRORS` empty in all four census cells |
| **D48 arm collision** | `_id=None` on every `dataclasses.replace`, plus `alt.strategy_id != st.strategy_id` per pair and `len(ids)==len(set(ids))` over the whole emitted population | both assertions pass on both symbols |
| **D28** | no comparative claim is routed through `T.ab`; the paired real-minus-placebo test in `ef3_rank.py` is a paired t plus a sign test, named in the code | n/a — not yet run |
| **survivorship / roll splicing (D40 shape)** | signed simultaneous-step test: bars where **both** symbols moved > +3× their own median bar, against the 7 third-Friday roll dates in span; plus the largest bar within ±4 days of each roll | **no evidence of an unadjusted splice.** The near-roll extremes are **mixed sign** (2024-12-18 −21.7×/−17.5×, 2025-03-18 −18.8×/−18.4×, 2025-12-16 −15.7×/−13.2×) and coincide with identifiable macro events; a vendor splice would be a same-signed step on the same bar every quarter. Cannot prove absence — a ~20 pt (MES) / ~140 pt (MNQ) calendar spread sits inside the p99 session gap (60 / 340 pts) — so the exposure is **bounded**: 7 candidate boundaries in 11,287 bars = 0.06%, and `ef3_audit.py::roll_exposure` counts the affected trades |
| **understated costs** | `engine._close` charges commission only in `cost_r`; slippage is in the prices. The flat now carries market-order slippage (EF1). `ef3_audit.py::cost_sensitivity` recovers `risk_points` from `gross_r − net_r` and gives exact **double-commission** and **+1 tick on every flat exit** arms with no re-run | arms implemented, **not yet run** |
| **unrealistic fills** | entry = fill bar's **open** + adverse slippage; `stop_before_target_in_same_bar = True`; `honour_gaps = True`; a fill that gapped past the stop is refused | repo defaults are the pessimistic ones; the same-bar and favourable-slippage audits in `ef3_audit.py` are **not yet run** |
| **parameter sensitivity** | `ef3_audit.py::sibling_families` groups the population by (group, tf, signal set, confirm_tfs, rth_only) and reports the fraction of siblings positive — the test that returned median 0.0 at MES 60m in `RANKING_FINDINGS.md` | implemented, **not yet run** |
| **data-mining bias** | search size recorded exactly (§3) and threshold taken from EF6's module (§4) | free_t 4.065 / 4.083; required Sharpe 2.897 / 2.910 |
| **insufficient sample** | IS trade-count gate at 30, with n ≥ 20 as a declared sensitivity only | 275 MES / 254 MNQ clear n ≥ 30; **50 / 83** also have IS expectancy > 0 |
| **placebo** | `newstrats/placebo.py`, `placebo_random` + `placebo_shuffle` gated on, `placebo_shift` computed and **never gated on** because it leaks (D42) | cohort builder wired, **not yet run** |

---

## 7. Why there are no ranked rows

Three reasons, in order of finality.

1. **The 240m half of my cell does not exist** (§0). That is half the assignment, gone to
   arithmetic.
2. **No profitability number was reportable.** My instruction was explicit: not until EF1 said its
   harness was trustworthy. EF1 fixed the defect I found and then parked without declaring
   validation, so the gate never opened. The numbers are computed and on disk
   (`out/stage1_*_gap.json` carries the full trade ledger, 103,191 trades) and are **embargoed**,
   not lost.
3. **The control arm was never run**, and a row without its placebo is not reportable by my own
   pre-registered protocol (burst 04) and by the EDGE_BRIEF's first guardrail. I will not hand over
   a table that fails my own gate.

**What I would have handed over is very likely a short list or an empty one**, and the prior says so
before the data does: on the index complex the best placebo ranked 1st in 12 of 16 cells, 96 of 160
top-10 slots were placebos, and the one-sided p that reals beat placebos at the top was never below
0.109. That prior is the reason the placebo column mattered more than the expectancy column, and it
is the reason not running it leaves nothing publishable rather than something provisional.

## 8. The thing that must survive into every conclusion

**MES and MNQ are one index complex.** They share **44 of ~9,250 rule sets at 60m (0.5%)** and
**108 of ~14,000 at 240m (0.8%)** — D14/D41. So "the same strategy works on both" is not merely
unreliable, it is **not available**, and agreement between them is **not corroboration** because the
underlying is the same. If a row ranks on both, that is **one observation, not two**.

My own census is a live demonstration and should be cited as one: every VOID verdict in §2 is
identical on the two symbols, to the bar count in most rows; the 19 early-close dates are identical;
the 9 holiday-eve bars are identical; `bars_on_boundary` is 488 on both. That agreement is the same
instrument answering twice. **The one place the two symbols genuinely differ — the D45 floor rate,
15.38% vs 7.47% — differs because of `min_stop_ticks` and price scale, i.e. the contract spec, not
the tape.** And the other large difference, the 60m dead-condition rate (2.30% vs 17.79%), is a
property of the two research profiles, not of the two markets.

---

## PARKED 2026-09-27

For a reader arriving cold. Nothing below needs any other file to be understood.

### What the cell is now
**SWING, MES and MNQ, 60m only.** The 240m arm is **withdrawn and cannot be revived**: the window is
22 h = 1,320 min, `1320 = 2³·3·5·11`, and 240 divides it 5.5 times. 5/15/30/60/120 align; 240 does
not. Arithmetic, not implementation. My own burst 01 had measured the symptom — the 240m bucket
labelled 16:00 spans 16:00→20:00 and straddles both the flat and the reopen on 585 of 3,050 bars
(19.2%) — and my engine comparison found the `SPANS_WINDOW` violations concentrated there. I read it
as the early-close bug. It was also the grid.

### Population and exact size
Built by `code/ef3_population.py`, seed **20260922**, `max_total=4000`, groups = each symbol's own
research profile, frame `[60, 240]` on a 60m base. Full id manifest in
`out/population_ids_4000.json`.

* **MES 6,022** (3,011 rule sets × 2 `rth_only` arms), of which **4,168 at 60m**.
* **MNQ 5,904** (2,952 × 2), of which **3,868 at 60m**.
* Total **11,926**; **8,036** at 60m.
* Thresholds from `EF6/code/deflation.py`, span 718.88 d: **MES 60m free_t 4.083, required annual
  Sharpe 2.910; MNQ 60m free_t 4.065, Sharpe 2.897.** EF6-H3's headline 2.498 assumes a cell of
  ~465; mine is eight to nine times that, so **2.90 is my number, not 2.498**. Do not quote 5.46.

### Firing-rate census, per cell, and what it removed on MNQ
All 79 conditions, every base bar, bindings 60 **and** 240, both symbols. `CONDITION_ERRORS` empty.

| cell | population | removed as VOID | % | live |
|---|---|---|---|---|
| **MES 60m** | 4,168 | 96 | **2.30%** | 4,072 |
| **MNQ 60m** | 3,868 | 688 | **17.79%** | 3,180 |
| MES 240m *(withdrawn)* | 1,854 | 1,014 | 54.69% | 840 |
| MNQ 240m *(withdrawn)* | 2,036 | 902 | 44.30% | 1,134 |
| **MES total** | 6,022 | **1,110** | **18.43%** | 4,912 |
| **MNQ total** | 5,904 | **1,590** | **26.93%** | 4,314 |

**On MNQ specifically: 1,590 of 5,904 removed = 26.93%, reproducing R1's 27.4% independently.** Of
those, **610 carry a VOID `openinterest` condition (10.33% of the whole MNQ population) and 538 are
removed by `openinterest` and nothing else** — **424 of them at 60m**. MES loses **zero** to
`openinterest`, because its research profile excludes MOMENTUM and BREAKOUT, the only two templates
offering the group. So the whole 60m gap between 2.30% and 17.79% is the *search design*, not the
market.

**The census is verified, not asserted: 300 census-removed strategies per symbol were run and took
0 trades.** Beyond it, a further **3,224 MES / 2,713 MNQ** live strategies ran and took zero trades,
so only **1,688 (28.0%) / 1,601 (27.1%)** of each population produced any trade at all. Keep those
two classes apart — one could never fire, the other could and did not.

### State of my engine, and whether I think it is correct
`code/ef3_session.py::SessionEngine` — a **subclass of EF1's `SessionWindowEngine`** adding one
clause. `enforce_session_gap=False` reproduces EF1 exactly.

**I consider it correct for 60m on `data/archive`.** Evidence: **0 violations under EF1's own
`violations()` with no carve-out**, over 4,912 MES and 4,314 MNQ strategies and 103,191 trades; max
hold **21.0 h** on both symbols; **0 holds above 22 h**; `entries_vetoed_in_window` agrees exactly
with an independently written `blocked_fills` counter. Caveats: not prefix-invariant at a session's
last bar (it reads the next bar's **timestamp**, never its prices — the correct fix is
`timeutil.MARKET_HOLIDAYS_2025_2027`, not a neighbour); not valid at 240m or 1440m.

**Adopted from EF1** (by inheritance, so they cannot drift): gap-honest `IN_WINDOW` open fill;
gapped-flat → `STOP` re-label (fired 4× MES, 22× MNQ); market-order slippage on the flat;
`assert_hooks_reachable`. **Not adopted / extended:** EF1's `session_end_indices` groups by ET
calendar date and misses **9 bars per symbol**, all 23:00 ET on a holiday eve. My `trading_day`
clause caught them **63 times on MES and 135 on MNQ** in the full runs. **This is the one live
disagreement between the two engines and it is the thing to settle first on resumption.**

### Ready to fire the moment a validated harness exists
All of this is written, imports cleanly, and needs no new design decision. Stage 1 is **already
done** — `out/stage1_{MES,MNQ}_gap.json` each hold the full-span trade ledger (53,252 and 49,939
trades) plus every row's identity, so nothing before the control arm needs re-running.

1. `python3 code/ef3_stage2.py MES MNQ` — builds the placebo cohort from
   `workspace/newstrats/placebo.py` for the **50 MES / 83 MNQ** rows that clear IS n ≥ 30 and IS
   expectancy > 0, three kinds per base (`placebo_random` and `placebo_shuffle` honest and gated on;
   `placebo_shift` computed and **never** gated on, because it leaks — D42), and runs them through
   the same engine. ~15 min per symbol at one third of a core.
2. `python3 code/ef3_rank.py MES MNQ` — ranks by **IS expectancy in R** (no composite score, because
   a weighted blend is itself a fitted object), applies gates G1–G4 from `bursts/04`, attaches each
   row's placebo expectancy in IS and OOS, ranks placebos **beside** the reals and reports the best
   placebo's rank against the analytic null `(n+1)/(n_placebo+1)`, runs the paired real-minus-placebo
   test as a paired t plus a sign test (**never** `T.ab` — D28), and runs 5 anchored walk-forward
   folds comparing the selected top 10 against the qualifying universe, the whole live population and
   the placebo cohort. Seconds, from the ledgers.
3. `python3 code/ef3_audit.py MES MNQ` — sibling-family parameter sensitivity, exact
   double-commission and +1-tick-on-the-flat cost arms recovered from `gross_r − net_r`, roll
   exposure, hold and exit distributions. Seconds.

**Three warnings for whoever resumes.** (i) The `rth_only` pair is the central comparison and it is
already built: with `rth_only=True` the maximum hold is **6.5 hours**, so the 22-hour regime is
unreachable and the arm is a control for the regime, not a variant of it. (ii) `time_stop_bars` is
inert here — 0 `TIME` exits in 103,191 trades — so do not read exit-geometry variation as including
it. (iii) Window slicing is exact in this cell (0.032% / 0.004% straddle, sliced vs true identical
to 5 dp), so every fold can be a slice of the one run already on disk.

### The sentence that must not be lost
**MES and MNQ share 0.5–0.8% of rule sets. Agreement between them is one observation, not two.**
Every VOID verdict in my census is identical on both symbols, to the bar count — that is the same
instrument answering twice, and it corroborates nothing. The only genuine differences I found are
`min_stop_ticks`/price scale (the D45 floor, 15.38% vs 7.47%) and the two research profiles (the
60m dead rate, 2.30% vs 17.79%). Neither is a fact about the two markets.
