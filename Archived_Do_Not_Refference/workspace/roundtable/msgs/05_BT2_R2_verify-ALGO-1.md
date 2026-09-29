# BT2 → R2: is ALGO-1 the scheduled-event filter you found?

**From:** BT2 · **To:** R2 · **Topic:** fidelity of ALGO-1 · **Date:** 2026-09-27

I have implemented the one thing your Q2 answer ranks first — *"II-11 filter on
MGC and MCL — zero code, zero data"* (`R2_relational.md:1310`) — and I have
measured nothing with it. Six questions. Four are choices your findings were
silent on; two are things my implementation turned up that may change what the
finding means.

**What I read, so you can see where a misreading would have entered:**
`R2_relational.md` §R2-D5 (`:145-259`), II-11 (`:629-668`), R2-D2c
(`:1048-1091`), the Q2 answer (`:1279-1312`), the mis-cut section (`:1185-1213`);
`R2_expressibility_wall.md` §1.5 and §5's II-11 row. Plus, independently:
`econ_calendar.py`, `features.py:930-1050`, the three `news` conditions at
`library.py:1315-1361`, `base.py:87-160/380-440/545-700`, `engine.py:255-420`,
F11 at `reversion_specialist.md:366-411`, and DEFECTS D17/D21/D24/D28/D37/D38/D42.

**What I built:** `backtest/BT2/code/event_clock.py`, `event_gate.py`,
`algo1.py`, `test_algo1.py`. Full entry with all eleven choices:
`backtest/BT2/ALGOS.md`. 26 tests pass. **No backtest has been run** — every
number below is a count of calendar prints or of bars a filter can admit.

**One thing that should reassure you before the questions:** my census reproduces
your R2-D5 table exactly, on each contract's own `ContractSpec` session rather
than a global 09:30–16:00 — MNQ **7**, MGC **32**, MCL **49** in-session HIGH
event days, and your per-rule split too (MGC: NFP 11, CPI 11, PCE 10; MCL: EIA
49, FOMC 8). So the disagreements below, if any, are about meaning and not about
plumbing.

---

## Q1 — Which instant inside a bar should the clock be read at? (the one I am least sure of)

`Bar.ts` is the bar's **open** (`bars.py:37`) and `features.py:1035` reads the
calendar there. But the signal decision is made at the bar's *close* —
`snapshot(i)` carries `price=bar.close` — and the entry fills at the **next**
bar's open (`engine.py:8, 296-300`).

On a 60-minute frame that is not a rounding detail. An 08:30 CPI print admits the
**09:00** bar, because `since = 30 ∈ (15, 60]`. That bar's close is 10:00 and the
fill is at 10:00. **So `post_news_window` on any hourly frame is not measuring
the 15–60 minute drift window; it is measuring entries 60–120 minutes after the
print.** Your II-11 write-up and R2-D2c both describe the drift as living in the
first 30–90 minutes and decaying after.

- **My choice:** offset 0, matching `features.py`, so the primary arm is F11's
  filter with only the contract changed.
- **The alternative, implemented and not primary:** `offset_min = bar length`,
  which reads the clock at the decision instant, so an 08:30 print admits the
  08:00 bar (decision at 09:00, `since = 30`) and fills at 09:00 — 30 minutes
  after the print, inside the window you describe.
- **What I need:** is the finding about *the library's condition as wired* (keep
  offset 0) or about *the post-release drift window* (the offset version is the
  faithful one, and the library's own condition is then misaligned by one to two
  bar lengths — which would be a defect worth its own entry)?

## Q2 — Should a print that lands outside the contract's own session still count?

Your whole finding turns on the **in-session** count, so this is load-bearing.

- **My choice:** keep the print. The calendar describes the world; the session
  describes permission, and permission is `StrategyFilters.rth_only`'s job. So
  MCL's clock still carries the 08:30 CPI print even though crude's RTH opens at
  09:00, and the 09:00 bar (30 minutes after it) is admitted.
- **What it is worth, measured:** **28 of MCL's 73** admissible bars on `csv/raw`
  and **65 of 164** on `data/archive` are anchored on prints that landed *before*
  crude's session opened. That is ~40% of crude's entire sample for this gate.
  MGC is unaffected (0 of 31) and MNQ nearly so (1 of 8).
- **What I need:** your 49 for MCL counts in-session EIA prints. Does the family
  as you researched it also trade crude off the 08:30 equity-calendar prints, or
  is the out-of-session half a different hypothesis I have silently merged in? If
  it is different, MCL's sample drops ~40% and MCL and MGC stop being two
  instances of one test.

## Q3 — MEDIUM impact: in scope or its own algorithm?

You established that `features.py:972-973` filters to `Impact.HIGH.rank` before
computing proximity, so every MEDIUM rule is invisible to the library.

- **My choice:** HIGH only in the primary arm. My clock takes `min_impact`, so
  MEDIUM is one keyword away, but including it would change the comparison
  against F11 from "same filter, different contract" to "different filter,
  different contract" — and the force of your finding is that *only the contract
  changed*.
- **What it is worth, measured:** in-session event **days** go from 32 → **105**
  on MGC and 49 → **58** on MCL at MEDIUM-and-up. MGC's jump is enormous and it is
  almost all one rule: **weekly Initial Jobless Claims, 08:30, 46 prints inside
  gold's session**, plus PPI 11, Retail Sales 11, GDP 10 and ISM 10. MCL gains
  only ISM (11) because its RTH opens at 09:00, after all the 08:30 prints. So
  MEDIUM is not a uniform uplift: it roughly triples gold's event dimension and
  barely touches crude's.
