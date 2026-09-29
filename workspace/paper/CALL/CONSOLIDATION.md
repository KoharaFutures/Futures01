# CONSOLIDATION — the CALL desk against the REPLAY desk and the research sessions

Written 2026-09-29 00:45 ET by agent CALL, at the account owner's instruction, after he said of
tonight's callouts: **"These are Horrible!"** — twice.

He is right, and the useful part is not the apology, it is that **the desk beside me could already prove
it and I had never looked.** Everything below is read from other sessions' files; nothing outside
`workspace/paper/CALL/**` was modified.

---

## 1. The two paper desks, side by side

| | **CALL** (live, me) | **REPLAY R1** (walk-forward) |
|---|---|---|
| instrument | MGC + MNQ, 15m gate | MES, 60m |
| period | 2026-09-27 → 09-29, live tape | bars 0→3,000 of 11,287 (2024-10 → 2025-03) |
| callouts issued | **11** | **50** |
| fills | **6** | **2** |
| closed | 5 | 2 |
| winners | 2 | **2** |
| losers | **3** | **0** |
| equity | $50,007.80 | **$50,688.86** |
| net | **+$7.80** | **+$688.86** |
| peak | $50,156.56 | $50,688.86 |
| **drawdown** | **$148.76** | **$0.00** |
| measured expectancy | **−0.434R** (n=4, CALL-0002 excluded per N155) | +1.87R mean on 2 fills, not an edge claim |
| placebo / control | **NONE** | **yes, and it runs on every bar** |
| counterfactual on misses | **NONE** | **yes, n=47** |

**The 88× difference in net is not the finding.** Two fills is not a sample and REPLAY says so itself. The
finding is in the last two rows.

## 2. The thing that actually explains "horrible"

**The live desk has issued callouts for two days with no placebo and no counterfactual.** REPLAY has both,
and uses them to say this about its own work, at n=47:

> always-long **+0.263R** vs control **+0.352R** (z **+1.72**) · always-short +0.026R vs −0.016R (z −0.08) ·
> coin-flip +0.222R vs +0.253R (z **+1.23**). *"Nothing above |z| 2, and the long arm's control now exceeds
> the sample."*

So the desk with a control can state that its reads do not separate from chance. **The desk without one —
mine — has been reporting 15m component tallies, seven-frame tables, sigma readings and bias panels every
two minutes for two days, and has no instrument capable of telling the owner whether any of it beats a coin
flip.** That is why nothing in my reporting caught what he caught in one glance. I have been measuring the
process in enormous detail and never once measured whether the process contains information.

That is the answer to "what are these callouts". They are the output of a side-picking instrument that was
never tested against a side-picking placebo.

## 3. Four independent nulls on DIRECTION, from four different instruments

| source | test | result |
|---|---|---|
| REPLAY E2 | variance ratio, heteroskedasticity-robust, MES 60m returns | **random walk.** q2..q24 all p ≥ 0.74, runs z −0.345. Detection floor \|ρ\| ≈ 0.11, breakeven needs **0.18** → *anything profitable would have been detectable, and nothing was* |
| REPLAY counterfactual | its own 47 declined callouts, scored against control | **nothing above \|z\| 2** |
| session 99X1 | key-level breach scan, **5,717 real vs 4,729 placebo levels** | **indistinguishable** |
| repo-wide search | 21,060 strategy candidates | best **t 3.82**, and it is **a placebo**, against `free_t` **5.46**. Largest *t* anywhere: 3.923 |

Four instruments, four nulls, on the one thing my gate exists to produce: **a side.**

**And there is exactly one positive result in the whole corpus, from REPLAY E2:**

> **Volatility *is* predictable (R² = 0.112) and is *directionless*. It sizes trades, it does not choose
> sides.**

My gate is built from EMA position, 40-bar range location and pivot sequence — geometry that responds to
volatility. I have been feeding the one measurable quantity in this market into the one question it is
measured not to answer.

## 4. The behavioural difference, which is the part I can own tonight

REPLAY issued **50 callouts and filled 2.** It logs the other 48 in `missed.jsonl` with `best_r`, `mfe_r`,
`long_r`, `short_r` per miss, and writes `NO_TRADE` rows that say things like *"the structure is the
cleanest downtrend since the record began … AND I HAVE NOTHING TO TRADE IT WITH, which is the honest state
of the desk rather than a mood."*

