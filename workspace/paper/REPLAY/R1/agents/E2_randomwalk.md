# Agent E2 — is MES 60m a random walk at this timeframe?

Scope: `visible.jsonl` only — 1,685 hourly MES bars, 2024-10-06 19:00 ET → 2025-01-23 23:00 ET,
giving **n = 1,684 log returns of closes**. Nothing outside R1's lane was read; the harness was
not run and no cursor was advanced. Script: `agents/E2_randomwalk.py` (reads `../visible.jsonl`,
writes nothing). Every number below is reproducible from it at seed 1685.

**Scope caveat, stated once and meant throughout:** 1,685 of 11,287 bars is **14.9%** of the
series. Everything here is a statement about this window — Oct 2024 to Jan 2025, a 13.3%-vol
uptrend — not about MES 60m for all time. The desk has 9,602 bars ahead of it.

---

## Lead findings

1. **The answer is yes: this window is statistically indistinguishable from a random walk in
   its returns.** All five variance ratios sit within 4% of 1.0 with robust |z| ≤ 0.33
   (p ≥ 0.745); the runs test gives z = −0.345 (p = 0.730); all three Hurst estimates land on
   their own null medians (p = 0.45–0.95). **This one fact explains every null the desk has
   recorded** — the stand-down counterfactual, the S/R levels, the thesis-5 mechanisation. They
   were not badly designed. They were looking for directional structure in a series that has
   none at 60 minutes.

2. **THE NAIVE TEST SAYS THE OPPOSITE, AND THE NAIVE TEST IS WRONG.** Read with the textbook
   ±1.96/√n band, this series shows **7 of 24 significant autocorrelation lags and a Ljung-Box
   Q(24) = 78.3 at p = 1.1 × 10⁻⁷** — a screaming rejection of the random walk. Both are
   artifacts of assuming homoskedasticity on a series with **excess kurtosis 21.1**. Under the
   heteroskedasticity-robust band the count drops to **1 of 24**, and under a sign-flip
   bootstrap the Ljung-Box p goes to **0.26**. A series built to have *exactly zero* return
   predictability produces **5.06 naive-"significant" lags on average** and Q(24) = 63. Anyone
   on this desk who runs a standard ACF on this tape will "find" structure that is not there.

3. **My synthetic control looks MORE structured than the real market.** The single seeded
   Gaussian random walk — a series I generated, guaranteed to have no memory — returned
   **VR(8) = 0.822 with robust z = −2.50** and a **runs z = +2.03**: two findings at p < 0.05
   announcing mean reversion that does not exist. The real tape returned |z| ≤ 0.33 everywhere.
   **This is the whole point of the exercise.** At n ≈ 1,685, a clean random walk throws off
   p < 0.05 "discoveries" routinely.

4. **Two data defects in this tape manufacture apparent structure, and one of them is already
   on the desk's books.** Seven of the twelve largest returns in the entire sample sit inside
   **bars 1146–1158 — agent C's contract-roll merge** — alternating ±1.1–1.3% (+1.30, −1.26,
   +1.15, −1.24, +1.14, −1.08, +1.17). That splice single-handedly creates the ρ₃ = +0.076 and
   ρ₆ = +0.095 that the naive band flags. Excise it and both collapse to −0.034 and +0.013.
   **The roll merge is not just a fill hazard; it is a source of fake autocorrelation.**

5. **The one number that survives to p < 0.10 is an artifact of a single afternoon.** With the
   merge excised, ρ₁ rises to +0.131 and VR(2) to 1.133 (z = +1.78, p = 0.076) — the largest
   hint in the study. **48% of that ρ₁ comes from one pair of bars: 1166–1167, the 18 Dec 2024
   FOMC selloff (−1.52% then −1.72%).** Winsorize at 3σ and it falls to +0.065; Spearman gives
   +0.038 (p = 0.12); consecutive-sign agreement is 0.508 ± 0.025. It is one macro event, not a
   tradeable pattern.