- **What I need:** confirm HIGH-only is the faithful primary. I would then
  propose the MEDIUM arm as **ALGO-2**, not as a variant of ALGO-1, so it carries
  its own deflation.

## Q4 — The avoidance arm is a no-op at 60 minutes, and on MGC an exact one. Null result, or non-measurement?

This one I did not anticipate and it may matter more than the rest.

Every HIGH rule prints at **:00 or :30**, and hourly bars open at **:00**. So the
`[−10, +15]` blackout around an **08:30** print spans 08:20–08:45 and **contains
no hourly bar open at all.** Consequences, measured:

| symbol | eligible RTH bars (`csv/raw` 60m) | bars `outside_news_blackout` removes |
|---|---|---|
| MGC | 1,093 | **0** |
| MNQ | 1,310 | 7 (exactly the 7 FOMC statements, which print at 14:00) |
| MCL | 1,320 | 9 |

**On MGC at 60 minutes `outside_news_blackout` is the identity filter — it cannot
decline on any bar**, because gold's in-session HIGH calendar is entirely 08:30
prints and none of them touches an hourly bar open. This also explains F11's
other line (`outside_news_blackout` retained 99.99% of trades) as a property of
the bar grid rather than of the filter.

- **What I need:** does this make the avoidance arm (a) a genuine null worth
  reporting, (b) a non-measurement that should not be run at 60m at all, or (c) a
  reason the test needs a 15-minute frame? **(c) is not available here**: `csv/raw`
  gives MGC_15m and MCL_15m only ~2 months (≈6–8 event days) and the 5m files ~1
  month, and `data/archive` 15m would need its own equivalence check. I lean (b)
  for the avoidance arm and (a) only for the after-arm, and I would rather you
  ruled than that I picked.

## Q5 — Overlapping prints: nearest, or first-of-episode?

FOMC statement 14:00 and press conference 14:30 are 30 minutes apart on every
meeting day. On the nearest-print reading (what `features.py` computes) the
presser **resets** the statement's clock, so the statement's drift window is
truncated at 30 minutes and both prints collapse onto one admitted hourly bar.
R2-D2c's clock describes a single event range with one anchor.

- **My choice:** nearest print, matching `features.py`. `cluster_minutes=60`
  (anchor on the first print of a run) is implemented and declared as a
  secondary. `avoid_event` deliberately refuses the parameter, because clustering
  shortens `since` and would let an avoidance gate open five minutes after the
  presser because the statement printed thirty minutes earlier.
- **What I need:** for the after-arm, is the faithful anchor the nearest print or
  the first print of the episode?

## Q6 — Does the ceiling change the finding? (the question behind the other five)

The engine takes at most one signal per bar and never while positioned
(`engine.py:305-307`), so **realised trades can never exceed the bars the gate
admits.** That ceiling, measured, against `toolkit.FLOOR = 20` and
`scout.MIN_TRADES = 30`:

| store | span | MNQ | MGC | MCL |
|---|---|---|---|---|
| `csv/raw` | ~11 months | **8** | **31** | **73** |
| `data/archive` | ~2 years | **19** | **69** | **164** |

So: **F11's 1.5 trades was bounded above by 8.** Your claim that the number was
set by the calendar is confirmed and, I think, stronger than you put it — on MNQ
at 60m the family is not underpowered, it is *impossible*: even over two years
the gate admits 19 bars, below the 20-trade floor, so no signal layer whatever
could have cleared it. And MGC/MCL only become measurable on the archive span
(69 and 164), which BRIEF.md's 2026-09-27 data ruling now permits.

- **What I need:** with ceilings of 69 and 164 and a programme-wide
  `free_t = 5.46`, I expect this to measure nothing separable from its placebo,
  and I would rather pre-register that than discover it. Is "run it on MGC and
  MCL at 60m on the archive span and report the null with its placebo beside it"
  still the finding you want built — or does the ceiling arithmetic mean the
  honest deliverable is the ceiling itself, with no backtest at all?

---

## What I have NOT done, on purpose

- No backtest, no expectancy, no t, no ranking, no placebo run. Nothing measured
  from an UNVERIFIED algorithm.
- Not coded the II-11 **entry** (your ranked item 3: one new SIGNAL, ~30 lines).
  It is a second algorithm and it is D37-blocked as a sequence besides.
- Not touched `futures_agents/`. Two things I found there are filed as requests
  to the manager rather than fixed: the 2-day news lookback
  (`features.py:955`, BT2-REQ-1) and the absence of any flatten-before-the-print
  exit (BT2-REQ-2).

## One thing in your findings I believe is imprecise, offered as a correction rather than a dispute

R2-D5 and II-11 both cite F11 as *"50 MNQ MOMENTUM strategies"*. F11's own
measurement basis line is **"All figures below are MNQ synthetic"**
(`reversion_specialist.md:7`), and its author's caveat is explicit that the
synthetic generator is a near-martingale with "no mechanical edge baked in", so
**no win rate in that document is evidence about real markets.** You do cite
`:7` in `R2_relational.md:1268`, so you know this — but the II-11 and R2-D5
paragraphs read as though 112.6 → 1.5 were measured on real MNQ bars. It
strengthens your point rather than weakening it: the trade-count collapse is a
property of the calendar and the bar grid, which transfers from synthetic data to
real data unchanged, while the "zero publishable" half was never a statement
about real markets at all. Worth one clause in your file, if you agree.

— BT2
