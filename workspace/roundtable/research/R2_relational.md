# R2 — Relational: second series, curve, calendar, surface

**Track R2.** Researcher R2. **Opened:** 2026-09-27. Appended to as work proceeds (BRIEF.md rule 1).
Companion file: `workspace/roundtable/research/R2_expressibility_wall.md` (R2-D3).

Marking per BRIEF.md rule 3: `[general knowledge]` / `[repo-verified: path:line]` /
`[measured: command -> result]`.

**Headline, up front, so it is not buried.** The manager pre-registered that this track's answer
risks being the one sentence "one `SymbolFrame` per backtest". That sentence is true
(`engine.py:548,554`) and it is the *wrong* wall. There are **two** walls, they cost very different
amounts, and they unlock disjoint sets of families:

- **Wall A — one `FeatureSnapshot` per symbol** (`features.py:687`, `base.py:87`). Eight additive
  edits, no breaking signature change. Unlocks **6** Class II families using data already on disk,
  **3 more** after a vendor fetch that needs zero code change.
- **Wall B — one instrument per position** (`base.py:552,499`; `engine.py:159,233`). A new
  multi-leg position object, a leg-ratio object, per-leg costs, R redefined on the spread.
  Unlocks **5**, none of them without A too.

And **two of my nineteen families need no second series at all** (II-10 seasonality, II-11
scheduled events) — which is my answer to "was Class II mis-cut": yes, in one specific place. See
§"Was Class II mis-cut".

---

## R2-D0 — The data inventory, measured (this is the substrate for everything below)

`[measured: for f in csv/raw/*.csv; do n=$(( $(wc -l < "$f") - 1 )); first=$(sed -n '2p' "$f" | cut -d, -f1); last=$(tail -1 "$f" | cut -d, -f1); printf "%s %s %s %s\n" ...; done]`

**`csv/raw/` — 48 files, 11 distinct symbols.** Span extremes, the ones that bind Class II:

| symbol | finest | daily? | longest span measured |
|---|---|---|---|
| MGC | 1m | `MGC_1d` 2511 bars | **2016-09-26 → 2026-09-21** (10.0y) |
| MES / MNQ | 1m | `*_1d` 1859 bars each | **2019-05-03 → 2026-09-21** (7.4y) |
| SPY / QQQ | 5m | `*_1d` 2512 bars each | **2016-09-21 → 2026-09-18** (10.0y) |
| MCL | 1m | **none** | `MCL_1h` 5000 bars, 2025-10-14 → 2026-09-22 (**11.3 months**) |
| ES / NQ | 5m | none | `*_1h` 5000 bars, 2025-11-03 → 2026-09-18 |
| MZC / MZS / MZW | 1m | none | `*_1h` ~5000 bars; **excluded, D40 splice** |

Every intraday file is capped at 5,000 bars, so `MGC_1h`, `MES_1h`, `MNQ_1h`, `MCL_1h` are all
~11 months. DIVISION Appendix B facts 1-4 confirmed as stated.

**`data/archive/` — 29 JSONL series, and it adds no new market.**
`[measured: ls data/archive/ -> 4 symbols (MCL, MES, MGC, MNQ) x 7 timeframes (1m,5m,15m,30m,60m,240m,1440m) = 28, plus CL_1440m]`

That is the single most important negative in this deliverable: **the 157k-bar pull extended the
history of the same four contracts. It did not add a second observable.** Verifying the BRIEF's
instruction to test "we cannot get a second series" rather than assume it: for *cross-market*
purposes the archive is empty-handed; the second series that exists is in `csv/raw/`
(SPY/QQQ/ES/NQ), and it was there all along.

Two things the archive *does* add that matter to me
`[measured: per-file head/tail ts scan over data/archive/*.jsonl]`:

1. **`CL_1440m.jsonl`: 6,192 daily bars, 2002-02-05 → 2026-09-25 — 24 full years of crude.**
   This is by a wide margin the longest series in the repository and it is the *only* data that
   makes a crude seasonality question answerable at all (see R2-D4). `MCL_1440m.jsonl` holds
   **exactly 1 row** `[measured: wc -l data/archive/MCL_1440m.jsonl -> 1]`, confirming the BRIEF's
   "MCL has no daily history on this vendor".
2. **`MGC_1440m.jsonl`: 4,008 bars from 2010-10-04 — 16 years**, six years longer than
   `csv/raw/MGC_1d.csv`.
3. 240m series exist here (2,990-3,052 bars back to 2024-10-06) and nowhere in `csv/raw/`.

**Timezone trap for any cross-store work:** `csv/raw` stamps are UTC
(`2016-09-26T04:00:00+00:00`) and `data/archive` stamps are Eastern
(`2002-02-05T00:00:00-05:00`) `[measured: head -1 of each]`. Aligning the two stores naively by
string is a 4-5 hour shift on every session boundary.

---

## R2-D4 — Seasonality feasibility, with the power arithmetic

Seasonality is the family where "we have ten years of daily bars" is routinely mistaken for 2,500
observations. It is not. **An annual effect over ten years is ten observations.** Measured counts:

`[measured: python3 -c "... distinct years with >200 bars, distinct (year,month), distinct ISO weeks per daily series ..."]`

| series | bars | **full years** | distinct months | distinct ISO weeks |
|---|---|---|---|---|
| `data/archive/CL_1440m` | 6192 | **24** | 296 | 1286 |
| `data/archive/MGC_1440m` | 4008 | **15** | 192 | 833 |
| `csv/raw/MGC_1d` | 2511 | **9** | 121 | 522 |
| `csv/raw/SPY_1d` / `QQQ_1d` | 2512 | **9** | 121 | 522 |
| `csv/raw/MES_1d` / `MNQ_1d` | 1859 | **6** | 89 | 387 |
| `data/archive/MES_1440m` / `MNQ_1440m` | 1863 | **6** | 89 | 387 |
| **MCL (any store)** | — | **0** | — | — |

### The independent-observation count and verdict, per sub-family

The threshold is not arbitrary: programme-wide `free_t = 5.46` (BRIEF). To clear it you need
`|effect| / SE = 5.46`, i.e. a standardised effect size `d = 5.46 / sqrt(n)`. I report both that and
the much softer `t = 2.0` bar, because the gap between them is itself the finding.

| sub-family | what one observation is | best n here | d needed @ free_t=5.46 | d needed @ t=2.0 | verdict |
|---|---|---|---|---|---|
| **Annual / month-of-year** | one instance of that month in one year | **24** (CL), 15 (MGC), 6 (MES/MNQ) | 1.11 (CL) / 1.41 / 2.23 | 0.41 / 0.52 / 0.82 | **Unanswerable.** A d of 1.11 on monthly returns does not exist in a liquid market `[general knowledge]`. Even the soft bar needs d=0.41 on a single calendar month. |
| **Time-of-month / turn-of-month** | one month | **296** (CL), 121 (MGC), 89 (MES/MNQ) | 0.32 / 0.50 / 0.58 | 0.12 / 0.18 / 0.21 | **Borderline, CL only.** The only annual-cycle variant with a real n, and it is on the symbol whose micro has no daily data. |
| **Day-of-week** | one week | **1286** (CL), 522 (MGC), 387 (MES/MNQ) | 0.15 / 0.24 / 0.28 | 0.056 / 0.088 / 0.102 | **Answerable — the one seasonal question this repo is powered for.** |
| **Expiry week** | one expiry | **0** | — | — | **Unobservable.** No contract-month label on any bar `[measured: header scan]`; no expiry field on `ContractSpec` `[repo-verified: config.py:22-53]`. |
| **Roll window** | one roll | **0** (D40 splices are the only visible rolls, and they are a defect) | — | — | **Unobservable.** |
| **Intraday time-of-day** | one session | ~250/yr | small | small | **Already settled, not mine to reopen** — BRIEF rules 5 and 6. |

### Three further things that kill most of what survives

1. **Overlap, not independence.** A "September effect" tested on MGC and on MES is not two
   independent tests: `[repo-verified: futures_agents/config.py:107-125]` MES/MNQ/ES/NQ share
   `correlation_group`, and D14/D41 measured 0.5-0.8% shared rule sets across the index complex.
   Pooling symbols to buy n buys correlated n, which buys almost nothing.
2. **CL is a spliced continuous series.** `CL=F` is a front-month continuous quote with no
   contract-month label — structurally the same object D40 excluded the grains for. A seasonal mean
   measured on it includes the roll's step changes. So the 24 years are 24 years of *a series that
   contains roll artefacts at seasonal frequency*, which is the worst possible confound for a
   seasonal test. **Stated plainly: the one dataset with enough years is the one dataset whose
   construction is confounded with the thing being measured.**
3. **CL is not MCL.** BRIEF: 0.95c mean / 4c worst divergence over 109 overlapping hourly bars.
   For *fills* that disqualifies substitution. For a *calendar-effect sign and magnitude* it is
   defensible, because the underlying economics are identical — but it must be declared, and any
   result must be labelled a CL result, not an MCL one.

### Expressibility of the one answerable question

Day-of-week is expressible **today**: `[repo-verified: futures_agents/strategies/base.py:392]`
`StrategyFilters.days_of_week: Optional[FrozenSet[str]]`, gated at
`[repo-verified: base.py:421]`, fed by `[repo-verified: futures_agents/features.py:697]`
`FeatureSnapshot.day_of_week`.

It has **never been varied by anything that generates strategies.**
`[measured: grep -rn "days_of_week" --include=*.py . | grep -v __pycache__ -> 12 hits: the dataclass field, the passes() check, label(), the identity docstring, one test, and prose in workspace notes. Zero in combinator.py. Zero in any generator.]`
R3 independently established the general form of this (their A-5: one distinct
`StrategyFilters` identity across 314 generated strategies) and I cite rather than re-derive it;
what is mine is the consequence for II-10 specifically.

There is **no month, day-of-month, week-of-month or quarter field** on `StrategyFilters`
`[repo-verified: base.py:389-396, eight fields, none calendrical beyond day-of-week]`. The date is
nonetheless *on* the snapshot — `[repo-verified: features.py:702]` `trading_day: Optional[date]` —
so a month filter is a new `Condition` reading `snap.trading_day.month`, not a new data object.
**Cost: one condition function, ~10 lines, no schema change.** That it has never been written is
the finding, and given the power table above the honest recommendation is *not to bother*: the
sub-families a month filter would serve are the unanswerable ones.

---

## R2-D5 — Event inventory against the repo's own calendar

### What the calendar holds, measured

`[measured: python3 -c "from futures_agents.econ_calendar import ECON_RULES; ..." -> total rules 11; by impact {'HIGH': 6, 'MEDIUM': 5}; LOW: 0]`

| impact | rule | pattern | at (ET) | scope |
|---|---|---|---|---|
| HIGH | US CPI | business_day=8 | 08:30 | market-wide |
| HIGH | US Nonfarm Payrolls | empsit | 08:30 | market-wide |
| HIGH | US Core PCE | business_day=-1 | 08:30 | market-wide |
| HIGH | FOMC Statement | fomc | 14:00 | market-wide |
| HIGH | FOMC Press Conference | fomc_presser | 14:30 | market-wide |
| HIGH | EIA Crude Oil Inventories | eia_weekly | 10:30 | **`("MCL","CL","MNG","NG")`** |
| MEDIUM | US PPI | business_day=9 | 08:30 | market-wide |
| MEDIUM | US Initial Jobless Claims | weekly Thu | 08:30 | market-wide |
| MEDIUM | US Retail Sales | business_day=11 | 08:30 | market-wide |
| MEDIUM | US GDP | business_day=-2 | 08:30 | market-wide |
| MEDIUM | ISM Manufacturing | business_day=1 | 10:00 | market-wide |

**Prior work I am citing rather than repeating:** `research/confluence/news_macro.md` (2026-09-22)
already audited these rules date-by-date and already ranked ten missing releases with add/do-not-add
verdicts. R2-D5's job is therefore only the **delta**: the movers DIVISION §3 names that that report
does not cover, plus the structural finding below.

