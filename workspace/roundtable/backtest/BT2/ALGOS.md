# BT2 — algorithms built from R2's findings

One entry per algorithm, in the PIPELINE §4 shape. **Fidelity is the only field
that gates reporting: no number from a non-FAITHFUL algorithm is reportable.**

A word on what this file does and does not contain, because ALGO-1 produced a
lot of arithmetic while producing no result. Everything quoted below is either a
**count of calendar prints** or a **count of bars a filter can admit**. No
backtest has been run, no position opened, no expectancy computed, no strategy
ranked. Those counts are here because they bound the sample *before* it is spent,
and because reproducing R2's own event census is the cheapest evidence that this
code's event plumbing is the plumbing R2 was describing.

---

## ALGO-1 scheduled-event entry gate, on the contract's own session

- **Implements:** R2's Q2 answer, "Near-miss 1, and the one I would actually
  spend a round on: II-11 on MGC and MCL"
  (`research/R2_relational.md:1300-1308`), resting on the structural finding in
  **R2-D5** (`:177-236`) and the family write-up at **II-11**
  (`:629-668`). The operating clock ALGO-1 deliberately does *not* implement is
  **R2-D2c** (`:1048-1091`) — see C7.

- **Code:** `backtest/BT2/code/`
  - `event_clock.py:1-312` — the parameterised, look-ahead-free calendar clock
    (`EventClock:143-255`, `read:203-242`, `read_bar:244-252`; per-year event
    cache `_year_events:102-117`; the contract-session census
    `CensusRow:258-280` / `census:282-312`)
  - `event_gate.py:1-220` — the three gate factories (`avoid_event:135-166`,
    `after_event:168-199`, `into_event:201-220`) and the name-uniqueness
    machinery that stops the condition cache lying (`_make:102-132`)
  - `algo1.py:1-335` — store-aware loading (`load_series:97-118`), frame
    construction on the contract's own spec (`load_frame:120-139`), arm
    construction (`gate_arm:141-162`), and the pre-flight ceiling
    (`preflight:206-266`)
  - `test_algo1.py:1-526` — **26 tests, all pass**
    `[measured: python -m pytest -q workspace/roundtable/backtest/BT2/code/test_algo1.py
    → 26 passed in 46.65s]`

- **My reading of the finding.** Four claims, which I take as one algorithm.

  1. The repo's event vocabulary is **three FILTER conditions and no SIGNAL**
     `[repo-verified: futures_agents/strategies/library.py:1326,1334,1345]`, so
     the library can decline to trade an event and can never trade one. II-11 is
     therefore only reachable *in filter form* today.
  2. The one published test of that filter form — F11, `post_news_window` on 50
     MOMENTUM strategies, 112.6 trades → 1.5, zero publishable
     `[repo-verified: research/confluence/reversion_specialist.md:366-386]` —
     ran on **MNQ**, and on *synthetic* MNQ at that
     `[repo-verified: :7 "All figures below are MNQ synthetic"]`.
  3. MNQ's own RTH contains **7** in-session HIGH-impact event days in the
     intraday span; MGC's contains **32** and MCL's **49**, because four of the
     six HIGH rules print at 08:30 — before the 09:30 equity open and **ten
     minutes after gold's 08:20 pit open** — and EIA prints at 10:30, inside
     crude's 09:00–14:30.
  4. So the number 1.5 was set by the calendar, not by the strategy, and the
     family has never been asked on the two contracts where its in-session
     sample is not near-zero. R2 is explicit that this is *not* a claim that it
     works there.

  ALGO-1 is therefore **the filter form of II-11, re-asked on MGC and MCL with
  each contract's own `ContractSpec` session**, with the library's own two
  windows as the primary parameterisation and nothing tuned.

