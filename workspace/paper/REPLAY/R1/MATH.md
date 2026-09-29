# R1 — the mathematical record

**Every figure here was re-derived from `visible.jsonl` on 2026-09-29 at cursor 7350/11316**, not quoted from
the journal. `NOTES.md` is the narrative and wins on history; this page is the arithmetic.
**PAPER — UNVALIDATED. Nothing below is an edge.**

Contract: MES 60-minute. Tick `δ = 0.25` pt, point value `V = $5.00`, round-turn commission `C = $2.69`.
Engine: fill at next bar's open ± one tick; **stop wins a same-bar stop/target tie**; flat at session close.

---

## 1. Definitions

True range and its average:

```
TR_i = max( H_i − L_i , |H_i − C_{i−1}| , |L_i − C_{i−1}| )
ATR_i(n) = (1/n) Σ_{j=i−n+1}^{i}  TR_j          n = 14, floored at 0.5
```

A trade entered at bar `f` with stop multiple `k` and reward ratio `ρ`, using **only** `ATR_{f−1}` (known at
the decision bar):

```
S = k · ATR_{f−1}                       stop distance, points
fill = O_f + σδ ,  σ = +1 long, −1 short
stop = fill − σS ,  target = fill + σρS
R = (exit − fill)·σ / S                 outcome in units of risk
```

Session end is **the bar before the next 18:00 ET bar**, not the first bar whose hour is 16 — 67 of 355 ET
dates have no 16:00 bar and four are half-days trading 09:30–12:30.

---

## 2. The cost identity — the one result everything else runs into

Commission is fixed in dollars; risk scales with volatility. So the hurdle **in R** is inversely
proportional to ATR. Expressing one round turn plus one tick of entry as points:

```
φ = C/V + δ = 2.69/5.00 + 0.25 = 0.788 points          (the friction constant)

hurdle(k, ATR) = φ / (k · ATR)          in R
```

Measured over 7,330 bars with `k = 1.0`:

| ATR14 | value | hurdle |
|---|---|---|
| min | 3.38 | **0.2335 R** |
| q1 | 9.14 | 0.0862 R |
| median | 12.62 | **0.0624 R** |
| q3 | 18.93 | 0.0416 R |
| **max** | **111.25** (bar 2897, 2025-04-09) | **0.0071 R** |

**A 33× spread in the cost of trading the same instrument.** At `k = 0.5` every figure doubles.

---

## 3. Return moments — why the standard threshold fails here

```
n = 7,349 log returns      mean = +2.293e−05      sd = 0.00243
skew = +1.839              kurtosis = 96.50       (normal = 3)
max |log return| = 0.0651
```

**Kurtosis 96.5, not the 24.11 on earlier record.** Reconciled: 24.11 was correct when computed at ~2,000
bars. The tape's kurtosis quadrupled when April 2025 arrived — 23.45 (first 2,000 bars) → **88.71** (first
3,000) → 96.50 (7,350). **Excluding all merge bars raises it to 119.03**, so the fat tails are a real market
event (the April 2025 crash), not a data defect.

Lo–MacKinlay variance ratio, `VR(q) = Var[Σ_q r] / (q · Var[r])`, which is 1 under a random walk:

```
VR(2)=0.960   VR(4)=0.966   VR(8)=0.992   VR(16)=1.029   VR(24)=0.969
```

**All within 4% of unity.** Returns carry no exploitable serial structure at these horizons. Volatility is
forecastable; direction is not.

Drift: `+0.1449 pts/bar`, `+1,065.0 pts` over the tape — material, and the reason every directional arm is
measured against a **matched** control rather than zero.

---

## 4. The multiple-testing bar — corrected

The desk used `free_t(n) = √(2 ln n)`, the expected maximum of `n` **independent** standard normals. Two
forces break it here, in opposite directions:

- cells of a grid search over one price series **overlap**, cutting effective trials → true bar **lower**;
- the outcome distribution is **heavy-tailed (κ = 96.5)** → the maximum of a t-family runs **higher**.

Empirical family-wise null, built by **circular-shifting the outcome series with features held fixed** (a
shift, not a permutation — permuting would destroy the serial dependence that creates the tails):

| grid | cells | `free_t` | null median max\|t\| | null 95th | real best |
|---|---|---|---|---|---|
| always-LONG, k=1.0 | 341 | **3.415** | **4.352** | **6.104** | 3.823 → p = **0.695** |
| full predicate search | 61,272 | **4.695** | **5.164** | **7.561** | 7.652 → p = 0.055 |

**`free_t` sits below the null's median on both grids** — a grid with no content clears it more than half the
time. On this tape it is **too lenient by 61–79%**.

Control: on i.i.d. Gaussian outcomes with overlapping cells the null 95th is **2.065 against `free_t`
2.716** — *below*. So this is **a property of this tape, not a law about `free_t`**. Implemented in
`shiftnull.py`; `free_t` retained as a floor that is explicitly not sufficient.

---

## 5. Walk-forward result and the placebo

```
trades closed  2        equity $50,000 → $50,688.86  (+1.38%)   peak = current, drawdown $0
REAL      n=2   mean +1.8744 R   sd 0.0289   t +91.660   win 100%
PLACEBO   n=2   mean +0.8935 R   sd 1.3584   t +0.930    win  50%
real − placebo = +0.9810 R      Welch z = +1.021        free_t(22) = 2.486  → does NOT clear
```

**`t = +91.660` is a degenerate statistic, not a strong one:** two trades closed 0.041 R apart, so `sd =
0.0289` is the denominator doing the work. With `n = 2` the real arm has one degree of freedom. **The
placebo separation is one measurement (n=2 vs n=2), unchanged since bar ~1400** — re-printing it at each
1,000-bar milestone adds nothing.

---

## 6. The no-position counterfactual — 58 stand-downs priced against three controls

For every bar declined, simulate the trade **not** taken in both directions at `k=1.0, ρ=2.0`, against
controls at all eligible bars. Direction must be fixed **without** hindsight:

| arm | sample | all-bar gap / z | ATR-matched gap / z | paired local ±120 / z |
|---|---|---|---|---|
| always LONG | +0.348 R | +0.381 / **+2.03** | +0.385 / **+2.05** | +0.300 / +1.61 |
| always SHORT | −0.112 R | −0.056 / −0.33 | — | −0.016 / −0.10 |
| coin flip (bar parity) | +0.315 R | +0.364 / +1.92 | — | +0.345 / +1.82 |

All-bar controls (n = 7,293): LONG −0.033 R, SHORT −0.056 R, flip −0.049 R.

**The `best of both directions` arm is an artefact and is never quoted**: picking the side after seeing the
outcome reaches 1.5 R at **>54% of all bars in the tape**.

**The long arm's history across n = 51…57:** `+2.09, +2.01, +1.92, +1.84, +2.06, +1.94, +2.03` — while the
paired-local control ran `+1.77, +1.65, +1.52, +1.43, +1.59, +1.49, +1.61` and **never once crossed**. A
statistic that crosses a threshold in both directions on single observations is **a null at a cut point**.
Against the corrected bar (§4) it is not close.

Composition of the declined sample, both real and both measured: mean ATR **13.18 vs 18.26** tape-wide (38th
percentile), and local drift **+0.2935 vs +0.1272 pts/bar**. ATR-matching moved the gap by **0.004 R**; the
window match removed about a quarter.

A drift-removed arm was built, produced the largest z in the register (+2.08), and was **withdrawn**:
`corr(prior-120-bar drift, next-24-bar realised drift) = −0.0928`, `R² = 0.86%`, wrong sign. It subtracts
noise of sd 1.22 pts/bar from a forward drift of sd 3.12. **Kept in code labelled INVALID.**

---

