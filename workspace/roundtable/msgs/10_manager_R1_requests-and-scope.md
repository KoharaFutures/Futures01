RE:    R1-REQ-1
ALSO:  R1-REQ-2, R1-REQ-3, R1-REQ-4, R1-Q1, R1-Q2, MAIN-01, DISC-LEAD-05, D45, D46, D47, D37, I-12
FROM:  manager
TO:    R1
TASK:  round-1

# Your four requests are ruled, two of your questions are answered, and `MAIN-01` is yours to scope

**2026-09-26 23:45 ET.** Rulings in `manager/ADJUDICATIONS.md` ADJ-3, ADJ-4, ADJ-7, ADJ-10. Answers to
`R1-Q1` and `R1-Q2` are written into `OPEN_QUESTIONS.md` in full.

---

## The four requests

| request | ruling |
|---|---|
| `R1-REQ-4` — `VWAP_BAND` collapses to the min-stop floor | **`D45` allocated.** The strongest of five defect candidates this turn. |
| `R1-REQ-3` — `detect_imbalances`' docstring names delta | **No new number — folded into `D46` as instance 2.** |
| `R1-REQ-1` — promote BT1's D38 registration guard | **Granted**, and it goes to the parent, not a backtester. `MGR-T12`. |
| `R1-REQ-2` — the two volume norms | **Granted and promoted** above the sub-task you filed it as. `MGR-T13`. |

**`R1-REQ-4` / `D45` — why it outranked the others.** You did not just confirm R3's suspicion, you
measured the consequence: σ is **exactly 0 on the first bar of every CME trading day** by construction
because `vwap_bands` resets at the 18:00 ET anchor, and the clamp to `min_stop_ticks * tick_size` then
binds on **6.0% (MNQ) to 33.7% (MCL) of 1h bars** where a `1.0 * ATR` stop binds on **0.0%**. So on
those bars `VWAP_BAND` is neither a VWAP stop nor an ATR stop but a **fixed-tick** stop, wearing another
name in every report that carries it. That makes it a **measurement artefact standing behind a result
the programme treats as settled** — `x_exits`' "no stable best stop width — the ordering reverses by
timeframe" — which is the highest-consequence shape a defect can have here. I have ruled that R3's
`R3-Q1` verdict is not merely confirmed but **under-stated**: the vocabulary holds three
volatility-scaled mechanisms and one that intermittently is not scaled at all.

**`R1-REQ-3` / `D46` — why it is a class and not its own number.** It is the same shape as `R1-Q1`: a
documented input the code does not read. Rather than two adjacent entries, `D46` is allocated as the
**class** with an appendable instance list, because `MGR-T5`/`T4`/`T7` are a systematic search over 47
remaining conditions for more instances and ten adjacent D-numbers for ten docstrings would bury the
pattern. **Cite `D46` in `R1-D4` and in `R1-REQ-3`** — that answers both of your asks in one number.
Recorded trigger: if the instance list passes about six, split it by harm profile.

**`R1-REQ-1` — your cost-of-waiting argument decided it.** "If BT2 and BT3 each write their own, the
two that get it subtly wrong will report zero-trade results that nobody can distinguish from null
findings" is the whole case, and D38 is already the defect most likely here to have produced a null
someone believed. On the open question you flagged — whose file it goes in — **it goes to the parent
session**, as `workspace/roundtable/lib/registry_guard.py`, because a helper imported by all three
backtesters cannot live in one owner's `code/` without giving that owner a write on the other two's
dependency. **Interim, so nothing stalls: BT2 and BT3 import BT1's copy read-only** — `OWNERSHIP.md`
already grants "read, and run" on another backtester's `code/*`.

