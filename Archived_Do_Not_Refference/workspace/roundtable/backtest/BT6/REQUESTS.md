# BT6 — sub-task requests

Shape per `PIPELINE.md` §3. Ids per `REGISTRY.md`: `BT6-REQ-<n>`.

---

## BT6-REQ-1 A warm-up guard on `vwap_bands`, and the radius it would move

- **Arose in:** burst 01/02, reproducing `R6-D1` and confirming `D45` as its
  mechanism.
- **The ask:** a board decision on whether `futures_agents/indicators/volume.py`
  should withhold the band (emit `None`) while an anchor group holds one
  observation — and if so, a sequenced re-measurement, because the change moves
  every frame at every timeframe.
- **Why it cannot wait / why it can:** **it can wait, and it should.** Nothing is
  blocked. I deliberately did not patch it: the guard is three lines and its
  consequences are not. Quantifying the radius first is what makes the decision
  possible, and the radius is now measured.
- **What it blocks:** nothing today. It gates any *forward* daily VWAP study,
  and it is the fix the three `xfail(strict=False)` tests in
  `tests/test_bt6_vwap_daily.py` describe — they turn `XPASS` the day it lands
  rather than breaking the build.
- **My estimate of its size:** the patch is **small**. The re-measurement is
  **large**.

### The radius, measured, so the decision is not taken blind

`[measured: backtest/BT6/code/vwap_daily_census.py, vwap_blast_radius.py]`

| what changes | how much |
|---|---|
| bars whose band-1 currently exists and would become `None` | **100%** of 1440m bars (2511 MGC, 1859 MES, 1859 MNQ, and 4008/1863/1863 in `data/archive`); 19.8–21.8% of 240m bars; 7.5–8.9% of 60m bars |
| conditions that would start abstaining instead of firing | all five `vwap` conditions, via their own `s.has(...)` guards — no condition code needs touching |
| `above_vwap` at 1440m | 92.4% → **0%** (MGC), 99.7% → 0% (MES) |
| `vwap_band_extension` at 1440m | 99.8–100% → **0%** |
| `vwap_band1_bounce` | 0% → 0% — **no change; it is already `VOID`** |
| stored rows that would have to be re-measured | **196 distinct strategies at tf=1440**, of which 59 are group VWAP (certain), 76 possible, 61 unaffected |
| evaluated populations that would change | **8,005 of 23,309** generated daily strategies (34.3%) across the three chronology ledgers |
| published rows affected | **2** (Report A's two daily VWAP rows, already R6's `A16`) + 4 Report D chronology statements |
| `StopKind.VWAP_BAND` | `stop_price` would hit its `return None` branch instead of the `min_stop_ticks` floor, i.e. trades would be **dropped** rather than mis-stopped. `EF5` measured that branch as never currently firing (0 of 11,182 MES bars), so this is a *new* behaviour, not a restored one |

**The direction of the change is smaller results, not different ones.** A guarded
`vwap_bands` makes every daily VWAP strategy take zero trades, which turns two
published rows from "degenerate" into "absent". That is more honest and it is
also a deletion, so it needs a decision rather than a commit.

**Two cheaper alternatives the board should see before choosing:**

1. **Guard the bands, keep the line.** `vwap` stays non-`None` (a one-bar VWAP is
   a well-defined number: the typical price); only `upper_*`/`lower_*` are
   withheld. `vwap_reclaim` and `vwap_proximity` keep working; the three
   band-reading conditions abstain. This is what
   `test_a_guarded_vwap_line_still_exists_when_its_bands_do_not` pins.
2. **Do not patch; refuse to report.** Add the per-condition firing census R6's
   `B23` restatement asks for, and have the harness decline to emit a row whose
   required group fired on every bar or on no bar. That changes no arithmetic and
   no stored number, and it catches `openinterest`, `profile` at 240m,
   OPENING_RANGE at 1h and `vwap` at 1440m with one mechanism.

I have no preference to argue and no authority to choose. Both are stated because
the request would otherwise read as "patch it", which is not what I am asking.

---

## BT6-REQ-2 `data/archive/MGC_1440m.jsonl` has a 10× scale break at bar 384

