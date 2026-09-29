# R2 — what changes in my catalogue if the R2-Q1 recut is accepted, and if it is not

**Owner:** researcher R2. **Opened:** 2026-09-27 (round 2).
**About:** **R2-Q1** per `REGISTRY.md` — *"Class II is mis-cut: II-10 and II-11 need no second
observable"*, raised in round 1 as OPEN_QUESTIONS Q4 and argued in
`research/R2_relational.md` §"Was Class II mis-cut?".

The manager is adjudicating R2-Q1 in parallel with this round. **I am not waiting on it and I am not
touching `DIVISION.md`, which is the manager's file** (`OWNERSHIP.md`). What I can do, and what this
file is, is record the consequence for my own catalogue **both ways in advance**, so whichever way
the ruling lands nobody has to reconstruct it.

The recut I proposed, in preference order (`R2_relational.md`): **(1)** a fourth axis, *"the clock"*,
holding II-10 (seasonality), II-11 (scheduled events) and R3's III-12 (time-based exits), unified by
*conditioning on the calendar rather than on the tape*; **(2)** failing that, fold II-10 and II-11
into Class III.

---

## 0. What does NOT change under any ruling — stated first, because it is most of the round

Every substantive round-1 result is a property of **code on disk** or **data on disk**, and taxonomy
cannot move either. If the manager accepts the recut, rejects it, or invents a third option, all of
the following stand verbatim:

| finding | why taxonomy cannot touch it |
|---|---|
| **Two walls, not one** (Wall A additive/8 edits, Wall B structural) | a statement about `features.py:686`, `base.py:87`, `base.py:552`, `engine.py:159,233` |
| **Wall A unlocks 6 families from on-disk data, 9 after one vendor fetch** | a count over families whose *class label* may change but whose *blocker* does not |
| **Wall B's real yield is 3, not 5** (II-1 and II-2 need a second expiry Wall B does not provide) | a data-availability fact |
| **The A6 cache-key collision and the §9.2 `strategy_id` collision** | defects in `base.py:121` and `base.py:613` |
| **R2-D4's seasonality power arithmetic** — n = 24 (CL) / 15 (MGC) / 6 (MES,MNQ) / 0 (MCL); d = 1.11-2.23 at `free_t = 5.46`; only day-of-week is powered | counts of years in files |
| **R2-D5's event census** — distinct in-RTH HIGH event days: MNQ **7**, MES **7**, MGC **32**, MCL **49**, MGC_1d **358**, each against that contract's own `ContractSpec` RTH | counts of calendar events against bar spans |
| **`post_news_window`'s F11 result (112.6 → 1.5 trades, zero publishable) was measured on MNQ, where the in-session sample is 7 days** | a fact about which symbol a published report used |
| **II-7's binding constraint is universe size (effective N≈2), not "needs a second observable"** | this is a *separate* mis-description and is independent of the clock recut; it stands either way |
| **The alignment measurements** — `MGC_1d`×`SPY_1d` 2,507; `MES_1d`×`SPY_1d` 1,855; `MES_1h`×`SPY_1h` 1,805 of 5,000 | timestamp intersections |

**So R2-Q1 is a presentation-and-ownership question, not a research one.** That is worth saying
plainly to the manager: the cost of getting it wrong is that a reader draws the wrong conclusion from
a correct table, which is real but bounded, and no measurement has to be redone either way.

---

## 1. If the recut is ACCEPTED (option 1 — a fourth axis, "the clock")

### 1.1 The arithmetic

Round 1's tally over **19** Class II families
(`R2_expressibility_wall.md` §5, "Count"): 6 valid proxy on disk (all needing Wall A) + 2 needing no
second series (II-10, II-11) + 3 after a zero-code vendor fetch + 8 with no valid proxy at any price
= 19. Moving II-10 and II-11 out leaves:

| | before | after |
|---|---|---|
| Class II families | 19 | **17** |
| expressible **today**, in part | 2 | **0** |
| valid proxy on disk, needing Wall A | 6 | 6 |
| proxy-able after a vendor fetch | 3 | 3 |
| no valid proxy at any price | 8 | 8 |
| new Class IV ("the clock") | — | **2 from R2** (II-10, II-11) + R3's III-12, if R3 concurs |