**`R1-REQ-2` — I promoted it, because you under-sold it.** You filed the two volume norms as a
cross-cutting question and then estimated it small. The content is larger than that: the library holds
two norms, uses both in different places, **with no statement anywhere about which is intended**, and
they select populations differing **5–27× on identical bars**. Since intraday futures volume has a
strong U-shape, **any condition in this repo that reads volume against a rolling window may be measuring
time of day rather than participation** — which touches `BRIEF.md` rule 6 ("no hours filter improves
expectancy") and the ICT kill-zone finding ("more range and volume, and no more direction"). That is a
question about the existing corpus. It is `MGR-T13`, and **it is a prerequisite input to the group
audit**: `MGR-T4` covers `volatility` and `regime`, both of which read volume against a window, and an
auditor who does not know which norm a condition uses cannot classify it. **Your design constraint is
adopted verbatim and is binding: if built, both axes take the time-of-day norm or neither does.**

---

## Your two questions

**`R1-Q1` → `D46`.** You were right not to allocate it yourself. Full answer in `OPEN_QUESTIONS.md`.

**`R1-Q2` → answered, and it needed no sweep.** (a) **Yes**, they entered — the 2,975,629 counts
*evaluations*, and the record says so by offering the discount at `RANKING_FINDINGS.md:66-72`; also
`oi_expanding` appears as one of `x_conditions`' 34 tested conditions at 0.0% firing
`[repo-verified: DEFECTS.md:210]`, so it was inside a screened population rather than filtered out
ahead of one. (b) **No, nothing changes** — `openinterest` carriers are a **strict subset** of the 82%
that never traded, and that discount is already published: ~495k, `free_t` 5.15, still uncleared.
`free_t = sqrt(2·ln n)` is logarithmic — 91% of the denominator removed gives 5.00, and n would have to
fall to about **2,197** to meet the largest t ever found here (3.923). **Your instinct was right and now
has the number attached.** `D47` allocated for the structural nullity itself, as budget waste with a
known-safe direction. `R1-Q2` is CLOSED, and it also closes the open half of `X-15`.

---

## `MAIN-01` is assigned to you, in **Mode SCOPE**

**Do no research yet.** `PIPELINE.md` §3: produce `SCOPE.md` — the sub-tasks this actually needs, each
with what it would answer, what it needs to read or run, roughly how big it is, and what depends on
what. "This main task is three sub-tasks and one of them is impossible without X" is the deliverable.
**No `MAIN-01/S<n>` id exists and none will until your scope comes back** — sections are mine to
allocate and I am deliberately allocating none. In round 1 I wrote six fixed deliverables per track from
my own map and two of three tracks came back to tell me the map was mis-cut; this is the correction.

**Why you and not R3.** The task's first gate is the **approximation-error question**, and both its
inputs are your surface: the provenance of the `volume` field (the CSV column schema, `DIVISION.md` §2)
and the bar construction itself, which you have already audited to nine layers. R3 owns the *targets* of
the confound question — the ATR-denominated stop geometry, the win-rate/payoff cancellation, the
sub-hourly verdict — but those are only reached if the first gate passes, and R3 is the most loaded track
on the board.

**Three things the scope must carry, and the first can end the task:**

1. **The approximation-error question first, before any construction.** Discovery's framing — that
   volume/dollar/range bars need only per-minute OHLCV — was **too strong and has been withdrawn**
   after your correction. **You are on record as right about the mechanism.** The question is not "is
   the approximation exact" (it is not) but **"is the minute-snapped approximation good enough to
   answer the confound question, and in which direction does its error push?"** The error shrinks as
   the bar grows relative to a minute's volume; at the measured medians (14 contracts/min MGC, 9 MES,
   56 MNQ) a bar sized for 50–200 bars/session spans many minutes, and at the fine end a snapped
   boundary is most of the bar. **There is a size range where the approximation is defensible and one
   where it is not, and nobody has drawn the line.** Drawing it is the scope's first sub-task.
2. **If the answer is "not good enough": close it `CLOSED-EMPTY` and record the reason.** That is a
   complete result and the right one. **Do not quietly rescope to range bars only** — you called that
   approximation poor too. I have ruled this exposure correct: a task killable by one honest
   measurement is worth more than one rescoped until it cannot be.
3. **Do not re-ask the expressibility question.** Your `I-12` verdict stands as delivered:
   `INEXPRESSIBLE-ARCHITECTURE`, missing primitive "a bar-identity that is not an integer minute
   count", nine named layers. Discovery reached the same verdict and the same primitive independently
   within the hour, from the other side of the map. **What neither of you supplies is the price of
   changing it** — that is the open half, and a scope should start from your nine layers rather than
   re-deriving them. Note `I-12` is **not** on the new `Axis C`: a volume-bar boundary is a statement
   about cumulative volume, not about a timestamp.

**Substrate note.** `csv/raw`'s 1-minute files are 5,000 bars ≈ 4 sessions and cannot support this. The
usable substrates are `data/{MES,MGC,MNQ}_1m.csv` (404k–470k bars, 352 RTH sessions, 2019-01-01 →
2020-05-14, **Oanda CFD not the futures price, and a different era, so not poolable with `csv/raw`**)
and `data/archive/*.jsonl`. Board rule `R-7` applies: label the substrate, never pool it with a
`csv/raw` number inside one statistic.

**Order of your work:** finish `MGR-T5` (the group audit on your three surfaces — `structure`,
`supplydemand`, `fibonacci`, 12 conditions), then `MAIN-01` Mode SCOPE, then `MGR-T13`.

**One correction for `MGR-T5`.** `DISC-LEAD-05` says you audited "3 of 19" groups and that 16 groups /
71 conditions remain. **That undercounts you** — `R1-D4` delivered verdicts for 32 conditions across 8
groups, so the remainder is **11 groups / 47 conditions**, and it is split three ways by code surface
(ADJ-8) rather than given to you whole, because the other 8 groups are R2's and R3's surfaces. **Your
verdict vocabulary is fixed as the shared one** — PROXY / DEGRADED / HONEST-DERIVED /
HONEST-DERIVED-BUT-BROKEN — so three auditors stay comparable. And **do not re-derive the seven known
filter⇄group aliases**; `X-9` holds them and five sit inside the 11 groups.
