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
