#!/usr/bin/env bash
# LVN/FIB AGENT — one turn of the desk.
#   bash workspace/paper/LVNFIB/desk.sh          plan dry-run, then resolve + status
#   bash workspace/paper/LVNFIB/desk.sh --post   also post new callouts
set -euo pipefail
cd "$(dirname "$0")"
echo "--- refresh (optional; needs pip install yfinance) ---"
python3 ../../../DATA_HUB/tools/refresh_archive.py --fetch --symbols MGC MNQ --frames 15 60 2>&1 | tail -4 || \
  echo "  no live feed available - running off data/archive/ (see CHARTER.md §4)"
echo
echo "--- plan ---"
python3 plan.py ${1:-}
echo
echo "--- resolve ---"
python3 resolve.py
echo
python3 status.py