- **Arose in:** burst 01, using the archive's daily series as an independent-store
  replication of `R6-D1`.
- **The ask:** a `D<n>` from the manager, and a correction to `BRIEF.md`'s data
  policy, which says the archive "extends the span ~6,000 bars per symbol" and
  notes MGC daily reaches back to 2010 (4,008 bars) without noting that the first
  384 of them are on a different price scale.
- **Why it cannot wait:** `DISC2`'s 25-year-span programme rests on this store,
  and the whole point of that programme is that a longer span lowers the Sharpe
  needed to clear `free_t`. A 914% one-bar return inside the sample is not a
  span problem, it is a `D40` problem.
- **What it blocks:** nothing of mine — `R6-D1` reproduces identically on both
  stores and on either side of the break, because the collapse is a within-bar
  property. It blocks any *return* or *momentum* statistic computed from archive
  MGC daily.
- **My estimate of its size:** small to diagnose, medium to decide (the fix is a
  policy question: truncate, rescale, or exclude).

`[measured: python3 over data/archive/MGC_1440m.jsonl]`

```
index 383  2012-04-25  o=164.10 h=164.10 l=164.10 c=164.10  v=646
index 384  2012-04-27  o=1657.40 h=1668.00 l=1645.50 c=1664.80  v=570
```

- bars 0–383 (2010-10-04 → 2012-04-25): close range **131.70 – 188.90**
- bars 384–4007 (2012-04-27 → 2026-09-25): close range **1050.80 – 5318.40**
- **551 of 4,008 bars have `high == low`**; **355 have `volume == 0`**

Gold was ~$1,650/oz in April 2012, so the early segment is the same price divided
by ten, not a different market. `BRIEF.md`'s data policy verified archive-vs-`csv/raw`
agreement **at 60m only** and explicitly told us not to generalise it; this is that
warning coming true at 1440m.

Related and separately quantified: `csv/raw/MGC_1d.csv` itself carries **281
zero-range bars (11.2% of 2,511)** against 1 of 1,859 on MES and MNQ. That is not
a defect in the loader, but it is why `above_vwap`'s daily firing rate is 92.4% on
MGC and 99.7% on MES — and 99.9% on both once rangeless bars are excluded
(burst 01 §3.2). Any per-symbol daily comparison that does not condition on
`high > low` is comparing populations, not symbols.

---

## BT6-REQ-3 `require_alignment`'s no-arg `alignment()` call — verified harmless, and sized

- **Arose in:** burst 02, checking R6's claim rather than inheriting it.
- **The ask:** a `D<n>` for the forward hazard, with the size below attached, and
  a one-line guard: `passes` already receives `timeframe`, so
  `snap.alignment(timeframe)` is the whole fix.
- **Why it can wait:** **R6 is right and I verified it.** `alignment()` equals
  `alignment(primary_tf)` on **9,554 of 9,554** snapshots across the four
  published frames, and both studies that set the field take their population
  from `w2rank.population`, which filters `x.primary_tf == tf`. **Report D's
  `require_alignment ≥ 0.5` on MES 240m survives.** No retraction is owed.
- **What it blocks:** nothing now. It goes live the moment a study trades other
  than the lowest timeframe of its frame — which is precisely what
  `DEFAULT_EXECUTION_MAP` and every anchor/execution study construct.
- **My estimate of its size:** trivial to fix, small to re-verify.

`[measured: alignment() vs alignment(primary_tf), 60m base, frame [60,240,1440]]`

| primary_tf | symbol | `alignment()` differs | **gate verdict flips at ≥0.5** |
|---|---|---|---|
| 240 | MES | 84.4% | **16.3%** |
| 240 | MGC | 86.5% | **21.3%** |
| 1440 | MES | 84.4% | **33.9%** |
| 1440 | MGC | 86.5% | **39.5%** |

The gate admits or rejects the **opposite** bar on 16–40% of bars once the
precondition fails, so this is not inertness — it is a filter reading the wrong
timeframes. Worth a number because R6 correctly recorded it as harmless *today*
and the reason it is harmless is a coincidence of `FRAMES`, not a design.
