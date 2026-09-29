# BT6 burst 02 — the blast radius of R6-D1, counted three ways

Continues `01_r6-d1-daily-vwap-collapse.md`. Burst question: **how many stored or
published results used a `vwap` condition at 1440m, and which templates require
the group?** Conservative by construction — R6 found 62% of published claims
survive everything, and over-retracting costs as much as under-retracting.

**Code:** `backtest/BT6/code/vwap_blast_radius.py`.
**Output:** `backtest/BT6/out/vwap_blast_radius.json`.

---

## 1. Which templates can reach the group — the structural answer

`[measured: python3 over futures_agents.strategies.combinator.TEMPLATES]`,
pinned in `tests/test_bt6_vwap_daily.py::test_vwap_is_the_required_group_of_exactly_one_template`.

| reachability | templates | consequence at 1440m |
|---|---|---|
| **`vwap` is REQUIRED** | **VWAP** (1 of 13) `[repo-verified: combinator.py:189-200 → required_groups=("vwap",)]` | every VWAP strategy holds a degenerate condition. There is no fallback: `_signal_pools` draws one condition from each required group and the pool is the five `vwap` conditions |
| **`vwap` is OPTIONAL** | TREND, PULLBACK, REVERSAL, OPENING_RANGE, LIQUIDITY, MEAN_REVERSION, MULTI_TIMEFRAME, VOLUME_PROFILE, FIBONACCI (9 of 13) | affected only when the draw lands on `vwap`; measured below |
| **cannot draw it at all** | BREAKOUT, MOMENTUM, SUPPLY_DEMAND (3 of 13) | unaffected, and this is the conservative anchor: a third of the taxonomy is untouched |

`vwap_proximity` is additionally an `optional_filter` of the VWAP template
`[repo-verified: combinator.py:198]`, and the VWAP template declares
`exclusive=(("above_vwap","vwap_proximity"),)` — which was decoration until the
filter-side check was added (`combinator.py:569-576` and its comment).

**One thing that is NOT a hazard, stated because it is the conservative
direction.** At 1440m `above_vwap` and `vwap_band_extension` are exact opposites
(burst 01 §3.1), and `Strategy.evaluate` returns `None` when two signals
disagree `[repo-verified: futures_agents/strategies/base.py:677-685]` — so a
strategy holding both would be zero-trade. **The generator cannot emit one:**
`itertools.combinations(range(len(optional)), n_opt)` picks distinct *groups*
`[repo-verified: combinator.py:538-541]` and no template lists `vwap` in both
its required and optional groups. **No published null is that artefact.**

---

## 2. Stored *rows* — 505 at 1440m, 196 distinct strategies

`[measured: PYTHONPATH=. python3 workspace/roundtable/backtest/BT6/code/vwap_blast_radius.py]`

197,083 result rows carry a timeframe field across `workspace/`, `scan_reports/`,
`reports/`, `research/`, `docs/` and `desk/`. By timeframe:

```
5m: 6,336   15m: 7,653   30m: 1,732   60m: 127,140   240m: 53,717   1440m: 505
```

**1440m is 0.26% of the stored corpus.** The 505 rows live in 22 files, and they
de-duplicate to **196 distinct strategy ids** — every one appears in at least two
files, because each `cells/*.json` row is also in its store's `all_rows.json`.
Anyone quoting 505 is counting the aggregates twice.

`[measured: de-duplication by `id` over the 22 files]`

| group | distinct ids at 1440m | reachability |
|---|---|---|
| MULTI_TIMEFRAME | 62 | possible |
| **VWAP** | **59** | **certain** |
| MOMENTUM | 57 | unaffected |
| TREND | 12 | possible |
| REVERSAL | 1 | possible |
| MEAN_REVERSION | 1 | possible |
| BREAKOUT | 4 | unaffected |
| **total** | **196** | 59 certain / 76 possible / 61 unaffected |

So **59 of 196 reported daily strategies (30.1%) certainly hold a degenerate
`vwap` condition**, 76 more may, and 61 cannot.

---

## 3. Evaluated *populations* — the number that actually matters, and it is exact

Rows understate the radius ~50× because a row must clear a trade floor. The
chronology study's daily ledgers record the full evaluated population, and I
reproduced each one **exactly** with the harness's own parameters
(`generate_strategies(sym, FRAMES[1440], groups=all 13, max_total=99999,
max_per_template=2400, seed=1)`, then `primary_tf == 1440`)
`[repo-verified: workspace/chrono/ledger.py:37-41]`:

| ledger | stored `strategies` | my reproduction | carries ≥1 `vwap` condition | carries `vwap_band1_bounce` |
|---|---|---|---|---|
| `chrono/ledgers/MGC_1440.json` | 7,875 | **7,875** ✓ | 2,653 = **33.7%** | **731 = 9.3%** |
| `chrono/ledgers/MES_1440.json` | 7,697 | **7,697** ✓ | 2,703 = **35.1%** | **730 = 9.5%** |
| `chrono/ledgers/MNQ_1440.json` | 7,737 | **7,737** ✓ | 2,649 = **34.2%** | **665 = 8.6%** |
| **total** | **23,309** | **23,309** | **8,005 = 34.3%** | **2,126 = 9.1%** |

