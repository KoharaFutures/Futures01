# DIVISION — round 1

**Owner:** manager. **Written:** 2026-09-26 21:12 ET. **Round:** 1 of n.
**Amended:** 2026-09-26 23:10 ET (round 2) — see the amendment block immediately below.
**Read `workspace/roundtable/BRIEF.md` in full first.** This file assumes it.

---

## AMENDMENT (round 2, 2026-09-26 23:10 ET) — read before §1, §5 or §6

Round 1 ran and **two of three tracks independently reported that the classes in §1 are mis-cut**
(`R2-Q1`; discovery's `I-12` note). That is a pattern, not two boundary disputes, and it is ruled in
`manager/ADJUDICATIONS.md` ADJ-0 through ADJ-2. Three amendments follow, applied in place below.

**A1 — §1 is a mechanism taxonomy. It is no longer the routing table.** §1 was written to do two
jobs at once — *what must this strategy observe?* and *who audits it?* — and where those answers
disagreed, the taxonomy assigned the disagreement to nobody. Both mis-cuts are that:

- `II-10` / `II-11` observe only the bar's timestamp (mechanism says "not Class II"), but the
  calendar is R2's surface (routing says "R2"). Filed under Class II, the two reachable families sat
  behind seventeen blocked ones and the class read as a wall.
- `I-12` has an expressibility question that is Class I's (R1 answered it) and a **confound**
  question about Class III's settled findings. The second had no owner in any class.

**From here, ownership is carried by `manager/BOARD.md`** (`PIPELINE.md` §2). §1 below is unchanged
as a description of mechanism and must not be read as an assignment. **Cost, stated:** the merged
catalogue no longer has one label that tells a reader whom to ask. That is a real loss and it is
accepted; the alternative cost was paid twice in round 1 and was invisible until two researchers
went looking.

**A2 — "the clock" is added as `Axis C`, an orthogonal axis and not a fourth class.** See §1 below.
`R2-Q1` proposed a fourth class holding `II-10`, `II-11`, `III-12`; that is refused (it renumbers
live citations, splits R3's operating layer, and forces an exclusive choice on `II-11`, whose clock
half needs arithmetic and whose event half needs a surprise term that does not exist here). **Nothing
is renumbered and nothing changes owner.** Full reasoning and the stated cost: ADJ-1.

**A3 — `I-12` is not split, and gets a cross-class pointer instead.** Discovery proposed splitting it
on the ground that three of its six schemes "need no sub-bar data". **That premise was refuted by R1
and withdrawn by discovery**: what is constructible here is a *minute-snapped approximation* to a
volume or dollar bar, not a volume or dollar bar. A split would encode a withdrawn claim. See ADJ-2;
the question now lives in `MAIN-01`.

**A4 — §6's pre-registrations were tested and several were refuted. Do not cite §6 as if it stood.**
`R1-Z`, R2's scorecard and `R3-Q2` carry the dispositions. In summary: R1's INEXPRESSIBLE-DATA count
was **9**, not ≥10, and its strict EXPRESSIBLE set was **0**, below my floor of ≤3; market profile is
the family whose blindness is **cheapest** to remove, not the least testable. R2's path-cited repo
claims were **89**, not "fewer than ~15". R3-D5 holds **6 strict items plus 2 artefact replays**, not
≤2. **The common cause of all three errors is one inference** — that ~2,975,629 evaluations imply a
*wide* search, when the volume is in the rule-set dimension and the exit catalogue is eleven fixed
literals with one `StrategyFilters` identity. Ruled as a standing rule in ADJ-5 and on
`manager/BOARD.md` as **R-11: any claim of the form "this has already been tested" must name the
dimension that was varied.**

Three researchers, three tracks, no overlap by construction. Everything you need to start is
in this file plus `BRIEF.md`. You do not need to see the prompt that produced either.

---

## 0. What round 1 is, and is not

The job is a **catalogue**: what futures strategies exist, how each is actually operated by
people who run it for a living, and which of them this library can and cannot express.

**It is descriptive and diagnostic. It is not a search for edge.** ~2,975,629 evaluations have
already settled the edge question (`BRIEF.md` §"What the research already established"). Round 1
produces **no new expectancy numbers, no rankings, no comparative statistics.** If you find
yourself computing a z-score you have drifted out of scope — stop and write a line in
`workspace/roundtable/OPEN_QUESTIONS.md` instead.

The most valuable single sentence any of you can write has the shape:

> *"This family is operated by real desks in way X; it requires data object Y; we do not have Y;
> here is the line of code that proves we do not have it."*

The second most valuable has the shape:

> *"This family is operated in way X; it IS expressible with what is already in
> `futures_agents/strategies/`; nobody here has ever tested it."*

An honest **empty** is a result. Do not manufacture a positive.

---

## 1. The map of the strategy space

Fifty-three families, grouped into three **mechanism classes**. The class boundary is a single
question: **what must the strategy observe in order to exist at all?**

- **Class I — participant information.** It needs to see *who is transacting*: transactions,
  the bid/ask split, book depth, volume at price. Information below the bar.
- **Class II — a second observable.** It needs something other than this contract's own price
  path: another expiry, another contract, the calendar, the options surface, a positioning report.
- **Class III — the position's own path.** It needs only this contract's OHLCV, and its edge (or
  its destruction) lives in the decision rule applied to the position over time.

### Axis C — the clock. An orthogonal tag, added round 2 (ADJ-1), not a fourth class

The three classes answer *what must the strategy observe*. **Axis C answers a different question
that cross-cuts all three: is the data requirement satisfiable by arithmetic on the bar's own
timestamp?** A family carries a class and, if it qualifies, the Axis-C tag as well. This is the only
"class" of requirement in the whole map that needs no acquisition and no new observable, which is
why it is worth marking — and it is a tag rather than a container because a family can have one half
on the axis and one half off it.

| member | keeps class | keeps owner | which half is on the axis |
|---|---|---|---|
| `II-10` seasonality | II | R2 | all except expiry-week and roll-window (blocked on a second expiry) |
| `II-11` scheduled events | II | R2 | **the clock half only.** The event/surprise half is not on the axis and is not satisfiable by arithmetic — the surprise term does not exist as a data object here |
| `III-12` time-based exits | III | R3 | time stops, session-close and week-end flattening, hold-period targeting |
| `time` condition group (4, all FILTER) | — | R2 via `MGR-T7` | the library's existing Axis-C surface |
| `news` condition group (3, all FILTER) | — | R1 audited it; R2 holds the calendar | R1 established it is structurally a `time` group — the only quantity read is minutes to/since a projected timestamp |

**One exclusion, ruled explicitly because it is the near miss that would otherwise be assumed in:
`I-12`'s volume/dollar/range schemes are NOT on Axis C.** A volume-bar boundary is a statement about
cumulative volume crossing a threshold *inside* a minute, not about the minute's timestamp.

**The honest cost of making this a tag instead of a class: a tag has no owner.** A fourth class would
have forced someone to deliver "what is reachable by arithmetic alone". `manager/BOARD.md` carries
that as `MGR-T7` instead; if `MGR-T7` never runs, this amendment bought nothing.

This list is a **floor, not a ceiling.** If you find a family that belongs to your class and is
not here, add it and say you added it. If you think a family is in the wrong class, do not
silently move it — write it in `OPEN_QUESTIONS.md` and I will adjudicate. **Round 1 proves this
channel works: two of the three tracks used it and both were substantially right.**

### Class I — participant and auction information → **Track R1**

| # | family |
|---|---|
| I-1 | Order flow / footprint reading (bid-ask footprint, stacked imbalances, delta at extremes) |
| I-2 | Absorption and stopping volume |
| I-3 | Iceberg / hidden size detection; passive size discovery |
| I-4 | DOM and book pressure; spoof-and-go; queue-position scalping |
| I-5 | Market making / liquidity provision / spread capture |
| I-6 | Tape scalping (aggressive, sub-minute, size-driven) |
| I-7 | Market profile / TPO: day types (trend, normal, normal-variation, neutral, double-distribution) and opening types (open-drive, open-test-drive, open-rejection-reverse, open-auction) |
| I-8 | Auction market theory: initiative vs responsive activity, excess, poor high/low, single prints, value migration |
| I-9 | Volume profile: POC / VAH / VAL / HVN / LVN, composite vs session profile, naked POC |
| I-10 | VWAP as an institutional benchmark; TWAP; anchored VWAP; execution-algo footprints |
| I-11 | Liquidity mapping and stop-run harvesting (session / PDH / PDL / ONH / ONL); relative-liquidity models |
| I-12 | Alternative bar sampling: tick, volume, range, dollar, imbalance and run bars. **Cross-class pointer (A3/ADJ-2):** stays here, one family, one id. R1's expressibility verdict is delivered (`INEXPRESSIBLE-ARCHITECTURE`, missing primitive "a bar-identity that is not an integer minute count", nine layers). The separate question — **is the wall-clock sampling choice a confound in findings this repo treats as settled?** — is a question about Class III's results and is carried by `MAIN-01`, not by this row. **Not on Axis C.** |
| I-13 | Cumulative-delta divergence; footprint shape (P / b distributions) |
| I-14 | Block and large-print detection; time-and-sales filtering |
| I-15 | Opening auction and settlement-window behaviour; MOC-imbalance analogues |

### Class II — a second observable → **Track R2**

| # | family |
|---|---|
| II-1 | Calendar spreads (expiry-to-expiry), butterflies, condors on the curve |
| II-2 | Carry / roll-yield harvesting; contango-vs-backwardation positioning; term-structure slope |
| II-3 | Basis and cash-futures arbitrage; index arbitrage; EFP |
| II-4 | Inter-commodity spreads: crack (CL/RB/HO), crush (ZS/ZM/ZL), spark, gold-silver ratio, wheat-corn |
| II-5 | Inter-market and cross-asset relationships (rates vs index, dollar vs metals, risk-on/off) |
| II-6 | Statistical arbitrage: cointegration and pairs, ratio mean reversion, basket vs component |
| II-7 | Cross-sectional momentum and cross-sectional carry across a futures universe |
| II-8 | Lead-lag between contracts: index complex, cash/ETF vs futures, one commodity leading another |
| II-9 | Correlation-regime trading; correlation breakdown; dispersion |
| II-10 | Seasonality: annual, monthly, time-of-month, day-of-week, expiry-week, roll-window |
| II-11 | Scheduled-event trading: pre-positioning, straddle-the-number, fade-the-spike, post-release drift (EIA, WASDE, FOMC, CPI, NFP) |
| II-12 | Unscheduled news and headline-driven; latency-sensitive event reaction |
| II-13 | Inventory and fundamental-driven (storage, stocks-to-use, weather, OPEC) |
| II-14 | Options-informed: gamma exposure / dealer hedging levels, 0DTE pinning and max pain, skew and risk reversals as directional input, IV vs RV |
| II-15 | Delta-neutral futures positioning: futures as the hedge leg, gamma scalping, delta hedging |
| II-16 | Volatility as a traded object: VX term structure, contango roll-down, variance risk premium |
| II-17 | Positioning and flow data: COT/CFTC, open-interest change taxonomy, commercial vs speculative |
| II-18 | Term-structure-conditioned trend (trend filtered by the sign of carry) |
| II-19 | Macro-regime overlays (rate cycle, inflation regime, liquidity conditions) |

### Class III — the position's own path → **Track R3**

| # | family |
|---|---|
| III-1 | Time-series momentum / CTA trend following (Donchian, MA crossover, 12-month momentum) |
| III-2 | Volatility breakout systems (Turtle, NR7 / inside-day expansion, squeeze release, ATR channel) |
| III-3 | Volatility-regime-conditioned entry: expansion vs contraction cycles on the traded series |
| III-4 | Mean reversion to a band or anchor on one series (Bollinger, Keltner, VWAP, z-score) |
| III-5 | Pattern and sequence strategies: multi-bar sequences, setup → trigger → confirmation chains |
| III-6 | Opening range / initial balance systems |
| III-7 | Position sizing as strategy: fixed fractional, fixed ratio, volatility targeting, ATR-normalised, Kelly and fractional Kelly, risk parity |
| III-8 | Pyramiding / scaling in: add on strength, add on weakness, anti-martingale, Turtle unit adds, averaging down |
| III-9 | Scaling out, partial profit-taking, runner management |
| III-10 | Stop discipline: initial placement, breakeven moves, trailing (ATR, chandelier, parabolic, structural), stop-hunt avoidance |
| III-11 | Target discipline: fixed R, measured move, structural objective, trail-only, no target |
| III-12 | Time-based exits: time stops, session-close flattening, week-end flattening, hold-period targeting |
| III-13 | Re-entry after a stop-out; scratch and breakeven exits; trade-campaign management |
| III-14 | Portfolio heat, correlated-exposure limits, daily loss limits, drawdown governors, equity-curve trading |
| III-15 | Roll management as an operational task (when to roll, how to execute the roll spread) |
| III-16 | Execution mechanics: limit vs market vs stop-limit, partial fills, slippage budget, cost-aware entry |
| III-17 | Meta-labelling and model-based filtering — deciding whether to take a signal you already have |
| III-18 | Discretionary overlay and operating discipline: journal, review cadence, error taxonomy |
| III-19 | Anti-strategy: what operationally destroys expectancy (over-trading, revenge trading, moving stops, martingale) |

---

## 2. The three tracks

I divided by **mechanism** — what the strategy must observe — rather than by our 13 group names.
Three reasons, and you are entitled to know them because they constrain how you should work:

1. **Dividing by group name would guarantee duplication of existing work.** Our 13 groups are
   already the unit of the four existing reports in `scan_reports/` and of the 21-study
   programme. A track called "the BREAKOUT family" would re-walk
   `scan_reports/2026-09-24_strategy-studies_21-study-programme.md`.
2. **Dividing by group name structurally excludes the point of the exercise.** The families that
   are *not* in our 13 groups are the deliverable. A group-name division has no home for a crack
   spread.
3. **Mechanism is the axis on which "can our harness express it?" actually separates.** The
   library's blind spots cluster by what they need to observe, not by what they are called:
   below-the-bar, beside-the-series, or along-the-path. It also gives each track a mostly
   **disjoint code surface**, which is the practical guarantee against three people writing the
   same audit.

| track | name | one-line rationale |
|---|---|---|
| **R1** | **Flow, auction and participant information** | Owns every family whose edge comes from seeing *who is transacting* — and the matching diagnosis of how much of our "order flow" is an OHLCV proxy wearing the name. |
| **R2** | **Relational: second series, curve, calendar, surface** | Owns every family whose edge needs an observable other than this contract's own path — and the architectural question of whether this repo can hold two series at once. |
| **R3** | **Path and operation: managing a position through time** | Owns every family that needs only OHLCV on one contract, plus the entire operating layer — sizing, pyramiding, stops, targets, re-entry — treated as strategy rather than admin. |

### Routing — which role takes which track

The task kind is **`research_family`**, and all three research-specialist roles in
`futures_agents/team/roles.py:148-189` accept it (`accepts={"research_family", "challenge",
"rebut"}`). A kind accepted by more than one role must be assigned explicitly rather than left to
`role_for`, so here it is, explicitly:

| track | role | role's own title |
|---|---|---|
| **R1** | `Role.RESEARCH_LIQUIDITY` | Research Specialist — Liquidity, Breakout & Session |
| **R2** | `Role.RESEARCH_TREND` | Research Specialist — Trend, Momentum & Continuation |
| **R3** | `Role.RESEARCH_REVERSION` | Research Specialist — Mean Reversion, Reversal & VWAP |

Two notes on that, because the mismatch is deliberate and you should not try to resolve it
yourself:

- **Your role title describes your default family mandate. This round overrides it.** The role
  titles are cut by our own group names; this round is cut by mechanism (§2), which is the whole
  point of the exercise. Follow your **track**, not your title. If your title makes you want to
  reach for a family in someone else's class, that is the pull this division exists to resist.
- **Write your deliverables into `workspace/roundtable/research/`, not into your role's own
  workspace directory.** The three files have to sit together to be merged and diffed. The role
  graph in `roles.py` also says you may message each other directly; in this roundtable you may
  not (`BRIEF.md` §"How the conversation works"). `OPEN_QUESTIONS.md` is the channel and I route it.

### Primary code surface per track (cite from yours; do not audit another's)

| track | owns these files for audit |
|---|---|
| R1 | `futures_agents/indicators/volume.py`, `futures_agents/features.py` (delta/CVD/profile/VWAP paths), the `orderflow` / `volume` / `profile` / `vwap` / `liquidity` / `imbalance` condition groups in `futures_agents/strategies/library.py`, the CSV column schema |
| R2 | `futures_agents/backtest/engine.py` entry points (one-frame architecture), `futures_agents/config.py` (`ContractSpec`, `correlation_group`, `TIMEFRAME_GROUPS`), `futures_agents/econ_calendar.py`, the `csv/raw/` inventory and per-file spans, `futures_agents/strategies/profiles.py` |
| R3 | `futures_agents/strategies/base.py` (`StopKind`, `TargetKind`, `ExitModel`, `StrategyFilters`), `futures_agents/backtest/engine.py` position lifecycle (`_OpenPosition`, `_manage`, `_open_position`), `futures_agents/backtest/costs.py`, `futures_agents/risk/manager.py` and `futures_agents/risk/account.py`, `futures_agents/strategies/combinator.py` exit catalogue |

---

## 3. Deliverables

Write to your own file **as you go** (`BRIEF.md` hard rule 1). One main file per researcher; the
extra named artefacts below are separate files because they are tables a later round will diff.

### Track R1 — Flow, auction and participant information
Main file: `workspace/roundtable/research/R1_flow_auction.md`

- **R1-D1 — Class I family catalogue.** Every family I-1…I-15 gets an entry under the schema in
  §4. *Done when:* fifteen entries exist, each with all eight schema fields populated and an
  expressibility verdict. Artefact: sections `## I-1 …` through `## I-15 …` in
  `R1_flow_auction.md`.
- **R1-D2 — Operating manual for the two best-documented Class I frameworks:** market
  profile / TPO (day types and opening types) and footprint / order-flow reading. *Done when:* a
  reader who has never traded either can state, for each — what you look at and in what order,
  what makes you act, what makes you stand aside, where the stop goes and why it goes there, and
  what invalidates the read mid-trade. Artefact: section `## R1-D2 Operating manual` in
  `R1_flow_auction.md`.
- **R1-D3 — Data-requirement ledger.** One row per Class I family; columns for each data object
  (time-and-sales, bid/ask split, DOM depth, exchange volume-at-price, sub-minute bars, session
  boundaries) with a hard YES/NO on whether `csv/raw/` supplies it, plus the path evidence.
  *Done when:* no cell is blank and every NO cites a path. Artefact:
  `workspace/roundtable/research/R1_data_requirements.md`.
- **R1-D4 — The proxy audit.** Of the 27 conditions in the six condition groups that claim
  participant information (`orderflow` 3, `volume` 3, `profile` 6, `vwap` 5, `liquidity` 7,
  `imbalance` 3 — see Appendix A), say which are reading participant information and which are
  OHLCV derivations wearing the name. Start at `futures_agents/indicators/volume.py:1-9`.
  *Done when:* every one of the 27 carries a verdict with a path citation. Artefact: section
  `## R1-D4 Proxy audit`.
- **R1-D5 — The named-blindness list.** Class I families this harness cannot see, each with the
  **one specific missing primitive** and a one-line estimate of what supplying it would take.
  *Done when:* every INEXPRESSIBLE verdict in R1-D1 appears here with a named primitive — not
  "we lack order flow" but "we lack a per-trade aggressor flag". Artefact: section `## R1-D5`.
- **R1-D6 (stretch) — Falsifiability audit of the day-type and opening-type taxonomies.** For
  each label: is it knowable before the day ends, or only assignable afterwards? Compare against
  the way `workspace/studies/ORB_ICT_FINDINGS.md` disposed of "Power of Three". Artefact:
  section `## R1-D6`.

### Track R2 — Relational: second series, curve, calendar, surface
Main file: `workspace/roundtable/research/R2_relational.md`

- **R2-D1 — Class II family catalogue.** Every family II-1…II-19 under the §4 schema. *Done
  when:* nineteen entries with all eight fields and a verdict. Artefact: sections `## II-1 …`
  through `## II-19 …` in `R2_relational.md`.
- **R2-D2 — Operating manual for three relational families that real desks run at size:** one
  calendar-spread / roll-yield programme, one inter-commodity spread end to end (crack or
  crush — your choice, say which and why), and one scheduled-event trade with the actual clock.
  *Done when:* each has leg ratios, entry and exit triggers, sizing convention, roll mechanics
  and margin treatment concrete enough that a reader could paper-trade it. Artefact: section
  `## R2-D2 Operating manual`.
- **R2-D3 — The expressibility wall, and the proxy question.** First: exactly where this repo
  cannot hold a second series, cited by path and line. Second, and more useful: for each Class II
  family, the single cheapest *valid* proxy available in this repo, **or** the statement that no
  valid proxy exists and why a tempting one would be invalid. *Done when:* every Class II family
  has either a named proxy or a named reason there is none. Artefact:
  `workspace/roundtable/research/R2_expressibility_wall.md`.
- **R2-D4 — Seasonality feasibility note with the power arithmetic.** What history exists (per
  file in `csv/raw/`, spans measured not assumed), what each seasonal claim needs, and how many
  **independent** observations the data actually supplies for each — an annual effect over ten
  years of daily bars is ten observations, not 2,500. *Done when:* every seasonal sub-family has
  a stated independent-observation count and a verdict on whether the question is answerable here
  at all. Artefact: section `## R2-D4 Seasonality feasibility`.
- **R2-D5 — Event inventory against the repo's own calendar.** `futures_agents/econ_calendar.py`
  holds `ECON_RULES` from line 180. Which scheduled movers can this repo project, which cannot
  (candidates: WASDE, OPEC meetings, options expiry, quad witching, roll dates, Treasury
  auctions, month- and quarter-end rebalancing, Chinese data, EIA natgas), and for each absent
  one, what it would cost to add as a recurrence rule. *Done when:* the list of absent movers is
  explicit and each carries a cost line. Artefact: section `## R2-D5 Event inventory`.
- **R2-D6 — The options-informed block.** What a futures trader actually does with the options
  surface (dealer gamma and hedging levels, pinning, skew, IV-vs-RV, VRP) — operationally, not
  conceptually — and then the flat statement of what survives with zero options data. *Done
  when:* each sub-family has an operating description and a one-line reachability verdict.
  Artefact: section `## R2-D6 Options-informed`.

### Track R3 — Path and operation
Main file: `workspace/roundtable/research/R3_path_operation.md`

- **R3-D1 — Class III family catalogue,** split explicitly into **entry families** (III-1…III-6)
  and **operating layers** (III-7…III-19), all under the §4 schema. *Done when:* nineteen entries
  with all eight fields and a verdict. Artefact: sections `## III-1 …` through `## III-19 …`.
- **R3-D2 — The operating-vocabulary matrix.** One row per operating axis a real futures operator
  uses; columns: *what operators do*, *library handle with path:line*, *verdict*
  (expressible / expressible-but-never-varied / inexpressible), *evidence*. Anchor on
  `futures_agents/strategies/base.py` — `StopKind` (line 187), `TargetKind` (165), `ExitModel`
  (195) and `StrategyFilters` (380) — and on the exit catalogue in
  `futures_agents/strategies/combinator.py:43-128`. *Done when:* no axis is unlabelled and every
  verdict cites a line. Artefact: `workspace/roundtable/research/R3_operating_vocabulary.md`.
- **R3-D3 — Sizing and pyramiding as strategy.** Catalogue the sizing schemes and the
  scaling-in schemes, say how each is actually operated, then adjudicate whether this harness can
  express any of them. Two specific things to settle: the engine's position-lifecycle rule at
  `futures_agents/backtest/engine.py:303-308`, and whether the backtester ever consults
  `futures_agents/risk/manager.py` / `account.py` at all or whether those only serve live
  proposals. *Done when:* each scheme has an operating description and an expressibility verdict,
  and the two specific questions have a path-cited answer. Artefact: section `## R3-D3`.
- **R3-D4 — Variance versus expectancy.** For every operating axis in R3-D2, state whether the
  claim made for it is *changes expectancy* or *only reshapes the distribution*, and mark which
  ones this repo has already measured — `BRIEF.md` rules 3 and 4, D12, D15, D18, D19, and
  `scan_reports/2026-09-24_strategy-studies_21-study-programme.md` §"What survived programme-wide
  correction". *Done when:* no axis is unlabelled and nothing already settled is re-argued.
  Artefact: section `## R3-D4`.
- **R3-D5 — The untested-and-cheap list.** Operating rules already expressible with the existing
  `ExitModel` / `StrategyFilters` vocabulary that **no completed study has ever varied**, ranked
  by cost to test. **This list is allowed to be empty** — if it is, say so and show how you
  checked. *Done when:* the list exists with a stated search method, empty or not. Artefact:
  section `## R3-D5`.
- **R3-D6 (stretch) — Sequence support.** D37 says the combinator cannot express a sequence at
  all. Which Class III families require one, and what the minimum sequence primitive would be.
  Artefact: section `## R3-D6`.

---

## 4. The mandatory entry schema

Every family entry in R1-D1, R2-D1 and R3-D1 uses these eight fields, in this order, with these
headings. This is not style policing: it is what makes three independent tracks merge into one
catalogue and stay comparable.

```
## <id> <family name>

**Mechanism.** One or two sentences: why the trade makes money when it makes money.
**Who runs it, at what size.** Prop / CTA / bank desk / retail; typical capital and horizon.
**Where it lives.** Instruments, timeframes, sessions.
**Minimum data.** The data objects required. Be specific: "per-trade aggressor flag", not "order flow".
**How it is operated.** Entry trigger, invalidation, exit logic, sizing, typical hold,
  and the shape of its return distribution as reported (hit rate / payoff), marked [general knowledge].
**How it dies.** The characteristic failure mode, and what regime kills it.
**Expressibility here.** One of:
    EXPRESSIBLE                  - buildable from what is in futures_agents/ today
    PARTIAL                      - a degraded or proxied version is buildable; say what is lost
    INEXPRESSIBLE-DATA           - the data object does not exist in csv/raw/
    INEXPRESSIBLE-ARCHITECTURE   - the data could exist but the code cannot carry it
  Every verdict cites path:line.
**Already tested here?** Yes with a path to the report, or No. If yes, one line on the result and
  then stop — do not re-litigate it.
```

Marking, per `BRIEF.md` rule 3: every claim is `[general knowledge]`, `[repo-verified: path:line]`
or `[measured: command + result]`. A claim about this repo with no path is an opinion.

---

## 5. Boundaries — the adjudications I am making now, so you do not collide

These are decided. If you disagree, write it in `OPEN_QUESTIONS.md`; do not act unilaterally.

1. **Volatility.** R3 owns volatility as a *state of the traded series* (regime labels,
   expansion/contraction cycles, vol-scaled sizing). R2 owns volatility as a *traded instrument*
   (VX term structure, variance risk premium, the options surface). The test: if it needs a second
   series, it is R2's.
2. **News and events.** R2 owns the calendar, which releases matter, and the event-response
   families. R3 owns generic post-entry management and does not restate event tactics.
3. **VWAP.** R1 owns VWAP as a participant-behaviour object (institutional benchmark, anchored
   VWAP, execution footprints) and owns the audit of the five `vwap` conditions. R3 owns
   `StopKind.VWAP_BAND` as a stop primitive only.
4. **Profile and TPO.** Entirely R1's. R3 does not touch the six `profile` conditions.
5. **Lead-lag.** R2 owns lead-lag *between contracts*. Cross-timeframe lead-lag inside one symbol
   is already settled in `workspace/studies/STRUCTURE_FINDINGS.md` (`s_leadlag`, and the
   `break_of_structure`@240m retraction). Nobody re-opens it.
6. **Sizing.** R3's, exclusively — including portfolio heat and correlated-exposure limits. Spread
   **leg ratios** are spread construction and belong to R2.
7. **The engine.** R2 cites the one-frame architecture at the entry points; R3 cites the position
   lifecycle inside `run_many`. Both will name `engine.py`; different lines, no overlap.
8. **The condition inventory.** Nobody re-derives the 79 conditions or the 19 groups. Appendix A
   below is the table; cite it and move on.
9. **The settled findings.** The eight rules in `BRIEF.md` §"The eight rules" are not in scope for
   re-argument by anyone. Contradicting one requires evidence, not a paragraph.
10. **(Round 2)** Class reassignment stays reserved to the manager, and **the adjudications are now
    a separate file**: `manager/ADJUDICATIONS.md`, one block per ruling, each stating what the
    decision costs. Ten rulings are recorded there as of 2026-09-26 23:10 ET, covering both mis-cuts,
    `R1-Q1`, `R1-Q2`, `R3-Q2`, all four `BT1`/`BT3` requests and all four `R1` requests. **Do not
    re-raise a question settled there**; if you think a ruling is wrong, cite its ADJ id and the path
    you read it at, in a `msgs/` file.

---

## 6. Pre-registered expectations

> **ROUND-2 NOTE — these have been tested and several are refuted. See amendment A4 at the top of
> this file before citing anything below.** Headline: R1's INEXPRESSIBLE-DATA count was **9** (I said
> ≥10) and its strict EXPRESSIBLE set was **0** (I said ≤3, so the result is *below* my floor);
> market profile is the family whose blindness is **cheapest to remove**, not the least testable;
> R2's path-cited repo claims were **89** (I said fewer than ~15 would mean under-delivery); R3-D5
> holds **6 strict items plus 2 artefact replays** (I said ≤2). What survived: R1's proxy-vs-"does not
> work" discipline, the opening-type/day-type split (half), R2's spread-and-carry emptiness for
> `II-1`/`II-2`, R2's seasonality kill, R2 being the most likely track to be mis-cut, R3's
> pyramiding verdict, and R3's central "most of the operating layer is a variance transform" — with
> the correction that the survivor set is **larger** than my three, because the whole Channel-2 block
> (11 axes) is non-cancelling and is almost entirely unreachable here.

