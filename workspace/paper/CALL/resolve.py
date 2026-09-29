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
import math
import pathlib
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from futures_agents.config import CONTRACTS  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "live"   # base layer: symlinks to data/archive (0000-archive); fetch deltas land beside them, gitignored
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

def plan_thesis(plan: dict) -> str:
    """The plan's stated thesis, whichever key it was written under.

    Two of the four live plans carry only `why_short`; `CALL-0001`/`CALL-0002` carry both.
    Indexing `plan["why"]` unconditionally raised KeyError and took down the ENTIRE resolve
    run - not just the one plan - at the exact moment CALL-0003's window expired (N33). This
    returns the thesis without asserting which key holds it, and says so plainly when neither
    does rather than inventing one.
    """
    for k in ("why", "why_short"):
        v = plan.get(k)
        if v:
            return v
    return "(no thesis recorded under 'why' or 'why_short')"


def unreachable(plan: dict, bars: list[dict], expiry: str | None) -> tuple[bool, dict]:
    """Is this plan's trigger so far away, with so little window left, that it cannot fill?

    THE OWNER'S CHANGE, 2026-09-28. Until now a pending plan could only die by the CLOCK. So
    CALL-0001 sat on the book for seventeen hours as a LONG, 493.50 points (6.28 ATR) above a
    market that fell all day, reported "live" at every check, blocking the book and guaranteed to
    produce no outcome. The owner called that being set in my ways and he was right: N8 forbids
    EDITING a plan after watching price, which is not the same as never retiring one.

    THE THRESHOLD IS MEASURED, NOT CHOSEN. P(price touches a level D*ATR away within T bars),
    over ~3,645 origins per symbol on `data/archive` 15m (ends 2026-09-25, out of sample):

        D(ATR)    T=4     T=8    T=16    T=32
          0.5   67.0%   77.3%   84.3%   89.5%
          1.0   39.7%   54.9%   68.6%   78.4%
          2.0   12.7%   25.7%   43.0%   59.8%
          3.0    4.1%   12.5%   26.2%   42.8%
          4.0    1.9%    6.2%   15.7%   30.7%
          6.0    0.6%    2.0%    6.3%   15.7%

    MGC reproduces it to within 1 point everywhere. Price travel scales as sqrt(time), so the
    10% contour is `D = 1.2 * sqrt(T)` - checked against the table at every T above and landing
    at 9-12% each time. That is the rule: **VOID when distance_ATR > 1.2 * sqrt(bars_remaining)**,
    i.e. when the plan has under roughly a 1-in-10 chance of being REACHED at all.

    WHY THIS IS NOT AN N8 EDIT. It can only ever REMOVE a plan. It cannot move an entry, widen a
    stop, shift a target or change size, so it cannot make any plan fill better or win more; the
    worst it can do is deny the desk an outcome. It is mechanical - trigger price, measured ATR and
    the clock, no per-trade discretion - and it lives in the resolver precisely so that I cannot
    apply it selectively to the plans I have gone off. Voided plans get their own resolution
    `VOID_UNREACHABLE`, never EXPIRED and never a win or a loss, so the void RATE is itself
    auditable: if this starts retiring plans that would have filled and paid, the record shows it.
    """
    if not bars or not expiry:
        return False, {}
    trs = [max(bars[i]["h"] - bars[i]["l"],
               abs(bars[i]["h"] - bars[i - 1]["c"]),
               abs(bars[i]["l"] - bars[i - 1]["c"])) for i in range(1, len(bars))]
    if len(trs) < 14:
        return False, {}
    atr = sum(trs[-14:]) / 14.0
    if atr <= 0:
        return False, {}
    px = bars[-1]["c"]
    dist_atr = abs(plan["trigger_price"] - px) / atr
    step = plan["bar_minutes"]
    remaining = (datetime.fromisoformat(expiry) - datetime.fromisoformat(bars[-1]["ts"])) \
        .total_seconds() / 60.0 / step
    if remaining <= 0:
        return False, {}                      # the clock will retire it; leave that path alone
    limit_atr = 1.2 * math.sqrt(remaining)
    facts = {"price": px, "atr": round(atr, 2), "distance_points": round(plan["trigger_price"] - px, 2),
             "distance_atr": round(dist_atr, 2), "bars_remaining": round(remaining, 1),
             "void_above_atr": round(limit_atr, 2)}
    return dist_atr > limit_atr, facts


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

        limit = plan.get("trigger_type", "").startswith("LIMIT")
        for bar in bars:
            if limit:
                # A LIMIT waits for price to come TO it: a sell limit sits ABOVE the market
                # and fills when the bar trades up into it; a buy limit sits BELOW.
                touched = bar["h"] >= trig if side == "SHORT" else bar["l"] <= trig
            else:
                touched = bar["h"] > trig if side == "LONG" else bar["l"] < trig
            if not touched:
                continue
            if limit:
                # A limit fills at its price or BETTER - the opposite of a stop. If the bar
                # opened beyond the limit the fill is that better open. Modelling a limit
                # like a stop would charge slippage that a resting order does not pay, and
                # modelling it as always-better would be the flattering error; this takes
                # the bar's open only when the open is genuinely through the level.
                raw = max(trig, bar["o"]) if side == "SHORT" else min(trig, bar["o"])
                slip = 0.0
            else:
                # Rule 2: a stop entry fills at the trigger or worse.
                raw = max(trig, bar["o"]) if side == "LONG" else min(trig, bar["o"])
            spec = CONTRACTS[sym]
            if not limit:
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
                "entry_fill_note": (
                    ("limit filled at the bar open, better than the limit price"
                     if (bar["o"] > trig if side == "SHORT" else bar["o"] < trig)
                     else "resting limit filled at its price, no slippage charged")
                    if limit else
                    ("gapped through the trigger; filled at the bar open"
                     if (bar["o"] > trig if side == "LONG" else bar["o"] < trig)
                     else "filled at the trigger plus one tick of slippage")),
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
                "confidence": plan["confidence"], "why": plan_thesis(plan),
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
            void, vf = unreachable(plan, all_bars, expiry)
            if void and not expired:
                plan["status"] = "VOID_UNREACHABLE"
                plan["voided_at_utc"] = now_iso
                plan["void_facts"] = vf
                changed = True
                append_journal({
                    "ts": now_iso, "call_id": plan["call_id"], "symbol": sym, "side": None,
                    "entry_price": None, "initial_stop": None, "target": None,
                    "contracts": 0, "risk_dollars": 0.0,
                    "ladder_mult": plan.get("ladder_mult"), "rr": None,
                    "confidence": "NO TRADE",
                    "why": (f"pre-registered {side} retired UNREACHABLE, not expired. Trigger "
                            f"{trig} sits {vf['distance_points']:+.2f} points = {vf['distance_atr']:.2f} "
                            f"ATR from {vf['price']:.2f} with {vf['bars_remaining']:.1f} bars left; "
                            f"the measured 10% reach contour at that horizon is "
                            f"{vf['void_above_atr']:.2f} ATR. Under a 1-in-10 chance of being "
                            f"REACHED, never mind won. Original thesis: {plan_thesis(plan)[:160]}"),
                    "basis": basis, "as_of": all_bars[-1]["ts"],
                    "pre_registered_at": plan["created_utc"],
                    "resolution": "VOID_UNREACHABLE",
                    "void_facts": vf,
                    "paper": "PAPER - UNVALIDATED",
                    "outcome": {"result": "NO_FILL", "reason": "voided unreachable",
                                "net_dollars": 0.0, "r_multiple": 0.0,
                                "resolved_at_utc": now_iso},
                })
                log.append(f"VOID {plan['call_id']} {sym} {side} UNREACHABLE - "
                           f"{vf['distance_atr']:.2f} ATR away, {vf['bars_remaining']:.1f} bars "
                           f"left, void contour {vf['void_above_atr']:.2f} ATR")
            elif expired:
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
                            f"Original thesis: {plan_thesis(plan)[:200]}"),
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
        # Rule 5 USED to say "strictly after the entry bar", and that hid a real stop-out.
        #
        # CALL-0006 filled at 30560.00 on the 15m 12:15 bar. That SAME bar printed a high of
        # 30628.75 - 10.75 points through its 30618.00 stop - and the strictly-after rule meant
        # the resolver never looked, so the desk carried a position that in fact was stopped.
        # An exclusion that can only ever DELETE losses is not conservatism, it is a flattering
        # error, and it would have put a fabricated open position in the ledger.
        #
        # The general worry behind the old rule is real: OHLC cannot order two touches inside one
        # bar. But it is not always undecidable. When a LIMIT fills, price must TRAVEL to the
        # limit from the far side, and a stop lying BEYOND the entry in that same direction can
        # only be reached afterwards. Here the 12:15 bar opened at 30515.75, BELOW the 30560.00
        # sell limit, so price rose through the limit and then on to 30628.75 - forced ordering,
        # and confirmed at 5m where the two touches fall in different bars (12:15 h 30591.50
        # crosses the limit, 12:20 h 30628.75 crosses the stop).
        #
        # So the entry bar is scanned only when the ordering is FORCED, which is exactly the
        # limit-entry case: side SHORT with the bar opening below the entry and the stop above
        # it, or side LONG with the bar opening above the entry and the stop below it. A stop
        # entry never qualifies, because there the stop sits on the opposite side of the travel
        # and could have been touched before the fill.
        #
        # AND ON THE ENTRY BAR ONLY THE STOP IS CHECKED, NEVER THE TARGET. Reaching a target on
        # the entry bar is NOT forced by the same argument, so crediting one would invent wins.
        # This check can therefore only ever turn an open position into a LOSS - the same
        # asymmetry that justifies the breakout prohibition and the unreachable-void rule, and
        # the only direction in which a mid-flight change to the resolver is safe to make.
        series = load_bars(sym, pos["bar_minutes"])
        bars = [b for b in series if b["ts"] > pos["entry_bar_ts"]]
        entry_bar = next((b for b in series if b["ts"] == pos["entry_bar_ts"]), None)
        if entry_bar is not None and (
                (side == "SHORT" and entry_bar["o"] < pos["entry_price"]
                 and pos["stop"] > pos["entry_price"])
                or (side == "LONG" and entry_bar["o"] > pos["entry_price"]
                    and pos["stop"] < pos["entry_price"])):
            bars = [entry_bar] + bars
        closed = False

        for bar in bars:
            stop_hit = bar["l"] <= pos["stop"] if side == "LONG" else bar["h"] >= pos["stop"]
            pending_tp = next((t for t in pos["tps"] if not t["hit"]), None)
            tp_hit = False
            if pending_tp and bar["ts"] != pos["entry_bar_ts"]:   # never credit a TP on the entry bar
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

    text = "\n".join(L)
    # Do not rewrite the ledger when the ONLY difference is the regenerated timestamp.
    # The stop hook requires a clean tree at the end of every turn, so a file that churns
    # every five minutes forces a commit every five minutes and buries the journal. Compare
    # with the timestamp line masked out; write only if something real moved.
    stamp_line = re.compile(r"^\*\*Regenerated:\*\* .*$", re.M)
    if LEDGER.exists():
        if stamp_line.sub("", LEDGER.read_text()) == stamp_line.sub("", text):
            return
    LEDGER.write_text(text)


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
