# Burst 01 — seed the ledger, then one sweep

**Agent:** discovery. **Date:** 2026-09-27. **Owner of this file:** discovery.
**Wrote:** `AVENUES.md` (new), `MAIN_TASKS.md` (new, MAIN-01), this file. Nothing else.
**Ran:** reads, `grep`, and four `python3 -c` inspections (row counts, timestamp spans, volume
quantiles, usage greps). **No backtest, no sweep, no expectancy, no z-score.**

---

## Part A — seeding

**Question.** What ground is already covered, and how much of it is genuinely closed rather than
merely mentioned?

**Read.** `PIPELINE.md`, `OWNERSHIP.md`, `BRIEF.md` (all in full); `DIVISION.md` §1 + §4 + §5 + §6 +
§8–§10 + Appendices A and B; `scan_reports/README.md` and the headline + conclusion of all four
reports; `workspace/studies/{STRUCTURE,ORB_ICT}_FINDINGS.md` headings and the sections the reports
pointed at; `workspace/roundtable/research/R1_flow_auction.md`; `OPEN_QUESTIONS.md` (Q1–Q3);
`msgs/01_manager_all_division.md`; `check_ownership.py` (to confirm my three paths are mapped to
`discovery` — they are, at lines 25–27).

**Result.** 69 avenues logged: the manager's 53 families (I-1…I-15, II-1…II-19, III-1…III-19) plus
16 cross-cutting `X-` avenues that are where most of the ~2.98M evaluations' effort actually went
and that had no home in a family taxonomy. Verdicts: **8 `CLOSED-EMPTY`, 1 `CLOSED-FOUND`,
36 `OPEN-PARTIAL`, 24 `DEFERRED`.**

**The number that mattered most.** 17 rows carry a stopping point of **"named only"** — the manager
listed them, nobody investigated them. I wrote the closure test into the top of `AVENUES.md` before
filling any row, because the tempting error here is obvious and one-directional: 53 families under
three mechanism classes *reads* like coverage, and marking them closed would make the ledger lie in
the direction of never looking again. I also added a **"rows I was tempted to close and did not"**
table — eight rows where a `CLOSED` verdict was available and I declined it, with the reason — so
that a later burst can overrule me on the record instead of by accident.

Two things I want to flag about the seeding rather than bury in a row:

- **"0 strategies reached 20 trades" is evidence about the library, not the family.** This repo has
  found four separate degenerate detectors (`session_extreme_sweep` self-referential,
  `range_position_extreme` a guaranteed zero inside REVERSAL, `opening_range_breakout` firing on 4
  of 4,256 bars, the shipped ORB condition with neither a first-break nor a session gate). Any
  avenue whose only negative evidence has that shape is `OPEN-PARTIAL`, not closed.
- **R1/R2/R3 are writing live.** Only `R1_flow_auction.md` existed when I read; rows say
  `IN FLIGHT (R<n>)` where a round-1 deliverable claims the avenue. That is a claim, not a verdict,
  and a later burst must re-read those files before treating such a row as advanced.

---

## Part B — one sweep

**The question I asked.**

> Every one of this repository's ~2,975,629 evaluations was computed on wall-clock bars. Sampling a
> price series on a clock is a modelling choice with a real alternative literature — volume, dollar
> and range bars. Is "what a bar is" a variable nobody here has ever varied, is the alternative
> reachable with the data on disk, and could the choice bear on findings this repo already treats as
> settled?

**Why this avenue and not another.** From the 17 genuinely-unexplored rows I wanted the one that
(a) nobody currently holds, (b) has its data already on disk, and (c) speaks to the manager's §7 Q1
— "is our null result a property of the market, or of our information set?" I-12 proposes a **third
possibility that is neither**: the sampling clock. The three strongest rivals all lost on (a) or on
being one experiment rather than an avenue, and are logged as LEAD-01/02/03 in `AVENUES.md` instead.

**What the sweep established**, in the order I found it:

1. **Genuinely unexplored.** `[measured: grep -rn "tick_bar\|volume_bar\|dollar_bar\|range_bar\|
   renko\|constant.volume\|bar_type\|BarType" futures_agents/ --include=*.py | grep -v __pycache__
   → no matches]`; `[measured: "tick bar" → 0 files, "dollar bar" → 0 across workspace,
   futures_agents, scan_reports, research, docs, desk, reports, scripts]`.
2. **A bar is definitionally a wall-clock interval, throughout.** `BarSeries` = "a series of
   **same-duration** bars" (`bars.py:160`), `Bar.minutes` commented "bar duration" (`bars.py:43`),
   `SymbolFrame` builds every timeframe by `resample(base, tf)` on integer minutes
   (`features.py:795-812`), `align_bucket` snaps to the hour and to the 18:00 ET roll
   (`bars.py:138-156`), and `[measured: 74 references to .minutes in futures_agents/]`.
3. **The blocker splits the family in half.** Tick, imbalance and run bars need the tape (blocked by
   data). Volume, dollar and range bars need only `(high, low, close, volume)` per minute, which
   exists — so their blocker is *architecture with the data present*, the rarest cell in the
   manager's expressibility matrix.
