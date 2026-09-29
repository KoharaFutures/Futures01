# BT2 — sub-task requests for the manager

PIPELINE §3 shape. Appended as they arise; I keep working rather than stalling on
any of them.

---

## BT2-REQ-1 `features.py`'s news lookback is 2 days against 45 days forward

- **Arose in:** burst 01, building ALGO-1's event clock and testing it for
  bar-for-bar agreement with `FeatureSnapshot`'s three news fields.
- **The ask:** record as a defect in `workspace/studies/DEFECTS.md` (I may not
  write that file), and decide whether `futures_agents/features.py:955` should
  change. Someone who owns `futures_agents/` would make it a one-line edit.
- **What it is.** `SymbolFrame._build_news_proximity` projects events over
  `bars[0].ts − 2 days .. bars[-1].ts + 45 days`
  `[repo-verified: futures_agents/features.py:952-959]`. The forward side carries
  a six-line comment explaining *why* 45 days ("at +5 days a run ending mid-month
  reported 'no high-impact event ahead' purely because CPI, payrolls and PCE all
  sat outside the projection"). The backward side is `timedelta(days=2)` with no
  comment, and it has exactly the symmetric failure: `minutes_since_high_impact`
  reports `inf` — read by every consumer as "no high-impact release has ever
  happened" — on every bar before the first print inside that window.
  `[measured: 56 of 5,000 MGC_1h bars, 53 of 5,000 MCL, 52 MNQ, 54 MES; the
  largest hidden gap is 10,050 minutes = 6.98 days, a whole CPI-to-NFP interval]`
- **Why it is smaller than it looks, stated so nobody over-corrects.** It is
  **behaviourally inert for every condition in the library today**, and ALGO-1's
  test suite asserts that rather than assuming it: the artefact can only fire when
  the true gap exceeds 2,880 minutes, and every window any library condition uses
  is at most 60 minutes (`outside_news_blackout` 10/15, `no_imminent_release` 30,
  `post_news_window` 15/60). A hidden value was therefore already outside every
  window. **It stops being inert the moment anyone writes a condition with a
  window wider than two days** — e.g. "more than a day since the last catalyst",
  or any MEDIUM-impact variant with a weekly cadence.
- **Why it cannot wait / why it can:** it can wait. ALGO-1 is unaffected because
  it reads its own clock. It is worth writing down now because the *next* person
  to use the snapshot field will not find this out.
- **What it blocks:** nothing.
- **My estimate of its size:** small (one constant, plus a test).

---

## BT2-REQ-2 there is no flatten-before-the-print exit, and II-11 as operated needs one

- **Arose in:** burst 01, choice C7 — comparing ALGO-1's gate against R2-D2c's
  operating clock (`research/R2_relational.md:1048-1091`).
- **The ask:** decide whether an event-driven exit is in scope for this programme,
  and if so add a sub-task to build it. It is a change to
  `futures_agents/backtest/engine.py` and `ExitReason`, which BT2 does not own.
- **What it is.** R2-D2c's operator is **flat** at 10:30: "Flat. No position. The
  first print is won by machines." Every filter in the library, ALGO-1's gates
  included, can only prevent *initiating* — the engine evaluates conditions in
  step 3 of the bar loop, for strategies not already positioned
  `[repo-verified: futures_agents/backtest/engine.py:305-307]`. A position opened
  before the window is carried straight through the print. `ExitReason` has seven
  members (TARGET, STOP, BREAKEVEN, TRAIL, TIME, SESSION_CLOSE, END_OF_DATA)
  `[repo-verified: engine.py:49-57]` and none of them is news, while
  `ExitModel.exit_at_session_close` shows the pattern an event-close exit would
  copy.
- **Why this is not cosmetic.** It means "avoid the event" as this repo can
  express it is a *strictly weaker* statement than "avoid the event" as the family
  is operated, and any null from the avoidance arm is a null about the weaker
  statement. That distinction has to be in whatever gets written up, whether or
  not the primitive is ever built.
- **Why it cannot wait / why it can:** it can wait. ALGO-1 is measurable without
  it, with the divergence declared.
- **What it blocks:** the faithful form of II-11's avoidance arm, and R3's
  time-based-exit family probably wants the same primitive.
- **My estimate of its size:** medium.

---

## BT2-REQ-3 the event family may be unmeasurable at 60m, and the finer frames are ~2 months long

- **Arose in:** burst 01, ALGO-1's pre-flight ceiling.
- **The ask:** either (a) rule that a 60-minute measurement with a ceiling of 69
  (MGC) / 164 (MCL) admissible bars is worth running with its placebo, or (b) add
  a sub-task to establish whether `data/archive` 15m is usable, which would be the
  only way to test this family at a resolution that matches its windows.
- **What it is.** Every HIGH rule prints at :00 or :30; hourly bars open only at
  :00. Three consequences, all measured
  `[measured: python3 workspace/roundtable/backtest/BT2/code/algo1.py --store csv
  --store archive]`:
  1. The `[−10, +15]` blackout around an 08:30 print contains **no hourly bar
     open**, so `outside_news_blackout` declines on **0 of 1,093** eligible MGC
     60m bars — it is the identity filter on gold.
  2. `post_news_window` admits **at most one bar per print**, and when two prints
     fall within 60 minutes they share it: 8 bars on MNQ, 31 on MGC, 73 on MCL
     over `csv/raw`'s ~11 months; 19 / 69 / 164 over the archive's ~2 years.
  3. The bar the after-window admits sits a full hour from the print, so the fill
     is 60–120 minutes after it rather than 15–60.
- **The blocker on the obvious fix.** 15m would resolve all three. `csv/raw`'s
  `MGC_15m` and `MCL_15m` span **2026-07-26 → 2026-09-22**, about two months —
  roughly 6–8 event days, which is worse than the 60m ceiling. `data/archive` has
  `MGC_15m.jsonl` / `MCL_15m.jsonl`, but BRIEF.md's data ruling condition 2
  requires verifying store equivalence **per symbol and timeframe**, and the
  ruling's own table is 60m only. I have verified 60m for MGC and MCL; 15m is
  unverified and I have not assumed it.
- **Why it cannot wait / why it can:** it gates what burst 2 does. If the answer
  is (a) I run the 60m null; if (b) I check 15m equivalence first, which is one
  small script.
- **What it blocks:** ALGO-1's measurement, and by extension whether R2's
  "cheapest untried thing in Class II" is testable at all in this repository.
- **My estimate of its size:** small for (a); small for (b) as well — the
  equivalence check is the same script I already wrote for 60m.
