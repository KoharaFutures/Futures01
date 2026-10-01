#!/usr/bin/env python3
"""LVN/FIB AGENT — prove the desk's live logic is the backtest's logic.

The prior in CHARTER.md §1 is only meaningful if the levels and triggers the desk computes
forward are the same ones the backtest scored. This replays arm A bar by bar, computing the
prior-week golden pocket from a TRUNCATED tape (so no bar after the decision is visible), and
compares the resulting trade set to the ANCH1 backtest's.
"""
from __future__ import annotations

import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "workspace" / "anchors" / "lib"))
import core                                        # noqa: E402
import engine                                      # noqa: E402
import structures as S                             # noqa: E402
from levels import touch_signals                   # noqa: E402

SYM = "MGC"
t = core.tape(SYM, 60)


class Slice:
    """A read-only view of the tape up to and including bar n - what the desk can see."""
    def __init__(self, base, n):
        self.bars, self.day = base.bars[:n + 1], base.day[:n + 1]
        self.rth, self.atr = base.rth[:n + 1], base.atr[:n + 1]


# --- 1. levels: desk-as-of-bar vs backtest's per-day table -------------------
bt_lv, _ = S.fib_levels(t, "prior_week", S.GOLDEN)
checked = mismatch = 0
seen = set()
for i in range(500, len(t.bars)):
    d = t.day[i]
    if d in seen or d not in bt_lv:
        continue
    # first bar of that trading day: the desk computes levels before the day trades
    if i > 0 and t.day[i - 1] == d:
        continue
    seen.add(d)
    plan_week = t.bars[i].ts.isocalendar()[:2]
    desk = engine.arm_a_levels(Slice(t, i - 1), plan_week=plan_week)
    if desk is None:
        continue
    checked += 1
    dp = sorted(round(x["price"], 4) for x in desk["levels"])
    bp = sorted(round(p, 4) for p, _tag, _h in bt_lv[d])
    if dp != bp:
        mismatch += 1
        if mismatch <= 3:
            print(f"  MISMATCH {d}: desk {dp} vs backtest {bp}")
print(f"1. levels: {checked} trading days checked, {mismatch} mismatch(es)")

# --- 2. triggers: desk's condition vs the backtest's signal set --------------
bt_sig = {(i, s) for i, s, _p, _tg in touch_signals(t, bt_lv, "anti_hint")}
desk_sig = set()
for i in range(len(t.bars)):
    d = t.day[i]
    if d not in bt_lv or not t.rth[i] or t.last_rth[i]:
        continue
    for p, _tag, hint in bt_lv[d]:
        side = 1 if hint < 0 else -1          # trade_side as engine.py computes it
        b = t.bars[i]
        if not (b.l <= p <= b.h):
            continue
        if (b.c > p) if side > 0 else (b.c < p):
            desk_sig.add((i, side))
bt_rth = {(i, s) for i, s in bt_sig if t.rth[i] and not t.last_rth[i]}
print(f"2. triggers inside the entry window: desk {len(desk_sig)}, backtest {len(bt_rth)}, "
      f"symmetric difference {len(desk_sig ^ bt_rth)}")

# --- 3. the prior the charter quotes, recomputed here ------------------------
sig = touch_signals(t, bt_lv, "anti_hint")
for nm, lo, hi, lim in (("OOS market", t.is_end, len(t), False),
                        ("OOS limit ", t.is_end, len(t), True)):
    s = core.summary(core.score(t, sig, lo, hi, limit=lim, limit_bars=2))
    print(f"3. {nm}: n={s['n']} avgR={s['avg_r']:+.4f} t={s['t']:+.3f} "
          f"win={s['win']:.3f} payoff={s['payoff']:.2f}")

# --- 4. the resolver, exercised on real fills -------------------------------
bk = core.score(t, sig, t.is_end, len(t), limit=True, limit_bars=2)
rs = [x.r for x in bk.trades]
onfill_target = 0
for x in bk.trades:
    j = next((k for k in range(x.i + 1, min(x.i + 3, len(t.bars)))
              if (x.side > 0 and t.bars[k].l <= x.fill) or (x.side < 0 and t.bars[k].h >= x.fill)), None)
    if j is not None and x.exit_i == j and x.why == "target":
        onfill_target += 1
print(f"4. resolver on {len(rs)} real arm-A fills: avgR {st.fmean(rs):+.4f}, "
      f"targets booked on the fill bar = {onfill_target} (must be 0 after the look-ahead fix)")
print(f"   exits {dict(sorted({w: sum(1 for x in bk.trades if x.why==w) for w in {x.why for x in bk.trades}}.items()))}")
