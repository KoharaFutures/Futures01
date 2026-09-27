# Edge-finding programme — the shared brief

Six agents (EF1–EF6). Read this in full, plus `../BRIEF.md`, `../REGISTRY.md` and `../OWNERSHIP.md`,
before writing anything. The task came from the account owner directly.

## The task

Find and test strategies for **profitability**, and produce, **per symbol**:
- a **top 10 for a SWING setting**, and
- a separate **top 10 for a SCALP setting**.

Symbols: **MGC, MCL, MES, MNQ**. MGC and MCL are the only independent contracts; MES/MNQ are one
index complex sharing 0.5–0.8% of rule sets, so agreement between them is **not** corroboration.

## The session constraint — the defining rule of this programme

**A position may exist only inside 18:00 ET → 16:00 ET the following day. Nothing may be held
across 16:00–18:00 ET.** So: flat at 16:00 ET, no new position opened between 16:00 and 18:00 ET,
holding through the overnight Globex session and the next RTH open is permitted.

**Three consequences, and they are not negotiable interpretations — they are arithmetic.**

1. **"Swing" here cannot mean multi-day.** The longest possible hold is one 18:00→16:00 cycle,
   **22 hours**. A strategy whose thesis needs three days cannot be tested under this rule. Say so
   rather than quietly truncating it.
2. **This has never been run in this repository.** `allow_overnight` defaults to `False` and
   **no call site anywhere passes `True`** `[repo-verified: grep over the tree → engine.py:233,241,470
   only]`, so every one of ~2.97M prior evaluations was flat by its contract's RTH close. The
   overnight-hold regime is genuinely unmeasured. That is the opportunity here, and it is also why
   no prior result transfers.
