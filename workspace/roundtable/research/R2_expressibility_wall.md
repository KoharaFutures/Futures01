# R2-D3 — The expressibility wall, and the proxy question

**Track R2 — Relational: second series, curve, calendar, surface.** Researcher R2.
**Opened:** 2026-09-27. Appended to as work proceeds (BRIEF.md hard rule 1).

Marking convention per BRIEF.md rule 3: `[general knowledge]`, `[repo-verified: path:line]`,
`[measured: command -> result]`.

---

## 0. Headline: there are TWO walls, not one, and they unlock different families

The manager pre-registered the risk that this track's answer is near-trivially "one `SymbolFrame`
per backtest" (DIVISION §6, Track R2, "Hardest"). That is true and it is also *not the wall*. The
one-frame signature is a **consequence**; there are two independent structural walls underneath it,
and conflating them is why Class II looks uniformly hopeless when it is not.

| | wall | what it blocks | cost to remove | Class II families it unlocks |
|---|---|---|---|---|
| **A** | **One `FeatureSnapshot` per symbol.** A condition can see one symbol's path and nothing beside it. | Every *relational signal*, even when the trade is a single outright leg. | ~8 named, mostly additive edits. Signature `ConditionFn` survives untouched. | **6** with data already on disk; **4 more** with a zero-code-change Yahoo pull. |
| **B** | **One instrument per position.** `Strategy.symbol`, `StrategySignal.symbol`, `_OpenPosition`, `BacktestEngine.spec` and the R unit are all scalar. | Every trade that *is* a spread: two legs, two tick grids, two round turns, a leg ratio. | New multi-leg position + `SpreadSpec` + leg-ratio object + R redefined on the spread. Structural, not additive. | **5**, and none of them without A as well. |

Wall A is cheap and buys six families. Wall B is expensive and buys five. **That asymmetry is the
finding**, and it means this repo's correct next move on Class II is Wall A alone — a relational
*signal* layer on a single traded leg — not a spread backtester.

---

## 1. Wall A, located exactly

### 1.1 The sentence that is the wall

`futures_agents/features.py:687` — the docstring of `FeatureSnapshot`:

> `"""Everything known about one symbol at one instant, across all timeframes."""`

`[repo-verified: futures_agents/features.py:685-713]` The dataclass carries `symbol: str` as a
**scalar** field (features.py:690) and `tfs: Dict[int, TFSnapshot]` keyed by **timeframe only**
(features.py:693). There is no key on which a second symbol could hang. The axis of extension the
author built is *timeframe*; the axis of extension Class II needs is *instrument*, and it does not
exist.

### 1.2 The signature that enforces it

`futures_agents/strategies/base.py:87`:

```
ConditionFn = Callable[[FeatureSnapshot, int], ConditionResult]
```

`[repo-verified: futures_agents/strategies/base.py:86-87]` Every one of the 79 conditions
(DIVISION Appendix A) is a function of exactly `(one-symbol snapshot, one timeframe)`. There is no
parameter through which a partner series could be passed. This is the enforcement point: even if
two `SymbolFrame`s were loaded side by side in a runner, no condition could read the second one.

### 1.3 The entry points, as the manager predicted

`[repo-verified: futures_agents/backtest/engine.py:548]` `run_backtest(frame: SymbolFrame, strategy: Strategy, *, ...)`
`[repo-verified: futures_agents/backtest/engine.py:554]` `run_portfolio(frame: SymbolFrame, strategies: Sequence[Strategy], *, ...)`
`[repo-verified: futures_agents/backtest/engine.py:231-233]` `BacktestEngine.__init__(self, frame: SymbolFrame, ...)`, and then `self.frame = frame; self.spec: ContractSpec = frame.spec`.

DIVISION Appendix B fact 5 is confirmed at the lines it claims. `[measured: sed -n '548p;554p' futures_agents/backtest/engine.py -> both signatures begin "frame: SymbolFrame"]`

`[repo-verified: futures_agents/backtest/engine.py:266]` `run_many` opens with `bars = self.frame.base.bars` — the loop clock is one symbol's bar list. Anything relational must be aligned *to that clock*, which is why the alignment map in §1.5 below is the look-ahead-critical part of the change, not the signature.

### 1.4 The loader, one CSV deep

