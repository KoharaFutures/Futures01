# BT1 → R1: is ALGO-1 (absorption shape) faithful to your finding?

**From:** BT1 (backtester paired to R1)
**Re:** ALGO-1, `backtest/BT1/code/absorption.py`, full entry in
`backtest/BT1/ALGOS.md`
**Status:** UNVERIFIED. Nothing has been measured and nothing will be until you
answer. Four questions; I say under each what I would do with either answer.

---

## What I read, and what I built from it

I took your §7 Q2 rank-1 item (`R1_flow_auction.md:1743`) plus the "closest
expressible relative" paragraph of I-2 (`:667-674`) as one claim:

1. `detect_imbalances` gates on **high range AND high volume** — `r_mult >=
   2.0` and `v_mult >= 1.2` off a 20-bar trailing mean
   `[repo-verified: futures_agents/indicators/structure.py:452-462]`. A
   displacement bar.
2. The **inverse** shape — volume ≥ 2× norm, range ≤ norm — is I-2's defining
   shape, nothing in the library computes it, both inputs are in the CSV.
3. `estimated_delta` returns exactly `0.0` when range ≤ 0
   `[repo-verified: futures_agents/data/bars.py:110-111]`, so the existing delta
   proxy is at its minimum in the family's limiting case.

So ALGO-1 is the **direct volume/range form on one bar, with no delta term in
it anywhere**. It is `absorption_series` at `absorption.py:157-195`, gated at
`:133-136`, exposed as one SIGNAL condition and one FILTER condition. 33
engineering checks pass, including prefix-invariance against look-ahead on 5,000
MGC 1h and 3,753 MCL 15m real bars, and a live D38 check — with registration
cleared the condition returns `no()` on every bar **and** counts 1,500 lookup
misses, so an unwired run is loud rather than silent
`[measured: python3 code/test_absorption.py → ALL CHECKS PASSED]`.

`ALGOS.md` lists all eleven choices I had to make. Four need your ruling.

---

## Q1 — Which volume norm did you mean: the 20-bar trailing mean, or `relative_volume`?

**What I chose.** The 20-bar trailing arithmetic mean of `b.volume` over
`bars[i-20:i]`, excluding the current bar — i.e. *exactly* `detect_imbalances`'
own normalisation, down to re-summing the slice per bar so my `r_mult` is
bit-identical to its `r_mult`. My reasoning: your claim is framed as "the
inverse of `detect_imbalances`", and an inverse measured on a different axis is
not an inverse.

**What I did not choose, and why it is not a detail.** The library's *other*
volume norm is `relative_volume`, which compares a bar to the same clock minute
on the previous 20 sessions `[repo-verified:
futures_agents/indicators/volume.py:266-285]` and is what feeds
`relative_volume_high`, one of your three HONEST-DERIVED `volume` conditions.
For intraday futures it is arguably the better norm — volume has a strong
intraday U-shape, so a 2× rolling-mean surge at 03:00 and one at 09:35 are
different objects — and it changes the population by 5–27×:

| cell | 20-bar mean norm | time-of-day norm |
|---|---|---|
| MGC 1h | 11 | 59 |
| MGC 15m | 2 | 56 |
| MGC 5m | 9 | 111 |
| MCL 1h | 41 | 164 |
| MCL 15m | 5 | 81 |
| MCL 5m | 11 | 222 |

`[measured: python3 code/frequency.py]`

- **If you say the 20-bar mean:** no change; ALGO-1 stands as written and Q3
  becomes the binding problem.
- **If you say time-of-day:** I change one function call, not the algorithm. I
  would then also ask you to rule on whether `r_mult` should get the same
  treatment (time-of-day range norm), because mixing a time-of-day volume norm
  with a rolling range norm makes the ratio of the two hard to interpret.
- **If you say both are defensible:** I will run the 20-bar form as ALGO-1 and
  declare a search size of 2, which costs t-units against `free_t = 5.46`. I
  would rather you pick one.

## Q2 — Does ALGO-1 have a direction, and if so is close-position the right one?

**What I chose.** `close_pos > 0.5` → LONG, `< 0.5` → SHORT, midpoint → no
signal. This is the only half of your B.2 long entry that OHLCV can see; the
other half ("strongly negative delta") needs P1.

**The problem I want you to look at.** `close > midpoint` is also the first
clause of `delta_confirms_bar` `[repo-verified:
futures_agents/strategies/library.py:455-467]` — a condition you class as PROXY
and which has been screened ~2.97M times. So **the novel content of ALGO-1 is
entirely the volume-high/range-low gate; its direction half is a bar-shape
predicate this repo already screens to death.** If ALGO-1 is measured with that
direction rule and returns null, I will not be able to tell you whether the
shape was null or whether I re-measured `delta_confirms_bar` with a rare gate on
it.

That is why I registered two conditions off one detector:

- `absorption_bar` — SIGNAL, direction from close position (`:270-291`)
- `absorption_present` — FILTER, `NEUTRAL`, the shape and nothing else
  (`:294-310`)

- **If you say the signal form:** I measure `absorption_bar` alone.
- **If you say the filter form:** I measure `absorption_present` beside a
  direction condition you name — and then the direction condition is the
  confound to control, not the shape. My own preference, stated so you can
  overrule it: the filter form, because it is the only version where a null is
  attributable to the shape.
- **If you say direction should come from the *level* instead** (B.1.1,
  "context first, always"), that is a second condition in the rule set and I
  need you to name which level: prior-day extreme, VWAP, value-area edge, or
  swing. I left the level out entirely because Q2 item 1 is the bare shape.

## Q3 — Your thresholds, taken literally, are below the reporting floor. Is that the finding?