The same generator call reproduces `bigscan`'s daily cells too: MGC 7,875 and
MES 7,697 match `screened` exactly; MNQ is 7,737 against a stored 7,733, a
0.05% difference I did not chase.

Which condition the draw lands on, MGC / MES / MNQ:

```
vwap_band1_bounce   731 / 730 / 665      <- VOID at 1440m
vwap_band_extension 708 / 661 / 657      <- the negation of above_vwap
above_vwap          660 / 693 / 662      <- sign(2C - H - L)
vwap_reclaim        554 / 619 / 665
vwap_proximity      108 / 111 / 105      (FILTER, never drawn without a vwap signal)
```

### 3.1 The 2,126 are confirmed zero-trade by the engine, not by inference

`vwap_band1_bounce` firing 0 times and a *strategy* taking 0 trades are different
claims, and only the second reaches a report. So I ran them.

`[measured: run_portfolio over csv/raw daily bars, the exact populations above]`

| MGC 1440m, 2,511 bars | strategies | trades | zero-trade |
|---|---|---|---|
| carry `vwap_band1_bounce` | 731 | **0** | **731 / 731 = 100.0%** |
| carry `above_vwap` | 660 | 11,014 | 466 = 70.6% |
| carry `vwap_band_extension` | 708 | 5,858 | 546 = 77.1% |
| carry `vwap_reclaim` | 554 | 6,977 | 444 = 80.1% |

MES: 730 carriers, **0 trades**, 730/730. MNQ: 665 carriers, **0 trades**,
665/665. The `above_vwap` arm is the control in the same run: it took 11,014
trades on the same bars with the same exits, so the zero is the condition and not
a broken harness.

**This is a sixth structurally zero-trade configuration**, to sit beside R1's
five (`research/R1_group_audit.md`), and it is the largest of them at daily
frequency: **9.1% of every daily population this programme has generated could
not take a trade**, silently, and its output is a null indistinguishable from a
measured absence.

---

## 4. Published claims — small, and R6 already found all of them

`[measured: grep -n "VWAP" scan_reports/*.md → 17 mentions in 2 of 4 reports]`

Only **two published rows** are VWAP at a daily timeframe, both in Report A's
per-timeframe table `[repo-verified: scan_reports/2026-09-23_MGC-MES-NQ_deep-scan.md:157-158]`:

```
| 1d | 9mo | MES MULTI_TIMEFRAME 74% n=27 e=+0.03 | MGC VWAP 2.1:1 w=33% e=+0.00 |
| 1d | 6mo | MES VWAP 52% n=33 e=+0.04 | MGC MOMENTUM 1.8:1 w=43% e=+0.02 |
```

