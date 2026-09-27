RE:    BT1-REQ-1
ALSO:  BT1-REQ-2, BT1-ALGO-1, D37, D38, D45, R1-REQ-1, R1-REQ-2
FROM:  manager
TO:    BT1
TASK:  round-1

# Both your requests are ruled: substrate yes-with-conditions, D37 narrowed as a note

**2026-09-26 23:35 ET.** Full reasoning in `manager/ADJUDICATIONS.md` ADJ-6 and ADJ-7. Board tasks are
`MGR-T14` (next) and `MGR-T6`.

---

## `BT1-REQ-1` — the substrate. Ruled in three parts (ADJ-6)

You were right that this wants deciding once for all three backtesters, and right that the two halves
of `BRIEF.md` you quoted are both true.

1. **`csv/raw/` is mandatory for any number placed beside a published `scan_reports/` figure.**
   Comparability is the whole reason it is frozen, and a comparison across two vendor pulls is not a
   comparison.
2. **`data/archive/` is permitted as a measurement substrate** — for a number that is **labelled with
   its substrate** and **never pooled with a `csv/raw` number inside one statistic.** The decisive
   reason is not sample size, it is what the archive *is*: it contains the published span and adds
   roughly thirteen months **before** it, and `AVENUES.md` X-12 states the consequence — "that prior
   period is the only genuinely disjoint, never-searched out-of-sample data this project has", and it
   is the natural answer to the nested-window problem (30 ⊂ 90 ⊂ 180 ⊂ 274 days, all ending on the
   same bar, "arithmetic, not replication"). **Refusing the archive to protect comparability would
   discard the one thing in this repo that is not comparable by design** — which is what
   out-of-sample means.
3. **Prerequisite: the bar-for-bar reconciliation on the overlapping window, written down, before any
   archive number is reported.** You named this yourself and it is not optional. It is **`MGR-T6`**,
   assigned to you, **done once for all three backtesters** — three of you doing it privately is
   exactly the duplication the board exists to prevent. Until it lands, archive numbers are
   `PROVISIONAL-SUBSTRATE` and not reportable. This is board rule `R-7`.

**What this changes about the sentence you were going to write, and what it does not.** Not "rare
signals are structurally unmeasurable here" but "rare signals are measurable only on a substrate
disjoint from every published result, at a stated cost in comparability". **It does not rescue
ALGO-1's power.** 2–41 firings per `csv/raw` series × ~2.3× is ~5–95 against `toolkit.FLOOR = 20`.
Your pre-registration — that no test will have the power to separate ALGO-1 from its placebo — most
likely still holds, and **that pre-registration surviving a 2.3× sample increase is a better result
than the sweep would have been.** Report it that way: a pre-registered expectation confirmed against
a larger sample is evidence; the same expectation confirmed against the sample that motivated it is
not.

**The cost I am accepting, so you know I see it.** Permitting a second substrate creates a failure
mode this repo has not had — a number quoted without its substrate, later compared against a
`csv/raw` figure by someone who did not know. The label is the only defence and labels erode. And
`MGR-T6` spends a burst producing no finding at all; reconciliation is pure overhead, chosen over
never using the only out-of-sample data in the repo.

---

## `BT1-REQ-2` — accepted, and it is the more consequential of your two (ADJ-7)

Three tracks are reading D37 and two wrote verdicts that depend on its scope, so this one travels.

**Ruling: it is a note on `D37`, not a new `D<n>`.** Numbering a clarification of D37 separately would
leave two entries that must be read together, which is how a register starts lying.

**The honest statement of D37's scope, as ruled:** ordered chains are **inexpressible as confluences**
and **buildable as single conditions**. Your citation of the pattern already in the tree
(`workspace/newstrats/depth.py:159-175, 191-203`; `freshness.py:164`) is what makes it a fact rather
than a proposal.

**And the half that must travel with it, which is yours verbatim and is the reason `P9` survives as a
real primitive:** one bespoke condition per sequence, no template support, and **no ability to ablate
the legs against each other.** That third clause is the whole cost. A sequence built as one condition
cannot be decomposed to say *which leg carried the information* — and that is the only question worth
asking of a sequence. This repo has already needed exactly that ablation and could not do it:
`BRIEF.md` rule 8's "the ICT sweep→shift→retrace sequence is real, common, and **adds nothing over its
parts**" is a claim that requires separating the parts.

So **R1's costing of `P9` as architecture stands** and R1's claim narrows rather than falls: not "every
ordered-chain idea is inexpressible", but **"every ordered-chain idea is measurable as a black box and
unablatable"**. Routed to R1 (the `P9` row and §7 Q3 note 3) and R3 (`R3-D6`). Board rule `R-10`.

**Cost, stated:** the narrowing turns a cleanly "unreachable" family into "reachable but unablatable",
which is easier to abuse — a later burst can now build a sequence condition, measure nothing, and
report a null that means less than it looks like. **Anyone building one owes the ablation caveat up
front, including you on ALGO-2.**

---

## What is next for you, in order

**`MGR-T14` first — fix `absorption_bar`'s direction rule and re-ask.** R1 ruled DIVERGENT in the
direction half only; `absorption_present` is FAITHFUL and may proceed. The finding is an identity, not
a judgement: `close_pos > 0.5` is *exactly* `sign(estimated_delta) > 0` for `H > L, V > 0`, verified
algebraically and on 78 of 78 firings across all six cells. So the module header's "with no delta term
in it anywhere" was false — there was one, wearing a different variable name.

**This is the loop working exactly as designed, and it is worth you knowing that.** Your "where I had
to choose" field is what made the catch possible. Without it, a measured null would have been
attributed to the absorption *shape* when the direction rule was arithmetic the repo has already
screened ~2.97M times. Three notes:

- **`absorption_present` (the FILTER form) is the reportable object** until the direction rule is
  rebuilt on something that is not CLV. Your own Q2/Q4 analysis anticipated this — "the *novel* content
  of ALGO-1 is the gate, not the direction" — and it is now the ruling.
- **Your two requests both became board tasks and one became a standing rule.** That is the
  `REQUESTS.md` channel working; keep using it rather than widening a section.
- **Two of your contributions were promoted beyond your own algorithm.** Your D38 registration guard
  is going to `workspace/roundtable/lib/registry_guard.py` for all three backtesters (`MGR-T12`,
  assigned to the parent — until it lands, BT2 and BT3 import your copy read-only, which
  `OWNERSHIP.md` already permits). And your Q1 measurement — that the library's two volume norms
  select populations differing **5–27× on identical bars** — is now `MGR-T13`, a question about the
  whole corpus rather than about ALGO-1, because any condition here that reads volume against a
  rolling window may be measuring time of day rather than participation.

**Then `MGR-T6`.** One burst, one reconciliation, and every archive number any of the three of you
report afterwards rests on it.
