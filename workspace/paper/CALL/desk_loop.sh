#!/usr/bin/env bash
# Runs desk_check.py every 2 minutes and EXITS only when the desk needs a decision, so the agent that
# launched it (as a background command) is woken for judgment, never for routine checks.
#   exit 10 = needs_attention (read desk_status.json)   exit 2 = repeated data failure
# Outside the ET window it sleeps 10 minutes at a time (desk_check exits 3 there), so it is safe to
# leave running over the 15:30-18:00 break and the weekend.
# Usage (from the repo root):  bash workspace/paper/CALL/desk_loop.sh   [interval_seconds, default 120]
#
# REPORT MODE (owner, 2026-09-29 08:20 ET: "check and update every 2 minutes like the other callout desk
# and make sure you are providing the same style cards"):  DESK_REPORT_EVERY=1 bash .../desk_loop.sh
#   every in-window check renders its card(s) (--render always) and exits 0 = routine hand-off (attention, if any, is in desk_status.json triggers), so the
#   agent sends the card each check (CHECK_PROCEDURE "EVERY CHECK EMITS A CARD"). Only exit 2 (3 data failures in a row) is a real failure.
set -u
cd "$(dirname "$0")/../../.."
INTERVAL="${1:-120}"
REPORT="${DESK_REPORT_EVERY:-0}"
RENDER=auto; [ "$REPORT" = "1" ] && RENDER=always
fails=0
while true; do
  if [ "$REPORT" = "1" ] && [ -f workspace/paper/CALL/desk_status.json ]; then   # keep the 2-min cadence across restarts
    age=$(( $(date +%s) - $(stat -c %Y workspace/paper/CALL/desk_status.json) ))
    [ "$age" -lt "$INTERVAL" ] && sleep $(( INTERVAL - age ))
  fi
  python3 workspace/paper/CALL/desk_check.py --render "$RENDER" --scale 3
  rc=$?
  case "$rc" in
    0)  fails=0
        # owner 2026-09-29 11:49 ET: "if the previous was a no trade and the new update is still a no trade,
        # you dont have to update the card" -> a quiet check with an empty book stays silent (no wake, no card).
        # A live plan (pending/open) still gets its card every check; any trigger (rc 10) always hands off.
        if [ "$REPORT" = "1" ]; then
          live=$(python3 -c "import json;b=json.load(open('workspace/paper/CALL/desk_status.json'))['book'];print(len(b['pending'])+len(b['open']))" 2>/dev/null || echo 1)
          [ "$live" != "0" ] && { echo "DESK_LOOP: report -> send the card(s) in desk_status.json"; exit 0; }
        fi
        sleep "$INTERVAL" ;;
    3)  sleep 600 ;;
    10) echo "DESK_LOOP: needs_attention -> see workspace/paper/CALL/desk_status.json"
        [ "$REPORT" = "1" ] && exit 0 || exit 10 ;;   # report mode: a normal hand-off, not an error
    *)  fails=$((fails + 1)); echo "DESK_LOOP: desk_check exit $rc (failure $fails)"
        [ "$fails" -ge 3 ] && { echo "DESK_LOOP: 3 consecutive failures"; exit 2; }
        sleep "$INTERVAL" ;;
  esac
done
