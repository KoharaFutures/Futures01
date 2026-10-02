#!/usr/bin/env python3
"""LVN/FIB AGENT — post callouts. Arm A can risk the account; B, C, D are observe-only.

A callout is written once and never edited (resolve.py appends). Ids are asserted unique, the
same guard the other paper desks use.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "workspace" / "anchors" / "lib"))
import core                                   # noqa: E402
import engine                                 # noqa: E402

CALLOUTS = HERE / "callouts.jsonl"
STATE = HERE / "state.json"
ARMED = {("MGC", "A")}        # the only arm allowed to risk the account - CHARTER.md §1
LIMIT_BARS = 2


def state():
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"equity": core.ACCOUNT, "peak": core.ACCOUNT, "closed": 0, "resolved_ids": []}


def budget(st):
    room = st["equity"] - (core.ACCOUNT - core.FLOOR_DD)
    if room <= 0:
        return 0.0
    return min(0.06 * room, 0.0075 * st["equity"], 500.0, core.RISK_CAP)


def existing_ids():
    if not CALLOUTS.exists():
        return set()
    return {json.loads(l)["id"] for l in CALLOUTS.read_text().splitlines() if l.strip()}


def mk_id(sym, arm, bar, price):
    h = hashlib.sha256(f"{sym}|{arm}|{bar}|{price:.6f}".encode()).hexdigest()[:10]
    return f"LF-{sym}-{arm}-{h}"


def triggered(snap, grp, lvl, t, i):
    """The bar traded into the level and closed against the anchor leg's direction."""
    b = t.bars[i]
    p = lvl["price"]
    if not (b.l <= p <= b.h):
        return False
    return (b.c > p) if lvl["trade_side"] == "LONG" else (b.c < p)


def build(sym, st, dry):
    snap = engine.snapshot(sym)
    t = core.tape(sym, 60)
    i = len(t.bars) - 1
    atr = snap["atr14_60m"]
    out = []
    for arm, key in (("A", "arm_A_prior_week_golden"), ("B", "arm_B_overnight_shallow")):
        grp = snap.get(key)
        if not grp:
            continue
        for lvl in grp["levels"]:
            armed = (sym, arm) in ARMED
            side = 1 if lvl["trade_side"] == "LONG" else -1
            risk_pts = max(core.STOP_ATR * atr + t.tick, t.min_stop)
            risk_usd = risk_pts * t.spec.point_value
            bud = budget(st)
            reasons = []
            if not armed:
                reasons.append("OBSERVE_ONLY: arm not armed (CHARTER.md §1)")
            if lvl["stacked_with"]:
                reasons.append(f"STACKED within 0.25 ATR of {lvl['stacked_with']}")
            if snap["vol_standdown_active"]:
                reasons.append(f"VOL_STANDDOWN: ATR14(15m) {snap['atr14_15m']} > {snap['vol_standdown_threshold']}")
            if armed and risk_usd > bud:
                reasons.append(f"REFUSED_SIZE: risk ${risk_usd:.2f} > budget ${bud:.2f}")
            fired = triggered(snap, grp, lvl, t, i)
            out.append({
                "id": mk_id(sym, arm, snap["newest_bar"], lvl["price"]),
                "desk": "LVNFIB", "symbol": sym, "arm": arm,
                "rule": {"A": "fib trend-failure, prior-week golden pocket, resting limit",
                         "B": "fib trend-failure, overnight range 0.382/0.5, resting limit"}[arm],
                "status": ("PENDING" if (fired and armed and not reasons) else
                           "OBSERVE" if fired else "WATCHING"),
                "side": lvl["trade_side"], "frac": lvl["frac"],
                "limit_entry": round(lvl["price"], 4), "limit_good_for_bars": LIMIT_BARS,
                "stop": round(lvl["price"] - side * risk_pts, 4),
                "target": round(lvl["price"] + side * core.TARGET_R * risk_pts, 4),
                "risk_points": round(risk_pts, 4), "risk_usd": round(risk_usd, 2),
                "budget_usd": round(bud, 2), "contracts": (1 if (armed and risk_usd <= bud) else 0),
                "anchor": {k: grp[k] for k in grp if k != "levels"},
                "as_of_bar": snap["newest_bar"], "as_of_close": snap["newest_close"],
                "atr14_60m": atr, "triggered_on_this_bar": fired,
                "measured_prior": {"A": "OOS n=24 +0.2379R t +1.027 (under its 2.327 bar)",
                                   "B": "OOS n=108 -0.0240R t -0.213 (null)"}[arm],
                "notes": reasons,
                # Was hardcoded "no live feed in this container", which became false the
                # moment yfinance was installed: callouts stamped with a live bar still
                # claimed the feed was absent. State the bar and the lag, not a guess.
                "feed_warning": ("newest bar " + str(snap["newest_bar"])
                                 + ("; live feed on, but Yahoo lags and the newest 1-2 bars "
                                    "revise for ~28 min" if _feed_on()
                                    else "; NO LIVE FEED (yfinance absent) - reading data/archive/")),
            })
    return out


def _feed_on() -> bool:
    try:
        import yfinance  # noqa: F401
        return True
    except ModuleNotFoundError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true", help="append to callouts.jsonl")
    a = ap.parse_args()
    st = state()
    rows = [r for s in engine.SYMS for r in build(s, st, not a.post)]
    have = existing_ids()
    new = [r for r in rows if r["id"] not in have]
    ids = [r["id"] for r in new]
    assert len(ids) == len(set(ids)), "callout id uniqueness assertion FIRED"
    for r in rows:
        tag = r["status"]
        print(f"[{tag:9s}] {r['symbol']} arm {r['arm']} {r['side']:5s} fib{r['frac']:g} "
              f"limit {r['limit_entry']} stop {r['stop']} target {r['target']} "
              f"risk ${r['risk_usd']:.2f}/bud ${r['budget_usd']:.2f} x{r['contracts']}"
              + (f"  <- {'; '.join(r['notes'])}" if r["notes"] else ""))
    if a.post:
        with CALLOUTS.open("a") as f:
            for r in new:
                f.write(json.dumps(r, default=str) + "\n")
        print(f"\nposted {len(new)} new callout(s); {len(rows)-len(new)} already on file")
    else:
        print(f"\ndry run — {len(new)} would be posted. Use --post to write them.")


if __name__ == "__main__":
    main()
