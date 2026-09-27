# Open questions — researcher to researcher, routed by the manager

You cannot call each other. Write the question here; the manager routes it and the parent session
relays it. Append only — never edit or delete someone else's row.

> **ROUND-2 NOTE, 2026-09-26 23:15 ET — read this before citing any `Q<n>` below.**
>
> **The numbering in this file collided.** Three agents reached for the same numbers independently,
> so **`Q2` and `Q3` each name two different questions** and a bare `Q2` is a malformed reference.
> `REGISTRY.md` holds the canonical ids and this file is **not** renumbered — renumbering would break
> every citation already written into five research files. The mapping:
>
> | as written below | canonical id | issuer → addressee | status |
> |---|---|---|---|
> | `Q1` | **`R1-Q1`** | R1 → manager | **ANSWERED** — ADJ-3, `D46` allocated |
> | `Q2` (first) | **`R1-Q2`** | R1 → manager | **ANSWERED / CLOSED** — ADJ-4, no figure changes, `D47` allocated |
> | `Q3` (first) | **`R1-Q3`** | R1 → R2 | **ANSWERED** by R2 below (`R2-Q2`) |
> | `Q4` | **`R2-Q1`** | R2 → manager | **ANSWERED** — ADJ-1, accepted in substance, fourth class refused |
> | `Q5` | **`R2-Q2`** | R2 → R1 | delivered; it is an answer, not a question |
> | `Q2` (second) | **`R3-Q1`** | R3 → R1 | **ANSWERED** by R1, `msgs/04_R1_R3_re-VWAP-BAND.md`; `D45` allocated |
> | `Q3` (second) | **`R3-Q2`** | R3 → manager | **ANSWERED** — ADJ-5, refutation accepted in full |
>
> **All seven round-1 questions are now closed.** Every ruling is in `manager/ADJUDICATIONS.md` with
> its cost stated. **From the pipeline onward, do not append here** — post `msgs/NN_<from>_<to>_<topic>.md`
> (write-once, no contention) and I consolidate. See `OWNERSHIP.md` §"The one live exception".
> **Sub-task requests are not questions**: they go in your own `REQUESTS.md` and reach
> `manager/BOARD.md`, not this file.

## Protocol

One block per question, newest at the bottom, using exactly this shape:

```
### Q<n> — <from> → <to or "manager"> — <one-line topic>
**Asked:** <YYYY-MM-DD HH:MM ET>
**Question.** <what you want to know, and what you would do differently depending on the answer>
**Why it is not mine to answer.** <which track owns it, per DIVISION.md §5>
**Blocking?** yes / no — if yes, name the deliverable it blocks.

**Routed:** <manager fills this: to whom, when>
**Answer:** <the answering researcher fills this, with path citations>
```

Use it for these three things and nothing else:

1. **A boundary dispute.** You think a family sits in another class, or in yours and not theirs.
   Do not annex it. Ask.
2. **A fact another track owns.** You need a verdict about code that DIVISION §5 assigns to
   someone else. Ask rather than auditing it yourself — a second audit of the same file is the
   duplication this division exists to prevent.
3. **A challenge.** You believe another track's claim is wrong or over-stated. Say so here, with
   the path that makes you think it. This is welcome and it is the point; one candidate shape for
   round 2 is exactly this, done deliberately.

If the answer would change a verdict you have already written, write the verdict anyway and mark it
`PENDING Q<n>`. Do not stall a deliverable waiting for a relay.

## Questions

*(none yet — round 1 has just been dispatched)*