6. **Volatility is strongly predictable and gives you nothing directional.** |rₜ| on |rₜ₋₁|
   has slope +0.334, **R² = 0.112, p = 3 × 10⁻⁴⁵** — about 32× the R² of any return-predicting
   regression here, and unlike those it survives every robustness check. It tells you how big
   the next bar will be, never which way. **It sizes positions and sets stops. It cannot
   rescue a directional strategy.**

---

## 0. The window

| | |
|---|---|
| bars / returns | 1,685 / **1,684** |
| span | 2024-10-06 19:00 ET → 2025-01-23 23:00 ET |
| mean return | +0.0000343 (+0.00343%/bar) |
| sd | 0.001752 (**0.1752%/bar**, ≈13.3% annualised at 23×252) |
| total drift | +5.77% (5802.25 → 6146.75) |
| skew / excess kurtosis | −0.601 / **+21.115** |
| exact-zero returns | 45 |
| mean \|move\| | 5.94 points |

The tape runs 23 bars/day, not 24 — there is no 17:00 ET bar. ~73 returns therefore span the
2-hour maintenance break; §6 reports the battery with them dropped.

**The kurtosis of 21 is the single most consequential number in this table.** It is why the
homoskedastic versions of every test below are untrustworthy, and why I report a robust variant
of each.

---

## 1. Autocorrelation, lags 1–24

`δⱼ` is the Lo–MacKinlay heteroskedasticity correction: the sampling variance of ρⱼ is inflated
by δⱼ, which is 1.0 under iid and larger when big moves cluster. The honest band is
1.96·√(δⱼ/n), not 1.96/√n.

| lag | ρ(r) | naive | robust band | robust | δⱼ | ρ(\|r\|) |
|----:|-----:|:--:|----:|:--:|----:|-----:|
| 1 | +0.0236 | | ±0.1494 | | 9.79 | **+0.3342** |
| 2 | −0.0393 | | ±0.0895 | | 3.51 | **+0.1998** |
| 3 | +0.0762 | ✱ | ±0.1168 | | 5.98 | **+0.2408** |
| 4 | −0.0885 | ✱ | ±0.0914 | | 3.66 | +0.1612 |
| 5 | −0.0551 | ✱ | ±0.0907 | | 3.60 | +0.1230 |
| 6 | **+0.0954** | ✱ | ±0.1039 | | 4.73 | +0.1624 |
| 7 | −0.0431 | | ±0.0707 | | 2.19 | +0.0412 |
| 8 | −0.0165 | | ±0.0715 | | 2.24 | +0.0183 |
| 9 | +0.0681 | ✱ | ±0.0653 | **✱** | 1.87 | −0.0018 |
| 10–20 | all \|ρ\| < 0.025 | | | | 0.4–1.5 | −0.06 → +0.10 |
| 21 | −0.0611 | ✱ | ±0.0881 | | 3.40 | +0.1569 |
| 22 | −0.0261 | | ±0.1175 | | 6.05 | **+0.2177** |
| 23 | +0.0616 | ✱ | ±0.0957 | | 4.02 | +0.1790 |
| 24 | −0.0410 | | ±0.0860 | | 3.24 | +0.1519 |

- **Naive band: 7 of 24 outside.** Expected under iid: 1.2.
- **Robust band: 1 of 24 outside** — lag 9, ρ = +0.0681 against ±0.0653, marginal, with no
  mechanism and no survival in the merge-excised series beyond the same marginal status.
  **1 of 24 is exactly chance.**
- Mean δⱼ = **2.75**, so the naive band is too narrow by a factor of **1.66** on average, and
  by **3.1× at lag 1** (δ₁ = 9.79).
- max|ρ| over 24 lags = 0.0954. Sign-flip null 95th percentile = **0.150**, empirical **p = 0.48**.

