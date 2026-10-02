#!/usr/bin/env python3
"""LVN/FIB AGENT — desk status: account, per-arm running record, and each arm's measured prior."""
from __future__ import annotations

import json
import pathlib
import statistics as st
import sys
from collections import defaultdict

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "workspace" / "anchors" / "lib"))
import core                                   # noqa: E402

PRIOR = {
    ("MGC", "A"): ("ARMED",   "n=24  +0.2379R  t +1.027  win 50.0%  payoff 1.58"),
    ("MNQ", "A"): ("OBSERVE", "n=57  -0.2390R  t -1.932  (measured losing on MNQ)"),
    ("MGC", "B"): ("OBSERVE", "not separately measured on MGC"),
    ("MNQ", "B"): ("OBSERVE", "n=108 -0.0240R  t -0.213  (null)"),
}


def load(n):
    p = HERE / n
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def _newest_bar():
    """Newest 60m bar across the desk's symbols, and its age in minutes."""
    import datetime as _dt
    newest = None
    for sym in ("MGC", "MNQ"):
        try:
            t = core.tape(sym, 60)
        except Exception:                                  # noqa: BLE001
            continue
        ts = t.bars[-1].ts
        if newest is None or ts > newest:
            newest = ts
    if newest is None:
        return "unknown", None
    # Age from the bar's CLOSE, not its start: a 60m bar stamped 19:00 covers
    # 19:00-20:00, so measuring from the stamp makes a current bar look an hour stale.
    age = (_dt.datetime.now(newest.tzinfo) - newest).total_seconds() / 60 - 60
    return newest.isoformat(), max(age, 0.0)


def main():
    calls, res = load("callouts.jsonl"), load("resolutions.jsonl")
    s = (json.loads((HERE / "state.json").read_text()) if (HERE / "state.json").exists()
         else {"equity": core.ACCOUNT, "peak": core.ACCOUNT, "max_dd": 0.0, "closed": 0})
    print("=" * 78)
    print("LVN/FIB AGENT — MGC + MNQ — paper only")
    print("=" * 78)
    room = s["equity"] - (core.ACCOUNT - core.FLOOR_DD)
    print(f"equity ${s['equity']:,.2f}   peak ${s['peak']:,.2f}   max dd ${s.get('max_dd',0.0):,.2f}"
          f"   room to floor ${room:,.2f}   closed {s.get('closed',0)}")
    print(f"risk budget now  ${min(0.06*room, 0.0075*s['equity'], 500.0, core.RISK_CAP):,.2f}"
          f"   (cap ${core.RISK_CAP:,.0f} while nothing is proven)")
    by = defaultdict(list)
    for c in calls:
        by[c["status"]].append(c)
    print(f"\ncallouts: " + "  ".join(f"{k} {len(v)}" for k, v in sorted(by.items())) or "none")

    print("\nper-arm record so far, against the prior it was armed on:")
    print(f"{'arm':10s} {'gate':8s} {'n':>4s} {'avgR':>8s} {'won':>4s} {'lost':>5s} {'nofill':>7s}  measured prior")
    agg = defaultdict(list)
    for r in res:
        agg[(r["symbol"], r["arm"])].append(r)
    for k in sorted(set(list(PRIOR) + list(agg))):
        rs = agg.get(k, [])
        rv = [x["r"] for x in rs if x.get("r") is not None]
        gate, prior = PRIOR.get(k, ("OBSERVE", "—"))
        print(f"{k[0]+' '+k[1]:10s} {gate:8s} {len(rv):4d} "
              f"{(f'{st.fmean(rv):+8.4f}' if rv else '      --')} "
              f"{sum(1 for x in rs if x['outcome']=='TARGET'):4d} "
              f"{sum(1 for x in rs if x['outcome'] in ('STOP','BE')):5d} "
              f"{sum(1 for x in rs if x['outcome']=='NO_FILL'):7d}  {prior}")
    open_c = [c for c in calls if c["status"] in ("PENDING", "OBSERVE")
              and c["id"] not in {r["id"] for r in res}]
    if open_c:
        print("\nopen / unresolved:")
        for c in open_c:
            print(f"  {c['id']} {c['symbol']} arm {c['arm']} {c['side']} "
                  f"limit {c['limit_entry']} stop {c['stop']} target {c['target']} x{c['contracts']}")
    # This note used to be unconditional, so it claimed "yfinance absent" in the same
    # breath as a fetch that had just appended a bar. Report what is actually true.
    try:
        import yfinance  # noqa: F401
        feed = True
    except ModuleNotFoundError:
        feed = False
    newest, age_min = _newest_bar()
    if not feed:
        print("\nNOTE: no live feed in this container (yfinance absent). Levels come from "
              "data/archive/\n      and are stamped with their source bar. Nothing here is "
              "a current price.")
    else:
        print(f"\nNOTE: live feed on (yfinance). Newest closed 60m bar stamped {newest}"
              f"{'' if age_min is None else f' (closed {age_min:.0f} min ago)'}.")
        print("      Yahoo lags ~13 min at 5m and ~23 min at 15m and the newest 1-2 bars "
              "revise for\n      ~28 min, so a level is stamped with its source bar and is "
              "still not a live quote.")


if __name__ == "__main__":
    main()
