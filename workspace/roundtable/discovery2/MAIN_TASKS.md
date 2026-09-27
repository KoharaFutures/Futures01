# MAIN_TASKS — DISC2's output

**Owner:** DISC2 (`OWNERSHIP.md`). DISC1 owns `discovery/MAIN_TASKS.md` and allocates **odd**
`MAIN-<nn>`; **DISC2 allocates even** (`OWNERSHIP.md`, "Main task numbering"). `MAIN-01` is DISC1's.

One entry per avenue judged worth depth, stated **at altitude**. **Discovery does not decompose
these** — the manager's first move is to ask the researcher what breakdown it needs, and the
breakdown is the researcher's (`PIPELINE.md` §2–§3).

---

## MAIN-02 — The region the sampler never moved in: a 25-year, ten-sector daily cross-section

**Raised by:** DISC2 burst 01 (`discovery2/bursts/01_cross-sectional-universe.md`), 2026-09-27.
**Avenue:** `II-7` — cross-sectional momentum and cross-sectional carry across a futures universe.
DISC1 records it `DEFERRED` in `discovery/AVENUES.md`; **its named blocker is measured lifted**
(`discovery2/AVENUES.md` `DISC2-D1`), and this task carries the avenue. Its twin on the
time-series side is `III-1`, still `OPEN-PARTIAL` with a stopping point of "named only" for the
classic version.

**This is a diagnostic task, not a search for edge.** `BRIEF.md` is explicit that the roundtable's
value is descriptive and diagnostic, and that "a finding of the form 'this family is widely used and
our harness cannot express it' is worth more than another expectancy table." A scope that reads this
as "go and find the edge the other 2.98M evaluations missed" has mis-read it, and the strongest
single reason to say so is in §"Why it matters" point 5: **this task cannot produce a live-eligible
strategy under the programme's own gate even if the family works exactly as advertised.**

### What the avenue is

**One sentence:** this programme searched *rule selection, at fixed size, on one contract, intraday,
over roughly 274 sessions*, and the futures families with the strongest documented out-of-sample
record live in the region that is **outside that box on four axes at once** — many markets, daily or
slower, size-varying, and held for weeks.

The families: **time-series momentum / trend-following** (rank the market against its own past) and
**cross-sectional momentum and carry** (rank markets against each other and go long the top,
short the bottom), operated as a diversified, volatility-scaled, monthly-or-weekly rebalanced
portfolio. This is the managed-futures industry's entire product and the most replicated set of
results in the futures literature — Moskowitz, Ooi and Pedersen on time-series momentum;
Asness, Moskowitz and Pedersen on value and momentum everywhere; Koijen, Moskowitz, Pedersen and
Vrugt on carry as a cross-asset premium; and the long-horizon trend replications that extend the
record over a century `[general knowledge — **not verified here, and this task must not assume
it**; primary sources were not fetched and prior work in this repo records egress failures on
some of them (`workspace/studies/ORB_ICT_FINDINGS.md:250-258`)]`.

**Four structural exclusions, each independently recorded in this repo as unexplored, and all four
binding at once.** That simultaneity is the point — any one of them alone would be a gap; all four
together mean the region was never approached.

| axis | what the programme did | where the repo records the exclusion |
|---|---|---|
| **market count** | 1 contract per backtest | `BLOCK-ONEFRAME`; R2's Wall A / Wall B; `engine.py:548,554` take one `frame` |
| **sample length** | ~274 sessions at 60m; longest anything is MGC daily 2,511 bars | `discovery/AVENUES.md` burst-01 addendum; `DIVISION.md` Appendix B #3 |
| **position size** | one flat risk unit, every evaluation | `msgs/01_manager_all_division.md`; DISC1's `III-7`; R3's `R3_path_operation.md` B-1 ("sizing is not in the measured universe at all") |
| **holding period** | intraday, with `exit_at_session_close` on by default and `allow_overnight` never True in any published result | R3's `R3_path_operation.md` A-7, A-10; `21-study-programme.md:40-46` |