One item from that report is now **resolved and should be marked so**: it states *"`features.
SymbolFrame._build_news_proximity` must pass `symbol=self.symbol` for MCL backtests to see it — I
did not make that change"*. It was subsequently made — `[repo-verified: futures_agents/features.py:971-972]`
`project_events(start, end, symbol=self.symbol)`. Also: that report's claim *"this repo contains no
real market data … `data/samples/` is empty"* is now false (48 CSVs + 29 archive series), another
instance of the stale prose the BRIEF warns about.

### The structural finding: the HIGH calendar is almost entirely outside RTH, and the one test that was run was run on the symbol where it is emptiest

R1's Q3 (OPEN_QUESTIONS) is **confirmed**: `[repo-verified: futures_agents/features.py:972-973]`
the projected list is filtered `if e.impact.rank >= Impact.HIGH.rank` *before*
`minutes_to_high_impact`, `minutes_since_high_impact` and `in_news_blackout` are computed. So the
five MEDIUM rules are invisible to every condition in the library. The count that matters for
expressibility is the **HIGH** count: 6 rules, of which one is symbol-scoped.

Now the arithmetic nobody had done. Counting HIGH events inside the **actual span of each file**,
and splitting by whether they land inside RTH 09:30-16:00:

**Self-correction, recorded rather than hidden.** My first pass used a global 09:30-16:00 RTH window.
That is wrong for two of the four contracts: `[repo-verified: futures_agents/config.py:157 (MGC 08:20-13:30) and :179 (MCL 09:00-14:30)]`
**MGC's RTH is 08:20-13:30 and MCL's is 09:00-14:30**, not the equity session. Re-measured with each
contract's own `ContractSpec.rth_open`/`rth_close` through `timeutil.is_rth`, the result is different
and much more interesting:

`[measured: python3 -c "from futures_agents.econ_calendar import Impact, project_events; from futures_agents.config import get_contract; from futures_agents.timeutil import is_rth, to_et; ... per measured file span, per-contract RTH ..." ->]`

| file | its own RTH | HIGH events | in-RTH events | **distinct in-RTH event DAYS** | which |
|---|---|---|---|---|---|
| `MNQ_1h` | 09:30-16:00 | 46 | 14 | **7** | FOMC only |
| `MES_1h` | 09:30-16:00 | 46 | 14 | **7** | FOMC only |
| **`MGC_1h`** | **08:20-13:30** | 46 | 32 | **32** | **NFP 11, CPI 11, PCE 10** |
| **`MCL_1h`** | **09:00-14:30** | 98 | 57 | **49** | **EIA 49**, FOMC 8 |
| `MES_1d` | 09:30-16:00 | 384 | 118 | 59 | FOMC only |
| **`MGC_1d`** | **08:20-13:30** | 502 | 360 | **358** | PCE 120, NFP 120, CPI 120 |

Four of the six HIGH rules print at **08:30 ET**. That is an hour before the equity open and
**ten minutes after gold's pit session opens.** So:

- On **MNQ/MES**, with `rth_only` defaulting to True `[repo-verified: base.py:393]`, the entire
  high-impact news dimension is **7 FOMC days in eleven months**.
- On **MGC** it is **32 event days in eleven months** and **358 in ten years of daily bars**.
- On **MCL** it is **49 event days in eleven months**, essentially all EIA.

**A comment in the codebase is wrong, and it is in my lane.**
`[repo-verified: futures_agents/features.py:969-971]`: *"Every other HIGH rule prints at 08:30,
before the 09:30 open, so for an rth_only strategy the news dimension was conditioning on four FOMC
days in a hundred and twenty and nothing else."* That is true for MNQ/MES and **false for MGC**,
whose session opens at 08:20. `profiles.py` already knows this about gold in another context
— `[repo-verified: futures_agents/strategies/profiles.py:22-28]` *"MGC is the one that exposes the
old approach. Its pit session opens at 08:20 … every equity-session assumption … was being applied
to a contract whose day is shaped differently"* — and the insight was applied to the opening range
and never to the news calendar.

**This explains a published result rather than contradicting it.**
`research/confluence/reversion_specialist.md` F11 measured that adding `post_news_window` to 50
MOMENTUM strategies cut mean trades from 112.6 to **1.5** and produced zero publishable strategies.
That report's measurement basis is *"MNQ synthetic"* `[repo-verified: research/confluence/reversion_specialist.md:7]`.
MNQ has **7** in-RTH HIGH event days in the whole intraday span. **The 1.5 was determined by the
calendar, not by the strategy.** The family was tested on the one contract where its in-session
sample is near-zero, and never on the two where it is 32 and 49. I am not claiming it works on MGC
or MCL — I am claiming it has never been asked there, which is a different and reportable thing.

Compounding it: `[measured: python3 -c "from futures_agents.strategies.profiles import SYMBOL_PROFILES, profile_for, timeframes_for; ..." -> profiled symbols ['MES','MGC','MNQ']; MCL -> NO PROFILE, tfs None]`
**MCL is the only one of the four contracts with no research profile** in
`futures_agents/strategies/profiles.py:77-157`. The symbol carrying the repo's only in-session
scheduled mover is the symbol the hypothesis-narrowing layer has no opinion about.

### The absent movers DIVISION §3 named, with a cost line each

`news_macro.md` covers OPEC+ (#10, do-not-add) and Treasury coupon auctions (#7, do-not-add). The
rest of DIVISION's candidate list is genuinely absent from both the rules and that report:

| absent mover | rule-derivable? | cost to add |
|---|---|---|
| **Equity-index options expiry** (3rd Friday) | **Yes, exactly.** Pure calendar. | **Near-zero.** Reuses the existing `nth_weekday` pattern `[repo-verified: econ_calendar.py:96,118-128]`: one `CalendarRule("Options Expiry", ..., "nth_weekday", weekday=4, nth=3)`. No new code path. |
| **Quad witching** (3rd Fri of Mar/Jun/Sep/Dec) | **Yes.** | **Near-zero.** Same rule plus `months=(3,6,9,12)` — the `months` field already exists `[repo-verified: econ_calendar.py:102]`. |
| **Index-futures roll date** (Thu before 3rd Fri) | **Yes.** | **Near-zero as a date.** But it is a date without a referent: nothing downstream can act on a roll, because no bar carries a contract month. Adding the rule would create a calendar flag for an event the data cannot show. |
| **Month- / quarter-end rebalancing** | **Yes.** | **Low.** `business_day=-1` already exists and is in use (Core PCE). Quarter-end = `business_day=-1, months=(3,6,9,12)`. |
| **EIA Natural Gas Storage** (Thu 10:30) | **Yes.** | **Low** — clone `eia_weekly` with `weekday=3`, scoped `("MNG","NG")`. Worthless here: no NG series exists in either store. |
| **WASDE** (~12th, 12:00 ET) | **Partly.** USDA publishes a schedule; the day-of-month drifts. | **Medium** — a new pattern, not a reuse. Worthless here: the only grain series are D40-excluded. |
| **Chinese data** (NBS PMI, trade) | **Partly**, but release times are overnight ET and the impact is regime-dependent. | **Medium**, and it would need a second `at` timezone; every rule today is Eastern `[repo-verified: econ_calendar.py:97]` `at: time  # release time, Eastern`. |
| **OPEC+ meetings** | **No** — dates move by announcement. | `news_macro.md` #10: do not add; a wrong rule is worse than an absent one. I agree. |

**The pattern in that table is the finding.** The four cheapest additions (options expiry, quad
witching, month-end, quarter-end) are *pure calendar arithmetic needing no external data at all* —
and they are precisely the four that are missing, while the expensive, data-dependent ones were
either added or correctly declined. The gap is not where acquisition is hard; it is where nobody
looked.

---

## R2-D1 — Class II family catalogue

**One measurement that governs all nineteen entries.**
`[measured: python3 -c "import inspect; from futures_agents.strategies.library import CONDITIONS; print([n for n,c in CONDITIONS.items() if 'symbol' in inspect.getsource(c.fn)])" -> []]`
**Not one of the 79 conditions' source code even contains the word "symbol".** There is no
relational condition group: `[measured: sorted({c.group for c in CONDITIONS.values()}) -> the 19 in
DIVISION Appendix A; none of calendar/spread/basis/curve/carry/intermarket/correlation/seasonal]`.

And a second:
`[measured: python3 -c "... which conditions read the calendar fields ..." -> minutes_to_high_impact: ['no_imminent_release'] FILTER; minutes_since_high_impact: ['post_news_window'] FILTER; in_news_blackout: ['outside_news_blackout'] FILTER; trading_day: []; day_of_week: []]`
**Exactly three conditions read the calendar, all three are FILTERs, and zero conditions read
`trading_day` or `day_of_week`.** The library can *avoid* an event; it can never *trade* one, and it
cannot see the date at all.

---

## II-1 Calendar spreads (expiry-to-expiry), butterflies, condors on the curve

**Mechanism.** The relative price of two expiries of one root is driven by storage cost, financing
and expected supply/demand at each delivery date, not by the flat price. Trading the difference
removes the flat-price beta and leaves a slower, mean-reverting, far lower-variance series whose
drift is the carry `[general knowledge]`.
**Who runs it, at what size.** The core inventory of commercial hedgers, physical trade houses
(Vitol, Trafigura, Cargill), bank commodity desks, and spread-specialist prop firms; in the
financials it is the dominant flow in STIR and Treasury futures. Retail participation is
real but small and concentrated in grain and energy bull/bear spreads. Horizon days to months;
margin is a small fraction of outright because exchanges grant inter-month credits `[general knowledge]`.
**Where it lives.** Every physically-delivered future with a term structure: CL, NG, ZC/ZS/ZW, GC,
and the STIR complex. Daily and hourly; not a sub-minute product — the spread does not trade with
enough resolution for that outside the exchange-listed spread book.
**Minimum data.** **Two simultaneously quoted expiries of the same root, each bar labelled with its
contract month**, or the exchange's own listed spread quote. Plus each leg's tick size and the
inter-month margin credit.
**How it is operated.** `[general knowledge]` Screen the whole curve, not one pair: plot the term
structure, identify a kink against the seasonal norm for that week-of-year, enter the pair that is
dislocated (long the cheap month, short the rich), size by spread volatility rather than by leg
volatility, and hold to convergence or to a calendar stop (the date at which the thesis's supply
event resolves). Invalidation is a *fundamental* change — an inventory build, a refinery outage —
not a price level, which is why practitioners use time stops and level stops together. Reported
shape: high hit rate (often 60-75%), small average win, occasional very large loss when a squeeze
runs the front month; i.e. a short-gamma-looking distribution.
**How it dies.** Front-month squeezes and delivery-period dislocations. The characteristic death is
the April 2020 WTI negative settle: a spread that had been mean-reverting for a decade re-priced by
more than its entire historical range in two sessions. Regime that kills it: a shift from
contango to steep backwardation (or the reverse) driven by a physical constraint the carry model
does not contain.
**Expressibility here.** **INEXPRESSIBLE-DATA**, and it is the strong form — *unobservable*, not
merely unexpressed. `[measured: head -1 csv/raw/*.csv | sort -u -> open_time,open,high,low,close,volume]`
no contract-month column; `[repo-verified: futures_agents/config.py:22-53]` `ContractSpec` has no
expiry, contract-month or curve-position field; `[repo-verified: futures_agents/data/yahoo.py:100-116]`
`ticker_for` produces `ROOT=F`, the continuous front-month quote, and the repo's only per-expiry
artefact is the D40 splice defect. Even given the data it would then be
**INEXPRESSIBLE-ARCHITECTURE** twice over: Wall A (`features.py:687`) and Wall B (`base.py:552`,
`engine.py:159,233`).
**Already tested here?** No. Nothing in `scan_reports/`, `workspace/studies/` or
`research/backtests/` mentions a calendar spread. The manager's pre-registration that the only
visible roll in this data is a defect (D40) is **confirmed**.

## II-2 Carry / roll-yield harvesting; contango-vs-backwardation positioning; term-structure slope

**Mechanism.** In backwardation a long position rolls into a cheaper contract and earns positive
roll yield; in contango it bleeds. Sorting markets by the sign and steepness of their front slope
and going long the backwardated, short the contangoed, is one of the two best-documented
cross-sectional premia in futures `[general knowledge]`.
**Who runs it, at what size.** Systematic CTAs and multi-strategy funds run it as a standalone
sleeve; it is the academic "commodity carry" factor and the design principle behind every
"optimised roll" commodity index (e.g. the enhanced/roll-select indices). Billions of notional,
monthly rebalance, 20-60 markets `[general knowledge]`.
**Where it lives.** Whole-of-universe commodity and financial futures; monthly or weekly bars.
Sessions are irrelevant — this is a settlement-to-settlement factor.
**Minimum data.** **The front and second (or Nth) expiry price for each market on each rebalance
date, with contract-month labels**, plus the days-to-expiry of each so the slope is annualised
comparably.
**How it is operated.** `[general knowledge]` At each rebalance compute annualised slope
`ln(P1/P2) * 365/(d2-d1)` per market, rank, go long the top tercile and short the bottom, weight
inversely to volatility, hold one month, roll on a fixed schedule. Invalidation is the ranking
flipping at the next rebalance — there is no stop in the conventional sense. Reported shape: modest
Sharpe (0.4-0.8 gross over long samples), positive skew absent, heavy left tail during
commodity dislocations.
**How it dies.** Curve-shape regime change and crowding. The 2005-2008 commodity-index inflow
flattened the front of many curves and compressed the premium; roll-yield strategies that had been
paid for a decade stopped paying. Also dies at expiry-cycle dislocations (see II-1).
**Expressibility here.** **INEXPRESSIBLE-DATA (unobservable).** Same evidence as II-1: no second
expiry, and `[repo-verified: config.py:22-53]` no days-to-expiry field to annualise with. The
tempting proxy — `MCL` vs `CL` in `data/archive/` — is two contract *sizes* of the same expiry, not
two curve points; their difference is a vendor/size artefact (BRIEF: 0.95c mean, 4c worst).
**Already tested here?** No.

## II-3 Basis and cash-futures arbitrage; index arbitrage; EFP

**Mechanism.** A future must converge to its underlying at expiry, so the basis is bounded by
financing, storage and dividends. Deviations beyond transaction costs are arbitrage; deviations
within them are a rich/cheap signal about hedging pressure `[general knowledge]`.
**Who runs it, at what size.** True index arb is a bank/HFT business requiring sub-millisecond
latency and a stock-borrow desk; the EFP/basis *market-making* version is a bank rates and equity
finance business. The retail-accessible residue is using basis as a *sentiment* read. Enormous
size, near-zero holding period for the arb; days to weeks for the sentiment version `[general knowledge]`.
**Where it lives.** Index futures vs cash index or ETF; Treasury futures vs deliverable bonds
(cheapest-to-deliver); physical commodities vs the future.
**Minimum data.** For the arb: **both legs quoted simultaneously at tick resolution, plus the
financing rate, the dividend stream and the borrow cost.** For the sentiment version: **two aligned
daily/hourly series, one futures one cash-proxy.**
**How it is operated.** `[general knowledge]` Arb: compute fair value continuously, trade when the
quoted future leaves the no-arb band, hold to convergence, unwind at expiry against cash settlement.
Sentiment version: z-score the futures-minus-ETF ratio, treat a persistently rich future as
long-hedging demand and a cheap one as the opposite, and use it as a filter on an outright.
Distribution for the arb: extremely high hit rate, tiny per-trade edge, capacity-limited; the
sentiment version is a weak filter, not a standalone.
**How it dies.** For the arb, competition and latency — the band narrows until the edge is below
costs. For the sentiment version, an ETF-specific dislocation (creation/redemption stress,
March 2020) makes the proxy diverge for reasons unrelated to futures positioning.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE — and this is the important one, because the
data exists.** `[measured: exact timestamp intersection -> MES_1d x SPY_1d = 1,855 aligned daily bars
(2019-05-03 -> 2026-09-18); MNQ_1d x QQQ_1d = 1,855; MES_1h x SPY_1h = 1,805 of 5,000]`. Note the
hourly figure: the ETF trades a fraction of the future's 23-hour day, so only ~36% of hourly bars
align and this family belongs at daily frequency here. The block is Wall A alone:
`[repo-verified: futures_agents/features.py:687]` one symbol per snapshot,
`[repo-verified: futures_agents/strategies/base.py:87]` `ConditionFn` cannot receive a second.
The *arb* is additionally INEXPRESSIBLE-DATA (no financing rate, no dividends, no tick data) and
`[repo-verified: futures_agents/config.py:227-234]` the repo's own comment warns the ETF specs carry
zero commission and so "flatter their backtests against the micros" — so an ETF leg must never be
costed as traded.
**Already tested here?** No. `SPY`/`QQQ` are carried as single-symbol proxies
`[repo-verified: config.py:227-234]`, never as a partner series.

