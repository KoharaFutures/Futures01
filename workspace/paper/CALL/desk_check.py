#!/usr/bin/env python3
"""One deterministic CALL desk check. It replaces the every-2-minute LLM wake-up.

It runs every mechanical step of CHECK_PROCEDURE.md in the audited order
(DATA_HUB/sources/automation_audit_CALL.md §3), reusing the desk's own tools and never
re-implementing outcome logic:

  window → fetch (fetch.main) → resolve (resolve.check_triggers / resolve_open / save / ledger)
  → events diff → sizing (drawdown ladder, 50% cap) → volatility stand-down (ATR14 15m)
  → regime bias / reversal / counter-trend setup → thesis & heat → hub-level proximity
  → cards (only when something happened) → desk_status.json + desk_events.jsonl

The only things that need judgment are a NEW directional read or plan, and prose. It sets
`needs_attention` (exit code 10) when a pre-registered trigger fires, so an LLM, or the
owner, is woken only then:
  PLAN_EVENT, EVENT_ON_PROVISIONAL_BAR, REVERSAL_CALLED, COUNTER_TREND_QUALIFIES,
  RULE_SIGNAL_READY (a registered rule fired AND its drafted plan passed every desk gate),
  DATA_STALE, DRAWDOWN_FLOOR, BRIEF_CHANGED
Quiet notes (no wake): STANDDOWN_CHANGE, HUB_LEVEL_TOUCH, WINDOW_CLOSE, HUB_STALE.

    python3 workspace/paper/CALL/desk_check.py                 # full check, fetch + resolve
    python3 workspace/paper/CALL/desk_check.py --no-fetch --render none
    python3 workspace/paper/CALL/desk_check.py --dry-run       # never writes desk state (resolve skipped)

Exit codes: 0 quiet · 10 needs_attention · 2 data failure · 3 outside the trading window (nothing done).
Time is computed in America/New_York, so there is no UTC-cron / 2026-11-01 DST breakage.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
ET = ZoneInfo("America/New_York")
STATUS = HERE / "desk_status.json"
EVENTS = HERE / "desk_events.jsonl"
SYMBOLS = ("MGC", "MNQ")
STANDDOWN = {"MGC": 10.0, "MNQ": 58.0}              # ATR14(15m) lines, N214
ARM_ATR, TOUCH_ATR = 1.0, 0.25                     # same ARM as bounce_levels.py
BRIEFS = (ROOT / "CALLOUT.md", HERE / "DESK_BRIEF.md", HERE / "CHECK_PROCEDURE.md",
          ROOT / "DATA_HUB" / "RULES_AND_PITFALLS.md")
FLOOR = 2600.0                                     # operational floor before the $2,800 absorbing state
PROVISIONAL_MIN = 30                               # 15m bars revise for ~28 min (N41/N65/N89)


def pb_defaults():
    """plan_builder's CLI defaults as a Namespace (so a rule signal only overrides what it sets)."""
    return argparse.Namespace(symbol=None, side=None, entry=None, stop=None, stop_beyond=None, stop_atr=1.0,
                              tp_r=1.8, trigger_type=None, expiry_bars=8, strategy="", strategy_basis=None,
                              entry_basis=None, invalidation=None, confidence="DISCRETIONARY", why="",
                              from_signal=None, now=None, commit=False)