**And the measured fact that changes the avenue's status:** the vendor this repo has already proven
it can reach serves **36 of 37 probed tickers with 2,317–2,513 daily bars on a common 2016→2026
span across ten sectors**, and on a 2001 start serves **≈6,460 daily bars per market — a common
25.7-year span** across US equity index, rates, FX, precious and industrial metals, energy, grains,
softs, livestock and `^VIX`, with **zero code change** (`ticker_for` passes any root through;
`INTERVALS[1440]` caps daily lookback at 25 years)
`[measured: `discovery2/AVENUES.md` `DISC2-D1`, both probes, availability only, nothing written]`.

### Why it plausibly matters *here*, given this repo's data and settled findings

1. **It is the largest possible instance of the manager's own standing rule `R-11`.** `R-11`, written
   this turn: *"any claim that 'this has already been tested' must name the dimension that was
   varied. `n = 2.97M` is coverage of the dimension the sampler moved in and nothing else"*
   `[repo-verified: msgs/05_manager_all_round2-board.md]`. The sampler moved in entry rule sets,
   stop kind, target kind, timeframe, symbol and window. **It never moved market count, sample
   length, size or holding period** — and the reference-class families require all four to move
   together. The catalogue this roundtable exists to build owes a statement of what the 2.98M
   covers, and this is the biggest uncovered region in it.
2. **A null here would be worth far more than another intraday null, and that asymmetry is the whole
   argument for the task.** Every negative result this programme holds is a negative on families
   with no strong prior — ORB, ICT, VOLUME_PROFILE aliases, MEAN_REVERSION. A negative on
   *time-series and cross-sectional momentum, on 25 years, on a ten-sector universe* would be a
   negative against the strongest prior in the asset class, and would be the first result here that
   distinguishes "this repo's harness finds nothing" from "there is nothing to find at the scale
   this repo measures at." Either outcome is publishable inside this programme. **`BRIEF.md`'s
   own standard — report absence as a result — is satisfied by both branches.**
3. **The blocker was never a data blocker, and the record says so twice without applying it.**
   DISC1's Class II preamble already states the general form — *"'we have no series for X' is now a
   purchase order"* — and then leaves `II-7` `DEFERRED` because `II-7`'s blocker is phrased as
   universe *size* rather than as a missing series. R2 files `II-7` under **"genuinely unobservable
   from here … a 40-market universe"** `[repo-verified: research/R2_relational.md:918,1267]`,
   beside an options surface and a news feed — objects that really are hard. **R2 is right about
   the disk and its premise about the vendor is untested** (`DISC2-D2`). A blocker that dissolves
   into one batch call is the cheapest real discovery available and it should be recorded as such
   whichever way the family then measures.
4. **Two of the four exclusions have already been independently flagged as the interesting ones by
   other tracks, from inside their own work.** R3: sizing *"is not in the measured universe at
   all"*, and of its four channels only two can move expectancy
   `[repo-verified: research/R3_path_operation.md, B-1…B-3]`. DISC1: `III-7` was *"the single
   largest named-only avenue in the ledger"*. Volatility-scaled sizing across a cross-section is
   not a cosmetic overlay on this family — **it is constitutive of it**: the premium documented in
   the literature is a premium on a risk-weighted portfolio, and equal-notional or one-flat-unit
   versions are a different object. So `III-7`'s open question and `II-7`'s open question are the
   *same* question seen from two classes, which is the third instance this round of `DIVISION.md`
   §1 hiding a question between classes (ADJ-0, `R2-Q1`, `MAIN-01`).
5. **It cannot produce a live-eligible strategy under this programme's gate, and stating that up
   front is what keeps it honest.** `t ≈ SR × sqrt(years)` `[general knowledge — Lo (2002)]`. On
   25.7 years, `sqrt(years) = 5.07`, so clearing `free_t = 5.46` needs a sustained annualised
   Sharpe of **≈ 1.08** — above anything the trend literature reports net of costs. On the 274-session
   span every published result rests on, the same gate needs **≈ 5.8**, which nothing in any asset
   class has ever sustained `[general knowledge]`. **Two readings follow and the task should carry
   both:** (a) this avenue is a calibration exercise, not a candidate pipeline; and (b) `free_t` and
   sample length are two knobs, this programme has only ever turned one, and the direction of that
   observation is *unfavourable* — it makes the largest `t` ever found here (3.923, which would
   require Sharpe ≈ 4.2 on its span) look more like an artefact, not less. See
   `discovery2/AVENUES.md` `DISC2-D5`, including the repo's own `1.177` floor at
   `workspace/studies/toolkit.py:58` and the heavy counter-argument that sits beside it.