- **Where I had to choose.** Eleven places. C1–C6 decide whether this is still
  R2's object and are what I need ruled on; C7–C11 are corners I resolved and am
  recording.

  - **C1 — the window widths are the library's own, unchanged.**
    `avoid_event(10, 15)` and `after_event(15, 60]` are exactly
    `outside_news_blackout` and `post_news_window`:
    `AccountConfig.news_blackout_before_min = 10`, `_after_min = 15`
    `[repo-verified: futures_agents/config.py:410-411]` and the literal `60.0`
    at `library.py:1358`. Lower bound **strictly** greater, upper bound
    inclusive, copied from `library.py:1356-1359` whose comment explains why
    (the blackout's own bound is inclusive, so sharing the endpoint put exactly
    one bar per event inside both windows). **Two tests assert bar-for-bar
    agreement with the library conditions on real MGC and MCL series**, so the
    primary arm differs from F11 in the *contract* and in nothing else. Widths
    are parameters; changing one is a declared variant and costs deflation.
  - **C2 — both directions of the family are implemented, and only two are
    primary.** `avoid_event` (stand aside) and `after_event` (participate only
    in the aftermath) are the primary arms, because those are the two F11
    measured. `into_event` — permit an entry *only* when a print is imminent, the
    pre-positioning arm, and the one direction the library has no condition for
    at all — is implemented and **not** in the primary set. Primary search size
    is therefore **2 gates × 2 contracts**, with MNQ run as a reference arm only.
  - **C3 — HIGH impact only, in the primary arm.** `features.py:972-973` filters
    to `Impact.HIGH.rank` *before* computing proximity, so every MEDIUM rule is
    invisible to the library regardless of what the calendar holds. My clock
    takes `min_impact` as a parameter, so MEDIUM is one keyword away. **I chose
    to keep it out of the primary arm** for one reason: including it changes what
    is being compared against F11 from "the same filter on a different contract"
    to "a different filter on a different contract", and the whole force of R2's
    finding is that only the contract changed. The MEDIUM *census* is reported
    (it is a count, not a result) and it is large — MGC goes from 32 to **105**
    in-session event days, MCL from 49 to **58**. The uplift is **not uniform**:
    gold's is almost all one rule (weekly Initial Jobless Claims, 08:30, **46**
    prints inside 08:20–13:30, plus PPI 11, Retail Sales 11, GDP 10, ISM 10),
    while crude gains only ISM (11) because its session opens at 09:00, after
    every 08:30 print. So MEDIUM roughly triples gold's event dimension and
    barely touches crude's — which makes it the single largest available sample
    gain and also a *different* experiment, so I recommend it as ALGO-2 rather
    than as a variant of ALGO-1.
  - **C4 — overlapping prints: the nearest print wins, matching the library.**
    Two HIGH prints 30 minutes apart happen on every FOMC day (statement 14:00,
    press conference 14:30), and on the nearest-print reading the presser resets
    the statement's clock, so the statement's drift window is truncated at 30
    minutes. `EventClock` reports **both** readings — `since_prev` (nearest) and
    `since_episode` (first print of a run clustered within `cluster_minutes`) —
    and the primary arm uses `since_prev` because that is what `features.py`
    computes. The `cluster_minutes=60` variant is declared and not primary.
    `avoid_event` and `into_event` deliberately **do not accept**
    `cluster_minutes`: clustering shortens `since`, which would let an avoidance
    gate open five minutes after the press conference because the statement
    printed thirty minutes earlier, and a parameter that is accepted and ignored
    manufactures two names for one behaviour.
  - **C5 — a print landing outside the contract's own session is KEPT.** The
    calendar describes the world; the session describes permission, and
    permission is `StrategyFilters.rth_only`'s job, not the clock's. So an 08:30
    CPI print is still on MCL's clock even though crude's RTH opens at 09:00,
    and the 09:00 bar — 30 minutes after that print — is admitted. **This is not
    a free choice: it is 28 of MCL's 73 admissible bars on `csv/raw` and 65 of
    164 on the archive, i.e. ~40% of crude's entire sample for this gate comes
    from prints that landed before crude's session opened.** The alternative
    (drop out-of-session prints) is defensible and would cut MCL's sample by
    ~40%. **R2 has to rule on this one.** MGC is unaffected (0 of 31) and MNQ
    nearly so (1 of 8).
  - **C6 — the clock is read at the bar's OPEN, matching `features.py`, and the
    consequence is that the primary arm's fills are 60–120 minutes after the
    print, not 15–60.** `Bar.ts` is the bar's open
    `[repo-verified: futures_agents/data/bars.py:37]`; `features.py:1035` reads
    the calendar there. But the signal decision is made at the bar's *close*
    (`snapshot(i)` carries `price=bar.close`) and the entry fills at the *next*
    bar's open `[repo-verified: futures_agents/backtest/engine.py:8, 296-300]`.
    On a 60-minute frame, an 08:30 print admits the 09:00 bar (`since = 30`),
    whose close is 10:00 and whose fill is 10:00 — **90 minutes after the
    print**. So the library's `post_news_window`, on any hourly frame, is not
    measuring the 15–60 minute drift window; it is measuring entries 60–120
    minutes after the print. `offset_min` exposes this (`offset_min=60` on a 60m
    frame reads the clock at the decision instant) and the primary arm leaves it
    at 0 to match the library. **This is the choice I am least sure of and the
    first one I want R2's ruling on**, because if the finding is about the drift
    window then the faithful implementation is the offset one and the library's
    own condition is misaligned.
  - **C7 — a gate is a permission, not an entry, and nothing is flattened.** The
    gate restricts where a *host strategy's own* signal may be acted on. It does
    not mark an event range and trade its break, which is what R2-D2c's operator
    does; that needs a SIGNAL condition **and** a two-step sequence, so it is
    blocked twice over (II-11's "all three conditions are FILTERs", plus D37).
    Separately, R2-D2c's operator is **flat** at 10:30; ALGO-1 only prevents
    *initiating* inside a window, and a position already open is carried straight
    through the print. `ExitReason` has no news member
    `[repo-verified: futures_agents/backtest/engine.py:49-57]`, so a
    flatten-before-the-print exit is a primitive the engine does not have. Filed
    as BT2-REQ-2.
  - **C8 — `rth_only=True` in the primary arm, deliberately against the
    toolkit's default.** `toolkit.make_strategy` defaults `rth_only=False`
    (`workspace/studies/toolkit.py:268-271`), and D24's correction measured what
    that buys and costs: trades ×2.1–4.2 and **paired median expectancy falls**,
    three cells, `p ≤ 0.001` `[repo-verified: workspace/studies/DEFECTS.md:610-618]`.
    For an event test `rth_only` is not a nuisance parameter — it decides which
    prints the strategy can see — and R2's 7/32/49 are **in-session** counts. So
    the primary arm is `rth_only=True`, which is also the library default
    (`base.py:393`) and F11's configuration. `rth_only=False` is a declared
    secondary and will be reported as such.
  - **C9 — 60-minute bars, and the finer frames are not available.** The event
    windows are 10–60 minutes wide, so the frame has to be fine enough to
    resolve them and long enough to contain events. `csv/raw` gives
    `MGC_15m`/`MCL_15m` **2 months** and `MGC_5m`/`MCL_5m` **1 month**
    `[measured: head/tail of each csv → MGC_15m 2026-07-26..2026-09-22,
    MGC_5m 2026-08-26..2026-09-22]`, which is 6–8 event days. Daily is worse
    than useless: a daily bar is stamped at midnight ET so `since` is never in
    (15, 60] and **`post_news_window` is identically false on every daily series
    in this repository**, MGC_1d's ten years and R2-D5's 358 in-session event
    days included (asserted by
    `test_the_after_gate_can_never_fire_on_a_daily_bar`). So 60m is the only
    frame where this family is measurable at all here, and BRIEF rule 7
    ("sub-hourly is a graveyard") does not need to be invoked to rule out 5m —
    the data does it.
  - **C10 — both stores, always reported separately.** `csv/raw` is the
    comparability baseline against F11 (it is the frozen snapshot every
    `scan_reports/` result was measured on); `data/archive` roughly doubles the
    span and is permitted by BRIEF.md's data-policy ruling of 2026-09-27. I
    re-verified the ruling's condition 2 for my own symbols and timeframe
    (`test_the_two_stores_are_the_same_series_on_the_overlap`) and found one
    correction to its table: the closes are **not** bit-identical,
    `[measured: max |close difference| over the 60m overlap → MGC 3.44e-07,
    MCL 4.82e-08, MNQ 0.0, MES 0.0]` — float32 round-trip noise at 3–5
    millionths of a tick, immaterial, but an exact-equality assertion would fail
    on it. Volume differs on 2 of ~4,987 bars for **all four** contracts, not
    only MGC.
  - **C11 — my own clock, not the snapshot's three fields.** `features.py`'s
    news fields are HIGH-only and fixed-width, and BT2 may not edit
    `futures_agents/`. The clock is re-derived from the same public primitive
    (`econ_calendar.project_events`) and **tested for bar-for-bar agreement with
    the snapshot fields** on MGC, MCL and MNQ, with exactly one documented
    divergence (below). It is a strict generalisation, not a second opinion.

- **What I verified myself, which is not a substitute for R2's ruling.**
  `[measured: python -m pytest -q workspace/roundtable/backtest/BT2/code/test_algo1.py
  → 26 passed]`

  - **The census reproduces R2-D5 exactly**, on all four of its numbers, using
    each contract's own `ContractSpec` session rather than a global 09:30–16:00:

    | symbol | its own RTH | HIGH events in span | in-RTH | **in-RTH event days** | which rules (mine) | R2-D5 |
    |---|---|---|---|---|---|---|
    | MNQ | 09:30–16:00 | 46 | 14 | **7** | FOMC statement 7, presser 7 | 7 ✓ |
    | MGC | 08:20–13:30 | 46 | 32 | **32** | NFP 11, CPI 11, PCE 10 | 32 ✓ |
    | MCL | 09:00–14:30 | 98 | 57 | **49** | EIA 49, FOMC statement 8 | 49 ✓ |

    `[measured: python3 workspace/roundtable/backtest/BT2/code/algo1.py --store csv]`
    R2-D5's per-rule split ("NFP 11, CPI 11, PCE 10"; "EIA 49, FOMC 8") is
    reproduced item for item. **The three contracts see disjoint in-session event
    sets** — MNQ sees only FOMC, MGC only the 08:30 prints, and they do not
    intersect at all (asserted). A result on one says nothing about the other,
    which is a stronger statement than "MNQ had fewer events".
  - **No look-ahead**: appending bars never changes a historical reading; a
    reading does not depend on the series it sits in; per-year caching neither
    loses nor duplicates an event shifted across a year boundary.
  - **The two silent-wrong-answer channels are closed and tested.** Every
    parameterisation gets a distinct condition `name`, because
    `Condition.evaluate` memoises on `(name, tf)` (`base.py:120`) and `run_many`
    allocates one such cache per bar (`engine.py:284`) — R2's own
    `R2_expressibility_wall.md` §1.5 mechanism, and D38's shape. `gate_arm`
    passes `_id=None`, because `Strategy._id` is a cached field and
    `run_portfolio` keys results on `strategy_id` (`engine.py:277`), so without
    it the gated arm would silently report the bare arm's trades.
  - **`EventClockError` subclasses `RuntimeError`, which `Condition.evaluate`
    does not swallow** (`base.py:131-133` catches TypeError, ValueError,
    ZeroDivisionError, KeyError, IndexError). Asserted directly. A misconfigured
    clock aborts the sweep; it does not report zero trades. That is D38's lesson
    applied rather than cited.
  - **D38 cannot reach ALGO-1 at all**, and not because it was worked around:
    the gates read `snap.ts` and `snap.symbol` only, so they need no frame
    registration, and `algo1.py` builds its own frame in the open and hands it to
    `run_portfolio` instead of going through `toolkit.measure_custom`.
  - **One divergence from `features.py`, documented not excused.**
    `_build_news_proximity` projects `bars[0].ts − 2 days .. bars[-1].ts + 45
    days` (`features.py:955-959`) — the forward side carries a comment
    explaining why 45 days, the backward side is 2 days with none. So
    `minutes_since_high_impact` reads `inf` — "no high-impact release has ever
    happened" — on the bars before the first print inside that window.
    `[measured: 56 of 5,000 MGC_1h bars, 53 MCL, 52 MNQ, 54 MES; largest hidden
    gap 10,050 minutes = 6.98 days]`. It is **behaviourally inert for the
    library** and that is asserted, not assumed: the artefact only fires when the
    true gap exceeds 2,880 minutes and every window any library condition uses is
    at most 60, so a hidden value was already outside every window. It stops
    being inert for any condition wider than two days. Filed as BT2-REQ-1.

- **The pre-flight ceiling — the reason this entry stops here.** The engine takes
  at most one signal per bar and never while positioned
  `[repo-verified: futures_agents/backtest/engine.py:305-307]`, so realised
  trades can never exceed the number of bars the gate admits. That is arithmetic
  on the bar clock and the calendar: no price, no trade, no expectancy.

  | store | span | symbol | eligible RTH bars | `after@lib(15,60]` admits | `avoid@lib(10,15)` **removes** |
  |---|---|---|---|---|---|
  | `csv/raw` | ~11 months | MNQ | 1,310 | **8** | 7 |
  | `csv/raw` | ~11 months | MGC | 1,093 | **31** | **0** |
  | `csv/raw` | ~11 months | MCL | 1,320 | **73** | 9 |
  | `archive` | ~2 years | MNQ | 2,955 | **19** | 16 |
  | `archive` | ~2 years | MGC | 2,477 | **69** | **0** |
  | `archive` | ~2 years | MCL | 2,881 | **164** | 17 |

  `[measured: python3 workspace/roundtable/backtest/BT2/code/algo1.py --store csv
  and --store archive]`

  Three things fall out, and they are the substance of what this burst learned.

  1. **F11's 1.5 trades was bounded above by 8.** On `csv/raw` MNQ at 60m the
     post-news gate can admit 8 bars in eleven months, against
     `toolkit.FLOOR = 20` and `scout.MIN_TRADES = 30`. Doubling the span to two
     years takes it to **19 — still below the floor.** So on MNQ at 60m this
     family is not underpowered, it is *impossible*: no signal layer, however
     good, can reach the reporting floor through that gate. R2's claim that "the
     1.5 was determined by the calendar" is confirmed and strengthened.
  2. **MGC and MCL clear the floor only on the archive span.** MGC 31 and MCL 73
     on `csv/raw`; 69 and 164 on the archive. So the store choice is not a
     convenience here, it is the difference between a measurable question and an
     unmeasurable one — which is exactly what BT1-REQ-1 was about.
  3. **The avoidance arm is a near-perfect no-op at 60 minutes, and on MGC it is
     an exact one.** Every HIGH rule prints at :00 or :30, and **4,992 of 5,000
     hourly bars open at :00**, so a [−10, +15] window around an **08:30** print
     (08:20–08:45) contains no hourly bar open at all. MGC's HIGH calendar is
     entirely 08:30 prints, so `outside_news_blackout` declines on **0 of 1,093**
     eligible MGC bars — it is the identity filter on gold. MNQ loses exactly 7
     bars (its 7 FOMC statements, which print at 14:00, on the grid) and MCL 9
     (its 8 FOMC statements plus **one** EIA print, 2025-12-24 10:30 — a
     shortened session where the vendor's hourly grid shifts to :30, so the print
     lands on the bar's own open). `[measured: 8 of 5,000 csv/raw hourly bars
     open at :30, 20 of ~11,000 in the archive, identically on all three
     symbols]` This explains F11's other line —
     `outside_news_blackout` retained 99.99% of trades — as a property of the bar
     grid rather than of the filter, and it means **the avoidance arm cannot be
     tested at 60m either.** Whether that makes it a null result or a
     non-measurement is R2's call, and it is question Q4.

- **Search size so far: 0 measured, 2 pre-registered.** No backtest has been run.
  The primary arm is 2 gates at the library's own settings on 2 contracts; the
  four declared secondaries (`cluster_minutes=60`, `offset_min=bar`,
  `min_impact=MEDIUM`, `into_event`) exist in code and are unmeasured. Every
  number above is a count of prints or of bars; if any variant is ever run as a
  strategy, the search size stated then will include it.

- **Placebo plan, pre-registered.** `placebo_random` count-matched on the base
  strategy's own eligible bars and `placebo_shuffle` on its own timestamps, both
  through ALGO-1's own exits, filters and sizing, via
  `workspace/newstrats/placebo.py`. **Not `placebo_shift`** — it retains part of
  the real signal and is a conservative control only
  `[repo-verified: workspace/studies/DEFECTS.md D42:620-638]`. No comparative
  claim will be routed through `T.ab` (D28: inflates z ~3.3×); the arms are the
  *same* base strategies with one condition appended, so the test is a paired
  one over base strategies, named when reported. Note the interaction worth
  stating now: a placebo keeps the base's FILTER conditions, so a placebo built
  on a gated arm draws from the gated arm's own admissible bars — which is the
  correct control and also means its ceiling is the same 8/31/73/19/69/164.

- **Fidelity: ASKED** — `msgs/05_BT2_R2_verify-ALGO-1.md`, six questions
  (Q1 the read instant, Q2 out-of-session prints, Q3 the impact rank, Q4 the
  60-minute no-op, Q5 overlapping prints, Q6 whether the ceiling changes the
  finding). **Nothing measured until R2 answers.**
