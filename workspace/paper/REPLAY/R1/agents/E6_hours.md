# E6 — the clock rules, tested on R1's own tape

**Agent E6, REPLAY desk, closed-market window.** Script: `agents/E6_hours.py` (reads only
`visible.jsonl`; writes nothing but this file; does not import `missed.py`, does not touch
`state.json`, does not advance a cursor).

**Brief:** independently test rule 5 ("no intraday entries 15:00–16:00 ET", reported z = −4.43,
median −0.617R, replicated) and rule 6 ("no hours filter improves expectancy"), which are in
apparent tension.

---

## Headline

| | result |
|---|---|
| **Rule 5** | **Does not replicate on this tape.** Measured z **+0.10** against a reported −4.43; median **−0.019R** against a reported −0.617R. The 15:00 hour is the single most *average* cell in the sweep. |
| **Rule 6** | **Holds, emphatically.** No single-hour exclusion comes close. Best available improvement is +0.005R/trade at z −1.26. |
| **Hours clearing `free_t` 2.4864** | **0 of 22** |
| **Hours clearing naive 1.96** | **0 of 22** |
| **The gap between those counts** | **0** — see "The gap is zero, and that is the finding" below |
| **18:00** | mean R **+0.0316**, z +0.41 — unremarkable in R. But its **price** behaviour is anomalous, and the volume defect is now pinned to a specific mechanism. |

The two rules are **not** in tension here, but not for the reason the desk assumed. The tension
was to be resolved by "a specific bad window can exist while general hour-selection fails."
On this substrate there is no bad window at all: rule 6 is true and rule 5 is simply absent.

---

## Population, conventions, and trial count — stated before the numbers

**Engine conventions**, copied from `missed.py` / `A_grid.py` so the figures are comparable:
fill at the next bar's open ± one tick (`TICK = 0.25`); **stop wins a same-bar stop/target tie**;
1.0 ATR stop, 2R target; ATR14 from bars at or before the decision bar, i.e. `atr(f−1)`; flat at
the first 16:00 ET bar at or after the fill.

**Population:** *both directions at every eligible bar* `f in range(20, len(rows))` whose forward
window closes inside the visible tape. Tape = 1,685 bars, 2024-10-06 19:00 → 2025-01-23 23:00 ET,
91 ET dates. **1,587 bars in the 22-hour grid = 3,174 trades.**

**The 22 hours.** The tape carries 23 distinct hours: 18–23 and 00–16 (17:00 is the CME
maintenance halt and has no bars). Hour 16 is the desk's **flat bar**, not an entry hour — a
"trade" there opens and closes on the same bar. So the cycle grid is **hours 18–23 and 00–15 =
exactly 22**, matching the `free_t = sqrt(2·ln 22) = 2.4864` the brief specifies. Hour 16 is
computed and reported separately (section 4) and is **not** in the 22-trial count.

**Unit of observation is the BAR, not the trade — and this matters.** For a `SESSION_CLOSE` exit,
`R_long + R_short = −2·TICK/S` *exactly*. Long and short at the same bar are near-perfect mirror
images, so counting them as two independent observations doubles n while the information is one
bar's forward path. Each bar is therefore scored as the mean of its long and short R. **The mean
is identical either way**; only the SE differs, and the paired SE is the honest one. Pooled-trade
figures are printed alongside throughout.

**Declared trial count: 22.** The rule-5 test and the 18:00 test are *two of those 22*, not extra
trials. The paired/pooled/date-clustered SE variants and the long-only/short-only arms are
**robustness views of the same cells reported together**, not independent searches — but if a
reader insists on counting them as searches, the count is ~66 and `free_t` = 2.89. **Nothing on
this tape reaches either figure**, so the distinction never becomes load-bearing.

**Two confounds, measured rather than hidden.**
1. **Holding window is not constant across hours.** An 18:00 entry has 22.4 bars to the flat; a
   15:00 entry has 1.0. Rule 5's window is also the shortest-horizon window on the tape. The
   `btf` column below makes this visible, and it is the main reason the 15:00 cell looks the way
   it does (6.2% TARGET, 31.2% STOP, 62.5% SESSION_CLOSE, against 32% / 66% tape-wide).
2. **Overlapping forward windows.** All 22 hour-buckets of one ET session read largely the same
   forward path, so hour observations inside a day are serially dependent. A session-date-clustered
   SE is reported for the rule-5 test as a check; it moves the z from +0.104 to +0.161, i.e.
   nowhere.

---