3. **The rule cannot be expressed by the engine today.** `exit_at_session_close` closes at the
   *contract's own RTH close* — `minutes_since_open(bar.ts, spec.rth_open) + bar.minutes >=
   self._rth_minutes` `[repo-verified: engine.py:470-473]` — which is **13:30 for MGC** and 14:30
   for MCL, not 16:00. And it is gated on `not self.allow_overnight`, so turning overnight on
   removes the session exit entirely rather than moving it. **A flat-at-16:00-ET clock rule does not
   exist and must be built.** That is EF1's job and it gates everyone else.

## The substrate, measured — and the scalp half is underpowered

| timeframe | bars/symbol | span |
|---|---|---|
| 1m | ~6,880 | **4 days** |
| 5m | ~11,215 | **57 days** |
| 15m | ~3,745 | 57 days |
| 30m | ~1,874 | 57 days |
| 60m | ~11,000 | **718 days** |
| 240m | ~3,000 | 718 days |
| 1440m | 4,008 (MGC) | 5,835 days |

`t ≈ SR × sqrt(years)`. **[Corrected 2026-09-27, ADJ-15: the span is 57.90 days = 0.1585 years,
sqrt = 0.3981, and the Sharpe needed is 2.96, not the 57 days / 2.98 this brief first said.
Verified against `data/archive/MGC_5m.jsonl`. These figures are canonical and belong on every row,
not once in a preamble.]** So on the scalp timeframes, clearing even `free_t = 1.177` — the floor
for a *single pre-registered* hypothesis — needs a sustained annualised Sharpe of **2.96**, and clearing a search-width threshold is arithmetically
out of reach. **Report the scalp top 10 with that bound attached to every row.** A ranked list
whose power is this low is a description of the sample, not a forecast, and must be labelled as one.

Swing at 60m/240m has 718 days = 1.97 years, sqrt = 1.40 — better, and still short.

## Guardrails. Every one of these has caught a real error in this repo already

1. **A placebo beside every reported row.** Count-matched random bars or timestamp-shuffled, run
   through the row's own exits, filters and sizing, under the same 18:00–16:00 rule.
   `placebo_shift` leaks (D42) and is conservative-only.
2. **State the search size and the deflation threshold.** `free_t = sqrt(2·ln n)`. If you screened
   40,000 variants, say 40,000. Quote the span beside it.
3. **Never route a comparative claim through `T.ab`** — it inflates z ~3.3× (D28). Name your test.
4. **`_id=None` on every `dataclasses.replace`, and assert arm-id uniqueness at emission.** D48:
   without it both arms collide into one `BacktestResult` and the measured difference is **exactly
   zero**, which is indistinguishable from "this makes no difference".
5. **A firing-rate check on every condition before any row is reported.** 19.0% of generated
   strategies carry a condition that can never fire, and `Strategy.evaluate` is a strict AND, so one
   dead condition kills the strategy. Per-symbol: MGC 11.5%, MCL 13.9%, MES 22.6%, **MNQ 27.4%**.
   A strategy that never traded and a strategy that traded and lost both produce a null. **Only the
   second is a result.**
6. **A look-ahead power control does not license reading nulls as absence.** A cheat is a different
   strategy that fires normally; ranking it first says nothing about whether any other strategy's
   detector fired. This was retracted from the published corpus on 2026-09-27.
7. **Win rate and payoff cancel.** Never quote one without the other and without expectancy in R.
8. **Costs, always.** MCL is cost-fragile: costs flip 8 of 183 MCL 60m rows from positive gross to
   negative net, against 1 of 259 for MGC.

## What the last attempt at exactly this found

The programme has produced ranked top-10 lists before. **Trading last period's top 10 returned
−0.0155R against a −0.0104R null, and underperformed trading the entire qualifying universe**
(+0.022R against +0.057R). *Selecting was worse than not selecting.* Name overlap across disjoint
thirds was at or below chance; Jaccard 0.081.

That is not a reason to refuse this task. It **is** the reason every list you produce must carry
its out-of-sample behaviour, not just its in-sample rank. **A top 10 ranked in-sample and reported
without a forward test is the exact artefact this repo has already been burned by.**

## Deliverables

Per agent, in your own directory: `FINDINGS.md`, `code/`, `bursts/NN_*.md`. Short bursts — one
cell, or one arm, or one verification, then written down and stopped.

The final lists go in `workspace/roundtable/edge/RESULTS.md`, which **the parent session owns and
writes**. You hand it rows with their controls, their search size, their span and their forward
behaviour; you do not write it yourself.

## Rules

`csv/` is read-only, always — never delete or edit any file under it, no matter what.
`data/archive/` is append-only and is the substrate for this programme (verified same series as
`csv/raw` at 60m, bit-identical on MNQ/MES and within 3.4e-07 on MGC/MCL — compare with a
tolerance, never `==`). Label every number with its substrate. Mark claims
`[repo-verified: path:line]` or `[measured: cmd → result]`. Append as you go. Post questions as
`msgs/EF<n>-NN_<to>_<topic>.md` with the `RE:/ALSO:/FROM:/TO:/TASK:` header. Do not commit or push.

---

# The 240m and 1440m cells are inexpressible under this rule (EF6, verified 2026-09-27)

The session window is 22 hours = **1320 minutes**, and `1320 = 2³ · 3 · 5 · 11`. A timeframe can
carry the rule only if it divides the window evenly:

| timeframe | 1320 / tf | |
|---|---|---|
| 5m, 15m, 30m, 60m, 120m | 264, 88, 44, 22, 11 | **expressible** |
| **240m** | **5.5** | **NOT expressible** |
| **1440m** | **0.917** | **NOT expressible** |

**A 4-hour bar cannot align with a 22-hour window.** This is arithmetic, not an implementation
limit, and no harness fix reaches it. Consequences:

- **The swing programme is 60m only.** The 240m arm of EF2's and EF3's cells is withdrawn — half of
  each original assignment. Neither agent did anything wrong; the cell cannot exist.
- It explains EF3's observation that EF1's `SPANS_WINDOW` violations were **all at 240m**. Those
  were not a bug in the flat so much as the flat being asked to land on a grid that cannot hold it.
- Any future request for a daily or 4-hour arm under this rule needs the *rule* changed, not the
  code. A 24-hour window (1440) would divide by 240 and 1440 both; a 22-hour one cannot.

## And the scalp threshold is far worse than this brief first said

`EF6-H3` computes the threshold from the actual search size rather than from a single hypothesis:

| cell | span | sqrt(years) | free_t | required annual Sharpe |
|---|---|---|---|---|
| swing 60m | 718.83 d | 1.403 | 3.505 | **2.498** |
| scalp | 57.90 d | 0.398 | — | **9.59** |

This brief's earlier figure of 2.96 was the floor for a *single pre-registered* hypothesis. At the
search width these cells actually use, the scalp requirement is **9.59**. That number does not
occur in futures. **Use `EF6/code/deflation.py`; do not derive a threshold by hand and do not quote
5.46.**
