# E1 — reconciliation of the 442-vs-91 contradiction in agent C's work

Scope: read-only on `visible.jsonl`, `callouts.jsonl`, `NOTES.md`, `agents/*`. I re-derived
C's signal logic independently in a scratchpad script (logic copied verbatim from
`C_regime.py` so the counts are comparable) and I ran `C_regime.py` in place without editing
it. The harness was not run and no cursor was advanced. C's files are untouched.

**Tape-length caveat, read this first.** `visible.jsonl` is now **1,685 bars**. C ran against
**1,635 bars** (`C_substrate.md` line 3). Every count therefore shifts by the 50 new bars:
C's **442** is today's **444**, and C's **91** is today's **92**. The discrepancy the desk is
asking about is *not* a tape-drift artefact — 442 and 91 coexist at the same tape length —
but do not read 444≠442 as a contradiction of C.

---

## 1. What the 91 are: Tier B, a post-hoc narrowing — not a bug, not a mislabelled print

**The 91 is `C_regime.py`'s Tier B population**, produced by section 5 of the script
(lines 230–268). It is a strict subset of the 442/444 Tier A population, narrowed by three
additional filters. The script prints it under a correct and explicit header:

```
238  print("\n\n" + "="*72)
239  print("TIER B - DESK-FAITHFUL: trend-aligned, first-retest-only, break within 12 bars")
240  print("="*72)
...
253  print(f"  TIER B signals = {len(tierB)}  = 1 per {N/max(1,len(tierB)):.1f} bars of tape")
254  print(f"  by side: {dict(Counter(s['side'] for s in tierB))}")
```

The three filters are lines 242–252:

```
244      v, d = s["reg"]
245      if v == "WARMUP": continue
246      if s["side"] == "SHORT" and d != "DOWN": continue
247      if s["side"] == "LONG"  and d != "UP":   continue
248      if s["i"] - s["brk"] > 12: continue
249      ep = (round(s["L"], 2), s["side"])
250      if any(abs(e[0]-ep[0]) < 1e-9 and e[1] == ep[1] and s["i"] - e[2] < 48 for e in seen_ep):
251          continue
```

### The apparent "mislabelled print" is a splice made at read time, not by the script

The desk's brief quotes a single line reading
`EVERY TRADEABLE SIGNAL (442 resolvable) by side: {'SHORT': 34, 'LONG': 57}`.
**No such line exists in C's output.** It is two lines from two different sections joined
together:

- `EVERY TRADEABLE SIGNAL (444 resolvable)` — line 223, header of the **Tier A** dump. Correct.
- `by side: {'SHORT': 34, 'LONG': 58}` — line 254, the **Tier B** side split. Correct.

The give-away is the formatting: Tier A's side split (line 166) prints through `Counter(...)`
and renders as `Counter({'LONG': 262, 'SHORT': 182})`; only Tier B's line 254 wraps in
`dict(...)` and renders as a bare `{'SHORT': 34, 'LONG': 58}`. So `{'SHORT': 34, 'LONG': 57}`
can only have come from the Tier B block.

**Stated plainly: C's script labels both populations correctly. The 91 is not an artefact of a
mislabelled print, and it is not a bug.** It is a deliberate, documented second tier. The
defect is in the *reporting layer*, covered in §2.

### Nor is it the Tier A dedup

`C_regime.py` does have a deduplication step, lines 146–152, one signal per `(bar, side)`
keeping the nearest level. That is what takes 816 raw `(bar, side)` candidates — 1,612 before
it — down to the 816 that feed the desk-rule filter and then to 444 tradeable. It is *upstream*
of the 442 headline and is not the source of the 91.

---

## 2. Did C's report misrepresent its own artefact? Partly — by omission, in the lead

`C_substrate.md` is **internally honest**. It carries a side-by-side Tier A / Tier B table at
lines 216–237 with both counts, both frequencies and both means; it states the FLAT cells are
"empty by construction — the trend-alignment filter" (line 267); it prints both placebo rows
(lines 244–247); and its limitations section concedes "Tier A and Tier B are *two readings*…
the exact 91 is not [robust]" (lines 404–407). Nothing is hidden in the artefact.

The fault is in the **lead finding** (lines 16–21) and in the hand-back that quoted it:

> **The pattern the desk has traded twice is not rare — it is common, and it has no edge.**
> Under a desk-faithful mechanisation it fires **91 times** (1 per 18 bars) for a mean of
> **−0.113R** at 36.3% win, against a matched placebo of −0.020R (−0.75 placebo-sd).