**Ljung-Box Q(24) = 78.32.** Against χ²₂₄ that is p = 1.1 × 10⁻⁷ and the random walk is dead.
Against the sign-flip null — which holds every |rₜ| in place and randomises only direction, so
it has zero return predictability by construction but the real volatility path — the null median
is **62.8**, the 95th percentile is **112.5**, and the observed 78.3 gives **p = 0.263**.

> The iid χ² critical value is 36.4. The correct critical value for *this* series is 112.5.
> Using the former on the latter is how a desk talks itself into a pattern.

---

## 2. Lo–MacKinlay variance ratio

**Heteroskedasticity-robust statistic (z₂) reported** — the homoskedastic z₁ is shown only to
expose how much volatility clustering alone inflates it.

| q | VR | z₁ (homosk.) | **z₂ (robust)** | p(z₂) | sign-flip 95% band | emp p |
|--:|---:|---:|---:|---:|:--:|---:|
| 2 | **1.0248** | +1.017 | **+0.325** | 0.745 | [0.858, 1.146] | 0.744 |
| 4 | **1.0378** | +0.828 | **+0.298** | 0.766 | [0.774, 1.248] | 0.760 |
| 8 | **0.9927** | −0.102 | **−0.041** | 0.967 | [0.708, 1.391] | 0.964 |
| 12 | **0.9925** | −0.082 | **−0.036** | 0.972 | [0.673, 1.489] | 0.926 |
| 24 | **1.0112** | +0.084 | **+0.043** | 0.966 | [0.605, 1.628] | 0.821 |

Every VR is within 4% of 1.0. There is no trending signature (VR > 1) and no mean-reverting
signature (VR < 1) at any horizon from 2 to 24 hours. Note z₁ at q = 2 is 3.1× z₂ — the
homoskedastic statistic overstates significance threefold here.

**The control, for contrast.** One seeded Gaussian random walk (seed 1685):

| q | 2 | 4 | 8 | 12 | 24 |
|--|--:|--:|--:|--:|--:|
| VR | 0.966 | 0.903 | **0.822** | 0.825 | 0.821 |
| z₂ | −1.44 | **−2.17** | **−2.50** | −1.93 | −1.35 |

**A series with no memory whatsoever returned two significant mean-reversion results.** The real
market returned none. If this desk had run a variance ratio test and found VR(8) = 0.82,
z = −2.50, it would have had a mean-reversion thesis. That is what one draw of noise looks like
at this sample size.

---

## 3. Runs test

| | |
|---|---|
| up / down / zeros dropped | 840 / 799 / 45 |
| observed runs | **813** |
| expected under independence | 820.0 (sd 20.2) |
| **z** | **−0.345**, p = 0.730 |
| permutation null 95% | [781, 859], emp p = 0.748 |
| sign-flip null 95% | [781, 859], emp p = 0.770 |

Seven runs fewer than independence predicts, against a standard deviation of twenty. Nothing.
Control draws: Gaussian **z = +2.031**, permutation z = +1.039, sign-flip z = −0.806 — again the
synthetic random walk produced a nominally significant result and the market did not.

---

## 4. Hurst exponent

| estimator | observed | Gaussian-RW null median (95%) | p | sign-flip null median | p |
|---|---:|---:|---:|---:|---:|
| R/S, Anis-Lloyd corrected | **0.5113** | 0.5097 [0.451, 0.566] | 0.95 | 0.4997 | 0.69 |
| R/S, **uncorrected** | **0.5691** | **0.5675** [0.509, 0.624] | 0.95 | 0.5574 | 0.69 |
| DFA-1 | **0.5248** | 0.4960 [0.422, 0.583] | 0.45 | 0.4849 | 0.49 |

**Bias direction, as required: short-series R/S is biased UPWARD.** The uncorrected estimator
returns **0.5675 on a series known to be an exact random walk** at this length — not 0.50. The
observed 0.5691 is therefore not evidence of persistence; it is *indistinguishable from the bias
itself* (p = 0.95). Reading 0.569 against a remembered textbook 0.5 would have produced a false
"MES 60m is persistent/trending" claim. The Anis-Lloyd correction removes it (0.5113), and DFA-1,
which is less biased, gives 0.5248 well inside its own [0.422, 0.583] null.

