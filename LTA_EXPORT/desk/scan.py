#!/usr/bin/env python3
"""LTA CONCEPT CALLOUTS — the 2-minute scan. One mechanical turn of the LTA strategy.

Runs the book's process on every symbol and decides whether the owner needs to hear anything.
It applies ONLY the LTA book's rules (study/CONCEPTS_DIGEST.md). It shares no rule, level or
state with the other desks (LVNFIB, CALL); the only things in common are the account rules
every desk must follow (paper, $50,000, $2,800 floor, flat by 16:00 ET).

Each turn:
  1. dormant check: weekend, or 16:00-18:00 ET with nothing open -> exit 3, no fetch
  2. fetch fresh 5/15/30/60m bars into live/ (throttled to FETCH_MIN_S; never rewrites desk/archive/)
  3. macro layer per symbol (cached MACRO_MIN_S): bias from valuation (with trend + correlation
     gate), seasonality and the owner's COT read
  4. war map per symbol; take entry-model candidates (EM1/EM3/EM4) that completed on the
     NEWEST CLOSED 30m or 60m bar only, and keep those that pass the book's filters:
       F1 level is a book execution level: PD/EPD/PW/EPW/CW/Swing POC-VAH-VAL, SO, PSO [p66-p80]
       F2 the side agrees with the intraday trend (60m or 30m two-touch trend) [p180-p182]
       F3 Asia session (18:00-02:00 ET) = low volume -> 60m confirmations only [p73]
       F4 one position per symbol; MES/MNQ count as one bet [p222]
     then callout.build() applies 2/2/2, two strikes, obstacle-in-path, session window
  5. post passing callouts, draw their PNG cards; NO_TRADE outcomes are logged, not sent
  6. resolve open positions on 5m bars (ledger.py) and draw the outcome card
  7. append one line to scan_events.jsonl

Exit: 0 quiet · 3 dormant · 10 something to tell the owner (WAKE/CARD lines printed) · 2 data failure
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import time
from datetime import datetime, timedelta
from types import SimpleNamespace

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from lta_common import now_et                    # noqa: E402
import lta_levels                                  # noqa: E402
import callout                                     # noqa: E402
import ledger                                      # noqa: E402

SYMS = ["MNQ", "MES", "MGC", "MCL"]
STATE = HERE / "state.json"
EVENTS = HERE / "scan_events.jsonl"
MACRO_CACHE = HERE / "live" / "macro_cache.json"
FETCH_MIN_S = 100
MACRO_MIN_S = 3600
BOOK_LEVELS = ("POC", "VAH", "VAL", "SO", "PSO")
INDEX_GROUP = {"MES", "MNQ"}


def _load(p, default):
    try:
        return json.loads(p.read_text())
    except Exception:
        return default


def dormant(t, open_pos):
    hm = t.hour * 60 + t.minute
    wk = t.weekday()
    weekend = wk == 5 or (wk == 4 and hm >= 17 * 60) or (wk == 6 and hm < 18 * 60)
    if weekend:
        return "weekend"
    if 16 * 60 <= hm < 18 * 60 and not open_pos:
        return "daily break 16:00-18:00 ET, nothing open"
    return None


def fetch(state):
    last = state.get("last_fetch", 0)
    if time.time() - last < FETCH_MIN_S:
        return True, f"fetch throttled ({time.time() - last:.0f}s since last)"
    r = subprocess.run([sys.executable, str(HERE / "fetch.py"), "--symbols", *SYMS],
                       capture_output=True, text=True, timeout=240)
    state["last_fetch"] = time.time()
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    bad = [l for l in lines if "FAILED" in l or "EMPTY" in l]
    return (r.returncode == 0), (f"fetch ok, {len(lines)} series" if r.returncode == 0
                                 else "fetch problems: " + " | ".join(bad[:3]))


def macro(sym, cache):
    hit = cache.get(sym)
    if hit and time.time() - hit.get("_at", 0) < MACRO_MIN_S:
        return hit
    try:
        import macro as mac
        m = mac.run(sym)
        m["_at"] = time.time()
        cache[sym] = m
        return m
    except Exception as e:
        return hit or {"macro_bias": {"bias": "NONE", "notes": [f"macro failed: {e}"]}}


def session(t):
    h = t.hour + t.minute / 60
    return "ASIA" if (h >= 18 or h < 2) else "LONDON" if h < 8 else "NY"


def open_positions():
    done = {r["key"] for r in ledger._read(ledger.RESOLVED)}
    return [c for c in ledger._read(ledger.JOURNAL)
            if c.get("verdict") in ("LONG", "SHORT") and ledger._key(c) not in done]


def newest_closed(sym, tf):
    bars = lta_levels.load(sym, tf)
    return bars[-1].ts.isoformat() if bars else None


def book_filter(s, m, t, open_pos):
    """None if the setup passes the book's filters, else the reason it does not."""
    names = [n.strip() for n in s["level"].split("+")]
    keep = [n for n in names if n.split()[-1] in BOOK_LEVELS]
    if not keep:
        return f"F1 level {s['level']} is not a book execution level"
    s["level"] = keep[0]
    want = "UP" if s["side"] == "LONG" else "DOWN"
    t60 = (m.get("trend_60m") or {}).get("trend")
    t30 = (m.get("trend_30m") or {}).get("trend")
    if want not in (t60, t30):
        return f"F2 {s['side']} against the intraday trend (60m {t60}, 30m {t30})"
    if session(t) == "ASIA" and s["tf"] != "60m":
        return "F3 Asia session: low volume, book wants the higher-timeframe (60m) close"
    for c in open_pos:
        if c["symbol"] == m["symbol"]:
            return f"F4 already holding {c['symbol']} {c['side']} ({c.get('id')})"
        if m["symbol"] in INDEX_GROUP and c["symbol"] in INDEX_GROUP:
            return f"F4 {c['symbol']} {c['side']} is open; MES/MNQ are one bet"
    return None