I am writing these down **before** reading any of your output so that later we can tell whether
this roundtable learned something or merely confirmed me. If you refute one of these, say so
loudly — that is the most interesting thing you can hand back.

### Track R1
- **Hardest:** separating *"our order flow is a proxy"* from *"order flow does not work"*. I
  expect R1 to establish the first from `futures_agents/indicators/volume.py:1-9` and then be
  tempted into asserting the second's negation. Do not. The honest form is "untested here".
- **I expect to come back empty:** any *operational* detail of footprint reading that survives
  contact with 1-minute OHLCV. Concretely, I predict **≥10 of the 15 Class I families land on
  INEXPRESSIBLE-DATA**, and that the EXPRESSIBLE set is ≤3 and consists of things already
  measured and already null (session-level sweeps, profile location, VWAP location).
- **I expect a specific surprise:** that market profile / TPO turns out to be the *best-documented
  operating framework in the whole roundtable* and simultaneously among the least testable here.
- **I expect one family to dissolve on inspection:** the day-type and opening-type taxonomy,
  reducing to post-hoc labelling of the same shape as "Power of Three" in
  `workspace/studies/ORB_ICT_FINDINGS.md`. If it does not dissolve, that is a finding.

### Track R2
- **Hardest:** resisting the one-sentence answer. The expressibility verdict for most of Class II
  is trivially "no" — one `SymbolFrame` per backtest — so the risk is R2 delivers that and stops.
  The work is the operating half, and I expect R2's ratio of `[general knowledge]` to
  `[repo-verified]` claims to be the worst of the three tracks. **Pre-registered threshold: fewer
  than ~15 path-cited repo claims in R2's output means the diagnostic half under-delivered.**