## 1. Mean R by ET hour of entry

Bar unit = mean of that bar's long and short R. `btf` = mean bars to the 16:00 flat.
`z_vs_rest` = Welch against all other hours (primary). `z_vs_all` = against the all-hours mean.

| hr | n bars | n trades | btf | mean R | SE | median R | z vs rest | z vs all | long R | short R | tgt% | stp% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 18 | 72 | 144 | 22.4 | +0.0316 | 0.0818 | +0.5000 | +0.408 | +0.398 | −0.0618 | +0.1250 | 34.0 | 65.3 |
| 19 | 72 | 144 | 21.4 | −0.1064 | 0.0863 | +0.5000 | −1.256 | −1.222 | −0.1599 | −0.0528 | 29.2 | 68.1 |
| 20 | 72 | 144 | 20.4 | −0.0622 | 0.0848 | +0.5000 | −0.742 | −0.722 | +0.0580 | −0.1824 | 30.6 | 66.0 |
| 21 | 72 | 144 | 19.4 | −0.0609 | 0.0847 | +0.5000 | −0.727 | −0.708 | −0.0276 | −0.0943 | 30.6 | 66.7 |
| 22 | 72 | 144 | 18.4 | −0.0258 | 0.0839 | +0.5000 | −0.304 | −0.296 | +0.0417 | −0.0932 | 31.9 | 66.7 |
| 23 | 72 | 144 | 17.4 | +0.0157 | 0.0822 | +0.5000 | +0.208 | +0.203 | +0.1667 | −0.1353 | 33.3 | 65.3 |
| 00 | 72 | 144 | 16.2 | +0.0762 | 0.0795 | +0.5000 | +0.994 | +0.970 | +0.1317 | +0.0206 | 35.4 | 63.2 |
| 01 | 72 | 144 | 15.2 | +0.0554 | 0.0807 | +0.5000 | +0.716 | +0.699 | +0.1250 | −0.0142 | 34.7 | 64.6 |
| 02 | 72 | 144 | 14.2 | +0.0460 | 0.0813 | +0.5000 | +0.592 | +0.578 | +0.1337 | −0.0417 | 34.7 | 64.6 |
| 03 | 72 | 144 | 13.2 | +0.0524 | 0.0808 | +0.5000 | +0.678 | +0.661 | +0.2083 | −0.1035 | 34.7 | 64.6 |
| 04 | 72 | 144 | 12.2 | +0.0341 | 0.0816 | +0.5000 | +0.440 | +0.429 | +0.0417 | +0.0265 | 34.0 | 64.6 |
| 05 | 72 | 144 | 11.2 | −0.0663 | 0.0859 | +0.5000 | −0.782 | −0.761 | −0.0833 | −0.0493 | 30.6 | 68.8 |
| 06 | 72 | 144 | 10.2 | −0.0208 | 0.0848 | +0.5000 | −0.241 | −0.234 | +0.1667 | −0.2083 | 32.6 | 67.4 |
| 07 | 72 | 144 | 9.2 | −0.0055 | 0.0836 | +0.5000 | −0.056 | −0.054 | +0.2083 | −0.2193 | 32.6 | 66.7 |
| 08 | 72 | 144 | 8.2 | −0.0218 | 0.0845 | +0.5000 | −0.254 | −0.247 | −0.0036 | −0.0400 | 31.9 | 66.7 |
| 09 | 74 | 148 | 7.6 | +0.0946 | 0.0780 | +0.5000 | +1.256 | +1.226 | −0.0676 | +0.2568 | 36.5 | 63.5 |
| 10 | 73 | 146 | 6.4 | −0.0225 | 0.0836 | +0.5000 | −0.265 | −0.258 | −0.0313 | −0.0137 | 32.2 | 67.1 |
| 11 | 73 | 146 | 5.4 | +0.0117 | 0.0777 | +0.5000 | +0.167 | +0.163 | +0.0241 | −0.0007 | 30.1 | 63.0 |
| 12 | 73 | 146 | 4.4 | −0.0043 | 0.0725 | +0.3634 | −0.047 | −0.047 | −0.1017 | +0.0931 | 24.7 | 61.0 |
| 13 | 71 | 142 | 3.0 | +0.0266 | 0.0576 | +0.0878 | +0.481 | +0.479 | −0.0440 | +0.0973 | 17.6 | 50.0 |
| 14 | 71 | 142 | 2.0 | −0.0745 | 0.0553 | −0.0158 | −1.329 | −1.329 | −0.2206 | +0.0716 | 12.0 | 45.1 |
| **15** | **72** | **144** | **1.0** | **+0.0024** | **0.0287** | **−0.0191** | **+0.104** | **+0.116** | −0.1147 | +0.1194 | 6.2 | 31.2 |

