#!/usr/bin/env bash
# Rebuild the Arcadia logo files and the workforce map preview.
#   python pipeline/run_pipeline.py --no-export   # warehouse first
#   bash docs/brand/build/build.sh
# Needs Node (npm) and Python with duckdb and playwright (Chromium).
set -euo pipefail
cd "$(dirname "$0")"
npm install --silent
node logo.js
python3 render.py
python3 export_map_data.py
python3 export_headcount_data.py
python3 -m http.server 8799 --bind 127.0.0.1 --directory .. >/dev/null 2>&1 &
SERVER=$!; trap 'kill $SERVER' EXIT; sleep 1
python3 shot.py http://127.0.0.1:8799/build/map_preview.html ../../images/workforce_map_preview.png
python3 shot.py http://127.0.0.1:8799/build/headcount_preview.html ../../images/headcount_walk_preview.png
echo "Done: docs/brand/*.svg|png and docs/images/*_preview.png"