4. **The dispersion that motivates the whole idea is large and measured.** Per-1-minute volume
   p10/median/p90 = 3/14/96 (MGC deep archive), 2/9/57 (MES), 7/56/286 (MNQ), 68/177/470 and
   63/248/1863 on the frozen snapshot. A 1-minute bar carries a ~30× range of activity depending on
   when it falls, and every per-bar statistic in the library counts each as one observation.
5. **A by-product that bears on two other rows, so I wrote it into the ledger as an addendum rather
   than keeping it here.** The frozen snapshot's sub-hourly files are ~5,000 bars each, which is
   **4 trading sessions at 1m, ~19 at 5m, ~41 at 15m/30m**. BRIEF rule 7 ("sub-hourly is a
   graveyard") is phrased as a timeframe law and, on `csv/raw`, rests on that sample. I did not and
   do not claim the rule is wrong — the ORB study's deep 1-minute replication was also negative. I
   recorded the sample basis and the two deeper stores that exist and have never been used for it.

**Where I stopped, and why there.**

I stopped at the point where I could name what depth is needed and could no longer make progress
without doing that depth myself. Concretely, I stopped when the next question became *"what does the
`volume` field in `data/*_1m.csv` actually count?"* — because answering it means opening the CFD
provenance, and the question after it is *"how much error does allocating a minute's volume across a
bar boundary introduce?"*, which is construction. Both are in MAIN-01 as unknowns for whoever scopes
it. Writing a sampler would have been the interesting thing to do next and it is exactly the thing
that would have turned this burst into the top-down shape this pipeline replaces.

Two other stopping decisions, stated so they are not mistaken for oversights:

- **I counted the 74 `.minutes` call sites and did not classify them.** Classifying them *is* the
  architecture answer, and it is a researcher's section, not a discovery sweep.
- **I did not open `costs.py`.** A non-time bar changes the number of decision points and therefore
  interacts with the cost model, which already has a known under-charging defect on multi-target
  exits — but it is R3's surface and it is depth.

**Then I stopped.** One sweep, one main task, no second sweep, no decomposition of MAIN-01.

---

## Things I cannot fix myself, for the parent session to route

1. **`DIVISION.md` §1 files all of I-12 under Class I.** Three of its six schemes need only OHLCV, so
   half the family sits in a class defined by needing sub-bar information. This is the structural
   reason it went unexplored: R1 correctly meets the tape blocker and stops, and R3 owns the
   OHLCV-only world but not the family. The manager owns `DIVISION.md`; I have not touched it.
2. **`OPEN_QUESTIONS.md` Q1 and Q2 (both R1's) are unanswered** and Q2 bears on `X-15` in my ledger
   — whether structurally-null `openinterest` candidates entered the 2,975,629 denominator. The
   manager routes; I cannot append there.
3. **One datum belongs to R1 and I logged it in my addendum rather than their file:** zero-range
   1-minute bars are 12.28% of `data/MES_1m.csv` and 3.54% of `data/MGC_1m.csv`, and R1 established
   that `estimated_delta()` returns exactly `0.0` when range ≤ 0. On a 1-minute MES series roughly
   one bar in eight therefore has a delta of exactly zero by construction.

---

## Addendum, same burst — a false claim I wrote, and what it cost

While reconciling against `R2_*`/`R3_*` (which appeared on disk after my 01:23 read of `research/`),
I wrote into `AVENUES.md` that none of the round-1 files touched bar sampling. **That was false**, and
the grep I pasted to support it disproved it in the same command: it returned
`R1_flow_auction.md` and `R1_data_requirements.md`. R1's file grew from 223 to 1,700+ lines while I
worked and now carries a full §I-12 entry at `:1098-1135`.

I appended the correction to `AVENUES.md` rather than editing the false line away. Two reasons, and
the second is the one that matters: a ledger that silently repairs itself cannot be audited, and the
correction turned out to carry the most useful content of the whole burst.

**What the correction is worth.** R1 reached **INEXPRESSIBLE-ARCHITECTURE** with the same missing
primitive I did — "a bar-identity that is not an integer minute count" — independently, from the
Class I side, within the same hour. And R1 contradicts one of my claims: I said volume, dollar and
range bars need only 1-minute OHLCV; R1 says a volume-bar boundary is a path statement that happens
*inside* a minute and the approximation is poor. **R1 is right about the mechanism.** MAIN-01 now
carries that contradiction as the first question a scope must settle, and explicitly authorises
closing the task `CLOSED-EMPTY` if the approximation error is too large — which is a better main task
than the one I wrote an hour ago.

**What I did not do.** I did not withdraw MAIN-01 and re-sweep. The question it asks (is the clock a
confound in settled findings?) is not the question R1's row answers (can the library express the
family?), and burst 01 has had its one sweep.

**LEAD-05, logged and not pursued, and I think it is burst 02's sweep.** R1 audited **3 of 19**
condition groups for name-versus-arithmetic and found **3 of 3** misnamed, and reports that half a
generated strategy set carries one of those three proxies (50.7% of a 284-strategy sample, 100% of
the REVERSAL group). **Sixteen groups and seventy-one conditions have never been audited that way**
(`AVENUES.md` X-8). No data needed, no code needed, and it determines how every one of ~2.98M
evaluations should be read. I am not starting it in this burst.
