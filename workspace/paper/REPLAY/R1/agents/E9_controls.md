# E9 — audit of the controls the R1 desk's nulls rest on

Scripts: `agents/E9_controls.py` (missed.py control + parity), `agents/E9_levels_fair.py`
(levels.py control). Both read-only over `visible.jsonl` / `callouts.jsonl`; both re-implement
the desk's logic rather than importing it, so nothing here can advance a cursor or rewrite
`missed.jsonl`. Reproduction check: `E9_controls.py` §0 returns the published figures exactly
(n=42; always-LONG +0.239R z +1.08, always-SHORT +0.081R z +0.38, coin-flip +0.161R z +0.73),
so the audit is measuring the same objects the record quotes.

---

## LEAD: does any published z change under a fairer control?

**`missed.py`: no. `levels.py`: yes — three of its numbers move, and one null breaks.**

| published claim | as published | under a fairer control | verdict |
|---|---|---|---|
| missed.py always LONG | **z +1.08** | +1.34 (hour × ATR-quartile matched) | holds |
| missed.py always SHORT | **z +0.38** | +0.09 (matched) | holds |
| missed.py coin flip | **z +0.73** | +0.66 (matched), +0.66 (parity-matched) | holds |
| missed.py BEST (hindsight) | **z +1.59** | +1.65 (matched) | holds |
| missed.py pivot, with-the-turn | **z +0.06** | −0.32 (matched) | holds (sign flips, magnitude nil) |
| levels.py bounce *rate*, 1-touch fresh extreme | **z ≈ +1.76**, −8.8pp | **−3.9pp, z −0.73** like-for-like | **halved — the kept finding shrinks** |
| levels.py **bounce trade arm** | **z +0.08** ("nothing") | **z +2.52** (10-seed mean, range +1.57…+3.20) | **NULL BREAKS** |
| levels.py break trade arm | **z +1.17** | **z −0.82** (sign flips) | **not reproducible** |

Nothing in `missed.py` moves materially, and nothing in either file crosses the desk's own
corrected `free_t` = 2.45 with confidence. **But `levels.py`'s "the levels are decoration"
conclusion is the one that should not be left standing as written**: its single largest null,
the bounce trade arm at z +0.08, is an artefact of three defects in the random-line control, and
under a control built without them the same data gives z ≈ +2.5. That is a **sixth mechanism by
which this codebase manufactured a false null**, and like the five in `BRIEF.md` it is silent.

---

## 1. `missed.py`'s all-bars control — **SOUND, with one caveat**

### 1a. The feared confound is not present

The brief's hypothesis was "the stand-downs are 60% overnight, the control is 25%". Measured:

| session | stand-down | control | ratio |
|---|---|---|---|
| overnight 00–08 ET | **33.3%** | 39.1% | 0.85 |
| evening 18–23 ET | 23.8% | 26.0% | 0.91 |
| RTH 09–16 ET | 42.9% | 34.9% | 1.23 |

The stand-downs lean **toward** RTH, not away from it, and by a factor of 1.23 — not 2.4. The
imbalance runs in the opposite direction to the one suspected.

### 1b. Balance statistics, all four axes

| axis | total variation distance | worst single cell |
|---|---|---|
| hour of day (24 buckets) | **0.292** | hour 00 and hour 12 at 2.2× control |
| ATR quartile | **0.180** | Q3 at 42.9% vs 24.8% (1.73×) |
| day of week | **0.069** | Tue 1.27× |
| bars to session close | **0.090** | 16:00 bars 1.65× |

Standardised mean differences on the continuous versions are negligible: ATR **SMD −0.052**
(stand-down mean 11.82 pts vs control 12.14), bars-to-close **SMD −0.096** (10.57 vs 11.28). Both
are an order of magnitude inside the |SMD| > 0.25 imbalance convention. The hour TVD of 0.292 looks
large only because 24 buckets at n=42 cannot be smooth — five hours have zero stand-downs purely
because 42 observations cannot fill 24 cells.

The one genuine structural imbalance is **ATR quartile Q3 at 1.73×**, and it is non-monotone
(Q1 0.86, Q2 0.76, Q3 1.73, Q4 0.67) — which is why the mean ATR barely moves. A non-monotone
imbalance cannot transmit much bias into a mean.

**Pivot rate: stand-down 38.1% vs control 51.3% (ratio 0.74).** The desk's declined bars were
*less* often at pivots than an arbitrary bar. This is the one place the composition genuinely
differs, and it works against the desk's "I missed reversals" impression rather than for it.

