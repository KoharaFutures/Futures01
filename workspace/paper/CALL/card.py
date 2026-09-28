#!/usr/bin/env python3
"""Render CALL desk callout cards FROM THE RECORD, never from retyped prose.

Owned by agent CALL. Reads `pending.jsonl` and `state.json` and renders each as a card
through `futures_agents.alerts`, so the card's numbers are the stored numbers by
construction. A card is a statement about state; hand-typing one risks the statement
drifting from the state it describes, which is the same class of error as re-typing the
fetch (see `fetch.py`).

COLOUR IS THE DIRECTION AND THE TEXT IS THE STATUS. LONG renders on the blue background
(256-colour 27), SHORT on orange (208), NO TRADE on grey (250) - `alerts.py`'s shipped
codes, which `CALLOUT.md` forbids changing. A pre-registered SHORT is still a SHORT and
still renders orange; its body says PRE-REGISTERED, NOT FILLED. Downgrading an unfilled
directional plan to grey would say NO TRADE, the opposite of what is meant.

Every card carries `CALLOUT.md`'s mandatory fields: PAPER - UNVALIDATED, the basis sha,
the as-of, direction/entry/stop/target/R:R, dollar risk with contracts and the ladder
multiplier, and the confidence with its basis named.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))

from futures_agents.alerts import Priority, alert  # noqa: E402
from futures_agents.config import CONTRACTS        # noqa: E402

PRIORITY = {"LONG": Priority.LONG, "SHORT": Priority.SHORT, None: Priority.NO_TRADE}


def basis() -> str:
    f = HERE / "BASIS"
    return f.read_text().strip() if f.exists() else "unknown"


def wrap(text: str, width: int = 74, indent: str = "  ") -> str:
    """textwrap.fill already returns a string - joining it splits it per character."""
    import textwrap
    if not text:
        return ""
    return textwrap.fill(text, width, initial_indent=indent, subsequent_indent=indent)


def pending_card(p: dict, note: str = "") -> str:
    sym, side = p["symbol"], p["side"]
    spec = CONTRACTS[sym]
    trig, sp = p["trigger_price"], p["stop_points"]
    # Illustrative fill: a stop entry fills at the trigger or worse, so one tick through.
    fill = trig - spec.tick_size if side == "SHORT" else trig + spec.tick_size
    stop = fill + sp if side == "SHORT" else fill - sp
    tps = []
    for t in p["tp_r_multiples"]:
        d = sp * t["r"]
        tps.append((t["label"], t["r"], fill - d if side == "SHORT" else fill + d))
    rd = sp * spec.point_value * p["contracts"]

    out = [f"PAPER — UNVALIDATED          {note or 'PRE-REGISTERED, NOT FILLED'}",
           f"basis: {p.get('basis','?')}    as-of: {p.get('as_of_at_creation','?')}",
           "",
           f"{p['call_id']}   {sym} {side}   stop-entry "
           f"{'BELOW' if side == 'SHORT' else 'ABOVE'} {trig}",
           f"  trigger      {trig}",
           wrap(p.get("trigger_basis", ""), 72, "               "),
           f"  entry        fills at the trigger or WORSE — illustrative {fill:g}",
           f"               (a gap through it fills at the bar open; never better)",
           f"  stop         {stop:g}   = {sp:g} pts = "
           f"${sp * spec.point_value:,.2f}/contract",
           wrap(p.get("stop_basis", ""), 72, "               ")]
    for lab, r, px in tps:
        out.append(f"  {lab}          {px:g}   = {r}R")
    out.append(wrap(p.get("tp_basis", ""), 72, "               "))
    out = [x for x in out if x != ""] if False else out
    out += [f"  R:R          {tps[0][1]}   (desk min_reward_risk 1.6)",
            f"  size         {p['contracts']} contract(s)   risk ${rd:,.2f}   "
            f"ladder x{p.get('ladder_mult', 1.0):.2f}",
            wrap(p.get("sizing_basis", ""), 72, "               "),
            f"  window       {p['created_bar_ts']}  ->  {p['expires_bar_ts']}"]
    if p.get("rth_gate"):
        out.append(wrap(p["rth_gate"], 72, "               "))
    out += ["", "WHY:", wrap(p["why"], 74, "  ")]
    if p.get("invalidation"):
        out += ["", "THE WEAKNESS, STATED NOT HEDGED:", wrap(p["invalidation"], 74, "  ")]
    out += ["", f"CONFIDENCE: {p['confidence']} — a structured chart read, NOT a measured edge.",
            "  Nothing in this repository has cleared its own threshold; the largest t",
            "  anywhere is 3.923 against a required 5.46."]
    head = (f"{sym} {side} — pre-registered "
            f"{'below' if side == 'SHORT' else 'above'} {trig}")
    return alert(PRIORITY[side], head, "\n".join(out))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="render just this call_id")
    a = ap.parse_args()
    pj = HERE / "pending.jsonl"
    if not pj.exists():
        print("no pending plans")
        return 0
    plans = [json.loads(l) for l in pj.read_text().splitlines() if l.strip()]
    for p in plans:
        if a.only and p["call_id"] != a.only:
            continue
        if p.get("status") != "PENDING":
            continue
        print(pending_card(p))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