`[repo-verified: futures_agents/research/runner.py:71-74]`

```python
def _frame(symbol: str, horizon: str):
    suffix, base_min, tfs = HORIZONS[horizon]
    series = load_csv(f"csv/raw/{symbol}_{suffix}.csv", symbol, base_min)
    return series, build_symbol_frame(series, tfs), tfs
```

One symbol, one file, one frame. This is the natural place a partner would enter and today cannot.

### 1.5 The silent-wrong-answer trap nobody has hit yet, because nobody has tried

`[repo-verified: futures_agents/strategies/base.py:118-120]` `Condition.evaluate` memoises on
`key = (self.name, tf)`, and `[repo-verified: futures_agents/backtest/engine.py:284]` `run_many`
allocates one such cache per bar: `cache: Dict[Tuple[str, int], ConditionResult] = {}`.

So a hypothetical relational condition `ratio_extreme` bound to MGC-vs-MCL and the same condition
bound to MGC-vs-MES **collide on the same cache key**, and the second binding silently receives
the first's answer. There is no exception, no zero, no log line — the strategy simply tests a pair
it was not configured for. This has the exact shape of D38 (`toolkit.measure_custom` silently
zeroes custom conditions): a feature that appears to work and reports a number that means
something else.

**Therefore the cache key is not an optional part of the change. It is part of the minimum.** Ship
Wall A without it and the repo acquires a new defect class rather than a new capability.

`Condition` already has the right idiom to copy: `[repo-verified: futures_agents/strategies/base.py:104-106]` `bind(timeframe)` returns `replace(self, timeframe=timeframe)` and `[repo-verified: futures_agents/strategies/base.py:154-155]` `label` renders it as `name@tf`. A `partner: Optional[str]` field with a `bind_partner()` and a `name@tf:PARTNER` label is a two-line extension of an existing pattern.

---

## 2. The precise named change — eight edits, in dependency order

Stated as named functions and signatures, as requested. Every edit is **additive**: no existing
call site changes, which matters because `[measured: grep -rln "run_portfolio\|run_backtest\|BacktestEngine(" --include=*.py . | wc -l -> 57]` — 57 files reference the backtest entry points. A breaking signature change is a 57-file refactor; a keyword-only default is zero files.

| # | file:line | change | breaking? |
|---|---|---|---|
| A1 | `futures_agents/features.py:685` (`FeatureSnapshot`) | add field `partners: Dict[str, "FeatureSnapshot"] = field(default_factory=dict)` and accessor `def partner(self, symbol: str) -> Optional["FeatureSnapshot"]`. Amend the docstring at :687 — it is the wall's plainest statement. | no |
| A2 | `futures_agents/features.py:795` (`SymbolFrame.__init__`, :798) | add keyword-only `partners: Sequence["SymbolFrame"] = ()`; store `self.partners: Dict[str, SymbolFrame]`. Reject a partner whose `base.minutes` is **coarser** than `self.base.minutes` (the mirror of the existing guard at `features.py:808-810`, which already raises on a timeframe finer than the source). | no |
| A3 | `futures_agents/features.py` (new, modelled on `_build_alignment` at :828) | `def _build_partner_alignment(self) -> Dict[str, List[int]]` — primary base-bar index → index of the last **closed** partner bar at or before that bar's timestamp; `-1` where none. **This is the causality-critical edit.** `_build_alignment`'s own docstring (`features.py:829-832`) states the invariant to copy: "index of the last COMPLETED bar", `-1` means none had closed yet. | no |
| A4 | `futures_agents/features.py:1004` (`SymbolFrame.snapshot`) | populate `partners=` by calling each partner frame's `snapshot(aligned_idx)` at the A3 index. Skip where the index is `-1`. | no |
| A5 | `futures_agents/strategies/base.py:91` (`Condition`) | add `partner: Optional[str] = None` and `def bind_partner(self, symbol: str) -> "Condition"` mirroring `bind` at :104. Extend `label` (:154) to render it. | no |
| A6 | `futures_agents/strategies/base.py:120` | cache key `(self.name, tf)` → `(self.name, tf, self.partner)`. **Mandatory, see §1.5.** Also widen the `cache` type hints at `base.py:110` and `engine.py:284`. | no (key is internal) |
| A7 | `futures_agents/backtest/engine.py:231` (`BacktestEngine.__init__`) | nothing required if partners ride inside the frame via A2. `self.spec = frame.spec` (:233) stays **deliberately** — the traded instrument remains one contract. This is the scoping decision that keeps Wall A cheap. | no |
| A8 | `futures_agents/research/runner.py:71` (`_frame`) | add a partner-loading path: `partners: Sequence[str] = ()` → load each `csv/raw/{p}_{suffix}.csv` and pass to `build_symbol_frame`. Also `futures_agents/features.py:1050` (`build_symbol_frame`) needs the same passthrough. | no |