**All-hours baseline:** n = 1,587 bars / 3,174 trades, mean R **−0.0010**, SE 0.0167.

**Hours differing from the all-hours mean:** *none, by either threshold.* The largest |z| in the
entire sweep is **1.329** (hour 14). Under a true null of 22 tests you would expect ~1.1 false
positives at 1.96; **this tape produced zero**, which is if anything a quieter result than chance.

The `btf`, `tgt%` and `stp%` columns show the one genuinely systematic gradient in the table, and
it is mechanical, not behavioural: as the hour approaches the flat, there is less time to reach
a 2R target, so TARGET rate falls 34% → 6% and SESSION_CLOSE rate rises correspondingly. **That
compresses the variance of the late hours without moving their mean** — which is exactly why the
15:00 cell has the smallest SE in the table (0.0287, a third of the overnight hours') and still
cannot be distinguished from anything.

---

## 2. Rule 5 — the 15:00 hour, specifically

> **Reported:** z = −4.43, median −0.617R, replicated.

| | n bars | n trades | mean R | SE | median (bar) | median (trades) |
|---|---|---|---|---|---|---|
| **15:00 hour** | 72 | 144 | **+0.0024** | 0.0287 | **−0.0191** | −0.0554 |
| all other hours | 1,515 | 3,030 | −0.0011 | 0.0174 | +0.5000 | −1.0000 |
| difference | | | **+0.0035 R** | | | |

| z variant | value |
|---|---|
| bar unit, Welch (primary) | **+0.1039** |
| pooled trades, Welch (inflated n, for comparability) | +0.0433 |
| ET-session-date clustered (72 dates vs 90) | +0.1614 |

**Verdict: rule 5 does not replicate on this substrate.** The measured z is **+0.10** against a
reported **−4.43** — a gap of 4.53, and *the wrong sign*. The 15:00 hour is very slightly the
*better* half of the split. Measured median is **−0.019R** against a reported **−0.617R**, a factor
of 32. The cell does not clear `free_t` 2.486; it does not clear 1.96; it does not clear 0.2.

### Why the reported median −0.617R cannot come from a population like this one — and what that implies

This is the part of the non-replication that is informative rather than merely negative.

For a `SESSION_CLOSE` exit the identity `R_long + R_short = −2·TICK/S` holds *exactly*. A
both-directions population is therefore **symmetric about −TICK/S ≈ −0.017R** by construction, and
its median is pinned near zero no matter how the market behaves. Measured pooled median here:
**−0.055**, against a construction floor of −0.017. A median of −0.617R is **arithmetically
unreachable** from any symmetric two-sided census.

So the programme's −0.617R must come from a **direction-selected** population — real signals with
a side chosen before the outcome. That is a different object from the one this desk can build
from its tape, and it means **the non-replication is not a clean refutation.** It establishes:

- there is **no unconditional 15:00 penalty** in MES price behaviour on these 91 sessions; and
- whatever rule 5 measured, it was a property of **the programme's signal population**, not of the
  hour. It is a statement about when a particular edge decays, not about when the market is bad.

The directional arms make the same point from the other side:

| arm | 15:00 mean | 15:00 median | rest mean | rest median | z |
|---|---|---|---|---|---|
| long-only | −0.1147 | −0.2442 | +0.0240 | −1.0000 | −1.262 |
| short-only | **+0.1194** | +0.0361 | −0.0262 | −1.0000 | **+1.247** |

Perfect mirror images. The 15:00 hour carried a mild net *downward* drift in this sample, so a
**long-biased** book would see 15:00 as a bad hour and a short-biased one would see it as a good
one. −0.1147R at z −1.26 is in the *direction* of rule 5's claim but is a fifth of its magnitude
and a third of its z, and it does not survive 22 trials. **If the desk's own book is long-biased,
that is the most charitable reading of rule 5 available from this tape — and it is still not a
result.**

### A reading of rule 5 the desk should be aware of

"15:00–16:00 ET" literally spans the 15:00 bar *and* the 16:00 print. Two alternative readings:

| reading | n bars | mean R | SE | median | Welch z | clears `free_t`? |
|---|---|---|---|---|---|---|
| 15:00 bar only (primary) | 72 | +0.0024 | 0.0287 | −0.0191 | +0.104 | no |
| 15:00 + 16:00 combined | 144 | −0.0249 | 0.0158 | −0.0193 | −1.010 | no |
| 16:00 flat bar alone | 72 | **−0.0522** | 0.0127 | −0.0194 | **−2.441** | **no** (needs 2.486) |

The 16:00 cell is **the only cell anywhere on this tape within reach of significance** — and it is
an artefact, which section 4 demonstrates. Under no reading does rule 5 replicate.

---

## 3. Rule 6 — does any single-hour exclusion improve the overall mean?

Baseline all-22-hours mean R = **−0.00097** (n = 1,587 bars).

| excl hr | n kept | mean R kept | delta | z of that hour vs rest | verdict |
|---|---|---|---|---|---|
| 19 | 1515 | +0.00404 | **+0.00501** | −1.256 | not significant |
| 14 | 1516 | +0.00248 | +0.00344 | −1.329 | not significant |
| 05 | 1515 | +0.00214 | +0.00311 | −0.782 | not significant |
| 20 | 1515 | +0.00194 | +0.00291 | −0.742 | not significant |
| 21 | 1515 | +0.00188 | +0.00285 | −0.727 | not significant |
| 22 | 1515 | +0.00021 | +0.00118 | −0.304 | not significant |
| 10 | 1514 | +0.00007 | +0.00104 | −0.265 | not significant |
| 08 | 1515 | +0.00002 | +0.00099 | −0.254 | not significant |
| 06 | 1515 | −0.00003 | +0.00094 | −0.241 | not significant |
| 07 | 1515 | −0.00075 | +0.00022 | −0.056 | not significant |
| 12 | 1514 | −0.00081 | +0.00016 | −0.047 | not significant |
| 15 | 1515 | −0.00113 | −0.00016 | +0.104 | not significant |
| 11 | 1514 | −0.00158 | −0.00061 | +0.167 | not significant |
| 18 | 1515 | −0.00252 | −0.00155 | +0.408 | not significant |
| 23 | 1515 | −0.00176 | −0.00079 | +0.208 | not significant |
| 13 | 1516 | −0.00226 | −0.00129 | +0.481 | not significant |
| 04 | 1515 | −0.00263 | −0.00167 | +0.440 | not significant |
| 02 | 1515 | −0.00320 | −0.00223 | +0.592 | not significant |
| 03 | 1515 | −0.00351 | −0.00254 | +0.678 | not significant |
| 01 | 1515 | −0.00365 | −0.00268 | +0.716 | not significant |
| 00 | 1515 | −0.00464 | −0.00367 | +0.994 | not significant |
| 09 | 1513 | −0.00564 | −0.00467 | +1.256 | not significant |

**11 of 22 single-hour exclusions raise the overall mean.** That is exactly the coin-flip you
expect when no hour carries information: half the hours sit below the mean, and dropping any one
of them raises it *arithmetically*, with no predictive content whatsoever.

The best available filter — drop 19:00 — buys **+0.005R per trade**. At 22 trials it needs
|z| ≥ 2.486 and has **1.256**.

### Multiple-testing: the counts the brief asked for

> **Hours clearing `free_t = sqrt(2·ln 22) = 2.4864`: 0 of 22**
> **Hours clearing naive 1.96: 0 of 22**
> **Gap: 0**

### The gap is zero, and that is the finding

The exercise was designed to show a gap — some hours passing 1.96 and being killed by 2.49. This
tape declined to supply one, and **the zero is more useful than a gap would have been**:

1. **The naive threshold had nothing to manufacture.** Expected false positives at 1.96 across 22
   true nulls is ~1.1. Getting 0 is consistent with the null and slightly on the quiet side.
2. **Rule 6 survives a test it could have failed and didn't.** A correction only matters when
   something clears the weaker bar. Here nothing clears even that. Rule 6 is not being *rescued*
   by the correction — it holds unconditionally on this substrate, which is the stronger outcome.
3. **The lesson survives as a counterfactual and should be stated as one.** Had the sweep been run
   on the flat bar as a 23rd cell without declaring the trial count, hour 16 at z −2.441 would have
   read as a significant hours filter at the naive 1.96 — a "don't trade the last hour" rule,
   supported by a plausible story, and **entirely a transaction cost** (section 4). That is the gap
   the exercise was after: *one* extra undeclared cell was all it would have taken. The correction
   earned its keep against a cell we nearly didn't count.

**Rule 6 verdict: holds.** No hours filter improves expectancy on this tape at any defensible
threshold. And since rule 5 *is* an hours filter that fails here too, the two rules are consistent
on this substrate by the simplest route available — **rule 6 is right and rule 5 is an instance of
what rule 6 rules out.**

---

## 4. The 18:00 hour

### R behaviour — unremarkable

| | n bars | mean R | SE | median | z vs rest | z vs all | btf | tgt% | stp% |
|---|---|---|---|---|---|---|---|---|---|
| 18:00 | 72 | **+0.0316** | 0.0818 | +0.5000 | +0.408 | +0.398 | 22.4 | 34.0 | 65.3 |

**Nothing to see in R.** It is the longest-hold hour on the tape (22.4 bars to the flat) and sits
well inside the pack.

Split by the volume field:

| | n | mean R |
|---|---|---|
| zero-volume 18:00 entries | 57 | **+0.0000** |
| volume-bearing 18:00 entries | 15 | +0.1517 |
| | | Welch z −0.812 |

The exact `+0.0000` is **not a bug**. At this hour essentially no trade exits at session close, so
bar R is quantised to just two values: `+0.5` (one side targets, one stops) and `−1.0` (both stop).
The sample is 38 bars at +0.5 and 19 at −1.0, and `38 × 0.5 − 19 × 1.0 = 0` exactly. An arithmetic
coincidence of a two-valued distribution, verified by value counts in the script.

### Volume — the defect is now pinned to a mechanism

Re-counted on the current 1,685-bar tape (which has grown since the earlier agent's pass):

- **62** zero-volume bars tape-wide; **58** of them in the 18:00 hour = 93.5% of all zero-volume bars
- **58 / 73 = 79.5% of the 18:00 hour** is zero-volume — the earlier agent's 56-of-60 / 79% figure,
  ratio intact
- **58 / 58** of those zero-volume 18:00 bars have **non-zero high–low range**
- the other four zero-volume bars: 2024-10-06 19:00, and 2024-12-17 09:00 / 12:00 / 15:00 (the
  three RTH ones sit inside the known roll merge, per NOTES.md)

**The new observation, and it is decisive:**

| | weekday breakdown |
|---|---|
| zero-volume 18:00 bars | **Mon 15, Tue 14, Wed 14, Thu 15** (= 58) |
| volume-bearing 18:00 bars | **Sun 15** (= 15) |

**Perfectly clean split.** The **Sunday** 18:00 weekly reopen reports volume every time. The
**Mon–Thu** 18:00 reopen — the one that follows the daily 17:00–18:00 maintenance halt — reports
zero, every time. A genuinely dead hour is not dead on exactly four weekdays and alive on the
fifth. **This is a field defect tied to the daily halt boundary**, and the earlier agent's read
("a missing volume field rather than a thin market") is confirmed with a mechanism attached.

### Price behaviour — yes, something is unusual, and it points the same way

The brief asked whether anything about the 18:00 bar's *price* is odd, not just its volume. It is.

ATR-normalised bar range (`range / atr(i−1)`), which removes the volatility regime:

| hour | mean | | hour | mean |
|---|---|---|---|---|
| **18** | **0.706** | | 22 | 0.422 |
| 19 | 0.521 | | 23 | 0.373 |
| 20 | 0.528 | | 00 | 0.355 |
| 21 | 0.443 | | 01 | 0.518 |

| comparison | mean vs mean | Welch z |
|---|---|---|
| 18:00 vs the 19:00–02:00 block | 0.706 vs 0.487 | **+4.303** |
| **zero-volume 18:00 bars only** vs that block | 0.657 vs 0.487 | **+2.954** |
| Sunday volume-bearing 18:00 bars | 0.893 | — |

**The bar that reports no volume is systematically wider than all eight volume-bearing hours that
follow it.** In raw points: 18:00 zero-volume bars average an 8.97-point range with a 3.69-point
body, against 7.41 / 3.69 for the 19:00 bars that report real volume. A truly untraded hour cannot
be the widest bar of the overnight block. **The price field says the market was open and moving
while the volume field says nothing traded — the two fields contradict each other, and the price
field is the credible one.**

A supporting structural hint: the 18:00 bar engulfs the whole of the following 19:00 bar's range
**25 / 73** times (34%), against a control rate of **14 / 74** (19%) for 19:00 engulfing 20:00. The
18:00 bar behaves like a bar covering a longer interval than one hour.

**Hypothesis, offered as a hypothesis:** the 18:00 print may be carrying price action from the
17:00–18:00 halt window (or from the session boundary more broadly) into a single bar, which would
explain both the excess width and a volume field that fails to populate across that boundary.
**This is not proven here** — confirming it needs the source series, which this lane must not read.
It is recorded so whoever does hold that lane can check it.

### Consequences the desk should weigh

1. **Do not use 18:00 volume in any filter, threshold or regime classifier.** 79.5% of the hour is a
   structural zero on Mon–Thu, and any volume-conditioned rule will silently key on *weekday*
   instead. This is a live hazard: it is the first bar of the owner's own cycle.
2. **The 18:00 hour's R is not compromised**, because R is computed from OHLC only. z +0.41, safe
   to leave in the population.
3. **The Sunday/weekday split contaminates the hour in a second way.** 18:00 entries are 57 Mon–Thu
   observations plus 15 Sunday-night ones that hold through an entire Monday session. Mean R
   +0.0000 vs +0.1517 across that split (z −0.812, not significant) — worth knowing before anyone
   reads the 18:00 cell as one homogeneous thing.

### Why the 16:00 flat-bar cell is an artefact, not a discovery

Flagged here because it is the tape's only near-significant cell and would otherwise get
mis-reported.

| | value |
|---|---|
| n bars / trades | 72 / 144 |
| mean R | −0.05215 |
| Welch z vs the 22-hour grid | **−2.441** (needs `free_t` 2.486 at 22, 2.504 at 23 — clears neither) |
| **long-only mean** | **−0.05187** |
| **short-only mean** | **−0.05243** |
| exits | SESSION_CLOSE 136, STOP 8 |

**Long and short lose the same amount to four decimal places.** A real bad-window is directional;
a symmetric loss on both sides is a *cost*. Mechanics alone predict
`(136 × −0.01957 + 8 × −1.0) / 144 = −0.07404` — one tick of slippage on a one-bar hold, plus eight
stop-outs. Observed: −0.05215. **Fully accounted for by the fill convention.** No market claim
survives, and it is properly excluded from the grid as the flat bar.

---

## Summary for the desk

1. **Rule 5 does not replicate on R1's tape.** z **+0.10** vs a reported −4.43 (wrong sign); median
   **−0.019R** vs a reported −0.617R. It fails under all three readings of its window.
2. **The non-replication is bounded, not total.** The reported median −0.617R is arithmetically
   unreachable from a two-sided census, so rule 5 must have been measured on a direction-selected
   population. What this tape refutes is an *unconditional* 15:00 penalty in MES price behaviour.
   Rule 5 may still be true **of the programme's signals** — but it is then a statement about when
   an edge decays, not about when the market is bad, and **the desk should stop citing it as the
   latter.** The long-only arm (−0.1147R, z −1.26) is the most charitable reading available and is
   still not a result.
3. **Rule 6 holds.** No single-hour exclusion improves expectancy at any defensible threshold. 11
   of 22 exclusions raise the mean, which is the coin-flip the null predicts. Best filter: +0.005R
   at z −1.26.
4. **0 of 22 hours clear `free_t` 2.4864; 0 of 22 clear naive 1.96; gap 0.** Largest |z| in the
   sweep is 1.329. The correction earned its keep anyway: an undeclared 23rd cell (the 16:00 flat
   bar, z −2.441) would have read as a significant "don't trade the last hour" filter at 1.96 and
   is **entirely one tick of slippage**.
5. **The two rules are not in tension on this substrate** — but not via the "specific bad window
   inside a general null" story the desk expected. There is no bad window. **Rule 6 is right, and
   rule 5 is an instance of exactly what rule 6 rules out.**
6. **18:00: R is fine (+0.0316, z +0.41); the bar is not.** The zero-volume defect splits perfectly
   by weekday — Mon–Thu zero (58/58), Sunday always populated (15/15) — pinning it to the daily
   17:00–18:00 halt boundary. And the *price* field contradicts the volume field: the 18:00 bar is
   **wider** than every volume-bearing hour after it (ATR-normalised z **+4.30** overall, **+2.95**
   for the zero-volume subset alone). **Never condition on 18:00 volume**; on Mon–Thu it is a
   constant.

**Trial count declared: 22 hour cells, `free_t` = 2.4864.** Rule 5 and 18:00 are two of those 22.
Counting every robustness view as a separate search gives ~66 and `free_t` 2.89; nothing on this
tape reaches either. **n = 91 ET sessions of one symbol — this refutes rule 5 *here*, it does not
overturn a programme-wide measurement, and `BRIEF.md` precedence is unaffected.** Not committed.
