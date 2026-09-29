#!/usr/bin/env bash
# One report-mode turn's mechanics (AUTOMATE_NEXT #11): print the one line, triggers, notes and card paths
# from desk_status.json, then commit + merge + push workspace/paper/CALL/** so the stop hook stays clean.
# The agent then only sends the printed cards (SendUserFile, render, last) and restarts desk_loop.sh.
cd "$(dirname "$0")/../../.."
python3 - <<'PY'
import json;d=json.load(open('workspace/paper/CALL/desk_status.json'))
print("LINE", d["one_line"]); print("TRIGGERS", d["triggers"]); print("NOTES", d["notes"])
live = len(d["book"]["pending"]) + len(d["book"]["open"])
need = bool(live or d["triggers"])
print("CARD_NEEDED" if need else "NO_CARD (still no trade: text update only)")
for c in d["cards"]: print("CARD", c)
PY
git add workspace/paper/CALL >/dev/null 2>&1
git commit -qm "CALL desk report $(TZ=America/New_York date +%H:%M) ET

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_013793BxAYNNtb18hb5zFxy1" >/dev/null 2>&1
git fetch -q origin claude/admiring-heisenberg-doycyh claude/intelligent-feynman-ongyjw 2>/dev/null
git merge -q --no-edit origin/claude/admiring-heisenberg-doycyh >/dev/null 2>&1
git merge -q --no-edit origin/claude/intelligent-feynman-ongyjw >/dev/null 2>&1
git push -q origin claude/intelligent-feynman-ongyjw 2>&1 | tail -1
