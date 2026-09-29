# R3 — board requests

Per PIPELINE §3. Filed and then I kept working; none of these stalled my round-2 tasks.
Shape is PIPELINE §3's. IDs are `R3-REQ-<n>` per REGISTRY.md.

---

## R3-REQ-1 `dataclasses.replace` inherits the cached `_id`, silently merging both arms of any paired re-emission — needs a `D<n>`

- **Arose in:** round-2 task 2, specifying the D15 paired re-emission for my seven remaining
  §7-Q2 items (`research/R3_pairing_design.md` §2, filed there as finding **R3-A-13**).
- **The ask:** allocate a programme-wide `D<n>` in `workspace/studies/DEFECTS.md`. Only the
  manager allocates `D` numbers (REGISTRY.md), so I cannot. I am not asking for a code change —
  see "why it can wait" — I am asking for the number, because this belongs in the file that
  every agent is told to read before trusting a library function, and it is the **third** instance
  of a defect family that already has two entries there.
- **The defect:** `Strategy._id` is a real dataclass field `[repo-verified: base.py:585]` and
  `strategy_id` memoises into it via `object.__setattr__` `[repo-verified: base.py:622]`.
  `dataclasses.replace` copies every field including `_id`, so a `replace` after `strategy_id`
  has been read yields a strategy claiming the original's id. **`generate_strategies` has already
  read it** — its dedupe is `seen.setdefault(st.strategy_id, st)`
  `[repo-verified: combinator.py:719]` — so every strategy it returns arrives with `_id`
  populated:
  `[measured: S=generate_strategies('MGC',[5,15,60,240],max_total=400); S[0]._id →
  'MGC-15m-668c0ed86d86' before anything touches strategy_id]`
  `[measured: replace(S[0], exit=replace(S[0].exit, trail_atr_mult=2.0)).strategy_id ==
  S[0].strategy_id → True]`
  `[measured: adding _id=None → ids differ]`
- **Why it matters more than it looks:** `run_many` keys `results` `[repo-verified:
  engine.py:277-281]`, `open_pos` and `pending` `[repo-verified: engine.py:282-283]` and the
  in-position skip guard `[repo-verified: engine.py:304-309]` all by `strategy_id`. A colliding
  pair therefore produces **one** `BacktestResult` whose trades are a path-dependent interleaving
  of both arms' exits, and the measured difference between arms is **exactly zero**. That is a
  **false null**, and every item on my §7-Q2 list is a "does this axis do anything" test — so the
  failure mode is indistinguishable from the result. This is the same family as the
  `ExitModel.label` fix and D43, but **D43 does not fix it**: D43 repaired what goes *into* the
  hash, and this defeats the hash by not recomputing it.
- **Why it cannot wait / why it can:** the *number* cannot wait, because any agent attempting a
  paired re-emission before it is recorded will hit this. The *code* can wait indefinitely — the
  combinator already uses the correct idiom at `combinator.py:694`
  (`replace(x, symbol=s, _id=None)`), so the library is not wrong, only sharp. My
  `R3_pairing_design.md` §2 states the discipline (`_id=None` on every `replace`, plus an
  `assert` on arm-id uniqueness at emission). If anyone does want a code change, the smallest
  honest one is to drop `_id` from `replace`'s reach by making it a non-field cache attribute —
  but that is a library change with test surface and I am not requesting it.
- **What it blocks:** nothing of mine; it is already worked around in the design. It blocks
  **any other agent** who pairs strategies without knowing.
- **My estimate of its size:** small (a `DEFECTS.md` entry). The optional code change is small-to-
  medium because of the test surface.

---

## R3-REQ-2 An exogenous-entry replay harness — the only route to trade-level pairing

- **Arose in:** round-2 task 2, `research/R3_pairing_design.md` §4 (finding **R3-A-14**).
- **The ask:** add a sub-task — a harness that runs a control strategy, harvests its
  `(entry_index, entry_price, direction, signal)` tuples, and then drives `_manage` over each
  treatment arm's `ExitModel` from **those fixed entries**, rather than letting each arm generate
  its own.
- **Why:** pairing on this engine is currently only possible at the **rule-set** level, never the
  trade level, and the reason is `engine.py:304-309` — a positioned strategy does not look for
  signals, so any axis that changes holding duration changes which later bars the arm is flat for.
  Measured on the one paired re-emission that already exists on disk (the geo study: 22 rule sets
  × 2 exits × 8 cells × 3 slices = 258 pairs), **the two arms of a pair share a median of 61.8%
  of their entry timestamps**, only 17 of 258 reach 90%, and the median trade-count ratio is
  1.332 `[measured: entry-timestamp Jaccard over stops_cache.json, see R3_pairing_design.md §4.3]`.
  An exogenous-entry harness holds the population *exactly* fixed and reduces the comparison to
  the pure exit effect — which is what D15 actually asks for and what no design available today
  can deliver.
- **Why it is cheap:** `_manage(self, pos, i, bar, *, is_last)` takes a `Bar` and needs no
  `FeatureSnapshot` `[repo-verified: engine.py:377-378]`. That is the same fact that makes
  condition-based exits impossible (the subject of R3-Q3) and it makes **this** harness easy —
  there is no feature plumbing to hoist, only a loop that opens a position at a given index and
  steps `_manage` forward.
- **Why it cannot wait / why it can:** it can wait. `R3_pairing_design.md` is written to work
  without it, at the rule-set level, with n = 1,260 pairs. But every result produced that way
  carries a permanent caveat this harness would remove, and it is the highest-leverage single
  piece of code on my track.
- **What it blocks:** nothing outright. It **upgrades** the statistic available to all seven of my
  §7-Q2 items from a rule-set-level paired test to a trade-level one.
- **My estimate of its size:** medium. New code path, so outside the "zero new code" framing of
  Tier 1 — that is precisely why it is a request rather than something I designed around.

---

## R3-REQ-3 `OPEN_QUESTIONS.md` — my round-1 dispatch was stale, and I am recording the switch

- **Arose in:** round 2, on reading `OWNERSHIP.md` (the "one live exception" section) and
  `REGISTRY.md`.
- **The ask:** nothing to add to the board. This is a record, filed where the manager will see it,
  that I have switched channels and that my round-1 appends need no action.
- **Detail:** my round-1 dispatch told me to append cross-track questions directly to
  `OPEN_QUESTIONS.md`. `OWNERSHIP.md` names the manager as its sole writer and declares my
  round-1 appends a defect in the *dispatch*, not the map, with the appends standing. **I have
  made no edit to `OPEN_QUESTIONS.md` in round 2** and will not. Round-2 correspondence went out
  as `msgs/03_R3_BT3_re-verify-ALGO-1.md`. My two questions are canonically **R3-Q1** (VWAP_BAND,
  to R1) and **R3-Q2** (the §6 refutation, to the manager) per REGISTRY.md; a bare `Q2` or `Q3`
  from me is malformed and I have stopped writing them.
- **What it blocks:** nothing.
- **My estimate of its size:** none.
