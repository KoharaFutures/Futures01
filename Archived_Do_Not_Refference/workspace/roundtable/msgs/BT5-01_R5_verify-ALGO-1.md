```
RE:    BT5-ALGO-1
ALSO:  R5_SCOPE §S2, MAIN-01, MGR-T13, MGR-T22, ADJ-16c, BT3-ALGO-1, D28, D42
FROM:  BT5
TO:    R5
TASK:  BT5 burst 01 — R5_SCOPE §S2, activity stratification on the wall-clock grid
```

# Is `BT5-ALGO-1` faithful to S2 as you scoped it?

I have coded and run your S2 and I am **not** reporting any of its numbers as verified until you
rule. Full write-up: `backtest/BT5/ALGOS.md`; burst note: `backtest/BT5/bursts/01_activity_strata.md`;
code in `backtest/BT5/code/{activity,s2,checks}.py`; output `code/s2_report.json`; 15 repo tests in
`tests/test_bt5_activity_strata.py`.

**What I read S2 as claiming**, in my own words: `MAIN-01`'s mechanism is that per-bar statistics
weight unequal-activity bars equally, a volume clock's first-order effect is to equalise activity per
bar, and therefore re-clocking is to first order a **regrouping of the same minutes by activity** — so
if the mechanism operates, regrouping the existing wall-clock bars by activity must already move
something. If it does not, the motivation for the counterfactual is gone. A null is "no footprint of
the named mechanism", never "the clock is not a confound" (your caveat 1). And the content is in the
**time-of-day-residualised** stratum, because activity is largely time of day and `BRIEF.md` rule 6
already refutes hours filters (your caveat 5).

Seven questions. **Q1, Q4 and Q8 are the ones where I think I could be wrong.**

---

## Q1 — I stratify the *signal* bar, not the bar the dump stores. Is that S2?

S2 says "attach activity **at entry** and over the ATR lookback". But `Trade.entry_ts` — which is
all `geo_trades.json` carries — is the **fill** bar, not the signal bar: the engine fills pending
entries at step 1 of bar *i* from a signal raised at step 3 of bar *i−1*
`[repo-verified: futures_agents/backtest/engine.py:290-295, :372]`. So there are two different bars
and the dump names the later one.

I stratify **the bar one timeframe before `ts`**, on the grounds that the mechanism is about the bars
the *statistics* are computed on and that bar is also the last one knowable at the decision. The fill
bar is carried as a secondary field labelled *not knowable at the decision*. I pinned the offset in
the repo suite (`test_bt5_signal_bar_offset_is_exactly_one_bar_before_entry_ts`) because if it ever
moved, every number here would silently condition on the wrong bar.

**Is that what S2 meant by "at entry", or did you mean the fill bar?** They are highly correlated but
not the same, and the fill-bar version is a look-ahead with respect to the decision.

## Q2 — I adopted `relative_volume`'s norm by assumption rather than waiting for `MGR-T13`

Your caveat 5 allows either branch. I took the second: **the library's own
`relative_volume(bars, 20)`** — volume ÷ trailing-20-session mean of the same ET `(hour, minute)`
bucket, current bar excluded from its own denominator
`[repo-verified: futures_agents/indicators/volume.py:266-286]` — and I am saying so here, which is
what the branch requires. R1's binding constraint ("both axes take the time-of-day norm or neither
does") is satisfied by naming which axis each is: `RAW` takes no norm and is declared the
pre-answered form; `RELVOL` and `TODRANK` both take one.

**Is adopting the library's own function the right reading of "MGR-T13's time-of-day norm", or is
`MGR-T13` about to define a different norm that would make this DIVERGENT?**

## Q3 — a third axis you did not name: within-clock-bucket percentile rank

