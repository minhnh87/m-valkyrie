#!/usr/bin/env bash
# Download the full Omniheroes spreadsheet as XLSX (preserves inline images that
# don't survive CSV export). Used by extract_sheet_images.py to recover hero
# avatars from sheets like Rune Priority List.
#
# Output: data/raw/omni.xlsx (~30-40 MB)
#
# Usage:
#   ./scripts/fetch_xlsx.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHEETS_JSON="$ROOT/data/sheets.json"
RAW_DIR="$ROOT/data/raw"
SHEET_ID="$(python3 -c "import json; print(json.load(open('$SHEETS_JSON'))['spreadsheetId'])")"

mkdir -p "$RAW_DIR"
OUT="$RAW_DIR/omni.xlsx"

echo "Fetching workbook XLSX → $OUT"
curl -sSfL -o "$OUT" \
  "https://docs.google.com/spreadsheets/d/$SHEET_ID/export?format=xlsx"

echo "  size: $(wc -c <"$OUT" | tr -d ' ') bytes"
