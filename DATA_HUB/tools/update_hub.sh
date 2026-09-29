#!/usr/bin/env bash
# One command to refresh everything the hub generates:
#   1. pull the newest bars from Yahoo into data/archive (append-only)
#   2. re-measure every bounce level against placebo, per symbol, 5m and 60m
#   3. rebuild the cross-symbol consistency table
# Usage: bash DATA_HUB/tools/update_hub.sh            (needs: pip install yfinance)
#        bash DATA_HUB/tools/update_hub.sh --no-fetch (re-analyse the archive only)
set -euo pipefail
cd "$(dirname "$0")/../.."
if [[ "${1:-}" != "--no-fetch" ]]; then
  python3 DATA_HUB/tools/refresh_archive.py --fetch
fi
python3 DATA_HUB/tools/bounce_levels.py
python3 DATA_HUB/tools/level_consistency.py
echo "Hub refreshed. Levels: DATA_HUB/levels/<SYMBOL>_bounce.md  Summary: DATA_HUB/levels/CONSISTENCY.md"
