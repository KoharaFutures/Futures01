#!/usr/bin/env python3
"""A compact, READ-ONLY update on the desk. Writes nothing, commits nothing.

desk_loop.sh is the single thing that runs the desk and commits; this only reads its
logs, so reporting every 2 minutes cannot double-report or race the loop's pushes.
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "workspace" / "anchors" / "lib"))
import core                                                  # noqa: E402

ET = core.ET if hasattr(core, "ET") else None


def jsonl(name):
    p = HERE / name
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def main():
    now = datetime.now(timezone.utc).astimezone()
    st = json.loads((HERE / "state.json").read_text()) if (HERE / "state.json").exists() else {}
    eq = st.get("equity", 50000.0)
    peak = st.get("peak", eq)
    dd = peak - eq
    ev = jsonl("desk_events.jsonl")
    ev.sort(key=lambda r: r["ts"])
    calls, res = jsonl("callouts.jsonl"), jsonl("resolutions.jsonl")

    # desk_loop.sh liveness, by pidfile - never by pgrep (its own command line matches).
    # The cron drives cycle.sh now, so "not running" is the intended state, not a fault;
    # what matters is whether a cycle ran recently. See NOTES_MECHANISM.md.
    pid_f = HERE / ".loop_pid"
    alive = False
    if pid_f.exists():
        try:
            import os
            os.kill(int(pid_f.read_text().strip()), 0)
            alive = True
        except (OSError, ValueError):
            alive = False

    last = ev[-1] if ev else None
    age = ((now - datetime.fromisoformat(last["ts"])).total_seconds() / 60) if last else None

    bars = []
    for sym in ("MGC", "MNQ"):
        try:
            t = core.tape(sym, 60)
            bars.append(f"{sym} {t.bars[-1].c:g} @ {t.bars[-1].ts.strftime('%Y-%m-%dT%H:%M')}")
        except Exception:                                    # noqa: BLE001
            bars.append(f"{sym} tape unreadable")

    win = last.get("active_window") if last else None
    resolved_ids = {r["id"] for r in res}
    open_c = [c for c in calls if c.get("contracts", 0) > 0 and c["id"] not in resolved_ids
              and c["status"] in ("PENDING", "OBSERVE")]

    # Health is "did a cycle run recently", whichever mechanism ran it.
    fresh = age is not None and age <= 5
    driver = "desk_loop" if alive else "cron"
    print(f"LVNFIB {now.strftime('%Y-%m-%d %H:%M:%S %Z')}  driver={driver}  "
          f"{'OK' if fresh else 'STALE'}: last cycle "
          f"{('%.1f min ago' % age) if age is not None else 'never'}")
    print(f"  window: {win if win else 'closed'}   bars: {'; '.join(bars)} (source bars, not quotes)")
    print(f"  equity ${eq:,.2f}  drawdown ${dd:,.2f}  room to floor ${2800 - dd:,.2f}"
          f"  closed {st.get('closed', 0)}")
    print(f"  callouts {len(calls)}  resolved {len(res)}  at-risk open {len(open_c)}")
    for c in open_c:
        print(f"    AT RISK {c['id']} {c['symbol']} arm {c['arm']} {c['side']} "
              f"limit {c['limit_entry']} stop {c['stop']} target {c['target']} x{c['contracts']}")
    mgc_a = [r for r in res if r.get("symbol") == "MGC" and r.get("arm") == "A"]
    print(f"  MGC arm A (the only armed rule): n={len(mgc_a)} forward"
          f"   prior n=24 +0.2379R t +1.027, win 50.0% at payoff 1.58")
    return 0


if __name__ == "__main__":
    sys.exit(main())
