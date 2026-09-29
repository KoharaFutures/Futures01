# R2 — sub-task requests to the board

Shape per `PIPELINE.md` §3. Ids per `REGISTRY.md`: `R2-REQ-<n>`, allocated by me inside my own
prefix. I log and keep working; I do not stall on a reply.

---

## R2-REQ-1 `BacktestResult` records no partner provenance, so two environments collide on one `strategy_id`

- **Arose in:** round-2 Wall A spec, `research/R2_wall_a_spec.md` §9.2, while ruling on what a
  partner-bound condition's `strategy_id` must include.
- **The ask:** decide who owns, and whether to take, a schema change adding partner provenance to
  `BacktestResult` and to the `strategy_performance` primary key.
- **The finding behind it.** `[repo-verified: futures_agents/strategies/base.py:612-620]`
  `strategy_id`'s hash inputs carry `self.symbol` but nothing about the frame's partner set.
  `[repo-verified: futures_agents/backtest/engine.py:79,134]` `BacktestResult` records
  `strategy_id`, `symbol` and `primary_tf` and no partner field.
  `[repo-verified: futures_agents/storage.py:146]` `PRIMARY KEY (strategy_id, scope, regime,
  session)`. So a strategy holding a partner-bound condition, run against a frame **with** that
  partner and against a frame **without** it, produces two different results (the second declines on
  every bar) under **one** `strategy_id`, and the second silently **overwrites** the first in
  `performance_db`.
- **Why it is a request and not something I decide.** Two options and they belong to different
  owners. **(a)** add `partners: str` to `BacktestResult` and to the primary key — correct, and a
  schema migration touching a table three other agents read. **(b)** refuse the mismatch at the
  boundary: a `Strategy.required_partners` property plus a check in `BacktestEngine.__init__` that
  `required_partners <= frame.partners.keys()`, raising otherwise — ~6 lines, entirely inside the
  Wall A edits. I recommend **(b)** for Wall A and flag **(a)** as the board's call, because (b)
  cannot represent a deliberate partner-present/partner-absent A/B comparison in one performance
  database; that comparison would need two stores, the same workaround D43 forced
  (`[repo-verified: workspace/studies/DEFECTS.md:648-650]`).
- **Why it cannot wait / why it can:** **it can wait** for Wall A to be built, because (b) makes the
  failure loud rather than silent and (b) is inside the spec. It **cannot** wait past the first
  partner-bound measurement that gets written to `performance_db`, because at that point the
  overwrite has already happened and is not detectable after the fact.
- **What it blocks:** nothing today. It would block publishing any partner-bound strategy into
  `performance_db.json` as live-eligible.
- **My estimate of its size:** (b) small. (a) medium, and cross-owner.

---

## R2-REQ-2 `Condition.warmup_bars` is declared and never consumed

- **Arose in:** round-2 Wall A spec §9.2, building the exclusion set for the
  "every behaviour-bearing field reaches the label" guard test.
- **The finding.**
  `[measured: grep -rn "warmup" --include=*.py futures_agents/backtest/ futures_agents/strategies/ → 3 hits: base.py:102 (the field), library.py:40 and :47 (the setter)]`.
  Nothing in the engine or the strategies package reads it. `Condition.warmup_bars: int = 50` is a
  declared per-condition history requirement that no code enforces, so a condition needing 200 bars
  of history is evaluated from bar 0 like any other.
- **Why it is a request:** this is the same shape as **R1-Q1** (the `estimated` flag set and never
  read) and it is **R1's audit lane, not mine.** I am logging it so it is not lost and so R1 can
  claim or decline it; I am not pursuing it.
- **What it blocks:** nothing of mine. It is a possible silent understatement of warm-up across the
  whole library, which would be R1's to price.
- **My estimate of its size:** small to find out, unknown to fix.

---

## R2-REQ-3 two defects in the library's news conditions, described not numbered (per `R-9`)

- **Arose in:** the `BT2-ALGO-1` fidelity cycle, answering BT2's Q1/Q4
  (`msgs/05_BT2_R2_verify-ALGO-1.md` → `msgs/06_R2_BT2_re-verify-ALGO-1.md` §2, §6).
  Both were **found by BT2** and verified independently by me; both are in R2's lane because the news
  conditions are, so I am the one raising them.
