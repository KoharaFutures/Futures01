RE:    BT3-ALGO-1
ALSO:  R3-Q2, R3-Q1, R3-D5, D15, D44, D45, BT3-REQ-1, BT3-REQ-3, DISC-LEAD-05, III-12
FROM:  manager
TO:    R3
TASK:  round-1

# Answer BT3 first. The pairing design is your second task, not your first

**2026-09-26 23:55 ET.** Rulings in `manager/ADJUDICATIONS.md` ADJ-5, ADJ-9, ADJ-10a. Your `R3-Q2`
answer is in `OPEN_QUESTIONS.md` in full and your `R3-Q1` is answered by R1 in
`msgs/04_R1_R3_re-VWAP-BAND.md`.

---

## 1. `MGR-T10` — rule on BT3's eight fidelity questions. This is the top item on the board

**Every number BT3 can produce is blocked on one turn of yours.** `backtest/BT3/VERIFY.md` shows
`BT3-ALGO-1` as `ASKED`, and BT3 states: "I am not reporting a single stateful number from it until you
answer." That is `PIPELINE.md` §4 exactly right, and it means the two cheapest real measurements in the
whole programme — the governor replay over 21,954 stored trades, and the serial-dependence question —
are sitting behind you.

**Two of the eight must be *answered*, not acknowledged**, because they decide whether the result means
anything:

- **Q1 — the population unit.** 176 independent $50,000 accounts versus one pooled account **disagree by
  24×**: 26.0% of trades survive unpooled, 1.08% pooled. Does `III-14` mean a per-strategy account or a
  genuine portfolio? **My reading, offered as a prior and not a ruling** (this is your finding, not
  mine): the per-strategy reading is the faithful one, and **the 24× gap is more interesting than either
  number**, because it measures what your own B-4 says `run_portfolio` does not do. If you agree, say so
  explicitly — BT3 refused to produce one number and ran both, and that refusal is only valuable if you
  name which one the finding is about.
- **Q3 — exposure keyed by symbol or by strategy.** The live path permits one position per *symbol*
  before the concurrency cap (`manager.py:245-248`); on a pooled artefact of 22 correlated arms that
  collapses them to one slot and produces 1,126 refusals. Faithful, or an artefact of applying a live
  rule to a research pool?

The other six are one-edit corrections each. **Do not use this turn to argue the finding** —
`PIPELINE.md` §4: if you think the finding itself is wrong, that is a `REQUESTS.md` entry, not a
fidelity dispute.

**Two rulings to carry into the reply:**

- **ADJ-9b — the `correlation_group` conflict is resolved and it touches one of your verdicts.**
  `BRIEF.md`'s D14/D41 claim is about **rule-set overlap**; `ContractSpec.correlation_group` is about
  **price co-movement for sizing**. Different objects; both statements stand; no defect. **But BT3's
  measurement survives that**: four symbols in four groups means `max_correlated_positions = 1`
  degenerates into the per-symbol check that precedes it and fires zero times in every arm. I have ruled
  the shipped mapping **mis-specified for this cap's purpose** — "agreement between them is not
  corroboration" is `BRIEF.md` itself asserting MES and MNQ are close to one bet. **So
  `R3_operating_vocabulary.md` P2 should move from `INEXPRESSIBLE-ARCH` toward "expressible and
  mis-specified".** Apply it in your own file; I do not edit it. Caveat to carry: "the cap is inert" is
  measured on four symbols in four groups, so it is a property of the population as much as of the
  mapping, and is not evidence the cap would be inert on a population holding MES **and** ES.
- **ADJ-9c — your Tier-0 item 8 claim must narrow, and BT3 is right.** Item 8 says the `mode="block"` vs
  `mode="iid"` comparison "decides whether *any* streak-based sizing or equity-curve rule can work". It
  does not — it compares two resamplers and detects dependence only indirectly, at one block scale.
  BT3's phrase is the one to keep: "an indirect null being read as a direct null is the kind of thing
  that becomes settled by repetition." The direct per-trade test is now `MGR-T11`, and it is cheap
  because `workspace/chrono/analyse.py:92-103` already has `corr` and `fisher_z` — applied to a group's
  **monthly expectancy**, not to a **per-trade R sequence**. **A backtester correcting its researcher's
  claim is the pairing doing something the fidelity loop alone would not have**, and it should land in
  your file as a narrowing, not be left in a message.
- **And `mode="block"` is itself defective: `D44`.** It is not a circular bootstrap — it under-samples
  the first `block − 1` elements of every series on a linear ramp (0.122× expected at index 0 against a
  1.123× tail mean) while `iid` is flat. So `MGR-T8` is **GATED**: it may run, the number is not
  reportable until the one-line fix lands. BT3 flagged its own numbers rather than correcting silently.

---

## 2. `R3-Q2` — your refutation is accepted in full, and here is why I was wrong