---

## 5. The controls — what "null" looks like at n = 1,685

Three nulls, 4,000 replications each, seed 1685:

- **Gaussian RW** — iid normal, mean and sd matched. The textbook null.
- **Permutation** — the real returns shuffled. Keeps the exact marginal (fat tails, tick
  granularity, the 45 zeros); destroys serial dependence only.
- **Sign-flip (wild) bootstrap** — rₜ × ±1. **Keeps every |rₜ| in place, so the entire
  volatility path and all clustering survive, and randomises only direction.** This is the
  correct null for the question "is *direction* predictable?" and it is the one I lean on.

**Headline control result.** On sign-flip surrogates — zero return predictability by
construction — the naive ±1.96/√n band flags a mean of **5.06 lags out of 24** (median 5, 95th
percentile 8). The real series flags 7. **Empirical p = 0.231.** The "7 significant lags" is not
merely weak evidence; it is *below* the median-plus-one-sigma of a series that provably has
nothing to find.

| statistic | observed | correct null 95% | naive threshold | verdict |
|---|---:|---:|---:|---|
| Ljung-Box Q(24) | 78.3 | ≤ 112.5 | ≤ 36.4 | null (p = 0.26) |
| max\|ρ\| lags 1–24 | 0.0954 | ≤ 0.150 | ≤ 0.048 | null (p = 0.48) |
| naive-sig lag count | 7 | ≤ 8 | ≤ 1.2 | null (p = 0.23) |

**The tests are not underpowered in the trivial sense** — the ρ = 0 row of the power curve
below returns a false-positive rate of 0.058, correctly calibrated. They are simply being asked
about a series that has nothing at the sizes they can see.

---

## 6. Power — bounding "no structure" rather than asserting it

**Analytic, single pre-specified lag, α = 0.05 two-sided, n = 1,684:**

