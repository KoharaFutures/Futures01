# Pre-registration — anchored structure families (ANCH1)

**Written 2026-10-01 BEFORE any arm was run.** Commit this file before any result file exists.
Owner request: research and backtest LVN, POC, Fibonacci retracements and standard deviations with
varied anchoring methodologies, across timeframes including merged ones, **uniquely per symbol**.

---

## 0. What is already dead, and therefore not re-tested here

| structure | prior result | source |
|---|---|---|
| LVN bounce (first touch from below, 1w/60m profile) | 106 trades, +0.06R, t 0.64 vs bar 1.79 | `DATA_HUB/walkforward/OQ1_*` |
| Deep-LVN fade, 5m rolling 24/48/72h profiles | 90 trials, all fail | `DATA_HUB/walkforward/LVN1718` |
| LVN / VAH / VAL sweep-and-reclaim, 15m & 60m | 30 trials, all fail; 60m pooled **−0.165R, t −3.21** | same |
| Classic POC / VWAP / PDH-PDL / round numbers as bounce levels | no excess reaction vs random prices, 4 independent methods | `DATA_HUB/BOUNCE_AND_VOLUME_PROFILE_PLAYBOOK.md` §2 |
| Stacked levels (2+ within ¼ ATR) as fade locations | combined z **−5.1** — the most reliable level finding in the project | same |

Those are inputs, not hypotheses. In particular **H4 below takes the stacked-level finding as a
prior and pre-registers the CONTINUATION side**, which has never been tested as a rule.

## 1. Data, fixed before looking

- Source: `data/archive/<SYM>_60m.jsonl`. 60m is the only timeframe with usable span
  (MES 11399, MNQ 11402, MGC 11406, MCL 11044 bars; 2024-10-06 → 2026-09-30, ~475 sessions).
  5m/15m hold only 2 months (2026-07-29 →) and 30m only 2013 bars — both already burnt by
  `LVN1718` and too short for a fresh family. 1440m is roll-clean for MES/MNQ (1865 bars, 7.4y)
  but cannot carry an intraday anchor, so it is used only for the F3 weekly/monthly anchors.
- Integrity census run before writing this: 0 duplicate timestamps, 0 backwards timestamps,
  ≤13 flat high=low bars per symbol, ≤3 stub bars, 3.5–3.9% zero-volume bars (the 17:00
  maintenance hour and holidays). Zero-volume bars contribute price range but no volume to a
  profile, and are ineligible as entry bars.
- **Split, fixed now: in-sample = first 60% of bars, out-of-sample = last 40%.**
  IS is for specification search and is explicitly exploratory — no significance is claimed on it.
  OOS is run **once** per (family × symbol) on the specification IS selected.
- Per-symbol specs from `futures_agents.config.get_contract`. Round-turn friction in points
  φ = 2·(commission+fee)/point_value, plus one adverse tick on each of entry and exit inside the
  fill itself: MES 0.288+0.50, MNQ 0.720+0.50, MGC 0.144+0.20, MCL 0.0144+0.02.
- RTH hours on 60m bars, from the contract spec: MES/MNQ 09–15, MGC 08–13, MCL 09–14 (ET).

## 2. Scoring, identical for every arm so nothing is selected by exit geometry

| element | value |
|---|---|
| entry fill | next bar's open, ± 1 tick adverse |
| stop | the level, displaced 0.5·ATR14 + 1 tick to the far side; floored at `min_stop_ticks` |
| target | 1.5 R, where R = the stop distance. One geometry only, no sweep |
| time exit | 12 bars after the entry bar, at that bar's close |
| session exit | hard flat at the symbol's RTH close bar; no new entries in the final RTH hour |
| same-bar tie | the stop wins a same-bar stop/target touch |
| position limit | one position at a time per symbol; an "all signals" census is reported alongside so the limit cannot silently select |
| R | net_R = (gross_points − φ)/stop_points |
| account | $50,000, floor $2,800 drawdown, risk min(6% room-to-floor, 0.75% equity, $500), halved to ≤$120 while nothing is proven |

## 3. Controls, every arm

1. **Level placebo** — identical rule, the structure prices replaced by uniform-random prices in
   the same profile range, 10 seeds, matched on realised trade count.