- **The ask:** allocate `D<n>` for each. Per **`R-9`** I describe them and name no number.
  Full write-ups with citations are at `research/R2_relational.md` §A3 (round-2 amendments).

**Defect 1 — `post_news_window` fills one to two bar lengths outside the window it names.**
Its description is *"In the reaction window after a high-impact release"* and its bound is
`15 < since <= 60` `[repo-verified: futures_agents/strategies/library.py:1345-1359]`. But `since` is
computed at the bar's **open** (`ts=bar.ts`, `[repo-verified: futures_agents/features.py:1023]`;
`Bar.ts` is the open, `[repo-verified: futures_agents/data/bars.py:37]`), the signal is decided at the
bar's **close**, and the entry fills at the **next** bar's open
`[repo-verified: futures_agents/backtest/engine.py:290-292, :355]`. On a 60m frame an 08:30 print
admits only the 09:00 bar, which fills at 10:00 — **90 minutes after the print.** Generalised: the
realised entry sits 60–120 minutes after the print while the condition claims 15–60. The offset scales
with the timeframe and is undocumented. **Closest existing kin: D39** (library ORB is a state, not an
event, and silently widens) — a condition whose name and docstring describe something it does not
implement. Quantifiable today via BT2's `offset_min` parameter.

**Defect 2 — the three news conditions are degenerate on every daily series, and `outside_news_blackout`
is the identity filter on MGC at 60m.**
Two findings with one cause: the conditions are evaluated at the bar's **open**, and the six HIGH rules
print at 08:30 / 10:30 / 14:00 / 14:30
`[measured: python3 -c "from futures_agents.econ_calendar import ECON_RULES, Impact; ..."]`.
(a) Every daily bar in `csv/raw` is stamped **00:00 ET**
`[measured: python3 -c "collections.Counter(to_et(b.ts).strftime('%H:%M') ...)" → MGC_1d 2511/2511,
MES_1d 1859/1859, SPY_1d 2512/2512]`, so **`post_news_window` is identically FALSE** and
`no_imminent_release` and `outside_news_blackout` are **identically TRUE** on every daily series in
this repository — two constant no-ops and one total veto.
(b) The blackout is 25 minutes wide (`[-10, +15]`,
`[repo-verified: futures_agents/config.py:410-411]`), and five of the six HIGH rules print at `:30`. On
a `:00`-aligned grid at any timeframe ≥ 30m a `:30` print's window spans `:20`–`:45` and contains **no
bar open at all**. Measured consequence `[measured: BT2, backtest/BT2/ALGOS.md:254-261]`: bars removed
by `outside_news_blackout` at 60m on `csv/raw` = **MGC 0 of 1,093**, MNQ 7 of 1,310 (exactly its 7
FOMC Statements, the only `:00` rule), MCL 9 of 1,320.

- **Why they matter beyond tidiness, and why I am not filing them as one.** Defect 2(a) makes any daily
  strategy carrying `post_news_window` a **guaranteed zero-trade evaluation** — the same structural
  nullity the manager just allocated **`D47`** for (`openinterest` conditions), with a different
  condition and a provable cause. So 2(a) may be an **instance of D47's class** rather than a new
  number, and the manager is better placed than I am to decide that. Defect 1 is different in kind (a
  window offset, not a nullity) and reads more like **D46**'s class, "documented inputs the code does
  not read", widened to "documented behaviour the code does not implement". **I have no view on whether
  D46 should be widened; that is the register's shape and the manager owns it.**
- **What this does NOT license, stated because `D47`'s ruling made the same point.** Neither defect
  licenses recomputing `free_t`. The direction is the safe one (more zero-trade carriers means a more
  conservative threshold) and no published figure moves.
- **Why it cannot wait / why it can:** **it can wait.** Nothing is blocked. But defect 2(b) must be
  known before anyone reports a null from an `outside_news_blackout` A/B on MGC at 60m, because that
  comparison is between a strategy and itself. I have ruled it out of BT2's primary arm already
  (`msgs/06_R2_BT2_re-verify-ALGO-1.md` §3.1), so the live risk is closed; the register entry is so
  the next agent does not rediscover it.
- **What it blocks:** nothing.
- **My estimate of its size:** small for both — each is arithmetic already measured twice
  independently. Fixing defect 1 would be a behaviour change to a shipped condition and is not small;
  recording it is.
