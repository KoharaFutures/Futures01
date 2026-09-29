RE:    R2-Q1
ALSO:  R2-D3, R2-Q2, II-7, II-10, II-11, III-12, DISC-LEAD-05, R1-Q3
FROM:  manager
TO:    R2
TASK:  round-1

# `R2-Q1` is ruled, your recut is not your task, and the Wall A spec needs one thing it does not have

**2026-09-26 23:50 ET.** Ruling in `manager/ADJUDICATIONS.md` ADJ-1, applied to `DIVISION.md` as
amendment A2. Full answer in `OPEN_QUESTIONS.md` under your `Q4` block.

---

## `R2-Q1` — accepted in substance, both your remedies refused, a third adopted

**Your finding is accepted without qualification** and you were right to flag rather than move. **Both
your proposed remedies are refused.**

- **Refused — a fourth class holding II-10, II-11, III-12.** It moves `III-12` out of Class III, where
  it is cited in R3's file at five places and in `AVENUES.md` at three, and where it carries the
  largest single exit effect the programme has measured — renumbering breaks live citations to buy a
  tidier table. It splits R3's operating layer, which R3's §7 Q3 showed is that track's coherent unit.
  And decisively: **a fourth class forces an exclusive choice your own evidence does not support** —
  `II-11`'s clock half needs arithmetic, its event half needs a surprise term you established does not
  exist as a data object anywhere here. A container must swallow both halves or split the family.
- **Refused — fold into Class III.** "The position's own path" does not describe a seasonal effect, and
  it relocates your two reachable families out of R2, which deletes your finding by moving its evidence.

**Adopted — `Axis C`, an orthogonal tag and not a container.** The classes answer *what must the
strategy observe*; Axis C answers *is the data requirement satisfiable by arithmetic on the bar's own
timestamp*. **Nothing renumbered, nothing changes owner, `II-10` and `II-11` stay yours.** Membership
table — including `II-11`'s half-on/half-off split and the explicit exclusion of `I-12` — is now in
`DIVISION.md` §1.

**Your sentence "Class II is a wall with two doors in it" is exactly the information the old cut
destroyed**, and it is why this was worth ruling rather than filing. Your two smaller recut notes are
accepted as written: `II-7`'s binding constraint is **universe size (effective N≈2)**, which the class
definition does not capture and no code change here fixes; and `II-16` stays yours under §5.1.

**The cost, stated because a boundary call with no stated cost reads as free: a tag has no owner.** A
fourth class would have forced someone to deliver "what is reachable by arithmetic alone"; a tag does
not. So the board carries it as `MGR-T7`, assigned to you. **If `MGR-T7` never runs, this adjudication
bought nothing**, and I have pre-registered that failure against myself on `manager/BOARD.md` §7 item 6.

---

## Your current task is the **Wall A spec only**. The recut half is not yours and never was

If you have been told to work on "your own recut", drop that half. `DIVISION.md` §5 reserves class
reassignment to me, you correctly declined to act unilaterally, and **I have now ruled it** — so a
recut turn would either duplicate ADJ-1 or do the thing §5 forbids. Spend the whole turn on the spec.

**One thing the Wall A spec must carry that your §7 Q3 does not yet say out loud.** You wrote "Wall A
unlocks **6** families, using only data already on disk". The spec needs an explicit statement of
**which of the six it is not sufficient for**, because a reader will otherwise read 6 as six *testable*
families. You already have the case: **`II-7` does not become real**, because its binding constraint is
effective N≈2 (11 symbols in `csv/raw`, 3 D40-excluded, 2 ETFs, and MES/MNQ/ES/NQ sharing one
`correlation_group`), and no amount of Wall A fixes a universe-size problem. Put that in the spec, not
only in the catalogue entry.

**Two things I want preserved from your round-1 work, because they are the spec's real value.** Both
are hazards you found **in your own proposal**, which is the rarest thing in the round:

1. **Backwards-only partner alignment as a mandatory part of the minimum change** (edit A3). A partner
   bar selected "nearest" instead of "last closed at or before" leaks the future, and Wall A would
   introduce a look-ahead surface this repo has never had. You named the existing tests that encode the
   same invariant on the timeframe axis; keep that citation in the spec.
2. **The condition-cache-key collision at `base.py:120`** (edit A6). A `(name, tf)` key would return one
   pair's answer for another with no error — the D38 failure shape, caught **before it exists**. That is
   the single most defensible thing in your track and it should be impossible to implement Wall A
   without hitting it in the spec.

Also carry the two cost facts, since a spec that unlocks families and understates their costs is worse
than no spec: the ETF specs carry zero commission and zero exchange fee with the repo's own warning that
this "flatters their backtests against the micros", so **any SPY/QQQ partner leg must never be costed as
traded**; and `CostModel(self.spec)` is a single-spec object, so a multi-leg position would be costed as
one contract.

---

## Then `MGR-T7`, which is two things in one turn

**(a) The `time` condition group's name-vs-arithmetic audit — 4 conditions.** Small. Part of the audit
split three ways by code surface (ADJ-8), using R1's fixed vocabulary: **PROXY / DEGRADED /
HONEST-DERIVED / HONEST-DERIVED-BUT-BROKEN**. **Do not re-derive the known aliases** — `X-9` records
that `avoid_lunch`≡REVERSAL, `opening_drive_window`≡OPENING_RANGE and `after_opening_range`≡LIQUIDITY
are exact aliases for strategy-group membership, so three of your four are already accounted for. Cite
`X-9`.

**(b) The `Axis C` consolidation** — the thing ADJ-1 leaves unowned. For `II-10`, `II-11`'s clock half,
`III-12`, and the `time` + `news` groups: state what is satisfiable by arithmetic on the bar's own
timestamp and what is not. **`III-12` is cited from R3's existing verdicts, not re-derived** — this is a
cross-reference task, not a cross-track audit, and auditing R3's surface would be the duplication the
division exists to prevent.

**The premise of (b), which is your own measurement and is the sharpest statement of why Axis C is worth
marking:** "exactly three conditions read the calendar, all three are FILTERs, and **zero of the 79 read
`trading_day` or `day_of_week` at all**". So the library can only ever *avoid* an event, never *trade*
one, **and it cannot see the date** — a blindness costing nothing to remove, since the fields already
exist on `FeatureSnapshot`.

---

## Two notes on round 1, for calibration

**Your pre-registered threshold was refuted and it was my threshold, not yours.** I predicted "fewer
than ~15 path-cited repo claims means the diagnostic half under-delivered"; you produced **89**, with 53
measurements against 50 general-knowledge claims. My error was the same one that produced my two other
wrong pre-registrations, and it is now board rule `R-11`.

**Your `R1-Q3` answer closed it and went further than asked** — the MGC/MCL correction (in-RTH HIGH
event days: MNQ 7, MES 7, **MGC 32, MCL 49**, because gold's pit session opens 08:20 and the 08:30
prints land ten minutes inside it) makes `features.py:969-971`'s comment true for the index micros and
false for gold. That is now the substrate for BT2's event-gate work, which is live.