6. **The repo is half-built for it already, in a way nobody has connected.** `correlation_group`
   already carries a sector taxonomy — `ENERGY`, `FX_MAJORS`, `GRAINS`, `PRECIOUS_METALS`, `RATES`,
   three equity buckets `[measured: `DISC2-D3`]` — which is exactly the sector-neutrality control a
   cross-sectional study needs; and `CONTRACTS` already holds **`ZN` and `M6E` specs for which no
   price series exists in either store.** The registry anticipated rates and FX and the data never
   arrived. `config.py:100-101` states that adding a contract makes the rest automatic.
7. **The one measurement that matters needs no engine change at all.** Whether a cross-sectional or
   time-series momentum premium exists in this data is a ranking-and-averaging computation on N
   aligned daily series. `BLOCK-ONEFRAME` / Wall B blocks **trading** a cross-section, not
   **measuring** one — the same distinction DISC1 drew for Class II and R2 sharpened into two walls.
   So the diagnostic half is reachable now and the execution half is priced already by R2.

### What it would take to know

Unknowns at altitude, in rough dependency order. The breakdown, the granularity and the order are
the scope's (`PIPELINE.md` §3, Mode SCOPE), **including the right to come back and say this is two
sub-tasks, or five, or that the first gate kills it.**

- **The roll convention, first, and it may end the task.** What *is* a Yahoo `<ROOT>=F` daily
  series? `yahoo.py` applies `auto_adjust=False` and contains **no roll handling of any kind**
  `[measured: `DISC2-D1`]`, and the module's own header warns that `MNQ=F` is not TradingView's
  `MNQ1!` because of *"different roll convention"* `[repo-verified:
  futures_agents/data/yahoo.py:10-13]`. An unadjusted front-month series has a **price gap at every
  roll**, and a momentum signal reads a roll gap as a return. This repo has already been bitten by
  exactly this failure mode and given it a number: **D40**, where a spliced continuous series
  produced 367 close-to-open gaps above 2% on MZC, 47% of which fully reverse
  `[repo-verified: workspace/studies/DEFECTS.md, D40]`. **If `=F` dailies are unadjusted, every
  number downstream is contaminated in an unknown direction and the honest outcome is
  `CLOSED-EMPTY` with the reason recorded.** D40 also supplies the diagnostic: flat-bar rate,
  zero-volume rate, and the count and reversal rate of >2% close-to-open gaps, per market.
- **The thin two-thirds of the universe, and whether it is tradeable at all.** A broad universe is
  broad *because* it includes grains, softs and livestock — 13 of the 35 markets I probed. D40's
  measured economics on this repo's own thin markets are **round-turn fees at 9.2% of one R (MZC)
  against 0.17% (NQ)**, 26.3% flat bars and 11.3% zero-volume bars. The literature's universes are
  full-size and institutionally executed; this repo's cost model has **no size term at all** in
  `SlippageModel` `[repo-verified: research/R3_path_operation.md A-11]`. A scope needs to say
  whether the answer is "restrict to the liquid half and lose the diversification that is the
  family's whole mechanism" or "carry the thin half with honest costs and watch it lose money", and
  **either answer is a result.**
- **The price of the universe, which is 28 contract specifications, not 28 downloads.** Seven of the
  35 roots have a `ContractSpec`; 28 do not `[measured: `DISC2-D3`]`. Each needs tick size, point
  value, per-side commission, exchange fee, slippage ticks, minimum stop ticks and typical ATR —
  looked up, not derived, and precisely the fields that decide the previous bullet. **Understated
  costs is one of the named anti-overfitting hazards and this is where it would enter.**
- **Survivorship of the ticker list itself.** A basket of today's liquid tickers is a *selected*
  basket, and the probe demonstrated tickers do vanish: `DX=F` returned HTTP 404, "Quote not found"
  `[measured: `DISC2-D1`]`. Delisted and de-liquefied contracts are absent by construction, which
  biases a cross-sectional study in the favourable direction. The repo already names "no
  cross-sectional selection is performed" as a survivorship *mitigation* it currently enjoys
  `[repo-verified: workspace/strategy_research/w3_publish.py:249]` — **this task gives that
  mitigation up, and must say so.**