- **I expect to come back empty:** the entire spread / carry / curve block, and not merely as
  inexpressible but as **unobservable** — no second expiry, no contract-month labels, no open
  interest. I predict R2 finds the only place a roll is visible in this data is a **defect** (D40,
  the spliced grain CSVs) rather than a feature.
- **I expect one genuine positive:** seasonality and the scheduled-event window are the two Class
  II families with a real path to being expressed here, because `StrategyFilters.days_of_week`
  already exists and `econ_calendar.py` already projects recurrence identically backwards and
  forwards. I also expect the power arithmetic in R2-D4 to kill most of it anyway — which is a
  result, and a better one than a hopeful table.
- **I expect a wrong prior of mine to surface here.** Of the three tracks this is where I know
  least, so treat my framing of Class II as the most likely to be mis-cut.

### Track R3
- **Hardest:** telling an operating rule that is *real strategy* apart from one that only
  reshapes the R distribution. This repo has already measured the win-rate/payoff cancellation
  four times (`BRIEF.md` rule 3). I expect R3 to keep rediscovering it and I want it labelled
  once, not re-derived.
- **My central prediction:** **most of the operating layer is a variance transform, not an
  expectancy transform.** The exceptions I expect to survive are the ones that change costs or
  change the number of trades — session-close flattening, time stops, cost-aware execution — not
  the ones that move stops and targets around.
