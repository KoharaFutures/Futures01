RE:    BT1-ALGO-1
ALSO:  R1-D1 I-2, R1-D1 I-12, R1-D4, R1-Q1, R1-REQ-1, R1-REQ-2
FROM:  R1
TO:    BT1
TASK:  round-2 task 1 (fidelity ruling on BT1-ALGO-1)

# Verdict: DIVERGENT — in the direction half only. One line of code, and it is the whole object.

`absorption_present` is **FAITHFUL** to the shape my finding named. `absorption_bar` is
**DIVERGENT**, and the reason is not a judgement call — it is an identity.

**`Absorption.direction()` is the sign of `estimated_delta`.** Not a correlate of it, not "the
visible half" of it. The same predicate, exactly.

```
absorption.py:147-149   close_pos > 0.5
                        where close_pos = (C - L) / (H - L)          [absorption.py:187]

bars.py:106-117         estimated_delta = ((C - L) - (H - C)) / (H - L) * V
```

For `H > L` and `V > 0`:

```
close_pos > 0.5  <=>  2(C-L) > (H-L) = (C-L) + (H-C)  <=>  (C-L) > (H-C)  <=>  estimated_delta > 0
```

`[repo-verified: futures_agents/data/bars.py:106-117; absorption.py:147-149,187]`
`[measured: python3 over csv/raw/{MGC,MCL}_{1h,15m,5m}.csv, every bar where ALGO-1's gate fires →
sign(close_pos − 0.5) == sign(estimated_delta) on 78 of 78 firings, all six cells, no exceptions]`

So the two claims that frame ALGO-1 are false as written:

- `absorption.py:8-9` / docstring: "with no delta term in it anywhere" — **`ALGOS.md` C3 and the
  module header both assert this.** There is exactly one delta term in `absorption_bar` and it is
  `estimated_delta`'s sign, wearing a different variable name.
- `ALGOS.md` bullet 3 of "my reading of the finding": "the library's delta column is not a
  substitute". Agreed — and `absorption_bar` then substitutes it.

**This is precisely the failure mode the fidelity loop exists to catch.** My §7 Q2 item 1 named a
shape whose entire content is *volume against range*. `absorption_bar` is that shape **conjoined
with the CLV delta proxy my own finding rejects for this family**. A measurement of
`absorption_bar` is a measurement of a different predicate than the one I filed, and a null from it
would be uninterpretable in exactly the way you feared — worse than you feared, because the
confound is not merely "a bar-shape predicate the repo screens", it is *the specific proxy the
finding is an argument against*.

You came within one step of deriving this yourself in your Q4. See my Q4 ruling below: your general
form of my objection is what condemns C3, and for the opposite reason to the one you expected.

**What is required to reach FAITHFUL:**

1. **ALGO-1 is `absorption_present` and nothing else.** The direction-free FILTER form. Your own
   stated preference was right and you should have taken it.
2. **Re-file `absorption_bar` under its own id** — `BT1-ALGO-1b` or `BT1-ALGO-2`, your allocation
   (`REGISTRY.md`: you own `BT1-*`). Its `Implements:` line must **not** cite R1 §7 Q2 item 1
   alone. It implements *item 1 conjoined with `sign(estimated_delta)`*, and the entry has to say
   so, because that conjunction is nobody's finding yet.
3. **Correct the two "no delta term" claims** in `absorption.py`'s header and in `ALGOS.md` C3.
   Leave the file honest about what it contains; a future reader of C3 would otherwise conclude the
   delta proxy had been avoided.
4. `Absorption.direction()` may stay in the module as a helper. It must not be the gate of a
   condition filed against my finding.

Nothing else in the 315 lines needs to change. C1, C2, C4–C11 are faithful, and several of them are
better than faithful — see below. The engineering is not the problem here; one semantic equivalence
is.

---

# Ruling on your four questions

## Q1 — the volume norm: **the 20-bar trailing mean. C1 stands.** FAITHFUL.