def _mod(name):
    spec = importlib.util.spec_from_file_location(f"call_{name}", HERE / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def in_window(now_et: datetime) -> bool:
    """Owner's cadence window: Sun 18:00 ET → Fri 15:30 ET, dark 15:30–18:00 daily."""
    wd, t = now_et.weekday(), now_et.hour * 60 + now_et.minute
    if wd == 5 or (wd == 6 and t < 18 * 60) or (wd == 4 and t >= 15 * 60 + 30):
        return False
    return not (15 * 60 + 30 <= t < 18 * 60)


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        out = fn(*a, **k)
    return out, buf.getvalue()


def brief_hash() -> str:
    h = hashlib.sha256()
    for p in BRIEFS:
        if p.exists():
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def diff_events(before: dict, after: dict) -> list[dict]:
    ev = []
    b_open = {p.get("call_id") for p in before.get("open", [])}
    b_closed = {p.get("call_id") for p in before.get("closed", [])}
    for p in after.get("open", []):
        if p.get("call_id") not in b_open:
            ev.append({"kind": "TRIGGERED", "id": p.get("call_id"), "detail": p})
    for p in after.get("closed", []):
        if p.get("call_id") not in b_closed:
            ev.append({"kind": "CLOSED", "id": p.get("call_id"),
                       "detail": {k: p.get(k) for k in ("result", "r_multiple", "ambiguous", "exit_price", "exit_ts")}})
    return ev


def plan_status(path: pathlib.Path) -> dict:
    out = {}
    if path.exists():
        for l in path.read_text().splitlines():
            if l.strip():
                d = json.loads(l)
                out[d.get("call_id")] = d.get("status")
    return out


def hub_levels(sym: str, close: float, atr: float, prev: dict) -> tuple[list, list]:
    """Hub levels near price, with arm/touch hysteresis kept between runs."""
    rows, touches = [], []
    lv = ROOT / "DATA_HUB" / "levels"
    cands = []
    try:
        for r in json.loads((lv / f"{sym}_bounce.json").read_text()):
            for x in r["current"]["levels"]:
                cands.append((f"{r['tf']}m {x['level']}", x["price"], r["current"]["asof"]))
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    try:
        for c in json.loads((lv / f"{sym}_volume_profile.json").read_text())["current"]:
            for x in c["lvn"]:
                cands.append((f"LVN {c['window']}", x["price"], c["asof"]))
            for k in ("poc", "vah", "val"):
                cands.append((f"{k.upper()} {c['window']}", c[k], c["asof"]))
    except (OSError, KeyError, json.JSONDecodeError):
        pass
    seen = set()
    for name, px, asof in cands:
        key = f"{name}@{px}"
        if key in seen or not atr:
            continue
        seen.add(key)
        dist = abs(close - px) / atr
        if dist > 3:
            continue
        was = prev.get(key, "armed" if dist >= ARM_ATR else "near")
        state = "armed" if dist >= ARM_ATR else ("touch" if dist <= TOUCH_ATR else was)
        if state == "touch" and was == "armed":
            touches.append({"level": name, "price": px, "dist_atr": round(dist, 2), "hub_asof": asof})
        if state == "touch":
            state = "near"                           # one touch per arming
        rows.append({"level": name, "price": px, "dist_atr": round(dist, 2), "state": state, "hub_asof": asof})
    rows.sort(key=lambda r: r["dist_atr"])
    return rows[:12], touches


def rule_signals(sym: str, prev_seen: dict) -> list[dict]:
    """Run every REGISTERED walk-forward rule on this symbol's live bars, so the rule traded live is
    byte-for-byte the rule that was backtested (DATA_HUB/tools/rules/, ledger-checked). Evaluated once
    per NEW completed bar of the rule's timeframe. A signal becomes a draft plan via plan_builder."""
    sys.path.insert(0, str(ROOT / "DATA_HUB" / "tools"))
    try:
        import walkforward as WF
    except Exception:                                   # engine missing -> no signals, never a crash
        return []
    shas = {r["sha"] for r in WF.ledger_rows()}
    resolve = _mod("resolve")
    out = []
    for path in sorted((ROOT / "DATA_HUB" / "tools" / "rules").glob("*.py")):
        if WF.file_sha(path) not in shas:
            continue                                    # unregistered or edited: not allowed to trade
        rule = WF.load_rule(path)
        tf = getattr(rule, "TF", 60)
        bars = resolve.load_bars(sym, tf)
        if len(bars) <= getattr(rule, "WARMUP", 0) + 2:
            continue
        key = f"{rule.NAME}:{sym}"
        if prev_seen.get(key) == bars[-1]["ts"]:
            continue
        prev_seen[key] = bars[-1]["ts"]
        ctx = WF.Ctx(bars, sym, tf)
        i_last = len(bars) - 1
        for i in range(rule.WARMUP, len(bars)):
            if hasattr(rule, "observe"):
                rule.observe(WF.View(bars, i), i, ctx)
        order = rule.decide(WF.View(bars, i_last), i_last, ctx)
        if not order:
            continue
        a = ctx.atr(i_last) or 0
        fired = ctx.state.get("fired") or [(i_last, bars[-1]["c"])]
        level = fired[-1][1]
        sign = 1 if order["side"] == "LONG" else -1
        stop = level - sign * order.get("stop_atr", 1.0) * a if order.get("stop") is None else order["stop"]
        tgt_r = order.get("target_atr", order.get("target_r", 1.0)) / order.get("stop_atr", 1.0)
        out.append({"rule": rule.NAME, "symbol": sym, "bar": bars[-1]["ts"], "side": order["side"],
                    "level": round(level, 4), "why": order.get("why", ""),
                    "plan_args": {"symbol": sym, "side": order["side"], "entry": level, "stop": stop,
                                  "tp_r": tgt_r, "strategy": f"RULE {rule.NAME} (pre-registered, walk-forward tested)",
                                  "confidence": f"RULE:{rule.NAME}",
                                  "trigger_type": "LIMIT_ENTRY_SELL" if order["side"] == "SHORT" else "LIMIT_ENTRY_BUY",
                                  "why": order.get("why", ""), "expiry_bars": 8}})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-fetch", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="skip resolve and never write desk state")
    ap.add_argument("--render", choices=("auto", "none", "always"), default="auto")
    ap.add_argument("--scale", type=int, default=3)
    ap.add_argument("--now", help="ISO time override (tests)")
    ap.add_argument("--ignore-window", action="store_true")
    a = ap.parse_args()

    now_utc = (datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)).astimezone(timezone.utc)
    now_et = now_utc.astimezone(ET)
    prev = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    if not (in_window(now_et) or a.ignore_window):
        print(f"{now_et:%H:%M %Z %a}: outside the owner's window (Sun 18:00 → Fri 15:30 ET). Nothing done.")
        return 3

    triggers, notes, events = [], [], []
    st = {"now_utc": now_utc.isoformat(timespec="seconds"), "now_et": now_et.strftime("%Y-%m-%d %H:%M %Z"),
          "mode": "dry-run" if a.dry_run else "live"}

    # 1. bars
    if not a.no_fetch:
        try:
            fetch = _mod("fetch")
            _, log = quiet(fetch.main)
            st["fetch_log"] = log.strip().splitlines()[-6:]
        except Exception as exc:                           # network, vendor
            st["fetch_error"] = str(exc)[:300]
            fails = prev.get("fetch_failures", 0) + 1
            st["fetch_failures"] = fails
            if fails >= 3:
                triggers.append("DATA_STALE")
    resolve = _mod("resolve")
    data = {}
    for sym in SYMBOLS:
        b5 = resolve.load_bars(sym, 5)
        if b5:
            newest = datetime.fromisoformat(b5[-1]["ts"])
            lag = (now_utc - newest.astimezone(timezone.utc)).total_seconds() / 60 - 5
            data[sym] = {"newest_5m": b5[-1]["ts"], "lag_min": round(lag, 1), "close": b5[-1]["c"]}
            if lag > 30:
                triggers.append("DATA_STALE")
        else:
            data[sym] = {"newest_5m": None}
            triggers.append("DATA_STALE")
    st["data"] = data

    # 2-5. resolve (the only writer of outcomes) and diff
    basis = (HERE / "BASIS").read_text().strip() if (HERE / "BASIS").exists() else "unknown"
    state = resolve.load_state()
    before = json.loads(json.dumps(state))
    plans_before = plan_status(HERE / "pending.jsonl")
    if not a.dry_run:
        now_iso = now_utc.replace(microsecond=0).isoformat()
        lines = resolve.check_triggers(state, now_iso, basis) + resolve.resolve_open(state, now_iso)
        resolve.save_state(state)
        resolve.write_ledger(state, basis, now_iso)
        st["resolve_log"] = lines
    events += diff_events(before, state)
    for cid, s in plan_status(HERE / "pending.jsonl").items():
        if plans_before.get(cid) != s:
            events.append({"kind": f"PLAN_{s}", "id": cid})
    if events:
        triggers.append("PLAN_EVENT")
        for e in events:
            ts = (e.get("detail") or {}).get("exit_ts") or (e.get("detail") or {}).get("entry_ts")
            if ts and now_utc - datetime.fromisoformat(ts).astimezone(timezone.utc) < timedelta(minutes=PROVISIONAL_MIN):
                triggers.append("EVENT_ON_PROVISIONAL_BAR")

    # 6-7. ledger & sizing
    closed = state.get("closed", [])
    rs = [c.get("r_multiple") for c in closed if isinstance(c.get("r_multiple"), (int, float))]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    dd = float(state.get("drawdown", 0.0))
    sc = _mod("status_card")
    watch = _mod("watch")
    (open_risk, pend_risk, labels), _ = quiet(watch.committed)
    st["ledger"] = {"closed": len(rs), "wins": len(wins), "losses": len(losses),
                    "win_rate": round(len(wins) / len(rs), 3) if rs else None,
                    "payoff": round((sum(wins) / len(wins)) / abs(sum(losses) / len(losses)), 3)
                    if wins and losses and sum(losses) else None,
                    "expectancy_r": round(sum(rs) / len(rs), 4) if rs else None,
                    "equity": state.get("equity"), "drawdown": dd, "to_2800": round(2800 - dd, 2),
                    "note": "state.json basis; the desk's MEASURED record excludes CALL-0002 (N155)"}
    st["sizing"] = {"permitted": sc.PERMITTED, "cap_50pct": sc.CAP, "committed_open": round(open_risk, 2),
                    "committed_pending": round(pend_risk, 2), "room": round(sc.CAP - open_risk - pend_risk, 2)}
    if dd >= FLOOR:
        triggers.append("DRAWDOWN_FLOOR")

    # 8-9. volatility stand-down, regime
    regime = _mod("regime")
    st["standdown"], st["regime"] = {}, {}
    hist = {}
    for sym in SYMBOLS:
        try:
            atr = sc.atr14(sym)
        except (IndexError, ZeroDivisionError):
            atr = None
        binding = bool(atr and atr > STANDDOWN[sym])
        st["standdown"][sym] = {"atr14_15m": round(atr, 2) if atr else None, "line": STANDDOWN[sym], "binding": binding}
        if prev.get("standdown", {}).get(sym, {}).get("binding") not in (None, binding):
            notes.append(f"STANDDOWN_CHANGE {sym} -> {'binding' if binding else 'lifted'}")
        tfs, _ = quiet(regime.timeframe_bias, sym)
        rv, _ = quiet(regime.reversal, sym, tfs)
        setup, _ = quiet(regime.reversal_setup, sym, tfs)
        b15 = resolve.load_bars(sym, 15)
        last15 = b15[-1]["ts"] if b15 else None
        if not a.dry_run and last15 and last15 != prev.get("regime", {}).get(sym, {}).get("last15"):
            regime.record(sym, tfs)                  # once per NEW 15m bar, not per check (N231/N248)
        prev_r = prev.get("regime", {}).get(sym, {})
        if rv.get("called") and not prev_r.get("reversal_called"):
            triggers.append("REVERSAL_CALLED")
        if setup.get("qualifies") and not prev_r.get("setup_qualifies"):
            triggers.append("COUNTER_TREND_QUALIFIES")
        st["regime"][sym] = {"frames": {regime.label(t["frame"]): t["headline"] for t in tfs},
                             "reversal_called": bool(rv.get("called")), "reversal_reasons": rv.get("reasons"),
                             "setup_qualifies": bool(setup.get("qualifies")), "setup_side": setup.get("side"),
                             "last15": last15}
        # 12. hub levels
        close = data[sym].get("close")
        rows, touches = hub_levels(sym, close, atr, prev.get("hub_state", {}).get(sym, {})) if close and atr else ([], [])
        st.setdefault("hub_levels", {})[sym] = rows
        hist[sym] = {f"{r['level']}@{r['price']}": r["state"] for r in rows}
        for t in touches:
            notes.append(f"HUB_LEVEL_TOUCH {sym} {t['level']} {t['price']} (hub bar {t['hub_asof'][:16]})")
    st["hub_state"] = hist

    # 12b. live signals from registered, walk-forward-tested rules -> draft plans (never auto-committed)
    seen = dict(prev.get("rule_seen", {}))
    sigs = []
    for sym in SYMBOLS:
        for sg in rule_signals(sym, seen):
            draft = HERE / "drafts" / f"signal_{sg['rule']}_{sym}_{sg['bar'][:16].replace(':', '')}.json"
            draft.parent.mkdir(exist_ok=True)
            draft.write_text(json.dumps(sg, indent=1))
            try:
                pb = _mod("plan_builder")
                ns = argparse.Namespace(**{**vars(pb_defaults()), **sg["plan_args"]})
                plan = pb.build(ns)
                sg["draft_verdict"] = plan["builder"]["verdict"]
                sg["failed_gates"] = [g["gate"] + ": " + g["why"] for g in plan["builder"]["gates"] if not g["pass"]]
            except Exception as exc:
                sg["draft_verdict"] = f"builder error {exc}"[:200]
            sg["draft_file"] = str(draft.relative_to(ROOT))
            sigs.append(sg)
            if not a.dry_run:
                with (HERE / "rule_signals.jsonl").open("a") as fh:
                    fh.write(json.dumps(sg, default=str) + "\n")
            if sg.get("draft_verdict") == "READY":
                triggers.append("RULE_SIGNAL_READY")
            else:
                notes.append(f"RULE_SIGNAL {sg['rule']} {sym} {sg['side']} @ {sg['level']} refused by desk gates "
                             f"(shadow-logged): {'; '.join(sg.get('failed_gates', []))[:200]}")
    st["rule_signals"] = sigs
    st["rule_seen"] = seen
    try:
        asof = json.loads((ROOT / "DATA_HUB/levels/MNQ_bounce.json").read_text())[0]["current"]["asof"]
        if now_utc - datetime.fromisoformat(asof).astimezone(timezone.utc) > timedelta(hours=24):
            notes.append("HUB_STALE: run bash DATA_HUB/tools/update_hub.sh --no-fetch")
    except (OSError, KeyError, IndexError, json.JSONDecodeError):
        notes.append("HUB_STALE: no hub level files")

    # 10. thesis / heat
    thesis = _mod("thesis")
    pend = [json.loads(l) for l in (HERE / "pending.jsonl").read_text().splitlines()
            if l.strip() and json.loads(l).get("status") == "PENDING"] if (HERE / "pending.jsonl").exists() else []
    st["book"] = {"pending": [p["call_id"] for p in pend], "open": [p.get("call_id") for p in state.get("open", [])],
                  "thesis": {p["call_id"]: quiet(thesis.track, p)[0].get("verdict") for p in pend}}

    # brief changes, window close
    bh = brief_hash()
    if prev.get("brief_hash") and prev["brief_hash"] != bh:
        triggers.append("BRIEF_CHANGED")
    st["brief_hash"] = bh
    if now_et.hour == 15 and now_et.minute >= 28 and pend:
        notes.append("WINDOW_CLOSE: pending plans are unwatched until 18:00 ET")

    # 13. cards: only when something happened, on the first check of each ET hour, or at window close
    first_of_hour = prev.get("now_et", "")[:13] != now_et.strftime("%Y-%m-%d %H")
    want = a.render == "always" or (a.render == "auto" and (events or triggers or first_of_hour
                                                             or any(n.startswith("WINDOW_CLOSE") for n in notes)))
    cards = []
    if want and not a.dry_run:
        try:
            card = _mod("card_png")
            card.SCALE = a.scale
            for p in pend:
                cards.append(str(card.render(p, HERE / f"card_{p['symbol']}_{p['call_id']}.png")))
            if not pend:
                sc.C.SCALE = a.scale
                cards.append(str(sc.render(HERE / "card_STATUS.png", sc.auto_reason())))
        except Exception as exc:                           # rendering must never block the check
            notes.append(f"CARD_ERROR {exc}"[:200])
    st["cards"] = cards

    triggers = sorted(set(triggers))
    st.update(events=events, triggers=triggers, notes=notes, needs_attention=bool(triggers))
    lg = st["ledger"]
    st["one_line"] = (f"{now_et:%H:%M %Z} · MNQ {data['MNQ'].get('close')} MGC {round(data['MGC'].get('close') or 0, 1)} · "
                      f"pending {','.join(st['book']['pending']) or 'none'} · open {len(st['book']['open'])} · "
                      f"eq ${lg['equity']:,.2f} dd ${dd:,.2f} · "
                      + ("ATTENTION: " + ", ".join(triggers) if triggers else "quiet"))
    if not a.dry_run:
        STATUS.write_text(json.dumps(st, indent=1, default=str))
        with EVENTS.open("a") as fh:
            fh.write(json.dumps({"t": st["now_utc"], "triggers": triggers, "events": events, "notes": notes},
                                default=str) + "\n")
    print(st["one_line"])
    for n in notes:
        print("  note:", n)
    return 10 if triggers else 0


if __name__ == "__main__":
    sys.exit(main())