### 1.2 The consequence I did not anticipate in round 1, and it is the interesting one

**After the recut, "Class II is a wall" becomes literally true** — 17 of 17 blocked, zero expressible
today. That is the sentence I spent round 1 arguing was misleading.

It is not a contradiction; it is the recut working. My objection was never that the sentence was
false about the *code*, it was that the two reachable families were **filed behind** seventeen
blocked ones, so a reader who scanned the table concluded that calendar conditioning was unreachable
too. Reclassifying them removes them from the table rather than hiding them in it. **The claim
"Class II is a wall with two doors in it" is replaced by "Class II is a wall, and the two doors were
never Class II's."** Both describe the same repository; the second is the one a reader cannot
misread.

I record this because it is the strongest argument *for* the recut and I did not make it in round 1.

### 1.3 The renumbering hazard, and the precedent that resolves it

If accepted, the obvious next step is to rename II-10 → `IV-1` and II-11 → `IV-2`. **Do not.**
`[measured: grep -c "II-10\|II-11" research/R2_relational.md research/R2_expressibility_wall.md →
19 and 3 matching lines]`, plus citations in BT2's live code:
`[repo-verified: workspace/roundtable/backtest/BT2/code/event_gate.py:5-6]` *"R2-D1 II-11 records
that the library's whole event vocabulary is three FILTER conditions"* and the same id again in its
gate docstrings. Renumbering breaks a reference inside code that is running right now.

**`REGISTRY.md` has already set the precedent and it should be followed here:** it declined to
renumber `OPEN_QUESTIONS.md` because *"renumbering would break every citation already written into
five research files"*, and instead published a canonical mapping. So:

> **Recommendation if accepted: keep `II-10` and `II-11` as stable identifiers and make the class a
> recorded attribute of the family, not a component of its id.** A one-row mapping in `REGISTRY.md`
> ("`II-10` and `II-11` are Class IV families; the `II-` prefix is historical, as with the `Q`
> numbers") costs one line and breaks nothing. `R2-Q1` asked whether the *cut* is wrong; it did not
> ask for new numbers, and the numbers are the part with 22 matching lines in my files alone, plus BT2's running code.

### 1.4 The ownership consequence, which matters more than the arithmetic

**BT2 is, right now, implementing II-11.** Its code reads *"ALGO-1 runner: the scheduled-event gate
on the contracts whose own session"* `[repo-verified:
workspace/roundtable/backtest/BT2/code/algo1.py:1]` and it cites II-11 by id. If II-11 becomes a
Class IV family, then under `PIPELINE.md` §4's pairing (BT2 ↔ R2) a backtester paired to R2 is
implementing a finding that no longer sits in R2's class.

**My position: the pairing must not move, and the recut must not be allowed to imply it does.**
`PIPELINE.md` §4 pairs a backtester to a *researcher*, not to a class — *"a backtester's questions go
to its own researcher"*. II-11 is **my** finding regardless of which class it is filed under, the
32/49 event-day census is mine, and BT2's fidelity questions about it are mine to answer. If the
recut created a new track owning Class IV, the correct disposition is that the *finding* stays with
its author and only the *catalogue heading* moves. Anything else interrupts a burst that is already
in flight to settle a taxonomy question, which is the wrong trade by a wide margin.

### 1.5 What I would then owe

- One paragraph at the head of `R2_relational.md`'s catalogue noting that II-10/II-11 are Class IV
  and why the ids are unchanged. Small.
- Nothing else. R3's III-12 is R3's to restate; I do not touch their arithmetic.

---

## 2. If option 2 is chosen instead (fold II-10 and II-11 into Class III)

Same arithmetic as §1.1 — Class II goes to 17, zero expressible today — with two differences, both
worse:

1. **It transfers authorship, not just a heading.** Class III is R3's track. Folding II-10 and II-11
   into it means two families whose research I did (R2-D4's power arithmetic, R2-D5's event census)
   sit in someone else's class. The cheap fix is explicit: the findings stay in `research/R2_*.md`,
   R3's catalogue cross-references them, and neither of us re-derives the other's numbers. Without
   that written down it is a duplication risk, which `AVENUES.md`'s whole design exists to prevent.
2. **It loses the insight the fourth axis carries.** Class I is below the bar, Class II beside the
   series, Class III along the path — and calendar conditioning is orthogonal to the bar entirely. It
   is also the only class whose data requirement is satisfiable by **arithmetic** rather than by
   acquisition, which is a real and decision-relevant distinction: it names the one place in this
   repository where "we lack the data" is not the answer. Folding into Class III makes that
   invisible, which is the same failure as the original mis-cut in a different direction.

I still prefer option 1 and this is why, but option 2 is not wrong and it is cheaper for the manager.
**Either is better than no ruling**, because the status quo is the one arrangement where a correct
table reads as a false conclusion.

---

## 3. If the recut is REJECTED (II-10 and II-11 stay in Class II)

**Nothing in my catalogue changes numerically, and I accept the ruling without reservation** — this
is a taxonomy call and the manager owns the taxonomy. One thing then becomes my responsibility
instead of the manager's, and I state it so the rejection is not a silent loss:

> **The catalogue must lead with the exception.** `R2_relational.md`'s R2-D1 opens on the measurement
> that no condition reads `trading_day` or `day_of_week` and that only three FILTERs touch the
> calendar. A reader who takes the tally at face value — 17 of 19 inexpressible — will not notice
> that the 2 are reachable **today, with no code change for one of them and ~10 lines for the
> other**. Under a rejection I would add a single sentence at the head of the catalogue:
> *"Two of the nineteen (II-10, II-11) need no second observable; they are Class II by filing, not by
> blocker."*

That is the whole remedy, and it costs one line. Which is itself an argument the manager may find
useful: **if a one-line caveat fixes the reader's problem, the recut is a nice-to-have and rejecting
it is cheap.** I would rather say that than overstate my own question.

---

## 4. The one thing I would ask the manager to rule on regardless of which way R2-Q1 goes

Not a new question — a clarification of the same one, and it is the part that has an operational
consequence today rather than a presentational one:

**Does "needs no second observable" make a family *expressible*, or only *unblocked*?** II-10 and
II-11 need no second series, but:

- II-10's only powered sub-family (day-of-week) is expressible **today** and has *never been
  generated*: `StrategyFilters.days_of_week` exists `[repo-verified:
  futures_agents/strategies/base.py:392, gated at :421]` and
  `[measured: grep -rn "days_of_week" --include=*.py . | grep -v __pycache__ → 12 hits, zero in
  combinator.py, zero in any generator]`.
- II-11 is expressible only as *avoidance*: `[measured: the three calendar-reading conditions
  (`no_imminent_release`, `post_news_window`, `outside_news_blackout`) are all
  `ConditionKind.FILTER`]` — the library can decline to trade an event and can never trade one.
  BT2's ALGO-1 keeps that limitation honestly and says so
  `[repo-verified: workspace/roundtable/backtest/BT2/code/event_gate.py:3-8]`.

So both are "unblocked and not exercised", which is a third state the class scheme has no word for
and which is *more actionable* than either "expressible" or "inexpressible": it names work that could
be done this week with no new primitive and no new data. Whatever R2-Q1's ruling, having a label for
that state is worth more to the programme than the class boundary is.

---

# 5. The actual ruling: `ADJ-1`, and it is a fourth option I did not anticipate

**Appended after the manager ruled**, while this round was still running.
`[repo-verified: workspace/roundtable/msgs/05_manager_all_round2-board.md:27]`:

> **ADJ-1 `R2-Q1`** — Accepted in substance. **Fourth class refused**; "the clock" becomes **`Axis C`**,
> an orthogonal tag. Nothing renumbered, nothing changes owner. `II-11` is half-on (clock) and half-off
> (surprise term). `I-12` is **not** on it.

This is neither §1 (accept a fourth class), nor §2 (fold into Class III), nor §3 (reject). It accepts
the *insight* — that calendar conditioning is a distinct observable — and refuses the *container*. The
substance is granted and the taxonomy is left alone.

**I accept it without reservation, and it is better than what I proposed.** My own §0 argued that
R2-Q1 is a presentation-and-ownership question rather than a research one, and a tag is the minimum
instrument that fixes presentation while leaving ownership untouched. A fourth class would have
created a container with two occupants and an owner question; a tag creates neither.

## 5.1 What the ruling costs my catalogue: nothing

- **Nothing renumbered.** §1.3's recommendation — keep `II-10` and `II-11` as stable identifiers,
  following `REGISTRY.md`'s precedent of declining to renumber `OPEN_QUESTIONS.md` — is what the
  ruling does. All 22 matching lines in my two round-1 files, and BT2's running code that cites
  `II-11` by id `[repo-verified: workspace/roundtable/backtest/BT2/code/event_gate.py:5-6]`, keep
  resolving.
- **Nothing changes owner.** §1.4's concern — that a fourth class would put BT2 mid-burst under a
  heading its paired researcher does not own — is answered directly by "nothing changes owner". The
  BT2 ↔ R2 pairing is undisturbed and ALGO-1 proceeded without interruption; its verdict is
  `msgs/06_R2_BT2_re-verify-ALGO-1.md` (**FAITHFUL**).
- **The arithmetic of §1.1 does not apply**, because Class II is not re-cut. Class II remains **19**
  families: 6 with a valid on-disk proxy needing Wall A, 2 needing no second series, 3 after a
  zero-code vendor fetch, 8 with no valid proxy at any price. Every count published in round 1 stands
  as written.
- **§3's remedy is the one that is owed**, since the container was refused: the catalogue must lead
  with the exception rather than bury it. Two of the nineteen are Class II by filing and not by
  blocker, and `Axis C` is now the tag that says so.

## 5.2 The one place the ruling is sharper than my question was, and it is a correction to me

> *"`II-11` is half-on (clock) and half-off (surprise term)."*

**This is a better cut than mine and I did not make it.** I argued II-11 needs no second observable
because `_build_news_proximity` is built from recurrence **rules**
`[repo-verified: futures_agents/features.py:946-1003]`. True of the **timing**. Not true of the
**surprise** — actual-versus-expected — which is a second observable this repository does not have in
any form.

I had in fact already reasoned exactly this way one family over and failed to carry it back:
`R2_relational.md` II-13 (inventory/fundamental) records *"No EIA/WASDE number, only the timing of the
release"*, and rejects using the post-release price move as the surprise because that is conditioning
on the outcome. **II-11's surprise term has the identical structure and the identical circular
temptation**, and my II-11 entry did not say so. The ruling's split says it in five words.

Consequence for what is buildable, and it is not cosmetic: **the arm of II-11 that is on `Axis C` is
the only arm that is expressible.** A gate keyed on *when* a print happens needs arithmetic; a
strategy keyed on *how surprising* it was needs a consensus number, and the tempting substitute is the
price reaction, which is the outcome. This is exactly the line BT2's ALGO-1 sits on — it gates on
timing only `[repo-verified: workspace/roundtable/backtest/BT2/code/event_gate.py:3-8, three FILTERs
and no SIGNAL]` — so the ruling retroactively explains why the implementable version of this family is
a permission and never a thesis.

## 5.3 What I am recording as a consequence for Class II's other entries

The clock/surprise split generalises, and applying it is cheap, so: **the same two-part test should be
run over every Class II family that involves an announcement.** Preliminary, from the catalogue as it
stands and offered rather than asserted:

| family | clock half (`Axis C`, arithmetic) | second-observable half (blocked) |
|---|---|---|
| **II-11** scheduled events | the release timetable — expressible today | the **surprise**: actual vs consensus. No consensus series exists |
| **II-13** inventory / fundamental | release timing only | the **number** (EIA stocks, WASDE). Already recorded as no-valid-proxy, with the circular temptation named |
| **II-10** seasonality | the calendar date — expressible today | nothing. **Fully on `Axis C`**, which is why it is the cleaner of the two |
| **II-1 / II-2** calendar spread, carry | roll and expiry *dates* are rule-derivable | the second **expiry's price**. Unobservable, and the dates without it are a flag for an event the data cannot show — already recorded in R2-D5's absent-movers table |

**So `Axis C` fully contains exactly one of my nineteen families (II-10) and partially contains three
(II-11, II-13, and the date half of II-1/II-2).** That is a more precise statement than R2-Q1's
original "II-10 and II-11", and it is the version I would now defend. It also does not require any
further ruling: the tag is orthogonal, so partial membership is expressible in it by construction,
which a class would not have been.
