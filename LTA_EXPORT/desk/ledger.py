#!/usr/bin/env python3
"""LTA CONCEPT CALLOUTS — resolve posted callouts against later bars, and report the record.

    python3 desk/ledger.py            # resolve what can be resolved, then status
    python3 desk/ledger.py --status   # status only

Resolution (pessimistic, deterministic):
  * entry is assumed filled at entry_price on the first 5m bar after the callout that trades
    through it (a market callout quoted from a fetched price fills on the next bar);
    unfilled by 16:00 ET the same session -> EXPIRED, no P&L
  * then the first of stop / target, bar by bar on 5m; a bar that touches both = STOP
  * CONTRARIAN: stop moves to entry once +1R is touched (book p229), on the NEXT bar
  * still open at the 15:55 bar -> closed at that bar's close (flat by 16:00)
  * P&L in $ = R x risk_pts x point_value x contracts - round-turn cost x contracts
Writes resolutions.jsonl (append-only). Win rate is always printed with payoff (CLAUDE.md #7).
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, time

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from lta_common import load, tday, get_contract            # noqa: E402

JOURNAL = HERE / "callouts.jsonl"
RESOLVED = HERE / "resolutions.jsonl"
START_EQUITY = 50_000.0
FLOOR_DD = 2_800.0


def _read(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def _key(c):
    return f"{c['ts']}|{c['symbol']}|{c['side']}"


def resolve_one(c):
    spec = get_contract(c["symbol"])
    bars = load(c["symbol"], 5)
    t0 = datetime.fromisoformat(c["ts_et"])
    sess = tday(t0)
    side = 1 if c["side"] == "LONG" else -1
    e, s, tgt, risk = c["entry_price"], c["initial_stop"], c["target"], c["risk_pts"]
    after = [b for b in bars if b.ts > t0]
    filled_at, stop, be_armed = None, s, False
    for b in after:
        if tday(b.ts) != sess or b.ts.time() >= time(16, 0) and b.ts.time() < time(18, 0):
            if filled_at is None:
                return {"outcome": "EXPIRED", "r": 0.0, "pnl": 0.0, "bar": b.ts.isoformat()}
            r = side * (b.o - e) / risk
            return _close(c, spec, "FLAT_1600", r, b.ts)
        if filled_at is None:
            if b.l <= e <= b.h:
                filled_at = b.ts
            continue
        if be_armed:
            stop = e
        hit_stop = (b.l <= stop) if side == 1 else (b.h >= stop)
        hit_tgt = (b.h >= tgt) if side == 1 else (b.l <= tgt)
        if hit_stop:
            return _close(c, spec, "BREAKEVEN" if stop == e else "STOP", side * (stop - e) / risk, b.ts)
        if hit_tgt:
            return _close(c, spec, "TARGET", side * (tgt - e) / risk, b.ts)
        if c.get("archetype") == "CONTRARIAN" and side * ((b.h if side == 1 else b.l) - e) >= risk:
            be_armed = True
        if b.ts.time() >= time(15, 55) and b.ts.time() < time(16, 0):
            return _close(c, spec, "FLAT_1600", side * (b.c - e) / risk, b.ts)
    return None          # still open, or the data has not reached the outcome yet


def _close(c, spec, how, r, ts):
    n = c["contracts"]
    pnl = r * c["risk_pts"] * spec.point_value * n - spec.round_turn_cost * n
    return {"outcome": how, "r": round(r, 3), "pnl": round(pnl, 2), "bar": ts.isoformat()}


def resolve_all():
    done = {x["key"] for x in _read(RESOLVED)}
    new = []
    for c in _read(JOURNAL):
        if c.get("verdict") == "NO_TRADE" or _key(c) in done:
            continue
        r = resolve_one(c)
        if r:
            r.update(key=_key(c), id=c.get("id"), symbol=c["symbol"], side=c["side"], model=c.get("model"),
                     archetype=c.get("archetype"), session_day=str(tday(datetime.fromisoformat(c["ts_et"]))),
                     resolved_utc=datetime.utcnow().isoformat(timespec="seconds") + "Z")
            new.append(r)
    if new:
        with RESOLVED.open("a") as f:
            for r in new:
                f.write(json.dumps(r) + "\n")
    return new


def account():
    eq = peak = START_EQUITY
    for r in _read(RESOLVED):
        eq += r["pnl"]
        peak = max(peak, eq)
    dd = peak - eq
    return {"equity": round(eq, 2), "peak": round(peak, 2), "drawdown": round(dd, 2),
            "room_to_floor": round(FLOOR_DD - dd, 2)}


def today_record(day):
    rs = [r for r in _read(RESOLVED) if r.get("session_day") == str(day) and r["outcome"] != "EXPIRED"]
    rs = sorted(rs, key=lambda r: r["bar"])          # in the order the trades actually closed
    net = sum(r["pnl"] for r in rs)
    # book p222: two losses in a row ends the day; a later win does not reopen it
    two = any(a["r"] < 0 and b["r"] < 0 for a, b in zip(rs, rs[1:]))
    last_loss = next(({"symbol": r["symbol"], "side": r["side"]} for r in reversed(rs) if r["r"] < 0), None)
    return {"trades": len(rs), "net": round(net, 2), "halt": bool(two and net <= 0),
            "why": "last two resolved trades today both lost and the day is not green" if two and net <= 0 else "",
            "last_loss": last_loss}


def stats(rs):
    n = len(rs)
    if not n:
        return "n=0"
    w = [r["r"] for r in rs if r["r"] > 0]
    l = [-r["r"] for r in rs if r["r"] < 0]
    pay = (sum(w) / len(w)) / (sum(l) / len(l)) if w and l else float("nan")
    return (f"n={n} · win {100 * len(w) / n:.0f}% · payoff {pay:.2f} · avg {sum(r['r'] for r in rs) / n:+.3f}R "
            f"· ${sum(r['pnl'] for r in rs):+,.2f}")


def status():
    rs = [r for r in _read(RESOLVED) if r["outcome"] != "EXPIRED"]
    acct = account()
    posted = [c for c in _read(JOURNAL) if c.get("verdict") != "NO_TRADE"]
    done = {r["key"] for r in _read(RESOLVED)}
    L = ["LTA CONCEPT CALLOUTS — paper record (no placebo yet: a record, not an edge)",
         f"equity ${acct['equity']:,.2f} · peak ${acct['peak']:,.2f} · drawdown ${acct['drawdown']:,.2f} · "
         f"room to the $2,800 floor ${acct['room_to_floor']:,.2f}",
         f"callouts posted {len(posted)} · resolved {len(rs)} · open/unresolved {len([c for c in posted if _key(c) not in done])} · "
         f"NO_TRADE cards {len(_read(JOURNAL)) - len(posted)}",
         f"all: {stats(rs)}"]
    for k in ("archetype", "model", "symbol"):
        g = defaultdict(list)
        for r in rs:
            g[r.get(k)].append(r)
        for v, xs in sorted(g.items(), key=lambda kv: str(kv[0])):
            L.append(f"  {k} {v}: {stats(xs)}")
    if len(rs) < 30:
        L.append(f"book p222/p237: the first 30 rule-following trades decide whether size may ever rise — {len(rs)}/30")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--status", action="store_true")
    a = ap.parse_args()
    if not a.status:
        for r in resolve_all():
            print(f"resolved {r['key']}: {r['outcome']} {r['r']:+}R ${r['pnl']:+,.2f}")
    print(status())


if __name__ == "__main__":
    main()
