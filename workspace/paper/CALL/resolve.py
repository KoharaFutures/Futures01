#!/usr/bin/env python3
"""The CALL desk's paper-trade resolver: triggers, fills and outcomes from real bars only.

Owned by agent CALL (`workspace/paper/CALL/**`). Nothing here writes outside that tree.

WHY THIS EXISTS. A callout that is never resolved is a memory, not a record. This is the
only thing in this desk that may write an `outcome`, and it writes one ONLY from a bar it
fetched. Writing an outcome any other way is fabrication (CALLOUT.md, PAPER MODE).

THE FIVE HONESTY RULES, each of which is a measured constraint from this repository:

1. STUB BARS ARE NOT BARS. A bar with `volume == 0` AND `high == low` is the vendor
   carrying the previous close across a closed session. Verified 2026-09-27: the
   2026-09-27T18:00 bar on both MGC and MNQ was o=h=l=c at Friday's close with volume 0,
   the only such bar in five days of 15m data. It is dropped everywhere here. This is
   SERIES_AUDIT.md section 5's rangeless/zero-volume degeneracy, live.

2. A STOP-ENTRY FILLS AT THE TRIGGER OR WORSE, NEVER BETTER. A buy stop above the market
   fills at `max(trigger, bar.open)` plus slippage. Where the bar gapped through the
   trigger, the open is the fill. This is why `open[i+1] != close[i]` matters: SERIES_AUDIT
   section 3 measured that gap on 57-80% of boundaries, so a level is not a fill.

3. WHEN ONE BAR HOLDS BOTH THE STOP AND THE TARGET, THE STOP WINS. OHLC cannot order two
   touches inside one bar. Assuming the good one first is how a paper record flatters
   itself. The trade resolves as a loss and is flagged `ambiguous: true` so the rate of
   those is auditable rather than invisible.

4. COSTS ARE CHARGED, BOTH SIDES. `commission_per_side + exchange_fee_per_side` from
   `futures_agents/config.py`, plus one tick of slippage per side. D40 measured fees at
   9.2% of one R in this repo's thin markets; a gross-only record is not a record.

5. NOTHING RESOLVES ON THE ENTRY BAR ITSELF. Scanning the fill bar for a stop or target
   would use the same bar twice and could read a touch that preceded the entry. Resolution
   starts strictly after the entry bar.
"""
from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from futures_agents.config import CONTRACTS  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
PENDING = HERE / "pending.jsonl"
JOURNAL = HERE / "journal.jsonl"
STATE = HERE / "state.json"
LEDGER = HERE / "LEDGER.md"


# ---------------------------------------------------------------- bars

def is_stub(bar: dict) -> bool:
    """Rule 1. A zero-volume, zero-range bar is a vendor placeholder, not a session."""
    return bar.get("v", 0) == 0 and bar["h"] == bar["l"]


def load_bars(symbol: str, minutes: int) -> list[dict]:
    """Every snapshot this desk has fetched for (symbol, timeframe), stub-free and deduped.

    Snapshots accumulate one file per fetch, so later turns see earlier turns' bars. Bars
    are keyed by timestamp and the LAST fetch wins - a bar that was forming when first
    seen is replaced by its finalised version.
    """
    merged: dict[str, dict] = {}
    for path in sorted(DATA.glob(f"{symbol}_{minutes}m_fetched_*.jsonl")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            bar = json.loads(line)
            if is_stub(bar):
                continue
            merged[bar["ts"]] = bar
    return [merged[k] for k in sorted(merged)]


def costs_per_contract(symbol: str) -> float:
    """Rule 4. Round-turn fees plus one tick of slippage per side."""
    spec = CONTRACTS[symbol]
    fees = 2.0 * (spec.commission_per_side + spec.exchange_fee_per_side)
    slip = 2.0 * spec.tick_size * spec.point_value
    return fees + slip


def round_to_tick(symbol: str, price: float) -> float:
    spec = CONTRACTS[symbol]
    return round(round(price / spec.tick_size) * spec.tick_size, 6)


# ---------------------------------------------------------------- state

def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {
        "starting_equity": 50000.0,
        "equity": 50000.0,
        "peak_equity": 50000.0,
        "drawdown": 0.0,
        "realized_pnl": 0.0,
        "open": [],
        "closed": [],
    }


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2) + "\n")