### Q1 — R1 → manager — the `estimated` flag is set and never read; is this a new defect?
**Asked:** 2026-09-27 (round 1)
**Question.** `futures_agents/indicators/volume.py:1-9` promises that any result derived from proxy
delta "is flagged `estimated=True` … the system says so rather than quietly presenting it as order
flow". The flag is produced (`Bar.delta_is_estimated`, `bars.py:91-92`; `VolumeProfile.estimated`,
`volume.py:258`) and **no consumer anywhere reads it**:
`[measured: grep -rn "estimated" futures_agents/ --include=*.py | grep -v __pycache__ → 13 hits,
all inside indicators/volume.py and data/bars.py]`. Zero hits in `strategies/library.py`,
`features.py`, `backtest/`, or the reporting path. So every published `scan_reports/` row containing
`cvd_directional`, `delta_confirms_bar` or `delta_divergence` presents a close-location-value
bar-shape predicate under the order-flow name, with the flag available and unconsulted. Should this
carry a D-number in `workspace/studies/DEFECTS.md`? I have not assigned one — D-numbers are not
mine to allocate. If you assign one I will cite it in R1-D4 instead of describing it longhand.
**Why it is not mine to answer.** `DEFECTS.md` is the manager's / programme's register.
**Blocking?** no.

**Routed:** to the manager (me), 2026-09-26 22:11 ET. Ruled in `manager/ADJUDICATIONS.md` ADJ-3.
**Answer (manager).** **Yes — allocated `D46`, and allocated as a *class* rather than a single
instance.** You were right not to allocate one yourself. It qualifies on the register's own
precedent: `DEFECTS.md` already holds entries that change no number (`D37` is an expressibility
limit, `D42` a methodological caveat), and the register's purpose — "read before trusting any number
a tool prints" — covers a reason not to trust the **name** on a number, which is the same class of
harm and the harder one to detect.

The class is **"documented inputs the code does not read"**, because your `R1-REQ-3` is a second
instance of exactly this shape (`detect_imbalances`' docstring names delta; the body reads volume and
returns `magnitude = r_mult`), and the group audit now on the board is a systematic search for more.
Ten adjacent D-numbers for ten docstrings would bury the pattern; one class entry with an instance
list makes it the finding it is. **Cite `D46` in R1-D4 and in `R1-REQ-3` instead of describing either
longhand** — which answers both of your asks. Exact register text for its owner to apply: ADJ-3.

Trigger recorded: if the instance list passes about six, split it by harm profile (labels-wrong
versus readers-misled) so the growth is a decision rather than a drift.

### Q2 — R1 → manager — did zero-trade `openinterest` strategies enter the 2,975,629 denominator?
**Asked:** 2026-09-27 (round 1)
**Question.** `oi_price_confirmation` (SIGNAL) and `oi_expanding` (FILTER) both return
`ConditionResult.no()` unconditionally on `csv/raw/` data, because `open_interest` is `None` on
every bar `[repo-verified: library.py:1281-1282,1309-1310; features.py:278-279]`
`[measured: all 300 MGC_1h bars have open_interest None]`. A SIGNAL that never fires yields zero
trades; a FILTER that never passes vetoes every entry. So any sampled strategy carrying either
condition is a guaranteed zero-trade strategy. Two questions I cannot answer without running sweeps
(forbidden, DIVISION §8): (a) were such strategies counted in the ~2,975,629 evaluation total and
in the multiple-testing denominator that produces `free_t = 5.46`? (b) if they were, does removing
them change `free_t`? A denominator inflated by structurally-null candidates would make the
threshold *more* conservative, not less, so the settled negative verdict is safe either way — but
the number should be right.
**Why it is not mine to answer.** Programme-level accounting; and answering needs a sweep.
**Blocking?** no.

**Routed:** to the manager (me), 2026-09-26 22:11 ET. Ruled in `manager/ADJUDICATIONS.md` ADJ-4.
**Answer (manager). (a) Yes. (b) No, and no sweep is needed — the bound is already published.**

**(a) They entered.** Two independent grounds. First, 2,975,629 counts *evaluations*, and the record
says so by offering the discount: `[repo-verified: workspace/studies/RANKING_FINDINGS.md:66-72]`
"2,975,629 strategy evaluations across the whole project (bigscan 533k, focus 613k, other studies
1.13M, rank cells 549k+152k) → free_t = 5.46 … **Even discounting the 82% of generated strategies
that never trade, the effective search is ~495k and free_t 5.15, still uncleared.**" A figure cannot
be discounted for non-traders unless non-traders were in it. Second, `openinterest` was *inside* a
screened population rather than filtered out ahead of one: `[repo-verified: DEFECTS.md:210]`, the
`x_conditions` verdict log, reports `oi_expanding` as one of its 34 tested conditions with the result
"fires on 0.0% of bars". A condition cannot be reported at 0.0% by a study that never sampled it.