This quotes only the narrowed tier, and it does so without naming it as the narrowed tier or
noting that the unnarrowed shape it was derived from has the **opposite sign** (+0.023R).
A desk reading only the lead learns the pattern loses money; the artefact's own table says the
bare shape makes money. Both are noise (§4) — but presenting only the negative one as *the*
answer is a selection the reader cannot see. **That is a misrepresentation by omission at the
summary layer, over an artefact whose body is sound.**

There is a second, sharper reason to distrust Tier B specifically: the script checks, at
lines 262–263, whether the filter set retained both known-winning desk trades —

```
262  print("  did Tier B keep the two real trades?",
263        {bi: any(s["i"]==bi for s in tierB) for bi in (452, 1337)})
```

— and it does (`{452: True, 1337: True}`). A filter set validated by whether it preserves the
two outcomes already known to be winners is tuned on the answer. C is transparent about the
intent, and its own counterfactual (line 300, Tier B minus the two desk trades) is exactly the
right correction, but it means Tier B's mean is **conditioned on retaining the sample's two
best-known trades** and cannot be quoted as an out-of-sample measurement of anything.

---

## 3. Real defects found in `C_regime.py` (none of them explain the 91)

**(a) Tier B's bars-per-signal uses the wrong denominator. Line 253 divides by `N`.**
Tier B structurally cannot fire on a WARMUP bar (line 245) or on a FLAT-trend bar (lines
246–247: SHORT needs DOWN, LONG needs UP, so FLAT admits neither side). Those are
263 + 301 = 564 of 1,685 bars, a third of the tape.

| denominator | Tier B frequency |
|---|---|
| whole tape, N=1685 (as printed) | 1 per 18.3 bars |
| eligible bars only, 1121 | **1 per 12.2 bars** |

"1 per 18 bars" therefore overstates the shape's rarity by ~1.5x. Tier A is barely affected
(the scan loop at line 124 starts at bar 60, so 1,624 scannable bars → 1 per 3.7 rather than 3.8).

**(b) Neither tier controls overlap, so neither headline frequency is a tradeable rate.**
The 444 Tier A signals sit on only **400 distinct bars: 44 bars emit a LONG *and* a SHORT
simultaneously** (e.g. bars 265, 266, 290, 292, 313, 314, 340, 360). Those 44 hedged pairs
cannot both be opportunities for a single-position desk, and as a group they are the worst
cohort in the sample (88 signals, mean −0.252R, win 26.1%). Beyond that, many trades run
concurrently inside one session. Walking the tape forward one position at a time:

| population | as printed | one position at a time |
|---|---|---|
| Tier A | n=444, 1 per 3.8 bars, +0.025R | **n=192, 1 per 8.8 bars, +0.008R**, win 37.5% |
| Tier B | n=92, 1 per 18.3 bars, −0.090R | n=76, 1 per 22.2 bars, −0.118R, win 34.2% |

**(c) Label/implementation mismatch in Tier B's dedup.** The comment at line 236 says
"**FIRST retest after a given break episode** only (level+break de-duplicated)", but the key
built at line 249 is `(round(s["L"],2), s["side"])` — `s["brk"]` never enters it, and the
48-bar window at line 250 is measured from the previously *accepted* signal, not from the
break. The implemented rule is "one signal per price level per side per 48 bars". Close in
spirit, but it is not what the comment claims and it is not break-episode-aware.

**(d) Latent crash, currently masked.** Line 255 calls `stats(tierB, ...)`, and `tierB` is
built from `tradeable` (line 242), not from `res_ok`. `stats` does `st.mean([s["r"] …])`. If
any tradeable signal were ever unresolvable, `s["r"]` would be `None` (line 170) and this
would raise `TypeError`. It survives only because `len(res_ok) == len(tradeable)` on this
tape — every signal resolves before the tape ends. A longer or truncated tape trips it.

**(e) The 442/444 headline itself is sound.** I reproduced C's pipeline independently and got
1,612 raw candidates → 816 after `(bar, side)` dedup → 372 rejected by desk rules → **444
tradeable, 444 resolvable, mean +0.025R, win 38.1%**, matching the desk's own independent
+0.023R / 38% on 442. No filter is applied silently after the headline; Tier B is announced.

---

## 4. Which population answers the question — and the number to quote

The desk's question, "how often was this pattern available and what did it earn", is answered
by **Tier A, not Tier B** — with the overlap correction from §3(b) applied.

**Why Tier A.** Tier A is the mechanisation of thesis 5 written from the two callouts' own
wording *before* outcomes were consulted; it is the population whose definition does not
depend on the answer. Tier B's three filters were selected and then validated against whether
they retained the two known winners (lines 262–263). A subset chosen that way measures the
filter, not the market. Tier B is also not an availability measure at all — it is a hypothesis
about what the desk *meant*, so it cannot answer "how often was the pattern available".