### 1c. How much can composition alone move the answer?

Reweighting the whole control to the stand-downs' (hour × ATR-quartile) mix:

| arm | raw control | reweighted | shift |
|---|---|---|---|
| always LONG | +0.015R | −0.033R | **−0.048R** |
| always SHORT | −0.021R | +0.042R | **+0.063R** |
| coin flip | −0.012R | +0.008R | +0.020R |
| BEST | +0.947R | +0.951R | +0.004R |

**Composition can move the control mean by at most ±0.06R.** The arm differences under audit are
+0.24R, +0.08R and +0.16R. So composition accounts for at most a quarter of the long arm's gap —
and in the direction that would make the desk look *better*, not worse. This is the number that
settles question 1: the imbalance exists, it is small, and it cannot manufacture the null.

### 1d. The matched re-run (post-stratified, paired)

Estimator: each stand-down's benchmark is the mean of every control bar in its own
(hour, ATR-quartile) cell; z = mean(d)/SE(d) over the 42 paired differences, with fallback to
(hour) then (ATR quartile) for empty cells. All 42 stand-downs matched under every design.

```
ARM: always LONG                             diff        z
  unmatched (published)                   +0.239R    +1.08
  matched: hour                           +0.258R    +1.18
  matched: ATR quartile                   +0.252R    +1.17
  matched: hour x ATRq                    +0.286R    +1.34
  matched: hour x ATRq x bars-to-close    +0.283R    +1.32
ARM: always SHORT      +0.081R/+0.38  ->  +0.017R/+0.09  (hour x ATRq)
ARM: coin flip         +0.161R/+0.73  ->  +0.141R/+0.66
ARM: BEST (hindsight)  +0.292R/+1.59  ->  +0.288R/+1.65
ARM: pivot, with turn  +0.006R/+0.02  ->  -0.113R/-0.32
```

**No z moves by more than 0.3, none changes a conclusion, none approaches 2.45.** The desk's
"my stand-downs cost nothing measurable" survives matching intact.

### 1e. Two SE problems, both checked, neither fatal

- **Self-inclusion.** The 42 stand-down bars are themselves members of the 1659-bar control.
  Removing them moves every z by ≤ 0.03 (LONG +1.08 → +1.10). Negligible at 42/1659, but it is a
  real circularity and should be excluded on principle.
- **Overlapping forward windows.** Control arm values have lag-1 autocorrelation of **ρ₁ = +0.67**
  (always LONG), so 1659 bars are nowhere near 1659 independent observations and Welch's SE for
  the control term is optimistic. The correct null here is a **circular-shift placement test** —
  slide the sample's own 42-bar spacing pattern along the tape and re-measure (70 placements):
  always LONG **z +1.11** (p = 0.143) against Welch's +1.08; coin flip **+0.72** against +0.73;
  always SHORT +0.91 against +0.38. The Welch z's are broadly honest. (A naive stationary block
  bootstrap gives +0.52, but it is the wrong shape — it imposes 24-bar clustering on a sample
  whose median gap is 50 bars, so it is over-conservative and should not be quoted.)

### 1f. The one caveat worth recording

A **16:00 bar's entire trade is one bar** — `session_end(f)` returns `f` itself, so the simulation
opens and flats inside the same candle and almost always exits SESSION_CLOSE at a fraction of R.
The control's 16:00 bars return **−0.052R long against +0.015R overall**. Stand-downs are 7.1%
16:00 bars vs the control's 4.3%, so the desk is *over*-weighted in the cheapest bars in the tape —
again a bias against the desk, not for it. Matching on bars-to-close (the last row of §1d) absorbs
it and changes nothing.

**Verdict on control 1: FAIR.** The eligible set is comparable on every axis measured; the
residual imbalance can move the control mean by ≤ 0.06R against differences of 0.08–0.29R; and
matched, parity-matched, self-inclusion-corrected and autocorrelation-aware re-runs all leave
every published z within 0.3 of where it was. **The nulls in the missed-opportunity register are
real nulls.**

---

## 2. `levels.py`'s random-price-line control — **NOT FAIR. Three defects, and one null breaks.**

### 2a. Where the lines sit (the price-distribution question)

The premise in the brief — that pivots cluster at extremes and a uniform draw would not — is
**false on this tape, and backwards**:

| position in trailing 300-bar range | real levels | random lines |
|---|---|---|
| outer 20% (0.0–0.1 and 0.9–1.0) | **11.8%** | **20.2%** |
| mean \|position − 0.5\| | 0.211 | 0.250 |

TVD over deciles = **0.193**. Real multi-touch levels are *more* mid-range than uniform, because a
level earns touches by being revisited and the range extremes are visited once by construction. So
the uniform draw is not mis-specified in the feared direction — but it is still mis-specified, and
it over-samples the extremes by 1.7×.

### 2b. The composition bias nobody looked for: the control tests in a more volatile tape

| ATR quartile at the *test event* | real level tests | control as published |
|---|---|---|
| Q1 | 25.3% | 17.6% |
| Q4 | 24.7% | **38.5%** |

Mean ATR at an event: **real 11.99 pts, published control 15.22 pts — 27% higher.** Twelve uniform
lines per bar get reached disproportionately when volatility is high, so the "random lines" are
tested in a systematically different regime from the levels they are supposed to control for. This
is the confound the brief asked about in §1, present in control 2 rather than control 1, and larger.
ATR-matching the published control halves the headline rate gap: **−4.7pp → −2.3pp**.

### 2c. The touch-count fabrication — the fatal one

`levels.py:129` assigns `rng.choice([2,2,3,4])`. Measured against the real level population
(32,195 level-instances):

| touches | real | control |
|---|---|---|
| 1 | **58.7%** | **0.0%** |
| 2 | 20.2% | 50.6% |
| 3 | 10.1% | 24.6% |
| 4 | 3.7% | 24.8% |
| 5+ | **7.3%** (to a max of 31) | **0.0%** |

Three consequences:

1. **100% of control lines clear `touches >= 2`; only 41.3% of real levels do.** The eligibility
   filter is load-bearing for the treatment and inert for the control.
2. **12 lines per bar against 9.78 real eligible lines per bar.** The docstring's claim that the
   control runs "in the same count" (`levels.py:19`) is **false as written** — same defect family
   as the dead `STOP_ATR` constant agent A found in `missed.py`: a label that lies while nobody
   checks the arithmetic.
3. **The buckets the record reports have no control counterpart at all.** NOTES.md:985 compares
   *"fresh swing extreme (1 touch), n=162, 45.7%"* to *"random price lines (control), n=200,
   55.0%"* — a control containing **zero 1-touch lines**. NOTES.md:994's touch-bucket row quotes
   control rates for 2/3/4 only, because 5 and 6+ **do not exist** in the control. The desk's own
   sentence, *"a control whose touch counts are fabricated is not a control for a touch-count
   claim"*, is exactly right and was never applied.

### 2d. Contamination: a fifth of the control **is** the treatment

**20.9% of uniform lines (490/2340) land inside the 0.25-ATR test band of a real detected level.**
At the count-matched density it is **46.8%**. A control that is one-fifth to one-half treatment
attenuates every real-minus-random difference toward zero — a textbook false-null generator, and
the mechanism that produced the +0.08 the record calls "nothing".

### 2e. Rebuilding the control fairly, and what moves

Four variants, identical test procedure throughout (`E9_levels_fair.py`):
**A** as published · **B** count-matched · **C** touch counts resampled from the real distribution
(so 1-touch and 5+ exist) · **D** count- and touch-matched **and** decontaminated (lines redrawn
until they are not within 0.25 ATR of any real level; residual contamination 0.0%).

**The kept finding (1-touch fresh extreme, published −8.8pp at z ≈ 1.76):**

| control | n | bounce | diff vs real 45.3% | z |
|---|---|---|---|---|
| A as published (pooled, no 1-touch lines exist) | 205 | 54.1% | −8.8pp | −1.70 |
| C, **its 1-touch subset** — like for like | 135 | 55.6% | −10.2pp | −1.78 |
| **D (fair), its 1-touch subset — like for like** | **189** | **49.2%** | **−3.9pp** | **−0.73** |

**More than half the desk's "largest deviation from control anywhere in the study" is the control's
contamination, not the levels.** The finding was already correctly declared a non-result against
`free_t` 2.45; it is a weaker non-result than the record states.

**The trade arms (published: bounce z +0.08 "nothing", break z +1.17):**

| control | bounce diff | z | break diff | z |
|---|---|---|---|---|
| A as published | +0.018R | +0.14 | +0.187R | +1.53 |
| B count-matched | +0.122R | +1.17 | +0.106R | +1.00 |
| C touch-matched | +0.132R | +1.12 | +0.134R | +1.12 |
| **D fair** | **+0.338R** | **+3.32** | −0.090R | −0.82 |

