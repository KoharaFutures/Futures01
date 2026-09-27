"""BT4 — the blast radius of the collapse beyond MULTI_TIMEFRAME.

The `multitimeframe` conditions are the obvious casualty, but they are carried by
one template. The collapse also reaches **every** 1440m strategy through a
channel nobody has counted: `_default_regime_tf`'s preference list
`(15, 30, 5, 60, 10, 3, 1)` misses every member of `[1440, 7200]` and falls
through to `return self.timeframes[-1]` (`features.py:820-826`), so
`SymbolFrame.regime_tf` is **7200** at the daily frame — the lagged copy.

`regime_at` then reads `classify_regime` off that copy, and because the copy's
OHLCV is the daily series bar for bar, the regime a daily strategy sees is its
own daily regime **2-4 sessions stale**.

That matters because `volatility_normal` is a base filter on 12 of 13 templates,
`regime_trending` is TREND's and `regime_ranging` is MEAN_REVERSION's. So this
measures the one number that bounds the non-MTF cost: on how many bars does the
stale regime differ from the on-timeframe one?

What this does NOT measure, and it is the honest gap: the *correct* counterfactual
at a fixed `align_bucket` is a genuine weekly regime, not the on-timeframe daily
one. A real weekly series cannot be built through `resample` while the collapse
stands, so the figures below bound the size of the discrepancy, not the sign of
the error.
"""
from __future__ import annotations

import collections
import os
from typing import Dict

from futures_agents.data.loader import load_csv
from futures_agents.features import SymbolFrame

REPO = os.path.dirname(os.path.abspath(__file__)).split("/workspace/")[0]
SYMS = {"MGC": "MGC_1d.csv", "MNQ": "MNQ_1d.csv", "MES": "MES_1d.csv"}


def compare(sym: str, fname: str) -> Dict[str, object]:
    daily = load_csv(os.path.join(REPO, "csv/raw", fname), sym, 1440)
    shipped = SymbolFrame(daily, [1440, 7200])                     # regime_tf -> 7200
    ontf = SymbolFrame(daily, [1440, 7200], regime_timeframe=1440)  # explicit override
    assert shipped.regime_tf == 7200 and ontf.regime_tf == 1440

    # The three base filters that read the regime channel, as their shipped
    # arithmetic: what matters to a strategy is the pass/veto decision, not the
    # label, and a label change inside one side of the gate costs nothing.
    GATES = {
        "volatility_normal": lambda r: r.volatility in ("LOW", "NORMAL", "HIGH"),
        "regime_trending": lambda r: r.regime in ("TREND_UP", "TREND_DOWN"),
        "regime_ranging": lambda r: r.regime == "RANGE",
    }

    n = len(daily)
    diff_regime = diff_vol = 0
    pairs = collections.Counter()
    vol_shipped = collections.Counter()
    vol_ontf = collections.Counter()
    gate_flip = collections.Counter()
    gate_pass_shipped = collections.Counter()
    gate_pass_ontf = collections.Counter()
    for i in range(n):
        a, b = shipped.regime_at(i), ontf.regime_at(i)
        vol_shipped[a.volatility] += 1
        vol_ontf[b.volatility] += 1
        if a.regime != b.regime:
            diff_regime += 1
            pairs[(b.regime, a.regime)] += 1
        if a.volatility != b.volatility:
            diff_vol += 1
        for name, gate in GATES.items():
            pa, pb = gate(a), gate(b)
            gate_pass_shipped[name] += pa
            gate_pass_ontf[name] += pb
            if pa != pb:
                gate_flip[name] += 1
    return {
        "gate_decision_flips": {k: f"{gate_flip[k]}/{n} = {100.0*gate_flip[k]/n:.2f}%"
                                for k in GATES},
        "gate_pass_rate_shipped_vs_on_timeframe":
            {k: f"{100.0*gate_pass_shipped[k]/n:.2f}% vs {100.0*gate_pass_ontf[k]/n:.2f}%"
             for k in GATES},
        "symbol": sym, "bars": n,
        "shipped_regime_tf": shipped.regime_tf,
        "regime_label_differs": f"{diff_regime}/{n} = {100.0*diff_regime/n:.2f}%",
        "volatility_label_differs": f"{diff_vol}/{n} = {100.0*diff_vol/n:.2f}%",
        "top_substitutions_on_timeframe_to_shipped":
            [f"{a} -> {b}: {c}" for (a, b), c in pairs.most_common(6)],
        "volatility_census_shipped": dict(vol_shipped.most_common()),
        "volatility_census_on_timeframe": dict(vol_ontf.most_common()),
    }


def main() -> int:
    for sym, fname in SYMS.items():
        r = compare(sym, fname)
        print(f"\n=== {sym} daily frame [1440, 7200], {r['bars']} bars")
        print(f"  shipped regime_tf: {r['shipped_regime_tf']} (the lagged copy)")
        print(f"  regime label differs from on-timeframe: {r['regime_label_differs']}")
        print(f"  volatility label differs:               {r['volatility_label_differs']}")
        print(f"  base-filter DECISION flips: {r['gate_decision_flips']}")
        print(f"  pass rate shipped vs on-tf: {r['gate_pass_rate_shipped_vs_on_timeframe']}")
        print(f"  substitutions (on-tf -> shipped): {r['top_substitutions_on_timeframe_to_shipped']}")
        print(f"  volatility shipped:      {r['volatility_census_shipped']}")
        print(f"  volatility on-timeframe: {r['volatility_census_on_timeframe']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
