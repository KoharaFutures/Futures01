#!/usr/bin/env python3
"""Build a complete CALL plan from a setup, run every desk gate, size it. The agent only says yes or no.

A plan used to take the desk agent ~30 lines of hand-written prose: entry basis, stop basis, sizing
basis, book note, RTH note, expiry basis, invalidation. This script writes all the MECHANICAL parts
from the rules the hub measured, and refuses the plan outright when a hard rule fails:

  GATES (any failure => REFUSED, with the reason and the rule it comes from)
    G1 volatility stand-down    ATR14(15m) > 58 MNQ / 10 MGC (N214)
    G2 no late entries          now or the entry window inside 15:00-18:00 ET (z -4.43, owner's 16:00 flat)
    G3 no breakout chasing      a STOP entry in the direction of the move (CONT-1: worse than placebo 4/4)
    G4 stop floor               stop distance >= 0.5 ATR14(15m) and >= the contract's min_stop_ticks
    G5 reward:risk              TP1 in R >= desk-config min_reward_risk (1.6), measured after costs
    G6 book room                risk <= 50% cap - (open + pending risk) (N249). Contracts are sized from the room
    G7 drawdown floor           drawdown < $2,600
    G8 max 3 per symbol         at most 3 PENDING/open plans on the same symbol (owner, 2026-09-29; was 1)

  CONTEXT (attached, never a gate): nearest hub levels and their measured history vs placebo, the LVN
  continuation/bounce lean, the 15m regime, and whether the entry sits on a STACKED level (measured
  worst place to rest an order, z -5.1).

    python3 plan_builder.py --symbol MGC --side LONG --entry 4150 --stop-beyond 4143.0 --why "..."
    python3 plan_builder.py --symbol MNQ --side SHORT --entry 30550 --stop 30576 --tp-r 1.6 --commit
    python3 plan_builder.py --from-signal signal.json            # a rule signal from desk_check.py

Without --commit it only prints and writes drafts/<id>.json. With --commit it appends the plan to
pending.jsonl as PENDING. resolve.py then owns it, exactly as for a hand-written plan.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import pathlib
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from futures_agents.config import CONTRACTS  # noqa: E402

ET = ZoneInfo("America/New_York")
CFG = json.loads((ROOT / "desk" / "desk-config.json").read_text())["account"]
STANDDOWN = {"MGC": 10.0, "MNQ": 80.0}   # owner 2026-09-29 13:55 ET: was 58
FLOOR = 2600.0
MAX_PER_SYMBOL = 3   # owner 2026-09-29 19:12 ET (was 1)
RTH_OPEN = {"MNQ": "09:30", "MES": "09:30", "MGC": "08:20", "MCL": "09:00"}


def _mod(name):
    spec = importlib.util.spec_from_file_location(f"pb_{name}", HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def tick_round(sym, px):
    t = CONTRACTS[sym].tick_size
    return round(round(px / t) * t, 6)


def next_call_id() -> str:
    ids = []
    for f in ("pending.jsonl", "journal.jsonl"):
        p = HERE / f
        if p.exists():
            for l in p.read_text().splitlines():
                if '"CALL-' in l:
                    try:
                        cid = json.loads(l).get("call_id") or ""
                    except json.JSONDecodeError:
                        continue
                    tail = cid.split("-")[1] if cid.startswith("CALL-") else ""
                    if tail.isdigit():
                        ids.append(int(tail))
    return f"CALL-{max(ids, default=0) + 1:04d}"


def hub_context(sym, entry, atr):
    """Nearest hub levels to the entry, their measured record vs fake levels, and stacking."""
    out, near = {}, []
    lv = ROOT / "DATA_HUB" / "levels"
    try:
        for r in json.loads((lv / f"{sym}_bounce.json").read_text()):
            for x in r["current"]["levels"]:
                d = abs(x["price"] - entry) / atr
                if d <= 0.5:
                    h = x["history"]["touch"]
                    near.append({"src": f"{r['tf']}m {x['level']}", "price": x["price"], "dist_atr15": round(d, 2),
                                 "real": h.get("real"), "fake": h.get("placebo"), "z": h.get("z")})
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    try:
        for c in json.loads((lv / f"{sym}_volume_profile.json").read_text())["current"]:
            for x in c["lvn"]:
                d = abs(x["price"] - entry) / atr
                if d <= 0.5:
                    near.append({"src": f"LVN {c['window']}", "price": x["price"], "dist_atr15": round(d, 2),
                                 "lean": x.get("lean"), "history": x.get("history")})
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    prices = sorted({round(n["price"], 2) for n in near})
    out["near_levels"] = sorted(near, key=lambda n: n["dist_atr15"])[:8]
    out["stacked"] = len(prices) >= 3
    if out["stacked"]:
        out["stacked_warning"] = ("3+ hub levels within 0.5 ATR of the entry: stacked levels were measured the "
                                  "WORST place to rest an order (combined z -5.1, playbook §2). Expect a sweep first; "
                                  "prefer a reclaim entry or skip")
    return out


def build(a) -> dict:
    sym, side = a.symbol, a.side
    spec = CONTRACTS[sym]
    sc = _mod("status_card")
    rs = _mod("resolve")
    watch = _mod("watch")
    atr = sc.atr14(sym)
    bars15 = rs.load_bars(sym, 15)
    last = bars15[-1]
    now_et = (datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)).astimezone(ET)
    sign = 1 if side == "LONG" else -1
    entry = tick_round(sym, a.entry)
    trig_type = a.trigger_type or ("LIMIT_ENTRY_BUY" if side == "LONG" else "LIMIT_ENTRY_SELL")
    # stop: explicit, or 1 tick + max(0.25 ATR, sweep buffer) beyond a named structural level
    if a.stop is not None:
        stop = tick_round(sym, a.stop)
    elif a.stop_beyond is not None:
        stop = tick_round(sym, a.stop_beyond - sign * (0.25 * atr + spec.tick_size))
    else:
        stop = tick_round(sym, entry - sign * a.stop_atr * atr)
    stop_pts = round(abs(entry - stop), 6)
    floor_pts = max(0.5 * atr, spec.min_stop_ticks * spec.tick_size)
    gates, notes = [], []

    def gate(code, ok, why):
        gates.append({"gate": code, "pass": bool(ok), "why": why})

    gate("G1 stand-down", atr <= STANDDOWN.get(sym, 1e9), f"ATR14(15m) {atr:.2f} vs line {STANDDOWN.get(sym)}")
    t = now_et.hour * 60 + now_et.minute
    # owner 2026-09-29 17:53 ET: 17:50-18:00 is the PRE-OPEN review; plans drafted then can only fill after the
    # 18:00 reopen, so they are allowed. 15:00-17:50 stays closed.
    gate("G2 no late entries", not (15 * 60 <= t < 17 * 60 + 50), f"now {now_et:%H:%M} ET (no entries 15:00-17:50; 17:50-18:00 = pre-open planning)")
    moving_up = last["c"] > bars15[-4]["c"]
    chasing = trig_type.startswith("STOP") and ((side == "LONG") == moving_up)
    gate("G3 no breakout chasing", not chasing, "STOP entry in the direction of the last hour's move" if chasing
         else "not a with-move stop entry")
    gate("G4 stop floor", stop_pts >= floor_pts - 1e-9, f"stop {stop_pts:.2f} pts vs floor {floor_pts:.2f} "
         f"(0.5 ATR / {spec.min_stop_ticks} ticks)")
    cost_pts = (2 * (spec.commission_per_side + spec.exchange_fee_per_side)) / spec.point_value + 2 * spec.tick_size
    tp_r = a.tp_r
    net_rr = (tp_r * stop_pts - cost_pts) / (stop_pts + cost_pts) if stop_pts else 0
    gate("G5 reward:risk", net_rr >= CFG["min_reward_risk"] - 1e-9,
         f"TP1 {tp_r}R -> {net_rr:.2f} after costs ({cost_pts:.2f} pts) vs min {CFG['min_reward_risk']}")
    open_r, pend_r, labels = watch.committed()
    room = sc.CAP - open_r - pend_r
    per = stop_pts * spec.point_value
    n = int(room // per) if per > 0 else 0
    gate("G6 book room", n >= 1, f"one contract risks ${per:,.2f}; room ${room:,.2f} of the ${sc.CAP:.2f} "
         f"50% cap (open ${open_r:.2f} + pending ${pend_r:.2f})")
    state = json.loads((HERE / "state.json").read_text())
    gate("G7 drawdown floor", state.get("drawdown", 0) < FLOOR, f"drawdown ${state.get('drawdown', 0):,.2f} vs ${FLOOR:,.0f}")
    busy = [l for l in labels if f" {sym} " in f" {l} "] + [p.get("call_id") for p in state.get("open", [])
                                                            if p.get("symbol") == sym]
    # owner 2026-09-29 19:12 ET: "do 3 plans per symbol" (was 1). Pending + open both count.
    gate("G8 max 3 per symbol", len(busy) < MAX_PER_SYMBOL, f"{len(busy)} live on {sym}: {busy} (max {MAX_PER_SYMBOL})")
    dl = _mod("daily_loss")
    day_r = dl.day_realized(state)
    gate("G9 daily loss limit", day_r > -dl.DAILY_LOSS_LIMIT,
         f"today's realized ${day_r:,.2f} vs -${dl.DAILY_LOSS_LIMIT:,.0f} (trading day from 18:00 ET)")

    regime = _mod("regime")
    tfs = regime.timeframe_bias(sym)
    ctx = hub_context(sym, entry, atr)
    if ctx.get("stacked"):
        notes.append(ctx["stacked_warning"])
    # expiry: the earlier of --expiry-bars 15m bars or 15:00 ET (no late entries)
    exp = datetime.fromisoformat(last["ts"]) + timedelta(minutes=15 * a.expiry_bars)
    cut = exp.astimezone(ET).replace(hour=15, minute=0, second=0, microsecond=0)
    if exp.astimezone(ET) > cut and datetime.fromisoformat(last["ts"]).astimezone(ET) < cut:
        exp = cut
    tp_px = tick_round(sym, entry + sign * tp_r * stop_pts)
    ok = all(g["pass"] for g in gates)
    try:
        basis = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                               text=True).stdout.strip() or "unknown"
    except OSError:
        basis = "unknown"
    plan = {
        "call_id": next_call_id(), "symbol": sym, "side": side, "status": "PENDING", "bar_minutes": 15,
        "trigger_type": trig_type, "trigger_price": entry,
        "trigger_basis": a.entry_basis or f"{trig_type} at {entry} (market {last['c']} at bar {last['ts']})",
        "stop_points": stop_pts,
        "stop_basis": (f"Stop {stop} = {stop_pts:.2f} pts ({stop_pts / atr:.2f} ATR14(15m) {atr:.2f}); floor "
                       f"{floor_pts:.2f}" + (f"; 0.25 ATR + 1 tick beyond structure {a.stop_beyond}"
                                             if a.stop_beyond is not None else "")),
        "tp_r_multiples": [{"label": "TP1", "r": tp_r, "fraction": 1.0}],
        "display_targets": [{"label": "TP1", "r": tp_r, "executable": True}],
        "display_targets_note": f"TP1 {tp_px}",
        "contracts": max(n, 0) if ok else 0,
        "risk_dollars_intended": round(per * max(n, 1), 2) if ok else 0.0,
        "ladder_mult": 1.0,
        "sizing_basis": f"{stop_pts:.2f} pts x ${spec.point_value:g}/pt x {max(n, 0)} = ${per * max(n, 0):,.2f} "
                        f"inside room ${room:,.2f} (50% cap ${sc.CAP:.2f}, book {labels or 'empty'})",
        "confidence": a.confidence,
        "strategy": a.strategy,
        "strategy_basis": a.strategy_basis or "built by plan_builder.py; gates and sizing mechanical",
        "why": a.why,
        "invalidation": a.invalidation or f"A 15m CLOSE beyond {stop}; or no fill by {exp.isoformat()}",
        "book_note": f"book before this plan: {labels or 'empty'}",
        "rth_note": f"{sym} RTH opens {RTH_OPEN.get(sym)} ET; outside it is unmeasured territory",
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        # CALL-0013 (2026-09-29): created at 17:59 from data ending 15:15, so resolve.py filled it on a 15:45 bar
        # that printed BEFORE the plan existed (look-ahead). The creation stamp is now the 15m bar containing
        # "now", so only bars that open after the decision can fill it, however stale the local data is.
        "created_bar_ts": max(last["ts"], datetime.now(ET).replace(minute=(datetime.now(ET).minute // 15) * 15,
                              second=0, microsecond=0).isoformat()), "expires_bar_ts": exp.isoformat(),
        "expiry_basis": f"{a.expiry_bars} x 15m bars, never past 15:00 ET",
        "basis": basis, "as_of_at_creation": last["ts"], "paper": "PAPER - UNVALIDATED",
        "horizon": "INTRADAY",
        "builder": {"gates": gates, "notes": notes, "hub_context": ctx,
                    "regime_15m": next((t["headline"] for t in tfs if t["frame"] == 15), None),
                    "atr14_15m": round(atr, 3), "verdict": "READY" if ok else "REFUSED"},
    }
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--symbol", choices=sorted(STANDDOWN))
    ap.add_argument("--side", choices=("LONG", "SHORT"))
    ap.add_argument("--entry", type=float)
    ap.add_argument("--stop", type=float)
    ap.add_argument("--stop-beyond", type=float, help="structural level; stop = level -/+ (0.25 ATR + 1 tick)")
    ap.add_argument("--stop-atr", type=float, default=1.0)
    ap.add_argument("--tp-r", type=float, default=1.8, help="1.8R clears the 1.6 min after costs on normal stops")
    ap.add_argument("--trigger-type", choices=("LIMIT_ENTRY_BUY", "LIMIT_ENTRY_SELL", "STOP_ENTRY_BUY", "STOP_ENTRY_SELL"))
    ap.add_argument("--expiry-bars", type=int, default=8)
    ap.add_argument("--strategy", default="DISCRETIONARY level plan")
    ap.add_argument("--strategy-basis")
    ap.add_argument("--entry-basis")
    ap.add_argument("--invalidation")
    ap.add_argument("--confidence", default="DISCRETIONARY")
    ap.add_argument("--why", default="")
    ap.add_argument("--from-signal", help="JSON written by desk_check.py for a rule signal")
    ap.add_argument("--now")
    ap.add_argument("--commit", action="store_true")
    a = ap.parse_args()
    if a.from_signal:
        s = json.loads(pathlib.Path(a.from_signal).read_text())
        for k, v in s.get("plan_args", {}).items():
            setattr(a, k, v)
    if not (a.symbol and a.side and a.entry is not None):
        ap.error("--symbol, --side and --entry are required (or --from-signal)")
    plan = build(a)
    b = plan["builder"]
    print(f"{plan['call_id']} {plan['symbol']} {plan['side']} {plan['trigger_type']} @ {plan['trigger_price']}  "
          f"stop {plan['stop_points']} pts  {plan['display_targets_note']}  x{plan['contracts']}  "
          f"risk ${plan['risk_dollars_intended']}  -> {b['verdict']}")
    for g in b["gates"]:
        print(f"  {'PASS' if g['pass'] else 'FAIL'}  {g['gate']:24s} {g['why']}")
    for n in b["notes"]:
        print("  NOTE", n)
    for n in b["hub_context"]["near_levels"][:5]:
        print("  level", n)
    drafts = HERE / "drafts"
    drafts.mkdir(exist_ok=True)
    (drafts / f"{plan['call_id']}.json").write_text(json.dumps(plan, indent=1, default=str))
    if a.commit:
        if b["verdict"] != "READY":
            print("NOT COMMITTED: a hard gate failed.")
            return 1
        with (HERE / "pending.jsonl").open("a") as fh:
            fh.write(json.dumps({k: v for k, v in plan.items() if k != "builder"} | {"builder": b}, default=str) + "\n")
        print(f"COMMITTED {plan['call_id']} to pending.jsonl. resolve.py owns it from here.")
    return 0 if b["verdict"] == "READY" else 1


if __name__ == "__main__":
    sys.exit(main())