**(b) Removing them changes nothing, and the reason is arithmetic.** `free_t = sqrt(2·ln n)` is
logarithmic, so the denominator barely matters at this scale
`[measured: python3 -c "import math; [(n, math.sqrt(2*math.log(n))) for n in (...)]"]`: n = 2,975,629
→ 5.4600; half removed (1,487,815) → 5.3316; the published zero-trade discount (~495k) → 5.15;
**91% removed (268,337) → 5.0000**; and n would have to fall to about **2,197** for the threshold to
meet the largest t ever found here, 3.923. `openinterest`-bearing strategies are a **strict subset**
of the 82% that never traded, so removing them is bounded above by a discount the programme has
already computed and already published — uncleared at both ends.

**So: no published deflation figure changes and no verdict moves.** Your own instinct — "the settled
negative verdict is safe either way" — is confirmed with the number attached. `R1-Q2` is **CLOSED**,
and this also closes the open half of `X-15` in `AVENUES.md`, routed to discovery (`msgs/07`).

**No defect for the denominator accounting** — the bound is on disk. What is *not* on disk is its
onward transmission: `BRIEF.md` and the scan reports quote `free_t = 5.46` without the 495k/5.15
companion. That is one line of reporting hygiene, routed, deliberately **not** numbered.

**But the narrower thing you found does get a number: `D47`** — `openinterest` conditions are
structurally dead on all 48 files, so any carrier is a guaranteed zero-trade evaluation **by
construction** rather than by chance, and `oi_expanding` as a FILTER is a deterministic veto of every
entry. Budget waste, not corruption; direction known and conservative. Register text: ADJ-4.

**One sentence the programme now owes**, and it is the cost of my ruling: the honest form is "≥
2,975,629 candidates were **generated**, of which an unmeasured subset could not trade". Anyone
writing "2,975,629 strategies were **tested**" is overstating it.

### Q3 — R1 → R2 — every MEDIUM/LOW `ECON_RULES` entry is invisible to all three `news` conditions
**Asked:** 2026-09-27 (round 1)
**Question.** Handoff for R2-D5, not a dispute. The news plumbing filters the projected event list
to `e.impact.rank >= Impact.HIGH.rank` *before* computing `minutes_to_high_impact`,
`minutes_since_high_impact` and `in_news_blackout`
`[repo-verified: futures_agents/features.py:972-973]`. So however many rules `ECON_RULES` holds,
only the HIGH-impact subset is observable by any condition in the library. When you inventory the
calendar, the count that matters for expressibility is the HIGH count, not the total. I own the
three `news` conditions' arithmetic (done, R1-D4); the rule inventory is yours per DIVISION §5.2
and I have not audited `econ_calendar.py`.
**Why it is not mine to answer.** DIVISION §5.2 gives R2 the calendar.
**Blocking?** no.

**Routed:** to R2, 2026-09-26 (round 1). **Answered by R2 below, in the block written as `Q5`
(canonical `R2-Q2`).** Closed — no manager ruling needed.
**Answer (summary, R2's, for the router's record).** Confirmed, and larger than "MEDIUM rules are
invisible": `ECON_RULES` holds **11 rules, 6 HIGH / 5 MEDIUM / 0 LOW**, one of the six HIGH is
symbol-scoped to crude/natgas, so the visible universe is **5 rules** for MGC/MES/MNQ. And R2 added
the correction that matters for your `R1-D4`: `features.py:969-971`'s comment ("four FOMC days in a
hundred and twenty and nothing else") is **true for MNQ/MES and false for MGC** — measured in-RTH HIGH
event days are MNQ 7, MES 7, **MGC 32**, **MCL 49**, because gold's pit session opens 08:20 and the
08:30 prints land ten minutes inside it. Full text and citations in the `Q5` block.

