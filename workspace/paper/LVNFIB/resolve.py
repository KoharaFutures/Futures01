#!/usr/bin/env python3
"""LVN/FIB AGENT — resolve posted callouts against bars that closed after them.

Resolution runs through `core._walk`, the SAME engine that measured every prior in CHARTER.md §1,
including its fill-bar rule (a resting limit gets no target credit on the bar it filled). If the
desk resolved trades on a friendlier engine than the backtest, the comparison would be worthless.

Append-only: a resolution is a new line in resolutions.jsonl. Callouts are never edited.
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "workspace" / "anchors" / "lib"))
import core                                   # noqa: E402

CALLOUTS = HERE / "callouts.jsonl"
RESOLUTIONS = HERE / "resolutions.jsonl"
STATE = HERE / "state.json"
LIMIT_BARS = 2


def load(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def main():
    calls = load(CALLOUTS)
    done = {r["id"] for r in load(RESOLUTIONS)}
    st = (json.loads(STATE.read_text()) if STATE.exists()
          else {"equity": core.ACCOUNT, "peak": core.ACCOUNT, "max_dd": 0.0, "closed": 0})
    tapes, out = {}, []
    for c in sorted(calls, key=lambda c: c["as_of_bar"]):
        if c["id"] in done or c["status"] == "WATCHING":
            continue
        sym = c["symbol"]
        t = tapes.setdefault(sym, core.tape(sym, 60))
        idx = next((i for i, b in enumerate(t.bars) if b.ts.isoformat() == c["as_of_bar"]), None)
        if idx is None or idx + 1 >= len(t.bars):
            print(f"  {c['id']}  STILL OPEN (no bar after {c['as_of_bar']})")
            continue
        side = 1 if c["side"] == "LONG" else -1
        tr = core._walk(t, idx, side, c["limit_entry"], limit_px=c["limit_entry"],
                        limit_bars=LIMIT_BARS)
        if tr is None:
            res = {"id": c["id"], "symbol": sym, "arm": c["arm"], "outcome": "NO_FILL",
                   "r": None, "pnl_usd": 0.0, "contracts": c["contracts"],
                   "note": f"limit at {c['limit_entry']} not reached within {LIMIT_BARS} bars"}
        else:
            pnl = tr.r * tr.risk * t.spec.point_value * c["contracts"]
            res = {"id": c["id"], "symbol": sym, "arm": c["arm"],
                   "outcome": tr.why.upper(), "r": round(tr.r, 4),
                   "fill": tr.fill, "exit_px": tr.exit_px,
                   "exit_bar": t.bars[tr.exit_i].ts.isoformat(),
                   "risk_points": round(tr.risk, 4), "contracts": c["contracts"],
                   "pnl_usd": round(pnl, 2)}
            if c["contracts"]:
                st["equity"] = round(st["equity"] + pnl, 2)
                st["peak"] = max(st["peak"], st["equity"])
                st["max_dd"] = round(max(st.get("max_dd", 0.0), st["peak"] - st["equity"]), 2)
                st["closed"] = st.get("closed", 0) + 1
        out.append(res)
        print(f"  {res['id']}  {res['outcome']:8s} r={res['r']} "
              f"x{res['contracts']} pnl ${res['pnl_usd']}")
    if out:
        with RESOLUTIONS.open("a") as f:
            for r in out:
                f.write(json.dumps(r, default=str) + "\n")
        STATE.write_text(json.dumps(st, indent=1))
    print(f"\nresolved {len(out)} | equity ${st['equity']:,.2f} peak ${st['peak']:,.2f} "
          f"max dd ${st.get('max_dd',0.0):,.2f} floor ${core.FLOOR_DD:,.0f} | closed {st.get('closed',0)}")


if __name__ == "__main__":
    main()
