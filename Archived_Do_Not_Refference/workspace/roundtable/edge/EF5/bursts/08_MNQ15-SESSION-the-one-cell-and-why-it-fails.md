# EF5 burst 08 — MNQ 15m SESSION: the one arm-cell of twelve where reals beat placebos, and why it still fails

EF1 has parked its harness as **trustworthy for the invariant** (0 violations on three instruments,
against **78** on a control run through the shipped engine — so the check has power rather than being
vacuously green). The `PROVISIONAL: EF1 unvalidated` label is therefore lifted **for the window rule**.
EF1's own qualification applies to me: trustworthy for the invariant, *not yet for a profitability
number*, and the remaining gate is mine — placebos, a stated search width and threshold, a forward
test, and the firing-rate check. **I have all four**, so the numbers below are reportable, with every
caveat attached.

`[measured: EF5/code/measure.py, stress_mnq15_session.py, stress2_clean_holdout.py,
stress3_regime_and_kind.py → EF5/out/PROVISIONAL_measure_all.json,
PROVISIONAL_stress{,2,3}_MNQ15_SESSION.json]`

## 1. Twelve arm-cells, and which of them a real row tops

Search: **12 arm-cells**, declared population **21,060**, `free_t(12) = 2.229`, `free_t(21,060) = 4.462`.
Gates: n ≥ 20, t ≥ 0, max consecutive losses ≤ 12. Score = `expectancy_r_net · n/(n+40)`.

| arm-cell | floored reals | floored placebos | placebo share | rank 1 is | best placebo rank | null E[best] | paired: reals above own placebo | sign z | Wilcoxon z |
|---|---|---|---|---|---|---|---|---|---|
| MES 5m RTH | 13 | 8 | 0.38 | **placebo** | 1 | 2.44 | 2/6 | −0.82 | −1.15 |
| MES 5m SESSION | 15 | 5 | 0.25 | real | 2 | 3.50 | 2/4 | 0.00 | −0.37 |
| MES 15m RTH | 8 | 7 | 0.47 | real | **3** | 2.00 | 3/6 | 0.00 | +0.52 |
| MES 15m SESSION | 17 | 5 | 0.23 | real | 2 | 3.83 | 3/4 | +1.00 | +1.46 |
| MES 30m RTH | 7 | 3 | 0.30 | real | 2 | 2.75 | 1/3 | −0.58 | −1.07 |
| MES 30m SESSION | 30 | 13 | 0.30 | **placebo** | 1 | 3.14 | 8/11 | +1.51 | +1.60 |
| MNQ 5m RTH | 21 | 22 | 0.51 | **placebo** | 1 | 1.91 | 6/17 | −1.21 | −1.25 |
| MNQ 5m SESSION | 59 | 50 | 0.46 | **placebo** | 1 | 2.16 | 16/41 | **−1.41** | −0.84 |
| MNQ 15m RTH | 3 | 4 | 0.57 | **placebo** | 1 | 1.60 | 1/3 | −0.58 | −0.54 |
| **MNQ 15m SESSION** | **47** | **40** | **0.46** | **real** | **7** | **2.15** | **25/31** | **+3.41** | **+2.82** |
| MNQ 30m RTH | 2 | 3 | 0.60 | **placebo** | 1 | 1.50 | 1/2 | 0.00 | −0.45 |
| MNQ 30m SESSION | 22 | 19 | 0.46 | **placebo** | 1 | 2.10 | 6/13 | −0.28 | −0.80 |

**Answer to the question my dispatch asked.** A real row ranks 1st in **5 of 12 arm-cells**
(MES 5m SESSION, MES 15m RTH, MES 15m SESSION, MES 30m RTH, MNQ 15m SESSION). But ranking 1st means
nothing at these placebo shares — the null puts the best placebo at rank 1.5–3.8. Only **one** cell has
a best-placebo rank clearly above its null *and* a positive paired test: **MNQ 15m SESSION**
(best placebo 7th against a null of 2.15; 25 of 31 reals above their own placebo). Everywhere else the
paired test is null or negative, and **MNQ 5m SESSION is negative at −1.41 with 41 pairs — the most
powered cell in the whole deliverable points the wrong way.**

Note the four seven-row-or-fewer cells (MES 30m RTH 7, MNQ 15m RTH 3, MNQ 30m RTH 2, MES 15m RTH 8)
after gating: **a top 10 is not available in them at all.** This reproduces EF6's warning that on
MNQ 15m the ranking window holds 4.5–7.8 qualifiers — I measure 3 in the RTH arm. The SESSION arm is
where a universe exists.

## 2. MNQ 15m SESSION, stressed four ways. It survives two and fails two.

The cautionary example in my dispatch — MNQ 60m `rth_only=True`, the single favourable cell of 20 —
failed on its holdout and its disjoint thirds. Same tests, same cell shape, different symbol/timeframe.

### Survives: a leak-free chronological holdout

**First, a defect in my own first attempt, found by reading its own output.** My initial holdout gated
the cohort on `t ≥ 0` measured over the **full** span and then read expectancy on the last 40% of that
same span — the gate used out-of-sample information. That OOS sign z of 6.19 is **not a clean holdout
and is retracted.** Rebuilt with selection touching only the in-sample cycles
(`stress2_clean_holdout.py`):

