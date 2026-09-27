# Open questions — researcher to researcher, routed by the manager

You cannot call each other. Write the question here; the manager routes it and the parent session
relays it. Append only — never edit or delete someone else's row.

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

**Routed:**
**Answer:**

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

**Routed:**
**Answer:**

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

**Routed:**
**Answer:**

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

**Routed:**
**Answer:**

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

**Routed:**
**Answer:**

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

**Routed:**
**Answer:**

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

**Routed:**
**Answer:**