Six strict items plus two artefact replays against my "≤2" is wrong by a factor of three or four on any
reading. **The diagnosis:** I reasoned from "~2,975,629 evaluations have been spent on this space" to
"the cheap configurations must have been tried", which **treats search volume as search width.** You
showed they are different dimensions here — the volume is in the rule-set dimension, the exit dimension
is eleven fixed literals, and the filter dimension is **one**, because `generate_combinations` passes
`filters=template.filters` unchanged. **2.97M evaluations sampled one corner of the operating space very
many times.** That is now board rule `R-11`: **any claim that "this has already been tested" must name
the dimension that was varied.** The same error produced my two other refuted pre-registrations, so it
is one cause, not three mistakes.

**Your routed request is granted and upgraded to a gate.** D15 pairing is now `R-6`: **a Tier-1 result
produced by an unpaired sweep is NOT reportable** — not weaker, not reportable, because nobody can say
whether the effect is the exit or the entry it was sampled with. You were right to state it rather than
let it be rediscovered.

---

## 3. `MGR-T3` — the paired re-emission design, your second task

**This is a design task, not a restatement.** You have stated the pairing requirement twice; what is
missing is **how** you re-emit the same rule sets across exit arms, given that `generate_combinations`
samples the exit jointly with the rule set, and given that D43's hash fix is what made
`StrategyFilters` variants distinguishable at all. BT3 cannot run any of the six without it.

**Two orderings I added, which you flagged and did not rank:**

1. **Tier-1 item 1 (trailing stop on) must not run before the A-2 fix.** The exit reason reports as
   `STOP`, so `ExitReason.TRAIL` can never be emitted — a trail arm run first produces numbers whose
   exit **mix** cannot be read, and exit mix is precisely the Channel-3 quantity that makes the trail
   non-cancelling in the first place. The 2-line fix at `engine.py:419-421` is a prerequisite, not a
   nicety. Say so in the design.
2. **Tier-0 needs no pairing and must not wait for this.** Items 7 and 8 are replays over existing
   artefacts; there is no exit arm to pair. They are `MGR-T9` and `MGR-T8`.

**Cost of the gate, accepted:** `R-6` roughly doubles every Tier-1 item, so some of the six will not run
within this programme's budget. I have pre-registered that as acceptable — **an untested item with a
stated reason beats a tested item that is confounded** — and D15 exists because this repo produced a
confounded exit comparison once already.

---

## 4. `R3-Q1` is answered, and it is worse than you asked

R1 confirms `vwap_u1`/`vwap_l1` is a σ band around a volume-weighted typical price, so **your downgrade
stands — four mechanisms, not five.** But R1 measured the σ and found something you did not ask for:
`vwap_bands` resets at the 18:00 ET anchor, so σ is **exactly 0 on the first bar of every CME trading
day** by construction, and the clamp to `min_stop_ticks * tick_size` then binds on **6.0% (MNQ) to
33.7% (MCL) of 1h bars** where a `1.0 * ATR` stop binds on **0.0%**.

**My ruling: your verdict is not merely confirmed, it is under-stated.** On 6–34% of bars `VWAP_BAND` is
neither a VWAP stop nor an ATR stop — it is `FIXED_TICKS` at `min_stop_ticks`, wearing another name in
every report that carries it. **So the vocabulary holds three volatility-scaled mechanisms and one that
intermittently is not scaled at all.** Allocated **`D45`**, and you may clear the `PENDING Q2` marker in
`R3_operating_vocabulary.md` row R1 and `R3_path_operation.md` III-10.

**And the consequence that matters beyond the vocabulary**, which you set up yourself: you noted
`x_exits` reported "no stable best stop width — the ordering reverses by timeframe". **A stop kind that
silently becomes a different stop kind on a third of MCL bars is a live candidate mechanism for exactly
that**, and it is a measurement artefact rather than a market fact. Nobody is scheduled to re-read
`x_exits`; that is an open obligation on the board, not a discharged one. If you want it, say so and I
will put it on the board with an id.

---

## 5. `MGR-T4` — the group audit on your surfaces, queued third

Seven groups, 31 conditions: `trend`, `momentum`, `meanreversion`, `volatility`, `regime`,
`multitimeframe`, `candlestick`. R1's vocabulary is fixed as the shared one — **PROXY / DEGRADED /
HONEST-DERIVED / HONEST-DERIVED-BUT-BROKEN**. **Queued behind `MGR-T13`** (R1's volume-norm question),
because `volatility` and `regime` both read volume against a window and an auditor who does not know
which of the repo's two norms a condition uses cannot classify it. **Do not re-derive the known
aliases** — `X-9` holds `mtf_not_conflicted`≡PULLBACK, `regime_trending`≡TREND,
`regime_ranging`≡MEAN_REVERSION and `volatility_compressed`≡BREAKOUT, four of your 31.

**One note on my own pre-registration for this task, so you can refute it too:** I predict **≤8 of the
47 remaining conditions land on PROXY**, on the reasoning that R1 audited the groups whose *names*
promise participant information and yours mostly name arithmetic they actually do. **Falsified by ≥15
PROXY verdicts.** `manager/BOARD.md` §7 item 2.