## II-4 Inter-commodity spreads: crack (CL/RB/HO), crush (ZS/ZM/ZL), spark, gold-silver, wheat-corn

**Mechanism.** A processing spread is the market's quote for a *conversion margin*: the refiner's
crack is the value of products minus crude, the crusher's board crush is meal plus oil minus beans.
It mean-reverts toward the marginal processor's economics because when it is too wide, capacity runs
harder and it compresses; too narrow, capacity shuts and it widens `[general knowledge]`.
**Who runs it, at what size.** Physical refiners and crushers hedging real margin (the dominant
flow, and the reason the spread has an economic anchor at all), commodity-desk prop books, and
seasonal-spread-specialist CTAs. Retail trades it, often badly, via the exchange-listed spread.
Horizon weeks to quarters.
**Where it lives.** Energy: 3:2:1 crack = 3 CL vs 2 RB + 1 HO. Ags: board crush ≈ 1 ZS vs 11 ZM +
0.22·10 ZL in CME's stated convention (commonly traded 10:11:9 in lots). Metals: gold-silver ratio,
no fixed lot ratio, sized by notional. Daily bars; the seasonal structure (summer gasoline, winter
distillate, harvest crush) is the point.
**Minimum data.** **Aligned price series for every leg, and the leg ratio,** plus each leg's tick
size and point value to convert a spread move into dollars. This is the family where the missing
**leg-ratio object** bites hardest.
**How it is operated.** `[general knowledge]` Compute the spread in consistent units ($/bbl for
cracks: RB and HO are $/gal, so ×42). Compare to the same calendar week in prior years — this is a
seasonal-spread family, not a z-score family. Enter when the spread is outside its seasonal band,
scale in, hold through the seasonal turn, exit on the calendar or on a break of the seasonal
envelope. Sizing is by *spread* volatility and the exchange's inter-commodity margin credit.
Reported shape: high hit rate, long holds, occasional large losses at refinery-outage or
weather shocks.
**How it dies.** A capacity shock breaks the economic anchor — a refinery fire, an export ban, an
African-swine-fever demand collapse in meal. The spread then trends for months against the seasonal
prior, and the practitioners who size by historical spread vol are sized for a distribution that no
longer applies.
**Expressibility here.** **INEXPRESSIBLE-DATA today, but the data is one fetch away.**
`[measured: ls csv/raw/ data/archive/]` there is no RB, HO, ZM, ZL or SI series in either store. The
only inter-commodity pair present is wheat-corn (`MZW`/`MZC`), excluded by D40. **However**
`[repo-verified: futures_agents/data/yahoo.py:100-116]` `ticker_for` passes any symbol containing
`=` through untouched, so `RB=F`, `HO=F`, `ZM=F`, `ZL=F`, `SI=F` are reachable with **zero code
change**, and `[repo-verified: yahoo.py:86]` daily lookback is 25 years. Once fetched it is
**INEXPRESSIBLE-ARCHITECTURE** on both walls, plus the missing leg ratio
`[measured: grep -rn "leg_ratio\|LegSpec\|SpreadSpec" --include=*.py futures_agents/ -> no match]`.
**Already tested here?** No.

## II-5 Inter-market and cross-asset relationships (rates vs index, dollar vs metals, risk-on/off)

**Mechanism.** Asset prices share discount-rate and risk-appetite factors, so one market's move
carries information about another's fair value before that market has fully repriced. The trade is
the residual `[general knowledge]`.
**Who runs it, at what size.** Global macro funds (discretionary, largest expression), multi-asset
CTAs, and bank cross-asset strategy desks. Also the most widely *taught* retail framework
("intermarket analysis"), where it is usually operated as a chart overlay rather than a measured
residual. Horizon days to months.
**Where it lives.** ZN/ZB vs ES/NQ, DX vs GC, CL vs the CAD and the airlines, HG vs global growth.
Daily and hourly; the RTH-overlap window matters because the two markets' sessions differ.
**Minimum data.** **Two or more aligned series across asset classes**, ideally with a rate or FX
series, at a common bar clock with a backwards-only alignment rule.
**How it is operated.** `[general knowledge]` Estimate a rolling beta of the traded market on the
lead market, take the residual, and trade the residual's reversion *or* the lead market's impulse
(two opposite trades from the same data — which is why this family needs a stated sign convention or
it is unfalsifiable). Invalidation is a regime change in the beta itself, which is why practitioners
re-estimate rolling and stand aside when the relationship's R² collapses. Sizing by the residual's
own volatility. Reported shape: modest and unstable; the honest version of this family is a *filter*
on a directional trade, not a standalone.
**How it dies.** The correlation flips sign. 2022 is the canonical case: for two decades bonds
rallied when equities fell, and then both fell together for a year. Every risk-on/off overlay
calibrated on the pre-2022 sign was wrong for the whole year.
**Expressibility here.** **PARTIAL, blocked by Wall A.** Data on disk supports *some* of it:
`MGC_1d` vs `MES_1d` (gold vs equity, ≈1,850 aligned daily bars) and `MGC_1h` vs `MCL_1h`
(≈10.5 months). What is lost is the canonical version — **no rates series, no dollar series, no FX
series exists in either store** `[measured: ls csv/raw/ data/archive/]`, even though `ContractSpec`
registers `ZN` and `M6E` `[repo-verified: futures_agents/config.py:254-267]`. So the repo has specs
for instruments it has no data for. Blocked at `[repo-verified: features.py:687]` and
`[repo-verified: base.py:87]`.
**Already tested here?** No — and note `research/backtests/cross_symbol_timeframes.md` is
cross-*symbol* in the sense of *running the same rules separately on each symbol*, which is the
opposite of a relational test. Nothing reads two symbols in one evaluation.

## II-6 Statistical arbitrage: cointegration and pairs, ratio mean reversion, basket vs component

**Mechanism.** If two series share a stochastic trend, their linear combination is stationary, so
its deviation from the long-run mean is a forecast of its own reversal. The trade is
market-neutral by construction, which is what makes a weak signal tradeable at size
`[general knowledge]`.
**Who runs it, at what size.** Equity statarb is a large, crowded, HFT-to-medium-frequency
institutional business; in futures it is smaller and concentrated in related contracts (index
complex, curve points, ETF-vs-future). Horizon hours to weeks.
**Where it lives.** Within a complex (ES/NQ, GC/SI, ZN/ZB), futures vs ETF, basket vs index.
Hourly and daily.
**Minimum data.** **Two aligned series, long enough to estimate a cointegrating relationship and
then to validate it out of sample** — plus, for the trade, the ability to hold two positions.
**How it is operated.** `[general knowledge]` Estimate the hedge ratio (OLS or Johansen) on a
training window; z-score the spread; enter at ±2σ, exit at 0, hard-stop at ±3-4σ or on a
cointegration-test failure; re-estimate the ratio on a schedule (and treat re-estimation as the main
source of overfitting). Sizing equalises the legs' risk, not their notional. Reported shape: high
hit rate (65-80%), small wins, fat left tail when the relationship breaks.
**How it dies.** The relationship was never cointegrated — it was a finite-sample correlation — and
the "reversion" was the two series decoupling permanently. This family has the worst
data-mining-bias profile in Class II: searching k(k-1)/2 pairs and reporting the best is exactly the
multiple-testing failure this repo has already documented programme-wide.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE for the signal (Wall A); INEXPRESSIBLE-
ARCHITECTURE for the trade (Wall B).** Data exists for the signal (see II-3, II-5). Wall B matters
*more* here than anywhere: `[repo-verified: futures_agents/backtest/engine.py:22-25]` the engine
"measures everything in R … with a notional one contract", and
`[repo-verified: base.py:499-503]` a `StrategySignal` has one `symbol`, one `entry`, one `stop`. A
one-legged version is buildable after Wall A but it is **not this family** — it is a directional
trade with a relational filter, and its variance is the leg's, not the spread's. Reporting a
one-legged result as a pairs result would overstate risk-adjusted performance by the ratio of the
leg's volatility to the spread's.
**Already tested here?** No.

## II-7 Cross-sectional momentum and cross-sectional carry across a futures universe

**Mechanism.** Rank a universe on a past-return (or carry) signal and go long the top, short the
bottom. The premium is distinct from time-series momentum: it survives even when the whole universe
is flat, because it is relative `[general knowledge]`.
**Who runs it, at what size.** This is the standard managed-futures factor sleeve — AQR, Man AHL,
Winton and every academic "commodity momentum" paper. Monthly rebalance, 40-60 markets, billions
of notional.
**Where it lives.** A broad multi-sector futures universe. Monthly or weekly; daily is noise for
this family.
**Minimum data.** **N aligned series with N large enough for a cross-section to mean anything, from
sectors that are not each other.** The universe size *is* the data requirement.
**How it is operated.** `[general knowledge]` Monthly: compute 12-1 month returns per market,
volatility-scale, rank, long top third / short bottom third, weight to equal risk, rebalance
monthly, cap sector exposure. No stops — the rebalance is the risk control. Reported shape: Sharpe
0.3-0.7 over multi-decade samples, long drawdowns (2009-2013 was brutal for the whole complex).
**How it dies.** Sector concentration turning the "cross-section" into one bet, and long flat
periods that are indistinguishable from death in real time.
**Expressibility here.** **INEXPRESSIBLE — and uniquely, the binding constraint is not the code, it
is the universe size.** `[measured: ls csv/raw/]` 11 symbols, of which 3 are D40-excluded grains and
2 are ETFs; the futures are MGC, MCL, MES, MNQ, ES, NQ. `[repo-verified: futures_agents/config.py:107-125]`
MES/MNQ/ES/NQ all share an index `correlation_group`, so the **effective cross-section is ≈2
sectors (index, metals) plus one energy series with no daily history.** Even with Wall A and Wall B
removed, a two-sector cross-section is not this family. The one degraded version that is honest — a
cross-sectional *rank filter* on a single traded leg — needs only Wall A.
**Already tested here?** No.

## II-8 Lead-lag between contracts

**Mechanism.** Price discovery is not simultaneous across venues and contracts. The more liquid,
lower-cost instrument moves first and the related one follows within a bounded lag, so the leader's
move is a short-horizon forecast of the follower `[general knowledge]`.
**Who runs it, at what size.** Almost exclusively latency-sensitive HFT and market-making firms —
this is the economic content of cross-venue arbitrage. At retail latency the lag has closed to
sub-millisecond in liquid pairs; what remains tradeable at human speed is *structural* lead-lag
(a whole-session-scale divergence), which is a different and much weaker claim.
**Where it lives.** ES↔SPY↔NQ↔QQQ, full-size↔micro, futures↔cash. Sub-second for the real version;
minutes-to-hours for the structural version.
**Minimum data.** **Two aligned series with timestamps precise enough to resolve the lag being
claimed.** At 1-minute bars a sub-second lead-lag is *definitionally* unmeasurable — the claim and
the resolution must match, and that is the trap in this family.
**How it is operated.** `[general knowledge]` HFT version: quote the follower off the leader's
book, no "trade" as such. Structural version: when the leader breaks a level and the follower has
not, take the follower in the leader's direction with a stop at the follower's pre-break structure,
target the follower's catch-up, time-stop when the catch-up does not come. Reported shape for the
structural version: unstable, and the honest prior is that most of it is a resolution artefact.
**How it dies.** Latency competition closes the lag — the real version dies continuously and is
already dead at human speed in liquid pairs. The structural version dies a different and more
insidious death: it was never there. At a coarse bar size the "lead" is an artefact of which series
printed its last trade nearer the bar boundary, so the measured lag can be entirely a sampling
property. The regime that kills it is a liquidity shift that reverses which contract is the price
leader — micros have at times led their full-size parents during overnight hours.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE (Wall A only) for the structural version;
INEXPRESSIBLE-DATA for the real one** — `[measured: header + finest-file scan]` 1-minute is the
finest bar, so the sub-second lag is unmeasurable in principle here. Data for the structural version
is on disk (ES/NQ/MES/MNQ/SPY/QQQ overlap). **Caveat that must travel with any result:** D14/D41 —
these are one complex, so a within-complex lead-lag finding is a microstructure statement and
agreement between the legs is *not* corroboration.
**Already tested here?** **Cross-timeframe lead-lag within one symbol: yes** — study `s_leadlag`,
`workspace/studies/STRUCTURE_FINDINGS.md`, implemented at `workspace/newstrats/leadlag.py`
`[repo-verified: workspace/newstrats/leadlag.py:1-28, HTF_OF at :42-43]`, which maps timeframe→
timeframe and never a symbol→symbol. DIVISION §5.5 closes that question. **Cross-contract lead-lag:
never tested, and not testable without Wall A.** The distinction is the finding: the repo built the
lead-lag machinery on the one axis it could reach.

## II-9 Correlation-regime trading; correlation breakdown; dispersion

**Mechanism.** Correlation is itself a state variable with persistence and regimes. Strategies
condition on it (a trend-follower wants low cross-correlation for diversification; a pairs trader
needs high correlation to exist) or trade it directly (dispersion: sell index vol, buy component
vol) `[general knowledge]`.
**Who runs it, at what size.** Dispersion is a bank/hedge-fund options business. Correlation as a
*conditioning variable* is universal in institutional risk management and in CTA portfolio
construction. Horizon weeks to months.
**Where it lives.** Index vs components (options); any two futures for the conditioning version.
Daily bars; correlation estimated on 20-120 day windows.
**Minimum data.** Direct trading: **an options surface on the index and on components.**
Conditioning version: **two aligned price series and nothing else** — the cheapest data requirement
in Class II.
**How it is operated.** `[general knowledge]` Conditioning version: rolling correlation over a
window, label HIGH/LOW/BREAKDOWN by percentile against its own history, and gate an existing
strategy on the label. Invalidation is the label changing. Reported shape: it is a filter, so it has
no distribution of its own — its claim is that it reshapes another strategy's.
**How it dies.** Correlation estimates are noisy and window-dependent; a 20-day and a 120-day
correlation routinely disagree in sign at turning points, so the "regime" is partly an artefact of
the window chosen — the classic parameter-sensitivity failure.
**Expressibility here.** **INEXPRESSIBLE-ARCHITECTURE (Wall A only) for the conditioning version —
and it is the single cheapest Wall-A unlock in Class II.** No second expiry, no surface, no
positioning report; two on-disk aligned series and a rolling correlation. The direct
(dispersion) version is **INEXPRESSIBLE-DATA**: no options data of any kind. Note the library has a
`regime` condition group `[DIVISION Appendix A: regime_trending*, regime_ranging*,
regime_matches_direction]` whose labels are computed from **one** series — so "regime" here already
means something narrower than the word does in this family.
**Already tested here?** No. `correlated_symbols()` `[repo-verified: futures_agents/config.py:285-295]`
is the only correlation machinery and it returns **a list of strings** for risk limits, never a
measured correlation.

