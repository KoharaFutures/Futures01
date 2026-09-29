"""EF4 - does requiring multi-timeframe alignment change the outcome? A declared paired test.

BRIEF rule 2 says requiring any alignment measured detectably *worse* than requiring none
(z = -4.09), and the independence rules say the question is answered with data rather than
assumed. My census (burst 03) shows why it could not be asked on a single-timeframe frame:
``mtf_aligned`` and ``mtf_strongly_aligned`` are **0/N in all six single-tf cells**, and
``mtf_not_conflicted`` fires on **100.00%** of their bars. On a frame of one, the family
either kills the strategy or is a no-op. So the test needs a frame of three.

Design, declared before running:

* frame = 5 + 15 + 30 on a 5-minute base, both symbols.
* arms = Track A's six hypotheses, each in two versions: **without** and **with**
  ``mtf_aligned`` added as a second SIGNAL. Adding a SIGNAL means direction must agree, which
  is precisely "require alignment".
* n = 6 hypotheses x 2 symbols = **12 pre-registered pairs.** Not a search.
* test = **Wilcoxon signed-rank on the 12 paired differences in net expectancy**, plus a
  plain sign test. Named explicitly, and NOT ``T.ab`` - D28 records that inflating z ~3.3x.
* Both arms run in ONE ``run_many`` pass over the same frame, so they see identical bars.
* ``_id=None`` on the replace and an arm-id uniqueness assertion (D48). Without it the two
  arms collide into one ``BacktestResult`` and the difference is exactly zero, which is
  indistinguishable from "alignment makes no difference" - the hypothesis under test.
"""
from __future__ import annotations

import json
import math
import statistics as st
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF1/code"))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF4/code"))

from futures_agents.backtest.costs import CostModel    # noqa: E402
from futures_agents.config import get_contract         # noqa: E402
from futures_agents.data.archive import BarArchive      # noqa: E402
from futures_agents.features import SymbolFrame         # noqa: E402
from futures_agents.strategies.library import CONDITIONS  # noqa: E402
from session_window import SessionWindowEngine          # noqa: E402
from population import build_track_a, assert_unique     # noqa: E402
from run_cell import metrics                            # noqa: E402


def wilcoxon(diffs):
    """Two-sided Wilcoxon signed-rank, normal approximation with tie correction.

    At n = 12 the normal approximation is rough; the exact-test caveat is stated in the
    write-up rather than hidden. The sign test is reported beside it as a distribution-free
    check that needs no approximation at all.
    """
    d = [x for x in diffs if abs(x) > 1e-12]
    n = len(d)
    if n < 3:
        return {"n": n, "W": None, "z": None, "p_approx": None}
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    wp = sum(ranks[i] for i in range(n) if d[i] > 0)
    wm = sum(ranks[i] for i in range(n) if d[i] < 0)
    W = min(wp, wm)
    mu = n * (n + 1) / 4.0
    sd = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    z = (W - mu) / sd if sd else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    return {"n": n, "W_plus": wp, "W_minus": wm, "W": W, "z": z, "p_approx": p}


rows = []
for sym in ("MGC", "MCL"):
    spec = get_contract(sym)
    series = BarArchive(str(ROOT / "data/archive")).load(sym, 5)
    frame = SymbolFrame(series, (5, 15, 30))
    base = build_track_a(sym, 5)
    aligned = [replace(s, name=f"{s.name}+MTF",
                       conditions=s.conditions + (CONDITIONS["mtf_aligned"],),
                       _id=None) for s in base]
    arms = base + aligned
    assert_unique(arms, f"mtf {sym}")
    eng = SessionWindowEngine(frame, CostModel(spec))
    res = eng.run_many(arms)
    for b, a in zip(base, aligned):
        mb = metrics(res[b.strategy_id], spec, CostModel(spec))
        ma = metrics(res[a.strategy_id], spec, CostModel(spec))
        rows.append({
            "symbol": sym, "hypothesis": b.name,
            "plain_trades": mb.get("trades", 0),
            "aligned_trades": ma.get("trades", 0),
            "plain_expectancy_net_r": mb.get("expectancy_net_r", 0.0),
            "aligned_expectancy_net_r": ma.get("expectancy_net_r", 0.0),
            "delta": ma.get("expectancy_net_r", 0.0) - mb.get("expectancy_net_r", 0.0),
            "trade_retention": (ma.get("trades", 0) / mb["trades"]) if mb.get("trades") else 0.0,
            "plain_id": b.strategy_id, "aligned_id": a.strategy_id,
        })

print(f"{'arm':<28}{'n plain':>9}{'n align':>9}{'retain':>8}"
      f"{'E plain':>10}{'E align':>10}{'delta':>10}")
for r in rows:
    print(f"{r['symbol']+' '+r['hypothesis']:<28}{r['plain_trades']:>9}"
          f"{r['aligned_trades']:>9}{r['trade_retention']:>8.2f}"
          f"{r['plain_expectancy_net_r']:>+10.4f}{r['aligned_expectancy_net_r']:>+10.4f}"
          f"{r['delta']:>+10.4f}")

usable = [r for r in rows if r["plain_trades"] >= 20 and r["aligned_trades"] >= 20]
diffs = [r["delta"] for r in usable]
w = wilcoxon(diffs)
pos = sum(1 for d in diffs if d > 0)
print(f"\npairs with >=20 trades on BOTH arms: {len(usable)} of {len(rows)}")
if diffs:
    print(f"mean delta = {st.mean(diffs):+.4f}R   median = {st.median(diffs):+.4f}R   "
          f"positive {pos}/{len(diffs)}")
    print(f"Wilcoxon signed-rank: {w}")
    print(f"sign test: {pos} of {len(diffs)} positive "
          f"(two-sided binomial p = "
          f"{2*sum(math.comb(len(diffs),k) for k in range(0,min(pos,len(diffs)-pos)+1))/2**len(diffs):.4f})")
    print(f"mean trade retention when alignment is required: "
          f"{st.mean([r['trade_retention'] for r in usable]):.2f}")

p = ROOT / "workspace/roundtable/edge/EF4/out/mtf_arms.json"
p.write_text(json.dumps({"rows": rows, "usable_pairs": len(usable),
                         "mean_delta": (st.mean(diffs) if diffs else None),
                         "wilcoxon": w, "positive": pos, "n_diffs": len(diffs)}, indent=2))
print(f"\nwrote {p}")
