#!/usr/bin/env python3
"""LVN/FIB AGENT — one mechanical turn. Exit code decides whether an LLM is needed at all.

Doctrine is DATA_HUB/AUTOMATION.md: a script does the repeating work every cycle and an LLM is
woken only when a pre-registered trigger actually fires. Arm A fires about 1.4 times a month, so
almost every cycle here should be silent, and silence must cost nothing.

    exit 0   quiet - nothing happened, do not wake anyone
    exit 10  attention - something a human or an LLM should see (printed as WAKE: lines)
    exit 2   data failure - the desk could not form a view

    python3 desk_check.py            # post new callouts, resolve, decide
    python3 desk_check.py --dry      # decide only, write nothing
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "workspace" / "anchors" / "lib"))
import core                                    # noqa: E402
import engine                                  # noqa: E402
import plan as planner                         # noqa: E402

ET = ZoneInfo("America/New_York")
EVENTS = HERE / "desk_events.jsonl"
DD_ALERT = 2_600.0            # RULES_AND_PITFALLS: operate as if the floor is $2,600
# The desk's own entry windows, ET. Outside these it still resolves, but it arms nothing.
WINDOW = {"MGC": (8, 13), "MNQ": (9, 15)}


def in_window(now):
    if now.weekday() >= 5:
        return []
    return [s for s, (a, b) in WINDOW.items() if a <= now.hour < b]


def try_refresh():
    """Returns (attempted, ok, note). A missing yfinance is expected, not a failure."""
    try:
        import yfinance  # noqa: F401
    except ModuleNotFoundError:
        return False, False, "no live feed (yfinance absent) - running off data/archive/"
    try:
        r = subprocess.run([sys.executable, str(ROOT / "DATA_HUB/tools/refresh_archive.py"),
                            "--fetch", "--symbols", "MGC", "MNQ", "--frames", "15", "60"],
                           capture_output=True, text=True, timeout=600)
        return True, r.returncode == 0, (r.stdout or r.stderr).strip().splitlines()[-1:] and \
            (r.stdout or r.stderr).strip().splitlines()[-1] or "fetch returned no output"
    except Exception as e:                                    # noqa: BLE001
        return True, False, f"fetch failed: {type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    now = datetime.now(ET)
    wake, notes = [], []
    attempted, ok, fnote = try_refresh()
    notes.append(fnote)
    if attempted and not ok:
        wake.append(f"DATA: live feed is configured but the fetch failed - {fnote}")

    st = planner.state()
    dd = st["peak"] - st["equity"]
    if dd >= DD_ALERT:
        wake.append(f"DRAWDOWN ${dd:,.2f} has reached the ${DD_ALERT:,.0f} alert "
                    f"(floor ${core.FLOOR_DD:,.0f}) - stop arming anything")

    # --- levels and triggers -------------------------------------------------
    active = in_window(now)
    posted = []
    try:
        rows = [r for s in engine.SYMS for r in planner.build(s, st, a.dry)]
    except Exception as e:                                    # noqa: BLE001
        print(f"FAIL: could not build a view: {type(e).__name__}: {e}")
        return 2
    if not rows:
        print("FAIL: no levels could be built for either symbol")
        return 2

    have = planner.existing_ids()
    new = [r for r in rows if r["id"] not in have]
    ids = [r["id"] for r in new]
    if len(ids) != len(set(ids)):
        print("FAIL: callout id uniqueness assertion FIRED")
        return 2
    if new and not a.dry:
        with planner.CALLOUTS.open("a") as f:
            for r in new:
                f.write(json.dumps(r, default=str) + "\n")
        posted = new

    for r in rows:
        if r["status"] == "PENDING":
            wake.append(f"ARMED TRIGGER {r['symbol']} arm {r['arm']} {r['side']} "
                        f"limit {r['limit_entry']} stop {r['stop']} target {r['target']} "
                        f"x{r['contracts']} (risk ${r['risk_usd']:.2f})")
        elif r["triggered_on_this_bar"] and any("REFUSED_SIZE" in n for n in r["notes"]):
            wake.append(f"REFUSED ON SIZE {r['symbol']} arm {r['arm']}: "
                        f"risk ${r['risk_usd']:.2f} > budget ${r['budget_usd']:.2f}")

    # --- resolve -------------------------------------------------------------
    resolved = 0
    if not a.dry:
        r = subprocess.run([sys.executable, str(HERE / "resolve.py")],
                           capture_output=True, text=True, timeout=600)
        out = (r.stdout or "").strip()
        for line in out.splitlines():
            if any(k in line for k in ("TARGET", "STOP", "SESSION", "TIME", "NO_FILL", "BE")):
                resolved += 1
                wake.append("RESOLVED " + line.strip())
        notes.append(out.splitlines()[-1] if out else "resolve.py produced no output")

    snap_line = "; ".join(
        f"{s} close {engine.snapshot(s)['newest_close']:.2f} @ "
        f"{engine.snapshot(s)['newest_bar'][:16]}" for s in engine.SYMS)
    rec = {"ts": now.isoformat(), "et": now.strftime("%Y-%m-%d %H:%M %Z"),
           "active_window": active, "posted": len(posted), "resolved": resolved,
           "equity": st["equity"], "drawdown": round(dd, 2),
           "wake": wake, "notes": notes}
    if not a.dry:
        with EVENTS.open("a") as f:
            f.write(json.dumps(rec, default=str) + "\n")

    print(f"LVN/FIB AGENT  {now.strftime('%Y-%m-%d %H:%M %Z')}  "
          f"entry window: {active or 'closed'}")
    print(f"  {snap_line}")
    print(f"  equity ${st['equity']:,.2f}  drawdown ${dd:,.2f}  "
          f"posted {len(posted)}  resolved {resolved}")
    for n in notes:
        print(f"  note: {n}")
    if wake:
        for w in wake:
            print(f"  WAKE: {w}")
        print("exit 10 - attention needed")
        return 10
    print("exit 0 - quiet, nothing to report")
    return 0


if __name__ == "__main__":
    sys.exit(main())
