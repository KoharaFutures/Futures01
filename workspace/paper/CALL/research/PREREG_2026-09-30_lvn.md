# Pre-registration: LVN fade (#17) and sweep & reclaim (#18)

**Written 2026-09-30 21:40 ET (2026-10-01T01:40Z), before any code for these rules was written or run.**
Nothing below may be changed after results are seen. Any added variant is appended here with a new
timestamp and counted in N_tried.

## Data and engine (shared by every variant)

- Symbols: MGC, MNQ (required), MES, MCL (data exists). Bars: `data/archive/<SYM>_15m.jsonl` and
  `_5m.jsonl` (2026-07-29 → 2026-09-30, ~2 months), `_60m.jsonl` (2024-10 → 2026-09) for 60m-built profiles.
- Fills, costs, sizing, exits from `DATA_HUB/tools/walkforward.py` (imported, not re-implemented):
  market orders fill at the next bar's open one tick worse; stop wins a same-bar tie; gaps fill at the
  open; flat at the first 16:00 ET; no fills on 15:xx/16:xx bars; calendar roll mask; cost = contract
  round turn (commission + fees + 1 tick slippage); R = net $ / $ at risk; drawdown-ladder sizing.
- Two extensions, written in a new driver (`workspace/paper/CALL/research/run_lvn_2026-09-30.py`):
  1. **Limit fills (A1 only):** a resting limit fills at the limit price when a bar trades through it
     (at the open if the bar gaps through it in our favour). No extra tick (slippage is in the cost).
     On the fill bar only the stop is checked (if the bar also reached the stop, it is a loss);
     the target can only be hit from the next bar on.
  2. **Time exit:** every position (all variants) is closed at the close of the 16th bar counting the
     fill bar, if stop/target/16:00 flat has not happened first.
- ATR = ATR14 of the bars being traded, through the signal bar.
- Target = 1.8 R from the actual fill for every variant.
- Walk-forward / out-of-sample: every parameter is fixed here, nothing is fitted, and each bar is
  decided only from data closed before it, so the whole run is out of sample. First-half vs
  second-half average R is reported as the stability check.

## Hypothesis A — deep first-LVN-outside-value fade (backlog #17)

- Profiles: rolling **72 h (primary)**, 24 h and 48 h, built from 5m bars exactly as
  `workspace/paper/CALL/preopen.py` (`profile` + `summarize` copied verbatim): volume spread evenly over
  the bins a bar's range covers; POC; 70% value area grown from POC; LVN = 3-bin smoothed local minimum
  < 50% of POC with heavier (>1.5x) volume on both sides; depth = valley / smaller of the highest
  smoothed peaks within 25 bins each side. Bins: MNQ 5.0, MGC 1.0 (preopen), MES 1.0, MCL 0.02 (fixed now).
- Profile at 15m bar i = the 5m bars whose close is at or before bar i's close and whose open is within
  the last H hours. Signals on bar i use the profile as of bar i-1's close (so the arriving bar never
  shapes its own level).
- Level U = first LVN above VAH, used only if depth < 0.35. Level D = first LVN below VAL, depth < 0.35.
- **Arming ("arrives from inside value"):** a side arms when a 15m bar closes inside value
  (VAL ≤ close ≤ VAH). The up side disarms on a close at/above U; the down side on a close at/below D.
  A signal disarms its side until the next inside-value close.
- **A1 limit:** while armed and flat, a SHORT limit rests at the current U (LONG at D). It lives at most
  16 bars after the most recent arming close. It fills on the first bar whose high ≥ U (low ≤ D).
  If both sides fill on one bar the bar is skipped.
- **A2 confirmation:** while armed, a 15m bar touches U (high ≥ U) and CLOSES back inside value
  (close ≤ VAH and ≥ VAL) → SHORT at the next bar's open (mirror for D → LONG).
- **Stop:** beyond the LVN, not the HVN edge: SHORT stop = U + 0.25 ATR + 1 tick; LONG stop = D −
  0.25 ATR − 1 tick. If the fill is already beyond the stop, no trade.
- Variants: {A1, A2} × {24h, 48h, 72h}. Primary: A1-72h and A2-72h.

## Hypothesis B — sweep & reclaim of a profile level (backlog #18)

- Levels: 1-week profile built from 60m bars = `vp_levels.build_profile` over the 60m bars of the 5
  trading days before the current trading day (the hub's definition). Levels = its LVNs + VAH + VAL.
- Signal on a 15m bar i, for any level L: previous close > L, low ≤ L − 1 tick, close > L → LONG
  (mirror: previous close < L, high ≥ L + 1 tick, close < L → SHORT). If both sides fire on one bar,
  skip. If several levels fire on one side, the level nearest the close is recorded.
- Entry next bar's open; stop = sweep extreme ∓ 1 tick (low − 1 tick for a LONG); target 1.8 R.
- **B15** (primary) as above on 15m bars. **B60** (secondary, longer history, 2024-10 → 2026-09): the
  same rule on 60m bars, 16-bar time exit.

## Stacked-level split (both hypotheses)

"Hub levels" at the signal = `bounce_levels.day_levels` start levels for that trading day (PDH, PDL,
PDC, prior-day POC & VWAP, prior RTH high/low, PWH, PWL, round numbers) + ONH/ONL during RTH, built
from the traded series, + `vp_levels.levels_of` of the 1-week 60m profile (LVN, HVN, POC, VAH, VAL).
Stacked = 3 or more hub levels within 0.5 ATR of the fill price (the signal level itself excluded
when it is within one tick). Each variant is reported for all / stacked / not stacked.

## Controls

- **P1 direction placebo:** same bar, same stop and target distances, random side (1000 draws), same
  time exit (walkforward.py `score`).
- **P3 level placebo, 10 seeds:** the whole run repeated with levels replaced by random prices:
  A: U → uniform(VAH, profile high), D → uniform(profile low, VAL), only when the real profile has a
  qualifying LVN on that side, redrawn once per clock hour; B: each level → uniform(profile low, high),
  fixed per trading day (as walkforward `Ctx.levels`).
- **Luck bar:** N_tried = 8 variants (A1×3, A2×3, B15, B60) × (4 symbols + pooled) × 3 subsets
  (all/stacked/not) = **120** → √(2·ln 120) = 3.09. Registered in `DATA_HUB/walkforward/LEDGER.tsv`
  (family LVN1718).

## Pass rule (fixed now)

A cell is an edge candidate only if: N ≥ 30, t ≥ luck bar, z vs P1 ≥ luck bar, and real average R
beats the level placebo in ≥ 9 of 10 seeds. Anything else is "no edge shown".
