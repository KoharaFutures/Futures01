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