```
selection: in-sample cycles only (24 of 41), floor 12 trades in-sample, t >= 0 in-sample
           -> 31 rows selected from 254 clone-collapsed candidates

IN  SAMPLE (24 cycles) : 29/31 reals above own placebo, real +0.1657R, placebo -0.0519R,
                         diff +0.2176R, sign z = +4.85
OUT OF SAMPLE (17 cyc) : 24/31 reals above own placebo, real +0.2452R, placebo -0.0141R,
                         diff +0.2593R, sign z = +3.05     <- no selection leak
```

The effect does not decay out of sample. That is the opposite of the cautionary example, whose 60/40
holdout came in *below* base rate.

### Survives: it is not purely directional drift

MNQ rose **+12.186%** over the 41 cycles (IS +5.829%, OOS +6.111%), so a long-biased rule earns from
drift alone. The discriminating control is **`placebo_shuffle`**, which keeps the real entry bars *and*
the exact long/short count and permutes only which bar gets which direction — so it holds the
directional exposure fixed and destroys only the pairing of direction to bar. Drift cannot survive
that.

```
vs placebo_random  (timing AND direction destroyed) : 29/31, diff +0.2875R, sign z = +4.85
vs placebo_shuffle (direction-to-bar pairing only)  : 27/31, diff +0.2170R, sign z = +4.13
LONG  trades only : 26/30, real +0.2604R vs placebo -0.0215R, sign z = +4.02
SHORT trades only : 24/26, real +0.1158R vs placebo -0.0903R, sign z = +4.32
```

Both legs beat their controls, and shorts beat theirs *in a rising tape*. Placebo id collisions:
**0** (`diag['id_collisions'] = 0`, asserted, not trusted — the coordinator's point 4: `_id=None` is not
the guard because `strategy_id` hashes condition *names*, and EF4 measured 400–540 collisions per cell
in its own construction).

### **Fails: the effect is absent in the one third where the tape fell**

| contiguous third | cycles | MNQ drift | paired sign z (all) | vs random | vs shuffle | LONG | SHORT |
|---|---|---|---|---|---|---|---|
| 0 | 14 | **+9.248%** | +4.38 | +4.27 | +3.29 | +3.40 | +2.36 |
| **1** | 13 | **−1.690%** | **+0.19** | **−0.93** | +0.56 | **−0.39** | +1.00 |
| 2 | 14 | +3.863% | +2.69 | +3.41 | +2.34 | +3.65 | +2.04 |

**The two up-tape thirds carry the entire effect and the one down-tape third has none of it**
(vs-random actually goes negative). In interleaved thirds a placebo lands 1st, 1st and 5th. The
shuffle control says the effect is not *only* the long/short mix — but the third-by-third split says it
only appears when the tape is rising, which is the same conclusion arrived at from the other side:
**41 consecutive sessions in one direction is one regime observation, not three.**

### **Fails: deflated for effective sample size it does not clear the 12-cell threshold**

The sign test treats 31 paired rows as 31 independent observations. They share bars, conditions and
trades. Mean pairwise Jaccard of realised trade ledgers = **0.0874**, giving
`n_eff = 31 / (1 + 30·0.0874) = 8.56`:

```
sign z vs placebo_shuffle, raw                      +4.131
sign z deflated by effective n (8.56 of 31)         +2.170
free_t for the 12 arm-cells searched                 2.229   -> DOES NOT CLEAR
free_t for the declared population of 21,060         4.462   -> not close
```

It fails, and it fails at the *most generous* denominator available — a search width of 12, which
ignores the 21,060 rule sets, the gate choices, the score definition and the frame choices.

### And it reproduces the programme's central negative inside itself

Select the top 10 on the in-sample cycles, read it on the out-of-sample cycles, against the whole
qualifying universe read on the same cycles:

```
selected in-sample top 10, read out of sample   +0.2202 R
whole qualifying universe, same cycles          +0.2980 R     <- selecting is WORSE
placebo cohort, same cycles                     +0.0113 R
```

**Selecting is worse than not selecting**, in my own cell, on my own data. The reals do beat the
placebos (+0.298R vs +0.011R universe-wide) — but *ranking* them and taking the top 10 destroys
0.078R of that. This is `RANKING_FINDINGS`' headline reproduced on an unmeasured regime at a new
timeframe, and it is the strongest single argument against handing over a ranked list at all.

## 3. Verdict on MNQ 15m SESSION

**Not live-eligible. Not a lead.** It is a genuine, cleanly-measured, *regime-conditional* effect on 41
sessions of a rising tape, carried by ~8.6 effectively independent rule sets, that fails its own
multiple-testing threshold at the most generous denominator and whose own top-10 selection
underperforms its own universe.

The honest deliverable for this cell is **the qualifying count and the universe's expectancy, not a
ranked list** — exactly as the coordinator predicted before I measured it.

And the treatment my dispatch prescribed for the MNQ 60m cautionary example applies here verbatim: this
is what a promising cell looks like. The difference is that I looked for the three ways it could be
noise before describing it, and found two of them.
