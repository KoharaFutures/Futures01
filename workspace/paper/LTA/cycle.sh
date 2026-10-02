#!/usr/bin/env bash
# LTA CONCEPT CALLOUTS — one 2-minute cycle: scan, and commit + push only when something happened.
#   bash workspace/paper/LTA/cycle.sh
# Exit passes through scan.py: 0 quiet · 3 dormant · 10 notify (CARD lines = PNGs to send) · 2 data failure.
# Pushes to this desk's own branch only; it never merges or pushes another desk's branch.
set -uo pipefail
cd "$(dirname "$0")/../../.."
BRANCH="${LTA_BRANCH:-claude/zealous-sagan-n7jnmn}"
python3 -c "import yfinance, PIL" 2>/dev/null || pip install -q yfinance pillow >/dev/null 2>&1
python3 workspace/paper/LTA/scan.py
rc=$?
if [[ $rc -eq 10 && -n "$(git status --porcelain workspace/paper/LTA)" ]]; then
  git add workspace/paper/LTA
  git commit -q -m "LTA cycle $(TZ=America/New_York date '+%Y-%m-%d %H:%M ET') — callout/outcome

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01FsjMu3FuXfDBstj3dv52X7"
  for i in 2 4 8 16; do
    git push -q -u origin "$BRANCH" 2>/dev/null && { echo "CYCLE: pushed"; break; }
    sleep $i
  done
fi
exit $rc