**Robustness of D, because a z that appears under a control I built is exactly what this audit
exists to distrust:**

- **Seed stability (10 seeds):** diff +0.262R (range +0.167…+0.329), **z mean +2.52, range
  +1.57…+3.20, sd 0.53.** Stable.
- **Support/resistance mix** (the obvious confound, since "trade the bounce" is LONG at support on
  an up-drifting tape): real 48.9% support, D 47.8%. Re-weighting the within-side differences to
  the real side mix gives **+0.338R — identical**. Not a side-composition effect.
- **Regime at the event bars:** real ATR 11.99 / |c−o|/ATR 0.799; D 11.85 / 0.821. Matched. (The
  *published* control A sits at 15.22 — it is control A, not control D, that is regime-confounded.)
- **ATR-quartile matched:** +0.331R, unchanged.
- **Decomposition:** decontamination alone takes the control's bounce arm from +0.026R to −0.038R
  (z +0.66); count+touch matching alone to −0.099R (z +1.36); together to −0.294R (z +3.32).

**Incidentally, the published control is a single `seed=7` draw with its own Monte Carlo error
unquoted:** across 10 seeds variant A's bounce z runs **−0.49 to +1.88, sd 0.79**. The record's
"+0.08" is one sample from that spread, reported as if it were the statistic.

**How to read the +2.5, honestly.** It is *not* an edge. Real levels' own bounce arm is +0.043R —
nothing in absolute terms. The entire movement comes from the fair control being **−0.294R**: a
price line demonstrably *not* at a pivot is a bad place to fade. The defensible statement is
**"real levels are distinguishable from non-levels on the fade trade"**, which is a weaker and
different claim from "levels are tradeable" — and my own search width here is 4 control variants ×
2 arms plus buckets, ≥ 10 trials, so z +2.52 against `free_t` 2.45 is **a flag for pre-registration,
not a result to bank**. One further caveat: variant D is strictly an *anti-level* control
("lines that are demonstrably not levels"), a sharper contrast than "random lines", and that
should be stated wherever it is quoted.

**Verdict on control 2: UNFAIR, and it manufactured a null.** The touch-count fabrication
invalidates every touch-count claim in NOTES.md:985–995 outright — the 1-touch and 5+ buckets have
no control, and `>= 2` is an eligibility filter the control cannot fail. The contamination and the
count mismatch attenuated the trade arms toward zero. **`levels.py` needs its control rebuilt
before any conclusion drawn from it is quoted again.**

---

## 3. `missed.py`'s coin-flip arm — **the parity is fine; the SAMPLE's parity mix is not**

### 3a. Parity is independent of the tape

The worry was that 22-bar cycles would lock parity to hour-of-day. They do not — this tape runs
**23 bars per session** (00–16 ET plus 18–23 ET), and 23 is odd, so parity rotates cleanly through
every hour:

```
max |even% - odd%| across the 24 hours: 0.005      TVD 0.0272
ATR            even 12.142  odd 12.144   z -0.00   SMD -0.000
bars-to-close  even 11.280  odd 11.274   z +0.02   SMD +0.001
LONG R         even  +0.010 odd  +0.020  z -0.15   SMD -0.007
SHORT R        even  -0.009 odd  -0.033  z +0.36   SMD +0.018
bar ret (c-o)/ATR even +0.005 odd +0.042 z -0.77   SMD -0.038
```

Every |SMD| ≤ 0.04. Parity is as good as a fair coin on this tape, and 400 genuinely randomised
flips put the parity flip's z (+0.73) squarely inside their spread (mean +0.66, sd 0.91).
**Agent A's burst-12 fix — keying the control on bar index rather than list position — was the
right fix and it holds.**

### 3b. But the 42 stand-downs split 29 even / 13 odd

Binomial **z = +2.47** against 50/50. The flip arm therefore reads **69% long-side on the sample
and 50% on the control** — the two arms are not running the same coin. On a tape where an
arbitrary bar returns +0.015R long and −0.021R short, that mix alone shifts the control's own flip
mean by +0.015R. Parity-matching the control:

```
coin flip, published        +0.161R   z +0.73
coin flip, parity-matched   +0.146R   z +0.66
```

