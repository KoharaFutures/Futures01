"""Did the THESIS work, independently of whether the entry ever filled?

The account owner's point, 2026-09-28: a plan that expires `NO_FILL` while price ran the
way it predicted is not the same event as one that expires `NO_FILL` because the read was
wrong. Both journal 0.0R — correctly, because no position was ever held and inventing a
number would be fabrication — but 0.0R alone destroys the distinction, and the
distinction is the whole diagnosis:

    direction right, entry unreachable  ->  fix the TRIGGER
    direction wrong                     ->  fix the READ

Those are opposite repairs, and a ledger of nothing but 0.0R cannot tell you which one
you need. Tonight makes the case: MGC fell ~60 points with two MGC shorts pre-registered
and neither filled, so the desk was right about gold for four hours and captured nothing.
That is a trigger-placement failure wearing the same 0.0R as a bad call.

WHAT THIS IS NOT. It is NOT a P&L, NOT an outcome, and NOT an R multiple. No position
existed, so there is no profit to claim and none is claimed here. `resolve.py` remains the
only thing permitted to write an outcome, `outcome` stays null until a trade actually
resolves, and nothing in this module writes to the journal or to state.json. This measures
the MARKET's behaviour after a prediction was recorded, which is a different object from
the account's behaviour, and it is reported under its own heading so the two can never be
read as one number.
"""
from __future__ import annotations

import datetime
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def track(plan: dict) -> dict:
    """Measure what price did, in the plan's direction, since the plan was written."""
    fetch = _load("fetch")
    sym, side = plan["symbol"], plan["side"]
    fr = int(plan.get("bar_minutes", 15))
    d = fetch.stored(sym, fr)

    created = plan.get("created_bar_ts")
    bars = []
    for k in sorted(d):
        o, h, l, c, v = d[k]
        if v == 0 and h == l:          # N5 stub guard
            continue
        bars.append((k, o, h, l, c))
    if not bars:
        return {"error": "no bars"}

    at_creation = [b for b in bars if b[0] <= created]
    if not at_creation:
        return {"error": "no bar at or before creation"}
    ref = at_creation[-1][4]                      # close of the bar the plan was written on
    after = [b for b in bars if b[0] > created]
    if not after:
        return {"error": "no bars since creation"}

    hi = max(b[2] for b in after)
    lo = min(b[3] for b in after)
    last = after[-1][4]

    # Favourable and adverse excursion FROM THE REFERENCE PRICE, in the plan's direction.
    # Deliberately measured from where price was when the call was made, not from the
    # unfilled trigger: the question is whether the DIRECTION was right, and the trigger is
    # the thing under suspicion.
    if side == "SHORT":
        fav, adv, now_move = ref - lo, hi - ref, ref - last
    else:
        fav, adv, now_move = hi - ref, ref - lo, last - ref

    # Did the market travel far enough, the right way, to have paid the plan's own target?
    # Using the plan's target DISTANCE applied from the reference price - not its absolute
    # target level, which is anchored to a fill that never happened.
    tgt_dist = None
    try:
        card = _load("card_png")
        spec, fill, stop, tgts, risk = card.mech(plan)
        if tgts:
            tgt_dist = abs(tgts[0][2] - fill)
    except Exception:
        pass
    stop_dist = float(plan.get("stop_points") or 0)

    verdict = "DIRECTION WRONG"
    if fav >= (tgt_dist or 1e9):
        verdict = "DIRECTION RIGHT, TARGET DISTANCE COVERED - trigger was the problem"
    elif fav > adv:
        verdict = "DIRECTION RIGHT, target distance not covered"
    elif fav == adv:
        verdict = "FLAT"

    return {
        "call_id": plan.get("call_id"), "symbol": sym, "side": side,
        "ref_price_at_creation": round(ref, 4), "created_bar_ts": created,
        "bars_since": len(after), "last": round(last, 4),
        "move_now": round(now_move, 4),
        "favourable_excursion": round(fav, 4),
        "adverse_excursion": round(adv, 4),
        "target_distance": round(tgt_dist, 4) if tgt_dist else None,
        "stop_distance": stop_dist,
        "trigger_distance_from_ref": round(abs(plan["trigger_price"] - ref), 4),
        "verdict": verdict,
        "NOT_A_PNL": ("no position was held; R is 0.0 and only resolve.py may say otherwise. "
                      "This is the market's behaviour after a recorded prediction, not the "
                      "account's."),
    }


def main() -> int:
    plans = [json.loads(l) for l in (HERE / "pending.jsonl").read_text().splitlines() if l.strip()]
    print("THESIS TRACKING - not a P&L, not an outcome, no position held")
    print(f"{'id':11s} {'sym':4s} {'side':6s} {'ref':>10s} {'now':>10s} "
          f"{'fav':>8s} {'adv':>8s} {'tgt':>8s} {'trig away':>10s}  verdict")
    for p in plans:
        if p.get("status") != "PENDING":
            continue
        t = track(p)
        if "error" in t:
            print(f"{p['call_id']:11s} {t['error']}")
            continue
        print(f"{t['call_id']:11s} {t['symbol']:4s} {t['side']:6s} "
              f"{t['ref_price_at_creation']:10.2f} {t['last']:10.2f} "
              f"{t['favourable_excursion']:8.2f} {t['adverse_excursion']:8.2f} "
              f"{str(t['target_distance']):>8s} {t['trigger_distance_from_ref']:10.2f}  {t['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