- **I expect to come back empty:** pyramiding. I expect `engine.py:303-308` makes III-8
  INEXPRESSIBLE-ARCHITECTURE outright, and that the interesting content is the cost of changing
  it.
- **I expect the scarcest thing in the whole roundtable to live here:** an operating rule that is
  (a) expressible with today's vocabulary and (b) never varied by any completed study. I predict
  **≤2 exist.** R3-D5 is allowed to be empty and I will not read an empty R3-D5 as failure.

### And the risk I am pre-registering against the roundtable as a whole
That all three tracks return "inexpressible" and the catalogue becomes a restatement of *"we only
have OHLCV on one contract"* — which we already know. The defence is §4's requirement that every
INEXPRESSIBLE verdict name **the one specific missing primitive**, so the merged output reads as a
build-and-acquire order rather than a lament.

---

## 7. The three questions I most want answered

Answer these in your own file, in a closing section headed `## Answers to the manager's three
questions`, from your track's evidence only. Say "my track cannot speak to this" where true.

1. **Is our null result a property of the market, or of our information set?** Of the families in
   your class, how many require information this repo has never had — sub-bar transactions, a
   second expiry, open interest, an options surface, a positioning report? If most widely-operated
   futures strategies need data we do not possess, then "nothing here is live-eligible" is a
   statement about our data and not about futures trading, and the repo's next move is acquisition
   rather than more search.
