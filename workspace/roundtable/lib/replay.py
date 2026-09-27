#!/usr/bin/env python3
"""Bar-at-a-time replay harness — a walk-forward paper desk the agent cannot read ahead in.

Why a harness and not a file
----------------------------
A replay is only worth something if the future is unreachable at the moment of the
decision.  If the agent reads the series, it knows the answer, and no amount of
good intent fixes that - this whole repository is a catalogue of ways a measurement
quietly stops measuring what it claims.  So the series is served one bar at a time
and the agent is told to read ``visible.jsonl`` and nothing else.

That is discipline, not proof: an agent with a shell can read the source file.  Two
things make the discipline checkable rather than merely asked for:

1. **Every decision is journalled with the bar count visible when it was made**, so
   the record can be replayed and audited independently.
2. **A placebo runs beside the agent** - random entries, count-matched, through the
   same exits and the same sizing on the same bars.  A leak does not look like skill,
   it looks like an impossible number: nothing in ~3M evaluations in this repository
   has ever produced t > 3.923.  ``score`` prints the agent's separation from its own
   placebo next to that ceiling, so an implausible result indicts itself.

Fills follow ``engine.py``, not convenience
-------------------------------------------
* an order placed on bar *i* fills at the **open of bar i+1** (``engine.py:290,355``)
* a gap through the stop fills at the open, worse than the stop (``engine.py:410-412``)
* a gap through the target fills at the open, in your favour (``engine.py:431``)
* stop and target both touched in one bar: **the stop wins** - the conservative read
* the account owner's session rule is enforced: flat by 16:00 ET, nothing held
  across 16:00-18:00

Sizing is the shipped ``desk/desk-config.json`` ladder, reproduced here, including
the absorbing state at a $2,800 drawdown where permitted risk is $21.60 against a
$25 minimum and the account can no longer trade at all.

Usage
-----
    replay.py init   --id R1 --symbol MES --tf 1440 [--start 0]
    replay.py next   [--id R1] [--n 1]
    replay.py order  --side LONG|SHORT --stop <price> [--target <price>] --why "..."
    replay.py flat   [--why "..."]
    replay.py status
    replay.py journal [--tail 20]
    replay.py score
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import random
import statistics
import sys

REPO = pathlib.Path(__file__).resolve().parents[3]
PAPER = REPO / "workspace" / "paper" / "REPLAY"
SRC = REPO / "data" / "archive"

# ---------------------------------------------------------------- account
CFG = json.loads((REPO / "desk" / "desk-config.json").read_text())["account"]
USABLE = CFG["max_total_drawdown"] * (1.0 - CFG["protected_buffer_pct"])


def permitted_risk(equity: float, drawdown: float) -> tuple[float, float]:
    """Dollar risk the shipped ladder allows, and the multiplier that produced it."""
    remaining = max(0.0, USABLE - drawdown)
    consumed = drawdown / USABLE if USABLE else 1.0
    mult = 1.0
    for thr, m in CFG["derisk_ladder"]:
        if consumed >= thr:
            mult = m
    allowed = min(CFG["base_risk_pct_of_buffer"] * remaining * mult,
                  CFG["max_risk_pct_of_equity"] * equity,
                  CFG["max_dollar_risk"])
    return allowed, mult


# ---------------------------------------------------------------- session rule
ET = dt.timezone(dt.timedelta(hours=-4))       # the archive is stamped -04:00


def _et(ts: str) -> dt.datetime:
    return dt.datetime.fromisoformat(ts)


def in_forbidden_window(ts: str) -> bool:
    """16:00 <= t < 18:00 ET - the account owner's rule forbids holding here."""
    h, m = _et(ts).hour, _et(ts).minute
    return 16 <= h < 18


def cycle_deadline_crossed(entry_ts: str, bar_ts: str) -> bool:
    """True once a position has reached its cycle's 16:00 ET flat."""
    a, b = _et(entry_ts), _et(bar_ts)
    # the deadline is the first 16:00 ET at or after the entry
    dl = a.replace(hour=16, minute=0, second=0, microsecond=0)
    if a >= dl:
        dl += dt.timedelta(days=1)
    return b >= dl