**`ConditionFn` at `base.py:87` does not change.** That is the whole reason this is cheap: the
second series rides *inside* the object conditions already receive. All 79 existing conditions keep
working untouched; relational conditions are new functions that call `snap.partner("SPY")`.

**What still has to be got right and is not a signature:** the 79 existing conditions must not
start reading partners by accident, and the partner snapshot must never be fresher than the primary
bar. Two series with different session calendars make this non-trivial — `[repo-verified: futures_agents/config.py:239-252]` the ETF specs carry `globex_open="04:00", globex_close="20:00"` while `[repo-verified: futures_agents/config.py:45-46]` the futures default is `globex_open="18:00", globex_close="17:00"`. A partner bar must be selected backwards-only (last closed at or before), never nearest, or the repo acquires look-ahead bias by interpolation. The existing `tests/test_features.py` suite already encodes exactly this invariant for timeframes (`test_no_aligned_bar_ends_after_the_base_bar_it_is_aligned_to`, `test_aligned_bar_contains_no_base_bar_that_had_not_closed`) `[repo-verified: tests/test_features.py:36,91]` — the partner-alignment test is a copy of those with the axis swapped.

---

## 3. Wall B, located exactly — why Wall A does not buy you a spread

Wall A buys *relational signals on one traded leg*. It does not buy a spread **position**, and the
blockers are all downstream of the signal:

| blocker | path:line | why a spread needs more |
|---|---|---|
| `Strategy.symbol: str` | `futures_agents/strategies/base.py:552` | scalar; a crack spread is three symbols |
| `StrategySignal.symbol: str`, single `entry`, single `stop`, `targets: List[float]` | `futures_agents/strategies/base.py:499-503` | one instrument, one price ladder. A spread needs per-leg entry/stop or a synthetic spread price with its own tick grid |
| `_OpenPosition` | `futures_agents/backtest/engine.py:159` | one instrument's lifecycle state |
| `BacktestEngine.spec = frame.spec` | `futures_agents/backtest/engine.py:233` | one `tick_size`, one `point_value`, one `CostModel(self.spec)` (:235). A 3:2:1 crack charges three round turns, on three different tick grids |
| R measured on one notional contract | `futures_agents/backtest/engine.py:22-25` (module docstring): *"measures everything in R ... with a notional one contract"* | a spread's R is the *spread's* stop distance in spread points; leg ratios convert that into per-leg contract counts |
| **no leg-ratio object anywhere** | `[measured: grep -rn "leg_ratio\|legs\|LegSpec\|SpreadSpec" --include=*.py futures_agents/ -> no match]` | 3:2:1 crack, 2:1:1 crush, 1:1 calendar, ~80:1 gold/silver are the *definition* of these families |
| `ContractSpec` has no expiry, no contract month, no curve position | `futures_agents/config.py:22-53` — fields are symbol, name, exchange, tick_size, point_value, currency, costs, session times, `is_micro`, `full_size_symbol`, `micro_symbol`, `correlation_group`, `min_stop_ticks`, `typical_atr_points` | a calendar spread is *defined* by two expiries of one root; the object cannot name a second expiry |

