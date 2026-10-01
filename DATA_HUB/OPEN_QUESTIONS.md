# Open questions — what to test next

**How to test anything here:** write the rule down **before** looking (pre-register it), test it
once on the archive against a placebo, and report it against the single-test bar (t ≥ 1.18).
Don't sweep 500 variants. That's how the last ~3 million tests found nothing.

## Priority list

| # | hypothesis (pre-register exactly this) | why it's first | where the evidence is |
|---|---|---|---|
| 1 | ✅ **TESTED 2026-09-29** (`walkforward/OQ1_*`): 106 trades, +0.06R, t 0.64 vs bar 1.79. Beats a coin-flip direction (p 0.035) and random levels (35/40), but not an edge yet. Positive on MES (+0.18R) and MGC (+0.23R); fails on MCL. Next: more span, or a new pre-registered MES+MGC-only variant (new ledger entry). Original: **LVN bounce on 60m-built profiles:** at an LVN of the 1-week (60m) profile, when price rises into it from below, fade it (short) with stop = target = 1 ATR | The owner's own method. It's the only volume-profile result that points the same way on all 4 symbols (−17 pts continuation vs random, n=177) | `levels/CONSISTENCY.md`, `levels/*_volume_profile.md` |
| 2 | ✅ **TESTED 2026-10-01** (ledger `PERSYM1_exit_management_08R`), **closed in both directions.** Breakeven at +0.8R **does nothing**: it changes only **4–7% of trades**, four arms positive and four negative, best paired t **+1.74** against a 2.327 bar. A **full exit at +0.8R is reliably worse on 8/8 arms**, paired t **−3.12 to −8.60**, costing 0.06–0.13R per trade while raising the win rate 5–8 pp — the project's own "win rate and payoff go together" rule, demonstrated. Both policies *do* cut drawdown, and on MES that matters: the baseline peaks at **$3,012 against the $2,800 floor (dead)** while the 0.8R exit holds $2,563. The six live fills that motivated this were a small enough sample that 5% of trades could look like all of them. Original: **Stop to breakeven at +0.8R** | ~8,000 paired trades, entries unselected so the exit is the only variable | `workspace/anchors/REPORT_PERSYM1.md` §0.1–0.2 |
| 3 | ❌ **RETIRED 2026-10-01** (ledger `PERSYM1_MGC_value_area_edge`). Moved 30m→60m because 30m holds only 2013 bars (declared before running). In-sample n=164 **−0.2259R t −3.713**, out-of-sample n=91 **+0.0148R t +0.144** — a complete sign flip. **54.9% winners at a 0.85 payoff**, i.e. a majority of winning trades earning nothing. A coin flip on the same bars averaged **+0.2553R** and beat the real rule **9 times out of 10**. Original: **MGC 30m: fade the value-area edge** | — | `workspace/anchors/REPORT_PERSYM1.md` §3.1 |
| 4 | **Sweep & reclaim of the prior-day / prior-RTH high → short** (5m MNQ, 60m MGC) | Beat fake levels z 2.3–2.4 on two symbols. Needs a pre-registered retest | `levels/MNQ_bounce.md`, `levels/MGC_bounce.md` |
| 5 | ❌ **RETIRED 2026-10-01** (ledger `PERSYM1_MCL_momentum`). **Does not replicate.** 60m loses in-sample (n=270, −0.1327R, t −2.145) *and* out-of-sample (n=174, −0.0879R, t −1.163). 240m loses in-sample and goes mildly positive out-of-sample (n=135, +0.0521R, t +0.496) — a sign flip, not a confirmation. Note the fundable version is the losing one: the $120 budget sizes 137 of 174 of the 60m trades. Original: **MCL momentum (60m/240m)**, claimed 97% of observations positive, t 2.97 | — | `workspace/anchors/REPORT_PERSYM1.md` §4 |
| 6 | ⚠️ **PARTLY TESTED 2026-10-01** (ledger `PERSYM1_MESMNQ_daily_7y`). A 20-day daily breakout is the right shape on both — MES n=70 **+0.1113R** t +0.701, MNQ n=65 **+0.1310R** t +0.777 with **both halves positive and similar (+0.108/+0.153)**, the only arm in either study to manage that, payoff 1.73, coin flip beaten 10/10 — but **neither clears the 2.327 bar** and **the $120 budget funded 1 of 252 trades** across all four arms, because a 1-ATR daily index stop is ~$300–400/contract. 2σ daily reversion fails on both. **MGC daily remains unusable**: my own audit measured a **909.99%** splice gap, confirming `RULES_AND_PITFALLS.md` §5. Still open: a longer slice for the MNQ breakout, and a fundable daily stop | 1865 bars, 2019-05-03→2026-09-29 | `workspace/anchors/REPORT_PERSYM1.md` §1–2 |
| 7 | Finish the parked **EF3 MES/MNQ 60m placebo stage** (103k trades, never run) | Already built, just unrun | `workspace/roundtable/edge/EF3/code/ef3_stage2.py`, `ef3_rank.py` (kept in place) |
| 8 | ⚙️ **FUNDING FIX CONFIRMED 2026-10-01** (ledger `PERSYM1_MGC_fib_limit_entry_DIAGNOSTIC`, diagnostic only — the rule was selected on these bars so no expectancy figure from it is evidence). The resting limit takes the median stop from **20.41 pts / $204 to 10.38 pts / $104**, inside the $120 budget, and raises fundable trades from **6 of 33 to 16 of 26**; 18 signals expire unfilled. **Significance still needs bars neither study has seen.** Original: **MGC fib trend-failure, with a resting limit at the level instead of a next-open market order.** Same rule as ledger `ANCH1_MGC_fib_trend_failure`; the limit removes the fill gap and takes the median stop from 20.4 points ($204) to ~0.5 ATR, which the $120 budget can fund | The best result the project has produced: OOS n=33, **+0.4324R, t +2.705** vs bar 2.521, win 66.7% / payoff 1.54, halves +0.446/+0.419, both placebos beaten 10/10 — but shift-null z 2.49 misses the bar, and the account could fund only 6 of 33 trades | `workspace/anchors/REPORT.md` §4 |
| 9 | **The 0.786 retracement alone, on MGC, on fresh bars.** Inside #8 the result is carried by the deepest level: 0.786 alone n=14 **+0.6541R t +2.993**, while 0.618 alone is +0.3040R t +1.123 and 0.705 alone +0.1489R t +0.541 | Either this is the real finding hiding inside #8 or it is the reason #8 is a fluke. One pre-registered test on new data separates them. "Golden pocket" is the wrong name for it | `workspace/anchors/diag_mgc.py` |

## The question that now blocks the most progress: sizing, not signals

Two of the three best ideas in this project die on the **$120 risk cap**, not on expectancy
(2026-10-01). Daily index trend-following funded **1 of 252** trades; the naked-POC magnet funded
**0 of 207**; the MGC fib candidate funded **6 of 33** on a market order and 16 of 26 on a limit.
Measuring more rules at this cap will keep producing unfundable winners. Either the risk policy
changes, the entry mechanism tightens the stop (as #8 showed a limit can), or the timeframe comes
down. This should be settled before the next signal search.

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
