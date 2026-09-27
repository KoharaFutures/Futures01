# BT2 — fidelity log

One numbered question per algorithm, its channel, and its verdict. An algorithm
leaves this file only as FAITHFUL or DIVERGENT-and-fixed. **Nothing is measured
from anything still open.**

---

## V-1 — ALGO-1 scheduled-event entry gate, on the contract's own session

- **Asked:** `msgs/05_BT2_R2_verify-ALGO-1.md`
- **Answered:** (awaiting R2)
- **Verdict:** **ASKED** — open.
- **Blocks:** every performance number ALGO-1 could produce. The code runs and
  passes 26 tests; not one of them is a result.

### The six questions, in the order they matter

| # | question | my choice | what changes on each answer |
|---|---|---|---|
| Q1 | which instant inside the bar is the clock read at — open, or the decision instant? | open, matching `features.py` | on a 60m frame, whether the arm measures fills 60–120m after the print (open) or 30m after it (offset). One keyword; the window being tested moves by a whole bar length |
| Q2 | does a print landing outside the contract's own session still count? | yes, keep it; the session gate is `rth_only`'s job | **28 of MCL's 73** admissible bars on `csv/raw`, **65 of 164** on the archive — ~40% of crude's sample. MGC unaffected (0 of 31) |
| Q3 | HIGH only, or MEDIUM too? | HIGH only in the primary arm | in-session event days 32 → **105** on MGC, 49 → **58** on MCL. If MEDIUM is in scope it is ALGO-2, with its own deflation |
| Q4 | the avoidance arm removes **0** of 1,093 MGC bars at 60m. Null, or non-measurement? | I lean non-measurement and will not report it as a null without a ruling | whether the avoidance arm is run at all |
| Q5 | overlapping prints — nearest, or first-of-episode? | nearest, matching `features.py` | the FOMC pair collapses onto one admitted bar either way; the *anchor* of the after-window moves by 30 minutes |
| Q6 | does the ceiling (69 MGC / 164 MCL over two years) change what the finding asks for? | I have pre-registered that I expect no separation from placebo | whether burst 2 runs a backtest at all, or whether the ceiling arithmetic *is* the deliverable |

**Why Q1 and Q4 are one question wearing two hats.** Both are consequences of the
same arithmetic: every HIGH rule prints at :00 or :30, and hourly bars open only
at :00. That single fact makes the blackout window contain no bar open (Q4) and
puts the after-window's admitted bar a full hour away from the print's own
reaction (Q1). **If the finding is about the reaction window rather than about the
condition as wired, then 60-minute bars cannot express this family at any
parameterisation, and the deliverable is that sentence rather than a backtest.**
That is the single most decision-relevant thing this burst produced and I am not
going to decide it myself.

### Pre-registered before any answer arrives, so it cannot be chosen after seeing a result

- **Search size is 2** — two gates at the library's own settings
  (`avoid_event(10,15)`, `after_event(15,60]`), on two contracts. Four
  secondaries exist in code (`cluster_minutes=60`, `offset_min=bar`,
  `min_impact=MEDIUM`, `into_event`) and are **unmeasured**; running any of them
  raises the stated search size and I will restate it at that point. Programme-wide
  `free_t = 5.46`; largest t ever found here 3.923.
- **Controls:** `placebo_random` (count-matched on the base strategy's own
  eligible bars) and `placebo_shuffle` (its own timestamps permuted), both through
  ALGO-1's own exits, filters and sizing, via `workspace/newstrats/placebo.py`.
  **Not `placebo_shift`** — it retains part of the real signal and is a
  conservative control only `[repo-verified: workspace/studies/DEFECTS.md
  D42:620-638]`.
- **No comparative claim through `T.ab`** (D28: inflates z ~3.3×). The arms are
  the same base strategies with one condition appended, so the comparison is
  paired over base strategies; the test will be named when a number is reported.
- **Cells are MGC and MCL.** MNQ appears only as the reference arm that
  reproduces R2-D5's 7, because MES/MNQ/NQ/ES are one index complex and agreement
  between them is not corroboration (BRIEF; D14/D41).
- **Store is stated on every row.** Primary `data/archive` for power, `csv/raw`
  reported beside it for comparability with F11, never pooled.
- **`rth_only=True` in the primary arm**, against `toolkit.make_strategy`'s
  default, because D24's correction measured that `rth_only=False` buys trades and
  costs paired median expectancy, and because R2's 7/32/49 are in-session counts.
- **I expect no separation from placebo** at ceilings of 69 and 164, and I am
  saying so now.

### What I verified myself, which is not a substitute for R2's ruling

