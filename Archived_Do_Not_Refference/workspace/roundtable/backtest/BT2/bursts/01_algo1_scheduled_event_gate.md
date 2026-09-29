# BT2 burst 01 — ALGO-1: the scheduled-event gate, on each contract's own session

**Question for this burst:** make R2's cheapest untried item executable — the
II-11 event filter on MGC and MCL rather than MNQ — and find out whether the code
means what the research said.
**Stopping point, declared up front:** the moment the algorithm exists and the
fidelity question is posted. No measurement, no second algorithm.

---

## What I did

Read, in full: `PIPELINE.md`, `OWNERSHIP.md`, `BRIEF.md` (including the
data-policy ruling appended 2026-09-27), `R2_expressibility_wall.md`,
`msgs/01`–`msgs/04`. From `R2_relational.md` (1,404 lines) I read the header and
R2-D0/D4 (`:1-144`), R2-D5 in full (`:145-259`), II-11 and II-12
(`:629-693`), R2-D2c (`:1048-1091`), the mis-cut section (`:1185-1213`), the
anti-overfitting audit, and the Q2/Q3 answers (`:1279-1349`).

Then read the machinery rather than trusting prose about it: `econ_calendar.py`
end to end, `features.py:680-1060`, the three `news` conditions
(`library.py:1315-1361`), `base.py:80-170` (the condition cache),
`base.py:380-440` (`StrategyFilters`), `base.py:545-700` (`Strategy`),
`engine.py:1-60` and `:255-420` (the bar loop and the fill rule), `config.py`'s
MGC/MCL specs, `timeutil.is_rth`, `workspace/studies/toolkit.py`,
`workspace/newstrats/placebo.py`, DEFECTS D17/D21/D24/D28/D37/D38/D42/D43, and
F11 in `research/confluence/reversion_specialist.md`.

Wrote four files under `backtest/BT2/code/`:

| file | what it is |
|---|---|
| `event_clock.py` | a parameterised, look-ahead-free clock over `econ_calendar.project_events`: `min_impact`, `cluster_minutes`, `offset_min`, plus the contract-session census |
| `event_gate.py` | three `Condition` factories — `avoid_event`, `after_event`, `into_event` — each parameterisation getting its own name |
| `algo1.py` | store-aware loading (`csv/raw` and `data/archive`), frame construction on the contract's own spec, arm construction, and the pre-flight ceiling |
| `test_algo1.py` | 26 tests `[measured: python -m pytest -q workspace/roundtable/backtest/BT2/code/test_algo1.py → 26 passed in 46.65s]` |

## What I chose

Eleven choices, all written up in `ALGOS.md` as C1–C11. The four that decide
whether this is still R2's object:

- **C1 — the library's own windows, unchanged.** `avoid_event(10, 15)` and
  `after_event(15, 60]` *are* `outside_news_blackout` and `post_news_window`, and
  two tests assert bar-for-bar agreement with them on real series. So the primary
  arm differs from F11 in the contract and in nothing else.
- **C5 — a print outside the contract's own session still counts.** The calendar
  describes the world; `rth_only` describes permission. Worth **28 of MCL's 73**
  admissible bars on `csv/raw` and **65 of 164** on the archive — ~40% of crude's
  sample comes from 08:30 prints that land before crude's 09:00 open.
- **C6 — the clock is read at the bar's OPEN, matching `features.py`**, and the
  consequence is that the primary arm's fills land 60–120 minutes after the print
  rather than 15–60. `offset_min` exposes the alternative; the primary arm leaves
  it at 0.
- **C8 — `rth_only=True`**, against `toolkit.make_strategy`'s default, because
  D24's correction measured that `rth_only=False` buys trades and costs paired
  median expectancy, and because R2's 7/32/49 are in-session counts.

Plus: HIGH-only in the primary arm (C3, with the MEDIUM census reported because a
count is not a result); nearest-print rather than first-of-episode for overlaps
(C4); 60-minute bars because the finer `csv/raw` files are 1–2 months long (C9);
both stores reported separately, never pooled (C10); my own clock rather than the
snapshot's three fields, because they are HIGH-only and fixed-width and BT2 may
not edit `futures_agents/` (C11).

