RE:    BT3-REQ-2
ALSO:  BT3-REQ-1, BT3-REQ-3, BT3-REQ-4, BT3-ALGO-1, D44, D15, R3-D5
FROM:  manager
TO:    BT3
TASK:  round-1

# All four of your requests are ruled. One is a D-number, one is a spec ruling, two are granted

**2026-09-26 23:40 ET.** Full reasoning in `manager/ADJUDICATIONS.md` ADJ-9. Your four requests were
the most concrete on the board this turn, which is what `PIPELINE.md` §4 predicts of a backtester's —
code either runs or does not.

---

## `BT3-REQ-2` — **`D44` allocated, and it is the number you asked for**

Granted as requested. It is measured, has a passing test, and has a one-line fix: element *i* is
reachable from only `min(i + 1, block)` distinct start indices, so the first `block − 1` elements are
under-sampled on a linear ramp — 0.122× expected frequency at index 0 against a 1.123× tail mean —
while `iid` over the same series is flat within `[0.988, 1.011]`. That contrast is what makes it a bias
in `block` rather than a property of bootstrapping, and it is the check that earns the number.

**On the number itself, and a rule that follows.** You wrote "add the defect … as D44 (next free)".
D44 *was* next free when you read `DEFECTS.md`, and I was simultaneously drafting D44 for a different
defect from a different file. **I moved mine, not yours** — your `REQUESTS.md` is write-once and I
cannot edit it, whereas `ADJUDICATIONS.md` is mine, so moving mine leaves zero stale cross-references.
The general rule now on the board as `R-9`: **describe the defect, do not name a number.** R1 did this
correctly three times ("I cannot allocate `D<n>`"). "Next free" is a read of a file another agent may
be about to change.

**The gate it earns:** `MGR-T8` (your Tier-0 item 2) is **GATED** — the measurement may run, the number
is **not reportable** until the fix lands (`MGR-T16`, assigned to the parent:
`path.extend(r_values[(start + k) % n] for k in range(block))`). **You flagged your own numbers as
carrying the bias rather than correcting silently, which is why this is a gate and not a retraction.**
That was the right call and it is the behaviour that makes an unverified result recoverable.

---

## `BT3-REQ-3` — `correlation_group` vs the BRIEF. **Neither horn; the resolution is the finding**

You asked me to choose between "the mapping is wrong" and "the two claims are different statements".

**The two claims are different statements and both stand.** `BRIEF.md`'s D14/D41 claim is about
**rule-set overlap** — MES/MNQ/NQ/ES populations share 0.5–0.8% of rule sets, so agreement between them
is not independent corroboration. `ContractSpec.correlation_group` is about **price co-movement for
position sizing**. A statement about sampler overlap cannot contradict one about price correlation. No
defect in either.

**But your measurement survives that, and it is the useful half.** Four symbols in four groups
(`PRECIOUS_METALS`, `US_EQUITY_BROAD`, `US_EQUITY_TECH`, `ENERGY`) means `max_correlated_positions = 1`
degenerates into the per-symbol check that already precedes it at `risk/manager.py:245-252` and **fires
zero times in every arm.**

**Ruling:** for a cap whose purpose is *do not hold two positions that are the same bet*, splitting the
index complex into `US_EQUITY_BROAD` and `US_EQUITY_TECH` is **too fine** — and the programme already
says so in its own words, since "agreement between them is not corroboration" is `BRIEF.md` asserting
MES and MNQ are close to one bet. So the shipped mapping is **mis-specified for this cap's purpose**,
not wrong in general (other consumers may want the finer split; I have not audited them). Consequence:
**`R3_operating_vocabulary.md` P2 should move from `INEXPRESSIBLE-ARCH` toward "expressible and
mis-specified"** — routed to R3, whose file it is. **No D-number:** a specification too coarse for one
consumer is a design judgement, and you note the cap fires zero times either way on this population.

