#!/usr/bin/env bash
# LVN/FIB AGENT — continuous loop. Runs desk_check.py every 2 minutes and EXITS only when the desk
# needs a decision, so the agent that launched it in the background is woken for judgment and never
# for a routine check.
#
#   exit 10 = attention needed    exit 2 = three consecutive data failures
#
# Outside every entry window with nothing waiting to resolve, desk_check exits 3 and the loop sleeps
# 10 minutes at a time, so it is safe to leave running across the 15:30-18:00 break and the weekend.
#
# Usage (from the repo root):  bash workspace/paper/LVNFIB/desk_loop.sh [interval_seconds]
# Default interval 120s. The CHECK runs at that cadence; the FEED is throttled separately inside
# desk_check.py (FETCH_MIN_SECONDS), because 15m bars close four times an hour and 60m bars once,
# so fetching every 2 minutes cannot surface information that does not exist yet.
set -u
cd "$(dirname "$0")/../../.."
INTERVAL="${1:-120}"
fails=0
echo "LVNFIB_LOOP: starting, interval ${INTERVAL}s, pid $$"
while true; do
  python3 workspace/paper/LVNFIB/desk_check.py
  rc=$?
  case "$rc" in
    0)  fails=0; sleep "$INTERVAL" ;;
    3)  fails=0; sleep 600 ;;
    10) echo "LVNFIB_LOOP: attention -> see the WAKE lines above and desk_events.jsonl"
        exit 10 ;;
    *)  fails=$((fails + 1)); echo "LVNFIB_LOOP: desk_check exit $rc (failure $fails of 3)"
        if [ "$fails" -ge 3 ]; then echo "LVNFIB_LOOP: 3 consecutive failures"; exit 2; fi
        sleep "$INTERVAL" ;;
  esac
done
