#!/usr/bin/env bash
# Fetch a sheet tab as CSV from the Omniheroes Google Spreadsheet.
#
# Usage:
#   ./fetch_sheet.sh                # fetch the Tier List tab
#   ./fetch_sheet.sh tier-list      # same
#   ./fetch_sheet.sh all            # fetch every tab listed in data/sheets.json
#
# Output: data/raw/<slug>.csv

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHEETS_JSON="$ROOT/data/sheets.json"
RAW_DIR="$ROOT/data/raw"
SHEET_ID="$(python3 -c "import json; print(json.load(open('$SHEETS_JSON'))['spreadsheetId'])")"

mkdir -p "$RAW_DIR"

fetch_one() {
  local slug="$1"
  local gid name
  gid="$(python3 -c "import json,sys; tabs=json.load(open('$SHEETS_JSON'))['tabs']; m=[t for t in tabs if t['slug']=='$slug']; print(m[0]['gid'] if m else '', end='')")"
  name="$(python3 -c "import json,sys; tabs=json.load(open('$SHEETS_JSON'))['tabs']; m=[t for t in tabs if t['slug']=='$slug']; print(m[0]['name'] if m else '', end='')")"
  if [[ -z "$gid" ]]; then
    echo "Unknown slug: $slug" >&2
    return 1
  fi
  local out="$RAW_DIR/$slug.csv"
  echo "Fetching '$name' (gid=$gid) → $out"
  curl -sSfL -o "$out" \
    "https://docs.google.com/spreadsheets/d/$SHEET_ID/export?format=csv&gid=$gid"
}

target="${1:-tier-list}"

if [[ "$target" == "all" ]]; then
  python3 -c "import json; [print(t['slug']) for t in json.load(open('$SHEETS_JSON'))['tabs']]" | while read -r slug; do
    fetch_one "$slug" || echo "  skip"
  done
else
  fetch_one "$target"
fi