def append_journal(row: dict) -> None:
    with JOURNAL.open("a") as fh:
        fh.write(json.dumps(row) + "\n")


def rewrite_journal_outcome(call_id: str, outcome: dict) -> bool:
    """Fill the `outcome` of an existing journal row in place. Never edits anything else."""
    if not JOURNAL.exists():
        return False
    rows = [json.loads(l) for l in JOURNAL.read_text().splitlines() if l.strip()]
    hit = False
    for row in rows:
        if row.get("call_id") == call_id and row.get("outcome") is None:
            row["outcome"] = outcome
            hit = True
    if hit:
        JOURNAL.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return hit


# ---------------------------------------------------------------- triggering

def check_triggers(state: dict, now_iso: str, basis: str) -> list[str]:
    """Turn pre-registered plans into open positions, on a real bar only."""
    log: list[str] = []
    if not PENDING.exists():
        return log
    plans = [json.loads(l) for l in PENDING.read_text().splitlines() if l.strip()]
    open_ids = {p["call_id"] for p in state["open"]}
    done_ids = {p["call_id"] for p in state["closed"]}
    changed = False

    for plan in plans:
        if plan.get("status") != "PENDING":
            continue
        if plan["call_id"] in open_ids or plan["call_id"] in done_ids:
            continue
        sym = plan["symbol"]
        all_bars = [b for b in load_bars(sym, plan["bar_minutes"])
                    if b["ts"] > plan["created_bar_ts"]]
        if not all_bars:
            continue
        # Expiry truncates the window a trigger may fire in. It must ALSO retire the plan,
        # or an untriggered plan sits in the ledger reading PENDING forever - state the
        # ledger would then be misreporting as live.
        expiry = plan.get("expires_bar_ts")
        bars = [b for b in all_bars if b["ts"] <= expiry] if expiry else all_bars
        expired = bool(expiry) and all_bars[-1]["ts"] > expiry
        side = plan["side"]
        trig = plan["trigger_price"]

        for bar in bars:
            touched = bar["h"] > trig if side == "LONG" else bar["l"] < trig
            if not touched:
                continue
            # Rule 2: a stop entry fills at the trigger or worse.
            raw = max(trig, bar["o"]) if side == "LONG" else min(trig, bar["o"])
            spec = CONTRACTS[sym]
            slip = spec.tick_size * (1 if side == "LONG" else -1)
            entry = round_to_tick(sym, raw + slip)
            risk_pts = plan["stop_points"]
            stop = round_to_tick(sym, entry - risk_pts if side == "LONG" else entry + risk_pts)
            tps = []
            for tp in plan["tp_r_multiples"]:
                d = risk_pts * tp["r"]
                tps.append({
                    "label": tp["label"], "r": tp["r"], "fraction": tp["fraction"],
                    "price": round_to_tick(sym, entry + d if side == "LONG" else entry - d),
                    "hit": False,
                })
            pos = {
                "call_id": plan["call_id"], "symbol": sym, "side": side,
                "bar_minutes": plan["bar_minutes"],
                "entry_price": entry, "entry_bar_ts": bar["ts"],
                "initial_stop": stop, "stop": stop, "risk_points": risk_pts,
                "contracts": plan["contracts"], "remaining": plan["contracts"],
                "tps": tps,
                "risk_dollars": round(risk_pts * spec.point_value * plan["contracts"], 2),
                "realized": 0.0, "triggered_at_utc": now_iso, "basis_at_trigger": basis,
                "entry_fill_note": ("gapped through the trigger; filled at the bar open"
                                    if (bar["o"] > trig if side == "LONG" else bar["o"] < trig)
                                    else "filled at the trigger plus one tick of slippage"),
            }
            state["open"].append(pos)
            plan["status"] = "TRIGGERED"
            changed = True
            append_journal({
                "ts": now_iso, "call_id": plan["call_id"], "symbol": sym, "side": side,
                "entry_price": entry, "initial_stop": stop,
                "target": tps[0]["price"] if tps else None,
                "all_targets": [{"label": t["label"], "price": t["price"], "r": t["r"]} for t in tps],
                "contracts": plan["contracts"], "risk_dollars": pos["risk_dollars"],
                "ladder_mult": plan.get("ladder_mult"),
                "rr": tps[0]["r"] if tps else None,
                "confidence": plan["confidence"], "why": plan["why"],
                "basis": basis, "as_of": bars[-1]["ts"],
                "entry_bar_ts": bar["ts"], "fill_note": pos["entry_fill_note"],
                "pre_registered_at": plan["created_utc"],
                "outcome": None,
            })
            log.append(f"TRIGGERED {plan['call_id']} {sym} {side} @ {entry} "
                       f"(bar {bar['ts']}) stop {stop} risk ${pos['risk_dollars']:.2f}")
            break
        else:
            # No bar in the window triggered it. If the window has closed, retire the plan
            # and journal the non-event: a setup that never triggered is a result, and a
            # record holding only the trades that fired is a record of what I remember.
            if expired:
                plan["status"] = "EXPIRED"
                plan["expired_at_utc"] = now_iso
                changed = True
                append_journal({
                    "ts": now_iso, "call_id": plan["call_id"], "symbol": sym, "side": None,
                    "entry_price": None, "initial_stop": None, "target": None,
                    "contracts": 0, "risk_dollars": 0.0,
                    "ladder_mult": plan.get("ladder_mult"), "rr": None,
                    "confidence": "NO TRADE",
                    "why": (f"pre-registered {side} never triggered. Window "
                            f"{plan['created_bar_ts']} -> {expiry} closed with no real bar "
                            f"{'above' if side == 'LONG' else 'below'} {trig}. "
                            f"Original thesis: {plan['why'][:200]}"),
                    "basis": basis, "as_of": all_bars[-1]["ts"],
                    "pre_registered_at": plan["created_utc"],
                    "resolution": "EXPIRED_UNTRIGGERED",
                    "paper": "PAPER - UNVALIDATED",
                    "outcome": {"result": "NO_FILL", "reason": "expired untriggered",
                                "net_dollars": 0.0, "r_multiple": 0.0,
                                "resolved_at_utc": now_iso},
                })
                log.append(f"EXPIRED {plan['call_id']} {sym} {side} - never triggered "
                           f"(window closed {expiry})")

    if changed:
        PENDING.write_text("".join(json.dumps(p) + "\n" for p in plans))
    return log


