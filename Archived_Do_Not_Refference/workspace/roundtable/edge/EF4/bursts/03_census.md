# EF4 burst 03 — the firing-rate census for the six scalp cells

`code/census.py` → `out/census.json` (632 rows). All 79 library conditions × 8 cells:
MGC/MCL at 5m, 15m, 30m single-timeframe frames, plus a 5+15+30 group frame per symbol.
Substrate `data/archive/`. Run **before** any population was constructed.

## Verdict scale, and why NEAR_VOID is derived rather than chosen

| verdict | rule |
|---|---|
| `VOID` | 0 of N bars — structurally, not rarely |
| `NEAR_VOID` | < 30 fires: cannot reach the 30-trade floor every prior study here used |
| `THIN` | < 2% of bars |
| `LIVE` | ≥ 2% |

At 5m, 30 fires is 0.27% of 11,216 bars. `Strategy.evaluate` is a strict AND
`[repo-verified: base.py:670-684]` and the engine holds one position at a time
`[repo-verified: engine.py:231]`, so a strategy's trade count cannot exceed its rarest
condition's fire count. NEAR_VOID therefore means "cannot produce a reportable sample **in
this cell on this span**" — a statement about the cell, not about the condition.

## Headline

`[measured: python3 workspace/roundtable/edge/EF4/code/census.py]`

| cell | snapshots | VOID | NEAR_VOID | THIN | LIVE |
|---|---|---|---|---|---|
| MGC 5m | 11,216 | 4 | 0 | 7 | 68 |
| MGC 15m | 3,746 | 4 | 2 | 4 | 69 |
| MGC 30m | 1,875 | 4 | 4 | 1 | 70 |
| MCL 5m | 11,212 | 4 | 1 | 5 | 69 |
| MCL 15m | 3,744 | 4 | 1 | 6 | 68 |
| MCL 30m | 1,873 | 4 | 4 | 2 | 69 |
| MGC 5+15+30 | 11,216 | 2 | 0 | 7 | 70 |
| MCL 5+15+30 | 11,212 | 2 | 1 | 5 | 71 |

**Not usable, per cell (VOID ∪ NEAR_VOID):**

- MGC 5m (4): `mtf_aligned`, `mtf_strongly_aligned`, `oi_expanding`, `oi_price_confirmation`
- MGC 15m (6): + `fresh_zone_approach`, `post_news_window`
- MGC 30m (8): + `lvn_rejection`, `zone_touch`
- MCL 5m (5): + `lvn_rejection`
- MCL 15m (5): same as MCL 5m
- MCL 30m (8): + `fresh_zone_approach`, `session_extreme_sweep`, `zone_touch`
- MGC group (2): `oi_expanding`, `oi_price_confirmation`
- MCL group (3): + `lvn_rejection`

## The four answers the dispatch asked for

### 1. `openinterest` — VOID in 8 of 8 cells, 0 fires

`oi_price_confirmation` and `oi_expanding`: **0 / N in every cell**, at 5m, 15m, 30m and on
the group frame, on both symbols. The CSV header is `open_time,open,high,low,close,volume`
— there is no open-interest column, so `_oi_change` has nothing to read. Any strategy
carrying either takes **zero trades** in this cell, and its null is "the detector never
fired", not "we measured absence."

### 2. `profile` — **emphatically NOT dead at 5/15/30.** The 240m verdict does not transfer

Fire rate, all six profile conditions:

| condition | MGC 5m | MGC 15m | MGC 30m | MCL 5m | MCL 15m | MCL 30m |
|---|---|---|---|---|---|---|
| `poc_reversion` | 40.4% | 35.3% | 31.7% | 30.6% | 26.8% | 22.8% |
| `value_area_edge` | 1.95% | 3.28% | 5.23% | 1.88% | 3.07% | 4.00% |
| `value_area_breakout` | 48.8% | 47.6% | 44.8% | **61.4%** | 60.6% | 59.0% |
| `lvn_rejection` | 1.60% | 1.33% | 1.12% | **0.12%** | 0.32% | 0.32% |
| `away_from_hvn` | 77.3% | 71.6% | 69.5% | **83.9%** | 79.2% | 77.0% |
| `open_outside_value` | 20.4% | 20.0% | 18.2% | 26.5% | 27.4% | 26.5% |