### Q4 — R2 → manager — Class II is mis-cut in one specific place: II-10 and II-11 need no second observable
**Asked:** 2026-09-27 (round 1)
**Question.** DIVISION §1 defines Class II as "it needs something other than this contract's own
price path". Two of my nineteen families fail that test and I am not moving them unilaterally
(§5 forbids it), so here is the proposed recut with the reason.

**II-10 seasonality** and **II-11 scheduled-event trading** need **no second series, no second
expiry, no surface and no positioning report.** They need the *timestamp already on the bar*.
- II-10's vehicle exists today: `[repo-verified: futures_agents/strategies/base.py:392]`
  `StrategyFilters.days_of_week`, fed by `[repo-verified: features.py:697]`
  `FeatureSnapshot.day_of_week`. Everything else it needs is `snap.trading_day.month`
  `[repo-verified: features.py:702]`.
- II-11's vehicle exists today: `[repo-verified: features.py:704-713]`
  `minutes_to_high_impact` / `minutes_since_high_impact` / `in_news_blackout`, populated by
  `_build_news_proximity` `[repo-verified: features.py:946-1003]` from recurrence *rules*, which is
  precisely a construction that avoids needing an external observable
  (`econ_calendar.py:8-10` argues this explicitly).

So the class boundary as written puts them with the crack spread, when mechanically they sit with
Class III: *the edge is a function of this one series plus its own clock.* **Proposed recut:** either
(a) move II-10 and II-11 to Class III as "III-20 calendar conditioning", or (b) — better, because it
keeps the classes honest — name a **fourth axis, "the clock"**, holding II-10, II-11 and R3's
time-based exits (III-12), since all three condition on the timestamp rather than on the tape.

**Why this matters rather than being taxonomy pedantry.** The cut as drawn hides the only two
Class II families that are *actionable today with zero new data and zero new code*, by filing them
behind seventeen that are blocked on architecture or acquisition. A reader of the merged catalogue
would conclude Class II is uniformly unreachable. It is not: 2 of 19 are reachable now.

**What I did instead of moving them.** Catalogued them in R2-D1 under their DIVISION ids with their
real verdicts (PARTIAL / EXPRESSIBLE, not INEXPRESSIBLE), and flagged the boundary here.
**Why it is not mine to answer.** §5 reserves class reassignment to the manager.
**Blocking?** no.

**Routed:** to the manager (me), 2026-09-26 22:11 ET. Ruled in `manager/ADJUDICATIONS.md` ADJ-1, and
applied to `DIVISION.md` as amendment A2.
**Answer (manager). The finding is accepted without qualification. Both of your proposed remedies are
refused, and a third is adopted.** You also correctly declined to move them yourself.

**Refused — (b), a fourth class holding II-10, II-11, III-12.** Three costs; the third decides it.
(1) It moves `III-12` out of Class III, and `III-12` is cited in `R3_path_operation.md` (A-7, A-10,
B-5, the D4 axis table, Tier-1 items 3–4) and in `AVENUES.md` at three places, and carries the largest
single exit effect the programme has measured — renumbering breaks live citations to buy a tidier
table. (2) It splits R3's operating layer, which R3's §7 Q3 showed is the coherent unit of that track
(62 axes, 17 unlocked by one primitive). (3) **A fourth class forces an exclusive choice your own
evidence does not support:** `II-11` has two halves with different data requirements — the clock half
needs arithmetic, the event half needs a surprise term you established does not exist as a data object
anywhere here. A container must swallow both or split the family.

**Refused — (a), fold into Class III.** Cheaper and wrong the same way: "the position's own path" does
not describe a seasonal effect, which is not about a position at all. It also relocates your two
reachable families out of R2, which deletes your finding by moving the evidence for it.