These are exactly R6's `A16`, already graded `INVALID — measured nothing
(DEGENERATE)`. **I found no daily VWAP row R6 missed.** Report D's four VWAP
items (`D17`, `D24`, `D25`, `D26`/`D27`) are chronology statements over the daily
ledgers in §3, which R6 also reached. Reports B and C name VWAP zero times.

**So the published blast radius is 2 rows plus 4 chronology statements — and it
was already fully mapped.** The under-counted part of R6-D1 is not in
`scan_reports/`; it is in the 23,309-strategy substrate underneath it, and in
`D45`'s own wording.

---

## 5. `D45` should be restated, and here is the sentence

`D45` currently reads: *"`StopKind.VWAP_BAND` silently becomes `FIXED_TICKS` on
6–34% of bars"* `[repo-verified: msgs/06_manager_parent_defects-and-registry.md:22]`.
Three things are wrong with it as a general statement, and R6 is right that it
understates:

1. **It names only the stop.** The same zero-σ band is read by five *conditions*
   in a **required** signal group. The stop is the smaller half of the harm.
2. **The range is 1-hour-only.** 6–34% is R1's four 60m cells. `EF5` measured
   5–15% at 5m/15m/30m and 1.8–6.2% under `rth_only=True`
   `[repo-verified: edge/EF5/bursts/03_d45-vwap-band-at-scalp-timeframes.md]`;
   I measure 19.8–21.8% at 240m and **100% at 1440m**.
3. **Two different thresholds are being quoted as one.** R1's 6–34% is
   `|entry − band|·stop_mult + pad < min_stop_ticks·tick_size` — on MES that is
   5 ticks, not 1. R6-D1's is `half-width < 1 tick`, which is far stricter and
   gives 8.4% on the same MES 60m bars. **Both are correct and they are not the
   same measurement**, which is why the 60m numbers look inconsistent between
   the two findings. Any restatement must say which threshold it means.

Proposed restatement, for the manager who owns `D<n>`:

> **`D45`** — `vwap_bands` has no warm-up guard, so the volume-weighted variance
> of a one-observation anchor group is zero and band-1 collapses onto the VWAP
> line. The rate is **100% of 1440m bars** (every daily bar is the first bar of
> its trading day), 19.8–21.8% of 240m bars and 7.5–8.9% of 60m bars at a
> one-tick threshold; **6–34% of 60m bars** at the wider `min_stop_ticks`
> threshold the stop uses, and 1.8–6.2% of scalp-timeframe bars under
> `rth_only=True`. Two consequences, not one: `StopKind.VWAP_BAND` silently
> becomes `FIXED_TICKS`, **and** the `vwap` condition group — VWAP's *required*
> group — becomes a bar-shape group, with `vwap_band1_bounce` **`VOID`** at
> 1440m (0 fires, 2,126 of 23,309 generated daily strategies structurally
> zero-trade). Per (symbol, timeframe); nothing transfers.

---

## 6. `require_alignment` — R6's "harmless in every published cell" is verified

R6 flagged `StrategyFilters.require_alignment` calling `snap.alignment()` with no
argument `[repo-verified: futures_agents/strategies/base.py:433-434]` as a
forward hazard. I checked the harmlessness claim rather than inheriting it.

`alignment(from_tf)` skips `tf < from_tf` `[repo-verified: features.py:742-750]`,
and `passes` is called with `self.primary_tf` `[repo-verified: base.py:660]`. So
the no-arg call is identical to the correct call **iff** `primary_tf` is the
minimum of the frame.

`[measured: alignment() vs alignment(primary_tf) on every snapshot]`

| cell | identical | differ |
|---|---|---|
| MES 240m, frame `[240,1440]` — Report D's cell | **1347 / 1347** | 0 |
| MGC 240m, frame `[240,1440]` | **1348 / 1348** | 0 |
| MES 60m, frame `[60,240,1440]` | **5000 / 5000** | 0 |
| MES 1440m, frame `[1440,7200]` | **1859 / 1859** | 0 |

**Verified: harmless, on 9,554 of 9,554 snapshots across four published frames.
Report D's `require_alignment ≥ 0.5` on MES 240m survives.** The two studies that
set the field — `w2/mtf2.py:80` and `w2/mtf3.py:61` — both take their population
from `w2rank.population`, which filters `x.primary_tf == tf`
`[repo-verified: workspace/strategy_research/w2/w2rank.py:69-71]`, and build
`FRAMES[tf]` whose minimum is `tf`. So the precondition holds by construction in
both.

**And the hazard is large the moment it does not.** `SymbolFrame` refuses a
timeframe finer than its base series `[repo-verified: features.py:806]`, so the
hazard needs a 60m base with a coarser `primary_tf` — which is exactly what
`execution_tf` pairing and any anchor/execution study produce:

| 60m base, frame `[60,240,1440]` | bars | `alignment()` differs | **gate verdict flips at ≥0.5** |
|---|---|---|---|
| MES, `primary_tf=240` | 5000 | 4219 = 84.4% | **813 = 16.3%** |
| MGC, `primary_tf=240` | 5000 | 4324 = 86.5% | **1066 = 21.3%** |
| MES, `primary_tf=1440` | 5000 | 4219 = 84.4% | **1693 = 33.9%** |
| MGC, `primary_tf=1440` | 5000 | 4324 = 86.5% | **1977 = 39.5%** |

So it is not a cosmetic inertness: the gate admits or rejects the *opposite* bar
on 16–40% of them. Filed as `BT6-REQ-3`.

---

## 7. Where I stopped

- `futures_agents/` **unpatched**, per dispatch. `BT6-REQ-1` proposes the guard
  with this radius attached.
- `tests/test_bt6_vwap_daily.py`: **14 pass, 3 xfail, 0.29s.**
  `[measured: python3 -m pytest -q tests → **1029 passed, 7 xfailed, 0 failed**
  in 203s]`. Baseline before my file was **917 passed / 0 xfailed**; the rest of
  the growth is other agents' test files landing concurrently. **My 17 tests
  broke none of the others**, which is the condition the dispatch set.
- **One transient failure seen and chased down, recorded because a check that
  fails is the check working.** An intermediate full-suite run reported 3 failures
  in `tests/test_ef7_session_window.py::test_h2_no_trade_spans_a_holiday_eve_boundary[MGC|MES|MNQ]`.
  That file is **EF7's**, it was being written at the time (a 103-line append at
  04:41, another edit at 04:42), and it passes both in isolation (66/66) and run
  immediately after mine (80 passed, 3 xfailed). The final suite run is clean. So
  it was a mid-edit collection, not an interaction with BT6 — but it is EF7's file
  and EF7 should know a full-suite run caught its intermediate state.
- `check_ownership.py` → `ownership clean`. `check_refs.py` → `references clean —
  35 checked, every one resolvable`.
- Fidelity question to R6: `msgs/BT6-01_R6_verify-ALGO-1.md`. Until R6 answers,
  `BT6-ALGO-1` is `ASKED` and nothing above is a verified number.
