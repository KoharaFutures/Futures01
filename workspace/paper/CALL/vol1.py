#!/usr/bin/env python3
"""VOL-1 — does volume at a 1m/5m bounce level tell you anything directional?

PRE-REGISTERED 2026-09-28 at the owner's request: *"look at the 1 and 5 minute bounce levels
and see if you can match that with anything line volume or delta or anything that can tell you
that it is a buy or a short."*

DELTA IS NOT AVAILABLE. Bars in this environment carry o,h,l,c,v and nothing else. There is no
bid/ask, no tick data, no CVD, no footprint. CALLOUT.md: all three `orderflow` conditions are
OHLCV proxies with no delta data. So this tests the two things that DO exist:

  1. VOLUME at the pivot, as a ratio to its own trailing median.
  2. CLOSE POSITION inside the pivot bar's range -- the only honest OHLCV proxy for absorption.
     A pivot low that closes near its high "absorbed" the selling in the crude sense. It is a
     PROXY and is labelled as one; it is not delta and must never be reported as delta.

EVERYTHING BELOW IS FIXED BEFORE ANY RESULT IS SEEN.

  K            = 3      bars either side for a strict pivot
  ENTRY        = close of bar i+K, the confirmation bar. Never the pivot bar itself -- a pivot
                 is only knowable K bars later, and entering at i would be look-ahead.
  VOL_LOOKBACK = 20     bars for the trailing median (zeros excluded)
  HIGH / LOW   = 1.5x / 1.0x   the two volume buckets that get compared
  FWD          = 6      bars held after entry
  NORM         = ATR14 at entry, so MGC and MNQ are on one scale
  PLACEBO      = 200 draws of the same number of NON-pivot bars, same forward measurement.
                 This is the floor. A bucket that does not beat its placebo has found nothing.

Direction convention: pivot LOWS are tested as LONGS, pivot HIGHS as SHORTS, so a positive
number always means "the trade in the obvious direction made money".

Owned by agent CALL. Reads data/archive/ only (ends 2026-09-25), so today is out of sample.
"""
from __future__ import annotations
import json, math, random, statistics as st, pathlib, sys

K, VOL_LOOKBACK, FWD = 3, 20, 6
HIGH, LOW = 1.5, 1.0
PLACEBO_DRAWS = 200
ROOT = pathlib.Path("/home/user/Futures01/data/archive")
random.seed(20260928)


def load(sym, mins):
    p = ROOT / f"{sym}_{mins}m.jsonl"
    return [json.loads(l) for l in p.open() if l.strip()]


def atr(bars, i, n=14):
    trs = []
    for j in range(max(1, i - n + 1), i + 1):
        b, pr = bars[j], bars[j - 1]
        trs.append(max(b["h"] - b["l"], abs(b["h"] - pr["c"]), abs(b["l"] - pr["c"])))
    return sum(trs) / len(trs) if trs else float("nan")


def pivot_idx(bars, k=K):
    lows, highs = [], []
    for i in range(k, len(bars) - k):
        w = bars[i - k:i + k + 1]
        if bars[i]["l"] == min(x["l"] for x in w):
            lows.append(i)
        if bars[i]["h"] == max(x["h"] for x in w):
            highs.append(i)
    return lows, highs


def features(bars, i):
    """volume ratio and close-position, both known at the pivot bar."""
    hist = [x["v"] for x in bars[max(0, i - VOL_LOOKBACK):i] if x["v"] > 0]
    med = st.median(hist) if hist else float("nan")
    vr = bars[i]["v"] / med if med and med > 0 and bars[i]["v"] > 0 else float("nan")
    rng = bars[i]["h"] - bars[i]["l"]
    cp = (bars[i]["c"] - bars[i]["l"]) / rng if rng > 0 else 0.5
    return vr, cp


def fwd(bars, i, side):
    """forward move from the CONFIRMATION bar's close, in ATR units, signed by side."""
    e, x = i + K, i + K + FWD
    if x >= len(bars):
        return None
    a = atr(bars, e)
    if not a or a <= 0 or math.isnan(a):
        return None
    raw = bars[x]["c"] - bars[e]["c"]
    return (raw if side == "LONG" else -raw) / a


def tstat(xs):
    if len(xs) < 3:
        return float("nan")
    s = st.pstdev(xs)
    return (st.mean(xs) / (s / math.sqrt(len(xs)))) if s > 0 else float("nan")


