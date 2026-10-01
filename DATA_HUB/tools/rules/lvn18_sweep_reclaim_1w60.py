"""#18: sweep & reclaim of a 1-week 60m-built profile level (LVN, VAH or VAL).

Pre-registered 2026-09-30 21:40 ET in workspace/paper/CALL/research/PREREG_2026-09-30_lvn.md, before
this file was run.

  levels  vp_levels.build_profile over the 60m bars of the 5 trading days before today: LVNs + VAH + VAL
  signal  previous close > L, bar low <= L - 1 tick, bar close > L  -> LONG   (mirror -> SHORT);
          both sides on one bar -> skip; several levels -> the one nearest the close is recorded
  order   next bar's open; stop = sweep extreme -/+ 1 tick; target 1.8 R; 16-bar time exit
  B15     on 15m bars (primary);  B60  on 60m bars, 2024-10 -> 2026-09 (secondary)

Runs through workspace/paper/CALL/research/run_lvn_2026-09-30.py (walkforward.py fills/costs/sizing/
scoring + a 16-bar time exit). `signals()` is the causal rule.
"""
from __future__ import annotations

import random

NAME = "LVN18_sweep_reclaim_1w60"
WARMUP = 0
USES_LEVELS = True
PREREG = {"family": "LVN1718", "trials": 30,
          "text": "15m (B15) / 60m (B60) bar sweeps a 1-week 60m-profile LVN/VAH/VAL by >=1 tick and closes back "
                  "on the original side; enter next open in the reclaim direction, stop sweep extreme +-1 tick, "
                  "target 1.8R, 16-bar time exit; MGC MNQ MES MCL; all/stacked/not; 2 variants x 5 x 3 = 30 trials."}

TARGET_R = 1.8


def day_level_map(profiles, level_seed=None):
    """{trading_day: [levels]} from {trading_day: Profile}. Placebo: same count, uniform in the range."""
    out = {}
    for d, pf in profiles.items():
        real = list(pf.lvn) + [pf.vah, pf.val]
        if level_seed is None:
            out[d] = real
        else:
            rng = random.Random(f"{level_seed}:{d}")
            out[d] = [rng.uniform(pf.lo, pf.hi) for _ in real]
    return out


def signals(bars, tdays, levels_by_day, tick):
    ev = {}
    for i in range(1, len(bars)):
        lv = levels_by_day.get(tdays[i])
        if not lv:
            continue
        b, pc = bars[i], bars[i - 1]["c"]
        longs = [L for L in lv if pc > L and b["l"] <= L - tick and b["c"] > L]
        shorts = [L for L in lv if pc < L and b["h"] >= L + tick and b["c"] < L]
        if longs and shorts:
            continue
        if longs:
            L = min(longs, key=lambda x: abs(b["c"] - x))
            ev[i] = {"side": "LONG", "stop": b["l"] - tick, "level": L,
                     "why": f"swept {L:.2f} to {b['l']}, closed {b['c']} back above"}
        elif shorts:
            L = min(shorts, key=lambda x: abs(b["c"] - x))
            ev[i] = {"side": "SHORT", "stop": b["h"] + tick, "level": L,
                     "why": f"swept {L:.2f} to {b['h']}, closed {b['c']} back below"}
    return ev