`correlated_symbols()` `[repo-verified: futures_agents/config.py:285-295]` is the closest thing the
repo has to a relational map — and it returns **a list of strings**. It never returns, loads or
aligns a frame. Its docstring says it exists for "correlated-exposure limits", i.e. the risk layer
(R3's lane), not for relational signals.

**Wall B is not required for any of the 6 families in §5.** It is required for II-1, II-2, II-4,
II-6-as-a-true-pair and II-15. That is the cost/benefit line round 2 should price.

---

## 4. What is NOT a wall, contrary to the pre-registration

`[repo-verified: futures_agents/data/yahoo.py:100-116]` `ticker_for()` passes through any symbol
starting `^` or containing `=` **untouched**, with the docstring "so a caller can reach an index or
an FX pair without this table growing to cover every instrument on the vendor." And
`[repo-verified: futures_agents/data/yahoo.py:86]` the daily interval's lookback cap is
`timedelta(days=365 * 25)` — twenty-five years.

So `RB=F`, `HO=F`, `ZM=F`, `ZL=F`, `SI=F`, `^VIX`, `^TNX`, `^GSPC`, `DX-Y.NYB` are reachable by the
existing module **with zero code change**. The data side of the inter-commodity-spread block is a
fetch call, not a build project. Whether each ticker actually returns bars is untested — I did not
pull vendor data this round (DIVISION §8 forbids it without assignment) — and Yahoo's documented
habit of returning an empty frame with no error (`yahoo.py:16-19`) means "reachable by the code" is
not "verified to have history". **That is a one-command round-2 assignment, and I recommend it.**

The genuinely unobservable-on-this-vendor item is a **per-expiry ticker**. `=F` is a continuous
front-month series. Whether Yahoo serves `CLZ26.NYM`-style single-expiry symbols at all is
`[general knowledge, low confidence]` — historically unreliable coverage. Until it is tested,
II-1 and II-2 are **unobservable**, and that half of the manager's pre-registration stands.

---

## 5. Per-family proxy ledger — the cheapest *valid* proxy, or the named reason there is none

Rule applied: a proxy is **valid** only if it preserves the family's *mechanism*. A proxy that
preserves the correlation but not the mechanism is named and rejected, because the tempting ones are
the dangerous ones.

| family | cheapest valid proxy in this repo | verdict |
|---|---|---|
| **II-1** calendar spread | **NONE.** The tempting one is the spliced grain series (D40) — `MZC/MZS/MZW` roll between contract months inside one CSV, so a roll *is* visible in this data. **Invalid:** a splice is a discontinuity in one series, not two simultaneously observable expiries. You can see that a roll happened; you can never see the spread, because the two legs never coexist on the same bar. | no proxy |
| **II-2** carry / roll yield | **NONE valid.** The tempting one is the `MCL`-vs-`CL` pair in `data/archive/` — both energy, different series. **Invalid:** those are the same expiry at two contract sizes, not two points on the curve; their spread is a size/vendor artefact (BRIEF: 0.95c mean, 4c worst across 109 hourly bars), not a carry signal. | no proxy |
| **II-3** basis / index arb | **YES, and the data is on disk.** `SPY_1d` vs `MES_1d` and `QQQ_1d` vs `MNQ_1d` `[measured: per-file span scan, §6]` overlap 2019-05-03 → 2026-09-18 ≈ 1,850 aligned daily bars. Valid as a *rich/cheap* signal; **invalid** as index arb proper (SPY is an ETF with its own NAV premium and creation/redemption mechanics; the futures fair value needs financing and dividends, neither present). Needs Wall A. | proxy: ETF-vs-futures ratio |
| **II-4** crack / crush / ratio | **NONE on disk.** No RB, HO, ZM, ZL or SI series exists `[measured: ls csv/raw data/archive]`. Wheat-corn (`MZW`/`MZC`) is the only inter-commodity pair present and is excluded by D40. **But the vendor reaches all of them with zero code change** (§4). | proxy after a fetch, not before |
| **II-5** inter-market | **YES.** `MGC_1d` vs `MES_1d` (gold vs equity) and `MGC_1h` vs `MCL_1h` on disk. **Invalid** for the canonical rates-vs-equity and dollar-vs-metals versions: no ZN, no DX, no FX series exists. | partial proxy |
| **II-6** statarb / cointegration | **YES for the signal.** Any of the pairs above. **Invalid** as a market-neutral pairs *trade* without Wall B: a one-legged "ratio is stretched, buy the cheap leg" is a directional bet with a relational filter, not a spread, and its risk is the leg's own risk. Say so or the backtest reports a spread's Sharpe on an outright's variance. | proxy: one-legged, and label it |
| **II-7** cross-sectional momentum | **YES, degraded.** Rank the 4-symbol universe and use the rank as a *filter* on one traded leg. **Invalid** as cross-sectional carry (needs the curve) and structurally underpowered as cross-sectional momentum: the canonical version ranks 40-60 markets; here N=4 and `[repo-verified: futures_agents/config.py:107-125]` MES/MNQ/ES/NQ share `correlation_group`, so the effective cross-section is closer to **2** (index complex, metals) than to 4. | proxy, but N≈2 |
| **II-8** lead-lag between contracts | **YES, cleanest of all.** One traded leg, partner used only as a signal. ES/NQ/MES/MNQ/SPY/QQQ overlap. **Caveat, not invalidation:** D14/D41 — they are one complex, so a lead-lag result is a statement about microstructure within a complex, and agreement between them is not corroboration. | proxy: intra-complex only |
| **II-9** correlation regime | **YES.** Rolling correlation of two on-disk series as a filter. Fully valid — correlation regime *is* the mechanism, and no second expiry or surface is needed. | full |
| **II-10** seasonality | **Needs no second series at all.** See §7 / R2-D4 in the main file — this family is mis-cut into Class II. | expressible today, in part |
| **II-11** scheduled events | **Needs no second series.** `econ_calendar.py` supplies it deterministically. | expressible today, in part |
| **II-12** unscheduled news | **NONE.** A headline feed is not a recurrence rule, and `econ_calendar.py:8-10` says so itself: *"Scraped headlines cannot answer that question for the past without look-ahead."* The tempting proxy — a large gap or a volume spike — is **invalid**: it is the *reaction*, so conditioning on it is conditioning on the outcome. | no proxy, and the tempting one is circular |
| **II-13** inventory / fundamental | **NONE.** No EIA/WASDE number, only the *timing* of the release. The tempting proxy — using the post-release price move as the surprise — is **invalid** for the same circularity. | no proxy |
| **II-14** options-informed / GEX | **NONE.** No strike, no open interest, no IV. The tempting proxy — round-number pinning as a stand-in for max pain — is **invalid**: round numbers attract price for reasons unrelated to dealer gamma, so it cannot discriminate the hypothesis. | no proxy |
| **II-15** delta-neutral / gamma scalping | **NONE.** Requires an options book to be neutral *against*. Not a data gap that a proxy closes. | no proxy |
| **II-16** volatility as an instrument | **NONE on disk.** No VX series. **Invalid tempting proxy:** realised volatility of the traded series is RV, and the entire family is about the *spread* between IV and RV — using RV for both sides measures zero by construction. `^VIX` is vendor-reachable; VX *term structure* needs per-expiry tickers (§4, untested). | no proxy; partial after a fetch |
| **II-17** COT / open interest | **NONE.** `[repo-verified: futures_agents/config.py:22-53]` `ContractSpec` has no OI field and `[measured: head -1 csv/raw/*.csv \| sort -u -> open_time,open,high,low,close,volume]` the bar has no OI column. The library's two `openinterest` conditions are the proxy question and belong to R1's audit (Appendix A; R1's OPEN_QUESTIONS Q2 reports they return `no()` on every bar). | no proxy |
| **II-18** carry-conditioned trend | **NONE.** The conditioning variable *is* the curve slope. Without a second expiry the filter has no input; what remains is unconditioned trend, i.e. Class III. | no proxy |
| **II-19** macro-regime overlay | **NONE valid on disk.** No rates, no dollar, no inflation series. A `MGC/MES` ratio is a *risk-appetite* proxy at best and cannot separate "rate cycle" from "inflation regime" from "liquidity" — three different overlays collapsing to one number. `^TNX`/`DX-Y.NYB` are vendor-reachable. | no proxy; partial after a fetch |

**Count:** 6 families have a valid proxy from data already on disk (II-3, II-5, II-6, II-7, II-8,
II-9) and all 6 require Wall A. 2 more (II-10, II-11) need no second series and are partly
expressible **today**. 3 become proxy-able after a zero-code-change vendor fetch (II-4, II-16,
II-19). 8 have **no valid proxy at any price** (II-1, II-2, II-12, II-13, II-14, II-15, II-17,
II-18) — and for 4 of those the tempting proxy is not merely weak but **circular or
zero-by-construction**, which is the more useful thing to have written down.