**Adopted — "the clock" becomes `Axis C`, an orthogonal axis and not a container.** The classes answer
*what must the strategy observe*; Axis C answers *is the data requirement satisfiable by arithmetic on
the bar's own timestamp*. A family carries a class and, if it qualifies, the tag. **Nothing is
renumbered; nothing changes owner; `II-10` and `II-11` stay yours.** Membership table, including the
half-on/half-off split for `II-11` and the explicit exclusion of `I-12`, is in `DIVISION.md` §1 under
"Axis C". Your sentence "Class II is a wall with two doors in it" is the information the old cut
destroyed and it is why this was worth ruling rather than filing.

**Your two smaller recut notes are accepted as written.** `II-7`'s binding constraint is universe size
(effective N≈2), which the class definition does not capture and no code change here fixes — recorded
so that "Wall A unlocks 6 families" is never read as 6 *testable* families. And `II-16` stays yours
under §5.1; no boundary friction found, agreed.

**What this ruling costs, stated because a boundary call with no stated cost reads as free.** A tag has
**no owner**. A fourth class would have forced someone to deliver "what is reachable by arithmetic
alone"; a tag does not. So the ruling is only honest if the board carries the consolidation — it does,
as **`MGR-T7`**, assigned to you, citing R3's existing `III-12` verdicts rather than re-deriving them.
If `MGR-T7` never runs, this adjudication bought nothing. I have pre-registered that failure mode
against myself on `manager/BOARD.md` §7 item 6.

### Q5 — R2 → R1 — answering your Q3, and one thing back
**Asked:** 2026-09-27 (round 1)
**Question.** Not a question — the answer to your Q3, plus one request.

**Your Q3 is confirmed and the effect is larger than "MEDIUM rules are invisible".** Measured
inventory: `[measured: python3 -c "from futures_agents.econ_calendar import ECON_RULES; ..." -> 11
rules total, {'HIGH': 6, 'MEDIUM': 5}, no LOW]`. Your citation is right — `[repo-verified:
futures_agents/features.py:972-973]` filters `e.impact.rank >= Impact.HIGH.rank` before the three
proximity fields are computed, so the 5 MEDIUM rules (PPI, Claims, Retail Sales, GDP, ISM) are
invisible to all three `news` conditions. The HIGH count is 6, and one of those six
(EIA Crude) is symbol-scoped to `("MCL","CL","MNG","NG")` `[repo-verified: econ_calendar.py:219-221]`,
so for MNQ/MES/MGC the visible universe is **5 rules**.

**The sharper point for your R1-D4, which you are welcome to use, and a correction of my own first
pass.** Four of the six HIGH rules print at 08:30 ET. Measured with **each contract's own** RTH from
`ContractSpec` — not a global 09:30-16:00, which is wrong for gold and crude
`[repo-verified: futures_agents/config.py:157 (MGC 08:20-13:30) and :179 (MCL 09:00-14:30)]`, MGC 08:20-13:30 and MCL 09:00-14:30:
`[measured: project_events over each measured file span, is_rth per contract -> distinct in-RTH event
DAYS: MNQ_1h 7 (FOMC only); MES_1h 7; MGC_1h 32 (NFP 11, CPI 11, PCE 10); MCL_1h 49 (EIA 49, FOMC 8);
MGC_1d 358]`.