## II-10 Seasonality: annual, monthly, time-of-month, day-of-week, expiry-week, roll-window

**Mechanism.** Real economic activity is dated — planting, harvest, driving season, heating demand,
quarter-end index rebalancing, tax-year flows — so supply and demand have calendar structure that
is not arbitraged away because the underlying physical or institutional flow is not optional
`[general knowledge]`.
**Who runs it, at what size.** Seasonal-spread specialists (a recognised sub-industry in ags and
energy), commercial hedgers whose own calendar creates the effect, and a large retail/newsletter
following built on historical seasonal charts. The institutional version is almost always seasonal
*spreads* (II-1/II-4), not seasonal outrights, because the spread is where the physical calendar
shows up cleanly.
**Where it lives.** Ags and energy above all; equity indices for the turn-of-month and
quarter-end effects. Daily bars, multi-year history.
**Minimum data.** **Many years of history — the count of *years*, not of bars — and, for the
expiry-week and roll-window variants, contract-month labels.**
**How it is operated.** `[general knowledge]` Build a per-calendar-date (or per-week-of-year)
average across as many years as exist, with each year plotted separately so the reader can see
whether the mean is an average or an artefact of two years. Enter on the seasonal window's start
date, exit on its end date, with a stop sized to the seasonal pattern's own historical adverse
excursion. The disciplined operators require the pattern to have worked in a large majority of
years *and* to have an economic story, precisely because the pattern alone is a data-mining
generator. Reported shape: hit rates quoted as "worked in 13 of the last 15 years", which is a
statement about 15 observations.
**How it dies.** The physical or institutional cause changes and the calendar effect does not
survive it — US shale changed crude's seasonal storage pattern; index-fund flows changed the ag
roll windows. And most of it was never there: the sub-family is the purest data-mining-bias
generator in the whole catalogue, because the number of candidate windows in a year is enormous
and the number of independent years is tiny.
**Expressibility here.** **PARTIAL, and mis-classified — see OPEN_QUESTIONS Q4.** This family needs
**no second observable at all**, so its presence in Class II is a mis-cut. Day-of-week is
expressible **today** `[repo-verified: futures_agents/strategies/base.py:392,421]`; a month or
day-of-month condition is ~10 lines against `snap.trading_day` `[repo-verified: features.py:702]`;
expiry-week and roll-window are **INEXPRESSIBLE-DATA (unobservable)** for want of a contract-month
label. And the power arithmetic in R2-D4 kills every sub-family except day-of-week: best available
n is **24 years (CL), 15 (MGC), 6 (MES/MNQ), 0 (MCL)**, needing d = 1.11-2.23 at `free_t = 5.46`.
**Already tested here?** **No, and never even generated.**
`[measured: grep -rn "days_of_week" --include=*.py . | grep -v __pycache__ -> the dataclass field, the passes() check, label(), the identity docstring, one test, and workspace prose; zero in any generator]`,
and `[measured: no condition in the 79 reads trading_day or day_of_week]`. R3's A-5 established the
general form (one distinct `StrategyFilters` identity across 314 generated strategies); this is the
Class II consequence of it.

## II-11 Scheduled-event trading: pre-positioning, straddle-the-number, fade-the-spike, post-release drift

**Mechanism.** A scheduled release resolves uncertainty at a known instant. Three distinct trades
live there and they are not the same family: (a) selling the pre-event volatility premium, (b)
capturing the initial repricing, (c) trading the *drift* after the print as slower participants
digest it `[general knowledge]`.
**Who runs it, at what size.** (a) and (b) are options and latency businesses respectively — the
number-reaction trade is won in microseconds by firms co-located with the release feed. (c),
post-release drift, is the only one operable at human speed, and it is run by discretionary macro
and by event-specialist retail. Horizon minutes to hours.
**Where it lives.** Index futures around 08:30 and 14:00 ET prints; **crude around the EIA weekly
10:30 ET print**; ags around WASDE at 12:00 ET.
**Minimum data.** **The release calendar (deterministic, projected backwards without look-ahead)**
and bars fine enough to resolve the reaction window. Not the release *value* — that is II-13.
**How it is operated.** `[general knowledge]` Post-release drift: stand aside through the print, let
the first 1-5 minutes establish a range, then trade the break of that range in the direction of the
break with a stop on the other side of it, targeting a multiple of the initial impulse, and flatten
by a fixed time (30-90 minutes) because the drift decays. Invalidation is a failed break back
through the initial range. Fade-the-spike is the mirror and requires the spike to exceed a
volatility-scaled threshold. Reported shape: low hit rate, large payoff for the break version;
higher hit rate and a fat tail for the fade.
**How it dies.** Two ways. The event's impact regime changes (CPI mattered enormously in 2022 and
much less in 2019), and the strategy is short-sample by construction so it cannot detect that. And
sample: at 8-52 events a year, a decade is 80-520 observations of a *mixed* population.
**Expressibility here.** **PARTIAL — and the only Class II family with a genuinely operable path
today, on one specific symbol.** Available: `[repo-verified: features.py:704-713]`
`minutes_to_high_impact`, `minutes_since_high_impact`, `in_news_blackout`, built without look-ahead
from recurrence rules `[repo-verified: features.py:946-1003]`, plus three library conditions. What is
lost: **all three conditions are FILTERs** `[measured: kinds -> FILTER, FILTER, FILTER]` and
`[measured: no condition reads the calendar except those three]` — so the library can *avoid* an
event and never *trade* one. A post-release-drift entry needs one new SIGNAL condition
("`minutes_since_high_impact` between 1 and 5 **and** price breaks the post-print range"), which is
also the D37 sequence problem in miniature. And the MEDIUM rules are invisible:
`[repo-verified: features.py:972-973]` filters to `Impact.HIGH.rank`.
**Already tested here?** **Yes, as a filter, and on the wrong symbol.**
`research/confluence/reversion_specialist.md` F11: `post_news_window` on 50 MNQ MOMENTUM strategies
cut mean trades 112.6 → **1.5**, zero publishable. I do not re-litigate that. What I add is the
measured reason: `[measured: project_events over each file span, split by each contract's OWN RTH ->
MNQ_1h 7 distinct in-RTH event days; MGC_1h 32; MCL_1h 49; MGC_1d 358]`. **The family was tested on
the contract where it has 7 in-session event days and never on the two where it has 32 and 49.**

## II-12 Unscheduled news and headline-driven; latency-sensitive event reaction

**Mechanism.** An unanticipated headline changes fair value discontinuously. The edge is being
faster at parsing it than the market is at repricing `[general knowledge]`.
**Who runs it, at what size.** Machine-readable-news HFT firms with direct vendor feeds (Bloomberg,
Reuters, Dow Jones elementized feeds) and co-location. Holding period: milliseconds to minutes. There
is no human-speed version of the *reaction*; there is a human-speed version of the *aftermath*, which
is II-11(c).
**Where it lives.** Every market, any hour. Tick to 1-minute.
**Minimum data.** **A timestamped machine-readable news feed with entity tagging, aligned to the bar
clock to better than the reaction time being claimed.**
**How it is operated.** `[general knowledge]` Classify the headline, map it to instruments and a
sign, fire immediately, exit within seconds-to-minutes on a fixed time or volatility stop. Reported
shape: very high frequency, small per-event edge, dominated by infrastructure cost.
**How it dies.** Everyone else buys the same feed; the edge is in the parsing latency and it decays
continuously.
**Expressibility here.** **INEXPRESSIBLE-DATA.** The one specific missing primitive: **a
timestamped, entity-tagged news record per bar.** The repo's calendar is explicit that this cannot be
substituted: `[repo-verified: futures_agents/econ_calendar.py:8-10]` *"Scraped headlines cannot
answer that question for the past without look-ahead: you would be reading an article written after
the bar. Recurrence rules can."* And the tempting proxy is **circular**: using a large gap or a
volume spike as the "news" is conditioning on the reaction, i.e. on the outcome.
**Already tested here?** No, and it cannot be.

## II-13 Inventory and fundamental-driven (storage, stocks-to-use, weather, OPEC)

**Mechanism.** Futures price a physical balance. A change in the balance — inventory build, yield
downgrade, export ban — changes fair value, and the market's *surprise* relative to consensus is the
tradeable quantity `[general knowledge]`.
**Who runs it, at what size.** Physical trade houses with proprietary information (vessel tracking,
satellite crop imagery, their own storage), discretionary commodity funds, and fundamental commodity
CTAs. Horizon weeks to quarters. This is where the largest genuine informational edges in commodities
live, and they are bought with research, not with latency `[general knowledge]`.
**Where it lives.** Energy, ags, metals. Weekly to monthly decision cadence.
**Minimum data.** **The fundamental series itself and a consensus expectation to difference it
against** — EIA weekly stocks, USDA stocks-to-use, weather model ensembles, OPEC quotas. Price data
is the *dependent* variable here, not the input.
**How it is operated.** `[general knowledge]` Maintain a supply/demand balance sheet, form a price
view, express it with a time horizon and a level stop that is wide enough to survive noise, size to
conviction, and revise on each data release. Invalidation is the balance changing, not the price
moving. Reported shape: low frequency, long holds, high variance.
**How it dies.** The balance is right and the price does not care for a quarter, and the position is
stopped out of a correct thesis — the classic fundamental-trader death. Also: everyone now buys the
same satellite data.
**Expressibility here.** **INEXPRESSIBLE-DATA.** The one specific missing primitive: **a numeric
fundamental series with a consensus estimate, timestamped at its release instant.** The repo has the
*timing* of the EIA print `[repo-verified: econ_calendar.py:219-221]` and never its value. The
tempting proxy — inferring the surprise from the post-release move — is the same circularity as
II-12.
**Already tested here?** No.

## II-14 Options-informed: gamma exposure / dealer hedging, 0DTE pinning and max pain, skew and risk reversals, IV vs RV