**Two defects in my own first draft, caught before the tests ran and recorded
because a silent version of either would have been the bug this pipeline exists
to avoid.** First, `cluster_minutes` was offered on `avoid_event`, where it
*shortens* the blackout: an avoidance gate would have opened five minutes after
the FOMC press conference because the statement printed thirty minutes earlier.
Second, the read instant was inferred from the condition's timeframe rather than
taken as a parameter, which is wrong whenever a frame's base is finer than the
timeframe the gate is bound to. Both are now structural: the parameter is only
offered where it is meaningful, and the offset is explicit.

## What I found, and none of it is a performance number

Everything below is a count of calendar prints or of bars a filter can admit.
No backtest was run, no position opened, no expectancy computed.

**1. R2-D5 reproduces exactly, on each contract's own session.**

| symbol | its own RTH | HIGH in span | in-RTH | in-RTH event days | R2-D5 says |
|---|---|---|---|---|---|
| MNQ | 09:30–16:00 | 46 | 14 | **7** | 7 ✓ |
| MGC | 08:20–13:30 | 46 | 32 | **32** | 32 ✓ |
| MCL | 09:00–14:30 | 98 | 57 | **49** | 49 ✓ |

R2's per-rule split reproduces item for item too (MGC: NFP 11, CPI 11, PCE 10;
MCL: EIA 49, FOMC 8). R2's self-correction — using each `ContractSpec`'s session
rather than a global 09:30–16:00 — is independently confirmed, and I did not
repeat the mistake it corrected. **The three contracts' in-session event sets are
disjoint**, which is a stronger statement than "MNQ had fewer events": MNQ sees
only FOMC, MGC only the 08:30 prints, and nothing is shared.

**2. The ceiling, which is the substance of the burst.** The engine takes at most
one signal per bar and never while positioned (`engine.py:305-307`), so realised
trades can never exceed the bars the gate admits:

| store | span | symbol | eligible RTH bars | `after@lib(15,60]` admits | `avoid@lib` removes |
|---|---|---|---|---|---|
| `csv/raw` | ~11 months | MNQ | 1,310 | **8** | 7 |
| `csv/raw` | ~11 months | MGC | 1,093 | **31** | **0** |
| `csv/raw` | ~11 months | MCL | 1,320 | **73** | 9 |
| `archive` | ~2 years | MNQ | 2,955 | **19** | 16 |
| `archive` | ~2 years | MGC | 2,477 | **69** | **0** |
| `archive` | ~2 years | MCL | 2,881 | **164** | 17 |

- **F11's 1.5 trades was bounded above by 8.** Against `toolkit.FLOOR = 20` and
  `scout.MIN_TRADES = 30`, MNQ at 60m cannot reach the floor through this gate
  even over two years (19). So the family was not merely underpowered on MNQ, it
  was *impossible* there — no signal layer could have cleared it. R2's claim that
  the calendar set the number is confirmed and strengthened.
- **MGC and MCL clear the floor only on the archive span** (69 and 164 against 31
  and 73), so BRIEF.md's data ruling is what makes this question measurable.
- **The avoidance arm is a no-op at 60 minutes and on MGC an exact one.** Every
  HIGH rule prints at :00 or :30, and 4,992 of 5,000 hourly bars open at :00, so a
  [−10, +15] window around an 08:30 print (08:20–08:45) contains no bar open.
  MGC's HIGH calendar is entirely 08:30 prints, so `outside_news_blackout`
  declines on **0 of 1,093** bars — the identity filter on gold. MNQ loses exactly
  its 7 FOMC statements (14:00, on the grid); MCL loses 9 — its 8 FOMC statements
  plus one EIA print on 2025-12-24, a shortened session where the vendor's hourly
  grid shifts to :30 so the print lands on a bar's own open
  `[measured: 8 of 5,000 hourly bars open at :30, 20 of ~11,000 in the archive]`.
  This explains F11's "retained 99.99% of trades" as a property of the bar grid,
  not of the filter.

**3. Two structural zeros, now asserted rather than discoverable as "the idea does
not work".** `post_news_window` is **identically false on every daily series in
this repository** — a daily bar is stamped at midnight ET, so `since` is never in
(15, 60], and MGC_1d's ten years with R2-D5's 358 in-session event days are
entirely unreachable by it. And an hourly grid admits at most one bar per print.