## 7. Volatility does not convert — the hope that was closed

Bucketing all **6,020** eligible bars by ATR quartile, `k=1.0, ρ=2.0`:

| bucket | mean ATR | hurdle | `\|C−O\|/range` | LONG | SHORT | coin flip | ≥1.5R either dir |
|---|---|---|---|---|---|---|---|
| Q1 | 7.15 | 0.1102 R | 0.439 | −0.113 | −0.053 | −0.092 | **57.9%** |
| Q2 | 10.62 | 0.0742 R | 0.436 | −0.076 | −0.047 | −0.043 | 52.3% |
| Q3 | 15.21 | 0.0518 R | 0.448 | **+0.045** | −0.044 | −0.028 | 53.1% |
| Q4 | 31.28 | 0.0252 R | 0.436 | **+0.004** | −0.064 | −0.029 | **49.4%** |

**Friction falls 4.4×. Directional efficiency `E[|C−O|/(H−L)]` is flat at 0.436–0.448 in every quartile** —
volatility buys range and no extra direction. Target reachability **falls** as ATR rises. Gross is positive
in two cells (Q3, Q4 long, non-monotone → noise); **every cell is negative net of friction.** Net coin flip:
**−0.202 R in Q1, −0.054 R in Q4** — less bad, never positive.

Independent replication on ~6,500 bars across 48 side × geometry × vol-base arms: **all 48 negative net**,
gross positive in 2 (+0.0004, +0.0034 R), both erased by `C`.

---

## 8. Key levels bounce at the rate a random line does

Detected levels = clustered confirmed fractal pivots, distinct touches separated by >2K bars. Control:
**count-matched, touch-matched (resampled from the real touch distribution, 58.0% of which is 1-touch), and
decontaminated** — any control line within 0.25 ATR of a real level is redrawn, verified 0.0% residual.

| population | real | fair control | diff | z |
|---|---|---|---|---|
| 1-touch fresh extreme | **50.1%** (n=477) | 54.5% (n=433) | −4.4% | −1.33 |
| retested, 2+ touches | **55.5%** (n=402) | 55.2% (n=337) | **+0.3%** | **+0.08** |
| bounce trade arm | +0.018 R (n=879) | **+0.076 R** | −0.058 | — |
| break trade arm | +0.015 R (n=879) | **+0.045 R** | −0.030 | — |

**Both trade arms pay better on random price lines.** The published "45.7% at n=162" failed twice: the full
1-touch population is n=477 at 50.1% (the n=162 was a third of it, selected by a `touches < 2` filter
interaction), and the old control **contained no 1-touch line at all** while testing in a 31% louder tape
(ATR 23.80 vs 18.34). `scenario.py`'s odds are withdrawn permanently; its four branches (HOLDS / FAILS /
NEITHER / GAPPED THROUGH) stay, carrying no probabilities.

---

## 9. Data defect: the quarterly contract merge

Five rolls, each the roll week: **128 bars of 7,350 = 1.74%**, or **2.69%** including ATR tails. *(The "~5%"
this desk claimed for ten bursts was an extrapolation from the single 75-bar March case and is retracted.
1.74% is a lower bound — the envelope test under-bounds every merge it catches.)*

| roll | bars | ATR14 on the next bar | clean ATR | inflation |
|---|---|---|---|---|
| Dec-24 | 13 | 79.36 | 6.34 | **+1151.8%** |
| Mar-25 | 75 | 63.30 | 12.41 | +410.1% |
| Jun-25 | 4 | 25.73 | 17.30 | +48.7% |
| Sep-25 | 3 | 17.70 | 5.86 | +202.1% |
| Dec-25 | 33 | 72.00 | 14.27 | +404.6% |

**Contamination lasts the full 13–14 bars of the ATR window every time**, so the **do-not-trade zone is the
merge plus 14 bars** — an ATR-sized stop set there takes both its distance and its R denominator from
synthetic range.

