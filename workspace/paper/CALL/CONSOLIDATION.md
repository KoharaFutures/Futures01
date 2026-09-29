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