def placebo(bars, side, n):
    """mean forward return of n random NON-pivot bars, repeated; returns (mean, sd of means)."""
    lows, highs = pivot_idx(bars)
    excl = set(lows) | set(highs)
    pool = [i for i in range(VOL_LOOKBACK, len(bars) - K - FWD - 1) if i not in excl]
    means = []
    for _ in range(PLACEBO_DRAWS):
        vals = [v for v in (fwd(bars, i, side) for i in random.sample(pool, min(n, len(pool)))) if v is not None]
        if vals:
            means.append(st.mean(vals))
    return (st.mean(means), st.pstdev(means)) if means else (float("nan"), float("nan"))


def run():
    print(f"VOL-1  pre-registered  K={K} FWD={FWD} HIGH={HIGH}x LOW={LOW}x "
          f"lookback={VOL_LOOKBACK} placebo={PLACEBO_DRAWS} draws")
    print("archive only, ends 2026-09-25.  NO DELTA EXISTS -- volume and close-position only.\n")
    rows = []
    for sym in ("MGC", "MNQ"):
        for mins in (1, 5):
            bars = load(sym, mins)
            lows, highs = pivot_idx(bars)
            for side, idxs in (("LONG", lows), ("SHORT", highs)):
                buckets = {"HIGH": [], "MID": [], "LOW": []}
                cp_hi, cp_lo = [], []
                for i in idxs:
                    r = fwd(bars, i, side)
                    if r is None:
                        continue
                    vr, cp = features(bars, i)
                    if math.isnan(vr):
                        continue
                    buckets["HIGH" if vr >= HIGH else "LOW" if vr < LOW else "MID"].append(r)
                    # close-position proxy: for a LONG pivot low, closing high in its range
                    (cp_hi if cp >= 0.66 else cp_lo if cp <= 0.34 else []).append(r) \
                        if (cp >= 0.66 or cp <= 0.34) else None
                n_all = sum(len(v) for v in buckets.values())
                pm, ps = placebo(bars, side, max(n_all, 1))
                print(f"--- {sym} {mins}m {side}   n={n_all}   placebo mean {pm:+.4f} ATR (sd {ps:.4f})")
                for name in ("HIGH", "MID", "LOW"):
                    v = buckets[name]
                    if len(v) < 10:
                        print(f"      {name:<5} n={len(v):<5} too few"); continue
                    m, t = st.mean(v), tstat(v)
                    z_vs_placebo = (m - pm) / ps if ps and ps > 0 else float("nan")
                    win = 100 * sum(1 for x in v if x > 0) / len(v)
                    print(f"      {name:<5} n={len(v):<5} mean {m:+.4f} ATR   t={t:+.2f}   "
                          f"win {win:4.1f}%   z vs placebo {z_vs_placebo:+.2f}")
                    rows.append((sym, mins, side, name, len(v), m, t, z_vs_placebo))
                h, l = buckets["HIGH"], buckets["LOW"]
                if len(h) >= 10 and len(l) >= 10:
                    diff = st.mean(h) - st.mean(l)
                    se = math.sqrt(st.pstdev(h)**2/len(h) + st.pstdev(l)**2/len(l))
                    print(f"      HIGH-minus-LOW  {diff:+.4f} ATR   t={diff/se if se>0 else float('nan'):+.2f}"
                          f"   <-- THE HYPOTHESIS")
                if len(cp_hi) >= 10 and len(cp_lo) >= 10:
                    d2 = st.mean(cp_hi) - st.mean(cp_lo)
                    se2 = math.sqrt(st.pstdev(cp_hi)**2/len(cp_hi) + st.pstdev(cp_lo)**2/len(cp_lo))
                    print(f"      close-pos proxy: favourable({len(cp_hi)}) minus adverse({len(cp_lo)})"
                          f"  {d2:+.4f} ATR  t={d2/se2 if se2>0 else float('nan'):+.2f}  (PROXY, not delta)")
                print()
    best = max((abs(r[6]) for r in rows), default=float("nan"))
    print(f"largest |t| on any bucket: {best:.2f}   free_t for ONE pre-registered claim: 2.2293")
    print(f"cells examined: {len(rows)} -> the honest multiple-testing bar is well above that.")


if __name__ == "__main__":
    run()