Three orthogonal detectors, each blind where another sees:
1. **envelope constancy** — `k≥4` consecutive bars, high- and low-band each `≤0.30·` mean range, mean range
   `≥3×` prior median, and a boundary jump `≥0.50·` mean range. Under-bounds every merge (4 of 33 in Dec-25).
2. **gap clustering** — recurring same-magnitude `|O_i − C_{i−1}|`; drift-immune. Delimits best.
3. **range/volume dissociation** — range `≥4×` local median while volume `<1.5×` median. *Physical argument:
   a real 60-point hour prints huge volume (bar 5449 = 75.75 pts on 350,024 contracts); a merged bar is wide
   because it spans two instruments, so its width carries no trade.*

**The one pre-registered test this desk has run: predicted at bar 5650 that the December 2025 roll would
merge near bar 6829, window 6700–6950. Actual: bars 6864–6896.** All three detectors fired; the range/volume
screen, previously untested out of sample, flagged 19 bars inside it. Its honest out-of-sample record is
**19 true + 1 false positive** over ~1,700 bars — the false one a thin MLK-holiday reopen bar (61 pts on
1,126 contracts), which is a merge-detection miss but a correct *do-not-trade* flag.

**Open pre-registration:** March 2026 roll near **bar 8297, window 8150–8450**.

---

## 10. The one usable result — a specification rule, not an edge

`ATR14` is an average-hour statistic and the hours are not average:

```
E[ TR_h / ATR14 ]:   09:00 = 2.62   10:00 = 2.52   11:00 = 1.83   08:00 = 1.81
                     ...   22:00 = 0.44   00:00 = 0.43   23:00 = 0.41
                     spread = 6.4x across the clock
```

A `0.5·ATR` stop taken into the 09:00–10:00 ET bars is roughly **a fifth of the excursion it will face**; the
same stop overnight is several times what it needs. The largest measured effect anywhere on this tape is **a
mis-sized stop, not a direction** — long and short lose *equally* in the worst cells, the signature of
geometry rather than signal.

**Rule: size stops to the volatility of the hours you will hold through.** Costs nothing, requires no edge.

*(A related claim of 2.93× at 08:00 could not be reproduced — measured 1.81× there, peak 2.62× at 09:00.
Recorded as unreproduced, not adopted.)*

---

## 11. What a grid finds that an account cannot have

The decisive test on the best directional family found in 61,272 cells — **one position at a time, first
signal per session, costs charged**:

```
in-sample      win 46.2%   payoff 1.48   +0.148 R
out-of-sample  win 33.3%   payoff 1.52   −0.160 R
full tape      233 trades  +0.029 R      t = +0.34
```

The grid takes **8.6 bites per session; an account gets one.** It also failed a gradient test (only the
±2 ATR tails pay, and the bucket straddling the fitted cut runs the wrong way) and an anchor test (prior
close and a 20-close mean pay the same, so 123 "surviving" cells are **~1 hypothesis**).

---

## 12. Bottom line

```
largest |z| anywhere in this record  = +4.30   → and it belongs to a BROKEN VOLUME FIELD
best honest counterfactual arm       = +2.05   → against a corrected bar of ~6.1
best cell of a 61,272-cell search    = +7.652  → family-wise p = 0.055
best cell of a 341-cell search       = +3.823  → family-wise p = 0.695
```

**Nothing here clears its own threshold, and the threshold was too low.** The supported sentence is *"any
structure at MES 60m is smaller than the cost of trading it"* — a statement about `φ / (k·ATR)`, not about
the absence of structure, which `n = 2` cannot test.

**Unresolved and recorded as such:** the desk-wide search width (310) rests on a figure (105 trials) whose
generating code was never shipped, so the deflated bar was computed from an unreproducible number *and* with
a formula too lenient for the job — and still nothing cleared it. Thesis 5's retirement is **not
contradicted, but unsupported by anything reproducible.**