- **Which sample, and the nested-window trap it must not repeat.** Three candidate substrates, and
  they are not interchangeable: the vendor's 25.7-year common span; `data/archive/`'s daily series
  (**`CL_1440m` is 6,192 bars from 2002-02-05 — the longest series in this repository and used by
  nothing**; `MGC_1440m` is 4,008 bars from 2010-10-04, ~6 years before the published daily span;
  `MCL_1440m` holds **one row**) `[measured: `discovery2/AVENUES.md` `X-12` pointer]`; and
  `csv/raw`'s five daily files. `R-7` requires a substrate label on every number and forbids pooling
  `csv/raw` with archive. **The nested-window problem is the specific hazard**: this repo's own
  30 ⊂ 90 ⊂ 180 ⊂ 274 windows all ended on the same bar and it called that *"arithmetic, not
  replication"* `[repo-verified: BRIEF.md]`. A 25-year daily sample can be split into genuinely
  disjoint decades, and a scope should pre-register that split before computing anything.
- **What a positive would have to survive to be believed, pre-registered before it is looked at.**
  Walk-forward across disjoint decades; sector-neutral and equal-risk variants (the
  `correlation_group` taxonomy is the control); the placebo the programme already demands — and note
  that the natural placebo here is **rank-shuffled cross-sections**, which is a construction this
  repo has never built, all five existing placebos being entry-randomisations `[repo-verified:
  `discovery/AVENUES.md` `X-14`, `DISC-LEAD-03`]`; `D28` (never route a comparative claim through
  `T.ab`); `D48` (`_id=None` on every `replace`, assert arm-id uniqueness); and a stated search size,
  because a lookback grid of {3,6,12} months × {weekly, monthly} rebalance is six variants and
  must be counted as six.
- **Only then, and only if the above survives: what the answer says about the programme's null.**
  If the reference class also measures flat here, the 2.98M null is *corroborated* and the catalogue
  can say so with a reference class attached for the first time. If it measures as the literature
  reports, the null is **localised** to intraday single-contract rule selection at fixed size — and
  that is a statement about coverage, not a rescue of any strategy. This is the comparative half and
  needs the manager's assignment, a paired test, and a deflation statement.

### What discovery deliberately did not investigate

- **Any performance number.** No backtest, no sweep, no ranking, no expectancy, no z-score, no
  correlation, no return. I did not compute a single return from the probed series. **Nothing in
  this task claims that cross-sectional or time-series momentum makes money here or anywhere.**
- **Whether the literature's claim is true.** Cited `[general knowledge]`, deliberately unverified,
  primary sources not fetched. If a scope's first move is to treat the literature as an established
  prior rather than as a hypothesis, it has mis-read this section.
- **The roll convention.** Named as the first gate; not tested. I ran no gap diagnostic, no flat-bar
  count, no expiry-date clustering check on any probed series.
- **Per-expiry availability.** Whether the vendor serves individual contract months is **untested**,
  and it is the cheapest unasked question left — it would move `II-1`, `II-2`, `II-18`, `III-15` and
  `II-16`'s term-structure arm, and it would decide whether **carry** (the second half of `II-7`'s
  own title) is reachable at all or remains blocked by `BLOCK-NOSECONDEXPIRY`. **I did not probe it
  because those are DISC1's rows and R2's families**, and this task should be read as covering the
  *momentum* half of `II-7` with the *carry* half still blocked.
- **Wall A / Wall B costing.** R2 has priced both and I did not re-derive either. I checked only
  that the **measurement** does not need them.
- **Any write to a data store.** Nothing was fetched to disk. `data/archive/` is append-only and not
  mine; `csv/` is read-only for everyone, always. A scope that needs the universe on disk needs
  someone who owns a store to put it there, and that is a manager decision with `R-7` attached.
- **The `^VIX` series I incidentally proved is available.** 6,470 daily bars from 2001-01-02. That
  belongs to `II-16` and `II-5`, which are DISC1's rows and R2's families, and I recorded it as a
  pointer rather than folding it into this task to make it look bigger.
- **Whether any of this transfers between symbols.** It does not, by standing policy, and a
  cross-sectional study is the one design where that policy needs restating rather than assuming:
  ranking markets *against each other* is precisely a claim that they share a mechanism. **The
  independence rule and the cross-sectional premise are in direct tension, and I did not resolve
  it.** A scope must, before it ranks anything.