I did the opposite. Faced with three plans expiring unfilled, I moved entries **toward** the market to get
fills — the sub-EMA and just-above-EMA limits — and that is precisely how CALL-0009 and CALL-0011 filled
on the bar that inverted their own gate (N233, three for three). **REPLAY's 96% no-fill rate is the
discipline; my 55% fill rate is the leak.** Three of my plans carry the tracker verdict *"DIRECTION RIGHT,
TARGET DISTANCE COVERED — trigger was the problem"*: the read was fine and the entry was the defect, and
my response to that was to make the entry easier to reach rather than to stop.

## 5. What the consolidated record says to do, in order

1. **Build the placebo and the counterfactual into the live desk.** Port REPLAY's construction: a
   random-direction control with my own stop/target geometry through my own exits, plus a `missed.jsonl`
   scoring every callout I decline or that expires. Until this exists, no callout from this desk should be
   read as evidence of anything. **This is first because it is the reason the owner had to tell me.**
2. **Pre-register `TP0 = 0.8R, fraction 0.5, stop to breakeven`** and score it against the archive.
   **6 of 6 fills reached ≥ +0.83R MFE; 2 of 5 closed positive** (N261). No exceptions in the record.
3. **Stop selecting sides on evening/overnight tape.** MGC pit is 08:20–13:30 ET, MNQ RTH 09:30–16:00.
   Every plan I registered tonight carries *"outside everything this repository measured"* in its own
   weakness list, on 0.15–0.68× volume.
4. **Use volatility for sizing and for standing down, never for direction** — the one measured result.
5. **Fix entries to fixed structural levels, not moving anchors** (N233/N257), or the plan expires in bars.
6. **Adopt REPLAY's declared-cut counting.** It retired its thesis 5 on *105 declared cuts at free_t 3.05*.
   My gate has never had its search width counted at all.

## 6. Cross-desk contradictions found — and there are none of substance

I looked for places where the desks disagree. There are two apparent ones and both resolve:

- **REPLAY's 2 fills both won; mine mostly lost.** Not a contradiction — REPLAY's n=2 is below any
  threshold and it refuses to call it an edge. Mine is n=4 at −0.434R. Both are consistent with the null.
- **REPLAY trades MES 60m; I trade MGC/MNQ 15m.** Its random-walk result is instrument-specific and does
  not transfer arithmetically. But rule 7 in `BRIEF.md` (11–16% of 5m strategies profitable) and the
  repo-wide 21,060-candidate search both cover my frames, and point the same way.

## 7. Session inventory for this project, as of 00:45 ET

| session | role | state |
|---|---|---|
| `session_01EE6PFk7fGa2tM4KP6dpfWD` | **CALL** — live paper callout desk (this one) | running, 362k/1M context |
| `session_01Aqg8aVp7jcAbzEF7sfZYjA` | **REPLAY R1** — walk-forward, MES 60m, bar 3,000 | idle, review-ready, **760k/1M context — near its limit** |
| `session_01M1u9BYAAVXRo95HBsA2EiA` | parent — research round 4 | **BLOCKED, needs the owner: "set a bar limit (2000, 5000, or end of series)"** |
| `session_01DMSyFfv13VD63wAZx52uWd` | 99X1 — key-level breach scan | complete: real vs placebo levels **indistinguishable** |
| `session_01AaM6papf7S5DgG3PC14es8` | grandparent — 99X2 | **BLOCKED, awaiting plan approval** |

**Two sessions are stalled waiting on the owner, and REPLAY is close to its context ceiling.** Those are
decisions only he can make; they are listed here so they are visible rather than buried in a session list.

---

## 8. Update, 00:50 ET — REPLAY published `SUMMARY.md` and it lands on this desk in four places

The replay desk woke at 00:45, advanced to bar **3,400**, and wrote its own one-page summary. Four of its
findings apply directly here, and two of them cost me claims I had made.

**Its headline number is the one this desk still cannot produce:** placebo separation **z +1.021** against a
`free_t(20)` of 2.448 — **does not clear.** And **0 of 36** stop/target geometries × 3 direction arms reach
|z| 2 on its stand-downs.

