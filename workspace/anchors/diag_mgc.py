#!/usr/bin/env python3
"""Diagnostics on the one candidate: MGC, Fibonacci trend-failure at the prior week's golden
pocket. These are checks on a single already-chosen rule, not a search, so they add no trials -
but anything they break, breaks the result."""
from __future__ import annotations

import collections
import math
import pathlib
import statistics as st
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "lib"))
import core                                      # noqa: E402
import structures as S                           # noqa: E402
from levels import touch_signals, fake_levels    # noqa: E402

t = core.tape("MGC")
lv, rg = S.fib_levels(t, "prior_week", S.GOLDEN)
sig = touch_signals(t, lv, "anti_hint")

print(f"MGC bars {len(t)}  IS/OOS split at {t.is_end} ({t.bars[t.is_end].ts.date()})")
print(f"level days {len(lv)}  signals {len(sig)}")

for name, lo, hi in (("IS", 0, t.is_end), ("OOS", t.is_end, len(t)), ("ALL", 0, len(t))):
    bk = core.score(t, sig, lo, hi)
    s = core.summary(bk)
    print(f"\n{name}: n={s['n']} avgR={s['avg_r']:+.4f} sd={s['sd']:.3f} t={s['t']:+.3f} "
          f"win={s['win']:.3f} payoff={(s['payoff'] or float('nan')):.2f}")
    print(f"   exits {s['exits']} | signals {s['signals']} late {s['late']} overlap {s['overlap']}")
    if name != "ALL":
        continue
    rs = [x.r for x in bk.trades]
    print(f"   R quantiles: {[round(q,3) for q in st.quantiles(rs, n=10)]}")
    print(f"   best 3 {sorted(rs)[-3:]}  worst 3 {sorted(rs)[:3]}")
    m = st.fmean(rs)
    jack = [st.fmean([r for j, r in enumerate(rs) if j != k]) for k in range(len(rs))]
    print(f"   drop-one worst case avgR {min(jack):+.4f}  (full {m:+.4f})")
    k5 = sorted(range(len(rs)), key=lambda k: -rs[k])[:5]
    rest = [r for j, r in enumerate(rs) if j not in set(k5)]
    print(f"   drop the 5 best: n={len(rest)} avgR={st.fmean(rest):+.4f} "
          f"t={st.fmean(rest)/(st.stdev(rest)/math.sqrt(len(rest))):+.3f}")
    by = collections.defaultdict(list)
    for x in bk.trades:
        by[t.bars[x.i].ts.year].append(x.r)
    for y in sorted(by):
        v = by[y]
        tt = (st.fmean(v) / (st.stdev(v) / math.sqrt(len(v)))) if len(v) > 1 and st.stdev(v) > 0 else None
        print(f"   {y}: n={len(v):3d} avgR={st.fmean(v):+.4f} t={(('%+.3f'%tt) if tt else '  --')}")
    byq = collections.defaultdict(list)
    for x in bk.trades:
        d = t.bars[x.i].ts
        byq[f"{d.year}Q{(d.month-1)//3+1}"].append(x.r)
    print("   by quarter: " + "  ".join(f"{q}:{len(v)}/{st.fmean(v):+.2f}" for q, v in sorted(byq.items())))
    print(f"   risk points: median {st.median([x.risk for x in bk.trades]):.3f} "
          f"max {max(x.risk for x in bk.trades):.3f} -> $ median "
          f"{st.median([x.risk for x in bk.trades])*t.spec.point_value:.0f} "
          f"(budget cap ${core.RISK_CAP})")
    print(f"   sides: long {sum(1 for x in bk.trades if x.side>0)} short {sum(1 for x in bk.trades if x.side<0)}")
    print(f"   hours: {dict(sorted(collections.Counter(t.bars[x.i].ts.hour for x in bk.trades).items()))}")

# count-matched level placebo: random prices, but keep only the first `n_real` signals per draw
print("\nCOUNT-MATCHED level placebo (OOS), 10 seeds:")
bk = core.score(t, sig, t.is_end, len(t))
n_real = len(bk.trades)
ms = []
for seed in range(10):
    fl = fake_levels(lv, rg, seed=seed)
    fb = core.score(t, touch_signals(t, fl, "anti_hint"), t.is_end, len(t))
    trs = sorted(fb.trades, key=lambda x: x.i)
    sub = [x.r for x in trs[:n_real]] if len(trs) >= n_real else [x.r for x in trs]
    if sub:
        ms.append(st.fmean(sub))
        print(f"   seed {seed}: all n={len(trs)} avgR={st.fmean([x.r for x in trs]):+.4f} | "
              f"first {len(sub)} avgR={st.fmean(sub):+.4f}")
print(f"   mean of count-matched draws {st.fmean(ms):+.4f} sd {st.stdev(ms):.4f} -> "
      f"z {(st.fmean([x.r for x in bk.trades])-st.fmean(ms))/st.stdev(ms):+.3f}")

# the same rule on the other three symbols, OOS, as a structural cross-check
print("\nSAME RULE, other symbols (OOS) - a structural effect should not be strongly negative:")
for s in ("MES", "MNQ", "MCL"):
    u = core.tape(s)
    l2, _r2 = S.fib_levels(u, "prior_week", S.GOLDEN)
    b2 = core.score(u, touch_signals(u, l2, "anti_hint"), u.is_end, len(u))
    q = core.summary(b2)
    print(f"   {s}: n={q['n']} avgR={(q.get('avg_r') or 0):+.4f} "
          f"t={(('%+.3f'%q['t']) if q.get('t') is not None else '  --')}")

# sensitivity: does it survive small changes to things that were never pre-registered?
print("\nSENSITIVITY (each is a free parameter that was never justified):")
for nm, fr in (("golden 0.618 only", (0.618,)), ("golden 0.705 only", (0.705,)),
               ("golden 0.786 only", (0.786,)), ("golden+0.5", (0.5, 0.618, 0.705, 0.786))):
    l3, _ = S.fib_levels(t, "prior_week", fr)
    q = core.summary(core.score(t, touch_signals(t, l3, "anti_hint"), t.is_end, len(t)))
    print(f"   {nm:20s} n={q['n']:3d} avgR={(q.get('avg_r') or 0):+.4f} "
          f"t={(('%+.3f'%q['t']) if q.get('t') is not None else '  --')}")