2. **Direction placebo** — identical bars and entries, direction from a seeded coin flip.
3. **Shift-null** — 200 circular shifts of the outcome series with the signal masks held fixed,
   giving the family-wise bar empirically rather than from √(2·ln N).

## 4. The hypotheses, stated as rules

**H1 — Anchored VWAP and its σ bands (the anchor-choice question).**
Build AVWAP from a chosen anchor bar: volume-weighted mean price from the anchor forward, plus
σ = the volume-weighted standard deviation of typical price about that mean. Anchors tested on IS:
(a) session open, (b) prior session close / 18:00 Globex open, (c) week open, (d) month open,
(e) highest-volume bar of the trailing 20 sessions, (f) widest-range bar of the trailing 20
sessions, (g) most recent 5-bar fractal swing high/low.
Rule: price tags AVWAP ± kσ (k ∈ {1,2}) and the bar **closes back inside** the band → enter next
open toward AVWAP; stop beyond the tagged extreme; target 1.5R as §2. Secondary form: AVWAP itself
as support/resistance, retest only (first touches are known to be worse than random, z −3.7).
**OOS prediction:** for each symbol, the single best IS anchor/k combination has OOS mean
net_R > 0 at t ≥ 2.35 (the §5 bar).

**H2 — Naked POC.**
A naked POC is the POC of a prior RTH session (or prior week) that price has not traded through
since it formed. Two separate instruments:
- **H2a (magnet / destination):** from a bar whose close is ≥ 1 ATR from the nearest nPOC and on
  the far side of it, enter toward the nPOC with target = the nPOC and stop = 1.5× the distance.
  Literature claims ~80% of nPOCs are revisited within 10 sessions. **Pre-registered: the revisit
  rate of real nPOCs exceeds that of random untested prices in the same range by ≥ 5 percentage
  points, and the magnet trade's net R beats the level placebo.**
- **H2b (fade on arrival):** fade the first arrival at an nPOC. Stated for completeness; the prior
  on classic POC is null, so this is expected to fail and is counted as a trial.

**H3 — Fibonacci retracements, four anchorings.**
Anchor the leg at (a) prior RTH session range, (b) prior week range, (c) overnight Globex range,
(d) the most recent completed impulse leg from an ATR-threshold ZigZag. Levels 0.382, 0.5, 0.618,
0.705, 0.786 of the leg. Rule: price retraces into the level and the bar closes back in the
impulse direction → enter next open **with the impulse** (continuation), stop beyond the
retracement extreme, target 1.5R.
**OOS prediction:** the golden-pocket band (0.618–0.786) beats the shallow levels (0.382, 0.5) on
mean net_R, and beats the level placebo, per symbol.

**H4 — Merged-timeframe confluence, traded as CONTINUATION.**
Build profiles from 60m bars over four window lengths — 1 session, 1 week, 1 month, 3 months —
and merge them: a **confluent LVN** is a price that is an LVN on ≥ 2 of the four windows within
¼ ATR. The project's most reliable level finding is that stacked levels are the worst place to
fade (z −5.1), so the pre-registered direction here is **through**, not against: when a 60m bar
closes beyond a confluent LVN having opened on the other side, enter next open in the direction
of the break, stop back inside the LVN by 0.5·ATR + 1 tick, target 1.5R.
**OOS prediction:** mean net_R > 0 at t ≥ 2.35, and strictly greater than the same rule run on
single-window (non-confluent) LVNs.

## 5. Trial count and the bar

- IS variants are counted and reported in full, and **no significance is claimed from IS**.
- OOS is 4 families × 4 symbols = **16 confirmation tests**, each run once.
  Luck bar √(2·ln 16) = **2.355**. H2a's revisit-rate test is one extra descriptive test (17 →
  2.38). The shift-null is reported next to it and takes precedence where they disagree.
- A result is reported as an edge only if it clears that bar **and** beats both placebos **and**
  holds the same sign in both halves of OOS.

## 6. What would make me drop a family

If an IS arm produces fewer than 20 trades per symbol it is reported as unmeasurable, not as a
null, and the floor-free census is given (the 20-trade floor is known to select exit geometry).