| quantity | naive (iid) | **robust (this series' δⱼ)** |
|---|---:|---:|
| significance threshold \|ρ\| | 0.0478 | **≈0.079** (typical lag) |
| min detectable at 50% power | 0.0478 | ≈0.079 |
| min detectable at 80% power | **0.0683** | **≈0.113** |
| Bonferroni over 24 lags | 0.0750 | ≈0.124 |
| at lag 1 specifically (δ₁ = 9.79) | 0.0478 | **±0.149** |

**Empirical power** (1,000 injected AR(1) series per row, sd matched):

| true ρ | lag-1 power | VR(2) power | edge pts/bar | × round-turn cost |
|---:|---:|---:|---:|---:|
| 0.000 | 0.058 | 0.057 | 0.000 | 0.00 |
| 0.020 | 0.130 | 0.136 | 0.119 | 0.11 |
| 0.040 | 0.385 | 0.394 | 0.238 | 0.23 |
| 0.050 | 0.542 | 0.551 | 0.297 | 0.29 |
| **0.068** | **0.791** | **0.801** | 0.404 | 0.39 |
| 0.100 | 0.983 | 0.989 | 0.594 | 0.57 |
| 0.150 | 1.000 | 1.000 | 0.891 | 0.86 |

**So the bounded statement is:** this sample would have caught a homoskedastic |ρ| ≥ 0.068 four
times in five, and did not. Allowing for the series' actual heteroskedasticity, the honest floor
is **|ρ| ≈ 0.11**, and at lag 1 — the lag a bar-to-bar directional strategy lives on — it is
**|ρ| ≈ 0.21**. Structure smaller than that could be present and invisible here.

**But that residual room is economically empty.** The cost column uses the desk's own spec
(round-turn 2.69 ÷ 5.0 point-value = 0.538 pt, plus one tick each way = **≈1.04 pts**). An AR(1)
at the 80%-power threshold ρ = 0.068 yields a conditional edge of **0.404 points per bar against
a 1.04-point cost — 39% of the fee**. Even ρ = 0.15, which this sample would detect with
certainty, returns 0.89 pts, still **below breakeven**. ρ² at these levels is 0.5–2.3% of return
variance.

> **The gap between "detectable" and "profitable" runs the wrong way.** An edge large enough to
> pay costs at 60m (|ρ| ≳ 0.18) is one this sample would find essentially every time. It is not
> there. The undetectable region is entirely inside the unprofitable region, so "we might have
> missed something small" is not a live hope — anything small enough to hide is too small to trade.

---

## 7. Two defects that manufacture apparent structure

### 7a. The contract-roll merge, bars 1146–1158 — already a known defect, newly implicated

Seven of the twelve largest |returns| in the whole tape sit in this 13-bar window, alternating
violently as price flips between two contracts ~70 points apart:

```
bar 1146 2024-12-17T04:00  +1.2953%     bar 1154 12:00  -1.2423%
bar 1151            09:00  -1.2555%     bar 1155 13:00  +1.1363%
bar 1152            10:00  +1.1535%     bar 1157 15:00  -1.0802%
                                        bar 1158 16:00  +1.1741%
```

Pairs six bars apart (1146→1152, 1151→1157, 1152→1158) share sign, which is precisely how
ρ₃ = +0.076 and ρ₆ = +0.095 — the two largest naive-significant lags — are produced. Excising
the window (n = 1,671):

| | full tape | merge excised |
|---|---:|---:|
| ρ₁ | +0.0236 | **+0.1313** |
| ρ₃ | +0.0762 ✱ | −0.0343 |
| ρ₆ | +0.0954 ✱ | +0.0126 |
| naive-sig lags | 7/24 | **1/24** |
| robust-sig lags | 1/24 | 1/24 |
| Ljung-Box Q(24) | 78.3 | 43.4 (sign-flip **p = 0.388**) |
| VR(2), z₂ | 1.025, +0.33 | 1.133, **+1.78** (p = 0.076) |

**Finding for the desk:** the roll merge is not only a fill hazard, it injects fake serial
correlation. Any future study of this tape should excise bars 1146–1158 before measuring
anything time-series-shaped.

### 7b. The lag-1 rise is one FOMC afternoon

Excising the merge *raises* ρ₁ to +0.131 (the merge's alternation had been masking it), which
looks like momentum. It is not.

| check | ρ₁ | note |
|---|---:|---|
| raw (merge excised) | +0.1313 | naive-sig; **robust band ±0.1463 → not sig** |
| winsorized 6σ | +0.0931 | |
| winsorized 4σ | +0.0693 | |
| winsorized 3σ | +0.0654 | |
| Spearman | +0.0381 | p = 0.120 |
| Kendall τ | +0.0251 | p = 0.124 |
| P(consecutive same sign) | 0.5082 | band ±0.0246 → null |

**One pair — bars 1166–1167, the 18 Dec 2024 FOMC selloff (−1.515% then −1.723%) — contributes
+0.0629 of the +0.1313, i.e. 48% of the entire statistic.** The top five pairs supply 61%. A
statistic that half-rests on one afternoon is a description of that afternoon.

The same fate meets the only other nominally significant number I found: regressing rₜ on
|rₜ₋₁| gives slope +0.0719, p = 0.015 — but its t-statistic of 2.43 sits inside a sign-flip null
band of **[−6.50, +6.59]** (empirical p = 0.528), and it decays to p = 0.21 winsorized at 3σ.

---

## 8. Volatility is predictable. Direction is not. These are different things.

| regression | slope | R² | p |
|---|---:|---:|---:|
| \|rₜ\| on \|rₜ₋₁\| | **+0.3343** (se 0.0230) | **0.1117** | 3 × 10⁻⁴⁵ |
| rₜ on \|rₜ₋₁\| | +0.0719 (se 0.0296) | 0.0035 | 0.015 → **0.528 robust** |

Absolute-return autocorrelation is positive and large out to lag 6 (+0.334, +0.200, +0.241,
+0.161, +0.123, +0.162) and **rises again at lags 21–24** (+0.157, +0.218, +0.179, +0.152, with
lag 46 at +0.151) — a clean diurnal cycle, since the tape runs 23 bars/day. Ljung-Box on |r| is
Q(24) = 738.6, p = 1.9 × 10⁻¹⁴⁰, and it survives the permutation null easily.

**The joint diagnosis — near-zero return autocorrelation sitting alongside strong, persistent
absolute-return autocorrelation — is the textbook signature of a martingale with GARCH-type
conditional heteroskedasticity.** That is not a defect in the data or a failure of measurement.
It is what a liquid, efficiently-priced index future is supposed to look like at 60 minutes.

**What this buys the desk, and what it does not:**

- **Does buy:** volatility is forecastable (R² = 0.112), so ATR-scaled stops, position sizing
  and regime labelling are all on solid empirical ground. Agent A's finding that stop distance
  behaves as a smooth cost gradient is consistent with this. The diurnal cycle means the hour of
  day genuinely predicts range.
- **Does not buy:** a direction. P(next bar same sign) = 0.5066 ± 0.0245. Knowing the next bar
  will be large tells you nothing about its sign, and a strategy that is right 50.7% of the time
  (well inside noise) cannot pay a 1.04-point round trip.

---

## 9. Verdict

**Is there detectable linear structure in MES 60m returns over this window? No.**

Four independent tests agree, each against a null matched to this sample and this series'
volatility: variance ratios within 4% of 1.0 at every horizon (robust |z| ≤ 0.33), a runs test
at z = −0.345, Hurst estimates on their own null medians, and an autocorrelation function whose
single robust exceedance out of 24 lags is exactly what chance delivers. The apparent
exceptions — a Ljung-Box p of 10⁻⁷, seven "significant" lags, a Hurst of 0.569, a lag-1 ρ of
0.131 — **every one of them dissolves when measured against the right null instead of the
textbook one.**

**Bounded, not absolute:** structure below |ρ| ≈ 0.11 (and below ≈0.21 at lag 1) could exist
here undetected. But an edge that small returns under 40% of the round-turn cost, so the
undetectable region is contained within the unprofitable region. **There is no size of hidden
linear edge that is both invisible to this sample and worth trading.**

**This explains the desk's nulls economically.** The stand-down counterfactual, the S/R level
study and the thesis-5 mechanisation were not underpowered or badly specified. They were
directional tests on a series whose direction is a martingale at this frequency. **A fifth
directional study at 60 minutes should not be commissioned**; the prior that it returns null is
now quantitative rather than anecdotal.

### Reconciliation with E5 — we are not contradicting each other

E5's commit reads *"structure smaller than cost" is supported, "no structure" is not*, on the
strength of a gross expectancy of **+0.0225 R** that one tick of slippage flips to −0.0032 R.
That is compatible with everything above, and the distinction is worth stating because the two
reports will be read side by side.

**Drift and serial dependence are different properties, and only the second is what "random
walk" denies.** A random walk *with drift* has VR = 1, zero autocorrelation, a null runs test
and H = 0.5 — every result in this report — and still pays a positive gross expectancy to an
always-long bracket, simply because price ends higher than it started. This window drifted
**+5.77%**, i.e. **+0.204 points/bar = +0.0195 R per bar held** at the median 1R of 10.46 points.
That is the same order as E5's +0.0225 R, so drift alone is a sufficient explanation for their
gross figure without any serial structure existing.

**So the two findings compose:** what little gross edge the tape offers comes from *being in it*
(drift, an unconditional beta the desk does not need a pattern to collect), not from *timing* it
(serial predictability, which is what every desk study has been hunting). Both of us then agree
it is smaller than cost.

**One caveat against my own reconciliation:** E5's 3,318 trials take *both* directions at every
eligible bar, and drift should largely cancel between the long and short arms — so drift may not
be the whole of their +0.0225 R, and geometry (a 2R target against a 1R stop under fat tails)
plausibly supplies some of it. I have not re-derived E5's number and do not claim to have
explained it fully. What I do claim is narrower and is what my tests actually support: **the
drift in this window is +0.0195 R/bar and its own t-statistic is 0.802 — not significant either.**
Neither the direction of the next bar nor the drift of the window clears its error bar here.

**What remains open, honestly:**

- **This window only.** 14.9% of the series, one regime (a 13.3%-vol uptrend). The remaining
  9,602 bars include regimes this sample does not contain. The claim is not "MES 60m is a
  random walk"; it is "this window is, and the tests had the power to say otherwise."
- **Linear structure only.** Every test here is a linear-dependence test. Conditional or
  non-linear structure — an edge that exists only after a specific setup, in a specific hour,
  or in a specific volatility regime — is untouched by all four, and a martingale is fully
  compatible with it. What is now ruled out is unconditional, always-on directional edge.
- **Other timeframes.** "At this timeframe" is load-bearing. Nothing here speaks to 5m or daily.
- **Volatility is the exploitable axis if there is one.** R² = 0.112 with a diurnal cycle is a
  real, robust, reproducible regularity in this tape. It is the only thing in this study that
  is not noise. It pays for better sizing and better stops — not for a direction.

---

## Trials

Declared rather than buried.

| block | statistics |
|---|---:|
| return ACF lags (each read against naive *and* robust band) | 24 |
| absolute-return ACF lags | 24 |
| Ljung-Box (returns, \|returns\|) | 2 |
| variance ratio, q = 2/4/8/12/24 (z₂ read; z₁ reported) | 5 |
| runs | 1 |
| Hurst (R/S corrected, R/S raw, DFA-1) | 3 |
| session-break robustness pass | 7 |
| volatility regressions + sign persistence | 3 |
| **script subtotal** | **69** |
| merge-excision battery (§7a) | ~16 |
| outlier diagnostics: 5 winsorisations × 2, Spearman, Kendall, sign (§7b) | 13 |
| **honest total** | **≈98** |

At α = 0.05 with 98 statistics, ~4.9 false positives are expected before anything real. **I am
claiming no finding on any individual statistic.** The verdict rests on the sign-flip empirical
nulls for the *maximum* |ρ| and the *joint* Ljung-Box, both of which absorb the 24-lag search by
construction and are therefore multiplicity-free — and both return p ≈ 0.25–0.48.

### One bug, found and fixed mid-study

The script was run to completion twice. The first run's Lo–MacKinlay `delta_j` was missing its
leading factor of `n`, which deflated ψ\* by n and **inflated every robust VR z-statistic by
√n ≈ 41** — reporting z = +16.0 for VR(2) = 1.031. It was caught because a VR of 1.03 cannot
produce a z of 16. **Only the fixed run is reported above.** The fix is verified two ways: on
homoskedastic iid input z₁ and z₂ now agree to within 0.2% (ψ\* → ψ, as theory requires), and on
an AR(1) with ρ = 0.5 the estimator returns VR(2) = 1.497 against the theoretical 1 + ρ = 1.5.
The ACF, runs and VR code were additionally validated against known processes: AR(1) ρ = 0.5
recovers ρ₁₋₃ = 0.497/0.245/0.125 (theory 0.5/0.25/0.125), and the runs test returns z = ±9.85
on perfectly alternating vs perfectly blocked signs.

---

## Reproduce

```
cd workspace/paper/REPLAY/R1/agents && python3 E2_randomwalk.py
```

Requires numpy and scipy. Seed 1685; 4,000 replications per null (Gaussian RW, permutation,
sign-flip); 1,000 per row of the power curve. Runtime ~12 minutes, dominated by the Hurst
replications. Reads `../visible.jsonl` and nothing else; writes nothing.
