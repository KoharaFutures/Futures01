#!/usr/bin/env bash
# LTA CONCEPT CALLOUTS — one desk turn: refresh bars, macro layer, war map, resolve, status.
#   bash workspace/paper/LTA/desk.sh              refresh + everything (needs: pip install yfinance)
#   bash workspace/paper/LTA/desk.sh --no-fetch   use data/archive as it is (levels are then NOT live)
#   bash workspace/paper/LTA/desk.sh MGC MNQ      limit symbols
set -uo pipefail
cd "$(dirname "$0")/../../.."
FETCH=1; SYMS=()
for a in "$@"; do [[ "$a" == "--no-fetch" ]] && FETCH=0 || SYMS+=("$a"); done
[[ ${#SYMS[@]} -eq 0 ]] && SYMS=(MNQ MES MGC MCL)
if [[ $FETCH -eq 1 ]]; then
  # own cache only: the shared refresh rewrites committed history (LVNFIB/archive_guard.py)
  python3 workspace/paper/LTA/fetch.py --symbols "${SYMS[@]}" \
    || echo "FETCH FAILED (or partly) — levels below may be from the archive, not live"
fi
echo; python3 workspace/paper/LTA/macro.py --symbols "${SYMS[@]}" || echo "macro layer failed"
echo; python3 workspace/paper/LTA/lta_levels.py --symbols "${SYMS[@]}" --write
echo; python3 workspace/paper/LTA/ledger.py