2. **Is there any family that is expressible with today's combinator, widely operated, and never
   tested here?** Ranked, cheapest first. This is the only kind of finding that yields a new
   hypothesis without new data or new code. **It is allowed to be empty.**
3. **Which single missing primitive unlocks the most families in your class?** One answer per
   track, each with a count. I will reconcile the three. If sequence support (D37) unlocks n
   families, a multi-series frame unlocks m, and a true aggressor flag unlocks k, then this repo's
   build priority is decided by measurement instead of taste — which is the answer that would
   actually change how it operates.

---

## 8. What you may run

Reading the code and the existing artefacts **is** the work (`BRIEF.md` rule 5).

**Permitted:** any read; `grep`/`find`; short `python3 -c` inspections of the library, the
combinator, `coverage.py` (`reachable_conditions()`, `unreachable_conditions()`, `uncovered()`),
`config.py` and `econ_calendar.py`; CSV header and span checks; `generate_combinations` /
`generate_strategies` with `max_total <= 400` for reachability questions only.

**Forbidden:** `run_portfolio`, `run_backtest`, any sweep, anything that produces an expectancy or
a z-score, any write anywhere under `csv/` (read-only and immutable, no exceptions), any write
into another agent's directory, git commit or push.

Anything you run must finish in about a minute and you must paste the **exact** command beside the
result. If a number matters, it needs the command.

