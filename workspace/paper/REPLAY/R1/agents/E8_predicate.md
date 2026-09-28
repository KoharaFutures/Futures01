# E8 — Can an honest predicate be built for thesis 5? **No.**

**Agent E8, REPLAY desk R1.** Reads only `visible.jsonl` (through `agents/C_regime.py`'s signal
generator, the same population `D_discretion.py` uses) plus `NOTES.md`, `callouts.jsonl` and the
other whitelisted files in this directory. **No harness run, no cursor advanced, `state.json` not
opened, `data/archive/`, `csv/` and `workspace/roundtable/lib/replay.py` not opened.** Not committed.

---

## The one-paragraph answer

**No predicate survives.** Across **105 pre-declared (variable, cut-point) trials** the best split in
the whole sample reaches **|z| = 2.10** against a deflation threshold of **free_t = 3.05**. A label
permutation of the identical grid says the observed best is not merely short of the threshold but
**worse than noise usually produces**: the null distribution of max|z| over this grid has median
**2.55** and 95th percentile **3.47**, giving the best split a family-wise **p = 0.86**. The one split
that *did* clear the threshold — fitted on the first half of the tape at z **+3.62** — **reverses sign
on the second half (z −2.01)**. At n = 444 this sample could not have detected a per-trade edge below
**≈ +0.19R**, and could not have detected a keep-versus-drop separation below **≈ +0.40R** on any
subset of a third of the population. Thesis 5 should not be traded.

---

## 1. Population — unchanged from agent C, so the numbers are comparable

```
BASE (creg.sigs, desk filt() applied, resolvable inside the visible tape)
  n = 444   mean +0.0247R   sd 1.3131   win 38.1%   SE of mean 0.0623R
  sides: LONG 262 / SHORT 182     signal bars 60..1667 of 1685
  both desk trades (bars 452, 1337) are in the population
```

**Reconciliation note:** the consolidation section of `NOTES.md` quotes **442**; I get **444** on the
same code. The tape has grown from cursor 1635 to 1685 since that figure was written, which is the
likely cause. I did not chase it, because the difference is 2 signals and 0.5%, and because **C's
unreconciled 442-vs-91 discrepancy is still open** — I inherited C's artefact (the `sigs` list), not
C's headline, which is what the consolidation section says to do.

## 2. The search grid — declared in full, because a search you cannot count is a search you cannot deflate

**15 conditioning variables, every one computable strictly from bars at or before the signal bar `i`.**
No variable reads bar `i+1` (the fill bar) or later. Definitions, so this is falsifiable rather than
narrated:

| # | name | definition (SHORT case; LONG is the mirror) |
|---|---|---|
| 1 | `v_distatr` | `abs(c[i] - L) / ATR[i]` — signal close's distance from the level |
| 2 | `v_levelage` | `i - piv` — bars since the fractal pivot that defined the level |
| 3 | `v_excursion` | `max(L - l[b]) / ATR[i]` over the break window — how far price travelled beyond the level |
| 4 | `v_brkbars` | count of bars in the break window closing beyond `L - 0.25*ATR` — how long the break lasted |
| 5 | `v_brkrecency` | `i - brk` — bars since the last bar that closed beyond the level |
| 6 | `v_rangeatr` | `(h[i] - l[i]) / ATR[i]` — signal bar range |
| 7 | `v_closepos` | `(c[i] - l[i]) / (h[i] - l[i])` — close position in range; low = strong rejection |
| 8 | `v_overshoot` | `(h[i] - L) / ATR[i]` — how far the retest *exceeded* the level rather than only approaching it |
| 9 | `v_volratio` | `v[i] / median(v[i-20..i-1])` — signal bar volume vs trailing median |
| 10 | `v_atrpct` | `pct_rank(ATR[i])` in the trailing 250 — ATR percentile (C's own function) |
| 11 | `v_touches` | distinct touch *episodes* of `L` (bar range straddles `L`) in the prior 300 bars |
| 12 | `v_sincesig` | bars since the previous signal in the population (capped 500) |
| 13 | `v_stopatr` | `S / ATR[i]` — stop size in ATR |
| 14 | `v_trendwith` | 40-bar close change in ATR, **signed with the trade** (`-td` for SHORT) |
| 15 | `v_hour` | ET hour of the fill bar |

**7 cut-points per variable**, fixed before any result was read: the 20/30/40/50/60/70/80th quantiles
of that variable inside the population. Splits leaving fewer than 25 signals on either side are
skipped; none were, so the grid is exactly **15 × 7 = 105 trials**.

**Direction is also chosen post-hoc** — I report whichever side of each cut has the higher mean — so
every `z` quoted here is two-sided and `free_t` applies to it directly.

## 3. The threshold, stated before the winner

```
variables examined            : 15
cut-points per variable       :  7
(var, cut) trials evaluated   : 105
free_t = sqrt(2 * ln 105)     = 3.051
if keep-above/keep-below is counted separately, n = 210, free_t = 3.270
```

**Nothing below |z| = 3.05 is a finding.** The desk's own corrected search width is 20 theses
(`free_t` 2.45); this search alone adds 105 trials, and those are *this file's* trials, so 3.05 is the
number that governs anything I claim. I am also not entitled to reuse the desk's 2.45 — the searches
compose, they do not compete.

## 4. The winner — and it loses

Top of the full-sample grid:

| var | q | cut | keep | n_keep | mean_keep | n_drop | mean_drop | z |
|---|---|---|---|---|---|---|---|---|
| `v_closepos` | 60 | 0.277 | BELOW | 266 | +0.132R | 178 | −0.135R | **−2.10** |
| `v_brkbars` | 80 | 21.0 | BELOW | 366 | +0.079R | 78 | −0.228R | −1.98 |
| `v_sincesig` | 50 | 1.0 | ABOVE | 184 | +0.162R | 260 | −0.073R | +1.84 |
| `v_brkbars` | 20 | 2.0 | BELOW | 95 | +0.240R | 349 | −0.034R | −1.81 |
| `v_distatr` | 30 | 0.205 | BELOW | 133 | +0.195R | 311 | −0.048R | −1.74 |
| `v_levelage` | 80 | 214.4 | ABOVE | 89 | +0.231R | 355 | −0.027R | +1.62 |
| `v_trendwith` | 20 | −3.553 | ABOVE | 355 | +0.074R | 89 | −0.170R | +1.61 |

**Best = `v_closepos` (the signal bar closing in the lower 28% of its own range) at |z| 2.10 against
free_t 3.05. FAILS.** The economic story is the most plausible one on the list — a rejection bar that
closes on its low is a more decisive rejection than one that closes mid-range — and it is still not a
result. *A variable that gives z +2.1 after 105 trials has found nothing*, which is the instruction I
was given and also what the arithmetic says.

**The count that settles it:** exactly **1 of 105** splits reaches |z| > 2.0. Pure noise on 105
independent tests would produce about **4.8**. The trials are correlated, so 4.8 is an overestimate —
but the search produced **fewer nominally significant splits than chance**, not more. There is no
structure here being obscured by multiplicity; there is no structure here.

## 5. Permutation null — the honest version of `free_t`

`free_t` assumes independent trials. Mine are not: 7 cuts of one variable are nested, and several
variables are correlated (`v_stopatr` with `v_rangeatr`, `v_atrpct` with `v_excursion`). So I shuffled
the R labels 1,000 times and re-ran the **identical 105-trial grid**, recording max|z| each time:

```
observed max|z| over the grid : 2.101
permutation null max|z|       : median 2.552   90th 3.202   95th 3.466   99th 4.126
family-wise p-value            : 0.860
```

**The observed best split is below the *median* of what pure noise produces on this grid.** The
correlation-aware threshold (3.47) is *stricter* than the analytic `free_t` (3.05), not more
forgiving. Both reject. This is the single strongest line in the file and it is the one I would put in
front of the account owner.

## 6. Out-of-sample — and here is where a filter would have fooled the desk

Split at bar **842** (2024-11-26), the midpoint of the tape by bar count.

```
H1 (bars 60..841)   n=207  mean +0.0676R
H2 (bars 842..1667) n=237  mean -0.0127R
```

Fitting the same 105-trial grid on **H1 alone** produces two variables that **clear free_t 3.05
in-sample**. Carried unchanged into H2:

| cut fitted on H1 | H1 n_keep | H1 mean_keep | H1 z | H2 n_keep | H2 mean_keep | **H2 z** |
|---|---|---|---|---|---|---|
| `v_hour` ≤ 13 (keep BELOW) | 169 | +0.193R | **+3.62** | 195 | **−0.095R** | **−2.01** |
| `v_stopatr` > 0.656 (keep ABOVE) | 165 | +0.209R | **+3.44** | 177 | **−0.105R** | **−1.72** |
| `v_stopatr` > 0.717 (keep ABOVE) | 146 | +0.272R | +3.71 | 164 | −0.089R | −1.26 |
| `v_hour` ≤ 12 (keep BELOW) | 155 | +0.210R | +3.14 | 176 | −0.117R | −2.09 |
| `v_atrpct` ≤ 64 (keep BELOW) | 146 | +0.200R | +2.47 | 193 | −0.083R | −1.70 |
| `v_trendwith` > −1.41 (keep ABOVE) | 145 | +0.205R | +2.40 | 153 | −0.021R | −0.13 |
| `v_sincesig` > 0 (keep ABOVE) | 161 | +0.173R | +2.33 | 195 | +0.027R | +1.03 |

**Sign agreement H1 → H2: 4 of 8.** A coin flip. And the two cuts that do keep their sign keep it
while the *kept* subset loses money out of sample (−0.095R, −0.105R), which is the worse of the two
failure modes: a filter can go on "separating" while the thing it selects is unprofitable.

**The reverse split is symmetric, which rules out the obvious objection.** Fitting on H2 and testing
on H1 also gives **4-of-8** sign agreement — and the variable H2 likes best among the hour cuts wants
the **opposite** direction:

| cut fitted on H2 | H2 z | H1 z |
|---|---|---|
| `v_hour` > 12 (keep **ABOVE**) | +2.09 | **−3.14** |
| `v_hour` > 13 (keep **ABOVE**) | +2.01 | **−3.62** |
| `v_trendwith` ≤ 5.265 | −2.28 | −2.49 |
| `v_rangeatr` ≤ 0.858 | −2.36 | −1.17 |

**The two halves of the tape disagree on the sign of the strongest variable in each of them, at |z|
above 3 in both directions.** On the full sample `v_hour ≤ 13` is **z +0.50** and `v_stopatr > 0.656`
is **z +0.62** — the halves cancel almost exactly. That is what a fitted parameter looks like.

**And the level shift does not explain it.** H1's mean is +0.068R and H2's is −0.013R, a gap of 0.08R.
The within-half separations being reversed are 0.5–0.7R. The sign flip is eight times too large to be
the two halves sitting at different baselines.

## 7. Side-stratified, since the desk has only ever traded shorts

| pool | n | mean | best split | z | free_t | verdict |
|---|---|---|---|---|---|---|
| SHORT | 182 | +0.0650R | `v_stopatr` > 0.717 keep ABOVE | +2.79 | 3.05 | **FAILS** |
| LONG | 262 | −0.0032R | `v_levelage` > 214 keep ABOVE | +2.60 | 3.05 | **FAILS** |

Stratifying by side does not create a survivor, and it is not free: it doubles the grid to 210 trials,
which raises the threshold to **3.27**. The SHORT-only best (2.79) is further from 3.27 than the
full-sample best is from 3.05. **Splitting the population to find a winner makes the winner harder to
believe, not easier.**

## 8. The combination, for completeness

ANDing the top three full-sample cuts: keep n=109 at **+0.171R**, drop n=335 at −0.023R, **z +1.30**.
On H2 alone the same combination gives keep n=57 at +0.238R, z +1.61. Both below every threshold in
this file, and a 3-way AND selected from 105 marginal cuts has an effective search width vastly larger
than 105 — the right threshold for it is higher than 3.05, not lower. **The `+0.171R` on 109 signals
is the most tempting number I produced and it is the one I trust least**, for exactly the reason agent
B found 27 times: it reads as evidence and is not traceable to anything that holds out of sample.

## 9. The predicate would reject one of the desk's two trades — again

The best full-sample cut (`v_closepos` ≤ 0.277) does this:

| trade | `v_closepos` | cut | verdict |
|---|---|---|---|
| bar 452 (pre-armed level, +1.895R) | 0.627 | 0.277 | **REJECTED** |
| bar 1337 (post-hoc level, +1.854R) | 0.080 | 0.277 | KEPT |

The desk's own three discretionary filters reject bar 1337; the best mechanical cut I could find
rejects bar 452. **Every filter anyone on this desk has proposed rejects one of the two trades it was
built to explain, and they do not agree on which one.** Two winners that no rule can contain jointly
are two winners that were not produced by a rule.

## 10. What this sample could and could not have detected

With sd = 1.313R and `free_t` = 3.05:

| population | n | SE(mean) | smallest detectable effect |
|---|---|---|---|
| whole | 444 | 0.062R | a mean edge of **+0.19R** per trade |
| half kept | 222 vs 222 | — | a keep-vs-drop difference of **+0.38R** |
| third kept | 148 vs 296 | — | a keep-vs-drop difference of **+0.40R** |
| fifth kept | 89 vs 355 | — | a keep-vs-drop difference of **+0.48R** |
| the desk's live record | 2 | 0.93R | **+2.83R** |

**Stated the way the desk needs it:**

> **No predicate survives at n = 444, and this sample could not have detected a per-trade edge below
> about +0.19R, nor a filter that separates by less than about +0.40R while keeping a third of the
> signals. The 2 live trades have a standard error of 0.93R and can distinguish nothing at all.**

The honest reading of the 444-signal population's **+0.025R** mean is therefore: consistent with
zero, and consistent with anything up to about +0.15R that this tape is too short to see. It is *not*
evidence of an edge, and it is *not* proof of no edge — it is a measurement too coarse to act on
either way. That asymmetry matters, because "we could not find it" is a weaker claim than "it is not
there," and only the weaker claim is supported.

## 11. Verdict, and the standing rule this file sets

**A pre-registered, falsifiable predicate for thesis 5 cannot be honestly built from this tape.** Not
because the candidate variables were badly chosen — several have sensible mechanisms, and
`v_closepos` is exactly the variable a discretionary trader would name — but because after counting
the 105 trials it took to find the best of them, the best of them is indistinguishable from what
shuffled labels produce, and the one cut that did clear the bar reversed its sign on the other half of
the tape.

**Therefore: no thesis-5 trade.** The desk's commitment was to take none until the predicate exists in
a file as a falsifiable statement. This file is the result of trying, and the statement it contains is
a negative one. The commitment is satisfied by *this* conclusion, not voided by it.

**Three things this file forecloses, so a later firing cannot reopen them by forgetting:**

1. **The 105 trials in §2 are spent.** Any future search over these variables and cut-points is a
   re-run, not a new test, and its threshold starts at 3.05 and goes up — it does not reset.
2. **`v_hour` and `v_stopatr` are specifically burned.** They are the two variables most likely to be
   rediscovered, because they are strong in each half of the tape. They are strong *in opposite
   directions*. Anyone who finds one of them again on a longer tape must reconcile §6 first.
3. **The `v_closepos` ≤ 0.277 cut is not a "lean".** It is the top of a 105-trial search at p = 0.86.
   Demoting a failed filter to a soft preference is how it gets traded anyway.

**What would change the answer:** more tape, and only more tape. To detect a +0.10R per-trade edge at
`free_t` 3.05 needs n ≈ 1,600 signals — roughly **3.6× the current population**, or about 6,000 more
bars at this signal density. The series has ~9,600 bars left. So the question is answerable, later,
without any new idea — and **that is the reason to keep advancing the cursor and stop taking the
trade**, rather than the reverse.

---

*Method note, against myself: I chose 15 variables and 7 quantiles before looking at any outcome, and
I am reporting the grid size rather than the winner's z first. But I chose the variable **list** with
the desk's brief in hand, which named about ten of them. That is not independent of the desk's
priors, and if a variable the desk had not thought of would have worked, this search would not have
found it. The negative result is a result about this list, on this tape, at this n — which is the
strongest form the claim can honestly take.*
