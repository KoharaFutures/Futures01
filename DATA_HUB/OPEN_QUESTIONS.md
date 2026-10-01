# Open questions — what to test next

**How to test anything here:** write the rule down **before** looking (pre-register it), test it
once on the archive against a placebo, and report it against the single-test bar (t ≥ 1.18).
Don't sweep 500 variants. That's how the last ~3 million tests found nothing.

## Priority list

| # | hypothesis (pre-register exactly this) | why it's first | where the evidence is |
|---|---|---|---|
| 1 | ✅ **TESTED 2026-09-29** (`walkforward/OQ1_*`): 106 trades, +0.06R, t 0.64 vs bar 1.79. Beats a coin-flip direction (p 0.035) and random levels (35/40), but not an edge yet. Positive on MES (+0.18R) and MGC (+0.23R); fails on MCL. Next: more span, or a new pre-registered MES+MGC-only variant (new ledger entry). Original: **LVN bounce on 60m-built profiles:** at an LVN of the 1-week (60m) profile, when price rises into it from below, fade it (short) with stop = target = 1 ATR | The owner's own method. It's the only volume-profile result that points the same way on all 4 symbols (−17 pts continuation vs random, n=177) | `levels/CONSISTENCY.md`, `levels/*_volume_profile.md` |
| 2 | **Stop to breakeven at +0.8R** (then test a full exit at +0.8R) on the old desks' entry rules | All 6 live paper fills reached ≥ +0.83R before most lost; losers' mean best point was +1.23R | `sources/agent3_desks.md` §1b, §3 |
| 3 | **MGC 30m: fade the value-area edge / revert to prior-session POC** | The only classic profile levels with a positive sign on 4/6 cells (+0.15 / +0.20R) | `sources/agent1_roundtable.md` §3.2 |
| 4 | **Sweep & reclaim of the prior-day / prior-RTH high → short** (5m MNQ, 60m MGC) | Beat fake levels z 2.3–2.4 on two symbols. Needs a pre-registered retest | `levels/MNQ_bounce.md`, `levels/MGC_bounce.md` |
| 5 | **MCL momentum (60m/240m)** | 97% of observations positive, beat control on both session arms, t 2.97 | `sources/agent2_research.md` §4 |
| 6 | Longer spans instead of wider searches: **MES/MNQ daily (7.4 years, roll-clean)** and a **roll-adjusted MGC daily** | At 7.4 years an annualised Sharpe of 0.43 is enough for one pre-registered test | `sources/agent1_roundtable.md` §8 |
| 7 | Finish the parked **EF3 MES/MNQ 60m placebo stage** (103k trades, never run) | Already built, just unrun | `workspace/roundtable/edge/EF3/code/ef3_stage2.py`, `ef3_rank.py` (kept in place) |
| 8 | **MGC fib trend-failure, with a resting limit at the level instead of a next-open market order.** Same rule as ledger `ANCH1_MGC_fib_trend_failure`; the limit removes the fill gap and takes the median stop from 20.4 points ($204) to ~0.5 ATR, which the $120 budget can fund | The best result the project has produced: OOS n=33, **+0.4324R, t +2.705** vs bar 2.521, win 66.7% / payoff 1.54, halves +0.446/+0.419, both placebos beaten 10/10 — but shift-null z 2.49 misses the bar, and the account could fund only 6 of 33 trades | `workspace/anchors/REPORT.md` §4 |
| 9 | **The 0.786 retracement alone, on MGC, on fresh bars.** Inside #8 the result is carried by the deepest level: 0.786 alone n=14 **+0.6541R t +2.993**, while 0.618 alone is +0.3040R t +1.123 and 0.705 alone +0.1489R t +0.541 | Either this is the real finding hiding inside #8 or it is the reason #8 is a fluke. One pre-registered test on new data separates them. "Golden pocket" is the wrong name for it | `workspace/anchors/diag_mgc.py` |

## Things the hub scanners could add next (scriptable)
- ~~**Anchored VWAP** (from swing points / session opens) and **weekly VWAP**~~ — ✅ **TESTED
  2026-10-01** (`workspace/anchors/`, ledger `ANCH1`). Seven anchors x 3 band widths x 4 symbols on
  60m, as a fade and as a continuation. **No anchor beat any other anchor out of sample.** The
  anchor choice moved the trade count a lot and expectancy not at all. The RTH-session-open anchor
  is **unusable on 60m** (the session is 6-7 bars, so a sigma needs most of it; MGC and MCL gave
  zero eligible trades at a 5-bar warm-up) — it needs 5m/15m data, of which the archive holds only
  2 months. Fading MGC's bands loses from every anchor (swing pivot -0.2522R **t -5.927**, n=470).
- ~~**Naked (untested) POCs** from prior profiles.~~ — ✅ **TESTED 2026-10-01** (same ledger entry).
  The "~80% of naked POCs are revisited within 10 sessions" claim is **true and worthless**: real
  nPOCs revisit at 90.9-92.0%, random prices in the same session range at 89.1-89.9%, a gap of only
  **+1.5 to +2.7 pp** against a pre-registered +5 pp threshold. The magnet trade is also
  **unfundable**: it needs >=1 ATR of distance and risks 1.5x that, so the $120 budget refused
  207/207 MGC and 210/212 MES trades, and 195 of 215 exits were the session close.
- **Merged-timeframe LVN confluence is unmeasurable on 60m, not null** (2026-10-01). LVN on >=2 of
  the 1-session/1-week/1-month/3-month profiles within 1/4 ATR gives **0.22-0.48 levels per day** =
  2-13 in-sample trades. Needs intraday data with span, or a wider tolerance (a new pre-registration).
- **Day-type classifier** (trend vs normal vs neutral, from the first-hour range) as a filter
  for continuation-vs-bounce. MCL 44% trend days vs MNQ 12% suggests it matters.
- De-duplicate stacked levels into one event (today a PDL that equals an RTH low counts twice
  in the "all touches" rows. The per-type rows aren't affected).
- Resolve stops on 1m bars to cut the feed blind spot.

## Obligations left by the old desks
1. **CALL-0010** (MNQ short 30,550, stop 30,576) is still *pending* past its 09-29 09:30 ET expiry.
   It closes with one `resolve.py` run on the CALL desk's branch. Nobody may hand-write "EXPIRED".
   (The CALL desk is paused, so this waits until it's restarted or retired.)
2. If the CALL desk is ever re-armed: crons in UTC, re-cut on 2026-11-01, add a placebo/counterfactual
   first, anchor entries to fixed structure, and count the width of the gate search.
3. **REPLAY desk** (still running, MES 60m, bar ~3,400 of 11,287): a contract roll is ~800 bars
   ahead (~2025-06-20). Its `levels.py` control must be swapped for the fair one (E9). Thesis 5
   is retired.
4. The `README.md` "Honest status" section in the repo root still says only synthetic data was used.
   That's stale: every study since 2026-09-23 ran on real CME bars.