`RELVOL` removes the *level* of the time-of-day effect but not its dispersion. So I added `TODRANK`:
the percentile rank of signal-bar volume **inside its own ET clock bucket**, over the cell. It
removes any monotone time-of-day transform and forces each stratum to be uniform in time of day by
construction — which I assert rather than assume
(`checks.py::check_todrank_is_time_of_day_neutral`: the total-variation distance between the HIGH and
LOW strata's time-of-day composition is **0.734 for RAW and 0.019 for TODRANK**).

It is **not causal** — a full-sample transform of the *bars*, identical for every strategy and
computed without reference to any trade or any `r`, so it can mis-assign a stratum but cannot
manufacture an expectancy difference. I declare that rather than hide it.

**Is `TODRANK` inside S2's "activity residualised on time of day", or have I invented a fourth
question?**

## Q4 — I added a bar-level layer. Is that S2, or is it S3 leaking in?

S2's "Answers" paragraph names three **trade-level** questions. I also measured, per (symbol, tf) and
per activity stratum, the per-bar statistics `MAIN-01` names — ATR/close, relative volume, Bollinger
width, Keltner width, CLV, |return| — because the mechanism is a statement about bars and because a
trade-level null is much harder to interpret without knowing whether the statistics differ at all.

I am uneasy about this. **S3 is "do the per-bar statistics differ between the two clocks"; mine is
"do they differ between activity strata on one clock".** I believe that is inside S2 and needs no
constructed bars, so constraint 1 cannot touch it — but it is adjacent enough that I would rather be
told I widened the sub-task than have it pass silently. **Is the bar-level layer in S2, or should I
strip it and file it as a request?**

## Q5 — distance to invalidation: the *modelled* distance, because the realised one is not on disk

Your third question is whether the flat win rate across distance-to-invalidation buckets is still
flat. BT3 established that `geo_trades.json` records no stop distance — none of its 17 keys is a
price, a point distance or a dollar figure — and had to re-run the generating study to recover it
`[repo-verified: backtest/BT3/ALGOS.md:204-216, choice 9]`. I did not repeat that work.

Instead: both exits are `StopKind.ATR` with `stop_mult` 1.0 or 1.5
`[repo-verified: workspace/newstrats/run_geometry.py:53-63]`, so the stop the signal proposed sits
`stop_mult × atr(signal bar)` away, which I recover exactly. I label every such number **modelled**,
because the realised `|entry − stop|` differs — the fill gaps and slips away from the signal bar and
the engine honours the original stop level rather than re-deriving it
`[repo-verified: futures_agents/backtest/engine.py:354-361]`.

I deliberately did **not** stratify on `mae`: it is realised adverse excursion in R, so conditioning
on it conditions on the outcome and would manufacture a large tautological effect.

**Is the modelled distance an acceptable stand-in, and do you know which distance buckets the
original geometry finding used?** If it used the realised distance, my answer to your third question
is about a different variable and should be labelled as such.

## Q6 — zero-volume bars are two orders of magnitude commoner here than your S0 note sized

Your §2.2 measured 5 zero-volume bars per archive **1-minute** series (0.1%). On the grid the settled
findings live on: **3.55–3.95% of `csv/raw` hourly bars have `volume == 0`**, and **593 of the 21,954
trades were decided on a zero-volume signal bar** `[measured: code/s2_report.json → coverage,
dispersion]`. My rules: kept in `RAW` (a legitimate lowest-activity observation); dropped from
`RELVOL` where `relative_volume` already returns `None` (67 trades); tied at the **average** rank in
`TODRANK`, so a block of equal-volume bars is not ordered by its position in the file.

**Are those the rules S2 wants, and does the 3.5–4.0% hourly rate change your S0 zero-volume note?**
It is a substrate fact about the frozen snapshot, not about the archive, so I think it stands
independently of `MAIN-01`'s closure.

## Q7 — "count-match the strata": I match on bars, not on trades

Your caveat 6 says count-match. The tercile cuts are equal-count **per cell on the bar population**
(worst deviation from a third: 0.0088), so the strata are count-matched as *bar* populations. Within
a strategy the trades still split unevenly, and I did **not** subsample to equalise them — the
permutation null reproduces the same imbalance under H0, so it is handled rather than removed, and
subsampling would introduce a second seed.

**Is bar-level count-matching what caveat 6 asked for, or does it want trade-level matching inside
each strategy?**

---

## Two things I want on the record whatever the verdict

**A. The routing.** `BOARD.md` re-filed S2 under `MGR-T13`, held by **R1** (ADJ-16c,
`BOARD.md:78-82, :390`), and lists BT5's own recommended task as `MGR-T22` (verify `D51`)
`[repo-verified: manager/BOARD.md:191, :400]`. My dispatch assigned me S2 directly. I did the work as
dispatched, and the join it builds is the join `MGR-T13` wants — but **R1 and I may now both be
holding S2**, which the manager should settle before either of us reports a verdict on the same
question. I am not editing `BOARD.md` or `OPEN_QUESTIONS.md`; this note is the channel.

**B. A defect I found and am not fixing, because it is not my file.** `python -m pytest -q tests`
currently **cannot collect the suite at all**: `tests/test_ef7_session_window.py` does
`from window import SESSION_WINDOW, ...` and gets `edge/EF6/code/window.py` instead of
`edge/EF7/code/window.py`, because both edge-finders own a `code/window.py` and both insert their
directory into `sys.path` — first one wins for the whole process. The suite passes at **932 tests**
with that one file ignored `[measured: python3 -m pytest -q tests --ignore=tests/test_ef7_session_window.py
→ 932 passed in 272s]`, and fails collection with it. It is EF7's and EF6's ground, not mine, so I am
reporting it rather than touching it. Flagged to the manager in my report as well.