# ---------------------------------------------------------------- state
def spec(symbol: str) -> dict:
    sys.path.insert(0, str(REPO))
    from futures_agents.config import CONTRACTS
    c = CONTRACTS[symbol]
    return {"symbol": symbol, "tick": c.tick_size, "point_value": c.point_value,
            "min_stop_ticks": c.min_stop_ticks, "rth_open": c.rth_open,
            "rth_close": c.rth_close,
            "cost_per_contract_round_turn":
                2 * (c.commission_per_side + c.exchange_fee_per_side)
                + c.typical_slippage_ticks * c.tick_size * c.point_value}


def home(rid: str) -> pathlib.Path:
    return PAPER / rid


def load(rid: str) -> dict:
    p = home(rid) / "state.json"
    if not p.exists():
        sys.exit(f"no replay '{rid}' - run: replay.py init --id {rid} --symbol MES --tf 1440")
    return json.loads(p.read_text())


def save(st: dict) -> None:
    (home(st["id"]) / "state.json").write_text(json.dumps(st, indent=2))


def source_bars(symbol: str, tf: int) -> list[dict]:
    f = SRC / f"{symbol}_{tf}m.jsonl"
    if not f.exists():
        sys.exit(f"no series at {f}")
    rows = [json.loads(l) for l in f.open() if l.strip()]
    # SERIES_AUDIT.md: MGC_1440m bars 0-383 are a different instrument (10.145x
    # splice, disjoint ranges). Never serve them.
    if symbol == "MGC" and tf == 1440:
        rows = rows[384:]
    return rows


def journal(st: dict, kind: str, **kw) -> None:
    rec = {"kind": kind, "cursor": st["cursor"], "visible_bars": st["cursor"],
           "at": dt.datetime.now(dt.timezone.utc).isoformat()}
    rec.update(kw)
    with (home(st["id"]) / "journal.jsonl").open("a") as fh:
        fh.write(json.dumps(rec) + "\n")


# ---------------------------------------------------------------- commands
def cmd_init(a) -> None:
    h = home(a.id)
    h.mkdir(parents=True, exist_ok=True)
    bars = source_bars(a.symbol, a.tf)
    sp = spec(a.symbol)
    st = {"id": a.id, "symbol": a.symbol, "tf": a.tf, "spec": sp,
          "n_source": len(bars), "start": a.start, "cursor": a.start,
          "equity": CFG["starting_equity"], "peak": CFG["starting_equity"],
          "position": None, "pending": None, "closed": 0, "seed": a.seed,
          "placebo_pending": None, "placebo_position": None,
          "first_ts": bars[0]["ts"], "last_ts": bars[-1]["ts"]}
    save(st)
    (h / "visible.jsonl").write_text("")
    (h / "journal.jsonl").write_text("")
    for b in bars[:a.start]:
        _reveal_line(st, b)
    save(st)
    print(f"replay '{a.id}' initialised: {a.symbol} {a.tf}m, {len(bars)} bars, "
          f"{bars[0]['ts'][:10]} -> {bars[-1]['ts'][:10]}")
    print(f"equity ${st['equity']:,.2f}   cursor {st['cursor']}/{len(bars)}")
    print("read ONLY workspace/paper/REPLAY/%s/visible.jsonl - never the source series." % a.id)


def _reveal_line(st: dict, bar: dict) -> None:
    with (home(st["id"]) / "visible.jsonl").open("a") as fh:
        fh.write(json.dumps(bar) + "\n")
    st["cursor"] += 1


def _round(sp: dict, px: float) -> float:
    return round(round(px / sp["tick"]) * sp["tick"], 8)