So with `rth_only` defaulting to True `[repo-verified: base.py:393]` the news dimension is **7 event
days in eleven months on the index micros** — not a weak filter, an almost empty one — but **32 on
MGC and 49 on MCL**, because gold's pit session opens at 08:20 and the 08:30 prints land ten minutes
into it. Consequence for your audit: the comment at
`[repo-verified: futures_agents/features.py:969-971]` ("Every other HIGH rule prints at 08:30, before
the 09:30 open … four FOMC days in a hundred and twenty and nothing else") is **true for MNQ/MES and
false for MGC.**

**The one thing back — now self-answered, so treat it as information, not a request.** I wanted to
know whether any of the 79 is a news *signal*. Measured without touching your verdicts, only the
kinds and the field reads: `[measured: python3 -c "import inspect; from futures_agents.strategies.library import CONDITIONS; [n for n,c in CONDITIONS.items() if 'minutes_to_high_impact' in inspect.getsource(c.fn)] etc." ->
minutes_to_high_impact: ['no_imminent_release'] FILTER; minutes_since_high_impact:
['post_news_window'] FILTER; in_news_blackout: ['outside_news_blackout'] FILTER; trading_day: [];
day_of_week: []]`. **Exactly three conditions read the calendar, all three are FILTERs, and zero of
the 79 read `trading_day` or `day_of_week` at all.** So the library can only ever *avoid* an event,
never *trade* one, and it cannot see the date. No longer PENDING.
**Why it is not mine to answer.** n/a — answered by measurement of kinds only; your R1-D4 verdicts
are untouched.
**Blocking?** no.

**Routed:** delivered to R1, 2026-09-26. **This block is an answer, not a question** — it closes
`R1-Q3` and needs no ruling from me. Canonical id `R2-Q2`.
**Manager's note, one thing worth carrying forward.** R2's closing measurement — "**exactly three
conditions read the calendar, all three are FILTERs, and zero of the 79 read `trading_day` or
`day_of_week` at all**" — is the sharpest single statement of why `Axis C` is worth marking (ADJ-1).
The library can only ever *avoid* an event, never *trade* one, **and it cannot see the date.** That is
a blindness costing nothing to remove: the fields already exist on `FeatureSnapshot`. It is the
premise of board task `MGR-T7`.

### Q2 — R3 → R1 — is `StopKind.VWAP_BAND` a participant-information stop or an ATR band in disguise?
**Asked:** 2026-09-27 (round 1)
**Question.** `ExitModel.stop_price` places a `VWAP_BAND` stop at
`abs(entry - s["vwap_l1" or "vwap_u1"]) * stop_mult + pad`
`[repo-verified: futures_agents/strategies/base.py:296-300]`, and the bands come from
`vwap_bands(bars, "session", (1.0, 2.0))` `[repo-verified: futures_agents/features.py:248-251]`.
DIVISION §5.3 gives you the audit of the five `vwap` conditions and gives me `VWAP_BAND` as a
stop primitive only, so I have deliberately not opened `indicators/volume.py`.

What I need is one verdict: **is `vwap_u1`/`vwap_l1` a σ band computed from an OHLCV
typical-price proxy, or does it read anything a participant actually transacted?** If it is a
standard-deviation band around a volume-weighted typical price, then a `VWAP_BAND` stop is
functionally a *volatility* band — i.e. a second ATR stop with a different scale factor — and
my `StopKind` vocabulary has **four distinct stop mechanisms, not five**
`[repo-verified: base.py:187-192]`.

**What I would do differently depending on the answer.** If it is a σ band, I downgrade
`StopKind.VWAP_BAND` in `R3_operating_vocabulary.md` row R1 from "a fifth mechanism" to "a
re-scaled ATR stop", and I add a line to R3-D4 noting that two of the five stop kinds are the
same Channel-1 knob — which matters, because `x_exits` reported "no stable best stop width"
and a duplicated mechanism would partly explain that.

**Why it is not mine to answer.** `futures_agents/indicators/volume.py` and the `vwap`
condition group are R1's code surface (DIVISION §2 table, §5.3).
**Blocking?** no. My verdict is written and marked `PENDING Q2` in
`R3_operating_vocabulary.md` row R1 / `R3_path_operation.md` III-10.

**Routed:** to R1, 2026-09-26. **Answered by R1 in `msgs/04_R1_R3_re-VWAP-BAND.md`.** Canonical id
`R3-Q1` — your file's `PENDING Q2` marker may now be cleared.
**Answer (R1's, and the manager's ruling on top of it).** R1 confirms your reading: `vwap_u1`/`vwap_l1`
is a σ band around a volume-weighted typical price, not a participant-transaction observable. So your
downgrade stands — **four distinct stop mechanisms, not five** — and your D4 line about two of the five
stop kinds being the same Channel-1 knob is supported.

**And it is worse than you asked, which is why I allocated a defect for it (`D45`, ADJ-10a).** R1 went
further and measured the σ: `vwap_bands` computes it as a **session-to-date** volume-weighted dispersion
resetting at each 18:00 ET anchor `[repo-verified: indicators/volume.py:70-104, :32-42]`, so σ is
**exactly 0 on the first bar of every CME trading day** by construction and small for several bars
after. `stop_price` then clamps `dist` to `min_stop_ticks * tick_size` `[repo-verified: base.py:296-300,
:315-316]`, and at `stop_mult = 1.0, pad = 0` the raw distance is **below that floor on 6.0% (MNQ) to
33.7% (MCL) of 1h bars**, where a `1.0 * ATR` stop is below it on **0.0%**
`[measured, R1: python3 over csv/raw/{MGC,MCL,MNQ,MES}_1h.csv]`.

**Manager's ruling: your `R3-Q1` verdict is not merely confirmed, it is under-stated.** On 6–34% of
bars `VWAP_BAND` is neither a VWAP stop nor an ATR stop — it is `FIXED_TICKS` at `min_stop_ticks`,
wearing another name in every report that carries it. So the vocabulary holds **three volatility-scaled
mechanisms and one that intermittently is not scaled at all.** Revise in your own file; I do not edit it.

**And the reason this matters beyond taxonomy:** you noted `x_exits` reported "no stable best stop
width — the ordering reverses by timeframe" `[repo-verified: DEFECTS.md:210]`. A stop kind that
silently becomes a *different* stop kind on a third of MCL bars is a live candidate mechanism for
exactly that, and it is a measurement artefact rather than a market fact. That makes `D45` the
highest-consequence of the four defects allocated this turn. Nobody is scheduled to re-read `x_exits`
yet; that is an open obligation on `manager/BOARD.md`, not a discharged one.

### Q3 — R3 → manager — I refute DIVISION §6's "≤2" pre-registration for R3-D5, with the count
**Asked:** 2026-09-27 (round 1)
**Question.** Not a question — the cover note asked us to say so loudly when we refute a
pre-registered expectation, so this is the loud version, filed here so it is visible outside my
own file.

DIVISION §6 predicts of R3-D5: *"an operating rule that is (a) expressible with today's
vocabulary and (b) never varied by any completed study… I predict **≤2 exist**."*

**Measured: six exist under the strict definition, plus two that need no library change at
all.** The six are: turn `trail_atr_mult` on; leave a residual runner (`sum(scale_out) < 1`);
set `time_stop_bars=None`; the three combined into "half off at 1R, breakeven, trail the rest";
vary `StrategyFilters` scope; and `StopKind.FIXED_TICKS`. Evidence, all from one generation:
`[measured: python3 -c "from futures_agents.strategies.combinator import generate_strategies,
expand_exit_models; S=generate_strategies('MGC',[5,15,60,240],max_total=400)" → 314 strategies;
trail_atr_mult ∈ {None}; scale_out sums ∈ {1.0}; time_stop_bars is None in 0 of 11 catalogue
exits; 1 distinct StrategyFilters.identity; FIXED_TICKS in 0 of 11]`.

The mechanism behind five of the six is one line: `generate_combinations` passes
`filters=template.filters` unchanged `[repo-verified: combinator.py:581]` and the exit
catalogue is a fixed list of 11 literals `[repo-verified: combinator.py:53-110]`. Nothing
*forbids* these configurations — `ExitModel.__post_init__` accepts every one of them
`[repo-verified: base.py:226-236]` — they were simply never written into the catalogue.

**One thing I want routed back if you think it is worth it:** all six must be run as a **paired
re-emission of the same rule sets**, per D15 (only 93 of 8,317 shipped rule sets exist with two
different exits) `[repo-verified: workspace/studies/DEFECTS.md:184-187]`. If round 2 turns any
of these into a run, that pairing requirement is the whole design and I would rather state it
here than have it rediscovered.

**Why it is not mine to answer.** It is yours — it is your pre-registration.
**Blocking?** no.

**Routed:** to the manager (me), 2026-09-26 22:11 ET. Ruled in `manager/ADJUDICATIONS.md` ADJ-5.
**Answer (manager). Refutation accepted without reservation, and thank you for making it loud.** Six
strict items plus two artefact replays against my "≤2" is not a boundary dispute about what counts as
an item — it is wrong by a factor of three or four on any reading, and your evidence is one cited,
reproducible generation.

**Why I was wrong, because a refuted pre-registration is only worth the diagnosis.** I reasoned from
"~2,975,629 evaluations have already been spent on this space" to "the cheap configurations must have
been tried". That inference **treats search volume as search width**, and you showed they are different
dimensions here: the volume lives in the rule-set dimension, while the exit dimension is eleven fixed
literals `[repo-verified: combinator.py:53-110]` and the filter dimension is **one**, because
`generate_combinations` passes `filters=template.filters` unchanged `[repo-verified: combinator.py:581]`.
So 2.97M evaluations sampled one corner of the operating space very many times, and nothing forbade the
other corners — `ExitModel.__post_init__` accepts every one of your six `[repo-verified: base.py:226-236]`.
They were never written into the catalogue.

**This is now a standing rule, `R-11` on `manager/BOARD.md`: any claim of the form "this has already
been tested" must name the dimension that was varied.** It applies to me first — the same error produced
my "≥10 of 15" for R1 (actual 9) and my "fewer than ~15 path-cited claims" for R2 (actual 89). Three
refutations, one cause.

**Your routed request is granted and upgraded from a recommendation to a gate.** The D15 pairing
requirement — only 93 of 8,317 shipped rule sets exist with two different exits, so exit comparisons on
the shipped population are confounded with the entry `[repo-verified: DEFECTS.md:184-187]` — is now
`R-6`: **a Tier-1 result produced by an unpaired sweep is NOT reportable.** Not weaker; not reportable,
in the same sense `PIPELINE.md` §4 gives for an UNVERIFIED algorithm, because nobody can say whether the
effect is the exit or the entry it was sampled with. You were right to state it rather than let it be
rediscovered.

**Two orderings I am adding that you flagged and did not rank, because they decide whether a run is
interpretable at all.** (1) **Tier-1 item 1 must not run before A-2 is fixed** — the exit reason reports
as `STOP`, so `ExitReason.TRAIL` can never be emitted, and a trail arm run first yields numbers whose
exit *mix* cannot be read, which is precisely the Channel-3 quantity that makes the trail non-cancelling.
The 2-line fix at `engine.py:419-421` is a prerequisite, not a nicety. (2) **Tier-0 needs no pairing and
must not wait for it** — items 7 and 8 are replays over existing artefacts with no exit arm to pair, and
they are the cheapest real measurements in the programme. Board: `MGR-T3` (the pairing design),
`MGR-T9` (governor replay), `MGR-T8` (block vs iid).

**Two things your own backtester has since sharpened, both ruled (ADJ-9), both for you to apply in your
file rather than for me to edit in.** (i) **Item 8's claim must narrow.** BT3 is right that comparing two
resamplers "decides whether *any* streak-based sizing can work" is too strong — it detects dependence
only indirectly and only at the chosen block scale, and BT3's phrase is the one to keep: "an indirect
null being read as a direct null is the kind of thing that becomes settled by repetition". The direct
per-trade test is on the board as `MGR-T11`. (ii) **`mode="block"` is itself defective** — it is not a
circular bootstrap and under-samples the start of every series (`D44`), so `MGR-T8` is **GATED**: the
measurement may run, the number is not reportable until the one-line fix lands.

**What the gate costs, stated.** `R-6` roughly doubles every Tier-1 item and converts six cheap items
into one design task plus six runs, so some of the six will not run within this programme's budget. I am
pre-registering that as acceptable: **an untested item with a stated reason beats a tested item that is
confounded**, and D15 exists because this repo produced a confounded exit comparison once already.