### 8.1 Costs — computed here for the first time

REPLAY: *"the round-turn is $2.69 = 2.15 ticks, never counted in any R figure before this run. Break-even
needs 0.081R/trade against a measured gross of +0.0225R."* My equivalents, computed from
`resolve.py:costs_per_contract` (fees + one tick of slippage per side):

| | round-turn | in points | in ticks | hurdle on the live plan | hurdle at the rule-4 floor |
|---|---|---|---|---|---|
| MGC | **$3.44** | 0.344 | 3.44 | **0.0748R** (CALL-0011, $46) | 0.0936R ($36.75) |
| MNQ | **$2.44** | 1.22 | 4.88 | **0.0469R** (CALL-0010, $52) | 0.0529R ($46.12) |

`resolve.py` *does* subtract these, so the ledger is honest — but **I had never reported the hurdle**, and
MNQ's 4.88-tick round-turn is more than double REPLAY's 2.15 on MES. For this desk costs are not the binding
constraint (my expectancy is −0.434R, twenty times the hurdle) — the constraint is direction. Stated anyway,
because REPLAY's point is that an R figure quoted without its cost hurdle is incomplete.

### 8.2 The +0.8R partial I have called "the top deferred item" all night is UNEXECUTABLE

**Every fill this desk has ever taken is 1 contract** — CALL-0002, 0006, 0007, 0008, 0009, 0011, all
`contracts: 1`. You cannot exit half of one contract. The proposal as I stated it, *"TP0 = 0.8R, fraction
0.5"*, cannot be run at any size this account has used, and 2 contracts at the rule-4 floor costs $73.50
(MGC) or $92.24 (MNQ) against a $120 cap.

**The executable forms are different instruments and must be tested as such:**
- **(a)** at +0.8R move the stop to breakeven, hold 1 contract — costs nothing, changes the loss
  distribution only
- **(b)** exit the whole position at +0.8R — converts every 1.5R target into 0.8R and needs a win rate above
  ~55% to beat the current geometry
- **(c)** 2 contracts, halved — doubles risk and only fits an empty book

I repeated the unexecutable version to the owner at least four times tonight. That is the cost of not
checking an arithmetic claim against the sizing floor.

### 8.3 Volume — a missing field read as an absence of trading (N262)

REPLAY found MES's 18:00 ET bar has no volume Mon–Thu. Mine is worse: **26% of MGC and MNQ 15m bars carry no
volume field, and the 102 affected timestamps are identical across the two contracts** — a vendor omission,
not a market fact. `reversal_setup`'s `climax_x` divides the extreme bar's raw volume by the median, and
**MGC's extreme-low bar right now is `00:35` with `v = 0.0`**, so it reports *"NO capitulation volume — a
drift, not a flush"* about a bar that has no volume field at all. **Every `climax_x` figure I have quoted is
suspect, and the "3.12× flush volume" I offered as confluence for MGC 4145.00 is unsupported** — not
disproved, unsupported, which is the honest status.

### 8.4 Touch-count claims — retracted by REPLAY's standard, so retracted here

REPLAY withdrew *"all key-level and touch-count claims"* because its control fabricated touch counts and
tested at 31% higher ATR. **My "five-times-tested shelf" at MGC 4145 and "the morning 30425–30434 base" at
MNQ 30430 are the same family of claim, and I ran no control on either.** The structural parts of that
research — the 78.6% retracement at 30434.72, the 40-bar range floor, and the higher low the desk's own
`swings()` registered at 30427.75 — do not depend on touch counts. The touch counts do, and they are
withdrawn as evidence.

### 8.5 The line from REPLAY worth carrying above all the numbers

> **"Two fabricated figures reached live decisions. Both happened to push me toward the safer action. That is
> luck, not a safeguard."**

Tonight this desk had the same shape three times over: `watch.py`'s 66/34 thresholds, its own `pivots()`, and
its trend test that ignored EMA slope all fed wrong numbers into live reporting, and the N249 capacity bug
told me I had $120 of room when I had $22. **Every one of those four happened to make me more cautious, not
less.** Same luck, same absence of a safeguard.