def _size(st: dict, entry: float, stop: float) -> tuple[int, float, str]:
    sp = st["spec"]
    dist = abs(entry - stop)
    if dist < sp["min_stop_ticks"] * sp["tick"]:
        return 0, 0.0, (f"stop {dist/sp['tick']:.1f} ticks is inside min_stop_ticks "
                        f"{sp['min_stop_ticks']} - noise, refused")
    dd = max(0.0, st["peak"] - st["equity"])
    allowed, mult = permitted_risk(st["equity"], dd)
    if allowed < CFG["min_dollar_risk"]:
        return 0, allowed, (f"ABSORBING STATE: drawdown ${dd:,.2f} permits ${allowed:.2f} "
                            f"against min_dollar_risk ${CFG['min_dollar_risk']:.2f} "
                            f"(ladder x{mult:.2f}) - the account cannot trade")
    per = dist * sp["point_value"]
    n = int(allowed // per)
    if n < 1:
        return 0, allowed, (f"one contract risks ${per:,.2f}, permitted ${allowed:.2f} "
                            f"(ladder x{mult:.2f}) - refused")
    return n, allowed, f"ladder x{mult:.2f}, permitted ${allowed:.2f}"


def _open(st: dict, key: str, bar: dict, order: dict) -> None:
    sp = st["spec"]
    sign = 1 if order["side"] == "LONG" else -1
    slip = sp["tick"] * 1.0
    entry = _round(sp, bar["o"] + sign * slip)
    stop = _round(sp, order["stop"])
    n, allowed, note = _size(st, entry, stop) if key == "position" else (
        st["position"]["contracts"] if st.get("position") else 1, 0.0, "matched")
    if key == "position" and n == 0:
        journal(st, "REFUSED", side=order["side"], reason=note, bar_ts=bar["ts"])
        print(f"REFUSED  {note}")
        st["pending"] = None
        # A placebo with no real arm beside it is not a control, it is a second
        # population. Drop it with the order it was matched to.
        st["placebo_pending"] = None
        return
    risk_pts = abs(entry - stop)
    st[key] = {"side": order["side"], "contracts": n, "entry_price": entry,
               "initial_stop": stop, "stop": stop, "target": order.get("target"),
               "entry_ts": bar["ts"], "symbol": st["symbol"],
               "risk_points": risk_pts,
               "risk_dollars": risk_pts * sp["point_value"] * n,
               "why": order.get("why", "")}
    if key == "position":
        journal(st, "ENTRY", **st[key], sizing=note)
        print(f"FILLED {order['side']} {n} {st['symbol']} @ {entry}  stop {stop}  "
              f"risk ${st[key]['risk_dollars']:,.2f}  ({note})")


def _close(st: dict, key: str, bar: dict, px: float, reason: str) -> None:
    pos = st[key]
    sp = st["spec"]
    sign = 1 if pos["side"] == "LONG" else -1
    gross = (px - pos["entry_price"]) * sign * sp["point_value"] * pos["contracts"]
    cost = sp["cost_per_contract_round_turn"] * pos["contracts"]
    net = gross - cost
    r = net / pos["risk_dollars"] if pos["risk_dollars"] else 0.0
    if key == "position":
        st["equity"] += net
        st["peak"] = max(st["peak"], st["equity"])
        st["closed"] += 1
        journal(st, "EXIT", side=pos["side"], contracts=pos["contracts"],
                symbol=pos["symbol"], entry_price=pos["entry_price"],
                initial_stop=pos["initial_stop"], exit_price=px, reason=reason,
                gross=round(gross, 2), cost=round(cost, 2), net=round(net, 2),
                r=round(r, 4), entry_ts=pos["entry_ts"], exit_ts=bar["ts"],
                equity=round(st["equity"], 2),
                drawdown=round(max(0.0, st["peak"] - st["equity"]), 2))
        print(f"CLOSED {pos['side']} @ {px}  {reason}  net ${net:,.2f}  {r:+.3f}R  "
              f"equity ${st['equity']:,.2f}")
    else:
        journal(st, "PLACEBO_EXIT", r=round(r, 4), net=round(net, 2), reason=reason)
    st[key] = None


def _resolve(st: dict, key: str, bar: dict) -> None:
    """Exits on this bar, in the conservative order engine.py uses."""
    pos = st.get(key)
    if not pos:
        return
    sp = st["spec"]
    sign = 1 if pos["side"] == "LONG" else -1
    stop, tgt = pos["stop"], pos.get("target")
    hit_stop = bar["l"] <= stop if sign > 0 else bar["h"] >= stop
    hit_tgt = (tgt is not None) and (bar["h"] >= tgt if sign > 0 else bar["l"] <= tgt)
    if hit_stop:                                    # stop wins a same-bar tie
        gapped = bar["o"] <= stop if sign > 0 else bar["o"] >= stop
        px = bar["o"] if gapped else stop
        _close(st, key, bar, _round(sp, px), "STOP_GAP" if gapped else "STOP")
        return
    if hit_tgt:
        gapped = bar["o"] >= tgt if sign > 0 else bar["o"] <= tgt
        _close(st, key, bar, _round(sp, bar["o"] if gapped else tgt), "TARGET")
        return
    if in_forbidden_window(bar["ts"]) or cycle_deadline_crossed(pos["entry_ts"], bar["ts"]):
        _close(st, key, bar, _round(sp, bar["c"]), "SESSION_FLAT")


def cmd_next(a) -> None:
    st = load(a.id)
    bars = source_bars(st["symbol"], st["tf"])
    rng = random.Random(f"{st['seed']}:{st['cursor']}")
    for _ in range(a.n):
        if st["cursor"] >= len(bars):
            print("end of series")
            break
        bar = bars[st["cursor"]]
        # 1. fill anything pending at this bar's open, before any exit test
        if st["pending"]:
            _open(st, "position", bar, st["pending"]); st["pending"] = None
        if st["placebo_pending"]:
            _open(st, "placebo_position", bar, st["placebo_pending"])
            st["placebo_pending"] = None
        # 2. resolve exits on this bar
        _resolve(st, "position", bar)
        _resolve(st, "placebo_position", bar)
        # 3. reveal it
        _reveal_line(st, bar)
        print(f"[{st['cursor']-1}] {bar['ts']}  o {bar['o']} h {bar['h']} "
              f"l {bar['l']} c {bar['c']} v {bar['v']:g}"
              + ("   <-- FORBIDDEN WINDOW" if in_forbidden_window(bar["ts"]) else ""))
    save(st)
    _print_status(st, bars)


def cmd_order(a) -> None:
    st = load(a.id)
    if st["position"]:
        sys.exit("already positioned - flat first (a positioned strategy does not look for signals)")
    if st["pending"]:
        sys.exit("an order is already pending for the next bar's open")
    st["pending"] = {"side": a.side, "stop": a.stop, "target": a.target, "why": a.why}
    journal(st, "ORDER", side=a.side, stop=a.stop, target=a.target, why=a.why)
    # the placebo: same geometry, an entry the agent did not choose, on a later bar
    rng = random.Random(f"{st['seed']}:placebo:{st['cursor']}")
    st["placebo_pending"] = {"side": rng.choice(["LONG", "SHORT"]),
                             "stop": a.stop, "target": a.target, "why": "placebo"}
    save(st)
    print(f"ORDER queued: {a.side} stop {a.stop} target {a.target}. "
          f"Fills at the OPEN of bar {st['cursor']} when you call next. A placebo is queued beside it.")


def cmd_flat(a) -> None:
    st = load(a.id)
    if not st["position"]:
        sys.exit("flat already")
    st["position"]["target"] = None
    st["position"]["stop"] = st["position"]["entry_price"]   # exit at next touch
    journal(st, "FLAT_REQUEST", why=a.why)
    save(st)
    print("flat requested - the position closes on the next bar. "
          "Note: this harness closes it at your entry, not at a chosen price, "
          "because you cannot pick a fill you have not seen.")


def _print_status(st: dict, bars: list[dict]) -> None:
    dd = max(0.0, st["peak"] - st["equity"])
    allowed, mult = permitted_risk(st["equity"], dd)
    dead = allowed < CFG["min_dollar_risk"]
    print(f"\ncursor {st['cursor']}/{len(bars)}   equity ${st['equity']:,.2f}   "
          f"peak ${st['peak']:,.2f}   drawdown ${dd:,.2f}   "
          f"permitted ${allowed:.2f} (x{mult:.2f})   closed {st['closed']}")
    if dead:
        print(f"*** ABSORBING STATE: permitted ${allowed:.2f} < min_dollar_risk "
              f"${CFG['min_dollar_risk']:.2f}. No further trade is possible. "
              f"has_failed is still False and ${CFG['max_total_drawdown']-dd:,.0f} "
              f"of the allowance is unspendable. ***")
    if st["position"]:
        p = st["position"]
        print(f"POSITION {p['side']} {p['contracts']} @ {p['entry_price']} "
              f"stop {p['stop']} target {p['target']} since {p['entry_ts']}")
    if st["pending"]:
        print(f"PENDING {st['pending']['side']} fills at the next bar's open")


def cmd_status(a) -> None:
    st = load(a.id)
    _print_status(st, source_bars(st["symbol"], st["tf"]))


def cmd_journal(a) -> None:
    p = home(a.id) / "journal.jsonl"
    rows = [json.loads(l) for l in p.open() if l.strip()]
    for r in rows[-a.tail:]:
        print(json.dumps(r))
    print(f"\n{len(rows)} records")


def cmd_score(a) -> None:
    st = load(a.id)
    rows = [json.loads(l) for l in (home(a.id) / "journal.jsonl").open() if l.strip()]
    real = [r["r"] for r in rows if r["kind"] == "EXIT"]
    plac = [r["r"] for r in rows if r["kind"] == "PLACEBO_EXIT"]
    print(f"replay {a.id}  {st['symbol']} {st['tf']}m  cursor {st['cursor']}/{st['n_source']}")
    print(f"equity ${st['equity']:,.2f}  from ${CFG['starting_equity']:,.2f}  "
          f"peak ${st['peak']:,.2f}  drawdown ${max(0.0,st['peak']-st['equity']):,.2f}")
    for name, xs in (("REAL", real), ("PLACEBO", plac)):
        if not xs:
            print(f"{name:8} no closed trades"); continue
        m = statistics.mean(xs)
        sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
        t = m / (sd / math.sqrt(len(xs))) if sd else 0.0
        wins = sum(1 for x in xs if x > 0)
        print(f"{name:8} n {len(xs):>4}  mean {m:+.4f}R  sd {sd:.4f}  "
              f"t {t:+.3f}  win {100*wins/len(xs):.1f}%")
    if real and plac and len(real) > 1 and len(plac) > 1:
        m1, m2 = statistics.mean(real), statistics.mean(plac)
        s1, s2 = statistics.stdev(real), statistics.stdev(plac)
        se = math.sqrt(s1**2/len(real) + s2**2/len(plac))
        z = (m1 - m2)/se if se else 0.0
        ft = math.sqrt(2*math.log(max(2, a.trials)))
        print(f"\nreal - placebo: {m1-m2:+.4f}R   Welch z {z:+.3f}   "
              f"(NOT T.ab; D28)   free_t({a.trials}) {ft:.3f}")
        print(f"  {'CLEARS' if abs(z) > ft else 'does NOT clear'} its stated threshold.")
        if abs(z) > 4.5:
            print("  *** |z| > 4.5. Nothing in ~3M evaluations in this repository has ever")
            print("      exceeded t = 3.923. Treat this as evidence of a LOOK-AHEAD LEAK")
            print("      before treating it as evidence of skill. Audit the journal's")
            print("      visible_bars against each decision. ***")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "next", "order", "flat", "status", "journal", "score"):
        s = sub.add_parser(name)
        s.add_argument("--id", default="R1")
        if name == "init":
            s.add_argument("--symbol", required=True)
            s.add_argument("--tf", type=int, required=True)
            s.add_argument("--start", type=int, default=0)
            s.add_argument("--seed", default="replay-v1")
        if name == "next":
            s.add_argument("--n", type=int, default=1)
        if name == "order":
            s.add_argument("--side", choices=["LONG", "SHORT"], required=True)
            s.add_argument("--stop", type=float, required=True)
            s.add_argument("--target", type=float, default=None)
            s.add_argument("--why", default="")
        if name == "flat":
            s.add_argument("--why", default="")
        if name == "journal":
            s.add_argument("--tail", type=int, default=20)
        if name == "score":
            s.add_argument("--trials", type=int, default=1)
    a = ap.parse_args(argv)
    return {"init": cmd_init, "next": cmd_next, "order": cmd_order, "flat": cmd_flat,
            "status": cmd_status, "journal": cmd_journal, "score": cmd_score}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