The mechanism is why: every profile condition reads `s.prior_profile` — the **prior
session's** profile — and asks only whether the current close is near one of its levels
(`_profile`, library.py:935-939). It never needs the current bar to populate bins. R1's
"median bar touches 3 of 40 value-area bins" is a fact about *constructing* a profile from
coarse bars; it does not gate *reading* one. **So `profile` is DEAD at 240m for a reason
that does not exist at 5/15/30, and the correct verdict for my cell is CLEAN-to-LIVE for
five of six and NEAR_VOID for `lvn_rejection` on MCL (14, 12 and 6 fires) and MGC 30m (21).**

The caution is the opposite one: `away_from_hvn` (69–84%) and `value_area_breakout`
(45–61%) fire so often they are close to information-free gates. **A high firing rate is
not evidence of content**, and three of the six profile conditions are FILTERs in that
range.

### 3. `OPENING_RANGE` — resolvable, and this is where the 30-minute window should work

`code/or_resolvability.py` → `out/or_resolvability.json`. The scan report's rule is that an
L-minute range resolves on a T-minute frame iff `T | L` and `T | RTH-open-in-minutes`. MGC
opens 08:20 = 500 minutes (500 % 15 = 5, 500 % 30 = 20 → fails); MCL opens 09:00 = 540
(divisible by 5, 15 and 30 → passes). Measured:

| cell | rule-resolvable | days with an OR | OR width | first bar's minutes-since-open | bars in the OR |
|---|---|---|---|---|---|
| MGC 5m | yes | 41 | 30 min | **0** | 6 |
| MGC 15m | **no** | 41 | 30 min | **10** | 2 |
| MGC 30m | **no** | 41 | 30 min | **10** | 1 |
| MCL 5m | yes | 41 | 30 min | 0 | 6 |
| MCL 15m | yes | 41 | 30 min | 0 | 2 |
| MCL 30m | yes | 41 | 30 min | 0 | 1 |

**New finding, and it is not the defect the scan report found.** The report recorded a
30-minute range built **60 minutes wide** on MCL. That does **not** replicate at 5/15/30:
the width is exactly 30 minutes in all six cells. What fails instead is the *placement*:
`_build_session_state` accumulates RTH bars with `minutes_since_open < 30`
`[repo-verified: features.py:890-895]`, and on MGC's 08:20 open no 15m or 30m bar starts at
minute 0. So **MGC's "opening range" at 15m and 30m is minutes 10–40 after the open, not
0–30** — it excludes the first ten minutes of gold's RTH, which is the most active part of
it, and includes ten minutes that are not in the opening range at all.

Verdict: MGC 5m and all three MCL cells **CLEAN**; **MGC 15m and MGC 30m `DEGRADED` — a
30-minute window shifted 10 minutes late**, 41 of 41 days, on both the ORB and the fade
condition and on `StopKind.RANGE`, which reads `snap.opening_range.size`
`[repo-verified: base.py:301-306]`. MGC 30m is additionally a **one-bar** range, so
`opening_range_fade` (needs `bar.high > OR.high >= bar.close`) cannot fire until a later bar.

`opening_range_breakout` is LIVE everywhere (22.0–24.2%) and `opening_range_fade` THIN-to-LIVE
(2.6–6.8%). So the ORB study's negative applies to a cell where the condition genuinely fires
— which is what makes R6's "STANDS" audit binding on me rather than deferrable.

### 4. `StopKind.VWAP_BAND` (D45) — inputs present in every cell

`stop_price` reads `s["vwap_l1"]` / `s["vwap_u1"]` and returns `None` if absent
`[repo-verified: base.py:296-300]`. The vwap-band family fires everywhere in my cells —
`vwap_band1_bounce` 11.2–24.5%, `vwap_band_extension` 9.7–14.1% — so the band columns are
populated and a `VWAP_BAND` stop is *resolvable* at 5/15/30 on both symbols. Whether it is
an ATR band in disguise is R3-Q1's question and EF5 owns D45; I record only that it is not
VOID here, so a null from it would be a measurement rather than an absence.

## What the census removes from a population, before any search

The strict-AND means these counts are multiplicative, not additive. Per cell, the fraction
of the 79 conditions that cannot supply a reportable sample: MGC 5m 4/79 = 5.1%; MGC 15m
7.6%; MGC 30m 10.1%; MCL 5m 6.3%; MCL 15m 6.3%; MCL 30m 10.1%. **The 30m cells lose twice
as much of the library as the 5m cells**, entirely because fewer bars means fewer fires of
a rare condition — so part of what looks like "30m is a cleaner timeframe" is 30m simply
being unable to see rare things.