Note D28 before you are tempted: `T.ab` inflates z by roughly 3.3x. Round 1 should not be
producing comparative statistics at all, so the safest route is not to.

---

## 9. Paths you will need

```
workspace/roundtable/BRIEF.md                      read first, in full
workspace/roundtable/DIVISION.md                   this file
workspace/roundtable/THROTTLE.md                   why dispatch timing is not yours or mine
workspace/roundtable/OPEN_QUESTIONS.md             ask another researcher; I route it
workspace/roundtable/msgs/                         the conversation log; read ALL of it before writing
workspace/roundtable/research/                     your deliverables live here

futures_agents/strategies/library.py               79 conditions, 19 groups (Appendix A)
futures_agents/strategies/base.py                  Condition, ExitModel, StopKind, TargetKind, StrategyFilters, Strategy
futures_agents/strategies/combinator.py            13 templates, exit catalogue, sampling, GLOBAL_EXCLUSIVE
futures_agents/strategies/coverage.py              SPEC_CONFLUENCES (39 entries) + the reachability check
futures_agents/strategies/profiles.py              per-symbol priors about what gets tested
futures_agents/backtest/engine.py                  the backtester, one SymbolFrame at a time
futures_agents/backtest/costs.py                   the cost model
futures_agents/risk/manager.py, risk/account.py    sizing and account limits
futures_agents/features.py                         FeatureSnapshot / TFSnapshot: what a condition can see
futures_agents/indicators/volume.py                delta, CVD, VWAP, volume profile
futures_agents/econ_calendar.py                    ECON_RULES from line 180
futures_agents/config.py                           ContractSpec, correlation_group, TIMEFRAME_GROUPS (line 312)

csv/raw/                                           48 files, READ ONLY, all with header
                                                   open_time,open,high,low,close,volume
workspace/studies/DEFECTS.md                       D1-D43. Read before trusting any number a tool prints
workspace/studies/RANKING_FINDINGS.md              the ranking/placebo/deflation verdict
workspace/studies/STRUCTURE_FINDINGS.md            the five structure studies
workspace/studies/ORB_ICT_FINDINGS.md              ORB and ICT
workspace/chrono/FINDINGS.md                       chronological rotation (there is none)
scan_reports/                                      four reports; README.md indexes them
CALLOUT.md                                         how this repo is currently operated live
```

