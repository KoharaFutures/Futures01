#!/usr/bin/env python3
"""Generic level-touch signal generator + the level placebo, shared by F2b, F3 and F4.

A level set is {trading_day: [(price, tag, hint)]} and must be knowable at the START of that
trading day. `hint` is None (the mode decides direction) or +-1 (the mode must obey it).
"""
from __future__ import annotations

import random


def touch_signals(t, lvl_by_day: dict, mode: str, retest: bool = False):
    """mode: 'fade' (reject off the level), 'break' (close through it), 'hint' (obey hint)."""
    sig = []
    seen: dict = {}
    for i in range(len(t.bars)):
        lv = lvl_by_day.get(t.day[i])
        if not lv:
            continue
        b = t.bars[i]
        prev_c = t.bars[i - 1].c if i else b.o
        for item in lv:
            p, tag = item[0], item[1]
            hint = item[2] if len(item) > 2 else None
            key = round(p / t.tick)
            if mode == "fade":
                if not (b.l <= p <= b.h):
                    continue
                if prev_c < p and b.c < p:
                    side = -1
                elif prev_c > p and b.c > p:
                    side = 1
                else:
                    continue
            elif mode == "break":
                if prev_c < p <= b.c:
                    side = 1
                elif prev_c > p >= b.c:
                    side = -1
                else:
                    continue
            elif mode == "hint":
                if hint is None or not (b.l <= p <= b.h):
                    continue
                if (hint > 0 and b.c <= p) or (hint < 0 and b.c >= p):
                    continue
                side = hint
            elif mode == "anti_hint":
                # the trend-failure side: retrace into the level, close AGAINST the impulse
                if hint is None or not (b.l <= p <= b.h):
                    continue
                if (hint > 0 and b.c >= p) or (hint < 0 and b.c <= p):
                    continue
                side = -hint
            else:
                raise ValueError(mode)
            n = seen.get(key, 0)
            seen[key] = n + 1
            if retest and n == 0:
                continue
            sig.append((i, side, p, tag))
    return sig


def fake_levels(lvl_by_day: dict, rng_by_day: dict, seed: int) -> dict:
    """Same count of levels per day, uniform random prices inside that day's profile range,
    hints preserved so direction mix is matched."""
    rng = random.Random(seed)
    out = {}
    for d, lv in lvl_by_day.items():
        lo, hi = rng_by_day.get(d, (None, None))
        if lo is None or hi <= lo:
            continue
        out[d] = [(rng.uniform(lo, hi), it[1], (it[2] if len(it) > 2 else None)) for it in lv]
    return out
