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

## Things the hub scanners could add next (scriptable)
- **Anchored VWAP** (from swing points / session opens) and **weekly VWAP**. Never tested anywhere.
- **Naked (untested) POCs** from prior profiles.
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