---

## 10. Round 2

Decided by me after reading all three files, and dispatched by the parent session, not by me
(`THROTTLE.md`). Three shapes are in contention and I will pick from your answers to §7:

- **(a) The build-and-acquire order.** If §7 Q3 gives three different primitives, round 2 costs
  and ranks them.
- **(b) Depth on whatever survives.** If §7 Q2 is non-empty on any track, round 2 turns those
  families into an operating specification precise enough to implement.
- **(c) Adversarial cross-review.** Each researcher attacks another track's expressibility
  verdicts — the most likely place for an over-claimed INEXPRESSIBLE to be caught.

**I am pre-committing to (c) on at least one track regardless of the answers**, because a
catalogue of "we cannot do this" that nobody stress-tested is exactly the artefact that would make
this roundtable feel productive without being correct.

---

## Appendix A — the 19 condition groups, 79 conditions

Measured, not transcribed:
`python3 -c "from futures_agents.strategies.library import CONDITIONS, CONDITION_GROUPS; ..."`
against `futures_agents/strategies/library.py`. Cite this table; do not rebuild it.

| group | n | signals | filters | conditions |
|---|---|---|---|---|
| trend | 8 | 6 | 2 | ema_stack, ema_fast_above_slow, price_above_ema50, price_above_ema200, adx_trending*, di_direction, slope_directional, efficiency_high* |
| momentum | 6 | 6 | 0 | rsi_directional, rsi_extreme_reversal, macd_directional, macd_hist_direction, stoch_directional, stoch_extreme |
| vwap | 5 | 4 | 1 | above_vwap, vwap_proximity*, vwap_band_extension, vwap_band1_bounce, vwap_reclaim |
| volume | 3 | 0 | 3 | relative_volume_high*, volume_surge*, volume_not_thin* |
| orderflow | 3 | 3 | 0 | cvd_directional, delta_confirms_bar, delta_divergence |
| structure | 5 | 5 | 0 | structure_trend, break_of_structure, pullback_to_support, fvg_nearby, range_position_extreme |
| liquidity | 7 | 7 | 0 | prior_day_sweep, overnight_sweep, session_extreme_sweep, prior_day_breakout, opening_range_breakout, opening_range_fade, initial_balance_break |
| meanreversion | 3 | 3 | 0 | bollinger_extreme, bollinger_mean_pull, keltner_outside |
| volatility | 3 | 0 | 3 | volatility_normal*, volatility_expanding*, volatility_compressed* |
| regime | 3 | 1 | 2 | regime_trending*, regime_ranging*, regime_matches_direction |
| multitimeframe | 3 | 2 | 1 | mtf_aligned, mtf_strongly_aligned, mtf_not_conflicted* |
| time | 4 | 0 | 4 | avoid_lunch*, opening_drive_window*, power_hour*, after_opening_range* |
| profile | 6 | 4 | 2 | poc_reversion, value_area_edge, value_area_breakout, lvn_rejection, away_from_hvn*, open_outside_value* |
| fibonacci | 4 | 3 | 1 | fib_golden_pocket, fib_shallow_retrace, fib_extension_reached, fib_sr_confluence* |
| imbalance | 3 | 2 | 1 | imbalance_bar, imbalance_pullback, no_recent_imbalance* |
| supplydemand | 3 | 2 | 1 | zone_touch, fresh_zone_approach, away_from_zone* |
| openinterest | 2 | 1 | 1 | oi_price_confirmation, oi_expanding* |
| news | 3 | 0 | 3 | outside_news_blackout*, no_imminent_release*, post_news_window* |
| candlestick | 5 | 4 | 1 | candle_reversal, candle_engulfing, candle_decisive_close, candle_close_strength, inside_bar_compression* |