# ---------------------------------------------------------------- resolving

def resolve_open(state: dict, now_iso: str) -> list[str]:
    """Walk real bars after entry and resolve stops and targets. Rules 3 and 5."""
    log: list[str] = []
    still_open = []

    for pos in state["open"]:
        sym, side = pos["symbol"], pos["side"]
        spec = CONTRACTS[sym]
        sign = 1.0 if side == "LONG" else -1.0
        # Rule 5: strictly after the entry bar.
        bars = [b for b in load_bars(sym, pos["bar_minutes"]) if b["ts"] > pos["entry_bar_ts"]]
        closed = False

        for bar in bars:
            stop_hit = bar["l"] <= pos["stop"] if side == "LONG" else bar["h"] >= pos["stop"]
            pending_tp = next((t for t in pos["tps"] if not t["hit"]), None)
            tp_hit = False
            if pending_tp:
                tp_hit = (bar["h"] >= pending_tp["price"] if side == "LONG"
                          else bar["l"] <= pending_tp["price"])

            if stop_hit and tp_hit:
                # Rule 3: the stop wins, and the bar is flagged.
                qty = pos["remaining"]
                gross = sign * (pos["stop"] - pos["entry_price"]) * spec.point_value * qty
                net = gross - costs_per_contract(sym) * qty
                pos["realized"] += net
                pos["remaining"] = 0
                pos["exit_price"], pos["exit_bar_ts"] = pos["stop"], bar["ts"]
                pos["exit_reason"] = "STOP (ambiguous bar - stop and target both touched)"
                pos["ambiguous"] = True
                closed = True
                break

            if stop_hit:
                qty = pos["remaining"]
                gross = sign * (pos["stop"] - pos["entry_price"]) * spec.point_value * qty
                net = gross - costs_per_contract(sym) * qty
                pos["realized"] += net
                pos["remaining"] = 0
                pos["exit_price"], pos["exit_bar_ts"] = pos["stop"], bar["ts"]
                pos["exit_reason"] = ("STOP" if pos["stop"] == pos["initial_stop"]
                                     else "STOP (moved to breakeven)")
                pos["ambiguous"] = False
                closed = True
                break

            if tp_hit and pending_tp:
                qty = max(1, round(pos["contracts"] * pending_tp["fraction"]))
                qty = min(qty, pos["remaining"])
                gross = sign * (pending_tp["price"] - pos["entry_price"]) * spec.point_value * qty
                net = gross - costs_per_contract(sym) * qty
                pos["realized"] += net
                pos["remaining"] -= qty
                pending_tp["hit"] = True
                pending_tp["hit_bar_ts"] = bar["ts"]
                pending_tp["qty"] = qty
                log.append(f"  {pos['call_id']} {pending_tp['label']} hit @ "
                           f"{pending_tp['price']} ({qty} lot) bar {bar['ts']} net ${net:+.2f}")
                # A scale-out moves the stop to breakeven: this is the governor that
                # BRIEF.md measures as net protective (|z| 6.164).
                if pos["remaining"] > 0:
                    pos["stop"] = pos["entry_price"]
                else:
                    pos["exit_price"], pos["exit_bar_ts"] = pending_tp["price"], bar["ts"]
                    pos["exit_reason"] = f"TARGET {pending_tp['label']}"
                    pos["ambiguous"] = False
                    closed = True
                    break

        if closed:
            pos["closed_at_utc"] = now_iso
            pos["net"] = round(pos["realized"], 2)
            pos["r_multiple"] = round(
                pos["net"] / (pos["risk_points"] * spec.point_value * pos["contracts"]), 3)
            pos["result"] = "WIN" if pos["net"] > 0 else ("LOSS" if pos["net"] < 0 else "SCRATCH")
            state["closed"].append(pos)
            state["realized_pnl"] = round(state["realized_pnl"] + pos["net"], 2)
            state["equity"] = round(state["starting_equity"] + state["realized_pnl"], 2)
            state["peak_equity"] = max(state["peak_equity"], state["equity"])
            state["drawdown"] = round(state["peak_equity"] - state["equity"], 2)
            rewrite_journal_outcome(pos["call_id"], {
                "exit_price": pos["exit_price"], "exit_bar_ts": pos["exit_bar_ts"],
                "reason": pos["exit_reason"], "net_dollars": pos["net"],
                "r_multiple": pos["r_multiple"], "result": pos["result"],
                "ambiguous_bar": pos.get("ambiguous", False),
                "targets_hit": [t["label"] for t in pos["tps"] if t["hit"]],
                "resolved_at_utc": now_iso,
            })
            log.append(f"CLOSED {pos['call_id']} {pos['result']} {pos['exit_reason']} "
                       f"net ${pos['net']:+.2f} ({pos['r_multiple']:+.3f}R)")
        else:
            still_open.append(pos)

    state["open"] = still_open
    return log


