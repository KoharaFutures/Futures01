# BT1 — sub-task requests for the manager's board

PIPELINE §3 shape. Appended as they arise; I keep working rather than stalling
on any of them.

---

## REQ-1 May a backtester measure on `data/archive/` rather than the frozen `csv/raw/`?

- **Arose in:** burst 01, building ALGO-1 (absorption shape) and running its
  frequency census
- **The ask:** rule on whether `data/archive/` (~11,300 hourly bars per symbol,
  ~2.3× the frozen store, newest bar 2026-09-25) may be used as the measurement
  substrate for a backtester's algorithm, or whether `csv/raw/` (5,000-bar
  vendor cap per file) is mandatory for anything that will be reported beside
  existing `scan_reports/` numbers.
- **Why it cannot wait / why it can:** **it can wait past ALGO-1's fidelity
  ruling, but not past its measurement.** ALGO-1 fires on 2–41 bars per
  `csv/raw` series `[measured: python3 code/frequency.py]`, i.e. below
  `toolkit.FLOOR = 20` in 4 of 6 cells. The archive is the only sample increase
  available that does not touch the algorithm's thresholds, so if the answer is
  "no", "rare signals are unmeasurable here" becomes a **structural** verdict
  rather than a threshold choice — and that is a different sentence to write
  down. Every rare-signal algorithm any of the three backtesters builds will hit
  this, so it wants deciding once.
- **The tension I cannot resolve from my side:** BRIEF says `csv/raw` "stays
  frozen for reproducibility" because it is the snapshot every published result
  was measured on, and also says the archive exists and is append-only. Both are
  true; which one a *new* measurement should use is a call about comparability
  with the existing corpus, which is the manager's, not mine.
- **What it blocks:** ALGO-1's measurement step, and the same step for any
  low-frequency algorithm. Not ALGO-1's fidelity ruling.
- **My estimate of its size:** small as a decision. Medium if the answer is
  "yes, but validate the two stores agree on their overlap first" — the
  archive's bar grid is a different vendor pull and would need a bar-for-bar
  reconciliation on the overlapping window before anything is measured on it.

## REQ-2 D37 has a partial workaround, and it should be written down before anyone else re-discovers it

- **Arose in:** burst 01, deciding whether ALGO-1 could include R1's B.1.6
  "failure to extend" confirmation
- **The ask:** record (as a note on D37, or wherever the manager routes defect
  corrections — I am not editing `DEFECTS.md`) that D37's "the combinator cannot
  express a sequence at all" binds the **template/`min_signals`** layer only,
  and that a **single precomputed condition can read as many bars as it likes**.
  The registration pattern already in the tree does exactly this
  `[repo-verified: workspace/newstrats/depth.py:159-175, 191-203;
  workspace/newstrats/freshness.py:164]`: a column is computed from the bar
  series, keyed by `(symbol, tf, ts)`, and the condition looks it up — so "A on
  bar i−1 and B on bar i" is one condition, one bar, and `min_signals` never
  sees the sequence.
- **Why this matters and why I am not just doing it:** R1 costs P9 (a sequence
  primitive) as **architecture** and says it blocks the operating form of five
  Class I families `[repo-verified: research/R1_flow_auction.md:1520 P9 row,
  and §7 Q3 note 3]`. That is right about the *combinator*. It is not right that
  a sequence cannot be **measured** here — it can, at the cost of one bespoke
  condition per sequence, with no template support and no ability to ablate the
  legs against each other. So the honest statement is narrower than "every
  ordered-chain idea is inexpressible": ordered chains are inexpressible *as
  confluences* and buildable *as single conditions*. If that distinction is not
  on the board, a later burst will either re-derive it or wrongly conclude a
  family is unreachable.
- **What it blocks:** nothing today. It changes what a *future* section can be
  scoped to attempt, and it is a correction to a defect note that three tracks
  are reading.
- **My estimate of its size:** small to record. The build it unblocks (ALGO-2,
  absorption → failure-to-extend) is small-to-medium and I have not started it.