Immaterial *here*, only because long and short are near-identical on this tape. **It will not stay
immaterial once the tape develops directional drift**, and the fix costs nothing: weight the
control's flip arm to the sample's own even/odd split, or draw the flip from an RNG seeded per bar
rather than from parity.

**Verdict on control 3: the coin is fair; the sample is not drawing from it evenly. Cosmetic
today, a real defect the moment drift appears.**

---

## 4. Is the all-bars control too easy or too hard? — **it answers a narrower question than the record implies**

**What it actually answers:** *"Conditional on the desk having written a NO_TRADE callout at bar f,
is the forgone R at bar f distinguishable from the forgone R at a bar drawn uniformly from the
tape?"*

Three gaps between that and "did the desk's judgement add value":

1. **The treatment arm is not "bars I declined" — it is "bars I declined *and chose to document*".**
   The desk was flat at essentially all 1,685 bars and journalled **43**. More than 97% of its
   actual stand-downs never enter the numerator. The register therefore measures the desk's
   *callout cadence* as much as its judgement, and a desk that writes callouts only when something
   looks interesting has pre-selected its own treatment arm. This selection layer is invisible in
   the statistic and is nowhere stated in NOTES.md.
2. **There is no positive arm.** Judgement is a *contrast* — bars taken versus bars declined. The
   desk has **2 DISCRETIONARY callouts and 2 closed trades**. With n=2 on the take side, no
   comparison of that shape is available at any power. The all-bars control cannot supply it; it
   can only ever answer the decline-side question.
3. **The benchmark is arbitrary-bar, not achievable-alternative.** "Better than a bar picked at
   random" is a floor almost any filter clears eventually; it is not "better than the next-best
   thing the desk could have done with the same capital and the same 16:00 flat".

So: **too easy as a test of judgement, correctly calibrated as a test of the specific claim it is
used for.** The record's own sentence — *"the bars I declined were not detectably better than
arbitrary bars"* (NOTES.md:895) — is precisely and only what the control supports, and it is
phrased correctly there. The risk is the next reader compressing it to "my judgement was
vindicated". It was not tested.

**Verdict on question 4: the control is honest but weaker than it reads. It should be labelled
"declines vs arbitrary bars", never "judgement vs no judgement", and the 43-of-1685 documentation
filter on the treatment arm should be stated wherever the n is quoted.**

---

## Summary of verdicts

| control | verdict |
|---|---|
| `missed.py` all-bars | **FAIR.** Balanced on hour, ATR, day-of-week and holding window; composition can move the control mean ≤ 0.06R against differences of 0.08–0.29R; every z survives matching within 0.3. The nulls are real. |
| `levels.py` random lines | **UNFAIR — a false-null generator.** Fabricated touch counts (0% 1-touch vs 58.7%), 20.9–46.8% contamination by real levels, unmatched count (12 vs 9.78/bar), 27% higher ATR at the event, single-seed reporting. Invalidates every touch-count claim; breaks the bounce-arm null (+0.08 → +2.5). |
| `missed.py` coin flip | **Parity is fair (all \|SMD\| ≤ 0.04). The sample's 29/13 split is not** (binomial z +2.47) — harmless on this tape, a defect once drift appears. |
| all-bars as a benchmark | **Honest but narrow.** Answers "declines vs arbitrary bars". Cannot answer "did judgement add value": n=2 on the take side, and 97% of stand-downs are undocumented. |

## What should change

1. **Retract nothing in the missed-opportunity register.** It is the sound one. Add the
   self-inclusion exclusion and the placement-test z as a footnote.
2. **Suspend every touch-count claim in NOTES.md:985–1014** until `levels.py`'s control draws
   touch counts from the real distribution. The "fresh swing extreme breaks more often" line
   should be restated at −3.9pp / z −0.73, not −9pp / z 1.76.
3. **Fix `levels.py`'s control**: resample touch counts from the real level population; draw the
   same number of lines as there are real levels; reject draws inside the test band of a real
   level *or* state plainly that the control includes real levels; average over ≥ 10 seeds and
   quote the seed spread.
4. **Correct `levels.py:19`** — "in the same count" is not true of the code beneath it.
5. **Pre-register the bounce-arm contrast** (real levels vs demonstrably-non-level lines, fade
   trade, +0.34R, z ≈ 2.5 at ≥ 10 trials) before it is measured again. It is the only live
   candidate this audit produced and it must not be banked on the search that found it.
6. **Weight the coin-flip control to the sample's parity split**, or reseed the flip per bar.

*Not committed, per the brief.*