# ---------------------------------------------------------------- ledger

def write_ledger(state: dict, basis: str, now_iso: str) -> None:
    closed = state["closed"]
    wins = [p for p in closed if p["result"] == "WIN"]
    losses = [p for p in closed if p["result"] == "LOSS"]
    amb = [p for p in closed if p.get("ambiguous")]
    gross_w = sum(p["net"] for p in wins)
    gross_l = sum(p["net"] for p in losses)
    n = len(closed)

    L = ["# CALL desk — paper trade ledger",
         "",
         "**PAPER — UNVALIDATED.** Every row is a paper trade. No strategy in this repository",
         "has a measured edge (largest *t* 3.923 against `free_t` 5.46), so this ledger is a",
         "record of a *process*, not evidence of one. It is generated by `resolve.py`;",
         "do not hand-edit it.",
         "",
         f"**Regenerated:** {now_iso} · **basis:** {basis}",
         "",
         "## Account",
         "",
         "| | |",
         "|---|---|",
         f"| starting equity | ${state['starting_equity']:,.2f} |",
         f"| equity | ${state['equity']:,.2f} |",
         f"| peak equity | ${state['peak_equity']:,.2f} |",
         f"| **drawdown** | **${state['drawdown']:,.2f}** |",
         f"| distance to the $2,800 absorbing state | ${2800 - state['drawdown']:,.2f} |",
         f"| realized P&L | ${state['realized_pnl']:+,.2f} |",
         "",
         "## Record",
         "",
         "| | |",
         "|---|---|",
         f"| closed trades | {n} |",
         f"| wins | {len(wins)} |",
         f"| losses | {len(losses)} |",
         f"| win rate | {(100.0 * len(wins) / n) if n else 0:.1f}% |",
         f"| gross won | ${gross_w:+,.2f} |",
         f"| gross lost | ${gross_l:+,.2f} |",
         f"| avg win | ${(gross_w / len(wins)) if wins else 0:+,.2f} |",
         f"| avg loss | ${(gross_l / len(losses)) if losses else 0:+,.2f} |",
         f"| expectancy | {(sum(p['r_multiple'] for p in closed) / n) if n else 0:+.3f}R |",
         f"| ambiguous-bar resolutions (counted as losses) | {len(amb)} |",
         "",
         "**Rule 3 of this desk: win rate and payoff are never quoted apart.** BRIEF.md rule 3",
         "measured four times that moving a stop raises payoff ~89% and drops win rate ~14",
         "points for no expectancy gain, so either number alone is misleading.",
         ""]

    if state["open"]:
        L += ["## Open positions", "",
              "| id | symbol | side | entry | stop | next target | lots | risk $ |",
              "|---|---|---|---|---|---|---|---|"]
        for p in state["open"]:
            nt = next((t for t in p["tps"] if not t["hit"]), None)
            L.append(f"| {p['call_id']} | {p['symbol']} | {p['side']} | {p['entry_price']} | "
                     f"{p['stop']} | {nt['price'] if nt else '—'} ({nt['label'] if nt else '—'}) | "
                     f"{p['remaining']}/{p['contracts']} | ${p['risk_dollars']:,.2f} |")
        L.append("")

    if PENDING.exists():
        plans = [json.loads(l) for l in PENDING.read_text().splitlines() if l.strip()]
        live = [p for p in plans if p.get("status") == "PENDING"]
        if live:
            L += ["## Pre-registered, awaiting trigger", "",
                  "Written down *before* the price existed — which is the only thing in this",
                  "programme that buys a lower threshold (`free_t` 1.177 for one pre-registered",
                  "hypothesis against 5.46 for a searched population).", "",
                  "| id | symbol | side | trigger | stop pts | targets (R) | lots | expires |",
                  "|---|---|---|---|---|---|---|---|"]
            for p in live:
                tps = ", ".join(f"{t['label']} {t['r']}R" for t in p["tp_r_multiples"])
                L.append(f"| {p['call_id']} | {p['symbol']} | {p['side']} | {p['trigger_price']} | "
                         f"{p['stop_points']} | {tps} | {p['contracts']} | "
                         f"{p.get('expires_bar_ts', '—')} |")
            L.append("")

    if closed:
        L += ["## Closed trades", "",
              "| id | symbol | side | entry | stop | exit | reason | targets hit | net $ | R | result |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for p in closed:
            hits = ", ".join(t["label"] for t in p["tps"] if t["hit"]) or "—"
            flag = " ⚠" if p.get("ambiguous") else ""
            L.append(f"| {p['call_id']} | {p['symbol']} | {p['side']} | {p['entry_price']} | "
                     f"{p['initial_stop']} | {p['exit_price']} | {p['exit_reason']}{flag} | {hits} | "
                     f"${p['net']:+,.2f} | {p['r_multiple']:+.3f} | **{p['result']}** |")
        L += ["", "⚠ = one bar held both the stop and the target; OHLC cannot order them, so it",
              "resolved as a loss (rule 3 of `resolve.py`).", ""]

    LEDGER.write_text("\n".join(L))


# ---------------------------------------------------------------- main

def main() -> int:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    basis = (pathlib.Path(HERE / "BASIS").read_text().strip()
             if (HERE / "BASIS").exists() else "unknown")
    state = load_state()
    print(f"resolve.py  {now}  basis {basis}")
    for line in check_triggers(state, now, basis):
        print(" ", line)
    for line in resolve_open(state, now):
        print(" ", line)
    save_state(state)
    write_ledger(state, basis, now)
    print(f"  open {len(state['open'])}  closed {len(state['closed'])}  "
          f"equity ${state['equity']:,.2f}  drawdown ${state['drawdown']:,.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
