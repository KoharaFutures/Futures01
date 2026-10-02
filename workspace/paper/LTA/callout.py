#!/usr/bin/env python3
"""LTA CONCEPT CALLOUTS — build, gate, size and (optionally) journal one paper callout.

    python3 workspace/paper/LTA/callout.py --symbol MNQ --side LONG --entry 30880.25 \
        --stop 30841.75 --model EM1 --level "PD VAH" --tf 30m \
        --macro BULLISH --htf "daily demand 30500-30620" \
        --why "PD VAH retest holding after break of PWC; 60m HH/HL" [--post]

Without --post it prints the card and writes nothing. With --post it appends one line to
callouts.jsonl (append-only).

THIS DESK TRADES THE LTA BOOK ONLY. It deliberately does not import the other desks' rules
(LVNFIB arms, CALL desk filters, hub stand-downs). Its gates are the book's, plus the account
rules every desk shares (CLAUDE.md #6: paper, $50,000, $2,800 floor; the owner's session window).

Gates, in order:
  data      the war map's newest bar must be < 2.5 h old (else STALE)          [CLAUDE.md #4]
  time      flat by 16:00 ET, nothing opened 15:30-18:00, weekend closed      [owner's window]
            not in the last 10 min of a 30m/60m candle                        [book p73]
  2/2/2 #1  target must be >= 2R (default target = exactly 2R)                [book p219]
  2/2/2 #2  risk budget: full = min(0.5% equity, 10% of room to the $2,800 floor);
            half for CONTRARIAN / counter-trend / unconfirmed                 [book p221, p236]
  2/2/2 #3  two losses in a row today (and the day not green) -> HALT         [book p222]
  obstacle  a key level inside the first 1R of the path -> NO TRADE          [book p79]
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys
from datetime import datetime, timedelta

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from futures_agents.config import get_contract, correlated_symbols   # noqa: E402
from futures_agents.timeutil import now_et                            # noqa: E402
from lta_levels import war_map, tday                                  # noqa: E402
from ledger import account, today_record                              # noqa: E402

JOURNAL = HERE / "callouts.jsonl"
START_EQUITY = 50_000.0
FLOOR_DD = 2_800.0
FULL_PCT_EQUITY = 0.005
FULL_PCT_ROOM = 0.10
MIN_RISK_USD = 25.0          # below this the account cannot place a trade (repo absorbing state)
STALE_HOURS = 2.5


def risk_budget(acct, half):
    full = min(FULL_PCT_EQUITY * acct["equity"], FULL_PCT_ROOM * acct["room_to_floor"])
    return round(full / 2 if half else full, 2), round(full, 2)


def time_gate(t):
    hm = t.hour * 60 + t.minute
    if 15 * 60 + 30 <= hm < 18 * 60:
        return "NO ENTRIES 15:30-18:00 ET (owner's window: flat by 16:00, nothing held 16:00-18:00)"
    if t.weekday() == 5 or (t.weekday() == 4 and hm >= 17 * 60) or (t.weekday() == 6 and hm < 18 * 60):
        return "MARKET CLOSED (weekend)"
    m30 = t.minute % 30
    if m30 >= 20:
        return f"WAIT: {30 - m30} min to the {('60m' if t.minute >= 50 else '30m')} close — book p73: let the candle close first"
    return None


def obstacles(m, side, entry, risk, target):
    lo, hi = (entry, target) if side == "LONG" else (target, entry)
    hits = []
    for x in m["levels"]:
        p = x["price"]
        if lo < p < hi and abs(p - entry) > 0.1 * risk:
            hits.append({"name": x["name"], "price": p, "r_from_entry": round(abs(p - entry) / risk, 2)})
    return sorted(hits, key=lambda h: h["r_from_entry"])


def build(a, m=None, t=None, closed_bar=False):
    """`m` = a war map already built this cycle; `t` = decision time; `closed_bar` = the
    decision is taken on a just-closed bar (the scanner), so the candle-close wait is met."""
    sym = a.symbol.upper()
    spec = get_contract(sym)
    m = m or war_map(sym)
    t = t or now_et()
    side = a.side.upper()
    sgn = 1 if side == "LONG" else -1
    risk = abs(a.entry - a.stop)
    if risk <= 0 or (a.stop - a.entry) * sgn > 0:
        raise SystemExit("stop must be on the losing side of the entry")
    target = a.target if a.target is not None else a.entry + sgn * 2 * risk
    rr = abs(target - a.entry) / risk
    tick = spec.tick_size
    target = round(round(target / tick) * tick, 6)

    tr60 = (m.get("trend_60m") or {}).get("trend")
    against_intraday = (side == "LONG" and tr60 == "DOWN") or (side == "SHORT" and tr60 == "UP")
    against_macro = (side == "LONG" and a.macro == "BEARISH") or (side == "SHORT" and a.macro == "BULLISH")
    archetype = a.archetype or ("CONTRARIAN" if (against_intraday or against_macro or a.macro == "NONE") else "MOMENTUM")
    half = archetype == "CONTRARIAN" or not a.confirmed

    acct = account()
    day = today_record(tday(t))
    budget, full = risk_budget(acct, half)
    per_contract = risk * spec.point_value + spec.round_turn_cost
    contracts = int(budget // per_contract) if per_contract > 0 else 0

    refusals, warnings = [], []
    newest = datetime.fromisoformat(m["newest_bar"])
    age_h = (t - newest).total_seconds() / 3600
    if age_h > STALE_HOURS and not a.price_given:
        refusals.append(f"STALE DATA: newest bar {m['newest_bar']} is {age_h:.1f} h old — refresh "
                        "(DATA_HUB/tools/refresh_archive.py --fetch) or pass --price-given if the owner quoted the price")
    tg = time_gate(t)
    if tg and tg.startswith("WAIT") and closed_bar:
        tg = None
    if tg:
        (warnings if tg.startswith("WAIT") else refusals).append(tg)
    if rr < 2 - 1e-9:
        refusals.append(f"2/2/2 RULE 1: target is {rr:.2f}R; every trade must offer >= 2R (book p219)")
    if day["halt"]:
        refusals.append(f"2/2/2 RULE 3 (two strikes): {day['why']} — stop for the day (book p222)")
    if acct["equity"] - (acct["peak"] - FLOOR_DD) <= 0:
        refusals.append("ACCOUNT AT THE $2,800 DRAWDOWN FLOOR")
    if full < MIN_RISK_USD:
        refusals.append(f"risk budget ${full} < ${MIN_RISK_USD}: the account cannot size a trade (absorbing state)")
    elif contracts < 1:
        refusals.append(f"SIZE: one contract risks ${per_contract:.2f} > budget ${budget} ({'half' if half else 'full'} risk)")
    obs = obstacles(m, side, a.entry, risk, target)
    if obs and obs[0]["r_from_entry"] < 1.0 and not a.accept_obstacle:
        refusals.append(f"OBSTACLE: {obs[0]['name']} {obs[0]['price']} sits {obs[0]['r_from_entry']}R into the path "
                        "(book p79: skip when a key level blocks the target)")
    lv = next((x for x in m["levels"] if a.level and x["name"].upper() == a.level.upper()), None)
    if lv and lv["stacked_with"]:
        warnings.append(f"CONFLUENCE: {a.level} lines up with {', '.join(lv['stacked_with'])} (book p48: a confluence zone)")
    corr = set(correlated_symbols(sym)) | {sym}
    if day["last_loss"] and day["last_loss"]["symbol"] in corr and day["last_loss"]["side"] == side:
        warnings.append(f"CORRELATED follow-up: today's last loss was {day['last_loss']['symbol']} {side} — "
                        "book p222: a second correlated bet is the same trade twice")
    if a.news_within_min is not None and a.news_within_min <= 60:
        warnings.append(f"RED-FOLDER NEWS in {a.news_within_min} min — book: conservative risk, close before the release")
    wc = m["weekly_cycle"]["day"]
    if wc in ("MON", "TUE"):
        warnings.append("Early week: book ch.3 says Mon/Tue moves are often traps — needs the confirmation, not the touch")

    verdict = "NO_TRADE" if refusals else side
    mgmt = []
    if archetype == "CONTRARIAN":
        mgmt.append("move stop to breakeven at +1R (book p229, contrarian)")
    else:
        mgmt.append("no breakeven move — momentum trades get room (book p229)")
    mgmt.append("flat by 16:00 ET")
    if t.hour < 9 or (t.hour == 9 and t.minute < 30):
        mgmt.append("if not in profit by 09:25 ET, exit before the NY open (book p230)")
    mgmt.append("late NY with no progress: close it — volume dries up (book p230)")

    card = {
        "id": f"LTA-{sym}-{t:%Y%m%d-%H%M}-{a.model}-{side[0]}",
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z", "ts_et": t.isoformat(timespec="seconds"),
        "writer": "LTA", "symbol": sym, "side": side, "verdict": verdict,
        "entry_price": a.entry, "initial_stop": a.stop, "target": target, "rr": round(rr, 2),
        "risk_pts": round(risk, 6), "contracts": contracts if verdict != "NO_TRADE" else 0,
        "risk_dollars": round(contracts * per_contract, 2) if verdict != "NO_TRADE" else 0.0,
        "budget_dollars": budget, "risk_mode": "HALF" if half else "FULL",
        "model": a.model, "tf": a.tf, "level": a.level, "level_price": lv["price"] if lv else None,
        "level_source_bar": lv["source_bar"] if lv else None,
        "archetype": archetype, "macro_bias": a.macro, "htf_zone": a.htf,
        "intraday_trend_60m": tr60, "intraday_trend_30m": (m.get("trend_30m") or {}).get("trend"),
        "vs_PW_range": m.get("vs_PW_range"), "vs_PD_value": m.get("vs_PD_value"), "weekly_cycle": wc,
        "obstacles": obs[:4], "management": mgmt, "refusals": refusals, "warnings": warnings,
        "confidence": "DISCRETIONARY", "basis": "LTA Concepts 2.0 layered read; not yet tested (CHARTER §5)",
        "as_of_bar": m["newest_bar"], "price_given_by_owner": bool(a.price_given),
        "account": acct, "why": a.why, "session": session_of(t),
    }
    return card


def session_of(t):
    h = t.hour + t.minute / 60
    return "ASIA" if (h >= 18 or h < 2) else "LONDON" if h < 8 else "NY" if h < 16 else "CLOSED"


def render(c):
    from futures_agents.alerts import Priority, alert
    pr = {"LONG": Priority.LONG, "SHORT": Priority.SHORT}.get(c["verdict"], Priority.NO_TRADE)
    head = (f"LTA {c['verdict']} {c['symbol']}" if c["verdict"] != "NO_TRADE"
            else f"LTA NO TRADE {c['symbol']} ({c['side']} idea)")
    body = [
        "PAPER — UNVALIDATED · confidence DISCRETIONARY (LTA layered read, no measured edge here)",
        f"as-of bar {c['as_of_bar']}" + (" · price quoted by owner" if c["price_given_by_owner"] else ""),
        f"{c['model']} {c['tf']} at {c['level']} {c['level_price'] or ''} · {c['archetype']} · macro {c['macro_bias']}"
        f" · intraday 60m {c['intraday_trend_60m']} / 30m {c['intraday_trend_30m']}",
        f"entry {c['entry_price']}  stop {c['initial_stop']}  target {c['target']}  R:R {c['rr']}",
        f"size {c['contracts']} ct · risk ${c['risk_dollars']} of ${c['budget_dollars']} ({c['risk_mode']} risk)"
        f" · equity ${c['account']['equity']:,.0f} · room to floor ${c['account']['room_to_floor']:,.0f}",
        f"HTF zone: {c['htf_zone'] or '—'} · {c['vs_PW_range'] or ''}",
    ]
    if c["obstacles"]:
        body.append("levels in the path: " + ", ".join(f"{o['name']} {o['price']} ({o['r_from_entry']}R)" for o in c["obstacles"]))
    for r in c["refusals"]:
        body.append("REFUSED: " + r)
    for w in c["warnings"]:
        body.append("warning: " + w)
    for g in c["management"]:
        body.append("manage: " + g)
    body.append("why: " + (c["why"] or "—"))
    return alert(pr, head, "\n".join(body))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--symbol", required=True)
    ap.add_argument("--side", required=True, choices=["LONG", "SHORT", "long", "short"])
    ap.add_argument("--entry", type=float, required=True)
    ap.add_argument("--stop", type=float, required=True)
    ap.add_argument("--target", type=float)
    ap.add_argument("--model", default="EM1", choices=["EM1", "EM2", "EM3", "EM4", "LIMIT"])
    ap.add_argument("--tf", default="30m")
    ap.add_argument("--level", help="level name as lta_levels.py prints it, e.g. 'PD POC'")
    ap.add_argument("--macro", default="NONE", choices=["BULLISH", "BEARISH", "NONE"])
    ap.add_argument("--htf", default="", help="the higher-timeframe supply/demand zone, in words")
    ap.add_argument("--archetype", choices=["CONTRARIAN", "MOMENTUM"])
    ap.add_argument("--confirmed", action="store_true", default=False,
                    help="the HTF zone has confirmed direction (else half risk, book p221)")
    ap.add_argument("--news-within-min", type=int)
    ap.add_argument("--accept-obstacle", action="store_true")
    ap.add_argument("--price-given", action="store_true", help="the owner quoted the price this turn")
    ap.add_argument("--why", default="")
    ap.add_argument("--post", action="store_true")
    a = ap.parse_args()
    c = build(a)
    render(c)                     # alert() prints the coloured card itself
    if a.post:
        with JOURNAL.open("a") as f:
            f.write(json.dumps(c, default=str) + "\n")
        print(f"\njournaled -> {JOURNAL.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