**Mechanism.** Dealers who are short options must hedge in the underlying, and their hedging is
mechanically predictable from the option open interest by strike. Long dealer gamma suppresses
realised volatility around large strikes (pinning); short dealer gamma amplifies moves. Skew and
risk reversals price the *asymmetry* of expected returns, which is directional information not
present in the price path `[general knowledge]`.
**Who runs it, at what size.** Volatility desks and dedicated vol funds run the real version; a
large and growing retail/newsletter industry runs the GEX-level version off vendor dashboards
(SpotGamma, Menthor, and the like). Horizon intraday to weekly; 0DTE flow has made the intraday
version the most-discussed version since ~2022.
**Where it lives.** SPX/SPY/ES above all (that is where the 0DTE open interest is), then NDX/QQQ/NQ.
Intraday; the levels are recomputed daily before the open.
**Minimum data.** **Open interest and implied volatility per strike per expiry, plus a dealer
positioning assumption** (the sign convention — who is long what — is an *assumption*, not data, and
that is the family's weakest joint). For IV-vs-RV: **an implied-volatility series.**
**How it is operated.** `[general knowledge]` Pre-open: compute total gamma by strike, identify the
gamma flip level, the largest positive-gamma strike (the "magnet") and the zero-gamma level. Treat
price above the flip as mean-reverting (long dealer gamma damps moves) and below it as trending
(short gamma amplifies). Use the large strikes as intraday support/resistance, fade approaches to a
big positive-gamma strike, and stand aside in the zero-gamma zone. Exit at the next strike or on a
break of the flip level. Invalidation is price closing decisively through the flip level. Reported
shape: presented as high hit rate near expiry with pinning, and as a regime *label* rather than a
signal the rest of the time.
**How it dies.** The dealer-positioning sign assumption is wrong (customers can be net *sellers* of
calls, flipping the hedging sign), or the open interest moves intraday as 0DTE is transacted, so a
pre-open snapshot is stale by 10:00. And the "levels" are round numbers that would attract price
anyway — so the hypothesis is very hard to separate from a round-number effect.
**Expressibility here.** **INEXPRESSIBLE-DATA.** The one specific missing primitive: **per-strike,
per-expiry option open interest and implied volatility, timestamped daily.** Not one byte of options
data exists: `[measured: head -1 csv/raw/*.csv | sort -u -> open_time,open,high,low,close,volume]`;
`[repo-verified: config.py:22-53]` `ContractSpec` has no options fields. The tempting proxy —
round-number levels as a stand-in for max pain — is **invalid because it cannot discriminate the
hypothesis** (it is the confound, not the signal).
**Already tested here?** No.

## II-15 Delta-neutral futures positioning: futures as the hedge leg, gamma scalping, delta hedging

**Mechanism.** An options position's P&L in the underlying is neutralised with futures, leaving
exposure to volatility rather than direction. Gamma scalping monetises the difference between
realised and implied volatility by re-hedging a long-gamma book as the underlying moves
`[general knowledge]`.
**Who runs it, at what size.** Every options market maker, as the core of the business; volatility
funds; and structured-products desks hedging issued risk. Continuous, size determined by the options
book, not by a directional view.
**Where it lives.** Wherever listed options and a liquid future on the same underlying coexist.
Continuous re-hedging, from seconds to daily depending on the re-hedge rule.
**Minimum data.** **The options position and its greeks, refreshed continuously, plus the future's
price.** The futures leg is *derived*; it has no independent signal.
**How it is operated.** `[general knowledge]` Hold long gamma (long options), re-hedge delta to zero
on a rule — fixed time interval, fixed delta band, or fixed underlying move. Each re-hedge locks in a
small realised-volatility gain; the cost is theta. Profitable iff realised vol exceeds implied over
the holding period net of re-hedge transaction costs. The choice of re-hedge rule *is* the strategy
and it is a variance/cost trade-off, not a direction call. Reported shape: many tiny gains against a
constant theta bleed.
**How it dies.** Realised volatility comes in below implied for a sustained period (the variance risk
premium being *earned by the other side*), or transaction costs at the chosen re-hedge frequency
exceed the gamma capture. And path-dependence: the same realised vol delivered as one gap instead of
many small moves pays nothing.
**Expressibility here.** **INEXPRESSIBLE-DATA.** The one specific missing primitive: **an options
position with greeks.** This is not a data gap a proxy narrows — without a book to be neutral
against, the concept has no referent. Also INEXPRESSIBLE-ARCHITECTURE on Wall B: a hedge leg is a
second position, and `[repo-verified: engine.py:303-308]` the engine refuses a new signal while
positioned and `[repo-verified: base.py:499]` a signal names one symbol.
**Already tested here?** No.

## II-16 Volatility as a traded object: VX term structure, contango roll-down, variance risk premium

**Mechanism.** Implied volatility exceeds subsequent realised volatility on average, because buyers
pay for insurance — the variance risk premium. The VIX futures curve is usually upward-sloping, so a
short VX position rolls down the curve and earns the premium plus the roll `[general knowledge]`.
**Who runs it, at what size.** Volatility funds, tail-risk funds (the other side), and a very large
retail flow through the VIX-ETP complex. Horizon days to months. Institutionally significant and,
notably, one of the few futures strategies with a documented structural reason for a premium
`[general knowledge]`.
**Where it lives.** VX futures, VIX ETPs, variance swaps. Daily.
**Minimum data.** **The VIX index and at least two VX expiries** (to have a slope), with contract
months and days-to-expiry. For the VRP directly: **an implied-vol series and a realised-vol
estimator on the same clock.**
**How it is operated.** `[general knowledge]` Measure the front slope (VX1 vs VX2, or VIX vs VX1).
Short VX1 or a VIX ETP when the curve is in contango beyond a threshold, flatten or reverse in
backwardation; size *small* and cap it, because the loss distribution is the defining feature. Stop
by a hard notional cap rather than a price level — a price stop does not help when the move is a
single overnight gap. Reported shape: a long run of small gains punctuated by catastrophic losses;
5 February 2018 destroyed an entire ETP (XIV) in one session.
**How it dies.** A volatility spike from a low base. The whole family is short a convex payoff, so
"how it dies" is not a regime, it is a single day — and any backtest that has not crossed such a day
has measured nothing about the risk.
**Expressibility here.** **INEXPRESSIBLE-DATA on disk; PARTIAL after a vendor fetch.**
`[measured: ls csv/raw/ data/archive/]` no VX, no VIX. `[repo-verified: yahoo.py:100-116]` `^VIX` is
reachable with zero code change, which makes **IV-vs-RV** reachable (VIX vs realised S&P vol). **VX
term structure is not**: it needs per-expiry tickers, the same unobservable as II-1. And the
tempting proxy for VRP — using realised volatility on both sides — measures **zero by
construction**. Then Wall A for anything relational.
**Already tested here?** No. Note DIVISION §5.1: volatility as a *state of the traded series* is
R3's; this entry is volatility as an *instrument*, which is mine, and the two have no code in common.

## II-17 Positioning and flow data: COT/CFTC, open-interest change taxonomy, commercial vs speculative

**Mechanism.** Knowing who holds what tells you about the *fragility* of a move. A rally on which
speculators are already maximally long has less fuel than one they are short. The open-interest
change taxonomy (price up + OI up = new longs, healthy; price up + OI down = short covering,
suspect) is the oldest formalisation of this `[general knowledge]`.
**Who runs it, at what size.** Discretionary commodity and macro funds as a *context* layer;
newsletter and retail analysis very heavily (the COT report is free and weekly); some systematic
CTAs use COT extremes as a contrarian factor. Horizon weeks.
**Where it lives.** All CFTC-reported US futures. Weekly (COT is Tuesday's positions published
Friday 15:30 ET — a **three-day reporting lag that is itself the main operational constraint**).
**Minimum data.** **Weekly CFTC Commitments of Traders records by category, and per-bar open
interest.**
**How it is operated.** `[general knowledge]` Normalise each category's net position as a percentile
of its own multi-year range ("COT index"); treat a specculative extreme as a contrarian warning
rather than a trigger; combine with price confirmation because the extreme can persist for months.
Never used as a standalone entry by anyone credible, precisely because of the lag and the
persistence. Reported shape: a slow filter, not a signal.
**How it dies.** The category definitions shift (the 2009 disaggregation, the swap-dealer category),
index-fund flows made "commercial" no longer mean "hedger", and extremes persist far longer than any
stop.
**Expressibility here.** **INEXPRESSIBLE-DATA.** Two specific missing primitives: **(1) a per-bar
open-interest value, (2) a weekly CFTC positioning record by trader category.** `[measured: header
scan -> no open_interest column]`. The library nonetheless *has* an `openinterest` condition group
(`oi_price_confirmation`, `oi_expanding*` — DIVISION Appendix A), which is exactly the
name-versus-content problem the BRIEF flags; R1's OPEN_QUESTIONS Q2 reports they return
`ConditionResult.no()` on every bar because `open_interest` is `None`. That audit is R1's
(DIVISION §5) and I cite rather than duplicate it. **Acquisition note:** the CFTC publishes COT as a
public CSV and it is *not* a market-data vendor, so reachability is plausible and untested — a
candidate round-2 one-command check, not a claim.
**Already tested here?** The conditions exist and are structurally null per R1's Q2. The *family* has
never been tested, because the data has never existed.

## II-18 Term-structure-conditioned trend (trend filtered by the sign of carry)

**Mechanism.** Trend-following and carry are weakly correlated premia, and a trend that agrees with
the carry sign has a fundamental tailwind: a long in a backwardated market is paid to wait, a long in
steep contango pays to wait. Conditioning trend entries on carry sign is one of the most durable
documented refinements in managed futures `[general knowledge]`.
**Who runs it, at what size.** Second-generation systematic CTAs; it is a standard published
enhancement to plain time-series momentum. Monthly to weekly, whole-universe.
**Where it lives.** Any future with a curve. Daily/weekly.
**Minimum data.** **The trend signal on the traded series (available here) *plus* the front-curve
slope (not available).** The conditioning variable is the entire relational content.
**How it is operated.** `[general knowledge]` Compute the usual trend signal; compute annualised
front slope; take long signals only where carry is non-negative and short signals only where it is
non-positive; size as in the base trend system. Invalidation and exits are the base system's.
Reported shape: fewer trades, similar-to-better expectancy per trade — i.e. a filter claim.
**How it dies.** Same as the base trend system, plus the extra failure that the carry sign flips
mid-trade and the filter has no rule for an existing position.
**Expressibility here.** **INEXPRESSIBLE-DATA (unobservable).** The one specific missing primitive:
**a second expiry's price with a days-to-expiry label, on the same bar.** Without it the filter has
no input and what is left is unconditioned trend, which is III-1 and R3's. This is worth stating
because II-18 is the *cheapest* real Class II refinement to the strategies this repo already has —
and it is blocked on the one data object the repo has never had any route to.
**Already tested here?** No. Unconditioned trend has been tested exhaustively; the conditioning has
never existed.

## II-19 Macro-regime overlays (rate cycle, inflation regime, liquidity conditions)

**Mechanism.** Asset-class risk premia are conditional on the macro state. The same trend signal has
different expected return in a tightening cycle than in an easing one, so the overlay scales or gates
exposure by regime rather than generating signals `[general knowledge]`.
**Who runs it, at what size.** Global macro funds, risk-parity and multi-asset allocators (the
"regime-based allocation" literature), pension overlay managers. Horizon months to years.
**Where it lives.** Asset allocation, not trade selection. Monthly.
**Minimum data.** **Macro series — policy rate path, inflation prints, a dollar index, a credit
spread, a liquidity measure — each with its correct release timestamp** so the regime label at time
t uses only data published by t. That vintage requirement is the family's hardest data problem and
the most common source of look-ahead bias in published macro-overlay backtests `[general knowledge]`.
**How it is operated.** `[general knowledge]` Label the regime from a small number of slow variables
(growth up/down × inflation up/down is the canonical 2×2), then set per-asset exposure multipliers by
regime. Rebalance monthly. There is no trade-level invalidation; the regime label changing *is* the
exit. Reported shape: it reshapes an allocation's drawdown profile; its expectancy claim is weak and
its sample is tiny — there have been perhaps six or seven distinguishable macro regimes since 1970,
so the honest independent-observation count is single digits.
**How it dies.** Regime labels are assigned with hindsight and revised (GDP and payrolls are revised
for years), so the backtest uses a label the operator could not have had. And n ≈ 7.
**Expressibility here.** **INEXPRESSIBLE-DATA.** The one specific missing primitive: **a macro time
series with release-vintage timestamps.** No rates, dollar, credit or inflation series exists
`[measured: ls csv/raw/ data/archive/]`, though `ContractSpec` registers `ZN` and `M6E`
`[repo-verified: config.py:254-267]` — specs without data. `^TNX` and `DX-Y.NYB` are vendor-reachable
`[repo-verified: yahoo.py:100-116]`, which would give *price-based* proxies but **not vintages**, so
the look-ahead problem survives the fetch. And the tempting single-number proxy (a `MGC/MES` ratio as
"risk appetite") **cannot separate rate cycle from inflation regime from liquidity** — three distinct
overlays collapsing to one series, which makes any result uninterpretable.
**Already tested here?** No.

---

### Catalogue tally

`[measured: count of verdicts written above]`

| verdict | n | families |
|---|---|---|
| EXPRESSIBLE (today, no new data or code) | **0** | — |
| **PARTIAL** (a degraded version is buildable today) | **2** | II-10 (day-of-week only), II-11 (avoid-only, as a filter) |
| **INEXPRESSIBLE-ARCHITECTURE** (data present, code cannot carry it) | **4** | II-3, II-6, II-8 (structural version), II-9 |
| **INEXPRESSIBLE-DATA — data absent but vendor-reachable with zero code change** | **3** | II-4, II-16 (IV-vs-RV arm only), II-19 (price proxies only) |
| **INEXPRESSIBLE-DATA — unobservable, no route from here** | **9** | II-1, II-2, II-12, II-13, II-14, II-15, II-17, II-18, and II-7 (where the binding constraint is **universe size**, not data format) |
| **INEXPRESSIBLE, mixed** | **1** | II-5 (Wall A + missing rates/FX legs) |

**19 families. 2 PARTIAL, 17 blocked.** Of the 17, **4 are blocked by code alone** — the data is
already on disk — and that is the group the manager's pre-registration did not anticipate.

---

## R2-D2 Operating manual

Three programmes real desks run at size, concrete enough to paper-trade. Everything in this section
is `[general knowledge]` unless a path is cited; contract arithmetic is checked against this repo's
own `ContractSpec` where a symbol exists here
`[measured: python3 -c "from futures_agents.config import CONTRACTS; ..." -> CL tick 0.01 pv 1000 tick_val $10.00 rt_cost $14.80 rth 09:00-14:30; MCL tick 0.01 pv 100 tick_val $1.00 rt_cost $2.44; MGC tick 0.1 pv 10 tick_val $1.00 rth 08:20-13:30]`.

### R2-D2a — A calendar-spread / roll-yield programme: WTI front-vs-second

**The instrument.** The spread `CL(front) − CL(second)`, quoted by the exchange as a single tradeable
instrument with its own order book, in $/bbl. Positive = backwardation, negative = contango. One
spread = 1 long leg + 1 short leg, 1,000 bbl each. `[measured: CONTRACTS['CL']]` tick 0.01 = **$10.00
per leg**, so the *spread* moves $10 per cent of a dollar, the same as one outright — the legs do not
double the tick value, they cancel the flat price.

**Leg ratio.** 1:1 in lots. That is the definition of a calendar spread and it is why it is the
cleanest teaching case: no unit conversion, no ratio to get wrong.

**Sizing convention.** Size on the *spread's* recent range, not on crude's. A front/second WTI spread
typically ranges a small fraction of the outright's daily range, so an operator sizing by outright ATR
will be 5-15× oversized. The rule: risk unit = 1× the spread's own 20-day ATR; contracts = risk
budget ÷ (spread ATR × $10 per 0.01 × 100). Never size by margin, because margin is *low* here by
design (next paragraph) and margin-based sizing therefore produces the largest position exactly where
the tail is fattest.

**Margin treatment — the trap.** Exchanges grant inter-month spread credits, so a 1:1 calendar
spread's initial margin is a small fraction of the sum of two outrights. This is correct for a normal
regime and dangerously wrong for a delivery squeeze: the credit reflects historical spread
volatility, and the exchange raises it *after* the dislocation has begun. Operating rule: set your own
notional cap and ignore the margin number entirely.

**Entry trigger.** Not a z-score. Compare the current spread to the same *week-of-year* in prior years
(a seasonal band), and require two things to agree: (1) the spread is outside the historical band for
that week, and (2) a physical reason exists — inventories at Cushing versus the five-year range,
refinery utilisation, or a known export/outage event. Condition (2) is the whole discipline: without
it, condition (1) is a data-mining generator over 52 weeks × N pairs.

**Invalidation.** A *fundamental* change, not a price level: an inventory build that contradicts the
thesis, or the outage ending. Because that is not a price, the operator carries **both** a level stop
(sized at ~2× the spread's ATR, as a disaster stop only) **and** a calendar stop (the date by which
the supply event must have resolved). If the calendar stop hits with the spread flat, exit flat — a
scratch on a spread is a win, because the carry already paid.

**Exit logic.** Scale out as the spread converges toward the seasonal median; take the final third
either at the median or at the roll date, whichever comes first.

**Roll mechanics.** This is the operational core and it is where the money leaks. Never roll the two
legs separately — that is two outright executions and a period of naked flat-price exposure between
them. Roll as a spread-of-spreads (the exchange lists these), or at minimum use a single
spread-market order. Roll **before** the front month enters its notice period: the front leg must be
out before delivery obligations attach. WTI stops trading roughly three business days before the 25th
of the month preceding delivery, and liquidity in the front spread deteriorates well before that, so
the practical roll window is the week prior.

**Return distribution as reported.** High hit rate (commonly quoted 60-75%), small average win, long
holds, and a rare very large loss when the front month squeezes. Short-gamma-shaped. The April 2020
negative WTI settle re-priced front spreads by more than their entire prior historical range in two
sessions, which is the honest prior for the tail.

**Reachability here: zero.** Requires two simultaneously quoted expiries (II-1, II-2). Described so
the catalogue records *what is being given up*, not because it can be run here.

### R2-D2b — An inter-commodity spread end to end: the 3:2:1 crack

**Why the crack and not the crush.** Three reasons, stated because DIVISION asks me to choose and say
why. (1) The crack's leg ratio is a *stated refinery convention* — roughly two barrels of gasoline and
one of distillate out of three of crude — so it has an economic anchor a reader can check, whereas the
board crush's conventional lot ratio (10 ZS : 11 ZM : 9 ZL) differs from its *unit* ratio and teaches
the arithmetic badly. (2) Crude is the one non-index contract this repo actually carries
(MCL), so the crack is the spread closest to its universe. (3) Both missing legs are
vendor-reachable with zero code change (`RB=F`, `HO=F`) `[repo-verified: futures_agents/data/yahoo.py:100-116]`,
whereas crush needs ZM/ZL and relates only to the D40-excluded grains.

**Leg ratio and the unit conversion that ruins most retail attempts.** 3 CL short vs 2 RB + 1 HO long
(for a long-crack, i.e. long refining margin). CL is $/barrel over 1,000 bbl. RB and HO are
**$/gallon over 42,000 gallons**. So to express the spread in $/bbl:

```
crack ($/bbl) = ( 2 * RB * 42  +  1 * HO * 42  -  3 * CL ) / 3
```

Omit the ×42 and the spread is off by a factor of 42; use 3 lots of RB instead of 2 and you are
trading a different product. This single conversion is the most common error in the family.

**Dollar value of a move.** 1 cent on CL = $10/lot; 1 cent/gal on RB or HO = $420/lot. So a $1.00/bbl
move in the computed crack is roughly $3,000 across the 6-lot structure. Size the structure as **one
unit**, on the crack's own volatility, not leg by leg.

**Margin treatment.** CME grants an inter-commodity spread credit for the crack, so initial margin is
materially below the sum of six outrights. Same warning as R2-D2a: the credit is withdrawn after the
regime breaks, not before.

**Entry trigger.** Seasonal, not statistical. The gasoline crack strengthens into the northern-summer
driving season and weakens after; the distillate crack strengthens into winter. The operating form:
plot the 3:2:1 crack against the same week-of-year across as many prior years as available, **each
year drawn separately** so you can see whether the average is an average or two outlier years. Enter
when the current crack sits below the band for that week *and* refinery utilisation or an outage
supports the thesis. Scale in over several sessions — this spread trends before it turns.

**Invalidation.** A capacity event, which is a fundamental, not a level: an unplanned outage (widens
the crack against a short, helps a long), an export policy change, a demand shock. Because the
invalidation is fundamental, the discipline is a **notional cap plus a calendar stop**, with a level
stop at roughly 2× the crack's 20-day ATR purely as a disaster stop.

**Exit logic.** Exit on the seasonal turn date regardless of P&L for the seasonal portion; hold any
fundamental portion to the resolution of the fundamental. Take partials as the crack re-enters its
band.

**Roll mechanics.** All three legs share a monthly cycle but **not the same expiry dates** — products
and crude expire on different schedules. Roll all three together, as one spread transaction, in the
week before the earliest leg's notice period. A partially rolled crack is not a crack; it is a naked
product position with a leftover crude hedge.

**Return distribution as reported.** High hit rate, long holds, occasional large loss at outage or
policy shocks. The tail is on the side that is short the constrained product.

**Reachability here: none today; one fetch and then Wall A + Wall B.** `[measured: ls csv/raw/ data/archive/]`
no RB, HO, ZM, ZL or SI series exists. After a fetch it remains blocked by Wall A
(`features.py:687`) for the signal, Wall B (`base.py:552`, `engine.py:159,233`) for the three-legged
position, and by the absent leg-ratio object
`[measured: grep -rn "leg_ratio\|LegSpec\|SpreadSpec" --include=*.py futures_agents/ -> no match]`.

### R2-D2c — A scheduled-event trade with the actual clock: EIA Weekly Petroleum Status Report

Chosen because it is the **one scheduled mover this repo can already see inside a trading session**:
`[repo-verified: futures_agents/econ_calendar.py:216-221]` `CalendarRule("EIA Crude Oil Inventories",
"EIA", Impact.HIGH, time(10, 30), "eia_weekly", symbols=("MCL","CL","MNG","NG"))`, and
`[measured: per-contract RTH scan -> 49 distinct in-RTH EIA event days in MCL_1h's 343-day span]`.

**The actual clock, in Eastern.**

| when | what | what the operator does |
|---|---|---|
| **Tue ~16:30** | API publishes its own private inventory estimate, after the NYMEX close | This is the market's consensus anchor. Note the sign and size of the API surprise; it sets the *expectation* the EIA number will be measured against |
| **Tue evening → Wed 10:29** | Globex drifts, often in the API's direction | **Stand aside.** Pre-positioning into the print is a coin flip with a gap risk; it is a different (options) trade |
| **Wed 10:30:00** | EIA release | Flat. No position. The first print is won by machines |
| **10:30 → 10:35** | Initial repricing. Violent, wide spreads, thin book | **Do not trade.** Mark the high and low of this window: this is the *event range* and it is the only level the rest of the trade uses |
| **10:35 → 11:15** | The drift window | The trade. Entry = a decisive close beyond the 10:30-10:35 event range, in the direction of the break. Stop = the other side of the event range. First target = 1× the event range projected from the break; runner trailed |
| **by ~12:00** | Drift decays | Time-stop anything still open. The edge claimed for this family is in the first 30-90 minutes, not the afternoon |
| **holiday weeks** | Report shifts to **Thursday** when the week contains a Monday federal holiday | `econ_calendar.py` handles this class of shift via `holiday_shift` on the *federal* calendar `[repo-verified: econ_calendar.py:104-107, and the module docstring's insistence on the federal rather than exchange calendar at :23-32]` |

**Sizing convention.** The event range *is* the risk unit, so position size = risk budget ÷ (event
range × point value). This is the important structural feature: the stop is set by the event's own
realised volatility rather than by a fixed ATR, so the position automatically shrinks on a big
surprise and grows on a small one. On MCL `[measured: CONTRACTS['MCL']]` point value $100, round-turn
cost $2.44, so a 0.30 event range is $30 of risk per lot against $2.44 of cost — a ~12:1
risk-to-cost ratio, which is the minimum an operator should accept before the trade is worth taking.

**Invalidation mid-trade.** Price returning inside the event range and closing there. That is a
failed break, and the failed-break version of this trade (fade back through the range) is a
*different* strategy — do not let one become the other inside a single position.

**Return distribution as reported.** Low hit rate (the break fails often), payoff 2-3:1, and a heavy
dependence on the volatility regime of crude at the time.

**Reachability here: PARTIAL, and this is the single most nearly-buildable Class II family.**
Available: the release clock, without look-ahead `[repo-verified: features.py:946-1003]`, and the
proximity fields `[repo-verified: features.py:704-713]`. Missing, precisely: **a news SIGNAL.**
`[measured: exactly three conditions read the calendar, all three ConditionKind.FILTER]` — so
"5 minutes after the print, break the post-print range" cannot be written as an entry, only as a gate
on someone else's entry. It is also a two-step sequence (establish range → break range), which is
D37. **Cost to build: one SIGNAL condition plus the range primitive, ~30 lines, no schema change and
no new data.**

---

## R2-D6 Options-informed

What a *futures* trader actually does with the options surface, operationally, and then the flat
statement of what survives with zero options data. All `[general knowledge]` unless cited.

### D6.1 Dealer gamma and hedging levels (GEX)

**Operationally.** Before the open, pull option open interest by strike for the nearest expiries on
SPX (or SPY/QQQ), multiply each strike's OI by its gamma and by a dealer-sign assumption (the standard
retail convention: dealers are short puts below spot and short calls above it), and sum. That yields
three numbers used as *levels*, not signals: the **gamma flip** (where net dealer gamma crosses zero),
the **largest positive-gamma strike** (the "magnet"), and the **zero-gamma band**. The operating rule
is a regime label: above the flip, treat intraday moves as mean-reverting and fade extensions toward
the magnet; below it, treat moves as trend-continuation and stop fading. Levels are re-computed daily;
intraday they are treated as static, which is itself a known weakness.

