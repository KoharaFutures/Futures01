#!/usr/bin/env bash
# LVN/FIB AGENT — one turn of the desk.
#   bash desk.sh              the gated mechanical turn (what the routine runs)
#   bash desk.sh --manual     plan dry-run + resolve + full status, for a human
# Exit codes from the gated turn: 0 quiet, 10 attention needed, 2 data failure.
set -uo pipefail
cd "$(dirname "$0")"
if [[ "${1:-}" == "--manual" ]]; then
  python3 plan.py; echo; python3 resolve.py; echo; python3 status.py; exit 0
fi
python3 desk_check.py
code=$?
if [[ $code -eq 10 ]]; then echo; python3 status.py; fi
exit $code
