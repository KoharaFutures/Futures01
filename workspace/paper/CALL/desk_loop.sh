#!/usr/bin/env bash
# Runs desk_check.py every 2 minutes and EXITS only when the desk needs a decision, so the agent that
# launched it (as a background command) is woken for judgment, never for routine checks.
#   exit 10 = needs_attention (read desk_status.json)   exit 2 = repeated data failure
# Outside the ET window it sleeps 10 minutes at a time (desk_check exits 3 there), so it is safe to
# leave running over the 15:30-18:00 break and the weekend.
# Usage (from the repo root):  bash workspace/paper/CALL/desk_loop.sh   [interval_seconds, default 120]
set -u
cd "$(dirname "$0")/../../.."
INTERVAL="${1:-120}"
fails=0
while true; do
  python3 workspace/paper/CALL/desk_check.py --render auto --scale 3
  rc=$?
  case "$rc" in
    0)  fails=0; sleep "$INTERVAL" ;;
    3)  sleep 600 ;;
    10) echo "DESK_LOOP: needs_attention -> see workspace/paper/CALL/desk_status.json"; exit 10 ;;
    *)  fails=$((fails + 1)); echo "DESK_LOOP: desk_check exit $rc (failure $fails)"
        [ "$fails" -ge 3 ] && { echo "DESK_LOOP: 3 consecutive failures"; exit 2; }
        sleep "$INTERVAL" ;;
  esac
done