def main():
    t = now_et()
    state = _load(STATE, {})
    ev = {"ts_et": t.isoformat(timespec="seconds"), "posted": [], "resolved": [], "filtered": [], "refused": []}
    open_pos = open_positions()
    why = dormant(t, open_pos)
    if why:
        ev["status"] = f"DORMANT: {why}"
        EVENTS.open("a").write(json.dumps(ev) + "\n")
        print(ev["status"])
        return 3

    ok, msg = fetch(state)
    ev["fetch"] = msg
    if not ok:
        state["fetch_fail"] = state.get("fetch_fail", 0) + 1
    else:
        state["fetch_fail"] = 0
    cache = _load(MACRO_CACHE, {})
    seen = set(state.get("seen", []))
    wake = []

    for sym in SYMS:
        try:
            m = lta_levels.war_map(sym)
        except Exception as e:
            wake.append(f"WAKE data: {sym} war map failed: {e}")
            continue
        age_h = (t - datetime.fromisoformat(m["newest_bar"])).total_seconds() / 3600
        if age_h > callout.STALE_HOURS:
            ev["filtered"].append(f"{sym}: newest bar {m['newest_bar']} is {age_h:.1f} h old — no callouts")
            continue
        mac = macro(sym, cache)
        bias = mac.get("macro_bias", {}).get("bias", "NONE")
        fresh = {"30m": newest_closed(sym, 30), "60m": newest_closed(sym, 60)}
        for s in m["setups"]:
            if s["bar"] != fresh.get(s["tf"]):
                continue                                   # only the bar that just closed
            key = f"{sym}|{s['model']}|{s['side']}|{s['tf']}|{s['bar']}"
            if key in seen:
                continue
            seen.add(key)
            r = book_filter(s, m, t, open_pos)
            if r:
                ev["filtered"].append(f"{sym} {s['model']} {s['side']} {s['tf']} @ {s['level']}: {r}")
                continue
            a = SimpleNamespace(
                symbol=sym, side=s["side"], entry=s["trigger_close"], stop=s["stop"], target=None,
                model=s["model"], tf=s["tf"], level=s["level"], macro=bias,
                htf=f"{m.get('vs_SO', '')}; PD value: {m.get('vs_PD_value', '')}",
                archetype=None, confirmed=(bias == ("BULLISH" if s["side"] == "LONG" else "BEARISH")),
                news_within_min=None, accept_obstacle=False, price_given=False,
                why=(f"scan: {s['model']} completed on the {s['tf']} bar {s['bar']} at {s['level']} "
                     f"{s['level_price']}; intraday 60m {(m.get('trend_60m') or {}).get('trend')}, "
                     f"macro {bias}"))
            c = callout.build(a, m=m, t=t, closed_bar=True)
            c["macro_detail"] = "; ".join(mac.get("macro_bias", {}).get("notes", []))[:120] or None
            if c["verdict"] == "NO_TRADE":
                ev["refused"].append(f"{sym} {s['model']} {s['side']} {s['tf']}: " + " | ".join(c["refusals"]))
                continue
            with callout.JOURNAL.open("a") as f:
                f.write(json.dumps(c, default=str) + "\n")
            open_pos.append(c)
            ev["posted"].append(c["id"])
            wake.append(f"WAKE callout: {c['id']} {c['side']} {sym} entry {c['entry_price']} stop "
                        f"{c['initial_stop']} target {c['target']} x{c['contracts']} (${c['risk_dollars']})")

    for r in ledger.resolve_all():
        ev["resolved"].append(f"{r.get('id')} {r['outcome']} {r['r']:+}R ${r['pnl']:+,.2f}")
        wake.append(f"WAKE outcome: {r.get('id')} {r['outcome']} {r['r']:+}R ${r['pnl']:+,.2f}")

    state["seen"] = sorted(seen)[-2000:]
    STATE.write_text(json.dumps(state))
    MACRO_CACHE.parent.mkdir(exist_ok=True)
    MACRO_CACHE.write_text(json.dumps(cache, default=str))

    cards = []
    if wake:
        out = subprocess.run([sys.executable, str(HERE / "card_png.py"), "--new"],
                             capture_output=True, text=True)
        cards = [l for l in out.stdout.splitlines() if l.startswith("CARD ")]
    ev["status"] = "WAKE" if wake else ("DATA_FAIL" if state.get("fetch_fail", 0) >= 3 else "QUIET")
    ev["cards"] = [c[5:] for c in cards]
    with EVENTS.open("a") as f:
        f.write(json.dumps(ev) + "\n")
    print(f"LTA scan {t:%Y-%m-%d %H:%M:%S} ET · {msg} · open {len(open_pos)} · "
          f"filtered {len(ev['filtered'])} · refused {len(ev['refused'])}")
    for line in wake + cards:
        print(line)
    if wake:
        return 10
    if state.get("fetch_fail", 0) >= 3:
        print("WAKE data: three fetch failures in a row")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
