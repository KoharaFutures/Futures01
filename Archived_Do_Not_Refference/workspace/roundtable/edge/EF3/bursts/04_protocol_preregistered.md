# EF3 burst 04 — the measurement protocol, pre-registered before any expectancy exists

**Written and on disk before `ef3_measure.py` was run once.** Nothing in this file was chosen
after seeing a result; where I later deviate I will say so in the burst that deviates.

## Harness

`EF3/code/ef3_session.py::SessionEngine`, which is now a **subclass of EF1's
`SessionWindowEngine`** adding one clause. Every fill convention, counter and audit is EF1's.
`enforce_session_gap=False` reproduces EF1 exactly, so the difference between us is one flag and
both readings are carried as arms. See `msgs/EF3-01_EF1_…` for the measured defect and
`code/ef3_session.py` for the rule as arithmetic.

**Verified on 400 live MES 60m all-hours strategies, 3,734 trades:** 0 violations under EF1's
`violations()` with **no carve-out**, max hold 21.0 h, zero holds above 22 h.
With `enforce_session_gap=False`: 3,717 trades, **43 `SPANS_WINDOW` violations**, max hold 71.0 h.

**Exit-reason mix on that probe** (this is why the flat's fill convention matters more than
anything else in the harness):

| exit | count | share |
|---|---|---|
| STOP | 1,595 | 42.7% |
| **SESSION_CLOSE (the 16:00 flat)** | **1,442** | **38.6%** |
| TARGET | 409 | 11.0% |
| BREAKEVEN | 288 | 7.7% |
| **TIME** | **0** | **0.0%** |

The zero confirms the arithmetic in burst 02: under a 22-hour cap the time stop cannot fire, so
every catalogue variation in `time_stop_bars` is measuring nothing in this cell.

## Windows

| window | bars | share | purpose |
|---|---|---|---|
| **IS** | `[0, 0.60n)` | 60% | **selection happens here and nowhere else** |
| **OOS** | `[0.60n, n)` | 40% | reported, never used to choose |

MES n = 11,287, MNQ n = 11,291, so IS ≈ 431 days and OOS ≈ 288 days. Walk-forward on top: 5
anchored folds, train `[0, t_k)` → test `[t_k, t_{k+1})`, `t_k` at 40/50/60/70/80% of bars.

## Gates, fixed now

1. **`G0` census** — a strategy carrying a VOID condition at its own binding is removed before
   ranking and never appears in a table. Burst 03: 1,110 on MES, 1,590 on MNQ.
2. **`G1` sample** — IS trade count ≥ **30**. The n ≥ 20 variant is reported as a sensitivity arm
   only. A profit factor of 1.8 over 18 trades is noise.
3. **`G2` sign** — IS expectancy in R > 0.
4. **`G3` control** — the row's own `placebo_random` **and** `placebo_shuffle` must both have lower
   IS expectancy in R than the row. `placebo_shift` is **excluded from every gate** because it
   leaks (D42) and is conservative-only; it is computed and reported beside the others as the
   leak's own measurement.
5. **`G4` out of sample** — OOS trade count ≥ 10 and OOS expectancy in R > 0. **This gate is
   applied after the IS ranking is fixed**, so it cannot select; it labels.

A row that fails `G4` is **reported with its failure**, not deleted. A strategy that fails out of
sample is a finding.

## Ranking

**Primary sort: IS expectancy in R.** Not profit, not profit factor, not Sharpe. Win rate and
payoff are reported side by side and never separately — they cancel, measured four times in this
programme (`BRIEF.md` rule 3).

No composite score. A weighted blend of expectancy, drawdown and t is itself a fitted object with
free parameters I would be choosing after looking, and it would let a bad row buy its way in on a
drawdown term. Durability enters as **gates**, which are falsifiable, not as weights.

Every row carries, per the dispatch: strategy id, group, timeframe, expectancy in R, win rate
**and** payoff, trade count, its placebo's expectancy, search size, threshold faced, forward-roll
outcome. Plus: profit factor, avg win, avg loss, max and average drawdown in R, Sharpe, Sortino,
max consecutive wins and losses, avg duration, avg MAE and MFE in R, and slices by session and
regime. **A row missing a control or a search size is not reportable and will not be handed over.**

## Deflation, stated per list

`free_t = sqrt(2·ln n)` with **n = the symbol's own population**, because a top 10 is chosen inside
one symbol: MES n = 6,022 → `free_t` **4.172**; MNQ n = 5,904 → `free_t` **4.167**. Span 1.968 yr,
sqrt = 1.403, so the required annualised Sharpe is **2.974 / 2.970**. Also quoted: the whole-search
n = 11,926 → 4.333, and `free_t = 1.177` for a single pre-registered hypothesis (Sharpe 0.839),
which **no row here has earned** because every row was selected from a search.

## The prior I am measuring against, stated up front

`RANKING_FINDINGS.md`'s MES/MNQ track is the worst of the four: best placebo ranked 1st in **12 of
16** cells, ≤3rd in 15 of 16, **96 of 160 top-10 slots were placebos**, and on **MES 30d/240m no
real strategy appeared in the top 10 at all**. One-sided p that reals beat placebos at the top was
never below 0.109 in any of the 16 cells. Walk-forward: selecting the IS top 10 beat its own fold
base rate in **4 of 16** folds. Parameter sensitivity at MES 60m: median fraction of siblings
positive **0.0**.

So the expected result is a short list or an empty one. **The placebo column is the most important
column in my table, and if it wins I will say it won.**

## And the thing that must appear in every conclusion

MES and MNQ are **one index complex**. They share **44 of ~9,250 rule sets at 60m (0.5%)** and
**108 of ~14,000 at 240m (0.8%)** (D14/D41). A rule set ranking on both is **one observation, not
two**, because the underlying is the same. My own census is a live demonstration: every VOID
verdict in burst 02 is identical on the two symbols, to the bar count in most rows. That agreement
is the same instrument answering twice, and it corroborates nothing.