**4. A defect in `features.py`, and the reason it is currently harmless.**
`_build_news_proximity` looks back **2 days** against 45 days forward
(`features.py:952-959`); the forward side carries a comment explaining why, the
backward side has none. So `minutes_since_high_impact` reads `inf` — "no
high-impact release has ever happened" — on the bars before the series' first
print: `[measured: 56 of 5,000 MGC_1h bars, 53 MCL, 52 MNQ, 54 MES; largest
hidden gap 10,050 minutes = 6.98 days]`. It is inert for every library condition
and my suite **asserts** that rather than assuming it, because every library
window is ≤ 60 minutes and the artefact only fires beyond 2,880. It stops being
inert for any wider window. Filed as BT2-REQ-1.

**5. A small correction to BRIEF.md's data ruling.** Its table says
`max |close difference|` is 0.0000 on all four contracts at 60m. Exactly:
`[measured: MGC 3.44e-07, MCL 4.82e-08, MNQ 0.0, MES 0.0]` — float32 round-trip
noise, 3–5 millionths of a tick, immaterial to any fill, but an exact-equality
assertion fails on it. Volume differs on 2 of ~4,987 bars for **all four**
contracts, not only MGC. My test asserts agreement to a thousandth of a tick.

## What I asked

`msgs/05_BT2_R2_verify-ALGO-1.md` — six questions to R2, four of them choices its
findings were silent on and two of them things the implementation turned up:

Q1 which instant the clock is read at (and therefore whether the arm tests the
drift window at all at 60m); Q2 whether out-of-session prints count, worth ~40% of
MCL's sample; Q3 whether MEDIUM impact is in scope or is ALGO-2; Q4 whether the
MGC avoidance no-op is a null or a non-measurement; Q5 nearest print versus
first-of-episode; Q6 whether the ceiling arithmetic changes what the finding asks
for.

Also posted one correction rather than a dispute: R2-D5 and II-11 read as though
F11's 112.6 → 1.5 were measured on real MNQ bars, when F11's own basis line is
"MNQ **synthetic**" (`reversion_specialist.md:7`). It strengthens R2's point — the
trade-count collapse is a calendar-and-grid property that transfers to real data,
while "zero publishable" was never a claim about real markets — but the two
paragraphs should carry the clause.

Three items went to the manager as `REQUESTS.md`: BT2-REQ-1 (the 2-day lookback),
BT2-REQ-2 (no flatten-before-the-print exit exists, so "avoid the event" as this
repo expresses it is strictly weaker than the operated family), BT2-REQ-3 (whether
a 60m measurement with a 69/164 ceiling is worth running, or whether
`data/archive` 15m should be equivalence-checked first).

## Where I stopped, and why

At **ASKED**. ALGO-1 runs, passes 26 tests, and has produced no expectancy, no t,
no ranking and no placebo run. PIPELINE §4 is explicit that an unverified result
is not a weak result but an unknown quantity, and four of my six questions would
each change what a number meant — Q1 moves the tested window by a whole bar
length, Q2 moves MCL's sample by 40%, Q3 triples MGC's event count, Q4 decides
whether one of the two arms should be run at all.

I did not code a second algorithm. The obvious next one — II-11 as an *entry*,
R2's ranked item 3, one new SIGNAL condition of ~30 lines — is both a separate
algorithm and D37-blocked as a two-step sequence, and coding it now would have
propagated any wrong assumption in ALGO-1 straight into it.

**What burst 2 does, depending on R2's answer:** if FAITHFUL, run the two primary
arms on MGC and MCL at 60m on the archive span with `placebo_random` and
`placebo_shuffle` beside them, paired over base strategies, search size 2, and
report the null. If DIVERGENT on Q1 or Q4, fix the offset or drop the avoidance
arm first. If R2's answer to Q6 is that the ceiling *is* the finding, burst 2
writes that up and runs nothing.

## Housekeeping

- `[measured: python3 workspace/roundtable/check_ownership.py BT2 → no BT2-owned
  path flagged]`. I wrote only `backtest/BT2/{ALGOS,VERIFY,REQUESTS}.md`,
  `backtest/BT2/bursts/01_*.md`, `backtest/BT2/code/*` and
  `msgs/05_BT2_R2_verify-ALGO-1.md`. Nothing under `csv/`, nothing under
  `futures_agents/`, nothing in another agent's workspace. `msgs/` already had a
  collision at `04` (two files), so I took `05`.
- `[measured: python -m pytest -q tests → 824 passed in 90.99s]` — the repository
  suite, quoted as the untouched baseline rather than as a result.
- `[measured: the pre-flight run twice → byte-identical output]`. No RNG anywhere
  in ALGO-1; the only mutable state is the per-year event cache, and a test
  asserts a reading does not depend on what else is in it.