`[measured: python -m pytest -q workspace/roundtable/backtest/BT2/code/test_algo1.py
→ 26 passed in 46.65s]`

- **The census reproduces R2-D5 exactly** — MNQ 7, MGC 32, MCL 49 in-session HIGH
  event days, each on its own `ContractSpec` session (08:20–13:30 / 09:00–14:30 /
  09:30–16:00), and R2's per-rule split item for item (MGC: NFP 11, CPI 11, PCE
  10; MCL: EIA 49, FOMC 8). R2's self-corrected numbers are independently
  confirmed. The three contracts' in-session event sets are **disjoint**
  (asserted), which is stronger than "MNQ had fewer".
- **The gates are the library's conditions, generalised, not replaced.**
  `avoid_event()` and `after_event()` at their defaults agree bar-for-bar with
  `outside_news_blackout` and `post_news_window` over whole real series
  (MGC 5,000 bars, MCL 1,200 bars). Two tests.
- **No look-ahead** on the calendar axis: appending bars never changes a
  historical reading; a reading does not depend on the series it sits in; per-year
  caching neither loses nor duplicates an event shifted across a year boundary by
  `holiday_shift`.
- **Both silent-wrong-answer channels are closed and tested.** Distinct condition
  `name` per parameterisation, because `Condition.evaluate` memoises on
  `(name, tf)` (`base.py:120`) and `run_many` allocates one cache per bar
  (`engine.py:284`) — R2's own `R2_expressibility_wall.md` §1.5 mechanism, and
  D38's shape. `gate_arm` passes `_id=None`, because `run_portfolio` keys results
  on `strategy_id` (`engine.py:277`) and a cached id would make the gated arm
  report the bare arm's trades.
- **`EventClockError` is not swallowed.** It subclasses `RuntimeError`, outside
  the tuple `Condition.evaluate` catches (`base.py:131-133`), asserted directly.
  A misconfigured clock aborts the sweep instead of reporting zero trades.
- **D38 cannot reach ALGO-1**, and not by workaround: the gates read `snap.ts` and
  `snap.symbol` only, so they need no frame registration, and `algo1.py` builds
  its frame in the open rather than going through `toolkit.measure_custom`.
- **Two structural zeros asserted rather than discovered:** `after_event` can
  never fire on a daily bar (stamped at midnight ET, so `since` is never in
  (15, 60]) — which makes `post_news_window` identically false on every daily
  series here, MGC_1d's ten years included; and an hourly grid admits at most one
  bar per print.
- **One documented divergence from `features.py`, and the reason it is inert.**
  `_build_news_proximity` looks back only 2 days (`features.py:955`) against 45
  days forward, so `minutes_since_high_impact` reads `inf` on the bars before the
  series' first print. `[measured: 56 of 5,000 MGC_1h bars, 53 MCL, 52 MNQ, 54
  MES; largest hidden gap 10,050 minutes = 6.98 days]`. Inert for the library and
  **asserted** to be: the artefact only fires beyond 2,880 minutes and every
  library window is ≤ 60. Live for any condition wider than two days. BT2-REQ-1.
- **The two stores are the same series on the overlap**, re-verified for MGC and
  MCL at 60m as BRIEF.md's data ruling requires, with one correction: closes are
  not bit-identical `[measured: max |Δclose| → MGC 3.44e-07, MCL 4.82e-08, MNQ
  0.0, MES 0.0]`, and volume differs on 2 of ~4,987 bars for **all four**
  contracts, not only MGC.
- **Determinism**: the pre-flight run twice produces byte-identical output
  `[measured: algo1.py --symbols MGC,MCL --store csv, twice → diff -q clean]`.
  The clock has no RNG anywhere; the only state is the per-year event cache, and
  a test asserts a reading does not depend on what else is in that cache.
- **The deterministic core is untouched.** BT2 wrote only under
  `backtest/BT2/**` and one `msgs/` file; nothing in `futures_agents/` changed.
  `[measured: python -m pytest -q tests → 824 passed in 90.99s]` — quoted as the
  baseline, not as a result of ALGO-1.
- **Off-the-hour bars, which is why MCL's avoidance count is 9 and not 8.** 4,992
  of 5,000 `csv/raw` hourly bars open at :00; the other **8** open at **:30**, on
  shortened sessions (20 of ~11,000 in the archive, identically on all three
  symbols). A :30 print can only land on a bar's own open on one of those, and
  exactly one does: MCL's EIA print on 2025-12-24 at 10:30. Pinned by
  `test_hourly_bars_open_on_the_hour_except_on_shortened_sessions`, because it is
  the difference between "the filter can never decline" (false) and "it declines
  only on FOMC days and half-days" (true).