**The number to quote:**

> **Tier A, the pre-registered failed-retest shape: n=444 signals on 400 distinct bars over
> 1,685 bars = 1 per 3.8 bars of tape (1 per 4.2 distinct bars). Mean +0.025R, median −1.000R,
> win 38.1%, sum +10.98R, 118 targets / 254 stops / 72 session-closes.
> Side- and stop-matched random-entry placebo: −0.011R (400 trials, sd of trial means 0.061).
> Difference +0.036R = z +0.59, one-sided empirical p = 0.28. Hour-of-day-matched placebo:
> −0.018R, z +0.68. 95% bootstrap CI on the mean: [−0.097R, +0.146R].**
>
> **Tradeable as one book, one position at a time: n=192 = 1 per 8.8 bars, mean +0.008R,
> win 37.5%, sum +1.51R.**

**The finding is "no edge", and the sign is not part of the finding.** The CI straddles zero,
z is under 1, and the per-signal R's are not independent — grouping by level-episode gives 235
clusters, cluster-mean +0.126R, t = +1.62, still short of significance. The honest sentence is:
*the shape is common (roughly one firing every 4 bars of tape, one tradeable firing every 9)
and its expectancy is indistinguishable from a random entry of the same side and stop size.*

### Is the answer "both, for different questions"? Only in this narrow sense

- **"How often was this shape available, and what did it earn?"** → **Tier A**, above. This is
  the desk's actual question and Tier A is the only population that can answer it.
- **"If the desk's stated preconditions (trend-aligned, live break, first retest) are taken
  literally, does that narrowing rescue the shape?"** → **Tier B: n=92, 1 per 12.2 eligible
  bars (not 18), mean −0.090R, win 37.0%, placebo −0.015R, z −0.54.** The answer is no — the
  narrowing does not help and nominally hurts. Quoted *only* as "the desk's own stated
  conditions do not rescue it", this is a legitimate and useful result, and it is the one
  result Tier B is good for.

**Tier B's mean must never be quoted as the pattern's expectancy.** Beyond the tuning problem,
the two tiers are not statistically distinguishable from each other: Tier A − Tier B =
+0.115R with se 0.143, **t = +0.80**. The sign flip between +0.023R and −0.113R that prompted
this reconciliation is *entirely inside the noise of both samples*. Reading a regime story
into it would be reading noise.

Decomposing which filter produces the flip confirms that. Applied one at a time to Tier A:

| filter alone | n | mean | win |
|---|---|---|---|
| Tier A baseline | 444 | +0.025R | 38.1% |
| (a) trend-aligned only | 181 | −0.034R | 36.5% |
| (a′) counter-trend only | 140 | −0.102R | 32.1% |
| (b) first-retest-only | 207 | −0.003R | 37.2% |
| (c) break within 12 bars | 380 | +0.019R | 37.1% |
| (c′) break 13–24 bars | 64 | +0.061R | 43.8% |
| drop WARMUP only | 425 | +0.004R | 37.4% |
| Tier B (a+b+c) | 92 | −0.090R | 37.0% |

Filter (a), trend alignment, does most of the work — but its complement (a′, counter-trend) is
*also* negative, and worse. A split where both halves lose relative to the whole is a small-sample
artefact, not a regime effect. Nothing here supports treating the Tier A/Tier B gap as signal.

---

## 5. What the desk should change in the record

1. Quote the **Tier A** line from §4 as the answer to "how often, and what did it earn", with
   the non-overlapping n=192 figure beside it. Lead with "no edge, z < 1", not with a sign.
2. Correct C's lead finding #2 (`C_substrate.md` lines 16–21) to name Tier B as a narrowed,
   outcome-validated subset and to state the bare shape's +0.023R alongside it. The body table
   at lines 216–247 already says this; only the lead is misleading.
3. Replace Tier B's "1 per 18 bars" with **1 per 12.2 eligible bars** wherever it is quoted
   (`C_regime.py` line 253 and `C_substrate.md` line 221), or state the denominator.
4. Note the 44 both-sides-same-bar signals as a known defect of the Tier A availability count.
5. C's conclusion — *the two real winners are not evidence of an edge in this shape* — stands
   on Tier A as firmly as on Tier B, and should be restated on Tier A where it is not
   vulnerable to the tuning objection. Tier A shorts: n=182, +0.065R, win 37.9%; the desk's two
   trades are 2 of those 182 and 2 of 54 target-hits.

*No files other than this one were written. `C_regime.py`, `C_substrate.md` and all other
agents' artefacts are unmodified. Nothing committed.*
