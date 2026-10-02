#!/usr/bin/env bash
# LVN/FIB AGENT — one monitored cycle. What the 2-minute check runs.
#
#   merge -> desk turn (fetches live) -> hold the archive append-only -> assert the
#   prior still reproduces -> commit+push whatever the turn wrote.
#
# Exit: passes through desk_check.py's own code - 0 quiet, 3 dormant, 10 attention,
#       2 data failure - EXCEPT 4, which is this wrapper's own: the prior no longer
#       reproduces, so the desk is not tradeable (STOP). 4 deliberately avoids 3,
#       which desk_check.py already uses for the benign dormant case.
set -uo pipefail
cd "$(dirname "$0")/../../.."

git fetch -q origin claude/intelligent-feynman-ongyjw 2>/dev/null \
  && git merge -q --no-edit FETCH_HEAD >/dev/null 2>&1

bash workspace/paper/LVNFIB/desk.sh
desk=$?

python3 workspace/paper/LVNFIB/archive_guard.py | tail -1

if ! python3 workspace/paper/LVNFIB/verify_prior.py; then
  echo "CYCLE: prior broken - desk is NOT tradeable this cycle"
  exit 4
fi

python3 workspace/roundtable/check_ownership.py LVNFIB | tail -1

# Push every cycle by default. A slower push cadence leaves the event log sitting
# uncommitted between pushes, which trips the repo's stop hook ("there are uncommitted
# changes"); a clean tree is worth more than the saved commits. The union-merge
# .gitattributes and the re-merge retry below make per-cycle pushes safe on a branch
# several desks share. Set LVNFIB_PUSH_EVERY=<seconds> to throttle it again.
PUSH_EVERY="${LVNFIB_PUSH_EVERY:-0}"
stamp=workspace/paper/LVNFIB/.push_stamp
now=$(date +%s)
last=$(cat "$stamp" 2>/dev/null || echo 0)
due=no
[[ $desk -eq 10 || $desk -eq 2 ]] && due=yes
[[ $(( now - last )) -ge $PUSH_EVERY ]] && due=yes

if [[ "$due" == no ]]; then
  echo "CYCLE: holding $(git status --porcelain | wc -l | tr -d ' ') change(s), next push in $(( PUSH_EVERY - (now - last) ))s"
elif [[ -n "$(git status --porcelain)" ]]; then
  echo "$now" > "$stamp"
  git add -A data/archive workspace/paper/LVNFIB
  git commit -q -F - <<MSG
LVNFIB cycle $(TZ=America/New_York date '+%Y-%m-%d %H:%M ET') — desk exit ${desk}

Append-only archive refresh + desk turn. Arm A prior re-verified:
n=24 +0.2379R t +1.027 win 50.0% payoff 1.58, 164/164 triggers.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01U7cfC71Ua4XdUkGbBQDJFS
MSG
  # Other desks push to this same branch, so a push can lose a race. Re-merge on
  # every attempt - retrying the push alone just loses the same race again. Merge,
  # never rebase, and never force.
  pushed=no
  for i in 1 2 4 8; do
    git fetch -q origin claude/intelligent-feynman-ongyjw 2>/dev/null
    if ! git merge --no-edit FETCH_HEAD >/dev/null 2>&1; then
      echo "CYCLE: merge conflict on push - resolve by hand, nothing pushed"
      git merge --abort 2>/dev/null
      break
    fi
    if git push -q -u origin claude/intelligent-feynman-ongyjw 2>/dev/null; then
      pushed=yes; echo "CYCLE: pushed"; break
    fi
    sleep $i
  done
  [[ $pushed == yes ]] || echo "CYCLE: push did not land - will retry next cycle"
else
  echo "CYCLE: nothing to commit"
fi
exit $desk
