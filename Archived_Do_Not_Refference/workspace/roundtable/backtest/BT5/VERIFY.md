# BT5 — fidelity questions

One numbered question per thing I had to decide that could make `BT5-ALGO-1` stop being the thing R5
scoped. Asked in `msgs/BT5-01_R5_verify-ALGO-1.md`. **Status: ASKED. No number from ALGO-1 is
verified.**

---

## ALGO-1 — activity stratification (`R5_SCOPE §S2`)

| # | question | my choice | status |
|---|---|---|---|
| **Q1** | S2 says attach activity "at entry", but `Trade.entry_ts` is the **fill** bar, not the signal bar (`engine.py:290-295, :372`). Which bar does S2 mean? | the **signal** bar, one timeframe before `ts` — the bar whose statistics the strategy read, and the last one knowable at the decision | ASKED |
| **Q2** | Caveat 5 binds S2 to `MGR-T13`'s time-of-day norm, or to adopting one by assumption and saying so. Is the library's own `relative_volume(bars, 20)` the right norm to adopt? | adopted it, and said so | ASKED |
| **Q3** | I added a third axis S2 does not name: within-clock-bucket percentile rank (`TODRANK`). Inside "activity residualised on time of day", or a fourth question? | kept it, declared non-causal, asserted time-of-day neutrality (TV 0.019 vs RAW 0.734) | ASKED |
| **Q4** | I added a **bar-level** layer S2's "Answers" paragraph does not name. Inside S2, or is it S3 leaking in? | kept it — the mechanism is a statement about bars, and it needs no constructed bars so constraint 1 cannot reach it | ASKED |
| **Q5** | "Distance to invalidation": the dump has no stop distance (BT3 choice 9). Is `stop_mult × atr(signal bar)` — the **modelled** distance — an acceptable stand-in, and which distance did the original finding use? | modelled distance, labelled as such; explicitly refused `mae` because it conditions on the outcome | ASKED |
| **Q6** | 3.55–3.95% of `csv/raw` hourly bars have `volume == 0` and 593 trades were decided on one. Keep them in `RAW`, drop from `RELVOL`, tie-average in `TODRANK`? | that rule | ASKED |
| **Q7** | Caveat 6 says "count-match the strata". Bar-level matching (equal-count terciles per cell) with the permutation handling the within-strategy trade imbalance, or trade-level subsampling? | bar-level, no subsampling | ASKED |

**The three I think I could be wrong on: Q1, Q4, Q7.**

## Not fidelity questions, recorded so they are not mistaken for them

- **Routing.** `BOARD.md` re-filed S2 under `MGR-T13` held by R1 (ADJ-16c, `BOARD.md:78-82, :390`),
  and lists BT5's own recommended task as `MGR-T22` `[:191, :400]`. My dispatch assigned me S2. Raised
  with R5 and in my report; it is the manager's to settle, not a fidelity dispute (`PIPELINE.md` §4:
  "if you think the finding itself is wrong, that is a `REQUESTS.md` entry for the manager, not a
  fidelity dispute").
- **A prediction about S3**, recorded in `ALGOS.md` §"Would S2's answer have changed…" and marked
  inference rather than measurement, so it can be checked if S3 is ever run.
