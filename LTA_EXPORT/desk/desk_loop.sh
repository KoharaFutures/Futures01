#!/usr/bin/env bash
# LTA CONCEPT CALLOUTS — silent background loop (the "background agent").
# Runs cycle.sh every INTERVAL seconds and prints NOTHING on quiet cycles. It exits only when
# something happened, so whoever launched it is woken only for real events:
#   exit 10  a new callout or outcome (the CARD lines + a NOTIFY line are printed)
#   exit 2   three data failures in a row
#   bash desk/desk_loop.sh [interval_s]      bash ... --status
set -u
cd "$(dirname "$0")/.."
INTERVAL="${1:-120}"
PIDFILE=desk/.loop_pid
if [ "${1:-}" = "--status" ]; then
  [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null && { echo "LTA_LOOP alive pid $(cat $PIDFILE)"; exit 0; }
  echo "LTA_LOOP not running"; exit 1
fi
if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
  echo "LTA_LOOP already running as pid $(cat "$PIDFILE")"; exit 0
fi
echo $$ > "$PIDFILE"; trap 'rm -f "$PIDFILE"' EXIT INT TERM
fails=0
while true; do
  out=$(bash desk/cycle.sh 2>&1); rc=$?
  case "$rc" in
    10) echo "$out"; echo "NOTIFY $(git rev-parse --short HEAD)"; exit 10 ;;
    0|3) fails=0 ;;
    *) fails=$((fails+1)); [ "$fails" -ge 3 ] && { echo "$out"; exit 2; } ;;
  esac
  sleep "$INTERVAL"
done