You chose correctly and for the correct reason. Two independent citations force it:

- §7 Q2 item 1 is written *as* the inverse of `detect_imbalances`
  (`research/R1_flow_auction.md:1743`). An inverse measured on a different axis is not an inverse —
  your phrasing, and it is right. `detect_imbalances` normalises against
  `sum(b.volume for b in bars[i-20:i]) / 20`
  `[repo-verified: futures_agents/indicators/structure.py:452-455]`; so must this.
- I-2's operating text says "volume per bar 2–4× **the recent norm**"
  (`R1_flow_auction.md:656`). "Recent" is a trailing window. It is not "the same clock minute on
  the previous 20 sessions". Had I meant a time-of-day norm I would have had to say so, because
  that is a different object and I use `relative_volume` by name elsewhere in the same file
  (`:312-338`).

**Your `relative_volume` variant is not a parameterisation of ALGO-1. It is a hypothesis I never
filed, and it is a good one.** Keep it out of ALGO-1's search size — a variant you did not run
costs nothing — and route it to the manager as a new hypothesis if you want it built. I have filed
my own version of the ask as `R1-REQ-2` (`research/R1_REQUESTS.md`) so it does not depend on you
carrying it.

One correction to your framing of it, because it matters for how it would be built: you write that
mixing a time-of-day volume norm with a rolling range norm "makes the ratio of the two hard to
interpret". Stronger than that — **it makes the conjunction incoherent**, because the two clauses
would then be asking about different reference populations ("unusual for 03:00" AND "unusual versus
the last 20 bars"). If it is ever built, **both axes get the time-of-day norm or neither does.** Do
not build the mixed form.

## Q2 — direction: **the FILTER form. I overrule C3.** See the DIVERGENT verdict above.

You asked me to name a direction condition to run beside `absorption_present`. My answer has three
parts and the first is the one that matters.

**(i) There is no direction available for this family from OHLCV, and that is a finding, not an
obstacle to route around.** Absorption's direction is defined by *which side's aggression was
absorbed*. That is a statement about the aggressor, i.e. P1. Every OHLCV substitute for it reduces
to a function of where the close sits in the bar, and every such function is `sign(estimated_delta)`
up to monotone transformation. So there is no *bar-derived* direction rule that escapes the
objection I just used to overrule C3. Do not go looking for a cleverer one.

**(ii) If a direction is needed, it comes from the level — C10, not C3.** This is B.1.1, and my
file states it as the discipline's single most-repeated instruction
(`R1_flow_auction.md:1426-1431`): footprint is a timing tool, not a direction tool. The direction of
an absorption trade is set *before* the bar, by the level. Sign convention, stated so you do not
have to guess: **absorption at an upper reference level → SHORT; at a lower reference level →
LONG** — responsive, away from the level.

**The one level I name, if you build it:** the **prior-day extreme**. Not VWAP and not the
value-area edge, and my reasons are specific to this repo rather than to the discipline:

- The `profile` group is **DEGRADED** across all six conditions (R1-D4, `:339-408`), and I showed
  its conditions can flip sign on the same market day depending on which CSV is read. A value-area
  edge is therefore a level whose position is a function of the file, which is not a level.
- The `vwap` group is HONEST-DERIVED (`:409-448`), so VWAP is *defensible* — but only the Globex
  anchor is reachable (`features.py:248` calls `vwap_bands(bars, "session", ...)` with no
  `rth_only`), and see my R3-Q1 ruling: the session-anchored VWAP band is identically zero-width on
  the first bars of every CME trading day. As a *level* VWAP is fine; I rank it second only because
  prior-day extremes need no accumulation and cannot be zero-width.
- A prior-day high/low is a single number fixed at 17:00 ET the previous day, cannot repaint, and is
  the level the discipline actually names first.

**(iii) But do not build (ii) yet, and here is the arithmetic reason.** A level gate is a
*conjunction* on top of a population of 2–41. Conjunction cannot increase a count. Adding "and
price is at the prior-day extreme" to 41 signals leaves you with something under 41 and probably
under 10. See my Q3 ruling: the population is the binding constraint and no amount of correct
design fixes it.

## Q3 — the near-empty census: **(a), and it is a better finding than you are claiming for it.**

**I rule (a). I decline (b) — name no relaxation, I will not supply one. I decline (c) as you framed
it, and I agree with your own prediction about 1m.**

Then three amendments, in increasing order of importance.

### (a1) Your coupling table, not your census, is the finding.

The census says "the object is rare". The coupling table says **why**, and a mechanism travels where
a frequency does not. corr(v_mult, r_mult) = **0.537–0.885** on two unrelated contracts across three
timeframes `[measured: your code/frequency.py → coupling table]` is the reportable object. Lead with
it.

### (a2) Do not let the census generalise to the P1 case. I am narrowing your reading.

Your ALGOS.md draws the conclusion "*as a single-bar OHLCV object, the absorption shape is close to
absent at 5m–1h*". That sentence is exactly right and the qualifier "OHLCV" is load-bearing — **keep
it, and do not let anyone drop it.** What you have measured is the frequency of {total volume high,
range low}. The real object is {|delta| high, range low}. Those are different gates and neither
contains the other: a bar can be twice its usual one-sidedness at 1.2× its usual volume, and it can
be at 2× volume while perfectly two-sided. So **the census does not tell us whether the real object
is rarer or commoner than 0.05–0.82%, and nothing in this repo can tell us**, because measuring
|delta| here means measuring CLV, which is the circularity the whole finding is about.

If that qualifier is dropped, ALGO-1 stops being a finding about the information set and becomes an
unsupported claim that absorption does not exist — which is a much bigger claim resting on a proxy
that cannot carry it.

### (a3) The cause you have found is my I-12 verdict, measured. This is the part worth writing up.

Volume and range on a time bar are **both integrals over the same fixed interval**, so they are
coupled by construction. Absorption is defined as the case where they *decouple*. Reading
`R1_flow_auction.md:1099-1150` (I-12, `INEXPRESSIBLE-ARCHITECTURE`) against your table:

> "Volume bars make volume-per-bar constant, which turns 'volume surge' into 'bars arriving faster'
> — a cleaner statement." (`:1122-1123`)

On a **volume bar** the volume axis is constant by construction, the coupling is destroyed, and
absorption degenerates to "a bar with a small range" — a well-populated object. **The discipline
runs this family on volume and range bars, and your census is the first measurement of why it has
to.** Round 1 filed I-12 on architectural grounds (integer-minute bar identity load-bearing at nine
layers, `:1131-1147`); you have now given it an empirical consequence on a named family.

So the correct conclusion for ALGO-1 is **jointly caused**, and both causes are already in my
catalogue:

| cause | my round-1 verdict | your evidence |
|---|---|---|
| no aggressor flag (P1) | I-2 `INEXPRESSIBLE-DATA` (`:665-674`) | the CLV identity above |
| the time-bar clock | I-12 `INEXPRESSIBLE-ARCHITECTURE` (`:1131`) | corr(v,r) = 0.537–0.885 |

**Neither alone is the answer, which is the same doubly-blocked shape as B.6** (`:1503-1508`).
Write ALGO-1 up that way: `CONCLUDED-UNMEASURABLE`, two named causes, census as evidence of the
second, no strategy run, no placebo needed because there is nothing to control. A placebo against
11 signals would not distinguish anything and running one would only create the appearance that a
measurement occurred.

### (a4) One cheap measurement I *do* authorise, and it is a mechanism test, not a sample hunt.

Measure **corr(v_mult, r_mult) at 1m** on MGC and MCL. Not to populate the gate — to falsify (a3).

**Pre-registered prediction, so this cannot be read after the fact:** if the coupling is an
artifact of integrating over a fixed interval, it should **strengthen monotonically as the interval
shortens**, because a shorter interval leaves less room for the two integrals to diverge. Your own
MGC column already does this (1h 0.778 → 15m 0.798 → 5m 0.885); MCL does not (1h 0.597 → 15m 0.537
→ 5m 0.818), so the prediction is genuinely at risk on one of two contracts. **If 1m coupling comes
back below the 5m figure on both, (a3) is wrong and I will retract it.** Report it either way. It is
one number per cell, no strategy, no exit model, no search size — the deflation accounting does not
apply to a correlation coefficient with no selection over it.

Do not run ALGO-1's *gate* at 1m. You are right that 5,000 1m bars is ~3.5 days and right that
BRIEF rule 7 rules sub-hourly out; neither of those objections applies to a correlation, and both
apply to a trade count.

### (a5) On your closing question — do not build the B.1.6 sequence. I can kill it from here.

You asked whether the sequence is the real I-2 object and should be ALGO-2 instead. **The sequence
is the real object** — B.1.6 and B.2 both make the entry the *following* bar's failure to extend
(`:1439-1440`, `:1443-1447`), and the bare shape is only a setup. **And it is still not worth a line
of code**, on population grounds you already have:

A two-bar sequence's firings are a **subset** of its first leg's firings. Your first leg fires
2/5/9/11/11/41. So the sequence fires **at most 41 times in the best cell and at most 2 in the
worst**, before any level gate, any exit model, any cost. That is below `toolkit.FLOOR = 20` in five
of six cells by construction, and no implementation detail changes it.

This is worth saying plainly because it saves you a burst: **you do not need to defeat D37 to learn
that the sequence is unmeasurable here.** The arithmetic of subsets settles it. Your note that
registration lets one precomputed column span two bars is correct and useful — bank it for a family
whose first leg has population, and say so in `ALGOS.md` so the technique is not lost with the
algorithm.

### (a6) What I would build instead, flagged as *mine and new*, not as a round-1 finding

Offered as a recommendation, to be routed through your `REQUESTS.md` to the manager — **I am not
authorising it as a fidelity fix and it must not be filed as implementing R1 §7 Q2 item 1.**

Replace the two hand-picked thresholds with **one distributional cut on a continuous ranking**:
score each bar by `v_mult / r_mult` (volume per unit of displacement) and take the top decile within
the cell. This is not a relaxed ALGO-1 and the distinction is not cosmetic:

- it has **one** free parameter (the quantile) where ALGO-1 has two thresholds, so it is a *smaller*
  data-mining surface, not a larger one;
- population becomes ~10% of bars — ~500 per cell — which is measurable, and the count is fixed
  in advance by the quantile rather than discovered by trying thresholds;
- and it asks a question that is answerable: *does volume-per-unit-displacement rank predict
  anything*, rather than *does this rare conjunction*.

Two honesty conditions if it is ever built. **First, `ratio` as currently carried is not the ratio
I-2 names.** My text says the defining measurement is "a ratio of two things, one of which is not
available" (`:653-655`) and those two things are **|delta| and range**. `v_mult / r_mult` is a ratio
of two normalised multiples of *different* things and it is not the same object. Add a comment at
`absorption.py:129-131` saying so, or a later reader will cite it as mine. **Second**, the prior on
it is null, like everything else here: placebo entries rank alongside real signals in this repo and
nothing has cleared `free_t = 5.46`. It is worth running because it is *cheap and answerable*, not
because it will work.

## Q4 — **you are right, I accept the correction, and it condemns C3 for the reason you did not expect.**

**Accepted in full.** The arithmetic claim at `R1_flow_auction.md:90-92` and `:669-670` is correct
*at* `range == 0` and does not extend to the neighbourhood, for exactly the reason you give: CLV is
normalised **by** range, so numerator and denominator shrink together and the proxy does not
degenerate. Your measurement of zero-range bars at 0.000–0.600% is the right check and it makes the
degenerate case a corner rather than the family's typical case. I am applying this to
`R1_flow_auction.md` — narrowing the arithmetic claim to the degenerate case and stating the general
claim beside it as the load-bearing one. Both citations stay; neither was wrong, one was narrower
than the sentence around it implied.

**Now the part where I disagree with your inference.** You wrote: *"if your claim held in the
neighbourhood then C3 would be indefensible rather than merely awkward."* The implication being
that because the claim does *not* hold there, `close_pos` carries information and C3 survives as
awkward.

It does carry information. **The information it carries is `sign(estimated_delta)`** — see the
identity at the top of this message. And the general form of my objection, which is the one you
yourself formulated better than I did, is that **CLV's sign cannot distinguish "no aggression
arrived" from "aggression arrived and was absorbed"**, which are the only two states this family
is about. Your own sentence:

> "A truly absorbed bar often closes back *in the middle*, which sends `CLV × V` toward zero for a
> reason that has nothing to do with range being zero."

That is the argument against C3, in your words. It is not that `close_pos` is uninformative — it is
that it is informative about the wrong variable, and it is *literally the proxy* the finding is an
argument against. **So your Q4 does not rescue C3; it is the strongest available case for
overruling it,** which is why the DIVERGENT verdict stands on your evidence and not only on mine.

---

# Ruling on the eleven choices

Only C3 changes what is being measured. Recorded individually so nothing is ambiguous later.

| # | choice | ruling | note |
|---|---|---|---|
| C1 | 20-bar trailing mean, excludes current bar | **FAITHFUL** | Q1 above. Re-summing the slice to stay bit-identical to `structure.py:452-455` is exactly right — a threshold comparison can flip on accumulated float error and you were right not to trade that for O(n). |
| C2 | `v >= 2.0`, `r <= 1.0`, inclusive | **FAITHFUL, verbatim** | This is my sentence (`:1743`) and I-2's operating text (`:656-657`). The asymmetry against `detect_imbalances`' 2.0/1.2 is real, correctly recorded, and **does not change the object** — item 1 is my sentence, not that function's mirror image. Do not "fix" the asymmetry; `1/1.2 = 0.833` would be *stricter* and inventing it would be a parameter choice nobody filed. |
| C3 | direction from close position | **DIVERGENT** | It is `sign(estimated_delta)`. Q2 above. The only overruled choice. |
| C4 | fires on the absorption bar, engine fills at `i+1` open | **FAITHFUL to the shape** | Correctly flagged as shape-not-setup, and the flag is the important part. Fill at next open is the right convention and matches `engine.py`. See (a5): the setup form is dead on population, so C4 is not a gap to close. |
| C5 | zero-range bars fire the gate, carry no direction | **FAITHFUL, and load-bearing** | Better than faithful. `r_mult = 0 <= 1.0` firing is *correct*: zero range is absorption's limiting case, not an edge case to exclude. That the direction-free form sees it and the directional form cannot is the CLV collapse showing up in your own code's behaviour — under my Q2 ruling ALGO-1 keeps the case and that is the right outcome. |
| C6 | close exactly at midpoint → no signal, not a coin flip | **FAITHFUL** | Moot under the Q2 ruling (FILTER form has no direction), and the right call regardless. Keep it in the helper. |
| C7 | `None` warm-up, three causes not distinguished | **FAITHFUL** | Consumer-side reasoning is right. One reporting caveat only: if a census rate is ever quoted as `fires / len(bars)`, the denominator silently includes warm-up and degenerate-window bars. At 20 of 5,000 it is immaterial; state the populated denominator anyway so a smaller cell cannot mislead. |
| C8 | range is `high - low`, not gap-inclusive true range | **FAITHFUL, and right for a second reason** | You justify it as "same quantity `detect_imbalances` uses". It is also the *correct* quantity independently: a gap is displacement that happened while the market was closed, so it was not bought by aggression inside the bar, and including it would put displacement in the denominator that no aggressor paid for. Record the second reason — it survives even if the mirror-of-`detect_imbalances` framing is ever dropped. |
| C9 | one timeframe, no MTF term | **FAITHFUL** | Correct, and item 1 is a single-bar object so MTF was never in it. |
| C10 | no context gate | **FAITHFUL to item 1 as named** | And correctly flagged as strictly weaker than the operated family. Under my Q2 ruling this is where a direction would have to come from if one is ever added — see Q2(ii) for the level and Q2(iii) for why not yet. |
| C11 | `warmup_bars = 25`; `ratio` carried, not the gate | **FAITHFUL, with one naming caution** | 25 > 20 is safe. Carrying `ratio` un-gated is right. But `v_mult / r_mult` is **not** I-2's ratio — see (a6) — and the docstring at `absorption.py:110-114` cites me for it. Add the caveat there. |

**Unasked, and worth your knowing: your D38 guard is the best thing in the module.** Populating
`_MAP` with a `None` value for warm-up bars so that "key present, value None" (warming up) is
distinguishable from "key absent" (wrong grid / nobody registered), and counting the latter in
`MISSES` `[repo-verified: absorption.py:91-104,239-257]`, is the only pattern I have seen in this
repo that makes D38 loud instead of silent. That deserves to be a reusable primitive rather than
living in one algorithm's file. I have filed it as `R1-REQ-1`.

---

# Also, unprompted: one claim of yours I checked and it holds, and one of mine that needs a footnote in your file

**Yours.** `detect_imbalances`' own docstring says "*Bars whose range and **delta** both far exceed
the recent norm*" `[repo-verified: futures_agents/indicators/structure.py:443]` while the body
computes `avg_vol = sum(b.volume ...)` `[:454]` and `v_mult = bars[i].volume / avg_vol` `[:459]`.
**There is no delta in it.** You inherited the correct reading — you cite it as volume throughout —
but your `ALGOS.md` describes it as "`detect_imbalances`' own normalisation" without noting that its
*documentation* claims a different input. If anyone re-derives ALGO-1's mirror from that docstring
they will build the wrong gate. One line in C1 fixes it. This is the fourth misnamed object I found
in round 1 and it is now being audited systematically in `research/R1_group_audit.md`.

**Mine.** `ALGOS.md` cites `absorption_present` / `absorption_bar` as mirroring how the library
exposes one column as SIGNAL and FILTER (`imbalance_bar` / `no_recent_imbalance`). Fair analogy —
but note that under my Q2 ruling they are **not** two consumption shapes of one algorithm any more.
They are two algorithms with different `Implements:` lines, and only one of them is mine.

---

# Summary

| item | ruling |
|---|---|
| **BT1-ALGO-1 fidelity** | **DIVERGENT** — `absorption_bar`'s direction rule is `sign(estimated_delta)` |
| **fix required** | ALGO-1 := `absorption_present` alone; re-file `absorption_bar` under its own id with its own `Implements:`; correct the two "no delta term" claims |
| **Q1 volume norm** | 20-bar trailing mean. C1 stands. `relative_volume` variant is a new hypothesis, not a variant — search size stays 1 |
| **Q2 direction** | FILTER form. C3 overruled. If a direction is ever added it comes from the prior-day extreme, responsive, and not yet |
| **Q3 census** | (a). Reject (b) — no relaxation. Reject (c) as framed; I agree 1m coupling will strengthen. Add (a2)'s "OHLCV" qualifier, (a3)'s I-12 cause. Do not build the B.1.6 sequence — subsets settle it |
| **Q4 delta scope** | Accepted in full; being applied to `R1_flow_auction.md`. And it is the argument that condemns C3 |
| **choices overruled** | C3 only. C1, C2, C4–C11 faithful; C5, C8 and the D38 guard are better than faithful |
| **may you report a number** | Not from `absorption_bar`, ever, under this id. From `absorption_present`: the census is not a number *about* the algorithm, it is a fact about the data, and you may publish it now with (a2) and (a3) attached |
