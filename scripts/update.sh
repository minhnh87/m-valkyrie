#!/usr/bin/env bash
# One-shot update: re-pull the spreadsheet tabs, refresh hero images, rebuild
# every page's data JSON, and re-assemble the single tabbed index.html.
#
# Usage:
#   ./scripts/update.sh                  # update everything
#   ./scripts/update.sh tier-list        # only rebuild this page's data
#   ./scripts/update.sh --no-images      # skip the wiki image refresh
#
# Adding a new page: see WORKFLOW.md.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

REFRESH_IMAGES=1
TARGETS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-images) REFRESH_IMAGES=0; shift ;;
    --) shift; TARGETS+=("$@"); break ;;
    *) TARGETS+=("$1"); shift ;;
  esac
done

ALL_PAGES=(tier-list beginners-priority endgame-priority rune-priority rune-notes)
if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("${ALL_PAGES[@]}")
fi

IMAGES_REFRESHED=0
maybe_refresh_images() {
  if [[ $REFRESH_IMAGES -eq 1 && $IMAGES_REFRESHED -eq 0 ]]; then
    echo "▶ refreshing hero images from Fandom"
    python3 scripts/fetch_images.py
    echo "▶ mirroring avatars into assets/heroes/ (Fandom CDN blocks hotlinks)"
    python3 scripts/download_images.py
    IMAGES_REFRESHED=1
  fi
}

# rune-priority needs avatars extracted from the workbook XLSX (CSV strips
# inline images). rune-notes opportunistically falls back to those same local
# PNGs for heroes Fandom doesn't have, so both pages share one extraction pass.
INLINE_REFRESHED=0
maybe_refresh_inline_images() {
  if [[ $INLINE_REFRESHED -eq 0 ]]; then
    echo "▶ downloading workbook XLSX (for inline avatars)"
    ./scripts/fetch_xlsx.sh
    echo "▶ extracting inline images from XLSX"
    python3 scripts/extract_sheet_images.py
    INLINE_REFRESHED=1
  fi
}

build_tier_list() {
  echo "▶ tier-list: pulling CSV"
  ./scripts/fetch_sheet.sh tier-list
  maybe_refresh_images
  echo "▶ tier-list: building data JSON"
  python3 scripts/build_tier_list.py
}

build_beginners_priority() {
  echo "▶ beginners-priority: pulling CSV"
  ./scripts/fetch_sheet.sh beginners-priority
  maybe_refresh_images
  echo "▶ beginners-priority: building data JSON"
  python3 scripts/build_beginners_priority.py
}

build_endgame_priority() {
  echo "▶ endgame-priority: pulling CSV"
  ./scripts/fetch_sheet.sh endgame-priority
  maybe_refresh_images
  echo "▶ endgame-priority: building data JSON"
  python3 scripts/build_endgame_priority.py
}

build_rune_priority() {
  echo "▶ rune-priority: pulling CSV"
  ./scripts/fetch_sheet.sh rune-priority
  maybe_refresh_images
  maybe_refresh_inline_images
  echo "▶ rune-priority: building data JSON"
  python3 scripts/build_rune_priority.py
}

build_rune_notes() {
  echo "▶ rune-notes: pulling CSV"
  ./scripts/fetch_sheet.sh rune-notes
  maybe_refresh_images
  maybe_refresh_inline_images
  echo "▶ rune-notes: building data JSON"
  python3 scripts/build_rune_notes.py
}

for t in "${TARGETS[@]}"; do
  case "$t" in
    tier-list) build_tier_list ;;
    beginners-priority) build_beginners_priority ;;
    endgame-priority) build_endgame_priority ;;
    rune-priority) build_rune_priority ;;
    rune-notes) build_rune_notes ;;
    *) echo "Unknown target: $t (known: ${ALL_PAGES[*]})" >&2; exit 1 ;;
  esac
done

echo "▶ assembling index.html"
python3 scripts/build_html.py

echo "✓ Done. Open index.html in a browser."