**The joint that breaks.** The dealer-sign assumption is an *assumption*, not an observation. If
customers are net sellers of calls into a rally, dealer gamma flips sign and every level inverts. No
public data resolves this, which is why the family is a *label* in careful hands and a *signal* in
careless ones.

**Reachability with zero options data: NONE.** Missing primitive: **per-strike, per-expiry option open
interest and implied volatility.** The tempting proxy (round numbers as max-pain magnets) is invalid
because round numbers attract price for unrelated reasons, so it cannot discriminate the hypothesis.

### D6.2 0DTE pinning and max pain

**Operationally.** On expiry day, identify the strike that would cause the largest aggregate option-
holder loss ("max pain") and the strikes with the largest OI, and expect price to be drawn toward them
into the cash close as dealers' hedges decay. Traded by selling premium into the pin, or by fading
excursions away from it in the last two hours. Requires an expiry-day clock and OI that has not
already been transacted away — which, with same-day expiries, it largely has by mid-morning.

**Reachability: NONE.** Missing primitive: **same-day option open interest by strike, intraday.**
Stronger than D6.1's requirement, because a stale pre-open snapshot is specifically useless here.

### D6.3 Skew and risk reversals as directional input

**Operationally.** Compare the implied volatility of a 25-delta put to a 25-delta call at a fixed
tenor. A skew that steepens faster than spot falls indicates genuine hedging demand rather than
mechanical repricing; a skew that *flattens* into a decline is read as capitulation, and some
discretionary operators use that flattening as a long trigger on the future. Used at daily frequency
as a conviction modifier on an existing directional view, not as an entry.

**Reachability: NONE.** Missing primitive: **an implied-volatility series at two deltas and a fixed
tenor.** There is no partial version: skew is a property of the surface's *shape*, and a price series
has no shape in that dimension.

### D6.4 IV versus RV

**Operationally.** Compare implied volatility at a tenor to realised volatility over the matching
lookback. When IV is materially above RV, sell volatility (or, for a futures-only operator, *reduce*
the size of mean-reversion trades and *widen* stops, since the market is paying for a move it may not
get). When IV is below RV, the reverse. The futures-only use is as a **volatility-regime input to
sizing and stop placement**, not as an entry.

**Reachability: PARTIAL, and only after a vendor fetch.** `^VIX` is reachable with zero code change
`[repo-verified: futures_agents/data/yahoo.py:100-116]`, which supplies the IV side for the S&P
complex; the RV side is computable from the traded series. **The tempting all-in-repo proxy — realised
vol on both sides — measures zero by construction**, and that is the sharpest thing in this section:
the one arm of the options block that is nearly reachable is also the one where the obvious substitute
is provably empty. After the fetch, it is blocked by Wall A like everything else relational.

### D6.5 Variance risk premium as a traded object

**Operationally.** Short variance systematically (short VX futures, short straddles, or long an
inverse-VIX ETP), size small, cap notional, and accept that the loss distribution is the strategy's
defining feature rather than an inconvenience. Roll down the VX curve while it is in contango; flatten
in backwardation. See II-16 for the full entry.

**Reachability: NONE for the term-structure form** (needs per-expiry VX, the same unobservable as
II-1); **PARTIAL for the index-level form** after fetching `^VIX`.

### D6.6 The flat statement

With zero options data, **five of the six sub-families above survive at zero**, and the sixth
(IV-vs-RV) survives only as a vendor fetch away and only for the S&P complex. Consolidated missing
primitives, in order of how many sub-families each unlocks:

| missing primitive | unlocks |
|---|---|
| **per-strike, per-expiry option open interest** | D6.1, D6.2 (2 sub-families) |
| **an implied-volatility surface (IV at ≥2 deltas, ≥1 tenor)** | D6.3, D6.4, D6.5 (3 sub-families) |
| **per-expiry VX futures prices** | D6.5 term-structure arm, and II-16 |

Nothing in `csv/raw/` or `data/archive/` bears on any of them
`[measured: head -1 csv/raw/*.csv | sort -u -> open_time,open,high,low,close,volume; ls data/archive/ -> 4 symbols x 7 timeframes + CL_1440m]`,
and `[repo-verified: futures_agents/config.py:22-53]` `ContractSpec` has no options field of any
kind. **II-14 and II-15 are the two families in my class with the largest gap between how heavily they
are operated in the real market and how completely invisible they are here.**

---

## Was Class II mis-cut?

**Yes, in one specific place, and the manager's instinct in DIVISION §6 was right.** Raised formally
as OPEN_QUESTIONS **Q4**; summarised here.

The class boundary is *"what must the strategy observe in order to exist at all?"*, and Class II is
*"something other than this contract's own price path"*. **II-10 (seasonality) and II-11
(scheduled events) fail that test.** Both observe only the *timestamp already on the bar*:

- II-10's vehicle is `[repo-verified: futures_agents/strategies/base.py:392]`
  `StrategyFilters.days_of_week`, fed by `[repo-verified: features.py:697]`
  `FeatureSnapshot.day_of_week`; its extension is `snap.trading_day.month`
  `[repo-verified: features.py:702]`.
- II-11's vehicle is `[repo-verified: features.py:946-1003]` `_build_news_proximity`, which is
  deliberately built from recurrence **rules** precisely so that it needs no external observable —
  `econ_calendar.py:8-10` makes that argument explicitly.

**Why this is not taxonomy pedantry.** As cut, Class II reads as uniformly unreachable, because the
two reachable families are filed behind seventeen blocked ones. The merged catalogue would tell a
reader "Class II is a wall". The truth is "Class II is a wall with two doors in it".

**Proposed recut, in preference order.**

1. **A fourth axis: "the clock".** Holds II-10, II-11 and R3's III-12 (time-based exits). The
   unifying mechanism is *conditioning on the calendar rather than on the tape*, and it is genuinely a
   different observable from all three existing classes — Class I is below the bar, Class II beside
   the series, Class III along the path, and this is **orthogonal to the bar entirely**. It is also
   the only class whose data requirement is satisfiable by arithmetic, which is a real distinction
   worth a class.
