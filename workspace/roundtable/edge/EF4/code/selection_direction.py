"""EF4 - is the top 10's advantage just "the market went up"?

`selection_control.py` shows the in-sample top 10 beats the universe out of sample at
percentile >= 0.96 against both a random-10 and a trade-count-matched-10 control in 3 of 4
cells - AND that selecting on the LATER half and scoring the EARLIER half wins just as well.
Winning in both directions of time means the property being selected is stationary across the
window, not persistent into the future. The obvious candidate for a stationary property is
**direction**: over this 58-day window MGC ran 4151 -> 4321 (+4.1%) and MCL 84.63 -> 92.41
(+9.2%), so a long-biased arm is favoured in BOTH halves for a reason that has nothing to do
with the rule it encodes.

This measures the long share of the in-sample top 10's realised trades against the long share
of the qualifying universe, per cell. If the top 10 are long-biased and the universe is not,
the selection effect is a drift artefact and must be reported as one.

Control included: the same comparison on SHORT-only and LONG-only versions of the same arms,
which separates "this rule has an edge" from "this rule happened to be pointing the right way".
"""
from __future__ import annotations

import json
import statistics as st
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path("/home/user/Futures01")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF1/code"))
sys.path.insert(0, str(ROOT / "workspace/roundtable/edge/EF4/code"))

from futures_agents.backtest.costs import CostModel   # noqa: E402
from futures_agents.config import get_contract        # noqa: E402
from futures_agents.schema import Direction           # noqa: E402
from session_window import SessionWindowEngine        # noqa: E402
from population import build_track_b, assert_unique   # noqa: E402
from run_cell import frame_for, metrics               # noqa: E402

OUT = ROOT / "workspace/roundtable/edge/EF4/out"
LONG, SHORT = frozenset({Direction.LONG}), frozenset({Direction.SHORT})

rows = []
for sym in ("MGC", "MCL"):
    spec = get_contract(sym)
    cost = CostModel(spec)
    for tf in (5, 15, 30):
        rp = OUT / f"run_{sym}_{tf}m_both.json"
        if not rp.is_file():
            continue
        d = json.loads(rp.read_text())
        uni = [r for r in d["rows"] if r["group"] == "EF4_SCREEN"
               and r["is"]["trades"] >= 30 and r["oos"]["trades"] >= 30]
        if len(uni) < 40:
            continue
        top = sorted(uni, key=lambda r: -r["is"]["expectancy_net_r"])[:10]
        want = {r["name"] for r in top}
        frame = frame_for(sym, tf)
        allb = build_track_b(sym, tf)
        base = [s for s in allb if s.name in want]
        # a random-40 comparison group, drawn deterministically from the universe
        import random
        rng = random.Random(77)
        # must not overlap `base` - the D48 uniqueness assertion caught exactly this
        # collision on the first run, which is the guard doing its job rather than
        # decorating the code.
        pool = [r for r in uni if r["name"] not in want]
        others = [s for s in allb
                  if s.name in {r["name"] for r in rng.sample(pool, 40)}]
        longs = [replace(s, name=s.name + "#L", allowed_directions=LONG, _id=None)
                 for s in base]
        shorts = [replace(s, name=s.name + "#S", allowed_directions=SHORT, _id=None)
                  for s in base]
        arms = base + longs + shorts + others
        assert_unique(arms, f"dir {sym} {tf}m")
        eng = SessionWindowEngine(frame, cost)
        res = eng.run_many(arms)

        def dirmix(s):
            r = res.get(s.strategy_id)
            if r is None or not r.trades:
                return None
            n = len(r.trades)
            lo = sum(1 for t in r.trades if t.direction.sign > 0)
            m = metrics(r, spec, cost)
            return {"trades": n, "long_share": lo / n,
                    "expectancy_net_r": m["expectancy_net_r"]}

        tm = [x for x in (dirmix(s) for s in base) if x]
        om = [x for x in (dirmix(s) for s in others) if x]
        lm = [x for x in (dirmix(s) for s in longs) if x]
        sm = [x for x in (dirmix(s) for s in shorts) if x]
        row = {
            "symbol": sym, "tf": tf,
            "top10_long_share": st.mean(x["long_share"] for x in tm) if tm else None,
            "random40_long_share": st.mean(x["long_share"] for x in om) if om else None,
            "top10_expectancy_full": st.mean(x["expectancy_net_r"] for x in tm) if tm else None,
            "random40_expectancy_full": st.mean(x["expectancy_net_r"] for x in om) if om else None,
            "top10_LONG_only_expectancy": st.mean(x["expectancy_net_r"] for x in lm) if lm else None,
            "top10_SHORT_only_expectancy": st.mean(x["expectancy_net_r"] for x in sm) if sm else None,
            "top10_LONG_only_trades": sum(x["trades"] for x in lm),
            "top10_SHORT_only_trades": sum(x["trades"] for x in sm),
        }
        rows.append(row)
        print(f"{sym} {tf:>2}m  top10 long share {row['top10_long_share']:.3f} vs "
              f"random-40 {row['random40_long_share']:.3f}   "
              f"E(top10)={row['top10_expectancy_full']:+.4f} "
              f"E(rand40)={row['random40_expectancy_full']:+.4f}   "
              f"top10 LONG-only {row['top10_LONG_only_expectancy']:+.4f} "
              f"(n={row['top10_LONG_only_trades']})  "
              f"SHORT-only {row['top10_SHORT_only_expectancy']:+.4f} "
              f"(n={row['top10_SHORT_only_trades']})")

p = OUT / "selection_direction.json"
p.write_text(json.dumps(rows, indent=2))
print(f"\nwrote {p}")