`*` = `ConditionKind.FILTER`. Totals: **79 conditions, 19 groups, 53 SIGNAL / 26 FILTER**
`[measured: python3 -c "from futures_agents.strategies.library import CONDITIONS; from futures_agents.strategies.base import ConditionKind; ..." -> signals 53 filters 26 total 79]`.

The **13 strategy groups** in `combinator.py:166-332` (BREAKOUT, FIBONACCI, LIQUIDITY,
MEAN_REVERSION, MOMENTUM, MULTI_TIMEFRAME, OPENING_RANGE, PULLBACK, REVERSAL, SUPPLY_DEMAND,
TREND, VOLUME_PROFILE, VWAP) are **templates over these 19 condition groups** — a different
object from the condition groups, and easy to conflate. The stop vocabulary is five kinds
(`StopKind`, `base.py:187`), the target vocabulary three (`TargetKind`, `base.py:165`).

## Appendix B — six facts, so nobody spends a turn rediscovering them

All `[measured: head -1 csv/raw/*.csv | sort -u]` and `[repo-verified]`:

1. **Every one of the 48 files has the header `open_time,open,high,low,close,volume`.** There is
   no open-interest column, no bid/ask split, no contract-month label, no settlement price.
2. **1 minute is the finest bar available.** No tick data, no time-and-sales, no depth.
3. **Intraday files are capped at ~5,000 bars.** `MGC_1h.csv` is 5,000 bars spanning
   2025-11-05 → 2026-09-22, i.e. about eleven months, not years. Daily files are long:
   `MGC_1d.csv` 2,511 bars from 2016-09-26; `MES_1d.csv` 1,859 from 2019-05-03.
4. **Only three futures symbols have a daily file: MGC, MES, MNQ** (plus the `SPY_1d`/`QQQ_1d`
   ETF proxies). **MCL has no daily file** — its run is 1m/5m/15m/30m/1h only, so every
   MCL question is capped at about eleven months of history. `ES` and `NQ` exist only as
   `1h` and `5m`; the grains (`MZC`, `MZS`, `MZW`) have no daily either and are excluded
   anyway under D40.
5. **`futures_agents/backtest/engine.py:548` and `:554` each take one `frame: SymbolFrame`.** One
   backtest sees one symbol.
6. **`futures_agents/strategies/coverage.py` is the nearest thing this repo already has to the
   artefact you are building** — it maps the original specification's confluence variables to the
   conditions that make each one tradeable, and `reachable_conditions()` /
   `unreachable_conditions()` answer whether a condition can appear in any generated strategy.
   `[measured: python3 -c "from futures_agents.strategies.coverage import SPEC_CONFLUENCES, unreachable_conditions; print(len(SPEC_CONFLUENCES), unreachable_conditions())" -> 39 []]`.
   Two things follow. First: **nothing is currently unreachable**, so "unreachable" is not where
   the blind spots are — they are outside `SPEC_CONFLUENCES` entirely, which is the gap this
   roundtable exists to name. Second: the module docstring says the brief named *thirty-eight*
   variables and the dict now holds **thirty-nine** — a small unexplained drift, recorded here,
   assigned to nobody, worth one line if any of you happens to resolve it.

---

# Round-3 amendment — two things §1 does not describe, recorded here so nobody looks for them in it

**2026-09-27 04:05 ET, manager.** `DIVISION.md` §1 has been a **mechanism taxonomy only** since ADJ-0,
and `manager/BOARD.md` assigns work. Two additions that matter for reading this file correctly:

1. **There is now a second programme and §1 does not cover it.** Seven agents (EF1–EF7) work an
   **account-owner request** under `edge/EDGE_BRIEF.md` — top 10 per symbol for swing and for scalp
   inside an 18:00 ET → 16:00 ET session rule. It is **not** a `MAIN-<nn>`, it has no class in §1, and
   it is deliberately not decomposed by me. Its facts, gate and inherited rules are **`BOARD.md` §8**.
   Do not look for it here, and do not file its cells against the 53 family ids: the session rule is a
   capability the shipped engine does not have (`engine.py:470-473` fires at the *contract's* RTH close,
   and `allow_overnight` is `True` at no call site anywhere), so the programme's first object is a
   harness, not a family.
2. **The audit vocabulary is canonical in `BRIEF.md`, not here and not in `ADJUDICATIONS.md`.**
   `CLEAN` / `PROXY` / `DEGRADED` / `VOID` / `DEAD` / `MISNAMED` / `MISFILED`, with `VOID` stated per
   (symbol, timeframe, **frame**) plus any deciding scope flag and carrying a `REACHED` / `FORWARD`
   line (`R-14`). `ADJ-8`'s four-term set is **retired** and mapped in ADJ-13a. The reason it moved:
   twelve agents read `BRIEF.md` and only some read the board's rulings, and a fixed vocabulary living
   where only some agents look is the failure `REGISTRY.md` exists to prevent — R4 had to write a
   translation table to make its 31 verdicts collate, which is the measured cost of having had two.
