# ADJUDICATIONS — the manager's rulings

**Owner:** manager (`OWNERSHIP.md`). Append-only, newest at the bottom. One block per ruling.
**Opened:** 2026-09-26 22:11 ET, round 2.

Every ruling states **the decision** and **what the decision costs**, because a boundary call with
no stated cost reads as free and gets cited as if it were. Ids are canonical per `REGISTRY.md`;
a bare `Q2` appears nowhere in this file.

---

## ADJ-0 — The pattern first: two of three tracks found the classes mis-cut, and it is one cause

**2026-09-26 22:11 ET.** R2-Q1 and discovery's I-12 note are not two boundary disputes. They are
one defect in `DIVISION.md` §1, and I am naming it before ruling on either, because the rulings
only make sense against it.

**§1 was written to do two jobs at once: it is a mechanism taxonomy *and* it was used as the
routing table.** "Class I → Track R1" made the class answer two different questions — *what must
this strategy observe?* and *who audits it?* Those questions have different right answers, and
where they disagree the taxonomy silently assigns the disagreement to nobody:

- **II-10 / II-11** observe only the timestamp on the bar, so the mechanism answer is "not Class
  II". But the *calendar* is R2's code surface (§5.2), so the routing answer is "R2". Filed under
  Class II, the two reachable families sit behind seventeen blocked ones and the class reads as a
  wall — R2's phrase, "a wall with two doors in it", is exactly the information the cut destroyed.
- **I-12** has an expressibility question that is Class I's (R1 answered it:
  INEXPRESSIBLE-ARCHITECTURE, nine layers, `R1_flow_auction.md:1098-1135`) and a *confound*
  question that is about Class III's settled findings — ATR-denominated stop geometry, the
  win-rate/payoff cancellation, the sub-hourly verdict. The second question had no owner in any
  class, which is what discovery is actually reporting.

**Ruling.** `DIVISION.md` §1 is from this point a **mechanism taxonomy only, and is not a routing
table.** Ownership is carried by `manager/BOARD.md`, per `PIPELINE.md` §2. This is not a new
policy invented to escape the two disputes — it is what the pipeline already does, and round 1's
mis-cuts are the evidence that §1 was still being read the old way. §1 gets an amendment saying so.

**What it costs.** The 53 family ids stay as they are, so no citation in five research files
breaks — but the merged catalogue no longer has a single label that tells a reader who to ask.
Anyone wanting the owner of a family must consult the board rather than the class. That is a real
loss of convenience and I am accepting it, because the alternative cost — a taxonomy that hides
reachable families behind unreachable ones — was paid twice in round 1 and was invisible until
two researchers went looking.

---

## ADJ-1 — R2-Q1: Class II is mis-cut at II-10 and II-11. Accepted in substance; the fourth class is refused

**2026-09-26 22:11 ET. Ruling on `R2-Q1`** (`OPEN_QUESTIONS.md`, written as `Q4`).

**The finding is accepted without qualification.** II-10 (seasonality) and II-11 (scheduled
events) fail §1's own Class II test — "it needs something other than this contract's own price
path" — because both read only the timestamp already on the bar. R2's citations hold:
`StrategyFilters.days_of_week` at `base.py:392` fed by `FeatureSnapshot.day_of_week` at
`features.py:697`, extended by `snap.trading_day.month` at `features.py:702`; and
`_build_news_proximity` at `features.py:946-1003` projecting from recurrence *rules* precisely so
that no external observable is needed (`econ_calendar.py:8-10` argues that explicitly).

**R2 offered two remedies. I am taking neither, and adopting a third.**

*Refused — option (b), a fourth class holding II-10, II-11, III-12.* Three costs, and the third
is decisive:
1. It moves III-12 out of Class III. III-12 is cited in `R3_path_operation.md` (A-7, A-10, B-5,
   the D4 axis table, Tier-1 items 3 and 4), in `AVENUES.md:185` and `:281` and `:335`, and it
   carries the largest single exit effect the programme has measured. Renumbering it breaks live
   citations to buy a tidier table.
2. It splits R3's operating layer, which R3's own §7 Q3 demonstrated is the coherent unit of that
   track — 62 operating axes, of which the `account: AccountState` primitive unlocks 17. A class
   that removes one row from that block makes the block harder to reason about, not easier.
3. **A fourth *class* forces an exclusive choice the evidence does not support.** II-11 has two
   halves with different data requirements: the **clock** half needs arithmetic on a timestamp,
   and the **event** half needs a surprise term that R2 established does not exist as a data
   object anywhere in this repo. A container class must swallow both halves or split the family.
   Neither is honest.

*Refused — option (a), fold II-10 and II-11 into Class III.* Cheaper, and wrong in the same
direction: "the position's own path" does not describe a seasonal effect, which is not about a
position at all. It also relocates R2's two reachable families out of R2, which deletes R2's
finding by moving the evidence for it.

**Adopted: "the clock" becomes an orthogonal axis, not a container.** Named **Axis C**. The three
classes answer *what must the strategy observe*. Axis C answers a different question that
cross-cuts all three: **is the data requirement satisfiable by arithmetic on the bar's own
timestamp?** A family carries a class and, if it qualifies, the Axis-C tag as well. Nothing is
renumbered and nothing changes owner.

**Axis C membership, as ruled:**

| member | class it keeps | owner it keeps | which half qualifies |
|---|---|---|---|
| II-10 seasonality | II | R2 | all of it except expiry-week and roll-window (blocked on a second expiry) |
| II-11 scheduled events | II | R2 | the **clock** half only. The event/surprise half is not on Axis C and is not satisfiable by arithmetic |
| III-12 time-based exits | III | R3 | time stops, session-close and week-end flattening, hold-period targeting |
| `time` condition group (4, all FILTER) | — | R2 (via `MGR-T7`) | the library's existing Axis-C surface |
| `news` condition group (3, all FILTER) | — | R1 audited; R2 holds the calendar | R1 established it is structurally a `time` group: the only quantity read is minutes to/since a projected timestamp |

**And one exclusion, ruled explicitly because it is the near miss that would otherwise be
assumed in:** **I-12's volume/dollar/range schemes are NOT on Axis C.** A volume-bar boundary is
a statement about cumulative volume inside a minute, not about the minute's timestamp. See ADJ-2.

**What this ruling costs, and it is a real cost.** An orthogonal tag has **no owner**. Where a
fourth class would have forced someone to answer "what is reachable by arithmetic alone" as a
deliverable, a tag does not. So the ruling is only honest if the board carries the consolidation
as a task — it does, as **`MGR-T7`**, assigned to R2, which cites R3's existing III-12 verdicts
rather than re-deriving them. If `MGR-T7` never runs, this adjudication bought nothing and the
cost was the turn I spent on it.

---

## ADJ-2 — Discovery's I-12 split: refused on its premise, and its diagnosis accepted by another route

**2026-09-26 22:11 ET. Ruling on discovery's report that `DIVISION.md` §1 files all of `I-12`
under Class I though three of its six schemes need no sub-bar data** (`MAIN_TASKS.md` §"Why it
plausibly matters *here*" point 4; `AVENUES.md:86`, `:345-393`).

**The premise is refuted and discovery has already conceded it.** The proposal rests on "volume,
dollar and range bars need only `(high, low, close, volume)` per minute, which this repo has".
R1 answered that time-and-sales is required for tick/volume/dollar/imbalance/run bars and that
range bars alone are approximable from 1-minute OHLCV — "and the approximation is **poor**,
because the intrabar path is unknown and a range bar boundary is a path statement"
`[repo-verified: research/R1_flow_auction.md:1113-1116]`. Discovery's own addendum accepts this:
"R1 is right about the mechanism and my phrasing was too strong"
`[repo-verified: discovery/AVENUES.md:365-380; discovery/MAIN_TASKS.md, MAIN-01 amendment §2]`.

So a split filed on the ground that three schemes "need no sub-bar data" would **encode a claim
that has already been withdrawn.** What is constructible here is a minute-snapped approximation
to a volume or dollar bar, not a volume or dollar bar. Refused.

**Ruling:** `I-12` stays **one family, one id, in Class I, with R1's expressibility verdict
standing as delivered.** No split, no new id, no reassignment.

**But discovery's diagnosis is accepted, restated correctly, because the corrected version is
sharper than the one it filed.** The claim "the class boundary is why nobody looked" is false as
to the *family*: R1 did look, wrote a full §4 entry, and converged with discovery on both the
verdict and the missing primitive within the same hour, from the other side of the map. The claim
is true as to the *question*: whether the wall-clock sampling choice is a confound in findings
this repo treats as settled had no owner in any class, because it is a Class-III question reachable
only from a Class-I row. That is ADJ-0's defect, and the instrument that fixes it is the board,
not the taxonomy.

**Where the question now lives:** `MAIN-01`, which exists, carries it. `DIVISION.md` §1 gets a
**cross-class flag** on the I-12 row pointing at `MAIN-01` — a pointer, not a reclassification.

**What this ruling costs.** Two things, and I would rather state them than have them found later.
1. **The structural gap is acknowledged and not closed.** If another family's unanswered question
   sits in a different class from its mechanism, the taxonomy will hide it again exactly as it
   hid this one. My mitigation is procedural — the board carries cross-class questions as main
   tasks — and procedure only works while someone runs it. A taxonomic fix would have been
   self-enforcing. I am choosing the weaker mechanism to avoid renumbering live citations, and
   that is a trade, not a free win.
2. **Refusing the split does not make `MAIN-01` cheaper, it makes it more killable.** The
   approximation-error question is now load-bearing: if R1's "poor" is quantitatively right at the
   bar sizes that matter, `MAIN-01` closes `CLOSED-EMPTY` and the whole avenue with it. I am
   ruling that this is the correct exposure. A task that can be killed by one honest measurement
   is worth more than one that has been rescoped until it cannot be.

---

## ADJ-3 — R1-Q1: the `estimated` flag is set and read by nothing. **Allocated D46, as a class**

**2026-09-26 22:11 ET. Ruling on `R1-Q1`** (`OPEN_QUESTIONS.md`, written as `Q1`). R1 declined to
allocate a number and was right to — `D<n>` is mine (`REGISTRY.md`). **It gets one: D46.**

**Number revised at 22:48 ET.** This block first said D44. `BT3-REQ-2` and `R1-REQ-3` / `R1-REQ-4`
landed while I was writing, and D44 went to BT3's measured bootstrap defect (ADJ-9) because BT3's
own write-once file already requested that number and I would rather move my own entry than leave
a stale cross-reference in a file I cannot edit. See the allocation table at the end.

**Why it qualifies.** The objection I weighed against it is that no published number changes: an
unread flag corrupts a *label*, not an arithmetic result. That objection fails on the register's
own precedent. `DEFECTS.md` already holds entries that change no number — **D37** is an
expressibility limit, **D42** is a methodological caveat about a control. The register's stated
purpose is "read before trusting any number a tool prints", and this is a reason not to trust the
**name** on a number, which is the same class of harm and is the harder one to detect.

**Why it matters more than a documentation nit.** `indicators/volume.py:1-9` makes a promise —
any result derived from proxy delta "is flagged `estimated=True` … the system says so rather than
quietly presenting it as order flow". The flag is produced (`Bar.delta_is_estimated`,
`bars.py:91-92`; `VolumeProfile.estimated`, `volume.py:258`) and no consumer reads it
`[measured, R1: grep -rn "estimated" futures_agents/ --include=*.py → 13 hits, all inside
indicators/volume.py and data/bars.py]`. So the docstring's safeguard is true of the dataclass and
false of the pipeline, and every published `scan_reports/` row carrying `cvd_directional`,
`delta_confirms_bar` or `delta_divergence` presents a close-location-value bar-shape predicate
under the order-flow name with the flag available and unconsulted.

**I am allocating it as a *class*, not a single instance, and the reason is forward-looking.**
`R1-REQ-3` reports a second instance of exactly this shape (ADJ-10): `detect_imbalances`'
docstring at `indicators/structure.py:443` documents the function as reading "range and **delta**",
and the body reads `volume` and never touches delta. The group audit now on the board
(`MGR-T5`/`T6`/`T7`) is *a systematic search for more instances of this class* over 47 remaining
conditions, and it will find more. Ten adjacent D-numbers for ten docstrings would bury the
pattern; one class entry with an instance list makes it the finding it is.

**D46, as allocated (text for whoever owns `DEFECTS.md` to apply — it is not my file):**

> **D46 — Documented inputs the code does not read.** A class, with instances appended as the
> condition-group audit finds them. Both known instances were found in round 1/2 by R1.
>
> **Instance 1 — the `estimated` flag is set and read by nothing.** `indicators/volume.py:1-9` promises
> that proxy-derived results are flagged `estimated=True` so the system "says so rather than
> quietly presenting it as order flow". The flag is produced (`data/bars.py:91-92`,
> `indicators/volume.py:258`) and has **zero consumers** — no read in `strategies/library.py`,
> `features.py`, `backtest/`, or the reporting path `[measured: grep -rn "estimated"
> futures_agents/ --include=*.py → 13 hits, all inside indicators/volume.py and data/bars.py]`.
> Consequence: every published row carrying `cvd_directional`, `delta_confirms_bar` or
> `delta_divergence` presents an OHLCV bar-shape predicate under the order-flow name. **No
> published number is wrong; every affected row's label is.** Found by R1, round 1
> (`research/R1_flow_auction.md`, HEADLINE and R1-D4). Status: open. Fix: either consume the flag
> in the reporting path or rename the three `orderflow` conditions.
>
> **Instance 2 — `detect_imbalances`' docstring names an input the function does not read.**
> `indicators/structure.py:443` documents "*Bars whose range and **delta** both far exceed the
> recent norm*"; the body computes `avg_vol` from `b.volume` `[:454]` and `v_mult` from
> `bars[i].volume` `[:459]`, and **reads no delta anywhere**. It also returns
> `magnitude = r_mult` `[:461]` — the *range* multiple — so a caller ranking "imbalances" by
> magnitude is ranking displacement, never participation. Upstream of the three `imbalance`
> conditions (`library.py:1168-1202`), a group screened programme-wide. **No published number is
> affected** — the conditions were screened with the body's arithmetic, and `BT1` inherited the
> correct reading by reading the body rather than the docstring. The harm is to future readers.
> Found by R1 (`R1-REQ-3`, `research/R1_group_audit.md`). Fix: one docstring line.

**R1 may now cite `D46` in R1-D4 and in `R1-REQ-3` instead of describing either longhand**, which
is what it asked for in both places.

**What it costs.** Two things. A D-number is a claim on someone's attention, and the register's
value is inversely proportional to how many entries are nits — I am spending some of that credit
here. And once `D46` exists, **`orderflow`-bearing rows in four published reports are formally
mislabelled**, so any future quotation of them owes a caveat. That is the point, and it is not
free: it makes the existing corpus slightly more expensive to cite correctly. The class framing
adds one more cost: an open-ended entry gets appended to by three agents, so `D46` is the one
defect in the register whose scope can grow without anyone re-adjudicating it. If its instance
list passes about six, it should be split by harm profile — labels-wrong versus readers-misled —
and I am recording that trigger now so the split is a decision rather than a drift.

---

## ADJ-4 — R1-Q2: the zero-trade denominator. **The bound is already published. No figure changes. Allocated D47 for the narrower defect**

**2026-09-26 22:11 ET. Ruling on `R1-Q2`** (`OPEN_QUESTIONS.md`, written as `Q2`). This one bears
on every deflation figure the programme has published, so I am ruling it in full and stating the
arithmetic.

**(a) Did zero-trade `openinterest` strategies enter the 2,975,629 denominator? Yes.** Two
independent grounds:

1. **2,975,629 counts evaluations, not traders, and the record says so by offering the
   alternative.** `[repo-verified: workspace/studies/RANKING_FINDINGS.md:66-72]`: "2,975,629
   strategy evaluations across the whole project (bigscan 533k, focus 613k, other studies 1.13M,
   rank cells 549k+152k) → free_t = 5.46 … **Even discounting the 82% of generated strategies that
   never trade, the effective search is ~495k and free_t 5.15, still uncleared.**" A figure cannot
   be *discounted* for non-traders unless non-traders were in it.
2. **`openinterest` was inside a screened population, not filtered out ahead of it.**
   `[repo-verified: workspace/studies/DEFECTS.md:210]`, the `x_conditions` verdict log, reports
   `oi_expanding` as one of its 34 tested conditions with the result "fires on 0.0% of bars". A
   condition cannot be reported at 0.0% by a study that never sampled it.

**(b) Does removing them change `free_t`? No — and the reason is arithmetic, not judgement.**
`free_t = sqrt(2·ln n)` is logarithmic, so the denominator is close to irrelevant at this scale
`[measured: python3 -c "import math; [math.sqrt(2*math.log(n)) for n in (...)]"]`:

| n | `free_t` |
|---|---|
| 2,975,629 (as published) | **5.4600** |
| 1,487,815 (half removed) | 5.3316 |
| 495,000 (the published zero-trade discount) | **5.15** (as published) |
| 268,337 (91% removed) | 5.0000 |
| 2,197 | 3.923 |