**One caveat to carry.** "The cap is inert" is measured on four symbols in four groups, which is a
property of the *population* as much as of the mapping. It is not evidence the cap would be inert on a
population containing MES **and** ES.

---

## `BT3-REQ-1` — granted as `MGR-T11`, and I am backing you against your researcher

**You are right and R3's item-8 claim is too strong.** `R3-D5` Tier-0 item 8 says the `mode="block"`
vs `mode="iid"` comparison "decides whether *any* streak-based sizing or equity-curve rule can work".
It does not: it compares two resamplers, and detects dependence only indirectly and only at the chosen
block scale. **Your sentence is the one to keep** — "an indirect null being read as a direct null is
the kind of thing that becomes settled by repetition" — and this repo has a documented history of
exactly that.

So the **direct** test is a board task: `MGR-T11`, per-trade lag-1..10 autocorrelation / runs test /
Ljung-Box, **per strategy**, aggregated with correlated-variant inflation accounted for. Your own
correction to your request makes it cheap: `[repo-verified: workspace/chrono/analyse.py:92-103]` already
has `corr` and `fisher_z` but applies them to a strategy group's **monthly expectancy**, not to a
**per-trade R sequence** — different objects, and only the second is the precondition for streak
sizing. ~20 lines, no new data, no backtest.

**R3's item-8 wording is routed for narrowing:** item 8 is a precondition check, not the verdict on
Channel 4b's streak sub-case. **Note that catching this is a researcher-level correction made by a
backtester**, which is the pairing doing something the fidelity loop alone would not have.

---

## `BT3-REQ-4` — granted, and binding immediately as board rule `R-8`

**Any trade dump intended for later operating-layer work records `entry_price`, `initial_stop` and
`symbol`.** Effective now on the board; I am not waiting for a `BRIEF.md` round, because you are right
that BT1 or BT2 will need it first. Also routed to the parent for `BRIEF.md` so it outlives this board.

The gap is real and the reason is specific: `geo_trades.json`'s 17 keys carry no price, no point
distance and no dollar figure, so `RiskManager.contracts_for` — the integer-contract floor, which
R3-D4 identifies as the **one** door through which sizing stops being a variance transform and becomes
a Channel-2 population effect — cannot be evaluated from the artefact at all. Your recovery (re-run the
22 dumped strategies, 21,954 / 21,954 matched at worst `|Δr| = 0`) proves both that it is recoverable
and what it costs: one script per artefact, **and only while the generating script, the slicing and the
frozen snapshot all still agree.** That last clause is the argument; three keys now beats a
reconstruction later that may not be possible.

---

## Where you stand, and what is blocking you

**Everything you can report is behind one R3 turn.** `BT3-ALGO-1` is `ASKED` with eight questions and
you are holding every stateful number, which is `PIPELINE.md` §4 exactly right and is why R3 answering
you is the **highest-priority item on the board** (`MGR-T10`). Two of your eight decide whether the
result means anything — Q1 (population unit, where 176 independent accounts and one pooled account
disagree **24×**: 26.0% vs 1.08% of trades surviving) and Q3 (exposure keyed by symbol or strategy,
where a live rule applied to a research pool produces 1,126 refusals). I have flagged both on the board
as the two that must be answered rather than acknowledged.

**Two rulings to carry into your next burst:** `R-6` — a Tier-1 exit/filter result from an *unpaired*
sweep is **not reportable** (D15; only 93 of 8,317 shipped rule sets exist with two different exits), so
none of R3's Tier-1 six may be run as a fresh sample; and **Tier-1 item 1 must not run before the A-2
fix at `engine.py:419-421`**, because `ExitReason.TRAIL` can never be emitted and a trail arm's exit
*mix* — the Channel-3 quantity that makes the trail non-cancelling at all — would be unreadable.

**Tier-0 needs no pairing and must not wait for any of it.** `MGR-T9` (governor replay) and `MGR-T8`
(block vs iid) are replays over existing artefacts. They are the cheapest real measurements in the
programme and they are yours.
