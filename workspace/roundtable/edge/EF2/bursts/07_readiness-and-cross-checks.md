# EF2 / Burst 07 — readiness, and three cross-checks against other agents' findings

Written while `EF1-H1`/`EF1-H2` are still being repaired, so that everything not gated on them is
finished and the measurement is a single command when the gate opens.

## 1. Cross-check: EF1's own validation run confirms both halves of my Burst 06, on its own substrate

`EF1/bursts/03_the-gate-failed-33-violations-on-early-close-sessions.md` ran three arms over
`data/archive` 60m with `max_total=400` and found **33 `SPANS_WINDOW` violations in arm C**, which is
the arm that is supposed to have zero. Every one was `primary_tf = 240m`, and **18 of the 33 were
MCL**. Two independent measurements, different methods, same two causes:

| | EF1's count | EF2's count | why they differ, and both are right |
|---|---|---|---|
| MGC | **9** ET dates | **17** cycles | EF1 counts ET dates carrying bars before 16:00 but no deadline bar. EF2 counts 18:00→16:00 **cycles** with no actionable bar, which additionally catches cycles that are entirely overnight — e.g. the cycle ending 2024-11-28, whose only bars are 18:00–23:00 on 11-27. Different denominators (596 dates vs 506 cycles), not a disagreement. |
| MCL | **27** ET dates | **34** cycles | same |

And EF1 reached the MCL data hole independently: *"a two-month hole in MCL 60m — 17 further dates,
2026-01-12 to 2026-03-10 … 1 to 5 bars each … this is a substrate defect, not a calendar one, and it
is EF2–EF5's problem as much as mine."* My Burst 06 puts a number on it — **366 missing bars over 34
dates, in both stores, zero recoverable from `csv/raw`** — and traces it to the vendor rather than to
`BarArchive`. **Two agents, disjoint methods, agreeing. That is evidence rather than one measurement
wearing two names.**

**The consequence for my cell is sharper than for anyone else's**, because all 33 of EF1's violations
were at 240m and half of my four cells are 240m.

## 2. A number of EF1's that changes what my exit axis can mean

EF1's arm C reports, at `max_total=400`:

```
MGC  184 strategies   554 trades   flats 420 = 75.8% of trades
MCL  167 strategies  2179 trades   flats 1283 = 58.9% of trades
```

**Between 59% and 76% of all trades are closed by the 16:00 flat**, not by their stop, their target
or their time stop. So in the swing setting the **clock is the dominant exit**, and the catalogue's
twelve geometries are differentiated mostly by where their *stop* sits, not by where their *target*
does — the target is usually never reached.

That is a prediction I can make now and it is falsifiable: **the spread of expectancy across exit
geometries sharing one rule set should be much narrower in the swing setting than the published
corpus reports for RTH-only runs**, and `target_kind` (`R_MULTIPLE` vs `ANCHOR_ATR` vs
`ANCHOR_STRUCTURE`, which split my population 50 / 32-35 / 15-18%) should matter less than
`stop_kind`. Registered here, before measurement. Note it is **not** one of the six pre-registered
Tier A hypotheses — it arrived from EF1's number rather than from my own design, so it is a Tier B
observation and faces the screen's threshold, not Tier A's.

It also means `time_stop_bars` being unreachable (Burst 01 §2d) costs nothing: the flat gets there
first in three quarters of MGC trades anyway.

## 3. Cross-check: my `sqrt_years` against EF6's

EF6 burst 01 measures the 60m and 240m span at **718.88 / 718.83 calendar days → 1.968 years →
sqrt 1.403**. I used 718 → 1.402. Agreement to three decimals, and EF6 separately verified that the
calendar-day-vs-trading-session convention is not load-bearing here (1.394 vs 1.403). **No dispute,
and I am adopting EF6's 1.403** so that a cross-cell comparison is not a convention comparison.

At `free_t(5092) = 4.132` that moves my required Sharpe from 2.95 to **2.946**. Immaterial, recorded.

EF6's own table also says the thing worth repeating on every row: **nobody should quote 5.46.** That
is the threshold for a search this programme has not run. My numbers are 4.132 (MGC, 5,092 arms) and
4.154 (MCL, 5,584 arms), and 3.87 / 3.87 on the fire-discounted denominators.

## 4. Id hygiene

`REGISTRY.md` allocated `EF2-H1` to "EF2's own local engine, built rather than blocking". **EF2 built
no local engine** — `measure.py` imports `EF1-H2` directly. My six pre-registered hypotheses were
already `EF2-H1..H6`, so that was a live collision of exactly the kind the registry exists to prevent.
**Renamed to `EF2-HYP-1` … `EF2-HYP-6`** across every EF2 file; verified no stale `EF2-H<digit>`
remains. Raised with the manager as `msgs/EF2-03_manager_id-collision-EF2-H1-and-no-local-engine.md`,
because `REGISTRY.md` is not mine to edit.

## 5. The one command, and the exact order it runs in

```
python3 EF2/code/measure.py --engine session            # both symbols, 4 cells, 2 rth arms
python3 EF2/code/measure.py --engine shipped            # the labelled NON-swing comparison arm
```
then, per (symbol, cell, arm) ledger written by the first command:
```
EF6/code/forward.roll(Ledger(json), lookback_days=..., criterion="expectancy")
EF6/code/placebo_w.build_cohort(frame, shortlist, realised, seed=0..19)
EF2/code/rank.select(rows, k=10)
```

`rank.py` enforces the reportability rule **in code**: a row missing its control, its search size or
its forward result is dropped rather than printed with a blank, and `select` returns however many rows
clear their own controls up to ten, with every rejection reason counted. It also carries, on every row:
the cell's count of cycles where the flat cannot fire (17 / 9 / 34 / 14), the measured D45 collapse
rate for that row's own `stop_kind` and cell, gross-vs-net and whether costs flipped the sign, and —
for MCL — a with-and-without variant for the two archive gap windows, both named before any
expectancy exists.

## 6. What EF2 is still waiting on, precisely

| blocker | owner | what it blocks |
|---|---|---|
| `EF1-H1`/`EF1-H2` session-end forced flat (component 1b), arm C back to **0** violations | EF1 | every profitability number |
| EF6's `probe_placebo` on **MCL** — EF6 measured MGC and MNQ only | EF2 (running) | whether MCL rows may carry a `placebo_random_legal` control |
| EF6's `forward.roll` being callable on an EF2 ledger | EF2 (format implemented) | the forward column on every row |

Nothing else. The population, its size, the thresholds, the VOID gate, the fire census, the stop
fidelity, the flat-reachability audit, the substrate verification and all six pre-registered
hypotheses are done and on disk.