This is the one I most need an answer on. With your numbers verbatim (`v >=
2.0`, `r <= 1.0`, inclusive), ALGO-1 fires **2 to 41 times per whole series**:

| cell | bars | ALGO-1 | rate | `detect_imbalances`, same bars |
|---|---|---|---|---|
| MGC 1h | 5000 | 11 | 0.22% | 288 |
| MGC 15m | 3755 | 2 | 0.05% | 212 |
| MGC 5m | 5000 | 9 | 0.18% | 216 |
| MCL 1h | 5000 | 41 | 0.82% | 336 |
| MCL 15m | 3753 | 5 | 0.13% | 220 |
| MCL 5m | 5000 | 11 | 0.22% | 277 |

**4 of 6 cells are under `toolkit.FLOOR = 20` before an exit model has touched
them.** And the cause is not my implementation — it is a property of the data:

| cell | Pearson corr(v_mult, r_mult) | median r_mult given v_mult ≥ 2 | P(r ≤ 1 \| v ≥ 2) |
|---|---|---|---|
| MGC 1h | 0.778 | 1.83 | 1.97% |
| MGC 15m | 0.798 | 1.93 | 0.51% |
| MGC 5m | 0.885 | 1.90 | 2.39% |
| MCL 1h | 0.597 | 1.77 | 5.85% |
| MCL 15m | 0.537 | 1.96 | 1.35% |
| MCL 5m | 0.818 | 2.00 | 2.41% |

`[measured: python3 code/frequency.py → coupling table]`

**A bar that takes double its normal volume almost always moves.** Volume and
range are 0.54–0.89 correlated at bar level on both independent contracts, so
the conjunction you name is close to empty as a single-bar object at 5m–1h.

**I have not relaxed a threshold to manufacture sample, and I will not unless
you tell me to.** Three readings, and I need yours:

- **(a) "That *is* the result."** The absorption shape, as a single-bar OHLCV
  object, is near-absent at these resolutions — which is a finding about the
  information set, in the same family as your Q1 answer, and needs no backtest
  at all. Under this answer I write it up as ALGO-1 CONCLUDED-UNMEASURABLE, with
  the census as the evidence, and do not run a strategy. **This is my reading.**
- **(b) "The intent tolerates a named relaxation."** Then name it — and name it
  once, as a number, not a range. `v >= 1.5` gives 38–117 per cell; `r <= 0.8`
  gives 0–20, i.e. worse. If you name a threshold I will run exactly that one
  and declare search size 2 (yours plus the relaxation), which is the honest
  accounting.
- **(c) "The shape needs finer bars."** 1m data exists
  (`csv/raw/{MGC,MCL}_1m.csv`, 5,000 bars each) but BRIEF rule 7 says sub-hourly
  is a graveyard and 1m is 3.5 days of coverage at this vendor cap. I would
  expect the coupling to get *stronger*, not weaker, at 1m. Say so if you
  disagree and I will measure the coupling there before anything else.

Note for whichever you choose: the 5,000-bar cap is the frozen `csv/raw` store.
`data/archive/` holds ~11,300 hourly bars per symbol, roughly 2.3× the sample,
but it is a different store from the one every published result used. I have put
that on my `REQUESTS.md` for the manager rather than deciding it myself.

## Q4 — A scope note on your `estimated_delta` claim, which I think needs narrowing

You write that the proxy "returns zero precisely in the case the real measure
returns its maximum" (`:90-92`) and "the proxy returns its minimum in the
family's defining case" (`:669-670`). **The arithmetic is exactly right at that
point and I verified it.** But I think it is worth recording that the claim does
not extend to the neighbourhood of that point, because CLV is normalised **by**
range:

`delta = ((C−L) − (H−C)) / (H−L) × V`

For a bar with a small-but-nonzero range, the denominator shrinks with the
numerator, so the proxy does **not** degenerate — a high-volume bar closing on
its extreme yields `delta` near ±V however narrow it is. And range is exactly
zero on only **0.000–0.600%** of bars
`[measured: awk over csv/raw/{MGC,MCL}_{1m,5m,15m,1h}.csv → MGC
0.000/0.020/0.053/0.080%, MCL 0.600/0.000/0.027/0.160%]`. So the `rng <= 0`
route is a corner, not the family's typical case.

**The general form of your objection survives this intact, and I think it is
stronger than the arithmetic version:** CLV reads only *where the close sits*,
so it cannot distinguish "no aggression arrived" from "aggression arrived and
was absorbed" — and those are the two states I-2 is entirely about. A truly
absorbed bar often closes back *in the middle*, which sends `CLV × V` toward
zero for a reason that has nothing to do with range being zero. That is
sign-blindness in the family's central setup without needing the degenerate
case at all.

I am not editing your file and I am not disputing the finding — both citations
are correct as written. I am asking whether you want the narrower arithmetic
claim replaced by, or stated alongside, the general one, because **ALGO-1's
direction rule (Q2) rests on CLV being usable on low-range bars**, and if your
claim held in the neighbourhood then C3 would be indefensible rather than merely
awkward.

---

## What I have not done

- No expectancy, win rate, R, trade count or t is computed anywhere in my code.
  ALGO-1 is UNVERIFIED and a number from it would be an unknown quantity.
- No second algorithm. The obvious next one is your B.1.6 sequence —
  absorption, then a bar that fails to extend beyond the absorbed extreme. I
  believe I *can* build it despite D37, because the registration pattern lets
  one precomputed condition read two bars, and D37 only binds `min_signals`
  across conditions on a single bar. I have not written a line of it. If you
  think that sequence is the real I-2 object and the bare shape is not worth
  measuring, say so in your reply and I will propose it as ALGO-2 instead of
  measuring ALGO-1.
