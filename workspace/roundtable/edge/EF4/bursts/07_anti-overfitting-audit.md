# EF4 burst 07 — the anti-overfitting audit: what was checked, and what was found

The EDGE_BRIEF requires that each of these be hunted for and the result stated. Here is each
one, what was done, and the answer. Two came back clean, three came back with numbers that
change how my rows must be read, and two are unfixable properties of the substrate.

| hazard | checked how | result |
|---|---|---|
| look-ahead bias / future-data leakage | full-pipeline prefix invariance | **clean, 5,274 comparisons, 0 mismatches** |
| repainting indicators | same test (a repaint changes on a prefix) | **clean by the same evidence** |
| unrealistic fills | same-bar target credit, tie resolution, gap accounting | **clean**, 3.5–4.2% same-bar targets, ties 100% stop-first |
| understated costs and slippage | reconstructed gross vs `Trade.gross_r`; thin-book share | **found: the repo's "gross" is already net of slippage**, and the dispatch's cost figure was commission-only |
| insufficient sample size | power bound per cell, trade-count ceiling per timeframe | **found and quantified: binding, and binding differently at 5m than at 30m** |
| data-mining bias | declared *n* before measuring; placebo beside every reported row; the selection test | **found: see burst 06** |
| parameter sensitivity | one fixed exit, never searched | **eliminated by design, not measured away** |
| survivorship bias | roll audit on the raw series | **unfixable property of the substrate; quantified** |

## 1. Look-ahead and repainting — clean, and this is the strongest result in the audit

`code/audit_lookahead.py` → `out/audit_lookahead.json`.

The ORB/ICT report states the reason this matters: *"Resampling cannot detect a bias whose
sign is always favourable. Only auditing the fill model can."* A +0.354R cluster at t = 5.19
in this repository survived a 60/40 split **and all three disjoint slices** and was a
look-ahead in the author's own code. Out-of-sample testing is blind to it.

The test that is not blind to it is prefix invariance: rebuild **everything** — `SymbolFrame`
features, the condition library, the engine, the session rule — on `bars[0:k]`, and require
every trade that closed strictly inside the prefix to be bit-identical to the same trade in
the full run. Any quantity computed from the whole series (a percentile over all bars, a swing
confirmed by later bars, a profile built from the future, a repainting pointer) makes the
prefix run differ.

`[measured: python3 code/audit_lookahead.py]`

| cell | prefix 40% | prefix 60% | prefix 80% |
|---|---|---|---|
| MGC 30m | 230 trades, **0** mismatched | 355, **0** | 441, **0** |
| MGC 15m | 350, **0** | 543, **0** | 693, **0** |
| MCL 30m | 242, **0** | 347, **0** | 455, **0** |
| MCL 15m | 367, **0** | 540, **0** | 711, **0** |

**Total: 5,274 trade comparisons across 12 prefix runs, 0 mismatches**, comparing entry
timestamp and price, initial stop, exit timestamp, price and reason, gross R, net R, MAE, MFE
and risk points, at 1e-9 tolerance on floats and exact equality on timestamps and reasons.

A clean pass is not a proof of no look-ahead — a bias that is a *function of the bar only*
would pass — but a failure would have been a proof of one, and **this pipeline has never been
checked this way end to end.** EF1's `prefix_invariance_report` checks the bar
*classification*; this checks the whole stack including the feature builder, which is where
the repo's known repainting risks live.

## 2. Fill model — clean, and it is pessimistic in the direction it claims to be

`code/audit_fills.py` → `out/audit_fills.json`. On Track A trades:

| cell | trades | same-bar TARGET credit | entry bar touched **both** stop and target | stop won the tie | stop exits with **zero** slippage | stop exits filled **worse** than the stop | mean adverse fill |
|---|---|---|---|---|---|---|---|
| MGC 30m | 597 | 21 (3.5%) | 6 | **6 / 6** | **0** | 344 | 0.0196 R |
| MGC 15m | 901 | 38 (4.2%) | 4 | **4 / 4** | **0** | 562 | 0.0280 R |

