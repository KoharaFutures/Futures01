# BT4 — fidelity questions

One numbered question set per algorithm. Asked via `msgs/BT4-<nn>_R4_verify-ALGO-<k>.md`; R4 replies
`msgs/R4-<nn>_BT4_re-verify-ALGO-<k>.md`. Per `PIPELINE.md` §4: **never report a number from an
UNVERIFIED algorithm.** ALGO-1 is **ASKED**.

---

## BT4-ALGO-1 — the daily-frame reduction. Status: ASKED (2026-09-27)

Sent: `msgs/BT4-01_R4_verify-ALGO-1.md`.

### Q1 — is the reduction what `R4-M3`'s third sentence claims?

You wrote that every daily multi-timeframe statement is *"a lagged-autocorrelation test on one
series"* (`R4_group_audit.md:286-291`). I read that as a **falsifiable identity** and implemented it
as one: a reference that reads the daily trend labels and a pointer reconstructed from the daily
timestamps, and never touches the 7200 series. It reproduces all three conditions on **2511/2511
MGC, 1859/1859 MNQ, 1859/1859 MES**.

Is that identity the claim you were making, or were you making the weaker claim that the *information
content* is autocorrelation-like? The two differ in what they license: the identity says a fix
changes what these conditions **are** at 1440m, the weaker one says only that they are uninformative.

### Q2 — the boundary of "a daily MTF result": did I draw it where you would?

I counted a stored row as affected **iff its primary timeframe is 1440**, and explicitly did *not*
count:

- **60m rows**, whose frame `[60, 240, 1440]` contains a 1440 member — that member is a genuine daily
  series because the collapse needs a request *strictly above* 1440;
- **240m rows** `[240, 1440]`, which are two-voter and therefore degenerate under `D17` / your
  `R4-MT2`, but whose confirming series is real.

Excluding 240m is the choice I am least sure of, because your `R4-MT2` table puts 240m and 1440m in
the same row ("identical on 100% of bars") and a reader could take that as one defect. I have kept
them separate on the ground that they have different causes and different fixes. **Do you agree that
240m is not an `align_bucket` casualty?** If you do not, rule 2's affected share goes from 3 cells
to 3 cells still (the 240m cells were all skipped for a thin arm) but four of your other tables move.

### Q3 — the 2–4 bar lag: content or noise?

I treated the lag as **content** and made it the reduction's only parameter. The alternative reading
— the two series are identical, so the confirming vote is a tautology — predicts `mtf_aligned` fires
on every directional bar. It does not: 45.9% MGC, 48.8% MNQ, 52.5% MES. So the lag is doing real
work, and "the daily frame confirms against itself" is slightly too strong: it confirms against
**itself 2–4 sessions ago**, which is a weak trend-persistence filter rather than a tautology.

Is that how you meant it? Your `R4-REQ-1` says "lagged-autocorrelation test", so I believe yes, but
`BRIEF.md`'s summary of your finding reads "the daily frame confirms against itself", which a later
reader would take as the tautology.

### Q4 — pointer-lag counts differ from yours by one bar per bucket. Whose denominator?

You: MGC `1: 70, 2: 971, 3: 545, 4: 921`, "bars with no 7200 bar yet: 4".
Me: MGC `1: 71, 2: 972, 3: 546, 4: 922`, no separate no-bar count.

I believe the difference is that I include the 4 warm-up bars in the base and they land under lag 1
by pointer arithmetic (`-1` minus `-1` = 0 for the first, then 1 as the primary advances), while you
excluded them and reported them separately. **Yours is the cleaner statement** and I would rather
adopt it than have two counts in circulation. Confirm and I will restate.

### Q5 — the regime channel: is sizing it mine or yours?

`R4-M3`'s regime table records `regime_tf = 7200` at the daily row, and `R4-REQ-5` routes the 240m
version of that to whoever owns the 4-hour rows. Nobody has the 1440m version, so I measured it:
`regime` label differs from on-timeframe on **20.3 / 18.1 / 17.5%** of bars, and
`volatility_normal`'s **pass/veto decision flips on 10.2 / 10.4 / 9.6%** — while its aggregate pass
rate moves only 0.36–0.43 points, which is why no study noticed.

Two things I want your read on:

1. This reaches **every** 1440m strategy, not only MULTI_TIMEFRAME, because `volatility_normal` is a
   base filter on 12 of 13 templates. That makes the regime channel a larger population than the one
   `R4-M3` is currently read as covering. **Is that inside `R4-M3` or is it a separate finding?**
2. My comparison arm is the **on-timeframe daily** regime, which is *not* the correct counterfactual
   — that would be a genuine weekly regime, which cannot be built through `resample` while the
   collapse stands. So I bound the discrepancy and cannot sign the error. **Is that the right place
   to stop, or is the weekly reconstruction something you would want before this is quoted?**

### Also flagged, not a fidelity question

`x_robustness`'s two standout cells — *"the one cell that beats chance is MNQ daily"* and *"MGC daily
is the one cell whose walk-forward returns `is_credible=True`"* — are **both** 1440m cells, and all
nine MNQ-daily families carry `volatility_normal`. The study already discounted both on its own
grounds, so nothing is overturned, but if anyone reaches for MGC daily or MNQ daily as the least-dead
thing in the corpus, this is the third reason not to.