2. **Or fold II-10 and II-11 into Class III**, since "this contract's OHLCV plus its own timestamps"
   is a fair reading of "the position's own path". Cheaper, loses the insight above.

**Two smaller recut notes, for completeness.**

- **II-7 (cross-sectional momentum) is in the right class but its binding constraint is misdescribed
  by the class.** Class II says "needs a second observable"; II-7 needs **N observables with N large
  and the sectors distinct**, which is a quantitative requirement no amount of code fixes here.
  `[measured: ls csv/raw/]` 11 symbols, 3 D40-excluded, 2 ETFs, and
  `[repo-verified: config.py:107-125]` MES/MNQ/ES/NQ share one `correlation_group` — effective
  cross-section ≈2. Worth flagging because a reader who sees "Wall A unlocks 6 families" might
  believe II-7 becomes real; it does not.
- **II-16 is correctly R2's under DIVISION §5.1** and I confirm the test the manager proposed works
  cleanly: the VX term structure needs a second series, so it is mine; the traded series' own realised
  volatility is R3's. No boundary friction found.

---

## Anti-overfitting and bias audit, for what this round actually produced

Round 1 produced **no expectancy, no z-score, no ranking** (DIVISION §8 compliance). So most of the
standard hazards are not yet applicable. Stating which I checked, and what I found, rather than
claiming a clean bill on things I had no opportunity to test:

| hazard | applicable this round? | what I checked and found |
|---|---|---|
| **Look-ahead bias** | **Yes — and it is the central risk in my own proposal.** | The Wall A change introduces a *new* look-ahead surface the repo has never had: a partner bar selected "nearest" instead of "last closed at or before" leaks the future. I made backwards-only partner alignment a **mandatory** part of the minimum change (`R2_expressibility_wall.md` §2, edit A3) and named the existing tests that encode the same invariant on the timeframe axis `[repo-verified: tests/test_features.py:36,91]`. Existing news plumbing checked and clean: `[repo-verified: features.py:946-1003]` projects from rules, not from headlines, and `econ_calendar.py:8-10` states why that matters. |
| **Silent-wrong-answer / repainting** | **Yes.** | Found one, pre-emptively: `[repo-verified: base.py:120]` the condition cache key `(name, tf)` would collide across partner bindings, returning one pair's answer for another with no error — the D38 failure shape. Fixed in the minimum change (edit A6). This is a hazard *created by* the proposal, caught before it exists. |
| **Data-mining bias** | **Yes, structurally.** | II-6 (pairs) and II-10 (seasonality) are the two worst offenders in Class II by construction: k(k−1)/2 candidate pairs, and ~52 candidate seasonal windows per year against 6-24 independent years. Recorded in both entries. R2-D4's power table is the defence — it rules the questions out *before* a search, which is the only reliable point at which to do it. |
| **Insufficient sample size** | **Yes, and it is my main quantitative result.** | R2-D4: annual seasonality has n = 24 (CL) / 15 (MGC) / 6 (MES,MNQ) / **0** (MCL), requiring d = 1.11-2.23 at `free_t = 5.46`. R2-D5: in-session HIGH event days = 7 (MNQ,MES) / 32 (MGC) / 49 (MCL). Only day-of-week (n = 387-1286 weeks) and MCL's EIA window are adequately sampled. |
| **Survivorship bias** | **Yes — and I found a live instance.** | `CL_1440m.jsonl` (6,192 bars, 24 years) and every `=F` series is a **continuous front-month splice with no contract-month label**, i.e. structurally the same object D40 excluded the grains for. Any seasonal or carry statistic measured on it is confounded by roll steps *at seasonal frequency*, which is the worst possible confound for the family it would be used for. Stated in R2-D4 §2. |
| **Understated costs / slippage** | **Partly.** | Not measurable without a run, but two structural findings: `[repo-verified: config.py:227-234]` the ETF specs carry `commission_per_side=0.0, exchange_fee_per_side=0.0` with the repo's own warning that this "flatters their backtests against the micros" — so any SPY/QQQ partner leg must never be costed as traded. And spreads multiply round turns: `[repo-verified: engine.py:235]` `CostModel(self.spec)` is a single-spec object, so a 6-lot crack would be costed as one contract. |
| **Unrealistic fills** | **Partly.** | Engine rules 2-4 `[repo-verified: engine.py:7-18]` are conservative and I found no defect. Note for any future spread work: a spread's fill is *not* the difference of two leg fills, because the exchange spread book has its own liquidity; modelling it as two independent fills understates slippage. |
| **Parameter sensitivity** | **Flagged, not tested.** | II-9's correlation window and II-6's re-estimation schedule are the two places in Class II where the parameter *is* the result. Recorded in both entries. |
| **Out-of-sample / walk-forward** | **Not applicable this round** — nothing was fitted, so there is nothing to hold out. Flagged as mandatory for any Wall-A follow-up: a cointegration hedge ratio estimated in-sample and applied in-sample is the single most common way this family manufactures an edge. |
| **Future-data leakage via the calendar** | **Yes.** | Checked and clean: `[repo-verified: econ_calendar.py:84-91]` `CalendarRule` stores recurrence rules, not dates, explicitly so that "a rule projects forwards and backwards indefinitely, which is what makes historical conditioning possible". One genuine caveat from prior work I am carrying forward rather than re-deriving: `research/confluence/news_macro.md` caveat 2 — the 2025-26 shutdown broke the real release schedule for a year, so **any backtest spanning 2025-10 to 2026-03 has an unreliable news channel**, and that window is *most of the intraday data in `csv/raw/`*. |

---

## Answers to the manager's three questions

### Q1 — Is our null result a property of the market, or of our information set?

**From Class II's evidence: overwhelmingly of the information set — but with a twist that is more
useful than the flat answer.**

Of 19 families, **17 cannot be expressed** (catalogue tally above). But they split into three groups
that imply three completely different remedies, and lumping them would waste the finding:

| group | n | remedy |
|---|---|---|
| Data is **already on disk**; only the code blocks it | **4** (II-3, II-6, II-8, II-9) | **Build Wall A.** No acquisition at all. |
| Data is **absent but the vendor reaches it with zero code change** | **3** (II-4, II-16 partial, II-19 partial) | **One fetch**, then Wall A. |
| Data is **genuinely unobservable from here** | **9** (II-1, II-2, II-7, II-12, II-13, II-14, II-15, II-17, II-18) | Real acquisition: a second expiry, an options surface, a positioning report, a news feed, a fundamental series, or a 40-market universe. |

So **7 of 19 Class II families are blocked by code or by a single unmade request, not by the market
and not by any fundamental data scarcity.** That is the part of "nothing is live-eligible" that this
track can speak to, and it says the next move is *build*, then *fetch*, then *acquire* — in that
order, because that is the order of cost.

The twist: **the 9 truly-unobservable families include the two largest real-world businesses in my
class** (II-14 options-informed and II-17 positioning). So a fair summary is: *the cheap blockages are
code, the expensive blockages are exactly where the most capital actually trades.* Both halves are
true and neither alone is honest.

### Q2 — Any family expressible with today's combinator, widely operated, and never tested here?

**On the strict reading: essentially empty, and I think that is the correct answer rather than a
failure to look.** Here is the search method and then the two near-misses, because the near-misses are
where the value is.

**Search method.** (a) `[measured: python3 -c "import inspect; from futures_agents.strategies.library import CONDITIONS; ..." -> no condition's source contains the word "symbol"; no condition reads trading_day or day_of_week; only three read the calendar, all FILTER]`. (b)
`[measured: generate_strategies('MCL',[5,15,60],max_total=400,seed=1) -> 280 strategies, 19 condition groups used, 120 news-bearing (42.9%), 2 distinct filter identities; generate_strategies('MGC',[15,60,240],max_total=400,seed=1) -> 268 strategies, 16 groups, 114 news-bearing (42.5%), 1 filter identity]`. (c) grep of `scan_reports/`, `workspace/studies/`, `research/backtests/` and `research/confluence/` for every Class II family name.

**Why strictly empty is structural, not lazy.** Class II is *defined* by needing an observable the
combinator cannot see. The intersection {expressible today} ∩ {Class II} is exactly the 2 mis-cut
families (II-10, II-11), and **both have already been touched** — II-11 as a filter (F11, on MNQ) and
II-10's vehicle exists but is inert. So the set {expressible ∧ operated ∧ untouched} is empty by
construction, and it would have been a red flag if I had produced one.

**Near-miss 1, and the one I would actually spend a round on: II-11 on MGC and MCL.** Expressible
today in filter form, unambiguously widely operated, and **never asked on the two contracts where the
calendar is not empty.** `[measured: distinct in-RTH HIGH event days -> MNQ 7, MES 7, MGC 32, MCL 49;
MGC_1d 358]`. This is not "never tested" — it is "tested only where it structurally could not work",
which is a *better* finding because it identifies a specific reproducible error rather than a gap.
Cost to test: zero new data, zero new code, one sweep on a symbol already in the universe.

**Near-miss 2: day-of-week (II-10), cost ~zero.** `StrategyFilters.days_of_week` exists
`[repo-verified: base.py:392]`, is never set by any generator `[measured: grep]`, and is the one
seasonal sub-family with adequate n (387-1,286 weeks). But I will not inflate it: day-of-week
seasonality is **widely claimed and thinly operated** — no desk I would cite runs it as a standalone
programme. It fails the "widely operated" half of the question. Listed because it is cheap and honest,
not because it is a real family.

**Ranked, cheapest first:** (1) II-11 filter on MGC and MCL — zero code, zero data. (2) II-10
day-of-week — zero code, zero data, weak provenance. (3) II-11 as an *entry* — one new SIGNAL
condition, ~30 lines, then it is a genuine test of the family rather than of the filter. **Nothing
else in Class II qualifies at any price without Wall A.**

### Q3 — Which single missing primitive unlocks the most families in your class?

**A second aligned `SymbolFrame` reachable from inside `FeatureSnapshot` on the primary series' bar
clock, with backwards-only partner alignment.** Concretely, one new field —
`FeatureSnapshot.partners: Dict[str, FeatureSnapshot]` at `futures_agents/features.py:685` — plus the
alignment map that populates it safely and the cache-key fix that stops it lying
(`R2_expressibility_wall.md` §2, edits A1-A8; eight named, additive edits; `ConditionFn` at
`base.py:87` does **not** change).

**Count: 6 families, using only data already on disk.**

| family | what becomes possible | partner data already present |
|---|---|---|
| II-3 basis | futures rich/cheap vs ETF as a signal | `MES_1d`×`SPY_1d` **1,855** aligned bars; `MNQ_1d`×`QQQ_1d` **1,855** |
| II-5 inter-market | gold-vs-equity, gold-vs-crude conditioning | `MGC_1d`×`SPY_1d` **2,507** (the longest aligned pair in the repo); `MGC_1h`×`MCL_1h` **4,636** |
| II-6 statarb | ratio z-score as a signal (one-legged, labelled as such) | `MES_1h`×`MGC_1h` **4,986** |
| II-7 cross-sectional | rank filter on a 4-symbol universe (degraded; effective N≈2) | the four micros |
| II-8 lead-lag | cross-contract structural lead-lag | ES/NQ/MES/MNQ/SPY/QQQ |
| II-9 correlation regime | rolling-correlation regime filter | any on-disk pair |

**Plus 3 more after a vendor fetch that needs zero code change** (`RB=F`, `HO=F`, `SI=F`, `^VIX`,
`^TNX` all pass through `ticker_for` untouched `[repo-verified: yahoo.py:100-116]`): II-4 signal-side,
II-16's IV-vs-RV arm, II-19's price-proxy arm. **So: 6 now, 9 after one fetch.**

**The runner-up primitive, for the manager's reconciliation:** a **multi-leg position** (Wall B).
It unlocks **5** (II-1, II-2, II-4, II-6-as-a-true-pair, II-15) and **none of them without Wall A as
well**, and it is a structural change rather than eight additive edits. **So within Class II the build
order is unambiguous and measured: Wall A first (6 families, additive, cheap), a vendor fetch second
(3 more, zero code), Wall B last (5 more, expensive, and 2 of its 5 are additionally blocked on data
that is unobservable anyway — II-1 and II-2 need a second expiry that Wall B does not provide).**

That last clause is the single most decision-relevant sentence in my track: **building a spread
backtester would not let this repo trade a calendar spread, because the data for one does not exist.**
Wall B's real yield is 3 families, not 5.

---

## Scorecard against the manager's pre-registrations (DIVISION §6, Track R2)

The manager asked to be told loudly where a pre-registration is refuted. Four of five, in order.

1. **"Hardest: resisting the one-sentence answer … the risk is R2 delivers that and stops."**
   **Accepted and addressed.** The one-frame fact is confirmed at the lines claimed
   (`engine.py:548,554`) and is not the answer. The answer is that there are **two** walls costing
   very different amounts and unlocking disjoint sets (6 vs 5), which makes the build order decidable.

2. **"I expect R2's ratio of `[general knowledge]` to `[repo-verified]` claims to be the worst of the
   three tracks. Pre-registered threshold: fewer than ~15 path-cited repo claims means the diagnostic
   half under-delivered."**
   **Refuted on the count.**
   `[measured: grep -o "repo-verified: [^]]*" R2_relational.md R2_expressibility_wall.md | wc -l -> 89]`,
   `[measured: grep -o "measured: " ... | wc -l -> 53]`,
   `[measured: grep -o "general knowledge" ... | wc -l -> 50]`.
   **89 path-cited repo claims and 53 measurements against 50 general-knowledge claims** — the
   general-knowledge share is the *minority*. The prediction's direction was reasonable and its
   magnitude was wrong, because Class II's diagnostic content turned out to be code architecture (a
   repo fact) rather than market description.