The comparison that matters: the bug the ORB report found had **51% of its winners hitting
target on the entry bar.** Here it is 3.5–4.2%, which is what a 1.5R target legitimately does
inside one bar whose range reaches 1.5 ATR. Every same-bar tie was resolved stop-first, as
`FillModel.stop_before_target_in_same_bar` claims. No stop exit filled at the level with zero
slippage. 58% of stop exits filled *worse* than the stop, averaging 0.02–0.03R of extra loss
— the gap-honest branch working.

## 3. Costs — understated by the repo's own reporting convention, and by the dispatch's figure

Two separate findings, both in burst 02:

- **`Trade.gross_r` is not gross.** The engine charges slippage into the *fill price*
  (`engine.py:352`, `:414`) and commission as dollars in `_close` (`:494-499`). So
  `net_r − gross_r` is the commission alone, and any row quoting `gross_r` as "gross"
  understates the true gross by the whole slippage term — which in this cell is 1.5–3.5× the
  commission. Every gross figure EF4 reports is reconstructed from the fill geometry.
- **The dispatch's "15.0% of R at 5m" is commission-only.** My commission-only figure for the
  same configuration (MCL 5m, 0.5 ATR) is 14.1%, confirming the provenance. The **all-in**
  figure is **33.7% in RTH and 53.2% thin**. Direction right, magnitude 2.4–3.8× too small.

And the thin-book regime is the normal case, not the exception: **76–78% of this cell's bars
are outside the contract's own RTH**, so `thin_book_extra_ticks = 1.0` applies to three
quarters of trades. That is a direct consequence of the 18:00→16:00 rule and it has never
been priced in this repository, because no prior run traded those bars.

## 4. Parameter sensitivity — removed by construction rather than measured

One exit geometry for all 19,188 arms in both tracks (burst 05). The repo's own catalogue
offers 11 geometries; sweeping them would multiply *n* by 11 and add ~1.2 t-units to the
threshold, for an axis BRIEF rule 3 says does not move expectancy anyway. **A sensitivity
test on a parameter that was never searched is not needed; declaring that it was never
searched is stronger than passing one.**

The one parameter that *is* forced rather than chosen is the stop floor. `min_stop_ticks`
silently widens any stop below 25 ticks (MGC) / 15 ticks (MCL)
`[repo-verified: base.py:313-314]`, and 0.5 ATR at 5m is below both. **So a "0.5 ATR" arm at
5m in this repository is not testing 0.5 ATR** — it is testing the floor, and nothing warns
you. Choosing 1.0 ATR sidesteps it; the finding stands for anyone who does not.

## 5. Survivorship / roll bias — an unfixable substrate property, now quantified

`yahoo.py` applies `auto_adjust=False` and contains **no roll handling of any kind**; its own
header warns that `MNQ=F` is not `MNQ1!` because of roll convention. That is **D40** wearing a
new instrument. On this 58-day window the effect is small but it is not zero.

`[measured: code/audit_fills.py]` MGC: median |open[i] − close[i−1]| = **0.1997 points = 2
ticks**; bar-to-bar discontinuities above 4× that median number 73 at 5m (0.65% of bars),
51 at 30m (2.7%). Clustered by ET hour at **18:00 (22–23 events)** — the session reopen, which
is expected — and at **00:00 (17–18 events)**, which is not a session boundary and is worth a
caveat rather than a theory.

Series contiguity, MGC 5m `[measured: gap census over data/archive/MGC_5m.jsonl]`: the only
recurring hole is **16:55 → 18:00 (65 minutes, 29 occurrences)** plus weekends (2,955-minute
holes, 7 occurrences) and **one** anomalous 16:55 → 00:00 hole and **one** missing 5m bar at
07:15. So the series is essentially contiguous and the 17:00–18:00 break is the real
maintenance window — the programme's rule is one hour stricter than the exchange's.