**The ruling.** `openinterest`-bearing strategies are a strict subset of the 82% that never
traded, so removing them is bounded above by a discount the programme has **already computed and
already published**: `free_t` 5.46 → 5.15, uncleared at both ends. The largest t anywhere in the
project is **3.923**; the denominator would have to fall to about **2,197** for the threshold to
meet it, which is a 99.93% reduction. **No published deflation figure changes, no verdict moves,
and R1's own instinct — "the settled negative verdict is safe either way" — is confirmed with the
number attached.** R1-Q2 is **CLOSED**.

**This also closes the open half of `X-15`** in `AVENUES.md` ("the verdict is settled; the
denominator is not verified"), which cites R1-Q2 as its open item. Routed to discovery, whose file
it is.

**No defect for the denominator accounting.** The bound is on disk at
`RANKING_FINDINGS.md:70-72`. What is *not* on disk is that bound's onward transmission — `BRIEF.md`
and the scan reports quote `free_t = 5.46` without the 495k/5.15 companion. That is a
reporting-hygiene gap, it is one line to fix, and inflating it to a D-number would dilute the
register for no gain. Recorded here and routed, not numbered.

**But the narrower thing R1 found does get a number: D47.** It is not about the denominator; it is
about the candidates. Both `openinterest` conditions are dead on *every* file in this repo, so any
strategy carrying one is a guaranteed zero-trade evaluation **by construction** rather than by
chance — a deterministically wasted evaluation, and for `oi_expanding` (a FILTER) a deterministic
veto of every entry in any strategy carrying it. The register already distinguishes defects that
"corrupt results" from those that "merely waste budget"; this is the second kind, and it is the
cleanest example of it in the repo.

**D47, as allocated (text for `DEFECTS.md`'s owner):**

> **D47 — `openinterest` conditions are structurally dead, so every strategy carrying one is a
> guaranteed zero-trade evaluation.** `open_interest` is `None` on every bar of all 48 `csv/raw`
> files — there is no such column `[repo-verified: features.py:278-279; DIVISION.md Appendix B.1]`
> `[measured, R1: all 300 MGC_1h bars have open_interest None]`. So `oi_price_confirmation`
> (SIGNAL) and `oi_expanding` (FILTER) both return `ConditionResult.no()` unconditionally
> `[repo-verified: strategies/library.py:1281-1282, 1309-1310]`, corroborated at
> `[repo-verified: DEFECTS.md:210]` ("`oi_expanding` fires on 0.0% of bars"). A never-firing
> SIGNAL yields zero trades; a never-passing FILTER vetoes every entry. **Budget waste, not
> corruption:** the deflation direction is safe (an inflated denominator makes the threshold more
> conservative) and the bound is already published — 82% of generated strategies never trade,
> effective search ~495k, `free_t` 5.15, still uncleared
> `[repo-verified: RANKING_FINDINGS.md:66-72]`. Found by R1, round 1 (`R1-Q2`). Status: open.
> Fix: exclude the `openinterest` group from generation while `open_interest` is `None`, or
> populate the column. **Do not "fix" this by recomputing `free_t`** — see `manager/ADJUDICATIONS.md`
> ADJ-4 for why the recomputation changes nothing.

**What ADJ-4 costs.** Ruling "no figure changes" removes the incentive to ever count the
structurally-null subclass exactly, so the programme will keep quoting a denominator it knows is
inflated by an unmeasured amount. I judge that acceptable because the error's *sign* is known and
conservative — but it means the honest sentence is "≥ 2,975,629 candidates were generated, of
which an unmeasured subset could not trade", and anyone writing "2,975,629 strategies were tested"
is overstating it. That sentence is now more awkward to write, permanently.

---

## ADJ-5 — R3-Q2: the "≤2" pre-registration is refuted. Accepted in full, with the reason I was wrong

**2026-09-26 22:11 ET. Ruling on `R3-Q2`** (`OPEN_QUESTIONS.md`, written as `Q3`).

**Refutation accepted without reservation.** `DIVISION.md` §6 predicted of R3-D5 "I predict **≤2
exist**". R3 found **six** under the strict definition plus **two** artefact-replay items needing
no library change: `trail_atr_mult` on; a residual runner (`sum(scale_out) < 1`);
`time_stop_bars=None`; the three combined; `StrategyFilters` scope variation; `StopKind.FIXED_TICKS`
`[repo-verified: research/R3_path_operation.md, R3-D5 Tier 1 and Tier 2]`. The evidence is one
generation, cited, reproducible: 314 strategies, `trail_atr_mult ∈ {None}`, `scale_out` sums
`∈ {1.0}`, `time_stop_bars is None` in 0 of 11 catalogue exits, **one** distinct
`StrategyFilters` identity, `FIXED_TICKS` in 0 of 11.

**The reason I was wrong, because a refuted pre-registration is only worth the diagnosis.** I
reasoned from "~2,975,629 evaluations have already been spent on this space" to "the cheap
configurations must have been tried". That inference treats search **volume** as search **width**,
and R3 showed they are different dimensions here. The volume is in the rule-set dimension; the
exit dimension is eleven fixed literals `[repo-verified: combinator.py:53-110]` and the filter
dimension is one, because `generate_combinations` passes `filters=template.filters` unchanged
`[repo-verified: combinator.py:581]`. **2.97M evaluations sampled one corner of the operating
space very many times.** Nothing forbade the other corners — `ExitModel.__post_init__` accepts
every one of R3's six `[repo-verified: base.py:226-236]` — they were never written into the
catalogue.

**Ruling, and this is the transferable part:** from here, **any claim of the form "this has
already been tested" must name the dimension that was varied.** "n = 2.97M" is not coverage of
anything but the dimension the sampler moved in. This applies to me first: it is the error that
produced the "≤2", and the same error would have produced "≥10 of 15" for R1 (I got 9) and "fewer
than ~15 path-cited claims" for R2 (I got 89).

**R3's routed request is granted, and upgraded from a recommendation to a gate.** R3 asked that
its six be run as a **paired re-emission of the same rule sets**, per D15 — only 93 of 8,317
shipped rule sets exist with two different exits, so exit comparisons on the shipped population
are confounded with the entry `[repo-verified: workspace/studies/DEFECTS.md:184-187]`.

> **RULING (binding on every agent).** A Tier-1 result produced by an unpaired sweep is **not
> reportable**. Not "weaker" — not reportable, in the same sense `PIPELINE.md` §4 gives for an
> UNVERIFIED algorithm: nobody can say whether the effect is the exit or the entry it was sampled
> with. This sits on the board as `MGR-T3`, and it gates `MGR-T3` → any Tier-1 run.

**Two orderings I am adding that R3 flagged and did not rank, because they decide whether a run
is interpretable at all:**

1. **Tier-1 item 1 (turn the trailing stop on) must not run before A-2 is fixed.** The exit
   *reason* reports as `STOP`, so `ExitReason.TRAIL` can never be emitted
   `[repo-verified: R3_path_operation.md A-1, A-2]`. A trail arm run first produces numbers whose
   exit-mix cannot be read, and exit mix is the Channel-3 quantity that makes the trail
   non-cancelling in the first place. The 2-line fix at `engine.py:419-421` is a prerequisite,
   not a nicety.
2. **Tier-0 needs no pairing and must not be delayed by it.** Items 7 (governor replay over 21,954
   stored trades) and 8 (`mode="block"` vs `mode="iid"`) are replays and a function call over
   existing artefacts — there is no exit arm to pair. They are the cheapest real measurements in
   the programme. Board: `MGR-T9`, `MGR-T8`.

**What ADJ-5 costs.** The pairing gate makes every Tier-1 item roughly twice the work, and it
converts six cheap items into one design task plus six runs. Some of the six will not be run
within this programme's remaining budget, and the ones that are not will stay untested with a
*reason* attached rather than being tested badly. I am ruling that is the right trade: D15 exists
because this repo already produced a confounded exit comparison once and had to retract it.

---

## ADJ-6 — BT1-REQ-1: which substrate may a backtester measure on

**2026-09-26 22:11 ET. Ruling on `BT1-REQ-1`** (`backtest/BT1/REQUESTS.md`). BT1 is right that
this wants deciding once for all three backtesters, and right that the two halves of `BRIEF.md`
it quotes are both true.

**Ruling, in three parts:**

1. **`csv/raw/` is mandatory for any number that is placed beside a published `scan_reports/`
   figure.** It is the snapshot every published result was measured on; comparability is the whole
   reason it is frozen, and a comparison across two vendor pulls is not a comparison.
2. **`data/archive/` is permitted as a measurement substrate** — for a number that is **labelled
   with its substrate** and **never pooled with a `csv/raw` number inside one statistic.** Two
   reasons, and the second is the stronger. The archive contains the published span *and* adds
   roughly thirteen months *before* it, and `AVENUES.md` X-12 states the consequence precisely:
   "that prior period is the only genuinely disjoint, never-searched out-of-sample data this
   project has", and it is the natural answer to the nested-window problem (30 ⊂ 90 ⊂ 180 ⊂ 274
   days, all ending on the same bar, "arithmetic, not replication"). Refusing the archive to
   protect comparability would discard the one thing in this repo that is *not* comparable **by
   design**, which is exactly what out-of-sample means.
3. **Prerequisite: a bar-for-bar reconciliation on the overlapping window, written down, before
   any archive number is reported.** BT1 named this itself and it is not optional — the two stores
   are different vendor pulls on different grids. **It is one task, done once, for all three
   backtesters**, and three backtesters each doing it privately is precisely the duplication this
   board exists to prevent. Board: `MGR-T4`, assigned to BT1 because it raised it and needs it
   first. Until `MGR-T4` lands, archive numbers are `PROVISIONAL-SUBSTRATE` and not reportable.

**What this does and does not do for BT1-ALGO-1, stated so BT1 does not over-read it.** The
ruling changes the sentence BT1 writes: not "rare signals are structurally unmeasurable here" but
"rare signals are measurable only on a substrate disjoint from every published result, at a stated
cost in comparability". **It does not rescue the power problem.** ALGO-1 fires on 2-41 bars per
`csv/raw` series; the archive is about 2.3×, so roughly 5-95, against `toolkit.FLOOR = 20`. BT1's
pre-registered expectation — that no test will have the power to separate ALGO-1 from its placebo
— most likely still holds, **and that pre-registration surviving a 2.3× sample increase is a
better result than the sweep would have been.** Report it that way.

**What it costs.** Permitting a second substrate creates a new way to be wrong that this repo has
not had: a result quoted without its substrate, later compared against a `csv/raw` figure by
someone who did not know. The label is the only defence and labels erode. I am also spending a
backtester burst on `MGR-T4`, which produces no finding at all — reconciliation is pure overhead,
and it is overhead I am choosing over the alternative of never using the only out-of-sample data
in the repo.

---

## ADJ-7 — BT1-REQ-2: D37's scope is narrower than stated. Accepted as a note on D37, not a new number

**2026-09-26 22:11 ET. Ruling on `BT1-REQ-2`** (`backtest/BT1/REQUESTS.md`).

**Accepted, and it is the most consequential of the two requests** because three tracks are
reading D37 and two wrote verdicts that depend on its scope.

BT1's correction: D37's "the combinator cannot express a sequence at all" binds the
**template/`min_signals`** layer only. A **single precomputed condition can read as many bars as
it likes**, and the pattern is already in this tree — a column computed from the bar series, keyed
by `(symbol, tf, ts)`, looked up by the condition
`[repo-verified: workspace/newstrats/depth.py:159-175, 191-203; workspace/newstrats/freshness.py:164]`.
So "A on bar i−1 and B on bar i" is one condition on one bar, and `min_signals` never sees the
sequence.

**Ruling:** this is a **correction to an existing defect note, so it becomes a note on `D37` and
does not get a new `D<n>`.** Numbering a clarification of D37 as D46 would leave two entries that
must be read together, which is how a register starts lying.

**The honest statement of D37's scope, as ruled:** ordered chains are **inexpressible as
confluences** and **buildable as single conditions.**

**And the cost that keeps `P9` a real primitive — which is the half that must travel with the
correction, or "D37 has a workaround" will be read as "D37 is fixed".** BT1 stated it exactly:
one bespoke condition per sequence, no template support, and **no ability to ablate the legs
against each other.** That third clause is the whole cost. A sequence built as one condition
cannot be decomposed to say *which leg carried the information* — which is the only question worth
asking of a sequence, and the question the ICT work already needed and could not answer ("the
sweep→shift→retrace sequence is real, common, and **adds nothing over its parts**" is a statement
that required exactly this ablation, `BRIEF.md` rule 8). So **R1's costing of `P9` as architecture
stands**, and R1's claim narrows rather than falls: not "every ordered-chain idea is
inexpressible", but "every ordered-chain idea is measurable as a black box and unablatable".

**Routed to R1** (revise the `P9` row's wording and §7 Q3 note 3, `R1-D5`) **and to R3** (`R3-D6`
is scoped to the sequence primitive and should carry the narrowed statement). Neither verdict is
overturned; both are narrowed.

**What it costs.** The narrowing makes a family that was cleanly "unreachable" into "reachable but
unablatable", which is a harder sentence to act on and an easier one to abuse — a later burst can
now build a sequence condition, measure it, find nothing, and report a null that means less than
it looks like it means, because the parts were never separated. Anyone building one owes the
ablation caveat up front.

---

## ADJ-8 — A correction to `DISC-LEAD-05`'s arithmetic, which changes the task's size by a third

**2026-09-26 22:11 ET.** Not a dispute; a measured correction that a task estimate depends on, so
it is ruled rather than mentioned.

`DISC-LEAD-05` states "R1 audited **3 of 19** condition groups for name-vs-arithmetic … The
remaining **16 groups / 71 conditions** have never been audited the same way"
`[repo-verified: discovery/AVENUES.md:393]`. **That undercounts R1's delivery.** R1-D4 is scoped
to "all 27 conditions in the six participant-information groups" and delivers verdicts for
`orderflow` 3, `volume` 3, `profile` 6, `vwap` 5, `liquidity` 7, `imbalance` 3 = 27, **plus**
`openinterest` 2 and `news` 3 from the HEADLINE = **32 conditions across 8 groups**
`[repo-verified: research/R1_flow_auction.md, "Tally of the 27" at :508-523 and the HEADLINE]`.
Discovery counted only the three *phantom* groups.

**So the unaudited remainder is 11 groups / 47 conditions, not 16 / 71** — a third smaller:
`trend` 8, `momentum` 6, `structure` 5, `meanreversion` 3, `volatility` 3, `regime` 3,
`multitimeframe` 3, `time` 4, `fibonacci` 4, `supplydemand` 3, `candlestick` 5 = 47, against
`DIVISION.md` Appendix A's 79 total.

**Two rulings follow.**

1. **The audit is split three ways by code surface, not given to R1.** The 11 remaining groups
   span all three tracks' surfaces; `DIVISION.md` §2 gives R1 only the six participant-information
   groups, so R1 auditing `meanreversion`, `volatility` and `regime` would put it inside R3's
   surface and re-create the duplication the division exists to prevent. The audit's value comes
   from having read the indicator underneath — R1 found `orderflow` was bar-shape algebra because
   it had read `indicators/volume.py`. Board: `MGR-T5` (R1: `structure`, `supplydemand`,
   `fibonacci` — 12), `MGR-T6` (R3: `trend`, `momentum`, `meanreversion`, `volatility`, `regime`,
   `multitimeframe`, `candlestick` — 31), `MGR-T7` (R2: `time` — 4, plus the ADJ-1 consolidation).
   **R1's verdict vocabulary is fixed as the shared one** — PROXY / DEGRADED / HONEST-DERIVED,
   plus HONEST-DERIVED-BUT-BROKEN from its own addendum — so three auditors stay comparable.
2. **Seven aliases are already known and must not be re-derived.** `X-9` records that seven filter
   names are exact aliases for strategy-group membership: `avoid_lunch`≡REVERSAL,
   `opening_drive_window`≡OPENING_RANGE, `after_opening_range`≡LIQUIDITY,
   `mtf_not_conflicted`≡PULLBACK, `regime_trending`≡TREND, `regime_ranging`≡MEAN_REVERSION,
   `volatility_compressed`≡BREAKOUT `[repo-verified: AVENUES.md X-9, citing
   21-study-programme.md:118-141]`. **Five of the seven sit inside the 11 unaudited groups.** Cite
   `X-9` and move on; the audit's new content is the other 42.

**Routed to discovery**, whose file `AVENUES.md` is — `DISC-LEAD-05` and `X-8`'s stopping point
both need the corrected count, and I do not edit another agent's file.

**What it costs.** Splitting the audit three ways buys surface knowledge and loses single-auditor
consistency; the fixed vocabulary is a partial defence and not a complete one. Three agents will
draw the PROXY/DEGRADED line slightly differently, and the merged table will need a reconciliation
pass I have not scheduled.

---

## ADJ-9 — BT3's four requests: **D44 allocated**, the `correlation_group` conflict ruled, two granted

**2026-09-26 22:48 ET.** `backtest/BT3/REQUESTS.md` landed while I was writing ADJ-0…ADJ-8. Ruling
on all four.

### ADJ-9a — `BT3-REQ-2`: the block bootstrap is not circular. **Allocated D44**

Granted as requested, **and it takes D44** — the number BT3 asked for. BT3 could not allocate it
(`REGISTRY.md`) and guessed the next free one correctly at the time it wrote; rather than make its
write-once file stale I moved my own two entries down and left BT3's citation valid. That is the
cheaper correction: I can edit this file and nobody can edit `backtest/BT3/REQUESTS.md`.

The defect is measured, has a passing test, and has a one-line fix.
`bootstrap_paths` draws `r_values[start:start + block]` with no wrap-around
`[repo-verified: futures_agents/backtest/montecarlo.py:103-107]`, so element *i* is reachable from
only `min(i + 1, block)` distinct starts: the first `block − 1` elements are under-sampled on a
linear ramp (frequency/expected **0.122** at index 0 against a tail mean of **1.123**) while `iid`
mode over the same series is flat within `[0.988, 1.011]`
`[measured: backtest/BT3/code/checks.py::check_block_bootstrap_undersamples_the_start → passes]`.

**D44, as allocated (text for `DEFECTS.md`'s owner):**

> **D44 — `bootstrap_paths(mode="block")` is not a circular bootstrap and under-samples the start
> of every series.** `futures_agents/backtest/montecarlo.py:103-107` draws
> `r_values[start:start + block]` without wrap-around, so the first `block − 1` elements are
> systematically under-sampled and the rest over-sampled — measured at 0.122× expected frequency
> at index 0 versus a 1.123× tail mean on a 40-element series with `block=10` over 20,000 paths,
> where `iid` mode is flat within `[0.988, 1.011]`
> `[measured: workspace/roundtable/backtest/BT3/code/checks.py]`. **Consequence:** the block arm
> silently discounts the beginning of every trade sequence, so drawdown, streak and p05 statistics
> from it are biased on any series whose early trades are unrepresentative — every warm-up-affected
> and every regime-shifted strategy. **Nothing published carries it** — no call site ever passed
> `mode="block"` `[measured: grep -rn 'mode="block"' --include=*.py . → montecarlo.py:91 docstring
> only]`. It gates every future use, and `R3-D5` Tier-0 item 2 is the first. Found by BT3, burst 01
> (`BT3-REQ-2`). Status: open. Fix: `path.extend(r_values[(start + k) % n] for k in range(block))`.

**Ruling with teeth attached:** the block-vs-iid measurement on the board (`MGR-T8`) is **not
reportable until D44 is fixed**. BT3 flagged its own numbers as carrying the bias rather than
correcting silently, which is the right call and is why this is a gate rather than a retraction.

### ADJ-9b — `BT3-REQ-3`: `correlation_group` versus the BRIEF's index complex. Both statements are true; the mapping is still too fine for the cap

BT3 asked me to choose between two horns. **Neither horn is right, and the resolution is the useful
part.**

**The two claims are about different objects and both stand.** `BRIEF.md`'s D14/D41 claim is about
**rule-set overlap** — MES/MNQ/NQ/ES populations share 0.5–0.8% of rule sets, so agreement between
them is not independent corroboration. `ContractSpec.correlation_group` is about **price
co-movement for position sizing**. A statement about sampler overlap cannot contradict a statement
about price correlation. No defect in either.

**But BT3's underlying measurement survives that, and it is the finding.** On the four-symbol
artefact population the groups are `PRECIOUS_METALS`, `US_EQUITY_BROAD`, `US_EQUITY_TECH`, `ENERGY`
— four symbols, four groups — so `max_correlated_positions = 1` `[repo-verified: config.py:374]`
degenerates into the per-symbol check that already precedes it at
`[repo-verified: risk/manager.py:245-252]` and **fires zero times in every arm**
`[measured: backtest/BT3/code/checks.py::check_correlation_cap_is_inert]`.

**Ruling.** For a cap whose stated purpose is *do not hold two positions that are the same bet*,
splitting the index complex into `US_EQUITY_BROAD` and `US_EQUITY_TECH` is **too fine**, and the
programme has already said so in its own words — "agreement between them is not corroboration" is
`BRIEF.md` asserting that MES and MNQ are close to one bet. So:
- the shipped mapping is **mis-specified for this cap's purpose**, not wrong in general (it may be
  right for other consumers, and I have not audited them);
- **`R3_operating_vocabulary.md` P2's verdict should be revised from `INEXPRESSIBLE-ARCH` toward
  "expressible and mis-specified"** — routed to R3, whose file it is. I am not applying it; a
  manager editing a researcher's verdict is the cross-edit `OWNERSHIP.md` forbids.
- **No D-number.** A specification being too coarse for one consumer is a design judgement, not a
  defect, and BT3 itself notes the cap fires zero times either way on this population.

**One caveat BT3 should carry:** "the cap is inert" is measured on *four symbols in four groups*,
which is a property of the population as much as of the mapping. It is not evidence that the cap
would be inert on a population containing MES **and** ES.

### ADJ-9c — `BT3-REQ-1`: a direct serial-dependence test. Granted, and R3's item-8 claim is narrowed

**Granted**, and I am backing the backtester against its researcher on the interpretation, because
BT3 is right. `R3-D5` Tier-0 item 8 claims the `mode="block"` vs `mode="iid"` comparison "decides
whether *any* streak-based sizing or equity-curve rule can work". **It does not.** It compares two
resamplers and detects dependence only indirectly and only at the chosen block scale. BT3's phrase
is the one to keep: "an indirect null being read as a direct null is the kind of thing that becomes
settled by repetition" — and this repo has a documented history of exactly that.

**Ruling:** the direct test (lag-1..10 autocorrelation, runs test or Ljung-Box, **per strategy**,
aggregated with correlated-variant inflation accounted for) goes on the board as `MGR-T11`. BT3's
own correction to its request makes it cheap: the machinery exists at
`[repo-verified: workspace/chrono/analyse.py:92-103]` (`corr`, `fisher_z`) but is applied to a
strategy group's **monthly expectancy**, not to a **per-trade R sequence** — different objects, and
only the second is the precondition for streak sizing. ~20 lines, no new data, no backtest.

**And R3's item-8 wording is narrowed**, routed to R3: item 8 measures whether *the block
resampler's* dependence assumption changes the ruin statistics; it is a precondition check, not the
verdict on Channel 4b's streak sub-case. Routed, not edited.

### ADJ-9d — `BT3-REQ-4`: trade dumps must record `entry_price`, `initial_stop`, `symbol`. Granted as a board convention, effective now

**Granted.** The gap is real: `geo_trades.json`'s 17 keys carry no price, no point distance and no
dollar figure, so `RiskManager.contracts_for` — the integer-contract floor, which R3-D4 labels the
one door through which sizing becomes a Channel-2 population effect — cannot be evaluated from the
artefact at all `[repo-verified: workspace/newstrats/run_geometry.py:113-121]`. BT3 recovered it by
re-running all 22 dumped strategies and matching 21,954 / 21,954 trades at worst `|Δr| = 0`, which
proves it is recoverable *and* proves the cost: one script per artefact, and only while the
generating script, the slicing and the frozen snapshot all still agree.

**Ruling:** this is a **binding convention on `manager/BOARD.md`, effective immediately** —
any trade dump intended for later operating-layer work records `entry_price`, `initial_stop` and
`symbol`. I am not waiting for a `BRIEF.md` edit, because BT1 and BT2 will hit this before a
`BRIEF.md` round happens and BT3 says so. Routed to the parent for `BRIEF.md` as well, so it
outlives this board.

**What ADJ-9 costs.** Three of the four are cheap. `ADJ-9b` costs the most: I am declining a
D-number on a mapping I have just called mis-specified, which means the correlated cap stays
inert with a ruling rather than a register entry behind it, and a future reader who greps
`DEFECTS.md` will not find it. That is the price of not inflating the register, and the mitigation
is that `MGR-T7`'s and R3's verdict revision both cite this block.

---

## ADJ-10 — R1's four requests: **D45 allocated**, one folded into D46, two granted

**2026-09-26 22:48 ET.** `research/R1_REQUESTS.md` also landed mid-turn, from R1's fidelity ruling
on `BT1-ALGO-1` and its group audit.

### ADJ-10a — `R1-REQ-4`: `StopKind.VWAP_BAND` collapses to the min-stop floor. **Allocated D45**

**This is the strongest of the five defect candidates on my desk this turn**, and it gets D45.

`vwap_bands` computes σ as a session-to-date volume-weighted dispersion that resets at each 18:00
ET anchor, so **σ is exactly 0 on the first bar of every CME trading day by construction**
(`pv2/vol − mean² = tp² − tp² = 0`) and small for several bars after
`[repo-verified: futures_agents/indicators/volume.py:70-104, :32-42]`. `stop_price` then sets
`dist = abs(entry − band) * stop_mult + pad` `[repo-verified: base.py:296-300]` and clamps to
`min_stop_ticks * tick_size` `[:315-316]`. Measured at `stop_mult = 1.0`, `pad = 0`, the raw
distance is **below that floor on 6.0% (MNQ) to 33.7% (MCL) of 1h bars**, where a `1.0 * ATR` stop
is below it on **0.0%** `[measured, R1: python3 over csv/raw/{MGC,MCL,MNQ,MES}_1h.csv]`.

**Why it outranks the others: it changes what a published result is about.** On those bars
`VWAP_BAND` is not a VWAP stop — it is `FIXED_TICKS` at `min_stop_ticks` wearing another name in
every report that carries it. And it is a live candidate mechanism for a *published finding*:
`x_exits` reported "no stable best stop width — the ordering reverses by timeframe"
`[repo-verified: DEFECTS.md:210]`, and a stop kind that silently becomes a different stop kind on a
third of MCL bars would do that. That makes it a measurement artefact standing behind a result the
programme treats as settled, which is the highest-consequence shape a defect can have here.

**D45, as allocated (text for `DEFECTS.md`'s owner):**

> **D45 — `StopKind.VWAP_BAND` silently becomes `FIXED_TICKS` on 6–34% of bars.** `vwap_bands`'
> σ is a session-to-date volume-weighted dispersion resetting at the 18:00 ET anchor
> `[repo-verified: indicators/volume.py:70-104, :32-42]`, hence **exactly 0 on the first bar of
> every CME trading day** and small for several bars after. `ExitModel`'s `stop_price` sets
> `dist = abs(entry − band) * stop_mult + pad` `[repo-verified: strategies/base.py:296-300]` and
> clamps it to `min_stop_ticks * tick_size` `[:315-316]`, so the clamp binds on
> **6.0% (MNQ) to 33.7% (MCL) of 1h bars** at `stop_mult = 1.0, pad = 0`, against **0.0%** for a
> `1.0 * ATR` stop `[measured, R1: python3 over csv/raw/{MGC,MCL,MNQ,MES}_1h.csv]`. **Any published
> result carrying `VWAP_BAND` is partly a result about a fixed-tick stop**, and this is a candidate
> mechanism for `x_exits`' "no stable best stop width" `[repo-verified: DEFECTS.md:210]`. Found by
> R1 answering `R3-Q1` (`msgs/04_R1_R3_re-VWAP-BAND.md`, `R1-REQ-4`). Status: open. Fix: report the
> clamp rate beside any `VWAP_BAND` result, or floor σ rather than the distance.

**Consequence I am ruling rather than leaving implied:** R3's `R3-Q1` verdict — that `VWAP_BAND` is
a re-scaled ATR stop, so the vocabulary holds four mechanisms not five — **is not merely confirmed,
it is under-stated.** On 6–34% of bars it is neither a VWAP stop nor an ATR stop but a fixed-tick
stop, so the vocabulary has *three* volatility-scaled mechanisms and one that intermittently is not
scaled at all. Routed to R3 to apply in its own file.

### ADJ-10b — `R1-REQ-3`: `detect_imbalances`' docstring. **No new number — folded into D46 as instance 2**

Ruled in ADJ-3 above. It is the same class as the `estimated` flag: a documented input the code does
not read. `R1-REQ-3` is answered — cite **D46**.

### ADJ-10c — `R1-REQ-1`: promote BT1's D38 registration guard to a shared primitive. Granted

**Granted, and this is the request I would have prioritised if R1 had not.** BT1 solved D38's
silent-zeroing properly: every bar of a registered frame gets a key, with value `None` for warm-up,
so **"key present, value `None`" (warming up) is distinguishable from "key absent" (wrong bar grid,
or nobody called `register_frame`)**, and the second case is counted in a module-level `MISSES` dict
`[repo-verified: backtest/BT1/code/absorption.py:91-104, 239-257]`. That is the difference between a
custom condition returning zero trades **loudly** and returning zero trades **silently**, and D38 is
the defect most likely in this repo to have already produced a null someone believed
`[repo-verified: AVENUES.md X-11]`.

R1's cost-of-waiting argument is correct and decides it: if BT2 and BT3 each write their own, the
two that get it subtly wrong will report zero-trade results indistinguishable from real nulls.

**Ruling on the open question R1 flagged — whose file it goes in.** Not a backtester's: a helper
imported by all three cannot live in one owner's `code/` without giving that owner a write on the
other two's dependency. **It goes to the parent session** as the only writer with no track, as
`workspace/roundtable/lib/registry_guard.py`, and lands on the board as `MGR-T12`. Until it exists,
**BT2 and BT3 must import BT1's copy read-only rather than re-implement it** — `OWNERSHIP.md` grants
"read, and run" on another backtester's `code/*`, so that is already legal.

### ADJ-10d — `R1-REQ-2`: time-of-day versus trailing-mean volume normalisation. Granted, and promoted

**Granted, and I am promoting it above the sub-task R1 filed it as.** R1 filed this as a cross-cutting
question and then under-sold it. The content: the library holds **two** volume norms — the 20-bar
trailing mean in `detect_imbalances` `[repo-verified: indicators/structure.py:452-455]` and the
time-of-day norm in `relative_volume` (same clock minute over the previous 20 sessions)
`[repo-verified: indicators/volume.py:266-285]` — it uses both, in different places, **with no
statement anywhere about which is intended**, and they select populations differing by **5–27× on
identical bars** `[measured: BT1, backtest/BT1/code/frequency.py]`.

Intraday futures volume has a strong U-shape, so a 2× rolling-mean surge at 03:00 and one at 09:35
are different events. **Therefore any condition in this repo that reads volume against a rolling
window may be measuring time of day rather than participation** — and `BRIEF.md` rule 6 ("no hours
filter improves expectancy") plus the ICT finding that kill zones show "more range and volume, and
no more direction" are both statements this question could reframe. That is a question about the
existing corpus, not about one algorithm.

**Ruling:** board task `MGR-T13`, and **it is a prerequisite input to the group audit** — `MGR-T6`
covers `volatility` and `regime`, both of which read volume against a window, and an auditor who
does not know which norm a condition uses cannot classify it. R1's design constraint is adopted
verbatim and is binding: **if built, both axes take the time-of-day norm or neither does**, because
a time-of-day volume norm against a rolling range norm conjoins two different reference populations
and the result is uninterpretable. **No D-number** — two norms coexisting is a design gap, and
nothing yet shows either is wrong.

**What ADJ-10 costs.** `D45` is the expensive one: it puts a caveat on every published
`VWAP_BAND`-bearing row and it nominates a measurement artefact as the explanation for a settled
finding, which means someone now owes either a re-read of `x_exits` or an explicit decision not to.
I am not scheduling that re-read this turn, so the cost is an open obligation on the board rather
than a discharged one.

---

## Id allocations made this turn

Only the manager allocates `D<n>` and `MAIN-<nn>/S<n>` (`REGISTRY.md`). Five defect candidates
arrived; **four numbers issued, one folded, one declined.**

| id | kind | what | where ruled |
|---|---|---|---|
| **D44** | defect | `bootstrap_paths(mode="block")` is not circular; under-samples every series' start | ADJ-9a |
| **D45** | defect | `StopKind.VWAP_BAND` silently becomes `FIXED_TICKS` on 6–34% of bars | ADJ-10a |
| **D46** | defect (class) | documented inputs the code does not read — inst. 1 the `estimated` flag, inst. 2 `detect_imbalances`' delta | ADJ-3, ADJ-10b |
| **D47** | defect | `openinterest` conditions are structurally dead; carriers are guaranteed zero-trade | ADJ-4 |
| — | **declined** | `correlation_group` too fine for `max_correlated_positions` — a design judgement, not a defect | ADJ-9b |
| — | **declined** | the two volume norms coexisting with no stated intent — a design gap; nothing shows either is wrong | ADJ-10d |
| — | **declined** | `free_t = 5.46` quoted without its published 495k/5.15 companion — reporting hygiene, one line | ADJ-4 |
| `MAIN-01/S<n>` | sections | **none allocated.** `PIPELINE.md` §2 forbids me decomposing `MAIN-01`; the scope request is on the board instead | `BOARD.md` |
| `MGR-T1` … `MGR-T13` | board task | standalone tasks not belonging to a main task | `BOARD.md` |

**Numbering note, recorded because it nearly went wrong.** BT3 requested "D44 (next free)" in a
write-once file at the same time as I was drafting D44 for a different defect. I resolved it by
moving mine, not BT3's. **The general rule from here: an agent that wants a `D<n>` describes the
defect and does not name a number**, exactly as R1 did three times ("I cannot allocate `D<n>`"),
because "next free" is a read of a file that another agent may be about to change.

**`MGR-T<n>` is a new id kind and `check_refs.py` does not yet accept it.** Its `ID` regex admits
issuer prefixes `R[123]|BT[123]|DISC` only, with kinds `Q|REQ|ALGO|D|A|B` — there is no manager
issuer and no `T` kind, so a message whose `RE:` line said `MGR-T4` would **fail the commit**.
Until `REGISTRY.md` and that regex are extended by their owner (the parent session — requested in
`msgs/05`), every message header this turn cites the registry-legal **anchor** id of the task
(`BT1-REQ-1`, `R3-D5`, `DISC-LEAD-05`, `MAIN-01`, …) and names the `MGR-T<n>` in the body only.
Nobody should put an `MGR-T` id in a `RE:` or `ALSO:` line before that lands.

---

## ADJ-11 — The parallel round landed while I was ruling. **D48 and D49 allocated**; nine new requests triaged

**2026-09-27 00:15 ET.** R1, R2 and R3 were dispatched in parallel with this turn and all three
delivered before I finished, along with BT2's and BT3's first bursts. **Nine further requests arrived
after `BOARD.md` was laid out.** Two need a number immediately because they bear on gates I created
earlier in this same file; the other seven are triaged here and ruled next turn. Triaging in writing
rather than ruling badly at speed is the choice, and it is recorded as a choice.

### ADJ-11a — `R3-REQ-1`: `dataclasses.replace` inherits the cached `_id`. **Allocated D48, and it is the most urgent thing on this page**

**This defeats the gate I set in ADJ-5, which makes it the highest-priority allocation of the turn.**
ADJ-5 ruled that every Tier-1 item must be run as a **paired re-emission** or not reported. R3 then
specified that pairing and discovered the pairing **silently cannot work by default**:

`Strategy._id` is a real dataclass field `[repo-verified: base.py:585]` and `strategy_id` memoises
into it via `object.__setattr__` `[repo-verified: base.py:622]`. `dataclasses.replace` copies every
field including `_id`, and **`generate_strategies` has already read it** — its dedupe is
`seen.setdefault(st.strategy_id, st)` `[repo-verified: combinator.py:719]` — so every strategy it
returns arrives with `_id` populated. Therefore
`[measured: replace(S[0], exit=replace(S[0].exit, trail_atr_mult=2.0)).strategy_id == S[0].strategy_id
→ True]`.

**Why this is worse than a nuisance, and why it is not covered by D43.** `run_many` keys `results`,
`open_pos`, `pending` and the in-position skip guard **all by `strategy_id`**
`[repo-verified: engine.py:277-283, 304-309]`. A colliding pair produces **one** `BacktestResult`
whose trades are a path-dependent interleaving of both arms' exits, so **the measured difference
between arms is exactly zero.** Every item on R3's list is a "does this axis do anything" test, which
makes the failure mode **indistinguishable from the result**: a false null that looks like the answer.
D43 repaired what goes *into* the hash; this defeats the hash by never recomputing it.

**D48, as allocated (text for `DEFECTS.md`'s owner):**

> **D48 — `dataclasses.replace` on a `Strategy` inherits the memoised `_id`, so both arms of a paired
> comparison collide into one result.** `Strategy._id` is a dataclass field
> `[repo-verified: strategies/base.py:585]`; `strategy_id` memoises into it
> `[repo-verified: base.py:622]`; `generate_strategies` reads it during dedupe
> `[repo-verified: combinator.py:719]`, so every returned strategy already carries `_id`. A later
> `replace(...)` therefore claims the original's id
> `[measured: replace(S[0], exit=replace(S[0].exit, trail_atr_mult=2.0)).strategy_id ==
> S[0].strategy_id → True; adding _id=None → ids differ]`. **`run_many` keys `results`, `open_pos`,
> `pending` and the in-position skip guard by `strategy_id`
> `[repo-verified: backtest/engine.py:277-283, 304-309]`, so a colliding pair yields one
> `BacktestResult` interleaving both arms and a measured between-arm difference of exactly zero — a
> false null that is indistinguishable from the finding being tested.** Third instance of the family
> holding the `ExitModel.label` fix and **D43**; D43 does **not** fix it. **The library is not wrong,
> only sharp**: the combinator itself uses the correct idiom at `combinator.py:694`
> (`replace(x, symbol=s, _id=None)`). Discipline: **`_id=None` on every `replace`, plus an assert on
> arm-id uniqueness at emission** (`research/R3_pairing_design.md` §2). Found by R3 (`R3-REQ-1`,
> finding `R3-A-13`). Status: open, worked around.

**Ruling with teeth:** **`R-6` is amended — a paired re-emission that does not pass `_id=None` and
assert arm-id uniqueness at emission is not a paired re-emission, and its output is not reportable.**
R3 asked only for the number and explicitly did not request a code change; I am not ordering one
either, because the combinator already demonstrates the correct idiom and a library change here has
test surface. **The discipline is the fix and the assert is what makes it auditable.**

### ADJ-11b — `StopKind.RANGE` is `StopKind.ATR`. **Allocated D49**

From `msgs/05_R1_R3_stopkind-RANGE.md`, found by R1 while auditing `liquidity` for `MGR-T5` — not by
looking for it. R1 correctly declined to allocate and correctly declined to rule, since `StopKind` is
R3's.

`base.py:301-309`'s `RANGE` branch falls through to `dist = self.stop_mult * a` when
`snap.opening_range` is `None`, which is **byte-identical to the ATR branch at `:285-289`**. The
fall-through is not a rare guard: `or_minutes = 30` is hard-coded `[repo-verified: features.py:865]`
and the range accumulates only over bars with `0 <= minutes_since_open < 30`
`[repo-verified: features.py:891-895]`, while the 1h grid is 4,992 bars at `:00` plus 8 strays at
`:30` and MGC's RTH opens at 08:20 — so `minutes_since_open` near the open takes only
`{−20, 40, 70, 100}` and **never lands in `[0, 30)`**.

| cell | `snap.opening_range is None` | `RANGE` behaves as |
|---|---|---|
| **MGC 1h** | **5000 / 5000** | **`ATR`, on 100% of bars** |
| MNQ 1h / MES 1h | 4990 / 5000 | `ATR` on 99.8% |
| MCL 1h | 3291 / 5000 | `ATR` on 65.8% |
| MGC 5m / MNQ 5m / MES 5m / MCL 5m | 3127–3290 / 5000 | `ATR` on 62.5–65.8% |

**D49, as allocated (text for `DEFECTS.md`'s owner):**

> **D49 — `StopKind.RANGE` silently becomes `StopKind.ATR` because the opening range is almost never
> constructed.** The `RANGE` branch falls through to `dist = stop_mult * atr`
> `[repo-verified: strategies/base.py:301-309]`, byte-identical to the ATR branch `[:285-289]`, when
> `snap.opening_range` is `None`. With `or_minutes = 30` hard-coded
> `[repo-verified: features.py:865]` and accumulation gated on `0 <= minutes_since_open < 30`
> `[repo-verified: features.py:891-895]`, MGC's 08:20 RTH open against a `:00` 1h grid makes that
> window unreachable: **`opening_range` is `None` on 5,000 of 5,000 MGC 1h bars**, 99.8% of MNQ/MES
> 1h, 65.8% of MCL 1h and 62.5–65.8% at 5m
> `[measured, R1: python3 over csv/raw, SymbolFrame._session_state[i][1] is None, 5,000 bars/cell]`.
> **Consequence: any comparison of `RANGE` against `ATR` on those cells compared a parameterisation
> against itself — the two arms differ only by `stop_mult`, and the expected difference is exactly
> zero by construction.** Shares its root cause with **D30** (the opening range is never constructed
> at 60m/240m) but is a distinct harm — a silent aliasing of two stop kinds rather than a
> non-firing condition — and the measurement extends to 5m, which D30 does not cover. With **D45**,
> `StopKind`'s five nominal kinds realise **three** distinct mechanisms on MGC 1h, one of which is
> itself a mixture, **and the count differs by symbol and timeframe**. Found by R1 (`MGR-T5`
> `liquidity` audit, `R1_group_audit.md` D-L1/D-L3; handed to R3 in
> `msgs/05_R1_R3_stopkind-RANGE.md`). Status: open.

**Ruling on the vocabulary question, since `R3-Q1` asked it and two findings have now overtaken the
answer.** R3 asked whether `StopKind` holds four mechanisms rather than five. **The answer is that the
question has no single number**: on MGC 1h five nominal kinds realise three mechanisms; on MCL 1h
`RANGE` is genuinely distinct on 34% of bars. **So the honest form is per-symbol and per-timeframe,
and R1's refusal to state one number is right and should be adopted rather than resolved.** R3 applies
this in its own file.

**And the consequence I am escalating rather than leaving as a footnote.** D45 and D49 together mean
`x_exits`' "no stable best stop width — the ordering reverses by timeframe"
`[repo-verified: DEFECTS.md:210]` now has **two** independent candidate mechanisms that are
measurement artefacts rather than market facts — one stop kind partly collapsing to a fixed-tick floor,
another wholly collapsing to ATR, both at rates that **vary by symbol and timeframe**, which is
precisely the pattern "the ordering reverses by timeframe" describes. **That is no longer an open
obligation I can leave unassigned.** It goes on the board as **`MGR-T17` — re-read `x_exits`' stop-kind
comparison against D45 and D49** and it is the highest-value re-read available, because it is the first
time in this programme that a settled negative finding has a named, measured, artefactual explanation.

### ADJ-11c — The other seven requests: triaged, not ruled

Stated as triage so nobody reads silence as refusal. **Each is `RECEIVED` on `BOARD.md`; none is
blocking its filer.** My preliminary read, to be confirmed or overturned next turn:

| request | subject | preliminary triage |
|---|---|---|
| `R2-REQ-1` | `BacktestResult` records no partner provenance, so two environments collide on one `strategy_id` | **Likely a `D<n>`, and likely the same family as `D48`** — an id that does not distinguish two things it is being used to distinguish. If so it should be an instance under `D48` rather than its own number. Needs reading before I rule. |
| `R2-REQ-2` | `Condition.warmup_bars` declared and never consumed | **Likely an instance of `D46`** (documented inputs the code does not read) rather than a new number. |
| `R2-REQ-3` | two defects in the news conditions, **described not numbered** | Filed correctly under `R-9`. Numbers next turn. |
| `R3-REQ-2` | an exogenous-entry replay harness, "the only route to trade-level pairing" | **The most consequential of the seven** — if pairing at trade level genuinely requires new harness code, `R-6`'s cost estimate is wrong and the Tier-1 queue needs re-planning. Do not start building it before I rule. |
| `R3-REQ-3` | R3's round-1 dispatch told it to write `OPEN_QUESTIONS.md` directly; it switched to `msgs/` | **Accepted, no ruling needed.** `OWNERSHIP.md` already declares this the live exception and instructs exactly the switch R3 made. Recording it was right. |
| `BT2-REQ-1` | `features.py`'s news lookback is 2 days back against 45 forward | Likely a `D<n>`; it is an asymmetry that would silently truncate `minutes_since_high_impact`. |
| `BT2-REQ-2` | no flatten-before-the-print exit, and `II-11` as operated needs one | Likely a named missing primitive for `R2-D3`, not a defect. |
| `BT2-REQ-3` | the event family may be unmeasurable at 60m; finer frames are ~2 months | **Cross-links `R-7` and `MGR-T6`** — this is the second track to hit the sample-substrate wall, which raises `MGR-T6`'s priority. |

**What ADJ-11 costs.** Triaging seven requests instead of ruling them leaves seven agents partly
blocked on my next turn, and two of the triage lines above ("likely an instance of `D46`", "likely the
same family as `D48`") are guesses I have labelled as guesses. The alternative was ruling nine requests
at the speed I ruled the first eight and getting some of them wrong silently, which is worse — `R-9`
and `R-11` both exist because this turn's careful rulings caught things a fast ruling would have
missed. **The `RECEIVED` status on the board is a promise, and if it is still `RECEIVED` two turns from
now that is a failure of mine, not a backlog.**

### ADJ-11d — Two process notes, because both are cheap to fix and expensive to rediscover

**1. R3 and BT3 raced, and the fidelity loop ran open-loop on one side.** BT3 posted its eight
questions at 02:12; R3 ruled at 02:16 **from the code**, having checked `msgs/` when it held only `01`
and `02` `[repo-verified: msgs/03_R3_BT3_re-verify-ALGO-1.md, opening paragraph]`. R3 handled it
correctly — it ruled rather than leave BT3 blocked, and invited a re-ask "on the difference only". But
the outcome is that **four choices R3 inferred are ruled, and two of BT3's eight — Q1 (the population
unit, where 176 independent accounts and one pooled account disagree 24×) and Q3 (exposure keyed by
symbol or strategy) — are not**, because those ask for the *finding's intent* and cannot be answered
from a code read. **`MGR-T10` therefore survives, narrowed to the residual**, and the fix is mine: the
board must carry **which `VERIFY.md` question numbers are open**, so a researcher ruling from code can
see what it has not covered. Added to `BOARD.md` §6.

**2. `check_refs.py` still has no manager issuer, so `R-12` stands.** The parent touched `REGISTRY.md`
and `check_refs.py` at 02:10 but the `ID` regex is unchanged — issuer alternation is still
`(R[123]|BT[123]|DISC)-` with no `T` kind
`[measured: sed -n '/^ID = re.compile/,/^)/p' check_refs.py]`. Every message I posted this turn cites a
registry-legal anchor id, and `check_refs.py` passes `13 checked, 4 pre-registry, every one
resolvable`. **Nobody may put an `MGR-T` id in a `RE:`/`ALSO:` header yet.** Re-requested in
`msgs/06`.

**3. `R-9` propagated within the hour, which is the cheapest evidence that these rules travel.**
`R2-REQ-3` is titled "two defects in the library's news conditions, **described not numbered (per
`R-9`)**" — a rule written in `ADJUDICATIONS.md` this turn, cited by name by another agent before the
turn ended. That is the board working as a shared artefact rather than as my notes.

---

## ADJ-12 — Round 3's defect allocations: **D50–D58**, two instances added to existing classes, four declines

**2026-09-27 04:05 ET.** Nine agents reported or are in flight since ADJ-11. Under **`R-9`** every one
of them described a defect and named no number, which worked — no collision this round. The backlog
was mine and it is cleared here.

### The pattern first, because it is worth more than any single number in the table

**Six of the register's entries are now the same mechanism: a defect whose signature is a null.**
`D38` (silent key absence read as warm-up), `D42` (a leaking control that is conservative-only),
`D44` (a bootstrap that discounts the start of every series), `D48` (both arms colliding into one
result with a between-arm difference of exactly zero), and now **`D51`** (two bar boundaries in one
minute collapsing into one bar with no warning) and **`D57`** (a filter that is the identity function,
so its A/B is a comparison between a strategy and itself). R5 named this shape as the fifth instance
before I did `[repo-verified: msgs/R5-01_manager_main01-scope-substrate.md, "a fifth false-null
mechanism"]`; R6's `D12` finding is the same observation from the reporting end — the published
corpus has exactly one sentence licensing nulls as results, and no guard on the list that sentence
rests on can see a detector that never fired.

**So the allocation table below is grouped by harm, not by discoverer**, and the first group is the
one to read.

### Group 1 — false-null generators. A number from an affected path cannot be distinguished from the finding

> **D50 — `align_bucket` ignores `minutes` for every request ≥ 1440, so `FRAMES[1440]` holds the
> daily series twice.** `data/bars.py:145-149` takes the `minutes >= 1440` branch for **every**
> coarser request and returns the CME trading-day start without reading `minutes` at all
> `[repo-verified: futures_agents/data/bars.py:144-149]`, so
> `align_bucket(ts, 1440) == align_bucket(ts, 7200) == align_bucket(ts, 10080)` for every timestamp
> `[measured, R4: BRIEF.md:405-409]`. `resample(daily, 7200)` therefore emits **one bar per trading
> day, OHLCV bit-identical to the daily series in order — 2510/2510 MGC, 1858/1858 MNQ, 1858/1858
> MES** — labelled `Bar.minutes = 7200`, and because `end_ts = ts + 7200 minutes` the alignment
> pointer lags the daily one by **2–4 bars**. `FRAMES[1440] = [1440, 7200]` is the shipped daily
> frame `[repo-verified: futures_agents/scout.py:58-67]`. **Consequence: every daily-timeframe
> multi-timeframe statement in this repository is a lagged-autocorrelation test on one series.**
> `mtf_not_conflicted` — PULLBACK's unconditional base filter — passes 99.1% / 99.3% / 99.6% at
> 1440m as a direct consequence, i.e. it is not a filter there. Found by R4 (`R4-M3`, filed as
> `R4-REQ-1`). Blast radius being quantified by **BT4**. Status: open. Fix: one branch plus one
> regression test asserting `align_bucket(ts, 7200) != align_bucket(ts, 1440)`.

> **D51 — `BarSeries.append` silently replaces on an equal timestamp and never enforces
> contiguity.** It raises on a duration mismatch `[repo-verified: futures_agents/data/bars.py:
> 192-195]` and on out-of-order input `[:199-202]`, but on an **equal** timestamp it takes
> `# Same bucket: replace` → `self._bars[-1] = b; return` `[repo-verified: :203-207]`, and there is
> no check anywhere that bar *i+1* begins where bar *i* ends. The replace is correct for its stated
> purpose — a developing bar being finalised — and **wrong for every other caller**, because any two
> constructed bar boundaries landing in the same minute collapse into one bar with no warning and no
> counter. **Consequence: at the fine end of any constructed-bar size range this is a correctness
> failure, not an accuracy one**, and its signature is an attenuated or exactly-zero difference,
> indistinguishable from this programme's settled nulls. Fifth member of the false-null family after
> `D38`, `D42`, `D44`, `D48`. Found by R5 (`MAIN-01` scope, `research/R5_SCOPE.md` §S1a;
> `msgs/R5-01_manager_main01-scope-substrate.md`). Status: open. Fix: a `collapsed` counter on the
> replace path and an optional contiguity assertion — **not** a behaviour change, because the
> finalising-bar caller depends on the current semantics.

> **D57 — `outside_news_blackout` is the identity filter on a `:00`-aligned grid.** The blackout is
> 25 minutes wide, `[-10, +15]` around a print `[repo-verified: futures_agents/config.py:410-411]`,
> and five of the six HIGH `ECON_RULES` print at `:30`. On a `:00`-aligned grid at any timeframe
> ≥ 30m a `:30` print's window spans `:20`–`:45` and **contains no bar open at all**. Measured bars
> removed at 60m on `csv/raw`: **MGC 0 of 1,093**, MNQ 7 of 1,310 (exactly its seven FOMC Statements,
> the only `:00` rule), MCL 9 of 1,320 `[measured: BT2, backtest/BT2/ALGOS.md:254-261]`.
> **Consequence: an `outside_news_blackout` A/B on MGC at 60m is a comparison between a strategy and
> itself, and its null is guaranteed.** Found by BT2, verified independently by R2 (`R2-REQ-3`
> defect 2b). The live risk is already closed — R2 ruled it out of BT2's primary arm
> `[repo-verified: msgs/06_R2_BT2_re-verify-ALGO-1.md §3.1]` — so this entry exists so the next agent
> does not rediscover it. Status: open. Fix: widen the window to cover the bar containing the print,
> or evaluate news proximity at the bar's close rather than its open.

### Group 2 — a published result is about a different object than its label says

> **D52 — at daily frequency the `vwap` group is a bar-shape group, and one of its members is
> arithmetically impossible.** Same root cause as **`D45`** — `vwap_bands`' σ is a session-to-date
> volume-weighted dispersion resetting at the 18:00 ET anchor — but a **different consumer, a
> different harm and a different fix**, which is why it is numbered separately rather than appended
> to `D45`. On a 1440m series every bar *is* a session, so band-1 half-width is **< 1 tick on
> 2511/2511 MGC and 1859/1859 MES daily bars**; the rate is 7.5–8.9% at 60m and 19.8–21.8% at 240m
> `[measured, R6: vwap_bands(bars,"session",(1.0,2.0)) over csv/raw against the contract's tick
> size]`. On the published daily frame `[1440, 7200]`: `above_vwap` fires 92.4% / 99.7%,
> `vwap_band_extension` 99.8% / 100.0%, **`vwap_band1_bounce` 0 / 2511 and 0 / 1859**, and
> `above_vwap`'s direction equals `candle_close_strength`'s on **1092/1092 and 919/919** co-firings
> `[measured, R6: CONDITIONS[name].fn(frame.snapshot(i), 1440) on every snapshot]`. `above_vwap`'s
> test collapses to `px > (H+L+C)/3`, i.e. `2C > H+L`, i.e. `sign(CLV)`
> `[repo-verified: futures_agents/strategies/library.py:314-324; indicators/volume.py:95-104]` — so
> the docstring's own account of the defect it fixed, "as `close != vwap` this fired on 99.99% of
> bars" `[repo-verified: library.py:296-305]`, **describes the daily behaviour exactly: the fix is
> void at 1440m.** `vwap` is **VWAP's required group** `[repo-verified: combinator.py TEMPLATES]`, so
> this sits inside a template's required slot and cannot be configured around. Blast radius, from
> R6's audit: two published rows **INVALID** (`A16`, the daily VWAP rows) and four **WEAKENED,
> strongly** (`A15`, the 4h VWAP rows). Found by R6 (`R6-D1`, `research/R6_report_audit.md` §1).
> Verification in flight with **BT6**. Status: open. Fix: floor σ at one tick, or refuse the `vwap`
> group where the anchor period is not shorter than the bar.

> **D53 — a class: conditions and filters that accept a timeframe and read a different one.**
> Six instances, five inside `library.py` and one outside it. The class exists because the six were
> being cited as three unrelated researcher-local notes (`D-R1`, `D-V3`, `D-MTF3`) that a
> `DEFECTS.md` reader cannot find, and because **the harm splits in two and the split is what keeps
> this from being an over-retraction.**
>
> *The inert half is a forward hazard and reaches no published row.* Where `primary_tf = min(frame)`
> — which every published harness enforces, filtering `s.primary_tf == tf`
> `[repo-verified: workspace/bigscan/cell.py:88-90; workspace/studies/toolkit.py:158-161;
> workspace/chrono/ledger.py:38-41]` — reading every timeframe is identical to reading `from_tf =
> primary_tf`, so the inertness is invisible in every published cell (R6-M1).
>
> *The frame-dependence half bites, and harder than round 1 stated.* Because the timeframe actually
> read is chosen by the frame the runner built rather than by the strategy: `regime_trending` and
> `regime_ranging` swing **13 points** on an identical 5m base series as only `tfs` varies
> (MEAN_REVERSION's base filter 55.2% → 68.2% on MGC) `[measured, R1: R1_group_audit.md D-R1]`;
> `mtf_not_conflicted` — PULLBACK's base filter — swings **37 points** across the frames the reports
> used, 62.6% at 60m → 79.6% at 240m → 99.1% at 1440m, monotone in the cell's timeframe
> `[measured, R6: R6-M2]`; and at 240m `_default_regime_tf` falls through to `self.timeframes[-1]`
> `[repo-verified: futures_agents/features.py:820-826]`, so **every 4-hour strategy's regime and
> volatility base filters are read off the daily series** — with 23–27% of `volatility_normal`'s 240m
> passes being `RegimeSnapshot`'s `"NORMAL"` field default, and `regime_matches_direction` firing
> **188 of 188 LONG on MES at 240m** `[measured, R4: R4-V3, R4-R3]`.
>
> **Instances:** (1) `regime_trending`, (2) `regime_ranging`, (3) `regime_matches_direction` —
> `tf` accepted and unused `[repo-verified: library.py:752-754, 760-762, 768-774]`;
> (4) `volatility_normal`, which inherits it in full and is the base filter of **12 of 13
> templates**; (5) `mtf_not_conflicted`; (6) **`StrategyFilters.require_alignment` calls
> `snap.alignment()` with no argument** `[repo-verified: futures_agents/strategies/base.py:433-434]`
> — the one instance outside `library.py`, found by R6 because it is a `StrategyFilters` field and
> not a condition, and `features.py:725-741` names this exact call as the defect that made
> `mtf_aligned` blind. **Instance 6 is not a retraction**: `require_alignment >= 0.5` on MES 240m is
> the ranking report's one controlled positive in the index complex and it is **not** corrupted by
> this. Found by R1 (`D-R1`, `D-V3`), R4 (`R4-V3`, `R4-R3`, `R4-REQ-5`) and R6 (instance 6, and the
> harm split). Status: open. Fix: either honour the `tf` argument, or delete it from the signature so
> the frame-dependence is explicit at every call site. **`R4-REQ-5` is instance 3+4's consequence and
> needs no separate number** — it is routed to `MGR-T17`, which must know the 240m base filters are
> partly a dataclass default before it interprets a 240m comparison.

### Group 3 — a declared guarantee that is not enforced, and an identity that does not identify

> **D54 — a required group with no SIGNAL member is silently dropped, so `volume` is declared
> required by two templates and never enforced.** `_signal_pools` builds each group's pool from
> SIGNAL conditions only and then discards the empty ones — `return [p for p in required if p], …`
> `[repo-verified: futures_agents/strategies/combinator.py:361-369]`, with `if not required:
> continue` at `:513`. **Four groups contain zero SIGNAL conditions:** `volatility` 0/3, `volume`
> 0/3, `time` 0/4, `news` 0/3 `[measured, R4: over CONDITION_GROUPS + CONDITIONS[n].kind]`. `volume`
> is in `required_groups` for **MOMENTUM** `[repo-verified: combinator.py:215]` and **BREAKOUT**
> `[:268]`, and in both the requirement is inert. MOMENTUM is additionally the **one template of
> thirteen without `volume_not_thin` in `base_filters`** `[repo-verified: combinator.py:219]`, so a
> generated MOMENTUM strategy can contain no volume condition of any kind: **24 of 40 generated MNQ
> MOMENTUM strategies and 15 of 25 MCL contain none** `[measured, R4]`. **No published number is
> wrong; two rows of the published requirement map are.** It also makes R1's `D-M2` worse — a
> `rsi_extreme_reversal` MOMENTUM strategy is a mean-reversion strategy, and R1's mitigating clause
> "with a `volume` filter on it" is false in a majority of the sample. Found by R4 (`R4-M1`, filed as
> `R4-REQ-2`); **verified independently by R1** `[repo-verified: msgs/14_R1_R4_re-signal-pools.md]`.
> Status: open. Fix: raise on a `required_groups` entry with an empty pool, then decide per template
> whether to enforce, drop or document the requirement as advisory. **Do not silently delete the
> declaration** — the map is published.

> **D55 — `strategy_id` carries no partner provenance, so two different environments collide on one
> key and the second overwrites the first.** `strategy_id`'s hash inputs carry `self.symbol` and
> nothing about the frame's partner set `[repo-verified: futures_agents/strategies/base.py:612-620]`;
> `BacktestResult` records `strategy_id`, `symbol` and `primary_tf` and no partner field
> `[repo-verified: futures_agents/backtest/engine.py:79,134]`; and `performance_db`'s primary key is
> `(strategy_id, scope, regime, session)` `[repo-verified: futures_agents/storage.py:146]`. So a
> strategy holding a partner-bound condition, run against a frame **with** the partner and against
> one **without** it, produces two genuinely different results — the second declines on every bar —
> under one id, and the second **silently overwrites** the first. **Fourth instance of the
> identity-hash family**, after the `ExitModel.label` fix, `D43` (`StrategyFilters.label` omitting
> four behaviour-bearing fields) and `D48` (`replace` inheriting the memoised `_id`). **Zero current
> blast radius and it is a forward hazard by construction**: no partner-bound condition exists yet,
> and Wall A's spec is what creates one `[repo-verified: research/R2_wall_a_spec.md §9.2]`. Numbered
> now rather than when it bites, because `D43`'s history is that this family is discovered by having
> a result silently disappear. Found by R2 (`R2-REQ-1`). Status: open, not yet reachable. Fix: the
> partner set joins the hash inputs and the storage key, in the same edit as the Wall A schema.

> **D56 — the news proximity clock misreports in both directions. Two instances, one object.**
> *Instance 1 — the forward offset.* `post_news_window`'s description is "in the reaction window
> after a high-impact release" and its bound is `15 < since <= 60`
> `[repo-verified: futures_agents/strategies/library.py:1345-1359]`, but `since` is computed at the
> bar's **open** `[repo-verified: futures_agents/features.py:1023; data/bars.py:37]`, the signal is
> decided at the bar's **close**, and the entry fills at the **next** bar's open
> `[repo-verified: futures_agents/backtest/engine.py:290-292, :355]`. On a 60m frame an 08:30 print
> admits only the 09:00 bar, which fills at 10:00 — **90 minutes after the print**; generalised, the
> realised entry sits 60–120 minutes after the print while the condition claims 15–60, and the offset
> **scales with the timeframe and is undocumented.** Closest kin is `D39` (library ORB is a state,
> not an event, and silently widens), not `D46` — the code implements a different behaviour, it does
> not fail to read a documented input. Quantifiable today via BT2's `offset_min`.
> *Instance 2 — the backward truncation.* `SymbolFrame._build_news_proximity` projects events over
> `bars[0].ts − 2 days .. bars[-1].ts + 45 days` `[repo-verified: futures_agents/features.py:
> 952-959]`. The forward side carries a six-line comment justifying 45 days; the backward side is two
> days with no stated reason, so `minutes_since_high_impact` reports "no recent high-impact event" at
> the head of every series when there was one three days earlier. **Extent unmeasured — BT2 owes the
> bar count**, and until it lands this instance's blast radius is stated as unknown rather than
> small. Found by BT2 and verified independently by R2 (instance 1, `R2-REQ-3` defect 1); by BT2
> (instance 2, `BT2-REQ-1`). Status: open. Fix: instance 2 is a one-line symmetry change at `:955`;
> instance 1 is a behaviour change to a shipped condition and is **not** small — documenting the
> realised offset is the cheap half and is what the register needs.

> **D58 — a class: the catalogue contains duplicate predicates, and `GLOBAL_EXCLUSIVE` covers
> neither kind.** Two instances, two different fixes, one finding — stated as one entry because a
> reader needs both halves to know what a "two-signal confluence" means in a published row.
> *Instance 1 — a reachable cross-group duplicate, and it is a live false confluence.*
> `candle_close_strength` (`candlestick`), `delta_confirms_bar` and `cvd_directional` (`orderflow`)
> are the same close-location arithmetic in two groups; R1 measured them co-firing on **92–93% of
> bars** (`C-1`), and R4 measured them **co-occurring in generated strategies** — 8 REVERSAL and 4 of
> 16 LIQUIDITY in a 400-cap probe on MCL. Neither pair is in `GLOBAL_EXCLUSIVE`. **Consequence: a
> two-signal confluence that drew both is one reading counted twice and reported as agreement**,
> which bears directly on `BRIEF.md` rule 1, a published rule about signal *count*. Fix: add the two
> pairs to `GLOBAL_EXCLUSIVE`, or state why not.
> *Instance 2 — two provable same-group duplicates, where an exclusion cannot help.*
> `macd_hist_direction` has an identical fire-and-direction vector to `macd_directional` in **23 of
> 23 cells**, and `bollinger_extreme ⊂ bollinger_mean_pull` (601/601, 686/686, … in **8 of 8** cells,
> same direction) `[measured, R4]`. One condition per group means they cannot co-occur, so the harm is
> not confluence but **denominator inflation**: every MOMENTUM rule set has roughly a 1-in-6 chance
> of being a byte-identical twin of another carrying a different `strategy_id`, which is a `free_t`
> accounting question and shares `D48`'s exact-zero signature. Fix: delete a condition, plus the
> citation repair that forces. Found by R4 (`R4-REQ-3`), building on R1's `C-1`. Status: open.
> **ADJ-3's split trigger applied and not fired**: two instances, and splitting at two would leave
> two entries that must be read together.

### Instances added to existing classes — no new numbers

| existing | new instance | ground |
|---|---|---|
| **`D46`** (documented inputs the code does not read) | **inst. 3** — `Condition.warmup_bars: int = 50` is declared and consumed by nothing `[measured, R2: grep -rn "warmup" → 3 hits: base.py:102 the field, library.py:40 and :47 the setter]`, so a condition needing 200 bars of history is evaluated from bar 0 like any other | identical shape to inst. 1, the `estimated` flag. `R2-REQ-2` triaged this correctly and is **confirmed** |
| **`D46`** | **inst. 4** — `metrics.py:31` comments "*Bars per year* used to annualise the Sharpe/Sortino" above `TRADING_DAYS_PER_YEAR = 252`, but `per_year = m.trades_per_calendar_day * TRADING_DAYS_PER_YEAR` `[:214-215]` is computed from **trade timestamps** `[:199-208]`, so the annualisation does not scale by bar count and is clock-robust | the comment is wrong and the code is right — the rare case where a `D46` instance makes a task **cheaper**: two of discovery's four named `MAIN-01` architecture costs are not real (`costs.py` has **zero** `minutes` references `[measured, R5: grep -c → 0]`). Found by R5 |
| **`D47`** — **now a class**, renamed in effect from "`openinterest` conditions are structurally dead" to **"conditions that are structurally dead on a whole substrate, so every carrier is a guaranteed zero-trade evaluation"** | **inst. 2** — the three `news` conditions on every daily series. Every daily bar in `csv/raw` is stamped **00:00 ET** `[measured, R2: MGC_1d 2511/2511, MES_1d 1859/1859, SPY_1d 2512/2512]` and the six HIGH rules print at 08:30/10:30/14:00/14:30, so **`post_news_window` is identically FALSE** and `no_imminent_release` and `outside_news_blackout` identically TRUE on every daily series — two constant no-ops and one total veto | `R2-REQ-3` defect 2(a) proposed exactly this and it is right. **R6 bounds the blast radius to zero and that bound is part of the entry**: `post_news_window` appears in **no** template's `base_filters` or `optional_filters` `[measured, R6: post_news_window in templates → []]`, so the combinator cannot emit a carrier; the only study that reached it by hand is `research/confluence/reversion_specialist.md` F11, not a `scan_reports/` result. **It invalidates F11's null and nothing published** |

### Four declines, each with the reason, because a decline is a ruling

1. **`R4-REQ-4` — `scout.rank` raises `KeyError` on 30m, a timeframe `FRAMES` declares supported.**
   `rank`'s `suffix` dict covers `{1440, 240, 60, 15, 5}` `[repo-verified: scout.py:219]` against
   `FRAMES`' `{5, 15, 30, 60, 240, 1440}` `[:58-67]`. **No number.** It is a live-path bug with no
   research consequence, and R4's point is the one that matters: the same mismatch makes the
   `FRAMES.get(timeframe, [timeframe])` fallback at `:230` unreachable, **and that unreachability is
   currently the only thing preventing the frame-of-one VOID from contaminating anything** (0/N in 23
   of 23 cells, `R4-MT1`). Board task, trivial, with the warning attached: **do not "fix" the
   fallback without fixing the frame-of-one VOID it is hiding.** This is the nit class and numbering
   it would spend register credit for nothing.
2. **`BT2-REQ-2` — no flatten-before-the-print exit.** **Not a defect; a named missing primitive**,
   routed to R2 for `R2-D3`. The engine evaluates conditions for strategies *not already positioned*,
   so every filter in the library can only prevent initiating; an event-driven exit is a capability
   the engine does not have, not one that is broken. **And the price has just fallen**: EF1 has built
   a clock-driven forced flat for the edge programme (`edge/EF1/code/`, component 1b), so extending
   an existing forced-flat hook to a calendar event is a smaller job than when BT2 asked. BT2 and R2
   read EF1's code before specifying anything.
3. **`R4-REQ-5` — the 240m `regime_tf = 1440` finding.** **No separate number: it is `D53`
   instances 3 and 4 in their sharpest form.** Its consequence is routed, as R4 asked, to
   **`MGR-T17`**, which is re-reading stop geometry at 240m and must know that the 240m row's regime
   and volatility base filters are read off the daily series — and that 23–27% of
   `volatility_normal`'s 240m passes are a dataclass default — before it interprets a 240m
   comparison.
4. **The misfiling itself — `rsi_extreme_reversal` and `stoch_extreme` filed under `momentum`.**
   No number. It is a taxonomy judgement, and ADJ-9b is the precedent: a specification being wrong
   for one consumer is a design call, not a defect. Its *measured* consequence is already numbered
   through **`D54`**, which is what removes the mitigating clause R1 attached to `D-M2`. It gets a
   **vocabulary verdict** instead — see ADJ-13.

**What ADJ-12 costs.** Nine numbers in one turn against 43 in the programme's whole prior history,
and I am the one who wrote that "the register's value is inversely proportional to how many entries
are nits" (ADJ-3). Three defences, and they are partial. Every one of the nine has a measurement and
a distinct fix; two of the nine (`D53`, `D58`) are classes that *absorb* items which would otherwise
have been four more numbers; and four candidates were declined and two more folded into existing
classes, so the turn's gross was fifteen and the net is nine. The real cost is elsewhere: **`D52`
puts two published rows in the INVALID column and four in strongly-WEAKENED, and `D50` puts a caveat
on the daily row of every multi-timeframe result in the corpus.** Neither is discharged by numbering
it. `D50`'s is assigned — BT4 — and `D52`'s verification is with BT6; `D52`'s *reporting* consequence
for `scan_reports/` is not assigned to anyone and I am recording that as an open obligation rather
than pretending otherwise.

---

## ADJ-13 — The two vocabulary gaps: **VOID adopted with a three-part amendment**, and **`MISFILED` added**

**2026-09-27 04:05 ET. Ruling on `R1-REQ-5` (as already actioned in `BRIEF.md`) and on the gap R4
raised at `research/R4_group_audit.md:1423-1426`.**

### ADJ-13a — One vocabulary, not two. `BRIEF.md`'s table is canonical and ADJ-8's four-term set is retired

**The problem is real and it already cost an agent a turn.** `ADJ-8` fixed **PROXY / DEGRADED /
HONEST-DERIVED / HONEST-DERIVED-BUT-BROKEN** as the shared set so three auditors would stay
comparable. R1 then used **CLEAN / HONEST-DERIVED / PROXY / DEGRADED / DEAD / MISNAMED**, R4 was
dispatched with **CLEAN / PROXY / DEGRADED / DEAD / MISNAMED**, and R4 had to **write a translation
table** to make its 31 verdicts collate with mine `[repo-verified: R4_group_audit.md:1410-1421]`.
The parent has since added **`VOID`** to `BRIEF.md` inside a six-term table. So there are two
vocabularies, and the instruction not to leave two definitions is right.

**Ruling: `BRIEF.md`'s six-term table is the single canonical audit vocabulary. `ADJ-8`'s four-term
set is retired.** Three reasons, and the third decides it:

1. It is the set the auditors actually used. Three of four (R1, R4, and R6's condition-level
   verdicts) used `CLEAN`/`MISNAMED`/`DEAD`; **nobody used `HONEST-DERIVED-BUT-BROKEN` except by
   translation.** A fixed vocabulary that has to be translated is not fixed.
2. The mapping is lossy in exactly one direction and `BRIEF.md`'s is the finer side.
   `HONEST-DERIVED-BUT-BROKEN` collapses two things R4 keeps apart: *wrong field or window*
   (`volatility_compressed`, `volatility_expanding`, `mtf_strongly_aligned`) and *right arithmetic,
   wrong group* (`rsi_extreme_reversal`, `stoch_extreme`). That second thing is ADJ-13b.
3. **`BRIEF.md` is read by all twelve live agents including the seven on the edge programme;
   `ADJUDICATIONS.md` is read by the ones who are told to read it.** A vocabulary that lives where
   only some agents look is the failure mode `REGISTRY.md` exists to prevent.

**Mapping, ruled, so no existing citation breaks.** `ADJ-8`'s terms remain *readable* forever and are
not to be used in new work:

| `ADJ-8` term (retired) | canonical term | note |
|---|---|---|
| `HONEST-DERIVED` | **`CLEAN`** | R4 already mapped its 20 this way |
| `HONEST-DERIVED-BUT-BROKEN` | **`MISNAMED`** | where the loss is a wrong field or window |
| `HONEST-DERIVED-BUT-BROKEN` | **`MISFILED`** | where the arithmetic is right and the *group* is wrong — new, ADJ-13b |
| `PROXY` | `PROXY` | unchanged |
| `DEGRADED` | `DEGRADED` | unchanged |
| — | `VOID`, `DEAD` | added by `R1-REQ-5`; `DEAD` was already in R1's set |

**`VOID` is adopted, with a three-part amendment.** `BRIEF.md` defines it as "cannot fire in this
configuration — 0 of N bars, structurally, not rarely", stated **per (symbol, timeframe), never
global**. That is right and it is not enough coordinates, and three independent measurements say so:

- **(i) VOID depends on the *frame*, not just the timeframe.** `mtf_aligned` is VOID at 0/N in **23
  of 23 frame-of-one cells** and alive in **all 23 corpus cells** at the same (symbol, timeframe),
  firing 201–1,791 times `[measured, R4: R4-MT1]`. "VOID at 1440m" read as a property of the daily
  bar, when it is a property of `FRAMES[1440]`, is precisely the error `D50` is made of.
- **(ii) VOID depends on a *scope flag* where one decides it.** `session_extreme_sweep` is VOID under
  `rth_only=True` on **314/314** generated strategies `[measured, R1]`, and `rth_only` is the
  generated default on **184/184 MGC and 167/167 MCL** `[measured, EF2]`.
- **(iii) A VOID verdict must state its *reachability*, and this is the amendment that matters
  most.** R6 spent its §2 establishing that five round-1/2 findings **cannot have reached any
  published row**, `D-MTF1` among them, because every published harness trades the lowest timeframe
  of its frame and `FRAMES` always places at least one timeframe above it
  `[repo-verified: workspace/bigscan/cell.py:88-90; workspace/studies/toolkit.py:158-161;
  workspace/chrono/ledger.py:38-41; futures_agents/scout.py:58]`. A VOID configuration that the
  corpus never builds is a **forward hazard**, not a retraction — and 62% of audited claims stood
  partly because R6 drew that line before drawing any other.

> **Ruling, binding: a `VOID` verdict is stated per (symbol, timeframe, frame) — plus the value of
> any scope flag that decides it — and it carries a reachability line: `REACHED` (the corpus builds
> this configuration; a published row may be affected) or `FORWARD` (it does not; this is a hazard
> for future work).** A VOID verdict with no reachability line is incomplete, in the same way a
> result with no placebo is incomplete under `R-2`. Standing rule **`R-14`**.

**What this costs.** Three coordinates and a reachability tag make a VOID verdict roughly twice as
expensive to write as R1 and R4 wrote theirs, and the six already on the record were written to the
looser standard, so **they need a reachability pass nobody has been assigned.** I am not assigning it
this turn; R6 has in effect done it for the four it touched and the gap is the other two. Recorded as
an open obligation.

### ADJ-13b — **`MISFILED`** added: the arithmetic is honest and the group is wrong

**R4's gap is real and it is not cosmetic.** `MISNAMED` is about a condition's own name against its
own arithmetic — a reader who sees it re-reads the docstring. R4's two conditions are not that:
`rsi_extreme_reversal` and `stoch_extreme` compute honestly what their names say, and what is wrong is
that they are filed in **`momentum`** when they are mean-reversion predicates. The same defect at
group scale is the whole of R1's `momentum` verdict (`MISNAMED` at the group level).

**Why it needs its own term rather than an extension of `MISNAMED`: the fix and the harm are both
different, which is the same test I applied to `D52` against `D45`.**

- **Different file.** `MISNAMED` sends the reader to the condition's docstring; `MISFILED` sends it
  to `CONDITION_GROUPS` and `TEMPLATES`.
- **Different harm, and it is the load-bearing one.** Group membership is not a label here — it is
  the selection mechanism. `_signal_pools` draws from `required_groups` and `optional_groups` by
  group `[repo-verified: combinator.py:361-369]`, so **a template that requires `momentum` can have
  that requirement satisfied by a mean-reversion predicate**, and every published `scan_reports/`
  result is grouped by the 13 strategy groups that are assembled from these condition groups. A
  `MISFILED` condition therefore corrupts a template's requirement semantics *and* a published group
  label; a `MISNAMED` one misleads a reader.

> **`MISFILED` — the arithmetic is honest and computes what the condition's own name says, but the
> condition group it is filed under names a different mechanism. So a template requiring that group
> can be satisfied by a predicate from another, and any result grouped by it carries the wrong
> mechanism label.** Stated with the group it belongs in, not only the one it is in.

**Two consequences, routed rather than applied.** R4 re-files `rsi_extreme_reversal` and
`stoch_extreme` as `MISFILED` (from `MISNAMED`) in its own file, and R1 restates the `momentum` group
verdict as "MISFILED-bearing: 2 of 6 members belong in `meanreversion`, which is what makes the
group's name misdescribe its contents". **Neither verdict is overturned and neither changes sign** —
this is a relabelling that makes the fix findable. I do not edit either file.

**What ADJ-13 costs.** A six-term vocabulary plus `MISFILED` is seven verdicts and a three-coordinate
`VOID`, for a task R1 originally did with three terms. Every term earned its place by a measurement,
and the system is now at the size where a *seventh* would need to displace one rather than be added
— I am recording that ceiling now so the next addition is a trade rather than a drift, the same
mechanism as ADJ-3's split trigger. And retiring `ADJ-8`'s set means `ADJ-8` now contains a fixed
vocabulary that is no longer fixed; the mapping table above is the only thing preventing that from
being a trap, and mapping tables erode exactly like the substrate labels in ADJ-6 do.

---

## ADJ-14 — **`BRIEF.md` rule 2's scope, ruled explicitly.** Narrowed in three places, retracted in none

**2026-09-27 04:05 ET.** The most consequential ruling on my desk this turn, and the one where
over-retraction costs as much as under-retraction. Rule 2 reads:

> **2. Multi-timeframe agreement is not a virtue.** Requiring any alignment measured detectably
> *worse* than requiring none (z = −4.09). On a two-timeframe frame, "majority" and "unanimous" are
> the same statement (D17). `[repo-verified: BRIEF.md:37-40]`

**Two round-3 findings bear on it and they appear to pull in opposite directions. They do not, and
resolving that is the ruling.**

- **`D50` (R4-M3) contaminates.** At 1440m the confirming series **is** the primary series, lagged
  2–4 bars and OHLCV bit-identical (2510/2510 MGC, 1858/1858 MNQ and MES). So at the daily row,
  "agreement" is a lagged-autocorrelation test on one series, and part of rule 2's evidence came from
  a frame that cannot disagree with itself.
- **`R6-M1` decontaminates.** `D-MTF1` — both MULTI_TIMEFRAME signals dead at the frame's top
  timeframe — **reaches no published row**, because all three harnesses trade the *lowest* timeframe
  of their frame and `FRAMES` always places at least one timeframe above it. Measured:
  `mtf_aligned` fires **1153/2511 (MGC)** and **976/1859 (MES)** at 1440m in `[1440, 7200]` — alive,
  not dead.

**They are about different things, and that is why both are true.** `R6-M1` removes the *dead
detector* explanation; `D50` supplies a different one — a **live detector reading a degenerate
confirming series.** A detector reading a series against a lagged copy of itself fires plenty; it
simply is not measuring multi-timeframe agreement. So the finding is not "the arm was empty" but
"the arm measured something else". Nothing here licenses a retraction, and nothing here leaves
rule 2 as stated.

### 1. What survives, unchanged and citable

**The 60-minute evidence is intact.** At 60m in `[60, 240, 1440]` the three series are genuinely
distinct — `D50` aliases only requests **≥ 1440** against 1440, so it does not touch a 60m or 240m
confirming pointer. `mtf_aligned` and `mtf_strongly_aligned` differ on **248–314 bars** at 60m
`[measured, R4: R4-MT2]`, so the graded/binary distinction has content there. `R6-M1` confirms the
detector fired in every published cell. And the comparison itself is **within-population, same bars,
same measurement, both arms drawn from one generation** — the structural immunity that makes `D8`
("selecting is worse than not selecting") the most robust claim in the corpus applies to it in the
same way: a dead or degenerate detector is in both arms or in neither.

**Rule 2's second sentence survives as written, and this is the conservative catch of the ruling.**
R6 graded `B13`'s *"Unanimity versus majority: no detectable difference"* as **INVALID — measured
nothing (DEGENERATE)**, because `mtf_strongly_aligned` and `mtf_aligned` return identical
`(triggered, direction)` on **100% of 240m bars (1348/1348 MGC, 1347/1347 MES) and 100% of 1440m bars
(2511/2511, 1859/1859)**, and 93.7–95.0% at 60m. But **rule 2 does not make `B13`'s claim.** It says
the two "**are the same statement**" and cites `D17` — an assertion of identity, which is exactly what
R6 measured. R4 strengthens it from measured to **provable**: two agreeing voters give `|a| ≥ 0.569`
and two disagreeing give `|a| ≤ 0.14` in every corpus frame `[measured, R4: R4-MT2]`. **The report
claim is invalid and the rule derived from it is right.** Rule 2's sentence 2 stands.

### 2. What is narrower than stated — three narrowings, each with a measurement

**(a) The 1440m arm is not evidence about multi-timeframe agreement at all.** `FRAMES[1440] =
[1440, 7200]` `[repo-verified: scout.py:58-67]` and `D50` makes 7200 the daily series lagged 2–4
bars. Any contribution the daily row made to z = −4.09 is evidence about autocorrelation, filed under
agreement. **The magnitude is unmeasured and that is the whole open question** — see §5.

**(b) The 240m arm tested one signal, not two.** `mtf_strongly_aligned ≡ mtf_aligned` on 1348/1348
and 1347/1347 bars `[measured, R6: R6-M2]`, so "requiring *any* alignment signal" at 240m is
"requiring `mtf_aligned`", and the population of distinct alignment conditions in the 366 is smaller
than the phrase implies.

**(c) Rule 2 must not be applied to the filter member.** `mtf_not_conflicted` is PULLBACK's
**unconditional base filter** `[repo-verified: combinator.py TEMPLATES]` and its pass rate runs
**62.6% at 60m → 79.6% at 240m → 99.1% at 1440m**, monotone in the cell's timeframe
`[measured, R6: R6-M2]`, a **37-point swing** produced by the frame the runner built. So every
PULLBACK row in every published per-timeframe table carries a veto that loosens from 37% of bars to
1% of bars as the timeframe rises, and no report records it. A rule reading "requiring alignment is
worse" says nothing about a veto whose strength is set by the frame rather than the strategy.
(`D53` instance 5.)

### 3. What rule 2 must not be cited for — five prohibitions

1. **Not** for "unanimity versus majority makes no detectable difference" **as an empirical result.**
   It is an arithmetic identity on every frame the programme used. Rule 2's own phrasing is correct;
   `B13`'s is the INVALID form and must not be restated in any future study.
2. **Not** for any claim about the **daily row**, in either direction.
3. **Not** as evidence that `mtf_aligned` is a **dead or absent detector.** It fired in all 23 corpus
   cells, 201–1,791 times `[measured, R4]`, and 1153/2511 at 1440m `[measured, R6]`. `D-MTF1`'s
   VOID configuration is `FORWARD`, not `REACHED` (ADJ-13a(iii)).
4. **Not** as a reason to omit an alignment arm in the **edge programme.** Rule 2's evidence is
   frame-specific and the edge programme builds frames the corpus never built (`[60, 240]`,
   `[5, 15, 30]`). An EF agent dropping alignment on rule 2's authority is citing a frame-dependent
   result outside its frame — which is `R-11` in its original form.
5. **Not** as "multi-timeframe agreement does not work." R1's own verdict is the sentence to carry:
   "**Whether multi-timeframe alignment helps is therefore still an open question here, not a settled
   negative**" `[repo-verified: research/R1_group_audit.md, Group 9]`.

### 4. The restatement, for `BRIEF.md` rule 2 and the matching `CALLOUT.md` rule

Routed to the parent; I own neither file. R6 flagged the `CALLOUT.md` propagation and it must travel
with this, or the operating brief keeps the un-narrowed form.

> **2. Multi-timeframe agreement has not been shown to be a virtue.** Requiring an alignment signal
> measured worse than requiring none on the 60-minute frames the corpus built (z = −4.09, 366 vs
> 1,151) — in an implementation where the graded and binary conditions are the **same function** at
> 240m and above, and where the daily frame's confirming series is the primary series lagged 2–4 bars
> (`D50`). "Majority" and "unanimous" are the same statement on these frames by **arithmetic, not by
> measurement** (`D17`, `R6-M2`). Do not apply this to `mtf_not_conflicted`, whose veto strength is
> set by the frame rather than by the strategy (`D53`). **Whether multi-timeframe agreement helps is
> an open question here, not a settled negative.**

### 5. The one measurement that would close this, pre-registered

Narrowing (a) is currently qualitative and I will not leave it there. **BT4 owes two numbers as part
of `D50`'s blast radius:** the count of `primary_tf = 1440` rows inside the 366-strategy and
1,151-strategy populations behind z = −4.09, and **the same z recomputed with those rows excluded.**

- If z survives exclusion, narrowing (a) **costs nothing** and rule 2's first sentence is restored
  to its full published scope with a footnote.
- If z does not survive, rule 2's first sentence is a **60m/240m result** and must say so.

Either outcome is cheap, and it is the shape `R-11` demands: name the dimension and measure it rather
than reason from volume.

### 6. Conservatism, stated so it can be checked

**Nothing is retracted.** z = −4.09 stands as measured. Rule 2 stays on the list of eight. **Rules 1,
3, 4, 5, 6, 7 and 8 are untouched by this ruling** — R6 graded 1, 3, 4, 5 and 7 as standing, rule 8's
ORB half as standing, and rule 6 as surviving with its `avoid_lunch` evidence weakened on MGC only.
And one I am declining to touch on purpose: **rule 5** ("no intraday entries 15:00–16:00 ET",
z = −4.43, replicated) is newly load-bearing, because the edge programme's session rule puts a forced
flat at 16:00 ET and therefore concentrates activity in exactly that hour. No round-3 finding touches
it and I am not narrowing it by association.

**What ADJ-14 costs.** Three narrowings and five prohibitions make rule 2 the most expensive rule on
the list to cite correctly — seven clauses where there were two — and a rule that is expensive to
cite correctly gets cited incorrectly. The mitigation is that the restatement in §4 is one paragraph
and is the only form anyone should quote. The second cost is sharper: I have made a published,
replicated, negative finding **conditional on a measurement that does not yet exist**, and if BT4's
count never lands, rule 2 sits in a narrowed-but-unquantified state indefinitely — which is a worse
place than either end. That is a real risk of this ruling and the reason §5 is a pre-registration
rather than a hope.

---

## ADJ-15 — The edge programme, folded into the board. Three arithmetic constraints, one hard gate, one new rule

**2026-09-27 04:05 ET.** Seven agents (EF1–EF7) are working an **account-owner request** that arrived
outside the research pipeline: top 10 per symbol for swing and for scalp on MGC/MCL/MES/MNQ, inside an
18:00→16:00 ET session rule `[repo-verified: edge/EDGE_BRIEF.md]`. It is not a `MAIN-<nn>` and I am
not decomposing it — the EF agents have already cut it into cells by (setting × symbol pair ×
timeframe band), the brief assigns the deliverable file to the parent, and `PIPELINE.md` §2's
prohibition on my decomposing a task I did not scope applies with more force here, not less, because
the requester is not in the room.

**What the board owes it is four things: the measured constraints as *binding facts* rather than as
findings in seven separate files, the gate structure, the ids, and the one rule this programme needs
that the research pipeline did not.**

### ADJ-15a — The hard gate: no EF profitability number is reportable until EF1's harness is validated

EF1 built the clock rule, ran it three-armed, and **its own gate failed**: 33 `SPANS_WINDOW`
violations, all at `primary_tf = 240m`, all on sessions with no bar at the deadline
`[measured, EF1: edge/EF1/bursts/03, workspace/developer/ef1_validation_swing_60m.json]`. EF3 built a
second harness independently, ran both over the same 400 MES strategies, and audited both with EF1's
own `violations()`: **EF1's 43 `SPANS_WINDOW`, max hold 71.0h, 19 holds over 22 hours; EF3's 0, max
hold 21.0h** `[measured, EF3: msgs/EF3-01_EF1_session-rule-misses-early-close-sessions.md]`.

**Two harnesses disagree on whether the defining rule of the programme is being enforced.** EF4 has
already drawn the right conclusion unprompted: "until EF1 declares validation, every profitability
number on this page is provisional and is not a programme result"
`[repo-verified: edge/EF4/FINDINGS.md]`.

> **Ruling: `R-5` applies to a harness component exactly as it applies to an algorithm.** A
> profitability number from an unvalidated session harness is **not weak, it is unknown** — nobody
> can say what rule the trades obeyed. Validation means EF1's `violations()` returns **zero**, or
> returns a **named, enumerated carve-out** with the sessions listed and the information it consumes
> stated. Standing rule **`R-13`**.

**And the disagreement is the most valuable thing the edge programme has produced so far**, because it
is two independent implementations of one rule differing by a measurable amount on a stated
population. Neither agent should yield to the other on authority: EF3 measured 0 with no carve-out, so
either EF1's carve-out is unnecessary or EF3's harness is silently doing something EF1's refuses to.
**Reconciled bar-for-bar on the 19 sessions, not argued.** That is `MGR-T19`.

### ADJ-15b — Three arithmetic constraints, now board facts

These are not interpretations and they are not negotiable, which is why they belong on the board
rather than in seven `FINDINGS.md` files where a later agent can miss one.

**1. Swing cannot exceed 22 hours, and the budget shrinks linearly through the cycle.** A position
opened at *T* must be flat at that cycle's 16:00, so the hold available is `16:00 − T`. **22 hours is
reachable only from an 18:00 ET entry**; from MGC's RTH open (08:20) the budget is **7h40m**, from
MCL's (09:00) **7h00m**, from 15:00 one hour `[measured, EF2: edge/EF2/FINDINGS.md F1a]`.
**"Swing" here is a hold budget that shrinks through the day, not a duration.** A thesis needing three
days is not testable under this rule and must be declined rather than truncated.

**2. The rule needs new code, and the new code has already produced one defect of its own.**
`exit_at_session_close` fires at the **contract's** RTH close —
`minutes_since_open(bar.ts, spec.rth_open) + bar.minutes >= self._rth_minutes`
`[repo-verified: futures_agents/backtest/engine.py:470-473]` — which is 13:30 for MGC and 14:30 for
MCL, not 16:00; and it is gated on `not self.allow_overnight`, so turning overnight on **removes** the
session exit rather than moving it. `allow_overnight` is `True` at **no call site anywhere in the
tree** `[repo-verified: grep → engine.py:233, 241, 470 only]`, so all ~2.97M prior evaluations were
flat by their contract's RTH close. **The 18:00→16:00 rule has never been run here and cannot be
expressed by the shipped engine**, which is why EF1's harness gates the programme and why ADJ-15a is a
gate rather than a caution.

**3. The scalp band spans 57.90 days, and clearing even the single-pre-registered floor needs an
annualised Sharpe of 2.96.** Measured spans, which **correct the brief's own table**: 5m/15m/30m all
**57.90 calendar days = 0.1585 years, √years = 0.398** `[measured, EF6: edge/EF6/bursts/01]`, against
the brief's 57. So `free_t = 1.177` — the floor for **one** pre-registered hypothesis — needs
**SR ≈ 2.96**, not 2.98; EF4's 36-arm Track A needs `free_t = 2.677` → **SR 6.73**; a 19,152-arm
screen needs `free_t = 4.441` → **SR 11.16**; and the largest *t* ever found in this programme
(3.923) corresponds to **SR 9.85** on this span `[measured, EF4: edge/EF4/FINDINGS.md]`.
**Canonical values for the programme: 57.90 days, √years 0.398, SR 2.96 for n = 1.** Every scalp row
carries this bound **on the row**, not once in a preamble — the brief already requires it and the
board is not softening it. A ranked list at this power is a description of 41 sessions of one
two-month window; that was established before any strategy was run and no result changes it.

**Two further measured constraints that belong here and were not in my dispatch:**

**4. `rth_only=True` makes the rule inert for entries, and the overnight arm is not free.**
`StrategyFilters.rth_only` defaults `True` `[repo-verified: futures_agents/strategies/base.py:393]`
and is `True` on **184/184 MGC and 167/167 MCL** generated strategies at `[60, 240]`
`[measured, EF2]` — consistent with R3's finding that the scope vocabulary is inert in the generation
path and R1's 314/314. MGC RTH 08:20–13:30 and MCL 09:00–14:30 sit **wholly inside one cycle**, and
the count of bars that are both RTH and swing-admissible equals the RTH count **exactly**
(2,477/2,477 MGC, 2,881/2,881 MCL). **So at the generated default the rule buys hold time, not entry
time: +2h30m on MGC, +1h30m on MCL, and nothing at all on MES/MNQ, whose RTH close already is
16:00.** Reaching overnight entries needs `rth_only=False`, which **`D24` measured as buying 2–4× the
sample while costing expectancy in every paired test.**
> **Ruling: the `rth_only` arm is a paired arm, never a swap.** `R-6` and `D48`'s discipline
> (`_id=None` on every `replace`, assert arm-id uniqueness at emission) apply to it in full, and
> **every swing row declares which of the two it is** — a longer hold on an RTH entry, or an
> overnight entry bought at `D24`'s price. EF2 already carries it as `EF2-H1`; this makes it binding
> on EF3, EF7 and anyone else who reaches the swing cell.

**5. Two substrate holes, both measured, neither owned.** (a) **MCL 60m is structurally thin for
roughly two months inside the 718-day span** — 17 ET dates from 2026-01-12 to 2026-03-10 carry **1 to
5 bars each** against ~20 on a normal day `[measured, EF1]`. That is EF2's MCL swing cell directly and
it is not fixed by anything EF1 does. (b) **MCL daily does not exist**: `MCL_1440m.jsonl` is one line
`[measured, EF6]`. So any "per symbol" claim at daily is three symbols, not four, and EF6 was right to
make `for_cell` **raise** on `("MCL", 1440)` rather than guess. Both go on the board as facts, and (a)
gets a task: **whoever reports an MCL 60m swing row states the thin window and whether its trades fall
inside it.**

### ADJ-15c — One question routed, not answered, because answering it would be analysis

**Does the 22-hour cap make the 1440m cell inexpressible?** EF6 observes that daily is the only cell
with enough span to answer anything at width *and* the cell where the session rule is nearly
degenerate, because a 22-hour hold is about one daily bar. That tension decides whether a daily swing
row means anything, and it is arithmetic on facts two agents already hold. **Routed to EF6 and to
whoever the parent gives the daily arm, to be answered before anything is built there, not after.**
I am not answering it: I run no analysis.

### ADJ-15d — What the edge programme inherits from the research pipeline, in one place

So no EF agent re-derives it: **`R-1`** (`csv/` read-only, no exceptions), **`R-2`** (a placebo beside
every row; `placebo_shift` leaks per `D42` and is conservative-only), **`R-3`** (state the search size
and the deflation threshold), **`R-4`** (never route a comparative claim through `T.ab`), **`R-6`** +
**`D48`** (paired re-emission discipline), **`R-7`** (substrate labelling; `data/archive/` is this
programme's substrate, compared with a tolerance and never `==`, and never pooled with a `csv/raw`
number inside one statistic), **`R-8`** (`entry_price`, `initial_stop`, `symbol` on every trade dump —
this programme will want account sizing and `R-8` is exactly why), **`R-13`** (new, ADJ-15a),
**`R-14`** (new, ADJ-13a — the VOID reachability line, which the 19.0% carrier rate makes immediately
relevant: MGC 11.5%, MCL 13.9%, MES 22.6%, MNQ 27.4%).

And the two research findings that constrain the deliverable most: **`D24`** (the price of
`rth_only=False`) and **`D8`** ("selecting is worse than not selecting" — trading last period's top 10
returned −0.0155R against a −0.0104R null and underperformed trading the whole qualifying universe,
+0.022R against +0.057R). `D8` is the finding this programme's deliverable is most exposed to, it is
**structurally immune to R6's entire audit** because both arms are drawn from the same population over
the same bars, and the brief already says the right thing: that is not a reason to refuse the task, it
is the reason every list carries its forward behaviour and not only its in-sample rank.

**What ADJ-15 costs.** Two things. **`R-13` will make the edge programme late** — five agents have
populations built and censuses run, and none of them may report a profitability number until two
harnesses are reconciled on 19 sessions. I am choosing that over the alternative, which is a top-10
list handed to an account owner whose trades may have been held through a window the rule forbids; the
programme has already retracted one published result for reading a null too broadly and a violated
session rule is worse, because it is not conservative. The second cost is mine to own: **I have added
two standing rules in one turn (`R-13`, `R-14`) after spending ADJ-12 arguing against register
inflation.** The defence is that both are gates rather than labels and each has a measured failure
behind it — 33 and 43 violations for `R-13`, 23-of-23 frame-of-one cells for `R-14` — but two rules is
the most I will add in a turn and I am recording that as the ceiling.

---

## ADJ-16 — The `RECEIVED` backlog is discharged, `R-12` is retired, and two process defects are mine

**2026-09-27 04:05 ET.** ADJ-11c left seven requests `RECEIVED` and said: "if any of these is still
`RECEIVED` two turns from now that is a failure of mine, not a backlog." **This is that turn.** All
seven are ruled, plus the five that arrived since.

| request | ruling | where |
|---|---|---|
| `R2-REQ-1` | **`D55`** — and the triage was *wrong*: it is the **`D43` identity-hash family**, not `D48`'s. `D48` is an id not recomputed; this is a behaviour-bearing field never in the hash | ADJ-12 |
| `R2-REQ-2` | **`D46` instance 3.** Triage confirmed | ADJ-12 |
| `R2-REQ-3` | defect 1 → **`D56` instance 1** (kin is `D39`, not `D46`); defect 2(a) → **`D47` instance 2**, `D47` becomes a class; defect 2(b) → **`D57`** | ADJ-12 |
| `R3-REQ-2` | **Granted as a board task, and `R-6` is amended a second time** — see below. Do not build before reading EF1's harness | this block |
| `R3-REQ-3` | accepted in ADJ-11c, no ruling needed | ADJ-11c |
| `BT2-REQ-1` | **`D56` instance 2**, not its own number — same object, the news proximity clock | ADJ-12 |
| `BT2-REQ-2` | **declined as a defect; a named missing primitive**, and EF1 has now built the clock-event form of it | ADJ-12 |
| `BT2-REQ-3` | **(a) yes, run it with its placebo.** 69 (MGC) / 164 (MCL) admissible bars against `FLOOR = 20` is BT1's situation and gets BT1's framing (ADJ-6): a pre-registration surviving a small sample is a better result than a sweep. **(b) needs no sub-task — the edge programme answered it.** `data/archive` 15m is 3,746 bars over 57.90 days and EF5 has verified store equivalence for its cells. BT2 cites EF6's `threshold(n, span_days)` and EF5's equivalence check rather than re-deriving either | this block |
| `R4-REQ-1` | **`D50`** | ADJ-12 |
| `R4-REQ-2` | **`D54`** | ADJ-12 |
| `R4-REQ-3` | **`D58`**, one class, two instances, two fixes | ADJ-12 |
| `R4-REQ-4` | **declined** — board task only, with R4's warning attached | ADJ-12 |
| `R4-REQ-5` | **`D53` instances 3–4**; consequence routed to `MGR-T17` | ADJ-12 |
| `R1-REQ-5` | **VOID adopted, amended three ways** | ADJ-13a |
| `R1-REQ-6` | ruled below | this block |
| R5's four | ruled below | this block |

### ADJ-16a — `R3-REQ-2`: granted, and `R-6` is amended again, because the cheap half is available today

R3's measurement is the ruling. On the only paired re-emission that exists on disk (the geo study:
22 rule sets × 2 exits × 8 cells × 3 slices = 258 pairs) **the two arms of a pair share a median of
61.8% of their entry timestamps, only 17 of 258 reach 90%, and the median trade-count ratio is 1.332**
`[measured, R3: entry-timestamp Jaccard over stops_cache.json, R3_pairing_design.md §4.3]`. The cause
is `engine.py:304-309` — a positioned strategy does not look for signals — so **any axis that changes
holding duration changes which later bars the arm is flat for.**

**So rule-set-level pairing does not deliver what `D15` asks for.** It fixes the rule set and leaves
the trade population free, and a pair sharing 61.8% of entries is not a paired comparison of exits; it
is a comparison of two overlapping trade populations.

> **`R-6` amended (second time, after ADJ-11a): a paired re-emission reports its entry-timestamp
> overlap beside its result.** One number, computable from artefacts that already exist, and it
> converts "this is paired" from an assertion into a measurement. A pair below a stated overlap floor
> is reported as a population comparison, not an exit comparison.

**The exogenous-entry harness is granted as a board task and deliberately ranked low.** It is the only
route to trade-level pairing and it touches the hottest loop in the engine while twelve agents are
live; the amendment above gets most of the value at none of the risk. **And it must not be built
twice** — EF1's `SessionWindowEngine` is the same *kind* of object (a driver that imposes exogenous
exit/entry constraints on `_manage`), so R3 reads `edge/EF1/code/` before writing a line. One caveat
that travels with the task: an exogenous-entry arm **is not a strategy anyone could trade**, so its
result is a statement about an exit mechanism and never a candidate.

### ADJ-16b — `R1-REQ-6`: what a second reading of the same 35 conditions is worth, given R4's declared anchor

R1 audited all 11 remaining groups before `ADJ-8` reached it, so two readings of 8 overlapping groups
exist. **R4 then declared, against its own interest, that its dispatch had it read R1's verdicts
before forming its own — all 31, stated before any verdict** `[repo-verified:
research/R4_group_audit.md, DECLARED ANCHOR]`. `BRIEF.md`'s independence rule already says how to
treat that: a declared anchor is usable, an undeclared one is not.

> **Ruling: the 8 overlapping groups are ONE audit, not two.** R4's 30-of-31 agreement and 7-of-7
> group agreement are **corroboration of a reading**, not replication, and must never be cited as
> two independent audits agreeing. **The second reading's independent weight is entirely in its
> disagreements and its new findings**, and that is where I am banking it:
> - **the one stricter verdict** — `mtf_strongly_aligned` MISNAMED as well as DEGRADED, because
>   "every timeframe from this one up agrees" is computed over only the **directional** timeframes
>   (`agreeing_timeframes` drops abstentions from `voting`, `[repo-verified: features.py:764-766]`),
>   making the description false on 65–88% of its firings at four of six corpus rows on all four
>   symbols;
> - **two live contradictions.** #1: the MACD double-count is **structurally impossible** — one
>   condition per group, no template lists a group in both required and optional, 0 co-occurrences
>   measured on four symbols; the real harm is `D58` instance 2. #3: **the direction is reversed and
>   the scope halved** — a 4h TREND strategy is gated by the **daily** regime, never the 15-minute
>   one, because `FRAMES` makes `regime_tf` coarser at 5m, the strategy's own timeframe at 15m/30m/60m
>   and the daily series at 240m. **#3 is the more valuable of the two**, because it converts a
>   plausible-direction defect into a measured one and it is what `MGR-T17` needs;
> - **the third contradiction R4 withdrew itself** to a REFINEMENT after R1's rebuttal
>   `[repo-verified: msgs/14_R1_R4_re-signal-pools.md]`, which is the behaviour to reward: it is
>   the only retraction in this round that cost its author a finding;
> - **eleven findings absent from R1's file**, of which `R4-M3` (→ `D50`) is the largest single item
>   in either audit, plus the prefix-invariance test over all 31 conditions in 3 cells and 16 probes
>   — **all 31 prefix-invariant**, which is the only direct look-ahead check either auditor ran.
>
> **Neither auditor has shipped an error on the 8 overlapping groups.** Every disagreement resolved
> to "both right about different objects" or to a refinement. That is a real result about the audit
> and it should be stated rather than assumed.

### ADJ-16c — R5's four routing questions

1. **Which verdict does the ledger carry for `MAIN-01`?** R5 recommends a split: `CLOSED-EMPTY` on the
   minute-snapped construction (substrate — and a tape would **not** fix it, so **not** `DEFERRED`),
   the tape-blocked schemes staying `DEFERRED` under `BLOCK-SUBBAR`, one sub-task moving. **Ruling:
   the ledger carries `CLOSED-EMPTY`, and the reason field carries `SUBSTRATE-1M`, not
   approximation error.** The reason is the load-bearing part because `AVENUES.md`'s revisit rule
   turns on it: a tape arriving does not create 1-minute history, and "the approximation was too
   poor" is a claim **nobody has measured** — my own pre-registration 1 predicted the task would die
   on approximation error and **R5 has refuted the mechanism while confirming the outcome**, one gate
   earlier. Scored in §7. The `DEFERRED`/`BLOCK-SUBBAR` half is discovery's file to write and I route
   it, not write it.
2. **A correction to `BOARD.md` §2's substrate note, and it is mine to take.** §2 says the usable
   substrates are `data/{MES,MGC,MNQ}_1m.csv` and `data/archive/*.jsonl`. **That is a 60-minute
   statement and it is false at 1 minute**: the archive's 1m series **starts inside** `csv/raw`'s span
   and the union is **9,069 unique minutes ≈ 6.5 RTH sessions per symbol**, overlap 2,812
   `[measured, R5]`. `BOARD.md` §2 is corrected below. **This is the substrate wall's third
   appearance** after `BT1-REQ-1` and `BT2-REQ-3`, at a third timeframe.
3. **Who owns `S2`, and does it survive `MAIN-01` closing? It survives, and it moves.** `S2` needs no
   constructed bars, so the substrate closure cannot kill it, and its content is the
   **time-of-day-residualised** stratum — which is exactly what `MGR-T13` was promoted to settle, at
   the same `(symbol, tf, ts)` join. **Ruling: `S2` is re-filed into `MGR-T13` and does not survive
   as a `MAIN-01` section**, with R1's binding design constraint applying verbatim: both axes take
   the time-of-day norm or neither does. `MGR-T13`'s holder owns it.
4. **The 1-minute store reconciliation.** **Ruling: it extends `MGR-T6` rather than living in a
   closing task's scope.** `MGR-T6` is scoped to the 60m overlap and `BRIEF.md`'s own condition 2 says
   not to assume that generalises; the 1m overlap is 2,812 bars for MGC and cheap. `R-7` continues to
   forbid pooling the two stores inside one statistic at any timeframe.

### ADJ-16d — `R-12` is **RETIRED**

The parent extended `check_refs.py`'s grammar and I have verified it rather than taking it on report:
`MGR-(T\d+|Q\d+|REQ-\d+)`, `ADJ-\d+`, `R-\d+`, `D-[A-Z]+\d+`, `X-\d+`, the `[ABM]-?\d+` kind that
resolves `R4-M3`, and `H\d+` for harness components (`EF1-H1`) all resolve, with issuers
`(R[1-6]|BT[1-6]|EF[1-7]|DISC2?)` — so `BT4`/`BT5`/`BT6` and `EF1`–`EF7` are covered
`[measured: sed -n '/^ID = re.compile/,/^)/p' check_refs.py]`.

> **`R-12` is retired. `MGR-T<n>` and `ADJ-<n>` may appear in a `RE:`/`ALSO:` header from now on.**
> The workaround — cite the anchor id and name the board task in the body — stays *valid* so no
> existing message becomes malformed, but it is no longer required. **Nobody should cite `R-12` again
> except historically.**

### ADJ-16e — Two process defects, both mine

**1. The board's holder column was stale at dispatch time twice in one round.** `MGR-T4` was
dispatched to R4 when R1 had already audited all 11 groups; `MAIN-01`'s scope was dispatched to R5
when the board names R1 `[repo-verified: BOARD.md:131, :308]`. Both agents handled it correctly — R4
converted its task into an independent replication and declared the anchor, R5 proceeded and told me
to merge rather than supersede — so nothing was lost. **But twice in one round is a mechanism, not
luck.** The mechanism is that the board is written once per turn while twelve agents write
continuously, so its holder column is stale by construction the moment it is published.
> **Ruling: from here the board's holder column is advisory, and the *output directory* is
> authoritative.** The dispatching parent reconciles against `ls` of the target's `out/`,
> `research/` or `bursts/` before dispatching a task, exactly as `BOARD.md` §3's own 00:25 ET
> reconciliation note did by hand. Cheaper than a stamp per row and it puts the check where the
> information is.

**2. `R-9` and the anchor declaration both worked, and saying so is part of the job.** No `D<n>`
collided this round across nine requests from six agents — `R-9` is doing what it was written for.
And R4's unprompted anchor declaration is the single most useful methodological act of the round: it
converted what would have read as a 30-of-31 independent replication into an honestly-labelled
corroboration, which is what let ADJ-16b bank the disagreements at full weight instead of
discounting everything.

**What ADJ-16 costs.** ADJ-16a's amendment adds a number to every paired result forever, including
the ones already computed, so R3's `MGR-T3` design gains a retro-fit item. And retiring `R-12` means
twelve agents may now put `MGR-T` ids in headers, which is correct and also means my board ids become
load-bearing in files I cannot edit — the numbering irregularity `BOARD.md` §3 records ("read the
table, not the numbers") stops being a private embarrassment and becomes a public one.

---

## Id allocations made this turn (round 3)

Only the manager allocates `D<n>` and `MAIN-<nn>/S<n>` (`REGISTRY.md`). **Fifteen defect candidates
arrived; nine numbers issued, four folded into existing entries, four declined.**

| id | kind | what | filer | where ruled |
|---|---|---|---|---|
| **D50** | defect | `align_bucket` ignores `minutes` ≥ 1440; `FRAMES[1440]` holds the daily series twice, lagged 2–4 bars | R4 (`R4-REQ-1`) | ADJ-12 |
| **D51** | defect | `BarSeries.append` silently replaces on an equal timestamp and never enforces contiguity | R5 | ADJ-12 |
| **D52** | defect | at daily frequency the `vwap` group is a bar-shape group; band-1 half-width < 1 tick on 100% of daily bars; `vwap_band1_bounce` fires 0/0 | R6 (`R6-D1`) | ADJ-12 |
| **D53** | defect (class, 6 inst.) | conditions and filters that accept a timeframe and read a different one — incl. `StrategyFilters.require_alignment` | R1, R4, R6 | ADJ-12 |
| **D54** | defect | a required group with no SIGNAL member is silently dropped; `volume` declared required by MOMENTUM and BREAKOUT, never enforced | R4 (`R4-M1`) | ADJ-12 |
| **D55** | defect (forward) | `strategy_id` carries no partner provenance; two frames collide on one key and the second overwrites | R2 (`R2-REQ-1`) | ADJ-12 |
| **D56** | defect (2 inst.) | the news proximity clock misreports in both directions — forward fill offset 60–120 min vs claimed 15–60; backward projection 2 days vs 45 forward | R2, BT2 | ADJ-12 |
| **D57** | defect | `outside_news_blackout` is the identity filter on a `:00` grid — MGC 0 of 1,093 bars removed | BT2 / R2 | ADJ-12 |
| **D58** | defect (class, 2 inst.) | the catalogue contains duplicate predicates and `GLOBAL_EXCLUSIVE` covers neither kind | R4 (`R4-REQ-3`) | ADJ-12 |
| `D46` | **+2 instances** | inst. 3 `Condition.warmup_bars` declared and never consumed; inst. 4 `metrics.py`'s annualisation comment | R2, R5 | ADJ-12 |
| `D47` | **now a class, +1 instance** | inst. 2 the three `news` conditions on every daily series — **blast radius bounded to zero**, the combinator cannot emit a carrier | R2, R6 | ADJ-12 |
| — | **declined** | `scout.rank` `KeyError` on 30m — a nit, and the unreachable fallback is currently protecting us | R4 (`R4-REQ-4`) | ADJ-12 |
| — | **declined** | no flatten-before-the-print exit — a named missing primitive, and EF1 has built the clock-event form | BT2 (`BT2-REQ-2`) | ADJ-12 |
| — | **declined** | the 240m `regime_tf = 1440` finding — it is `D53` instances 3–4, routed to `MGR-T17` | R4 (`R4-REQ-5`) | ADJ-12 |
| — | **declined** | `rsi_extreme_reversal`/`stoch_extreme` misfiled under `momentum` — a taxonomy judgement (ADJ-9b precedent); gets a **vocabulary verdict** instead | R4 | ADJ-13b |
| **`R-13`** | standing rule | `R-5` applies to harness components: no profitability number from an unvalidated session harness | — | ADJ-15a |
| **`R-14`** | standing rule | a `VOID` verdict is per (symbol, timeframe, frame) + scope flag, and carries `REACHED` / `FORWARD` | R1, R4, R6 | ADJ-13a |
| **`R-12`** | **RETIRED** | `check_refs.py`'s grammar now resolves `MGR-T<n>`, `ADJ-<n>`, `R-<n>`, `D-L1`, `X-<n>`, `M<n>`, `EF<n>-H<n>` | parent | ADJ-16d |
| **`R-6`** | **amended (2nd)** | a paired re-emission reports its entry-timestamp overlap; median 61.8% measured on the only one on disk | R3 (`R3-REQ-2`) | ADJ-16a |
| `MGR-T19`…`MGR-T28` | board task | see `BOARD.md` §3 and §8; `MGR-T28` (`D51` verification) is **unassigned** and is the only round-3 defect with no verifier | — | `BOARD.md` |
| `MAIN-01/S<n>` | sections | **still none, and now none ever** — `MAIN-01` closes `CLOSED-EMPTY / SUBSTRATE-1M`, `S2` re-files into `MGR-T13` | R5 | ADJ-16c |

**Vocabulary state after this turn, in one place, so nobody carries two:** the canonical audit
vocabulary is `BRIEF.md`'s, extended by one term — **`CLEAN` / `PROXY` / `DEGRADED` / `VOID` /
`DEAD` / `MISNAMED` / `MISFILED`** — with `VOID` carrying three coordinates and a reachability line.
`ADJ-8`'s `HONEST-DERIVED` and `HONEST-DERIVED-BUT-BROKEN` are **retired**, readable, and mapped in
ADJ-13a. R6's report-level vocabulary (`STANDS` / `WEAKENED` / `INVALID` / `UNAFFECTED`, with the
`SUBSTITUTED` / `DEGENERATE` / `ZERO-FIRE` sub-kinds) is **orthogonal to this one and is not
merged** — it grades a published claim, not a condition, and conflating them is how a retraction gets
read as a verdict on a condition or vice versa.

### ADJ-16f — Correction to ADJ-16c §3, made at 04:20 ET by reading the output directory rather than the board

**`S2` is not awaiting a holder — it is in flight with BT5**, and I found that by doing the thing
ADJ-16e had just made mandatory. `LEDGER.md`'s round-3 row lists BT5 as dispatched with no scope
recorded, so my first draft of `MGR-T22` offered BT5 a recommended scope. **BT5's own code records its
scope**: `backtest/BT5/code/activity.py` and `s2.py` are `BT5-ALGO-1` parts 1 and 2, and `s2.py`'s
docstring opens *"R5's S2. Two layers, and they answer two different questions"* — layer 1 with the bar
as the unit, layer 2 with the strategy as the unit, the second explicitly *"per R3's ruling that the
unit of a finding over this artefact is per-strategy, so the primary number is the median over the 176
strategies of a within-strategy contrast"*.

**So ADJ-16c §3 is amended, and narrowed to what it should have said.** The ruling stands on where the
*question* lives — `S2`'s content is the time-of-day-residualised activity stratum and that is
`MGR-T13`'s subject, with R1's both-axes-or-neither constraint binding. It was **wrong to imply the
work needed re-assigning**: the work is running, and `MGR-T13` is `S2`'s conceptual home and its
prerequisite input, not its new holder. Board row corrected to **IN FLIGHT / BT5**.

**Two things this is worth beyond the correction.** First, it is ADJ-16e's remedy catching ADJ-16e's
own defect **within the same turn** — the board's holder column was stale again, and the output
directory was authoritative again. Second, it exposes a real gap the stale row was hiding: **`D51` is
the only round-3 defect with no verification in flight.** BT4 holds `D50`, BT6 holds `D52`, BT5 holds
`S2` — and `D51`, a false-null mechanism whose collapse floor is exact and needs no tape, has nobody.
On the board as **`MGR-T28`, unassigned**, which is the honest status rather than a name invented to
fill the column.
