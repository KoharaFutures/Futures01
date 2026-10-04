#!/usr/bin/env bash
# LTA CONCEPT CALLOUTS — one desk turn: refresh bars, macro layer, war map, resolve, status.
#   bash desk/desk.sh              refresh + everything (needs: pip install yfinance)
#   bash desk/desk.sh --no-fetch   use the bars already fetched (levels are then NOT live)
#   bash desk/desk.sh MGC MNQ      limit symbols
set -uo pipefail
cd "$(dirname "$0")/.."
FETCH=1; SYMS=()
for a in "$@"; do [[ "$a" == "--no-fetch" ]] && FETCH=0 || SYMS+=("$a"); done
[[ ${#SYMS[@]} -eq 0 ]] && SYMS=(MNQ MES MGC MCL)
if [[ $FETCH -eq 1 ]]; then
  # own cache only: the shared refresh rewrites committed history (LVNFIB/archive_guard.py)
  python3 desk/fetch.py --symbols "${SYMS[@]}" \
    || echo "FETCH FAILED (or partly) — levels below may be from the archive, not live"
fi
echo; python3 desk/macro.py --symbols "${SYMS[@]}" || echo "macro layer failed"
echo; python3 desk/lta_levels.py --symbols "${SYMS[@]}" --write
echo; python3 desk/ledger.py