**A median 2-tick discontinuity between one bar's close and the next bar's open is itself a
finding about every backtest in this repository**, because the engine fills entries at
`bar.open` after computing the signal on the previous close. That 2 ticks is not slippage and
is not in the cost model; it is the price of acting on a closed bar, and whether it is
*biased* against the signal is measured in `code/audit_adverse_selection.py`.

## 6. D48 caught two real collisions in EF4's own code, in two different places

The arm-id uniqueness assertion is not decoration. It fired twice on work that looked correct:

**(a) In the direction control.** `code/selection_direction.py` drew a random-40 comparison group
from the same universe as the top 10 and the two overlapped: *1 collision*. Without the
assertion one arm would have appeared in both the treatment and the control group and their
difference would have been computed against itself.

**(b) In the placebo construction, and this one would have invalidated every control in the
study.** `Strategy.strategy_id` hashes `"|".join(sorted(c.label for c in self.conditions))`
`[repo-verified: base.py:606-623]` and `Condition.label` is just the condition's name
`[repo-verified: base.py:154-155]`. My first placebo named its condition `placebo_s{seed}` — so
**every base arm sharing a filter set collided with every other at the same seed: 400–540
collisions per cell.**

```
AssertionError: placebo MGC 30m: 460 arm-id collisions, e.g. ['MGC-30m-b79bbe6ada89', ...]
AssertionError: placebo MCL 30m: 540 arm-id collisions
```

Each cell's ~700 placebo arms would have collapsed to ~20 distinct `BacktestResult`s shared
across all 35 real arms, and every "real vs placebo" comparison would have been made against a
control belonging to a different strategy — **with no symptom whatsoever**, because the
collapsed results still contain plausible trades and plausible expectancies. Fixed by keying the
placebo condition name on `(base arm id, seed)`.

**This is the D48 mechanism in a place the D48 audit did not look.** The programme's scope
correction checked nine `dataclasses.replace` call sites on a `Strategy` and found all nine
passing `_id=None` — mine did too. **Passing `_id=None` is necessary and not sufficient:** a
fresh id is still a *colliding* id when two different strategies hash to the same condition
labels. The guard that catches it is the uniqueness assertion at emission, not the `_id=None`.

## 7. Harness-revision stability: EF1 changed `session_window.py` mid-study and my numbers did not move

While EF4's runs were in flight, EF1 added a `session_end_indices` mechanism (a forced flat on
the last bar of a trading day, to close the flat-unreachability gap `EF2-02` and `EF3-01`
reported) and briefly shipped it with a missing `trading_day` import, which crashed one of my
placebo cells. Once it was importable I re-ran MGC 15m Track A against the new version and
compared to the old:

```
A1_ON_SWEEP   now n=50  E=-0.3167   then n=50  E=-0.3167   dn=+0  dE=+0.0000
A2_PD_SWEEP   now n=140 E=-0.1193   then n=140 E=-0.1193   dn=+0  dE=+0.0000
A3_VA_EDGE    now n=79  E=-0.0320   then n=79  E=-0.0320   dn=+0  dE=+0.0000
A4_VWAP_BAND  now n=330 E=-0.2171   then n=330 E=-0.2171   dn=+0  dE=+0.0000
A5_ORB        now n=201 E=-0.1292   then n=201 E=-0.1292   dn=+0  dE=+0.0000
A6_ON_COMPR   now n=101 E=-0.2584   then n=101 E=-0.2584   dn=+0  dE=+0.0000
new counters: flats_forced_session_end = 0, bars_session_end = 0
```

**Identical to four decimal places, and the new branch never fires.** That is the predicted
consequence of §1a: the flat is reachable in 41 of 41 cycles in all six of my cells, so a fix
aimed at unreachable flats is a no-op here by construction. It is also the cheapest possible
verification that an exact-zero difference is a *real* zero rather than a D48 collision — the
two arms were run in separate engine instantiations with separately built frames, not as two
arms of one `run_many`, so there is no shared-id path by which they could have collapsed.
