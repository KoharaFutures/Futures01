#!/usr/bin/env python3
"""The OOS confirmation stage: run once, against all three pre-registered controls."""
from __future__ import annotations

import statistics as st

import core
from levels import fake_levels, touch_signals


def confirm(t, sig, spec: dict, lvl_by_day=None, rng_by_day=None, mode=None, retest=False) -> dict:
    lo, hi = t.is_end, len(t)
    bk = core.score(t, sig, lo, hi)
    real = core.summary(bk)
    dp = [core.direction_placebo(t, sig, lo, hi, seed=s) for s in range(core.N_PLACEBO_SEEDS)]
    dpa = [p["avg_r"] for p in dp if p["n"]]
    sh = core.shift_placebo(t, sig, lo, hi)
    out = {"spec": spec, "real": real,
           "dir_placebo_avg": st.fmean(dpa) if dpa else None,
           "dir_placebo_beaten": sum(1 for p in dp if p["n"] and real.get("n") and real["avg_r"] > p["avg_r"]),
           "shift": sh, "z_shift": core.z_shift(real, sh),
           "account": core.account(bk, t)}
    if lvl_by_day is not None and mode is not None:
        lp = []
        for s in range(core.N_PLACEBO_SEEDS):
            fl = fake_levels(lvl_by_day, rng_by_day, seed=s)
            lp.append(core.summary(core.score(t, touch_signals(t, fl, mode, retest), lo, hi)))
        lpa = [p["avg_r"] for p in lp if p["n"]]
        out["lvl_placebo_avg"] = st.fmean(lpa) if lpa else None
        out["lvl_placebo_n_avg"] = st.fmean([p["n"] for p in lp]) if lp else None
        out["lvl_placebo_beaten"] = sum(1 for p in lp if p["n"] and real.get("n") and real["avg_r"] > p["avg_r"])
    return out


def line(tag, r):
    rl = r["real"]
    if not rl.get("n"):
        return f"  {tag}: no OOS trades"
    s = (f"  {tag}: n={rl['n']} avgR={rl['avg_r']:+.4f} t={(rl['t'] if rl['t'] is not None else float('nan')):+.3f} "
         f"win={rl['win']:.2f} payoff={(rl['payoff'] or float('nan')):.2f} "
         f"halves {(rl['h1'] or 0):+.3f}/{(rl['h2'] or 0):+.3f}")
    s += f"\n      dir-plc {r['dir_placebo_avg']} beaten {r['dir_placebo_beaten']}/10"
    if "lvl_placebo_avg" in r:
        s += f" | lvl-plc {r['lvl_placebo_avg']} (n~{r['lvl_placebo_n_avg']}) beaten {r['lvl_placebo_beaten']}/10"
    s += f"\n      shift-null {r['shift'].get('mean')} sd {r['shift'].get('sd')} -> z {r['z_shift']}"
    s += f"\n      exits {rl['exits']} | account {r['account']}"
    return s