3. **"I expect to come back empty: the entire spread / carry / curve block, and not merely as
   inexpressible but as unobservable … the only place a roll is visible is a defect (D40)."**
   **Confirmed for the curve (II-1, II-2); refuted for the rest of the block.** Calendar spreads and
   carry are genuinely unobservable and D40 is indeed the only visible roll. But **inter-commodity
   spreads (II-4) are not unobservable** — `RB=F`, `HO=F`, `SI=F` pass through `ticker_for` with zero
   code change `[repo-verified: futures_agents/data/yahoo.py:100-116]` and the daily lookback is 25
   years `[repo-verified: yahoo.py:86]`. And **basis (II-3) is not unobservable at all**: `SPY_1d` vs
   `MES_1d` gives ≈1,850 aligned daily bars and has been sitting in `csv/raw/` the whole time. The
   block is not one thing.

4. **"I expect one genuine positive: seasonality and the scheduled-event window … I also expect the
   power arithmetic to kill most of it anyway."**
   **Confirmed, and the shape of the kill is more specific than predicted.** Seasonality: killed
   except day-of-week (n = 387-1,286 weeks vs 6-24 years for everything else), and the one long series
   that could answer an annual question (`CL_1440m`, 24 years) is a front-month splice, so it is
   confounded with the thing being measured. Scheduled events: **not killed by power — killed by the
   session.** `[measured: distinct in-RTH HIGH event days -> MNQ 7, MES 7, MGC 32, MCL 49, MGC_1d 358]`.
   The family has sample on MGC and MCL and was tested on MNQ.

5. **"I expect a wrong prior of mine to surface here … treat my framing of Class II as the most likely
   to be mis-cut."**
   **Confirmed.** II-10 and II-11 need no second observable and are mis-classified; full recut
   proposal in OPEN_QUESTIONS Q4 and in "Was Class II mis-cut?" above. A secondary mis-description:
   II-7's binding constraint is **universe size (effective N≈2)**, which no code change here fixes and
   which the class definition does not capture.

### One thing the division got exactly right, recorded because confirmations are cheap to omit

DIVISION §5.5 reserved cross-timeframe lead-lag as settled and gave R2 only cross-*contract*
lead-lag. That boundary is real and load-bearing:
`[repo-verified: workspace/newstrats/leadlag.py:42-43]` `HTF_OF: Dict[int, int] = {5: 15, 15: 60,
30: 240, 60: 240, 240: 1440}` maps **timeframe to timeframe** and never symbol to symbol. The repo
built its lead-lag machinery on the one axis it could reach, and the axis the family actually names
has never been touched. Without §5.5 I would have spent the round re-reading `s_leadlag`.

---

# Round-2 amendments (appended 2026-09-27)

**Appended, never inserted.** BT2 cites this file by line range —
`R2_relational.md:145-259`, `:629-668`, `:1048-1091`, `:1185-1213`, `:1268`, `:1279-1312`, `:1310`
(`msgs/05_BT2_R2_verify-ALGO-1.md`) — and `msgs/06_R2_BT2_re-verify-ALGO-1.md` cites those back.
Inserting a line anywhere above would silently shift every one of them into pointing at the wrong
paragraph, which is the failure `REGISTRY.md` exists to prevent. So round-2 corrections are appended
here with the line they amend, and the text above is left byte-for-byte intact even where it is now
known to be imprecise.

New round-2 files: `research/R2_wall_a_spec.md` (the Wall A change as eight implementable edits),
`research/R2_recut_contingency.md` (what changes in this catalogue either way on **R2-Q1**),
`research/R2_REQUESTS.md`.

## A1 — amends `:664-665` and `:1290`: F11's basis is MNQ **synthetic**, and only half of it transfers

**Raised by BT2** (`msgs/05_BT2_R2_verify-ALGO-1.md`, closing section) and accepted.

`:664-665` reads *"F11: `post_news_window` on 50 **MNQ** MOMENTUM strategies cut mean trades 112.6 →
1.5, zero publishable"*, and `:1290` reads *"II-11 as a filter (F11, on MNQ)"*. Neither carries the
qualifier. **Read `:664` and `:1290` as "MNQ **synthetic**" throughout**
`[repo-verified: research/confluence/reversion_specialist.md:7 → "All figures below are MNQ
synthetic, seed=5"]`.

Partial credit where it is due: `:226` — R2-D5's own paragraph — **already** states the synthetic
basis inline, so the imprecision is in II-11 and in the Q2 answer, not in R2-D5. BT2 read the file
correctly; I am narrowing the scope of the correction rather than widening it.

**The substantive half of BT2's point is new and is the reason this amendment matters**, and I adopt
it: F11's one sentence has two halves with completely different transferability.

| half of F11 | transfers from synthetic to real bars? | why |
|---|---|---|
| **trade count 112.6 → 1.5** | **Yes, unchanged.** | It is a property of the **calendar** (projected from recurrence rules, identical on any bar series) and of the **bar grid** (identical). Neither depends on the price process. |
| **"zero publishable"** | **No — it was never a statement about real markets.** | The synthetic generator is a near-martingale with no mechanical edge baked in, so no win rate in that document is evidence about real markets. |

So R2-D5's claim *"the 1.5 was determined by the calendar, not by the strategy"* is **strengthened**,
not weakened, by the synthetic basis: the determining mechanism is exactly the one that survives the
substitution. Conversely, nothing in F11 licenses "this family does not work", on MNQ or anywhere.

## A2 — amends the R2-D5 table row for `MGC_1d`: the 358 in-session event days are **unreachable**

**Found by BT2** (its choice C9, `backtest/BT2/ALGOS.md:163-176`), verified and extended here.

R2-D5's table (`:172`-ish) reports `MGC_1d`: 502 HIGH events, 360 in-RTH, **358 distinct in-RTH event
days** over ten years. Every number is correct **as a count of calendar events against a session**,
and I presented it in a column headed the same way as the intraday rows, which invites reading it as
*available sample for this family*. **It is not.** No news condition in the library can act on any of
those 358 days at daily frequency.

Every daily bar in `csv/raw` is stamped **00:00 ET**:
`[measured: python3 -c "from futures_agents.timeutil import to_et; from futures_agents.data.loader
import load_csv; import collections; collections.Counter(to_et(b.ts).strftime('%H:%M') for b in
load_csv(p,s,1440).bars)" → MGC_1d 2511/2511 at 00:00; MES_1d 1859/1859; SPY_1d 2512/2512]`

and the six HIGH rules print at 08:30 (CPI, NFP, PCE), 10:30 (EIA), 14:00 (FOMC Statement) and 14:30
(FOMC Press Conference) `[measured: python3 -c "from futures_agents.econ_calendar import ECON_RULES,
Impact; [(r.name, r.at) for r in ECON_RULES if r.impact.rank >= Impact.HIGH.rank]"]`. Therefore, on
every daily bar in this repository:

| condition | value | mechanism |
|---|---|---|
| `post_news_window` `[repo-verified: futures_agents/strategies/library.py:1345-1361]` | **identically FALSE** | window is `15 < since <= 60`; the smallest possible `since` at 00:00 ET is from the prior day's 14:30 presser = **570 min** |
| `no_imminent_release` `[repo-verified: futures_agents/strategies/library.py:1334-1342]` | **identically TRUE** | declines only when `minutes_to_high_impact < 30`; at 00:00 ET the nearest print ahead is 08:30 = **510 min** |
| `outside_news_blackout` `[repo-verified: futures_agents/strategies/library.py:1326-1331]` | **identically TRUE** | the blackout is `[-10, +15]`, 25 minutes wide; 00:00 ET is never inside it for any of the six print times |

**So all three of the library's news conditions are degenerate on every daily series in this
repository** — two constant-true no-ops and one constant-false total veto. Two consequences:

1. **A daily strategy carrying `post_news_window` trades exactly zero times, by arithmetic, before
   any price is consulted.** That is the same shape as **R1-Q2** — whether zero-trade strategies
   entered the 2,975,629 denominator — with a different condition and a *provable* cause rather than a
   suspected one. Flagged to R1 in `msgs/06_R2_BT2_re-verify-ALGO-1.md` §6.1; it is their
   denominator question, not mine.
2. **II-11's expressible arm is 60-minute-or-finer only, and on this data that means 60m exactly.**
   Daily is arithmetically excluded (above); `csv/raw`'s 15m series give ~2 months and 5m ~1 month,
   i.e. 6-8 event days `[measured: BT2, ALGOS.md:163-176]`. So the one window in which the family is
   measurable here is 60m, and the only sample extension available is `data/archive`.

## A3 — new: two defect-grade findings about the library's news conditions

Both surfaced in the BT2-ALGO-1 fidelity cycle, both in my lane (the news conditions), both raised to
the manager for `D<n>` allocation — only the manager allocates defect numbers (`REGISTRY.md`).

### A3.1 `post_news_window` fills one to two bar lengths outside the window it names

`[repo-verified: futures_agents/strategies/library.py:1345-1347]` the condition's description is
*"In the reaction window after a high-impact release"* and its bound is
`[repo-verified: futures_agents/strategies/library.py:1358-1359]` `lo(15) < since <= 60.0`. But
`since` is computed at the bar's **open** (`Bar.ts`
`[repo-verified: futures_agents/data/bars.py:37]`; the snapshot passes `ts=bar.ts`
`[repo-verified: futures_agents/features.py:1023]`), the signal is decided at the bar's **close**
(`price=bar.close`, same line), and the entry fills at the **next** bar's open
`[repo-verified: futures_agents/backtest/engine.py:290-292, :355 → entry = spec.round_to_tick(bar.open
+ sign * slip)]`.

On a 60-minute frame an 08:30 print admits `ts ∈ (08:45, 09:30]`, which on a `:00` grid is `ts = 09:00`
alone, closing 10:00 and filling **10:00 — ninety minutes after the print.** Generalised across grids
the realised entry sits 60–120 minutes after the print while the condition claims 15–60.
**The misalignment is one to two bar lengths, scales with the timeframe, and is undocumented.**

Same family as D39 (library ORB is a state, not an event, and silently widens): a condition whose name
and docstring describe a window it does not implement. Found by BT2 (its choice C6); the `offset_min`
parameter in `backtest/BT2/code/event_clock.py` is the instrument that quantifies it.

### A3.2 `outside_news_blackout`'s reachability is a function of the bar grid, and on MGC at 60m it is the identity filter

The blackout is 25 minutes wide (`[-10, +15]`,
`[repo-verified: futures_agents/config.py:410-411]`) and is tested at the bar's **open**. Five of the
six HIGH rules print at `:30` and one at `:00` (FOMC Statement, 14:00) `[measured: as A2]`. So:

> On a `:00`-aligned grid at any timeframe ≥ 30m, a `:30` print's blackout spans `:20`–`:45` and
> **contains no bar open at all**; a `:00` print's spans `13:50`–`14:15` and does contain the `14:00`
> open.

That is a complete explanation of BT2's measured table
`[measured: BT2, ALGOS.md:254-261]`: bars removed by `outside_news_blackout` at 60m on `csv/raw` =
MGC **0** of 1,093, MNQ 7 of 1,310 (exactly the 7 FOMC Statements), MCL 9 of 1,320.

**On MGC at 60m `outside_news_blackout` is the identity filter — it cannot decline on any bar**,
because gold's in-session HIGH calendar is entirely `:30` prints. It follows that a filtered and an
unfiltered arm are the same strategy bar for bar, so any comparison between them measures **nothing**
and must not be reported as a null. It also re-explains F11's second line (`outside_news_blackout`
retained 99.99% of trades) as a property of the bar grid rather than of the filter — the same kind of
finding as R2-D5 itself, one level down.

## A4 — amends the reading of R2-D5's 7 / 32 / 49: these are three hypotheses, not three instances of one

The census stands exactly as published and BT2 reproduced all of it independently, on each contract's
own `ContractSpec` session `[measured: BT2, ALGOS.md:203-207 → MNQ 7, MGC 32, MCL 49, with the
per-rule split "NFP 11, CPI 11, PCE 10" and "EIA 49, FOMC statement 8" reproduced item for item]`.
What needs stating is what the three numbers are *of*, because R2-D5's sentence *"the family has
sample on MGC and MCL and was tested on MNQ"* does not say it and a reader can fairly infer the wrong
thing:

- **MGC's 32** are NFP / CPI / PCE — market-wide **macro** prints, in-session only because gold's pit
  opens at 08:20 `[repo-verified: futures_agents/config.py:157]`.
- **MCL's 49** are dominated by **EIA**, a crude-specific physical inventory release — a different
  kind of event with different size, persistence and cause.
- **MNQ's 7** are FOMC Statements and Press Conferences.

So a result on one says nothing about another, and **a consistent sign across contracts is not
corroboration** — the D14/D41 non-corroboration hazard arriving through the calendar rather than
through price.

**And the overlap is not zero, which is the part I had not measured.**
`[measured: python3 -c "... per-symbol in-RTH HIGH event days over each csv/raw *_1h span with that
contract's own spec, then pairwise set intersections ..." →]`

| pair | shared in-session event **days** | note |
|---|---|---|
| MNQ ∩ MGC | **1** (2025-12-10) | same day, **different events** (MGC 08:30 print, MNQ 14:00 statement) |
| **MNQ ∩ MCL** | **7 of MNQ's 7** | **the same FOMC Statement prints, the same instants** — MNQ's entire sample is a strict subset of MCL's |
| MGC ∩ MCL | 7 | same days, different events |
| MNQ ∩ MES | **7 of 7** | identical: same session, same calendar. D14/D41's "one complex" holds on the calendar axis too |

**Operational consequence: MNQ cannot serve as an independent reference arm against MCL** — 100% of
its events are inside MCL's sample, so the contrast would be a subset against its superset. The
**MNQ vs MGC** contrast is the near-clean one (one shared day, different events on it) and it is the
one that carries R2-D5's argument. Recorded as a correction to a claim in
`backtest/BT2/ALGOS.md:211-214` in `msgs/06_R2_BT2_re-verify-ALGO-1.md` §4.

## A5 — status of the Class II expressibility conclusion after round 2

Unchanged. Round 2 produced no new family verdict and no measurement that moves one. Wall A is still
**6 families from on-disk data, 9 after one zero-code-change vendor fetch**; Wall B is still
**structural, and its real yield is 3 not 5**. The round-2 work turned the Wall A finding into an
implementable spec (`research/R2_wall_a_spec.md`) and the II-11 finding into running code (BT2's
ALGO-1, verdict **FAITHFUL**, `msgs/06_R2_BT2_re-verify-ALGO-1.md`). Nothing was fitted, nothing was
ranked, no expectancy and no z-score was computed in either round.
