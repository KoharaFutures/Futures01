#!/usr/bin/env python3
"""HEAT — how close every trade came to its stop, and how much of the stop it used.

Owner, 2026-09-28 20:09 ET: *"i want as you make these calls i want you to learn how close you
were to your Stop losses as well."*

WHAT THIS MEASURES, in the standard language:

  MAE   maximum ADVERSE excursion: the worst the trade ever looked, in points, from entry.
  MFE   maximum FAVOURABLE excursion: the best it ever looked.
  HEAT  MAE as a fraction of the stop distance -- "how much of the stop did it use".
        HEAT 0.00 = never went against me at all.  HEAT 1.00 = stopped out.
        HEAT 0.90 on a WINNER is the number that matters: it means the trade paid, but one
        more tick of noise would have turned it into a full loss. A book of those is not a
        system with good stops, it is a book that got away with tight ones.

WHY IT EARNS ITS PLACE. Rule 4 says structural stops must never be tighter than ~0.5 ATR,
because below that the tighter stop is hit more often than the better ratio is worth. That rule
was measured on a population. HEAT is how this desk measures it on ITS OWN trades: if winners
routinely run HEAT above ~0.7 the stops are too tight for the noise in this feed, and if losers
routinely show MFE far above zero before dying, the exits are wrong rather than the entries.

HONEST LIMIT, stated because it bounds every number below. MAE here is computed from the finest
bars this environment has -- 1m where available, else 5m -- so it is a LOWER BOUND on the true
excursion. Ticks inside a 1m bar can exceed its high and low, and there is no tick data here.
A HEAT of 0.95 measured this way could have been a touch of the stop in reality. Never report
HEAT as exact, and never use it to argue a stop was "not quite" hit -- resolve.py decides that
from the bars, and it is the only thing that may.

Owned by agent CALL.
"""
from __future__ import annotations
import datetime, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from chart import load  # noqa: E402

PV = {"MGC": 10.0, "MNQ": 2.0}


def finest(sym: str, bar_minutes: int):
    """Finest series available, so MAE is as tight a lower bound as the data allows."""
    for m in (1, 5, 15):
        if m > bar_minutes:
            break
        try:
            b = load(sym, m)
            if b:
                return b, m
        except Exception:
            continue
    return load(sym, bar_minutes), bar_minutes


def excursions(pos: dict) -> dict:
    bars, grain = finest(pos["symbol"], pos["bar_minutes"])
    # CLIP AT THE EXIT. Measuring a closed trade's excursion through to "now" is meaningless:
    # a stopped-out trade then reports how far price ran AFTER the exit, which says nothing about
    # whether the stop was sized right. Found this in my own tool minutes after writing it --
    # CALL-0006 read HEAT 2.79, which was not 2.79 of stop used, it was price continuing for hours.
    seg = [b for b in bars if b["ts"] >= pos["entry_bar_ts"]]
    if pos.get("exit_bar_ts"):
        # END OF THE EXIT BAR, not its timestamp. A 15m plan exiting on the 12:15 bar was filled
        # and stopped somewhere inside 12:15-12:30, so clipping 1m bars at "<= 12:15" keeps ONE
        # minute and reports MAE 0.00 for a trade that demonstrably hit its stop. Second bug in
        # this tool in five minutes, and the check that caught it is that a stopped-out trade must
        # read HEAT >= 1.00 by definition -- if it does not, the window is wrong, not the trade.
        end = (datetime.datetime.fromisoformat(pos["exit_bar_ts"])
               + datetime.timedelta(minutes=pos["bar_minutes"]))
        seg = [b for b in seg if datetime.datetime.fromisoformat(b["ts"]) < end]
        # AND STOP AT THE BAR THAT BREACHED THE EXIT. Running to the end of the exit bar measures
        # how far price continued AFTER the trade was over, which is not stop usage. CALL-0006 read
        # MAE 162.00 / HEAT 2.79 that way: real movement, but 96 of those points happened after the
        # 30618.00 stop was already hit. The honest reading of a stopped-out trade is HEAT just over
        # 1.00 -- the stop was reached, plus whatever the breaching bar overshot -- and an MFE
        # measured only over the life of the trade.
        xp = pos.get("exit_price")
        if xp is not None:
            for i, b in enumerate(seg):
                if b["l"] <= xp <= b["h"]:
                    seg = seg[:i + 1]
                    break
    if not seg:
        return {"n": 0, "grain": grain}
    e, side, risk = pos["entry_price"], pos["side"], pos["risk_points"]
    hi = max(b["h"] for b in seg)
    lo = min(b["l"] for b in seg)
    if side == "SHORT":
        mae, mfe = hi - e, e - lo
    else:
        mae, mfe = e - lo, hi - e
    mae, mfe = max(mae, 0.0), max(mfe, 0.0)
    return {
        "n": len(seg), "grain": grain,
        "mae": mae, "mfe": mfe,
        "heat": mae / risk if risk else float("nan"),
        "mfe_r": mfe / risk if risk else float("nan"),
        "mae_usd": mae * PV[pos["symbol"]] * pos["contracts"],
        "stop_gap": risk - mae,
    }


def line(pos: dict, x: dict, closed: bool) -> str:
    if not x["n"]:
        return f"  {pos['call_id']} {pos['symbol']} {pos['side']:5s}  no bars since entry yet"
    tag = "CLOSED" if closed else "OPEN  "
    res = f" {pos.get('result','')} {pos.get('r_multiple',0):+.3f}R" if closed else ""
    return (f"  {pos['call_id']} {pos['symbol']} {pos['side']:5s} {tag}  "
            f"MAE {x['mae']:6.2f}pt (${x['mae_usd']:5.0f})  HEAT {x['heat']:5.2f}  "
            f"MFE {x['mfe']:6.2f}pt ({x['mfe_r']:+.2f}R)  "
            f"stop had {x['stop_gap']:+6.2f}pt left  [{x['grain']}m bars]{res}")


def main() -> int:
    st = json.loads((HERE / "state.json").read_text())
    print("HEAT — MAE, MFE and stop usage.  MAE is a LOWER BOUND: finest bars available, no ticks.")
    rows = []
    for p in st["open"]:
        x = excursions(p); rows.append((p, x, False)); print(line(p, x, False))
    for p in st["closed"]:
        x = excursions(p); rows.append((p, x, True)); print(line(p, x, True))

    graded = [(p, x) for p, x, c in rows if x.get("n") and c and p["call_id"] != "CALL-0002"]
    if graded:
        print(f"\n  MEASURED closed trades (CALL-0002 EXCLUDED, N155): n={len(graded)}")
        hs = [x["heat"] for _, x in graded]
        print(f"    mean HEAT {sum(hs)/len(hs):.2f}   max {max(hs):.2f}")
        won = [(p, x) for p, x in graded if p.get("r_multiple", 0) > 0]
        if won:
            wh = [x["heat"] for _, x in won]
            print(f"    winners n={len(won)} mean HEAT {sum(wh)/len(wh):.2f}"
                  f"  <-- above ~0.70 means the stops are too tight for this feed's noise")
        else:
            print("    winners n=0 — no winner exists yet to measure stop adequacy against")
        lost = [(p, x) for p, x in graded if p.get("r_multiple", 0) <= 0]
        if lost:
            lm = [x["mfe_r"] for _, x in lost]
            print(f"    losers  n={len(lost)} mean MFE {sum(lm)/len(lm):+.2f}R"
                  f"  <-- well above 0 means the EXIT was wrong, not the entry")
    else:
        print("\n  no countable closed trade carries bars yet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
